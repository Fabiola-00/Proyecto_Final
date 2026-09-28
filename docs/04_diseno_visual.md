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
- Dashboard de administrador: resumen de voluntarios, solicitudes pendientes, período y acceso a gestión/reportes.
- Dashboard de instructor: voluntarios asignados, avance y tareas pendientes.
- Dashboard de voluntario: evaluaciones habilitadas, avance personal e historial propio.
- Perfil y detalle: datos, cursos, experiencia, asistencia, evaluaciones y observaciones según permiso.
- Formularios de calificación con validación en línea y confirmación antes de guardar.
- Tablas con búsqueda, filtros, paginación y vistas compactas para móvil.
- Estados vacíos, error, carga, no autorizado y confirmación de acción con mensajes directos.

## Responsividad e interacción

En pantalla pequeña, barra lateral pasa a menú accesible; tablas se convierten en tarjetas o permiten desplazamiento horizontal señalizado; campos y botones ocupan ancho cómodo. No comunicar estados únicamente con color. Etiquetar campos, asociar errores con controles, permitir navegación por teclado y respetar `prefers-reduced-motion`.

## Confidencialidad en UI

No incluir respuestas psicométricas en tarjetas o notificaciones. Evitar nombres/identificadores innecesarios en reportes consolidados. Ocultar acciones por rol mejora claridad, pero el backend mantiene el control real. Mostrar que los pesos y puntajes son una configuración institucional pendiente de aprobación; nunca rotularlos como baremos clínicos o científicamente validados.
