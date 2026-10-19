"""Solicitudes de alta, invitaciones y gestión segura de perfiles voluntarios."""

import hashlib
import re
import secrets
import unicodedata
from datetime import date, datetime, timedelta, timezone

from flask import Blueprint, current_app, jsonify, render_template, request, send_file, url_for
from flask_login import current_user
from werkzeug.security import generate_password_hash

from . import db
from .permissions import role_required
from .perfil_residencia import CAMPOS_RESIDENCIA, DEPARTAMENTOS_BOLIVIA, PAISES_RESIDENCIA, leer_geografia, guardar_geografia, validar_perfil_residencia, antiguedad_calculada

def _leer_secundarias(conexion, usuario_id):
    return [fila[0] for fila in conexion.execute(
        "SELECT especialidad FROM especialidades_secundarias WHERE voluntario_id=? ORDER BY especialidad",
        (usuario_id,),
    )]


management_bp = Blueprint("management", __name__)
USERNAME_RE = re.compile(r"^[A-Za-z0-9._-]{3,80}$")
ESPECIALIDADES_PRINCIPALES = (
    "Rescate en agua", "Rescate en montaña", "Rescate en selva",
    "Lucha contra incendios", "Primeros Auxilios", "K-9",
)


GRADOS_INSTRUCTOR = ("Instructor Inicial", "Instructor Segundo", "Instructor Primero", "Instructor Principal", "Instructor Mayor")


def _grado(datos):
    valor = _texto(datos, "grado", 80)
    if valor and valor not in GRADOS_INSTRUCTOR: raise ValueError("Selecciona un grado válido.")
    return valor or None


def _validar_alta_completa(datos, residencia):
    if not _texto(datos, "correo", 254, True): raise ValueError("Ingresa el correo electrónico.")
    if not residencia.get("nacionalidad"): raise ValueError("Selecciona la nacionalidad.")
    if not residencia.get("departamento_residencia"): raise ValueError("Selecciona el departamento.")
    foto = request.files.get("foto")
    if foto is None or not foto.filename: raise ValueError("Selecciona una foto de perfil PNG/JPEG.")


def _guardar_incorporacion_grado(conexion, usuario_id, datos, residencia):
    if "fecha_incorporacion" in residencia:
        conexion.execute("UPDATE voluntarios SET fecha_incorporacion=? WHERE usuario_id=?", (residencia["fecha_incorporacion"], usuario_id))
    if "grado" in datos:
        conexion.execute("UPDATE voluntarios SET grado=? WHERE usuario_id=?", (_grado(datos), usuario_id))


@management_bp.get("/registro")
def pagina_registro():
    return render_template("registro.html", token=None, paises=PAISES_RESIDENCIA, departamentos=DEPARTAMENTOS_BOLIVIA)


@management_bp.get("/registro/invitacion/<token>")
def pagina_registro_invitacion(token):
    return render_template("registro.html", token=token, paises=PAISES_RESIDENCIA, departamentos=DEPARTAMENTOS_BOLIVIA)


@management_bp.get("/gestion/voluntarios")
@management_bp.get("/gestion/instructores-voluntarios")
@role_required("ADMINISTRADOR", "JEFE_PERSONAL")
def pagina_gestion_voluntarios():
    return render_template("gestion_instructores_voluntarios.html", titulo_pagina="Gestión de Instructores Voluntarios",
                           nav_activo="voluntarios", indicadores=[], grados=GRADOS_INSTRUCTOR, departamentos=DEPARTAMENTOS_BOLIVIA, paises=PAISES_RESIDENCIA, ano_actual=date.today().year,
                           descripcion=("Alta manual, solicitudes pendientes y administración integral de perfiles."
                                        if current_user.rol == "ADMINISTRADOR" else
                                        "Solicita altas y gestiona el personal de SBRAB."),
                           periodo_actual=db.periodo_actual())


@management_bp.get("/gestion/instructores")
@management_bp.get("/gestion/jefes-personal")
@role_required("ADMINISTRADOR")
def pagina_gestion_instructores():
    return render_template("gestion_jefes_personal.html", titulo_pagina="Administración de Jefes de Personal",
                           nav_activo="instructores", indicadores=[],
                           descripcion="Crea y administra las cuentas con rol de Jefe de Personal.",
                           periodo_actual=db.periodo_actual())


def _geografia_propia():
    conexion = db.obtener_conexion()
    perfil = conexion.execute("SELECT pais_residencia,departamento_residencia,grado,especialidad_principal FROM voluntarios WHERE usuario_id=?",(current_user.id,)).fetchone()
    valores = dict(perfil) if perfil else {}
    valores.update(leer_geografia(conexion,current_user.id))
    return valores


@management_bp.get("/mi-perfil")
@role_required("INSTRUCTOR_VOLUNTARIO")
def pagina_perfil_propio():
    return render_template("perfil_instructor_voluntario.html", titulo_pagina="Mi perfil",
                           nav_activo="perfil", indicadores=[], periodo_actual=db.periodo_actual(),
                           descripcion="Actualiza tu correo y foto de perfil.",
                           especialidades_secundarias=_leer_secundarias(db.obtener_conexion(), current_user.id),
                           geografia=_geografia_propia())


