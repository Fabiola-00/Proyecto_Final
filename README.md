# SICOSE

**Sistema de Control y Evaluación de Personal** es un prototipo académico para el seguimiento de personal voluntario de rescate y emergencias. Usa Flask, SQLite y HTML/CSS/JavaScript puro. No es un producto comercial ni clínico.

Paleta institucional vigente (2026-10-16): azules `#0500B2` y `#0054B2`, naranjas `#FA9A4B` y `#FCC495`, complementarios `#226DC6` y `#C67B22`. Interfaz con tonos derivados para modos claro/oscuro; PDF en paleta clara para impresión. Verde/rojo conservan su significado de estado.

## Estado actual — revisión 2026-10-15

**SQLite v27. Espacio de trabajo organizado, Gestión/Evaluaciones separadas, cursos con bajas y retiradas auditadas, físicas v3 sin fechas y formularios aritméticos demostrativos independientes. PDF anual v3 administrativo y reportes en otra pestaña. Psicometría oficial y red neuronal pendientes.** Véase [organización vigente](docs/21_organizacion_espacio_trabajo.md). Véase la actualización v24 al final. El siguiente resumen v23 conserva el alcance histórico aceptado, no sustituye las decisiones nuevas.

Fases 4A/4B y 5A implementadas técnicamente, con aceptación operativa pendiente. **Fase 5B implementada técnicamente y aceptada operativamente por el solicitante el 2026-10-14; SQLite v23.** Están implementados períodos y configuración, habilitación individual por gestión, notas manuales auditadas, cursos con puntaje y estado automático, asignación/finalización personal y PDF operativos. 5B.1 física, 5B.2 acumulación/cálculos y 5B.3 publicación/republicación implementadas; regla nueva y publicación requieren acciones explícitas. 5B.4 cierre/reapertura con instantáneas y reapertura excepcional de históricos sin instantánea implementadas técnicamente; aceptación operativa confirmada; aprobación institucional pendiente. Psicometría e IA no están implementadas.

Administrador/Jefe crean, editan borradores y eliminan lógicamente Gestiones (años), y activan/desactivan evaluaciones por Gestión. Configurar/publicar el ciclo y activar la regla nueva siguen reservados al Administrador. Instructor conserva consulta propia por año. El Jefe único tiene alcance global SBRAB; el Comandante se registra como evaluador externo, sin cuenta operativa. Las entregas anteriores y sus evidencias fechadas se conservan en [HISTORY.md](HISTORY.md).

## Capacidades y permisos

La autorización se comprueba en servidor para páginas, APIs y objetos. Cuentas pendientes/inactivas no acceden a información protegida. Los roles históricos INSTRUCTOR/VOLUNTARIO se migran a JEFE_PERSONAL/INSTRUCTOR_VOLUNTARIO conservando IDs e historial.

