# SICOSE

**Sistema de Control y Evaluación de Personal** es un prototipo académico para organizar información de personal voluntario de rescate y emergencias. No es un producto comercial, un sistema clínico ni una herramienta para tomar decisiones automáticas sobre personas.

Este README consolida los acuerdos funcionales y técnicos tomados desde el inicio y distingue las capacidades ya implementadas de las que siguen pendientes. Las especificaciones ampliadas están en [`docs/`](docs/).

## Estado actual

El proyecto está en **Fase 5 parcial**. Están implementados autenticación y dashboards por rol, gestión básica de cuentas y perfiles, fotos privadas, parte del catálogo y asignación de evaluaciones, asistencia, capacitaciones y calificaciones manuales no psicométricas con historial. La Fase 6 no ha comenzado. La versión actual del esquema SQLite es **7**; `flask --app sicose init-db` amplía el esquema de forma aditiva y conserva las filas existentes.

Las pruebas automatizadas verificadas en el último cambio funcional: **42 pruebas aprobadas** con `python -m unittest discover -s tests -v`. No se afirma que las capacidades listadas como pendientes estén implementadas.

## Requerimientos acordados

### Roles y acceso

Los roles vigentes son:

| Código | Nombre en la interfaz | Alcance acordado |
|---|---|---|
| `ADMINISTRADOR` | Administrador | Administración global de cuentas y evaluaciones. |
| `JEFE_PERSONAL` | Jefe de Personal | Gestión de Instructores Voluntarios dentro de su ámbito asignado. |
| `INSTRUCTOR_VOLUNTARIO` | Instructor Voluntario | Acceso a su propio perfil y al estado/avance de sus evaluaciones. |

Después de autenticarse, cada rol debe llegar a un dashboard distinto. La autorización se valida en el backend para páginas, APIs y objetos; ocultar acciones en la interfaz no es un control de seguridad. Cuentas pendientes o inactivas no acceden a información protegida. Las bases antiguas con los roles `INSTRUCTOR` y `VOLUNTARIO` se migran conservando IDs e historial.

### Capacidades por rol y estado

| Área | Administrador | Jefe de Personal | Instructor Voluntario |
|---|---|---|---|
| Cuentas y perfiles | Alcance global; administra Jefes de Personal e Instructores Voluntarios, aprueba/rechaza solicitudes y puede crear cuentas manualmente. | CRUD de Instructores Voluntarios activos asignados; las bajas son lógicas. | El autoservicio para editar sus datos personales está acordado, pero aún no está completo. |
| Evaluaciones | Administra el catálogo y las asignaciones globales implementadas. | Consulta evaluaciones/resultados autorizados de su equipo; registra notas no psicométricas y activa/desactiva pruebas solo cuando exista instrumento aprobado. | Consulta las evaluaciones propias completadas/pendientes y su estado/avance, sin notas, resultados individuales u observaciones. |
| Asistencia | Tiene acceso administrativo a la pantalla y datos globales. | Registra por fecha y actividad a su equipo activo con estado Asiste, Atraso, Permiso o Falta; consulta por persona, último día registrado o rango de fechas. | Sin funciones de administración de asistencia. |
| Capacitaciones o cursos | Listado, alta y edición de registros basados en `capacitaciones`. | Listado, alta y edición en el ámbito asignado. No hay borrado físico. | Consulta de sus cursos como funcionalidad posterior. |
| Contraseñas y fotos | Puede editar el nombre, foto y contraseña propios; editar perfiles y restablecer contraseña de Jefes de Personal e Instructores Voluntarios. | Foto de perfil visible en su panel; no restablece contraseñas ajenas. | Foto visible en su panel; no restablece contraseñas ajenas. |

El alta de Instructor Voluntario puede originarse como solicitud pública pendiente o como alta manual administrativa. El dashboard de Administración conserva la bandeja de solicitudes pendientes y los perfiles registrados, ofrece el alta manual en un bloque plegable y enlaza a directorios CRUD de Instructores Voluntarios y Jefes de Personal. Ya no ofrece invitaciones por correo; las rutas heredadas se conservan por compatibilidad. La aprobación administrativa activa la cuenta. La desactivación conserva perfil, calificaciones, asistencia y demás historial.

