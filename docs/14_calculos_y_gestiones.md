# 14. Gestiones, activación anual y cálculos — 5B.2, v20

Entrega del **2026-10-13**, posterior a 5B.1/v19. Implementación técnica; aceptación operativa e institucional pendientes. No publica notas ni implementa cierre/reapertura con instantáneas. Fase 5B sigue parcial.

## Decisiones confirmadas en esta entrega

- Gestión es el año evaluado, distinta del catálogo de Evaluaciones. Administrador y Jefe crean, editan y eliminan lógicamente gestiones.
- Eliminar retira la gestión de listas operativas y bloquea nuevas acciones; conserva períodos, notas, programación, formación e historial. No equivale a un cierre con instantánea.
- Administrador/Jefe activan/desactivan evaluaciones **por Gestión** para todo el personal. La habilitación individual se conserva aparte. Física o Desempeño obligatorios desactivados dejan el conjunto No disponible, sin redistribuir pesos; Académica también es un componente necesario.
- Sin formación finalizada en el año, Académica permanece pendiente. Una finalización personal explícita con cero sí es válida.
- Administrador activa explícitamente ACUMULADO_TRES_V2 por Gestión: usa notas vinculadas a su configuración publicada y formación personal del año; excluye notas sin configuración y físicas sin resultado programado. No convierte ni modifica PROMEDIO_TRES_V1.

Crear/editar/eliminar gestiones y activar evaluaciones son permisos compartidos. Configurar/publicar el ciclo y activar la regla nueva conservan autorización administrativa. Publicar configuración no publica notas al Instructor.

## Recorrido y menú

Menú de ambos gestores: Inicio; Personal y operaciones (Instructores, Jefes solo para Administrador, Asistencias, Cursos, Operaciones); Evaluación anual (Gestiones, Catálogo, Habilitación y avance, Notas y resultados). Administrador conserva Mi cuenta y contraseña.

Se retiraron del catálogo los formularios duplicados de creación de períodos y asignación antigua. El catálogo común mantiene edición y disponibilidad para configurar gestiones; sus controles se nombran Habilitar/Retirar del catálogo, diferenciados de la activación anual. Las APIs y registros anteriores permanecen por compatibilidad. Notas anteriores se consultan desde un enlace contextual de historial, sin otro inciso repetido del menú.

**Gestiones (año)** permite crear borradores enero–diciembre, editar nombre/año cuando no hay registros/asignaciones ni configuración publicada, activar/desactivar los mismos seis ítems anuales (dos físicas, Académica, dos aportaciones de Desempeño y Psicométricas), consultar historial y dar baja lógica motivada. La edición conserva valores anteriores, autor y fecha; revisión obsoleta se rechaza. Una gestión publicada conserva nombre/año y configuración para no reasignar historia entre años.

La baja conserva el estado original del período; marca su retiro en tabla separada. No cierra ni cambia configuraciones congeladas. La unicidad operativa de ACTIVO excluye gestiones retiradas y permite abrir otro ciclo. Gestiones retiradas se listan aparte con actor/fecha/motivo y enlace de consulta histórica sin controles de escritura.

Psicométricas no se activan sin un instrumento aprobado y disponible. Aun existiendo aprobación de catálogo, los formularios continúan bloqueados y no se añaden reactivos, puntuación ni interpretación. No participan del resultado conjunto de los tres componentes operativos.

## Regla de cálculo exacta

En una gestión anual ACTIVA y configurada, el Administrador revisa y confirma el alcance de la regla nueva. La migración no realiza esa acción. Su registro conserva configuración, año, actor y fecha; es inmutable. Una sola gestión puede activar la regla v2 para cada año, incluso si luego se retira, para impedir imputaciones académicas duplicadas en gestiones paralelas del mismo año. Los borradores/históricos duplicados se conservan, sin adoptar cursos en dos cálculos anuales.

**Física:** promedio de las dos últimas notas válidas con resultado físico programado. No cumplida confirmado aporta cero y sigue aportándolo tras una reprogramación, hasta cumplimiento/corrección. Falta de nota/resultados programados es pendiente, no cero. Un cero Cumplida también es válido.

