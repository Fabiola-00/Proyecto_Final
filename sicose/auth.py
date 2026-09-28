"""Login, cierre de sesión y API del usuario actual."""

from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, render_template, request, session
from flask_login import current_user, login_required, login_user, logout_user

from . import db

auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/login")
def login_page():
    if current_user.is_authenticated:
        return render_template("inicio.html", usuario=current_user)
    return render_template("login.html")


@auth_bp.post("/api/auth/login")
def login_api():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        return jsonify(error="Solicitud no válida.", codigo="solicitud_invalida"), 400

    username = datos.get("username")
    password = datos.get("password")
    if (
        not isinstance(username, str)
        or not isinstance(password, str)
        or not username.strip()
        or not password
        or len(username) > 80
        or len(password) > 256
    ):
        return jsonify(error="Solicitud no válida.", codigo="solicitud_invalida"), 400

    usuario = db.validar_credenciales(username.strip(), password)
    conexion = db.obtener_conexion()
    if usuario is None:
        db.registrar_auditoria(
            conexion, None, "LOGIN", "FALLIDO", request.remote_addr
        )
        conexion.commit()
        return jsonify(error="Usuario o contraseña incorrectos.", codigo="credenciales_invalidas"), 401

    ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conexion.execute(
        "UPDATE usuarios SET ultimo_acceso = ?, actualizado_en = ? WHERE id = ?",
        (ahora, ahora, usuario.id),
    )
    db.registrar_auditoria(conexion, usuario.id, "LOGIN", "EXITOSO", request.remote_addr)
    conexion.commit()

    session.clear()
    session.permanent = True
    login_user(usuario, fresh=True)
    current_app.logger.info("Inicio de sesión exitoso para usuario_id=%s", usuario.id)
    return jsonify(ok=True, usuario=usuario.publico(), redirect_url="/"), 200


@auth_bp.post("/api/auth/logout")
@login_required
def logout_api():
    usuario_id = current_user.id
    conexion = db.obtener_conexion()
    logout_user()
    session.clear()
    db.registrar_auditoria(conexion, usuario_id, "LOGOUT", "EXITOSO", request.remote_addr)
    conexion.commit()
    return jsonify(ok=True, mensaje="Sesión cerrada."), 200


@auth_bp.get("/api/auth/me")
@login_required
def me_api():
    return jsonify(usuario=current_user.publico()), 200
