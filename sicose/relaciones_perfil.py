"""Catálogo de cursos y participaciones en operaciones por ámbito autorizado."""
import sqlite3
from datetime import date
from flask import Blueprint, jsonify, request, render_template
from flask_login import current_user
from . import db
from .permissions import role_required
from .formacion import proyectar_curso, validar_puntaje, fecha, hoy_bolivia, TIPOS

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
    return conexion.execute(consulta, parametros).fetchone() is not None

def curso_para_registro(conexion, valor):
    if valor is None or valor == '': return None
    if not isinstance(valor, int) or isinstance(valor, bool): raise ValueError('Selecciona un curso válido.')
    fila = conexion.execute('SELECT id,nombre FROM cursos WHERE id=?', (valor,)).fetchone()
    if fila is None: raise ValueError('Curso no encontrado.')
    if conexion.execute('SELECT 1 FROM bajas_curso WHERE curso_id=?',(valor,)).fetchone(): raise ValueError('El curso está dado de baja.')
    return fila

@relaciones_bp.get('/api/cursos')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
def listar_cursos():
    filtro='' if request.args.get('incluir_bajas')=='1' else ' WHERE NOT EXISTS(SELECT 1 FROM bajas_curso b WHERE b.curso_id=c.id)'
    return jsonify(hoy=hoy_bolivia().isoformat(), cursos=[proyectar_curso(f) for f in db.obtener_conexion().execute("SELECT c.*,EXISTS(SELECT 1 FROM bajas_curso b WHERE b.curso_id=c.id) AS baja,(SELECT COUNT(*) FROM participaciones_curso p WHERE p.curso_id=c.id) AS participantes_total,(SELECT COUNT(*) FROM participaciones_curso p WHERE p.curso_id=c.id AND p.estado='Finalizado') AS finalizados_total FROM cursos c"+filtro+" ORDER BY c.nombre,c.id")])

@relaciones_bp.post('/api/cursos')
@relaciones_bp.patch('/api/cursos/<int:curso_id>')
@role_required('ADMINISTRADOR','JEFE_PERSONAL')
def guardar_curso(curso_id=None):
    entrada = datos()
    campos = ("nombre", "tipo", "entidad", "fecha_inicio", "fecha_fin", "puntaje", "observaciones")
    if entrada is None or not entrada or set(entrada)-set(campos): return error("Campos de curso no válidos.")
    conexion = db.obtener_conexion()
    try: conexion.execute('BEGIN IMMEDIATE')
    except sqlite3.OperationalError: return error('Edición concurrente del curso. Recarga.',409)
    anterior = conexion.execute("SELECT * FROM cursos WHERE id=?", (curso_id,)).fetchone() if curso_id else None
    if curso_id and conexion.execute('SELECT 1 FROM bajas_curso WHERE curso_id=?',(curso_id,)).fetchone(): return error('El curso está dado de baja.',409)
    if curso_id and anterior is None: return error("Curso no encontrado.",404)
    valores = dict(anterior) if anterior else {}
    valores.update(entrada)
    try:
        for campo,limite in (("nombre",160),("entidad",160),("observaciones",2000)):
            valor = valores.get(campo)
            if valor is not None and (not isinstance(valor,str) or len(valor.strip())>limite): raise ValueError("Texto del curso no válido.")
            valores[campo] = valor.strip() or None if valor is not None else None
        if not valores["nombre"]: raise ValueError("El nombre es obligatorio.")
        if (curso_id is None or "entidad" in entrada) and not valores["entidad"]: raise ValueError("La entidad organizadora es obligatoria.")
        if (curso_id is None or "tipo" in entrada) and valores.get("tipo") not in TIPOS: raise ValueError("Selecciona un tipo válido.")
        if curso_id is None or "puntaje" in entrada: validar_puntaje(valores.get("puntaje"))
        for campo in ("fecha_inicio","fecha_fin"):
            valor = valores.get(campo)
            if curso_id is None or campo in entrada:
                valores[campo] = fecha(valor).isoformat()
        if curso_id is None or {"fecha_inicio","fecha_fin"}.intersection(entrada):
            if not valores.get("fecha_inicio") or not valores.get("fecha_fin") or valores["fecha_fin"] < valores["fecha_inicio"]: raise ValueError("Inicio y fin son obligatorios; el fin no puede preceder al inicio.")
    except (ValueError,TypeError) as fallo: return error(str(fallo))
    registro=tuple(valores.get(c) for c in campos)
    try:
        if curso_id is None:
            curso_id=conexion.execute("INSERT INTO cursos(nombre,tipo,entidad,fecha_inicio,fecha_fin,puntaje,observaciones) VALUES (?,?,?,?,?,?,?)",registro).lastrowid
        else:
            conexion.execute("UPDATE cursos SET nombre=?,tipo=?,entidad=?,fecha_inicio=?,fecha_fin=?,puntaje=?,observaciones=? WHERE id=?",(*registro,curso_id))
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
    from .panel_instructor import pagina
    return pagina('cursos')

