import uuid
from src.application.ports.customer_repository import ICustomerRepository
from src.application.ports.password_hasher import IPasswordHasher
from src.application.dtos.auth_dto import RegisterB2BDTO
from src.domain.entities.customer import Customer
from src.domain.entities.user_role import UserRole
from src.domain.value_objects.cuit import CUIT
from src.domain.exceptions.domain_exceptions import CustomerAlreadyExistsError, UnauthorizedActionError


class RegisterB2BCustomerUseCase:
    """
    Caso de uso para el alta directa de clientes comerciales aprobados.
    Protegido para ejecución exclusiva por parte de un Administrador (UserRole.ADMIN).
    Los usuarios y prospectos públicos deben registrarse a través de 'SolicitarCuentaUseCase'.
    """

    def __init__(self, customer_repo: ICustomerRepository, hasher: IPasswordHasher):
        self.customer_repo = customer_repo
        self.hasher = hasher

    async def execute(self, dto: RegisterB2BDTO, requester: Customer | UserRole | str | None = None) -> Customer:
        # Verificar permisos de Administrador
        requester_role = None
        if isinstance(requester, Customer):
            requester_role = requester.role
        elif isinstance(requester, UserRole):
            requester_role = requester
        elif isinstance(requester, str):
            try:
                requester_role = UserRole(requester.upper())
            except ValueError:
                requester_role = None

        if requester_role != UserRole.ADMIN:
            raise UnauthorizedActionError(
                "Operación no autorizada: El alta directa de cuentas mayoristas aprobadas es exclusiva para administradores."
            )

        # Validar CUIT
        cuit_vo = CUIT(dto.cuit)


        # Chequear existencia
        existing_cuit = await self.customer_repo.get_by_cuit(cuit_vo.value)
        if existing_cuit:
            raise CustomerAlreadyExistsError("Ya existe una cuenta registrada con este CUIT.")

        existing_email = await self.customer_repo.get_by_email(dto.email)
        if existing_email:
            raise CustomerAlreadyExistsError("Ya existe una cuenta con este correo electrónico.")

        customer = Customer(
            id=str(uuid.uuid4()),
            email=dto.email,
            business_name=dto.business_name,
            cuit=cuit_vo,
            phone=dto.phone,
            address=dto.address,
            city=dto.city,
            role=UserRole.B2B_CLIENT,
            is_approved=True,
            hashed_password=self.hasher.hash(dto.password)
        )

        await self.customer_repo.save(customer)
        return customer