**Académica:** sumar puntos enteros de participaciones personales vigentes en estado Finalizado cuya fecha personal pertenece al año de la regla. Cada participación es única por curso/persona y aparece una sola vez; su revisión vigente enlaza el historial. Tope del componente 100, conservando suma sin tope, nombre capturado, fecha, participación/revisión/ID de historial y todo el detalle. Sin finalizaciones: pendiente. Corregir fecha/puntos o retirar una finalización recalcula provisionalmente el año correspondiente; no suma versiones anteriores ni copia puntos a otro año. Formación histórica `capacitaciones` y nota global manual anterior no se suman automáticamente.

**Desempeño:** promedio de las últimas notas del Jefe y Comandante externo vinculadas a la configuración seleccionada. Se conservan evaluador y autor de transcripción históricos; no se crea un cargo operativo Comandante.

**Conjunto:** (Física + Académica + Desempeño) / 3. Requiere los tres componentes y sus fuentes activas/habilitadas. Cualquier pendiente o desactivación necesaria deja No disponible, con detalle de faltantes/bloqueos. No redistribuye pesos ni usa asistencia como nota.

Las medias usan fracciones de centésimas; no hay redondeos intermedios. Componentes exactos pueden mostrar tres decimales (por ejemplo 80.015). Solo el conjunto se redondea a dos decimales, mitad hacia arriba. Ejemplo comprobado: ambas medias 0.005 y Académica cero dan 0.00; redondearlas antes produciría 0.01 incorrectamente. Un conjunto exacto 0.005 da 0.01.

## Provisionalidad, privacidad y compatibilidad

Notas y resultados muestra componentes, conjunto y detalle de fuentes/versiones para Administrador/Jefe, incluidas cuentas inactivas en consulta. El cálculo se lee en una transacción consistente; no escribe calificaciones ni instantáneas. Cambios de cursos/notas/activaciones afectan la consulta provisional posterior. Un retiro de gestión bloquea sus fuentes operativas; sus notas y versiones siguen consultables. La preservación de cada resultado cerrado mediante instantáneas pertenece a 5B.4.

Con regla v2, Académica se muestra calculada en tabla/avance y PDF administrativo; no admite nuevas notas globales manuales ni correcciones de ellas. Las versiones manuales anteriores siguen en historial. Sin regla v2 permanece el comportamiento anterior, claramente separado del acumulado.

Instructor recibe exclusivamente habilitación personal, activación anual, estados y avance propios. No recibe puntos de cursos, notas físicas/Desempeño, autores, motivos, fuentes numéricas ni resultado conjunto. Las APIs de cálculo y activación están protegidas por rol. Publicación/republicación permanece pendiente en 5B.3.

## Persistencia y APIs

Esquema v20 añade cuatro tablas, con FK restrictivas y triggers que impiden UPDATE/DELETE de su historial:

- `bajas_gestion`: baja lógica única por período, motivo/actor/nombre/fecha.
- `historial_gestiones`: nombres/años anteriores y nuevos, actor/fecha.
- `activaciones_gestion`: cadena por período/clave, estado, motivo, revisión anterior y actor/fecha.
- `reglas_calculo_5b`: opt-in inmutable ACUMULADO_TRES_V2 por período/año/configuración.

Se actualizan únicamente los triggers de unicidad operativa de ACTIVO para excluir bajas; configuraciones congeladas y datos anteriores no se reescriben. No hay columnas reconstruidas ni nuevas dependencias.

- GET/POST `/api/admin/5b/periodos`, PATCH `/api/admin/5b/periodos/<id>` y página `/gestion/periodos-5b`: Administrador/Jefe. El prefijo histórico `admin` no sustituye la autorización backend.
- DELETE `/api/admin/5b/periodos/<id>`: motivo, nombre/año/estado anteriores; baja lógica con CSRF y transacción serializada. No hay restauración automática ni eliminación física.
- GET `/api/5b/gestiones/<id>/evaluaciones`: seis ítems, revisión y todo el historial anual.
- PATCH `/api/5b/gestiones/<id>/evaluaciones/<clave>`: activa boolean, revisión vigente (cero inicial), motivo; Administrador/Jefe. Conserva habilitaciones individuales y notas anteriores.
- POST `/api/admin/5b/periodos/<id>/calculo`: Administrador; configuración_id, regla ACUMULADO_TRES_V2 y confirmar_fuentes=true. Segunda activación/año duplicado rechazada.
- GET `/api/5b/personas/<id>/calculo?periodo_id=<id>`: Administrador/Jefe; resultado provisional, exactitud, fuentes, detalle y faltantes.

