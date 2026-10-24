# SIPAM-USCO — Plan y Registro de Pruebas
**Sistema de Prácticas y Asesorías de Monitorías — Universidad Surcolombiana**
**Trabajo de Grado — Ingeniería de Software**

---

## Convenciones

| Símbolo | Significado |
|---|---|
| ✅ | Prueba ejecutada y aprobada |
| ❌ | Prueba ejecutada y fallida |
| 🔄 | Prueba implementada — pendiente de ejecutar |
| — | Prueba manual / cobertura de regla de negocio |

**Scripts disponibles:**
- `backend/test_api.py` — Prueba rápida de endpoints básicos
- `backend/test_usuarios.py` — Prueba de gestión de usuarios
- `backend/test_api_full.py` — Verificación E2E completa de todos los módulos

**Comando de ejecución:**
```bash
cd backend && .\venv\Scripts\python test_api_full.py
```

---

## MÓDULO 1 — Sistema / Health

| ID | Caso de prueba | Tipo | HTTP esperado | Estado |
|---|---|---|---|---|
| T-SYS-01 | `GET /health` retorna `{ status: "ok" }` | Positivo | 200 | ✅ |

---

## MÓDULO 2 — Autenticación (`/auth`)

### Pruebas positivas

| ID | Caso de prueba | Tipo | HTTP esperado | Estado |
|---|---|---|---|---|
| T-AUTH-01 | Login con código y contraseña correctos (JEFE001) | Positivo | 200 | ✅ |
| T-AUTH-02 | Login con código y contraseña correctos (PROF001) | Positivo | 200 | ✅ |
| T-AUTH-03 | Login con código y contraseña correctos (GASTOS001) | Positivo | 200 | ✅ |
| T-AUTH-04 | Token retornado contiene `access_token` y datos del usuario | Positivo | 200 | ✅ |
| T-AUTH-05 | `GET /auth/me` retorna datos del usuario autenticado | Positivo | 200 | ✅ |
| T-AUTH-06 | `GET /auth/validar-academica/{codigo}` retorna resultado de aptitud | Positivo | 200 | ✅ |
| T-AUTH-07 | Listar usuarios (jefe) retorna lista completa | Positivo | 200 | ✅ |
| T-AUTH-08 | Filtrar usuarios por rol (`?rol=estudiante`) | Positivo | 200 | ✅ |
| T-AUTH-09 | Buscar usuarios por nombre (`?q=Valentina`) | Positivo | 200 | ✅ |
| T-AUTH-10 | Crear usuario nuevo con rol `estudiante` | Positivo | 201 | ✅ |
| T-AUTH-11 | Toggle activo: desactivar usuario creado | Positivo | 200 | ✅ |
| T-AUTH-12 | Toggle activo: reactivar usuario | Positivo | 200 | ✅ |
| T-AUTH-13 | Reset de contraseña sin indicar nueva → genera temporal | Positivo | 200 | 🔄 |
| T-AUTH-14 | Reset de contraseña con nueva contraseña específica | Positivo | 200 | 🔄 |
| T-AUTH-15 | Actualizar perfil (nombre, email, teléfono) | Positivo | 200 | 🔄 |
| T-AUTH-16 | Cambio de contraseña con contraseña actual correcta | Positivo | 200 | 🔄 |

### Pruebas negativas

| ID | Caso de prueba | Tipo | HTTP esperado | Estado |
|---|---|---|---|---|
| T-AUTH-N01 | Login con contraseña incorrecta | Negativo | 401 | ✅ |
| T-AUTH-N02 | Acceso a endpoint protegido sin token | Negativo | 401 | ✅ |
| T-AUTH-N03 | Profesor intenta listar usuarios → sin permiso | Negativo | 403 | ✅ |
| T-AUTH-N04 | Toggle desactivar la propia cuenta | Negativo | 400 | ✅ |
| T-AUTH-N05 | `encargado_facultad` crea usuario con rol `admin` | Negativo | 403 | 🔄 |
| T-AUTH-N06 | `encargado_facultad` crea usuario con rol `encargado_gastos` | Negativo | 403 | 🔄 |
| T-AUTH-N07 | Crear usuario con código duplicado | Negativo | 400 | 🔄 |
| T-AUTH-N08 | Crear usuario con email duplicado | Negativo | 400 | 🔄 |
| T-AUTH-N09 | Crear usuario con cédula duplicada | Negativo | 400 | 🔄 |
| T-AUTH-N10 | Reset contraseña con nueva contraseña < 8 caracteres | Negativo | 400 | 🔄 |
| T-AUTH-N11 | Cambio de contraseña con contraseña actual incorrecta | Negativo | 400 | 🔄 |
| T-AUTH-N12 | Login con usuario inactivo | Negativo | 403 | 🔄 |

