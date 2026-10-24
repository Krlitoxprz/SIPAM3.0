"""
Cliente OpenRouteService (ORS) — rutas y geocodificación para Colombia.
API key gratuita: https://openrouteservice.org (2 000 req/día en plan free).
"""
import math
import logging
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)
ORS_BASE = "https://api.openrouteservice.org"


# ── Geometría ────────────────────────────────────────────────────────────────

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia en km entre dos puntos (fórmula Haversine)."""
    R = 6_371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def distancia_punto_a_ruta(lat: float, lon: float, coords: list[list[float]]) -> float:
    """
    Distancia mínima (km) de un punto a la polilínea de la ruta.
    coords: lista de [lon, lat] devuelta por ORS GeoJSON.
    """
    if not coords:
        return 999.0
    return min(_haversine(lat, lon, c[1], c[0]) for c in coords)


# ── Geocodificación ──────────────────────────────────────────────────────────

async def geocode_ciudad(ciudad: str) -> tuple[float, float] | None:
    """
    Convierte el nombre de una ciudad colombiana en (lon, lat).
    Retorna None si ORS_API_KEY no está configurada o la búsqueda falla.
    """
    if not settings.ORS_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{ORS_BASE}/geocode/search",
                params={
                    "api_key": settings.ORS_API_KEY,
                    "text": f"{ciudad}, Colombia",
                    "boundary.country": "CO",
                    "size": 1,
                },
            )
            if r.status_code == 200:
                feats = r.json().get("features", [])
                if feats:
                    c = feats[0]["geometry"]["coordinates"]
                    return (float(c[0]), float(c[1]))
    except Exception as exc:
        logger.warning(f"ORS geocode '{ciudad}': {exc}")
    return None


# ── Cálculo de ruta ──────────────────────────────────────────────────────────

async def calcular_ruta(origen: str, destino: str) -> dict | None:
    """
    Calcula la ruta entre dos ciudades colombianas.

    Returns:
        {
          distancia_km: float,
          duracion_min: int,
          coordenadas: [[lon, lat], ...],   # polilínea completa
          origen_coords: (lon, lat),
          destino_coords: (lon, lat),
        }
        o None si ORS no está disponible.
    """
    if not settings.ORS_API_KEY:
        return None

    o = await geocode_ciudad(origen)
    d = await geocode_ciudad(destino)
    if not o or not d:
        logger.warning(f"No se pudo geocodificar '{origen}' o '{destino}'")
        return None

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                f"{ORS_BASE}/v2/directions/driving-car/geojson",
                headers={
                    "Authorization": settings.ORS_API_KEY,
                    "Content-Type": "application/json",
                },
                json={"coordinates": [list(o), list(d)]},
            )
            if r.status_code == 200:
                feat = r.json()["features"][0]
                summary = feat["properties"]["summary"]
                coords = feat["geometry"]["coordinates"]
                return {
                    "distancia_km": round(summary["distance"] / 1000, 1),
                    "duracion_min": round(summary["duration"] / 60),
                    "coordenadas": coords,
                    "origen_coords": o,
                    "destino_coords": d,
                }
            else:
                logger.warning(f"ORS directions HTTP {r.status_code}: {r.text[:200]}")
    except Exception as exc:
        logger.warning(f"ORS directions '{origen}→{destino}': {exc}")
    return None
