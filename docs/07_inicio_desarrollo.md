# Inicio de desarrollo en Windows

Guía para ejecutar localmente la base de Fase 5. Requiere Python 3.10 o posterior y PowerShell. Flask usa su servidor de desarrollo, por lo que se limita a la máquina local; no desplegarlo en producción.

## Continuar con el entorno existente

Si ya existen `.venv`, `.env` e `instance/sicose.sqlite3`, conservarlos. Desde la raíz, activar `.\.venv\Scripts\Activate.ps1` y ejecutar `flask --app sicose run --debug`. No reinstalar dependencias, copiar `.env`, inicializar ni ejecutar seed por una revisión documental. Solo aplicar `init-db` si una actualización de esquema lo requiere; nunca resetear datos.

Los pasos 1–4 siguientes son para instalación inicial en un entorno nuevo.

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

El comando crea o amplía `instance\sicose.sqlite3`; preserva los datos, aplica migraciones aditivas y crea las tablas/columnas del modelo actual y tres roles (`ADMINISTRADOR`, `JEFE_PERSONAL` e `INSTRUCTOR_VOLUNTARIO`, esquema versión 9). La v8 añade especialidad principal y la v9 añade residencia/año de incorporación sin rellenar perfiles históricos. Si se continúa desde v8, aplicar esta migración aditiva con el entorno existente, conservando `.env` y la base.

Cuando una actualización funcional requiera migración de esquema, detén el servidor y ejecuta este comando antes de usar los módulos nuevos. Es aditivo e idempotente: añade las tablas faltantes y no reinicia ni borra los datos existentes.

## 4. Crear el administrador DEMO

```powershell
flask --app sicose seed-admin
```

El usuario es `admin.demo`, salvo que configures otro valor. El comando falla si falta la contraseña o no cumple el mínimo, y es idempotente: no cambia una cuenta ya existente. Guarda la contraseña solo como hash.

## 5. Ejecutar la aplicación

```powershell
flask --app sicose run --debug
```

Abrir `http://127.0.0.1:5000/login`. Administración puede registrar y editar perfiles de Jefes de Personal e Instructores Voluntarios, cargar fotos PNG/JPEG (máximo 3 MiB) y restablecer sus contraseñas; comunica la nueva clave al usuario por un canal seguro. El alta de Instructor Voluntario solicita nombres, ambos apellidos, fecha completa de nacimiento y especialidad principal del catálogo acordado; genera el código como iniciales + `DDMMAA`. Los perfiles históricos sin fecha o especialidad muestran el dato pendiente hasta actualizarlo. En su dashboard ve las fotos de los perfiles registrados. Desde **Configuración** puede editar su propio nombre y foto; para cambiar su contraseña debe ingresar la actual y volver a iniciar sesión después. Las fotos se almacenan localmente en `instance\perfiles`. Administración usa **Evaluaciones** para catálogo/asignaciones y **Capacitaciones o cursos** para consultar, registrar o editar cursos. Jefe de Personal usa **Asistencias**, **Capacitaciones o cursos** y **Notas e historial**. En Asistencias selecciona fecha y actividad; cada voluntario activo aparece con Nombre completo, Código, Estado de cuenta horizontal y Asistencia seleccionable; guarda el conjunto con el botón de asistencia y puede filtrar el historial por persona, última gestión o rango de fechas. La etiqueta de período del dashboard presenta el año calendario actual; las filas de períodos se mantienen sin cambios. Instructor Voluntario ve estados de evaluaciones sin notas ni observaciones y usa **Mi perfil** para editar solo correo y foto; los demás datos no son editables por autoservicio. Las operaciones mutables requieren CSRF mediante `X-CSRFToken`. Detener el servidor con `Ctrl+C`.

## 6. Ejecutar pruebas

Con el entorno virtual activo:

```powershell
python -m unittest discover -s tests -v
```

Las pruebas usan el cliente de Flask y bases SQLite temporales aisladas; no requieren iniciar un servidor ni alteran la base local.

## Estructura inicial

```text
sicose/                 fábrica Flask, auth, permisos, dashboards, SQLite y esquema
frontend/               login, registro, gestión por rol, tres paneles, CSS y JS
tests/                  pruebas HTTP de autenticación, autorización y datos
instance/               base local ignorada por Git
docs/07_inicio_desarrollo.md  instrucciones para Windows
```

## Alcance y seguridad

La sesión dura ocho horas; cookies `HttpOnly`, `SameSite=Lax` y `Secure` configurable para HTTPS. Los endpoints JSON distinguen 401 y 403. Login y logout validan CSRF; las demás operaciones mutables desde la interfaz también usan token CSRF. Los paneles y módulos disponibles aplican autorización por rol y ámbito en backend; algunas capacidades futuras permanecen señaladas como pendientes en la interfaz. `/api/admin/estado` es solo una ruta breve de comprobación de autorización. La limitación de intentos de login y el despliegue con servidor WSGI/HTTPS están pendientes.

Las solicitudes guardan hash de contraseña y permanecen pendientes sin sesión. La administración crea manualmente cuentas activas de Instructores Voluntarios desde **Agregar manualmente**; puede consultar solicitudes pendientes y usar **Ver todos los perfiles** para acceder al directorio de consulta, edición y desactivación; el alta activa directa es administrativa. El Jefe usa **Agregar Instructor Voluntario** para enviar una solicitud pendiente asignada a su equipo; el Administrador la aprueba o rechaza. La cuenta pendiente no inicia sesión ni aparece en el directorio activo del Jefe. Las rutas de invitaciones previas se conservan por compatibilidad, pero el dashboard ya no ofrece crear invitaciones. Desactivar conserva historial. El servidor incorporado de Flask es exclusivamente para desarrollo local; antes de un despliegue será necesario definir servidor WSGI, HTTPS, secretos y demás requisitos operativos.

## Residencia e incorporación en gestión

Administrador y Jefe registran opcionalmente residencia en Bolivia, departamento dependiente y año de incorporación desde el alta autorizada o edición. El directorio presenta incorporación y antigüedad calculada (año actual del servidor menos incorporación); sin dato muestra No disponible. La fecha histórica Antigüedad desde se conserva por separado. El Instructor no ve estos campos; Mi perfil sigue limitado a correo/foto.


Perfil v14 (2026-10-10): al continuar con la base existente, ejecutar `flask --app sicose init-db` de forma aditiva tras respaldo si faltan las columnas grado/fecha_incorporacion; en esta entrega la base local ya fue migrada y verificada. Altas administrativas y solicitudes ahora requieren correo, nacionalidad, departamento y foto válida, además de identidad/credenciales. Alta administrativa elige Activo/Inactivo; solicitudes quedan pendientes. Usar una sola Fecha de incorporación; no volver a pedir año y antigüedad desde separados. Los perfiles con solo año histórico conservan ese dato hasta completar la fecha.
