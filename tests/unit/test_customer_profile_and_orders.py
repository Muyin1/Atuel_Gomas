import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.database.connection import init_db
from src.infrastructure.database.models import ClienteModel, OrdenModel, OrdenItemModel
from src.adapters.repositories.sql_customer_repository import SqlAlchemyCustomerRepository
from src.adapters.repositories.sql_order_repository import SqlAlchemyOrderRepository
from src.application.dtos.auth_dto import UpdateProfileDTO
from src.application.use_cases.update_customer_profile import UpdateCustomerProfileUseCase
from src.domain.entities.user_role import UserRole
from src.domain.entities.order_status import OrderStatus


@pytest.fixture
def sqlite_customer_order_env():
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    with session_factory() as session:
        cliente = ClienteModel(
            id="cust-b2b-100",
            email="cliente.mayorista@atuel.com",
            razon_social="Repuestos y Accesorios del Sol SA",
            cuit="30-71122334-9",
            telefono="+54 11 4000-1111",
            direccion="Av. San Martín 2500",
            ciudad="Mendoza",
            rol="b2b_client",
            rubro="AUTOPARTES",
            is_approved=True,
            markup_percent=30.0,
            hashed_password="hash_test_secret",
        )
        ord1 = OrdenModel(
            id="ORD-SOL-01",
            cliente=cliente,
            cliente_nombre="Repuestos y Accesorios del Sol SA",
            total=125000.0,
            estado="PENDIENTE_APROBACION",
            notas="Despacho urgente por Expreso Luján"
        )
        ord2 = OrdenModel(
            id="ORD-SOL-02",
            cliente=cliente,
            cliente_nombre="Repuestos y Accesorios del Sol SA",
            total=84000.0,
            estado="DESPACHADO",
            notas="Retiro en sucursal"
        )
        session.add_all([cliente, ord1, ord2])
        session.commit()

    cust_repo = SqlAlchemyCustomerRepository(session_factory=session_factory)
    order_repo = SqlAlchemyOrderRepository(session_factory=session_factory)
    return cust_repo, order_repo


@pytest.mark.asyncio
async def test_update_customer_profile_and_orders_history(sqlite_customer_order_env):
    cust_repo, order_repo = sqlite_customer_order_env
    use_case = UpdateCustomerProfileUseCase(cust_repo)

    # 1. Verificar estado inicial del cliente
    c_init = await cust_repo.get_by_id("cust-b2b-100")
    assert c_init is not None
    assert c_init.markup_percent == 30.0
    assert c_init.phone == "+54 11 4000-1111"

    # 2. Actualizar perfil con margen personalizado (ej: 33.5%)
    dto = UpdateProfileDTO(
        markup_percent=33.5,
        phone="+54 261 455-6789",
        address="Av. Acceso Este 1020, Guaymallén"
    )
    c_updated = await use_case.execute("cust-b2b-100", dto)
    assert c_updated.markup_percent == 33.5
    assert c_updated.phone == "+54 261 455-6789"
    assert "Guaymallén" in c_updated.address

    # Verificar persistencia en base de datos
    c_db = await cust_repo.get_by_id("cust-b2b-100")
    assert c_db.markup_percent == 33.5
    assert c_db.phone == "+54 261 455-6789"

    # 3. Validar rechazo de margen negativo
    with pytest.raises(ValueError):
        await use_case.execute("cust-b2b-100", UpdateProfileDTO(markup_percent=-5.0))

    # 4. Consultar historial de pedidos del cliente
    orders = await order_repo.get_by_customer("cust-b2b-100")
    assert len(orders) == 2
    order_ids = [o.id for o in orders]
    assert "ORD-SOL-01" in order_ids
    assert "ORD-SOL-02" in order_ids

    # Validar mapeo de estados del dominio
    statuses = {o.id: o.status for o in orders}
    assert statuses["ORD-SOL-01"] == OrderStatus.PENDING_APPROVAL
    assert statuses["ORD-SOL-02"] == OrderStatus.DISPATCHED
