"""Reportes agregados — estadísticas de convocatorias, prácticas y presupuesto."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.db.database import get_db
from app.models.user import User, RolEnum
from app.models.convocatoria import Convocatoria, EstadoConvocatoriaEnum, Asignatura
from app.models.postulacion import Postulacion, EstadoPostulacionEnum
from app.models.practica import Practica, EstadoPracticaEnum, RutaPractica, FirmaConsentimiento, Viatico, TarifaViatico
from app.models.presupuesto import Presupuesto
from app.api.deps import get_current_user, require_roles

router = APIRouter()


@router.get("/resumen")
def resumen_general(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.decano, RolEnum.admin)),
):
    """Resumen ejecutivo para la página de Reportes."""

    # ── Convocatorias ─────────────────────────────────────────────────────────
    convs = db.query(Convocatoria).all()
    conv_por_estado = {}
    for c in convs:
        k = c.estado.value
        conv_por_estado[k] = conv_por_estado.get(k, 0) + 1

    periodos = sorted(set(c.periodo_academico for c in convs), reverse=True)

    # ── Postulaciones ─────────────────────────────────────────────────────────
    posts = db.query(Postulacion).options(
        joinedload(Postulacion.estudiante),
        joinedload(Postulacion.convocatoria).joinedload(Convocatoria.asignatura),
    ).all()
    post_por_estado = {}
    for p in posts:
        k = p.estado.value
        post_por_estado[k] = post_por_estado.get(k, 0) + 1

    seleccionados = [p for p in posts if p.estado == EstadoPostulacionEnum.seleccionado]

    # ── Monitores seleccionados (con datos) ───────────────────────────────────
    monitores = []
    for p in seleccionados:
        monitores.append({
            "postulacion_id": p.id,
            "estudiante": f"{p.estudiante.nombres} {p.estudiante.apellidos}" if p.estudiante else "—",
            "codigo": p.estudiante.codigo if p.estudiante else "—",
            "convocatoria": p.convocatoria.titulo if p.convocatoria else "—",
            "asignatura": p.convocatoria.asignatura.nombre if p.convocatoria and p.convocatoria.asignatura else "—",
            "puntaje_final": p.puntaje_final,
            "periodo": p.convocatoria.periodo_academico if p.convocatoria else "—",
        })

    # ── Prácticas ─────────────────────────────────────────────────────────────
    practicas = db.query(Practica).options(
        joinedload(Practica.asignatura),
        joinedload(Practica.profesor),
    ).all()
    prac_por_estado = {}
    for pr in practicas:
        k = pr.estado.value
        prac_por_estado[k] = prac_por_estado.get(k, 0) + 1

    practicas_lista = []
    for pr in practicas:
        practicas_lista.append({
            "id": pr.id,
            "nombre": pr.nombre_practica,
            "asignatura": pr.asignatura.nombre if pr.asignatura else "—",
            "profesor": f"{pr.profesor.nombres} {pr.profesor.apellidos}" if pr.profesor else "—",
            "estado": pr.estado.value,
            "periodo": pr.periodo_academico,
            "fecha_inicio": pr.fecha_inicio.strftime("%d/%m/%Y") if pr.fecha_inicio else None,
            "fecha_fin": pr.fecha_fin.strftime("%d/%m/%Y") if pr.fecha_fin else None,
            "num_alumnos": pr.num_alumnos,
            "quorum_alcanzado": pr.quorum_alcanzado,
            "firmas_obtenidas": pr.total_firmas_obtenidas,
            "firmas_requeridas": pr.total_firmas_requeridas,
        })

    # ── Presupuesto ───────────────────────────────────────────────────────────
    presupuestos = db.query(Presupuesto).order_by(Presupuesto.periodo_academico.desc()).all()
    presupuesto_resumen = []
    for p in presupuestos:
        disponible = p.monto_total_asignado - p.monto_ejecutado - p.monto_comprometido
        pct = round((p.monto_ejecutado / p.monto_total_asignado) * 100, 1) if p.monto_total_asignado > 0 else 0
        presupuesto_resumen.append({
            "periodo": p.periodo_academico,
            "total_asignado": p.monto_total_asignado,
            "ejecutado": p.monto_ejecutado,
            "comprometido": p.monto_comprometido,
            "disponible": disponible,
            "porcentaje_ejecutado": pct,
            "estado": p.estado.value if p.estado else "aprobado",
        })

    return {
        "convocatorias": {
            "total": len(convs),
            "por_estado": conv_por_estado,
            "periodos": periodos,
        },
        "postulaciones": {
            "total": len(posts),
            "por_estado": post_por_estado,
        },
        "monitores_seleccionados": monitores,
        "practicas": {
            "total": len(practicas),
            "por_estado": prac_por_estado,
            "lista": practicas_lista,
        },
        "presupuesto": presupuesto_resumen,
    }


@router.get("/fo14/{convocatoria_id}")
def datos_fo14(
    convocatoria_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.jefe_programa, RolEnum.decano, RolEnum.profesor)),
):
    """Datos completos para generar el formulario MI-FOR-FO-14 (Requerimiento Monitores)."""
    conv = db.query(Convocatoria).options(
        joinedload(Convocatoria.asignatura),
        joinedload(Convocatoria.profesor),
        joinedload(Convocatoria.postulaciones).joinedload(Postulacion.estudiante),
    ).filter(Convocatoria.id == convocatoria_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")

    monitor = next(
        (p for p in conv.postulaciones if p.estado == EstadoPostulacionEnum.seleccionado), None
    )

    return {
        "convocatoria": {
            "id": conv.id,
            "titulo": conv.titulo,
            "periodo_academico": conv.periodo_academico,
            "tipo_monitoria": conv.tipo_monitoria.value,
            "horas_semana": conv.horas_semana,
            "horas_semestre": conv.horas_semestre,
            "descripcion_actividades": conv.descripcion_actividades,
            "promedio_minimo": conv.promedio_minimo,
            "creditos_minimo_pct": conv.creditos_minimo_pct,
            "sede": conv.sede,
        },
        "asignatura": {
            "nombre": conv.asignatura.nombre if conv.asignatura else "—",
            "codigo": conv.asignatura.codigo if conv.asignatura else "—",
            "creditos": conv.asignatura.creditos if conv.asignatura else 0,
            "programa": conv.asignatura.programa if conv.asignatura else "—",
            "facultad": conv.asignatura.facultad if conv.asignatura else None,
            "semestre": conv.asignatura.semestre if conv.asignatura else 0,
        },
        "docente": {
            "nombres": f"{conv.profesor.nombres} {conv.profesor.apellidos}" if conv.profesor else "—",
            "cedula": conv.profesor.cedula if conv.profesor else "—",
            "email": conv.profesor.email if conv.profesor else "—",
        },
        "monitor": {
            "nombres": f"{monitor.estudiante.nombres} {monitor.estudiante.apellidos}" if monitor and monitor.estudiante else None,
            "codigo": monitor.estudiante.codigo if monitor and monitor.estudiante else None,
            "cedula": monitor.estudiante.cedula if monitor and monitor.estudiante else None,
            "promedio": monitor.estudiante.promedio if monitor and monitor.estudiante else None,
            "porcentaje_creditos": monitor.estudiante.porcentaje_creditos if monitor and monitor.estudiante else None,
            "programa": monitor.estudiante.programa if monitor and monitor.estudiante else None,
            "nota_asignatura": monitor.nota_asignatura if monitor else None,
            "nota_entrevista": monitor.nota_entrevista if monitor else None,
            "puntaje_final": monitor.puntaje_final if monitor else None,
        } if monitor else None,
        "total_postulantes": len(conv.postulaciones),
    }


@router.get("/fo15/{practica_id}")
def datos_fo15(
    practica_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.jefe_programa, RolEnum.decano, RolEnum.profesor)),
):
    """Datos completos para generar el formulario MI-FOR-FO-15 (Requerimiento Prácticas Extramuros)."""
    pr = db.query(Practica).options(
        joinedload(Practica.asignatura),
        joinedload(Practica.profesor),
        joinedload(Practica.rutas),
        joinedload(Practica.firmas).joinedload(FirmaConsentimiento.estudiante),
        joinedload(Practica.viaticos).joinedload(Viatico.tarifa),
    ).filter(Practica.id == practica_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="Práctica no encontrada")

    rutas = sorted(pr.rutas, key=lambda r: r.orden)
    firmas = sorted(pr.firmas, key=lambda f: f.signed_at or f.id)

    return {
        "practica": {
            "id": pr.id,
            "nombre": pr.nombre_practica,
            "periodo_academico": pr.periodo_academico,
            "estado": pr.estado.value,
            "fecha_inicio": pr.fecha_inicio.isoformat() if pr.fecha_inicio else None,
            "fecha_fin": pr.fecha_fin.isoformat() if pr.fecha_fin else None,
            "duracion_dias": pr.duracion_dias,
            "num_alumnos": pr.num_alumnos,
            "quorum_alcanzado": pr.quorum_alcanzado,
            "firmas_obtenidas": pr.total_firmas_obtenidas,
            "firmas_requeridas": pr.total_firmas_requeridas,
            "observaciones": pr.observaciones,
            "tipo_docente": pr.tipo_docente.value if pr.tipo_docente else None,
            "hora_salida": pr.hora_salida,
            "hora_llegada": pr.hora_llegada,
        },
        "asignatura": {
            "nombre": pr.asignatura.nombre if pr.asignatura else "—",
            "codigo": pr.asignatura.codigo if pr.asignatura else "—",
            "programa": pr.asignatura.programa if pr.asignatura else "—",
            "facultad": pr.asignatura.facultad if pr.asignatura else None,
        },
        "docente": {
            "nombres": f"{pr.profesor.nombres} {pr.profesor.apellidos}" if pr.profesor else "—",
            "cedula": pr.profesor.cedula if pr.profesor else "—",
            "email": pr.profesor.email if pr.profesor else "—",
        },
        "rutas": [
            {
                "orden": r.orden,
                "tipo_punto": r.tipo_punto,
                "lugar": r.lugar,
                "municipio": r.municipio,
                "departamento": r.departamento,
                "distancia_km": float(r.distancia_km) if r.distancia_km is not None else None,
            } for r in rutas
        ],
        "participantes": [
            {
                "nombres": f"{f.estudiante.nombres} {f.estudiante.apellidos}" if f.estudiante else "—",
                "codigo": f.estudiante.codigo if f.estudiante else "—",
                "cedula": f.estudiante.cedula if f.estudiante else "—",
                "fecha_firma": f.signed_at.strftime("%d/%m/%Y %H:%M") if f.signed_at else None,
                "eps": f.estudiante.eps if f.estudiante else None,
                "arl": f.estudiante.arl if f.estudiante else None,
                "fondo_pensiones": f.estudiante.fondo_pensiones if f.estudiante else None,
            } for f in firmas
        ],
        "viaticos": [
            {
                "descripcion": v.tarifa.descripcion if v.tarifa else v.descripcion,
                "valor_dia": float(v.tarifa.valor_dia) if v.tarifa and v.tarifa.valor_dia is not None else 0,
                "num_dias": v.num_dias,
                "num_personas": v.num_personas,
                "total": float(v.valor_calculado) if v.valor_calculado is not None else 0,
                "descripcion_extra": v.descripcion,
            } for v in pr.viaticos
        ],
        "total_viaticos": float(sum(float(v.valor_calculado or 0) for v in pr.viaticos)),
    }


@router.get("/fo16/{practica_id}")
def datos_fo16(
    practica_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.jefe_programa, RolEnum.decano, RolEnum.profesor)),
):
    """Datos completos para generar el formulario MI-FOR-FO-16 (Justificación Prácticas Extramuros)."""
    pr = db.query(Practica).options(
        joinedload(Practica.asignatura),
        joinedload(Practica.profesor),
        joinedload(Practica.rutas),
    ).filter(Practica.id == practica_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="Práctica no encontrada")

    rutas = sorted(pr.rutas, key=lambda r: r.orden)

    return {
        "practica": {
            "id": pr.id,
            "nombre": pr.nombre_practica,
            "periodo_academico": pr.periodo_academico,
            "estado": pr.estado.value,
            "fecha_inicio": pr.fecha_inicio.isoformat() if pr.fecha_inicio else None,
            "fecha_fin": pr.fecha_fin.isoformat() if pr.fecha_fin else None,
            "duracion_dias": pr.duracion_dias,
            "num_alumnos": pr.num_alumnos,
            "hora_salida": pr.hora_salida,
            "hora_llegada": pr.hora_llegada,
            "caracter_curso": pr.caracter_curso,
            "caracteristica_curso": pr.caracteristica_curso,
            "modalidad_docente": pr.modalidad_docente,
            "articulacion_curso": pr.articulacion_curso,
            "descripcion_practica": pr.descripcion_practica,
            "justificacion": pr.justificacion,
            "metodologia": pr.metodologia,
            "carta_autorizacion_empresa": pr.carta_autorizacion_empresa,
            "evaluacion": pr.evaluacion,
            "observaciones": pr.observaciones,
            "informe_resultados": pr.informe_resultados,
            "fecha_informe": pr.fecha_informe.isoformat() if pr.fecha_informe else None,
        },
        "asignatura": {
            "nombre": pr.asignatura.nombre if pr.asignatura else "—",
            "codigo": pr.asignatura.codigo if pr.asignatura else "—",
            "creditos": pr.asignatura.creditos if pr.asignatura else 0,
            "semestre": pr.asignatura.semestre if pr.asignatura else 0,
            "programa": pr.asignatura.programa if pr.asignatura else "—",
            "facultad": pr.asignatura.facultad if pr.asignatura else None,
        },
        "docente": {
            "nombres": f"{pr.profesor.nombres} {pr.profesor.apellidos}" if pr.profesor else "—",
            "cedula": pr.profesor.cedula if pr.profesor else "—",
            "email": pr.profesor.email if pr.profesor else "—",
        },
        "rutas": [
            {
                "orden": r.orden,
                "tipo_punto": r.tipo_punto,
                "lugar": r.lugar,
                "municipio": r.municipio,
                "departamento": r.departamento,
                "distancia_km": float(r.distancia_km) if r.distancia_km is not None else None,
                "vereda": r.vereda,
            } for r in rutas
        ],
    }


@router.get("/consentimiento/{practica_id}")
def datos_consentimiento(
    practica_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Datos para el PDF de consentimiento individual del estudiante."""
    pr = db.query(Practica).options(
        joinedload(Practica.asignatura),
        joinedload(Practica.profesor),
        joinedload(Practica.rutas),
    ).filter(Practica.id == practica_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="Práctica no encontrada")

    firma = db.query(FirmaConsentimiento).filter(
        FirmaConsentimiento.practica_id == practica_id,
        FirmaConsentimiento.estudiante_id == current_user.id,
    ).first()

    if current_user.rol == RolEnum.estudiante and not firma:
        raise HTTPException(status_code=403, detail="No has firmado el consentimiento de esta práctica")

    rutas_ordenadas = sorted(pr.rutas, key=lambda r: r.orden)
    origen = next((r for r in rutas_ordenadas if r.tipo_punto == "origen"), rutas_ordenadas[0] if rutas_ordenadas else None)
    destino = next((r for r in reversed(rutas_ordenadas) if r.tipo_punto == "destino"), rutas_ordenadas[-1] if rutas_ordenadas else None)

    return {
        "estudiante": {
            "nombres": f"{current_user.nombres} {current_user.apellidos}",
            "codigo": current_user.codigo,
            "cedula": current_user.cedula,
            "programa": current_user.programa,
        },
        "practica": {
            "id": pr.id,
            "nombre": pr.nombre_practica,
            "periodo_academico": pr.periodo_academico,
            "fecha_inicio": pr.fecha_inicio.isoformat() if pr.fecha_inicio else None,
            "fecha_fin": pr.fecha_fin.isoformat() if pr.fecha_fin else None,
            "duracion_dias": pr.duracion_dias,
            "num_alumnos": pr.num_alumnos,
            "observaciones": pr.observaciones,
        },
        "asignatura": {
            "nombre": pr.asignatura.nombre if pr.asignatura else "—",
            "codigo": pr.asignatura.codigo if pr.asignatura else "—",
            "programa": pr.asignatura.programa if pr.asignatura else "—",
            "facultad": pr.asignatura.facultad if pr.asignatura else None,
        },
        "docente": {
            "nombres": f"{pr.profesor.nombres} {pr.profesor.apellidos}" if pr.profesor else "—",
            "email": pr.profesor.email if pr.profesor else "—",
        },
        "origen": origen.lugar if origen else "—",
        "origen_municipio": origen.municipio if origen else "—",
        "destino": destino.lugar if destino else "—",
        "destino_municipio": destino.municipio if destino else "—",
        "rutas": [
            {"orden": r.orden, "tipo_punto": r.tipo_punto, "lugar": r.lugar,
             "municipio": r.municipio, "departamento": r.departamento, "distancia_km": r.distancia_km}
            for r in rutas_ordenadas
        ],
        "fecha_firma": firma.signed_at.strftime("%d/%m/%Y %H:%M") if firma and firma.signed_at else None,
        "ip_firma": firma.ip_address if firma else None,
    }


