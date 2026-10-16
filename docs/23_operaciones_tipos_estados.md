# Operaciones: tipos, estados y baja histórica — v26, 2026-10-16

## Decisiones confirmadas

- Campo visible **Tipo de Operativo** con Preventivo, Reactivo, Especial y Emergencia.
- Campo visible **Estado de la Operación** con Planificación, En ejecución, Finalizado y Suspendido. Estado manual, no inferido por fechas.
- Ambos campos disponibles al crear y al editar desde la tabla. La tabla muestra tipo/estado; Planificación azul, En ejecución naranja, Finalizado verde y Suspendido rojo, acompañados por texto. Temas claro/oscuro conservados.
- Administrador/Jefe eliminan operaciones sin vínculos permanentemente; con participantes o notas se conserva una baja histórica. Decisión confirmada expresamente por el solicitante. Instructor solo consulta sus participaciones.

## Persistencia y compatibilidad

Migración aditiva a SQLite v26: `operaciones.tipo_operativo` y `operaciones.estado_operacion` con CHECK de catálogo y NULL histórico; `revision` positiva con valor inicial 1. `tipo_evento` conserva su contenido anterior para no reemplazar descripciones históricas ni evidencia capturada. No se deducen tipos o estados de textos/fechas antiguos. La interfaz solicita clasificación explícita al editar un registro sin ella.

Nuevas altas de la interfaz envían `tipo_operativo`/`estado_operacion`; en servidor se validan contra los catálogos y se exige estado si el alta usa el contrato nuevo. La API anterior `tipo_evento` permanece como compatibilidad para clientes/fixtures históricos, sin clasificar sus registros automáticamente. No usar ese contrato anterior para nuevas interfaces. Los reportes de operaciones y el detalle del cálculo usan el tipo nuevo cuando existe, con el texto anterior como respaldo histórico.

Tabla `bajas_operacion`: operación, motivo obligatorio, actor, nombre y fecha UTC. Triggers impiden modificar/eliminar la evidencia de baja. La baja no es el estado Suspendido ni un cierre de Gestión; no borra participantes, notas o instantáneas, no recalcula ni retira puntos ya registrados. Bajas se excluyen de la lista operativa administrativa por defecto y se consultan con Mostrar bajas históricas. Instructor conserva consulta de su participación histórica sin terceros.

## Rutas y seguridad

- `POST /api/operaciones`: campos nuevos y catálogo validado en servidor.
- `PATCH /api/operaciones/<id>`: campos nuevos, revisión vigente enviada por interfaz, bloqueo ante baja o notas en Gestión cerrada. No se cambia la protección de cierres.
- `GET /api/operaciones?incluir_bajas=1`: consulta administrativa de bajas; Instructor sigue limitado a sí mismo aunque manipule el parámetro.
- `DELETE /api/operaciones/<id>`: exige revisión vigente/motivo, roles y CSRF. Transacción BEGIN IMMEDIATE revisa vínculos y elimina o registra baja; auditoría mínima por operación/actor. No hay cascada destructiva ni desvinculación de participantes.
- Operaciones dadas de baja no admiten edición, nueva asignación ni nuevas calificaciones/correcciones. Se conservan notas previamente registradas y su contribución conforme a la regla original.

## Migración local verificada

Respaldo `instance/backups/sicose-20261016-pre-v26-6a4fec05.sqlite3`. Dos inicializaciones consecutivas, 53 tablas anteriores comparadas íntegramente por sus columnas previas y preservadas (excepto valor de schema_version), 54 tablas actuales, bajas vacía. Ningún tipo/estado inferido en registros existentes. `quick_check=ok`, cero infracciones FK. Evidencia `.tmp/operaciones-v26/migracion.json`. Sin seed ni modificación de entorno, credenciales o fotos. La aplicación debe cargar el código vigente para usar la nueva interfaz.

## Verificación

Cinco pruebas específicas aprobadas inicialmente en 3,684 s: catálogos/SQL, edición y revisión, eliminación sin vínculos, baja con participantes/notas conservadas y acumulado intacto, bloqueo de nuevas acciones, consulta propia, permisos/CSRF/cierre e inicialización v25 repetida sin pérdida. Sintaxis JavaScript y compilación Python comprobadas.

La suite completa y su resultado final se registran en HISTORY. El intento de inspección visual de una DEMO aislada no logró conexión del navegador al servidor local; no declarar nueva revisión visual aprobada. No se probó alterando datos de trabajo ni se usó la base local para el ensayo.

Verificación final: suite completa de 176 pruebas aprobada en 159,971 s, comprobación adicional del tipo vigente en el reporte individual aprobada en 0,870 s. Dos expectativas antiguas de versión/paleta corregidas tras la primera suite. Logs .tmp/operaciones-v26/suite-final.log; sintaxis, compilación y diff correctos.

Actualización posterior: [v27 Departamento/Zona y participantes](24_operaciones_ubicacion_retiros.md) sustituye ubicación, orden de formulario/tabla y añade retirada individual confirmada. La baja de operación completa conserva su alcance v26; no equivale a retirar participantes.
