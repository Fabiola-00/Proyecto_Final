# SICOSE

**Sistema de Control y Evaluación de Personal** es un prototipo académico para el seguimiento de personal voluntario de rescate y emergencias. Usa Flask, SQLite y HTML/CSS/JavaScript puro. No es un producto comercial ni clínico.

## Estado actual — 2026-10-11

El proyecto tiene **Fase 5A cerrada técnicamente, con aceptación operativa pendiente**, con Fases 4A/4B implementadas técnicamente y aceptación operativa pendiente. El esquema vigente es **SQLite v18**. La actualización del 2026-10-12 al final detalla las reglas nuevas y sus límites. Existen perfiles y gestión por rol, asistencia con correcciones, calendario propio, registro de cursos, operaciones relacionadas y notas manuales con historial. Hay PDF operativos de cursos y asistencia. Psicometría aplicada, promedios oficiales, Excel e IA siguen pendientes.

Verificación histórica de la segunda entrega 5B (2026-10-11): **77 pruebas aprobadas en 86,620 s**, ocho escenarios de interfaz y esquema local v16 verificado tras respaldo. Evidencia histórica de la primera entrega: 73 pruebas en 80,440 s y migración v15. Cierre técnico 5A previo: 68 pruebas en 48,333 s, registrado en [HISTORY.md](HISTORY.md). 5B sigue parcial: rol/fuentes/respaldo y configuración/publicación/activación implementados; cálculo y cierres/reaperturas pendientes.

## Capacidades y permisos

La autorización se comprueba en servidor para páginas, APIs y objetos. Cuentas pendientes/inactivas no acceden a información protegida. Los roles históricos INSTRUCTOR/VOLUNTARIO se migran a JEFE_PERSONAL/INSTRUCTOR_VOLUNTARIO conservando IDs e historial.

| Área | Administrador | Jefe de Personal | Instructor Voluntario |
|---|---|---|---|
| Personal | Lista, crea, consulta, edita y desactiva perfiles; administra Jefes, asignaciones y aprobación/rechazo de solicitudes. | Solicita altas pendientes para su equipo; consulta, edita y desactiva únicamente personal activo asignado. | Consulta sus datos permitidos; edita exclusivamente correo y foto propios. |
| Grado y especialidades | Asigna/edita grado y especialidades. | Lo hace dentro de su ámbito activo asignado; puede proponer grado en su solicitud de alta. | Consulta grado y especialidades propios, sin editar. |
| Asistencia | Registra, consulta y corrige en su ámbito global; historial y PDF. | Registra, consulta, corrige y reporta solo personal activo asignado. | Calendario anual propio y totales de cuatro estados, sin edición, observaciones ni datos de terceros. |
| Cursos | Crea/edita catálogo común; consulta y genera PDF filtrado. | Crea/edita el mismo catálogo y genera PDF. | Consulta asignaciones y formación histórica propias, sin puntajes ni observaciones hasta publicación. |
| Operaciones | Crea/edita eventos y vincula participantes activos. | Vincula únicamente personal activo asignado a eventos existentes. | Consulta solo sus participaciones, sin información de terceros ni observaciones. |
| Notas manuales | Registra/corrige notas no psicométricas y consulta historial autorizado. | Mismas operaciones dentro del ámbito asignado. | Consulta estado/avance de evaluaciones; no recibe notas ni observaciones. |
| Credenciales y fotos | Gestiona su perfil/clave y restablece claves de personal; fotos privadas. | No restablece claves ajenas. | Autoservicio de correo/foto; no restablece claves ajenas. |

Desde 2026-10-12 Comandante es un evaluador externo registrado por nombre en su nota de Desempeño; Administrador/Jefe transcriben. El rol previo se conserva en históricos, sin acceso operativo.

### Altas, perfil y directorio

