import sqlite3

def run():
    conn = sqlite3.connect("atuel_gomas.db")
    c = conn.cursor()
    
    # 1. Columnas rubro si no existen
    for table, col in [("productos", "rubro TEXT DEFAULT 'AUTOPARTES'"), 
                       ("categorias", "rubro TEXT DEFAULT 'AMBOS'"), 
                       ("clientes", "rubro TEXT DEFAULT 'AMBOS'")]:
        try:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {col}")
            print(f"Columna {col} agregada a {table}")
        except sqlite3.OperationalError as e:
            print(f"{table} ya tiene columna o error: {e}")
            
    # 2. Asignar rubros a categorias
    # 1: Mangueras Automotor -> AUTOPARTES
    # 2: Mangueras Industriales e Hidráulicas -> FERRETERIA
    # 3: Abrazaderas y Acoples -> AMBOS
    # 4: Artículos de Protección y EPP -> FERRETERIA
    # 5: Correas y Transmisión -> AMBOS
    # 6: Pisos y Revestimientos -> FERRETERIA
    # 7: Ferretería Industrial y Autopartes -> AMBOS
    rubros_cat = {
        1: "AUTOPARTES",
        2: "FERRETERIA",
        3: "AMBOS",
        4: "FERRETERIA",
        5: "AMBOS",
        6: "FERRETERIA",
        7: "AMBOS",
    }
    for cat_id, rubro in rubros_cat.items():
        c.execute("UPDATE categorias SET rubro = ? WHERE id = ?", (rubro, cat_id))
        
    # 3. Asignar rubro a productos basado en su categoria_id
    for cat_id, rubro in rubros_cat.items():
        c.execute("UPDATE productos SET rubro = ? WHERE categoria_id = ?", (rubro, cat_id))
        
    # Ajustar correas automotor a AUTOPARTES y correas industriales a FERRETERIA
    c.execute("UPDATE productos SET rubro = 'AUTOPARTES' WHERE familia_id = 31")
    c.execute("UPDATE productos SET rubro = 'FERRETERIA' WHERE familia_id in (32, 33)")
    # Cebadores y Escobillas en Cat 1 a AUTOPARTES (ya esta por cat 1)
    # Acoples y abrazaderas
    c.execute("UPDATE productos SET rubro = 'AUTOPARTES' WHERE familia_id in (13, 14, 16)") # mini americana, fleje ancho, alambre
    c.execute("UPDATE productos SET rubro = 'FERRETERIA' WHERE familia_id in (15, 17, 18)") # super presion, acoples rapidos, aluminio
    # O-rings y fluidos
    c.execute("UPDATE productos SET rubro = 'AUTOPARTES' WHERE familia_id = 41") # fluidos de freno
    c.execute("UPDATE productos SET rubro = 'FERRETERIA' WHERE familia_id in (37, 38, 39, 40, 42)") # orings, cadenas, grampas, remaches, precintos
    
    # 4. Reclasificar Tubos Termocontraibles:
    # Ver si existe o creamos la familia 'Accesorios Técnicos' o movemos familia 29 a categoria 7
    # "Reclasificar Tubos Termocontraíbles fuera de EPP hacia Ferretería Industrial."
    c.execute("UPDATE familias SET categoria_id = 7, nombre = 'Tubos Termocontraíbles' WHERE id = 29")
    c.execute("UPDATE productos SET categoria_id = 7, rubro = 'FERRETERIA' WHERE familia_id = 29")
    print("Tubos termocontraibles reclasificados a categoria 7")
    
    conn.commit()
    
    # Verificacion
    c.execute("SELECT id, nombre, rubro FROM categorias")
    print("Categorias con rubro:", c.fetchall())
    
    c.execute("SELECT rubro, count(id) FROM productos GROUP BY rubro")
    print("Productos por rubro:", c.fetchall())
    
    c.execute("SELECT p.id, p.nombre, p.categoria_id, p.rubro, f.nombre, c.nombre FROM productos p JOIN familias f ON p.familia_id = f.id JOIN categorias c ON p.categoria_id = c.id WHERE f.id = 29")
    print("Tubos en DB:", c.fetchall())

    conn.close()

if __name__ == "__main__":
    run()
