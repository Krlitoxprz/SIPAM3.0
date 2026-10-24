# DOCUMENTO DE ARQUITECTURA DE SOFTWARE (SAD)
## SIPAM — Sistema Integrado de Prácticas Académicas y Monitorías
### Universidad Surcolombiana — Programa Ingeniería de Software
**Versión:** 1.0 | **Fecha:** Mayo 2026 | **Autores:** Equipo SIPAM

---

## 1. INTRODUCCIÓN

### 1.1 Propósito
Este documento describe la arquitectura del sistema SIPAM, definiendo sus componentes, capas, flujos de datos e integraciones, con el fin de documentar las decisiones arquitectónicas tomadas durante el diseño e implementación.

### 1.2 Alcance
SIPAM gestiona digitalmente los procesos de convocatoria, selección y seguimiento de monitores estudiantiles (Acuerdo 012/2023) y la solicitud, aprobación y ejecución de prácticas extramuros (Acuerdo 003/2012) en la Universidad Surcolombiana.

### 1.3 Definiciones
| Término | Definición |
|---------|------------|
| RF | Requerimiento Funcional |
| ORM | Object-Relational Mapping |
| JWT | JSON Web Token |
| API | Application Programming Interface |
| RBAC | Role-Based Access Control |

---

## 2. REPRESENTACIÓN ARQUITECTÓNICA

SIPAM adopta una **arquitectura Cliente-Servidor de 3 capas** con servicios desacoplados:

```
┌─────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN                  │
│          React 19 + TypeScript + Tailwind CSS v4         │
│              Vite v8 · http://localhost:5173              │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP/REST (JSON)
                           │ JWT Bearer Token
┌──────────────────────────▼──────────────────────────────┐
│                   CAPA DE NEGOCIO (API)                  │
│              FastAPI (Python 3.13) + Uvicorn             │
│              http://localhost:8000/api/v1                │
│  ┌────────────┐ ┌────────────┐ ┌────────────────────┐   │
│  │Auth/JWT    │ │Monitorías  │ │Prácticas Extramuros│   │
│  │Endpoints   │ │Endpoints   │ │Endpoints           │   │
│  └────────────┘ └────────────┘ └────────────────────┘   │
│  ┌────────────┐ ┌────────────┐ ┌────────────────────┐   │
│  │PDF Gen     │ │Notific.    │ │Admin / Reportes    │   │
│  │WeasyPrint  │ │APScheduler │ │Endpoints           │   │
│  └────────────┘ └────────────┘ └────────────────────┘   │
│                      SQLAlchemy ORM                      │
└──────────────────────────┬──────────────────────────────┘
                           │ SQL
┌──────────────────────────▼──────────────────────────────┐
│                   CAPA DE DATOS                          │
│              PostgreSQL 15 — sipam_db                    │
│              localhost:5432                              │
└─────────────────────────────────────────────────────────┘

          ┌──────────────────────────────────┐
          │     SERVICIO IA (Microservicio)  │
          │  Flask + scikit-learn + SHAP     │
          │  http://localhost:5001           │
          │  3 modelos ML: RF, XGBoost, LR   │
          └──────────────────────────────────┘
```

---

## 3. OBJETIVOS Y RESTRICCIONES ARQUITECTÓNICAS

| Objetivo | Decisión |
|----------|----------|
| Seguridad de acceso | JWT + RBAC (5 roles) |
| Escalabilidad | Separación Frontend/Backend/AI |
| Mantenibilidad | ORM + migraciones + seed automatizado |
| Fidelidad documental | PDF server-side WeasyPrint |
| Recomendación IA | Microservicio Flask desacoplado con fallback heurístico |
| Trazabilidad | Historial de estados (HistorialEstado) + AuditLog |

---

## 4. VISTAS ARQUITECTÓNICAS

### 4.1 Vista de Componentes

