from abc import ABC, abstractmethod
from src.domain.entities.customer import Customer


class ICustomerRepository(ABC):
    @abstractmethod
    async def get_by_id(self, customer_id: str) -> Customer | None:
        pass

    @abstractmethod
    async def get_by_cuit(self, cuit_str: str) -> Customer | None:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Customer | None:
        pass

    @abstractmethod
    async def save(self, customer: Customer) -> None:
        pass

    @abstractmethod
    async def update_profile(
        self,
        customer_id: str,
        markup_percent: float,
        phone: str | None = None,
        address: str | None = None
    ) -> Customer:
        pass

    @abstractmethod
    async def get_sales_agents(self) -> list[Customer]:
        pass

    @abstractmethod
    async def get_customers_by_sales_agent(self, sales_agent_id: str) -> list[Customer]:
        pass

    @abstractmethod
    async def assign_sales_agent(self, customer_id: str, sales_agent_id: str | None) -> None:
        pass


