# Registro de Cambios - Tech Lead (Backend & Core Architecture)

Este archivo registra las entregas de arquitectura, persistencia, contratos y modelos de base de datos.

---

## [2026-09-23] - Entrega Etapa 1: Conexión a Base de Datos y Modelos Relacionales SQLAlchemy 2.0 (3FN)

### 📌 Resumen de la Entrega:
Se diseñó e implementó la capa de persistencia completa en `src/infrastructure/database/` utilizando **SQLAlchemy 2.0** (`Mapped`, `mapped_column`, `relationship`, tipado estricto Python 3.12+). Se modeló el esquema relacional en Tercera Forma Normal (3FN) documentado en los insumos técnicos del catálogo comercial, soportando productos base, jerarquía de categorías/familias, variantes dimensionales y compuestas, compatibilidad vehicular multimarca, y gestión de clientes y pedidos mayoristas.

---

### 📂 Archivos Creados:
1. `src/infrastructure/database/connection.py`
2. `src/infrastructure/database/models/categoria_model.py`
3. `src/infrastructure/database/models/familia_model.py`
4. `src/infrastructure/database/models/talle_model.py`
5. `src/infrastructure/database/models/color_model.py`
6. `src/infrastructure/database/models/material_model.py`
7. `src/infrastructure/database/models/puntera_model.py`
8. `src/infrastructure/database/models/producto_model.py`
9. `src/infrastructure/database/models/variante_model.py`
10. `src/infrastructure/database/models/compatibilidad_vehicular_model.py`
11. `src/infrastructure/database/models/cliente_model.py`
12. `src/infrastructure/database/models/orden_model.py`
13. `src/infrastructure/database/models/orden_item_model.py`
14. `src/infrastructure/database/models/__init__.py`
15. `tests/unit/test_database_models.py`

---

### 📊 Especificación de Modelos, Tablas y Tipos de Datos (Contrato para Data Specialist y Fullstack Dev):

#### 1. Conexión y Motor (`src/infrastructure/database/connection.py`)
- **`Base`**: `DeclarativeBase` unificada para todos los modelos ORM.
- **`engine`**: Configurado por defecto a `sqlite:///./atuel_gomas.db` (o variable de entorno `DATABASE_URL` para PostgreSQL en producción con auto-corrección `postgres://` -> `postgresql://`).
- **`SessionLocal`**: `sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)`.
- **`init_db(target_engine=None)`**: Función que importa todos los modelos y ejecuta `Base.metadata.create_all(bind=engine)`.
- **`get_db_context()`**: Context manager generador para scripts ETL (`with get_db_context() as session:`).

#### 2. Catálogo de Atributos y Clasificación
- **`CategoriaModel`** (tabla `categorias`):
  - `id`: `Integer` (PK, autoincremental)
  - `nombre`: `String(100)` (unique, not null, index)
  - `descripcion`: `Text` (nullable)
  - `slug`: `String(120)` (nullable, index)
  - `activo`: `Boolean` (default True)
  - Relaciones: `familias` (1:N), `productos` (1:N).

- **`FamiliaModel`** (tabla `familias`):
  - `id`: `Integer` (PK, autoincremental)
  - `categoria_id`: `Integer` (FK `categorias.id`, ondelete SET NULL, nullable, index)
  - `nombre`: `String(100)` (not null, index)
  - `descripcion`: `Text` (nullable)
  - `slug`: `String(120)` (nullable, index)
  - `activo`: `Boolean` (default True)
  - Relaciones: `categoria` (N:1), `productos` (1:N).

- **`TalleModel`** (tabla `talles_medidas`):
  - `id`: `Integer` (PK, autoincremental)
  - `valor`: `String(50)` (not null, index - ej: "42", "Nro. 8", "1/2\"", "3mm x 1m")
  - `unidad_medida`: `String(30)` (nullable)
  - Relaciones: `variantes` (1:N).

- **`ColorModel`** (tabla `colores`):
  - `id`: `Integer` (PK, autoincremental)
  - `nombre`: `String(50)` (not null, index - ej: "Blanco", "Negro", "Amarillo")
  - `codigo_hex`: `String(10)` (nullable - ej: "#000000")
  - Relaciones: `variantes` (1:N).

- **`MaterialModel`** (tabla `materiales`):
  - `id`: `Integer` (PK, autoincremental)
  - `nombre`: `String(100)` (not null, index - ej: "Cuero Descarne", "EPDM", "Nitrilo", "PVC")
  - `propiedades_tecnicas`: `Text` (nullable)
  - Relaciones: `variantes` (1:N).

- **`PunteraModel`** (tabla `punteras_seguridad`):
  - `id`: `Integer` (PK, autoincremental)
  - `tipo_puntera`: `String(50)` (not null, index - ej: "Acero", "Aluminio", "Dieléctrica", "Sin puntera")
  - `descripcion`: `Text` (nullable)
  - Relaciones: `variantes` (1:N).

#### 3. Catálogo Principal de Productos y Relaciones M:N
- **`ProductoModel`** (tabla `productos`):
  - `id`: `Integer` (PK, autoincremental)
  - `sku`: `String(50)` (nullable, index - *Nota: se indexó sin restricción de unicidad estricta para tolerar productos provisionales 'S/C' y códigos duplicados entre hojas*)
  - `codigo_oem`: `String(50)` (nullable, index)
  - `nombre`: `String(255)` (not null, index)
  - `descripcion`: `Text` (nullable)
  - `categoria_id`: `Integer` (FK `categorias.id`, ondelete SET NULL, nullable, index)
  - `familia_id`: `Integer` (FK `familias.id`, ondelete SET NULL, nullable, index)
  - `precio_base`: `Float` (default 0.0 - precio consumidor)
  - `precio_mayorista_b2b`: `Float` (default 0.0 - precio gremio)
  - `stock`: `Integer` (default 0)
  - `imagen_url`: `String(255)` (nullable)
  - `diametro_interior_mm`: `Float` (nullable)
  - `diametro_exterior_mm`: `Float` (nullable)
  - `largo_mm`: `Float` (nullable)
  - `espesor_mm`: `Float` (nullable)
  - `activo`: `Boolean` (default True, index)
  - `created_at`: `DateTime` (default UTC)
  - `updated_at`: `DateTime` (default UTC, onupdate UTC)
  - Relaciones: `categoria`, `familia`, `variantes` (cascade delete-orphan), `compatibilidades` (cascade delete-orphan).

- **`VarianteModel`** (tabla `producto_variantes` - Puente M:N):
  - `id`: `Integer` (PK, autoincremental)
  - `producto_id`: `Integer` (FK `productos.id`, ondelete CASCADE, not null, index)
  - `talle_id`: `Integer` (FK `talles_medidas.id`, ondelete SET NULL, nullable, index)
  - `color_id`: `Integer` (FK `colores.id`, ondelete SET NULL, nullable, index)
  - `material_id`: `Integer` (FK `materiales.id`, ondelete SET NULL, nullable, index)
  - `puntera_id`: `Integer` (FK `punteras_seguridad.id`, ondelete SET NULL, nullable, index)
  - `codigo_barras`: `String(50)` (nullable, index)
  - `sku_variante`: `String(50)` (nullable, index)
  - `stock_variante`: `Integer` (default 0)
  - `precio_especifico`: `Float` (nullable)
  - `activo`: `Boolean` (default True)
  - Relaciones: `producto`, `talle`, `color`, `material`, `puntera`.

