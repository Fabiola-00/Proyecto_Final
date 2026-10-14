"""Catálogo, asistencias, calificaciones y resúmenes de evaluación por rol."""

import math
import sqlite3
from datetime import date, datetime, timezone

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user

from . import db
from .permissions import role_required

evaluations_bp = Blueprint("evaluations", __name__)
CATEGORIAS = {"PSICOMETRICA", "FISICA", "ACADEMICA", "JEFE_PERSONAL"}


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _bad(message, code="datos_invalidos", status=400):
    return jsonify(error=message, codigo=code), status


def _json():
    value = request.get_json(silent=True)
    return value if isinstance(value, dict) else None


def _audit(connection, action):
    db.registrar_auditoria(connection, current_user.id, action, "EXITOSO", request.remote_addr)


def _authorized_assignment(connection, assignment_id):
    sql = """SELECT a.id, a.voluntario_id, a.periodo_id, a.evaluacion_id, a.estado,
                    e.codigo, e.nombre AS evaluacion, e.categoria, e.activo,
                    i.estado_aprobacion AS estado_instrumento, p.estado AS periodo_estado,
                    u.nombre_completo AS voluntario, u.estado AS cuenta_estado, v.instructor_id
             FROM asignaciones_evaluacion a
             JOIN evaluaciones e ON e.id=a.evaluacion_id
             JOIN voluntarios v ON v.usuario_id=a.voluntario_id
             JOIN usuarios u ON u.id=v.usuario_id
             JOIN periodos p ON p.id=a.periodo_id
             LEFT JOIN instrumentos i ON i.id=e.instrumento_id
             WHERE a.id=? AND u.estado IN ('ACTIVO','INACTIVO')"""
    row = connection.execute(sql, (assignment_id,)).fetchone()
    if row and current_user.rol == "INSTRUCTOR_VOLUNTARIO" and row["voluntario_id"] != current_user.id:
        return None
    from .gestiones import retirada
    if row and request.method != "GET" and retirada(connection, row["periodo_id"]):
        return None
    return row


@evaluations_bp.get("/gestion/evaluaciones")
@role_required("ADMINISTRADOR", "JEFE_PERSONAL")
def pagina_catalogo():
    return render_template("gestion_evaluaciones.html", titulo_pagina="Catálogo de evaluaciones",
                           nav_activo="evaluaciones", indicadores=[],
                           descripcion="Catálogo común de evaluaciones; la activación por año se administra en Gestiones.",
                           periodo_actual=db.periodo_actual())


@evaluations_bp.get("/gestion/asistencias")
@role_required("ADMINISTRADOR", "JEFE_PERSONAL")
def pagina_asistencias():
    return render_template("gestion_asistencias.html", titulo_pagina="Asistencias",
                           nav_activo="asistencias", indicadores=[],
                           descripcion="Registra y consulta la asistencia de tu equipo.",
                           periodo_actual=db.periodo_actual())


@evaluations_bp.get("/gestion/capacitaciones")
@role_required("ADMINISTRADOR", "JEFE_PERSONAL")
def pagina_capacitaciones():
    return render_template("gestion_capacitaciones.html", titulo_pagina="Capacitaciones y Cursos",
                           nav_activo="capacitaciones", indicadores=[],
                           descripcion="Registra y edita cursos; genera reportes del catálogo.",
                           periodo_actual=db.periodo_actual())


@evaluations_bp.get("/gestion/calificaciones")
@role_required("ADMINISTRADOR", "JEFE_PERSONAL")
def pagina_calificaciones():
    return render_template("gestion_calificaciones.html", titulo_pagina="Notas e historial",
                           nav_activo="calificaciones", indicadores=[],
                           descripcion="Registra y consulta notas no psicométricas e historial.",
                           periodo_actual=db.periodo_actual())


@evaluations_bp.get("/api/admin/evaluaciones")
@role_required("ADMINISTRADOR", "JEFE_PERSONAL")
def listar_evaluaciones():
    rows = db.obtener_conexion().execute(
        """SELECT e.id,e.codigo,e.nombre,e.categoria,e.origen_nota,e.instrumento_id,
                  e.activo,i.estado_aprobacion AS estado_instrumento
           FROM evaluaciones e LEFT JOIN instrumentos i ON i.id=e.instrumento_id
           ORDER BY e.categoria,e.nombre"""
    ).fetchall()
    return jsonify(evaluaciones=[dict(row) for row in rows]), 200


