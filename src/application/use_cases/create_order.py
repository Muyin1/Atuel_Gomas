import uuid
from src.application.ports.order_repository import IOrderRepository
from src.application.ports.product_repository import IProductRepository
from src.application.ports.customer_repository import ICustomerRepository
from src.application.dtos.order_dto import CreateOrderDTO
from src.domain.entities.order import Order
from src.domain.entities.order_item import OrderItem
from src.domain.entities.order_status import OrderStatus
from src.domain.exceptions.domain_exceptions import ProductNotFoundError, InsufficientStockError


class CreateOrderUseCase:
    def __init__(
        self,
        order_repo: IOrderRepository,
        product_repo: IProductRepository,
        customer_repo: ICustomerRepository
    ):
        self.order_repo = order_repo
        self.product_repo = product_repo
        self.customer_repo = customer_repo

    async def execute(self, dto: CreateOrderDTO) -> Order:
        customer = await self.customer_repo.get_by_id(dto.customer_id)
        if not customer:
            raise ValueError("Cliente no encontrado para emitir la orden")

        order_items: list[OrderItem] = []

        for item_dto in dto.items:
            product = await self.product_repo.get_by_id(item_dto.product_id)
            if not product:
                raise ProductNotFoundError(f"Producto {item_dto.product_id} no encontrado")

            if not product.has_stock(item_dto.quantity):
                raise InsufficientStockError(f"Stock insuficiente para {product.name}. Disponible: {product.stock}")

            price = product.calculate_price_for_role(customer.role)

            order_items.append(
                OrderItem(
                    product_id=product.id,
                    product_sku=product.sku,
                    product_name=product.name,
                    unit_price=price,
                    quantity=item_dto.quantity
                )
            )

        order = Order(
            id=f"ORD-{uuid.uuid4().hex[:8].upper()}",
            customer_id=customer.id,
            customer_name=customer.business_name,
            items=order_items,
            status=OrderStatus.PENDING_APPROVAL,
            notes=dto.notes,
            sales_agent_id=customer.sales_agent_id
        )


        return await self.order_repo.create_order(order)
