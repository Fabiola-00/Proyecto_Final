# 02. Arquitectura técnica

## Esquema implementado

Aplicación Flask monolítica modular: frontend HTML/CSS/JavaScript nativo en `frontend/` → endpoints JSON del blueprint `sicose.auth` → servicios/persistencia `sicose.db` → SQLite en `instance/sicose.sqlite3`. La fábrica `sicose.create_app` permite configuración aislada en pruebas. El directorio `instance/` no se publica como estático y está excluido de Git. Mismo origen web/API.

## Módulos propuestos

- `sicose.auth`: login, logout y consulta del usuario autenticado mediante Flask-Login.
- `sicose.permissions`: decorador backend `role_required`.
- `sicose.db`: SQLite, esquema aditivo, seed de roles/administrador y auditoría de auth.
- `sicose.models`: objeto de sesión con proyección pública sin hash.
- `sicose.dashboard`: tres rutas HTML protegidas, cada una por rol; consultas agregadas filtran asignaciones según instructor/voluntario autenticado.
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

`GET /login`; `POST /api/auth/login`; `POST /api/auth/logout`; `GET /api/auth/me`; `GET /panel/administrador`; `GET /panel/instructor`; `GET /panel/voluntario`; `GET /api/admin/estado` (endpoint mínimo para demostrar autorización). La raíz `/` redirige al panel del rol autenticado. Gestión de usuarios, registro/invitaciones y acciones de los módulos siguen sin implementar.

## Dependencias y ejecución

Flask, Flask-Login, Flask-WTF, python-dotenv y `sqlite3` estándar. Flask-Login evita una implementación casera del ciclo de sesión; Flask-WTF aporta CSRF; dotenv integra configuración local con Flask CLI. No se introduce ORM ni framework frontend. SQLite se inicializa con `flask --app sicose init-db`: esquema SQL idempotente y versión técnica en `app_meta`, conservando tablas/datos previos. `flask --app sicose seed-admin` crea el usuario de demo.

## Límites

SQLite es adecuado para el prototipo local; multiinstancia/alta concurrencia requiere revisar persistencia. El servidor Flask integrado es solo desarrollo: un despliegue requerirá WSGI, HTTPS, cookies Secure, secretos y revisión de seguridad. No es un sistema clínico ni una plataforma diagnóstica. La IA futura debe ser invocable por instructor, auditable, revisable por profesional y nunca decisión automática.
