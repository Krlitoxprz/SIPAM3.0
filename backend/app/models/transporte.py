from sqlalchemy import Column, Integer, String, Float, Numeric, Boolean, Date, DateTime, Index, UniqueConstraint
from sqlalchemy.sql import func

from app.db.database import Base


class PrecioCombustible(Base):
    __tablename__ = "precios_combustible"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(30), nullable=False)       # gasolina_corriente | diesel | gasolina_extra
    precio_litro = Column(Numeric(10, 4), nullable=False)
    departamento = Column(String(100), nullable=False, default="HUILA")
    fecha_vigencia = Column(Date, nullable=False)
    fuente = Column(String(100), default="SICOM")
    actualizado_en = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_precios_combustible_tipo_dept", "tipo", "departamento"),
        UniqueConstraint("tipo", "departamento", "fecha_vigencia", name="uq_precio_combustible"),
    )


class PeajeNacional(Base):
    __tablename__ = "peajes_nacionales"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    departamento = Column(String(100), nullable=False)
    municipio = Column(String(100), nullable=True)
    corredor = Column(String(300), nullable=True)   # e.g. "Bogotá-Neiva"
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    tarifa_cat1 = Column(Integer, nullable=False)   # Auto / camioneta / moto
    tarifa_cat2 = Column(Integer, nullable=False)   # Bus 2 ejes liviano
    tarifa_cat3 = Column(Integer, nullable=False)   # Bus 2 ejes pesado / van escolar
    tarifa_cat4 = Column(Integer, nullable=True)    # Camión 2 ejes
    tarifa_cat5 = Column(Integer, nullable=True)    # Camión 3+ ejes
    administrado_por = Column(String(150), nullable=True)  # INVIAS | nombre concesión ANI
    vigente_desde = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        Index("ix_peajes_departamento", "departamento"),
        Index("ix_peajes_corredor", "corredor"),
        UniqueConstraint("nombre", name="uq_peaje_nombre"),
    )