---

## MÓDULO 3 — Convocatorias (`/convocatorias`)

### Pruebas positivas

| ID | Caso de prueba | Tipo | HTTP esperado | Estado |
|---|---|---|---|---|
| T-CONV-01 | Listar convocatorias como jefe | Positivo | 200 | ✅ |
| T-CONV-02 | Listar convocatorias como profesor (solo las propias) | Positivo | 200 | ✅ |
| T-CONV-03 | Obtener detalle de convocatoria por ID | Positivo | 200 | ✅ |
| T-CONV-04 | Crear convocatoria como jefe con datos válidos | Positivo | 201 | ✅ |
| T-CONV-05 | Cambiar estado `borrador → abierta` | Positivo | 200 | ✅ |
| T-CONV-06 | Listar profesores disponibles para asignar | Positivo | 200 | 🔄 |
| T-CONV-07 | Crear asignatura con datos completos | Positivo | 201 | 🔄 |
| T-CONV-08 | Actualizar asignatura existente | Positivo | 200 | 🔄 |
| T-CONV-09 | Matricular estudiante en asignatura | Positivo | 201 | 🔄 |
| T-CONV-10 | Listar estudiantes matriculados en asignatura | Positivo | 200 | 🔄 |
| T-CONV-11 | Desmatricular estudiante de asignatura | Positivo | 200 | 🔄 |
| T-CONV-12 | Flujo completo de estados: borrador→abierta→cerrada→en_evaluacion→finalizada | Positivo | 200 c/u | 🔄 |

### Pruebas negativas

| ID | Caso de prueba | Tipo | HTTP esperado | Estado |
|---|---|---|---|---|
| T-CONV-N01 | Transición de estado inválida (`abierta → finalizada`) | Negativo | 400 | ✅ |
| T-CONV-N02 | Crear convocatoria con ventana de postulación < 5 días | Negativo | 400 | 🔄 |
| T-CONV-N03 | Crear convocatoria con ventana de postulación > 20 días | Negativo | 400 | 🔄 |
| T-CONV-N04 | Crear convocatoria con fecha de inicio en el pasado | Negativo | 400 | 🔄 |
| T-CONV-N05 | Fecha publicación resultados anterior al cierre de postulaciones | Negativo | 400 | 🔄 |
| T-CONV-N06 | Profesor edita convocatoria de otro profesor | Negativo | 403 | 🔄 |
| T-CONV-N07 | Editar convocatoria en estado `en_evaluacion` | Negativo | 400 | 🔄 |
| T-CONV-N08 | Crear asignatura con código duplicado | Negativo | 400 | 🔄 |
| T-CONV-N09 | Matricular mismo estudiante dos veces en el mismo período | Negativo | 400 | 🔄 |
| T-CONV-N10 | Abrir convocatoria fuera del período habilitado en calendario | Negativo | 400 | 🔄 |

---

## MÓDULO 4 — Postulaciones (`/postulaciones`)

### Pruebas positivas

| ID | Caso de prueba | Tipo | HTTP esperado | Estado |
|---|---|---|---|---|
| T-POST-01 | Estudiante se postula a convocatoria abierta | Positivo | 201 | 🔄 |
| T-POST-02 | Subir documento tipo `cedula` (PDF) | Positivo | 200 | 🔄 |
| T-POST-03 | Subir documento tipo `rut` (PDF) | Positivo | 200 | 🔄 |
| T-POST-04 | Subir documento tipo `certificado_bancario` (PDF) | Positivo | 200 | 🔄 |
| T-POST-05 | Al subir 3 documentos `documentos_completos` pasa a `true` | Positivo | 200 | ✅ |
| T-POST-06 | Reemplazar documento del mismo tipo (borra el anterior) | Positivo | 200 | 🔄 |
| T-POST-07 | Consultar mis postulaciones | Positivo | 200 | 🔄 |
| T-POST-08 | Listar postulantes de una convocatoria como profesor | Positivo | 200 | 🔄 |
| T-POST-09 | Registrar nota de asignatura (0.0–5.0) | Positivo | 200 | 🔄 |
| T-POST-10 | Registrar nota de entrevista con observaciones | Positivo | 200 | 🔄 |
| T-POST-11 | Descargar documento adjunto como jefe | Positivo | 200 | 🔄 |

