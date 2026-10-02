import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.database.connection import init_db
from src.infrastructure.database.models import ClienteModel, OrdenModel, OrdenItemModel, ProductoModel, CategoriaModel, FamiliaModel
from src.adapters.repositories.sql_customer_repository import SqlAlchemyCustomerRepository
from src.adapters.repositories.sql_order_repository import SqlAlchemyOrderRepository
from src.adapters.repositories.sql_product_repository import SqlAlchemyProductRepository
from src.application.dtos.auth_dto import AssignSalesAgentDTO
from src.application.dtos.order_dto import CreateOrderDTO, OrderItemDTO
from src.application.use_cases.manage_sales_agents import ManageSalesAgentUseCase
from src.application.use_cases.create_order import CreateOrderUseCase
from src.domain.entities.user_role import UserRole
from src.domain.exceptions.domain_exceptions import UnauthorizedActionError


@pytest.fixture
def sqlite_sales_agent_env():
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    with session_factory() as session:
        # Vendedor de prueba
        vendedor = ClienteModel(
            id="cli-vendedor-001",
            email="vendedor@atuelgomas.com",
            razon_social="Carlos Ventas (Zona Cuyo)",
            cuit="20-33445566-7",
            telefono="+54 261 411-2233",
            direccion="San Martín 1500",
            ciudad="Mendoza",
            rol="sales_agent",
            rubro="AMBOS",
            is_approved=True,
            markup_percent=30.0,
            hashed_password="hash_test_vendedor",
        )
        # Cliente 1 asignado al vendedor
        cliente1 = ClienteModel(
            id="cli-b2b-001",
            email="cliente1@repuestos.com",
            razon_social="Distribuidora Central de Gomas SRL",
            cuit="30-71122334-9",
            telefono="+54 11 4855-9000",
            direccion="Av. Warnes 1450",
            ciudad="CABA",
            rol="b2b_client",
            rubro="AUTOPARTES",
            sales_agent_id="cli-vendedor-001",
            is_approved=True,
            markup_percent=30.0,
            hashed_password="hash_test_cliente",
        )
        # Cliente 2 sin asignar inicialmente
        cliente2 = ClienteModel(
            id="cli-b2b-002",
            email="cliente2@ferreteria.com",
            razon_social="Ferretería Industrial Andina SA",
            cuit="30-88997766-5",
            telefono="+54 261 499-8877",
            direccion="Acceso Sur 100",
            ciudad="Godoy Cruz",
            rol="b2b_client",
            rubro="FERRETERIA",
            sales_agent_id=None,
            is_approved=True,
            markup_percent=30.0,
            hashed_password="hash_test_cliente2",
        )

        cat = CategoriaModel(nombre="Mangueras Automotor", slug="mangueras-automotor")
        fam = FamiliaModel(nombre="Mangueras de Radiador", slug="mangueras-radiador", categoria=cat)
        prod = ProductoModel(
            id=5001,
            sku="AG-5001",
            nombre="Manguera Radiador Test",
            categoria=cat,
            familia=fam,
            precio_base=10000.0,
            precio_mayorista_b2b=7000.0,
            stock=50,
            activo=True
        )

        session.add_all([vendedor, cliente1, cliente2, cat, fam, prod])
        session.commit()

    cust_repo = SqlAlchemyCustomerRepository(session_factory=session_factory)
    order_repo = SqlAlchemyOrderRepository(session_factory=session_factory)
    prod_repo = SqlAlchemyProductRepository(session_factory=session_factory)
    return cust_repo, order_repo, prod_repo


@pytest.mark.asyncio
async def test_get_sales_agents_and_portfolio(sqlite_sales_agent_env):
    cust_repo, order_repo, prod_repo = sqlite_sales_agent_env
    manage_uc = ManageSalesAgentUseCase(cust_repo)

    # 1. Obtener lista de vendedores
    agents = await manage_uc.get_sales_agents()
    assert len(agents) == 1
    assert agents[0].id == "cli-vendedor-001"
    assert agents[0].role == UserRole.SALES_AGENT
    assert agents[0].business_name == "Carlos Ventas (Zona Cuyo)"

    # 2. Obtener cartera de clientes asignados a cli-vendedor-001
    portfolio = await manage_uc.get_portfolio("cli-vendedor-001")
    assert len(portfolio) == 1
    assert portfolio[0].id == "cli-b2b-001"
    assert portfolio[0].sales_agent_id == "cli-vendedor-001"


@pytest.mark.asyncio
async def test_assign_sales_agent_protection_and_execution(sqlite_sales_agent_env):
    cust_repo, order_repo, prod_repo = sqlite_sales_agent_env
    manage_uc = ManageSalesAgentUseCase(cust_repo)

    dto = AssignSalesAgentDTO(
        customer_id="cli-b2b-002",
        sales_agent_id="cli-vendedor-001"
    )

    # 1. Intento no autorizado sin rol ADMIN
    with pytest.raises(UnauthorizedActionError):
        await manage_uc.assign_agent(dto, requester_role=UserRole.B2B_CLIENT)

    with pytest.raises(UnauthorizedActionError):
        await manage_uc.assign_agent(dto, requester_role=None)

    # 2. Asignación autorizada por ADMIN
    await manage_uc.assign_agent(dto, requester_role=UserRole.ADMIN)

    # Verificar que cliente2 ahora esté en la cartera del vendedor
    updated_portfolio = await manage_uc.get_portfolio("cli-vendedor-001")
    portfolio_ids = [c.id for c in updated_portfolio]
    assert "cli-b2b-001" in portfolio_ids
    assert "cli-b2b-002" in portfolio_ids

    # 3. Desvincular cliente2
    unassign_dto = AssignSalesAgentDTO(customer_id="cli-b2b-002", sales_agent_id=None)
    await manage_uc.assign_agent(unassign_dto, requester_role=UserRole.ADMIN)
    portfolio_after = await manage_uc.get_portfolio("cli-vendedor-001")
    assert [c.id for c in portfolio_after] == ["cli-b2b-001"]


@pytest.mark.asyncio
async def test_create_order_auto_assigns_sales_agent_and_query_by_sales_agent(sqlite_sales_agent_env):
    cust_repo, order_repo, prod_repo = sqlite_sales_agent_env
    create_order_uc = CreateOrderUseCase(order_repo, prod_repo, cust_repo)

    # Emitir orden para cli-b2b-001 (que tiene sales_agent_id='cli-vendedor-001')
    order_dto = CreateOrderDTO(
        customer_id="cli-b2b-001",
        items=[OrderItemDTO(product_id="5001", quantity=3)],
        notes="Despacho urgente Zona Cuyo"
    )

    created_order = await create_order_uc.execute(order_dto)
    assert created_order.id.startswith("ORD-")
    assert created_order.sales_agent_id == "cli-vendedor-001"

    # Consultar pedidos del vendedor
    agent_orders = await order_repo.get_by_sales_agent("cli-vendedor-001")
    assert len(agent_orders) >= 1
    assert agent_orders[0].id == created_order.id
    assert agent_orders[0].sales_agent_id == "cli-vendedor-001"
    assert agent_orders[0].customer_name == "Distribuidora Central de Gomas SRL"
