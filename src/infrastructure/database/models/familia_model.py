from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infrastructure.database.connection import Base

if TYPE_CHECKING:
    from src.infrastructure.database.models.categoria_model import CategoriaModel
    from src.infrastructure.database.models.producto_model import ProductoModel


class FamiliaModel(Base):
    """
    Tabla: familias
    Subfamilia / división técnica dentro de una categoría (ej: Calzado de Seguridad, Mangueras Moldeadas).
    """
    __tablename__ = "familias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    categoria_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("categorias.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    slug: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    rubro: Mapped[str] = mapped_column(String(30), default="AMBOS", nullable=False, index=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relaciones
    categoria: Mapped[CategoriaModel | None] = relationship(
        "CategoriaModel",
        back_populates="familias"
    )
    productos: Mapped[list[ProductoModel]] = relationship(
        "ProductoModel",
        back_populates="familia"
    )
