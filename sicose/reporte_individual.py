"""Expediente administrativo de la Gestión activa; sin resultados inferidos."""
import re
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from flask import current_app
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak

from .asistencias import PROYECCION, totales
from .calculos_5b import calcular
from .perfil_residencia import leer_geografia, antiguedad_calculada


def gestion_activa(c):
    filas = c.execute("""SELECT p.* FROM periodos p WHERE p.estado='ACTIVO'
        AND NOT EXISTS(SELECT 1 FROM bajas_gestion b WHERE b.periodo_id=p.id)""").fetchall()
    if len(filas) != 1:
        raise ValueError('Se requiere una única Gestión activa para generar el reporte individual.')
    return dict(filas[0])


def datos_individual(c, uid, esperado=None):
    p = gestion_activa(c)
    if esperado is not None and p['id'] != esperado:
        raise ValueError('La Gestión activa cambió. Actualiza la selección antes de generar el reporte.')
    fila = c.execute("""SELECT u.id,u.username,u.nombre_completo,u.correo,u.estado,u.foto_perfil,
        v.nombres,v.apellido_paterno,v.apellido_materno,v.fecha_nacimiento,v.codigo_instructor,
        v.especialidad_principal,v.experiencia_operaciones,v.pais_residencia,v.departamento_residencia,
        v.ano_incorporacion,v.fecha_incorporacion,v.grado
        FROM usuarios u JOIN voluntarios v ON v.usuario_id=u.id JOIN roles r ON r.id=u.rol_id
        WHERE u.id=? AND r.nombre='INSTRUCTOR_VOLUNTARIO' AND u.estado IN ('ACTIVO','INACTIVO')""", (uid,)).fetchone()
    if fila is None:
        raise LookupError('Instructor Voluntario admitido no encontrado.')
    persona = dict(fila)
    persona.update(leer_geografia(c, uid))
    persona['antiguedad'] = antiguedad_calculada(persona['ano_incorporacion'])
    persona['secundarias'] = [f[0] for f in c.execute('SELECT especialidad FROM especialidades_secundarias WHERE voluntario_id=? ORDER BY especialidad', (uid,))]
    cursos = [dict(f) for f in c.execute("""SELECT pc.nombre_curso,pc.tipo_curso,pc.entidad_curso,
        pc.inicio_curso,pc.fin_curso,pc.estado,pc.puntaje,pc.fecha_finalizacion,
        EXISTS(SELECT 1 FROM retiros_curso r WHERE r.participacion_id=pc.id) AS retirada
        FROM participaciones_curso pc WHERE pc.voluntario_id=? AND
        ((pc.inicio_curso<=? AND pc.fin_curso>=?) OR pc.fecha_finalizacion BETWEEN ? AND ?)
        ORDER BY pc.inicio_curso,pc.id""", (uid,p['fecha_fin'],p['fecha_inicio'],p['fecha_inicio'],p['fecha_fin']))]
    operaciones = [dict(f) for f in c.execute("""SELECT COALESCE(o.tipo_operativo,o.tipo_evento) AS tipo_evento,CASE WHEN o.departamento IS NOT NULL THEN o.departamento || ' - ' || o.zona ELSE o.lugar END AS lugar,o.institucion_responsable,
        o.fecha_inicio,o.fecha_fin,n.puntos_centesimas,EXISTS(SELECT 1 FROM retiros_operacion r WHERE r.operacion_id=o.id AND r.voluntario_id=x.voluntario_id) AS retirada FROM operaciones o
        JOIN participaciones_operacion x ON x.operacion_id=o.id
        LEFT JOIN notas_operacion_anual n ON n.operacion_id=o.id AND n.voluntario_id=x.voluntario_id
        AND n.periodo_id=? AND NOT EXISTS(SELECT 1 FROM notas_operacion_anual nueva WHERE nueva.anterior_id=n.id)
        WHERE x.voluntario_id=? AND o.fecha_inicio<=? AND COALESCE(o.fecha_fin,o.fecha_inicio)>=?
        ORDER BY o.fecha_inicio,o.id""", (p['id'],uid,p['fecha_fin'],p['fecha_inicio']))]
    asistencia = totales(f[0] for f in c.execute(f'SELECT {PROYECCION} FROM asistencias a WHERE a.voluntario_id=? AND a.fecha BETWEEN ? AND ?', (uid,p['fecha_inicio'],p['fecha_fin'])))
    return dict(persona=persona,periodo=p,cursos=cursos,operaciones=operaciones,
                asistencia=asistencia,calculo=calcular(c,uid,p['id']),
                generado=datetime.now(timezone(timedelta(hours=-4))))


