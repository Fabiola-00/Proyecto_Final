# 10. Reformulación de evaluaciones y formación

Fecha de acuerdos: **2026-10-12**. Estado: **entregas v17–v22 y 5B.1–5B.4 implementadas técnicamente; aceptación operativa/institucional pendiente**. Esta revisión sustituye los acuerdos anteriores incompatibles de Fase 5B; no modifica retrospectivamente configuraciones publicadas ni notas. El alcance del Jefe y retiro operativo del Comandante quedan implementados en v17. La evidencia de 77 pruebas del 2026-10-11 es histórica, no una ejecución de esta revisión.

## Reglas confirmadas

1. El rol Comandante dejará de utilizarse. Administrador/Jefe ingresarán su aportación de Desempeño; se conservarán por separado nombre del Comandante evaluador y autor de transcripción/corrección. Cuentas y notas históricas no se eliminarán ni reasignarán silenciosamente.
2. Un solo Jefe de Personal, con todos los Instructores Voluntarios bajo su mando sin necesidad de asignación. Inactivos consultables en historial/reportes; nuevas habilitaciones y notas bloqueadas hasta reactivar. Alcance global confirmado también para personal, asistencia, operaciones, evaluaciones y cursos. No modifica las operaciones que cada rol puede ejecutar: eventos de operaciones siguen creados/editados por Administrador; Jefe vincula participantes activos sin filtro de asignación.
3. Habilitación individual por evaluación/persona/gestión. Deshabilitar conserva notas/historial y bloquea nuevas acciones. Tabla por gestión con activos/inactivos y consulta modal de finalizadas/pendientes/no cumplidas.
4. Dos fechas físicas comunes por gestión, reprogramación extraordinaria individual y fecha de cierre anual. Formación acumulada durante el año; dos aportaciones independientes de Desempeño.
5. Física pendiente sin nota; Administrador/Jefe confirman No cumplida con cero, pudiendo reprogramar. Durante la reprogramación conserva cero hasta registrar cumplimiento/corrección. Promedio de las dos físicas. Esta regla sustituye el tratamiento previo que impedía calcular ante cualquier física no realizada; no convierte pendientes en cero automáticamente.
6. Instructor consulta solo notas físicas individuales/promedio, notas de sus cursos y acumulado académico, después de publicación administrativa. No consulta Desempeño ni resultado conjunto. Observaciones ajenas siguen excluidas. Administrador/Jefe publican; una corrección conserva visible la versión publicada anterior y su fecha hasta republicar. Publicación/republicación implementada en [5B.3](15_publicacion_notas.md), parcial y con ocultación por deshabilitación/retiro confirmada en esa entrega.
7. Puntaje del curso: puntos enteros que gana cada participante al finalizar. Académica acumulativa; sustituye la nota global manual anterior para el alcance nuevo. Tope académico confirmado: 100. Administrador/Jefe pueden asignar puntos individuales distintos del puntaje del curso; se imputa una sola vez a la gestión de la fecha de finalización personal. Acumulación y fórmula reproducible implementadas mediante opt-in v2 en [5B.2](14_calculos_y_gestiones.md); no convertir notas globales históricas automáticamente.
8. Cursos creados/editados por Administrador/Jefe; asignación personal sin duplicados y estados Asignado, En curso, Finalizado, No completado. Administrador/Jefe confirman finalización y nota individual cuando corresponda. Correcciones con historial; finalizar catálogo no finaliza automáticamente a participantes.
9. Tipos: Capacitación, Especialización, Actualización, Taller, Seminario (Webinar). Campos: entidad, nombre, inicio/fin, puntaje y observaciones adicionales opcionales. Nombre/tipo/entidad/fechas/puntaje obligatorios para cursos nuevos; puntaje base e individual de 0 a 100 enteros, confirmado por el solicitante. Observaciones opcionales; históricos sin completar no se rellenan automáticamente. Estado derivado de fecha de Bolivia: Próximo antes del inicio (amarillo), En curso entre inicio y fin inclusive (verde), Finalizado después del fin (rojo). Históricos sin fechas conservados como incompletos, sin inventar fechas. Texto acompaña al color.
10. Avance sobre evaluaciones habilitadas de la gestión; finalizadas y no cumplidas cuentan como resueltas. Mostrar finalizadas, pendientes y no cumplidas separadas. Sin evaluaciones habilitadas: no asignar un porcentaje de cumplimiento ficticio. PDF consolidado para Administrador/Jefe con habilitación, estados y notas incluyendo Desempeño, carimbo SBRAB y ámbito autorizado.
11. Psicometría aún en desarrollo: habilitación por persona no acredita autorización de instrumentos ni abre formularios. Conservar requisitos institucionales/profesionales, licencia, idioma, puntuación, intentos y retención.

