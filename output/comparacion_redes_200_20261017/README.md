# Comparación: 9→6→4 frente a 9→8→4→4 — 2026-10-17

**El ensayo favorece conservar 9→6→4. El modelo actual no se sustituyó.**

Comparación exploratoria con los mismos 200 registros sintéticos y las mismas particiones 140/30/30. Diez inicializaciones prefijadas por arquitectura, 20 entrenamientos en total. El conjunto de prueba de 30 casos ya fue consultado en la entrega anterior; no constituye una validación independiente nueva. Repetir con semillas diferentes estudia la sensibilidad a la inicialización, no agrega datos.

| Medida | Actual 9→6→4 | Alternativa 9→8→4→4 |
|---|---:|---:|
| Capas ocultas | 1 | 2 |
| Parámetros | 88 | 136 (+54,55%) |
| Coincidencia completa en entrenamiento | 89,36% ± 1,73 pp | 88,14% ± 4,35 pp |
| Coincidencia completa en validación | 82,67% ± 3,44 pp | 83,67% ± 5,54 pp |
| Pérdida media de validación, menor es mejor | **0,4347** | 0,4883 |
| Coincidencia completa en prueba | **80,33% ± 2,92 pp** | 76,00% ± 4,39 pp |
| Rango de coincidencia en prueba | 76,67%–83,33% | 70,00%–83,33% |
| Pérdida media de prueba, menor es mejor | 0,4911 | 0,6213 |
| Abstenciones medias por 30 casos de prueba | 6,1 | 3,8 |
| Época elegida media | 120,2 | 63,5 |
| Tiempo de entrenamiento medio en este ensayo | 0,548 s | 0,489 s |

± corresponde a la desviación estándar muestral entre inicializaciones; no es un intervalo de confianza sobre personas. Coincidencia completa significa acertar simultáneamente las cuatro etiquetas al umbral 0,5. Abstención se calcula por separado con el intervalo 0,35–0,65: no es una quinta clase ni complementa el porcentaje de aciertos. Menos abstenciones no equivale automáticamente a mejor calidad.

Con semillas pareadas, la red actual obtuvo mayor coincidencia en prueba en ocho ejecuciones; la alternativa en una y hubo un empate. La diferencia media profunda–actual fue −4,33 puntos porcentuales. Esto es descriptivo, sin afirmar significación estadística. En validación la alternativa tuvo algo más de coincidencias binarias, pero peor entropía cruzada media: estas métricas evalúan aspectos distintos. El criterio principal fijado fue **menor entropía cruzada media de validación**, que favoreció a la actual.

El tiempo total fue algo menor para la alternativa en esta ejecución porque la parada temprana eligió épocas anteriores. No demuestra que una pasada por una red con más capas sea más barata; los tiempos dependen del equipo, carga y épocas realizadas.

## Condiciones controladas

- CSV original copiado sin regeneración, SHA-256 `e242160516c378d22221da0ae37d9cc78af81951e7e66a7a94a1848e0fc75015`.
- Semillas de pesos: 31415, 7, 19, 43, 101, 211, 307, 401, 503 y 607. Mismo rango de inicialización uniforme [−0,5; 0,5] y sesgos iniciales cero. Igual semilla de orden de entrenamiento 42.
- Ambas usan tanh en sus capas ocultas y cuatro sigmoides de salida; mismos rangos y normalización de entradas.
- SGD, tasa 0,03, L2=0,001, máximo 300 épocas, paciencia 25. Cada ejecución restaura la menor pérdida de validación. La prueba nunca actualiza pesos ni elige épocas.
- No se buscó una configuración óptima diferente para cada arquitectura. Las conclusiones se limitan a este protocolo y a estas etiquetas sintéticas.
- La ejecución 9→6→4 con semilla 31415 reproduce exactamente los pesos existentes y las métricas de prueba de la entrega anterior. En esa semilla concreta: 24/30 aciertos completos frente a 22/30 de la alternativa.
- Se guardan las 20 ejecuciones, no solo la de mejor resultado. Las semillas señaladas como mejores en el JSON se identifican exclusivamente por validación; no sustituyen al modelo vigente.

## Archivos y reproducción

`comparacion.json`: protocolo, resúmenes, diferencias pareadas y métricas de cada ejecución. `ejecuciones.csv`: tabla detallada. `9-6-4/` y `9-8-4-4/`: pesos por semilla. `datos_sinteticos.csv`: copia exacta del conjunto original.

```powershell
.venv\Scripts\python.exe scripts\comparar_redes_sinteticas.py --salida output\comparacion_nueva
```

La carpeta debe ser inexistente. Se requiere la ejecución original de 200 casos disponible para comprobar sus huellas y reproducir el control. La duración puede variar; pesos y métricas son reproducibles. No hay lectura de SQLite, habilitación de instrumentos ni inferencia personal.

La etiqueta de revisión profesional proviene de reglas didácticas inventadas. El resultado no demuestra validez de recomendaciones reales ni superioridad universal de una arquitectura. Para una conclusión más sólida se necesitan datos independientes y evaluación del propósito con responsables profesionales.
