class DomainException(Exception):
    """Excepción base de dominio"""
    pass


class ProductNotFoundError(DomainException):
    pass


class InsufficientStockError(DomainException):
    pass


class InvalidCustomerCredentialsError(DomainException):
    pass


class CustomerAlreadyExistsError(DomainException):
    pass
