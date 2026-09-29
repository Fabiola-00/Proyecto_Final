# 02. Arquitectura técnica

## Esquema implementado

Aplicación Flask monolítica modular: frontend HTML/CSS/JavaScript nativo en `frontend/` → endpoints JSON del blueprint `sicose.auth` → servicios/persistencia `sicose.db` → SQLite en `instance/sicose.sqlite3`. La fábrica `sicose.create_app` permite configuración aislada en pruebas. El directorio `instance/` no se publica como estático y está excluido de Git. Mismo origen web/API.

## Módulos propuestos

- `sicose.auth`: login, logout y consulta del usuario autenticado mediante Flask-Login.
- `sicose.permissions`: decorador backend `role_required`.
- `sicose.db`: SQLite, esquema aditivo, seed de roles/administrador y auditoría de auth.
- `sicose.models`: objeto de sesión con proyección pública sin hash.
- `sicose.dashboard`: tres rutas HTML protegidas, cada una por rol; `/` redirige según `ADMINISTRADOR`, `JEFE_PERSONAL` o `INSTRUCTOR_VOLUNTARIO`. Se mantienen rutas antiguas como alias de compatibilidad. Las consultas filtran asignaciones según Jefe de Personal/Instructor Voluntario autenticado. Las vistas son iniciales; las funciones futuras deben respetar la matriz de permisos de `docs/01_especificacion_funcional.md`.
- `sicose.management`: solicitudes públicas pendientes, aprobación/rechazo administrativo, alta manual de Instructores Voluntarios activos por administración, asignación a Jefes de Personal activos, edición/desactivación lógica de perfiles con el ámbito comprobado en servidor, y gestión de cuentas de Jefe de Personal exclusiva del administrador. Los directorios de Instructores Voluntarios y Jefes de Personal ofrecen vistas tabulares CRUD con formularios de alta plegables. Al desactivar un Jefe de Personal, los Instructores Voluntarios activos quedan sin asignación y se conservan perfiles/historial. El esquema y las rutas heredadas de invitación se conservan para compatibilidad, pero el panel ya no genera invitaciones.
- `sicose.evaluations`: CRUD lógico del catálogo y períodos para administración, asignaciones de evaluación a Instructores Voluntarios/períodos activos, habilitación psicométrica por ámbito con verificación de aprobación, asistencia y capacitación por ámbito, notas manuales no psicométricas con correcciones append-only e historial, resultados de intentos visibles solo para roles autorizados, y estados de evaluación sin notas/observaciones en la vista del voluntario.
- `frontend/`: login, plantilla común de dashboards, vistas iniciales por rol, CSS responsivo y JS nativo para navegación móvil/sesión.
- Evaluaciones, reportes e IA: solo tablas preparatorias o documentación; sin lógica de producto.

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
- Pendientes: rate limiting, política formal de retención, gestión/recuperación de cuenta, monitoreo y hardening de despliegue.
- Base de datos con permisos de sistema operativo, copias de respaldo y retención definidos antes de uso real. Demo con datos ficticios.
- HTTPS, política de privacidad, consentimiento/aviso de uso y respuesta a incidentes son requisitos para despliegue real, fuera del prototipo local.

## API y rutas presentes

`GET /login`; `POST /api/auth/login`; `POST /api/auth/logout`; `GET /api/auth/me`; `GET /panel/administrador`; `GET /panel/jefe-personal`; `GET /panel/instructor-voluntario` (aliases heredados: `/panel/instructor`, `/panel/voluntario`); `GET /registro`; gestión de registro/usuarios de Fase 4; `GET/POST /api/admin/periodos`; `GET/POST/PATCH /api/admin/evaluaciones`; `POST /api/admin/asignaciones`; `GET /api/jefe-personal/asignaciones`; `PATCH /api/jefe-personal/asignaciones/<id>/estado`; `POST /api/jefe-personal/asistencias`, `GET /api/jefe-personal/asistencias`; `POST /api/jefe-personal/instructores-voluntarios/<id>/capacitaciones`; `POST/GET /api/jefe-personal/asignaciones/<id>/calificaciones`; `GET /api/jefe-personal/asignaciones/<id>/resultados`; `GET /api/instructor-voluntario/evaluaciones` (las rutas `/api/instructor/*` y `/api/voluntario/*` siguen como aliases heredados); `GET /gestion/evaluaciones` (admin), `GET /gestion/asistencias` y `GET /gestion/calificaciones` (admin/instructor). La raíz `/` redirige al panel del rol autenticado. El inicio de intentos psicométricos responde no disponible mientras no se aprueben instrumento, formulario y retención.

## Dependencias y ejecución

Flask, Flask-Login, Flask-WTF, python-dotenv y `sqlite3` estándar. Flask-Login evita una implementación casera del ciclo de sesión; Flask-WTF aporta CSRF; dotenv integra configuración local con Flask CLI. No se introduce ORM ni framework frontend. SQLite se inicializa con `flask --app sicose init-db`: esquema SQL idempotente y versión técnica en `app_meta`, conservando tablas/datos previos. `flask --app sicose seed-admin` crea el usuario de demo.

## Límites

SQLite es adecuado para el prototipo local; multiinstancia/alta concurrencia requiere revisar persistencia. El servidor Flask integrado es solo desarrollo: un despliegue requerirá WSGI, HTTPS, cookies Secure, secretos y revisión de seguridad. No es un sistema clínico ni una plataforma diagnóstica. La IA futura debe ser invocable por Jefe de Personal, auditable, revisable por profesional y nunca decisión automática.
