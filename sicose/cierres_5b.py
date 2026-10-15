"""Ciclo administrativo y conservación inmutable de cada cierre, sin publicar notas."""
import hashlib
import json
import sqlite3
from flask import Blueprint, jsonify, request
from flask_login import current_user
from . import db
from .permissions import role_required

cierres_bp = Blueprint('cierres_5b', __name__)


def serializar(valor):
    return json.dumps(valor, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def filas(c, sql, args=()):
    return [dict(f) for f in c.execute(sql, args)]


def ultimo(c, pid):
    f = c.execute('SELECT * FROM cierres_5b WHERE periodo_id=? ORDER BY id DESC LIMIT 1', (pid,)).fetchone()
    return dict(f) if f else None


def resumen(c, pid):
    return filas(c, '''SELECT c.id,c.numero,c.anterior_id,c.motivo,c.actor_nombre,c.registrada_en,
                      c.total_personas,c.incompletos,r.id AS reapertura_id,r.motivo AS motivo_reapertura,
                      r.actor_nombre AS reabierta_por,r.registrada_en AS reabierta_en
                      FROM cierres_5b c LEFT JOIN reaperturas_5b r ON r.cierre_id=c.id
                      WHERE c.periodo_id=? ORDER BY c.id''', (pid,))


def resultado_cerrado(c, uid, pid):
    f = c.execute('''SELECT i.contenido_json,i.cierre_id FROM instantaneas_cierre_5b i
                     WHERE i.voluntario_id=? AND i.cierre_id=(SELECT MAX(id) FROM cierres_5b WHERE periodo_id=?)''', (uid, pid)).fetchone()
    if not f:
        return {'regla': None, 'estado': 'FUERA_DEL_CIERRE', 'resultado_conjunto': None,
                'faltantes': ['SIN_INSTANTANEA'], 'bloqueos': [], 'provisional': False,
                'academica': {'valor': None, 'puntos_sin_tope': 0, 'tope': 100, 'detalle': []},
                'fisica': None, 'desempeno': None, 'fuentes': {},
                'limite': 'La persona no tiene instantánea en este cierre; no se reconstruyen resultados.'}
    valor = json.loads(f['contenido_json'])['calculo']
    valor.update(provisional=False, cierre_id=f['cierre_id'])
    return valor


def preparar(c, pid, documental=False):
    from .gestiones import retirada, estado_evaluaciones
    from .periodos_5b import configuracion
    from .calculos_5b import calcular, regla
    p = c.execute('SELECT * FROM periodos WHERE id=?', (pid,)).fetchone()
    if p is None:
        raise LookupError('Gestión no encontrada.')
    esperado = 'CERRADO' if documental else 'ACTIVO'
    if retirada(c, pid) or p['estado'] != esperado:
        raise ValueError(f'Requiere una Gestión {esperado} no retirada.')
    if documental and (ultimo(c, pid) or c.execute('SELECT 1 FROM reaperturas_historicas_5b WHERE periodo_id=?', (pid,)).fetchone()):
        raise ValueError('La Gestión tiene un cierre conservado o una reapertura histórica registrada; usa el ciclo ordinario.')
    contexto = {'formato': 'EVIDENCIA_REAPERTURA_HISTORICA_V1' if documental else 'CIERRE_5B_V1', 'periodo': dict(p), 'configuracion': configuracion(c, pid),
                'regla_calculo': regla(c, pid), 'evaluaciones': estado_evaluaciones(c, pid),
                'activaciones': filas(c, 'SELECT * FROM activaciones_gestion WHERE periodo_id=? ORDER BY id', (pid,)),
                'programaciones': filas(c, 'SELECT * FROM programaciones_fisicas WHERE periodo_id=? ORDER BY id', (pid,)),
                'ponderaciones_historicas': filas(c, 'SELECT * FROM versiones_ponderacion WHERE periodo_id=? ORDER BY id', (pid,)),
                'pesos_historicos': filas(c, 'SELECT pe.* FROM pesos_evaluacion pe JOIN versiones_ponderacion v ON v.id=pe.version_id WHERE v.periodo_id=? ORDER BY pe.version_id,pe.evaluacion_id', (pid,)),
                'reapertura_historica': filas(c, 'SELECT id,motivo,actor_id,actor_nombre,registrada_en FROM reaperturas_historicas_5b WHERE periodo_id=?', (pid,))}
    if documental:
        contexto.update(fecha_cierre_original=None, sin_instantanea_original=True,
                        advertencia='Evidencia disponible al reabrir; no representa los resultados del cierre original.')
    personas = []
    miembros = filas(c, '''SELECT u.id,u.nombre_completo AS nombre,u.estado,r.nombre AS rol,v.codigo_instructor AS codigo
                         FROM voluntarios v JOIN usuarios u ON u.id=v.usuario_id JOIN roles r ON r.id=u.rol_id
                         WHERE (r.nombre='INSTRUCTOR_VOLUNTARIO' AND u.estado IN ('ACTIVO','INACTIVO'))
                         OR EXISTS(SELECT 1 FROM notas_operativas n WHERE n.voluntario_id=u.id AND n.periodo_id=?)
                         OR EXISTS(SELECT 1 FROM asignaciones_evaluacion a WHERE a.voluntario_id=u.id AND a.periodo_id=?)
                         ORDER BY u.id''', (pid, pid))
    for persona in miembros:
        uid = persona['id']
        calculo = ({'regla': None, 'estado': 'NO_RECONSTRUIDO', 'resultado_conjunto': None,
                    'faltantes': [], 'provisional': False} if documental else calcular(c, uid, pid))
        if not documental and calculo['regla'] is None:
            calculo.update(estado='INCOMPLETO', faltantes=['REGLA_V2_NO_ACTIVADA'], provisional=False)
        else:
            calculo['provisional'] = False
        datos = {'persona': persona, 'calculo': calculo,
                 'notas': filas(c, 'SELECT * FROM notas_operativas WHERE voluntario_id=? AND periodo_id=? ORDER BY id', (uid, pid)),
                 'respaldo_academico': filas(c, 'SELECT a.* FROM respaldo_academico a JOIN notas_operativas n ON n.id=a.nota_id WHERE n.voluntario_id=? AND n.periodo_id=? ORDER BY a.nota_id,a.capacitacion_id', (uid, pid)),
                 'habilitaciones': filas(c, 'SELECT * FROM habilitaciones_operativas WHERE voluntario_id=? AND periodo_id=? ORDER BY id', (uid, pid)),
                 'reprogramaciones': filas(c, 'SELECT * FROM reprogramaciones_fisicas WHERE voluntario_id=? AND periodo_id=? ORDER BY id', (uid, pid)),
                 'resultados_fisicos': filas(c, 'SELECT f.* FROM resultados_fisicos f JOIN notas_operativas n ON n.id=f.nota_id WHERE n.voluntario_id=? AND n.periodo_id=? ORDER BY f.nota_id', (uid, pid)),
                 'formacion': filas(c, '''SELECT p.*,h.id AS historial_id,h.registrada_por,h.responsable_nombre,h.registrada_en,h.motivo
                              FROM participaciones_curso p JOIN historial_participaciones_curso h ON h.participacion_id=p.id AND h.revision=p.revision
                              WHERE p.voluntario_id=? AND (p.fecha_finalizacion BETWEEN ? AND ? OR (p.inicio_curso<=? AND p.fin_curso>=?)) ORDER BY p.id''', (uid,p['fecha_inicio'],p['fecha_fin'],p['fecha_fin'],p['fecha_inicio'])),
                 'asignaciones_historicas': filas(c, 'SELECT a.*,e.nombre AS evaluacion,e.categoria FROM asignaciones_evaluacion a JOIN evaluaciones e ON e.id=a.evaluacion_id WHERE a.voluntario_id=? AND a.periodo_id=? ORDER BY a.id', (uid,pid)),
                 'notas_historicas': filas(c, '''SELECT n.*,u.nombre_completo AS autor_al_cierre FROM calificaciones n JOIN asignaciones_evaluacion a ON a.id=n.asignacion_id JOIN evaluaciones e ON e.id=a.evaluacion_id JOIN usuarios u ON u.id=n.registrada_por WHERE a.voluntario_id=? AND a.periodo_id=? AND e.categoria!='PSICOMETRICA' ORDER BY n.id''', (uid,pid)),
                 'publicacion': None}
        pub = c.execute('SELECT * FROM publicaciones_5b WHERE voluntario_id=? AND periodo_id=? ORDER BY id DESC LIMIT 1', (uid,pid)).fetchone()
        if pub:
            datos['publicacion'] = dict(pub)
        personas.append(datos)
    previo = ultimo(c, pid)
    contenido = {'contexto': contexto, 'personas': personas, 'cierre_anterior_id': previo['id'] if previo else None}
    firma = hashlib.sha256(serializar(contenido).encode('utf-8')).hexdigest()
    return contenido, firma


@cierres_bp.after_request
def cache_privada(respuesta):
    respuesta.headers['Cache-Control'] = 'private, no-store'
    return respuesta


@cierres_bp.get('/api/5b/periodos/<int:pid>/cierre-previo')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
def vista(pid):
    c = db.obtener_conexion()
    try:
        c.execute('BEGIN')
        contenido, firma = preparar(c, pid)
        c.commit()
        return jsonify(**contenido, firma_fuentes=firma)
    except (LookupError, ValueError) as error:
        c.rollback(); return jsonify(error=str(error)), 404 if isinstance(error, LookupError) else 409


@cierres_bp.post('/api/admin/5b/periodos/<int:pid>/cerrar')
@role_required('ADMINISTRADOR')
def cerrar(pid):
    datos = request.get_json(silent=True)
    if (not isinstance(datos,dict) or set(datos) != {'motivo','firma_fuentes','cierre_anterior_id','confirmar_incompletos'}
            or not isinstance(datos['motivo'],str) or not 1 <= len(datos['motivo'].strip()) <= 2000
            or not isinstance(datos['firma_fuentes'],str) or type(datos['confirmar_incompletos']) is not bool
            or (datos['cierre_anterior_id'] is not None and type(datos['cierre_anterior_id']) is not int)):
        return jsonify(error='Motivo, firma, cierre anterior y confirmación de incompletos requeridos.'),400
    c = db.obtener_conexion()
    try:
        c.execute('BEGIN IMMEDIATE')
        contenido, firma = preparar(c, pid)
        if firma != datos['firma_fuentes'] or contenido['cierre_anterior_id'] != datos['cierre_anterior_id']:
            raise ValueError('Las fuentes cambiaron; revisa de nuevo antes de cerrar.')
        personas = contenido['personas']
        incompletos = sum(p['calculo']['estado'] != 'COMPLETO' for p in personas)
        if incompletos and not datos['confirmar_incompletos']:
            raise ValueError('Confirma expresamente las personas incompletas; no se convertirán faltantes en cero.')
        previo = ultimo(c,pid)
        cid = c.execute('''INSERT INTO cierres_5b(periodo_id,numero,anterior_id,contexto_json,firma_fuentes,motivo,actor_id,actor_nombre,registrada_en,total_personas,incompletos)
                           VALUES (?,?,?,?,?,?,?,?,?,?,?)''', (pid,previo['numero']+1 if previo else 1,previo['id'] if previo else None,serializar(contenido['contexto']),firma,datos['motivo'].strip(),current_user.id,current_user.nombre,db._ahora_utc(),len(personas),incompletos)).lastrowid
        c.executemany('INSERT INTO instantaneas_cierre_5b(cierre_id,voluntario_id,contenido_json) VALUES (?,?,?)', ((cid,p['persona']['id'],serializar(p)) for p in personas))
        c.execute("UPDATE periodos SET estado='CERRADO' WHERE id=?", (pid,))
        db.registrar_auditoria(c,current_user.id,'GESTION_CERRADA','EXITOSO')
        c.commit()
        return jsonify(ok=True,cierre_id=cid,incompletos=incompletos,total_personas=len(personas)),201
    except (LookupError,ValueError) as error:
        c.rollback();return jsonify(error=str(error)),404 if isinstance(error,LookupError) else 409
    except (sqlite3.IntegrityError,sqlite3.OperationalError):
        c.rollback();return jsonify(error='Cierre concurrente; recarga la Gestión.'),409


@cierres_bp.get('/api/5b/periodos/<int:pid>/cierres')
@role_required('ADMINISTRADOR','JEFE_PERSONAL')
def historial(pid):
    c=db.obtener_conexion()
    if not c.execute('SELECT 1 FROM periodos WHERE id=?',(pid,)).fetchone():
        return jsonify(error='Gestión no encontrada.'),404
    return jsonify(cierres=resumen(c,pid))


@cierres_bp.get('/api/5b/periodos/<int:pid>/cierres/<int:cid>')
@role_required('ADMINISTRADOR','JEFE_PERSONAL')
def detalle(pid,cid):
    c=db.obtener_conexion()
    f=c.execute('SELECT * FROM cierres_5b WHERE id=? AND periodo_id=?',(cid,pid)).fetchone()
    if not f:return jsonify(error='Cierre no encontrado en esta Gestión.'),404
    valor=dict(f);valor['contexto']=json.loads(valor.pop('contexto_json'))
    valor['personas']=[json.loads(p[0]) for p in c.execute('SELECT contenido_json FROM instantaneas_cierre_5b WHERE cierre_id=? ORDER BY voluntario_id',(cid,))]
    return jsonify(cierre=valor)


@cierres_bp.post('/api/admin/5b/periodos/<int:pid>/reabrir')
@role_required('ADMINISTRADOR')
def reabrir(pid):
    datos=request.get_json(silent=True)
    if (not isinstance(datos,dict) or set(datos)!={'motivo','cierre_id'} or not isinstance(datos['motivo'],str)
            or not 1<=len(datos['motivo'].strip())<=2000 or type(datos['cierre_id']) is not int):
        return jsonify(error='Motivo y cierre vigente requeridos.'),400
    c=db.obtener_conexion()
    try:
        c.execute('BEGIN IMMEDIATE')
        from .gestiones import retirada
        p=c.execute('SELECT estado FROM periodos WHERE id=?',(pid,)).fetchone()
        cierre=ultimo(c,pid)
        if p is None:
            c.rollback();return jsonify(error='Gestión no encontrada.'),404
        if retirada(c,pid) or p['estado']!='CERRADO' or cierre is None or cierre['id']!=datos['cierre_id']:
            raise ValueError('Requiere Gestión cerrada no retirada y su último cierre conservado.')
        if c.execute("SELECT 1 FROM periodos WHERE estado='ACTIVO' AND id!=? AND NOT EXISTS(SELECT 1 FROM bajas_gestion b WHERE b.periodo_id=periodos.id)",(pid,)).fetchone():
            raise ValueError('Ya existe otra Gestión activa. No se cerrará automáticamente.')
        c.execute('INSERT INTO reaperturas_5b(cierre_id,motivo,actor_id,actor_nombre,registrada_en) VALUES (?,?,?,?,?)',(cierre['id'],datos['motivo'].strip(),current_user.id,current_user.nombre,db._ahora_utc()))
        c.execute("UPDATE periodos SET estado='ACTIVO' WHERE id=?",(pid,))
        db.registrar_auditoria(c,current_user.id,'GESTION_REABIERTA','EXITOSO')
        c.commit();return jsonify(ok=True,cierre_id=cierre['id'])
    except ValueError as error:
        c.rollback();return jsonify(error=str(error)),409
    except (sqlite3.IntegrityError,sqlite3.OperationalError):
        c.rollback();return jsonify(error='Reapertura concurrente; recarga la Gestión.'),409
