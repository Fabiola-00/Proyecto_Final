"""Correcciones trazables, resumen propio y reportes de asistencia."""
from collections import Counter
from datetime import date
from flask import Blueprint,jsonify,request,render_template,send_file
from flask_login import current_user
from . import db
from .permissions import role_required

asistencias_bp=Blueprint('asistencias',__name__)
ESTADOS=('ASISTE','ATRASO','PERMISO','FALTA')
PROYECCION="COALESCE(a.estado_detalle,CASE a.estado WHEN 'PRESENTE' THEN 'ASISTE' WHEN 'AUSENTE' THEN 'FALTA' ELSE 'PERMISO' END)"

def fallo(mensaje,estado=400):return jsonify(error=mensaje,codigo='asistencia_invalida'),estado

def alcance(conexion,identificador):
    consulta='''SELECT a.* FROM asistencias a JOIN voluntarios v ON v.usuario_id=a.voluntario_id
                JOIN usuarios u ON u.id=v.usuario_id WHERE a.id=?'''
    parametros=[identificador]
    return conexion.execute(consulta,parametros).fetchone()

@asistencias_bp.patch('/api/jefe-personal/asistencias/<int:identificador>')
@role_required('ADMINISTRADOR','JEFE_PERSONAL')
def corregir_asistencia(identificador):
    entrada=request.get_json(silent=True)
    if not isinstance(entrada,dict) or set(entrada)!={'estado'} or entrada['estado'] not in ESTADOS:return fallo('Selecciona uno de los cuatro estados.')
    conexion=db.obtener_conexion();fila=alcance(conexion,identificador)
    if fila is None:return fallo('Asistencia fuera de tu ámbito.',404)
    if conexion.execute("SELECT estado FROM usuarios WHERE id=?",(fila['voluntario_id'],)).fetchone()[0]!='ACTIVO':return fallo('Reactiva la cuenta antes de corregir asistencia.',409)
    estado=entrada['estado']
    anterior=fila['estado_detalle'] or {'PRESENTE':'ASISTE','AUSENTE':'FALTA','JUSTIFICADO':'PERMISO'}[fila['estado']]
    if anterior==estado:return jsonify(ok=True)
    historico={'ASISTE':'PRESENTE','ATRASO':'PRESENTE','PERMISO':'JUSTIFICADO','FALTA':'AUSENTE'}[estado]
    conexion.execute('UPDATE asistencias SET estado=?,estado_detalle=?,registrado_por=? WHERE id=?',(historico,estado,current_user.id,identificador))
    db.registrar_auditoria(conexion,current_user.id,'ASISTENCIA_CORREGIDA','EXITOSO');conexion.commit()
    return jsonify(ok=True)

@asistencias_bp.get('/api/jefe-personal/asistencias/<int:identificador>/historial')
@role_required('ADMINISTRADOR','JEFE_PERSONAL')
def historial_asistencia(identificador):
    conexion=db.obtener_conexion()
    if alcance(conexion,identificador) is None:return fallo('Asistencia fuera de tu ámbito.',404)
    filas=conexion.execute('''SELECT h.estado_anterior,h.estado_nuevo,h.corregido_en,u.nombre_completo AS corregido_por
        FROM historial_asistencias h JOIN usuarios u ON u.id=h.corregido_por WHERE h.asistencia_id=? ORDER BY h.id''',(identificador,))
    return jsonify(historial=[dict(f) for f in filas])

def totales(estados):
    conteo=Counter(estados);resultado={estado:conteo[estado] for estado in ESTADOS}
    base=resultado['ASISTE']+resultado['ATRASO']+resultado['FALTA']
    resultado['porcentaje']=round(100*(resultado['ASISTE']+resultado['ATRASO'])/base,2) if base else None
    resultado['computables']=base
    return resultado

@asistencias_bp.get('/mis-asistencias')
@role_required('INSTRUCTOR_VOLUNTARIO')
def pagina_propia():
    return render_template('calendario_asistencias.html',titulo_pagina='Mis asistencias',nav_activo='asistencias',indicadores=[],
        periodo_actual=db.periodo_actual(),descripcion='Calendario y resumen de tus asistencias por gestión.')

