"""
conftest.py — SIPAM USCO
Fixtures compartidos para toda la suite de pruebas.
Usa SQLite en memoria para aislar pruebas de la base de datos real.
"""
import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import Base, get_db
from app.models.user import User, RolEnum
from app.models.convocatoria import Convocatoria, Asignatura, EstadoConvocatoriaEnum, TipoMonitoriaEnum
from app.models.postulacion import Postulacion, EstadoPostulacionEnum
from app.models.practica import Practica, EstadoPracticaEnum, TarifaViatico, RutaPractica
from app.core.security import get_password_hash
from sqlalchemy import text

from sqlalchemy.pool import StaticPool

SQLALCHEMY_TEST_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

PASSWORD = "sipam2025"


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Crea todas las tablas en SQLite antes de correr los tests."""
    Base.metadata.create_all(bind=engine)
    # Crear tabla raw SQL sistema_config y activar testing_mode
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sistema_config (
                id INTEGER PRIMARY KEY DEFAULT 1,
                testing_mode BOOLEAN NOT NULL DEFAULT TRUE
            )"""))
        conn.execute(text("DELETE FROM sistema_config"))
        conn.execute(text("INSERT INTO sistema_config (id, testing_mode) VALUES (1, 1)"))
        conn.commit()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def session_db():
    """Sesión compartida para crear fixtures de toda la sesión."""
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def db():
    """Sesión por test individual."""
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client():
    """TestClient de FastAPI."""
    with TestClient(app) as c:
        yield c


# ── Usuarios de prueba (session scope — se crean una sola vez) ─────────────────

@pytest.fixture(scope="session")
def usuario_admin(session_db):
    u = User(
        codigo="TEST_ADMIN",
        nombres="Admin",
        apellidos="Test",
        email="admin.test@usco.edu.co",
        cedula="10000001",
        hashed_password=get_password_hash(PASSWORD),
        rol=RolEnum.admin,
        is_active=True,
    )
    session_db.add(u); session_db.commit(); session_db.refresh(u)
    return u


@pytest.fixture(scope="session")
def usuario_profesor(session_db):
    u = User(
        codigo="TEST_PROF",
        nombres="Profesor",
        apellidos="Test",
        email="prof.test@usco.edu.co",
        cedula="20000001",
        hashed_password=get_password_hash(PASSWORD),
        rol=RolEnum.profesor,
        is_active=True,
        programa="Ingeniería de Software",
        sede="Neiva",
        tipo_docente="planta",
        modalidad_docente="TCP",
    )
    session_db.add(u); session_db.commit(); session_db.refresh(u)
    return u


@pytest.fixture(scope="session")
def usuario_estudiante(session_db):
    u = User(
        codigo="TEST_EST",
        nombres="Estudiante",
        apellidos="Test",
        email="est.test@usco.edu.co",
        cedula="30000001",
        hashed_password=get_password_hash(PASSWORD),
        rol=RolEnum.estudiante,
        is_active=True,
        promedio=4.0,
        porcentaje_creditos=60.0,
        programa="Ingeniería de Software",
    )
    session_db.add(u); session_db.commit(); session_db.refresh(u)
    return u


@pytest.fixture(scope="session")
def usuario_jefe(session_db):
    u = User(
        codigo="TEST_JEFE",
        nombres="Jefe",
        apellidos="Programa",
        email="jefe.test@usco.edu.co",
        cedula="40000001",
        hashed_password=get_password_hash(PASSWORD),
        rol=RolEnum.jefe_programa,
        is_active=True,
        programa="Ingeniería de Software",
    )
    session_db.add(u); session_db.commit(); session_db.refresh(u)
    return u


@pytest.fixture(scope="session")
def usuario_decano(session_db):
    u = User(
        codigo="TEST_DECANO",
        nombres="Decano",
        apellidos="Test",
        email="decano.test@usco.edu.co",
        cedula="50000001",
        hashed_password=get_password_hash(PASSWORD),
        rol=RolEnum.decano,
        is_active=True,
    )
    session_db.add(u); session_db.commit(); session_db.refresh(u)
    return u


# ── Asignatura de prueba (session scope) ──────────────────────────────────────

@pytest.fixture(scope="session")
def asignatura(session_db, usuario_profesor):
    a = Asignatura(
        codigo="IS-101",
        nombre="Ingeniería de Software I",
        programa="Ingeniería de Software",
        facultad="Ingeniería",
        creditos=3,
        semestre=4,
        profesor_id=usuario_profesor.id,
        is_active=True,
        caracter_curso="teorico_practico",
        caracteristica_curso="especifico",
    )
    session_db.add(a); session_db.commit(); session_db.refresh(a)
    return a


# ── Convocatoria de prueba (session scope) ─────────────────────────────────────

@pytest.fixture(scope="session")
def convocatoria(session_db, asignatura, usuario_profesor):
    ahora = datetime.now(timezone.utc)
    c = Convocatoria(
        titulo="Monitor IS-101 2026-1",
        asignatura_id=asignatura.id,
        profesor_id=usuario_profesor.id,
        tipo_monitoria=TipoMonitoriaEnum.academica_cursos,
        estado=EstadoConvocatoriaEnum.abierta,
        periodo_academico="2026-1",
        fecha_inicio_postulacion=ahora - timedelta(days=1),
        fecha_fin_postulacion=ahora + timedelta(days=10),
        num_monitores_requeridos=1,
        horas_semana=8,
        horas_semestre=120,
        promedio_minimo=3.5,
        creditos_minimo_pct=30.0,
    )
    session_db.add(c); session_db.commit(); session_db.refresh(c)
    return c


# ── Helpers para tokens ────────────────────────────────────────────────────────

def get_token(client: TestClient, codigo: str, password: str = PASSWORD) -> str:
    r = client.post("/api/v1/auth/login", json={"codigo": codigo, "password": password})
    assert r.status_code == 200, f"Login falló: {r.text}"
    return r.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
