# 03. Modelo de datos

## Esquema implementado

SQLite usa `PRAGMA foreign_keys = ON`. El esquema `sicose/schema.sql` declara las tablas; `flask --app sicose init-db` agrega las columnas faltantes y marca `app_meta.schema_version` como 8 después de completar las migraciones. La base previa se preserva y amplía; no se eliminan tablas/filas. Fechas técnicas se expresan en UTC; claves numéricas son internas.

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

El registro público crea usuario y perfil en estado PENDIENTE con contraseña hasheada y sin sesión. Un administrador aprueba o rechaza la solicitud. Las invitaciones duran siete días, son de un solo uso, guardan solo el hash del token y no se envían por correo: el administrador comparte manualmente el enlace mostrado al crearlas. Administración crea directamente las cuentas de Jefe de Personal en estado ACTIVO con hash de contraseña y perfil asociado; puede editar o desactivar. Desactivar un Jefe de Personal conserva su cuenta/perfil y desvincula los voluntarios activos para evitar nuevas operaciones bajo una asignación inactiva. Los Jefes de Personal solo consultan, editan y desactivan perfiles de Instructores Voluntarios asignados a su cuenta.

Los códigos internos de rol se actualizaron en el esquema v5. La migración renombra `INSTRUCTOR` a `JEFE_PERSONAL` y `VOLUNTARIO` a `INSTRUCTOR_VOLUNTARIO` conservando los IDs y actualiza categorías/orígenes históricos de evaluación. El esquema v6 agrega campos de identidad del Instructor Voluntario de forma aditiva. El esquema v7 añade `asistencias.estado_detalle`; preserva `estado` histórico y asigna una categoría inicial (`PRESENTE`→`ASISTE`, `AUSENTE`→`FALTA`, `JUSTIFICADO`→`PERMISO`) para hacer consultables los datos previos sin reemplazarlos. El esquema v8 agrega `voluntarios.especialidad_principal`, nullable para preservar los perfiles previos; solicitudes nuevas y altas manuales validan el catálogo acordado. El año mostrado en el encabezado se calcula dinámicamente y no cambia filas de `periodos`. Los cursos tienen listado, alta y edición por ámbito, sin borrado físico. El código institucional se forma con las iniciales de nombres, apellido paterno y materno, más `DDMMAA`; la colisión devuelve un error y requiere revisión. Nacionalidades/departamentos y catálogos relacionales de cursos/operaciones están pendientes de definición. Los nombres internos de tablas y columnas (`instructores`, `voluntarios`, `instructor_id`, `voluntario_id`) se conservan para no romper relaciones ni datos existentes.

Las fotos PNG/JPEG (máximo 3 MiB y 4096 × 4096) se guardan en `instance/perfiles`, fuera de static, con nombre generado y acceso por API autenticada con control por rol/ámbito. No se guardan bytes en SQLite. Administración puede editar perfil y restablecer clave de Jefes de Personal/Instructores Voluntarios; no se muestra la clave anterior. El backend guarda un hash nuevo e incrementa `password_version`, por lo que las sesiones previas dejan de autenticar.

IDs numéricos son internos y no autorizan por sí mismos acceso a un recurso. Campos de respuestas son sensibles; aún no se almacenan. Los instrumentos permanecen pendientes y sin reactivos. El modelo de tablas futuras no significa que APIs o cálculos estén implementados. Reglas de retención, privacidad, faltantes, pesos y publicación necesitan aprobación institucional antes de operar evaluaciones.
