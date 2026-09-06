from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.infrastructure.config.container import container
from src.application.dtos.product_dto import ProductSearchDTO
from src.application.dtos.auth_dto import RegisterB2BDTO, LoginDTO
from src.domain.entities.product_category import ProductCategory
from src.domain.entities.user_role import UserRole
from src.domain.exceptions.domain_exceptions import (
    CustomerAlreadyExistsError,
    InvalidCustomerCredentialsError
)

router = APIRouter()
templates = Jinja2Templates(directory="src/infrastructure/templates")


async def get_current_user_from_cookie(request: Request):
    """Adaptador de seguridad para obtener el usuario autenticado desde la cookie de sesión"""
    customer_id = request.cookies.get("b2b_session_user_id")
    if customer_id:
        customer = await container.customer_repo.get_by_id(customer_id)
        return customer
    return None


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, current_user = Depends(get_current_user_from_cookie)):
    role = current_user.role if current_user else UserRole.PUBLIC
    dto = ProductSearchDTO(role=role)
    products = await container.search_products_uc.execute(dto)
    categories = await container.product_repo.get_categories()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "products": products,
            "categories": categories,
            "current_user": current_user,
            "is_b2b": role in (UserRole.B2B_CLIENT, UserRole.SALES_AGENT, UserRole.ADMIN)
        }
    )


@router.get("/api/productos/search", response_class=HTMLResponse)
async def search_products_htmx(
    request: Request,
    query: str | None = None,
    category: str | None = None,
    vehicle_brand: str | None = None,
    vehicle_model: str | None = None,
    current_user = Depends(get_current_user_from_cookie)
):
    """Endpoint reactivo HTMX para filtrado instantáneo del catálogo"""
    role = current_user.role if current_user else UserRole.PUBLIC
    
    cat_enum = None
    if category and category.strip():
        try:
            cat_enum = ProductCategory[category.strip()]
        except KeyError:
            cat_enum = None

    dto = ProductSearchDTO(
        query=query if query and query.strip() else None,
        category=cat_enum,
        vehicle_brand=vehicle_brand if vehicle_brand and vehicle_brand.strip() else None,
        vehicle_model=vehicle_model if vehicle_model and vehicle_model.strip() else None,
        role=role
    )
    products = await container.search_products_uc.execute(dto)

    return templates.TemplateResponse(
        request=request,
        name="partials/product_grid.html",
        context={
            "products": products,
            "is_b2b": role in (UserRole.B2B_CLIENT, UserRole.SALES_AGENT, UserRole.ADMIN)
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
        response.set_cookie(
            key="b2b_session_user_id",
            value=customer.id,
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
        response.set_cookie(
            key="b2b_session_user_id",
            value=customer.id,
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
    response.delete_cookie("b2b_session_user_id")
    return response
