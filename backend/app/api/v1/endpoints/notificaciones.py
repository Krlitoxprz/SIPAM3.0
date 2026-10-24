"""Notificaciones in-app para todos los roles."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.notificacion import Notificacion
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/")
def mis_notificaciones(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    nots = (
        db.query(Notificacion)
        .filter(Notificacion.usuario_id == current_user.id)
        .order_by(Notificacion.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": n.id,
            "tipo": n.tipo,
            "titulo": n.titulo,
            "mensaje": n.mensaje,
            "leida": n.leida,
            "url": n.url,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in nots
    ]


@router.get("/no-leidas/count")
def count_no_leidas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = (
        db.query(Notificacion)
        .filter(Notificacion.usuario_id == current_user.id, Notificacion.leida == False)
        .count()
    )
    return {"count": count}


@router.patch("/{nid}/leer")
def marcar_leida(
    nid: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    n = db.query(Notificacion).filter(
        Notificacion.id == nid,
        Notificacion.usuario_id == current_user.id,
    ).first()
    if n:
        n.leida = True
        db.commit()
    return {"ok": True}


@router.patch("/leer-todas")
def marcar_todas_leidas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(Notificacion).filter(
        Notificacion.usuario_id == current_user.id,
        Notificacion.leida == False,
    ).update({"leida": True})
    db.commit()
    return {"ok": True}


@router.delete("/{nid}")
def eliminar_notificacion(
    nid: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(Notificacion).filter(
        Notificacion.id == nid,
        Notificacion.usuario_id == current_user.id,
    ).delete()
    db.commit()
    return {"ok": True}
