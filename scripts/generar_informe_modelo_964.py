"""Maqueta el informe didáctico Markdown como PDF; no modifica el modelo."""
from html import escape
from pathlib import Path
import re
import textwrap

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, Image, Preformatted, KeepTogether)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'docs/26_informe_modelo_964_gse_miniipip.md'
DEST = ROOT/'output/pdf/informe_modelo_964_gse_miniipip.pdf'
AZUL, NARANJA, TINTA = colors.HexColor('#0054B2'), colors.HexColor('#FA9A4B'), colors.HexColor('#142942')
WIDTH = A4[0]-96


def inline(text):
    text = escape(text)
    text = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<link href="\2" color="#0054B2">\1</link>', text)
    text = re.sub(r'`([^`]+)`', r'<font name="Mono" size="8.3">\1</font>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    return text


class Informe(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == 'Chapter':
            label = flowable.getPlainText()
            key = 'chapter-'+str(self.page)+'-'+str(len(label))
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(label, key, 0)
            self.notify('TOCEntry', (0, label, self.page, key))


def pie(canvas, doc):
    canvas.saveState()
    w,h = A4
    canvas.setFillColor(AZUL)
    canvas.setFont('Texto-Bold', 8)
    canvas.drawString(48,h-29,'SICOSE  /  INFORME DIDÁCTICO DEL MODELO 9 → 6 → 4')
    canvas.setStrokeColor(colors.HexColor('#DCE5EF'))
    canvas.line(48,h-38,w-48,h-38)
    canvas.line(48,37,w-48,37)
    canvas.setFillColor(colors.HexColor('#526479'))
    canvas.setFont('Texto',7.5)
    canvas.drawString(48,24,'GSE + Mini-IPIP | Experimento académico | 17/10/2026')
    canvas.drawRightString(w-48,24,str(doc.page))
    canvas.restoreState()


def main():
    fontdir = Path('C:/Windows/Fonts')
    for name, file in [('Texto','segoeui.ttf'),('Texto-Bold','segoeuib.ttf'),
                       ('Texto-Italic','segoeuii.ttf'),('Mono','consola.ttf')]:
        pdfmetrics.registerFont(TTFont(name,str(fontdir/file)))
    pdfmetrics.registerFontFamily('Texto',normal='Texto',bold='Texto-Bold',italic='Texto-Italic',boldItalic='Texto-Bold')
    s = getSampleStyleSheet()
    s.add(ParagraphStyle('BodyTextReport',fontName='Texto',fontSize=9.7,leading=14.5,
                         textColor=TINTA,spaceAfter=8,splitLongWords=True))
    s.add(ParagraphStyle('Chapter',fontName='Texto-Bold',fontSize=16,leading=21,
                         textColor=AZUL,spaceBefore=16,spaceAfter=11,keepWithNext=True))
    s.add(ParagraphStyle('Subchapter',fontName='Texto-Bold',fontSize=11.2,leading=16,
                         textColor=TINTA,spaceBefore=11,spaceAfter=7,keepWithNext=True))
    s.add(ParagraphStyle('Cell',fontName='Texto',fontSize=8.1,leading=11.4,textColor=TINTA,splitLongWords=True))
    s.add(ParagraphStyle('CellHead',parent=s['Cell'],fontName='Texto-Bold',textColor=colors.white))
    s.add(ParagraphStyle('CodeReport',fontName='Mono',fontSize=7.9,leading=11,
                         textColor=TINTA,backColor=colors.HexColor('#F0F6FF'),borderPadding=8,spaceAfter=12))
    s.add(ParagraphStyle('CoverTitle',fontName='Texto-Bold',fontSize=33,leading=41,textColor=TINTA,spaceAfter=20))
    s.add(ParagraphStyle('CoverSub',fontName='Texto',fontSize=17,leading=24,textColor=AZUL,spaceAfter=20))
    s.add(ParagraphStyle('Small',parent=s['BodyTextReport'],fontSize=8.5,leading=13))
    s.add(ParagraphStyle('TOCReport',fontName='Texto',fontSize=10,leading=16,spaceBefore=5,textColor=TINTA))
    s['TOCReport'].fontSize=9.2
    s['TOCReport'].leading=12
    s['TOCReport'].spaceBefore=1
    s['TOCReport'].spaceAfter=0
    story = [Spacer(1,65),Paragraph('SICOSE',s['CoverSub']),
             Paragraph('Informe didáctico<br/>del modelo neuronal<br/>seleccionado',s['CoverTitle']),
             Paragraph('9 → 6 → 4<br/>GSE + Mini-IPIP',s['CoverSub']),
             Spacer(1,12)]
    datos = [[Paragraph(inline(t),s['CellHead']),Paragraph(inline(v),s['Cell'])] for t,v in
        [('Datos','200 casos | 140 entrenamiento / 30 validación / 30 prueba'),
         ('Parámetros','78 pesos + 10 sesgos = 88'),
         ('Modelo seleccionado','Semilla 31415 | mejores pesos: época 84'),
         ('Resultado individual','20/30 coincidencias completas en prueba | 6 abstenciones'),
         ('Destinatarios','Estudiantes de primeros años de universidad')]]
    tabla=Table(datos,colWidths=[130,WIDTH-130])
    tabla.setStyle(TableStyle([('BACKGROUND',(0,0),(0,-1),AZUL),('BACKGROUND',(1,0),(1,-1),colors.HexColor('#F0F6FF')),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]))
    story += [tabla,Spacer(1,25),Paragraph('17 de octubre de 2026',s['BodyTextReport']),
        Paragraph('Explicación basada en el código y los artefactos guardados. Los datos fueron generados para ensayo. No acredita recomendaciones para personas reales.',s['Small']),PageBreak(),
        Paragraph('Guía de lectura',s['CoverSub']),
        Paragraph('Las primeras secciones explican qué recibe y produce la red. Las secciones 8 a 13 desarrollan los datos, el entrenamiento y la evaluación. El cierre reúne la selección de arquitectura, la trazabilidad y un glosario.',s['BodyTextReport'])]
    toc=TableOfContents()
    toc.levelStyles=[s['TOCReport']]
    toc.dotsMinLevel=0
    story += [toc,PageBreak()]
    lines=SOURCE.read_text(encoding='utf-8').splitlines()
    # El alcance inicial se conserva en el cuerpo, aunque la portada lo resume.
    i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line or line.startswith('# ') or line.startswith('## SICOSE'):
            i+=1
            continue
        if line.startswith('```'):
            block=[];i+=1
            while i<len(lines) and not lines[i].startswith('```'):
                raw=lines[i].replace('−','-').replace('–','-').replace('—','-')
                block.extend(textwrap.wrap(raw,width=99,subsequent_indent='  ',replace_whitespace=False,drop_whitespace=False) or [''])
                i+=1
            story.append(Preformatted('\n'.join(block),s['CodeReport']))
            i+=1
            continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                cells=[v.strip() for v in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?',v) for v in cells):rows.append(cells)
                i+=1
            count=len(rows[0])
            if count==2: widths=[WIDTH*.32,WIDTH*.68]
            elif count==3: widths=[WIDTH*.32,WIDTH*.30,WIDTH*.38]
            elif count==4: widths=[WIDTH*.19,WIDTH*.25,WIDTH*.21,WIDTH*.35]
            elif count==7: widths=[WIDTH*.30]+[WIDTH*.70/6]*6
            else: widths=[WIDTH/count]*count
            if rows[0][0]=='Posición':widths=[WIDTH*.09,WIDTH*.29,WIDTH*.17,WIDTH*.45]
            if rows[0][0]=='Salida' and count==4:widths=[WIDTH*.37]+[WIDTH*.63/3]*3
            data=[[Paragraph(inline(v),s['CellHead'] if row==0 else s['Cell']) for v in cells] for row,cells in enumerate(rows)]
            t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
            padding=3 if rows[0][0]=='Concepto' else 5.5
            t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),AZUL),
                ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#F0F6FF'),colors.white]),
                ('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),1,NARANJA),
                ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
                ('TOPPADDING',(0,0),(-1,-1),padding),('BOTTOMPADDING',(0,0),(-1,-1),padding)]))
            story += [t,Spacer(1,11)]
            continue
        if line.startswith('!['):
            path=SOURCE.parent/re.search(r'\]\(([^)]+)\)',line).group(1)
            story += [Image(str(path),width=WIDTH,height=WIDTH*3320/3600),Spacer(1,12)]
            i+=1
            continue
        if line.startswith('### '):
            story.append(Paragraph(inline(line[4:]),s['Subchapter']));i+=1;continue
        if line.startswith('## '):
            story.append(Paragraph(inline(line[3:]),s['Chapter']));i+=1;continue
        if line.startswith('- '):
            story.append(Paragraph('• '+inline(line[2:]),s['BodyTextReport']));i+=1;continue
        paragraph=[line];i+=1
        while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|','```','![','- ')):
            paragraph.append(lines[i].strip());i+=1
        story.append(Paragraph(inline(' '.join(paragraph)),s['BodyTextReport']))
    DEST.parent.mkdir(parents=True,exist_ok=True)
    doc=Informe(str(DEST),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=52,bottomMargin=52,
                title='SICOSE - Informe didáctico del modelo 9-6-4 GSE y Mini-IPIP',author='SICOSE - documentación técnica')
    doc.multiBuild(story,onFirstPage=pie,onLaterPages=pie)
    print(str(DEST))


if __name__=='__main__':
    main()
