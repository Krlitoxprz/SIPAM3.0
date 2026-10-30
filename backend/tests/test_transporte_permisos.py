"""
Control de acceso en endpoints de transporte que operan sobre una práctica.

- POST /transporte/rutas/{id}/calcular-distancias: solo docente dueño,
  jefe del programa, decano o admin.
- GET /transporte/costos/{id}: mismos permisos y sin persistir distancias.
"""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.models.practica import EstadoPracticaEnum, Practica, RutaPractica
from app.models.user import RolEnum, User
from tests.conftest import PASSWORD, auth, get_token


@pytest.fixture(autouse=True)
def _sin_ors(monkeypatch):
    async def _none(*args, **kwargs):
        return None
    monkeypatch.setattr("app.api.v1.endpoints.transporte.calcular_ruta", _none)


@pytest.fixture(scope="function")
def profesor_ajeno_tr(db):
    u = db.query(User).filter(User.codigo == "TEST_PROF_TR").first()
    if u:
        return u
    u = User(
        codigo="TEST_PROF_TR", nombres="Ajeno", apellidos="Transporte",
        email="proftr.test@usco.edu.co", cedula="20000030", rol=RolEnum.profesor,
        hashed_password=get_password_hash(PASSWORD), is_active=True,
    )
    db.add(u); db.commit(); db.refresh(u)
    return u


@pytest.fixture(scope="function")
def jefe_otro_programa(db):
    u = db.query(User).filter(User.codigo == "TEST_JEFE_TR").first()
    if u:
        return u
    u = User(
        codigo="TEST_JEFE_TR", nombres="Jefe", apellidos="Otro",
        email="jefetr.test@usco.edu.co", cedula="40000030", rol=RolEnum.jefe_programa,
        hashed_password=get_password_hash(PASSWORD), is_active=True,
        programa="Medicina",
    )
    db.add(u); db.commit(); db.refresh(u)
    return u


@pytest.fixture(scope="function")
def practica_tr(db, asignatura, usuario_profesor):
    p = db.query(Practica).filter(Practica.nombre_practica == "Práctica TR test").first()
    if not p:
        ahora = datetime.now(timezone.utc)
        p = Practica(
            nombre_practica="Práctica TR test", asignatura_id=asignatura.id,
            profesor_id=usuario_profesor.id, estado=EstadoPracticaEnum.solicitada,
            periodo_academico="2026-1",
            fecha_inicio=ahora + timedelta(days=35), fecha_fin=ahora + timedelta(days=37),
            duracion_dias=3, num_alumnos=15,
        )
        db.add(p); db.commit(); db.refresh(p)
        db.add_all([
            RutaPractica(practica_id=p.id, orden=1, tipo_punto="origen",
                         lugar="Neiva", municipio="Neiva", departamento="Huila"),
            RutaPractica(practica_id=p.id, orden=2, tipo_punto="destino",
                         lugar="Pitalito", municipio="Pitalito", departamento="Huila"),
        ])
        db.commit()
    for r in db.query(RutaPractica).filter(RutaPractica.practica_id == p.id):
        r.distancia_km = None
    db.commit()
    return p


def _distancias(db, practica_id):
    db.expire_all()
    return [
        r.distancia_km
        for r in db.query(RutaPractica)
        .filter(RutaPractica.practica_id == practica_id)
        .order_by(RutaPractica.orden)
    ]


def _post(client, user, pid):
    token = get_token(client, user.codigo)
    return client.post(f"/api/v1/transporte/rutas/{pid}/calcular-distancias", headers=auth(token))


def _get_costos(client, user, pid):
    token = get_token(client, user.codigo)
    return client.get(f"/api/v1/transporte/costos/{pid}", headers=auth(token))


@pytest.mark.parametrize("fixture", ["usuario_estudiante", "profesor_ajeno_tr", "jefe_otro_programa"])
def test_calcular_distancias_sin_permiso_403(client: TestClient, db, practica_tr, request, fixture):
    user = request.getfixturevalue(fixture)
    r = _post(client, user, practica_tr.id)
    assert r.status_code == 403
    assert _distancias(db, practica_tr.id) == [None, None]


@pytest.mark.parametrize("fixture", ["usuario_profesor", "usuario_jefe", "usuario_decano", "usuario_admin"])
def test_calcular_distancias_autorizado(client: TestClient, db, practica_tr, request, fixture):
    user = request.getfixturevalue(fixture)
    r = _post(client, user, practica_tr.id)
    assert r.status_code == 200, r.text
    assert r.json()["rutas_actualizadas"] == 1
    assert _distancias(db, practica_tr.id)[1] is not None


@pytest.mark.parametrize("fixture", ["usuario_estudiante", "profesor_ajeno_tr", "jefe_otro_programa"])
def test_costos_sin_permiso_403(client: TestClient, practica_tr, request, fixture):
    user = request.getfixturevalue(fixture)
    assert _get_costos(client, user, practica_tr.id).status_code == 403


def test_costos_no_persiste_distancias(client: TestClient, db, practica_tr, usuario_profesor):
    r = _get_costos(client, usuario_profesor, practica_tr.id)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["parametros_calculo"]["km_total_ida"] > 0
    assert body["distancias_auto"]
    assert _distancias(db, practica_tr.id) == [None, None]
