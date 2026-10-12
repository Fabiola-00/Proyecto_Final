"""Consolidado administrativo por gestión sin observaciones privadas."""
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from .reportes_cursos import carimbo_institucional


def generar_pdf(datos):
    salida = BytesIO()
    estilo = ParagraphStyle('Evaluacion', fontName='Helvetica', fontSize=8, leading=11)
    def texto(valor):
        return Paragraph(escape(str(valor if valor is not None else 'Pendiente')), estilo)
    doc = SimpleDocTemplate(salida, pagesize=landscape(A4), leftMargin=30, rightMargin=30, topMargin=105, bottomMargin=40,
                            title='Evaluaciones por gestión', author='SBRAB')
    contenido = [Paragraph('Evaluaciones por gestión', getSampleStyleSheet()['Title']), texto(datos['periodo']['nombre']),
                 texto('Notas administrativas vigentes; no acredita publicación al Instructor ni aprobación institucional.'), Spacer(1, 12)]
    filas = [[texto(v) for v in ('Instructor / Código', 'Cuenta', 'Evaluación', 'Habilitación', 'Estado', 'Nota')]]
    for persona in datos['personas']:
        for e in persona['evaluaciones']:
            filas.append([texto(persona['nombre'] + ' / ' + (persona['codigo'] or 'Sin código')), texto(persona['estado']), texto(e['nombre']),
                          texto('Habilitada' if e['habilitada'] else 'Deshabilitada'), texto(e['estado']), texto(e['nota'])])
    if len(filas) > 1:
        tabla = Table(filas, colWidths=[220, 65, 180, 115, 115, 86.89], repeatRows=1)
        tabla.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E8E9FA')), ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                   ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F4F5F8')]),
                                   ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
        contenido.append(tabla)
    else:
        contenido.append(texto('Sin Instructores Voluntarios registrados.'))
    doc.build(contenido, onFirstPage=carimbo_institucional, onLaterPages=carimbo_institucional)
    salida.seek(0)
    return salida
