# HISTORIAS DE USUARIO — SIPAM
*(Formato: Historias Usuario.xls.xlsx — PMOInformatica)*

**Encabezados del Excel:**
`ID | Rol | Característica/Funcionalidad | Razón/Resultado | N° Escenario | Criterio de Aceptación | Contexto | Evento | Resultado/Comportamiento esperado`

---

## MÓDULO: AUTENTICACIÓN

| ID | Rol | Característica / Funcionalidad | Razón / Resultado |
|----|-----|-------------------------------|-------------------|
| **HU-001** | Como un **Usuario del sistema** | Necesito iniciar sesión con mi código institucional y contraseña | Con la finalidad de acceder a las funciones del sistema según mi rol |

**Criterios de Aceptación HU-001:**
| N° | Título | Contexto | Evento | Resultado esperado |
|----|--------|---------|--------|-------------------|
| 1 | Login exitoso | En caso de que las credenciales sean válidas y el usuario esté activo | Cuando ingrese código y contraseña correctos y haga clic en "Ingresar" | El sistema muestra el panel principal según el rol del usuario |
| 2 | Credenciales inválidas | En caso de que la contraseña sea incorrecta | Cuando ingrese credenciales erróneas | El sistema muestra mensaje de error y no permite el acceso |
| 3 | Cuenta inactiva | En caso de que el usuario esté desactivado | Cuando intente iniciar sesión | El sistema muestra "Usuario inactivo. Contacte al administrador" |
| 4 | Bloqueo por fuerza bruta | En caso de 5 intentos fallidos consecutivos | Cuando supere el límite de intentos | El sistema bloquea temporalmente la cuenta y registra el intento |

---

## MÓDULO: MONITORÍAS — CONVOCATORIAS

| ID | Rol | Característica / Funcionalidad | Razón / Resultado |
|----|-----|-------------------------------|-------------------|
| **HU-002** | Como un **Profesor** | Necesito crear una convocatoria de monitoría para mi asignatura | Con la finalidad de formalizar el proceso de selección de monitores según el Acuerdo 012/2023 |

**Criterios de Aceptación HU-002:**
| N° | Título | Contexto | Evento | Resultado esperado |
|----|--------|---------|--------|-------------------|
| 1 | Convocatoria creada exitosamente | Estando en el período habilitado del calendario académico | Cuando complete el formulario con datos válidos y haga clic en "Crear" | La convocatoria queda en estado "borrador" y aparece en mi lista |
| 2 | Período no habilitado | En caso de que el calendario no permita convocatorias | Cuando intente crear la convocatoria fuera del período | El sistema rechaza con mensaje indicando semanas habilitadas |
| 3 | Convocatoria duplicada | En caso de que ya exista una convocatoria activa para esa asignatura en el período | Cuando intente crear una nueva | El sistema rechaza indicando la convocatoria existente (ID) |
| 4 | Ventana de postulación inválida | En caso de que la fecha fin sea anterior a la de inicio | Cuando ingrese fechas inválidas | El sistema muestra error de validación |

| **HU-003** | Como un **Jefe de Programa** | Necesito publicar una convocatoria (cambiar estado a "abierta") | Con la finalidad de permitir que los estudiantes puedan postularse |

**Criterios de Aceptación HU-003:**
| N° | Título | Contexto | Evento | Resultado esperado |
|----|--------|---------|--------|-------------------|
| 1 | Publicación exitosa | Convocatoria en estado "borrador" y período habilitado | Cuando haga clic en "Publicar" | Estado cambia a "abierta" y todos los estudiantes elegibles reciben notificación |
| 2 | Fecha inicio pasada | Fecha de inicio de postulación ya pasó | Cuando intente publicar | El sistema rechaza con mensaje "Actualice las fechas antes de publicar" |
| 3 | Cerrar convocatoria | Convocatoria en estado "abierta" | Cuando seleccione "Cerrar" | Estado cambia a "cerrada" |

---

## MÓDULO: MONITORÍAS — POSTULACIONES

| ID | Rol | Característica / Funcionalidad | Razón / Resultado |
|----|-----|-------------------------------|-------------------|
| **HU-004** | Como un **Estudiante** | Necesito postularme a una convocatoria de monitoría abierta | Con la finalidad de participar en el proceso de selección como monitor |

**Criterios de Aceptación HU-004:**
| N° | Título | Contexto | Evento | Resultado esperado |
|----|--------|---------|--------|-------------------|
| 1 | Postulación exitosa | Convocatoria abierta, estudiante cumple requisitos académicos | Cuando complete la carta de motivación y envíe la postulación | Postulación en estado "pendiente", aparece en "Mis postulaciones" |
| 2 | Sin promedio suficiente | Promedio del estudiante < promedio mínimo de la convocatoria | Cuando intente postularse | El sistema rechaza mostrando el motivo específico |
| 3 | Postulación duplicada | El estudiante ya tiene una postulación activa | Cuando intente postularse de nuevo | El sistema rechaza con estado 409 |
| 4 | Convocatoria cerrada | La convocatoria no está en estado "abierta" | Cuando intente postularse | El sistema rechaza con mensaje de estado |

