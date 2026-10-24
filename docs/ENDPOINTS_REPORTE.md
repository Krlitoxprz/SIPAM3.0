# SIPAM-USCO — Reporte de Endpoints del Backend
**Sistema de Prácticas y Asesorías de Monitorías — Universidad Surcolombiana**
**Base URL:** `http://localhost:8000/api/v1`
**Versión:** 1.0.0 | **Fecha:** 2026

---

## Resumen General

| Módulo | Prefijo | Total Endpoints |
|---|---|---|
| Sistema | `/health` | 1 |
| Autenticación | `/auth` | 8 |
| Convocatorias | `/convocatorias` | 12 |
| Postulaciones | `/postulaciones` | 7 |
| Selección de Monitores | `/seleccion` | 2 |
| Prácticas Extramuros | `/practicas` | 13 |
| Presupuesto | `/presupuesto` | 19 |
| Reportes | `/reportes` | 4 |
| Notificaciones | `/notificaciones` | 5 |
| Monitor (Horas) | `/monitor` | 5 |
| Transporte | `/transporte` | 5 |
| **TOTAL** | | **81** |

---

## Roles del sistema

| Código | Descripción |
|---|---|
| `admin` | Administrador del sistema |
| `encargado_facultad` | Jefe de Programa / Encargado de Facultad |
| `encargado_gastos` | Encargado de Gastos |
| `profesor` | Profesor |
| `estudiante` | Estudiante |

---

## 1. Sistema

### `GET /health`
- **Descripción:** Verificación de estado del sistema (health check).
- **Acceso:** Público (sin autenticación).
- **Respuesta:** `{ "status": "ok", "system": "SIPAM-USCO", "version": "1.0.0" }`

---

## 2. Autenticación — `/auth`

### `POST /auth/login`
- **Descripción:** Autentica un usuario con código y contraseña. Retorna un token JWT y los datos del usuario. Registra en el audit log el intento (exitoso o fallido). Bloquea usuarios inactivos con `403 Forbidden`.
- **Acceso:** Público.
- **Body:** `{ "codigo": string, "password": string }`
- **Respuesta:** `{ "access_token": string, "user": UserOut }`

### `GET /auth/me`
- **Descripción:** Retorna el perfil completo del usuario autenticado actualmente.
- **Acceso:** Todos los roles autenticados.
- **Respuesta:** `UserOut`

### `GET /auth/validar-academica/{codigo_estudiante}`
- **Descripción:** Valida si un estudiante cumple los requisitos académicos (promedio ≥ 3.5 y créditos aprobados ≥ 30%). Implementa el RF-MON-01.
- **Acceso:** `profesor`, `encargado_facultad`.
- **Parámetro:** `codigo_estudiante` — código del estudiante a validar.
- **Respuesta:** `{ apto: bool, promedio, porcentaje_creditos, motivos_rechazo[] }`

### `GET /auth/usuarios`
- **Descripción:** Lista todos los usuarios del sistema. Permite filtrar por rol (`?rol=`) y buscar por código, nombre o email (`?q=`).
- **Acceso:** `admin`, `encargado_facultad`.
- **Query params:** `rol` (opcional), `q` (opcional — búsqueda de texto).
- **Respuesta:** `UserOut[]`

### `POST /auth/usuarios`
- **Descripción:** Crea un nuevo usuario en el sistema. El `encargado_facultad` solo puede crear usuarios con rol `estudiante` o `profesor`. Nadie puede crear un `admin` por esta vía. Valida unicidad de código, email y cédula. Contraseña mínima 8 caracteres.
- **Acceso:** `admin`, `encargado_facultad`.
- **Body:** `UserCreate { codigo, nombres, apellidos, email, cedula, password, rol, promedio?, porcentaje_creditos?, programa?, sede? }`
- **Respuesta:** `UserOut` (HTTP 201)

### `PATCH /auth/me/perfil`
- **Descripción:** Permite al usuario autenticado actualizar sus propios datos de perfil (nombres, apellidos, email, teléfono, foto). También permite cambiar la contraseña (requiere ingresar la contraseña actual). Valida que el email no esté duplicado.
- **Acceso:** Todos los roles autenticados.
- **Body:** `{ nombres?, apellidos?, email?, telefono?, foto_url?, password_actual?, password_nuevo? }`
- **Respuesta:** `UserOut`

### `PATCH /auth/usuarios/{user_id}/toggle-activo`
- **Descripción:** Activa o desactiva un usuario. No permite desactivar la propia cuenta. Registra la acción en el audit log.
- **Acceso:** `admin`, `encargado_facultad`.
- **Parámetro:** `user_id` — ID del usuario.
- **Respuesta:** `UserOut` (con estado actualizado)