@relaciones_bp.get('/gestion/operaciones')
@role_required('ADMINISTRADOR','JEFE_PERSONAL','INSTRUCTOR_VOLUNTARIO')
def pagina_operaciones():
    contexto = {}
    if current_user.rol == 'INSTRUCTOR_VOLUNTARIO':
        from .panel_instructor import seleccion
        opciones, elegida = seleccion(db.obtener_conexion())
        contexto = dict(gestiones=opciones, gestion=elegida)
    return render_template('gestion_operaciones.html',titulo_pagina='Operaciones',nav_activo='operaciones',
        indicadores=[],periodo_actual=db.periodo_actual(),descripcion='Eventos y participaciones dentro de tu ámbito.', **contexto)

@relaciones_bp.get('/api/operaciones')
@role_required('ADMINISTRADOR','JEFE_PERSONAL','INSTRUCTOR_VOLUNTARIO')
def listar_operaciones():
    from .operaciones import baja
    conexion=db.obtener_conexion()
    consulta='SELECT o.* FROM operaciones o'
    parametros=[]
    if current_user.rol=='INSTRUCTOR_VOLUNTARIO':
        consulta+=' WHERE EXISTS(SELECT 1 FROM participaciones_operacion p WHERE p.operacion_id=o.id AND p.voluntario_id=?)'
        parametros.append(current_user.id)
        from .panel_instructor import seleccion
        _, p = seleccion(conexion) if request.args else ([], None)
        if p:
            consulta += ' AND o.fecha_inicio<=? AND COALESCE(o.fecha_fin,o.fecha_inicio)>=?'
            parametros.extend((p['fecha_fin'],p['fecha_inicio']))
        elif request.args:
            consulta += ' AND 0'
    elif request.args.get('incluir_bajas') != '1':
        consulta+=' WHERE NOT EXISTS(SELECT 1 FROM bajas_operacion b WHERE b.operacion_id=o.id)'
    eventos=[dict(f) for f in conexion.execute(consulta+' ORDER BY o.fecha_inicio DESC,o.id DESC',parametros)]
    for evento in eventos:
        evento['baja']=baja(conexion,evento['id'])
        q='''SELECT p.voluntario_id,p.revision,u.estado AS cuenta_estado,u.nombre_completo AS nombre,EXISTS(SELECT 1 FROM retiros_operacion_vigentes r WHERE r.operacion_id=p.operacion_id AND r.voluntario_id=p.voluntario_id) AS retirada FROM participaciones_operacion p
             JOIN voluntarios v ON v.usuario_id=p.voluntario_id JOIN usuarios u ON u.id=v.usuario_id WHERE p.operacion_id=?'''
        args=[evento['id']]
        if current_user.rol=='INSTRUCTOR_VOLUNTARIO': q+=' AND p.voluntario_id=?';args.append(current_user.id)
        evento['participantes']=[dict(f) for f in conexion.execute(q+' ORDER BY u.nombre_completo',args)]
    return jsonify(operaciones=eventos)

