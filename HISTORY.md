# Historial de cambios y configuraciones — SICOSE
Las entradas describen el estado y las verificaciones de cada entrega en su fecha. Los acuerdos posteriores sustituyen los anteriores; el estado actual se consolida en [README.md](README.md) y [AGENTS.md](AGENTS.md). Las cifras históricas de pruebas no son ejecuciones nuevas.


## 2026-10-10 — Acciones visibles en directorios

- Editar, restablecer contraseña y desactivar se apilan verticalmente en una columna de acciones fija al borde derecho del contenedor. Los botones ocupan el ancho de la celda y permiten ajuste de texto; la columna permanece visible durante el desplazamiento horizontal.
- Aplicado a directorios de Instructores Voluntarios y Jefes de Personal, sin cambiar permisos ni la operación de desactivación.
- Seis escenarios en Chromium (tres vistas, 360/1447 px), con API simulada, comprobaron botones completos en ambos extremos del desplazamiento. git diff --check sin errores; no se reejecutó la suite backend por este ajuste de presentación.

## 2026-10-10 — Edición de perfiles en modal

- Se movieron formularios de edición de perfiles y restablecimiento de contraseña fuera de las filas de los directorios, a un diálogo nativo centrado y responsivo. La tabla conserva su altura; formulario con dos columnas en escritorio y una en móvil, desplazamiento interno y cancelación/Escape.
- Errores visibles dentro del modal; guardado correcto cierra y actualiza el listado. Se conservan campos, rutas, permisos, datos y cambios locales existentes.
- Sintaxis JavaScript y git diff --check correctos. Seis escenarios en Chromium con API simulada/datos sintéticos verificaron apertura, tabla estable, límites móviles, Escape/foco, errores y guardado. No se reejecutó la suite backend para este ajuste de interfaz.

## 2026-10-10 — Primera entrega 4B: residencia e incorporación, esquema v9

- El solicitante confirmó país/departamento de residencia (Bolivia con nueve departamentos inicialmente), año de incorporación y antigüedad por diferencia de años calendario del servidor. Administrador/Jefe autorizado consultan/editan, Jefe solo personal activo asignado; Instructor no recibe esos campos ni los edita.
- La migración aditiva v9 añade campos opcionales NULL a voluntarios; no infiere datos ni modifica antiguedad_desde. Hay captura en alta administrativa/solicitudes del Jefe, validación compartida, edición/directorio y cálculo no persistido. Registro público y autoservicio del Instructor conservan su alcance.
- Verificación final: **54 pruebas aprobadas en 61,107 s**, compilación Python, sintaxis JavaScript, enlaces y diff correctos. La primera ejecución del conjunto previo detectó una expectativa de versión 8; se actualizó a 9 y la suite final pasó. Se añadió prueba de migración v8→v9 idempotente, preservación, catálogos, límites de años y permisos.
- Base local migrada tras respaldo SQLite en .tmp ignorado por Git: datos previos conservados en 18 tablas, nuevos campos NULL, quick_check=ok y cero infracciones FK; se conservaron entorno/configuración e historial.
- Formularios/directorio pasaron seis escenarios en Chromium (Administrador/Jefe y 360/768/1447 px) con datos sintéticos y API simulada. El ensayo confirma catálogos dependientes, edición y ausencia de desbordamiento; no sustituye aceptación operativa. Nacionalidad, otros países, especialidades secundarias y relaciones de cursos/operaciones siguen pendientes.

## 2026-10-10 — Corrección del ancho responsivo de pantallas

- Se reprodujeron en Chromium los espacios laterales del dashboard con menú plegado y se corrigió el contenedor compartido para ocupar todo el ancho disponible. Cabecera/contenido conservan márgenes pequeños; acceso, registro y errores dejan de limitarse a un bloque central estrecho.
- Se corrigieron mínimos de rejilla en Asistencias para impedir desbordamiento del documento en móvil y con barra lateral expandida. Se conservaron los cambios previos del formulario/tabla, colores y navegación.
- Verificación: 135 comprobaciones de ancho/desbordamiento con Chromium sobre 14 pantallas renderizadas por Flask, en cinco anchos y variantes de menú donde aplica; todas correctas. Inspección de captura del dashboard oscuro plegado y `git diff --check` sin errores. No se reejecutó la suite funcional para este ajuste CSS ni se modificaron backend, permisos o base local.

## 2026-10-10 — Fase 4A: autoservicio de correo y foto

- El solicitante autorizó exclusivamente correo y foto para el perfil propio. Se añadió Mi perfil a la navegación del Instructor Voluntario y `PATCH /api/instructor-voluntario/perfil`, sin identificador de persona recibido desde el cliente.
- El servidor limita campos, exige rol/sesión activa y CSRF, valida correo y foto, conserva otros datos y rechaza cambios de identidad, código, especialidad, antigüedad, rol, estado, asignación, notas u observaciones. Correo y foto se guardan en una transacción; fallos por duplicado o imagen inválida no dejan actualizaciones parciales ni fotos nuevas huérfanas.
- Verificación: **50 pruebas aprobadas en 40,153 s**. Se corrigió un ResourceWarning de la prueba de lectura de foto cerrando la respuesta; después pasaron las **3 pruebas de autoservicio en 1,493 s**, sin ese aviso. Compilación Python, sintaxis JavaScript, enlaces locales y `git diff --check` correctos. Sin ensayo visual completo en navegador.
- Los dos flujos acordados de 4A están implementados y verificados mediante pruebas HTTP. Sigue pendiente aceptación visual/operativa; no se declara aceptación institucional. La política definitiva de colisiones continúa abierta, con rechazo preventivo vigente. Esquema v8 y base local conservados; sin recrear entorno/configuración.

## 2026-10-10 — Fase 4A parcial: solicitudes de alta por Jefe

- Se acordó que el Jefe registre solicitudes pendientes, asignadas a su equipo, con aprobación/rechazo exclusivo del Administrador. El formulario y `POST /api/jefe-personal/instructores-voluntarios` implementan ese flujo; el servidor fija la asignación y rechaza campos administrativos.
- La aprobación conserva la asignación previa si no se envía una nueva y comprueba que el Jefe siga activo. La bandeja administrativa muestra la asignación seleccionada. El alta administrativa directa conserva su comportamiento.
- Se corrigió el alcance del directorio, edición/desactivación y lectura de fotos por Jefe para admitir únicamente personal activo asignado; solicitudes pendientes e inactivos quedan fuera. No se elimina historial.
- Se reutiliza el esquema v8; no se migró ni alteró la base local o el entorno. Se preservaron cambios funcionales previos en asistencia y pruebas.
- Verificación final: **47 pruebas aprobadas en 49,009 s** con `python -m unittest discover -s tests -v`; compilación Python y sintaxis JavaScript correctas, 16 enlaces locales válidos y `git diff --check` sin errores (avisos LF/CRLF en archivos previos). La primera ejecución encontró una expectativa antigua del rótulo CRUD; se actualizó a Acciones y las ejecuciones posteriores pasaron. No se realizó ensayo visual completo en navegador.
- Fase 4A sigue parcial: los campos editables del autoservicio necesitan decisión del solicitante. Se mantiene el rechazo de colisiones de código, sin inventar política definitiva.

## 2026-10-10 — Revisión documental del plan y continuidad

- Se contrastaron código, rutas, decoradores, plantillas, JavaScript, esquema y pruebas con la documentación. Se reformularon entregas 4A/4B, 5A/5B, 6 y 7, preparación del piloto y 8 opcional, conservando las fases históricas.
- Se precisaron operaciones por rol, perfil pendiente, límites de ponderaciones y psicometría, reportes operativos independientes y requisitos institucionales. No se implementaron funciones ni se cambiaron permisos/esquema.
- Se conservaron los cambios locales previos en asistencia HTML/CSS/JS y `tests/test_app.py`; su fecha funcional no se conoce y esta entrada no se la atribuye. No se recrearon entorno, configuración o base.
- Verificación de esta revisión: **44 pruebas aprobadas en 18,734 s** el 2026-10-10, con `python -m unittest discover -s tests -v` mediante `.venv`; bases aisladas. Enlaces locales comprobados y `git diff --check` sin errores de espacios (con avisos de conversión LF/CRLF en archivos locales previos).
- La revisión anterior comunicó **44 pruebas aprobadas en 19,215 s** el mismo 2026-10-10; es un resultado anterior, separado de la ejecución aquí registrada. Las cifras 42/43 e integridad local siguientes se conservan como historia, sin presentarlas como evidencia vigente.

## 2026-09-29 — Especialidad principal y año mostrado en dashboards

- Se agregó `voluntarios.especialidad_principal` mediante migración aditiva SQLite v8, con el catálogo acordado: Rescate en agua, Rescate en montaña, Rescate en selva, Lucha contra incendios, Primeros Auxilios y K-9. Los registros históricos quedan NULL y la interfaz los identifica como “Sin especialidad registrada”.
- La especialidad se captura en solicitudes y altas manuales, se valida en backend, se puede editar en el directorio autorizado y aparece en el directorio de Instructores Voluntarios y junto a nombre/código en el registro de asistencia.
- Las pantallas protegidas muestran el año calendario actual en la etiqueta del dashboard. La actualización no cambia ni crea filas en `periodos`, que continúan como datos operativos administrados por su módulo.
- README, continuidad de AGENTS y documentación del esquema/inicio se alinearon con v8. Se añadieron pruebas para las vistas anuales y la nueva propiedad del perfil.
- Verificación: 43 pruebas aprobadas, compilación Python, sintaxis JavaScript y diff limpios. Base local migrada a v8 con `quick_check=ok`, cero infracciones FK, cuatro asistencias y un período existente conservados.

Registra requisitos acordados, cambios funcionales y configuraciones relevantes. Los estados describen el repositorio y las verificaciones disponibles; una entrada no implica que el cambio esté publicado o en producción. Las fechas de las fases tempranas no pudieron confirmarse y por eso se conserva su orden sin atribuirles fechas inventadas.

## Historial por fases

### Fase 1 — Base ejecutable