## Respuestas complementarias confirmadas

- Acumulado académico entero limitado a 100; mantener el detalle de puntos de cada formación, sin borrar lo que exceda el tope del componente.
- Puntos individuales editables por Administrador/Jefe. Finalización personal define la gestión de cómputo; no repetir puntos en otra gestión.
- Jefe único con alcance global también para personal, asistencia y operaciones, sin requerir asignación al Jefe.
- Administrador **y Jefe** publican las notas permitidas al Instructor. Correcciones pendientes de republicar mantienen visible la versión publicada anterior y su fecha.

Estos acuerdos sustituyen los pendientes equivalentes de la revisión inicial. No alteran aprobaciones institucionales ni autorizan psicometría.

## Secuencia propuesta

1. **Implementado v17:** ajustar autorización/entrada de Desempeño sin rol Comandante activo, preservando identidad y autoría; implementar tabla por gestión y habilitación individual, con consulta de inactivos.
2. **Implementado v18:** cursos, asignación y finalización personal con historial y puntos; estado calendario calculado.
3. Programación física/reprogramación/No cumplida, cálculo académico y publicación de notas permitidas al Instructor.
4. Avance ampliado con No cumplida y publicación; después cierre/reapertura reproducible con instantáneas. Tabla, avance de habilitadas y PDF administrativo inicial implementados en la primera entrega.

Cada entrega requiere pruebas de autorización por objeto/CSRF, privacidad de proyecciones, conservación de históricos, cálculos y revisión responsiva. No declarar cierre 5B ni alterar configuraciones congeladas para aplicar nuevas reglas: preparar una versión nueva explícita una vez definida su compatibilidad.

Referencias: [reglas anteriores](09_reglas_fase_5b.md), [plan](05_plan_desarrollo.md), [historial](../HISTORY.md).


## Entrega implementada — 2026-10-12 (v17)

