# 03. Modelo de datos

## Esquema implementado

**v29, 2026-10-18:** seis tablas aditivas: `revisiones_pruebas` (una constancia por rol/versión/Gestión), `activaciones_pruebas` (Gestión/prueba y revisión), `historial_activaciones_pruebas`, `intentos_pruebas` (único persona/prueba/Gestión, finalización inmutable), `recomendaciones` (evidencia, entradas, modelo y resultados append-only con cadena previa) y `confirmaciones_recomendacion` (observación/actor/fecha inmutables). DASS/CBI anteriores intactos. SQLite local v29/64 tablas, 58 previas preservadas tras respaldo y dos inicializaciones; nuevas vacías, quick_check=ok/FK=0. [Reglas y APIs](27_recomendaciones_sistema.md). El inicializador vigente marca schema_version 29; referencias inferiores a versiones anteriores son históricas.

**Actualización de código v28, 2026-10-17:** se agregan `activaciones_psicometria` (PK Gestión/prueba, revisión/actor/fecha), `historial_activaciones_psicometria` (append-only) e `intentos_psicometria` (único Gestión/persona/prueba). Intentos conservan formulario revisado/versión/huella, respuestas, subescalas finales y revisión del avance; finalizaciones inmutables y FK RESTRICT. Ninguna carga automática de instrumentos o resultados. Véase [diseño y condiciones de activación](25_psicometria_y_red_experimental.md). La descripción v23 siguiente es histórica; las adiciones v24–v28 la amplían.

SQLite usa `PRAGMA foreign_keys = ON`. El esquema `sicose/schema.sql` declara las tablas; `flask --app sicose init-db` agrega las columnas faltantes y marca `app_meta.schema_version` como 23 después de completar las migraciones. La base previa se preserva y amplía; no se eliminan tablas/filas. Fechas técnicas se expresan en UTC; claves numéricas son internas.

| Tabla | Uso y restricciones principales |
|---|---|
| `roles` | Catálogo restringido a ADMINISTRADOR, JEFE_PERSONAL e INSTRUCTOR_VOLUNTARIO; seed repetible. |
| `usuarios` | `username` único sin distinguir mayúsculas; `password_hash` obligatorio; `password_version` para invalidar sesiones tras restablecimiento; nombre de foto aleatorio en `foto_perfil`; FK restrictiva a rol; estados y timestamps. |
| `solicitudes_registro` | Historial de alta 1:1 con usuario; estado PENDIENTE/APROBADA/RECHAZADA, revisor y fecha. |
| `invitaciones` | Hash SHA-256 de token aleatorio, correo opcional, expiración y uso único; el token claro solo se devuelve al crearla. |
| `instructores` | Perfil 1:1 con usuario, FK restrictiva. |
| `voluntarios` | Perfil 1:1 con usuario; nombres y apellidos separados; fecha completa de nacimiento; código institucional único generado desde las iniciales y fecha; especialidad principal nullable con catálogo aprobado; instructor asignado opcional referenciado a perfil de instructor. La fecha completa y especialidad de perfiles históricos pueden ser NULL hasta su actualización. |
| `periodos` | Nombre único, rango de fechas validado y estados BORRADOR/ACTIVO/CERRADO. |
| `instrumentos` | Metadatos y aprobación PENDIENTE por defecto; no contiene ítems y ninguno está habilitado. |
| `evaluaciones` | Catálogo administrado; nuevas evaluaciones inactivas por defecto, categoría/origen restringidos y enlace opcional a instrumento. Psicométricas no se activan sin aprobación del instrumento. |
| `asignaciones_evaluacion` | Relaciona voluntario activo, período activo y evaluación activa; única por combinación; control de estado por backend. |
| `versiones_ponderacion` | Versiones únicas por período y estado; no se publican ni calculan automáticamente en esta fase. |
| `pesos_evaluacion` | Relación N:M versión/evaluación, PK compuesta, peso entre 0 y 1; suma de 100% pendiente de validación transaccional antes de publicar. |
| `intentos` | FK a asignación, número único positivo por asignación; score opcional restringido a 0–100. El esquema conserva soporte para historial, pero no se generan intentos psicométricos sin formulario autorizado. |
| `respuestas` | FK restrictiva a intento y referencia única por intento; tabla vacía y sin reactivos ni lógica psicométrica. |
| `calificaciones` | FK a asignación y usuario que registra; nota 0–100; correcciones enlazables sin sobrescribir la fila previa. Operación manual habilitada solo para evaluaciones no psicométricas. |
| `capacitaciones` | Historial de cursos asociado a voluntario; instructor/admin registran para perfiles dentro de su ámbito. |
| `asistencias` | Registro por voluntario/fecha/actividad con estado histórico y estado detallado (`ASISTE`, `ATRASO`, `PERMISO`, `FALTA`); la consulta valida ámbito de Jefe de Personal y permite último día o rango de fechas. |
| `auditoria` | Actor nullable (fallos de usuario desconocido), acción, resultado, IP y fecha. No guarda contraseñas, hashes ni username fallido. |

