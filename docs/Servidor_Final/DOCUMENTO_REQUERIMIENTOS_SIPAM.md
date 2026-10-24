# DOCUMENTO DE REQUERIMIENTOS DE SOFTWARE
## SIPAM — Sistema Integrado de Prácticas Académicas y Monitorías
*(Formato: PMOI-Documento de requerimientos)*

---

## HISTORIAL DE VERSIONES

| Fecha | Versión | Autor | Organización | Descripción |
|-------|---------|-------|-------------|-------------|
| 01/03/2026 | 1.0 | Equipo SIPAM | USCO — Ing. de Software | Versión inicial del documento |
| 15/04/2026 | 1.1 | Equipo SIPAM | USCO — Ing. de Software | Actualización flujo prácticas y monitorías |
| 17/05/2026 | 1.2 | Equipo SIPAM | USCO — Ing. de Software | Adición módulo IA y generación PDF |

---

## INFORMACIÓN DEL PROYECTO

| Campo | Valor |
|-------|-------|
| **Empresa / Organización** | Universidad Surcolombiana — USCO |
| **Proyecto** | SIPAM — Sistema Integrado de Prácticas Académicas y Monitorías |
| **Fecha de preparación** | 17/05/2026 |
| **Cliente** | Facultad de Ingeniería — USCO |
| **Patrocinador principal** | Programa de Ingeniería de Software — USCO |
| **Gerente / Líder de Proyecto** | Equipo de desarrollo SIPAM |
| **Gerente / Líder de Análisis** | Equipo de desarrollo SIPAM |

---

## APROBACIONES

| Nombre y Apellido | Cargo | Departamento | Fecha | Firma |
|------------------|-------|-------------|-------|-------|
| Director de Proyecto | Director | Ingeniería de Software | 17/05/2026 | __________ |

---

## 1. PROPÓSITO

Este documento especifica los requerimientos de software del sistema **SIPAM** (Sistema Integrado de Prácticas Académicas y Monitorías), versión 1.0. El documento cubre la totalidad del sistema, incluyendo los módulos de monitorías estudiantiles, prácticas extramuros, inteligencia artificial y generación de documentos institucionales.

SIPAM es un sistema de información web desarrollado para la Universidad Surcolombiana con el objetivo de digitalizar y sistematizar los procesos académico-administrativos de monitorías (Acuerdo 012/2023) y prácticas extramuros (Acuerdo 003/2012).

---

## 2. ALCANCE DEL PRODUCTO / SOFTWARE

**Propósito u objetivo general:** Digitalizar el ciclo completo de gestión de monitorías estudiantiles y prácticas extramuros de la Universidad Surcolombiana, eliminando el uso de papel y agilizando los flujos de aprobación institucional.

**Beneficios para el área de negocio:**
- Reducción del tiempo de procesamiento de solicitudes de monitorías en ≥60%
- Trazabilidad completa de cada proceso mediante historial de estados
- Generación automática de formularios institucionales (FO-14, FO-15, FO-16)
- Recomendaciones personalizadas para estudiantes mediante inteligencia artificial

**Objetivos y metas:**
- Implementar el flujo completo de convocatoria → selección de monitores
- Implementar el flujo de solicitud → aprobación escalonada → ejecución de prácticas extramuros
- Integrar un módulo de IA que recomiende convocatorias a los estudiantes
- Generar PDFs institucionales con fidelidad a los formatos oficiales

---

## 3. REFERENCIAS

| Título | Tipo | Versión | Fecha |
|--------|------|---------|-------|
| Acuerdo 012/2023 — Reglamento Monitorías Estudiantiles | Normativa USCO | 1.0 | 2023 |
| Acuerdo 003/2012 — Requisitos Prácticas Extramuros | Normativa USCO | 1.0 | 2012 |
| MI-FOR-FO-14 — Requerimiento Monitores | Formulario institucional | Vigente | 2024 |
| MI-FOR-FO-15 — Requerimiento Prácticas Extramuros | Formulario institucional | Vigente | 2024 |
| MI-FOR-FO-16 — Justificación Práctica Extramuros | Formulario institucional | Vigente | 2024 |
| MI-FOR-FO-46 — Convocatoria para Monitores | Formulario institucional | Vigente | 2024 |
| AP-INF-FO-05 — Solicitud Desplazamiento Vial | Formulario institucional | Vigente | 2024 |

---

## 4. FUNCIONALIDADES DEL PRODUCTO

