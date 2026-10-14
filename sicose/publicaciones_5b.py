"""Publicación propia por versiones: solo físicas y formación, sin Desempeño."""
import hashlib
import json
import sqlite3
from fractions import Fraction
from flask import Blueprint, jsonify, request
from flask_login import current_user
from . import db
from .permissions import role_required
from .gestiones import retirada
from .calculos_5b import regla, expresar

publicaciones_bp = Blueprint('publicaciones_5b', __name__)
FISICAS = ('FISICA_1', 'FISICA_2')


@publicaciones_bp.after_request
def respuesta_privada(respuesta):
    respuesta.headers['Cache-Control'] = 'private, no-store'
    return respuesta


def serializar(valor):
    return json.dumps(valor, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def ultima(c, uid, pid):
    return c.execute('SELECT * FROM publicaciones_5b WHERE voluntario_id=? AND periodo_id=? ORDER BY revision DESC LIMIT 1', (uid, pid)).fetchone()


def preparar(c, uid, pid):
    from .tabla_evaluaciones import habilitada
    from .seguimiento_5b import persona
    perfil = persona(c, uid)
    periodo = c.execute('SELECT * FROM periodos WHERE id=?', (pid,)).fetchone()
    if perfil is None or periodo is None:
        raise ValueError('Persona o gestión no encontrada.')
    r = regla(c, pid)
    anterior = ultima(c, uid, pid)
    contenido = json.loads(anterior['contenido_json']) if anterior else {'fisicas': {}, 'academica': None}
    fuentes = json.loads(anterior['fuentes_json']) if anterior else {}
    habilitadas = {f: habilitada(c, uid, pid, f) for f in (*FISICAS, 'ACADEMICA')}
    if r:
        for f in FISICAS:
            if not habilitadas[f]:
                continue
            n = c.execute("""SELECT n.id,n.puntos_centesimas,x.estado,x.fecha_realizacion,x.programacion_id,x.reprogramacion_id
                FROM notas_operativas n LEFT JOIN resultados_fisicos x ON x.nota_id=n.id
                WHERE n.voluntario_id=? AND n.periodo_id=? AND n.fuente=? ORDER BY n.id DESC LIMIT 1""", (uid, pid, f)).fetchone()
            configurada = c.execute('SELECT configuracion_id FROM notas_operativas WHERE id=?', (n['id'],)).fetchone()[0] if n else None
            valida = bool(n and n['estado'] and configurada == r['configuracion_id'])
            contenido['fisicas'][f] = {'estado': 'NO_CUMPLIDA' if valida and n['estado'] == 'NO_CUMPLIDA' else 'FINALIZADA' if valida else 'PENDIENTE',
                                       'nota': f"{n['puntos_centesimas']/100:.2f}" if valida else None,
                                       'fecha_realizacion': n['fecha_realizacion'] if valida else None}
            fuentes[f] = {'nota_id': n['id'] if valida else None, 'programacion_id': n['programacion_id'] if valida else None,
                          'reprogramacion_id': n['reprogramacion_id'] if valida else None}
        if habilitadas['ACADEMICA']:
            filas = [dict(p) for p in c.execute("""SELECT p.id AS participacion_id,p.curso_id,p.nombre_curso,p.puntaje,p.fecha_finalizacion,p.revision,h.id AS historial_id
                FROM participaciones_curso p JOIN historial_participaciones_curso h ON h.participacion_id=p.id AND h.revision=p.revision
                WHERE p.voluntario_id=? AND p.estado='Finalizado' AND substr(p.fecha_finalizacion,1,4)=? ORDER BY p.fecha_finalizacion,p.id""", (uid, f"{r['ano']:04d}"))]
            suma = sum(p['puntaje'] for p in filas)
            contenido['academica'] = {'valor': min(suma, 100) if filas else None, 'puntos_sin_tope': suma if filas else None,
                                      'cursos': [{k: p[k] for k in ('participacion_id', 'nombre_curso', 'puntaje', 'fecha_finalizacion')} for p in filas]}
            fuentes['ACADEMICA'] = [{k: p[k] for k in ('participacion_id', 'curso_id', 'revision', 'historial_id')} for p in filas]
    # Las fechas de publicación son metadatos de versión, no datos editables del cliente.
    for f in FISICAS:
        if f in contenido['fisicas']:
            contenido['fisicas'][f].pop('publicada_en', None)
    if contenido['academica']:
        contenido['academica'].pop('publicada_en', None)
    firma = hashlib.sha256(serializar({'contenido': contenido, 'fuentes': fuentes, 'habilitadas': habilitadas, 'regla': r}).encode()).hexdigest()
    alguna_nota = any(p.get('nota') is not None for p in contenido['fisicas'].values()) or (contenido['academica'] is not None and contenido['academica']['valor'] is not None)
    puede = bool(r and perfil['estado'] == 'ACTIVO' and periodo['estado'] == 'ACTIVO' and not retirada(c, pid) and any(habilitadas.values()) and (anterior or alguna_nota))
    return {'contenido': contenido, 'fuentes': fuentes, 'firma_fuentes': firma, 'revision_publicada': anterior['revision'] if anterior else 0,
            'puede_publicar': puede, 'habilitadas': habilitadas, 'regla': r, 'anterior': anterior}


def proyeccion(c, uid, pid):
    """Lista positiva, filtrada en servidor incluso tras deshabilitación o baja."""
    from .tabla_evaluaciones import habilitada
    fila = ultima(c, uid, pid)
    if fila is None or retirada(c, pid):
        return None
    contenido = json.loads(fila['contenido_json'])
    fisicas = []
    for f in FISICAS:
        p = contenido['fisicas'].get(f)
        if p and habilitada(c, uid, pid, f):
            fisicas.append({'clave': f, 'nombre': 'Física 1' if f == 'FISICA_1' else 'Física 2',
                            **{k: p[k] for k in ('estado', 'nota', 'fecha_realizacion', 'publicada_en')}})
    academica = contenido['academica'] if habilitada(c, uid, pid, 'ACADEMICA') else None
    if academica:
        academica = {k: academica[k] for k in ('valor', 'puntos_sin_tope', 'publicada_en', 'cursos')}
        academica['cursos'] = [{k: curso[k] for k in ('participacion_id', 'nombre_curso', 'puntaje', 'fecha_finalizacion')} for curso in academica['cursos']]
    if not fisicas and academica is None:
        return None
    promedio = None
    if len(fisicas) == 2 and all(p['nota'] is not None for p in fisicas):
        from decimal import Decimal
        promedio = expresar(Fraction(sum(int(Decimal(p['nota']) * 100) for p in fisicas), 2))
    return {'revision': fila['revision'], 'publicada_en': fila['publicada_en'], 'fisicas': fisicas,
            'promedio_fisico': promedio, 'academica': academica}


def estado_admin(c, uid, pid):
    p = preparar(c, uid, pid)
    fila = p.pop('anterior')
    anterior = json.loads(fila['contenido_json']) if fila else None
    comparar = json.loads(fila['contenido_json']) if fila else None
    if comparar:
        for f in comparar['fisicas'].values(): f.pop('publicada_en', None)
        if comparar['academica']: comparar['academica'].pop('publicada_en', None)
    p['hay_cambios'] = bool(fila and (comparar != p['contenido'] or json.loads(fila['fuentes_json']) != p['fuentes']))
    p['publicada_en'] = fila['publicada_en'] if fila else None
    p['contenido_publicado'] = anterior
    return p


@publicaciones_bp.get('/api/5b/personas/<int:uid>/publicacion')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
def consultar(uid):
    from .tabla_evaluaciones import periodo_solicitado
    c = db.obtener_conexion()
    try:
        pid = periodo_solicitado(); c.execute('BEGIN')
        datos = estado_admin(c, uid, pid); c.commit()
        return jsonify(publicacion=datos)
    except ValueError as error:
        c.rollback(); return jsonify(error=str(error)), 400


@publicaciones_bp.post('/api/5b/personas/<int:uid>/publicacion')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
def publicar(uid):
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict) or set(datos) != {'periodo_id', 'revision_publicada', 'firma_fuentes', 'motivo'} or type(datos['periodo_id']) is not int or type(datos['revision_publicada']) is not int or datos['revision_publicada'] < 0 or not isinstance(datos['firma_fuentes'], str) or len(datos['firma_fuentes']) != 64 or not isinstance(datos['motivo'], str) or not 1 <= len(datos['motivo'].strip()) <= 2000:
        return jsonify(error='Gestión, revisión, firma de vista previa y motivo requeridos.'), 400
    c = db.obtener_conexion()
    try:
        c.execute('BEGIN IMMEDIATE')
        p = preparar(c, uid, datos['periodo_id'])
        if not p['puede_publicar'] or p['revision_publicada'] != datos['revision_publicada'] or p['firma_fuentes'] != datos['firma_fuentes']:
            c.rollback(); return jsonify(error='No se puede publicar o las fuentes cambiaron. Recarga la vista previa.'), 409
        anterior = p['anterior']
        viejo = json.loads(anterior['contenido_json']) if anterior else {'fisicas': {}, 'academica': None}
        refs = json.loads(anterior['fuentes_json']) if anterior else {}
        ahora = db._ahora_utc()
        for f, valor in p['contenido']['fisicas'].items():
            valor['publicada_en'] = viejo['fisicas'][f]['publicada_en'] if f in viejo['fisicas'] and refs.get(f) == p['fuentes'].get(f) and {k: v for k, v in viejo['fisicas'][f].items() if k != 'publicada_en'} == valor else ahora
        if p['contenido']['academica']:
            igual = viejo['academica'] and refs.get('ACADEMICA') == p['fuentes'].get('ACADEMICA') and {k: v for k, v in viejo['academica'].items() if k != 'publicada_en'} == p['contenido']['academica']
            p['contenido']['academica']['publicada_en'] = viejo['academica']['publicada_en'] if igual else ahora
        if anterior and serializar(p['contenido']) == anterior['contenido_json'] and serializar(p['fuentes']) == anterior['fuentes_json']:
            c.rollback(); return jsonify(ok=True, revision=anterior['revision'], sin_cambios=True)
        revision = p['revision_publicada'] + 1
        c.execute('INSERT INTO publicaciones_5b(voluntario_id,periodo_id,revision,anterior_id,contenido_json,fuentes_json,motivo,publicada_por,responsable_nombre,publicada_en) VALUES (?,?,?,?,?,?,?,?,?,?)',
                  (uid, datos['periodo_id'], revision, anterior['id'] if anterior else None, serializar(p['contenido']), serializar(p['fuentes']), datos['motivo'].strip(), current_user.id, current_user.nombre, ahora))
        db.registrar_auditoria(c, current_user.id, 'NOTAS_REPUBLICADAS' if anterior else 'NOTAS_PUBLICADAS', 'EXITOSO')
        c.commit()
        return jsonify(ok=True, revision=revision), 201
    except ValueError as error:
        c.rollback(); return jsonify(error=str(error)), 400
    except (sqlite3.IntegrityError, sqlite3.OperationalError):
        c.rollback(); return jsonify(error='Conflicto al publicar; recarga la vista previa.'), 409


@publicaciones_bp.get('/api/5b/personas/<int:uid>/publicaciones/historial')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
def historial(uid):
    from .tabla_evaluaciones import periodo_solicitado
    try:
        pid = periodo_solicitado()
    except ValueError as error:
        return jsonify(error=str(error)), 400
    filas = db.obtener_conexion().execute('SELECT revision,contenido_json,fuentes_json,motivo,responsable_nombre,publicada_en FROM publicaciones_5b WHERE voluntario_id=? AND periodo_id=? ORDER BY revision', (uid, pid))
    return jsonify(historial=[{'revision': f['revision'], 'contenido': json.loads(f['contenido_json']), 'fuentes': json.loads(f['fuentes_json']),
                              'motivo': f['motivo'], 'responsable_nombre': f['responsable_nombre'], 'publicada_en': f['publicada_en']} for f in filas])
