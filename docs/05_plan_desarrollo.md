# 05. Plan de desarrollo

Estado revisado: **2026-10-11**. **Fase 5A tiene cierre técnico y aceptación operativa pendiente; Fase 5B tiene primera entrega de rol/fuentes/respaldo implementada y ciclo/cálculo/cierres pendientes**. Fase 4B conserva su cierre técnico y aceptación operativa pendiente. La base técnica, autenticación y dashboards funcionan para el prototipo local; esto no acredita preparación para un piloto institucional. Existen PDF operativos de cursos/asistencia; no hay psicometría aplicada, Excel ni IA.

## Numeración y orden de entregas

Se conservan las fases históricas 0 (especificación), 1/1A (base ejecutable), 2 (persistencia/autenticación) y 3 (diseño/dashboards). Las antiguas 4.1 y 4.3 describen gestión administrativa y fotos/recuperación ya implementadas; 4.2 se continúa en 4A. El antiguo rótulo 4B para períodos/ponderaciones se reubica en 5B; desde esta revisión **4B significa ampliación del perfil**. No se reescribe el historial funcional ni se atribuyen fechas nuevas a cambios locales.

Orden recomendado: consolidación documental → 4A → 4B → 5A → 5B. Fase 6 es independiente y condicionada. Los reportes operativos de Fase 7 pueden avanzar sin Fase 6 si tienen alcance y permisos definidos. La preparación del piloto tiene su propia aceptación. Fase 8 es opcional y queda fuera del cierre básico. No se asignan porcentajes ni fechas de entrega.

## Consolidación documental — entrega actual

- **Objetivo:** disponer de una línea base comprobable para continuar el prototipo.
- **Alcance:** README, continuidad de AGENTS, HISTORY, plan y correcciones técnicas necesarias; sin cambiar código, permisos, esquema o entorno.
- **Estado actual:** revisión de rutas, decoradores, esquema, plantillas, JavaScript y pruebas; cambios funcionales locales previos preservados.
- **Pendientes:** mantener la documentación al completar cada entrega futura; esta revisión no cierra capacidades funcionales pendientes.
- **Dependencias:** estado de Git y evidencias del repositorio; acuerdos existentes de roles y privacidad.
- **Cierre verificable:** operaciones documentadas coinciden con rutas y pantallas; enlaces locales válidos; evidencias fechadas y separadas del historial; decisiones pendientes explícitas; `git diff --check` sin errores.

## Fase 4A — Gestión por rol y autoservicio

- **Objetivo:** completar la gestión de personal prevista por rol.
- **Alcance:** alta de Instructor Voluntario por Jefe de Personal y edición del perfil propio por Instructor Voluntario, conservando historial y autorización por objeto.
- **Estado actual:** Administrador lista, crea, edita y desactiva Jefes de Personal e Instructores Voluntarios, aprueba/rechaza solicitudes, asigna personal y restablece claves. El Jefe consulta, edita y desactiva únicamente personal activo asignado; ya registra solicitudes pendientes para su equipo con aprobación/rechazo administrativo. El Instructor ve estados/avance propios sin notas ni observaciones; tiene formulario Mi perfil y API para actualizar exclusivamente correo y foto propios, según alcance autorizado el 2026-10-10.
- **Pendientes:** aceptación visual/operativa de ambos flujos; se conserva rechazo de colisiones hasta definir política definitiva; no se habilitan cambios de identidad/código desde autoservicio. Correo y foto fueron autorizados y están implementados. El 2026-10-10 se acordó alta por Jefe como solicitud pendiente, asignada al Jefe autenticado, con aprobación/rechazo del Administrador.
- **Dependencias:** decisiones confirmadas: altas por Jefe pendientes de aprobación administrativa; autoservicio limitado a correo y foto. Se mantienen los roles y la regla de código acordados.
- **Cierre verificable:** pruebas de altas válidas y denegadas por rol/ámbito, edición exclusivamente propia, rechazo de campos administrativos, CSRF, cuentas pendientes/inactivas sin acceso, conservación del historial y ausencia de notas/observaciones en respuestas al Instructor.

