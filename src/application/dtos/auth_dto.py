from pydantic import BaseModel, EmailStr


class RegisterB2BDTO(BaseModel):
    business_name: str
    cuit: str
    email: EmailStr
    phone: str
    address: str
    city: str
    password: str


class LoginDTO(BaseModel):
    cuit_or_email: str
    password: str


class CustomerDTO(BaseModel):
    id: str
    email: str
    business_name: str
    cuit: str
    phone: str
    address: str
    city: str
    role: str
    business_line: str
    is_approved: bool
    markup_percent: float = 30.0
    sales_agent_id: str | None = None


class UpdateProfileDTO(BaseModel):
    markup_percent: float
    phone: str | None = None
    address: str | None = None


class AssignSalesAgentDTO(BaseModel):
    customer_id: str
    sales_agent_id: str | None = None



