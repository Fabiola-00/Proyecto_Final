# Organización del espacio de trabajo — 2026-10-15, SQLite v25

Esta entrega sustituye los recorridos duplicados de Gestión/Modelo Anual/Evaluaciones para el trabajo nuevo. Conserva los históricos funcionales de V1/V2 mediante enlaces contextuales; no elimina evidencia ni transforma sus notas. La aceptación operativa anterior de 5B no se extiende automáticamente a esta reorganización.

## Pantallas y navegación

- Todas las plantillas HTML independientes usan `SICOSE - SBRAB` y el PNG institucional del logo como favicon. Las demás heredan la plantilla común.
- Inicio del Jefe mantiene indicadores pequeños y añade cuatro gráficos de barras por meses de la Gestión activa no retirada (actualización del 2026-10-16): operaciones, cursos registrados, días distintos con asistencia registrada y formaciones finalizadas. Cada barra cuenta registros del mes dentro de las fechas inclusivas de la Gestión activa; no calcula notas ni predicciones. Una Gestión superpuesta histórica puede compartir registros con otra; el gráfico describe intervalos, no suma acumulados de calificación.
- Directorio de Instructores sin cambio de organización. Asistencia de registro tiene filas más bajas; el historial conserva sus medidas y filtros.
- Cursos y Operaciones usan desplegables nativos con el mismo resumen visual de Agregar Instructor. Operaciones presenta una tabla compacta con edición y asignación múltiple. Se retiró el reporte duplicado del catálogo de cursos.
- Gestión reúne nombre/inicio/fin/creación, edición anterior al inicio, inicio explícito, cierre, reapertura administrativa e instantáneas. La tabla incorpora gestiones nuevas e históricas. La interfaz dice Crear Gestión/Preparada; el estado interno BORRADOR se conserva para compatibilidad y para impedir ceros antes del inicio. Crear no cierra ni activa otro ciclo silenciosamente. Iniciar incluye a todos los Instructores activos, sin reiniciar gestiones anteriores. Se retiró el botón de inscripción adicional durante el ciclo; no se interpretó la respuesta como autorización para incorporar automáticamente nuevas altas a una Gestión ya iniciada. Cuentas inactivas conservan sus restricciones.
- Evaluaciones reúne activación anual, habilitación individual, tabla de personas, componentes compactos y calificación. Física v3 admite Cumplida/No cumplida sin programación ni fecha; No cumplida requiere cero, versión previa y motivo. Fechas/programaciones históricas y sus APIs siguen conservadas. El circuito V1/V2 mantiene su comportamiento anterior.
- Notas y Resultados deja de ser una opción del menú. Su ruta anterior redirige al espacio único; `?historico=1` permite consultar/calificar/publicar datos históricos aún funcionales. No se borran páginas necesarias para esas operaciones ni se permite acceso de Instructor a fuentes privadas.
- Reportes concentra cinco opciones. Generar abre el PDF en otra pestaña, con manejo de errores en origen; no usa un enlace de descarga. Las respuestas PDF son privadas, no-store e inline. Se incorpora el modelo anual v3 al selector y al PDF de evaluaciones: fuentes numéricas oficiales, psicométricas pendientes y ninguna recomendación. En cerrado se exportan cálculo e identidad de la última instantánea, sin reconstruirlos desde el directorio actual.

## Eliminación de gestiones

Confirmado: Administrador/Jefe pueden eliminar permanentemente gestiones únicamente sin resultados. Los ceros oficiales de inicio son resultados: una Gestión iniciada con personal no es vacía. Se bloquea también la eliminación cuando exista evidencia protegida, configuración histórica vinculada, publicaciones, cierres o habilitaciones que deban conservarse. No se desmontan las restricciones de históricos para forzar un borrado.

`DELETE /api/gestiones/<id>/eliminar` exige motivo, nombre y estado anteriores; comprueba dependencias bajo `BEGIN IMMEDIATE` y registra auditoría antes de confirmar. Solo permite eliminar los eventos/metadatos de un modelo nunca iniciado, sin inscripciones ni resultados. Las tablas anteriores continúan protegidas; no hay cascadas destructivas ni desactivación de claves foráneas. Las APIs de baja lógica previas conservan compatibilidad, pero no se presentan como eliminación permanente.

## Cursos y retiradas

Confirmado: eliminar físicamente solo un curso sin participaciones ni vínculos formativos históricos. Con vínculos se registra una baja inmutable en `bajas_curso`, se oculta del catálogo operativo y se impiden asignaciones/ediciones nuevas. Un selector permite volver a consultar los cursos dados de baja y su historial. Dar de baja el catálogo **no retira** las participaciones ni sus puntos.

