import json
import base64
import hmac
import hashlib
import os
import math
import urllib.parse
from fastapi import APIRouter, Request, Depends, Form, HTTPException, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.infrastructure.config.container import container
from src.application.dtos.product_dto import ProductSearchDTO, PaginatedProductsDTO
from src.application.dtos.auth_dto import RegisterB2BDTO, LoginDTO, UpdateProfileDTO, AssignSalesAgentDTO
from src.application.dtos.order_dto import CreateOrderDTO, OrderItemInputDTO
from src.application.dtos.solicitud_cuenta_dto import SolicitudCuentaDTO
from src.domain.entities.product_category import ProductCategory
from src.domain.entities.user_role import UserRole
from src.domain.entities.business_line import BusinessLine
from src.domain.exceptions.domain_exceptions import (
    CustomerAlreadyExistsError,
    InvalidCustomerCredentialsError,
    UnauthorizedActionError
)

router = APIRouter()
templates = Jinja2Templates(directory="src/infrastructure/templates")

# Clave secreta para firma criptográfica de cookies de sesión
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "atuel_gomas_secret_session_key_2026_industrial").encode("utf-8")
SESSION_COOKIE_NAME = "b2b_session_user_id"
CART_COOKIE_NAME = "atuel_cart_items"
PAGE_SIZE_DEFAULT = 24


def get_cart_from_cookie(request: Request) -> dict[str, int]:
    """Lee el diccionario {product_id: cantidad} desde la cookie firmada o serializada en base64"""
    raw_val = request.cookies.get(CART_COOKIE_NAME)
    if not raw_val:
        return {}
    try:
        # Formato: base64_payload.signature
        if "." in raw_val:
            payload_b64, signature = raw_val.split(".", 1)
            expected_sig = hmac.new(SESSION_SECRET_KEY, payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected_sig):
                return {}
            json_bytes = base64.b64decode(payload_b64.encode("utf-8"))
            data = json.loads(json_bytes.decode("utf-8"))
            if isinstance(data, dict):
                return {str(k): int(v) for k, v in data.items() if int(v) > 0}
        return {}
    except Exception:
        return {}


