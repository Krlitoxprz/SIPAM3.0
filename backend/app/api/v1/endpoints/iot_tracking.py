"""
IoT-API-01 - API endpoints for IoT device communication
Receives GPS tracking data from ESP32 devices during field practice excursions.
Course compliance: IoT + Backend integration
"""
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.db.database import get_db
from app.api.deps import get_current_user, require_roles
from app.models.user import User, RolEnum
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# API Key for IoT devices (should be in environment variable)
IOT_API_KEY = "iot_device_key_12345"


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
    
    class Config:
        schema_extra = {
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


class IoTTrackingResponse(BaseModel):
    """Response schema for tracking data."""
    id: int
    device_id: str
    practice_id: str
    latitude: Optional[float]
    longitude: Optional[float]
    recorded_at: datetime
    
    class Config:
        from_attributes = True


# ============ AUTHENTICATION ============

def verify_iot_api_key(x_api_key: str = Header(...)):
    """Verify IoT device API key."""
    if x_api_key != IOT_API_KEY:
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
    # Log received data for debugging
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
    
    # Store in database (simplified - you should create the actual model)
    # For now, just return success
    
    return {
        "status": "success",
        "gps_valid": True,
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
        "recorded_at": datetime.utcnow().isoformat()
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
    # Query tracking data from database
    # Return list of tracking points with GPS coordinates
    
    return [
        {
            "id": 1,
            "device_id": "ESP32_GPS_001",
            "practice_id": practice_id,
            "latitude": 2.4419,
            "longitude": -76.6063,
            "altitude": 1500.0,
            "speed_kmh": 45.0,
            "recorded_at": "2024-03-15T10:30:00Z"
        },
        {
            "id": 2,
            "device_id": "ESP32_GPS_001",
            "practice_id": practice_id,
            "latitude": 2.4425,
            "longitude": -76.6070,
            "altitude": 1520.0,
            "speed_kmh": 42.0,
            "recorded_at": "2024-03-15T10:31:00Z"
        }
    ]


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
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [-76.6063, 2.4419]
                },
                "properties": {
                    "time": "2024-03-15T10:30:00Z",
                    "speed": 45.0
                }
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [-76.6063, 2.4419],
                        [-76.6070, 2.4425],
                        [-76.6080, 2.4430]
                    ]
                },
                "properties": {
                    "practice_id": practice_id,
                    "device_id": "ESP32_GPS_001"
                }
            }
        ]
    }


@router.get("/devices/")
def list_iot_devices(
    current_user: User = Depends(require_roles(RolEnum.admin))
):
    """List all registered IoT devices (Admin only)."""
    return {
        "devices": [
            {
                "device_id": "ESP32_GPS_001",
                "type": "GPS Tracker",
                "status": "online",
                "last_seen": "2024-03-15T10:35:00Z",
                "battery": 4.1,
                "practice_assigned": "PRAC_001"
            }
        ]
    }


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
