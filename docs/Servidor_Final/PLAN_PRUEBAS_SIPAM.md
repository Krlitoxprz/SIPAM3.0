# PLAN DE PRUEBAS DE SOFTWARE
## SIPAM — Sistema Integrado de Prácticas Académicas y Monitorías
### Universidad Surcolombiana — Ingeniería de Software
**Versión:** 1.0 | **Fecha:** Mayo 2026

---

## 1. IDENTIFICACIÓN

| Campo | Valor |
|-------|-------|
| **Proyecto** | SIPAM — Sistema Integrado de Prácticas Académicas y Monitorías |
| **Versión del sistema** | 1.0.0 |
| **Responsables** | Equipo de desarrollo SIPAM |
| **Fecha de elaboración** | Mayo 2026 |
| **Herramientas usadas** | pytest, Postman, Navegador web |

---

## 2. OBJETIVO DE LAS PRUEBAS

Verificar que el sistema SIPAM cumple con los requerimientos funcionales y no funcionales definidos, garantizando el correcto funcionamiento de los flujos de monitorías estudiantiles, prácticas extramuros y el módulo de inteligencia artificial.

---

## 3. ALCANCE

### Incluye:
- Módulo de Autenticación y Control de Acceso (RF-AUTH)
- Módulo de Convocatorias de Monitorías (RF-MON)
- Módulo de Prácticas Extramuros (RF-PRA)
- Módulo de Inteligencia Artificial — Recomendaciones (RF-IA)
- Generación de PDFs institucionales (FO-14, FO-15, FO-16)

### No incluye:
- Pruebas de carga o estrés
- Pruebas de seguridad avanzadas (pentesting)

---

## 4. TIPOS DE PRUEBAS

| Tipo | Herramienta | Descripción |
|------|------------|-------------|
| **Unitarias** | pytest | Verificación de funciones y endpoints individuales |
| **Integración** | pytest + TestClient | Flujos completos entre capas del sistema |
| **API** | Postman | Verificación de endpoints REST con colección |
| **Funcional** | Navegador + capturas | Verificación manual de la interfaz de usuario |

---

## 5. CASOS DE PRUEBA

### 5.1 Módulo de Autenticación

| ID | Nombre | Precondición | Pasos | Resultado Esperado | Estado |
|----|--------|-------------|-------|-------------------|--------|
| PA-001 | Login Admin exitoso | Sistema activo | POST /auth/login usuario=Krlitoxprz pwd=Sasuke24 | Status 200, access_token presente, rol=admin | ✅ PASA |
| PA-002 | Login Profesor exitoso | Sistema activo | POST /auth/login usuario=87650001 pwd=sipam2025 | Status 200, access_token presente, rol=profesor | ✅ PASA |
| PA-003 | Login Estudiante exitoso | Sistema activo | POST /auth/login usuario=1136279761 pwd=sipam2025 | Status 200, access_token presente, rol=estudiante | ✅ PASA |
| PA-004 | Login Jefe de Programa | Sistema activo | POST /auth/login usuario=76001001 pwd=sipam2025 | Status 200, rol=jefe_programa | ✅ PASA |
| PA-005 | Login Decano | Sistema activo | POST /auth/login usuario=12791500 pwd=sipam2025 | Status 200, rol=decano | ✅ PASA |
| PA-006 | Credenciales inválidas | Sistema activo | POST /auth/login usuario=NADIE pwd=WRONG | Status 401, mensaje de error | ✅ PASA |
| PA-007 | Perfil autenticado | Token válido | GET /auth/me con Bearer token | Status 200, datos del usuario | ✅ PASA |
| PA-008 | Sin token rechazado | Sistema activo | GET /auth/me sin Authorization | Status 401 | ✅ PASA |
| PA-009 | Acceso denegado por rol | Token estudiante | POST /convocatorias/ | Status 403 | ✅ PASA |

### 5.2 Módulo de Monitorías

| ID | Nombre | Precondición | Pasos | Resultado Esperado | Estado |
|----|--------|-------------|-------|-------------------|--------|
| PM-001 | Listar convocatorias | Autenticado | GET /convocatorias/ | Status 200, array JSON | ✅ PASA |
| PM-002 | Crear convocatoria | Autenticado como profesor | POST /convocatorias/ con datos válidos | Status 201, estado=borrador | ✅ PASA |
| PM-003 | Postularse a convocatoria | Estudiante autenticado, convocatoria abierta | POST /postulaciones/convocatoria/{id} | Status 201, estado=pendiente | ✅ PASA |
| PM-004 | Postulación duplicada rechazada | Ya postulado | POST /postulaciones/convocatoria/{id} de nuevo | Status 409 | ✅ PASA |
| PM-005 | Sin promedio suficiente | Promedio < mínimo | POST /postulaciones/convocatoria/{id} | Status 422, motivo promedio | ✅ PASA |
| PM-006 | Mis postulaciones | Estudiante autenticado | GET /postulaciones/mis-postulaciones | Status 200, array con mis postulaciones | ✅ PASA |
| PM-007 | Desistir postulación | Postulación activa | PATCH /postulaciones/{id}/desistir | Status 200, estado=desistido | ✅ PASA |
| PM-008 | Ejecutar selección | Conv. cerrada, candidatos con notas | POST /seleccion/convocatorias/{id}/ejecutar-seleccion | Status 200, resultados con estado seleccionado/no_seleccionado | ✅ PASA |
| PM-009 | Cambiar estado convocatoria | Jefe autenticado, conv. abierta | PATCH /convocatorias/{id}/estado {estado: cerrada} | Status 200, estado=cerrada | ✅ PASA |
| PM-010 | Listar postulantes | Profesor/Jefe autenticado | GET /postulaciones/convocatoria/{id} | Status 200, lista de postulantes | ✅ PASA |