| Área | Administrador | Jefe de Personal | Instructor Voluntario |
|---|---|---|---|
| Personal | Lista, crea, consulta, edita y activa/desactiva perfiles; administra cuentas y aprobación/rechazo de solicitudes. | Solicita altas pendientes; consulta personal activo/inactivo global SBRAB, edita activos y activa/desactiva cuentas ya admitidas. | Consulta sus datos permitidos; edita exclusivamente correo y foto propios. |
| Grado y especialidades | Asigna/edita grado y especialidades. | Asigna/edita sobre personal activo SBRAB; puede proponer grado en solicitudes. | Consulta grado y especialidades propios, sin editar. |
| Asistencia | Registra, consulta y corrige en su ámbito global; historial y PDF. | Registra/corrige sobre activos SBRAB; consulta historial y reporta también inactivos. | Calendario anual propio y totales de cuatro estados, sin edición, observaciones ni datos de terceros. |
| Cursos | Crea/edita catálogo común, asigna participantes activos, registra/corrige finalización y genera PDF filtrado. | Crea/edita el mismo catálogo, asigna participantes activos, registra/corrige finalización y genera PDF. | Consulta asignaciones/formación propias y puntos de versiones publicadas visibles; sin motivos/observaciones ajenos. |
| Operaciones | Crea/edita eventos y vincula participantes activos. | Crea/edita eventos y vincula participantes activos globales, también por selección múltiple. | Consulta solo sus participaciones, sin información de terceros ni observaciones. |
| Gestiones y evaluaciones anuales | Crea/edita borradores, retira con historial y activa/desactiva ítems por año; configura/publica el ciclo, activa cálculo v2 y cierra/reabre con instantáneas. | Crea/edita borradores, retira con historial y activa/desactiva ítems por año; sin configurar/publicar el ciclo ni activar regla v2. | Consulta propia, sin administración. |
| Cálculos provisionales | Consulta componentes, conjunto, fuentes y detalle académico de activos/inactivos. | Misma consulta global SBRAB. | Solo físicas/promedio y formación/acumulado publicados; Desempeño/conjunto ocultos. |
| Notas manuales | Registra/corrige notas no psicométricas y consulta historial autorizado. | Registra/corrige sobre activos SBRAB habilitados en gestión activa/configurada; consulta historial. | Consulta estados/avance propios y físicas/acumulado publicados; sin notas vigentes no publicadas ni observaciones. |
| Credenciales y fotos | Gestiona su perfil/clave y restablece claves de personal; fotos privadas. | No restablece claves ajenas. | Autoservicio de correo/foto; no restablece claves ajenas. |

Desde 2026-10-12 Comandante es un evaluador externo registrado por nombre en su nota de Desempeño; Administrador/Jefe transcriben. El rol previo se conserva en históricos, sin acceso operativo.

### Altas, perfil y directorio

- Alta administrativa con estado ACTIVO o INACTIVO. Solicitudes públicas y del Jefe permanecen PENDIENTE hasta aprobación/rechazo administrativo. La asignación histórica a un Jefe se conserva, pero ya no delimita permisos. Desactivar conserva perfil e historial.
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

El reporte matricial usa rango inclusivo de fechas, columnas por fecha/actividad, código/nombre y cuatro totales. Porcentaje operativo = `(Asiste + Atraso)/(Asiste + Atraso + Falta)`, excluyendo Permiso y redondeando a dos decimales; sin denominador, No disponible. No constituye una nota ni promedio oficial. PDF horizontal imprimible, paginado sin perder columnas, con carimbo SBRAB en cada página, nombre institucional completo y fecha/hora de generación de Bolivia. Administrador y Jefe reportan el ámbito global SBRAB; Instructor no accede al reporte administrativo.

### Cursos, operaciones y notas

**Capacitaciones y Cursos** registra catálogo con nombre, tipo, entidad, fechas obligatorias y puntaje entero 0–100; observaciones opcionales. Tipos: Capacitación, Especialización, Actualización, Taller y Seminario (Webinar). Estado automático por fecha de Bolivia: Próximo amarillo, En curso verde (inicio/fin inclusive), Finalizado rojo. Edición y asignación en modales; participantes con estados personales, puntaje/fecha explícitos al finalizar y correcciones con historial. Instructor consulta solo lo propio, sin puntajes hasta publicación. Históricos conservados sin adopción automática; ver [formación v18](docs/11_cursos_formacion.md).

Se conservan registros personales en `capacitaciones`, APIs por ámbito y vínculo opcional `curso_id`; no se enlazan históricos automáticamente ni se reescriben sus nombres al renombrar el catálogo. Mis cursos muestra formación propia sin observaciones. El PDF del catálogo filtra por rango inclusivo de fecha de inicio y tipo/estado opcionales; excluye cursos sin inicio. Incluye carimbo SBRAB, no datos personales ni observaciones; resultado vacío válido.

Operaciones guarda tipo, lugar, inicio/fin e institución y sus participaciones. El texto histórico `experiencia_operaciones` permanece independiente de ese modelo. Sin borrado físico ni interfaz de desvinculación en esta entrega.

