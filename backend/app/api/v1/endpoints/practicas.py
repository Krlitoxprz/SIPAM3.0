"""
Módulo de Prácticas Extramuros — RF-PRA-01 a RF-PRA-07
"""
import math
from datetime import datetime, timedelta, timezone, date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.db.database import get_db
from app.models.user import User, RolEnum
from app.models.convocatoria import Convocatoria, AsignaturaEstudiante, Asignatura
from app.models.practica import (
    Practica, RutaPractica, FirmaConsentimiento, TarifaViatico, Viatico,
    EstadoPracticaEnum, PracticaPlantilla,
)
from app.models.presupuesto import ConfiguracionCalendario, Presupuesto, MovimientoPresupuestal, TipoMovimientoEnum
from app.models.pago_viatico import PagoViatico
from app.schemas.practica import (
    PracticaCreate, PracticaUpdate, PracticaOut,
    FirmaConsentimientoOut, TarifaViaticoOut, ViaticosCalculadoOut,
)
from app.api.deps import get_current_user, require_roles
from app.utils.notificaciones import crear_notificacion
from app.models.historial_estado import HistorialEstado
from app.utils.historial import registrar_historial
from app.db.database import es_modo_prueba

router = APIRouter()

# ── Reglas de tiempo RF-PRA ────────────────────────────────────────────────────
DIAS_ANTELACION_MINIMA = 30        # mín. días entre hoy y fecha_inicio al crear/solicitar
DIAS_APERTURA_CONSENTIMIENTO = 10  # ventana se abre N días antes de fecha_inicio
DIAS_CIERRE_CONSENTIMIENTO = 5     # ventana se cierra N días antes de fecha_inicio
MAX_DIAS_PRACTICA_DENTRO_HUILA = 3    # duración máxima para práctica dentro del departamento del Huila
MAX_DIAS_PRACTICA_FUERA_HUILA = 4   # duración máxima para práctica fuera del departamento del Huila
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/plantillas")
def listar_plantillas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    programa: Optional[str] = Query(None),
):
    """Lista plantillas de prácticas extramuros del catálogo institucional."""
    q = db.query(PracticaPlantilla)
    # Para profesores, filtrar por su programa (determinado por sus asignaturas o su campo programa)
    if current_user.rol == RolEnum.profesor:
        from sqlalchemy import func as sa_func
        # Obtener asignaturas asignadas al profesor
        asig_rows = (
            db.query(Asignatura.nombre, Asignatura.programa)
            .filter(Asignatura.profesor_id == current_user.id, Asignatura.is_active == True)
            .all()
        )
        if asig_rows:
            # Filtrar plantillas cuya asignatura coincida (case-insensitive) con las del profesor
            nombres_lower = [r.nombre.lower() for r in asig_rows]
            q = q.filter(sa_func.lower(PracticaPlantilla.asignatura).in_(nombres_lower))
        else:
            # Fallback: filtrar por programa del usuario o parámetro
            prog = programa or current_user.programa
            if prog:
                q = q.filter(PracticaPlantilla.programa == prog)
    elif programa:
        q = q.filter(PracticaPlantilla.programa == programa)
    def _f(v):
        return float(v) if v is not None else None

    return [
        {
            "id": p.id,
            "nombre": p.nombre,
            "programa": p.programa,
            "sede": p.sede,
            "asignatura": p.asignatura,
            "caracter_curso": p.caracter_curso,
            "ruta_texto": p.ruta_texto,
            "tipo_bus": p.tipo_bus,
            "costo_bus_externo": _f(p.costo_bus_externo),
            "costo_tiquetes": _f(p.costo_tiquetes),
            "viat_docente_dias": _f(p.viat_docente_dias),
            "viat_docente_valor_dia": _f(p.viat_docente_valor_dia),
            "profesor": p.profesor,
        }
        for p in q.order_by(PracticaPlantilla.programa, PracticaPlantilla.nombre).all()
    ]


