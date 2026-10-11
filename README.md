# SICOSE

**Sistema de Control y Evaluación de Personal** es un prototipo académico para organizar información de personal voluntario de rescate y emergencias. No es un producto comercial, un sistema clínico ni una herramienta para tomar decisiones automáticas sobre personas.

Este README consolida los acuerdos funcionales y técnicos tomados desde el inicio y distingue las capacidades ya implementadas de las que siguen pendientes. Las especificaciones ampliadas están en [`docs/`](docs/).

## Estado actual

El proyecto está en **Fase 5 parcial; 4B implementada técnicamente y pendiente de aceptación operativa**. Están implementados autenticación y dashboards por rol, gestión básica de cuentas y perfiles, fotos privadas, parte del catálogo y asignación de evaluaciones, asistencia, capacitaciones y calificaciones manuales no psicométricas con historial. La Fase 6 no ha comenzado. La versión actual del esquema SQLite es **14**; `flask --app sicose init-db` amplía el esquema de forma aditiva y conserva las filas existentes.

Verificación actual del **2026-10-10**: **64 pruebas aprobadas en 31,611 s** con `python -m unittest discover -s tests -v`, usando el entorno existente y bases aisladas. No se afirma que las capacidades listadas como pendientes estén implementadas.

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
| Cuentas y perfiles | Alcance global; administra Jefes de Personal e Instructores Voluntarios, aprueba/rechaza solicitudes y puede crear cuentas manualmente. | Consulta, edición y desactivación de Instructores Voluntarios activos asignados; el Jefe puede solicitar altas pendientes de aprobación administrativa, asignadas a su equipo. | Consulta estados/avance propios; autoservicio implementado de correo y foto mediante Mi perfil; los demás datos quedan bajo gestión autorizada. |
| Evaluaciones | Administra el catálogo y las asignaciones globales implementadas. | Consulta evaluaciones/resultados autorizados de su equipo; registra notas no psicométricas y activa/desactiva pruebas solo cuando exista instrumento aprobado. | Consulta las evaluaciones propias completadas/pendientes y su estado/avance, sin notas, resultados individuales u observaciones. |
| Asistencia | Tiene acceso administrativo a la pantalla y datos globales. | Registra por fecha y actividad a su equipo activo con estado Asiste, Atraso, Permiso o Falta; consulta por persona, último día registrado o rango de fechas. | Sin funciones de administración de asistencia. |
| Capacitaciones o cursos | Listado, alta y edición de registros basados en `capacitaciones`. | Listado, alta y edición en el ámbito asignado. No hay borrado físico. | Consulta de sus cursos como funcionalidad posterior. |
| Contraseñas y fotos | Puede editar el nombre, foto y contraseña propios; editar perfiles y restablecer contraseña de Jefes de Personal e Instructores Voluntarios. | Foto de perfil visible en su panel; no restablece contraseñas ajenas. | Foto visible en su panel; no restablece contraseñas ajenas. |

El alta de Instructor Voluntario puede originarse como solicitud pública pendiente, solicitud pendiente registrada por su Jefe de Personal o alta manual administrativa. Las solicitudes del Jefe se asignan en servidor a su equipo; solo el Administrador aprueba o rechaza. El dashboard de Administración conserva la bandeja de solicitudes pendientes y los perfiles registrados, ofrece el alta manual en un bloque plegable y enlaza a directorios de consulta, alta, edición y desactivación administrativa de Instructores Voluntarios y Jefes de Personal. Ya no ofrece invitaciones por correo; las rutas heredadas se conservan por compatibilidad. La aprobación administrativa activa la cuenta. La desactivación conserva perfil, calificaciones, asistencia y demás historial.

### Datos de Instructor Voluntario

Los datos acordados incluyen:

