"""Utilidad para crear notificaciones desde cualquier endpoint."""
from sqlalchemy.orm import Session
from app.models.notificacion import Notificacion


def crear_notificacion(
    db: Session,
    usuario_id: int,
    tipo: str,
    titulo: str,
    mensaje: str,
    url: str | None = None,
) -> Notificacion:
    n = Notificacion(
        usuario_id=usuario_id,
        tipo=tipo,
        titulo=titulo,
        mensaje=mensaje,
        url=url,
    )
    db.add(n)
    db.flush()
    return n
