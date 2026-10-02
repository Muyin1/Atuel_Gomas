"""
Contenedor central de Inyección de Dependencias (IoC Container).
Permite instanciar Use Cases conectando los Adaptadores correspondientes sin acoplamiento.
"""
from src.adapters.repositories.sql_product_repository import SqlAlchemyProductRepository
from src.adapters.repositories.sql_customer_repository import SqlAlchemyCustomerRepository
from src.adapters.repositories.sql_order_repository import SqlAlchemyOrderRepository
from src.adapters.security.hasher import BcryptPasswordHasher
from src.application.use_cases.search_products import SearchProductsUseCase
from src.application.use_cases.get_product_detail import GetProductDetailUseCase
from src.application.use_cases.register_b2b_customer import RegisterB2BCustomerUseCase
from src.application.use_cases.authenticate_customer import AuthenticateCustomerUseCase
from src.application.use_cases.create_order import CreateOrderUseCase
from src.application.use_cases.solicitar_cuenta import SolicitarCuentaUseCase
from src.application.use_cases.update_customer_profile import UpdateCustomerProfileUseCase
from src.application.use_cases.manage_sales_agents import ManageSalesAgentUseCase


class Container:
    def __init__(self):
        # Repositorios (Adaptadores Persistentes SQLAlchemy 2.0)
        self.product_repo = SqlAlchemyProductRepository()
        self.customer_repo = SqlAlchemyCustomerRepository()
        self.order_repo = SqlAlchemyOrderRepository()
        self.hasher = BcryptPasswordHasher()

        # Casos de Uso (Aplicación)
        self.search_products_uc = SearchProductsUseCase(self.product_repo)
        self.get_product_detail_uc = GetProductDetailUseCase(self.product_repo)
        self.register_b2b_uc = RegisterB2BCustomerUseCase(self.customer_repo, self.hasher)
        self.solicitar_cuenta_uc = SolicitarCuentaUseCase(self.customer_repo)
        self.auth_customer_uc = AuthenticateCustomerUseCase(self.customer_repo, self.hasher)
        self.create_order_uc = CreateOrderUseCase(self.order_repo, self.product_repo, self.customer_repo)
        self.update_profile_uc = UpdateCustomerProfileUseCase(self.customer_repo)
        self.manage_sales_agents_uc = ManageSalesAgentUseCase(self.customer_repo)



container = Container()


