# 05. Plan de desarrollo

Estado revisado: **2026-10-14; SQLite v22**. Fases 0–3 y 4A/4B/5A implementadas técnicamente para el prototipo local; aceptación operativa de 4A/4B/5A pendiente. **5B parcial**: gestiones/configuración, habilitación, notas manuales auditadas y formación individual implementadas; 5B.1–5B.4 implementadas técnicamente; aceptación operativa/institucional pendiente. Fase 7 parcial con PDF de cursos, asistencia y evaluaciones; Fase 6 condicionada y Fase 8 opcional sin implementación. Piloto pendiente.

Este resumen y los alcances vigentes siguientes prevalecen sobre los puntos de control históricos al final. Los acuerdos del 2026-10-12 están en [reformulación](10_reformulacion_evaluaciones.md) y [formación v18](11_cursos_formacion.md). El diagnóstico estructural y documental está en [revisión del proyecto](12_revision_proyecto.md).

## Numeración y orden de entregas

Se conservan las fases históricas 0 (especificación), 1/1A (base ejecutable), 2 (persistencia/autenticación) y 3 (diseño/dashboards). Las antiguas 4.1 y 4.3 describen gestión administrativa y fotos/recuperación ya implementadas; 4.2 se continúa en 4A. El antiguo rótulo 4B para períodos/ponderaciones se reubica en 5B; desde esta revisión **4B significa ampliación del perfil**. No se reescribe el historial funcional ni se atribuyen fechas nuevas a cambios locales.

Orden recomendado: consolidación documental → 4A → 4B → 5A → 5B. Fase 6 es independiente y condicionada. Los reportes operativos de Fase 7 pueden avanzar sin Fase 6 si tienen alcance y permisos definidos. La preparación del piloto tiene su propia aceptación. Fase 8 es opcional y queda fuera del cierre básico. No se asignan porcentajes ni fechas de entrega.

## Consolidación documental — revisión previa

- **Objetivo:** disponer de una línea base comprobable para continuar el prototipo.
- **Alcance:** README, continuidad de AGENTS, HISTORY, plan y correcciones técnicas necesarias; sin cambiar código, permisos, esquema o entorno.
- **Estado actual:** revisión de rutas, decoradores, esquema, plantillas, JavaScript y pruebas; cambios funcionales locales previos preservados.
- **Pendientes:** mantener la documentación al completar cada entrega futura; esta revisión no cierra capacidades funcionales pendientes.
- **Dependencias:** estado de Git y evidencias del repositorio; acuerdos existentes de roles y privacidad.
- **Cierre verificable:** operaciones documentadas coinciden con rutas y pantallas; enlaces locales válidos; evidencias fechadas y separadas del historial; decisiones pendientes explícitas; `git diff --check` sin errores.

## Fase 4A — Gestión por rol y autoservicio

- **Objetivo:** completar la gestión de personal prevista por rol.
- **Alcance:** alta de Instructor Voluntario por Jefe de Personal y edición del perfil propio por Instructor Voluntario, conservando historial y autorización por objeto.
- **Estado actual:** Administrador lista, crea, edita y desactiva Jefes de Personal e Instructores Voluntarios, aprueba/rechaza solicitudes, asigna personal y restablece claves. El Jefe único consulta activos/inactivos globales SBRAB, edita/desactiva activos y registra solicitudes pendientes con aprobación/rechazo administrativo; la asignación histórica no delimita autorización. El Instructor ve estados/avance propios sin notas ni observaciones; tiene formulario Mi perfil y API para actualizar exclusivamente correo y foto propios, según alcance autorizado el 2026-10-10.
- **Pendientes:** aceptación visual/operativa de ambos flujos; se conserva rechazo de colisiones hasta definir política definitiva; no se habilitan cambios de identidad/código desde autoservicio. Correo y foto fueron autorizados y están implementados. El alta por Jefe sigue siendo solicitud pendiente; desde el 2026-10-12 su alcance es global, conservando vínculos históricos.
- **Dependencias:** decisiones confirmadas: altas por Jefe pendientes de aprobación administrativa; autoservicio limitado a correo y foto. Se mantienen los roles y la regla de código acordados.
- **Cierre verificable:** pruebas de altas válidas y denegadas por rol/ámbito, edición exclusivamente propia, rechazo de campos administrativos, CSRF, cuentas pendientes/inactivas sin acceso, conservación del historial y ausencia de notas/observaciones en respuestas al Instructor.

