"""Solicitudes de alta, invitaciones y gestión segura de perfiles voluntarios."""

import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, render_template, request, url_for
from flask_login import current_user
from werkzeug.security import generate_password_hash

from . import db
from .permissions import role_required

management_bp = Blueprint("management", __name__)
USERNAME_RE = re.compile(r"^[A-Za-z0-9._-]{3,80}$")


@management_bp.get("/registro")
def pagina_registro():
    return render_template("registro.html", token=None)


@management_bp.get("/registro/invitacion/<token>")
def pagina_registro_invitacion(token):
    return render_template("registro.html", token=token)


@management_bp.get("/gestion/voluntarios")
@role_required("ADMINISTRADOR", "INSTRUCTOR")
def pagina_gestion_voluntarios():
    return render_template("gestion_voluntarios.html", titulo_pagina="Gestión de voluntarios",
                           nav_activo="voluntarios", indicadores=[],
                           descripcion="Solicitudes, perfiles y asignación de instructores.",
                           periodo_actual="Sin período activo")


@management_bp.get("/gestion/instructores")
@role_required("ADMINISTRADOR")
def pagina_gestion_instructores():
    return render_template("gestion_instructores.html", titulo_pagina="Administración de instructores",
                           nav_activo="instructores", indicadores=[],
                           descripcion="Crea y administra las cuentas con rol de instructor.",
                           periodo_actual="Sin período activo")


def _fallo(mensaje, codigo, status):
    return jsonify(error=mensaje, codigo=codigo), status


def _datos_json():
    datos = request.get_json(silent=True)
    return datos if isinstance(datos, dict) else None


def _texto(datos, campo, maximo, obligatorio=False):
    valor = datos.get(campo)
    if valor is None and not obligatorio:
        return None
    if not isinstance(valor, str):
        raise ValueError(f"El campo {campo} no es válido.")
    valor = valor.strip()
    if (obligatorio and not valor) or len(valor) > maximo:
        raise ValueError(f"El campo {campo} no es válido.")
    return valor or None


def _auditar(conexion, accion, resultado="EXITOSO"):
    db.registrar_auditoria(conexion, current_user.id if current_user.is_authenticated else None,
                           accion, resultado, request.remote_addr)


def _crear_solicitud(datos, invitacion_id=None):
    try:
        username = _texto(datos, "username", 80, True)
        nombre = _texto(datos, "nombre", 160, True)
        correo = _texto(datos, "correo", 254)
        if correo:
            correo = correo.casefold()
        password = datos.get("password")
        if not USERNAME_RE.fullmatch(username):
            raise ValueError("El nombre de usuario debe tener entre 3 y 80 caracteres válidos.")
        if correo and ("@" not in correo or any(char.isspace() for char in correo)):
            raise ValueError("El correo no es válido.")
        if not isinstance(password, str) or not 12 <= len(password) <= 256:
            raise ValueError("La contraseña debe tener entre 12 y 256 caracteres.")
        experiencia = _texto(datos, "experiencia_operaciones", 2000)
        antiguedad = _texto(datos, "antiguedad_desde", 10)
        if antiguedad:
            datetime.strptime(antiguedad, "%Y-%m-%d")
    except (ValueError, TypeError) as error:
        return None, _fallo(str(error), "datos_invalidos", 400)

    conexion = db.obtener_conexion()
    try:
        rol_id = conexion.execute("SELECT id FROM roles WHERE nombre = 'VOLUNTARIO'").fetchone()[0]
        cursor = conexion.execute(
            """INSERT INTO usuarios (username, nombre_completo, correo, password_hash, rol_id, estado)
               VALUES (?, ?, ?, ?, ?, 'PENDIENTE')""",
            (username, nombre, correo, generate_password_hash(password), rol_id),
        )
        usuario_id = cursor.lastrowid
        conexion.execute(
            """INSERT INTO voluntarios (usuario_id, experiencia_operaciones, antiguedad_desde)
               VALUES (?, ?, ?)""", (usuario_id, experiencia, antiguedad)
        )
        conexion.execute(
            "INSERT INTO solicitudes_registro (usuario_id, invitacion_id) VALUES (?, ?)",
            (usuario_id, invitacion_id),
        )
        if invitacion_id is not None:
            cursor = conexion.execute(
                "UPDATE invitaciones SET utilizada_en=? WHERE id=? AND utilizada_en IS NULL AND expira_en>?",
                (_now(), invitacion_id, _now()),
            )
            if cursor.rowcount != 1:
                conexion.rollback()
                return None, _fallo("La invitación ya fue utilizada o expiró.", "invitacion_invalida", 404)
        _auditar(conexion, "SOLICITUD_REGISTRO")
        conexion.commit()
    except Exception as error:
        conexion.rollback()
        # Unique constraints deliberately produce the same response for username/email collisions.
        if error.__class__.__name__ == "IntegrityError":
            return None, _fallo("No se pudo registrar la solicitud. Verifica los datos e inténtalo de nuevo.", "registro_no_disponible", 409)
        raise
    return usuario_id, None