## Relaciones

`usuarios` N:1 `roles`; los perfiles `instructores` y `voluntarios` tienen FK 1:1 a `usuarios`. Una solicitud se vincula al usuario y, opcionalmente, a una invitación. Un voluntario puede referir su instructor. `periodos` 1:N versiones de peso; `versiones_ponderacion` N:M `evaluaciones`; asignación conecta voluntario/período/evaluación; una asignación agrupa intentos, respuestas y calificaciones; voluntarios agrupan capacitación y asistencia. Auditoría refiere al actor cuando existe. Las restricciones de borrado conservan historial con `RESTRICT` o `SET NULL`, nunca cascada para resultados.

## Autenticación y roles

La cuenta guarda el nombre de rol por FK y un hash generado por Werkzeug (scrypt predeterminado de la versión instalada), nunca la contraseña original. Solo estado ACTIVO puede completar login; cuentas pendientes/inactivas no obtienen sesión. El seed inserta únicamente ADMINISTRADOR y no modifica una cuenta existente. No se crean cuentas de Jefe de Personal o Instructor Voluntario demo automáticamente.

## Decisiones y límites

El registro público crea usuario y perfil en estado PENDIENTE con contraseña hasheada y sin sesión. Un administrador aprueba o rechaza la solicitud. Las rutas heredadas de invitación se conservan, sin formulario de creación en el dashboard actual. Las invitaciones duran siete días, son de un solo uso, guardan solo el hash del token y no se envían por correo: el administrador comparte manualmente el enlace mostrado al crearlas. Administración crea directamente las cuentas de Jefe de Personal en estado ACTIVO con hash de contraseña y perfil asociado; puede editar o desactivar. Desactivar un Jefe de Personal conserva su cuenta/perfil y desvincula los voluntarios activos para evitar nuevas operaciones bajo una asignación inactiva. Los Jefes de Personal consultan, editan y desactivan perfiles activos asignados a su cuenta; además registran solicitudes pendientes, con asignación al Jefe autenticado y aprobación/rechazo exclusivo del Administrador. Se reutilizan `solicitudes_registro` y `voluntarios.instructor_id`, sin requerir nuevas tablas de solicitud en 4A. Aprobar sin enviar asignación conserva la existente y valida que el Jefe siga activo.

Los códigos internos de rol se actualizaron en el esquema v5. La migración renombra `INSTRUCTOR` a `JEFE_PERSONAL` y `VOLUNTARIO` a `INSTRUCTOR_VOLUNTARIO` conservando los IDs y actualiza categorías/orígenes históricos de evaluación. El esquema v6 agrega campos de identidad del Instructor Voluntario de forma aditiva. El esquema v7 añade `asistencias.estado_detalle`; preserva `estado` histórico y asigna una categoría inicial (`PRESENTE`→`ASISTE`, `AUSENTE`→`FALTA`, `JUSTIFICADO`→`PERMISO`) para hacer consultables los datos previos sin reemplazarlos. El esquema v8 agrega `voluntarios.especialidad_principal`, nullable para preservar los perfiles previos; solicitudes nuevas y altas manuales validan el catálogo acordado. El año mostrado en el encabezado se calcula dinámicamente y no cambia filas de `periodos`. Los cursos tienen listado, alta y edición por ámbito, sin borrado físico. El código institucional se forma con las iniciales de nombres, apellido paterno y materno, más `DDMMAA`; la colisión devuelve un error y requiere revisión. Nacionalidad/residencia ampliada y relaciones de cursos/operaciones están implementadas en v11; ver detalle abajo. `antiguedad_desde` almacena una fecha y `experiencia_operaciones` texto libre; no calculan antigüedad ni completan un modelo relacional de operaciones. La especialidad principal quedó resuelta en v8, incorporación/antigüedad calculada quedó implementada en v9 y secundarias en v10. Los nombres internos de tablas y columnas (`instructores`, `voluntarios`, `instructor_id`, `voluntario_id`) se conservan para no romper relaciones ni datos existentes.

