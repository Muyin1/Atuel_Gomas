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


from src.domain.entities.business_line import BusinessLine
from src.domain.entities.category_item import CategoryItem
from src.domain.entities.customer import Customer


def test_business_line_and_category_item():
    assert BusinessLine.AUTOPARTES == 'AUTOPARTES'
    assert BusinessLine.FERRETERIA == 'FERRETERIA'
    assert BusinessLine.AMBOS == 'AMBOS'

    cat = CategoryItem(
        id=1,
        name='mangueras-automotor',
        value='Mangueras Automotor',
        slug='mangueras-automotor',
        rubro=BusinessLine.AUTOPARTES,
        product_count=9623
    )
    assert cat.product_count == 9623
    assert cat.rubro == BusinessLine.AUTOPARTES
    assert cat == 'Mangueras Automotor'
    assert cat == 'mangueras-automotor'

    cust = Customer(
        id='c1',
        email='test@atuel.com',
        business_name='Repuestos Warnes',
        cuit=CUIT('30712345678'),
        phone='1123456789',
        address='Warnes 1234',
        city='CABA',
        business_line=BusinessLine.AUTOPARTES
    )
    assert cust.business_line == BusinessLine.AUTOPARTES


from src.domain.entities.family_item import FamilyItem


def test_family_item_entity():
    fam = FamilyItem(
        id=43,
        name='mangueras-radiador',
        value='Mangueras de Radiador',
        slug='mangueras-radiador',
        category_id=1,
        category_name='Mangueras Automotor',
        rubro=BusinessLine.AUTOPARTES,
        product_count=4660
    )
    assert fam.id == 43
    assert fam.value == 'Mangueras de Radiador'
    assert fam.category_name == 'Mangueras Automotor'
    assert fam.rubro == BusinessLine.AUTOPARTES
    assert fam.product_count == 4660
    assert fam == 'Mangueras de Radiador'
    assert fam == 'mangueras-radiador'