- Se creó el esqueleto de desarrollo con Python/Flask, HTML, CSS y JavaScript nativo.
- Se configuraron SQLite, variables locales, archivos de entorno de ejemplo, estructura inicial, ruta mínima y guía para instalar y ejecutar en Windows.
- Se añadieron pruebas iniciales para verificar la respuesta HTTP.

### Fase 2 — Persistencia y autenticación

- Se añadieron el modelo SQLite, perfiles y cuentas con contraseñas almacenadas como hash, autenticación y autorización por rol.
- Se añadieron login/logout, sesiones protegidas, validación CSRF, auditoría mínima y seed idempotente del Administrador.
- Se acordó validar permisos en backend y conservar datos e historial al ampliar el esquema.

### Fase 3 — Diseño y dashboards por rol

- Se implementaron una plantilla compartida y dashboards separados para Administrador, Jefe de Personal e Instructor Voluntario; login dirige al panel correspondiente al rol.
- Se incorporaron navegación lateral plegable, modo claro/oscuro, indicadores conectados a la base y diseño adaptable.
- Se adoptó la identidad SBRAB: emblema institucional, azul `#1D1BBE` y naranja `#F57B1A`. El acceso también se actualizó para incluir el logo y mantener el mismo lenguaje visual.
- Evaluar.com quedó como referencia general de organización; no se copia su marca o interfaz.

### Fase 4 — Solicitudes y administración de personal

- Se implementaron solicitudes públicas de registro de Instructor Voluntario, aprobación/rechazo administrativo y asignación a un Jefe de Personal. Las cuentas pendientes no acceden a datos protegidos.
- Administración puede crear cuentas de Instructor Voluntario manualmente. Se conserva la revisión de solicitudes; el panel dejó de ofrecer invitaciones por correo y mantiene las rutas antiguas por compatibilidad.
- Se incorporaron directorios tabulares de Instructores Voluntarios y Jefes de Personal. Administración dispone de alta, consulta, edición y desactivación; Jefe de Personal consulta, edita y desactiva personal activo asignado, sin alta. La baja lógica conserva historial.
- Se añadieron altas/edición/desactivación de Jefes de Personal y controles para que un Jefe de Personal opere solo sobre su equipo asignado.

### Fotos, configuración de cuenta y cambio de nombres de rol

- Se agregó carga opcional de fotos PNG/JPEG a los formularios de perfiles, edición administrativa y visualización privada en los paneles del Administrador, Jefe de Personal e Instructor Voluntario. Las imágenes se guardan bajo `instance/perfiles`, fuera de recursos estáticos.
- Administración puede editar su propio nombre, foto y contraseña; también restablecer las contraseñas de Jefes de Personal e Instructores Voluntarios. El cambio almacena un hash e invalida sesiones anteriores.
- Los nombres vigentes pasaron de `INSTRUCTOR`/`VOLUNTARIO` a `JEFE_PERSONAL`/`INSTRUCTOR_VOLUNTARIO`. La migración v5 conserva IDs, perfiles, relaciones e historial.

### Datos de identidad del Instructor Voluntario — esquema v6

- Se acordaron nombres, apellido paterno, apellido materno y fecha completa de nacimiento para crear el código institucional de tres iniciales más `DDMMAA` (ejemplo `DMC-020478`).
- Los formularios de solicitud, alta administrativa y edición se coordinaron con los campos almacenados. El servidor genera el código y rechaza colisiones; la política definitiva para duplicados sigue pendiente.
- La migración v6 agrega los campos sin inventar información para perfiles históricos y crea un índice único parcial para códigos presentes.
- Siguen pendientes datos demográficos/organizacionales: país/nacionalidad y departamento dependiente, año de incorporación y antigüedad calculada, especialidad principal/secundarias, catálogo relacional de cursos y operaciones. Este era el pendiente en v6: la especialidad principal se resolvió después en v8; las secundarias y los demás campos siguen pendientes.

### Fase 5 parcial — Evaluaciones, asistencia y capacitaciones

- Administración tiene pantallas iniciales para períodos, catálogo de evaluaciones y asignaciones. Jefe de Personal puede registrar/corregir calificaciones manuales no psicométricas con historial; el Instructor Voluntario solo consulta estados y avance, sin notas ni observaciones.
- Se rediseñó asistencia como lista por fecha y actividad con los estados Asiste, Atraso, Permiso y Falta. El historial filtra por Instructor Voluntario, última fecha registrada o rango de fechas.
- Capacitaciones o Cursos se separó de Asistencias y se añadió al menú lateral de Administrador y Jefe de Personal. La pantalla permite listar, registrar y editar entradas de `capacitaciones`; no hay borrado físico y el Jefe de Personal queda limitado a su ámbito.
- La migración aditiva v7 agregó `asistencias.estado_detalle` y conservó la columna de estado previa. Los registros antiguos siguen intactos; una categoría de presentación se deriva de cada estado legado para el historial nuevo.
- Las pruebas psicométricas continúan bloqueadas: no hay instrumentos, reactivos ni reglas de puntuación aprobados para habilitarlas. Fase 6 no ha comenzado.

## Revisión de consistencia y migración local — 2026-09-29

- La auditoría de base y formularios encontró desajuste entre el esquema local anterior y los campos requeridos por el código. Se corrigió el orden de actualización de `schema_version` para marcar una migración solo después de ejecutarla correctamente.
- Se alineó la vista previa del código de Instructor Voluntario con la validación del servidor; se reforzó la validación de solicitudes y se evita dejar archivos de foto huérfanos cuando una operación falla.
- En esa revisión la base local aún estaba en versión 5. Posteriormente se ejecutó `flask --app sicose init-db` para aplicar la migración acumulada a versión 7. Se conservaron las 4 filas existentes de asistencia.
- Tras la migración local, SQLite devolvió `quick_check=ok` y cero infracciones de claves foráneas.
- En las verificaciones históricas de esa revisión v7 del 2026-09-29, 42 pruebas aprobaron; también pasaron la compilación de Python, `node --check frontend\static\js\app.js` y `git diff --check` (este último mostró avisos de conversión de finales de línea, sin errores de espacios).

## Actualización documental — 2026-09-29

- Se reorganizó este historial para reflejar fases, migraciones, acuerdos visuales, cambios de roles, administración de perfiles y el estado parcial de Fase 5.
- Se amplió `README.md` con requisitos aprobados, alcance por rol, privacidad, datos del Instructor Voluntario, identidad visual, estado implementado/pendiente, instalación, pruebas y referencias técnicas.
- Esta actualización solo modifica documentación; las cifras de pruebas de la sección anterior corresponden al último cambio funcional verificado.

## 2026-10-10 — Fase 4B parcial: especialidades secundarias

- Esquema v10: conjunto relacional opcional del catálogo aprobado, sin duplicados; principal permitida también como secundaria. Edición en modal por Administrador/Jefe dentro del ámbito; consulta propia de Instructor en Mi perfil.
- Migración local tras respaldo SQLite, inicialización repetida: 18 tablas previas conservadas, quick_check=ok y cero infracciones FK. No se recreó entorno ni base.
- Suite final: 55 pruebas aprobadas en 24,331 s. La primera ejecución detectó una expectativa de versión 9 obsoleta; se actualizó a 10 y se repitió la suite completa. Compilación Python, sintaxis JavaScript y diff correctos; modal verificado en Chromium a 360 y 1447 px con API simulada.
- Cursos/operaciones y alcance geográfico adicional pendientes de consultas al solicitante; no se declara cerrada 4B ni aceptación institucional.

## 2026-10-10 — Cierre técnico de Fase 4B, esquema v11

- Acuerdos confirmados: catálogo común exclusivo de Administrador; Administrador/Jefe gestionan capacitaciones por ámbito e Instructor consulta lo propio sin observaciones. Eventos solo Administrador; Jefe vincula personal activo asignado; Instructor consulta sus participaciones. Nacionalidad/residencia ampliada editable por gestión y consultable por Instructor propio.
- Implementados catálogo/relación opcional de cursos, operaciones compartidas/participaciones y geografía diferenciada con catálogo inicial latinoamericano. Bolivia conserva nueve departamentos; provincia libre en otros países. Históricos sin inferencia ni vinculación automática; nombres, IDs y experiencia textual preservados.
- Migración local v11 tras respaldo: todas las columnas previas de 19 tablas conservadas, inicialización repetida, curso_id histórico NULL, quick_check=ok, FK=0. No se recreó entorno/base.
- 58 pruebas aprobadas en 62,893 s; compilación Python y sintaxis JavaScript correctas. Cierre técnico; aceptación operativa pendiente. Siguiente entrega 5A; requisitos institucionales del piloto pendientes.

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


### Corrección visual — Cabecera de asistencia (2026-10-10)

Responsable, Gestión, Actividad y Fecha en una fila de escritorio, dos columnas en tablet y una en móvil. Actividad cambia de texto libre a selector con Ordinaria, Actividad Externa, Terreno y Operación; históricos conservados sin cambios de esquema ni permisos. Se igualó la altura de los controles para alinear la fila.

Verificación de esta corrección: seis escenarios Chromium (Administrador/Jefe, 360/768/1447 px), orden y opciones exactos, sin desborde y una sola fila a 1447 px. Carga de asistencia existente al elegir Ordinaria comprobada con API simulada. Sintaxis JavaScript y git diff --check correctos. No se repitió la suite funcional para este ajuste de HTML/CSS; las 62 pruebas de la entrega anterior conservan su contexto histórico.


### Corrección visual — Columnas de llamada de asistencia (2026-10-10)

Tabla reducida a Nombre completo, Código, Estado y Asistencia; especialidad retirada solo de esta tabla. Estado con orientación vertical y colores verde para ACTIVO/rojo para INACTIVO. Se conservan el filtro de personal activo y los permisos; se ajustan los mensajes vacíos a cuatro columnas. Seis escenarios Chromium con datos sintéticos (Administrador/Jefe, 360/768/1447 px) comprobaron columnas, orientación, colores, Falta inicial, exclusión de inactivos y ausencia de desborde. Sintaxis JavaScript y git diff --check correctos; no se repitió la suite funcional para esta corrección visual.


### Ajuste vigente — Estado horizontal en asistencia (2026-10-10)

