"""Habilitación individual por gestión, independiente de notas y finalización."""
import sqlite3
from flask import Blueprint, jsonify, render_template, request, send_file
from flask_login import current_user
from . import db
from .permissions import role_required
from .seguimiento_5b import FUENTES

tabla_bp = Blueprint('tabla_evaluaciones', __name__)
NOMBRES = dict(zip(FUENTES, ('Física 1', 'Física 2', 'Académica', 'Desempeño del Jefe', 'Desempeño del Comandante')))


def habilitacion_personal(c, uid, pid, clave):
    fila = c.execute('SELECT habilitada FROM habilitaciones_operativas WHERE voluntario_id=? AND periodo_id=? AND clave=? ORDER BY id DESC LIMIT 1', (uid, pid, clave)).fetchone()
    if fila is not None:
        return bool(fila[0])
    if clave.startswith('PSICO:'):
        a = c.execute("SELECT estado FROM asignaciones_evaluacion WHERE voluntario_id=? AND periodo_id=? AND evaluacion_id=?", (uid, pid, int(clave[6:]))).fetchone()
        return bool(a and a[0] in ('HABILITADA', 'EN_PROGRESO', 'COMPLETADA'))
    return False


def habilitada(c, uid, pid, clave):
    from .gestiones import activa
    return activa(c, pid, clave) and habilitacion_personal(c, uid, pid, clave)


def evaluaciones_persona(c, uid, pid):
    from .gestiones import activa
    resultado = []
    for fuente in FUENTES:
        ultima = c.execute('SELECT id,puntos_centesimas,configuracion_id FROM notas_operativas WHERE voluntario_id=? AND periodo_id=? AND fuente=? ORDER BY id DESC LIMIT 1', (uid, pid, fuente)).fetchone()
        fisica = c.execute('SELECT estado FROM resultados_fisicos WHERE nota_id=?', (ultima['id'],)).fetchone() if ultima else None
        resultado.append({'clave': fuente, 'nombre': NOMBRES[fuente], 'activa': activa(c, pid, fuente), 'habilitada': habilitacion_personal(c, uid, pid, fuente), 'estado': 'FINALIZADA' if ultima else 'PENDIENTE',
                          'nota': f'{ultima["puntos_centesimas"]/100:.2f}' if ultima else None, 'nota_id': ultima['id'] if ultima else None,
                          'historica': bool(ultima and ultima['configuracion_id'] is None)})
        if fisica and fisica['estado'] == 'NO_CUMPLIDA':
            resultado[-1]['estado'] = 'NO_CUMPLIDA'
    filas = c.execute("""SELECT e.id,e.nombre,a.estado FROM evaluaciones e LEFT JOIN asignaciones_evaluacion a
                       ON a.evaluacion_id=e.id AND a.voluntario_id=? AND a.periodo_id=?
                       WHERE e.categoria='PSICOMETRICA' AND (e.activo=1 OR a.id IS NOT NULL) ORDER BY e.nombre,e.id""", (uid, pid))
    for f in filas:
        clave = f'PSICO:{f["id"]}'
        resultado.append({'clave': clave, 'nombre': f['nombre'], 'activa': activa(c, pid, clave), 'habilitada': habilitacion_personal(c, uid, pid, clave),
                          'estado': 'FINALIZADA' if f['estado'] == 'COMPLETADA' else 'EN_PROGRESO' if f['estado'] == 'EN_PROGRESO' else 'PENDIENTE', 'nota': None})
    from .calculos_5b import regla, calcular
    if regla(c, pid):
        calculo = calcular(c, uid, pid)
        academica = next(e for e in resultado if e['clave'] == 'ACADEMICA')
        puntos = calculo['academica']['valor']
        academica.update(nota=f'{puntos:.2f}' if puntos is not None else None, nota_id=None,
                         estado='FINALIZADA' if puntos is not None else 'PENDIENTE', calculada=True, historica=False)
    return resultado


def datos_gestion(c, pid):
    periodo = c.execute('SELECT id,nombre,estado,fecha_inicio,fecha_fin FROM periodos WHERE id=?', (pid,)).fetchone()
    if periodo is None:
        raise ValueError('Gestión no encontrada.')
    personas = []
    from .gestiones import retirada
    for p in c.execute("""SELECT u.id,u.nombre_completo AS nombre,u.estado,v.codigo_instructor AS codigo
                          FROM voluntarios v JOIN usuarios u ON u.id=v.usuario_id WHERE u.estado IN ('ACTIVO','INACTIVO') ORDER BY u.nombre_completo,u.id"""):
        valor = dict(p)
        valor['evaluaciones'] = evaluaciones_persona(c, p['id'], pid)
        valor['resumen'] = resumen(valor['evaluaciones'])
        personas.append(valor)
    return {'periodo': {**dict(periodo), 'retirada': retirada(c, pid)}, 'personas': personas}


