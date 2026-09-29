# 01. Especificación funcional

**Estado:** requerimientos funcionales aprobados para separación por rol y Fase 5. Fase 5 añade asistencias, catálogo/asignación de evaluaciones y notas no psicométricas con historial. El sistema aún no incorpora formularios psicométricos: todos los candidatos documentados siguen pendientes de autorización profesional/institucional, versión exacta, derechos y regla de puntuación. Las capacidades sin ruta o pantalla continúan pendientes.

## Propósito y alcance

SICOSE apoyará el seguimiento, capacitación y evaluación periódica de voluntarios de rescate y emergencias. El prototipo tendrá autenticación, permisos por rol, perfiles, seis evaluaciones, períodos con ponderaciones versionadas, historial y reportes. La IA se reserva como integración futura, sin generar predicciones en esta fase.

## Roles y permisos

| Capacidad | Administrador | Jefe de Personal | Instructor Voluntario |
|---|---:|---:|---:|
| Iniciar sesión y abrir su dashboard por rol | Sí | Sí | Sí |
| Administrar todas las cuentas y evaluaciones | Sí | No | No |
| CRUD de voluntarios activos de su ámbito | Todos los voluntarios | Sí, solo voluntarios asignados; baja lógica, sin borrado físico | No |
| Editar datos personales | Todas las cuentas | Perfil de voluntario dentro de su ámbito | Solo su propio perfil |
| Ver estado/avance de evaluaciones | Todos | Voluntarios de su ámbito | Evaluaciones propias completadas y pendientes |
| Ver resultados psicométricos de voluntarios | Sí, administración global | Sí, solo voluntarios autorizados | No |
| Modificar notas/resultados psicométricos | Gestión administrativa global, con auditoría | No | No |
| Activar/desactivar una prueba psicométrica por voluntario | Sí | Sí, dentro de su ámbito | No |
| Registrar notas de evaluación física, cursos y desempeño | Sí | Sí, para su ámbito | No |
| Editar calificaciones u observaciones | Sí, sujeto a historial y auditoría | Solo calificaciones no psicométricas de su ámbito; psicométricas no | No |
| Ver notas u observaciones individuales | Sí, según autorización institucional | Sí, para voluntarios de su ámbito | No |

Una solicitud de registro o usuario invitado se mantiene `pendiente` hasta aprobación. Las rutas API deben denegar datos protegidos y evaluaciones antes de esa aprobación. La autorización se aplica en backend a cada recurso, no solo ocultando controles. Tras autenticarse, cada cuenta se dirige al dashboard correspondiente a su rol: Administrador, Jefe de Personal o Instructor Voluntario; no se comparte un dashboard con contenido intercambiado por URL.

El dashboard administrativo ofrece control global de cuentas y evaluaciones. El dashboard del Jefe de Personal se limita a sus voluntarios activos asignados, sus evaluaciones y resultados autorizados y el registro de notas no psicométricas. El dashboard del Instructor Voluntario permite actualizar sus datos personales, consultar qué evaluaciones propias están completadas o pendientes y ver un resumen limitado, sin editar calificaciones.

El resumen del Instructor Voluntario muestra solamente estado y avance. No expone notas/calificaciones, resultados individuales ni observaciones.

## Flujos principales

1. Administrador crea un período, confirma pesos que suman 100% y administra usuarios y Jefes de Personal.
2. Un Instructor Voluntario solicita alta o ingresa con código de invitación; el administrador aprueba o rechaza. No se concede sesión protegida al estado pendiente.
3. Una cuenta autenticada es redirigida al dashboard exclusivo de su rol. Administración gestiona globalmente las cuentas y evaluaciones.
4. Jefe de Personal da de alta/edita/desactiva voluntarios activos de su ámbito, consulta evaluaciones/resultados permitidos, registra notas físicas, de cursos y desempeño, y activa/desactiva pruebas psicométricas por voluntario sin poder alterar sus notas.
5. El Instructor Voluntario puede editar sus propios datos personales, ve evaluaciones completadas/pendientes y resumen permitido, pero no edita calificaciones.
6. El Instructor Voluntario completa cada prueba habilitada. Reiniciar crea intento nuevo y conserva el anterior.
7. El sistema calcula avance y promedio ponderado solo con una regla de datos faltantes previamente aprobada; hasta entonces el promedio aparece como no disponible si no están todas las notas requeridas.
8. Usuarios autorizados descargan reportes PDF individuales/consolidados y Excel según permisos.

## Evaluaciones y calificaciones

Seis componentes por período: psicométrica 1, 2 y 3 (autoinforme); física; rendimiento académico; criterio del instructor. Escala institucional propuesta de 0–100. Pesos iniciales configurables: 10%, 10%, 10%, 25%, 15%, 30%. La configuración es una hipótesis inicial para aprobar, no una ponderación validada científicamente. Fase 5 no carga reactivos, procesa respuestas ni habilita candidatos pendientes. El flujo manual rechaza calificaciones de categoría psicométrica.

La nota 0 debe distinguirse de “sin evaluar”. Cada calificación guarda autor, fecha, período, evaluación y versión del peso aplicable. Los cambios de peso generan versión nueva, no reescriben resultados históricos. Intentos guardan inicio, envío, estado y puntuación oficial/normalizada si está aprobada.

## Perfil y seguimiento

Datos del voluntario: identidad mínima necesaria, estado, instructor responsable, experiencia en operaciones, antigüedad, cursos/capacitaciones y asistencia. La retención y visibilidad de cada campo necesita política institucional. Registrar auditoría para aprobación de usuarios, reasignaciones, cambios de nota/pesos, estados de pruebas y generación/revisión de informes.

## Reportes

PDF individual, PDF consolidado y Excel: datos necesarios, notas por componente, avance, promedio cuando calculable, observaciones autorizadas y fechas. El reporte no incluye respuestas psicométricas salvo necesidad profesional y aprobación explícita. Sección IA queda omitida/no disponible hasta la existencia de modelo validado; no mostrar recomendaciones ficticias.

## Fuera de alcance inicial

Aplicación de instrumentos no aprobados, diagnóstico, decisión automática de permanencia, integración de modelo/dataset, sincronización con terceros, pagos, firma electrónica, portal público de resultados y analítica predictiva.

## Criterios funcionales de aceptación futuros

- Después de autenticarse, cada usuario llega a su dashboard correspondiente; no puede abrir dashboards o datos de otro rol.
- Jefe de Personal solo consulta y opera voluntarios activos asignados; puede registrar notas no psicométricas y activar/desactivar pruebas, pero no modificar resultados psicométricos.
- Instructor Voluntario edita únicamente su perfil personal, consulta estados/avance propios y nunca accede a notas, resultados individuales u observaciones.
- Un usuario pendiente no obtiene datos privados ni puede iniciar evaluaciones.
- Un Instructor Voluntario no puede leer/alterar recursos de otra persona mediante URL o API.
- Reintentar una evaluación conserva todos los intentos previos.
- Una nueva versión de ponderación no modifica períodos o resultados cerrados.
- Los roles y acciones sensibles quedan comprobables mediante auditoría.
- Interfaz usable en móvil y escritorio, con estados vacíos, carga y error comprensibles.
