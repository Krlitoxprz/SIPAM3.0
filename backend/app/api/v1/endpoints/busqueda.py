"""Búsqueda global en todas las entidades del sistema (SF-07)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User, RolEnum
from app.models.convocatoria import Convocatoria, Asignatura
from app.models.practica import Practica
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/", summary="Búsqueda global (SF-07)")
def buscar(
    q: str = Query(..., min_length=2, description="Texto a buscar"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q_like = f"%{q.strip()}%"
    resultados = {"convocatorias": [], "asignaturas": [], "practicas": [], "usuarios": []}

    # Convocatorias
    convs = (
        db.query(Convocatoria)
        .filter(Convocatoria.titulo.ilike(q_like))
        .limit(8)
        .all()
    )
    for c in convs:
        resultados["convocatorias"].append({
            "id": c.id,
            "titulo": c.titulo,
            "estado": c.estado,
            "periodo": c.periodo_academico,
            "url": f"/convocatorias",
        })

    # Asignaturas
    asigs = (
        db.query(Asignatura)
        .filter(or_(Asignatura.nombre.ilike(q_like), Asignatura.codigo.ilike(q_like)))
        .limit(8)
        .all()
    )
    for a in asigs:
        resultados["asignaturas"].append({
            "id": a.id,
            "codigo": a.codigo,
            "nombre": a.nombre,
            "url": f"/configuracion",
        })

    # Prácticas
    pracs = (
        db.query(Practica)
        .filter(Practica.nombre_practica.ilike(q_like))
        .limit(8)
        .all()
    )
    for p in pracs:
        resultados["practicas"].append({
            "id": p.id,
            "nombre": p.nombre_practica,
            "estado": p.estado,
            "periodo": p.periodo_academico,
            "url": f"/practicas",
        })

    # Usuarios (solo admin, jefe_programa y decano)
    if current_user.rol in (RolEnum.admin, RolEnum.jefe_programa, RolEnum.decano):
        usuarios = (
            db.query(User)
            .filter(or_(
                User.nombres.ilike(q_like),
                User.apellidos.ilike(q_like),
                User.codigo.ilike(q_like),
                User.email.ilike(q_like),
            ))
            .limit(8)
            .all()
        )
        for u in usuarios:
            resultados["usuarios"].append({
                "id": u.id,
                "nombre": f"{u.nombres} {u.apellidos}",
                "codigo": u.codigo,
                "rol": u.rol,
                "url": f"/usuarios",
            })

    total = sum(len(v) for v in resultados.values())
    return {"query": q, "total": total, "resultados": resultados}