def resumen(evaluaciones):
    habilitadas = [e for e in evaluaciones if e['habilitada'] and e.get('activa', True)]
    resueltas = sum(e['estado'] in ('FINALIZADA', 'NO_CUMPLIDA') for e in habilitadas)
    return {'habilitadas': len(habilitadas), 'finalizadas': sum(e['estado'] == 'FINALIZADA' for e in habilitadas),
            'no_cumplidas': sum(e['estado'] == 'NO_CUMPLIDA' for e in habilitadas), 'pendientes': len(habilitadas) - resueltas,
            'avance': round(100 * resueltas / len(habilitadas), 2) if habilitadas else None}


def periodo_solicitado():
    if set(request.args) != {'periodo_id'} or len(request.args.getlist('periodo_id')) != 1:
        raise ValueError('Selecciona una gestión.')
    pid = int(request.args['periodo_id'])
    if pid < 1:
        raise ValueError('Gestión no válida.')
    return pid


@tabla_bp.get('/gestion/tabla-evaluaciones')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
def pagina():
    return render_template('tabla_evaluaciones.html', titulo_pagina='Evaluaciones por gestión', nav_activo='tabla_evaluaciones',
                           indicadores=[], periodo_actual=db.periodo_actual(), descripcion='Habilitación individual, estado e historial de personal activo e inactivo.')


@tabla_bp.get('/api/evaluaciones/gestiones')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL', 'INSTRUCTOR_VOLUNTARIO')
def gestiones():
    c = db.obtener_conexion()
    from .gestiones import retirada
    valores = [{**dict(p), 'retirada': retirada(c, p['id'])} for p in c.execute('SELECT id,nombre,estado,substr(fecha_inicio,1,4) AS gestion FROM periodos ORDER BY fecha_inicio DESC,id DESC')]
    return jsonify(periodos=[p for p in valores if not p['retirada']],
                   retiradas=[p for p in valores if p['retirada']] if current_user.rol != 'INSTRUCTOR_VOLUNTARIO' else [])


@tabla_bp.get('/api/evaluaciones/tabla')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
def listar():
    try:
        pid = periodo_solicitado()
        c = db.obtener_conexion()
        c.execute('BEGIN')
        datos = datos_gestion(c, pid)
        c.commit()
        return jsonify(datos)
    except ValueError as error:
        return jsonify(error=str(error)), 400


