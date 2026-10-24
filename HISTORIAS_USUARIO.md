# SIPAM-USCO — Historias de Usuario
**Sistema de Prácticas y Asesorías de Monitorías — Universidad Surcolombiana**
**Trabajo de Grado — Ingeniería de Software**

---

## Convenciones

- **Formato:** `Como [rol], quiero [funcionalidad], para [beneficio].`
- **Prioridad:** 🔴 Alta · 🟡 Media · 🟢 Baja
- **Estado:** ✅ Implementada · 🔄 En progreso · ⬜ Pendiente

---

## ÉPICA 1 — Autenticación y Gestión de Usuarios

### HU-01 · Login seguro
🔴 Alta | ✅ Implementada

**Como** cualquier usuario del sistema,
**quiero** iniciar sesión con mi código institucional y contraseña,
**para** acceder a las funcionalidades según mi rol.

**Criterios de aceptación:**
- El sistema valida código y contraseña; si son incorrectos retorna error 401.
- Si el usuario está inactivo, retorna error 403 con mensaje claro.
- El sistema genera un token JWT al autenticar exitosamente.
- Cada intento (exitoso o fallido) queda registrado en el log de auditoría.

---

### HU-02 · Consultar perfil propio
🔴 Alta | ✅ Implementada

**Como** cualquier usuario autenticado,
**quiero** consultar mis datos de perfil,
**para** verificar la información que el sistema tiene registrada sobre mí.

**Criterios de aceptación:**
- El endpoint retorna nombres, apellidos, código, email, rol y estado activo.
- Solo se retornan los datos del usuario que realiza la petición.

---

### HU-03 · Actualizar perfil personal
🟡 Media | ✅ Implementada

**Como** cualquier usuario autenticado,
**quiero** actualizar mis datos de perfil (nombre, email, teléfono, foto),
**para** mantener mi información institucional al día.

**Criterios de aceptación:**
- El usuario puede actualizar nombres, apellidos, email, teléfono y foto.
- Si se desea cambiar la contraseña, debe ingresar la contraseña actual para confirmar.
- La nueva contraseña debe tener mínimo 8 caracteres.
- El sistema valida que el nuevo email no esté en uso por otro usuario.

---

### HU-04 · Crear usuarios del sistema
🔴 Alta | ✅ Implementada

**Como** administrador o encargado de facultad,
**quiero** crear nuevos usuarios (estudiantes, profesores, encargados),
**para** incorporar al personal al sistema sin acceso directo a la base de datos.

**Criterios de aceptación:**
- El código, email y cédula deben ser únicos en el sistema.
- La contraseña inicial debe tener mínimo 8 caracteres.
- El `encargado_facultad` solo puede crear usuarios con rol `estudiante` o `profesor`.
- No se puede crear ningún usuario con rol `admin` por esta interfaz.
- El sistema retorna el usuario creado con HTTP 201.

---

### HU-05 · Listar y buscar usuarios
🟡 Media | ✅ Implementada

**Como** administrador o encargado de facultad,
**quiero** listar todos los usuarios con posibilidad de filtrar por rol y buscar por nombre o código,
**para** gestionar fácilmente el directorio del sistema.

**Criterios de aceptación:**
- Se puede filtrar por rol (`?rol=`).
- Se puede buscar por texto libre en código, nombres, apellidos o email (`?q=`).
- Los resultados se ordenan por rol y apellido.

---

### HU-06 · Activar / desactivar usuarios
🟡 Media | ✅ Implementada

**Como** administrador o encargado de facultad,
**quiero** activar o desactivar cuentas de usuario,
**para** controlar el acceso al sistema sin eliminar registros históricos.

**Criterios de aceptación:**
- El estado cambia al opuesto del actual (toggle).
- No se puede desactivar la propia cuenta.
- La acción queda registrada en el log de auditoría.

---

### HU-07 · Restablecer contraseña de un usuario
🟡 Media | ✅ Implementada

**Como** administrador o encargado de facultad,
**quiero** restablecer la contraseña de un usuario,
**para** ayudarlo cuando pierde el acceso a su cuenta.

