from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infrastructure.database.connection import Base

if TYPE_CHECKING:
    from src.infrastructure.database.models.producto_model import ProductoModel


class CompatibilidadVehicularModel(Base):
    """
    Tabla: producto_compatibilidad_vehicular
    Compatibilidad automotor de autopartes y mangueras con marcas, modelos, motorizaciones y años.
    """
    __tablename__ = "producto_compatibilidad_vehicular"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    producto_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("productos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    marca: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    modelo: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    motorizacion: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    anio_desde: Mapped[int | None] = mapped_column(Integer, nullable=True)
    anio_hasta: Mapped[int | None] = mapped_column(Integer, nullable=True)
    anios_texto: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relaciones
    producto: Mapped[ProductoModel] = relationship(
        "ProductoModel",
        back_populates="compatibilidades"
    )
