# Operaciones: Departamento/Zona y participantes — v27, 2026-10-16

Esta entrega sustituye la ubicación libre y el orden de la interfaz v26. Conserva sus catálogos de tipo/estado y la eliminación segura de la operación completa.

## Interfaz confirmada

Formulario, tanto alta como edición: Tipo de evento, Estado, Institución, Departamento, Zona, Inicio, Fin. Tipo de evento conserva el campo interno tipo_operativo y las opciones Preventivo/Reactivo/Especial/Emergencia. Estado conserva Planificación/En ejecución/Finalizado/Suspendido, sin inferencia por fechas. Departamento usa los nueve departamentos de Bolivia; Zona es texto libre de 1–160 caracteres. Fin sigue opcional.

Tabla: Departamento, Fecha inicio, Fecha fin, Institución, Estado, Acciones. Estado con etiqueta/color institucional. Acciones en iconos equivalentes a Cursos: Ver, Editar, Asignar, Retirar, Eliminar. Ver reúne tipo, estado, institución, Departamento/Zona, fechas, ubicación histórica y participantes con condición vigente/retirada. Instructor solo consulta su detalle y su participación; no accede a acciones administrativas ni a otros participantes.

La lógica de pantalla se separa de app.js hacia operaciones.js, sin framework ni cambio de rutas anteriores. Formularios en modal, validación, nombres accesibles y distribución responsiva conservados.

## Preservación y migración

operaciones añade departamento y zona con CHECK de catálogo/longitud y NULL para históricos. No se divide ni interpreta lugar automáticamente. La ubicación original se conserva en lugar; para nuevas altas se genera una representación compatible, mientras consultas/reportes priorizan los campos atómicos cuando existen. No sobrescribir ubicaciones previas al clasificar registros históricos.

participaciones_operacion conserva su clave compuesta y añade revision positiva DEFAULT 1. La revisión aumenta al calificar o retirar la participación, de modo que una retirada basada en información anterior a una corrección se rechaza.

retiros_operacion conserva operación/persona como clave compuesta y FK RESTRICT a la participación, motivo obligatorio, actor/nombre y fecha UTC. Triggers impiden modificar/eliminar esta evidencia. No se borra ni modifica ninguna nota histórica.

## Retirada confirmada por el solicitante

Retirar permite seleccionar participantes, igual que en Cursos. Excluye su aporte de los cálculos Académicos abiertos, conservando notas, vínculos e historial. Una baja de la operación completa sigue siendo distinta: conserva los puntos; no equivale a retirar participantes.

- Solo Administrador/Jefe, con CSRF, motivo y revisión de cada participación.
- Cuentas inactivas, participaciones ya retiradas o revisiones obsoletas bloquean la acción.
- Notas de la participación en cualquier Gestión cerrada bloquean la retirada hasta reapertura administrativa. Participaciones sin nota se tratan como pendientes, sin inventar puntos ni cierres.
- Selección múltiple transaccional BEGIN IMMEDIATE: si falla una persona, no se guarda una retirada parcial.
- No se permite volver a asignar ni calificar una participación retirada. No se ha autorizado reactivación de participaciones.
- Consultas propias/administrativas conservan la participación marcada como retirada. Instantáneas de cierres anteriores no se reconstruyen. El reporte individual identifica retirada sin aporte; las notas permanecen en el historial.

Ruta nueva: POST /api/operaciones/<id>/retirar-participantes con motivo y participaciones[{voluntario_id,revision}]. GET /api/operaciones aporta revisión, estado de cuenta y marca retirada para el selector autorizado; Instructor conserva exclusividad propia.

## Migración local y verificación

Respaldo instance/backups/sicose-20261016-pre-v27-3ef77450.sqlite3. Dos inicializaciones, 54 tablas previas comparadas por sus columnas originales y preservadas (excepto schema_version), 55 tablas actuales; retiros vacía, sin Departamento/Zona inferidos, quick_check=ok y FK=0. No seed ni cambios de entorno/fotos/datos para ensayos. Evidencia .tmp/operaciones-v27/migracion.json.

Cinco pruebas específicas aprobadas en 3,514 s: ubicación y validaciones SQL/API, edición, retirada con recalculo/historial, bloqueo de calificación/reasignación, cierre/reapertura, atomicidad, concurrencia por revisión, inactivos, CSRF/roles y migración v26 repetida sin dividir lugar. Resultados de la suite completa al cierre en HISTORY. No se acredita nueva inspección visual en navegador.

Verificación final v27: **181 pruebas aprobadas en 171,192 s**, log .tmp/operaciones-v27/suite-final.log. Cinco específicas finales aprobadas en 3,915 s. Sintaxis JavaScript, compilación Python y git diff --check correctos. Sin nueva revisión visual de navegador.