**Criterios de aceptación:**
- Se puede ingresar una nueva contraseña específica o dejar que el sistema genere una temporal de 10 caracteres.
- La contraseña debe tener mínimo 8 caracteres.
- La acción queda registrada en el log de auditoría.
- La respuesta incluye la nueva contraseña en texto claro para comunicársela al usuario.

---

### HU-08 · Validar requisitos académicos de un estudiante
🔴 Alta | ✅ Implementada

**Como** profesor o encargado de facultad,
**quiero** validar si un estudiante cumple los requisitos académicos para ser monitor,
**para** asegurar que solo estudiantes aptos participen en las convocatorias (RF-MON-01).

**Criterios de aceptación:**
- El sistema evalúa promedio ≥ 3.5 y porcentaje de créditos aprobados ≥ 30%.
- Retorna un campo `apto: true/false` y los motivos de rechazo si aplica.
- Retorna los valores actuales de promedio y porcentaje de créditos del estudiante.

---

## ÉPICA 2 — Gestión de Asignaturas

### HU-09 · Crear y gestionar asignaturas
🔴 Alta | ✅ Implementada

**Como** encargado de facultad,
**quiero** crear y actualizar asignaturas con su información académica,
**para** tener un catálogo actualizado de materias disponibles para convocatorias y prácticas.

**Criterios de aceptación:**
- Cada asignatura tiene código único, nombre, créditos, programa, facultad y semestre.
- Se puede asignar un profesor responsable.
- Se puede activar o desactivar la asignatura.
- El sistema valida código duplicado.

---

### HU-10 · Consultar asignaturas disponibles
🟡 Media | ✅ Implementada

**Como** cualquier usuario autenticado,
**quiero** ver el listado de asignaturas activas,
**para** conocer las materias disponibles en el sistema.

**Criterios de aceptación:**
- Los profesores solo ven las asignaturas que dictan.
- El `encargado_facultad` puede ver también las inactivas con un parámetro opcional.
- Los resultados se ordenan por semestre y nombre.

---

### HU-11 · Matricular y desmatricular estudiantes en asignaturas
🔴 Alta | ✅ Implementada

**Como** encargado de facultad,
**quiero** matricular y desmatricular estudiantes en asignaturas por período académico,
**para** reflejar la asistencia real a clases y controlar quién puede firmar consentimientos.

**Criterios de aceptación:**
- No se permite duplicar una matrícula para el mismo estudiante, asignatura y período.
- La desmatrícula elimina el registro.
- Se puede consultar la lista de estudiantes matriculados por asignatura.

---

## ÉPICA 3 — Convocatorias de Monitorías

### HU-12 · Crear convocatoria de monitoría
🔴 Alta | ✅ Implementada

**Como** profesor o encargado de facultad,
**quiero** crear una convocatoria de monitoría en estado borrador,
**para** iniciar el proceso de selección de monitores para una asignatura.

**Criterios de aceptación:**
- La ventana de postulación debe ser mínimo 5 días y máximo 20 días (Acuerdo 012/2023 Art.6).
- La fecha de inicio de postulación no puede ser en el pasado.
- La fecha de publicación de resultados debe ser posterior al cierre de postulaciones (Art.8).
- El profesor solo puede crear convocatorias para asignaturas que él dicta.
- El `encargado_facultad` debe seleccionar explícitamente el profesor responsable.
- La convocatoria se crea en estado `borrador`.

---

### HU-13 · Publicar convocatoria (cambio de estado)
🔴 Alta | ✅ Implementada

**Como** encargado de facultad,
**quiero** abrir, cerrar y finalizar convocatorias siguiendo un flujo controlado,
**para** garantizar que el proceso de selección de monitores siga los pasos establecidos.

**Criterios de aceptación:**
- El flujo de estados es: `borrador → abierta → cerrada → en_evaluacion → finalizada`.
- No se permiten transiciones fuera del flujo.
- Al abrir una convocatoria, el sistema verifica que estemos dentro del período habilitado en el calendario académico.
- Al abrir, se notifica automáticamente a todos los estudiantes activos.
- Al pasar a `en_evaluacion`, se notifica a los postulantes.
- Al finalizar, se notifica a los postulantes con su resultado.
- Las convocatorias cuya fecha de cierre venció se cierran automáticamente.

---

### HU-14 · Consultar convocatorias
🟡 Media | ✅ Implementada

