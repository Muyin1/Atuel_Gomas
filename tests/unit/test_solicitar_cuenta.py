import pytest
from src.application.dtos.solicitud_cuenta_dto import SolicitudCuentaDTO
from src.application.dtos.auth_dto import RegisterB2BDTO
from src.application.use_cases.solicitar_cuenta import SolicitarCuentaUseCase
from src.application.use_cases.register_b2b_customer import RegisterB2BCustomerUseCase
from src.application.use_cases.authenticate_customer import AuthenticateCustomerUseCase
from src.application.ports.customer_repository import ICustomerRepository
from src.application.ports.password_hasher import IPasswordHasher
from src.domain.entities.customer import Customer
from src.domain.entities.user_role import UserRole
from src.domain.entities.business_line import BusinessLine
from src.domain.exceptions.domain_exceptions import CustomerAlreadyExistsError, UnauthorizedActionError


class InMemoryCustomerRepository(ICustomerRepository):
    def __init__(self):
        self.customers: dict[str, Customer] = {}

    async def get_by_id(self, customer_id: str) -> Customer | None:
        return self.customers.get(customer_id)

    async def get_by_cuit(self, cuit_str: str) -> Customer | None:
        clean = cuit_str.replace("-", "").strip()
        for c in self.customers.values():
            if c.cuit.value.replace("-", "").strip() == clean:
                return c
        return None

    async def get_by_email(self, email: str) -> Customer | None:
        clean = email.strip().lower()
        for c in self.customers.values():
            if c.email.lower() == clean:
                return c
        return None

    async def save(self, customer: Customer) -> None:
        self.customers[customer.id] = customer

    async def update_profile(
        self,
        customer_id: str,
        markup_percent: float,
        phone: str | None = None,
        address: str | None = None
    ) -> Customer:
        c = self.customers.get(customer_id)
        if not c:
            raise ValueError(f"Cliente {customer_id} no encontrado")
        c.markup_percent = float(markup_percent)
        if phone is not None:
            c.phone = phone
        if address is not None:
            c.address = address
        return c

    async def get_sales_agents(self) -> list[Customer]:
        return [c for c in self.customers.values() if c.role == UserRole.SALES_AGENT]

    async def get_customers_by_sales_agent(self, sales_agent_id: str) -> list[Customer]:
        return [c for c in self.customers.values() if c.sales_agent_id == sales_agent_id]

    async def assign_sales_agent(self, customer_id: str, sales_agent_id: str | None) -> None:
        c = self.customers.get(customer_id)
        if c:
            c.sales_agent_id = sales_agent_id



class FakePasswordHasher(IPasswordHasher):
    def hash(self, password: str) -> str:
        return f"hashed_{password}"

    def verify(self, password: str, hashed_password: str) -> bool:
        return hashed_password == f"hashed_{password}"


@pytest.mark.asyncio
async def test_solicitar_cuenta_success():
    repo = InMemoryCustomerRepository()
    use_case = SolicitarCuentaUseCase(repo)

    dto = SolicitudCuentaDTO(
        business_name="Ferretería y Repuestos del Valle SRL",
        cuit="30-71122334-9",
        rubro=BusinessLine.AUTOPARTES,
        email="contacto@ferreteriavalle.com.ar",
        phone="+54 261 4239999",
        province="Mendoza",
        city="Godoy Cruz",
        message="Deseamos abrir cuenta mayorista para taller y repuestos."
    )

    created = await use_case.execute(dto)

    assert created.id is not None
    assert created.business_name == "Ferretería y Repuestos del Valle SRL"
    assert created.cuit.value == "30-71122334-9"
    assert created.business_line == BusinessLine.AUTOPARTES
    assert created.is_approved is False
    assert created.role == UserRole.B2B_CLIENT
    assert "Mendoza" in created.city
    assert "Deseamos abrir cuenta" in created.address

    # Verificar persistencia en repo
    saved = await repo.get_by_cuit("30-71122334-9")
    assert saved is not None
    assert saved.is_approved is False