```
Frontend (React)
├── pages/
│   ├── Login.tsx           ← Autenticación
│   ├── Convocatorias.tsx   ← RF-MON-01..06 + Widget IA
│   ├── Postulaciones.tsx   ← RF-MON-02..04
│   ├── Evaluaciones.tsx    ← RF-MON-05
│   ├── Practicas.tsx       ← RF-PRA-01..08
│   ├── Reportes.tsx        ← Reportes y estadísticas
│   └── Admin.tsx           ← Panel administrador
├── services/api.ts         ← Capa de comunicación HTTP
├── context/AuthContext.tsx ← Estado global de autenticación
└── utils/pdfForms.ts       ← PDF cliente (FO-05, FO-46)

Backend (FastAPI)
├── api/v1/endpoints/
│   ├── auth.py             ← Login, JWT, perfil
│   ├── convocatorias.py    ← CRUD + estados + notificaciones
│   ├── postulaciones.py    ← Postular, desistir, documentos
│   ├── seleccion.py        ← Algoritmo selección RF-MON-05
│   ├── practicas.py        ← Flujo completo prácticas
│   ├── presupuesto.py      ← Presupuesto y calendario
│   ├── ia.py               ← Proxy IA + /recomendaciones
│   ├── pdf_gen.py          ← FO-14, FO-15, FO-16 WeasyPrint
│   └── admin.py            ← Panel de administración
├── models/                 ← SQLAlchemy ORM
├── templates/              ← Jinja2 HTML para PDFs
└── utils/
    ├── seleccion_utils.py  ← Algoritmo centralizado
    ├── historial.py        ← Registro de cambios de estado
    └── notificaciones.py   ← Sistema de notificaciones

AI Service (Flask)
├── app.py                  ← Endpoints /predict, /explain, /metrics
├── predict.py              ← 3 modelos ML entrenados
└── models/                 ← Modelos serializados (.pkl)
```

### 4.2 Vista de Despliegue

```
┌──────────────────────────────────────────────────────────┐
│                    SERVIDOR UBUNTU 22.04                 │
│  ┌──────────────────┐  ┌──────────────────┐             │
│  │  Container       │  │  Container       │             │
│  │  sipam-backend   │  │  sipam-frontend  │             │
│  │  Puerto: 8000    │  │  Puerto: 80      │             │
│  └────────┬─────────┘  └────────┬─────────┘             │
│           │                     │                        │
│  ┌────────▼─────────┐  ┌────────▼─────────┐             │
│  │  Container       │  │  Nginx Reverse   │             │
│  │  sipam-ai        │  │  Proxy           │             │
│  │  Puerto: 5001    │  └──────────────────┘             │
│  └──────────────────┘                                   │
│  ┌──────────────────┐                                   │
│  │  PostgreSQL 15   │                                   │
│  │  sipam_db        │                                   │
│  └──────────────────┘                                   │
└──────────────────────────────────────────────────────────┘
         Docker Compose — Orquestación de contenedores
```

### 4.3 Vista de Datos (Modelo Relacional resumido)

Entidades principales:
- **users** — Usuarios del sistema (todos los roles)
- **asignaturas** — Catálogo de asignaturas por programa
- **convocatorias** — Convocatorias de monitoría
- **postulaciones** — Postulaciones de estudiantes
- **archivos_adjuntos** — Documentos de la postulación
- **practicas** — Prácticas extramuros
- **rutas_practica** — Itinerario de la práctica (FO-16)
- **firmas_consentimiento** — Firmas digitales de estudiantes
- **viaticos** — Viáticos calculados por práctica
- **tarifas_viaticos** — Tarifas vigentes por período
- **presupuesto** — Control presupuestal por período
- **historial_estado** — Auditoría de cambios de estado (SF-06)
- **notificaciones** — Notificaciones en tiempo real

---

## 5. PATRONES ARQUITECTÓNICOS UTILIZADOS

| Patrón | Aplicación |
|--------|------------|
| **Repository** | SQLAlchemy ORM como capa de abstracción |
| **Dependency Injection** | FastAPI `Depends()` para DB, Auth, Roles |
| **Strategy** | Fallback heurístico si IA no disponible |
| **Observer** | Notificaciones automáticas en cambios de estado |
| **Factory** | `get_db()` genera sesiones de BD |
| **RBAC** | `require_roles()` decorator por endpoint |
| **Chain of Responsibility** | Flujo escalonado de aprobación de prácticas |

