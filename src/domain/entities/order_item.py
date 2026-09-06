from dataclasses import dataclass
from src.domain.value_objects.money import Money


@dataclass
class OrderItem:
    product_id: str
    product_sku: str
    product_name: str
    unit_price: Money
    quantity: int

    @property
    def subtotal(self) -> Money:
        return Money(amount=self.unit_price.amount * self.quantity)