- **`CompatibilidadVehicularModel`** (tabla `producto_compatibilidad_vehicular` - Puente M:N):
  - `id`: `Integer` (PK, autoincremental)
  - `producto_id`: `Integer` (FK `productos.id`, ondelete CASCADE, not null, index)
  - `marca`: `String(100)` (not null, index - ej: "Renault", "Ford", "Fiat")
  - `modelo`: `String(100)` (not null, index - ej: "Kangoo", "Hilux", "Gol")
  - `motorizacion`: `String(100)` (nullable, index - ej: "1.6 16v K4M")
  - `anio_desde`: `Integer` (nullable)
  - `anio_hasta`: `Integer` (nullable)
  - `anios_texto`: `String(50)` (nullable - ej: "2008-2018")
  - Relaciones: `producto`.

#### 4. Clientes y Pedidos Mayoristas
- **`ClienteModel`** (tabla `clientes`):
  - `id`: `String(36)` (PK, UUID string)
  - `email`: `String(255)` (unique, not null, index)
  - `razon_social`: `String(255)` (not null)
  - `cuit`: `String(20)` (unique, not null, index)
  - `telefono`: `String(50)` (nullable)
  - `direccion`: `String(255)` (nullable)
  - `ciudad`: `String(100)` (nullable)
  - `rol`: `String(30)` (default "b2b_client")
  - `is_approved`: `Boolean` (default False)
  - `hashed_password`: `String(255)` (not null)
  - `created_at`: `DateTime` (default UTC)
  - Relaciones: `ordenes` (1:N).

- **`OrdenModel`** (tabla `ordenes`):
  - `id`: `String(36)` (PK - ej: "ORD-XXXXXXXX" o UUID)
  - `cliente_id`: `String(36)` (FK `clientes.id`, ondelete RESTRICT, not null, index)
  - `cliente_nombre`: `String(255)` (not null)
  - `estado`: `String(50)` (default "PENDIENTE_APROBACION")
  - `total`: `Float` (default 0.0)
  - `notas`: `Text` (nullable)
  - `created_at`: `DateTime` (default UTC)
  - Relaciones: `cliente` (N:1), `items` (1:N, cascade delete-orphan).

- **`OrdenItemModel`** (tabla `orden_items`):
  - `id`: `Integer` (PK, autoincremental)
  - `orden_id`: `String(36)` (FK `ordenes.id`, ondelete CASCADE, not null, index)
  - `producto_id`: `Integer` (FK `productos.id`, ondelete SET NULL, nullable, index)
  - `producto_sku`: `String(50)` (nullable)
  - `producto_nombre`: `String(255)` (not null)
  - `precio_unitario`: `Float` (not null)
  - `cantidad`: `Integer` (default 1)
  - `subtotal`: `Float` (not null)
  - Relaciones: `orden` (N:1), `producto` (N:1).

---

### 🔓 Mensaje de Desbloqueo para Etapa 2 (Data Specialist):
El motor y los esquemas relacionales se encuentran listos, probados y verificados.

Para el script `scripts/seed_database.py`:
```python
from src.infrastructure.database.connection import get_db_context, init_db
from src.infrastructure.database.models import (
    CategoriaModel, FamiliaModel, ProductoModel,
    VarianteModel, TalleModel, ColorModel,
    MaterialModel, PunteraModel, CompatibilidadVehicularModel
)

# 1. Asegurar tablas creadas
init_db()

# 2. Utilizar sesión para ingesta masiva
with get_db_context() as session:
    # Inserción de categorías, familias, productos y variantes...
    session.commit()
```
- **Nota clave sobre SKUs**: El campo `sku` en `ProductoModel` no es forzado como unique constraint para evitar colisiones con filas que tengan 'S/C' o códigos compartidos en los archivos provisorios. La clave primaria única e irrepetible es `id` (autoincremental).

---

## [2026-09-28] - Entrega Etapa 3: Repositorios SQLAlchemy 2.0, Paginación y Consultas SQL Reales

### 📌 Resumen de la Entrega:
Se implementaron los repositorios concretos basados en SQLAlchemy 2.0 (`SqlAlchemyProductRepository`, `SqlAlchemyCustomerRepository` y `SqlAlchemyOrderRepository`) conectados directamente a la base de datos poblada `atuel_gomas.db`. Se actualizó el puerto de aplicación `IProductRepository` para admitir paginación (`page: int = 1`, `page_size: int = 24`) y método `count()`. Se introdujo el DTO `PaginatedProductsDTO` y se enchufaron los repositorios SQL en el contenedor IoC central (`src/infrastructure/config/container.py`) reemplazando los mocks en memoria. Todos los tests de la suite pasan al 100% (9 de 9).

---

### 📂 Archivos Creados y Modificados:
1. **Creados:**
   - `src/adapters/repositories/sql_product_repository.py`
   - `src/adapters/repositories/sql_customer_repository.py`
   - `src/adapters/repositories/sql_order_repository.py`
2. **Modificados:**
   - `src/application/ports/product_repository.py` (incorporación de `page`, `page_size` y `count()`)
   - `src/adapters/repositories/product_repo.py` (actualización de `MemoryProductRepository` para cumplir con la firma del puerto)
   - `src/application/dtos/product_dto.py` (campos de paginación en `ProductSearchDTO` y creación de `PaginatedProductsDTO`)
   - `src/application/use_cases/search_products.py` (soporte de paginación)
   - `src/infrastructure/config/container.py` (inyección de repositorios SQL reales)
   - `.team/board.json` (actualización de etapas)
   - `.team/changelog/backend.md` (este documento)

---

### 🛠️ Contratos y Especificación de Repositorios para el Fullstack Dev (Etapa 4):

#### 1. `SqlAlchemyProductRepository` (`src/adapters/repositories/sql_product_repository.py`)
Implementa `IProductRepository` con mapeo a la entidad de dominio `Product` (incluyendo variantes y compatibilidades vehiculares hidratadas vía `selectinload`):

- **`search(query: str | None = None, category: ProductCategory | None = None, vehicle_brand: str | None = None, vehicle_model: str | None = None, page: int = 1, page_size: int = 24) -> list[Product]`**:
  - Filtro por texto libre (`query`): Búsqueda insensible a mayúsculas en `nombre`, `sku`, `codigo_oem` y `descripcion`.
  - Filtro por categoría (`category`): Acepta `ProductCategory` enum o nombre/slug.
  - Filtro vehicular (`vehicle_brand`, `vehicle_model`): Cruza con la tabla `producto_compatibilidad_vehicular` y filtra por marca/modelo automotor.
  - Paginación: `offset = (page - 1) * page_size`, `limit = page_size`.
  - Ordenamiento: `id DESC` para destacar productos técnicos clave y recientes.
- **`count(query: str | None = None, category: ProductCategory | None = None, vehicle_brand: str | None = None, vehicle_model: str | None = None) -> int`**:
  - Retorna el conteo total exacto de productos que cumplen los criterios (sin aplicar limit/offset).
  - Optimizado mediante subconsulta `select(func.count()).select_from(subquery)` para evitar sobreconteo por joins 1:N.
