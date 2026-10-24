import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload

from app.db.database import get_db, es_modo_prueba
from app.models.user import User, RolEnum
from app.models.convocatoria import Convocatoria, EstadoConvocatoriaEnum
from app.models.postulacion import Postulacion, ArchivoAdjunto, EstadoPostulacionEnum
from app.schemas.postulacion import (
    PostulacionCreate, PostulacionOut, NotaEntrevistaRequest,
    ResultadoSeleccionOut, ArchivoAdjuntoOut,
)
from app.api.deps import get_current_user, require_roles
from app.core.config import settings
from app.utils.file_security import validate_and_save
from app.utils.seleccion_utils import calcular_puntaje as _calcular_puntaje

router = APIRouter()

TIPOS_DOCUMENTO_VALIDOS = {"cedula", "rut", "certificado_bancario"}


@router.post(
    "/convocatoria/{conv_id}",
    response_model=PostulacionOut,
    status_code=201,
    summary="Postularse a una convocatoria (RF-MON-02)",
)
def postularse(
    conv_id: int,
    body: PostulacionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.estudiante)),
):
    conv = db.query(Convocatoria).filter(Convocatoria.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")

    modo_prueba = es_modo_prueba(db)

    if conv.estado != EstadoConvocatoriaEnum.abierta and not modo_prueba:
        raise HTTPException(status_code=400, detail="La convocatoria no está abierta para postulaciones")
    if conv.estado == EstadoConvocatoriaEnum.finalizada:
        raise HTTPException(status_code=400, detail="La convocatoria ya fue finalizada")

    # RF-MON-TIME-01 (Acuerdo 012/2023 Art.6): respetar ventana de postulación
    hoy = datetime.now(timezone.utc)
    if not modo_prueba:
        if conv.fecha_inicio_postulacion and hoy < conv.fecha_inicio_postulacion:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"El período de postulación aún no ha iniciado. "
                    f"Inicio: {conv.fecha_inicio_postulacion.strftime('%d/%m/%Y a las %H:%M')}."
                ),
            )
        if conv.fecha_fin_postulacion and hoy > conv.fecha_fin_postulacion:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"El período de postulación ha cerrado. "
                    f"Finalizó el {conv.fecha_fin_postulacion.strftime('%d/%m/%Y a las %H:%M')}."
                ),
            )

    ya_postulado = db.query(Postulacion).filter(
        Postulacion.convocatoria_id == conv_id,
        Postulacion.estudiante_id == current_user.id,
    ).first()
    if ya_postulado:
        raise HTTPException(status_code=409, detail="Ya tienes una postulación activa en esta convocatoria")

    # Acuerdo 012/2023 Art.4.c — sanción disciplinaria
    if current_user.sancionado_disciplinariamente and not modo_prueba:
        raise HTTPException(
            status_code=403,
            detail="No puede postularse: tiene una sanción disciplinaria vigente (Acuerdo 012/2023 Art.4.c).",
        )

    promedio = current_user.promedio or 0.0
    pct_creditos = current_user.porcentaje_creditos or 0.0
    # Los requisitos académicos se aplican SIEMPRE — el modo_prueba solo omite
    # restricciones de fechas y estado de convocatoria, nunca los requisitos del estudiante.
    motivos: list[str] = []
    if promedio < conv.promedio_minimo:
        motivos.append(f"Promedio {promedio:.2f} < mínimo requerido {conv.promedio_minimo:.2f}")
    if pct_creditos < conv.creditos_minimo_pct:
        motivos.append(f"Créditos aprobados {pct_creditos:.1f}% < mínimo requerido {conv.creditos_minimo_pct:.1f}%")
    if motivos:
        raise HTTPException(
            status_code=422,
            detail={"mensaje": "No cumple los requisitos académicos", "motivos": motivos},
        )

    post = Postulacion(
        convocatoria_id=conv_id,
        estudiante_id=current_user.id,
        promedio_estudiante=promedio,
        carta_motivacion=body.carta_motivacion,
        estado=EstadoPostulacionEnum.pendiente,
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    post = (
        db.query(Postulacion)
        .options(
            joinedload(Postulacion.convocatoria).joinedload(Convocatoria.asignatura),
            joinedload(Postulacion.convocatoria).joinedload(Convocatoria.profesor),
            joinedload(Postulacion.estudiante),
            joinedload(Postulacion.archivos),
        )
        .filter(Postulacion.id == post.id)
        .first()
    )
    return post


@router.post(
    "/{post_id}/documentos",
    response_model=ArchivoAdjuntoOut,
    summary="Subir documento adjunto (RF-MON-03)",
    description="Sube Cédula, RUT o Certificado Bancario en PDF. El archivo se renombra como [Codigo]_[TipoDocumento].pdf",
)
async def subir_documento(
    post_id: int,
    tipo_documento: str = Form(..., description="Valores: cedula | rut | certificado_bancario"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.estudiante)),
):
    tipo_doc = tipo_documento.lower().strip()
    if tipo_doc not in TIPOS_DOCUMENTO_VALIDOS:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de documento inválido. Permitidos: {list(TIPOS_DOCUMENTO_VALIDOS)}",
        )

    post = (
        db.query(Postulacion)
        .options(joinedload(Postulacion.convocatoria))
        .filter(
            Postulacion.id == post_id,
            Postulacion.estudiante_id == current_user.id,
        )
        .first()
    )
    if not post:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")

    # No se puede subir documentos si la convocatoria ya fue finalizada
    if post.convocatoria and post.convocatoria.estado == EstadoConvocatoriaEnum.finalizada:
        raise HTTPException(
            status_code=400,
            detail="No se pueden subir documentos: la convocatoria ya fue finalizada.",
        )

    nombre_original = file.filename or f"{tipo_doc}.pdf"
    safe_name, ruta_completa = await validate_and_save(
        file,
        subfolder="postulaciones",
        allowed_extensions=[".pdf"],
        upload_dir=settings.UPLOAD_DIR,
        max_bytes=settings.MAX_FILE_SIZE_MB * 1024 * 1024,
    )
    ruta_relativa = os.path.join("postulaciones", safe_name)
    tamanio = os.path.getsize(ruta_completa)

    existente = db.query(ArchivoAdjunto).filter(
        ArchivoAdjunto.postulacion_id == post_id,
        ArchivoAdjunto.tipo_documento == tipo_doc,
    ).first()
    if existente:
        # Eliminar archivo anterior del disco
        old_path = os.path.join(settings.UPLOAD_DIR, existente.ruta_archivo) if not os.path.isabs(existente.ruta_archivo) else existente.ruta_archivo
        if os.path.exists(old_path):
            os.remove(old_path)
        existente.nombre_original = nombre_original
        existente.nombre_almacenado = safe_name
        existente.ruta_archivo = ruta_relativa
        existente.tamanio_bytes = tamanio
        archivo = existente
    else:
        archivo = ArchivoAdjunto(
            postulacion_id=post_id,
            usuario_id=current_user.id,
            tipo_documento=tipo_doc,
            nombre_original=nombre_original,
            nombre_almacenado=safe_name,
            ruta_archivo=ruta_relativa,
            tamanio_bytes=tamanio,
        )
        db.add(archivo)

    db.flush()  # materialise pending INSERT before counting (autoflush=False)
    docs_subidos = (
        db.query(ArchivoAdjunto)
        .filter(ArchivoAdjunto.postulacion_id == post_id)
        .count()
    )
    post.documentos_completos = docs_subidos >= 3
    if post.estado == EstadoPostulacionEnum.pendiente and docs_subidos > 0:
        post.estado = EstadoPostulacionEnum.en_revision

    db.commit()
    db.refresh(archivo)
    return archivo