@pytest.mark.asyncio
async def test_solicitar_cuenta_duplicate_cuit_active_or_pending():
    repo = InMemoryCustomerRepository()
    use_case = SolicitarCuentaUseCase(repo)

    dto = SolicitudCuentaDTO(
        business_name="Ferretería Uno",
        cuit="30-71122334-9",
        rubro=BusinessLine.FERRETERIA,
        email="uno@test.com",
        phone="123456",
        province="Buenos Aires",
        city="La Plata",
        message=""
    )

    # 1. Primer registro exitoso (pendiente)
    await use_case.execute(dto)

    # 2. Intento duplicado con el mismo CUIT mientras está pendiente
    with pytest.raises(CustomerAlreadyExistsError) as exc_pending:
        await use_case.execute(dto)
    assert "solicitud pendiente" in str(exc_pending.value).lower()

    # 3. Si la cuenta ya está aprobada
    pending_cust = await repo.get_by_cuit("30-71122334-9")
    pending_cust.is_approved = True

    dto_diff_email = SolicitudCuentaDTO(
        business_name="Ferretería Dos",
        cuit="30-71122334-9",
        rubro=BusinessLine.FERRETERIA,
        email="otro@test.com",
        phone="123456",
        province="Buenos Aires",
        city="La Plata"
    )
    with pytest.raises(CustomerAlreadyExistsError) as exc_active:
        await use_case.execute(dto_diff_email)
    assert "cuenta mayorista activa" in str(exc_active.value).lower()


@pytest.mark.asyncio
async def test_solicitar_cuenta_duplicate_email():
    repo = InMemoryCustomerRepository()
    use_case = SolicitarCuentaUseCase(repo)

    dto1 = SolicitudCuentaDTO(
        business_name="Empresa A",
        cuit="30-71122334-9",
        rubro=BusinessLine.AMBOS,
        email="repetido@atuel.com",
        phone="111"
    )
    await use_case.execute(dto1)

    dto2 = SolicitudCuentaDTO(
        business_name="Empresa B",
        cuit="30-99999999-9",
        rubro=BusinessLine.AMBOS,
        email="repetido@atuel.com",
        phone="222"
    )
    with pytest.raises(CustomerAlreadyExistsError) as exc:
        await use_case.execute(dto2)
    assert "solicitud pendiente asociada al correo" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_demo_authentication_mode():
    repo = InMemoryCustomerRepository()
    hasher = FakePasswordHasher()
    auth_uc = AuthenticateCustomerUseCase(repo, hasher)

    # Caso A: Sin usuario demo en DB -> Devuelve entidad simulada en memoria
    demo_fallback = await auth_uc.authenticate_demo()
    assert demo_fallback.id == "DEMO-PROSPECTO"
    assert demo_fallback.role == UserRole.B2B_CLIENT
    assert demo_fallback.is_approved is True

    # Caso B: Con usuario demo en DB
    demo_cust = Customer(
        id="cli-b2b-001",
        email="cliente@atuelgomas.com",
        business_name="Distribuidora Demo SRL",
        cuit=demo_fallback.cuit,
        phone="11223344",
        address="Warnes 100",
        city="CABA",
        role=UserRole.B2B_CLIENT,
        business_line=BusinessLine.AMBOS,
        is_approved=True
    )
    await repo.save(demo_cust)

    demo_db = await auth_uc.authenticate_demo()
    assert demo_db.id == "cli-b2b-001"
    assert demo_db.business_name == "Distribuidora Demo SRL"
    assert demo_db.role == UserRole.B2B_CLIENT
    assert demo_db.is_approved is True


@pytest.mark.asyncio
async def test_register_b2b_requires_admin_role():
    repo = InMemoryCustomerRepository()
    hasher = FakePasswordHasher()
    register_uc = RegisterB2BCustomerUseCase(repo, hasher)

    dto = RegisterB2BDTO(
        business_name="Cliente Directo SRL",
        cuit="30-71122334-9",
        email="directo@cliente.com",
        phone="123",
        address="Calle Falsa 123",
        city="Quilmes",
        password="segura"
    )

    # 1. Llamada anónima o sin rol ADMIN debe fallar
    with pytest.raises(UnauthorizedActionError):
        await register_uc.execute(dto, requester=None)

    with pytest.raises(UnauthorizedActionError):
        await register_uc.execute(dto, requester=UserRole.PUBLIC)

    with pytest.raises(UnauthorizedActionError):
        await register_uc.execute(dto, requester=UserRole.B2B_CLIENT)

    # 2. Llamada autorizada con rol ADMIN
    created = await register_uc.execute(dto, requester=UserRole.ADMIN)
    assert created.id is not None
    assert created.email == "directo@cliente.com"
    assert created.role == UserRole.B2B_CLIENT
    assert created.is_approved is True