- **Generales:** nombres, apellido paterno, apellido materno, fecha completa de nacimiento, país/nacionalidad y departamento dependiente del país.
- **Específicos:** año de incorporación, antigüedad calculada, especialidad principal y secundarias, cursos relacionados y operaciones relacionadas.
- **Código:** inicial de nombres + inicial de apellido paterno + inicial de apellido materno + fecha `DDMMAA`; por ejemplo, `DMC-020478`. El servidor calcula el código. Una colisión se rechaza de forma preventiva; la política definitiva aún no está acordada.
- **Especialidades acordadas:** Rescate en agua, Rescate en montaña, Rescate en selva, Lucha contra incendios, Primeros Auxilios y K-9.
- **Operaciones acordadas:** tipo de evento, lugar, fecha de inicio, fecha de fin e institución responsable.
- **Fotografía:** opción de carga de foto para perfiles de Jefe de Personal e Instructor Voluntario; archivos privados y servidos mediante una ruta autenticada.

Están implementados nombres, ambos apellidos, fecha completa, generación del código, especialidad principal (catálogo acordado) y carga/visualización de fotos. Los perfiles antiguos pueden conservar la especialidad vacía y muestran “Sin especialidad registrada”. En v9 se incorporan país/departamento de residencia (Bolivia y sus nueve departamentos) y año de incorporación; antigüedad = año calendario actual del servidor menos año de incorporación. Son opcionales y permanecen NULL en perfiles históricos, con antigüedad no disponible. Administrador y Jefe autorizado los registran/editan; Jefe solo personal activo asignado. Desde v11 el Instructor consulta residencia/nacionalidad propias; incorporación permanece oculta y no puede editar ninguno de estos campos. En v11 están implementados nacionalidad/residencia ampliada, catálogo relacional de cursos y eventos/participaciones de operaciones; consultar las reglas actuales al final de este documento. Los campos existentes `antiguedad_desde` (fecha) y `experiencia_operaciones` (texto libre) se preservan; la antigüedad nueva se calcula únicamente desde ano_incorporacion y las participaciones relacionales se guardan independientemente en v11. Actualmente `capacitaciones` guarda el nombre del curso como texto, entidad, fecha y observación; en v11 añade curso_id opcional al catálogo común, manteniendo el nombre registrado.

### Evaluaciones, asistencia y capacitación

- El catálogo previsto comprende seis componentes por período: tres psicométricos, evaluación física, rendimiento académico y criterio/desempeño del Jefe de Personal. Los pesos de referencia documentados son una propuesta, no una regla institucional aprobada.
- Administración tiene pantallas iniciales para períodos, catálogo de evaluaciones y asignaciones. La gestión completa de versiones de ponderación y reglas para datos faltantes sigue pendiente.
- Jefe de Personal registra y corrige notas manuales no psicométricas conservando el historial de cambios. Las notas psicométricas no se modifican desde su panel.
- Las asistencias tienen cuatro estados nuevos. El esquema v7 agrega `estado_detalle`; conserva el estado histórico original (`PRESENTE`, `AUSENTE` o `JUSTIFICADO`) y asigna una categoría de presentación al registro antiguo. El esquema v8 añade la especialidad principal de forma aditiva. No se borran filas en las migraciones.
- La etiqueta de año/período en las vistas de dashboard muestra dinámicamente el año calendario actual; no crea ni cambia períodos persistidos, que siguen administrándose mediante su pantalla.
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

## Continuación con entorno existente en Windows

Si ya existen `.venv`, `.env` y la base local, conservarlos. Desde la raíz:

```powershell
.\.venv\Scripts\Activate.ps1
flask --app sicose run --debug
```

Esta entrega documental no requiere `init-db`, seed ni reinstalación. Ejecutar migraciones aditivas solo cuando una actualización de esquema lo requiera.

## Instalación inicial en Windows

Solo para un entorno nuevo; no copiar `.env.example` sobre una configuración existente. Requiere Python 3.10 o posterior. En PowerShell, desde la raíz del repositorio:

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

Las pruebas usan bases aisladas y no reinician la base local. En la revisión documental del 2026-10-10 se verificaron 44 pruebas aprobadas en 18,734 s y enlaces locales; `git diff --check` sin errores de espacios. Las 42/43 pruebas, compilación Python, sintaxis JavaScript e integridad/migraciones locales del 2026-09-29 son evidencias históricas en [HISTORY.md](HISTORY.md), no comprobaciones nuevas de la base local. `/api/admin/estado` comprueba acceso administrativo; no diagnostica salud, disponibilidad ni integridad del sistema.

