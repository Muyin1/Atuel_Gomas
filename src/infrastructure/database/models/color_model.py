from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infrastructure.database.connection import Base

if TYPE_CHECKING:
    from src.infrastructure.database.models.variante_model import VarianteModel


class ColorModel(Base):
    """
    Tabla: colores
    Catálogo de colores para productos y variantes técnicas (ej: Blanco, Negro, Amarillo, Azul).
    """
    __tablename__ = "colores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    codigo_hex: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Relaciones
    variantes: Mapped[list[VarianteModel]] = relationship(
        "VarianteModel",
        back_populates="color"
    )
