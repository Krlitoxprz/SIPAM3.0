"""RF-PRA-06 — Control Presupuestal para el Decano."""
import os
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User, RolEnum
from app.models.presupuesto import Presupuesto, MovimientoPresupuestal, ConfiguracionCalendario, EstadoPresupuestoEnum, TipoMovimientoEnum
from app.models.documento_presupuesto import DocumentoPresupuesto
from app.schemas.practica import PresupuestoOut
from app.api.deps import get_current_user, require_roles
from app.utils.notificaciones import crear_notificacion
from app.utils.file_security import validate_and_save
from app.core.config import settings

ALLOWED_DOC_EXTS = [".pdf", ".png", ".jpg", ".jpeg", ".docx", ".xlsx"]


class PresupuestoCreate(BaseModel):
    periodo_academico: str
    monto_total_asignado: float
    descripcion: Optional[str] = None


class CalendarioCreate(BaseModel):
    periodo_academico: str
    semana_inicio_solicitudes: int = 3
    semana_fin_solicitudes: int = 14
    fecha_inicio_semestre: datetime
    fecha_fin_semestre: datetime
    is_active: bool = True


class CalendarioOut(BaseModel):
    id: int
    periodo_academico: str
    semana_inicio_solicitudes: int
    semana_fin_solicitudes: int
    fecha_inicio_semestre: datetime
    fecha_fin_semestre: datetime
    is_active: bool

    model_config = {"from_attributes": True}

router = APIRouter()


def _to_out(p: Presupuesto) -> PresupuestoOut:
    disponible = p.monto_total_asignado - p.monto_ejecutado - p.monto_comprometido
    pct = 0.0
    if p.monto_total_asignado > 0:
        pct = round((p.monto_ejecutado / p.monto_total_asignado) * 100, 1)
    return PresupuestoOut(
        id=p.id,
        periodo_academico=p.periodo_academico,
        monto_total_asignado=p.monto_total_asignado,
        monto_solicitado=p.monto_solicitado,
        monto_ejecutado=p.monto_ejecutado,
        monto_comprometido=p.monto_comprometido,
        monto_disponible=disponible,
        porcentaje_ejecutado=pct,
        estado=p.estado.value if p.estado else "aprobado",
        observaciones_admin=p.observaciones_admin,
        descripcion=p.descripcion,
    )


# ── Rutas estáticas PRIMERO (antes de /{periodo}) para evitar route capture ──

