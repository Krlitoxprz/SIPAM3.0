"""
PDF Generator — server-side usando WeasyPrint + Jinja2.
Endpoints: /pdf/fo14/{conv_id}, /pdf/fo16/{practica_id}, /pdf/fo15/{practica_id}
"""
import os
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.db.database import get_db
from app.models.user import User, RolEnum
from app.models.convocatoria import Convocatoria, Asignatura
from app.models.postulacion import Postulacion, EstadoPostulacionEnum
from app.models.practica import Practica
from app.api.deps import get_current_user, require_roles

router = APIRouter()

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"

_jinja = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)

TIPO_MONITORIA_LABEL = {
    "nee": "a) Acompañamiento NEE (Bienestar)",
    "regimenes_especiales": "b) Regímenes Especiales",
    "academica_cursos": "c) Académica — Cursos/Asignaturas",
    "laboratorios": "d) Laboratorios",
    "tic": "e) TIC / Salas Informática",
    "permanencia_graduacion": "f) Permanencia y Graduación",
    "deportiva": "g) Deportiva (Bienestar)",
    "cultural": "h) Cultural y Artística (Bienestar)",
    "biblioteca": "i) Biblioteca",
    "acreditacion": "j) Acreditación y Registro Calificado",
    "investigacion": "k) Investigación / Proyección Social",
    "academica": "Académica",
    "administrativa": "Administrativa",
}


def _fmt_date(iso_or_dt) -> str:
    if not iso_or_dt:
        return "—"
    if isinstance(iso_or_dt, str):
        try:
            iso_or_dt = datetime.fromisoformat(iso_or_dt)
        except ValueError:
            return iso_or_dt
    return iso_or_dt.strftime("%d/%m/%Y")


def _fmt_cop(value) -> str:
    try:
        return f"${float(value):,.0f}".replace(",", ".")
    except Exception:
        return "—"


def _render_pdf(template_name: str, context: dict) -> bytes:
    """Renderiza el template Jinja2 y convierte a PDF con WeasyPrint.

    NOTA: Esta función es síncrona y CPU-intensiva. Los endpoints que la llaman
    están declarados como `def` (no `async def`) deliberadamente, para que
    FastAPI los envíe automáticamente al threadpool externo (anyio) y nunca
    bloqueen el event loop principal.
    """
    try:
        from weasyprint import HTML
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="WeasyPrint no está instalado en este servidor.",
        )
    html_str = _jinja.get_template(template_name).render(**context)
    return HTML(string=html_str, base_url=str(TEMPLATES_DIR)).write_pdf()


# ── FO-14 ─────────────────────────────────────────────────────────────────────

