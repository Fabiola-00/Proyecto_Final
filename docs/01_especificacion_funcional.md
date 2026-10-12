# 01. Especificación funcional

**Estado:** requerimientos funcionales aprobados para separación por rol y Fase 5. Fase 5 añade asistencias, catálogo/asignación de evaluaciones y notas no psicométricas con historial. El sistema aún no incorpora formularios psicométricos: todos los candidatos documentados siguen pendientes de autorización profesional/institucional, versión exacta, derechos y regla de puntuación. Las capacidades sin ruta o pantalla continúan pendientes.

## Propósito y alcance

SICOSE apoyará el seguimiento, capacitación y evaluación periódica de voluntarios de rescate y emergencias. El prototipo tendrá autenticación, permisos por rol, perfiles, seis evaluaciones, períodos con ponderaciones versionadas, historial y reportes. La IA se reserva como integración futura, sin generar predicciones en esta fase.

## Roles y permisos requeridos

La matriz expresa el alcance requerido, no una certificación de implementación. Estado comprobado al 2026-10-10: alta manual exclusiva del Administrador; Jefe consulta, edita y desactiva personal activo asignado, con solicitudes de alta pendientes de aprobación administrativa; autoservicio de correo y foto implementado; Instructor consulta estados/avance, cursos y operaciones propios, especialidades secundarias y geografía propia, sin notas ni observaciones. Psicometría, reportes y cálculos oficiales no están implementados. Véase [plan y criterios de cierre](05_plan_desarrollo.md).

| Capacidad | Administrador | Jefe de Personal | Instructor Voluntario |
|---|---:|---:|---:|
| Iniciar sesión y abrir su dashboard por rol | Sí | Sí | Sí |
| Administrar todas las cuentas y evaluaciones | Sí | No | No |
| Consultar, crear, editar y desactivar personal | Administrador: operaciones implementadas | Consulta/edición/desactivación de activos asignados y solicitud de alta pendiente de aprobación administrativa implementadas | No |
| Editar datos personales | Todas las cuentas | Perfil de voluntario dentro de su ámbito | Solo correo y foto propios (implementado) |
| Ver estado/avance de evaluaciones | Todos | Voluntarios de su ámbito | Evaluaciones propias completadas y pendientes |
| Ver resultados psicométricos de voluntarios | Sí, administración global | Sí, solo voluntarios autorizados | No |
| Modificar notas/resultados psicométricos | Gestión administrativa global, con auditoría | No | No |
| Activar/desactivar una prueba psicométrica por voluntario | Sí | Sí, dentro de su ámbito | No |
| Registrar notas de evaluación física, cursos y desempeño | Sí | Sí, para su ámbito | No |
| Editar calificaciones u observaciones | Sí, sujeto a historial y auditoría | Solo calificaciones no psicométricas de su ámbito; psicométricas no | No |
| Ver notas u observaciones individuales | Sí, según autorización institucional | Sí, para voluntarios de su ámbito | No |

Una solicitud de registro o usuario invitado se mantiene `pendiente` hasta aprobación. Las rutas API deben denegar datos protegidos y evaluaciones antes de esa aprobación. La autorización se aplica en backend a cada recurso, no solo ocultando controles. Tras autenticarse, cada cuenta se dirige al dashboard correspondiente a su rol: Administrador, Jefe de Personal o Instructor Voluntario; no se comparte un dashboard con contenido intercambiado por URL.

El dashboard administrativo ofrece control global de cuentas y evaluaciones. El dashboard del Jefe de Personal se limita a sus voluntarios activos asignados, sus evaluaciones y resultados autorizados y el registro de notas no psicométricas. El dashboard del Instructor Voluntario permite actualizar solo correo y foto propios y consultar qué evaluaciones propias están completadas o pendientes y ver un resumen limitado, sin editar calificaciones.

El resumen del Instructor Voluntario muestra solamente estado y avance. No expone notas/calificaciones, resultados individuales ni observaciones.

## Flujos objetivo (incluyen capacidades pendientes)

