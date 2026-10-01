import hmac
import hashlib
import os
import math
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.infrastructure.config.container import container
from src.application.dtos.product_dto import ProductSearchDTO, PaginatedProductsDTO
from src.application.dtos.auth_dto import RegisterB2BDTO, LoginDTO
from src.domain.entities.product_category import ProductCategory
from src.domain.entities.user_role import UserRole
from src.domain.entities.business_line import BusinessLine
from src.domain.exceptions.domain_exceptions import (
    CustomerAlreadyExistsError,
    InvalidCustomerCredentialsError
)

router = APIRouter()
templates = Jinja2Templates(directory="src/infrastructure/templates")

# Clave secreta para firma criptográfica de cookies de sesión
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "atuel_gomas_secret_session_key_2026_industrial").encode("utf-8")
SESSION_COOKIE_NAME = "b2b_session_user_id"
PAGE_SIZE_DEFAULT = 24


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

    dto = ProductSearchDTO(role=role, page=page, page_size=PAGE_SIZE_DEFAULT)
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

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "products": products,
            "paginated": paginated,
            "categories": all_categories,
            "families": initial_families,
            "current_user": current_user,
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

    dto = ProductSearchDTO(
        query=clean_query,
        category=clean_category,
        family=clean_family,
        vehicle_brand=clean_brand,
        vehicle_model=clean_model,
        role=role,
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
    price = product.calculate_price_for_role(role)

    return templates.TemplateResponse(
        request=request,
        name="product_detail.html",
        context={
            "product": product,
            "price": price,
            "current_user": current_user,
            "is_b2b": role in (UserRole.B2B_CLIENT, UserRole.SALES_AGENT, UserRole.ADMIN)
        }
    )


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, current_user = Depends(get_current_user_from_cookie)):
    if current_user:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(request=request, name="login.html", context={"current_user": None})


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
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": str(e), "current_user": None},
            status_code=400
        )


@router.get("/registro", response_class=HTMLResponse)
async def register_page(request: Request, current_user = Depends(get_current_user_from_cookie)):
    if current_user:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(request=request, name="register.html", context={"current_user": None})


@router.post("/registro", response_class=HTMLResponse)
async def process_register(
    request: Request,
    business_name: str = Form(...),
    cuit: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    address: str = Form(...),
    city: str = Form(...),
    password: str = Form(...)
):
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
        customer = await container.register_b2b_uc.execute(dto)
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
    except (CustomerAlreadyExistsError, ValueError) as e:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": str(e), "current_user": None},
            status_code=400
        )


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response


@router.get("/nosotros", response_class=HTMLResponse)
async def nosotros_page(request: Request, current_user = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse(
        request=request,
        name="nosotros.html",
        context={"current_user": current_user}
    )


@router.get("/contacto", response_class=HTMLResponse)
async def contacto_page(request: Request, current_user = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse(
        request=request,
        name="contacto.html",
        context={"current_user": current_user, "mensaje_enviado": False}
    )


@router.post("/contacto", response_class=HTMLResponse)
async def contacto_submit(
    request: Request,
    nombre: str = Form(...),
    email: str = Form(...),
    telefono: str = Form(...),
    rubro: str = Form("autopartes"),
    mensaje: str = Form(...),
    current_user = Depends(get_current_user_from_cookie)
):
    # Formulario institucional procesado
    return templates.TemplateResponse(
        request=request,
        name="contacto.html",
        context={"current_user": current_user, "mensaje_enviado": True}
    )