@router.get("/periodo-activo", summary="Devuelve el período académico activo")
def get_periodo_activo(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Retorna el período activo: primero busca en ConfiguracionCalendario (is_active=True),
    luego el presupuesto aprobado más reciente, y como fallback genera el periodo actual.
    """
    cal = (
        db.query(ConfiguracionCalendario)
        .filter(ConfiguracionCalendario.is_active == True)  # noqa: E712
        .order_by(ConfiguracionCalendario.periodo_academico.desc())
        .first()
    )
    if cal:
        return {"periodo_academico": cal.periodo_academico}

    pres = (
        db.query(Presupuesto)
        .filter(Presupuesto.estado == EstadoPresupuestoEnum.aprobado)
        .order_by(Presupuesto.periodo_academico.desc())
        .first()
    )
    if pres:
        return {"periodo_academico": pres.periodo_academico}

    from datetime import date
    hoy = date.today()
    semestre = "1" if hoy.month <= 6 else "2"
    return {"periodo_academico": f"{hoy.year}-{semestre}"}


@router.get("/", response_model=list[PresupuestoOut])
def listar_presupuestos(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.jefe_programa, RolEnum.decano, RolEnum.admin)),
):
    return [_to_out(p) for p in db.query(Presupuesto).order_by(Presupuesto.periodo_academico.desc()).all()]


@router.post("/", response_model=PresupuestoOut, status_code=201)
def crear_presupuesto(
    body: PresupuestoCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.jefe_programa, RolEnum.decano)),
):
    if db.query(Presupuesto).filter(Presupuesto.periodo_academico == body.periodo_academico).first():
        raise HTTPException(status_code=400, detail="Ya existe un presupuesto para ese período")
    p = Presupuesto(
        periodo_academico=body.periodo_academico,
        monto_total_asignado=body.monto_total_asignado,
        monto_ejecutado=0.0,
        monto_comprometido=0.0,
        descripcion=body.descripcion,
        estado=EstadoPresupuestoEnum.borrador,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return _to_out(p)


@router.patch("/{periodo}/solicitar", response_model=PresupuestoOut)
def solicitar_presupuesto(
    periodo: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.jefe_programa, RolEnum.decano)),
):
    """Jefe de Programa envía la solicitud de presupuesto al Administrador."""
    p = db.query(Presupuesto).filter(Presupuesto.periodo_academico == periodo).first()
    if not p:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    if p.estado not in [EstadoPresupuestoEnum.borrador, EstadoPresupuestoEnum.modificacion, EstadoPresupuestoEnum.rechazado]:
        raise HTTPException(status_code=400, detail=f"No se puede solicitar desde estado '{p.estado.value}'")
    p.estado = EstadoPresupuestoEnum.solicitado
    # Notificar a todos los administradores
    admins = db.query(User).filter(User.rol == RolEnum.admin, User.is_active == True).all()
    for gu in admins:
        crear_notificacion(
            db, gu.id,
            tipo="presupuesto_solicitado",
            titulo=f"Solicitud de presupuesto — {periodo}",
            mensaje=f"El Jefe de Programa ha enviado una solicitud de presupuesto para el período {periodo} por ${p.monto_total_asignado:,.0f} COP.",
            url="/presupuesto",
        )
    db.commit()
    db.refresh(p)
    return _to_out(p)


class DecisionBody(BaseModel):
    observaciones: Optional[str] = None


class PresupuestoUpdate(BaseModel):
    monto_total_asignado: Optional[float] = None
    descripcion: Optional[str] = None


@router.get("/siguiente-periodo")
def siguiente_periodo(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.jefe_programa, RolEnum.decano)),
):
    """Sugiere el código del siguiente período académico aún sin presupuesto."""
    periodos = [p.periodo_academico for p in db.query(Presupuesto).all()]
    # Genera candidatos hasta encontrar uno libre
    from datetime import date
    anio = date.today().year
    candidatos = []
    for y in range(anio, anio + 3):
        for sem in ["1", "2"]:
            candidatos.append(f"{y}-{sem}")
    for c in candidatos:
        if c not in periodos:
            return {"periodo_sugerido": c, "periodos_existentes": periodos}
    return {"periodo_sugerido": f"{anio + 3}-1", "periodos_existentes": periodos}


class IncrementoBody(BaseModel):
    nuevo_monto: float
    descripcion: Optional[str] = None


@router.patch("/{periodo}/solicitar-incremento", response_model=PresupuestoOut)
def solicitar_incremento(
    periodo: str,
    body: IncrementoBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.jefe_programa, RolEnum.decano)),
):
    """Jefe reabre un presupuesto ya aprobado para pedir más recursos al Administrador."""
    p = db.query(Presupuesto).filter(Presupuesto.periodo_academico == periodo).first()
    if not p:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    if p.estado != EstadoPresupuestoEnum.aprobado:
        raise HTTPException(status_code=400, detail="Solo puedes pedir incremento de un presupuesto aprobado")
    if body.nuevo_monto <= p.monto_total_asignado:
        raise HTTPException(status_code=400, detail=f"El nuevo monto debe ser mayor al actual (${p.monto_total_asignado:,.0f})")
    # Guardamos el monto solicitado SIN tocar monto_total_asignado (que sigue siendo el aprobado)
    diff = body.nuevo_monto - p.monto_total_asignado
    p.monto_solicitado = body.nuevo_monto
    if body.descripcion:
        p.descripcion = body.descripcion
    p.estado = EstadoPresupuestoEnum.solicitado
    p.observaciones_admin = None
    admins = db.query(User).filter(User.rol == RolEnum.admin, User.is_active == True).all()
    for gu in admins:
        crear_notificacion(
            db, gu.id,
            tipo="presupuesto_incremento",
            titulo=f"Solicitud de incremento — {periodo}",
            mensaje=f"El Jefe de Programa solicita un incremento de ${diff:,.0f} COP para {periodo}. Nuevo monto propuesto: ${body.nuevo_monto:,.0f} COP.",
            url="/presupuesto",
        )
    db.commit()
    db.refresh(p)
    return _to_out(p)


@router.patch("/{periodo}/editar", response_model=PresupuestoOut)
def editar_presupuesto(
    periodo: str,
    body: PresupuestoUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.jefe_programa, RolEnum.decano)),
):
    """Jefe de Programa edita monto/descripcion del presupuesto (solo en borrador, modificacion o rechazado)."""
    p = db.query(Presupuesto).filter(Presupuesto.periodo_academico == periodo).first()
    if not p:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    if p.estado not in [
        EstadoPresupuestoEnum.borrador,
        EstadoPresupuestoEnum.modificacion,
        EstadoPresupuestoEnum.rechazado,
    ]:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede editar un presupuesto en estado '{p.estado.value}'. Solo en borrador, pendiente de modificación o rechazado.",
        )
    if body.monto_total_asignado is not None:
        p.monto_total_asignado = body.monto_total_asignado
    if body.descripcion is not None:
        p.descripcion = body.descripcion
    db.commit()
    db.refresh(p)
    return _to_out(p)


@router.patch("/{periodo}/aprobar", response_model=PresupuestoOut)
def aprobar_presupuesto(
    periodo: str,
    body: DecisionBody,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.admin)),
):
    """Admin aprueba la solicitud de presupuesto tal como fue establecida por el Jefe."""
    p = db.query(Presupuesto).filter(Presupuesto.periodo_academico == periodo).first()
    if not p:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    if p.estado != EstadoPresupuestoEnum.solicitado:
        raise HTTPException(status_code=400, detail="Solo se pueden aprobar presupuestos solicitados")
    p.estado = EstadoPresupuestoEnum.aprobado
    p.observaciones_admin = body.observaciones
    # Si había un incremento pendiente, aplicarlo ahora que fue aprobado
    if p.monto_solicitado is not None:
        p.monto_total_asignado = p.monto_solicitado
        p.monto_solicitado = None
    jefes = db.query(User).filter(User.rol.in_([RolEnum.jefe_programa, RolEnum.decano]), User.is_active == True).all()
    for j in jefes:
        crear_notificacion(
            db, j.id,
            tipo="presupuesto_aprobado",
            titulo=f"Presupuesto {periodo} APROBADO ✅",
            mensaje=f"El Administrador aprobó el presupuesto de ${p.monto_total_asignado:,.0f} COP para {periodo}.",
            url="/presupuesto",
        )
    db.commit()
    db.refresh(p)
    return _to_out(p)


@router.patch("/{periodo}/rechazar", response_model=PresupuestoOut)
def rechazar_presupuesto(
    periodo: str,
    body: DecisionBody,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.admin)),
):
    """Admin rechaza la solicitud de presupuesto."""
    p = db.query(Presupuesto).filter(Presupuesto.periodo_academico == periodo).first()
    if not p:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    if p.estado != EstadoPresupuestoEnum.solicitado:
        raise HTTPException(status_code=400, detail="Solo se pueden rechazar presupuestos solicitados")
    era_incremento = p.monto_solicitado is not None
    # Si era un incremento pendiente, volver a aprobado (no rechazado) para que el jefe pueda re-pedir
    p.estado = EstadoPresupuestoEnum.aprobado if era_incremento else EstadoPresupuestoEnum.rechazado
    p.observaciones_admin = body.observaciones
    p.monto_solicitado = None
    jefes = db.query(User).filter(User.rol.in_([RolEnum.jefe_programa, RolEnum.decano]), User.is_active == True).all()
    obs = f" Motivo: {body.observaciones}" if body.observaciones else ""
    for j in jefes:
        crear_notificacion(
            db, j.id,
            tipo="presupuesto_rechazado",
            titulo=f"Presupuesto {periodo} RECHAZADO ❌",
            mensaje=f"El Administrador rechazó la solicitud de presupuesto para {periodo}.{obs}",
            url="/presupuesto",
        )
    db.commit()
    db.refresh(p)
    return _to_out(p)


@router.patch("/{periodo}/pedir-modificacion", response_model=PresupuestoOut)
def pedir_modificacion_presupuesto(
    periodo: str,
    body: DecisionBody,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.admin)),
):
    """Admin devuelve la solicitud al Jefe indicando qué debe corregir."""
    p = db.query(Presupuesto).filter(Presupuesto.periodo_academico == periodo).first()
    if not p:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    if p.estado != EstadoPresupuestoEnum.solicitado:
        raise HTTPException(status_code=400, detail="Solo se pueden solicitar modificaciones de presupuestos solicitados")
    p.estado = EstadoPresupuestoEnum.modificacion
    p.observaciones_admin = body.observaciones
    # Si era un incremento, limpiar monto_solicitado para que el jefe empiece de nuevo
    p.monto_solicitado = None
    jefes = db.query(User).filter(User.rol.in_([RolEnum.jefe_programa, RolEnum.decano]), User.is_active == True).all()
    obs = f" Indica: {body.observaciones}" if body.observaciones else ""
    for j in jefes:
        crear_notificacion(
            db, j.id,
            tipo="presupuesto_modificacion",
            titulo=f"Presupuesto {periodo} requiere corrección ⚠️",
            mensaje=f"El Administrador devuelve la solicitud para que la corrijas.{obs}",
            url="/presupuesto",
        )
    db.commit()
    db.refresh(p)
    return _to_out(p)


@router.get("/actual", response_model=PresupuestoOut)
def presupuesto_actual(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.jefe_programa, RolEnum.decano, RolEnum.admin)),
):
    # Intentar obtener el del período activo primero
    cal = db.query(ConfiguracionCalendario).filter(
        ConfiguracionCalendario.is_active == True
    ).order_by(ConfiguracionCalendario.periodo_academico.desc()).first()
    p = None
    if cal:
        p = db.query(Presupuesto).filter(Presupuesto.periodo_academico == cal.periodo_academico).first()
    if not p:
        # fallback: el más reciente
        p = db.query(Presupuesto).order_by(Presupuesto.id.desc()).first()
    if not p:
        raise HTTPException(status_code=404, detail="No hay presupuesto configurado")
    return _to_out(p)


@router.get("/movimientos/{periodo}")
def movimientos_por_periodo(
    periodo: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.jefe_programa, RolEnum.decano, RolEnum.admin)),
):
    p = db.query(Presupuesto).filter(Presupuesto.periodo_academico == periodo).first()
    if not p:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    movimientos = (
        db.query(MovimientoPresupuestal)
        .filter(MovimientoPresupuestal.presupuesto_id == p.id)
        .order_by(MovimientoPresupuestal.fecha_movimiento.desc())
        .all()
    )
    return [
        {
            "id": m.id,
            "tipo": m.tipo.value,
            "monto": float(m.monto) if m.monto is not None else None,
            "concepto": m.concepto,
            "fecha": m.fecha_movimiento.isoformat() if m.fecha_movimiento else None,
        }
        for m in movimientos
    ]


@router.get("/periodo-activo")
def periodo_activo(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Retorna el período académico activo — accesible por todos los roles."""
    cal = db.query(ConfiguracionCalendario).filter(
        ConfiguracionCalendario.is_active == True
    ).order_by(ConfiguracionCalendario.periodo_academico.desc()).first()
    if not cal:
        raise HTTPException(status_code=404, detail="No hay período académico activo configurado")
    return {
        "periodo_academico": cal.periodo_academico,
        "fecha_inicio_semestre": cal.fecha_inicio_semestre,
        "fecha_fin_semestre": cal.fecha_fin_semestre,
        "semana_inicio_solicitudes": cal.semana_inicio_solicitudes,
        "semana_fin_solicitudes": cal.semana_fin_solicitudes,
    }


@router.get("/configuracion-calendario/", response_model=list[CalendarioOut])
def listar_calendarios(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.jefe_programa, RolEnum.decano, RolEnum.admin)),
):
    return db.query(ConfiguracionCalendario).order_by(ConfiguracionCalendario.periodo_academico.desc()).all()


