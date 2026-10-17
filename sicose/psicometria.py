"""Circuito restringido, sin reactivos oficiales cargados ni inferencia sobre personas."""
import hashlib
import json
import sqlite3
from functools import wraps
from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user
from . import db
from .modelo_anual import periodo, persona, serializar
from .permissions import role_required
from .psicometria_puntuacion import CATALOGO, puntuar, validar_respuestas

psicometria_bp = Blueprint('psicometria', __name__)


@psicometria_bp.after_request
def privada(r):
    r.headers['Cache-Control'] = 'private, no-store'
    return r


def transaccion(f):
    @wraps(f)
    def ejecutar(*args, **kwargs):
        c = db.obtener_conexion()
        try:
            c.execute('BEGIN IMMEDIATE' if request.method != 'GET' else 'BEGIN')
            r = f(c, *args, **kwargs)
            c.commit()
            return r
        except LookupError as e:
            c.rollback()
            return jsonify(error=str(e)), 404
        except (ValueError, sqlite3.IntegrityError, sqlite3.OperationalError) as e:
            c.rollback()
            return jsonify(error=str(e) if isinstance(e, ValueError) else 'Conflicto de revisión. Recarga.'), 409
    return ejecutar


def formulario_revisado(clave):
    """Configuración de despliegue, sin API que permita autoaprobar instrumentos.

    El expediente firmado es evidencia humana externa, no un booleano de entorno.
    La firma enlaza instrucciones, opciones, orden, versión y algoritmo revisados.
    """
    if clave not in CATALOGO:
        raise LookupError('Prueba no encontrada.')
    revisiones = current_app.config.get('PSICOMETRIA_REVISIONES', {})
    if not isinstance(revisiones, dict):
        return None
    m = revisiones.get(clave)
    if not isinstance(m, dict):
        return None
    form, revision = m.get('formulario'), m.get('revision')
    if not isinstance(form, dict) or not isinstance(revision, dict):
        return None
    ficha = CATALOGO[clave]
    if form.get('version') != ficha['version'] or form.get('algoritmo') != ficha['algoritmo']:
        return None
    items = form.get('items')
    if (not isinstance(items, list) or len(items) != ficha['cantidad'] or
            not isinstance(form.get('instrucciones'), str) or not form['instrucciones'].strip()):
        return None
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get('texto'), str) or not item['texto'].strip():
            return None
        opciones = item.get('opciones')
        if not isinstance(opciones, list) or len(opciones) != ficha['maximo_respuesta']+1 or any(not isinstance(v, str) or not v.strip() for v in opciones):
            return None
    firma = hashlib.sha256(serializar(form).encode()).hexdigest()
    campos = ('profesional', 'referencia_profesional', 'aprobacion_institucional', 'fecha',
              'retencion', 'protocolo_confidencialidad')
    if clave == 'CBI':
        campos += ('aplicabilidad_19_items_cbi',)
    if any(not isinstance(revision.get(k), str) or not revision[k].strip() for k in campos):
        return None
    if revision.get('firma_formulario') != firma or revision.get('devolucion_instructor') != 'SOLO_ESTADO':
        return None
    return form, firma


def estado(c, pid, clave):
    fila = c.execute('SELECT activa,revision FROM activaciones_psicometria WHERE periodo_id=? AND clave=?', (pid, clave)).fetchone()
    return {'activa': bool(fila['activa']) if fila else False, 'revision': fila['revision'] if fila else 0}


def intento(c, pid, uid, clave):
    return c.execute('SELECT * FROM intentos_psicometria WHERE periodo_id=? AND voluntario_id=? AND clave=?', (pid, uid, clave)).fetchone()


