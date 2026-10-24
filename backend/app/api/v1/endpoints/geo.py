"""
Módulo de Geolocalización — Nominatim (OpenStreetMap) + OSRM
- GET  /geo/departamentos          → lista de departamentos de Colombia
- GET  /geo/municipios?departamento → municipios de un departamento
- POST /geo/geocodificar            → coordenadas de un lugar en Colombia
- POST /geo/distancia               → distancia vial (km) entre dos municipios vía OSRM
"""
import logging
from functools import lru_cache

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.data.colombia_geo import DEPARTAMENTOS_CO, MUNICIPIOS_POR_DEPTO
from app.services.geocoder_co import geocode_local

log = logging.getLogger(__name__)
router = APIRouter()

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "http://router.project-osrm.org/route/v1/driving"
HEADERS = {"User-Agent": "SIPAM-USCO/1.0 (sipam@usco.edu.co)"}


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/departamentos")
def get_departamentos(_=Depends(get_current_user)):
    """Retorna los 33 departamentos + Bogotá D.C. de Colombia."""
    return {"departamentos": DEPARTAMENTOS_CO}


@router.get("/municipios")
def get_municipios(
    departamento: str = Query(..., description="Nombre del departamento"),
    _=Depends(get_current_user),
):
    """Retorna los municipios de un departamento colombiano (datos DIVIPOLA)."""
    municipios = MUNICIPIOS_POR_DEPTO.get(departamento)
    if municipios is None:
        raise HTTPException(status_code=404, detail=f"Departamento '{departamento}' no encontrado")
    return {"departamentos": departamento, "municipios": sorted(municipios)}


class GeocodificarRequest(BaseModel):
    municipio: str
    departamento: str


class GeocodificarResponse(BaseModel):
    lat: float
    lon: float
    display_name: str


@router.post("/geocodificar", response_model=GeocodificarResponse)
def geocodificar(body: GeocodificarRequest, _=Depends(get_current_user)):
    """Geocodifica un municipio colombiano usando Nominatim (OSM)."""
    coords = _geocodificar_cached(body.municipio, body.departamento)
    if coords is None:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró '{body.municipio}, {body.departamento}, Colombia'",
        )
    return GeocodificarResponse(**coords)


class DistanciaRequest(BaseModel):
    origen_municipio: str
    origen_departamento: str
    destino_municipio: str
    destino_departamento: str


class DistanciaResponse(BaseModel):
    distancia_km: float | None
    duracion_min: float | None
    origen_coords: dict | None = None
    destino_coords: dict | None = None


@router.post("/distancia", response_model=DistanciaResponse)
def calcular_distancia(body: DistanciaRequest, _=Depends(get_current_user)):
    """
    Calcula la distancia vial (km) entre dos municipios colombianos.
    Paso 1: Geocodifica ambos via Nominatim.
    Paso 2: Consulta OSRM para la ruta más corta en carretera.
    """
    origen = _geocodificar_cached(body.origen_municipio, body.origen_departamento)
    destino = _geocodificar_cached(body.destino_municipio, body.destino_departamento)

    if not origen or not destino:
        raise HTTPException(
            status_code=404,
            detail="No se pudieron geocodificar uno o ambos municipios",
        )

    distancia_km, duracion_min = _calcular_osrm(
        origen["lat"], origen["lon"], destino["lat"], destino["lon"]
    )

    return DistanciaResponse(
        distancia_km=distancia_km,
        duracion_min=duracion_min,
        origen_coords={"lat": origen["lat"], "lon": origen["lon"]},
        destino_coords={"lat": destino["lat"], "lon": destino["lon"]},
    )


# ── Helpers (cached) ───────────────────────────────────────────────────────────

@lru_cache(maxsize=256)
def _geocodificar_cached(municipio: str, departamento: str) -> dict | None:
    """Geocodifica con caché: primero tabla local, luego Nominatim como fallback."""
    # 1. Tabla local offline (más confiable para municipios colombianos)
    local = geocode_local(municipio, departamento)
    if local:
        lat, lon = local
        return {"lat": lat, "lon": lon, "display_name": f"{municipio}, {departamento}, Colombia"}
    # 2. Fallback: Nominatim (OpenStreetMap)
    query = f"{municipio}, {departamento}, Colombia"
    try:
        with httpx.Client(timeout=8.0, headers=HEADERS) as client:
            r = client.get(
                NOMINATIM_URL,
                params={"q": query, "format": "json", "limit": 1, "countrycodes": "CO"},
            )
            r.raise_for_status()
            results = r.json()
            if results:
                item = results[0]
                return {
                    "lat": float(item["lat"]),
                    "lon": float(item["lon"]),
                    "display_name": item.get("display_name", query),
                }
    except Exception as exc:
        log.warning("Nominatim error para '%s': %s", query, exc)
    return None


def _calcular_osrm(lat1: float, lon1: float, lat2: float, lon2: float):
    """Llama al servidor público OSRM y devuelve (distancia_km, duracion_min)."""
    url = f"{OSRM_URL}/{lon1},{lat1};{lon2},{lat2}"
    try:
        with httpx.Client(timeout=10.0, headers=HEADERS) as client:
            r = client.get(url, params={"overview": "false"})
            r.raise_for_status()
            data = r.json()
            if data.get("code") == "Ok" and data.get("routes"):
                route = data["routes"][0]
                return round(route["distance"] / 1000, 1), round(route["duration"] / 60, 1)
    except Exception as exc:
        log.warning("OSRM error: %s", exc)
    return None, None
