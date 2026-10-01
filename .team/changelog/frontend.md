# Registro de Cambios - Fullstack Dev (UI, HTMX & Controllers)

Este archivo registra las entregas de vistas Jinja2, dinamismo HTMX, controladores web, experiencia de usuario y seguridad.

---

## [2026-09-28] - Entrega Etapa 4: Paginación Reactiva HTMX, Filtros en Vivo y Seguridad de Sesión B2B

### 📌 Resumen de la Entrega:
Se implementó con éxito la navegación reactiva y paginación en tiempo real para el catálogo de más de 12.800 artículos técnicos, integrando controles de paginación industrial con Jinja2 y HTMX (`hx-get`, `hx-target="#product-grid-container"`, `hx-push-url="true"`). Se sincronizaron los formularios de búsqueda y selectores de vehículos/categorías para reiniciar a la página 1 en cada filtrado. Asimismo, se protegió la sesión de autenticación B2B contra spoofing básico mediante firmado y verificación de cookies con HMAC-SHA256.

---

### 📂 Archivos Modificados y Creados:
1. **`src/adapters/controllers/web_controller.py`**:
   - Soporte para parámetro `page: int = 1` en `/` y `/api/productos/search`.
   - Consulta del conteo total (`container.product_repo.count(...)`) y construcción de `PaginatedProductsDTO` con cálculo de `total_pages`, `has_prev` y `has_next`.
   - Rutinas de seguridad de sesión: `sign_session_cookie(user_id)` y `verify_session_cookie(cookie_value)` usando `hmac` y `hashlib.sha256` con `compare_digest`.
   - Mantenimiento y propagación de los filtros actuales (`current_query`, `current_category`, `current_brand`, `current_model`) hacia la plantilla para persistencia del estado en la paginación.
2. **`src/infrastructure/templates/partials/product_grid.html`**:
   - Cabecera con conteo exacto de artículos (ej: *"Mostrando 24 de 12.829 productos disponibles (Página 1 de 535)"*).
   - Barra de controles de paginación reactivos con HTMX:
     - Botón Primera Página (`«`) y Última Página (`»`).
     - Botones Anterior (`‹ Anterior`) y Siguiente (`Siguiente ›`).
     - Rango de botones numéricos con elipsis inteligentes (`...`).
     - `hx-push-url="true"` para permitir navegación nativa en historial del navegador (Atrás/Adelante).
3. **`src/infrastructure/templates/index.html`**:
   - Campo oculto `page=1` en el formulario para asegurar reseteo automático al tipear en búsqueda o cambiar marcas/categorías.
   - Activación de `hx-push-url="true"` en el formulario para reflejar el estado del filtro en la barra de direcciones.
   - Preservación de valores seleccionados en los campos de entrada.
4. **`src/infrastructure/static/css/main.css`**:
   - Nuevos estilos industriales para controles de paginación: `.pagination-container`, `.page-btn`, `.page-btn.active`, `.page-btn.disabled` y `.page-ellipsis`.
5. **`tests/integration/test_web.py`**:
   - Tests de integración para verificar renderizado de paginación en `/` y `/api/productos/search?page=2`.
   - Test unitario/integración para validación de firma y rechazo de cookies de sesión manipuladas/spoofed.
6. **`.team/board.json`**:
   - Etapa 4 marcada como `"COMPLETED"`.

---

### 🚀 Desempeño y Experiencia de Usuario:
- **Carga inicial (`/`)**: ~96 ms.
- **Filtrado reactivo por marca automotor (`/api/productos/search?vehicle_brand=Renault`)**: ~33 ms.
- **Paginación instantánea (`/api/productos/search?page=2`)**: ~24 ms.
- **Navegabilidad**: Fluida y sin recargas de página completa (SPA-like con server-side rendering).

---

### 🔓 Estado del Proyecto:
Todas las 4 etapas del plan secuencial (`etapa_1_modelos_y_tablas`, `etapa_2_ingesta_y_datos`, `etapa_3_repos_y_queries`, `etapa_4_frontend_y_seguridad`) se encuentran **COMPLETADAS**. El sistema Atuel Gomas cuenta con base de datos real, repositorios persistentes y frontend reactivo industrial asegurado.

---

## [2026-09-28] - Entrega Etapa 2.2 (Fase 2): Vistas Institucionales y Badges de Precios

### 📌 Resumen de la Entrega:
Se implementaron las páginas institucionales `/nosotros` y `/contacto` manteniendo la línea estética industrial y la integración con WhatsApp directo para cotizaciones. Asimismo, se renovó el diseño de los badges y etiquetas de precio (mayorista B2B con efecto glow dorado y diferenciación clara frente al precio sugerido minorista).