@evaluations_bp.post("/api/admin/evaluaciones")
@role_required("ADMINISTRADOR", "JEFE_PERSONAL")
def crear_evaluacion():
    data = _json()
    if data is None:
        return _bad("Solicitud no válida.", "solicitud_invalida")
    codigo, nombre = data.get("codigo"), data.get("nombre")
    categoria, origen = data.get("categoria"), data.get("origen_nota")
    instrument_id = data.get("instrumento_id")
    if not isinstance(codigo, str) or not 2 <= len(codigo.strip()) <= 40:
        return _bad("El código debe tener entre 2 y 40 caracteres.")
    if not isinstance(nombre, str) or not 2 <= len(nombre.strip()) <= 160:
        return _bad("El nombre debe tener entre 2 y 160 caracteres.")
    if not isinstance(categoria, str) or categoria not in CATEGORIAS or not isinstance(origen, str) or origen not in {"INSTRUCTOR_VOLUNTARIO", "JEFE_PERSONAL"}:
        return _bad("Categoría u origen de nota no válido.")
    if categoria == "PSICOMETRICA" and (origen != "INSTRUCTOR_VOLUNTARIO" or not isinstance(instrument_id, int) or isinstance(instrument_id, bool)):
        return _bad("Una evaluación psicométrica requiere instrumento asociado y respuesta del voluntario.")
    if categoria != "PSICOMETRICA":
        if origen != "JEFE_PERSONAL":
            return _bad("Las notas físicas, académicas y de desempeño las registra el Jefe de Personal.")
        instrument_id = None
    connection = db.obtener_conexion()
    try:
        cursor = connection.execute(
            """INSERT INTO evaluaciones (codigo,nombre,categoria,origen_nota,instrumento_id,activo)
               VALUES (?,?,?,?,?,0)""",
            (codigo.strip().upper(), nombre.strip(), categoria, origen, instrument_id),
        )
        _audit(connection, "EVALUACION_CREADA")
        connection.commit()
    except Exception as error:
        connection.rollback()
        if error.__class__.__name__ == "IntegrityError":
            return _bad("El código ya existe o el instrumento asociado no es válido.", "evaluacion_duplicada", 409)
        raise
    return jsonify(ok=True, id=cursor.lastrowid, activo=False), 201


@evaluations_bp.patch("/api/admin/evaluaciones/<int:evaluation_id>")
@role_required("ADMINISTRADOR", "JEFE_PERSONAL")
def editar_evaluacion(evaluation_id):
    data = _json()
    if data is None:
        return _bad("Solicitud no válida.", "solicitud_invalida")
    connection = db.obtener_conexion()
    evaluation = connection.execute("SELECT * FROM evaluaciones WHERE id=?", (evaluation_id,)).fetchone()
    if not evaluation:
        return _bad("Evaluación no encontrada.", "evaluacion_no_encontrada", 404)
    name = data.get("nombre", evaluation["nombre"])
    active = data.get("activo", bool(evaluation["activo"]))
    if not isinstance(name, str) or not 2 <= len(name.strip()) <= 160 or not isinstance(active, bool):
        return _bad("Nombre o estado no válido.")
    if active and evaluation["categoria"] == "PSICOMETRICA":
        instrument = connection.execute(
            "SELECT estado_aprobacion FROM instrumentos WHERE id=?", (evaluation["instrumento_id"],)
        ).fetchone()
        if not instrument or instrument["estado_aprobacion"] != "APROBADO":
            return _bad("El instrumento no cuenta con aprobación; la evaluación permanece inactiva.", "instrumento_no_autorizado", 409)
    connection.execute("UPDATE evaluaciones SET nombre=?, activo=? WHERE id=?", (name.strip(), int(active), evaluation_id))
    _audit(connection, "EVALUACION_ACTUALIZADA" if active else "EVALUACION_DESACTIVADA")
    connection.commit()
    return jsonify(ok=True, activo=active), 200


@evaluations_bp.get("/api/admin/periodos-activos")
@role_required("ADMINISTRADOR")
def periodos_activos():
    rows = db.obtener_conexion().execute("SELECT id,nombre FROM periodos WHERE estado='ACTIVO' AND NOT EXISTS(SELECT 1 FROM bajas_gestion b WHERE b.periodo_id=periodos.id) ORDER BY fecha_inicio DESC").fetchall()
    return jsonify(periodos=[dict(row) for row in rows]), 200


@evaluations_bp.get("/api/admin/periodos")
@role_required("ADMINISTRADOR")
def listar_periodos():
    rows = db.obtener_conexion().execute(
        "SELECT id,nombre,fecha_inicio,fecha_fin,estado FROM periodos WHERE NOT EXISTS(SELECT 1 FROM bajas_gestion b WHERE b.periodo_id=periodos.id) ORDER BY fecha_inicio DESC,id DESC"
    ).fetchall()
    return jsonify(periodos=[dict(row) for row in rows]), 200


