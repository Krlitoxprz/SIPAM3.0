import httpx

BASE = "http://localhost:8000/api/v1"

def ok(label, r, expected=200):
    status = "[ OK]" if r.status_code == expected else "[FAIL]"
    print(f"  {status} {label} => {r.status_code}")
    if r.status_code != expected:
        print(f"         {r.text[:200]}")
    return r

token_jefe = httpx.post(f"{BASE}/auth/login", json={"codigo": "JEFE001", "password": "sipam2025"}).json()["access_token"]
token_prof = httpx.post(f"{BASE}/auth/login", json={"codigo": "PROF001", "password": "sipam2025"}).json()["access_token"]
h_jefe = {"Authorization": f"Bearer {token_jefe}"}
h_prof = {"Authorization": f"Bearer {token_prof}"}

print("\n[USUARIOS]")

r = ok("GET /usuarios (jefe)", httpx.get(f"{BASE}/auth/usuarios", headers=h_jefe))
total = len(r.json())
print(f"         {total} usuarios encontrados")

r2 = ok("GET /usuarios?rol=estudiante", httpx.get(f"{BASE}/auth/usuarios", params={"rol": "estudiante"}, headers=h_jefe))
print(f"         {len(r2.json())} estudiantes")

r3 = ok("GET /usuarios?q=Valentina", httpx.get(f"{BASE}/auth/usuarios", params={"q": "Valentina"}, headers=h_jefe))
print(f"         {len(r3.json())} resultado(s)")

ok("GET /usuarios (profesor) => 403", httpx.get(f"{BASE}/auth/usuarios", headers=h_prof), 403)

r4 = ok("POST /usuarios (crear)", httpx.post(f"{BASE}/auth/usuarios", json={
    "codigo": "TESTX01", "nombres": "Test", "apellidos": "Prueba",
    "email": "testx01@usco.edu.co", "cedula": "88888888",
    "password": "test1234", "rol": "estudiante",
    "promedio": 4.2, "porcentaje_creditos": 65.0, "programa": "Ing. Sistemas",
}), 201)
uid = r4.json().get("id")

r5 = ok("PATCH toggle-activo => inactivo", httpx.patch(f"{BASE}/auth/usuarios/{uid}/toggle-activo", headers=h_jefe))
activo = r5.json().get("is_active")
print(f"         is_active={activo}")

r6 = ok("PATCH toggle-activo => activo", httpx.patch(f"{BASE}/auth/usuarios/{uid}/toggle-activo", headers=h_jefe))
print(f"         is_active={r6.json().get('is_active')}")

# No puede desactivar su propia cuenta
import app.models.user, app.models.convocatoria, app.models.postulacion, app.models.practica, app.models.presupuesto
from app.db.database import SessionLocal
from app.models.user import User
db = SessionLocal()
jefe = db.query(User).filter(User.codigo == "JEFE001").first()
db.close()
ok("PATCH self-deactivate => 400", httpx.patch(f"{BASE}/auth/usuarios/{jefe.id}/toggle-activo", headers=h_jefe), 400)

print("\n[LIMPIEZA]")
db2 = SessionLocal()
db2.query(User).filter(User.codigo == "TESTX01").delete()
db2.commit()
db2.close()
print("  [ OK] Usuario TEST999 eliminado")
print("\n  USUARIOS OK\n")
