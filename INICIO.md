# Cómo instalar y ejecutar SICOSE

Guía para **Windows y PowerShell**, revisada el 2026-10-19. SICOSE utiliza Python, Flask y SQLite; la interfaz funciona en el navegador con HTML, CSS y JavaScript.

Si este proyecto ya tiene `.venv`, `.env` y `instance/sicose.sqlite3`, ve directamente a **Ejecuciones posteriores**. Conserva esos archivos: no necesitas repetir la instalación, inicializar la base ni crear otra vez el administrador.

## Primera puesta en marcha

### 1. Requisitos

- Instalar **Python 3.10 o posterior**, con `pip` y soporte para entornos virtuales. Al instalarlo, habilitar su acceso desde la terminal cuando el instalador ofrezca esa opción. El entorno de este proyecto se comprobó con Python 3.14.7.
- Tener una copia completa del proyecto, incluidos `requirements.txt`, `.env.example`, `sicose/`, `frontend/` y los artefactos del modelo en `output/` que referencia el sistema. No basta copiar solamente los archivos Python.
- Disponer de conexión a Internet para descargar las dependencias durante la instalación.
- Usar PowerShell y un navegador actualizado, por ejemplo Edge, Chrome o Firefox.

No necesitas instalar SQLite como servicio: Python incluye el módulo `sqlite3`. Tampoco necesitas Node.js, npm ni compilar el frontend para ejecutar SICOSE. Git y un editor de código son opcionales si ya tienes los archivos del proyecto.

Si todavía no tienes Python:

