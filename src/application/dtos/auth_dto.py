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
