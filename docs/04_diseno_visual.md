# 04. Diseño visual

## Dirección

Interfaz en español, clara, sobria y adaptable. Como inspiración funcional general se observó el sitio público de Evaluar (https://www.evaluar.com/), que presenta navegación de producto, accesos para candidatos/empresas y módulos de evaluación. SICOSE tomará solo patrones comunes de claridad, navegación y organización por módulos; no usará marca, textos, ilustraciones, composición ni interfaz propietaria de Evaluar.

## Identidad

- Azul primario: `#1F1ABC` para navegación, títulos activos y acciones principales.
- Naranja: `#FA9648` para acentos y estados que requieran atención, no como único indicador.
- Neutros: fondo gris muy claro, superficies blancas, texto carbón y bordes suaves.
- Tipografía de sistema; jerarquía por tamaño, peso y espaciado. Contraste y foco visible accesibles.

## Estructura de pantallas

- Inicio de sesión y solicitud de registro/aprobación.
- Cascarón autenticado: barra lateral colapsable, encabezado con período activo y menú de cuenta; navegación cambia según rol.
- Dashboard de administrador: resumen general y acceso global para administrar todas las cuentas, instructores, voluntarios y evaluaciones.
- Dashboard de instructor: solo su equipo de voluntarios registrados y activos, evaluaciones tomadas y resultados autorizados, notas no psicométricas y controles para habilitar/deshabilitar pruebas por voluntario.
- Dashboard de voluntario: edición de sus datos personales, evaluaciones propias completadas y pendientes y resumen de estado/avance, sin notas, resultados individuales ni observaciones.
- Perfil y detalle: datos, cursos, experiencia, asistencia, evaluaciones y observaciones según permiso.
- Formularios de calificación con validación en línea y confirmación antes de guardar.
- Tablas con búsqueda, filtros, paginación y vistas compactas para móvil.
- Estados vacíos, error, carga, no autorizado y confirmación de acción con mensajes directos.

## Implementación de Fase 3

Se implementó una plantilla compartida con barra lateral condicionada por rol, encabezado, período actual, identidad de cuenta, estado activo de navegación y salida de sesión. Hay una página diferente para cada rol y el inicio redirige según el rol autenticado. Las tarjetas usan cifras leídas de SQLite: administrador ve perfiles activos, cuentas pendientes y períodos; instructor ve únicamente voluntarios asignados y sus asignaciones incompletas; voluntario ve sus propias asignaciones y capacitaciones. También están las primeras pantallas para administrar cuentas de instructor y perfiles/solicitudes de voluntario.

Estas pantallas y contadores son una base, no la implementación completa de todos los permisos descritos arriba. Con Fase 5 se agregan registros de asistencia, notas no psicométricas y estados de evaluaciones del voluntario. Continúan pendientes el autoservicio del perfil del voluntario y los formularios/intentros psicométricos, que permanecen bloqueados por falta de instrumentos autorizados. Las funciones no disponibles deben mostrarse como pendientes.

## Implementación de Fase 5

Administración cuenta con pantallas iniciales para períodos, catálogo y asignaciones. Instructor/admin pueden marcar asistencias, registrar capacitaciones y crear/corregir notas no psicométricas conservando versiones anteriores; instructor queda limitado a voluntarios activos asignados. Voluntario ve la lista de evaluaciones completadas/pendientes sin notas ni observaciones. Los candidatos psicométricos no están aprobados en `docs/06_pruebas_psicometricas.md`, por lo que se bloquea su activación y no se muestran formularios, intentos o reinicios operativos.

La barra lateral se convierte en menú móvil con control accesible por teclado. En escritorio permanece visible. Se conservan los colores institucionales y los estados usan texto además de color.

## Responsividad e interacción

En pantalla pequeña, barra lateral pasa a menú accesible; tablas se convierten en tarjetas o permiten desplazamiento horizontal señalizado; campos y botones ocupan ancho cómodo. No comunicar estados únicamente con color. Etiquetar campos, asociar errores con controles, permitir navegación por teclado y respetar `prefers-reduced-motion`.

## Confidencialidad en UI

El panel de voluntario muestra únicamente estado y avance de sus evaluaciones; nunca calificaciones, resultados individuales, observaciones ni respuestas psicométricas. Instructor ve resultados solo de voluntarios bajo su ámbito, pero no puede modificar las calificaciones psicométricas; solo puede habilitar/deshabilitar pruebas específicas. Administración tiene alcance global. Evitar nombres/identificadores innecesarios en reportes consolidados. Ocultar acciones por rol mejora claridad, pero el backend mantiene el control real. Mostrar que los pesos y puntajes son una configuración institucional pendiente de aprobación; nunca rotularlos como baremos clínicos o científicamente validados.