@management_bp.patch("/api/instructor-voluntario/perfil")
@role_required("INSTRUCTOR_VOLUNTARIO")
def editar_perfil_propio():
    """Autoservicio limitado a correo y foto de la cuenta autenticada."""
    datos = _datos_form_o_json()
    if datos is None:
        return _fallo("Solicitud no válida.", "solicitud_invalida", 400)
    if set(datos) - {"correo"} or set(request.files) - {"foto"}:
        return _fallo("Solo puedes actualizar correo y foto.", "campos_no_permitidos", 400)
    tiene_foto = request.files.get("foto") is not None
    if "correo" not in datos and not tiene_foto:
        return _fallo("No se enviaron cambios.", "sin_cambios", 400)
    try:
        correo = current_user.correo
        if "correo" in datos:
            correo = _texto(datos, "correo", 254)
            if correo:
                correo = correo.casefold()
                if "@" not in correo or any(char.isspace() for char in correo):
                    raise ValueError("El correo no es válido.")
    except ValueError as error:
        return _fallo(str(error), "datos_invalidos", 400)
    from .profile_media import guardar_foto
    foto = None
    try:
        if tiene_foto:
            foto = guardar_foto(request.files.get("foto"))
    except ValueError as error:
        return _fallo(str(error), "foto_invalida", 400)
    conexion = db.obtener_conexion()
    try:
        conexion.execute(
            """UPDATE usuarios SET correo=?, foto_perfil=COALESCE(?,foto_perfil), actualizado_en=?
               WHERE id=?""", (correo, foto, _now(), current_user.id))
        _auditar(conexion, "PERFIL_PROPIO_ACTUALIZADO")
        conexion.commit()
    except Exception as error:
        conexion.rollback()
        _descartar_foto(foto)
        if error.__class__.__name__ == "IntegrityError":
            return _fallo("No se pudo actualizar el correo. Verifica los datos.", "correo_no_disponible", 409)
        raise
    return jsonify(ok=True, mensaje="Correo y foto actualizados."), 200


@management_bp.get("/configuracion")
@role_required("ADMINISTRADOR")
def pagina_configuracion():
    return render_template("configuracion_administrador.html", titulo_pagina="Configuración",
                           nav_activo="configuracion", indicadores=[],
                           descripcion="Actualiza tu perfil y las credenciales de administración.",
                           periodo_actual=db.periodo_actual())


def _especialidad_principal(datos, obligatorio=False):
    valor = _texto(datos, "especialidad_principal", 80, obligatorio)
    if valor is None and not obligatorio:
        return None
    if valor not in ESPECIALIDADES_PRINCIPALES:
        raise ValueError("Selecciona una especialidad principal válida.")
    return valor


def _fallo(mensaje, codigo, status):
    return jsonify(error=mensaje, codigo=codigo), status


def _datos_json():
    datos = request.get_json(silent=True)
    return datos if isinstance(datos, dict) else None


def _datos_form_o_json():
    if request.mimetype == "multipart/form-data":
        return request.form.to_dict()
    return _datos_json()


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


def _identidad_instructor(datos, existentes=None):
    """Valida nombres y nacimiento y calcula la clave institucional del perfil."""
    existentes = existentes or {}
    nombres = _texto(datos, "nombres", 120, True) if "nombres" in datos else existentes.get("nombres")
    paterno = _texto(datos, "apellido_paterno", 80, True) if "apellido_paterno" in datos else existentes.get("apellido_paterno")
    materno = _texto(datos, "apellido_materno", 80, True) if "apellido_materno" in datos else existentes.get("apellido_materno")
    fecha_texto = _texto(datos, "fecha_nacimiento", 10, True) if "fecha_nacimiento" in datos else existentes.get("fecha_nacimiento")
    if not all((nombres, paterno, materno, fecha_texto)):
        raise ValueError("Nombres, ambos apellidos y fecha completa de nacimiento son obligatorios.")
    nombre_completo = " ".join((nombres, paterno, materno))
    if len(nombre_completo) > 160:
        raise ValueError("La suma de nombres y apellidos no puede superar 160 caracteres.")
    try:
        nacimiento = date.fromisoformat(fecha_texto)
    except (ValueError, TypeError):
        raise ValueError("La fecha de nacimiento debe ser válida y estar en formato AAAA-MM-DD.") from None
    if nacimiento.isoformat() != fecha_texto or nacimiento > date.today():
        raise ValueError("La fecha de nacimiento debe ser válida y no futura.")

    iniciales = []
    for parte in (nombres, paterno, materno):
        transliterada = unicodedata.normalize("NFKD", parte[0]).encode("ascii", "ignore").decode("ascii")
        if not transliterada or not transliterada[0].isalpha():
            raise ValueError("Los nombres y apellidos deben comenzar con letras compatibles con el código del instructor.")
        iniciales.append(transliterada[0].upper())
    codigo = f"{''.join(iniciales)}-{nacimiento:%d%m%y}"
    return {
        "nombres": nombres,
        "apellido_paterno": paterno,
        "apellido_materno": materno,
        "fecha_nacimiento": fecha_texto,
        "codigo_instructor": codigo,
        "nombre_completo": nombre_completo,
    }


def _auditar(conexion, accion, resultado="EXITOSO"):
    db.registrar_auditoria(conexion, current_user.id if current_user.is_authenticated else None,
                           accion, resultado, request.remote_addr)


def _descartar_foto(foto):
    if foto:
        from pathlib import Path
        try:
            (Path(current_app.config["PERFIL_MEDIA_FOLDER"]) / foto).unlink(missing_ok=True)
        except OSError:
            current_app.logger.warning("No se pudo limpiar un archivo de perfil no asociado a una solicitud confirmada.")