1. Autenticación y control de acceso por roles (RF-AUTH)
2. Gestión de convocatorias de monitorías (RF-MON-01)
3. Postulación de estudiantes a convocatorias (RF-MON-02)
4. Carga de documentos de postulación (RF-MON-03)
5. Evaluación y selección de monitores (RF-MON-04, RF-MON-05)
6. Gestión del ciclo de vida de prácticas extramuros (RF-PRA-01 a RF-PRA-08)
7. Firma digital de consentimiento informado (RF-PRA-07)
8. Control presupuestal y viáticos (RF-PRE)
9. Módulo de inteligencia artificial — recomendaciones (RF-IA-01)
10. Generación de PDFs institucionales (RF-PDF)
11. Notificaciones en tiempo real (RF-NOT)
12. Panel de administración y reportes (RF-ADM)

---

## 5. CLASES Y CARACTERÍSTICAS DE USUARIOS

| Tipo de Usuario | Rol en sistema | Frecuencia de uso | Funcionalidades principales |
|----------------|---------------|------------------|---------------------------|
| **Estudiante** | `estudiante` | Alta — consultivo | Ver convocatorias, postularse, firmar consentimiento, recibir recomendaciones IA |
| **Profesor** | `profesor` | Media — operativo | Crear convocatorias, evaluar postulantes, crear/gestionar prácticas, subir informe |
| **Jefe de Programa** | `jefe_programa` | Media — aprobador | Aprobar/rechazar prácticas (Comité Currículo), supervisar monitorías |
| **Decano** | `decano` | Baja — aprobador | Avalar prácticas (Consejo de Facultad), aprobar estados de convocatoria |
| **Administrador** | `admin` | Media — gestión | Aprobación final (Vicerrectoría), gestión de tarifas, presupuesto, usuarios |

---

## 6. ENTORNO OPERATIVO

- **Sistema operativo servidor:** Ubuntu 22.04 LTS (contenedores Docker)
- **Navegadores soportados:** Chrome 110+, Firefox 115+, Edge 110+
- **Base de datos:** PostgreSQL 15
- **Conectividad:** Red universitaria USCO (intranet) + acceso web HTTPS
- **Resolución mínima:** 1280×720 px

---

## 7. REQUERIMIENTOS FUNCIONALES

### 7.1 Módulo de Autenticación (RF-AUTH)

**RF-AUTH-01 — Login por código institucional**
| Campo | Detalle |
|-------|---------|
| Descripción | El sistema permite al usuario autenticarse con su código institucional (cédula o código asignado) y contraseña. |
| Entradas | Código institucional, contraseña |
| Proceso | Validar credenciales, verificar cuenta activa, generar JWT |
| Salidas | Token JWT con información del rol y datos básicos del usuario |
| Precondición | Usuario registrado y activo en el sistema |
| Postcondición | Sesión activa con permisos según rol |
| Regla de negocio | Máximo 5 intentos fallidos → bloqueo temporal (protección fuerza bruta) |

**RF-AUTH-02 — Control de acceso por roles (RBAC)**
| Campo | Detalle |
|-------|---------|
| Descripción | Cada endpoint del sistema aplica restricción de acceso según el rol del usuario autenticado. |
| Entradas | Token JWT, recurso solicitado |
| Proceso | Validar token, extraer rol, verificar permisos |
| Salidas | Acceso permitido o denegado (HTTP 403) |

### 7.2 Módulo de Monitorías (RF-MON)

**RF-MON-01 — Crear convocatoria de monitoría**
| Campo | Detalle |
|-------|---------|
| Descripción | El profesor o jefe de programa crea una convocatoria de monitoría para una asignatura específica. |
| Entradas | Título, asignatura, tipo de monitoría, período académico, fechas de postulación, número de monitores, promedio mínimo, horas por semana |
| Proceso | Validar período habilitado (calendario), verificar no duplicado por asignatura+período, crear convocatoria en estado `borrador` |
| Salidas | Convocatoria creada con ID |
| Restricciones | Una sola convocatoria activa por asignatura por período (Acuerdo 012/2023) |

**RF-MON-02 — Postulación de estudiante**
| Campo | Detalle |
|-------|---------|
| Descripción | El estudiante se postula a una convocatoria abierta si cumple los requisitos académicos. |
| Entradas | ID de convocatoria, carta de motivación |
| Proceso | Verificar convocatoria abierta, verificar promedio ≥ mínimo, verificar % créditos ≥ mínimo, verificar no duplicado |
| Salidas | Postulación creada en estado `pendiente` |

**RF-MON-03 — Carga de documentos**
| Campo | Detalle |
|-------|---------|
| Descripción | El estudiante sube su cédula, RUT y certificado bancario como documentos de la postulación. |
| Entradas | Archivo PDF (máx. 5MB), tipo de documento |
| Proceso | Validar extensión y tamaño, almacenar, marcar documentos completos si 3 subidos |
| Salidas | Archivo almacenado, postulación pasa a `en_revision` |