@router.get("/tarifas/vigentes", response_model=list[TarifaViaticoOut])
def listar_tarifas(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return db.query(TarifaViatico).filter(TarifaViatico.is_active == True).all()


@router.get("/limites-duracion")
def get_limites_duracion(_: User = Depends(get_current_user)):
    """Retorna la duración máxima en días para prácticas dentro y fuera del departamento del Huila."""
    return {
        "dentro_huila": MAX_DIAS_PRACTICA_DENTRO_HUILA,
        "fuera_huila": MAX_DIAS_PRACTICA_FUERA_HUILA,
    }


def _semana_actual(fecha_inicio: datetime) -> int:
    hoy = datetime.now(timezone.utc).date()
    delta = (hoy - fecha_inicio.date()).days
    return max(1, (delta // 7) + 1)


def _semana_de_fecha(fecha_inicio: datetime, fecha_ref: datetime) -> int:
    """Semana del semestre en que cae fecha_ref, contada desde fecha_inicio."""
    delta = (fecha_ref.date() - fecha_inicio.date()).days
    return max(1, (delta // 7) + 1)


def _es_fuera_del_huila(rutas) -> bool:
    """True si alguna ruta tiene departamento distinto de Huila."""
    for r in rutas:
        dept = getattr(r, 'departamento', None) or ''
        if dept.strip().lower() not in ('', 'huila'):
            return True
    return False


def _enrich(p: Practica, testing_mode: bool = False) -> PracticaOut:
    out = PracticaOut.model_validate(p)
    if p.num_alumnos and p.num_alumnos > 0:
        out.porcentaje_quorum = min(100.0, round(
            (p.total_firmas_obtenidas / p.num_alumnos) * 100, 1
        ))
    else:
        out.porcentaje_quorum = 0.0
    # Ventana de consentimiento
    hoy = datetime.now(timezone.utc)
    if p.fecha_inicio:
        fi = p.fecha_inicio if p.fecha_inicio.tzinfo else p.fecha_inicio.replace(tzinfo=timezone.utc)
        ff = (p.fecha_fin.replace(tzinfo=timezone.utc)
              if p.fecha_fin and not p.fecha_fin.tzinfo else p.fecha_fin)
        ventana_inicio = fi - timedelta(days=DIAS_APERTURA_CONSENTIMIENTO)
        ventana_fin = fi - timedelta(days=DIAS_CIERRE_CONSENTIMIENTO)
        out.ventana_firma_inicio = ventana_inicio
        out.ventana_firma_fin = ventana_fin
        practica_vigente = ff is None or ff >= hoy
        estado_firma_ok = p.estado in [
            EstadoPracticaEnum.solicitada,
            EstadoPracticaEnum.pendiente_quorum,
            EstadoPracticaEnum.aprobada_curriculo,
            EstadoPracticaEnum.aprobada_facultad,
            EstadoPracticaEnum.aprobado_transporte,
        ]
        out.puede_firmar_ahora = testing_mode or bool(
            practica_vigente and estado_firma_ok and ventana_inicio <= hoy <= ventana_fin
        )
    return out


@router.get("/", response_model=list[PracticaOut])
def listar_practicas(
    estado: Optional[str] = Query(None),
    periodo: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Practica).options(
        joinedload(Practica.asignatura),
        joinedload(Practica.profesor),
        joinedload(Practica.rutas),
    )
    if estado:
        q = q.filter(Practica.estado == estado)
    if periodo:
        q = q.filter(Practica.periodo_academico == periodo)

    if current_user.rol == RolEnum.profesor:
        q = q.filter(Practica.profesor_id == current_user.id)
    elif current_user.rol == RolEnum.jefe_programa and current_user.programa:
        q = q.filter(Practica.asignatura.has(Asignatura.programa == current_user.programa))
    elif current_user.rol == RolEnum.estudiante:
        enrolled_ids = (
            db.query(AsignaturaEstudiante.asignatura_id)
            .filter(AsignaturaEstudiante.estudiante_id == current_user.id)
            .subquery()
        )
        q = q.filter(Practica.asignatura_id.in_(enrolled_ids))
        q = q.filter(Practica.estado.in_([
            EstadoPracticaEnum.solicitada,
            EstadoPracticaEnum.pendiente_quorum,
            EstadoPracticaEnum.aprobada_curriculo,
            EstadoPracticaEnum.aprobada_facultad,
            EstadoPracticaEnum.aprobado_transporte,
            EstadoPracticaEnum.en_ejecucion,
            EstadoPracticaEnum.finalizada,
        ]))
        # Ocultar prácticas cuya fecha de fin ya pasó salvo las marcadas finalizada
        hoy_date = datetime.now(timezone.utc)
        q = q.filter(
            or_(
                Practica.fecha_fin >= hoy_date,
                Practica.estado == EstadoPracticaEnum.finalizada,
            )
        )

    practicas = q.order_by(Practica.created_at.desc()).all()
    modo_prueba = es_modo_prueba(db)
    practica_ids = [p.id for p in practicas]

    # Batch: prácticas que ya tienen pago de viáticos registrado
    pagadas_ids = {
        row.practica_id
        for row in db.query(PagoViatico.practica_id)
        .filter(PagoViatico.practica_id.in_(practica_ids))
        .all()
    } if practica_ids else set()

    if current_user.rol == RolEnum.estudiante:
        firmadas = {
            f.practica_id
            for f in db.query(FirmaConsentimiento.practica_id).filter(
                FirmaConsentimiento.practica_id.in_(practica_ids),
                FirmaConsentimiento.estudiante_id == current_user.id,
            ).all()
        }
        result = []
        for p in practicas:
            out = _enrich(p, testing_mode=modo_prueba)
            out.ya_firme = p.id in firmadas
            out.pago_registrado = p.id in pagadas_ids
            result.append(out)
        return result

    result = []
    for p in practicas:
        out = _enrich(p, testing_mode=modo_prueba)
        out.pago_registrado = p.id in pagadas_ids
        result.append(out)
    return result


@router.get("/autocompletar", summary="Autocompletar ruta y FO-16 desde práctica previa de la misma asignatura")
def autocompletar_practica_get(
    asignatura_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.profesor)),
):
    """
    Devuelve la práctica más reciente del profesor para la asignatura indicada.
    Permite auto-rellenar rutas y campos FO-16 en el formulario de nueva práctica.
    """
    practica = (
        db.query(Practica)
        .options(joinedload(Practica.rutas))
        .filter(
            Practica.asignatura_id == asignatura_id,
            Practica.profesor_id == current_user.id,
        )
        .order_by(Practica.created_at.desc())
        .first()
    )
    if not practica:
        return {"found": False}

    rutas = sorted(practica.rutas, key=lambda r: r.orden)
    return {
        "found": True,
        "practica_id": practica.id,
        "nombre_practica": practica.nombre_practica,
        "caracter_curso": practica.caracter_curso,
        "caracteristica_curso": practica.caracteristica_curso,
        "modalidad_docente": practica.modalidad_docente,
        "articulacion_curso": practica.articulacion_curso,
        "descripcion_practica": practica.descripcion_practica,
        "justificacion": practica.justificacion,
        "metodologia": practica.metodologia,
        "evaluacion": practica.evaluacion,
        "carta_autorizacion_empresa": practica.carta_autorizacion_empresa,
        "placa_vehiculo": getattr(practica, "placa_vehiculo", None),
        "tipo_vehiculo": getattr(practica, "tipo_vehiculo", None),
        "empresa_transporte": getattr(practica, "empresa_transporte", None),
        "conductor_nombre": getattr(practica, "conductor_nombre", None),
        "rutas": [
            {
                "orden": r.orden,
                "tipo_punto": r.tipo_punto,
                "lugar": r.lugar,
                "municipio": r.municipio or "",
                "departamento": r.departamento or "Huila",
                "distancia_km": str(r.distancia_km) if r.distancia_km is not None else "",
                "vereda": r.vereda or "",
                "es_rural": r.es_rural,
            }
            for r in rutas
        ],
    }


@router.get("/datos-asignatura", summary="Datos de asignatura+profesor para auto-llenado del formulario de práctica")
def datos_asignatura(
    asignatura_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.profesor, RolEnum.jefe_programa, RolEnum.decano, RolEnum.admin)),
):
    """
    Retorna datos de la asignatura y su profesor para pre-llenar el formulario:
    sede, facultad, programa, tipo_docente, modalidad_docente, caracter_curso,
    caracteristica_curso, num_estudiantes, y datos de la práctica previa si existe.
    """
    from sqlalchemy import func as sa_func

    asig = (
        db.query(Asignatura)
        .options(joinedload(Asignatura.profesor))
        .filter(Asignatura.id == asignatura_id)
        .first()
    )
    if not asig:
        raise HTTPException(status_code=404, detail="Asignatura no encontrada")

    num_estudiantes = db.query(sa_func.count(AsignaturaEstudiante.id)).filter(
        AsignaturaEstudiante.asignatura_id == asignatura_id
    ).scalar() or 0

    profesor = asig.profesor
    sede = getattr(profesor, "sede", None) if profesor else None
    tipo_doc = getattr(profesor, "tipo_docente", None) if profesor else None
    mod_doc = getattr(profesor, "modalidad_docente", None) if profesor else None
    tipo_docente = tipo_doc.value if hasattr(tipo_doc, "value") else (str(tipo_doc) if tipo_doc else None)
    modalidad_docente = mod_doc.value if hasattr(mod_doc, "value") else (str(mod_doc) if mod_doc else None)

    result: dict = {
        "asignatura_id": asig.id,
        "nombre_asignatura": asig.nombre,
        "facultad": asig.facultad,
        "programa": asig.programa,
        "creditos": asig.creditos,
        "semestre": asig.semestre,
        "caracter_curso": asig.caracter_curso,
        "caracteristica_curso": asig.caracteristica_curso,
        "num_estudiantes": num_estudiantes,
        "sede": sede,
        "tipo_docente": tipo_docente,
        "modalidad_docente": modalidad_docente,
        "found_practica": False,
    }

    practica_q = (
        db.query(Practica)
        .options(joinedload(Practica.rutas))
        .filter(Practica.asignatura_id == asignatura_id)
    )
    if current_user.rol == RolEnum.profesor:
        practica_q = practica_q.filter(Practica.profesor_id == current_user.id)
    practica = practica_q.order_by(Practica.created_at.desc()).first()

    if practica:
        rutas = sorted(practica.rutas, key=lambda r: r.orden)
        result.update({
            "found_practica": True,
            "articulacion_curso": practica.articulacion_curso,
            "descripcion_practica": practica.descripcion_practica,
            "justificacion": practica.justificacion,
            "metodologia": practica.metodologia,
            "evaluacion": practica.evaluacion,
            "carta_autorizacion_empresa": practica.carta_autorizacion_empresa,
            "placa_vehiculo": practica.placa_vehiculo,
            "tipo_vehiculo": practica.tipo_vehiculo,
            "empresa_transporte": practica.empresa_transporte,
            "conductor_nombre": practica.conductor_nombre,
            "rutas": [
                {
                    "orden": r.orden,
                    "tipo_punto": r.tipo_punto,
                    "lugar": r.lugar,
                    "municipio": r.municipio or "",
                    "departamento": r.departamento or "Huila",
                    "distancia_km": str(r.distancia_km) if r.distancia_km is not None else "",
                    "vereda": r.vereda or "",
                    "es_rural": r.es_rural,
                }
                for r in rutas
            ],
        })

    return result


@router.get("/{practica_id}", response_model=PracticaOut)
def obtener_practica(
    practica_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    p = (
        db.query(Practica)
        .options(
            joinedload(Practica.asignatura),
            joinedload(Practica.profesor),
            joinedload(Practica.rutas),
        )
        .filter(Practica.id == practica_id)
        .first()
    )
    if not p:
        raise HTTPException(status_code=404, detail="Práctica no encontrada")
    return _enrich(p, testing_mode=es_modo_prueba(db))


@router.post("/", response_model=PracticaOut, status_code=201)
def crear_practica(
    body: PracticaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.profesor)),
):
    """RF-PRA-01 — Solo permite solicitudes en semanas 3 a 14 del semestre."""
    cal = (
        db.query(ConfiguracionCalendario)
        .filter(
            ConfiguracionCalendario.periodo_academico == body.periodo_academico,
            ConfiguracionCalendario.is_active == True,
        )
        .first()
    )
    if cal and not es_modo_prueba(db):
        semana = _semana_actual(cal.fecha_inicio_semestre)
        # semana_fin_efectiva: el máximo entre el límite configurado y la semana
        # que corresponde a fecha_fin_semestre — así los cambios del admin en
        # la fecha de fin del semestre se reflejan inmediatamente.
        if cal.fecha_fin_semestre:
            semana_fin_efectiva = max(
                cal.semana_fin_solicitudes,
                _semana_de_fecha(cal.fecha_inicio_semestre, cal.fecha_fin_semestre),
            )
        else:
            semana_fin_efectiva = cal.semana_fin_solicitudes
        if not (cal.semana_inicio_solicitudes <= semana <= semana_fin_efectiva):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Fuera del período habilitado para '{body.periodo_academico}'. "
                    f"Solo semanas {cal.semana_inicio_solicitudes}–{semana_fin_efectiva}. "
                    f"Semana actual: {semana}. Contacte al administrador para ampliar "
                    f"la semana fin o la fecha fin del semestre."
                ),
            )

    asig = db.query(Asignatura).filter(Asignatura.id == body.asignatura_id).first()
    if not asig:
        raise HTTPException(status_code=404, detail="Asignatura no encontrada")

    # RF-PRA-UNI-01: una sola práctica activa por asignatura + período + docente
    duplicada = (
        db.query(Practica)
        .filter(
            Practica.asignatura_id == body.asignatura_id,
            Practica.periodo_academico == body.periodo_academico,
            Practica.profesor_id == current_user.id,
            Practica.estado != EstadoPracticaEnum.rechazada,
        )
        .first()
    )
    if duplicada:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Ya existe una práctica activa para esta asignatura en el período "
                f"'{body.periodo_academico}' (ID: {duplicada.id}, estado: {duplicada.estado.value}). "
                f"Solo se permite una práctica por asignatura por período académico."
            ),
        )

    # RF-PRA-TIME-01: la práctica debe programarse con al menos 30 días de anticipación
    hoy = datetime.now(timezone.utc)
    min_fecha_inicio = hoy + timedelta(days=DIAS_ANTELACION_MINIMA)
    # Normalizar fechas naive (frontend datetime-local no incluye zona horaria) a UTC
    fi = body.fecha_inicio if body.fecha_inicio.tzinfo else body.fecha_inicio.replace(tzinfo=timezone.utc)
    ff = body.fecha_fin if body.fecha_fin.tzinfo else body.fecha_fin.replace(tzinfo=timezone.utc)
    if fi < min_fecha_inicio and not es_modo_prueba(db):
        raise HTTPException(
            status_code=400,
            detail=(
                f"La práctica debe programarse con al menos {DIAS_ANTELACION_MINIMA} días de anticipación. "
                f"Fecha mínima de inicio permitida: {min_fecha_inicio.strftime('%d/%m/%Y')}."
            ),
        )

    duracion = max(1, (ff.date() - fi.date()).days + 1)
    dias_viaje = (ff.date() - fi.date()).days   # días de desplazamiento (sin +1) para límite
    fuera_huila = _es_fuera_del_huila(body.rutas)
    max_dias = MAX_DIAS_PRACTICA_FUERA_HUILA if fuera_huila else MAX_DIAS_PRACTICA_DENTRO_HUILA
    if dias_viaje > max_dias and not es_modo_prueba(db):
        tipo = "fuera del departamento del Huila" if fuera_huila else "dentro del departamento del Huila"
        raise HTTPException(
            status_code=400,
            detail=(
                f"La duración de la práctica ({dias_viaje} días) excede el máximo permitido "
                f"para prácticas {tipo}: {max_dias} días."
            ),
        )
    firmas_req = max(1, math.ceil(body.num_alumnos * 0.66))

    practica = Practica(
        nombre_practica=body.nombre_practica,
        asignatura_id=body.asignatura_id,
        profesor_id=current_user.id,
        estado=EstadoPracticaEnum.borrador,
        periodo_academico=body.periodo_academico,
        fecha_inicio=fi,
        fecha_fin=ff,
        duracion_dias=duracion,
        num_alumnos=body.num_alumnos,
        total_firmas_requeridas=firmas_req,
        total_firmas_obtenidas=0,
        tipo_docente=body.tipo_docente,
        observaciones=body.observaciones,
        caracter_curso=body.caracter_curso,
        caracteristica_curso=body.caracteristica_curso,
        modalidad_docente=body.modalidad_docente,
        hora_salida=body.hora_salida,
        hora_llegada=body.hora_llegada,
        articulacion_curso=body.articulacion_curso,
        descripcion_practica=body.descripcion_practica,
        evaluacion=body.evaluacion,
        justificacion=body.justificacion,
        metodologia=body.metodologia,
        carta_autorizacion_empresa=body.carta_autorizacion_empresa,
        conductor_nombre=body.conductor_nombre,
        sede=body.sede,
    )
    db.add(practica)
    db.flush()

    for ruta in body.rutas:
        db.add(RutaPractica(practica_id=practica.id, **ruta.model_dump()))

    db.commit()
    db.refresh(practica)

    practica = (
        db.query(Practica)
        .options(
            joinedload(Practica.asignatura),
            joinedload(Practica.profesor),
            joinedload(Practica.rutas),
        )
        .filter(Practica.id == practica.id)
        .first()
    )
    return _enrich(practica, testing_mode=es_modo_prueba(db))


