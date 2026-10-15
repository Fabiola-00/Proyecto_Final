# 02. Arquitectura técnica

## Esquema implementado

Aplicación Flask monolítica modular: frontend HTML/CSS/JavaScript nativo en `frontend/` → endpoints JSON del blueprint `sicose.auth` → servicios/persistencia `sicose.db` → SQLite en `instance/sicose.sqlite3`. La fábrica `sicose.create_app` permite configuración aislada en pruebas. El directorio `instance/` no se publica como estático y está excluido de Git. Mismo origen web/API.

## Módulos presentes

- `sicose.auth`: login, logout y consulta del usuario autenticado mediante Flask-Login.
- `sicose.permissions`: decorador backend `role_required`.
- `sicose.db`: SQLite, esquema aditivo, seed de roles/administrador y auditoría de auth.
- `sicose.models`: objeto de sesión con proyección pública sin hash.
- `sicose.dashboard`: tres rutas HTML protegidas, cada una por rol; `/` redirige según `ADMINISTRADOR`, `JEFE_PERSONAL` o `INSTRUCTOR_VOLUNTARIO`. Se mantienen rutas antiguas como alias de compatibilidad. Las consultas filtran asignaciones según Jefe de Personal/Instructor Voluntario autenticado. Las vistas son iniciales; las funciones futuras deben respetar la matriz de permisos de `docs/01_especificacion_funcional.md`.
- `sicose.management`: solicitudes públicas pendientes, aprobación/rechazo administrativo, alta manual de Instructores Voluntarios activos por administración, asignación a Jefes de Personal activos, edición/desactivación lógica de perfiles con el ámbito comprobado en servidor, y gestión de cuentas de Jefe de Personal exclusiva del administrador. Los directorios ofrecen consulta, edición y desactivación; los formularios de alta son exclusivos de Administración. Jefe de Personal registra solicitudes pendientes asignadas a su equipo; solo Administración aprueba/rechaza. El Instructor tiene Mi perfil para actualizar exclusivamente correo y foto propios; el backend rechaza otros campos. Al desactivar un Jefe de Personal, los Instructores Voluntarios activos quedan sin asignación y se conservan perfiles/historial. El esquema y las rutas heredadas de invitación se conservan para compatibilidad, pero el panel ya no genera invitaciones.
- `sicose.evaluations`: listado/alta/edición del catálogo y listado/alta de períodos para administración, asignaciones de evaluación a Instructores Voluntarios/períodos activos, habilitación psicométrica por ámbito con verificación de aprobación, asistencia con cuatro estados y filtros por persona/fecha, capacitaciones listables/creables/editables dentro del ámbito, notas manuales no psicométricas con correcciones append-only e historial, resultados de intentos visibles solo para roles autorizados, y estados de evaluación sin notas/observaciones en la vista del voluntario.
- `frontend/`: login, plantilla común de dashboards, vistas iniciales por rol, CSS responsivo y JS nativo para navegación móvil/sesión.
- Psicometría: tablas/rutas preparatorias, sin aplicación de instrumentos; el inicio de intento devuelve formulario no disponible. Reportes e IA: sin funcionalidad implementada. La gestión completa de versiones de ponderación y promedios oficiales sigue pendiente.

Separar rutas, servicios, persistencia y validadores. Las reglas de autorización residen en servidor y se aplican antes de consultar/devolver el recurso. API responde errores JSON con código HTTP apropiado sin filtrar trazas o información sensible.

## Seguridad implementada y pendientes

- Werkzeug genera/verifica hash adaptativo de contraseña; nunca se persiste texto plano.
- `SICOSE_SECRET_KEY` es obligatoria y solo se carga del entorno/`.env` local ignorado. La aplicación falla con mensaje claro si falta.
- Cookie `sicose_session` `HttpOnly`, `SameSite=Lax`, `Secure` configurable (`SICOSE_SESSION_COOKIE_SECURE`), sesión permanente de ocho horas.
- Flask-WTF valida CSRF en POST de login y logout; frontend envía `X-CSRFToken`.
- Entradas del login limitadas y consultas parametrizadas. Fallos de autenticación usan respuesta genérica para no revelar si existe la cuenta.
- Flask-Login identifica la sesión. `role_required` valida rol en servidor; API devuelve 401 sin sesión y 403 con rol insuficiente.
- `/api/auth/me` solo serializa id, username, nombre, rol y estado.
- Auditoría registra seed, login exitoso/fallido y logout con id (si conocido), resultado, fecha UTC e IP; nunca guarda contraseña, hash ni username fallido.
- Seed desde variables locales; idempotente y no actualiza contraseñas existentes.
- Pendientes: rate limiting, política formal de retención, recuperación autónoma de cuenta (el restablecimiento administrativo ya existe), monitoreo y hardening de despliegue.
- Base de datos con permisos de sistema operativo, copias de respaldo y retención definidos antes de uso real. Demo con datos ficticios.
- HTTPS, política de privacidad, consentimiento/aviso de uso y respuesta a incidentes son requisitos para despliegue real, fuera del prototipo local.