def encode_cart_cookie(cart: dict[str, int]) -> str:
    """Serializa el carrito a base64 firmado con HMAC-SHA256"""
    clean_cart = {str(k): int(v) for k, v in cart.items() if int(v) > 0}
    json_str = json.dumps(clean_cart)
    payload_b64 = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
    signature = hmac.new(SESSION_SECRET_KEY, payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{signature}"


def sign_session_cookie(user_id: str) -> str:
    """Genera cookie firmada con HMAC-SHA256 para prevenir spoofing de identidad"""
    signature = hmac.new(SESSION_SECRET_KEY, user_id.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{user_id}.{signature}"


def verify_session_cookie(cookie_value: str | None) -> str | None:
    """Verifica la integridad de la cookie firmada. Retorna user_id si es válida o None si fue alterada"""
    if not cookie_value or "." not in cookie_value:
        return None
    try:
        user_id, signature = cookie_value.split(".", 1)
        expected_signature = hmac.new(SESSION_SECRET_KEY, user_id.encode("utf-8"), hashlib.sha256).hexdigest()
        if hmac.compare_digest(signature, expected_signature):
            return user_id
    except Exception:
        return None
    return None


async def get_current_user_from_cookie(request: Request):
    """Adaptador de seguridad para obtener el usuario autenticado desde la cookie de sesión firmada"""
    raw_cookie = request.cookies.get(SESSION_COOKIE_NAME)
    customer_id = verify_session_cookie(raw_cookie)
    if customer_id:
        customer = await container.customer_repo.get_by_id(customer_id)
        return customer
    return None


@router.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    page: int = 1,
    rubro: str | None = None,
    current_user = Depends(get_current_user_from_cookie)
):
    page = max(1, page)
    role = current_user.role if current_user else UserRole.PUBLIC

    # Preselección inteligente por rubro del cliente autenticado
    selected_rubro = None
    if rubro and rubro.strip():
        r_upper = rubro.strip().upper()
        if r_upper in ("AUTOPARTES", "FERRETERIA"):
            selected_rubro = r_upper
    elif current_user and getattr(current_user, "business_line", None):
        user_bl = current_user.business_line.value.upper() if hasattr(current_user.business_line, "value") else str(current_user.business_line).upper()
        if user_bl in ("AUTOPARTES", "FERRETERIA"):
            selected_rubro = user_bl

    # Obtener todas las categorías reales con su conteo y rubro
    all_categories = await container.product_repo.get_categories()
    
    # Obtener subfamilias iniciales (por defecto para Mangueras Automotor o según rubro)
    initial_category = "mangueras-automotor"
    initial_families = await container.product_repo.get_families(
        category_id_or_slug=initial_category,
        rubro=selected_rubro
    )

    user_markup = getattr(current_user, "markup_percent", None) if current_user else None
    dto = ProductSearchDTO(role=role, custom_markup=user_markup, page=page, page_size=PAGE_SIZE_DEFAULT)
    products = await container.search_products_uc.execute(dto)
    total_count = await container.product_repo.count()

    total_pages = max(1, math.ceil(total_count / PAGE_SIZE_DEFAULT)) if total_count > 0 else 1
    has_prev = page > 1
    has_next = page < total_pages

    paginated = PaginatedProductsDTO(
        items=products,
        total=total_count,
        page=page,
        page_size=PAGE_SIZE_DEFAULT,
        total_pages=total_pages,
        has_prev=has_prev,
        has_next=has_next
    )

    cart = get_cart_from_cookie(request)
    cart_total_items = sum(cart.values())

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "products": products,
            "paginated": paginated,
            "categories": all_categories,
            "families": initial_families,
            "current_user": current_user,
            "cart_total_items": cart_total_items,
            "is_b2b": role in (UserRole.B2B_CLIENT, UserRole.SALES_AGENT, UserRole.ADMIN),
            "current_query": "",
            "current_category": "",
            "current_family": "",
            "current_brand": "",
            "current_model": "",
            "current_rubro": selected_rubro or ""
        }
    )


@router.get("/api/familias", response_class=HTMLResponse)
async def get_families_htmx(
    request: Request,
    category: str | None = None,
    rubro: str | None = None,
    current_family: str | None = None
):
    """Endpoint reactivo HTMX para devolver selector/badges de subfamilias según categoría y rubro"""
    clean_cat = category.strip() if category and category.strip() else None
    clean_rubro = rubro.strip().upper() if rubro and rubro.strip() else None
    if clean_rubro not in ("AUTOPARTES", "FERRETERIA"):
        clean_rubro = None

    families = await container.product_repo.get_families(
        category_id_or_slug=clean_cat,
        rubro=clean_rubro
    )

    return templates.TemplateResponse(
        request=request,
        name="partials/family_selector.html",
        context={
            "families": families,
            "current_family": current_family.strip() if current_family else "",
            "current_category": clean_cat or "",
            "current_rubro": clean_rubro or ""
        }
    )


