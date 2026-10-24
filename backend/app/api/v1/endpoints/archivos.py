"""
Secure file access endpoint with JWT authentication and RBAC.
Files are served with access control - users can only access their own files
or files they have permission to view based on their role.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
import os

from app.api.deps import get_current_user, get_db
from app.models.user import User, RolEnum
from app.models.postulacion import ArchivoAdjunto
from app.core.config import settings

router = APIRouter()


@router.get("/{archivo_id}")
async def descargar_archivo(
    archivo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Descargar un archivo subido con control de acceso basado en roles.

    - **archivo_id**: ID del archivo en la base de datos
    - Requiere autenticación JWT
    - Los estudiantes solo pueden descargar sus propios archivos
    - Los roles con permisos especiales (JEFE001, GASTOS001, admin) pueden descargar
      archivos relacionados con su trabajo
    """
    archivo = db.query(ArchivoAdjunto).filter(ArchivoAdjunto.id == archivo_id).first()

    if not archivo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo no encontrado"
        )

    # Verificar permisos de acceso
    # Propietario del archivo
    if archivo.usuario_id == current_user.id:
        pass  # Permitido

    # Roles con acceso especial
    elif current_user.rol in [RolEnum.admin, RolEnum.jefe_programa, RolEnum.decano]:
        pass  # Permitido

    # Estudiantes solo pueden acceder a sus propios archivos
    elif current_user.rol == RolEnum.estudiante:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para acceder a este archivo"
        )

    # Profesores solo pueden acceder si es su archivo
    elif current_user.rol == RolEnum.profesor:
        if archivo.usuario_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para acceder a este archivo"
            )

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para acceder a este archivo"
        )

    # Verificar que el archivo existe físicamente
    ruta_archivo = archivo.ruta_completa if archivo.ruta_completa else archivo.ruta_archivo
    if not os.path.exists(ruta_archivo):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El archivo físico no existe en el servidor"
        )

    # Devolver el archivo con el nombre original
    return FileResponse(
        path=ruta_archivo,
        filename=archivo.nombre_original,
        media_type=archivo.tipo_mime or "application/octet-stream"
    )


@router.get("/metadata/{archivo_id}")
async def obtener_metadata_archivo(
    archivo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener metadatos de un archivo sin descargarlo.
    Útil para verificar permisos antes de descargar.
    """
    archivo = db.query(ArchivoAdjunto).filter(ArchivoAdjunto.id == archivo_id).first()

    if not archivo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo no encontrado"
        )

    # Mismas verificaciones de permisos que el endpoint de descarga
    if (archivo.usuario_id != current_user.id and
        current_user.rol not in [RolEnum.admin, RolEnum.jefe_programa, RolEnum.decano]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para acceder a este archivo"
        )

    return {
        "id": archivo.id,
        "nombre_original": archivo.nombre_original,
        "tipo_mime": archivo.tipo_mime,
        "tamano_bytes": archivo.tamanio_bytes,
        "categoria": archivo.categoria,
        "fecha_subida": archivo.uploaded_at,
        "usuario_id": archivo.usuario_id
    }
