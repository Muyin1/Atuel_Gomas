from src.application.dtos.auth_dto import UpdateProfileDTO
from src.application.ports.customer_repository import ICustomerRepository
from src.domain.entities.customer import Customer


class UpdateCustomerProfileUseCase:
    """
    Caso de uso para actualizar la configuración de perfil del cliente comercial B2B:
    - Margen de ganancia comercial para mostrador (markup_percent)
    - Teléfono de contacto
    - Dirección comercial
    """

    def __init__(self, customer_repo: ICustomerRepository):
        self.customer_repo = customer_repo

    async def execute(self, customer_id: str, dto: UpdateProfileDTO) -> Customer:
        if dto.markup_percent < 0:
            raise ValueError("El margen de ganancia no puede ser negativo.")

        return await self.customer_repo.update_profile(
            customer_id=customer_id,
            markup_percent=dto.markup_percent,
            phone=dto.phone,
            address=dto.address,
        )
