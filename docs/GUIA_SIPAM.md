# SIPAM-USCO — Usuarios y guía de arranque

## 1. Usuarios del sistema (BD de desarrollo)

**Contraseña universal de prueba: `sipam2025`** (todos los usuarios del seed).

| Código | Rol | Email | Nota |
|---|---|---|---|
| `Krlitoxprz` | admin | admin.sipam@usco.edu.co | Clave `Sasuke24` (= `ADMIN_PASSWORD` de `backend/.env`, gitignored) |
| `DECANO001` | decano | alvaro.guzman@usco.edu.co | |
| `JEFE001`–`JEFE005` | jefe_programa | carlos.ospina / luis.rubio / patricia.rodriguez / german.acosta / andres.morales @usco.edu.co | 5 jefes, uno por programa |
| `PROF001`–`PROF047` | profesor | ver CSV | 47 profesores reales (nombres del plan docente) |
| `2018…`, `2019…`, `2023…`, `2024…`, `2025…` | estudiante | ver CSV | 600 estudiantes (50 fijos + 550 generados) |

Totales: **654 usuarios** — 1 admin, 1 decano, 5 jefes, 47 profesores, 600 estudiantes.
Lista completa con código, nombre, email y rol: **`USUARIOS_SIPAM.csv`** (adjunto).

Acceso rápido recomendado para pruebas:

| Qué probar | Código | Clave |
|---|---|---|
| Administración total | `Krlitoxprz` | `Sasuke24` |
| Aprobación de presupuestos/convocatorias | `DECANO001` | `sipam2025` |
| Gestión de programa (postulantes, FO-15) | `JEFE001` | `sipam2025` |
| Convocatorias y evaluación | `PROF001` | `sipam2025` |
| Postularse / consentimiento FO-05 | `20231150092` | `sipam2025` |

## 2. Guía de arranque del proyecto

### Opción A — Local (recomendada para desarrollo)

**Requisitos:** Python 3.11+, Node 20+ (o nvm), SQLite (incluido).

```bash
git clone https://github.com/Krlitoxprz/SIPAM3.0.git && cd SIPAM3.0

# Backend
cd backend
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt pytest
uvicorn app.main:app --reload --port 8000            # API en http://localhost:8000
```

El arranque crea `sipam_usco.db`, las tablas y el admin automáticamente. Para datos de prueba:

```bash
python seed.py            # siembra usuarios/asignaturas/convocatorias (idempotente)
```

**Frontend** (otra terminal):

```bash
cd frontend
npm install
npm run dev             # http://localhost:5173 (proxies /api y /uploads → :8000)
```

**Servicio de IA** (opcional — solo si usas OCR/NLP/predictor):

```bash
cd ai_service
pip install -r requirements.txt
python app.py           # http://localhost:5001
```

### Opción B — Docker

```bash
docker compose -f docker-compose.dev.yml up --build   # backend :8000 + frontend :5173 + ai_service :5001
```

### Verificación rápida

- Swagger: `http://localhost:8000/api/v1/docs`
- Login de prueba en la UI: `PROF001` / `sipam2025`
- Tests backend: `cd backend && python -m pytest` (53 tests)
- Lint frontend: `cd frontend && npm run lint` · Build: `npm run build`

### Variables de entorno (`backend/.env`)

| Variable | Default | Para qué |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./sipam_usco.db` | Postgres en prod: `postgresql+psycopg2://user:pass@host/db` |
| `SECRET_KEY` | (vacío → aleatorio en dev) | Firma de JWT — **obligatorio en prod** |
| `ADMIN_PASSWORD` | `Sasuke24` (`.env` dev) | Clave del admin `Krlitoxprz` al primer arranque — **obligatorio en prod** |
| `AI_SERVICE_URL` | `http://localhost:5001` | En Docker: `http://ai_service:5001` |
| `IOT_API_KEY` | `iot_device_key_12345` | Clave de dispositivos GPS (header `X-API-Key`) |
| `UPLOAD_DIR` | `uploads` | Solo `uploads/fotos_perfil` es público |

### Rutas útiles

| Qué | Ruta |
|---|---|
| Docs API | `GET /api/v1/docs` |
| Subir punto GPS (dispositivo) | `POST /api/v1/iot/tracking/` + `X-API-Key` |
| Ver ruta en mapa | `GET /api/v1/iot/tracking/{practice_id}/map` |
| Descargar documento | `GET /api/v1/archivos/{id}` (con sesión) |
| PDFs | `GET /api/v1/pdf/{fo14|fo15|fo16|fo46|fo05|consentimiento}/...` |
