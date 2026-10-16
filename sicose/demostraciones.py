"""Ejercicios aritméticos de ejemplo, separados de la psicometría oficial."""
import json
import secrets
import sqlite3
from flask import Blueprint, jsonify, request, render_template
from flask_login import current_user
from . import db
from .permissions import role_required
from .modelo_anual import periodo, persona

demo_bp = Blueprint('demostraciones', __name__)
CLAVES = ('PSICOMETRICA_1', 'PSICOMETRICA_2')


@demo_bp.after_request
def privada(r):
    r.headers['Cache-Control'] = 'private, no-store'
    return r


def disponible(c, pid, clave, uid):
    periodo(c, pid, True); persona(c, pid, uid)
    if clave not in CLAVES or not c.execute('SELECT 1 FROM activaciones_demo WHERE periodo_id=? AND clave=? AND activa=1', (pid, clave)).fetchone():
        raise ValueError('El ejercicio de ejemplo no está activo.')


@demo_bp.get('/mis-evaluaciones/anual')
@role_required('INSTRUCTOR_VOLUNTARIO')
def pagina():
    return render_template('evaluaciones_anuales_propias.html', titulo_pagina='Mis evaluaciones', nav_activo='tabla_evaluaciones', indicadores=[], periodo_actual=db.periodo_actual(), descripcion='Evaluaciones pendientes y ejercicios de ejemplo de la Gestión activa.')


@demo_bp.get('/api/modelo-anual/propio')
@role_required('INSTRUCTOR_VOLUNTARIO')
def propio():
    if request.args: return jsonify(error='La consulta es propia y no admite seleccionar otra persona.'),400
    c = db.obtener_conexion(); c.execute('BEGIN')
    filas = c.execute("SELECT p.id,p.nombre FROM periodos p JOIN personas_modelo_anual a ON a.periodo_id=p.id WHERE a.voluntario_id=? AND p.estado='ACTIVO' AND NOT EXISTS(SELECT 1 FROM bajas_gestion b WHERE b.periodo_id=p.id)", (current_user.id,)).fetchall()
    from .tabla_evaluaciones import habilitada
    salida = []
    for p in filas:
        items = []
        for clave, nombre in [('FISICA_1','Física 1'), ('FISICA_2','Física 2'), ('ACADEMICA','Académica')]:
            if habilitada(c, current_user.id, p['id'], clave):
                if clave == 'ACADEMICA':
                    finalizada = c.execute("SELECT 1 FROM participaciones_curso f JOIN periodos p ON p.id=? WHERE f.voluntario_id=? AND f.estado='Finalizado' AND f.fecha_finalizacion BETWEEN p.fecha_inicio AND p.fecha_fin", (p['id'], current_user.id)).fetchone() or c.execute('SELECT 1 FROM notas_operacion_anual WHERE periodo_id=? AND voluntario_id=?', (p['id'], current_user.id)).fetchone()
                else:
                    n = c.execute('SELECT origen FROM notas_modelo_anual WHERE periodo_id=? AND voluntario_id=? AND fuente=? ORDER BY id DESC LIMIT 1', (p['id'], current_user.id, clave)).fetchone()
                    finalizada = n and n[0] != 'CERO_INICIAL'
                items.append(dict(clave=clave, nombre=nombre, estado='Registrada' if finalizada else 'Pendiente', ejemplo=False))
        for clave in CLAVES:
            if c.execute('SELECT 1 FROM activaciones_demo WHERE periodo_id=? AND clave=? AND activa=1', (p['id'], clave)).fetchone():
                intento = c.execute('SELECT finalizada_en FROM intentos_demo WHERE periodo_id=? AND voluntario_id=? AND clave=?', (p['id'], current_user.id, clave)).fetchone()
                items.append(dict(clave=clave, nombre=clave.replace('_', ' ').title() + ' · Ejemplo aritmético', estado='Finalizado' if intento and intento[0] else 'Pendiente', ejemplo=True))
        salida.append(dict(id=p['id'], nombre=p['nombre'], evaluaciones=items))
    c.commit(); return jsonify(gestiones=salida)