## Fase 4B — Perfil, cursos y operaciones relacionados

- **Objetivo:** completar información del perfil y relaciones de formación/participación sin inventar datos históricos.
- **Alcance implementado:** residencia y nacionalidad diferenciadas, incorporación/antigüedad, especialidades secundarias, catálogo común de cursos y relación opcional desde capacitaciones, eventos y participaciones de operaciones.
- **Cierre técnico histórico (2026-10-10):** esquema v11 en esa entrega; base actual v21. Especialidad principal resuelta en v8; residencia/incorporación en v9; secundarias en v10; cursos, operaciones y geografía ampliada en v11. Pendiente aceptación operativa del solicitante.
- **Pendientes:** aceptación del recorrido funcional; ampliar países o incorporar catálogos territoriales según necesidad futura. Institución, minimización/retención y uso de datos reales siguen siendo requisitos del piloto.
- **Dependencias:** permisos confirmados por el solicitante y migración aditiva con respaldo. No depende de psicometría ni cálculos oficiales.
- **Cierre verificable:** permisos por rol/objeto, CSRF, fechas ordenadas, duplicados rechazados, consulta propia sin observaciones, provincias conservadas en edición, históricos e IDs preservados; inicialización repetida con integridad SQLite; pruebas y revisión responsiva. Evidencias en el punto de control.

### Reglas confirmadas e implementación

- **Residencia/nacionalidad:** país de nacionalidad separado de país de residencia. Catálogo inicial de 20 países latinoamericanos: Argentina, Bolivia, Brasil, Chile, Colombia, Costa Rica, Cuba, Ecuador, El Salvador, Guatemala, Haití, Honduras, México, Nicaragua, Panamá, Paraguay, Perú, República Dominicana, Uruguay y Venezuela. Bolivia usa sus nueve departamentos; para los demás países departamento/provincia es texto libre de hasta 160 caracteres, sin presentarlo como catálogo oficial validado. Administrador/Jefe autorizado editan; Instructor consulta solo sus datos propios. No se infiere país ni nacionalidad de perfiles históricos.
- **Incorporación:** año entero positivo no futuro; antigüedad = año calendario del servidor menos año de incorporación. Sin año, no disponible. La fecha canónica sincroniza fecha_incorporacion, ano_incorporacion y antiguedad_desde; históricos incompletos se conservan sin inferir fechas. El Instructor consulta incorporación propia; no la edita.
- **Secundarias:** catálogo de seis especialidades acordadas; selección múltiple sin duplicados; principal permitida también como secundaria. Administrador edita globalmente; Jefe sobre personal activo global SBRAB; Instructor consulta las propias.
- **Cursos:** Administrador/Jefe crean/editan catálogo común; Administrador/Jefe registran y editan capacitaciones en su ámbito activo. Relación `curso_id` opcional para conservar compatibilidad con registros de nombre libre. Históricos quedan sin enlace automático. El nombre registrado se conserva como instantánea; renombrar catálogo no reescribe registros previos. Instructor consulta sus cursos sin observaciones.
- **Operaciones:** Administrador crea/edita eventos (tipo, lugar, inicio/fin, institución). Fin opcional; si existe no precede al inicio. Administrador/Jefe vinculan participantes activos; Jefe sobre activos globales SBRAB. Instructor consulta solo eventos donde participa y su propia participación, sin listar terceros. Sin borrado físico ni desvinculación en esta entrega; la corrección de vínculos requerirá alcance definido. `experiencia_operaciones` permanece como texto histórico, independiente de las participaciones nuevas.
- **Conservación:** v11 agrega tablas y `capacitaciones.curso_id`; conserva columnas v9 de residencia y añade `perfil_geografico` para ampliar sin reconstruirlas ni alterar sus CHECK. La lectura prioriza el perfil geográfico si existe; en caso contrario utiliza los datos v9. No se rellenan históricos.