@evaluations_bp.post("/api/admin/periodos")
@role_required("ADMINISTRADOR")
def crear_periodo():
    data = _json() or {}
    name, start, end, state = (data.get(key) for key in ("nombre", "fecha_inicio", "fecha_fin", "estado"))
    if not isinstance(name, str) or not 2 <= len(name.strip()) <= 120 or not isinstance(state, str) or state != "BORRADOR":
        return _bad("Nombre o estado de período no válido.")
    try:
        start_date, end_date = date.fromisoformat(start), date.fromisoformat(end)
        if (start_date.month, start_date.day) != (1, 1) or (end_date.month, end_date.day) != (12, 31) or start_date.year != end_date.year:
            raise ValueError
    except (ValueError, TypeError):
        return _bad("El rango de fechas no es válido.")
    connection = db.obtener_conexion()
    try:
        cursor = connection.execute(
            "INSERT INTO periodos (nombre,fecha_inicio,fecha_fin,estado,creado_por) VALUES (?,?,?,?,?)",
            (name.strip(), start_date.isoformat(), end_date.isoformat(), state, current_user.id),
        )
        _audit(connection, "PERIODO_CREADO")
        connection.commit()
    except Exception as error:
        connection.rollback()
        if error.__class__.__name__ == "IntegrityError":
            return _bad("Ya existe un período con ese nombre.", "periodo_duplicado", 409)
        raise
    return jsonify(ok=True, id=cursor.lastrowid, estado=state), 201


@evaluations_bp.post("/api/admin/asignaciones")
@role_required("ADMINISTRADOR")
def asignar_evaluacion():
    data = _json() or {}
    ids = [data.get(key) for key in ("voluntario_id", "periodo_id", "evaluacion_id")]
    if any(not isinstance(value, int) or isinstance(value, bool) for value in ids):
        return _bad("Voluntario, período y evaluación son obligatorios.")
    connection = db.obtener_conexion()
    try:
        connection.execute('BEGIN IMMEDIATE')
    except sqlite3.OperationalError:
        return _bad('Hay una actualización en curso; recarga la gestión.', 'conflicto_gestion', 409)
    volunteer = connection.execute(
        """SELECT 1 FROM voluntarios v JOIN usuarios u ON u.id=v.usuario_id
           WHERE v.usuario_id=? AND u.estado='ACTIVO'""", (ids[0],)
    ).fetchone()
    period = connection.execute("SELECT 1 FROM periodos WHERE id=? AND estado='ACTIVO'", (ids[1],)).fetchone()
    evaluation = connection.execute("SELECT id,activo,categoria,instrumento_id FROM evaluaciones WHERE id=?", (ids[2],)).fetchone()
    from .gestiones import retirada, activa
    if not volunteer or not period or not evaluation or not evaluation["activo"] or retirada(connection, ids[1]):
        return _bad("Se requiere un voluntario activo, período activo y evaluación habilitada.", "asignacion_invalida", 400)
    if evaluation["categoria"] == "PSICOMETRICA":
        instrument = connection.execute("SELECT estado_aprobacion FROM instrumentos WHERE id=?", (evaluation["instrumento_id"],)).fetchone()
        if not instrument or instrument["estado_aprobacion"] != "APROBADO":
            return _bad("No se puede asignar: el instrumento no está autorizado.", "instrumento_no_autorizado", 409)
        if not activa(connection, ids[1], 'PSICOMETRICAS'):
            return _bad('Psicométricas desactivadas en esta gestión.', 'evaluacion_gestion_inactiva', 409)
    try:
        cursor = connection.execute(
            """INSERT INTO asignaciones_evaluacion (voluntario_id,periodo_id,evaluacion_id)
               VALUES (?,?,?)""", tuple(ids)
        )
        _audit(connection, "EVALUACION_ASIGNADA")
        connection.commit()
    except Exception as error:
        connection.rollback()
        if error.__class__.__name__ == "IntegrityError":
            return _bad("La evaluación ya está asignada a ese voluntario en el período.", "asignacion_duplicada", 409)
        raise
    return jsonify(ok=True, id=cursor.lastrowid, estado="NO_HABILITADA"), 201


@evaluations_bp.get("/api/admin/voluntarios-activos")
@evaluations_bp.get("/api/admin/instructores-voluntarios-activos")
@role_required("ADMINISTRADOR")
def voluntarios_activos_admin():
    rows = db.obtener_conexion().execute(
        """SELECT u.id,u.nombre_completo AS nombre FROM voluntarios v
           JOIN usuarios u ON u.id=v.usuario_id WHERE u.estado='ACTIVO'
           ORDER BY u.nombre_completo"""
    ).fetchall()
    return jsonify(voluntarios=[dict(row) for row in rows]), 200


