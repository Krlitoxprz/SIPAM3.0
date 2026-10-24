"""
FASTAPI-01 — AI prediction proxy endpoint.
Forwards requests to the Flask AI microservice on port 5001.
Also provides /recomendaciones endpoint (DB + AI hybrid scoring).
"""
import os
import asyncio
import httpx
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db
from app.models.user import User, RolEnum

router = APIRouter()

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:5001")
_TIMEOUT = 10.0       # endpoints de métricas/explicaciones (no crítico para UX)
_TIMEOUT_RECOM = 3.0  # recomendaciones (user-facing): falla rápido → fallback heurístico


class PredictRequest(BaseModel):
    promedio: float             = Field(..., ge=0.0, le=5.0)
    porcentaje_creditos: float  = Field(..., ge=0.0, le=100.0)
    nota_asignatura: float      = Field(..., ge=0.0, le=5.0)
    nota_entrevista: float      = Field(3.5, ge=0.0, le=5.0)
    tipo_monitoria: str         = Field("academica_cursos")
    semestre_asignatura: int    = Field(4, ge=1, le=12)
    creditos_asignatura: int    = Field(3, ge=1, le=10)
    num_postulantes: int        = Field(6, ge=1, le=100)
    num_monitores_requeridos: int = Field(1, ge=1, le=10)


class PredictResponse(BaseModel):
    selected_probability: float
    prediction: str
    confidence: str
    model_used: str
    puntaje_estimado: float
    rank_estimado: int
    selection_ratio: float


@router.post(
    "/predecir",
    response_model=PredictResponse,
    summary="Predict monitor selection probability (AI microservice)",
)
async def predecir(
    body: PredictRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Forwards the request to the Flask AI microservice and returns the prediction.
    All authenticated users may call this endpoint.
    """
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        try:
            resp = await client.post(
                f"{AI_SERVICE_URL}/predict",
                json=body.model_dump(),
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="AI service unavailable. Make sure Flask is running on port 5001.",
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="AI service timed out.",
            )

    if resp.status_code == 422:
        raise HTTPException(status_code=422, detail=resp.json())
    if resp.status_code != 200:
        raise HTTPException(
            status_code=resp.status_code,
            detail=resp.json().get("error", "AI service error"),
        )

    return resp.json()


@router.post(
    "/explicar",
    summary="Prediction + SHAP explanation of top contributing features",
)
async def explicar(
    body: PredictRequest,
    current_user: User = Depends(get_current_user),
):
    """Calls Flask /predict/explain and returns prediction + SHAP top features."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(
                f"{AI_SERVICE_URL}/predict/explain",
                json=body.model_dump(),
            )
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="AI service unavailable.")
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="AI service timed out.")
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())
    return resp.json()


@router.get(
    "/metricas",
    summary="Get trained model metrics (accuracy, F1, AUC per model)",
)
async def metricas(current_user: User = Depends(get_current_user)):
    """Returns training and test metrics for all 3 ML models."""
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        try:
            resp = await client.get(f"{AI_SERVICE_URL}/models/metrics")
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="AI service unavailable.")
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="AI service timed out.")
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())
    return resp.json()


@router.get(
    "/feature-importance",
    summary="Get feature importances from the best model",
)
async def feature_importance(current_user: User = Depends(get_current_user)):
    """Returns feature importances (only available for tree-based models)."""
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        try:
            resp = await client.get(f"{AI_SERVICE_URL}/models/feature-importance")
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="AI service unavailable.")
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="AI service timed out.")
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())
    return resp.json()


# ── Helpers internos ──────────────────────────────────────────────────────────

async def _ai_probabilidad(
    client: httpx.AsyncClient,
    promedio: float, pct_creditos: float,
    tipo_monitoria: str, semestre: int, creditos: int,
    num_postulantes: int, num_requeridos: int,
):
    """Llama al Flask AI service; retorna None si no está disponible."""
    try:
        resp = await client.post(
            f"{AI_SERVICE_URL}/predict",
            json={
                "promedio": promedio,
                "porcentaje_creditos": pct_creditos,
                "nota_asignatura": promedio,
                "nota_entrevista": 3.5,
                "tipo_monitoria": tipo_monitoria,
                "semestre_asignatura": semestre,
                "creditos_asignatura": creditos,
                "num_postulantes": max(num_postulantes, 1),
                "num_monitores_requeridos": max(num_requeridos, 1),
            },
            timeout=_TIMEOUT_RECOM,
        )
        if resp.status_code == 200:
            return resp.json().get("selected_probability")
    except Exception:
        pass
    return None


