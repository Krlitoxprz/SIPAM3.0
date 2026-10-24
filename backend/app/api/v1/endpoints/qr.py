"""
SF-12 — Generación de códigos QR para verificación de documentos SIPAM-USCO.
GET /qr/convocatoria/{id}  → QR con URL al FO-14
GET /qr/practica/{id}      → QR con URL al FO-15
GET /qr/postulacion/{id}   → QR con datos básicos de la postulación
"""
import io
import qrcode
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.convocatoria import Convocatoria
from app.models.practica import Practica
from app.models.postulacion import Postulacion
from app.core.config import settings

router = APIRouter()


def _generate_qr_png(data: str) -> bytes:
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=3)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#8D191D", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _qr_response(data: str, filename: str) -> StreamingResponse:
    png = _generate_qr_png(data)
    return StreamingResponse(
        io.BytesIO(png),
        media_type="image/png",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.get("/convocatoria/{conv_id}", summary="QR de convocatoria (SF-12)")
def qr_convocatoria(
    conv_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    conv = db.query(Convocatoria).filter(Convocatoria.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")
    url = f"{settings.FRONTEND_URL}/convocatorias?id={conv_id}"
    data = f"SIPAM-USCO | Convocatoria #{conv_id}\n{conv.titulo}\nEstado: {conv.estado}\nURL: {url}"
    return _qr_response(data, f"qr_convocatoria_{conv_id}.png")


@router.get("/practica/{practica_id}", summary="QR de práctica extramural (SF-12)")
def qr_practica(
    practica_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    p = db.query(Practica).filter(Practica.id == practica_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Práctica no encontrada")
    url = f"{settings.FRONTEND_URL}/practicas?id={practica_id}"
    data = f"SIPAM-USCO | Práctica #{practica_id}\n{p.nombre_practica}\nEstado: {p.estado}\nURL: {url}"
    return _qr_response(data, f"qr_practica_{practica_id}.png")


@router.get("/postulacion/{post_id}", summary="QR de postulación (SF-12)")
def qr_postulacion(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(Postulacion).filter(Postulacion.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")
    if current_user.rol.value == "estudiante" and post.estudiante_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sin permiso para este QR")
    data = (
        f"SIPAM-USCO | Postulación #{post_id}\n"
        f"Convocatoria: {post.convocatoria.titulo if post.convocatoria else '—'}\n"
        f"Estado: {post.estado}\n"
        f"Verificado en: {settings.FRONTEND_URL}"
    )
    return _qr_response(data, f"qr_postulacion_{post_id}.png")
