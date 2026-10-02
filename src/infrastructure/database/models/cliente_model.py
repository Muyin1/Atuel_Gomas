from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infrastructure.database.connection import Base

if TYPE_CHECKING:
    from src.infrastructure.database.models.orden_model import OrdenModel


class ClienteModel(Base):
    """
    Tabla: clientes
    Registro de clientes comerciales B2B (ferreterías, repuesteras) y usuarios del sistema.
    """
    __tablename__ = "clientes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    razon_social: Mapped[str] = mapped_column(String(255), nullable=False)
    cuit: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    telefono: Mapped[str | None] = mapped_column(String(50), nullable=True)
    direccion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ciudad: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rol: Mapped[str] = mapped_column(String(30), default="b2b_client", nullable=False)
    rubro: Mapped[str] = mapped_column(String(30), default="AMBOS", nullable=False, index=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    markup_percent: Mapped[float] = mapped_column(Float, default=30.0, nullable=False)
    sales_agent_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("clientes.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)



    # Relaciones
    ordenes: Mapped[list[OrdenModel]] = relationship(
        "OrdenModel",
        back_populates="cliente"
    )