- Alta administrativa con estado ACTIVO o INACTIVO. Solicitudes públicas y del Jefe permanecen PENDIENTE hasta aprobación/rechazo administrativo; el Jefe no elige otro equipo. Desactivar conserva perfil e historial.
- Altas requieren nombres, ambos apellidos, nacimiento, especialidad principal, usuario, correo, contraseña de 12–256 caracteres, nacionalidad, departamento y foto PNG/JPEG de hasta 3 MiB. Código generado por servidor: inicial de nombres y de cada apellido + `DDMMAA`, por ejemplo `DMC-020478`. Colisiones rechazadas preventivamente; política definitiva pendiente.
- Grados: Instructor Inicial, Instructor Segundo, Instructor Primero, Instructor Principal e Instructor Mayor. Grado opcional; la solicitud pública no puede enviarlo. No se infiere por antigüedad ni se asigna por defecto a históricos.
- Especialidades: Rescate en agua, Rescate en montaña, Rescate en selva, Lucha contra incendios, Primeros Auxilios y K-9. Secundarias múltiples sin duplicados; la principal puede repetirse como secundaria. El pendiente de especialidad principal quedó resuelto en v8.
- Una sola **Fecha de incorporación**, opcional. Al guardarla se sincronizan `fecha_incorporacion`, `ano_incorporacion` y `antiguedad_desde`. Antigüedad = año calendario actual del servidor menos año de incorporación; no calcula años completos por aniversario. Se rechazan fechas futuras y valores contradictorios.
- Históricos con solo año/fecha antigua se conservan hasta completar explícitamente la fecha canónica, sin fabricar fechas ni recalcular datos guardados. Borrar una fecha canónica existente borra sus valores derivados. Incorporación sigue limitada a gestión autorizada.
- Nacionalidad usa el catálogo existente de 20 países latinoamericanos y es independiente de residencia. Las altas muestran departamento de Bolivia (nueve opciones) y envían residencia Bolivia sin selector visible. País/provincia históricos de otras residencias se conservan en consulta/edición.
- Directorio: Nombre completo, Código, Grado, Especialidad Principal, Estado, Antigüedad y Acciones. Estado horizontal, ACTIVO verde/INACTIVO rojo. Filas alineadas y compactas; iconos de Ver, Editar perfil y Desactivar en una fila con `aria-label` y título. Ver/Editar abren modales; restablecer contraseña está dentro de Editar y es exclusivo del Administrador.

### Asistencia y PDF

Responsable, Gestión, Actividad y Fecha comparten una fila en escritorio, dos columnas en tablet y una en móvil. Actividades nuevas: Ordinaria, Actividad Externa, Terreno y Operación; textos históricos conservados. La tabla de llamada muestra Nombre completo, Código, Estado y Asistencia.

Los estados son **Asiste, Atraso, Permiso y Falta**. Llamadas nuevas comienzan en Falta; seleccionar una fecha/actividad existente carga sus estados. La clave persona/fecha/actividad evita duplicados. Correcciones conservan estado anterior/nuevo, actor y fecha UTC; repetir el estado no genera corrección. Sin registro no equivale a Falta. El calendario propio cuenta registros, que pueden ser varios por día.

El reporte matricial usa rango inclusivo de fechas, columnas por fecha/actividad, código/nombre y cuatro totales. Porcentaje operativo = `(Asiste + Atraso)/(Asiste + Atraso + Falta)`, excluyendo Permiso y redondeando a dos decimales; sin denominador, No disponible. No constituye una nota ni promedio oficial. PDF horizontal imprimible, paginado sin perder columnas, con carimbo SBRAB en cada página, nombre institucional completo y fecha/hora de generación de Bolivia. Jefe reporta solo su ámbito; Instructor no accede al reporte administrativo.

### Cursos, operaciones y notas

**Capacitaciones y Cursos** registra catálogo con nombre, tipo, entidad, fechas obligatorias y puntaje entero 0–100; observaciones opcionales. Tipos: Capacitación, Especialización, Actualización, Taller y Seminario (Webinar). Estado automático por fecha de Bolivia: Próximo amarillo, En curso verde (inicio/fin inclusive), Finalizado rojo. Edición y asignación en modales; participantes con estados personales, puntaje/fecha explícitos al finalizar y correcciones con historial. Instructor consulta solo lo propio, sin puntajes hasta publicación. Históricos conservados sin adopción automática; ver [formación v18](docs/11_cursos_formacion.md).