Las fotos PNG/JPEG (máximo 3 MiB y 4096 × 4096) se guardan en `instance/perfiles`, fuera de static, con nombre generado y acceso por API autenticada con control por rol/ámbito. No se guardan bytes en SQLite. Administración puede editar perfil y restablecer clave de Jefes de Personal/Instructores Voluntarios; no se muestra la clave anterior. El backend guarda un hash nuevo e incrementa `password_version`, por lo que las sesiones previas dejan de autenticar.

IDs numéricos son internos y no autorizan por sí mismos acceso a un recurso. Campos de respuestas son sensibles; aún no se almacenan. Los instrumentos permanecen pendientes y sin reactivos. El modelo de tablas futuras no significa que APIs o cálculos estén implementados. Reglas de retención, privacidad, faltantes, pesos y publicación necesitan aprobación institucional antes de operar evaluaciones.

## Esquema v9 — Residencia e incorporación

Migración aditiva con `pais_residencia`, `departamento_residencia` y `ano_incorporacion` nullable en `voluntarios`. No rellena perfiles existentes ni modifica `antiguedad_desde`. Catálogo inicial: Bolivia; Beni, Chuquisaca, Cochabamba, La Paz, Oruro, Pando, Potosí, Santa Cruz y Tarija. El servidor comprueba dependencia país/departamento, año entero positivo y no futuro; NULL representa dato no registrado. `antiguedad_anos` se calcula en consulta como año actual local del servidor menos incorporación, no se guarda en SQLite. Residencia no representa nacionalidad ni lugar de nacimiento.

Los campos se registran desde altas administrativas o solicitudes por Jefe, y se editan desde gestión autorizada. El Jefe solo consulta/edita perfiles activos asignados. No se incorporan al registro público; desde v11 Instructor consulta solo residencia/nacionalidad propias, con incorporación aún oculta; autoservicio limitado a correo y foto. La política institucional de retención y el uso de datos reales siguen pendientes antes del piloto.

## Esquema v10 — Especialidades secundarias

Tabla `especialidades_secundarias`, con clave primaria `(voluntario_id, especialidad)`, FK a `voluntarios(usuario_id)` con borrado restringido y CHECK del catálogo acordado. La principal puede pertenecer al conjunto; sus cambios no alteran automáticamente las secundarias. Lista vacía representa ausencia; no se infieren datos históricos. Actualización del conjunto y auditoría en una transacción; permisos por objeto en backend. Migración aditiva/idempotente: tablas anteriores preservadas. Cursos y operaciones relacionales fueron completados en v11.

## Esquema v11 — Geografía y relaciones operativas

- `perfil_geografico`: PK/FK voluntario_id con borrado restringido; país de residencia, departamento/provincia y nacionalidad (país) opcionales. Permite ampliación sin reconstruir CHECK de columnas v9. Si existe fila se usa esa fuente incluso para NULL; en ausencia se conserva lectura v9. Catálogo/validación en servidor; Bolivia restringida a nueve departamentos, otros países provincia libre.
- `cursos`: nombre único, catálogo administrativo. `capacitaciones.curso_id`: FK opcional con borrado restringido; históricos NULL y nombre previo preservado, sin correspondencia automática.
- `operaciones`: tipo_evento, lugar, fecha_inicio, fecha_fin opcional e institucion_responsable. `participaciones_operacion`: PK compuesta operacion_id/voluntario_id, ambas FK restringidas. Fechas y alcance validados por servidor; sin eliminación/desvinculación habilitada.
- Instructor obtiene solo cursos propios sin observaciones y operaciones propias con participante propio; no obtiene incorporacion ni notas. Inicialización aditiva/idempotente; datos anteriores conservados.

### Corrección vigente — Registro de cursos (2026-10-10, v12)

La pantalla “Capacitaciones y Cursos” registra cursos independientes de personas. Incluye nombre, tipo (Capacitación, Especialización, Actualización, Taller, Seminario (Webinar)), entidad organizadora, inicio/fin, estado (Próximo, En curso, Finalizado) y observaciones opcionales. Nombre, tipo y estado obligatorios para registros nuevos; fechas/entidad opcionales; fin requiere inicio y no puede precederlo. Estado se elige manualmente, sin deducirlo de fechas. Administrador registra/edita; Jefe consulta el catálogo según permisos ya acordados. Edición mediante modal responsivo con datos precargados y errores en el modal.

