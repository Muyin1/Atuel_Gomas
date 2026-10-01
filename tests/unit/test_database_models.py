import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session
from src.infrastructure.database.connection import init_db
from src.infrastructure.database.models import (
    CategoriaModel,
    FamiliaModel,
    TalleModel,
    ColorModel,
    MaterialModel,
    PunteraModel,
    ProductoModel,
    VarianteModel,
    CompatibilidadVehicularModel,
    ClienteModel,
    OrdenModel,
    OrdenItemModel,
)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    with Session(engine) as session:
        yield session


def test_tables_created_successfully(db_session):
    engine = db_session.get_bind()
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    expected_tables = {
        "categorias",
        "familias",
        "talles_medidas",
        "colores",
        "materiales",
        "punteras_seguridad",
        "productos",
        "producto_variantes",
        "producto_compatibilidad_vehicular",
        "clientes",
        "ordenes",
        "orden_items",
    }

    assert expected_tables.issubset(set(table_names))


def test_create_product_with_variants_and_compatibility(db_session):
    cat = CategoriaModel(nombre="Mangueras Automotor", slug="mangueras-automotor")
    fam = FamiliaModel(nombre="Mangueras Radiador", categoria=cat)
    prod = ProductoModel(
        sku="AG-1001",
        nombre="Manguera Superior Radiador",
        categoria=cat,
        familia=fam,
        precio_base=15000.0,
        precio_mayorista_b2b=10000.0,
        stock=25,
    )
    talle = TalleModel(valor="32mm")
    color = ColorModel(nombre="Negro")
    material = MaterialModel(nombre="EPDM Reforzado")
    puntera = PunteraModel(tipo_puntera="Sin puntera")

    var = VarianteModel(
        producto=prod,
        talle=talle,
        color=color,
        material=material,
        puntera=puntera,
        stock_variante=25,
    )
    compat = CompatibilidadVehicularModel(
        producto=prod,
        marca="Renault",
        modelo="Kangoo",
        motorizacion="1.6 16v K4M",
        anio_desde=2008,
        anio_hasta=2018,
    )

    db_session.add_all([cat, fam, prod, talle, color, material, puntera, var, compat])
    db_session.commit()

    assert prod.id is not None
    assert len(prod.variantes) == 1
    assert prod.variantes[0].material.nombre == "EPDM Reforzado"
    assert len(prod.compatibilidades) == 1
    assert prod.compatibilidades[0].modelo == "Kangoo"


def test_create_customer_and_order(db_session):
    cliente = ClienteModel(
        id="cust-uuid-001",
        email="ferreteria@ejemplo.com",
        razon_social="Ferretería Industrial SRL",
        cuit="30-71234567-8",
        hashed_password="hashed_pw_test",
        is_approved=True,
    )
    prod = ProductoModel(
        sku="EPP-BOT-01",
        nombre="Botín de Trabajo Cuero",
        precio_base=45000.0,
        precio_mayorista_b2b=32000.0,
        stock=10,
    )
    orden = OrdenModel(
        id="ORD-TEST-01",
        cliente=cliente,
        cliente_nombre="Ferretería Industrial SRL",
        total=64000.0,
        estado="APROBADA",
    )
    item = OrdenItemModel(
        orden=orden,
        producto=prod,
        producto_sku="EPP-BOT-01",
        producto_nombre="Botín de Trabajo Cuero",
        precio_unitario=32000.0,
        cantidad=2,
        subtotal=64000.0,
    )

    db_session.add_all([cliente, prod, orden, item])
    db_session.commit()

    assert cliente.id == "cust-uuid-001"
    assert len(cliente.ordenes) == 1
    assert cliente.ordenes[0].id == "ORD-TEST-01"
    assert len(orden.items) == 1
    assert orden.items[0].subtotal == 64000.0
