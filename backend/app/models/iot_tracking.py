"""Puntos GPS recibidos de dispositivos IoT (ESP32 / simulador) durante prácticas."""
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Index
from sqlalchemy.sql import func

from app.db.database import Base


class IoTTrackingPoint(Base):
    __tablename__ = "iot_tracking_points"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(64), nullable=False)
    practice_id = Column(String(64), nullable=False)
    device_timestamp = Column(Integer, nullable=True)      # uptime en ms del dispositivo

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    altitude = Column(Float, nullable=True)
    speed_kmh = Column(Float, nullable=True)
    course = Column(Float, nullable=True)

    satellites = Column(Integer, nullable=True)
    hdop = Column(Float, nullable=True)
    datetime_gps = Column(String(64), nullable=True)

    battery_voltage = Column(Float, nullable=True)
    wifi_rssi = Column(Integer, nullable=True)
    uptime_seconds = Column(Integer, nullable=True)
    error = Column(Text, nullable=True)

    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_iot_tracking_practice", "practice_id"),
        Index("ix_iot_tracking_device", "device_id"),
    )
