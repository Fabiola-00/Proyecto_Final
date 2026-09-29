# Historial de cambios y configuraciones — SICOSE

Este archivo registra cambios funcionales y configuraciones relevantes del proyecto. Se actualiza al cerrar cada cambio grande. Los estados se basan en el código y la documentación disponibles; una entrada no implica que el cambio esté en un commit o en producción.

## 2026-09-29 — Revisión de consistencia de base y formularios

- La base local `instance/sicose.sqlite3` se inspeccionó en modo de solo lectura: `PRAGMA quick_check` devolvió `ok` y `PRAGMA foreign_key_check` encontró cero infracciones.
- Se detectó que esa base local aún informa esquema v5 y no contiene las columnas de identidad v6. No se ejecutó la migración en la base local durante la auditoría. La migración v5→v6 sí se comprueba en las pruebas aisladas; para sincronizar la base de desarrollo se requiere ejecutar `flask --app sicose init-db` desde el entorno local.
- Se corrigió el orden de actualización de versión: el esquema se marca v6 solo después de completar las migraciones en `init-db`.
- Se alineó la vista previa de iniciales con la regla exacta del backend; se añadió validación de formulario de solicitud y campos obligatorios para corregir perfiles históricos incompletos.
- Se limpian las fotos guardadas cuando una solicitud no se confirma por colisión o invitación inválida. Se añadió una prueba de regresión para que la colisión no deje archivos sin referencia.
- Verificación posterior: 39 pruebas — OK; compilación Python, `node --check` y `git diff --check` — OK.
- Hallazgos funcionales aún pendientes según los requisitos del perfil: catálogos de nacionalidades/departamentos, año de incorporación y cálculo de antigüedad, especialidad principal/secundarias, catálogo relacional de cursos y tabla/relación de operaciones. `capacitaciones` sigue guardando el curso como texto y no existe tabla de operaciones.

## 2026-09-29 — Identidad del Instructor Voluntario (en curso, sin commit)

- Se incorporaron nombres, apellido paterno, apellido materno y fecha completa de nacimiento a los flujos de solicitud pública, alta administrativa y edición del perfil.
- El servidor genera el código con la primera letra de cada uno de los tres campos de nombre/apellido y la fecha `DDMMAA` (por ejemplo, `DMC-020478`). Los formularios muestran una vista previa; el valor persistido lo calcula el backend.
- El directorio CRUD expone código y fecha de nacimiento a Administración y al Jefe de Personal dentro de su ámbito. Los perfiles históricos no reciben una fecha ni un código inventados; sus campos nuevos quedan nulos hasta que se actualicen.
- La migración aditiva eleva SQLite al esquema v6 y agrega columnas a `voluntarios`, con índice único parcial para códigos presentes. Una colisión se rechaza con error para revisión; esta política es provisional.
- Documentación actualizada en `docs/01_especificacion_funcional.md`, `docs/03_modelo_datos.md` y `docs/07_inicio_desarrollo.md`.
- Pendiente de definición antes de completar los demás datos solicitados: nacionalidad frente a país de residencia y departamentos, campos/administración del catálogo de cursos, relación y administración de operaciones, y política definitiva para colisiones de código. Año de incorporación/antigüedad calculada y especialidades principal/secundarias también están pendientes de implementación.
- Verificación ejecutada: `python -m unittest discover -s tests` — 39 pruebas, OK; `python -m compileall -q sicose tests` — OK; `node --check frontend\static\js\app.js` — OK; `git diff --check` — OK. Los cambios de este turno no se han confirmado en Git.

## 2026-09-29 — Directorios administrativos y alta plegable (cambios de trabajo previos)

- Administración de Instructores Voluntarios: el alta manual se presenta en una sección plegable con control `+`; se conserva la revisión de solicitudes pendientes y se incorporó un directorio tabular con acciones CRUD.
- Administración de Jefes de Personal: mismo patrón de alta plegable y directorio tabular CRUD, incluyendo perfil, correo, especialidad, cantidad de Instructores Voluntarios activos, estado y acciones.
- El dashboard administrativo tiene enlaces directos para agregar cuentas y abrir cada directorio.
- Se conservaron las rutas legadas de invitaciones por compatibilidad; la interfaz administrativa ya no crea invitaciones.
- Las operaciones de baja siguen siendo lógicas y preservan perfiles e historial.

## Historial de desarrollo por fases

Las fases iniciales se registran por orden; el repositorio no contiene fechas verificables para cada entrega anterior.

### Fase 1 — Base ejecutable

- Estructura inicial Python/Flask y frontend HTML, CSS y JavaScript nativo.
- Configuración local, SQLite, ruta mínima de comprobación y pruebas iniciales.
- Instrucciones de instalación y ejecución para Windows/PowerShell en `docs/07_inicio_desarrollo.md`.

### Fase 2 — Persistencia y autenticación