Las notas manuales se validan entre 0 y 100. Una corrección agrega una fila enlazada a la nota más reciente y conserva la anterior; registra autor y fecha. El flujo manual rechaza psicometría y cambios en períodos cerrados. La revisión de **Notas e historial** quedó verificada en el cierre técnico 5A: guardado/corrección consecutivos sin perder selección y comprobación/inserción serializadas para evitar ramas ante simultaneidad; formulario bloqueado durante carga/errores o período cerrado.

## Evaluaciones por gestión: implementación y acuerdos pendientes

Administrador/Jefe crean gestiones anuales enero–diciembre y editan nombre/año de borradores sin registros ni configuración publicada, con valores anteriores e historial. Ambos eliminan mediante baja lógica motivada: retiro operativo, sin borrar datos ni cerrar con instantánea. Ambos activan/desactivan los mismos ítems anuales, conservando habilitación individual e historial. Administrador configura las cinco fuentes y publica/activa con configuración congelada y una única gestión operativa activa. Publicar la configuración **no publica las notas al Instructor**.

Administrador/Jefe consultan la tabla de activos e inactivos, habilitación, avance, pendientes y notas; Ver abre un modal compacto y el reporte PDF es un botón. Cambiar el año invalida el reporte previo. Las habilitaciones tienen historial; deshabilitar no borra notas. Inactivos conservan consulta/historial, sin nuevas habilitaciones, notas ni finalizaciones. Administrador/Jefe pueden activar o desactivar cuentas ya admitidas desde los iconos del directorio, con confirmación, auditoría y control de estado anterior. Reactivar exige un nuevo inicio de sesión; no altera contraseña, historial ni habilitaciones existentes. Las solicitudes pendientes/rechazadas siguen fuera de este flujo.

Las fuentes son Física 1, Física 2, Académica, Desempeño del Jefe y Desempeño del Comandante. Las notas manuales 0–100 admiten dos decimales, se almacenan en centésimas y conservan correcciones anteriores. Requieren persona activa, fuente habilitada y gestión activa/configurada. La nota del Comandante guarda por separado su nombre y quién la transcribió. El rol antiguo `COMANDANTE_GRUPO` conserva registros históricos; su acceso operativo está bloqueado. El Jefe activo es único y opera globalmente, sin asignación obligatoria.

Cursos nuevos requieren entidad, inicio/fin y puntaje entero 0–100. Estado calculado con fecha de Bolivia: antes del inicio Próximo; inicio/fin inclusive En curso; después del fin Finalizado. Asignación única curso/persona, con datos del curso capturados y estados personales Asignado, En curso, Finalizado y No completado. Finalizar exige puntaje individual 0–100 y fecha personal explícita; las correcciones requieren motivo y revisión vigente. Cambiar el catálogo no reescribe participaciones. Cursos históricos incompletos conservan sus datos, sin puntos ni fechas inferidos.

Instructor consulta habilitación/estado/avance autorizado y formación propios; ve únicamente físicas/promedio y formación/acumulado de la última versión publicada. Correcciones conservan valor/fecha anteriores hasta republicar; fuentes deshabilitadas y gestiones retiradas ocultan sus notas. Filas/estados de Desempeño no entran en su avance. El flujo académico manual anterior se conserva por compatibilidad; no equivale al acumulado por cursos ni adopta históricos automáticamente.

Secuencia acordada y estado de las entregas:

