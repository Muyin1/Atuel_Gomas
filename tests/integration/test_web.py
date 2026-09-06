from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_home_page_renders_successfully():
    response = client.get("/")
    assert response.status_code == 200
    assert "ATUEL" in response.text
    assert "GOMAS" in response.text
    assert "Catálogo Técnico" in response.text

def test_htmx_search_filter_by_brand():
    response = client.get("/api/productos/search?vehicle_brand=Renault")
    assert response.status_code == 200
    assert "Renault" in response.text
    assert "Kangoo" in response.text
    # El burlete universal o productos no Renault no deberían aparecer si filtramos exclusivamente
    assert "Peugeot" not in response.text

def test_product_detail_page():
    response = client.get("/producto/PROD-001")
    assert response.status_code == 200
    assert "AG-RAD-101" in response.text
    assert "Manguera Superior de Radiador" in response.text