## Fase 4B — Perfil, cursos y operaciones relacionados

- **Objetivo:** completar información del perfil y relaciones de formación/participación sin inventar datos históricos.
- **Alcance implementado:** residencia y nacionalidad diferenciadas, incorporación/antigüedad, especialidades secundarias, catálogo común de cursos y relación opcional desde capacitaciones, eventos y participaciones de operaciones.
- **Estado actual (2026-10-10):** esquema v11; cierre técnico de esta entrega. Especialidad principal resuelta en v8; residencia/incorporación en v9; secundarias en v10; cursos, operaciones y geografía ampliada en v11. Pendiente aceptación operativa del solicitante.
- **Pendientes:** aceptación del recorrido funcional; ampliar países o incorporar catálogos territoriales según necesidad futura. Institución, minimización/retención y uso de datos reales siguen siendo requisitos del piloto.
- **Dependencias:** permisos confirmados por el solicitante y migración aditiva con respaldo. No depende de psicometría ni cálculos oficiales.
- **Cierre verificable:** permisos por rol/objeto, CSRF, fechas ordenadas, duplicados rechazados, consulta propia sin observaciones, provincias conservadas en edición, históricos e IDs preservados; inicialización repetida con integridad SQLite; pruebas y revisión responsiva. Evidencias en el punto de control.

### Reglas confirmadas e implementación

- **Residencia/nacionalidad:** país de nacionalidad separado de país de residencia. Catálogo inicial de 20 países latinoamericanos: Argentina, Bolivia, Brasil, Chile, Colombia, Costa Rica, Cuba, Ecuador, El Salvador, Guatemala, Haití, Honduras, México, Nicaragua, Panamá, Paraguay, Perú, República Dominicana, Uruguay y Venezuela. Bolivia usa sus nueve departamentos; para los demás países departamento/provincia es texto libre de hasta 160 caracteres, sin presentarlo como catálogo oficial validado. Administrador/Jefe autorizado editan; Instructor consulta solo sus datos propios. No se infiere país ni nacionalidad de perfiles históricos.
- **Incorporación:** año entero positivo no futuro; antigüedad = año calendario del servidor menos año de incorporación. Sin año, no disponible. `antiguedad_desde` sigue siendo un dato histórico independiente; incorporación no se expone al Instructor.
- **Secundarias:** catálogo de seis especialidades acordadas; selección múltiple sin duplicados; principal permitida también como secundaria. Administrador edita globalmente; Jefe solo personal activo asignado; Instructor consulta las propias.
- **Cursos:** Administrador crea/edita catálogo común; Administrador/Jefe registran y editan capacitaciones en su ámbito activo. Relación `curso_id` opcional para conservar compatibilidad con registros de nombre libre. Históricos quedan sin enlace automático. El nombre registrado se conserva como instantánea; renombrar catálogo no reescribe registros previos. Instructor consulta sus cursos sin observaciones.
- **Operaciones:** Administrador crea/edita eventos (tipo, lugar, inicio/fin, institución). Fin opcional; si existe no precede al inicio. Administrador/Jefe vinculan participantes activos; Jefe solo su equipo. Instructor consulta solo eventos donde participa y su propia participación, sin listar terceros. Sin borrado físico ni desvinculación en esta entrega; la corrección de vínculos requerirá alcance definido. `experiencia_operaciones` permanece como texto histórico, independiente de las participaciones nuevas.
- **Conservación:** v11 agrega tablas y `capacitaciones.curso_id`; conserva columnas v9 de residencia y añade `perfil_geografico` para ampliar sin reconstruirlas ni alterar sus CHECK. La lectura prioriza el perfil geográfico si existe; en caso contrario utiliza los datos v9. No se rellenan históricos.

## Fase 5A — Cierre del seguimiento operativo

