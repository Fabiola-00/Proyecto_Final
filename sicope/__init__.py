"""Fábrica de la aplicación Flask SICOPE."""

import os
from pathlib import Path

from flask import Flask, jsonify, render_template


def create_app(test_config=None):
    """Crea la aplicación y permite sustituir su configuración en pruebas."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SICOPE_SECRET_KEY"),
        DATABASE=os.environ.get(
            "SICOPE_DATABASE", str(Path(app.instance_path) / "sicope.sqlite3")
        ),
    )

    if test_config is not None:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    from . import db

    db.init_app(app)

    @app.get("/")
    def inicio():
        return render_template("inicio.html")

    @app.get("/api/health")
    def salud():
        return jsonify(estado="ok", aplicacion="SICOPE")

    return app
