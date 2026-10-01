"""
Clasificador Profesional y Generador de Esquema Relacional para Atuel Gomas.

Ubicación: datos provicionales/clasificador_familias_y_esquema.py
Función:
1. Re-analiza con precisión quirúrgica la columna CÓDIGO (reincorporando DPS, etc.)
2. En páginas heterogéneas como '02_ART_DE_PROTECCION', '08_GUANTES_COMPLETA', '14_PISOS', etc.,
   desglosa los artículos en archivos TXT separados e independientes por tipo de producto.
3. Para cada artículo, extrae sus variantes relacionales:
   - Talle / Medida (ej: Nro.8, Talle 42, 3MM X 1M, 1/2")
   - Material / Composición (ej: Cuero descarne, Látex, Nitrilo, EPDM, PVC, Acero Inoxidable)
   - Puntera (ej: Puntera de Acero, Puntera de Aluminio)
   - Color (ej: Blanco, Amarillo, Azul, Naranja, Negro)
4. Genera en cada carpeta un archivo maestro:
   'ESQUEMA_TABLAS_Y_RELACIONES.txt'
   que documenta la arquitectura de tablas principales, tablas de atributos y tablas puente (M:N)
   para cuando se construya la base de datos relacional.
"""

import os
import re
import openpyxl

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_NAME = "Para la revista del burneeee.xlsx"
EXCEL_PATH = os.path.join(BASE_DIR, EXCEL_NAME)


def sanitize_filename(name: str) -> str:
    clean = name.strip()
    reemplazos = {
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Ñ': 'N', 'ñ': 'n', '\ufffd': 'I'
    }
    for orig, dest in reemplazos.items():
        clean = clean.replace(orig, dest)
    clean = re.sub(r'[\\/*?:"<>|()]', '', clean)
    clean = re.sub(r'\s+', '_', clean).strip('_')
    return clean


def clean_str(val) -> str:
    if val is None:
        return ""
    s = str(val).strip().replace('\ufffd', 'I')
    return re.sub(r'\s+', ' ', s)


