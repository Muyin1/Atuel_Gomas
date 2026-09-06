from src.application.ports.order_repository import IOrderRepository
from src.domain.entities.order import Order


class MemoryOrderRepository(IOrderRepository):
    def __init__(self):
        self._orders: dict[str, Order] = {}

    async def create_order(self, order: Order) -> Order:
        self._orders[order.id] = order
        return order

    async def get_by_id(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)

    async def get_by_customer(self, customer_id: str) -> list[Order]:
        return [o for o in self._orders.values() if o.customer_id == customer_id]