**RF-MON-04 — Desistir postulación**
| Campo | Detalle |
|-------|---------|
| Descripción | El estudiante puede retirar su postulación mientras la convocatoria está abierta o cerrada. |
| Entradas | ID de postulación |
| Proceso | Verificar ownership, verificar estado (no después de selección), cambiar estado a `desistido`, notificar al profesor |
| Salidas | Postulación en estado `desistido` |

**RF-MON-05 — Algoritmo de selección de monitores**
| Campo | Detalle |
|-------|---------|
| Descripción | Ejecutar el algoritmo de selección ponderado sobre los candidatos con notas registradas. |
| Entradas | ID de convocatoria |
| Proceso | Calcular puntaje = (Nota_Asig×0.30) + (Promedio×0.30) + (Entrevista×0.40); Ordenar; Seleccionar top N según cupos |
| Salidas | Resultados con estado `seleccionado` / `no_seleccionado` por postulante |
| Precondición | Convocatoria en estado `cerrada` o `en_evaluacion`, todos los candidatos con notas |

**RF-MON-06 — Gestión de estados de convocatoria**
| Campo | Detalle |
|-------|---------|
| Descripción | El jefe de programa o decano puede avanzar el estado de la convocatoria en el flujo definido. |
| Flujo | `borrador` → `abierta` → `cerrada` → `en_evaluacion` → `finalizada` |
| Restricciones | Cada transición dispara notificaciones a los involucrados |

### 7.3 Módulo de Prácticas Extramuros (RF-PRA)

**RF-PRA-01 — Crear práctica extramural**
| Campo | Detalle |
|-------|---------|
| Descripción | El profesor crea una solicitud de práctica extramural para su asignatura. |
| Entradas | Nombre, asignatura, período, fechas, número de alumnos, rutas, campos FO-16 |
| Proceso | Validar antelación mínima 30 días, validar duración máxima (3 días Huila / 4 días fuera), verificar no duplicado |
| Salidas | Práctica en estado `borrador` |

**RF-PRA-02 — Flujo de aprobación escalonado (Acuerdo 003/2012)**
| Campo | Detalle |
|-------|---------|
| Descripción | La práctica pasa por tres instancias de aprobación antes de ejecutarse. |
| Flujo | `borrador` → `solicitada` → `pendiente_quorum` → `aprobada_curriculo` → `aprobada_facultad` → `aprobado_transporte` → `en_ejecucion` → `finalizada` |
| Jefe de Programa | Comité de Currículo → `aprobada_curriculo` |
| Decano | Consejo de Facultad → `aprobada_facultad` |
| Admin | Vicerrectoría → `aprobado_transporte` |

**RF-PRA-07 — Firma de consentimiento informado**
| Campo | Detalle |
|-------|---------|
| Descripción | Los estudiantes matriculados firman digitalmente el consentimiento para participar. |
| Entradas | ID de práctica |
| Proceso | Verificar matrícula, verificar ventana de firma (D-10 a D-5), registrar firma con IP y timestamp |
| Quórum | ≥ 66% de firmas activa automáticamente la aprobación del Comité de Currículo |

**RF-PRA-08 — Finalizar práctica con informe**
| Campo | Detalle |
|-------|---------|
| Descripción | El profesor entrega el informe de resultados en máximo 5 días hábiles post-práctica. |
| Entradas | Informe de resultados (texto), observaciones opcionales |
| Restricción | Plazo máximo 5 días hábiles desde `fecha_fin` de la práctica |

### 7.4 Módulo de Inteligencia Artificial (RF-IA)

**RF-IA-01 — Recomendaciones personalizadas**
| Campo | Detalle |
|-------|---------|
| Descripción | El sistema recomienda convocatorias abiertas ordenadas por probabilidad de selección para cada estudiante. |
| Proceso | Filtrar elegibles → Llamar servicio IA → Si no disponible usar heurística → Ordenar por (match_programa, probabilidad) |
| Salidas | Lista de convocatorias con probabilidad_pct, programa_match, días_restantes |
| Fallback | Scoring heurístico basado en margen sobre promedio mínimo y ratio cupos/postulantes |

---

## 8. REGLAS DE NEGOCIO

