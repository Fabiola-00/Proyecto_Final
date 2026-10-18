# Datos etiquetados NASA-TLX, GSE y Mini-IPIP

200 filas originales conservadas, 15 entradas y cuatro etiquetas binarias combinables. Origen visible: Datos. Son puntuaciones generadas por computadora, sin observaciones reales.

## Reglas V1

Todas las variables se normalizan por sus rangos teóricos. Cada salida exige una condición contextual y un índice >= 0,50. Pesos/cortes son hipótesis didácticas inventadas, no interpretaciones validadas de los instrumentos.

F=fisica,D=desempeno,AC=academica,G=GSE,E=extraversion,A=amabilidad,C=responsabilidad,N=neuroticismo,O=apertura,M=demanda mental,PF=demanda fisica,T=demanda temporal,R=rendimiento TLX (alto=malo),EF=esfuerzo,FR=frustracion.

### Preparación progresiva y confianza

- Condición: `F < 0.60 o PF >= 0.60`.
- Índice: `0.45*(1-F) + 0.20*(1-G) + 0.25*PF + 0.10*EF`.

### Organización de tareas y manejo de la carga

- Condición: `M >= 0.60 o T >= 0.60 o R >= 0.60`.
- Índice: `0.30*M + 0.30*T + 0.20*R + 0.10*EF + 0.10*(1-C)`.

### Comunicación y aprendizaje acompañado

- Condición: `D < 0.60 o AC < 0.60`.
- Índice: `0.30*(1-D) + 0.25*(1-AC) + 0.15*(1-G) + 0.10*(1-E) + 0.10*(1-A) + 0.10*(1-O)`.

### Afrontamiento y seguimiento del bienestar

- Condición: `FR >= 0.60 o EF >= 0.60`.
- Índice: `0.35*FR + 0.20*EF + 0.20*(1-G) + 0.15*N + 0.10*(1-C)`.

1: línea de apoyo propuesta por regla; 0: esa regla no propone la línea, no acredita bienestar ni capacidad. Cuatro ceros: seguimiento general. Varios unos: apoyos combinables.

Pesos, condiciones y umbral 0.50 inventados para ensayo, no baremos ni cortes de los instrumentos. Rasgos de personalidad no activan por sí solos una salida. No implican causalidad. Carga alta puede responder a la tarea o a su organización.

## Conservación y estado

No se regeneran datos ni se cambian particiones. 140 entrenamiento / 30 validación / 30 prueba. La regla se aplica igual a las tres; solo se resume la cobertura de entrenamiento/validación, manteniendo prueba sin explorar.

No hay entrenamiento, métricas nuevas ni integración en Flask o SQLite. El modelo vigente 9→6→4 sigue intacto. La aprobación de las cuatro salidas no acredita validez de estas reglas ni recomendaciones personales.

Reproducir: `python scripts/etiquetar_datos_tlx_gse_miniipip.py --salida output/nueva_carpeta_etiquetada`. Se exige carpeta nueva. Ver reglas.json e informe.json.