@tabla_bp.patch('/api/evaluaciones/personas/<int:uid>/habilitacion')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
def cambiar(uid):
    entrada = request.get_json(silent=True)
    if not isinstance(entrada, dict) or set(entrada) != {'periodo_id', 'clave', 'habilitada'} or type(entrada['periodo_id']) is not int or type(entrada['habilitada']) is not bool or not isinstance(entrada['clave'], str):
        return jsonify(error='Gestión, evaluación y habilitación no válidas.'), 400
    c = db.obtener_conexion()
    try:
        c.execute('BEGIN IMMEDIATE')
        p = c.execute("SELECT u.estado FROM voluntarios v JOIN usuarios u ON u.id=v.usuario_id WHERE u.id=?", (uid,)).fetchone()
        periodo = c.execute('SELECT estado FROM periodos WHERE id=?', (entrada['periodo_id'],)).fetchone()
        if p is None or periodo is None:
            raise ValueError('Persona o gestión no encontrada.')
        from .gestiones import retirada, activa
        if retirada(c, entrada['periodo_id']) or p[0] != 'ACTIVO' or periodo[0] != 'ACTIVO':
            c.rollback(); return jsonify(error='La cuenta y la gestión deben estar activas para cambiar habilitaciones.'), 409
        clave = entrada['clave']
        opciones = evaluaciones_persona(c, uid, entrada['periodo_id'])
        if clave not in {e['clave'] for e in opciones}:
            raise ValueError('Evaluación no válida.')
        if entrada['habilitada'] and not activa(c, entrada['periodo_id'], clave):
            c.rollback(); return jsonify(error='Activa primero la evaluación en esta gestión.'), 409
        if clave in FUENTES:
            if entrada['habilitada'] and not c.execute("SELECT 1 FROM configuraciones_5b WHERE periodo_id=? AND estado='PUBLICADA'", (entrada['periodo_id'],)).fetchone():
                c.rollback(); return jsonify(error='Primero publica la configuración de la gestión.'), 409
        else:
            eid = int(clave[6:])
            e = c.execute('SELECT e.activo,i.estado_aprobacion FROM evaluaciones e LEFT JOIN instrumentos i ON i.id=e.instrumento_id WHERE e.id=?', (eid,)).fetchone()
            if entrada['habilitada'] and (not e[0] or e[1] != 'APROBADO'):
                c.rollback(); return jsonify(error='Instrumento sin aprobación o evaluación inactiva; el formulario no está disponible.'), 409
            c.execute("INSERT INTO asignaciones_evaluacion(voluntario_id,periodo_id,evaluacion_id) VALUES (?,?,?) ON CONFLICT DO NOTHING", (uid, entrada['periodo_id'], eid))
            c.execute("UPDATE asignaciones_evaluacion SET estado=?,habilitada_por=?,habilitada_en=? WHERE voluntario_id=? AND periodo_id=? AND evaluacion_id=? AND estado NOT IN ('COMPLETADA','EN_PROGRESO')",
                      ('HABILITADA' if entrada['habilitada'] else 'NO_HABILITADA', current_user.id, db._ahora_utc(), uid, entrada['periodo_id'], eid))
        if habilitacion_personal(c, uid, entrada['periodo_id'], clave) != entrada['habilitada'] or not c.execute('SELECT 1 FROM habilitaciones_operativas WHERE voluntario_id=? AND periodo_id=? AND clave=?', (uid, entrada['periodo_id'], clave)).fetchone():
            c.execute('INSERT INTO habilitaciones_operativas(voluntario_id,periodo_id,clave,habilitada,registrada_por,registrada_en) VALUES (?,?,?,?,?,?)',
                      (uid, entrada['periodo_id'], clave, int(entrada['habilitada']), current_user.id, db._ahora_utc()))
            db.registrar_auditoria(c, current_user.id, 'HABILITACION_EVALUACION_CAMBIADA', 'EXITOSO')
        c.commit()
    except ValueError as error:
        c.rollback(); return jsonify(error=str(error)), 400
    except (sqlite3.IntegrityError, sqlite3.OperationalError):
        c.rollback(); return jsonify(error='Conflicto al guardar; recarga la tabla.'), 409
    return jsonify(ok=True)


@tabla_bp.get('/mis-evaluaciones')
@role_required('INSTRUCTOR_VOLUNTARIO')
def pagina_propia():
    return render_template('tabla_evaluaciones.html', titulo_pagina='Mis evaluaciones por gestión', nav_activo='tabla_evaluaciones', indicadores=[],
                           periodo_actual=db.periodo_actual(), descripcion='Habilitación y avance de tus evaluaciones. Las notas requieren publicación.')


@tabla_bp.get('/api/evaluaciones/propias')
@role_required('INSTRUCTOR_VOLUNTARIO')
def propias():
    try:
        pid = periodo_solicitado()
        c = db.obtener_conexion()
        c.execute('BEGIN')
        p = c.execute('SELECT id,nombre,estado FROM periodos WHERE id=?', (pid,)).fetchone()
        if p is None:
            raise ValueError('Gestión no encontrada.')
        valores = evaluaciones_persona(c, current_user.id, pid)
        # Ni filas ni denominadores propios revelan estados de Desempeño.
        valores = [e for e in valores if not e['clave'].startswith('DESEMPENO_')]
        # Proyección explícita sin notas, ids de notas, responsables ni observaciones.
        evaluaciones = [{k: e[k] for k in ('clave', 'nombre', 'habilitada', 'activa', 'estado')} for e in valores]
        from .publicaciones_5b import proyeccion
        publicacion = proyeccion(c, current_user.id, pid)
        c.commit()
        respuesta = jsonify(periodo=dict(p), evaluaciones=evaluaciones, resumen=resumen(valores), publicacion=publicacion)
        respuesta.headers['Cache-Control'] = 'private, no-store'
        return respuesta
    except ValueError as error:
        return jsonify(error=str(error)), 400


@tabla_bp.get('/api/evaluaciones/reporte.pdf')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
def reporte():
    from .reportes_evaluaciones import generar_pdf
    c = db.obtener_conexion()
    try:
        c.execute('BEGIN')
        datos = datos_gestion(c, periodo_solicitado())
        c.commit()
    except ValueError as error:
        return jsonify(error=str(error)), 400
    archivo = generar_pdf(datos)
    db.registrar_auditoria(c, current_user.id, 'REPORTE_EVALUACIONES_GENERADO', 'EXITOSO')
    c.commit()
    respuesta = send_file(archivo, mimetype='application/pdf', as_attachment=True, download_name='evaluaciones-gestion.pdf', max_age=0)
    respuesta.headers['Cache-Control'] = 'private, no-store'
    return respuesta
