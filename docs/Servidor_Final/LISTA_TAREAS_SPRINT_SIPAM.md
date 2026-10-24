# LISTA DE TAREAS DE LA ITERACIÓN (SPRINT BACKLOG)
## SIPAM — Sistema Integrado de Prácticas Académicas y Monitorías
*(Formato: PMOInformatica Plantilla Scrum Lista de tareas de la iteración.xlsx)*

**Sprint:** 5 — Sprint Final (Semanas 13-15)
**Período:** Abril 2026 – Mayo 2026
**Equipo:** Equipo SIPAM

---

## SPRINT 1 — Autenticación y Convocatorias

| ID Item Backlog | Enunciado del Item | Tarea | Dueño | Estatus | Horas Est. | Horas Consumidas | Horas Rest. |
|-----------------|-------------------|-------|-------|---------|-----------|-----------------|-------------|
| HU-001 | Login con código institucional | Diseñar esquema BD usuarios y roles | Equipo SIPAM | Hecho | 4 | 4 | 0 |
| HU-001 | Login con código institucional | Implementar endpoint POST /auth/login con JWT | Equipo SIPAM | Hecho | 6 | 6 | 0 |
| HU-001 | Login con código institucional | Implementar protección brute-force (AuditLog) | Equipo SIPAM | Hecho | 4 | 4 | 0 |
| HU-001 | Login con código institucional | Diseñar pantalla Login con validaciones | Equipo SIPAM | Hecho | 5 | 5 | 0 |
| HU-001 | Login con código institucional | Implementar RBAC con require_roles decorator | Equipo SIPAM | Hecho | 4 | 4 | 0 |
| HU-002 | Crear convocatoria | Diseñar modelo Convocatoria + Asignatura (ORM) | Equipo SIPAM | Hecho | 4 | 4 | 0 |
| HU-002 | Crear convocatoria | Implementar POST /convocatorias/ con validaciones | Equipo SIPAM | Hecho | 8 | 8 | 0 |
| HU-002 | Crear convocatoria | Implementar validación período habilitado (calendario) | Equipo SIPAM | Hecho | 4 | 4 | 0 |
| HU-002 | Crear convocatoria | Diseñar formulario creación convocatoria (React) | Equipo SIPAM | Hecho | 8 | 8 | 0 |
| HU-003 | Gestionar estados convocatoria | Implementar PATCH /convocatorias/{id}/estado | Equipo SIPAM | Hecho | 6 | 6 | 0 |
| HU-003 | Gestionar estados convocatoria | Implementar máquina de estados y transiciones | Equipo SIPAM | Hecho | 4 | 4 | 0 |
| HU-003 | Gestionar estados convocatoria | Implementar notificaciones automáticas por estado | Equipo SIPAM | Hecho | 5 | 5 | 0 |
| HU-004 | Postulación básica | Implementar POST /postulaciones/convocatoria/{id} | Equipo SIPAM | Hecho | 6 | 6 | 0 |
| HU-004 | Postulación básica | Validar promedio y % créditos mínimo | Equipo SIPAM | Hecho | 3 | 3 | 0 |
| HU-004 | Postulación básica | Vista Convocatorias con botón postular | Equipo SIPAM | Hecho | 8 | 8 | 0 |
| **TOTAL SPRINT 1** | | | | | **89** | **89** | **0** |

---

## SPRINT 2 — Documentos, Evaluación y Selección

