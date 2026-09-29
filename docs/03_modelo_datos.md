# 03. Modelo de datos

## Esquema implementado

SQLite usa `PRAGMA foreign_keys = ON`. El esquema `sicose/schema.sql` es aditivo e idempotente y actualiza `app_meta.schema_version` a 4. La base local previa se preserva y amplía; `init-db` agrega las columnas faltantes y no elimina tablas/filas. Fechas técnicas se expresan en UTC; claves numéricas son internas.

| Tabla | Uso y restricciones principales |
|---|---|
| `roles` | Catálogo restringido a ADMINISTRADOR, INSTRUCTOR y VOLUNTARIO; seed repetible. |
| `usuarios` | `username` único sin distinguir mayúsculas; `password_hash` obligatorio; `password_version` para invalidar sesiones tras restablecimiento; nombre de foto aleatorio en `foto_perfil`; FK restrictiva a rol; estados y timestamps. |
| `solicitudes_registro` | Historial de alta 1:1 con usuario; estado PENDIENTE/APROBADA/RECHAZADA, revisor y fecha. |
| `invitaciones` | Hash SHA-256 de token aleatorio, correo opcional, expiración y uso único; el token claro solo se devuelve al crearla. |
| `instructores` | Perfil 1:1 con usuario, FK restrictiva. |
| `voluntarios` | Perfil 1:1 con usuario; instructor asignado opcional referenciado a perfil de instructor. |
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
| `asistencias` | Registro por voluntario/fecha/actividad con estado limitado y autor; la operación valida ámbito de instructor y conserva fecha/actividad. |
| `auditoria` | Actor nullable (fallos de usuario desconocido), acción, resultado, IP y fecha. No guarda contraseñas, hashes ni username fallido. |

## Relaciones

`usuarios` N:1 `roles`; los perfiles `instructores` y `voluntarios` tienen FK 1:1 a `usuarios`. Una solicitud se vincula al usuario y, opcionalmente, a una invitación. Un voluntario puede referir su instructor. `periodos` 1:N versiones de peso; `versiones_ponderacion` N:M `evaluaciones`; asignación conecta voluntario/período/evaluación; una asignación agrupa intentos, respuestas y calificaciones; voluntarios agrupan capacitación y asistencia. Auditoría refiere al actor cuando existe. Las restricciones de borrado conservan historial con `RESTRICT` o `SET NULL`, nunca cascada para resultados.

## Autenticación y roles

La cuenta guarda el nombre de rol por FK y un hash generado por Werkzeug (scrypt predeterminado de la versión instalada), nunca la contraseña original. Solo estado ACTIVO puede completar login; cuentas pendientes/inactivas no obtienen sesión. El seed inserta únicamente ADMINISTRADOR y no modifica una cuenta existente. No se crean cuentas de instructor o voluntario demo automáticamente.

## Decisiones y límites

El registro público crea usuario y perfil en estado PENDIENTE con contraseña hasheada y sin sesión. Un administrador aprueba o rechaza la solicitud. Las invitaciones duran siete días, son de un solo uso, guardan solo el hash del token y no se envían por correo: el administrador comparte manualmente el enlace mostrado al crearlas. Administración crea directamente las cuentas de instructor en estado ACTIVO con hash de contraseña y perfil asociado; puede editar o desactivar. Desactivar un instructor conserva su cuenta/perfil y desvincula los voluntarios activos para evitar nuevas operaciones bajo una asignación inactiva. Instructores solo consultan, editan y desactivan perfiles asignados a su cuenta.

Las fotos PNG/JPEG (máximo 3 MiB y 4096 × 4096) se guardan en `instance/perfiles`, fuera de static, con nombre generado y acceso por API autenticada con control por rol/ámbito. No se guardan bytes en SQLite. Administración puede editar perfil y restablecer clave de instructores/voluntarios; no se muestra la clave anterior. El backend guarda un hash nuevo e incrementa `password_version`, por lo que las sesiones previas dejan de autenticar.

IDs numéricos son internos y no autorizan por sí mismos acceso a un recurso. Campos de respuestas son sensibles; aún no se almacenan. Los instrumentos permanecen pendientes y sin reactivos. El modelo de tablas futuras no significa que APIs o cálculos estén implementados. Reglas de retención, privacidad, faltantes, pesos y publicación necesitan aprobación institucional antes de operar evaluaciones.