### `PATCH /auth/usuarios/{user_id}/reset-password`
- **Descripción:** Restablece la contraseña de un usuario. Si no se envía `nueva_password`, genera una contraseña temporal de 10 caracteres aleatorios. Registra la acción en audit log.
- **Acceso:** `admin`, `encargado_facultad`.
- **Body:** `{ nueva_password?: string }`
- **Respuesta:** `{ ok: true, nueva_password: string, mensaje: string }`

---

## 3. Convocatorias — `/convocatorias`

### `GET /convocatorias/`
- **Descripción:** Lista todas las convocatorias. Filtra por estado y período académico. Los profesores solo ven las suyas; los estudiantes solo ven las abiertas/cerradas/en evaluación/finalizadas. Auto-cierra convocatorias vencidas al consultarlas.
- **Acceso:** Todos los roles autenticados.
- **Query params:** `estado` (opcional), `periodo` (opcional).
- **Respuesta:** `ConvocatoriaOut[]` (incluye `total_postulantes`)

### `POST /convocatorias/`
- **Descripción:** Crea una nueva convocatoria en estado `borrador`. Valida: ventana de postulación mínima 5 días y máxima 20 (Acuerdo 012/2023 Art.6); fecha inicio no puede ser pasada; fecha publicación resultados debe ser posterior al cierre (Art.8). Los profesores solo pueden crear convocatorias para sus propias asignaturas.
- **Acceso:** `encargado_facultad`, `profesor`.
- **Body:** `ConvocatoriaCreate`
- **Respuesta:** `ConvocatoriaOut` (HTTP 201)

### `GET /convocatorias/{conv_id}`
- **Descripción:** Obtiene el detalle de una convocatoria por su ID, incluyendo asignatura y profesor.
- **Acceso:** Todos los roles autenticados.
- **Respuesta:** `ConvocatoriaOut`

### `PUT /convocatorias/{conv_id}`
- **Descripción:** Actualiza los datos de una convocatoria. Solo editable en estado `borrador` o `abierta`. Los profesores solo pueden editar sus propias convocatorias y no pueden asignar asignaturas ajenas.
- **Acceso:** `encargado_facultad`, `profesor`.
- **Body:** `ConvocatoriaUpdate`
- **Respuesta:** `ConvocatoriaOut`

### `PATCH /convocatorias/{conv_id}/estado`
- **Descripción:** Cambia el estado de una convocatoria siguiendo el flujo: `borrador → abierta → cerrada → en_evaluacion → finalizada`. Al abrir, verifica que estemos dentro del período habilitado en `ConfiguracionCalendario`. Envía notificaciones automáticas a los interesados según el nuevo estado.
- **Acceso:** `encargado_facultad`.
- **Body:** `{ estado: EstadoConvocatoriaEnum }`
- **Respuesta:** `ConvocatoriaOut`

### `GET /convocatorias/profesores`
- **Descripción:** Lista todos los profesores activos disponibles para asignar a una convocatoria.
- **Acceso:** `encargado_facultad`.
- **Respuesta:** `[{ id, codigo, nombre }]`

### `GET /convocatorias/asignaturas/todas`
- **Descripción:** Lista todas las asignaturas activas. El `encargado_facultad` puede incluir inactivas con `?include_inactive=true`. Los profesores solo ven las suyas.
- **Acceso:** Todos los roles autenticados.
- **Query params:** `include_inactive` (bool, solo `encargado_facultad`).
- **Respuesta:** `AsignaturaOut[]`

### `POST /convocatorias/asignaturas/`
- **Descripción:** Crea una nueva asignatura con código, nombre, créditos, programa, facultad, semestre y profesor asignado. Valida unicidad de código.
- **Acceso:** `encargado_facultad`.
- **Body:** `AsignaturaCreate`
- **Respuesta:** `AsignaturaOut` (HTTP 201)

### `PATCH /convocatorias/asignaturas/{asig_id}`
- **Descripción:** Actualiza los datos de una asignatura existente (nombre, créditos, facultad, estado activo, etc.).
- **Acceso:** `encargado_facultad`.
- **Body:** `AsignaturaCreate`
- **Respuesta:** `AsignaturaOut`

### `GET /convocatorias/asignaturas/{asig_id}/estudiantes`
- **Descripción:** Lista todos los estudiantes matriculados en una asignatura específica con su período académico.
- **Acceso:** `encargado_facultad`, `profesor`.
- **Respuesta:** `[{ id, estudiante_id, nombre, codigo, periodo_academico }]`

