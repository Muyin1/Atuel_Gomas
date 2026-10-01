# PROTOCOLO DE TRABAJO MULTI-AGENTE: ATUEL GOMAS
**Modalidad:** Postas Secuenciales (Un agente activo por turno)

Este documento establece las reglas obligatorias de sincronización, gobernanza y delimitación de código para cualquier agente de IA o desarrollador que opere en este repositorio.

---

## 1. Regla de Oro: Paso 0 Obligatorio y Relevos
Antes de planificar, sugerir cambios o escribir una sola línea de código, **CADA AGENTE DEBE**:
1. Leer `.team/board.json` para verificar en qué etapa se encuentra el proyecto.
2. Leer el changelog del rol anterior en `.team/changelog/` para conocer qué contratos, tablas o rutas fueron publicados y dejados como insumo.
3. Si la etapa asignada depende de una etapa previa que **NO** está en estado `"COMPLETED"`, **ESTÁ ESTRICTAMENTE PROHIBIDO** inventar suposiciones o código ficticio. Debe responder al usuario:
   > *"Esperando a que la Etapa previa sea completada por [Rol]."*

---

## 2. Delimitación Estricta de Áreas de Trabajo (Scopes)

Para evitar pisar código y mantener la arquitectura Clean Architecture + MVC:

### 👑 Rol 1: Tech Lead (Backend & Core Architecture)
- **Etapas asignadas:** Etapa 1 (Modelos y DB) y Etapa 3 (Repositorios SQL y Paginación).
- **Áreas permitidas:**
  - `src/domain/` (Entidades, Value Objects, Excepciones)
  - `src/application/` (Casos de Uso, Ports, DTOs de negocio)
  - `src/adapters/repositories/` (Implementaciones SQL / In-Memory)
  - `src/infrastructure/database/` (Modelos SQLAlchemy 2.0, conexiones, migraciones)
  - `src/infrastructure/config/` (Contenedor IoC `container.py`)
  - `.team/changelog/backend.md` y actualizar etapas correspondientes en `.team/board.json`.
- **Prohibido tocar:**
  - `src/infrastructure/templates/` (HTML Jinja2)
  - `src/infrastructure/static/` (CSS/JS)
  - `scripts/` (Scripts ETL del Data Specialist)

### 📊 Rol 2: Data Specialist (ETL & Sincronización)
- **Etapas asignadas:** Etapa 2 (Seeder e Ingesta masiva).
- **Áreas permitidas:**
  - `scripts/` (Scripts de parseo, seeding de base de datos e ingesta)
  - `datos provicionales/` (Archivos de insumo, TXTs normalizados)
  - `.team/changelog/data.md` y actualizar `etapa_2_ingesta_y_datos` en `.team/board.json`.
- **Prohibido tocar:**
  - `src/adapters/controllers/`
  - `src/infrastructure/templates/`
  - `src/domain/`

### 🎨 Rol 3: Fullstack Dev (UI, HTMX & Controllers)
- **Etapas asignadas:** Etapa 4 (UI reactiva, filtros y seguridad).
- **Áreas permitidas:**
  - `src/infrastructure/templates/` (HTML5, layouts, parciales HTMX)
  - `src/infrastructure/static/` (CSS industrial, JS mínimo)
  - `src/adapters/controllers/web_controller.py` (Endpoints que renderizan vistas SSR y endpoints reactivos HTMX)
  - `.team/changelog/frontend.md` y actualizar `etapa_4_frontend_y_seguridad` en `.team/board.json`.
- **Prohibido tocar:**
  - `src/domain/` (No altera lógica de negocio pura)
  - `src/infrastructure/database/models/` (No define tablas ORM)
  - `scripts/` (No toca ETL)

---

## 3. Protocolo Obligatorio de Finalización y Detención (Criterio de Parada)
Al concluir el objetivo exacto de la etapa:
1. **Actualizar `.team/board.json`:**
   - Cambiar el `status` de la etapa actual a `"COMPLETED"`.
   - Cambiar la siguiente etapa a `"READY"`.
   - Actualizar el campo `ultimo_evento`.
2. **Documentar en el Changelog Propio (`.team/changelog/{tu_rol}.md`):**
   - Fecha y resumen de la entrega.
   - Lista de archivos creados o modificados.
   - **Mensaje claro de desbloqueo:** Explicar qué modelos, esquemas, rutas o datos quedan listos para que el siguiente agente tome la posta sin fricción.
3. **Detenerse de inmediato:** Informar al usuario que la etapa está terminada y ceder el turno para el siguiente rol.
