from sqlalchemy import Column, Integer, String, Enum, DateTime, Float, Numeric, ForeignKey, Text, Boolean, Date, Time, Index, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.database import Base


class TipoDocenteEnum(str, enum.Enum):
    catedra = "catedra"
    planta = "planta"
    ocasional = "ocasional"
    visitante = "visitante"


class CaracterCursoEnum(str, enum.Enum):
    teorico = "teorico"
    teorico_practico = "teorico_practico"


class CaracteristicaCursoEnum(str, enum.Enum):
    especifico = "especifico"
    facultad = "facultad"
    institucional = "institucional"
    componente_flexible = "componente_flexible"


class ModalidadDocenteEnum(str, enum.Enum):
    TCP = "TCP"
    TCO = "TCO"
    MTP = "MTP"
    MTO = "MTO"
    CAT = "CAT"


class EstadoPracticaEnum(str, enum.Enum):
    borrador = "borrador"
    solicitada = "solicitada"
    pendiente_quorum = "pendiente_quorum"
    aprobada_curriculo = "aprobada_curriculo"   # jefe_programa → pasa a decano
    aprobada_facultad = "aprobada_facultad"     # decano → pasa a admin/Vicerrectoría
    aprobado_transporte = "aprobado_transporte" # admin aprueba final
    en_ejecucion = "en_ejecucion"
    finalizada = "finalizada"
    rechazada = "rechazada"


class Practica(Base):
    __tablename__ = "practicas"

    id = Column(Integer, primary_key=True, index=True)
    nombre_practica = Column(String(300), nullable=False)
    asignatura_id = Column(Integer, ForeignKey("asignaturas.id"), nullable=False)
    profesor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    estado = Column(Enum(EstadoPracticaEnum), nullable=False, default=EstadoPracticaEnum.borrador)
    periodo_academico = Column(String(10), nullable=False)
    fecha_inicio = Column(DateTime(timezone=True), nullable=False)
    fecha_fin = Column(DateTime(timezone=True), nullable=False)
    duracion_dias = Column(Integer, nullable=False)
    num_alumnos = Column(Integer, nullable=False)
    total_firmas_requeridas = Column(Integer, nullable=True)
    total_firmas_obtenidas = Column(Integer, default=0)
    quorum_alcanzado = Column(Boolean, default=False)
    tipo_docente = Column(Enum(TipoDocenteEnum), nullable=True)
    observaciones = Column(Text, nullable=True)
    observaciones_jefe = Column(Text, nullable=True)  # motivo de rechazo o comentarios del jefe
    # Campos FO-16 Justificación Práctica Extramuros
    caracter_curso = Column(String(30), nullable=True)          # teorico | teorico_practico
    caracteristica_curso = Column(String(30), nullable=True)    # especifico | facultad | institucional | componente_flexible
    modalidad_docente = Column(String(10), nullable=True)       # TCP | TCO | MTP | MTO | CAT
    hora_salida = Column(String(5), nullable=True)              # HH:MM
    hora_llegada = Column(String(5), nullable=True)             # HH:MM
    articulacion_curso = Column(Text, nullable=True)            # articulación con área del curso y evaluación
    descripcion_practica = Column(Text, nullable=True)          # descripción detallada
    evaluacion = Column(Text, nullable=True)                    # criterios de evaluación
    # Acuerdo 003/2012 Art.3.e y Art.3.l
    justificacion = Column(Text, nullable=True)                 # justificación de la práctica (Art.3.e)
    metodologia = Column(Text, nullable=True)                   # metodología de la práctica (Art.3.e)
    carta_autorizacion_empresa = Column(Text, nullable=True)    # carta de autorización empresa (Art.3.l)
    # Acuerdo 003/2012 Art.7 — Informe post-práctica
    informe_resultados = Column(Text, nullable=True)
    fecha_informe = Column(DateTime(timezone=True), nullable=True)
    # AP-INF-FO-05 — Solicitud de desplazamiento vial
    placa_vehiculo = Column(String(20), nullable=True)
    tipo_vehiculo = Column(String(50), nullable=True)
    empresa_transporte = Column(String(200), nullable=True)
    conductor_nombre = Column(String(200), nullable=True)
    sede = Column(String(100), nullable=True)               # sede universitaria (FO-05, FO-15)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("num_alumnos > 0", name="ck_practica_num_alumnos"),
        CheckConstraint("duracion_dias > 0", name="ck_practica_duracion"),
        CheckConstraint("fecha_fin >= fecha_inicio", name="ck_practica_fechas"),
        Index("ix_practicas_estado", "estado"),
        Index("ix_practicas_periodo_profesor", "periodo_academico", "profesor_id"),
        Index("ix_practicas_asignatura", "asignatura_id"),
        Index("ix_practicas_profesor", "profesor_id"),
    )

    asignatura = relationship("Asignatura")
    profesor = relationship("User", foreign_keys=[profesor_id])
    rutas = relationship("RutaPractica", back_populates="practica", cascade="all, delete-orphan")
    firmas = relationship("FirmaConsentimiento", back_populates="practica", cascade="all, delete-orphan")
    viaticos = relationship("Viatico", back_populates="practica", cascade="all, delete-orphan")