| ID Item Backlog | Enunciado del Item | Tarea | Dueño | Estatus | Horas Est. | Horas Consumidas | Horas Rest. |
|-----------------|-------------------|-------|-------|---------|-----------|-----------------|-------------|
| HU-005 | Subir documentos | Implementar POST /postulaciones/{id}/documentos (multipart) | Equipo SIPAM | Hecho | 8 | 8 | 0 |
| HU-005 | Subir documentos | Validación de archivos (extensión, tamaño, path traversal) | Equipo SIPAM | Hecho | 4 | 4 | 0 |
| HU-005 | Subir documentos | UI para carga de documentos con drag & drop | Equipo SIPAM | Hecho | 6 | 6 | 0 |
| HU-006 | Desistir postulación | Implementar PATCH /postulaciones/{id}/desistir | Equipo SIPAM | Hecho | 4 | 4 | 0 |
| HU-006 | Desistir postulación | Notificación al profesor al desistir | Equipo SIPAM | Hecho | 2 | 2 | 0 |
| HU-007 | Registrar notas | Implementar PATCH /postulaciones/{id}/nota-asignatura | Equipo SIPAM | Hecho | 3 | 3 | 0 |
| HU-007 | Registrar notas | Implementar PATCH /postulaciones/{id}/entrevista | Equipo SIPAM | Hecho | 3 | 3 | 0 |
| HU-007 | Registrar notas | Modal de notas en UI Evaluaciones.tsx | Equipo SIPAM | Hecho | 6 | 6 | 0 |
| HU-008 | Ejecutar selección | Implementar algoritmo RF-MON-05 en seleccion_utils.py | Equipo SIPAM | Hecho | 6 | 6 | 0 |
| HU-008 | Ejecutar selección | Implementar POST /seleccion/convocatorias/{id}/ejecutar | Equipo SIPAM | Hecho | 5 | 5 | 0 |
| HU-008 | Ejecutar selección | Vista de resultados de selección | Equipo SIPAM | Hecho | 5 | 5 | 0 |
| **TOTAL SPRINT 2** | | | | | **52** | **52** | **0** |

---

## SPRINT 3 — Prácticas Extramuros y Consentimiento

| ID Item Backlog | Enunciado del Item | Tarea | Dueño | Estatus | Horas Est. | Horas Consumidas | Horas Rest. |
|-----------------|-------------------|-------|-------|---------|-----------|-----------------|-------------|
| HU-009 | Crear práctica | Diseñar modelo Practica + RutaPractica (ORM) | Equipo SIPAM | Hecho | 6 | 6 | 0 |
| HU-009 | Crear práctica | Implementar POST /practicas/ con validaciones temporales | Equipo SIPAM | Hecho | 10 | 10 | 0 |
| HU-009 | Crear práctica | Formulario prácticas con mapa de rutas (React) | Equipo SIPAM | Hecho | 12 | 12 | 0 |
| HU-010 | Solicitar aprobación | Implementar PATCH /practicas/{id}/solicitar | Equipo SIPAM | Hecho | 4 | 4 | 0 |
| HU-010 | Solicitar aprobación | Notificaciones a jefes del mismo programa | Equipo SIPAM | Hecho | 3 | 3 | 0 |
| HU-011 | Firma consentimiento | Implementar POST /practicas/{id}/firmar-consentimiento | Equipo SIPAM | Hecho | 6 | 6 | 0 |
| HU-011 | Firma consentimiento | Validación ventana de firma (D-10 a D-5) | Equipo SIPAM | Hecho | 4 | 4 | 0 |
| HU-011 | Firma consentimiento | Lógica de quórum automático (66%) | Equipo SIPAM | Hecho | 4 | 4 | 0 |
| HU-011 | Firma consentimiento | UI firma consentimiento para estudiantes | Equipo SIPAM | Hecho | 5 | 5 | 0 |
| HU-012 | Aprobación jefe programa | Implementar PATCH /practicas/{id}/aprobar (jefe) | Equipo SIPAM | Hecho | 5 | 5 | 0 |
| HU-012 | Aprobación jefe programa | Implementar PATCH /practicas/{id}/rechazar | Equipo SIPAM | Hecho | 4 | 4 | 0 |
| HU-013 | Aprobación decano | Implementar PATCH /practicas/{id}/aprobar (decano) | Equipo SIPAM | Hecho | 3 | 3 | 0 |
| **TOTAL SPRINT 3** | | | | | **66** | **66** | **0** |

---

## SPRINT 4 — Aprobación Final, Ejecución y PDFs