Retirar participantes se hace por checkbox, con motivo obligatorio y revisión por participación. El lote se valida/guarda íntegramente; una revisión obsoleta o selección inválida revierte todo. Se registra `retiros_curso`, cambia el estado vigente a No completado sin puntos/fecha y añade una versión a `historial_participaciones_curso`. Las revisiones anteriores conservan el puntaje y su finalización; la interfaz identifica Retirado. No se borra ni reutiliza la participación, no se permiten correcciones sobre una retirada y no se modifican cuentas inactivas. Si el puntaje pertenece a una Gestión cerrada, se exige reapertura antes de retirar. El cálculo abierto se actualiza desde las evidencias vigentes; las publicaciones históricas explícitas conservan su versión hasta republicar.

APIs nuevas: `DELETE /api/cursos/<id>` con motivo; `POST /api/cursos/<id>/retirar-participantes` con motivo y lista de `{id,revision}`. `GET /api/cursos?incluir_bajas=1` incluye los archivados para gestión autorizada. Escrituras protegidas por roles, sesión activa, CSRF y transacción serializada.

## Formularios demostrativos solicitados

El solicitante pidió dos preguntas aleatorias de sumas/restas, con puntaje y Finalizar, como ejemplo temporal. No son instrumentos psicométricos ni reemplazan su autorización. Cada uno de los dos ejemplos genera dos operaciones con operandos de 1 a 20 y 50 puntos por respuesta correcta. El resultado posible es 0/50/100, calculado por el servidor; no se acepta puntaje enviado por el cliente.

Administrador/Jefe activan por Gestión cada ejemplo por separado. Solo Instructor activo e inscrito puede iniciar/responder el suyo en Gestión activa y no retirada. Reabrir el formulario retoma las mismas preguntas; una finalización por persona/Gestión/ejemplo, sin repetir ni sobrescribir. Finalización concurrente produce un éxito y un conflicto. Desactivar o cerrar bloquea el inicio y la finalización. Se mantiene la exclusividad propia, sin recibir identificador de persona desde el cliente.

En Mis evaluaciones se ven físicas/Académica habilitadas y su estado sin notas privadas; los ejemplos activos permiten abrir el formulario. El Jefe ve los resultados demostrativos en un apartado separado. La página de Evaluaciones consulta cambios cada 15 segundos mientras es visible y sin modal abierto; actualiza los resultados al finalizar el Instructor. Desempeño y fuentes privadas permanecen ocultos al Instructor. Las dos entradas psicométricas oficiales siguen `PENDIENTE_INSTRUMENTO`, valor null; el puntaje de ejemplo no entra en Académica, cierres oficiales, PDF ni recomendaciones. No existe IA entrenada.

Rutas: `/mis-evaluaciones/anual`, `GET /api/modelo-anual/propio`, `GET /api/modelo-anual/gestiones/<id>/ejemplos`, `PATCH .../ejemplos/<clave>`, `POST .../ejemplo/<clave>` y `POST .../ejemplo/<clave>/finalizar`. Claves PSICOMETRICA_1/PSICOMETRICA_2 dentro de tablas demostrativas separadas. Roles/validación/CSRF aplican en servidor; respuestas propias y demostrativas son privadas/no-store. No se auditan respuestas completas.

## Persistencia y preservación

SQLite v25 incorpora cuatro tablas: bajas_curso, retiros_curso, activaciones_demo e intentos_demo. Bajas/retiradas son inmutables; intento finalizado no admite sobrescritura o eliminación. Se ajustan exclusivamente las restricciones de eliminación de metadatos de modelos nunca iniciados. Los modelos iniciados y todas sus notas siguen inmutables.

Migración local respaldada en `instance/backups/sicose-20261015-pre-v25-1014685e.sqlite3`. Comparación íntegra de las 49 tablas previas, excluyendo únicamente schema_version en app_meta: preservadas. Dos inicializaciones consecutivas; 53 tablas, cuatro nuevas vacías, v25, quick_check=ok y cero infracciones FK. Sin seed, dependencias ni creación automática de gestiones, ceros, bajas o ejemplos. Evidencia en `.tmp/organizacion-migracion.json`.

## Verificación

Las verificaciones finales y sus cifras se registran al cierre de esta entrega; las evidencias anteriores de v24 son históricas. Nueve pruebas específicas cubren bajas, recalculo, historial, límites de cierre, permisos, CSRF, cuentas inactivas, concurrencia, físicas sin fecha, puntuación demostrativa, privacidad y PDF. Capturas revisadas con Flask real, base DEMO aislada, Chrome 360/1447 px y temas claro/oscuro. El PDF v3 se generó y renderizó para inspección; sin superposiciones ni texto cortado.