@router.get("/api/productos/search", response_class=HTMLResponse)
async def search_products_htmx(
    request: Request,
    query: str | None = None,
    category: str | None = None,
    family: str | None = None,
    vehicle_brand: str | None = None,
    vehicle_model: str | None = None,
    rubro: str | None = None,
    page: int = 1,
    current_user = Depends(get_current_user_from_cookie)
):
    """Endpoint reactivo HTMX para filtrado instantáneo del catálogo, subfamilias y paginación fluida"""
    page = max(1, page)
    role = current_user.role if current_user else UserRole.PUBLIC

    # Limpieza de parámetros de entrada
    clean_query = query.strip() if query and query.strip() else None
    clean_brand = vehicle_brand.strip() if vehicle_brand and vehicle_brand.strip() else None
    clean_model = vehicle_model.strip() if vehicle_model and vehicle_model.strip() else None
    clean_category = category.strip() if category and category.strip() else None
    clean_family = family.strip() if family and family.strip() else None
    clean_rubro = rubro.strip().upper() if rubro and rubro.strip() else None
    if clean_rubro not in ("AUTOPARTES", "FERRETERIA"):
        clean_rubro = None

    user_markup = getattr(current_user, "markup_percent", None) if current_user else None
    dto = ProductSearchDTO(
        query=clean_query,
        category=clean_category,
        family=clean_family,
        vehicle_brand=clean_brand,
        vehicle_model=clean_model,
        role=role,
        custom_markup=user_markup,
        page=page,
        page_size=PAGE_SIZE_DEFAULT
    )
    products = await container.search_products_uc.execute(dto)
    total_count = await container.product_repo.count(
        query=clean_query,
        category=clean_category,
        family=clean_family,
        vehicle_brand=clean_brand,
        vehicle_model=clean_model
    )

    total_pages = max(1, math.ceil(total_count / PAGE_SIZE_DEFAULT)) if total_count > 0 else 1
    has_prev = page > 1
    has_next = page < total_pages

    paginated = PaginatedProductsDTO(
        items=products,
        total=total_count,
        page=page,
        page_size=PAGE_SIZE_DEFAULT,
        total_pages=total_pages,
        has_prev=has_prev,
        has_next=has_next
    )

    return templates.TemplateResponse(
        request=request,
        name="partials/product_grid.html",
        context={
            "products": products,
            "paginated": paginated,
            "is_b2b": role in (UserRole.B2B_CLIENT, UserRole.SALES_AGENT, UserRole.ADMIN),
            "current_query": clean_query or "",
            "current_category": clean_category or "",
            "current_family": clean_family or "",
            "current_brand": clean_brand or "",
            "current_model": clean_model or "",
            "current_rubro": clean_rubro or ""
        }
    )




@router.get("/producto/{product_id}", response_class=HTMLResponse)
async def product_detail(request: Request, product_id: str, current_user = Depends(get_current_user_from_cookie)):
    product = await container.get_product_detail_uc.execute(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto técnico no encontrado")

    role = current_user.role if current_user else UserRole.PUBLIC
    user_markup = getattr(current_user, "markup_percent", None) if current_user else None
    price = product.calculate_price_for_role(role, custom_markup=user_markup)

    cart = get_cart_from_cookie(request)
    cart_total_items = sum(cart.values())

    return templates.TemplateResponse(
        request=request,
        name="product_detail.html",
        context={
            "product": product,
            "price": price,
            "current_user": current_user,
            "cart_total_items": cart_total_items,
            "is_b2b": role in (UserRole.B2B_CLIENT, UserRole.SALES_AGENT, UserRole.ADMIN)
        }
    )


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, current_user = Depends(get_current_user_from_cookie)):
    if current_user:
        return RedirectResponse(url="/", status_code=303)
    cart = get_cart_from_cookie(request)
    cart_total_items = sum(cart.values())
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"current_user": None, "cart_total_items": cart_total_items}
    )


@router.post("/login", response_class=HTMLResponse)
async def process_login(
    request: Request,
    cuit_or_email: str = Form(...),
    password: str = Form(...)
):
    try:
        dto = LoginDTO(cuit_or_email=cuit_or_email, password=password)
        customer = await container.auth_customer_uc.execute(dto)
        response = RedirectResponse(url="/", status_code=303)
        signed_cookie_val = sign_session_cookie(customer.id)
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=signed_cookie_val,
            httponly=True,
            samesite="lax",
            max_age=86400 * 7
        )
        return response
    except InvalidCustomerCredentialsError as e:
        cart = get_cart_from_cookie(request)
        cart_total_items = sum(cart.values())
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": str(e), "current_user": None, "cart_total_items": cart_total_items},
            status_code=400
        )


@router.get("/solicitar-cuenta", response_class=HTMLResponse)
async def solicitar_cuenta_page(request: Request, current_user = Depends(get_current_user_from_cookie)):
    if current_user:
        return RedirectResponse(url="/", status_code=303)
    cart = get_cart_from_cookie(request)
    cart_total_items = sum(cart.values())
    return templates.TemplateResponse(
        request=request,
        name="solicitar_cuenta.html",
        context={
            "current_user": None,
            "cart_total_items": cart_total_items,
            "enviado_ok": False,
            "error": None,
            "form_data": None
        }
    )


