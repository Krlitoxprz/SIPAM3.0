from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Numeric, Text, Index, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class HorasMonitor(Base):
    """Registro semanal de horas cumplidas por cada monitor seleccionado."""
    __tablename__ = "horas_monitor"

    id = Column(Integer, primary_key=True, index=True)
    postulacion_id = Column(Integer, ForeignKey("postulaciones.id"), nullable=False)
    semana = Column(Integer, nullable=False)
    horas = Column(Numeric(5, 2), nullable=False)
    descripcion = Column(Text, nullable=True)
    aprobado_por_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("postulacion_id", "semana", name="uq_horas_semana"),
        CheckConstraint("horas > 0", name="ck_horas_positivas"),
        CheckConstraint("semana >= 1 AND semana <= 20", name="ck_horas_semana_rango"),
        Index("ix_horas_postulacion", "postulacion_id"),
        Index("ix_horas_aprobado_por", "aprobado_por_id"),
    )

    postulacion = relationship("Postulacion", foreign_keys=[postulacion_id])
    aprobado_por = relationship("User", foreign_keys=[aprobado_por_id])


class AuditLog(Base):
    """Bitácora de acciones relevantes en el sistema."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    accion = Column(String(150), nullable=False)
    entidad = Column(String(100), nullable=False)
    entidad_id = Column(Integer, nullable=True)
    detalle = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_audit_usuario", "usuario_id"),
        Index("ix_audit_entidad", "entidad", "entidad_id"),
        Index("ix_audit_created", "created_at"),
    )

    usuario = relationship("User", foreign_keys=[usuario_id])
