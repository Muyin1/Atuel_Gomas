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