## API y rutas presentes

`GET /login`; `POST /api/auth/login`; `POST /api/auth/logout`; `GET /api/auth/me`; `GET /panel/administrador`; `GET /panel/jefe-personal`; `GET /panel/instructor-voluntario` (aliases heredados: `/panel/instructor`, `/panel/voluntario`); `GET /mi-perfil` y `PATCH /api/instructor-voluntario/perfil` (Instructor: solo correo/foto propios); `GET /registro`; `POST /api/jefe-personal/instructores-voluntarios` (solicitud pendiente, asignación en servidor al Jefe autenticado); gestión de registro/usuarios de Fase 4; `GET/POST /api/admin/periodos`; `GET/POST/PATCH /api/admin/evaluaciones`; `POST /api/admin/asignaciones`; `GET /api/jefe-personal/asignaciones`; `PATCH /api/jefe-personal/asignaciones/<id>/estado`; `POST/GET /api/jefe-personal/asistencias` (último día o rango, filtro opcional por persona); `GET /api/jefe-personal/capacitaciones`; `PATCH /api/jefe-personal/capacitaciones/<id>`; `POST /api/jefe-personal/instructores-voluntarios/<id>/capacitaciones`; `POST/GET /api/jefe-personal/asignaciones/<id>/calificaciones`; `GET /api/jefe-personal/asignaciones/<id>/resultados`; `GET /api/instructor-voluntario/evaluaciones` (las rutas `/api/instructor/*` y `/api/voluntario/*` siguen como aliases heredados); `GET /gestion/evaluaciones` (admin), `GET /gestion/asistencias`, `GET /gestion/capacitaciones` y `GET /gestion/calificaciones` (admin/Jefe de Personal). `GET /api/admin/estado` devuelve `{"estado":"autorizado"}` tras validar rol administrativo; no es un diagnóstico de salud ni de integridad. La raíz `/` redirige al panel del rol autenticado. El inicio de intentos psicométricos responde no disponible mientras no se aprueben instrumento, formulario y retención.

## Dependencias y ejecución

Flask, Flask-Login, Flask-WTF, python-dotenv y `sqlite3` estándar. Flask-Login evita una implementación casera del ciclo de sesión; Flask-WTF aporta CSRF; dotenv integra configuración local con Flask CLI. No se introduce ORM ni framework frontend. SQLite se inicializa con `flask --app sicose init-db`: esquema SQL idempotente y versión técnica en `app_meta`, conservando tablas/datos previos. `flask --app sicose seed-admin` crea el usuario de demo.

## Límites

SQLite es adecuado para el prototipo local; multiinstancia/alta concurrencia requiere revisar persistencia. El servidor Flask integrado es solo desarrollo: un despliegue requerirá WSGI, HTTPS, cookies Secure, secretos y revisión de seguridad. No es un sistema clínico ni una plataforma diagnóstica. La IA futura debe ser invocable por Jefe de Personal, auditable, revisable por profesional y nunca decisión automática.

## Perfil v9

`sicose.perfil_residencia` valida el catálogo de residencia y el año de incorporación y calcula antigüedad sin persistirla. Gestión administrativa y solicitudes por Jefe reutilizan esas reglas; la API de listado devuelve campos v9 solo a Administrador/Jefe, dentro del ámbito. No se amplía la proyección del Instructor ni su autoservicio. Migración aditiva, nullable, idempotente y sin reinterpretar la fecha histórica.

## Fase 4B — Rutas y autorización v11

`relaciones_perfil.py` separa catálogo/operaciones del módulo de evaluaciones. GET `/api/cursos` Administrador/Jefe; POST y PATCH `/api/cursos[/<id>]` solo Administrador. Capacitaciones existentes aceptan curso_id opcional validado; se mantiene compatibilidad de nombres históricos. GET `/api/instructor-voluntario/capacitaciones` devuelve proyección propia sin observaciones; página `/mis-cursos`.

