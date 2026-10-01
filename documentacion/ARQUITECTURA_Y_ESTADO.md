# DOCUMENTACIÓN GENERAL DEL PROYECTO: ATUEL GOMAS
**Sistema Web B2B y Catálogo Técnico para Venta Mayorista y Minorista**  
**Arquitectura:** Clean Architecture (Robert C. Martin / Uncle Bob) + Patrón MVC  
**Lenguaje Principal:** Python 3.12+ (FastAPI + Jinja2 + HTMX)  
**Fecha de Actualización:** Septiembre 2026  

---

## 1. ¿Qué es este proyecto y para qué sirve?

**Atuel Gomas** es una plataforma web desarrollada para un comercio e industria dedicado a la distribución y venta de:
- **Línea Automotor:** Mangueras de radiador y calefacción conformadas, fuelles de semieje y dirección, correas de distribución y poly-v, burletes perimetrales de cabina.
- **Línea Industrial y Ferretería:** Mangueras hidráulicas de alta presión (mallas de acero), planchas y pisos de goma antideslizante (moneda, grano arroz, bastón), abrazaderas sin fin / súper presión, acoples rápidos, cadenas, remaches y elementos de protección personal (EPP).

### Objetivos Clave de Negocio:
1. **Atención B2B (Ferreterías y Casas de Repuestos):** Lista de precios mayorista protegida, solicitud de pedidos por volumen y presupuestos ágiles.
2. **Atención al Consumidor Final y Talleres:** Catálogo técnico público abierto con búsqueda por compatibilidad vehicular (marca, modelo, año) y derivación inmediata a WhatsApp comercial.
3. **Escalabilidad y Seguridad:** Sistema concebido bajo estándares bancarios/OWASP (cookies HttpOnly, hashes Argon2/Bcrypt) para crecer sin deuda técnica.

---

## 2. Decisiones de Arquitectura y Principios de Diseño

El sistema está construido siguiendo dos pilares innegociables:
1. **Clean Architecture (Arquitectura Limpia):** La lógica de negocio y las entidades no dependen de ninguna base de datos, librería web o framework externo.
2. **Principios SOLID:**
   - **SRP (Single Responsibility Principle):** Cada clase, caso de uso, entidad o interfaz está alojada en su propio archivo independiente. Los archivos `__init__.py` se mantienen limpios.
   - **ISP (Interface Segregation Principle):** Interfaces/puertos específicos y granulares (`IProductRepository`, `ICustomerRepository`, `IOrderRepository`, `IPasswordHasher`).
   - **DIP (Dependency Inversion Principle):** Los casos de uso dependen de abstracciones (puertos), inyectadas centralizadamente a través de un contenedor IoC (`container.py`).
3. **Patrón MVC (Model-View-Controller) Moderno:**
   - **Modelo:** Entidades de Dominio puras (`Product`, `Customer`, `Order`, `Dimensions`, `Money`, `CUIT`).
   - **Vista:** Renderizado del lado del servidor (SSR) mediante **Jinja2** potenciado con **HTMX**, logrando dinamismo en tiempo real (búsquedas instantáneas de repuestos) sin el bloat ni la complejidad de un frontend SPA desacoplado en React/Vue.
   - **Controlador:** Endpoints web en FastAPI encargados del flujo HTTP, cookies seguras y llamado a casos de uso.

---

## 3. Estructura del Código Fuente

