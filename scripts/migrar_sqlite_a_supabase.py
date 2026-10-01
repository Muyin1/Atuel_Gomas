#!/usr/bin/env python3
"""
Script de Migración Masiva: SQLite ('atuel_gomas.db') -> PostgreSQL Cloud ('Supabase')
Etapa: Posta 2 - Data Specialist (ETL & Sincronización)

Migra de forma ordenada respetando integridad referencial (Foreign Keys)
todas las 12 tablas del modelo 3FN de Atuel Gomas:
1. Tablas de atributos (talles_medidas, colores, materiales, punteras_seguridad)
2. Clasificación (categorias, familias)
3. Productos (12.829 productos con rubros, precios, stocks y medidas)
4. Variantes relacionales (producto_variantes)
5. Compatibilidad vehicular (producto_compatibilidad_vehicular)
6. Clientes y Pedidos (clientes, ordenes, orden_items)

Optimizado para inserción por lotes (batches de 1.000 registros) para evitar timeouts de red.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import os
import sys
import time
from typing import Any

# Asegurar path del proyecto
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, func, insert, select, text
from sqlalchemy.orm import Session

from src.infrastructure.database.connection import DATABASE_URL as PG_DATABASE_URL, engine as pg_engine
from src.infrastructure.database.models import (
    CategoriaModel,
    ClienteModel,
    ColorModel,
    CompatibilidadVehicularModel,
    FamiliaModel,
    MaterialModel,
    OrdenItemModel,
    OrdenModel,
    ProductoModel,
    PunteraModel,
    TalleModel,
    VarianteModel,
)

SQLITE_PATH = os.path.join(PROJECT_ROOT, "atuel_gomas.db")
SQLITE_URL = f"sqlite:///{SQLITE_PATH}"


def parse_datetime(val: Any) -> datetime | None:
    """Convierte cadenas ISO de SQLite a objetos datetime con timezone UTC."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val if val.tzinfo else val.replace(tzinfo=timezone.utc)
    if isinstance(val, str) and val.strip():
        try:
            dt = datetime.fromisoformat(val.strip())
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            return None
    return None


def parse_bool(val: Any) -> bool | None:
    """Convierte 1/0 o strings a booleanos nativos de PostgreSQL."""
    if val is None:
        return None
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val != 0
    if isinstance(val, str):
        return val.strip().lower() in ("true", "1", "t", "yes", "si")
    return bool(val)


def migrate_table(
    table_name: str,
    model: Any,
    sqlite_conn: Any,
    pg_conn: Any,
    transform_row_func: Any = None,
    batch_size: int = 1000,
) -> int:
    """Extrae registros de SQLite e inserta en Supabase PostgreSQL por lotes."""
    print(f"\n[+] Migrando tabla '{table_name}'...")
    t0 = time.time()

    # Extraer registros de SQLite
    result = sqlite_conn.execute(text(f"SELECT * FROM {table_name}"))
    columns = result.keys()
    raw_rows = [dict(zip(columns, row)) for row in result.fetchall()]
    total_rows = len(raw_rows)

    if total_rows == 0:
        print(f"    - Sin registros en '{table_name}' (0 filas).")
        return 0

    # Aplicar transformaciones de tipos si corresponde
    transformed_rows = []
    for r in raw_rows:
        row_dict = dict(r)
        if transform_row_func:
            row_dict = transform_row_func(row_dict)
        transformed_rows.append(row_dict)

    # Inserción en lotes (batch insert)
    inserted_count = 0
    for i in range(0, total_rows, batch_size):
        chunk = transformed_rows[i : i + batch_size]
        stmt = insert(model).values(chunk)
        pg_conn.execute(stmt)
        inserted_count += len(chunk)
        print(f"    -> Insertadas {inserted_count}/{total_rows} filas ({int(inserted_count/total_rows*100)}%)")

    pg_conn.commit()

    # Actualizar secuencia de autoincremento en PostgreSQL si la tabla tiene PK entero
    try:
        seq_query = text(f"""
            SELECT setval(
                pg_get_serial_sequence('{table_name}', 'id'),
                COALESCE((SELECT MAX(id) FROM {table_name}), 1),
                (SELECT MAX(id) FROM {table_name}) IS NOT NULL
            );
        """)
        pg_conn.execute(seq_query)
        pg_conn.commit()
    except Exception:
        # Tablas con PK no entero (ej: clientes con UUID) no tienen sequence 'id'
        pass

    duration = time.time() - t0
    print(f"    [OK] Tabla '{table_name}' completada: {inserted_count} filas migradas en {duration:.2f}s.")
    return inserted_count


def transform_categoria(r: dict) -> dict:
    r["activo"] = parse_bool(r.get("activo"))
    return r


def transform_familia(r: dict) -> dict:
    r["activo"] = parse_bool(r.get("activo"))
    return r


def transform_producto(r: dict) -> dict:
    r["activo"] = parse_bool(r.get("activo"))
    r["created_at"] = parse_datetime(r.get("created_at"))
    r["updated_at"] = parse_datetime(r.get("updated_at"))
    return r


def transform_variante(r: dict) -> dict:
    r["activo"] = parse_bool(r.get("activo"))
    return r


def transform_cliente(r: dict) -> dict:
    r["is_approved"] = parse_bool(r.get("is_approved"))
    r["created_at"] = parse_datetime(r.get("created_at"))
    return r


