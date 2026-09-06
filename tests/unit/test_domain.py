import pytest
from src.domain.entities.product import Product
from src.domain.entities.product_category import ProductCategory
from src.domain.entities.user_role import UserRole
from src.domain.value_objects.dimensions import Dimensions
from src.domain.value_objects.money import Money
from src.domain.value_objects.cuit import CUIT


def test_money_validation_and_formatting():
    m = Money(15420.50)
    assert "15.420,50" in m.format_ars()

    with pytest.raises(ValueError):
        Money(-10.0)


def test_cuit_validation():
    valid_cuit = CUIT("30712345678")
    assert valid_cuit.value == "30-71234567-8"

    with pytest.raises(ValueError):
        CUIT("12345") # Menos de 11 dígitos


def test_product_price_tier_by_role():
    product = Product(
        id="P-01",
        sku="TEST-01",
        oem_code="OEM-01",
        name="Manguera de Radiador",
        category=ProductCategory.MANGUERAS_AUTOMOTOR,
        description="Prueba",
        dimensions=Dimensions(inner_diameter_mm=32.0),
        base_price=Money(20000.0),
        wholesale_price=Money(14000.0),
        stock=10,
        image_url="/test.png"
    )

    # Usuario público ve precio base
    assert product.calculate_price_for_role(UserRole.PUBLIC).amount == 20000.0

    # Usuario cliente B2B ve precio mayorista
    assert product.calculate_price_for_role(UserRole.B2B_CLIENT).amount == 14000.0

    # Administrador ve precio mayorista
    assert product.calculate_price_for_role(UserRole.ADMIN).amount == 14000.0
