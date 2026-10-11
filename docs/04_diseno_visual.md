# 04. Diseño visual

## Dirección

Interfaz en español, clara, sobria y adaptable. Como inspiración funcional general se observó el sitio público de Evaluar (https://www.evaluar.com/), que presenta navegación de producto, accesos para candidatos/empresas y módulos de evaluación. SICOSE tomará solo patrones comunes de claridad, navegación y organización por módulos; no usará marca, textos, ilustraciones, composición ni interfaz propietaria de Evaluar.

## Identidad

- Azul primario institucional: `#1D1BBE` para navegación y acciones principales.
- Naranja institucional: `#F57B1A` para acentos y estados que requieran atención, no como único indicador.
- Neutros: fondo gris muy claro, superficies blancas, texto carbón y bordes suaves.
- El emblema SBRAB proporcionado se muestra en la parte superior de la barra lateral junto a la identificación SICOSE.
- Tipografía de sistema; jerarquía por tamaño, peso y espaciado. Contraste y foco visible accesibles.

## Ancho y adaptación de pantallas

Corrección del 2026-10-10: el contenedor general ocupa el 100% del ancho. Los paneles reservan únicamente el ancho real de la barra lateral (expandida o plegada); en móvil, el contenido ocupa toda la pantalla y el menú se superpone. Cabecera y contenido usan márgenes internos pequeños y responsivos. Acceso, registro y errores también utilizan el ancho disponible, sin límites centrales de 42/66rem. Tablas anchas desplazan dentro de su contenedor, sin extender la página.

Verificación con Chromium sobre HTML renderizado por Flask con datos sintéticos: 13 pantallas en cinco anchos (360, 760, 768, 1447 y 1920 px), con menú expandido/plegado, más error de acceso en los cinco anchos: 135 comprobaciones de ancho y desbordamiento correctas. Se inspeccionó además una captura del dashboard oscuro con menú plegado. Esta comprobación de distribución no sustituye aceptación operativa de flujos ni prueba completa de contenido dinámico.

## Estructura de pantallas

- Inicio de sesión y solicitud de registro/aprobación.
- Cascarón autenticado: barra lateral colapsable, encabezado con período activo y menú de cuenta; navegación cambia según rol.
- Dashboard de administrador: resumen general y acceso global para administrar todas las cuentas, Jefes de Personal, Instructores Voluntarios y evaluaciones.
- Dashboard de Jefe de Personal: solo su equipo de Instructores Voluntarios registrados y activos, evaluaciones tomadas y resultados autorizados, notas no psicométricas y controles para habilitar/deshabilitar pruebas por voluntario.
- Dashboard de Instructor Voluntario: edición de correo y foto propios, evaluaciones propias completadas y pendientes y resumen de estado/avance, sin notas, resultados individuales ni observaciones.
- Perfil y detalle: datos, cursos, experiencia, asistencia, evaluaciones y observaciones según permiso.
- Formularios de calificación con validación en línea y confirmación antes de guardar.
- Tablas con búsqueda, filtros, paginación y vistas compactas para móvil.
- Estados vacíos, error, carga, no autorizado y confirmación de acción con mensajes directos.

## Implementación de Fase 3

Se implementó una plantilla compartida con barra lateral condicionada por rol, encabezado, período actual, identidad de cuenta, estado activo de navegación y salida de sesión. Hay una página diferente para cada rol y el inicio redirige según el rol autenticado. Las tarjetas usan cifras leídas de SQLite: administrador ve perfiles activos, cuentas pendientes y períodos; Jefe de Personal ve únicamente Instructores Voluntarios asignados y sus asignaciones incompletas; Instructor Voluntario ve sus propias asignaciones y capacitaciones. También están las primeras pantallas para administrar cuentas de instructor y perfiles/solicitudes de voluntario.

El bloque de perfil de la barra lateral muestra la foto privada de la cuenta para Administrador, Jefe de Personal e Instructor Voluntario; si no hay foto, conserva el avatar con inicial. La imagen se solicita a la API autenticada de perfil.

El panel inicial de administración incluye tarjetas de Jefes de Personal e Instructores Voluntarios con sus fotos, estado e inicial de respaldo cuando aún no hay imagen. La navegación de Configuración abre la edición del nombre, foto y contraseña del administrador; al cambiar la contraseña solicita la clave actual y termina la sesión para volver a ingresar.

Estas pantallas y contadores son una base, no la implementación completa de todos los permisos descritos arriba. Con Fase 5 se agregan registros de asistencia, notas no psicométricas y estados de evaluaciones del Instructor Voluntario. Mi perfil permite al Instructor Voluntario editar exclusivamente correo y foto. Continúan pendientes los formularios/intentos psicométricos, que permanecen bloqueados por falta de instrumentos autorizados. Las funciones no disponibles deben mostrarse como pendientes.

## Implementación de Fase 5

Administración cuenta con pantallas iniciales para períodos, catálogo y asignaciones. Jefe de Personal/Administrador pueden marcar asistencias, registrar capacitaciones y crear/corregir notas no psicométricas conservando versiones anteriores; Jefe de Personal queda limitado a Instructores Voluntarios activos asignados. Instructor Voluntario ve la lista de evaluaciones completadas/pendientes sin notas ni observaciones. Los candidatos psicométricos no están aprobados en `docs/06_pruebas_psicometricas.md`, por lo que se bloquea su activación y no se muestran formularios, intentos o reinicios operativos.

Asistencias tiene una lista de estado por persona y fecha, con opciones Asiste, Atraso, Permiso y Falta; la actividad se conserva como referencia de la gestión. El historial se filtra por persona y permite consultar la última fecha con registros o un rango. Capacitaciones o Cursos es una sección aparte para Administrador y Jefe de Personal, con listado, alta y edición vinculada a `capacitaciones`; no permite borrado físico.

La barra lateral se convierte en menú móvil con control accesible por teclado y también puede plegarse en escritorio para liberar espacio. El estado plegado se recuerda en el navegador; la navegación sigue identificable mediante nombres accesibles. El selector de tema permite cambiar entre modo claro y oscuro y conserva la preferencia local. Ambos temas mantienen contraste, foco visible y los colores institucionales como identidad de las acciones y acentos. Los estados usan texto además de color.

## Responsividad e interacción

En pantalla pequeña, barra lateral pasa a menú accesible; tablas se convierten en tarjetas o permiten desplazamiento horizontal señalizado; campos y botones ocupan ancho cómodo. No comunicar estados únicamente con color. Etiquetar campos, asociar errores con controles, permitir navegación por teclado y respetar `prefers-reduced-motion`.

## Confidencialidad en UI

El panel de Instructor Voluntario muestra únicamente estado y avance de sus evaluaciones; nunca calificaciones, resultados individuales, observaciones ni respuestas psicométricas. Jefe de Personal ve resultados solo de voluntarios bajo su ámbito, pero no puede modificar las calificaciones psicométricas; solo puede habilitar/deshabilitar pruebas específicas. Administración tiene alcance global. Evitar nombres/identificadores innecesarios en reportes consolidados. Ocultar acciones por rol mejora claridad, pero el backend mantiene el control real. Mostrar que los pesos y puntajes son una configuración institucional pendiente de aprobación; nunca rotularlos como baremos clínicos o científicamente validados.

## Edición de directorios en modal — 2026-10-10

La edición de perfiles y el restablecimiento de contraseña en directorios de Instructores Voluntarios y Jefes de Personal usan un diálogo nativo centrado; los formularios quedan fuera de las celdas de acciones. Dos columnas en escritorio, una en móvil, desplazamiento interno, título de persona, cierre/cancelación y Escape con retorno de foco. Los errores se presentan dentro del diálogo; guardar correctamente lo cierra y actualiza el listado. Los campos de contraseña y archivo se vacían al cerrar. Se conservan autorizaciones y endpoints existentes.

Verificado en Chromium en seis escenarios (Jefe/Administrador en directorio de Instructores Voluntarios y administración de Jefes, a 360/1447 px) con datos sintéticos/API simulada: tabla estable al abrir, modal dentro de pantalla, Escape y foco, error visible y cierre tras guardado.

La columna de acciones de los directorios permanece fija al borde derecho durante el desplazamiento horizontal. Botones de edición/restablecimiento/desactivación apilados verticalmente y ajustados al ancho de la celda, para evitar recortes en escritorio o móvil.

### Corrección vigente — Registro de cursos (2026-10-10, v12)

La pantalla “Capacitaciones y Cursos” registra cursos independientes de personas. Incluye nombre, tipo (Capacitación, Especialización, Actualización, Taller, Seminario (Webinar)), entidad organizadora, inicio/fin, estado (Próximo, En curso, Finalizado) y observaciones opcionales. Nombre, tipo y estado obligatorios para registros nuevos; fechas/entidad opcionales; fin requiere inicio y no puede precederlo. Estado se elige manualmente, sin deducirlo de fechas. Administrador registra/edita; Jefe consulta el catálogo según permisos ya acordados. Edición mediante modal responsivo con datos precargados y errores en el modal.

Se retiraron de esta pantalla el selector de Instructor y el formulario de asignación. Los registros personales históricos, sus vínculos y APIs se conservan; no hay interfaz nueva de asignación en esta entrega. “Mis cursos” sigue consultando historial personal sin observaciones. Las observaciones del catálogo son distintas del historial personal y solo se muestran a Administrador/Jefe.

Migración v12 aditiva: campos nuevos nullable en cursos, sin inferir tipo, estado ni fechas de históricos. Respaldo SQLite previo, datos de 23 tablas anteriores preservados, inicialización repetida, quick_check=ok y FK=0. 59 pruebas aprobadas en 42,354 s (ejecución final); cuatro escenarios Chromium con API simulada, Administrador/Jefe a 360/1447px, opciones exactas y edición modal correctas. Compilación Python, sintaxis JavaScript y diff comprobados.

### Entrega vigente — Asistencia, correcciones, calendario y reporte (2026-10-10, v13)

- Administrador consulta/registra/corrige asistencia; Jefe solo personal activo asignado. La llamada muestra nombre del responsable autenticado, gestión anual de la fecha seleccionada y fecha; conserva actividad obligatoria. Los cuatro estados exactos son Asiste, Atraso, Permiso y Falta. Llamada nueva inicia todas las filas en Falta; al elegir fecha/actividad existente se cargan sus estados guardados para corregirlos.
- Clave única persona/fecha/actividad: guardar otra vez actualiza el mismo registro. Corrección conserva estado anterior/nuevo, actor y fecha UTC en historial_asistencias mediante trigger; cambios se auditan. Repetir el mismo estado no crea corrección ni sustituye al último responsable. No se permiten cambiar identidad/fecha/actividad mediante el PATCH de corrección. Históricos no se borran ni se fabrican correcciones anteriores.
- Instructor consulta solo su calendario anual y totales de los cuatro estados, sin datos de terceros ni observaciones ni edición. El día puede tener varias llamadas; totales cuentan registros, no días calendario. Sin registro no se considera Falta.
- Reporte matricial por rango inclusivo de fechas, sin materia ni filtros adicionales. Columnas por fecha/actividad, código y nombre, cuatro totales y porcentaje. Asiste y Atraso cuentan como asistencia; Permiso excluido: (Asiste + Atraso)/(Asiste + Atraso + Falta), redondeado a dos decimales; sin denominador, No disponible. Es un indicador operativo aprobado para esta entrega, no una nota ni promedio oficial de Fase 5B. Jefe exporta solo ámbito activo asignado; Administrador todo su alcance; Instructor no exporta reporte administrativo.
- PDF imprimible horizontal: matriz dividida en bloques de hasta ocho llamadas, filas paginadas y cabeceras repetidas, sin perder columnas. Carimbo SBRAB en cada página con escudo, nombre completo institucional y generación en hora de Bolivia; paginación, rango, leyenda y fórmula visibles. Sin observaciones; descarga privada no-store y auditoría mínima.
- Migración local v13 tras respaldo: 23 tablas anteriores preservadas, inicialización repetida, quick_check=ok y cero infracciones FK. Entorno, secretos y base existente conservados. Aceptación operativa del solicitante pendiente; Fase 5A aún requiere revisar integralmente cursos/notas y sus casos de corrección. Retención/privacidad y autorización institucional siguen pendientes antes del piloto.


### Cabecera de llamada de asistencia (2026-10-10)

Responsable, Gestión, Actividad y Fecha se presentan, en ese orden, en una sola fila en escritorio; en tablet se distribuyen en dos columnas y en móvil en una para mantener legibilidad. Actividad se selecciona entre Ordinaria, Actividad Externa, Terreno y Operación. Los textos de actividades históricos se conservan en registros, historial y reportes; esta corrección de interfaz no reclasifica datos anteriores.


La tabla de llamada de asistencia presenta únicamente Nombre completo, Código, Estado y Asistencia. El estado de la cuenta se muestra con texto orientado horizontalmente: ACTIVO en verde e INACTIVO en rojo, además de su etiqueta textual. La llamada sigue limitada al personal activo autorizado; el estilo de INACTIVO no habilita registrar asistencia de cuentas inactivas.


### Directorio de Instructores — revisión vigente (2026-10-10)

Columnas: Nombre completo, Código, Grado, Especialidad Principal, Estado, Antigüedad y Acciones. Estado horizontal con ACTIVO verde e INACTIVO rojo; etiquetas pendientes/rechazadas conservadas cuando corresponda. Ver abre un modal de consulta del perfil permitido, incluida foto y especialidades secundarias, sin contraseñas ni hashes. Editar perfil y Desactivar conservan sus autorizaciones; el restablecimiento administrativo de contraseña está dentro del modal de edición. Grado tiene cinco opciones aprobadas, editable por Administrador/Jefe dentro de su ámbito; históricos sin dato muestran Sin registrar. El alta oculta país de residencia y envía Bolivia; botón Guardar. Alta y edición usan Fecha de incorporación única; al guardarla sincroniza año y antigüedad desde. Solicitud pública ampliada con nacionalidad, departamento, incorporación y foto; estado Pendiente informativo y grado reservado al personal autorizado. Los países de residencia históricos no se sobrescriben por este ajuste visual.


### Directorio compacto (2026-10-10)

Las celdas del directorio conservan su formato de tabla y se alinean verticalmente al centro; foto/nombre usan un contenedor interno flex. Acciones usa un contenedor interno con iconos SVG de ojo (Ver), lápiz (Editar perfil) y círculo tachado (Desactivar), lado a lado sin envolver. Cada botón conserva aria-label y title con acción y persona; el icono es decorativo para lectores de pantalla. Celdas con padding reducido, acciones compactas y columna fija durante desplazamiento horizontal. Se conservan modales y permisos.
