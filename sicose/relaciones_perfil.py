"""Catálogo de cursos y participaciones en operaciones por ámbito autorizado."""
import sqlite3
from datetime import date
from flask import Blueprint, jsonify, request, render_template
from flask_login import current_user
from . import db
from .permissions import role_required

relaciones_bp = Blueprint('relaciones', __name__)

def error(mensaje, estado=400):
    return jsonify(error=mensaje, codigo='datos_invalidos' if estado == 400 else 'sin_permiso'), estado

def datos():
    valor = request.get_json(silent=True)
    return valor if isinstance(valor, dict) else None

def auditar(conexion, accion):
    db.registrar_auditoria(conexion, current_user.id, accion, 'EXITOSO')

def personal_permitido(conexion, usuario_id):
    consulta = "SELECT 1 FROM voluntarios v JOIN usuarios u ON u.id=v.usuario_id WHERE v.usuario_id=? AND u.estado='ACTIVO'"
    parametros = [usuario_id]
    if current_user.rol == 'JEFE_PERSONAL':
        consulta += ' AND v.instructor_id=?'; parametros.append(current_user.id)
    return conexion.execute(consulta, parametros).fetchone() is not None

def curso_para_registro(conexion, valor):
    if valor is None or valor == '': return None
    if not isinstance(valor, int) or isinstance(valor, bool): raise ValueError('Selecciona un curso válido.')
    fila = conexion.execute('SELECT id,nombre FROM cursos WHERE id=?', (valor,)).fetchone()
    if fila is None: raise ValueError('Curso no encontrado.')
    return fila

@relaciones_bp.get('/api/cursos')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
def listar_cursos():
    return jsonify(cursos=[dict(f) for f in db.obtener_conexion().execute('SELECT * FROM cursos ORDER BY nombre,id')])

@relaciones_bp.post('/api/cursos')
@relaciones_bp.patch('/api/cursos/<int:curso_id>')
@role_required('ADMINISTRADOR','JEFE_PERSONAL')
def guardar_curso(curso_id=None):
    entrada = datos()
    campos = ("nombre", "tipo", "entidad", "fecha_inicio", "fecha_fin", "estado", "observaciones")
    if entrada is None or not entrada or set(entrada)-set(campos): return error("Campos de curso no válidos.")
    conexion = db.obtener_conexion()
    anterior = conexion.execute("SELECT * FROM cursos WHERE id=?", (curso_id,)).fetchone() if curso_id else None
    if curso_id and anterior is None: return error("Curso no encontrado.",404)
    valores = dict(anterior) if anterior else {}
    valores.update(entrada)
    try:
        for campo,limite in (("nombre",160),("entidad",160),("observaciones",2000)):
            valor = valores.get(campo)
            if valor is not None and (not isinstance(valor,str) or len(valor.strip())>limite): raise ValueError("Texto del curso no válido.")
            valores[campo] = valor.strip() or None if valor is not None else None
        if not valores["nombre"]: raise ValueError("El nombre es obligatorio.")
        for campo,opciones in (("tipo",("Capacitación","Especialización","Actualización","Taller","Seminario (Webinar)")),("estado",("Próximo","En curso","Finalizado"))):
            if valores.get(campo) not in opciones and (curso_id is None or campo in entrada): raise ValueError("Selecciona tipo y estado válidos.")
        for campo in ("fecha_inicio","fecha_fin"):
            valor = valores.get(campo)
            if valor is not None and not isinstance(valor,str): raise ValueError("Fecha no válida.")
            valores[campo] = date.fromisoformat(valor).isoformat() if valor else None
        if valores["fecha_fin"] and (not valores["fecha_inicio"] or valores["fecha_fin"]<valores["fecha_inicio"]): raise ValueError("El fin requiere inicio y no puede precederlo.")
    except (ValueError,TypeError) as fallo: return error(str(fallo))
    registro=tuple(valores.get(c) for c in campos)
    try:
        if curso_id is None:
            curso_id=conexion.execute("INSERT INTO cursos(nombre,tipo,entidad,fecha_inicio,fecha_fin,estado,observaciones) VALUES (?,?,?,?,?,?,?)",registro).lastrowid
        else:
            conexion.execute("UPDATE cursos SET nombre=?,tipo=?,entidad=?,fecha_inicio=?,fecha_fin=?,estado=?,observaciones=? WHERE id=?",(*registro,curso_id))
        auditar(conexion,'CURSO_GUARDADO'); conexion.commit()
    except sqlite3.IntegrityError:
        conexion.rollback(); return error('Ya existe un curso con ese nombre.',409)
    return jsonify(ok=True,id=curso_id), 201 if request.method=='POST' else 200

