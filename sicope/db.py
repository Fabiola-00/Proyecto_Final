"""Conexión SQLite y comando de inicialización del esquema base."""

import sqlite3
from pathlib import Path

import click
from flask import current_app, g


def obtener_conexion():
    """Obtiene una conexión SQLite asociada a la solicitud/contexto actual."""
    if "conexion_db" not in g:
        configuracion_ruta = current_app.config["DATABASE"]
        if configuracion_ruta == ":memory:":
            g.conexion_db = sqlite3.connect(":memory:")
        else:
            ruta = Path(configuracion_ruta)
            if not ruta.is_absolute():
                ruta = Path(current_app.root_path).parent / ruta
            ruta.parent.mkdir(parents=True, exist_ok=True)
            g.conexion_db = sqlite3.connect(ruta)
        g.conexion_db.row_factory = sqlite3.Row
        g.conexion_db.execute("PRAGMA foreign_keys = ON")
    return g.conexion_db


def cerrar_conexion(_error=None):
    conexion = g.pop("conexion_db", None)
    if conexion is not None:
        conexion.close()


def inicializar_base_datos():
    """Crea solo metadatos de esquema; aún no crea entidades de negocio."""
    conexion = obtener_conexion()
    esquema = Path(current_app.root_path) / "schema.sql"
    conexion.executescript(esquema.read_text(encoding="utf-8"))
    conexion.commit()


@click.command("init-db")
def comando_init_db():
    """Inicializa la base de datos local sin borrar contenido existente."""
    inicializar_base_datos()
    click.echo("Base SQLite inicializada (esquema base).")


def init_app(app):
    app.teardown_appcontext(cerrar_conexion)
    app.cli.add_command(comando_init_db)
