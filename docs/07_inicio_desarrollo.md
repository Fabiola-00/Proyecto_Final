# Inicio de desarrollo en Windows

Guía para ejecutar localmente la base de Fase 2. Requiere Python 3.10 o posterior y PowerShell. Flask usa su servidor de desarrollo, por lo que se limita a la máquina local; no desplegarlo en producción.

## 1. Abrir el proyecto y crear entorno virtual

En PowerShell, desde la raíz del repositorio:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la activación, en esa terminal puede ejecutarse `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` y volver a activar. No cambia la política permanente del equipo.

## 2. Instalar dependencias y preparar configuración

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

`.env` queda excluido de Git. Define `SICOSE_SECRET_KEY` con un valor aleatorio y `SICOSE_ADMIN_PASSWORD` con una contraseña de desarrollo robusta (mínimo 12 caracteres). Genera un secreto con Python:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copiar la salida a `SICOSE_SECRET_KEY` dentro de `.env`; define también la contraseña local de `admin.demo` en `SICOSE_ADMIN_PASSWORD`. `python-dotenv` hace que Flask CLI lea el archivo local. No uses la misma contraseña en otros sistemas.

## 3. Inicializar SQLite

```powershell
flask --app sicose init-db
```

El comando crea o amplía `instance\sicose.sqlite3`; preserva los datos y la metadata existente, y crea las tablas del modelo inicial y tres roles.

## 4. Crear el administrador DEMO

```powershell
flask --app sicose seed-admin
```

El usuario es `admin.demo`, salvo que configures otro valor. El comando falla si falta la contraseña o no cumple el mínimo, y es idempotente: no cambia una cuenta ya existente. Guarda la contraseña solo como hash.

## 5. Ejecutar la aplicación

```powershell
flask --app sicose run --debug
```

Abrir `http://127.0.0.1:5000/login`. API: `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`; token CSRF se envía en `X-CSRFToken` desde la página de login. Detener el servidor con `Ctrl+C`.

## 6. Ejecutar pruebas

Con el entorno virtual activo:

```powershell
python -m unittest discover -s tests -v
```

Las pruebas usan el cliente de Flask y una base SQLite en memoria; no requieren iniciar un servidor ni alteran la base local.

## Estructura inicial

```text
sicose/                 fábrica Flask, auth, permisos, conexión SQLite y esquema
frontend/               login, página mínima, CSS y JavaScript nativo
tests/                  pruebas HTTP de autenticación, autorización y datos
instance/               base local ignorada por Git
docs/07_inicio_desarrollo.md  instrucciones para Windows
```

## Alcance y seguridad

La sesión dura ocho horas; cookies `HttpOnly`, `SameSite=Lax` y `Secure` configurable para HTTPS. Los endpoints JSON distinguen 401 y 403. Login y logout validan CSRF. Solo `/api/admin/estado` demuestra ahora una ruta limitada al administrador; no es un dashboard ni existe aún API de gestión de usuarios. La limitación de intentos de login y despliegue con servidor WSGI/HTTPS están pendientes.

El servidor incorporado de Flask es exclusivamente para desarrollo local; antes de un despliegue será necesario definir servidor WSGI, HTTPS, secretos y demás requisitos operativos.
