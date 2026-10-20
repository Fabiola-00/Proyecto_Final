"""Tipos, estados y baja histórica de operaciones sin destruir evidencia."""
import sqlite3
from flask import Blueprint, jsonify, request
from flask_login import current_user
from . import db
from .permissions import role_required

TIPOS = ('Preventivo','Reactivo','Especial','Emergencia')
ESTADOS = ('Planificación','En ejecución','Finalizado','Suspendido')
operaciones_bp = Blueprint('operaciones',__name__)


def baja(c, oid):
    return c.execute('SELECT 1 FROM bajas_operacion WHERE operacion_id=?',(oid,)).fetchone() is not None


@operaciones_bp.post('/api/operaciones/<int:oid>/retirar-participantes')
@role_required('ADMINISTRADOR','JEFE_PERSONAL')
def retirar(oid):
    c=db.obtener_conexion();d=request.get_json(silent=True)
    if (not isinstance(d,dict) or set(d)!={'motivo','participaciones'} or not isinstance(d['motivo'],str)
            or not 1<=len(d['motivo'].strip())<=2000 or not isinstance(d['participaciones'],list)
            or not 1<=len(d['participaciones'])<=200):
        return jsonify(error='Selecciona participantes e ingresa el motivo.'),400
    items=d['participaciones']
    if (any(not isinstance(i,dict) or set(i)!={'voluntario_id','revision'} or any(type(v) is not int for v in i.values()) for i in items)
            or len({i['voluntario_id'] for i in items})!=len(items)):
        return jsonify(error='Participantes o revisiones inválidos.'),400
    try:
        c.execute('BEGIN IMMEDIATE')
        if not c.execute('SELECT 1 FROM operaciones WHERE id=?',(oid,)).fetchone():
            c.rollback();return jsonify(error='Operación no encontrada.'),404
        if baja(c,oid):raise ValueError('La operación está dada de baja.')
        for i in items:
            p=c.execute('SELECT revision FROM participaciones_operacion WHERE operacion_id=? AND voluntario_id=?',(oid,i['voluntario_id'])).fetchone()
            if (p is None or p['revision']!=i['revision'] or c.execute('SELECT 1 FROM retiros_operacion_vigentes WHERE operacion_id=? AND voluntario_id=?',(oid,i['voluntario_id'])).fetchone()):
                raise ValueError('Una participación cambió o ya fue retirada. No se guardaron cambios parciales.')
            if not c.execute("SELECT 1 FROM usuarios WHERE id=? AND estado='ACTIVO'",(i['voluntario_id'],)).fetchone():
                raise ValueError('Reactiva la cuenta antes de retirar su participación.')
            if c.execute("SELECT 1 FROM notas_operacion_anual n JOIN periodos p ON p.id=n.periodo_id WHERE n.operacion_id=? AND n.voluntario_id=? AND p.estado='CERRADO'",(oid,i['voluntario_id'])).fetchone():
                raise ValueError('La participación tiene notas en una Gestión cerrada; requiere reapertura administrativa.')
            if not c.execute('SELECT 1 FROM retiros_operacion WHERE operacion_id=? AND voluntario_id=?',(oid,i['voluntario_id'])).fetchone():
                c.execute('INSERT INTO retiros_operacion VALUES (?,?,?,?,?,?)',(oid,i['voluntario_id'],d['motivo'].strip(),current_user.id,current_user.nombre,db._ahora_utc()))
            c.execute('INSERT INTO movimientos_participacion_operacion VALUES (?,?,?,?,?,?,?,?)',(oid,i['voluntario_id'],p['revision']+1,'RETIRO',d['motivo'].strip(),current_user.id,current_user.nombre,db._ahora_utc()))
            c.execute('UPDATE participaciones_operacion SET revision=revision+1 WHERE operacion_id=? AND voluntario_id=?',(oid,i['voluntario_id']))
        db.registrar_auditoria(c,current_user.id,f'PARTICIPANTES_OPERACION_RETIRADOS:{oid}','EXITOSO')
        c.commit();return jsonify(ok=True,retirados=len(items))
    except (ValueError,sqlite3.IntegrityError,sqlite3.OperationalError) as error:
        c.rollback();return jsonify(error=str(error) if isinstance(error,ValueError) else 'Conflicto concurrente; recarga.'),409


@operaciones_bp.delete('/api/operaciones/<int:oid>')
@role_required('ADMINISTRADOR','JEFE_PERSONAL')
def eliminar(oid):
    c=db.obtener_conexion();d=request.get_json(silent=True)
    if (not isinstance(d,dict) or set(d)!={'revision','motivo'} or type(d['revision']) is not int
            or not isinstance(d['motivo'],str) or not 1<=len(d['motivo'].strip())<=2000):
        return jsonify(error='Revisión vigente y motivo de eliminación requeridos.'),400
    try:
        c.execute('BEGIN IMMEDIATE')
        o=c.execute('SELECT revision FROM operaciones WHERE id=?',(oid,)).fetchone()
        if o is None:c.rollback();return jsonify(error='Operación no encontrada.'),404
        if o['revision']!=d['revision'] or baja(c,oid):
            raise ValueError('La operación cambió o ya está dada de baja. Recarga.')
        vinculos=bool(c.execute('SELECT 1 FROM participaciones_operacion WHERE operacion_id=?',(oid,)).fetchone()
                      or c.execute('SELECT 1 FROM notas_operacion_anual WHERE operacion_id=?',(oid,)).fetchone())
        if vinculos:
            c.execute('INSERT INTO bajas_operacion VALUES (?,?,?,?,?)',(oid,d['motivo'].strip(),current_user.id,current_user.nombre,db._ahora_utc()))
        else:
            c.execute('DELETE FROM operaciones WHERE id=?',(oid,))
        db.registrar_auditoria(c,current_user.id,f'OPERACION_{"BAJA" if vinculos else "ELIMINADA"}:{oid}','EXITOSO')
        c.commit();return jsonify(ok=True,baja=vinculos)
    except (ValueError,sqlite3.IntegrityError,sqlite3.OperationalError) as error:
        c.rollback();return jsonify(error=str(error) if isinstance(error,ValueError) else 'Conflicto al eliminar; la evidencia se conserva. Recarga.'),409
