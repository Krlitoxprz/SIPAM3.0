"""Endpoints exclusivos del Administrador SIPAM.

Cubre:
- CRUD completo de ConfiguracionCalendario (semestres)
- Eliminación forzada de convocatorias, postulaciones y prácticas
- Listado enriquecido de recursos del sistema
"""
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func as sa_func

from app.db.database import get_db
from app.models.user import User, RolEnum
from app.models.presupuesto import ConfiguracionCalendario
from app.models.convocatoria import Convocatoria, EstadoConvocatoriaEnum, Asignatura
from app.models.postulacion import Postulacion
from app.models.practica import Practica, EstadoPracticaEnum
from app.api.deps import require_roles

router = APIRouter()

_ADMIN = Depends(require_roles(RolEnum.admin))


# ══════════════════════════════════════════════════════════════════════════════
#  SEMESTRES  (ConfiguracionCalendario)
# ══════════════════════════════════════════════════════════════════════════════

class SemestreCreate(BaseModel):
    periodo_academico: str
    fecha_inicio_semestre: datetime
    fecha_fin_semestre: datetime
    semana_inicio_solicitudes: int = 3
    semana_fin_solicitudes: int = 14
    is_active: bool = False


class SemestreUpdate(BaseModel):
    fecha_inicio_semestre: Optional[datetime] = None
    fecha_fin_semestre: Optional[datetime] = None
    semana_inicio_solicitudes: Optional[int] = None
    semana_fin_solicitudes: Optional[int] = None
    is_active: Optional[bool] = None


def _semestre_estado(cal: ConfiguracionCalendario) -> str:
    if not cal.is_active:
        return "inactivo"
    now = datetime.now(timezone.utc)
    inicio = cal.fecha_inicio_semestre
    fin = cal.fecha_fin_semestre
    if inicio.tzinfo is None:
        inicio = inicio.replace(tzinfo=timezone.utc)
    if fin.tzinfo is None:
        fin = fin.replace(tzinfo=timezone.utc)
    if now < inicio:
        return "futuro"
    if now > fin:
        return "pasado"
    return "activo"


def _cal_to_dict(cal: ConfiguracionCalendario) -> dict:
    return {
        "id": cal.id,
        "periodo_academico": cal.periodo_academico,
        "fecha_inicio_semestre": cal.fecha_inicio_semestre.isoformat(),
        "fecha_fin_semestre": cal.fecha_fin_semestre.isoformat(),
        "semana_inicio_solicitudes": cal.semana_inicio_solicitudes,
        "semana_fin_solicitudes": cal.semana_fin_solicitudes,
        "is_active": cal.is_active,
        "estado": _semestre_estado(cal),
        "created_at": cal.created_at.isoformat() if cal.created_at else None,
        "updated_at": cal.updated_at.isoformat() if cal.updated_at else None,
    }


@router.get("/semestres")
def listar_semestres(
    db: Session = Depends(get_db),
    _: User = _ADMIN,
):
    """Lista todos los semestres ordenados por período descendente."""
    cals = db.query(ConfiguracionCalendario).order_by(
        ConfiguracionCalendario.periodo_academico.desc()
    ).all()
    return [_cal_to_dict(c) for c in cals]


@router.post("/semestres", status_code=201)
def crear_semestre(
    body: SemestreCreate,
    db: Session = Depends(get_db),
    _: User = _ADMIN,
):
    """Crea un nuevo semestre. Si se marca activo, desactiva todos los demás."""
    if body.semana_inicio_solicitudes >= body.semana_fin_solicitudes:
        raise HTTPException(400, "semana_inicio debe ser menor que semana_fin")
    if body.fecha_fin_semestre <= body.fecha_inicio_semestre:
        raise HTTPException(400, "fecha_fin debe ser posterior a fecha_inicio")
    if db.query(ConfiguracionCalendario).filter(
        ConfiguracionCalendario.periodo_academico == body.periodo_academico
    ).first():
        raise HTTPException(400, f"Ya existe un semestre con período '{body.periodo_academico}'")

    if body.is_active:
        db.query(ConfiguracionCalendario).update({"is_active": False})

    cal = ConfiguracionCalendario(
        periodo_academico=body.periodo_academico,
        fecha_inicio_semestre=body.fecha_inicio_semestre,
        fecha_fin_semestre=body.fecha_fin_semestre,
        semana_inicio_solicitudes=body.semana_inicio_solicitudes,
        semana_fin_solicitudes=body.semana_fin_solicitudes,
        is_active=body.is_active,
    )
    db.add(cal)
    db.commit()
    db.refresh(cal)
    return _cal_to_dict(cal)