@router.post("/configuracion-calendario/", response_model=CalendarioOut, status_code=201)
def crear_calendario(
    body: CalendarioCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.admin)),
):
    existing = db.query(ConfiguracionCalendario).filter(
        ConfiguracionCalendario.periodo_academico == body.periodo_academico
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe configuración para ese período")
    cal = ConfiguracionCalendario(**body.model_dump())
    db.add(cal)
    db.commit()
    db.refresh(cal)
    return cal


@router.patch("/configuracion-calendario/{cal_id}", response_model=CalendarioOut)
def actualizar_calendario(
    cal_id: int,
    body: CalendarioCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.admin)),
):
    cal = db.query(ConfiguracionCalendario).filter(ConfiguracionCalendario.id == cal_id).first()
    if not cal:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(cal, field, value)
    db.commit()
    db.refresh(cal)
    return cal


# ── Documentos de soporte ────────────────────────────────────────────────────

class DocumentoOut(BaseModel):
    id: int
    tipo_solicitud: str
    nombre_original: str
    descripcion: str | None
    subido_por: str
    created_at: str | None
    download_url: str


def _doc_to_out(d: DocumentoPresupuesto) -> DocumentoOut:
    nombre = f"{d.subido_por.nombres} {d.subido_por.apellidos}" if d.subido_por else "—"
    return DocumentoOut(
        id=d.id,
        tipo_solicitud=d.tipo_solicitud,
        nombre_original=d.nombre_original,
        descripcion=d.descripcion,
        subido_por=nombre,
        created_at=d.created_at.isoformat() if d.created_at else None,
        download_url=f"/api/v1/presupuesto/documentos/{d.id}/descargar",
    )


