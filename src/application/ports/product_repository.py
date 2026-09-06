from abc import ABC, abstractmethod
from src.domain.entities.product import Product
from src.domain.entities.product_category import ProductCategory


class IProductRepository(ABC):
    @abstractmethod
    async def get_by_id(self, product_id: str) -> Product | None:
        pass

    @abstractmethod
    async def get_by_sku(self, sku: str) -> Product | None:
        pass

    @abstractmethod
    async def search(
        self,
        query: str | None = None,
        category: ProductCategory | None = None,
        vehicle_brand: str | None = None,
        vehicle_model: str | None = None
    ) -> list[Product]:
        pass

    @abstractmethod
    async def save(self, product: Product) -> None:
        pass

    @abstractmethod
    async def get_categories(self) -> list[ProductCategory]:
        pass