1. **Implementado 5B.1/v19:** dos fechas físicas comunes, reprogramación extraordinaria individual y No cumplida auditada con cero. Pendiente sin nota distinto; reprogramar conserva el cero hasta cumplimiento/corrección. Administrador/Jefe programan y reprograman. Ver [programación física y compatibilidad](docs/13_programacion_fisica.md).
2. **Implementado 5B.2/v20:** activación explícita ACUMULADO_TRES_V2 por Gestión, sin modificar PROMEDIO_TRES_V1. Académica entera hasta 100, detalle completo/imputación anual única y pendiente sin formación finalizada. Física y Desempeño promedian sus dos fuentes; conjunto de tres componentes iguales, exactitud sin redondeos intermedios y resultado final a dos decimales mitad arriba. Fuente obligatoria desactivada/faltante deja No disponible. [Alcance y compatibilidad](docs/14_calculos_y_gestiones.md).
3. **Implementado 5B.3/v21:** Administrador/Jefe publican/republican físicas y formación/acumulado mediante revisión previa, también parcial. Se conservan versiones/fechas anteriores hasta republicar; se ocultan fuentes deshabilitadas y gestiones retiradas. Desempeño y conjunto no se publican. [Reglas y evidencia](docs/15_publicacion_notas.md).
4. **Implementado 5B.4/v22:** Administrador cierra/reabre con motivo e instantáneas por persona; incompletos identificados y confirmados, cada cierre anterior conservado, configuración intacta y bloqueo de correcciones de formación del año anterior/nuevo cerrado. Administrador/Jefe consultan el historial; no publica notas automáticamente. [Uso, compatibilidad y evidencias](docs/16_cierres_reaperturas.md). Aceptación operativa/institucional pendiente.

La reapertura excepcional de históricos exige motivo y constancia de ausencia de instantánea original; conserva evidencia actual sin reconstruir el cierre antiguo ni adoptar notas/reglas. La [guía de validación integral y aceptación](docs/17_validacion_integral_5b.md) prepara el ensayo humano pendiente.

Ver [reformulación vigente](docs/10_reformulacion_evaluaciones.md) y [formación v18](docs/11_cursos_formacion.md). [Reglas iniciales 5B](docs/09_reglas_fase_5b.md) documenta el alcance anterior; los acuerdos posteriores cambian el rol Comandante y la fuente académica.

La Fase 6 depende de aprobación institucional/profesional, licencia, idioma, puntuación, intentos y retención. Fase 7 tiene PDF operativos acotados de cursos, asistencia y evaluaciones; Excel y reportes psicométricos pendientes. Piloto: respaldo/restauración, HTTPS/WSGI, operación, privacidad/retención y aceptación institucional. IA opcional en Fase 8, fuera del cierre básico. Los acuerdos de puntuación del prototipo no acreditan aprobación institucional.

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

Las pruebas usan bases aisladas; no reinician la base local. Evidencias registradas del 2026-10-12:

| Verificación | Resultado | Alcance |
|---|---|---|
| Última suite completa, entrega v18 | 86 pruebas aprobadas en 87,375 s | Cursos y formación individual; anterior a la corrección de gestiones. |
| Corrección posterior de gestiones | 10 pruebas aprobadas en 7,090 s | Administración exclusiva, edición y consulta por año. |
| Revisión documental del 2026-10-12 | 87 pruebas definidas; SQLite v18, quick_check=ok, cero infracciones FK | Inspección del código y lectura de la base; no se ejecutó una nueva suite funcional. |

Las cifras históricas de 42/43 pruebas y las entregas anteriores permanecen en [HISTORY.md](HISTORY.md). No deben presentarse como verificaciones nuevas. `/api/admin/estado` comprueba acceso administrativo, no salud integral.

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

- [Reglas iniciales 5B](docs/09_reglas_fase_5b.md), [reformulación de evaluaciones](docs/10_reformulacion_evaluaciones.md) y [cursos y formación personal](docs/11_cursos_formacion.md).

## Revisión estructural y del plan — 2026-10-13

La [revisión del proyecto](docs/12_revision_proyecto.md) contrasta documentación, código y pruebas. El [plan actualizado](docs/05_plan_desarrollo.md) conserva fases y organiza lo restante de 5B en física programada, acumulación/cálculos, publicación/republicación y cierre/reapertura. 4A/4B/5A tienen implementación técnica y aceptación operativa pendiente; 5B/7 siguen parciales; psicometría condicionada, piloto pendiente e IA opcional.