@router.post("/{periodo}/documentos", response_model=DocumentoOut, status_code=201)
async def subir_documento_presupuesto(
    periodo: str,
    tipo_solicitud: str = Form(..., description="solicitud | incremento | modificacion"),
    descripcion: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.jefe_programa, RolEnum.decano)),
):
    """Jefe sube un documento de soporte al presupuesto (PDF, imagen, Word, Excel)."""
    p = db.query(Presupuesto).filter(Presupuesto.periodo_academico == periodo).first()
    if not p:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    tipos_validos = {"solicitud", "incremento", "modificacion"}
    if tipo_solicitud not in tipos_validos:
        raise HTTPException(status_code=400, detail=f"Tipo inválido. Use: {tipos_validos}")

    nombre_original = file.filename or "documento"
    safe_name, _ = await validate_and_save(
        file,
        subfolder=f"presupuesto/{periodo}",
        allowed_extensions=ALLOWED_DOC_EXTS,
        upload_dir=settings.UPLOAD_DIR,
        max_bytes=settings.MAX_FILE_SIZE_MB * 1024 * 1024,
    )
    ruta_relativa = os.path.join("presupuesto", periodo, safe_name)

    doc = DocumentoPresupuesto(
        presupuesto_id=p.id,
        subido_por_id=current_user.id,
        tipo_solicitud=tipo_solicitud,
        nombre_original=nombre_original,
        nombre_almacenado=safe_name,
        ruta=ruta_relativa,
        descripcion=descripcion,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    doc.subido_por  # eager load
    return _doc_to_out(doc)


@router.get("/{periodo}/documentos", response_model=list[DocumentoOut])
def listar_documentos_presupuesto(
    periodo: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.jefe_programa, RolEnum.decano, RolEnum.admin)),
):
    """Lista todos los documentos adjuntos a un presupuesto."""
    p = db.query(Presupuesto).filter(Presupuesto.periodo_academico == periodo).first()
    if not p:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    docs = (
        db.query(DocumentoPresupuesto)
        .filter(DocumentoPresupuesto.presupuesto_id == p.id)
        .order_by(DocumentoPresupuesto.created_at.desc())
        .all()
    )
    for d in docs:
        d.subido_por  # eager load
    return [_doc_to_out(d) for d in docs]


