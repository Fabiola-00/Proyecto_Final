# 02. Arquitectura técnica

## Esquema implementado

Aplicación Flask monolítica modular: frontend HTML/CSS/JavaScript nativo en `frontend/` → endpoints JSON del blueprint `sicose.auth` → servicios/persistencia `sicose.db` → SQLite en `instance/sicose.sqlite3`. La fábrica `sicose.create_app` permite configuración aislada en pruebas. El directorio `instance/` no se publica como estático y está excluido de Git. Mismo origen web/API.

## Módulos presentes

- `sicose.auth`: login, logout y consulta del usuario autenticado mediante Flask-Login.
- `sicose.permissions`: decorador backend `role_required`.
- `sicose.db`: SQLite, esquema aditivo, seed de roles/administrador y auditoría de auth.
- `sicose.models`: objeto de sesión con proyección pública sin hash.
- `sicose.dashboard`: tres rutas HTML protegidas, cada una por rol; `/` redirige según `ADMINISTRADOR`, `JEFE_PERSONAL` o `INSTRUCTOR_VOLUNTARIO`. Se mantienen rutas antiguas como alias de compatibilidad. Las consultas filtran asignaciones según Jefe de Personal/Instructor Voluntario autenticado. Las vistas son iniciales; las funciones futuras deben respetar la matriz de permisos de `docs/01_especificacion_funcional.md`.
- `sicose.management`: solicitudes públicas pendientes, aprobación/rechazo administrativo, alta manual de Instructores Voluntarios activos por administración, asignación a Jefes de Personal activos, edición/desactivación lógica de perfiles con el ámbito comprobado en servidor, y gestión de cuentas de Jefe de Personal exclusiva del administrador. Los directorios ofrecen consulta, edición y desactivación; los formularios de alta son exclusivos de Administración. Jefe de Personal registra solicitudes pendientes asignadas a su equipo; solo Administración aprueba/rechaza. El Instructor tiene Mi perfil para actualizar exclusivamente correo y foto propios; el backend rechaza otros campos. Al desactivar un Jefe de Personal, los Instructores Voluntarios activos quedan sin asignación y se conservan perfiles/historial. El esquema y las rutas heredadas de invitación se conservan para compatibilidad, pero el panel ya no genera invitaciones.
- `sicose.evaluations`: listado/alta/edición del catálogo y listado/alta de períodos para administración, asignaciones de evaluación a Instructores Voluntarios/períodos activos, habilitación psicométrica por ámbito con verificación de aprobación, asistencia con cuatro estados y filtros por persona/fecha, capacitaciones listables/creables/editables dentro del ámbito, notas manuales no psicométricas con correcciones append-only e historial, resultados de intentos visibles solo para roles autorizados, y estados de evaluación sin notas/observaciones en la vista del voluntario.
- `frontend/`: login, plantilla común de dashboards, vistas iniciales por rol, CSS responsivo y JS nativo para navegación móvil/sesión.
- Psicometría: tablas/rutas preparatorias, sin aplicación de instrumentos; el inicio de intento devuelve formulario no disponible. Reportes e IA: sin funcionalidad implementada. La gestión completa de versiones de ponderación y promedios oficiales sigue pendiente.

Separar rutas, servicios, persistencia y validadores. Las reglas de autorización residen en servidor y se aplican antes de consultar/devolver el recurso. API responde errores JSON con código HTTP apropiado sin filtrar trazas o información sensible.

## Seguridad implementada y pendientes

- Werkzeug genera/verifica hash adaptativo de contraseña; nunca se persiste texto plano.
- `SICOSE_SECRET_KEY` es obligatoria y solo se carga del entorno/`.env` local ignorado. La aplicación falla con mensaje claro si falta.
- Cookie `sicose_session` `HttpOnly`, `SameSite=Lax`, `Secure` configurable (`SICOSE_SESSION_COOKIE_SECURE`), sesión permanente de ocho horas.
- Flask-WTF valida CSRF en POST de login y logout; frontend envía `X-CSRFToken`.
- Entradas del login limitadas y consultas parametrizadas. Fallos de autenticación usan respuesta genérica para no revelar si existe la cuenta.
- Flask-Login identifica la sesión. `role_required` valida rol en servidor; API devuelve 401 sin sesión y 403 con rol insuficiente.
- `/api/auth/me` solo serializa id, username, nombre, rol y estado.
- Auditoría registra seed, login exitoso/fallido y logout con id (si conocido), resultado, fecha UTC e IP; nunca guarda contraseña, hash ni username fallido.
- Seed desde variables locales; idempotente y no actualiza contraseñas existentes.
- Pendientes: rate limiting, política formal de retención, recuperación autónoma de cuenta (el restablecimiento administrativo ya existe), monitoreo y hardening de despliegue.
- Base de datos con permisos de sistema operativo, copias de respaldo y retención definidos antes de uso real. Demo con datos ficticios.
- HTTPS, política de privacidad, consentimiento/aviso de uso y respuesta a incidentes son requisitos para despliegue real, fuera del prototipo local.

