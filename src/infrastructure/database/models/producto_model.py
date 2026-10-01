from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infrastructure.database.connection import Base

if TYPE_CHECKING:
    from src.infrastructure.database.models.categoria_model import CategoriaModel
    from src.infrastructure.database.models.familia_model import FamiliaModel
    from src.infrastructure.database.models.variante_model import VarianteModel
    from src.infrastructure.database.models.compatibilidad_vehicular_model import CompatibilidadVehicularModel


class ProductoModel(Base):
    """
    Tabla: productos
    Catálogo central de productos de Atuel Gomas.
    Admite artículos individuales, artículos con variantes técnicas y compatibilidad vehicular.
    """
    __tablename__ = "productos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    codigo_oem: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)

    categoria_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("categorias.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    familia_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("familias.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    precio_base: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    precio_mayorista_b2b: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    imagen_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rubro: Mapped[str] = mapped_column(String(30), default="AUTOPARTES", nullable=False, index=True)

    # Medidas técnicas opcionales (mangueras, burletes, etc.)
    diametro_interior_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    diametro_exterior_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    largo_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    espesor_mm: Mapped[float | None] = mapped_column(Float, nullable=True)

    activo: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relaciones
    categoria: Mapped[CategoriaModel | None] = relationship(
        "CategoriaModel",
        back_populates="productos"
    )
    familia: Mapped[FamiliaModel | None] = relationship(
        "FamiliaModel",
        back_populates="productos"
    )
    variantes: Mapped[list[VarianteModel]] = relationship(
        "VarianteModel",
        back_populates="producto",
        cascade="all, delete-orphan"
    )
    compatibilidades: Mapped[list[CompatibilidadVehicularModel]] = relationship(
        "CompatibilidadVehicularModel",
        back_populates="producto",
        cascade="all, delete-orphan"
    )
