from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infrastructure.database.connection import Base

if TYPE_CHECKING:
    from src.infrastructure.database.models.variante_model import VarianteModel


class MaterialModel(Base):
    """
    Tabla: materiales
    Catálogo de materiales y compuestos técnicos (ej: Cuero Descarne, EPDM, Nitrilo, Látex, PVC, Acero Inoxidable).
    """
    __tablename__ = "materiales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    propiedades_tecnicas: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relaciones
    variantes: Mapped[list[VarianteModel]] = relationship(
        "VarianteModel",
        back_populates="material"
    )