Se conservan registros personales en `capacitaciones`, APIs por ámbito y vínculo opcional `curso_id`; no se enlazan históricos automáticamente ni se reescriben sus nombres al renombrar el catálogo. Mis cursos muestra formación propia sin observaciones. El PDF del catálogo filtra por rango inclusivo de fecha de inicio y tipo/estado opcionales; excluye cursos sin inicio. Incluye carimbo SBRAB, no datos personales ni observaciones; resultado vacío válido.

Operaciones guarda tipo, lugar, inicio/fin e institución y sus participaciones. El texto histórico `experiencia_operaciones` permanece independiente de ese modelo. Sin borrado físico ni interfaz de desvinculación en esta entrega.

Las notas manuales se validan entre 0 y 100. Una corrección agrega una fila enlazada a la nota más reciente y conserva la anterior; registra autor y fecha. El flujo manual rechaza psicometría y cambios en períodos cerrados. La revisión de **Notas e historial** quedó verificada en el cierre técnico 5A: guardado/corrección consecutivos sin perder selección y comprobación/inserción serializadas para evitar ramas ante simultaneidad; formulario bloqueado durante carga/errores o período cerrado.

## Próxima entrega y decisiones abiertas

1. **Aceptación operativa de 5A:** el solicitante revisa el recorrido visible de notas, cursos, asistencia, calendario y PDF con datos sintéticos; registrar aceptación o incidencias. El cierre técnico ya está verificado.
2. **Continuación de Fase 5B:** tabla/habilitación por gestión y cursos/formación individual implementados. Siguen acumulado académico, programación/reprogramación física, publicación y cierres, conforme a [reglas actualizadas](docs/10_reformulacion_evaluaciones.md).

La Fase 6 depende de aprobación institucional/profesional, licencia, idioma, puntuación, intentos y retención. Fase 7 ya tiene PDF operativos acotados; Excel, informes consolidados y reportes psicométricos siguen pendientes. Preparación del piloto requiere respaldo/restauración, HTTPS/WSGI, operación, privacidad y aceptación institucional. Fase 8 (IA) es opcional y queda fuera del cierre básico. No se asumen respuestas institucionales, porcentajes ni fechas de entrega.

## Reglas técnicas y de seguridad

- Consultas parametrizadas, claves foráneas y migraciones aditivas; no resetear base ni borrar historial.
- Hash moderno; secretos solo en entorno/`.env` ignorado. Cookies HttpOnly/SameSite y Secure en HTTPS; CSRF en operaciones mutables.
- Errores JSON sin trazas sensibles; auditoría mínima, sin credenciales ni respuestas psicométricas completas. Fotos autenticadas y PDF privados con `no-store`.
- Demostraciones con datos sintéticos. `instance/`, `.env`, `.venv` y temporales fuera de Git.
- Azul `#1D1BBE`, naranja `#F57B1A`, emblema SBRAB, diseño responsivo, barra plegable y temas claro/oscuro. Evaluar.com es solo referencia general.

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

## Pruebas y evidencia

Con el entorno existente activo:

```powershell
python -m unittest discover -s tests -v
python -m compileall -q sicose tests
node --check frontend/static/js/app.js
git diff --check
```

Las pruebas usan bases aisladas; no reinician la base local. Suite final del cierre 5A (2026-10-11): 68 pruebas aprobadas en 48,333 s; compilación Python, sintaxis JavaScript, enlaces locales y diff correctos. La evidencia anterior permanece en [HISTORY.md](HISTORY.md). `/api/admin/estado` comprueba acceso administrativo, no salud integral.

## Estructura y documentación

| Ruta | Contenido |
|---|---|
| `sicose/` | Flask, permisos, lógica, reportes y esquema SQLite. |
| `frontend/` | Plantillas, CSS, JavaScript e imágenes. |
| `tests/` | Pruebas HTTP, permisos, migraciones y datos sintéticos. |
| `instance/` | SQLite y fotos privadas locales, fuera de Git. |