## Fase 5A — Cierre del seguimiento operativo

- **Objetivo:** cerrar técnicamente los flujos de notas/historial, cursos/formación personal y asistencia/calendario/PDF, y registrar su aceptación operativa por separado.
- **Alcance:** permisos ya aprobados, registros/correcciones y conservación; revisión móvil/escritorio y PDF operativos. Sin nuevas reglas de puntuación, promedios ni psicometría.
- **Cierre técnico histórico (2026-10-11):** cumplido. Corregidos selección/carga/guardado de notas, serialización de correcciones simultáneas, formulario oculto y conservación del nombre histórico al editar una capacitación vinculada. Cuatro pruebas nuevas; suite de 68 aprobada y 20 escenarios de interfaz. PDF sintéticos multipágina revisados. Esquema v14 conservado.
- **Pendientes:** aceptación operativa del solicitante sobre el recorrido visible, registro de incidencias si existen. No se declara aceptación institucional ni versionado completo de ediciones de cursos/capacitaciones.
- **Dependencias:** personal activo en ámbito global SBRAB, períodos/evaluaciones/asignaciones y datos sintéticos. Permisos y fórmula operativa de asistencia ya acordados; no volver a preguntar esos acuerdos.
- **Cierre verificable:** notas anteriores conservadas, cero válido, rechazo fuera de ámbito/CSRF/psicometría/período cerrado, una sola cadena ante simultaneidad; histórico personal sin observaciones en Instructor; cuatro estados de asistencia y reportes por ámbito; aceptación humana registrada aparte. Evidencias y casos en [cierre de Fase 5A](08_cierre_fase_5a.md).

## Fase 5B — Evaluaciones por gestión, cálculo y publicación

- **Objetivo:** completar resultados reproducibles y su ciclo de publicación/cierre según los acuerdos del 2026-10-12.
- **Implementado:** tres roles operativos, Jefe único global, Comandante externo; gestiones anuales creadas/editadas/retiradas por Administrador/Jefe, configuración/publicación del ciclo y activación de regla v2 por Administrador, edición de borrador con revisión, configuración congelada/activo único; habilitación individual e historial, notas manuales por cinco fuentes, cursos y participaciones/finalización auditadas (v18). Publicar configuración no publica notas.
- **Reglas acordadas:** Física promedia dos pruebas; Académica suma puntos enteros por finalización personal en su año, una sola imputación y tope 100 conservando detalle; Desempeño promedia Jefe/Comandante. Resultado conjunto: igual importancia de tres componentes y dos decimales finales, mitad hacia arriba, sin redondeos intermedios. Pendiente sin nota no se convierte automáticamente en cero.
- **Compatibilidad:** conservar notas manuales, formación antigua y configuraciones PROMEDIO_TRES_V1; establecer tratamiento explícito para reglas nuevas sin alterar versiones congeladas ni adoptar históricos automáticamente.
- **Dependencias:** cierre técnico 5A, reglas confirmadas, pruebas de compatibilidad; aceptación operativa/institucional aparte. No depende de psicometría.

### Entregas de la reformulación sin renumerar las fases

| Entrega | Alcance y estado | Cierre verificable |
|---|---|---|
| 5B.1 Física programada | **Implementada técnicamente v19.** Dos fechas comunes anuales, reprogramación individual extraordinaria y No cumplida=0 confirmado por Administrador/Jefe. | Historial de fechas/actores; pendiente distinto de cero; reprogramar conserva cero hasta cumplimiento/corrección; permisos, concurrencia y límites comprobados. |
| 5B.2 Acumulación y cálculos | **Implementada técnicamente v20, opt-in explícito.** Imputación académica única, detalle/tope 100, promedios físicos/desempeño/conjunto y tratamiento explícito de configuraciones históricas. | Casos exactos de cero/faltantes/tope/cambio de año/corrección y redondeo final; resultados trazables a fuentes/versiones; sin duplicaciones. |
| 5B.3 Publicación de notas | **Implementada técnicamente v21.** Administrador/Jefe publican/republican físicas y cursos/acumulado académico propios visibles al Instructor. | Corrección conserva versión publicada anterior y fecha hasta republicar; Desempeño/resultado conjunto ocultos también en API/PDF; autorización por persona y concurrencia. |
| 5B.4 Cierre y reapertura | Implementada técnicamente en v22: Administrador cierra/reabre con motivo, incompletos identificados e instantáneas de cada cierre. | Configuración intacta, cierres anteriores reproducibles, permisos y bloqueo de escritura verificados; aceptación operativa pendiente. [Detalle](16_cierres_reaperturas.md). |

