# PLAN DE MEJORAS FASE 3: SEGREGACIÓN DE CORREAS, REUBICACIÓN Y SUBCATEGORÍAS
**Modalidad:** Híbrida (Simultánea en Preparación + Secuencial en Integración de Filtros)  
**Fecha:** Septiembre 2026

---

## 1. Diagrama de Gantt

```mermaid
gantt
    title Fase 3: Correas, Accesorios y Subítems de Mangueras
    dateFormat  X
    axisFormat %s

    section Tech Lead
    Etapa 3.1: Reorganizar DB, Segregar Correas y API get_families :active, tl1, 0, 4

    section Fullstack Dev
    Etapa 3.2 (SIMULTÁNEA): Maquetación visual de Subítems en UI    :active, fs1, 0, 3
    ESPERA AL TECH LEAD (Etapa 3.1)                                :crit, wait1, 3, 4
    Etapa 3.3 (DEPENDIENTE): Conectar /api/familias y Filtro HTMX   :fs2, 4, 7
```

---

## 2. Objetivos Específicos de la Fase 3

1. **Correas Exclusivas por Rubro:**
   - **Autopartes:** Únicamente *Correas Automotor y Poly-V* (distribución y accesorios vehiculares).
   - **Ferretería Industrial:** Únicamente *Correas Industriales* (perfiles en V: A, B, C) y *Cintas Rotoenfardadoras*.
2. **Reubicación de Escobillas, Cebadores y Caños:**
   - Sacar *Escobillas Limpiaparabrisas* y *Cebadores* de la bolsa de mangueras, reubicándolos en la categoría *Accesorios y Mantenimiento Automotor*.
   - Mover *Caños Pileteros* a *Ferretería Industrial / Conducción de Fluidos*.
3. **Subítems y Familias para Mangueras Automotor (+9.000 artículos):**
   - Permitir al usuario filtrar directamente por aplicación sin tener que recorrer 500 páginas:
     - 🌡️ **Radiador (Superior, Inferior, Derivaciones)** (~2.555 artículos)
     - 💨 **Admisión de Aire y Filtros** (~555 artículos)
     - ⛽ **Combustible y Retorno** (~308 artículos)
     - 🚀 **Turbo e Intercooler** (~285 artículos)
     - ❄️ **Calefacción y Climatización** (~52 artículos)
     - 🛡️ **Fuelles de Suspensión y Dirección** (~36 artículos)
     - 📏 **Mangueras por Metro** (~469 artículos)
