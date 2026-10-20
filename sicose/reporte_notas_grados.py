"""Listado administrativo por grado, exclusivamente con notas publicadas."""
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, KeepTogether

from .publicaciones_5b import proyeccion
from .management import GRADOS_INSTRUCTOR


def datos_listado(c, pid):
    p = c.execute('SELECT p.* FROM periodos p JOIN modelos_anuales m ON m.periodo_id=p.id WHERE p.id=? AND NOT EXISTS(SELECT 1 FROM bajas_gestion b WHERE b.periodo_id=p.id)', (pid,)).fetchone()
    if p is None:
        raise LookupError('Gestión del modelo anual no encontrada o retirada.')
    filas = []
    for fila in c.execute("""SELECT u.id,v.apellido_paterno,v.apellido_materno,v.nombres,v.grado
        FROM personas_modelo_anual a JOIN usuarios u ON u.id=a.voluntario_id
        JOIN roles r ON r.id=u.rol_id JOIN voluntarios v ON v.usuario_id=u.id
        WHERE a.periodo_id=? AND u.estado='ACTIVO' AND r.nombre='INSTRUCTOR_VOLUNTARIO'""", (pid,)).fetchall():
        persona = dict(fila)
        publicada = proyeccion(c, persona['id'], pid) or {}
        valores = [publicada.get('promedio_fisico'), (publicada.get('academica') or {}).get('valor'), (publicada.get('desempeno') or {}).get('valor')]
        notas = [Decimal(str(v)) if v is not None else None for v in valores]
        persona['notas'] = notas
        # Ordenar con precisión exacta; redondear únicamente para presentar.
        persona['final'] = sum((Fraction(n) for n in notas), Fraction()) / 3 if all(n is not None for n in notas) else None
        filas.append(persona)
    grados = list(reversed(GRADOS_INSTRUCTOR))
    def orden(f):
        return (grados.index(f['grado']) if f['grado'] in grados else len(grados),
                f['final'] is None, -f['final'] if f['final'] is not None else 0,
                *(str(f[k] or '').casefold() for k in ('apellido_paterno','apellido_materno','nombres')), f['id'])
    filas.sort(key=orden)
    return dict(periodo=dict(p), filas=filas, generado=datetime.now(timezone(timedelta(hours=-4))))


def generar_listado(datos):
    salida = BytesIO()
    azul, naranja = colors.HexColor('#0500B2'), colors.HexColor('#FA9A4B')
    ancho, alto = landscape(A4)
    disponible = ancho-72
    normal = ParagraphStyle('ListadoNotas',fontName='Helvetica',fontSize=8,leading=11,textColor=colors.HexColor('#24364D'))
    seccion = ParagraphStyle('GradoListado',parent=normal,fontName='Helvetica-Bold',fontSize=11,leading=15,textColor=azul,spaceBefore=12,spaceAfter=8,keepWithNext=True)
    titulo = ParagraphStyle('TituloListado',parent=seccion,fontSize=18,leading=22)
    def texto(v, estilo=normal):
        return Paragraph(escape(str(v if v is not None and v != '' else 'Sin registrar')),estilo)
    def nota(v):
        if v is None:
            return 'Sin resultado'
        if isinstance(v,Fraction):
            v = Decimal(v.numerator)/Decimal(v.denominator)
        return format(v.quantize(Decimal('.01'),rounding=ROUND_HALF_UP),'.2f')
    def carimbo(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(azul);canvas.roundRect(32,alto-94,ancho-64,66,6,stroke=1,fill=0)
        logo=Path(__file__).resolve().parent.parent/'frontend/static/images/sbrab-logo.png'
        canvas.drawImage(str(logo),42,alto-84,width=46,height=46,preserveAspectRatio=True,mask='auto')
        canvas.setFillColor(azul);canvas.setFont('Helvetica-Bold',12);canvas.drawString(100,alto-47,'ARMADA BOLIVIANA - SBRAB')
        canvas.setFont('Helvetica',8);canvas.drawString(100,alto-61,'Servicio de Búsqueda y Rescate de la Armada Boliviana')
        canvas.setFillColor(colors.HexColor('#24364D'));canvas.drawString(100,alto-76,'SICOSE | Listado de notas publicadas por grado')
        canvas.setStrokeColor(naranja);canvas.line(36,40,ancho-36,40)
        canvas.setFont('Helvetica',7);canvas.drawString(36,28,'Confidencial - Uso administrativo')
        canvas.drawRightString(ancho-36,28,f"{datos['generado'].strftime('%d/%m/%Y %H:%M')} Bolivia | Página {doc.page}")
        canvas.restoreState()
    p=datos['periodo']
    ano=p['fecha_inicio'][:4]
    contenido=[texto(f"Gestión {ano}",titulo),texto(f"{p['nombre']} | Fecha de emisión: {datos['generado'].strftime('%d/%m/%Y %H:%M')} (Bolivia)"),Spacer(1,8)]
    grados=[]
    for f in datos['filas']:
        grado=f['grado'] or 'Sin grado registrado'
        if grado not in grados:
            grados.append(grado)
    for grado in grados:
        contenido.append(texto(grado,seccion))
        cabecera=['Apellido Paterno','Apellido Materno','Nombres','Grado','Promedio Físico','Evaluación Académica','Promedio Evaluación Desempeño','NOTA FINAL']
        filas=[[texto(v) for v in cabecera]]
        for f in datos['filas']:
            if (f['grado'] or 'Sin grado registrado') != grado:
                continue
            filas.append([texto(v) for v in [f['apellido_paterno'],f['apellido_materno'],f['nombres'],grado,*(nota(n) for n in f['notas']),nota(f['final'])]])
        tabla=Table(filas,colWidths=[disponible*w/100 for w in (12,12,16,13,10,11,15,11)],repeatRows=1,hAlign='LEFT')
        tabla.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EAF2FC')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F6F9FD')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),1,azul),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6)]))
        contenido.append(tabla)
    if not datos['filas']:
        contenido.append(texto('Sin Instructores Voluntarios activos vinculados a esta Gestión.'))
    firma_estilo=ParagraphStyle('FirmaListado',parent=normal,alignment=1)
    firmas=Table([[texto('____________________________',firma_estilo),texto('____________________________',firma_estilo)],[texto('Comandante',firma_estilo),texto('Jefe de Personal',firma_estilo)]],colWidths=[disponible/2]*2)
    firmas.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),('TOPPADDING',(0,0),(-1,-1),6)]))
    contenido.append(KeepTogether([Spacer(1,24),firmas]))
    doc=SimpleDocTemplate(salida,pagesize=landscape(A4),leftMargin=36,rightMargin=36,topMargin=110,bottomMargin=54,title=f"Gestión {ano}",author='SBRAB')
    doc.build(contenido,onFirstPage=carimbo,onLaterPages=carimbo)
    salida.seek(0)
    return salida