@evaluations_bp.get("/api/instructor/asignaciones")
@evaluations_bp.get("/api/jefe-personal/asignaciones")
@role_required("ADMINISTRADOR", "JEFE_PERSONAL")
def asignaciones_equipo():
    params, where = [], "u.estado='ACTIVO'"
    rows = db.obtener_conexion().execute(
        f"""SELECT a.id,a.voluntario_id,a.periodo_id,a.evaluacion_id,a.estado,
                   u.nombre_completo AS voluntario,p.nombre AS periodo,e.nombre AS evaluacion,
                   e.categoria,e.activo AS evaluacion_activa,p.estado AS periodo_estado
            FROM asignaciones_evaluacion a JOIN voluntarios v ON v.usuario_id=a.voluntario_id
            JOIN usuarios u ON u.id=v.usuario_id JOIN periodos p ON p.id=a.periodo_id
            JOIN evaluaciones e ON e.id=a.evaluacion_id WHERE {where}
            ORDER BY p.fecha_inicio DESC,u.nombre_completo,e.nombre""", params
    ).fetchall()
    return jsonify(asignaciones=[dict(row) for row in rows]), 200


@evaluations_bp.patch("/api/instructor/asignaciones/<int:assignment_id>/estado")
@evaluations_bp.patch("/api/jefe-personal/asignaciones/<int:assignment_id>/estado")
@role_required("JEFE_PERSONAL", "ADMINISTRADOR")
def cambiar_estado_asignacion(assignment_id):
    data = _json() or {}
    state = data.get("estado")
    if state not in {"HABILITADA", "NO_HABILITADA"}:
        return _bad("El estado debe ser HABILITADA o NO_HABILITADA.")
    connection = db.obtener_conexion()
    try:
        connection.execute('BEGIN IMMEDIATE')
    except sqlite3.OperationalError:
        return _bad('Hay una actualización en curso; recarga la gestión.', 'conflicto_gestion', 409)
    assignment = _authorized_assignment(connection, assignment_id)
    if not assignment:
        return _bad("Asignación no encontrada en tu ámbito.", "asignacion_no_encontrada", 404)
    if assignment["cuenta_estado"] != "ACTIVO":
        return _bad("Reactiva la cuenta antes de modificar evaluaciones.", "cuenta_inactiva", 409)
    if assignment["periodo_estado"] != "ACTIVO":
        connection.rollback()
        return _bad("La Gestión debe estar activa para cambiar habilitaciones.", "periodo_cerrado", 409)
    if assignment["categoria"] != "PSICOMETRICA":
        return _bad("Solo las pruebas psicométricas se habilitan por voluntario.", "categoria_incompatible", 400)
    instrument = connection.execute("SELECT estado_aprobacion FROM instrumentos WHERE id=(SELECT instrumento_id FROM evaluaciones WHERE id=?)", (assignment["evaluacion_id"],)).fetchone()
    if state == "HABILITADA" and (not assignment["activo"] or not instrument or instrument["estado_aprobacion"] != "APROBADO"):
        return _bad("El instrumento no está aprobado y activo; no se puede habilitar.", "instrumento_no_autorizado", 409)
    from .gestiones import activa
    if state == 'HABILITADA' and not activa(connection, assignment['periodo_id'], 'PSICOMETRICAS'):
        return _bad('Psicométricas desactivadas en esta gestión.', 'evaluacion_gestion_inactiva', 409)
    connection.execute("UPDATE asignaciones_evaluacion SET estado=CASE WHEN estado IN ('COMPLETADA','EN_PROGRESO') THEN estado ELSE ? END, habilitada_por=?, habilitada_en=? WHERE id=?",
                       (state, current_user.id if state == "HABILITADA" else None,
                        _now() if state == "HABILITADA" else None, assignment_id))
    connection.execute("INSERT INTO habilitaciones_operativas(voluntario_id,periodo_id,clave,habilitada,registrada_por,registrada_en) VALUES (?,?,?,?,?,?)",
                       (assignment["voluntario_id"], assignment["periodo_id"], f'PSICO:{assignment["evaluacion_id"]}', int(state=="HABILITADA"), current_user.id, _now()))
    _audit(connection, "PRUEBA_HABILITADA" if state == "HABILITADA" else "PRUEBA_DESHABILITADA")
    connection.commit()
    return jsonify(ok=True, estado=state), 200