class RutaPractica(Base):
    __tablename__ = "rutas_practica"

    id = Column(Integer, primary_key=True, index=True)
    practica_id = Column(Integer, ForeignKey("practicas.id"), nullable=False)
    orden = Column(Integer, nullable=False)
    tipo_punto = Column(String(20), nullable=False)
    lugar = Column(String(300), nullable=False)
    municipio = Column(String(150), nullable=True)
    departamento = Column(String(150), nullable=True)
    distancia_km = Column(Numeric(8, 3), nullable=True)
    vereda = Column(String(200), nullable=True)
    es_rural = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("practica_id", "orden", name="uq_ruta_orden"),
        Index("ix_rutas_practica", "practica_id"),
    )

    practica = relationship("Practica", back_populates="rutas")


class FirmaConsentimiento(Base):
    __tablename__ = "firmas_consentimiento"

    id = Column(Integer, primary_key=True, index=True)
    practica_id = Column(Integer, ForeignKey("practicas.id"), nullable=False)
    estudiante_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    signed_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("practica_id", "estudiante_id", name="uq_firma_practica"),
        Index("ix_firmas_practica", "practica_id"),
        Index("ix_firmas_estudiante", "estudiante_id"),
    )

    practica = relationship("Practica", back_populates="firmas")
    estudiante = relationship("User", foreign_keys=[estudiante_id])


class TarifaViatico(Base):
    __tablename__ = "tarifas_viaticos"

    id = Column(Integer, primary_key=True, index=True)
    descripcion = Column(String(200), nullable=False)
    valor_dia = Column(Numeric(14, 2), nullable=False)
    aplica_desde = Column(Date, nullable=False)
    aplica_hasta = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)


class Viatico(Base):
    __tablename__ = "viaticos"

    id = Column(Integer, primary_key=True, index=True)
    practica_id = Column(Integer, ForeignKey("practicas.id"), nullable=False)
    tarifa_id = Column(Integer, ForeignKey("tarifas_viaticos.id"), nullable=False)
    num_dias = Column(Integer, nullable=False)
    num_personas = Column(Integer, nullable=False)
    valor_calculado = Column(Numeric(14, 2), nullable=False)
    descripcion = Column(String(300), nullable=True)

    __table_args__ = (
        CheckConstraint("num_dias > 0", name="ck_viatico_num_dias"),
        CheckConstraint("num_personas > 0", name="ck_viatico_num_personas"),
        CheckConstraint("valor_calculado >= 0", name="ck_viatico_valor"),
        Index("ix_viaticos_practica", "practica_id"),
        Index("ix_viaticos_tarifa", "tarifa_id"),
    )

    practica = relationship("Practica", back_populates="viaticos")
    tarifa = relationship("TarifaViatico")


class PracticaPlantilla(Base):
    """Plantillas precargadas de prácticas extramuros extraídas del Excel institucional."""
    __tablename__ = "practica_plantillas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(500), nullable=False)          # Col D — nombre de la práctica
    programa = Column(String(200), nullable=True)          # Col B — programa académico
    sede = Column(String(100), nullable=True)              # Col C — sede
    asignatura = Column(String(300), nullable=True)        # Col G — asignatura asociada
    profesor = Column(String(300), nullable=True)          # Col E — profesor(es)
    caracter_curso = Column(String(5), nullable=True)      # Col K — T | TP
    ruta_texto = Column(Text, nullable=True)               # Col L — ruta FO-15 (texto libre)
    visitas_fo16 = Column(Text, nullable=True)             # Col M — visitas FO-16
    tipo_bus = Column(String(20), nullable=True)           # Col T — INTERNO | EXTERNO | TIQUETES
    costo_bus_externo = Column(Numeric(14, 2), nullable=True)       # Col Z
    costo_tiquetes = Column(Numeric(14, 2), nullable=True)          # Col Y
    viat_docente_dias = Column(Numeric(4, 1), nullable=True)        # Col AD
    viat_docente_valor_dia = Column(Numeric(14, 2), nullable=True)  # Col AE

    __table_args__ = (
        Index("ix_plantillas_programa", "programa"),
    )
