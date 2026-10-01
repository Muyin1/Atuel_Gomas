"""
Normalizador de Catálogo para Atuel Gomas.

Ubicación: datos provicionales/normalizador_tablas.py
Función:
- Procesa hoja por hoja (excluyendo el índice general).
- Detecta subtablas paralelas (ej. Mangueras Moldeadas vs Mangueras por Metro, Cintas vs Guantes vs Tubos, Cadenas vs Remaches vs Grampas).
- Resuelve jerarquías de productos padre/hijo (ej. Guante Táctil DPS -> Nro.8 cod.85193).
- Separa y normaliza cada registro para que exista UN SOLO ARTÍCULO por fila con:
  [CODIGO | CATEGORIA/FAMILIA | DESCRIPCION NORMALIZADA | MEDIDA/TALLES | PRECIO_SIN_IVA]
- Genera en cada carpeta:
  1. 'articulos_normalizados.txt' (tabla limpia y legible alineada)
  2. Tablas individuales si la página contiene múltiples familias de productos claramente separadas.
"""

import os
import re
import openpyxl

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_NAME = "Para la revista del burneeee.xlsx"
EXCEL_PATH = os.path.join(BASE_DIR, EXCEL_NAME)


def sanitize_folder_name(name: str) -> str:
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
    s = str(val).strip()
    s = s.replace('\ufffd', 'I')
    s = re.sub(r'\s+', ' ', s)
    return s


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


def extract_code_and_desc(text: str) -> tuple[str, str]:
    """Extrae código embebido tipo 'cod.85193' o 'DPS 88305' de la descripción si existe."""
    cod_match = re.search(r'(?:cod\.?|código:?)\s*([A-Za-z0-9\+\-]+)', text, re.IGNORECASE)
    if cod_match:
        code = cod_match.group(1).strip()
        desc = re.sub(r'(?:cod\.?|código:?)\s*[A-Za-z0-9\+\-]+', '', text, flags=re.IGNORECASE).strip()
        return code, desc
    return "", text


class NormalizedItem:
    def __init__(self, code: str, family: str, description: str, measure: str, price: float):
        self.code = code.strip()
        self.family = family.strip()
        self.description = description.strip()
        self.measure = measure.strip()
        self.price = price


def parse_column_block(ws, start_col: int, end_col: int, default_family: str) -> list[NormalizedItem]:
    """
    Analiza un bloque vertical de columnas que representa una tabla de artículos.
    """
    items: list[NormalizedItem] = []
    current_parent_desc = ""
    current_family = default_family

    max_row = ws.max_row
    for r in range(1, max_row + 1):
        # Filtrar valores no nulos en el rango
        non_empty = []
        for c in range(start_col, end_col + 1):
            val = ws.cell(r, c).value
            if val is not None and str(val).strip():
                non_empty.append((c, val))

        if not non_empty:
            continue

        # Si toda la fila contiene palabras de cabecera o índice, omitir
        all_text = " ".join(clean_str(v).lower() for _, v in non_empty)
        if "indice" in all_text or "precio sin iva" in all_text or "descripción art" in all_text:
            continue

        # Buscar si el último elemento no vacío es un precio numérico
        last_col, last_val = non_empty[-1]
        price = parse_price(last_val)

        if price is not None:
            # Hay un precio en esta fila para este bloque
            preceding = [v for c, v in non_empty[:-1]]
            
            if len(preceding) == 2:
                # Caso: [Código, Descripción]
                code = clean_str(preceding[0])
                desc = clean_str(preceding[1])
                items.append(NormalizedItem(code=code, family=current_family, description=desc, measure="", price=price))
            elif len(preceding) == 1:
                # Caso: [Descripción / Medida]
                raw_desc = clean_str(preceding[0])
                code, clean_desc = extract_code_and_desc(raw_desc)
                if current_parent_desc and not clean_desc.lower().startswith(current_parent_desc.lower()[:7]):
                    full_desc = f"{current_parent_desc} - {clean_desc}"
                else:
                    full_desc = clean_desc if clean_desc else raw_desc
                items.append(NormalizedItem(code=code, family=current_family, description=full_desc, measure="", price=price))
            elif len(preceding) >= 3:
                code = clean_str(preceding[0])
                desc = " - ".join(clean_str(p) for p in preceding[1:])
                items.append(NormalizedItem(code=code, family=current_family, description=desc, measure="", price=price))
        else:
            # Fila sin precio: puede ser un título de familia o producto padre
            texts = [clean_str(v) for _, v in non_empty if clean_str(v)]
            if len(texts) == 1 and len(texts[0]) > 2:
                # Título o categoría padre
                current_parent_desc = texts[0]
                if not current_family or current_family == default_family:
                    current_family = texts[0]

    return items