**Como** cualquier usuario del sistema,
**quiero** ver el listado de convocatorias con sus detalles,
**para** conocer las oportunidades de monitoría disponibles.

**Criterios de aceptación:**
- Se puede filtrar por estado y período académico.
- Los estudiantes solo ven convocatorias en estado abierta, cerrada, en evaluación o finalizada.
- Los profesores solo ven sus propias convocatorias.
- Cada convocatoria muestra el total de postulantes.

---

### HU-15 · Editar convocatoria
🟡 Media | ✅ Implementada

**Como** profesor o encargado de facultad,
**quiero** editar los datos de una convocatoria antes de publicarla o mientras está abierta,
**para** corregir errores o actualizar la información.

**Criterios de aceptación:**
- Solo se pueden editar convocatorias en estado `borrador` o `abierta`.
- El profesor solo puede editar sus propias convocatorias y no puede asignar asignaturas ajenas.

---

## ÉPICA 4 — Postulaciones

### HU-16 · Postularse a una convocatoria
🔴 Alta | ✅ Implementada

**Como** estudiante,
**quiero** postularme a una convocatoria de monitoría abierta,
**para** participar en el proceso de selección (RF-MON-02).

**Criterios de aceptación:**
- Solo se pueden realizar postulaciones a convocatorias en estado `abierta`.
- La postulación solo es válida dentro de la ventana de postulación (RF-MON-TIME-01).
- No se permiten postulaciones duplicadas en la misma convocatoria.
- El estudiante debe cumplir el promedio mínimo y porcentaje de créditos de la convocatoria; si no, el sistema rechaza con los motivos.
- La postulación se crea en estado `pendiente`.

---

### HU-17 · Subir documentos a la postulación
🔴 Alta | ✅ Implementada

**Como** estudiante,
**quiero** subir mis documentos requeridos (cédula, RUT, certificado bancario) a mi postulación,
**para** completar mi expediente y avanzar en el proceso (RF-MON-03).

**Criterios de aceptación:**
- Solo se aceptan archivos PDF.
- Los tipos válidos son: `cedula`, `rut`, `certificado_bancario`.
- Si se sube un documento del mismo tipo, reemplaza el anterior (borra el archivo físico previo).
- Al tener los 3 documentos, se marca `documentos_completos = true`.
- Al subir el primer documento, el estado de la postulación cambia a `en_revision`.

---

### HU-18 · Consultar mis postulaciones
🟡 Media | ✅ Implementada

**Como** estudiante,
**quiero** ver el estado de todas mis postulaciones,
**para** hacer seguimiento a los procesos en los que participo.

**Criterios de aceptación:**
- Muestra todas las postulaciones del estudiante ordenadas por fecha descendente.
- Incluye el estado actual, documentos adjuntos y datos de la convocatoria.

---

### HU-19 · Ver postulantes de una convocatoria
🟡 Media | ✅ Implementada

**Como** profesor o encargado de facultad,
**quiero** ver la lista de postulantes de una convocatoria con sus datos y estado,
**para** gestionar el proceso de evaluación.

**Criterios de aceptación:**
- El profesor solo puede ver los postulantes de sus propias convocatorias.
- Se puede filtrar por estado de postulación.
- Incluye documentos adjuntos del postulante.

---

### HU-20 · Registrar nota de asignatura al postulante
🔴 Alta | ✅ Implementada

**Como** profesor,
**quiero** registrar la nota de la asignatura de cada postulante,
**para** que el algoritmo de selección pueda calcular el puntaje final.

**Criterios de aceptación:**
- La nota debe estar entre 0.0 y 5.0.
- Solo el profesor dueño de la convocatoria puede registrar notas.

---

### HU-21 · Registrar nota de entrevista
🔴 Alta | ✅ Implementada

**Como** profesor,
**quiero** registrar la nota de entrevista y observaciones de cada postulante,
**para** completar la evaluación necesaria para la selección.

**Criterios de aceptación:**
- La nota debe estar entre 0.0 y 5.0.
- Solo el profesor dueño de la convocatoria puede registrar la nota.
- El sistema registra automáticamente la fecha y hora de la entrevista.

---