@router.patch("/semestres/{cal_id}")
def actualizar_semestre(
    cal_id: int,
    body: SemestreUpdate,
    db: Session = Depends(get_db),
    _: User = _ADMIN,
):
    """Actualiza campos de un semestre (fechas, semanas, estado activo)."""
    cal = db.query(ConfiguracionCalendario).filter(
        ConfiguracionCalendario.id == cal_id
    ).first()
    if not cal:
        raise HTTPException(404, "Semestre no encontrado")

    if body.fecha_inicio_semestre is not None:
        cal.fecha_inicio_semestre = body.fecha_inicio_semestre
    if body.fecha_fin_semestre is not None:
        cal.fecha_fin_semestre = body.fecha_fin_semestre
    if body.semana_inicio_solicitudes is not None:
        cal.semana_inicio_solicitudes = body.semana_inicio_solicitudes
    if body.semana_fin_solicitudes is not None:
        cal.semana_fin_solicitudes = body.semana_fin_solicitudes

    # Validar consistencia
    if cal.semana_inicio_solicitudes >= cal.semana_fin_solicitudes:
        raise HTTPException(400, "semana_inicio debe ser menor que semana_fin")
    if cal.fecha_fin_semestre <= cal.fecha_inicio_semestre:
        raise HTTPException(400, "fecha_fin debe ser posterior a fecha_inicio")

    if body.is_active is True:
        db.query(ConfiguracionCalendario).filter(
            ConfiguracionCalendario.id != cal_id
        ).update({"is_active": False})
        cal.is_active = True
    elif body.is_active is False:
        cal.is_active = False

    db.commit()
    db.refresh(cal)
    return _cal_to_dict(cal)


@router.patch("/semestres/{cal_id}/activar")
def activar_semestre(
    cal_id: int,
    db: Session = Depends(get_db),
    _: User = _ADMIN,
):
    """Designa un semestre como activo y desactiva todos los demás."""
    cal = db.query(ConfiguracionCalendario).filter(
        ConfiguracionCalendario.id == cal_id
    ).first()
    if not cal:
        raise HTTPException(404, "Semestre no encontrado")
    db.query(ConfiguracionCalendario).filter(
        ConfiguracionCalendario.id != cal_id
    ).update({"is_active": False})
    cal.is_active = True
    db.commit()
    db.refresh(cal)
    return _cal_to_dict(cal)


@router.delete("/semestres/{cal_id}", status_code=204)
def eliminar_semestre(
    cal_id: int,
    db: Session = Depends(get_db),
    _: User = _ADMIN,
):
    """Elimina un semestre. No se puede eliminar el semestre activo actual."""
    cal = db.query(ConfiguracionCalendario).filter(
        ConfiguracionCalendario.id == cal_id
    ).first()
    if not cal:
        raise HTTPException(404, "Semestre no encontrado")
    if cal.is_active and _semestre_estado(cal) == "activo":
        raise HTTPException(400, "No se puede eliminar el semestre activo en curso. Desactívalo primero.")
    db.delete(cal)
    db.commit()