- **`get_by_id(product_id: str) -> Product | None`**:
  - Resuelve tanto por ID primario numérico (`int`) como por SKU/código o identificadores legados (ej: `"PROD-001"`).
- **`get_by_sku(sku: str) -> Product | None`**:
  - Búsqueda exacta de producto por código de artículo / SKU.
- **`get_categories() -> list[ProductCategory]`**:
  - Retorna la lista de categorías activas existentes en el catálogo.

#### 2. DTO de Paginación (`src/application/dtos/product_dto.py`):
```python
@dataclass
class ProductSearchDTO:
    query: str | None = None
    category: ProductCategory | None = None
    vehicle_brand: str | None = None
    vehicle_model: str | None = None
    role: UserRole = UserRole.PUBLIC
    page: int = 1
    page_size: int = 24

@dataclass
class PaginatedProductsDTO:
    items: list[ProductDTO]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_prev: bool
    has_next: bool
```

#### 3. `SqlAlchemyCustomerRepository` (`src/adapters/repositories/sql_customer_repository.py`)
Implementa `ICustomerRepository`:
- **`get_by_cuit(cuit: str) -> Customer | None`**: Normaliza CUIT (remueve guiones y espacios) y mapea al dominio `Customer` y `UserRole`.
- **`get_by_email(email: str) -> Customer | None`**: Búsqueda por email insensible a mayúsculas.
- **`get_by_id(customer_id: str) -> Customer | None`**
- **`save(customer: Customer) -> None`**

#### 4. `SqlAlchemyOrderRepository` (`src/adapters/repositories/sql_order_repository.py`)
Implementa `IOrderRepository`:
- **`save(order: Order) -> None`**: Persiste `OrdenModel` y sus `OrdenItemModel` correspondientes en transacción atómica.
- **`get_by_id(order_id: str) -> Order | None`**
- **`list_by_customer(customer_id: str) -> list[Order]`**

---

### 🔓 Mensaje de Desbloqueo para Etapa 4 (Fullstack Dev):
El backend y la persistencia están completamente operativos con los 12.828+ artículos reales:
- Puedes invocar `container.product_repo.search(..., page=page, page_size=page_size)` y `container.product_repo.count(...)`.
- En `web_controller.py`, puedes recibir los query params `page: int = 1` y utilizarlos para la paginación con HTMX (ej: `hx-get="/api/productos/search?page=..."` o infinite scroll).
- El catálogo real ya responde a filtros de vehículos (ej: `vehicle_brand=Renault`), categorías y términos de búsqueda.

---

## [2026-09-28] - Entrega Etapa 2.1 (Fase 2): Rubros Comerciales (BusinessLine), Reclasificación, Categorías Dinámicas e Imágenes de Catálogo

### 📌 Resumen de la Entrega:
Se implementó la segmentación comercial por rubro de negocio (**Autopartes**, **Ferretería Industrial** y **Ambos**) en todo el sistema. Se diseñó el enum de dominio `BusinessLine` y la entidad de metadatos `CategoryItem`, integrándolos con la persistencia en SQLAlchemy 2.0 (`ProductoModel.rubro`, `CategoriaModel.rubro`, `ClienteModel.rubro`). Se reclasificaron los tubos termocontraíbles fuera de EPP hacia ferretería. Se refactorizó `get_categories()` en `SqlAlchemyProductRepository` para devolver las categorías reales de la base de datos con conteo exacto de artículos y filtrado opcional por rubro comercial. Se copiaron las 28 imágenes técnicas desde `datos provicionales/` a `src/infrastructure/static/img/catalogo/` y se enlazaron a sus familias y artículos correspondientes en la DB.

---

### 📂 Archivos Creados y Modificados:
1. **Creados:**
   - `src/domain/entities/business_line.py` (Enum `BusinessLine.AUTOPARTES`, `FERRETERIA`, `AMBOS`).
   - `src/domain/entities/category_item.py` (Entidad de dominio `CategoryItem` con `id`, `name`, `value`, `slug`, `rubro`, `product_count`).
   - `src/infrastructure/static/img/catalogo/` (28 imágenes técnicas de alta resolución organizadas).
   - `scripts/migrate_rubros.py` (Script de migración y asignación de rubros en DB).
   - `scripts/link_catalog_images.py` (Script de enlace y vinculación de imágenes técnicas a `ProductoModel.imagen_url`).
2. **Modificados:**
   - `src/domain/entities/product.py` (incorporación de campo `business_line`).
   - `src/domain/entities/customer.py` (incorporación de campo `business_line`).
   - `src/domain/entities/product_category.py` (alineación canónica con los nombres y slugs de la DB y alias retrocompatibles).
   - `src/domain/entities/__init__.py` (exportación de `BusinessLine` y `CategoryItem`).
   - `src/infrastructure/database/models/categoria_model.py` (columna `rubro`).
   - `src/infrastructure/database/models/producto_model.py` (columna `rubro`).
   - `src/infrastructure/database/models/cliente_model.py` (columna `rubro`).
   - `src/application/ports/product_repository.py` (actualización de firma `get_categories(rubro: BusinessLine | str | None = None) -> list[CategoryItem]`).
   - `src/adapters/repositories/sql_product_repository.py` (implementación dinámica de `get_categories()` con conteo por categoría y filtro por rubro, soporte de persistencia de `rubro` en `save()`).
   - `src/adapters/repositories/sql_customer_repository.py` (soporte y persistencia de `rubro` en `ClienteModel`).
   - `src/adapters/repositories/product_repo.py` (actualización en memoria de `get_categories`).
   - `tests/unit/test_domain.py` (test unitario para `BusinessLine` y `CategoryItem`).
   - `.team/board.json` (etapa 2.1 a `COMPLETED`, etapa 2.3 a `READY`).

---

### 🛠️ Especificación de Contratos para el Fullstack Dev (Etapa 2.3):

#### 1. Categorías Reales Dinámicas (`container.product_repo.get_categories`):
Ahora `await container.product_repo.get_categories(rubro=...)` devuelve una lista de objetos `CategoryItem` reales desde SQLite:
```python
@dataclass
class CategoryItem:
    id: int
    name: str          # Slug/Identificador legible (ej: 'mangueras-automotor', 'pisos-revestimientos')
    value: str         # Nombre canónico para la UI (ej: 'Mangueras Automotor', 'Pisos y Revestimientos')
    slug: str          # Slug URL friendly (ej: 'pisos-revestimientos')
    rubro: BusinessLine # BusinessLine.AUTOPARTES | BusinessLine.FERRETERIA | BusinessLine.AMBOS
    product_count: int # Cantidad exacta de artículos activos en la DB
```

**Comportamiento en Jinja2:**
`CategoryItem` implementa `__str__` y expone `.name`, `.value`, `.slug`, `.rubro` y `.product_count`. En los templates HTML se puede usar directamente:
```html
<select id="category" name="category" class="form-control">
    <option value="">Todas las categorías</option>
    {% for cat in categories %}
        <option value="{{ cat.slug }}" data-rubro="{{ cat.rubro.value }}">
            {{ cat.value }} ({{ cat.product_count }})
        </option>
    {% endfor %}
</select>
```

