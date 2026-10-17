# Comparación: 9→6→4 frente a 9→6→4→4 — 2026-10-17

**Este ensayo favorece conservar 9→6→4. El modelo vigente no se sustituyó.**

Mismos 200 registros y particiones 140 entrenamiento/30 validación/30 prueba. Diez semillas por arquitectura, fijadas antes de ejecutar; 20 entrenamientos en total. La alternativa agrega una capa oculta de cuatro neuronas a la primera capa de seis. Las salidas siguen siendo cuatro etiquetas combinables, con activaciones sigmoidales no calibradas.

| Medida | Actual 9→6→4 | Alternativa 9→6→4→4 |
|---|---:|---:|
| Capas ocultas | 1 | 2 |
| Parámetros | 88 | 108 (+22,73%) |
| Coincidencia completa en entrenamiento | 89,36% ± 1,73 pp | 84,57% ± 5,57 pp |
| Coincidencia completa en validación | 82,67% ± 3,44 pp | 78,67% ± 6,13 pp |
| Pérdida media de validación, menor es mejor | **0,4347** | 0,5724 |
| Coincidencia completa en prueba | **80,33% ± 2,92 pp** | 72,33% ± 5,22 pp |
| Rango de coincidencia en prueba | 76,67%–83,33% | 63,33%–80,00% |
| Pérdida media de prueba, menor es mejor | **0,4911** | 0,7027 |
| Abstenciones medias por 30 casos de prueba | 6,1 | 5,1 |
| Época elegida media | 120,2 | 58,4 |
| Tiempo de entrenamiento medio observado | 0,560 s | 0,394 s |

± indica desviación estándar muestral entre inicializaciones, no un intervalo de confianza sobre datos independientes. Coincidencia completa exige acertar simultáneamente las cuatro etiquetas al umbral 0,5. La abstención se mide por separado si cualquier activación está entre 0,35 y 0,65; no constituye una categoría complementaria a los aciertos.

La actual superó a la alternativa en coincidencia de prueba en nueve pares; hubo un empate y ninguna victoria de la alternativa. Diferencia media alternativa–actual: −8,00 puntos porcentuales. La alternativa tiene más parámetros y mayor variabilidad en este ensayo. Tampoco mejoró el criterio principal, definido como menor entropía cruzada media de validación. Esto no demuestra que toda arquitectura de dos capas sea inferior ni que un ajuste diferente produzca el mismo resultado.

La alternativa terminó antes en promedio por parada temprana; eso explica que su tiempo total observado sea menor aunque tenga más parámetros. Los tiempos dependen de equipo, carga y épocas. No se hizo una búsqueda de hiperparámetros específica para cada arquitectura.

## Protocolo y conservación

- CSV idéntico al original, sin regeneración ni mezcla con otros conjuntos. SHA-256: `e242160516c378d22221da0ae37d9cc78af81951e7e66a7a94a1848e0fc75015`.
- Semillas de pesos: 31415, 7, 19, 43, 101, 211, 307, 401, 503 y 607. Sesgos iniciales cero; pesos uniformes [−0,5; 0,5]. Semilla de orden de entrenamiento 42.
- Misma normalización, tanh en capas ocultas, cuatro sigmoides, SGD con tasa 0,03, L2=0,001, máximo 300 épocas, paciencia 25 y restauración de la menor pérdida de validación. Prueba no actualiza pesos ni selecciona épocas.
- El control 9→6→4 con semilla 31415 reproduce exactamente los pesos del modelo actual y sus resultados. Con esa misma semilla, la actual obtiene 24/30 aciertos completos y la alternativa 22/30. Se informan también las otras nueve inicializaciones para evitar elegir solo un caso favorable.
- Los mismos 30 casos de prueba ya fueron consultados y reutilizados en comparaciones anteriores. El resultado es exploratorio, no una prueba independiente nueva. Diez semillas no agregan datos ni representan diez muestras independientes.
- Se guardan todos los pesos por semilla y los resultados por partición. La identificación de mejores semillas en el JSON usa exclusivamente validación; no sustituye el modelo vigente.

## Archivos y reproducción

`comparacion.json`: protocolo, medias/desviaciones/rangos, diferencias pareadas y métricas por ejecución. `ejecuciones.csv`: tabla detallada. Carpetas `9-6-4/` y `9-6-4-4/`: 20 modelos en total. `datos_sinteticos.csv`: copia exacta del original.

```powershell
.venv\Scripts\python.exe scripts\comparar_redes_sinteticas.py --alternativa 9-6-4-4 --salida output\comparacion_9644_nueva
```

Usar una carpeta inexistente. El comparador conserva como opción anterior `--alternativa 9-8-4-4`; las dos comparaciones se almacenan por separado. No se modifican la base de trabajo, el modelo vigente, la interfaz ni las habilitaciones psicométricas.

Solo simulación con etiquetas sintéticas inventadas. No demuestra validez de recomendaciones sobre personas. Para una conclusión más sólida hacen falta datos independientes y revisión del propósito y etiquetas por responsables profesionales.
