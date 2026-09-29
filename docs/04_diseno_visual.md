# 04. Diseño visual

## Dirección

Interfaz en español, clara, sobria y adaptable. Como inspiración funcional general se observó el sitio público de Evaluar (https://www.evaluar.com/), que presenta navegación de producto, accesos para candidatos/empresas y módulos de evaluación. SICOSE tomará solo patrones comunes de claridad, navegación y organización por módulos; no usará marca, textos, ilustraciones, composición ni interfaz propietaria de Evaluar.

## Identidad

- Azul primario institucional: `#1D1BBE` para navegación y acciones principales.
- Naranja institucional: `#F57B1A` para acentos y estados que requieran atención, no como único indicador.
- Neutros: fondo gris muy claro, superficies blancas, texto carbón y bordes suaves.
- El emblema SBRAB proporcionado se muestra en la parte superior de la barra lateral junto a la identificación SICOSE.
- Tipografía de sistema; jerarquía por tamaño, peso y espaciado. Contraste y foco visible accesibles.

## Estructura de pantallas

- Inicio de sesión y solicitud de registro/aprobación.
- Cascarón autenticado: barra lateral colapsable, encabezado con período activo y menú de cuenta; navegación cambia según rol.
- Dashboard de administrador: resumen general y acceso global para administrar todas las cuentas, Jefes de Personal, Instructores Voluntarios y evaluaciones.
- Dashboard de Jefe de Personal: solo su equipo de Instructores Voluntarios registrados y activos, evaluaciones tomadas y resultados autorizados, notas no psicométricas y controles para habilitar/deshabilitar pruebas por voluntario.
- Dashboard de Instructor Voluntario: edición de sus datos personales, evaluaciones propias completadas y pendientes y resumen de estado/avance, sin notas, resultados individuales ni observaciones.
- Perfil y detalle: datos, cursos, experiencia, asistencia, evaluaciones y observaciones según permiso.
- Formularios de calificación con validación en línea y confirmación antes de guardar.
- Tablas con búsqueda, filtros, paginación y vistas compactas para móvil.
- Estados vacíos, error, carga, no autorizado y confirmación de acción con mensajes directos.

## Implementación de Fase 3

Se implementó una plantilla compartida con barra lateral condicionada por rol, encabezado, período actual, identidad de cuenta, estado activo de navegación y salida de sesión. Hay una página diferente para cada rol y el inicio redirige según el rol autenticado. Las tarjetas usan cifras leídas de SQLite: administrador ve perfiles activos, cuentas pendientes y períodos; Jefe de Personal ve únicamente Instructores Voluntarios asignados y sus asignaciones incompletas; Instructor Voluntario ve sus propias asignaciones y capacitaciones. También están las primeras pantallas para administrar cuentas de instructor y perfiles/solicitudes de voluntario.

El bloque de perfil de la barra lateral muestra la foto privada de la cuenta para Administrador, Jefe de Personal e Instructor Voluntario; si no hay foto, conserva el avatar con inicial. La imagen se solicita a la API autenticada de perfil.

El panel inicial de administración incluye tarjetas de Jefes de Personal e Instructores Voluntarios con sus fotos, estado e inicial de respaldo cuando aún no hay imagen. La navegación de Configuración abre la edición del nombre, foto y contraseña del administrador; al cambiar la contraseña solicita la clave actual y termina la sesión para volver a ingresar.

Estas pantallas y contadores son una base, no la implementación completa de todos los permisos descritos arriba. Con Fase 5 se agregan registros de asistencia, notas no psicométricas y estados de evaluaciones del Instructor Voluntario. Continúan pendientes el autoservicio del perfil del voluntario y los formularios/intentos psicométricos, que permanecen bloqueados por falta de instrumentos autorizados. Las funciones no disponibles deben mostrarse como pendientes.

## Implementación de Fase 5

Administración cuenta con pantallas iniciales para períodos, catálogo y asignaciones. Jefe de Personal/Administrador pueden marcar asistencias, registrar capacitaciones y crear/corregir notas no psicométricas conservando versiones anteriores; Jefe de Personal queda limitado a Instructores Voluntarios activos asignados. Instructor Voluntario ve la lista de evaluaciones completadas/pendientes sin notas ni observaciones. Los candidatos psicométricos no están aprobados en `docs/06_pruebas_psicometricas.md`, por lo que se bloquea su activación y no se muestran formularios, intentos o reinicios operativos.

Asistencias tiene una lista de estado por persona y fecha, con opciones Asiste, Atraso, Permiso y Falta; la actividad se conserva como referencia de la gestión. El historial se filtra por persona y permite consultar la última fecha con registros o un rango. Capacitaciones o Cursos es una sección aparte para Administrador y Jefe de Personal, con listado, alta y edición vinculada a `capacitaciones`; no permite borrado físico.

La barra lateral se convierte en menú móvil con control accesible por teclado y también puede plegarse en escritorio para liberar espacio. El estado plegado se recuerda en el navegador; la navegación sigue identificable mediante nombres accesibles. El selector de tema permite cambiar entre modo claro y oscuro y conserva la preferencia local. Ambos temas mantienen contraste, foco visible y los colores institucionales como identidad de las acciones y acentos. Los estados usan texto además de color.

## Responsividad e interacción

En pantalla pequeña, barra lateral pasa a menú accesible; tablas se convierten en tarjetas o permiten desplazamiento horizontal señalizado; campos y botones ocupan ancho cómodo. No comunicar estados únicamente con color. Etiquetar campos, asociar errores con controles, permitir navegación por teclado y respetar `prefers-reduced-motion`.

## Confidencialidad en UI

El panel de Instructor Voluntario muestra únicamente estado y avance de sus evaluaciones; nunca calificaciones, resultados individuales, observaciones ni respuestas psicométricas. Jefe de Personal ve resultados solo de voluntarios bajo su ámbito, pero no puede modificar las calificaciones psicométricas; solo puede habilitar/deshabilitar pruebas específicas. Administración tiene alcance global. Evitar nombres/identificadores innecesarios en reportes consolidados. Ocultar acciones por rol mejora claridad, pero el backend mantiene el control real. Mostrar que los pesos y puntajes son una configuración institucional pendiente de aprobación; nunca rotularlos como baremos clínicos o científicamente validados.