@router.put("/{practica_id}", response_model=PracticaOut)
def actualizar_practica(
    practica_id: int,
    body: PracticaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.profesor, RolEnum.jefe_programa, RolEnum.decano)),
):
    p = db.query(Practica).filter(Practica.id == practica_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Práctica no encontrada")

    ESTADOS_NO_EDITABLES = [EstadoPracticaEnum.finalizada, EstadoPracticaEnum.rechazada]
    if current_user.rol == RolEnum.profesor:
        if p.profesor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Solo puede editar sus propias prácticas")
        if p.estado not in [EstadoPracticaEnum.borrador, EstadoPracticaEnum.solicitada]:
            raise HTTPException(status_code=400, detail="Solo se pueden editar prácticas en borrador o solicitadas")
    elif current_user.rol in (RolEnum.jefe_programa, RolEnum.decano):
        if p.estado in ESTADOS_NO_EDITABLES:
            raise HTTPException(status_code=400, detail="No se pueden editar prácticas finalizadas o rechazadas")

    # Revalidar antelación mínima si se cambia la fecha de inicio (solo para profesores)
    if body.fecha_inicio is not None and current_user.rol == RolEnum.profesor and not es_modo_prueba(db):
        hoy = datetime.now(timezone.utc)
        min_fecha_inicio = hoy + timedelta(days=DIAS_ANTELACION_MINIMA)
        fi_up = body.fecha_inicio if body.fecha_inicio.tzinfo else body.fecha_inicio.replace(tzinfo=timezone.utc)
        if fi_up < min_fecha_inicio:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"La práctica debe programarse con al menos {DIAS_ANTELACION_MINIMA} días de anticipación. "
                    f"Fecha mínima de inicio permitida: {min_fecha_inicio.strftime('%d/%m/%Y')}."
                ),
            )

    for field, value in body.model_dump(exclude_unset=True, exclude={"rutas"}).items():
        setattr(p, field, value)

    if p.fecha_inicio and p.fecha_fin:
        p.duracion_dias = max(1, (p.fecha_fin.date() - p.fecha_inicio.date()).days + 1)
        if not es_modo_prueba(db):
            dias_viaje_check = (p.fecha_fin.date() - p.fecha_inicio.date()).days
            rutas_check = body.rutas if body.rutas is not None else p.rutas
            fuera_check = _es_fuera_del_huila(rutas_check)
            max_dias_check = MAX_DIAS_PRACTICA_FUERA_HUILA if fuera_check else MAX_DIAS_PRACTICA_DENTRO_HUILA
            if dias_viaje_check > max_dias_check:
                tipo_check = "fuera del Huila" if fuera_check else "dentro del Huila"
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"La duración ({dias_viaje_check} días) excede el máximo permitido para "
                        f"prácticas {tipo_check}: {max_dias_check} días."
                    ),
                )

    if body.rutas is not None:
        db.query(RutaPractica).filter(RutaPractica.practica_id == practica_id).delete()
        for ruta in body.rutas:
            db.add(RutaPractica(practica_id=practica_id, **ruta.model_dump()))

    db.commit()
    db.refresh(p)
    p = (
        db.query(Practica)
        .options(joinedload(Practica.asignatura), joinedload(Practica.profesor), joinedload(Practica.rutas))
        .filter(Practica.id == practica_id)
        .first()
    )
    return _enrich(p, testing_mode=es_modo_prueba(db))