GET `/api/operaciones` por ámbito; POST/PATCH de eventos Administrador/Jefe (permiso ampliado confirmado el 2026-10-14); POST `/api/operaciones/<id>/participaciones` Administrador/Jefe con validación de personal activo global SBRAB, singular o lote atómico. Instructor recibe solo eventos propios con su propia participación; ningún control mutable. Página `/gestion/operaciones` disponible por rol. Sin borrado/desvinculación habilitados. Mutaciones con CSRF y auditoría mínima.

Geografía ampliada validada en `perfil_residencia.py`, persistida en perfil_geografico sin reconstruir columnas v9. La página Mi perfil muestra residencia/nacionalidad propias en lectura; PATCH de autoservicio continúa aceptando únicamente correo/foto. Incorporación no se expone.

### Actualización vigente — Cursos por Jefe y PDF operativo (2026-10-10)

El solicitante autorizó también al Jefe de Personal a crear/editar el catálogo común; esta decisión sustituye la exclusividad administrativa anterior. Administrador y Jefe ven formulario Registro de curso, edición modal y menú/título “Capacitaciones y Cursos”. La asignación de personas continúa fuera de esta pantalla; historial personal conservado.

Reporte GET `/api/cursos/reporte.pdf`, autorizado para Administrador/Jefe; Instructor excluido. Rango obligatorio e inclusivo por fecha de inicio, tipo/estado opcionales combinados; fechas/filtros inválidos rechazados. Cursos sin inicio excluidos; resultado vacío produce PDF explícito. Incluye nombre, tipo, entidad, fechas, estado y total, sin datos personales ni observaciones. Carimbo en cada página con logo SBRAB, nombre institucional completo, fecha/hora de Bolivia y numeración; respuesta privada no-store y auditoría mínima de generación.

ReportLab incorporado a requirements y al entorno existente; no se recreó .venv, .env ni base. Este reporte inicia una entrega operativa acotada de Fase 7; no implementa reportes personales/psicométricos, Excel ni promedios oficiales. Privacidad/retención y aprobación del piloto siguen pendientes.

### Entrega vigente — Asistencia, correcciones, calendario y reporte (2026-10-10, v13)

- Administrador consulta/registra/corrige asistencia; Jefe solo personal activo asignado. La llamada muestra nombre del responsable autenticado, gestión anual de la fecha seleccionada y fecha; conserva actividad obligatoria. Los cuatro estados exactos son Asiste, Atraso, Permiso y Falta. Llamada nueva inicia todas las filas en Falta; al elegir fecha/actividad existente se cargan sus estados guardados para corregirlos.
- Clave única persona/fecha/actividad: guardar otra vez actualiza el mismo registro. Corrección conserva estado anterior/nuevo, actor y fecha UTC en historial_asistencias mediante trigger; cambios se auditan. Repetir el mismo estado no crea corrección ni sustituye al último responsable. No se permiten cambiar identidad/fecha/actividad mediante el PATCH de corrección. Históricos no se borran ni se fabrican correcciones anteriores.
- Instructor consulta solo su calendario anual y totales de los cuatro estados, sin datos de terceros ni observaciones ni edición. El día puede tener varias llamadas; totales cuentan registros, no días calendario. Sin registro no se considera Falta.
- Reporte matricial por rango inclusivo de fechas, sin materia ni filtros adicionales. Columnas por fecha/actividad, código y nombre, cuatro totales y porcentaje. Asiste y Atraso cuentan como asistencia; Permiso excluido: (Asiste + Atraso)/(Asiste + Atraso + Falta), redondeado a dos decimales; sin denominador, No disponible. Es un indicador operativo aprobado para esta entrega, no una nota ni promedio oficial de Fase 5B. Jefe exporta solo ámbito activo asignado; Administrador todo su alcance; Instructor no exporta reporte administrativo.
- PDF imprimible horizontal: matriz dividida en bloques de hasta ocho llamadas, filas paginadas y cabeceras repetidas, sin perder columnas. Carimbo SBRAB en cada página con escudo, nombre completo institucional y generación en hora de Bolivia; paginación, rango, leyenda y fórmula visibles. Sin observaciones; descarga privada no-store y auditoría mínima.
- Migración local v13 tras respaldo: 23 tablas anteriores preservadas, inicialización repetida, quick_check=ok y cero infracciones FK. Entorno, secretos y base existente conservados. Aceptación operativa del solicitante pendiente; Fase 5A aún requiere revisar integralmente cursos/notas y sus casos de corrección. Retención/privacidad y autorización institucional siguen pendientes antes del piloto.