# ══════════════════════════════════════════════════════════════════════════════
#  MONITORÍAS — Convocatorias y Postulaciones
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/monitorias")
def listar_monitorias_admin(
    estado: Optional[EstadoConvocatoriaEnum] = Query(None),
    q: Optional[str] = Query(None, description="Buscar por título o periodo"),
    db: Session = Depends(get_db),
    _: User = _ADMIN,
):
    """Listado completo de convocatorias con conteo de postulaciones."""
    query = db.query(Convocatoria).options(
        joinedload(Convocatoria.asignatura),
        joinedload(Convocatoria.profesor),
    )
    if estado:
        query = query.filter(Convocatoria.estado == estado)
    if q:
        term = q.strip().lower()
        query = query.filter(
            sa_func.lower(Convocatoria.titulo).contains(term)
            | Convocatoria.periodo_academico.contains(term)
        )
    convocatorias = query.order_by(Convocatoria.created_at.desc()).all()

    postulaciones_count = dict(
        db.query(Postulacion.convocatoria_id, sa_func.count(Postulacion.id))
        .group_by(Postulacion.convocatoria_id)
        .all()
    )

    return [
        {
            "id": c.id,
            "titulo": c.titulo,
            "estado": c.estado.value,
            "periodo_academico": c.periodo_academico,
            "tipo_monitoria": c.tipo_monitoria.value if c.tipo_monitoria else None,
            "asignatura": f"{c.asignatura.codigo} — {c.asignatura.nombre}" if c.asignatura else None,
            "profesor": f"{c.profesor.nombres} {c.profesor.apellidos}" if c.profesor else None,
            "num_monitores_requeridos": c.num_monitores_requeridos,
            "postulaciones": postulaciones_count.get(c.id, 0),
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in convocatorias
    ]


@router.get("/monitorias/{conv_id}/postulaciones")
def listar_postulaciones_convocatoria(
    conv_id: int,
    db: Session = Depends(get_db),
    _: User = _ADMIN,
):
    """Lista todas las postulaciones de una convocatoria."""
    conv = db.query(Convocatoria).filter(Convocatoria.id == conv_id).first()
    if not conv:
        raise HTTPException(404, "Convocatoria no encontrada")
    posts = (
        db.query(Postulacion)
        .options(joinedload(Postulacion.estudiante))
        .filter(Postulacion.convocatoria_id == conv_id)
        .order_by(Postulacion.created_at.desc())
        .all()
    )
    return [
        {
            "id": p.id,
            "estado": p.estado.value,
            "estudiante": f"{p.estudiante.nombres} {p.estudiante.apellidos}" if p.estudiante else None,
            "codigo_estudiante": p.estudiante.codigo if p.estudiante else None,
            "promedio": float(p.estudiante.promedio) if p.estudiante and p.estudiante.promedio else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in posts
    ]


@router.delete("/monitorias/{conv_id}", status_code=204)
def eliminar_convocatoria_admin(
    conv_id: int,
    db: Session = Depends(get_db),
    _: User = _ADMIN,
):
    """Elimina una convocatoria y todas sus postulaciones (acción irreversible)."""
    conv = db.query(Convocatoria).filter(Convocatoria.id == conv_id).first()
    if not conv:
        raise HTTPException(404, "Convocatoria no encontrada")
    db.delete(conv)
    db.commit()


@router.delete("/monitorias/postulaciones/{post_id}", status_code=204)
def eliminar_postulacion_admin(
    post_id: int,
    db: Session = Depends(get_db),
    _: User = _ADMIN,
):
    """Elimina una postulación individual."""
    post = db.query(Postulacion).filter(Postulacion.id == post_id).first()
    if not post:
        raise HTTPException(404, "Postulación no encontrada")
    db.delete(post)
    db.commit()


# ══════════════════════════════════════════════════════════════════════════════
#  PRÁCTICAS EXTRAMUROS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/practicas")
def listar_practicas_admin(
    estado: Optional[EstadoPracticaEnum] = Query(None),
    programa: Optional[str] = Query(None),
    q: Optional[str] = Query(None, description="Buscar por nombre, profesor o asignatura"),
    db: Session = Depends(get_db),
    _: User = _ADMIN,
):
    """Listado completo de prácticas con filtros opcionales."""
    query = db.query(Practica).options(
        joinedload(Practica.asignatura),
        joinedload(Practica.profesor),
    )
    if estado:
        query = query.filter(Practica.estado == estado)
    if programa:
        query = query.join(Practica.asignatura).filter(
            sa_func.lower(Asignatura.programa).contains(programa.lower())
        )
    if q:
        term = q.strip().lower()
        query = query.filter(
            sa_func.lower(Practica.nombre_practica).contains(term)
        )
    practicas = query.order_by(Practica.created_at.desc()).all()
    return [
        {
            "id": p.id,
            "nombre_practica": p.nombre_practica,
            "estado": p.estado.value,
            "periodo_academico": p.periodo_academico,
            "fecha_inicio": p.fecha_inicio.isoformat() if p.fecha_inicio else None,
            "fecha_fin": p.fecha_fin.isoformat() if p.fecha_fin else None,
            "asignatura": f"{p.asignatura.codigo} — {p.asignatura.nombre}" if p.asignatura else None,
            "programa": p.asignatura.programa if p.asignatura else None,
            "profesor": f"{p.profesor.nombres} {p.profesor.apellidos}" if p.profesor else None,
            "municipio": p.municipio,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in practicas
    ]


@router.delete("/practicas/{practica_id}", status_code=204)
def eliminar_practica_admin(
    practica_id: int,
    db: Session = Depends(get_db),
    _: User = _ADMIN,
):
    """Elimina una práctica y todos sus datos asociados (acción irreversible)."""
    p = db.query(Practica).filter(Practica.id == practica_id).first()
    if not p:
        raise HTTPException(404, "Práctica no encontrada")
    db.delete(p)
    db.commit()
