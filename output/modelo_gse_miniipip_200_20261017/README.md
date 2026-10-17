# Red experimental GSE + Mini-IPIP — 200 casos

Modelo 9→6→4, 88 parámetros. Exclusivamente sintético, sin uso en personas.

Entradas: fisica, desempeno, academica, gse_autoeficacia, mini_extraversion, mini_amabilidad, mini_responsabilidad, mini_neuroticismo, mini_apertura.

Salidas: preparacion_y_confianza, comunicacion_y_colaboracion, aprendizaje_y_autonomia, afrontamiento_y_metas.

## Generación y significado

Se simulan puntuaciones agregadas, no respuestas ni reactivos oficiales. GSE 10–40; cada suma Mini-IPIP 4–20. Todas las entradas se normalizan por su rango completo a 0–1.

Muestreo uniforme independiente por rechazo y estratificación: 200 filas únicas, 16 combinaciones de etiquetas en cada partición, mitad de positivos por salida. No representa prevalencias ni correlaciones poblacionales.

Reglas de etiquetado ficticias (valores normalizados):

- **naturaleza**: HIPOTESIS_DIDACTICA_NO_VALIDADA
- **preparacion_y_confianza**: fisica < 60 y 0.70*(1-F) + 0.20*(1-G) + 0.10*(1-C) > 0.42
- **comunicacion_y_colaboracion**: desempeno < 60 y 0.65*(1-D) + 0.20*(1-G) + 0.075*(1-E) + 0.075*(1-A) > 0.42
- **aprendizaje_y_autonomia**: academica < 60 y 0.65*(1-Ac) + 0.20*(1-G) + 0.075*(1-O) + 0.075*(1-C) > 0.42
- **afrontamiento_y_metas**: G < 0.50 y 0.65*(1-G) + 0.20*N + 0.15*(1-C) > 0.50
- **leyenda**: F=fisica,D=desempeno,Ac=academica,G=GSE,E=extraversion,A=amabilidad,C=responsabilidad,N=neuroticismo,O=apertura; todos normalizados 0-1.
- **limites**: Cortes y pesos inventados solo para simulación. Ningún rasgo activa por sí solo una salida. GSE no tiene corte universal. No implican causalidad ni necesidades reales.

Estas ponderaciones NO constituyen una interpretación validada de personalidad. Las primeras tres salidas requieren además una nota institucional menor a 60; la cuarta requiere GSE normalizada menor a 0,50, corte inventado. Ningún rasgo aislado basta. GSE carece de corte universal.

## Entrenamiento y evaluación

Semillas fijas: datos 2718, pesos 31415, orden SGD 42. L2 0,001, tasa 0,03, máximo 300 épocas, paciencia 25. Se restaura la mejor pérdida de validación; la prueba no interviene en la selección.

Época elegida: 84; ejecutadas: 109.

| Partición | Casos | Coincidencia de las 4 etiquetas a umbral 0,5 | Abstenciones |
|---|---:|---:|---:|
| entrenamiento | 140 | 92.14% | 14 |
| validacion | 30 | 86.67% | 3 |
| prueba | 30 | 66.67% | 6 |

La coincidencia anterior fuerza etiquetas a 0,5; no equivale a recomendaciones emitidas. La simulación se abstiene si alguna activación está entre 0,35 y 0,65. Las activaciones no son probabilidades calibradas.

Los 200 casos sirven para verificar aprendizaje de reglas artificiales; no bastan para acreditar utilidad real. No comparar estas métricas directamente con DASS/CBI: cambiaron datos, etiquetas y significado.

## Reproducir

Desde la raíz, ejecutar con el Python existente: `python scripts/entrenar_red_gse_miniipip.py --salida output/nueva_ejecucion_gse`. El destino debe ser nuevo. No accede a SQLite, formularios, rutas ni personas.

Se conservan íntegros el modelo DASS/CBI y sus comparaciones. Esta versión es el nuevo experimento solicitado; no se integra automáticamente en Flask.

Fuentes de rangos y dimensiones: [GSE](https://userpage.fu-berlin.de/~health/faq_gse.pdf) y [Mini-IPIP en español](https://ipip.ori.org/Spanishmini-IPIPposneg.htm).


Verificación de esta entrega: 31 pruebas aprobadas en 25,482 s (siete nuevas), sintaxis de cuatro archivos Python correcta y huellas de artefactos actuales/anteriores comprobadas. Sin suite global ni validación profesional.

## Diagrama del modelo

[PNG de alta resolución](diagrama_red_gse_miniipip.png) · [SVG vectorial](diagrama_red_gse_miniipip.svg). Representa 19 nodos y 78 conexiones, nueve entradas con rangos, activaciones, cuatro salidas, normalización, entrenamiento y métricas del modelo guardado. Generar con `python scripts/graficar_red_gse_miniipip.py`. No reentrena ni modifica los artefactos originales.