Pendientes: instrumentos psicométricos autorizados, publicación propia numérica v3, modelo entrenado/validado, aprobación institucional y piloto. Los ejemplos y verificaciones técnicas no acreditan validez psicométrica, aceptación humana nueva ni cierre global de fase.


### Verificación final de la reorganización v25 — 2026-10-15

- Suite completa final: **158 pruebas aprobadas en 286,819 s**; nueve específicas de esta entrega aprobadas previamente en **17,368 s**. Se actualizaron las expectativas de navegación anteriores que exigían Notas y Resultados/Gestiones (año); no se restauraron controles retirados para satisfacerlas. Log final `.tmp/organizacion-suite-cierre.log`.
- **48 escenarios visuales** con Flask/Werkzeug real y base DEMO aislada: 36 del recorrido integral, ocho tras el ajuste final de ancho de cursos/eliminación visible solo en Gestión preparada y cuatro de Asistencias con guardado real DEMO y comprobación de padding exclusivo del registro. Chrome, 360/1447 px, temas claro/oscuro, tres roles; cero errores JavaScript y cero desbordes globales. Capturas inspeccionadas. Se comprobó el puntaje de ejemplo 100 calculado por servidor y actualizado en el Jefe sin recargar, retirada por checkbox con historial, navegación, desplegables y PDF actual/operaciones en pestaña sin descarga. Evidencias `.tmp/organizacion-ui/resultado.json` y `ajuste-resultado.json` y `asistencias-resultado.json`.
- PDF v3 real generado/renderizado e inspeccionado; encabezado institucional, tabla y pendientes legibles. El test verifica privacidad, denegación a Instructor e identidad congelada tras cierre aunque cambie el directorio.
- Compilación Python, sintaxis de los ocho JavaScript, **174 enlaces locales en 25 documentos** y git diff --check correctos. DDL de DESARROLLO (v23+v24+v25) ejecutado dos veces en SQLite temporal: **53 tablas/56 triggers**, quick_check=ok/FK=0.
- Relectura de la base de trabajo contra el respaldo pre-v25: **49 tablas previas preservadas**, salvo el identificador de versión; cuatro nuevas tablas vacías, v25/quick_check=ok/FK=0. DEMO detenida y base temporal retirada; sin seed, dependencias nuevas o cambios en .venv/.env/fotos.

La aceptación operativa de 5B del 2026-10-14 sigue siendo histórica y no acredita esta reorganización. Pendientes: instrumentos psicométricos autorizados, publicación numérica propia v3, entrenamiento/validación del modelo, aprobación institucional y piloto. Los formularios aritméticos son ejemplos independientes, no resultados psicométricos ni recomendaciones.


### 2026-10-16 — Dashboard por meses de la gestión activa

Los gráficos de Inicio del Jefe sustituyen la comparación de últimas gestiones por Operaciones, Cursos registrados, Asistencias registradas y Formaciones finalizadas agrupadas por mes de la Gestión ACTIVA no retirada. Se respeta el intervalo inclusivo de inicio/fin, incluidos meses parciales y períodos que cruzan años. Cada mes aparece con su año y conteo cero cuando no hay registros; sin Gestión activa se solicita activarla, sin inventar un intervalo. En móvil el desplazamiento horizontal se limita al gráfico y admite teclado; dos columnas cuando hay espacio. Indicadores y resúmenes restantes conservan su alcance.

Verificación de esta corrección: cuatro pruebas específicas aprobadas en 0,002 s (límites, cuatro series, ceros, bisiesto, cruce anual y ausencia de Gestión), tres de regresión del espacio del Jefe aprobadas en 7,868 s. Cuatro escenarios con Flask real/DEMO aislada y Chrome, 360/1447 px, claro/oscuro: doce meses por gráfico, conteos comprobados, sin errores JavaScript ni desbordes de página; capturas inspeccionadas. Compilación Python y git diff --check correctos. No cambia JavaScript de producto, esquema ni datos de trabajo; SQLite permanece v25. No se repitió la suite completa: la evidencia de 158 pruebas del 2026-10-15 es histórica. Logs/capturas en .tmp/mensual-regresion.log y .tmp/mensual-ui/.


### 2026-10-16 — Días con asistencia registrada por mes

