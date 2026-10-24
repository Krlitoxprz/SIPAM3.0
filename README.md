# SIPAM-USCO — v3.0
**Sistema Integrado de Prácticas Académicas y Monitorías**  
Facultad de Ingeniería · Universidad Surcolombiana · Trabajo de Grado

---

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend API | FastAPI (Python 3.13) |
| Base de Datos | PostgreSQL 15 (dev y prod) vía SQLAlchemy ORM + Alembic |
| Frontend | React 19 + TypeScript (Vite) |
| Estilos | Tailwind CSS v4 |
| Autenticación | JWT (PyJWT) + cookies HttpOnly |
| IA Service | Flask + TensorFlow/Keras (CNN OCR + Transformer NLP) |
| IoT | ESP32 GPS Tracking + Python Simulator |
| PDF Generation | WeasyPrint (backend) |

---

## Estructura del Proyecto

```
SIPAM3.0/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Endpoints REST
│   │   │   ├── endpoints/   # auth, convocatorias, postulaciones, archivos (seguro), etc.
│   │   │   └── router.py    # Router principal
│   │   ├── core/            # Config y seguridad (JWT con PyJWT, bcrypt)
│   │   ├── db/              # SQLAlchemy engine y sesiones
│   │   ├── models/          # Modelos ORM (incluye ArchivoAdjunto, AuditLog)
│   │   ├── schemas/         # Esquemas Pydantic
│   │   └── utils/           # file_security.py (validación magic bytes, UUID)
│   ├── alembic/             # Migraciones de base de datos
│   ├── uploads/             # Archivos subidos (NO sirven como estáticos)
│   ├── requirements.txt
│   ├── .env.example
│   └── seed.py             # Seeder (solo corre en ENVIRONMENT=development)
├── frontend/
│   ├── src/
│   │   ├── components/      # Header, Sidebar, ProtectedRoute, NotificacionesBell
│   │   ├── context/         # AuthContext (JWT global - actualizar a cookies HttpOnly)
│   │   ├── hooks/           # useAuth
│   │   ├── pages/           # Login, Dashboard, Convocatorias, Presupuesto, etc.
│   │   ├── services/        # Axios + endpoints
│   │   └── types/           # TypeScript interfaces
│   └── vite.config.ts
├── ai_service/
│   ├── app.py               # Flask API para CNN OCR y Transformer NLP
│   ├── cnn_ocr.py           # Modelo CNN para reconocimiento de caracteres
│   ├── transformer_nlp.py   # Modelo Transformer para análisis de texto
│   ├── models/saved/        # Modelos entrenados
│   └── requirements_ai.txt
├── iot/
│   ├── gps_simulator.py     # Simulador Python de GPS
│   └── gps_tracker_esp32.ino  # Código ESP32 para tracking GPS real
├── docs/
│   ├── latex/               # Documentación LaTeX
│   ├── diagrams/            # Diagramas PlantUML
│   ├── Servidor_Final/      # Documentación del servidor
│   ├── Monitoria/           # PDFs de monitorías por programa
│   ├── Practicas/           # PDFs de prácticas extramuros
│   ├── ENDPOINTS_REPORTE.md
│   ├── HISTORIAS_USUARIO.md
│   ├── PRUEBAS.md
│   └── TASKS_IMMEDIATE.md
├── docker-compose.yml           # Compose para producción
├── docker-compose.dev.yml       # Compose para desarrollo (PostgreSQL local)
├── deploy.sh
└── README.md
```

---

## Seguridad Implementada

### ✅ Correcciones de Seguridad Críticas

1. **Archivos protegidos con JWT y RBAC**
   - Endpoint `/api/v1/archivos/{archivo_id}` requiere autenticación
   - Validación de permisos: estudiantes solo ven sus archivos
   - Roles especiales (admin, jefe_programa, decano) tienen acceso ampliado
   - Archivos renombrados con UUID para evitar path traversal

2. **Librerías criptográficas actualizadas**
   - Reemplazado `python-jose` (abandonado) por `PyJWT` (mantenido activamente)
   - Reemplazado `passlib` por `bcrypt` directo (compatible Python 3.13)
   - Tokens JWT con expiración reducida a 30 minutos

3. **Validación de archivos**
   - Magic bytes validados (no confiar solo en extensión)
   - Límite de tamaño reducido a 5 MB
   - Nombres seguros con UUID en disco

4. **Seeder seguro**
   - Solo se ejecuta si `ENVIRONMENT=development`
   - Nunca corre en producción automáticamente

5. **Volúmenes persistentes en Docker**
   - PostgreSQL: `postgres_data` (named volume)
   - Uploads: `uploads_data` (named volume)
   - Modelos IA: `ai_models` (named volume)

---

## Iniciar en Desarrollo

### Opción 1: PostgreSQL en Docker (Recomendado)

```powershell
# Levantar todos los servicios con PostgreSQL local
docker compose -f docker-compose.dev.yml up -d

# Backend estará en http://localhost:8000
# Frontend estará en http://localhost:5173
# AI Service estará en http://localhost:5001
```

