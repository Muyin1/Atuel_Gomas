from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.application.ports.order_repository import IOrderRepository
from src.domain.entities.order import Order
from src.domain.entities.order_item import OrderItem
from src.domain.entities.order_status import OrderStatus
from src.domain.value_objects.money import Money
from src.infrastructure.database.connection import SessionLocal
from src.infrastructure.database.models import OrdenItemModel, OrdenModel


def _normalize_order_status(status_str: str | None) -> OrderStatus:
    if not status_str:
        return OrderStatus.PENDING_APPROVAL
    clean = status_str.strip().upper()
    try:
        return OrderStatus(clean)
    except ValueError:
        return OrderStatus.PENDING_APPROVAL


class SqlAlchemyOrderRepository(IOrderRepository):
    """
    Repositorio de infraestructura para órdenes y pedidos mayoristas conectados a SQLAlchemy 2.0.
    Implementa IOrderRepository garantizando atomicidad transaccional y persistencia de renglones.
    """

    def __init__(self, session_factory=SessionLocal):
        self._session_factory = session_factory

    def _map_to_entity(self, model: OrdenModel) -> Order:
        items = [
            OrderItem(
                product_id=str(item.producto_id or ""),
                product_sku=item.producto_sku or "",
                product_name=item.producto_nombre,
                unit_price=Money(amount=float(item.precio_unitario)),
                quantity=int(item.cantidad),
            )
            for item in model.items
        ]

        sales_agent = getattr(model, "sales_agent_id", None)
        return Order(
            id=model.id,
            customer_id=model.cliente_id,
            customer_name=model.cliente_nombre,
            items=items,
            status=_normalize_order_status(model.estado),
            notes=model.notes or "" if hasattr(model, "notes") else (model.notas or ""),
            sales_agent_id=sales_agent,
            created_at=model.created_at,
        )

    async def create_order(self, order: Order) -> Order:
        with self._session_factory() as session:
            orden_model = OrdenModel(
                id=order.id,
                cliente_id=order.customer_id,
                cliente_nombre=order.customer_name,
                estado=order.status.value if hasattr(order.status, "value") else str(order.status),
                total=float(order.total.amount),
                notas=order.notes,
                sales_agent_id=order.sales_agent_id,
                created_at=order.created_at,
            )

            item_models = []
            for item in order.items:
                prod_int_id = int(item.product_id) if item.product_id.isdigit() else None
                item_models.append(
                    OrdenItemModel(
                        orden_id=order.id,
                        producto_id=prod_int_id,
                        producto_sku=item.product_sku,
                        producto_nombre=item.product_name,
                        precio_unitario=float(item.unit_price.amount),
                        cantidad=int(item.quantity),
                        subtotal=float(item.subtotal.amount),
                    )
                )

            orden_model.items = item_models
            session.add(orden_model)
            session.commit()

            return order

    async def get_by_id(self, order_id: str) -> Order | None:
        with self._session_factory() as session:
            stmt = (
                select(OrdenModel)
                .options(selectinload(OrdenModel.items))
                .filter(OrdenModel.id == order_id)
            )
            model = session.scalars(stmt).first()
            if not model:
                return None
            return self._map_to_entity(model)

    async def get_by_customer(self, customer_id: str) -> list[Order]:
        with self._session_factory() as session:
            stmt = (
                select(OrdenModel)
                .options(selectinload(OrdenModel.items))
                .filter(OrdenModel.cliente_id == customer_id)
                .order_by(OrdenModel.created_at.desc())
            )
            models = session.scalars(stmt).all()
            return [self._map_to_entity(m) for m in models]

    async def get_by_sales_agent(self, sales_agent_id: str) -> list[Order]:
        """
        Obtiene todos los pedidos correspondientes a los clientes asignados al vendedor.
        """
        with self._session_factory() as session:
            stmt = (
                select(OrdenModel)
                .options(selectinload(OrdenModel.items))
                .filter(OrdenModel.sales_agent_id == sales_agent_id)
                .order_by(OrdenModel.created_at.desc())
            )
            models = session.scalars(stmt).all()
            return [self._map_to_entity(m) for m in models]

