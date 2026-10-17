# Psicometría y red experimental — 2026-10-17

[Informe didáctico del modelo seleccionado 9→6→4](26_informe_modelo_964_gse_miniipip.md), con configuración y cálculos verificados desde los artefactos actuales; [PDF](../output/pdf/informe_modelo_964_gse_miniipip.pdf). No modifica pesos, datos ni habilitaciones.

## Nueva versión experimental: GSE + Mini-IPIP

### Comparación posterior con 9→6→4→4

[Informe y modelos](../output/comparacion_gse_miniipip_9644_200_20261017/README.md). Alternativa solicitada implementada como `RedGseMiniIpipDosCapas`, 108 parámetros, mismas nueve entradas/rangos/cuatro salidas. Comparador admite `--perfil gse-miniipip --alternativa 9-6-4-4`, valida manifiesto de origen, copia el mismo CSV y conserva repartos 140/30/30. No vuelve a generar datos o etiquetas.

Veinte entrenamientos, diez semillas por arquitectura, mismo SGD/L2/parada temprana. Control 31415 reproduce el archivo del modelo actual exactamente. La alternativa 31415 elige época 64 de 89, obtiene 20/30 coincidencias completas y seis abstenciones, igual que el resultado binario individual de la actual. Su pérdida de prueba es 0,8517 frente a 0,5899; no todas las métricas son equivalentes.

Criterio principal prefijado: menor pérdida media de validación, que favorece 9→6→4 (0,4036 vs 0,4830). Prueba media actual 74,67% ±4,50 pp y alternativa 69,67% ±5,97 pp; cinco victorias de la actual, una de la alternativa y cuatro empates en pares. Media entre semillas distinta del resultado individual guardado; ± es desviación muestral de inicializaciones, no intervalo poblacional. Prueba ya consultada, comparación exploratoria; no se optimiza por prueba ni se sustituye automáticamente la actual. Datos artificiales sin validez personal. Verificación: 25 pruebas aprobadas en 15,195 s (cuatro nuevas), incluidos gradientes de 108 parámetros, restauración de todas las matrices y preservación de originales.

### Entrenamiento de la versión base

El solicitante aprobó las cuatro salidas y pidió regenerar 200 datos y entrenar nuevamente. [Artefactos y protocolo reproducible](../output/modelo_gse_miniipip_200_20261017/README.md): nueve entradas (Físico, Desempeño, Académica, GSE global y cinco dimensiones Mini-IPIP), una capa oculta de seis neuronas, cuatro salidas independientes, 88 parámetros. GSE suma 10–40 y Mini-IPIP cinco sumas 4–20, normalizadas a 0–1 por rango completo. Se generan puntuaciones agregadas posibles, no reactivos ni respuestas oficiales.

Salidas aprobadas: preparación y confianza; comunicación y colaboración; aprendizaje y autonomía; afrontamiento y metas. El CSV incluye etiquetas derivadas de reglas didácticas explícitas en el informe, no baremos ni criterios profesionales. Estas reglas de simulación ponderan rasgos, pero no acreditan relaciones causales ni necesidades de acompañamiento; ningún rasgo aislado activa una salida. La revisión profesional de objetivos sigue pendiente antes de cualquier uso real.

Particiones fijas: 140/30/30, filas únicas, 16 combinaciones presentes por partición y mitad de positivos por salida. Esto no reproduce prevalencias ni correlaciones poblacionales. Semillas datos 2718/pesos 31415/orden 42; L2=0,001, tasa 0,03, máximo 300, paciencia 25. Entrenamiento detuvo en 109 y restauró 84 por pérdida de validación. Prueba: 20/30 coincidencias completas (66,67%) a umbral 0,5; seis abstenciones con intervalo 0,35–0,65. Activaciones no calibradas. No comparar directamente con DASS/CBI: cambian datos y etiquetas.