1. Administrador crea un período, confirma pesos que suman 100% y administra usuarios y Jefes de Personal.
2. Un Instructor Voluntario solicita alta o ingresa con código de invitación; el administrador aprueba o rechaza. No se concede sesión protegida al estado pendiente.
3. Una cuenta autenticada es redirigida al dashboard exclusivo de su rol. Administración gestiona globalmente las cuentas y evaluaciones.
4. Jefe de Personal da de alta/edita/desactiva voluntarios activos de su ámbito, consulta evaluaciones/resultados permitidos, registra notas físicas, de cursos y desempeño, y activa/desactiva pruebas psicométricas por voluntario sin poder alterar sus notas.
5. El Instructor Voluntario puede editar solo correo y foto propios, ve evaluaciones completadas/pendientes y resumen permitido, pero no edita calificaciones.
6. El Instructor Voluntario completa cada prueba habilitada. Reiniciar crea intento nuevo y conserva el anterior.
7. El sistema calcula avance y promedio ponderado solo con una regla de datos faltantes previamente aprobada; hasta aprobar esas reglas no hay cálculo oficial implementado; no se adopta una regla de faltantes por defecto.
8. Usuarios autorizados descargan reportes PDF individuales/consolidados y Excel según permisos.

## Evaluaciones y calificaciones

Seis componentes por período: psicométrica 1, 2 y 3 (autoinforme); física; rendimiento académico; criterio del instructor. Escala institucional propuesta de 0–100. Pesos iniciales configurables: 10%, 10%, 10%, 25%, 15%, 30%. La configuración es una hipótesis inicial para aprobar, no una ponderación validada científicamente. Fase 5 no carga reactivos, procesa respuestas ni habilita candidatos pendientes. El flujo manual rechaza calificaciones de categoría psicométrica.

La nota 0 debe distinguirse de “sin evaluar”. El requisito futuro es que cada calificación quede vinculada a autor, fecha, período, evaluación y versión del peso aplicable; actualmente la asignación vincula período/evaluación, pero no hay vinculación completa a pesos publicados. Los cambios de peso generan versión nueva, no reescriben resultados históricos. Intentos guardan inicio, envío, estado y puntuación oficial/normalizada si está aprobada.

## Perfil y seguimiento

Datos del Instructor Voluntario requeridos: nombres, apellidos paterno y materno, fecha completa de nacimiento para formar su código institucional `XXX-DDMMAA`, nacionalidad, departamento según país, año de incorporación, antigüedad calculada por año, especialidad principal/secundarias, cursos y operaciones vinculados. La fecha completa se solicitó expresamente para el código; se limita a administración y Jefes de Personal autorizados. En la implementación v8 están persistidos nombres/apellidos, nacimiento, código y especialidad principal con catálogo acordado; la migración conserva NULL para perfiles antiguos. En v9 están implementados país/departamento de residencia (Bolivia inicialmente) y año de incorporación con antigüedad calculada por diferencia de años calendario; no son nacionalidad. Son opcionales, no se infieren datos históricos, y solo Administrador/Jefe autorizado los ven/editan. Desde v11 consulta residencia/nacionalidad propias, sin editar; incorporación permanece oculta. En v11 están implementados nacionalidad/residencia ampliada, cursos y operaciones relacionados, según las reglas actuales abajo. La retención y visibilidad del resto de campos requiere política institucional. Registrar auditoría para aprobación de usuarios, reasignaciones, cambios de nota/pesos, estados de pruebas y generación/revisión de informes.

## Reportes

Pendientes: separar reportes operativos (pueden avanzar sin psicometría con alcance/permisos definidos) de reportes con resultados psicométricos (requieren cierre de Fase 6). Promedios requieren además reglas de Fase 5B aprobadas.

PDF individual, PDF consolidado y Excel: datos necesarios, notas por componente, avance, promedio cuando calculable, observaciones autorizadas y fechas. El reporte no incluye respuestas psicométricas salvo necesidad profesional y aprobación explícita. Sección IA queda omitida/no disponible hasta la existencia de modelo validado; no mostrar recomendaciones ficticias.

## Fuera de alcance inicial

Aplicación de instrumentos no aprobados, diagnóstico, decisión automática de permanencia, integración de modelo/dataset, sincronización con terceros, pagos, firma electrónica, portal público de resultados y analítica predictiva.

## Criterios funcionales de aceptación futuros

- Después de autenticarse, cada usuario llega a su dashboard correspondiente; no puede abrir dashboards o datos de otro rol.
- Jefe de Personal solo consulta y opera voluntarios activos asignados; puede registrar notas no psicométricas y activar/desactivar pruebas, pero no modificar resultados psicométricos.
- Instructor Voluntario edita únicamente correo y foto de su cuenta, consulta estados/avance propios y nunca accede a notas, resultados individuales u observaciones.
- Un usuario pendiente no obtiene datos privados ni puede iniciar evaluaciones.
- Un Instructor Voluntario no puede leer/alterar recursos de otra persona mediante URL o API.
- Reintentar una evaluación conserva todos los intentos previos.
- Una nueva versión de ponderación no modifica períodos o resultados cerrados.
- Los roles y acciones sensibles quedan comprobables mediante auditoría.
- Interfaz usable en móvil y escritorio, con estados vacíos, carga y error comprensibles.

