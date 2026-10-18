# Comparación 15 → 6 → 4 y 15 → 6 → 6 → 4

Entrenamiento experimental sobre los mismos 200 Datos generados, con reglas de etiquetas V1; sin respuestas reales. No mide utilidad ni precisión sobre personas.

## Protocolo

Diez semillas pareadas por arquitectura: 31415, 7, 19, 43, 101, 211, 307, 401, 503, 607. Misma partición 140/30/30, sin regenerar filas ni etiquetas. Normalización por rangos teóricos, tanh oculta, cuatro sigmoides independientes. SGD lote 1, orden 42, tasa 0,03, L2 0,001 solo en pesos; máximo 300 épocas, paciencia 25, mejora mínima 1e-6 y restauración de mejores pesos.

BCE: suma de entropías cruzadas de cuatro salidas, promediada por caso, sin penalización L2 en la métrica. Menor es mejor. Selección por media de BCE de validación; ejemplar por menor BCE de validación dentro de cada arquitectura. Selección guardada antes de evaluar prueba.

## Comparativo de diez inicializaciones

| Medida | 15 → 6 → 4 | 15 → 6 → 6 → 4 |
|---|---:|---:|
| Parámetros | 124 | 166 |
| BCE validación ↓ | 0.7621 ± 0.1528 | 0.9351 ± 0.0872 |
| BCE prueba ↓ | 0.9322 ± 0.0782 | 1.2223 ± 0.2377 |
| Coincidencia completa prueba ↑ | 65.00% ± 6.53% | 62.67% ± 7.34% |
| F1 macro prueba ↑ | 89.14% ± 1.89% | 88.26% ± 1.92% |
| Abstenciones / 30 | 8.3000 ± 3.0930 | 6.7000 ± 2.8694 |
| Segundos entrenamiento | 0.7374 ± 0.7707 | 0.9751 ± 0.6020 |

Media ± desviación estándar muestral entre semillas; no intervalos de confianza ni diez conjuntos independientes.

## Control con semilla 31415

| Arquitectura | Época elegida / ejecutadas | BCE validación | Aciertos completos / 30 | Abstenciones / 30 |
|---|---:|---:|---:|---:|
| 15-6-4 | 45 / 70 | 0.7752 | 20 | 10 |
| 15-6-6-4 | 40 / 65 | 0.9318 | 14 | 6 |

## Selección y límites

**Arquitectura recomendada para este experimento: 15-6-4**, por menor BCE media de validación. No se sustituye el modelo operativo.

Ejemplares elegidos únicamente por validación: 15-6-4: semilla 401, 15-6-6-4: semilla 401. Se conservan todos los modelos y el control fijo 31415; no escoger semilla por aciertos de prueba.

Coincidencia completa exige acertar las cuatro etiquetas simultáneamente con umbral 0,50. F1 macro promedia las cuatro salidas. Son métricas distintas de emisión de recomendaciones: cualquier activación entre 0,35 y 0,65 implica abstención global; las activaciones no son probabilidades calibradas.

La mayor profundidad agrega 42 parámetros (+33,87%). Puede representar relaciones más complejas, pero aumenta costo y variabilidad; con 140 filas de entrenamiento no garantiza mejor generalización.

Solo un reparto y 30 filas de prueba; etiquetas de reglas inventadas y distribución artificial. Las semillas estudian inicialización, no variabilidad de población. Comparación exploratoria; no demuestra eficacia clínica/institucional ni autoriza decisiones de personal. Una siguiente ronda que use esta prueba deberá declararla reutilizada.

Pesos/modelos JSON por semilla; métricas, predicciones y huellas en esta carpeta. Sin SQLite, cambios de formularios ni inferencia sobre personas.

Reproducir: `python scripts/comparar_redes_tlx.py --salida output/nueva_comparacion_tlx` (destino nuevo).
