from abc import ABC, abstractmethod
from src.domain.entities.order import Order


class IOrderRepository(ABC):
    @abstractmethod
    async def create_order(self, order: Order) -> Order:
        pass

    @abstractmethod
    async def get_by_id(self, order_id: str) -> Order | None:
        pass

    @abstractmethod
    async def get_by_customer(self, customer_id: str) -> list[Order]:
        pass

    @abstractmethod
    async def get_by_sales_agent(self, sales_agent_id: str) -> list[Order]:
        pass

