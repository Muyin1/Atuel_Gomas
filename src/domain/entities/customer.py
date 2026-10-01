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
    created_at: datetime = field(default_factory=datetime.utcnow)