Por corrección del solicitante, la etiqueta Estado pasa a orientación horizontal; conserva ACTIVO en verde e INACTIVO en rojo. Sustituye la orientación vertical de la revisión anterior. Estilos comprobados en Chromium a 360/1447 px; git diff --check correcto.


### Revisión en curso — Directorio y alta de Instructores (2026-10-10)

Se simplifica el directorio a siete columnas y tres acciones principales: Ver (consulta modal), Editar perfil (modal existente) y Desactivar (baja lógica existente). Estado horizontal verde/rojo; nacimiento, usuario, correo, residencia, incorporación, experiencia y especialidades secundarias se consultan en Ver. Restablecer contraseña sigue disponible para Administrador dentro de Editar perfil. Alta con residencia Bolivia oculta y botón Guardar. Grado aún carece de catálogo/permisos/persistencia y muestra Sin registrar; unificación de fecha de incorporación y ampliación de solicitud siguen pendientes, sin cambios de esquema ni cálculo actual.

Cuatro escenarios Chromium con API simulada (Administrador/Jefe, 360/1447 px): siete columnas, tres acciones, consulta con datos, edición precargada y sin desborde. Sintaxis JavaScript y git diff --check correctos. La entrega completa aún requiere resolver las consultas y verificar los cambios funcionales restantes.


### Perfil y directorio vigentes — Grado e incorporación (2026-10-10, v14)

- Directorio con Nombre completo, Código, Grado, Especialidad Principal, Estado, Antigüedad y Acciones. Estado horizontal: ACTIVO verde, INACTIVO rojo, con texto identificable. Ver consulta en modal los datos permitidos y foto; Editar perfil usa modal y Desactivar conserva baja lógica. Restablecer contraseña sigue siendo exclusivo del Administrador, dentro de Editar perfil; nunca se muestra la contraseña guardada ni su hash.
- Grados permitidos: Instructor Inicial, Instructor Segundo, Instructor Primero, Instructor Principal e Instructor Mayor. Administrador los asigna/edita; Jefe solo en personal activo asignado y puede proponerlo al solicitar el alta de su equipo. Instructor consulta el suyo sin editar. La solicitud pública no permite enviar grado; queda NULL hasta revisión del personal autorizado. No se asigna un grado por defecto a históricos ni se infiere por antigüedad.
- Una sola Fecha de incorporación en alta y edición. Al registrarla se sincronizan fecha_incorporacion, antiguedad_desde y ano_incorporacion. Antigüedad = año calendario actual del servidor menos año de incorporación, sin descontar meses/días. Fechas inválidas/futuras y año/fecha contradictorios rechazados. Históricos mantienen año y fecha anterior, incluso si difieren, hasta completar explícitamente la nueva fecha; no se fabrican fechas desde un año. Borrar una fecha canónica existente borra también sus dos valores derivados; un formulario sin fecha histórica completa conserva el año previo.
- Alta administrativa permite ACTIVO o INACTIVO. Solicitudes de Jefe/públicas permanecen PENDIENTE, sin selector que habilite acceso, hasta aprobación administrativa. Las cuentas inactivas/pendientes no acceden a información protegida.
- Alta y solicitudes incluyen nombres, ambos apellidos, nacimiento, código generado en servidor, especialidad principal, usuario, correo, contraseña, nacionalidad, departamento y foto PNG/JPEG (máximo 3 MiB). Correo, nacionalidad, departamento y foto ahora son obligatorios también en servidor. Fecha de incorporación y grado son opcionales; las solicitudes públicas no incluyen grado. Residencia Bolivia oculta en las pantallas nuevas, nacionalidad independiente y catálogo latinoamericano existente. Países históricos se conservan en consulta/edición; no hay reclasificación automática a Bolivia en migración. Botón Guardar. Invitaciones usan el mismo formulario y validaciones.
- Migración v14 aditiva: grado y fecha_incorporacion nullable, sin rellenar perfiles anteriores. Respaldo local previo; 24 tablas anteriores preservadas, inicialización repetida, quick_check=ok y cero infracciones de claves foráneas. No se recrearon .venv, .env ni base local.

Verificación actual (2026-10-10): 64 pruebas aprobadas en 31,611 s, con bases aisladas. Ocho escenarios Chromium con datos sintéticos/API simulada (Administración, Jefe, Instructor y solicitud pública; 360/1447 px), modales precargados, campos/opciones/roles y ausencia de desborde comprobados. Compilación Python, sintaxis JavaScript y git diff --check correctos. La primera ejecución detectó dos expectativas antiguas de etiquetas (Guardar y retiro de Especialidad en tabla de asistencia); actualizadas y suite completa repetida. No se afirma cierre de Fase 5A ni aceptación institucional del piloto.


### Corrección visual — Filas compactas del directorio (2026-10-10)

Se corrige la desalineación causada por display:flex aplicado a la celda del nombre: celda table-cell y contenedor interno para foto/nombre. Acciones con iconos SVG en una fila, etiquetas accesibles y título descriptivo; padding/anchos ajustados. Ver y Editar conservan sus modales; Desactivar conserva la baja lógica autorizada.

Ocho escenarios Chromium con API simulada: Administrador/Jefe, 360/1447 px y temas claro/oscuro; alturas de celdas alineadas, filas sintéticas de aproximadamente 59 px, tres iconos lado a lado, etiquetas accesibles y modales precargados, sin desborde de página. Captura sintética inspeccionada. Sintaxis JavaScript y git diff --check correctos. No se repitió la suite funcional para este ajuste de presentación; las 64 pruebas de v14 conservan su contexto.


## 2026-10-11 — Consolidación documental y siguiente entrega

- README reorganizado por capacidades/permisos vigentes, perfil v14, asistencia/calendario/PDF, catálogo de cursos, operaciones, notas y planificación. Retiradas las afirmaciones actuales que negaban PDF, consulta propia de cursos o gestión del catálogo por Jefe; su evolución sigue documentada en las entradas históricas.
- AGENTS conserva la guía general y reemplaza bloques de continuidad acumulados por un punto único: esquema v14, acuerdos confirmados, directorio compacto con iconos en fila, límites abiertos y uso del entorno existente. No cambia permisos, código ni esquema.
- Siguiente entrega recomendada: Notas e historial, revisión de registro/corrección, errores/concurrencia, ámbitos y conservación; luego aceptación integral de asistencia/cursos/notas para 5A. 5B exige definir reglas de períodos/versiones/faltantes/redondeo. No se inicia funcionalidad por esta revisión ni se declara aceptación operativa/institucional.
- Evidencia funcional anterior preservada: 64 pruebas aprobadas en 31,611 s el 2026-10-10. Se conservan también 42 pruebas de v7 y 43 de v8 del 2026-09-29, y las ejecuciones intermedias en su contexto. No se reejecutó la suite ni las migraciones el 2026-10-11.
- Verificación de esta revisión: rutas/código/plantillas/pruebas contrastados; 64 pruebas definidas. Consulta SQLite local solo lectura: esquema 14, quick_check=ok y cero infracciones FK. Enlaces locales y git diff --check correctos. Cambios existentes en frontend/login.html preservados, sin atribuirles fecha funcional. .venv, .env y base local conservadas.


## 2026-10-11 — Cierre técnico de Fase 5A: seguimiento operativo

- Secuencia completada: Notas e historial → cursos/historial personal → recorrido integral de asistencia/calendario/PDF por rol. Cierre técnico cumplido; aceptación operativa humana pendiente, sin declarar aprobación institucional.
- Corregidos pérdida de asignación tras guardar nota, opción inicial sin valor vacío, historial/carga con respuestas tardías y guardado habilitado durante error/cierre; formulario hidden respetado. Guardar y corregir mantiene selección/historial; controles bloqueados durante carga/envío.
- Notas: BEGIN IMMEDIATE serializa comprobación/inserción; dos primeras notas o correcciones sobre una referencia común producen un éxito y un conflicto, sin ramas. Referencia entera positiva, campos admitidos y nota finita 0–100 validados; no se modifica puntuación, precisión ni pesos.
- Capacitaciones: edición de observación sin cambio de curso_id conserva nombre histórico pese a renombrado del catálogo; fechas falsas/numéricas/listas/no ISO rechazadas. Sin nueva interfaz de asignación ni versionado completo de cursos.
- Suite final: **68 pruebas aprobadas en 48,333 s**. Cuatro pruebas nuevas de notas/privacidad/cierre, simultaneidad real con dos clientes, preservación de curso/fechas y reasignación. Primeras ejecuciones detectaron fallos en la preparación CSRF del cliente concurrente; se corrigió obteniendo el token del dashboard tras login y siguiendo su redirección. Prueba concurrente aprobada y suite completa repetida.
- 20 escenarios Chromium con API simulada y datos sintéticos: Administrador/Jefe (notas/cursos/asistencia), Instructor (cursos/calendario), 360/1447 px y vacíos de notas. Sin errores JavaScript ni desborde; guardado/corrección consecutivos, cierre/error y modales comprobados. Dos PDF reales exportados desde fixture aislada, tres páginas cada uno, renderizados e inspeccionados con carimbo/cabeceras/paginación sin solapamiento.
- Compilación Python, sintaxis JavaScript, enlaces locales y git diff --check correctos. Esquema v14 sin migraciones ni cambios en base local/.env/.venv. Modificación previa de frontend/login.html conservada. Detalle en [cierre 5A](docs/08_cierre_fase_5a.md).
- Siguiente entrega: definir reglas 5B; no asumir pesos, faltantes, redondeo ni decisiones institucionales. Recorrido humano de aceptación operativa pendiente, separado del cierre técnico.


## 2026-10-11 — Inicio de definición de reglas 5B

Confirmados por el solicitante: cálculo independiente con Física/Académica/Desempeño manuales; asistencia separada; períodos anuales enero–diciembre con uno ACTIVO; Administrador gestiona borradores/publicación/cierre/reapertura con motivo y Jefe registra/corrige solo en período activo. Se crea [borrador 5B](docs/09_reglas_fase_5b.md) con estado real del código, acuerdos, propuestas pendientes y criterios futuros. Pesos/faltantes/precisión/versiones/instantáneas continúan en consulta; no se adoptan pesos históricos ni decisiones institucionales. Sin cambios de código, esquema v14, entorno o base; no se reejecutó la suite funcional. Enlaces locales y git diff --check comprobados.