### HU-22 · Descargar documento adjunto de postulación
🟢 Baja | ✅ Implementada

**Como** profesor o encargado de facultad,
**quiero** descargar los documentos adjuntos de un postulante,
**para** verificar la autenticidad de la documentación presentada.

**Criterios de aceptación:**
- El estudiante solo puede descargar sus propios documentos.
- El sistema protege contra ataques de path-traversal.
- El archivo se descarga con el nombre original.

---

## ÉPICA 5 — Selección de Monitores

### HU-23 · Ejecutar algoritmo de selección
🔴 Alta | ✅ Implementada

**Como** profesor o encargado de facultad,
**quiero** ejecutar el algoritmo de selección automático sobre los postulantes evaluados,
**para** determinar objetivamente quién(es) serán el (los) monitor(es) seleccionado(s) (RF-MON-05).

**Criterios de aceptación:**
- La fórmula es: `(Nota_Asignatura × 0.30) + (Promedio × 0.30) + (Entrevista × 0.40)`.
- Solo opera en convocatorias en estado `cerrada` o `en_evaluacion`.
- Solo aplica a candidatos con las tres notas registradas.
- El desempate se resuelve por: 1° mejor entrevista → 2° mejor promedio → 3° mejor nota de asignatura.
- Se marcan como `seleccionado` los primeros N según el número de monitores requeridos; el resto como `no_seleccionado`.
- Si la convocatoria estaba `cerrada`, cambia automáticamente a `en_evaluacion`.

---

### HU-24 · Consultar resultados de selección
🔴 Alta | ✅ Implementada

**Como** estudiante, profesor o encargado de facultad,
**quiero** consultar los resultados de selección de una convocatoria,
**para** conocer quiénes fueron seleccionados como monitores y el ranking de puntajes.

**Criterios de aceptación:**
- El estudiante solo ve su propio resultado.
- El profesor y el jefe ven todos los resultados con ranking completo.
- Los resultados se ordenan por puesto (puntaje descendente).

---

## ÉPICA 6 — Prácticas Extramuros

### HU-25 · Crear solicitud de práctica extramural
🔴 Alta | ✅ Implementada

**Como** profesor,
**quiero** registrar una nueva práctica extramural con sus rutas y datos logísticos,
**para** iniciar el proceso de aprobación institucional (RF-PRA-01).

**Criterios de aceptación:**
- Solo se pueden crear prácticas durante las semanas habilitadas en el calendario académico.
- La fecha de inicio debe ser al menos 30 días a partir de hoy.
- Debe incluir al menos una ruta con origen y destino.
- El sistema calcula automáticamente la duración en días y las firmas requeridas (66% de alumnos).
- La práctica se crea en estado `borrador`.
- El tipo de docente (cátedra, planta, ocasional, visitante) es obligatorio.

---

### HU-26 · Enviar práctica a revisión
🔴 Alta | ✅ Implementada

**Como** profesor,
**quiero** enviar mi práctica registrada al jefe de programa para su aprobación,
**para** continuar el proceso logístico.

**Criterios de aceptación:**
- La práctica debe estar en estado `borrador` y tener al menos una ruta.
- Revalida que la fecha de inicio sea al menos 30 días en el futuro.
- Cambia el estado a `solicitada`.
- Notifica automáticamente a todos los jefes de programa.

---

### HU-27 · Aprobar o rechazar práctica extramural
🔴 Alta | ✅ Implementada

**Como** encargado de facultad,
**quiero** aprobar o rechazar solicitudes de prácticas extramuros,
**para** controlar las salidas de campo institucionales.

**Criterios de aceptación:**
- Solo se pueden aprobar/rechazar prácticas en estado `solicitada` o `pendiente_quorum`.
- Al aprobar: si el quórum de firmas ya fue alcanzado, pasa a `aprobado_transporte`; si no, a `pendiente_quorum`.
- Al aprobar con viáticos, se registra el compromiso en el presupuesto del período.
- Al rechazar se registran observaciones opcionales.
- En ambos casos se notifica al profesor.

---

### HU-28 · Firmar consentimiento informado
🔴 Alta | ✅ Implementada

**Como** estudiante,
**quiero** firmar digitalmente el consentimiento informado de una práctica extramural,
**para** confirmar mi participación y cumplir el requisito institucional (RF-PRA-07).