## API y rutas presentes

`GET /login`; `POST /api/auth/login`; `POST /api/auth/logout`; `GET /api/auth/me`; `GET /panel/administrador`; `GET /panel/jefe-personal`; `GET /panel/instructor-voluntario` (aliases heredados: `/panel/instructor`, `/panel/voluntario`); `GET /mi-perfil` y `PATCH /api/instructor-voluntario/perfil` (Instructor: solo correo/foto propios); `GET /registro`; `POST /api/jefe-personal/instructores-voluntarios` (solicitud pendiente, asignación en servidor al Jefe autenticado); gestión de registro/usuarios de Fase 4; `GET/POST /api/admin/periodos`; `GET/POST/PATCH /api/admin/evaluaciones`; `POST /api/admin/asignaciones`; `GET /api/jefe-personal/asignaciones`; `PATCH /api/jefe-personal/asignaciones/<id>/estado`; `POST/GET /api/jefe-personal/asistencias` (último día o rango, filtro opcional por persona); `GET /api/jefe-personal/capacitaciones`; `PATCH /api/jefe-personal/capacitaciones/<id>`; `POST /api/jefe-personal/instructores-voluntarios/<id>/capacitaciones`; `POST/GET /api/jefe-personal/asignaciones/<id>/calificaciones`; `GET /api/jefe-personal/asignaciones/<id>/resultados`; `GET /api/instructor-voluntario/evaluaciones` (las rutas `/api/instructor/*` y `/api/voluntario/*` siguen como aliases heredados); `GET /gestion/evaluaciones` (admin), `GET /gestion/asistencias`, `GET /gestion/capacitaciones` y `GET /gestion/calificaciones` (admin/Jefe de Personal). `GET /api/admin/estado` devuelve `{"estado":"autorizado"}` tras validar rol administrativo; no es un diagnóstico de salud ni de integridad. La raíz `/` redirige al panel del rol autenticado. El inicio de intentos psicométricos responde no disponible mientras no se aprueben instrumento, formulario y retención.

## Dependencias y ejecución

Flask, Flask-Login, Flask-WTF, python-dotenv y `sqlite3` estándar. Flask-Login evita una implementación casera del ciclo de sesión; Flask-WTF aporta CSRF; dotenv integra configuración local con Flask CLI. No se introduce ORM ni framework frontend. SQLite se inicializa con `flask --app sicose init-db`: esquema SQL idempotente y versión técnica en `app_meta`, conservando tablas/datos previos. `flask --app sicose seed-admin` crea el usuario de demo.

## Límites

SQLite es adecuado para el prototipo local; multiinstancia/alta concurrencia requiere revisar persistencia. El servidor Flask integrado es solo desarrollo: un despliegue requerirá WSGI, HTTPS, cookies Secure, secretos y revisión de seguridad. No es un sistema clínico ni una plataforma diagnóstica. La IA futura debe ser invocable por Jefe de Personal, auditable, revisable por profesional y nunca decisión automática.

## Perfil v9

`sicose.perfil_residencia` valida el catálogo de residencia y el año de incorporación y calcula antigüedad sin persistirla. Gestión administrativa y solicitudes por Jefe reutilizan esas reglas; la API de listado devuelve campos v9 solo a Administrador/Jefe, dentro del ámbito. No se amplía la proyección del Instructor ni su autoservicio. Migración aditiva, nullable, idempotente y sin reinterpretar la fecha histórica.

## Fase 4B — Rutas y autorización v11

`relaciones_perfil.py` separa catálogo/operaciones del módulo de evaluaciones. GET `/api/cursos` Administrador/Jefe; POST y PATCH `/api/cursos[/<id>]` solo Administrador. Capacitaciones existentes aceptan curso_id opcional validado; se mantiene compatibilidad de nombres históricos. GET `/api/instructor-voluntario/capacitaciones` devuelve proyección propia sin observaciones; página `/mis-cursos`.

GET `/api/operaciones` por ámbito; POST/PATCH de eventos solo Administrador; POST `/api/operaciones/<id>/participaciones` Administrador/Jefe con validación de personal activo y equipo. Instructor recibe solo eventos propios con su propia participación; ningún control mutable. Página `/gestion/operaciones` disponible por rol. Sin borrado/desvinculación habilitados. Mutaciones con CSRF y auditoría mínima.

Geografía ampliada validada en `perfil_residencia.py`, persistida en perfil_geografico sin reconstruir columnas v9. La página Mi perfil muestra residencia/nacionalidad propias en lectura; PATCH de autoservicio continúa aceptando únicamente correo/foto. Incorporación no se expone.

