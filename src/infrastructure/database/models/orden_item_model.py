from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infrastructure.database.connection import Base

if TYPE_CHECKING:
    from src.infrastructure.database.models.orden_model import OrdenModel
    from src.infrastructure.database.models.producto_model import ProductoModel


class OrdenItemModel(Base):
    """
    Tabla: orden_items
    Renglón o ítem individual de una orden de pedido mayorista.
    """
    __tablename__ = "orden_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    orden_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ordenes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    producto_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("productos.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    producto_sku: Mapped[str | None] = mapped_column(String(50), nullable=True)
    producto_nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    precio_unitario: Mapped[float] = mapped_column(Float, nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)

    # Relaciones
    orden: Mapped[OrdenModel] = relationship(
        "OrdenModel",
        back_populates="items"
    )
    producto: Mapped[ProductoModel | None] = relationship(
        "ProductoModel"
    )
