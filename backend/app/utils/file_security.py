"""Utilidades de seguridad para archivos subidos al servidor."""
import os
import uuid
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.models.postulacion import ArchivoAdjunto

# Tipos MIME permitidos por extensión visible
ALLOWED_TYPES: dict[str, bytes] = {
    ".pdf":  b"%PDF",
    ".png":  b"\x89PNG",
    ".jpg":  b"\xff\xd8\xff",
    ".jpeg": b"\xff\xd8\xff",
    ".doc":  b"\xd0\xcf\x11\xe0",
    ".docx": b"PK\x03\x04",
    ".xlsx": b"PK\x03\x04",
}

MAX_BYTES = int(os.environ.get("MAX_FILE_SIZE_MB", "5")) * 1024 * 1024


async def validate_and_save(
    file: UploadFile,
    subfolder: str,
    allowed_extensions: list[str],
    usuario_id: int,
    tipo_documento: str,
    postulacion_id: int = None,
    upload_dir: str = "uploads",
    max_bytes: int = MAX_BYTES,
    db: Session = None,
) -> ArchivoAdjunto:
    """
    Valida extensión, magic bytes y tamaño. Guarda con nombre UUID seguro.
    Crea registro en base de datos con metadatos.
    Retorna objeto ArchivoAdjunto.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo requerido")

    ext = os.path.splitext(file.filename.lower())[1]
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Extensión no permitida. Tipos aceptados: {allowed_extensions}",
        )

    content = await file.read()

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="El archivo está vacío")
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"El archivo supera el límite de {max_bytes // (1024*1024)} MB",
        )

    # Validar magic bytes (MIME real)
    expected_magic = ALLOWED_TYPES.get(ext)
    if expected_magic and not content.startswith(expected_magic):
        raise HTTPException(
            status_code=400,
            detail="El contenido del archivo no coincide con su extensión (posible archivo malicioso)",
        )

    # Nombre seguro con UUID para evitar colisiones y path traversal
    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest_dir = os.path.join(upload_dir, subfolder)
    os.makedirs(dest_dir, exist_ok=True)
    full_path = os.path.join(dest_dir, safe_name)

    with open(full_path, "wb") as f:
        f.write(content)

    # Crear registro en base de datos
    archivo = ArchivoAdjunto(
        usuario_id=usuario_id,
        postulacion_id=postulacion_id,
        tipo_documento=tipo_documento,
        nombre_original=file.filename,
        nombre_almacenado=safe_name,
        ruta_archivo=subfolder + "/" + safe_name,
        ruta_completa=full_path,
        tipo_mime=file.content_type,
        tamanio_bytes=len(content),
        categoria=tipo_documento
    )

    if db:
        db.add(archivo)
        db.commit()
        db.refresh(archivo)

    return archivo