def generar_individual(datos):
    salida = BytesIO()
    azul, naranja = colors.HexColor('#0500B2'), colors.HexColor('#FA9A4B')
    ancho, alto = A4
    disponible = ancho - 72
    normal = ParagraphStyle('Individual',fontName='Helvetica',fontSize=9,leading=13,textColor=colors.HexColor('#24364D'),wordWrap='CJK')
    pequeno = ParagraphStyle('IndividualTabla',parent=normal,fontSize=8,leading=11)
    titulo = ParagraphStyle('IndividualTitulo',parent=normal,fontName='Helvetica-Bold',fontSize=20,leading=25,textColor=azul,spaceAfter=8)
    seccion = ParagraphStyle('IndividualSeccion',parent=normal,fontName='Helvetica-Bold',fontSize=12,leading=16,textColor=azul,spaceBefore=12,spaceAfter=8,keepWithNext=True)
    def texto(v, estilo=pequeno):
        return Paragraph(escape(str(v if v is not None and v != '' else 'Sin registrar')).replace('\n','<br/>'),estilo)
    def tabla(columnas, filas, pesos):
        filas = filas or [['Sin registros en esta Gestión.']+[' ']*(len(columnas)-1)]
        t = Table([[texto(v) for v in columnas]]+[[texto(v) for v in fila] for fila in filas],colWidths=[disponible*w/sum(pesos) for w in pesos],repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EAF2FC')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F6F9FD')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),1,azul),('BOTTOMPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7)]))
        return t
    p, persona, c = datos['periodo'], datos['persona'], datos['calculo']
    codigo = persona['codigo_instructor'] or 'Sin código'
    fecha = datos['generado'].strftime('%d/%m/%Y %H:%M')
    def carimbo(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(azul);canvas.roundRect(32,alto-94,ancho-64,66,6,stroke=1,fill=0)
        logo=Path(__file__).resolve().parent.parent/'frontend/static/images/sbrab-logo.png'
        canvas.drawImage(str(logo),42,alto-84,width=46,height=46,preserveAspectRatio=True,mask='auto')
        canvas.setFillColor(azul);canvas.setFont('Helvetica-Bold',12);canvas.drawString(100,alto-47,'ARMADA BOLIVIANA - SBRAB')
        canvas.setFont('Helvetica',8);canvas.drawString(100,alto-61,'Servicio de Búsqueda y Rescate de la Armada Boliviana')
        canvas.setFillColor(colors.HexColor('#24364D'));canvas.drawString(100,alto-76,'SICOSE | Reporte individual de personal')
        canvas.setStrokeColor(naranja);canvas.line(36,40,ancho-36,40)
        canvas.setFont('Helvetica',7);canvas.drawString(36,28,f'Confidencial - Uso administrativo | {codigo}')
        canvas.drawRightString(ancho-36,28,f'{fecha} Bolivia | Página {doc.page}')
        canvas.restoreState()
    doc = SimpleDocTemplate(salida,pagesize=A4,leftMargin=36,rightMargin=36,topMargin=110,bottomMargin=54,title='Reporte individual - '+persona['nombre_completo'],author='SBRAB')
    contenido = [texto('Reporte individual',titulo),texto(f"Gestión activa: {p['nombre']} | {p['fecha_inicio']} a {p['fecha_fin']}",normal),texto('Información vigente al '+fecha+' (hora de Bolivia). Documento administrativo; no certifica aptitud psicológica.',normal),Spacer(1,12)]
    foto = None
    nombre_foto = persona['foto_perfil']
    if nombre_foto and re.fullmatch(r'[0-9a-f]{32}\.(?:png|jpg)',nombre_foto):
        ruta = Path(current_app.config['PERFIL_MEDIA_FOLDER'])/nombre_foto
        if ruta.is_file():
            try:
                from PIL import Image as Imagen
                with Imagen.open(ruta) as imagen:
                    imagen.load();imagen.thumbnail((400,400));buffer=BytesIO();imagen.convert('RGB').save(buffer,format='JPEG')
                buffer.seek(0);foto=Image(buffer,width=82,height=96,kind='proportional')
            except (OSError,ValueError):
                foto=None
    identidad=Table([[foto or texto('Fotografía no disponible'),[texto(persona['nombre_completo'],seccion),texto('Código: '+codigo,normal),texto('Grado: '+(persona['grado'] or 'Sin registrar'),normal),texto('Estado de cuenta: '+persona['estado'],normal)]]],colWidths=[100,disponible-100])
    identidad.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#F6F9FD')),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]));contenido.append(identidad)
    contenido.append(texto('1. Información personal e institucional',seccion))
    campos=[('Nombres',persona['nombres']),('Apellido paterno',persona['apellido_paterno']),('Apellido materno',persona['apellido_materno']),('Nacimiento',persona['fecha_nacimiento']),('Nacionalidad',persona.get('nacionalidad')),('Correo',persona['correo']),('Usuario',persona['username']),('País de residencia',persona.get('pais_residencia')),('Departamento',persona.get('departamento_residencia')),('Incorporación',persona['fecha_incorporacion'] or (f"Solo año registrado: {persona['ano_incorporacion']}" if persona['ano_incorporacion'] else None)),('Antigüedad (años)',persona['antiguedad']),('Especialidad principal',persona['especialidad_principal']),('Especialidades secundarias',', '.join(persona['secundarias']) or None)]
    pares=[]
    for i in range(0,len(campos),2):
        pares.append([*campos[i],*(campos[i+1] if i+1<len(campos) else (' ',' '))])
    contenido.append(tabla(['Dato','Información','Dato','Información'],pares,[1.2,1.8,1.2,1.8]))
    contenido.extend([texto('Experiencia previa registrada',seccion),texto(persona['experiencia_operaciones'],normal),PageBreak(),texto('2. Calificaciones de la Gestión',seccion)])
    fuentes=c.get('fuentes',{})
    def fuente(clave):
        n=fuentes.get(clave,{})
        nota=n.get('nota') if 'puntos_centesimas' not in n else f"{n['puntos_centesimas']/100:.2f}"
        estado=n.get('origen') or ('INCLUIDA' if n.get('incluida') else 'NO DISPONIBLE')
        if clave in c.get('bloqueos',[]):estado='DESHABILITADA'
        return [nota if nota is not None else 'No disponible',estado.replace('_',' ')]
    filas=[]
    for clave,nombre in [('FISICA_1','Física 1'),('FISICA_2','Física 2'),('DESEMPENO_JEFE','Desempeño del Jefe'),('DESEMPENO_COMANDANTE','Desempeño del Comandante')]:
        filas.append([nombre,*fuente(clave)])
    contenido.append(tabla(['Fuente','Nota / 100','Estado / origen'],filas,[2,1,2]))
    def nota_componente(valor):
        if valor is None:
            return 'No disponible'
        numero=Decimal(str(valor))
        return format(numero,'.2f') if numero.as_tuple().exponent>=-2 else format(numero,'f')
    contenido.extend([Spacer(1,10),tabla(['Componente','Resultado / 100'],[['Físico - promedio de dos pruebas',nota_componente(c.get('fisica'))],['Desempeño - promedio Jefe/Comandante',nota_componente(c.get('desempeno'))],['Académico - acumulado con tope 100',nota_componente(c.get('academica',{}).get('valor'))]],[3,1]),Spacer(1,8),texto('Se conserva el cálculo del sistema sin redistribuir pesos. CERO INICIAL es un cero oficial de inicio, distinto de una nota registrada. Fuentes deshabilitadas no aportan al componente. Regla: '+str(c.get('regla') or 'Sin regla nueva activada')+'.',normal)])
    contenido.append(texto('3. Cursos y Capacitaciones',seccion))
    contenido.append(texto('Participaciones con fechas del curso que coinciden con la Gestión o finalización personal dentro de ella. Se muestran finalizadas y pendientes; la asignación no equivale a aprobación.',normal))
    filas=[]
    for f in datos['cursos']:
        filas.append([f['nombre_curso']+'\n'+f['tipo_curso']+'\n'+f['entidad_curso'],f['inicio_curso']+'\n'+f['fin_curso'],'Retirada' if f['retirada'] else f['estado'],f['fecha_finalizacion'] or 'Pendiente',f['puntaje'] if f['puntaje'] is not None else 'Pendiente'])
    contenido.extend([Spacer(1,8),tabla(['Curso / tipo / entidad','Inicio / fin','Estado personal','Finalización','Puntos'],filas,[3,1.3,1.4,1.4,1])])
    contenido.append(texto('4. Operaciones en las que participó',seccion))
    filas=[[f['tipo_evento']+'\n'+f['institucion_responsable'],f['lugar'],f['fecha_inicio']+'\n'+(f['fecha_fin'] or f['fecha_inicio']),'Retirada (sin aporte)' if f.get('retirada') else (f"{f['puntos_centesimas']/100:.2f}" if f['puntos_centesimas'] is not None else 'Pendiente')] for f in datos['operaciones']]
    contenido.append(tabla(['Operación / institución','Lugar','Inicio / fin','Nota / 100'],filas,[3,2,1.5,1]))
    contenido.append(PageBreak())
    contenido.append(texto('5. Resumen de asistencia',seccion))
    a=datos['asistencia'];porcentaje='No disponible' if a['porcentaje'] is None else f"{a['porcentaje']:.2f}%"
    contenido.append(tabla(['Asiste','Atraso','Permiso','Falta','Asistencia'],[[a['ASISTE'],a['ATRASO'],a['PERMISO'],a['FALTA'],porcentaje]],[1,1,1,1,1.5]))
    contenido.extend([Spacer(1,8),texto('(Asiste + Atraso) / (Asiste + Atraso + Falta) x 100. Permiso excluido. Sin registros computables: No disponible. Conteo por registros, no por días; una fecha sin registro no se convierte en falta. Indicador informativo separado de las notas.',normal),texto('6. Pruebas psicométricas',seccion)])
    contenido.append(tabla(['Instrumento','Resultado','Subescalas'],[['Psicométrica 1','Pendiente','Pendientes de seleccionar y aprobar el instrumento.'],['Psicométrica 2','Pendiente','Pendientes de seleccionar y aprobar el instrumento.']],[1.4,1,3]))
    contenido.extend([Spacer(1,8),texto('No existen instrumentos oficiales implementados ni resultados psicométricos. Los formularios aritméticos demostrativos no se incluyen. Las futuras subescalas conservarán las reglas de su instrumento; no se asignan valores ni categorías ficticias.',normal),texto('7. Recomendación de la red neuronal',seccion),tabla(['Ámbito','Recomendación'],[['Ascenso','Pendiente'],['Participación en operaciones','Pendiente']],[2,3]),Spacer(1,8),texto('Modelo sin entrenar ni validar. No se ha realizado inferencia y no se emite recomendación automática.',normal),texto('Alcance y trazabilidad',seccion),texto('Fuentes: perfil institucional, participaciones en cursos y operaciones, notas vigentes y registros personales de asistencia de la Gestión activa. Se presenta el estado actual consultado en una misma transacción; no es una instantánea de cierre ni una evaluación clínica. Datos ausentes se identifican expresamente. Uso reservado a personal administrativo autorizado.',normal)])
    doc.build(contenido,onFirstPage=carimbo,onLaterPages=carimbo)
    salida.seek(0)
    return salida