El [plan reformulado](docs/05_plan_desarrollo.md) separa consolidación documental, 4A (gestión por rol), 4B (perfil y relaciones), 5A (seguimiento operativo), 5B (períodos y cálculos), 6 (psicometría condicionada), 7 (reportes operativos y psicométricos), preparación del piloto y 8 (IA opcional). Cada entrega define dependencias y cierre verificable.

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

## Verificación de la primera entrega 4B — 2026-10-10

54 pruebas aprobadas en 61,107 s, compilación Python, sintaxis JavaScript, enlaces y diff correctos. Migración local v9 aplicada tras respaldo: datos previos conservados en 18 tablas, nuevos campos NULL, quick_check=ok y cero infracciones FK. Seis escenarios de formulario/directorio en Chromium (Administrador/Jefe, tres anchos) pasaron con API simulada y datos sintéticos. Pendiente aceptación operativa del solicitante; Fase 4B aún requiere las ampliaciones restantes.

### Estado vigente — Cierre técnico de Fase 4B (2026-10-10)

Esquema v11. Nacionalidad (país) y residencia diferenciadas, con 20 países latinoamericanos iniciales; Bolivia con nueve departamentos, los demás con provincia/departamento en texto libre. Administrador/Jefe autorizado editan; Instructor consulta sus propios datos geográficos. Incorporación sigue limitada a gestión. Secundarias consultables por ámbito, editables por Administrador/Jefe; la principal puede repetirse como secundaria.

Catálogo común de cursos creado/editado solo por Administrador; capacitaciones vinculadas opcionalmente por Administrador/Jefe al personal de su ámbito activo. Instructor consulta su formación sin observaciones. Históricos sin enlace automático; renombrar catálogo no cambia nombres previamente registrados. Administrador crea/edita eventos de operaciones; Administrador/Jefe vinculan personal activo de su ámbito; Instructor consulta solo sus participaciones. Se conserva el texto histórico de experiencia; no se implementa borrado/desvinculación.

58 pruebas aprobadas en 62,893 s. Migración local v11 con respaldo, 19 tablas anteriores preservadas, inicialización repetida, curso_id previo NULL, quick_check=ok y cero infracciones FK. Cierre técnico implementado; aceptación operativa pendiente. Siguiente entrega: Fase 5A, ensayo de asistencia, capacitaciones y notas manuales por rol, con correcciones e historial. Privacidad/retención y autorización institucional siguen pendientes antes del piloto.

Verificación visual final 4B (2026-10-10): 18 escenarios en Chromium, tres roles y anchos 360/1447 px con datos sintéticos/API simulada; sin desborde ni errores JavaScript. Conservación de provincia al abrir modal y curso_id al editar comprobadas. El desborde inicial del control de foto móvil se corrigió limitando controles al ancho disponible. Enlaces documentales, compilación Python, sintaxis JavaScript y git diff --check correctos.

### Corrección vigente — Registro de cursos (2026-10-10, v12)

La pantalla “Capacitaciones y Cursos” registra cursos independientes de personas. Incluye nombre, tipo (Capacitación, Especialización, Actualización, Taller, Seminario (Webinar)), entidad organizadora, inicio/fin, estado (Próximo, En curso, Finalizado) y observaciones opcionales. Nombre, tipo y estado obligatorios para registros nuevos; fechas/entidad opcionales; fin requiere inicio y no puede precederlo. Estado se elige manualmente, sin deducirlo de fechas. Administrador registra/edita; Jefe consulta el catálogo según permisos ya acordados. Edición mediante modal responsivo con datos precargados y errores en el modal.

Se retiraron de esta pantalla el selector de Instructor y el formulario de asignación. Los registros personales históricos, sus vínculos y APIs se conservan; no hay interfaz nueva de asignación en esta entrega. “Mis cursos” sigue consultando historial personal sin observaciones. Las observaciones del catálogo son distintas del historial personal y solo se muestran a Administrador/Jefe.

Migración v12 aditiva: campos nuevos nullable en cursos, sin inferir tipo, estado ni fechas de históricos. Respaldo SQLite previo, datos de 23 tablas anteriores preservados, inicialización repetida, quick_check=ok y FK=0. 59 pruebas aprobadas en 42,354 s (ejecución final); cuatro escenarios Chromium con API simulada, Administrador/Jefe a 360/1447px, opciones exactas y edición modal correctas. Compilación Python, sintaxis JavaScript y diff comprobados.

