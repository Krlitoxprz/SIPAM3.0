from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class DocumentoPresupuesto(Base):
    __tablename__ = "documentos_presupuesto"

    id = Column(Integer, primary_key=True, index=True)
    presupuesto_id = Column(Integer, ForeignKey("presupuestos.id"), nullable=False)
    subido_por_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tipo_solicitud = Column(String(30), nullable=False)   # solicitud | incremento | modificacion
    nombre_original = Column(String(255), nullable=False)  # nombre que dio el usuario
    nombre_almacenado = Column(String(255), nullable=False)  # UUID filename en disco
    ruta = Column(String(500), nullable=False)             # ruta relativa en uploads/
    descripcion = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_docs_presupuesto", "presupuesto_id"),
        Index("ix_docs_subido_por", "subido_por_id"),
    )

    presupuesto = relationship("Presupuesto", backref="documentos")
    subido_por = relationship("User", foreign_keys=[subido_por_id])