@router.get("/fo46/{convocatoria_id}")
def datos_fo46(
    convocatoria_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.jefe_programa, RolEnum.decano, RolEnum.profesor)),
):
    """Datos para MI-FOR-FO-46 — Convocatoria para Monitores (cartel público)."""
    conv = db.query(Convocatoria).options(
        joinedload(Convocatoria.asignatura),
        joinedload(Convocatoria.profesor),
    ).filter(Convocatoria.id == convocatoria_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")

    return {
        "convocatoria": {
            "id": conv.id,
            "titulo": conv.titulo,
            "periodo_academico": conv.periodo_academico,
            "tipo_monitoria": conv.tipo_monitoria.value,
            "horas_semana": conv.horas_semana,
            "horas_semestre": conv.horas_semestre,
            "descripcion_actividades": conv.descripcion_actividades,
            "promedio_minimo": float(conv.promedio_minimo) if conv.promedio_minimo else 0,
            "creditos_minimo_pct": float(conv.creditos_minimo_pct) if conv.creditos_minimo_pct else 0,
            "fecha_inicio_postulacion": conv.fecha_inicio_postulacion.isoformat() if conv.fecha_inicio_postulacion else None,
            "fecha_fin_postulacion": conv.fecha_fin_postulacion.isoformat() if conv.fecha_fin_postulacion else None,
            "num_monitores_requeridos": conv.num_monitores_requeridos,
            "sede": conv.sede,
            "estado": conv.estado.value,
        },
        "asignatura": {
            "nombre": conv.asignatura.nombre if conv.asignatura else "—",
            "codigo": conv.asignatura.codigo if conv.asignatura else "—",
            "creditos": conv.asignatura.creditos if conv.asignatura else 0,
            "semestre": conv.asignatura.semestre if conv.asignatura else 0,
            "programa": conv.asignatura.programa if conv.asignatura else "—",
            "facultad": conv.asignatura.facultad if conv.asignatura else None,
        },
        "docente": {
            "nombres": f"{conv.profesor.nombres} {conv.profesor.apellidos}" if conv.profesor else "—",
            "cedula": conv.profesor.cedula if conv.profesor else "—",
            "email": conv.profesor.email if conv.profesor else "—",
            "programa": conv.profesor.programa if conv.profesor else "—",
        },
    }


@router.get("/fo05/{practica_id}")
def datos_fo05(
    practica_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.jefe_programa, RolEnum.decano, RolEnum.profesor)),
):
    """Datos para AP-INF-FO-05 — Solicitud de Desplazamiento Vial."""
    pr = db.query(Practica).options(
        joinedload(Practica.asignatura),
        joinedload(Practica.profesor),
        joinedload(Practica.rutas),
        joinedload(Practica.firmas).joinedload(FirmaConsentimiento.estudiante),
    ).filter(Practica.id == practica_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="Práctica no encontrada")

    rutas = sorted(pr.rutas, key=lambda r: r.orden)
    participantes = [
        {
            "nombres": f"{f.estudiante.nombres} {f.estudiante.apellidos}" if f.estudiante else "—",
            "codigo": f.estudiante.codigo if f.estudiante else "—",
            "cedula": f.estudiante.cedula if f.estudiante else "—",
            "eps": f.estudiante.eps if f.estudiante else None,
            "arl": f.estudiante.arl if f.estudiante else None,
            "fondo_pensiones": f.estudiante.fondo_pensiones if f.estudiante else None,
        }
        for f in sorted(pr.firmas, key=lambda f: f.id)
    ]

    return {
        "practica": {
            "id": pr.id,
            "nombre": pr.nombre_practica,
            "periodo_academico": pr.periodo_academico,
            "fecha_inicio": pr.fecha_inicio.isoformat() if pr.fecha_inicio else None,
            "fecha_fin": pr.fecha_fin.isoformat() if pr.fecha_fin else None,
            "hora_salida": pr.hora_salida,
            "hora_llegada": pr.hora_llegada,
            "num_alumnos": pr.num_alumnos,
            "duracion_dias": pr.duracion_dias,
            "placa_vehiculo": pr.placa_vehiculo,
            "tipo_vehiculo": pr.tipo_vehiculo,
            "empresa_transporte": pr.empresa_transporte,
            "conductor_nombre": pr.conductor_nombre,
            "observaciones": pr.observaciones,
            "sede": pr.sede,
        },
        "asignatura": {
            "nombre": pr.asignatura.nombre if pr.asignatura else "—",
            "codigo": pr.asignatura.codigo if pr.asignatura else "—",
            "programa": pr.asignatura.programa if pr.asignatura else "—",
            "facultad": pr.asignatura.facultad if pr.asignatura else None,
        },
        "docente": {
            "nombres": f"{pr.profesor.nombres} {pr.profesor.apellidos}" if pr.profesor else "—",
            "cedula": pr.profesor.cedula if pr.profesor else "—",
            "email": pr.profesor.email if pr.profesor else "—",
            "tipo_docente": pr.profesor.tipo_docente if pr.profesor else None,
            "modalidad_docente": pr.profesor.modalidad_docente if pr.profesor else None,
        },
        "rutas": [
            {
                "orden": r.orden,
                "tipo_punto": r.tipo_punto,
                "lugar": r.lugar,
                "municipio": r.municipio,
                "departamento": r.departamento,
                "distancia_km": float(r.distancia_km) if r.distancia_km is not None else None,
                "vereda": r.vereda,
            } for r in rutas
        ],
        "participantes": participantes,
    }