@relaciones_bp.get('/api/instructor-voluntario/capacitaciones')
@role_required('INSTRUCTOR_VOLUNTARIO')
def cursos_propios():
    filas = db.obtener_conexion().execute('''SELECT c.id,c.nombre,c.entidad,c.fecha,c.curso_id,
        k.nombre AS curso_catalogo FROM capacitaciones c LEFT JOIN cursos k ON k.id=c.curso_id
        WHERE c.voluntario_id=? ORDER BY c.fecha DESC,c.id DESC''',(current_user.id,))
    return jsonify(capacitaciones=[dict(f) for f in filas])

@relaciones_bp.get('/mis-cursos')
@role_required('INSTRUCTOR_VOLUNTARIO')
def pagina_cursos_propios():
    return render_template('consulta_cursos.html',titulo_pagina='Mis cursos',nav_activo='capacitaciones',
        indicadores=[],periodo_actual=db.periodo_actual(),descripcion='Consulta tu historial formativo.')

@relaciones_bp.get('/gestion/operaciones')
@role_required('ADMINISTRADOR','JEFE_PERSONAL','INSTRUCTOR_VOLUNTARIO')
def pagina_operaciones():
    return render_template('gestion_operaciones.html',titulo_pagina='Operaciones',nav_activo='operaciones',
        indicadores=[],periodo_actual=db.periodo_actual(),descripcion='Eventos y participaciones dentro de tu ámbito.')

@relaciones_bp.get('/api/operaciones')
@role_required('ADMINISTRADOR','JEFE_PERSONAL','INSTRUCTOR_VOLUNTARIO')
def listar_operaciones():
    conexion=db.obtener_conexion()
    consulta='SELECT o.* FROM operaciones o'
    parametros=[]
    if current_user.rol=='INSTRUCTOR_VOLUNTARIO':
        consulta+=' WHERE EXISTS(SELECT 1 FROM participaciones_operacion p WHERE p.operacion_id=o.id AND p.voluntario_id=?)'
        parametros.append(current_user.id)
    eventos=[dict(f) for f in conexion.execute(consulta+' ORDER BY o.fecha_inicio DESC,o.id DESC',parametros)]
    for evento in eventos:
        q='''SELECT p.voluntario_id,u.nombre_completo AS nombre FROM participaciones_operacion p
             JOIN voluntarios v ON v.usuario_id=p.voluntario_id JOIN usuarios u ON u.id=v.usuario_id WHERE p.operacion_id=?'''
        args=[evento['id']]
        if current_user.rol=='JEFE_PERSONAL': q+=" AND v.instructor_id=? AND u.estado='ACTIVO'";args.append(current_user.id)
        if current_user.rol=='INSTRUCTOR_VOLUNTARIO': q+=' AND p.voluntario_id=?';args.append(current_user.id)
        evento['participantes']=[dict(f) for f in conexion.execute(q+' ORDER BY u.nombre_completo',args)]
    return jsonify(operaciones=eventos)