@relaciones_bp.post('/api/operaciones')
@relaciones_bp.patch('/api/operaciones/<int:operacion_id>')
@role_required('ADMINISTRADOR','JEFE_PERSONAL')
def guardar_operacion(operacion_id=None):
    from .operaciones import TIPOS as TIPOS_OPERATIVO, ESTADOS, baja
    entrada=datos(); campos={'tipo_evento','tipo_operativo','estado_operacion','revision','lugar','departamento','zona','fecha_inicio','fecha_fin','institucion_responsable'}
    if entrada is None or set(entrada)-campos: return error('Campos de operación no válidos.')
    conexion=db.obtener_conexion()
    anterior=conexion.execute('SELECT * FROM operaciones WHERE id=?',(operacion_id,)).fetchone() if operacion_id else None
    if operacion_id and anterior is None:return error('Operación no encontrada.',404)
    valores=dict(anterior) if anterior else {};valores.update(entrada)
    if not anterior and 'tipo_operativo' in entrada:
        valores['tipo_evento']=entrada['tipo_operativo']
    try:
        if 'departamento' in entrada or 'zona' in entrada:
            from .perfil_residencia import DEPARTAMENTOS_BOLIVIA
            if valores.get('departamento') not in DEPARTAMENTOS_BOLIVIA or not isinstance(valores.get('zona'),str) or not 1<=len(valores['zona'].strip())<=160:
                raise ValueError('Selecciona Departamento y Zona válidos.')
            valores['zona']=valores['zona'].strip()
            if not anterior:valores['lugar']=valores['departamento']+' - '+valores['zona']
        for campo,opciones in [('tipo_operativo',TIPOS_OPERATIVO),('estado_operacion',ESTADOS)]:
            if campo in entrada and entrada[campo] not in opciones:
                raise ValueError('Tipo o estado fuera del catálogo.')
        if not anterior and 'tipo_operativo' in entrada and 'estado_operacion' not in entrada:
            raise ValueError('Selecciona el estado de la operación.')
        for campo in ('tipo_evento','institucion_responsable'):
            valor=valores.get(campo)
            if not isinstance(valor,str) or not 1<=len(valor.strip())<=160: raise ValueError('Tipo, lugar e institución son obligatorios (máximo 160 caracteres).')
            valores[campo]=valor.strip()
        if not isinstance(valores.get('lugar'),str) or not 1<=len(valores['lugar'].strip())<=(200 if valores.get('departamento') else 160):raise ValueError('Lugar histórico no válido.')
        inicio=date.fromisoformat(valores.get('fecha_inicio',''))
        fin=valores.get('fecha_fin') or None
        if fin and date.fromisoformat(fin)<inicio:raise ValueError('La fecha final no puede preceder a la inicial.')
        valores['fecha_fin']=fin
    except (ValueError,TypeError):return error('Revisa los campos obligatorios y las fechas de inicio/fin.')
    registro=tuple(valores.get(c) for c in ('tipo_evento','lugar','fecha_inicio','fecha_fin','institucion_responsable','tipo_operativo','estado_operacion','departamento','zona'))
    try:
        conexion.execute('BEGIN IMMEDIATE')
    except sqlite3.OperationalError:
        return error('Edición concurrente; recarga la operación.',409)
    if operacion_id:
        vigente=conexion.execute('SELECT revision FROM operaciones WHERE id=?',(operacion_id,)).fetchone()
        if vigente is None or vigente['revision']!=anterior['revision'] or baja(conexion,operacion_id) or ('revision' in entrada and (type(entrada['revision']) is not int or vigente['revision']!=entrada['revision'])):
            conexion.rollback();return error('La operación cambió o está dada de baja. Recarga.',409)
    if operacion_id and conexion.execute("SELECT 1 FROM notas_operacion_anual n JOIN periodos p ON p.id=n.periodo_id WHERE n.operacion_id=? AND p.estado='CERRADO' LIMIT 1",(operacion_id,)).fetchone():
        conexion.rollback();return error('La operación tiene notas en una Gestión cerrada; requiere reapertura administrativa.',409)
    if operacion_id:
        conexion.execute('UPDATE operaciones SET tipo_evento=?,lugar=?,fecha_inicio=?,fecha_fin=?,institucion_responsable=?,tipo_operativo=?,estado_operacion=?,departamento=?,zona=?,revision=revision+1 WHERE id=?',(*registro,operacion_id))
    else:
        operacion_id=conexion.execute('INSERT INTO operaciones(tipo_evento,lugar,fecha_inicio,fecha_fin,institucion_responsable,tipo_operativo,estado_operacion,departamento,zona) VALUES (?,?,?,?,?,?,?,?,?)',registro).lastrowid
    auditar(conexion,f'OPERACION_GUARDADA:{operacion_id}:TIPO={valores.get("tipo_operativo")}:ESTADO={valores.get("estado_operacion")}');conexion.commit()
    return jsonify(ok=True,id=operacion_id),201 if request.method=='POST' else 200

