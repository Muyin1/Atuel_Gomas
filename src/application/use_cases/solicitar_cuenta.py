import uuid
from src.application.dtos.solicitud_cuenta_dto import SolicitudCuentaDTO
from src.application.ports.customer_repository import ICustomerRepository
from src.domain.entities.customer import Customer
from src.domain.entities.user_role import UserRole
from src.domain.entities.business_line import BusinessLine
from src.domain.value_objects.cuit import CUIT
from src.domain.exceptions.domain_exceptions import CustomerAlreadyExistsError


class SolicitarCuentaUseCase:
    """
    Caso de uso para el registro de solicitudes de cuenta mayorista B2B (prospectos).
    Registra el cliente en estado pendiente (is_approved=False) para posterior revisión/aprobación por parte del administrador.
    Si ya existe un cliente con cuenta aprobada para el CUIT, se rechaza con error amigable.
    """

    def __init__(self, customer_repo: ICustomerRepository):
        self.customer_repo = customer_repo

    async def execute(self, dto: SolicitudCuentaDTO) -> Customer:
        # Validar formato y dígitos de CUIT
        cuit_vo = CUIT(dto.cuit)

        # Verificar si ya existe cliente con este CUIT
        existing_cuit = await self.customer_repo.get_by_cuit(cuit_vo.value)
        if existing_cuit:
            if existing_cuit.is_approved:
                raise CustomerAlreadyExistsError(
                    f"El CUIT {cuit_vo.value} ya posee una cuenta mayorista activa en Atuel Gomas. Por favor, inicie sesión."
                )
            else:
                raise CustomerAlreadyExistsError(
                    f"Ya existe una solicitud pendiente de aprobación para el CUIT {cuit_vo.value}. Nuestro equipo comercial se comunicará a la brevedad."
                )

        # Verificar si el email ya está en uso
        existing_email = await self.customer_repo.get_by_email(dto.email)
        if existing_email:
            if existing_email.is_approved:
                raise CustomerAlreadyExistsError(
                    f"El correo electrónico {dto.email} ya se encuentra registrado con una cuenta activa."
                )
            else:
                raise CustomerAlreadyExistsError(
                    f"Ya existe una solicitud pendiente asociada al correo {dto.email}."
                )

        # Componer ubicación y observaciones
        location_parts = [p for p in (dto.city.strip(), dto.province.strip()) if p]
        location_str = ", ".join(location_parts) if location_parts else dto.city.strip()

        # En dirección se puede almacenar mensaje o notas del prospecto si existen
        notes = f"Obs: {dto.message.strip()}" if dto.message.strip() else ""

        rubro_val = dto.rubro if isinstance(dto.rubro, BusinessLine) else BusinessLine(str(dto.rubro).upper())

        prospect = Customer(
            id=str(uuid.uuid4()),
            email=dto.email.strip().lower(),
            business_name=dto.business_name.strip(),
            cuit=cuit_vo,
            phone=dto.phone.strip(),
            address=notes,
            city=location_str,
            role=UserRole.B2B_CLIENT,
            business_line=rubro_val,
            is_approved=False,  # Prospecto pendiente de aprobación por el admin
            hashed_password=""
        )

        await self.customer_repo.save(prospect)
        return prospect