5B.1 implementada técnicamente en v19; ver [reglas, compatibilidad y evidencia](13_programacion_fisica.md). 5B.2 implementada técnicamente en v20; ver [gestiones y cálculos](14_calculos_y_gestiones.md). 5B.3 implementada en v21; ver [publicación](15_publicacion_notas.md). 5B.4 sigue pendiente. Las entregas v15–v18 conservan su historia.

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
- **Estado actual:** PDF operativos de cursos, asistencia y evaluaciones implementados; el PDF de evaluaciones resume habilitación/avance/notas autorizadas, sin resultado conjunto calculado. Excel, reportes finales de resultados y reportes psicométricos pendientes.
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

## Evidencia vigente

Ver [revisión del 2026-10-13](12_revision_proyecto.md) para comprobaciones actuales. Las cifras y estados siguientes son históricos y no sustituyen los alcances vigentes anteriores.

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
4. Implementar las reglas ya confirmadas de componentes/faltantes/redondeo, publicación/republicación y cierre/reapertura; resolver explícitamente compatibilidad de configuraciones históricas. No volver a consultar los acuerdos documentados; distinguirlos de aprobación institucional.
5. Expedientes psicométricos, población/modalidad, derechos e idioma, puntuación, intentos, interpretación, accesos y retención.
6. Campos/destinatarios de reportes operativos y psicométricos por separado; permisos de exportación y conservación fuera del sistema.
7. Destino de despliegue, responsables de operación, respaldo, HTTPS, incidentes y aceptación del piloto.

Ya están acordados el prototipo local en español con datos sintéticos, stack, roles, bajas lógicas, identidad visual, código con fecha completa, especialidad principal, cuatro estados de asistencia y campos de operación. El seed administrativo local idempotente ya está implementado; no es una pregunta abierta. No se asumen población ni política institucional aprobadas. Las reglas de puntuación del prototipo están acordadas; no acreditan aprobación institucional.

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

- Administrador consulta/registra/corrige asistencia; Jefe sobre personal activo global SBRAB. La llamada muestra nombre del responsable autenticado, gestión anual de la fecha seleccionada y fecha; conserva actividad obligatoria. Los cuatro estados exactos son Asiste, Atraso, Permiso y Falta. Llamada nueva inicia todas las filas en Falta; al elegir fecha/actividad existente se cargan sus estados guardados para corregirlos.
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


Punto vigente 5B (2026-10-11, v15): primera entrega implementada y verificada — rol Comandante/cargo único, fuentes separadas, respaldo académico y permisos. 73 pruebas y ocho escenarios UI; históricos preservados. Punto histórico v15: el ciclo/configuración todavía estaba pendiente; la entrega v16 siguiente lo implementa. No cerrada 5B. Ver [reglas y estado](09_reglas_fase_5b.md).


## Segunda entrega de Fase 5B — 2026-10-11 (v16)

Administrador dispone de **Períodos y configuración**: crea borradores anuales enero–diciembre, configura cinco fuentes mediante modal y publica/activa en una transacción. La revisión del borrador evita sobrescribir cambios concurrentes. Publicación exige fuentes completas con evaluaciones manuales activas de categoría compatible; dos fuentes de la misma categoría pueden usar la misma evaluación de catálogo, manteniendo sus notas independientes. Configuración versión 1 con regla PROMEDIO_TRES_V1 (igual importancia de los tres componentes); no habilita porcentajes arbitrarios ni cálculo aún.