### 2026-10-11 — Reglas 5B: faltantes y precisión confirmados

Solicitante confirma Incompleto/No calculable ante alguna nota faltante, sin sustitución por cero ni redistribución; cero registrado válido. Notas nuevas de hasta dos decimales y resultado final a dos decimales, mitad hacia arriba, sin redondeos intermedios ni alteración de históricos. Su respuesta 0–100 puntos se registra como escala por componente; no se infiere promedio simple ni porcentajes. Se consulta combinación, selección de evaluación por componente y congelación de configuración; cierre/reapertura e instantáneas quedan pendientes. Documentación y casos matemáticos actualizados, sin código/cálculo/migración ni cambios en entorno/base. Enlaces y git diff --check correctos; suite no repetida para esta definición.


### 2026-10-11 — Reglas 5B: composición anual y Comandante

Confirmados promedio simple de tres componentes y configuración congelada en período activo. Física: dos evaluaciones obligatorias promediadas; Académica: nota global manual respaldada por historial, sin conversión automática de cantidad de cursos a puntos. Desempeño involucra Jefe y Comandante, con combinación interna pendiente. Solicitante requiere rol propio Comandante limitado a grupo; no se crea rol ni se asignan permisos/grupos en esta definición. Se consultan combinación de Desempeño, responsable Académico y estructura del grupo; cierre/instantáneas/permisos siguen pendientes. Sustituida propuesta de una evaluación única por componente en el borrador. Solo documentación: sin código, cálculo, migración ni cambio de entorno/base; enlaces y git diff --check verificados, suite no repetida.


### 2026-10-11 — Reglas 5B: Desempeño y grupo único

Solicitante confirma dos notas de Desempeño (Jefe/Comandante) promediadas, ambas obligatorias. Académica la registra/corrige Jefe; Administrador puede corregir con historial. Aclara un único grupo SBRAB y un solo cargo Comandante (nombre modificable, cargo estable); se descarta la propuesta de múltiples grupos. Promedio conjunto de tres componentes equivale a (Física_1 + Física_2 + 2×Académica + Desempeño_Jefe + Desempeño_Comandante)/6, sin promediar las cinco entradas por igual. Acceso del Comandante, respaldo académico y cierre/instantáneas siguen en consulta. Solo documentación; no rol, permiso, grupo ni fórmula implementados. Enlaces y git diff --check correctos.


### 2026-10-11 — Definición de reglas 5B acordada

Últimas decisiones confirmadas: Comandante consulta personal/seguimiento/formación/notas/resultados operativos SBRAB sin observaciones ajenas y edita solo su propia aportación de Desempeño; no administra cuentas/permisos/períodos/configuración. Académica requiere motivo y referencias a formación personal, sin formación queda pendiente. Cierre permite personas incompletas identificadas, conserva instantáneas y cada reapertura/cierre posterior, sin cambiar configuración congelada.

Se consolida docs/09_reglas_fase_5b.md: fórmulas exactas, casos de aceptación, permisos, fuentes/respaldo, período anual/activo único, cierre/reapertura y secuencia de implementación. README/AGENTS y bloque 5B del plan alineados. La definición queda acordada para implementar el prototipo; no acredita aprobación institucional de puntuación ni aceptación del piloto. Sin código, rol/grupo/cálculo, esquema, migración ni cambios de entorno/base en esta entrega. Enlaces locales, casos aritméticos y git diff --check verificados; suite funcional no repetida. Evidencia previa de 68 pruebas conserva su fecha y contexto.


## Primera entrega implementada de Fase 5B — 2026-10-11 (v15)

- Rol COMANDANTE_GRUPO con panel propio y cargo único SBRAB. Administrador crea/edita/desactiva cuentas y restablece contraseña; una sola cuenta Comandante ACTIVO, garantizada también por triggers SQLite. No se reutiliza una cuenta para otra persona ni se elimina autoría; nombre editable e historial con nombres capturados. No se creó una cuenta automáticamente.
- Seguimiento 5B para Administrador/Jefe/Comandante: selección de persona activa/período, perfil básico, formación, asistencia y notas sin asignar históricos a nuevas fuentes. Jefe solo personal activo asignado. Comandante consulta seguimiento de personal activo SBRAB y registra/corrige solo su aportación; sin administración ni observaciones/motivos/referencias privadas ajenas. Instructor sin acceso numérico 5B.
- Cinco fuentes independientes: FISICA_1, FISICA_2, ACADEMICA, DESEMPENO_JEFE y DESEMPENO_COMANDANTE. Notas nuevas 0–100 con hasta dos decimales, almacenadas en centésimas enteras; solo período ACTIVO. Física: Admin/Jefe autorizado. Académica inicial: Jefe; requiere motivo y formación personal referenciada. Desempeño inicial de cada evaluador: Jefe/Comandante correspondiente. Administración puede corregir aportaciones existentes conservando responsable y autor de corrección.
- Cadena por persona/período/fuente: primera nota única, corrección solo de la vigente, inserción serializada y anteriores conservadas. No admitir autor/responsable arbitrarios en JSON. Jefe/Comandante no corrigen Desempeño de otro titular; si cambió responsable, la corrección histórica requiere Administración. Motivo y referencias se conservan como instantánea de respaldo académico; editar el curso después no altera ese respaldo.
- Migración v15: ampliar CHECK de roles preservando IDs/referencias y añadir notas_operativas/respaldo_academico; triggers de Comandante único se crean después de ampliar roles. Inicialización local repetida tras respaldo, 24 tablas anteriores preservadas (roles anteriores incluidos), quick_check=ok y cero infracciones FK. Tablas nuevas vacías, sin cuentas ni notas inferidas. .venv/.env/base existente conservados.
- Verificación: **73 pruebas aprobadas en 80,440 s**, ocho escenarios Chromium (Administración/Jefe/Comandante/gestión de cuenta, 360/1447 px), sin desborde ni errores; modales y envíos, fuentes/roles y período cerrado comprobados. Compilación Python, sintaxis de ambos JavaScript y git diff --check correctos. Pruebas de migración incluyeron esquemas antiguos; se corrigió orden de creación de triggers y fixture de catálogo de roles.

### Límites de esta entrega

Todavía no implementados publicación/configuración congelada, vinculación de fuentes a evaluaciones configuradas, períodos anuales con activo único, cálculo conjunto ni cierre/reapertura con instantáneas de resultados. No se declara cerrada 5B. Las APIs/notas históricas y pantalla de asignaciones anterior se mantienen por compatibilidad; no se convierten ni participan automáticamente en el futuro cálculo 5B. Instructor conserva su avance existente, sin nuevo resultado 5B. La aceptación operativa del solicitante y requisitos institucionales mantienen sus pendientes.

Siguiente entrega concreta: ciclo de períodos y configuración de las fuentes, publicación/congelación y un solo período activo; luego cálculo y cierres. Los permisos/periodicidad más estrictos se aplicarán al ciclo configurado, sin modificar períodos guardados silenciosamente.


## 2026-10-11 — Segunda entrega de Fase 5B — 2026-10-11 (v16)

Administrador dispone de **Períodos y configuración**: crea borradores anuales enero–diciembre, configura cinco fuentes mediante modal y publica/activa en una transacción. La revisión del borrador evita sobrescribir cambios concurrentes. Publicación exige fuentes completas con evaluaciones manuales activas de categoría compatible; dos fuentes de la misma categoría pueden usar la misma evaluación de catálogo, manteniendo sus notas independientes. Configuración versión 1 con regla PROMEDIO_TRES_V1 (igual importancia de los tres componentes); no habilita porcentajes arbitrarios ni cálculo aún.

La publicación congela fuentes, nombres/códigos/categorías, autor y fecha UTC. Cambiar el catálogo después no reescribe esas referencias. Un solo período puede activarse bajo concurrencia, también protegido por triggers. No se cierran otros períodos automáticamente. Notas/correcciones 5B requieren período ACTIVO y configuración PUBLICADA; configuración_id/evaluacion_id se resuelven en servidor, sin aceptar esos valores del cliente. La API de calificación anterior no registra notas en períodos configurados 5B; los registros anteriores siguen consultables.

Migración v16 aditiva: configuraciones_5b y fuentes_configuracion_5b, dos referencias nullable en notas_operativas y restricciones. Respaldo local previo, 26 tablas anteriores preservadas, inicialización repetida, quick_check=ok y cero infracciones FK. Períodos y notas históricas sin modificación ni adopción; referencias anteriores NULL. La base local no tenía períodos ACTIVO; una base histórica que sí los tenga bloqueará nuevas activaciones hasta un tratamiento explícito en la entrega de cierre, sin alterar sus estados al migrar.

Verificación actual: **77 pruebas aprobadas en 86,620 s** (bases aisladas), incluyendo publicación concurrente, revisiones obsoletas, fuentes incompletas/categoría inválida, congelación, permisos/CSRF y preservación v15. Ocho escenarios Chromium con API simulada a 360/1447 px: publicación y modal administrativo, notas por los tres roles y bloqueo de edición sin configuración publicada; sin desborde ni errores JavaScript. Compilación Python, sintaxis de los tres JavaScript, enlaces locales y git diff --check correctos.

Pendientes: cálculo provisional exacto/faltantes/redondeo, cierre y reapertura motivada con cada instantánea preservada, aceptación operativa e institucional/privacidad antes del piloto. **No se declara cerrada Fase 5B.** Siguiente entrega: cálculo provisional vinculado a configuración y últimas notas válidas, separado de asistencia y psicometría.


## 2026-10-12 — Acuerdos de reformulación de evaluaciones y cursos (documental)

Se registran las respuestas del solicitante en [reglas nuevas](docs/10_reformulacion_evaluaciones.md): Comandante sin rol operativo propio, transcripción con evaluador/autor separados, Jefe único sin asignación necesaria, habilitación por evaluación/gestión, inactivos consultables sin nuevas habilitaciones/notas, físicas reprogramables con No cumplida=0, notas físicas/académicas publicadas al Instructor, acumulación académica entera, participantes con estados/historial, estado de cursos derivado de fechas, avance y PDF consolidado. Pendientes de aclaración: límites/imputación académica, alcance global del Jefe y corrección/republicación. Sin cambios funcionales, de permisos, esquema o base. Sin nueva ejecución de suite; evidencia v16 del 2026-10-11 sigue histórica. Enlaces locales y git diff --check verificados.