@router.patch("/{practica_id}/solicitar", response_model=PracticaOut)
def solicitar_practica(
    practica_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.profesor)),
):
    p = (
        db.query(Practica)
        .options(joinedload(Practica.asignatura), joinedload(Practica.rutas))
        .filter(Practica.id == practica_id)
        .first()
    )
    if not p or p.profesor_id != current_user.id:
        raise HTTPException(status_code=404, detail="Práctica no encontrada")
    if p.estado != EstadoPracticaEnum.borrador:
        raise HTTPException(status_code=400, detail="Solo se pueden solicitar prácticas en borrador")
    if not p.rutas:
        raise HTTPException(status_code=422, detail="Debe agregar al menos una ruta antes de solicitar")

    # Verificar antelación mínima al momento de solicitar (segunda barrera)
    hoy = datetime.now(timezone.utc)
    min_fecha_inicio = hoy + timedelta(days=DIAS_ANTELACION_MINIMA)
    fi_p = (p.fecha_inicio.replace(tzinfo=timezone.utc)
            if p.fecha_inicio and not p.fecha_inicio.tzinfo else p.fecha_inicio)
    if fi_p and fi_p < min_fecha_inicio and not es_modo_prueba(db):
        raise HTTPException(
            status_code=400,
            detail=(
                f"No se puede solicitar: la práctica debe realizarse con al menos "
                f"{DIAS_ANTELACION_MINIMA} días de anticipación desde hoy. "
                f"Fecha mínima permitida: {min_fecha_inicio.strftime('%d/%m/%Y')}."
            ),
        )

    registrar_historial(db, "practica", practica_id, EstadoPracticaEnum.borrador, EstadoPracticaEnum.solicitada, current_user.id)
    p.estado = EstadoPracticaEnum.solicitada
    # Notificar solo al jefe_programa del mismo programa (no a todos)
    asig_nombre = p.asignatura.nombre if p.asignatura else f"#{p.asignatura_id}"
    programa_asig = p.asignatura.programa if p.asignatura else None
    jefes_q = db.query(User).filter(User.rol == RolEnum.jefe_programa, User.is_active == True)
    if programa_asig:
        jefes_q = jefes_q.filter(User.programa == programa_asig)
    for j in jefes_q.all():
        crear_notificacion(
            db, j.id,
            tipo="practica_solicitada",
            titulo=f"Práctica extramural solicitada 📍",
            mensaje=f"{current_user.nombres} {current_user.apellidos} solicita aprobación de la práctica '{p.nombre_practica}' ({asig_nombre}).",
            url="/practicas",
        )
    db.commit()
    db.refresh(p)
    p = (
        db.query(Practica)
        .options(joinedload(Practica.asignatura), joinedload(Practica.profesor), joinedload(Practica.rutas))
        .filter(Practica.id == practica_id)
        .first()
    )
    return _enrich(p, testing_mode=es_modo_prueba(db))


