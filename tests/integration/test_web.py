from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_home_page_renders_successfully():
    response = client.get("/")
    assert response.status_code == 200
    assert "ATUEL" in response.text
    assert "GOMAS" in response.text
    assert "Tecnico" in response.text or "Técnico" in response.text or "Catalogo" in response.text
    assert "Solicitar Cuenta Mayorista" in response.text
    assert "Acceso Clientes" in response.text

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
    # Verificación de enrutamiento dinámico de números comerciales
    assert "261 262-9209" in response.text or "5492612629209" in response.text
    assert "2625 46-8732" in response.text or "5492625468732" in response.text
    assert "Mendoza / San Luis (Cuyo)" in response.text
    assert "Otras Provincias / Resto del País" in response.text

    post_resp = client.post(
        "/contacto",
        data={
            "nombre": "Ferretería Industrial Sur",
            "email": "sur@ferreteria.com",
            "telefono": "1144445555",
            "rubro": "ferreteria",
            "zona": "resto",
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

def test_solicitar_cuenta_page_and_submission():
    import uuid
    # 1. Carga de formulario
    resp_get = client.get("/solicitar-cuenta")
    assert resp_get.status_code == 200
    assert "Solicitud de Cuenta y Tarifa Mayorista" in resp_get.text
    assert "CUIT (11 dígitos)" in resp_get.text

    # Generar un CUIT y email únicos para asegurar idempotencia en base de datos real
    unique_suffix = str(uuid.uuid4().int % 100000000).zfill(8)
    test_cuit = f"30-{unique_suffix}-4"
    test_email = f"compras_{unique_suffix}@repuestossanjuan.com"

    # 2. Envío exitoso con CUIT nuevo
    resp_post = client.post(
        "/solicitar-cuenta",
        data={
            "business_name": "Casa de Repuestos San Juan SRL",
            "cuit": test_cuit,
            "rubro": "AUTOPARTES",
            "email": test_email,
            "phone": "+54 264 4220000",
            "province": "San Juan",
            "city": "Capital",
            "message": "Distribuidor mayorista de mangueras y correas"
        }
    )
    assert resp_post.status_code == 200
    assert "Solicitud Registrada con Éxito" in resp_post.text
    assert "Agilizar Alta por WhatsApp Directo" in resp_post.text

    # 3. Envío duplicado del mismo CUIT
    resp_dup = client.post(
        "/solicitar-cuenta",
        data={
            "business_name": "Repuestos Duplicados",
            "cuit": test_cuit,
            "rubro": "AUTOPARTES",
            "email": f"otro_{unique_suffix}@repuestossanjuan.com",
            "phone": "123456",
            "province": "San Juan",
            "city": "Capital"
        }
    )
    assert resp_dup.status_code == 400
    assert "solicitud pendiente" in resp_dup.text.lower() or "ya posee una cuenta" in resp_dup.text.lower()

def test_demo_login_endpoint():
    resp = client.get("/demo-login", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/"
    assert "b2b_session_user_id" in resp.headers["set-cookie"]

    # Al ingresar a la portada con esa cookie, se activa tarifa B2B
    cookie_header = resp.headers["set-cookie"].split(";")[0]
    home_resp = client.get("/", headers={"Cookie": cookie_header})
    assert home_resp.status_code == 200
    assert "Precios de Gremio / Mayorista Activos" in home_resp.text

def test_registro_admin_protection():
    # Usuario público o no autenticado intentando acceder a /registro -> Redirigido a /solicitar-cuenta
    resp = client.get("/registro", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/solicitar-cuenta"

def test_cart_empty_and_add_item():
    # 1. Carrito vacío
    resp_empty = client.get("/carrito")
    assert resp_empty.status_code == 200
    assert "Tu pedido actual está vacío" in resp_empty.text

    # 2. Agregar artículo al pedido con HTMX (retorna badge actualizado)
    resp_add = client.post("/carrito/agregar", data={"product_id": "PROD-001", "cantidad": 2})
    assert resp_add.status_code == 200
    assert 'id="cart-badge"' in resp_add.text
    assert '>2<' in resp_add.text
    assert "atuel_cart_items" in resp_add.headers["set-cookie"]

    # 3. Ver carrito con artículo cargado
    cart_cookie = resp_add.headers["set-cookie"].split(";")[0]
    resp_cart = client.get("/carrito", headers={"Cookie": cart_cookie})
    assert resp_cart.status_code == 200
    assert "AG-RAD-101" in resp_cart.text
    assert "Manguera Superior de Radiador" in resp_cart.text
    assert "Simulador de Envío / Despacho" in resp_cart.text
    assert "Confirmar y Enviar Pedido por WhatsApp" in resp_cart.text

    # 4. Actualizar cantidad
    resp_update = client.post(
        "/carrito/actualizar",
        data={"product_id": "PROD-001", "cantidad": 5},
        headers={"Cookie": cart_cookie},
        follow_redirects=False
    )
    assert resp_update.status_code == 303
    updated_cookie = resp_update.headers.get("set-cookie", cart_cookie).split(";")[0]

    # Verificar nueva cantidad en /carrito
    resp_cart_updated = client.get("/carrito", headers={"Cookie": updated_cookie})
    assert resp_cart_updated.status_code == 200
    assert ">5<" in resp_cart_updated.text

    # 5. Eliminar artículo del carrito
    resp_delete = client.post(
        "/carrito/eliminar",
        data={"product_id": "PROD-001"},
        headers={"Cookie": updated_cookie},
        follow_redirects=False
    )
    assert resp_delete.status_code == 303
    deleted_cookie = resp_delete.headers.get("set-cookie", updated_cookie).split(";")[0]

    # Verificar que vuelve a estar vacío
    resp_cart_cleared = client.get("/carrito", headers={"Cookie": deleted_cookie})
    assert resp_cart_cleared.status_code == 200
    assert "Tu pedido actual está vacío" in resp_cart_cleared.text


def test_cart_badge_persistence_across_all_pages():
    # 1. Agregar artículo al carrito
    resp_add = client.post("/carrito/agregar", data={"product_id": "PROD-001", "cantidad": 3})
    assert resp_add.status_code == 200
    cart_cookie = resp_add.headers["set-cookie"].split(";")[0]

    # 2. Verificar que en /contacto el badge del navbar muestre 3
    resp_contacto = client.get("/contacto", headers={"Cookie": cart_cookie})
    assert resp_contacto.status_code == 200
    assert '<span id="cart-badge" class="cart-badge">3</span>' in resp_contacto.text

    # 3. Verificar en /nosotros
    resp_nosotros = client.get("/nosotros", headers={"Cookie": cart_cookie})
    assert resp_nosotros.status_code == 200
    assert '<span id="cart-badge" class="cart-badge">3</span>' in resp_nosotros.text

    # 4. Verificar en /solicitar-cuenta
    resp_solicitar = client.get("/solicitar-cuenta", headers={"Cookie": cart_cookie})
    assert resp_solicitar.status_code == 200
    assert '<span id="cart-badge" class="cart-badge">3</span>' in resp_solicitar.text

    # 5. Verificar en /login
    resp_login = client.get("/login", headers={"Cookie": cart_cookie})
    assert resp_login.status_code == 200
    assert '<span id="cart-badge" class="cart-badge">3</span>' in resp_login.text

    # 6. Verificar en /carrito el texto de advertencia comercial actualizado
    resp_cart = client.get("/carrito", headers={"Cookie": cart_cookie})
    assert resp_cart.status_code == 200
    assert "Estás visualizando precios minoristas" in resp_cart.text
    assert "Contactate con un vendedor para conseguir una mejor oferta mayorista para tu negocio" in resp_cart.text


def test_perfil_page_and_markup_update():
    anon_client = TestClient(app)
    # 1. Intentar acceder a /perfil sin estar logueado -> Redirección a /login
    resp_anon = anon_client.get("/perfil", follow_redirects=False)
    assert resp_anon.status_code == 303
    assert resp_anon.headers["location"] == "/login"

    # 2. Iniciar sesión en modo demo
    resp_demo = client.get("/demo-login", follow_redirects=False)
    assert resp_demo.status_code == 303
    session_cookie = resp_demo.headers["set-cookie"].split(";")[0]

    # 3. Acceder a /perfil logueado
    resp_perfil = client.get("/perfil", headers={"Cookie": session_cookie})
    assert resp_perfil.status_code == 200
    assert "Mi Perfil Comercial" in resp_perfil.text
    assert "Modo Mostrador" in resp_perfil.text
    assert "user-avatar-bubble" in resp_perfil.text
    assert 'name="markup_percent"' in resp_perfil.text

    # 4. Actualizar margen de ganancia a 45.0%
    resp_update_markup = client.post(
        "/perfil/margen",
        data={"markup_percent": "45.0"},
        headers={"Cookie": session_cookie}
    )
    assert resp_update_markup.status_code == 200
    assert "45" in resp_update_markup.text
    assert "actualizado al 45" in resp_update_markup.text

    # 5. Verificar que el navbar en la portada ahora muestre el avatar bubble y link a /perfil
    resp_home = client.get("/", headers={"Cookie": session_cookie})
    assert resp_home.status_code == 200
    assert 'href="/perfil"' in resp_home.text
    assert "user-avatar-btn" in resp_home.text


def test_sales_agent_profile_view():
    from src.adapters.controllers.web_controller import sign_session_cookie, SESSION_COOKIE_NAME
    # cli-vendedor-001 es el vendedor semilla creado en Posta 7.1
    cookie_val = sign_session_cookie("cli-vendedor-001")
    cookie_header = f"{SESSION_COOKIE_NAME}={cookie_val}"

    resp = client.get("/perfil", headers={"Cookie": cookie_header})
    assert resp.status_code == 200
    assert "Panel del Asesor Comercial" in resp.text
    assert "Asesor Comercial Oficial" in resp.text
    assert "Mi Cartera de Clientes" in resp.text
    assert "Pedidos de mi Cartera" in resp.text
    assert "WhatsApp" in resp.text


def test_admin_assign_sales_agent_and_protection():
    from src.adapters.controllers.web_controller import sign_session_cookie, SESSION_COOKIE_NAME

    # 1. Intentar asignar como usuario no logueado -> 403
    resp_anon = client.post(
        "/admin/asignar-vendedor",
        data={"customer_id": "cli-b2b-001", "sales_agent_id": "cli-vendedor-001"}
    )
    assert resp_anon.status_code == 403

    # 2. Intentar asignar como SALES_AGENT -> 403
    vendedor_cookie = f"{SESSION_COOKIE_NAME}={sign_session_cookie('cli-vendedor-001')}"
    resp_vendedor = client.post(
        "/admin/asignar-vendedor",
        data={"customer_id": "cli-b2b-001", "sales_agent_id": "cli-vendedor-001"},
        headers={"Cookie": vendedor_cookie}
    )
    assert resp_vendedor.status_code == 403

    # 3. Asignar como ADMIN -> Crear o mockear admin
    from src.domain.entities.customer import Customer
    from src.domain.entities.user_role import UserRole
    from src.domain.value_objects.cuit import CUIT
    from src.infrastructure.config.container import container
    import pytest

    admin_user = Customer(
        id="usr-admin-test",
        email="admin.test@atuelgomas.com",
        business_name="Admin General Atuel",
        cuit=CUIT("20-11223344-5"),
        phone="+54 11 4000-5000",
        address="Oficina Central",
        city="Mendoza",
        role=UserRole.ADMIN,
        is_approved=True
    )
    # Guardar en repositorio para que get_current_user_from_cookie lo encuentre
    import asyncio
    asyncio.run(container.customer_repo.save(admin_user))

    admin_cookie = f"{SESSION_COOKIE_NAME}={sign_session_cookie(admin_user.id)}"

    # Asignar cliente a vendedor
    resp_assign = client.post(
        "/admin/asignar-vendedor",
        data={"customer_id": "cli-b2b-001", "sales_agent_id": "cli-vendedor-001"},
        headers={"Cookie": admin_cookie}
    )
    assert resp_assign.status_code == 200
    assert "✓ Asignado a" in resp_assign.text or "status-entregado" in resp_assign.text

    # Desasignar vendedor
    resp_unassign = client.post(
        "/admin/asignar-vendedor",
        data={"customer_id": "cli-b2b-001", "sales_agent_id": ""},
        headers={"Cookie": admin_cookie}
    )
    assert resp_unassign.status_code == 200
    assert "Sin Vendedor Asignado" in resp_unassign.text or "status-pendiente" in resp_unassign.text


def test_cart_confirm_order_checkout():
    from src.adapters.controllers.web_controller import (
        sign_session_cookie,
        encode_cart_cookie,
        get_cart_from_cookie,
        SESSION_COOKIE_NAME,
        CART_COOKIE_NAME
    )
    import asyncio
    from src.infrastructure.config.container import container

    # 1. Asegurar asignación de cli-b2b-001 a cli-vendedor-001
    asyncio.run(container.customer_repo.assign_sales_agent("cli-b2b-001", "cli-vendedor-001"))

    # 2. Preparar sesión B2B y carrito con artículos
    user_cookie = f"{SESSION_COOKIE_NAME}={sign_session_cookie('cli-b2b-001')}"
    cart_cookie_val = encode_cart_cookie({"PROD-001": 4})
    cart_cookie = f"{CART_COOKIE_NAME}={cart_cookie_val}"
    combined_cookies = f"{user_cookie}; {cart_cookie}"

    # 3. Confirmar pedido vía checkout JSON / AJAX
    resp = client.post(
        "/carrito/confirmar",
        data={"dest_zone": "cuyo", "notes": "Entrega por la mañana en taller"},
        headers={
            "Cookie": combined_cookies,
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest"
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    order_id = data["order_id"]
    assert order_id.startswith("ORD-")
    assert "wa.me/5492612629209" in data["whatsapp_url"]
    assert order_id in data["whatsapp_url"]

    # 4. Verificar que la cookie del carrito en la respuesta haya quedado vacía (badge en 0)
    set_cookie_header = resp.headers.get("set-cookie", "")
    assert CART_COOKIE_NAME in set_cookie_header
    for part in set_cookie_header.split(";"):
        if CART_COOKIE_NAME in part:
            cleared_cookie_val = part.split("=")[1].strip()
            # Crear mock request para verificar carrito
            class DummyReq:
                cookies = {CART_COOKIE_NAME: cleared_cookie_val}
            cleared_cart = get_cart_from_cookie(DummyReq())
            assert cleared_cart == {}

    # 5. Verificar que la orden exista en la DB y esté vinculada al cliente y a su vendedor
    order = asyncio.run(container.order_repo.get_by_id(order_id))
    assert order is not None
    assert order.customer_id == "cli-b2b-001"
    assert order.sales_agent_id == "cli-vendedor-001"
    assert "Mendoza / San Luis (Cuyo)" in order.notes

    # 6. Verificar que la orden aparezca en los pedidos del vendedor
    vendedor_orders = asyncio.run(container.order_repo.get_by_sales_agent("cli-vendedor-001"))
    assert any(o.id == order_id for o in vendedor_orders)







