from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from typing import Optional

from app.db.database import get_db
from app.models.user import User, RolEnum
from app.models.convocatoria import Convocatoria, Asignatura, AsignaturaEstudiante, EstadoConvocatoriaEnum, MonitoriaPlantilla
from app.models.postulacion import Postulacion
from app.schemas.convocatoria import (
    ConvocatoriaCreate, ConvocatoriaUpdate, ConvocatoriaOut,
    CambiarEstadoRequest, AsignaturaOut,
)
from app.api.deps import get_current_user, require_roles
from app.utils.historial import registrar_historial
from app.utils.notificaciones import crear_notificacion
from app.models.presupuesto import ConfiguracionCalendario

from app.db.database import es_modo_prueba

router = APIRouter()

# ── Reglas de tiempo Acuerdo 012/2023 ────────────────────────────────────────
DIAS_MINIMOS_POSTULACION = 5   # Art.6: mínimo 5 días hábiles de ventana de postulación
DIAS_MAXIMOS_POSTULACION = 20  # razonable: máximo 20 días corridos de postulación
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/plantillas", summary="Catálogo de monitorías por asignatura (Acuerdo 012/2023)")
def listar_plantillas_monitoria(
    programa: Optional[str] = Query(None),
    asignatura_id: Optional[int] = Query(None),
    profesor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista plantillas de monitorías. Filtrable por programa, asignatura_id y profesor_id.
    Si el usuario es profesor, se pre-filtra a sus propias asignaturas.
    """
    q = db.query(MonitoriaPlantilla)

    if current_user.rol == RolEnum.profesor:
        # Obtener IDs de asignaturas asignadas al profesor
        asig_ids = [
            a.id for a in db.query(Asignatura.id)
            .filter(Asignatura.profesor_id == current_user.id, Asignatura.is_active == True)
            .all()
        ]
        q = q.filter(MonitoriaPlantilla.asignatura_id.in_(asig_ids))
    elif profesor_id:
        asig_ids = [
            a.id for a in db.query(Asignatura.id)
            .filter(Asignatura.profesor_id == profesor_id, Asignatura.is_active == True)
            .all()
        ]
        q = q.filter(MonitoriaPlantilla.asignatura_id.in_(asig_ids))

    if programa:
        q = q.filter(MonitoriaPlantilla.programa == programa)
    if asignatura_id:
        q = q.filter(MonitoriaPlantilla.asignatura_id == asignatura_id)

    def _f(v):
        return float(v) if v is not None else None

    return [
        {
            "id": p.id,
            "nombre_sugerido": p.nombre_sugerido,
            "programa": p.programa,
            "asignatura_id": p.asignatura_id,
            "asignatura_nombre": p.asignatura_nombre,
            "tipo_monitoria": p.tipo_monitoria,
            "descripcion_actividades": p.descripcion_actividades,
            "horas_semana": p.horas_semana,
            "horas_semestre": p.horas_semestre,
            "promedio_minimo": _f(p.promedio_minimo),
            "creditos_minimo_pct": _f(p.creditos_minimo_pct),
            "num_monitores_sugerido": p.num_monitores_sugerido,
            "semestre_asignatura": p.semestre_asignatura,
            "creditos_asignatura": p.creditos_asignatura,
            "caracter_curso": p.caracter_curso,
        }
        for p in q.order_by(MonitoriaPlantilla.programa, MonitoriaPlantilla.asignatura_nombre).all()
    ]


@router.get("/asignaturas/todas", response_model=list[AsignaturaOut])
def todas_asignaturas(
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import func as sa_func
    q = db.query(Asignatura)
    if not include_inactive or current_user.rol not in (RolEnum.jefe_programa, RolEnum.decano):
        q = q.filter(Asignatura.is_active == True)
    if current_user.rol == RolEnum.profesor:
        asig_propias = q.filter(Asignatura.profesor_id == current_user.id).all()
        if asig_propias:
            asigs = sorted(asig_propias, key=lambda a: (a.semestre, a.nombre))
        elif current_user.programa:
            asigs = q.filter(Asignatura.programa == current_user.programa).order_by(
                Asignatura.semestre, Asignatura.nombre
            ).all()
        else:
            asigs = []
    else:
        asigs = q.order_by(Asignatura.semestre, Asignatura.nombre).all()

    if asigs:
        ids = [a.id for a in asigs]
        counts = dict(
            db.query(AsignaturaEstudiante.asignatura_id, sa_func.count(AsignaturaEstudiante.id))
            .filter(AsignaturaEstudiante.asignatura_id.in_(ids))
            .group_by(AsignaturaEstudiante.asignatura_id)
            .all()
        )
    else:
        counts = {}

    result = []
    for a in asigs:
        out = AsignaturaOut.model_validate(a)
        out = out.model_copy(update={"num_estudiantes": counts.get(a.id, 0)})
        result.append(out)
    return result


class AsignaturaCreate(BaseModel):
    codigo: str
    nombre: str
    creditos: int
    programa: str
    facultad: Optional[str] = None
    semestre: int
    profesor_id: Optional[int] = None
    is_active: bool = True


@router.post("/asignaturas/", response_model=AsignaturaOut, status_code=201)
def crear_asignatura(
    body: AsignaturaCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.jefe_programa, RolEnum.admin)),
):
    if db.query(Asignatura).filter(Asignatura.codigo == body.codigo).first():
        raise HTTPException(status_code=400, detail="Ya existe una asignatura con ese código")
    a = Asignatura(**body.model_dump())
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


@router.patch("/asignaturas/{asig_id}", response_model=AsignaturaOut)
def actualizar_asignatura(
    asig_id: int,
    body: AsignaturaCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.jefe_programa, RolEnum.admin)),
):
    a = db.query(Asignatura).filter(Asignatura.id == asig_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Asignatura no encontrada")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(a, k, v)
    db.commit()
    db.refresh(a)
    return a


@router.get("/asignaturas/{asig_id}/estudiantes")
def estudiantes_asignatura(
    asig_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.jefe_programa, RolEnum.decano, RolEnum.profesor)),
):
    matriculas = (
        db.query(AsignaturaEstudiante)
        .filter(AsignaturaEstudiante.asignatura_id == asig_id)
        .all()
    )
    return [
        {
            "id": m.id,
            "estudiante_id": m.estudiante_id,
            "nombre": f"{m.estudiante.nombres} {m.estudiante.apellidos}" if m.estudiante else "—",
            "codigo": m.estudiante.codigo if m.estudiante else "—",
            "periodo_academico": m.periodo_academico,
        }
        for m in matriculas
    ]


class MatriculaIn(BaseModel):
    estudiante_id: int
    periodo_academico: str


@router.post("/asignaturas/{asig_id}/matricular", status_code=201)
def matricular_estudiante(
    asig_id: int,
    body: MatriculaIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.jefe_programa, RolEnum.admin)),
):
    exists = db.query(AsignaturaEstudiante).filter(
        AsignaturaEstudiante.asignatura_id == asig_id,
        AsignaturaEstudiante.estudiante_id == body.estudiante_id,
        AsignaturaEstudiante.periodo_academico == body.periodo_academico,
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="El estudiante ya está matriculado en esta asignatura")
    m = AsignaturaEstudiante(
        asignatura_id=asig_id,
        estudiante_id=body.estudiante_id,
        periodo_academico=body.periodo_academico,
    )
    db.add(m)
    db.commit()
    return {"ok": True}


@router.delete("/asignaturas/matricula/{matricula_id}")
def desmatricular_estudiante(
    matricula_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.jefe_programa, RolEnum.admin)),
):
    matricula = db.query(AsignaturaEstudiante).filter(AsignaturaEstudiante.id == matricula_id).first()
    if not matricula:
        raise HTTPException(status_code=404, detail="Matrícula no encontrada")
    db.delete(matricula)
    db.commit()
    return {"ok": True}


TRANSICIONES_VALIDAS: dict[EstadoConvocatoriaEnum, list[EstadoConvocatoriaEnum]] = {
    EstadoConvocatoriaEnum.borrador: [EstadoConvocatoriaEnum.abierta],
    EstadoConvocatoriaEnum.abierta: [EstadoConvocatoriaEnum.cerrada],
    EstadoConvocatoriaEnum.cerrada: [EstadoConvocatoriaEnum.en_evaluacion],
    EstadoConvocatoriaEnum.en_evaluacion: [EstadoConvocatoriaEnum.finalizada],
    EstadoConvocatoriaEnum.finalizada: [],
}


def _enrich(conv: Convocatoria, db: Session) -> ConvocatoriaOut:
    total = db.query(Postulacion).filter(Postulacion.convocatoria_id == conv.id).count()
    out = ConvocatoriaOut.model_validate(conv)
    out.total_postulantes = total
    return out


@router.get("/", response_model=list[ConvocatoriaOut])
def listar_convocatorias(
    estado: Optional[str] = Query(None),
    periodo: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Convocatoria).options(
        joinedload(Convocatoria.asignatura),
        joinedload(Convocatoria.profesor),
    )
    if estado:
        q = q.filter(Convocatoria.estado == estado)
    if periodo:
        q = q.filter(Convocatoria.periodo_academico == periodo)

    if current_user.rol == RolEnum.profesor:
        q = q.filter(Convocatoria.profesor_id == current_user.id)
    elif current_user.rol == RolEnum.jefe_programa and current_user.programa:
        q = q.filter(Convocatoria.asignatura.has(Asignatura.programa == current_user.programa))
    elif current_user.rol == RolEnum.estudiante:
        q = q.filter(Convocatoria.estado.in_([
            EstadoConvocatoriaEnum.abierta,
            EstadoConvocatoriaEnum.cerrada,
            EstadoConvocatoriaEnum.en_evaluacion,
            EstadoConvocatoriaEnum.finalizada,
        ]))

    # Auto-cerrar convocatorias cuyo plazo de postulación ya venció
    now = datetime.now(timezone.utc)
    vencidas = (
        db.query(Convocatoria)
        .filter(
            Convocatoria.estado == EstadoConvocatoriaEnum.abierta,
            Convocatoria.fecha_fin_postulacion < now,
        )
        .all()
    )
    if vencidas:
        for cv in vencidas:
            cv.estado = EstadoConvocatoriaEnum.cerrada
        db.commit()

    convocatorias = q.order_by(Convocatoria.created_at.desc()).all()
    return [_enrich(c, db) for c in convocatorias]


@router.get("/profesores", response_model=list)
def listar_profesores(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.jefe_programa, RolEnum.decano)),
):
    profesores = db.query(User).filter(User.rol == RolEnum.profesor, User.is_active == True).all()
    return [{"id": p.id, "codigo": p.codigo, "nombre": f"{p.nombres} {p.apellidos}"} for p in profesores]


@router.get("/mis-materias", summary="Materias del profesor con estudiantes matriculados")
def mis_materias(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.profesor)),
):
    """Retorna las asignaturas asignadas al profesor con la lista de estudiantes matriculados."""
    asignaturas = (
        db.query(Asignatura)
        .options(joinedload(Asignatura.matriculas).joinedload(AsignaturaEstudiante.estudiante))
        .filter(Asignatura.profesor_id == current_user.id, Asignatura.is_active == True)
        .all()
    )
    return [
        {
            "id": a.id,
            "codigo": a.codigo,
            "nombre": a.nombre,
            "semestre": a.semestre,
            "creditos": a.creditos,
            "total_estudiantes": len(a.matriculas),
            "estudiantes": [
                {
                    "id": m.estudiante.id,
                    "codigo": m.estudiante.codigo,
                    "nombre": f"{m.estudiante.nombres} {m.estudiante.apellidos}",
                    "promedio": m.estudiante.promedio,
                    "apto_monitoria": (
                        (m.estudiante.promedio or 0) >= 3.5
                        and (m.estudiante.porcentaje_creditos or 0) >= 30.0
                    ),
                }
                for m in a.matriculas
                if m.estudiante is not None
            ],
        }
        for a in asignaturas
    ]


@router.get("/programa-academico", summary="Vista programa: profesores, materias y estudiantes matriculados")
def programa_academico(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.jefe_programa, RolEnum.decano)),
):
    """Retorna profesores activos con sus materias. jefe_programa solo ve su propio programa."""
    q = db.query(User).filter(User.rol == RolEnum.profesor, User.is_active == True)
    # jefe_programa: filtrar solo profesores con asignaturas del propio programa
    if current_user.rol == RolEnum.jefe_programa and current_user.programa:
        prof_ids_subq = (
            db.query(Asignatura.profesor_id)
            .filter(Asignatura.programa == current_user.programa, Asignatura.is_active == True,
                    Asignatura.profesor_id.isnot(None))
            .distinct()
            .subquery()
        )
        q = q.filter(User.id.in_(prof_ids_subq))
    profesores = q.order_by(User.apellidos).all()
    result = []
    for prof in profesores:
        mat_q = (
            db.query(Asignatura)
            .options(joinedload(Asignatura.matriculas))
            .filter(Asignatura.profesor_id == prof.id, Asignatura.is_active == True)
        )
        if current_user.rol == RolEnum.jefe_programa and current_user.programa:
            mat_q = mat_q.filter(Asignatura.programa == current_user.programa)
        materias = mat_q.order_by(Asignatura.semestre).all()
        total_estudiantes = sum(len(m.matriculas) for m in materias)
        result.append({
            "profesor_id": prof.id,
            "codigo": prof.codigo,
            "nombre": f"{prof.nombres} {prof.apellidos}",
            "email": prof.email,
            "total_materias": len(materias),
            "total_estudiantes": total_estudiantes,
            "materias": [
                {
                    "id": a.id,
                    "codigo": a.codigo,
                    "nombre": a.nombre,
                    "semestre": a.semestre,
                    "creditos": a.creditos,
                    "total_estudiantes": len(a.matriculas),
                }
                for a in materias
            ],
        })
    return result


@router.get("/{conv_id}", response_model=ConvocatoriaOut)
def obtener_convocatoria(
    conv_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    conv = (
        db.query(Convocatoria)
        .options(joinedload(Convocatoria.asignatura), joinedload(Convocatoria.profesor))
        .filter(Convocatoria.id == conv_id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")
    return _enrich(conv, db)


@router.post("/", response_model=ConvocatoriaOut, status_code=201)
def crear_convocatoria(
    body: ConvocatoriaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(RolEnum.jefe_programa, RolEnum.decano, RolEnum.profesor)
    ),
):
    asig = db.query(Asignatura).filter(Asignatura.id == body.asignatura_id).first()
    if not asig:
        raise HTTPException(status_code=404, detail="Asignatura no encontrada")

    # RF-MON-TIME-02: validar ventana de postulación al crear la convocatoria
    hoy = datetime.now(timezone.utc)
    ini = body.fecha_inicio_postulacion
    fin = body.fecha_fin_postulacion
    if fin <= ini:
        raise HTTPException(status_code=400, detail="La fecha de cierre debe ser posterior a la fecha de apertura de postulación.")
    delta_dias = (fin.date() - ini.date()).days
    if delta_dias < DIAS_MINIMOS_POSTULACION and not es_modo_prueba(db):
        raise HTTPException(
            status_code=400,
            detail=f"La ventana de postulación debe ser de al menos {DIAS_MINIMOS_POSTULACION} días (Acuerdo 012/2023 Art.6). Diferencia actual: {delta_dias} día(s).",
        )
    if delta_dias > DIAS_MAXIMOS_POSTULACION:
        raise HTTPException(
            status_code=400,
            detail=f"La ventana de postulación no puede superar {DIAS_MAXIMOS_POSTULACION} días. Diferencia actual: {delta_dias} día(s).",
        )
    if ini.date() < hoy.date():
        raise HTTPException(
            status_code=400,
            detail="La fecha de inicio de postulación no puede ser en el pasado.",
        )
    if body.fecha_publicacion_resultados and body.fecha_publicacion_resultados <= fin:
        raise HTTPException(
            status_code=400,
            detail="La fecha de publicación de resultados debe ser posterior al cierre de postulaciones (Art.8).",
        )

    if current_user.rol in (RolEnum.jefe_programa, RolEnum.decano):
        if not body.profesor_id:
            raise HTTPException(status_code=400, detail="Debe seleccionar un profesor")
        prof = db.query(User).filter(User.id == body.profesor_id, User.rol == RolEnum.profesor).first()
        if not prof:
            raise HTTPException(status_code=404, detail="Profesor no encontrado")
        profesor_id = body.profesor_id
    else:
        profesor_id = current_user.id
        if asig.profesor_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Solo puede crear convocatorias para asignaturas que usted dicta.",
            )

    # RF-MON-DUP: verificar si ya existe una convocatoria activa para esta asignatura y período
    existente = (
        db.query(Convocatoria)
        .filter(
            Convocatoria.asignatura_id == body.asignatura_id,
            Convocatoria.periodo_academico == body.periodo_academico,
            Convocatoria.estado != EstadoConvocatoriaEnum.finalizada,
        )
        .first()
    )
    if existente:
        estados_es = {
            "borrador": "en borrador",
            "abierta": "abierta",
            "cerrada": "cerrada",
            "en_evaluacion": "en evaluación",
        }
        estado_texto = estados_es.get(existente.estado, existente.estado)
        raise HTTPException(
            status_code=409,
            detail=(
                f"Ya existe una convocatoria {estado_texto} para «{asig.nombre}» "
                f"en el período {body.periodo_academico} (ID #{existente.id}). "
                f"Solo puede haber una convocatoria activa por asignatura por período académico (Acuerdo 012/2023)."
            ),
        )

    data = body.model_dump(exclude={"profesor_id"})
    conv = Convocatoria(
        **data,
        profesor_id=profesor_id,
        estado=EstadoConvocatoriaEnum.borrador,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)

    conv = (
        db.query(Convocatoria)
        .options(joinedload(Convocatoria.asignatura), joinedload(Convocatoria.profesor))
        .filter(Convocatoria.id == conv.id)
        .first()
    )
    return _enrich(conv, db)


@router.put("/{conv_id}", response_model=ConvocatoriaOut)
def actualizar_convocatoria(
    conv_id: int,
    body: ConvocatoriaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(RolEnum.jefe_programa, RolEnum.decano, RolEnum.profesor)
    ),
):
    conv = db.query(Convocatoria).filter(Convocatoria.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")

    if current_user.rol == RolEnum.profesor and conv.profesor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Solo puede editar sus propias convocatorias")

    if conv.estado not in [EstadoConvocatoriaEnum.borrador, EstadoConvocatoriaEnum.abierta]:
        raise HTTPException(status_code=400, detail="Solo se pueden editar convocatorias en borrador o abiertas")

    updates = body.model_dump(exclude_unset=True)
    if current_user.rol == RolEnum.profesor and "asignatura_id" in updates:
        nueva_asig = db.query(Asignatura).filter(Asignatura.id == updates["asignatura_id"]).first()
        if not nueva_asig or nueva_asig.profesor_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Solo puede asignar asignaturas que usted dicta.",
            )
    for field, value in updates.items():
        setattr(conv, field, value)

    db.commit()
    db.refresh(conv)
    conv = (
        db.query(Convocatoria)
        .options(joinedload(Convocatoria.asignatura), joinedload(Convocatoria.profesor))
        .filter(Convocatoria.id == conv_id)
        .first()
    )
    return _enrich(conv, db)


@router.patch("/{conv_id}/estado", response_model=ConvocatoriaOut)
def cambiar_estado(
    conv_id: int,
    body: CambiarEstadoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(RolEnum.jefe_programa, RolEnum.decano)
    ),
):
    conv = db.query(Convocatoria).filter(Convocatoria.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")

    permitidos = TRANSICIONES_VALIDAS.get(conv.estado, [])
    if body.estado not in permitidos:
        raise HTTPException(
            status_code=400,
            detail=f"Transición inválida: {conv.estado} → {body.estado}. Permitidas: {[e.value for e in permitidos]}",
        )

    nuevo_estado = body.estado

    # RF-MON-TIME-03: al abrir la convocatoria, verificar que estamos dentro del
    # período habilitado según ConfiguracionCalendario (semanas permitidas)
    if nuevo_estado == EstadoConvocatoriaEnum.abierta:
        cal = (
            db.query(ConfiguracionCalendario)
            .filter(
                ConfiguracionCalendario.periodo_academico == conv.periodo_academico,
                ConfiguracionCalendario.is_active == True,
            )
            .first()
        )
        if cal:
            hoy_ts = datetime.now(timezone.utc)
            delta = (hoy_ts.date() - cal.fecha_inicio_semestre.date()).days
            semana_actual = max(1, (delta // 7) + 1)
            if not (cal.semana_inicio_solicitudes <= semana_actual <= cal.semana_fin_solicitudes):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Fuera del período habilitado para '{conv.periodo_academico}'. "
                        f"Semanas permitidas: {cal.semana_inicio_solicitudes}–{cal.semana_fin_solicitudes}. "
                        f"Semana actual: {semana_actual}. Contacte al administrador si necesita ampliar el rango."
                    ),
                )
        # Verificar que la fecha de inicio de postulación no sea pasada al abrir
        hoy = datetime.now(timezone.utc)
        if conv.fecha_inicio_postulacion and conv.fecha_inicio_postulacion.date() < hoy.date():
            raise HTTPException(
                status_code=400,
                detail=(
                    f"No se puede abrir: la fecha de inicio de postulación "
                    f"({conv.fecha_inicio_postulacion.strftime('%d/%m/%Y')}) ya pasó. "
                    "Actualice las fechas antes de publicar."
                ),
            )

    estado_anterior = conv.estado
    conv.estado = nuevo_estado
    registrar_historial(db, "convocatoria", conv_id, estado_anterior, nuevo_estado, current_user.id)

    # Notificaciones según el nuevo estado
    postulaciones = db.query(Postulacion).filter(Postulacion.convocatoria_id == conv_id).all()
    conv_nombre = conv.titulo
    asig = conv.asignatura.nombre if conv.asignatura else f"#{conv.asignatura_id}"

    if nuevo_estado == EstadoConvocatoriaEnum.abierta:
        # Notificar a todos los estudiantes activos
        estudiantes = db.query(User).filter(
            User.rol == RolEnum.estudiante, User.is_active == True
        ).all()
        for est in estudiantes:
            crear_notificacion(
                db, est.id,
                tipo="convocatoria_abierta",
                titulo=f"Nueva convocatoria abierta 📌",
                mensaje=f"La convocatoria '{conv_nombre}' ({asig}) está abierta para postulaciones.",
                url="/convocatorias",
            )
    elif nuevo_estado == EstadoConvocatoriaEnum.en_evaluacion:
        # Notificar a los postulantes
        for p in postulaciones:
            crear_notificacion(
                db, p.estudiante_id,
                tipo="convocatoria_evaluacion",
                titulo=f"Convocatoria '{conv_nombre}' en evaluación",
                mensaje=f"Tu postulación está siendo evaluada. Pronto conocerás los resultados.",
                url="/postulaciones",
            )
    elif nuevo_estado == EstadoConvocatoriaEnum.finalizada:
        # Notificar a todos los postulantes con su resultado
        for p in postulaciones:
            from app.models.postulacion import EstadoPostulacionEnum
            if p.estado == EstadoPostulacionEnum.seleccionado:
                msg = f"Felicidades, has sido seleccionado como monitor en '{conv_nombre}'."
            else:
                msg = f"El proceso de '{conv_nombre}' ha finalizado. Gracias por participar."
            crear_notificacion(
                db, p.estudiante_id,
                tipo="convocatoria_finalizada",
                titulo=f"Convocatoria '{conv_nombre}' finalizada",
                mensaje=msg,
                url="/postulaciones",
            )

    db.commit()
    db.refresh(conv)
    conv = (
        db.query(Convocatoria)
        .options(joinedload(Convocatoria.asignatura), joinedload(Convocatoria.profesor))
        .filter(Convocatoria.id == conv_id)
        .first()
    )
    return _enrich(conv, db)


@router.get("/{conv_id}/historial", summary="Historial de cambios de estado (SF-06)")
def historial_convocatoria(
    conv_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    from app.models.historial_estado import HistorialEstado
    registros = (
        db.query(HistorialEstado)
        .filter(HistorialEstado.entidad == "convocatoria", HistorialEstado.entidad_id == conv_id)
        .order_by(HistorialEstado.created_at.asc())
        .all()
    )
    return [
        {
            "id": r.id,
            "estado_anterior": r.estado_anterior,
            "estado_nuevo": r.estado_nuevo,
            "observaciones": r.observaciones,
            "usuario_id": r.usuario_id,
            "usuario": f"{r.usuario.nombres} {r.usuario.apellidos}" if r.usuario else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in registros
    ]


