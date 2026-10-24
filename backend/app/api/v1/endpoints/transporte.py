"""
API de Costos de Transporte — Prácticas Extramuros USCO
Integra: SICOM (precios combustible), OpenRouteService (rutas), INVIAS/ANI (peajes).
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.db.database import get_db
from app.models.user import User
from app.models.practica import Practica
from app.models.transporte import PrecioCombustible, PeajeNacional
from app.api.deps import get_current_user
from app.services.ors_client import calcular_ruta, distancia_punto_a_ruta
from app.services.geocoder_co import distancia_entre_municipios, geocode_local, haversine_km
from app.services.colombia_geo import get_departamentos, get_municipios

router = APIRouter()

# ─── Rendimiento de vehículos (km/litro) ──────────────────────────────────────
RENDIMIENTO = {"bus": 8.5, "camioneta": 11.0, "moto": 35.0}
TARIFA_CONDUCTOR_DIA = 180_000   # COP
SEGURO_PASAJERO = 15_000         # COP por estudiante
RADIO_PEAJE_KM = 5.0             # Radio (km) para detectar peajes en la ruta


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _precio_combustible_actual(db: Session, tipo: str = "diesel") -> tuple[float, str, str]:
    """Retorna (precio_litro, fuente, fecha) del combustible más reciente en DB."""
    row = (
        db.query(PrecioCombustible)
        .filter(PrecioCombustible.tipo == tipo, PrecioCombustible.departamento == "HUILA")
        .order_by(PrecioCombustible.fecha_vigencia.desc())
        .first()
    )
    if row:
        return float(row.precio_litro), row.fuente, str(row.fecha_vigencia)
    fallback = {"gasolina_corriente": 15_978.0, "diesel": 12_721.0, "gasolina_extra": 19_387.0}
    return fallback.get(tipo, 10_280.0), "Referencia interna", str(date.today())


def _detectar_peajes_ruta(
    db: Session,
    coords: list[list[float]] | None,
    municipios: list[str],
    categoria: int = 3,
) -> tuple[list[dict], str]:
    """
    Detecta los peajes en la ruta. Devuelve (lista_peajes, metodo_usado).

    Métodos (en orden de precisión):
    1. ORS: proximidad geográfica a la polilínea real (< RADIO_PEAJE_KM).
    2. Triangular offline: dist(O,P) + dist(P,D) ≤ dist(O,D) × 1.35
       usando la tabla interna de coordenadas de ciudades colombianas.
    3. Municipio: coincidencia de nombre como último recurso.
    """
    peajes_db = db.query(PeajeNacional).filter(PeajeNacional.is_active == True).all()
    resultado: list[dict] = []

    tarifa_field = {1: "tarifa_cat1", 2: "tarifa_cat2", 3: "tarifa_cat3",
                   4: "tarifa_cat4", 5: "tarifa_cat5"}.get(categoria, "tarifa_cat3")

    if coords:
        # ── Método 1: polilínea ORS (máxima precisión) ───────────────────────
        for peaje in peajes_db:
            if peaje.lat is None or peaje.lon is None:
                continue
            dist = distancia_punto_a_ruta(peaje.lat, peaje.lon, coords)
            if dist <= RADIO_PEAJE_KM:
                tarifa = getattr(peaje, tarifa_field) or peaje.tarifa_cat3
                resultado.append({
                    "id": peaje.id,
                    "nombre": peaje.nombre,
                    "departamento": peaje.departamento,
                    "municipio": peaje.municipio,
                    "corredor": peaje.corredor,
                    "tarifa_cop": tarifa,
                    "distancia_ruta_km": round(dist, 1),
                })
        return resultado, "geográfico (ORS)"

    # ── Sin ORS: intentar detección triangular offline ────────────────────────
    origen  = municipios[0].split(",")[0].strip() if municipios else ""
    destino = municipios[1].split(",")[0].strip() if len(municipios) > 1 else ""
    coords_o = geocode_local(origen)  if origen  else None
    coords_d = geocode_local(destino) if destino else None

    if coords_o and coords_d:
        # ── Método 2: criterio triangular ─────────────────────────────────
        lat_o, lon_o = coords_o
        lat_d, lon_d = coords_d
        dist_od = haversine_km(lat_o, lon_o, lat_d, lon_d)
        # Un peaje está "en el trayecto" si no alarga el recorrido más del 35%
        # respecto a la distancia haversine directa (misma tasa que factor_ruta).
        umbral = dist_od * 1.35

        for peaje in peajes_db:
            if peaje.lat is None or peaje.lon is None:
                continue
            dist_op = haversine_km(lat_o, lon_o, peaje.lat, peaje.lon)
            dist_pd = haversine_km(peaje.lat, peaje.lon, lat_d, lon_d)
            if dist_op + dist_pd <= umbral:
                tarifa = getattr(peaje, tarifa_field) or peaje.tarifa_cat3
                resultado.append({
                    "id": peaje.id,
                    "nombre": peaje.nombre,
                    "departamento": peaje.departamento,
                    "municipio": peaje.municipio,
                    "corredor": peaje.corredor,
                    "tarifa_cop": tarifa,
                    "distancia_ruta_km": round(dist_op, 1),
                })
        resultado.sort(key=lambda x: x["distancia_ruta_km"])
        return resultado, "geográfico offline (sin ORS)"

    # ── Método 3: coincidencia de municipio (fallback final) ────────────────
    muni_lower = [m.lower().strip() for m in municipios if m]
    for peaje in peajes_db:
        ref = (peaje.municipio or "").lower()
        if any(ref in m or m in ref for m in muni_lower if ref):
            tarifa = getattr(peaje, tarifa_field) or peaje.tarifa_cat3
            resultado.append({
                "id": peaje.id,
                "nombre": peaje.nombre,
                "departamento": peaje.departamento,
                "municipio": peaje.municipio,
                "corredor": peaje.corredor,
                "tarifa_cop": tarifa,
                "distancia_ruta_km": None,
            })
    return resultado, "por municipio (ciudades no encontradas en tabla offline)"


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/combustible/precios")
def precios_combustible(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Precios actuales de combustible (actualizados diariamente desde SICOM)."""
    filas = (
        db.query(PrecioCombustible)
        .filter(PrecioCombustible.departamento == "HUILA")
        .order_by(PrecioCombustible.fecha_vigencia.desc())
        .limit(10)
        .all()
    )
    # Uno más reciente por tipo
    por_tipo: dict[str, PrecioCombustible] = {}
    for f in filas:
        if f.tipo not in por_tipo:
            por_tipo[f.tipo] = f

    return {
        "departamento": "HUILA",
        "precios": [
            {
                "tipo": t,
                "precio_litro_cop": float(row.precio_litro) if row.precio_litro is not None else None,
                "fecha_vigencia": str(row.fecha_vigencia),
                "fuente": row.fuente,
                "actualizado_en": row.actualizado_en.isoformat() if row.actualizado_en else None,
            }
            for t, row in por_tipo.items()
        ],
        "nota": "Precios vigentes para Huila. Actualizados cada 24 h desde SICOM.",
    }