Se retiraron de esta pantalla el selector de Instructor y el formulario de asignación. Los registros personales históricos, sus vínculos y APIs se conservan; no hay interfaz nueva de asignación en esta entrega. “Mis cursos” sigue consultando historial personal sin observaciones. Las observaciones del catálogo son distintas del historial personal y solo se muestran a Administrador/Jefe.

Migración v12 aditiva: campos nuevos nullable en cursos, sin inferir tipo, estado ni fechas de históricos. Respaldo SQLite previo, datos de 23 tablas anteriores preservados, inicialización repetida, quick_check=ok y FK=0. 59 pruebas aprobadas en 42,354 s (ejecución final); cuatro escenarios Chromium con API simulada, Administrador/Jefe a 360/1447px, opciones exactas y edición modal correctas. Compilación Python, sintaxis JavaScript y diff comprobados.

### Entrega vigente — Asistencia, correcciones, calendario y reporte (2026-10-10, v13)

- Administrador consulta/registra/corrige asistencia; Jefe solo personal activo asignado. La llamada muestra nombre del responsable autenticado, gestión anual de la fecha seleccionada y fecha; conserva actividad obligatoria. Los cuatro estados exactos son Asiste, Atraso, Permiso y Falta. Llamada nueva inicia todas las filas en Falta; al elegir fecha/actividad existente se cargan sus estados guardados para corregirlos.
- Clave única persona/fecha/actividad: guardar otra vez actualiza el mismo registro. Corrección conserva estado anterior/nuevo, actor y fecha UTC en historial_asistencias mediante trigger; cambios se auditan. Repetir el mismo estado no crea corrección ni sustituye al último responsable. No se permiten cambiar identidad/fecha/actividad mediante el PATCH de corrección. Históricos no se borran ni se fabrican correcciones anteriores.
- Instructor consulta solo su calendario anual y totales de los cuatro estados, sin datos de terceros ni observaciones ni edición. El día puede tener varias llamadas; totales cuentan registros, no días calendario. Sin registro no se considera Falta.
- Reporte matricial por rango inclusivo de fechas, sin materia ni filtros adicionales. Columnas por fecha/actividad, código y nombre, cuatro totales y porcentaje. Asiste y Atraso cuentan como asistencia; Permiso excluido: (Asiste + Atraso)/(Asiste + Atraso + Falta), redondeado a dos decimales; sin denominador, No disponible. Es un indicador operativo aprobado para esta entrega, no una nota ni promedio oficial de Fase 5B. Jefe exporta solo ámbito activo asignado; Administrador todo su alcance; Instructor no exporta reporte administrativo.
- PDF imprimible horizontal: matriz dividida en bloques de hasta ocho llamadas, filas paginadas y cabeceras repetidas, sin perder columnas. Carimbo SBRAB en cada página con escudo, nombre completo institucional y generación en hora de Bolivia; paginación, rango, leyenda y fórmula visibles. Sin observaciones; descarga privada no-store y auditoría mínima.
- Migración local v13 tras respaldo: 23 tablas anteriores preservadas, inicialización repetida, quick_check=ok y cero infracciones FK. Entorno, secretos y base existente conservados. Aceptación operativa del solicitante pendiente; Fase 5A aún requiere revisar integralmente cursos/notas y sus casos de corrección. Retención/privacidad y autorización institucional siguen pendientes antes del piloto.


### Perfil y directorio vigentes — Grado e incorporación (2026-10-10, v14)

