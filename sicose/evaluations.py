"""Catálogo, asistencias, calificaciones y resúmenes de evaluación por rol."""

import math
from datetime import date, datetime, timezone

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user

from . import db
from .permissions import role_required

evaluations_bp = Blueprint("evaluations", __name__)
CATEGORIAS = {"PSICOMETRICA", "FISICA", "ACADEMICA", "INSTRUCTOR"}


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
                    u.nombre_completo AS voluntario, v.instructor_id
             FROM asignaciones_evaluacion a
             JOIN evaluaciones e ON e.id=a.evaluacion_id
             JOIN voluntarios v ON v.usuario_id=a.voluntario_id
             JOIN usuarios u ON u.id=v.usuario_id
             JOIN periodos p ON p.id=a.periodo_id
             LEFT JOIN instrumentos i ON i.id=e.instrumento_id
             WHERE a.id=? AND u.estado='ACTIVO'"""
    row = connection.execute(sql, (assignment_id,)).fetchone()
    if row and current_user.rol == "INSTRUCTOR" and row["instructor_id"] != current_user.id:
        return None
    if row and current_user.rol == "VOLUNTARIO" and row["voluntario_id"] != current_user.id:
        return None
    return row


@evaluations_bp.get("/gestion/evaluaciones")
@role_required("ADMINISTRADOR")
def pagina_catalogo():
    return render_template("gestion_evaluaciones.html", titulo_pagina="Catálogo de evaluaciones",
                           nav_activo="evaluaciones", indicadores=[],
                           descripcion="Administra el catálogo y las asignaciones de cada período.",
                           periodo_actual="Sin período activo")


@evaluations_bp.get("/gestion/asistencias")
@role_required("ADMINISTRADOR", "INSTRUCTOR")
def pagina_asistencias():
    return render_template("gestion_asistencias.html", titulo_pagina="Asistencias y cursos",
                           nav_activo="asistencias", indicadores=[],
                           descripcion="Registra asistencia y capacitación del equipo autorizado.",
                           periodo_actual="Sin período activo")


@evaluations_bp.get("/gestion/calificaciones")
@role_required("ADMINISTRADOR", "INSTRUCTOR")
def pagina_calificaciones():
    return render_template("gestion_calificaciones.html", titulo_pagina="Notas e historial",
                           nav_activo="calificaciones", indicadores=[],
                           descripcion="Registra y consulta notas no psicométricas e historial.",
                           periodo_actual="Sin período activo")


@evaluations_bp.get("/api/admin/evaluaciones")
@role_required("ADMINISTRADOR")
def listar_evaluaciones():
    rows = db.obtener_conexion().execute(
        """SELECT e.id,e.codigo,e.nombre,e.categoria,e.origen_nota,e.instrumento_id,
                  e.activo,i.estado_aprobacion AS estado_instrumento
           FROM evaluaciones e LEFT JOIN instrumentos i ON i.id=e.instrumento_id
           ORDER BY e.categoria,e.nombre"""
    ).fetchall()
    return jsonify(evaluaciones=[dict(row) for row in rows]), 200


@evaluations_bp.post("/api/admin/evaluaciones")
@role_required("ADMINISTRADOR")
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
    if not isinstance(categoria, str) or categoria not in CATEGORIAS or not isinstance(origen, str) or origen not in {"VOLUNTARIO", "INSTRUCTOR"}:
        return _bad("Categoría u origen de nota no válido.")
    if categoria == "PSICOMETRICA" and (origen != "VOLUNTARIO" or not isinstance(instrument_id, int) or isinstance(instrument_id, bool)):
        return _bad("Una evaluación psicométrica requiere instrumento asociado y respuesta del voluntario.")
    if categoria != "PSICOMETRICA":
        if origen != "INSTRUCTOR":
            return _bad("Las notas físicas, académicas y de desempeño las registra el instructor.")
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
@role_required("ADMINISTRADOR")
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
    rows = db.obtener_conexion().execute("SELECT id,nombre FROM periodos WHERE estado='ACTIVO' ORDER BY fecha_inicio DESC").fetchall()
    return jsonify(periodos=[dict(row) for row in rows]), 200


@evaluations_bp.get("/api/admin/periodos")
@role_required("ADMINISTRADOR")
def listar_periodos():
    rows = db.obtener_conexion().execute(
        "SELECT id,nombre,fecha_inicio,fecha_fin,estado FROM periodos ORDER BY fecha_inicio DESC,id DESC"
    ).fetchall()
    return jsonify(periodos=[dict(row) for row in rows]), 200


@evaluations_bp.post("/api/admin/periodos")
@role_required("ADMINISTRADOR")
def crear_periodo():
    data = _json() or {}
    name, start, end, state = (data.get(key) for key in ("nombre", "fecha_inicio", "fecha_fin", "estado"))
    if not isinstance(name, str) or not 2 <= len(name.strip()) <= 120 or not isinstance(state, str) or state not in {"BORRADOR", "ACTIVO"}:
        return _bad("Nombre o estado de período no válido.")
    try:
        start_date, end_date = date.fromisoformat(start), date.fromisoformat(end)
        if end_date < start_date:
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
    volunteer = connection.execute(
        """SELECT 1 FROM voluntarios v JOIN usuarios u ON u.id=v.usuario_id
           WHERE v.usuario_id=? AND u.estado='ACTIVO'""", (ids[0],)
    ).fetchone()
    period = connection.execute("SELECT 1 FROM periodos WHERE id=? AND estado='ACTIVO'", (ids[1],)).fetchone()
    evaluation = connection.execute("SELECT id,activo,categoria,instrumento_id FROM evaluaciones WHERE id=?", (ids[2],)).fetchone()
    if not volunteer or not period or not evaluation or not evaluation["activo"]:
        return _bad("Se requiere un voluntario activo, período activo y evaluación habilitada.", "asignacion_invalida", 400)
    if evaluation["categoria"] == "PSICOMETRICA":
        instrument = connection.execute("SELECT estado_aprobacion FROM instrumentos WHERE id=?", (evaluation["instrumento_id"],)).fetchone()
        if not instrument or instrument["estado_aprobacion"] != "APROBADO":
            return _bad("No se puede asignar: el instrumento no está autorizado.", "instrumento_no_autorizado", 409)
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
@role_required("ADMINISTRADOR")
def voluntarios_activos_admin():
    rows = db.obtener_conexion().execute(
        """SELECT u.id,u.nombre_completo AS nombre FROM voluntarios v
           JOIN usuarios u ON u.id=v.usuario_id WHERE u.estado='ACTIVO'
           ORDER BY u.nombre_completo"""
    ).fetchall()
    return jsonify(voluntarios=[dict(row) for row in rows]), 200


@evaluations_bp.get("/api/instructor/asignaciones")
@role_required("ADMINISTRADOR", "INSTRUCTOR")
def asignaciones_equipo():
    params, where = [], "u.estado='ACTIVO'"
    if current_user.rol == "INSTRUCTOR":
        where += " AND v.instructor_id=?"
        params.append(current_user.id)
    rows = db.obtener_conexion().execute(
        f"""SELECT a.id,a.voluntario_id,a.periodo_id,a.evaluacion_id,a.estado,
                   u.nombre_completo AS voluntario,p.nombre AS periodo,e.nombre AS evaluacion,
                   e.categoria,e.activo AS evaluacion_activa
            FROM asignaciones_evaluacion a JOIN voluntarios v ON v.usuario_id=a.voluntario_id
            JOIN usuarios u ON u.id=v.usuario_id JOIN periodos p ON p.id=a.periodo_id
            JOIN evaluaciones e ON e.id=a.evaluacion_id WHERE {where}
            ORDER BY p.fecha_inicio DESC,u.nombre_completo,e.nombre""", params
    ).fetchall()
    return jsonify(asignaciones=[dict(row) for row in rows]), 200


@evaluations_bp.patch("/api/instructor/asignaciones/<int:assignment_id>/estado")
@role_required("INSTRUCTOR", "ADMINISTRADOR")
def cambiar_estado_asignacion(assignment_id):
    data = _json() or {}
    state = data.get("estado")
    if state not in {"HABILITADA", "NO_HABILITADA"}:
        return _bad("El estado debe ser HABILITADA o NO_HABILITADA.")
    connection = db.obtener_conexion()
    assignment = _authorized_assignment(connection, assignment_id)
    if not assignment:
        return _bad("Asignación no encontrada en tu ámbito.", "asignacion_no_encontrada", 404)
    if assignment["categoria"] != "PSICOMETRICA":
        return _bad("Solo las pruebas psicométricas se habilitan por voluntario.", "categoria_incompatible", 400)
    instrument = connection.execute("SELECT estado_aprobacion FROM instrumentos WHERE id=(SELECT instrumento_id FROM evaluaciones WHERE id=?)", (assignment["evaluacion_id"],)).fetchone()
    if state == "HABILITADA" and (not assignment["activo"] or not instrument or instrument["estado_aprobacion"] != "APROBADO"):
        return _bad("El instrumento no está aprobado y activo; no se puede habilitar.", "instrumento_no_autorizado", 409)
    connection.execute("UPDATE asignaciones_evaluacion SET estado=?, habilitada_por=?, habilitada_en=? WHERE id=?",
                       (state, current_user.id if state == "HABILITADA" else None,
                        _now() if state == "HABILITADA" else None, assignment_id))
    _audit(connection, "PRUEBA_HABILITADA" if state == "HABILITADA" else "PRUEBA_DESHABILITADA")
    connection.commit()
    return jsonify(ok=True, estado=state), 200


@evaluations_bp.post("/api/instructor/asistencias")
@role_required("INSTRUCTOR", "ADMINISTRADOR")
def registrar_asistencias():
    data = _json() or {}
    try:
        activity = data.get("actividad")
        when = data.get("fecha")
        entries = data.get("asistencias")
        if not isinstance(activity, str) or not 1 <= len(activity.strip()) <= 160:
            raise ValueError("La actividad es obligatoria (máximo 160 caracteres).")
        date.fromisoformat(when)
        if not isinstance(entries, list) or not 1 <= len(entries) <= 200:
            raise ValueError("Selecciona al menos un voluntario.")
        for item in entries:
            if not isinstance(item, dict) or not isinstance(item.get("voluntario_id"), int) or isinstance(item.get("voluntario_id"), bool) or item.get("estado") not in {"PRESENTE", "AUSENTE", "JUSTIFICADO"}:
                raise ValueError("Hay un registro de asistencia no válido.")
    except (ValueError, TypeError):
        return _bad("Fecha, actividad o registros de asistencia no válidos.")
    connection = db.obtener_conexion()
    connection.execute("SAVEPOINT registrar_asistencias")
    try:
        for item in entries:
            sql = """SELECT 1 FROM voluntarios v JOIN usuarios u ON u.id=v.usuario_id
                     WHERE v.usuario_id=? AND u.estado='ACTIVO'"""
            args = [item["voluntario_id"]]
            if current_user.rol == "INSTRUCTOR":
                sql += " AND v.instructor_id=?"
                args.append(current_user.id)
            if not connection.execute(sql, args).fetchone():
                raise ValueError("Uno o más voluntarios no pertenecen a tu ámbito activo.")
            connection.execute(
                """INSERT INTO asistencias (voluntario_id,fecha,estado,actividad,registrado_por)
                   VALUES (?,?,?,?,?) ON CONFLICT(voluntario_id,fecha,actividad)
                   DO UPDATE SET estado=excluded.estado,registrado_por=excluded.registrado_por""",
                (item["voluntario_id"], when, item["estado"], activity.strip(), current_user.id),
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
@role_required("INSTRUCTOR", "ADMINISTRADOR")
def listar_asistencias():
    when = request.args.get("fecha")
    try:
        if when:
            date.fromisoformat(when)
    except ValueError:
        return _bad("La fecha no es válida.")
    params = [when] if when else []
    where = ""
    if when:
        where = " AND a.fecha=?"
    if current_user.rol == "INSTRUCTOR":
        where += " AND v.instructor_id=?"
        params.append(current_user.id)
    rows = db.obtener_conexion().execute(
        """SELECT a.id,a.voluntario_id,u.nombre_completo AS voluntario,a.fecha,a.estado,a.actividad
           FROM asistencias a JOIN voluntarios v ON v.usuario_id=a.voluntario_id
           JOIN usuarios u ON u.id=v.usuario_id WHERE 1=1""" + where + " ORDER BY a.fecha DESC,a.actividad,u.nombre_completo",
        params,
    ).fetchall()
    return jsonify(asistencias=[dict(row) for row in rows]), 200


@evaluations_bp.post("/api/instructor/voluntarios/<int:volunteer_id>/capacitaciones")
@role_required("INSTRUCTOR", "ADMINISTRADOR")
def registrar_capacitacion(volunteer_id):
    data = _json() or {}
    name, entity, when, note = (data.get(key) for key in ("nombre", "entidad", "fecha", "observacion"))
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 160:
        return _bad("El nombre del curso es obligatorio.")
    for value, limit in ((entity, 160), (note, 2000)):
        if value is not None and (not isinstance(value, str) or len(value) > limit):
            return _bad("Entidad u observación no válida.")
    if when:
        try: date.fromisoformat(when)
        except (ValueError, TypeError): return _bad("La fecha no es válida.")
    connection = db.obtener_conexion()
    query = "SELECT 1 FROM voluntarios v JOIN usuarios u ON u.id=v.usuario_id WHERE v.usuario_id=? AND u.estado='ACTIVO'"
    args = [volunteer_id]
    if current_user.rol == "INSTRUCTOR":
        query += " AND v.instructor_id=?"; args.append(current_user.id)
    if not connection.execute(query, args).fetchone():
        return _bad("Voluntario no encontrado en el ámbito activo.", "voluntario_no_encontrado", 404)
    cursor = connection.execute(
        "INSERT INTO capacitaciones (voluntario_id,nombre,entidad,fecha,observacion) VALUES (?,?,?,?,?)",
        (volunteer_id, name.strip(), entity.strip() if entity else None, when, note.strip() if note else None),
    )
    _audit(connection, "CAPACITACION_REGISTRADA")
    connection.commit()
    return jsonify(ok=True, id=cursor.lastrowid), 201


@evaluations_bp.post("/api/instructor/asignaciones/<int:assignment_id>/calificaciones")
@role_required("INSTRUCTOR", "ADMINISTRADOR")
def registrar_calificacion(assignment_id):
    data = _json() or {}
    score = data.get("nota_0_100")
    observation = data.get("observacion")
    correction_id = data.get("corregida_de_id")
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score) or not 0 <= score <= 100:
        return _bad("La nota debe ser un número entre 0 y 100.")
    if observation is not None and (not isinstance(observation, str) or len(observation) > 2000):
        return _bad("La observación admite hasta 2000 caracteres.")
    connection = db.obtener_conexion()
    assignment = _authorized_assignment(connection, assignment_id)
    if not assignment:
        return _bad("Asignación no encontrada en tu ámbito.", "asignacion_no_encontrada", 404)
    if assignment["categoria"] == "PSICOMETRICA":
        return _bad("Las calificaciones psicométricas no se editan desde el flujo manual.", "nota_psicometrica_protegida", 403)
    if assignment["periodo_estado"] == "CERRADO":
        return _bad("El período está cerrado; no se pueden cambiar sus calificaciones.", "periodo_cerrado", 409)
    latest = connection.execute("SELECT id FROM calificaciones WHERE asignacion_id=? ORDER BY registrada_en DESC,id DESC LIMIT 1", (assignment_id,)).fetchone()
    if latest and correction_id != latest["id"]:
        return _bad("Ya existe una calificación. Envía su identificador como corregida_de_id para conservar el historial.", "correccion_requerida", 409)
    if correction_id is not None and (not latest or correction_id != latest["id"]):
        return _bad("Solo se puede corregir la calificación más reciente.", "correccion_invalida", 409)
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
@role_required("INSTRUCTOR", "ADMINISTRADOR")
def historial_calificaciones(assignment_id):
    connection = db.obtener_conexion()
    assignment = _authorized_assignment(connection, assignment_id)
    if not assignment:
        return _bad("Asignación no encontrada en tu ámbito.", "asignacion_no_encontrada", 404)
    if assignment["categoria"] == "PSICOMETRICA" and current_user.rol == "INSTRUCTOR":
        return _bad("El resultado psicométrico no forma parte del historial de notas manuales.", "resultado_psicometrico_protegido", 403)
    rows = connection.execute(
        """SELECT c.id,c.nota_0_100,c.observacion,c.corregida_de_id,c.registrada_en,
                  u.nombre_completo AS registrada_por
           FROM calificaciones c JOIN usuarios u ON u.id=c.registrada_por
           WHERE c.asignacion_id=? ORDER BY c.registrada_en,c.id""", (assignment_id,)
    ).fetchall()
    return jsonify(historial=[dict(row) for row in rows]), 200


@evaluations_bp.get("/api/instructor/asignaciones/<int:assignment_id>/resultados")
@role_required("INSTRUCTOR", "ADMINISTRADOR")
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
@role_required("VOLUNTARIO")
def evaluaciones_voluntario():
    rows = db.obtener_conexion().execute(
        """SELECT a.id,e.nombre AS evaluacion,e.categoria,p.nombre AS periodo,a.estado
           FROM asignaciones_evaluacion a JOIN evaluaciones e ON e.id=a.evaluacion_id
           JOIN periodos p ON p.id=a.periodo_id
           WHERE a.voluntario_id=? ORDER BY p.fecha_inicio DESC,e.nombre""", (current_user.id,)
    ).fetchall()
    return jsonify(evaluaciones=[dict(row) for row in rows]), 200


@evaluations_bp.post("/api/voluntario/asignaciones/<int:assignment_id>/intentos")
@role_required("VOLUNTARIO")
def iniciar_intento(assignment_id):
    connection = db.obtener_conexion()
    assignment = _authorized_assignment(connection, assignment_id)
    if not assignment or assignment["categoria"] != "PSICOMETRICA":
        return _bad("Evaluación no disponible.", "evaluacion_no_disponible", 404)
    instrument = connection.execute("SELECT estado_aprobacion FROM instrumentos WHERE id=(SELECT instrumento_id FROM evaluaciones WHERE id=?)", (assignment["evaluacion_id"],)).fetchone()
    if not assignment["activo"] or assignment["estado"] != "HABILITADA" or not instrument or instrument["estado_aprobacion"] != "APROBADO":
        return _bad("La evaluación no está habilitada con un instrumento autorizado.", "instrumento_no_autorizado", 409)
    # No instrument has approved items or a response-retention policy in docs/06 yet.
    return _bad("El instrumento está aprobado en catálogo, pero el formulario digital requiere ítems y retención de respuestas autorizados.", "formulario_no_disponible", 409)
