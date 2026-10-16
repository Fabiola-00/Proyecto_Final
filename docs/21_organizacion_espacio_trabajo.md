# Organización del espacio de trabajo — 2026-10-15, SQLite v25

Esta entrega sustituye los recorridos duplicados de Gestión/Modelo Anual/Evaluaciones para el trabajo nuevo. Conserva los históricos funcionales de V1/V2 mediante enlaces contextuales; no elimina evidencia ni transforma sus notas. La aceptación operativa anterior de 5B no se extiende automáticamente a esta reorganización.

## Pantallas y navegación

- Todas las plantillas HTML independientes usan `SICOSE - SBRAB` y el PNG institucional del logo como favicon. Las demás heredan la plantilla común.
- Inicio del Jefe mantiene indicadores pequeños y añade cuatro gráficos de barras de las cinco últimas gestiones no retiradas: operaciones, cursos registrados, asistencias personales registradas y formaciones finalizadas. Cada barra cuenta registros dentro de las fechas inclusivas de su Gestión; no calcula notas ni predicciones. Una Gestión superpuesta histórica puede compartir registros con otra; el gráfico describe intervalos, no suma acumulados de calificación.
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