@router.get("/peajes")
def listar_peajes(
    departamento: Optional[str] = Query(None),
    corredor: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Lista todos los peajes activos, con filtros opcionales por departamento o corredor."""
    q = db.query(PeajeNacional).filter(PeajeNacional.is_active == True)
    if departamento:
        q = q.filter(PeajeNacional.departamento.ilike(f"%{departamento}%"))
    if corredor:
        q = q.filter(PeajeNacional.corredor.ilike(f"%{corredor}%"))
    peajes = q.order_by(PeajeNacional.departamento, PeajeNacional.nombre).all()
    return [
        {
            "id": p.id,
            "nombre": p.nombre,
            "departamento": p.departamento,
            "municipio": p.municipio,
            "corredor": p.corredor,
            "lat": p.lat,
            "lon": p.lon,
            "tarifas": {
                "cat1_auto": p.tarifa_cat1,
                "cat2_bus_liviano": p.tarifa_cat2,
                "cat3_bus_pesado": p.tarifa_cat3,
                "cat4_camion_2ejes": p.tarifa_cat4,
                "cat5_camion_3ejes": p.tarifa_cat5,
            },
            "administrado_por": p.administrado_por,
            "vigente_desde": str(p.vigente_desde) if p.vigente_desde else None,
        }
        for p in peajes
    ]


class CalcularRutaRequest(BaseModel):
    origen: str
    destino: str
    tipo_vehiculo: str = "bus"       # bus | camioneta | moto
    num_vehiculos: int = 1
    categoria_peaje: int = 3          # 1-5
    tipo_combustible: str = "diesel"  # diesel | gasolina_corriente


@router.post("/rutas/calcular")
async def calcular_ruta_endpoint(
    body: CalcularRutaRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Calcula el costo estimado de un trayecto origen–destino.

    Usa OpenRouteService para distancia/ruta real (requiere ORS_API_KEY en .env).
    Si ORS no está configurado, solo devuelve costos básicos sin ruta exacta.
    """
    # 1. Ruta con ORS (async)
    ruta_ors = await calcular_ruta(body.origen, body.destino)

    # 2. Precio combustible
    precio_litro, fuente_precio, fecha_precio = _precio_combustible_actual(
        db, body.tipo_combustible
    )

    # 3. Distancia
    km_ida = ruta_ors["distancia_km"] if ruta_ors else None
    km_ida_vuelta = (km_ida * 2) if km_ida else None
    duracion_min = ruta_ors["duracion_min"] if ruta_ors else None

    # 4. Peajes
    coords = ruta_ors["coordenadas"] if ruta_ors else None
    peajes, metodo_peajes = _detectar_peajes_ruta(db, coords, [body.origen, body.destino], body.categoria_peaje)
    costo_peajes_unitario = sum(p["tarifa_cop"] for p in peajes)
    costo_peajes_total = costo_peajes_unitario * 2 * body.num_vehiculos if km_ida else None

    # 5. Combustible
    rendimiento = RENDIMIENTO.get(body.tipo_vehiculo, 8.5)
    if km_ida_vuelta:
        litros = (km_ida_vuelta / rendimiento) * body.num_vehiculos
        costo_combustible = round(litros * precio_litro)
    else:
        litros = None
        costo_combustible = None

    total = None
    if costo_combustible is not None and costo_peajes_total is not None:
        total = costo_combustible + costo_peajes_total

    return {
        "origen": body.origen,
        "destino": body.destino,
        "ruta": {
            "distancia_km_ida": km_ida,
            "distancia_km_ida_vuelta": km_ida_vuelta,
            "duracion_min": duracion_min,
            "fuente": "OpenRouteService" if ruta_ors else "No disponible (configure ORS_API_KEY)",
        },
        "combustible": {
            "tipo": body.tipo_combustible,
            "rendimiento_km_litro": rendimiento,
            "litros_estimados": round(litros, 1) if litros else None,
            "precio_litro_cop": precio_litro,
            "costo_cop": costo_combustible,
            "fuente_precio": fuente_precio,
            "fecha_precio": fecha_precio,
        },
        "peajes": {
            "categoria_vehiculo": body.categoria_peaje,
            "num_peajes": len(peajes),
            "detalle": peajes,
            "costo_unitario_cop": costo_peajes_unitario,
            "costo_total_cop": costo_peajes_total,
            "metodo_deteccion": metodo_peajes,
        },
        "resumen": {
            "num_vehiculos": body.num_vehiculos,
            "costo_combustible_cop": costo_combustible,
            "costo_peajes_cop": costo_peajes_total,
            "total_estimado_cop": total,
        },
        "nota": "Costos estimados basados en precios SICOM e INVIAS. Requieren aprobación del encargado de gastos.",
    }


# ─── Endpoint: calcular y guardar distancias entre puntos de ruta ─────────────

class CalcularDistanciasResponse(BaseModel):
    practica_id: int
    rutas_actualizadas: int
    distancias: list[dict]
    metodo: str
    advertencias: list[str]


@router.post("/rutas/{practica_id}/calcular-distancias", summary="Calcula y guarda distancias entre waypoints de la práctica")
async def calcular_distancias_practica(
    practica_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Geocodifica los municipios de cada segmento de ruta y calcula la distancia vial estimada.
    - Intenta ORS primero (si hay API key configurada).
    - Fallback: haversine × 1.35 con tabla interna de ciudades colombianas.
    Guarda el resultado en RutaPractica.distancia_km.
    """
    from app.models.practica import RutaPractica
    pr = db.query(Practica).options(joinedload(Practica.rutas)).filter(Practica.id == practica_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="Práctica no encontrada")

    rutas = sorted(pr.rutas, key=lambda r: r.orden)
    if not rutas:
        raise HTTPException(status_code=422, detail="La práctica no tiene rutas registradas")

    actualizadas = 0
    advertencias: list[str] = []
    distancias_out: list[dict] = []
    metodo_global = "geocoder_interno"

    # Calcular distancia entre cada par consecutivo de waypoints
    for i in range(len(rutas) - 1):
        seg_a = rutas[i]
        seg_b = rutas[i + 1]

        ciudad_a = seg_a.municipio or seg_a.lugar or ""
        ciudad_b = seg_b.municipio or seg_b.lugar or ""
        dept_a = seg_a.departamento or ""
        dept_b = seg_b.departamento or ""

        km = None

        # 1. Intentar ORS si hay API key
        try:
            ruta_ors = await calcular_ruta(ciudad_a, ciudad_b)
            if ruta_ors:
                km = ruta_ors["distancia_km"]
                metodo_global = "OpenRouteService"
        except Exception:
            pass

        # 2. Fallback: geocoder interno con haversine
        if km is None:
            km = distancia_entre_municipios(ciudad_a, ciudad_b, dept_a, dept_b)

        if km is not None:
            # Guardar en el segmento de destino (seg_b recibe la distancia desde seg_a)
            db_ruta = db.query(RutaPractica).filter(RutaPractica.id == seg_b.id).first()
            if db_ruta:
                db_ruta.distancia_km = km
                actualizadas += 1
            distancias_out.append({
                "de": ciudad_a,
                "a": ciudad_b,
                "distancia_km": km,
            })
        else:
            advertencias.append(
                f"No se pudo geocodificar el tramo '{ciudad_a}' → '{ciudad_b}'. "
                "Ingrese la distancia manualmente."
            )
            distancias_out.append({"de": ciudad_a, "a": ciudad_b, "distancia_km": None})

    db.commit()
    return {
        "practica_id": practica_id,
        "rutas_actualizadas": actualizadas,
        "distancias": distancias_out,
        "metodo": metodo_global,
        "advertencias": advertencias,
    }


# Mapa vehículo → combustible por defecto
_COMBUSTIBLE_VEHICULO = {
    "bus": "diesel",
    "camioneta": "gasolina_corriente",
    "moto": "gasolina_corriente",
}


@router.get("/costos/{practica_id}")
async def calcular_costos_practica(
    practica_id: int,
    tipo_vehiculo: str = "bus",
    num_vehiculos: int = 1,
    categoria_peaje: int = 3,
    tipo_combustible: str = "",   # si viene vacío se auto-deriva del tipo_vehiculo
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Calcula el costo estimado de transporte para una práctica extramural registrada."""
    from app.models.practica import RutaPractica
    pr = db.query(Practica).options(joinedload(Practica.rutas)).filter(Practica.id == practica_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="Práctica no encontrada")

    rutas = sorted(pr.rutas, key=lambda r: r.orden)
    if not rutas:
        raise HTTPException(status_code=422, detail="La práctica no tiene rutas registradas")

    # ── Auto-calcular distancias faltantes con geocoder interno ───────────────
    distancias_auto = []
    for i in range(len(rutas) - 1):
        seg_a, seg_b = rutas[i], rutas[i + 1]
        if seg_b.distancia_km is None or seg_b.distancia_km == 0:
            ciudad_a = seg_a.municipio or seg_a.lugar or ""
            ciudad_b = seg_b.municipio or seg_b.lugar or ""
            dept_a = seg_a.departamento or ""
            dept_b = seg_b.departamento or ""
            km = distancia_entre_municipios(ciudad_a, ciudad_b, dept_a, dept_b)
            if km:
                # Persistir para futuras consultas
                db_ruta = db.query(RutaPractica).filter(RutaPractica.id == seg_b.id).first()
                if db_ruta:
                    db_ruta.distancia_km = km
                    seg_b.distancia_km = km  # actualizar objeto en memoria
                distancias_auto.append(f"{ciudad_a}→{ciudad_b}: {km} km (auto)")
    if distancias_auto:
        db.commit()

    km_total_ida = sum(float(r.distancia_km or 0) for r in rutas)

    if km_total_ida == 0:
        raise HTTPException(
            status_code=422,
            detail=(
                "No se pudo determinar la distancia de la ruta. "
                "Ingrese las distancias en km al crear o editar la práctica, "
                "o asegúrese de que los municipios coincidan con ciudades colombianas conocidas."
            ),
        )

    km_ida_vuelta = km_total_ida * 2

    # Precio combustible desde DB — auto-derivar tipo si no se especifica
    combustible = tipo_combustible or _COMBUSTIBLE_VEHICULO.get(tipo_vehiculo, "diesel")
    precio_litro, fuente_precio, fecha_precio = _precio_combustible_actual(db, combustible)

    rendimiento = RENDIMIENTO.get(tipo_vehiculo, 8.5)
    litros = (km_ida_vuelta / rendimiento) * num_vehiculos if km_ida_vuelta else 0
    costo_combustible = round(litros * precio_litro)

    municipios_ruta = [r.municipio or r.lugar or "" for r in rutas]
    origen_ruta  = next((m for m in municipios_ruta if m), "")
    destino_ruta = next((m for m in reversed(municipios_ruta) if m), "")
    peajes, _ = _detectar_peajes_ruta(db, None, [origen_ruta, destino_ruta], categoria_peaje)
    costo_peajes_total = sum(p["tarifa_cop"] for p in peajes) * 2 * num_vehiculos

    costo_conductor = TARIFA_CONDUCTOR_DIA * pr.duracion_dias * num_vehiculos
    costo_seguro = SEGURO_PASAJERO * pr.num_alumnos
    total = costo_combustible + costo_peajes_total + costo_conductor + costo_seguro

    return {
        "practica_id": practica_id,
        "nombre_practica": pr.nombre_practica,
        "periodo_academico": pr.periodo_academico,
        "parametros_calculo": {
            "tipo_vehiculo": tipo_vehiculo,
            "num_vehiculos": num_vehiculos,
            "km_total_ida": km_total_ida,
            "km_total_ida_vuelta": km_ida_vuelta,
            "litros_estimados": round(litros, 1),
            "precio_diesel_litro": precio_litro,
            "fuente_precio": fuente_precio,
            "fecha_precio": fecha_precio,
            "duracion_dias": pr.duracion_dias,
            "num_alumnos": pr.num_alumnos,
        },
        "desglose": {
            "combustible": {
                "descripcion": f"{combustible.replace('_', ' ').title()} — {km_ida_vuelta:.0f} km × {num_vehiculos} vehículo(s)",
                "litros": round(litros, 1),
                "valor_cop": costo_combustible,
            },
            "peajes": {
                "descripcion": f"{len(peajes)} peaje(s) × 2 trayectos × {num_vehiculos} vehículo(s)",
                "peajes_detectados": [p["nombre"] for p in peajes],
                "valor_cop": costo_peajes_total,
            },
            "conductor": {
                "descripcion": f"Conductor {pr.duracion_dias} día(s) × {num_vehiculos} vehículo(s)",
                "valor_cop": costo_conductor,
            },
            "seguro_pasajeros": {
                "descripcion": f"Seguro viaje — {pr.num_alumnos} estudiante(s)",
                "valor_cop": costo_seguro,
            },
        },
        "total_estimado_cop": total,
        "distancias_auto": distancias_auto,
        "nota": "Costos estimados. Requieren aprobación del encargado de gastos.",
    }


# ─── Endpoint: peajes detallados de una práctica ─────────────────────────────

@router.get("/peajes-ruta/{practica_id}", summary="Peajes detectados en la ruta de una práctica")
async def peajes_ruta_practica(
    practica_id: int,
    categoria_peaje: int = Query(3, description="Categoría INVIAS: 2=bus liviano, 3=bus pesado, 4=camión 2 ejes"),
    num_vehiculos: int = Query(1, ge=1, le=20),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Devuelve los peajes detectados en la ruta de una práctica extramural,
    con tarifa unitaria, costo de ida y vuelta, y total por número de vehículos.
    """
    pr = db.query(Practica).options(joinedload(Practica.rutas)).filter(Practica.id == practica_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="Práctica no encontrada")

    rutas = sorted(pr.rutas, key=lambda r: r.orden)
    if not rutas:
        raise HTTPException(status_code=422, detail="La práctica no tiene rutas registradas")

    municipios_ruta = [r.municipio or r.lugar or "" for r in rutas]
    origen = next((m for m in municipios_ruta if m), "")
    destino = next((m for m in reversed(municipios_ruta) if m), "")

    # Intentar con ORS para mayor precisión (coords reales)
    ruta_ors = await calcular_ruta(origen, destino)
    coords = ruta_ors["coordenadas"] if ruta_ors else None
    km_ida = ruta_ors["distancia_km"] if ruta_ors else None

    peajes, metodo = _detectar_peajes_ruta(db, coords, [origen, destino], categoria_peaje)

    tarifa_field = {1: "tarifa_cat1", 2: "tarifa_cat2", 3: "tarifa_cat3",
                   4: "tarifa_cat4", 5: "tarifa_cat5"}.get(categoria_peaje, "tarifa_cat3")

    detalle_peajes = [
        {
            "nombre": p["nombre"],
            "departamento": p["departamento"],
            "municipio": p["municipio"],
            "corredor": p["corredor"],
            "tarifa_unitaria_cop": p["tarifa_cop"],
            "costo_ida_cop": p["tarifa_cop"] * num_vehiculos,
            "costo_ida_vuelta_cop": p["tarifa_cop"] * 2 * num_vehiculos,
            "distancia_desde_ruta_km": p.get("distancia_ruta_km"),
        }
        for p in peajes
    ]

    total_peajes = sum(p["tarifa_cop"] for p in peajes) * 2 * num_vehiculos

    return {
        "practica_id": practica_id,
        "nombre_practica": pr.nombre_practica,
        "ruta_resumen": f"{origen} → {destino}",
        "km_ida": km_ida,
        "km_ida_vuelta": (km_ida * 2) if km_ida else None,
        "parametros": {
            "categoria_peaje": categoria_peaje,
            "num_vehiculos": num_vehiculos,
            "metodo_deteccion": metodo,
        },
        "num_peajes": len(detalle_peajes),
        "peajes": detalle_peajes,
        "costo_total_peajes_cop": total_peajes,
        "nota": (
            f"Peajes detectados mediante '{metodo}'. "
            "Para mayor precisión configure ORS_API_KEY en el servidor."
            if not coords else
            f"Peajes detectados por proximidad geográfica real (ORS). Ruta: {km_ida:.1f} km de ida."
        ),
    }


# ─── Endpoints Geo: Departamentos / Municipios / Distancia ────────────────────

@router.get("/geo/departamentos", summary="Lista los departamentos de Colombia")
def listar_departamentos(_: User = Depends(get_current_user)):
    """Retorna la lista ordenada de los 33 departamentos de Colombia."""
    return {"departamentos": get_departamentos()}


@router.get("/geo/municipios", summary="Lista los municipios de un departamento")
def listar_municipios(
    departamento: str = Query(..., description="Nombre exacto del departamento"),
    _: User = Depends(get_current_user),
):
    """Retorna los municipios del departamento especificado (DIVIPOLA 2024)."""
    municipios = get_municipios(departamento)
    if not municipios:
        raise HTTPException(status_code=404, detail=f"Departamento '{departamento}' no encontrado")
    return {"departamento": departamento, "municipios": municipios}


class DistanciaGeoRequest(BaseModel):
    origen_municipio: str
    origen_departamento: str
    destino_municipio: str
    destino_departamento: str


@router.post("/geo/distancia", summary="Calcula la distancia vial entre dos municipios")
async def calcular_distancia_geo(
    body: DistanciaGeoRequest,
    _: User = Depends(get_current_user),
):
    """
    Calcula la distancia vial estimada entre dos municipios colombianos.
    - Usa OpenRouteService (si ORS_API_KEY está configurado) para distancia real.
    - Fallback: haversine × 1.35 con tabla interna de ~200 municipios.
    Retorna {distancia_km, metodo}.
    """
    origen_str = f"{body.origen_municipio}, {body.origen_departamento}"
    destino_str = f"{body.destino_municipio}, {body.destino_departamento}"

    # 1. Intentar ORS (distancia real por carretera)
    try:
        ruta_ors = await calcular_ruta(origen_str, destino_str)
        if ruta_ors and ruta_ors.get("distancia_km"):
            return {
                "distancia_km": ruta_ors["distancia_km"],
                "metodo": "OpenRouteService",
                "origen": origen_str,
                "destino": destino_str,
            }
    except Exception:
        pass

    # 2. Fallback: geocoder interno (haversine × factor_ruta)
    km = distancia_entre_municipios(
        body.origen_municipio, body.destino_municipio,
        body.origen_departamento, body.destino_departamento,
    )
    if km:
        return {
            "distancia_km": km,
            "metodo": "geocoder_interno",
            "origen": origen_str,
            "destino": destino_str,
        }

    return {
        "distancia_km": None,
        "metodo": "no_disponible",
        "origen": origen_str,
        "destino": destino_str,
        "advertencia": (
            f"No se encontraron coordenadas para '{body.origen_municipio}' o "
            f"'{body.destino_municipio}'. Ingrese la distancia manualmente."
        ),
    }


@router.get("/parametros")
def parametros_transporte(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Parámetros generales: precios combustible, rendimientos y constantes."""
    gc, _, _ = _precio_combustible_actual(db, "gasolina_corriente")
    diesel, fuente, fecha = _precio_combustible_actual(db, "diesel")
    extra, _, _ = _precio_combustible_actual(db, "gasolina_extra")
    total_peajes = db.query(PeajeNacional).filter(PeajeNacional.is_active == True).count()
    return {
        "combustible": {
            "gasolina_corriente_cop_litro": gc,
            "diesel_cop_litro": diesel,
            "gasolina_extra_cop_litro": extra,
            "fuente": fuente,
            "fecha_actualizacion": fecha,
        },
        "rendimientos_km_litro": RENDIMIENTO,
        "otros": {
            "tarifa_conductor_dia_cop": TARIFA_CONDUCTOR_DIA,
            "seguro_por_pasajero_cop": SEGURO_PASAJERO,
        },
        "base_datos_peajes": {
            "total_activos": total_peajes,
            "fuente": "INVIAS / ANI 2024-2025",
        },
    }
