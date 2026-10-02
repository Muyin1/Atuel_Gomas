from src.application.dtos.auth_dto import AssignSalesAgentDTO
from src.application.ports.customer_repository import ICustomerRepository
from src.domain.entities.customer import Customer
from src.domain.entities.user_role import UserRole
from src.domain.exceptions.domain_exceptions import UnauthorizedActionError


class ManageSalesAgentUseCase:
    """
    Caso de uso para la administración y consulta de vendedores (SALES_AGENT) y cartera de clientes:
    - Listar vendedores activos (para Administradores y paneles internos).
    - Consultar clientes asignados a un vendedor.
    - Asignar o reasignar un cliente B2B a un vendedor comercial (protegido para ADMIN).
    """

    def __init__(self, customer_repo: ICustomerRepository):
        self.customer_repo = customer_repo

    async def get_sales_agents(self) -> list[Customer]:
        """Retorna todos los usuarios con rol vendedor (SALES_AGENT)"""
        return await self.customer_repo.get_sales_agents()

    async def get_portfolio(self, sales_agent_id: str) -> list[Customer]:
        """Retorna la cartera de clientes asignados al vendedor"""
        return await self.customer_repo.get_customers_by_sales_agent(sales_agent_id)

    async def assign_agent(self, dto: AssignSalesAgentDTO, requester_role: UserRole | str | None = None) -> None:
        """Asigna un cliente a un vendedor. Operación protegida exclusiva para ADMIN"""
        role_val = None
        if isinstance(requester_role, UserRole):
            role_val = requester_role
        elif isinstance(requester_role, str):
            try:
                role_val = UserRole(requester_role.upper())
            except ValueError:
                role_val = None

        if role_val != UserRole.ADMIN:
            raise UnauthorizedActionError(
                "Operación no autorizada: Solo el Administrador puede asignar o reasignar la cartera de clientes a los vendedores."
            )

        # Si se especificó un vendedor, validar que exista y tenga rol SALES_AGENT
        if dto.sales_agent_id:
            agent = await self.customer_repo.get_by_id(dto.sales_agent_id)
            if not agent:
                raise ValueError(f"Vendedor con ID '{dto.sales_agent_id}' no encontrado.")
            if agent.role != UserRole.SALES_AGENT:
                raise ValueError(f"El usuario '{agent.business_name}' no posee el rol de vendedor (SALES_AGENT).")

        await self.customer_repo.assign_sales_agent(dto.customer_id, dto.sales_agent_id)