## 2026-10-12 — Primera entrega de la reformulación (v17)

Jefe único activo con alcance global sin filtro de asignación; Comandante retirado del acceso operativo, conservado solo en datos históricos. Desempeño del Comandante transcrito por Administrador/Jefe con nombre del evaluador y autor de transcripción separados. Tabla Evaluaciones por gestión y consulta modal de activos/inactivos, habilitación individual con historial y notas 5B bloqueadas al deshabilitar; PDF administrativo con carimbo SBRAB. Instructor consulta habilitación/estado/avance por gestión, todavía sin notas publicadas.

Acuerdos complementarios: Académica acumulará puntos enteros con tope 100; puntos individuales ajustables, gestión de finalización personal y cómputo único. Administrador/Jefe publicarán; después de corrección se conservará la versión publicada anterior hasta republicar. **Cursos con puntos, programación/reprogramación física, No cumplida=0, acumulación y publicación/republicación aún pendientes.** El flujo manual académico anterior y configuraciones congeladas no se convierten automáticamente. Psicometría continúa bloqueada; Fase 5B no cerrada.

Evidencia vigente: 81 pruebas aprobadas en 45,711 s; ocho escenarios UI, PDF sintético de cinco páginas, compilación/sintaxis/enlaces/diff correctos. Migración v17 tras respaldo, 28 tablas anteriores preservadas, inicialización repetida, quick_check=ok, FK=0. Detalles en [reglas y estado](docs/10_reformulacion_evaluaciones.md). Siguiente entrega: cursos con puntaje y asignación/finalización individual con historial.


## 2026-10-12 — Estilo de Evaluaciones por gestión

Gestión se presenta como año derivado de fecha_inicio del período, sin renombrar ni modificar fechas guardadas. El listado de gestiones añade ese dato a su proyección; conserva IDs y distingue borradores del mismo año cuando sea necesario. Filtro proporcionado, botón Generar reporte PDF (no enlace), tabla con anchos y espaciado consistentes, estado horizontal con color y acción Ver por icono con nombre accesible. Modal con filas compactas, etiquetas de habilitación/finalización y controles breves; adaptación móvil y ambos temas. Instructor conserva proyección sin notas ni controles administrativos.

El PDF queda deshabilitado al cambiar año o durante la consulta, habilitándose solo tras una respuesta vigente; descarga institucional existente conservada. Sin cambios de permisos, puntuación, esquema ni base. Cambios locales previos y frontend/login.html preservados.

Verificación: cuatro pruebas relevantes de reformulación aprobadas en 3,164 s; 12 escenarios Chromium con API simulada (tres roles, 360/1447 px, claro/oscuro), descarga PDF, año, iconos accesibles, modal compacto y cuentas inactivas sin escritura comprobados; sin desborde ni errores JavaScript. Compilación Python del módulo, sintaxis JavaScript y git diff --check correctos. La suite completa de 81 pruebas de la entrega v17 sigue como evidencia histórica, no se repitió para esta corrección visual.


## 2026-10-12 — Cursos, participantes y finalización individual (v18)

Administrador/Jefe registran/editar catálogo con puntaje entero 0–100, fechas/entidad obligatorias en cursos nuevos y estado automático de Bolivia. Asignación personal/múltiple sin duplicados, finalización independiente con puntaje y fecha explícitos, correcciones con actor/fecha/motivo/revisión y valores anteriores preservados. Edición del catálogo no reescribe datos capturados al asignar. Inactivos solo consulta/historial. Instructor ve sus estados y formación histórica, sin puntajes hasta publicación; Dashboard/seguimiento enlazan las participaciones. PDF de catálogo filtra estado calculado. Histórico sin datos completos permanece intacto y sin puntos inferidos.

Verificación vigente: 86 pruebas aprobadas en 87,375 s; 12 escenarios UI, sin desborde/errores; migración local tras respaldo e inicialización repetida preservando 29 tablas, quick_check=ok y FK=0. Compilación, sintaxis, enlaces y diff correctos. Detalles en [reglas y evidencias](docs/11_cursos_formacion.md). Pendientes acumulado académico hasta 100, físicas/reprogramación/No cumplida, publicación/republicación y cierres; no se declara cierre 5B ni del piloto.


## Gestiones de evaluaciones: administración exclusiva — 2026-10-12

Menú/pantalla Gestiones de evaluaciones solo para Administrador. Jefe e Instructor conservan Gestión (año) únicamente para consultar evaluaciones, conforme a la aclaración del solicitante. Creación/configuración/publicación y nueva edición de nombre/año se comprueban en servidor mediante role_required ADMINISTRADOR, incluidos accesos directos a APIs.

PATCH /api/admin/5b/periodos/<id> edita un borrador anual sin asignaciones ni notas y sin configuración publicada. Valida nombre/año y valores anteriores para rechazar ediciones obsoletas; conserva enero–diciembre. Incrementa la revisión de configuración en borrador cuando existe, invalidando publicaciones/configuraciones de pestañas antiguas; cambios auditados. Las gestiones publicadas, cerradas, no anuales o con registros conservan sus datos. Edición mediante modal administrativo. Sin cambios de esquema ni migración/local SQLite.

Verificación: 10 pruebas relevantes de Fase 5B aprobadas en 7,090 s (bases aisladas), con denegación para Jefe/Instructor de creación, edición, configuración/publicación y consulta de administración; consulta por año preservada. Seis escenarios Chromium con API simulada (tres roles, 360/1447 px), edición modal y navegación por permisos correctas, sin desborde ni errores. Compilación Python, sintaxis JavaScript y git diff --check correctos. La suite completa de 86 de cursos sigue como evidencia histórica, no se repitió para esta corrección.


## 2026-10-12 — Consolidación documental de README, AGENTS e HISTORY

Se consolidó el estado vigente en README y el bloque de continuidad de AGENTS, retirando de esos resúmenes las entregas antiguas duplicadas. HISTORY conserva íntegramente la cronología, incluidas las cifras históricas de 42 y 43 pruebas y sus contextos. Se corrigieron las contradicciones sobre alcance global del Jefe único, Comandante externo sin acceso operativo, gestión exclusiva del Administrador y selector anual de consulta para los demás roles. Cursos v18 reflejan puntaje, estado automático, participaciones/finalización personal e historial, sin presentar acumulación ni publicación como implementadas.

Se distinguen configuración publicada y notas publicadas, formación histórica y participaciones nuevas, así como datos registrados y cálculos todavía pendientes. Queda identificado el flujo explícito de reactivación de cuentas inactivas como pendiente; no se incorporó funcionalidad. Se mantiene instalación inicial separada de continuación con entorno existente, aceptación operativa pendiente y requisitos institucionales/privacidad previos al piloto.

Verificación de esta revisión: inspección de Git, código/rutas/plantillas y evidencias existentes; 87 pruebas definidas, sin nueva ejecución de suite funcional. Base consultada solo en lectura: SQLite v18, quick_check=ok y cero infracciones de claves foráneas. Última suite completa registrada: 86 pruebas en 87,375 s; corrección posterior de gestiones: 10 pruebas en 7,090 s, ambas del 2026-10-12. No se presenta el conteo de 87 como suite aprobada. Enlaces locales y git diff --check comprobados.

Entrega exclusivamente documental: README.md, AGENTS.md e HISTORY.md; sin cambios funcionales, permisos, esquema, configuración o datos locales. Cambios locales anteriores preservados, sin atribuir fechas desconocidas. Siguiente entrega recomendada: programación/reprogramación física y No cumplida auditada; después acumulación/cálculos, publicación/republicación y cierres con instantáneas.

## 2026-10-13 — Revisión estructural y actualización del plan general

Revisados README, AGENTS, HISTORY, estructura, plan, acuerdos 10/11, módulos y pruebas. README/AGENTS coherentes con v18; cabecera y apartados principales del plan conservaban reglas anteriores de Jefe por equipo, Comandante operativo, Académica manual y reportes sin PDF de evaluaciones. Se actualizaron los alcances vigentes y se identificaron puntos de control históricos sin borrar sus evidencias. HISTORY combina bloques por fases y fechas fuera de orden; se preservan para no alterar trazabilidad.

Se añadió docs/12_revision_proyecto.md: estado por fase, mantenimiento gradual de módulos/pruebas, pendientes y reformulación acotada. Numeración preservada; lo restante de 5B se organiza en física, acumulación/cálculos, publicación/republicación y cierres/reaperturas con criterios verificables. No se declara cerrada 5B ni aceptadas operativamente 4A/4B/5A; psicometría condicionada, reportes parciales, piloto pendiente e IA opcional.

Verificación actual: **87 pruebas aprobadas en 143,824 s**, usando .venv y bases sintéticas aisladas; compilación Python, sintaxis de cinco JavaScript, enlaces de documentos revisados y git diff --check correctos. Base local solo en lectura: schema_version=18, quick_check=ok, cero infracciones FK. Sin ensayo visual nuevo ni init-db/seed/migración local. Modificaciones previas preservadas. Entrega documental, sin cambios funcionales, permisos, esquema, secretos o datos.


## 2026-10-13 — 5B.1 Programación física, reprogramación y No cumplida (v19)

Inspeccionados Git, documentos vigentes, APIs/esquema/pruebas. Conservadas las modificaciones locales anteriores en AGENTS, README, HISTORY, plan y docs/12. Solicitante confirmó Administrador/Jefe para creación/corrección de fechas comunes y reprogramación individual; administración de gestiones/configuración permanece exclusiva del Administrador.

Añadido módulo fisicas con dos fuentes comunes por gestión anual, reprogramación extraordinaria y versiones inmutables con fecha anterior, motivo, actor/nombre y modificación UTC. Resultados vinculados a programación y nota vigente: Cumplida con fecha real/nota, No cumplida con motivo/cero sin fecha de realización. Pendiente no genera cero; reprogramar conserva la nota previa. Correcciones con versiones vigentes y transacciones serializadas; activos/habilitados, gestión anual ACTIVA y configuración PUBLICADA. Tabla/avance/PDF distinguen No cumplida. Interfaz de Notas operativas incorpora fechas/historial/resultados; Instructor sin notas/motivos/autores. La interfaz exige programación previa, mientras el API manual anterior sin programación conserva compatibilidad hasta programar explícitamente. Configuraciones PROMEDIO_TRES_V1 y notas históricas no se modifican ni adoptan automáticamente.

