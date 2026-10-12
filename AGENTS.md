# Guía del proyecto SICOSE

SICOSE significa **Sistema de Control y Evaluación de Personal**. Es un prototipo académico para seguimiento de personal voluntario de rescate y emergencias, no un producto comercial ni clínico.

## Stack y arquitectura

- Frontend: HTML5, CSS3 y JavaScript puro.
- Backend: Python y Flask; comunicación de interfaz mediante API REST JSON.
- Persistencia: SQLite con consultas parametrizadas, claves foráneas activadas y cambios de esquema aditivos.
- Mantener módulos pequeños y nombres consistentes en español. No agregar frameworks/servicios sin necesidad y autorización.
- Identidad visual aprobada: azul `#1D1BBE`, naranja `#F57B1A`; incorporar el emblema institucional SBRAB proporcionado en la cabecera de la barra lateral. Usar Evaluar.com solo como referencia general, sin copiar marca o interfaz.

## Roles y datos

- Roles operativos vigentes: `ADMINISTRADOR` (Administrador), `JEFE_PERSONAL` (Jefe de Personal), `INSTRUCTOR_VOLUNTARIO` (Instructor Voluntario). Las bases previas con `INSTRUCTOR`/`VOLUNTARIO` se migran preservando IDs e historial.
- Toda autorización debe comprobarse en el backend; ocultar controles de interfaz no constituye seguridad.
- El Jefe de Personal desactiva, no elimina físicamente, Instructores Voluntarios. Conservar historial y evitar cascadas destructivas.
- Estados pendientes/inactivos no acceden a información protegida.
- No incorporar reactivos ni habilitar pruebas psicométricas sin verificar licencia, versión lingüística, puntuación y revisión profesional.
- No almacenar datos reales para demo. No exponer SQLite, contraseñas, hashes, claves ni tokens a la interfaz.

## Seguridad

- Contraseñas con hash moderno y secretos únicamente desde entorno/`.env` local ignorado por Git.
- Sesiones protegidas, cookie HttpOnly/SameSite, Secure en HTTPS y CSRF en operaciones mutables con cookie.
- Validar entradas en servidor, parametrizar SQL y devolver errores JSON claros sin trazas ni información sensible.
- Auditar operaciones sensibles con metadatos mínimos; nunca registrar credenciales o respuestas psicométricas completas.
- La IA no existe aún. No inventar predicciones ni presentar reglas como modelo entrenado.

## Desarrollo

- Antes de cambiar archivos, inspeccionar el estado actual y explicar objetivo/alcance.
- Avanzar por fases pequeñas. Mantener README y documentos técnicos alineados con lo realmente implementado.
- Ejecutar pruebas relevantes y reportar exactamente sus resultados; no afirmar funciones sin verificarlas.
- No borrar datos históricos ni resetear la base en comandos de inicialización.
- Si falta una decisión que afecte privacidad, autorización, puntuación o validez psicométrica, documentar el límite y consultar antes de asumir.

## Punto de continuidad — 2026-10-11 (cierre técnico 5A)

Este bloque consolida el estado vigente. Las entregas y verificaciones anteriores están en [HISTORY.md](HISTORY.md); no deben tratarse como ejecuciones nuevas.

### Estado y entorno

- **Fase:** 5A cerrada técnicamente; aceptación operativa del solicitante pendiente, igual que perfiles de 4A/4B. Reglas 5B acordadas para el prototipo; Comandante/fuentes/respaldo y borradores/configuración/publicación/activación implementados; cursos con puntos/finalización personal implementados; pendientes físicas, acumulado académico, publicación y cierres según docs/09_reglas_fase_5b.md. Evidencias en [cierre 5A](docs/08_cierre_fase_5a.md); conservar numeración de [plan](docs/05_plan_desarrollo.md).
- **Esquema:** SQLite v18; cursos.puntaje y participaciones/historial de formación implementados; habilitación por persona/gestión y Jefe único activo; rol Comandante y notas_operativas/respaldo_academico implementados. Datos anteriores preservados. Grado y fecha_incorporacion nullable; no rellenar históricos ni inferir grado/fechas. Migraciones aditivas con respaldo y comprobación de integridad cuando sean necesarias; nunca resetear.
- **Entorno existente:** .venv, .env e instance/sicose.sqlite3. No recrear ni reemplazar configuración/base ni mostrar secretos. Inspeccionar Git y preservar cambios locales. Al inicio de esta revisión había un cambio en frontend/login.html: se conserva y no se le atribuye una fecha de implementación.
- **Suite histórica v16:** 2026-10-11, 77 pruebas aprobadas en 86,620 s con bases aisladas; ocho escenarios UI de segunda entrega 5B y migración local v16 preservando las 26 tablas anteriores. Primera entrega: 73 pruebas/80,440 s, histórica. Evidencia 5A (68 pruebas/20 escenarios) queda histórica en HISTORY.
- **Comprobación de la revisión documental anterior (2026-10-11):** código/rutas/plantillas contrastados; 64 pruebas definidas; base consultada en modo solo lectura, versión 14, quick_check=ok y cero infracciones FK. Enlaces locales y git diff --check comprobados. Sin migraciones ni cambios funcionales.