- Fábrica de aplicación Flask, acceso a SQLite, esquema aditivo, roles, autenticación, control de permisos, sesiones y auditoría.
- Seed idempotente del Administrador mediante configuración local; las contraseñas se guardan como hash.
- Protección CSRF en operaciones con sesión y respuestas JSON de error.

### Fase 3 — Dashboards

- Plantilla compartida y dashboards protegidos distintos para Administrador, Jefe de Personal e Instructor Voluntario.
- Navegación según rol, indicadores obtenidos de la base y diseño adaptable.
- Se incorporó el emblema institucional SBRAB, menú lateral plegable y alternancia de modo claro/oscuro.
- Colores institucionales vigentes: azul `#1D1BBE` y naranja `#F57B1A`.

### Fase 4 — Solicitudes y gestión de personal

- Registro público de Instructores Voluntarios con estado pendiente, revisión administrativa, aprobación/rechazo y asignación a un Jefe de Personal.
- Gestión de perfiles con autorización por rol y ámbito; desactivación lógica para conservar historial.
- Se añadió alta administrativa manual de Instructores Voluntarios; las solicitudes pendientes permanecen disponibles.
- Se añadió gestión de cuentas de Jefe de Personal por Administración.

### Fase 4.3 — Fotos y recuperación administrativa

- Carga y edición de fotos de perfil PNG/JPEG, guardadas fuera de `static` en `instance/perfiles` y servidas mediante una ruta autenticada.
- Administración puede editar perfiles y restablecer contraseñas de Jefes de Personal e Instructores Voluntarios. El restablecimiento usa hash e invalida sesiones previas.

### Cambio de roles — Esquema v5

- Roles actuales: `ADMINISTRADOR`, `JEFE_PERSONAL` e `INSTRUCTOR_VOLUNTARIO`.
- La migración de códigos anteriores `INSTRUCTOR` y `VOLUNTARIO` conserva IDs y relaciones históricas.
- Se actualizaron categorías y orígenes de evaluación asociados a los roles nuevos.

### Fase 5 — Evaluaciones, asistencias y calificaciones (parcial)

- Administración dispone de catálogo/períodos y asignaciones; Jefe de Personal registra asistencias, capacitaciones y calificaciones no psicométricas con historial.
- Los perfiles de Instructor Voluntario pueden consultar estados y avance, sin calificaciones ni observaciones.
- No hay pruebas psicométricas habilitadas ni reactivos cargados. La selección, licencia, versión lingüística, puntuación y revisión profesional/institucional siguen pendientes, conforme a `docs/06_pruebas_psicometricas.md`.

## Configuración de desarrollo vigente

- **Stack:** Python 3.10+, Flask, Flask-Login, Flask-WTF, SQLite, HTML5, CSS3 y JavaScript nativo. Dependencias Python declaradas en `requirements.txt`.
- **Inicio en Windows:** crear/activar `.venv`, instalar `requirements.txt`, completar `.env`, ejecutar `flask --app sicose init-db`, `flask --app sicose seed-admin` y `flask --app sicose run --debug`. La guía está en `docs/07_inicio_desarrollo.md`.
- **Variables de entorno documentadas:** `SICOSE_SECRET_KEY`, `SICOSE_DATABASE`, `SICOSE_SESSION_COOKIE_SECURE`, `SICOSE_ADMIN_USERNAME` y `SICOSE_ADMIN_PASSWORD`. `.env.example` contiene valores en blanco o valores DEMO; nunca guardar aquí secretos reales.
- **Base local por defecto:** `instance/sicose.sqlite3`. `init-db` es aditivo e idempotente; habilita claves foráneas y no borra tablas ni historial.
- **Sesión:** cookie `sicose_session`, `HttpOnly`, `SameSite=Lax`, `Secure` configurable y duración de ocho horas. La aplicación requiere `SICOSE_SECRET_KEY`.
- **Datos y archivos locales:** `.env`, `instance/`, entornos virtuales y temporales se excluyen en `.gitignore`. Las fotos se guardan en `instance/perfiles`. No usar datos personales reales para demostración.
- **Pruebas:** `python -m unittest discover -s tests -v`; las pruebas utilizan bases aisladas en memoria o temporales.
- **Límite de uso:** servidor incorporado de Flask para desarrollo local solamente; despliegue institucional, HTTPS, retención formal, respaldos y monitoreo requieren definición adicional.

## Decisiones abiertas

- Completar el modelo demográfico/organizacional del Instructor Voluntario: país/nacionalidad, departamentos dependientes, año de incorporación y cálculo de antigüedad, catálogo de especialidades principal/secundarias, cursos y operaciones.
- Confirmar la política final para códigos repetidos; el comportamiento actual de rechazo es preventivo y provisional.
- Completar el CRUD/autoservicio del perfil del Instructor Voluntario conforme a `docs/01_especificacion_funcional.md`.
- Fase 6, reportes e integración de IA no iniciados; no presentar puntuaciones psicométricas o predicciones no autorizadas como funcionalidad existente.