### Datos de Instructor Voluntario

Los datos acordados incluyen:

- **Generales:** nombres, apellido paterno, apellido materno, fecha completa de nacimiento, país/nacionalidad y departamento dependiente del país.
- **Específicos:** año de incorporación, antigüedad calculada, especialidad principal y secundarias, cursos relacionados y operaciones relacionadas.
- **Código:** inicial de nombres + inicial de apellido paterno + inicial de apellido materno + fecha `DDMMAA`; por ejemplo, `DMC-020478`. El servidor calcula el código. Una colisión se rechaza de forma preventiva; la política definitiva aún no está acordada.
- **Especialidades acordadas:** Rescate en agua, Rescate en montaña, Rescate en selva, Lucha contra incendios, Primeros Auxilios y K-9.
- **Operaciones acordadas:** tipo de evento, lugar, fecha de inicio, fecha de fin e institución responsable.
- **Fotografía:** opción de carga de foto para perfiles de Jefe de Personal e Instructor Voluntario; archivos privados y servidos mediante una ruta autenticada.

Están implementados nombres, ambos apellidos, fecha completa, generación del código y carga/visualización de fotos. Permanecen pendientes los catálogos de país/departamento y especialidades, año de incorporación con cálculo de antigüedad, catálogo relacional de cursos y modelo/relaciones de operaciones. Actualmente `capacitaciones` guarda el nombre del curso como texto, entidad, fecha y observación; no representa todavía un catálogo de cursos.

### Evaluaciones, asistencia y capacitación

- El catálogo previsto comprende seis componentes por período: tres psicométricos, evaluación física, rendimiento académico y criterio/desempeño del Jefe de Personal. Los pesos de referencia documentados son una propuesta, no una regla institucional aprobada.
- Administración tiene pantallas iniciales para períodos, catálogo de evaluaciones y asignaciones. La gestión completa de versiones de ponderación y reglas para datos faltantes sigue pendiente.
- Jefe de Personal registra y corrige notas manuales no psicométricas conservando el historial de cambios. Las notas psicométricas no se modifican desde su panel.
- Las asistencias tienen cuatro estados nuevos. El esquema v7 agrega `estado_detalle`; conserva el estado histórico original (`PRESENTE`, `AUSENTE` o `JUSTIFICADO`) y asigna una categoría de presentación al registro antiguo. No se borran filas en la migración.
- Capacitaciones permite listar, registrar y editar entradas existentes en `capacitaciones`, con autorización por ámbito. La baja física no está disponible para preservar el historial.
- No hay reactivos ni formularios psicométricos activos. No se debe habilitar una prueba sin comprobar instrumento, versión lingüística, derechos/licencia, regla de puntuación y aprobación profesional e institucional.
- PDF, Excel, informes consolidados, cálculos oficiales de promedios e integración de IA están pendientes. No se deben inventar predicciones ni presentar reglas provisionales como un modelo entrenado o una medida validada.

### Diseño e identidad institucional

- Interfaz en español, adaptable a móvil/escritorio, minimalista, profesional y con controles accesibles.
- Colores institucionales: azul `#1D1BBE` y naranja `#F57B1A`.
- Emblema SBRAB en la barra lateral y en el acceso al sistema.
- Dashboards con barra lateral plegable y modo claro/oscuro. Los paneles muestran la foto del usuario cuando está disponible.
- Evaluar.com solo se consideró referencia general de organización; no se copian marca, textos ni composición propietaria.

## Reglas técnicas y de seguridad

