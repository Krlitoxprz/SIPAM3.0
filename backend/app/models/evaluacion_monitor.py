"""Evaluación de desempeño del monitor al finalizar la convocatoria (SF-03)."""
from sqlalchemy import Column, Integer, Float, Numeric, Text, DateTime, ForeignKey, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class EvaluacionMonitor(Base):
    """Evaluación cualitativa y cuantitativa que el profesor hace del monitor."""
    __tablename__ = "evaluaciones_monitor"

    id = Column(Integer, primary_key=True, index=True)
    postulacion_id = Column(Integer, ForeignKey("postulaciones.id"), nullable=False)
    evaluado_por_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    nota_desempeno = Column(Numeric(4, 2), nullable=False)   # 0.00 – 5.00
    puntualidad = Column(Numeric(4, 2), nullable=True)       # 0.00 – 5.00
    calidad_academica = Column(Numeric(4, 2), nullable=True) # 0.00 – 5.00
    observaciones = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("postulacion_id", name="uq_evaluacion_postulacion"),
        CheckConstraint("nota_desempeno >= 0 AND nota_desempeno <= 5", name="ck_eval_nota"),
        CheckConstraint("puntualidad IS NULL OR (puntualidad >= 0 AND puntualidad <= 5)", name="ck_eval_puntualidad"),
        CheckConstraint("calidad_academica IS NULL OR (calidad_academica >= 0 AND calidad_academica <= 5)", name="ck_eval_calidad"),
        Index("ix_evaluacion_postulacion", "postulacion_id"),
        Index("ix_evaluacion_evaluado_por", "evaluado_por_id"),
    )

    postulacion = relationship("Postulacion", foreign_keys=[postulacion_id])
    evaluado_por = relationship("User", foreign_keys=[evaluado_por_id])
