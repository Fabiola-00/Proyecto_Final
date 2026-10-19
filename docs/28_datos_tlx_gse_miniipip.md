# Datos de quince entradas — 2026-10-18

## Decisiones confirmadas

- Propósito orientativo para el desarrollo del Instructor Voluntario, sin decisiones automáticas de ascenso, sanción o aptitud operativa.
- NASA-TLX, GSE y Mini-IPIP; tres dimensiones institucionales y doce de los instrumentos, quince entradas en total.
- NASA-TLX después de una práctica o simulacro común, una aplicación por Gestión.
- Generar 200 registros nuevos; nombre y campo origen «Datos».
- Definir nuevas salidas antes de entrenar, sin reutilizar etiquetas antiguas.

## Entrega y límites

Conjunto en `output/datos_tlx_gse_miniipip_200_20261018/datos.csv`, diccionario, README y manifiesto de huellas en la misma carpeta. Generador reproducible: `scripts/generar_datos_tlx_gse_miniipip.py`. Son puntuaciones agregadas generadas por computadora, no respuestas reales ni una muestra de personal.

Las quince entradas conservan sus escalas originales: Físico/Desempeño/Académica 0–100; GSE 10–40; cinco Mini-IPIP 4–20; seis NASA-TLX 0–100 en pasos de 5. Rendimiento NASA-TLX conserva 0 bueno / 100 malo. No calcular índice ponderado sin comparaciones por pares; las seis valoraciones se guardan por separado. No se crean reactivos ni se selecciona una traducción española oficial en esta entrega.

Partición preliminar 140/30/30, semilla 20261018, permutaciones independientes con cobertura equilibrada de los niveles marginales. Sin hipótesis de correlaciones o prevalencias de población. Sin etiquetas aún, no hay entrenamiento supervisado ni métricas de modelo nuevo. La cobertura de etiquetas deberá revisarse antes del entrenamiento; no usar la partición de prueba para diseñar reglas o seleccionar arquitectura.

Quedan por aprobar los nombres/descripciones de las nuevas salidas y documentar sus reglas experimentales antes del etiquetado. Una futura arquitectura 15→6→4 es una propuesta, no un modelo construido, entrenado ni seleccionado. El modelo operativo 9→6→4, su huella, sus datos, las revisiones ya registradas, los formularios y SQLite permanecen intactos.

Fuente NASA consultada: [manual original](https://www.nasa.gov/wp-content/uploads/2026/03/nasa-tlx-v1-0-searchable-text-and-forms.pdf), escalas y dirección de rendimiento. Las fuentes de GSE y Mini-IPIP y sus algoritmos vigentes se documentan en [integración v29](27_recomendaciones_sistema.md).

## Actualización posterior: cuatro salidas aprobadas y etiquetas V1

El solicitante aprobó Preparación progresiva y confianza; Organización de tareas y manejo de la carga; Comunicación y aprendizaje acompañado; Afrontamiento y seguimiento del bienestar. Esto sustituye el estado anterior de nombres pendientes. Se etiquetaron las 200 filas en una carpeta nueva `output/datos_etiquetados_tlx_gse_miniipip_200_20261018`, sin cambiar el conjunto original, los IDs, las quince entradas o la partición 140/30/30.

Generador `scripts/etiquetar_datos_tlx_gse_miniipip.py`; reglas completas en `reglas.json` y README de la nueva carpeta. Cada etiqueta combina una condición contextual institucional/TLX con un índice ponderado >= 0,50. Son pesos y cortes inventados para experimentar, no baremos de GSE, Mini-IPIP o NASA-TLX. Ningún rasgo por sí solo activa una línea. Las cuatro pueden coexistir; cuatro ceros indican seguimiento general según las reglas, no acreditan capacidad ni bienestar.

Se comprueba cobertura únicamente en entrenamiento/validación, sin explorar prueba para ajustar reglas. Entrenamiento contiene las 16 combinaciones; las cuatro salidas tienen ambas clases en entrenamiento y validación. No se fuerza balance ni se remuestrea. El entrenamiento del nuevo modelo sigue pendiente; no cambia el modelo operativo, SQLite, formularios o revisiones existentes. El diagrama anterior conserva su fecha/estado de propuesta antes de aprobar las salidas.

## Entrenamiento posterior solicitado

El entrenamiento pendiente del corte anterior se completó después para ambas arquitecturas, con diez semillas por red. Ver [comparación verificada](29_comparacion_redes_tlx.md). La recomendación experimental favorece 15→6→4, sin sustituir automáticamente el modelo operativo 9→6→4.
