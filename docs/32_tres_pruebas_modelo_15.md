# NASA-TLX, GSE y Mini-IPIP: integración del modelo 15→6→4

Entrega del 2026-10-18, SQLite v31. La instrucción posterior del solicitante sustituye la decisión anterior de conservar solo dos pruebas. Se mantiene la separación entre Evaluaciones institucionales y el módulo Pruebas y Recomendación, sin incorporar funciones en DEMO.

## Modelo y entradas

Se utiliza **el modelo ya entrenado 15→6→4**, 124 parámetros, semilla 401 y época elegida 196, seleccionado por menor pérdida de validación dentro de la arquitectura preferida en la comparación de diez semillas. No se reentrena, no se generan nuevos datos ni se elige por resultados de prueba. [Comparación y límites originales](29_comparacion_redes_tlx.md).

Archivo `output/comparacion_tlx_1564_15664_200_20261018/15-6-4/modelo_ejemplar_validacion.json`, SHA-256 fijada en servidor `a98b65067700a975bb1993fe9510235900c21e15009adec8a18f46bca05e1353`. Inferencia aislada en `sicose/modelo_orientacion_tlx.py`: valida dimensiones, orden y rangos; normaliza `(valor-minimo)/(maximo-minimo)`, tanh oculta y cuatro sigmoides independientes. No importa generadores o entrenadores desde las rutas del sistema, no usa pickle y no permite entrenar en solicitudes.

| Grupo | Entradas | Rango |
|---|---|---|
| Institucional | Físico promedio, Desempeño promedio, Académica acumulada | 0–100, tres entradas |
| GSE | Autoeficacia | 10–40, una entrada |
| Mini-IPIP | Extraversión, amabilidad, responsabilidad, neuroticismo, apertura | 4–20, cinco entradas |
| NASA-TLX | Demanda mental, física, temporal, rendimiento, esfuerzo, frustración | 0–100, seis entradas |

Orden fijo: tres institucionales, GSE, cinco Mini-IPIP y seis NASA-TLX. No se imputa una prueba pendiente como cero. Las quince entradas deben proceder de fuentes completas, habilitadas y revisadas. Más variables no garantizan mejor generalización; este modelo sigue siendo experimental y entrenado con Datos generados y etiquetas de reglas didácticas, sin validación sobre personas.

Salidas aprobadas: Preparación progresiva y confianza; Organización de tareas y manejo de la carga; Comunicación y aprendizaje acompañado; Afrontamiento y seguimiento del bienestar. **Decisión posterior del 2026-10-18: las nuevas propuestas seleccionan exactamente una, la de mayor activación (argmax), como Línea de orientación prioritaria.** No se reentrena ni se interpreta su activación como probabilidad. Continúan Propuesta/Confirmada/Desactualizada, observación humana separada, cierre/reapertura y PDF solo con confirmación vigente. El criterio inicial de varias salidas/umbrales 0,35–0,65 y abstención queda exclusivamente para consultar las versiones anteriores; no se reescriben sus resultados ni las comparaciones offline.

## NASA-TLX y simulacro común