Verificación de la revisión documental anterior a 5B.1: **87 pruebas aprobadas en 143,824 s**, compilación Python, sintaxis de los cinco JavaScript y git diff --check correctos. Base local solo en lectura: v18, quick_check=ok y cero infracciones FK. No se repitió ensayo visual ni se migró la base. La evidencia del 2026-10-12 anterior permanece histórica.


## Entrega 5B.1 — 2026-10-13 (v19)

[Programación física](docs/13_programacion_fisica.md) implementada: dos fechas comunes, reprogramación individual y No cumplida auditada con cero conservado hasta cumplimiento/corrección. Administrador/Jefe programan y reprograman; gestiones/configuración siguen exclusivas del Administrador. Interfaz en Notas operativas por fuente; tabla/avance/PDF distinguen No cumplida. Configuraciones y notas anteriores conservadas, con compatibilidad explícita del API manual sin programación; sin cálculos ni publicación al Instructor.

Verificación nueva: **93 pruebas aprobadas en 195,680 s**, con bases aisladas y seis pruebas específicas de físicas; 20 escenarios Chromium con API simulada, 360/1447 px y temas claro/oscuro, sin errores JavaScript ni desbordes. Se inspeccionaron capturas de modales/pantallas; prueba HTTP de PDF con No cumplida/cero, respuesta privada no-store y auditoría correcta. Compilación Python, sintaxis de cinco JavaScript, enlaces locales y git diff --check correctos.

Migración local respaldada v18→v19: **32 tablas previas preservadas**, inicialización repetida dos veces, quick_check=ok, cero infracciones FK y tres tablas nuevas vacías. `.venv`, `.env`, fotos e historial conservados. Evidencias anteriores mantienen su contexto histórico. Pendientes 5B.2 acumulación/cálculos, 5B.3 publicación/republicación y 5B.4 cierre/reapertura; aceptación operativa e institucional pendientes. No se declara cerrada Fase 5B.


## Entrega 5B.2 y revisión de Gestiones — 2026-10-13 (v20)

Separadas Gestión (año), catálogo común, activación anual e habilitación personal. Menú de Administrador/Jefe sin creación de períodos duplicada en catálogo ni otro inciso de notas antiguas; historial anterior accesible por enlace contextual. Notas y resultados muestra cálculo provisional y detalle de fuentes; Instructor conserva proyección sin notas/resultados. [Reglas, APIs y límites](docs/14_calculos_y_gestiones.md).

Evidencia nueva: **104 pruebas aprobadas en 158,822 s**, 36 escenarios Chromium con API simulada (360/1447 px, claro/oscuro), sin errores JavaScript ni desbordes tras revisión visual. Migración respaldada v19→v20, **35 tablas previas preservadas**, dos inicializaciones, quick_check=ok y FK=0; cuatro tablas nuevas vacías, sin reglas ni históricos adoptados automáticamente. Entorno, fotos y cambios locales conservados. Publicación 5B.3 y cierres 5B.4 pendientes; sin aceptación operativa/institucional ni cierre 5B.


## Entrega 5B.3 — 2026-10-13 (v21)

Publicación/republicación parcial por persona/Gestión en Notas y resultados, con motivo, revisión de fuentes e historial. Mis evaluaciones y Mis cursos muestran versiones publicadas propias; correcciones no sustituyen automáticamente los valores/fechas visibles. Deshabilitación personal/anual o baja de Gestión oculta sus notas en servidor. Desempeño no se incluye en publicación ni en filas/denominador del avance del Instructor. [Detalle](docs/15_publicacion_notas.md).

Verificación nueva: **114 pruebas aprobadas en 123,012 s**, 16 escenarios Chromium con API simulada en 360/1447 px y ambos temas, sin errores/desbordes; capturas inspeccionadas. Migración respaldada v20→v21, 39 tablas previas preservadas, dos inicializaciones, quick_check=ok y FK=0; ninguna publicación creada automáticamente. Entorno/fotos/cambios locales conservados. Próxima entrega 5B.4 cierre/reapertura; no se declara cerrada 5B ni aceptación operativa/institucional.

