"""Circuito GSE/Mini-IPIP por Gestión, revisión humana y privacidad propia."""
import json
from datetime import date, datetime, timezone, timedelta
from flask import Blueprint, jsonify, request
from flask_login import current_user
from werkzeug.security import check_password_hash
from . import db
from .modelo_anual import periodo, persona, serializar
from .permissions import role_required
from .psicometria import transaccion
from .instrumentos_actuales import CATALOGO, formulario, firma, validar, puntuar

pruebas_bp = Blueprint('pruebas_actuales', __name__)


def tabla_prueba(nombre, clave):
    return ('tlx_' if clave == 'NASATLX' else '') + nombre


def simulacro(c, pid):
    r = c.execute('SELECT * FROM simulacros_tlx WHERE periodo_id=?', (pid,)).fetchone()
    return dict(r) if r else None


def contexto_tlx(c, pid):
    s = simulacro(c, pid)
    if not s:
        raise ValueError('Registra el simulacro común realizado antes de habilitar o responder NASA-TLX.')
    return {k:s[k] for k in ('periodo_id','nombre','fecha','revision')}


@pruebas_bp.after_request
def privada(r):
    r.headers['Cache-Control'] = 'private, no-store'
    return r


def estado(c, pid, clave):
    f = c.execute(f'SELECT activa,revision FROM {tabla_prueba("activaciones_pruebas", clave)} WHERE periodo_id=? AND clave=?', (pid, clave)).fetchone()
    revisiones = [dict(r) for r in c.execute(f'SELECT rol,actor_nombre,registrada_en FROM {tabla_prueba("revisiones_pruebas", clave)} WHERE periodo_id=? AND clave=? AND firma_formulario=? ORDER BY id', (pid, clave, firma(clave)))]
    return dict(activa=bool(f['activa']) if f else False, revision=f['revision'] if f else 0,
                revisada={r['rol'] for r in revisiones} == {'ADMINISTRADOR', 'JEFE_PERSONAL'}, revisiones=revisiones)


def intento(c, pid, uid, clave):
    reinicio = c.execute(f'SELECT id FROM {tabla_prueba("reinicios_pruebas", clave)} WHERE periodo_id=? AND voluntario_id=? AND clave=? ORDER BY id DESC LIMIT 1', (pid, uid, clave)).fetchone()
    if reinicio:
        return c.execute(f'SELECT *,reinicio_id AS ciclo FROM {tabla_prueba("reintentos_pruebas", clave)} WHERE reinicio_id=?', (reinicio['id'],)).fetchone()
    return c.execute(f'SELECT *,0 AS ciclo FROM {tabla_prueba("intentos_pruebas", clave)} WHERE periodo_id=? AND voluntario_id=? AND clave=?', (pid, uid, clave)).fetchone()


def referencia(i):
    return f'{"reintento" if i["ciclo"] else "original"}:{i["id"]}'


