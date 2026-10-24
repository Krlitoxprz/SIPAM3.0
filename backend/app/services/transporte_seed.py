"""
Datos semilla de peajes nacionales (fuente: INVIAS / ANI, tarifas 2024-2025).
Se insertan al iniciar el sistema si la tabla está vacía.
Categorías vehiculares:
  Cat 1 — Auto, camioneta, moto
  Cat 2 — Bus 2 ejes liviano (≤30 pasajeros)
  Cat 3 — Bus 2 ejes pesado / van escolar
  Cat 4 — Camión 2 ejes (6 llantas)
  Cat 5 — Camión 3+ ejes
"""
from datetime import date

PEAJES_SEED = [
    # ── Corredor Bogotá–Neiva (Ruta 45A, Troncal del Magdalena) ──────────────
    {"nombre": "Peaje Chinauta", "departamento": "Cundinamarca", "municipio": "Fusagasugá",
     "corredor": "Bogotá-Neiva", "lat": 4.3479, "lon": -74.3610,
     "tarifa_cat1": 10_200, "tarifa_cat2": 16_800, "tarifa_cat3": 14_200,
     "tarifa_cat4": 20_400, "tarifa_cat5": 30_600, "administrado_por": "INVIAS"},

    {"nombre": "Peaje Flandes", "departamento": "Tolima", "municipio": "Flandes",
     "corredor": "Bogotá-Neiva", "lat": 4.3876, "lon": -74.8258,
     "tarifa_cat1": 9_500, "tarifa_cat2": 15_600, "tarifa_cat3": 13_200,
     "tarifa_cat4": 19_000, "tarifa_cat5": 28_500, "administrado_por": "INVIAS"},

    {"nombre": "Peaje Chicoral", "departamento": "Tolima", "municipio": "El Espinal",
     "corredor": "Bogotá-Neiva", "lat": 4.3110, "lon": -74.9947,
     "tarifa_cat1": 9_500, "tarifa_cat2": 15_600, "tarifa_cat3": 13_200,
     "tarifa_cat4": 19_000, "tarifa_cat5": 28_500, "administrado_por": "INVIAS"},

    {"nombre": "Peaje Natagaima", "departamento": "Tolima", "municipio": "Natagaima",
     "corredor": "Bogotá-Neiva", "lat": 3.6261, "lon": -75.0971,
     "tarifa_cat1": 8_100, "tarifa_cat2": 13_300, "tarifa_cat3": 11_300,
     "tarifa_cat4": 16_200, "tarifa_cat5": 24_300, "administrado_por": "INVIAS"},

    # ── Corredor Neiva–Florencia / Huila interior (Ruta 45) ──────────────────
    {"nombre": "Peaje Neiva (Vía al Llano)", "departamento": "Huila", "municipio": "Neiva",
     "corredor": "Neiva-Interior Huila", "lat": 2.9149, "lon": -75.2862,
     "tarifa_cat1": 8_100, "tarifa_cat2": 13_300, "tarifa_cat3": 11_400,
     "tarifa_cat4": 16_200, "tarifa_cat5": 24_300, "administrado_por": "INVIAS"},

    {"nombre": "Peaje Campoalegre", "departamento": "Huila", "municipio": "Campoalegre",
     "corredor": "Neiva-Interior Huila", "lat": 2.6863, "lon": -75.3261,
     "tarifa_cat1": 8_100, "tarifa_cat2": 13_300, "tarifa_cat3": 9_800,
     "tarifa_cat4": 16_200, "tarifa_cat5": 24_300, "administrado_por": "INVIAS"},

    {"nombre": "Peaje Gigante", "departamento": "Huila", "municipio": "Gigante",
     "corredor": "Neiva-Interior Huila", "lat": 2.3849, "lon": -75.5339,
     "tarifa_cat1": 8_100, "tarifa_cat2": 13_300, "tarifa_cat3": 9_800,
     "tarifa_cat4": 16_200, "tarifa_cat5": 24_300, "administrado_por": "INVIAS"},

    {"nombre": "Peaje Garzón", "departamento": "Huila", "municipio": "Garzón",
     "corredor": "Neiva-Interior Huila", "lat": 2.1983, "lon": -75.6286,
     "tarifa_cat1": 8_100, "tarifa_cat2": 13_300, "tarifa_cat3": 10_200,
     "tarifa_cat4": 16_200, "tarifa_cat5": 24_300, "administrado_por": "INVIAS"},

    {"nombre": "Peaje Altamira", "departamento": "Huila", "municipio": "Altamira",
     "corredor": "Neiva-Interior Huila", "lat": 2.0003, "lon": -75.7698,
     "tarifa_cat1": 8_100, "tarifa_cat2": 13_300, "tarifa_cat3": 10_200,
     "tarifa_cat4": 16_200, "tarifa_cat5": 24_300, "administrado_por": "INVIAS"},

    {"nombre": "Peaje Suaza", "departamento": "Huila", "municipio": "Suaza",
     "corredor": "Neiva-Interior Huila", "lat": 1.9876, "lon": -75.8112,
     "tarifa_cat1": 8_100, "tarifa_cat2": 13_300, "tarifa_cat3": 10_200,
     "tarifa_cat4": 16_200, "tarifa_cat5": 24_300, "administrado_por": "INVIAS"},

    {"nombre": "Peaje Timaná", "departamento": "Huila", "municipio": "Timaná",
     "corredor": "Neiva-Interior Huila", "lat": 1.9704, "lon": -75.9191,
     "tarifa_cat1": 8_100, "tarifa_cat2": 13_300, "tarifa_cat3": 9_800,
     "tarifa_cat4": 16_200, "tarifa_cat5": 24_300, "administrado_por": "INVIAS"},

    {"nombre": "Peaje Pitalito (Acceso)", "departamento": "Huila", "municipio": "Pitalito",
     "corredor": "Neiva-Interior Huila", "lat": 1.8483, "lon": -76.0491,
     "tarifa_cat1": 9_500, "tarifa_cat2": 15_600, "tarifa_cat3": 11_400,
     "tarifa_cat4": 19_000, "tarifa_cat5": 28_500, "administrado_por": "INVIAS"},

    {"nombre": "Peaje La Chiquita (Pitalito–Mocoa)", "departamento": "Putumayo", "municipio": "Mocoa",
     "corredor": "Pitalito-Mocoa", "lat": 1.2197, "lon": -76.6443,
     "tarifa_cat1": 10_200, "tarifa_cat2": 16_800, "tarifa_cat3": 12_500,
     "tarifa_cat4": 20_400, "tarifa_cat5": 30_600, "administrado_por": "INVIAS"},

    {"nombre": "Peaje Villavieja", "departamento": "Huila", "municipio": "Villavieja",
     "corredor": "Neiva-Villavieja", "lat": 3.2278, "lon": -75.2134,
     "tarifa_cat1": 6_900, "tarifa_cat2": 11_300, "tarifa_cat3": 8_500,
     "tarifa_cat4": 13_800, "tarifa_cat5": 20_700, "administrado_por": "INVIAS"},

    # ── Corredor Neiva–La Plata–Popayán (Ruta 25) ────────────────────────────
    {"nombre": "Peaje Paicol", "departamento": "Huila", "municipio": "Paicol",
     "corredor": "Neiva-La Plata-Popayán", "lat": 2.4870, "lon": -75.7260,
     "tarifa_cat1": 8_100, "tarifa_cat2": 13_300, "tarifa_cat3": 9_800,
     "tarifa_cat4": 16_200, "tarifa_cat5": 24_300, "administrado_por": "INVIAS"},

    {"nombre": "Peaje La Plata (Cruce)", "departamento": "Huila", "municipio": "La Plata",
     "corredor": "Neiva-La Plata-Popayán", "lat": 2.3924, "lon": -75.8942,
     "tarifa_cat1": 8_100, "tarifa_cat2": 13_300, "tarifa_cat3": 9_800,
     "tarifa_cat4": 16_200, "tarifa_cat5": 24_300, "administrado_por": "INVIAS"},

    {"nombre": "Peaje Inzá", "departamento": "Cauca", "municipio": "Inzá",
     "corredor": "Neiva-La Plata-Popayán", "lat": 2.5498, "lon": -76.0681,
     "tarifa_cat1": 8_100, "tarifa_cat2": 13_300, "tarifa_cat3": 9_800,
     "tarifa_cat4": 16_200, "tarifa_cat5": 24_300, "administrado_por": "INVIAS"},

    # ── Corredor Bogotá–Medellín (Ruta 62 / Autopista Bogotá-Medellín) ───────
    {"nombre": "Peaje Balsillas", "departamento": "Cundinamarca", "municipio": "Mosquera",
     "corredor": "Bogotá-Medellín", "lat": 4.4591, "lon": -74.2809,
     "tarifa_cat1": 11_600, "tarifa_cat2": 19_000, "tarifa_cat3": 16_100,
     "tarifa_cat4": 23_200, "tarifa_cat5": 34_800, "administrado_por": "Concesión Devimar"},

    {"nombre": "Peaje La Ye", "departamento": "Cundinamarca", "municipio": "Facatativá",
     "corredor": "Bogotá-Medellín", "lat": 4.8152, "lon": -74.3563,
     "tarifa_cat1": 11_600, "tarifa_cat2": 19_000, "tarifa_cat3": 16_100,
     "tarifa_cat4": 23_200, "tarifa_cat5": 34_800, "administrado_por": "Concesión Devimar"},

    {"nombre": "Peaje Honda", "departamento": "Tolima", "municipio": "Honda",
     "corredor": "Bogotá-Medellín", "lat": 5.2041, "lon": -74.7390,
     "tarifa_cat1": 9_500, "tarifa_cat2": 15_600, "tarifa_cat3": 13_200,
     "tarifa_cat4": 19_000, "tarifa_cat5": 28_500, "administrado_por": "INVIAS"},

    {"nombre": "Peaje Los Cuervos", "departamento": "Antioquia", "municipio": "Puerto Triunfo",
     "corredor": "Bogotá-Medellín", "lat": 5.8786, "lon": -74.6421,
     "tarifa_cat1": 13_000, "tarifa_cat2": 21_300, "tarifa_cat3": 18_100,
     "tarifa_cat4": 26_000, "tarifa_cat5": 39_000, "administrado_por": "Devimed"},

    {"nombre": "Peaje Marinilla", "departamento": "Antioquia", "municipio": "Marinilla",
     "corredor": "Bogotá-Medellín", "lat": 6.1755, "lon": -75.3341,
     "tarifa_cat1": 13_000, "tarifa_cat2": 21_300, "tarifa_cat3": 18_100,
     "tarifa_cat4": 26_000, "tarifa_cat5": 39_000, "administrado_por": "Devimed"},

    # ── Corredor Bogotá–Cali (Ruta 40) ───────────────────────────────────────
    {"nombre": "Peaje La Mesa", "departamento": "Cundinamarca", "municipio": "La Mesa",
     "corredor": "Bogotá-Cali", "lat": 4.6360, "lon": -74.4614,
     "tarifa_cat1": 10_200, "tarifa_cat2": 16_800, "tarifa_cat3": 14_200,
     "tarifa_cat4": 20_400, "tarifa_cat5": 30_600, "administrado_por": "INVIAS"},

    {"nombre": "Peaje Girardot", "departamento": "Cundinamarca", "municipio": "Girardot",
     "corredor": "Bogotá-Cali", "lat": 4.2965, "lon": -74.7822,
     "tarifa_cat1": 9_500, "tarifa_cat2": 15_600, "tarifa_cat3": 13_200,
     "tarifa_cat4": 19_000, "tarifa_cat5": 28_500, "administrado_por": "INVIAS"},

    {"nombre": "Peaje Buga", "departamento": "Valle del Cauca", "municipio": "Guadalajara de Buga",
     "corredor": "Bogotá-Cali", "lat": 3.9034, "lon": -76.2998,
     "tarifa_cat1": 11_600, "tarifa_cat2": 19_000, "tarifa_cat3": 16_100,
     "tarifa_cat4": 23_200, "tarifa_cat5": 34_800, "administrado_por": "Autopista Bogotá-Buenaventura"},

    {"nombre": "Peaje Loboguerrero", "departamento": "Valle del Cauca", "municipio": "Dagua",
     "corredor": "Cali-Buenaventura", "lat": 3.7741, "lon": -76.6521,
     "tarifa_cat1": 11_600, "tarifa_cat2": 19_000, "tarifa_cat3": 16_100,
     "tarifa_cat4": 23_200, "tarifa_cat5": 34_800, "administrado_por": "Autopista Bogotá-Buenaventura"},

    # ── Corredor Cali–Pasto (Ruta 25) ────────────────────────────────────────
    {"nombre": "Peaje Mediacanoa", "departamento": "Valle del Cauca", "municipio": "El Cerrito",
     "corredor": "Cali-Pasto", "lat": 3.7195, "lon": -76.3386,
     "tarifa_cat1": 11_600, "tarifa_cat2": 19_000, "tarifa_cat3": 16_100,
     "tarifa_cat4": 23_200, "tarifa_cat5": 34_800, "administrado_por": "INVIAS"},

    {"nombre": "Peaje Popayán", "departamento": "Cauca", "municipio": "Popayán",
     "corredor": "Cali-Pasto", "lat": 2.4391, "lon": -76.6069,
     "tarifa_cat1": 8_100, "tarifa_cat2": 13_300, "tarifa_cat3": 11_300,
     "tarifa_cat4": 16_200, "tarifa_cat5": 24_300, "administrado_por": "INVIAS"},

    {"nombre": "Peaje La Variante (Pasto)", "departamento": "Nariño", "municipio": "Pasto",
     "corredor": "Cali-Pasto", "lat": 1.2136, "lon": -77.2811,
     "tarifa_cat1": 8_100, "tarifa_cat2": 13_300, "tarifa_cat3": 11_300,
     "tarifa_cat4": 16_200, "tarifa_cat5": 24_300, "administrado_por": "INVIAS"},

    # ── Corredor Bogotá–Bucaramanga (Ruta 45) ────────────────────────────────
    {"nombre": "Peaje Barbosa", "departamento": "Santander", "municipio": "Barbosa",
     "corredor": "Bogotá-Bucaramanga", "lat": 5.9353, "lon": -73.6193,
     "tarifa_cat1": 9_500, "tarifa_cat2": 15_600, "tarifa_cat3": 13_200,
     "tarifa_cat4": 19_000, "tarifa_cat5": 28_500, "administrado_por": "INVIAS"},

    {"nombre": "Peaje Vélez", "departamento": "Santander", "municipio": "Vélez",
     "corredor": "Bogotá-Bucaramanga", "lat": 6.0103, "lon": -73.6761,
     "tarifa_cat1": 9_500, "tarifa_cat2": 15_600, "tarifa_cat3": 13_200,
     "tarifa_cat4": 19_000, "tarifa_cat5": 28_500, "administrado_por": "INVIAS"},

    {"nombre": "Peaje Bucaramanga (Acceso)", "departamento": "Santander", "municipio": "Bucaramanga",
     "corredor": "Bogotá-Bucaramanga", "lat": 7.1195, "lon": -73.1227,
     "tarifa_cat1": 9_500, "tarifa_cat2": 15_600, "tarifa_cat3": 13_200,
     "tarifa_cat4": 19_000, "tarifa_cat5": 28_500, "administrado_por": "INVIAS"},

    # ── Corredor Ruta del Sol (Bogotá–Santa Marta) ───────────────────────────
    {"nombre": "Peaje Villeta", "departamento": "Cundinamarca", "municipio": "Villeta",
     "corredor": "Bogotá-Santa Marta (Ruta del Sol)", "lat": 5.0152, "lon": -74.4734,
     "tarifa_cat1": 13_800, "tarifa_cat2": 22_700, "tarifa_cat3": 19_200,
     "tarifa_cat4": 27_600, "tarifa_cat5": 41_400, "administrado_por": "Ruta del Sol"},

    {"nombre": "Peaje Puerto Salgar", "departamento": "Cundinamarca", "municipio": "Puerto Salgar",
     "corredor": "Bogotá-Santa Marta (Ruta del Sol)", "lat": 5.4876, "lon": -74.6554,
     "tarifa_cat1": 13_800, "tarifa_cat2": 22_700, "tarifa_cat3": 19_200,
     "tarifa_cat4": 27_600, "tarifa_cat5": 41_400, "administrado_por": "Ruta del Sol"},

    {"nombre": "Peaje El Korán (Barranquilla)", "departamento": "Atlántico", "municipio": "Barranquilla",
     "corredor": "Bogotá-Santa Marta (Ruta del Sol)", "lat": 10.9639, "lon": -74.8175,
     "tarifa_cat1": 11_600, "tarifa_cat2": 19_000, "tarifa_cat3": 16_100,
     "tarifa_cat4": 23_200, "tarifa_cat5": 34_800, "administrado_por": "Ruta del Sol"},

    # ── Eje Cafetero ─────────────────────────────────────────────────────────
    {"nombre": "Peaje La Paila", "departamento": "Valle del Cauca", "municipio": "Zarzal",
     "corredor": "Cali-Pereira-Medellín", "lat": 4.3995, "lon": -75.9139,
     "tarifa_cat1": 11_600, "tarifa_cat2": 19_000, "tarifa_cat3": 16_100,
     "tarifa_cat4": 23_200, "tarifa_cat5": 34_800, "administrado_por": "Autopistas del Café"},

    {"nombre": "Peaje Manizales (Acceso)", "departamento": "Caldas", "municipio": "Manizales",
     "corredor": "Cali-Pereira-Medellín", "lat": 5.0700, "lon": -75.5074,
     "tarifa_cat1": 9_500, "tarifa_cat2": 15_600, "tarifa_cat3": 13_200,
     "tarifa_cat4": 19_000, "tarifa_cat5": 28_500, "administrado_por": "INVIAS"},

    {"nombre": "Peaje Pereira (Variante)", "departamento": "Risaralda", "municipio": "Pereira",
     "corredor": "Cali-Pereira-Medellín", "lat": 4.8133, "lon": -75.6961,
     "tarifa_cat1": 9_500, "tarifa_cat2": 15_600, "tarifa_cat3": 13_200,
     "tarifa_cat4": 19_000, "tarifa_cat5": 28_500, "administrado_por": "INVIAS"},

    # ── Llanos Orientales (Bogotá–Villavicencio) ─────────────────────────────
    {"nombre": "Peaje El Tablón (Villavicencio)", "departamento": "Cundinamarca",
     "municipio": "Cáqueza", "corredor": "Bogotá-Villavicencio",
     "lat": 4.4112, "lon": -73.9500,
     "tarifa_cat1": 14_300, "tarifa_cat2": 23_400, "tarifa_cat3": 19_900,
     "tarifa_cat4": 28_600, "tarifa_cat5": 42_900, "administrado_por": "Concesión Vial Autopistas del Llano"},

    {"nombre": "Peaje Pipiral", "departamento": "Meta", "municipio": "El Calvario",
     "corredor": "Bogotá-Villavicencio", "lat": 4.2765, "lon": -73.6289,
     "tarifa_cat1": 14_300, "tarifa_cat2": 23_400, "tarifa_cat3": 19_900,
     "tarifa_cat4": 28_600, "tarifa_cat5": 42_900, "administrado_por": "Concesión Vial Autopistas del Llano"},
]