| ID Item Backlog | Enunciado del Item | Tarea | Dueño | Estatus | Horas Est. | Horas Consumidas | Horas Rest. |
|-----------------|-------------------|-------|-------|---------|-----------|-----------------|-------------|
| HU-014 | Aprobación admin | Implementar PATCH /practicas/{id}/aprobar (admin) | Equipo SIPAM | Hecho | 5 | 5 | 0 |
| HU-014 | Aprobación admin | Compromiso presupuestal automático al aprobar | Equipo SIPAM | Hecho | 4 | 4 | 0 |
| HU-015 | Iniciar y finalizar | Implementar PATCH /practicas/{id}/iniciar | Equipo SIPAM | Hecho | 3 | 3 | 0 |
| HU-015 | Iniciar y finalizar | Implementar PATCH /practicas/{id}/finalizar con plazo 5 días | Equipo SIPAM | Hecho | 5 | 5 | 0 |
| HU-015 | Iniciar y finalizar | UI de informe final en Practicas.tsx | Equipo SIPAM | Hecho | 4 | 4 | 0 |
| HU-016 | PDFs servidor | Instalar WeasyPrint + Jinja2 en backend | Equipo SIPAM | Hecho | 2 | 2 | 0 |
| HU-016 | PDFs servidor | Crear templates HTML/CSS FO-14, FO-15, FO-16 | Equipo SIPAM | Hecho | 16 | 16 | 0 |
| HU-016 | PDFs servidor | Implementar endpoints GET /pdf/fo14, fo15, fo16 | Equipo SIPAM | Hecho | 8 | 8 | 0 |
| HU-016 | PDFs servidor | Integrar botones de descarga PDF en frontend | Equipo SIPAM | Hecho | 4 | 4 | 0 |
| **TOTAL SPRINT 4** | | | | | **51** | **51** | **0** |

---

## SPRINT 5 — IA, Notificaciones, Reportes y Pruebas

| ID Item Backlog | Enunciado del Item | Tarea | Dueño | Estatus | Horas Est. | Horas Consumidas | Horas Rest. |
|-----------------|-------------------|-------|-------|---------|-----------|-----------------|-------------|
| HU-017 | Recomendaciones IA | Implementar servicio Flask con 3 modelos ML (RF, XGBoost, LR) | Equipo SIPAM | Hecho | 20 | 20 | 0 |
| HU-017 | Recomendaciones IA | Implementar GET /ia/recomendaciones con fallback heurístico | Equipo SIPAM | Hecho | 8 | 8 | 0 |
| HU-017 | Recomendaciones IA | Widget de recomendaciones en Convocatorias.tsx | Equipo SIPAM | Hecho | 6 | 6 | 0 |
| HU-018 | Notificaciones | Implementar modelo Notificacion y endpoints | Equipo SIPAM | Hecho | 6 | 6 | 0 |
| HU-018 | Notificaciones | Cron job APScheduler recordatorios diarios | Equipo SIPAM | Hecho | 4 | 4 | 0 |
| HU-018 | Notificaciones | Bell de notificaciones en navbar | Equipo SIPAM | Hecho | 5 | 5 | 0 |
| HU-019 | Presupuesto | Implementar modelo Presupuesto + endpoints | Equipo SIPAM | Hecho | 8 | 8 | 0 |
| HU-019 | Presupuesto | Gestión de tarifas de viáticos | Equipo SIPAM | Hecho | 4 | 4 | 0 |
| HU-020 | Reportes y pruebas | Panel de administración Admin.tsx | Equipo SIPAM | Hecho | 8 | 8 | 0 |
| HU-020 | Reportes y pruebas | Crear suite pytest (36 pruebas automatizadas) | Equipo SIPAM | Hecho | 10 | 10 | 0 |
| HU-020 | Reportes y pruebas | Crear colección Postman (28 casos de prueba API) | Equipo SIPAM | Hecho | 4 | 4 | 0 |
| HU-020 | Reportes y pruebas | Documentación SAD, Requerimientos, Historias | Equipo SIPAM | Hecho | 8 | 8 | 0 |
| **TOTAL SPRINT 5** | | | | | **91** | **91** | **0** |

---

## RESUMEN TOTAL DEL PROYECTO

| Sprint | Horas estimadas | Horas consumidas | % Completado |
|--------|----------------|-----------------|-------------|
| Sprint 1 | 89 | 89 | 100% |
| Sprint 2 | 52 | 52 | 100% |
| Sprint 3 | 66 | 66 | 100% |
| Sprint 4 | 51 | 51 | 100% |
| Sprint 5 | 91 | 91 | 100% |
| **TOTAL** | **349** | **349** | **100%** |
