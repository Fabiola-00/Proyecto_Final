"""Persistencia SQLite, seed idempotente y auditoría mínima."""

import re
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

import click
from flask import current_app, g
from werkzeug.security import check_password_hash, generate_password_hash

from .models import Usuario

ROLES = ("ADMINISTRADOR", "JEFE_PERSONAL", "INSTRUCTOR_VOLUNTARIO", "COMANDANTE_GRUPO")
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


def periodo_actual():
    """Año calendario mostrado en la interfaz; no modifica períodos persistidos."""
    return str(date.today().year)


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
        consulta += " AND r.nombre != 'COMANDANTE_GRUPO' AND u.estado = ?"
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
    if fila is None or fila["estado"] != "ACTIVO" or fila["rol"] == "COMANDANTE_GRUPO":
        return None
    if not check_password_hash(fila["password_hash"], password):
        return None
    return _usuario_desde_fila(fila)


def inicializar_base_datos():
    conexion = obtener_conexion()
    esquema = Path(current_app.root_path) / "schema.sql"
    conexion.executescript(esquema.read_text(encoding="utf-8"))
    columnas_operaciones = {fila['name'] for fila in conexion.execute('PRAGMA table_info(operaciones)')}
    for campo, tipo in {
        'tipo_operativo': "TEXT CHECK(tipo_operativo IS NULL OR tipo_operativo IN ('Preventivo','Reactivo','Especial','Emergencia'))",
        'estado_operacion': "TEXT CHECK(estado_operacion IS NULL OR estado_operacion IN ('Planificación','En ejecución','Finalizado','Suspendido'))",
        'revision': 'INTEGER NOT NULL DEFAULT 1 CHECK(revision>0)',
    }.items():
        if campo not in columnas_operaciones:
            conexion.execute(f'ALTER TABLE operaciones ADD COLUMN {campo} {tipo}')
    for campo,tipo in {
        'departamento': "TEXT CHECK(departamento IS NULL OR departamento IN ('Beni','Chuquisaca','Cochabamba','La Paz','Oruro','Pando','Potosí','Santa Cruz','Tarija'))",
        'zona': 'TEXT CHECK(zona IS NULL OR length(trim(zona)) BETWEEN 1 AND 160)',
    }.items():
        if campo not in columnas_operaciones:
            conexion.execute(f'ALTER TABLE operaciones ADD COLUMN {campo} {tipo}')
    if 'revision' not in {f['name'] for f in conexion.execute('PRAGMA table_info(participaciones_operacion)')}:
        conexion.execute('ALTER TABLE participaciones_operacion ADD COLUMN revision INTEGER NOT NULL DEFAULT 1 CHECK(revision>0)')
    _migrar_nombres_rol(conexion)
    _asegurar_comandante_unico(conexion)
    _asegurar_jefe_unico(conexion)
    columnas = {fila["name"] for fila in conexion.execute("PRAGMA table_info(usuarios)")}
    if "password_version" not in columnas:
        conexion.execute("ALTER TABLE usuarios ADD COLUMN password_version INTEGER NOT NULL DEFAULT 1")
    if "foto_perfil" not in columnas:
        conexion.execute("ALTER TABLE usuarios ADD COLUMN foto_perfil TEXT")
    columnas_voluntarios = {fila["name"] for fila in conexion.execute("PRAGMA table_info(voluntarios)")}
    for campo in ("nombres", "apellido_paterno", "apellido_materno", "fecha_nacimiento", "codigo_instructor"):
        if campo not in columnas_voluntarios:
            conexion.execute(f"ALTER TABLE voluntarios ADD COLUMN {campo} TEXT")
    if "especialidad_principal" not in columnas_voluntarios:
        conexion.execute(
            "ALTER TABLE voluntarios ADD COLUMN especialidad_principal TEXT "
            "CHECK (especialidad_principal IS NULL OR especialidad_principal IN "
            "('Rescate en agua','Rescate en montaña','Rescate en selva',"
            "'Lucha contra incendios','Primeros Auxilios','K-9'))"
        )
    nuevas_columnas = {
        "fecha_incorporacion": "TEXT",
        "grado": "TEXT CHECK (grado IS NULL OR grado IN ('Instructor Inicial','Instructor Segundo','Instructor Primero','Instructor Principal','Instructor Mayor'))",
        "pais_residencia": "TEXT CHECK (pais_residencia IS NULL OR pais_residencia = 'Bolivia')",
        "departamento_residencia": "TEXT CHECK (departamento_residencia IS NULL OR departamento_residencia IN ('Beni','Chuquisaca','Cochabamba','La Paz','Oruro','Pando','Potosí','Santa Cruz','Tarija'))",
        "ano_incorporacion": "INTEGER CHECK (ano_incorporacion IS NULL OR (typeof(ano_incorporacion) = 'integer' AND ano_incorporacion BETWEEN 1 AND 9999))",
    }
    for campo, tipo in nuevas_columnas.items():
        if campo not in columnas_voluntarios:
            conexion.execute(f"ALTER TABLE voluntarios ADD COLUMN {campo} {tipo}")
    columnas_catalogo = {fila["name"] for fila in conexion.execute("PRAGMA table_info(cursos)")}
    campos_catalogo = {
        "tipo": "TEXT CHECK(tipo IS NULL OR tipo IN ('Capacitación','Especialización','Actualización','Taller','Seminario (Webinar)'))",
        "entidad": "TEXT", "fecha_inicio": "TEXT", "fecha_fin": "TEXT",
        "estado": "TEXT CHECK(estado IS NULL OR estado IN ('Próximo','En curso','Finalizado'))",
        "observaciones": "TEXT",
        "puntaje": "INTEGER CHECK(puntaje IS NULL OR (typeof(puntaje)='integer' AND puntaje BETWEEN 0 AND 100))",
    }
    for campo, definicion in campos_catalogo.items():
        if campo not in columnas_catalogo:
            conexion.execute(f"ALTER TABLE cursos ADD COLUMN {campo} {definicion}")
    columnas_cursos = {fila["name"] for fila in conexion.execute("PRAGMA table_info(capacitaciones)")}
    if "curso_id" not in columnas_cursos:
        conexion.execute("ALTER TABLE capacitaciones ADD COLUMN curso_id INTEGER REFERENCES cursos(id) ON DELETE RESTRICT")
    columnas_notas = {fila["name"] for fila in conexion.execute("PRAGMA table_info(notas_operativas)")}
    for campo, tabla in (("configuracion_id", "configuraciones_5b"), ("evaluacion_id", "evaluaciones")):
        if campo not in columnas_notas:
            conexion.execute(f"ALTER TABLE notas_operativas ADD COLUMN {campo} INTEGER REFERENCES {tabla}(id) ON DELETE RESTRICT")
    _asegurar_periodos_5b(conexion)
    columnas_asistencias = {fila["name"] for fila in conexion.execute("PRAGMA table_info(asistencias)")}
    if "estado_detalle" not in columnas_asistencias:
        conexion.execute(
            "ALTER TABLE asistencias ADD COLUMN estado_detalle TEXT "
            "CHECK (estado_detalle IS NULL OR estado_detalle IN ('ASISTE','ATRASO','PERMISO','FALTA'))"
        )
    conexion.execute(
        """UPDATE asistencias SET estado_detalle = CASE estado
               WHEN 'PRESENTE' THEN 'ASISTE'
               WHEN 'AUSENTE' THEN 'FALTA'
               WHEN 'JUSTIFICADO' THEN 'PERMISO'
           END WHERE estado_detalle IS NULL"""
    )
    conexion.executescript("""
        CREATE TRIGGER IF NOT EXISTS conservar_correccion_asistencia
        AFTER UPDATE OF estado,estado_detalle ON asistencias
        WHEN COALESCE(OLD.estado_detalle,OLD.estado) != COALESCE(NEW.estado_detalle,NEW.estado)
        BEGIN
          INSERT INTO historial_asistencias(asistencia_id,estado_anterior,estado_nuevo,corregido_por)
          VALUES (OLD.id,COALESCE(OLD.estado_detalle,OLD.estado),COALESCE(NEW.estado_detalle,NEW.estado),NEW.registrado_por);
        END;
    """)
    conexion.execute(
        """CREATE UNIQUE INDEX IF NOT EXISTS idx_voluntarios_codigo_instructor
           ON voluntarios(codigo_instructor) WHERE codigo_instructor IS NOT NULL"""
    )
    conexion.executemany(
        "INSERT OR IGNORE INTO roles (nombre) VALUES (?)",
        ((rol,) for rol in ROLES),
    )
    conexion.execute(
        """INSERT INTO app_meta (clave, valor) VALUES ('schema_version', '27')
           ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor"""
    )
    conexion.commit()