| **HU-005** | Como un **Estudiante** | Necesito subir mis documentos de postulación (cédula, RUT, certificado bancario) | Con la finalidad de completar mi postulación y avanzar en el proceso de evaluación |

**Criterios de Aceptación HU-005:**
| N° | Título | Contexto | Evento | Resultado esperado |
|----|--------|---------|--------|-------------------|
| 1 | Documento subido exitosamente | Postulación activa, archivo PDF válido | Cuando seleccione el tipo de documento y adjunte el archivo | Documento almacenado, contador de documentos actualizado |
| 2 | Documentos completos | 3 documentos subidos (cédula + RUT + certificado) | Al subir el tercer documento | Postulación marcada como "documentos_completos" |
| 3 | Archivo inválido | Archivo no es PDF o supera 5MB | Cuando intente subir el archivo | El sistema rechaza mostrando el error de validación |

| **HU-006** | Como un **Estudiante** | Necesito retirar mi postulación | Con la finalidad de desistir del proceso antes de la selección final |

**Criterios de Aceptación HU-006:**
| N° | Título | Contexto | Evento | Resultado esperado |
|----|--------|---------|--------|-------------------|
| 1 | Desistimiento exitoso | Postulación activa, convocatoria abierta o cerrada | Cuando confirme el desistimiento | Postulación pasa a "desistido", el profesor recibe notificación |
| 2 | Desistimiento post-selección | Postulación ya fue seleccionada o rechazada | Cuando intente desistir | El sistema rechaza indicando que no es posible después de la selección |

---

## MÓDULO: MONITORÍAS — SELECCIÓN

| ID | Rol | Característica / Funcionalidad | Razón / Resultado |
|----|-----|-------------------------------|-------------------|
| **HU-007** | Como un **Profesor** | Necesito registrar las notas de asignatura y entrevista de los postulantes | Con la finalidad de alimentar el algoritmo de selección con los datos necesarios |

**Criterios de Aceptación HU-007:**
| N° | Título | Contexto | Evento | Resultado esperado |
|----|--------|---------|--------|-------------------|
| 1 | Nota registrada | Postulación activa de mi convocatoria | Cuando ingrese la nota (0.0-5.0) y guarde | Nota almacenada, puntaje calculable |
| 2 | Nota inválida | Nota fuera del rango 0.0-5.0 | Cuando ingrese un valor inválido | El sistema rechaza con error de validación |

| **HU-008** | Como un **Profesor** | Necesito ejecutar el algoritmo de selección de monitores | Con la finalidad de determinar quién será el monitor según los criterios del Acuerdo 012/2023 |

**Criterios de Aceptación HU-008:**
| N° | Título | Contexto | Evento | Resultado esperado |
|----|--------|---------|--------|-------------------|
| 1 | Selección ejecutada | Convocatoria cerrada, todos los candidatos con notas | Cuando haga clic en "Ejecutar selección" | Se muestran los resultados ordenados, top N marcados como "seleccionado" |
| 2 | Sin candidatos con notas | Ningún postulante tiene notas completas | Cuando intente ejecutar | El sistema rechaza indicando que faltan notas |

---

## MÓDULO: PRÁCTICAS EXTRAMUROS

| ID | Rol | Característica / Funcionalidad | Razón / Resultado |
|----|-----|-------------------------------|-------------------|
| **HU-009** | Como un **Profesor** | Necesito crear una solicitud de práctica extramural | Con la finalidad de formalizar el proceso de aprobación institucional según el Acuerdo 003/2012 |

**Criterios de Aceptación HU-009:**
| N° | Título | Contexto | Evento | Resultado esperado |
|----|--------|---------|--------|-------------------|
| 1 | Práctica creada | Período habilitado, 30+ días de antelación | Cuando complete el formulario y guarde | Práctica en estado "borrador" con rutas e itinerario |
| 2 | Sin antelación mínima | Fecha de inicio < 30 días desde hoy | Cuando intente crear | El sistema rechaza indicando la fecha mínima permitida |
| 3 | Duración excedida | Duración > 3 días (Huila) o > 4 días (fuera) | Cuando ingrese fechas | El sistema rechaza con límite de duración |

| **HU-010** | Como un **Profesor** | Necesito solicitar la aprobación de mi práctica al Comité de Currículo | Con la finalidad de iniciar el flujo de aprobación institucional |

**Criterios de Aceptación HU-010:**
| N° | Título | Contexto | Evento | Resultado esperado |
|----|--------|---------|--------|-------------------|
| 1 | Solicitud enviada | Práctica en borrador con al menos una ruta | Cuando haga clic en "Solicitar aprobación" | Estado pasa a "solicitada", jefe de programa recibe notificación |
| 2 | Sin rutas definidas | Práctica sin itinerario | Cuando intente solicitar | El sistema rechaza indicando que debe agregar al menos una ruta |

| **HU-011** | Como un **Estudiante** | Necesito firmar el consentimiento informado para participar en la práctica | Con la finalidad de autorizar legalmente mi participación en la actividad extramural |

