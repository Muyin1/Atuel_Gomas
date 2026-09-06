"""
Contenedor central de Inyección de Dependencias (IoC Container).
Permite instanciar Use Cases conectando los Adaptadores correspondientes sin acoplamiento.
"""
from src.adapters.repositories.product_repo import MemoryProductRepository
from src.adapters.repositories.customer_repository import MemoryCustomerRepository
from src.adapters.repositories.order_repository import MemoryOrderRepository
from src.adapters.security.hasher import BcryptPasswordHasher
from src.application.use_cases.search_products import SearchProductsUseCase
from src.application.use_cases.get_product_detail import GetProductDetailUseCase
from src.application.use_cases.register_b2b_customer import RegisterB2BCustomerUseCase
from src.application.use_cases.authenticate_customer import AuthenticateCustomerUseCase
from src.application.use_cases.create_order import CreateOrderUseCase


class Container:
    def __init__(self):
        # Repositorios (Adaptadores)
        self.product_repo = MemoryProductRepository()
        self.customer_repo = MemoryCustomerRepository()
        self.order_repo = MemoryOrderRepository()
        self.hasher = BcryptPasswordHasher()

        # Casos de Uso (Aplicación)
        self.search_products_uc = SearchProductsUseCase(self.product_repo)
        self.get_product_detail_uc = GetProductDetailUseCase(self.product_repo)
        self.register_b2b_uc = RegisterB2BCustomerUseCase(self.customer_repo, self.hasher)
        self.auth_customer_uc = AuthenticateCustomerUseCase(self.customer_repo, self.hasher)
        self.create_order_uc = CreateOrderUseCase(self.order_repo, self.product_repo, self.customer_repo)


container = Container()
