"""Empaqueta código y artefactos verificados para Colab; no entrena ni abre SQLite."""
import ast
import csv
import hashlib
import io
import json
from pathlib import Path
import textwrap

ROOT=Path(__file__).resolve().parents[1]
DESTINO=ROOT/'output/colab_modelo_15_6_4_20261019'
BASE=ROOT/'output/comparacion_tlx_1564_15664_200_20261018'
SHA_MODELO='a98b65067700a975bb1993fe9510235900c21e15009adec8a18f46bca05e1353'


def extraer(ruta,nombre):
    fuente=ruta.read_text(encoding='utf-8')
    nodo=next(n for n in ast.parse(fuente).body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name==nombre)
    return ast.get_source_segment(fuente,nodo)


def main():
    modelo_texto=(BASE/'15-6-4/modelo_ejemplar_validacion.json').read_bytes().decode('utf-8')
    modelo=json.loads(modelo_texto)
    datos=(BASE/'datos.csv').read_bytes().decode('utf-8')
    protocolo=json.loads((BASE/'protocolo.json').read_text(encoding='utf-8'))
    assert hashlib.sha256(modelo_texto.encode()).hexdigest()==SHA_MODELO
    assert hashlib.sha256(datos.encode()).hexdigest()==protocolo['sha256_datos']
    assert modelo['arquitectura']==[15,6,4] and modelo['semilla_pesos']==401
    referencias={}
    with (BASE/'predicciones.csv').open(encoding='utf-8',newline='') as archivo:
        for f in csv.DictReader(archivo):
            if f['arquitectura']=='15-6-4' and f['semilla']=='401':
                referencias[int(f['id'])]=[float(f['activacion_'+k]) for k in modelo['salidas']]
    assert len(referencias)==200
    clase=extraer(ROOT/'scripts/red_tlx_experimental.py','RedTlx')
    # Solo se ofrece la arquitectura vigente, sin modificar sus operaciones numéricas.
    clase=clase.replace("if tuple(ocultas) not in ((6,), (6, 6)):","if tuple(ocultas) != (6,):")
    clase=clase.replace("Arquitecturas admitidas: 15-6-4 y 15-6-6-4.","Este cuaderno utiliza la arquitectura 15-6-4.")
    seleccion=extraer(ROOT/'sicose/recomendaciones.py','seleccionar_prioridad')
    textos=ast.literal_eval(next(n.value for n in ast.parse((ROOT/'sicose/modelo_orientacion_tlx.py').read_text(encoding='utf-8')).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='TEXTOS' for t in n.targets)))
    celdas=[]
    def agregar(tipo,contenido):
        contenido=textwrap.dedent(contenido).strip()+'\n'
        celda=dict(cell_type=tipo,id=f'sicose-{len(celdas)+1:02}',metadata={},source=contenido.splitlines(keepends=True))
        if tipo=='code':celda.update(execution_count=None,outputs=[])
        celdas.append(celda)

    agregar('markdown','''
    # SICOSE · Modelo de Red Neuronal 15 → 6 → 4
    **Google Colab / Python 3 · 19/10/2026**

    Este cuaderno incluye el código, los pesos vigentes y los **200 Datos**. No necesita
    Flask, acceso a la base, Google Drive, GPU ni instalar paquetes. Ejecuta las celdas
    en orden (o **Ejecutar todo**) para cargar el modelo y generar una recomendación.

    El reentrenamiento está **desactivado inicialmente**. Puedes activarlo en su sección
    para reproducir el experimento, sin sustituir los pesos que se usan para los ejemplos.

    Los Datos son puntuaciones generadas por computadora y sus etiquetas proceden de
    reglas didácticas, no de respuestas o recomendaciones reales. Uso orientativo con
    revisión humana; sin diagnóstico ni decisiones automáticas de ascenso, sanción o
    aptitud operativa. Las puntuaciones de salida no son porcentajes de certeza.
    ''')
    agregar('markdown','''
    ## 1. Entradas: dos grupos claramente separados

    | Grupo | Entradas | Rango original |
    |---|---|---|
    | **Evaluación institucional** | Físico (promedio), Desempeño (promedio), Académica (acumulado) | 0–100 cada una |
    | **GSE** | Autoeficacia general | 10–40 |
    | **Mini-IPIP** | Extraversión, Amabilidad, Responsabilidad, Neuroticismo, Apertura / intelecto | 4–20 cada una |
    | **NASA-TLX** | Demanda mental, física, temporal, rendimiento percibido, esfuerzo, frustración | 0–100 cada una |

    NASA-TLX se refiere al simulacro común: en rendimiento **0 = bueno; 100 = malo**.
    No se invierte esta dimensión ni neuroticismo. Se normaliza cada entrada mediante
    `(valor − mínimo) / (máximo − mínimo)`. No se imputan faltantes como cero.

    Hay seis neuronas ocultas **tanh** y cuatro salidas **sigmoides**: 114 pesos y diez
    sesgos, **124 parámetros**. La selección **argmax** es un paso posterior a la red:
    elige una sola recomendación. No es una capa adicional ni una salida softmax.
    ''')
    agregar('code',r'''
    import csv, hashlib, io, json, math, random, sys
    from collections import Counter
    from copy import deepcopy
    from pathlib import Path
    print('Python:', sys.version.split()[0])
    ''')
    agregar('markdown','''
    ## 2. Pesos y Datos incluidos
    La siguiente celda contiene los artefactos completos, para que no debas subir
    archivos auxiliares. Las huellas permiten comprobar que no cambiaron.
    ''')
    agregar('code',f'MODELO_JSON = {modelo_texto!r}\nDATOS_CSV = {datos!r}\n'
        f'SHA_MODELO = {SHA_MODELO!r}\nSHA_DATOS = {protocolo["sha256_datos"]!r}\n'
        f'REFERENCIAS = {referencias!r}\n'
        'assert hashlib.sha256(MODELO_JSON.encode()).hexdigest() == SHA_MODELO\n'
        'assert hashlib.sha256(DATOS_CSV.encode()).hexdigest() == SHA_DATOS\n'
        'MODELO = json.loads(MODELO_JSON)\n'
        'ENTRADAS = MODELO["entradas"]\nSALIDAS = MODELO["salidas"]\nTITULOS = MODELO["titulos"]\n'
        'VARIABLES = [(k,k,lo,hi,"") for k,lo,hi in zip(ENTRADAS,MODELO["minimos"],MODELO["maximos"])]\n'
        f'TEXTOS = {textos!r}\n'
        'filas = [dict(id=int(f["id"]),origen=f["origen"],particion=f["particion"],entradas=[float(f[k]) for k in ENTRADAS],objetivos=[int(f[k]) for k in SALIDAS]) for f in csv.DictReader(io.StringIO(DATOS_CSV))]\n'
        'grupos = {p:[f for f in filas if f["particion"]==p] for p in ("entrenamiento","validacion","prueba")}\n'
        'assert len(filas)==200 and len({f["id"] for f in filas})==200\n'
        'assert {p:len(g) for p,g in grupos.items()}=={"entrenamiento":140,"validacion":30,"prueba":30}\n'
        'assert all(f["origen"]=="Datos" for f in filas)\n'
        'assert MODELO["arquitectura"]==[15,6,4] and MODELO["parametros"]==124\n'
        'print("Datos:",len(filas),"· Particiones:",{p:len(g) for p,g in grupos.items()})\n'
        'print("Modelo:", MODELO["arquitectura"],"· SHA-256 verificada")')
    agregar('markdown','''
    ## 3. Código del modelo
    Implementación numérica del proyecto: propagación, gradientes y entrenamiento
    SGD con regularización L2. Se usa Python estándar para conservar las operaciones
    originales, en lugar de cambiar de biblioteca o algoritmo.
    ''')
    agregar('code',clase)
    agregar('code',seleccion)
    agregar('markdown','''
    ## 4. Cargar los pesos vigentes y comprobar las 200 predicciones
    Cargar estos pesos **no entrena nuevamente**. Se contrastan las cuatro
    puntuaciones de cada registro con las predicciones guardadas del modelo elegido.
    ''')
    agregar('code',r'''
    red_vigente = RedTlx(ocultas=(6,), semilla=401)
    red_vigente.w = deepcopy(MODELO['pesos']['w'])
    red_vigente.b = deepcopy(MODELO['pesos']['b'])
    red_vigente.entrenamiento = deepcopy(MODELO['entrenamiento'])
    assert [len(w) for w in red_vigente.w]==[6,4]
    assert all(len(f)==15 for f in red_vigente.w[0]) and all(len(f)==6 for f in red_vigente.w[1])
    assert all(math.isfinite(v) for capa in red_vigente.w for fila in capa for v in fila)
    for f in filas:
        assert len(f['objetivos'])==4 and all(t in (0,1) for t in f['objetivos'])
        red_vigente.normalizar(f['entradas'])
    error_maximo = max(abs(y-ref) for f in filas for y,ref in zip(red_vigente.adelante(f['entradas'])[-1],REFERENCIAS[f['id']]))
    assert error_maximo <= 1e-12, 'Las predicciones no coinciden con la referencia.'
    print('200 predicciones verificadas. Diferencia máxima:', error_maximo)
    ''')
    agregar('markdown','''
    ## 5. Generar una recomendación
    Las cuatro opciones son: **Preparación progresiva y confianza**;
    **Organización de tareas y manejo de la carga**; **Comunicación y aprendizaje acompañado**;
    **Afrontamiento y seguimiento del bienestar**.

    Se elige siempre la mayor puntuación, sin umbrales ni resultados generales. Si hay
    empate exacto, se usa el orden de esta lista. Es una **Propuesta**: requiere revisión
    humana y confirmación en el sistema para incorporarla a un reporte. El cuaderno
    no crea aprobaciones ni recomendaciones en SICOSE.
    ''')
    agregar('code',r'''
    def recomendar(entradas, red=None):
        if not isinstance(entradas,dict) or set(entradas)!=set(ENTRADAS):
            raise ValueError('Incluye exactamente las quince entradas con sus nombres originales.')
        red = red_vigente if red is None else red
        valores = [entradas[k] for k in ENTRADAS]
        puntuaciones = red.adelante(valores)[-1]
        seleccion = seleccionar_prioridad(puntuaciones)
        return dict(estado='Propuesta', recomendacion=TITULOS[SALIDAS.index(seleccion['salida_prioritaria'])],
            activaciones=dict(zip(SALIDAS,puntuaciones)), **seleccion)

    # Ejemplo editable de puntuaciones agregadas. No representa a una persona real.
    ejemplo = {
        'fisica':82.5, 'desempeno':82.5, 'academica':40,
        'gse_autoeficacia':31,
        'mini_extraversion':14, 'mini_amabilidad':14, 'mini_responsabilidad':15,
        'mini_neuroticismo':19, 'mini_apertura':11,
        'tlx_demanda_mental':20, 'tlx_demanda_fisica':70, 'tlx_demanda_temporal':60,
        'tlx_rendimiento':70, 'tlx_esfuerzo':65, 'tlx_frustracion':30
    }
    resultado = recomendar(ejemplo)
    print('Recomendación (Salida del Modelo):',resultado['recomendacion'])
    print(resultado['sugerencias'][0])
    print('Estado:',resultado['estado'])
    print('\nCuatro puntuaciones (no porcentajes de certeza):')
    for k,v in resultado['activaciones'].items(): print(' -',TITULOS[SALIDAS.index(k)],':',round(v,6))
    print('Diferencia entre las dos mayores:',resultado['margen_activacion'])
    ''')
    agregar('markdown','''
    ## 6. Evaluación: separar entrenamiento de selección prioritaria
    Las etiquetas originales permiten varias líneas simultáneas. Por ello, la BCE
    (pérdida de entrenamiento) y la coincidencia de cuatro etiquetas a corte 0,50
    **no son una medida de acierto de la recomendación única por argmax**.
    Se informa por separado cuántas veces se elige cada opción, sin llamarlo exactitud.
    La partición de prueba ya fue consultada en el experimento original; no es nueva
    evidencia independiente. Faltan recomendaciones de referencia de revisores humanos.
    ''')
    agregar('code',r'''
    for p,grupo in grupos.items():
        ps=[red_vigente.adelante(f['entradas'])[-1] for f in grupo]
        aciertos=sum(all(int(y>=.5)==t for y,t in zip(ys,f['objetivos'])) for ys,f in zip(ps,grupo))
        print(p,':',len(grupo),'Datos · BCE:',round(red_vigente.perdida(grupo),6),
              '· Coincidencia original de cuatro etiquetas:',str(aciertos)+'/'+str(len(grupo)))
    conteo=Counter(seleccionar_prioridad(red_vigente.adelante(f['entradas'])[-1])['salida_prioritaria'] for f in filas)
    print('\nDistribución de las 200 recomendaciones (no exactitud):')
    for k,titulo in zip(SALIDAS,TITULOS): print(' -',titulo,':',conteo[k])
    ''')
    agregar('markdown','''
    ## 7. Reproducir el entrenamiento (opcional)
    Cambia `REENTRENAR = False` a `True` y ejecuta esta celda. Se inicializa otro modelo
    con semilla 401, SGD lote 1, orden 42, tasa 0,03, L2 0,001 solo en pesos,
    máximo 300 épocas, paciencia 25 y mejora mínima 1e-6. Se restauran los mejores
    pesos de validación. **Solo 140 Datos entrenan; 30 validan; la prueba no se usa
    para entrenar ni elegir pesos.** No se selecciona otra semilla mirando la prueba.

    Referencia: época elegida 196 de 221 ejecutadas. Diferencias numéricas pequeñas
    entre plataformas pueden afectar la reproducción; se muestra la diferencia real.
    `red_vigente` y sus ejemplos siguen utilizando los pesos originales incluidos.
    ''')
    agregar('code',r'''
    REENTRENAR = False
    red_reentrenada = None
    if REENTRENAR:
        red_reentrenada = RedTlx(ocultas=(6,),semilla=401)
        red_reentrenada.entrenar(grupos['entrenamiento'],grupos['validacion'],
            epocas=300,paciencia=25,tasa=.03,l2=.001)
        print('Época elegida:',red_reentrenada.entrenamiento['epoca_elegida'])
        print('Épocas ejecutadas:',red_reentrenada.entrenamiento['epocas_ejecutadas'])
        diferencias=[abs(v-ref) for capa,capa_ref in zip(red_reentrenada.w,red_vigente.w) for fila,fila_ref in zip(capa,capa_ref) for v,ref in zip(fila,fila_ref)]
        diferencias += [abs(v-ref) for capa,capa_ref in zip(red_reentrenada.b,red_vigente.b) for v,ref in zip(capa,capa_ref)]
        print('Máxima diferencia de parámetros:',max(diferencias))
        print('Coinciden dentro de tolerancia 1e-9:',max(diferencias)<=1e-9)
    else:
        print('Reentrenamiento omitido. El modelo vigente continúa intacto.')
    ''')
    agregar('markdown','''
    ## 8. Exportar resultados del ejercicio
    Se crea una carpeta `resultados_colab_sicose` en el entorno del cuaderno con los
    pesos originales, Datos, ejemplo y política de selección. Si activaste el
    reentrenamiento, se guarda **otro archivo**, separado del modelo vigente.
    Descarga los archivos desde el explorador de Colab si deseas conservarlos.
    No se modifica el sistema ni se envían resultados a servicios externos.

    Fuente de instrucciones generales: [documentación oficial de Colab](https://research.google.com/colaboratory/faq.html).
    ''')
    agregar('code',r'''
    destino = Path('resultados_colab_sicose')
    destino.mkdir(exist_ok=True)
    (destino/'modelo_vigente.json').write_bytes(MODELO_JSON.encode())
    (destino/'Datos.csv').write_bytes(DATOS_CSV.encode())
    (destino/'recomendacion_ejemplo.json').write_text(json.dumps(resultado,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    politica=dict(criterio='ARGMAX_V1',arquitectura=[15,6,4],modelo_sha256=SHA_MODELO,
        orden_empates=SALIDAS,revision_humana=True,nota='Una propuesta relativa; sin probabilidades de certeza.')
    (destino/'politica_seleccion.json').write_text(json.dumps(politica,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if red_reentrenada is not None:
        nuevo=red_reentrenada.exportar()
        nuevo['semilla_pesos']=401
        nuevo['datos_sha256']=SHA_DATOS
        (destino/'modelo_reentrenado.json').write_text(json.dumps(nuevo,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    assert hashlib.sha256((destino/'modelo_vigente.json').read_bytes()).hexdigest()==SHA_MODELO
    print('Archivos del ejercicio:',*[str(p) for p in sorted(destino.iterdir())],sep='\n')
    ''')
    notebook=dict(nbformat=4,nbformat_minor=5,cells=celdas,metadata=dict(
        kernelspec=dict(display_name='Python 3',language='python',name='python3'),
        language_info=dict(name='python',version='3'),
        colab=dict(name='SICOSE_Modelo_15_6_4.ipynb',provenance=[])))
    DESTINO.mkdir(exist_ok=True)
    (DESTINO/'SICOSE_Modelo_15_6_4.ipynb').write_text(json.dumps(notebook,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    codigo='"""Modelo SICOSE autocontenido. Reentrenamiento opcional; sin acceso al sistema."""\n\n'
    codigo+='\n\n'.join(''.join(c['source']) for c in celdas if c['cell_type']=='code')
    compile(codigo,'SICOSE_Modelo_15_6_4.py','exec')
    (DESTINO/'SICOSE_Modelo_15_6_4.py').write_text(codigo,encoding='utf-8')
    print(json.dumps(dict(carpeta=str(DESTINO),celdas=len(celdas),codigo_celdas=sum(c['cell_type']=='code' for c in celdas)),ensure_ascii=False))


if __name__=='__main__':main()