### 📂 Archivos Creados y Modificados:
1. **`src/infrastructure/templates/nosotros.html`**:
   - Reseña institucional sobre más de 30 años de trayectoria de Atuel Gomas.
   - Detalle de líneas de abastecimiento: Autopartes vs Ferretería Industrial.
   - Cobertura logística nacional y llamados a la acción para clientes B2B.
2. **`src/infrastructure/templates/contacto.html`**:
   - Formulario de contacto comercial y cotizaciones especiales por código OEM/muestra.
   - Tarjeta destacada de WhatsApp comercial directo para gremios y ferreterías (`+54 9 11 4000-5000`).
   - Ubicación de despacho en polo Warnes, CABA, y horarios de atención comercial.
3. **`src/adapters/controllers/web_controller.py`**:
   - Registrados endpoints `@router.get("/nosotros")`, `@router.get("/contacto")` y `@router.post("/contacto")`.
4. **`src/infrastructure/static/css/main.css`**:
   - Nuevos estilos para `.price-tag.wholesale` con resplandor dorado y tipografía técnica.
   - Insignias `.wholesale-indicator` (★ Gremio B2B) y `.retail-indicator` (PVP Lista).
5. **`src/infrastructure/templates/partials/product_grid.html`** y **`product_detail.html`**:
   - Incorporación de las nuevas insignias y clases visuales diferenciadas para usuarios logueados vs públicos.
6. **`tests/integration/test_web.py`**:
   - Tests añadidos para validar respuesta 200 en `/nosotros`, `/contacto` y envío de formulario POST `/contacto`. Total: 13 tests pasando al 100%.

### 🛑 Estado y Relevo:
- **Etapa 2.2:** `COMPLETED`.
- **Etapa 2.3:** `READY` -> `COMPLETED`.

---

## [2026-09-28] - Entrega Etapa 2.3 (Fase 2): Solapas de Rubro, Categorías Dinámicas y Catálogo Visual

### 📌 Resumen de la Entrega:
Tras la conclusión y desbloqueo de la Etapa 2.1 por parte del Tech Lead, se implementó en la portada (`index.html`) la segmentación comercial completa mediante **Solapas / Tabs de Rubro** (🌐 Catálogo Completo: 12.829 arts, 🚗 Autopartes y Transporte: 10.905 arts, y 🏭 Ferretería e Industria: 3.206 arts). Se pobló el selector de categorías dinámicamente con las categorías reales de la DB y su conteo de artículos, resolviendo de forma definitiva la navegación en *Pisos y Revestimientos*, *Fuelles*, *Burletes* y *EPP*. Además, se incorporó preselección automática por el perfil comercial del cliente (`cliente.business_line`) y renderizado de las imágenes técnicas reales del catálogo en la grilla y ficha técnica.

### 📂 Archivos Creados y Modificados:
1. **`src/infrastructure/templates/index.html`**:
   - Pestañas interactivas de rubro comercial con conteos exactos de artículos.
   - Sincronización client-side y HTMX para filtrar las opciones de categorías según el rubro activo.
   - Preselección automática del rubro preferido del cliente autenticado.
   - Envío de inputs ocultos `page=1` y `rubro` en el formulario para refresco reactivo.
2. **`src/adapters/controllers/web_controller.py`**:
   - Adaptados `@router.get("/")` y `@router.get("/api/productos/search")` para aceptar y propagar `rubro` y recibir `category` como string o slug.
   - Detección automática del `business_line` del `current_user` para activar la solapa adecuada.
   - Suministro de la lista de `CategoryItem` dinámicas al contexto de la plantilla.
3. **`src/infrastructure/templates/partials/product_grid.html`**:
   - Renderizado condicional de imágenes técnicas reales (`/static/img/catalogo/...`) con fallback SVG/emoji en caso de fallo de carga o artículos sin fotografía.
   - Preservación del parámetro `rubro` en todos los controles de paginación reactivos de HTMX.
4. **`src/infrastructure/templates/product_detail.html`**:
   - Soporte para renderizado de imágenes técnicas de alta resolución en la ficha de producto.
5. **`src/infrastructure/static/css/main.css`**:
   - Estilos para `.rubro-tabs-wrapper`, `.rubro-tab`, `.rubro-tab.active` y `.rubro-tab-count` acordes a la identidad industrial y moderna de Atuel Gomas.