@router.get("/mis-postulaciones", response_model=list[PostulacionOut])
def mis_postulaciones(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.estudiante)),
):
    postulaciones = (
        db.query(Postulacion)
        .options(
            joinedload(Postulacion.convocatoria).joinedload(Convocatoria.asignatura),
            joinedload(Postulacion.convocatoria).joinedload(Convocatoria.profesor),
            joinedload(Postulacion.archivos),
        )
        .filter(Postulacion.estudiante_id == current_user.id)
        .order_by(Postulacion.fecha_postulacion.desc())
        .all()
    )
    return postulaciones


@router.get("/convocatoria/{conv_id}", response_model=list[PostulacionOut])
def postulantes_de_convocatoria(
    conv_id: int,
    estado: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(RolEnum.profesor, RolEnum.jefe_programa, RolEnum.decano)
    ),
):
    conv = db.query(Convocatoria).filter(Convocatoria.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")
    if current_user.rol == RolEnum.profesor and conv.profesor_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tiene permisos sobre esta convocatoria")

    q = (
        db.query(Postulacion)
        .options(
            joinedload(Postulacion.estudiante),
            joinedload(Postulacion.archivos),
        )
        .filter(Postulacion.convocatoria_id == conv_id)
    )
    if estado:
        q = q.filter(Postulacion.estado == estado)
    return q.order_by(Postulacion.fecha_postulacion).all()


@router.patch("/{post_id}/nota-asignatura", response_model=PostulacionOut)
def registrar_nota_asignatura(
    post_id: int,
    nota: float = Query(..., ge=0.0, le=5.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.profesor)),
):
    post = (
        db.query(Postulacion)
        .options(joinedload(Postulacion.convocatoria))
        .filter(Postulacion.id == post_id)
        .first()
    )
    if not post:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")
    if post.convocatoria.profesor_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tiene permisos sobre esta postulación")
    
    # Validar estado de la convocatoria
    if post.convocatoria.estado not in [EstadoConvocatoriaEnum.cerrada, EstadoConvocatoriaEnum.en_evaluacion]:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede evaluar: la convocatoria está en estado '{post.convocatoria.estado.value}'. Solo se permite evaluar en estados 'cerrada' o 'en_evaluacion'."
        )

    post.nota_asignatura = round(nota, 2)
    db.commit()
    db.refresh(post)
    return post


