"""Seguimiento de horas de monitores seleccionados (RF post-selección)."""
import csv
import io
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session, joinedload

from app.db.database import get_db
from app.models.user import User, RolEnum
from app.models.monitor import HorasMonitor, AuditLog
from app.models.postulacion import Postulacion, EstadoPostulacionEnum
from app.models.evaluacion_monitor import EvaluacionMonitor
from app.models.convocatoria import Convocatoria, EstadoConvocatoriaEnum
from app.api.deps import get_current_user, require_roles

router = APIRouter()


class HorasIn(BaseModel):
    semana: int
    horas: float
    descripcion: Optional[str] = None


class EvaluacionIn(BaseModel):
    nota_desempeno: float
    puntualidad: Optional[float] = None
    calidad_academica: Optional[float] = None
    observaciones: Optional[str] = None

    @field_validator("nota_desempeno", "puntualidad", "calidad_academica")
    @classmethod
    def rango_nota(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0.0 <= v <= 5.0):
            raise ValueError("La nota debe estar entre 0.0 y 5.0")
        return v


def _log(db: Session, usuario_id: int, accion: str, entidad: str, entidad_id: Optional[int] = None, detalle: Optional[str] = None):
    db.add(AuditLog(usuario_id=usuario_id, accion=accion, entidad=entidad, entidad_id=entidad_id, detalle=detalle))
    db.flush()


# ── Estudiante: registrar horas propias ──────────────────────────────────────

@router.post("/registrar-horas", status_code=201)
def registrar_horas(
    body: HorasIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.estudiante)),
):
    post = db.query(Postulacion).filter(
        Postulacion.estudiante_id == current_user.id,
        Postulacion.estado == EstadoPostulacionEnum.seleccionado,
    ).first()
    if not post:
        raise HTTPException(status_code=403, detail="No eres monitor seleccionado en ninguna convocatoria activa")
    if body.semana < 1 or body.semana > 20:
        raise HTTPException(status_code=400, detail="La semana debe estar entre 1 y 20")
    if body.horas <= 0 or body.horas > 40:
        raise HTTPException(status_code=400, detail="Las horas deben ser entre 0.5 y 40 por semana")
    ya_existe = db.query(HorasMonitor).filter(
        HorasMonitor.postulacion_id == post.id,
        HorasMonitor.semana == body.semana,
    ).first()
    if ya_existe:
        raise HTTPException(
            status_code=409,
            detail=f"Ya tienes horas registradas para la semana {body.semana}. Contacta a tu profesor para corregirlas.",
        )
    h = HorasMonitor(
        postulacion_id=post.id,
        semana=body.semana,
        horas=body.horas,
        descripcion=body.descripcion,
    )
    db.add(h)
    _log(db, current_user.id, "registrar_horas", "horas_monitor", detalle=f"semana {body.semana}: {body.horas}h")
    db.commit()
    db.refresh(h)
    return {"id": h.id, "semana": h.semana, "horas": h.horas, "descripcion": h.descripcion, "aprobado_por_id": h.aprobado_por_id}


@router.get("/mis-horas")
def mis_horas(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.estudiante)),
):
    post = db.query(Postulacion).filter(
        Postulacion.estudiante_id == current_user.id,
        Postulacion.estado == EstadoPostulacionEnum.seleccionado,
    ).first()
    if not post:
        return {"postulacion": None, "horas": [], "total_horas": 0}
    horas = db.query(HorasMonitor).filter(HorasMonitor.postulacion_id == post.id).order_by(HorasMonitor.semana).all()
    total = sum(h.horas for h in horas)
    return {
        "postulacion": {
            "id": post.id,
            "convocatoria": post.convocatoria.titulo if post.convocatoria else "—",
            "asignatura": post.convocatoria.asignatura.nombre if post.convocatoria and post.convocatoria.asignatura else "—",
        },
        "horas": [{"id": h.id, "semana": h.semana, "horas": h.horas, "descripcion": h.descripcion, "aprobado": h.aprobado_por_id is not None} for h in horas],
        "total_horas": total,
    }


# ── Profesor: ver y aprobar horas de sus monitores ───────────────────────────

@router.get("/convocatoria/{conv_id}")
def horas_por_convocatoria(
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.profesor, RolEnum.jefe_programa, RolEnum.decano)),
):
    posts = (
        db.query(Postulacion)
        .options(joinedload(Postulacion.estudiante))
        .filter(
            Postulacion.convocatoria_id == conv_id,
            Postulacion.estado == EstadoPostulacionEnum.seleccionado,
        )
        .all()
    )
    result = []
    for p in posts:
        horas = db.query(HorasMonitor).filter(HorasMonitor.postulacion_id == p.id).order_by(HorasMonitor.semana).all()
        total = sum(h.horas for h in horas)
        result.append({
            "postulacion_id": p.id,
            "estudiante": f"{p.estudiante.nombres} {p.estudiante.apellidos}" if p.estudiante else "—",
            "codigo": p.estudiante.codigo if p.estudiante else "—",
            "total_horas": total,
            "horas": [{"id": h.id, "semana": h.semana, "horas": h.horas, "descripcion": h.descripcion, "aprobado": h.aprobado_por_id is not None} for h in horas],
        })
    return result


