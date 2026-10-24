from sqlalchemy import Column, Integer, String, Enum, DateTime, Float, Numeric, ForeignKey, Text, Boolean, Index, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.database import Base


class EstadoPostulacionEnum(str, enum.Enum):
    pendiente = "pendiente"
    documentos_incompletos = "documentos_incompletos"
    en_revision = "en_revision"
    preseleccionado = "preseleccionado"
    seleccionado = "seleccionado"
    no_seleccionado = "no_seleccionado"
    desistido = "desistido"


class Postulacion(Base):
    __tablename__ = "postulaciones"

    id = Column(Integer, primary_key=True, index=True)
    convocatoria_id = Column(Integer, ForeignKey("convocatorias.id"), nullable=False)
    estudiante_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    estado = Column(Enum(EstadoPostulacionEnum), nullable=False, default=EstadoPostulacionEnum.pendiente)

    nota_asignatura = Column(Numeric(4, 2), nullable=True)
    promedio_estudiante = Column(Numeric(4, 2), nullable=True)
    nota_entrevista = Column(Numeric(4, 2), nullable=True)
    puntaje_final = Column(Numeric(6, 3), nullable=True)
    puesto = Column(Integer, nullable=True)

    carta_motivacion = Column(Text, nullable=True)
    fecha_postulacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_entrevista = Column(DateTime(timezone=True), nullable=True)
    fecha_evaluacion = Column(DateTime(timezone=True), nullable=True)
    observaciones_evaluador = Column(Text, nullable=True)

    documentos_completos = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("convocatoria_id", "estudiante_id", name="uq_postulacion"),
        CheckConstraint(
            "nota_asignatura IS NULL OR (nota_asignatura >= 0 AND nota_asignatura <= 5)",
            name="ck_postulacion_nota_asig",
        ),
        CheckConstraint(
            "nota_entrevista IS NULL OR (nota_entrevista >= 0 AND nota_entrevista <= 5)",
            name="ck_postulacion_nota_entrevista",
        ),
        CheckConstraint(
            "promedio_estudiante IS NULL OR (promedio_estudiante >= 0 AND promedio_estudiante <= 5)",
            name="ck_postulacion_promedio",
        ),
        Index("ix_postulaciones_convocatoria_estado", "convocatoria_id", "estado"),
        Index("ix_postulaciones_estudiante", "estudiante_id"),
    )

    convocatoria = relationship("Convocatoria", back_populates="postulaciones")
    estudiante = relationship("User", back_populates="postulaciones", foreign_keys=[estudiante_id])
    archivos = relationship("ArchivoAdjunto", back_populates="postulacion", cascade="all, delete-orphan")


class ArchivoAdjunto(Base):
    __tablename__ = "archivos_adjuntos"

    id = Column(Integer, primary_key=True, index=True)
    postulacion_id = Column(Integer, ForeignKey("postulaciones.id"), nullable=True)
    usuario_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tipo_documento = Column(String(50), nullable=False)
    nombre_original = Column(String(255), nullable=False)
    nombre_almacenado = Column(String(255), nullable=False, unique=True)
    ruta_archivo = Column(String(500), nullable=False)
    tamanio_bytes = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_archivos_postulacion", "postulacion_id"),
        Index("ix_archivos_usuario", "usuario_id"),
    )

    postulacion = relationship("Postulacion", back_populates="archivos")
    usuario = relationship("User", back_populates="archivos")
