from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infrastructure.database.connection import Base

if TYPE_CHECKING:
    from src.infrastructure.database.models.variante_model import VarianteModel


class PunteraModel(Base):
    """
    Tabla: punteras_seguridad
    Catálogo de punteras de protección para calzado de seguridad (ej: Acero, Aluminio, Dieléctrica, Sin puntera).
    """
    __tablename__ = "punteras_seguridad"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tipo_puntera: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relaciones
    variantes: Mapped[list[VarianteModel]] = relationship(
        "VarianteModel",
        back_populates="puntera"
    )
