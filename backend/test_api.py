"""Script de prueba rapida de los endpoints del Paso 4."""
import httpx

BASE = "http://localhost:8000/api/v1"


def run():
    print("=" * 60)
    print("  SIPAM-USCO -- Prueba de Endpoints API")
    print("=" * 60)

    print("\n[1] Health check")
    r = httpx.get(f"{BASE}/health")
    print(f"  GET /health => {r.status_code} {r.json()}")

    print("\n[2] Login JEFE001")
    r = httpx.post(f"{BASE}/auth/login", json={"codigo": "JEFE001", "password": "sipam2025"})
    print(f"  POST /auth/login => {r.status_code}")
    jefe_token = r.json().get("access_token", "")
    u = r.json().get("user", {})
    print(f"  Usuario: {u.get('nombres')} {u.get('apellidos')} | Rol: {u.get('rol')}")

    print("\n[3] Login PROF001")
    r = httpx.post(f"{BASE}/auth/login", json={"codigo": "PROF001", "password": "sipam2025"})
    print(f"  POST /auth/login => {r.status_code}")
    prof_token = r.json().get("access_token", "")

    print("\n[4] GET /me (profesor)")
    r = httpx.get(f"{BASE}/auth/me", headers={"Authorization": f"Bearer {prof_token}"})
    print(f"  GET /auth/me => {r.status_code} | {r.json().get('nombres')} | {r.json().get('rol')}")

    print("\n[5] Listar convocatorias (jefe)")
    r = httpx.get(f"{BASE}/convocatorias/", headers={"Authorization": f"Bearer {jefe_token}"})
    convs = r.json()
    print(f"  GET /convocatorias => {r.status_code} ({len(convs)} convocatorias)")
    for c in convs:
        print(f"    [{c['estado']:15}] {c['titulo']} | {c['total_postulantes']} postulantes")

    print("\n[6] Validacion academica mock (jefe consulta a PROF001)")
    r = httpx.get(
        f"{BASE}/auth/validar-academica/PROF001",
        headers={"Authorization": f"Bearer {jefe_token}"},
    )
    print(f"  GET /validar-academica/PROF001 => {r.status_code}")
    print(f"  Resultado: {r.json()}")

    print("\n[7] Resultados de seleccion (convocatoria en_evaluacion = id 3)")
    r = httpx.get(
        f"{BASE}/seleccion/convocatorias/3/resultados",
        headers={"Authorization": f"Bearer {jefe_token}"},
    )
    print(f"  Status: {r.status_code} | Body[:200]: {r.text[:200]}")
    if r.status_code == 200:
        resultados = r.json()
        print(f"  ({len(resultados)} con puntaje calculado)")
        for res in resultados[:5]:
            print(
                f"    Puesto {res['puesto']}: {res['estudiante_nombre']} "
                f"| Puntaje={res['puntaje_final']} | {res['estado']}"
            )

    print("\n[8] Credenciales incorrectas")
    r = httpx.post(f"{BASE}/auth/login", json={"codigo": "JEFE001", "password": "wrong"})
    print(f"  POST /auth/login (wrong pass) => {r.status_code} {r.json().get('detail')}")

    print("\n[9] Acceso sin token")
    r = httpx.get(f"{BASE}/convocatorias/")
    print(f"  GET /convocatorias (sin token) => {r.status_code}")

    print("\n" + "=" * 60)
    print("  PRUEBAS COMPLETADAS")
    print("=" * 60)


if __name__ == "__main__":
    run()
