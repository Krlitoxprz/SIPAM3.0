"""Registro de pagos de viáticos para prácticas aprobadas (SF-09)."""
from sqlalchemy import Column, Integer, Float, Numeric, String, DateTime, ForeignKey, Text, Index, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class PagoViatico(Base):
    __tablename__ = "pagos_viaticos"

    id = Column(Integer, primary_key=True, index=True)
    practica_id = Column(Integer, ForeignKey("practicas.id"), nullable=False)
    registrado_por_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    monto_pagado = Column(Numeric(14, 2), nullable=False)
    fecha_pago = Column(DateTime(timezone=True), nullable=False)
    comprobante_url = Column(String(500), nullable=True)
    observaciones = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("monto_pagado > 0", name="ck_pago_monto_positivo"),
        Index("ix_pago_viatico_practica", "practica_id"),
        Index("ix_pago_viatico_registrado", "registrado_por_id"),
    )

    practica = relationship("Practica", foreign_keys=[practica_id])
    registrado_por = relationship("User", foreign_keys=[registrado_por_id])