### Pruebas negativas

| ID | Caso de prueba | Tipo | HTTP esperado | Estado |
|---|---|---|---|---|
| T-POST-N01 | Postular a convocatoria en estado `cerrada` | Negativo | 400 | 🔄 |
| T-POST-N02 | Postular fuera de la ventana de postulación (antes del inicio) | Negativo | 400 | 🔄 |
| T-POST-N03 | Postular fuera de la ventana de postulación (después del cierre) | Negativo | 400 | 🔄 |
| T-POST-N04 | Postular dos veces a la misma convocatoria | Negativo | 409 | 🔄 |
| T-POST-N05 | Postular con promedio por debajo del mínimo | Negativo | 422 | 🔄 |
| T-POST-N06 | Postular con créditos aprobados por debajo del mínimo | Negativo | 422 | 🔄 |
| T-POST-N07 | Subir documento de tipo inválido (`foto`) | Negativo | 400 | 🔄 |
| T-POST-N08 | Subir archivo que no es PDF | Negativo | 400 | 🔄 |
| T-POST-N09 | Descargar documento de otro estudiante | Negativo | 403 | 🔄 |
| T-POST-N10 | Profesor registra nota en convocatoria ajena | Negativo | 403 | 🔄 |
| T-POST-N11 | Nota de asignatura fuera del rango (6.0) | Negativo | 422 | 🔄 |

---

## MÓDULO 5 — Selección de Monitores (`/seleccion`)

### Pruebas positivas

| ID | Caso de prueba | Tipo | HTTP esperado | Estado |
|---|---|---|---|---|
| T-SEL-01 | Consultar resultados de selección como jefe | Positivo | 200 | ✅ |
| T-SEL-02 | Ejecutar selección sobre convocatoria `cerrada` con candidatos completos | Positivo | 200 | 🔄 |
| T-SEL-03 | Verificar fórmula: `(nota×0.30)+(prom×0.30)+(entrevista×0.40)` | Positivo | 200 | 🔄 |
| T-SEL-04 | Verificar que el 1er puesto tiene el mayor puntaje | Positivo | 200 | 🔄 |
| T-SEL-05 | Candidatos sin todas las notas quedan `no_seleccionado` | Positivo | 200 | 🔄 |
| T-SEL-06 | Estado convocatoria `cerrada` pasa a `en_evaluacion` al ejecutar | Positivo | 200 | 🔄 |
| T-SEL-07 | Estudiante consulta solo su propio resultado | Positivo | 200 | 🔄 |

### Pruebas negativas

| ID | Caso de prueba | Tipo | HTTP esperado | Estado |
|---|---|---|---|---|
| T-SEL-N01 | Ejecutar selección en convocatoria `abierta` (estado inválido) | Negativo | 400 | ✅ |
| T-SEL-N02 | Ejecutar selección sin candidatos con notas completas | Negativo | 422 | 🔄 |
| T-SEL-N03 | Profesor ejecuta selección de convocatoria ajena | Negativo | 403 | 🔄 |

---

## MÓDULO 6 — Prácticas Extramuros (`/practicas`)

### Pruebas positivas

