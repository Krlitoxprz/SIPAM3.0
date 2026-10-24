# SIPAM-USCO — v1.0 COMPLETO
**Sistema Integrado de Prácticas Académicas y Monitorías**  
Facultad de Ingeniería · Universidad Surcolombiana · Trabajo de Grado

---

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend API | FastAPI (Python 3.13) |
| Base de Datos | PostgreSQL 15 (prod) / SQLite (dev) vía SQLAlchemy ORM |
| Frontend | React 19 + TypeScript (Vite) |
| Estilos | Tailwind CSS v4 |
| Autenticación | JWT (python-jose) |

---

## Estructura del Proyecto

```
windsurf-project/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Endpoints REST
│   │   ├── core/            # Config y seguridad (JWT)
│   │   ├── db/              # SQLAlchemy engine y sesiones
│   │   ├── models/          # Modelos ORM
│   │   └── schemas/         # Esquemas Pydantic
│   ├── uploads/             # Archivos subidos (cédulas, RUT, etc.)
│   ├── venv/                # Entorno virtual Python
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/      # Header, Sidebar, ProtectedRoute
│   │   ├── context/         # AuthContext (JWT global)
│   │   ├── hooks/           # useAuth
│   │   ├── pages/           # Login, Dashboard, Convocatorias...
│   │   ├── services/        # Axios + endpoints
│   │   └── types/           # TypeScript interfaces
│   └── vite.config.ts
├── start-backend.ps1
├── start-frontend.ps1
└── README.md
```

---

## Iniciar en Desarrollo

### Terminal 1 — Backend (FastAPI)
```powershell
.\start-backend.ps1
# API disponible en: http://localhost:8000
# Swagger UI:        http://localhost:8000/api/docs
```

### Terminal 2 — Frontend (React)
```powershell
.\start-frontend.ps1
# App disponible en: http://localhost:5173
```

---

## Roles de Usuario

| Rol | Código de Prueba | Acceso |
|-----|-----------------|--------|
| Estudiante | `2020115001` | Convocatorias, postulaciones, firma consentimiento |
| Profesor | `PROF001` | Evaluación monitores, rutas de práctica |
| Encargado Facultad | `JEFE001` | Gestión total, presupuesto, actas |
| Encargado Gastos | `GASTOS001` | Viáticos, control presupuestal |

> **Contraseña de prueba:** `sipam2025` (configurada en el seeder — Paso 3)

---

## Formatos Digitalizados

- **MI-FOR-FO-14** — Requerimiento Monitores (Módulo de Monitorías)
- **MI-FOR-FO-15** — Prácticas Extramuros (Módulo de Prácticas)

---

## Plan de Desarrollo

- [x] **Paso 1:** Scaffolding y estructura base
- [ ] **Paso 2:** Modelos de base de datos (SQLAlchemy)
- [ ] **Paso 3:** Seeders con datos de prueba
- [ ] **Paso 4:** Endpoints API — Flujo completo de Monitorías
