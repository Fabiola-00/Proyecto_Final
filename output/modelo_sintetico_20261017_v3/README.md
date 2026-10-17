# Entrenamiento experimental — 2026-10-17

**Ejecución histórica de 2.048 casos.** El modelo vigente fue adaptado a [200 registros](../modelo_sintetico_200_20261017/README.md). El script actual por defecto genera 200; el comando original conservado abajo describe la ejecución anterior, no reproduce este modelo con los nuevos valores por defecto. El generador histórico se conserva mediante `datos_sinteticos(por_patron=128)`.

**Solo datos sintéticos. No usar para recomendaciones sobre personas.**

- `datos_sinteticos.csv`: 2.048 casos sin identidad, 16 combinaciones equilibradas de objetivos inventados; particiones explícitas 1.424/304/320.
- `modelo.json`: pesos de una red 9→16→4, normalización y orden de entradas/salidas. Estado ENTRENADO_SOLO_SINTETICO. Ninguna ruta Flask carga estos pesos.
- `informe.json`: semillas, huella del CSV, coincidencias binarias (umbral 0,5) y abstenciones (intervalo 0,35–0,65).

Prueba reservada: coincidencia completa 0,85625; 53 abstenciones entre 320 casos. Estas cifras miden reproducción de reglas sintéticas; no acreditan exactitud clínica, aptitud operativa ni recomendaciones profesionales. Las activaciones sigmoidales no son probabilidades calibradas.

Generación independiente de cada subescala, en rejillas numéricas alcanzables; no pretende reproducir distribución, correlación o prevalencia en SBRAB. Los objetivos didácticos usan nota <60 y máximo psicométrico normalizado >0,6, sin significado clínico/institucional. Las respuestas individuales no forman parte del CSV.

Para reproducir desde la raíz del proyecto, usar una carpeta inexistente:

```powershell
.venv\Scripts\python.exe scripts\entrenar_red_sintetica.py --salida output\nuevo_ensayo --epocas 60
```

El script no lee SQLite ni modifica el entorno. La guía completa y las propuestas para las 16 combinaciones están en [la especificación](../../docs/25_psicometria_y_red_experimental.md).
