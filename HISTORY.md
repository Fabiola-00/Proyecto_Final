# Historial de cambios y configuraciones — SICOSE

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