def _notif(db, user_id: int, tipo: str, titulo: str, mensaje: str):
    crear_notificacion(db, user_id, tipo=tipo, titulo=titulo, mensaje=mensaje, url="/practicas")


def _notif_rol(db, rol: RolEnum, titulo: str, mensaje: str):
    for u in db.query(User).filter(User.rol == rol, User.is_active == True).all():
        _notif(db, u.id, "practica_estado", titulo, mensaje)


def _reload(db, practica_id: int):
    return (
        db.query(Practica)
        .options(joinedload(Practica.asignatura), joinedload(Practica.profesor), joinedload(Practica.rutas))
        .filter(Practica.id == practica_id).first()
    )


# ── Flujo escalonado Acuerdo 003/2012 ─────────────────────────────────────────
# solicitada → [jefe] → aprobada_curriculo → [decano] → aprobada_facultad
#            → [admin] → aprobado_transporte → [profesor] → en_ejecucion
#            → [jefe] → finalizada

@router.patch("/{practica_id}/aprobar", response_model=PracticaOut)
def aprobar_practica(
    practica_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(
        RolEnum.jefe_programa, RolEnum.decano, RolEnum.admin,
    )),
):
    p = db.query(Practica).options(joinedload(Practica.viaticos)).filter(Practica.id == practica_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Práctica no encontrada")

    # ── Etapa 1: jefe_programa — Comité de Currículo ────────────────────────────────────
    if current_user.rol == RolEnum.jefe_programa:
        estados_validos = [EstadoPracticaEnum.solicitada, EstadoPracticaEnum.pendiente_quorum]
        if p.estado not in estados_validos:
            raise HTTPException(
                status_code=400,
                detail="El Comité de Currículo solo puede aprobar prácticas en estado 'Solicitada' o 'Pendiente de quórum'.",
            )
        # Desde 'solicitada': verificar quórum antes de avanzar
        if p.estado == EstadoPracticaEnum.solicitada and not p.quorum_alcanzado and not es_modo_prueba(db):
            # Mover a pendiente_quorum (esperar firmas de estudiantes)
            registrar_historial(db, "practica", practica_id,
                                EstadoPracticaEnum.solicitada, EstadoPracticaEnum.pendiente_quorum,
                                current_user.id)
            p.estado = EstadoPracticaEnum.pendiente_quorum
            if p.profesor_id:
                _notif(db, p.profesor_id, "practica_estado",
                       f"Práctica '{p.nombre_practica}' pre-aprobada — pendiente de quórum",
                       f"El Comité de Currículo aprobó la solicitud pero falta quórum "
                       f"(≥66%% de firmas). Los estudiantes tienen hasta "
                       f"{p.fecha_inicio.strftime('%d/%m/%Y') if p.fecha_inicio else '—'} para firmar.")
        else:
            # Desde 'solicitada' con quórum, o desde 'pendiente_quorum' (override explícito del jefe)
            registrar_historial(db, "practica", practica_id, p.estado,
                                EstadoPracticaEnum.aprobada_curriculo, current_user.id)
            p.estado = EstadoPracticaEnum.aprobada_curriculo
            if p.profesor_id:
                aviso_quorum = " (sin quórum completo — override del Comité)" if not p.quorum_alcanzado else ""
                _notif(db, p.profesor_id, "practica_estado",
                       f"Práctica '{p.nombre_practica}' aprobada por Comité de Currículo ✅",
                       f"Siguiente paso: aval del Consejo de Facultad (Decano).{aviso_quorum}")
            _notif_rol(db, RolEnum.decano,
                       f"Práctica pendiente de aval: '{p.nombre_practica}'",
                       "El Comité de Currículo aprobó esta práctica. Requiere su aval como Consejo de Facultad.")

    # ── Etapa 2: decano — Consejo de Facultad ────────────────────────────────
    elif current_user.rol == RolEnum.decano:
        if p.estado != EstadoPracticaEnum.aprobada_curriculo:
            raise HTTPException(
                status_code=400,
                detail="El Consejo de Facultad solo puede avalar prácticas aprobadas por el Comité de Currículo.",
            )
        registrar_historial(db, "practica", practica_id, p.estado, EstadoPracticaEnum.aprobada_facultad, current_user.id)
        p.estado = EstadoPracticaEnum.aprobada_facultad
        if p.profesor_id:
            _notif(db, p.profesor_id, "practica_estado",
                   f"Práctica '{p.nombre_practica}' avalada por el Consejo de Facultad ✅",
                   "Siguiente paso: aprobación final de la Vicerrectoría Académica.")
        _notif_rol(db, RolEnum.admin,
                   f"Práctica pendiente de aprobación final: '{p.nombre_practica}'",
                   "El Consejo de Facultad avaló esta práctica. Requiere aprobación final (Vicerrectoría).")

    # ── Etapa 3: admin — Vicerrectoría / Consejo Académico ───────────────────
    elif current_user.rol == RolEnum.admin:
        if p.estado != EstadoPracticaEnum.aprobada_facultad:
            raise HTTPException(
                status_code=400,
                detail="La Vicerrectoría solo puede dar aprobación final a prácticas avaladas por el Consejo de Facultad.",
            )
        registrar_historial(db, "practica", practica_id, p.estado, EstadoPracticaEnum.aprobado_transporte, current_user.id)
        p.estado = EstadoPracticaEnum.aprobado_transporte

        total_viaticos = sum(v.valor_calculado for v in p.viaticos) if p.viaticos else 0.0
        if total_viaticos > 0:
            presupuesto = db.query(Presupuesto).filter(
                Presupuesto.periodo_academico == p.periodo_academico
            ).first()
            if presupuesto:
                presupuesto.monto_comprometido += total_viaticos
                db.add(MovimientoPresupuestal(
                    presupuesto_id=presupuesto.id,
                    tipo=TipoMovimientoEnum.comprometido,
                    monto=total_viaticos,
                    concepto=f"Compromiso viáticos: {p.nombre_practica}",
                    practica_id=p.id,
                    responsable_id=current_user.id,
                ))
        if p.profesor_id:
            _notif(db, p.profesor_id, "practica_aprobada",
                   f"Práctica '{p.nombre_practica}' APROBADA por Vicerrectoría ✅",
                   "Tu práctica tiene aprobación final. Puedes confirmar el inicio el día programado.")

    db.commit()
    db.refresh(p)
    return _enrich(_reload(db, practica_id), testing_mode=es_modo_prueba(db))


@router.post(
    "/{practica_id}/firmar-consentimiento",
    response_model=FirmaConsentimientoOut,
    summary="RF-PRA-07 — Firma de consentimiento (captura IP + timestamp)",
)
def firmar_consentimiento(
    practica_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.estudiante)),
):
    p = db.query(Practica).filter(Practica.id == practica_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Práctica no encontrada")
    ESTADOS_FIRMA = [
        EstadoPracticaEnum.solicitada,
        EstadoPracticaEnum.pendiente_quorum,
        EstadoPracticaEnum.aprobada_curriculo,
        EstadoPracticaEnum.aprobada_facultad,
        EstadoPracticaEnum.aprobado_transporte,
    ]
    if p.estado not in ESTADOS_FIRMA:
        raise HTTPException(
            status_code=400,
            detail="No es posible firmar: la práctica ya inició, fue finalizada o fue rechazada.",
        )

    # RF-PRA-TIME-02: no permitir firmar si la práctica ya finalizó
    hoy = datetime.now(timezone.utc)
    if p.fecha_fin and p.fecha_fin.date() < hoy.date():
        raise HTTPException(
            status_code=400,
            detail="No es posible firmar el consentimiento: la práctica ya fue realizada.",
        )

    # RF-PRA-TIME-03: ventana de consentimiento (D-10 a D-5 antes de fecha_inicio)
    ventana_inicio = p.fecha_inicio - timedelta(days=DIAS_APERTURA_CONSENTIMIENTO)
    ventana_fin = p.fecha_inicio - timedelta(days=DIAS_CIERRE_CONSENTIMIENTO)
    if not (ventana_inicio <= hoy <= ventana_fin) and not es_modo_prueba(db):
        if hoy < ventana_inicio:
            msg = (
                f"La firma de consentimiento estará disponible a partir del "
                f"{ventana_inicio.strftime('%d/%m/%Y')} hasta el {ventana_fin.strftime('%d/%m/%Y')}."
            )
        else:
            msg = (
                f"La ventana de firma del consentimiento cerró el "
                f"{ventana_fin.strftime('%d/%m/%Y')}. Ya no es posible firmar."
            )
        raise HTTPException(status_code=400, detail=msg)

    matriculado = db.query(AsignaturaEstudiante).filter(
        AsignaturaEstudiante.asignatura_id == p.asignatura_id,
        AsignaturaEstudiante.estudiante_id == current_user.id,
    ).first()
    if not matriculado:
        raise HTTPException(
            status_code=403,
            detail="No estás matriculado en la asignatura de esta práctica. Contacta a tu profesor.",
        )

    ya_firmo = db.query(FirmaConsentimiento).filter(
        FirmaConsentimiento.practica_id == practica_id,
        FirmaConsentimiento.estudiante_id == current_user.id,
    ).first()
    if ya_firmo:
        raise HTTPException(status_code=409, detail="Ya has firmado el consentimiento para esta práctica")

    ip = request.client.host if request.client else "0.0.0.0"
    user_agent = request.headers.get("user-agent", "")

    firma = FirmaConsentimiento(
        practica_id=practica_id,
        estudiante_id=current_user.id,
        ip_address=ip,
        user_agent=user_agent[:500],
    )
    db.add(firma)

    p.total_firmas_obtenidas = (
        db.query(FirmaConsentimiento)
        .filter(FirmaConsentimiento.practica_id == practica_id)
        .count()
    ) + 1

    firmas_req = p.total_firmas_requeridas or max(1, math.ceil(p.num_alumnos * 0.66))
    p.total_firmas_requeridas = firmas_req

    if p.total_firmas_obtenidas >= firmas_req:
        p.quorum_alcanzado = True
        if p.estado == EstadoPracticaEnum.pendiente_quorum:
            # Quórum alcanzado: avanza a aprobada_curriculo para que el decano avalúe
            registrar_historial(db, "practica", practica_id,
                                EstadoPracticaEnum.pendiente_quorum,
                                EstadoPracticaEnum.aprobada_curriculo, None)
            p.estado = EstadoPracticaEnum.aprobada_curriculo
            if p.profesor_id:
                _notif(db, p.profesor_id, "practica_estado",
                       f"Práctica '{p.nombre_practica}' alcanzó quórum y fue aprobada por Comité de Currículo ✅",
                       "Siguiente paso: aval del Consejo de Facultad (Decano).")
            _notif_rol(db, RolEnum.decano,
                       f"Práctica lista para aval: '{p.nombre_practica}'",
                       "Se alcanzó el quórum de firmas. La práctica requiere su aval como Consejo de Facultad.")

    db.commit()
    db.refresh(firma)
    return firma


class RechazoPracticaBody(BaseModel):
    observaciones_jefe: Optional[str] = None


class TarifaCreate(BaseModel):
    descripcion: str
    valor_dia: float
    aplica_desde: str
    is_active: bool = True


class TarifaUpdate(BaseModel):
    descripcion: Optional[str] = None
    valor_dia: Optional[float] = None
    is_active: Optional[bool] = None


@router.patch("/{practica_id}/rechazar", response_model=PracticaOut)
def rechazar_practica(
    practica_id: int,
    body: RechazoPracticaBody = RechazoPracticaBody(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(
        RolEnum.jefe_programa, RolEnum.decano, RolEnum.admin,
    )),
):
    p = db.query(Practica).filter(Practica.id == practica_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Práctica no encontrada")

    # Cualquier etapa del flujo puede ser rechazada por la instancia correspondiente
    RECHAZABLES = [
        EstadoPracticaEnum.solicitada,
        EstadoPracticaEnum.pendiente_quorum,
        EstadoPracticaEnum.aprobada_curriculo,
        EstadoPracticaEnum.aprobada_facultad,
    ]
    if p.estado not in RECHAZABLES:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede rechazar una práctica en estado '{p.estado.value}'.",
        )

    roles_etapa = {
        EstadoPracticaEnum.solicitada: [RolEnum.jefe_programa],
        EstadoPracticaEnum.pendiente_quorum: [RolEnum.jefe_programa],
        EstadoPracticaEnum.aprobada_curriculo: [RolEnum.decano, RolEnum.jefe_programa],  # Jefe puede retractar su aprobación
        EstadoPracticaEnum.aprobada_facultad: [RolEnum.admin, RolEnum.decano],  # Decano puede retractar su aval
    }
    if current_user.rol not in roles_etapa.get(p.estado, []):
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos para rechazar en la etapa actual del flujo.",
        )

    registrar_historial(db, "practica", practica_id, p.estado,
                        EstadoPracticaEnum.rechazada, current_user.id,
                        body.observaciones_jefe if body else None)
    p.estado = EstadoPracticaEnum.rechazada
    if body and body.observaciones_jefe:
        p.observaciones_jefe = body.observaciones_jefe
    if p.profesor_id:
        rol_label = {
            RolEnum.jefe_programa: "Comité de Currículo",
            RolEnum.decano: "Consejo de Facultad",
            RolEnum.admin: "Vicerrectoría Académica",
        }.get(current_user.rol, "la instancia evaluadora")
        obs = f" Motivo: {body.observaciones_jefe}" if body and body.observaciones_jefe else ""
        _notif(db, p.profesor_id, "practica_rechazada",
               f"Práctica '{p.nombre_practica}' rechazada ❌",
               f"{rol_label} rechazó la práctica.{obs}")
    db.commit()
    return _enrich(_reload(db, practica_id), testing_mode=es_modo_prueba(db))


