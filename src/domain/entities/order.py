from dataclasses import dataclass, field
from datetime import datetime
from src.domain.value_objects.money import Money
from src.domain.entities.order_item import OrderItem
from src.domain.entities.order_status import OrderStatus


@dataclass
class Order:
    id: str
    customer_id: str
    customer_name: str
    items: list[OrderItem]
    status: OrderStatus = OrderStatus.PENDING_APPROVAL
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def total(self) -> Money:
        total_amount = sum(item.subtotal.amount for item in self.items)
        return Money(amount=total_amount)