| ID | Regla | Fuente |
|----|-------|--------|
| RN-01 | Una sola convocatoria activa por asignatura por período académico | Acuerdo 012/2023 |
| RN-02 | Ventana de postulación: mínimo 5 días, máximo 20 días | Acuerdo 012/2023 Art.6 |
| RN-03 | Estudiante con sanción disciplinaria no puede postularse | Acuerdo 012/2023 Art.4.c |
| RN-04 | Puntaje selección: Nota_Asig×0.30 + Promedio×0.30 + Entrevista×0.40 | RF-MON-05 |
| RN-05 | Práctica debe programarse con ≥30 días de anticipación | Acuerdo 003/2012 |
| RN-06 | Duración máxima práctica: 3 días (Huila) / 4 días (fuera Huila) | Acuerdo 003/2012 |
| RN-07 | Quórum consentimiento: ≥66% firmas de estudiantes matriculados | Acuerdo 003/2012 |
| RN-08 | Informe post-práctica: máximo 5 días hábiles después de fecha_fin | Acuerdo 003/2012 Art.7 |
| RN-09 | Máximo 5 intentos de login fallidos antes de bloqueo temporal | Seguridad |
| RN-10 | Una sola práctica activa por asignatura por período por docente | RF-PRA-UNI-01 |

---

## 9. REQUERIMIENTOS DE INTERFACES EXTERNAS

### 9.1 Interfaces de Usuario
- Aplicación web SPA (Single Page Application) en React 19 + TypeScript
- Diseño responsivo con Tailwind CSS v4
- Colores institucionales: vinotinto (#8D191D) y gris (#4E6470)
- Compatibilidad: Chrome 110+, Firefox 115+, Edge 110+

### 9.2 Interfaces de Hardware
- Servidor Ubuntu 22.04 LTS con mínimo 4GB RAM y 20GB almacenamiento
- Acceso a red para conexión de los clientes

### 9.3 Interfaces de Software
- Backend FastAPI expone API REST JSON en puerto 8000
- Servicio IA Flask en puerto 5001 (comunicación interna)
- Base de datos PostgreSQL 15 en puerto 5432
- Autenticación: JWT (JSON Web Tokens)

### 9.4 Interfaces de Comunicación
- HTTPS con certificado SSL para comunicación cliente-servidor
- CORS configurado para dominios institucionales
- API REST con formato JSON para todas las respuestas

---

## 10. REQUERIMIENTOS NO FUNCIONALES

| ID | Categoría | Descripción |
|----|-----------|-------------|
| RNF-01 | **Rendimiento** | Respuesta de endpoints API < 500ms bajo carga normal (≤50 usuarios concurrentes) |
| RNF-02 | **Seguridad** | JWT con expiración, RBAC estricto, headers de seguridad (X-Frame-Options, CSP) |
| RNF-03 | **Disponibilidad** | Sistema disponible 99% del tiempo en horario laboral (7am-7pm) |
| RNF-04 | **Escalabilidad** | Arquitectura de 3 servicios independientes escalables de forma independiente |
| RNF-05 | **Mantenibilidad** | Código documentado, ORM con migraciones versionadas, seed automatizado |
| RNF-06 | **Usabilidad** | Interfaz intuitiva, flujos guiados, notificaciones de feedback al usuario |
| RNF-07 | **Compatibilidad** | Funciona en los últimos 2 años de versión de Chrome, Firefox y Edge |
| RNF-08 | **Integridad de datos** | Historial de estados inmutable, validaciones en backend, transacciones ACID |
| RNF-09 | **Portabilidad** | Desplegable mediante Docker Compose en cualquier servidor Linux |
| RNF-10 | **Trazabilidad** | Registro de auditoría para todos los cambios de estado y acciones críticas |

---

## 11. OTROS REQUERIMIENTOS

- El sistema debe soportar los idiomas de los formularios institucionales en español
- Los PDFs generados deben cumplir con los formatos oficiales de la USCO
- El modo de prueba permite bypass de restricciones temporales para demostraciones
- Los archivos adjuntos se almacenan en el servidor con validación de tipo y tamaño

---

## 12. GLOSARIO

| Término | Definición |
|---------|-----------|
| **Convocatoria** | Proceso formal de selección de monitores estudiantiles para una asignatura |
| **Monitoría** | Programa de acompañamiento académico realizado por estudiantes destacados |
| **Práctica Extramural** | Actividad académica que se desarrolla fuera de las instalaciones universitarias |
| **Quórum** | Porcentaje mínimo (66%) de firmas de consentimiento requeridas para aprobar una práctica |
| **JWT** | JSON Web Token — mecanismo de autenticación sin estado |
| **RBAC** | Role-Based Access Control — control de acceso basado en roles |
| **FO-14** | Formulario institucional MI-FOR-FO-14: Requerimiento de Monitores |
| **FO-15** | Formulario institucional MI-FOR-FO-15: Lista de Participantes Prácticas |
| **FO-16** | Formulario institucional MI-FOR-FO-16: Justificación Práctica Extramuros |
| **RF** | Requerimiento Funcional |
| **RNF** | Requerimiento No Funcional |
| **Viáticos** | Compensación económica para gastos de desplazamiento del docente |
| **WeasyPrint** | Librería Python para generación de PDFs desde HTML/CSS |
| **SPA** | Single Page Application — aplicación web de página única |