6. **`tests/integration/test_web.py`**:
   - Tests de integración para pestañas de rubro, conteos dinámicos en selector y búsqueda por categoría/slug con imágenes.
   - Suite total: **16 pruebas aprobadas al 100%**.
7. **`.team/board.json`**:
   - Etapa 2.3 actualizada a `"COMPLETED"`.

### 🏁 Estado Final de la Fase 2:
Todas las etapas de la Fase 2 (`etapa_2_1_tech_lead_rubros_y_modelos`, `etapa_2_2_fullstack_paginas_institucionales`, `etapa_2_3_fullstack_filtros_rubros`) se encuentran **COMPLETED**.

---

## [2026-09-28] - Entrega Etapa 3.2 y 3.3 (Fase 3): Selector de Subfamilias, Badges de Aplicación y Segregación Reactiva

### 📌 Resumen de la Entrega:
Se implementó la maquetación visual y la arquitectura interactiva con Jinja2 + HTMX para la navegación técnica por **Subfamilias y Aplicaciones Rápidas**:
1. **Badges Rápidos de Aplicación:** Se incorporaron botones tipo píldora para filtrar instantáneamente entre aplicaciones clave de Mangueras Automotor (🌡️ Radiador: 4.660, ❄️ Calefacción: 1.245, 💨 Admisión: 794, 🚀 Turbo/Intercooler: 294, ⛽ Combustible: 398, 🛡️ Fuelles: 36, 📏 Por Metro: 469), Correas y Accesorios.
2. **Endpoint Reactivo HTMX `@router.get("/api/familias")`:** Creado en `web_controller.py` para devolver el parcial HTML `family_selector.html` filtrando las subfamilias según la categoría seleccionada y el rubro comercial activo.
3. **Segregación Estricta de Correas en la UI:**
   - En **🚗 Autopartes y Transporte**, el selector muestra exclusivamente *Correas Automotor y Poly-V*.
   - En **🏭 Ferretería e Industria**, muestra exclusivamente *Correas Industriales* y *Cintas Rotoenfardadoras*.
4. **Propagación en Paginación:** El parámetro `family` se preserva en todos los controles de navegación paginada de `product_grid.html`.

### 📂 Archivos Creados y Modificados:
1. **`src/infrastructure/templates/partials/family_selector.html`** *(Creado)*:
   - Parcial reutilizable con badges interactivos, iconos temáticos por aplicación y conteo dinámico de artículos.
2. **`src/infrastructure/templates/index.html`**:
   - Contenedor dinámico `#family-badges-wrapper-target` dentro de `filter-card`.
   - Evento `hx-get="/api/familias"` en el selector de categoría.
   - Funciones javascript `selectFamily(slug)` y actualización en `selectRubro(rubro)`.
3. **`src/adapters/controllers/web_controller.py`**:
   - Endpoint `@router.get("/api/familias")`.
   - Soporte para parámetro `family: str | None = None` en `/api/productos/search` y home `/`.
4. **`src/infrastructure/templates/partials/product_grid.html`**:
   - Enlaces de paginación reactiva actualizados para incluir `&family={{ current_family }}`.
5. **`src/infrastructure/static/css/main.css`**:
   - Estilos industriales para `.family-badges-wrapper`, `.family-badges-list`, `.family-badge`, `.family-badge.active` y `.family-badge-count`.
6. **`tests/integration/test_web.py`**:
   - Nuevos tests para validar endpoint `/api/familias`, segregación de correas por rubro y filtrado por subfamilia. Total: **19 pruebas aprobadas al 100%**.
7. **`.team/board.json`**:
   - Etapas 3.2 y 3.3 marcadas como `"COMPLETED"`.

### 🏁 Estado Final de la Fase 3:
Todas las etapas de la Fase 3 se encuentran concluidas y verificadas exitosamente.

---

## [2026-09-28] - Corrección de UX / Reactividad: Filtro Automático por Categoría y Subfamilia

### 📌 Resumen de la Corrección:
Se detectó y solucionó un conflicto de colisión de eventos HTMX entre el selector de `<select id="category">` y el formulario contenedor `<form id="catalog-filter-form">`:
1. **Conflicto de Eventos en Categoría:** El `<select id="category">` tenía un `hx-get="/api/familias"` propio que capturaba el evento `change` e impedía que el `<form>` disparara la búsqueda reactiva a `/api/productos/search`. Se desacopló la llamada con un controlador dedicado `onCategoryChange(this.value)` que:
   - Resetea el input de subfamilia (`family-input`).
   - Actualiza de forma asíncrona mediante `htmx.ajax` los badges rápidos de subfamilia acordes a la categoría seleccionada (`/api/familias?category=...&rubro=...`).
   - Despacha de inmediato el evento `change` en el formulario para refrescar en tiempo real el grid de productos con los resultados de la categoría elegida.
