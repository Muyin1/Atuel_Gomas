from src.application.ports.product_repository import IProductRepository
from src.domain.entities.product import Product
from src.domain.entities.user_role import UserRole


class GetProductDetailUseCase:
    def __init__(self, product_repo: IProductRepository):
        self.product_repo = product_repo

    async def execute(self, product_id: str, role: UserRole = UserRole.PUBLIC) -> Product | None:
        return await self.product_repo.get_by_id(product_id)