@router.post("/solicitar-cuenta", response_class=HTMLResponse)
async def process_solicitar_cuenta(
    request: Request,
    business_name: str = Form(...),
    cuit: str = Form(...),
    rubro: str = Form("AMBOS"),
    email: str = Form(...),
    phone: str = Form(...),
    province: str = Form(...),
    city: str = Form(...),
    message: str = Form(""),
    current_user = Depends(get_current_user_from_cookie)
):
    form_data = {
        "business_name": business_name,
        "cuit": cuit,
        "rubro": rubro,
        "email": email,
        "phone": phone,
        "province": province,
        "city": city,
        "message": message
    }
    cart = get_cart_from_cookie(request)
    cart_total_items = sum(cart.values())
    try:
        rubro_enum = BusinessLine(rubro.upper()) if rubro.upper() in BusinessLine.__members__ else BusinessLine.AMBOS
        dto = SolicitudCuentaDTO(
            business_name=business_name,
            cuit=cuit,
            rubro=rubro_enum,
            email=email,
            phone=phone,
            province=province,
            city=city,
            message=message
        )
        prospecto = await container.solicitar_cuenta_uc.execute(dto)
        return templates.TemplateResponse(
            request=request,
            name="solicitar_cuenta.html",
            context={
                "current_user": None,
                "cart_total_items": cart_total_items,
                "enviado_ok": True,
                "prospecto": prospecto,
                "error": None,
                "form_data": None
            }
        )
    except (CustomerAlreadyExistsError, ValueError) as e:
        return templates.TemplateResponse(
            request=request,
            name="solicitar_cuenta.html",
            context={
                "current_user": None,
                "cart_total_items": cart_total_items,
                "enviado_ok": False,
                "error": str(e),
                "form_data": form_data
            },
            status_code=400
        )


@router.get("/demo-login")
@router.post("/demo-login")
async def demo_login():
    """Autentica al usuario en Modo Demo / Simulación Comercial con permisos B2B_CLIENT"""
    demo_customer = await container.auth_customer_uc.authenticate_demo()
    response = RedirectResponse(url="/", status_code=303)
    signed_cookie_val = sign_session_cookie(demo_customer.id)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=signed_cookie_val,
        httponly=True,
        samesite="lax",
        max_age=86400 * 7
    )
    return response


@router.get("/registro", response_class=HTMLResponse)
async def register_page(request: Request, current_user = Depends(get_current_user_from_cookie)):
    # Si no es ADMIN, se redirige a la vista comercial de solicitud de cuenta
    if not current_user or current_user.role != UserRole.ADMIN:
        return RedirectResponse(url="/solicitar-cuenta", status_code=303)
    cart = get_cart_from_cookie(request)
    cart_total_items = sum(cart.values())
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"current_user": current_user, "cart_total_items": cart_total_items}
    )


@router.post("/registro", response_class=HTMLResponse)
async def process_register(
    request: Request,
    business_name: str = Form(...),
    cuit: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    address: str = Form(...),
    city: str = Form(...),
    password: str = Form(...),
    current_user = Depends(get_current_user_from_cookie)
):
    # Proteger alta directa: solo permitida para administradores
    if not current_user or current_user.role != UserRole.ADMIN:
        return RedirectResponse(url="/solicitar-cuenta", status_code=303)

    cart = get_cart_from_cookie(request)
    cart_total_items = sum(cart.values())
    try:
        dto = RegisterB2BDTO(
            business_name=business_name,
            cuit=cuit,
            email=email,
            phone=phone,
            address=address,
            city=city,
            password=password
        )
        customer = await container.register_b2b_uc.execute(dto, requester=current_user.role)
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "success": f"Cliente {customer.business_name} dado de alta con éxito.",
                "current_user": current_user,
                "cart_total_items": cart_total_items
            }
        )
    except (CustomerAlreadyExistsError, UnauthorizedActionError, ValueError) as e:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "error": str(e),
                "current_user": current_user,
                "cart_total_items": cart_total_items
            },
            status_code=400
        )


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response