- **Objetivo:** cerrar técnicamente los flujos de notas/historial, cursos/formación personal y asistencia/calendario/PDF, y registrar su aceptación operativa por separado.
- **Alcance:** permisos ya aprobados, registros/correcciones y conservación; revisión móvil/escritorio y PDF operativos. Sin nuevas reglas de puntuación, promedios ni psicometría.
- **Estado actual (2026-10-11):** cierre técnico cumplido. Corregidos selección/carga/guardado de notas, serialización de correcciones simultáneas, formulario oculto y conservación del nombre histórico al editar una capacitación vinculada. Cuatro pruebas nuevas; suite de 68 aprobada y 20 escenarios de interfaz. PDF sintéticos multipágina revisados. Esquema v14 conservado.
- **Pendientes:** aceptación operativa del solicitante sobre el recorrido visible, registro de incidencias si existen. No se declara aceptación institucional ni versionado completo de ediciones de cursos/capacitaciones.
- **Dependencias:** personal activo/asignado, períodos/evaluaciones/asignaciones y datos sintéticos. Permisos y fórmula operativa de asistencia ya acordados; no volver a preguntar esos acuerdos.
- **Cierre verificable:** notas anteriores conservadas, cero válido, rechazo fuera de ámbito/CSRF/psicometría/período cerrado, una sola cadena ante simultaneidad; histórico personal sin observaciones en Instructor; cuatro estados de asistencia y reportes por ámbito; aceptación humana registrada aparte. Evidencias y casos en [cierre de Fase 5A](08_cierre_fase_5a.md).

## Fase 5B — Períodos, configuración y cálculo operativo

- **Objetivo:** implementar las reglas operativas acordadas el 2026-10-11 con resultados reproducibles.
- **Alcance:** Física (dos notas obligatorias promediadas), Académica (nota global con motivo/formación propia), Desempeño (Jefe/Comandante, dos notas obligatorias promediadas). Promedio simple de los tres; asistencia separada y psicometría fuera.
- **Estado actual:** definición acordada y primera entrega implementada: cuatro roles, esquema v15, Comandante/cuenta única, notas por fuente y respaldo académico. Publicación/activación/ciclo anual, cálculo e instantáneas siguen pendientes; ver [reglas y estado](09_reglas_fase_5b.md).
- **Pendientes de implementación:** configuración anual congelada y un solo período ACTIVO; faltantes/cero, dos decimales/mitad hacia arriba solo al final; cierre permitido con incompletos e instantáneas por persona; reapertura motivada sin cambiar configuración y preservando cierres anteriores.
- **Dependencias:** acuerdos confirmados para el prototipo; cierre técnico 5A y prueba de compatibilidad histórica. Aceptación humana/privacidad del piloto no se infiere de aprobar estas reglas. No depende de psicometría.
- **Cierre verificable:** permisos/CSRF por rol/objeto, notas separadas sin suplantación, respaldo de la persona, exactitud y casos aprobados, un activo bajo concurrencia, configuración inmutable, cierres reproducibles sin perder anteriores. Pruebas y revisión responsiva antes de declarar implementación.

## Fase 6 — Psicometría independiente y condicionada

- **Objetivo:** permitir únicamente instrumentos y usos autorizados, sin diagnóstico ni decisiones automáticas.
- **Alcance:** instrumento/versiones, formularios, puntuación, habilitación, intentos y acceso/retención, según [revisión de instrumentos](06_pruebas_psicometricas.md).
- **Estado actual:** tablas y rutas preparatorias, controles que rechazan activación/calificación no autorizada; iniciar intento devuelve formulario no disponible incluso con aprobación en catálogo. No hay reactivos, aplicación ni resultados psicométricos implementados.
- **Pendientes:** aprobación institucional/profesional, derechos/licencia y traducción, idioma/población/modalidad, algoritmo de puntuación, intentos/reinicios, interpretación, acceso y retención de respuestas/resultados.
- **Dependencias:** expediente documental aprobado para cada instrumento y política de privacidad; no basta marcar una fila como APROBADO.
- **Cierre verificable:** expediente revisado; puntuación contrastada con ejemplos oficiales autorizados; intentos anteriores preservados; controles por rol/objeto y retención comprobados; sin respuestas completas en logs ni notas en la vista del Instructor. La conversión a escala institucional requiere aprobación adicional.

## Fase 7 — Reportes separados por contenido