- [AGENTS.md](AGENTS.md): instrucciones y punto de continuidad vigente.
- [HISTORY.md](HISTORY.md): cambios, acuerdos y evidencias fechadas; conserva las cifras históricas de 42/43 pruebas.
- [Especificación funcional](docs/01_especificacion_funcional.md), [arquitectura](docs/02_arquitectura_tecnica.md), [modelo de datos](docs/03_modelo_datos.md) y [diseño](docs/04_diseno_visual.md).
- [Plan de desarrollo](docs/05_plan_desarrollo.md): numeración, dependencias y cierre por entrega; sus puntos de control posteriores sustituyen descripciones anteriores. La continuidad actual se resume arriba.
- [Psicometría](docs/06_pruebas_psicometricas.md): requisitos previos y límites.
- [Inicio de desarrollo](docs/07_inicio_desarrollo.md): instalación, ejecución y solución de problemas.

- [Cierre técnico de Fase 5A](docs/08_cierre_fase_5a.md): matriz de casos, correcciones, evidencias y aceptación operativa pendiente.


Reglas 5B acordadas el 2026-10-11, con primera entrega implementada y resto pendiente: tres componentes de igual importancia; Física promedia dos evaluaciones obligatorias; Académica es nota global manual con motivo/referencias a formación propia (sin formación, pendiente); Desempeño promedia aportaciones obligatorias independientes de Jefe y Comandante. Resultado = (Física + Académica + Desempeño)/3, faltantes no calculables, cero válido, entradas hasta dos decimales y redondeo final mitad hacia arriba sin redondeos intermedios. Períodos anuales con uno activo; configuración congelada. Administrador gestiona/publica/cierra/reabre con motivo; Jefe opera en activo y Admin corrige con historial. Único SBRAB y cargo Comandante con rol propio implementado: consulta seguimiento/notas/resultados sin observaciones ajenas, edita solo su aportación y no administra cuentas/períodos/configuración. Cierre permite incompletos identificados, guarda instantáneas y reapertura conserva cada cierre sin cambiar configuración. Código con cuatro roles y esquema v16; rol/fuentes/respaldo y borradores/configuración/publicación/activación implementados; cálculo y cierres/reaperturas pendientes. Ver [reglas de Fase 5B](docs/09_reglas_fase_5b.md).


## Primera entrega implementada de Fase 5B — 2026-10-11 (v15)

- Rol COMANDANTE_GRUPO con panel propio y cargo único SBRAB. Administrador crea/edita/desactiva cuentas y restablece contraseña; una sola cuenta Comandante ACTIVO, garantizada también por triggers SQLite. No se reutiliza una cuenta para otra persona ni se elimina autoría; nombre editable e historial con nombres capturados. No se creó una cuenta automáticamente.
- Seguimiento 5B para Administrador/Jefe/Comandante: selección de persona activa/período, perfil básico, formación, asistencia y notas sin asignar históricos a nuevas fuentes. Jefe solo personal activo asignado. Comandante consulta seguimiento de personal activo SBRAB y registra/corrige solo su aportación; sin administración ni observaciones/motivos/referencias privadas ajenas. Instructor sin acceso numérico 5B.
- Cinco fuentes independientes: FISICA_1, FISICA_2, ACADEMICA, DESEMPENO_JEFE y DESEMPENO_COMANDANTE. Notas nuevas 0–100 con hasta dos decimales, almacenadas en centésimas enteras; solo período ACTIVO. Física: Admin/Jefe autorizado. Académica inicial: Jefe; requiere motivo y formación personal referenciada. Desempeño inicial de cada evaluador: Jefe/Comandante correspondiente. Administración puede corregir aportaciones existentes conservando responsable y autor de corrección.
- Cadena por persona/período/fuente: primera nota única, corrección solo de la vigente, inserción serializada y anteriores conservadas. No admitir autor/responsable arbitrarios en JSON. Jefe/Comandante no corrigen Desempeño de otro titular; si cambió responsable, la corrección histórica requiere Administración. Motivo y referencias se conservan como instantánea de respaldo académico; editar el curso después no altera ese respaldo.
- Migración v15: ampliar CHECK de roles preservando IDs/referencias y añadir notas_operativas/respaldo_academico; triggers de Comandante único se crean después de ampliar roles. Inicialización local repetida tras respaldo, 24 tablas anteriores preservadas (roles anteriores incluidos), quick_check=ok y cero infracciones FK. Tablas nuevas vacías, sin cuentas ni notas inferidas. .venv/.env/base existente conservados.
- Verificación: **73 pruebas aprobadas en 80,440 s**, ocho escenarios Chromium (Administración/Jefe/Comandante/gestión de cuenta, 360/1447 px), sin desborde ni errores; modales y envíos, fuentes/roles y período cerrado comprobados. Compilación Python, sintaxis de ambos JavaScript y git diff --check correctos. Pruebas de migración incluyeron esquemas antiguos; se corrigió orden de creación de triggers y fixture de catálogo de roles.

