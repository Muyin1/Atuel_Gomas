# Registro de Cambios - Data Specialist (ETL & Sincronización)

Este archivo registra las entregas de scripts de ingesta masiva (Seeder), normalización de datos y balance del catálogo comercial.

---

## [2026-09-23] - Entrega Etapa 2: Ingesta Masiva del Catálogo Técnico y Carga de Base de Datos Real

### 📌 Resumen de la Entrega:
Se desarrolló e implementó el script integral de ingesta masiva (`scripts/seed_database.py`), ejecutando la carga estructurada y normalizada de los insumos comerciales contenidos en las 27 carpetas de `datos provicionales/`. 

La ingesta pobló la base de datos relacional (`atuel_gomas.db` / SQLAlchemy 2.0) respetando la Tercera Forma Normal (3FN), vinculando artículos a una jerarquía de **7 Categorías Maestras** y **42 Familias Técnicas**, extrayendo variantes dimensionales (talles, materiales, colores, punteras), derivando compatibilidades vehiculares multimarca y creando cuentas de demostración para clientes mayoristas B2B y administradores.

---

### 📂 Archivos Creados y Modificados:
1. `scripts/seed_database.py` (Script Seeder modular de alta velocidad y ejecución idempotente)
2. `atuel_gomas.db` (Base de datos relacional con 12.828 artículos técnicos y tablas puente pobladas)
3. `.team/board.json` (Actualización: Etapa 2 -> `COMPLETED`, Etapa 3 -> `READY`)
4. `.team/changelog/data.md` (Este documento con el inventario auditado)

---

### 📊 Balance Auditado de Registros Persistidos en Base de Datos:

