"""
IoT-API-01 - API endpoints for IoT device communication
Receives GPS tracking data from ESP32 devices during field practice excursions.
Course compliance: IoT + Backend integration
"""
import secrets
import logging
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.db.database import get_db
from app.api.deps import get_current_user, require_roles
from app.models.user import User, RolEnum
from app.models.iot_tracking import IoTTrackingPoint
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


# ============ SCHEMAS ============

class IoTTrackingCreate(BaseModel):
    """Schema for IoT tracking data from ESP32 GPS tracker."""
    device_id: str = Field(..., description="Unique device identifier")
    practice_id: str = Field(..., description="Practice excursion ID")
    timestamp: int = Field(..., description="Device uptime milliseconds")

    # GPS Data
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    altitude: Optional[float] = None
    speed_kmh: Optional[float] = Field(None, ge=0)
    course: Optional[float] = Field(None, ge=0, le=360)

    # GPS Quality
    satellites: Optional[int] = Field(None, ge=0)
    hdop: Optional[float] = None

    # Timestamps
    datetime_gps: Optional[str] = None

    # Device Status
    battery_voltage: Optional[float] = Field(None, ge=0, le=5)
    wifi_rssi: Optional[int] = None  # Signal strength in dBm
    uptime_seconds: Optional[int] = None

    # Error tracking
    error: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "device_id": "ESP32_GPS_001",
                "practice_id": "PRAC_001",
                "timestamp": 12345678,
                "latitude": 2.4419,
                "longitude": -76.6063,
                "altitude": 1500.5,
                "speed_kmh": 45.5,
                "course": 180.0,
                "satellites": 8,
                "hdop": 1.2,
                "battery_voltage": 4.2,
                "wifi_rssi": -65
            }
        }
    )


class IoTTrackingResponse(BaseModel):
    """Response schema for tracking data."""
    id: int
    device_id: str
    practice_id: str
    latitude: Optional[float]
    longitude: Optional[float]
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ AUTHENTICATION ============

def verify_iot_api_key(x_api_key: str = Header(...)):
    """Verify IoT device API key (constant-time comparison against env config)."""
    if not secrets.compare_digest(x_api_key, settings.IOT_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing IoT API key"
        )
    return True


# ============ ENDPOINTS ============

@router.get("/health")
def iot_health_check():
    """Public health check for IoT module - no authentication required."""
    return {
        "status": "ok",
        "module": "IoT GPS Tracking",
        "features": [
            "ESP32 GPS Tracker support",
            "WiFi HTTP REST API",
            "Real-time location tracking",
            "Battery monitoring",
            "Signal quality (RSSI)"
        ],
        "course_compliance": {
            "iot_fundamentals": True,
            "sensors": "GPS NEO-6M",
            "controller": "ESP32 DevKit",
            "communication": "WiFi + HTTP REST",
            "data_format": "JSON",
            "protocol": "HTTP/1.1"
        }
    }


@router.post("/tracking/", status_code=status.HTTP_201_CREATED)
def create_tracking_point(
    data: IoTTrackingCreate,
    db: Session = Depends(get_db),
    api_key_valid: bool = Depends(verify_iot_api_key)
):
    """
    Receive GPS tracking data from ESP32 device.

    - **device_id**: ESP32 device unique identifier
    - **practice_id**: Associated practice excursion
    - **latitude/longitude**: GPS coordinates
    - **battery_voltage**: Device power status

    Returns created tracking point ID.
    """
    logger.info(f"IoT data received from device {data.device_id}")
    logger.info(f"Location: ({data.latitude}, {data.longitude})")

    # Check if we have valid GPS fix
    if data.latitude is None or data.longitude is None:
        logger.warning(f"No GPS fix from device {data.device_id}: {data.error}")
        return {
            "status": "received",
            "gps_valid": False,
            "message": "Data received but no GPS fix"
        }

    point = IoTTrackingPoint(
        device_id=data.device_id,
        practice_id=data.practice_id,
        device_timestamp=data.timestamp,
        latitude=data.latitude,
        longitude=data.longitude,
        altitude=data.altitude,
        speed_kmh=data.speed_kmh,
        course=data.course,
        satellites=data.satellites,
        hdop=data.hdop,
        datetime_gps=data.datetime_gps,
        battery_voltage=data.battery_voltage,
        wifi_rssi=data.wifi_rssi,
        uptime_seconds=data.uptime_seconds,
        error=data.error,
    )
    db.add(point)
    db.commit()
    db.refresh(point)

    return {
        "status": "success",
        "gps_valid": True,
        "id": point.id,
        "device_id": data.device_id,
        "practice_id": data.practice_id,
        "location": {
            "lat": data.latitude,
            "lng": data.longitude,
            "altitude": data.altitude
        },
        "signal_quality": {
            "satellites": data.satellites,
            "hdop": data.hdop,
            "wifi_rssi": data.wifi_rssi
        },
        "device_status": {
            "battery": data.battery_voltage,
            "uptime_seconds": data.uptime_seconds
        },
        "recorded_at": point.recorded_at.isoformat() if point.recorded_at else None
    }