@relaciones_bp.post('/api/operaciones')
@relaciones_bp.patch('/api/operaciones/<int:operacion_id>')
@role_required('ADMINISTRADOR')
def guardar_operacion(operacion_id=None):
    entrada=datos(); campos={'tipo_evento','lugar','fecha_inicio','fecha_fin','institucion_responsable'}
    if entrada is None or set(entrada)-campos: return error('Campos de operación no válidos.')
    conexion=db.obtener_conexion()
    anterior=conexion.execute('SELECT * FROM operaciones WHERE id=?',(operacion_id,)).fetchone() if operacion_id else None
    if operacion_id and anterior is None:return error('Operación no encontrada.',404)
    valores=dict(anterior) if anterior else {};valores.update(entrada)
    try:
        for campo in ('tipo_evento','lugar','institucion_responsable'):
            valor=valores.get(campo)
            if not isinstance(valor,str) or not 1<=len(valor.strip())<=160: raise ValueError('Tipo, lugar e institución son obligatorios (máximo 160 caracteres).')
            valores[campo]=valor.strip()
        inicio=date.fromisoformat(valores.get('fecha_inicio',''))
        fin=valores.get('fecha_fin') or None
        if fin and date.fromisoformat(fin)<inicio:raise ValueError('La fecha final no puede preceder a la inicial.')
        valores['fecha_fin']=fin
    except (ValueError,TypeError):return error('Revisa los campos obligatorios y las fechas de inicio/fin.')
    registro=tuple(valores.get(c) for c in ('tipo_evento','lugar','fecha_inicio','fecha_fin','institucion_responsable'))
    if operacion_id:
        conexion.execute('UPDATE operaciones SET tipo_evento=?,lugar=?,fecha_inicio=?,fecha_fin=?,institucion_responsable=? WHERE id=?',(*registro,operacion_id))
    else:
        operacion_id=conexion.execute('INSERT INTO operaciones(tipo_evento,lugar,fecha_inicio,fecha_fin,institucion_responsable) VALUES (?,?,?,?,?)',registro).lastrowid
    auditar(conexion,'OPERACION_GUARDADA');conexion.commit()
    return jsonify(ok=True,id=operacion_id),201 if request.method=='POST' else 200

@relaciones_bp.post('/api/operaciones/<int:operacion_id>/participaciones')
@role_required('ADMINISTRADOR','JEFE_PERSONAL')
def vincular_participacion(operacion_id):
    entrada=datos()
    if entrada is None or set(entrada)!={'voluntario_id'}:return error('Selecciona un Instructor Voluntario.')
    usuario_id=entrada['voluntario_id'];conexion=db.obtener_conexion()
    if not isinstance(usuario_id,int) or isinstance(usuario_id,bool):return error('Instructor no válido.')
    if not conexion.execute('SELECT 1 FROM operaciones WHERE id=?',(operacion_id,)).fetchone():return error('Operación no encontrada.',404)
    if not personal_permitido(conexion,usuario_id):return error('Personal fuera de tu ámbito activo.',404)
    try:
        conexion.execute('INSERT INTO participaciones_operacion VALUES (?,?)',(operacion_id,usuario_id))
        auditar(conexion,'PARTICIPACION_REGISTRADA');conexion.commit()
    except sqlite3.IntegrityError:
        conexion.rollback();return error('La participación ya está registrada.',409)
    return jsonify(ok=True),201

@relaciones_bp.get('/api/cursos/reporte.pdf')
@role_required('ADMINISTRADOR','JEFE_PERSONAL')
def reporte_cursos():
    from .reportes_cursos import generar_pdf_cursos
    from flask import send_file
    argumentos=request.args
    if set(argumentos)-{'desde','hasta','tipo','estado'}: return error('Filtros no válidos.')
    try:
        desde=date.fromisoformat(argumentos.get('desde','')).isoformat()
        hasta=date.fromisoformat(argumentos.get('hasta','')).isoformat()
        if hasta<desde: raise ValueError
    except (ValueError,TypeError): return error('Selecciona un rango de fechas válido por fecha de inicio.')
    tipo=argumentos.get('tipo','');estado=argumentos.get('estado','')
    if tipo and tipo not in ('Capacitación','Especialización','Actualización','Taller','Seminario (Webinar)'):return error('Tipo no válido.')
    if estado and estado not in ('Próximo','En curso','Finalizado'):return error('Estado no válido.')
    consulta='SELECT nombre,tipo,entidad,fecha_inicio,fecha_fin,estado FROM cursos WHERE fecha_inicio>=? AND fecha_inicio<=?'
    parametros=[desde,hasta]
    for campo,valor in (('tipo',tipo),('estado',estado)):
        if valor: consulta+=f' AND {campo}=?';parametros.append(valor)
    conexion=db.obtener_conexion()
    filas=[dict(f) for f in conexion.execute(consulta+' ORDER BY fecha_inicio,nombre,id',parametros)]
    archivo=generar_pdf_cursos(filas,desde,hasta,tipo,estado)
    auditar(conexion,'REPORTE_CURSOS_GENERADO');conexion.commit()
    respuesta=send_file(archivo,mimetype='application/pdf',as_attachment=True,download_name=f'cursos-{desde}-{hasta}.pdf',max_age=0)
    respuesta.headers['Cache-Control']='private, no-store'
    return respuesta