def parse_price(val) -> float | None:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace("$", "").replace(" ", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def extract_attributes(desc: str) -> dict:
    """Extrae talle, material, color y puntera a partir de la descripción."""
    attrs = {
        "talle": "",
        "material": "",
        "color": "",
        "puntera": ""
    }

    # Talle / Medida
    talle_match = re.search(r'(?:talle|nro\.?|tam\.?)\s*([0-9A-Za-z\-/]+|\b[SMLX]+\b)', desc, re.IGNORECASE)
    if talle_match:
        attrs["talle"] = talle_match.group(1).strip()

    # Puntera
    if re.search(r'puntera\s+de\s+acero', desc, re.IGNORECASE):
        attrs["puntera"] = "Acero"
    elif re.search(r'puntera\s+de\s+aluminio', desc, re.IGNORECASE):
        attrs["puntera"] = "Aluminio"
    elif re.search(r'sin\s+puntera', desc, re.IGNORECASE):
        attrs["puntera"] = "Sin puntera"

    # Materiales comunes
    mats = []
    if re.search(r'cuero\s+descarne', desc, re.IGNORECASE):
        mats.append("Cuero Descarne")
    elif re.search(r'vaqueta', desc, re.IGNORECASE):
        mats.append("Vaqueta")
    if re.search(r'nitrilo', desc, re.IGNORECASE):
        mats.append("Nitrilo")
    if re.search(r'latex|látex', desc, re.IGNORECASE):
        mats.append("Látex")
    if re.search(r'pvc', desc, re.IGNORECASE):
        mats.append("PVC")
    if re.search(r'poliester|poliéster', desc, re.IGNORECASE):
        mats.append("Poliéster")
    if re.search(r'acero\s+inox', desc, re.IGNORECASE):
        mats.append("Acero Inoxidable")
    if mats:
        attrs["material"] = ", ".join(mats)

    # Colores comunes
    colores = []
    for c in ["Blanco", "Amarillo", "Verde", "Naranja", "Azul", "Rojo", "Negro", "Gris", "Rosa"]:
        if re.search(r'\b' + c + r'\b', desc, re.IGNORECASE):
            colores.append(c)
    if colores:
        attrs["color"] = ", ".join(colores)

    return attrs


def classify_guantes_completa_row(desc: str) -> str:
    """Clasifica con exactitud los 1.259 renglones de la hoja GUANTES COMPLETA."""
    d = desc.lower()
    if any(k in d for k in ["botin", "zapato", "calzado", "bota"]):
        return "CALZADO_DE_SEGURIDAD"
    if any(k in d for k in ["gte", "guante", "miton"]):
        return "GUANTES_Y_PROTECCION_MANOS"
    if any(k in d for k in ["casco", "mentonera", "barbijo", "mascara", "semimascara", "cofia"]):
        return "PROTECCION_CRANEANA_Y_FACIAL"
    if any(k in d for k in ["arnes", "arnés", "cabo", "linea de vida", "cola de amarre", "mosqueton", "amortiguador"]):
        return "TRABAJO_EN_ALTURA_Y_ARNESES"
    if any(k in d for k in ["campera", "pantalon", "chaleco", "camisa", "mameluco", "capa", "delantal", "traje"]):
        return "INDUMENTARIA_LABORAL"
    if any(k in d for k in ["anteojo", "antiparra", "lente"]):
        return "PROTECCION_OCULAR"
    if any(k in d for k in ["protector auditivo", "tapon", "tapón", "sordina"]):
        return "PROTECCION_AUDITIVA"
    if any(k in d for k in ["cono", "valla", "cartel", "baliza", "cinta peligro"]):
        return "SEGURIDAD_VIAL_Y_SENALIZACION"
    return "ACCESORIOS_Y_OTROS_EPP"


def classify_art_proteccion_row(desc: str) -> str:
    """Clasifica los artículos de ART DE PROTECCION."""
    d = desc.lower()
    if "cinta" in d:
        return "CINTAS_REFLECTIVAS"
    if "guante" in d:
        return "GUANTES_DE_PROTECCION"
    if "termocontraible" in d:
        return "TUBOS_TERMOCONTRAIBLES"
    if "bombeador" in d or "diafragma" in d:
        return "DIAFRAGMAS_Y_BOMBEADORES"
    return "OTROS_PROTECCION"


def classify_pisos_row(desc: str) -> str:
    d = desc.lower()
    if "piso" in d:
        return "PISOS_GOMA_Y_PVC"
    if "cuerina" in d or "tapiceria" in d:
        return "CUERINAS_Y_TAPICERIA"
    if "cristal" in d:
        return "ROLLOS_CRISTAL_PVC"
    return "PISOS_GENERAL"


def save_classified_table(items: list[dict], output_path: str, title: str):
    headers = ["CODIGO", "DESCRIPCION", "TALLE/MEDIDA", "MATERIAL", "COLOR", "PRECIO (S/IVA)"]
    rows = []
    for it in items:
        cod = it["code"] if it["code"] else "S/C"
        desc = it["desc"]
        attrs = it["attrs"]
        talle = attrs.get("talle", "")
        mat = attrs.get("material", "")
        color = attrs.get("color", "")
        price = f"${it['price']:,.2f}"
        rows.append([cod, desc, talle, mat, color, price])

    widths = [len(h) for h in headers]
    for r in rows:
        for i in range(len(headers)):
            widths[i] = max(widths[i], len(r[i]))

    widths[1] = min(widths[1], 65)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"=== TABLA NORMALIZADA: {title} ===\n")
        f.write(f"Total de registros clasificados: {len(rows)}\n")
        f.write("=" * 115 + "\n\n")

        header_line = " | ".join(headers[i].ljust(widths[i]) for i in range(len(headers)))
        f.write(header_line + "\n")
        f.write("-" * len(header_line) + "\n")

        for r in rows:
            line = " | ".join(r[i].ljust(widths[i]) for i in range(len(headers)))
            f.write(line + "\n")