Rutas de asistencia v13: PATCH `/api/jefe-personal/asistencias/<id>` estado exclusivamente; GET `/<id>/historial` por ámbito. `/api/instructor-voluntario/asistencias?gestion=AAAA` se liga siempre a la cuenta autenticada, con proyección fecha/estado; `/mis-asistencias` presenta calendario. GET `/api/jefe-personal/asistencias/reporte` y `/reporte.pdf` admiten solo desde/hasta; backend valida rango/ámbito. Módulos `asistencias.py` y `reportes_asistencias.py`; carimbo compartido con cursos.


Actualización de perfil v14 (2026-10-10): validación compartida de fecha de incorporación con sincronización de año/fecha histórica solo por edición explícita. Grado de catálogo validado en servidor; permisos administrativos/Jefe activo asignado y consulta propia. Alta administrativa admite ACTIVO/INACTIVO; solicitudes siempre PENDIENTE y público sin grado. Altas requieren multipart con foto validada, correo, nacionalidad y departamento. Migración aditiva nullable y auditada por las operaciones existentes; no inferir valores históricos.


Cierre técnico 5A (2026-10-11): calificaciones validan campos y referencia entera positiva; BEGIN IMMEDIATE engloba autorización, comprobación de última nota e inserción para serializar guardados concurrentes. Conflicto devuelve 409 sin rama; rechazos posteriores al inicio hacen rollback. Interfaz preserva asignación, espera historial y bloquea guardado durante carga/envío/error/período cerrado. Una edición de capacitación vinculada sin cambiar curso_id conserva nombre histórico; fecha opcional exige ISO de calendario. Sin cambios de esquema v14. Evidencias en [cierre 5A](08_cierre_fase_5a.md).


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


### Módulo y contratos de períodos 5B

`sicose.periodos_5b` expone la página administrativa `/gestion/periodos-5b`, GET/POST `/api/admin/5b/periodos`, POST/PATCH `/api/admin/5b/periodos/<id>/configuracion` y POST `/api/admin/5b/periodos/<id>/publicar`. POST de período recibe nombre/ano; PATCH de configuración y publicación exigen revisión vigente. BEGIN IMMEDIATE serializa publicación y edición; conflictos devuelven 409 y revierten toda la transacción. Los triggers protegen activo único, congelación y notas vinculadas. CSRF y role_required se mantienen. El alta anterior `/api/admin/periodos` solo admite BORRADOR anual.


## Primera entrega de la reformulación — 2026-10-12 (v17)

Jefe único activo con alcance global sin filtro de asignación; Comandante retirado del acceso operativo, conservado solo en datos históricos. Desempeño del Comandante transcrito por Administrador/Jefe con nombre del evaluador y autor de transcripción separados. Tabla Evaluaciones por gestión y consulta modal de activos/inactivos, habilitación individual con historial y notas 5B bloqueadas al deshabilitar; PDF administrativo con carimbo SBRAB. Instructor consulta habilitación/estado/avance por gestión, todavía sin notas publicadas.

Acuerdos complementarios: Académica acumulará puntos enteros con tope 100; puntos individuales ajustables, gestión de finalización personal y cómputo único. Administrador/Jefe publicarán; después de corrección se conservará la versión publicada anterior hasta republicar. **Cursos con puntos, programación/reprogramación física, No cumplida=0, acumulación y publicación/republicación aún pendientes.** El flujo manual académico anterior y configuraciones congeladas no se convierten automáticamente. Psicometría continúa bloqueada; Fase 5B no cerrada.

Evidencia vigente: 81 pruebas aprobadas en 45,711 s; ocho escenarios UI, PDF sintético de cinco páginas, compilación/sintaxis/enlaces/diff correctos. Migración v17 tras respaldo, 28 tablas anteriores preservadas, inicialización repetida, quick_check=ok, FK=0. Detalles en [reglas y estado](10_reformulacion_evaluaciones.md). Siguiente entrega: cursos con puntaje y asignación/finalización individual con historial.


## Cursos y formación personal implementados — 2026-10-12 (v18)

Administrador/Jefe registran/editar catálogo con puntaje entero 0–100, fechas/entidad obligatorias en cursos nuevos y estado automático de Bolivia. Asignación personal/múltiple sin duplicados, finalización independiente con puntaje y fecha explícitos, correcciones con actor/fecha/motivo/revisión y valores anteriores preservados. Edición del catálogo no reescribe datos capturados al asignar. Inactivos solo consulta/historial. Instructor ve sus estados y formación histórica, sin puntajes hasta publicación; Dashboard/seguimiento enlazan las participaciones. PDF de catálogo filtra estado calculado. Histórico sin datos completos permanece intacto y sin puntos inferidos.

