from src.application.ports.customer_repository import ICustomerRepository
from src.domain.entities.customer import Customer


class MemoryCustomerRepository(ICustomerRepository):
    def __init__(self):
        self._customers: dict[str, Customer] = {}

    async def get_by_id(self, customer_id: str) -> Customer | None:
        return self._customers.get(customer_id)

    async def get_by_cuit(self, cuit_str: str) -> Customer | None:
        for c in self._customers.values():
            if c.cuit.value == cuit_str:
                return c
        return None

    async def get_by_email(self, email: str) -> Customer | None:
        for c in self._customers.values():
            if c.email.lower() == email.lower():
                return c
        return None

    async def save(self, customer: Customer) -> None:
        self._customers[customer.id] = customer
