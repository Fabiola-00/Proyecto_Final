"""Informe breve de dos páginas desde los resultados verificados del experimento."""
import hashlib
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'output/comparacion_tlx_1564_15664_200_20261018'
DEST = ROOT/'output/pdf/informe_comparativo_redes_15_6_4_y_15_6_6_4.pdf'
AZUL, TINTA, GRIS = (colors.HexColor(v) for v in ('#0054B2', '#142942', '#526479'))
ANCHO = A4[0]-96


def main():
    for n, h in json.loads((BASE/'manifest.json').read_text(encoding='utf-8')).items():
        assert hashlib.sha256((BASE/n).read_bytes()).hexdigest() == h
    r = json.loads((BASE/'resultados.json').read_text(encoding='utf-8'))
    assert r['seleccion']['arquitectura_recomendada'] == '15-6-4'
    for nombre, fichero in (('Texto', 'segoeui.ttf'), ('Texto-Bold', 'segoeuib.ttf')):
        pdfmetrics.registerFont(TTFont(nombre, str(Path('C:/Windows/Fonts')/fichero)))
    pdfmetrics.registerFontFamily('Texto', normal='Texto', bold='Texto-Bold', italic='Texto', boldItalic='Texto-Bold')
    estilos = {
        'titulo': ParagraphStyle('titulo', fontName='Texto-Bold', fontSize=24, leading=29, textColor=TINTA, spaceAfter=10),
        'sub': ParagraphStyle('sub', fontName='Texto', fontSize=12, leading=17, textColor=AZUL, spaceAfter=16),
        'h': ParagraphStyle('h', fontName='Texto-Bold', fontSize=12, leading=17, textColor=AZUL, spaceBefore=13, spaceAfter=7),
        'p': ParagraphStyle('p', fontName='Texto', fontSize=10, leading=14.5, textColor=TINTA, spaceAfter=8),
        'small': ParagraphStyle('small', fontName='Texto', fontSize=8.5, leading=12, textColor=GRIS, spaceAfter=7),
        'cell': ParagraphStyle('cell', fontName='Texto', fontSize=9, leading=12.5, textColor=TINTA),
        'head': ParagraphStyle('head', fontName='Texto-Bold', fontSize=9, leading=12.5, textColor=colors.white),
    }
    def p(texto, estilo='p'):
        return Paragraph(texto, estilos[estilo])
    def cuadro(texto):
        t = Table([[p(texto)]], colWidths=[ANCHO])
        t.setStyle(TableStyle([('BACKGROUND', (0,0),(-1,-1), colors.HexColor('#EDF4FF')),
            ('BOX',(0,0),(-1,-1),.6,colors.HexColor('#C8DBF3')),
            ('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),
            ('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
        return t
    def pie(canvas, doc):
        canvas.saveState()
        w, h = A4
        canvas.setFont('Texto-Bold',8)
        canvas.setFillColor(AZUL)
        canvas.drawString(48,h-31,'SICOSE / INFORME COMPARATIVO DE REDES NEURONALES')
        canvas.setStrokeColor(colors.HexColor('#DCE5EF'))
        canvas.line(48,h-42,w-48,h-42)
        canvas.line(48,40,w-48,40)
        canvas.setFont('Texto',8)
        canvas.setFillColor(GRIS)
        canvas.drawString(48,26,'NASA-TLX + GSE + Mini-IPIP | 18/10/2026')
        canvas.drawRightString(w-48,26,f'{doc.page} / 2')
        canvas.restoreState()
    story = [p('Comparación de dos<br/>arquitecturas neuronales', 'titulo'),
        p('15 → 6 → 4 frente a 15 → 6 → 6 → 4', 'sub'),
        cuadro('<b>Recomendación:</b> conservar <b>15 → 6 → 4</b> como alternativa preferida de este experimento. Presentó menor error medio de validación y requiere menos parámetros. Su adopción en el sistema sigue pendiente.'),
        p('Qué se comparó', 'h'),
        p('Ambas redes reciben las mismas <b>15 entradas</b>: tres evaluaciones institucionales (Físico, Desempeño y Académica), GSE, cinco dimensiones Mini-IPIP y seis dimensiones NASA-TLX. Producen cuatro líneas de apoyo combinables, sin decisiones automáticas de aptitud, ascenso o sanción.'),
        p('La primera red tiene <b>una capa oculta de seis neuronas</b>; la segunda, <b>dos capas ocultas de seis</b>. Una neurona combina valores y aplica una función matemática. Los <b>parámetros</b> son los pesos y sesgos que se ajustan durante el aprendizaje.'),
        p('Cómo se hizo una comparación equivalente', 'h'),
        p('Se utilizaron <b>200 Datos</b> generados para experimentación: 140 de entrenamiento, 30 de validación y 30 de prueba. Se conservaron las filas y sus etiquetas. Cada arquitectura se entrenó con <b>diez semillas prefijadas</b>: diez inicializaciones distintas para observar cuánto cambia el resultado al comenzar con otros pesos.'),
        p('Resultados medios de las diez ejecuciones', 'h')]
    a, b = (r['resumen'][n] for n in ('15-6-4', '15-6-6-4'))
    def numero(x, dec=4): return f'{x:.{dec}f}'.replace('.', ',')
    filas = [('Indicador', '15 → 6 → 4', '15 → 6 → 6 → 4'),
        ('Parámetros', '124', '166'),
        ('Error de validación (BCE)', numero(a['validacion_bce']['media']), numero(b['validacion_bce']['media'])),
        ('Error de prueba (BCE)', numero(a['prueba_bce']['media']), numero(b['prueba_bce']['media'])),
        ('Coincidencia completa en prueba', numero(a['prueba_coincidencia']['media']*100,2)+' %', numero(b['prueba_coincidencia']['media']*100,2)+' %'),
        ('F1 macro en prueba', numero(a['prueba_f1_macro']['media']*100,2)+' %', numero(b['prueba_f1_macro']['media']*100,2)+' %'),
        ('Abstenciones por 30 casos', numero(a['prueba_abstenciones']['media'],1), numero(b['prueba_abstenciones']['media'],1))]
    t = Table([[p(v,'head' if i==0 else 'cell') for v in fila] for i,fila in enumerate(filas)], colWidths=[245, (ANCHO-245)/2, (ANCHO-245)/2])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),AZUL),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F4F7FB')]),
        ('LINEBELOW',(0,0),(-1,0),1,AZUL),('LINEBELOW',(0,-1),(-1,-1),.5,colors.HexColor('#DCE5EF')),
        ('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),8),
        ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
    story += [t, Spacer(1,9), p('En BCE, un valor menor es mejor. En coincidencia completa y F1, un valor mayor es mejor. Las cifras son promedios, no el resultado de un único modelo.', 'small'), PageBreak(),
        p('Cómo interpretar la elección', 'titulo'),
        p('Métricas, ventajas y límites del resultado', 'sub'),
        p('Qué significan las métricas', 'h'),
        p('<b>BCE o entropía cruzada binaria:</b> mide la diferencia entre las etiquetas esperadas y las activaciones de la red. Penaliza especialmente errores muy seguros. Aquí suma las cuatro salidas y promedia los casos; menor es mejor.'),
        p('<b>Coincidencia completa:</b> exige acertar las cuatro etiquetas de un caso simultáneamente, usando umbral 0,50. Por eso es más exigente que evaluar cada salida por separado.'),
        p('<b>F1 macro:</b> resume el equilibrio entre aciertos positivos, falsos positivos y positivos omitidos en cada salida, y después promedia las cuatro. No equivale al porcentaje de casos completamente acertados.'),
        p('<b>Abstención:</b> si alguna activación está entre 0,35 y 0,65, el resultado se considera indeterminado y requiere revisión humana. Abstenerse menos no demuestra mayor calidad; las activaciones tampoco son probabilidades calibradas.'),
        p('Por qué se prefiere la red 15 → 6 → 4', 'h'),
        p('<b>1. Menor error al seleccionar.</b> Su BCE media de validación fue 0,7621 frente a 0,9351. La validación permite elegir los pesos y comparar arquitecturas sin utilizar la prueba para esa decisión.'),
        p('<b>2. Mejor resultado medio en prueba.</b> Después de fijar la selección, obtuvo 65,00 % de coincidencia completa frente a 62,67 %, además de menor BCE y mayor F1 macro. La diferencia es descriptiva; no se ha demostrado superioridad estadística.'),
        p('<b>3. Menor complejidad.</b> Tiene 124 parámetros frente a 166: la segunda capa agrega 42 (+33,87 %). Más capas permiten representar relaciones más complejas, pero también pueden dificultar el aprendizaje o ajustarse demasiado a los datos disponibles. Aquí no aportaron una mejora media.'),
        p('Promedio y ejemplar seleccionado: no son lo mismo', 'h'),
        p('El ejemplar de 15 → 6 → 4 elegido por su menor error de validación corresponde a <b>semilla 401, época 196</b>. Logró <b>22 de 30 coincidencias completas</b> y <b>3 abstenciones</b> en prueba. Es el resultado de un modelo concreto; no sustituye el promedio de diez ejecuciones ni fue elegido por sus aciertos de prueba.'),
        cuadro('<b>Alcance de la conclusión:</b> se recomienda la red más simple <b>para este experimento</b>. Los Datos y sus etiquetas provienen de generación y reglas didácticas, no de evaluaciones reales. Diez semillas no son diez muestras independientes. Solo hay treinta casos de prueba; se requiere validación con evidencia adecuada antes de atribuir utilidad sobre personas.'),
        Spacer(1,10),p('Configuración y trazabilidad', 'h'),
        p('Misma configuración: normalización por rangos teóricos, tanh en capas ocultas y sigmoides en salidas; SGD, lote 1, tasa 0,03 y L2 0,001. Máximo 300 épocas y parada temprana tras 25 sin mejora de validación, restaurando los mejores pesos. La comparación conserva veinte modelos y no modifica el modelo operativo actual.', 'small'),
        p('Fuente: resultados.json, protocolo.json y selección por validación del experimento SICOSE del 18/10/2026. Se conservan reglas de etiquetas V1, particiones y huellas verificadas.', 'small')]
    DEST.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(DEST), pagesize=A4, leftMargin=48, rightMargin=48, topMargin=62, bottomMargin=56,
        title='Comparativo breve: 15-6-4 y 15-6-6-4', author='SICOSE', subject='Comparación experimental NASA-TLX, GSE y Mini-IPIP')
    doc.build(story, onFirstPage=pie, onLaterPages=pie)
    print(DEST)


if __name__ == '__main__':
    main()