Migración local aditiva tras respaldo `instance/backups/sicose-20261013-pre-v19-b3c3c9bd.sqlite3`: tres tablas nuevas vacías, **32 tablas previas comparadas y preservadas**, salvo actualización esperada de schema_version; inicialización repetida dos veces, versión 19, quick_check=ok, cero infracciones FK. `.venv`, `.env`, fotos e historial preservados; sin seed ni dependencias nuevas.

Verificación final nueva: **93 pruebas aprobadas en 195,680 s**, incluyendo seis específicas de físicas. Permisos/CSRF, inactivos/deshabilitados/gestión, fechas/revisiones, cero confirmado/cumplido, reprogramación/correcciones/historial, concurrencia de fechas individuales/comunes y notas iniciales/correcciones, privacidad y migración idempotente cubiertos. Primera ejecución de cinco pruebas específicas: 7,015 s; suite intermedia 92/81,770 s; seis específicas posteriores: 12,364 s. La suite final incluye las ampliaciones de dos pruebas independientes y correcciones concurrentes; las ejecuciones intermedias no sustituyen su resultado.

20 escenarios Chromium con API simulada: 12 en Notas operativas/proyección propia y ocho en tabla/modal administrativo, 360/1447 px, claro/oscuro; programación/reprogramación/envío de No cumplida/cero, historial visual disponible y privacidad propios. Sin errores JavaScript ni desbordes; capturas de pantallas/modales inspeccionadas. Prueba HTTP adicional del PDF con No cumplida/cero: 200, cabecera PDF, privado no-store y auditoría correcta; sin nueva inspección visual de PDF. Compilación Python, sintaxis de los cinco JavaScript, enlaces locales y git diff --check correctos. Evidencias en `.tmp/fisicas-suite-final.log`, `.tmp/fisicas-ui/` y `.tmp/fisicas-migracion.json` (ignoradas por Git).

README/AGENTS/plan y docs/10–12 actualizados; [docs/13_programacion_fisica.md](docs/13_programacion_fisica.md) registra reglas/APIs/compatibilidad/evidencias. Pendientes **5B.2** acumulación/cálculos, **5B.3** publicación/republicación y **5B.4** cierres/reaperturas con instantáneas. No se declara cerrada Fase 5B ni aceptadas operativamente las fases anteriores; requisitos institucionales/piloto, psicometría e IA conservan sus límites.


## 2026-10-13 — 5B.2, Gestión anual y activación por Gestión (v20)

El solicitante pidió continuar 5B.2 revisando antes permisos de Gestiones, activación de evaluaciones y menú. Confirmó: CRUD compartido Administrador/Jefe; eliminación lógica conservando historial; activación anual para todo el personal aparte de habilitación personal; fuente necesaria desactivada deja conjunto No disponible sin redistribuir pesos; Académica pendiente sin formación finalizada; activación explícita administrativa de la nueva regla con notas configuradas y físicas programadas, sin adoptar notas sin configuración ni físicas sin resultado programado.

Gestiones (años) separadas del catálogo. Administrador/Jefe crean, editan borradores sin registros/configuración publicada y dan baja lógica motivada con historial. Año/nombre publicados permanecen protegidos para no reasignar datos históricos. Configuración/publicación del ciclo y opt-in de regla nueva siguen administrativos. Ítems anuales fijos (Física 1/2, Académica, Jefe/Comandante y grupo Psicométricas), activaciones versionadas/motivadas; desactivar conserva notas y habilitación personal, bloquea acciones nuevas y excluye del avance operativo. Psicométricas sin instrumento aprobado no se activan; no hay formularios nuevos. Baja no cambia estado original ni cierra con instantánea, retira listas operativas y mantiene consulta histórica. ACTIVO operativo único excluye retiradas.

Cálculo provisional exacto ACUMULADO_TRES_V2 en registro inmutable separado de PROMEDIO_TRES_V1, una gestión por año para impedir doble imputación. Académica suma participaciones finalizadas vigentes por año personal, tope 100/detalle sin tope/revisión/historial; cero finalizado válido, sin finalizaciones pendiente. Corrección cambia cómputo del año sin sumar versiones anteriores. Física promedia dos resultados programados y conserva No cumplida=0 al reprogramar; Desempeño promedia dos notas configuradas. Conjunto de tres componentes iguales, fracciones exactas y solo redondeo final mitad arriba a dos decimales; faltantes/desactivaciones necesarios dejan No disponible. Fuentes referenciadas y consultas en transacción consistente; no se escriben resultados publicados/instantáneas. Nuevas notas globales académicas bloqueadas bajo v2; anteriores conservadas como historial. Instructor sin datos numéricos/resultados/autores/motivos, solo proyección propia de estado/habilitación/activación/avance.

Menú agrupado y sin incisos repetidos de notas: Personal/operaciones, Evaluación anual (Gestiones/Catálogo/Habilitación y avance/Notas y resultados), cuenta administrativa aparte. Catálogo sin creación de períodos ni asignaciones anteriores duplicadas; APIs previas conservadas y notas antiguas accesibles por enlace contextual. Disponibilidad del catálogo diferenciada de activación anual. Revisada también serialización de asignación/habilitación psicométrica legada para evitar carreras con bajas/activaciones anuales.

Migración local respaldada v19→v20: `instance/backups/sicose-20261013-pre-v20-57e238bb.sqlite3`, **35 tablas previas comparadas/preservadas**, dos inicializaciones, versión 20, quick_check=ok y FK=0. Cuatro tablas nuevas vacías; sin reglas, bajas ni activaciones inferidas, seed o dependencias nuevas. `.venv`, `.env`, fotos y cambios locales anteriores conservados.

Pruebas: once nuevas de cálculo/gestiones, además de las seis físicas previas y 87 del módulo principal. Suite intermedia 103 con un fallo HTTP psicométrico (404 por un rechazo anticipado, en vez de 403); corregido sin permitir la operación y prueba específica aprobada en 0,615 s. Suite posterior **104 aprobadas en 90,025 s**. Fixtures iniciales duplicaban persona/curso y se corrigieron; no cambiaron reglas de negocio. Repetición de cierre tras serializar APIs legadas se registra en la evidencia final de [5B.2](docs/14_calculos_y_gestiones.md).

36 escenarios Chromium con API simulada (32 de ambos gestores en cuatro pantallas, cuatro propios del Instructor), 360/1447 px y claro/oscuro: edición/baja/activación anual, catálogo separado, menú sin duplicados, componentes exactos/detalle/tope y privacidad. Capturas inspeccionadas; corregido resumen provisional móvil y separación visual de retiradas, escenarios repetidos sin errores JavaScript ni desbordes. Comprobación HTTP adicional de tabla/PDF con regla v2: Académica 100.00 Finalizada, PDF 200/privado no-store. No se realizó nueva inspección visual del PDF. Artefactos ignorados en `.tmp/calculos-ui/`, logs de suite y `.tmp/calculos-migracion.json`.

[docs/14_calculos_y_gestiones.md](docs/14_calculos_y_gestiones.md), README/AGENTS/plan/modelo y documentos de reformulación/formación/revisión actualizados. Pendientes **5B.3 publicación/republicación** y **5B.4 cierre/reapertura con instantáneas**; no se declara cerrada Fase 5B ni aceptación operativa/institucional. Psicometría/IA/piloto conservan sus condiciones.


Cierre de verificación de 5B.2 — 2026-10-13: tras serializar también las APIs legadas de asignación/habilitación, suite completa repetida: **104 pruebas aprobadas en 158,822 s**, log `.tmp/calculos-suite-cierre.log`. Compilación Python, sintaxis de cinco JavaScript, enlaces locales de los once documentos revisados y git diff --check correctos. Relectura de base local en modo solo lectura: v20, quick_check=ok, FK=0. Las 104 pruebas en 90,025 s anteriores son evidencia intermedia; resultado de cierre vigente es 104/158,822 s. No se activó cálculo v2 en la base local ni se adoptaron datos automáticamente.


## 2026-10-13 — 5B.3 Publicación y republicación (v21)

Continuación tras 5B.2. Confirmado por el solicitante: publicación parcial permitida con pendientes sin ceros inferidos; ocultar valores publicados mientras su evaluación esté deshabilitada o Gestión retirada. Correcciones conservan versión/fecha anterior hasta republicar. Sin nuevos permisos de configuración/cierre ni habilitación psicométrica.

Administrador/Jefe revisan y publican/republican por persona/Gestión en Notas y resultados: cuenta/gestión activas no retiradas, configuración publicada, regla v2 y fuentes habilitadas. Firma de fuentes/revisión/motivo, valores resueltos en servidor, BEGIN IMMEDIATE, cadena única bajo concurrencia y versiones inmutables; sin cambios no se duplican filas/auditoría. Parcial admite pendientes explícitos; una republicación puede rectificar hacia pendiente/cursos retirados sin fabricar cero. Componentes deshabilitados conservan ocultos su contenido/fecha anteriores aunque se republice otro; rehabilitación muestra última versión publicada, no la corrección vigente.

Snapshot y fuentes solo físicas/formación; publicación no consulta Desempeño ni copia el objeto de cálculo conjunto. Cambiar Desempeño no cambia firma/fecha/versión ni genera una publicación. Instructor recibe lista positiva propia sin fuentes/IDs de notas/firmas/motivo/actor/conjunto. Desempeño excluido también de filas y denominador del avance propio. Mis evaluaciones separa estados vigentes de notas publicadas; Mis cursos separa asignaciones actuales de puntos/finalizaciones publicados por Gestión. Ocultación en servidor en ambas APIs por deshabilitación individual/anual o baja de Gestión; cuentas inactivas sin acceso. No PDF propio, notificaciones externas, psicometría ni cierre/reapertura.

