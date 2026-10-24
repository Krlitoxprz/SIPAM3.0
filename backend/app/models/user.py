from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime, Date, Float, Numeric, Index, CheckConstraint, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.database import Base


class RolEnum(str, enum.Enum):
    admin = "admin"
    estudiante = "estudiante"
    profesor = "profesor"
    jefe_programa = "jefe_programa"        # Jefe de Programa — aprueba solicitudes
    decano = "decano"                       # Decano de Facultad — imprime y envía a consejo


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=False)
    nombres = Column(String(150), nullable=False)
    apellidos = Column(String(150), nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    cedula = Column(String(20), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    rol = Column(Enum(RolEnum), nullable=False)
    is_active = Column(Boolean, default=True)
    promedio = Column(Numeric(4, 2), nullable=True)
    porcentaje_creditos = Column(Numeric(5, 2), nullable=True)
    programa = Column(String(150), nullable=True)
    sede = Column(String(100), nullable=True)
    telefono = Column(String(30), nullable=True)
    foto_url = Column(String(500), nullable=True)
    email_personal = Column(String(200), nullable=True)
    bio = Column(Text, nullable=True)
    fecha_nacimiento = Column(Date, nullable=True)
    ciudad = Column(String(100), nullable=True)
    linkedin_url = Column(String(300), nullable=True)
    github_url = Column(String(300), nullable=True)
    # Datos de seguridad social (AP-INF-FO-05)
    eps = Column(String(150), nullable=True)
    arl = Column(String(150), nullable=True)
    fondo_pensiones = Column(String(150), nullable=True)
    # Perfil docente (planta | ocasional | catedra | visitante)
    tipo_docente = Column(String(20), nullable=True)
    modalidad_docente = Column(String(10), nullable=True)  # TCP | TCO | CAT | MTP
    # Acuerdo 012/2023 Art.4.c — sanción disciplinaria
    sancionado_disciplinariamente = Column(Boolean, default=False, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            "promedio IS NULL OR (promedio >= 0 AND promedio <= 5)",
            name="ck_user_promedio",
        ),
        CheckConstraint(
            "porcentaje_creditos IS NULL OR (porcentaje_creditos >= 0 AND porcentaje_creditos <= 100)",
            name="ck_user_pct_creditos",
        ),
        Index("ix_users_rol", "rol"),
        Index("ix_users_programa", "programa"),
        Index("ix_users_sede", "sede"),
    )

    postulaciones = relationship("Postulacion", back_populates="estudiante", foreign_keys="Postulacion.estudiante_id")
    archivos = relationship("ArchivoAdjunto", back_populates="usuario")