- **Objetivo:** exportar información necesaria con destinatarios y permisos definidos.
- **Alcance:** entrega operativa (asistencia, capacitaciones, seguimiento/notas permitidas) separada de entrega con resultados psicométricos; PDF/Excel individuales y consolidados según alcance aprobado.
- **Estado actual:** PDF operativos de cursos y asistencia implementados y revisados en cierre 5A; Excel, informes consolidados y reportes con resultados psicométricos pendientes.
- **Pendientes:** campos, filtros, destinatarios, exclusiones, auditoría, retención y tratamiento de archivos exportados; diseñar y verificar ambas entregas por separado.
- **Dependencias:** reportes operativos dependen del alcance/permisos aprobados y datos de 5A; promedios solo tras 5B. Reportes psicométricos dependen además de 6 y autorización específica. Los operativos pueden avanzar sin psicometría.
- **Cierre verificable:** por cada entrega, exportaciones cotejadas con datos fuente/filtros; pruebas contra acceso ajeno y filtración de campos; archivos legibles y auditados; no se presentan promedios pendientes ni resultados ficticios; retención y destinatarios documentados.

## Preparación del piloto — cierre básico del prototipo

- **Objetivo:** demostrar operación recuperable y aceptada antes de usar datos institucionales.
- **Alcance:** respaldo/restauración de SQLite y fotos, WSGI/HTTPS, cookies Secure, secretos, operación, privacidad y aceptación institucional.
- **Estado actual:** entorno local existente con Flask de desarrollo; no hay evidencia de aceptación del piloto, restauración ensayada o despliegue institucional preparado.
- **Pendientes:** responsables, aviso/consentimiento aplicable, retención, incidentes, disponibilidad, controles de acceso y limitación de intentos de login; manual operativo y prueba de restauración.
- **Dependencias:** institución responsable y alcance del piloto definidos; entregas funcionales seleccionadas y aceptadas. Psicometría solo si se incluye y se ha cerrado 6; IA no es requisito.
- **Cierre verificable:** restauración ensayada en entorno separado con integridad y archivos comprobados; HTTPS y cookies verificados; secretos externos; ensayo de operación/incidentes; aceptación institucional registrada, sin confundir pruebas locales con autorización de uso real.

## Fase 8 — IA opcional

- **Objetivo:** evaluar una integración futura solo bajo solicitud y autorización específica.
- **Alcance:** modelo validado, adaptador y revisión humana; fuera del cierre básico del prototipo.
- **Estado actual:** IA no implementada; no hay modelo entrenado ni predicciones.
- **Pendientes:** propósito, datos autorizados, model card, validación, sesgos, versiones, acceso y supervisión profesional/ética.
- **Dependencias:** autorización institucional y evidencia de utilidad/validez; privacidad y operación aceptadas. No condiciona reportes operativos ni piloto básico.
- **Cierre verificable:** validación reproducible y límites documentados, salidas trazables/revisables, permisos y supervisión comprobados; nunca decisión automática sobre personas.

## Evidencias del punto de control

- **Histórico, primera entrega 4B (2026-10-10):** 54 pruebas aprobadas en 61,107 s; compilación Python, sintaxis JavaScript, enlaces y diff correctos. Migración local v9 tras respaldo, datos previos de 18 tablas conservados, nuevos campos NULL, quick_check=ok y cero infracciones FK. Formulario/directorio verificados en Chromium en seis escenarios con API simulada y datos sintéticos. Aceptación operativa pendiente.

- **Histórico, Fase 4A (2026-10-10):** alta pendiente por Jefe y autoservicio de correo/foto implementados; 50 pruebas aprobadas en 40,153 s. Tras cerrar la respuesta de foto en la prueba, las 3 de autoservicio pasaron en 1,493 s sin ResourceWarning. Compilación Python, sintaxis JavaScript y diff correctos. Aceptación visual/operativa pendiente; no se declara aceptación institucional.

- **Histórico, Fase 4A parcial (2026-10-10):** alta por Jefe implementada conforme a la decisión del solicitante; 47 pruebas aprobadas en 49,009 s, compilación Python, sintaxis JavaScript, 16 enlaces locales válidos y diff sin errores. En ese punto faltaba decidir los campos del autoservicio; posteriormente se autorizaron correo y foto. No se ejecutó ensayo visual completo.

