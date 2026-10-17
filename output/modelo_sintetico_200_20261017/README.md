# Modelo compacto para 200 registros — 2026-10-17

**Entrenado exclusivamente con datos sintéticos. Sin uso para recomendaciones sobre personas.**

**Selección confirmada por el solicitante el 2026-10-17:** conservar este modelo original 9→6→4 para las recomendaciones del prototipo. Se mantienen los pesos originales de semilla 31415 y época 55; no se adopta una semilla diferente de los ensayos. [Registro de selección con huellas SHA-256](seleccion_modelo.json). Las redes de dos capas quedan como alternativas comparativas. El registro no habilita inferencia en el panel ni constituye validación profesional/institucional.

[Diagrama PNG en alta resolución](diagrama_red_200.png) · [Diagrama SVG vectorial](diagrama_red_200.svg).

El diagrama muestra las nueve entradas agrupadas, seis neuronas ocultas, cuatro salidas combinables, las 78 conexiones y 10 sesgos, normalización, activaciones y entrenamiento. Los trazos tienen grosor uniforme y no representan importancia de pesos. Se genera desde los artefactos guardados con `.venv\Scripts\python.exe scripts\graficar_red_sintetica.py`, usando Pillow ya disponible, sin entrenar ni modificar datos.

| Característica | Valor |
|---|---|
| Total de registros | 200, sin mezclar los 2.048 de la ejecución anterior |
| Entrenamiento / validación / prueba | 140 / 30 / 30 |
| Arquitectura | 9 entradas → 6 ocultas → 4 salidas; 88 parámetros |
| Grupos de entradas | Física, Desempeño, Académica, tres subescalas DASS y tres CBI |
| Optimización | SGD, tasa 0,03; L2=0,001 en pesos |
| Parada temprana | Menor entropía cruzada en validación, paciencia 25, máximo 300 épocas |
| Ejecución obtenida | Detenida en época 80; restaurada época 55 |
| Coincidencia conjunta en prueba | 24 de 30 casos (80%), umbral binario 0,5 |
| Abstenciones en prueba | 7 de 30; intervalo de activación 0,35–0,65 |

Las cuatro salidas combinables siguen siendo apoyo físico, acompañamiento en Desempeño, formación y revisión profesional. Las 16 combinaciones aparecen en las tres particiones. Ocho tienen 12 casos y ocho tienen 13 en el conjunto completo; cada salida binaria está equilibrada en cada partición. Ninguna fila se comparte entre particiones.

`datos_sinteticos.csv` contiene los 200 casos con su partición; `modelo.json` contiene pesos/restauración y `informe.json` contiene métricas, semillas y huella SHA-256 del CSV. Las etiquetas proceden de reglas didácticas inventadas, no de profesionales. El porcentaje no valida recomendaciones reales; con 30 casos, un error cambia el resultado en 3,33 puntos porcentuales. Las activaciones no son probabilidades calibradas. La abstención se informa por separado de las coincidencias.

Para reproducir, desde la raíz del proyecto y con una carpeta inexistente:

```powershell
.venv\Scripts\python.exe scripts\entrenar_red_sintetica.py --salida output\ensayo_200_nuevo
```

Las semillas, dimensiones, umbrales, regularización y paciencia se fijaron antes de evaluar prueba; no se ajustaron para mejorar su porcentaje. No se consulta SQLite ni se añaden dependencias. [Especificación y límites](../../docs/25_psicometria_y_red_experimental.md).
