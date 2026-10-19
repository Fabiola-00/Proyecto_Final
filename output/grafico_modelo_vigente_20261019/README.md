# Modelo de Red Neuronal vigente · 19/10/2026

[Gráfico PNG de alta resolución](modelo_red_neuronal_actual.png) · [SVG vectorial](modelo_red_neuronal_actual.svg) · [Configuración verificada](verificacion.json)

Arquitectura 15 → 6 → 4, 124 parámetros. Tres entradas institucionales (Físico, Desempeño, Académica) separadas de doce entradas de GSE, Mini-IPIP y NASA-TLX. Las cuatro salidas siguen siendo sigmoides; fuera de la red se elige la mayor puntuación (argmax) para proponer una sola recomendación. Empates exactos por orden original. Revisión humana y confirmación antes del reporte.

Datos: 200 registros, reparto 140/30/30. Generados por computadora para experimentación, sin respuestas reales ni validación sobre personas. El gráfico no muestra una nueva medición de acierto. La política de selección actual no es el criterio de evaluación usado en las comparaciones originales.

Modelo original verificado: semilla 401, época elegida 196 de 221 ejecutadas; tasa 0,03, L2 0,001, paciencia 25 y máximo 300 épocas. SHA-256 `a98b65067700a975bb1993fe9510235900c21e15009adec8a18f46bca05e1353`. Se preservan los artefactos y gráficos anteriores.

Reproducción: `.venv/Scripts/python.exe scripts/graficar_modelo_tlx_vigente.py` desde la raíz. Comprueba arquitectura, entradas, salidas, rangos, número de parámetros, huellas del modelo/Datos, particiones y metadatos. Genera un PNG de 4000 × 3860 y un SVG con título/descripcion accesibles. No entrena, abre SQLite ni modifica el sistema.