@router.get("/practicas-programa")
def practicas_por_programa(
    programa: Optional[str] = Query(None),
    periodo: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.jefe_programa, RolEnum.decano, RolEnum.admin)),
):
    """Lista consolidada de prácticas por programa/período — FO-15 jefe_programa / Consejo Académico."""
    q = db.query(Practica).options(
        joinedload(Practica.asignatura),
        joinedload(Practica.profesor),
        joinedload(Practica.rutas),
        joinedload(Practica.viaticos),
    )
    # jefe_programa sólo ve su propio programa (ignorar parámetro externo)
    programa_filtro = current_user.programa if current_user.rol == RolEnum.jefe_programa else programa
    if programa_filtro:
        q = q.join(Practica.asignatura).filter(Asignatura.programa == programa_filtro)
    if periodo:
        q = q.filter(Practica.periodo_academico == periodo)
    practicas = q.order_by(Practica.fecha_inicio).all()

    result = []
    for pr in practicas:
        rutas = sorted(pr.rutas, key=lambda r: r.orden)
        destino = next((r for r in reversed(rutas) if r.tipo_punto == "destino"), rutas[-1] if rutas else None)
        total_viat = float(sum(float(v.valor_calculado or 0) for v in pr.viaticos))
        ruta_str = " → ".join(
            f"{r.lugar}{(' – ' + r.municipio) if r.municipio else ''}" for r in rutas
        ) if rutas else "—"
        result.append({
            "id": pr.id,
            "nombre": pr.nombre_practica,
            "asignatura": pr.asignatura.nombre if pr.asignatura else "—",
            "asignatura_codigo": pr.asignatura.codigo if pr.asignatura else "—",
            "programa": pr.asignatura.programa if pr.asignatura else "—",
            "facultad": pr.asignatura.facultad if pr.asignatura else "—",
            "docente": f"{pr.profesor.nombres} {pr.profesor.apellidos}" if pr.profesor else "—",
            "periodo_academico": pr.periodo_academico,
            "estado": pr.estado.value,
            "fecha_inicio": pr.fecha_inicio.strftime("%d/%m/%Y") if pr.fecha_inicio else None,
            "hora_salida": pr.hora_salida,
            "fecha_fin": pr.fecha_fin.strftime("%d/%m/%Y") if pr.fecha_fin else None,
            "hora_llegada": pr.hora_llegada,
            "duracion_dias": pr.duracion_dias,
            "num_alumnos": pr.num_alumnos,
            "quorum_alcanzado": pr.quorum_alcanzado,
            "ruta": ruta_str,
            "destino": destino.lugar if destino else "—",
            "municipio_destino": destino.municipio if destino else "—",
            "total_viaticos": total_viat,
            "placa_vehiculo": pr.placa_vehiculo,
            "tipo_vehiculo": pr.tipo_vehiculo,
        })
    return result
