"""
Tests de alcance del profesor en endpoints de lectura de monitor:
- GET /api/v1/monitor/convocatoria/{conv_id}
- GET /api/v1/monitor/convocatoria/{conv_id}/exportar
- GET /api/v1/monitor/postulaciones/{post_id}/evaluacion

Solo el profesor titular de la convocatoria (o jefe/decano) puede consultar.
Usa datos propios (convocatoria finalizada) para no interferir con otros tests.
"""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.models.convocatoria import Asignatura, Convocatoria, EstadoConvocatoriaEnum, TipoMonitoriaEnum
from app.models.evaluacion_monitor import EvaluacionMonitor
from app.models.monitor import HorasMonitor
from app.models.postulacion import EstadoPostulacionEnum, Postulacion
from app.models.user import RolEnum, User
from tests.conftest import PASSWORD, auth, get_token


def _get_or_create_user(db, codigo, **kwargs):
    u = db.query(User).filter(User.codigo == codigo).first()
    if u:
        return u
    u = User(codigo=codigo, hashed_password=get_password_hash(PASSWORD), is_active=True, **kwargs)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture(scope="function")
def profesor_ajeno(db):
    return _get_or_create_user(
        db, "TEST_PROF_MON2",
        nombres="Ajeno", apellidos="Profesor", email="profmon2.test@usco.edu.co",
        cedula="20000020", rol=RolEnum.profesor,
    )


@pytest.fixture(scope="function")
def datos_monitor(db, usuario_profesor):
    """Convocatoria finalizada (titular: usuario_profesor) con monitor, horas y evaluación."""
    conv = db.query(Convocatoria).filter(Convocatoria.titulo == "Monitor MONPERM test").first()
    if not conv:
        asig = db.query(Asignatura).filter(Asignatura.codigo == "MP-101").first()
        if not asig:
            asig = Asignatura(
                codigo="MP-101", nombre="Monitor Permisos Test", programa="Ingeniería de Software",
                facultad="Ingeniería", creditos=3, semestre=4, profesor_id=usuario_profesor.id,
                is_active=True, caracter_curso="teorico_practico", caracteristica_curso="especifico",
            )
            db.add(asig)
            db.commit()
            db.refresh(asig)
        ahora = datetime.now(timezone.utc)
        conv = Convocatoria(
            titulo="Monitor MONPERM test", asignatura_id=asig.id, profesor_id=usuario_profesor.id,
            tipo_monitoria=TipoMonitoriaEnum.academica_cursos, estado=EstadoConvocatoriaEnum.finalizada,
            periodo_academico="2026-1",
            fecha_inicio_postulacion=ahora - timedelta(days=40),
            fecha_fin_postulacion=ahora - timedelta(days=30),
            num_monitores_requeridos=1, horas_semana=8, horas_semestre=120,
            promedio_minimo=3.5, creditos_minimo_pct=30.0,
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)

    est = _get_or_create_user(
        db, "TEST_EST_MONPERM",
        nombres="Est", apellidos="Monitor", email="estmonperm.test@usco.edu.co",
        cedula="30000020", rol=RolEnum.estudiante, promedio=4.0, porcentaje_creditos=60.0,
        programa="Ingeniería de Software",
    )
    post = db.query(Postulacion).filter(
        Postulacion.convocatoria_id == conv.id, Postulacion.estudiante_id == est.id
    ).first()
    if not post:
        post = Postulacion(
            convocatoria_id=conv.id, estudiante_id=est.id,
            estado=EstadoPostulacionEnum.seleccionado, promedio_estudiante=4.0,
            carta_motivacion="x" * 40,
        )
        db.add(post)
        db.commit()
        db.refresh(post)
        db.add(HorasMonitor(postulacion_id=post.id, semana=1, horas=4, descripcion="Tutoría"))
        db.add(EvaluacionMonitor(postulacion_id=post.id, evaluado_por_id=usuario_profesor.id, nota_desempeno=4.5))
        db.commit()
    return conv, post


def _urls(conv, post):
    return [
        f"/api/v1/monitor/convocatoria/{conv.id}",
        f"/api/v1/monitor/convocatoria/{conv.id}/exportar",
        f"/api/v1/monitor/postulaciones/{post.id}/evaluacion",
    ]


def test_profesor_titular_accede(client: TestClient, datos_monitor):
    token = get_token(client, "TEST_PROF")
    for url in _urls(*datos_monitor):
        r = client.get(url, headers=auth(token))
        assert r.status_code == 200, url
    r = client.get(f"/api/v1/monitor/convocatoria/{datos_monitor[0].id}", headers=auth(token))
    assert r.json()[0]["total_horas"] == 4


def test_profesor_ajeno_403(client: TestClient, profesor_ajeno, datos_monitor):
    token = get_token(client, "TEST_PROF_MON2")
    for url in _urls(*datos_monitor):
        r = client.get(url, headers=auth(token))
        assert r.status_code == 403, url


def test_jefe_accede(client: TestClient, usuario_jefe, datos_monitor):
    token = get_token(client, "TEST_JEFE")
    for url in _urls(*datos_monitor):
        r = client.get(url, headers=auth(token))
        assert r.status_code == 200, url


def test_profesor_convocatoria_inexistente_404(client: TestClient, usuario_profesor):
    token = get_token(client, "TEST_PROF")
    r = client.get("/api/v1/monitor/convocatoria/999999", headers=auth(token))
    assert r.status_code == 404