1. Abre las [descargas oficiales de Python para Windows](https://www.python.org/downloads/windows/). Para reproducir el entorno revisado, utiliza la rama Python 3.14.
2. Descarga el instalador correspondiente a tu equipo, normalmente **Windows installer (64-bit)**; para Windows ARM usa la variante ARM64. El paquete embebible no es el instalador habitual para esta guía.
3. Ejecuta el instalador y completa la instalación estándar con `pip`. Si aparece la opción **Add Python to PATH**, actívala.
4. Cierra y vuelve a abrir PowerShell para que reconozca la instalación.

Abre una terminal de PowerShell y comprueba Python:

```powershell
py -3 --version
```

Si `py` no está disponible pero Python está instalado, comprueba `python --version` y utiliza `python` en lugar de `py -3` en el siguiente paso. Si ninguno funciona, completa la instalación de Python y abre una terminal nueva.

### 2. Entrar a la carpeta del proyecto

```powershell
Set-Location 'D:\2-Proyecto_FF\Project_FF_v3'
Get-ChildItem requirements.txt
```

Si lo guardaste en otra ubicación, sustituye la ruta. Todos los comandos siguientes se ejecutan desde la raíz, donde están `requirements.txt` y la carpeta `sicose`.

### 3. Crear y activar el entorno virtual

En una instalación nueva:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Si `.venv` ya existe, no lo recrees: ejecuta únicamente la activación. Normalmente aparecerá `(.venv)` al principio de la línea de la terminal.

Si PowerShell bloquea `Activate.ps1`, usa la alternativa **sin activación** indicada más abajo; no hace falta cambiar la política de ejecución del equipo.

### 4. Instalar las dependencias de requirements.txt

Con el entorno activo:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip check
```

`-r requirements.txt` indica que `pip` debe leer el archivo e instalar sus dependencias: Flask, python-dotenv, Flask-Login, Flask-WTF y ReportLab, además de las dependencias que estas bibliotecas necesitan. El comando `pip check` comprueba la compatibilidad de lo instalado.

### 5. Preparar la configuración local

Crea `.env` a partir del ejemplo **solo si todavía no existe**:

```powershell
if (-not (Test-Path -LiteralPath '.env')) {
    Copy-Item -LiteralPath '.env.example' -Destination '.env'
}
notepad .env
```

Genera un secreto aleatorio en la terminal:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copia el resultado en `SICOSE_SECRET_KEY`. Completa `.env` con tus valores locales:

```dotenv
SICOSE_SECRET_KEY=REEMPLAZAR_POR_EL_SECRETO_GENERADO
SICOSE_DATABASE=instance/sicose.sqlite3
SICOSE_SESSION_COOKIE_SECURE=false
SICOSE_ADMIN_USERNAME=admin.demo
SICOSE_ADMIN_PASSWORD=REEMPLAZAR_POR_TU_CONTRASENA_LOCAL
```

Los textos `REEMPLAZAR_...` son marcadores: sustitúyelos antes de continuar. La contraseña del administrador inicial debe tener **entre 12 y 256 caracteres**. `admin.demo` es la cuenta de desarrollo del ejemplo; puedes configurar otro nombre válido de 3 a 80 caracteres con letras, números, punto, guion o guion bajo.

Guarda y cierra el editor. Mantén `SICOSE_SESSION_COOKIE_SECURE=false` para este arranque local por HTTP. Flask CLI carga `.env` mediante python-dotenv. No compartas ni subas `.env` al repositorio; conserva el secreto entre ejecuciones.

### 6. Crear la base SQLite

**Solo para la instalación inicial en una carpeta sin base previa:**

```powershell
python -m flask --app sicose init-db
```

El comando crea el esquema actual y los roles. Con la configuración anterior, la base queda en `instance\sicose.sqlite3`; no tienes que crear el archivo manualmente. El esquema del código revisado es v32.

Si estás continuando una instalación con datos, no ejecutes este paso como parte del inicio diario. Las actualizaciones de esquema se aplican únicamente cuando la entrega correspondiente lo requiera, con respaldo previo y el servidor detenido. No borres la base para solucionar errores de inicio.

### 7. Crear el administrador inicial de desarrollo

```powershell
python -m flask --app sicose seed-admin
```

Este comando usa `SICOSE_ADMIN_USERNAME` y `SICOSE_ADMIN_PASSWORD` de `.env` para crear una cuenta Administrador activa y guarda la contraseña como hash. No crea Instructores, notas ni respuestas de pruebas.

Si esa cuenta administradora ya existe, el comando informa que no se modificó. Cambiar la contraseña en `.env` y volver a ejecutar `seed-admin` **no cambia la contraseña de una cuenta existente**.

### 8. Ejecutar el servidor desde la terminal

```powershell
python -m flask --app sicose run --debug
```

Mantén abierta esa terminal. Cuando aparezca `Running on http://127.0.0.1:5000`, abre en el navegador:

[Iniciar sesión en SICOSE](http://127.0.0.1:5000/login)

Ingresa con el usuario y la contraseña configurados al crear el administrador. La instalación no crea automáticamente una Gestión ni habilita pruebas; esas acciones se realizan después desde los módulos autorizados.

El comando anterior inicia el servidor **local de desarrollo** y facilita la recarga de cambios. No constituye una configuración de despliegue institucional.

Para detenerlo, vuelve a la terminal y pulsa **Ctrl+C**.

## Ejecuciones posteriores

Cada vez que quieras volver a usar el sistema:

1. Abre PowerShell.
2. Entra a la carpeta del proyecto.
3. Activa el entorno existente.
4. Inicia el servidor.

```powershell
Set-Location 'D:\2-Proyecto_FF\Project_FF_v3'
.\.venv\Scripts\Activate.ps1
python -m flask --app sicose run --debug
```

Abre [SICOSE](http://127.0.0.1:5000/login) e inicia sesión con tu cuenta existente. Al terminar, detén el servidor con **Ctrl+C**. Opcionalmente, ejecuta `deactivate` para salir del entorno virtual.

**No repitas** `venv`, la copia de `.env`, `init-db` ni `seed-admin` en el uso diario. Tampoco reinstales las dependencias en cada inicio; hazlo cuando una actualización de `requirements.txt` lo requiera.

## Alternativa sin activar el entorno virtual

Si la activación está bloqueada, puedes llamar directamente al Python de `.venv` desde la raíz del proyecto.

Para instalar dependencias en la primera puesta en marcha:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

Para generar el secreto y ejecutar los comandos **iniciales**, solo cuando correspondan:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))"
# Completar y guardar .env antes de ejecutar los dos comandos siguientes.
.\.venv\Scripts\python.exe -m flask --app sicose init-db
.\.venv\Scripts\python.exe -m flask --app sicose seed-admin
```

Para arrancar normalmente, sin activar el entorno:

```powershell
Set-Location 'D:\2-Proyecto_FF\Project_FF_v3'
.\.venv\Scripts\python.exe -m flask --app sicose run --debug
```

## Problemas frecuentes

| Situación | Qué comprobar |
|---|---|
| No se encuentra `requirements.txt` o el módulo `sicose` | Ejecuta los comandos desde la raíz del proyecto. |
| No se reconoce `python`, `py` o `pip` | Comprueba la instalación de Python y abre una terminal nueva. Usa `python -m pip` o el ejecutable directo de `.venv`. |
| `No module named flask` | Estás usando otro Python o faltan dependencias. Usa el de `.venv` e instala `-r requirements.txt` si aún no lo hiciste. |
| Falta `SICOSE_SECRET_KEY` | Revisa que el archivo se llame exactamente `.env`, esté en la raíz, tenga un secreto y esté guardado. |
| Error al crear el administrador | Revisa usuario/contraseña en `.env` y que hayas inicializado la base nueva antes de ejecutar `seed-admin`. |
| La cuenta ya existe pero la contraseña no coincide | Usa la contraseña vigente. `seed-admin` no restablece cuentas existentes. |
| El puerto 5000 está ocupado | Comprueba si SICOSE ya está abierto. Detén tu servidor anterior con Ctrl+C o usa `python -m flask --app sicose run --debug --port 5001` y abre `http://127.0.0.1:5001/login`. |
| Los cambios de diseño no aparecen | Si arrancaste sin recarga automática, detén y vuelve a iniciar el servidor. Después pulsa Ctrl+F5 en el navegador; no recrees la base ni el entorno. |
| Faltan tablas en una instalación existente | Consulta la migración indicada para esa actualización y respalda antes de aplicarla; no elimines SQLite ni ejecutes seed como solución. |

## Archivos que debes conservar

- `.env`: configuración y secretos locales.
- `.venv/`: entorno y bibliotecas instaladas.
- `instance/sicose.sqlite3`: información persistida, o la ruta que hayas configurado.
- `instance/perfiles/`: fotos locales, o la ubicación configurada.
- `instance/backups/`: respaldos disponibles.
- Los archivos del modelo que referencia el sistema dentro de `output/`.

Detener el servidor no borra estos archivos. No publiques la base, las fotos ni los secretos en Git.

## Referencias del proyecto

- [Dependencias de Python](requirements.txt).
- [Ejemplo de configuración sin secretos](.env.example).
- [Descripción y estado actual](README.md).
- [Guía de desarrollo y antecedentes](docs/07_inicio_desarrollo.md).
- [Continuidad e instrucciones del proyecto](AGENTS.md).

Esta guía se preparó contrastando los comandos con la fábrica Flask, `sicose/db.py`, `requirements.txt` y `.env.example`. Su elaboración no instala paquetes, inicializa la base ni crea cuentas en la instalación existente.