### Límites de esta entrega

Límite histórico al terminar v15: publicación/configuración, vinculación de fuentes y activo único todavía estaban pendientes; quedan implementados en v16 según la actualización siguiente. Cálculo conjunto y cierre/reapertura con instantáneas de resultados continúan pendientes. No se declara cerrada 5B. Las APIs/notas históricas y pantalla de asignaciones anterior se mantienen por compatibilidad; no se convierten ni participan automáticamente en el futuro cálculo 5B. Instructor conserva su avance existente, sin nuevo resultado 5B. La aceptación operativa del solicitante y requisitos institucionales mantienen sus pendientes.

Siguiente entrega concreta: cálculo provisional exacto con faltantes y redondeo; después cierre/reapertura con instantáneas. Los permisos y períodos se validan en servidor, sin modificar históricos silenciosamente.


## Segunda entrega de Fase 5B — 2026-10-11 (v16)

Administrador dispone de **Períodos y configuración**: crea borradores anuales enero–diciembre, configura cinco fuentes mediante modal y publica/activa en una transacción. La revisión del borrador evita sobrescribir cambios concurrentes. Publicación exige fuentes completas con evaluaciones manuales activas de categoría compatible; dos fuentes de la misma categoría pueden usar la misma evaluación de catálogo, manteniendo sus notas independientes. Configuración versión 1 con regla PROMEDIO_TRES_V1 (igual importancia de los tres componentes); no habilita porcentajes arbitrarios ni cálculo aún.

La publicación congela fuentes, nombres/códigos/categorías, autor y fecha UTC. Cambiar el catálogo después no reescribe esas referencias. Un solo período puede activarse bajo concurrencia, también protegido por triggers. No se cierran otros períodos automáticamente. Notas/correcciones 5B requieren período ACTIVO y configuración PUBLICADA; configuración_id/evaluacion_id se resuelven en servidor, sin aceptar esos valores del cliente. La API de calificación anterior no registra notas en períodos configurados 5B; los registros anteriores siguen consultables.

Migración v16 aditiva: configuraciones_5b y fuentes_configuracion_5b, dos referencias nullable en notas_operativas y restricciones. Respaldo local previo, 26 tablas anteriores preservadas, inicialización repetida, quick_check=ok y cero infracciones FK. Períodos y notas históricas sin modificación ni adopción; referencias anteriores NULL. La base local no tenía períodos ACTIVO; una base histórica que sí los tenga bloqueará nuevas activaciones hasta un tratamiento explícito en la entrega de cierre, sin alterar sus estados al migrar.

Verificación actual: **77 pruebas aprobadas en 86,620 s** (bases aisladas), incluyendo publicación concurrente, revisiones obsoletas, fuentes incompletas/categoría inválida, congelación, permisos/CSRF y preservación v15. Ocho escenarios Chromium con API simulada a 360/1447 px: publicación y modal administrativo, notas por los tres roles y bloqueo de edición sin configuración publicada; sin desborde ni errores JavaScript. Compilación Python, sintaxis de los tres JavaScript, enlaces locales y git diff --check correctos.

Pendientes: cálculo provisional exacto/faltantes/redondeo, cierre y reapertura motivada con cada instantánea preservada, aceptación operativa e institucional/privacidad antes del piloto. **No se declara cerrada Fase 5B.** Siguiente entrega: cálculo provisional vinculado a configuración y últimas notas válidas, separado de asistencia y psicometría.


