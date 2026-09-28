# Inicio de desarrollo en Windows

Guía para ejecutar localmente la base de Fase 1. Requiere Python 3.10 o posterior y PowerShell. Flask usa su servidor de desarrollo, por lo que se limita a la máquina local; no desplegarlo en producción.

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

`.env` queda excluido de Git. Reemplazar el marcador de `SICOPE_SECRET_KEY` por un secreto aleatorio local antes de incorporar sesiones. La aplicación mínima de esta fase no usa sesiones todavía. Para generar una clave con Python:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copiar la salida a `SICOPE_SECRET_KEY` dentro de `.env`. `python-dotenv` hace que Flask CLI lea el archivo local.

## 3. Inicializar SQLite

```powershell
flask --app sicope init-db
```

El comando crea `instance\sicope.sqlite3` y una tabla técnica de versión de esquema. No borra ni reinicia una base existente. Las tablas de usuarios y evaluaciones no forman parte de esta fase.

## 4. Ejecutar la aplicación

```powershell
flask --app sicope run --debug
```

Abrir `http://127.0.0.1:5000/`. El endpoint JSON de verificación está en `http://127.0.0.1:5000/api/health`. Detener el servidor con `Ctrl+C`.

## 5. Ejecutar pruebas

Con el entorno virtual activo:

```powershell
python -m unittest discover -s tests -v
```

Las pruebas usan el cliente de Flask y una base SQLite en memoria; no requieren iniciar un servidor ni alteran la base local.

## Estructura inicial

```text
sicope/                 fábrica Flask, conexión SQLite, esquema y web estática
  static/css/           estilos base
  static/js/            entrada JavaScript vacía
  templates/            página inicial
tests/                  pruebas HTTP básicas
instance/               base local ignorada por Git
docs/07_inicio_desarrollo.md
```

El servidor incorporado de Flask es exclusivamente para desarrollo local; antes de un despliegue será necesario definir servidor WSGI, HTTPS, secretos y demás requisitos operativos.