class InformeBody(BaseModel):
    informe_resultados: str
    observaciones: Optional[str] = None


def _dias_habiles(desde: date, hasta: date) -> int:
    """Cuenta días hábiles (lunes-viernes) EXCLUYE el día 'desde'.
    Ej: práctica termina viernes, informe lunes = 1 día hábil transcurrido.
    """
    total = 0
    d = desde + timedelta(days=1)  # No cuenta el día de regreso
    while d <= hasta:
        if d.weekday() < 5:
            total += 1
        d += timedelta(days=1)
    return total


@router.patch("/{practica_id}/iniciar", response_model=PracticaOut,
              summary="Confirma el inicio de la práctica (Fase 4 — ejecución)")
def iniciar_practica(
    practica_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.profesor)),
):
    """El docente confirma el inicio el día de la práctica. Requiere aprobación final."""
    p = db.query(Practica).filter(Practica.id == practica_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Práctica no encontrada")
    if p.profesor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Solo el docente titular puede confirmar el inicio")
    if p.estado != EstadoPracticaEnum.aprobado_transporte:
        raise HTTPException(
            status_code=400,
            detail="Solo se puede iniciar una práctica con aprobación final de la Vicerrectoría.",
        )
    hoy = datetime.now(timezone.utc).date()
    if p.fecha_inicio and p.fecha_inicio.date() > hoy and not es_modo_prueba(db):
        raise HTTPException(
            status_code=400,
            detail=f"La práctica no puede iniciarse antes de su fecha programada ({p.fecha_inicio.strftime('%d/%m/%Y')}).",
        )
    registrar_historial(db, "practica", practica_id,
                        EstadoPracticaEnum.aprobado_transporte,
                        EstadoPracticaEnum.en_ejecucion, current_user.id)
    p.estado = EstadoPracticaEnum.en_ejecucion
    _notif_rol(db, RolEnum.jefe_programa,
               f"Práctica '{p.nombre_practica}' en ejecución 🚌",
               f"El docente {current_user.nombres} {current_user.apellidos} confirmó el inicio.")
    db.commit()
    return _enrich(_reload(db, practica_id), testing_mode=es_modo_prueba(db))


@router.patch("/{practica_id}/finalizar", response_model=PracticaOut,
              summary="Cierra la práctica con informe de resultados (Art. 7 Acuerdo 003)")
def finalizar_practica(
    practica_id: int,
    body: InformeBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(
        RolEnum.profesor, RolEnum.jefe_programa, RolEnum.admin,
    )),
):
    """
    El docente sube el informe (máx. 5 días hábiles post-práctica).
    El jefe_programa o admin pueden también cerrar la práctica.
    """
    p = db.query(Practica).filter(Practica.id == practica_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Práctica no encontrada")
    if p.estado != EstadoPracticaEnum.en_ejecucion:
        raise HTTPException(
            status_code=400,
            detail="Solo se puede finalizar una práctica que esté en ejecución. Primero confirma el inicio.",
        )
    # Verificar plazo de 5 días hábiles (solo para docentes)
    if current_user.rol == RolEnum.profesor:
        if p.profesor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Solo el docente titular puede subir el informe")
        if p.fecha_fin and not es_modo_prueba(db):
            hoy = datetime.now(timezone.utc).date()
            dias_transcurridos = _dias_habiles(p.fecha_fin.date(), hoy)
            PLAZO_INFORME = 5
            if dias_transcurridos > PLAZO_INFORME:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"El plazo para entregar el informe venció hace "
                        f"{dias_transcurridos - PLAZO_INFORME} día(s) hábil(es). "
                        f"Comuníquese con el Jefe de Programa."
                    ),
                )
    if not body.informe_resultados.strip():
        raise HTTPException(status_code=422, detail="El informe de resultados no puede estar vacío.")
    registrar_historial(db, "practica", practica_id, p.estado,
                        EstadoPracticaEnum.finalizada, current_user.id)
    p.estado = EstadoPracticaEnum.finalizada
    p.informe_resultados = body.informe_resultados
    p.fecha_informe = datetime.now(timezone.utc)
    if body.observaciones:
        p.observaciones = body.observaciones
    if p.profesor_id and current_user.rol != RolEnum.profesor:
        _notif(db, p.profesor_id, "practica_estado",
               f"Práctica '{p.nombre_practica}' finalizada y cerrada ✅",
               "El proceso de práctica extramural ha sido cerrado oficialmente.")
    _notif_rol(db, RolEnum.jefe_programa,
               f"Práctica '{p.nombre_practica}' cerrada con informe ✅",
               "El informe de resultados fue entregado y la práctica está finalizada.")
    db.commit()
    return _enrich(_reload(db, practica_id), testing_mode=es_modo_prueba(db))