**Criterios de aceptación:**
- Solo se puede firmar en prácticas en estado `solicitada` o `pendiente_quorum`.
- La práctica no debe haber finalizado.
- Solo se puede firmar dentro de la ventana habilitada (entre D-10 y D-5 antes de la fecha de inicio) (RF-PRA-TIME-03).
- El estudiante debe estar matriculado en la asignatura de la práctica.
- No se permiten firmas duplicadas.
- El sistema captura IP y User-Agent como evidencia digital.
- Al alcanzar el quórum (66% de alumnos), la práctica avanza automáticamente a `aprobado_transporte`.

---

### HU-29 · Consultar prácticas extramuros
🟡 Media | ✅ Implementada

**Como** cualquier usuario,
**quiero** ver el listado de prácticas con su estado, quórum y ventana de firma,
**para** hacer seguimiento al proceso.

**Criterios de aceptación:**
- Los profesores ven solo sus prácticas.
- Los estudiantes ven solo las prácticas de las asignaturas en las que están matriculados.
- Cada práctica muestra el porcentaje de quórum alcanzado y si el usuario ya firmó.
- Se puede filtrar por estado y período académico.

---

### HU-30 · Gestionar tarifas de viáticos
🟡 Media | ✅ Implementada

**Como** encargado de facultad,
**quiero** crear y actualizar tarifas de viáticos con valor por día y fecha de vigencia,
**para** que el cálculo de viáticos de prácticas sea automático y actualizado.

**Criterios de aceptación:**
- El valor por día debe ser mayor a 0.
- Se puede activar o desactivar una tarifa.
- Las tarifas activas son visibles para todos los usuarios autenticados.

---

### HU-31 · Calcular viáticos de una práctica
🟡 Media | ✅ Implementada

**Como** profesor, encargado de facultad o encargado de gastos,
**quiero** ver el cálculo estimado de viáticos de una práctica,
**para** tener una referencia presupuestal antes de aprobar (RF-PRA-02/03).

**Criterios de aceptación:**
- Cruza los días de duración y número de alumnos con las tarifas vigentes a la fecha de inicio.
- Retorna el subtotal por tarifa.

---

## ÉPICA 7 — Control Presupuestal

### HU-32 · Crear presupuesto para un período académico
🔴 Alta | ✅ Implementada

**Como** encargado de facultad,
**quiero** crear un presupuesto para un período académico con el monto asignado,
**para** iniciar el proceso de control financiero (RF-PRA-06).

**Criterios de aceptación:**
- No puede existir más de un presupuesto por período.
- Se crea en estado `borrador`.
- El sistema sugiere automáticamente el próximo período sin presupuesto.

---

### HU-33 · Solicitar aprobación del presupuesto
🔴 Alta | ✅ Implementada

**Como** encargado de facultad,
**quiero** enviar la solicitud de presupuesto al encargado de gastos,
**para** obtener la aprobación formal del monto.

**Criterios de aceptación:**
- Solo se puede solicitar desde estado `borrador`, `modificacion` o `rechazado`.
- Cambia el estado a `solicitado`.
- Notifica automáticamente a todos los encargados de gastos con el monto solicitado.

---

### HU-34 · Aprobar o rechazar presupuesto
🔴 Alta | ✅ Implementada

**Como** encargado de gastos,
**quiero** aprobar, rechazar o solicitar modificaciones al presupuesto enviado por el jefe,
**para** controlar el gasto institucional.

**Criterios de aceptación:**
- Solo opera sobre presupuestos en estado `solicitado`.
- Al aprobar: si había incremento pendiente, aplica el nuevo monto; notifica al jefe.
- Al rechazar: si era un incremento, el presupuesto vuelve a `aprobado` (no rechazado); notifica al jefe.
- Al pedir modificación: cambia a estado `modificacion`, limpia incremento pendiente; notifica al jefe con las indicaciones.

---

### HU-35 · Solicitar incremento de presupuesto
🟡 Media | ✅ Implementada

**Como** encargado de facultad,
**quiero** solicitar un incremento a un presupuesto ya aprobado,
**para** cubrir gastos adicionales no previstos.