def transform_orden(r: dict) -> dict:
    r["created_at"] = parse_datetime(r.get("created_at"))
    return r


def main():
    parser = argparse.ArgumentParser(description="Migración masiva de SQLite a PostgreSQL Supabase")
    parser.add_argument("--batch-size", type=int, default=1000, help="Tamaño del lote de inserción")
    parser.add_argument("--truncate", action="store_true", default=True, help="Limpiar tablas remotas antes de migrar")
    args = parser.parse_args()

    print("=" * 80)
    print("ATUEL GOMAS - MIGRACIÓN MASIVA DE DATOS: SQLITE -> SUPABASE POSTGRESQL")
    print("=" * 80)
    print(f"Origen (SQLite):    {SQLITE_PATH}")
    print(f"Destino (Supabase): {PG_DATABASE_URL[:35]}...{PG_DATABASE_URL[-20:]}")
    print("=" * 80)

    if not os.path.exists(SQLITE_PATH):
        print(f"[ERROR] No se encontró el archivo de base de datos local '{SQLITE_PATH}'")
        sys.exit(1)

    t_global_start = time.time()
    sqlite_engine = create_engine(SQLITE_URL)

    with sqlite_engine.connect() as sqlite_conn, pg_engine.connect() as pg_conn:
        if args.truncate:
            print("\n[+] Limpiando tablas previas en Supabase (TRUNCATE CASCADE)...")
            truncate_sql = text("""
                TRUNCATE TABLE 
                    orden_items, 
                    ordenes, 
                    clientes, 
                    producto_compatibilidad_vehicular, 
                    producto_variantes, 
                    productos, 
                    familias, 
                    categorias, 
                    punteras_seguridad, 
                    materiales, 
                    colores, 
                    talles_medidas 
                RESTART IDENTITY CASCADE;
            """)
            pg_conn.execute(truncate_sql)
            pg_conn.commit()
            print("    [OK] Tablas remotas limpias e identidades reiniciadas.")

        stats: dict[str, int] = {}

        # 1. Atributos maestros
        stats["talles_medidas"] = migrate_table("talles_medidas", TalleModel, sqlite_conn, pg_conn, batch_size=args.batch_size)
        stats["colores"] = migrate_table("colores", ColorModel, sqlite_conn, pg_conn, batch_size=args.batch_size)
        stats["materiales"] = migrate_table("materiales", MaterialModel, sqlite_conn, pg_conn, batch_size=args.batch_size)
        stats["punteras_seguridad"] = migrate_table("punteras_seguridad", PunteraModel, sqlite_conn, pg_conn, batch_size=args.batch_size)

        # 2. Clasificación
        stats["categorias"] = migrate_table("categorias", CategoriaModel, sqlite_conn, pg_conn, transform_categoria, batch_size=args.batch_size)
        stats["familias"] = migrate_table("familias", FamiliaModel, sqlite_conn, pg_conn, transform_familia, batch_size=args.batch_size)

        # 3. Productos del catálogo
        stats["productos"] = migrate_table("productos", ProductoModel, sqlite_conn, pg_conn, transform_producto, batch_size=args.batch_size)

        # 4. Variantes y compatibilidades
        stats["producto_variantes"] = migrate_table("producto_variantes", VarianteModel, sqlite_conn, pg_conn, transform_variante, batch_size=args.batch_size)
        stats["producto_compatibilidad_vehicular"] = migrate_table("producto_compatibilidad_vehicular", CompatibilidadVehicularModel, sqlite_conn, pg_conn, batch_size=args.batch_size)

        # 5. Clientes y Pedidos
        stats["clientes"] = migrate_table("clientes", ClienteModel, sqlite_conn, pg_conn, transform_cliente, batch_size=args.batch_size)
        stats["ordenes"] = migrate_table("ordenes", OrdenModel, sqlite_conn, pg_conn, transform_orden, batch_size=args.batch_size)
        stats["orden_items"] = migrate_table("orden_items", OrdenItemModel, sqlite_conn, pg_conn, batch_size=args.batch_size)

    # Verificación final de integridad y conteos en Supabase
    print("\n" + "=" * 80)
    print("VERIFICACIÓN DE CONTEO Y AUDITORÍA FINAL (SUPABASE POSTGRESQL)")
    print("=" * 80)
    
    with pg_engine.connect() as pg_conn:
        audit_results = {}
        for t in [
            "categorias",
            "familias",
            "productos",
            "producto_variantes",
            "producto_compatibilidad_vehicular",
            "talles_medidas",
            "colores",
            "materiales",
            "punteras_seguridad",
            "clientes",
            "ordenes",
            "orden_items",
        ]:
            count = pg_conn.execute(text(f"SELECT count(*) FROM {t}")).scalar()
            audit_results[t] = count
            expected = stats.get(t, 0)
            status_tag = "[MATCH]" if count == expected else "[MISMATCH!]"
            print(f"  • {t:<35}: {count:>6} filas {status_tag} (Esperado: {expected})")

    total_migrated = sum(stats.values())
    total_duration = time.time() - t_global_start
    print("=" * 80)
    print(f"MIGRACIÓN COMPLETADA: {total_migrated:,} filas totales transferidas en {total_duration:.2f} segundos.")
    print("=" * 80)


if __name__ == "__main__":
    main()
