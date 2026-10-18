# Datos NASA-TLX, GSE y Mini-IPIP

200 registros nuevos, 15 entradas, origen visible **Datos**. Puntuaciones generadas por computadora para experimentación; no proceden de personas reales.

## Alcance

Una aplicación NASA-TLX por Gestión después de una práctica o simulacro común. El conjunto no se vincula a usuarios, fechas, prácticas ni gestiones reales. Solo puntuaciones agregadas, sin reactivos ni respuestas individuales.

No hay etiquetas: el solicitante decidió definir nuevas salidas antes de entrenar. Este conjunto aún no permite entrenamiento supervisado. No se ha entrenado ni sustituido el modelo vigente ni cambiado formularios o SQLite.

## Variables

| Variable | Rango | Paso |
|---|---:|---:|
| fisica: Físico promedio | 0–100 | 0.5 |
| desempeno: Desempeño promedio | 0–100 | 0.5 |
| academica: Académica acumulada con tope | 0–100 | 1 |
| gse_autoeficacia: GSE: autoeficacia general | 10–40 | 1 |
| mini_extraversion: Mini-IPIP: extraversión | 4–20 | 1 |
| mini_amabilidad: Mini-IPIP: amabilidad | 4–20 | 1 |
| mini_responsabilidad: Mini-IPIP: responsabilidad | 4–20 | 1 |
| mini_neuroticismo: Mini-IPIP: neuroticismo | 4–20 | 1 |
| mini_apertura: Mini-IPIP: apertura | 4–20 | 1 |
| tlx_demanda_mental: NASA-TLX: demanda mental | 0–100 | 5 |
| tlx_demanda_fisica: NASA-TLX: demanda física | 0–100 | 5 |
| tlx_demanda_temporal: NASA-TLX: demanda temporal | 0–100 | 5 |
| tlx_rendimiento: NASA-TLX: rendimiento percibido (0 bueno; 100 malo) | 0–100 | 5 |
| tlx_esfuerzo: NASA-TLX: esfuerzo | 0–100 | 5 |
| tlx_frustracion: NASA-TLX: frustración | 0–100 | 5 |

NASA-TLX usa seis valoraciones individuales 0–100 en pasos de 5. Rendimiento conserva el sentido del formulario: 0 bueno, 100 malo; las demás van de baja a alta demanda/esfuerzo/frustración. No se calcula el índice ponderado original ni se inventan pesos.

## Generación y verificación

Semilla 20261018. Cobertura marginal equilibrada y permutaciones independientes. Muestreo de rangos posibles, sin asumir distribución, correlación o prevalencia real. Las combinaciones extremas son deliberadas para ensayar límites, no perfiles de una población.

Partición preliminar fija 140 entrenamiento / 30 validación / 30 prueba. Sin estratificación por salidas todavía inexistentes; revisar cobertura de etiquetas antes de entrenar y documentar cualquier cambio de versión. No consultar prueba para elegir reglas, arquitectura o pesos.

Verificado: 200 filas únicas, 15 valores completos por fila, IDs únicos, rangos, pasos y particiones. Normalización futura por rangos teóricos, no por mínimos/máximos observados.

Reproducir desde la raíz: `python scripts/generar_datos_tlx_gse_miniipip.py --salida output/nueva_carpeta_datos`. Se exige destino nuevo.

## Fuentes

- https://www.nasa.gov/wp-content/uploads/2026/03/nasa-tlx-v1-0-searchable-text-and-forms.pdf
- https://userpage.fu-berlin.de/~health/spanscal.htm
- https://ipip.ori.org/Spanishmini-IPIPposneg.htm