@management_bp.post("/api/registro/solicitudes")
def solicitar_registro():
    datos = _datos_json()
    if datos is None:
        return _fallo("Solicitud no válida.", "solicitud_invalida", 400)
    _, respuesta = _crear_solicitud(datos)
    if respuesta:
        return respuesta
    return jsonify(ok=True, estado="PENDIENTE", mensaje="Solicitud recibida; requiere aprobación administrativa."), 201


def _hash_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@management_bp.post("/api/admin/invitaciones")
@role_required("ADMINISTRADOR")
def crear_invitacion():
    datos = _datos_json() or {}
    try:
        correo = _texto(datos, "correo", 254)
        if correo and ("@" not in correo or any(char.isspace() for char in correo)):
            raise ValueError("El correo no es válido.")
    except ValueError as error:
        return _fallo(str(error), "datos_invalidos", 400)
    token = secrets.token_urlsafe(32)
    expira = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(timespec="seconds")
    conexion = db.obtener_conexion()
    conexion.execute(
        "INSERT INTO invitaciones (token_hash, correo, creada_por, expira_en) VALUES (?, ?, ?, ?)",
        (_hash_token(token), correo, current_user.id, expira),
    )
    _auditar(conexion, "INVITACION_CREADA")
    conexion.commit()
    return jsonify(ok=True, invitacion_url=url_for("management.pagina_registro_invitacion", token=token, _external=False), expira_en=expira), 201


def _invitacion_valida(token):
    return db.obtener_conexion().execute(
        """SELECT id, correo, expira_en, utilizada_en FROM invitaciones
           WHERE token_hash = ?""", (_hash_token(token),)
    ).fetchone()


@management_bp.get("/api/registro/invitaciones/<token>")
def consultar_invitacion(token):
    if len(token) > 128:
        return _fallo("La invitación no es válida.", "invitacion_invalida", 404)
    invitacion = _invitacion_valida(token)
    ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if not invitacion or invitacion["utilizada_en"] or invitacion["expira_en"] <= ahora:
        return _fallo("La invitación no es válida o ha expirado.", "invitacion_invalida", 404)
    return jsonify(valida=True, correo=invitacion["correo"]), 200


@management_bp.post("/api/registro/invitaciones/<token>")
def usar_invitacion(token):
    datos = _datos_json()
    if datos is None or len(token) > 128:
        return _fallo("Solicitud no válida.", "solicitud_invalida", 400)
    conexion = db.obtener_conexion()
    invitacion = _invitacion_valida(token)
    ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if not invitacion or invitacion["utilizada_en"] or invitacion["expira_en"] <= ahora:
        return _fallo("La invitación no es válida o ha expirado.", "invitacion_invalida", 404)
    if invitacion["correo"]:
        correo_enviado = datos.get("correo")
        if not isinstance(correo_enviado, str) or correo_enviado.strip().casefold() != invitacion["correo"].casefold():
            return _fallo("El correo no coincide con la invitación.", "correo_no_coincide", 400)
    usuario_id, respuesta = _crear_solicitud(datos, invitacion["id"])
    if respuesta:
        return respuesta
    return jsonify(ok=True, estado="PENDIENTE", mensaje="Registro recibido; la cuenta requiere aprobación."), 201