Migración aditiva v20→v21 tras respaldo `instance/backups/sicose-20261013-pre-v21-2724fe76.sqlite3`: una tabla nueva vacía, **39 tablas previas preservadas**, dos inicializaciones, versión 21, quick_check=ok y cero infracciones FK. Sin publicaciones/reglas inferidas, seed ni dependencias nuevas. `.venv`, `.env`, fotos y todos los cambios locales previos conservados.

Verificación nueva: **114 pruebas aprobadas en 221,488 s**, diez específicas de publicación. Cobertura parcial/cero/No cumplida/promedio/tope, conservación de valores/fechas, cambio de año/rectificación a pendiente, versiones ocultas al republicar otros componentes, ocultación/reactivación/baja, privacidad sin estados/denominador de Desempeño, ausencia de efectos de Desempeño, vistas obsoletas/concurrencia inicial/republicación, CSRF/inactivos/campos arbitrarios/historial/migración repetida. Primera suite de 112 en 207,464 s y diez específicas en 28,367 s aprobadas; suite final incluye las ampliaciones posteriores.

16 escenarios Chromium con API simulada, tres roles, 360/1447 px y claro/oscuro, vista previa/republicación/historial y consulta propia en evaluaciones/cursos, sin errores/desbordes; capturas inspeccionadas y escenarios repetidos tras ajustes. Logs `.tmp/publicaciones-suite-final.log`, `.tmp/publicaciones-ui/`, `.tmp/publicaciones-migracion.json` ignorados por Git. README/AGENTS/plan/modelo/arquitectura/reglas/formación/revisión y [docs/15_publicacion_notas.md](docs/15_publicacion_notas.md) alineados; evidencias anteriores conservan su contexto.

Pendiente **5B.4 cierre/reapertura con motivo, incompletos e instantáneas**, aceptación operativa/institucional y requisitos del piloto. No se declara cerrada Fase 5B.


Revisión de privacidad al cierre de 5B.3: respuestas de publicación/vista previa/historial y propias con puntajes marcadas `Cache-Control: private, no-store`; prueba HTTP añadida a los casos existentes. Compilación Python, sintaxis de cinco JavaScript, 107 enlaces locales en doce documentos y diff correctos. La suite de cierre se repite con esta protección; su resultado se registra a continuación.


Cierre final de 5B.3 — 2026-10-13: **114 pruebas aprobadas en 123,012 s** tras añadir private/no-store a publicaciones y respuestas propias numéricas. Resultado vigente en `.tmp/publicaciones-suite-cierre.log`; las 114 en 221,488 s anteriores son evidencia intermedia. Compilación Python, cinco JavaScript, 107 enlaces locales en doce documentos y git diff --check correctos. Base local en lectura: v21, quick_check=ok, FK=0, publicaciones=0. No se publicaron datos automáticamente.

### 2026-10-13 — Selección de participantes mediante casillas

- El modal «Asignar participantes» de cursos sustituye la lista de selección múltiple por casillas junto a nombre/código, con contador accesible. Permite marcar varias personas sin Ctrl y bloquea el envío vacío o repetido mientras se guarda.
- Conserva el filtro de activos sin participación previa, el contrato `voluntario_ids`, la autorización/CSRF del backend y la selección si falla la solicitud. Sin migración ni modificación de datos locales.
- Verificación de esta corrección: ocho escenarios de navegador con API simulada (Administrador/Jefe, 360/1447 px, claro/oscuro), sin errores JavaScript ni desbordamiento del modal; selección múltiple, teclado, desmarcado, exclusión de inactivos/asignados, envío y recuperación tras error correctos. Sintaxis de cursos.js y git diff --check correctos. Prueba backend de asignación/formación ejecutada por separado; no se repitió la suite completa.
- Resultado backend de esta corrección: 1 prueba aprobada en 0,794 s (`test_formacion_asignacion_atomica_snapshots_historia_y_privacidad`).

### 2026-10-13 — Activar/desactivar Instructores Voluntarios

- Solicitud confirmada por el usuario: Administrador y Jefe de Personal pueden poner ACTIVO o INACTIVO a Instructores Voluntarios ya admitidos. El directorio muestra Activar (icono de confirmación) en inactivos y Desactivar en activos, con nombre accesible, confirmación y bloqueo durante el guardado. El Jefe sigue editando perfiles activos; puede activar primero un inactivo.
- Nueva API PATCH `/api/instructores-voluntarios/<id>/estado` con estado deseado y anterior, autorización backend, CSRF, validación estricta y transacción BEGIN IMMEDIATE. Conflicto devuelve 409; cambio nulo no duplica auditoría. La auditoría registra actor, identificador de persona y transición en acción, resultado y fecha UTC; sin credenciales. Se conservan POST de desactivación heredados con las mismas restricciones.
- PENDIENTE/RECHAZADO no se convierten en cuentas admitidas mediante este flujo. La aprobación administrativa sigue separada. El alcance es global SBRAB, independiente de instructor_id histórico.
- Cada transición invalida sesiones previas usando password_version existente; conserva hash de contraseña, identidad, asignaciones e historial. Reactivar exige nuevo login y no crea habilitaciones ni publica resultados. Sin migración ni modificación de la base local.
- Verificación específica final: tres pruebas aprobadas en 2,235 s (roles, alcance global, CSRF, estados inválidos/pendientes/rechazados, conflictos, cambio nulo, auditoría, conservación de perfil/hash, bloqueo de login inactivo y sesiones antiguas tras reactivar). Ocho escenarios de navegador con API simulada (dos roles, 360/1447 px, claro/oscuro), sin errores ni desbordamiento: activar/desactivar, cancelar, conflicto y CSRF. Compilación Python, sintaxis app.js y git diff --check correctos. Se conserva todo el trabajo local anterior.
- Cierre de verificación de esta entrega: suite completa **117 pruebas aprobadas en 238,180 s**; sintaxis de los cinco JavaScript, compilación Python, 56 enlaces locales en cuatro documentos afectados y git diff --check correctos. Los ocho escenarios visuales se ejecutaron también tras ajustar el estilo del icono Activar. No se efectuó migración, seed ni cambio de estado en la base local.

### 2026-10-14 — 5B.4: cierre/reapertura con instantáneas (v22)

- Administrador revisa/cierra/reabre Gestiones con motivo. Administrador/Jefe consultan incompletos e historial por versión. Instructor sin acceso a firmas, Desempeño/conjunto ni instantáneas administrativas. Cierre no publica/republica ni altera las versiones visibles de 5B.3.
- Cierre atómico de estado, cabecera e instantáneas por persona con fuente/revisión/autoría, identidad mínima, configuración/regla, faltantes y resultado exacto como fracción de centésimas/final mitad arriba. Permite incompletos solo confirmados; no infiere ceros ni redistribuye. Firma detecta fuentes/cuenta cambiadas desde revisión y enlace anterior evita ramas; BEGIN IMMEDIATE serializa cierre/reapertura. Cada recierre conserva su versión/enlace sin reemplazar anteriores.
- Reapertura motivada del último cierre, sin segundo activo, conservando configuración, regla y cierres previos. Gestión retirada no se reabre; historial sigue consultable. Notas/físicas/habilitaciones/activaciones/publicaciones permanecen bloqueadas en CERRADO; se añadió comprobación al cambio de habilitación heredado. Lectura de cálculo cerrado usa snapshot, no cursos actuales; persona sin snapshot queda FUERA_DEL_CIERRE.
- Decisión confirmada durante esta entrega: bloquear finalizaciones/correcciones de formación si el año anterior o nuevo está cerrado, incluido desfinalizar/mover de año, hasta reapertura administrativa. Catálogo/asignaciones sin finalización separados del cálculo; no se congelan cuentas, asistencia u operaciones.
- Compatibilidad: permite cierre documental de históricos ACTIVO sin opt-in v2, con datos originales y resultado conjunto ausente. PROMEDIO_TRES_V1 intacta, sin adopción. Primera activación de otra regla bloqueada después de un cierre. Históricos ya CERRADO sin instantáneas no se reabren por este circuito; no se fabrican cierres retroactivos.
- Migración aditiva v21→v22, respaldo `instance/backups/sicose-20261014-pre-v22-3289032b.sqlite3`, 40 tablas previas comparadas/preservadas, dos inicializaciones, v22, quick_check=ok y FK=0. Nuevas cierres_5b/instantaneas_cierre_5b/reaperturas_5b vacías, FK restrictivas y UPDATE/DELETE bloqueados. No seed, dependencias, cierres ni publicaciones automáticos. Entorno, fotos e historial local preservados.
- Verificación: suite completa **127 pruebas aprobadas en 257,841 s**; diez específicas de cierres aprobadas en **12,635 s** tras ampliar comprobación de habilitación heredada (primera ejecución final específica: 10/11,452 s). Incluye permisos, CSRF, inactivos, fuentes obsoletas, cierres/reaperturas concurrentes, incompletos, cero confirmado, exactitud, historial inmutable, privacidad, bloqueo académico en origen/destino y migración repetida. Ocho escenarios Chromium con API simulada (Administrador/Jefe, 360/1447 px, claro/oscuro), sin errores/desbordes, revisión/cierre/reapertura/recierre/consulta histórica y rechazo de fuentes obsoletas; capturas inspeccionadas. No nuevo ensayo PDF.
- Documentación alineada en README/AGENTS/plan, arquitectura/datos, reformulación, formación, revisión, cálculos y publicación; nueva especificación docs/16_cierres_reaperturas.md. Logs ignorados `.tmp/cierres-suite-final.log`, `.tmp/cierres-tests-cierre.log`, `.tmp/cierres-migracion.json`, `.tmp/cierres-ui/`.
- Entrega técnica completada, sin declarar cerrada Fase 5B. Pendientes aceptación operativa/institucional, política de colisiones, tratamiento explícito de históricos ya cerrados sin instantáneas y requisitos del piloto.
- Controles finales de 5B.4: compilación Python, sintaxis de cinco JavaScript, 116 enlaces locales en doce documentos y git diff --check correctos. Nueva consulta de base solo lectura confirmó v22, quick_check=ok, FK=0 y las tres tablas nuevas vacías. La suite completa y la ejecución específica se distinguen arriba; no se atribuyen las evidencias anteriores al 2026-10-14.

