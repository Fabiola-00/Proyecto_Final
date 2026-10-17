"""Diagrama PNG y SVG de los artefactos GSE/Mini-IPIP, sin reentrenar."""
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

from graficar_red_sintetica import Lienzo, AZUL, PRIMARIO, NARANJA, COMPLEMENTO, TINTA, GRIS

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT/'output/modelo_gse_miniipip_200_20261017'


def main():
    m = json.loads((DIR/'modelo.json').read_text(encoding='utf-8'))
    r = json.loads((DIR/'informe.json').read_text(encoding='utf-8'))
    manifest = json.loads((DIR/'manifest.json').read_text(encoding='utf-8'))
    for nombre, huella in manifest['sha256'].items():
        assert hashlib.sha256((DIR/nombre).read_bytes()).hexdigest() == huella
    assert m['arquitectura'] == r['arquitectura'] == [9, 6, 4]
    assert m['formato'] == 'MLP_GSE_MINIIPIP_SINTETICO_V1'
    assert m['estado'] == 'ENTRENADO_SOLO_SINTETICO' and not m['uso_en_personas']
    assert m['entradas'] == ['fisica', 'desempeno', 'academica', 'gse_autoeficacia',
        'mini_extraversion', 'mini_amabilidad', 'mini_responsabilidad', 'mini_neuroticismo', 'mini_apertura']
    assert m['salidas'] == ['preparacion_y_confianza', 'comunicacion_y_colaboracion',
                           'aprendizaje_y_autonomia', 'afrontamiento_y_metas']
    assert m['entrenamiento'] == r['entrenamiento']
    assert len(m['pesos']['w1']) == 6 and all(len(f) == 9 for f in m['pesos']['w1'])
    assert len(m['pesos']['w2']) == 4 and all(len(f) == 6 for f in m['pesos']['w2'])
    conexiones = sum(len(f) for f in m['pesos']['w1']+m['pesos']['w2'])
    sesgos = len(m['pesos']['b1'])+len(m['pesos']['b2'])
    assert conexiones == 78 and sesgos == 10 and r['parametros'] == 88
    n = {k: v['n'] for k, v in r['evaluaciones'].items()}
    assert sum(n.values()) == r['registros_totales'] == 200
    t = r['entrenamiento']
    c = Lienzo(ancho=1800, alto=1660, escala=2)
    c.svg.find('{*}title').text = 'SICOSE: red neuronal GSE + Mini-IPIP, 9 entradas, 6 neuronas ocultas y 4 salidas'
    c.svg.find('{*}desc').text = (
        'Diagrama del modelo entrenado con 200 datos: tres notas institucionales, '
        'GSE global y cinco dimensiones Mini-IPIP. Capa oculta tanh y cuatro salidas sigmoidales independientes. '
        '88 parámetros; 140 casos de entrenamiento, 30 de validación y 30 de prueba. '
        f'Mejor época {t["epoca_elegida"]}. Sin validación ni uso en personas.')
    c.rect(72, 50, 48, 6, NARANJA)
    c.texto(136, 54, 'SICOSE  /  RED NEURONAL EXPERIMENTAL', 19, AZUL, True)
    c.texto(72, 110, 'Modelo entrenado · GSE + Mini-IPIP', 42, TINTA, True)
    c.texto(72, 163, '9 entradas  →  6 neuronas ocultas  →  4 recomendaciones combinables', 25, GRIS)
    c.linea(72, 199, 1728, 199)
    c.texto(72, 237, '01  Entradas', 26, AZUL, True)
    c.texto(855, 237, '02  Capa oculta', 26, TINTA, True, 'middle')
    c.texto(1190, 237, '03  Salidas', 26, PRIMARIO, True)
    c.texto(72, 275, 'Puntuaciones agregadas → rango [0, 1]', 19, GRIS)
    c.texto(855, 275, '6 neuronas · activación tanh', 19, GRIS, ancla='middle')
    c.texto(1190, 275, '4 neuronas · activación sigmoide', 19, GRIS)

    yi = [365, 418, 471, 578, 660, 712, 764, 816, 868]
    yh = [360+87*i for i in range(6)]
    yo = [390+140*i for i in range(4)]
    # Dos bloques visuales y un subgrupo explícito para las cinco escalas Mini-IPIP.
    c.rect(60, 302, 470, 196, '#F0F6FF', 12)
    c.rect(60, 302, 5, 196, AZUL, 2)
    c.rect(60, 514, 470, 378, '#FFF5EC', 12)
    c.rect(60, 514, 5, 378, NARANJA, 2)
    c.texto(86, 327, 'EVALUACIÓN INSTITUCIONAL', 18, AZUL, True)
    c.texto(507, 327, '3 notas', 16, GRIS, ancla='end')
    c.texto(86, 540, 'PRUEBAS PSICOMÉTRICAS', 18, '#925716', True)
    c.texto(507, 540, '6 entradas', 16, GRIS, ancla='end')
    for i, y in enumerate(yi):
        for h in yh:
            c.linea(520, y, 833, h, '#D2E0F1' if i < 3 else '#EED4BE', 1.1)
    for h in yh:
        for y in yo:
            c.linea(877, h, 1128, y, '#EBCDB4', 1.3)
    etiquetas = ['Físico · promedio', 'Desempeño · promedio', 'Académica · acumulado',
                 'GSE · Autoeficacia', 'Extraversión', 'Amabilidad', 'Responsabilidad',
                 'Neuroticismo', 'Apertura / intelecto']
    for i, (nombre, y, minimo, maximo) in enumerate(zip(etiquetas, yi, m['minimos'], m['maximos'])):
        c.texto(109 if i >= 4 else 86, y, nombre, 21, TINTA, i <= 3)
        c.texto(451, y, f'{minimo}–{maximo}', 18, GRIS, ancla='end')
        c.nodo(500, y, 20, AZUL if i < 3 else NARANJA, f'x{i+1}', 'white' if i < 3 else TINTA)
    c.linea(86, 609, 507, 609, '#EBCDB4')
    c.texto(109, 630, 'MINI-IPIP · CINCO DIMENSIONES', 15, '#925716', True)
    c.linea(88, yi[4]-8, 88, yi[8]+13, '#C67B22', 2)
    c.linea(88, yi[4]-8, 98, yi[4]-8, '#C67B22', 2)
    c.linea(88, yi[8]+13, 98, yi[8]+13, '#C67B22', 2)
    for i, y in enumerate(yh):
        c.nodo(855, y, 22, NARANJA, f'h{i+1}', TINTA)
    salidas = [
        ('Preparación y confianza', 'Metas físicas, hábitos y reconocimiento', 'de avances para fortalecer la confianza.'),
        ('Comunicación y colaboración', 'Coordinación, participación gradual', 'y retroalimentación individual.'),
        ('Aprendizaje y autonomía', 'Capacitación práctica, objetivos', 'de aprendizaje y seguimiento.'),
        ('Afrontamiento y metas', 'Orientación voluntaria para organizar', 'metas y explorar formas de afrontar retos.'),
    ]
    for i, ((titulo, detalle, detalle2), y) in enumerate(zip(salidas, yo)):
        c.nodo(1150, y, 22, PRIMARIO, f'y{i+1}')
        c.texto(1190, y-15, titulo, 23, TINTA, True)
        c.texto(1190, y+22, detalle, 19, GRIS)
        c.texto(1190, y+49, detalle2, 19, GRIS)
    c.texto(855, 869, 'h = tanh(W₁x + b₁)', 20, GRIS, ancla='middle')
    c.texto(1190, 909, 'y = σ(W₂h + b₂)', 20, GRIS)
    c.texto(72, 907, 'Normalización: (valor − mínimo) / (máximo − mínimo)', 20, AZUL, True)
    c.texto(72, 946, f'{conexiones} conexiones + {sesgos} sesgos = 88 parámetros entrenados', 23, AZUL, True)
    c.texto(72, 977, 'Cada línea representa un peso aprendido; el grosor y el color no representan su importancia.', 18, GRIS)
    c.linea(72, 1007, 1728, 1007)

    c.texto(72, 1044, 'Datos · 200 casos únicos', 24, TINTA, True)
    x, w = 72, 744
    for clave, color, texto in [('entrenamiento', AZUL, 'white'), ('validacion', NARANJA, TINTA), ('prueba', COMPLEMENTO, 'white')]:
        ancho = w*n[clave]/200
        c.rect(x, 1075, ancho, 42, color)
        c.texto(x+ancho/2, 1096, str(n[clave]), 22, texto, True, 'middle')
        x += ancho
    c.texto(72, 1147, '140 entrenamiento (70%)', 17, AZUL, True)
    c.texto(344, 1147, '30 validación (15%)', 17, GRIS)
    c.texto(599, 1147, '30 prueba (15%)', 17, COMPLEMENTO, True)
    c.texto(72, 1184, 'Etiquetas inventadas para ensayo; no son criterios profesionales.', 18, GRIS)
    c.texto(945, 1044, 'Entrenamiento reproducible', 24, TINTA, True)
    c.texto(945, 1089, f'SGD · tasa {str(t["tasa"]).replace(".", ",")} · L2 {str(t["l2"]).replace(".", ",")}', 21)
    c.texto(945, 1131, f'Máximo {t["epocas_maximas"]} épocas · paciencia {t["paciencia"]}', 21)
    c.texto(945, 1173, f'Detenido en {t["epocas_ejecutadas"]} · mejores pesos: época {t["epoca_elegida"]}', 21, AZUL, True)
    c.texto(945, 1206, 'Selección por pérdida de validación; prueba reservada.', 18, GRIS)
    c.linea(72, 1238, 1728, 1238)

    c.texto(72, 1277, 'Resultado en los 30 casos de prueba', 24, TINTA, True)
    coincidencia = r['evaluaciones']['prueba']['coincidencia_completa']
    aciertos = round(coincidencia*n['prueba'])
    abstenciones = r['evaluaciones']['prueba']['abstenciones']
    c.texto(72, 1322, f'{aciertos}/30  ·  {coincidencia:.2%}'.replace('.', ','), 31, AZUL, True)
    c.texto(390, 1322, 'Coincidencia simultánea de las cuatro etiquetas a umbral 0,5.', 22)
    c.texto(72, 1364, f'{abstenciones}/30 abstenciones al aplicar la regla de incertidumbre. Es una medida distinta.', 21, GRIS)
    c.linea(72, 1395, 1728, 1395)
    c.texto(72, 1434, 'Cómo se leen las salidas', 24, TINTA, True)
    c.texto(72, 1474, '≥ 0,65: activa  ·  ≤ 0,35: inactiva  ·  Si alguna está entre ambos valores: abstención global.', 21)
    c.texto(72, 1510, 'Pueden activarse varias. Todas inactivas: seguimiento general. Datos incompletos: sin salida.', 20, GRIS)
    c.rect(72, 1541, 1656, 64, '#FFF1E4', 8)
    c.texto(96, 1561, 'Solo simulación: sin validación ni uso en personas. Las activaciones no son probabilidades calibradas.', 20, TINTA, True)
    c.texto(96, 1587, 'No genera diagnósticos ni determina ascensos, sanciones o aptitud operativa.', 19, GRIS)
    c.texto(72, 1634, 'Fuente: modelo.json e informe.json · GSE + Mini-IPIP · 17/10/2026 · Esquema de arquitectura, sin pesos numéricos.', 16, GRIS)

    png = DIR/'diagrama_red_gse_miniipip.png'
    svg = DIR/'diagrama_red_gse_miniipip.svg'
    c.im.save(png, dpi=(192, 192))
    ET.indent(c.svg)
    ET.ElementTree(c.svg).write(svg, encoding='utf-8', xml_declaration=True)
    print(json.dumps(dict(png=str(png), svg=str(svg), dimensiones_png=list(c.im.size)), ensure_ascii=False))


if __name__ == '__main__':
    main()