@management_bp.get("/api/admin/solicitudes")
@role_required("ADMINISTRADOR")
def listar_solicitudes():
    filas = db.obtener_conexion().execute(
        """SELECT s.id, u.username, u.nombre_completo AS nombre, u.correo,
                  s.estado, s.creada_en, s.invitacion_id
           FROM solicitudes_registro s JOIN usuarios u ON u.id = s.usuario_id
           WHERE s.estado = 'PENDIENTE' ORDER BY s.creada_en, s.id"""
    ).fetchall()
    return jsonify(solicitudes=[dict(fila) for fila in filas]), 200


@management_bp.get("/api/admin/instructores")
@role_required("ADMINISTRADOR")
def listar_instructores():
    filas = db.obtener_conexion().execute(
        """SELECT i.usuario_id AS id, u.username, u.nombre_completo AS nombre,
                  u.correo, u.estado, i.especialidad,
                  (SELECT COUNT(*) FROM voluntarios v JOIN usuarios uv ON uv.id=v.usuario_id
                   WHERE v.instructor_id=i.usuario_id AND uv.estado='ACTIVO') AS voluntarios_activos
           FROM instructores i JOIN usuarios u ON u.id=i.usuario_id
           ORDER BY u.nombre_completo, u.id"""
    ).fetchall()
    return jsonify(instructores=[dict(fila) for fila in filas]), 200


@management_bp.post("/api/admin/instructores")
@role_required("ADMINISTRADOR")
def crear_instructor():
    datos = _datos_json()
    if datos is None:
        return _fallo("Solicitud no válida.", "solicitud_invalida", 400)
    try:
        username = _texto(datos, "username", 80, True)
        nombre = _texto(datos, "nombre", 160, True)
        correo = _texto(datos, "correo", 254)
        especialidad = _texto(datos, "especialidad", 160)
        password = datos.get("password")
        if not USERNAME_RE.fullmatch(username):
            raise ValueError("El nombre de usuario debe tener entre 3 y 80 caracteres válidos.")
        if correo and ("@" not in correo or any(char.isspace() for char in correo)):
            raise ValueError("El correo no es válido.")
        if not isinstance(password, str) or not 12 <= len(password) <= 256:
            raise ValueError("La contraseña inicial debe tener entre 12 y 256 caracteres.")
    except (ValueError, TypeError) as error:
        return _fallo(str(error), "datos_invalidos", 400)

    conexion = db.obtener_conexion()
    rol_id = conexion.execute("SELECT id FROM roles WHERE nombre='INSTRUCTOR'").fetchone()[0]
    ahora = _now()
    try:
        cursor = conexion.execute(
            """INSERT INTO usuarios (username, nombre_completo, correo, password_hash, rol_id, estado)
               VALUES (?, ?, ?, ?, ?, 'ACTIVO')""",
            (username, nombre, correo.casefold() if correo else None, generate_password_hash(password), rol_id),
        )
        usuario_id = cursor.lastrowid
        conexion.execute("INSERT INTO instructores (usuario_id, especialidad) VALUES (?, ?)", (usuario_id, especialidad))
        _auditar(conexion, "INSTRUCTOR_CREADO")
        conexion.commit()
    except Exception as error:
        conexion.rollback()
        if error.__class__.__name__ == "IntegrityError":
            return _fallo("El nombre de usuario o correo ya está asociado a otra cuenta.", "cuenta_duplicada", 409)
        raise
    return jsonify(ok=True, id=usuario_id, estado="ACTIVO"), 201