### Actualización vigente — Cursos por Jefe y PDF operativo (2026-10-10)

El solicitante autorizó también al Jefe de Personal a crear/editar el catálogo común; esta decisión sustituye la exclusividad administrativa anterior. Administrador y Jefe ven formulario Registro de curso, edición modal y menú/título “Capacitaciones y Cursos”. La asignación de personas continúa fuera de esta pantalla; historial personal conservado.

Reporte GET `/api/cursos/reporte.pdf`, autorizado para Administrador/Jefe; Instructor excluido. Rango obligatorio e inclusivo por fecha de inicio, tipo/estado opcionales combinados; fechas/filtros inválidos rechazados. Cursos sin inicio excluidos; resultado vacío produce PDF explícito. Incluye nombre, tipo, entidad, fechas, estado y total, sin datos personales ni observaciones. Carimbo en cada página con logo SBRAB, nombre institucional completo, fecha/hora de Bolivia y numeración; respuesta privada no-store y auditoría mínima de generación.

ReportLab incorporado a requirements y al entorno existente; no se recreó .venv, .env ni base. Este reporte inicia una entrega operativa acotada de Fase 7; no implementa reportes personales/psicométricos, Excel ni promedios oficiales. Privacidad/retención y aprobación del piloto siguen pendientes.

### Entrega vigente — Asistencia, correcciones, calendario y reporte (2026-10-10, v13)

- Administrador consulta/registra/corrige asistencia; Jefe solo personal activo asignado. La llamada muestra nombre del responsable autenticado, gestión anual de la fecha seleccionada y fecha; conserva actividad obligatoria. Los cuatro estados exactos son Asiste, Atraso, Permiso y Falta. Llamada nueva inicia todas las filas en Falta; al elegir fecha/actividad existente se cargan sus estados guardados para corregirlos.
- Clave única persona/fecha/actividad: guardar otra vez actualiza el mismo registro. Corrección conserva estado anterior/nuevo, actor y fecha UTC en historial_asistencias mediante trigger; cambios se auditan. Repetir el mismo estado no crea corrección ni sustituye al último responsable. No se permiten cambiar identidad/fecha/actividad mediante el PATCH de corrección. Históricos no se borran ni se fabrican correcciones anteriores.
- Instructor consulta solo su calendario anual y totales de los cuatro estados, sin datos de terceros ni observaciones ni edición. El día puede tener varias llamadas; totales cuentan registros, no días calendario. Sin registro no se considera Falta.
- Reporte matricial por rango inclusivo de fechas, sin materia ni filtros adicionales. Columnas por fecha/actividad, código y nombre, cuatro totales y porcentaje. Asiste y Atraso cuentan como asistencia; Permiso excluido: (Asiste + Atraso)/(Asiste + Atraso + Falta), redondeado a dos decimales; sin denominador, No disponible. Es un indicador operativo aprobado para esta entrega, no una nota ni promedio oficial de Fase 5B. Jefe exporta solo ámbito activo asignado; Administrador todo su alcance; Instructor no exporta reporte administrativo.
- PDF imprimible horizontal: matriz dividida en bloques de hasta ocho llamadas, filas paginadas y cabeceras repetidas, sin perder columnas. Carimbo SBRAB en cada página con escudo, nombre completo institucional y generación en hora de Bolivia; paginación, rango, leyenda y fórmula visibles. Sin observaciones; descarga privada no-store y auditoría mínima.
- Migración local v13 tras respaldo: 23 tablas anteriores preservadas, inicialización repetida, quick_check=ok y cero infracciones FK. Entorno, secretos y base existente conservados. Aceptación operativa del solicitante pendiente; Fase 5A aún requiere revisar integralmente cursos/notas y sus casos de corrección. Retención/privacidad y autorización institucional siguen pendientes antes del piloto.

Rutas de asistencia v13: PATCH `/api/jefe-personal/asistencias/<id>` estado exclusivamente; GET `/<id>/historial` por ámbito. `/api/instructor-voluntario/asistencias?gestion=AAAA` se liga siempre a la cuenta autenticada, con proyección fecha/estado; `/mis-asistencias` presenta calendario. GET `/api/jefe-personal/asistencias/reporte` y `/reporte.pdf` admiten solo desde/hasta; backend valida rango/ámbito. Módulos `asistencias.py` y `reportes_asistencias.py`; carimbo compartido con cursos.


Actualización de perfil v14 (2026-10-10): validación compartida de fecha de incorporación con sincronización de año/fecha histórica solo por edición explícita. Grado de catálogo validado en servidor; permisos administrativos/Jefe activo asignado y consulta propia. Alta administrativa admite ACTIVO/INACTIVO; solicitudes siempre PENDIENTE y público sin grado. Altas requieren multipart con foto validada, correo, nacionalidad y departamento. Migración aditiva nullable y auditada por las operaciones existentes; no inferir valores históricos.
