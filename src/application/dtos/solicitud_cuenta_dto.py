from pydantic import BaseModel, EmailStr
from src.domain.entities.business_line import BusinessLine


class SolicitudCuentaDTO(BaseModel):
    business_name: str
    cuit: str
    rubro: BusinessLine = BusinessLine.AMBOS
    email: EmailStr
    phone: str
    province: str = ""
    city: str = ""
    message: str = ""