La publicación congela fuentes, nombres/códigos/categorías, autor y fecha UTC. Cambiar el catálogo después no reescribe esas referencias. Un solo período puede activarse bajo concurrencia, también protegido por triggers. No se cierran otros períodos automáticamente. Notas/correcciones 5B requieren período ACTIVO y configuración PUBLICADA; configuración_id/evaluacion_id se resuelven en servidor, sin aceptar esos valores del cliente. La API de calificación anterior no registra notas en períodos configurados 5B; los registros anteriores siguen consultables.

Migración v16 aditiva: configuraciones_5b y fuentes_configuracion_5b, dos referencias nullable en notas_operativas y restricciones. Respaldo local previo, 26 tablas anteriores preservadas, inicialización repetida, quick_check=ok y cero infracciones FK. Períodos y notas históricas sin modificación ni adopción; referencias anteriores NULL. La base local no tenía períodos ACTIVO; una base histórica que sí los tenga bloqueará nuevas activaciones hasta un tratamiento explícito en la entrega de cierre, sin alterar sus estados al migrar.

Verificación actual: **77 pruebas aprobadas en 86,620 s** (bases aisladas), incluyendo publicación concurrente, revisiones obsoletas, fuentes incompletas/categoría inválida, congelación, permisos/CSRF y preservación v15. Ocho escenarios Chromium con API simulada a 360/1447 px: publicación y modal administrativo, notas por los tres roles y bloqueo de edición sin configuración publicada; sin desborde ni errores JavaScript. Compilación Python, sintaxis de los tres JavaScript, enlaces locales y git diff --check correctos.

Pendientes: cálculo provisional exacto/faltantes/redondeo, cierre y reapertura motivada con cada instantánea preservada, aceptación operativa e institucional/privacidad antes del piloto. **No se declara cerrada Fase 5B.** Siguiente entrega: cálculo provisional vinculado a configuración y últimas notas válidas, separado de asistencia y psicometría.


## Reglas nuevas acordadas — 2026-10-12

La [reformulación de evaluaciones y formación](10_reformulacion_evaluaciones.md) sustituye acuerdos anteriores incompatibles: Comandante sin cuenta operativa propia, Jefe único sin asignaciones necesarias, publicación de notas físicas/académicas al Instructor, No cumplida física con cero y formación acumulativa en enteros. Primera entrega de autorización/tabla/habilitación/PDF implementada en v17; el resto queda pendiente según la actualización siguiente. Configuraciones/históricos anteriores se conservan; no aplicar las reglas nuevas retrospectivamente. Límite/imputación académica, alcance global del Jefe y publicación/republicación quedaron confirmados; ver la actualización siguiente. La próxima entrega se reordena conforme a ese documento; las verificaciones del 2026-10-11 permanecen históricas.


## Primera entrega de la reformulación — 2026-10-12 (v17)

Jefe único activo con alcance global sin filtro de asignación; Comandante retirado del acceso operativo, conservado solo en datos históricos. Desempeño del Comandante transcrito por Administrador/Jefe con nombre del evaluador y autor de transcripción separados. Tabla Evaluaciones por gestión y consulta modal de activos/inactivos, habilitación individual con historial y notas 5B bloqueadas al deshabilitar; PDF administrativo con carimbo SBRAB. Instructor consulta habilitación/estado/avance por gestión, todavía sin notas publicadas.

Acuerdos complementarios: Académica acumulará puntos enteros con tope 100; puntos individuales ajustables, gestión de finalización personal y cómputo único. Administrador/Jefe publicarán; después de corrección se conservará la versión publicada anterior hasta republicar. **Cursos con puntos, programación/reprogramación física, No cumplida=0, acumulación y publicación/republicación aún pendientes.** El flujo manual académico anterior y configuraciones congeladas no se convierten automáticamente. Psicometría continúa bloqueada; Fase 5B no cerrada.