class HorasCorreccion(BaseModel):
    horas: Optional[float] = None
    descripcion: Optional[str] = None


@router.patch("/horas/{hora_id}")
def corregir_horas(
    hora_id: int,
    body: HorasCorreccion,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.profesor, RolEnum.jefe_programa, RolEnum.decano)),
):
    """Profesor corrige horas o descripción registradas por el monitor."""
    h = db.query(HorasMonitor).filter(HorasMonitor.id == hora_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Registro no encontrado")

    if current_user.rol == RolEnum.profesor:
        post = db.query(Postulacion).options(joinedload(Postulacion.convocatoria)).filter(
            Postulacion.id == h.postulacion_id
        ).first()
        if not post or post.convocatoria.profesor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Solo puede corregir horas de sus propios monitores")

    if body.horas is not None:
        if body.horas <= 0 or body.horas > 40:
            raise HTTPException(status_code=400, detail="Las horas deben estar entre 0.5 y 40")
        h.horas = body.horas
    if body.descripcion is not None:
        h.descripcion = body.descripcion

    _log(db, current_user.id, "corregir_horas", "horas_monitor", hora_id,
         f"horas={h.horas}, desc={h.descripcion}")
    db.commit()
    db.refresh(h)
    return {"id": h.id, "semana": h.semana, "horas": h.horas, "descripcion": h.descripcion, "aprobado": h.aprobado_por_id is not None}


@router.patch("/horas/{hora_id}/aprobar")
def aprobar_horas(
    hora_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.profesor, RolEnum.jefe_programa, RolEnum.decano)),
):
    h = db.query(HorasMonitor).filter(HorasMonitor.id == hora_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Registro no encontrado")

    if current_user.rol == RolEnum.profesor:
        post = db.query(Postulacion).options(joinedload(Postulacion.convocatoria)).filter(
            Postulacion.id == h.postulacion_id
        ).first()
        if not post or post.convocatoria.profesor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Solo puede aprobar horas de sus propios monitores")

    h.aprobado_por_id = current_user.id
    _log(db, current_user.id, "aprobar_horas", "horas_monitor", hora_id)
    db.commit()
    return {"ok": True}


# ── Evaluación de desempeño del monitor (SF-03) ──────────────────────────────

@router.post("/postulaciones/{post_id}/evaluacion", status_code=201, summary="Registrar evaluación del monitor (SF-03)")
def crear_evaluacion(
    post_id: int,
    body: EvaluacionIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.profesor, RolEnum.jefe_programa, RolEnum.decano)),
):
    post = (
        db.query(Postulacion)
        .options(joinedload(Postulacion.convocatoria), joinedload(Postulacion.estudiante))
        .filter(Postulacion.id == post_id)
        .first()
    )
    if not post:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")
    if current_user.rol == RolEnum.profesor and post.convocatoria.profesor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Solo puede evaluar monitores de sus propias convocatorias")
    if post.convocatoria.estado != EstadoConvocatoriaEnum.finalizada:
        raise HTTPException(status_code=400, detail="Solo se puede evaluar cuando la convocatoria está finalizada")
    if post.estado != EstadoPostulacionEnum.seleccionado:
        raise HTTPException(status_code=400, detail="Solo se evalúa al monitor seleccionado")

    existing = db.query(EvaluacionMonitor).filter(EvaluacionMonitor.postulacion_id == post_id).first()
    if existing:
        existing.nota_desempeno = body.nota_desempeno
        existing.puntualidad = body.puntualidad
        existing.calidad_academica = body.calidad_academica
        existing.observaciones = body.observaciones
        existing.evaluado_por_id = current_user.id
        ev = existing
    else:
        ev = EvaluacionMonitor(
            postulacion_id=post_id,
            evaluado_por_id=current_user.id,
            nota_desempeno=body.nota_desempeno,
            puntualidad=body.puntualidad,
            calidad_academica=body.calidad_academica,
            observaciones=body.observaciones,
        )
        db.add(ev)

    _log(db, current_user.id, "evaluar_monitor", "evaluacion_monitor", post_id,
         f"nota={body.nota_desempeno}")

    # Notificar al estudiante
    try:
        from app.models.notificacion import Notificacion
        if post.estudiante:
            titulo_conv = post.convocatoria.titulo if post.convocatoria else f"#{post.convocatoria_id}"
            db.add(Notificacion(
                usuario_id=post.estudiante_id,
                titulo="Tu desempeño fue evaluado",
                mensaje=f"El profesor registró tu evaluación final en «{titulo_conv}». "
                        f"Nota de desempeño: {body.nota_desempeno:.1f}/5.0.",
                tipo="monitor",
            ))
    except Exception:
        pass

    db.commit()
    db.refresh(ev)
    return {
        "id": ev.id,
        "postulacion_id": ev.postulacion_id,
        "nota_desempeno": ev.nota_desempeno,
        "puntualidad": ev.puntualidad,
        "calidad_academica": ev.calidad_academica,
        "observaciones": ev.observaciones,
        "evaluado_por_id": ev.evaluado_por_id,
        "created_at": ev.created_at.isoformat() if ev.created_at else None,
    }


