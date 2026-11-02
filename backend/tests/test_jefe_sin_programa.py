"""
Un jefe_programa sin programa asignado (User.programa NULL) no debe tener
alcance global: los guards de programa fallan cerrado (403).
"""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.models.practica import EstadoPracticaEnum, Practica
from app.models.user import RolEnum, User
from tests.conftest import PASSWORD, auth, get_token


@pytest.fixture(scope="function")
def jefe_sin_programa(db):
    u = db.query(User).filter(User.codigo == "TEST_JEFE_NULL").first()
    if u:
        return u
    u = User(
        codigo="TEST_JEFE_NULL", nombres="Jefe", apellidos="SinPrograma",
        email="jefenull.test@usco.edu.co", cedula="40000099", rol=RolEnum.jefe_programa,
        hashed_password=get_password_hash(PASSWORD), is_active=True, programa=None,
    )
    db.add(u); db.commit(); db.refresh(u)
    return u


@pytest.fixture(scope="function")
def practica_null(db, asignatura, usuario_profesor):
    p = db.query(Practica).filter(Practica.nombre_practica == "Práctica jefe NULL").first()
    if p:
        return p
    ahora = datetime.now(timezone.utc)
    p = Practica(
        nombre_practica="Práctica jefe NULL",
        asignatura_id=asignatura.id,
        profesor_id=usuario_profesor.id,
        estado=EstadoPracticaEnum.solicitada,
        periodo_academico="2099-8",
        fecha_inicio=ahora + timedelta(days=35),
        fecha_fin=ahora + timedelta(days=37),
        duracion_dias=3,
        num_alumnos=15,
        total_firmas_requeridas=10,
        total_firmas_obtenidas=10,
        quorum_alcanzado=True,
    )
    db.add(p); db.commit(); db.refresh(p)
    return p


def _token(client, user):
    token = get_token(client, user.codigo)
    client.cookies.clear()
    return auth(token)


def test_jefe_sin_programa_no_lee_ni_muta_convocatoria(client: TestClient, jefe_sin_programa, convocatoria):
    h = _token(client, jefe_sin_programa)
    assert client.get(f"/api/v1/convocatorias/{convocatoria.id}", headers=h).status_code == 403
    assert client.get("/api/v1/convocatorias/", headers=h).status_code == 403
    r = client.put(f"/api/v1/convocatorias/{convocatoria.id}", headers=h, json={"titulo": "hack"})
    assert r.status_code == 403
    assert client.get(f"/api/v1/monitor/convocatoria/{convocatoria.id}", headers=h).status_code == 403


def test_jefe_sin_programa_no_aprueba_practica(client: TestClient, jefe_sin_programa, practica_null, db):
    h = _token(client, jefe_sin_programa)
    assert client.patch(f"/api/v1/practicas/{practica_null.id}/aprobar", headers=h).status_code == 403
    assert client.get("/api/v1/practicas/", headers=h).status_code == 403
    db.refresh(practica_null)
    assert practica_null.estado == EstadoPracticaEnum.solicitada


def test_jefe_sin_programa_no_obtiene_consolidado(client: TestClient, jefe_sin_programa):
    h = _token(client, jefe_sin_programa)
    r = client.get("/api/v1/reportes/practicas-programa?programa=Ingeniería Civil", headers=h)
    assert r.status_code == 403


def test_jefe_sin_programa_no_matricula(client: TestClient, jefe_sin_programa, asignatura, usuario_estudiante):
    h = _token(client, jefe_sin_programa)
    r = client.post(
        f"/api/v1/convocatorias/asignaturas/{asignatura.id}/matricular", headers=h,
        json={"estudiante_id": usuario_estudiante.id, "periodo_academico": "2099-8"},
    )
    assert r.status_code == 403


def test_jefe_con_programa_sigue_accediendo(client: TestClient, usuario_jefe, convocatoria):
    h = _token(client, usuario_jefe)
    assert client.get(f"/api/v1/convocatorias/{convocatoria.id}", headers=h).status_code == 200


def test_crear_jefe_sin_programa_rechazado(client: TestClient, usuario_admin):
    h = _token(client, usuario_admin)
    r = client.post("/api/v1/auth/usuarios", headers=h, json={
        "codigo": "JEFENOPROG", "nombres": "J", "apellidos": "N",
        "email": "jefenoprog@usco.edu.co", "cedula": "40000098",
        "password": "sipam2025x", "rol": "jefe_programa", "programa": "  ",
    })
    assert r.status_code == 422


def test_jefe_sin_programa_no_lee_formularios(client: TestClient, jefe_sin_programa, practica_null, convocatoria):
    h = _token(client, jefe_sin_programa)
    assert client.get(f"/api/v1/reportes/fo15/{practica_null.id}", headers=h).status_code == 403
    assert client.get(f"/api/v1/reportes/fo14/{convocatoria.id}", headers=h).status_code == 403


def test_jefe_no_edita_asignatura_de_otro_programa(client: TestClient, usuario_jefe, db):
    from app.models.convocatoria import Asignatura
    a = db.query(Asignatura).filter(Asignatura.codigo == "IC-NULL-1").first()
    if not a:
        a = Asignatura(codigo="IC-NULL-1", nombre="Civil test", programa="Ingeniería Civil",
                       creditos=3, semestre=2, is_active=True)
        db.add(a); db.commit(); db.refresh(a)
    h = _token(client, usuario_jefe)
    body = {"codigo": a.codigo, "nombre": "hack", "creditos": 3, "programa": "Ingeniería Civil", "semestre": 2}
    assert client.patch(f"/api/v1/convocatorias/asignaturas/{a.id}", headers=h, json=body).status_code == 403
    body["codigo"] = "IC-NULL-2"
    assert client.post("/api/v1/convocatorias/asignaturas/", headers=h, json=body).status_code == 403
