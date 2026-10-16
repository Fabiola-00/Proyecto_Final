"""Reporte operativo del catálogo, sin datos personales ni observaciones."""
from datetime import datetime, timezone, timedelta
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def generar_pdf_cursos(cursos, desde, hasta, tipo='', estado=''):
    salida=BytesIO()
    ancho,alto=landscape(A4)
    generado=datetime.now(timezone(timedelta(hours=-4))).strftime('%d/%m/%Y %H:%M')
    logo=Path(__file__).resolve().parent.parent/'frontend/static/images/sbrab-logo.png'
    estilos=getSampleStyleSheet()
    celda=ParagraphStyle('CeldaCurso',fontName='Helvetica',fontSize=9,leading=12)
    def texto(valor): return Paragraph(escape(str(valor or 'Sin registrar')),celda)
    documento=SimpleDocTemplate(salida,pagesize=landscape(A4),leftMargin=30,rightMargin=30,topMargin=105,bottomMargin=40,title='Reporte de Capacitaciones y Cursos',author='SBRAB')
    contenido=[Paragraph('Capacitaciones y Cursos',estilos['Title']),Paragraph(f'Fecha de inicio: {escape(desde)} a {escape(hasta)} (inclusive). Tipo: {escape(tipo or "Todos")}. Estado: {escape(estado or "Todos")}.',estilos['Normal']),Spacer(1,12)]
    if cursos:
        filas=[[texto(v) for v in ('Curso','Tipo','Entidad','Inicio','Fin','Estado')]]
        filas.extend([[texto(c.get(k)) for k in ('nombre','tipo','entidad','fecha_inicio','fecha_fin','estado')] for c in cursos])
        tabla=Table(filas,colWidths=[192,125,175,85,85,ancho-60-662],repeatRows=1,hAlign='LEFT')
        tabla.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EAF2FC')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F6F9FD')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,0),(-1,0),1,colors.HexColor('#0500B2'))]))
        contenido.append(tabla)
    else: contenido.append(Paragraph('Sin cursos para los filtros seleccionados.',estilos['Normal']))
    contenido.extend([Spacer(1,12),Paragraph(f'Total de cursos: {len(cursos)}. Cursos sin fecha de inicio excluidos.',estilos['Normal'])])
    documento.build(contenido,onFirstPage=carimbo_institucional,onLaterPages=carimbo_institucional)
    salida.seek(0);return salida

def carimbo_institucional(canvas,documento):
    ancho,alto=landscape(A4)
    generado=datetime.now(timezone(timedelta(hours=-4))).strftime('%d/%m/%Y %H:%M')
    logo=Path(__file__).resolve().parent.parent/'frontend/static/images/sbrab-logo.png'
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#0500B2'));canvas.roundRect(28,alto-87,ancho-56,62,7,stroke=1,fill=0)
    canvas.drawImage(str(logo),38,alto-78,width=47,height=47,preserveAspectRatio=True,anchor='c',mask='auto')
    canvas.setFont('Helvetica-Bold',11);canvas.drawString(96,alto-46,'SBRAB - Servicio de Búsqueda y Rescate de la Armada Boliviana')
    canvas.setFont('Helvetica',9);canvas.drawString(96,alto-64,f'Generado: {generado} (hora de Bolivia)')
    canvas.setFont('Helvetica',8);canvas.drawString(30,23,'SICOSE - Reporte operativo')
    canvas.drawRightString(ancho-30,23,f'Página {documento.page}')
    canvas.restoreState()