@router.patch("/{post_id}/entrevista", response_model=PostulacionOut)
def registrar_entrevista(
    post_id: int,
    body: NotaEntrevistaRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.profesor)),
):
    if not (0.0 <= body.nota_entrevista <= 5.0):
        raise HTTPException(status_code=400, detail="La nota debe estar entre 0.0 y 5.0")

    post = (
        db.query(Postulacion)
        .options(joinedload(Postulacion.convocatoria))
        .filter(Postulacion.id == post_id)
        .first()
    )
    if not post:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")
    if post.convocatoria.profesor_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tiene permisos sobre esta postulación")
    
    # Validar estado de la convocatoria
    if post.convocatoria.estado not in [EstadoConvocatoriaEnum.cerrada, EstadoConvocatoriaEnum.en_evaluacion]:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede evaluar: la convocatoria está en estado '{post.convocatoria.estado.value}'. Solo se permite evaluar en estados 'cerrada' o 'en_evaluacion'."
        )

    post.nota_entrevista = round(body.nota_entrevista, 2)
    post.observaciones_evaluador = body.observaciones
    post.fecha_entrevista = datetime.now(timezone.utc)
    db.commit()
    db.refresh(post)
    return post


@router.patch("/{post_id}/desistir", response_model=PostulacionOut, summary="Retirar postulación (SF-01)")
def desistir_postulacion(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.estudiante)),
):
    post = (
        db.query(Postulacion)
        .options(
            joinedload(Postulacion.convocatoria).joinedload(Convocatoria.asignatura),
            joinedload(Postulacion.convocatoria).joinedload(Convocatoria.profesor),
            joinedload(Postulacion.estudiante),
            joinedload(Postulacion.archivos),
        )
        .filter(Postulacion.id == post_id, Postulacion.estudiante_id == current_user.id)
        .first()
    )
    if not post:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")
    if post.estado == EstadoPostulacionEnum.desistido:
        raise HTTPException(status_code=400, detail="La postulación ya fue retirada")
    if post.estado in (EstadoPostulacionEnum.seleccionado, EstadoPostulacionEnum.no_seleccionado):
        raise HTTPException(
            status_code=400,
            detail="No se puede retirar una postulación luego de ejecutarse la selección",
        )
    conv_estado = post.convocatoria.estado if post.convocatoria else None
    if conv_estado not in (EstadoConvocatoriaEnum.abierta, EstadoConvocatoriaEnum.cerrada):
        raise HTTPException(
            status_code=400,
            detail="Solo puedes retirar tu postulación mientras la convocatoria está abierta o cerrada",
        )
    post.estado = EstadoPostulacionEnum.desistido

    # Notificar al profesor
    try:
        from app.models.notificacion import Notificacion
        nombre_est = f"{current_user.nombres} {current_user.apellidos}"
        titulo_conv = post.convocatoria.titulo if post.convocatoria else f"#{post.convocatoria_id}"
        if post.convocatoria and post.convocatoria.profesor_id:
            db.add(Notificacion(
                usuario_id=post.convocatoria.profesor_id,
                titulo="Postulante se retiró",
                mensaje=f"{nombre_est} retiró su postulación de la convocatoria «{titulo_conv}».",
                tipo="postulacion",
            ))
    except Exception:
        pass

    db.commit()
    db.refresh(post)
    return post


@router.get(
    "/documentos/{archivo_id}/descargar",
    summary="Descarga autenticada de documento adjunto a postulación",
)
def descargar_documento(
    archivo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Accesible por:
    - El estudiante dueño de la postulación
    - Profesores y jefe de programa
    """
    archivo = db.query(ArchivoAdjunto).filter(ArchivoAdjunto.id == archivo_id).first()
    if not archivo:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    if current_user.rol == RolEnum.estudiante and archivo.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permisos para acceder a este documento")

    full_path = os.path.join(settings.UPLOAD_DIR, archivo.ruta_archivo)
    # Protección contra path traversal
    base = os.path.abspath(settings.UPLOAD_DIR)
    resolved = os.path.abspath(full_path)
    if not resolved.startswith(base):
        raise HTTPException(status_code=400, detail="Ruta de archivo inválida")

    if not os.path.exists(resolved):
        raise HTTPException(status_code=404, detail="Archivo no encontrado en el servidor")

    return FileResponse(
        path=resolved,
        filename=archivo.nombre_original,
        media_type="application/octet-stream",
    )