def _heuristica(
    promedio: float, pct_creditos: float,
    req_promedio: float, req_pct: float,
    num_postulantes: int, num_requeridos: int,
) -> float:
    """Score heurístico [0-1] si el servicio IA no está disponible."""
    denom_p = max(5.0 - req_promedio, 0.01)
    denom_c = max(100.0 - req_pct, 0.01)
    margen_p = min((promedio - req_promedio) / denom_p, 1.0)
    margen_c = min((pct_creditos - req_pct) / denom_c, 1.0)
    ratio = min(num_requeridos / max(num_postulantes, 1), 1.0)
    return round(margen_p * 0.35 + margen_c * 0.15 + ratio * 0.50, 4)


# ── Recomendaciones ───────────────────────────────────────────────────────────

@router.get(
    "/recomendaciones",
    summary="Convocatorias recomendadas para el estudiante actual (AI scoring)",
)
async def recomendaciones(
    limite: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Devuelve las convocatorias abiertas ordenadas por probabilidad de selección
    estimada por el modelo IA (con fallback heurístico si el servicio no está disponible).
    Solo disponible para rol estudiante.
    """
    from app.models.convocatoria import Convocatoria, EstadoConvocatoriaEnum
    from app.models.postulacion import Postulacion

    if current_user.rol != RolEnum.estudiante:
        raise HTTPException(status_code=403, detail="Solo disponible para estudiantes.")

    ahora = datetime.now(timezone.utc)
    convs = (
        db.query(Convocatoria)
        .options(joinedload(Convocatoria.asignatura), joinedload(Convocatoria.profesor))
        .filter(
            Convocatoria.estado == EstadoConvocatoriaEnum.abierta,
            Convocatoria.fecha_fin_postulacion >= ahora,
        )
        .all()
    )

    ya_postuladas = {
        p.convocatoria_id
        for p in db.query(Postulacion).filter_by(estudiante_id=current_user.id).all()
    }

    prom = float(current_user.promedio or 0)
    pct  = float(current_user.porcentaje_creditos or 0)

    elegibles = []
    for c in convs:
        if c.id in ya_postuladas:
            continue
        req_p = float(c.promedio_minimo or 3.5)
        req_c = float(c.creditos_minimo_pct or 30.0)
        if prom < req_p or pct < req_c:
            continue
        elegibles.append(c)

    if not elegibles:
        return {"recomendaciones": [], "total_elegibles": 0, "fuente": "sin_datos"}

    n_posts = {
        c.id: db.query(Postulacion).filter_by(convocatoria_id=c.id).count()
        for c in elegibles
    }

    async with httpx.AsyncClient(timeout=_TIMEOUT_RECOM) as client:
        tasks = [
            _ai_probabilidad(
                client, prom, pct,
                c.tipo_monitoria.value,
                c.asignatura.semestre if c.asignatura else 4,
                c.asignatura.creditos if c.asignatura else 3,
                n_posts[c.id], c.num_monitores_requeridos or 1,
            )
            for c in elegibles
        ]
        probs = await asyncio.gather(*tasks)

    fuente = "heuristica"
    results = []
    for conv, prob in zip(elegibles, probs):
        req_p = float(conv.promedio_minimo or 3.5)
        req_c = float(conv.creditos_minimo_pct or 30.0)
        if prob is None:
            score = _heuristica(prom, pct, req_p, req_c, n_posts[conv.id], conv.num_monitores_requeridos or 1)
        else:
            score = round(prob, 4)
            fuente = "modelo_ia"

        programa_match = bool(
            current_user.programa and conv.asignatura
            and conv.asignatura.programa == current_user.programa
        )
        fp = conv.fecha_fin_postulacion
        if fp and fp.tzinfo is None:
            fp = fp.replace(tzinfo=timezone.utc)
        dias_restantes = (fp - ahora).days if fp else 0

        results.append({
            "convocatoria_id": conv.id,
            "titulo": conv.titulo,
            "asignatura": conv.asignatura.nombre if conv.asignatura else "—",
            "programa": conv.asignatura.programa if conv.asignatura else "—",
            "tipo_monitoria": conv.tipo_monitoria.value,
            "sede": conv.sede or "Neiva",
            "fecha_cierre": conv.fecha_fin_postulacion.isoformat() if conv.fecha_fin_postulacion else None,
            "dias_restantes": max(dias_restantes, 0),
            "horas_semana": conv.horas_semana,
            "promedio_minimo": req_p,
            "docente": f"{conv.profesor.nombres} {conv.profesor.apellidos}" if conv.profesor else "—",
            "num_postulantes": n_posts[conv.id],
            "num_requeridos": conv.num_monitores_requeridos or 1,
            "probabilidad_pct": round(score * 100, 1),
            "programa_match": programa_match,
        })

    results.sort(key=lambda x: (x["programa_match"], x["probabilidad_pct"]), reverse=True)

    return {
        "recomendaciones": results[:limite],
        "total_elegibles": len(results),
        "fuente": fuente,
    }
