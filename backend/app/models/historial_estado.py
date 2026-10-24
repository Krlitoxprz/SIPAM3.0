"""Historial de transiciones de estado por entidad (SF-06)."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class HistorialEstado(Base):
    """Registra cada cambio de estado en convocatorias, prácticas y presupuestos."""
    __tablename__ = "historial_estados"

    id = Column(Integer, primary_key=True, index=True)
    entidad = Column(String(50), nullable=False)       # convocatoria | practica | presupuesto
    entidad_id = Column(Integer, nullable=False)
    estado_anterior = Column(String(80), nullable=True)
    estado_nuevo = Column(String(80), nullable=False)
    usuario_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    observaciones = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_historial_entidad", "entidad", "entidad_id"),
        Index("ix_historial_created", "created_at"),
    )

    usuario = relationship("User", foreign_keys=[usuario_id])
