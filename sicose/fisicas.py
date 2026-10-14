"""Programación física versionada; no convierte notas históricas."""
import sqlite3
from datetime import date, datetime, timedelta, timezone

from flask import Blueprint, jsonify, request
from flask_login import current_user

from . import db
from .permissions import role_required

fisicas_bp = Blueprint('fisicas', __name__)
FUENTES = ('FISICA_1', 'FISICA_2')


def hoy():
    return datetime.now(timezone(timedelta(hours=-4))).date()


def fecha(valor, periodo):
    if not isinstance(valor, str):
        raise ValueError('Fecha obligatoria en formato AAAA-MM-DD.')
    try:
        dia = date.fromisoformat(valor)
    except ValueError:
        raise ValueError('Fecha no válida.') from None
    if dia.isoformat() != valor or not periodo['fecha_inicio'] <= valor <= periodo['fecha_fin']:
        raise ValueError('La fecha debe pertenecer a la gestión anual.')
    return dia


def vigente(c, pid, fuente, uid=None):
    comun = c.execute('SELECT * FROM programaciones_fisicas WHERE periodo_id=? AND fuente=? ORDER BY id DESC LIMIT 1', (pid, fuente)).fetchone()
    individual = c.execute('SELECT * FROM reprogramaciones_fisicas WHERE periodo_id=? AND fuente=? AND voluntario_id=? ORDER BY id DESC LIMIT 1', (pid, fuente, uid)).fetchone() if uid is not None else None
    return {'comun': dict(comun) if comun else None, 'individual': dict(individual) if individual else None,
            'fecha_prevista': individual['fecha'] if individual else comun['fecha'] if comun else None}


def periodo_activo(c, pid):
    from .periodos_5b import anual
    p = c.execute('SELECT * FROM periodos WHERE id=?', (pid,)).fetchone()
    if p is None:
        raise ValueError('Gestión no encontrada.')
    from .gestiones import retirada
    if retirada(c, pid) or p['estado'] != 'ACTIVO' or not anual(p) or not c.execute("SELECT 1 FROM configuraciones_5b WHERE periodo_id=? AND estado='PUBLICADA'", (pid,)).fetchone():
        raise Conflicto('Requiere gestión anual activa y configuración publicada.')
    return p


class Conflicto(ValueError):
    pass


def validar_resultado(c, uid, pid, fuente, datos, puntos):
    """Se ejecuta dentro de la transacción serializada de notas."""
    agenda = vigente(c, pid, fuente, uid)
    # El circuito manual anterior permanece separado hasta programar explícitamente.
    if not agenda['comun'] and datos is None:
        return None
    if not agenda['comun']:
        raise Conflicto('Programa primero la fecha común de esta prueba.')
    if not isinstance(datos, dict) or set(datos) != {'estado', 'fecha_realizacion', 'programacion_id', 'reprogramacion_id'}:
        raise ValueError('Indica estado físico, fecha realizada y versiones de programación.')
    if type(datos['programacion_id']) is not int or datos['programacion_id'] != agenda['comun']['id'] or (datos['reprogramacion_id'] is not None and type(datos['reprogramacion_id']) is not int) or datos['reprogramacion_id'] != (agenda['individual']['id'] if agenda['individual'] else None):
        raise Conflicto('La programación cambió; recarga antes de registrar el resultado.')
    p = periodo_activo(c, pid)
    if datos['estado'] == 'NO_CUMPLIDA':
        if puntos != 0 or datos['fecha_realizacion'] is not None:
            raise ValueError('No cumplida exige cero y no tiene fecha de realización.')
        if agenda['fecha_prevista'] > hoy().isoformat():
            raise Conflicto('No se confirma incumplimiento antes de la fecha prevista.')
    elif datos['estado'] == 'CUMPLIDA':
        if fecha(datos['fecha_realizacion'], p) > hoy():
            raise ValueError('La fecha de realización no puede ser futura.')
    else:
        raise ValueError('Estado físico no válido.')
    return datos