### Actualización vigente — Cursos por Jefe y PDF operativo (2026-10-10)

El solicitante autorizó también al Jefe de Personal a crear/editar el catálogo común; esta decisión sustituye la exclusividad administrativa anterior. Administrador y Jefe ven formulario Registro de curso, edición modal y menú/título “Capacitaciones y Cursos”. La asignación de personas continúa fuera de esta pantalla; historial personal conservado.

Reporte GET `/api/cursos/reporte.pdf`, autorizado para Administrador/Jefe; Instructor excluido. Rango obligatorio e inclusivo por fecha de inicio, tipo/estado opcionales combinados; fechas/filtros inválidos rechazados. Cursos sin inicio excluidos; resultado vacío produce PDF explícito. Incluye nombre, tipo, entidad, fechas, estado y total, sin datos personales ni observaciones. Carimbo en cada página con logo SBRAB, nombre institucional completo, fecha/hora de Bolivia y numeración; respuesta privada no-store y auditoría mínima de generación.

ReportLab incorporado a requirements y al entorno existente; no se recreó .venv, .env ni base. Este reporte inicia una entrega operativa acotada de Fase 7; no implementa reportes personales/psicométricos, Excel ni promedios oficiales. Privacidad/retención y aprobación del piloto siguen pendientes.

Verificación final (2026-10-10): 60 pruebas aprobadas en 28,375 s; PDF sintético multipágina renderizado e inspeccionado, carimbo y tabla sin solapamientos. La primera ejecución falló en dos expectativas del antiguo título; corregidas y suite completa repetida. Compilación Python, sintaxis JavaScript y diff correctos.

Interfaz de Jefe verificada en Chromium a 360/1447 px con API simulada: formulario visible, edición modal y acción de generación PDF sin desborde. El endpoint entrega PDF real validado en pruebas HTTP.

### Entrega vigente — Asistencia, correcciones, calendario y reporte (2026-10-10, v13)

- Administrador consulta/registra/corrige asistencia; Jefe solo personal activo asignado. La llamada muestra nombre del responsable autenticado, gestión anual de la fecha seleccionada y fecha; conserva actividad obligatoria. Los cuatro estados exactos son Asiste, Atraso, Permiso y Falta. Llamada nueva inicia todas las filas en Falta; al elegir fecha/actividad existente se cargan sus estados guardados para corregirlos.
- Clave única persona/fecha/actividad: guardar otra vez actualiza el mismo registro. Corrección conserva estado anterior/nuevo, actor y fecha UTC en historial_asistencias mediante trigger; cambios se auditan. Repetir el mismo estado no crea corrección ni sustituye al último responsable. No se permiten cambiar identidad/fecha/actividad mediante el PATCH de corrección. Históricos no se borran ni se fabrican correcciones anteriores.
- Instructor consulta solo su calendario anual y totales de los cuatro estados, sin datos de terceros ni observaciones ni edición. El día puede tener varias llamadas; totales cuentan registros, no días calendario. Sin registro no se considera Falta.
- Reporte matricial por rango inclusivo de fechas, sin materia ni filtros adicionales. Columnas por fecha/actividad, código y nombre, cuatro totales y porcentaje. Asiste y Atraso cuentan como asistencia; Permiso excluido: (Asiste + Atraso)/(Asiste + Atraso + Falta), redondeado a dos decimales; sin denominador, No disponible. Es un indicador operativo aprobado para esta entrega, no una nota ni promedio oficial de Fase 5B. Jefe exporta solo ámbito activo asignado; Administrador todo su alcance; Instructor no exporta reporte administrativo.
- PDF imprimible horizontal: matriz dividida en bloques de hasta ocho llamadas, filas paginadas y cabeceras repetidas, sin perder columnas. Carimbo SBRAB en cada página con escudo, nombre completo institucional y generación en hora de Bolivia; paginación, rango, leyenda y fórmula visibles. Sin observaciones; descarga privada no-store y auditoría mínima.
- Migración local v13 tras respaldo: 23 tablas anteriores preservadas, inicialización repetida, quick_check=ok y cero infracciones FK. Entorno, secretos y base existente conservados. Aceptación operativa del solicitante pendiente; Fase 5A aún requiere revisar integralmente cursos/notas y sus casos de corrección. Retención/privacidad y autorización institucional siguen pendientes antes del piloto.