@router.get(
    "/fo14/{convocatoria_id}",
    summary="Generar PDF MI-FOR-FO-14 — Requerimiento de Monitores",
    response_class=Response,
)
def pdf_fo14(
    convocatoria_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.jefe_programa, RolEnum.decano, RolEnum.admin, RolEnum.profesor)),
):
    conv = (
        db.query(Convocatoria)
        .options(joinedload(Convocatoria.asignatura), joinedload(Convocatoria.profesor))
        .filter(Convocatoria.id == convocatoria_id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")

    seleccionado = (
        db.query(Postulacion)
        .filter(
            Postulacion.convocatoria_id == convocatoria_id,
            Postulacion.estado == EstadoPostulacionEnum.seleccionado,
        )
        .options(joinedload(Postulacion.estudiante))
        .first()
    )
    total_posts = db.query(Postulacion).filter_by(convocatoria_id=convocatoria_id).count()

    monitor = None
    if seleccionado and seleccionado.estudiante:
        e = seleccionado.estudiante
        monitor = {
            "nombres": f"{e.nombres} {e.apellidos}",
            "codigo": e.codigo,
            "cedula": e.cedula,
            "programa": e.programa,
            "promedio": float(e.promedio) if e.promedio else None,
            "porcentaje_creditos": float(e.porcentaje_creditos) if e.porcentaje_creditos else None,
            "nota_asignatura": float(seleccionado.nota_asignatura) if seleccionado.nota_asignatura else None,
            "nota_entrevista": float(seleccionado.nota_entrevista) if seleccionado.nota_entrevista else None,
            "puntaje_final": float(seleccionado.puntaje_final) if seleccionado.puntaje_final else None,
        }

    horas_s = conv.horas_semana or 1
    num_semanas = round((conv.horas_semestre or 0) / horas_s) if horas_s else 0

    ctx = {
        "fecha_hoy": datetime.now().strftime("%d de %B de %Y"),
        "convocatoria": {
            "periodo_academico": conv.periodo_academico,
            "horas_semana": conv.horas_semana,
            "horas_semestre": conv.horas_semestre,
            "sede": conv.sede,
            "descripcion_actividades": conv.descripcion_actividades,
            "promedio_minimo": float(conv.promedio_minimo) if conv.promedio_minimo else 3.5,
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
        },
        "monitor": monitor,
        "total_postulantes": total_posts,
        "num_semanas": num_semanas,
        "tipo_monitoria_label": TIPO_MONITORIA_LABEL.get(conv.tipo_monitoria.value, conv.tipo_monitoria.value),
    }

    pdf_bytes = _render_pdf("fo14.html", ctx)
    filename = f"FO-14_Monitor_{conv.asignatura.codigo if conv.asignatura else conv.id}_{conv.periodo_academico}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── FO-16 ─────────────────────────────────────────────────────────────────────

@router.get(
    "/fo16/{practica_id}",
    summary="Generar PDF MI-FOR-FO-16 — Justificación Prácticas Extramuros",
    response_class=Response,
)
def pdf_fo16(
    practica_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.jefe_programa, RolEnum.decano, RolEnum.admin, RolEnum.profesor)),
):
    pr = (
        db.query(Practica)
        .options(joinedload(Practica.asignatura), joinedload(Practica.profesor), joinedload(Practica.rutas))
        .filter(Practica.id == practica_id)
        .first()
    )
    if not pr:
        raise HTTPException(status_code=404, detail="Práctica no encontrada")

    rutas = sorted(pr.rutas, key=lambda r: r.orden)
    origen = next((r for r in rutas if r.tipo_punto == "origen"), rutas[0] if rutas else None)
    destino = next((r for r in rutas if r.tipo_punto == "destino"), rutas[-1] if rutas else None)
    intermedios = [r for r in rutas if r.tipo_punto == "intermedio"]

    n_dias = max(pr.duracion_dias or 1, 1)
    dias = []
    for d in range(1, min(n_dias, 7) + 1):
        fecha_dia = None
        if pr.fecha_inicio:
            from datetime import timedelta
            fecha_dia = pr.fecha_inicio + timedelta(days=d - 1)
        es_ultimo = d == n_dias
        sal = origen if d == 1 else (intermedios[d - 2] if len(intermedios) >= d - 1 else origen)
        lleg = destino if es_ultimo else (intermedios[d - 1] if len(intermedios) >= d else destino)
        dias.append({
            "numero": d,
            "fecha_str": fecha_dia.strftime("%A %d de %B de %Y") if fecha_dia else "",
            "origen_lugar": sal.lugar if sal else "—",
            "origen_municipio": sal.municipio if sal else "—",
            "destino_lugar": lleg.lugar if lleg else "—",
            "destino_municipio": lleg.municipio if lleg else "—",
            "destino_departamento": lleg.departamento if lleg else "—",
            "destino_vereda": lleg.vereda if lleg else None,
        })

    ctx = {
        "fecha_hoy": datetime.now().strftime("%d de %B de %Y"),
        "practica": {
            "id": pr.id,
            "nombre": pr.nombre_practica,
            "periodo_academico": pr.periodo_academico,
            "estado": pr.estado.value,
            "fecha_inicio_fmt": _fmt_date(pr.fecha_inicio),
            "fecha_fin_fmt": _fmt_date(pr.fecha_fin),
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
        "dias": dias,
    }

    pdf_bytes = _render_pdf("fo16.html", ctx)
    filename = f"FO-16_Practica{pr.id}_{pr.periodo_academico}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── FO-15 ─────────────────────────────────────────────────────────────────────

@router.get(
    "/fo15/{practica_id}",
    summary="Generar PDF MI-FOR-FO-15 — Lista de Participantes",
    response_class=Response,
)
def pdf_fo15(
    practica_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.jefe_programa, RolEnum.decano, RolEnum.admin, RolEnum.profesor)),
):
    from app.models.practica import FirmaConsentimiento, Viatico
    pr = (
        db.query(Practica)
        .options(
            joinedload(Practica.asignatura), joinedload(Practica.profesor),
            joinedload(Practica.rutas),
            joinedload(Practica.firmas).joinedload(FirmaConsentimiento.estudiante),
            joinedload(Practica.viaticos).joinedload(Viatico.tarifa),
        )
        .filter(Practica.id == practica_id)
        .first()
    )
    if not pr:
        raise HTTPException(status_code=404, detail="Práctica no encontrada")

    rutas = sorted(pr.rutas, key=lambda r: r.orden)
    destino = next((r for r in rutas if r.tipo_punto == "destino"), rutas[-1] if rutas else None)
    destino_lugar = f"{destino.lugar}, {destino.municipio}" if destino else "—"

    participantes = []
    for f in pr.firmas:
        e = f.estudiante
        if not e:
            continue
        participantes.append({
            "nombres": f"{e.nombres} {e.apellidos}",
            "codigo": e.codigo,
            "cedula": e.cedula,
            "fecha_firma": f.signed_at.strftime("%d/%m/%Y %H:%M") if f.signed_at else None,
        })

    viaticos = []
    for v in pr.viaticos:
        viaticos.append({
            "descripcion": v.tarifa.descripcion if v.tarifa else (v.descripcion or "—"),
            "valor_dia_fmt": _fmt_cop(v.tarifa.valor_dia if v.tarifa else 0),
            "num_dias": v.num_dias,
            "num_personas": v.num_personas,
            "total_fmt": _fmt_cop(v.valor_calculado),
        })

    total_v = sum(float(v.valor_calculado or 0) for v in pr.viaticos)

    ctx = {
        "fecha_hoy": datetime.now().strftime("%d de %B de %Y"),
        "practica": {
            "nombre": pr.nombre_practica,
            "periodo_academico": pr.periodo_academico,
            "estado": pr.estado.value,
            "fecha_inicio_fmt": _fmt_date(pr.fecha_inicio),
            "fecha_fin_fmt": _fmt_date(pr.fecha_fin),
            "num_alumnos": pr.num_alumnos,
            "firmas_obtenidas": pr.total_firmas_obtenidas,
            "firmas_requeridas": pr.total_firmas_requeridas,
            "quorum_alcanzado": pr.quorum_alcanzado,
        },
        "asignatura": {
            "nombre": pr.asignatura.nombre if pr.asignatura else "—",
            "codigo": pr.asignatura.codigo if pr.asignatura else "—",
            "programa": pr.asignatura.programa if pr.asignatura else "—",
        },
        "docente": {
            "nombres": f"{pr.profesor.nombres} {pr.profesor.apellidos}" if pr.profesor else "—",
        },
        "destino_lugar": destino_lugar,
        "participantes": participantes,
        "viaticos": viaticos,
        "total_viaticos_fmt": _fmt_cop(total_v),
    }

    pdf_bytes = _render_pdf("fo15.html", ctx)
    filename = f"FO-15_Participantes_Practica{pr.id}_{pr.periodo_academico}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
