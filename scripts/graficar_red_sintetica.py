"""Diagrama PNG/SVG desde los artefactos del modelo de 200 casos; no entrena."""
import json
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT/'output/modelo_sintetico_200_20261017'
AZUL = '#0054B2'
PRIMARIO = '#0500B2'
NARANJA = '#FA9A4B'
COMPLEMENTO = '#226DC6'
TINTA = '#142942'
GRIS = '#526479'
BORDE = '#DCE5EF'


class Lienzo:
    def __init__(self, ancho=1800, alto=1450, escala=2):
        self.s = escala
        self.im = Image.new('RGB', (ancho*escala, alto*escala), 'white')
        self.d = ImageDraw.Draw(self.im)
        self.svg = ET.Element('svg', xmlns='http://www.w3.org/2000/svg',
                              width=str(ancho), height=str(alto), viewBox=f'0 0 {ancho} {alto}')
        ET.SubElement(self.svg, 'title').text = 'SICOSE: red neuronal experimental 9–6–4, entrenada con 200 casos sintéticos'
        ET.SubElement(self.svg, 'desc').text = (
            'Cinco grupos conforman nueve entradas normalizadas, conectadas a seis neuronas tanh '
            'y cuatro salidas sigmoidales combinables. 78 pesos y 10 sesgos. '
            '140 casos de entrenamiento, 30 de validación y 30 de prueba. '
            'Sin uso sobre personas; las activaciones no son probabilidades calibradas.')
        ET.SubElement(self.svg, 'rect', width=str(ancho), height=str(alto), fill='white')
        self.fuentes = {}

    def texto(self, x, y, contenido, tam=20, color=TINTA, negrita=False, ancla='start'):
        tipo = 'segoeuib.ttf' if negrita else 'segoeui.ttf'
        llave = (tipo, tam)
        if llave not in self.fuentes:
            self.fuentes[llave] = ImageFont.truetype(str(Path('C:/Windows/Fonts')/tipo), tam*self.s)
        fuente = self.fuentes[llave]
        anchor = {'start': 'lm', 'middle': 'mm', 'end': 'rm'}[ancla]
        bbox = self.d.textbbox((x*self.s, y*self.s), contenido, font=fuente, anchor=anchor)
        if bbox[0] < 0 or bbox[1] < 0 or bbox[2] > self.im.width or bbox[3] > self.im.height:
            raise ValueError(f'Texto fuera de los límites: {contenido}')
        self.d.text((x*self.s, y*self.s), contenido, fill=color, font=fuente, anchor=anchor)
        e = ET.SubElement(self.svg, 'text', x=str(x), y=str(y), fill=color,
                          attrib={'font-family': 'Segoe UI, Arial, sans-serif', 'font-size': str(tam),
                                  'font-weight': '700' if negrita else '400',
                                  'text-anchor': ancla, 'dominant-baseline': 'central'})
        e.text = contenido

    def linea(self, x1, y1, x2, y2, color=BORDE, grosor=1):
        self.d.line((x1*self.s, y1*self.s, x2*self.s, y2*self.s), fill=color, width=max(1, round(grosor*self.s)))
        ET.SubElement(self.svg, 'line', x1=str(x1), y1=str(y1), x2=str(x2), y2=str(y2),
                      stroke=color, attrib={'stroke-width': str(grosor)})

    def rect(self, x, y, ancho, alto, color, radio=0):
        self.d.rounded_rectangle((x*self.s, y*self.s, (x+ancho)*self.s, (y+alto)*self.s),
                                 radius=radio*self.s, fill=color)
        ET.SubElement(self.svg, 'rect', x=str(x), y=str(y), width=str(ancho), height=str(alto),
                      rx=str(radio), fill=color)

    def nodo(self, x, y, radio, color, etiqueta, texto='white'):
        self.d.ellipse(((x-radio)*self.s, (y-radio)*self.s, (x+radio)*self.s, (y+radio)*self.s), fill=color)
        ET.SubElement(self.svg, 'circle', cx=str(x), cy=str(y), r=str(radio), fill=color)
        self.texto(x, y, etiqueta, 16, texto, True, 'middle')

    def guardar(self):
        png = DIR/'diagrama_red_200.png'
        svg = DIR/'diagrama_red_200.svg'
        self.im.save(png, dpi=(192, 192))
        ET.indent(self.svg)
        ET.ElementTree(self.svg).write(svg, encoding='utf-8', xml_declaration=True)
        print(json.dumps({'png': str(png), 'svg': str(svg), 'dimensiones_png': list(self.im.size)}, ensure_ascii=False))