2. **Filtrado Automático de Subfamilias:** La función `selectFamily()` llamaba a `htmx.trigger('#catalog-filter-form', 'submit')`, pero el formulario no contaba con `submit` en su atributo `hx-trigger`. Se agregó `submit` a `hx-trigger="submit, input, change, delay:250ms"` y se implementó la función unificada `triggerSearch()` que resetea la página a 1 y dispara el refresco reactivo automático tanto al hacer clic en cualquier badge de subfamilia como al seleccionar una categoría o rubro.
3. Se pasó la referencia `this` en el evento `onclick="selectFamily('...', this)"` de `family_selector.html` para asegurar el resaltado visual inmediato del botón activo.

### 📂 Archivos Modificados:
- `src/infrastructure/templates/index.html`
- `src/infrastructure/templates/partials/family_selector.html`

### 🧪 Pruebas:
- Suite completa de 19 pruebas de integración y dominio ejecutadas y pasando con 100% de éxito.

---

## [2026-09-30] - Entrega Posta 3: Verificación Integral Frontend Supabase y Preparación para Producción en Render

### 📌 Resumen de la Entrega:
Se concluyó la **Posta 3** del ciclo de migración a la nube:
1. **Preparación de Infraestructura & Despliegue:**
   - Creación de `Procfile` para Render y PaaS con comando `web: uvicorn main:app --host 0.0.0.0 --port $PORT`.
   - Creación de `render.yaml` especificando servicio web Python 3.11, dependencias e inyección de variables de entorno seguras (`DATABASE_URL`, `SESSION_SECRET_KEY`, `ADMIN_PASSWORD`).
   - Auditoría y blindaje de `.gitignore` para excluir estrictamente `.env`, `.env.local`, `atuel_gomas.db`, `*.db` y archivos SQLite temporales.
2. **Verificación Integral de Rutas & Frontend SSR/HTMX contra Supabase Cloud:**
   - Portada `/` verificada con renderizado dinámico de 12.829 artículos técnicos, navegación fluida y tiempos de respuesta ultra-bajos.
   - Solapas de Rubro (`AUTOPARTES` y `FERRETERIA`) y selector reactivo de categorías funcionando con HTMX de forma instantánea.
   - Badges rápidos de subfamilias cargándose dinámicamente vía `/api/familias` y filtrando el catálogo en tiempo real.
   - Vistas de detalle técnico `/producto/{id}` y páginas institucionales `/nosotros` y `/contacto` respondiendo HTTP 200 OK.
   - Suite completa de 19 tests unitarios y de integración ejecutada con 100% de aprobación (`19 passed`).

### 📂 Archivos Creados y Modificados:
1. **`Procfile`** *(Creado)*: Definición del proceso web de producción.
2. **`render.yaml`** *(Creado)*: Configuración Infrastructure-as-Code para Render.
3. **`.gitignore`**: Exclusión explícita de `atuel_gomas.db` y `*.db`.
4. **`.team/board.json`**: Posta 3 actualizada a estado `"COMPLETED"`.
5. **`.team/changelog/frontend.md`**: Registro de entrega y guía de despliegue.

---

### 🚀 Guía de Despliegue a Producción (GitHub + Render):

Para que el usuario publique la aplicación en producción:

1. **Subir cambios a GitHub:**
   ```bash
   git add .
   git commit -m "chore: preparacion para despliegue en Render y verificacion de Supabase (Posta 3)"
   git push origin main
   ```
2. **Conectar en Render:**
   - Ingresar a [Render Dashboard](https://dashboard.render.com).
   - Crear un nuevo **Web Service** seleccionando el repositorio de GitHub (o usar la opción **Blueprints** detectando `render.yaml`).
   - Configurar las variables de entorno en la sección **Environment**:
     - `DATABASE_URL`: Pegar la URL de conexión a Supabase (`postgresql+psycopg2://postgres.[ref]:[password]@aws-0-us-east-2.pooler.supabase.com:5432/postgres`)
     - `SESSION_SECRET_KEY`: Una cadena secreta aleatoria o generada automáticamente.
     - `ADMIN_PASSWORD`: Clave para el panel de administración.
3. **Deploy:**
   - Render ejecutará `pip install -r requirements.txt` y levantará `uvicorn main:app --host 0.0.0.0 --port $PORT`.
   - La aplicación quedará disponible públicamente con SSL automático.
