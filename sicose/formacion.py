"""Estado calendario del catálogo y formación personal con historial."""
import sqlite3
from datetime import date, datetime, timezone, timedelta
from flask import Blueprint, jsonify, request
from flask_login import current_user
from . import db
from .permissions import role_required

formacion_bp = Blueprint('formacion', __name__)
ESTADOS = ('Asignado', 'En curso', 'Finalizado', 'No completado')
TIPOS = ('Capacitación', 'Especialización', 'Actualización', 'Taller', 'Seminario (Webinar)')


def hoy_bolivia():
    return datetime.now(timezone(timedelta(hours=-4))).date()


def fecha(valor):
    if not isinstance(valor, str) or len(valor) != 10 or date.fromisoformat(valor).isoformat() != valor:
        raise ValueError('Fecha no válida; usa una fecha completa.')
    return date.fromisoformat(valor)


def validar_puntaje(valor):
    if type(valor) is not int or not 0 <= valor <= 100:
        raise ValueError('El puntaje debe ser un entero entre 0 y 100.')
    return valor


def proyectar_curso(fila, hoy=None):
    curso = dict(fila)
    curso['estado_historico'] = curso.get('estado')
    try:
        inicio, fin = fecha(curso.get('fecha_inicio')), fecha(curso.get('fecha_fin'))
        if fin < inicio:
            raise ValueError()
    except (ValueError, TypeError):
        curso['estado'] = None
        return curso
    actual = hoy or hoy_bolivia()
    curso['estado'] = 'Próximo' if actual < inicio else 'En curso' if actual <= fin else 'Finalizado'
    return curso


def fallo(mensaje, estado=400):
    return jsonify(error=mensaje, codigo='formacion_invalida'), estado


def historial(c, identificador):
    return [dict(f) for f in c.execute('SELECT revision,estado,puntaje,fecha_finalizacion,motivo,registrada_por,responsable_nombre,registrada_en FROM historial_participaciones_curso WHERE participacion_id=? ORDER BY revision', (identificador,))]


def registrar_version(c, fila, motivo):
    c.execute('INSERT INTO historial_participaciones_curso(participacion_id,revision,estado,puntaje,fecha_finalizacion,motivo,registrada_por,responsable_nombre,registrada_en) VALUES (?,?,?,?,?,?,?,?,?)',
              (fila['id'], fila['revision'], fila['estado'], fila['puntaje'], fila['fecha_finalizacion'], motivo, current_user.id, current_user.nombre, db._ahora_utc()))


@formacion_bp.get('/api/cursos/<int:cid>/participantes')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
def listar(cid):
    c = db.obtener_conexion()
    if not c.execute('SELECT 1 FROM cursos WHERE id=?', (cid,)).fetchone():
        return fallo('Curso no encontrado.', 404)
    filas = c.execute('SELECT p.*,EXISTS(SELECT 1 FROM retiros_curso r WHERE r.participacion_id=p.id) AS retirada,u.nombre_completo AS nombre,u.estado AS cuenta_estado,v.codigo_instructor AS codigo FROM participaciones_curso p JOIN usuarios u ON u.id=p.voluntario_id JOIN voluntarios v ON v.usuario_id=p.voluntario_id WHERE p.curso_id=? ORDER BY u.nombre_completo,p.id', (cid,))
    return jsonify(participantes=[dict(f) for f in filas])