@router.get("/documentos/{doc_id}/descargar")
def descargar_documento_presupuesto(
    doc_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.jefe_programa, RolEnum.decano, RolEnum.admin)),
):
    """Descarga / visualiza un documento de presupuesto."""
    doc = db.query(DocumentoPresupuesto).filter(DocumentoPresupuesto.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    base = os.path.abspath(settings.UPLOAD_DIR)
    full_path = os.path.abspath(os.path.join(settings.UPLOAD_DIR, doc.ruta))
    if not full_path.startswith(base):
        raise HTTPException(status_code=400, detail="Ruta de archivo inválida")
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado en el servidor")
    return FileResponse(
        path=full_path,
        filename=doc.nombre_original,
        media_type="application/octet-stream",
    )


@router.delete("/{periodo}/documentos/{doc_id}", status_code=204)
def eliminar_documento_presupuesto(
    periodo: str,
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.jefe_programa, RolEnum.decano)),
):
    """Jefe elimina un documento propio (solo si el presupuesto no está aprobado)."""
    p = db.query(Presupuesto).filter(Presupuesto.periodo_academico == periodo).first()
    if not p:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    if p.estado == EstadoPresupuestoEnum.aprobado:
        raise HTTPException(status_code=400, detail="No se pueden eliminar documentos de un presupuesto aprobado")
    doc = db.query(DocumentoPresupuesto).filter(
        DocumentoPresupuesto.id == doc_id,
        DocumentoPresupuesto.presupuesto_id == p.id,
        DocumentoPresupuesto.subido_por_id == current_user.id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado o sin permisos")
    full_path = os.path.join(settings.UPLOAD_DIR, doc.ruta)
    if os.path.exists(full_path):
        os.remove(full_path)
    db.delete(doc)
    db.commit()


# ── Endpoints exclusivos del Administrador ────────────────────────────────────

class AmpliarSemestreBody(BaseModel):
    semanas_adicionales: int = 2
    nueva_fecha_fin: Optional[datetime] = None


@router.patch("/configuracion-calendario/{cal_id}/ampliar-semestre", response_model=CalendarioOut)
def ampliar_semestre(
    cal_id: int,
    body: AmpliarSemestreBody,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.admin)),
):
    """Admin: amplía el rango de semanas de solicitudes y la fecha fin del semestre."""
    cal = db.query(ConfiguracionCalendario).filter(ConfiguracionCalendario.id == cal_id).first()
    if not cal:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    if body.semanas_adicionales < 1:
        raise HTTPException(status_code=400, detail="Debe agregar al menos 1 semana")
    cal.semana_fin_solicitudes = cal.semana_fin_solicitudes + body.semanas_adicionales
    if body.nueva_fecha_fin:
        if body.nueva_fecha_fin <= cal.fecha_fin_semestre:
            raise HTTPException(status_code=400, detail="La nueva fecha fin debe ser posterior a la actual")
        cal.fecha_fin_semestre = body.nueva_fecha_fin
    db.commit()
    db.refresh(cal)
    return cal