- Jefe consulta personal ACTIVO/INACTIVO y seguimiento global sin asignación necesaria; perfiles inactivos de consulta para Jefe, y notas/correcciones/habilitaciones nuevas exigen cuenta activa. Asistencia/cursos/participaciones activas mantienen validación de cuenta; históricos/reportes de inactivos visibles. Administración conserva reactivación/gestión global.
- Un solo Jefe activo, protegido también por triggers. Cambio de titular conserva cuentas anteriores. Campos de asignación previa quedan como referencias históricas, no como límite de autorización; no se rellenan ni borran al migrar.
- Comandante queda como rol histórico en SQLite para preservar claves foráneas/autoría, sin login ni sesiones operativas. Creación/edición de cuenta Comandante retirada (410). Nota de Desempeño transcrita/corregida por Administrador/Jefe, con nombre del evaluador externo obligatorio y registrado_por independiente; la cadena anterior permanece.
- Menú Evaluaciones por gestión: todos los perfiles activos/inactivos, selección de gestión, Ver en modal, habilitación individual de cinco fuentes y evaluaciones psicométricas de catálogo. Para las manuales, habilitar requiere configuración publicada y período activo. No hay habilitación manual inferida al migrar. Guardar/corregir notas 5B exige habilitación explícita. Deshabilitar conserva notas/finalización; cada cambio conserva actor/fecha, sin eliminar historia.
- Instructor dispone de Mis evaluaciones por gestión: habilitación, estado y avance calculado sobre habilitadas; cero habilitadas implica No disponible. No recibe notas ni autores/observaciones: publicación de notas aún pendiente. Los dos desempeños son fuentes independientes. FINALIZADA se determina por existencia de nota; No cumplida y programación física siguen pendientes. Notas v15 sin configuración se identifican como históricas, sin adoptarlas al cálculo.
- PDF administrativo por gestión con estado de cuenta, evaluación, habilitación, estado y nota vigente; incluye Desempeño, no observaciones. Carimbo SBRAB y páginas/cabeceras repetidas, privado no-store. El indicador no acredita publicación de notas al Instructor ni aprobación institucional.
- Psicometricas sin aprobación no se habilitan; formularios siguen bloqueados incluso con aprobación del catálogo. No se añadieron reactivos ni puntuación.

Esquema v17: habilitaciones_operativas (historial de cambios, persona/período/clave) e índice de consulta; triggers para Jefe único. Inicialización local repetida tras respaldo, 28 tablas anteriores preservadas, quick_check=ok y FK=0. No se reemplazó entorno, configuración ni base.

Verificación 2026-10-12: **81 pruebas aprobadas en 45,711 s** (bases aisladas). Ocho escenarios Chromium con API simulada (tres roles en tabla y catálogo de Jefe, 360/1447 px), sin desborde ni errores; modal, personal inactivo sin controles, privacidad propia y enlace PDF invalidado al cambiar gestión comprobados. PDF sintético de cinco páginas, carimbo/texto de todas las páginas comprobado y páginas 1/4 inspeccionadas visualmente. Compilación Python, sintaxis JavaScript, enlaces y git diff --check correctos. Las ejecuciones iniciales detectaron expectativas del filtro por equipo antiguo y un fixture de instrumento con columna incorrecta; corregidos antes de repetir la suite completa.

Siguiente entrega: cursos con puntaje, fechas obligatorias/estado derivado y asignación/finalización personal con historial. Luego programación física/No cumplida, acumulado académico y publicación/republicación. El flujo manual académico v16 y configuraciones PROMEDIO_TRES_V1 se conservan por compatibilidad: no se presentan como acumulación por cursos ni se transforman automáticamente. Fase 5B y piloto no están cerrados.


### Ajuste visual de la tabla — 2026-10-12

Gestión (año) muestra el año de inicio del período guardado y conserva su ID; Reporte PDF es un botón que se habilita solo tras consultar la gestión vigente. Tabla proporcional con estados de cuenta coloreados y acción Ver por icono accesible. El modal usa filas compactas con evaluación, nota administrativa, etiquetas de habilitación/finalización y acción; sin tarjetas grandes. Adaptación a móvil y temas claro/oscuro verificada. No cambia reglas ni permisos; notas numéricas del Instructor siguen pendientes de publicación.


## Segunda entrega de la reformulación — Cursos y formación (2026-10-12, v18)

Implementados puntajes enteros 0–100, estado automático por fechas de Bolivia, asignación múltiple sin duplicados, cuatro estados personales, finalización/puntaje/fecha explícitos y correcciones con versiones. Catálogo previo, formación histórica y autoría conservados; propios sin puntajes hasta publicación. 86 pruebas en 87,375 s, 12 escenarios UI y migración local preservando 29 tablas. [Reglas, API y evidencias de esta entrega](11_cursos_formacion.md). Cursos ya no están pendientes; acumulación, físicas y publicación/republicación permanecen pendientes.


## 5B.1 implementada — 2026-10-13 (v19)