@router.get("/tarifas/todas", response_model=list[TarifaViaticoOut])
def listar_todas_tarifas(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.jefe_programa, RolEnum.decano, RolEnum.admin)),
):
    return db.query(TarifaViatico).order_by(TarifaViatico.aplica_desde.desc()).all()


@router.post("/tarifas/", response_model=TarifaViaticoOut, status_code=201)
def crear_tarifa(
    body: TarifaCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.admin)),
):
    from datetime import date as date_type
    aplica = date_type.fromisoformat(body.aplica_desde) if isinstance(body.aplica_desde, str) else body.aplica_desde
    if body.valor_dia <= 0:
        raise HTTPException(status_code=400, detail="El valor por día debe ser mayor a 0")
    tarifa = TarifaViatico(
        descripcion=body.descripcion,
        valor_dia=body.valor_dia,
        aplica_desde=aplica,
        is_active=body.is_active,
    )
    db.add(tarifa)
    db.commit()
    db.refresh(tarifa)
    return tarifa


@router.patch("/tarifas/{tarifa_id}", response_model=TarifaViaticoOut)
def actualizar_tarifa(
    tarifa_id: int,
    body: TarifaUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.admin)),
):
    tarifa = db.query(TarifaViatico).filter(TarifaViatico.id == tarifa_id).first()
    if not tarifa:
        raise HTTPException(status_code=404, detail="Tarifa no encontrada")
    if body.valor_dia is not None and body.valor_dia <= 0:
        raise HTTPException(status_code=400, detail="El valor por día debe ser mayor a 0")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(tarifa, field, value)
    db.commit()
    db.refresh(tarifa)
    return tarifa


