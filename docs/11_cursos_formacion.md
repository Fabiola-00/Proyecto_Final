# 11. Cursos y formación personal — v18

Entrega: **2026-10-12**. Estado: **implementada técnicamente**; aceptación operativa pendiente. Acuerdos en [reformulación](10_reformulacion_evaluaciones.md). No implementa todavía el acumulado académico ni publicación/republicación de notas.

## Catálogo y estado automático

Administrador/Jefe registran y editan cursos. Nuevos cursos requieren nombre, tipo, entidad, fecha de inicio/fin y puntaje entero 0–100; observaciones opcionales. Tipos: Capacitación, Especialización, Actualización, Taller, Seminario (Webinar). El fin no puede preceder al inicio.

El servidor consulta la fecha de Bolivia (UTC−04:00): antes del inicio Próximo (amarillo), desde inicio hasta fin inclusive En curso (verde), después del fin Finalizado (rojo). El estado se calcula al consultar, no mediante tareas que escriban diariamente en SQLite. El cliente no puede enviar estado manual. La vista previa usa el día proporcionado por el servidor.

Históricos incompletos conservan campos anteriores, incluido el estado manual almacenado; no se inventan fechas ni puntos. La proyección muestra Sin fechas completas cuando no puede calcular estado. Pueden editarse datos puntuales sin rellenar otros implícitamente; para asignar participantes deben completarse tipo, entidad, fechas coherentes y puntaje. El PDF de catálogo conserva rango inclusivo por inicio y filtros tipo/estado; el filtro usa estado calculado, sin observaciones ni puntajes individuales.

## Participación individual

Asignación por curso/persona, sin duplicados, exclusivamente a personal activo. Selección múltiple y transacción completa: si una persona es inválida o ya está asignada, no se guardan cambios parciales. Se capturan nombre/entidad/tipo/fechas/puntaje de referencia del curso; editar después el catálogo no reescribe esos datos ni notas anteriores.

Estados personales: Asignado, En curso, Finalizado, No completado. El curso terminado no finaliza automáticamente personas. Cada cambio exige revisión vigente y motivo; guarda actor, nombre del responsable, fecha UTC y valores anteriores/nuevos como versiones. Repetir exactamente el mismo estado/puntaje/fecha no genera una corrección duplicada. Cuentas inactivas: consulta e historial, sin asignación ni corrección.

Finalizado exige puntaje individual entero 0–100 y fecha personal explícita, desde el inicio capturado al asignar y no futura según Bolivia. Puede diferir del puntaje base. Finalización personal independiente del fin del catálogo: admite finalización anterior al fin o registrada después, sin inferirla automáticamente. En curso no se registra antes del inicio. En otros estados, puntaje obtenido y fecha de finalización quedan ausentes; no se fabrica cero. Un cero explícito en Finalizado sí es válido. Rectificar una finalización conserva sus puntos/fecha previos en historial, aunque el registro vigente pase a No completado.

Una única participación vigente evita duplicar el curso en distintas gestiones; su fecha personal queda preparada para imputar puntos una sola vez al año correspondiente. El cálculo académico de tope 100 aún no se ejecuta; tampoco se altera una nota global manual anterior ni se adoptan cursos históricos automáticamente.

## Pantallas y privacidad

Catálogo tabular con colores/estado textual, puntaje y cantidad de participantes; acciones por iconos: Ver participantes, Editar curso (modal), Asignar participantes (modal). Participantes: cuenta, estado, puntaje obtenido, finalización, edición e historial. Activos/inactivos consultables por Administrador/Jefe, con controles de escritura solo para activos.

Mis cursos muestra asignaciones y formación histórica diferenciadas, solo de la persona autenticada. No devuelve puntaje base/obtenido, motivos ni autores/observaciones mientras publicación esté pendiente. Dashboard propio incorpora cantidades de cursos asignados/finalizados; seguimiento administrativo muestra la formación nueva junto a la histórica, sin convertirla en calificaciones 5B.

## Persistencia y API

- `cursos.puntaje`: nullable para históricos; CHECK entero 0–100.
- `participaciones_curso`: FK curso/persona, UNIQUE por ambos, estado/revisión, instantánea del catálogo, puntaje base, puntaje obtenido y fecha personal; CHECK distingue Finalizado de estados sin puntaje.
- `historial_participaciones_curso`: versión única por participación/revisión, actor/nombre/fecha/motivo/estado/puntaje/fecha personal. FK restrictivas; sin borrado físico ni desvinculación.
- GET/POST `/api/cursos/<id>/participantes` (Administrador/Jefe); POST recibe `voluntario_ids`.
- PATCH `/api/formacion/participaciones/<id>`: revisión, estado, motivo y, para Finalizado, puntaje/fecha_finalizacion. Campos de identidad/autor arbitrarios rechazados.
- GET `/api/formacion/participaciones/<id>/historial` (Administrador/Jefe).
- GET `/api/instructor-voluntario/formacion`: proyección propia explícita, sin selector de terceros ni puntajes.

