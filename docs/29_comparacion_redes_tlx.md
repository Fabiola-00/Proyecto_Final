# Comparación de redes con quince entradas — 2026-10-18

Decisión posterior del solicitante: integrar el ejemplar 15→6→4 elegido por validación, semilla 401/época 196. [Entrega del sistema v31](32_tres_pruebas_modelo_15.md). Este informe conserva las métricas y el alcance de la comparación original.

[Informe comparativo breve en PDF, dos páginas](../output/pdf/informe_comparativo_redes_15_6_4_y_15_6_6_4.pdf): resultados medios, conceptos básicos, motivos de selección y límites, generado a partir de los artefactos verificados.

## Alcance verificado

Entrenadas 15→6→4 (124 parámetros) y 15→6→6→4 (166 parámetros), diez semillas prefijadas por arquitectura, sobre los mismos 200 registros ya etiquetados. Sin regenerar puntuaciones, etiquetas ni particiones 140/30/30. La aprobación de cuatro salidas y sus reglas didácticas está documentada en [datos de quince entradas](28_datos_tlx_gse_miniipip.md).

Pesos, protocolo, selección previa a prueba, veinte ejecuciones, métricas y predicciones en [artefactos completos](../output/comparacion_tlx_1564_15664_200_20261018/README.md). Implementación aislada en `scripts/red_tlx_experimental.py` y comparador `scripts/comparar_redes_tlx.py`. Sin importar este módulo desde rutas operativas.

## Protocolo común

- Semillas de pesos: 31415, 7, 19, 43, 101, 211, 307, 401, 503, 607; inicialización uniforme −0,5 a 0,5, sesgos cero.
- Normalización por rangos teóricos, tanh en capas ocultas y cuatro sigmoides independientes.
- SGD lote 1, tasa 0,03, L2 0,001 solo en pesos, orden con semilla 42.
- Máximo 300 épocas, paciencia 25, mejora mínima 1e-6; restauración de pesos elegidos por menor BCE de validación.
- BCE: suma sobre cuatro salidas y promedio por caso, sin L2 en la métrica. Selección de arquitectura por menor media de validación entre semillas; ejemplar por menor validación dentro de cada arquitectura.
- Selección escrita antes de consultar resultados de prueba. La prueba se usa después para informar resultados, no para elegir arquitectura, semilla o parámetros.

## Resultados

Media ± desviación estándar muestral de diez inicializaciones sobre una única partición:

| Medida | 15→6→4 | 15→6→6→4 |
|---|---:|---:|
| Parámetros | 124 | 166 |
| BCE de validación (menor mejor) | 0,7621 ± 0,1528 | 0,9351 ± 0,0872 |
| BCE de prueba | 0,9322 ± 0,0782 | 1,2223 ± 0,2377 |
| Coincidencia completa de prueba | 65,00% ± 6,53 puntos | 62,67% ± 7,34 puntos |
| F1 macro de prueba | 89,14% ± 1,89 puntos | 88,26% ± 1,92 puntos |
| Abstenciones por 30 casos | 8,3 ± 3,09 | 6,7 ± 2,87 |

**Recomendada para este experimento: 15→6→4**, por menor pérdida media de validación y menor complejidad. No se ha adoptado como modelo del sistema.

Los ejemplares de ambas arquitecturas elegidos por validación corresponden a semilla 401: 15→6→4 elige época 196 y obtiene 22/30 coincidencias completas en prueba, tres abstenciones; 15→6→6→4 elige época 41 y obtiene 20/30, seis abstenciones. No confundir estos ejemplares con las medias anteriores ni con el control prefijado 31415 (20/30 y 14/30, respectivamente). Todos los modelos quedan conservados.

Coincidencia completa exige acertar las cuatro etiquetas simultáneamente al umbral 0,50. No mide recomendaciones efectivamente emitidas: se conserva abstención global si cualquier activación queda estrictamente entre 0,35 y 0,65. Las activaciones no son probabilidades calibradas. Menos abstenciones no implica mayor exactitud.

## Límites y verificación

Solo 200 Datos generados y etiquetas de reglas inventadas: no es validación sobre personas ni demuestra utilidad institucional. Diez semillas no constituyen diez muestras independientes ni intervalos de confianza. La comparación utiliza un solo reparto y treinta casos de prueba; no acredita superioridad universal de una arquitectura. Una nueva ronda que consulte esta prueba deberá identificarla como reutilizada.

Nueve pruebas unitarias aprobadas: cinco de etiquetas y cuatro del MLP. Comprobados gradientes numéricos de todos los pesos/sesgos de ambas arquitecturas, dimensiones, parámetros, límites de datos, exclusión de prueba/solapamiento y restauración del mejor peso de validación. Recargados veinte modelos y recalculadas sesenta evaluaciones de partición, con coincidencia exacta. Dos entrenamientos de control 31415 reproducen exactamente los pesos y registros guardados. Manifiesto de huellas correcto y modelo operativo original intacto. Evidencia `.tmp/tlx-verificacion.json`.

Sin cambios en SQLite, formularios, activaciones, respuestas, recomendaciones reales ni reporte individual. No se ejecuta la suite funcional general porque esta entrega está aislada del circuito operativo.
