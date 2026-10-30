# SIPAM-USCO — Guía para levantar el proyecto y probarlo

## 1. Levantar el proyecto (máquina nueva)

**Requisitos:** Python 3.11+, Node 20+.

```bash
git clone https://github.com/Krlitoxprz/SIPAM3.0.git && cd SIPAM3.0

# ── Backend ──────────────────────────────────────────────
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt pytest

# .env mínimo para dev (el admin toma esta clave al PRIMER arranque)
printf 'ADMIN_PASSWORD=Sasuke24\nSECRET_KEY=dev-cambia-esto\n' > .env

uvicorn app.main:app --reload --port 8000          # API → http://localhost:8000
python seed.py                                     # datos de prueba (idempotente)

# ── Frontend (otra terminal) ─────────────────────────────
cd frontend && npm install && npm run dev          # → http://localhost:5173
```

Entra a `http://localhost:5173`. En la pantalla de login, la tarjeta **"Acceso rápido"** (solo en modo dev) rellena credenciales con un clic — usa esos botones.

## 2. Credenciales

| Rol | Código | Clave | Quién |
|---|---|---|---|
| admin | `Krlitoxprz` | `Sasuke24` | Superusuario |
| decano | `DECANO001` | `sipam2025` | Álvaro Guzmán |
| jefe_programa | `JEFE001`–`JEFE005` | `sipam2025` | 1 por programa (ver abajo) |
| profesor | `PROF001`–`PROF047` | `sipam2025` | 47 profesores |
| estudiante | códigos por cohorte | `sipam2025` | 600 estudiantes |

Jefes por programa: `JEFE001` Agroindustrial · `JEFE002` Agrícola · `JEFE003` Civil · `JEFE004` Petróleos · `JEFE005` Software.

## 3. Usuarios para cada flujo de prueba

### A. Crear monitorías (convocatorias)

| Paso | Usuario |
|---|---|
| Crear convocatoria | **`JEFE001`** (o `Krlitoxprz`) — `POST /convocatorias` solo acepta `jefe_programa`/`admin` |
| Postularse (subir docs) | **`20231150092`** (Mateo, estudiante) o cualquier código de estudiante del CSV |
| Evaluar postulantes | **`PROF001`** — profesor titular de la convocatoria; ve chips de descarga de Cédula/RUT/Cert. Bancario |
| Aprobar/seleccionar | `JEFE001` / `DECANO001` |

### B. Crear prácticas extramuros

| Paso | Usuario |
|---|---|
| Crear práctica + rutas | **`PROF001`** — tiene la asignatura `IAGR-107` (Procesos industriales cárnicos) con 30 estudiantes matriculados |
| Solicitar aprobación | `PROF001` (la práctica debe tener ≥1 ruta) |
| Aprobar por programa | **`JEFE001`** (Ingeniería Agroindustrial) |
| Aprobar facultad | `DECANO001` |
| Transporte/viáticos | `Krlitoxprz` |

### C. Firma del consentimiento (FO-05) — estudiante

La firma exige: práctica en estado `solicitada`/`pendiente_quorum`/aprobada*, **fecha_fin futura**, estudiante **matriculado en la asignatura**, y ventana de firma (10–5 días antes del inicio) **o modo de prueba activo**.

| Paso | Usuario |
|---|---|
| Activar modo de prueba (quita las restricciones de fechas/quórum) | **`Krlitoxprz`** → `PATCH /api/v1/sistema/testing-mode {"enabled": true}` o desde el panel de admin |
| Crear práctica con fechas futuras | `PROF001` (asignatura `IAGR-107`) |
| **Firmar el consentimiento** | **`20231150092`** (Mateo) — matriculado en IAGR-107. Otros firmables: `20191150166` Andrea, `20191150005` Ángela, `20231150033` Sara, `20191150277` Fabián, `20201150502` Camila, `20231150505` Felipe, `20251150507` Harold (30 en total) |

> La `practicas.id=1` del seed ya venció (`fecha_fin` 2026-05-14) — **no se puede firmar aunque el modo prueba esté activo**. Crea una nueva con `PROF001` poniendo inicio/fin dentro de ~1 mes.

## 4. Flujo recomendado de punta a punta (15 min)

1. Entra como `Krlitoxprz`/`Sasuke24` → activa **modo de prueba**.
2. Entra como `JEFE001`/`sipam2025` → crea una **convocatoria** de monitoría.
3. Entra como `20231150092`/`sipam2025` → postúlate subiendo 3 PDFs.
4. Entra como `PROF001`/`sipam2025` → revisa/descarga los docs del postulante.
5. Como `PROF001` → crea una **práctica** sobre `IAGR-107` con fechas futuras + una ruta → **Solicitar**.
6. Como `20231150092` → en la práctica pulsa **Firmar consentimiento** (registra IP + timestamp).
7. Como `JEFE001` → aprueba; como `DECANO001` → aprueba facultad.
8. Descarga los PDFs institucionales (FO-05, FO-14, FO-46…) — todos llevan QR + hash de verificación.

## 5. Utiles

- Swagger: `http://localhost:8000/api/v1/docs`
- Tests backend: `cd backend && python -m pytest` (53 tests)
- Login por API: `POST /api/v1/auth/login` con JSON `{"codigo": "...", "password": "..."}`
- Ojo con el anti-fuerza-bruta: **5 fallos por cuenta+IP en 15 min → 429** (la UI lo muestra como "credenciales incorrectos").
