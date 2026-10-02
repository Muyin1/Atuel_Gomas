from dataclasses import dataclass, field
from datetime import datetime
from src.domain.value_objects.cuit import CUIT
from src.domain.entities.user_role import UserRole
from src.domain.entities.business_line import BusinessLine


@dataclass
class Customer:
    id: str
    email: str
    business_name: str               # Razón social
    cuit: CUIT
    phone: str
    address: str
    city: str
    role: UserRole = UserRole.B2B_CLIENT
    business_line: BusinessLine = BusinessLine.AMBOS
    is_approved: bool = False        # Aprobación de cuenta mayorista por vendedor
    hashed_password: str = ""
    markup_percent: float = 30.0     # Margen de reventa comercial configurable (por defecto 30%)
    sales_agent_id: str | None = None # ID del vendedor asignado (rol SALES_AGENT)
    created_at: datetime = field(default_factory=datetime.utcnow)


