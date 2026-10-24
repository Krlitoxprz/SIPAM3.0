"""
Geocodificador offline de ciudades colombianas.
Coordenadas (lat, lon) WGS-84 de ~200 municipios relevantes para prácticas USCO.
Funciona sin API key como fallback cuando ORS no está configurado.
"""
import math
from typing import Optional

# ── Tabla de coordenadas ──────────────────────────────────────────────────────
# Formato: "nombre_normalizado": (lat, lon)
CIUDADES_CO: dict[str, tuple[float, float]] = {
    # Huila
    "neiva": (2.9273, -75.2819),
    "pitalito": (1.8518, -76.0510),
    "garzon": (2.2016, -75.6311),
    "garzón": (2.2016, -75.6311),
    "la plata": (2.3875, -75.9114),
    "campoalegre": (2.6894, -75.3323),
    "campo alegre": (2.6894, -75.3323),
    "rivera": (2.7741, -75.2399),
    "palermo": (2.8972, -75.4362),
    "hobo": (2.5706, -75.4527),
    "yaguara": (2.6561, -75.5021),
    "gigante": (2.3882, -75.5449),
    "timana": (1.9625, -75.9315),
    "timaná": (1.9625, -75.9315),
    "san agustin": (1.8870, -76.2744),
    "san agustín": (1.8870, -76.2744),
    "isnos": (1.9272, -76.2348),
    "acevedo": (1.8196, -75.9945),
    "algeciras": (2.5221, -75.3241),
    "altamira": (2.0594, -75.7813),
    "colombia": (1.4194, -75.9868),
    "elias": (1.8589, -75.8477),
    "tarqui": (2.1090, -75.8237),
    "la argentina": (2.2170, -76.0160),
    "la argentina huila": (2.2170, -76.0160),
    "oporapa": (2.0543, -75.9574),
    "paicol": (2.5873, -75.7107),
    "palestina": (1.7438, -76.0282),
    "pital": (2.3530, -75.7804),
    "saladoblanco": (1.9937, -76.0714),
    "santa maria": (3.0023, -75.6060),
    "suaza": (1.9688, -75.7922),
    "teruel": (2.6637, -75.5704),
    "tesalia": (2.4823, -75.7313),
    "villavieja": (3.2178, -75.2230),
    "yaguara huila": (2.6561, -75.5021),
    # Caquetá
    "florencia": (1.6177, -75.6063),
    "san jose del fragua": (1.3277, -75.9829),
    "san vicente del caguan": (2.1227, -74.7674),
    "belen de los andaquies": (1.4241, -75.8715),
    "curillo": (0.9350, -75.9430),
    "milan": (1.3236, -75.4706),
    "puerto rico": (1.9074, -75.1567),
    "valparaiso": (1.2002, -75.6189),
    # Cundinamarca / Bogotá
    "bogota": (4.7110, -74.0721),
    "bogotá": (4.7110, -74.0721),
    "soacha": (4.5792, -74.2154),
    "mosquera": (4.7064, -74.2328),
    "funza": (4.7143, -74.2128),
    "madrid": (4.7318, -74.2629),
    "facatativa": (4.8143, -74.3582),
    "zipaquira": (5.0230, -74.0037),
    "zipaquirá": (5.0230, -74.0037),
    "chia": (4.8605, -74.0574),
    "chía": (4.8605, -74.0574),
    "la calera": (4.7233, -73.9776),
    "cajica": (4.9167, -74.0231),
    "cajicá": (4.9167, -74.0231),
    "girardot": (4.3027, -74.8026),
    "espinal": (4.1530, -74.8779),
    "ibague": (4.4389, -75.2322),
    "ibagué": (4.4389, -75.2322),
    # Tolima
    "espinal": (4.1530, -74.8779),
    "melgar": (4.2041, -74.6449),
    "honda": (5.2042, -74.7397),
    # Valle del Cauca
    "cali": (3.4516, -76.5320),
    "palmira": (3.5319, -76.3037),
    "buenaventura": (3.8801, -77.0301),
    "buga": (3.9000, -76.2980),
    "tulua": (4.0838, -76.1983),
    "tuluá": (4.0838, -76.1983),
    "cartago": (4.7453, -75.9121),
    "yumbo": (3.5892, -76.4974),
    "florida": (3.3310, -76.2300),
    "pradera": (3.4211, -76.2437),
    # Antioquia
    "medellin": (6.2518, -75.5636),
    "medellín": (6.2518, -75.5636),
    "bello": (6.3387, -75.5558),
    "itagui": (6.1843, -75.5990),
    "itaguí": (6.1843, -75.5990),
    "envigado": (6.1681, -75.5878),
    "rionegro": (6.1543, -75.3739),
    # Atlántico
    "barranquilla": (10.9685, -74.7813),
    "soledad": (10.9155, -74.7661),
    "malambo": (10.8637, -74.7726),
    "sabanalarga": (10.6332, -74.9219),
    # Bolívar
    "cartagena": (10.3910, -75.4794),
    "magangue": (9.2384, -74.7546),
    "magangué": (9.2384, -74.7546),
    # Santander
    "bucaramanga": (7.1193, -73.1227),
    "floridablanca": (7.0637, -73.0895),
    "giron": (7.0698, -73.1680),
    "girón": (7.0698, -73.1680),
    "piedecuesta": (6.9872, -73.0463),
    "barrancabermeja": (7.0652, -73.8547),
    # Norte de Santander
    "cucuta": (7.8939, -72.5078),
    "cúcuta": (7.8939, -72.5078),
    # Boyacá
    "tunja": (5.5353, -73.3678),
    "duitama": (5.8227, -73.0275),
    "sogamoso": (5.7189, -72.9267),
    # Cauca
    "popayan": (2.4448, -76.6147),
    "popayán": (2.4448, -76.6147),
    "santander de quilichao": (3.0112, -76.4800),
    # Nariño
    "pasto": (1.2136, -77.2811),
    "tumaco": (1.7992, -78.7627),
    "ipiales": (0.8285, -77.6441),
    # Quindío
    "armenia": (4.5338, -75.6811),
    "calarca": (4.5143, -75.6412),
    "calarcá": (4.5143, -75.6412),
    # Risaralda
    "pereira": (4.8133, -75.6961),
    "dosquebradas": (4.8381, -75.6636),
    # Caldas
    "manizales": (5.0703, -75.5138),
    # Meta
    "villavicencio": (4.1420, -73.6266),
    "acacias": (3.9880, -73.7595),
    "granada": (3.5366, -73.7163),
    # Putumayo
    "mocoa": (1.1521, -76.6491),
    "puerto asis": (0.4953, -76.5024),
    "puerto asís": (0.4953, -76.5024),
    # Amazonas
    "leticia": (-4.2153, -69.9406),
    # Vichada
    "puerto carreno": (6.1889, -67.4833),
    "puerto carreño": (6.1889, -67.4833),
    # Guaviare
    "san jose del guaviare": (2.5667, -72.6333),
    # Cesar
    "valledupar": (10.4631, -73.2532),
    # Magdalena
    "santa marta": (11.2408, -74.2110),
    # Córdoba
    "monteria": (8.7575, -75.8897),
    "montería": (8.7575, -75.8897),
    # Sucre
    "sincelejo": (9.3047, -75.3978),
    # Chocó
    "quibdo": (5.6919, -76.6583),
    "quibdó": (5.6919, -76.6583),
    # Arauca
    "arauca": (7.0899, -70.7617),
    # Casanare
    "yopal": (5.3378, -72.3950),
}