### `POST /convocatorias/asignaturas/{asig_id}/matricular`
- **Descripción:** Matricula un estudiante en una asignatura para un período académico dado. Valida que no exista matrícula duplicada para el mismo período.
- **Acceso:** `encargado_facultad`.
- **Body:** `{ estudiante_id: int, periodo_academico: string }`
- **Respuesta:** `{ ok: true }` (HTTP 201)

### `DELETE /convocatorias/asignaturas/matricula/{matricula_id}`
- **Descripción:** Elimina la matrícula de un estudiante en una asignatura (desmatricular).
- **Acceso:** `encargado_facultad`.
- **Respuesta:** `{ ok: true }`

---

## 4. Postulaciones — `/postulaciones`

### `POST /postulaciones/convocatoria/{conv_id}`
- **Descripción:** Permite a un estudiante postularse a una convocatoria abierta. Valida: convocatoria en estado `abierta`; ventana de postulación activa (RF-MON-TIME-01); que no exista postulación duplicada; que el estudiante cumpla el promedio mínimo y porcentaje de créditos exigidos.
- **Acceso:** `estudiante`.
- **Body:** `{ carta_motivacion?: string }`
- **Respuesta:** `PostulacionOut` (HTTP 201)

### `POST /postulaciones/{post_id}/documentos`
- **Descripción:** Sube un documento adjunto a una postulación (RF-MON-03). Tipos válidos: `cedula`, `rut`, `certificado_bancario`. Solo acepta PDF. Al cargar 3 documentos, marca `documentos_completos = true`. Si es reemplazo, borra el archivo anterior del disco.
- **Acceso:** `estudiante` (dueño de la postulación).
- **Form data:** `tipo_documento`, `file` (PDF).
- **Respuesta:** `ArchivoAdjuntoOut`

### `GET /postulaciones/mis-postulaciones`
- **Descripción:** Retorna todas las postulaciones del estudiante autenticado, ordenadas por fecha descendente.
- **Acceso:** `estudiante`.
- **Respuesta:** `PostulacionOut[]`

### `GET /postulaciones/convocatoria/{conv_id}`
- **Descripción:** Lista todos los postulantes de una convocatoria. Permite filtrar por estado (`?estado=`). Los profesores solo pueden ver postulantes de sus propias convocatorias.
- **Acceso:** `profesor`, `encargado_facultad`.
- **Query params:** `estado` (opcional).
- **Respuesta:** `PostulacionOut[]`

### `PATCH /postulaciones/{post_id}/nota-asignatura`
- **Descripción:** Registra la nota de la asignatura de un postulante (0.0 – 5.0). Solo el profesor dueño de la convocatoria puede hacerlo.
- **Acceso:** `profesor`.
- **Query param:** `nota` (float, 0.0–5.0).
- **Respuesta:** `PostulacionOut`

### `PATCH /postulaciones/{post_id}/entrevista`
- **Descripción:** Registra la nota de entrevista (0.0 – 5.0) y observaciones del evaluador. Registra la fecha/hora de la entrevista automáticamente. Solo el profesor dueño de la convocatoria puede ejecutarlo.
- **Acceso:** `profesor`.
- **Body:** `{ nota_entrevista: float, observaciones?: string }`
- **Respuesta:** `PostulacionOut`

### `GET /postulaciones/documentos/{archivo_id}/descargar`
- **Descripción:** Descarga autenticada de un documento adjunto a postulación. Los estudiantes solo pueden descargar sus propios documentos; profesores y jefe pueden descargar cualquiera. Incluye protección anti path-traversal.
- **Acceso:** Todos los roles autenticados (con restricción por rol).
- **Respuesta:** `FileResponse` (application/octet-stream)

---

## 5. Selección de Monitores — `/seleccion`

### `POST /seleccion/convocatorias/{conv_id}/ejecutar-seleccion`
- **Descripción:** Ejecuta el algoritmo de selección de monitores (RF-MON-05). Fórmula: `(Nota_Asignatura × 0.30) + (Promedio × 0.30) + (Entrevista × 0.40)`. Desempate: mejor entrevista → mejor promedio → mejor nota asignatura. Asigna estados `seleccionado` / `no_seleccionado`. Solo opera en convocatorias `cerrada` o `en_evaluacion`. Cambia automáticamente la convocatoria a `en_evaluacion` si estaba cerrada.
- **Acceso:** `profesor` (de la convocatoria), `encargado_facultad`.
- **Respuesta:** `ResultadoSeleccionOut[]` (ordenado por puntaje)

