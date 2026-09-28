# 01. Especificación funcional

**Estado:** especificación de producto. En Fase 2 quedaron implementados el esquema base, login/sesión y comprobación de roles; los demás flujos de esta especificación son objetivos pendientes. No constituye política institucional aprobada.

## Propósito y alcance

SICOSE apoyará el seguimiento, capacitación y evaluación periódica de voluntarios de rescate y emergencias. El prototipo tendrá autenticación, permisos por rol, perfiles, seis evaluaciones, períodos con ponderaciones versionadas, historial y reportes. La IA se reserva como integración futura, sin generar predicciones en esta fase.

## Roles y permisos

| Capacidad | Administrador | Instructor autorizado | Voluntario |
|---|---:|---:|---:|
| Gestionar usuarios, instructores, períodos y ponderaciones | Sí | No | No |
| Crear, editar, desactivar y reasignar voluntarios | Sí | Sí, dentro de su ámbito | No |
| Eliminar definitivamente voluntarios | No como operación ordinaria; preservar historial | No | No |
| Habilitar, deshabilitar y reiniciar pruebas | Sí | Sí, según asignación | No |
| Registrar notas físicas, académicas y de criterio | Sí | Sí, según asignación | No |
| Ver sus evaluaciones y resultados | Sí, con auditoría | Sí, según asignación | Solo propios |
| Ver resultados psicométricos | Sí, con acceso auditado | Solo voluntarios autorizados | Solo propios |
| Solicitar informe de análisis IA | Futuro | Futuro y explícito | No |

Una solicitud de registro o usuario invitado se mantiene `pendiente` hasta aprobación. Las rutas API deben denegar datos protegidos y evaluaciones antes de esa aprobación. La autorización se aplica en backend a cada recurso, no solo ocultando controles.

## Flujos principales

1. Administrador crea un período, confirma pesos que suman 100% y administra usuarios/instructores.
2. Un voluntario solicita alta o ingresa con código de invitación; el administrador aprueba o rechaza. No se concede sesión protegida al estado pendiente.
3. Instructor autorizado crea/edita/desactiva/reasigna voluntarios y habilita evaluaciones psicométricas aprobadas.
4. El voluntario completa cada prueba habilitada. Reiniciar crea intento nuevo y conserva el anterior.
5. Instructor registra notas y observaciones de evaluación física, rendimiento académico y criterio del instructor.
6. El sistema calcula avance y promedio ponderado solo con una regla de datos faltantes previamente aprobada; hasta entonces el promedio aparece como no disponible si no están todas las notas requeridas.
7. Usuarios autorizados descargan reportes PDF individuales/consolidados y Excel según permisos.

## Evaluaciones y calificaciones

Seis componentes por período: psicométrica 1, 2 y 3 (autoinforme); física; rendimiento académico; criterio del instructor. Escala institucional propuesta de 0–100. Pesos iniciales configurables: 10%, 10%, 10%, 25%, 15%, 30%. La configuración es una hipótesis inicial para aprobar, no una ponderación validada científicamente.

La nota 0 debe distinguirse de “sin evaluar”. Cada calificación guarda autor, fecha, período, evaluación y versión del peso aplicable. Los cambios de peso generan versión nueva, no reescriben resultados históricos. Intentos guardan inicio, envío, estado y puntuación oficial/normalizada si está aprobada.

## Perfil y seguimiento

Datos del voluntario: identidad mínima necesaria, estado, instructor responsable, experiencia en operaciones, antigüedad, cursos/capacitaciones y asistencia. La retención y visibilidad de cada campo necesita política institucional. Registrar auditoría para aprobación de usuarios, reasignaciones, cambios de nota/pesos, estados de pruebas y generación/revisión de informes.

## Reportes

PDF individual, PDF consolidado y Excel: datos necesarios, notas por componente, avance, promedio cuando calculable, observaciones autorizadas y fechas. El reporte no incluye respuestas psicométricas salvo necesidad profesional y aprobación explícita. Sección IA queda omitida/no disponible hasta la existencia de modelo validado; no mostrar recomendaciones ficticias.

## Fuera de alcance inicial

Aplicación de instrumentos no aprobados, diagnóstico, decisión automática de permanencia, integración de modelo/dataset, sincronización con terceros, pagos, firma electrónica, portal público de resultados y analítica predictiva.

## Criterios funcionales de aceptación futuros

- Un usuario pendiente no obtiene datos privados ni puede iniciar evaluaciones.
- Un voluntario no puede leer/alterar recursos de otra persona mediante URL o API.
- Reintentar una evaluación conserva todos los intentos previos.
- Una nueva versión de ponderación no modifica períodos o resultados cerrados.
- Los roles y acciones sensibles quedan comprobables mediante auditoría.
- Interfaz usable en móvil y escritorio, con estados vacíos, carga y error comprensibles.