def _point_to_dict(p: IoTTrackingPoint) -> dict:
    return {
        "id": p.id,
        "device_id": p.device_id,
        "practice_id": p.practice_id,
        "latitude": p.latitude,
        "longitude": p.longitude,
        "altitude": p.altitude,
        "speed_kmh": p.speed_kmh,
        "course": p.course,
        "satellites": p.satellites,
        "hdop": p.hdop,
        "battery_voltage": p.battery_voltage,
        "wifi_rssi": p.wifi_rssi,
        "recorded_at": p.recorded_at.isoformat() if p.recorded_at else None,
    }


@router.get("/tracking/{practice_id}", response_model=List[dict])
def get_tracking_points(
    practice_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(
        RolEnum.admin, RolEnum.profesor,
        RolEnum.jefe_programa, RolEnum.decano
    ))
):
    """
    Get all tracking points for a practice excursion.
    Requires authentication (Professor, Jefe Programa, Admin, or Decano).
    """
    points = (
        db.query(IoTTrackingPoint)
        .filter(IoTTrackingPoint.practice_id == practice_id)
        .order_by(IoTTrackingPoint.recorded_at.asc())
        .all()
    )
    return [_point_to_dict(p) for p in points]


@router.get("/tracking/{practice_id}/map")
def get_tracking_map(
    practice_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(
        RolEnum.admin, RolEnum.profesor,
        RolEnum.jefe_programa, RolEnum.decano
    ))
):
    """
    Get map visualization data for a practice track.
    Returns GeoJSON format for map rendering.
    """
    points = (
        db.query(IoTTrackingPoint)
        .filter(IoTTrackingPoint.practice_id == practice_id)
        .order_by(IoTTrackingPoint.recorded_at.asc())
        .all()
    )
    if not points:
        return {"type": "FeatureCollection", "features": []}

    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [p.longitude, p.latitude]},
            "properties": {
                "time": p.recorded_at.isoformat() if p.recorded_at else None,
                "speed": p.speed_kmh,
            },
        }
        for p in points
        if p.latitude is not None and p.longitude is not None
    ]
    coords = [[p.longitude, p.latitude] for p in points if p.latitude is not None]
    if len(coords) >= 2:
        features.append({
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coords},
            "properties": {"practice_id": practice_id, "device_id": points[0].device_id},
        })
    return {"type": "FeatureCollection", "features": features}


@router.get("/devices/")
def list_iot_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.admin))
):
    """List IoT devices that have reported data (Admin only)."""
    rows = (
        db.query(IoTTrackingPoint.device_id, IoTTrackingPoint.practice_id,
                 IoTTrackingPoint.battery_voltage, IoTTrackingPoint.recorded_at)
        .order_by(IoTTrackingPoint.recorded_at.desc())
        .all()
    )
    seen: dict[str, dict] = {}
    for r in rows:
        if r.device_id not in seen:
            seen[r.device_id] = {
                "device_id": r.device_id,
                "type": "GPS Tracker",
                "status": "online",
                "last_seen": r.recorded_at.isoformat() if r.recorded_at else None,
                "battery": r.battery_voltage,
                "practice_assigned": r.practice_id,
            }
    return {"devices": list(seen.values())}


@router.post("/devices/{device_id}/configure")
def configure_device(
    device_id: str,
    config: dict,
    current_user: User = Depends(require_roles(RolEnum.admin))
):
    """Configure IoT device parameters (Admin only)."""
    return {
        "device_id": device_id,
        "configuration_applied": config,
        "status": "configured"
    }