@router.get("/postulaciones/{post_id}/evaluacion", summary="Consultar evaluación del monitor (SF-03)")
def get_evaluacion(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ev = db.query(EvaluacionMonitor).filter(EvaluacionMonitor.postulacion_id == post_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
    if current_user.rol == RolEnum.estudiante:
        post = db.query(Postulacion).filter(
            Postulacion.id == post_id, Postulacion.estudiante_id == current_user.id
        ).first()
        if not post:
            raise HTTPException(status_code=403, detail="No tienes acceso a esta evaluación")
    return {
        "id": ev.id,
        "postulacion_id": ev.postulacion_id,
        "nota_desempeno": ev.nota_desempeno,
        "puntualidad": ev.puntualidad,
        "calidad_academica": ev.calidad_academica,
        "observaciones": ev.observaciones,
        "evaluado_por_id": ev.evaluado_por_id,
        "created_at": ev.created_at.isoformat() if ev.created_at else None,
    }


# ── Audit log (admin / jefe_programa / decano) ────────────────────────────

@router.get("/audit-log")
def audit_log(
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.admin, RolEnum.jefe_programa, RolEnum.decano)),
):
    limit = min(max(1, limit), 1000)
    logs = (
        db.query(AuditLog)
        .options(joinedload(AuditLog.usuario))
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": l.id,
            "usuario": f"{l.usuario.nombres} {l.usuario.apellidos}" if l.usuario else "Sistema",
            "codigo": l.usuario.codigo if l.usuario else "—",
            "accion": l.accion,
            "entidad": l.entidad,
            "entidad_id": l.entidad_id,
            "detalle": l.detalle,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        }
        for l in logs
    ]


@router.get("/audit-log/exportar", summary="Exportar audit log a CSV (SF-04)")
def exportar_audit_log_csv(
    limit: int = 1000,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.admin, RolEnum.jefe_programa, RolEnum.decano)),
):
    limit = min(max(1, limit), 5000)
    logs = (
        db.query(AuditLog)
        .options(joinedload(AuditLog.usuario))
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Fecha", "Usuario", "Código", "Acción", "Entidad", "Entidad ID", "Detalle"])
    for l in logs:
        writer.writerow([
            l.id,
            l.created_at.strftime("%Y-%m-%d %H:%M:%S") if l.created_at else "",
            f"{l.usuario.nombres} {l.usuario.apellidos}" if l.usuario else "Sistema",
            l.usuario.codigo if l.usuario else "—",
            l.accion,
            l.entidad,
            l.entidad_id or "",
            l.detalle or "",
        ])
    output.seek(0)
    filename = f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/convocatoria/{conv_id}/exportar", summary="Exportar horas de monitores a CSV (SF-04)")
def exportar_horas_csv(
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.profesor, RolEnum.jefe_programa, RolEnum.decano)),
):
    posts = (
        db.query(Postulacion)
        .options(joinedload(Postulacion.estudiante))
        .filter(
            Postulacion.convocatoria_id == conv_id,
            Postulacion.estado == EstadoPostulacionEnum.seleccionado,
        )
        .all()
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Estudiante", "Código", "Semana", "Horas", "Descripción", "Aprobado"])
    for p in posts:
        horas = db.query(HorasMonitor).filter(HorasMonitor.postulacion_id == p.id).order_by(HorasMonitor.semana).all()
        nombre = f"{p.estudiante.nombres} {p.estudiante.apellidos}" if p.estudiante else "—"
        codigo = p.estudiante.codigo if p.estudiante else "—"
        for h in horas:
            writer.writerow([nombre, codigo, h.semana, h.horas, h.descripcion or "", "Sí" if h.aprobado_por_id else "No"])
    output.seek(0)
    filename = f"horas_monitor_conv{conv_id}_{datetime.now().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