@relaciones_bp.post('/api/operaciones/<int:operacion_id>/participaciones')
@role_required('ADMINISTRADOR','JEFE_PERSONAL')
def vincular_participacion(operacion_id):
    from .operaciones import baja
    entrada=datos()
    if entrada is None or set(entrada) not in ({'voluntario_id'},{'voluntario_ids'}):return error('Selecciona participantes.')
    ids=entrada.get('voluntario_ids',[entrada.get('voluntario_id')])
    if not isinstance(ids,list) or not 1<=len(ids)<=500 or any(not isinstance(i,int) or isinstance(i,bool) for i in ids) or len(ids)!=len(set(ids)):
        return error('Selecciona participantes válidos sin duplicados (máximo 500).')
    conexion=db.obtener_conexion()
    try:
        conexion.execute('BEGIN IMMEDIATE')
        if not conexion.execute('SELECT 1 FROM operaciones WHERE id=?',(operacion_id,)).fetchone():
            conexion.rollback();return error('Operación no encontrada.',404)
        if baja(conexion,operacion_id):
            conexion.rollback();return error('La operación está dada de baja; conserva sus participaciones históricas.',409)
        if any(not personal_permitido(conexion,i) for i in ids):
            conexion.rollback();return error('Personal fuera de tu ámbito activo.',404)
        for i in ids:
            anterior=conexion.execute('SELECT revision FROM participaciones_operacion WHERE operacion_id=? AND voluntario_id=?',(operacion_id,i)).fetchone()
            if anterior:
                if not conexion.execute('SELECT 1 FROM retiros_operacion_vigentes WHERE operacion_id=? AND voluntario_id=?',(operacion_id,i)).fetchone():
                    conexion.rollback();return error('Una participación ya está vigente; no se guardó ninguna.',409)
                if conexion.execute("SELECT 1 FROM notas_operacion_anual n JOIN periodos p ON p.id=n.periodo_id WHERE n.operacion_id=? AND n.voluntario_id=? AND p.estado='CERRADO'",(operacion_id,i)).fetchone():
                    conexion.rollback();return error('La participación tiene notas en una Gestión cerrada; requiere reapertura administrativa.',409)
                conexion.execute('INSERT INTO movimientos_participacion_operacion VALUES (?,?,?,?,?,?,?,?)',(operacion_id,i,anterior['revision']+1,'REINGRESO','Reincorporación solicitada mediante asignación de participantes.',current_user.id,current_user.nombre,db._ahora_utc()))
                conexion.execute('UPDATE participaciones_operacion SET revision=revision+1 WHERE operacion_id=? AND voluntario_id=?',(operacion_id,i))
                auditar(conexion,f'PARTICIPACION_REINCORPORADA:OPERACION={operacion_id}:PERSONA={i}')
            else:
                conexion.execute('INSERT INTO participaciones_operacion(operacion_id,voluntario_id) VALUES (?,?)',(operacion_id,i))
        auditar(conexion,'PARTICIPACION_REGISTRADA');conexion.commit()
    except sqlite3.IntegrityError:
        conexion.rollback();return error('Una participación ya está registrada; no se guardó ninguna.',409)
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
    consulta='SELECT nombre,tipo,entidad,fecha_inicio,fecha_fin,estado,puntaje FROM cursos WHERE fecha_inicio>=? AND fecha_inicio<=?'
    parametros=[desde,hasta]
    for campo,valor in (('tipo',tipo),):
        if valor: consulta+=f' AND {campo}=?';parametros.append(valor)
    conexion=db.obtener_conexion()
    filas=[proyectar_curso(f) for f in conexion.execute(consulta+' ORDER BY fecha_inicio,nombre,id',parametros)]
    if estado: filas=[f for f in filas if f['estado']==estado]
    archivo=generar_pdf_cursos(filas,desde,hasta,tipo,estado)
    auditar(conexion,'REPORTE_CURSOS_GENERADO');conexion.commit()
    respuesta=send_file(archivo,mimetype='application/pdf',as_attachment=False,download_name=f'cursos-{desde}-{hasta}.pdf',max_age=0)
    respuesta.headers['Cache-Control']='private, no-store'
    return respuesta