@evaluations_bp.post("/api/instructor/asistencias")
@evaluations_bp.post("/api/jefe-personal/asistencias")
@role_required("JEFE_PERSONAL", "ADMINISTRADOR")
def registrar_asistencias():
    data = _json() or {}
    try:
        activity = data.get("actividad")
        when = data.get("fecha")
        entries = data.get("asistencias")
        if not isinstance(activity, str) or not 1 <= len(activity.strip()) <= 160:
            raise ValueError("La actividad es obligatoria (máximo 160 caracteres).")
        when = date.fromisoformat(when).isoformat()
        if not isinstance(entries, list) or not 1 <= len(entries) <= 200:
            raise ValueError("Selecciona al menos un voluntario.")
        states = {"ASISTE", "ATRASO", "PERMISO", "FALTA", "PRESENTE", "AUSENTE", "JUSTIFICADO"}
        for item in entries:
            if not isinstance(item, dict) or not isinstance(item.get("voluntario_id"), int) or isinstance(item.get("voluntario_id"), bool) or item.get("estado") not in states:
                raise ValueError("Hay un registro de asistencia no válido.")
        if len({item["voluntario_id"] for item in entries}) != len(entries):
            raise ValueError("No repitas Instructores Voluntarios en la misma gestión.")
    except (ValueError, TypeError):
        return _bad("Fecha, actividad o registros de asistencia no válidos.")
    connection = db.obtener_conexion()
    connection.execute("SAVEPOINT registrar_asistencias")
    try:
        for item in entries:
            sql = """SELECT 1 FROM voluntarios v JOIN usuarios u ON u.id=v.usuario_id
                     WHERE v.usuario_id=? AND u.estado='ACTIVO'"""
            args = [item["voluntario_id"]]
            if not connection.execute(sql, args).fetchone():
                raise ValueError("Uno o más voluntarios no pertenecen a tu ámbito activo.")
            detail = {"PRESENTE": "ASISTE", "AUSENTE": "FALTA", "JUSTIFICADO": "PERMISO"}.get(item["estado"], item["estado"])
            legacy_state = {"ASISTE": "PRESENTE", "ATRASO": "PRESENTE", "PERMISO": "JUSTIFICADO", "FALTA": "AUSENTE"}[detail]
            connection.execute(
                """INSERT INTO asistencias (voluntario_id,fecha,estado,estado_detalle,actividad,registrado_por)
                   VALUES (?,?,?,?,?,?) ON CONFLICT(voluntario_id,fecha,actividad)
                   DO UPDATE SET estado=excluded.estado,estado_detalle=excluded.estado_detalle,
                                 registrado_por=excluded.registrado_por
                   WHERE COALESCE(asistencias.estado_detalle,asistencias.estado) != COALESCE(excluded.estado_detalle,excluded.estado)""",
                (item["voluntario_id"], when, legacy_state, detail, activity.strip(), current_user.id),
            )
        _audit(connection, "ASISTENCIAS_REGISTRADAS")
        connection.execute("RELEASE SAVEPOINT registrar_asistencias")
        connection.commit()
    except ValueError as error:
        connection.execute("ROLLBACK TO SAVEPOINT registrar_asistencias")
        connection.execute("RELEASE SAVEPOINT registrar_asistencias")
        return _bad(str(error), "voluntario_fuera_de_ambito", 403)
    return jsonify(ok=True, registrados=len(entries)), 200


@evaluations_bp.get("/api/instructor/asistencias")
@evaluations_bp.get("/api/jefe-personal/asistencias")
@role_required("JEFE_PERSONAL", "ADMINISTRADOR")
def listar_asistencias():
    mode = request.args.get("modo", "ultima")
    person = request.args.get("voluntario_id", "")
    start, end = request.args.get("desde"), request.args.get("hasta")
    if mode not in {"ultima", "rango"}:
        return _bad("El modo de consulta no es válido.")
    if person:
        try:
            person_id = int(person)
            if person_id < 1: raise ValueError
        except ValueError:
            return _bad("El Instructor Voluntario no es válido.")
    else:
        person_id = None
    if mode == "rango":
        try:
            start_date, end_date = date.fromisoformat(start or ""), date.fromisoformat(end or "")
            if end_date < start_date: raise ValueError
        except ValueError:
            return _bad("El rango de fechas no es válido.")
    elif start or end:
        return _bad("Selecciona el modo por rango para filtrar fechas.")
    connection = db.obtener_conexion()
    scope = ""
    scope_params = []
    if person_id is not None:
        scope += " AND a.voluntario_id=?"
        scope_params.append(person_id)
    effective_date = None
    if mode == "ultima":
        latest = connection.execute(
            """SELECT MAX(a.fecha) FROM asistencias a JOIN voluntarios v ON v.usuario_id=a.voluntario_id
               WHERE 1=1""" + scope, scope_params
        ).fetchone()[0]
        effective_date = latest
        where = " AND a.fecha=?" if latest else " AND 1=0"
        params = [latest] + scope_params if latest else scope_params
    else:
        where = " AND a.fecha BETWEEN ? AND ?"
        params = [start_date.isoformat(), end_date.isoformat()] + scope_params
    rows = connection.execute(
        """SELECT a.id,a.voluntario_id,u.nombre_completo AS voluntario,a.fecha,
                  COALESCE(a.estado_detalle, CASE a.estado WHEN 'PRESENTE' THEN 'ASISTE' WHEN 'AUSENTE' THEN 'FALTA' ELSE 'PERMISO' END) AS estado,
                  a.actividad
           FROM asistencias a JOIN voluntarios v ON v.usuario_id=a.voluntario_id
           JOIN usuarios u ON u.id=v.usuario_id WHERE 1=1""" + where + scope +
        " ORDER BY a.fecha DESC,a.actividad,u.nombre_completo", params,
    ).fetchall()
    return jsonify(asistencias=[dict(row) for row in rows], modo=mode,
                   fecha_consultada=effective_date), 200


