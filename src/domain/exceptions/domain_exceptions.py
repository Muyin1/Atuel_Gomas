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


class UnauthorizedActionError(DomainException):
    """Excepción lanzada cuando una operación requiere privilegios específicos (ej. ADMIN)"""
    pass