**Criterios de Aceptación HU-011:**
| N° | Título | Contexto | Evento | Resultado esperado |
|----|--------|---------|--------|-------------------|
| 1 | Firma exitosa | Dentro de ventana D-10 a D-5, matriculado en asignatura | Cuando haga clic en "Firmar consentimiento" | Firma registrada con IP y timestamp, contador actualizado |
| 2 | Fuera de ventana | Antes de D-10 o después de D-5 | Cuando intente firmar | El sistema indica fecha de disponibilidad |
| 3 | Quórum alcanzado | Al firmar la última persona necesaria (≥66%) | Cuando se registre la última firma requerida | Práctica avanza automáticamente a "aprobada_curriculo" |

| **HU-012** | Como un **Jefe de Programa** | Necesito aprobar o rechazar una práctica en nombre del Comité de Currículo | Con la finalidad de dar el primer aval institucional |

**Criterios de Aceptación HU-012:**
| N° | Título | Contexto | Evento | Resultado esperado |
|----|--------|---------|--------|-------------------|
| 1 | Aprobación con quórum | Práctica solicitada con ≥66% firmas | Cuando apruebe | Estado pasa a "aprobada_curriculo", decano notificado |
| 2 | Pre-aprobación sin quórum | Práctica solicitada sin quórum suficiente | Cuando apruebe | Estado pasa a "pendiente_quorum", profesor notificado |
| 3 | Rechazo con observaciones | Práctica solicitada o pendiente quórum | Cuando rechace con motivo | Estado pasa a "rechazada", profesor recibe motivo |

| **HU-013** | Como un **Profesor** | Necesito confirmar el inicio de la práctica el día programado y subir el informe final | Con la finalidad de registrar la ejecución y cumplir con la entrega del informe (Art. 7 Acuerdo 003/2012) |

**Criterios de Aceptación HU-013:**
| N° | Título | Contexto | Evento | Resultado esperado |
|----|--------|---------|--------|-------------------|
| 1 | Inicio confirmado | Estado "aprobado_transporte", fecha de inicio llegó | Cuando haga clic en "Confirmar inicio" | Estado pasa a "en_ejecucion", jefe de programa notificado |
| 2 | Informe entregado a tiempo | En ejecución, dentro de 5 días hábiles post-práctica | Cuando envíe el informe | Estado pasa a "finalizada", proceso concluido |
| 3 | Informe fuera de plazo | Más de 5 días hábiles después de fecha_fin | Cuando intente subir informe | El sistema rechaza indicando días de plazo vencido |

---

## MÓDULO: INTELIGENCIA ARTIFICIAL

| ID | Rol | Característica / Funcionalidad | Razón / Resultado |
|----|-----|-------------------------------|-------------------|
| **HU-014** | Como un **Estudiante** | Necesito ver convocatorias recomendadas por el sistema de IA | Con la finalidad de identificar rápidamente las oportunidades donde tengo mayor probabilidad de ser seleccionado como monitor |

**Criterios de Aceptación HU-014:**
| N° | Título | Contexto | Evento | Resultado esperado |
|----|--------|---------|--------|-------------------|
| 1 | Recomendaciones con IA | Servicio Flask disponible, existen convocatorias abiertas elegibles | Cuando acceda a la página de convocatorias | Widget muestra recomendaciones ordenadas con % de probabilidad (fuente: modelo_ia) |
| 2 | Recomendaciones heurísticas | Servicio IA no disponible | Cuando acceda a la página de convocatorias | Widget muestra recomendaciones ordenadas con scoring heurístico (fuente: heuristica) |
| 3 | Sin recomendaciones | No hay convocatorias elegibles o ya se postuló a todas | Cuando acceda | Widget no se muestra o indica "sin recomendaciones disponibles" |
| 4 | Match de programa | La convocatoria es de su mismo programa académico | En cualquier caso | La convocatoria aparece destacada primero en la lista |

---

## MÓDULO: GENERACIÓN DE PDFs

| ID | Rol | Característica / Funcionalidad | Razón / Resultado |
|----|-----|-------------------------------|-------------------|
| **HU-015** | Como un **Jefe de Programa / Decano** | Necesito descargar los formularios institucionales FO-14, FO-15 y FO-16 generados automáticamente | Con la finalidad de contar con la documentación oficial para el proceso de aprobación y archivo |

**Criterios de Aceptación HU-015:**
| N° | Título | Contexto | Evento | Resultado esperado |
|----|--------|---------|--------|-------------------|
| 1 | FO-14 descargado | Convocatoria finalizada con datos completos | Cuando haga clic en "Descargar FO-14" | PDF descargado con datos de convocatoria, asignatura, docente y monitor seleccionado |
| 2 | FO-16 descargado | Práctica con rutas y datos FO-16 | Cuando haga clic en "Descargar FO-16" | PDF con justificación de práctica, itinerario, criterios de evaluación |
| 3 | FO-15 descargado | Práctica con lista de firmas | Cuando haga clic en "Descargar FO-15" | PDF con lista de participantes y firmas de consentimiento |
| 4 | PDF no disponible | ID de convocatoria o práctica no existe | Cuando intente descargar | El sistema retorna error 404 con mensaje descriptivo |
