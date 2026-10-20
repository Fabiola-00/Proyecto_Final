# Diseño institucional y temas — 2026-10-20

La decisión del solicitante sustituye la paleta anterior de la interfaz web: azul principal `#1E1BBB` y naranja de acento `#F2AB7E`. En oscuro el azul de acción es `#9C9AFF`; sobre fondos claros el texto naranja se sustituye por `#8F3A0A`. Los reportes PDF conservan la paleta anterior. No cambia SQLite v32, permisos, calificaciones ni modelos.

## Ajuste posterior solicitado

La barra lateral usa #16163A en oscuro y #3B3B70 en claro, un tono más claro de la misma gama. Se retira el buscador de cabecera, su lógica y estilos. El selector desplegable se sustituye por un botón que indica el tema al que cambiará: Modo Claro o Modo Oscuro, con nombre accesible, icono y preferencia persistente. No ofrece una opción Sistema; sin preferencia guardada sigue inicialmente el equipo. Las descripciones de búsqueda y selector de tres opciones más abajo documentan la primera implementación, sustituida por este ajuste.

Verificación del ajuste: dos pruebas de contraste aprobadas, ensayo Node actualizado para alternancia por clic y persistencia, sintaxis JavaScript y diff correctos. No se repite la suite general ni se añade otra comprobación visual completa.

## Presentación

Los tokens de `frontend/static/css/estilos.css` definen los neutros, superficies, textos, bordes, acciones y estados solicitados. El reparto 60/30/10 orienta la jerarquía visual; no se presenta como una medición exacta de píxeles. Advertencias en ámbar, éxito en verde, información teal y errores/destrucción en rojo. Badges con punto y texto, sin depender exclusivamente del color. Gráficos con azul, naranja y teal; en oscuro la elevación usa superficies más claras y se suprimen sombras.

Barra lateral de 230 px en escritorio y menú ocultable en móvil; tarjetas apiladas y desplazamiento local de tablas anchas. Tipografía Plus Jakarta Sans con alternativa system-ui: no se descarga una fuente ni se añade dependencia externa. Controles de al menos 44 px y foco de 2 px separado 2 px. El texto auxiliar sobre superficies elevadas oscuras usa text-secondary para conservar contraste; text-muted se mantiene como token sin forzarlo sobre esos fondos.

La cabecera incorpora búsqueda de secciones entre los enlaces que el servidor ya autorizó para el rol actual. No consulta personas ni añade una API. La acción principal de cabecera remite al botón o enlace existente, respetando su estado deshabilitado y validación. Al abrir un diálogo, la acción principal pasa al diálogo; cancelar, consultar y filtrar mantienen jerarquía secundaria. Pantallas de consulta pueden no tener acción principal. Las acciones destructivas se identifican por su texto o nombre accesible.

## Preferencias

`tema_inicio.js` aplica el tema antes de cargar estilos. El selector compartido ofrece Claro suave, Oscuro y Sistema, guarda `sicose-tema` en localStorage y sincroniza pestañas. Sistema sigue prefers-color-scheme y sus cambios; si el almacenamiento está bloqueado, sigue funcionando durante la sesión. CSS cubre la preferencia del sistema sin JavaScript y las elecciones explícitas mediante data-theme, con color-scheme correspondiente.

Archivos principales: `_dashboard_base.html`, `_selector_tema.html`, `login.html`, `registro.html`, `error.html`, `estilos.css`, `app.js`, `tema_inicio.js` e `interfaz.js`, dentro de frontend.

## Verificación y límites

- Regresión final: **14 pruebas aprobadas en 30,571 s**, incluyendo temas, módulos de evaluación, panel del Instructor, inicio administrativo y autoservicio de correo/foto. Evidencia: `.tmp/temas-regresion-cierre.log`. Una ejecución inicial encontró una expectativa de la paleta anterior; se actualizó al nuevo acuerdo y se repitió el conjunto. No se ejecutó la suite general.
- Dos pruebas de tokens comprueban 36 combinaciones de texto con contraste mínimo 4,5:1 y seis pares de bordes de campos con mínimo 3:1, además de igualdad entre el oscuro automático y manual. No equivalen a una certificación integral WCAG de todas las pantallas.
- Prueba Node de preferencia del sistema, cambios del equipo, selección manual, persistencia, sincronización entre pestañas, preferencia inválida y almacenamiento bloqueado. Sintaxis de los tres archivos JavaScript comprobada.
- Inspección visual del acceso en ambos temas y panel del Jefe; Operaciones con formulario y diálogo en oscuro. Se detectaron controles compactos menores de 44 px y se corrigieron; la comprobación posterior del formulario no encontró controles menores. Perfil del Instructor a 360 px sin desborde global; guardado desde la cabecera verificado sobre una cuenta sintética. Búsqueda de secciones verificada. Una lectura de estilos/textos de Operaciones oscuro no encontró contrastes inferiores a 4,5:1 en la muestra.
- No se afirma recorrido exhaustivo de todos los roles, tamaños y pantallas. La última comprobación visual administrativa quedó limitada por un timeout de la conexión del navegador; el inicio administrativo sí pasó su regresión automatizada. No se cargaron fotografías reales ni se modificó la base operativa para estos ensayos.

Si el servidor no usa recarga automática, reiniciarlo con su configuración existente y recargar con Ctrl+F5 para renovar plantillas y estáticos.

En esta entrega el servidor local de puerto 5000 retenía la plantilla anterior. Se reinició con la misma orden `flask --app sicose run`; acceso HTTP 200, script de inicio de tema y nueva paleta comprobados. El servidor sintético de ensayo se detuvo y sus dos bases identificadas se retiraron, sin modificar la base operativa ni el entorno.
