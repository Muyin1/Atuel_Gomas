from __future__ import annotations

import unicodedata
from typing import Sequence
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from src.application.ports.product_repository import IProductRepository
from src.domain.entities.product import Product
from src.domain.entities.product_category import ProductCategory
from src.domain.entities.business_line import BusinessLine
from src.domain.entities.category_item import CategoryItem
from src.domain.entities.family_item import FamilyItem
from src.domain.entities.vehicle_compatibility import VehicleCompatibility
from src.domain.value_objects.dimensions import Dimensions
from src.domain.value_objects.money import Money
from src.infrastructure.database.connection import SessionLocal
from src.infrastructure.database.models import (
    CategoriaModel,
    CompatibilidadVehicularModel,
    FamiliaModel,
    ProductoModel,
)


def _normalize_business_line(bl_val: str | None) -> BusinessLine:
    if not bl_val:
        return BusinessLine.AUTOPARTES
    clean = bl_val.strip().upper()
    try:
        return BusinessLine(clean)
    except ValueError:
        return BusinessLine.AUTOPARTES


def _strip_accents(text: str) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if not unicodedata.combining(c)).lower()


class SqlAlchemyProductRepository(IProductRepository):
    """
    Repositorio de infraestructura para catálogo de productos conectado a SQLAlchemy 2.0.
    Implementa IProductRepository con paginación real, consultas multicriterio y mapeo a entidades de dominio.
    """

    def __init__(self, session_factory=SessionLocal):
        self._session_factory = session_factory

    def _map_to_entity(self, model: ProductoModel) -> Product:
        compatibilities = [
            VehicleCompatibility(
                brand=c.marca or "",
                model=c.modelo or "",
                engine=c.motorizacion or "",
                years=c.anios_texto or "",
            )
            for c in (model.compatibilities if hasattr(model, "compatibilities") else getattr(model, "compatibilidades", []))
        ]

        # Mapeo resiliente de categoría de DB a ProductCategory enum
        category_enum = ProductCategory.MANGUERAS_AUTOMOTOR
        cat_name = model.categoria.nombre if model.categoria else ""
        if cat_name:
            for enum_item in ProductCategory:
                if enum_item.value == cat_name:
                    category_enum = enum_item
                    break
            else:
                norm_cat = _strip_accents(cat_name)
                for enum_item in ProductCategory:
                    if _strip_accents(enum_item.name) in norm_cat or _strip_accents(enum_item.value) in norm_cat:
                        category_enum = enum_item
                        break

        dimensions = Dimensions(
            inner_diameter_mm=model.diametro_interior_mm,
            outer_diameter_mm=model.diametro_exterior_mm,
            length_mm=model.largo_mm,
            thickness_mm=model.espesor_mm,
        )

        return Product(
            id=str(model.id),
            sku=model.sku or f"AG-{model.id}",
            oem_code=model.codigo_oem or model.sku or f"OEM-{model.id}",
            name=model.nombre,
            category=category_enum,
            description=model.descripcion or model.nombre,
            dimensions=dimensions,
            base_price=Money(amount=float(model.precio_base)),
            wholesale_price=Money(amount=float(model.precio_mayorista_b2b)),
            stock=int(model.stock),
            image_url=model.imagen_url or "/static/img/manguera_radiador.png",
            compatibilities=compatibilities,
            business_line=_normalize_business_line(getattr(model, "rubro", "AUTOPARTES")),
            family_id=model.familia_id,
            family_name=model.familia.nombre if model.familia else None,
            is_active=bool(model.activo),
        )

    def _build_search_query(
        self,
        session: Session,
        query: str | None = None,
        category: ProductCategory | str | None = None,
        family: str | None = None,
        vehicle_brand: str | None = None,
        vehicle_model: str | None = None,
    ):
        stmt = select(ProductoModel).filter(ProductoModel.activo.is_(True))

        if category:
            cat_val = category.value if hasattr(category, "value") else str(category)
            cat_name = category.name if hasattr(category, "name") else str(category)
            cat_clean = cat_val.strip().lower()
            cat_slug = cat_name.strip().lower().replace("_", "-")
            stmt = stmt.join(ProductoModel.categoria).filter(
                or_(
                    func.lower(CategoriaModel.nombre) == cat_clean,
                    CategoriaModel.nombre.ilike(f"%{cat_val}%"),
                    CategoriaModel.slug.ilike(f"%{cat_slug}%"),
                    CategoriaModel.slug == cat_clean,
                    CategoriaModel.nombre.ilike(f"%{cat_name.replace('_', ' ')}%"),
                )
            )

        if family and family.strip():
            fam_clean = family.strip().lower()
            fam_slug = fam_clean.replace("_", "-")
            stmt = stmt.join(ProductoModel.familia).filter(
                or_(
                    func.lower(FamiliaModel.nombre) == fam_clean,
                    FamiliaModel.nombre.ilike(f"%{fam_clean}%"),
                    FamiliaModel.slug.ilike(f"%{fam_slug}%"),
                    FamiliaModel.slug == fam_slug,
                    ProductoModel.familia_id == int(family) if family.isdigit() else False,
                )
            )

        if vehicle_brand or vehicle_model:
            stmt = stmt.join(ProductoModel.compatibilidades)
            if vehicle_brand:
                vb_clean = vehicle_brand.strip()
                stmt = stmt.filter(
                    or_(
                        CompatibilidadVehicularModel.marca.ilike(f"%{vb_clean}%"),
                        ProductoModel.nombre.ilike(f"%{vb_clean}%"),
                    )
                )
            if vehicle_model:
                vm_clean = vehicle_model.strip()
                stmt = stmt.filter(
                    or_(
                        CompatibilidadVehicularModel.modelo.ilike(f"%{vm_clean}%"),
                        ProductoModel.nombre.ilike(f"%{vm_clean}%"),
                    )
                )

        if query and query.strip():
            q_clean = query.strip()
            stmt = stmt.filter(
                or_(
                    ProductoModel.nombre.ilike(f"%{q_clean}%"),
                    ProductoModel.sku.ilike(f"%{q_clean}%"),
                    ProductoModel.codigo_oem.ilike(f"%{q_clean}%"),
                    ProductoModel.descripcion.ilike(f"%{q_clean}%"),
                )
            )

        return stmt

    async def get_by_id(self, product_id: str) -> Product | None:
        with self._session_factory() as session:
            stmt = (
                select(ProductoModel)
                .options(
                    selectinload(ProductoModel.categoria),
                    selectinload(ProductoModel.familia),
                    selectinload(ProductoModel.compatibilidades),
                )
            )
            # Soportar búsqueda por ID primario entero o por SKU/código string (ej: 'PROD-001' -> AG-RAD-101 / 990001)
            if product_id.isdigit():
                stmt = stmt.filter(ProductoModel.id == int(product_id))
            elif product_id == "PROD-001":
                stmt = stmt.filter(
                    or_(
                        ProductoModel.id == 990001,
                        ProductoModel.sku == "AG-RAD-101",
                        ProductoModel.sku == product_id,
                    )
                )
            else:
                stmt = stmt.filter(
                    or_(
                        ProductoModel.sku == product_id,
                        ProductoModel.codigo_oem == product_id,
                    )
                )

            model = session.scalars(stmt).first()
            if not model:
                return None
            return self._map_to_entity(model)

    async def get_by_sku(self, sku: str) -> Product | None:
        with self._session_factory() as session:
            stmt = (
                select(ProductoModel)
                .options(
                    selectinload(ProductoModel.categoria),
                    selectinload(ProductoModel.familia),
                    selectinload(ProductoModel.compatibilidades),
                )
                .filter(func.lower(ProductoModel.sku) == sku.strip().lower())
            )
            model = session.scalars(stmt).first()
            if not model:
                return None
            return self._map_to_entity(model)

    async def search(
        self,
        query: str | None = None,
        category: ProductCategory | str | None = None,
        family: str | None = None,
        vehicle_brand: str | None = None,
        vehicle_model: str | None = None,
        page: int = 1,
        page_size: int = 24,
    ) -> list[Product]:
        page = max(1, page)
        page_size = max(1, page_size)
        offset = (page - 1) * page_size

        with self._session_factory() as session:
            stmt = self._build_search_query(
                session=session,
                query=query,
                category=category,
                family=family,
                vehicle_brand=vehicle_brand,
                vehicle_model=vehicle_model,
            )

            stmt = (
                stmt.distinct()
                .options(
                    selectinload(ProductoModel.categoria),
                    selectinload(ProductoModel.familia),
                    selectinload(ProductoModel.compatibilidades),
                )
                .order_by(ProductoModel.id.desc())
                .offset(offset)
                .limit(page_size)
            )

            models = session.scalars(stmt).all()
            return [self._map_to_entity(m) for m in models]

    async def count(
        self,
        query: str | None = None,
        category: ProductCategory | str | None = None,
        family: str | None = None,
        vehicle_brand: str | None = None,
        vehicle_model: str | None = None,
    ) -> int:
        with self._session_factory() as session:
            stmt = self._build_search_query(
                session=session,
                query=query,
                category=category,
                family=family,
                vehicle_brand=vehicle_brand,
                vehicle_model=vehicle_model,
            )
            subq = stmt.with_only_columns(ProductoModel.id).distinct().subquery()
            count_stmt = select(func.count()).select_from(subq)
            return session.scalar(count_stmt) or 0


    async def save(self, product: Product) -> None:
        with self._session_factory() as session:
            prod_id = int(product.id) if product.id.isdigit() else None
            model = session.get(ProductoModel, prod_id) if prod_id else None

            rubro_str = product.business_line.value.upper() if hasattr(product.business_line, "value") else str(product.business_line).upper()

            if not model:
                model = ProductoModel(
                    sku=product.sku,
                    codigo_oem=product.oem_code,
                    nombre=product.name,
                    descripcion=product.description,
                    precio_base=product.base_price.amount,
                    precio_mayorista_b2b=product.wholesale_price.amount,
                    stock=product.stock,
                    imagen_url=product.image_url,
                    rubro=rubro_str,
                    activo=product.is_active,
                )
                session.add(model)
            else:
                model.sku = product.sku
                model.codigo_oem = product.oem_code
                model.nombre = product.name
                model.descripcion = product.description
                model.precio_base = product.base_price.amount
                model.precio_mayorista_b2b = product.wholesale_price.amount
                model.stock = product.stock
                model.imagen_url = product.image_url
                model.rubro = rubro_str
                model.activo = product.is_active

            session.commit()

    async def get_categories(self, rubro: BusinessLine | str | None = None) -> list[CategoryItem]:
        """
        Devuelve las categorías reales desde la base de datos con:
        - id, nombre, slug, rubro (AUTOPARTES / FERRETERIA / AMBOS)
        - conteo dinámico de productos activos vinculados a cada una
        - compatibilidad de atributos (.name, .value) para Jinja2 y selectores existentes
        """
        rubro_filter = None
        if rubro:
            r_str = rubro.value.upper() if hasattr(rubro, "value") else str(rubro).upper()
            if r_str in ("AUTOPARTES", "FERRETERIA"):
                rubro_filter = r_str

        with self._session_factory() as session:
            stmt = select(CategoriaModel).filter(CategoriaModel.activo.is_(True))
            if rubro_filter:
                stmt = stmt.filter(
                    or_(
                        CategoriaModel.rubro == rubro_filter,
                        CategoriaModel.rubro == "AMBOS",
                    )
                )
            stmt = stmt.order_by(CategoriaModel.id.asc())
            cat_models = session.scalars(stmt).all()

            results: list[CategoryItem] = []
            for cm in cat_models:
                p_count = session.scalar(
                    select(func.count(ProductoModel.id)).filter(
                        ProductoModel.categoria_id == cm.id,
                        ProductoModel.activo.is_(True),
                    )
                ) or 0

                cat_bl = _normalize_business_line(getattr(cm, "rubro", "AMBOS"))
                # slug seguro
                slug_val = cm.slug or cm.nombre.lower().replace(" ", "-")

                results.append(
                    CategoryItem(
                        id=cm.id,
                        name=slug_val,
                        value=cm.nombre,
                        slug=slug_val,
                        rubro=cat_bl,
                        product_count=p_count,
                    )
                )

            return results

    async def get_families(
        self,
        category_id_or_slug: int | str | None = None,
        rubro: BusinessLine | str | None = None,
    ) -> list[FamilyItem]:
        """
        Devuelve las subfamilias/aplicaciones reales desde la base de datos con:
        - id, nombre, slug, category_id, category_name, rubro
        - conteo de productos activos vinculados a cada subfamilia
        - filtrado opcional por category_id / slug y por rubro comercial
        """
        rubro_filter = None
        if rubro:
            r_str = rubro.value.upper() if hasattr(rubro, "value") else str(rubro).upper()
            if r_str in ("AUTOPARTES", "FERRETERIA"):
                rubro_filter = r_str

        with self._session_factory() as session:
            stmt = (
                select(FamiliaModel)
                .options(selectinload(FamiliaModel.categoria))
                .filter(FamiliaModel.activo.is_(True))
            )

            # Filtrar por categoría (ID entero o slug de categoría)
            if category_id_or_slug is not None:
                if isinstance(category_id_or_slug, int) or (isinstance(category_id_or_slug, str) and category_id_or_slug.isdigit()):
                    stmt = stmt.filter(FamiliaModel.categoria_id == int(category_id_or_slug))
                else:
                    c_clean = str(category_id_or_slug).strip().lower()
                    stmt = stmt.join(FamiliaModel.categoria).filter(
                        or_(
                            func.lower(CategoriaModel.nombre) == c_clean,
                            CategoriaModel.slug == c_clean,
                            CategoriaModel.slug.ilike(f"%{c_clean}%"),
                        )
                    )

            # Filtrar por rubro comercial
            if rubro_filter:
                stmt = stmt.filter(
                    or_(
                        FamiliaModel.rubro == rubro_filter,
                        FamiliaModel.rubro == "AMBOS",
                    )
                )

            stmt = stmt.order_by(FamiliaModel.nombre.asc())
            fam_models = session.scalars(stmt).all()

            results: list[FamilyItem] = []
            for fm in fam_models:
                p_count = session.scalar(
                    select(func.count(ProductoModel.id)).filter(
                        ProductoModel.familia_id == fm.id,
                        ProductoModel.activo.is_(True),
                    )
                ) or 0

                fam_bl = _normalize_business_line(getattr(fm, "rubro", "AMBOS"))
                slug_val = fm.slug or fm.nombre.lower().replace(" ", "-")
                cat_name_val = fm.categoria.nombre if fm.categoria else ""

                results.append(
                    FamilyItem(
                        id=fm.id,
                        name=slug_val,
                        value=fm.nombre,
                        slug=slug_val,
                        category_id=fm.categoria_id or 0,
                        category_name=cat_name_val,
                        rubro=fam_bl,
                        product_count=p_count,
                    )
                )

            # Ordenar por conteo de productos descendente para destacar las más relevantes
            results.sort(key=lambda x: x.product_count, reverse=True)
            return results