- **Consolidación documental anterior, 2026-10-10:** inspección de `sicose/management.py`, `evaluations.py`, `dashboard.py`, `db.py`, `schema.sql`, plantillas y JavaScript; suite `python -m unittest discover -s tests -v`: **44 pruebas, todas aprobadas en 18,734 s**, usando el Python de `.venv` y bases aisladas. Esto no acredita funcionalidades futuras ni ensayo visual completo.
- **Histórico:** 42 pruebas en revisión/migración v7 y 43 en v8, registradas el 2026-09-29 en [HISTORY](../HISTORY.md). El resultado comunicado de 44 pruebas en 19,215 s el 2026-10-10 pertenece a la revisión anterior; no es el tiempo de esta ejecución.
- La integridad y recuentos de la base local descritos en el historial son evidencias históricas; la revisión documental no ejecutó migración ni modificó la base local; la migración actual v9 tiene su propia evidencia arriba.
- Los cambios locales preexistentes en asistencia HTML/CSS/JS y `tests/test_app.py` se preservan; su fecha de implementación no se deduce de esta revisión documental.

## Decisiones abiertas y requisitos previos

1. Institución responsable, marco de privacidad del piloto, minimización, aviso/consentimiento, destinatarios y plazos de retención.
2. Política definitiva de colisiones de código; autoservicio ya definido exclusivamente para correo y foto, sin cambios de identidad/código. La aprobación administrativa de solicitudes públicas ya existe.
3. Ampliaciones futuras del catálogo territorial y reglas de corrección de vínculos operativos, si se solicitan. El alcance de perfil, catálogo de cursos, operaciones y sus permisos ya fue confirmado para esta entrega; no volver a preguntar esas decisiones.
4. Faltantes, redondeo, pesos/componentes, quién publica versiones y cierre/reapertura de períodos. No considerar los pesos de ejemplo aprobados.
5. Expedientes psicométricos, población/modalidad, derechos e idioma, puntuación, intentos, interpretación, accesos y retención.
6. Campos/destinatarios de reportes operativos y psicométricos por separado; permisos de exportación y conservación fuera del sistema.
7. Destino de despliegue, responsables de operación, respaldo, HTTPS, incidentes y aceptación del piloto.

Ya están acordados el prototipo local en español con datos sintéticos, stack, roles, bajas lógicas, identidad visual, código con fecha completa, especialidad principal, cuatro estados de asistencia y campos de operación. El seed administrativo local idempotente ya está implementado; no es una pregunta abierta. No se asumen población, política institucional, pesos aprobados ni reglas de puntuación.

## Riesgos a controlar

Acceso o exportación excesivos; conservación indefinida; pérdida de historial; cálculos no reproducibles; uso de instrumentos fuera de población/licencia; confundir esquema preparatorio con funcionalidad; usar datos reales en demo; y extender el alcance opcional de IA al cierre básico. Cada entrega debe aportar pruebas y evidencia de aceptación proporcionadas a su alcance.

### Evidencia histórica de Fase 4B — Especialidades secundarias (2026-10-10)

Implementadas en v10 como conjunto opcional del catálogo de seis especialidades ya acordado. Se permite que la principal figure también como secundaria; no se permiten duplicados dentro del conjunto. Administrador consulta/edita globalmente; Jefe consulta/edita únicamente personal activo asignado; Instructor consulta solo sus propias especialidades en Mi perfil, sin editar. La edición se realiza en el modal de perfil; el autoservicio sigue limitado a correo y foto. Los perfiles anteriores quedan sin secundarias, sin inferencias.

Verificación: 55 pruebas aprobadas en 24,331 s, compilación Python, sintaxis JavaScript y diff correctos. Migración v10 aplicada dos veces tras respaldo: 18 tablas anteriores conservadas, quick_check=ok y cero infracciones FK. Fase 4B sigue parcial: pendientes de respuesta las consultas sobre catálogo/consulta de cursos, gestión/visibilidad de operaciones y alcance de nacionalidad/otros países. No se han asumido esas decisiones ni la aceptación institucional.

