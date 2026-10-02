#!/usr/bin/env python3
"""
Script de Carga Masiva (Seeder) - Atuel Gomas
Etapa 2: Ingesta Masiva de Datos del Catálogo Comercial y Técnico

Lee los datos estructurados en 'datos provicionales/' (27 carpetas y archivos TXT normalizados/clasificados)
e inserta ordenadamente:
- Categorías y Familias (3FN)
- Catálogos de Atributos (Talles/Medidas, Colores, Materiales, Punteras)
- Productos Base con SKUs, Precios de Lista y Mayorista B2B, Stock y Medidas Dimensionales
- Variantes Relacionales (M:N)
- Compatibilidad Vehicular Multimarca
- Clientes B2B y Administrador de prueba
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time

# Asegurar que el directorio raíz del proyecto esté en sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.infrastructure.database.connection import (
    DATABASE_URL,
    SessionLocal,
    drop_db,
    init_db,
)
from src.infrastructure.database.models import (
    CategoriaModel,
    ClienteModel,
    ColorModel,
    CompatibilidadVehicularModel,
    FamiliaModel,
    MaterialModel,
    ProductoModel,
    PunteraModel,
    TalleModel,
    VarianteModel,
)


# ==============================================================================
# 1. Utilidades de Limpieza, Parseo y Extracción
# ==============================================================================

def clean_text(s: str | None) -> str:
    """Normaliza texto, remueve caracteres de reemplazo inválidos y normaliza espacios."""
    if not s:
        return ""
    text = str(s).strip()
    replacements = {
        "\ufffd": "",
        "Descripcin": "Descripción",
        "Cdigo": "Código",
        "Artculo": "Artículo",
        "Hidrulica": "Hidráulica",
        "LQUIDOS": "LÍQUIDOS",
        "LTEX": "LÁTEX",
        "Lquidos": "Líquidos",
        "Ltex": "Látex",
        "Tctil": "Táctil",
        "Caos": "Caños",
        "Arns": "Arnés",
        "cinturn": "cinturón",
        "proteccin": "protección",
        "sealizacin": "señalización",
        "metlico": "metálico",
        "dlar": "dólar",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return re.sub(r"\s+", " ", text).strip()


def parse_price(val: str | float | int | None) -> float:
    """Extrae precio flotante limpio a partir de valores string o numéricos."""
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val) if val > 0 else 0.0
    s = str(val).strip().replace("$", "").replace(" ", "").replace(",", "")
    try:
        p = float(s)
        return p if p > 0 else 0.0
    except ValueError:
        return 0.0


def extract_dimensions_from_text(desc: str) -> dict[str, float | None]:
    """Extrae diámetros, largo y espesor en mm a partir de expresiones técnicas."""
    dims: dict[str, float | None] = {
        "inner_diameter_mm": None,
        "outer_diameter_mm": None,
        "length_mm": None,
        "thickness_mm": None,
    }

    # Espesor x Ancho/Largo: ej "3MM X 1M", "5 mm"
    th_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:mm|MM)\s*x\s*(\d+(?:\.\d+)?)\s*(?:m|M|mt|MT)", desc)
    if th_match:
        dims["thickness_mm"] = float(th_match.group(1))
        dims["length_mm"] = float(th_match.group(2)) * 1000.0
        return dims

    # Diámetro / Medida en mm: ej "25 mm", "10MM", "32mm"
    mm_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:mm|MM)\b", desc)
    if mm_match:
        dims["inner_diameter_mm"] = float(mm_match.group(1))

    # Pulgadas: ej '1/2"', '3/4"', '1"'
    inch_match = re.search(r'(\d+/\d+|\d+)\s*(?:"|pulg|Pulg)', desc)
    if inch_match:
        inch_str = inch_match.group(1)
        try:
            if "/" in inch_str:
                n, d = inch_str.split("/")
                val_mm = (float(n) / float(d)) * 25.4
            else:
                val_mm = float(inch_str) * 25.4
            dims["inner_diameter_mm"] = round(val_mm, 2)
        except ZeroDivisionError:
            pass

    return dims


def extract_vehicle_compatibilities(desc: str, prod: ProductoModel) -> list[CompatibilidadVehicularModel]:
    """Extrae marcas, modelos y aplicaciones automotores homologadas."""
    compats: list[CompatibilidadVehicularModel] = []
    d = desc.lower()

    brands_catalog = [
        ("Renault", ["kangoo", "clio", "master", "megane", "trafic", "sandero", "duster", "r19", "r12", "r9"]),
        ("Volkswagen", ["gol", "voyage", "fox", "suran", "saveiro", "amarok", "bora", "polo", "vento", "gacel", "senda"]),
        ("Ford", ["ranger", "f-100", "f100", "falcon", "fiesta", "focus", "ka", "ecosport", "taunus", "sierra"]),
        ("Fiat", ["palio", "siena", "uno", "duna", "fiorino", "punto", "cronos", "toro", "128", "147"]),
        ("Chevrolet", ["corsa", "classic", "onix", "astra", "s10", "cruze", "agile", "meriva", "aveo"]),
        ("Peugeot", ["206", "207", "208", "306", "307", "308", "405", "504", "partner", "boxer"]),
        ("Citroën", ["berlingo", "c3", "c4", "xsara", "jumper"]),
        ("Mercedes Benz", ["sprinter", "1114", "1518", "1620", "accelo", "atego"]),
        ("Scania", ["112", "113", "114", "124", "serie 4"]),
        ("Iveco", ["daily", "eurocargo", "stralis", "tector"]),
        ("Toyota", ["hilux", "corolla", "etios", "yaris"]),
        ("Nissan", ["frontier"]),
    ]

    for brand, models in brands_catalog:
        brand_key = brand.lower().split()[0]
        if re.search(r"\b" + brand_key + r"\b", d):
            detected_model = "Línea Multimodelo"
            for m in models:
                if re.search(r"\b" + m + r"\b", d):
                    detected_model = m.capitalize()
                    break
            compats.append(
                CompatibilidadVehicularModel(
                    producto=prod,
                    marca=brand,
                    modelo=detected_model,
                    motorizacion="Nafta / Diesel",
                    anios_texto="Homologado OEM",
                )
            )

    return compats


# ==============================================================================
# 2. Definición Canónica de Categorías y Familias Técnicas (3FN)
# ==============================================================================

CATEGORIAS_DEF = [
    {
        "nombre": "Mangueras Automotor",
        "slug": "mangueras-automotor",
        "descripcion": "Mangueras de radiador, calefacción, combustible, depósito y retorno para automotores y utilitarios.",
        "familias": [
            ("Mangueras de Goma Moldeada", "mangueras-goma-moldeada", "Mangueras conformadas según molde original de fábrica."),
            ("Mangueras de Goma por Metro", "mangueras-goma-por-metro", "Mangueras continuas por metro para circuitos de refrigeración."),
            ("Escobillas Limpiaparabrisas", "escobillas-limpiaparabrisas", "Escobillas de goma natural para visibilidad automotriz."),
            ("Cebadores", "cebadores", "Cebadores manuales y peras de purga de combustible."),
            ("Caños Pileteros", "canos-pileteros", "Caños y mangueras para sistemas de refrigeración pileteros."),
        ],
    },
    {
        "nombre": "Mangueras Industriales e Hidráulicas",
        "slug": "mangueras-industriales",
        "descripcion": "Mangueras para alta presión oleohidráulica, aire, agua, hidrocarburos, agro e industria.",
        "familias": [
            ("Mangueras Industriales", "mangueras-industriales-pesadas", "Mangueras pesadas para aspiración y descarga de fluidos."),
            ("Mangueras Hidrocarburo", "mangueras-hidrocarburo", "Mangueras resistentes a derivados de petróleo, naftas y aceites."),
            ("Mangueras Air-House", "mangueras-air-house", "Mangueras de 300 LB para circuitos neumáticos y compresores."),
            ("Mangueras de Fumigación", "mangueras-fumigacion", "Mangueras de alta resistencia química 120 BAR para agro."),
            ("Mangas PVC", "mangas-pvc", "Mangas planas de PVC azul para impulsión y riego agrícola."),
            ("Mangueras de Riego", "mangueras-riego", "Mangueras domiciliarias y para conducción de gas aprobadas."),
            ("Látex", "latex", "Tubos de goma látex natural de alta elasticidad."),
        ],
    },
    {
        "nombre": "Abrazaderas y Acoples",
        "slug": "abrazaderas-acoples",
        "descripcion": "Abrazaderas sin fin, súper presión, alambre y acoples rápidos de unión para mangueras.",
        "familias": [
            ("Abrazaderas Mini Americana", "abrazaderas-mini-americana", "Abrazaderas compactas para diámetros reducidos."),
            ("Abrazaderas Fleje Ancho", "abrazaderas-fleje-ancho", "Abrazaderas cremallera de alta retención tipo americana."),
            ("Abrazaderas Súper Presión", "abrazaderas-super-presion", "Abrazaderas con bulón y tuerca de máxima sujeción."),
            ("Abrazaderas de Alambre", "abrazaderas-alambre", "Abrazaderas dobles de alambre elástico."),
            ("Acoples Rápidos", "acoples-rapidos", "Acoples universales para empalme seguro de líneas hidráulicas."),
            ("Acoples de Aluminio", "acoples-aluminio", "Acoples livianos de aleación de aluminio para trasvase."),
        ],
    },
    {
        "nombre": "Artículos de Protección y EPP",
        "slug": "proteccion-epp",
        "descripcion": "Equipamiento de protección personal homologado para industria pesada, taller y faena.",
        "familias": [
            ("Calzado de Seguridad", "calzado-seguridad", "Botines y zapatos de seguridad con punteras certificadas."),
            ("Guantes de Protección", "guantes-proteccion", "Guantes de vaqueta, descarne, nitrilo, látex y anticorte."),
            ("Protección Craneana y Facial", "proteccion-craneana-facial", "Cascos de seguridad, barbijos y semimáscaras."),
            ("Trabajo en Altura y Arneses", "altura-arneses", "Arneses anticaída, líneas de vida y colas de amarre."),
            ("Indumentaria Laboral", "indumentaria-laboral", "Camisas, pantalones, camperas y delantales de protección."),
            ("Protección Ocular", "proteccion-ocular", "Anteojos y antiparras de seguridad anti-impacto."),
            ("Protección Auditiva", "proteccion-auditiva", "Protectores auditivos de copa y tapones endoaurales."),
            ("Seguridad Vial y Señalización", "seguridad-vial", "Conos, vallas y balizas de advertencia vial."),
            ("Accesorios y Otros EPP", "accesorios-epp", "Complementos para protección de operarios."),
            ("Cintas Reflectivas", "cintas-reflectivas", "Cintas reflectivas de alta visibilidad para indumentaria."),
            ("Tubos Termocontraíbles", "tubos-termocontraibles", "Tubos termocontraíbles para aislamiento eléctrico."),
            ("Diafragmas y Bombeadores", "diafragmas-bombeadores", "Membranas y diafragmas de goma para bombeo."),
        ],
    },
    {
        "nombre": "Correas y Transmisión",
        "slug": "correas-transmision",
        "descripcion": "Correas en V automotores, Poly-V, industriales perfiles A/B/C y cintas para el agro.",
        "familias": [
            ("Correas Automotor y Poly-V", "correas-automotor", "Correas de distribución y accesorios automotores."),
            ("Correas Industriales", "correas-industriales", "Correas trapeciales de transmisión de potencia."),
            ("Cintas Rotoenfardadoras", "cintas-rotoenfardadoras", "Cintas planas de goma reforzada para maquinaria agrícola."),
        ],
    },
    {
        "nombre": "Pisos y Revestimientos",
        "slug": "pisos-revestimientos",
        "descripcion": "Pisos de goma antideslizantes, cuerinas técnicas para tapicería y rollos cristal PVC.",
        "familias": [
            ("Pisos de Goma", "pisos-goma", "Pisos de goma botón, estriado y grano de arroz."),
            ("Cuerinas y Tapicería", "cuerinas-tapiceria", "Revestimientos sintéticos de alta resistencia al roce."),
            ("Rollos Cristal PVC", "rollos-cristal-pvc", "Láminas transparentes flexibles de PVC cristal."),
        ],
    },
    {
        "nombre": "Ferretería Industrial y Autopartes",
        "slug": "ferreteria-autopartes",
        "descripcion": "O-rings métricos y en pulgadas, cadenas de transmisión, remaches, grampas y fluidos.",
        "familias": [
            ("O-Rings y Sellos", "orings-sellos", "Anillos de estanqueidad elastoméricos NBR/Viton."),
            ("Cadenas", "cadenas", "Cadenas a rodillos estándar para transmisión mecánica."),
            ("Grampas", "grampas", "Grampas omega y fijaciones metálicas."),
            ("Remaches", "remaches", "Remaches ciegos de aluminio y acero."),
            ("Líquidos de Freno y Fluidos", "fluidos-frenos", "Líquidos de freno DOT3/DOT4 y lubricantes técnicos."),
            ("Precintos", "precintos", "Precintos plásticos de nylon de alta tenacidad."),
        ],
    },
]


# ==============================================================================
# 3. Cachés en Memoria y Catálogos de Atributos
# ==============================================================================

STANDARD_PUNTERAS = [
    ("Acero", "Puntera de acero al carbono resistente a impactos de 200 Joules."),
    ("Aluminio", "Puntera de aleación liviana ultrarresistente."),
    ("Dieléctrica", "Puntera no metálica en composite / fibra de vidrio para riesgos eléctricos."),
    ("Sin puntera", "Calzado ocupacional estándar sin puntera reforzada."),
]

STANDARD_MATERIALES = [
    ("Cuero Descarne", "Cuero vacuno curtido al cromo para alta resistencia al desgarro."),
    ("Vaqueta", "Cuero flor suave de máxima flexibilidad."),
    ("Nitrilo", "Caucho sintético resistente a aceites, hidrocarburos y solventes."),
    ("Látex", "Polímero de caucho natural de máxima elasticidad."),
    ("PVC", "Policloruro de vinilo flexible resistente a la intemperie y agua."),
    ("EPDM", "Caucho de etileno propileno dieno de alta resistencia térmica."),
    ("SBR", "Caucho sintético de estireno-butadieno de uso general y pisos."),
    ("Acero Inoxidable", "Aleación resistente a la corrosión y alta presión."),
    ("Poliéster", "Fibra textil sintética de refuerzo estructural."),
]

STANDARD_COLORES = [
    ("Negro", "#000000"),
    ("Blanco", "#FFFFFF"),
    ("Amarillo", "#FFD700"),
    ("Azul", "#0000FF"),
    ("Rojo", "#FF0000"),
    ("Verde", "#008000"),
    ("Naranja", "#FFA500"),
    ("Gris", "#808080"),
    ("Transparente", "#E0E0E0"),
]


class AttributeCache:
    def __init__(self, session: Session):
        self.session = session
        self.talles: dict[str, TalleModel] = {}
        self.colores: dict[str, ColorModel] = {}
        self.materiales: dict[str, MaterialModel] = {}
        self.punteras: dict[str, PunteraModel] = {}
        self._init_standard_catalogs()

    def _init_standard_catalogs(self):
        """Inicializa los valores canónicos del catálogo de atributos técnicos."""
        for tipo, desc in STANDARD_PUNTERAS:
            p = PunteraModel(tipo_puntera=tipo, descripcion=desc)
            self.session.add(p)
            self.punteras[tipo.lower()] = p

        for mat, prop in STANDARD_MATERIALES:
            m = MaterialModel(nombre=mat, propiedades_tecnicas=prop)
            self.session.add(m)
            self.materiales[mat.lower()] = m

        for col, hex_code in STANDARD_COLORES:
            c = ColorModel(nombre=col, codigo_hex=hex_code)
            self.session.add(c)
            self.colores[col.lower()] = c

        self.session.flush()

    def get_or_create_talle(self, valor: str | None) -> TalleModel | None:
        if not valor or not valor.strip():
            return None
        v = valor.strip()[:50]
        v_key = v.lower()
        if v_key not in self.talles:
            t = TalleModel(valor=v)
            self.session.add(t)
            self.talles[v_key] = t
        return self.talles[v_key]

    def get_or_create_color(self, nombre: str | None) -> ColorModel | None:
        if not nombre or not nombre.strip():
            return None
        n = nombre.strip().title()[:50]
        n_key = n.lower()
        if n_key not in self.colores:
            c = ColorModel(nombre=n)
            self.session.add(c)
            self.colores[n_key] = c
        return self.colores[n_key]

    def get_or_create_material(self, nombre: str | None) -> MaterialModel | None:
        if not nombre or not nombre.strip():
            return None
        m = nombre.strip().title()[:100]
        m_key = m.lower()
        if m_key not in self.materiales:
            mat = MaterialModel(nombre=m)
            self.session.add(mat)
            self.materiales[m_key] = mat
        return self.materiales[m_key]

    def get_or_create_puntera(self, tipo: str | None) -> PunteraModel | None:
        if not tipo or not tipo.strip():
            return None
        p = tipo.strip().title()[:50]
        p_key = p.lower()
        if p_key not in self.punteras:
            punt = PunteraModel(tipo_puntera=p)
            self.session.add(punt)
            self.punteras[p_key] = punt
        return self.punteras[p_key]


# ==============================================================================
# 4. Ingesta Masiva desde Carpetas de datos provicionales/
# ==============================================================================

class DataSeeder:
    def __init__(self, session: Session, data_dir: str):
        self.session = session
        self.data_dir = data_dir
        self.attr_cache = AttributeCache(session)
        self.cat_map: dict[str, CategoriaModel] = {}
        self.fam_map: dict[str, FamiliaModel] = {}

        # Contadores estadísticos
        self.stats = {
            "categorias": 0,
            "familias": 0,
            "productos": 0,
            "variantes": 0,
            "compatibilidades": 0,
            "clientes": 0,
        }

    def seed_categories_and_families(self):
        """Registra las categorías y familias maestras en 3FN."""
        for cat_def in CATEGORIAS_DEF:
            cat = CategoriaModel(
                nombre=cat_def["nombre"],
                slug=cat_def["slug"],
                descripcion=cat_def["descripcion"],
            )
            self.session.add(cat)
            self.session.flush()
            self.cat_map[cat.nombre] = cat
            self.stats["categorias"] += 1

            for fam_name, fam_slug, fam_desc in cat_def["familias"]:
                fam = FamiliaModel(
                    categoria_id=cat.id,
                    nombre=fam_name,
                    slug=fam_slug,
                    descripcion=fam_desc,
                )
                self.session.add(fam)
                self.session.flush()
                self.fam_map[fam_name] = fam
                self.stats["familias"] += 1

        self.session.commit()
        print(f"✓ Registradas {self.stats['categorias']} Categorías y {self.stats['familias']} Familias.")

    def _create_product_record(
        self,
        categoria_nombre: str,
        familia_nombre: str,
        raw_code: str,
        raw_desc: str,
        raw_price: float,
        talle: str = "",
        material: str = "",
        color: str = "",
        puntera: str = "",
        image_url: str | None = None,
    ) -> ProductoModel:
        """Crea el objeto ProductoModel con sus variantes, dimensiones y compatibilidades."""
        cat = self.cat_map[categoria_nombre]
        fam = self.fam_map[familia_nombre]

        clean_code = clean_text(raw_code)
        clean_desc = clean_text(raw_desc)
        price_mayorista = round(raw_price, 2)
        price_base = round(raw_price * 1.30, 2)

        # Tratar casos donde el código está embebido en la descripción (ej: CORREAS - 10AV0535)
        if (not clean_code or clean_code in ("S/C", "s/c")) and " - " in clean_desc:
            parts = clean_desc.split(" - ", 1)
            candidate = parts[1].strip()
            if len(candidate) <= 50 and not any(k in candidate.lower() for k in ["rollo", "tramo", "bolsa"]):
                clean_code = candidate

        sku_val = clean_code[:50] if clean_code and clean_code not in ("S/C", "s/c") else None
        oem_val = sku_val

        # Extraer dimensiones métricas
        dims = extract_dimensions_from_text(clean_desc)

        # Stock simulado entre 15 y 85 unidades
        seed_num = sum(ord(c) for c in (sku_val or clean_desc[:20]))
        stock_val = (seed_num % 70) + 15

        prod = ProductoModel(
            sku=sku_val,
            codigo_oem=oem_val,
            nombre=clean_desc[:250],
            descripcion=clean_desc,
            categoria_id=cat.id,
            familia_id=fam.id,
            precio_base=price_base,
            precio_mayorista_b2b=price_mayorista,
            stock=stock_val,
            imagen_url=image_url,
            diametro_interior_mm=dims["inner_diameter_mm"],
            diametro_exterior_mm=dims["outer_diameter_mm"],
            largo_mm=dims["length_mm"],
            espesor_mm=dims["thickness_mm"],
        )

        # Compatibilidad vehicular
        compats = extract_vehicle_compatibilities(clean_desc, prod)
        if not compats and categoria_nombre == "Mangueras Automotor":
            compats.append(
                CompatibilidadVehicularModel(
                    producto=prod,
                    marca="Universal Automotor",
                    modelo="Línea Liviana y Pesada",
                    motorizacion="Universal",
                    anios_texto="Universal",
                )
            )
        prod.compatibilidades = compats
        self.stats["compatibilidades"] += len(compats)

        # Atributos y variantes relacionales
        if not puntera:
            d_low = clean_desc.lower()
            if "puntera de acero" in d_low or "con puntera" in d_low:
                puntera = "Acero"
            elif "puntera de aluminio" in d_low:
                puntera = "Aluminio"
            elif "sin puntera" in d_low:
                puntera = "Sin puntera"

        if not material:
            d_low = clean_desc.lower()
            if "cuero descarne" in d_low:
                material = "Cuero Descarne"
            elif "vaqueta" in d_low:
                material = "Vaqueta"
            elif "nitrilo" in d_low:
                material = "Nitrilo"
            elif "epdm" in d_low:
                material = "EPDM"
            elif "pvc" in d_low:
                material = "PVC"
            elif "acero inox" in d_low:
                material = "Acero Inoxidable"

        has_variant = bool(talle or material or color or puntera)
        if has_variant:
            t_obj = self.attr_cache.get_or_create_talle(talle)
            c_obj = self.attr_cache.get_or_create_color(color)
            m_obj = self.attr_cache.get_or_create_material(material)
            p_obj = self.attr_cache.get_or_create_puntera(puntera)

            var = VarianteModel(
                producto=prod,
                talle=t_obj,
                color=c_obj,
                material=m_obj,
                puntera=p_obj,
                stock_variante=stock_val,
                precio_especifico=price_mayorista,
            )
            prod.variantes = [var]
            self.stats["variantes"] += 1

        self.stats["productos"] += 1
        return prod

    def run_seeder(self):
        """Ejecuta la lectura e inserción masiva a través de los 26 directorios de insumo."""
        print("\n" + "=" * 80)
        print("INICIANDO INGESTA MASIVA EN BASE DE DATOS (ATUEL GOMAS)")
        print(f"Directorio de origen: {self.data_dir}")
        print("=" * 80)

        t_start = time.time()
        self.seed_categories_and_families()

        batch_prods: list[ProductoModel] = []

        def flush_batch():
            if batch_prods:
                self.session.add_all(batch_prods)
                self.session.flush()
                batch_prods.clear()

        # ----------------------------------------------------------------------
        # 1. 08_GUANTES_COMPLETA (9 archivos especializados clasificados)
        # ----------------------------------------------------------------------
        fldr_08 = os.path.join(self.data_dir, "08_GUANTES_COMPLETA")
        fam_map_08 = {
            "articulos_calzado_de_seguridad.txt": "Calzado de Seguridad",
            "articulos_guantes_y_proteccion_manos.txt": "Guantes de Protección",
            "articulos_proteccion_craneana_y_facial.txt": "Protección Craneana y Facial",
            "articulos_trabajo_en_altura_y_arneses.txt": "Trabajo en Altura y Arneses",
            "articulos_indumentaria_laboral.txt": "Indumentaria Laboral",
            "articulos_proteccion_ocular.txt": "Protección Ocular",
            "articulos_proteccion_auditiva.txt": "Protección Auditiva",
            "articulos_seguridad_vial_y_senalizacion.txt": "Seguridad Vial y Señalización",
            "articulos_accesorios_y_otros_epp.txt": "Accesorios y Otros EPP",
        }
        for fname, fam_name in fam_map_08.items():
            fpath = os.path.join(fldr_08, fname)
            if os.path.exists(fpath):
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f.readlines()[6:]:
                        parts = [p.strip() for p in line.split("|")]
                        if len(parts) >= 6:
                            p = self._create_product_record(
                                categoria_nombre="Artículos de Protección y EPP",
                                familia_nombre=fam_name,
                                raw_code=parts[0],
                                raw_desc=parts[1],
                                raw_price=parse_price(parts[5]),
                                talle=parts[2],
                                material=parts[3],
                                color=parts[4],
                            )
                            batch_prods.append(p)
                            if len(batch_prods) >= 1000:
                                flush_batch()

        # ----------------------------------------------------------------------
        # 2. 02_ART_DE_PROTECCION (archivos clasificados)
        # ----------------------------------------------------------------------
        fldr_02 = os.path.join(self.data_dir, "02_ART_DE_PROTECCION")
        fam_map_02 = {
            "articulos_cintas_reflectivas.txt": "Cintas Reflectivas",
            "articulos_diafragmas_y_bombeadores.txt": "Diafragmas y Bombeadores",
            "articulos_guantes_de_proteccion.txt": "Guantes de Protección",
            "articulos_tubos_termocontraibles.txt": "Tubos Termocontraíbles",
        }
        for fname, fam_name in fam_map_02.items():
            fpath = os.path.join(fldr_02, fname)
            if os.path.exists(fpath):
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f.readlines()[6:]:
                        parts = [p.strip() for p in line.split("|")]
                        if len(parts) >= 6:
                            p = self._create_product_record(
                                categoria_nombre="Artículos de Protección y EPP",
                                familia_nombre=fam_name,
                                raw_code=parts[0],
                                raw_desc=parts[1],
                                raw_price=parse_price(parts[5]),
                                talle=parts[2],
                                material=parts[3],
                                color=parts[4],
                                image_url="/static/img/02_ART_DE_PROTECCION/imagen_1.jpg",
                            )
                            batch_prods.append(p)

        # ----------------------------------------------------------------------
        # 3. 14_PISOS (archivos clasificados)
        # ----------------------------------------------------------------------
        fldr_14 = os.path.join(self.data_dir, "14_PISOS")
        fam_map_14 = {
            "articulos_pisos_general.txt": "Pisos de Goma",
            "articulos_cuerinas_y_tapiceria.txt": "Cuerinas y Tapicería",
        }
        for fname, fam_name in fam_map_14.items():
            fpath = os.path.join(fldr_14, fname)
            if os.path.exists(fpath):
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f.readlines()[6:]:
                        parts = [p.strip() for p in line.split("|")]
                        if len(parts) >= 6:
                            p = self._create_product_record(
                                categoria_nombre="Pisos y Revestimientos",
                                familia_nombre=fam_name,
                                raw_code=parts[0],
                                raw_desc=parts[1],
                                raw_price=parse_price(parts[5]),
                                talle=parts[2],
                                material=parts[3],
                                color=parts[4],
                                image_url="/static/img/14_PISOS/imagen_1.jpg",
                            )
                            batch_prods.append(p)

        # ----------------------------------------------------------------------
        # 4. 07_ACOPLES (tablas individuales)
        # ----------------------------------------------------------------------
        fldr_07 = os.path.join(self.data_dir, "07_ACOPLES")
        for fname, fam_name in [("tabla_ACOPLES.txt", "Acoples Rápidos"), ("tabla_ACOPLES_ALUMINIO.txt", "Acoples de Aluminio")]:
            fpath = os.path.join(fldr_07, fname)
            if os.path.exists(fpath):
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f.readlines()[6:]:
                        parts = [p.strip() for p in line.split("|")]
                        if len(parts) >= 4:
                            p = self._create_product_record(
                                categoria_nombre="Abrazaderas y Acoples",
                                familia_nombre=fam_name,
                                raw_code=parts[0],
                                raw_desc=f"{fam_name} - {parts[2]}",
                                raw_price=parse_price(parts[3]),
                                talle=parts[2],
                            )
                            batch_prods.append(p)

        # ----------------------------------------------------------------------
        # 5. 22_CADENAS_Y_GRAMPAS (tablas individuales)
        # ----------------------------------------------------------------------
        fldr_22 = os.path.join(self.data_dir, "22_CADENAS_Y_GRAMPAS")
        for fname, fam_name in [("tabla_CADENAS.txt", "Cadenas"), ("tabla_GRAMPAS.txt", "Grampas"), ("tabla_REMACHES.txt", "Remaches")]:
            fpath = os.path.join(fldr_22, fname)
            if os.path.exists(fpath):
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f.readlines()[6:]:
                        parts = [p.strip() for p in line.split("|")]
                        if len(parts) >= 4:
                            p = self._create_product_record(
                                categoria_nombre="Ferretería Industrial y Autopartes",
                                familia_nombre=fam_name,
                                raw_code=parts[0],
                                raw_desc=f"{fam_name} - {parts[2]}",
                                raw_price=parse_price(parts[3]),
                                talle=parts[2],
                            )
                            batch_prods.append(p)

        # ----------------------------------------------------------------------
        # 6. 19_MANGUERAS_DE_GOMA (Lectura directa de articulos.txt con subtables)
        # ----------------------------------------------------------------------
        fldr_19 = os.path.join(self.data_dir, "19_MANGUERAS_DE_GOMA")
        art_19 = os.path.join(fldr_19, "articulos.txt")
        if os.path.exists(art_19):
            with open(art_19, "r", encoding="utf-8", errors="ignore") as f:
                for line in f.readlines()[8:]:
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 8:
                        # Subtabla izquierda: Mangueras Moldeadas
                        c1, d1, pr1 = parts[1], parts[2], parse_price(parts[3])
                        if d1 and pr1 > 0:
                            p1 = self._create_product_record(
                                categoria_nombre="Mangueras Automotor",
                                familia_nombre="Mangueras de Goma Moldeada",
                                raw_code=c1,
                                raw_desc=f"Manguera {d1}",
                                raw_price=pr1,
                            )
                            batch_prods.append(p1)

                        # Subtabla derecha: Mangueras por Metro
                        c2, d2, pr2 = parts[5], parts[6], parse_price(parts[7])
                        if d2 and pr2 > 0:
                            p2 = self._create_product_record(
                                categoria_nombre="Mangueras Automotor",
                                familia_nombre="Mangueras de Goma por Metro",
                                raw_code=c2,
                                raw_desc=d2,
                                raw_price=pr2,
                            )
                            batch_prods.append(p2)

                        if len(batch_prods) >= 1000:
                            flush_batch()

        # ----------------------------------------------------------------------
        # 7. 12_MANGUERAS_INDUSTRIALES (Lectura directa de articulos.txt)
        # ----------------------------------------------------------------------
        fldr_12 = os.path.join(self.data_dir, "12_MANGUERAS_INDUSTRIALES")
        art_12 = os.path.join(fldr_12, "articulos.txt")
        if os.path.exists(art_12):
            with open(art_12, "r", encoding="utf-8", errors="ignore") as f:
                for line in f.readlines()[6:]:
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 4:
                        c, d, pr = parts[1], parts[2], parse_price(parts[3])
                        if d and pr > 0:
                            p = self._create_product_record(
                                categoria_nombre="Mangueras Industriales e Hidráulicas",
                                familia_nombre="Mangueras Industriales",
                                raw_code=c,
                                raw_desc=d,
                                raw_price=pr,
                            )
                            batch_prods.append(p)

        # ----------------------------------------------------------------------
        # 8. 13_ACRILICOS (Mangueras Hidrocarburo)
        # ----------------------------------------------------------------------
        fldr_13 = os.path.join(self.data_dir, "13_ACRILICOS")
        art_13 = os.path.join(fldr_13, "articulos.txt")
        if os.path.exists(art_13):
            with open(art_13, "r", encoding="utf-8", errors="ignore") as f:
                for line in f.readlines()[6:]:
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 4:
                        c, d, pr = parts[1], parts[2], parse_price(parts[3])
                        if c and pr > 0:
                            p = self._create_product_record(
                                categoria_nombre="Mangueras Industriales e Hidráulicas",
                                familia_nombre="Mangueras Hidrocarburo",
                                raw_code=c,
                                raw_desc=f"Manguera Hidrocarburo {c} - Rollo {d}m",
                                raw_price=pr,
                                image_url="/static/img/13_ACRILICOS/imagen_1.jpg",
                            )
                            batch_prods.append(p)

        # ----------------------------------------------------------------------
        # 9. Demás carpetas usando articulos_normalizados.txt
        # ----------------------------------------------------------------------
        standard_folders = [
            ("03_ABRAZADERA_MINI_AMERICANA", "Abrazaderas y Acoples", "Abrazaderas Mini Americana", "/static/img/03_ABRAZADERA_MINI_AMERICANA/imagen_1.jpg"),
            ("04_ABRAZADERA_TIPO_AMERICANA_F", "Abrazaderas y Acoples", "Abrazaderas Fleje Ancho", "/static/img/04_ABRAZADERA_TIPO_AMERICANA_F/imagen_1.jpg"),
            ("05_ABRAZADERA_SUPER_PRESION", "Abrazaderas y Acoples", "Abrazaderas Súper Presión", "/static/img/05_ABRAZADERA_SUPER_PRESION/imagen_1.jpg"),
            ("06_ABRAZADERAS_DE_ALAMBRE", "Abrazaderas y Acoples", "Abrazaderas de Alambre", "/static/img/06_ABRAZADERAS_DE_ALAMBRE/imagen_1.jpg"),
            ("09_PILETEROS", "Mangueras Automotor", "Caños Pileteros", "/static/img/09_PILETEROS/imagen_1.jpg"),
            ("10_MANGAS", "Mangueras Industriales e Hidráulicas", "Mangas PVC", None),
            ("11_FUMIGACION", "Mangueras Industriales e Hidráulicas", "Mangueras de Fumigación", None),
            ("15_CORREAS_IND", "Correas y Transmisión", "Correas Industriales", None),
            ("16_CORREAS_AUTOM_Y_POLYV", "Correas y Transmisión", "Correas Automotor y Poly-V", None),
            ("17_CINTA_ROTOENFARDADORA", "Correas y Transmisión", "Cintas Rotoenfardadoras", None),
            ("18_ESCOBILLAS", "Mangueras Automotor", "Escobillas Limpiaparabrisas", "/static/img/18_ESCOBILLAS/imagen_1.jpg"),
            ("20_MANGUERAS_AIR-HOUSE", "Mangueras Industriales e Hidráulicas", "Mangueras Air-House", None),
            ("21_ORINGS", "Ferretería Industrial y Autopartes", "O-Rings y Sellos", None),
            ("23_LIQUIDOS", "Ferretería Industrial y Autopartes", "Líquidos de Freno y Fluidos", "/static/img/23_LIQUIDOS/imagen_1.jpg"),
            ("24_LATEX", "Mangueras Industriales e Hidráulicas", "Látex", "/static/img/24_LATEX/imagen_1.jpg"),
            ("25_MANGUERAS_RIEGO", "Mangueras Industriales e Hidráulicas", "Mangueras de Riego", "/static/img/25_MANGUERAS_RIEGO/imagen_1.jpg"),
            ("26_CEBADORES", "Mangueras Automotor", "Cebadores", "/static/img/26_CEBADORES/imagen_1.jpg"),
            ("27_PRECINTOS", "Ferretería Industrial y Autopartes", "Precintos", "/static/img/27_PRECINTOS/imagen_1.jpg"),
        ]

        for fldr, cat_name, fam_name, img_path in standard_folders:
            norm_path = os.path.join(self.data_dir, fldr, "articulos_normalizados.txt")
            if os.path.exists(norm_path):
                with open(norm_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f.readlines()[6:]:
                        parts = [p.strip() for p in line.split("|")]
                        if len(parts) >= 4:
                            p = self._create_product_record(
                                categoria_nombre=cat_name,
                                familia_nombre=fam_name,
                                raw_code=parts[0],
                                raw_desc=parts[2],
                                raw_price=parse_price(parts[3]),
                                image_url=img_path,
                            )
                            batch_prods.append(p)
                            if len(batch_prods) >= 1000:
                                flush_batch()

        # Descarga final de productos pendientes
        flush_batch()
        self.session.commit()
        print(f"✓ Catálogo de Productos insertado: {self.stats['productos']} registros.")

        # ----------------------------------------------------------------------
        # 10. Clientes B2B y Administrador de demostración
        # ----------------------------------------------------------------------
        demo_clientes = [
            ClienteModel(
                id="cli-vendedor-001",
                email="vendedor@atuelgomas.com",
                razon_social="Carlos Ventas (Zona Cuyo)",
                cuit="20-33445566-7",
                telefono="+54 261 411-2233",
                direccion="San Martín 1500",
                ciudad="Mendoza",
                rol="sales_agent",
                is_approved=True,
                hashed_password="pbkdf2_sha256$260000$salt$vendedor_pass_hash",
            ),
            ClienteModel(
                id="cli-b2b-001",
                email="cliente@atuelgomas.com",
                razon_social="Distribuidora Central de Gomas y Repuestos SRL",
                cuit="30-71122334-9",
                telefono="+54 11 4855-9000",
                direccion="Av. Warnes 1450",
                ciudad="CABA",
                rol="b2b_client",
                sales_agent_id="cli-vendedor-001",
                is_approved=True,
                hashed_password="pbkdf2_sha256$260000$salt$cliente_pass_hash",
            ),
            ClienteModel(
                id="cli-admin-001",
                email="admin@atuelgomas.com",
                razon_social="Atuel Gomas Casa Central",
                cuit="30-55112233-4",
                telefono="+54 11 4000-5000",
                direccion="Av. San Martín 2500",
                ciudad="Buenos Aires",
                rol="admin",
                is_approved=True,
                hashed_password="pbkdf2_sha256$260000$salt$admin_pass_hash",
            ),
        ]
        self.session.add_all(demo_clientes)
        self.session.commit()

        self.stats["clientes"] += len(demo_clientes)
        print(f"✓ Clientes iniciales cargados: {self.stats['clientes']}.")

        duration = time.time() - t_start
        print(f"\n[OK] INGESTA COMPLETADA EXITOSAMENTE EN {duration:.2f} SEGUNDOS.")
        return self.stats


# ==============================================================================
# 5. Punto de Entrada Principal y Reporte
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="Seeder masivo de datos para Atuel Gomas")
    parser.add_argument("--reset", action="store_true", default=True, help="Reiniciar tablas antes de cargar")
    parser.add_argument("--data-dir", default=os.path.join(PROJECT_ROOT, "datos provicionales"), help="Ruta de insumos")
    args = parser.parse_args()

    print(f"Conectando a base de datos: {DATABASE_URL}")
    if args.reset:
        print("Reiniciando esquema físico de tablas...")
        drop_db()

    init_db()

    with SessionLocal() as session:
        seeder = DataSeeder(session, args.data_dir)
        stats = seeder.run_seeder()

        # Verificación y balance final directamente en base de datos
        total_cats = session.scalar(select(func.count(CategoriaModel.id)))
        total_fams = session.scalar(select(func.count(FamiliaModel.id)))
        total_prods = session.scalar(select(func.count(ProductoModel.id)))
        total_vars = session.scalar(select(func.count(VarianteModel.id)))
        total_compats = session.scalar(select(func.count(CompatibilidadVehicularModel.id)))
        total_talles = session.scalar(select(func.count(TalleModel.id)))
        total_colores = session.scalar(select(func.count(ColorModel.id)))
        total_materiales = session.scalar(select(func.count(MaterialModel.id)))
        total_punteras = session.scalar(select(func.count(PunteraModel.id)))
        total_clientes = session.scalar(select(func.count(ClienteModel.id)))

        print("\n" + "=" * 80)
        print("BALANCE AUDITADO DE BASE DE DATOS (TABLAS FÍSICAS)")
        print("=" * 80)
        print(f"  • Categorías maestras:               {total_cats:>6}")
        print(f"  • Familias técnicas:                 {total_fams:>6}")
        print(f"  • Artículos y Productos cargados:    {total_prods:>6}")
        print(f"  • Variantes relacionales (M:N):      {total_vars:>6}")
        print(f"  • Talles y Medidas normalizados:     {total_talles:>6}")
        print(f"  • Colores técnicos:                  {total_colores:>6}")
        print(f"  • Materiales y Compuestos:           {total_materiales:>6}")
        print(f"  • Punteras de seguridad:             {total_punteras:>6}")
        print(f"  • Compatibilidades vehiculares:      {total_compats:>6}")
        print(f"  • Clientes B2B registrados:          {total_clientes:>6}")
        print("=" * 80)


if __name__ == "__main__":
    main()