class AumentarMontoBody(BaseModel):
    nuevo_monto: float
    razon: Optional[str] = None


@router.patch("/{periodo}/aumentar-monto", response_model=PresupuestoOut)
def aumentar_monto_admin(
    periodo: str,
    body: AumentarMontoBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.admin)),
):
    """Admin: aumenta directamente el monto total asignado (sin flujo de aprobación)."""
    p = db.query(Presupuesto).filter(Presupuesto.periodo_academico == periodo).first()
    if not p:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    if body.nuevo_monto <= float(p.monto_total_asignado):
        raise HTTPException(
            status_code=400,
            detail=f"El nuevo monto debe ser mayor al actual (${p.monto_total_asignado:,.0f})",
        )
    diferencia = body.nuevo_monto - float(p.monto_total_asignado)
    p.monto_total_asignado = body.nuevo_monto
    if p.estado != EstadoPresupuestoEnum.aprobado:
        p.estado = EstadoPresupuestoEnum.aprobado
    p.monto_solicitado = None
    mov = MovimientoPresupuestal(
        presupuesto_id=p.id,
        tipo=TipoMovimientoEnum.ajuste,
        monto=diferencia,
        concepto=body.razon or f"Incremento directo por Administrador — {periodo}",
        responsable_id=current_user.id,
    )
    db.add(mov)
    jefes = db.query(User).filter(
        User.rol.in_([RolEnum.jefe_programa, RolEnum.decano]), User.is_active == True
    ).all()
    for j in jefes:
        crear_notificacion(
            db, j.id,
            tipo="presupuesto_aprobado",
            titulo=f"Presupuesto {periodo} aumentado ✅",
            mensaje=f"El Administrador aumentó el presupuesto de {periodo} en ${diferencia:,.0f} COP. Nuevo total: ${body.nuevo_monto:,.0f} COP.",
            url="/presupuesto",
        )
    db.commit()
    db.refresh(p)
    return _to_out(p)