@router.get("/nosotros", response_class=HTMLResponse)
async def nosotros_page(request: Request, current_user = Depends(get_current_user_from_cookie)):
    cart = get_cart_from_cookie(request)
    cart_total_items = sum(cart.values())
    return templates.TemplateResponse(
        request=request,
        name="nosotros.html",
        context={"current_user": current_user, "cart_total_items": cart_total_items}
    )


@router.get("/contacto", response_class=HTMLResponse)
async def contacto_page(request: Request, current_user = Depends(get_current_user_from_cookie)):
    cart = get_cart_from_cookie(request)
    cart_total_items = sum(cart.values())
    return templates.TemplateResponse(
        request=request,
        name="contacto.html",
        context={
            "current_user": current_user,
            "cart_total_items": cart_total_items,
            "mensaje_enviado": False
        }
    )


@router.post("/contacto", response_class=HTMLResponse)
async def contacto_submit(
    request: Request,
    nombre: str = Form(...),
    email: str = Form(...),
    telefono: str = Form(...),
    rubro: str = Form("autopartes"),
    zona: str = Form("cuyo"),
    mensaje: str = Form(...),
    current_user = Depends(get_current_user_from_cookie)
):
    cart = get_cart_from_cookie(request)
    cart_total_items = sum(cart.values())
    # Formulario institucional procesado registrando zona comercial
    return templates.TemplateResponse(
        request=request,
        name="contacto.html",
        context={
            "current_user": current_user,
            "cart_total_items": cart_total_items,
            "mensaje_enviado": True
        }
    )


# =========================================================================
# PERFIL COMERCIAL Y CONTROL DE MARGEN DE GANANCIA (POSTA 6.2)
# =========================================================================

