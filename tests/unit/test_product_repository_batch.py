import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.database.connection import init_db
from src.infrastructure.database.models import CategoriaModel, FamiliaModel, ProductoModel
from src.adapters.repositories.sql_product_repository import SqlAlchemyProductRepository
from src.application.use_cases.get_product_detail import GetProductDetailUseCase


@pytest.fixture
def sqlite_product_repo():
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    # Poblado inicial de prueba
    with session_factory() as session:
        cat = CategoriaModel(nombre="Mangueras Automotor", slug="mangueras-automotor")
        fam = FamiliaModel(nombre="Mangueras de Radiador", slug="mangueras-radiador", categoria=cat)

        p1 = ProductoModel(
            id=101,
            sku="AG-101",
            codigo_oem="OEM-101",
            nombre="Manguera Superior Radiador",
            categoria=cat,
            familia=fam,
            precio_base=15000.0,
            precio_mayorista_b2b=10500.0,
            stock=25,
            activo=True,
        )
        p2 = ProductoModel(
            id=102,
            sku="AG-102",
            codigo_oem="OEM-102",
            nombre="Manguera Inferior Radiador",
            categoria=cat,
            familia=fam,
            precio_base=18000.0,
            precio_mayorista_b2b=12600.0,
            stock=15,
            activo=True,
        )
        p3 = ProductoModel(
            id=103,
            sku="AG-103",
            codigo_oem="OEM-103",
            nombre="Manguera Calefacción",
            categoria=cat,
            familia=fam,
            precio_base=12000.0,
            precio_mayorista_b2b=8400.0,
            stock=30,
            activo=True,
        )
        session.add_all([cat, fam, p1, p2, p3])
        session.commit()

    return SqlAlchemyProductRepository(session_factory=session_factory)


@pytest.mark.asyncio
async def test_get_by_ids_batch_fetch_and_order_preservation(sqlite_product_repo):
    repo = sqlite_product_repo
    uc = GetProductDetailUseCase(repo)

    # 1. Recuperar múltiples productos por ID numérico en orden invertido
    products = await repo.get_by_ids(["103", "101"])
    assert len(products) == 2
    assert products[0].id == "103"
    assert products[0].sku == "AG-103"
    assert products[1].id == "101"
    assert products[1].sku == "AG-101"

    # 2. Recuperar por SKU mixto y código OEM
    mixed = await repo.get_by_ids(["OEM-102", "AG-103"])
    assert len(mixed) == 2
    assert mixed[0].id == "102"
    assert mixed[1].id == "103"

    # 3. Ignorar IDs inexistentes sin fallar
    with_invalid = await repo.get_by_ids(["999", "101", "INEXISTENTE"])
    assert len(with_invalid) == 1
    assert with_invalid[0].id == "101"

    # 4. Caso de lista vacía
    assert await repo.get_by_ids([]) == []

    # 5. Verificación a través del UseCase GetProductDetailUseCase.get_many
    uc_products = await uc.get_many(["102", "101", "103"])
    assert len(uc_products) == 3
    assert [p.id for p in uc_products] == ["102", "101", "103"]