## Evidencia de cierre técnico 4B — 2026-10-10

58 pruebas aprobadas en 62,893 s con bases aisladas. Migración local v11 tras respaldo: 19 tablas anteriores preservadas al comparar todas sus columnas previas; curso_id histórico NULL; inicialización repetida, quick_check=ok y cero infracciones FK. Compilación Python, sintaxis JavaScript, enlaces locales y diff verificados. La aceptación operativa/institucional no se deduce de estas pruebas.

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


Actualización de continuidad (2026-10-10, v14): revisión del perfil/directorio de 4B con grados aprobados, consulta completa en modal y fecha de incorporación única (cálculo por diferencia de años aprobado, sin años completos cumplidos). Alta administrativa Activo/Inactivo; solicitudes pendientes con datos geográficos/foto y grado público reservado. Implementación y 64 pruebas verificadas; históricos preservados. La siguiente entrega sigue siendo aceptación/revisión integral del seguimiento de Fase 5A; esta revisión no completa 5B ni los requisitos de privacidad/retención y aceptación institucional del piloto.


Punto vigente del 2026-10-11: 5A cerrada técnicamente según [evidencias](08_cierre_fase_5a.md); aceptación operativa humana pendiente. Siguiente entrega: definición de reglas 5B, sin anticipar pesos, faltantes ni redondeo institucional. Los puntos de control anteriores conservan su fecha y contexto.


Definición 5B en curso (2026-10-11): tres componentes manuales y asistencia separada; períodos anuales con uno activo y control administrativo del ciclo confirmados. Pendientes pesos/faltantes/precisión/versiones/instantáneas. Decisiones y propuestas sin implementación en [reglas 5B](09_reglas_fase_5b.md).


Decisiones adicionales 5B (2026-10-11): faltantes impiden calcular sin sustituirlos por cero/redistribuir; cero registrado válido; notas nuevas hasta dos decimales y resultado final con dos decimales, mitad hacia arriba sin redondeos intermedios. Escala de cada componente 0–100 puntos; combinación aún por aclarar, sin adoptar ponderaciones. Consultas y casos en [reglas 5B](09_reglas_fase_5b.md).


Reglas 5B adicionales confirmadas (2026-10-11): promedio simple de Física/Académica/Desempeño; configuración congelada durante período activo. Física promedia dos notas obligatorias por gestión; Académica es nota global manual respaldada por cursos/capacitaciones; Desempeño involucra Jefe y Comandante y falta definir su combinación. Comandante requiere rol propio limitado a grupo; no existe en código y estructura/permisos aún se consultan. Sin implementación ni cambios de esquema v14. Estado detallado en [reglas 5B](09_reglas_fase_5b.md).


Definición 5B ampliada (2026-10-11): Desempeño promedia notas independientes obligatorias de Jefe y Comandante. Académica: Jefe registra/corrige y Administrador puede corregir con historial. Único grupo SBRAB, un cargo Comandante cuyo nombre de responsable puede cambiar; no diseñar varios grupos ni asignaciones multigrupo. Pendientes acceso del nuevo rol, evidencia Académica y cierre/instantáneas. Sin implementación; fórmulas/casos en [reglas 5B](09_reglas_fase_5b.md).


Punto vigente 5B (2026-10-11): reglas acordadas; sustituye consultas/propuestas anteriores recogidas en este plan. Cierre con incompletos y cada instantánea conservada, respaldo académico obligatorio y Comandante de único SBRAB limitado a consulta/Desempeño, sin observaciones ajenas. Próxima entrega: implementación de rol/fuentes/respaldo, luego períodos/configuración, cálculo y cierres. Detalle en [reglas definitivas para implementación](09_reglas_fase_5b.md).


Punto vigente 5B (2026-10-11, v15): primera entrega implementada y verificada — rol Comandante/cargo único, fuentes separadas, respaldo académico y permisos. 73 pruebas y ocho escenarios UI; históricos preservados. No cerrada 5B: siguiente entrega ciclo de períodos/configuración/publicación/congelación y activo único, seguida de cálculo y cierres. Ver [reglas y estado](09_reglas_fase_5b.md).