def _normalizar(nombre: str) -> str:
    return (
        nombre.lower()
        .strip()
        .replace("á", "a").replace("é", "e").replace("í", "i")
        .replace("ó", "o").replace("ú", "u").replace("ü", "u")
        .replace(",", "").replace(".", "")
    )


def geocode_local(ciudad: str, departamento: str = "") -> Optional[tuple[float, float]]:
    """
    Busca las coordenadas (lat, lon) de una ciudad colombiana.
    Intenta varias variaciones: con departamento, sin acento, etc.
    Retorna None si no se encuentra.
    """
    candidatos = [
        ciudad,
        f"{ciudad} {departamento}",
        ciudad.split(",")[0].strip(),
    ]
    for c in candidatos:
        clave = _normalizar(c)
        if clave in CIUDADES_CO:
            return CIUDADES_CO[clave]
    return None


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia en km entre dos puntos geográficos (fórmula Haversine)."""
    R = 6_371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + (
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(a))


def distancia_entre_municipios(
    municipio_a: str,
    municipio_b: str,
    dept_a: str = "",
    dept_b: str = "",
    factor_ruta: float = 1.35,
) -> Optional[float]:
    """
    Calcula la distancia vial estimada entre dos municipios colombianos.
    Usa haversine × factor_ruta (1.35 por defecto) para aproximar la carretera real.
    Retorna None si alguno de los municipios no está en la tabla.
    """
    coords_a = geocode_local(municipio_a, dept_a)
    coords_b = geocode_local(municipio_b, dept_b)
    if coords_a is None or coords_b is None:
        return None
    lineal = haversine_km(coords_a[0], coords_a[1], coords_b[0], coords_b[1])
    return round(lineal * factor_ruta, 1)