@evaluations_bp.get("/api/instructor/capacitaciones")
@evaluations_bp.get("/api/jefe-personal/capacitaciones")
@role_required("JEFE_PERSONAL", "ADMINISTRADOR")
def listar_capacitaciones():
    volunteer = request.args.get("voluntario_id", "")
    params, where = [], ""
    if volunteer:
        try:
            volunteer_id = int(volunteer)
            if volunteer_id < 1: raise ValueError
        except ValueError:
            return _bad("El Instructor Voluntario no es válido.")
        where += " AND c.voluntario_id=?"; params.append(volunteer_id)
    rows = db.obtener_conexion().execute(
        """SELECT c.id,c.voluntario_id,u.nombre_completo AS voluntario,c.nombre,c.entidad,
                  c.fecha,c.observacion,c.creado_en,c.curso_id
           FROM capacitaciones c JOIN voluntarios v ON v.usuario_id=c.voluntario_id
           JOIN usuarios u ON u.id=v.usuario_id WHERE 1=1""" + where +
        " ORDER BY c.fecha DESC,c.id DESC", params,
    ).fetchall()
    return jsonify(capacitaciones=[dict(row) for row in rows]), 200


@evaluations_bp.post("/api/instructor/voluntarios/<int:volunteer_id>/capacitaciones")
@evaluations_bp.post("/api/jefe-personal/instructores-voluntarios/<int:volunteer_id>/capacitaciones")
@role_required("JEFE_PERSONAL", "ADMINISTRADOR")
def registrar_capacitacion(volunteer_id):
    from .relaciones_perfil import curso_para_registro
    data = _json() or {}
    connection = db.obtener_conexion()
    try: curso = curso_para_registro(connection, data.get("curso_id"))
    except ValueError as fallo: return _bad(str(fallo))
    if curso is not None: data["nombre"] = curso["nombre"]
    name, entity, when, note = (data.get(key) for key in ("nombre", "entidad", "fecha", "observacion"))
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 160:
        return _bad("El nombre del curso es obligatorio.")
    for value, limit in ((entity, 160), (note, 2000)):
        if value is not None and (not isinstance(value, str) or len(value) > limit):
            return _bad("Entidad u observación no válida.")
    if when not in (None, ""):
        try:
            if not isinstance(when, str) or date.fromisoformat(when).isoformat() != when: raise ValueError
        except (ValueError, TypeError): return _bad("La fecha no es válida.")
    connection = db.obtener_conexion()
    query = "SELECT 1 FROM voluntarios v JOIN usuarios u ON u.id=v.usuario_id WHERE v.usuario_id=? AND u.estado='ACTIVO'"
    args = [volunteer_id]
    if not connection.execute(query, args).fetchone():
        return _bad("Instructor Voluntario no encontrado en el ámbito activo.", "instructor_voluntario_no_encontrado", 404)
    cursor = connection.execute(
        "INSERT INTO capacitaciones (voluntario_id,nombre,entidad,fecha,observacion,curso_id) VALUES (?,?,?,?,?,?)",
        (volunteer_id, name.strip(), entity.strip() if entity else None, when, note.strip() if note else None, curso["id"] if curso is not None else None),
    )
    _audit(connection, "CAPACITACION_REGISTRADA")
    connection.commit()
    return jsonify(ok=True, id=cursor.lastrowid), 201


@evaluations_bp.patch("/api/instructor/capacitaciones/<int:training_id>")
@evaluations_bp.patch("/api/jefe-personal/capacitaciones/<int:training_id>")
@role_required("JEFE_PERSONAL", "ADMINISTRADOR")
def editar_capacitacion(training_id):
    data = _json()
    if data is None:
        return _bad("Solicitud no válida.", "solicitud_invalida")
    connection = db.obtener_conexion()
    row = connection.execute(
        """SELECT c.* FROM capacitaciones c JOIN voluntarios v ON v.usuario_id=c.voluntario_id
           WHERE c.id=?""", (training_id,),
    ).fetchone()
    if not row:
        return _bad("Capacitación no encontrada.", "capacitacion_no_encontrada", 404)
    if current_user.rol == "JEFE_PERSONAL":
        allowed = connection.execute(
            "SELECT 1 FROM voluntarios v JOIN usuarios u ON u.id=v.usuario_id WHERE v.usuario_id=? AND u.estado='ACTIVO'",
            (row["voluntario_id"],),
        ).fetchone()
        if not allowed:
            return _bad("Capacitación fuera de tu ámbito.", "sin_permiso", 403)
    from .relaciones_perfil import curso_para_registro
    try: curso = curso_para_registro(connection, data.get("curso_id", row["curso_id"]))
    except ValueError as fallo: return _bad(str(fallo))
    name = (curso["nombre"] if curso["id"] != row["curso_id"] else row["nombre"]) if curso is not None else data.get("nombre", row["nombre"])
    entity = data.get("entidad", row["entidad"])
    when = data.get("fecha", row["fecha"])
    note = data.get("observacion", row["observacion"])
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 160:
        return _bad("El nombre del curso es obligatorio.")
    if entity is not None and (not isinstance(entity, str) or len(entity) > 160):
        return _bad("La entidad no es válida.")
    if note is not None and (not isinstance(note, str) or len(note) > 2000):
        return _bad("La observación no es válida.")
    if when not in (None, ""):
        try:
            if not isinstance(when, str) or date.fromisoformat(when).isoformat() != when: raise ValueError
        except (ValueError, TypeError): return _bad("La fecha no es válida.")
    connection.execute(
        "UPDATE capacitaciones SET nombre=?,entidad=?,fecha=?,observacion=?,curso_id=? WHERE id=?",
        (name.strip(), entity.strip() if entity else None, when or None,
         note.strip() if note else None, curso["id"] if curso is not None else None, training_id),
    )
    _audit(connection, "CAPACITACION_ACTUALIZADA")
    connection.commit()
    return jsonify(ok=True), 200