### Decisiones confirmadas: no volver a preguntar

- Roles ADMINISTRADOR, JEFE_PERSONAL e INSTRUCTOR_VOLUNTARIO, dashboards propios y autorización en backend. Pendientes/inactivos sin acceso protegido.
- Administrador crea cuentas ACTIVO/INACTIVO, administra personal global, aprueba/rechaza solicitudes y restablece claves. Jefe solicita altas PENDIENTE asignadas a sí mismo y consulta/edita/desactiva solo personal activo asignado; no elige otro equipo ni aprueba solicitudes. No hay eliminación física.
- Instructor edita exclusivamente correo/foto propios. Consulta grado, datos geográficos, especialidades, formación y participaciones propios; no notas, observaciones ni información de terceros. Incorporación sigue limitada a gestión.
- Alta/solicitud: identidad, especialidad principal, usuario, correo, contraseña, nacionalidad, departamento y foto PNG/JPEG hasta 3 MiB; correo/nacionalidad/departamento/foto obligatorios en servidor. Fecha de incorporación y grado opcionales. Solicitud pública sin grado ni selector de estado habilitante; siempre pendiente.
- Código generado en servidor: iniciales de nombres y ambos apellidos + DDMMAA. Colisión rechazada preventivamente; política definitiva pendiente.
- Grados: Instructor Inicial, Instructor Segundo, Instructor Primero, Instructor Principal e Instructor Mayor. Administrador/Jefe autorizado asignan/editan; Jefe puede proponerlo en alta de su equipo. Instructor consulta el propio. No inferir por antigüedad ni asignar a históricos.
- Especialidades principal/secundarias: Rescate en agua, Rescate en montaña, Rescate en selva, Lucha contra incendios, Primeros Auxilios y K-9. Secundarias múltiples sin duplicados; principal permitida también como secundaria. Especialidad principal implementada desde v8.
- Una sola Fecha de incorporación en formularios. Guardarla sincroniza fecha_incorporacion, ano_incorporacion y antiguedad_desde; antigüedad = año calendario actual del servidor menos incorporación, sin aniversario. Rechazar futuro/incoherencias. Históricos mantienen año/fecha antigua hasta completar explícitamente la fecha canónica; no convertir un año en una fecha ficticia. Borrar fecha canónica existente borra sus derivados.
- Nacionalidad independiente de residencia, catálogo existente de 20 países latinoamericanos. Altas envían Bolivia sin selector visible y usan nueve departamentos. Conservar otras residencias/provincias históricas; no reclasificarlas automáticamente.
- Directorio de Instructores: Nombre completo, Código, Grado, Especialidad Principal, Estado, Antigüedad, Acciones. Estado horizontal verde/rojo, texto sin partir. Celdas alineadas, contenedores internos flex y tres iconos lado a lado con aria-label/title: Ver y Editar en modal, Desactivar con baja lógica. Restablecer clave dentro de Editar, solo Administrador.
- Asistencia: fecha y actividad, cuatro estados exactos Asiste/Atraso/Permiso/Falta; nueva llamada toda Falta. Actividades Ordinaria, Actividad Externa, Terreno y Operación, sin cambiar textos históricos. Cabecera Responsable/Gestión/Actividad/Fecha en fila de escritorio, adaptación móvil. Tabla Nombre completo/Código/Estado/Asistencia.
- Clave única persona/fecha/actividad; cargar estados guardados al seleccionar llamada existente. Corrección conserva anterior/nuevo, actor y fecha UTC; no duplicar correcciones si estado no cambia. Sin registro no equivale a Falta. Calendario propio anual y totales cuentan registros, no días.
- Reporte asistencia: rango inclusivo, matriz por fecha/actividad, cuatro totales y porcentaje (Asiste+Atraso)/(Asiste+Atraso+Falta), Permiso excluido, dos decimales y No disponible si denominador cero. Indicador operativo, no nota/promedio oficial. PDF horizontal con carimbo institucional; Jefe solo ámbito activo asignado, Instructor sin exportación administrativa.
- Capacitaciones y Cursos registra catálogo independiente; ahora permite asignar personas mediante modal, sin duplicados, y finalizar/corregir su participación con historial (v18). Administrador/Jefe crean/editan catálogo común, edición modal. Tipos Capacitación/Especialización/Actualización/Taller/Seminario (Webinar); estados Próximo/En curso/Finalizado, calculados según fecha de Bolivia en v18. Nombre/tipo/entidad/fechas/puntaje entero 0–100 obligatorios en cursos nuevos; fin no anterior a inicio. PDF por rango de inicio y tipo/estado opcionales; sin inicio excluido. Sin observaciones ni datos personales en PDF.
- Historial personal de capacitaciones y APIs por ámbito conservados, curso_id opcional sin enlace automático. Renombrar catálogo no reescribe nombres históricos. Instructor consulta lo propio sin observaciones.
- Operaciones: Administrador crea/edita eventos (tipo/lugar/inicio-fin/institución); Administrador/Jefe vinculan personal activo autorizado; Jefe no gestiona eventos. Instructor consulta solo su participación sin terceros/observaciones. Sin borrado/desvinculación implementados; experiencia_operaciones sigue como texto histórico independiente.
- Notas manuales 0–100, corrección enlazada a la más reciente conservando anteriores y actor/fecha. Rechazo de psicometría y período cerrado. Instructor solo estado/avance sin notas/observaciones. Cierre técnico 5A verificado: guardado conserva selección, historial cargado antes de corregir, período cerrado/error bloquea edición y BEGIN IMMEDIATE serializa última nota/inserción. Rechazar referencias no enteras/campos ajenos; recargar historial tras conflicto. Aceptación operativa humana sigue pendiente.
- Año de cabecera calculado con calendario local del servidor; no crea/renombra períodos persistidos. Tablas de pesos no equivalen a gestión completa de versiones ni promedios oficiales.
- PDF operativos de cursos/asistencia implementados, privados no-store, con logo SBRAB, nombre completo institucional y generación en hora de Bolivia. Excel, informes consolidados y resultados psicométricos no implementados. /api/admin/estado comprueba acceso administrativo, no salud integral.
- Logo SBRAB, azul #1D1BBE, naranja #F57B1A, barra plegable y claro/oscuro. Evaluar.com solo referencia general.

