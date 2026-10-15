"""Reapertura excepcional: evidencia actual sin reconstruir un cierre antiguo."""
import json
import sqlite3
from flask import Blueprint, jsonify, request
from flask_login import current_user
from . import db
from .permissions import role_required
from .cierres_5b import preparar, serializar

historicos_bp = Blueprint('historicos_5b', __name__)


@historicos_bp.after_request
def privada(respuesta):
    respuesta.headers['Cache-Control'] = 'private, no-store'
    return respuesta


@historicos_bp.get('/api/5b/periodos/<int:pid>/reapertura-historica-previa')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
def vista(pid):
    c = db.obtener_conexion()
    try:
        c.execute('BEGIN')
        contenido, firma = preparar(c, pid, documental=True)
        c.commit()
        return jsonify(**contenido, firma_fuentes=firma)
    except (LookupError, ValueError) as error:
        c.rollback(); return jsonify(error=str(error)), 404 if isinstance(error, LookupError) else 409


@historicos_bp.get('/api/5b/periodos/<int:pid>/reapertura-historica')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
def evidencia(pid):
    c = db.obtener_conexion()
    f = c.execute('SELECT * FROM reaperturas_historicas_5b WHERE periodo_id=?', (pid,)).fetchone()
    if not f:
        return jsonify(error='No existe evidencia de reapertura histórica en esta Gestión.'), 404
    valor = dict(f); valor['evidencia'] = json.loads(valor.pop('contenido_json'))
    return jsonify(reapertura=valor)


@historicos_bp.post('/api/admin/5b/periodos/<int:pid>/reabrir-historico')
@role_required('ADMINISTRADOR')
def reabrir(pid):
    datos = request.get_json(silent=True)
    if (not isinstance(datos, dict) or set(datos) != {'motivo', 'firma_fuentes', 'confirmar_sin_instantanea'}
            or not isinstance(datos['motivo'], str) or not 1 <= len(datos['motivo'].strip()) <= 2000
            or not isinstance(datos['firma_fuentes'], str) or datos['confirmar_sin_instantanea'] is not True):
        return jsonify(error='Motivo, firma y confirmación expresa de ausencia de instantánea original requeridos.'), 400
    c = db.obtener_conexion()
    try:
        c.execute('BEGIN IMMEDIATE')
        contenido, firma = preparar(c, pid, documental=True)
        if firma != datos['firma_fuentes']:
            raise ValueError('La evidencia cambió; revisa de nuevo antes de reabrir.')
        if c.execute("SELECT 1 FROM periodos WHERE estado='ACTIVO' AND id!=? AND NOT EXISTS(SELECT 1 FROM bajas_gestion b WHERE b.periodo_id=periodos.id)", (pid,)).fetchone():
            raise ValueError('Ya existe otra Gestión activa; no se cerrará automáticamente.')
        rid = c.execute('''INSERT INTO reaperturas_historicas_5b(periodo_id,contenido_json,firma_fuentes,motivo,actor_id,actor_nombre,registrada_en)
                           VALUES (?,?,?,?,?,?,?)''', (pid, serializar(contenido), firma, datos['motivo'].strip(), current_user.id, current_user.nombre, db._ahora_utc())).lastrowid
        c.execute("UPDATE periodos SET estado='ACTIVO' WHERE id=?", (pid,))
        db.registrar_auditoria(c, current_user.id, f'GESTION_HISTORICA_REABIERTA:{pid}:{rid}', 'EXITOSO')
        c.commit()
        return jsonify(ok=True, reapertura_historica_id=rid), 201
    except (LookupError, ValueError) as error:
        c.rollback(); return jsonify(error=str(error)), 404 if isinstance(error, LookupError) else 409
    except (sqlite3.IntegrityError, sqlite3.OperationalError):
        c.rollback(); return jsonify(error='Reapertura concurrente; recarga la Gestión.'), 409