#### 2. Filtrado por Rubro Comercial:
- `await container.product_repo.get_categories("AUTOPARTES")` retorna solo las categorías de automotor y las mixtas (ej: *Mangueras Automotor*, *Abrazaderas y Acoples*, *Correas y Transmisión*, *Ferretería Industrial y Autopartes*).
- `await container.product_repo.get_categories("FERRETERIA")` retorna las categorías industriales, EPP y mixtas (ej: *Mangueras Industriales*, *EPP*, *Pisos y Revestimientos*, *Abrazaderas*, *Correas*, etc.).
- Si el usuario logueado tiene `current_user.business_line` (`AUTOPARTES` o `FERRETERIA`), se puede utilizar para preseleccionar la solapa y prefiltrar la lista.

#### 3. Búsqueda y Filtrado Resiliente en `search(...)` y `count(...)`:
El repositorio `SqlAlchemyProductRepository` ahora acepta como `category` tanto el enum `ProductCategory` como directamente el `slug` (ej: `"pisos-revestimientos"`) o el nombre de texto (ej: `"Pisos y Revestimientos"`), resolviendo de raíz el problema donde *Pisos de Goma*, *Fuelles* o *Burletes* no traían resultados o quedaban desacoplados de los 7 grupos reales de la base de datos.

#### 4. Imágenes Técnicas en Portada y Detalle:
- Los productos de familias clave (abrazaderas mini americana, fleje ancho, súper presión, alambre, caños pileteros, pisos de goma, escobillas, líquidos de freno, látex, mangueras de riego, cebadores y precintos) ya tienen `imagen_url` apuntando a `/static/img/catalogo/...` que existen físicamente en disco y se sirven directamente desde FastAPI.

---

### 🔓 Mensaje de Desbloqueo para Etapa 2.3 (Fullstack Dev):
El backend ha sido actualizado y verificado con 14 tests pasando al 100%. La **Etapa 2.3** se encuentra en estado **READY**. Puedes proceder a:
1. Diseñar las pestañas/solapas en `index.html` para alternar entre **🚗 Línea Automotor y Autopartes** y **🏭 Línea Ferretería Industrial y EPP**.
2. Alimentar el selector de categorías dinámicamente con las categorías reales de la DB y su conteo de productos.
3. Preseleccionar automáticamente el rubro comercial preferido del cliente logueado (`current_user.business_line`).

---

## [2026-09-28] - Entrega Etapa 3.1 (Fase 3): Segregación de Correas, Reubicación de Accesorios, Subfamilias de Mangueras y Filtro `family`

### 📌 Resumen de la Entrega:
Se completó la reorganización estructural del catálogo técnico en la base de datos `atuel_gomas.db` y en la arquitectura de dominio/persistencia:
1. **Segregación Estricta de Correas:** *Correas Automotor y Poly-V* asignadas con exclusividad al rubro `AUTOPARTES`. *Correas Industriales* y *Cintas Rotoenfardadoras* asignadas con exclusividad al rubro `FERRETERIA`.
2. **Reubicación de Accesorios y Mantenimiento:** Se extrajeron *Escobillas Limpiaparabrisas* y *Cebadores* de la categoría de mangueras, agrupándolos en la nueva categoría propia **Accesorios y Mantenimiento Automotor** (`id=8`, `slug="accesorios-mantenimiento-automotor"`). Se reubicaron los *Caños Pileteros* a *Ferretería Industrial* (`id=2`).
3. **Desglose de Mangueras Automotor en Subfamilias/Aplicaciones (+9.000 artículos):** Se crearon y vincularon subfamilias especializadas para permitir navegación por aplicación técnica:
   - **Mangueras de Radiador y Refrigeración** (`slug="mangueras-radiador"`): 4.660 artículos
   - **Mangueras Especiales y Derivaciones** (`slug="mangueras-especiales-derivaciones"`): 1.714 artículos
   - **Mangueras de Calefacción** (`slug="mangueras-calefaccion"`): 1.245 artículos
   - **Mangueras de Admisión de Aire** (`slug="mangueras-admision-aire"`): 794 artículos
   - **Mangueras de Goma por Metro** (`slug="mangueras-goma-por-metro"`): 469 artículos
   - **Mangueras de Combustible** (`slug="mangueras-combustible"`): 398 artículos
   - **Mangueras de Turbo e Intercooler** (`slug="mangueras-turbo-intercooler"`): 294 artículos
   - **Fuelles de Suspensión y Dirección** (`slug="fuelles-suspension-direccion"`): 36 artículos
4. **Entidad `FamilyItem` y Métodos de Repositorio:** Creada la entidad de dominio `FamilyItem`. Se implementó `get_families(...)` en `IProductRepository` y `SqlAlchemyProductRepository` con filtrado por categoría y rubro comercial, y se añadió el parámetro `family` en `search()` y `count()`. Todos los 17 tests de la suite pasan al 100%.

---

### 📂 Archivos Creados y Modificados:
1. **Creados:**
   - `src/domain/entities/family_item.py` (Entidad `FamilyItem` con `id`, `name`, `value`, `slug`, `category_id`, `category_name`, `rubro`, `product_count`).
   - `scripts/reorganizar_familias_y_correas.py` (Script de migración y reclasificación en la base de datos).
2. **Modificados:**
   - `src/domain/entities/product.py` (campos `family_id` y `family_name`).
   - `src/domain/entities/product_category.py` (agregado `ACCESORIOS_AUTOMOTOR`).
   - `src/domain/entities/__init__.py` (exportación de `FamilyItem`).
   - `src/infrastructure/database/models/familia_model.py` (columna `rubro`).
   - `src/application/dtos/product_dto.py` (`family` en `ProductSearchDTO` y `family` en `ProductSummaryDTO`).
   - `src/application/use_cases/search_products.py` (soporte y propagación de `family`).
   - `src/application/ports/product_repository.py` (firmas con `family` y `get_families`).
   - `src/adapters/repositories/sql_product_repository.py` (soporte de filtrado por `family`, eager loading de `familia`, implementación de `get_families()`).
   - `src/adapters/repositories/product_repo.py` (actualización de memoria para `family` y `get_families`).
   - `tests/unit/test_domain.py` (tests unitarios para `FamilyItem`).
   - `.team/board.json` (`etapa_3_1` -> `COMPLETED`, `etapa_3_3` -> `READY`).

---

### 🛠️ Especificación de Contratos para el Fullstack Dev (Etapa 3.3):

#### 1. Nuevo Método `container.product_repo.get_families(...)`:
Permite obtener la lista de subfamilias/aplicaciones con su conteo de productos activos en la base de datos:
```python
async def get_families(
    self,
    category_id_or_slug: int | str | None = None,
    rubro: BusinessLine | str | None = None,
) -> list[FamilyItem]:
```

**Ejemplos de uso:**
- **Todas las subfamilias de Mangueras Automotor:**
  ```python
  families = await container.product_repo.get_families("mangueras-automotor")
  # Retorna: Radiador (4.660), Especiales (1.714), Calefacción (1.245), Admisión (794),
  #          Por Metro (469), Combustible (398), Turbo/Intercooler (294), Fuelles (36)
  ```
- **Todas las familias para Autopartes:**
  ```python
  families = await container.product_repo.get_families(rubro="AUTOPARTES")
  # Incluye Correas Automotor y Poly-V, Mangueras, Escobillas, Cebadores, etc.
  # NO incluye Correas Industriales ni Cintas Rotoenfardadoras.
  ```
