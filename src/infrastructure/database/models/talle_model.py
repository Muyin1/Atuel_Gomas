from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infrastructure.database.connection import Base

if TYPE_CHECKING:
    from src.infrastructure.database.models.variante_model import VarianteModel


class TalleModel(Base):
    """
    Tabla: talles_medidas
    Catálogo de talles, números y medidas dimensionales de variantes (ej: 42, Nro. 8, 1/2", 3mm x 1m).
    """
    __tablename__ = "talles_medidas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    valor: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    unidad_medida: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Relaciones
    variantes: Mapped[list[VarianteModel]] = relationship(
        "VarianteModel",
        back_populates="talle"
    )