Código separado: `sicose/red_gse_miniipip.py`, `scripts/entrenar_red_gse_miniipip.py`. Se reutiliza el motor MLP por métodos de normalización/salidas específicos, manteniendo exacto el experimento anterior. Modelo previo, CSV, manifiesto y comparaciones se conservan. Ningún cambio de esquema, base, formularios oficiales, PDF, cierre o inferencia para personas.

Fuentes primarias para rangos: [GSE](https://userpage.fu-berlin.de/~health/faq_gse.pdf) y [Mini-IPIP español](https://ipip.ori.org/Spanishmini-IPIPposneg.htm). GSE no tiene punto de corte universal. La aprobación de estas salidas y de entrenamiento sintético no habilita instrumentos oficiales ni acredita validez institucional. Los apartados siguientes describen el circuito DASS/CBI y sus experimentos históricos, conservados como antecedente; su palabra «vigente» se interpreta dentro de esa entrega anterior.

## Alcance y estado

Decisiones confirmadas: ampliar Evaluaciones; Administrador/Jefe habilitan DASS-21 y CBI por separado y por Gestión. Una finalización propia por prueba/Gestión, con avances recuperables. **El Instructor solo recibe «Completada» al finalizar**, sin puntuaciones, subescalas, respuestas finales ni recomendaciones. Esta decisión sustituye la petición anterior de mostrarle sus subescalas. Administrador/Jefe pueden consultar resultados y respuestas finalizadas; los borradores no se les entregan.

Circuito implementado y probado con formularios **ficticios** en SQLite aislado. No se han incorporado reactivos oficiales, simulado una aprobación profesional ni habilitado instrumentos en la base local. Falta identificar profesional responsable, documentar revisión institucional/profesional y definir retención. La ausencia de cualquiera de estas evidencias bloquea la activación en servidor, además de deshabilitar el botón. El circuito no acredita validez en personal SBRAB.

La red está desarrollada y se entrena fuera de Flask con datos sintéticos, sin consultar SQLite. No hay un modelo validado/desplegado para personas. Las recomendaciones personales y las entradas psicométricas del cálculo/cierre anterior siguen pendientes: no se sustituyen instantáneas, notas, PDFs ni reglas históricas por resultados experimentales.

## Revisión de fuentes y versiones candidatas

Fuentes primarias consultadas el 2026-10-17; esta revisión documental no equivale a revisión profesional.

| Instrumento | Versión candidata y derechos | Algoritmo preparado | Límite pendiente |
|---|---|---|---|
| DASS-21 | Traducción española Daza et al. (2002), enlazada por UNSW. Los cuestionarios se pueden copiar; conservar texto y atribución, sin vender las escalas. | 21 respuestas enteras 0–3. Tres sumas de siete ítems, cada una 0–21; se guarda también el doble 0–42. No hay total conjunto, nota institucional ni categorías diagnósticas. | Revisión del formulario exacto, equivalencia local, administración confidencial y devolución profesional. |
| CBI | Traducción española de Molinero Ruiz, Basart Gómez-Quintero y Moncada Lluis (2013). El estudio describe el instrumento como dominio público; no confundir derechos del instrumento con derechos de todo el artículo. | 19 respuestas canónicas 0–4, transformadas a 0/25/50/75/100; personal 6 ítems, trabajo 7 y atención a personas 6. Invertir el ítem 13 global (último de trabajo). Medias separadas 0–100, conservando numerador/denominador. | Adecuación de «trabajo» y «clientes» al voluntariado boliviano y aplicación de la tercera escala; no cambiar palabras silenciosamente. |

Referencias y condiciones:

- [DASS, descarga oficial y condiciones](https://www2.psy.unsw.edu.au/dass/down.htm).
- [Daza: traducción española, referencia y puntuación](https://www2.psy.unsw.edu.au/dass/Spanish/Daza.htm).
- [DASS FAQ, especialmente 8, 9, 21 y 25](https://www2.psy.unsw.edu.au/DASS/DASSFAQ.htm): administración informática para grupo definido, resultados dirigidos al profesional/investigador, sin devolución computarizada al respondiente ni interpretación automática. El dominio público no elimina estas indicaciones específicas. Se ha aceptado que el Instructor solo vea el estado final.
- [CBI, formato y puntuación originales del NFA](https://nfa.dk/media/a4wheblj/cbi-scales.pdf).
- [Validación española de CBI, artículo original](https://www.sanidad.gob.es/biblioPublic/publicaciones/recursos_propios/resp/revista_cdrom/vol87/vol87_2/RS872C_165.pdf). Estudio en España; no acredita validación en rescatistas bolivianos.

Claves DASS, índices desde 1: depresión 3/5/10/13/16/17/21; ansiedad 2/4/7/9/15/19/20; estrés 1/6/8/11/12/14/18. Revisarlas contra el formulario elegido antes de aprobar. Se requieren todas las respuestas al finalizar; no se calcula con blancos ni se imputan ceros. CBI admite reglas publicadas para respuestas faltantes y escalas independientes, pero este circuito completo **no implementa omisiones/N/A**: la revisión debe confirmar aplicabilidad de los 19 ítems; de lo contrario se debe adaptar el circuito y volver a probar antes de habilitarlo. Guardar un borrador parcial sí está permitido.

## Expediente obligatorio antes de la habilitación oficial

Pendientes reales: profesional y referencia de acreditación; aprobación institucional; versión española exacta; pertinencia para población/edad/contexto; propósito voluntario y consentimiento informado; explicación de acceso de Jefe/Administrador a respuestas individuales; plazo concreto y fundamento de conservación; protocolo de devolución, protección y atención profesional. No usar para ascensos, sanciones ni aptitud operativa automática. El plazo no se inventa ni se aplica un borrado automático todavía; también deben contemplarse copias de respaldo y conservación legal/institucional que corresponda.

El despliegue puede cargar `instance/psicometria_revisionada.json` (privado, ignorado por Git), con claves `DASS21` y/o `CBI`. Cada entrada tiene `formulario` y `revision`. No se suministra un expediente aprobado de ejemplo ni una API de autoaprobación. Configurar un texto en este archivo **no constituye** revisión profesional: quien despliega debe conservar la evidencia externa firmada. No crear este archivo con datos reales durante ensayos.

`formulario`: `version` y `algoritmo` iguales a los candidatos en `psicometria_puntuacion.py`; `instrucciones`; `items` ordenados, cada uno con `texto` y `opciones` como lista de etiquetas en orden canónico ascendente de codificación. DASS conserva sus opciones originales 0–3. CBI usa opciones de menor a mayor frecuencia/intensidad 0–4, con etiquetas apropiadas por ítem; el ítem 13 se invierte únicamente al puntuar. Revisar también este orden de presentación; no mezclar traducciones. La disposición electrónica requiere aprobación profesional.

`revision`: `profesional`, `referencia_profesional`, `aprobacion_institucional`, `fecha`, `retencion`, `protocolo_confidencialidad`, `devolucion_instructor: "SOLO_ESTADO"` y `firma_formulario` (SHA-256 del JSON canónico generado por `modelo_anual.serializar(formulario)`, UTF-8). Para CBI agregar `aplicabilidad_19_items_cbi` con la justificación revisada. La huella vincula versión, algoritmo, instrucciones, textos y opciones. Cualquier cambio invalida la aprobación técnica y bloquea reanudar borradores con otra huella; no hay migración automática de respuestas entre versiones. El expediente se carga al iniciar Flask; requiere reiniciar la aplicación tras una revisión aprobada. Cada intento conserva copia del formulario revisado para interpretar respuestas históricas aunque cambie la configuración después.

## Flujo y autorización

1. Gestión activa/no retirada; persona activa e inscrita en el modelo anual. Administrador/Jefe habilitan cada prueba independientemente tras validación del expediente. Activaciones con revisión optimista e historial de actor/fecha; deshabilitar conserva todos los datos.
2. Instructor obtiene únicamente formulario aprobado y borrador propios, sin aceptar persona desde cliente. Guarda avances con revisión; dos pestañas no pueden sobrescribir la misma versión silenciosamente.
3. Finalización validada y puntuada en servidor, en transacción serializada. Unicidad persona/prueba/Gestión y triggers que impiden editar/borrar una finalización. Sin reintentos ni corrección administrativa de respuestas en este alcance. Cierre, retiro de Gestión, desactivación de prueba o inactivación de cuenta bloquean nuevas respuestas.
4. Instructor finalizado recibe solo estado. Administrador/Jefe consultan respuestas finales codificadas, versión, fecha y subescalas; nunca borradores. Consultas auditadas con identificadores mínimos, sin respuestas/puntuaciones en auditoría. Rutas privadas `no-store`; sesión/rol/CSRF en backend. Se mantiene el acceso histórico administrativo tras cierre/desactivación.

APIs nuevas:

- `GET /api/modelo-anual/gestiones/<pid>/psicometria`: activaciones y estados administrativos.
- `PATCH /api/modelo-anual/gestiones/<pid>/psicometria/<clave>`: `activa` y `revision`.
- `GET /api/psicometria/propia`: pruebas propias habilitadas y estados; sin números finales.
- `GET/PUT /api/modelo-anual/gestiones/<pid>/psicometria/<clave>/propia`: formulario/borrador propio y guardado (`revision`, `respuestas`).
- `POST /api/modelo-anual/gestiones/<pid>/psicometria/<clave>/finalizar`: finalización con esos mismos campos.
- `GET /api/modelo-anual/gestiones/<pid>/personas/<uid>/psicometria`: resultados finales para Administrador/Jefe.

SQLite v28 agrega activaciones, historial de activaciones e intentos psicométricos; no adopta los ejemplos aritméticos ni cambia su historial. Esos ejemplos conservan sus APIs y no cuentan como DASS/CBI. La habilitación psicométrica nueva es independiente del interruptor histórico genérico PSICOMETRICAS.

## Red neuronal: cinco grupos, nueve dimensiones

**Decisión confirmada tras comparar alternativas:** conservar el modelo original 9→6→4 de 200 registros como base para las recomendaciones del prototipo. Se fija el artefacto entrenado original (semilla 31415, época elegida 55, 88 parámetros) y sus huellas en [seleccion_modelo.json](../output/modelo_sintetico_200_20261017/seleccion_modelo.json). No se sustituye por otra semilla de la comparación. Las dos redes de dos capas se conservan solo como ensayos. Esta selección no equivale a validación profesional/institucional ni habilita recomendaciones sobre personas.

[Diagrama didáctico completo en PNG](../output/modelo_sintetico_200_20261017/diagrama_red_200.png) · [Versión vectorial SVG](../output/modelo_sintetico_200_20261017/diagrama_red_200.svg).

Entrada en orden fijo: Física promedio (0–100), Desempeño promedio (0–100), Académica (0–100), DASS depresión/ansiedad/estrés (cada una 0–42), CBI personal/trabajo/personas (cada una 0–100). Se normaliza cada valor por su máximo. Las psicométricas no se convierten en una nota institucional. No imputar datos ausentes ni confundir cero oficial inicial con evidencia de cumplimiento físico/desempeño.

**Perfil vigente adaptado a 200 registros:** MLP 9→6→4 (88 parámetros frente a 228 del perfil anterior 9→16→4), `tanh` y cuatro sigmoides independientes. Mantiene las nueve dimensiones y las cuatro salidas; reduce capacidad, sin eliminar subescalas. SGD con entropía cruzada, regularización L2=0,001 solo en pesos y tasa 0,03. Parada temprana con paciencia de 25 épocas, máximo 300; selecciona/restaura pesos exclusivamente por menor entropía cruzada de validación. La prueba no interviene en entrenamiento o selección. Estas medidas limitan capacidad y ayudan a controlar sobreajuste, sin garantizar generalización. Biblioteca estándar de Python, sin dependencias nuevas. Pesos JSON. No existe integración de inferencia con las rutas personales ni carga automática de estos pesos en Flask.

Las cuatro salidas didácticas son independientes y **combinables**; cubren las 16 combinaciones posibles:

| Salida propuesta | Texto sugerido para revisión humana |
|---|---|
| Apoyo físico | Proponer acompañamiento para preparación física. |
| Acompañamiento en Desempeño | Proponer acompañamiento y retroalimentación en el desempeño. |
| Apoyo formativo | Proponer un plan de formación y capacitación. |
| Revisión profesional | Solicitar revisión confidencial por un profesional, sin conclusión automática. |
| Ninguna activada | Mantener seguimiento y oportunidades generales de desarrollo; no significa aptitud acreditada. |
| Una o varias activaciones ambiguas | Abstenerse y solicitar revisión humana. |
| Datos faltantes/fuera de rango | No inferir; completar/revisar datos, sin rellenarlos con cero. |

Activaciones >=0,65 proponen una salida simulada; cualquier valor entre 0,35 y 0,65 provoca abstención. No son probabilidades calibradas ni niveles clínicos. Las combinaciones unen propuestas sin emitir «apto/no apto», «ascender/no ascender», diagnósticos o sanciones. Una decisión institucional distinta exige nuevo diseño y validación.

Cobertura completa, usando F=físico, D=Desempeño, A=formación y R=revisión profesional:

| Patrón F/D/A/R | Propuestas combinadas |
|---|---|
| 0/0/0/0 | Seguimiento general |
| 0/0/0/1 | R |
| 0/0/1/0 | A |
| 0/0/1/1 | A + R |
| 0/1/0/0 | D |
| 0/1/0/1 | D + R |
| 0/1/1/0 | D + A |
| 0/1/1/1 | D + A + R |
| 1/0/0/0 | F |
| 1/0/0/1 | F + R |
| 1/0/1/0 | F + A |
| 1/0/1/1 | F + A + R |
| 1/1/0/0 | F + D |
| 1/1/0/1 | F + D + R |
| 1/1/1/0 | F + D + A |
| 1/1/1/1 | F + D + A + R |

Esta tabla es una propuesta de vocabulario para la simulación, pendiente de aprobación del propósito/etiquetado. No todas las filas representan situaciones clínicas o distribuciones reales. La abstención y la falta de datos tienen prioridad sobre las propuestas de la tabla.

## Datos sintéticos y entrenamiento reproducible

Ejecutar desde la raíz con una carpeta de salida nueva:

```powershell
.venv\Scripts\python.exe scripts\entrenar_red_sintetica.py --salida output\modelo_sintetico_200_nuevo
```

Genera **200 filas en total**, sin nombres, cuentas, respuestas reales ni lectura de base. Partición estratificada: **140 entrenamiento, 30 validación y 30 prueba**. Ocho combinaciones tienen 12 casos y ocho tienen 13; las 16 aparecen en cada partición. Ordenar patrones por pares complementarios equilibra cada salida binaria: 70/70 en entrenamiento y 15/15 en cada parte reservada. Semillas fijas 2718/31415/42. Solo entrenamiento actualiza pesos. Validación controla la parada y restauración de pesos; la prueba se evalúa una vez fijado el modelo. No hay filas idénticas entre particiones. Datos psicométricos en rejillas numéricas alcanzables por las sumas/medias; independencia simulada entre dimensiones, sin afirmar correlaciones, prevalencias o distribución real.

Ejecución vigente: `output/modelo_sintetico_200_20261017`. Se detuvo en la época 80 y restauró la 55. En prueba obtuvo coincidencia conjunta en 24/30 casos (80%) y siete abstenciones; son medidas distintas sobre los mismos 30 casos. Con una prueba tan pequeña, un caso cambia la coincidencia conjunta en 3,33 puntos porcentuales. No comparar directamente este porcentaje con el de la ejecución anterior: cambiaron el conjunto y su tamaño.

La ejecución previa de 2.048 registros queda preservada como evidencia histórica en `output/modelo_sintetico_20261017_v3`, separada del modelo actual. El generador anterior sigue disponible explícitamente como `datos_sinteticos(por_patron=128)` y reproduce su CSV; la llamada por defecto y el script actual usan solamente 200. No se mezclan ambas ejecuciones.

Las métricas de coincidencia usan umbral binario 0,5 y se informan por salida y para las cuatro etiquetas simultáneamente. La abstención usa por separado el intervalo 0,35–0,65; se cuenta sobre la misma partición. No interpretar la coincidencia binaria como precisión clínica, cobertura ni confianza calibrada de las sugerencias que superan la abstención.

Las etiquetas se generan con reglas **inventadas para ensayo**: apoyo si nota simulada <60, revisión si máximo de seis dimensiones psicométricas normalizadas >0,6. Estos valores NO son puntos de corte clínicos, institucionales ni recomendaciones profesionales. La red aprende a reproducir ese generador; su desempeño no valida las reglas. No puede generar etiquetas profesionales desconocidas a partir de datos sintéticos. No usar el equilibrio artificial de clases como prevalencia real.

Artefactos: `datos_sinteticos.csv`, `modelo.json` e `informe.json` con particiones, métricas, abstenciones y SHA-256 del CSV. Carpeta de entrenamiento versionada como evidencia reproducible. El conjunto actual se identifica en HISTORY. No sobrescribir ejecuciones previas; el script exige carpeta inexistente.

Antes de recomendaciones sobre personas: definir objetivos con responsables profesionales, obtener datos autorizados y etiquetas humanas independientes, validar diseño de entradas y propósito permitido (en particular DASS sin interpretación automatizada), evaluar sesgos/calibración/abstención, validar fuera de muestra y aprobar institucionalmente. El ensayo actual no cubre estos requisitos.

## Comparación solicitada con dos capas ocultas

[Informe completo 9→6→4 frente a 9→8→4→4](../output/comparacion_redes_200_20261017/README.md). Diez semillas prefijadas por arquitectura, mismo CSV y particiones 140/30/30, misma optimización/L2/parada temprana. Se verificó reproducción exacta del modelo base. En este protocolo, la pérdida media de validación favoreció 9→6→4 (0,4347 frente a 0,4883). Coincidencia completa media en prueba: 80,33% frente a 76,00%; desviación entre semillas 2,92 frente a 4,39 puntos porcentuales. La alternativa agrega 48 parámetros (136 frente a 88) y se abstiene menos, sin mejorar coincidencia global. No se sustituye automáticamente el modelo vigente.

Es una comparación exploratoria sobre los mismos 30 casos ya consultados, no una prueba independiente nueva. Las inicializaciones no multiplican el tamaño del conjunto. Se preservan pesos por semilla y métricas por partición; el criterio principal y la selección de épocas usan validación, no prueba. No hay evidencia de validez en personas.

Comparación posterior solicitada: [9→6→4 frente a 9→6→4→4](../output/comparacion_redes_9644_200_20261017/README.md), con las mismas diez semillas, datos, particiones y política de entrenamiento. La alternativa tiene 108 parámetros. Pérdida media de validación: 0,5724 frente a 0,4347 de la actual; coincidencia completa media de prueba 72,33% ±5,22 pp frente a 80,33% ±2,92 pp. La actual ganó en nueve pares y hubo un empate por coincidencia de prueba. Se mantiene 9→6→4. No se ajustaron hiperparámetros para favorecer un resultado ni se presenta la prueba reutilizada como evidencia independiente.


Verificación de esta entrega: 31 pruebas aprobadas en 25,482 s (siete nuevas), sintaxis de cuatro archivos Python correcta y huellas de artefactos actuales/anteriores comprobadas. Sin suite global ni validación profesional.