Evidencia vigente: 81 pruebas aprobadas en 45,711 s; ocho escenarios UI, PDF sintético de cinco páginas, compilación/sintaxis/enlaces/diff correctos. Migración v17 tras respaldo, 28 tablas anteriores preservadas, inicialización repetida, quick_check=ok, FK=0. Detalles en [reglas y estado](10_reformulacion_evaluaciones.md). Siguiente entrega: cursos con puntaje y asignación/finalización individual con historial.


## Cursos y formación personal implementados — 2026-10-12 (v18)

Administrador/Jefe registran/editar catálogo con puntaje entero 0–100, fechas/entidad obligatorias en cursos nuevos y estado automático de Bolivia. Asignación personal/múltiple sin duplicados, finalización independiente con puntaje y fecha explícitos, correcciones con actor/fecha/motivo/revisión y valores anteriores preservados. Edición del catálogo no reescribe datos capturados al asignar. Inactivos solo consulta/historial. Instructor ve sus estados y formación histórica, sin puntajes hasta publicación; Dashboard/seguimiento enlazan las participaciones. PDF de catálogo filtra estado calculado. Histórico sin datos completos permanece intacto y sin puntos inferidos.

Verificación vigente: 86 pruebas aprobadas en 87,375 s; 12 escenarios UI, sin desborde/errores; migración local tras respaldo e inicialización repetida preservando 29 tablas, quick_check=ok y FK=0. Compilación, sintaxis, enlaces y diff correctos. Detalles en [reglas y entrega v18](11_cursos_formacion.md). Pendientes acumulado académico hasta 100, físicas/reprogramación/No cumplida, publicación/republicación y cierres; no se declara cierre 5B ni del piloto.


Ejecución de 5B.1 — 2026-10-13: 93 pruebas aprobadas en 195,680 s, 20 escenarios UI sintéticos, compilación/sintaxis/enlaces/diff correctos; migración respaldada v19, 32 tablas previas preservadas, inicialización repetida, quick_check=ok y FK=0. [Detalle y límites](13_programacion_fisica.md). 5B.2–5B.4 pendientes; sin aceptación operativa/institucional ni cierre 5B.


Ejecución de 5B.2 — 2026-10-13: Gestiones compartidas Administrador/Jefe con baja lógica, activación anual separada de habilitación personal y menú ordenado. Cálculos provisionales exactos mediante opt-in ACUMULADO_TRES_V2; sin formación finalizada queda pendiente y fuente necesaria desactivada deja No disponible. 104 pruebas aprobadas en 158,822 s y 36 escenarios UI sintéticos. Migración respaldada v20: 35 tablas previas preservadas, inicialización repetida, quick_check=ok y FK=0. [Detalle y compatibilidad](14_calculos_y_gestiones.md). Próxima entrega 5B.3; 5B.4 y aceptación operativa/institucional pendientes.


Ejecución de 5B.3 — 2026-10-13: publicación/republicación parcial con firma/revisión y versiones, ocultación por deshabilitación/baja confirmada, proyecciones propias sin Desempeño/conjunto ni fuentes privadas. 114 pruebas aprobadas en 123,012 s, 16 escenarios UI sintéticos y migración respaldada v21 preservando 39 tablas previas, inicialización repetida, quick_check=ok y FK=0. [Detalle](15_publicacion_notas.md). Próxima entrega 5B.4; sin cierre 5B ni aceptación operativa/institucional.

Ejecución de 5B.4 — 2026-10-14: cierre/reapertura administrativa motivada e instantáneas por persona/versiones; incompletos confirmados, configuración intacta, bloqueo académico del año anterior/nuevo y resultado cerrado conservado. Suite completa 127 pruebas aprobadas en 257,841 s; diez específicas aprobadas en 12,635 s tras ampliar la comprobación de habilitación heredada. Ocho escenarios visuales sintéticos, ambos roles/temas y 360/1447 px. Migración respaldada v22, 40 tablas previas preservadas, inicialización repetida, quick_check=ok, FK=0; tres tablas nuevas vacías. [Alcance y compatibilidad](16_cierres_reaperturas.md). Las cuatro entregas están implementadas técnicamente; no se declara cerrada Fase 5B ni resuelta la aceptación operativa/institucional.
