"""Fábrica de la aplicación Flask SICOSE."""

import os
from datetime import timedelta
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_wtf.csrf import CSRFError

from .extensions import csrf, login_manager


def _entorno_verdadero(valor):
    return str(valor or "").strip().lower() in {"1", "true", "yes", "si", "sí"}


def create_app(test_config=None):
    """Crea SICOSE con secretos externos y configuración sustituible en pruebas."""
    frontend = Path(__file__).resolve().parent.parent / "frontend"
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=str(frontend),
        static_folder=str(frontend / "static"),
    )
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SICOSE_SECRET_KEY"),
        DATABASE=os.environ.get(
            "SICOSE_DATABASE", str(Path(app.instance_path) / "sicose.sqlite3")
        ),
        SESSION_COOKIE_NAME="sicose_session",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=_entorno_verdadero(
            os.environ.get("SICOSE_SESSION_COOKIE_SECURE")
        ),
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        SESSION_REFRESH_EACH_REQUEST=False,
        WTF_CSRF_TIME_LIMIT=3600,
    )
    if test_config is not None:
        app.config.update(test_config)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError(
            "Falta SICOSE_SECRET_KEY. Configura un secreto local en .env antes de iniciar."
        )

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    csrf.init_app(app)
    login_manager.init_app(app)

    from . import db
    from .auth import auth_bp
    from .dashboard import dashboard_bp

    db.init_app(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)

    @login_manager.user_loader
    def cargar_usuario(user_id):
        return db.obtener_usuario_por_id(user_id, solo_activo=True)

    @login_manager.unauthorized_handler
    def no_autorizado():
        if request.path.startswith("/api/"):
            return jsonify(error="No autenticado.", codigo="no_autenticado"), 401
        return redirect(url_for("auth.login_page"))

    @app.errorhandler(CSRFError)
    def error_csrf(_error):
        return jsonify(error="La solicitud expiró o no es válida.", codigo="csrf_invalido"), 400

    @app.errorhandler(403)
    def acceso_denegado(_error):
        if request.path.startswith("/api/"):
            return jsonify(error="No tienes permiso para esta operación.", codigo="sin_permiso"), 403
        return render_template("error.html", codigo=403, mensaje="No tienes permiso para ver esta página."), 403

    @app.get("/")
    @login_required
    def inicio():
        paneles = {
            "ADMINISTRADOR": "dashboard.administrador",
            "INSTRUCTOR": "dashboard.instructor",
            "VOLUNTARIO": "dashboard.voluntario",
        }
        endpoint = paneles.get(current_user.rol)
        if endpoint is None:
            return jsonify(error="Rol sin panel asignado.", codigo="rol_no_configurado"), 403
        return redirect(url_for(endpoint))

    return app
