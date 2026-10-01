from dataclasses import dataclass, field
from src.domain.value_objects.dimensions import Dimensions
from src.domain.value_objects.money import Money
from src.domain.entities.product_category import ProductCategory
from src.domain.entities.user_role import UserRole
from src.domain.entities.vehicle_compatibility import VehicleCompatibility
from src.domain.entities.business_line import BusinessLine


@dataclass
class Product:
    id: str
    sku: str                          # Código Atuel Gomas (ej: AG-1045)
    oem_code: str                     # Código original de fábrica / cruce
    name: str
    category: ProductCategory
    description: str
    dimensions: Dimensions
    base_price: Money                 # Precio lista público / consumidor
    wholesale_price: Money            # Precio mayorista B2B (ferreterías / repuesteras)
    stock: int
    image_url: str
    compatibilities: list[VehicleCompatibility] = field(default_factory=list)
    business_line: BusinessLine = BusinessLine.AUTOPARTES
    family_id: int | None = None
    family_name: str | None = None
    is_active: bool = True

    def calculate_price_for_role(self, role: UserRole) -> Money:
        """Regla de negocio pura: cálculo de precio según perfil"""
        if role in (UserRole.B2B_CLIENT, UserRole.SALES_AGENT, UserRole.ADMIN):
            return self.wholesale_price
        return self.base_price

    def has_stock(self, quantity: int = 1) -> bool:
        return self.stock >= quantity