---

## 6. FLUJOS PRINCIPALES

### 6.1 Flujo Monitorías (Acuerdo 012/2023)
```
Profesor/Jefe → Crear Convocatoria (borrador)
      → Publicar (abierta) → Estudiantes postulan
      → Cerrar → Evaluación notas + entrevistas
      → Ejecutar Selección (Algoritmo 30%+30%+40%)
      → Finalizar → Notificación resultados
```

### 6.2 Flujo Prácticas (Acuerdo 003/2012)
```
Profesor → Crear Práctica (borrador) → Solicitar
      → Jefe Programa (Comité Currículo) aprueba
      → Estudiantes Firman Consentimiento (≥66%)
      → Decano (Consejo Facultad) avala
      → Admin (Vicerrectoría) aprueba final
      → Profesor confirma inicio
      → Profesor entrega informe (≤5 días hábiles)
      → Finalizada
```

### 6.3 Flujo IA — Recomendaciones
```
Estudiante → GET /ia/recomendaciones
      → Backend filtra convocatorias elegibles
      → Llama a Flask AI /predict por cada convocatoria
      → Si falla: aplica heurística interna
      → Ordena por (programa_match, probabilidad)
      → Retorna top-N recomendaciones
```

---

## 7. DECISIONES ARQUITECTÓNICAS CLAVE (ADR)

### ADR-01: Microservicio IA desacoplado
**Decisión:** El servicio de ML corre en Flask separado del backend principal.
**Justificación:** Permite escalar independientemente y re-entrenar sin afectar la API.
**Consecuencia:** Se implementó fallback heurístico para alta disponibilidad.

### ADR-02: PDF server-side con WeasyPrint
**Decisión:** Los formularios FO-14, FO-15, FO-16 se generan en el servidor.
**Justificación:** Mayor fidelidad al formato oficial, independiente del navegador del cliente.
**Consecuencia:** Requiere dependencias del sistema (cairo, pango).

### ADR-03: Historial de estados inmutable
**Decisión:** Cada cambio de estado genera un registro en `historial_estado`.
**Justificación:** Trazabilidad completa para auditoría (SF-06, Acuerdo 003/2012).

### ADR-04: RBAC estricto por endpoint
**Decisión:** Cada endpoint define explícitamente los roles permitidos.
**Justificación:** Mínimo privilegio; cada actor solo accede a sus funciones.

---

## 8. CALIDAD Y SEGURIDAD

- **Autenticación:** JWT con expiración configurable
- **Autorización:** RBAC — 5 roles (admin, decano, jefe_programa, profesor, estudiante)
- **Protección fuerza bruta:** AuditLog en BD (multi-worker safe)
- **Headers de seguridad:** X-Frame-Options, X-Content-Type-Options, CSP
- **Validación de archivos:** Extensión + tamaño + path traversal check
- **CORS:** Configurado para dominios permitidos
- **Modo prueba:** Bypass de validaciones temporales para demos

---

## 9. TECNOLOGÍAS UTILIZADAS

| Capa | Tecnología | Versión |
|------|-----------|---------|
| Frontend | React | 19 |
| Frontend | TypeScript | 5 |
| Frontend | Vite | 8 |
| Frontend | Tailwind CSS | 4 |
| Frontend | lucide-react | latest |
| Backend | Python | 3.13 |
| Backend | FastAPI | latest |
| Backend | SQLAlchemy | 2.x |
| Backend | WeasyPrint | 68.1 |
| Backend | Jinja2 | 3.1.6 |
| Backend | APScheduler | 3.x |
| Base de datos | PostgreSQL | 15 |
| IA | Flask | 3.x |
| IA | scikit-learn | latest |
| IA | XGBoost | latest |
| IA | SHAP | latest |
| Despliegue | Docker + Compose | latest |