Verificación final de asistencia (2026-10-10): 62 pruebas aprobadas en 69,702 s con bases aisladas; seis escenarios Chromium a 360/1447 px por los tres roles con API simulada. PDF sintético de seis páginas inspeccionado, cabeceras/carimbo y paginación correctos; encabezado del reporte adaptado para mantener legibilidad. Compilación Python, sintaxis JavaScript, enlaces locales y git diff --check correctos.


### Perfil y directorio vigentes — Grado e incorporación (2026-10-10, v14)

- Directorio con Nombre completo, Código, Grado, Especialidad Principal, Estado, Antigüedad y Acciones. Estado horizontal: ACTIVO verde, INACTIVO rojo, con texto identificable. Ver consulta en modal los datos permitidos y foto; Editar perfil usa modal y Desactivar conserva baja lógica. Restablecer contraseña sigue siendo exclusivo del Administrador, dentro de Editar perfil; nunca se muestra la contraseña guardada ni su hash.
- Grados permitidos: Instructor Inicial, Instructor Segundo, Instructor Primero, Instructor Principal e Instructor Mayor. Administrador los asigna/edita; Jefe solo en personal activo asignado y puede proponerlo al solicitar el alta de su equipo. Instructor consulta el suyo sin editar. La solicitud pública no permite enviar grado; queda NULL hasta revisión del personal autorizado. No se asigna un grado por defecto a históricos ni se infiere por antigüedad.
- Una sola Fecha de incorporación en alta y edición. Al registrarla se sincronizan fecha_incorporacion, antiguedad_desde y ano_incorporacion. Antigüedad = año calendario actual del servidor menos año de incorporación, sin descontar meses/días. Fechas inválidas/futuras y año/fecha contradictorios rechazados. Históricos mantienen año y fecha anterior, incluso si difieren, hasta completar explícitamente la nueva fecha; no se fabrican fechas desde un año. Borrar una fecha canónica existente borra también sus dos valores derivados; un formulario sin fecha histórica completa conserva el año previo.
- Alta administrativa permite ACTIVO o INACTIVO. Solicitudes de Jefe/públicas permanecen PENDIENTE, sin selector que habilite acceso, hasta aprobación administrativa. Las cuentas inactivas/pendientes no acceden a información protegida.
- Alta y solicitudes incluyen nombres, ambos apellidos, nacimiento, código generado en servidor, especialidad principal, usuario, correo, contraseña, nacionalidad, departamento y foto PNG/JPEG (máximo 3 MiB). Correo, nacionalidad, departamento y foto ahora son obligatorios también en servidor. Fecha de incorporación y grado son opcionales; las solicitudes públicas no incluyen grado. Residencia Bolivia oculta en las pantallas nuevas, nacionalidad independiente y catálogo latinoamericano existente. Países históricos se conservan en consulta/edición; no hay reclasificación automática a Bolivia en migración. Botón Guardar. Invitaciones usan el mismo formulario y validaciones.
- Migración v14 aditiva: grado y fecha_incorporacion nullable, sin rellenar perfiles anteriores. Respaldo local previo; 24 tablas anteriores preservadas, inicialización repetida, quick_check=ok y cero infracciones de claves foráneas. No se recrearon .venv, .env ni base local.

Verificación actual (2026-10-10): 64 pruebas aprobadas en 31,611 s, con bases aisladas. Ocho escenarios Chromium con datos sintéticos/API simulada (Administración, Jefe, Instructor y solicitud pública; 360/1447 px), modales precargados, campos/opciones/roles y ausencia de desborde comprobados. Compilación Python, sintaxis JavaScript y git diff --check correctos. La primera ejecución detectó dos expectativas antiguas de etiquetas (Guardar y retiro de Especialidad en tabla de asistencia); actualizadas y suite completa repetida. No se afirma cierre de Fase 5A ni aceptación institucional del piloto.
