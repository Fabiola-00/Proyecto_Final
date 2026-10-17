# Informe didáctico del modelo neuronal seleccionado

## SICOSE | Arquitectura 9 → 6 → 4 | GSE + Mini-IPIP

Fecha de elaboración y verificación: 17 de octubre de 2026. Destinatarios: estudiantes de primeros años de universidad. Alcance: explicar la implementación y el entrenamiento existentes; no se modifica ni se vuelve a entrenar el modelo para elaborar este documento.

El modelo seleccionado es el archivo `output/modelo_gse_miniipip_200_20261017/modelo.json`, con semilla de pesos 31415 y mejores pesos de la época 84. Se conserva como experimento académico. Los 200 datos fueron generados artificialmente mediante reglas explícitas y no contienen información de instructores reales. En este informe se usa el rótulo «Datos» para mantener la presentación solicitada, sin cambiar su procedencia experimental.

## 1. Qué hace el modelo y qué significa aprender

Una red neuronal es una función matemática con números ajustables. Recibe valores de entrada, los combina y produce valores de salida. Aprender consiste en modificar esos números para que las salidas se aproximen a respuestas objetivo conocidas en los ejemplos de entrenamiento.

En este caso recibe nueve puntuaciones y produce cuatro activaciones asociadas a propuestas de acompañamiento. Es un problema de aprendizaje supervisado: cada ejemplo contiene entradas y cuatro etiquetas objetivo. Una etiqueta 1 indica que el generador propuso una salida; una etiqueta 0 indica que no la propuso.

Es también una clasificación multietiqueta: las cuatro salidas pueden combinarse. Un ejemplo puede tener el objetivo `[1, 0, 1, 0]`, que representa preparación y confianza junto con aprendizaje y autonomía. No es obligatorio elegir una sola categoría.

El entrenamiento realizado aprende a aproximar las reglas que generaron las etiquetas. No descubre por sí mismo qué recomendaciones son correctas para personas reales. La utilidad técnica del experimento consiste en estudiar el procesamiento, el aprendizaje, la evaluación y sus límites de forma reproducible.

## 2. Cómo leer la arquitectura 9 → 6 → 4

El número 9 representa las entradas; el 6, las neuronas de una capa oculta; y el 4, las neuronas de salida. Las flechas indican la dirección del cálculo. Es un perceptrón multicapa, abreviado MLP, de propagación hacia adelante: la información avanza desde las entradas hasta las salidas, sin ciclos ni memoria de eventos anteriores.

| Parte | Cantidad | Función |
|---|---:|---|
| Entradas | 9 | Presentar las puntuaciones normalizadas |
| Capa oculta | 6 neuronas | Construir combinaciones no lineales de las nueve entradas |
| Capa de salida | 4 neuronas | Producir una activación independiente por recomendación |

La capa de entrada no aprende pesos propios. Hay dos transformaciones con parámetros aprendidos: entrada a capa oculta y capa oculta a salida. Por eso puede describirse como tres niveles de representación, pero tiene una sola capa oculta y dos capas de cálculo entrenables.

Las neuronas ocultas no tienen nombres psicológicos. No puede afirmarse que h1 mida confianza o que h2 mida colaboración: sus funciones surgen conjuntamente de los pesos aprendidos.

![Diagrama del modelo seleccionado](../output/modelo_gse_miniipip_200_20261017/diagrama_red_gse_miniipip.png)

## 3. Las nueve entradas y su orden

El orden de las columnas forma parte del modelo. Intercambiar dos puntuaciones cambia el significado del cálculo aunque ambas estén en rangos válidos.

| Posición | Entrada | Rango original | Significado previsto |
|---|---|---|---|
| x1 | Físico | 0 a 100 | Promedio de las dos pruebas físicas |
| x2 | Desempeño | 0 a 100 | Promedio de Jefe y Comandante |
| x3 | Académica | 0 a 100 | Acumulado de cursos y operaciones con tope de 100 |
| x4 | GSE: autoeficacia | 10 a 40 | Puntuación global del cuestionario |
| x5 | Mini-IPIP: extraversión | 4 a 20 | Dimensión de personalidad |
| x6 | Mini-IPIP: amabilidad | 4 a 20 | Dimensión de personalidad |
| x7 | Mini-IPIP: responsabilidad | 4 a 20 | Dimensión de personalidad |
| x8 | Mini-IPIP: neuroticismo | 4 a 20 | Dimensión de personalidad |
| x9 | Mini-IPIP: apertura | 4 a 20 | Dimensión de personalidad |

Las tres primeras entradas constituyen la evaluación institucional. Las seis restantes proceden de las pruebas psicométricas: una puntuación GSE y cinco de Mini-IPIP. Se conserva cada dimensión por separado; no se promedian las dos pruebas como una sola nota psicológica.