@asistencias_bp.get('/api/instructor-voluntario/asistencias')
@role_required('INSTRUCTOR_VOLUNTARIO')
def resumen_propio():
    if set(request.args)-{'gestion'}:return fallo('Solo se admite la gestión propia.')
    try:
        ano=int(request.args.get('gestion',date.today().year))
        if not 1<=ano<=9999:raise ValueError
    except (ValueError,TypeError):return fallo('Gestión no válida.')
    conexion=db.obtener_conexion()
    filas=conexion.execute(f'SELECT a.fecha,{PROYECCION} AS estado FROM asistencias a WHERE a.voluntario_id=? AND a.fecha BETWEEN ? AND ? ORDER BY a.fecha,a.id',
        (current_user.id,f'{ano:04d}-01-01',f'{ano:04d}-12-31')).fetchall()
    return jsonify(gestion=ano,registros=[dict(f) for f in filas],totales=totales(f['estado'] for f in filas))

def datos_reporte():
    if set(request.args)-{'desde','hasta'}:raise ValueError('Selecciona únicamente el rango de fechas.')
    try:
        desde=date.fromisoformat(request.args.get('desde','')).isoformat();hasta=date.fromisoformat(request.args.get('hasta','')).isoformat()
        if hasta<desde:raise ValueError
    except (ValueError,TypeError):raise ValueError('Rango de fechas no válido.')
    consulta=f'''SELECT a.fecha,a.actividad,{PROYECCION} AS estado,u.id AS voluntario_id,
        u.nombre_completo AS nombre,v.codigo_instructor AS codigo FROM asistencias a
        JOIN voluntarios v ON v.usuario_id=a.voluntario_id JOIN usuarios u ON u.id=v.usuario_id WHERE a.fecha BETWEEN ? AND ?'''
    parametros=[desde,hasta]
    filas=db.obtener_conexion().execute(consulta+' ORDER BY a.fecha,a.actividad,u.nombre_completo,a.id',parametros).fetchall()
    llamadas=sorted({(f['fecha'],f['actividad'] or '') for f in filas})
    personas={}
    for fila in filas:
        persona=personas.setdefault(fila['voluntario_id'],{'nombre':fila['nombre'],'codigo':fila['codigo'],'marcas':{},'estados':[]})
        persona['marcas'][(fila['fecha'],fila['actividad'] or '')]=fila['estado'];persona['estados'].append(fila['estado'])
    registros=[]
    for persona in sorted(personas.values(),key=lambda p:p['nombre']):
        registros.append({'nombre':persona['nombre'],'codigo':persona['codigo'],
            'estados':[persona['marcas'].get(llamada) for llamada in llamadas], 'totales':totales(persona['estados'])})
    return {'desde':desde,'hasta':hasta,'responsable':current_user.nombre,'llamadas':[{'fecha':f,'actividad':a} for f,a in llamadas], 'personas':registros}

@asistencias_bp.get('/api/jefe-personal/asistencias/reporte')
@role_required('ADMINISTRADOR','JEFE_PERSONAL')
def reporte_json():
    try:return jsonify(datos_reporte())
    except ValueError as e:return fallo(str(e))

@asistencias_bp.get('/api/jefe-personal/asistencias/reporte.pdf')
@role_required('ADMINISTRADOR','JEFE_PERSONAL')
def reporte_pdf():
    from .reportes_asistencias import generar_pdf_asistencias
    try:datos=datos_reporte()
    except ValueError as e:return fallo(str(e))
    archivo=generar_pdf_asistencias(datos)
    conexion=db.obtener_conexion();db.registrar_auditoria(conexion,current_user.id,'REPORTE_ASISTENCIAS_GENERADO','EXITOSO');conexion.commit()
    respuesta=send_file(archivo,mimetype='application/pdf',as_attachment=False,download_name=f"asistencias-{datos['desde']}-{datos['hasta']}.pdf",max_age=0)
    respuesta.headers['Cache-Control']='private, no-store';return respuesta