def detect_subtables_and_parse(ws) -> dict[str, list[NormalizedItem]]:
    """
    Detecta columnas con precio y divide la hoja en subtablas limpias.
    """
    sheet_title = ws.title.strip()
    max_col = ws.max_column

    # Detectar todas las columnas que actúan como columna de precios
    price_cols = []
    for c in range(1, max_col + 1):
        # 1. Comprobar si en las primeras 10 filas hay cabecera tipo 'precio'
        is_price_col = False
        for r in range(1, min(10, ws.max_row + 1)):
            v = clean_str(ws.cell(r, c).value).lower()
            if "precio" in v or "dólar" in v or "dolar" in v:
                is_price_col = True
                break
        
        # 2. Si no tuvo cabecera explícita, comprobar si tiene valores flotantes
        if not is_price_col:
            numeric_count = 0
            for r in range(1, min(30, ws.max_row + 1)):
                if isinstance(ws.cell(r, c).value, (int, float)):
                    numeric_count += 1
            if numeric_count >= 2:
                is_price_col = True

        if is_price_col:
            price_cols.append(c)

    subtables: dict[str, list[NormalizedItem]] = {}

    if not price_cols:
        # Fallback a todo el ancho
        items = parse_column_block(ws, 1, max_col, default_family=sheet_title)
        if items:
            subtables[sheet_title] = items
        return subtables

    # Dividir en bloques verticales
    prev_start = 1
    for idx, p_col in enumerate(price_cols, start=1):
        # Título de la subtabla
        sub_title = ""
        for r in range(1, 5):
            for c in range(prev_start, p_col + 1):
                val = clean_str(ws.cell(r, c).value)
                if val and "indice" not in val.lower() and "precio" not in val.lower() and "código" not in val.lower():
                    sub_title = val
                    break
            if sub_title:
                break

        if not sub_title:
            sub_title = f"{sheet_title}_Parte_{idx}" if len(price_cols) > 1 else sheet_title

        items = parse_column_block(ws, prev_start, p_col, default_family=sub_title)
        if items:
            subtables[sub_title] = items
        prev_start = p_col + 1

    return subtables


def save_normalized_txt(items: list[NormalizedItem], output_path: str, title: str):
    headers = ["CODIGO", "FAMILIA / CATEGORIA", "DESCRIPCION NORMALIZADA", "PRECIO (S/IVA)"]
    rows = []
    for it in items:
        cod = it.code if it.code else "S/C"
        fam = it.family
        desc = it.description
        price = f"${it.price:,.2f}"
        rows.append([cod, fam, desc, price])

    widths = [len(h) for h in headers]
    for r in rows:
        for i in range(4):
            widths[i] = max(widths[i], len(r[i]))

    widths[2] = min(widths[2], 75)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"=== TABLA NORMALIZADA: {title} ===\n")
        f.write(f"Total de artículos únicos: {len(rows)}\n")
        f.write("=" * 95 + "\n\n")

        header_line = " | ".join(headers[i].ljust(widths[i]) for i in range(4))
        f.write(header_line + "\n")
        f.write("-" * len(header_line) + "\n")

        for r in rows:
            line = " | ".join(r[i].ljust(widths[i]) for i in range(4))
            f.write(line + "\n")


def process_all_normalizations():
    print("=" * 80)
    print("INICIANDO NORMALIZACION ATOMICA DE ARTICULOS (1 ARTICULO POR REGISTRO)")
    print("=" * 80)

    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    total_articulos_global = 0

    for idx, sheet_name in enumerate(wb.sheetnames, start=1):
        if "INDICE" in sheet_name:
            continue

        clean_name = sanitize_folder_name(sheet_name)
        folder_name = f"{idx:02d}_{clean_name}"
        folder_path = os.path.join(BASE_DIR, folder_name)

        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)

        ws = wb[sheet_name]
        subtables = detect_subtables_and_parse(ws)

        all_page_items: list[NormalizedItem] = []
        for sub_name, items in subtables.items():
            all_page_items.extend(items)

        page_txt_path = os.path.join(folder_path, "articulos_normalizados.txt")
        save_normalized_txt(all_page_items, page_txt_path, title=sheet_name)

        if len(subtables) > 1:
            for sub_name, items in subtables.items():
                safe_sub_name = sanitize_folder_name(sub_name)
                sub_file_path = os.path.join(folder_path, f"tabla_{safe_sub_name}.txt")
                save_normalized_txt(items, sub_file_path, title=sub_name)

        total_articulos_global += len(all_page_items)
        sub_desc = f" ({len(subtables)} subtablas detectadas)" if len(subtables) > 1 else ""
        print(f"[{idx:02d}] {sheet_name}{sub_desc}: {len(all_page_items)} artículos normalizados -> {folder_name}/articulos_normalizados.txt")

    print("\n" + "=" * 80)
    print(f"NORMALIZACION COMPLETADA: {total_articulos_global:,} ARTICULOS TOTALES EXTRAIDOS Y ATOMIZADOS.")
    print("=" * 80)


if __name__ == "__main__":
    process_all_normalizations()