def _asegurar_periodos_5b(conexion):
    """Proteger cambios nuevos sin cerrar ni modificar períodos históricos."""
    conexion.executescript("""
    DROP TRIGGER IF EXISTS periodo_activo_insertar;
    DROP TRIGGER IF EXISTS periodo_activo_actualizar;
    CREATE TRIGGER IF NOT EXISTS periodo_activo_insertar BEFORE INSERT ON periodos
    WHEN NEW.estado='ACTIVO' AND EXISTS(SELECT 1 FROM periodos WHERE estado='ACTIVO' AND NOT EXISTS(SELECT 1 FROM bajas_gestion b WHERE b.periodo_id=periodos.id))
    BEGIN SELECT RAISE(ABORT,'periodo_activo_existente'); END;
    CREATE TRIGGER IF NOT EXISTS periodo_activo_actualizar BEFORE UPDATE OF estado ON periodos
    WHEN NEW.estado='ACTIVO' AND OLD.estado!='ACTIVO' AND EXISTS(SELECT 1 FROM periodos WHERE estado='ACTIVO' AND id!=NEW.id AND NOT EXISTS(SELECT 1 FROM bajas_gestion b WHERE b.periodo_id=periodos.id))
    BEGIN SELECT RAISE(ABORT,'periodo_activo_existente'); END;
    CREATE TRIGGER IF NOT EXISTS configuracion_publicada_actualizar BEFORE UPDATE ON configuraciones_5b
    WHEN OLD.estado='PUBLICADA' BEGIN SELECT RAISE(ABORT,'configuracion_congelada'); END;
    CREATE TRIGGER IF NOT EXISTS configuracion_publicada_borrar BEFORE DELETE ON configuraciones_5b
    WHEN OLD.estado='PUBLICADA' BEGIN SELECT RAISE(ABORT,'configuracion_congelada'); END;
    CREATE TRIGGER IF NOT EXISTS fuente_publicada_insertar BEFORE INSERT ON fuentes_configuracion_5b
    WHEN EXISTS(SELECT 1 FROM configuraciones_5b WHERE id=NEW.configuracion_id AND estado='PUBLICADA')
    BEGIN SELECT RAISE(ABORT,'configuracion_congelada'); END;
    CREATE TRIGGER IF NOT EXISTS fuente_publicada_actualizar BEFORE UPDATE ON fuentes_configuracion_5b
    WHEN EXISTS(SELECT 1 FROM configuraciones_5b WHERE id IN (OLD.configuracion_id,NEW.configuracion_id) AND estado='PUBLICADA')
    BEGIN SELECT RAISE(ABORT,'configuracion_congelada'); END;
    CREATE TRIGGER IF NOT EXISTS fuente_publicada_borrar BEFORE DELETE ON fuentes_configuracion_5b
    WHEN EXISTS(SELECT 1 FROM configuraciones_5b WHERE id=OLD.configuracion_id AND estado='PUBLICADA')
    BEGIN SELECT RAISE(ABORT,'configuracion_congelada'); END;
    CREATE TRIGGER IF NOT EXISTS periodo_publicado_fechas BEFORE UPDATE OF nombre,fecha_inicio,fecha_fin ON periodos
    WHEN (NEW.nombre!=OLD.nombre OR NEW.fecha_inicio!=OLD.fecha_inicio OR NEW.fecha_fin!=OLD.fecha_fin)
    AND EXISTS(SELECT 1 FROM configuraciones_5b WHERE periodo_id=OLD.id AND estado='PUBLICADA')
    BEGIN SELECT RAISE(ABORT,'periodo_congelado'); END;
    CREATE TRIGGER IF NOT EXISTS nota_operativa_configurada BEFORE INSERT ON notas_operativas
    WHEN NOT EXISTS(SELECT 1 FROM configuraciones_5b c JOIN fuentes_configuracion_5b f ON f.configuracion_id=c.id
                    JOIN periodos p ON p.id=c.periodo_id WHERE c.id=NEW.configuracion_id AND c.periodo_id=NEW.periodo_id
                    AND c.estado='PUBLICADA' AND p.estado='ACTIVO' AND f.fuente=NEW.fuente AND f.evaluacion_id=NEW.evaluacion_id)
    BEGIN SELECT RAISE(ABORT,'nota_sin_configuracion_publicada'); END;
    """)