| ID | Caso de prueba | Tipo | HTTP esperado | Estado |
|---|---|---|---|---|
| T-PRA-01 | Listar prácticas como jefe | Positivo | 200 | ✅ |
| T-PRA-02 | Crear práctica con rutas válidas (profesor) | Positivo | 201 | ✅ |
| T-PRA-03 | `fecha_inicio` al menos 30 días en el futuro | Positivo | 201 | ✅ |
| T-PRA-04 | Calcular viáticos de una práctica | Positivo | 200 | ✅ |
| T-PRA-05 | Solicitar práctica (borrador → solicitada) | Positivo | 200 | ✅ |
| T-PRA-06 | Jefe aprueba práctica solicitada | Positivo | 200 | ✅ |
| T-PRA-07 | Jefe rechaza práctica con observaciones | Positivo | 200 | 🔄 |
| T-PRA-08 | Estudiante firma consentimiento dentro de la ventana (D-10 a D-5) | Positivo | 200 | 🔄 |
| T-PRA-09 | Al alcanzar quórum 66%, práctica pasa a `aprobado_transporte` | Positivo | 200 | 🔄 |
| T-PRA-10 | Listar tarifas vigentes | Positivo | 200 | ✅ |
| T-PRA-11 | Crear nueva tarifa de viáticos | Positivo | 201 | 🔄 |
| T-PRA-12 | Actualizar tarifa existente | Positivo | 200 | 🔄 |
| T-PRA-13 | Obtener detalle de práctica por ID | Positivo | 200 | 🔄 |
| T-PRA-14 | Editar práctica en estado `borrador` | Positivo | 200 | 🔄 |

### Pruebas negativas

| ID | Caso de prueba | Tipo | HTTP esperado | Estado |
|---|---|---|---|---|
| T-PRA-N01 | Usuario sin rol `profesor` crea práctica | Negativo | 403 | ✅ |
| T-PRA-N02 | `fecha_inicio` con menos de 30 días de anticipación | Negativo | 400 | 🔄 |
| T-PRA-N03 | Solicitar práctica sin rutas registradas | Negativo | 422 | 🔄 |
| T-PRA-N04 | Firmar consentimiento fuera de la ventana habilitada | Negativo | 400 | 🔄 |
| T-PRA-N05 | Firmar consentimiento de práctica ya finalizada | Negativo | 400 | 🔄 |
| T-PRA-N06 | Firmar consentimiento sin estar matriculado en la asignatura | Negativo | 403 | 🔄 |
| T-PRA-N07 | Firmar consentimiento dos veces | Negativo | 409 | 🔄 |
| T-PRA-N08 | Editar práctica en estado `aprobado_transporte` | Negativo | 400 | 🔄 |
| T-PRA-N09 | Crear práctica fuera de las semanas habilitadas en el calendario | Negativo | 400 | 🔄 |
| T-PRA-N10 | Aprobar práctica no solicitada (`borrador`) | Negativo | 400 | 🔄 |

---

## MÓDULO 7 — Presupuesto (`/presupuesto`)

### Pruebas positivas

| ID | Caso de prueba | Tipo | HTTP esperado | Estado |
|---|---|---|---|---|
| T-PRES-01 | Obtener presupuesto actual | Positivo | 200 | ✅ |
| T-PRES-02 | Encargado de gastos consulta presupuesto actual | Positivo | 200 | ✅ |
| T-PRES-03 | Listar movimientos de un período | Positivo | 200 | ✅ |
| T-PRES-04 | Crear nuevo presupuesto para un período | Positivo | 201 | 🔄 |
| T-PRES-05 | Editar monto/descripción en estado `borrador` | Positivo | 200 | 🔄 |
| T-PRES-06 | Solicitar presupuesto (borrador → solicitado) | Positivo | 200 | 🔄 |
| T-PRES-07 | Gastos aprueba presupuesto (solicitado → aprobado) | Positivo | 200 | 🔄 |
| T-PRES-08 | Gastos rechaza presupuesto (solicitado → rechazado) | Positivo | 200 | 🔄 |
| T-PRES-09 | Gastos pide modificación (solicitado → modificacion) | Positivo | 200 | 🔄 |
| T-PRES-10 | Jefe solicita incremento sobre presupuesto aprobado | Positivo | 200 | 🔄 |
| T-PRES-11 | Gastos aprueba incremento (aplica nuevo monto) | Positivo | 200 | 🔄 |
| T-PRES-12 | Gastos rechaza incremento (vuelve a `aprobado`) | Positivo | 200 | ✅ |
| T-PRES-13 | Consultar período académico sugerido siguiente | Positivo | 200 | 🔄 |
| T-PRES-14 | Crear y actualizar configuración de calendario académico | Positivo | 201 / 200 | 🔄 |
| T-PRES-15 | Subir documento PDF de soporte al presupuesto | Positivo | 201 | 🔄 |
| T-PRES-16 | Listar documentos de soporte de un presupuesto | Positivo | 200 | 🔄 |
| T-PRES-17 | Descargar documento de soporte | Positivo | 200 | 🔄 |
| T-PRES-18 | Eliminar documento propio en presupuesto no aprobado | Positivo | 204 | 🔄 |
| T-PRES-19 | Consultar período activo (todos los roles) | Positivo | 200 | 🔄 |