**Criterios de aceptación:**
- Solo se puede sobre un presupuesto en estado `aprobado`.
- El nuevo monto debe ser mayor al monto actualmente aprobado.
- El monto aprobado no cambia hasta que el encargado de gastos lo apruebe.
- Notifica al encargado de gastos con el diferencial solicitado.

---

### HU-36 · Subir documentos de soporte al presupuesto
🟡 Media | ✅ Implementada

**Como** encargado de facultad,
**quiero** adjuntar documentos de soporte a una solicitud de presupuesto (actas, cotizaciones, etc.),
**para** respaldar la solicitud ante el encargado de gastos.

**Criterios de aceptación:**
- Formatos aceptados: PDF, PNG, JPG, DOCX, XLSX.
- Tipos válidos: `solicitud`, `incremento`, `modificacion`.
- Solo el jefe que subió el documento puede eliminarlo, y solo si el presupuesto no está aprobado.
- Los documentos tienen URL de descarga autenticada.

---

### HU-37 · Consultar movimientos presupuestales
🟡 Media | ✅ Implementada

**Como** encargado de facultad o encargado de gastos,
**quiero** ver el historial de movimientos (compromisos, ejecuciones) de un presupuesto,
**para** hacer trazabilidad del gasto.

**Criterios de aceptación:**
- Los movimientos se ordenan por fecha descendente.
- Incluye tipo, monto, concepto y fecha de cada movimiento.

---

### HU-38 · Configurar calendario académico
🔴 Alta | ✅ Implementada

**Como** encargado de facultad,
**quiero** configurar el calendario del semestre con las fechas y semanas habilitadas para solicitudes,
**para** controlar los períodos en que se pueden abrir convocatorias y registrar prácticas.

**Criterios de aceptación:**
- Cada período tiene una sola configuración de calendario.
- Define fecha de inicio/fin del semestre y rango de semanas habilitadas (ej: semanas 3-14).
- El sistema calcula la semana actual a partir de la fecha de inicio para validar solicitudes.
- El período activo es accesible por todos los roles.

---

## ÉPICA 8 — Reportes y Formularios Oficiales

### HU-39 · Consultar resumen ejecutivo del sistema
🔴 Alta | ✅ Implementada

**Como** encargado de facultad o encargado de gastos,
**quiero** ver un resumen ejecutivo con estadísticas de convocatorias, postulaciones, prácticas y presupuesto,
**para** tomar decisiones informadas y rendir cuentas.

**Criterios de aceptación:**
- Muestra convocatorias agrupadas por estado y períodos disponibles.
- Muestra postulaciones por estado y lista de monitores seleccionados con puntajes.
- Muestra prácticas por estado con detalle de quórum.
- Muestra resumen financiero por período (total, ejecutado, comprometido, disponible, % ejecución).

---

### HU-40 · Generar datos para el formulario FO-14
🔴 Alta | ✅ Implementada

**Como** encargado de facultad o profesor,
**quiero** obtener los datos necesarios para diligenciar el formulario oficial MI-FOR-FO-14 (Requerimiento de Monitores),
**para** cumplir con el proceso administrativo institucional.

**Criterios de aceptación:**
- Incluye datos completos de la convocatoria: sede, tipo de monitoría, descripción de actividades, horas.
- Incluye datos de la asignatura con facultad.
- Incluye datos del docente (nombre, cédula, email).
- Si ya hay monitor seleccionado, incluye sus datos: código, cédula, promedio, notas y puntaje final.
- Muestra el total de postulantes.

---

### HU-41 · Generar datos para el formulario FO-15
🔴 Alta | ✅ Implementada

**Como** encargado de facultad o profesor,
**quiero** obtener los datos necesarios para diligenciar el formulario oficial MI-FOR-FO-15 (Requerimiento de Prácticas Extramuros),
**para** cumplir con el proceso administrativo institucional.

**Criterios de aceptación:**
- Incluye datos de la práctica: tipo de docente, fechas, quórum, firmas.
- Incluye asignatura con facultad y docente.
- Incluye las rutas ordenadas con distancias.
- Lista todos los participantes que firmaron el consentimiento con fecha y hora de firma.
- Detalla los viáticos por tarifa y el total.

---