Verificación vigente: 86 pruebas aprobadas en 87,375 s; 12 escenarios UI, sin desborde/errores; migración local tras respaldo e inicialización repetida preservando 29 tablas, quick_check=ok y FK=0. Compilación, sintaxis, enlaces y diff correctos. Detalles en [reglas y entrega v18](11_cursos_formacion.md). Pendientes acumulado académico hasta 100, físicas/reprogramación/No cumplida, publicación/republicación y cierres; no se declara cierre 5B ni del piloto.


sicose.formacion concentra validación de puntaje/fechas, fecha de Bolivia, proyección de estado del catálogo y API de participaciones. sicose.relaciones_perfil conserva las rutas existentes del catálogo/PDF, usando esa proyección. frontend/static/js/cursos.js reemplaza el bloque previo de cursos en app.js y atiende catálogo/modales y consulta propia; no agrega frameworks ni dependencias.


Edición administrativa de gestión: PATCH `/api/admin/5b/periodos/<id>` recibe nombre/ano y nombre_anterior/ano_anterior. BEGIN IMMEDIATE, comparación de valores anteriores y bloqueo de registros/configuración publicada; actualiza fechas anuales e incrementa revisión de configuración borrador para evitar publicación desde una vista obsoleta. Auditada, con conflictos 409; role_required ADMINISTRADOR. Consulta por año del Jefe/Instructor sigue en `/api/evaluaciones/gestiones`. Sin migración de esquema.


## Actualización 5B.2 — 2026-10-13

`gestiones.py` separa baja lógica/activación anual de la habilitación personal; `calculos_5b.py` implementa opt-in de regla v2 y cálculo provisional exacto con fuentes referenciadas. Blueprints registrados en la fábrica existente; Flask/SQLite/JavaScript puro, sin dependencias nuevas ni reestructuración masiva. Vistas de catálogo, Gestiones, habilitación y notas/resultados diferenciadas, con autorización backend y CSRF. [Reglas, contratos y límites](14_calculos_y_gestiones.md). Publicación e instantáneas siguen pendientes.


## Actualización 5B.3 — 2026-10-13

`publicaciones_5b.py` genera versiones explícitas de físicas/formación en una transacción serializada, con firma/revisión para detectar vistas obsoletas. No reutiliza la proyección del cálculo conjunto: construye un contrato positivo independiente, sin consultar Desempeño. APIs propias filtran visibilidad actual y entregan valores publicados anteriores, nunca puntajes corrientes sin republicar. Historial administrativo separado; [reglas y límites](15_publicacion_notas.md).

## Cierres y reaperturas — 2026-10-14, v22

`cierres_5b.py` separa el ciclo administrativo de la publicación de notas. Construye revisión/firma y snapshots por persona en lectura consistente; el cierre recalcula la firma y guarda cierre, instantáneas y estado CERRADO dentro de BEGIN IMMEDIATE. Reapertura motivada conserva versiones/configuración y respeta activo único. Las lecturas numéricas de una Gestión cerrada usan el snapshot; no reconstruyen un cierre antiguo con cursos o reglas actuales. `formacion.py` bloquea cambios que afecten al año anterior o nuevo cerrado. Rutas administrativas de cierre e historial con caché privada; proyecciones propias no amplían permisos. [Diseño y contratos](16_cierres_reaperturas.md).

## Compatibilidad histórica v23 — 2026-10-14

`historicos_5b.py` implementa una reapertura excepcional administrativa separada del ciclo ordinario de cierres. Reutiliza la captura de fuentes de `cierres_5b.preparar` en modo documental: no calcula resultados ni simula la instantánea original. Conserva evidencia inmutable con firma, actor/motivo/fecha y actualiza ACTIVO en la misma transacción. La activación de una regla nueva queda bloqueada tras este evento; una regla/configuración existente permanece intacta. Las vistas administrativas distinguen evidencia de reapertura y cierres posteriores. [Contratos](16_cierres_reaperturas.md) y [ensayo operativo pendiente](17_validacion_integral_5b.md).


Actualización de permisos y navegación — 2026-10-14: Administrador/Jefe crean y editan operaciones y asignan participantes, también mediante lote atómico por checkbox. Centro de reportes administrativo con PDF de formación personal finalizada y operaciones/participantes; campos privados excluidos. Esto sustituye el alcance anterior de eventos exclusivos del Administrador. [Espacio del Jefe y reportes](19_espacio_jefe_reportes.md).