### Pruebas negativas

| ID | Caso de prueba | Tipo | HTTP esperado | Estado |
|---|---|---|---|---|
| T-PRES-N01 | Profesor accede a presupuesto → sin permiso | Negativo | 403 | ✅ |
| T-PRES-N02 | Crear presupuesto para período ya existente | Negativo | 400 | 🔄 |
| T-PRES-N03 | Solicitar incremento con monto menor al actual | Negativo | 400 | 🔄 |
| T-PRES-N04 | Editar presupuesto ya aprobado | Negativo | 400 | 🔄 |
| T-PRES-N05 | Eliminar documento de presupuesto aprobado | Negativo | 400 | 🔄 |
| T-PRES-N06 | Jefe aprueba presupuesto (solo gastos puede) | Negativo | 403 | 🔄 |

---

## MÓDULO 8 — Reportes (`/reportes`)

| ID | Caso de prueba | Tipo | HTTP esperado | Estado |
|---|---|---|---|---|
| T-REP-01 | Obtener resumen ejecutivo como jefe | Positivo | 200 | 🔄 |
| T-REP-02 | Obtener datos FO-14 de convocatoria con monitor seleccionado | Positivo | 200 | 🔄 |
| T-REP-03 | Obtener datos FO-15 de práctica con rutas y firmas | Positivo | 200 | 🔄 |
| T-REP-04 | Obtener datos de consentimiento como estudiante que firmó | Positivo | 200 | 🔄 |
| T-REP-N01 | Estudiante que no firmó accede a consentimiento → 403 | Negativo | 403 | 🔄 |
| T-REP-N02 | Resumen ejecutivo como `profesor` → sin permiso | Negativo | 403 | 🔄 |

---

## MÓDULO 9 — Notificaciones (`/notificaciones`)

| ID | Caso de prueba | Tipo | HTTP esperado | Estado |
|---|---|---|---|---|
| T-NOT-01 | Listar notificaciones del usuario autenticado | Positivo | 200 | 🔄 |
| T-NOT-02 | Obtener conteo de notificaciones no leídas | Positivo | 200 | 🔄 |
| T-NOT-03 | Marcar una notificación como leída | Positivo | 200 | 🔄 |
| T-NOT-04 | Marcar todas las notificaciones como leídas | Positivo | 200 | 🔄 |
| T-NOT-05 | Eliminar una notificación | Positivo | 200 | 🔄 |
| T-NOT-06 | Notificación generada al abrir convocatoria | Integración | 200 | 🔄 |
| T-NOT-07 | Notificación generada al aprobar práctica | Integración | 200 | 🔄 |
| T-NOT-08 | Notificación generada al aprobar presupuesto | Integración | 200 | 🔄 |

---

## MÓDULO 10 — Monitor / Horas (`/monitor`)

| ID | Caso de prueba | Tipo | HTTP esperado | Estado |
|---|---|---|---|---|
| T-MON-01 | Monitor registra horas de una semana | Positivo | 201 | 🔄 |
| T-MON-02 | Monitor consulta sus horas registradas y total | Positivo | 200 | 🔄 |
| T-MON-03 | Profesor consulta horas de monitores de su convocatoria | Positivo | 200 | 🔄 |
| T-MON-04 | Profesor aprueba registro de horas | Positivo | 200 | 🔄 |
| T-MON-05 | Consultar audit log como jefe | Positivo | 200 | 🔄 |
| T-MON-06 | Login exitoso genera entrada en audit log | Integración | — | 🔄 |
| T-MON-07 | Login fallido genera entrada en audit log | Integración | — | 🔄 |
| T-MON-N01 | Estudiante no monitor intenta registrar horas → 403 | Negativo | 403 | 🔄 |
| T-MON-N02 | Registrar horas de semana ya registrada → 409 | Negativo | 409 | 🔄 |
| T-MON-N03 | Horas fuera del rango (0 o > 40) → 400 | Negativo | 400 | 🔄 |
| T-MON-N04 | Semana fuera del rango (0 o > 18) → 400 | Negativo | 400 | 🔄 |
| T-MON-N05 | Profesor aprueba horas de monitor de otro profesor → 403 | Negativo | 403 | 🔄 |