### `GET /seleccion/convocatorias/{conv_id}/resultados`
- **Descripción:** Consulta los resultados de selección de una convocatoria. Los estudiantes solo ven su propio resultado. Profesores y jefe ven todos los resultados ordenados por puesto.
- **Acceso:** `profesor`, `encargado_facultad`, `estudiante`.
- **Respuesta:** `ResultadoSeleccionOut[]`

---

## 6. Prácticas Extramuros — `/practicas`

### `GET /practicas/`
- **Descripción:** Lista prácticas según el rol: profesores ven las suyas; estudiantes ven las de sus asignaturas matriculadas (excluyendo prácticas finalizadas antiguas). Calcula el porcentaje de quórum y la ventana de firma para cada práctica.
- **Acceso:** Todos los roles autenticados.
- **Query params:** `estado` (opcional), `periodo` (opcional).
- **Respuesta:** `PracticaOut[]`

### `POST /practicas/`
- **Descripción:** Crea una nueva práctica extramural en estado `borrador` (RF-PRA-01). Valida: semana del semestre dentro del rango permitido en `ConfiguracionCalendario`; fecha de inicio con al menos 30 días de anticipación. Calcula automáticamente `duracion_dias` y las firmas requeridas (66% del total de alumnos).
- **Acceso:** `profesor`.
- **Body:** `PracticaCreate { nombre_practica, asignatura_id, periodo_academico, fecha_inicio, fecha_fin, num_alumnos, tipo_docente, rutas[], observaciones? }`
- **Respuesta:** `PracticaOut` (HTTP 201)

### `GET /practicas/{practica_id}`
- **Descripción:** Obtiene el detalle completo de una práctica, incluyendo asignatura, profesor, rutas, ventana de firma y porcentaje de quórum.
- **Acceso:** Todos los roles autenticados.
- **Respuesta:** `PracticaOut`

### `PUT /practicas/{practica_id}`
- **Descripción:** Actualiza los datos de una práctica. Solo editable en estado `borrador` o `solicitada`. Solo el profesor dueño puede editarla. Revalida la antelación mínima si se modifica la fecha de inicio.
- **Acceso:** `profesor` (dueño de la práctica).
- **Body:** `PracticaUpdate`
- **Respuesta:** `PracticaOut`

### `PATCH /practicas/{practica_id}/solicitar`
- **Descripción:** El profesor envía la práctica a revisión (cambia de `borrador` a `solicitada`). Requiere al menos una ruta registrada. Verifica la antelación mínima de 30 días. Notifica automáticamente a todos los jefes de programa.
- **Acceso:** `profesor` (dueño de la práctica).
- **Respuesta:** `PracticaOut`

### `PATCH /practicas/{practica_id}/aprobar`
- **Descripción:** El jefe de programa aprueba una práctica solicitada. Si ya se alcanzó el quórum de firmas, cambia a `aprobado_transporte` y compromete los viáticos en el presupuesto; si no, cambia a `pendiente_quorum`. Notifica al profesor.
- **Acceso:** `encargado_facultad`.
- **Respuesta:** `PracticaOut`

### `PATCH /practicas/{practica_id}/rechazar`
- **Descripción:** El jefe de programa rechaza una práctica en estado `solicitada` o `pendiente_quorum`. Registra observaciones opcionales. Notifica al profesor con el motivo.
- **Acceso:** `encargado_facultad`.
- **Body:** `{ observaciones_jefe?: string }`
- **Respuesta:** `PracticaOut`

### `POST /practicas/{practica_id}/firmar-consentimiento`
- **Descripción:** Firma digital del consentimiento informado por un estudiante (RF-PRA-07). Valida: práctica en estado `solicitada` o `pendiente_quorum`; práctica no finalizada; dentro de la ventana de firma (D-10 a D-5 antes de la fecha inicio); que el estudiante esté matriculado en la asignatura; que no haya firmado antes. Captura IP y User-Agent. Si se alcanza el quórum del 66%, actualiza automáticamente el estado.
- **Acceso:** `estudiante`.
- **Respuesta:** `FirmaConsentimientoOut`

### `GET /practicas/tarifas/vigentes`
- **Descripción:** Lista todas las tarifas de viáticos activas (disponible para todos los usuarios autenticados, para visualización).
- **Acceso:** Todos los roles autenticados.
- **Respuesta:** `TarifaViaticoOut[]`

### `GET /practicas/tarifas/todas`
- **Descripción:** Lista todas las tarifas de viáticos (activas e inactivas), para administración.
- **Acceso:** `encargado_facultad`, `encargado_gastos`.
- **Respuesta:** `TarifaViaticoOut[]`

