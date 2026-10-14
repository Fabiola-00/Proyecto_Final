"""Baja lógica de gestiones y activación anual, separada de habilitación personal."""
import sqlite3
from flask import Blueprint, jsonify, request
from flask_login import current_user
from . import db
from .permissions import role_required

gestiones_bp = Blueprint('gestiones', __name__)
NOMBRES = {'FISICA_1': 'Física 1', 'FISICA_2': 'Física 2', 'ACADEMICA': 'Académica',
           'DESEMPENO_JEFE': 'Desempeño del Jefe', 'DESEMPENO_COMANDANTE': 'Desempeño del Comandante',
           'PSICOMETRICAS': 'Psicométricas'}


def retirada(c, pid):
    return c.execute('SELECT 1 FROM bajas_gestion WHERE periodo_id=?', (pid,)).fetchone() is not None


def revision(c, pid, clave):
    return c.execute('SELECT * FROM activaciones_gestion WHERE periodo_id=? AND clave=? ORDER BY id DESC LIMIT 1', (pid, clave)).fetchone()


def psicometria_aprobada(c):
    return bool(c.execute("SELECT 1 FROM evaluaciones e JOIN instrumentos i ON i.id=e.instrumento_id WHERE e.categoria='PSICOMETRICA' AND e.activo=1 AND i.estado_aprobacion='APROBADO'").fetchone())


def activa(c, pid, clave):
    if retirada(c, pid):
        return False
    clave = 'PSICOMETRICAS' if clave.startswith('PSICO:') else clave
    fila = revision(c, pid, clave)
    return bool(fila['activa']) if fila else psicometria_aprobada(c) if clave == 'PSICOMETRICAS' else clave in NOMBRES


def estado_evaluaciones(c, pid):
    valores = []
    for clave, nombre in NOMBRES.items():
        fila = revision(c, pid, clave)
        valores.append({'clave': clave, 'nombre': nombre, 'activa': activa(c, pid, clave),
                        'revision': fila['id'] if fila else 0,
                        'disponible': clave != 'PSICOMETRICAS' or psicometria_aprobada(c)})
    return valores


@gestiones_bp.get('/api/5b/gestiones/<int:pid>/evaluaciones')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
def consultar(pid):
    c = db.obtener_conexion()
    if not c.execute('SELECT 1 FROM periodos WHERE id=?', (pid,)).fetchone():
        return jsonify(error='Gestión no encontrada.'), 404
    return jsonify(evaluaciones=estado_evaluaciones(c, pid), retirada=retirada(c, pid),
                   historial=[dict(r) for r in c.execute('SELECT * FROM activaciones_gestion WHERE periodo_id=? ORDER BY id', (pid,))])


@gestiones_bp.patch('/api/5b/gestiones/<int:pid>/evaluaciones/<clave>')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
def cambiar(pid, clave):
    datos = request.get_json(silent=True)
    if clave not in NOMBRES or not isinstance(datos, dict) or set(datos) != {'activa', 'revision', 'motivo'} or type(datos['activa']) is not bool or type(datos['revision']) is not int or datos['revision'] < 0 or not isinstance(datos['motivo'], str) or not 1 <= len(datos['motivo'].strip()) <= 2000:
        return jsonify(error='Evaluación, estado, revisión y motivo requeridos.'), 400
    c = db.obtener_conexion()
    try:
        c.execute('BEGIN IMMEDIATE')
        p = c.execute('SELECT estado FROM periodos WHERE id=?', (pid,)).fetchone()
        if p is None:
            c.rollback(); return jsonify(error='Gestión no encontrada.'), 404
        if retirada(c, pid) or p['estado'] not in ('BORRADOR', 'ACTIVO'):
            c.rollback(); return jsonify(error='Gestión retirada o cerrada: solo consulta.'), 409
        ultima = revision(c, pid, clave)
        rid = ultima['id'] if ultima else 0
        if rid != datos['revision']:
            c.rollback(); return jsonify(error='La activación cambió; recarga la gestión.'), 409
        if clave == 'PSICOMETRICAS' and datos['activa'] and not psicometria_aprobada(c):
            c.rollback(); return jsonify(error='No hay instrumento aprobado y activo. Los formularios psicométricos continúan bloqueados.'), 409
        if ultima and bool(ultima['activa']) == datos['activa']:
            c.rollback(); return jsonify(ok=True, revision=rid)
        nid = c.execute('INSERT INTO activaciones_gestion(periodo_id,clave,activa,motivo,anterior_id,actor_id,actor_nombre,registrada_en) VALUES (?,?,?,?,?,?,?,?)',
                        (pid, clave, int(datos['activa']), datos['motivo'].strip(), rid or None, current_user.id, current_user.nombre, db._ahora_utc())).lastrowid
        db.registrar_auditoria(c, current_user.id, 'EVALUACION_GESTION_ACTIVADA' if datos['activa'] else 'EVALUACION_GESTION_DESACTIVADA', 'EXITOSO')
        c.commit()
        return jsonify(ok=True, revision=nid)
    except (sqlite3.IntegrityError, sqlite3.OperationalError):
        c.rollback(); return jsonify(error='Conflicto de activación; recarga.'), 409


@gestiones_bp.delete('/api/admin/5b/periodos/<int:pid>')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
def eliminar(pid):
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict) or set(datos) != {'motivo', 'nombre_anterior', 'ano_anterior', 'estado_anterior'} or not isinstance(datos['motivo'], str) or not 1 <= len(datos['motivo'].strip()) <= 2000 or type(datos['ano_anterior']) is not int:
        return jsonify(error='Motivo y valores vigentes de la gestión requeridos.'), 400
    c = db.obtener_conexion()
    try:
        c.execute('BEGIN IMMEDIATE')
        p = c.execute('SELECT * FROM periodos WHERE id=?', (pid,)).fetchone()
        if p is None:
            c.rollback(); return jsonify(error='Gestión no encontrada.'), 404
        if retirada(c, pid) or (datos['nombre_anterior'], datos['ano_anterior'], datos['estado_anterior']) != (p['nombre'], int(p['fecha_inicio'][:4]), p['estado']):
            c.rollback(); return jsonify(error='Gestión retirada o modificada; recarga.'), 409
        c.execute('INSERT INTO bajas_gestion(periodo_id,motivo,actor_id,actor_nombre,registrada_en) VALUES (?,?,?,?,?)', (pid, datos['motivo'].strip(), current_user.id, current_user.nombre, db._ahora_utc()))
        db.registrar_auditoria(c, current_user.id, 'GESTION_RETIRADA', 'EXITOSO')
        c.commit()
        return jsonify(ok=True)
    except (sqlite3.IntegrityError, sqlite3.OperationalError):
        c.rollback(); return jsonify(error='Conflicto al retirar la gestión; recarga.'), 409