### HU-42 · Descargar comprobante de consentimiento informado
🟡 Media | ✅ Implementada

**Como** estudiante o personal administrativo,
**quiero** obtener los datos de mi consentimiento firmado en una práctica,
**para** tener constancia del acto de firma con evidencia digital (fecha, IP).

**Criterios de aceptación:**
- El estudiante solo puede acceder si ya firmó el consentimiento.
- Incluye datos del estudiante, práctica, asignatura, docente y puntos de ruta (origen y destino).
- Incluye la fecha/hora de firma y la IP registrada.

---

## ÉPICA 9 — Notificaciones In-App

### HU-43 · Recibir notificaciones del sistema
🔴 Alta | ✅ Implementada

**Como** cualquier usuario,
**quiero** recibir notificaciones dentro del sistema sobre eventos relevantes a mi rol,
**para** estar informado sin necesidad de consultar cada módulo manualmente.

**Criterios de aceptación:**
- Las notificaciones se generan automáticamente para eventos como: convocatoria abierta, práctica solicitada/aprobada/rechazada, presupuesto aprobado/rechazado, etc.
- Se retornan ordenadas por fecha, máximo 50.
- Cada notificación tiene tipo, título, mensaje, estado de lectura y URL de destino.

---

### HU-44 · Gestionar notificaciones leídas
🟢 Baja | ✅ Implementada

**Como** cualquier usuario,
**quiero** marcar notificaciones como leídas (individualmente o todas a la vez) y eliminarlas,
**para** mantener limpia mi bandeja de notificaciones.

**Criterios de aceptación:**
- Se puede marcar una notificación específica como leída.
- Se pueden marcar todas las notificaciones no leídas de una vez.
- Se puede eliminar una notificación individual.
- El conteo de no leídas se actualiza en tiempo real para la UI.

---

## ÉPICA 10 — Seguimiento de Horas de Monitores

### HU-45 · Registrar horas semanales como monitor
🔴 Alta | ✅ Implementada

**Como** estudiante monitor seleccionado,
**quiero** registrar mis horas de trabajo por semana,
**para** llevar el control de mi actividad como monitor.

**Criterios de aceptación:**
- Solo pueden registrar horas los estudiantes con postulación en estado `seleccionado`.
- La semana debe estar entre 1 y 18; las horas entre 0.5 y 40 por semana.
- No se permite registrar dos veces la misma semana.
- La acción queda en el log de auditoría.

---

### HU-46 · Consultar mis horas registradas
🟡 Media | ✅ Implementada

**Como** estudiante monitor,
**quiero** ver el historial de mis horas semanales registradas y el total acumulado,
**para** hacer seguimiento a mi carga de trabajo.

**Criterios de aceptación:**
- Muestra cada semana con sus horas, descripción y si fueron aprobadas por el profesor.
- Incluye el total acumulado de horas.
- Incluye los datos de la convocatoria y asignatura.

---

### HU-47 · Aprobar horas de monitores
🟡 Media | ✅ Implementada

**Como** profesor,
**quiero** aprobar los registros de horas de mis monitores semana a semana,
**para** validar oficialmente la carga de trabajo reportada.

**Criterios de aceptación:**
- El profesor solo puede aprobar horas de monitores pertenecientes a sus propias convocatorias.
- Al aprobar, registra quién aprobó y en qué momento (audit log).
- El `encargado_facultad` puede aprobar horas de cualquier monitor.

---

### HU-48 · Consultar horas de todos los monitores de una convocatoria
🟡 Media | ✅ Implementada

**Como** profesor o encargado de facultad,
**quiero** ver un resumen de horas por monitor en una convocatoria,
**para** supervisar el cumplimiento de cada monitor.

**Criterios de aceptación:**
- Lista solo los monitores seleccionados de la convocatoria.
- Muestra total de horas y detalle semanal con estado de aprobación.

---

### HU-49 · Consultar log de auditoría
🟡 Media | ✅ Implementada

**Como** administrador, encargado de facultad o encargado de gastos,
**quiero** consultar el registro de auditoría del sistema con las acciones recientes,
**para** supervisar el uso del sistema y detectar acciones indebidas.

