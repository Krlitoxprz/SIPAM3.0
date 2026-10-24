from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime, Float, Numeric, ForeignKey, Text, Index, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.database import Base


class EstadoConvocatoriaEnum(str, enum.Enum):
    borrador = "borrador"
    abierta = "abierta"
    cerrada = "cerrada"
    en_evaluacion = "en_evaluacion"
    finalizada = "finalizada"


class TipoMonitoriaEnum(str, enum.Enum):
    nee = "nee"
    regimenes_especiales = "regimenes_especiales"
    academica_cursos = "academica_cursos"
    laboratorios = "laboratorios"
    tic = "tic"
    permanencia_graduacion = "permanencia_graduacion"
    deportiva = "deportiva"
    cultural = "cultural"
    biblioteca = "biblioteca"
    acreditacion = "acreditacion"
    investigacion = "investigacion"
    academica = "academica"  # legacy
    administrativa = "administrativa"  # legacy


class Convocatoria(Base):
    __tablename__ = "convocatorias"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(300), nullable=False)
    descripcion = Column(Text, nullable=True)
    asignatura_id = Column(Integer, ForeignKey("asignaturas.id"), nullable=False)
    profesor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tipo_monitoria = Column(Enum(TipoMonitoriaEnum), default=TipoMonitoriaEnum.academica_cursos)
    estado = Column(Enum(EstadoConvocatoriaEnum), default=EstadoConvocatoriaEnum.borrador)
    periodo_academico = Column(String(10), nullable=False)
    fecha_inicio_postulacion = Column(DateTime(timezone=True), nullable=False)
    fecha_fin_postulacion = Column(DateTime(timezone=True), nullable=False)
    num_monitores_requeridos = Column(Integer, default=1)
    horas_semana = Column(Integer, nullable=False)
    horas_semestre = Column(Integer, nullable=False)
    promedio_minimo = Column(Numeric(3, 2), default=3.50)
    creditos_minimo_pct = Column(Numeric(5, 2), default=30.00)
    descripcion_actividades = Column(Text, nullable=True)
    sede = Column(String(100), nullable=True)
    fecha_publicacion_resultados = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("promedio_minimo >= 0 AND promedio_minimo <= 5", name="ck_convocatoria_promedio"),
        CheckConstraint("horas_semana > 0", name="ck_convocatoria_horas_semana"),
        CheckConstraint("horas_semestre > 0", name="ck_convocatoria_horas_semestre"),
        CheckConstraint("num_monitores_requeridos > 0", name="ck_convocatoria_monitores"),
        Index("ix_convocatorias_estado", "estado"),
        Index("ix_convocatorias_periodo", "periodo_academico"),
        Index("ix_convocatorias_profesor", "profesor_id"),
        UniqueConstraint("asignatura_id", "periodo_academico", name="uq_convocatoria_asignatura_periodo"),
    )

    asignatura = relationship("Asignatura", back_populates="convocatorias")
    profesor = relationship("User", foreign_keys=[profesor_id])
    postulaciones = relationship("Postulacion", back_populates="convocatoria", cascade="all, delete-orphan")


class Asignatura(Base):
    __tablename__ = "asignaturas"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=False)
    nombre = Column(String(200), nullable=False)
    creditos = Column(Integer, nullable=False)
    programa = Column(String(150), nullable=False)
    facultad = Column(String(200), nullable=True)
    semestre = Column(Integer, nullable=False)
    profesor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    caracter_curso = Column(String(20), nullable=True)        # 'teorico' | 'teorico_practico'
    caracteristica_curso = Column(String(30), nullable=True)  # 'especifico' | 'facultad' | 'institucional' | 'componente_flexible'
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        CheckConstraint("creditos > 0", name="ck_asignatura_creditos"),
        CheckConstraint("semestre >= 1 AND semestre <= 12", name="ck_asignatura_semestre"),
        Index("ix_asignaturas_programa", "programa"),
        Index("ix_asignaturas_profesor", "profesor_id"),
    )

    convocatorias = relationship("Convocatoria", back_populates="asignatura")
    profesor = relationship("User", foreign_keys=[profesor_id])
    matriculas = relationship("AsignaturaEstudiante", back_populates="asignatura")


class MonitoriaPlantilla(Base):
    """Catálogo institucional de monitorías por asignatura/programa (Acuerdo 012/2023 Art. 3)."""
    __tablename__ = "monitoria_plantillas"

    id = Column(Integer, primary_key=True, index=True)
    nombre_sugerido = Column(String(400), nullable=False)
    programa = Column(String(200), nullable=True)
    asignatura_id = Column(Integer, ForeignKey("asignaturas.id"), nullable=True)
    asignatura_nombre = Column(String(300), nullable=False)
    tipo_monitoria = Column(Enum(TipoMonitoriaEnum), nullable=False, default=TipoMonitoriaEnum.academica_cursos)
    descripcion_actividades = Column(Text, nullable=True)
    horas_semana = Column(Integer, nullable=False, default=8)
    horas_semestre = Column(Integer, nullable=False, default=128)
    promedio_minimo = Column(Numeric(3, 2), nullable=False, default=3.50)
    creditos_minimo_pct = Column(Numeric(5, 2), nullable=False, default=30.00)
    num_monitores_sugerido = Column(Integer, nullable=False, default=1)
    semestre_asignatura = Column(Integer, nullable=True)
    creditos_asignatura = Column(Integer, nullable=True)
    caracter_curso = Column(String(30), nullable=True)

    __table_args__ = (
        Index("ix_monitoria_plantillas_programa", "programa"),
        Index("ix_monitoria_plantillas_asig", "asignatura_id"),
    )

    asignatura_rel = relationship("Asignatura", foreign_keys=[asignatura_id])


class AsignaturaEstudiante(Base):
    """Matrículas — qué estudiantes están inscritos en cada asignatura."""
    __tablename__ = "asignatura_estudiantes"

    id = Column(Integer, primary_key=True, index=True)
    asignatura_id = Column(Integer, ForeignKey("asignaturas.id"), nullable=False)
    estudiante_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    periodo_academico = Column(String(10), nullable=False, default="2026-1")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("asignatura_id", "estudiante_id", "periodo_academico", name="uq_matricula"),
        Index("ix_matriculas_estudiante", "estudiante_id"),
    )

    asignatura = relationship("Asignatura", back_populates="matriculas")
    estudiante = relationship("User", foreign_keys=[estudiante_id])
