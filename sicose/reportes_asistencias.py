"""Matriz de asistencia paginada con carimbo institucional."""
from io import BytesIO
from datetime import date
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
from .reportes_cursos import carimbo_institucional


def generar_pdf_asistencias(datos):
    salida=BytesIO();ancho,_=landscape(A4);estilos=getSampleStyleSheet()
    estilo=ParagraphStyle('CeldaAsistencia',fontName='Helvetica',fontSize=8,leading=10)
    def texto(valor):return Paragraph(escape(str(valor if valor is not None else '-')),estilo)
    contenido=[];llamadas=datos['llamadas'];marcas={'ASISTE':'A','ATRASO':'T','PERMISO':'P','FALTA':'F'}
    for inicio in range(0,max(1,len(llamadas)),8):
        if inicio:contenido.append(PageBreak())
        bloque=llamadas[inicio:inicio+8]
        contenido.extend([Paragraph('REPORTE ASISTENCIA',estilos['Title']),texto(f"Responsable: {datos['responsable']} | Rango: {datos['desde']} a {datos['hasta']}"),
            texto('A: Asiste | T: Atraso | P: Permiso | F: Falta | -: Sin registro'),
            texto('Porcentaje: (Asiste + Atraso) / (Asiste + Atraso + Falta). Permiso excluido. Totales del rango completo.'),Spacer(1,10)])
        if not datos['personas']:
            contenido.append(texto('Sin asistencias registradas en el rango.'));continue
        encabezado=['#','Código','Instructor Voluntario']+[date.fromisoformat(c['fecha']).strftime('%d/%m/%y')+' / '+(c['actividad'] or 'Sin actividad') for c in bloque]+['Total A','Total T','Total P','Total F','%']
        filas=[[texto(v) for v in encabezado]]
        for numero,p in enumerate(datos['personas'],1):
            t=p['totales'];porcentaje='No disponible' if t['porcentaje'] is None else f"{t['porcentaje']:.2f}%"
            valores=[numero,p['codigo'] or 'Sin código',p['nombre']]+[marcas.get(e,'-') for e in p['estados'][inicio:inicio+8]]+[t[k] for k in ('ASISTE','ATRASO','PERMISO','FALTA')]+[porcentaje]
            filas.append([texto(v) for v in valores])
        disponible=ancho-60;fijos=[22,65,130];finales=[30,30,30,30,60]
        anchos=fijos+[(disponible-sum(fijos)-sum(finales))/len(bloque)]*len(bloque)+finales if bloque else fijos+finales
        tabla=Table(filas,colWidths=anchos,repeatRows=1,hAlign='LEFT')
        tabla.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E8E9FA')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F4F5F8')]),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.25,colors.HexColor('#D7DBE5')),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
        contenido.append(tabla)
    documento=SimpleDocTemplate(salida,pagesize=landscape(A4),leftMargin=30,rightMargin=30,topMargin=105,bottomMargin=40,title='Reporte Asistencia',author='SBRAB')
    documento.build(contenido,onFirstPage=carimbo_institucional,onLaterPages=carimbo_institucional);salida.seek(0);return salida