@psicometria_bp.get('/api/modelo-anual/gestiones/<int:pid>/psicometria')
@psicometria_bp.patch('/api/modelo-anual/gestiones/<int:pid>/psicometria/<clave>')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
@transaccion
def gestionar(c, pid, clave=None):
    p = periodo(c, pid)
    if request.method == 'GET':
        return jsonify(pruebas=[dict(clave=k, nombre=v['nombre'], **estado(c, pid, k),
            revisada=bool(formulario_revisado(k)), bloqueo=None if formulario_revisado(k) else
            'Pendiente: versión y revisión profesional/institucional, privacidad y retención.') for k, v in CATALOGO.items()],
            resultados=[{'voluntario_id': r['voluntario_id'], 'clave': r['clave'],
                         'estado': 'Completada' if r['finalizada_en'] else 'Pendiente'}
                        for r in c.execute('SELECT voluntario_id,clave,finalizada_en FROM intentos_psicometria WHERE periodo_id=?', (pid,))],
            personas=[{'id': u['id'], 'nombre': u['nombre_completo'],
                       'pruebas': {k: 'Completada' if ((i := intento(c, pid, u['id'], k)) and i['finalizada_en']) else 'Pendiente' for k in CATALOGO}}
                      for u in c.execute('SELECT u.id,u.nombre_completo FROM personas_modelo_anual a JOIN usuarios u ON u.id=a.voluntario_id WHERE a.periodo_id=? ORDER BY u.nombre_completo,u.id', (pid,)).fetchall()])
    if clave not in CATALOGO:
        raise LookupError('Prueba no encontrada.')
    periodo(c, pid, True)
    d = request.get_json(silent=True)
    if not isinstance(d, dict) or set(d) != {'activa', 'revision'} or type(d['activa']) is not bool or type(d['revision']) is not int:
        raise ValueError('Activación y revisión requeridas.')
    anterior = estado(c, pid, clave)
    if d['revision'] != anterior['revision']:
        raise ValueError('La activación cambió. Recarga.')
    if d['activa'] and not formulario_revisado(clave):
        raise ValueError('Prueba bloqueada: falta expediente profesional/institucional y política de conservación aprobados.')
    if anterior['activa'] == d['activa']:
        return jsonify(ok=True)
    rev, ahora = anterior['revision']+1, db._ahora_utc()
    c.execute('INSERT INTO activaciones_psicometria VALUES (?,?,?,?,?,?) ON CONFLICT(periodo_id,clave) DO UPDATE SET activa=excluded.activa,revision=excluded.revision,actor_id=excluded.actor_id,modificada_en=excluded.modificada_en',
              (pid, clave, int(d['activa']), rev, current_user.id, ahora))
    c.execute('INSERT INTO historial_activaciones_psicometria(periodo_id,clave,activa,revision,actor_id,registrada_en) VALUES (?,?,?,?,?,?)', (pid, clave, int(d['activa']), rev, current_user.id, ahora))
    db.registrar_auditoria(c, current_user.id, f'PSICOMETRIA_ACTIVACION:{pid}:{clave}:{int(d["activa"])}', 'EXITOSO')
    return jsonify(ok=True)


@psicometria_bp.get('/api/psicometria/propia')
@role_required('INSTRUCTOR_VOLUNTARIO')
@transaccion
def propia(c):
    if request.args:
        raise ValueError('La consulta es exclusivamente propia.')
    salida = []
    for p in c.execute("SELECT p.id,p.nombre FROM periodos p JOIN personas_modelo_anual a ON a.periodo_id=p.id WHERE a.voluntario_id=? AND p.estado='ACTIVO' AND NOT EXISTS(SELECT 1 FROM bajas_gestion b WHERE b.periodo_id=p.id)", (current_user.id,)).fetchall():
        for k, ficha in CATALOGO.items():
            a, i = estado(c, p['id'], k), intento(c, p['id'], current_user.id, k)
            if a['activa'] or (i and i['finalizada_en']):
                salida.append({'periodo_id': p['id'], 'gestion': p['nombre'], 'clave': k, 'nombre': ficha['nombre'],
                    'estado': 'Completada' if i and i['finalizada_en'] else 'Pendiente',
                    'disponible': bool(a['activa'] and formulario_revisado(k) and not (i and i['finalizada_en']))})
    return jsonify(pruebas=salida)