- Directorio con Nombre completo, Código, Grado, Especialidad Principal, Estado, Antigüedad y Acciones. Estado horizontal: ACTIVO verde, INACTIVO rojo, con texto identificable. Ver consulta en modal los datos permitidos y foto; Editar perfil usa modal y Desactivar conserva baja lógica. Restablecer contraseña sigue siendo exclusivo del Administrador, dentro de Editar perfil; nunca se muestra la contraseña guardada ni su hash.
- Grados permitidos: Instructor Inicial, Instructor Segundo, Instructor Primero, Instructor Principal e Instructor Mayor. Administrador los asigna/edita; Jefe solo en personal activo asignado y puede proponerlo al solicitar el alta de su equipo. Instructor consulta el suyo sin editar. La solicitud pública no permite enviar grado; queda NULL hasta revisión del personal autorizado. No se asigna un grado por defecto a históricos ni se infiere por antigüedad.
- Una sola Fecha de incorporación en alta y edición. Al registrarla se sincronizan fecha_incorporacion, antiguedad_desde y ano_incorporacion. Antigüedad = año calendario actual del servidor menos año de incorporación, sin descontar meses/días. Fechas inválidas/futuras y año/fecha contradictorios rechazados. Históricos mantienen año y fecha anterior, incluso si difieren, hasta completar explícitamente la nueva fecha; no se fabrican fechas desde un año. Borrar una fecha canónica existente borra también sus dos valores derivados; un formulario sin fecha histórica completa conserva el año previo.
- Alta administrativa permite ACTIVO o INACTIVO. Solicitudes de Jefe/públicas permanecen PENDIENTE, sin selector que habilite acceso, hasta aprobación administrativa. Las cuentas inactivas/pendientes no acceden a información protegida.
- Alta y solicitudes incluyen nombres, ambos apellidos, nacimiento, código generado en servidor, especialidad principal, usuario, correo, contraseña, nacionalidad, departamento y foto PNG/JPEG (máximo 3 MiB). Correo, nacionalidad, departamento y foto ahora son obligatorios también en servidor. Fecha de incorporación y grado son opcionales; las solicitudes públicas no incluyen grado. Residencia Bolivia oculta en las pantallas nuevas, nacionalidad independiente y catálogo latinoamericano existente. Países históricos se conservan en consulta/edición; no hay reclasificación automática a Bolivia en migración. Botón Guardar. Invitaciones usan el mismo formulario y validaciones.
- Migración v14 aditiva: grado y fecha_incorporacion nullable, sin rellenar perfiles anteriores. Respaldo local previo; 24 tablas anteriores preservadas, inicialización repetida, quick_check=ok y cero infracciones de claves foráneas. No se recrearon .venv, .env ni base local.

Verificación actual (2026-10-10): 64 pruebas aprobadas en 31,611 s, con bases aisladas. Ocho escenarios Chromium con datos sintéticos/API simulada (Administración, Jefe, Instructor y solicitud pública; 360/1447 px), modales precargados, campos/opciones/roles y ausencia de desborde comprobados. Compilación Python, sintaxis JavaScript y git diff --check correctos. La primera ejecución detectó dos expectativas antiguas de etiquetas (Guardar y retiro de Especialidad en tabla de asistencia); actualizadas y suite completa repetida. No se afirma cierre de Fase 5A ni aceptación institucional del piloto.


## Primera entrega implementada de Fase 5B — 2026-10-11 (v15)

- Rol COMANDANTE_GRUPO con panel propio y cargo único SBRAB. Administrador crea/edita/desactiva cuentas y restablece contraseña; una sola cuenta Comandante ACTIVO, garantizada también por triggers SQLite. No se reutiliza una cuenta para otra persona ni se elimina autoría; nombre editable e historial con nombres capturados. No se creó una cuenta automáticamente.
- Seguimiento 5B para Administrador/Jefe/Comandante: selección de persona activa/período, perfil básico, formación, asistencia y notas sin asignar históricos a nuevas fuentes. Jefe solo personal activo asignado. Comandante consulta seguimiento de personal activo SBRAB y registra/corrige solo su aportación; sin administración ni observaciones/motivos/referencias privadas ajenas. Instructor sin acceso numérico 5B.
- Cinco fuentes independientes: FISICA_1, FISICA_2, ACADEMICA, DESEMPENO_JEFE y DESEMPENO_COMANDANTE. Notas nuevas 0–100 con hasta dos decimales, almacenadas en centésimas enteras; solo período ACTIVO. Física: Admin/Jefe autorizado. Académica inicial: Jefe; requiere motivo y formación personal referenciada. Desempeño inicial de cada evaluador: Jefe/Comandante correspondiente. Administración puede corregir aportaciones existentes conservando responsable y autor de corrección.
- Cadena por persona/período/fuente: primera nota única, corrección solo de la vigente, inserción serializada y anteriores conservadas. No admitir autor/responsable arbitrarios en JSON. Jefe/Comandante no corrigen Desempeño de otro titular; si cambió responsable, la corrección histórica requiere Administración. Motivo y referencias se conservan como instantánea de respaldo académico; editar el curso después no altera ese respaldo.
- Migración v15: ampliar CHECK de roles preservando IDs/referencias y añadir notas_operativas/respaldo_academico; triggers de Comandante único se crean después de ampliar roles. Inicialización local repetida tras respaldo, 24 tablas anteriores preservadas (roles anteriores incluidos), quick_check=ok y cero infracciones FK. Tablas nuevas vacías, sin cuentas ni notas inferidas. .venv/.env/base existente conservados.
- Verificación: **73 pruebas aprobadas en 80,440 s**, ocho escenarios Chromium (Administración/Jefe/Comandante/gestión de cuenta, 360/1447 px), sin desborde ni errores; modales y envíos, fuentes/roles y período cerrado comprobados. Compilación Python, sintaxis de ambos JavaScript y git diff --check correctos. Pruebas de migración incluyeron esquemas antiguos; se corrigió orden de creación de triggers y fixture de catálogo de roles.