async def seed_peajes(db) -> int:
    """
    Inserta los peajes semilla si la tabla está vacía.
    Retorna el número de filas insertadas.
    """
    from app.models.transporte import PeajeNacional

    existing = db.query(PeajeNacional).count()
    if existing > 0:
        return 0

    for p in PEAJES_SEED:
        db.add(PeajeNacional(
            nombre=p["nombre"],
            departamento=p["departamento"],
            municipio=p.get("municipio"),
            corredor=p.get("corredor"),
            lat=p.get("lat"),
            lon=p.get("lon"),
            tarifa_cat1=p["tarifa_cat1"],
            tarifa_cat2=p["tarifa_cat2"],
            tarifa_cat3=p["tarifa_cat3"],
            tarifa_cat4=p.get("tarifa_cat4"),
            tarifa_cat5=p.get("tarifa_cat5"),
            administrado_por=p.get("administrado_por"),
            vigente_desde=date(2024, 1, 1),
        ))
    db.commit()
    return len(PEAJES_SEED)


async def seed_precios_iniciales(db) -> None:
    """Inserta precios de combustible de referencia si la tabla está vacía."""
    from app.models.transporte import PrecioCombustible
    from app.services.sicom import PRECIOS_REFERENCIA

    existing = db.query(PrecioCombustible).count()
    if existing > 0:
        return

    today = date.today()
    for tipo, precio in PRECIOS_REFERENCIA.items():
        db.add(PrecioCombustible(
            tipo=tipo,
            precio_litro=precio,
            departamento="HUILA",
            fecha_vigencia=today,
            fuente="Referencia inicial SICOM 2026-Q1",
        ))
    db.commit()