- **Todas las familias para Ferretería Industrial:**
  ```python
  families = await container.product_repo.get_families(rubro="FERRETERIA")
  # Incluye Correas Industriales, Cintas Rotoenfardadoras, Mangueras Industriales, Caños Pileteros, EPP, Pisos, etc.
  # NO incluye Correas Automotor y Poly-V.
  ```

#### 2. Entidad `FamilyItem`:
```python
@dataclass
class FamilyItem:
    id: int               # ID primario en la tabla familias (ej: 43)
    name: str             # Slug identificador (ej: 'mangueras-radiador')
    value: str            # Nombre visible (ej: 'Mangueras de Radiador')
    slug: str             # Slug url-friendly (ej: 'mangueras-radiador')
    category_id: int      # ID de categoría padre
    category_name: str    # Nombre de categoría padre (ej: 'Mangueras Automotor')
    rubro: BusinessLine   # AUTOPARTES / FERRETERIA / AMBOS
    product_count: int    # Total de productos activos en la familia
```

#### 3. Parámetro `family` en Búsqueda y Paginación HTMX:
El endpoint `/api/productos/search` y los casos de uso ahora aceptan `family: str | None = None`. Puede enviarse como query param:
`GET /api/productos/search?category=mangueras-automotor&family=mangueras-turbo-intercooler`
El repositorio filtrará automáticamente por ID de familia, slug o coincidencia de nombre.

---

### 🔓 Mensaje de Desbloqueo para Etapa 3.3 (Fullstack Dev):
El backend se encuentra listo, probado y verificado. La **Etapa 3.3** se encuentra en estado **READY**. Puedes proceder a:
1. Crear el endpoint `@router.get("/api/familias")` en `web_controller.py` que devuelva las familias para una categoría o rubro.
2. Renderizar los badges o selector secundario de subítems en `index.html`.
3. Disparar el filtrado reactivo de catálogo pasando `family` hacia `/api/productos/search`.

---

## [2026-09-29] - Entrega Posta 1: Conectividad e Infraestructura PostgreSQL Cloud (Supabase)

### 📌 Resumen de la Entrega:
Se configuró la infraestructura de conexión para la base de datos PostgreSQL en la nube alojada en **Supabase** sin alterar la Clean Architecture.
1. Se instaló y registró la dependencia oficial `psycopg2-binary>=2.9.9` y `python-dotenv>=1.0.0` en `requirements.txt`.
2. Se configuró el archivo `.env` en la raíz con la cadena de conexión optimizada para compatibilidad IPv4/IPv6 a través del transaction pooler de Supabase (`aws-0-us-east-2.pooler.supabase.com:5432`).
3. Se actualizó `src/infrastructure/database/connection.py` para cargar automáticamente variables mediante `python-dotenv` y normalizar prefijos `postgres://` y `postgresql://` hacia `postgresql+psycopg2://`.
4. Se ejecutó la inicialización DDL creando exitosamente las **12 tablas físicas** en el esquema público de Supabase:
   - `categorias` (6 columnas)
   - `familias` (7 columnas)
   - `talles_medidas` (3 columnas)
   - `colores` (3 columnas)
   - `materiales` (3 columnas)
   - `punteras_seguridad` (3 columnas)
   - `productos` (19 columnas)
   - `producto_variantes` (11 columnas)
   - `producto_compatibilidad_vehicular` (8 columnas)
   - `clientes` (12 columnas)
   - `ordenes` (7 columnas)
   - `orden_items` (8 columnas)
5. Se validaron los tests de dominio y modelos relacionales (`tests/unit/`) al 100% de éxito (8/8 passed).

---

### 📂 Archivos Creados / Modificados:
1. `requirements.txt` (agregados `psycopg2-binary>=2.9.9` y `python-dotenv>=1.0.0`).
2. `.env` (cadena de conexión de Supabase configurada).
3. `src/infrastructure/database/connection.py` (carga de entorno y normalización de dialecto SQLAlchemy).
4. `.team/board.json` (etapa `etapa_posta_1_tech_lead_supabase` en `COMPLETED`, `etapa_posta_2_data_specialist_migracion_datos` en `READY`).

---

### 🔓 Mensaje de Desbloqueo para Posta 2 (Data Specialist):
La infraestructura remota en Supabase PostgreSQL se encuentra completamente creada, conectada y lista para recibir datos.
- **Cadena de Conexión activa en `.env`:** lista para que los scripts consuman `DATABASE_URL` o `get_db_context()`.
- **Tablas físicas:** Las 12 tablas en Tercera Forma Normal (3FN) con sus claves foráneas, restricciones de unicidad e índices están creadas en la base de datos de producción.
- **Siguiente paso:** El Data Specialist puede ejecutar su script de migración masiva/seeder para transferir los registros de SQLite local (`atuel_gomas.db`) hacia PostgreSQL en Supabase.

---

## [2026-09-30] - Corrección DevOps: Dependencia 'email-validator' para Pydantic y Despliegue en Render