### Estado vigente — Cierre técnico de Fase 4B (2026-10-10)

Esquema v11. Nacionalidad (país) y residencia diferenciadas, con 20 países latinoamericanos iniciales; Bolivia con nueve departamentos, los demás con provincia/departamento en texto libre. Administrador/Jefe autorizado editan; Instructor consulta sus propios datos geográficos. Incorporación sigue limitada a gestión. Secundarias consultables por ámbito, editables por Administrador/Jefe; la principal puede repetirse como secundaria.

Catálogo común de cursos creado/editado solo por Administrador; capacitaciones vinculadas opcionalmente por Administrador/Jefe al personal de su ámbito activo. Instructor consulta su formación sin observaciones. Históricos sin enlace automático; renombrar catálogo no cambia nombres previamente registrados. Administrador crea/edita eventos de operaciones; Administrador/Jefe vinculan personal activo de su ámbito; Instructor consulta solo sus participaciones. Se conserva el texto histórico de experiencia; no se implementa borrado/desvinculación.

58 pruebas aprobadas en 62,893 s. Migración local v11 con respaldo, 19 tablas anteriores preservadas, inicialización repetida, curso_id previo NULL, quick_check=ok y cero infracciones FK. Cierre técnico implementado; aceptación operativa pendiente. Siguiente entrega: Fase 5A, ensayo de asistencia, capacitaciones y notas manuales por rol, con correcciones e historial. Privacidad/retención y autorización institucional siguen pendientes antes del piloto.

### Corrección vigente — Registro de cursos (2026-10-10, v12)

La pantalla “Capacitaciones y Cursos” registra cursos independientes de personas. Incluye nombre, tipo (Capacitación, Especialización, Actualización, Taller, Seminario (Webinar)), entidad organizadora, inicio/fin, estado (Próximo, En curso, Finalizado) y observaciones opcionales. Nombre, tipo y estado obligatorios para registros nuevos; fechas/entidad opcionales; fin requiere inicio y no puede precederlo. Estado se elige manualmente, sin deducirlo de fechas. Administrador registra/edita; Jefe consulta el catálogo según permisos ya acordados. Edición mediante modal responsivo con datos precargados y errores en el modal.

Se retiraron de esta pantalla el selector de Instructor y el formulario de asignación. Los registros personales históricos, sus vínculos y APIs se conservan; no hay interfaz nueva de asignación en esta entrega. “Mis cursos” sigue consultando historial personal sin observaciones. Las observaciones del catálogo son distintas del historial personal y solo se muestran a Administrador/Jefe.

Migración v12 aditiva: campos nuevos nullable en cursos, sin inferir tipo, estado ni fechas de históricos. Respaldo SQLite previo, datos de 23 tablas anteriores preservados, inicialización repetida, quick_check=ok y FK=0. 59 pruebas aprobadas en 42,354 s (ejecución final); cuatro escenarios Chromium con API simulada, Administrador/Jefe a 360/1447px, opciones exactas y edición modal correctas. Compilación Python, sintaxis JavaScript y diff comprobados.

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


### Perfil y directorio vigentes — Grado e incorporación (2026-10-10, v14)

