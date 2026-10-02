from src.application.ports.customer_repository import ICustomerRepository
from src.application.ports.password_hasher import IPasswordHasher
from src.application.dtos.auth_dto import LoginDTO
from src.domain.entities.customer import Customer
from src.domain.entities.user_role import UserRole
from src.domain.entities.business_line import BusinessLine
from src.domain.value_objects.cuit import CUIT
from src.domain.exceptions.domain_exceptions import InvalidCustomerCredentialsError



class AuthenticateCustomerUseCase:
    def __init__(self, customer_repo: ICustomerRepository, hasher: IPasswordHasher):
        self.customer_repo = customer_repo
        self.hasher = hasher

    async def execute(self, dto: LoginDTO) -> Customer:
        identifier = dto.cuit_or_email.strip()

        customer = None
        if "@" in identifier:
            customer = await self.customer_repo.get_by_email(identifier)
        else:
            try:
                cuit_vo = CUIT(identifier)
                customer = await self.customer_repo.get_by_cuit(cuit_vo.value)
            except ValueError:
                customer = None

        if not customer:
            raise InvalidCustomerCredentialsError("Credenciales inválidas o cuenta inexistente.")

        if not self.hasher.verify(dto.password, customer.hashed_password):
            raise InvalidCustomerCredentialsError("Credenciales inválidas o cuenta inexistente.")

        return customer

    async def authenticate_demo(self) -> Customer:
        """
        Modo Demo / Prospecto (Simulación Comercial):
        Permite generar una sesión segura con rol UserRole.B2B_CLIENT para simulación de precios y pedidos mayoristas.
        Si existe el cliente de demostración 'cliente@atuelgomas.com' en el repositorio, se utiliza su registro.
        En caso contrario, se retorna una entidad simulada en memoria con permisos B2B activos.
        """
        demo_customer = await self.customer_repo.get_by_email("cliente@atuelgomas.com")
        if demo_customer:
            return demo_customer

        # Fallback a sesión simulada en memoria
        return Customer(
            id="DEMO-PROSPECTO",
            email="demo@atuelgomas.com.ar",
            business_name="Cliente Simulación Comercial (Modo Demo)",
            cuit=CUIT("30-71122334-9"),
            phone="+54 11 4855-9000",
            address="Av. Warnes 1450",
            city="CABA",
            role=UserRole.B2B_CLIENT,
            business_line=BusinessLine.AMBOS,
            is_approved=True,
            hashed_password=""
        )

