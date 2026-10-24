"""
Cliente SICOM — Sistema de Información de Combustibles
Ministerio de Minas y Energía de Colombia.
Obtiene precios vigentes de combustibles líquidos por departamento.
"""
import logging
import httpx
from datetime import date

logger = logging.getLogger(__name__)

SICOM_BASE = "https://eds.sicom.gov.co/eds/api/v1"

# Precios de referencia Huila Q1-2026 (fallback cuando SICOM no responde)
# Fuente: SICOM/MME — vigentes año 2026 tras reducción progresiva de subsidios
PRECIOS_REFERENCIA: dict[str, float] = {
    "gasolina_corriente": 15_978.0,
    "diesel":             12_721.0,
    "gasolina_extra":     19_387.0,
}


async def fetch_precios_departamento(departamento: str = "HUILA") -> dict[str, float] | None:
    """
    Consulta precios actuales de combustible desde SICOM.
    Devuelve dict {tipo: precio_litro} o None si el servicio no responde.
    """
    endpoints = [
        f"{SICOM_BASE}/birest/consultar-precio-departamento",
        f"{SICOM_BASE}/birest/precios",
    ]
    params_variants = [
        {"departamento": departamento},
        {"departamento": departamento, "tipoCombustible": "GASOLINA_CORRIENTE"},
    ]

    for url in endpoints:
        for params in params_variants:
            try:
                async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
                    r = await client.get(url, params=params,
                                         headers={"Accept": "application/json"})
                    if r.status_code == 200:
                        raw = r.json()
                        items = raw if isinstance(raw, list) else [raw]
                        precios: dict[str, float] = {}
                        for item in items:
                            tipo_raw = str(item.get("tipoCombustible", "")
                                          or item.get("tipo", "")).lower()
                            precio = item.get("precioLitro") or item.get("precio")
                            if not precio or not tipo_raw:
                                continue
                            precio = float(precio)
                            if "corriente" in tipo_raw or "regular" in tipo_raw:
                                precios["gasolina_corriente"] = precio
                            elif "acpm" in tipo_raw or "diesel" in tipo_raw:
                                precios["diesel"] = precio
                            elif "extra" in tipo_raw or "premium" in tipo_raw:
                                precios["gasolina_extra"] = precio
                        if precios:
                            logger.info(f"SICOM precios obtenidos para {departamento}: {precios}")
                            return precios
            except Exception as exc:
                logger.debug(f"SICOM {url} falló: {exc}")

    logger.warning("SICOM no disponible; se usarán precios de referencia.")
    return None


def get_precios_fallback() -> dict[str, float]:
    """Precios de referencia cuando SICOM no está disponible."""
    return dict(PRECIOS_REFERENCIA)