def generate_database_schema_documentation(folder_path: str, entity_name: str, subcategories: list[str]):
    """Genera la especificación formal de tablas y tablas puente M:N para base de datos relacional."""
    schema_path = os.path.join(folder_path, "ESQUEMA_TABLAS_Y_RELACIONES.txt")
    with open(schema_path, "w", encoding="utf-8") as f:
        f.write(f"=================================================================================\n")
        f.write(f"MODELO RELACIONAL Y TABLAS NORMALIZADAS (3FN): {entity_name.upper()}\n")
        f.write(f"=================================================================================\n\n")
        f.write(f"1. TABLA PRINCIPAL DE PRODUCTOS:\n")
        f.write(f"   - TABLA: productos\n")
        f.write(f"     * id (UUID / INT PK)\n")
        f.write(f"     * sku / codigo (VARCHAR(50), UNIQUE, INDEX)\n")
        f.write(f"     * nombre_descripcion (VARCHAR(255), NOT NULL)\n")
        f.write(f"     * id_categoria (INT FK -> categorias.id)\n")
        f.write(f"     * id_familia (INT FK -> familias.id)\n")
        f.write(f"     * precio_base (DECIMAL(12,2))\n")
        f.write(f"     * precio_mayorista_b2b (DECIMAL(12,2))\n")
        f.write(f"     * stock (INT)\n")
        f.write(f"     * activo (BOOLEAN)\n\n")

        f.write(f"2. TABLAS DE CATÁLOGO / DOMINIO DE ATRIBUTOS:\n")
        f.write(f"   - TABLA: categorias (id, nombre, descripcion)\n")
        f.write(f"   - TABLA: talles_medidas (id, valor, unidad_medida)\n")
        f.write(f"   - TABLA: materiales (id, nombre, propiedades_tecnicas)\n")
        f.write(f"   - TABLA: colores (id, nombre, codigo_hex)\n")
        f.write(f"   - TABLA: punteras_seguridad (id, tipo_puntera [Acero, Aluminio, Dieléctrica])\n\n")

        f.write(f"3. TABLAS PUENTE (RELACIONES MUCHOS A MUCHOS - M:N):\n")
        f.write(f"   - TABLA: producto_variantes (\n")
        f.write(f"       id (PK),\n")
        f.write(f"       id_producto (FK -> productos.id),\n")
        f.write(f"       id_talle (FK -> talles_medidas.id),\n")
        f.write(f"       id_color (FK -> colores.id),\n")
        f.write(f"       id_material (FK -> materiales.id),\n")
        f.write(f"       codigo_barras_especifico (VARCHAR),\n")
        f.write(f"       stock_variante (INT)\n")
        f.write(f"     )\n\n")

        f.write(f"   - TABLA: producto_compatibilidad_vehicular (\n")
        f.write(f"       id (PK),\n")
        f.write(f"       id_producto (FK -> productos.id),\n")
        f.write(f"       marca (VARCHAR),\n")
        f.write(f"       modelo (VARCHAR),\n")
        f.write(f"       motorizacion (VARCHAR),\n")
        f.write(f"       anio_desde (INT),\n")
        f.write(f"       anio_hasta (INT)\n")
        f.write(f"     )\n\n")

        f.write(f"4. SUB-FAMILIAS Y DIVISIONES EXTRAÍDAS DE ESTA SECCIÓN:\n")
        for sc in subcategories:
            f.write(f"   * {sc}\n")
        f.write(f"\n=================================================================================\n")