GSE tiene diez ítems y una puntuación global de autoeficacia percibida. Los autores no establecen un punto de corte universal. Mini-IPIP tiene veinte ítems, cuatro por dimensión; la representación elegida para este experimento usa cinco sumas de 4 a 20 después de corregir los ítems inversos. [Documentación GSE](https://userpage.fu-berlin.de/~health/faq_gse.pdf), [clave española Mini-IPIP](https://ipip.ori.org/Spanishmini-IPIPposneg.htm).

El experimento utiliza puntuaciones agregadas posibles. No administra cuestionarios ni calcula estas sumas desde respuestas reales. Los significados institucionales describen el diseño de integración previsto, no una conexión activa con los expedientes del sistema. El neuroticismo se mantiene en su dirección original; no se renombra silenciosamente como estabilidad emocional.

## 4. Normalización: poner las entradas en una escala común

Normalizar es transformar números de diferentes rangos a una escala comparable. Aquí se utiliza el mínimo y máximo teóricos de cada entrada:

```text
valor_normalizado = (valor_original - minimo) / (maximo - minimo)
```

| Entrada de ejemplo | Operación | Valor normalizado |
|---|---|---:|
| Físico = 75 | (75 - 0) / (100 - 0) | 0,75 |
| GSE = 25 | (25 - 10) / (40 - 10) | 0,50 |
| Responsabilidad = 12 | (12 - 4) / (20 - 4) | 0,50 |

Así, un 25 en GSE no se divide simplemente entre 40. Su mínimo es 10, y se debe restar antes de dividir. El mínimo de cada rango se transforma en 0 y el máximo en 1.

Esta transformación no convierte las puntuaciones en percentiles, diagnósticos ni porcentajes de aptitud. Un GSE normalizado de 0,50 significa que está a mitad de su rango posible; no que la persona tiene «50% de confianza».

Se usan rangos teóricos fijos y no mínimos o máximos aprendidos del conjunto de prueba. No hace falta ajustar un normalizador a esos 30 casos. Tampoco se recortan valores fuera de rango para que parezcan válidos: se rechazan.

El modelo exige nueve números finitos. Rechaza blancos, valores ausentes, NaN, infinito, booleanos y puntuaciones fuera de rango. No sustituye una prueba pendiente por cero; en particular, cero no es una puntuación válida de GSE ni de Mini-IPIP.

## 5. Pesos, sesgos y los 88 parámetros

Un peso controla cómo participa una señal en una combinación matemática. Un sesgo es un término adicional que permite desplazar esa combinación sin depender de una entrada particular. Ambos se ajustan durante el entrenamiento.

| Componente | Dimensión | Cantidad de parámetros |
|---|---|---:|
| W1: pesos de entradas a capa oculta | 6 filas por 9 columnas | 54 |
| b1: sesgos de capa oculta | 6 valores | 6 |
| W2: pesos de capa oculta a salidas | 4 filas por 6 columnas | 24 |
| b2: sesgos de salida | 4 valores | 4 |
| Total | 78 pesos y 10 sesgos | 88 |

La operación de una neurona empieza con una suma ponderada. Por ejemplo, para la neurona oculta h1:

```text
z1 = w11*x1 + w12*x2 + ... + w19*x9 + b1
h1 = tanh(z1)
```

Los pesos no son porcentajes de importancia ni tienen que sumar 1. Pueden ser negativos y superar el rango de inicialización después de aprender. El signo de un peso individual tampoco basta para afirmar una relación causal con la recomendación final: existen otras conexiones y una transformación no lineal intermedia.

Los seis valores ocultos alimentan cada salida. Todas las entradas se conectan con todas las neuronas ocultas y todas las ocultas con todas las salidas; esto se llama conexión densa o completa.

## 6. Funciones de activación

Una función de activación transforma la suma que recibe una neurona. Introduce relaciones no lineales; sin ella, encadenar transformaciones lineales seguiría siendo equivalente a una sola transformación lineal.

### 6.1 Capa oculta: tangente hiperbólica, tanh

La capa oculta aplica tanh a cada una de sus seis sumas. Su salida se encuentra entre -1 y 1. Cerca de cero cambia con rapidez y, para valores muy positivos o negativos, se aproxima gradualmente a los extremos.

```text
tanh(0) = 0
tanh(1) ≈ 0,7616
tanh(-1) ≈ -0,7616
```

Esta función permite combinar señales con efectos positivos o negativos y es derivable, propiedad necesaria para calcular cómo ajustar los pesos. Es una elección aplicada en este experimento; no se demostró que sea la mejor activación para este problema.

### 6.2 Capa de salida: sigmoide

Cada salida usa una sigmoide independiente:

```text
sigmoide(z) = 1 / (1 + exp(-z))
```

Devuelve un valor entre 0 y 1. Por ejemplo, con z = 0 devuelve 0,5 y con z = 2 devuelve aproximadamente 0,8808. Las cuatro activaciones no deben sumar 1 porque las recomendaciones pueden coexistir.

Se eligieron cuatro sigmoides, no una función softmax que obligue a competir entre categorías. Las activaciones sirven para aplicar los umbrales del experimento; no están calibradas como probabilidades reales de necesidad de apoyo.

Para estabilidad numérica, el código limita el argumento usado por la exponencial al intervalo [-40, 40]. La pérdida utiliza un mínimo de 0,000000000001 antes de tomar logaritmos. Son protecciones aritméticas, no reglas psicométricas.

## 7. Las cuatro salidas aprobadas

| Salida | Nombre | Tipo de propuesta |
|---|---|---|
| y1 | Preparación y confianza | Preparación física progresiva, metas alcanzables, hábitos y reconocimiento de avances |
| y2 | Comunicación y colaboración | Coordinación, participación gradual y retroalimentación individual |
| y3 | Aprendizaje y autonomía | Capacitación práctica, objetivos de aprendizaje y seguimiento |
| y4 | Afrontamiento y metas | Orientación voluntaria sobre exigencias, organización de metas y estrategias de afrontamiento |

Los nombres corresponden a categorías de acompañamiento propuestas y aprobadas para el prototipo. El texto asociado se recupera de una lista fija: el modelo no redacta libremente como un modelo de lenguaje ni produce un diagnóstico.

La salida numérica tiene cuatro posiciones, por ejemplo `[0,82; 0,14; 0,76; 0,09]`. Este ejemplo ilustra el formato y no corresponde a una predicción sobre una persona. Después se aplica una regla de lectura, explicada en la sección 13.

## 8. Datos: qué representan los 200 ejemplos

Cada fila contiene identificador, procedencia, partición, nueve entradas y cuatro etiquetas. Los identificadores numeran ejemplos de laboratorio; no corresponden a personas ni son entradas del modelo.

El generador propone Físico y Desempeño entre 0 y 100 en incrementos de 0,5; Académica entre 0 y 100 en enteros; GSE entre 10 y 40 en enteros; y cada dimensión Mini-IPIP entre 4 y 20 en enteros. Se simulan sumas posibles, sin generar las respuestas individuales de los cuestionarios.

Primero se proponen valores con muestreo uniforme independiente. Luego se aceptan o rechazan según la combinación objetivo que se necesita completar. Por tanto, el conjunto finalmente aceptado está condicionado por las reglas y el equilibrio de etiquetas; no se puede afirmar que conserve independencia o distribución uniforme poblacional.

Hay 16 combinaciones posibles de cuatro etiquetas binarias, porque 2 elevado a 4 es 16. Todas aparecen en cada partición. Las filas de entrada son únicas, sin duplicados entre particiones. Cada salida tiene 100 etiquetas positivas y 100 negativas en los 200 datos; ese equilibrio se construyó deliberadamente y no representa prevalencias reales.

### 8.1 Reglas utilizadas para asignar etiquetas

Las siguientes expresiones son hipótesis didácticas inventadas. No son baremos de GSE o Mini-IPIP ni criterios institucionales de evaluación. Sus coeficientes se eligieron para construir un problema de aprendizaje, no se estimaron a partir de decisiones profesionales.

Para leerlas, F es Físico, D es Desempeño, Ac es Académica, G es GSE, E es extraversión, A es amabilidad, C es responsabilidad, N es neuroticismo y O es apertura. Todas estas letras representan valores normalizados entre 0 y 1.

```text
y1_objetivo = 1 si:
F < 0,60 y 0,70*(1-F) + 0,20*(1-G) + 0,10*(1-C) > 0,42

y2_objetivo = 1 si:
D < 0,60 y 0,65*(1-D) + 0,20*(1-G)
            + 0,075*(1-E) + 0,075*(1-A) > 0,42

y3_objetivo = 1 si:
Ac < 0,60 y 0,65*(1-Ac) + 0,20*(1-G)
             + 0,075*(1-O) + 0,075*(1-C) > 0,42

y4_objetivo = 1 si:
G < 0,50 y 0,65*(1-G) + 0,20*N + 0,15*(1-C) > 0,50

Si no se cumplen las condiciones de una salida, su etiqueta es 0.
```

Por ejemplo, con F = 0,40, G = 0,50 y C = 0,50, la suma de la primera regla es 0,42 + 0,10 + 0,05 = 0,57. Como F < 0,60 y 0,57 > 0,42, el generador asigna y1 = 1.

Las primeras tres reglas requieren una nota institucional inferior a 60; un rasgo de personalidad por sí solo no activa esas etiquetas. La cuarta exige además G < 0,50, equivalente a GSE < 25. Este último corte es inventado para el ensayo: no debe presentarse como un umbral oficial de autoeficacia.

Es importante reconocer una limitación del diseño: aunque ningún rasgo aislado basta, las reglas sí hacen que determinados rasgos modifiquen las etiquetas en casos cercanos al límite. Esa relación no está validada y requeriría revisión antes de cualquier uso con personas. Entrenar una red para reproducirla no la convierte en evidencia científica.

## 9. Separación de entrenamiento, validación y prueba

| Partición | Casos | Proporción | Para qué se usa |
|---|---:|---:|---|
| Entrenamiento | 140 | 70% | Calcular el error y modificar pesos y sesgos |
| Validación | 30 | 15% | Elegir la mejor época y decidir cuándo detenerse |
| Prueba | 30 | 15% | Describir el resultado después de elegir los pesos |

Una analogía útil es estudiar con ejercicios, comprobar el progreso con un simulacro y realizar una evaluación final. Los tres conjuntos tienen funciones distintas. La validación no realiza actualizaciones de pesos, pero sí influye en qué versión se conserva. Por eso no equivale a un conjunto independiente para la evaluación final.

Cada salida tiene 70 positivos y 70 negativos en entrenamiento, y 15 positivos y 15 negativos tanto en validación como en prueba. Las particiones se fijan antes del entrenamiento; el código rechaza entrenamiento o validación con etiquetas de partición incorrectas y detecta solapamientos entre ambos conjuntos.

La prueba no se utilizó para elegir la época 84. Sin embargo, esos mismos 30 casos se han consultado después en comparaciones de arquitecturas. Desde ese momento, los resultados comparativos son exploratorios; no debe llamarse a esa prueba una evaluación nueva e independiente de todas las decisiones de diseño.

## 10. Configuración del entrenamiento, explicada paso a paso

### 10.1 Inicialización y semillas

Antes de aprender, los pesos se generan con distribución uniforme entre -0,5 y 0,5. Los diez sesgos comienzan en cero. Dar pesos iniciales diferentes permite que las neuronas empiecen a construir combinaciones distintas.

Una semilla es el número que inicia un generador pseudoaleatorio. Permite repetir una secuencia de elecciones. Se usan tres semillas independientes:

| Semilla | Valor | Función |
|---|---:|---|
| Datos | 2718 | Generación, aceptación de ejemplos y mezcla final de filas |
| Pesos | 31415 | Inicialización de las conexiones del modelo seleccionado |
| Orden | 42 | Barajado del entrenamiento en cada época |

La semilla no es una puntuación de calidad. Cambiarla puede cambiar el resultado, pero elegirla por su acierto en prueba introduciría una selección favorable a esa prueba. El modelo seleccionado conserva la semilla 31415; no fue reemplazado por la mejor de las diez inicializaciones posteriores.

### 10.2 Función de pérdida: entropía cruzada binaria

La pérdida mide cuánto difieren las activaciones de las etiquetas objetivo. Para una salida, con objetivo t y activación p:

```text
error = -[t*ln(p) + (1-t)*ln(1-p)]
```

Si el objetivo es 1, una activación 0,9 produce un error aproximado de 0,1053; una activación 0,1 produce 2,3026. Equivocarse con una activación muy extrema recibe una penalización considerable.

En cada ejemplo se suman los errores de las cuatro salidas. Para informar la pérdida de una partición se promedian esas sumas entre sus ejemplos. No se divide además entre cuatro: una implementación que lo hiciera reportaría números distintos aun con las mismas predicciones.

Una pérdida menor indica mejor ajuste a las etiquetas del experimento. No es un porcentaje de error ni una medida de salud o aptitud. La coincidencia binaria puede empatar y la pérdida diferir, porque esta última también considera los valores de las activaciones.

### 10.3 Retropropagación y gradiente

Un gradiente indica cómo cambiaría el error al modificar ligeramente un parámetro. La retropropagación aplica la regla de la cadena para calcularlo desde las salidas hacia las capas anteriores.

Con sigmoide y entropía cruzada, el término de error de salida es p - t. Para la capa oculta se combina ese error con los pesos de salida y con la derivada de tanh, que es 1 - h². El código calcula estos términos antes de modificar las matrices, para que una actualización no altere indebidamente el cálculo de otra.

Se verifica matemáticamente comparando los gradientes calculados con pequeñas perturbaciones numéricas de los parámetros. Esta prueba comprueba el algoritmo, pero no valida el significado de las etiquetas.

### 10.4 Optimizador SGD y tamaño de lote

SGD significa descenso de gradiente estocástico. «Descenso» indica que se avanza en una dirección que busca reducir el error. «Estocástico» hace referencia al uso de ejemplos individuales en un orden barajado.

El tamaño de lote es 1: se actualizan los parámetros después de cada ejemplo de entrenamiento. No se espera a procesar los 140 para actualizar una sola vez. Tampoco se utilizan Adam, momentum o lotes mayores en esta implementación.

### 10.5 Tasa de aprendizaje: 0,03

La tasa de aprendizaje controla el tamaño del ajuste. Sin regularización, una actualización ilustrativa sería:

```text
peso_nuevo = peso_anterior - 0,03 * gradiente
```

Si el peso es 0,50 y su gradiente 0,20, se obtiene 0,494. Una tasa excesiva puede producir cambios inestables; una muy pequeña puede hacer el avance lento. Aquí se usa 0,03 constante, sin programación automática de reducción. No se realizó una búsqueda que demostrara que es la tasa óptima.

### 10.6 Regularización L2: 0,001

Regularizar consiste en añadir una preferencia por soluciones menos extremas. L2 penaliza el cuadrado de los pesos. En la actualización aplicada:

```text
peso_nuevo = peso_anterior - 0,03 * (gradiente + 0,001*peso_anterior)
```

El término adicional tiende a reducir la magnitud del peso, salvo que el error de los ejemplos justifique compensarlo. Por ejemplo, con peso 0,50 y gradiente 0,20, resulta 0,493985 al incluir L2.

L2 se aplica a las matrices W1 y W2, no a los sesgos. La pérdida reportada y usada para elegir la época es la entropía cruzada de validación sin sumar la penalización L2. La regularización puede ayudar a controlar el ajuste excesivo, pero no lo elimina ni compensa la ausencia de ejemplos reales.

### 10.7 Épocas, máximo y parada temprana

Una época es una pasada completa por los 140 ejemplos de entrenamiento. El máximo configurado es 300 épocas. En cada época se vuelve a barajar el orden con la secuencia reproducible de semilla 42.

Después de cada época se calcula la pérdida de validación. Si disminuye en más de 0,000001 respecto de la mejor guardada, se conserva una copia de todos los pesos y sesgos y se reinicia el contador de espera. Esa pequeña tolerancia evita considerar como mejora diferencias numéricas insignificantes.

La paciencia es 25: se detiene el entrenamiento después de 25 épocas consecutivas sin una mejora suficiente. En la ejecución seleccionada:

| Configuración o resultado | Valor |
|---|---:|
| Máximo permitido | 300 épocas |
| Mejor época encontrada | 84 |
| Épocas ejecutadas | 109 |
| Épocas posteriores sin mejora suficiente | 25 |
| Pesos finalmente guardados | Los de la época 84 |

Se realizaron 109 × 140 = 15.260 actualizaciones durante la ejecución. Al terminar se restauró el punto de control de la época 84; no se utilizaron los pesos de la época 109 para el modelo seleccionado. Hasta el punto restaurado se habían realizado 84 × 140 = 11.760 actualizaciones.

El archivo conserva los parámetros finales y el resumen de entrenamiento, pero no una curva completa por época. Por ello este informe no inventa una trayectoria de pérdida ni asegura que el error de entrenamiento aumentó o disminuyó en una época concreta no registrada.

## 11. Ejemplo numérico con el modelo guardado

El siguiente recorrido se calcula directamente a partir de una fila del CSV y de los pesos conservados. Es un ejemplo experimental, no un expediente personal ni una recomendación aplicada.

Fila experimental elegida: ID 171, partición de prueba. No se seleccionó por un resultado favorable.

| Entrada | Original | Normalizada |
|---|---:|---:|
| fisica | 66.5 | 0,665000 |
| desempeno | 39 | 0,390000 |
| academica | 8 | 0,080000 |
| gse_autoeficacia | 24 | 0,466667 |
| mini_extraversion | 4 | 0,000000 |
| mini_amabilidad | 11 | 0,437500 |
| mini_responsabilidad | 8 | 0,250000 |
| mini_neuroticismo | 18 | 0,875000 |
| mini_apertura | 5 | 0,062500 |

Para h1, los nueve pesos aprendidos son:

```text
[-0,083759; -0,205878; 0,513477; -5,383244; 0,354495; 0,135349; -0,205579; 0,184466; -0,209806]
Sesgo b1[0] = 1,921216
Suma z1 = -0,529764
h1 = tanh(z1) = -0,485201
```

Las seis activaciones ocultas calculadas son:

```text
[-0,485201; 0,559609; 0,427280; 0,432400; 0,989863; -0,277400]
```

| Salida | Suma antes de sigmoide | Activación | Objetivo |
|---|---:|---:|---:|
| preparacion_y_confianza | -0,584988 | 0,357786 | 0 |
| comunicacion_y_colaboracion | 5,351353 | 0,995281 | 1 |
| aprendizaje_y_autonomia | 6,979931 | 0,999070 | 1 |
| afrontamiento_y_metas | -2,194163 | 0,100276 | 1 |

Estado de la simulación: ABSTENCION. Texto devuelto: Resultado indeterminado: requiere revisión humana.

Observe la diferencia entre etiqueta objetivo y activación. La etiqueta procede de la regla generadora; la activación procede de los pesos de la red. Pueden diferir porque el modelo aproxima las reglas, sin reproducirlas exactamente en todos los casos.

## 12. Resultados de la ejecución seleccionada

Estas métricas corresponden exclusivamente al archivo con semilla 31415, mejor época 84, no al promedio de varias redes.

| Partición | Casos | Coincidencia completa | Pérdida | Abstenciones |
|---|---:|---:|---:|---:|
| entrenamiento | 140 | 129/140 = 92.14% | 0.253423 | 14 |
| validacion | 30 | 26/30 = 86.67% | 0.385394 | 3 |
| prueba | 30 | 20/30 = 66.67% | 0.589899 | 6 |

### 12.1 Coincidencia completa y coincidencia por salida

La coincidencia completa exige acertar las cuatro etiquetas del mismo caso al aplicar un umbral de 0,5. En prueba se acertaron simultáneamente en 20 de 30 casos: 66,67%. Si se falló una sola etiqueta, el caso ya no cuenta como coincidencia completa.

La coincidencia por salida cuenta cada recomendación por separado. Por eso sus porcentajes pueden ser mayores que la coincidencia completa. No deben promediarse y presentarse como si fueran el mismo indicador.

| Salida en prueba | Coincidencia | VP | VN | FP | FN | F1 |
|---|---:|---:|---:|---:|---:|---:|
| preparacion y confianza | 86.67% | 15 | 11 | 4 | 0 | 0.8824 |
| comunicacion y colaboracion | 96.67% | 14 | 15 | 0 | 1 | 0.9655 |
| aprendizaje y autonomia | 90.00% | 14 | 13 | 2 | 1 | 0.9032 |
| afrontamiento y metas | 93.33% | 13 | 15 | 0 | 2 | 0.9286 |

VP significa verdadero positivo: se activó una etiqueta que tenía objetivo 1. VN es verdadero negativo: se dejó en 0 una etiqueta que tenía objetivo 0. FP es falso positivo y FN es falso negativo. Aquí «verdadero» significa coincidencia con la etiqueta artificial del ejemplo, no certeza sobre necesidades humanas.

### 12.2 Qué significa F1

F1 combina precisión positiva y sensibilidad. La precisión positiva pregunta cuántas activaciones fueron correctas entre todas las predicciones positivas. La sensibilidad pregunta cuántos objetivos positivos se recuperaron. Una forma equivalente de calcular F1 es:

```text
F1 = 2*VP / (2*VP + FP + FN)
```

Para preparación y confianza, VP = 15, FP = 4 y FN = 0. Así, F1 = 30/34 = 0,8824. No cuenta los verdaderos negativos y no debe llamarse «88,24% de recomendaciones válidas».

### 12.3 Tamaño de prueba y alcance

Un caso cambia la coincidencia completa de prueba en aproximadamente 3,33 puntos porcentuales, porque solo hay 30 casos. El resultado es sensible al conjunto utilizado. Tampoco una buena coincidencia demuestra que la regla generadora sea adecuada fuera del laboratorio.

## 13. Cómo se interpreta una salida y cuándo se abstiene

Para las métricas anteriores se usa 0,5. Para convertir activaciones en textos de simulación se aplica una regla distinta:

| Activación | Lectura de esa salida |
|---|---|
| Menor o igual a 0,35 | Inactiva |
| Mayor o igual a 0,65 | Activa |
| Estrictamente entre 0,35 y 0,65 | Incierta |

Si cualquiera de las cuatro salidas es incierta, el sistema se abstiene globalmente y devuelve «Resultado indeterminado: requiere revisión humana». Esa respuesta sustituye las sugerencias parciales que pudieran haber superado 0,65. Los valores exactos 0,35 y 0,65 no pertenecen a la zona incierta.

Si no hay incertidumbre y ninguna salida se activa, devuelve seguimiento y oportunidades generales de desarrollo. Si varias se activan sin incertidumbre en las demás, muestra los textos correspondientes a todas ellas.

Ejemplos ilustrativos, no calculados para personas:

| Vector de activaciones | Resultado de la regla de lectura |
|---|---|
| [0,82; 0,14; 0,76; 0,09] | Activa y1 e y3 |
| [0,82; 0,50; 0,76; 0,09] | Abstención global por y2 incierta |
| [0,10; 0,20; 0,15; 0,30] | Seguimiento general |

En prueba hubo seis abstenciones de treinta casos, es decir 20%. Los otros 24 casos no tuvieron activaciones intermedias; eso no significa que los 24 fueran correctos. La abstención y la coincidencia completa se calculan por separado y no son porcentajes complementarios.

Los umbrales 0,35 y 0,65 son decisiones experimentales. No están calibrados con resultados humanos ni garantizan un nivel de seguridad o confianza. Una activación 0,80 no significa automáticamente «80% de probabilidad de necesitar apoyo».

## 14. Por qué se conserva una capa oculta de seis neuronas

La arquitectura de seis neuronas es una base compacta: tiene 88 parámetros y permite estudiar relaciones no lineales sin aumentar innecesariamente el tamaño. La elección es una decisión de diseño del prototipo, no el resultado de demostrar que seis es el número óptimo universal.

Se comparó con 9 → 6 → 4 → 4 usando el mismo CSV GSE/Mini-IPIP, diez semillas por arquitectura y el mismo protocolo. El criterio principal definido antes de interpretar resultados fue la menor pérdida media de validación.

| Medida media entre diez inicializaciones | 9 → 6 → 4 | 9 → 6 → 4 → 4 |
|---|---:|---:|
| Parámetros | 88 | 108 |
| Pérdida de validación | 0,4036 | 0,4830 |
| Coincidencia completa de prueba | 74,67% | 69,67% |

Este ensayo favoreció conservar la arquitectura actual bajo ese protocolo. No prueba que todas las redes con dos capas sean peores ni que no puedan mejorar con otro diseño debidamente evaluado. No se hizo una búsqueda de hiperparámetros específica para cada arquitectura.

El 74,67% es un promedio de diez inicializaciones de la arquitectura; el 66,67% corresponde al modelo individual guardado. No se debe reemplazar una cifra por la otra. Las diez semillas no multiplican el conjunto de datos ni crean diez muestras independientes de personas.

Las comparaciones anteriores con DASS-21 y CBI pertenecen a otro problema de entradas y etiquetas. Sus porcentajes no se utilizan como resultados de este modelo GSE/Mini-IPIP. La alternativa 9 → 8 → 4 → 4 no se ha evaluado con estos datos nuevos.

## 15. Parámetros aprendidos frente a hiperparámetros

Un parámetro se aprende durante el entrenamiento: un peso o un sesgo. Un hiperparámetro se fija para organizarlo: la cantidad de neuronas, la tasa o la paciencia. Un valor aprendido no equivale a una decisión profesional interpretada por el sistema.

| Configuración | Valor aplicado | Tipo o finalidad |
|---|---|---|
| Arquitectura | 9 → 6 → 4 | Hiperparámetro de estructura |
| Pesos y sesgos | 88 valores | Parámetros aprendidos |
| Activación oculta | tanh | Transformación no lineal |
| Activación de salida | Cuatro sigmoides | Salidas combinables |
| Normalización | Mínimos y máximos teóricos | Preprocesamiento fijo |
| Optimizador | SGD | Método de actualización |
| Lote | 1 ejemplo | Actualización por ejemplo |
| Tasa | 0,03 constante | Tamaño del paso |
| Regularización | L2 = 0,001 | Penalización de pesos, no sesgos |
| Pérdida | Entropía cruzada binaria | Suma de cuatro salidas, media por caso |
| Épocas máximas | 300 | Límite de entrenamiento |
| Paciencia | 25 | Parada sin mejora de validación |
| Mejora mínima | Más de 0,000001 | Tolerancia de selección |
| Mejor época | 84 | Resultado observado |
| Épocas ejecutadas | 109 | Resultado observado |
| Umbral para métricas | 0,5 | Binarización para evaluación |
| Umbrales para simulación | 0,35 y 0,65 | Lectura con abstención |

No se aplican dropout, normalización por lotes, momentum, ajuste automático de tasa, selección automática de variables o búsqueda automática de arquitectura. Son características del código inspeccionado; su ausencia no demuestra por sí sola una carencia o una ventaja.

## 16. Guardado, reproducibilidad y trazabilidad

El motor está escrito con la biblioteca estándar de Python. No utiliza TensorFlow, PyTorch ni un servicio externo para entrenar. Los pesos se guardan como números en JSON, con arquitectura, entradas, rangos, activaciones y metadatos de entrenamiento.

| Archivo | Contenido |
|---|---|
| modelo.json | Los 88 valores aprendidos, estructura y configuración |
| informe.json | Protocolo, reglas, métricas y resumen del entrenamiento |
| datos_sinteticos.csv | Los 200 datos y sus particiones originales |
| predicciones.csv | Etiquetas, activaciones y estado para auditar cada ejemplo |
| manifest.json | Huellas SHA-256 de los cuatro archivos anteriores |

SHA-256 produce una huella de los bytes de un archivo. Si cambia el archivo, normalmente cambia su huella. Permite detectar modificaciones respecto del manifiesto; no certifica la validez científica ni reemplaza una firma institucional.

Huellas verificadas de los artefactos principales:

```text
modelo.json
abb2bed7e4bcc7e232388bf671afbf5d2ba5bce309f14b79026d92a2d0bad252
```

```text
datos_sinteticos.csv
b092c954c6580180b517af7dfaaaf1dbc29a99d7428dcbb00fea420693be499d
```


Para repetir el entrenamiento se debe usar una carpeta nueva, conservando el entorno y los artefactos existentes:

```powershell
.venv\Scripts\python.exe scripts\entrenar_red_gse_miniipip.py --salida output\replica_gse_964
```

El comando anterior sí inicia un entrenamiento nuevo; no fue necesario ejecutarlo para elaborar este informe. Mantener semillas, código, orden de columnas, datos y entorno permite verificar la reproducción. No se deben eliminar ni sobrescribir los archivos del modelo seleccionado para hacer una prueba.

## 17. Estado real, verificaciones y límites

El modelo está entrenado para simulación offline. No está conectado a las rutas de instructores ni produce recomendaciones en sus expedientes. No se han habilitado cuestionarios oficiales GSE/Mini-IPIP mediante esta entrega y no se ha alterado la base SQLite para elaborar el informe.

Las pruebas técnicas existentes comprueban rangos, distribución, ausencia de solapamientos, gradientes numéricos, restauración de mejores pesos, archivos guardados y conservación de modelos previos. Estas comprobaciones aportan evidencia sobre el software. No evalúan la idoneidad psicológica de una recomendación ni la aceptación institucional.

El conjunto pequeño, sus reglas artificiales, el equilibrio construido y la falta de etiquetas profesionales independientes limitan la generalización. La revisión de los objetivos es necesaria para evitar que los rasgos de personalidad se conviertan en juicios no justificados sobre desempeño o necesidades de apoyo.

Para estudiar un uso posterior con personas harían falta objetivos acordados, datos autorizados y representativos, revisión de pertinencia de instrumentos, recomendaciones humanas de referencia, evaluación independiente, análisis de errores y sesgos, calibración y reglas de seguimiento. Es trabajo pendiente; no se presume resuelto por haber entrenado o seleccionado una arquitectura.

El alcance acordado sigue siendo orientación y referencia, sin diagnóstico ni decisiones automáticas de ascenso, sanción o aptitud operativa. Aprobar nombres de salidas no valida las reglas que relacionan las puntuaciones con esas salidas.

## 18. Glosario de consulta rápida

| Concepto | Explicación sencilla |
|---|---|
| Entrada o característica | Número que se entrega a la red |
| Etiqueta objetivo | Respuesta que se intenta aprender en un ejemplo |
| Neurona | Suma ponderada seguida de una transformación |
| Peso | Número aprendido que multiplica una señal |
| Sesgo | Número aprendido que desplaza una suma |
| Activación | Resultado de la transformación de una neurona |
| Capa oculta | Transformación intermedia entre entradas y salidas |
| Multietiqueta | Permite varias salidas activas a la vez |
| Pérdida | Medida numérica del desacuerdo con los objetivos |
| Gradiente | Indicación matemática de cómo cambiar un parámetro |
| Retropropagación | Cálculo del gradiente a través de las capas |
| Época | Una pasada por los ejemplos de entrenamiento |
| Sobreajuste | Ajustarse a particularidades del entrenamiento que no se mantienen fuera de él |
| Regularización | Preferencia añadida para controlar soluciones demasiado extremas |
| Validación | Datos usados para elegir cómo o cuándo conservar el modelo |
| Prueba | Datos usados para evaluar después de esa elección |
| Abstención | Decisión de no emitir sugerencias por incertidumbre definida |
| Calibración | Correspondencia comprobada entre puntuaciones y frecuencias observadas |

## 19. Fuentes y correspondencia con la implementación

Las cifras de esta versión se verifican contra archivos locales, no contra estimaciones de conversaciones previas. El conjunto de fuentes principales es:

- `sicose/red_gse_miniipip.py`: orden y rangos, normalización, generación, reglas y salidas.
- `sicose/red_experimental.py`: cálculo hacia adelante, SGD, regularización, pérdida, parada y abstención.
- `scripts/entrenar_red_gse_miniipip.py`: configuración efectiva de la ejecución, particiones y guardado.
- `output/modelo_gse_miniipip_200_20261017/modelo.json`, `informe.json` y `manifest.json`: valores de la ejecución seleccionada e integridad.
- `output/comparacion_gse_miniipip_9644_200_20261017/comparacion.json`: comparación actual de diez inicializaciones.
- [GSE, documentación de los autores](https://userpage.fu-berlin.de/~health/faq_gse.pdf): puntuación y ausencia de corte universal.
- [Mini-IPIP, clave española del IPIP](https://ipip.ori.org/Spanishmini-IPIPposneg.htm): dimensiones y corrección de ítems inversos.

Las explicaciones de pesos, activaciones y entrenamiento describen las operaciones del código inspeccionado. Las reglas didácticas son propias del experimento y no se atribuyen a los autores de los instrumentos.