# ── Historial de estados (SF-06) ──────────────────────────────────────────────

@router.get("/{practica_id}/historial", summary="Historial de cambios de estado (SF-06)")
def historial_practica(
    practica_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    registros = (
        db.query(HistorialEstado)
        .filter(HistorialEstado.entidad == "practica", HistorialEstado.entidad_id == practica_id)
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


# ── Pagos de viáticos (SF-09) ──────────────────────────────────────────────────

class PagoViaticoIn(BaseModel):
    monto_pagado: float
    fecha_pago: str
    observaciones: Optional[str] = None


@router.post("/{practica_id}/registrar-pago", status_code=201, summary="Registrar pago de viáticos (SF-09)")
def registrar_pago_viatico(
    practica_id: int,
    body: PagoViaticoIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.admin, RolEnum.jefe_programa, RolEnum.decano)),
):
    p = db.query(Practica).filter(Practica.id == practica_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Práctica no encontrada")
    if p.estado not in (EstadoPracticaEnum.finalizada, EstadoPracticaEnum.en_ejecucion, EstadoPracticaEnum.aprobado_transporte):
        raise HTTPException(status_code=400, detail="Solo se pueden registrar pagos en prácticas aprobadas o finalizadas")
    if body.monto_pagado <= 0:
        raise HTTPException(status_code=400, detail="El monto debe ser mayor a cero")

    try:
        fecha = datetime.fromisoformat(body.fecha_pago)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido (use ISO 8601)")

    pago = PagoViatico(
        practica_id=practica_id,
        registrado_por_id=current_user.id,
        monto_pagado=body.monto_pagado,
        fecha_pago=fecha,
        observaciones=body.observaciones,
    )
    db.add(pago)

    # Notificar al profesor
    try:
        from app.models.notificacion import Notificacion
        db.add(Notificacion(
            usuario_id=p.profesor_id,
            titulo="Viáticos pagados",
            mensaje=f"Se registró el pago de viáticos para «{p.nombre_practica}» "
                    f"por ${body.monto_pagado:,.0f} COP.",
            tipo="practica",
        ))
    except Exception:
        pass

    db.commit()
    db.refresh(pago)
    return {
        "id": pago.id,
        "practica_id": pago.practica_id,
        "monto_pagado": pago.monto_pagado,
        "fecha_pago": pago.fecha_pago.isoformat(),
        "observaciones": pago.observaciones,
        "registrado_por_id": pago.registrado_por_id,
        "created_at": pago.created_at.isoformat() if pago.created_at else None,
    }


@router.get("/{practica_id}/pagos", summary="Listar pagos de viáticos (SF-09)")
def listar_pagos_viatico(
    practica_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.admin, RolEnum.jefe_programa, RolEnum.decano, RolEnum.profesor)),
):
    pagos = db.query(PagoViatico).filter(PagoViatico.practica_id == practica_id).order_by(PagoViatico.fecha_pago.desc()).all()
    return [
        {
            "id": pg.id,
            "monto_pagado": pg.monto_pagado,
            "fecha_pago": pg.fecha_pago.isoformat(),
            "observaciones": pg.observaciones,
            "registrado_por": f"{pg.registrado_por.nombres} {pg.registrado_por.apellidos}" if pg.registrado_por else None,
            "created_at": pg.created_at.isoformat() if pg.created_at else None,
        }
        for pg in pagos
    ]


@router.get("/{practica_id}/viaticos", response_model=list[ViaticosCalculadoOut])
def calcular_viaticos(
    practica_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.profesor, RolEnum.jefe_programa, RolEnum.decano, RolEnum.admin)),
):
    """RF-PRA-02/03 — Calcula viáticos cruzando días de práctica con tarifas vigentes."""
    p = db.query(Practica).filter(Practica.id == practica_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Práctica no encontrada")

    tarifas = db.query(TarifaViatico).filter(
        TarifaViatico.is_active == True,
        TarifaViatico.aplica_desde <= p.fecha_inicio.date(),
    ).all()

    NUM_DOCENTES = 1  # Viáticos para el docente responsable (Acuerdo 003/2012)
    resultado = []
    for tarifa in tarifas:
        subtotal = tarifa.valor_dia * p.duracion_dias * NUM_DOCENTES
        resultado.append(ViaticosCalculadoOut(
            tarifa_id=tarifa.id,
            descripcion=tarifa.descripcion,
            valor_dia=tarifa.valor_dia,
            num_dias=p.duracion_dias,
            num_personas=NUM_DOCENTES,
            subtotal=subtotal,
        ))
    return resultado