| Tabla Física (`Model`) | Registros Cargados | Descripción Técnica |
| :--- | :---: | :--- |
| `categorias` (`CategoriaModel`) | **7** | Categorías maestras del catálogo general |
| `familias` (`FamiliaModel`) | **42** | Subfamilias y divisiones técnicas por línea de producto |
| `productos` (`ProductoModel`) | **12.828** | Total de artículos comerciales con precios base y mayoristas |
| `producto_variantes` (`VarianteModel`) | **1.267** | Variantes dimensionales y de composición técnica |
| `talles_medidas` (`TalleModel`) | **103** | Talles normalizados (ej: 36..46, 1/2", 3mm x 1m) |
| `colores` (`ColorModel`) | **16** | Colores industriales con código hex (ej: Negro, Amarillo) |
| `materiales` (`MaterialModel`) | **10** | Compuestos (Cuero Descarne, EPDM, Nitrilo, Látex, PVC) |
| `punteras_seguridad` (`PunteraModel`) | **4** | Punteras homologadas (Acero, Aluminio, Dieléctrica, Sin puntera) |
| `producto_compatibilidad_vehicular` (`CompatibilidadVehicularModel`) | **9.777** | Aplicaciones vehiculares (Renault, Ford, Fiat, VW, etc.) |
| `clientes` (`ClienteModel`) | **2** | Cuentas iniciales: Cliente B2B mayorista y Administrador |

---

### 🏷️ Distribución del Catálogo por Categoría Principal:

1. **Mangueras Automotor:** `9.622` artículos
   - Familias: Mangueras de Goma Moldeada (radiador, calefacción, retorno, turbo), Mangueras por Metro, Escobillas Limpiaparabrisas, Cebadores y Caños Pileteros.
2. **Artículos de Protección y EPP:** `1.295` artículos
   - Familias: Calzado de Seguridad (con variantes de talle, cuero y puntera de acero), Guantes de Protección (vaqueta, nitrilo, látex), Protección Craneana y Facial, Trabajo en Altura y Arneses, Indumentaria Laboral, Ocular, Auditiva, Seguridad Vial, Cintas Reflectivas, Tubos Termocontraíbles y Diafragmas.
3. **Correas y Transmisión:** `724` artículos
   - Familias: Correas Automotor y Poly-V, Correas Industriales en V (perfiles A, B, C) y Cintas Rotoenfardadoras para agro.
4. **Mangueras Industriales e Hidráulicas:** `614` artículos
   - Familias: Mangueras Industriales de alta resistencia, Mangueras Hidrocarburo (rollos 50m), Mangueras Air-House 300 LB, Fumigación 120 BAR, Mangas PVC para riego y Látex natural.
5. **Ferretería Industrial y Autopartes:** `369` artículos
   - Familias: O-Rings y Sellos hidráulicos, Cadenas a rodillos, Grampas, Remaches, Líquidos de Freno (DOT3/DOT4) y Precintos.
6. **Abrazaderas y Acoples:** `186` artículos
   - Familias: Abrazaderas Mini Americana, Fleje Ancho tipo Americana, Súper Presión, Abrazaderas de Alambre, Acoples Rápidos y Acoples de Aluminio.
7. **Pisos y Revestimientos:** `18` artículos
   - Familias: Pisos de Goma antideslizante (moneda, grano de arroz), Cuerinas Técnicas y Rollos Cristal PVC.

---

### ⚙️ Lógica de Transformación y Precios Aplicada:
- **Precios Mayoristas B2B (`precio_mayorista_b2b`):** Corresponde exactamente al "Precio sin Iva" neto provisto en los listados originales.
- **Precios de Lista / Consumidor (`precio_base`):** Calculado con un recargo comercial sugerido del 30% (`raw_price * 1.30`).
- **Stock:** Stock simulado asignado por algoritmo determinístico entre 15 y 85 unidades para garantizar disponibilidad inmediata en catálogo.
- **Normalización de SKUs:** En artículos donde el código estaba embebido en la descripción (ej: `CORREAS AUTOMOTOR - 10AV0535`), se aisló el código técnico exacto (`10AV0535`) como SKU. En artículos sin código explícito se toleró `NULL` o el código original, apoyándose en la clave primaria irrepetible `id`.

---

### 🔓 Mensaje de Desbloqueo para Etapa 3 (Tech Lead):
La base de datos SQLite `atuel_gomas.db` queda completamente poblada con volumen de datos real (**12.828 artículos**).

Para la implementación de `SqlAlchemyProductRepository`:
1. **Conexión:** Utilizar `SessionLocal` o `get_db_context()` desde `src.infrastructure.database.connection`.
2. **Paginación indispensable:** Dado el volumen de 12.828 productos, la implementación de `search()` **debe recibir `page` y `page_size`** (o `limit` y `offset`) para evitar saturar memoria o tiempos de respuesta HTTP.
3. **Filtros requeridos:**
   - Por texto libre (`query`): Búsqueda insensible a mayúsculas sobre `ProductoModel.nombre`, `ProductoModel.sku` y `ProductoModel.codigo_oem`.
   - Por categoría: Búsqueda cruzando `ProductoModel.categoria_id == CategoriaModel.id` o por slug de categoría.
   - Por compatibilidad vehicular: Búsqueda cruzando `ProductoModel.compatibilidades` con `CompatibilidadVehicularModel.marca` y `CompatibilidadVehicularModel.modelo` (o marca "Universal Automotor").
4. **Clientes B2B listos para autenticación:**
   - Email: `cliente@atuelgomas.com` (Rol: `b2b_client`, Aprobado: `True`)
   - Email: `admin@atuelgomas.com` (Rol: `admin`, Aprobado: `True`)

El relevo queda habilitado y en estado `"READY"` en `.team/board.json`.

---

## [2026-09-30] - Entrega Posta 2: Migración Masiva de Datos a PostgreSQL en la Nube (Supabase)

### 📌 Resumen de la Entrega:
En cumplimiento con el protocolo de trabajo multi-agente, se diseñó, implementó y ejecutó el script de migración masiva por lotes `scripts/migrar_sqlite_a_supabase.py` para transferir el catálogo completo y todas las tablas relacionales 3FN desde la base de datos local SQLite (`atuel_gomas.db`) hacia la infraestructura de producción PostgreSQL alojada en **Supabase**.

La migración se ejecutó preservando la integridad referencial (orden estricto de Foreign Keys), manteniendo los identificadores primarios para no romper relaciones M:N, convirtiendo tipos nativos (booleanos y timestamps ISO-8601 con zona horaria UTC), sincronizando los punteros de secuencias autoincrementales (`pg_get_serial_sequence`) e insertando en bloques de 1.000 registros para evitar timeouts de red.

---

### 📂 Archivos Creados y Modificados:
1. `scripts/migrar_sqlite_a_supabase.py` (Script de migración e ingesta masiva por lotes con auditoría automática de conteos).
2. `.team/board.json` (Fase PostgreSQL: `etapa_posta_2_data_specialist_migracion_datos` -> `COMPLETED`, `etapa_posta_3_fullstack_verificacion` -> `READY`).
3. `.team/changelog/data.md` (Este reporte de auditoría técnica).

---

### 📊 Balance Auditado de Migración (SQLite vs Supabase PostgreSQL):

| Tabla Física (`Model`) | Filas en SQLite | Filas en Supabase | Estado de Auditoría |
| :--- | :---: | :---: | :---: |
| `categorias` (`CategoriaModel`) | 8 | **8** | `[MATCH]` 100% |
| `familias` (`FamiliaModel`) | 48 | **48** | `[MATCH]` 100% |
| `productos` (`ProductoModel`) | 12.829 | **12.829** | `[MATCH]` 100% |
| `producto_variantes` (`VarianteModel`) | 1.267 | **1.267** | `[MATCH]` 100% |
| `producto_compatibilidad_vehicular` (`CompatibilidadVehicularModel`) | 9.779 | **9.779** | `[MATCH]` 100% |
| `talles_medidas` (`TalleModel`) | 103 | **103** | `[MATCH]` 100% |
| `colores` (`ColorModel`) | 16 | **16** | `[MATCH]` 100% |
| `materiales` (`MaterialModel`) | 10 | **10** | `[MATCH]` 100% |
| `punteras_seguridad` (`PunteraModel`) | 4 | **4** | `[MATCH]` 100% |
| `clientes` (`ClienteModel`) | 2 | **2** | `[MATCH]` 100% |
| `ordenes` (`OrdenModel`) | 0 | **0** | `[MATCH]` 100% |
| `orden_items` (`OrdenItemModel`) | 0 | **0** | `[MATCH]` 100% |
| **TOTAL GENERAL** | **24.066** | **24.066** | **CONVERGENCIA TOTAL** |

- **Tiempo total de transferencia remota:** 69.07 segundos.
- **Sincronización de secuencias (`setval`):** Ejecutada con éxito sobre todas las tablas con claves primarias seriales/enteras para garantizar que futuras inserciones manuales o de pedidos operen sin colisiones de clave primaria.
- **Suite de pruebas de regresión:** Ejecutada post-migración con `pytest`: **19 de 19 tests pasaron exitosamente (100% OK)** conectando contra Supabase.

---

### 🔓 Mensaje de Desbloqueo para Posta 3 (Fullstack Dev):
La base de datos remota en Supabase contiene ahora el catálogo completo con los **12.829 productos**, sus precios, stocks, rubros (`AUTOPARTES`, `FERRETERIA`), subfamilias/aplicaciones, variantes relacionales y compatibilidades vehiculares.

Para la Posta 3 de Verificación y Frontend:
1. **Navegación en vivo:** El backend ya lee directamente de Supabase mediante `.env`.
2. **Subfamilias y Rubros:** Los 12.829 productos están distribuidos entre las 48 familias y 8 categorías segregadas por rubro.
3. **Autenticación:** Las cuentas de prueba (`cliente@atuelgomas.com` y `admin@atuelgomas.com`) están migradas y activas.
4. **Pruebas E2E:** La suite de pruebas de integración web (`tests/integration/test_web.py`) responde correctamente sobre la base de producción.

La Posta 3 se encuentra habilitada y en estado `"READY"` en `.team/board.json`.

