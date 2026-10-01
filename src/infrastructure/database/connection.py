from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe
load_dotenv()

# Configuración de URL de Base de Datos (soporte para SQLite local y PostgreSQL en producción)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./atuel_gomas.db")

# Normalizar dialecto para PostgreSQL para asegurar el uso de psycopg2
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DATABASE_URL.startswith("postgresql://") and not DATABASE_URL.startswith("postgresql+"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

# Argumentos específicos por motor
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

# Motor SQLAlchemy 2.0
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    future=True
)

# Fábrica de sesiones
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    """Clase base declarativa para todos los modelos ORM de Atuel Gomas (SQLAlchemy 2.0)"""
    pass


def get_db() -> Generator[Session, None, None]:
    """Generador de sesiones para inyección de dependencias o contexto controlado"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Context manager para scripts y procesos fuera del ciclo de vida HTTP"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(target_engine=None) -> None:
    """
    Inicializa y crea todas las tablas físicas registradas en el catálogo de modelos.
    Garantiza la importación de todos los modelos antes de invocar create_all.
    """
    import src.infrastructure.database.models  # noqa: F401
    eng = target_engine or engine
    Base.metadata.create_all(bind=eng)


def drop_db(target_engine=None) -> None:
    """Elimina todas las tablas (útil para tests o reset controlado)"""
    eng = target_engine or engine
    Base.metadata.drop_all(bind=eng)


if __name__ == "__main__":
    print("Inicializando base de datos y creando tablas en:", DATABASE_URL)
    init_db()
    print("Todas las tablas físicas fueron creadas exitosamente.")
