"""
Módulo de perfil de usuario — edición de información personal y foto de perfil.
Endpoints:
  GET    /perfil/me          → perfil completo del usuario autenticado
  PATCH  /perfil/me          → actualizar información personal y/o contraseña
  POST   /perfil/me/foto     → subir o reemplazar foto de perfil
  DELETE /perfil/me/foto     → eliminar foto de perfil
"""
import os
import uuid
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserOut, ProfileUpdate
from app.core.security import verify_password, get_password_hash
from app.api.deps import get_current_user
from app.core.config import settings

router = APIRouter()

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FOTO_BYTES = 5 * 1024 * 1024  # 5 MB


def _foto_dir() -> str:
    path = os.path.join(settings.UPLOAD_DIR, "fotos_perfil")
    os.makedirs(path, exist_ok=True)
    return path


@router.get("/me", response_model=UserOut, summary="Obtener perfil propio")
def get_perfil(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserOut, summary="Actualizar información personal")
def update_perfil(
    body: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # ── Cambio de contraseña ────────────────────────────────────────────────
    if body.password_nuevo:
        if not body.password_actual:
            raise HTTPException(status_code=400, detail="Debes ingresar tu contraseña actual para cambiarla.")
        if not verify_password(body.password_actual, current_user.hashed_password):
            raise HTTPException(status_code=401, detail="La contraseña actual no es correcta.")
        if len(body.password_nuevo) < 8:
            raise HTTPException(status_code=422, detail="La nueva contraseña debe tener al menos 8 caracteres.")
        current_user.hashed_password = get_password_hash(body.password_nuevo)

    # ── Validar unicidad de email institucional ────────────────────────────
    if body.email and body.email != current_user.email:
        existe = db.query(User).filter(
            User.email == body.email, User.id != current_user.id
        ).first()
        if existe:
            raise HTTPException(status_code=409, detail="Ese correo institucional ya está registrado por otro usuario.")
        current_user.email = body.email

    # ── Validar unicidad de email personal ────────────────────────────────
    if body.email_personal and body.email_personal != current_user.email_personal:
        existe = db.query(User).filter(
            User.email_personal == body.email_personal, User.id != current_user.id
        ).first()
        if existe:
            raise HTTPException(status_code=409, detail="Ese correo personal ya está registrado por otro usuario.")

    # ── Actualizar campos opcionales ───────────────────────────────────────
    campos = ["nombres", "apellidos", "email_personal", "telefono",
              "bio", "fecha_nacimiento", "ciudad", "linkedin_url", "github_url",
              "eps", "arl", "fondo_pensiones"]
    for campo in campos:
        valor = getattr(body, campo)
        if valor is not None:
            setattr(current_user, campo, valor)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/foto", response_model=UserOut, summary="Subir o reemplazar foto de perfil")
async def upload_foto(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Tipo de archivo no permitido: {file.content_type}. Use JPEG, PNG, WEBP o GIF.",
        )

    contents = await file.read()
    if len(contents) > MAX_FOTO_BYTES:
        raise HTTPException(status_code=413, detail="La imagen no puede superar los 5 MB.")

    foto_dir = _foto_dir()

    # Eliminar foto anterior si existe
    if current_user.foto_url:
        old_filename = current_user.foto_url.split("/")[-1]
        old_path = os.path.join(foto_dir, old_filename)
        if os.path.exists(old_path):
            os.remove(old_path)

    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename and "." in file.filename else "jpg"
    filename = f"user_{current_user.id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(foto_dir, filename)

    with open(filepath, "wb") as f:
        f.write(contents)

    current_user.foto_url = f"/uploads/fotos_perfil/{filename}"
    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/me/foto", response_model=UserOut, summary="Eliminar foto de perfil")
def delete_foto(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.foto_url:
        raise HTTPException(status_code=404, detail="No tienes una foto de perfil configurada.")

    foto_dir = _foto_dir()
    filename = current_user.foto_url.split("/")[-1]
    filepath = os.path.join(foto_dir, filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    current_user.foto_url = None
    db.commit()
    db.refresh(current_user)
    return current_user