@management_bp.patch("/api/admin/instructores/<int:usuario_id>")
@role_required("ADMINISTRADOR")
def editar_instructor(usuario_id):
    datos = _datos_json()
    if datos is None:
        return _fallo("Solicitud no válida.", "solicitud_invalida", 400)
    conexion = db.obtener_conexion()
    instructor = conexion.execute(
        """SELECT u.nombre_completo, u.correo, i.especialidad FROM instructores i
           JOIN usuarios u ON u.id=i.usuario_id WHERE i.usuario_id=?""", (usuario_id,)
    ).fetchone()
    if not instructor:
        return _fallo("Instructor no encontrado.", "instructor_no_encontrado", 404)
    try:
        campos = {}
        for campo, limite in (("nombre", 160), ("correo", 254), ("especialidad", 160)):
            if campo in datos:
                valor = _texto(datos, campo, limite, campo == "nombre")
                if campo == "correo" and valor:
                    valor = valor.casefold()
                    if "@" not in valor or any(char.isspace() for char in valor):
                        raise ValueError("El correo no es válido.")
                campos[campo] = valor
    except (ValueError, TypeError) as error:
        return _fallo(str(error), "datos_invalidos", 400)
    if not campos:
        return _fallo("No se enviaron campos para actualizar.", "sin_cambios", 400)
    nombre = campos.pop("nombre", instructor["nombre_completo"])
    correo = campos.pop("correo", instructor["correo"])
    especialidad = campos.pop("especialidad", instructor["especialidad"])
    try:
        conexion.execute("UPDATE usuarios SET nombre_completo=?, correo=?, actualizado_en=? WHERE id=?",
                         (nombre, correo, _now(), usuario_id))
        conexion.execute("UPDATE instructores SET especialidad=? WHERE usuario_id=?", (especialidad, usuario_id))
        _auditar(conexion, "INSTRUCTOR_EDITADO")
        conexion.commit()
    except Exception as error:
        conexion.rollback()
        if error.__class__.__name__ == "IntegrityError":
            return _fallo("El correo ya está asociado a otra cuenta.", "correo_duplicado", 409)
        raise
    return jsonify(ok=True, mensaje="Perfil de instructor actualizado."), 200


@management_bp.post("/api/admin/instructores/<int:usuario_id>/desactivar")
@role_required("ADMINISTRADOR")
def desactivar_instructor(usuario_id):
    conexion = db.obtener_conexion()
    fila = conexion.execute("SELECT estado FROM usuarios u JOIN instructores i ON i.usuario_id=u.id WHERE u.id=?", (usuario_id,)).fetchone()
    if not fila:
        return _fallo("Instructor no encontrado.", "instructor_no_encontrado", 404)
    if fila["estado"] == "INACTIVO":
        return jsonify(ok=True, estado="INACTIVO"), 200
    ahora = _now()
    conexion.execute("UPDATE usuarios SET estado='INACTIVO', actualizado_en=? WHERE id=?", (ahora, usuario_id))
    # Desvincular voluntarios activos, conservando sus perfiles e historial.
    cursor = conexion.execute(
        """UPDATE voluntarios SET instructor_id=NULL WHERE instructor_id=?
           AND usuario_id IN (SELECT id FROM usuarios WHERE estado='ACTIVO')""",
        (usuario_id,),
    )
    _auditar(conexion, "INSTRUCTOR_DESACTIVADO")
    if cursor.rowcount:
        _auditar(conexion, "VOLUNTARIOS_REASIGNADOS_POR_BAJA")
    conexion.commit()
    return jsonify(ok=True, estado="INACTIVO", voluntarios_desvinculados=cursor.rowcount), 200


