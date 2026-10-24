"""
RF-MON-05 — Algoritmo de Selección de Monitores
Fórmula: (Nota_Asignatura * 0.30) + (Promedio * 0.30) + (Entrevista * 0.40)
Regla de empate: 1° Mejor entrevista  2° Mejor promedio  3° Mejor nota asignatura
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.db.database import get_db
from app.models.user import User, RolEnum
from app.models.convocatoria import Convocatoria, EstadoConvocatoriaEnum
from app.models.postulacion import Postulacion, EstadoPostulacionEnum
from app.schemas.postulacion import ResultadoSeleccionOut
from app.api.deps import require_roles
from app.utils.seleccion_utils import calcular_puntaje as _calcular_puntaje

router = APIRouter()


@router.post(
    "/convocatorias/{conv_id}/ejecutar-seleccion",
    response_model=list[ResultadoSeleccionOut],
    summary="Ejecutar algoritmo de selección de monitores (RF-MON-05)",
)
def ejecutar_seleccion(
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(RolEnum.profesor, RolEnum.jefe_programa, RolEnum.decano)
    ),
):
    conv = (
        db.query(Convocatoria)
        .options(joinedload(Convocatoria.postulaciones).joinedload(Postulacion.estudiante))
        .filter(Convocatoria.id == conv_id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")

    if current_user.rol == RolEnum.profesor and conv.profesor_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tiene permisos sobre esta convocatoria")

    if conv.estado not in [EstadoConvocatoriaEnum.cerrada, EstadoConvocatoriaEnum.en_evaluacion]:
        raise HTTPException(
            status_code=400,
            detail=f"El algoritmo solo se ejecuta en convocatorias cerradas o en evaluación. Estado actual: {conv.estado.value}",
        )

    candidatos = [
        p for p in conv.postulaciones
        if p.nota_asignatura is not None
        and p.promedio_estudiante is not None
        and p.nota_entrevista is not None
        and p.estado not in [EstadoPostulacionEnum.desistido, EstadoPostulacionEnum.no_seleccionado]
    ]

    if not candidatos:
        raise HTTPException(
            status_code=422,
            detail="No hay candidatos con nota de asignatura, promedio y nota de entrevista registrados.",
        )

    for post in candidatos:
        post.puntaje_final = _calcular_puntaje(
            float(post.nota_asignatura),
            float(post.promedio_estudiante),
            float(post.nota_entrevista),
        )

    candidatos_ordenados = sorted(
        candidatos,
        key=lambda p: (
            p.puntaje_final,
            p.nota_entrevista,
            p.promedio_estudiante,
            p.nota_asignatura,
        ),
        reverse=True,
    )

    num_cupos = conv.num_monitores_requeridos
    resultados: list[ResultadoSeleccionOut] = []

    for puesto, post in enumerate(candidatos_ordenados, start=1):
        post.puesto = puesto
        post.fecha_evaluacion = datetime.now(timezone.utc)

        if puesto <= num_cupos:
            post.estado = EstadoPostulacionEnum.seleccionado
        else:
            post.estado = EstadoPostulacionEnum.no_seleccionado

        resultados.append(
            ResultadoSeleccionOut(
                postulacion_id=post.id,
                estudiante_codigo=post.estudiante.codigo,
                estudiante_nombre=f"{post.estudiante.nombres} {post.estudiante.apellidos}",
                nota_asignatura=post.nota_asignatura,
                promedio=post.promedio_estudiante,
                nota_entrevista=post.nota_entrevista,
                puntaje_final=post.puntaje_final,
                puesto=puesto,
                estado=post.estado,
            )
        )

    for p in conv.postulaciones:
        if p not in candidatos and p.estado != EstadoPostulacionEnum.desistido:
            p.estado = EstadoPostulacionEnum.no_seleccionado

    if conv.estado == EstadoConvocatoriaEnum.cerrada:
        conv.estado = EstadoConvocatoriaEnum.en_evaluacion

    db.commit()
    return resultados


@router.get(
    "/convocatorias/{conv_id}/resultados",
    response_model=list[ResultadoSeleccionOut],
    summary="Consultar resultados de selección de una convocatoria",
)
def resultados_seleccion(
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(
        RolEnum.profesor, RolEnum.jefe_programa, RolEnum.decano, RolEnum.estudiante
    )),
):
    conv = db.query(Convocatoria).filter(Convocatoria.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")

    q = (
        db.query(Postulacion)
        .options(joinedload(Postulacion.estudiante))
        .filter(
            Postulacion.convocatoria_id == conv_id,
            Postulacion.puntaje_final.isnot(None),
        )
    )

    if current_user.rol == RolEnum.estudiante:
        q = q.filter(Postulacion.estudiante_id == current_user.id)

    postulaciones = q.order_by(Postulacion.puesto).all()

    return [
        ResultadoSeleccionOut(
            postulacion_id=p.id,
            estudiante_codigo=p.estudiante.codigo,
            estudiante_nombre=f"{p.estudiante.nombres} {p.estudiante.apellidos}",
            nota_asignatura=p.nota_asignatura,
            promedio=p.promedio_estudiante,
            nota_entrevista=p.nota_entrevista,
            puntaje_final=p.puntaje_final,
            puesto=p.puesto,
            estado=p.estado,
        )
        for p in postulaciones
    ]