### `POST /practicas/tarifas/`
- **Descripción:** Crea una nueva tarifa de viáticos con descripción, valor por día y fecha de vigencia. El valor por día debe ser mayor a 0.
- **Acceso:** `encargado_facultad`.
- **Body:** `{ descripcion, valor_dia, aplica_desde, is_active }`
- **Respuesta:** `TarifaViaticoOut` (HTTP 201)

### `PATCH /practicas/tarifas/{tarifa_id}`
- **Descripción:** Actualiza una tarifa de viáticos existente (descripción, valor o estado activo).
- **Acceso:** `encargado_facultad`.
- **Body:** `{ descripcion?, valor_dia?, is_active? }`
- **Respuesta:** `TarifaViaticoOut`

### `GET /practicas/{practica_id}/viaticos`
- **Descripción:** Calcula los viáticos estimados de una práctica cruzando los días de duración con las tarifas vigentes a la fecha de inicio (RF-PRA-02/03). Retorna el subtotal por tarifa.
- **Acceso:** `profesor`, `encargado_facultad`, `encargado_gastos`.
- **Respuesta:** `ViaticosCalculadoOut[]`

---

## 7. Presupuesto — `/presupuesto`

### `GET /presupuesto/`
- **Descripción:** Lista todos los presupuestos registrados ordenados por período descendente, con montos ejecutado, comprometido, disponible y porcentaje de ejecución.
- **Acceso:** `encargado_facultad`, `encargado_gastos`.
- **Respuesta:** `PresupuestoOut[]`

### `POST /presupuesto/`
- **Descripción:** Crea un nuevo presupuesto para un período académico en estado `borrador`. Valida que no exista otro presupuesto para el mismo período.
- **Acceso:** `encargado_facultad`.
- **Body:** `{ periodo_academico, monto_total_asignado, descripcion? }`
- **Respuesta:** `PresupuestoOut` (HTTP 201)

### `GET /presupuesto/actual`
- **Descripción:** Retorna el presupuesto del período académico activo (según `ConfiguracionCalendario`). Si no existe, retorna el más reciente.
- **Acceso:** `encargado_facultad`, `encargado_gastos`.
- **Respuesta:** `PresupuestoOut`

### `GET /presupuesto/{periodo}`
- **Descripción:** Retorna el presupuesto de un período académico específico.
- **Acceso:** `encargado_facultad`, `encargado_gastos`.
- **Respuesta:** `PresupuestoOut`

### `PATCH /presupuesto/{periodo}/editar`
- **Descripción:** El jefe de programa edita el monto o descripción de un presupuesto en estado `borrador`, `modificacion` o `rechazado`.
- **Acceso:** `encargado_facultad`.
- **Body:** `{ monto_total_asignado?, descripcion? }`
- **Respuesta:** `PresupuestoOut`

### `PATCH /presupuesto/{periodo}/solicitar`
- **Descripción:** El jefe envía la solicitud de presupuesto al encargado de gastos (cambia a estado `solicitado`). Notifica automáticamente a todos los encargados de gastos.
- **Acceso:** `encargado_facultad`.
- **Respuesta:** `PresupuestoOut`

### `PATCH /presupuesto/{periodo}/aprobar`
- **Descripción:** El encargado de gastos aprueba la solicitud (cambia a `aprobado`). Si había un incremento pendiente, aplica el nuevo monto. Notifica al jefe de programa.
- **Acceso:** `encargado_gastos`.
- **Body:** `{ observaciones?: string }`
- **Respuesta:** `PresupuestoOut`

### `PATCH /presupuesto/{periodo}/rechazar`
- **Descripción:** El encargado de gastos rechaza la solicitud. Si era un incremento, revierte a estado `aprobado` (no rechazado) para que el jefe pueda re-solicitar. Notifica al jefe con el motivo.
- **Acceso:** `encargado_gastos`.
- **Body:** `{ observaciones?: string }`
- **Respuesta:** `PresupuestoOut`

### `PATCH /presupuesto/{periodo}/pedir-modificacion`
- **Descripción:** El encargado de gastos devuelve la solicitud al jefe indicando correcciones (estado `modificacion`). Limpia el monto solicitado si había un incremento pendiente. Notifica al jefe.
- **Acceso:** `encargado_gastos`.
- **Body:** `{ observaciones?: string }`
- **Respuesta:** `PresupuestoOut`

### `PATCH /presupuesto/{periodo}/solicitar-incremento`
- **Descripción:** El jefe solicita un incremento del presupuesto ya aprobado. El nuevo monto debe ser mayor al actual. Guarda el monto solicitado sin modificar el monto aprobado, hasta que sea aprobado. Notifica al encargado de gastos con el diferencial.
- **Acceso:** `encargado_facultad`.
- **Body:** `{ nuevo_monto: float, descripcion?: string }`
- **Respuesta:** `PresupuestoOut`

