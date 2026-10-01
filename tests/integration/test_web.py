from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_home_page_renders_successfully():
    response = client.get("/")
    assert response.status_code == 200
    assert "ATUEL" in response.text
    assert "GOMAS" in response.text
    assert "Tecnico" in response.text or "Técnico" in response.text or "Catalogo" in response.text

def test_htmx_search_filter_by_brand():
    response = client.get("/api/productos/search?vehicle_brand=Renault")
    assert response.status_code == 200
    assert "Renault" in response.text
    assert "Kangoo" in response.text
    assert "Peugeot" not in response.text

def test_product_detail_page():
    response = client.get("/producto/PROD-001")
    assert response.status_code == 200
    assert "AG-RAD-101" in response.text
    assert "Manguera Superior de Radiador" in response.text

def test_pagination_in_home_and_search():
    # Home debe incluir paginacion y conteo
    response = client.get("/?page=1")
    assert response.status_code == 200
    assert "12.829" in response.text or "12829" in response.text or "productos disponibles" in response.text

    # Busqueda HTMX en pagina 2
    response_p2 = client.get("/api/productos/search?page=2")
    assert response_p2.status_code == 200
    assert "2 de 535" in response_p2.text
    assert "page=3" in response_p2.text

def test_signed_session_cookie_spoofing_protection():
    from src.adapters.controllers.web_controller import sign_session_cookie, verify_session_cookie

    user_id = "test-user-uuid-1234"
    valid_signed = sign_session_cookie(user_id)
    assert verify_session_cookie(valid_signed) == user_id

    # Intentar alterar el user_id manteniendo la firma
    tampered = f"admin-id.{valid_signed.split('.')[1]}"
    assert verify_session_cookie(tampered) is None

    # Intentar cookie sin firma o formato invalido
    assert verify_session_cookie(user_id) is None
    assert verify_session_cookie(None) is None

def test_nosotros_page():
    response = client.get("/nosotros")
    assert response.status_code == 200
    assert "Atuel Gomas" in response.text
    assert "Nuestras" in response.text or "Trayectoria" in response.text

def test_contacto_page_and_submission():
    response = client.get("/contacto")
    assert response.status_code == 200
    assert "WhatsApp" in response.text
    assert "Envianos tu Consulta" in response.text

    post_resp = client.post(
        "/contacto",
        data={
            "nombre": "Ferretería Industrial Sur",
            "email": "sur@ferreteria.com",
            "telefono": "1144445555",
            "rubro": "ferreteria",
            "mensaje": "Solicito lista de precios mayorista de mangueras y pisos."
        }
    )
    assert post_resp.status_code == 200
    assert "recibida con" in post_resp.text

def test_rubro_tabs_and_dynamic_categories_in_home():
    response = client.get("/")
    assert response.status_code == 200
    # Tabs de rubro
    assert "Autopartes y Transporte" in response.text
    assert "Ferretería e Industria" in response.text
    assert "10.905" in response.text
    assert "3.206" in response.text
    # Categorías dinámicas desde DB con sus conteos
    assert "mangueras-automotor" in response.text
    assert "pisos-revestimientos" in response.text
    assert "abrazaderas-acoples" in response.text

def test_search_by_category_slug_htmx():
    # Búsqueda por slug de Pisos y Revestimientos
    response = client.get("/api/productos/search?category=pisos-revestimientos")
    assert response.status_code == 200
    assert "Pisos y Revestimientos" in response.text

    # Búsqueda por slug de Abrazaderas
    response_abr = client.get("/api/productos/search?category=abrazaderas-acoples")
    assert response_abr.status_code == 200
    assert "Abrazaderas" in response_abr.text
    # Debe renderizar la imagen técnica real enlazada
    assert "/static/img/catalogo/" in response_abr.text

def test_api_familias_htmx_endpoint():
    # Familias de mangueras automotor
    resp = client.get("/api/familias?category=mangueras-automotor")
    assert resp.status_code == 200
    assert "Mangueras de Radiador" in resp.text
    assert "Mangueras de Calefacci" in resp.text
    assert "Mangueras de Turbo" in resp.text

    # Segregación de Correas: en AUTOPARTES solo Poly-V / Automotor
    resp_auto = client.get("/api/familias?category=correas-transmision&rubro=AUTOPARTES")
    assert resp_auto.status_code == 200
    assert "Correas Automotor y Poly-V" in resp_auto.text
    assert "Correas Industriales" not in resp_auto.text
    assert "Cintas Rotoenfardadoras" not in resp_auto.text

    # Segregación de Correas: en FERRETERIA solo Industriales y Cintas
    resp_ferre = client.get("/api/familias?category=correas-transmision&rubro=FERRETERIA")
    assert resp_ferre.status_code == 200
    assert "Correas Industriales" in resp_ferre.text
    assert "Cintas Rotoenfardadoras" in resp_ferre.text
    assert "Correas Automotor y Poly-V" not in resp_ferre.text

def test_search_by_family_htmx():
    # Filtrar por subfamilia específica de turbo/intercooler
    resp = client.get("/api/productos/search?category=mangueras-automotor&family=mangueras-turbo-intercooler")
    assert resp.status_code == 200
    assert "TURBO" in resp.text.upper() or "INTERCOOLER" in resp.text.upper()