@router.get("/perfil", response_class=HTMLResponse)
async def perfil_page(
    request: Request,
    pedido_confirmado: str | None = None,
    wa_url: str | None = None,
    current_user = Depends(get_current_user_from_cookie)
):
    """Panel Comercial adaptativo: B2B_CLIENT (margen y pedidos), SALES_AGENT (cartera y pedidos cartera), ADMIN (gestión cartera)"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    cart = get_cart_from_cookie(request)
    cart_total_items = sum(cart.values())

    portfolio = []
    agent_orders = []
    sales_agents = []
    b2b_customers = []
    orders = []

    if current_user.role == UserRole.SALES_AGENT:
        portfolio = await container.manage_sales_agents_uc.get_portfolio(current_user.id)
        agent_orders = await container.order_repo.get_by_sales_agent(current_user.id)
    elif current_user.role == UserRole.ADMIN:
        sales_agents = await container.manage_sales_agents_uc.get_sales_agents()
        # Para el panel de asignación del Admin, listamos todos los clientes y los vendedores
        with container.customer_repo._session_factory() as session:
            from sqlalchemy import select
            from src.infrastructure.database.models.cliente_model import ClienteModel
            cust_models = session.scalars(select(ClienteModel).order_by(ClienteModel.razon_social.asc())).all()
            b2b_customers = [container.customer_repo._map_to_entity(m) for m in cust_models if m.rol == "b2b_client"]
    else:
        orders = await container.order_repo.get_by_customer(current_user.id)

    success_msg = None
    if pedido_confirmado:
        success_msg = f"¡Pedido {pedido_confirmado} registrado con éxito en nuestro sistema! Tu asesor comercial ya tiene asignada la preparación."

    return templates.TemplateResponse(
        request=request,
        name="perfil.html",
        context={
            "current_user": current_user,
            "cart_total_items": cart_total_items,
            "orders": orders,
            "portfolio": portfolio,
            "agent_orders": agent_orders,
            "sales_agents": sales_agents,
            "b2b_customers": b2b_customers,
            "success_msg": success_msg,
            "error_msg": None,
            "pedido_confirmado": pedido_confirmado,
            "wa_url": wa_url
        }
    )


@router.post("/admin/asignar-vendedor", response_class=HTMLResponse)
async def admin_asignar_vendedor(
    request: Request,
    customer_id: str = Form(...),
    sales_agent_id: str = Form(""),
    current_user = Depends(get_current_user_from_cookie)
):
    """Asignación/Reasignación dinámica de vendedor a cliente con respuesta reactiva HTMX (Solo ADMIN)"""
    if not current_user or current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Operación no autorizada. Requiere rol Administrador.")

    clean_agent_id = sales_agent_id.strip() if sales_agent_id and sales_agent_id.strip() else None

    try:
        dto = AssignSalesAgentDTO(customer_id=customer_id, sales_agent_id=clean_agent_id)
        await container.manage_sales_agents_uc.assign_agent(dto, requester_role=current_user.role)

        if clean_agent_id:
            agent = await container.customer_repo.get_by_id(clean_agent_id)
            agent_name = agent.business_name if agent else clean_agent_id
            return HTMLResponse(
                f'<span class="status-badge status-entregado" style="font-size: 0.78rem;">✓ Asignado a {agent_name}</span>'
            )
        else:
            return HTMLResponse(
                '<span class="status-badge status-pendiente" style="font-size: 0.78rem;">○ Sin Vendedor Asignado</span>'
            )
    except Exception as e:
        return HTMLResponse(
            f'<span class="status-badge status-cancelado" style="font-size: 0.78rem;">✕ Error: {str(e)}</span>',
            status_code=400
        )


@router.post("/perfil/margen", response_class=HTMLResponse)
async def perfil_actualizar_margen(
    request: Request,
    markup_percent: float = Form(...),
    current_user = Depends(get_current_user_from_cookie)
):
    """Actualiza el porcentaje de margen comercial para mostrador del cliente"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    cart = get_cart_from_cookie(request)
    cart_total_items = sum(cart.values())

    try:
        dto = UpdateProfileDTO(markup_percent=float(markup_percent))
        updated_customer = await container.update_profile_uc.execute(customer_id=current_user.id, dto=dto)
        current_user = updated_customer
        success_msg = f"¡Margen de mostrador actualizado al {markup_percent}%! Los precios del catálogo ahora se calculan con esta rentabilidad."
        error_msg = None
    except ValueError as e:
        success_msg = None
        error_msg = str(e)

    portfolio = []
    agent_orders = []
    sales_agents = []
    b2b_customers = []
    orders = []

    if current_user.role == UserRole.SALES_AGENT:
        portfolio = await container.manage_sales_agents_uc.get_portfolio(current_user.id)
        agent_orders = await container.order_repo.get_by_sales_agent(current_user.id)
    elif current_user.role == UserRole.ADMIN:
        sales_agents = await container.manage_sales_agents_uc.get_sales_agents()
    else:
        orders = await container.order_repo.get_by_customer(current_user.id)

    return templates.TemplateResponse(
        request=request,
        name="perfil.html",
        context={
            "current_user": current_user,
            "cart_total_items": cart_total_items,
            "orders": orders,
            "portfolio": portfolio,
            "agent_orders": agent_orders,
            "sales_agents": sales_agents,
            "b2b_customers": b2b_customers,
            "success_msg": success_msg,
            "error_msg": error_msg
        }
    )


# =========================================================================
# CARRITO DE COMPRAS B2B Y PEDIDOS MAYORISTAS
# =========================================================================

@router.post("/carrito/agregar")
async def cart_add_item(
    request: Request,
    product_id: str = Form(...),
    cantidad: int = Form(1)
):
    """Agrega o incrementa un artículo en el carrito y retorna el badge HTML actualizado"""
    cart = get_cart_from_cookie(request)
    current_qty = cart.get(str(product_id), 0)
    new_qty = current_qty + max(1, cantidad)
    cart[str(product_id)] = new_qty

    total_items = sum(cart.values())
    response = HTMLResponse(
        content=f'<span id="cart-badge" class="cart-badge">{total_items}</span>',
        status_code=200
    )
    cookie_val = encode_cart_cookie(cart)
    response.set_cookie(
        key=CART_COOKIE_NAME,
        value=cookie_val,
        httponly=True,
        samesite="lax",
        max_age=86400 * 14
    )
    return response


