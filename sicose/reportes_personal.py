"""Listados PDF operativos sin datos de contacto ni observaciones privadas."""
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from .reportes_cursos import carimbo_institucional


def generar_listado(titulo, subtitulo, columnas, filas, anchos):
    salida=BytesIO()
    documento=SimpleDocTemplate(salida,pagesize=landscape(A4),leftMargin=30,rightMargin=30,topMargin=105,bottomMargin=40,title=titulo,author='SBRAB')
    estilos=getSampleStyleSheet()
    celda=ParagraphStyle('ListadoPersonal',fontName='Helvetica',fontSize=8,leading=11,wordWrap='CJK')
    def texto(v):
        return Paragraph(escape(str(v if v is not None and v!='' else 'Sin registrar')),celda)
    contenido=[Paragraph(escape(titulo),estilos['Title']),Paragraph(escape(subtitulo),estilos['Normal']),Spacer(1,12)]
    if filas:
        ancho=landscape(A4)[0]-60
        tabla=Table([[texto(v) for v in columnas]]+[[texto(v) for v in f] for f in filas],colWidths=[v*ancho/sum(anchos) for v in anchos],repeatRows=1)
        tabla.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EAF2FC')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F6F9FD')]),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
        contenido.append(tabla)
    else:
        contenido.append(Paragraph('Sin registros para los filtros seleccionados.',estilos['Normal']))
    contenido.extend([Spacer(1,12),Paragraph(f'Total de filas: {len(filas)}.',estilos['Normal'])])
    documento.build(contenido,onFirstPage=carimbo_institucional,onLaterPages=carimbo_institucional)
    salida.seek(0)
    return salida
