import sqlite3

def run():
    conn = sqlite3.connect("atuel_gomas.db")
    c = conn.cursor()

    # 1. Asegurar columna rubro en familias
    try:
        c.execute("ALTER TABLE familias ADD COLUMN rubro TEXT DEFAULT 'AMBOS'")
        print("Columna rubro agregada a familias")
    except sqlite3.OperationalError as e:
        print("Columna rubro ya existe o error en familias:", e)

    # 2. Reubicar Caños Pileteros a Ferretería Industrial (Categoría 2)
    # Familia 5: Caños Pileteros
    c.execute("UPDATE familias SET categoria_id = 2, rubro = 'FERRETERIA' WHERE id = 5")
    c.execute("UPDATE productos SET categoria_id = 2, rubro = 'FERRETERIA' WHERE familia_id = 5")
    print("[OK] Caños Pileteros reubicados a Categoría 2 (Ferretería Industrial)")

    # 3. Crear categoría 'Accesorios y Mantenimiento Automotor' para Autopartes si no existe
    c.execute("SELECT id FROM categorias WHERE slug = 'accesorios-mantenimiento-automotor'")
    cat_acc = c.fetchone()
    if not cat_acc:
        c.execute("""
            INSERT INTO categorias (nombre, slug, descripcion, rubro, activo)
            VALUES ('Accesorios y Mantenimiento Automotor', 'accesorios-mantenimiento-automotor', 
                    'Escobillas limpiaparabrisas, peras cebadoras de combustible y accesorios de mantenimiento.', 'AUTOPARTES', 1)
        """)
        cat_acc_id = c.lastrowid
        print(f"[OK] Creada Categoría 'Accesorios y Mantenimiento Automotor' con ID {cat_acc_id}")
    else:
        cat_acc_id = cat_acc[0]
        c.execute("UPDATE categorias SET rubro = 'AUTOPARTES' WHERE id = ?", (cat_acc_id,))
        print(f"[OK] Categoría 'Accesorios y Mantenimiento Automotor' existente con ID {cat_acc_id}")

    # Reubicar Escobillas Limpiaparabrisas (Familia 3) y Cebadores (Familia 4) a cat_acc_id
    c.execute("UPDATE familias SET categoria_id = ?, rubro = 'AUTOPARTES' WHERE id = 3", (cat_acc_id,))
    c.execute("UPDATE productos SET categoria_id = ?, rubro = 'AUTOPARTES' WHERE familia_id = 3", (cat_acc_id,))
    c.execute("UPDATE familias SET categoria_id = ?, rubro = 'AUTOPARTES' WHERE id = 4", (cat_acc_id,))
    c.execute("UPDATE productos SET categoria_id = ?, rubro = 'AUTOPARTES' WHERE familia_id = 4", (cat_acc_id,))
    print("[OK] Escobillas y Cebadores reubicados a 'Accesorios y Mantenimiento Automotor'")

    # 4. Segregar Correas
    # Familia 31: Correas Automotor y Poly-V -> AUTOPARTES
    # Familia 32: Correas Industriales -> FERRETERIA
    # Familia 33: Cintas Rotoenfardadoras -> FERRETERIA
    c.execute("UPDATE familias SET rubro = 'AUTOPARTES' WHERE id = 31")
    c.execute("UPDATE productos SET rubro = 'AUTOPARTES' WHERE familia_id = 31")

    c.execute("UPDATE familias SET rubro = 'FERRETERIA' WHERE id IN (32, 33)")
    c.execute("UPDATE productos SET rubro = 'FERRETERIA' WHERE familia_id IN (32, 33)")
    print("[OK] Correas segregadas estrictamente (Automotor -> AUTOPARTES, Industriales/Rotoenfardadoras -> FERRETERIA)")

    # 5. Crear las subfamilias/aplicaciones para Mangueras Automotor (Categoría 1)
    # Definición de subfamilias requeridas:
    subfamilias_def = [
        ("Mangueras de Radiador", "mangueras-radiador", "Mangueras superiores, inferiores y de refrigeración de motor."),
        ("Mangueras de Admisión de Aire", "mangueras-admision-aire", "Mangueras de filtro de aire, admisión y toberas."),
        ("Mangueras de Combustible", "mangueras-combustible", "Mangueras de conducción y retorno de combustible."),
        ("Mangueras de Turbo e Intercooler", "mangueras-turbo-intercooler", "Mangueras de silicona y caucho de alta presión y temperatura."),
        ("Mangueras de Calefacción", "mangueras-calefaccion", "Mangueras de circuito de calefacción y climatización de habitáculo."),
        ("Fuelles de Suspensión y Dirección", "fuelles-suspension-direccion", "Fuelles para semieje, caja de dirección y homocinética."),
    ]

    fam_ids = {}
    for name, slug, desc in subfamilias_def:
        c.execute("SELECT id FROM familias WHERE slug = ?", (slug,))
        row = c.fetchone()
        if not row:
            c.execute("""
                INSERT INTO familias (categoria_id, nombre, slug, descripcion, rubro, activo)
                VALUES (1, ?, ?, ?, 'AUTOPARTES', 1)
            """, (name, slug, desc))
            fam_ids[slug] = c.lastrowid
            print(f"[OK] Creada subfamilia '{name}' con ID {fam_ids[slug]}")
        else:
            fam_ids[slug] = row[0]
            c.execute("UPDATE familias SET categoria_id = 1, rubro = 'AUTOPARTES' WHERE id = ?", (fam_ids[slug],))
            print(f"[OK] Subfamilia '{name}' existente con ID {fam_ids[slug]}")

    # Asegurar familia 2 (Mangueras de Goma por Metro) en Cat 1 con rubro AUTOPARTES
    c.execute("UPDATE familias SET categoria_id = 1, rubro = 'AUTOPARTES' WHERE id = 2")
    c.execute("UPDATE productos SET categoria_id = 1, rubro = 'AUTOPARTES' WHERE familia_id = 2")

    # Reclasificar productos de Familia 1 (Mangueras de Goma Moldeada) hacia las nuevas subfamilias según keywords
    # Orden de precedencia para evitar clasificaciones incorrectas:
    # 1. Fuelles
    c.execute("""
        UPDATE productos 
        SET familia_id = ? 
        WHERE categoria_id = 1 AND familia_id = 1 
          AND (lower(nombre) LIKE '%fuelle%' OR lower(nombre) LIKE '%semieje%' OR lower(nombre) LIKE '%cremallera%')
    """, (fam_ids["fuelles-suspension-direccion"],))
    print(f"  -> Fuelles asignados: {c.rowcount}")

    # 2. Turbo e Intercooler
    c.execute("""
        UPDATE productos 
        SET familia_id = ? 
        WHERE categoria_id = 1 AND familia_id = 1 
          AND (lower(nombre) LIKE '%turbo%' OR lower(nombre) LIKE '%intercooler%')
    """, (fam_ids["mangueras-turbo-intercooler"],))
    print(f"  -> Turbo/Intercooler asignados: {c.rowcount}")

    # 3. Combustible
    c.execute("""
        UPDATE productos 
        SET familia_id = ? 
        WHERE categoria_id = 1 AND familia_id = 1 
          AND (lower(nombre) LIKE '%combustible%' OR lower(nombre) LIKE '%nafta%' OR lower(nombre) LIKE '%gasoil%' OR lower(nombre) LIKE '%retorno%')
    """, (fam_ids["mangueras-combustible"],))
    print(f"  -> Combustible asignados: {c.rowcount}")

    # 4. Admisión de Aire
    c.execute("""
        UPDATE productos 
        SET familia_id = ? 
        WHERE categoria_id = 1 AND familia_id = 1 
          AND (lower(nombre) LIKE '%admision%' OR lower(nombre) LIKE '%aire%' OR lower(nombre) LIKE '%filtro%')
    """, (fam_ids["mangueras-admision-aire"],))
    print(f"  -> Admisión de Aire asignados: {c.rowcount}")

    # 5. Calefacción
    c.execute("""
        UPDATE productos 
        SET familia_id = ? 
        WHERE categoria_id = 1 AND familia_id = 1 
          AND (lower(nombre) LIKE '%calefaccion%' OR lower(nombre) LIKE '%calefactor%')
    """, (fam_ids["mangueras-calefaccion"],))
    print(f"  -> Calefacción asignados: {c.rowcount}")

    # 6. Radiador y Refrigeración
    c.execute("""
        UPDATE productos 
        SET familia_id = ? 
        WHERE categoria_id = 1 AND familia_id = 1 
          AND (lower(nombre) LIKE '%radiador%' OR lower(nombre) LIKE '%deposito%' OR lower(nombre) LIKE '%vaso%' 
               OR lower(nombre) LIKE '%bomba%' OR lower(nombre) LIKE '%termostato%' OR lower(nombre) LIKE '%enfriador%'
               OR lower(nombre) LIKE '%inferior%' OR lower(nombre) LIKE '%superior%' OR lower(nombre) LIKE '%paso%')
    """, (fam_ids["mangueras-radiador"],))
    print(f"  -> Radiador y refrigeración asignados: {c.rowcount}")

    # Renombrar familia 1 a 'Mangueras Especiales y Derivaciones' para albergar las restantes
    c.execute("""
        UPDATE familias 
        SET nombre = 'Mangueras Especiales y Derivaciones',
            slug = 'mangueras-especiales-derivaciones',
            descripcion = 'Mangueras técnicas conformadas para conexiones especiales de motor y fluidos.',
            rubro = 'AUTOPARTES'
        WHERE id = 1
    """)

    # 6. Asignar rubros por defecto a todas las familias restantes según su categoría
    c.execute("""
        UPDATE familias 
        SET rubro = (SELECT c.rubro FROM categorias c WHERE c.id = familias.categoria_id)
        WHERE rubro IS NULL OR rubro = 'AMBOS'
    """)
    # Reforzar rubros específicos
    c.execute("UPDATE familias SET rubro = 'AUTOPARTES' WHERE id = 31")
    c.execute("UPDATE familias SET rubro = 'FERRETERIA' WHERE id IN (32, 33)")
    c.execute("UPDATE familias SET rubro = 'FERRETERIA' WHERE id = 5") # Caños pileteros
    c.execute("UPDATE familias SET rubro = 'AUTOPARTES' WHERE categoria_id = 1")
    c.execute("UPDATE familias SET rubro = 'AUTOPARTES' WHERE categoria_id = ?", (cat_acc_id,))

    conn.commit()

    # Reporte de verificación
    print("\n" + "=" * 60)
    print("REPORTE DE CATEGORIAS Y FAMILIAS RESULTANTE:")
    print("=" * 60)
    c.execute("SELECT id, nombre, rubro FROM categorias ORDER BY id")
    for cat in c.fetchall():
        print(f"\n[Categoría {cat[0]}] {cat[1]} ({cat[2]}):")
        c.execute("""
            SELECT f.id, f.nombre, f.slug, f.rubro, count(p.id)
            FROM familias f
            LEFT JOIN productos p ON p.familia_id = f.id
            WHERE f.categoria_id = ?
            GROUP BY f.id
            ORDER BY count(p.id) DESC
        """, (cat[0],))
        for fam in c.fetchall():
            print(f"   -> Fam {fam[0]}: {fam[1]} (slug={fam[2]}, rubro={fam[3]}) => {fam[4]} productos")

    conn.close()

if __name__ == "__main__":
    run()