def resultados_persona(c, pid, uid):
    salida = []
    for k, f in CATALOGO.items():
        i = intento(c, pid, uid, k)
        r = dict(clave=k, nombre=f['nombre'], estado='Completada' if i and i['finalizada_en'] else 'Pendiente')
        if i and i['finalizada_en']:
            r.update(intento_ref=referencia(i), revision=i['revision'], version=i['version'], firma_formulario=i['firma_formulario'], finalizada_en=i['finalizada_en'],
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
        return jsonify(pruebas=pruebas, personas=personas, simulacro=simulacro(c,pid), editable=p['estado']=='ACTIVO' and not p['retirada'])
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
    if clave == 'NASATLX' and d['activa']:
        contexto_tlx(c,pid)
    if a['activa'] != d['activa']:
        ahora, rev = db._ahora_utc(), a['revision']+1
        c.execute(f'INSERT INTO {tabla_prueba("activaciones_pruebas", clave)} VALUES (?,?,?,?,?,?) ON CONFLICT(periodo_id,clave) DO UPDATE SET activa=excluded.activa,revision=excluded.revision,actor_id=excluded.actor_id,modificada_en=excluded.modificada_en', (pid, clave, int(d['activa']), rev, current_user.id, ahora))
        c.execute(f'INSERT INTO {tabla_prueba("historial_activaciones_pruebas", clave)}(periodo_id,clave,activa,revision,actor_id,registrada_en) VALUES (?,?,?,?,?,?)', (pid, clave, int(d['activa']), rev, current_user.id, ahora))
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
    existente = c.execute(f'SELECT id FROM {tabla_prueba("revisiones_pruebas", clave)} WHERE periodo_id=? AND clave=? AND firma_formulario=? AND rol=?', (pid, clave, firma(clave), current_user.rol)).fetchone()
    if not existente:
        c.execute(f'INSERT INTO {tabla_prueba("revisiones_pruebas", clave)}(periodo_id,clave,firma_formulario,formulario_json,observacion,actor_id,actor_nombre,rol,registrada_en) VALUES (?,?,?,?,?,?,?,?,?)', (pid, clave, firma(clave), serializar(formulario(clave)), d['observacion'].strip(), current_user.id, current_user.nombre, current_user.rol, db._ahora_utc()))
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
    if clave == 'NASATLX':
        f['simulacro'] = contexto_tlx(c,pid)
    if request.method == 'GET':
        return jsonify(estado='Pendiente', formulario=f, revision=i['revision'] if i else 0,
                       ciclo=i['ciclo'] if i else 0,
                       respuestas=json.loads(i['respuestas_json']) if i else [None]*len(f['items']))
    d = request.get_json(silent=True)
    campos = {'respuestas','revision'}
    opcionales = {'ciclo'} | ({'confirmar_simulacro'} if clave=='NASATLX' else set())
    if not isinstance(d, dict) or not campos <= set(d) or not set(d) <= campos|opcionales or type(d['revision']) is not int:
        raise ValueError('Respuestas y revisión requeridas; no se aceptan notas ni otra persona.')
    if type(d.get('ciclo', 0)) is not int or d.get('ciclo', 0) != (i['ciclo'] if i else 0):
        raise ValueError('La prueba fue reiniciada. Cierra el formulario y vuelve a abrirla.')
    if d['revision'] != (i['revision'] if i else 0):
        raise ValueError('El avance cambió. Recarga.')
    final = request.method == 'POST'
    if clave == 'NASATLX' and final and d.get('confirmar_simulacro') is not True:
        raise ValueError('Confirma que participaste y finalizaste el simulacro común indicado.')
    validar(clave, d['respuestas'], final)
    ahora = db._ahora_utc()
    resultados = serializar(puntuar(clave, d['respuestas'])) if final else None
    if i:
        tabla = tabla_prueba('reintentos_pruebas' if i['ciclo'] else 'intentos_pruebas', clave)
        confirmacion = ',simulacro_confirmado=1' if clave=='NASATLX' and final else ''
        c.execute(f'UPDATE {tabla} SET respuestas_json=?,resultados_json=?,revision=revision+1,guardada_en=?,finalizada_en=?{confirmacion} WHERE id=?', (serializar(d['respuestas']), resultados, ahora, ahora if final else None, i['id']))
    else:
        extra = ',simulacro_confirmado' if clave=='NASATLX' else ''
        marcador = ',?' if extra else ''
        parametros = (pid, current_user.id, clave, f['version'], firma(clave), serializar(f), serializar(d['respuestas']), resultados, ahora, ahora, ahora if final else None)
        if extra: parametros += (int(final),)
        c.execute(f'INSERT INTO {tabla_prueba("intentos_pruebas", clave)}(periodo_id,voluntario_id,clave,version,firma_formulario,formulario_json,respuestas_json,resultados_json,revision,iniciada_en,guardada_en,finalizada_en{extra}) VALUES (?,?,?,?,?,?,?,?,1,?,?,?{marcador})', parametros)
    db.registrar_auditoria(c, current_user.id, f'PRUEBA:{"COMPLETADA" if final else "AVANCE"}:{pid}:{clave}', 'EXITOSO')
    return jsonify(estado='Completada' if final else 'Avance guardado', revision=d['revision']+1)


@pruebas_bp.get('/api/modelo-anual/gestiones/<int:pid>/personas/<int:uid>/pruebas')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
@transaccion
def resultados(c, pid, uid):
    p = periodo(c, pid)
    if not c.execute('SELECT 1 FROM personas_modelo_anual WHERE periodo_id=? AND voluntario_id=?', (pid, uid)).fetchone():
        raise LookupError('Persona no inscrita en esta Gestión.')
    db.registrar_auditoria(c, current_user.id, f'PRUEBAS_CONSULTA:{pid}:{uid}', 'EXITOSO')
    u = c.execute('SELECT estado,nombre_completo FROM usuarios WHERE id=?', (uid,)).fetchone()
    historia = []
    for r in sorted([dict(r) for t in ('reinicios_pruebas','tlx_reinicios_pruebas') for r in c.execute(f'SELECT * FROM {t} WHERE periodo_id=? AND voluntario_id=?', (pid,uid))], key=lambda r:r['reiniciada_en'], reverse=True):
        tabla = tabla_prueba('intentos_pruebas' if r['intento_original_id'] is not None else 'reintentos_pruebas', r['clave'])
        anterior = c.execute(f'SELECT finalizada_en,resultados_json FROM {tabla} WHERE id=?', (r['intento_original_id'] or r['reintento_anterior_id'],)).fetchone()
        historia.append(dict(nombre=CATALOGO[r['clave']]['nombre'], finalizada_en=anterior['finalizada_en'],
            reiniciada_en=r['reiniciada_en'], actor_nombre=r['actor_nombre'], subescalas=json.loads(anterior['resultados_json'])))
    return jsonify(pruebas=resultados_persona(c, pid, uid), historial=historia, persona=dict(id=uid,nombre=u['nombre_completo']),
                   puede_reiniciar=p['estado']=='ACTIVO' and not p['retirada'] and u['estado']=='ACTIVO')


@pruebas_bp.post('/api/modelo-anual/gestiones/<int:pid>/personas/<int:uid>/pruebas/<clave>/reiniciar')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
@transaccion
def reiniciar(c, pid, uid, clave):
    periodo(c, pid, True)
    persona(c, pid, uid)
    if clave not in CATALOGO:
        raise LookupError('Prueba no encontrada.')
    d = request.get_json(silent=True)
    if not isinstance(d, dict) or set(d) != {'password', 'intento_ref', 'revision', 'confirmar'} or d['confirmar'] is not True or type(d['revision']) is not int:
        raise ValueError('Contraseña, intento vigente y confirmación requeridos.')
    password = d['password']
    if not isinstance(password, str) or not 1 <= len(password) <= 256:
        raise ValueError('Ingresa tu contraseña de inicio de sesión.')
    credencial = c.execute('SELECT password_hash FROM usuarios WHERE id=?', (current_user.id,)).fetchone()
    if not check_password_hash(credencial['password_hash'], password):
        db.registrar_auditoria(c, current_user.id, f'PRUEBA_REINICIO:{pid}:{uid}:{clave}', 'FALLIDO')
        return jsonify(error='La contraseña de tu cuenta no es correcta.'), 403
    i = intento(c, pid, uid, clave)
    if not i or not i['finalizada_en']:
        raise ValueError('Solo se puede reiniciar una prueba completada.')
    if d['intento_ref'] != referencia(i) or d['revision'] != i['revision']:
        raise ValueError('El resultado cambió. Recarga antes de reiniciar.')
    ahora = db._ahora_utc()
    cursor = c.execute(f'INSERT INTO {tabla_prueba("reinicios_pruebas", clave)}(periodo_id,voluntario_id,clave,intento_original_id,reintento_anterior_id,actor_id,actor_nombre,reiniciada_en) VALUES (?,?,?,?,?,?,?,?)',
        (pid, uid, clave, None if i['ciclo'] else i['id'], i['id'] if i['ciclo'] else None, current_user.id, current_user.nombre, ahora))
    reinicio_id = cursor.lastrowid
    f = formulario(clave)
    if clave=='NASATLX':
        f['simulacro']=contexto_tlx(c,pid)
    c.execute(f'INSERT INTO {tabla_prueba("reintentos_pruebas", clave)}(reinicio_id,periodo_id,voluntario_id,clave,version,firma_formulario,formulario_json,respuestas_json,revision,iniciada_en,guardada_en) VALUES (?,?,?,?,?,?,?,?,1,?,?)',
        (reinicio_id, pid, uid, clave, f['version'], firma(clave), serializar(f), serializar([None]*len(f['items'])), ahora, ahora))
    db.registrar_auditoria(c, current_user.id, f'PRUEBA_REINICIO:{pid}:{uid}:{clave}:{reinicio_id}', 'EXITOSO')
    return jsonify(ok=True, estado='Pendiente')


@pruebas_bp.put('/api/modelo-anual/gestiones/<int:pid>/simulacro-tlx')
@role_required('ADMINISTRADOR','JEFE_PERSONAL')
@transaccion
def registrar_simulacro(c,pid):
    p=periodo(c,pid,True)
    d=request.get_json(silent=True)
    if not isinstance(d,dict) or set(d)!={'nombre','fecha','revision','realizado'} or d['realizado'] is not True or type(d['revision']) is not int:
        raise ValueError('Nombre, fecha, revisión y confirmación de simulacro realizado requeridos.')
    if not isinstance(d['nombre'],str) or not 3<=len(d['nombre'].strip())<=200:
        raise ValueError('Nombre del simulacro entre 3 y 200 caracteres.')
    try: fecha=date.fromisoformat(d['fecha'])
    except (TypeError,ValueError): raise ValueError('Fecha de simulacro inválida.') from None
    if not p['fecha_inicio']<=fecha.isoformat()<=p['fecha_fin'] or fecha>datetime.now(timezone(timedelta(hours=-4))).date():
        raise ValueError('El simulacro debe haberse realizado dentro de las fechas de esta Gestión.')
    actual=simulacro(c,pid)
    if d['revision']!=(actual['revision'] if actual else 0):
        raise ValueError('El simulacro cambió. Recarga.')
    if c.execute('SELECT 1 FROM tlx_intentos_pruebas WHERE periodo_id=?',(pid,)).fetchone():
        raise ValueError('El simulacro se conserva sin cambios porque ya existen intentos vinculados.')
    c.execute('INSERT INTO simulacros_tlx VALUES (?,?,?,?,?,?,?) ON CONFLICT(periodo_id) DO UPDATE SET nombre=excluded.nombre,fecha=excluded.fecha,revision=excluded.revision,actor_id=excluded.actor_id,actor_nombre=excluded.actor_nombre,registrada_en=excluded.registrada_en',
        (pid,d['nombre'].strip(),fecha.isoformat(),d['revision']+1,current_user.id,current_user.nombre,db._ahora_utc()))
    db.registrar_auditoria(c,current_user.id,f'SIMULACRO_TLX:{pid}','EXITOSO')
    return jsonify(ok=True)