- Directorio con Nombre completo, Código, Grado, Especialidad Principal, Estado, Antigüedad y Acciones. Estado horizontal: ACTIVO verde, INACTIVO rojo, con texto identificable. Ver consulta en modal los datos permitidos y foto; Editar perfil usa modal y Desactivar conserva baja lógica. Restablecer contraseña sigue siendo exclusivo del Administrador, dentro de Editar perfil; nunca se muestra la contraseña guardada ni su hash.
- Grados permitidos: Instructor Inicial, Instructor Segundo, Instructor Primero, Instructor Principal e Instructor Mayor. Administrador los asigna/edita; Jefe solo en personal activo asignado y puede proponerlo al solicitar el alta de su equipo. Instructor consulta el suyo sin editar. La solicitud pública no permite enviar grado; queda NULL hasta revisión del personal autorizado. No se asigna un grado por defecto a históricos ni se infiere por antigüedad.
- Una sola Fecha de incorporación en alta y edición. Al registrarla se sincronizan fecha_incorporacion, antiguedad_desde y ano_incorporacion. Antigüedad = año calendario actual del servidor menos año de incorporación, sin descontar meses/días. Fechas inválidas/futuras y año/fecha contradictorios rechazados. Históricos mantienen año y fecha anterior, incluso si difieren, hasta completar explícitamente la nueva fecha; no se fabrican fechas desde un año. Borrar una fecha canónica existente borra también sus dos valores derivados; un formulario sin fecha histórica completa conserva el año previo.
- Alta administrativa permite ACTIVO o INACTIVO. Solicitudes de Jefe/públicas permanecen PENDIENTE, sin selector que habilite acceso, hasta aprobación administrativa. Las cuentas inactivas/pendientes no acceden a información protegida.
- Alta y solicitudes incluyen nombres, ambos apellidos, nacimiento, código generado en servidor, especialidad principal, usuario, correo, contraseña, nacionalidad, departamento y foto PNG/JPEG (máximo 3 MiB). Correo, nacionalidad, departamento y foto ahora son obligatorios también en servidor. Fecha de incorporación y grado son opcionales; las solicitudes públicas no incluyen grado. Residencia Bolivia oculta en las pantallas nuevas, nacionalidad independiente y catálogo latinoamericano existente. Países históricos se conservan en consulta/edición; no hay reclasificación automática a Bolivia en migración. Botón Guardar. Invitaciones usan el mismo formulario y validaciones.
- Migración v14 aditiva: grado y fecha_incorporacion nullable, sin rellenar perfiles anteriores. Respaldo local previo; 24 tablas anteriores preservadas, inicialización repetida, quick_check=ok y cero infracciones de claves foráneas. No se recrearon .venv, .env ni base local.

Verificación actual (2026-10-10): 64 pruebas aprobadas en 31,611 s, con bases aisladas. Ocho escenarios Chromium con datos sintéticos/API simulada (Administración, Jefe, Instructor y solicitud pública; 360/1447 px), modales precargados, campos/opciones/roles y ausencia de desborde comprobados. Compilación Python, sintaxis JavaScript y git diff --check correctos. La primera ejecución detectó dos expectativas antiguas de etiquetas (Guardar y retiro de Especialidad en tabla de asistencia); actualizadas y suite completa repetida. No se afirma cierre de Fase 5A ni aceptación institucional del piloto.


## Primera entrega implementada de Fase 5B — 2026-10-11 (v15)

- Rol COMANDANTE_GRUPO con panel propio y cargo único SBRAB. Administrador crea/edita/desactiva cuentas y restablece contraseña; una sola cuenta Comandante ACTIVO, garantizada también por triggers SQLite. No se reutiliza una cuenta para otra persona ni se elimina autoría; nombre editable e historial con nombres capturados. No se creó una cuenta automáticamente.
- Seguimiento 5B para Administrador/Jefe/Comandante: selección de persona activa/período, perfil básico, formación, asistencia y notas sin asignar históricos a nuevas fuentes. Jefe solo personal activo asignado. Comandante consulta seguimiento de personal activo SBRAB y registra/corrige solo su aportación; sin administración ni observaciones/motivos/referencias privadas ajenas. Instructor sin acceso numérico 5B.
- Cinco fuentes independientes: FISICA_1, FISICA_2, ACADEMICA, DESEMPENO_JEFE y DESEMPENO_COMANDANTE. Notas nuevas 0–100 con hasta dos decimales, almacenadas en centésimas enteras; solo período ACTIVO. Física: Admin/Jefe autorizado. Académica inicial: Jefe; requiere motivo y formación personal referenciada. Desempeño inicial de cada evaluador: Jefe/Comandante correspondiente. Administración puede corregir aportaciones existentes conservando responsable y autor de corrección.
- Cadena por persona/período/fuente: primera nota única, corrección solo de la vigente, inserción serializada y anteriores conservadas. No admitir autor/responsable arbitrarios en JSON. Jefe/Comandante no corrigen Desempeño de otro titular; si cambió responsable, la corrección histórica requiere Administración. Motivo y referencias se conservan como instantánea de respaldo académico; editar el curso después no altera ese respaldo.
- Migración v15: ampliar CHECK de roles preservando IDs/referencias y añadir notas_operativas/respaldo_academico; triggers de Comandante único se crean después de ampliar roles. Inicialización local repetida tras respaldo, 24 tablas anteriores preservadas (roles anteriores incluidos), quick_check=ok y cero infracciones FK. Tablas nuevas vacías, sin cuentas ni notas inferidas. .venv/.env/base existente conservados.
- Verificación: **73 pruebas aprobadas en 80,440 s**, ocho escenarios Chromium (Administración/Jefe/Comandante/gestión de cuenta, 360/1447 px), sin desborde ni errores; modales y envíos, fuentes/roles y período cerrado comprobados. Compilación Python, sintaxis de ambos JavaScript y git diff --check correctos. Pruebas de migración incluyeron esquemas antiguos; se corrigió orden de creación de triggers y fixture de catálogo de roles.

