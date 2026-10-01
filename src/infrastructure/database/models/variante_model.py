from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infrastructure.database.connection import Base

if TYPE_CHECKING:
    from src.infrastructure.database.models.producto_model import ProductoModel
    from src.infrastructure.database.models.talle_model import TalleModel
    from src.infrastructure.database.models.color_model import ColorModel
    from src.infrastructure.database.models.material_model import MaterialModel
    from src.infrastructure.database.models.puntera_model import PunteraModel


class VarianteModel(Base):
    """
    Tabla: producto_variantes
    Tabla puente M:N para variantes dimensionales y de composición técnica de cada producto
    (talles, colores, materiales, punteras, stock y precio específico).
    """
    __tablename__ = "producto_variantes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    producto_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("productos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    talle_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("talles_medidas.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    color_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("colores.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    material_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("materiales.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    puntera_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("punteras_seguridad.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    codigo_barras: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    sku_variante: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    stock_variante: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    precio_especifico: Mapped[float | None] = mapped_column(Float, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relaciones
    producto: Mapped[ProductoModel] = relationship(
        "ProductoModel",
        back_populates="variantes"
    )
    talle: Mapped[TalleModel | None] = relationship(
        "TalleModel",
        back_populates="variantes"
    )
    color: Mapped[ColorModel | None] = relationship(
        "ColorModel",
        back_populates="variantes"
    )
    material: Mapped[MaterialModel | None] = relationship(
        "MaterialModel",
        back_populates="variantes"
    )
    puntera: Mapped[PunteraModel | None] = relationship(
        "PunteraModel",
        back_populates="variantes"
    )
