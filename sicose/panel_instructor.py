"""Consultas personales por intervalo de Gestión; notas solo publicadas."""
from datetime import date
from flask import abort, make_response, render_template, request
from flask_login import current_user
from . import db


def gestiones(c):
    return [dict(p) for p in c.execute("""SELECT id,nombre,estado,fecha_inicio,fecha_fin FROM periodos
        WHERE estado IN ('ACTIVO','CERRADO') AND NOT EXISTS
        (SELECT 1 FROM bajas_gestion b WHERE b.periodo_id=periodos.id)
        ORDER BY (estado='ACTIVO') DESC,fecha_inicio DESC,id DESC""")]


def seleccion(c):
    opciones = gestiones(c)
    if set(request.args) - {'periodo_id'} or len(request.args.getlist('periodo_id')) > 1:
        abort(400, 'Selecciona únicamente una Gestión.')
    pid = request.args.get('periodo_id')
    if pid is None:
        return opciones, opciones[0] if opciones else None
    elegida = next((p for p in opciones if str(p['id']) == pid), None)
    if elegida is None:
        abort(400, 'Gestión no disponible.')
    return opciones, elegida


def estados(c, uid, p):
    from .modelo_anual import es_modelo
    from .tabla_evaluaciones import habilitada, evaluaciones_persona
    if not p:
        return []
    if not es_modelo(c, p['id']):
        filas = evaluaciones_persona(c, uid, p['id'])
        resultado = []
        for claves, nombre in [(('FISICA_1',), 'Física 1'), (('FISICA_2',), 'Física 2'), (('ACADEMICA',), 'Académica'), (('DESEMPENO_JEFE','DESEMPENO_COMANDANTE'), 'Desempeño')]:
            fuentes = [e for e in filas if e['clave'] in claves]
            if len(fuentes) == len(claves) and all(habilitada(c, uid, p['id'], k) for k in claves):
                resultado.append(dict(nombre=nombre, completa=all(e['estado'] in ('FINALIZADA','NO_CUMPLIDA') for e in fuentes)))
        return resultado
    if not c.execute('SELECT 1 FROM personas_modelo_anual WHERE periodo_id=? AND voluntario_id=?', (p['id'], uid)).fetchone():
        return []
    resultado = []
    for claves, nombre in [(('FISICA_1',), 'Física 1'), (('FISICA_2',), 'Física 2'), (('ACADEMICA',), 'Académica'), (('DESEMPENO_JEFE','DESEMPENO_COMANDANTE'), 'Desempeño')]:
        if not all(habilitada(c, uid, p['id'], k) for k in claves):
            continue
        if claves == ('ACADEMICA',):
            completa = c.execute("SELECT 1 FROM participaciones_curso WHERE voluntario_id=? AND estado='Finalizado' AND fecha_finalizacion BETWEEN ? AND ?", (uid,p['fecha_inicio'],p['fecha_fin'])).fetchone() or c.execute("""SELECT 1 FROM notas_operacion_anual n JOIN operaciones o ON o.id=n.operacion_id
                WHERE n.periodo_id=? AND n.voluntario_id=? AND o.fecha_inicio BETWEEN ? AND ?
                AND NOT EXISTS(SELECT 1 FROM retiros_operacion_vigentes r WHERE r.operacion_id=n.operacion_id AND r.voluntario_id=n.voluntario_id)""", (p['id'],uid,p['fecha_inicio'],p['fecha_fin'])).fetchone()
        else:
            notas = [c.execute('SELECT origen FROM notas_modelo_anual WHERE periodo_id=? AND voluntario_id=? AND fuente=? ORDER BY id DESC LIMIT 1', (p['id'],uid,k)).fetchone() for k in claves]
            completa = all(n and n['origen'] != 'CERO_INICIAL' for n in notas)
        resultado.append(dict(nombre=nombre, completa=bool(completa)))
    return resultado


def cursos(c, uid, p):
    if not p:
        return []
    from .publicaciones_5b import proyeccion
    publicacion = proyeccion(c,uid,p['id'])
    publicados = {f['participacion_id']:f for f in (publicacion or {}).get('academica',{}).get('cursos',[])} if publicacion and publicacion['academica'] else {}
    filas = c.execute("""SELECT id,nombre_curso,entidad_curso,tipo_curso,inicio_curso,fin_curso,estado,fecha_finalizacion
        FROM participaciones_curso WHERE voluntario_id=? AND
        ((inicio_curso<=? AND COALESCE(fin_curso,inicio_curso)>=?) OR fecha_finalizacion BETWEEN ? AND ?)
        ORDER BY inicio_curso DESC,id DESC""", (uid,p['fecha_fin'],p['fecha_inicio'],p['fecha_inicio'],p['fecha_fin']))
    return [{**dict(f),'puntaje_publicado':publicados.get(f['id'],{}).get('puntaje')} for f in filas]


def pagina(tipo):
    c = db.obtener_conexion()
    c.execute('BEGIN')
    opciones, p = seleccion(c)
    uid = current_user.id
    datos = dict(gestiones=opciones, gestion=p, tipo=tipo)
    if tipo == 'cursos':
        datos['cursos'] = cursos(c,uid,p)
    elif tipo == 'evaluaciones':
        from .publicaciones_5b import proyeccion
        datos['publicacion'] = proyeccion(c,uid,p['id']) if p else None
    elif tipo == 'asistencias':
        from .asistencias import PROYECCION, ESTADOS
        filas = c.execute(f'SELECT a.fecha,{PROYECCION} AS estado FROM asistencias a WHERE a.voluntario_id=? AND a.fecha BETWEEN ? AND ?', (uid,p['fecha_inicio'],p['fecha_fin'])).fetchall() if p else []
        meses = []
        if p:
            mes = date.fromisoformat(p['fecha_inicio']).replace(day=1)
            fin = date.fromisoformat(p['fecha_fin'])
            while mes <= fin:
                meses.append(mes.strftime('%Y-%m'))
                if mes.year == 9999 and mes.month == 12:
                    break
                mes = date(mes.year + (mes.month == 12), mes.month % 12 + 1, 1)
        graficos = []
        for estado, nombre in zip(ESTADOS, ('Asiste','Atraso','Permiso','Falta')):
            valores = [sum(f['fecha'].startswith(m) and f['estado']==estado for f in filas) for m in meses]
            maximo = max([1,*valores])
            graficos.append(dict(titulo=nombre, filas=[dict(nombre=m,valor=v,alto=round(v/maximo*130)) for m,v in zip(meses,valores)]))
        datos['graficos'] = graficos
    c.commit()
    respuesta = make_response(render_template('panel_instructor_consulta.html', **datos,
        titulo_pagina={'cursos':'Mis cursos','evaluaciones':'Mis evaluaciones','asistencias':'Mis asistencias'}[tipo],
        nav_activo={'cursos':'capacitaciones','evaluaciones':'tabla_evaluaciones','asistencias':'asistencias'}[tipo],
        indicadores=[],periodo_actual=db.periodo_actual(),descripcion='Consulta tu información personal de la Gestión seleccionada.'))
    respuesta.headers['Cache-Control'] = 'private, no-store'
    return respuesta
