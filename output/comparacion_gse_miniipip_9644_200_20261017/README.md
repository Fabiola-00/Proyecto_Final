# Comparación GSE + Mini-IPIP: 9→6→4 y 9→6→4→4

Fecha de ejecución: 2026-10-17. Alternativa construida y entrenada; modelo vigente conservado.

## Mismos datos y protocolo

CSV idéntico al conjunto actual: 200 datos, particiones 140 entrenamiento/30 validación/30 prueba, nueve entradas GSE/Mini-IPIP y las cuatro salidas aprobadas. No se regeneraron etiquetas ni se mezclaron con DASS/CBI.

Semillas de pesos prefijadas: 31415, 7, 19, 43, 101, 211, 307, 401, 503, 607. Orden SGD 42; tasa 0,03; L2 0,001; máximo 300 épocas; paciencia 25. Cada ejecución restaura la menor pérdida de validación. La prueba no interviene en la selección.

Control con semilla 31415: reproduce exactamente el archivo del modelo actual, incluida época 84 y sus resultados. Las demás inicializaciones no sustituyen al modelo vigente.

## Comparación directa, semilla original 31415

| Medida | Actual 9→6→4 | Alternativa 9→6→4→4 |
|---|---:|---:|
| Parámetros | 88 | 108 (+22,73%) |
| Época elegida / ejecutadas | 84 / 109 | 64 / 89 |
| Coincidencia completa en entrenamiento | 92.14% | 87.14% |
| Coincidencia completa en validacion | 86.67% | 86.67% |
| Coincidencia completa en prueba | 66.67% | 66.67% |
| Pérdida de validación | 0.3854 | 0.4672 |
| Pérdida de prueba | 0.5899 | 0.8517 |
| Abstenciones en los 30 casos de prueba | 6 | 6 |

## Diez inicializaciones por arquitectura

| Medida | 9→6→4 | 9→6→4→4 |
|---|---:|---:|
| Coincidencia completa media en entrenamiento | 94.93% ± 1.92 pp | 85.79% ± 4.10 pp |
| Coincidencia completa media en validacion | 81.33% ± 4.50 pp | 82.67% ± 7.50 pp |
| Coincidencia completa media en prueba | 74.67% ± 4.50 pp | 69.67% ± 5.97 pp |
| Pérdida media de validacion (menor es mejor) | 0.4036 | 0.4830 |
| Pérdida media de prueba (menor es mejor) | 0.5648 | 0.7943 |
| Abstenciones medias en 30 casos de prueba | 5.2 | 4.6 |

En coincidencia completa de prueba: la actual supera en 5 pares, la alternativa en 1, con 4 empates. La diferencia media alternativa−actual es -5.00 pp. El criterio principal prefijado, pérdida media de validación, favorece 9-6-4. No demuestra superioridad universal.

La media de diez inicializaciones de la actual (74,67%) no sustituye su resultado individual guardado (66,67%). ± es la desviación estándar muestral entre semillas, no un intervalo de confianza poblacional.

Coincidencia completa exige las cuatro etiquetas a umbral 0,5. Abstención se calcula por separado si alguna activación está entre 0,35 y 0,65; no es el complemento de aciertos. Activaciones no calibradas.

## Límites y artefactos

Datos generados para ensayo con reglas artificiales explícitas: no son datos de personas ni validación profesional. Los mismos 30 casos de prueba ya fueron consultados: comparación exploratoria, no evaluación independiente nueva. Diez semillas no aumentan los 200 datos. No se optimizaron hiperparámetros por arquitectura ni se eligieron por prueba.

[Modelo alternativo, semilla original](9-6-4-4/modelo_semilla_31415.json) · [Resultados de todas las ejecuciones](ejecuciones.csv) · [Informe estructurado](comparacion.json). Se conservan los 20 modelos en sus carpetas. El CSV copiado y las huellas permiten reproducir la comparación.

```powershell
.venv\Scripts\python.exe scripts\comparar_redes_sinteticas.py --perfil gse-miniipip --alternativa 9-6-4-4 --salida output\comparacion_gse_nueva
```

Usar una carpeta nueva. No accede a SQLite ni habilita instrumentos o recomendaciones personales.

Verificación: 25 pruebas aprobadas en 15,195 s, cuatro nuevas; gradientes de 108 parámetros, restauración, rangos GSE y control idéntico al modelo actual.