### 📌 Resumen de la Corrección:
Se corrigió la falta de la dependencia `email-validator` requerida en tiempo de ejecución por `pydantic.EmailStr` en [`src/application/dtos/auth_dto.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/application/dtos/auth_dto.py). Sin este paquete, la inicialización del contenedor y los DTOs de autenticación/registro B2B provocaban un error fatal durante el inicio de la aplicación en Render (`pydantic.errors.PydanticImportError: email-validator is not installed`).

### 📂 Archivos Modificados:
1. [`requirements.txt`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/requirements.txt):
   - Se agregó explícitamente `email-validator>=2.0.0`.
2. [`render.yaml`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/render.yaml):
   - Se verificó que `buildCommand: pip install -r requirements.txt` instala automáticamente la lista completa de dependencias de producción.
3. [`.team/board.json`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/.team/board.json):
   - Se actualizó el campo `ultimo_evento` certificando la solución del fallo y la ejecución exitosa de pruebas.

### 🧪 Certificación y Pruebas:
- Inicialización y validación aislada de `RegisterB2BDTO` con `EmailStr` satisfactoria.
- Suite completa de pruebas ejecutada: **19 pasadas de 19 tests (100% OK)** cubriendo integración web, modelos relacionales y lógica de dominio.

---

## [2026-10-01] - Entrega Posta 3.1: Solicitud de Cuentas B2B, Modo Demo y Protección de Alta Directa

### 📌 Resumen de la Entrega:
Se implementaron los contratos, DTOs y casos de uso del backend comercial y de seguridad requeridos para:
1. **Solicitud de Cuenta Mayorista:** Registro de prospectos comerciales que ingresan en estado pendiente (`is_approved=False`) sin password para aprobación posterior por parte del administrador. Se valida formato de CUIT de 11 dígitos y duplicidad tanto para cuentas activas como para solicitudes ya en trámite.
2. **Modo Demo / Prospecto (Simulación Comercial):** Implementación del método `authenticate_demo()` en `AuthenticateCustomerUseCase`. Permite emitir una sesión con permisos `UserRole.B2B_CLIENT` (utilizando el cliente semilla `cliente@atuelgomas.com` o una entidad simulada en memoria) para que los prospectos evalúen el catálogo con precios mayoristas en vivo.
3. **Protección de Alta Directa:** En `RegisterB2BCustomerUseCase`, se restringió la creación directa de cuentas aprobadas exigiendo que el invocador posea `UserRole.ADMIN`. En caso contrario se eleva `UnauthorizedActionError`.

---

### 📂 Archivos Creados y Modificados:
1. [`src/application/dtos/solicitud_cuenta_dto.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/application/dtos/solicitud_cuenta_dto.py): Creado `SolicitudCuentaDTO` con campos de razón social, CUIT, rubro, email, teléfono, provincia, ciudad y mensaje.
2. [`src/application/dtos/auth_dto.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/application/dtos/auth_dto.py): Agregado `CustomerDTO`.
3. [`src/domain/exceptions/domain_exceptions.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/domain/exceptions/domain_exceptions.py): Agregada excepción `UnauthorizedActionError`.
4. [`src/application/use_cases/solicitar_cuenta.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/application/use_cases/solicitar_cuenta.py): Creado `SolicitarCuentaUseCase`.
5. [`src/application/use_cases/authenticate_customer.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/application/use_cases/authenticate_customer.py): Agregado método `authenticate_demo()`.
6. [`src/application/use_cases/register_b2b_customer.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/application/use_cases/register_b2b_customer.py): Validación de rol `ADMIN` para alta directa.
7. [`src/infrastructure/config/container.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/infrastructure/config/container.py): Registrado `container.solicitar_cuenta_uc`.
8. [`tests/unit/test_solicitar_cuenta.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/tests/unit/test_solicitar_cuenta.py): 5 pruebas unitarias cubriendo solicitud exitosa, duplicidad CUIT/email, modo demo y protección ADMIN.
9. [`.team/board.json`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/.team/board.json): Posta 3.1 en `COMPLETED`, Posta 3.2 en `READY`.

---

### 🛠️ Especificación de Contratos para el Fullstack Dev (Posta 3.2):

#### 1. Caso de Uso: `container.solicitar_cuenta_uc.execute(dto: SolicitudCuentaDTO)`
```python
from src.application.dtos.solicitud_cuenta_dto import SolicitudCuentaDTO

dto = SolicitudCuentaDTO(
    business_name=business_name,
    cuit=cuit,
    rubro=rubro,           # "AUTOPARTES", "FERRETERIA" o "AMBOS"
    email=email,
    phone=phone,
    province=province,     # Opcional
    city=city,             # Opcional
    message=message        # Opcional
)
prospecto = await container.solicitar_cuenta_uc.execute(dto)
# prospecto.is_approved == False
```
*Manejo de Errores:* Eleva `CustomerAlreadyExistsError` si el CUIT o email ya existen (sea con cuenta activa o solicitud previa).

#### 2. Autenticación Modo Demo: `container.auth_customer_uc.authenticate_demo()`
```python
customer = await container.auth_customer_uc.authenticate_demo()
# Retorna entidad Customer con role=UserRole.B2B_CLIENT e is_approved=True.
# Para iniciar la sesión en web_controller:
response = RedirectResponse(url="/", status_code=303)
signed_cookie_val = sign_session_cookie(customer.id)
response.set_cookie(
    key=SESSION_COOKIE_NAME,
    value=signed_cookie_val,
    httponly=True,
    samesite="lax",
    max_age=86400 * 7
)
```

#### 3. Protección de Alta Directa:
```python
# Requiere requester=current_user o requester=UserRole.ADMIN
customer = await container.register_b2b_uc.execute(dto, requester=current_user)
# Si requester no es ADMIN -> UnauthorizedActionError
```

---

### 🔓 Mensaje de Desbloqueo para Posta 3.2 (Fullstack Dev):
Los contratos de negocio y persistencia se encuentran listos, testeados y verificados. La **Etapa Posta 3.2** se encuentra en estado **READY**. Puedes proceder a:
1. Conectar `POST /registro` a `container.solicitar_cuenta_uc.execute(dto)` mostrando mensaje de confirmación de solicitud enviada.
2. Incorporar en `/login` (y en el header o banner promocional) el botón de acceso directo *"Ingresar en Modo Demo / Simulación Comercial"* llamando a un endpoint que ejecute `authenticate_demo()` y configure la cookie de sesión.

---

## [2026-10-01] - Entrega Posta 5.1: Optimización Batch para Carrito B2B (Eliminación de N+1 Queries)

### 📌 Resumen de la Entrega:
Se optimizó radicalmente la capa de persistencia y aplicación para la carga de productos del carrito mayorista. Anteriormente, al visualizar `/carrito`, se realizaba una consulta secuencial por cada ítem contenido en el carrito (problema de N+1 queries que multiplicaba la latencia de red contra Supabase).

1. **Puerto `IProductRepository`:** Se incorporó el contrato abstracto:
   ```python
   @abstractmethod
   async def get_by_ids(self, product_ids: list[str]) -> list[Product]:
       pass
   ```
2. **Implementación `SqlAlchemyProductRepository`:**
   - Se implementó `get_by_ids` ejecutando una única sentencia SQL optimizada con cláusula `IN (...)` y eager loading mediante `selectinload` (`categoria`, `familia`, `compatibilidades`).
   - Soportó de forma híbrida IDs primarios numéricos, SKUs y códigos OEM (incluyendo alias de compatibilidad de tests).
   - Reconstruye y preserva el orden exacto en el que los IDs fueron solicitados por el cliente.
3. **Caso de Uso `GetProductDetailUseCase`:**
   - Se añadió el método de conveniencia `get_many(product_ids: list[str])` que delega de manera directa en `product_repo.get_by_ids(product_ids)`.
4. **Pruebas y Certificación:**
   - Se creó `tests/unit/test_product_repository_batch.py` validando la consulta única, orden de respuesta, soporte de SKUs/OEMs y manejo de identificadores no encontrados.
   - Suite completa de pruebas ejecutada: **29 pasadas de 29 tests (100% OK)**.

---

### 📂 Archivos Creados y Modificados:
1. [`src/application/ports/product_repository.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/application/ports/product_repository.py): Definición de `get_by_ids`.
2. [`src/adapters/repositories/sql_product_repository.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/adapters/repositories/sql_product_repository.py): Implementación batch con `selectinload` y orden preservado.
3. [`src/application/use_cases/get_product_detail.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/application/use_cases/get_product_detail.py): Método `get_many(product_ids)`.
4. [`tests/unit/test_product_repository_batch.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/tests/unit/test_product_repository_batch.py): Prueba unitaria de resolución en lote.
5. [`.team/board.json`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/.team/board.json): `etapa_posta_5_1_tech_lead_batch_products_cart` en `COMPLETED`, `etapa_posta_5_2_fullstack_optimizacion_carrito_ui` en `READY`.

---

### 🛠️ Especificación de Contrato para el Fullstack Dev (Posta 5.2):

#### En `src/adapters/controllers/web_controller.py` (endpoint `/carrito`):
Reemplazar el bucle de consultas secuenciales por una única llamada en lote:

```python
# Obtener los IDs del carrito
cart = get_cart_from_cookie(request)
product_ids = list(cart.keys())

# ÚNICA llamada a base de datos (1 ida y vuelta en lugar de N)
products = await container.get_product_detail_uc.get_many(product_ids)
# Alternativa directa equivalente:
# products = await container.product_repo.get_by_ids(product_ids)

# Iterar sobre la lista devuelta en memoria:
for prod in products:
    qty = cart.get(str(prod.id), cart.get(prod.sku, 1))
    price_vo = prod.calculate_price_for_role(role)
    item_subtotal = price_vo.amount * qty
    subtotal_amount += item_subtotal
    ...
```

---

### 🔓 Mensaje de Desbloqueo para Posta 5.2 (Fullstack Dev):
El backend se encuentra optimizado, testeado y disponible en el contenedor IoC. La **Etapa Posta 5.2** se encuentra en estado **READY**. Puedes proceder a actualizar el controlador `/carrito` para aprovechar la resolución batch y dejar la carga del carrito instantánea.

---

## [2026-10-01] - Entrega Posta 6.1: Perfil de Cliente B2B, Margen Configurable y Consulta de Pedidos

### 📌 Resumen de la Entrega:
Se implementaron las capacidades de dominio, base de datos y aplicación para que los clientes comerciales puedan configurar libremente su margen de ganancia comercial para mostrador y consultar su historial completo de pedidos:

1. **Entidad `Customer` y Modelo `ClienteModel`:**
   - Se añadió el campo `markup_percent: float = 30.0` (por defecto 30%).
   - Se añadió la columna física `markup_percent FLOAT NOT NULL DEFAULT 30.0` en PostgreSQL Supabase y en `ClienteModel` (SQLAlchemy 2.0).
   - Se aseguró mapeo resiliente con fallback `getattr(model, "markup_percent", 30.0)` en `SqlAlchemyCustomerRepository`.
2. **Cálculo Dinámico de Precio de Mostrador:**
   - En [`src/domain/entities/product.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/domain/entities/product.py), el método `calculate_price_for_role(role, custom_markup=None)` calcula de forma exacta:
     ```python
     if custom_markup is not None:
         markup_factor = 1.0 + (custom_markup / 100.0)
         return Money(amount=round(wholesale_price.amount * markup_factor, 2))
     ```