Dos fechas comunes, reprogramaciones extraordinarias individuales y No cumplida auditada con cero; pendiente sin nota distinto y cero conservado al reprogramar. Administrador/Jefe programan y reprograman, conforme a los permisos confirmados en esta entrega. Estados/avance y PDF reflejan No cumplida; notas del Instructor siguen ocultas. [Reglas, APIs, compatibilidad y evidencias](13_programacion_fisica.md). Los bloques v17/v18 anteriores son evidencia histórica. No cambia PROMEDIO_TRES_V1 ni adopta históricos. Pendientes 5B.2 cálculos/acumulación, 5B.3 publicación y 5B.4 cierres.


## 5B.2 implementada — 2026-10-13 (v20)

Confirmados CRUD compartido Administrador/Jefe para Gestiones con baja lógica, activación anual separada de habilitación personal y menú sin incisos duplicados. Sin formación finalizada: Académica pendiente; una fuente necesaria desactivada deja conjunto No disponible sin cambiar fórmula. Administrador activa explícitamente ACUMULADO_TRES_V2, incluyendo notas vinculadas a configuración y físicas programadas, excluyendo notas sin configuración y físicas no programadas. Configuración histórica no modificada. [Reglas, APIs, evidencia y límites](14_calculos_y_gestiones.md). Los acuerdos de CRUD de Gestiones de esta entrega sustituyen la exclusividad administrativa anterior; configurar/publicar el ciclo sigue administrativo. Pendientes 5B.3/5B.4.


## 5B.3 implementada — 2026-10-13 (v21)

Administrador/Jefe publican/republican versiones propias físicas/académicas, con vista previa/revisión/firma/motivo e historial inmutable. Confirmado: publicación parcial permitida; ocultar en servidor lo publicado mientras su fuente esté deshabilitada o la Gestión retirada. Correcciones no sustituyen valores/fechas publicados hasta republicar; fuentes ocultas se conservan en historial. Instructor no recibe Desempeño ni estado/denominador que lo revele, conjunto ni fuentes privadas. [Reglas, APIs y evidencia](15_publicacion_notas.md). Pendiente 5B.4.

### Actualización de permisos de personal — 2026-10-13

Por solicitud posterior del usuario, Administrador y Jefe de Personal pueden cambiar cuentas ya admitidas entre ACTIVO e INACTIVO desde el directorio global. Sustituye el límite anterior de reactivación exclusivamente administrativa: el Jefe activa primero y luego puede editar el perfil. Las solicitudes PENDIENTE/RECHAZADO no se activan por este mecanismo ni por la baja heredada; aprobación/rechazo sigue exclusivo del Administrador. Cambiar estado conserva registros y credenciales, audita actor/persona/transición/fecha UTC e invalida sesiones previas. Reactivar requiere nuevo login. No habilita evaluaciones ni publica resultados automáticamente.

API: `PATCH /api/instructores-voluntarios/<id>/estado`, con `estado` y `estado_anterior` (ACTIVO/INACTIVO). Verificación del estado anterior dentro de transacción serializada; discrepancia devuelve 409. Los endpoints POST de desactivación anteriores se conservan y aplican las mismas restricciones.

### Cierre/reapertura implementado — 2026-10-14

5B.4 conserva cada cierre completo o incompleto y permite reapertura administrativa motivada sin segundo activo ni cambio de configuración. Las lecturas de resultados cerrados usan la versión conservada. Confirmado: correcciones de formación bloqueadas si su año anterior o nuevo está cerrado, hasta reapertura. Cierre/reapertura no publica ni cambia la privacidad de 5B.3. Históricos sin opt-in v2 se cierran documentalmente sin adoptar notas ni generar conjunto; no se activan reglas nuevas después de un cierre. [Contratos, límites y verificación](16_cierres_reaperturas.md). No constituye cierre de Fase 5B ni aceptación operativa/institucional.
