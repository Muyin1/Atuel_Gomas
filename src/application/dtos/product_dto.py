from pydantic import BaseModel
from src.domain.entities.product_category import ProductCategory
from src.domain.entities.user_role import UserRole


class ProductSearchDTO(BaseModel):
    query: str | None = None
    category: ProductCategory | None = None
    vehicle_brand: str | None = None
    vehicle_model: str | None = None
    role: UserRole = UserRole.PUBLIC


class ProductSummaryDTO(BaseModel):
    id: str
    sku: str
    oem_code: str
    name: str
    category: str
    dimensions: str
    price_formatted: str
    is_wholesale: bool
    stock: int
    image_url: str
    compatibilities_summary: str