@psicometria_bp.get('/api/modelo-anual/gestiones/<int:pid>/psicometria/<clave>/propia')
@psicometria_bp.put('/api/modelo-anual/gestiones/<int:pid>/psicometria/<clave>/propia')
@psicometria_bp.post('/api/modelo-anual/gestiones/<int:pid>/psicometria/<clave>/finalizar')
@role_required('INSTRUCTOR_VOLUNTARIO')
@transaccion
def responder(c, pid, clave):
    if request.args:
        raise ValueError('La consulta es exclusivamente propia.')
    periodo(c, pid, True)
    persona(c, pid, current_user.id)
    if clave not in CATALOGO:
        raise LookupError('Prueba no encontrada.')
    i = intento(c, pid, current_user.id, clave)
    if i and i['finalizada_en']:
        if request.method == 'GET':
            return jsonify(estado='Completada')
        raise ValueError('La prueba ya está completada; no admite nuevos intentos.')
    revisado = formulario_revisado(clave)
    if not estado(c, pid, clave)['activa'] or not revisado:
        raise ValueError('La prueba no está habilitada o su revisión está pendiente.')
    form, firma = revisado
    if i and i['firma_formulario'] != firma:
        raise ValueError('La versión cambió; requiere revisión profesional del intento conservado.')
    if request.method == 'GET':
        return jsonify(estado='Pendiente', formulario=form, revision=i['revision'] if i else 0,
                       respuestas=json.loads(i['respuestas_json']) if i else [None]*CATALOGO[clave]['cantidad'])
    d = request.get_json(silent=True)
    if not isinstance(d, dict) or set(d) != {'respuestas', 'revision'} or type(d['revision']) is not int:
        raise ValueError('Respuestas y revisión requeridas; no se reciben puntuaciones ni identificadores de persona.')
    if d['revision'] != (i['revision'] if i else 0):
        raise ValueError('El avance cambió. Recarga para evitar sobrescribirlo.')
    final = request.method == 'POST'
    validar_respuestas(clave, d['respuestas'], completa=final)
    ahora = db._ahora_utc()
    resultados = serializar(puntuar(clave, d['respuestas'])) if final else None
    if i:
        c.execute('UPDATE intentos_psicometria SET respuestas_json=?,resultados_json=?,revision=revision+1,guardada_en=?,finalizada_en=? WHERE id=?',
                  (serializar(d['respuestas']), resultados, ahora, ahora if final else None, i['id']))
    else:
        c.execute('INSERT INTO intentos_psicometria(periodo_id,voluntario_id,clave,version,firma_formulario,formulario_json,respuestas_json,resultados_json,revision,iniciada_en,guardada_en,finalizada_en) VALUES (?,?,?,?,?,?,?,?,1,?,?,?)',
                  (pid, current_user.id, clave, form['version'], firma, serializar(form), serializar(d['respuestas']), resultados, ahora, ahora, ahora if final else None))
    db.registrar_auditoria(c, current_user.id, f'PSICOMETRIA:{"COMPLETADA" if final else "AVANCE"}:{pid}:{clave}', 'EXITOSO')
    return jsonify(estado='Completada' if final else 'Avance guardado', revision=d['revision']+1)


@psicometria_bp.get('/api/modelo-anual/gestiones/<int:pid>/personas/<int:uid>/psicometria')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
@transaccion
def resultados(c, pid, uid):
    periodo(c, pid)
    if not c.execute('SELECT 1 FROM personas_modelo_anual WHERE periodo_id=? AND voluntario_id=?', (pid, uid)).fetchone():
        raise LookupError('Persona no inscrita en esta Gestión.')
    salida = []
    for k, ficha in CATALOGO.items():
        i = intento(c, pid, uid, k)
        r = {'clave': k, 'nombre': ficha['nombre'], 'estado': 'Completada' if i and i['finalizada_en'] else 'Pendiente'}
        # Los borradores no se revelan al personal administrativo.
        if i and i['finalizada_en']:
            r.update(version=i['version'], firma_formulario=i['firma_formulario'], finalizada_en=i['finalizada_en'],
                     respuestas=json.loads(i['respuestas_json']), formulario=json.loads(i['formulario_json']), subescalas=json.loads(i['resultados_json']))
        salida.append(r)
    db.registrar_auditoria(c, current_user.id, f'PSICOMETRIA_CONSULTA:{pid}:{uid}', 'EXITOSO')
    return jsonify(pruebas=salida, recomendacion={'estado': 'PENDIENTE_VALIDACION', 'uso_en_personas': False})