Verificación del complemento 5B — **2026-10-14, v23**: 135 pruebas aprobadas en 301,157 s, ocho escenarios visuales sintéticos, sintaxis Python/cinco JavaScript/enlaces/diff correctos. Migración respaldada, 43 tablas previas preservadas, dos inicializaciones, quick_check=ok y FK=0; evidencia histórica nueva vacía. Ensayo y aceptación humana/institucional todavía pendientes; no se declara cerrada Fase 5B.

Ensayo adicional de 5B del **2026-10-14**: servidor Flask real y base DEMO aislada, sin respuestas API simuladas; 12 comprobaciones funcionales y 12 escenarios visuales de los tres roles correctos en el alcance recorrido. Base de trabajo preservada, servidor DEMO final detenido, sin nueva migración ni cambios del producto. [Informe del ensayo](docs/18_ensayo_servidor_real_5b.md). Aceptación humana/institucional aún pendiente; no equivale al cierre de Fase 5B.


### Espacio del Jefe y reportes — 2026-10-14 (v23)

Navegación del Jefe organizada en Inicio, Personal y Operaciones y Evaluación Anual: Gestión, Evaluaciones, Notas y Resultados, Reportes. Dashboard global con tarjetas y gráficos descriptivos; Gestión separada de activación anual e habilitación individual. Activación/configuración del ciclo y regla de cálculo siguen exclusivas del Administrador (confirmado). Administrador/Jefe ahora crean y editan operaciones y asignan participantes, incluidos lotes por checkbox con validación íntegra; sustituye restricciones antiguas de eventos solo administrativos. Centro de PDF existentes y nuevos reportes de formación personal finalizada y operaciones con participantes, solo Administrador/Jefe, sin contactos/observaciones/motivos privados. [Alcance y verificación](docs/19_espacio_jefe_reportes.md). Sin migración ni adopción de históricos.


Verificación final del 2026-10-14: **138 pruebas aprobadas en 354,019 s**; cuatro dirigidas finales en 10,106 s y una del Inicio administrativo en 0,664 s. Treinta escenarios visuales con Flask real/base DEMO, 360/1447 px y ambos temas, sin errores JavaScript ni desbordes; capturas revisadas. Dos PDF nuevos, caso vacío y paginación de 80 filas/11 páginas renderizados e inspeccionados. Compilación Python, seis JavaScript, 159 enlaces en 22 documentos y git diff --check correctos. Sin migración, nuevas dependencias ni seed de la base de trabajo; v23/quick_check=ok/FK=0 en consulta solo lectura. Entorno, fotos, historial y trabajo local previo conservados. Servidores DEMO detenidos y sus bases temporales retiradas. La aceptación operativa previa de 5B no se extiende automáticamente a esta reorganización; aprobación institucional/piloto conservan sus pendientes.


### Guía autónoma de reconstrucción — 2026-10-15

[DESARROLLO.md](DESARROLLO.md) reúne el alcance vigente, diseño claro/oscuro, permisos, reglas de dominio, arquitectura propuesta para un proyecto limpio, etapas implementadas/pendientes, contratos HTTP y anexos completos del esquema v23 sin datos. Es la base para reconstruir en otro proyecto/chat sin repetir decisiones antiguas. No contiene secretos ni transfiere datos, activos gráficos o aceptación institucional. La evidencia funcional del 2026-10-14 se identifica como histórica; la revisión actual es documental y estructural.


### Modelo anual de cinco entradas — 2026-10-15, v24

Acuerdos posteriores al corte v23: Gestión con fechas propias; Jefe inicia y cierra, reapertura administrativa. Inicio registra ceros oficiales salvo dos psicométricas pendientes. Académica suma cursos y notas de operaciones del intervalo hasta 100; sin operaciones, estado Pendiente y aporte cero. Física y Desempeño conservan sus dos fuentes. Formato CINCO_ENTRADAS_V3 separado de históricos V1/V2, sin adopción ni reseteo al migrar. Modelo SIN_ENTRENAR y sin recomendaciones; no se sustituye por promedio. Instructor sin acceso v3 hasta publicación específica, aún pendiente; PDF v3 también pendiente. [Reglas, APIs, compatibilidad y verificación](docs/20_modelo_anual_cinco_entradas.md). La aceptación previa de 5B no se extiende a esta reformulación.