### `GET /presupuesto/siguiente-periodo`
- **Descripción:** Sugiere el código del siguiente período académico que aún no tiene presupuesto registrado (formato `YYYY-1` o `YYYY-2`).
- **Acceso:** `encargado_facultad`.
- **Respuesta:** `{ periodo_sugerido, periodos_existentes[] }`

### `GET /presupuesto/movimientos/{periodo}`
- **Descripción:** Lista todos los movimientos presupuestales de un período (compromisos, ejecuciones, etc.) ordenados por fecha descendente.
- **Acceso:** `encargado_facultad`, `encargado_gastos`.
- **Respuesta:** `[{ id, tipo, monto, concepto, fecha }]`

### `GET /presupuesto/periodo-activo`
- **Descripción:** Retorna el período académico activo con sus fechas y semanas habilitadas para solicitudes. Accesible por todos los roles.
- **Acceso:** Todos los roles autenticados.
- **Respuesta:** `{ periodo_academico, fecha_inicio_semestre, fecha_fin_semestre, semana_inicio_solicitudes, semana_fin_solicitudes }`

### `GET /presupuesto/configuracion-calendario/`
- **Descripción:** Lista todas las configuraciones de calendario académico registradas, ordenadas por período descendente.
- **Acceso:** `encargado_facultad`.
- **Respuesta:** `CalendarioOut[]`

### `POST /presupuesto/configuracion-calendario/`
- **Descripción:** Crea una nueva configuración de calendario para un período académico (fecha inicio/fin del semestre, semanas habilitadas para solicitudes). Valida que no exista configuración previa para el mismo período.
- **Acceso:** `encargado_facultad`.
- **Body:** `CalendarioCreate { periodo_academico, semana_inicio_solicitudes, semana_fin_solicitudes, fecha_inicio_semestre, fecha_fin_semestre, is_active }`
- **Respuesta:** `CalendarioOut` (HTTP 201)

### `PATCH /presupuesto/configuracion-calendario/{cal_id}`
- **Descripción:** Actualiza una configuración de calendario existente.
- **Acceso:** `encargado_facultad`.
- **Body:** `CalendarioCreate`
- **Respuesta:** `CalendarioOut`

### `POST /presupuesto/{periodo}/documentos`
- **Descripción:** El jefe sube un documento de soporte al presupuesto (PDF, imagen, Word, Excel). Tipos válidos: `solicitud`, `incremento`, `modificacion`. Máximo según configuración de `MAX_FILE_SIZE_MB`.
- **Acceso:** `encargado_facultad`.
- **Form data:** `tipo_solicitud`, `descripcion?`, `file`.
- **Respuesta:** `DocumentoOut` (HTTP 201)

### `GET /presupuesto/{periodo}/documentos`
- **Descripción:** Lista todos los documentos adjuntos a un presupuesto de un período, con URL de descarga.
- **Acceso:** `encargado_facultad`, `encargado_gastos`.
- **Respuesta:** `DocumentoOut[]`

### `GET /presupuesto/documentos/{doc_id}/descargar`
- **Descripción:** Descarga/visualiza un documento de presupuesto. Incluye protección anti path-traversal.
- **Acceso:** `encargado_facultad`, `encargado_gastos`.
- **Respuesta:** `FileResponse`

### `DELETE /presupuesto/{periodo}/documentos/{doc_id}`
- **Descripción:** El jefe elimina un documento propio del presupuesto. Solo permite eliminar si el presupuesto no está aprobado. Borra también el archivo del disco.
- **Acceso:** `encargado_facultad` (solo el subidor).
- **Respuesta:** HTTP 204 (sin contenido)

---

## 8. Reportes — `/reportes`

### `GET /reportes/resumen`
- **Descripción:** Resumen ejecutivo del sistema. Incluye: total de convocatorias por estado y períodos; total de postulaciones por estado; lista de monitores seleccionados con puntajes; total de prácticas por estado con detalle; resumen de presupuesto por período (totales, ejecutado, disponible, % ejecución).
- **Acceso:** `encargado_facultad`, `encargado_gastos`.
- **Respuesta:** JSON estructurado con secciones `convocatorias`, `postulaciones`, `monitores_seleccionados`, `practicas`, `presupuesto`.

### `GET /reportes/fo14/{convocatoria_id}`
- **Descripción:** Datos completos para generar el formulario oficial **MI-FOR-FO-14** (Requerimiento de Monitores). Incluye datos de la convocatoria (sede, tipo de monitoría, descripción de actividades), asignatura (facultad), docente y monitor seleccionado (código, cédula, promedio, puntajes).
- **Acceso:** `encargado_facultad`, `profesor`.
- **Respuesta:** JSON con secciones `convocatoria`, `asignatura`, `docente`, `monitor`, `total_postulantes`.