3. **Repositorios y Caso de Uso:**
   - Se agregó `update_profile(customer_id, markup_percent, phone=None, address=None)` en `ICustomerRepository` y `SqlAlchemyCustomerRepository`.
   - Se creó [`UpdateCustomerProfileUseCase`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/application/use_cases/update_customer_profile.py) validando que el porcentaje no sea negativo y se registró en [`container.update_profile_uc`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/infrastructure/config/container.py).
   - Se validó el repositorio de pedidos `order_repo.get_by_customer(customer_id)` retornando las órdenes ordenadas por fecha descendente con ítems y estados del dominio (`OrderStatus`).
4. **Pruebas y Certificación:**
   - Pruebas unitarias en `tests/unit/test_domain.py` y `tests/unit/test_customer_profile_and_orders.py`.
   - Suite completa de pruebas ejecutada: **31 pasadas de 31 tests (100% OK)**.

---

### 📂 Archivos Creados y Modificados:
1. [`src/domain/entities/customer.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/domain/entities/customer.py): Campo `markup_percent: float = 30.0`.
2. [`src/infrastructure/database/models/cliente_model.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/infrastructure/database/models/cliente_model.py): Columna `markup_percent`.
3. [`src/domain/entities/product.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/domain/entities/product.py): Parámetro `custom_markup` en `calculate_price_for_role`.
4. [`src/application/ports/customer_repository.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/application/ports/customer_repository.py): Contrato de `update_profile`.
5. [`src/adapters/repositories/sql_customer_repository.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/adapters/repositories/sql_customer_repository.py): Implementación de `update_profile` y guardado de `markup_percent`.
6. [`src/application/dtos/auth_dto.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/application/dtos/auth_dto.py): `CustomerDTO.markup_percent` y `UpdateProfileDTO`.
7. [`src/application/use_cases/update_customer_profile.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/application/use_cases/update_customer_profile.py): Caso de uso de actualización de perfil.
8. [`src/infrastructure/config/container.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/infrastructure/config/container.py): Registro de `container.update_profile_uc`.
9. [`tests/unit/test_customer_profile_and_orders.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/tests/unit/test_customer_profile_and_orders.py): Prueba unitaria integral.
10. [`.team/board.json`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/.team/board.json): `etapa_posta_6_1_tech_lead_perfil_markup_y_pedidos` en `COMPLETED`, `etapa_posta_6_2_fullstack_panel_cliente_y_pedidos_ui` en `READY`.

---

### 🛠️ Especificación de Contratos para el Fullstack Dev (Posta 6.2):

#### 1. Actualizar Margen y Datos del Perfil:
```python
from src.application.dtos.auth_dto import UpdateProfileDTO

dto = UpdateProfileDTO(
    markup_percent=float(markup_percent_form),  # Ej: 33.0
    phone=phone_form,                           # Opcional
    address=address_form                        # Opcional
)
updated_customer = await container.update_profile_uc.execute(customer_id=current_user.id, dto=dto)
```

#### 2. Consultar Historial de Pedidos del Cliente:
```python
orders = await container.order_repo.get_by_customer(current_user.id)
# orders es una list[Order] con:
# - order.id (ej: "ORD-...")
# - order.status.value (ej: "PENDIENTE_APROBACION", "EN_PREPARACION", "DESPACHADO", "ENTREGADO")
# - order.total.format_ars()
# - order.created_at
# - order.items (list[OrderItem] con product_sku, product_name, quantity, unit_price, subtotal)
```

#### 3. Calcular Precio Sugerido de Mostrador con el Margen del Cliente:
```python
# En vistas de catálogo o detalle si current_user es B2B:
user_markup = current_user.markup_percent if current_user else None
resale_price = product.calculate_price_for_role(role, custom_markup=user_markup)
```

---

### 🔓 Mensaje de Desbloqueo para Posta 6.2 (Fullstack Dev):
La base de datos, los casos de uso y las entidades se encuentran listos para construir el Panel de Mi Cuenta / Perfil. La **Etapa Posta 6.2** se encuentra en estado **READY**. Puedes proceder a:
1. Crear la vista `/perfil` (o `/mi-cuenta`) con el formulario de margen comercial.
2. Renderizar la tabla de historial de pedidos del cliente con sus badges de estado.
3. Exponer el precio de mostrador sugerido recalculado con el `markup_percent` del cliente autenticado.

---

## [2026-10-01] - Entrega Posta 7.1: Modelado de Vendedores (SALES_AGENT), Cartera de Clientes y Trazabilidad Comercial

### 📌 Resumen de la Entrega:
Se implementó la arquitectura de dominio, persistencia en Supabase PostgreSQL y casos de uso para la gestión comercial y trazabilidad de pedidos asignados a vendedores:

1. **Entidades de Dominio:**
   - [`Customer`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/domain/entities/customer.py): Incorporación del atributo `sales_agent_id: str | None = None`.
   - [`Order`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/domain/entities/order.py): Incorporación del atributo `sales_agent_id: str | None = None`.
2. **Persistencia Relacional (SQLAlchemy 2.0 & Supabase):**
   - [`ClienteModel`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/infrastructure/database/models/cliente_model.py): Agregada columna `sales_agent_id` con clave foránea referenciando a `clientes.id` (`ondelete="SET NULL"`) e índice `ix_clientes_sales_agent_id`.
   - [`OrdenModel`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/infrastructure/database/models/orden_model.py): Agregada columna `sales_agent_id` e índice `ix_ordenes_sales_agent_id`.
   - Migración física aplicada con éxito en la base de datos remota de Supabase PostgreSQL mediante `ALTER TABLE ... ADD COLUMN IF NOT EXISTS ...`.
3. **Repositorios y Contratos:**
   - [`ICustomerRepository`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/application/ports/customer_repository.py) y [`SqlAlchemyCustomerRepository`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/adapters/repositories/sql_customer_repository.py):
     * `get_sales_agents() -> list[Customer]`: Devuelve todos los clientes con rol `UserRole.SALES_AGENT` y estado activo.
     * `get_customers_by_sales_agent(sales_agent_id: str) -> list[Customer]`: Devuelve la cartera completa de clientes asignados a un vendedor.
     * `assign_sales_agent(customer_id: str, sales_agent_id: str | None) -> None`: Asigna o reasigna un vendedor a un cliente B2B.
   - [`IOrderRepository`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/application/ports/order_repository.py) y [`SqlAlchemyOrderRepository`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/adapters/repositories/sql_order_repository.py):
     * `get_by_sales_agent(sales_agent_id: str) -> list[Order]`: Retorna las órdenes generadas por los clientes de ese vendedor, ordenadas por fecha descendente con carga de ítems.
4. **Casos de Uso y Automatización:**
   - [`CreateOrderUseCase`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/application/use_cases/create_order.py): Cuando un cliente genera un pedido, se toma automáticamente su `sales_agent_id` y se estampa en la orden creada.
   - [`ManageSalesAgentUseCase`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/application/use_cases/manage_sales_agents.py): Expone `get_sales_agents()`, `get_portfolio(sales_agent_id)` y `assign_agent(customer_id, sales_agent_id, requester)`. Protege la asignación de vendedores exigiendo que `requester.role == UserRole.ADMIN`.
   - Inyección en [`container.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/infrastructure/config/container.py): Registrado `container.manage_sales_agents_uc`.