## Reglas nuevas acordadas — 2026-10-12

La [reformulación de evaluaciones y formación](docs/10_reformulacion_evaluaciones.md) sustituye acuerdos anteriores incompatibles: Comandante sin cuenta operativa propia, Jefe único sin asignaciones necesarias, publicación de notas físicas/académicas al Instructor, No cumplida física con cero y formación acumulativa en enteros. Primera entrega de autorización/tabla/habilitación/PDF implementada en v17; el resto queda pendiente según la actualización siguiente. Configuraciones/históricos anteriores se conservan; no aplicar las reglas nuevas retrospectivamente. Límite/imputación académica, alcance global del Jefe y publicación/republicación quedaron confirmados; ver la actualización siguiente. La próxima entrega se reordena conforme a ese documento; las verificaciones del 2026-10-11 permanecen históricas.


## Primera entrega de la reformulación — 2026-10-12 (v17)

Jefe único activo con alcance global sin filtro de asignación; Comandante retirado del acceso operativo, conservado solo en datos históricos. Desempeño del Comandante transcrito por Administrador/Jefe con nombre del evaluador y autor de transcripción separados. Tabla Evaluaciones por gestión y consulta modal de activos/inactivos, habilitación individual con historial y notas 5B bloqueadas al deshabilitar; PDF administrativo con carimbo SBRAB. Instructor consulta habilitación/estado/avance por gestión, todavía sin notas publicadas.

Acuerdos complementarios: Académica acumulará puntos enteros con tope 100; puntos individuales ajustables, gestión de finalización personal y cómputo único. Administrador/Jefe publicarán; después de corrección se conservará la versión publicada anterior hasta republicar. **Cursos con puntos, programación/reprogramación física, No cumplida=0, acumulación y publicación/republicación aún pendientes.** El flujo manual académico anterior y configuraciones congeladas no se convierten automáticamente. Psicometría continúa bloqueada; Fase 5B no cerrada.

Evidencia vigente: 81 pruebas aprobadas en 45,711 s; ocho escenarios UI, PDF sintético de cinco páginas, compilación/sintaxis/enlaces/diff correctos. Migración v17 tras respaldo, 28 tablas anteriores preservadas, inicialización repetida, quick_check=ok, FK=0. Detalles en [reglas y estado](docs/10_reformulacion_evaluaciones.md). Siguiente entrega: cursos con puntaje y asignación/finalización individual con historial.


## Cursos y formación personal implementados — 2026-10-12 (v18)

Administrador/Jefe registran/editar catálogo con puntaje entero 0–100, fechas/entidad obligatorias en cursos nuevos y estado automático de Bolivia. Asignación personal/múltiple sin duplicados, finalización independiente con puntaje y fecha explícitos, correcciones con actor/fecha/motivo/revisión y valores anteriores preservados. Edición del catálogo no reescribe datos capturados al asignar. Inactivos solo consulta/historial. Instructor ve sus estados y formación histórica, sin puntajes hasta publicación; Dashboard/seguimiento enlazan las participaciones. PDF de catálogo filtra estado calculado. Histórico sin datos completos permanece intacto y sin puntos inferidos.

Verificación vigente: 86 pruebas aprobadas en 87,375 s; 12 escenarios UI, sin desborde/errores; migración local tras respaldo e inicialización repetida preservando 29 tablas, quick_check=ok y FK=0. Compilación, sintaxis, enlaces y diff correctos. Detalles en [reglas y entrega v18](docs/11_cursos_formacion.md). Pendientes acumulado académico hasta 100, físicas/reprogramación/No cumplida, publicación/republicación y cierres; no se declara cierre 5B ni del piloto.


Administración de **Gestiones de evaluaciones** exclusiva del Administrador: crea y edita nombre/año de borradores sin registros, configura y publica. Jefe/Instructor mantienen el selector de año para consultar; sin acciones de administración. Gestiones publicadas/históricas protegidas y acceso validado en servidor. Corrección del 2026-10-12 registrada en HISTORY.