### Límites de esta entrega

Límite histórico al terminar v15: publicación/configuración, vinculación de fuentes y activo único todavía estaban pendientes; quedan implementados en v16 según la actualización siguiente. Cálculo conjunto y cierre/reapertura con instantáneas de resultados continúan pendientes. No se declara cerrada 5B. Las APIs/notas históricas y pantalla de asignaciones anterior se mantienen por compatibilidad; no se convierten ni participan automáticamente en el futuro cálculo 5B. Instructor conserva su avance existente, sin nuevo resultado 5B. La aceptación operativa del solicitante y requisitos institucionales mantienen sus pendientes.

Siguiente entrega concreta: cálculo provisional exacto con faltantes y redondeo; después cierre/reapertura con instantáneas. Los permisos y períodos se validan en servidor, sin modificar históricos silenciosamente.


## Segunda entrega de Fase 5B — 2026-10-11 (v16)

Administrador dispone de **Períodos y configuración**: crea borradores anuales enero–diciembre, configura cinco fuentes mediante modal y publica/activa en una transacción. La revisión del borrador evita sobrescribir cambios concurrentes. Publicación exige fuentes completas con evaluaciones manuales activas de categoría compatible; dos fuentes de la misma categoría pueden usar la misma evaluación de catálogo, manteniendo sus notas independientes. Configuración versión 1 con regla PROMEDIO_TRES_V1 (igual importancia de los tres componentes); no habilita porcentajes arbitrarios ni cálculo aún.

La publicación congela fuentes, nombres/códigos/categorías, autor y fecha UTC. Cambiar el catálogo después no reescribe esas referencias. Un solo período puede activarse bajo concurrencia, también protegido por triggers. No se cierran otros períodos automáticamente. Notas/correcciones 5B requieren período ACTIVO y configuración PUBLICADA; configuración_id/evaluacion_id se resuelven en servidor, sin aceptar esos valores del cliente. La API de calificación anterior no registra notas en períodos configurados 5B; los registros anteriores siguen consultables.

Migración v16 aditiva: configuraciones_5b y fuentes_configuracion_5b, dos referencias nullable en notas_operativas y restricciones. Respaldo local previo, 26 tablas anteriores preservadas, inicialización repetida, quick_check=ok y cero infracciones FK. Períodos y notas históricas sin modificación ni adopción; referencias anteriores NULL. La base local no tenía períodos ACTIVO; una base histórica que sí los tenga bloqueará nuevas activaciones hasta un tratamiento explícito en la entrega de cierre, sin alterar sus estados al migrar.

Verificación actual: **77 pruebas aprobadas en 86,620 s** (bases aisladas), incluyendo publicación concurrente, revisiones obsoletas, fuentes incompletas/categoría inválida, congelación, permisos/CSRF y preservación v15. Ocho escenarios Chromium con API simulada a 360/1447 px: publicación y modal administrativo, notas por los tres roles y bloqueo de edición sin configuración publicada; sin desborde ni errores JavaScript. Compilación Python, sintaxis de los tres JavaScript, enlaces locales y git diff --check correctos.

Pendientes: cálculo provisional exacto/faltantes/redondeo, cierre y reapertura motivada con cada instantánea preservada, aceptación operativa e institucional/privacidad antes del piloto. **No se declara cerrada Fase 5B.** Siguiente entrega: cálculo provisional vinculado a configuración y últimas notas válidas, separado de asistencia y psicometría.