@formacion_bp.post('/api/cursos/<int:cid>/participantes')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
def asignar(cid):
    entrada = request.get_json(silent=True)
    if not isinstance(entrada, dict) or set(entrada) != {'voluntario_ids'}:
        return fallo('Selecciona los Instructores Voluntarios.')
    ids = entrada['voluntario_ids']
    if not isinstance(ids, list) or not 1 <= len(ids) <= 200 or any(type(i) is not int or i < 1 for i in ids) or len(set(ids)) != len(ids):
        return fallo('Selecciona entre 1 y 200 personas, sin repetir.')
    c = db.obtener_conexion()
    try:
        c.execute('BEGIN IMMEDIATE')
        curso = c.execute('SELECT * FROM cursos WHERE id=?', (cid,)).fetchone()
        if c.execute('SELECT 1 FROM bajas_curso WHERE curso_id=?',(cid,)).fetchone(): raise ValueError('El curso está dado de baja.')
        if curso is None:
            c.rollback(); return fallo('Curso no encontrado.', 404)
        if not curso['entidad'] or curso['tipo'] not in TIPOS or not curso['fecha_inicio'] or not curso['fecha_fin'] or curso['puntaje'] is None:
            raise ValueError('Completa entidad, tipo, fechas y puntaje del curso antes de asignar participantes.')
        inicio, fin = fecha(curso['fecha_inicio']), fecha(curso['fecha_fin'])
        if fin < inicio:
            raise ValueError('Fechas del curso incoherentes.')
        validar_puntaje(curso['puntaje'])
        for uid in ids:
            if not c.execute("SELECT 1 FROM voluntarios v JOIN usuarios u ON u.id=v.usuario_id WHERE u.id=? AND u.estado='ACTIVO'", (uid,)).fetchone():
                raise ValueError('Solo puede asignarse personal activo; no se guardó ninguna asignación.')
            identificador = c.execute('INSERT INTO participaciones_curso(curso_id,voluntario_id,nombre_curso,entidad_curso,tipo_curso,inicio_curso,fin_curso,puntaje_base,creado_por,creado_en) VALUES (?,?,?,?,?,?,?,?,?,?)',
                                      (cid, uid, curso['nombre'], curso['entidad'], curso['tipo'], curso['fecha_inicio'], curso['fecha_fin'], curso['puntaje'], current_user.id, db._ahora_utc())).lastrowid
            fila = c.execute('SELECT * FROM participaciones_curso WHERE id=?', (identificador,)).fetchone()
            registrar_version(c, fila, None)
        db.registrar_auditoria(c, current_user.id, 'PARTICIPANTES_CURSO_ASIGNADOS', 'EXITOSO')
        c.commit()
    except ValueError as error:
        c.rollback(); return fallo(str(error))
    except (sqlite3.IntegrityError, sqlite3.OperationalError):
        c.rollback(); return fallo('Hay una asignación duplicada o concurrente; recarga la lista. No se guardaron cambios parciales.', 409)
    return jsonify(ok=True, asignados=len(ids)), 201


@formacion_bp.get('/api/formacion/participaciones/<int:identificador>/historial')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
def consultar_historial(identificador):
    c = db.obtener_conexion()
    if not c.execute('SELECT 1 FROM participaciones_curso WHERE id=?', (identificador,)).fetchone():
        return fallo('Participación no encontrada.', 404)
    return jsonify(historial=historial(c, identificador))


