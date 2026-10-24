import os
import logging
import warnings
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from app.core.config import settings
from app.api.v1.router import api_router
from app.db.database import init_db, SessionLocal

# Importar nuevos modelos para que init_db los registre en Base.metadata
import app.models.historial_estado  # noqa: F401
import app.models.evaluacion_monitor  # noqa: F401
import app.models.password_reset  # noqa: F401
import app.models.pago_viatico  # noqa: F401

logger = logging.getLogger(__name__)


def _build_scheduler() -> AsyncIOScheduler:
    """Crea el scheduler con SQLAlchemy JobStore cuando sea posible.

    En producción multi-worker, el JobStore de PostgreSQL actúa como lock
    distribuido: solo el primer worker que tome el job lo ejecuta, evitando
    que se dispare N veces (una por worker).
    """
    try:
        from app.db.database import engine
        jobstores = {"default": SQLAlchemyJobStore(engine=engine)}
        return AsyncIOScheduler(
            jobstores=jobstores,
            timezone="America/Bogota",
        )
    except Exception:
        return AsyncIOScheduler(timezone="America/Bogota")


scheduler = _build_scheduler()

_DEFAULT_SECRET = "sipam-usco-super-secret-key-2024-change-in-production"


def _ensure_admin() -> None:
    """Crea el superusuario administrador si todavía no existe en la BD."""
    from app.models.user import User, RolEnum
    from app.core.security import get_password_hash

    db = SessionLocal()
    try:
        if not db.query(User).filter(User.codigo == "Krlitoxprz").first():
            admin = User(
                codigo="Krlitoxprz",
                nombres="Administrador",
                apellidos="SIPAM",
                email="admin.sipam@usco.edu.co",
                cedula="00000001",
                hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                rol=RolEnum.admin,
                is_active=True,
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()


async def _seed_transporte() -> None:
    """Siembra peajes y precios iniciales de combustible si las tablas están vacías."""
    from app.services.transporte_seed import seed_peajes, seed_precios_iniciales

    db = SessionLocal()
    try:
        n = await seed_peajes(db)
        if n:
            logger.info(f"Transporte: {n} peajes sembrados.")
        await seed_precios_iniciales(db)
    finally:
        db.close()


async def _enviar_recordatorios() -> None:
    """Cron job diario: envía recordatorios de fechas límite próximas (SF-08)."""
    from app.models.convocatoria import Convocatoria, EstadoConvocatoriaEnum
    from app.models.user import User, RolEnum
    from app.models.postulacion import Postulacion
    from app.models.notificacion import Notificacion
    from app.services.email_service import send_email

    db = SessionLocal()
    try:
        ahora = datetime.now(timezone.utc).replace(tzinfo=None)
        en_3_dias = ahora + timedelta(days=3)

        # 1. Convocatorias que cierran en ≤3 días
        convs_cierre = db.query(Convocatoria).filter(
            Convocatoria.estado == EstadoConvocatoriaEnum.abierta,
            Convocatoria.fecha_fin_postulacion.isnot(None),
            Convocatoria.fecha_fin_postulacion <= en_3_dias,
            Convocatoria.fecha_fin_postulacion >= ahora,
        ).all()

        for conv in convs_cierre:
            dias = (conv.fecha_fin_postulacion - ahora).days + 1

            # Sub-query de estudiantes ya postulados — evita N+1 queries
            ya_postulados_ids = (
                db.query(Postulacion.estudiante_id)
                .filter(Postulacion.convocatoria_id == conv.id)
                .subquery()
            )

            # Una sola consulta: todos los elegibles que NO se han postulado
            candidatos = db.query(User).filter(
                User.rol == RolEnum.estudiante,
                User.is_active == True,
                User.promedio >= conv.promedio_minimo,
                User.porcentaje_creditos >= (conv.creditos_minimo_pct or 0.0),
                ~User.id.in_(ya_postulados_ids),
            ).all()

            for est in candidatos:
                db.add(Notificacion(
                    usuario_id=est.id,
                    titulo=f"⏰ Convocatoria cierra en {dias} día(s)",
                    mensaje=f"La convocatoria «{conv.titulo}» cierra el "
                            f"{conv.fecha_fin_postulacion.strftime('%d/%m/%Y')}. "
                            f"¡No pierdas tu oportunidad de postularte!",
                    tipo="convocatoria",
                ))
        db.commit()
        logger.info("Recordatorios enviados para %d convocatorias próximas a cerrar", len(convs_cierre))
    except Exception as exc:
        logger.error("Error enviando recordatorios: %s", exc)
        db.rollback()
    finally:
        db.close()


async def _actualizar_precios_sicom() -> None:
    """Cron job diario: actualiza precios de combustible desde SICOM."""
    from app.services.sicom import fetch_precios_departamento, get_precios_fallback
    from app.models.transporte import PrecioCombustible

    sicom_data = await fetch_precios_departamento("HUILA")
    precios = sicom_data or get_precios_fallback()
    fuente = "SICOM" if sicom_data else "Referencia interna"
    today = date.today()
    db = SessionLocal()
    try:
        for tipo, precio in precios.items():
            existing = (
                db.query(PrecioCombustible)
                .filter(
                    PrecioCombustible.tipo == tipo,
                    PrecioCombustible.departamento == "HUILA",
                    PrecioCombustible.fecha_vigencia == today,
                )
                .first()
            )
            if existing:
                existing.precio_litro = precio
            else:
                db.add(PrecioCombustible(
                    tipo=tipo,
                    precio_litro=precio,
                    departamento="HUILA",
                    fecha_vigencia=today,
                    fuente=fuente,
                ))
        db.commit()
        logger.info(f"Precios combustible actualizados: {precios}")
    except Exception as exc:
        logger.error(f"Error actualizando precios SICOM: {exc}")
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Hard-fail si se intenta arrancar en producción con clave insegura
    if settings.SECRET_KEY == _DEFAULT_SECRET and not settings.DEBUG:
        raise ValueError(
            "SECRET_KEY usa el valor por defecto inseguro. "
            "Define SECRET_KEY en el archivo .env antes de desplegar en producción."
        )
    if settings.SECRET_KEY == _DEFAULT_SECRET:
        logger.warning(
            "⚠  SECRET_KEY es el valor por defecto inseguro. "
            "Define SECRET_KEY en tu .env antes de usar en producción."
        )
    # init_db: create_all (idempotente) + _run_cross_migrations (ALTER TABLE incremental)
    # Es seguro en producción — nunca elimina tablas ni columnas existentes.
    init_db()
    _ensure_admin()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    await _seed_transporte()
    # Actualizar precios inmediatamente al arrancar y luego cada día a las 6:00 am
    await _actualizar_precios_sicom()
    scheduler.add_job(
        _actualizar_precios_sicom, "cron", hour=6, minute=0,
        id="sicom_daily", replace_existing=True, max_instances=1,
        misfire_grace_time=3600,
    )
    scheduler.add_job(
        _enviar_recordatorios, "cron", hour=8, minute=0,
        id="recordatorios_daily", replace_existing=True, max_instances=1,
        misfire_grace_time=3600,
    )
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


_USING_DEFAULT_KEY = settings.SECRET_KEY == _DEFAULT_SECRET
if _USING_DEFAULT_KEY:
    warnings.warn(
        "\033[91m[SEGURIDAD] SECRET_KEY usa el valor por defecto. "
        "Define SECRET_KEY en backend/.env antes de desplegar en producción.\033[0m",
        stacklevel=1,
    )
    logger.critical("SECRET_KEY usa el valor por defecto — RIESGO CRITICO en producción")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Sistema Integrado de Prácticas Académicas y Monitorías - Universidad Surcolombiana",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    openapi_url="/api/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: blob:; "
        "connect-src 'self' http://localhost:5001;"
    )
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response

app.include_router(api_router, prefix="/api/v1")

# Servir archivos subidos (fotos de perfil, documentos, etc.)
_uploads_abs = os.path.abspath(settings.UPLOAD_DIR)
os.makedirs(_uploads_abs, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=_uploads_abs), name="uploads")


@app.get("/", tags=["root"])
def root():
    return {
        "system": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/api/docs",
        "status": "running",
    }