5. **Datos Semilla en Producción (Supabase):**
   - Creado vendedor semilla en la base remota:
     * ID: `cli-vendedor-001`
     * Email: `vendedor@atuelgomas.com`
     * Rol: `UserRole.SALES_AGENT`
     * Razón social: `Carlos Ventas (Zona Cuyo)`
     * CUIT: `20-33445566-7`
     * Clave: `vendedor123`
   - Asignado el cliente demo B2B (`cli-b2b-001` / `cliente@atuelgomas.com`) a la cartera de `cli-vendedor-001`.
6. **Pruebas y Certificación:**
   - Implementado test unitario integral en [`tests/unit/test_sales_agent_and_portfolio.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/tests/unit/test_sales_agent_and_portfolio.py).
   - Suite completa ejecutada: **35 pasadas de 35 tests (100% OK)**.

---

### 📂 Archivos Creados y Modificados:
1. [`src/domain/entities/customer.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/domain/entities/customer.py): Campo `sales_agent_id`.
2. [`src/domain/entities/order.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/domain/entities/order.py): Campo `sales_agent_id`.
3. [`src/infrastructure/database/models/cliente_model.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/infrastructure/database/models/cliente_model.py): Columna `sales_agent_id` con FK.
4. [`src/infrastructure/database/models/orden_model.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/infrastructure/database/models/orden_model.py): Columna `sales_agent_id`.
5. [`src/application/ports/customer_repository.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/application/ports/customer_repository.py): Métodos `get_sales_agents`, `get_customers_by_sales_agent`, `assign_sales_agent`.
6. [`src/adapters/repositories/sql_customer_repository.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/adapters/repositories/sql_customer_repository.py): Implementaciones SQL y mapeos.
7. [`src/application/ports/order_repository.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/application/ports/order_repository.py): Método `get_by_sales_agent`.
8. [`src/adapters/repositories/sql_order_repository.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/adapters/repositories/sql_order_repository.py): Implementación SQL y mapeos.
9. [`src/application/use_cases/create_order.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/application/use_cases/create_order.py): Auto-asignación de `sales_agent_id`.
10. [`src/application/use_cases/manage_sales_agents.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/application/use_cases/manage_sales_agents.py): Caso de uso de gestión y autorización.
11. [`src/application/dtos/auth_dto.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/application/dtos/auth_dto.py): DTOs `AssignSalesAgentDTO` y `CustomerDTO.sales_agent_id`.
12. [`src/infrastructure/config/container.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/src/infrastructure/config/container.py): Registro en contenedor IoC.
13. [`scripts/seed_database.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/scripts/seed_database.py): Inclusión del vendedor en seeder.
14. [`tests/unit/test_sales_agent_and_portfolio.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/tests/unit/test_sales_agent_and_portfolio.py): Pruebas de vendedor, cartera, asignación y pedidos.
15. [`tests/unit/test_solicitar_cuenta.py`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/tests/unit/test_solicitar_cuenta.py): Actualización de mock in-memory.
16. [`.team/board.json`](file:///c:/Users/burne/OneDrive/Desktop/Proyectos%20Personales/Atuel%20Gomas/.team/board.json): `etapa_posta_7_1_tech_lead_vendedores_y_cartera` a `COMPLETED`, `etapa_posta_7_2_fullstack_panel_vendedores_y_cartera_ui` a `READY`.

---

### 🛠️ Especificación de Contratos para el Fullstack Dev (Posta 7.2):

#### 1. Obtener Cartera de Clientes para el Vendedor Logueado:
```python
# Si current_user.role == UserRole.SALES_AGENT:
cartera_clientes = await container.manage_sales_agents_uc.get_portfolio(current_user.id)
# Cada elemento es un Customer:
# - cliente.id
# - cliente.business_name
# - cliente.cuit.value
# - cliente.email
# - cliente.phone (útil para armar enlace https://wa.me/549...)
# - cliente.business_line.value
```

#### 2. Obtener Pedidos Generados por la Cartera del Vendedor:
```python
# Órdenes de todos los clientes a cargo del vendedor:
orders = await container.order_repo.get_by_sales_agent(current_user.id)
# Lista de Order con id, customer_id, total, status, items, created_at
```

#### 3. Obtener Lista de Vendedores para Dropdown Administrativo:
```python
vendedores = await container.manage_sales_agents_uc.get_sales_agents()
# Lista de Customer con role == UserRole.SALES_AGENT (id, business_name, email)
```

#### 4. Asignar o Reasignar Vendedor a un Cliente (Solo ADMIN):
```python
# Requiere requester=current_user (debe ser ADMIN)
await container.manage_sales_agents_uc.assign_agent(
    customer_id=cliente_id,
    sales_agent_id=vendedor_id, # o None para desasignar
    requester=current_user
)
```

---

### 🔓 Mensaje de Desbloqueo para Posta 7.2 (Fullstack Dev):
El backend, los esquemas relacionales en Supabase, los casos de uso protegidos y los métodos de consulta están completamente listos y verificados. La **Etapa Posta 7.2** se encuentra en estado **READY**. Puedes proceder a:
1. Crear el Panel Comercial del Vendedor (`/vendedor` o pestaña en `/perfil` cuando `current_user.role == UserRole.SALES_AGENT`) mostrando la cartera asignada, los pedidos generados y botón de contacto por WhatsApp.
2. Crear o integrar en la vista Admin (`/admin/clientes` o similar) el selector reactivo para asignar/reasignar vendedores a los clientes.









