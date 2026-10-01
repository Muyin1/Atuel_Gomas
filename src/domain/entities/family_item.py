from dataclasses import dataclass
from src.domain.entities.business_line import BusinessLine


@dataclass
class FamilyItem:
    id: int
    name: str
    value: str
    slug: str
    category_id: int
    category_name: str
    rubro: BusinessLine = BusinessLine.AMBOS
    product_count: int = 0

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"<FamilyItem id={self.id} name='{self.name}' value='{self.value}' cat_id={self.category_id} rubro='{self.rubro}' count={self.product_count}>"

    def __eq__(self, other) -> bool:
        if isinstance(other, FamilyItem):
            return self.name == other.name or self.id == other.id
        if hasattr(other, "name"):
            return self.name == other.name
        if hasattr(other, "value"):
            return self.value == other.value
        if isinstance(other, str):
            return self.name == other or self.value == other or self.slug == other
        return False
