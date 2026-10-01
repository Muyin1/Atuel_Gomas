from src.application.ports.product_repository import IProductRepository
from src.domain.entities.product import Product
from src.domain.entities.product_category import ProductCategory
from src.domain.entities.business_line import BusinessLine
from src.domain.entities.category_item import CategoryItem
from src.domain.entities.family_item import FamilyItem
from src.domain.entities.vehicle_compatibility import VehicleCompatibility
from src.domain.value_objects.dimensions import Dimensions
from src.domain.value_objects.money import Money


class MemoryProductRepository(IProductRepository):
    """
    Repositorio en memoria para productos, desacoplado bajo IProductRepository.
    Permite reemplazarse por SqlAlchemyProductRepository sin tocar lógica de negocio.
    """
    def __init__(self):
        self._products: dict[str, Product] = {}
        self._seed_initial_catalog()

    def _seed_initial_catalog(self):
        sample_products = [
            Product(
                id="PROD-001",
                sku="AG-RAD-101",
                oem_code="7700838132",
                name="Manguera Superior de Radiador Reforzada",
                category=ProductCategory.MANGUERAS_AUTOMOTOR,
                description="Manguera de caucho EPDM reforzada con hilo de poliéster. Alta resistencia térmica hasta 130°C.",
                dimensions=Dimensions(inner_diameter_mm=32.0, outer_diameter_mm=40.0, length_mm=380.0, thickness_mm=4.0),
                base_price=Money(18500.0),
                wholesale_price=Money(12200.0),
                stock=45,
                image_url="/static/img/manguera_radiador.png",
                compatibilities=[
                    VehicleCompatibility(brand="Renault", model="Kangoo", engine="1.6 16v K4M", years="2008-2018"),
                    VehicleCompatibility(brand="Renault", model="Clio 2", engine="1.6 16v K4M", years="2003-2014"),
                ]
            ),
            Product(
                id="PROD-002",
                sku="AG-CAL-204",
                oem_code="5U0121049B",
                name="Manguera de Calefacción Entrada de Motor",
                category=ProductCategory.MANGUERAS_AUTOMOTOR,
                description="Manguera conformada para circuito de calefacción en caucho sintético resistente a líquido refrigerante glicol.",
                dimensions=Dimensions(inner_diameter_mm=16.0, outer_diameter_mm=23.0, length_mm=420.0, thickness_mm=3.5),
                base_price=Money(14200.0),
                wholesale_price=Money(9100.0),
                stock=30,
                image_url="/static/img/manguera_calefaccion.png",
                compatibilities=[
                    VehicleCompatibility(brand="Volkswagen", model="Gol Trend", engine="1.6 8v MSI", years="2009-2020"),
                    VehicleCompatibility(brand="Volkswagen", model="Voyage", engine="1.6 8v MSI", years="2010-2021"),
                    VehicleCompatibility(brand="Volkswagen", model="Fox", engine="1.6 8v", years="2008-2017"),
                ]
            ),
            Product(
                id="PROD-003",
                sku="AG-BUR-305",
                oem_code="BUR-P-50M",
                name="Burlete de Puerta Tubular Esponjoso con Inserto Metálico (Rollo 25m)",
                category=ProductCategory.BURLETES_PERFILES,
                description="Perfil de goma vulcanizada con alma de acero flexible. Aislamiento termoacústico para cabinas y furgones.",
                dimensions=Dimensions(length_mm=25000.0, thickness_mm=12.0),
                base_price=Money(42000.0),
                wholesale_price=Money(28500.0),
                stock=18,
                image_url="/static/img/burlete_perfil.png",
                compatibilities=[
                    VehicleCompatibility(brand="Universal", model="Línea Pesada y Utilitarios", engine="Todos", years="Universal"),
                    VehicleCompatibility(brand="Ford", model="F-100 / Ranger", engine="Todas", years="1998-2015"),
                ]
            ),
            Product(
                id="PROD-004",
                sku="AG-FUE-401",
                oem_code="7701470567",
                name="Fuelle de Semieje Lado Rueda con Abrazaderas y Grasa",
                category=ProductCategory.FUELLES_SUSPENSION,
                description="Kit de fuelle de goma termoplástica resistente a grasas grafitadas y flexión extrema con abrazaderas cremallera.",
                dimensions=Dimensions(inner_diameter_mm=24.0, outer_diameter_mm=78.0, length_mm=115.0),
                base_price=Money(9800.0),
                wholesale_price=Money(6300.0),
                stock=60,
                image_url="/static/img/fuelle_semieje.png",
                compatibilities=[
                    VehicleCompatibility(brand="Peugeot", model="206 / 207", engine="1.4 / 1.6", years="2000-2016"),
                    VehicleCompatibility(brand="Citroën", model="C3", engine="1.4 / 1.6", years="2003-2015"),
                ]
            ),
            Product(
                id="PROD-005",
                sku="AG-IND-502",
                oem_code="MAN-HID-R2-12",
                name="Manguera Hidráulica 2 Mallas de Acero R2-AT 1/2\"",
                category=ProductCategory.MANGUERAS_INDUSTRIALES,
                description="Manguera de alta presión para circuitos oleohidráulicos. Presión de trabajo: 275 BAR (3980 PSI). Por metro.",
                dimensions=Dimensions(inner_diameter_mm=12.7, outer_diameter_mm=22.2, thickness_mm=4.75),
                base_price=Money(19800.0),
                wholesale_price=Money(13500.0),
                stock=120,
                image_url="/static/img/manguera_hidraulica.png",
                compatibilities=[
                    VehicleCompatibility(brand="Agro / Vial", model="Tractores y Maquinaria Vial", engine="Circuitos Hidráulicos", years="Universal"),
                ]
            ),
            Product(
                id="PROD-006",
                sku="AG-PIS-601",
                oem_code="PIS-MON-120",
                name="Piso de Goma Antideslizante Moneda Alto Tránsito (Rollo 1.20 x 10m)",
                category=ProductCategory.PISOS_PLANCHAS,
                description="Piso de caucho SBR de 3mm con diseño botón/moneda. Ideal para talleres, furgones de carga y pasillos comerciales.",
                dimensions=Dimensions(thickness_mm=3.0, length_mm=10000.0),
                base_price=Money(115000.0),
                wholesale_price=Money(79000.0),
                stock=10,
                image_url="/static/img/piso_goma.png",
                compatibilities=[
                    VehicleCompatibility(brand="Ferretería Industrial", model="Instalaciones / Utilitarios", engine="N/A", years="Universal"),
                ]
            ),
            Product(
                id="PROD-007",
                sku="AG-ABR-701",
                oem_code="ABR-SIN-CREM",
                name="Caja de Abrazaderas a Cremallera Acero Inoxidable 25-40mm (Pack x 50u)",
                category=ProductCategory.ABRAZADERAS_ACCESORIOS,
                description="Abrazaderas sin fin con bordes redondeados anti-corte de manguera. Fleje de acero inox AISI 430.",
                dimensions=Dimensions(inner_diameter_mm=25.0, outer_diameter_mm=40.0),
                base_price=Money(38000.0),
                wholesale_price=Money(24500.0),
                stock=35,
                image_url="/static/img/abrazadera.png",
                compatibilities=[
                    VehicleCompatibility(brand="Universal", model="Mangueras Automotor e Industria", engine="Todos", years="Universal"),
                ]
            )
        ]
        for p in sample_products:
            self._products[p.id] = p

    async def get_by_id(self, product_id: str) -> Product | None:
        return self._products.get(product_id)

    async def get_by_sku(self, sku: str) -> Product | None:
        for p in self._products.values():
            if p.sku.upper() == sku.upper():
                return p
        return None

    async def search(
        self,
        query: str | None = None,
        category: ProductCategory | str | None = None,
        family: str | None = None,
        vehicle_brand: str | None = None,
        vehicle_model: str | None = None,
        page: int = 1,
        page_size: int = 24
    ) -> list[Product]:
        results = self._filter_products(query, category, family, vehicle_brand, vehicle_model)
        offset = max(0, (page - 1) * page_size)
        return results[offset: offset + page_size]

    async def count(
        self,
        query: str | None = None,
        category: ProductCategory | str | None = None,
        family: str | None = None,
        vehicle_brand: str | None = None,
        vehicle_model: str | None = None
    ) -> int:
        return len(self._filter_products(query, category, family, vehicle_brand, vehicle_model))

    def _filter_products(
        self,
        query: str | None = None,
        category: ProductCategory | str | None = None,
        family: str | None = None,
        vehicle_brand: str | None = None,
        vehicle_model: str | None = None
    ) -> list[Product]:
        results = list(self._products.values())

        if category:
            results = [p for p in results if p.category == category]

        if vehicle_brand:
            brand_clean = vehicle_brand.strip().lower()
            results = [
                p for p in results
                if any(brand_clean in c.brand.lower() or "universal" in c.brand.lower() for c in p.compatibilities)
            ]

        if vehicle_model:
            model_clean = vehicle_model.strip().lower()
            results = [
                p for p in results
                if any(model_clean in c.model.lower() or "universal" in c.model.lower() for c in p.compatibilities)
            ]

        if query:
            q = query.strip().lower()
            results = [
                p for p in results
                if (
                    q in p.name.lower()
                    or q in p.sku.lower()
                    or q in p.oem_code.lower()
                    or q in p.description.lower()
                    or any(q in c.brand.lower() or q in c.model.lower() for c in p.compatibilities)
                )
            ]

        return results


    async def save(self, product: Product) -> None:
        self._products[product.id] = product

    async def get_categories(self, rubro: BusinessLine | str | None = None) -> list[CategoryItem]:
        counts = {}
        for p in self._products.values():
            if p.is_active:
                cat_val = p.category.value if hasattr(p.category, "value") else str(p.category)
                counts[cat_val] = counts.get(cat_val, 0) + 1

        items: list[CategoryItem] = []
        for idx, pc in enumerate(ProductCategory, start=1):
            val = pc.value
            slug = pc.name.lower().replace("_", "-")
            items.append(
                CategoryItem(
                    id=idx,
                    name=slug,
                    value=val,
                    slug=slug,
                    rubro=BusinessLine.AMBOS,
                    product_count=counts.get(val, 0),
                )
            )
        return items

    async def get_families(
        self,
        category_id_or_slug: int | str | None = None,
        rubro: BusinessLine | str | None = None,
    ) -> list[FamilyItem]:
        return []