@evaluations_bp.post("/api/instructor/asignaciones/<int:assignment_id>/calificaciones")
@evaluations_bp.post("/api/jefe-personal/asignaciones/<int:assignment_id>/calificaciones")
@role_required("JEFE_PERSONAL", "ADMINISTRADOR")
def registrar_calificacion(assignment_id):
    data = _json()
    if data is None or set(data) - {"nota_0_100", "observacion", "corregida_de_id"}:
        return _bad("Campos de calificación no válidos.")
    score = data.get("nota_0_100")
    observation = data.get("observacion")
    correction_id = data.get("corregida_de_id")
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score) or not 0 <= score <= 100:
        return _bad("La nota debe ser un número entre 0 y 100.")
    if observation is not None and (not isinstance(observation, str) or len(observation) > 2000):
        return _bad("La observación admite hasta 2000 caracteres.")
    if correction_id is not None and (isinstance(correction_id, bool) or not isinstance(correction_id, int) or correction_id < 1):
        return _bad("La referencia de corrección no es válida.")
    connection = db.obtener_conexion()
    try:
        connection.execute("BEGIN IMMEDIATE")
    except sqlite3.OperationalError:
        return _bad("La nota está siendo actualizada. Vuelve a cargar el historial.", "nota_en_actualizacion", 409)
    def rechazar(mensaje, codigo, estado):
        connection.rollback()
        return _bad(mensaje, codigo, estado)
    assignment = _authorized_assignment(connection, assignment_id)
    if not assignment:
        return rechazar("Asignación no encontrada en tu ámbito.", "asignacion_no_encontrada", 404)
    if assignment["cuenta_estado"] != "ACTIVO":
        return _bad("Reactiva la cuenta antes de modificar evaluaciones.", "cuenta_inactiva", 409)
    if connection.execute("SELECT 1 FROM configuraciones_5b WHERE periodo_id=? AND estado='PUBLICADA'", (assignment["periodo_id"],)).fetchone():
        return rechazar("Usa Notas operativas 5B para este período configurado.", "periodo_configurado_5b", 409)
    if assignment["categoria"] == "PSICOMETRICA":
        return rechazar("Las calificaciones psicométricas no se editan desde el flujo manual.", "nota_psicometrica_protegida", 403)
    if assignment["periodo_estado"] == "CERRADO":
        return rechazar("El período está cerrado; no se pueden cambiar sus calificaciones.", "periodo_cerrado", 409)
    latest = connection.execute("SELECT id FROM calificaciones WHERE asignacion_id=? ORDER BY registrada_en DESC,id DESC LIMIT 1", (assignment_id,)).fetchone()
    if latest and correction_id != latest["id"]:
        return rechazar("Ya existe una calificación. Envía su identificador como corregida_de_id para conservar el historial.", "correccion_requerida", 409)
    if correction_id is not None and (not latest or correction_id != latest["id"]):
        return rechazar("Solo se puede corregir la calificación más reciente.", "correccion_invalida", 409)
    cursor = connection.execute(
        """INSERT INTO calificaciones (asignacion_id,registrada_por,nota_0_100,observacion,corregida_de_id)
           VALUES (?,?,?,?,?)""",
        (assignment_id, current_user.id, score, observation.strip() if observation else None, correction_id),
    )
    connection.execute("UPDATE asignaciones_evaluacion SET estado='COMPLETADA' WHERE id=?", (assignment_id,))
    _audit(connection, "CALIFICACION_REGISTRADA" if correction_id is None else "CALIFICACION_CORREGIDA")
    connection.commit()
    return jsonify(ok=True, id=cursor.lastrowid, estado="COMPLETADA"), 201