@fisicas_bp.get('/api/5b/periodos/<int:pid>/fisicas')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
def consultar(pid):
    c = db.obtener_conexion()
    if not c.execute('SELECT 1 FROM periodos WHERE id=?', (pid,)).fetchone():
        return jsonify(error='Gestión no encontrada.'), 404
    return jsonify(pruebas={f: vigente(c, pid, f) for f in FUENTES},
                   historial=[dict(r) for r in c.execute('SELECT * FROM programaciones_fisicas WHERE periodo_id=? ORDER BY id', (pid,))])


@fisicas_bp.post('/api/5b/periodos/<int:pid>/fisicas/<fuente>')
@fisicas_bp.post('/api/5b/periodos/<int:pid>/fisicas/<fuente>/personas/<int:uid>')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
def programar(pid, fuente, uid=None):
    entrada = request.get_json(silent=True)
    campos = {'fecha', 'motivo', 'anterior_id'} | ({'programacion_id'} if uid is not None else set())
    if fuente not in FUENTES or not isinstance(entrada, dict) or set(entrada) != campos or not isinstance(entrada['motivo'], str) or not 1 <= len(entrada['motivo'].strip()) <= 2000 or (entrada['anterior_id'] is not None and (type(entrada['anterior_id']) is not int or entrada['anterior_id'] < 1)):
        return jsonify(error='Prueba, motivo o revisión no válidos.'), 400
    c = db.obtener_conexion()
    try:
        c.execute('BEGIN IMMEDIATE')
        p = periodo_activo(c, pid)
        from .gestiones import activa
        if not activa(c, pid, fuente):
            raise Conflicto("La evaluación está desactivada en esta gestión.")
        fecha(entrada['fecha'], p)
        agenda = vigente(c, pid, fuente, uid)
        anterior = agenda['individual' if uid is not None else 'comun']
        if entrada['anterior_id'] != (anterior['id'] if anterior else None):
            raise Conflicto('La fecha cambió; recarga su versión vigente.')
        if uid is not None:
            from .seguimiento_5b import persona
            from .tabla_evaluaciones import habilitada
            perfil = persona(c, uid)
            if perfil is None:
                raise ValueError('Persona no encontrada.')
            if perfil['estado'] != 'ACTIVO' or not habilitada(c, uid, pid, fuente):
                raise Conflicto('La persona debe estar activa y habilitada.')
            if not agenda['comun'] or type(entrada['programacion_id']) is not int or entrada['programacion_id'] != agenda['comun']['id']:
                raise Conflicto('Recarga la programación común vigente.')
        if anterior and anterior['fecha'] == entrada['fecha']:
            c.rollback()
            return jsonify(ok=True, id=anterior['id'])
        valores = (pid, fuente, entrada['fecha'], entrada['motivo'].strip(), entrada['anterior_id'], current_user.id, current_user.nombre, db._ahora_utc())
        if uid is not None:
            nid = c.execute('INSERT INTO reprogramaciones_fisicas(periodo_id,fuente,fecha,motivo,anterior_id,actor_id,actor_nombre,modificada_en,voluntario_id,programacion_id,fecha_anterior) VALUES (?,?,?,?,?,?,?,?,?,?,?)', (*valores, uid, agenda['comun']['id'], agenda['fecha_prevista'])).lastrowid
        else:
            nid = c.execute('INSERT INTO programaciones_fisicas(periodo_id,fuente,fecha,motivo,anterior_id,actor_id,actor_nombre,modificada_en) VALUES (?,?,?,?,?,?,?,?)', valores).lastrowid
        db.registrar_auditoria(c, current_user.id, 'FISICA_REPROGRAMADA' if uid is not None else 'FISICA_PROGRAMADA', 'EXITOSO')
        c.commit()
        return jsonify(ok=True, id=nid), 201
    except (Conflicto, sqlite3.IntegrityError, sqlite3.OperationalError) as error:
        c.rollback()
        return jsonify(error=str(error) if isinstance(error, Conflicto) else 'Conflicto de programación; recarga antes de reintentar.'), 409
    except ValueError as error:
        c.rollback()
        return jsonify(error=str(error)), 400