### 5.3 Módulo de Prácticas Extramuros

| ID | Nombre | Precondición | Pasos | Resultado Esperado | Estado |
|----|--------|-------------|-------|-------------------|--------|
| PP-001 | Crear práctica en borrador | Profesor autenticado | POST /practicas/ con datos válidos | Status 201, estado=borrador | ✅ PASA |
| PP-002 | Solicitar práctica | Práctica en borrador | PATCH /practicas/{id}/solicitar | Status 200, estado=solicitada | ✅ PASA |
| PP-003 | Jefe aprueba (Comité Currículo) | Práctica solicitada, quórum OK | PATCH /practicas/{id}/aprobar (jefe) | Status 200, estado=aprobada_curriculo | ✅ PASA |
| PP-004 | Decano avala (Consejo Facultad) | Práctica aprobada_curriculo | PATCH /practicas/{id}/aprobar (decano) | Status 200, estado=aprobada_facultad | ✅ PASA |
| PP-005 | Admin aprueba final (Vicerrectoría) | Práctica aprobada_facultad | PATCH /practicas/{id}/aprobar (admin) | Status 200, estado=aprobado_transporte | ✅ PASA |
| PP-006 | Rechazar práctica | Práctica solicitada | PATCH /practicas/{id}/rechazar con observaciones | Status 200, estado=rechazada | ✅ PASA |
| PP-007 | Iniciar práctica | Estado=aprobado_transporte, fecha llegó | PATCH /practicas/{id}/iniciar (profesor) | Status 200, estado=en_ejecucion | ✅ PASA |
| PP-008 | Finalizar práctica con informe | Estado=en_ejecucion | PATCH /practicas/{id}/finalizar con informe | Status 200, estado=finalizada | ✅ PASA |
| PP-009 | Listar prácticas | Autenticado | GET /practicas/ | Status 200, array JSON | ✅ PASA |
| PP-010 | Historial de estados | Práctica con historial | GET /practicas/{id}/historial | Status 200, lista de transiciones | ✅ PASA |

### 5.4 Módulo de Inteligencia Artificial

| ID | Nombre | Precondición | Pasos | Resultado Esperado | Estado |
|----|--------|-------------|-------|-------------------|--------|
| PIA-001 | Recomendaciones para estudiante | Estudiante autenticado | GET /ia/recomendaciones?limite=5 | Status 200, {recomendaciones:[], fuente, total_elegibles} | ✅ PASA |
| PIA-002 | Recomendaciones solo estudiante | Profesor autenticado | GET /ia/recomendaciones | Status 403 | ✅ PASA |
| PIA-003 | Recomendaciones sin convocatorias | No hay convocatorias abiertas | GET /ia/recomendaciones | Status 200, total_elegibles=0 | ✅ PASA |
| PIA-004 | Recomendaciones con convocatoria | Convocatoria abierta elegible | GET /ia/recomendaciones | Status 200, total_elegibles≥1, probabilidad_pct en [0,100] | ✅ PASA |
| PIA-005 | Fallback heurístico | Servicio Flask no disponible | GET /ia/recomendaciones | Status 200, fuente=heuristica | ✅ PASA |
| PIA-006 | Predicción IA | Flask disponible | POST /ia/predecir datos válidos | Status 200, selected_probability presente | ✅ PASA |
| PIA-007 | Validación parámetros | Datos inválidos | POST /ia/predecir promedio=10.0 | Status 422 | ✅ PASA |

### 5.5 Generación de PDFs

| ID | Nombre | Precondición | Pasos | Resultado Esperado | Estado |
|----|--------|-------------|-------|-------------------|--------|
| PPDF-001 | FO-14 Requerimiento Monitores | Conv. finalizada con datos | GET /pdf/fo14/{id} | Status 200, Content-Type=application/pdf | ✅ PASA |
| PPDF-002 | FO-16 Justificación Práctica | Práctica con rutas | GET /pdf/fo16/{id} | Status 200, Content-Type=application/pdf | ✅ PASA |
| PPDF-003 | FO-15 Lista de Participantes | Práctica con firmas | GET /pdf/fo15/{id} | Status 200, Content-Type=application/pdf | ✅ PASA |
| PPDF-004 | PDF inexistente retorna 404 | ID no existe | GET /pdf/fo14/9999 | Status 404 | ✅ PASA |

---

## 6. EJECUCIÓN DE PRUEBAS AUTOMATIZADAS

### Comando pytest:
```bash
cd backend
.\venv\Scripts\pytest tests/ -v --tb=short
```

### Importar colección Postman:
1. Abrir Postman
2. File → Import
3. Seleccionar: `docs/Servidor_Final/SIPAM_Postman_Collection.json`
4. Ejecutar colección completa con Runner

---

## 7. CRITERIOS DE ACEPTACIÓN

| Criterio | Umbral |
|----------|--------|
| Pruebas unitarias pasando | ≥ 90% |
| Endpoints de API respondiendo | 100% |
| Flujos críticos sin errores | 100% (Auth, Monitorías, Prácticas) |
| Tiempo de respuesta API | < 500ms por endpoint |

---

## 8. RIESGOS IDENTIFICADOS

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Servicio IA no disponible | Media | Medio | Fallback heurístico implementado |
| BD PostgreSQL no disponible | Baja | Alto | SQLite para pruebas unitarias |
| Dependencias WeasyPrint | Baja | Medio | Validado en entorno local y Docker |
