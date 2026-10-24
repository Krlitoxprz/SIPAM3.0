"""Helper para registrar historial de cambios de estado (SF-06)."""
from enum import Enum
from typing import Optional, Any
from sqlalchemy.orm import Session

from app.models.historial_estado import HistorialEstado


def _str(v: Any) -> Optional[str]:
    """Convierte un enum o cualquier valor a string, o None si es None."""
    if v is None:
        return None
    if isinstance(v, Enum):
        return v.value
    return str(v)


def registrar_historial(
    db: Session,
    entidad: str,
    entidad_id: int,
    estado_anterior: Any,
    estado_nuevo: Any,
    usuario_id: Optional[int] = None,
    observaciones: Optional[str] = None,
) -> None:
    db.add(HistorialEstado(
        entidad=entidad,
        entidad_id=entidad_id,
        estado_anterior=_str(estado_anterior),
        estado_nuevo=_str(estado_nuevo),
        usuario_id=usuario_id,
        observaciones=observaciones,
    ))
    db.flush()
