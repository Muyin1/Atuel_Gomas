from enum import Enum


class UserRole(str, Enum):
    PUBLIC = "PUBLIC"
    B2B_CLIENT = "B2B_CLIENT"     # Ferretería / Casa de Repuestos
    SALES_AGENT = "SALES_AGENT"   # Vendedor Atuel Gomas
    ADMIN = "ADMIN"               # Administrador total