Verificación del 2026-10-15: suite completa de **149 pruebas aprobadas en 339,579 s**; regresión posterior de doce pruebas en **21,002 s**, incluida consulta histórica de retiradas y cierre del Jefe. Dieciséis escenarios visuales finales con Flask real/base DEMO, 360/1447 px y ambos temas, sin errores JavaScript ni desbordes; capturas revisadas. Python, siete JavaScript, 167 enlaces locales en 24 documentos y git diff --check correctos. DESARROLLO conserva DDL v23 y suplemento v24: ambos ejecutados dos veces en temporal, 49 tablas/13 índices explícitos/50 triggers, quick_check=ok/FK=0. Base de trabajo migrada tras respaldo, dos inicializaciones y 44 tablas anteriores preservadas salvo versión; cinco tablas nuevas vacías, v24/quick_check=ok/FK=0, ninguna Gestión ni cero creado automáticamente. Servidores DEMO detenidos y bases temporales retiradas. Sin dependencias nuevas, seed ni cambio de .env/.venv/fotos; documentación previa preservada. Psicométricas, red neuronal, publicación propia y PDF específicos de v3 pendientes; no se declara aceptación humana/institucional ni cierre global de 5B.


### Verificación final de la reorganización v25 — 2026-10-15

- Suite completa final: **158 pruebas aprobadas en 286,819 s**; nueve específicas de esta entrega aprobadas previamente en **17,368 s**. Se actualizaron las expectativas de navegación anteriores que exigían Notas y Resultados/Gestiones (año); no se restauraron controles retirados para satisfacerlas. Log final `.tmp/organizacion-suite-cierre.log`.
- **48 escenarios visuales** con Flask/Werkzeug real y base DEMO aislada: 36 del recorrido integral, ocho tras el ajuste final de ancho de cursos/eliminación visible solo en Gestión preparada y cuatro de Asistencias con guardado real DEMO y comprobación de padding exclusivo del registro. Chrome, 360/1447 px, temas claro/oscuro, tres roles; cero errores JavaScript y cero desbordes globales. Capturas inspeccionadas. Se comprobó el puntaje de ejemplo 100 calculado por servidor y actualizado en el Jefe sin recargar, retirada por checkbox con historial, navegación, desplegables y PDF actual/operaciones en pestaña sin descarga. Evidencias `.tmp/organizacion-ui/resultado.json` y `ajuste-resultado.json` y `asistencias-resultado.json`.
- PDF v3 real generado/renderizado e inspeccionado; encabezado institucional, tabla y pendientes legibles. El test verifica privacidad, denegación a Instructor e identidad congelada tras cierre aunque cambie el directorio.
- Compilación Python, sintaxis de los ocho JavaScript, **174 enlaces locales en 25 documentos** y git diff --check correctos. DDL de DESARROLLO (v23+v24+v25) ejecutado dos veces en SQLite temporal: **53 tablas/56 triggers**, quick_check=ok/FK=0.
- Relectura de la base de trabajo contra el respaldo pre-v25: **49 tablas previas preservadas**, salvo el identificador de versión; cuatro nuevas tablas vacías, v25/quick_check=ok/FK=0. DEMO detenida y base temporal retirada; sin seed, dependencias nuevas o cambios en .venv/.env/fotos.

La aceptación operativa de 5B del 2026-10-14 sigue siendo histórica y no acredita esta reorganización. Pendientes: instrumentos psicométricos autorizados, publicación numérica propia v3, entrenamiento/validación del modelo, aprobación institucional y piloto. Los formularios aritméticos son ejemplos independientes, no resultados psicométricos ni recomendaciones.


### 2026-10-16 — Dashboard por meses de la gestión activa

