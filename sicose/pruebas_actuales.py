"""Circuito GSE/Mini-IPIP por Gestión, revisión humana y privacidad propia."""
import json
from flask import Blueprint, jsonify, request
from flask_login import current_user
from . import db
from .modelo_anual import periodo, persona, serializar
from .permissions import role_required
from .psicometria import transaccion
from .instrumentos_actuales import CATALOGO, formulario, firma, validar, puntuar

pruebas_bp = Blueprint('pruebas_actuales', __name__)


@pruebas_bp.after_request
def privada(r):
    r.headers['Cache-Control'] = 'private, no-store'
    return r


def estado(c, pid, clave):
    f = c.execute('SELECT activa,revision FROM activaciones_pruebas WHERE periodo_id=? AND clave=?', (pid, clave)).fetchone()
    revisiones = [dict(r) for r in c.execute('SELECT rol,actor_nombre,registrada_en FROM revisiones_pruebas WHERE periodo_id=? AND clave=? AND firma_formulario=? ORDER BY id', (pid, clave, firma(clave)))]
    return dict(activa=bool(f['activa']) if f else False, revision=f['revision'] if f else 0,
                revisada={r['rol'] for r in revisiones} == {'ADMINISTRADOR', 'JEFE_PERSONAL'}, revisiones=revisiones)


def intento(c, pid, uid, clave):
    return c.execute('SELECT * FROM intentos_pruebas WHERE periodo_id=? AND voluntario_id=? AND clave=?', (pid, uid, clave)).fetchone()


def resultados_persona(c, pid, uid):
    salida = []
    for k, f in CATALOGO.items():
        i = intento(c, pid, uid, k)
        r = dict(clave=k, nombre=f['nombre'], estado='Completada' if i and i['finalizada_en'] else 'Pendiente')
        if i and i['finalizada_en']:
            r.update(version=i['version'], firma_formulario=i['firma_formulario'], finalizada_en=i['finalizada_en'],
                formulario=json.loads(i['formulario_json']), respuestas=json.loads(i['respuestas_json']), subescalas=json.loads(i['resultados_json']))
        salida.append(r)
    return salida


@pruebas_bp.get('/api/modelo-anual/gestiones/<int:pid>/pruebas')
@pruebas_bp.patch('/api/modelo-anual/gestiones/<int:pid>/pruebas/<clave>')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
@transaccion
def gestionar(c, pid, clave=None):
    p = periodo(c, pid)
    if request.method == 'GET':
        pruebas = [dict(clave=k, nombre=f['nombre'], firma_formulario=firma(k), formulario=formulario(k), **estado(c, pid, k)) for k, f in CATALOGO.items()]
        personas = []
        for u in c.execute('SELECT u.id,u.nombre_completo FROM personas_modelo_anual a JOIN usuarios u ON u.id=a.voluntario_id WHERE a.periodo_id=? ORDER BY u.nombre_completo,u.id', (pid,)):
            personas.append(dict(id=u['id'], nombre=u['nombre_completo'], pruebas={k: 'Completada' if (i := intento(c, pid, u['id'], k)) and i['finalizada_en'] else 'Pendiente' for k in CATALOGO}))
        return jsonify(pruebas=pruebas, personas=personas, editable=p['estado']=='ACTIVO' and not p['retirada'])
    periodo(c, pid, True)
    if clave not in CATALOGO:
        raise LookupError('Prueba no encontrada.')
    d = request.get_json(silent=True)
    if not isinstance(d, dict) or set(d) != {'activa', 'revision'} or type(d['activa']) is not bool or type(d['revision']) is not int:
        raise ValueError('Activación y revisión requeridas.')
    a = estado(c, pid, clave)
    if a['revision'] != d['revision']:
        raise ValueError('La habilitación cambió. Recarga.')
    if d['activa'] and not a['revisada']:
        raise ValueError('Administrador y Jefe de Personal deben registrar la revisión de esta versión antes de habilitarla.')
    if a['activa'] != d['activa']:
        ahora, rev = db._ahora_utc(), a['revision']+1
        c.execute('INSERT INTO activaciones_pruebas VALUES (?,?,?,?,?,?) ON CONFLICT(periodo_id,clave) DO UPDATE SET activa=excluded.activa,revision=excluded.revision,actor_id=excluded.actor_id,modificada_en=excluded.modificada_en', (pid, clave, int(d['activa']), rev, current_user.id, ahora))
        c.execute('INSERT INTO historial_activaciones_pruebas(periodo_id,clave,activa,revision,actor_id,registrada_en) VALUES (?,?,?,?,?,?)', (pid, clave, int(d['activa']), rev, current_user.id, ahora))
        db.registrar_auditoria(c, current_user.id, f'PRUEBA_ACTIVACION:{pid}:{clave}:{int(d["activa"])}', 'EXITOSO')
    return jsonify(ok=True)


@pruebas_bp.post('/api/modelo-anual/gestiones/<int:pid>/pruebas/<clave>/revision')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
@transaccion
def revisar(c, pid, clave):
    periodo(c, pid, True)
    if clave not in CATALOGO:
        raise LookupError('Prueba no encontrada.')
    d = request.get_json(silent=True)
    if not isinstance(d, dict) or set(d) != {'firma_formulario', 'confirmar', 'observacion'} or d['confirmar'] is not True:
        raise ValueError('Confirma la revisión del formulario, su puntuación y política de conservación por Gestión.')
    if d['firma_formulario'] != firma(clave):
        raise ValueError('El formulario cambió. Revisa la versión vigente.')
    if not isinstance(d['observacion'], str) or not 1 <= len(d['observacion'].strip()) <= 2000:
        raise ValueError('Registra la constancia de revisión, máximo 2000 caracteres.')
    existente = c.execute('SELECT id FROM revisiones_pruebas WHERE periodo_id=? AND clave=? AND firma_formulario=? AND rol=?', (pid, clave, firma(clave), current_user.rol)).fetchone()
    if not existente:
        c.execute('INSERT INTO revisiones_pruebas(periodo_id,clave,firma_formulario,formulario_json,observacion,actor_id,actor_nombre,rol,registrada_en) VALUES (?,?,?,?,?,?,?,?,?)', (pid, clave, firma(clave), serializar(formulario(clave)), d['observacion'].strip(), current_user.id, current_user.nombre, current_user.rol, db._ahora_utc()))
        db.registrar_auditoria(c, current_user.id, f'PRUEBA_REVISION:{pid}:{clave}', 'EXITOSO')
    return jsonify(ok=True)