### `GET /reportes/fo15/{practica_id}`
- **Descripción:** Datos completos para generar el formulario oficial **MI-FOR-FO-15** (Requerimiento de Prácticas Extramuros). Incluye datos de la práctica (tipo de docente, quórum, firmas), asignatura (facultad), docente, rutas ordenadas, participantes firmantes con fecha/hora de firma y total de viáticos calculados.
- **Acceso:** `encargado_facultad`, `profesor`.
- **Respuesta:** JSON con secciones `practica`, `asignatura`, `docente`, `rutas`, `participantes`, `viaticos`, `total_viaticos`.

### `GET /reportes/consentimiento/{practica_id}`
- **Descripción:** Datos para generar el PDF de consentimiento informado individual de un estudiante. Incluye datos del estudiante, práctica, asignatura, docente, puntos de origen y destino de la ruta, y fecha/IP de firma. Los estudiantes solo pueden acceder si ya firmaron.
- **Acceso:** Todos los roles autenticados (estudiante solo si firmó).
- **Respuesta:** JSON con secciones `estudiante`, `practica`, `asignatura`, `docente`, `origen`, `destino`, `rutas`, `fecha_firma`, `ip_firma`.

---

## 9. Notificaciones — `/notificaciones`

### `GET /notificaciones/`
- **Descripción:** Retorna las últimas 50 notificaciones del usuario autenticado, ordenadas por fecha descendente (leídas y no leídas).
- **Acceso:** Todos los roles autenticados.
- **Respuesta:** `[{ id, tipo, titulo, mensaje, leida, url, created_at }]`

### `GET /notificaciones/no-leidas/count`
- **Descripción:** Retorna el conteo de notificaciones no leídas del usuario autenticado (útil para badges en la UI).
- **Acceso:** Todos los roles autenticados.
- **Respuesta:** `{ count: int }`

### `PATCH /notificaciones/{nid}/leer`
- **Descripción:** Marca una notificación específica como leída. Solo opera sobre notificaciones propias del usuario.
- **Acceso:** Todos los roles autenticados.
- **Respuesta:** `{ ok: true }`

### `PATCH /notificaciones/leer-todas`
- **Descripción:** Marca todas las notificaciones no leídas del usuario autenticado como leídas.
- **Acceso:** Todos los roles autenticados.
- **Respuesta:** `{ ok: true }`

### `DELETE /notificaciones/{nid}`
- **Descripción:** Elimina permanentemente una notificación del usuario autenticado. Solo puede eliminar las suyas propias.
- **Acceso:** Todos los roles autenticados.
- **Respuesta:** `{ ok: true }`

---

## 10. Monitor (Horas) — `/monitor`

### `POST /monitor/registrar-horas`
- **Descripción:** El estudiante monitor registra sus horas trabajadas por semana. Requiere tener una postulación en estado `seleccionado`. La semana debe estar entre 1 y 18, y las horas entre 0.5 y 40. No permite duplicados por semana (si ya existe, debe pedir corrección al profesor). Registra en audit log.
- **Acceso:** `estudiante` (solo si es monitor seleccionado).
- **Body:** `{ semana: int, horas: float, descripcion?: string }`
- **Respuesta:** `{ id, semana, horas, descripcion, aprobado_por_id }`

### `GET /monitor/mis-horas`
- **Descripción:** El estudiante consulta sus propias horas registradas, junto con el total acumulado y los datos de la convocatoria/asignatura. Retorna estructura vacía si no es monitor activo.
- **Acceso:** `estudiante`.
- **Respuesta:** `{ postulacion, horas[], total_horas }`

### `GET /monitor/convocatoria/{conv_id}`
- **Descripción:** El profesor o jefe consulta el registro de horas de todos los monitores seleccionados de una convocatoria, con el total por monitor y estado de aprobación por semana.
- **Acceso:** `profesor`, `encargado_facultad`.
- **Respuesta:** `[{ postulacion_id, estudiante, codigo, total_horas, horas[] }]`

### `PATCH /monitor/horas/{hora_id}/aprobar`
- **Descripción:** El profesor (o jefe) aprueba un registro de horas de un monitor. Los profesores solo pueden aprobar horas de sus propios monitores. Registra en audit log quién aprobó.
- **Acceso:** `profesor` (solo sus monitores), `encargado_facultad`.
- **Respuesta:** `{ ok: true }`

