"""Actualiza el gráfico del modelo vigente; no entrena ni abre la base de datos."""
import csv
import hashlib
import json
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from graficar_red_sintetica import Lienzo, AZUL, PRIMARIO, NARANJA, TINTA, GRIS
from sicose.recomendaciones import MODELO_PATH, MODELO_SHA, cargar_modelo, seleccionar_prioridad
from sicose.modelo_orientacion_tlx import ENTRADAS, SALIDAS

DESTINO=ROOT/'output/grafico_modelo_vigente_20261019'


def main():
    contenido=MODELO_PATH.read_bytes()
    assert hashlib.sha256(contenido).hexdigest()==MODELO_SHA
    modelo=cargar_modelo().exportar()
    base=MODELO_PATH.parents[1]
    protocolo=json.loads((base/'protocolo.json').read_text(encoding='utf-8'))
    assert hashlib.sha256((base/'datos.csv').read_bytes()).hexdigest()==protocolo['sha256_datos']
    with (base/'datos.csv').open(encoding='utf-8',newline='') as archivo:
        filas=list(csv.DictReader(archivo))
    assert len(filas)==200 and modelo['entradas']==list(ENTRADAS) and modelo['salidas']==list(SALIDAS)
    assert protocolo['particiones']==dict(entrenamiento=140,validacion=30,prueba=30)
    assert modelo['arquitectura']==[15,6,4] and modelo['parametros']==124
    entrenamiento=modelo['entrenamiento']
    assert modelo['semilla_pesos']==401 and entrenamiento['epoca_elegida']==196 and entrenamiento['epocas_ejecutadas']==221
    assert seleccionar_prioridad([.2,.3,.1,.15])['salida_prioritaria']==SALIDAS[1]
    conexiones=sum(len(f) for capa in modelo['pesos']['w'] for f in capa)
    sesgos=sum(len(capa) for capa in modelo['pesos']['b'])
    assert (conexiones,sesgos)==(114,10)

    c=Lienzo(ancho=2000,alto=1930,escala=2)
    c.svg.find('{*}title').text='SICOSE: modelo vigente 15 → 6 → 4 y selección de una recomendación'
    c.svg.find('{*}desc').text=('Tres entradas institucionales se distinguen de doce entradas de pruebas: '
        'GSE, cinco dimensiones Mini-IPIP y seis NASA-TLX. Se normalizan por rangos teóricos; '
        'seis neuronas tanh y cuatro sigmoides, con pesos ya entrenados. Fuera de la red se elige '
        'la mayor puntuación: una recomendación propuesta, pendiente de revisión humana. '
        '200 Datos: 140 entrenamiento, 30 validación, 30 prueba. 124 parámetros. '
        'Datos generados por computadora; sin validación personal.')
    c.rect(65,48,48,6,NARANJA)
    c.texto(130,50,'SICOSE / MODELO VIGENTE',20,AZUL,True)
    c.texto(65,108,'NASA-TLX + GSE + Mini-IPIP',44,TINTA,True)
    c.texto(65,160,'15 entradas → 6 neuronas ocultas → 4 puntuaciones → 1 recomendación',27,GRIS)
    c.rect(1510,42,425,65,'#EDF4FF',10)
    c.texto(1722,74,'MODELO ENTRENADO',23,AZUL,True,'middle')
    c.linea(65,202,1935,202)
    c.texto(65,247,'01  Entradas',27,AZUL,True)
    c.texto(925,247,'02  Capa oculta',27,TINTA,True,'middle')
    c.texto(1300,247,'03  Salidas de la red',27,PRIMARIO,True)
    c.texto(65,285,'Escalas originales → normalización [0, 1]',20,GRIS)
    c.texto(925,285,'6 neuronas · tanh',20,GRIS,ancla='middle')
    c.texto(1300,285,'4 sigmoides · puntuaciones entre 0 y 1',20,GRIS)

    c.rect(55,313,540,170,'#EDF4FF',12);c.rect(55,313,6,170,AZUL)
    c.texto(80,337,'A. EVALUACIÓN INSTITUCIONAL',19,AZUL,True)
    c.rect(55,502,540,805,'#FFF7EF',12);c.rect(55,502,6,805,NARANJA)
    c.texto(80,529,'B. PRUEBAS PSICOMÉTRICAS',19,'#925716',True)
    yi=[380,420,460,587,681,723,765,807,849,977,1027,1077,1127,1177,1227]
    yh=[400+150*i for i in range(6)];yo=[450,660,870,1080]
    for i,y in enumerate(yi):
        for h in yh:c.linea(589,y,901,h,'#D3E1F2' if i<3 else '#EBDACB',1)
    for h in yh:
        for y in yo:c.linea(949,h,1234,y,'#D8D8ED',1.2)
    nombres=['Físico · promedio','Desempeño · promedio','Académica · acumulado',
        'Autoeficacia general','Extraversión','Amabilidad','Responsabilidad','Neuroticismo','Apertura / intelecto',
        'Demanda mental','Demanda física','Demanda temporal','Rendimiento percibido','Esfuerzo','Frustración']
    c.texto(80,559,'GSE · 1 entrada',17,'#925716',True)
    c.linea(80,616,570,616,'#EAD5C0')
    c.texto(80,644,'MINI-IPIP · 5 dimensiones',17,'#925716',True)
    c.linea(80,883,570,883,'#EAD5C0')
    c.texto(80,914,'NASA-TLX · 6 dimensiones',17,'#925716',True)
    c.texto(80,943,'Carga percibida después del simulacro común',17,GRIS)
    for i,(nombre,y,mi,ma) in enumerate(zip(nombres,yi,modelo['minimos'],modelo['maximos'])):
        c.texto(80,y,nombre,21,TINTA,i<4)
        c.texto(506,y,f'{mi}–{ma}',18,GRIS,ancla='end')
        c.nodo(567,y,21,AZUL if i<3 else NARANJA if i<9 else '#C67B22',f'x{i+1}','white' if i<3 or i>=9 else TINTA)
    c.texto(80,1260,'Rendimiento TLX: 0 = bueno; 100 = malo.',17,'#925716',True)
    c.texto(80,1287,'Cada dimensión se mantiene por separado.',17,GRIS)
    for i,y in enumerate(yh):c.nodo(925,y,25,PRIMARIO,f'h{i+1}')
    salidas=[
        ('Preparación progresiva','y confianza','Prácticas paso a paso y metas','alcanzables para fortalecer la preparación.'),
        ('Organización de tareas','y manejo de la carga','Prioridades claras y distribución de tareas','para afrontar mejor las actividades.'),
        ('Comunicación y aprendizaje','acompañado','Aprender juntos, compartir dudas','y coordinar mejor en equipo.'),
        ('Afrontamiento y seguimiento','del bienestar','Escucha voluntaria y apoyos para afrontar','las exigencias cuidando el bienestar.')]
    for i,((t1,t2,d1,d2),y) in enumerate(zip(salidas,yo)):
        c.nodo(1258,y,24,PRIMARIO,f'y{i+1}')
        c.texto(1300,y-30,t1,24,TINTA,True);c.texto(1300,y+4,t2,24,TINTA,True)
        c.texto(1300,y+47,d1,20,GRIS);c.texto(1300,y+77,d2,20,GRIS)
    c.texto(925,1230,'h = tanh(W₁x + b₁)',22,GRIS,ancla='middle')
    c.texto(925,1267,'y = σ(W₂h + b₂)',22,GRIS,ancla='middle')
    c.rect(1230,1193,705,117,'#FFF0E3',10)
    c.texto(1252,1216,'04  Selección fuera de la red',23,'#925716',True)
    c.texto(1252,1250,'Se elige la puntuación mayor (argmax): una opción.',20,TINTA)
    c.texto(1252,1283,'Revisión humana y confirmación antes del reporte.',20,TINTA)

    c.linea(65,1345,1935,1345)
    c.texto(65,1383,'Cómo funciona',25,TINTA,True)
    c.texto(65,1428,'1. Poner las entradas en la misma escala',21,AZUL,True)
    c.texto(65,1460,'(valor − mínimo) / (máximo − mínimo)',20,GRIS)
    c.texto(735,1428,'2. Combinar la información',21,PRIMARIO,True)
    c.texto(735,1460,'Las líneas son conexiones ya entrenadas.',20,GRIS)
    c.texto(1390,1428,'3. Proponer un apoyo prioritario',21,'#925716',True)
    c.texto(1390,1460,'La elección final requiere revisión humana.',20,GRIS)
    c.texto(65,1506,'114 conexiones + 10 sesgos = 124 parámetros entrenados',25,AZUL,True)
    c.linea(65,1544,1935,1544)
    c.texto(65,1582,'Datos · 200 registros',25,TINTA,True)
    x=65
    for n,color in [(140,AZUL),(30,NARANJA),(30,'#226DC6')]:
        ancho=800*n/200;c.rect(x,1615,ancho,40,color)
        c.texto(x+ancho/2,1635,str(n),21,TINTA if color==NARANJA else 'white',True,'middle');x+=ancho
    c.texto(65,1682,'140 entrenamiento · 30 validación · 30 prueba',20,GRIS)
    c.texto(65,1720,'Generados por computadora para experimentación.',20,GRIS)
    c.texto(65,1754,'No son respuestas reales de Instructores.',20,GRIS)
    c.texto(1030,1582,'Configuración verificada',25,TINTA,True)
    c.texto(1030,1625,'SGD · tasa de aprendizaje 0,03 · L2 = 0,001',21,GRIS)
    c.texto(1030,1665,'Parada temprana: paciencia 25 · máximo 300 épocas',21,GRIS)
    c.texto(1030,1705,'Semilla 401 · época elegida 196 de 221 ejecutadas',21,GRIS)
    c.texto(1030,1745,'Empate exacto: prevalece el orden de las salidas 1 → 4.',20,GRIS)
    c.rect(65,1790,1870,77,'#FFF0E3',8)
    c.texto(87,1815,'Uso orientativo: no es diagnóstico ni evaluación de aptitud; no decide ascensos o sanciones.',21,TINTA,True)
    c.texto(87,1847,'Las puntuaciones no son porcentajes de certeza. La selección única no acredita validación sobre personas.',20,GRIS)
    c.texto(65,1900,'SICOSE · Actualizado el 19/10/2026 · Pesos vigentes preservados; este gráfico no reentrena el modelo.',18,GRIS)

    DESTINO.mkdir(exist_ok=True)
    png=DESTINO/'modelo_red_neuronal_actual.png';svg=DESTINO/'modelo_red_neuronal_actual.svg'
    c.im.save(png,dpi=(192,192));ET.indent(c.svg)
    ET.ElementTree(c.svg).write(svg,encoding='utf-8',xml_declaration=True)
    visible=' '.join(e.text or '' for e in c.svg.iter())
    assert 'sintétic' not in visible.lower() and 'sintetic' not in visible.lower()
    assert len(c.svg.findall('line'))==114+5  # Conexiones y separadores del gráfico.
    assert len(c.svg.findall('circle'))==25
    assert hashlib.sha256(MODELO_PATH.read_bytes()).hexdigest()==MODELO_SHA
    evidencia=dict(modelo_sha256=MODELO_SHA,arquitectura=modelo['arquitectura'],parametros=124,
        entradas=modelo['entradas'],salidas=modelo['salidas'],semilla=401,epoca=196,
        politica='ARGMAX_V1',datos=200,particiones=protocolo['particiones'],
        grafico_actualizado='2026-10-19',png_dimensiones=list(c.im.size))
    (DESTINO/'verificacion.json').write_text(json.dumps(evidencia,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(png=str(png),svg=str(svg),dimensiones=list(c.im.size)),ensure_ascii=False))


if __name__=='__main__':main()