CSRF en escrituras, BEGIN IMMEDIATE y revisión para conflictos concurrentes; primera asignación y sus cambios dejan versiones. `capacitaciones` y sus vínculos históricos permanecen intactos, sin copiar registros a las nuevas tablas.

## Evidencia y límites

Migración local v17→v18 tras respaldo: 29 tablas anteriores preservadas, campos previos comparados, inicialización repetida, puntajes anteriores NULL y nuevas tablas vacías; quick_check=ok y cero infracciones FK. No se recrearon .venv/.env/base ni se añadieron dependencias.

**86 pruebas aprobadas en 87,375 s**, con bases aisladas. Cobertura incluye límites/fechas de Bolivia, cero/enteros, asignación y corrección concurrentes, duplicados y rollback, revisión obsoleta, inactivos/CSRF/privacidad, preservación de instantáneas y migración v17. La primera suite de 85 pasó; al agregar el caso de migración, el fixture omitía una columna histórica y se corrigió antes de la ejecución final completa.

**12 escenarios Chromium** con API simulada: tres roles, 360/1447 px, claro/oscuro; edición, asignación, finalización con cero, historial, cursos incompletos e inactivos sin escritura y privacidad propia. Sin desbordes ni errores JavaScript. Compilación Python, sintaxis JavaScript, enlaces locales y git diff --check correctos. Frontend/login.html y cambios locales anteriores preservados.

Pendientes: acumulación académica hasta 100, programación/reprogramación física/No cumplida, publicación/republicación de notas permitidas al Instructor y cierre/reapertura con instantáneas. Fase 5B y piloto no están cerrados. Psicometría y decisiones institucionales siguen condicionadas según el plan.


Actualización posterior — 2026-10-13: programación/reprogramación física y No cumplida implementadas en [5B.1/v19](13_programacion_fisica.md). La evidencia v18 anterior conserva su fecha. Acumulación académica, cálculos, publicación/republicación y cierres continúan pendientes; no se modificó el cómputo de cursos en esta entrega.


Actualización posterior — 2026-10-13, v20: [5B.2 y Gestiones](14_calculos_y_gestiones.md) implementa acumulado académico/cálculos provisionales mediante activación explícita, CRUD compartido de gestiones con baja lógica y activación anual separada de habilitación individual. Sustituye los pendientes de cálculo y la exclusividad de CRUD de gestiones de los bloques anteriores; configuración/publicación del ciclo siguen administrativas. Pendientes 5B.3 publicación y 5B.4 cierres. La evidencia anterior conserva su fecha/contexto.


Actualización posterior — 2026-10-13, v21: [5B.3 publicación/republicación](15_publicacion_notas.md) implementa versiones físicas/académicas propias, publicación parcial y ocultación mientras la fuente esté deshabilitada o Gestión retirada. Mis cursos muestra puntos desde snapshot publicado; correcciones mantienen versión/fecha anterior hasta republicar. Desempeño/conjunto y fuentes privadas no se publican. La evidencia de esta entrega anterior conserva su contexto. Siguiente pendiente 5B.4 cierre/reapertura con instantáneas.

### Ajuste de interfaz — 2026-10-13

«Asignar participantes» permite seleccionar varias personas mediante casillas con nombre/código y muestra la cantidad seleccionada. Solo lista personal activo aún no asignado; el botón se habilita al marcar al menos una persona. El envío conserva el contrato y la asignación atómica existentes. Si hay un error, la selección permanece para reintentar.

### Formación y cierres — 2026-10-14

En 5B.4 se confirmó bloquear registrar/corregir una finalización si su año anterior o nuevo corresponde a una Gestión anual cerrada. Incluye retirar una finalización o moverla a otro año; exige reapertura administrativa previa. Una petición sin cambios no crea revisión. Catálogo y asignaciones permanecen separados del cálculo y no modifican instantáneas. [Ciclo y bloqueos](16_cierres_reaperturas.md).


Actualización de permisos y navegación — 2026-10-14: Administrador/Jefe crean y editan operaciones y asignan participantes, también mediante lote atómico por checkbox. Centro de reportes administrativo con PDF de formación personal finalizada y operaciones/participantes; campos privados excluidos. Esto sustituye el alcance anterior de eventos exclusivos del Administrador. [Espacio del Jefe y reportes](19_espacio_jefe_reportes.md).