### Límites y decisiones abiertas

Política definitiva de colisiones; aceptación operativa de 4A/4B/5A; implementación de las reglas 5B ya acordadas para el prototipo (no acreditan aprobación institucional de puntuación). Reportes operativos pueden avanzar sin psicometría con alcance y permisos definidos.

No habilitar psicometría sin aprobación institucional/profesional, licencia/derechos, idioma, puntuación, intentos y retención. No fabricar reactivos/resultados. Piloto requiere respaldo/restauración, HTTPS/WSGI, operación, privacidad/minimización/retención y aceptación institucional. IA no implementada, opcional en Fase 8 y fuera del cierre básico.

### Continuar en Windows

Desde la raíz, activar .venv existente y ejecutar `flask --app sicose run --debug`. Pruebas: `python -m unittest discover -s tests -v`. El cierre 5A no cambió esquema ni base local y no requiere init-db, seed ni reinstalación. Para cambios futuros leer [README.md](README.md), [especificación](docs/01_especificacion_funcional.md), [arquitectura](docs/02_arquitectura_tecnica.md), [datos](docs/03_modelo_datos.md), [plan](docs/05_plan_desarrollo.md) y [guía de inicio](docs/07_inicio_desarrollo.md).


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


### Aclaración vigente — Gestiones de evaluaciones (2026-10-12)

Solo Administrador ve la administración de gestiones y crea/edita sus borradores/configuración. Jefe e Instructor conservan el selector de año solo para consulta de evaluaciones; no ocultarlo. Backend restringe APIs administrativas. Nueva edición de nombre/año solo en borrador anual sin asignaciones/notas/configuración publicada, con comprobación de valores anteriores; incrementa revisión del borrador para evitar publicación obsoleta. Sin cambiar gestiones históricas, esquema o base local. Evidencia de esta corrección: 10 pruebas en 7,090 s y seis escenarios UI; detalle en HISTORY.
