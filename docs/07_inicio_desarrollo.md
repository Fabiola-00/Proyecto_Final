# Inicio de desarrollo en Windows

Guía para ejecutar localmente la base de Fase 4. Requiere Python 3.10 o posterior y PowerShell. Flask usa su servidor de desarrollo, por lo que se limita a la máquina local; no desplegarlo en producción.

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

El comando crea o amplía `instance\sicose.sqlite3`; preserva los datos y la metadata existente, y crea las tablas del modelo actual y tres roles (versión 3).

Después de actualizar el código a una fase nueva, detén el servidor y vuelve a ejecutar este comando antes de usar los módulos nuevos. Es aditivo e idempotente: añade las tablas faltantes y no reinicia ni borra los datos existentes.

## 4. Crear el administrador DEMO

```powershell
flask --app sicose seed-admin
```

El usuario es `admin.demo`, salvo que configures otro valor. El comando falla si falta la contraseña o no cumple el mínimo, y es idempotente: no cambia una cuenta ya existente. Guarda la contraseña solo como hash.

## 5. Ejecutar la aplicación

```powershell
flask --app sicose run --debug
```

Abrir `http://127.0.0.1:5000/login`. Registro voluntario: `http://127.0.0.1:5000/registro`; las solicitudes quedan pendientes hasta aprobación administrativa. Se pueden crear invitaciones de un solo uso con siete días de vigencia para compartir manualmente. Tras iniciar como administrador, usa el menú **Instructores** para dar de alta/editar/desactivar cuentas y **Voluntarios** para solicitudes y perfiles. Instructores y voluntarios tienen paneles separados con datos según su rol. Las operaciones mutables requieren CSRF mediante `X-CSRFToken`. Detener el servidor con `Ctrl+C`.

## 6. Ejecutar pruebas

Con el entorno virtual activo:

```powershell
python -m unittest discover -s tests -v
```

Las pruebas usan el cliente de Flask y una base SQLite en memoria; no requieren iniciar un servidor ni alteran la base local.

## Estructura inicial

```text
sicose/                 fábrica Flask, auth, permisos, dashboards, SQLite y esquema
frontend/               login, registro, gestión de voluntarios, tres paneles, CSS y JS
tests/                  pruebas HTTP de autenticación, autorización y datos
instance/               base local ignorada por Git
docs/07_inicio_desarrollo.md  instrucciones para Windows
```

## Alcance y seguridad

La sesión dura ocho horas; cookies `HttpOnly`, `SameSite=Lax` y `Secure` configurable para HTTPS. Los endpoints JSON distinguen 401 y 403. Login y logout validan CSRF. Hay vistas iniciales protegidas por rol; los enlaces de gestión aparecen deshabilitados hasta que sus módulos se implementen. `/api/admin/estado` es solo una ruta breve de comprobación de autorización. La limitación de intentos de login y el despliegue con servidor WSGI/HTTPS están pendientes.

Las solicitudes guardan hash de contraseña y permanecen pendientes sin sesión. Las invitaciones no se envían por correo; administración comparte el enlace. Desactivar conserva historial. El servidor incorporado de Flask es exclusivamente para desarrollo local; antes de un despliegue será necesario definir servidor WSGI, HTTPS, secretos y demás requisitos operativos.