@demo_bp.get('/api/modelo-anual/gestiones/<int:pid>/ejemplos')
@demo_bp.patch('/api/modelo-anual/gestiones/<int:pid>/ejemplos/<clave>')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
def administracion(pid, clave=None):
    c = db.obtener_conexion()
    try:
        if request.method == 'GET':
            periodo(c, pid)
            return jsonify(activaciones=[dict(clave=k, activa=bool((c.execute('SELECT activa FROM activaciones_demo WHERE periodo_id=? AND clave=?', (pid,k)).fetchone() or [0])[0])) for k in CLAVES], resultados=[dict(r) for r in c.execute('SELECT voluntario_id,clave,puntaje,finalizada_en FROM intentos_demo WHERE periodo_id=? AND finalizada_en IS NOT NULL', (pid,))])
        d = request.get_json(silent=True)
        if clave not in CLAVES or not isinstance(d,dict) or set(d) != {'activa','anterior'} or type(d['activa']) is not bool or type(d['anterior']) is not bool:
            raise ValueError('Activación y estado anterior requeridos.')
        c.execute('BEGIN IMMEDIATE'); periodo(c,pid,True)
        anterior = bool((c.execute('SELECT activa FROM activaciones_demo WHERE periodo_id=? AND clave=?', (pid,clave)).fetchone() or [0])[0])
        if anterior != d['anterior']: raise ValueError('La activación cambió. Recarga.')
        c.execute('INSERT INTO activaciones_demo VALUES (?,?,?,?,?) ON CONFLICT(periodo_id,clave) DO UPDATE SET activa=excluded.activa,actor_id=excluded.actor_id,modificada_en=excluded.modificada_en', (pid,clave,int(d['activa']),current_user.id,db._ahora_utc()))
        db.registrar_auditoria(c,current_user.id,f'EJEMPLO_ARITMETICO:{pid}:{clave}:{int(d["activa"])}','EXITOSO'); c.commit()
        return jsonify(ok=True)
    except LookupError as e: c.rollback(); return jsonify(error=str(e)),404
    except (ValueError,sqlite3.IntegrityError,sqlite3.OperationalError) as e:
        c.rollback(); return jsonify(error=str(e) if isinstance(e,ValueError) else 'Conflicto concurrente. Recarga.'),409


@demo_bp.post('/api/modelo-anual/gestiones/<int:pid>/ejemplo/<clave>')
@demo_bp.post('/api/modelo-anual/gestiones/<int:pid>/ejemplo/<clave>/finalizar')
@role_required('INSTRUCTOR_VOLUNTARIO')
def ejercicio(pid, clave):
    c = db.obtener_conexion()
    try:
        c.execute('BEGIN IMMEDIATE'); disponible(c,pid,clave,current_user.id)
        fila = c.execute('SELECT * FROM intentos_demo WHERE periodo_id=? AND voluntario_id=? AND clave=?', (pid,current_user.id,clave)).fetchone()
        if request.path.endswith('/finalizar'):
            d = request.get_json(silent=True)
            if not fila or fila['finalizada_en']: raise ValueError('No hay un intento abierto. Recarga.')
            if not isinstance(d,dict) or set(d) != {'intento_id','respuestas'} or type(d['intento_id']) is not int or d['intento_id'] != fila['id'] or not isinstance(d['respuestas'],list) or len(d['respuestas']) != 2 or any(type(v) is not int or not -1000 <= v <= 1000 for v in d['respuestas']):
                raise ValueError('Responde las dos preguntas con números enteros.')
            preguntas = json.loads(fila['preguntas_json'])
            puntaje = sum(50 for q,a in zip(preguntas,d['respuestas']) if a == (q['a'] + q['b'] if q['operador']=='+' else q['a']-q['b']))
            c.execute('UPDATE intentos_demo SET puntaje=?,finalizada_en=? WHERE id=? AND finalizada_en IS NULL', (puntaje,db._ahora_utc(),fila['id']))
            db.registrar_auditoria(c,current_user.id,'EJEMPLO_ARITMETICO_FINALIZADO','EXITOSO'); c.commit()
            return jsonify(ok=True,puntaje_ejemplo=puntaje,oficial=False)
        if request.get_json(silent=True) != {}: raise ValueError('El inicio no admite parámetros adicionales.')
        if fila and fila['finalizada_en']: raise ValueError('El ejemplo ya fue finalizado.')
        if fila is None:
            preguntas = [dict(a=secrets.randbelow(20)+1,b=secrets.randbelow(20)+1,operador=secrets.choice(('+','-')),valor=50) for _ in range(2)]
            iid = c.execute('INSERT INTO intentos_demo(periodo_id,voluntario_id,clave,preguntas_json,iniciada_en) VALUES (?,?,?,?,?)', (pid,current_user.id,clave,json.dumps(preguntas),db._ahora_utc())).lastrowid
        else: preguntas=json.loads(fila['preguntas_json']); iid=fila['id']
        c.commit(); return jsonify(intento_id=iid,preguntas=preguntas,oficial=False)
    except LookupError as e: c.rollback(); return jsonify(error=str(e)),404
    except (ValueError,sqlite3.IntegrityError,sqlite3.OperationalError) as e:
        c.rollback(); return jsonify(error=str(e) if isinstance(e,ValueError) else 'Conflicto concurrente. Recarga.'),409