def main():
    m = json.loads((DIR/'modelo.json').read_text(encoding='utf-8'))
    informe = json.loads((DIR/'informe.json').read_text(encoding='utf-8'))
    assert m['arquitectura'] == informe['arquitectura'] == [9, 6, 4]
    assert m['entradas'] == ['fisica', 'desempeno', 'academica', 'dass_depresion', 'dass_ansiedad',
                             'dass_estres', 'cbi_personal', 'cbi_trabajo', 'cbi_personas']
    assert m['salidas'] == ['apoyo_fisico', 'acompanamiento_desempeno', 'apoyo_formativo', 'revision_profesional']
    assert m['entrenamiento'] == informe['entrenamiento']
    assert m['estado'] == 'ENTRENADO_SOLO_SINTETICO' and not m['uso_en_personas']
    assert len(m['pesos']['w1']) == 6 and all(len(f) == 9 for f in m['pesos']['w1'])
    assert len(m['pesos']['w2']) == 4 and all(len(f) == 6 for f in m['pesos']['w2'])
    conexiones = sum(len(f) for f in m['pesos']['w1']+m['pesos']['w2'])
    sesgos = len(m['pesos']['b1'])+len(m['pesos']['b2'])
    assert conexiones+sesgos == informe['parametros'] == 88
    n = {k: v['n'] for k, v in informe['evaluaciones'].items()}
    assert sum(n.values()) == informe['registros_totales'] == 200
    entrenamiento = m['entrenamiento']
    c = Lienzo()
    c.rect(72, 50, 48, 6, NARANJA)
    c.texto(136, 54, 'SICOSE  /  MODELO EXPERIMENTAL', 19, AZUL, True)
    c.texto(72, 109, 'Red neuronal entrenada con 200 registros', 39, TINTA, True)
    c.texto(72, 157, '5 grupos de datos  →  9 entradas  →  6 neuronas ocultas  →  4 salidas combinables', 23, GRIS)
    c.linea(72, 194, 1728, 194)

    c.texto(72, 234, '01   Entradas (9)', 25, AZUL, True)
    c.texto(865, 234, '02   Capa oculta (6)', 25, TINTA, True, 'middle')
    c.texto(1180, 234, '03   Salidas (4)', 25, PRIMARIO, True)
    c.texto(72, 271, 'Normalización: cada valor / su máximo → [0, 1]', 19, GRIS)
    c.texto(865, 271, 'tanh · combina las nueve entradas', 19, GRIS, False, 'middle')
    c.texto(1180, 271, 'Sigmoide · activaciones entre 0 y 1', 19, GRIS)

    yi = [330+62*i for i in range(9)]
    yh = [350+87*i for i in range(6)]
    yo = [380+130*i for i in range(4)]
    for y in yi:
        for h in yh:
            c.linea(510, y, 843, h, '#D2E0F1', 1.15)
    for h in yh:
        for y in yo:
            c.linea(887, h, 1168, y, '#EBCDB4', 1.35)

    etiquetas = ['Física · promedio', 'Desempeño · promedio', 'Académica',
                 'Depresión', 'Ansiedad', 'Estrés', 'Personal', 'Trabajo', 'Atención a personas']
    for i, (etiqueta, y, maximo) in enumerate(zip(etiquetas, yi, m['maximos'])):
        c.texto(118 if i >= 3 else 72, y, etiqueta, 22, TINTA, i < 3)
        c.texto(446, y, f'0–{maximo}', 18, GRIS, False, 'end')
        c.nodo(490, y, 20, AZUL, f'x{i+1}')
    for titulo, primero, ultimo in [('DASS-21', 3, 5), ('CBI', 6, 8)]:
        c.texto(118, yi[primero]-28, titulo, 16, AZUL, True)
        c.linea(90, yi[primero]-8, 90, yi[ultimo]+12, '#9CB4CC', 2)
        c.linea(90, yi[primero]-8, 100, yi[primero]-8, '#9CB4CC', 2)
        c.linea(90, yi[ultimo]+12, 100, yi[ultimo]+12, '#9CB4CC', 2)
    for i, y in enumerate(yh):
        c.nodo(865, y, 22, NARANJA, f'h{i+1}', TINTA)
    salidas = [('Apoyo físico', 'Preparación y acondicionamiento'),
               ('Acompañamiento en Desempeño', 'Retroalimentación y desarrollo'),
               ('Apoyo formativo', 'Plan de cursos y capacitaciones'),
               ('Revisión profesional', 'Revisión confidencial, sin conclusión automática')]
    for i, ((titulo, detalle), y) in enumerate(zip(salidas, yo)):
        c.nodo(1190, y, 22, PRIMARIO, f'y{i+1}')
        c.texto(1234, y-9, titulo, 22, TINTA, True)
        c.texto(1234, y+24, detalle, 17, GRIS)
    c.texto(865, 851, 'h = tanh(W₁x + b₁)', 20, GRIS, False, 'middle')
    c.texto(1234, 839, 'y = σ(W₂h + b₂)', 20, GRIS)
    c.texto(1234, 869, 'Activaciones no calibradas; no son probabilidades.', 17, GRIS)
    c.texto(72, 902, f'{conexiones} conexiones + {sesgos} sesgos = {conexiones+sesgos} parámetros entrenados', 22, AZUL, True)
    c.texto(72, 934, 'Cada línea es una conexión entrenada. El grosor uniforme no representa la importancia de los pesos.', 18, GRIS)
    c.linea(72, 967, 1728, 967)

    c.texto(72, 1004, 'Distribución de los 200 datos sintéticos', 24, TINTA, True)
    x, w = 72, 744
    for clave, color, txtcolor in [('entrenamiento', AZUL, 'white'), ('validacion', NARANJA, TINTA), ('prueba', COMPLEMENTO, 'white')]:
        ancho = w*n[clave]/200
        c.rect(x, 1034, ancho, 42, color)
        c.texto(x+ancho/2, 1055, str(n[clave]), 22, txtcolor, True, 'middle')
        x += ancho
    c.texto(72, 1102, '140 entrenamiento (70%)', 17, AZUL, True)
    c.texto(344, 1102, '30 validación (15%)', 17, GRIS)
    c.texto(599, 1102, '30 prueba (15%)', 17, COMPLEMENTO, True)
    c.texto(72, 1136, 'Los 16 patrones de salida aparecen en cada partición.', 18, GRIS)

    c.texto(950, 1004, 'Entrenamiento del modelo', 24, TINTA, True)
    c.texto(950, 1043, f'SGD · tasa {str(entrenamiento["tasa"]).replace(".", ",")}', 20)
    c.texto(1360, 1043, f'L2 = {str(entrenamiento["l2"]).replace(".", ",")}', 20)
    c.texto(950, 1085, f'Paciencia: {entrenamiento["paciencia"]} épocas', 20)
    c.texto(1360, 1085, f'Máximo: {entrenamiento["epocas_maximas"]} épocas', 20)
    c.texto(950, 1127, f'Detenido: época {entrenamiento["epocas_ejecutadas"]}', 20)
    c.texto(1360, 1127, f'Pesos elegidos: época {entrenamiento["epoca_elegida"]}', 20, AZUL, True)
    c.texto(950, 1161, 'Selección por validación; prueba reservada.', 18, GRIS)

    c.linea(72, 1191, 1728, 1191)
    c.texto(72, 1226, 'Cómo se leen las salidas', 23, TINTA, True)
    c.texto(72, 1264, '≥ 0,65: activa  ·  ≤ 0,35: inactiva  ·  Cualquier valor intermedio: abstención y revisión humana.', 20)
    c.texto(72, 1298, 'Todas inactivas: seguimiento general. Entradas incompletas: no se genera una salida.', 19, GRIS)
    c.rect(72, 1334, 1656, 52, '#FFF1E4', 8)
    c.texto(96, 1360, 'Solo simulación: etiquetas sintéticas. Sin diagnóstico ni decisiones sobre personas.', 21, TINTA, True)
    c.texto(72, 1417, 'Fuente: pesos y metadatos de modelo.json e informe.json · Entrenamiento de 200 casos · 17/10/2026', 16, GRIS)
    c.guardar()


if __name__ == '__main__':
    main()
