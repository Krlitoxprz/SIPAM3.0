from sqlalchemy import Column, Integer, String, Enum, DateTime, Float, Numeric, ForeignKey, Text, Boolean, Index, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.database import Base


class ConfiguracionSistema(Base):
    """Tabla singleton (id=1) con flags globales del sistema."""
    __tablename__ = "sistema_config"
    id = Column(Integer, primary_key=True, default=1)
    testing_mode = Column(Boolean, default=False, nullable=False)


class TipoMovimientoEnum(str, enum.Enum):
    asignacion = "asignacion"
    comprometido = "comprometido"
    ejecucion = "ejecucion"
    ajuste = "ajuste"
    devolucion = "devolucion"


class EstadoPresupuestoEnum(str, enum.Enum):
    borrador = "borrador"          # jefe crea la solicitud
    solicitado = "solicitado"      # jefe envía solicitud al admin
    aprobado = "aprobado"          # admin aprueba
    rechazado = "rechazado"        # admin rechaza
    modificacion = "modificacion"  # admin pide ajuste


class Presupuesto(Base):
    __tablename__ = "presupuestos"

    id = Column(Integer, primary_key=True, index=True)
    periodo_academico = Column(String(10), nullable=False, unique=True, index=True)
    monto_total_asignado = Column(Numeric(14, 2), nullable=False, default=0)
    monto_solicitado = Column(Numeric(14, 2), nullable=True)          # monto pendiente de aprobación (incremento)
    monto_ejecutado = Column(Numeric(14, 2), nullable=False, default=0)
    monto_comprometido = Column(Numeric(14, 2), nullable=False, default=0)
    descripcion = Column(Text, nullable=True)
    estado = Column(Enum(EstadoPresupuestoEnum), nullable=False, default=EstadoPresupuestoEnum.aprobado)
    observaciones_admin = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("monto_total_asignado >= 0", name="ck_presupuesto_monto"),
        CheckConstraint("monto_ejecutado >= 0", name="ck_presupuesto_ejecutado"),
        CheckConstraint("monto_comprometido >= 0", name="ck_presupuesto_comprometido"),
    )

    movimientos = relationship("MovimientoPresupuestal", back_populates="presupuesto", cascade="all, delete-orphan")

    @property
    def monto_disponible(self):
        return self.monto_total_asignado - self.monto_ejecutado - self.monto_comprometido


class MovimientoPresupuestal(Base):
    __tablename__ = "movimientos_presupuestales"

    id = Column(Integer, primary_key=True, index=True)
    presupuesto_id = Column(Integer, ForeignKey("presupuestos.id"), nullable=False)
    tipo = Column(Enum(TipoMovimientoEnum), nullable=False)
    monto = Column(Numeric(14, 2), nullable=False)
    concepto = Column(String(300), nullable=False)
    practica_id = Column(Integer, ForeignKey("practicas.id"), nullable=True)
    responsable_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    fecha_movimiento = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("monto != 0", name="ck_movimiento_monto_nonzero"),
        Index("ix_movimientos_presupuesto", "presupuesto_id"),
        Index("ix_movimientos_fecha", "fecha_movimiento"),
        Index("ix_movimientos_practica_id", "practica_id"),
        Index("ix_movimientos_responsable", "responsable_id"),
    )

    presupuesto = relationship("Presupuesto", back_populates="movimientos")
    practica = relationship("Practica")
    responsable = relationship("User", foreign_keys=[responsable_id])


class ConfiguracionCalendario(Base):
    __tablename__ = "configuracion_calendario"

    id = Column(Integer, primary_key=True, index=True)
    periodo_academico = Column(String(10), nullable=False, unique=True, index=True)
    semana_inicio_solicitudes = Column(Integer, default=3, nullable=False)
    semana_fin_solicitudes = Column(Integer, default=14, nullable=False)
    fecha_inicio_semestre = Column(DateTime(timezone=True), nullable=False)
    fecha_fin_semestre = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            "semana_inicio_solicitudes < semana_fin_solicitudes",
            name="ck_calendario_semanas",
        ),
        CheckConstraint(
            "fecha_fin_semestre > fecha_inicio_semestre",
            name="ck_calendario_fechas",
        ),
    )
