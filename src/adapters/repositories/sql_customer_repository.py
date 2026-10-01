from __future__ import annotations

import re
from sqlalchemy import func, or_, select

from src.application.ports.customer_repository import ICustomerRepository
from src.domain.entities.customer import Customer
from src.domain.entities.user_role import UserRole
from src.domain.entities.business_line import BusinessLine
from src.domain.value_objects.cuit import CUIT
from src.infrastructure.database.connection import SessionLocal
from src.infrastructure.database.models import ClienteModel


def _normalize_role(role_val: str | None) -> UserRole:
    if not role_val:
        return UserRole.B2B_CLIENT
    clean = role_val.strip().upper()
    try:
        return UserRole(clean)
    except ValueError:
        if "ADMIN" in clean:
            return UserRole.ADMIN
        if "SALES" in clean or "VENTAS" in clean:
            return UserRole.SALES_AGENT
        return UserRole.B2B_CLIENT


def _normalize_business_line(bl_val: str | None) -> BusinessLine:
    if not bl_val:
        return BusinessLine.AMBOS
    clean = bl_val.strip().upper()
    try:
        return BusinessLine(clean)
    except ValueError:
        return BusinessLine.AMBOS


def _clean_cuit(cuit_str: str) -> str:
    return re.sub(r"[^\d]", "", cuit_str)


class SqlAlchemyCustomerRepository(ICustomerRepository):
    """
    Repositorio de infraestructura para clientes comerciales B2B y administradores.
    Implementa ICustomerRepository con conexión persistente a SQLAlchemy 2.0 y mapeo CUIT / UserRole / BusinessLine.
    """

    def __init__(self, session_factory=SessionLocal):
        self._session_factory = session_factory

    def _map_to_entity(self, model: ClienteModel) -> Customer:
        bl = getattr(model, "rubro", "AMBOS")
        return Customer(
            id=model.id,
            email=model.email,
            business_name=model.razon_social,
            cuit=CUIT(model.cuit),
            phone=model.telefono or "",
            address=model.direccion or "",
            city=model.ciudad or "",
            role=_normalize_role(model.rol),
            business_line=_normalize_business_line(bl),
            is_approved=bool(model.is_approved),
            hashed_password=model.hashed_password,
            created_at=model.created_at,
        )

    async def get_by_id(self, customer_id: str) -> Customer | None:
        with self._session_factory() as session:
            model = session.get(ClienteModel, customer_id)
            if not model:
                return None
            return self._map_to_entity(model)

    async def get_by_cuit(self, cuit_str: str) -> Customer | None:
        raw_clean = _clean_cuit(cuit_str)
        with self._session_factory() as session:
            # Buscar coincidencia exacta formateada o coincidencia por dígitos
            models = session.scalars(select(ClienteModel)).all()
            for m in models:
                if m.cuit == cuit_str or _clean_cuit(m.cuit) == raw_clean:
                    return self._map_to_entity(m)
            return None

    async def get_by_email(self, email: str) -> Customer | None:
        clean_email = email.strip().lower()
        with self._session_factory() as session:
            stmt = select(ClienteModel).filter(func.lower(ClienteModel.email) == clean_email)
            model = session.scalars(stmt).first()
            if not model:
                return None
            return self._map_to_entity(model)

    async def save(self, customer: Customer) -> None:
        with self._session_factory() as session:
            model = session.get(ClienteModel, customer.id)
            role_str = customer.role.value.lower() if hasattr(customer.role, "value") else str(customer.role).lower()
            rubro_str = customer.business_line.value.upper() if hasattr(customer.business_line, "value") else str(customer.business_line).upper()

            if not model:
                model = ClienteModel(
                    id=customer.id,
                    email=customer.email.lower().strip(),
                    razon_social=customer.business_name,
                    cuit=customer.cuit.value,
                    telefono=customer.phone,
                    direccion=customer.address,
                    ciudad=customer.city,
                    rol=role_str,
                    rubro=rubro_str,
                    is_approved=customer.is_approved,
                    hashed_password=customer.hashed_password,
                    created_at=customer.created_at,
                )
                session.add(model)
            else:
                model.email = customer.email.lower().strip()
                model.razon_social = customer.business_name
                model.cuit = customer.cuit.value
                model.telefono = customer.phone
                model.direccion = customer.address
                model.ciudad = customer.city
                model.rol = role_str
                model.rubro = rubro_str
                model.is_approved = customer.is_approved
                model.hashed_password = customer.hashed_password

            session.commit()