@management_bp.post("/api/admin/solicitudes/<int:solicitud_id>/aprobar")
@role_required("ADMINISTRADOR")
def aprobar_solicitud(solicitud_id):
    datos = _datos_json() or {}
    instructor_id = datos.get("instructor_id")
    conexion = db.obtener_conexion()
    solicitud = conexion.execute(
        "SELECT usuario_id FROM solicitudes_registro WHERE id = ? AND estado = 'PENDIENTE'",
        (solicitud_id,),
    ).fetchone()
    if not solicitud:
        return _fallo("No existe una solicitud pendiente con ese identificador.", "solicitud_no_encontrada", 404)
    if instructor_id is not None:
        if not isinstance(instructor_id, int) or isinstance(instructor_id, bool) or not conexion.execute(
            """SELECT 1 FROM instructores i JOIN usuarios u ON u.id=i.usuario_id
               WHERE i.usuario_id=? AND u.estado='ACTIVO'""", (instructor_id,)
        ).fetchone():
            return _fallo("El instructor asignado no es válido o no está activo.", "instructor_invalido", 400)
    ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conexion.execute("UPDATE usuarios SET estado='ACTIVO', actualizado_en=? WHERE id=?", (ahora, solicitud["usuario_id"]))
    conexion.execute("UPDATE voluntarios SET instructor_id=? WHERE usuario_id=?", (instructor_id, solicitud["usuario_id"]))
    conexion.execute(
        "UPDATE solicitudes_registro SET estado='APROBADA', revisada_por=?, revisada_en=? WHERE id=?",
        (current_user.id, ahora, solicitud_id),
    )
    _auditar(conexion, "SOLICITUD_APROBADA")
    conexion.commit()
    return jsonify(ok=True, estado="ACTIVO"), 200


@management_bp.post("/api/admin/solicitudes/<int:solicitud_id>/rechazar")
@role_required("ADMINISTRADOR")
def rechazar_solicitud(solicitud_id):
    conexion = db.obtener_conexion()
    solicitud = conexion.execute(
        "SELECT usuario_id FROM solicitudes_registro WHERE id=? AND estado='PENDIENTE'", (solicitud_id,)
    ).fetchone()
    if not solicitud:
        return _fallo("No existe una solicitud pendiente con ese identificador.", "solicitud_no_encontrada", 404)
    ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conexion.execute("UPDATE usuarios SET estado='RECHAZADO', actualizado_en=? WHERE id=?", (ahora, solicitud["usuario_id"]))
    conexion.execute(
        "UPDATE solicitudes_registro SET estado='RECHAZADA', revisada_por=?, revisada_en=? WHERE id=?",
        (current_user.id, ahora, solicitud_id),
    )
    _auditar(conexion, "SOLICITUD_RECHAZADA")
    conexion.commit()
    return jsonify(ok=True, estado="RECHAZADO"), 200


def _alcance_voluntario(conexion, usuario_id):
    consulta = """SELECT u.id, u.username, u.nombre_completo AS nombre, u.correo, u.estado,
                         v.instructor_id, v.experiencia_operaciones, v.antiguedad_desde
                  FROM usuarios u JOIN voluntarios v ON v.usuario_id=u.id
                  JOIN roles r ON r.id=u.rol_id WHERE u.id=? AND r.nombre='VOLUNTARIO'"""
    fila = conexion.execute(consulta, (usuario_id,)).fetchone()
    if fila and current_user.rol == "INSTRUCTOR" and fila["instructor_id"] != current_user.id:
        return None
    return fila


@management_bp.get("/api/voluntarios")
@role_required("ADMINISTRADOR", "INSTRUCTOR")
def listar_voluntarios():
    conexion = db.obtener_conexion()
    consulta = """SELECT u.id, u.username, u.nombre_completo AS nombre, u.correo, u.estado,
                         v.instructor_id, ui.nombre_completo AS instructor_nombre,
                         v.experiencia_operaciones, v.antiguedad_desde
                  FROM voluntarios v JOIN usuarios u ON u.id=v.usuario_id
                  LEFT JOIN usuarios ui ON ui.id=v.instructor_id
                  ORDER BY u.nombre_completo, u.id"""
    parametros = ()
    if current_user.rol == "INSTRUCTOR":
        consulta = consulta.replace("ORDER BY", "WHERE v.instructor_id = ? ORDER BY")
        parametros = (current_user.id,)
    filas = conexion.execute(consulta, parametros).fetchall()
    return jsonify(voluntarios=[dict(fila) for fila in filas]), 200