---

## MÓDULO 11 — Transporte (`/transporte`)

| ID | Caso de prueba | Tipo | HTTP esperado | Estado |
|---|---|---|---|---|
| T-TRAN-01 | Consultar precios de combustible vigentes (Huila) | Positivo | 200 | 🔄 |
| T-TRAN-02 | Listar peajes activos | Positivo | 200 | 🔄 |
| T-TRAN-03 | Filtrar peajes por departamento | Positivo | 200 | 🔄 |
| T-TRAN-04 | Calcular ruta Neiva → Pitalito (sin ORS) | Positivo | 200 | 🔄 |
| T-TRAN-05 | Calcular costos de transporte de una práctica registrada | Positivo | 200 | 🔄 |
| T-TRAN-06 | Consultar parámetros generales de transporte | Positivo | 200 | 🔄 |
| T-TRAN-N01 | Calcular costos de práctica sin rutas → 422 | Negativo | 422 | 🔄 |
| T-TRAN-N02 | Acceder sin token → 401 | Negativo | 401 | 🔄 |

---

## Resumen de cobertura

| Módulo | Total pruebas | Ejecutadas ✅ | Pendientes 🔄 |
|---|---|---|---|
| Sistema | 1 | 1 | 0 |
| Autenticación | 28 | 9 | 19 |
| Convocatorias | 22 | 5 | 17 |
| Postulaciones | 22 | 1 | 21 |
| Selección | 10 | 3 | 7 |
| Prácticas | 24 | 8 | 16 |
| Presupuesto | 25 | 5 | 20 |
| Reportes | 6 | 0 | 6 |
| Notificaciones | 8 | 0 | 8 |
| Monitor / Horas | 12 | 0 | 12 |
| Transporte | 8 | 0 | 8 |
| **TOTAL** | **166** | **32** | **134** |

---

## Pruebas de Integración — Flujos E2E

### Flujo E2E-01: Proceso completo de monitoría
1. ✅ Jefe crea convocatoria → estado `borrador`
2. 🔄 Jefe abre convocatoria → estado `abierta` → estudiantes notificados
3. 🔄 Estudiante se postula y sube 3 documentos
4. 🔄 Profesor registra notas de asignatura y entrevista
5. 🔄 Jefe cierra convocatoria → estado `cerrada`
6. 🔄 Profesor ejecuta algoritmo de selección → monitor seleccionado
7. 🔄 Jefe finaliza convocatoria → participantes notificados
8. 🔄 Monitor registra horas semanales
9. 🔄 Profesor aprueba horas del monitor

### Flujo E2E-02: Proceso completo de práctica extramural
1. ✅ Profesor crea práctica con rutas → estado `borrador`
2. ✅ Profesor solicita práctica → jefes notificados
3. ✅ Jefe aprueba práctica (sin quórum) → estado `pendiente_quorum`
4. 🔄 Estudiantes firman consentimiento hasta alcanzar 66%
5. 🔄 Sistema actualiza automáticamente a `aprobado_transporte`
6. 🔄 Se genera FO-15 con datos completos

### Flujo E2E-03: Ciclo presupuestal
1. 🔄 Jefe crea presupuesto → estado `borrador`
2. 🔄 Jefe edita monto y adjunta documentos de soporte
3. 🔄 Jefe solicita aprobación → gastos notificado
4. 🔄 Gastos aprueba → jefe notificado → estado `aprobado`
5. 🔄 Jefe solicita incremento → gastos notificado
6. 🔄 Gastos rechaza incremento → presupuesto vuelve a `aprobado`
7. 🔄 Aprobación de práctica compromete viáticos en el presupuesto

---

*Documento generado a partir de los scripts de prueba del proyecto SIPAM-USCO.*
*Scripts: `test_api.py`, `test_usuarios.py`, `test_api_full.py`*
