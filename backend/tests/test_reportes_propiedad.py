"""
Tests de control de propiedad en los datos de formularios FO-* (/api/v1/reportes).

Un profesor solo puede obtener los datos (con PII de docentes y estudiantes)
de prácticas/convocatorias de las que es titular; admin/jefe/decano sin cambios.

Usa su propia convocatoria (estado cerrada) y práctica para no interferir con
otros tests que comparten la BD de sesión.
"""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.models.convocatoria import Convocatoria, EstadoConvocatoriaEnum, TipoMonitoriaEnum
from app.models.practica import EstadoPracticaEnum, Practica
from app.models.user import RolEnum, User
from tests.conftest import PASSWORD, auth, get_token


@pytest.fixture(scope="function")
def profesor_ajeno(db):
    u = db.query(User).filter(User.codigo == "TEST_PROF_REP").first()
    if u:
        return u
    u = User(
        codigo="TEST_PROF_REP", nombres="Ajeno", apellidos="Profesor",
        email="profrep.test@usco.edu.co", cedula="20000020", rol=RolEnum.profesor,
        hashed_password=get_password_hash(PASSWORD), is_active=True,
    )
    db.add(u); db.commit(); db.refresh(u)
    return u


@pytest.fixture(scope="function")
def convocatoria_rep(db, asignatura, usuario_profesor):
    conv = db.query(Convocatoria).filter(Convocatoria.titulo == "Monitor REP test").first()
    if conv:
        return conv
    ahora = datetime.now(timezone.utc)
    conv = Convocatoria(
        titulo="Monitor REP test", asignatura_id=asignatura.id, profesor_id=usuario_profesor.id,
        tipo_monitoria=TipoMonitoriaEnum.academica_cursos, estado=EstadoConvocatoriaEnum.cerrada,
        periodo_academico="2099-9",
        fecha_inicio_postulacion=ahora - timedelta(days=20),
        fecha_fin_postulacion=ahora - timedelta(days=10),
        num_monitores_requeridos=1, horas_semana=8, horas_semestre=120,
        promedio_minimo=3.5, creditos_minimo_pct=30.0,
    )
    db.add(conv); db.commit(); db.refresh(conv)
    return conv


@pytest.fixture(scope="function")
def practica_rep(db, asignatura, usuario_profesor):
    p = db.query(Practica).filter(Practica.nombre_practica == "Práctica REP test").first()
    if p:
        return p
    ahora = datetime.now(timezone.utc)
    p = Practica(
        nombre_practica="Práctica REP test", asignatura_id=asignatura.id,
        profesor_id=usuario_profesor.id, estado=EstadoPracticaEnum.solicitada,
        periodo_academico="2026-1",
        fecha_inicio=ahora + timedelta(days=35), fecha_fin=ahora + timedelta(days=37),
        duracion_dias=3, num_alumnos=15, total_firmas_requeridas=10,
        total_firmas_obtenidas=0, quorum_alcanzado=False,
    )
    db.add(p); db.commit(); db.refresh(p)
    return p


FO_CONVOCATORIA = ["fo14", "fo46"]
FO_PRACTICA = ["fo15", "fo16", "fo05"]


@pytest.mark.parametrize("fo", FO_CONVOCATORIA)
def test_fo_convocatoria_profesor_ajeno_403(client: TestClient, profesor_ajeno, convocatoria_rep, fo):
    token = get_token(client, profesor_ajeno.codigo)
    r = client.get(f"/api/v1/reportes/{fo}/{convocatoria_rep.id}", headers=auth(token))
    assert r.status_code == 403


@pytest.mark.parametrize("fo", FO_PRACTICA)
def test_fo_practica_profesor_ajeno_403(client: TestClient, profesor_ajeno, practica_rep, fo):
    token = get_token(client, profesor_ajeno.codigo)
    r = client.get(f"/api/v1/reportes/{fo}/{practica_rep.id}", headers=auth(token))
    assert r.status_code == 403


@pytest.mark.parametrize("fo", FO_CONVOCATORIA)
def test_fo_convocatoria_titular_y_admin_200(client: TestClient, usuario_profesor, usuario_admin, convocatoria_rep, fo):
    for codigo in (usuario_profesor.codigo, usuario_admin.codigo):
        token = get_token(client, codigo)
        r = client.get(f"/api/v1/reportes/{fo}/{convocatoria_rep.id}", headers=auth(token))
        assert r.status_code == 200, r.text
        assert r.json()["docente"]["cedula"] == usuario_profesor.cedula


@pytest.mark.parametrize("fo", FO_PRACTICA)
def test_fo_practica_titular_y_admin_200(client: TestClient, usuario_profesor, usuario_admin, practica_rep, fo):
    for codigo in (usuario_profesor.codigo, usuario_admin.codigo):
        token = get_token(client, codigo)
        r = client.get(f"/api/v1/reportes/{fo}/{practica_rep.id}", headers=auth(token))
        assert r.status_code == 200, r.text


@pytest.mark.parametrize("ruta,fixture", [("fo46", "convocatoria_rep"), ("fo05", "practica_rep")])
def test_pdf_helpers_profesor_ajeno_403(client: TestClient, profesor_ajeno, request, ruta, fixture):
    obj = request.getfixturevalue(fixture)
    token = get_token(client, profesor_ajeno.codigo)
    r = client.get(f"/api/v1/pdf/{ruta}/{obj.id}", headers=auth(token))
    assert r.status_code == 403