def _asegurar_jefe_unico(conexion):
    """Bloquear nuevos titulares simultáneos sin borrar los históricos."""
    conexion.executescript("""
    CREATE TRIGGER IF NOT EXISTS jefe_unico_insertar BEFORE INSERT ON usuarios
    WHEN NEW.estado='ACTIVO' AND NEW.rol_id IN (SELECT id FROM roles WHERE nombre='JEFE_PERSONAL')
    AND EXISTS(SELECT 1 FROM usuarios u JOIN roles r ON r.id=u.rol_id WHERE r.nombre='JEFE_PERSONAL' AND u.estado='ACTIVO')
    BEGIN SELECT RAISE(ABORT,'jefe_activo_existente'); END;
    CREATE TRIGGER IF NOT EXISTS jefe_unico_actualizar BEFORE UPDATE OF estado,rol_id ON usuarios
    WHEN NEW.estado='ACTIVO' AND NEW.rol_id IN (SELECT id FROM roles WHERE nombre='JEFE_PERSONAL')
    AND EXISTS(SELECT 1 FROM usuarios u JOIN roles r ON r.id=u.rol_id WHERE r.nombre='JEFE_PERSONAL' AND u.estado='ACTIVO' AND u.id!=NEW.id)
    BEGIN SELECT RAISE(ABORT,'jefe_activo_existente'); END;
    """)