@evaluations_bp.get("/api/instructor/asignaciones/<int:assignment_id>/calificaciones")
@evaluations_bp.get("/api/jefe-personal/asignaciones/<int:assignment_id>/calificaciones")
@role_required("JEFE_PERSONAL", "ADMINISTRADOR")
def historial_calificaciones(assignment_id):
    connection = db.obtener_conexion()
    assignment = _authorized_assignment(connection, assignment_id)
    if not assignment:
        return _bad("Asignación no encontrada en tu ámbito.", "asignacion_no_encontrada", 404)
    if assignment["categoria"] == "PSICOMETRICA" and current_user.rol == "JEFE_PERSONAL":
        return _bad("El resultado psicométrico no forma parte del historial de notas manuales.", "resultado_psicometrico_protegido", 403)
    rows = connection.execute(
        """SELECT c.id,c.nota_0_100,c.observacion,c.corregida_de_id,c.registrada_en,
                  u.nombre_completo AS registrada_por
           FROM calificaciones c JOIN usuarios u ON u.id=c.registrada_por
           WHERE c.asignacion_id=? ORDER BY c.registrada_en,c.id""", (assignment_id,)
    ).fetchall()
    return jsonify(historial=[dict(row) for row in rows]), 200


@evaluations_bp.get("/api/instructor/asignaciones/<int:assignment_id>/resultados")
@evaluations_bp.get("/api/jefe-personal/asignaciones/<int:assignment_id>/resultados")
@role_required("JEFE_PERSONAL", "ADMINISTRADOR")
def resultados_psicometricos(assignment_id):
    connection = db.obtener_conexion()
    assignment = _authorized_assignment(connection, assignment_id)
    if not assignment:
        return _bad("Asignación no encontrada en tu ámbito.", "asignacion_no_encontrada", 404)
    if assignment["categoria"] != "PSICOMETRICA":
        return _bad("La asignación no es psicométrica.", "categoria_incompatible", 400)
    if assignment["estado_instrumento"] != "APROBADO":
        return _bad("El instrumento no está autorizado.", "instrumento_no_autorizado", 409)
    rows = connection.execute(
        """SELECT id,numero,estado,iniciado_en,enviado_en,nota_0_100
           FROM intentos WHERE asignacion_id=? ORDER BY numero""", (assignment_id,)
    ).fetchall()
    return jsonify(intentos=[dict(row) for row in rows]), 200


@evaluations_bp.get("/api/voluntario/evaluaciones")
@evaluations_bp.get("/api/instructor-voluntario/evaluaciones")
@role_required("INSTRUCTOR_VOLUNTARIO")
def evaluaciones_voluntario():
    rows = db.obtener_conexion().execute(
        """SELECT a.id,e.nombre AS evaluacion,e.categoria,p.nombre AS periodo,a.estado
           FROM asignaciones_evaluacion a JOIN evaluaciones e ON e.id=a.evaluacion_id
           JOIN periodos p ON p.id=a.periodo_id
           WHERE a.voluntario_id=? ORDER BY p.fecha_inicio DESC,e.nombre""", (current_user.id,)
    ).fetchall()
    return jsonify(evaluaciones=[dict(row) for row in rows]), 200


@evaluations_bp.post("/api/voluntario/asignaciones/<int:assignment_id>/intentos")
@evaluations_bp.post("/api/instructor-voluntario/asignaciones/<int:assignment_id>/intentos")
@role_required("INSTRUCTOR_VOLUNTARIO")
def iniciar_intento(assignment_id):
    connection = db.obtener_conexion()
    assignment = _authorized_assignment(connection, assignment_id)
    if not assignment or assignment["categoria"] != "PSICOMETRICA":
        return _bad("Evaluación no disponible.", "evaluacion_no_disponible", 404)
    from .tabla_evaluaciones import habilitada
    if not habilitada(connection, current_user.id, assignment["periodo_id"], f'PSICO:{assignment["evaluacion_id"]}'):
        return _bad("Evaluación deshabilitada.", "evaluacion_deshabilitada", 409)
    instrument = connection.execute("SELECT estado_aprobacion FROM instrumentos WHERE id=(SELECT instrumento_id FROM evaluaciones WHERE id=?)", (assignment["evaluacion_id"],)).fetchone()
    if not assignment["activo"] or assignment["estado"] != "HABILITADA" or not instrument or instrument["estado_aprobacion"] != "APROBADO":
        return _bad("La evaluación no está habilitada con un instrumento autorizado.", "instrumento_no_autorizado", 409)
    # No instrument has approved items or a response-retention policy in docs/06 yet.
    return _bad("El instrumento está aprobado en catálogo, pero el formulario digital requiere ítems y retención de respuestas autorizados.", "formulario_no_disponible", 409)