**Criterios de aceptación:**
- Registra acciones críticas: login, reset de contraseña, activación/desactivación de usuarios, aprobación de horas, etc.
- Se pueden consultar hasta 1000 entradas (por defecto 100).
- Cada entrada incluye usuario, rol, acción, entidad, ID y timestamp.

---

## ÉPICA 11 — Costos de Transporte

### HU-50 · Consultar precios de combustible vigentes
🟡 Media | ✅ Implementada

**Como** cualquier usuario autenticado,
**quiero** consultar los precios de combustible actualizados para el departamento de Huila,
**para** tener una referencia al calcular costos de transporte de prácticas.

**Criterios de aceptación:**
- Muestra un precio por tipo de combustible (gasolina corriente, diésel, extra).
- Los precios provienen de SICOM y se actualizan cada 24 horas.
- Incluye la fecha de vigencia y la fuente del precio.

---

### HU-51 · Consultar peajes en rutas nacionales
🟡 Media | ✅ Implementada

**Como** cualquier usuario autenticado,
**quiero** consultar los peajes activos con sus tarifas por categoría de vehículo,
**para** incluirlos en el presupuesto de transporte de prácticas.

**Criterios de aceptación:**
- Incluye todos los peajes activos con coordenadas GPS, corredor vial y tarifas por categoría (1 a 5).
- Permite filtrar por departamento y corredor.
- Fuente: base de datos INVIAS / ANI 2024-2025.

---

### HU-52 · Calcular costo de transporte de un trayecto
🔴 Alta | ✅ Implementada

**Como** cualquier usuario autenticado,
**quiero** calcular el costo estimado de transporte entre dos puntos,
**para** planificar el presupuesto de una práctica extramural.

**Criterios de aceptación:**
- Usa OpenRouteService (ORS) para obtener la distancia y ruta real cuando está configurado.
- Calcula costo de combustible usando precio SICOM y rendimiento del vehículo (bus/camioneta/moto).
- Detecta peajes en la ruta: geográficamente si hay coordenadas ORS, o por municipio si no.
- El resultado incluye desglose de combustible, peajes y totales.
- Si ORS no está configurado, el cálculo opera en modo degradado con distancias aproximadas.

---

### HU-53 · Calcular costos de transporte de una práctica registrada
🔴 Alta | ✅ Implementada

**Como** cualquier usuario autenticado,
**quiero** calcular el costo completo de transporte para una práctica extramural registrada,
**para** obtener un presupuesto integral que incluya todos los rubros.

**Criterios de aceptación:**
- Usa las rutas registradas en la práctica para calcular el total de kilómetros.
- Incluye: combustible (diésel, precio SICOM), peajes detectados, tarifa de conductor por día ($180.000 COP) y seguro por pasajero ($15.000 COP/estudiante).
- El desglose es detallado por cada rubro.

---

### HU-54 · Consultar parámetros generales de transporte
🟢 Baja | ✅ Implementada

**Como** cualquier usuario autenticado,
**quiero** consultar los parámetros base del módulo de transporte (rendimientos, tarifas, precios),
**para** entender las constantes usadas en los cálculos.

**Criterios de aceptación:**
- Muestra precios de combustible vigentes, rendimiento km/litro por tipo de vehículo, tarifa de conductor y seguro por pasajero.
- Muestra el total de peajes activos en la base de datos y su fuente.

---

## Resumen por Épica

| Épica | Total HU | Implementadas |
|---|---|---|
| E1 — Autenticación y Usuarios | 8 | 8 ✅ |
| E2 — Asignaturas | 3 | 3 ✅ |
| E3 — Convocatorias | 4 | 4 ✅ |
| E4 — Postulaciones | 7 | 7 ✅ |
| E5 — Selección de Monitores | 2 | 2 ✅ |
| E6 — Prácticas Extramuros | 7 | 7 ✅ |
| E7 — Presupuesto | 7 | 7 ✅ |
| E8 — Reportes y Formularios | 4 | 4 ✅ |
| E9 — Notificaciones | 2 | 2 ✅ |
| E10 — Horas de Monitor | 5 | 5 ✅ |
| E11 — Transporte | 5 | 5 ✅ |
| **TOTAL** | **54** | **54 ✅** |

---

*Documento generado a partir del código fuente implementado del backend SIPAM-USCO.*
