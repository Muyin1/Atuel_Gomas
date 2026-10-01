import sqlite3

def run():
    conn = sqlite3.connect("atuel_gomas.db")
    c = conn.cursor()

    # 1. Mini americana (familia 13)
    c.execute("UPDATE productos SET imagen_url = '/static/img/catalogo/03_abrazadera_mini_americana_imagen_1.jpg' WHERE familia_id = 13")

    # 2. Fleje ancho / americana (familia 14)
    c.execute("UPDATE productos SET imagen_url = '/static/img/catalogo/04_abrazadera_tipo_americana_f_imagen_1.png' WHERE familia_id = 14")

    # 3. Super presion (familia 15)
    c.execute("UPDATE productos SET imagen_url = '/static/img/catalogo/05_abrazadera_super_presion_imagen_1.jpg' WHERE familia_id = 15")

    # 4. Abrazaderas de alambre (familia 16)
    c.execute("UPDATE productos SET imagen_url = '/static/img/catalogo/06_abrazaderas_de_alambre_imagen_1.jpg' WHERE familia_id = 16")

    # 5. Pileteros (familia 5)
    c.execute("UPDATE productos SET imagen_url = '/static/img/catalogo/09_pileteros_imagen_1.png' WHERE familia_id = 5")

    # 6. Pisos (familia 34)
    c.execute("UPDATE productos SET imagen_url = '/static/img/catalogo/14_pisos_imagen_1.png' WHERE familia_id = 34")

    # 7. Escobillas (familia 3)
    c.execute("UPDATE productos SET imagen_url = '/static/img/catalogo/18_escobillas_imagen_1.jpg' WHERE familia_id = 3")

    # 8. Fluidos y Liquidos de freno (familia 41)
    c.execute("UPDATE productos SET imagen_url = '/static/img/catalogo/23_liquidos_imagen_1.jpg' WHERE familia_id = 41")

    # 9. Latex (familia 12)
    c.execute("UPDATE productos SET imagen_url = '/static/img/catalogo/24_latex_imagen_1.jpg' WHERE familia_id = 12")

    # 10. Mangueras de riego (familia 11)
    c.execute("UPDATE productos SET imagen_url = '/static/img/catalogo/25_mangueras_riego_imagen_1.png' WHERE familia_id = 11")

    # 11. Cebadores (familia 4)
    c.execute("UPDATE productos SET imagen_url = '/static/img/catalogo/26_cebadores_imagen_1.jpg' WHERE familia_id = 4")

    # 12. Precintos (familia 42)
    c.execute("UPDATE productos SET imagen_url = '/static/img/catalogo/27_precintos_imagen_1.jpg' WHERE familia_id = 42")

    # 13. Articulos de proteccion general (familia 27 y 28)
    c.execute("UPDATE productos SET imagen_url = '/static/img/catalogo/02_art_de_proteccion_imagen_1.jpg' WHERE familia_id IN (27, 28) AND (imagen_url IS NULL OR imagen_url LIKE '%02_ART_DE_PROTECCION%')")

    # 14. Corregir cualquier imagen_url previa con ruta vieja
    c.execute("SELECT id, imagen_url FROM productos WHERE imagen_url LIKE '%02_ART_DE_PROTECCION%'")
    for pid, url in c.fetchall():
        new_url = url.replace("/static/img/02_ART_DE_PROTECCION/", "/static/img/catalogo/02_art_de_proteccion_")
        c.execute("UPDATE productos SET imagen_url = ? WHERE id = ?", (new_url, pid))

    conn.commit()

    c.execute("SELECT count(id) FROM productos WHERE imagen_url IS NOT NULL")
    print("Total productos con imagen_url en DB:", c.fetchone()[0])

    c.execute("SELECT id, nombre, imagen_url FROM productos WHERE imagen_url IS NOT NULL AND familia_id in (3, 4, 5, 11, 12, 13, 14, 15, 16, 34, 41, 42) LIMIT 10")
    for row in c.fetchall():
        print(row)

    conn.close()

if __name__ == "__main__":
    run()