@management_bp.patch("/api/voluntarios/<int:usuario_id>")
@role_required("ADMINISTRADOR", "INSTRUCTOR")
def editar_voluntario(usuario_id):
    datos = _datos_json()
    if datos is None:
        return _fallo("Solicitud no válida.", "solicitud_invalida", 400)
    conexion = db.obtener_conexion()
    voluntario = _alcance_voluntario(conexion, usuario_id)
    if not voluntario:
        return _fallo("Voluntario no encontrado en tu ámbito.", "voluntario_no_encontrado", 404)
    campos = {}
    try:
        for campo, limite in (("nombre", 160), ("correo", 254), ("experiencia_operaciones", 2000), ("antiguedad_desde", 10)):
            if campo in datos:
                valor = _texto(datos, campo, limite, campo == "nombre")
                if campo == "correo" and valor:
                    valor = valor.casefold()
                if campo == "correo" and valor and ("@" not in valor or any(char.isspace() for char in valor)):
                    raise ValueError("El correo no es válido.")
                if campo == "antiguedad_desde" and valor:
                    datetime.strptime(valor, "%Y-%m-%d")
                campos[campo] = valor
        if "instructor_id" in datos:
            if current_user.rol != "ADMINISTRADOR":
                raise ValueError("Solo administración puede cambiar instructor asignado.")
            instructor_id = datos["instructor_id"]
            if instructor_id is not None and (not isinstance(instructor_id, int) or isinstance(instructor_id, bool) or not conexion.execute(
                "SELECT 1 FROM instructores i JOIN usuarios u ON u.id=i.usuario_id WHERE i.usuario_id=? AND u.estado='ACTIVO'", (instructor_id,)
            ).fetchone()):
                raise ValueError("El instructor asignado no es válido o no está activo.")
            campos["instructor_id"] = instructor_id
    except (ValueError, TypeError) as error:
        return _fallo(str(error), "datos_invalidos", 400)
    if not campos:
        return _fallo("No se enviaron campos para actualizar.", "sin_cambios", 400)
    nombre = campos.pop("nombre", voluntario["nombre"])
    correo = campos.pop("correo", voluntario["correo"])
    ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        conexion.execute("UPDATE usuarios SET nombre_completo=?, correo=?, actualizado_en=? WHERE id=?", (nombre, correo, ahora, usuario_id))
        perfil = {k: v for k, v in campos.items() if k in {"experiencia_operaciones", "antiguedad_desde", "instructor_id"}}
        if perfil:
            asignaciones = ", ".join(f"{campo}=?" for campo in perfil)
            conexion.execute(f"UPDATE voluntarios SET {asignaciones} WHERE usuario_id=?", (*perfil.values(), usuario_id))
        _auditar(conexion, "VOLUNTARIO_EDITADO")
        conexion.commit()
    except Exception as error:
        conexion.rollback()
        if error.__class__.__name__ == "IntegrityError":
            return _fallo("El correo ya está asociado a otra cuenta.", "correo_duplicado", 409)
        raise
    return jsonify(ok=True, mensaje="Perfil actualizado."), 200


@management_bp.post("/api/voluntarios/<int:usuario_id>/desactivar")
@role_required("ADMINISTRADOR", "INSTRUCTOR")
def desactivar_voluntario(usuario_id):
    conexion = db.obtener_conexion()
    voluntario = _alcance_voluntario(conexion, usuario_id)
    if not voluntario:
        return _fallo("Voluntario no encontrado en tu ámbito.", "voluntario_no_encontrado", 404)
    if voluntario["estado"] == "INACTIVO":
        return jsonify(ok=True, estado="INACTIVO", mensaje="El voluntario ya estaba desactivado."), 200
    ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conexion.execute("UPDATE usuarios SET estado='INACTIVO', actualizado_en=? WHERE id=?", (ahora, usuario_id))
    _auditar(conexion, "VOLUNTARIO_DESACTIVADO")
    conexion.commit()
    return jsonify(ok=True, estado="INACTIVO"), 200
