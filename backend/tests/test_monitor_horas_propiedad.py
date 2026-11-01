"""
Tests de control de propiedad en consulta/exportación de horas de monitores
(/api/v1/monitor/convocatoria/{id} y /exportar).

Un profesor solo puede ver horas de convocatorias de las que es titular;
jefe/decano sin cambios.
"""
import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.models.user import RolEnum, User
from tests.conftest import PASSWORD, auth, get_token

RUTAS = ["/api/v1/monitor/convocatoria/{id}", "/api/v1/monitor/convocatoria/{id}/exportar"]


@pytest.fixture(scope="function")
def profesor_ajeno(db):
    u = db.query(User).filter(User.codigo == "TEST_PROF_HORAS").first()
    if u:
        return u
    u = User(
        codigo="TEST_PROF_HORAS", nombres="Ajeno", apellidos="Horas",
        email="profhoras.test@usco.edu.co", cedula="20000030", rol=RolEnum.profesor,
        hashed_password=get_password_hash(PASSWORD), is_active=True,
    )
    db.add(u); db.commit(); db.refresh(u)
    return u


@pytest.mark.parametrize("ruta", RUTAS)
def test_profesor_ajeno_403(client: TestClient, profesor_ajeno, convocatoria, ruta):
    token = get_token(client, profesor_ajeno.codigo)
    r = client.get(ruta.format(id=convocatoria.id), headers=auth(token))
    assert r.status_code == 403


@pytest.mark.parametrize("ruta", RUTAS)
def test_profesor_titular_200(client: TestClient, usuario_profesor, convocatoria, ruta):
    token = get_token(client, usuario_profesor.codigo)
    r = client.get(ruta.format(id=convocatoria.id), headers=auth(token))
    assert r.status_code == 200


@pytest.mark.parametrize("ruta", RUTAS)
@pytest.mark.parametrize("rol", ["usuario_jefe", "usuario_decano"])
def test_jefe_decano_200(client: TestClient, request, convocatoria, ruta, rol):
    user = request.getfixturevalue(rol)
    token = get_token(client, user.codigo)
    r = client.get(ruta.format(id=convocatoria.id), headers=auth(token))
    assert r.status_code == 200


@pytest.mark.parametrize("ruta", RUTAS)
def test_convocatoria_inexistente_404(client: TestClient, usuario_profesor, ruta):
    token = get_token(client, usuario_profesor.codigo)
    r = client.get(ruta.format(id=999999), headers=auth(token))
    assert r.status_code == 404