El gráfico de asistencia del Inicio del Jefe cuenta fechas distintas dentro de cada mes de la Gestión activa (COUNT DISTINCT fecha), no filas por persona. Varias personas o actividades registradas el mismo día cuentan como un único día. No se filtra por Asiste: se cuentan días con registro de llamada, independientemente del estado personal. Se conserva el intervalo inclusivo y los meses sin registros. Título: Días con asistencia registrada. Las demás series mantienen sus conteos.

Verificación nueva: cinco pruebas mensuales aprobadas en 0,002 s, incluida deduplicación de fechas con múltiples registros y límites del período; tres pruebas del espacio del Jefe aprobadas en 7,287 s, incluida la etiqueta renderizada. Compilación Python y git diff --check correctos. Sin migración, cambios de datos ni nueva suite completa o ensayo visual. Evidencia en .tmp/dias-asistencia-tests.log y .tmp/dias-asistencia-regresion.log; las verificaciones visuales anteriores siguen siendo históricas.


### 2026-10-16 — Observación opcional al calificar

Por confirmación del solicitante, únicamente los formularios de calificación sustituyen Motivo por Observación (opcional): físicas, Desempeño, operaciones y finalización/corrección de cursos, incluidos formularios históricos de notas. Se permite texto vacío u omitido en servidor; texto presente debe ser cadena de hasta 2000 caracteres. Se conserva el campo interno motivo y su historial para compatibilidad, sin migración ni modificación retroactiva de registros. No cambia la exigencia de motivo en cierre/reapertura, eliminación, publicación, activación o programación física. Las referencias académicas históricas y el nombre del Comandante siguen siendo obligatorios.


### 2026-10-16 — Participaciones y asistencia del Instructor seleccionado

Evaluaciones muestra en Cursos, operaciones y asistencia las participaciones del Instructor seleccionado dentro de las fechas de la Gestión seleccionada (alcance y fórmula confirmados por el solicitante). Cursos por solapamiento del intervalo capturado al asignar o fecha personal de finalización dentro de Gestión; estados personales y retiradas identificados, sin confundir asignación con finalización. Operaciones por solapamiento inclusivo, usando inicio cuando el histórico no tiene fin; la calificación conserva la regla vigente de inicio dentro de Gestión. La lista informativa no cambia las fuentes del acumulado académico.

Asistencia reutiliza la proyección histórica y la fórmula del reporte: (Asiste + Atraso)/(Asiste + Atraso + Falta), dos decimales; Permiso excluido, sin registros computables No disponible. Conteo por registros personales, sin inventar faltas por fechas sin registro. Indicador separado de Académica y de instantáneas de cierre; las participaciones y asistencias se consultan en su estado actual. API administrativa existente protegida por roles, usuario y período; sin ampliar proyección propia de Instructor.

Presentación actualizada 2026-10-16: las participaciones del Instructor se muestran en dos tablas compactas independientes (Cursos y Capacitaciones / Operaciones), con información, estados, fechas y acción de calificar donde corresponde. Desplazamiento horizontal local en móvil, encabezados y caption; asistencia como resumen de texto sin tarjeta.

Corrección de distribución 2026-10-16: la sección de participaciones se apila en una sola columna; ambas tablas ocupan todo el ancho disponible y títulos/cabeceras se alinean a la izquierda. En móvil el desplazamiento horizontal permanece dentro de cada tabla.

Visibilidad 2026-10-16: el desplegable Historial de notas y correcciones del modelo anual se muestra únicamente al Administrador, retirado de la interfaz del Jefe de Personal. Se conserva la evidencia persistida y los contratos administrativos de API existentes.

Asistencia personal 2026-10-16: resumen con gráfico compacto de cuatro torres por estado, conteos y etiquetas visibles, junto al porcentaje general existente. Ceros sin altura positiva; sin cambio de fórmula o calificaciones.

Calificación y habilitación 2026-10-16: tabla compacta con Evaluación, Nota, Estado/origen, Habilitación y Acción, con el mismo constructor y estilo de las tablas de Cursos y Operaciones. Se conservan las condiciones y modales de calificación.

Reporte individual 2026-10-16: se añade una opción administrativa en Reportes para seleccionar Instructor admitido y exportar su expediente de la Gestión activa. Perfil/foto, formación, operaciones, notas, asistencia, psicometría y recomendación pendientes. Alcance, permisos y referencias de presentación en [reporte individual](22_reporte_individual.md).

Centro de reportes 2026-10-16: las seis opciones se presentan como filas compactas apiladas, con icono, título/criterio, filtros y botón alineados. Filtros debajo del nombre en pantallas pequeñas; permisos, criterios y generación PDF permanecen intactos.
