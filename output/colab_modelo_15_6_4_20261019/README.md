# SICOSE · Modelo 15 → 6 → 4 para Google Colab

- [Notebook listo para subir](SICOSE_Modelo_15_6_4.ipynb).
- [Código Python autocontenido](SICOSE_Modelo_15_6_4.py).
- [Verificación local](verificacion_local.json).

## Ejecutar

1. Descarga el archivo `.ipynb`.
2. Abre [Google Colab](https://colab.research.google.com/) y elige **Archivo → Subir cuaderno**. Es el procedimiento indicado en la [documentación oficial](https://research.google.com/colaboratory/faq.html).
3. Ejecuta las celdas en orden o usa **Ejecutar todo**. No necesitas GPU, Drive, Flask ni instalar paquetes.
4. Edita las quince puntuaciones del diccionario `ejemplo` si deseas probar otros valores agregados. Se validan nombres, faltantes y rangos.
5. Para reproducir el entrenamiento, cambia `REENTRENAR = False` por `True` en la sección 7. La red reentrenada se mantiene separada de la red vigente.

El `.py` también contiene todos los Datos y pesos. Para ejecutarlo fuera de Colab: `python SICOSE_Modelo_15_6_4.py`, desde una carpeta destinada a este ejercicio. Crea `resultados_colab_sicose/` con archivos del ejercicio; no se conecta al proyecto.

## Contenido y límites

18 celdas (nueve de código): explicación de entradas institucionales/pruebas, pesos y 200 Datos embebidos, código completo del modelo y argmax, verificación de las 200 predicciones, ejemplo editable, evaluación original, reentrenamiento opcional y exportación JSON/CSV. Sin descargas de paquetes, archivos auxiliares, credenciales, respuestas reales o consultas de red desde el código.

Modelo de 124 parámetros, semilla 401, época elegida 196 de 221 ejecutadas. SGD lote 1, orden 42, tasa 0,03, L2 0,001, máximo 300 y paciencia 25. Partición fija 140/30/30. Se elige una recomendación por argmax; empates exactos por orden original. La recomendación es una propuesta y el notebook no realiza confirmaciones institucionales.

Las cuatro etiquetas de entrenamiento son combinables y provienen de reglas didácticas sobre Datos generados por computadora. La coincidencia a corte 0,50/BCE se informa como evaluación original de esas etiquetas, **no como exactitud de una recomendación única**. La distribución por argmax tampoco mide exactitud. Prueba ya consultada, sin nueva validación independiente ni validación sobre personas. Las puntuaciones no son probabilidades de certeza.

Los JSON originales conservan sus metadatos del experimento (incluidos umbrales históricos); la selección actual está en el código y en `politica_seleccion.json`. No se sustituye argmax por esos umbrales. Los nuevos pesos, si se entrenan, se exportan a otro archivo y no se adoptan en SICOSE.

## Verificación realizada

Ejecutadas localmente las nueve celdas con reentrenamiento desactivado y activado; 200 predicciones coinciden exactamente y el reentrenamiento reproduce pesos e historial originales sin diferencias, época elegida 196. Se ejecutó también el `.py` en una carpeta temporal independiente. Comprobados huellas, particiones, argmax para las cuatro salidas/empate, rechazo de faltantes/rangos/booleanos, rechazo de usar prueba para entrenar y archivos exportados. JSON y estructura de celdas comprobados por código; no se instaló `nbformat` para validación formal de su esquema.

**No ejecutado dentro del servicio de Google Colab.** Las operaciones utilizan Python estándar y no rutas locales de Windows. No se cambió el sistema, la base, el entorno ni los artefactos de entrenamiento originales.

Recrear el paquete desde el repositorio: `.venv/Scripts/python.exe scripts/generar_notebook_colab.py`. Reutiliza el código numérico y selector del proyecto y verifica sus artefactos originales. No vuelve a generar etiquetas ni Datos.