def process_special_splits():
    print("=" * 80)
    print("PROCESANDO SEPARACION QUIRURGICA DE ARTICULOS HETEROGENEOS Y ESQUEMAS")
    print("=" * 80)

    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)

    # 1. Procesar GUANTES COMPLETA (separar en Calzado, Guantes, Cascos, Altura, etc.)
    ws_guantes = wb["GUANTES COMPLETA"]
    folder_guantes = os.path.join(BASE_DIR, "08_GUANTES_COMPLETA")
    items_by_cat = {}

    for r in range(5, ws_guantes.max_row + 1):
        cod = clean_str(ws_guantes.cell(r, 1).value)
        desc = clean_str(ws_guantes.cell(r, 2).value)
        price = parse_price(ws_guantes.cell(r, 3).value)

        if desc and price is not None:
            category = classify_guantes_completa_row(desc)
            attrs = extract_attributes(desc)
            if category not in items_by_cat:
                items_by_cat[category] = []
            items_by_cat[category].append({
                "code": cod,
                "desc": desc,
                "attrs": attrs,
                "price": price
            })

    for cat_name, cat_items in items_by_cat.items():
        file_path = os.path.join(folder_guantes, f"articulos_{cat_name.lower()}.txt")
        save_classified_table(cat_items, file_path, title=cat_name.replace("_", " "))
        print(f"  [08_GUANTES_COMPLETA] Generado: articulos_{cat_name.lower()}.txt ({len(cat_items)} productos)")

    generate_database_schema_documentation(folder_guantes, "Artículos de Seguridad y EPP", list(items_by_cat.keys()))

    # 2. Procesar 02_ART_DE_PROTECCION (separar Cintas, Guantes, Tubos, Diafragmas)
    ws_prot = wb["ART DE PROTECCION"]
    folder_prot = os.path.join(BASE_DIR, "02_ART_DE_PROTECCION")
    prot_by_cat = {}

    # Leer artículos ya normalizados de la página para reclasificarlos atómicamente
    norm_prot_file = os.path.join(folder_prot, "articulos_normalizados.txt")
    if os.path.exists(norm_prot_file):
        with open(norm_prot_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines[7:]: # Saltear encabezados
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 4:
                cod = parts[0]
                desc = parts[2]
                price = parse_price(parts[3]) or 0.0
                cat = classify_art_proteccion_row(desc)
                attrs = extract_attributes(desc)
                if cat not in prot_by_cat:
                    prot_by_cat[cat] = []
                prot_by_cat[cat].append({
                    "code": cod,
                    "desc": desc,
                    "attrs": attrs,
                    "price": price
                })

        for cat_name, cat_items in prot_by_cat.items():
            file_path = os.path.join(folder_prot, f"articulos_{cat_name.lower()}.txt")
            save_classified_table(cat_items, file_path, title=cat_name.replace("_", " "))
            print(f"  [02_ART_DE_PROTECCION] Generado: articulos_{cat_name.lower()}.txt ({len(cat_items)} productos)")

        generate_database_schema_documentation(folder_prot, "Artículos de Protección y Varios", list(prot_by_cat.keys()))

    # 3. Procesar 14_PISOS (separar Pisos Goma/PVC, Cuerinas, Cristal)
    folder_pisos = os.path.join(BASE_DIR, "14_PISOS")
    norm_pisos_file = os.path.join(folder_pisos, "articulos_normalizados.txt")
    pisos_by_cat = {}
    if os.path.exists(norm_pisos_file):
        with open(norm_pisos_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines[7:]:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 4:
                cod = parts[0]
                desc = parts[2]
                price = parse_price(parts[3]) or 0.0
                cat = classify_pisos_row(desc)
                attrs = extract_attributes(desc)
                if cat not in pisos_by_cat:
                    pisos_by_cat[cat] = []
                pisos_by_cat[cat].append({
                    "code": cod,
                    "desc": desc,
                    "attrs": attrs,
                    "price": price
                })

        for cat_name, cat_items in pisos_by_cat.items():
            file_path = os.path.join(folder_pisos, f"articulos_{cat_name.lower()}.txt")
            save_classified_table(cat_items, file_path, title=cat_name.replace("_", " "))
            print(f"  [14_PISOS] Generado: articulos_{cat_name.lower()}.txt ({len(cat_items)} productos)")

        generate_database_schema_documentation(folder_pisos, "Pisos Técnicos y Revestimientos", list(pisos_by_cat.keys()))

    # 4. Generar documento de esquema para todas las demás carpetas del catálogo
    for idx, sheet_name in enumerate(wb.sheetnames, start=1):
        if "INDICE" in sheet_name:
            continue
        clean_name = sanitize_filename(sheet_name)
        folder_name = f"{idx:02d}_{clean_name}"
        fpath = os.path.join(BASE_DIR, folder_name)
        schema_file = os.path.join(fpath, "ESQUEMA_TABLAS_Y_RELACIONES.txt")
        if not os.path.exists(schema_file):
            generate_database_schema_documentation(fpath, clean_name.replace("_", " "), [clean_name])

    print("\n" + "=" * 80)
    print("PROCESO COMPLETADO: ARCHIVOS SEPARADOS POR ARTICULO Y ESQUEMAS DOCUMENTADOS.")
    print("=" * 80)


if __name__ == "__main__":
    process_special_splits()