### `GET /monitor/audit-log`
- **Descripción:** Retorna el log de auditoría del sistema con las últimas N acciones (máximo 1000, por defecto 100). Incluye usuario, acción, entidad afectada, ID y timestamp.
- **Acceso:** `admin`, `encargado_facultad`, `encargado_gastos`.
- **Query params:** `limit` (int, por defecto 100, máximo 1000).
- **Respuesta:** `[{ id, usuario, codigo, accion, entidad, entidad_id, detalle, created_at }]`

---

## 11. Transporte — `/transporte`

### `GET /transporte/combustible/precios`
- **Descripción:** Retorna los precios actuales de combustible para el departamento de Huila (gasolina corriente, diésel, gasolina extra), actualizados diariamente desde SICOM. Muestra uno por tipo (el más reciente).
- **Acceso:** Todos los roles autenticados.
- **Respuesta:** `{ departamento, precios[], nota }`

### `GET /transporte/peajes`
- **Descripción:** Lista todos los peajes activos del país con sus tarifas por categoría de vehículo (1-5), coordenadas GPS, corredor vial y entidad administradora. Permite filtrar por `departamento` y `corredor`.
- **Acceso:** Todos los roles autenticados.
- **Query params:** `departamento?`, `corredor?`
- **Respuesta:** `[{ id, nombre, departamento, municipio, corredor, lat, lon, tarifas{}, administrado_por }]`

### `POST /transporte/rutas/calcular`
- **Descripción:** Calcula el costo estimado de un trayecto origen–destino. Usa **OpenRouteService (ORS)** para obtener distancia y ruta real. Calcula: costo de combustible (precio SICOM × rendimiento del vehículo), peajes en ruta (detección geográfica si ORS disponible, o por municipio). Si ORS no está configurado, calcula con distancias aproximadas.
- **Acceso:** Todos los roles autenticados.
- **Body:** `{ origen, destino, tipo_vehiculo (bus|camioneta|moto), num_vehiculos, categoria_peaje (1-5), tipo_combustible (diesel|gasolina_corriente) }`
- **Respuesta:** JSON con secciones `ruta`, `combustible`, `peajes`, `resumen`.

### `GET /transporte/costos/{practica_id}`
- **Descripción:** Calcula el costo completo de transporte para una práctica extramural registrada, usando sus rutas definidas. Incluye: combustible (diésel, precio SICOM), peajes detectados por municipio, tarifa de conductor por día y seguro por pasajero (`$15.000 COP/estudiante`).
- **Acceso:** Todos los roles autenticados.
- **Query params:** `tipo_vehiculo`, `num_vehiculos`, `categoria_peaje`.
- **Respuesta:** JSON con `parametros_calculo`, `desglose` (combustible, peajes, conductor, seguro), `total_estimado_cop`.

### `GET /transporte/parametros`
- **Descripción:** Retorna los parámetros generales del módulo de transporte: precios de combustible vigentes, rendimientos por tipo de vehículo (km/litro), tarifa de conductor por día, seguro por pasajero y total de peajes activos en la base de datos.
- **Acceso:** Todos los roles autenticados.
- **Respuesta:** `{ combustible{}, rendimientos_km_litro{}, otros{}, base_datos_peajes{} }`

---

## Apéndice — Flujos de Estado

### Flujo de una Convocatoria
```
borrador → abierta → cerrada → en_evaluacion → finalizada
```

### Flujo de una Práctica Extramural
```
borrador → solicitada → pendiente_quorum ─┐
                     └──────────────────→ aprobado_transporte → en_ejecucion → finalizada
                                           rechazada
```

### Flujo del Presupuesto
```
borrador → solicitado → aprobado
                      → rechazado → borrador (re-editar)
                      → modificacion → solicitar de nuevo
aprobado → solicitar-incremento → solicitado (ciclo de aprobación de nuevo)
```

### Flujo de una Postulación
```
pendiente → en_revision → seleccionado
                        → no_seleccionado
                        → desistido
```

---

## Seguridad

- **Autenticación:** JWT Bearer Token en header `Authorization: Bearer <token>`.
- **Autorización:** Basada en roles (RBAC) con validación en cada endpoint mediante el decorador `require_roles()`.
- **Protección de archivos:** Anti path-traversal en todas las descargas de documentos.
- **Contraseñas:** Hasheo con `bcrypt` (mínimo 8 caracteres).
- **Auditoría:** Registro automático de acciones críticas (login, reset de contraseña, activación/desactivación de usuarios, aprobación de horas) en la tabla `AuditLog`.

---

*Documento generado automáticamente a partir del código fuente del backend SIPAM-USCO.*