@router.post("/carrito/actualizar")
async def cart_update_item(
    request: Request,
    product_id: str = Form(...),
    cantidad: int = Form(...)
):
    """Actualiza la cantidad de un artículo. Si es <= 0, lo elimina."""
    cart = get_cart_from_cookie(request)
    pid = str(product_id)
    if cantidad <= 0:
        cart.pop(pid, None)
    else:
        cart[pid] = cantidad

    response = RedirectResponse(url="/carrito", status_code=303)
    cookie_val = encode_cart_cookie(cart)
    response.set_cookie(
        key=CART_COOKIE_NAME,
        value=cookie_val,
        httponly=True,
        samesite="lax",
        max_age=86400 * 14
    )
    return response


@router.post("/carrito/eliminar")
async def cart_remove_item(
    request: Request,
    product_id: str = Form(...)
):
    """Elimina completamente un artículo del carrito"""
    cart = get_cart_from_cookie(request)
    cart.pop(str(product_id), None)

    response = RedirectResponse(url="/carrito", status_code=303)
    cookie_val = encode_cart_cookie(cart)
    response.set_cookie(
        key=CART_COOKIE_NAME,
        value=cookie_val,
        httponly=True,
        samesite="lax",
        max_age=86400 * 14
    )
    return response


@router.get("/carrito", response_class=HTMLResponse)
async def cart_view(
    request: Request,
    current_user = Depends(get_current_user_from_cookie)
):
    """Vista completa del pedido mayorista, simulador de despacho y flete y totalizador"""
    cart = get_cart_from_cookie(request)
    role = current_user.role if current_user else UserRole.PUBLIC
    is_b2b = role in (UserRole.B2B_CLIENT, UserRole.SALES_AGENT, UserRole.ADMIN)

    cart_items = []
    subtotal_amount = 0.0

    product_ids = list(cart.keys())
    if product_ids:
        products = await container.get_product_detail_uc.get_many(product_ids)
        for prod in products:
            # Resolver la cantidad usando el ID del producto o su SKU como fallback
            qty = cart.get(str(prod.id), cart.get(prod.sku, 1))
            price_vo = prod.calculate_price_for_role(role)
            item_subtotal = price_vo.amount * qty
            subtotal_amount += item_subtotal

            # Formatear precio
            unit_price_ars = price_vo.format_ars()
            subtotal_ars = f"$ {item_subtotal:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            cart_items.append({
                "product": prod,
                "quantity": qty,
                "unit_price_ars": unit_price_ars,
                "unit_price_amount": price_vo.amount,
                "subtotal_ars": subtotal_ars,
                "subtotal_amount": item_subtotal
            })

    # Cálculo económico: Subtotal Neto, IVA 21% y Total estimado
    iva_amount = subtotal_amount * 0.21
    total_amount = subtotal_amount + iva_amount

    subtotal_formatted = f"$ {subtotal_amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    iva_formatted = f"$ {iva_amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    total_formatted = f"$ {total_amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    cart_total_items = sum(cart.values())

    return templates.TemplateResponse(
        request=request,
        name="cart.html",
        context={
            "cart_items": cart_items,
            "cart_total_items": cart_total_items,
            "subtotal_ars": subtotal_formatted,
            "iva_ars": iva_formatted,
            "total_ars": total_formatted,
            "current_user": current_user,
            "is_b2b": is_b2b
        }
    )


@router.post("/carrito/confirmar")
async def cart_confirm_order(
    request: Request,
    dest_zone: str = Form("resto"),
    notes: str = Form(""),
    current_user = Depends(get_current_user_from_cookie)
):
    """
    Checkout Real del Carrito B2B:
    1. Si no hay usuario logueado, redirige a /login?redirect=/carrito
    2. Si el carrito está vacío, redirige a /carrito
    3. Construye y ejecuta CreateOrderDTO en container.create_order_uc
    4. Limpia la cookie del carrito dejándolo vacío (badge en 0)
    5. Retorna JSON o Redirect a /perfil con los datos de orden y URL oficial de WhatsApp
    """
    if not current_user:
        return RedirectResponse(url="/login?redirect=/carrito", status_code=303)

    cart = get_cart_from_cookie(request)
    if not cart:
        return RedirectResponse(url="/carrito", status_code=303)

    # Mapeo de zona comercial a texto y teléfono oficial
    shipping_info = {
        "cuyo": {
            "name": "Mendoza / San Luis (Cuyo)",
            "phone": "5492612629209"
        },
        "resto": {
            "name": "Otras Provincias / Resto del País (Expreso)",
            "phone": "5492625468732"
        },
        "deposito": {
            "name": "Retiro en Depósito Warnes (CABA)",
            "phone": "5492612629209"
        }
    }
    zone_data = shipping_info.get(dest_zone.lower(), shipping_info["resto"])
    full_notes = f"Destino: {zone_data['name']}. {notes.strip()}".strip()

    items_dto = [OrderItemInputDTO(product_id=str(pid), quantity=int(qty)) for pid, qty in cart.items()]
    order_dto = CreateOrderDTO(
        customer_id=current_user.id,
        items=items_dto,
        notes=full_notes
    )

    try:
        created_order = await container.create_order_uc.execute(order_dto)
    except Exception as e:
        # En caso de error de stock o producto, recargar carrito con error
        return RedirectResponse(url=f"/carrito?error={urllib.parse.quote(str(e))}", status_code=303)

    # Armar mensaje preformateado de WhatsApp con el N° de Orden oficial
    total_formatted = created_order.total.format_ars()
    msg_lines = [
        f"Hola Atuel Gomas, acabo de confirmar mi pedido mayorista a través del portal web:",
        f"",
        f"📋 *N° de Pedido:* {created_order.id}",
        f"🏢 *Cliente:* {current_user.business_name} (CUIT: {current_user.cuit.value if current_user.cuit else 'N/A'})",
        f"📍 *Destino / Logística:* {zone_data['name']}",
        f"",
        f"📦 *Artículos solicitados:*"
    ]
    for idx, item in enumerate(created_order.items, 1):
        msg_lines.append(f"{idx}. [{item.product_sku or 'S/C'}] {item.product_name} x {item.quantity}u ({item.subtotal.format_ars()})")

    msg_lines.append(f"")
    msg_lines.append(f"💰 *Total Cotizado:* {total_formatted}")
    msg_lines.append(f"")
    msg_lines.append(f"Quedo a la espera de la confirmación de stock físico y despacho. ¡Muchas gracias!")

    whatsapp_text = urllib.parse.quote("\n".join(msg_lines))
    whatsapp_url = f"https://wa.me/{zone_data['phone']}?text={whatsapp_text}"

    # Soporte para peticiones AJAX / fetch
    accept_header = request.headers.get("accept", "")
    is_json = "application/json" in accept_header or request.headers.get("x-requested-with") == "XMLHttpRequest"

    empty_cart_cookie = encode_cart_cookie({})

    if is_json:
        from fastapi.responses import JSONResponse
        res = JSONResponse({
            "success": True,
            "order_id": created_order.id,
            "whatsapp_url": whatsapp_url,
            "redirect_url": f"/perfil?pedido_confirmado={created_order.id}"
        })
    else:
        # Si fue un submit tradicional de formulario HTML, redirigir a /perfil
        res = RedirectResponse(
            url=f"/perfil?pedido_confirmado={created_order.id}&wa_url={urllib.parse.quote(whatsapp_url)}",
            status_code=303
        )

    # Limpiar cookie del carrito
    res.set_cookie(
        key=CART_COOKIE_NAME,
        value=empty_cart_cookie,
        httponly=True,
        samesite="lax",
        max_age=86400 * 14
    )
    return res


