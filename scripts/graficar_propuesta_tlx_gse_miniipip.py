"""Diagrama didáctico de arquitectura propuesta; no entrena ni cambia el modelo."""
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from graficar_red_sintetica import Lienzo, AZUL, PRIMARIO, NARANJA, TINTA, GRIS

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT/'output/datos_tlx_gse_miniipip_200_20261018'


def main():
    datos = json.loads((DIR/'diccionario.json').read_text(encoding='utf-8'))
    assert datos['registros'] == 200 and datos['entradas'] == 15
    assert not datos['entrenamiento_realizado']
    for nombre, huella in json.loads((DIR/'manifest.json').read_text()).items():
        assert hashlib.sha256((DIR/nombre).read_bytes()).hexdigest() == huella
    c = Lienzo(ancho=2000, alto=1810, escala=2)
    c.svg.find('{*}title').text = 'SICOSE: propuesta 15 → 6 → 4, NASA-TLX, GSE y Mini-IPIP'
    c.svg.find('{*}desc').text = ('Arquitectura propuesta, pendiente de entrenamiento. Tres entradas institucionales azules, '
        'seis de GSE y Mini-IPIP naranjas y seis de carga de trabajo NASA-TLX en color ocre. '
        'Seis neuronas ocultas y cuatro salidas propuestas pendientes de aprobación. Datos: 200 registros.')
    c.rect(65, 48, 48, 6, NARANJA)
    c.texto(130, 50, 'SICOSE / ARQUITECTURA PROPUESTA', 20, AZUL, True)
    c.texto(65, 108, 'NASA-TLX + GSE + Mini-IPIP', 44, TINTA, True)
    c.texto(65, 160, '15 entradas  →  6 neuronas ocultas  →  4 salidas propuestas', 28, GRIS)
    c.rect(1440, 65, 495, 68, '#FFF1E4', 10)
    c.texto(1687, 99, 'PENDIENTE DE ENTRENAMIENTO', 21, '#925716', True, 'middle')
    c.linea(65, 202, 1935, 202)
    c.texto(65, 247, '01  Entradas', 27, AZUL, True)
    c.texto(925, 247, '02  Capa oculta', 27, TINTA, True, 'middle')
    c.texto(1300, 247, '03  Recomendaciones propuestas', 27, PRIMARIO, True)
    c.texto(65, 285, 'Escalas originales → normalización [0, 1]', 20, GRIS)
    c.texto(925, 285, '6 neuronas · tanh propuesta', 20, GRIS, ancla='middle')
    c.texto(1300, 285, '4 salidas independientes · sigmoide propuesta', 20, GRIS)
    c.rect(55, 313, 540, 170, '#EDF4FF', 12)
    c.rect(55, 313, 6, 170, AZUL)
    c.texto(80, 337, 'A. EVALUACIÓN INSTITUCIONAL', 19, AZUL, True)
    c.rect(55, 502, 540, 780, '#FFF7EF', 12)
    c.rect(55, 502, 6, 780, NARANJA)
    c.texto(80, 529, 'B. PRUEBAS Y CARGA DE TRABAJO', 19, '#925716', True)
    yi = [380, 420, 460, 587, 681, 723, 765, 807, 849, 977, 1027, 1077, 1127, 1177, 1227]
    yh = [400+150*i for i in range(6)]
    yo = [450, 660, 870, 1080]
    for i, y in enumerate(yi):
        for h in yh:
            c.linea(595, y, 901, h, '#D3E1F2' if i < 3 else '#EBDACB', 1)
    for h in yh:
        for y in yo:
            c.linea(949, h, 1234, y, '#D8D8ED', 1.2)
    nombres = ['Físico · promedio', 'Desempeño · promedio', 'Académica · acumulado',
        'Autoeficacia general', 'Extraversión', 'Amabilidad', 'Responsabilidad', 'Neuroticismo', 'Apertura / intelecto',
        'Demanda mental', 'Demanda física', 'Demanda temporal', 'Rendimiento percibido', 'Esfuerzo', 'Frustración']
    c.texto(80, 559, 'GSE · 1 entrada', 17, '#925716', True)
    c.linea(80, 616, 570, 616, '#EAD5C0')
    c.texto(80, 644, 'MINI-IPIP · 5 dimensiones', 17, '#925716', True)
    c.linea(80, 883, 570, 883, '#EAD5C0')
    c.texto(80, 914, 'NASA-TLX · 6 dimensiones', 17, '#925716', True)
    c.texto(80, 943, 'Carga percibida después del simulacro común', 17, GRIS)
    for i, (nombre, y, v) in enumerate(zip(nombres, yi, datos['variables'])):
        c.texto(80, y, nombre, 21, TINTA, i < 4)
        c.texto(506, y, f'{v["minimo"]}–{v["maximo"]}', 18, GRIS, ancla='end')
        c.nodo(567, y, 21, AZUL if i < 3 else NARANJA if i < 9 else '#C67B22', f'x{i+1}', 'white' if i < 3 or i >= 9 else TINTA)
    c.texto(80, 1260, 'Rendimiento TLX: 0 = bueno; 100 = malo.', 17, '#925716', True)
    for i, y in enumerate(yh):
        c.nodo(925, y, 25, PRIMARIO, f'h{i+1}')
    salidas = [
        ('Preparación progresiva', 'y confianza', 'Prácticas graduales y apoyo según', 'capacidades y carga física percibida.'),
        ('Organización de tareas', 'y manejo de la carga', 'Priorización y distribución de tareas', 'según demanda mental y temporal.'),
        ('Comunicación y aprendizaje', 'acompañado', 'Coordinación, retroalimentación', 'y capacitación con acompañamiento.'),
        ('Afrontamiento y seguimiento', 'del bienestar', 'Orientación voluntaria para revisar', 'exigencias y estrategias de afrontamiento.'),
    ]
    for i, ((t1, t2, d1, d2), y) in enumerate(zip(salidas, yo)):
        c.nodo(1258, y, 24, PRIMARIO, f'y{i+1}')
        c.texto(1300, y-30, t1, 24, TINTA, True)
        c.texto(1300, y+4, t2, 24, TINTA, True)
        c.texto(1300, y+47, d1, 20, GRIS)
        c.texto(1300, y+77, d2, 20, GRIS)
    c.texto(925, 1218, 'h = tanh(W₁x + b₁)', 22, GRIS, ancla='middle')
    c.texto(1300, 1237, 'Nombres y criterios pendientes de aprobación.', 20, '#925716', True)
    c.linea(65, 1314, 1935, 1314)
    c.texto(65, 1350, 'Cómo funciona', 24, TINTA, True)
    c.texto(65, 1393, '1. Normalizar cada entrada', 22, AZUL, True)
    c.texto(65, 1426, '(valor − mínimo) / (máximo − mínimo)', 20, GRIS)
    c.texto(735, 1393, '2. Combinar las 15 entradas', 22, PRIMARIO, True)
    c.texto(735, 1426, 'Las líneas representan conexiones por aprender.', 20, GRIS)
    c.texto(1390, 1393, '3. Proponer líneas de apoyo', 22, PRIMARIO, True)
    c.texto(1390, 1426, 'Pueden coexistir varias; revisión humana.', 20, GRIS)
    c.texto(65, 1482, '114 conexiones + 10 sesgos = 124 parámetros por entrenar', 25, AZUL, True)
    c.linea(65, 1520, 1935, 1520)
    c.texto(65, 1558, 'Datos · 200 registros', 25, TINTA, True)
    x = 65
    for n, color in [(140, AZUL), (30, NARANJA), (30, '#226DC6')]:
        ancho = 800*n/200
        c.rect(x, 1590, ancho, 40, color)
        c.texto(x+ancho/2, 1610, str(n), 21, TINTA if n == 30 and color == NARANJA else 'white', True, 'middle')
        x += ancho
    c.texto(65, 1656, '140 entrenamiento · 30 validación · 30 prueba (partición preliminar)', 20, GRIS)
    c.texto(1030, 1558, 'Aplicación prevista', 25, TINTA, True)
    c.texto(1030, 1600, 'NASA-TLX: una vez por Gestión, después del simulacro común.', 21, GRIS)
    c.texto(1030, 1638, 'Datos generados para experimentación; no respuestas reales.', 21, GRIS)
    c.rect(65, 1693, 1870, 65, '#FFF1E4', 8)
    c.texto(87, 1714, 'Estado: datos preparados; salidas, etiquetado, entrenamiento y validación pendientes.', 21, TINTA, True)
    c.texto(87, 1743, 'Uso orientativo con revisión humana. Sin decisiones automáticas de ascenso, sanción o aptitud operativa.', 20, GRIS)
    c.texto(65, 1785, 'SICOSE · 18/10/2026 · Esquema propuesto sin pesos aprendidos. El modelo vigente 9 → 6 → 4 se conserva.', 17, GRIS)
    png, svg = DIR/'diagrama_propuesta_15_6_4.png', DIR/'diagrama_propuesta_15_6_4.svg'
    c.im.save(png, dpi=(192, 192))
    ET.indent(c.svg)
    ET.ElementTree(c.svg).write(svg, encoding='utf-8', xml_declaration=True)
    print(json.dumps(dict(png=str(png), svg=str(svg), dimensiones=list(c.im.size)), ensure_ascii=False))


if __name__ == '__main__':
    main()