Los gráficos de Inicio del Jefe sustituyen la comparación de últimas gestiones por Operaciones, Cursos registrados, Asistencias registradas y Formaciones finalizadas agrupadas por mes de la Gestión ACTIVA no retirada. Se respeta el intervalo inclusivo de inicio/fin, incluidos meses parciales y períodos que cruzan años. Cada mes aparece con su año y conteo cero cuando no hay registros; sin Gestión activa se solicita activarla, sin inventar un intervalo. En móvil el desplazamiento horizontal se limita al gráfico y admite teclado; dos columnas cuando hay espacio. Indicadores y resúmenes restantes conservan su alcance.

Verificación de esta corrección: cuatro pruebas específicas aprobadas en 0,002 s (límites, cuatro series, ceros, bisiesto, cruce anual y ausencia de Gestión), tres de regresión del espacio del Jefe aprobadas en 7,868 s. Cuatro escenarios con Flask real/DEMO aislada y Chrome, 360/1447 px, claro/oscuro: doce meses por gráfico, conteos comprobados, sin errores JavaScript ni desbordes de página; capturas inspeccionadas. Compilación Python y git diff --check correctos. No cambia JavaScript de producto, esquema ni datos de trabajo; SQLite permanece v25. No se repitió la suite completa: la evidencia de 158 pruebas del 2026-10-15 es histórica. Logs/capturas en .tmp/mensual-regresion.log y .tmp/mensual-ui/.


### 2026-10-16 — Días con asistencia registrada por mes

El gráfico de asistencia del Inicio del Jefe cuenta fechas distintas dentro de cada mes de la Gestión activa (COUNT DISTINCT fecha), no filas por persona. Varias personas o actividades registradas el mismo día cuentan como un único día. No se filtra por Asiste: se cuentan días con registro de llamada, independientemente del estado personal. Se conserva el intervalo inclusivo y los meses sin registros. Título: Días con asistencia registrada. Las demás series mantienen sus conteos.

Verificación nueva: cinco pruebas mensuales aprobadas en 0,002 s, incluida deduplicación de fechas con múltiples registros y límites del período; tres pruebas del espacio del Jefe aprobadas en 7,287 s, incluida la etiqueta renderizada. Compilación Python y git diff --check correctos. Sin migración, cambios de datos ni nueva suite completa o ensayo visual. Evidencia en .tmp/dias-asistencia-tests.log y .tmp/dias-asistencia-regresion.log; las verificaciones visuales anteriores siguen siendo históricas.

Actualización 2026-10-16: los modales de calificación usan Observación opcional (también validada como opcional en servidor); el resto de las acciones conserva sus requisitos de motivo. Véase docs/21_organizacion_espacio_trabajo.md.

Evaluaciones: Cursos, operaciones y asistencia muestra las participaciones y el porcentaje de asistencia del Instructor y la Gestión seleccionados; indicador informativo separado de las notas.

Reporte individual administrativo (2026-10-16): en Reportes, seleccionar Instructor y generar PDF de la Gestión activa con perfil/foto, formación finalizada/pendiente, operaciones, calificaciones, asistencia y psicometría/recomendación pendientes. Disponible para Administrador/Jefe. Véase [reporte individual](docs/22_reporte_individual.md).

Actualización 2026-10-16: Operaciones incorpora tipos y estados por catálogo, edición y estado por colores. Eliminar sin vínculos elimina permanentemente; con participantes/notas conserva baja histórica y sus puntajes. SQLite v26, 54 tablas; históricos sin clasificación automática. Véase [operaciones v26](docs/23_operaciones_tipos_estados.md).

Operaciones v27 (2026-10-16): Departamento/Zona, formulario ordenado y tabla compacta con Ver/Editar/Asignar/Retirar/Eliminar. Retirada individual excluye puntos abiertos y conserva historial, bloqueada por cierres/inactivos. 55 tablas, sin ubicaciones históricas inferidas. Véase [ubicación y retiradas](docs/24_operaciones_ubicacion_retiros.md).