```text
Atuel Gomas/
├── src/
│   ├── domain/                         # 1. CAPA DE DOMINIO (Reglas de Negocio Puras)
│   │   ├── entities/                   # Entidades (1 archivo por clase)
│   │   │   ├── product.py              # Entidad Producto, cálculo de precios y stock
│   │   │   ├── customer.py             # Entidad Cliente B2B con validación de aprobación
│   │   │   ├── order.py                # Entidad Orden de Pedido
│   │   │   ├── order_item.py           # Ítem individual de pedido
│   │   │   ├── product_category.py     # Enumerador de categorías del catálogo
│   │   │   ├── user_role.py            # Roles (Público, B2B_Client, Vendedor, Admin)
│   │   │   ├── vehicle_compatibility.py# Marca, modelo, motorización y años compatibles
│   │   │   └── order_status.py         # Estados de pedido (Pendiente, Preparación, etc.)
│   │   ├── value_objects/              # Objetos de Valor Inmutables
│   │   │   ├── money.py                # Manejo de divisas (ARS) y formato contable
│   │   │   ├── dimensions.py           # Diámetros interiores/exteriores, espesores, largos
│   │   │   └── cuit.py                 # Validación estricta de 11 dígitos fiscales
│   │   └── exceptions/                 # Excepciones de negocio
│   │       └── domain_exceptions.py    # InsufficientStockError, CustomerAlreadyExistsError...
│   │
│   ├── application/                    # 2. CAPA DE APLICACIÓN (Casos de Uso del Negocio)
│   │   ├── ports/                      # Interfaces y Contratos de Repositorios (ISP)
│   │   │   ├── product_repository.py   # IProductRepository
│   │   │   ├── customer_repository.py  # ICustomerRepository
│   │   │   ├── order_repository.py     # IOrderRepository
│   │   │   └── password_hasher.py      # IPasswordHasher
│   │   ├── use_cases/                  # Casos de Uso atómicos (1 por archivo - SRP)
│   │   │   ├── search_products.py      # Búsqueda multicriterio y cálculo de precios por rol
│   │   │   ├── get_product_detail.py   # Obtención de ficha técnica de producto
│   │   │   ├── register_b2b_customer.py# Registro de cuenta de gremio
│   │   │   ├── authenticate_customer.py# Login y verificación de credenciales
│   │   │   └── create_order.py         # Creación de orden mayorista con control de stock
│   │   └── dtos/                       # Data Transfer Objects (Pydantic)
│   │       ├── product_dto.py          # DTOs de búsqueda y vista de productos
│   │       ├── auth_dto.py             # DTOs de login y registro
│   │       └── order_dto.py            # DTOs de creación de pedidos
│   │
│   ├── adapters/                       # 3. ADAPTADORES DE INTERFAZ (Controladores y Repos)
│   │   ├── controllers/                # Controladores Web MVC
│   │   │   └── web_controller.py       # Rutas HTTP, Jinja2 y endpoints HTMX
│   │   ├── repositories/               # Repositorios concretos desacoplados
│   │   │   ├── product_repo.py         # MemoryProductRepository (con catálogo inicial)
│   │   │   ├── customer_repository.py  # MemoryCustomerRepository
│   │   │   └── order_repository.py     # MemoryOrderRepository
│   │   └── security/                   # Adaptador criptográfico
│   │       └── hasher.py               # BcryptPasswordHasher (12 rounds de salting)
│   │
│   └── infrastructure/                 # 4. INFRAESTRUCTURA Y FRAMEWORKS
│       ├── config/                     # Contenedor central de Inyección de Dependencias
│       │   └── container.py            # Container IoC
│       ├── static/                     # Assets estáticos
│       │   ├── css/main.css            # Estilos CSS modernos industriales (tema grafito/ámbar)
│       │   └── img/                    # Imágenes técnicas de productos
│       └── templates/                  # Vistas HTML5 + Jinja2 + HTMX
│           ├── base.html               # Layout maestro con navbar y footer corporativo
│           ├── index.html              # Portada con buscador técnico en vivo
│           ├── product_detail.html     # Ficha métrica y compatibilidad de repuestos
│           ├── login.html              # Formulario de acceso mayorista
│           ├── register.html           # Solicitud de cuenta para ferreterías/repuesteras
│           └── partials/product_grid.html # Grid reactivo actualizado por HTMX
│
├── tests/                              # SUITE DE PRUEBAS AUTOMATIZADAS
│   ├── unit/test_domain.py             # Tests unitarios puros de lógica de negocio (sin DB)
│   └── integration/test_web.py         # Tests de integración HTTP de rutas y templates
│
├── datos provicionales/                # ÁREA DE EXTRACCIÓN Y NORMALIZACIÓN DE DATOS
│   ├── Para la revista del burneeee.xlsx # Archivo Excel original maestro
│   ├── extractor_catalogo.py           # Script para volcar hojas e imágenes a carpetas
│   ├── normalizador_tablas.py          # Script de atomización y desglose de subtablas
│   ├── clasificador_familias_y_esquema.py # Script de clasificación profunda y esquemas 3FN
│   └── [01 a 27]_NOMBRE_PAGINA/        # 27 carpetas con TXTs normalizados, imágenes y esquemas
│
├── documentacion/                      # DOCUMENTACIÓN INTEGRAL DEL PROYECTO
│   └── ARQUITECTURA_Y_ESTADO.md        # Este documento maestro
│
├── Dockerfile                          # Contenedor para despliegue en producción (Render/Railway)
├── requirements.txt                    # Dependencias del entorno Python
├── README.md                           # Guía de inicio rápido
└── main.py                             # Entrypoint de la aplicación FastAPI
```

---

## 4. Pasos y Tareas Realizadas hasta la Fecha

A lo largo del proyecto se han completado las siguientes fases:

### Fase 1: Planificación y Diseño Arquitectónico
- Se diseñó el plan técnico integral respetando Clean Architecture y MVC.
- Se definió la estrategia de seguridad OWASP (Bcrypt, sesiones en cookies `HttpOnly`, protección CSRF, consultas parametrizadas).
- Se seleccionó el stack: Python 3.12+, FastAPI, Jinja2, HTMX, Pydantic, SQLAlchemy y Pytest.
- Se definió el plan de hosting de costo $0 inicial: Repositorio en **GitHub** con integración continua (CI/CD) hacia **Render.com** o **Railway.app**, utilizando **Neon.tech** para PostgreSQL en la nube.