def _asegurar_comandante_unico(conexion):
    """Crear restricciones después de ampliar el catálogo de roles."""
    conexion.executescript("""
CREATE TRIGGER IF NOT EXISTS unico_comandante_insertar BEFORE INSERT ON usuarios
WHEN NEW.estado='ACTIVO' AND NEW.rol_id IN (SELECT id FROM roles WHERE nombre='COMANDANTE_GRUPO')
AND EXISTS(SELECT 1 FROM usuarios u JOIN roles r ON r.id=u.rol_id WHERE r.nombre='COMANDANTE_GRUPO' AND u.estado='ACTIVO')
BEGIN SELECT RAISE(ABORT,'comandante_activo_existente'); END;
CREATE TRIGGER IF NOT EXISTS unico_comandante_actualizar BEFORE UPDATE OF estado,rol_id ON usuarios
WHEN NEW.estado='ACTIVO' AND NEW.rol_id IN (SELECT id FROM roles WHERE nombre='COMANDANTE_GRUPO')
AND EXISTS(SELECT 1 FROM usuarios u JOIN roles r ON r.id=u.rol_id WHERE r.nombre='COMANDANTE_GRUPO' AND u.estado='ACTIVO' AND u.id!=NEW.id)
BEGIN SELECT RAISE(ABORT,'comandante_activo_existente'); END;
    """)


def _migrar_nombres_rol(conexion):
    """Renombra códigos de rol y su origen/categoría de nota preservando IDs y FKs."""
    roles = {fila["nombre"] for fila in conexion.execute("SELECT nombre FROM roles")}
    sql_roles = conexion.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='roles'"
    ).fetchone()["sql"] or ""
    sql_eval = conexion.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='evaluaciones'"
    ).fetchone()["sql"] or ""
    migrar_roles = bool(roles & {"INSTRUCTOR", "VOLUNTARIO"}) or "COMANDANTE_GRUPO" not in sql_roles
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
                           ('ADMINISTRADOR', 'JEFE_PERSONAL', 'INSTRUCTOR_VOLUNTARIO', 'COMANDANTE_GRUPO'))
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
