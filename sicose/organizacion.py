"""Bajas conservadoras y eliminación de gestiones sin resultados."""
import sqlite3
from flask import Blueprint, request, jsonify
from flask_login import current_user
from . import db
from .permissions import role_required

organizacion_bp = Blueprint('organizacion', __name__)


def razon(d):
    if not isinstance(d, dict) or not isinstance(d.get('motivo'), str) or not 1 <= len(d['motivo'].strip()) <= 2000:
        raise ValueError('Motivo obligatorio, máximo 2000 caracteres.')
    return d['motivo'].strip()


@organizacion_bp.delete('/api/gestiones/<int:pid>/eliminar')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
def eliminar_gestion(pid):
    c = db.obtener_conexion()
    try:
        d = request.get_json(silent=True); motivo = razon(d)
        if set(d) != {'motivo', 'nombre_anterior', 'estado_anterior'}:
            raise ValueError('Nombre y estado anteriores requeridos.')
        c.execute('BEGIN IMMEDIATE')
        p = c.execute('SELECT * FROM periodos WHERE id=?', (pid,)).fetchone()
        if p is None: c.rollback(); return jsonify(error='Gestión no encontrada.'), 404
        if (p['nombre'], p['estado']) != (d['nombre_anterior'], d['estado_anterior']):
            raise ValueError('La Gestión cambió. Recarga antes de eliminar.')
        # Las notas iniciales oficiales son resultados. Tampoco se destruye evidencia
        # publicada, congelada o histórica aunque no haya una nota manual.
        for row in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
            tabla = row[0]
            if tabla in ('modelos_anuales', 'eventos_modelo_anual'): continue
            for fk in c.execute('PRAGMA foreign_key_list("' + tabla.replace('"', '""') + '")'):
                if fk['table'] == 'periodos' and fk['to'] == 'id':
                    col = fk['from'].replace('"', '""')
                    if c.execute('SELECT 1 FROM "' + tabla.replace('"', '""') + '" WHERE "' + col + '"=? LIMIT 1', (pid,)).fetchone():
                        raise ValueError('La Gestión tiene resultados o evidencia vinculada; conserva su historial.')
        if c.execute('SELECT 1 FROM personas_modelo_anual WHERE periodo_id=?', (pid,)).fetchone():
            raise ValueError('La Gestión contiene calificaciones oficiales; no puede eliminarse.')
        c.execute('DELETE FROM eventos_modelo_anual WHERE periodo_id=?', (pid,))
        c.execute('DELETE FROM modelos_anuales WHERE periodo_id=?', (pid,))
        c.execute('DELETE FROM periodos WHERE id=?', (pid,))
        db.registrar_auditoria(c, current_user.id, f'GESTION_ELIMINADA:{pid}:{p["nombre"]}:{motivo}', 'EXITOSO')
        c.commit(); return jsonify(ok=True)
    except (ValueError, sqlite3.IntegrityError, sqlite3.OperationalError) as e:
        c.rollback(); return jsonify(error=str(e) if isinstance(e, ValueError) else 'La Gestión tiene evidencia protegida o cambió. Recarga.'), 409


@organizacion_bp.delete('/api/cursos/<int:cid>')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
def eliminar_curso(cid):
    c = db.obtener_conexion()
    try:
        motivo = razon(request.get_json(silent=True)); c.execute('BEGIN IMMEDIATE')
        curso = c.execute('SELECT * FROM cursos WHERE id=?', (cid,)).fetchone()
        if curso is None: c.rollback(); return jsonify(error='Curso no encontrado.'), 404
        if c.execute('SELECT 1 FROM bajas_curso WHERE curso_id=?', (cid,)).fetchone():
            raise ValueError('El curso ya está dado de baja.')
        vinculado = c.execute('SELECT 1 FROM participaciones_curso WHERE curso_id=?', (cid,)).fetchone() or c.execute('SELECT 1 FROM capacitaciones WHERE curso_id=?', (cid,)).fetchone()
        if vinculado:
            c.execute('INSERT INTO bajas_curso VALUES (?,?,?,?,?)', (cid, motivo, current_user.id, current_user.nombre, db._ahora_utc()))
        else: c.execute('DELETE FROM cursos WHERE id=?', (cid,))
        db.registrar_auditoria(c, current_user.id, f'CURSO_{"BAJA" if vinculado else "ELIMINADO"}:{cid}', 'EXITOSO')
        c.commit(); return jsonify(ok=True, baja=bool(vinculado))
    except (ValueError, sqlite3.IntegrityError, sqlite3.OperationalError) as e:
        c.rollback(); return jsonify(error=str(e) if isinstance(e, ValueError) else 'Conflicto al retirar el curso. Recarga.'), 409


@organizacion_bp.post('/api/cursos/<int:cid>/retirar-participantes')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
def retirar_participantes(cid):
    c = db.obtener_conexion()
    try:
        d = request.get_json(silent=True); motivo = razon(d)
        items = d.get('participaciones')
        if set(d) != {'motivo', 'participaciones'} or not isinstance(items, list) or not 1 <= len(items) <= 200:
            raise ValueError('Selecciona entre 1 y 200 participaciones con su revisión.')
        if any(not isinstance(i, dict) or set(i) != {'id', 'revision'} or any(type(i[k]) is not int for k in i) for i in items) or len({i['id'] for i in items}) != len(items):
            raise ValueError('Participaciones y revisiones inválidas o repetidas.')
        c.execute('BEGIN IMMEDIATE')
        from .formacion import registrar_version
        for item in items:
            p = c.execute('SELECT * FROM participaciones_curso WHERE curso_id=? AND id=?', (cid, item['id'])).fetchone()
            if p is None or p['revision'] != item['revision'] or c.execute('SELECT 1 FROM retiros_curso WHERE participacion_id=?', (item['id'],)).fetchone():
                raise ValueError('Una participación cambió o ya fue retirada. No se guardaron cambios parciales.')
            if not c.execute("SELECT 1 FROM usuarios WHERE id=? AND estado='ACTIVO'", (p['voluntario_id'],)).fetchone():
                raise ValueError('Reactiva la cuenta antes de modificar su formación.')
            dia = p['fecha_finalizacion']
            if dia and c.execute("SELECT 1 FROM periodos WHERE estado='CERRADO' AND ? BETWEEN fecha_inicio AND fecha_fin", (dia,)).fetchone():
                raise ValueError('El puntaje pertenece a una Gestión cerrada; requiere reapertura administrativa.')
            c.execute('INSERT INTO retiros_curso VALUES (?,?,?,?,?)', (p['id'], motivo, current_user.id, current_user.nombre, db._ahora_utc()))
            c.execute("UPDATE participaciones_curso SET estado='No completado',puntaje=NULL,fecha_finalizacion=NULL,revision=revision+1 WHERE id=?", (p['id'],))
            registrar_version(c, c.execute('SELECT * FROM participaciones_curso WHERE id=?', (p['id'],)).fetchone(), 'Retirada: ' + motivo)
        db.registrar_auditoria(c, current_user.id, 'PARTICIPANTES_CURSO_RETIRADOS', 'EXITOSO')
        c.commit(); return jsonify(ok=True, retirados=len(items))
    except (ValueError, sqlite3.IntegrityError, sqlite3.OperationalError) as e:
        c.rollback(); return jsonify(error=str(e) if isinstance(e, ValueError) else 'Conflicto concurrente. Recarga.'), 409