[NASA permite el uso y traducción sin autorización adicional](https://www.nasa.gov/human-systems-integration-division/nasa-task-load-index-tlx/). El [manual original](https://www.nasa.gov/wp-content/uploads/2026/03/nasa-tlx-v1-0-searchable-text-and-forms.pdf) describe seis dimensiones, valoraciones 0–100 en pasos de 5 y rendimiento desde bueno a malo. Consultados el 2026-10-18.

La versión `NASA-TLX-es-SICOSE-adaptacion-V1` es una **adaptación al español para este prototipo**, no una traducción cuya validación lingüística se afirme. Se conserva cada dimensión; no se aplica el índice ponderado original ni sus comparaciones por pares, ni se inventan pesos TLX, categorías clínicas o un promedio psicológico. Rendimiento conserva **0 bueno / 100 malo**. El sentido se explica en el reactivo, resumen y PDF.

El formulario, opciones, puntuación, fuente, atribución y privacidad están en la huella revisada por Administrador y Jefe, por separado y por Gestión, antes de habilitar NASA-TLX. Las huellas de GSE y Mini-IPIP permanecen intactas, sin perder revisiones o resultados existentes.

Administrador/Jefe registra el nombre y la fecha de un simulacro común **realizado**, dentro de las fechas de la Gestión y no futuro en Bolivia, con revisión optimista y confirmación. No se inventa uno durante la migración. NASA-TLX se bloquea hasta disponer del contexto. La configuración queda inmutable desde el primer intento para conservar comparabilidad y trazabilidad.

El Instructor ve el nombre y fecha del simulacro, responde seis selectores de 0 a 100 en pasos de 5 y debe confirmar que participó y finalizó esa actividad antes de finalizar la prueba. Se pueden guardar avances; el servidor rechaza una finalización sin esa confirmación. Una aplicación final por Gestión; un nuevo ciclo exige reinicio administrativo explícito con contraseña propia, como en las otras pruebas. El reinicio conserva el mismo simulacro común.

Privacidad sin cambios: Instructor solo «Completada», sin resultados/respuestas finales ni recomendaciones. Administrador/Jefe solo consultan respuestas finalizadas, nunca borradores. Se conservan respuestas y resultados por Gestión sin borrado automático. La auditoría no almacena contraseñas ni respuestas completas.

## Históricos y persistencia

No se modifica el archivo del modelo anterior 9→6→4 ni se eliminan propuestas/confirmaciones previas. En Gestiones abiertas, las propuestas antiguas quedan Desactualizadas al cambiar modelo/fuentes y se requieren las quince entradas para generar otra. En Gestiones cerradas con última recomendación del modelo anterior se conserva la consulta histórica de nueve entradas y su firma original; al reabrir, pasa al circuito vigente. La confirmación histórica no se reinterpreta mediante salidas nuevas.

SQLite v31 agrega siete tablas: `simulacros_tlx` y una familia independiente `tlx_revisiones_pruebas`, `tlx_activaciones_pruebas`, `tlx_historial_activaciones_pruebas`, `tlx_intentos_pruebas`, `tlx_reinicios_pruebas`, `tlx_reintentos_pruebas`. Esto evita reconstruir tablas con restricciones GSE/Mini-IPIP, copiar respuestas sensibles o alterar IDs/historial. Triggers y FKs conservan inmutabilidad, cadenas y pertenencia; un finalizado exige confirmación del simulacro en base de datos.

Se reutilizan las rutas actuales de pruebas con clave `NASATLX`. Nueva ruta `PUT /api/modelo-anual/gestiones/<pid>/simulacro-tlx`, cuerpo exacto `nombre`, `fecha`, `revision`, `realizado:true`, solo Administrador/Jefe con CSRF. Cierre, retiro e inactivo mantienen sus bloqueos. El PDF incluye las tres pruebas, seis dimensiones TLX, contexto del simulacro y arquitectura efectiva de la recomendación; sin respuestas individuales ni borradores.

Migración local aplicada por `scripts/migrar_tlx_v31.py`, respaldo `instance/backups/sicose-20261018-pre-v31-2898bedb.sqlite3`: 66 tablas previas preservadas íntegramente salvo valor schema_version, 73 finales, siete nuevas vacías, dos inicializaciones, quick_check=ok/FK=0. Evidencia `.tmp/tlx-migracion.json`. No se crearon simulacros, revisiones, activaciones, respuestas ni recomendaciones reales durante la entrega.

## Verificación

- 38 pruebas de regresión aprobadas en 103,131 s, más cinco específicas NASA-TLX aprobadas en 12,422 s: puntuación, pasos/extremos, revisión/simulacro, confirmación, borradores privados, reinicios, bloqueo de fuentes y conservación histórica cerrada/reabierta.
- El adaptador de inferencia reproduce **exactamente las 200 predicciones** guardadas para el ejemplar elegido, sin reentrenar ni alterar archivos.
- Doce escenarios Chromium, tres roles, 360/1447 px y ambos temas, con HTML/CSS/JS reales y API de base temporal: tres pruebas, quince entradas, separación institucional, navegación, formulario TLX con códigos 0–100, confirmación/privacidad y finalización. Sin errores/desbordes de página, tablas con desplazamiento interno móvil. PDF de prueba renderizado e inspeccionado; tres páginas con las seis dimensiones, simulacro y modelo correcto.
- Verificación adicional NASA/PDF: diez pruebas aprobadas en 26,054 s. Suite completa: **250 pruebas en 529,103 s; 249 aprobadas y una expectativa de nota cambiada accidentalmente de 30 a 31 durante la actualización de versiones de esquema**. Se corrigió únicamente esa expectativa y se repitieron las diez pruebas del módulo de cierres: **10 aprobadas en 12,544 s**. El cálculo institucional siempre devolvió 30; no se cambió para satisfacer la prueba. No se afirma una segunda suite completa ejecutada.
- Logs `.tmp/tlx-integracion-cierre.log`, `.tmp/tlx-nuevos-tests.log`, `.tmp/tlx-ultimos-tests.log`, `.tmp/tlx-suite-final.log`, `.tmp/tlx-cierres-cierre.log`, `.tmp/tlx-ui/`. Sintaxis, enlaces, diff, integridad local y huellas de ambos modelos correctos al cierre. Sin aceptación profesional ni validación del modelo sobre personas implícitas.

## Presentación y lectura de la recomendación — 2026-10-18

El botón Generar recomendación tiene un bloque de acciones separado de las tablas, con espacio y línea divisoria. Versión/estado y autor/fecha se presentan con tipografía secundaria. La salida conservada del modelo aparece destacada; después se ofrece una explicación descriptiva de las puntuaciones, con evaluación institucional separada de GSE, Mini-IPIP y NASA-TLX. Un detalle desplegable explica cada dimensión.

La lectura se construye en la interfaz desde `entradas` y `resultado` **guardados en cada versión**, también en el historial. No usa las puntuaciones actuales para reinterpretar una propuesta anterior. Las versiones desactualizadas lo advierten; las antiguas de nueve entradas no reciben una sección TLX ficticia. No se reescriben recomendaciones ni se cambia su firma, confirmación, PDF, modelo o base de datos.

Se diferencia entre líneas activadas, seguimiento general sin líneas activadas y abstención global. Para las líneas activadas se amplía el propósito y los temas que el responsable puede revisar, sin atribuir causalidad a entradas concretas. GSE se describe como confianza declarada; Mini-IPIP como rasgos sin nota global ni aprobado/reprobado; NASA-TLX como experiencia de la actividad, con rendimiento 0 bueno/100 malo. Sin categorías clínicas, percentiles, diagnósticos, atribuciones de importancia de variables ni porcentajes de certeza. La observación del responsable permanece separada.

Referencias de lectura: [GSE, autores de la adaptación española](https://userpage.fu-berlin.de/~health/spanscal.htm), [Mini-IPIP, traducción y clave balanceada](https://ipip.ori.org/Spanishmini-IPIPposneg.htm) y [NASA-TLX, documentación oficial](https://www.nasa.gov/human-systems-integration-division/nasa-task-load-index-tlx/). Las explicaciones son textos descriptivos de presentación, no un nuevo modelo ni una interpretación profesional automatizada.

Verificación de esta presentación: 24 escenarios Chromium con API aislada (seguimiento general, líneas activas, abstención, versión desactualizada, histórica de nueve entradas y pruebas pendientes), 360/1447 px y ambos temas, Administrador/Jefe. Verificadas separación del botón, tipografía, uso de puntuaciones históricas distintas a las actuales, formularios y detalle; sin errores ni desbordes. Otros doce escenarios del circuito de tres roles aprobados. Capturas de escritorio oscuro y móvil claro inspeccionadas; evidencia `.tmp/recomendacion-diseno/` y `.tmp/tlx-ui/`. Sin nueva suite backend por tratarse de presentación; sintaxis JavaScript y `git diff --check` correctos.

### Gráficos desplegables de las dimensiones

Se agrega «Ver gráficos de las dimensiones», con selector Barras horizontales / Diagrama de araña y cuatro grupos independientes: institucional, GSE, Mini-IPIP y NASA-TLX. Las puntuaciones originales y sus rangos permanecen visibles. La representación geométrica usa `(valor − mínimo) / (máximo − mínimo) × 100`, una posición en el rango teórico, no un percentil, una probabilidad o un porcentaje de aptitud. No se invierte neuroticismo ni rendimiento TLX, ni se calcula un total de personalidad o carga. Se indica expresamente la dirección del rendimiento TLX.

El radar usa ejes numerados con leyenda de dimensiones y puntuaciones, rejilla 25/50/75/100 y descripción accesible del SVG. GSE tiene una dimensión y conserva una barra en ambas vistas. En escritorio se presentan los tres radares juntos y GSE en una fila propia; en móvil se apilan. Colores azules/naranjas institucionales, derivados legibles según el tema, textos y valores independientes del color.

Los gráficos se generan al desplegar cada versión y usan exclusivamente su instantánea de entradas; el historial de nueve entradas omite NASA-TLX. No se envían datos a servicios externos ni se incorporan dependencias. Se mantiene la privacidad por roles y no se modifican el modelo, la puntuación, el PDF ni la base. La comprobación de historial abierto detectó y corrigió un desborde móvil del texto largo de la huella, permitiendo su ajuste de línea.

Verificación de gráficos: los 24 escenarios de interfaz se ampliaron para abrir ambas vistas, comprobar 15 o nueve barras según versión, dos o tres radares, leyendas, extremos 0/100, GSE 22 → 40 de posición, Mini-IPIP 4 → 0 y 20 → 100, y rendimiento TLX 80 → 80 sin inversión. Contrastadas entradas guardadas frente a actuales diferentes e historial desactualizado; sin errores/desbordes al cierre. Se repitieron los doce escenarios de tres roles. Capturas y resultados en `.tmp/recomendacion-diseno/` y `.tmp/tlx-ui/`; sin nueva suite backend para este cambio de presentación.

### Orden de página y confirmación del reporte — 2026-10-18

Secuencia administrativa: Gestión → Habilitación de pruebas → Estado por Instructor → selector de Instructor → Reinicio Individual → Resumen de pruebas → entradas institucionales → entradas psicométricas → Generar recomendación → versión/estado en letra pequeña → salida destacada en cuadro naranja → resumen en texto → significado de dimensiones → gráficos → observaciones del responsable → Confirmar propuesta para el reporte. El historial protegido queda al final. El simulacro común y sus controles permanecen dentro de Habilitación.

Reiniciar sale de la tabla de habilitación global y tiene tabla propia bajo el selector personal, conservando selección, permisos, verificación de contraseña y auditoría. La salida se destaca con tonos institucionales naranjas adaptados a ambos temas. Antes de enviar la confirmación del reporte se pregunta expresamente «¿Estás seguro de confirmar esta propuesta para el reporte individual?». Cancelar no envía la petición ni borra las observaciones; aceptar conserva la verificación de fuentes y autorización del servidor. Se mantiene la constancia mediante checkbox y la observación requerida.

Verificación: 24 escenarios Chromium ampliados con orden de nodos, ubicación de reinicios, apertura del modal con contraseña, cuadros, gráficos y confirmación aceptada/cancelada (cuatro combinaciones de resolución/tema, ambos roles). Doce escenarios de navegación/privacidad de tres roles aprobados; capturas móvil claro/escritorio oscuro inspeccionadas. Tres pruebas backend de separación de módulos aprobadas en 4,128 s. Sintaxis de ambos JavaScript y diff correctos. Sin cambios en SQLite, modelo, cálculos, PDF ni DEMO.

## Selección única de orientación prioritaria — 2026-10-18

Autorizado por el solicitante: elegir siempre una de las cuatro líneas mediante **argmax**, sin cambiar pesos, arquitectura, entrenamiento, entradas o puntuación de las pruebas. Las cuatro sigmoides originales se conservan. Para nuevas propuestas no se aplican los umbrales de activación ni hay categorías generales o abstención. Esto asegura una elección relativa, no su acierto ni certeza; no convierte la red en un modelo softmax entrenado para clases excluyentes.

El servidor ordena las cuatro activaciones de mayor a menor y guarda `criterio_seleccion=ARGMAX_V1`, `salida_prioritaria`, una sola sugerencia, ranking completo, diferencia entre las dos mayores y empates máximos. Si dos o más máximos son exactamente iguales, prevalece el orden original: Preparación, Organización, Comunicación, Afrontamiento. No se usa tolerancia para fabricar empates ni se redondea antes de seleccionar. Activaciones inválidas/incompletas siguen rechazadas: la obligación de elegir no permite fabricar una salida ante un error o fuentes pendientes.

La interfaz muestra «Salida del modelo · Línea de orientación prioritaria», amplía únicamente esa línea y presenta las dos mayores activaciones y su diferencia sin porcentajes de certeza. Los empates se explican. No se inventa un nuevo corte para llamar a una diferencia pequeña. La confirmación humana, observaciones y pregunta de seguridad siguen siendo necesarias. El reporte individual identifica la línea prioritaria solo después de una confirmación vigente.

Versionado sin migración: `ORIENTACION_PRIORITARIA_V1` entra en la firma de fuentes. Las versiones anteriores de gestiones abiertas quedan Desactualizadas, permitiendo regenerar aun sin corregir notas, sin modificar sus filas ni confirmaciones. Las gestiones cerradas reconstruyen la versión de integración conservada en sus fuentes: mantienen recomendaciones anteriores, incluidos resultados generales/abstenciones, hasta reapertura. Las nuevas confirmadas también permanecen vigentes al cerrar. Las comparaciones y métricas de entrenamiento anteriores conservan su alcance original y no evalúan esta nueva regla de selección.

Verificación: 25 pruebas backend aprobadas (3 nuevas de prioridad/historia en 1,388 s; 12 de recomendaciones en 26,748 s; 5 NASA/modelo en 5,166 s; 5 PDF individual en 21,897 s). Cubren máximos en las cuatro posiciones, valores bajos/intermedios, empates, inválidos, idempotencia, conservación de filas, cierres/reapertura, permisos, CSRF, privacidad y las 200 predicciones originales sin cambios. 16 escenarios UI nuevos de prioridad y 24 de versiones anteriores, ambos temas/360 y 1447 px/ambos roles, sin errores/desbordes. Capturas y PDF temporal de tres páginas inspeccionados. Huellas seleccionada y anterior intactas; sintaxis y diff correctos. Sin entrenamiento, modificación de SQLite local ni DEMO. Evidencia `.tmp/prioridad-ui/`, `.tmp/recomendacion-diseno/` y `.tmp/tlx-ui/`; no se ejecutó una nueva suite completa.

### Interpretación breve y amigable de la salida

Por solicitud posterior, «Resumen en texto de las pruebas» se reemplaza por **Interpretación de la recomendación**. Es un texto breve, específico de la línea seleccionada: prácticas paso a paso/confianza; prioridades y reparto de tareas; aprendizaje acompañado/comunicación; o escucha voluntaria/apoyos para afrontar exigencias. Se ofrece como punto de partida para conversar y acordar próximos pasos, sin afirmar déficits, causas concretas ni conclusiones clínicas.

El cuadro usa un naranja más claro que la Salida del modelo, con adaptación legible a ambos temas. Se retiran de este bloque las listas de puntuaciones y la explicación numérica de activaciones, margen y empates. Esos datos siguen conservados por el servidor; no se modifica la selección argmax, sus evidencias ni las recomendaciones guardadas. Significado de dimensiones y gráficos permanecen como desplegables después de la interpretación, seguidos de observaciones y confirmación. Los históricos de nueve entradas, salidas combinadas y resultados indeterminados reciben una explicación sencilla acorde a su resultado original, sin convertirlos a la política nueva.

Verificación de este ajuste: 16 escenarios de prioridad y 24 históricos en Chromium, ambos roles/temas/360 y 1447 px. Comprobadas las cuatro interpretaciones, ausencia de lenguaje técnico y puntuaciones en el cuadro, fondo más claro, conservación de gráficos con valores históricos, orden y confirmación cancelada/aceptada; sin errores/desbordes. Capturas móvil claro/escritorio oscuro inspeccionadas; sintaxis JavaScript y diff correctos. Sin nueva suite backend por tratarse exclusivamente de presentación; sin cambios de SQLite, modelo, PDF o DEMO.
