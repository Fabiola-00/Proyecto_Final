# Separación de Evaluaciones y Pruebas y Recomendación - 2026-10-18

Actualización posterior: se conserva esta organización de módulos y se incorporan las tres pruebas y el modelo 15→6→4 por nueva instrucción del solicitante. Véase [integración v31](32_tres_pruebas_modelo_15.md). Las referencias inferiores al modelo operativo de nueve entradas describen el corte previo.

## Organización confirmada

El solicitante autorizó separar la evaluación institucional de las pruebas y la recomendación en la barra lateral. Se conserva SQLite v30 y el modelo operativo GSE/Mini-IPIP 9→6→4, sin cambiar pesos, entrenamiento, cálculos, intentos, revisiones, recomendaciones, reportes o permisos. NASA-TLX y sus experimentos no se incorporan.

| Módulo | Contenido |
|---|---|
| Evaluaciones | Físico, Desempeño y Académica; activación institucional, calificación, formación, operaciones, asistencia y habilitación individual. Historial de notas exclusivo del Administrador como antes. |
| Pruebas y Recomendación | GSE/Mini-IPIP: revisión, habilitación por Gestión, estados por persona, resultados, respuestas finalizadas y reinicios con contraseña; generación, confirmación, versiones e historial de recomendaciones. |

La recomendación muestra las tres notas institucionales en una tabla de consulta y las seis dimensiones de pruebas en otra, con rangos propios y orden fijo. El enlace a Evaluaciones permite corregir las notas en su módulo; no hay formularios institucionales duplicados en el nuevo módulo. La edición vuelve a marcar las propuestas anteriores como Desactualizadas mediante el mecanismo existente.

## Rutas y selección

- `/gestion/modelo-anual`: Evaluaciones, solo Administrador/Jefe.
- `/gestion/pruebas-recomendacion`: nuevo módulo. Administrador/Jefe ven el circuito administrativo; Instructor solo sus formularios y estados propios.
- `/mis-evaluaciones/anual`: conserva la consulta institucional propia; sus formularios GSE/Mini-IPIP se trasladan al nuevo módulo.

Las APIs y sus verificaciones de rol, propiedad, CSRF y estado permanecen. La nueva página no habilita pruebas ni modifica registros al abrirse. El Instructor no recibe resultados/subescalas/respuestas finalizadas ni acceso a recomendaciones; solo «Completada». Las APIs aritméticas históricas no se cambian ni se habilitan nuevos ejemplos.

En ambas páginas administrativas se seleccionan Gestión e Instructor. Los parámetros `periodo_id` y `persona_id` mantienen el contexto en URL, enlaces cruzados y enlaces laterales; recargar conserva una selección válida. Se verifica la pertenencia de la persona a la lista de esa Gestión antes de restaurarla. Cambiar Gestión vacía selección y resultados anteriores; cambiar persona invalida solicitudes pendientes de resultados/recomendaciones mediante los controles existentes.

El nuevo controlador es `frontend/static/js/pruebas_recomendacion.js`; el contexto de enlaces se comparte mediante `contexto_evaluacion.js`. `modelo_anual.js` queda para Gestión/Evaluaciones, filtra sus tres componentes institucionales y deja de consultar ejercicios aritméticos cada quince segundos. Se retira también la referencia obsoleta no declarada `firmaEjemplos` que fallaba al cambiar Gestión; no se modifica el circuito histórico de ejemplos.

La barra lateral marca correctamente el módulo activo en los tres roles. El selector de Instructor aparece antes de la tabla de pruebas, identificando claramente el alcance individual de Reiniciar frente al alcance por Gestión de Habilitar/Deshabilitar.

## Verificación

- **38 pruebas aprobadas en 37,208 s**: tres específicas de separación, sesión, navegación activa y ausencia de escrituras al abrir páginas; más regresión de modelo anual, recomendaciones, reinicios y PDF individual. Tras el cambio final de descripción de página propia, repetidas únicamente las tres pruebas de separación: **3 aprobadas en 2,099 s**.
- **12 escenarios Chromium**: tres roles, 360/1447 px, temas claro/oscuro. HTML/CSS/JS reales y respuestas API capturadas de una base temporal aislada, sin datos reales ni despliegue en DEMO. Verificados ida/vuelta con misma Gestión/persona, recarga por URL, limpieza de selección, separación de controles, rangos de pruebas y privacidad propia; sin errores JavaScript ni desbordes de página. Las tablas conservan desplazamiento interno horizontal en móvil. Capturas inspeccionadas.
- Evidencia `.tmp/modulos-evaluacion-tests.log`, `.tmp/modulos-ui/resultados.json`. Sin nueva suite general completa; la última ejecución general y su expectativa histórica corregida están documentadas en [reinicios v30](30_reinicio_pruebas.md).
- Sin migración o escrituras en la base local. Huella del modelo original, sintaxis y enlaces comprobados al cierre.