BEGIN IMMEDIATE serializa escrituras; revisiones evitan sobrescrituras. Se bloquean acciones nuevas en gestiones retiradas también desde APIs anteriores. Consultas parametrizadas y auditoría mínima; sin datos de credenciales ni resultados psicométricos.

## Evidencia — 2026-10-13

Suite final: **104 pruebas aprobadas en 158,822 s**, bases aisladas. Incluye once pruebas nuevas de cálculos/gestiones y las seis de físicas previas. Cubiertos permisos/CSRF/inactivos, precisión/tope/faltantes/cero, formación por año/correcciones, activación explícita y anual concurrentes, conservación de habilitación/historial, bajas y activo único, menú/rutas funcionales, privacidad y migración idempotente. Suite intermedia 103 pruebas con un fallo de compatibilidad HTTP psicométrica (404 en lugar de 403), corregido y comprobado antes de repetir la suite completa. Los fallos iniciales de fixtures nuevos (alta de persona/curso duplicada) se corrigieron sin cambiar las reglas de negocio.

36 escenarios Chromium con API simulada, 360/1447 px y temas claro/oscuro: Gestiones/Notas/Tabla/Catálogo para Administrador/Jefe (32) y propia para Instructor (4), sin errores JavaScript ni desbordes. Capturas inspeccionadas; se corrigió la disposición del resumen provisional en móvil y la separación de gestiones retiradas. No equivale a aceptación operativa.

Compilación Python, sintaxis de cinco JavaScript, enlaces locales y git diff --check correctos. La suite de cierre se repitió después de serializar las APIs legadas de asignación/habilitación para evitar carreras con bajas y activaciones. La ejecución anterior de 104 pruebas en 90,025 s se conserva como evidencia intermedia en HISTORY. Logs locales ignorados: `.tmp/calculos-suite-cierre.log`, `.tmp/calculos-ui/`, `.tmp/calculos-migracion.json`.

Pendientes: **5B.3 publicación/republicación** y **5B.4 cierres/reaperturas con instantáneas**. No se declara cerrada 5B ni preparado el piloto; psicometría/IA conservan sus condiciones.


### Migración local y comprobaciones complementarias

Respaldo `instance/backups/sicose-20261013-pre-v20-57e238bb.sqlite3`; migración v19→v20 con dos inicializaciones, **35 tablas previas preservadas** (salvo actualización esperada de schema_version), quick_check=ok y cero infracciones FK. Cuatro tablas nuevas vacías, sin activaciones/reglas inferidas. Entorno/fotos/cambios locales conservados, sin seed ni dependencias nuevas.

Prueba HTTP adicional con regla v2: tabla refleja Académica 100.00 Finalizada desde 130 puntos de detalle; PDF 200, válido y privado no-store. Sin nueva inspección visual de PDF. La evidencia fechada anterior de 5B.1 conserva su contexto y no sustituye estas comprobaciones.


Actualización posterior — 2026-10-13, v21: [5B.3 publicación/republicación](15_publicacion_notas.md) implementa versiones físicas/académicas propias, publicación parcial y ocultación mientras la fuente esté deshabilitada o Gestión retirada. Mis cursos muestra puntos desde snapshot publicado; correcciones mantienen versión/fecha anterior hasta republicar. Desempeño/conjunto y fuentes privadas no se publican. La evidencia de esta entrega anterior conserva su contexto. Siguiente pendiente 5B.4 cierre/reapertura con instantáneas.

### Resultados cerrados — 2026-10-14

5B.4 conserva cada cálculo y sus fuentes en instantáneas. Mientras la Gestión está CERRADO, la consulta devuelve `provisional=false` y `cierre_id` desde el último cierre, sin consultar puntajes actuales para reconstruirlo. La fracción exacta de centésimas se guarda junto al conjunto final. Tras reapertura vuelve el cálculo provisional con la misma regla/configuración; nunca se reemplazan cierres anteriores. Una regla no activada antes del primer cierre no puede adoptarse después de reabrir. [Compatibilidad y bloqueos académicos](16_cierres_reaperturas.md).
