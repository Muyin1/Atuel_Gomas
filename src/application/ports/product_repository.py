from abc import ABC, abstractmethod
from src.domain.entities.product import Product
from src.domain.entities.product_category import ProductCategory
from src.domain.entities.category_item import CategoryItem
from src.domain.entities.family_item import FamilyItem
from src.domain.entities.business_line import BusinessLine


class IProductRepository(ABC):
    @abstractmethod
    async def get_by_id(self, product_id: str) -> Product | None:
        pass

    @abstractmethod
    async def get_by_ids(self, product_ids: list[str]) -> list[Product]:
        pass

    @abstractmethod
    async def get_by_sku(self, sku: str) -> Product | None:
        pass


    @abstractmethod
    async def search(
        self,
        query: str | None = None,
        category: ProductCategory | str | None = None,
        family: str | None = None,
        vehicle_brand: str | None = None,
        vehicle_model: str | None = None,
        page: int = 1,
        page_size: int = 24
    ) -> list[Product]:
        pass

    @abstractmethod
    async def count(
        self,
        query: str | None = None,
        category: ProductCategory | str | None = None,
        family: str | None = None,
        vehicle_brand: str | None = None,
        vehicle_model: str | None = None
    ) -> int:
        pass

    @abstractmethod
    async def save(self, product: Product) -> None:
        pass

    @abstractmethod
    async def get_categories(self, rubro: BusinessLine | str | None = None) -> list[CategoryItem]:
        pass

    @abstractmethod
    async def get_families(
        self,
        category_id_or_slug: int | str | None = None,
        rubro: BusinessLine | str | None = None
    ) -> list[FamilyItem]:
        pass