- Frontend: HTML5, CSS3 y JavaScript nativo. Backend: Python y Flask con API REST JSON. Persistencia: SQLite.
- Consultas SQL parametrizadas y claves foráneas activadas. Cambios de esquema aditivos; no reiniciar la base para actualizar. Los cambios sensibles requieren validación de permisos en servidor.
- Contraseñas guardadas como hash moderno; secreto de Flask solo desde entorno o `.env` local ignorado por Git. No se devuelven hashes, contraseñas, claves, tokens ni respuestas psicométricas a la interfaz.
- Sesiones con cookie `HttpOnly`, `SameSite=Lax`, `Secure` configurable para HTTPS y duración de ocho horas. Operaciones mutables desde la interfaz validan CSRF.
- Errores de APIs con códigos HTTP/JSON claros, sin trazas ni datos sensibles. Auditoría con metadatos mínimos; nunca guarda credenciales o respuestas psicométricas completas.
- No usar información personal real en demostraciones. `instance/`, `.env`, entornos virtuales y archivos temporales no se versionan.
- El servidor integrado de Flask es solo para desarrollo local; antes de cualquier despliegue real se necesitan revisión de seguridad, HTTPS, WSGI, respaldo, retención, privacidad y operación institucional.

## Inicio rápido en Windows

Requiere Python 3.10 o posterior. En PowerShell, desde la raíz del repositorio:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

En `.env`, configura `SICOSE_SECRET_KEY` con un secreto aleatorio y `SICOSE_ADMIN_PASSWORD` con una contraseña local robusta de al menos 12 caracteres. Puedes generar el secreto así:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Luego inicializa la base, crea el administrador DEMO y arranca Flask:

```powershell
flask --app sicose init-db
flask --app sicose seed-admin
flask --app sicose run --debug
```

Abre `http://127.0.0.1:5000/login`. El usuario de seed predeterminado es `admin.demo`; el comando no imprime ni reemplaza la contraseña existente. Para detener el servidor, pulsa `Ctrl+C`. Para los detalles y solución de problemas, consulta [`docs/07_inicio_desarrollo.md`](docs/07_inicio_desarrollo.md).

## Pruebas

Con el entorno virtual activo:

```powershell
python -m unittest discover -s tests -v
```

Las pruebas usan bases aisladas y no reinician la base local. En el último cambio funcional se ejecutaron 42 pruebas y todas aprobaron. También se verificaron `python -m compileall -q sicose tests`, `node --check frontend\static\js\app.js`, `git diff --check` y la integridad de la base local tras su migración a v7 (`quick_check=ok`, cero infracciones de claves foráneas).

## Estructura del proyecto

```text
sicose/       Aplicación Flask, blueprints, permisos, lógica y esquema SQLite
frontend/     Plantillas HTML, estilos CSS, JavaScript e imágenes estáticas
tests/        Pruebas HTTP, permisos, migraciones y flujos de datos
docs/         Requerimientos, arquitectura, datos, diseño, plan y guía de desarrollo
instance/     Base SQLite y fotos privadas locales; excluido de Git
HISTORY.md    Historial de cambios relevantes y verificaciones
```

## Documentos del proyecto

- [`AGENTS.md`](AGENTS.md): convenciones, seguridad y reglas de desarrollo.
- [`docs/01_especificacion_funcional.md`](docs/01_especificacion_funcional.md): permisos, perfiles y requerimientos funcionales aprobados.
- [`docs/02_arquitectura_tecnica.md`](docs/02_arquitectura_tecnica.md): módulos, APIs, arquitectura y seguridad.
- [`docs/03_modelo_datos.md`](docs/03_modelo_datos.md): tablas, relaciones y migraciones.
- [`docs/04_diseno_visual.md`](docs/04_diseno_visual.md): identidad y patrones de interfaz.
- [`docs/05_plan_desarrollo.md`](docs/05_plan_desarrollo.md): fases, estado, dependencias y decisiones pendientes.
- [`docs/06_pruebas_psicometricas.md`](docs/06_pruebas_psicometricas.md): revisión documental y límites para instrumentos.
- [`docs/07_inicio_desarrollo.md`](docs/07_inicio_desarrollo.md): instalación y ejecución en Windows.
- [`HISTORY.md`](HISTORY.md): cronología de decisiones, cambios de esquema y verificaciones.