### Opción 2: Local sin Docker

#### Terminal 1 — Backend (FastAPI)
```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
# Crear .env desde .env.example
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# API disponible en: http://localhost:8000
# Swagger UI:        http://localhost:8000/api/docs
```

#### Terminal 2 — Frontend (React)
```powershell
cd frontend
npm install
npm run dev
# App disponible en: http://localhost:5173
```

#### Terminal 3 — AI Service (Opcional)
```powershell
cd ai_service
python -m venv venv
venv\Scripts\activate
pip install -r requirements_ai.txt
python app.py
# AI Service disponible en: http://localhost:5001
```

---

## Migraciones de Base de Datos (Alembic)

```powershell
cd backend

# Crear nueva migración
python -m alembic revision --autogenerate -m "descripcion_del_cambio"

# Aplicar migraciones
python -m alembic upgrade head

# Revertir última migración
python -m alembic downgrade -1
```

---

## Variables de Entorno (backend/.env)

```bash
# Seguridad
SECRET_KEY=cambia-esta-clave-en-produccion-min-32-caracteres
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
DEBUG=false
ENVIRONMENT=production

# Base de datos
DATABASE_URL=postgresql://user:pass@localhost:5432/sipam_db

# Archivos
UPLOAD_DIR=uploads
MAX_FILE_SIZE_MB=5

# Cookies (HTTPS en producción)
COOKIE_SECURE=true
COOKIE_SAMESITE=lax
COOKIE_DOMAIN=.usco.edu.co
```

---

## Roles de Usuario

| Rol | Código de Prueba | Acceso |
|-----|-----------------|--------|
| Estudiante | `2020115001` | Convocatorias, postulaciones, firma consentimiento |
| Profesor | `PROF001` | Evaluación monitores, rutas de práctica |
| Jefe de Programa | `JEFE001` | Gestión total, presupuesto, actas |
| Decano | `DECANO001` | Aprobación final, imprimir actas |
| Admin | `Krlitoxprz` | Superusuario, configuración sistema |

> **⚠️ Importante:** Los datos de prueba (códigos y contraseña `sipam2025`) solo se crean en desarrollo. En producción, el admin debe crearse vía variables de entorno.

---

## Servicios del Sistema

### 🤖 IA Service (CNN + Transformer)
- **CNN OCR:** Reconocimiento de caracteres en documentos escaneados
- **Transformer NLP:** Análisis de textos de postulaciones y cartas motivación
- **Endpoints:**
  - `POST /ocr/extract` - Extraer texto de imágenes
  - `POST /nlp/analyze` - Análisis de sentimiento y keywords

### 📍 IoT GPS Tracking
- **ESP32 Tracker:** Tracking GPS en tiempo real de estudiantes en prácticas
- **Simulador Python:** Pruebas sin hardware real
- **Endpoints:**
  - `POST /iot/gps/update` - Recibir coordenadas GPS
  - `GET /iot/locations/{practica_id}` - Ver ruta de práctica

### 📄 PDF Generation (Backend)
- **WeasyPrint:** Generación de PDFs en el servidor (no en cliente)
- **Formatos:**
  - MI-FOR-FO-14 (Requerimiento Monitores)
  - MI-FOR-FO-15 (Prácticas Extramuros)
  - AP-INF-FO-05 (Solicitud Desplazamiento Vial)

---

## Auditoría y Trazabilidad

### Tabla AuditLog (Inmutable)
Registra todas las acciones críticas:
- Firmas de consentimiento (hash SHA-256 del documento)
- Aprobaciones presupuestales
- Cambios de estado en postulaciones
- IP origen, user agent, fecha/hora UTC

---

## Despliegue en Producción

```bash
# Construir y levantar servicios
docker compose --env-file .env.production up -d

# Ejecutar migraciones
docker compose exec backend python -m alembic upgrade head

# Crear admin inicial (si no existe)
docker compose exec backend python -c "from app.db.database import init_db; init_db()"
```

---

## Plan de Desarrollo

- [x] ✅ Scaffolding y estructura base
- [x] ✅ Modelos de base de datos (SQLAlchemy)
- [x] ✅ Seeders con datos de prueba (solo desarrollo)
- [x] ✅ Endpoints API — Flujo completo de Monitorías
- [x] ✅ Endpoints API — Flujo completo de Prácticas
- [x] ✅ Sistema de archivos seguro (UUID, RBAC)
- [x] ✅ Integración Alembic para migraciones
- [x] ✅ PostgreSQL en Docker para desarrollo
- [x] ✅ Tabla de auditoría inmutable
- [ ] 🔄 Cookies HttpOnly para JWT (frontend)
- [ ] 🔄 RBAC estricto en todos los endpoints
- [ ] 🔄 GitHub Actions para CI/CD
- [ ] 🔄 Implementación completa de Refresh Tokens

---

## Licencia

Este proyecto es propiedad de la Universidad Surcolombiana - Facultad de Ingeniería.

---

## Contacto

Para soporte técnico, consulte el repositorio o contacte al equipo de desarrollo.