@pruebas_bp.get('/api/pruebas/propias')
@role_required('INSTRUCTOR_VOLUNTARIO')
@transaccion
def propias(c):
    if request.args:
        raise ValueError('La consulta es exclusivamente propia.')
    salida = []
    for p in c.execute("SELECT p.id,p.nombre,p.estado FROM periodos p JOIN personas_modelo_anual a ON a.periodo_id=p.id WHERE a.voluntario_id=? AND NOT EXISTS(SELECT 1 FROM bajas_gestion b WHERE b.periodo_id=p.id)", (current_user.id,)).fetchall():
        for k, f in CATALOGO.items():
            a, i = estado(c, p['id'], k), intento(c, p['id'], current_user.id, k)
            if a['activa'] or (i and i['finalizada_en']):
                salida.append(dict(periodo_id=p['id'], gestion=p['nombre'], clave=k, nombre=f['nombre'],
                    estado='Completada' if i and i['finalizada_en'] else 'Pendiente',
                    disponible=p['estado']=='ACTIVO' and a['activa'] and a['revisada'] and not (i and i['finalizada_en'])))
    return jsonify(pruebas=salida)


@pruebas_bp.get('/api/modelo-anual/gestiones/<int:pid>/pruebas/<clave>/propia')
@pruebas_bp.put('/api/modelo-anual/gestiones/<int:pid>/pruebas/<clave>/propia')
@pruebas_bp.post('/api/modelo-anual/gestiones/<int:pid>/pruebas/<clave>/finalizar')
@role_required('INSTRUCTOR_VOLUNTARIO')
@transaccion
def responder(c, pid, clave):
    periodo(c, pid)
    persona(c, pid, current_user.id)
    if request.args:
        raise ValueError('La consulta es exclusivamente propia.')
    if clave not in CATALOGO:
        raise LookupError('Prueba no encontrada.')
    i = intento(c, pid, current_user.id, clave)
    if i and i['finalizada_en']:
        if request.method == 'GET':
            return jsonify(estado='Completada')
        raise ValueError('La prueba ya está completada; no admite nuevos intentos.')
    periodo(c, pid, True)
    a = estado(c, pid, clave)
    if not a['activa'] or not a['revisada']:
        raise ValueError('La prueba no está habilitada o su revisión está pendiente.')
    if i and i['firma_formulario'] != firma(clave):
        raise ValueError('La versión cambió; el intento conservado requiere revisión.')
    f = formulario(clave)
    if request.method == 'GET':
        return jsonify(estado='Pendiente', formulario=f, revision=i['revision'] if i else 0,
                       respuestas=json.loads(i['respuestas_json']) if i else [None]*len(f['items']))
    d = request.get_json(silent=True)
    if not isinstance(d, dict) or set(d) != {'respuestas', 'revision'} or type(d['revision']) is not int:
        raise ValueError('Respuestas y revisión requeridas; no se aceptan notas ni otra persona.')
    if d['revision'] != (i['revision'] if i else 0):
        raise ValueError('El avance cambió. Recarga.')
    final = request.method == 'POST'
    validar(clave, d['respuestas'], final)
    ahora = db._ahora_utc()
    resultados = serializar(puntuar(clave, d['respuestas'])) if final else None
    if i:
        c.execute('UPDATE intentos_pruebas SET respuestas_json=?,resultados_json=?,revision=revision+1,guardada_en=?,finalizada_en=? WHERE id=?', (serializar(d['respuestas']), resultados, ahora, ahora if final else None, i['id']))
    else:
        c.execute('INSERT INTO intentos_pruebas(periodo_id,voluntario_id,clave,version,firma_formulario,formulario_json,respuestas_json,resultados_json,revision,iniciada_en,guardada_en,finalizada_en) VALUES (?,?,?,?,?,?,?,?,1,?,?,?)', (pid, current_user.id, clave, f['version'], firma(clave), serializar(f), serializar(d['respuestas']), resultados, ahora, ahora, ahora if final else None))
    db.registrar_auditoria(c, current_user.id, f'PRUEBA:{"COMPLETADA" if final else "AVANCE"}:{pid}:{clave}', 'EXITOSO')
    return jsonify(estado='Completada' if final else 'Avance guardado', revision=d['revision']+1)


@pruebas_bp.get('/api/modelo-anual/gestiones/<int:pid>/personas/<int:uid>/pruebas')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
@transaccion
def resultados(c, pid, uid):
    periodo(c, pid)
    if not c.execute('SELECT 1 FROM personas_modelo_anual WHERE periodo_id=? AND voluntario_id=?', (pid, uid)).fetchone():
        raise LookupError('Persona no inscrita en esta Gestión.')
    db.registrar_auditoria(c, current_user.id, f'PRUEBAS_CONSULTA:{pid}:{uid}', 'EXITOSO')
    return jsonify(pruebas=resultados_persona(c, pid, uid))