### Tablas añadidas en v16

- `configuraciones_5b`: una por período (UNIQUE), versión 1, revisión incremental del borrador, BORRADOR/PUBLICADA, regla fija PROMEDIO_TRES_V1, autor de creación/publicación y fecha UTC de publicación.
- `fuentes_configuracion_5b`: clave configuración/fuente, evaluación referenciada y nombre/código/categoría capturados al publicar; cinco fuentes obligatorias para publicación.
- `notas_operativas.configuracion_id` y `.evaluacion_id`: FK nullable para preservar históricos; obligatorias en nuevas inserciones mediante trigger y resueltas por el backend. ON DELETE RESTRICT mantiene referencias.

No se transforman tablas históricas `versiones_ponderacion`/`pesos_evaluacion` en configuración operativa, ni se calculan resultados al migrar. Publicar fija configuración; revisión de borrador no representa un cierre ni un resultado calculado.


## Primera entrega de la reformulación — 2026-10-12 (v17)

Jefe único activo con alcance global sin filtro de asignación; Comandante retirado del acceso operativo, conservado solo en datos históricos. Desempeño del Comandante transcrito por Administrador/Jefe con nombre del evaluador y autor de transcripción separados. Tabla Evaluaciones por gestión y consulta modal de activos/inactivos, habilitación individual con historial y notas 5B bloqueadas al deshabilitar; PDF administrativo con carimbo SBRAB. Instructor consulta habilitación/estado/avance por gestión, todavía sin notas publicadas.

Acuerdos complementarios: Académica acumulará puntos enteros con tope 100; puntos individuales ajustables, gestión de finalización personal y cómputo único. Administrador/Jefe publicarán; después de corrección se conservará la versión publicada anterior hasta republicar. **Cursos con puntos, programación/reprogramación física, No cumplida=0, acumulación y publicación/republicación aún pendientes.** El flujo manual académico anterior y configuraciones congeladas no se convierten automáticamente. Psicometría continúa bloqueada; Fase 5B no cerrada.

Evidencia vigente: 81 pruebas aprobadas en 45,711 s; ocho escenarios UI, PDF sintético de cinco páginas, compilación/sintaxis/enlaces/diff correctos. Migración v17 tras respaldo, 28 tablas anteriores preservadas, inicialización repetida, quick_check=ok, FK=0. Detalles en [reglas y estado](10_reformulacion_evaluaciones.md). Siguiente entrega: cursos con puntaje y asignación/finalización individual con historial.


## Cursos y formación personal implementados — 2026-10-12 (v18)

Administrador/Jefe registran/editar catálogo con puntaje entero 0–100, fechas/entidad obligatorias en cursos nuevos y estado automático de Bolivia. Asignación personal/múltiple sin duplicados, finalización independiente con puntaje y fecha explícitos, correcciones con actor/fecha/motivo/revisión y valores anteriores preservados. Edición del catálogo no reescribe datos capturados al asignar. Inactivos solo consulta/historial. Instructor ve sus estados y formación histórica, sin puntajes hasta publicación; Dashboard/seguimiento enlazan las participaciones. PDF de catálogo filtra estado calculado. Histórico sin datos completos permanece intacto y sin puntos inferidos.

Verificación vigente: 86 pruebas aprobadas en 87,375 s; 12 escenarios UI, sin desborde/errores; migración local tras respaldo e inicialización repetida preservando 29 tablas, quick_check=ok y FK=0. Compilación, sintaxis, enlaces y diff correctos. Detalles en [reglas y entrega v18](11_cursos_formacion.md). Pendientes acumulado académico hasta 100, físicas/reprogramación/No cumplida, publicación/republicación y cierres; no se declara cierre 5B ni del piloto.


Las tablas nuevas son participaciones_curso (curso/persona únicos, estado/revisión, datos capturados y puntaje obtenido/fecha nullable solo fuera de Finalizado) e historial_participaciones_curso (revisión única por participación con actor/nombre/fecha/motivo/valores). cursos.puntaje es nullable para históricos, con CHECK entero 0–100; las relaciones FK son restrictivas. No se convierte capacitaciones ni se crean notas/calificaciones académicas al migrar.


## Ampliación aditiva 5B.1 — 2026-10-13, v19