class ForzarEstadoBody(BaseModel):
    estado: EstadoPresupuestoEnum
    observaciones: Optional[str] = None


@router.patch("/{periodo}/forzar-estado", response_model=PresupuestoOut)
def forzar_estado_presupuesto(
    periodo: str,
    body: ForzarEstadoBody,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.admin)),
):
    """Admin: fuerza el estado de un presupuesto a cualquier valor (override total)."""
    p = db.query(Presupuesto).filter(Presupuesto.periodo_academico == periodo).first()
    if not p:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    p.estado = body.estado
    if body.observaciones:
        p.observaciones_admin = body.observaciones
    db.commit()
    db.refresh(p)
    return _to_out(p)


@router.delete("/{periodo}", status_code=204)
def eliminar_presupuesto(
    periodo: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.admin)),
):
    """Admin: elimina un presupuesto y todos sus movimientos (acción irreversible)."""
    p = db.query(Presupuesto).filter(Presupuesto.periodo_academico == periodo).first()
    if not p:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    db.delete(p)
    db.commit()


@router.get("/admin/estadisticas-globales")
def estadisticas_globales(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.admin)),
):
    """Admin: resumen global del sistema SIPAM (usuarios, prácticas, presupuesto)."""
    from sqlalchemy import func as sa_func
    from app.models.convocatoria import Asignatura
    from app.models.practica import Practica

    total_users = db.query(sa_func.count(User.id)).scalar()
    users_por_rol = dict(db.query(User.rol, sa_func.count(User.id)).group_by(User.rol).all())
    total_asignaturas = db.query(sa_func.count(Asignatura.id)).scalar()
    total_practicas = db.query(sa_func.count(Practica.id)).scalar()
    practicas_por_estado = dict(
        db.query(Practica.estado, sa_func.count(Practica.id)).group_by(Practica.estado).all()
    )
    total_presupuestos = db.query(sa_func.count(Presupuesto.id)).scalar()
    presupuesto_activo = db.query(Presupuesto).order_by(Presupuesto.id.desc()).first()
    return {
        "usuarios": {
            "total": total_users,
            "por_rol": {k.value if hasattr(k, "value") else str(k): v for k, v in users_por_rol.items()},
        },
        "asignaturas": {"total": total_asignaturas},
        "practicas": {
            "total": total_practicas,
            "por_estado": {k.value if hasattr(k, "value") else str(k): v for k, v in practicas_por_estado.items()},
        },
        "presupuesto": {
            "total_periodos": total_presupuestos,
            "activo": {
                "periodo": presupuesto_activo.periodo_academico,
                "monto_total": float(presupuesto_activo.monto_total_asignado),
                "monto_disponible": float(presupuesto_activo.monto_disponible),
                "estado": presupuesto_activo.estado.value,
            } if presupuesto_activo else None,
        },
    }


# ── Ruta dinámica AL FINAL para evitar capturar rutas estáticas ──────────────

@router.get("/{periodo}", response_model=PresupuestoOut)
def presupuesto_por_periodo(
    periodo: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.jefe_programa, RolEnum.decano, RolEnum.admin)),
):
    p = db.query(Presupuesto).filter(Presupuesto.periodo_academico == periodo).first()
    if not p:
        raise HTTPException(status_code=404, detail=f"Presupuesto para {periodo} no encontrado")
    return _to_out(p)