### Fase 2: Implementación del Core (Clean Architecture + MVC)
- Creación de la capa de Dominio con validaciones estrictas (`Product`, `Customer`, `Order`, `Dimensions`, `Money`, `CUIT`).
- Creación de los Casos de Uso en la capa de Aplicación (`search_products`, `get_product_detail`, `register_b2b_customer`, `authenticate_customer`, `create_order`).
- Creación de las Vistas (`index.html`, `product_detail.html`, `login.html`, `register.html`, `base.html`, `product_grid.html`) con diseño industrial moderno, responsivo y dinámico mediante HTMX.
- Ensamblado mediante Inversión de Dependencias en `container.py`.

### Fase 3: Refactorización a Principios SOLID Estrictos
- A pedido expreso de no violar SRP e ISP:
  - Se desglosó cada clase en su propio archivo individual.
  - Se vaciaron los archivos `__init__.py` para evitar acoplamientos circulares y mantener paquetes Python impecables.
  - Se configuró la suite de tests en `tests/`, alcanzando **100% de éxito (6/6 tests pasando)**.

### Fase 4: Procesamiento, Extracción y Normalización de Datos del Catálogo
- Se incorporó el archivo de Excel real de la empresa: `Para la revista del burneeee.xlsx` dentro de la carpeta `datos provicionales/`, **sin tocar ninguna línea del sistema principal**.
- **Extracción de Páginas e Imágenes:**
  - Se crearon 27 carpetas dedicadas (una por cada hoja del Excel).
  - Se extrajeron **12.461 registros** de artículos a archivos `articulos.txt`.
  - Se recuperaron **28 imágenes técnicas incrustadas** (`imagen_1.jpg`, `imagen_2.png`, etc.).
- **Normalización Atómica y Desacoplamiento de Subtablas:**
  - Se detectaron subtablas paralelas que convivían en la misma hoja (ej. Mangueras Moldeadas vs Mangueras por Metro; Cintas vs Guantes vs Tubos; Cadenas vs Remaches vs Grampas) y se separaron en archivos individuales.
  - Se resolvió la jerarquía padre/hijo para que cada variante tenga una descripción completa y su precio correspondiente.
- **Clasificación Profunda y Atributos Relacionales:**
  - En páginas heterogéneas como `08_GUANTES_COMPLETA` (que mezclaba calzado, cascos, arneses, guantes y ropa), se crearon archivos específicos para cada familia:
    * `articulos_calzado_de_seguridad.txt` (con talles 36-46 y puntera de acero/aluminio desglosada)
    * `articulos_proteccion_craneana_y_facial.txt` (con colores de cascos y accesorios)
    * `articulos_trabajo_en_altura_y_arneses.txt`
    * `articulos_guantes_y_proteccion_manos.txt`
    * `articulos_indumentaria_laboral.txt`
    * etc.
  - En cada carpeta se generó el archivo `ESQUEMA_TABLAS_Y_RELACIONES.txt` que documenta el modelo relacional en Tercera Forma Normal (3FN) con tablas maestras, tablas de catálogo de atributos (talles, materiales, colores, punteras) y tablas puente (`M:N`).

---

## 5. ¿Dónde estamos parados hoy y cuál es el próximo paso?

### Estado Actual (4 Etapas Secuenciales Completadas):
1. **Persistencia Real en Base de Datos (Etapa 1):** SQLAlchemy 2.0 completamente modelado en 3FN con tablas maestras, atributos y puentes `M:N`.
2. **Ingesta Masiva y Catálogo Real (Etapa 2):** Seeder ejecutado con éxito, poblando **12.828 productos técnicos**, 7 categorías, 42 familias, 1.267 variantes y 9.777 aplicaciones vehiculares en `atuel_gomas.db`.
3. **Repositorios SQL y Paginación (Etapa 3):** Repositorios desacoplados enchufados al contenedor IoC (`container.py`), con consultas optimizadas y conteos dinámicos.
4. **UI Reactiva y Seguridad (Etapa 4):** Catálogo con paginación HTMX instantánea, filtros sincronizados con URL (`hx-push-url`) y sesiones B2B aseguradas con firmas criptográficas HMAC-SHA256 contra spoofing. Suite de pruebas con **11/11 tests aprobados**.

### Próximos Pasos Sugeridos para Producción:
1. **Despliegue Cloud (Producción):**
   - Subir el repositorio a GitHub y conectar el despliegue automático a Render.com o Railway.app.
   - Conectar un cluster administrado de PostgreSQL (ej: Neon.tech o Supabase) configurando la variable de entorno `DATABASE_URL`.
2. **Panel de Gestión (Backoffice B2B):**
   - Interfaz interna para que los vendedores de Atuel Gomas aprueben solicitudes de registro de cuentas de gremio (`Customer.is_approved = True`).
   - Módulo de carga masiva/actualización de listas de precios mediante subida de archivos Excel.
3. **Checkout y WhatsApp:**
   - Botón en el carrito de compras para exportar el pedido en PDF formal con membrete y derivar la orden formateada directamente al WhatsApp de ventas.