def _crear_solicitud(datos, invitacion_id=None, jefe_id=None):
    try:
        if "estado" in datos: raise ValueError("Las solicitudes permanecen pendientes hasta aprobación.")
        if jefe_id is None and "grado" in datos: raise ValueError("El grado se asigna desde gestión autorizada.")
        if jefe_id is None and datos.get("pais_residencia") not in (None, "", "Bolivia"):
            raise ValueError("La solicitud registra residencia en Bolivia.")
        if "departamento_residencia" in datos and not datos.get("pais_residencia"):
            datos = dict(datos, pais_residencia="Bolivia")
        residencia = validar_perfil_residencia(datos)
        _grado(datos)
        _validar_alta_completa(datos, residencia)
        identidad = _identidad_instructor(datos)
        especialidad = _especialidad_principal(datos, obligatorio=True)
        username = _texto(datos, "username", 80, True)
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
        antiguedad = residencia.get("antiguedad_desde", _texto(datos, "antiguedad_desde", 10))
        if antiguedad:
            datetime.strptime(antiguedad, "%Y-%m-%d")
    except (ValueError, TypeError) as error:
        return None, None, _fallo(str(error), "datos_invalidos", 400)

    conexion = db.obtener_conexion()
    rol = conexion.execute("SELECT id FROM roles WHERE nombre='INSTRUCTOR_VOLUNTARIO'").fetchone()
    if rol is None:
        return None, None, _fallo("Falta el rol Instructor Voluntario en la base de datos.", "rol_no_configurado", 500)
    from .profile_media import guardar_foto

    try:
        foto = guardar_foto(request.files.get("foto"))
    except ValueError as error:
        return None, None, _fallo(str(error), "foto_invalida", 400)
    try:
        cursor = conexion.execute(
            """INSERT INTO usuarios (username, nombre_completo, correo, password_hash, rol_id, estado, foto_perfil)
               VALUES (?, ?, ?, ?, ?, 'PENDIENTE', ?)""",
            (username, identidad["nombre_completo"], correo, generate_password_hash(password), rol["id"], foto),
        )
        usuario_id = cursor.lastrowid
        conexion.execute(
            """INSERT INTO voluntarios
               (usuario_id, nombres, apellido_paterno, apellido_materno, fecha_nacimiento,
                codigo_instructor, especialidad_principal, experiencia_operaciones, antiguedad_desde,
                pais_residencia, departamento_residencia, ano_incorporacion)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (usuario_id, identidad["nombres"], identidad["apellido_paterno"],
             identidad["apellido_materno"], identidad["fecha_nacimiento"],
             identidad["codigo_instructor"], especialidad, experiencia, antiguedad,
             residencia.get("pais_residencia") if residencia.get("pais_residencia") == "Bolivia" else None, residencia.get("departamento_residencia") if residencia.get("pais_residencia") == "Bolivia" else None, residencia.get("ano_incorporacion")),
        )
        guardar_geografia(conexion, usuario_id, residencia)
        _guardar_incorporacion_grado(conexion, usuario_id, datos, residencia)
        if jefe_id is not None:
            conexion.execute("UPDATE voluntarios SET instructor_id=? WHERE usuario_id=?", (jefe_id, usuario_id))
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
                _descartar_foto(foto)
                return None, None, _fallo("La invitación ya fue utilizada o expiró.", "invitacion_invalida", 404)
        _auditar(conexion, "SOLICITUD_ALTA_JEFE" if jefe_id is not None else "SOLICITUD_REGISTRO")
        conexion.commit()
    except Exception as error:
        conexion.rollback()
        _descartar_foto(foto)
        # Unique constraints deliberately produce the same response for username/email collisions.
        if error.__class__.__name__ == "IntegrityError":
            if "codigo_instructor" in str(error):
                return None, None, _fallo("Ya existe otro Instructor Voluntario con ese código generado; administración debe revisar el conflicto.", "codigo_instructor_duplicado", 409)
            return None, None, _fallo("No se pudo registrar la solicitud. Verifica los datos e inténtalo de nuevo.", "registro_no_disponible", 409)
        raise
    return usuario_id, identidad["codigo_instructor"], None


@management_bp.post("/api/jefe-personal/instructores-voluntarios")
@role_required("JEFE_PERSONAL")
def solicitar_alta_equipo():
    """Registra una solicitud pendiente asignada al Jefe autenticado."""
    datos = _datos_form_o_json()
    if datos is None:
        return _fallo("Solicitud no válida.", "solicitud_invalida", 400)
    permitidos = {"nombres", "apellido_paterno", "apellido_materno", "fecha_nacimiento",
                  "especialidad_principal", "username", "correo", "password",
                  "experiencia_operaciones", "antiguedad_desde"}
    permitidos |= CAMPOS_RESIDENCIA | {"grado"}
    if set(datos) - permitidos:
        return _fallo("Se enviaron campos no permitidos para el alta.", "campos_no_permitidos", 400)
    conexion = db.obtener_conexion()
    if not conexion.execute("SELECT 1 FROM instructores WHERE usuario_id=?", (current_user.id,)).fetchone():
        return _fallo("Falta el perfil de Jefe de Personal.", "perfil_no_encontrado", 409)
    usuario_id, codigo, error = _crear_solicitud(datos, jefe_id=current_user.id)
    if error is not None:
        return error
    return jsonify(ok=True, id=usuario_id, codigo_instructor=codigo, estado="PENDIENTE",
                   mensaje="Solicitud registrada. Requiere aprobación del Administrador."), 201


@management_bp.post("/api/registro/solicitudes")
def solicitar_registro():
    datos = _datos_form_o_json()
    if datos is None:
        return _fallo("Solicitud no válida.", "solicitud_invalida", 400)
    _, codigo, respuesta = _crear_solicitud(datos)
    if respuesta:
        return respuesta
    return jsonify(ok=True, estado="PENDIENTE", codigo_instructor=codigo,
                   mensaje="Solicitud recibida; requiere aprobación administrativa."), 201


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
    datos = _datos_form_o_json()
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
    usuario_id, codigo, respuesta = _crear_solicitud(datos, invitacion["id"])
    if respuesta:
        return respuesta
    return jsonify(ok=True, estado="PENDIENTE", codigo_instructor=codigo,
                   mensaje="Registro recibido; la cuenta requiere aprobación."), 201


@management_bp.get("/api/admin/solicitudes")
@role_required("ADMINISTRADOR")
def listar_solicitudes():
    filas = db.obtener_conexion().execute(
        """SELECT s.id, u.id AS usuario_id, u.username, u.nombre_completo AS nombre, u.correo,
                  v.nombres, v.apellido_paterno, v.apellido_materno,
                  v.fecha_nacimiento, v.codigo_instructor,
                  (u.foto_perfil IS NOT NULL) AS tiene_foto,
                  s.estado, s.creada_en, s.invitacion_id, v.instructor_id
           FROM solicitudes_registro s JOIN usuarios u ON u.id = s.usuario_id
           JOIN voluntarios v ON v.usuario_id = u.id
           WHERE s.estado = 'PENDIENTE' ORDER BY s.creada_en, s.id"""
    ).fetchall()
    return jsonify(solicitudes=[dict(fila) for fila in filas]), 200


@management_bp.post("/api/admin/instructores-voluntarios")
@role_required("ADMINISTRADOR")
def crear_instructor_voluntario():
    """Crea desde administración una cuenta activa sin pasar por solicitudes."""
    datos = _datos_form_o_json()
    if datos is None:
        return _fallo("Solicitud no válida.", "solicitud_invalida", 400)
    try:
        estado_inicial = datos.get("estado", "ACTIVO")
        if estado_inicial not in ("ACTIVO", "INACTIVO"): raise ValueError("Selecciona Activo o Inactivo.")
        _grado(datos)
        residencia = validar_perfil_residencia(datos)
        _validar_alta_completa(datos, residencia)
        identidad = _identidad_instructor(datos)
        especialidad = _especialidad_principal(datos, obligatorio=True)
        username = _texto(datos, "username", 80, True)
        correo = _texto(datos, "correo", 254)
        if correo:
            correo = correo.casefold()
        password = datos.get("password")
        if not USERNAME_RE.fullmatch(username):
            raise ValueError("El nombre de usuario debe tener entre 3 y 80 caracteres válidos.")
        if correo and ("@" not in correo or any(char.isspace() for char in correo)):
            raise ValueError("El correo no es válido.")
        if not isinstance(password, str) or not 12 <= len(password) <= 256:
            raise ValueError("La contraseña inicial debe tener entre 12 y 256 caracteres.")
        experiencia = _texto(datos, "experiencia_operaciones", 2000)
        antiguedad = residencia.get("antiguedad_desde", _texto(datos, "antiguedad_desde", 10))
        if antiguedad:
            datetime.strptime(antiguedad, "%Y-%m-%d")
        jefe_dato = datos.get("instructor_id")
        if jefe_dato in (None, ""):
            jefe_id = None
        elif isinstance(jefe_dato, int) and not isinstance(jefe_dato, bool):
            jefe_id = jefe_dato
        elif isinstance(jefe_dato, str) and jefe_dato.isdecimal():
            jefe_id = int(jefe_dato)
        else:
            raise ValueError("El Jefe de Personal asignado no es válido.")
    except (ValueError, TypeError) as error:
        return _fallo(str(error), "datos_invalidos", 400)

    conexion = db.obtener_conexion()
    if jefe_id is not None and not conexion.execute(
        """SELECT 1 FROM instructores i JOIN usuarios u ON u.id=i.usuario_id
           JOIN roles r ON r.id=u.rol_id
           WHERE i.usuario_id=? AND u.estado='ACTIVO' AND r.nombre='JEFE_PERSONAL'""",
        (jefe_id,),
    ).fetchone():
        return _fallo("El Jefe de Personal asignado no existe o no está activo.", "jefe_personal_no_valido", 400)

    rol = conexion.execute(
        "SELECT id FROM roles WHERE nombre='INSTRUCTOR_VOLUNTARIO'"
    ).fetchone()
    if rol is None:
        return _fallo("Falta el rol Instructor Voluntario en la base de datos.", "rol_no_configurado", 500)

    from .profile_media import guardar_foto
    try:
        foto = guardar_foto(request.files.get("foto"))
    except ValueError as error:
        return _fallo(str(error), "foto_invalida", 400)

    try:
        cursor = conexion.execute(
            """INSERT INTO usuarios (username, nombre_completo, correo, password_hash,
                                     rol_id, estado, foto_perfil)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (username, identidad["nombre_completo"], correo, generate_password_hash(password), rol["id"], estado_inicial, foto),
        )
        usuario_id = cursor.lastrowid
        conexion.execute(
            """INSERT INTO voluntarios
               (usuario_id, instructor_id, nombres, apellido_paterno, apellido_materno,
                fecha_nacimiento, codigo_instructor, especialidad_principal, experiencia_operaciones, antiguedad_desde,
                pais_residencia, departamento_residencia, ano_incorporacion)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (usuario_id, jefe_id, identidad["nombres"], identidad["apellido_paterno"],
             identidad["apellido_materno"], identidad["fecha_nacimiento"],
             identidad["codigo_instructor"], especialidad, experiencia, antiguedad,
             residencia.get("pais_residencia") if residencia.get("pais_residencia") == "Bolivia" else None, residencia.get("departamento_residencia") if residencia.get("pais_residencia") == "Bolivia" else None, residencia.get("ano_incorporacion")),
        )
        guardar_geografia(conexion, usuario_id, residencia)
        _guardar_incorporacion_grado(conexion, usuario_id, datos, residencia)
        _auditar(conexion, "INSTRUCTOR_VOLUNTARIO_CREADO_MANUALMENTE")
        conexion.commit()
    except Exception as error:
        conexion.rollback()
        _descartar_foto(foto)
        if error.__class__.__name__ == "IntegrityError":
            if "codigo_instructor" in str(error):
                return _fallo("Ya existe otro Instructor Voluntario con ese código generado; revisa el nombre y la fecha de nacimiento.", "codigo_instructor_duplicado", 409)
            return _fallo("El nombre de usuario o correo ya está asociado a otra cuenta.", "cuenta_duplicada", 409)
        raise
    return jsonify(ok=True, id=usuario_id, estado=estado_inicial, codigo_instructor=identidad["codigo_instructor"],
                   mensaje="Instructor Voluntario guardado."), 201


@management_bp.get("/api/admin/instructores")
@management_bp.get("/api/admin/jefes-personal")
@role_required("ADMINISTRADOR")
def listar_instructores():
    filas = db.obtener_conexion().execute(
        """SELECT i.usuario_id AS id, u.username, u.nombre_completo AS nombre,
                  u.correo, u.estado, (u.foto_perfil IS NOT NULL) AS tiene_foto, i.especialidad,
                  (SELECT COUNT(*) FROM voluntarios v JOIN usuarios uv ON uv.id=v.usuario_id
                   WHERE v.instructor_id=i.usuario_id AND uv.estado='ACTIVO') AS voluntarios_activos
           FROM instructores i JOIN usuarios u ON u.id=i.usuario_id
           ORDER BY u.nombre_completo, u.id"""
    ).fetchall()
    return jsonify(instructores=[dict(fila) for fila in filas]), 200


@management_bp.post("/api/admin/instructores")
@management_bp.post("/api/admin/jefes-personal")
@role_required("ADMINISTRADOR")
def crear_instructor():
    datos = _datos_form_o_json()
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

    from .profile_media import guardar_foto

    try:
        foto = guardar_foto(request.files.get("foto"))
    except ValueError as error:
        return _fallo(str(error), "foto_invalida", 400)
    conexion = db.obtener_conexion()
    rol_id = conexion.execute("SELECT id FROM roles WHERE nombre='JEFE_PERSONAL'").fetchone()[0]
    ahora = _now()
    try:
        cursor = conexion.execute(
            """INSERT INTO usuarios (username, nombre_completo, correo, password_hash, rol_id, estado, foto_perfil)
               VALUES (?, ?, ?, ?, ?, 'ACTIVO', ?)""",
            (username, nombre, correo.casefold() if correo else None, generate_password_hash(password), rol_id, foto),
        )
        usuario_id = cursor.lastrowid
        conexion.execute("INSERT INTO instructores (usuario_id, especialidad) VALUES (?, ?)", (usuario_id, especialidad))
        _auditar(conexion, "JEFE_PERSONAL_CREADO")
        conexion.commit()
    except Exception as error:
        conexion.rollback()
        if error.__class__.__name__ == "IntegrityError":
            return _fallo("Ya existe un Jefe activo o el usuario/correo está ocupado.", "cuenta_duplicada", 409)
        raise
    return jsonify(ok=True, id=usuario_id, estado="ACTIVO"), 201


@management_bp.patch("/api/admin/instructores/<int:usuario_id>")
@management_bp.patch("/api/admin/jefes-personal/<int:usuario_id>")
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
        return _fallo("Jefe de Personal no encontrado.", "jefe_personal_no_encontrado", 404)
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
    if not campos and secundarias is None:
        return _fallo("No se enviaron campos para actualizar.", "sin_cambios", 400)
    nombre = campos.pop("nombre", instructor["nombre_completo"])
    correo = campos.pop("correo", instructor["correo"])
    especialidad = campos.pop("especialidad", instructor["especialidad"])
    try:
        conexion.execute("UPDATE usuarios SET nombre_completo=?, correo=?, actualizado_en=? WHERE id=?",
                         (nombre, correo, _now(), usuario_id))
        conexion.execute("UPDATE instructores SET especialidad=? WHERE usuario_id=?", (especialidad, usuario_id))
        _auditar(conexion, "JEFE_PERSONAL_EDITADO")
        conexion.commit()
    except Exception as error:
        conexion.rollback()
        if error.__class__.__name__ == "IntegrityError":
            return _fallo("El correo ya está asociado a otra cuenta.", "correo_duplicado", 409)
        raise
    return jsonify(ok=True, mensaje="Perfil de instructor actualizado."), 200


@management_bp.patch("/api/admin/perfil")
@role_required("ADMINISTRADOR")
def editar_perfil_administrador():
    datos = _datos_form_o_json()
    if datos is None:
        return _fallo("Solicitud no válida.", "solicitud_invalida", 400)
    try:
        nombre = _texto(datos, "nombre", 160, True)
        nueva_clave = datos.get("nueva_clave", "")
        clave_actual = datos.get("clave_actual", "")
        if nueva_clave and (not isinstance(nueva_clave, str) or not 12 <= len(nueva_clave) <= 256):
            raise ValueError("La nueva contraseña debe tener entre 12 y 256 caracteres.")
        if nueva_clave and (not isinstance(clave_actual, str) or len(clave_actual) > 256):
            raise ValueError("La contraseña actual no es válida.")
        if nueva_clave and datos.get("confirmar_clave") != nueva_clave:
            raise ValueError("La confirmación no coincide con la nueva contraseña.")
    except (TypeError, ValueError) as error:
        return _fallo(str(error), "datos_invalidos", 400)

    conexion = db.obtener_conexion()
    fila = conexion.execute("SELECT password_hash FROM usuarios WHERE id=?", (current_user.id,)).fetchone()
    if nueva_clave:
        from werkzeug.security import check_password_hash
        if not clave_actual or not check_password_hash(fila["password_hash"], clave_actual):
            return _fallo("La contraseña actual no coincide.", "clave_actual_invalida", 400)

    from .profile_media import guardar_foto
    try:
        foto = guardar_foto(request.files.get("foto"))
    except ValueError as error:
        return _fallo(str(error), "foto_invalida", 400)
    ahora = _now()
    if foto is not None:
        conexion.execute("UPDATE usuarios SET foto_perfil=? WHERE id=?", (foto, current_user.id))
    if nueva_clave:
        conexion.execute(
            "UPDATE usuarios SET nombre_completo=?, password_hash=?, password_version=password_version+1, actualizado_en=? WHERE id=?",
            (nombre, generate_password_hash(nueva_clave), ahora, current_user.id),
        )
    else:
        conexion.execute("UPDATE usuarios SET nombre_completo=?, actualizado_en=? WHERE id=?", (nombre, ahora, current_user.id))
    _auditar(conexion, "PERFIL_ADMIN_EDITADO")
    conexion.commit()
    requiere_login = bool(nueva_clave)
    if requiere_login:
        from flask import session
        from flask_login import logout_user
        logout_user()
        session.clear()
    return jsonify(ok=True, mensaje="Perfil actualizado.", requiere_nuevo_login=requiere_login), 200


@management_bp.post("/api/admin/usuarios/<int:usuario_id>/restablecer-clave")
@role_required("ADMINISTRADOR")
def restablecer_clave(usuario_id):
    datos = _datos_json()
    password = datos.get("password") if datos else None
    if not isinstance(password, str) or not 12 <= len(password) <= 256:
        return _fallo("La nueva contraseña debe tener entre 12 y 256 caracteres.", "datos_invalidos", 400)
    conexion = db.obtener_conexion()
    fila = conexion.execute(
        """SELECT u.id FROM usuarios u JOIN roles r ON r.id=u.rol_id
           WHERE u.id=? AND r.nombre IN ('JEFE_PERSONAL','INSTRUCTOR_VOLUNTARIO','COMANDANTE_GRUPO')""", (usuario_id,)
    ).fetchone()
    if not fila:
        return _fallo("Perfil no encontrado.", "perfil_no_encontrado", 404)
    conexion.execute(
        "UPDATE usuarios SET password_hash=?, password_version=password_version+1, actualizado_en=? WHERE id=?",
        (generate_password_hash(password), _now(), usuario_id),
    )
    _auditar(conexion, "CLAVE_RESTABLECIDA_ADMIN")
    conexion.commit()
    return jsonify(ok=True, mensaje="Contraseña restablecida. Las sesiones anteriores quedaron invalidadas."), 200


@management_bp.route("/api/usuarios/<int:usuario_id>/foto", methods=["GET", "PUT"])
@role_required("ADMINISTRADOR", "JEFE_PERSONAL", "INSTRUCTOR_VOLUNTARIO")
def foto_perfil(usuario_id):
    conexion = db.obtener_conexion()
    fila = conexion.execute(
        """SELECT u.foto_perfil, u.estado, r.nombre AS rol FROM usuarios u JOIN roles r ON r.id=u.rol_id
           WHERE u.id=? AND r.nombre IN ('ADMINISTRADOR','JEFE_PERSONAL','INSTRUCTOR_VOLUNTARIO')""", (usuario_id,)
    ).fetchone()
    if not fila:
        return _fallo("Perfil no encontrado.", "perfil_no_encontrado", 404)
    es_admin = current_user.rol == "ADMINISTRADOR"
    es_propio = current_user.id == usuario_id
    es_equipo = current_user.rol == "JEFE_PERSONAL" and fila["estado"] in ("ACTIVO","INACTIVO") and fila["rol"] == "INSTRUCTOR_VOLUNTARIO" and conexion.execute(
        "SELECT 1 FROM voluntarios WHERE usuario_id=?", (usuario_id,)
    ).fetchone()
    if request.method == "PUT":
        if not (es_admin or es_propio):
            return _fallo("No tienes permiso para cambiar esta foto.", "sin_permiso", 403)
        if request.files.get("foto") is None:
            return _fallo("Selecciona una foto PNG o JPEG.", "foto_requerida", 400)
        from .profile_media import guardar_foto

        try:
            nombre = guardar_foto(request.files.get("foto"))
        except ValueError as error:
            return _fallo(str(error), "foto_invalida", 400)
        conexion.execute("UPDATE usuarios SET foto_perfil=?, actualizado_en=? WHERE id=?", (nombre, _now(), usuario_id))
        _auditar(conexion, "FOTO_PERFIL_ACTUALIZADA")
        conexion.commit()
        return jsonify(ok=True, mensaje="Foto de perfil actualizada."), 200
    if not (es_admin or es_propio or es_equipo):
        return _fallo("No tienes permiso para ver esta foto.", "sin_permiso", 403)
    if not fila["foto_perfil"]:
        return _fallo("Este perfil aún no tiene foto.", "foto_no_encontrada", 404)
    if not re.fullmatch(r"[0-9a-f]{32}\.(?:png|jpg)", fila["foto_perfil"]):
        return _fallo("Foto no disponible.", "foto_no_encontrada", 404)
    extension = fila["foto_perfil"].rsplit(".", 1)[-1]
    respuesta = send_file(
        current_app.config["PERFIL_MEDIA_FOLDER"] + "/" + fila["foto_perfil"],
        mimetype="image/png" if extension == "png" else "image/jpeg",
        conditional=False,
    )
    respuesta.headers["Cache-Control"] = "private, no-store"
    respuesta.headers["X-Content-Type-Options"] = "nosniff"
    respuesta.headers["Content-Security-Policy"] = "default-src 'none'; sandbox"
    return respuesta


@management_bp.post("/api/admin/instructores/<int:usuario_id>/desactivar")
@management_bp.post("/api/admin/jefes-personal/<int:usuario_id>/desactivar")
@role_required("ADMINISTRADOR")
def desactivar_instructor(usuario_id):
    conexion = db.obtener_conexion()
    fila = conexion.execute("SELECT estado FROM usuarios u JOIN instructores i ON i.usuario_id=u.id WHERE u.id=?", (usuario_id,)).fetchone()
    if not fila:
        return _fallo("Jefe de Personal no encontrado.", "jefe_personal_no_encontrado", 404)
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
    _auditar(conexion, "JEFE_PERSONAL_DESACTIVADO")
    if cursor.rowcount:
        _auditar(conexion, "INSTRUCTORES_VOLUNTARIOS_REASIGNADOS_POR_BAJA")
    conexion.commit()
    return jsonify(ok=True, estado="INACTIVO", voluntarios_desvinculados=cursor.rowcount), 200


@management_bp.post("/api/admin/solicitudes/<int:solicitud_id>/aprobar")
@role_required("ADMINISTRADOR")
def aprobar_solicitud(solicitud_id):
    datos = _datos_json() or {}
    instructor_id = datos.get("instructor_id")
    conexion = db.obtener_conexion()
    solicitud = conexion.execute(
        """SELECT s.usuario_id, v.instructor_id FROM solicitudes_registro s
           JOIN voluntarios v ON v.usuario_id=s.usuario_id
           WHERE s.id = ? AND s.estado = 'PENDIENTE'""",
        (solicitud_id,),
    ).fetchone()
    if not solicitud:
        return _fallo("No existe una solicitud pendiente con ese identificador.", "solicitud_no_encontrada", 404)
    if "instructor_id" not in datos:
        instructor_id = solicitud["instructor_id"]
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
                         (u.foto_perfil IS NOT NULL) AS tiene_foto,
                         v.instructor_id, v.nombres, v.apellido_paterno, v.apellido_materno,
                         v.fecha_nacimiento, v.codigo_instructor, v.especialidad_principal,
                         v.experiencia_operaciones, v.antiguedad_desde,
                         v.pais_residencia, v.departamento_residencia, v.ano_incorporacion, v.fecha_incorporacion, v.grado
                  FROM usuarios u JOIN voluntarios v ON v.usuario_id=u.id
                  JOIN roles r ON r.id=u.rol_id WHERE u.id=? AND r.nombre='INSTRUCTOR_VOLUNTARIO'"""
    fila = conexion.execute(consulta, (usuario_id,)).fetchone()
    if fila and current_user.rol == "JEFE_PERSONAL" and fila["estado"] not in ("ACTIVO", "INACTIVO"):
        return None
    if fila:
        fila = dict(fila); fila.update(leer_geografia(conexion, usuario_id))
    return fila


@management_bp.get("/api/voluntarios")
@management_bp.get("/api/instructores-voluntarios")
@role_required("ADMINISTRADOR", "JEFE_PERSONAL")
def listar_voluntarios():
    conexion = db.obtener_conexion()
    consulta = """SELECT u.id, u.username, u.nombre_completo AS nombre, u.correo, u.estado,
                         (u.foto_perfil IS NOT NULL) AS tiene_foto,
                         v.instructor_id, ui.nombre_completo AS instructor_nombre,
                         v.nombres, v.apellido_paterno, v.apellido_materno,
                         v.fecha_nacimiento, v.codigo_instructor, v.especialidad_principal,
                         v.experiencia_operaciones, v.antiguedad_desde,
                         v.pais_residencia, v.departamento_residencia, v.ano_incorporacion, v.fecha_incorporacion, v.grado
                  FROM voluntarios v JOIN usuarios u ON u.id=v.usuario_id
                  LEFT JOIN usuarios ui ON ui.id=v.instructor_id
                  ORDER BY u.nombre_completo, u.id"""
    parametros = ()
    if current_user.rol == "JEFE_PERSONAL":
        consulta = consulta.replace("ORDER BY", "WHERE u.estado IN ('ACTIVO','INACTIVO') ORDER BY")
    filas = conexion.execute(consulta, parametros).fetchall()
    # La antigüedad se calcula al consultar, sin persistir un resultado que envejezca.
    perfiles = [dict(fila) for fila in filas]
    for perfil in perfiles:
        perfil.update(leer_geografia(conexion, perfil["id"]))
        perfil["especialidades_secundarias"] = _leer_secundarias(conexion, perfil["id"])
        perfil["antiguedad_anos"] = antiguedad_calculada(perfil["ano_incorporacion"])
    return jsonify(voluntarios=perfiles), 200


@management_bp.patch("/api/voluntarios/<int:usuario_id>")
@management_bp.patch("/api/instructores-voluntarios/<int:usuario_id>")
@role_required("ADMINISTRADOR", "JEFE_PERSONAL")
def editar_voluntario(usuario_id):
    datos = _datos_json()
    if datos is None:
        return _fallo("Solicitud no válida.", "solicitud_invalida", 400)
    conexion = db.obtener_conexion()
    voluntario = _alcance_voluntario(conexion, usuario_id)
    if not voluntario:
        return _fallo("Instructor Voluntario no encontrado en tu ámbito.", "instructor_voluntario_no_encontrado", 404)
    if current_user.rol == "JEFE_PERSONAL" and voluntario["estado"] != "ACTIVO":
        return _fallo("Activa primero la cuenta desde el directorio para editar su perfil.", "cuenta_inactiva", 409)
    campos = {}
    identidad = None
    secundarias = None
    try:
        if "especialidades_secundarias" in datos:
            secundarias = datos["especialidades_secundarias"]
            if (not isinstance(secundarias, list) or len(secundarias) > len(ESPECIALIDADES_PRINCIPALES)
                    or any(not isinstance(v, str) or v not in ESPECIALIDADES_PRINCIPALES for v in secundarias)
                    or len(set(secundarias)) != len(secundarias)):
                raise ValueError("Selecciona especialidades secundarias válidas, sin duplicados.")
        campos.update(validar_perfil_residencia(datos, dict(voluntario)))
        if "grado" in datos: campos["grado"] = _grado(datos)
        campos_identidad = {"nombres", "apellido_paterno", "apellido_materno", "fecha_nacimiento"}
        if campos_identidad.intersection(datos):
            identidad = _identidad_instructor(datos, dict(voluntario))
            campos.update({k: identidad[k] for k in ("nombres", "apellido_paterno", "apellido_materno", "fecha_nacimiento", "codigo_instructor")})
        for campo, limite in (("correo", 254), ("experiencia_operaciones", 2000), ("antiguedad_desde", 10)):
            if campo in datos:
                valor = _texto(datos, campo, limite)
                if campo == "correo" and valor:
                    valor = valor.casefold()
                if campo == "correo" and valor and ("@" not in valor or any(char.isspace() for char in valor)):
                    raise ValueError("El correo no es válido.")
                if campo == "antiguedad_desde" and valor:
                    datetime.strptime(valor, "%Y-%m-%d")
                campos[campo] = valor
        if "especialidad_principal" in datos:
            campos["especialidad_principal"] = _especialidad_principal(datos)
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
    if not campos and secundarias is None:
        return _fallo("No se enviaron campos para actualizar.", "sin_cambios", 400)
    correo = campos.pop("correo", voluntario["correo"])
    ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        if identidad:
            conexion.execute("UPDATE usuarios SET nombre_completo=?, correo=?, actualizado_en=? WHERE id=?",
                             (identidad["nombre_completo"], correo, ahora, usuario_id))
        elif "correo" in datos:
            conexion.execute("UPDATE usuarios SET correo=?, actualizado_en=? WHERE id=?", (correo, ahora, usuario_id))
        guardar_geografia(conexion, usuario_id, campos, voluntario)
        if campos.get("pais_residencia") not in (None, "Bolivia"):
            campos["pais_residencia"] = None; campos["departamento_residencia"] = None
        perfil = {k: v for k, v in campos.items() if k in {
            "nombres", "apellido_paterno", "apellido_materno", "fecha_nacimiento", "codigo_instructor",
            "experiencia_operaciones", "antiguedad_desde", "especialidad_principal", "instructor_id",
            "pais_residencia", "departamento_residencia", "ano_incorporacion", "fecha_incorporacion", "grado",
        }}
        if perfil:
            asignaciones = ", ".join(f"{campo}=?" for campo in perfil)
            conexion.execute(f"UPDATE voluntarios SET {asignaciones} WHERE usuario_id=?", (*perfil.values(), usuario_id))
        if secundarias is not None:
            conexion.execute("DELETE FROM especialidades_secundarias WHERE voluntario_id=?", (usuario_id,))
            conexion.executemany("INSERT INTO especialidades_secundarias (voluntario_id, especialidad) VALUES (?, ?)",
                                 ((usuario_id, valor) for valor in secundarias))
        _auditar(conexion, "INSTRUCTOR_VOLUNTARIO_EDITADO")
        conexion.commit()
    except Exception as error:
        conexion.rollback()
        if error.__class__.__name__ == "IntegrityError":
            if identidad and "codigo_instructor" in str(error):
                return _fallo("Ya existe otro Instructor Voluntario con ese código generado; revisa el nombre y la fecha de nacimiento.", "codigo_instructor_duplicado", 409)
            return _fallo("El correo ya está asociado a otra cuenta.", "correo_duplicado", 409)
        raise
    return jsonify(ok=True, codigo_instructor=identidad["codigo_instructor"] if identidad else voluntario["codigo_instructor"],
                   mensaje="Perfil actualizado."), 200


@management_bp.post("/api/voluntarios/<int:usuario_id>/desactivar")
@management_bp.post("/api/instructores-voluntarios/<int:usuario_id>/desactivar")
@role_required("ADMINISTRADOR", "JEFE_PERSONAL")
def desactivar_voluntario(usuario_id):
    return _cambiar_estado_voluntario(usuario_id, "INACTIVO")


@management_bp.patch("/api/instructores-voluntarios/<int:usuario_id>/estado")
@role_required("ADMINISTRADOR", "JEFE_PERSONAL")
def cambiar_estado_voluntario(usuario_id):
    datos = _datos_json()
    if (not isinstance(datos, dict) or set(datos) != {"estado", "estado_anterior"}
            or datos.get("estado") not in ("ACTIVO", "INACTIVO")
            or datos.get("estado_anterior") not in ("ACTIVO", "INACTIVO")):
        return _fallo("Indica un estado ACTIVO/INACTIVO y su estado anterior.", "datos_invalidos", 400)
    return _cambiar_estado_voluntario(usuario_id, datos["estado"], datos["estado_anterior"])


def _cambiar_estado_voluntario(usuario_id, estado, estado_anterior=None):
    conexion = db.obtener_conexion()
    conexion.execute("BEGIN IMMEDIATE")
    voluntario = _alcance_voluntario(conexion, usuario_id)
    if not voluntario:
        conexion.rollback()
        return _fallo("Instructor Voluntario no encontrado en tu ámbito.", "instructor_voluntario_no_encontrado", 404)
    if voluntario["estado"] not in ("ACTIVO", "INACTIVO"):
        conexion.rollback()
        return _fallo("Las solicitudes pendientes o rechazadas requieren revisión administrativa.", "estado_no_permitido", 409)
    if estado_anterior is not None and voluntario["estado"] != estado_anterior:
        conexion.rollback()
        return _fallo("El estado cambió. Actualiza el directorio antes de continuar.", "conflicto_estado", 409)
    if voluntario["estado"] == estado:
        conexion.rollback()
        return jsonify(ok=True, estado=estado, sin_cambios=True), 200
    ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    # La versión invalida sesiones previas incluso si se reactiva antes de su próxima petición.
    conexion.execute("UPDATE usuarios SET estado=?, password_version=password_version+1, actualizado_en=? WHERE id=?", (estado, ahora, usuario_id))
    accion = "ACTIVADO" if estado == "ACTIVO" else "DESACTIVADO"
    _auditar(conexion, f"INSTRUCTOR_VOLUNTARIO_{accion}:{usuario_id}:{voluntario['estado']}->{estado}")
    conexion.commit()
    return jsonify(ok=True, estado=estado), 200