@formacion_bp.patch('/api/formacion/participaciones/<int:identificador>')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
def actualizar(identificador):
    entrada = request.get_json(silent=True)
    if not isinstance(entrada, dict) or set(entrada) - {'revision', 'estado', 'puntaje', 'fecha_finalizacion', 'motivo'} or type(entrada.get('revision')) is not int or entrada.get('revision', 0) < 1 or entrada.get('estado') not in ESTADOS:
        return fallo('Estado y revisión vigentes requeridos.')
    motivo = entrada.get('motivo')
    if not isinstance(motivo, str) or not 1 <= len(motivo.strip()) <= 2000:
        return fallo('Ingresa el motivo del cambio (máximo 2000 caracteres).')
    puntos, finalizacion = entrada.get('puntaje'), entrada.get('fecha_finalizacion')
    try:
        if entrada['estado'] == 'Finalizado':
            validar_puntaje(puntos)
            finalizacion = fecha(finalizacion)
            if finalizacion > hoy_bolivia():
                raise ValueError('La finalización personal no puede ser futura.')
        elif puntos is not None or finalizacion is not None:
            raise ValueError('Puntaje y fecha de finalización solo corresponden a Finalizado; no se asigna cero a pendientes o no completados.')
    except (ValueError, TypeError) as error:
        return fallo(str(error))
    c = db.obtener_conexion()
    try:
        c.execute('BEGIN IMMEDIATE')
        fila = c.execute('SELECT p.*,u.estado AS cuenta_estado FROM participaciones_curso p JOIN usuarios u ON u.id=p.voluntario_id WHERE p.id=?', (identificador,)).fetchone()
        if fila is None:
            c.rollback(); return fallo('Participación no encontrada.', 404)
        if c.execute('SELECT 1 FROM retiros_curso WHERE participacion_id=?',(identificador,)).fetchone(): raise ValueError('La participación fue retirada; su historial está conservado.')
        if c.execute('SELECT 1 FROM bajas_curso WHERE curso_id=?',(fila['curso_id'],)).fetchone(): raise ValueError('El curso está dado de baja; conserva su formación como historial.')
        if fila['cuenta_estado'] != 'ACTIVO':
            c.rollback(); return fallo('Reactiva la cuenta antes de registrar o corregir su formación.', 409)
        if fila['revision'] != entrada['revision']:
            c.rollback(); return fallo('Revisión desactualizada; recarga antes de corregir.', 409)
        if finalizacion is not None and finalizacion < fecha(fila['inicio_curso']):
            raise ValueError('La finalización personal no puede preceder al inicio del curso capturado al asignar.')
        if entrada['estado'] == 'En curso' and hoy_bolivia() < fecha(fila['inicio_curso']):
            raise ValueError('El curso todavía no comenzó.')
        final = finalizacion.isoformat() if finalizacion else None
        if (entrada['estado'], puntos, final) == (fila['estado'], fila['puntaje'], fila['fecha_finalizacion']):
            c.rollback(); return jsonify(ok=True, revision=fila['revision'])
        for dia in (fila['fecha_finalizacion'], final):
            if dia and c.execute("SELECT 1 FROM periodos p JOIN modelos_anuales m ON m.periodo_id=p.id WHERE p.estado='CERRADO' AND ? BETWEEN p.fecha_inicio AND p.fecha_fin",(dia,)).fetchone():
                c.rollback();return fallo('La finalización anterior o nueva pertenece a un período cerrado. Requiere reapertura administrativa.',409)
        # Tanto retirar una imputación anterior como agregar una nueva afecta al año.
        anos = {f[:4] for f in (fila['fecha_finalizacion'], final) if f}
        for ano in anos:
            if c.execute("SELECT 1 FROM periodos p WHERE p.estado='CERRADO' AND substr(p.fecha_inicio,1,4)=? AND p.fecha_inicio=? AND p.fecha_fin=? LIMIT 1", (ano, f'{ano}-01-01', f'{ano}-12-31')).fetchone():
                c.rollback(); return fallo('La finalización anterior o nueva pertenece a una Gestión cerrada. El Administrador debe reabrirla antes de corregir formación.', 409)
        c.execute('UPDATE participaciones_curso SET estado=?,puntaje=?,fecha_finalizacion=?,revision=revision+1 WHERE id=?', (entrada['estado'], puntos, final, identificador))
        actual = c.execute('SELECT * FROM participaciones_curso WHERE id=?', (identificador,)).fetchone()
        registrar_version(c, actual, motivo.strip())
        db.registrar_auditoria(c, current_user.id, 'FORMACION_PERSONAL_ACTUALIZADA', 'EXITOSO')
        c.commit()
    except ValueError as error:
        c.rollback(); return fallo(str(error))
    except (sqlite3.IntegrityError, sqlite3.OperationalError):
        c.rollback(); return fallo('Conflicto al guardar la participación. Recarga su historial.', 409)
    return jsonify(ok=True, revision=actual['revision'])


@formacion_bp.get('/api/instructor-voluntario/formacion')
@role_required('INSTRUCTOR_VOLUNTARIO')
def propias():
    if request.args:
        return fallo("La consulta de formación es propia y no admite seleccionar otra persona.")
    # Datos vigentes sin puntos; valores numéricos solo en versiones publicadas propias.
    c = db.obtener_conexion()
    c.execute("BEGIN")
    filas = c.execute('SELECT id,curso_id,nombre_curso,entidad_curso,tipo_curso,inicio_curso,fin_curso,estado,fecha_finalizacion FROM participaciones_curso WHERE voluntario_id=? ORDER BY inicio_curso DESC,id DESC', (current_user.id,))
    participaciones = [dict(f) for f in filas]
    from .publicaciones_5b import proyeccion
    publicaciones = []
    for p in c.execute("SELECT DISTINCT p.periodo_id,substr(g.fecha_inicio,1,4) AS gestion FROM publicaciones_5b p JOIN periodos g ON g.id=p.periodo_id WHERE p.voluntario_id=? ORDER BY gestion DESC", (current_user.id,)):
        valor = proyeccion(c, current_user.id, p["periodo_id"])
        if valor and valor["academica"] is not None:
            publicaciones.append({"periodo_id": p["periodo_id"], "gestion": p["gestion"], "academica": valor["academica"]})
    c.commit()
    respuesta = jsonify(participaciones=participaciones, publicaciones=publicaciones)
    respuesta.headers['Cache-Control'] = 'private, no-store'
    return respuesta