### Límites de esta entrega

Límite histórico v15: configuración/publicación/activación todavía pendientes; implementadas en v16. Cálculo y cierre/reapertura con instantáneas siguen pendientes. No se declara cerrada 5B. Las APIs/notas históricas y pantalla de asignaciones anterior se mantienen por compatibilidad; no se convierten ni participan automáticamente en el futuro cálculo 5B. Instructor conserva su avance existente, sin nuevo resultado 5B. La aceptación operativa del solicitante y requisitos institucionales mantienen sus pendientes.

Siguiente entrega concreta desde v16: cálculo provisional exacto con faltantes/redondeo; después cierre/reapertura con instantáneas.


## Períodos y configuración vigentes — v16 (2026-10-11)

Solo Administrador crea borradores anuales, configura cinco fuentes compatibles y publica/activa. Configuración y fuentes se congelan al publicar; una sola activación bajo concurrencia. Borradores incompletos pueden guardarse, pero no publicarse. Notas y correcciones 5B requieren ACTIVO y configuración PUBLICADA; las referencias a configuración/evaluación las establece el servidor. La vía anterior de notas por asignación no permite registrar en períodos configurados 5B. Períodos/notas anteriores conservados sin adopción automática; un activo histórico bloquea nuevas activaciones sin cerrarlo automáticamente. Cálculo y cierre/reapertura siguen pendientes; ver [reglas](09_reglas_fase_5b.md) y [plan](05_plan_desarrollo.md).


## Primera entrega de la reformulación — 2026-10-12 (v17)

Jefe único activo con alcance global sin filtro de asignación; Comandante retirado del acceso operativo, conservado solo en datos históricos. Desempeño del Comandante transcrito por Administrador/Jefe con nombre del evaluador y autor de transcripción separados. Tabla Evaluaciones por gestión y consulta modal de activos/inactivos, habilitación individual con historial y notas 5B bloqueadas al deshabilitar; PDF administrativo con carimbo SBRAB. Instructor consulta habilitación/estado/avance por gestión, todavía sin notas publicadas.

Acuerdos complementarios: Académica acumulará puntos enteros con tope 100; puntos individuales ajustables, gestión de finalización personal y cómputo único. Administrador/Jefe publicarán; después de corrección se conservará la versión publicada anterior hasta republicar. **Cursos con puntos, programación/reprogramación física, No cumplida=0, acumulación y publicación/republicación aún pendientes.** El flujo manual académico anterior y configuraciones congeladas no se convierten automáticamente. Psicometría continúa bloqueada; Fase 5B no cerrada.

Evidencia vigente: 81 pruebas aprobadas en 45,711 s; ocho escenarios UI, PDF sintético de cinco páginas, compilación/sintaxis/enlaces/diff correctos. Migración v17 tras respaldo, 28 tablas anteriores preservadas, inicialización repetida, quick_check=ok, FK=0. Detalles en [reglas y estado](10_reformulacion_evaluaciones.md). Siguiente entrega: cursos con puntaje y asignación/finalización individual con historial.


## Cursos y formación personal implementados — 2026-10-12 (v18)

Administrador/Jefe registran/editar catálogo con puntaje entero 0–100, fechas/entidad obligatorias en cursos nuevos y estado automático de Bolivia. Asignación personal/múltiple sin duplicados, finalización independiente con puntaje y fecha explícitos, correcciones con actor/fecha/motivo/revisión y valores anteriores preservados. Edición del catálogo no reescribe datos capturados al asignar. Inactivos solo consulta/historial. Instructor ve sus estados y formación histórica, sin puntajes hasta publicación; Dashboard/seguimiento enlazan las participaciones. PDF de catálogo filtra estado calculado. Histórico sin datos completos permanece intacto y sin puntos inferidos.

Verificación vigente: 86 pruebas aprobadas en 87,375 s; 12 escenarios UI, sin desborde/errores; migración local tras respaldo e inicialización repetida preservando 29 tablas, quick_check=ok y FK=0. Compilación, sintaxis, enlaces y diff correctos. Detalles en [reglas y entrega v18](11_cursos_formacion.md). Pendientes acumulado académico hasta 100, físicas/reprogramación/No cumplida, publicación/republicación y cierres; no se declara cierre 5B ni del piloto.
