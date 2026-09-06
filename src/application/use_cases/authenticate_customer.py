from src.application.ports.customer_repository import ICustomerRepository
from src.application.ports.password_hasher import IPasswordHasher
from src.application.dtos.auth_dto import LoginDTO
from src.domain.entities.customer import Customer
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
