"""Persistencia SQLite, seed idempotente y auditoría mínima."""

import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import click
from flask import current_app, g
from werkzeug.security import check_password_hash, generate_password_hash

from .models import Usuario

ROLES = ("ADMINISTRADOR", "INSTRUCTOR", "VOLUNTARIO")
USERNAME_RE = re.compile(r"^[A-Za-z0-9._-]{3,80}$")


def obtener_conexion():
    if "conexion_db" not in g:
        configuracion_ruta = current_app.config["DATABASE"]
        if configuracion_ruta == ":memory:":
            conexion = sqlite3.connect(":memory:")
        else:
            ruta = Path(configuracion_ruta)
            if not ruta.is_absolute():
                ruta = Path(current_app.root_path).parent / ruta
            ruta.parent.mkdir(parents=True, exist_ok=True)
            conexion = sqlite3.connect(ruta)
        conexion.row_factory = sqlite3.Row
        conexion.execute("PRAGMA foreign_keys = ON")
        conexion.execute("PRAGMA busy_timeout = 5000")
        g.conexion_db = conexion
    return g.conexion_db


def cerrar_conexion(_error=None):
    conexion = g.pop("conexion_db", None)
    if conexion is not None:
        conexion.close()


def _ahora_utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def registrar_auditoria(conexion, usuario_id, accion, resultado, ip=None):
    conexion.execute(
        """INSERT INTO auditoria (usuario_id, accion, resultado, direccion_ip, fecha)
           VALUES (?, ?, ?, ?, ?)""",
        (usuario_id, accion, resultado, ip, _ahora_utc()),
    )


def _usuario_desde_fila(fila):
    if fila is None:
        return None
    return Usuario(
        id=fila["id"],
        username=fila["username"],
        nombre=fila["nombre_completo"],
        correo=fila["correo"],
        rol=fila["rol"],
        estado=fila["estado"],
    )


def obtener_usuario_por_id(user_id, solo_activo=False):
    consulta = """SELECT u.id, u.username, u.nombre_completo, u.correo,
                         r.nombre AS rol, u.estado
                  FROM usuarios u JOIN roles r ON r.id = u.rol_id
                  WHERE u.id = ?"""
    parametros = [user_id]
    if solo_activo:
        consulta += " AND u.estado = ?"
        parametros.append("ACTIVO")
    return _usuario_desde_fila(obtener_conexion().execute(consulta, parametros).fetchone())


def obtener_usuario_por_username(username):
    return obtener_conexion().execute(
        """SELECT u.id, u.username, u.nombre_completo, u.correo, u.password_hash,
                         r.nombre AS rol, u.estado
           FROM usuarios u JOIN roles r ON r.id = u.rol_id
           WHERE u.username = ? COLLATE NOCASE""",
        (username,),
    ).fetchone()


def validar_credenciales(username, password):
    fila = obtener_usuario_por_username(username)
    if fila is None or fila["estado"] != "ACTIVO":
        return None
    if not check_password_hash(fila["password_hash"], password):
        return None
    return _usuario_desde_fila(fila)


def inicializar_base_datos():
    conexion = obtener_conexion()
    esquema = Path(current_app.root_path) / "schema.sql"
    conexion.executescript(esquema.read_text(encoding="utf-8"))
    conexion.executemany(
        "INSERT OR IGNORE INTO roles (nombre) VALUES (?)",
        ((rol,) for rol in ROLES),
    )
    conexion.execute(
        """INSERT INTO app_meta (clave, valor) VALUES ('schema_version', '2')
           ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor"""
    )
    conexion.commit()


def seed_admin(username, password, nombre="Administrador DEMO"):
    if not username or not USERNAME_RE.fullmatch(username):
        raise ValueError("SICOSE_ADMIN_USERNAME debe tener de 3 a 80 caracteres válidos.")
    if not password or len(password) < 12 or len(password) > 256:
        raise ValueError("SICOSE_ADMIN_PASSWORD debe tener entre 12 y 256 caracteres.")

    conexion = obtener_conexion()
    existente = obtener_usuario_por_username(username)
    if existente is not None:
        if existente["rol"] != "ADMINISTRADOR":
            raise ValueError("Ese nombre de usuario ya pertenece a una cuenta no administradora.")
        return False

    rol = conexion.execute(
        "SELECT id FROM roles WHERE nombre = ?", ("ADMINISTRADOR",)
    ).fetchone()
    if rol is None:
        raise RuntimeError("Faltan roles. Ejecuta primero: flask --app sicose init-db")

    ahora = _ahora_utc()
    cursor = conexion.execute(
        """INSERT INTO usuarios
           (username, nombre_completo, password_hash, rol_id, estado, creado_en, actualizado_en)
           VALUES (?, ?, ?, ?, 'ACTIVO', ?, ?)""",
        (username, nombre, generate_password_hash(password), rol["id"], ahora, ahora),
    )
    registrar_auditoria(conexion, cursor.lastrowid, "ADMIN_SEED", "EXITOSO")
    conexion.commit()
    return True


@click.command("init-db")
def comando_init_db():
    """Crea/actualiza tablas y roles sin borrar los datos existentes."""
    inicializar_base_datos()
    click.echo("Base SQLite inicializada; roles disponibles: administrador, instructor, voluntario.")


@click.command("seed-admin")
def comando_seed_admin():
    """Crea una cuenta administradora DEMO desde variables locales de entorno."""
    import os

    try:
        creado = seed_admin(
            os.environ.get("SICOSE_ADMIN_USERNAME"),
            os.environ.get("SICOSE_ADMIN_PASSWORD"),
        )
    except (ValueError, RuntimeError) as error:
        raise click.ClickException(str(error)) from error
    click.echo("Administrador DEMO creado." if creado else "El administrador ya existe; no se modificó.")


def init_app(app):
    app.teardown_appcontext(cerrar_conexion)
    app.cli.add_command(comando_init_db)
    app.cli.add_command(comando_seed_admin)