Tres tablas nuevas: programaciones_fisicas (versiones de fechas comunes por período/fuente), reprogramaciones_fisicas (excepciones por persona con fecha anterior/versión común/actor/motivo) y resultados_fisicos (estado/fecha real y referencias a nota/programación). Claves foráneas restrictivas, unicidad de versiones iniciales y sucesoras, índices e historial inmutable por triggers. No cumplida exige nota cero; Cumplida con cero es distinta. Sin datos inferidos ni columnas previas modificadas; configuraciones y notas históricas preservadas. [Reglas, API, compatibilidad y migración verificada](13_programacion_fisica.md). No añade cálculos ni publicación/cierres.


## Ampliación aditiva 5B.2 — 2026-10-13, v20

Cuatro tablas nuevas: bajas_gestion, historial_gestiones, activaciones_gestion y reglas_calculo_5b. FK restrictivas, historial inmutable, revisión encadenada de activaciones y opt-in de regla nueva único por período/año. Unicidad de ACTIVO operativo excluye gestiones retiradas sin cambiar sus estados originales. Configuraciones/notas anteriores intactas; cálculo académico usa participaciones únicas/revisión vigente/fecha personal, sin duplicar versiones. No persiste resultados publicados ni instantáneas: [reglas, compatibilidad y migración](14_calculos_y_gestiones.md).


## Ampliación aditiva 5B.3 — 2026-10-13, v21

`publicaciones_5b` conserva versiones por persona/Gestión: revisión/enlace anterior, snapshot JSON generado en servidor solo de físicas/formación, fuentes internas, motivo/actor/nombre/fecha. FK restrictivas a persona y regla de Gestión, unicidad de primera versión y de revisión; triggers impiden UPDATE/DELETE. No copia Desempeño ni conjunto, ni modifica notas/configuraciones previas. [Contratos, proyección y migración](15_publicacion_notas.md).

## Ampliación aditiva 5B.4 — 2026-10-14, v22

- `cierres_5b`: período, número/enlace anterior, contexto JSON versionado, firma, motivo, actor/nombre/fecha UTC y totales de personas/incompletos. Primera versión única por Gestión y numeración única.
- `instantaneas_cierre_5b`: PK cierre/persona; copia de fuentes, valores, autoría y cálculo exacto/final. FK restrictivas a cierre y persona.
- `reaperturas_5b`: una reapertura por cierre, motivo, actor/nombre/fecha UTC. Reabrir no elimina ni reemplaza snapshots anteriores.
- Las tres tablas impiden UPDATE/DELETE mediante triggers. No se alteraron configuraciones, notas, cursos o períodos al migrar. Base anterior v21 preservada; no se crean cierres retroactivos para períodos ya cerrados. El cálculo exacto se conserva como fracción de centésimas en JSON, sin aritmética flotante. [Alcance y migración](16_cierres_reaperturas.md).

## Ampliación aditiva de históricos — 2026-10-14, v23

`reaperturas_historicas_5b`: PK interna, `periodo_id` único/FK restrictiva, evidencia JSON versionada, firma de fuentes, motivo, actor/nombre/fecha UTC. Triggers impiden UPDATE/DELETE. No agrega un cierre antiguo a `cierres_5b`; el primer cierre real posterior referencia esta evidencia en su contexto JSON. No cambia notas, configuraciones ni estados al migrar. [Alcance y compatibilidad](16_cierres_reaperturas.md).


## Actualización aditiva v26 — 2026-10-16

Operaciones conserva tipo_evento histórico; nuevas columnas tipo_operativo y estado_operacion con CHECK por catálogos (NULL histórico sin inferir), revision INTEGER positiva DEFAULT 1. Nueva bajas_operacion con PK/FK RESTRICT a operación, motivo, actor FK a usuarios, nombre y fecha UTC; evidencia inmutable por triggers. Total 54 tablas. Eliminación física solo sin vínculos; participantes/notas fuerzan baja histórica, sin cascadas ni retiro de resultados. Véase [operaciones v26](23_operaciones_tipos_estados.md) y schema.sql para restricciones exactas.

## Actualización v27 — 2026-10-16

operaciones añade departamento/zona con catálogo/longitud y NULL histórico; lugar intacto. participaciones_operacion añade revision positiva; retiros_operacion registra baja personal inmutable por clave operación/persona y FK compuesta RESTRICT, motivo/autor/fecha. Total 55 tablas. La retirada individual excluye notas de cálculos abiertos sin borrarlas, con protección por cierre y revisión. Véase [v27](24_operaciones_ubicacion_retiros.md).
