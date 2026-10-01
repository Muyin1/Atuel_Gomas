from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infrastructure.database.connection import Base

if TYPE_CHECKING:
    from src.infrastructure.database.models.cliente_model import ClienteModel
    from src.infrastructure.database.models.orden_item_model import OrdenItemModel


class OrdenModel(Base):
    """
    Tabla: ordenes
    Encabezado de orden de pedido mayorista generada por clientes B2B.
    """
    __tablename__ = "ordenes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    cliente_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("clientes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    cliente_nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    estado: Mapped[str] = mapped_column(String(50), default="PENDIENTE_APROBACION", nullable=False)
    total: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relaciones
    cliente: Mapped[ClienteModel] = relationship(
        "ClienteModel",
        back_populates="ordenes"
    )
    items: Mapped[list[OrdenItemModel]] = relationship(
        "OrdenItemModel",
        back_populates="orden",
        cascade="all, delete-orphan"
    )
