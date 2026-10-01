# PLAN DE MEJORAS FASE 2: ATUEL GOMAS
**Modalidad:** Trabajo Híbrido (Simultáneo en Tareas Desacopladas + Secuencial en Vistas de Catálogo)  
**Fecha:** Septiembre 2026

---

## 1. Diagrama de Gantt: ¿Qué se hace en simultáneo y qué debe esperar?

```mermaid
gantt
    title Fase 2: Rubros Comerciales, Vistas Institucionales e Imágenes
    dateFormat  X
    axisFormat %s

    section Tech Lead
    Etapa 2.1: Rubros (Autopartes vs Ferretería), DB e Imágenes :active, tl1, 0, 4

    section Fullstack Dev
    Etapa 2.2 (SIMULTÁNEA): Páginas /nosotros y /contacto        :active, fs1, 0, 3
    ESPERA AL TECH LEAD (Etapa 2.1)                             :crit, wait1, 3, 4
    Etapa 2.3 (DEPENDIENTE): Pestañas de Rubro y Filtros DB      :fs2, 4, 7
```

---

## 2. Detalle de Tareas por Agente

### 👑 Tech Lead (Backend & Core)
- **Tarea (Etapa 2.1 - INICIO INMEDIATO):**
  1. **Campo de Rubro (`BusinessLine`):** Crear enum `BusinessLine` (`AUTOPARTES`, `FERRETERIA`, `AMBOS`) y agregar la columna `rubro` en `ProductoModel`, `CategoriaModel` y `ClienteModel`.
  2. **Reclasificación de Tubos Termocontraíbles:** Reasignar su categoría/familia a `Ferretería Industrial / Accesorios Técnicos`.
  3. **Categorías Dinámicas con Conteo:** Modificar `get_categories()` en `sql_product_repository.py` para devolver las categorías reales de la base de datos (con su nombre exacto, slug, rubro y cantidad de productos), resolviendo el bug de *Pisos de Goma*, *Fuelles* y *Burletes*.
  4. **Enlace de Imágenes Reales:** Copiar las imágenes técnicas de `datos provicionales/` hacia `src/infrastructure/static/img/catalogo/` y asignar rutas válidas en `ProductoModel.imagen_url` por familia/categoría.
  5. **Criterio de Parada:** Actualizar `.team/board.json` (`etapa_2_1` a `COMPLETED`) y documentar los nuevos métodos en `.team/changelog/backend.md`.

---

### 🎨 Fullstack Dev (UI, HTMX & Controllers)
- **Tarea Inicial (Etapa 2.2 - SIMULTÁNEA - INICIO INMEDIATO):**
  1. **Páginas Institucionales:**
     - Crear `src/infrastructure/templates/nosotros.html` (Historia comercial de Atuel Gomas, valores y cobertura nacional).
     - Crear `src/infrastructure/templates/contacto.html` (Formulario de consulta, dirección y botón flotante/directo a WhatsApp).
     - Crear los endpoints `@router.get("/nosotros")` y `@router.get("/contacto")` en `web_controller.py`.
  2. **Estética de Precios:** Destacar visualmente el badge de *"Precio Mayorista Gremio"* cuando el usuario esté logueado.
  3. **🛑 CRITERIO DE ESPERA:** Cuando termines esto, **DETENTE**. No toques el catálogo principal (`index.html`) hasta que el Tech Lead termine la Etapa 2.1 y publique los contratos de rubros en `backend.md`.

- **Tarea Secundaria (Etapa 2.3 - TRAS EL RELEVO DEL TECH LEAD):**
  1. Incorporar en `index.html` las dos pestañas de acceso directo:
     - 🚗 **Línea Automotor y Autopartes**
     - 🏭 **Línea Ferretería Industrial y EPP**
  2. Modificar el selector de categorías para consumir la lista dinámica devuelta por el backend.
  3. Si hay un cliente logueado, preseleccionar automáticamente su rubro comercial (`cliente.business_line`).
  4. **Criterio de Parada:** Actualizar `etapa_2_3` a `COMPLETED` en `.team/board.json` y documentar en `.team/changelog/frontend.md`.
