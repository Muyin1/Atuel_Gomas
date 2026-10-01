from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infrastructure.database.connection import Base

if TYPE_CHECKING:
    from src.infrastructure.database.models.familia_model import FamiliaModel
    from src.infrastructure.database.models.producto_model import ProductoModel


class CategoriaModel(Base):
    """
    Tabla: categorias
    Categoría principal del catálogo de Atuel Gomas (ej: Mangueras Automotor, Pisos, EPP).
    """
    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    slug: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    rubro: Mapped[str] = mapped_column(String(30), default="AMBOS", nullable=False, index=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relaciones
    familias: Mapped[list[FamiliaModel]] = relationship(
        "FamiliaModel",
        back_populates="categoria",
        cascade="all, delete-orphan"
    )
    productos: Mapped[list[ProductoModel]] = relationship(
        "ProductoModel",
        back_populates="categoria"
    )
