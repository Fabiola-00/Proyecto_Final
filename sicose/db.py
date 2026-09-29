"""Persistencia SQLite, seed idempotente y auditoría mínima."""

import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import click
from flask import current_app, g
from werkzeug.security import check_password_hash, generate_password_hash

from .models import Usuario

ROLES = ("ADMINISTRADOR", "JEFE_PERSONAL", "INSTRUCTOR_VOLUNTARIO")
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
        password_version=fila["password_version"],
        foto_perfil=fila["foto_perfil"],
    )


def obtener_usuario_por_id(user_id, solo_activo=False):
    consulta = """SELECT u.id, u.username, u.nombre_completo, u.correo,
                         r.nombre AS rol, u.estado, u.password_version, u.foto_perfil
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
                         r.nombre AS rol, u.estado, u.password_version, u.foto_perfil
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
    _migrar_nombres_rol(conexion)
    columnas = {fila["name"] for fila in conexion.execute("PRAGMA table_info(usuarios)")}
    if "password_version" not in columnas:
        conexion.execute("ALTER TABLE usuarios ADD COLUMN password_version INTEGER NOT NULL DEFAULT 1")
    if "foto_perfil" not in columnas:
        conexion.execute("ALTER TABLE usuarios ADD COLUMN foto_perfil TEXT")
    columnas_voluntarios = {fila["name"] for fila in conexion.execute("PRAGMA table_info(voluntarios)")}
    for campo in ("nombres", "apellido_paterno", "apellido_materno", "fecha_nacimiento", "codigo_instructor"):
        if campo not in columnas_voluntarios:
            conexion.execute(f"ALTER TABLE voluntarios ADD COLUMN {campo} TEXT")
    conexion.execute(
        """CREATE UNIQUE INDEX IF NOT EXISTS idx_voluntarios_codigo_instructor
           ON voluntarios(codigo_instructor) WHERE codigo_instructor IS NOT NULL"""
    )
    conexion.executemany(
        "INSERT OR IGNORE INTO roles (nombre) VALUES (?)",
        ((rol,) for rol in ROLES),
    )
    conexion.execute(
        """INSERT INTO app_meta (clave, valor) VALUES ('schema_version', '6')
           ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor"""
    )
    conexion.commit()


def _migrar_nombres_rol(conexion):
    """Renombra códigos de rol y su origen/categoría de nota preservando IDs y FKs."""
    roles = {fila["nombre"] for fila in conexion.execute("SELECT nombre FROM roles")}
    sql_roles = conexion.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='roles'"
    ).fetchone()["sql"] or ""
    sql_eval = conexion.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='evaluaciones'"
    ).fetchone()["sql"] or ""
    migrar_roles = bool(roles & {"INSTRUCTOR", "VOLUNTARIO"}) or "JEFE_PERSONAL" not in sql_roles
    migrar_evaluaciones = "INSTRUCTOR_VOLUNTARIO" not in sql_eval
    if not migrar_roles and not migrar_evaluaciones:
        return

    conexion.commit()
    conexion.execute("PRAGMA foreign_keys = OFF")
    try:
        conexion.execute("BEGIN")
        if migrar_roles:
            conexion.execute(
                """CREATE TABLE roles_nueva (
                       id INTEGER PRIMARY KEY,
                       nombre TEXT NOT NULL UNIQUE CHECK (nombre IN
                           ('ADMINISTRADOR', 'JEFE_PERSONAL', 'INSTRUCTOR_VOLUNTARIO'))
                   )"""
            )
            conexion.execute(
                """INSERT INTO roles_nueva (id, nombre)
                   SELECT id, CASE nombre WHEN 'INSTRUCTOR' THEN 'JEFE_PERSONAL'
                          WHEN 'VOLUNTARIO' THEN 'INSTRUCTOR_VOLUNTARIO' ELSE nombre END
                   FROM roles"""
            )
            conexion.execute("DROP TABLE roles")
            conexion.execute("ALTER TABLE roles_nueva RENAME TO roles")

        if migrar_evaluaciones:
            conexion.execute(
                """CREATE TABLE evaluaciones_nueva (
                    id INTEGER PRIMARY KEY,
                    codigo TEXT NOT NULL UNIQUE,
                    nombre TEXT NOT NULL,
                    categoria TEXT NOT NULL CHECK (categoria IN ('PSICOMETRICA', 'FISICA', 'ACADEMICA', 'JEFE_PERSONAL')),
                    origen_nota TEXT NOT NULL CHECK (origen_nota IN ('INSTRUCTOR_VOLUNTARIO', 'JEFE_PERSONAL')),
                    instrumento_id INTEGER REFERENCES instrumentos(id) ON DELETE RESTRICT,
                    activo INTEGER NOT NULL DEFAULT 0 CHECK (activo IN (0, 1)),
                    creado_en TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
                )"""
            )
            conexion.execute(
                """INSERT INTO evaluaciones_nueva
                   SELECT id, codigo, nombre,
                          CASE categoria WHEN 'INSTRUCTOR' THEN 'JEFE_PERSONAL' ELSE categoria END,
                          CASE origen_nota WHEN 'INSTRUCTOR' THEN 'JEFE_PERSONAL'
                               WHEN 'VOLUNTARIO' THEN 'INSTRUCTOR_VOLUNTARIO' ELSE origen_nota END,
                          instrumento_id, activo, creado_en
                   FROM evaluaciones"""
            )
            conexion.execute("DROP TABLE evaluaciones")
            conexion.execute("ALTER TABLE evaluaciones_nueva RENAME TO evaluaciones")
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.execute("PRAGMA foreign_keys = ON")
    violaciones = conexion.execute("PRAGMA foreign_key_check").fetchall()
    if violaciones:
        raise RuntimeError("La migración de roles detectó referencias inválidas; no uses la base hasta revisar el respaldo.")


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
    click.echo("Base SQLite inicializada; roles disponibles: Administrador, Jefe de Personal e Instructor Voluntario.")


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