### 2026-10-14 — Complemento de Fase 5B: históricos y validación integral (v23)

- Estado inicial Git limpio; se preservaron entorno, base, fotos e historial. Se contrastó el pendiente histórico de 5B.4 con rutas, esquema y pruebas antes de editar.
- Decisión confirmada por el usuario: permitir reapertura excepcional de períodos históricos CERRADO sin instantáneas, exclusivamente al Administrador, con motivo y constancia explícita de ausencia de instantánea original. No presentar datos actuales como cierre antiguo ni adoptar notas/cambiar reglas.
- Nuevo módulo historicos_5b.py: revisión/firma de evidencia, reapertura atómica sin segundo activo, auditoría y consulta administrativa privada no-store. Evidencia JSON versionada con identidad mínima/fuentes disponibles, sin respuestas psicométricas ni credenciales. Estado NO_RECONSTRUIDO y fecha original no acreditada. Una evidencia por Gestión con FK restrictivas e inmutabilidad UPDATE/DELETE. Jefe consulta, no confirma; Instructor sin acceso.
- Cierres posteriores referencian la reapertura excepcional; su primer cierre es el primero con instantáneas, no un cierre anterior inventado. Reapertura ordinaria a partir de entonces. Configuración/regla existentes conservadas; opt-in nuevo bloqueado después de esta excepción. Una v2 preexistente mantiene sus fuentes; notas históricas ajenas no se adoptan. Publicaciones/fechas propias intactas.
- Interfaz en Gestiones (año): Administrador «Reabrir histórico sin instantánea», Jefe «Revisar histórico sin instantánea», ambos «Evidencia de reapertura histórica» tras el evento. Motivo y casilla obligatorios, error por fuentes obsoletas/concurrencia, evidencia consultable tras correcciones y nuevo cierre.
- Se preparó docs/17_validacion_integral_5b.md con matriz de cobertura, recorrido humano por tres roles, resultados esperados y acta pendiente. No inventa participantes, firmas ni aceptación institucional. Prueba integral adicional verifica No cumplida=0/reprogramación, Física=40, Académica=75, Desempeño=85 y conjunto=66,67; tras corregir curso a 100, conjunto=75,00 y versión publicada anterior hasta republicar, con primer cierre intacto.
- Migración aditiva v22→v23: respaldo `instance/backups/sicose-20261014-pre-v23-c8c8c9bf.sqlite3`, 43 tablas previas comparadas/preservadas, dos inicializaciones, v23/quick_check=ok/FK=0 y nueva tabla vacía. Sin reapertura, notas/publicaciones, reglas automáticas, seed o dependencias nuevas.
- Pruebas específicas: ocho aprobadas en 20,885 s; diez de regresión de cierres aprobadas en 24,903 s. Primera pasada completa: 135 pruebas en 308,357 s con dos fallos de aserciones antiguas que esperaban v22; se actualizaron a v23 y se repitió la suite. No se atribuyen resultados v22 a esta entrega.
- Revisión visual: ocho escenarios Chromium con API simulada, Administrador/Jefe, claro/oscuro y 360/1447 px: motivo/constancia, fuentes obsoletas, acceso por rol, evidencia sin resultado antiguo y primer cierre auténtico. Sin errores ni desbordes, capturas inspeccionadas; sin nuevo ensayo visual PDF.
- Evidencias ignoradas: `.tmp/historicos-tests-final.log`, `.tmp/historicos-cierres-regresion.log`, `.tmp/historicos-suite-final.log` (primera pasada), `.tmp/historicos-suite-cierre.log` (repetición), `.tmp/historicos-migracion.json`, `.tmp/historicos-ui/`.
- Pendientes: ensayo y aceptación operativa humana, aprobación institucional/privacidad y requisitos del piloto; política de colisiones del personal separada. No se declara cerrada Fase 5B ni se habilita psicometría/IA.
- Cierre de esta entrega v23: **135 pruebas aprobadas en 301,157 s** en la repetición completa (`.tmp/historicos-suite-cierre.log`), con ambas aserciones de versión corregidas. Compilación Python, sintaxis de cinco JavaScript, 122 enlaces locales en once documentos y git diff --check correctos. Relectura local v23/quick_check=ok/FK=0 y tabla nueva vacía. Ocho escenarios visuales también repetidos tras precisar que la evidencia no acredita fecha/resultados del cierre antiguo. Sin nuevas migraciones o acciones operativas posteriores al respaldo/verificación descritos.

### 2026-10-14 — Ensayo integral de 5B con servidor real

- Se preservó todo el trabajo local pendiente y se revisó la guía de aceptación antes del ensayo. No se cambió el producto ni el esquema v23.
- Flask/Werkzeug servido exclusivamente en 127.0.0.1, base DEMO temporal con datos sintéticos y tres sesiones de navegador. Sin intercepción de HTTP ni respuestas simuladas. El aislamiento bloqueó la primera conexión; servidor y navegador se ejecutaron en el mismo entorno autorizado fuera del aislamiento. Sin servicio externo ni uso de la base de trabajo.
- Doce comprobaciones funcionales satisfactorias; 25 peticiones API de comprobación explícitas más tráfico real de interfaz. UI real para login, publicación/republicación, cierre/reapertura y excepción histórica; correcciones/comprobaciones adicionales por HTTP autenticado real. Resultado conjunto 66,67→75,00 tras corrección, versión publicada anterior hasta republicar y primera instantánea intacta. Permisos 403, bloqueo académico cerrado 409, inactivo/sesión anterior 401 y ausencia de segundo activo verificados.
- Doce escenarios visuales de Administrador/Jefe/Instructor, 360/1447 px y claro/oscuro, sin errores JavaScript ni desbordes en el alcance recorrido. Capturas finales estabilizadas y revisadas. Sin nuevo ensayo visual PDF, carga ni despliegue productivo.
- El arnés temporal cerró explícitamente la conexión SQLite para la limpieza en Windows y capturó sin animaciones para evitar transiciones. No fueron cambios del producto. Ejecución final terminada limpiamente: servidor detenido, base temporal final retirada; DEMO final v23/quick_check=ok/FK=0, cierres=3, instantáneas=3, reapertura ordinaria=1, excepcional=1 y publicaciones=2.
- Base de trabajo consultada solo en lectura, datos anteriores comparados con respaldo v22 sin cambios; meta preservada en v23 e integridad correcta, evidencia histórica de trabajo vacía. Sin nueva migración/seed/dependencias ni cambios en notas, estados o publicaciones locales; entorno/fotos/historial conservados.
- Nuevos informe docs/18_ensayo_servidor_real_5b.md y actualización de guía/continuidad. Evidencias ignoradas `.tmp/ensayo5b/resultado.json`, `base-final.json`, logs y capturas. Suite previa 135/301,157 s es evidencia histórica de la entrega anterior, no repetida al no cambiar código del producto.
- La aceptación humana/institucional permanece pendiente; no se declara cerrada Fase 5B ni se inventan firmas o responsables.
- Controles finales del ensayo real: compilación Python, cinco JavaScript, 91 enlaces locales en seis documentos y git diff --check correctos. `.tmp/ensayo5b/preservacion.json` confirma 43 tablas anteriores preservadas, v23/quick_check=ok/FK=0 y tabla histórica de trabajo vacía. Estado de revisión humana consultado al solicitante; sin respuesta aún no se registra aceptación.

### 2026-10-14 — Aceptación operativa de Fase 5B comunicada por el solicitante

- Ante la consulta de aceptación, el solicitante respondió explícitamente: «Ya realicé el ensayo humano y acepto operativamente 5B». Se registra esa declaración como aceptación operativa del alcance 5B.1–5B.4 y compatibilidad histórica descrito en la guía/informe.
- Actualizados registro de aceptación, README, AGENTS y resumen vigente del plan. La aceptación se fundamenta en la declaración humana, no se deduce de pruebas automatizadas. Los estados pendientes anteriores se conservan como historia y quedan sustituidos en lo operativo por esta confirmación.
- No se aportaron identidad nominal/cargo, fecha detallada del ensayo, revisión Git exacta, desglose por caso ni acta institucional firmada. No se inventan esos datos ni incidencias/resoluciones. Aprobación institucional y piloto siguen pendientes; no se declara cierre global de Fase 5B ni aceptación de otras fases.
- Cambio exclusivamente documental: sin nueva ejecución funcional, migración, cambio de código, notas o estados de la base. Evidencias técnicas anteriores conservan sus fechas y resultados.


### Espacio del Jefe y reportes — 2026-10-14 (v23)

Navegación del Jefe organizada en Inicio, Personal y Operaciones y Evaluación Anual: Gestión, Evaluaciones, Notas y Resultados, Reportes. Dashboard global con tarjetas y gráficos descriptivos; Gestión separada de activación anual e habilitación individual. Activación/configuración del ciclo y regla de cálculo siguen exclusivas del Administrador (confirmado). Administrador/Jefe ahora crean y editan operaciones y asignan participantes, incluidos lotes por checkbox con validación íntegra; sustituye restricciones antiguas de eventos solo administrativos. Centro de PDF existentes y nuevos reportes de formación personal finalizada y operaciones con participantes, solo Administrador/Jefe, sin contactos/observaciones/motivos privados. [Alcance y verificación](docs/19_espacio_jefe_reportes.md). Sin migración ni adopción de históricos.


Verificación final del 2026-10-14: **138 pruebas aprobadas en 354,019 s**; cuatro dirigidas finales en 10,106 s y una del Inicio administrativo en 0,664 s. Treinta escenarios visuales con Flask real/base DEMO, 360/1447 px y ambos temas, sin errores JavaScript ni desbordes; capturas revisadas. Dos PDF nuevos, caso vacío y paginación de 80 filas/11 páginas renderizados e inspeccionados. Compilación Python, seis JavaScript, 159 enlaces en 22 documentos y git diff --check correctos. Sin migración, nuevas dependencias ni seed de la base de trabajo; v23/quick_check=ok/FK=0 en consulta solo lectura. Entorno, fotos, historial y trabajo local previo conservados. Servidores DEMO detenidos y sus bases temporales retiradas. La aceptación operativa previa de 5B no se extiende automáticamente a esta reorganización; aprobación institucional/piloto conservan sus pendientes.
