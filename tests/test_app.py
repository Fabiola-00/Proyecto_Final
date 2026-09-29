"""Pruebas de autenticación, autorización y persistencia SICOSE."""

import re
import sqlite3
import struct
import unittest
import uuid
import zlib
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

from sicose import create_app
from sicose.db import inicializar_base_datos, seed_admin


class AplicacionTestCase(unittest.TestCase):
    def setUp(self):
        Path(".tmp").mkdir(exist_ok=True)
        self.db_path = Path(".tmp") / f"test-{uuid.uuid4().hex}.sqlite3"
        self.media_path = Path(".tmp") / f"media-{uuid.uuid4().hex}"
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "clave-de-prueba-no-usar-fuera-de-tests",
                "DATABASE": str(self.db_path.resolve()),
                "PERFIL_MEDIA_FOLDER": str(self.media_path.resolve()),
            }
        )
        self.cliente = self.app.test_client()
        with self.app.app_context():
            inicializar_base_datos()
            self._crear_usuario("admin.demo", "ADMINISTRADOR", "Clave demo segura 123!")
            self._crear_usuario("instructor.demo", "JEFE_PERSONAL", "Clave instructor 123!")
            self._crear_usuario("voluntario.demo", "INSTRUCTOR_VOLUNTARIO", "Clave voluntario 123!")

    def tearDown(self):
        self.cliente = None
        if self.db_path.exists():
            self.db_path.unlink()
        if self.media_path.exists():
            for archivo in self.media_path.iterdir():
                archivo.unlink()
            self.media_path.rmdir()

    def _crear_usuario(self, username, rol, password):
        from sicose.db import obtener_conexion

        conexion = obtener_conexion()
        rol_id = conexion.execute("SELECT id FROM roles WHERE nombre = ?", (rol,)).fetchone()[0]
        conexion.execute(
            """INSERT INTO usuarios (username, nombre_completo, password_hash, rol_id)
               VALUES (?, ?, ?, ?)""",
            (username, username, generate_password_hash(password), rol_id),
        )
        conexion.commit()

    def _login(self, username="admin.demo", password="Clave demo segura 123!"):
        token = self._csrf_token()
        return self.cliente.post(
            "/api/auth/login",
            json={"username": username, "password": password},
            headers={"X-CSRFToken": token},
        )

    def _csrf_token(self):
        pagina = self.cliente.get("/", follow_redirects=True)
        coincidencia = re.search(rb'name="csrf_token" value="([^"]+)"', pagina.data)
        self.assertIsNotNone(coincidencia, "El formulario debe emitir token CSRF")
        return coincidencia.group(1).decode("ascii")

    def test_login_correcto(self):
        respuesta = self._login()
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json["usuario"]["rol"], "ADMINISTRADOR")
        cookie = respuesta.headers.get("Set-Cookie", "")
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Lax", cookie)

    def test_login_con_contrasena_incorrecta(self):
        respuesta = self._login(password="incorrecta")
        self.assertEqual(respuesta.status_code, 401)
        self.assertEqual(respuesta.json["error"], "Usuario o contraseña incorrectos.")

    def test_login_con_usuario_inexistente(self):
        respuesta = self._login(username="nadie.demo")
        self.assertEqual(respuesta.status_code, 401)
        self.assertEqual(respuesta.json["error"], "Usuario o contraseña incorrectos.")

    def test_usuario_inactivo_no_inicia_sesion(self):
        with self.app.app_context():
            from sicose.db import obtener_conexion

            self._crear_usuario("pendiente.demo", "INSTRUCTOR_VOLUNTARIO", "Clave pendiente 123!")
            obtener_conexion().execute(
                "UPDATE usuarios SET estado = 'PENDIENTE' WHERE username = ?",
                ("pendiente.demo",),
            )
            obtener_conexion().commit()
        respuesta = self._login("pendiente.demo", "Clave pendiente 123!")
        self.assertEqual(respuesta.status_code, 401)

    def test_api_protegida_rechaza_sin_sesion(self):
        respuesta = self.cliente.get("/api/admin/estado")
        self.assertEqual(respuesta.status_code, 401)

    def test_ruta_api_inexistente_devuelve_json_y_no_html(self):
        respuesta = self.cliente.get("/api/ruta-que-no-existe")
        self.assertEqual(respuesta.status_code, 404)
        self.assertEqual(respuesta.mimetype, "application/json")
        self.assertEqual(respuesta.json["codigo"], "no_encontrado")

    def test_admin_puede_acceder_a_ruta_restringida(self):
        self.assertEqual(self._login().status_code, 200)
        respuesta = self.cliente.get("/api/admin/estado")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json, {"estado": "autorizado"})

    def test_instructor_no_accede_a_ruta_admin(self):
        self.assertEqual(self._login("instructor.demo", "Clave instructor 123!").status_code, 200)
        self.assertEqual(self.cliente.get("/api/admin/estado").status_code, 403)

    def test_voluntario_no_accede_a_ruta_admin(self):
        self.assertEqual(self._login("voluntario.demo", "Clave voluntario 123!").status_code, 200)
        self.assertEqual(self.cliente.get("/api/admin/estado").status_code, 403)

    def test_inicio_admin_muestra_dashboard_y_metricas(self):
        self.assertEqual(self._login().status_code, 200)
        respuesta = self.cliente.get("/", follow_redirects=True)
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(b"Panel de administraci\xc3\xb3n", respuesta.data)
        self.assertIn(b"Voluntarios activos", respuesta.data)
        self.assertIn(b'id="boton-tema"', respuesta.data)
        self.assertIn(b'id="boton-sidebar"', respuesta.data)
        self.assertIn(b"images/sbrab-logo.png", respuesta.data)
        self.assertIn(b"Agregar Jefe de Personal", respuesta.data)
        self.assertIn(b"Ver todos los Jefes de Personal", respuesta.data)
        self.assertIn(b"Capacitaciones o cursos", respuesta.data)
        self.assertIn(b"SICOSE", respuesta.data)

    def test_logo_institucional_esta_disponible_como_imagen(self):
        respuesta = self.cliente.get("/static/images/sbrab-logo.png")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.mimetype, "image/png")
        respuesta.close()

    def test_login_muestra_emblema_y_estilos_institucionales(self):
        respuesta = self.cliente.get("/login")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(b"images/sbrab-logo.png", respuesta.data)
        self.assertIn(b"Emblema institucional SBRAB", respuesta.data)
        css = self.cliente.get("/static/css/estilos.css")
        self.assertEqual(css.status_code, 200)
        self.assertIn(b"#1D1BBE", css.data)
        self.assertIn(b"#F57B1A", css.data)
        css.close()

    def test_inicio_instructor_muestra_solo_su_panel(self):
        self.assertEqual(self._login("instructor.demo", "Clave instructor 123!").status_code, 200)
        respuesta = self.cliente.get("/", follow_redirects=True)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(self.cliente.get("/panel/jefe-personal").status_code, 200)
        self.assertIn(b"Panel del Jefe de Personal", respuesta.data)
        self.assertIn(b"Seguimiento asignado", respuesta.data)
        self.assertNotIn(b"Panel de administraci\xc3\xb3n", respuesta.data)

    def test_inicio_voluntario_muestra_solo_su_panel(self):
        self.assertEqual(self._login("voluntario.demo", "Clave voluntario 123!").status_code, 200)
        respuesta = self.cliente.get("/", follow_redirects=True)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(self.cliente.get("/panel/instructor-voluntario").status_code, 200)
        self.assertIn(b"Mi seguimiento", respuesta.data)
        self.assertIn(b"Privacidad personal", respuesta.data)
        self.assertNotIn(b"Panel del Jefe de Personal", respuesta.data)

    def test_ruta_panel_de_otro_rol_retorna_403(self):
        self.assertEqual(self._login("voluntario.demo", "Clave voluntario 123!").status_code, 200)
        respuesta = self.cliente.get("/panel/administrador")
        self.assertEqual(respuesta.status_code, 403)
        self.assertIn(b"Acceso no disponible", respuesta.data)

    def test_logout_y_rechazo_posterior(self):
        self.assertEqual(self._login().status_code, 200)
        respuesta = self.cliente.post(
            "/api/auth/logout", headers={"X-CSRFToken": self._csrf_token()}
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(self.cliente.get("/api/auth/me").status_code, 401)

    def test_me_solo_devuelve_campos_publicos(self):
        self.assertEqual(self._login().status_code, 200)
        usuario = self.cliente.get("/api/auth/me").json["usuario"]
        self.assertEqual(set(usuario), {"id", "username", "nombre", "rol", "estado"})
        self.assertNotIn("password", usuario)
        self.assertNotIn("password_hash", usuario)

    def test_password_se_guarda_solo_como_hash(self):
        with self.app.app_context():
            from sicose.db import obtener_conexion

            fila = obtener_conexion().execute(
                "SELECT password_hash FROM usuarios WHERE username = ?", ("admin.demo",)
            ).fetchone()
            self.assertNotEqual(fila["password_hash"], "Clave demo segura 123!")
            self.assertTrue(check_password_hash(fila["password_hash"], "Clave demo segura 123!"))

    def test_seed_admin_es_idempotente_y_no_cambia_clave(self):
        with self.app.app_context():
            from sicose.db import obtener_conexion

            self.assertTrue(seed_admin("otro.admin.demo", "Primera clave segura 123!"))
            antes = obtener_conexion().execute(
                "SELECT password_hash FROM usuarios WHERE username = ?", ("otro.admin.demo",)
            ).fetchone()[0]
            self.assertFalse(seed_admin("otro.admin.demo", "Otra clave segura 456!"))
            despues = obtener_conexion().execute(
                "SELECT password_hash FROM usuarios WHERE username = ?", ("otro.admin.demo",)
            ).fetchone()[0]
            self.assertEqual(antes, despues)
            cantidad_eventos = obtener_conexion().execute(
                "SELECT COUNT(*) FROM auditoria WHERE accion = 'ADMIN_SEED'"
            ).fetchone()[0]
            self.assertEqual(cantidad_eventos, 1)

    def test_esquema_incluye_entidades_base_y_versiona_sin_borrar(self):
        with self.app.app_context():
            from sicose.db import obtener_conexion

            conexion = obtener_conexion()
            tablas = {
                fila[0]
                for fila in conexion.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
            self.assertTrue(
                {
                    "roles", "usuarios", "voluntarios", "instructores", "periodos",
                    "evaluaciones", "intentos", "respuestas", "calificaciones",
                    "capacitaciones", "asistencias", "auditoria",
                }.issubset(tablas)
            )
            columnas_voluntarios = {fila["name"] for fila in conexion.execute("PRAGMA table_info(voluntarios)")}
            self.assertTrue({"nombres", "apellido_paterno", "apellido_materno", "fecha_nacimiento", "codigo_instructor"}.issubset(columnas_voluntarios))
            version = conexion.execute(
                "SELECT valor FROM app_meta WHERE clave = ?", ("schema_version",)
            ).fetchone()[0]
            self.assertEqual(version, "7")
            columnas_asistencias = {fila["name"] for fila in conexion.execute("PRAGMA table_info(asistencias)")}
            self.assertIn("estado_detalle", columnas_asistencias)
            self.assertEqual(
                conexion.execute("SELECT COUNT(*) FROM roles").fetchone()[0], 3
            )
            self.assertEqual(conexion.execute("PRAGMA foreign_keys").fetchone()[0], 1)
            with self.assertRaises(sqlite3.IntegrityError):
                conexion.execute(
                    """INSERT INTO usuarios (username, nombre_completo, password_hash, rol_id)
                       VALUES (?, ?, ?, ?)""",
                    ("sin.rol", "Sin rol", "hash-no-usado", 9999),
                )

    def test_migracion_renombra_roles_sin_perder_perfiles_ni_evaluaciones(self):
        legacy_path = Path(".tmp") / f"legacy-{uuid.uuid4().hex}.sqlite3"
        old_schema = (Path("sicose") / "schema.sql").read_text(encoding="utf-8")
        old_schema = old_schema.replace(
            "('ADMINISTRADOR', 'JEFE_PERSONAL', 'INSTRUCTOR_VOLUNTARIO')",
            "('ADMINISTRADOR', 'INSTRUCTOR', 'VOLUNTARIO')",
        ).replace(
            "('PSICOMETRICA', 'FISICA', 'ACADEMICA', 'JEFE_PERSONAL')",
            "('PSICOMETRICA', 'FISICA', 'ACADEMICA', 'INSTRUCTOR')",
        ).replace(
            "('INSTRUCTOR_VOLUNTARIO', 'JEFE_PERSONAL')",
            "('VOLUNTARIO', 'INSTRUCTOR')",
        ).replace(
            "    nombres TEXT,\n    apellido_paterno TEXT,\n    apellido_materno TEXT,\n    fecha_nacimiento TEXT,\n    codigo_instructor TEXT UNIQUE,\n", ""
        ).replace(
            "    estado_detalle TEXT CHECK (estado_detalle IS NULL OR estado_detalle IN ('ASISTE', 'ATRASO', 'PERMISO', 'FALTA')),\n", ""
        )
        legacy = sqlite3.connect(legacy_path)
        legacy.execute("PRAGMA foreign_keys=ON")
        legacy.executescript(old_schema)
        legacy.execute("INSERT INTO app_meta (clave, valor) VALUES ('schema_version', '5')")
        legacy.executemany("INSERT INTO roles(nombre) VALUES (?)", [("ADMINISTRADOR",), ("INSTRUCTOR",), ("VOLUNTARIO",)])
        roles = {name: role_id for role_id, name in legacy.execute("SELECT id,nombre FROM roles")}
        legacy.execute("INSERT INTO usuarios(username,nombre_completo,password_hash,rol_id) VALUES ('jefe.demo','Jefe demo','hash',?)", (roles["INSTRUCTOR"],))
        jefe_id = legacy.execute("SELECT id FROM usuarios WHERE username='jefe.demo'").fetchone()[0]
        legacy.execute("INSERT INTO instructores(usuario_id) VALUES (?)", (jefe_id,))
        legacy.execute("INSERT INTO usuarios(username,nombre_completo,password_hash,rol_id) VALUES ('iv.demo','IV demo','hash',?)", (roles["VOLUNTARIO"],))
        iv_id = legacy.execute("SELECT id FROM usuarios WHERE username='iv.demo'").fetchone()[0]
        legacy.execute("INSERT INTO voluntarios(usuario_id,instructor_id) VALUES (?,?)", (iv_id, jefe_id))
        legacy.execute("INSERT INTO asistencias(voluntario_id,fecha,estado,actividad,registrado_por) VALUES (?, '2026-09-01', 'PRESENTE', 'Histórica', ?)", (iv_id, jefe_id))
        period_id = legacy.execute("INSERT INTO periodos(nombre,fecha_inicio,fecha_fin) VALUES ('Migración','2026-01-01','2026-12-31')").lastrowid
        eval_id = legacy.execute("INSERT INTO evaluaciones(codigo,nombre,categoria,origen_nota) VALUES ('JEF-OLD','Registro previo','INSTRUCTOR','INSTRUCTOR')").lastrowid
        legacy.execute("INSERT INTO asignaciones_evaluacion(voluntario_id,periodo_id,evaluacion_id) VALUES (?,?,?)", (iv_id, period_id, eval_id))
        legacy.commit()
        legacy.close()

        legacy_app = create_app({
            "TESTING": True,
            "SECRET_KEY": "clave-de-prueba-migracion",
            "DATABASE": str(legacy_path.resolve()),
            "PERFIL_MEDIA_FOLDER": str(self.media_path.resolve()),
        })
        try:
            with legacy_app.app_context():
                inicializar_base_datos()
                from sicose.db import obtener_conexion
                conexion = obtener_conexion()
                migrated_roles = {fila["nombre"]: fila["id"] for fila in conexion.execute("SELECT id,nombre FROM roles")}
                self.assertEqual(migrated_roles["JEFE_PERSONAL"], roles["INSTRUCTOR"])
                self.assertEqual(migrated_roles["INSTRUCTOR_VOLUNTARIO"], roles["VOLUNTARIO"])
                self.assertEqual(conexion.execute("SELECT instructor_id FROM voluntarios WHERE usuario_id=?", (iv_id,)).fetchone()[0], jefe_id)
                self.assertEqual(tuple(conexion.execute("SELECT categoria,origen_nota FROM evaluaciones WHERE id=?", (eval_id,)).fetchone()), ("JEFE_PERSONAL", "JEFE_PERSONAL"))
                self.assertEqual(conexion.execute("SELECT COUNT(*) FROM asignaciones_evaluacion WHERE voluntario_id=? AND evaluacion_id=?", (iv_id, eval_id)).fetchone()[0], 1)
                self.assertIsNone(conexion.execute("SELECT fecha_nacimiento FROM voluntarios WHERE usuario_id=?", (iv_id,)).fetchone()[0])
                asistencia_migrada = conexion.execute("SELECT estado,estado_detalle FROM asistencias WHERE voluntario_id=?", (iv_id,)).fetchone()
                self.assertEqual(tuple(asistencia_migrada), ("PRESENTE", "ASISTE"))
                self.assertEqual(conexion.execute("SELECT valor FROM app_meta WHERE clave='schema_version'").fetchone()[0], "7")
                self.assertEqual(conexion.execute("PRAGMA foreign_key_check").fetchall(), [])
        finally:
            if legacy_path.exists():
                legacy_path.unlink()

    def test_solicitud_publica_crea_usuario_pendiente_sin_sesion(self):
        respuesta = self.cliente.post("/api/registro/solicitudes", json={
            "username": "nueva.demo", "nombres": "Nueva", "apellido_paterno": "Voluntaria", "apellido_materno": "Demo",
            "fecha_nacimiento": "1978-04-02",
            "correo": "nueva@example.org", "password": "Contraseña segura 123!",
        }, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.json["codigo_instructor"], "NVD-020478")
        self.assertEqual(self.cliente.get("/api/auth/me").status_code, 401)
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            usuario = conexion.execute("SELECT estado, password_hash FROM usuarios WHERE username='nueva.demo'").fetchone()
            self.assertEqual(usuario["estado"], "PENDIENTE")
            self.assertNotEqual(usuario["password_hash"], "Contraseña segura 123!")
            self.assertEqual(conexion.execute("SELECT COUNT(*) FROM solicitudes_registro").fetchone()[0], 1)
            perfil = conexion.execute("SELECT fecha_nacimiento, codigo_instructor FROM voluntarios JOIN usuarios ON usuarios.id=voluntarios.usuario_id WHERE username='nueva.demo'").fetchone()
            self.assertEqual(tuple(perfil), ("1978-04-02", "NVD-020478"))

    def _png_prueba(self):
        def chunk(tipo, contenido):
            crc = zlib.crc32(tipo + contenido) & 0xffffffff
            return struct.pack(">I", len(contenido)) + tipo + contenido + struct.pack(">I", crc)
        return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00")) + chunk(b"IEND", b""))

    def test_registro_guarda_foto_en_instancia_y_la_sirve_solo_con_autorizacion(self):
        import io
        self.assertEqual(self.cliente.post("/api/registro/solicitudes", data={
            "username": "foto.demo", "nombres": "Voluntaria", "apellido_paterno": "Foto", "apellido_materno": "Demo",
            "fecha_nacimiento": "1980-02-03", "password": "Contraseña segura 123!",
            "foto": (io.BytesIO(self._png_prueba()), "perfil.png"),
        }, headers={"X-CSRFToken": self._csrf_token()}, content_type="multipart/form-data").status_code, 201)
        archivos_confirmados = set(self.media_path.iterdir())
        colision = self.cliente.post("/api/registro/solicitudes", data={
            "username": "foto.colision", "nombres": "Voluntaria", "apellido_paterno": "Foto", "apellido_materno": "Demo",
            "fecha_nacimiento": "1980-02-03", "password": "Contraseña segura 123!",
            "foto": (io.BytesIO(self._png_prueba()), "colision.png"),
        }, headers={"X-CSRFToken": self._csrf_token()}, content_type="multipart/form-data")
        self.assertEqual(colision.status_code, 409)
        self.assertEqual(set(self.media_path.iterdir()), archivos_confirmados)
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            usuario_id, nombre_archivo = conexion.execute("SELECT id, foto_perfil FROM usuarios WHERE username='foto.demo'").fetchone()
            archivo = Path(self.app.config["PERFIL_MEDIA_FOLDER"]) / nombre_archivo
            self.assertTrue(archivo.is_file())
        # El administrador puede revisar la imagen de un perfil pendiente.
        self.assertEqual(self._login().status_code, 200)
        imagen = self.cliente.get(f"/api/usuarios/{usuario_id}/foto")
        self.assertEqual(imagen.status_code, 200)
        self.assertEqual(imagen.mimetype, "image/png")
        self.assertEqual(imagen.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(imagen.headers["Cache-Control"], "private, no-store")
        imagen.close()

    def test_admin_restablece_clave_e_invalida_sesion_anterior(self):
        admin = self.app.test_client()
        volunteer = self.app.test_client()
        def login(client, username, password):
            pagina = client.get("/registro")
            csrf = re.search(rb'name="csrf_token" value="([^"]+)"', pagina.data).group(1).decode()
            return client.post("/api/auth/login", json={"username": username, "password": password}, headers={"X-CSRFToken": csrf})
        self.assertEqual(login(volunteer, "voluntario.demo", "Clave voluntario 123!").status_code, 200)
        self.assertEqual(login(admin, "admin.demo", "Clave demo segura 123!").status_code, 200)
        with self.app.app_context():
            from sicose.db import obtener_conexion
            user_id = obtener_conexion().execute("SELECT id FROM usuarios WHERE username='voluntario.demo'").fetchone()[0]
        csrf = re.search(rb'name="csrf_token" value="([^"]+)"', admin.get("/gestion/instructores-voluntarios").data).group(1).decode()
        response = admin.post(f"/api/admin/usuarios/{user_id}/restablecer-clave", json={"password": "Nueva clave segura 456!"}, headers={"X-CSRFToken": csrf})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(volunteer.get("/api/auth/me").status_code, 401)
        self.assertEqual(login(volunteer, "voluntario.demo", "Nueva clave segura 456!").status_code, 200)

    def test_paginas_registro_y_gestion_cargan(self):
        registro = self.cliente.get("/registro")
        self.assertEqual(registro.status_code, 200)
        self.assertIn(b"Solicitud de registro", registro.data)
        self.assertEqual(self._login().status_code, 200)
        gestion = self.cliente.get("/gestion/instructores-voluntarios")
        self.assertEqual(gestion.status_code, 200)
        self.assertIn(b"Solicitudes pendientes", gestion.data)
        self.assertIn(b"Agregar Instructor Voluntario", gestion.data)
        self.assertIn(b"Todos los Instructores Voluntarios", gestion.data)
        self.assertNotIn(b'id="invitacion-form"', gestion.data)
        self.assertIn(b'<details id="agregar-instructor-voluntario"', gestion.data)
        self.assertIn(b'<tbody id="voluntarios-lista"', gestion.data)
        self.assertIn(b"Acciones CRUD", gestion.data)
        instructores = self.cliente.get("/gestion/jefes-personal")
        self.assertEqual(instructores.status_code, 200)
        self.assertIn(b"Agregar Jefe de Personal", instructores.data)
        self.assertIn(b'<details id="agregar-jefe-personal"', instructores.data)
        self.assertIn(b'<tbody id="instructores-lista"', instructores.data)
        self.assertIn(b"Acciones CRUD", instructores.data)
        self.assertEqual(self.cliente.get("/api/admin/jefes-personal").mimetype, "application/json")

    def test_admin_crea_instructor_y_cuenta_accede_a_panel_diferenciado(self):
        self.assertEqual(self._login().status_code, 200)
        creada = self.cliente.post("/api/admin/jefes-personal", json={
            "username": "instructor.nuevo", "nombre": "Instructor Nuevo",
            "correo": "nuevo@example.org", "especialidad": "Rescate",
            "password": "Contraseña inicial 123!",
        }, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(creada.status_code, 201)
        instructor_id = creada.json["id"]
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            self.assertEqual(conexion.execute("SELECT estado FROM usuarios WHERE id=?", (instructor_id,)).fetchone()[0], "ACTIVO")
            self.assertEqual(conexion.execute("SELECT especialidad FROM instructores WHERE usuario_id=?", (instructor_id,)).fetchone()[0], "Rescate")
            password_hash = conexion.execute("SELECT password_hash FROM usuarios WHERE id=?", (instructor_id,)).fetchone()[0]
            self.assertNotEqual(password_hash, "Contraseña inicial 123!")
        self.cliente.post("/api/auth/logout", headers={"X-CSRFToken": self._csrf_token()})
        ingreso = self._login("instructor.nuevo", "Contraseña inicial 123!")
        self.assertEqual(ingreso.status_code, 200)
        inicio = self.cliente.get("/", follow_redirects=True)
        self.assertIn(b"Panel del Jefe de Personal", inicio.data)
        self.assertNotIn(b"Panel de administraci", inicio.data)
        rechazo = self.cliente.post("/api/admin/jefes-personal", json={}, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(rechazo.status_code, 403)

    def test_admin_crea_instructor_voluntario_manualmente_con_foto(self):
        import io

        self.assertEqual(self._login().status_code, 200)
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            jefe_id = conexion.execute("SELECT id FROM usuarios WHERE username='instructor.demo'").fetchone()[0]
            conexion.execute("INSERT INTO instructores (usuario_id, especialidad) VALUES (?, 'Rescate')", (jefe_id,))
            conexion.commit()

        creada = self.cliente.post("/api/admin/instructores-voluntarios", data={
            "username": "iv.manual",
            "nombres": "Instructor Voluntario", "apellido_paterno": "Manual", "apellido_materno": "Demo",
            "fecha_nacimiento": "1980-02-03",
            "correo": "iv.manual@example.org",
            "password": "Clave inicial manual 123!",
            "experiencia_operaciones": "Rescate urbano",
            "antiguedad_desde": "2024-01-15",
            "instructor_id": str(jefe_id),
            "foto": (io.BytesIO(self._png_prueba()), "perfil.png"),
        }, headers={"X-CSRFToken": self._csrf_token()}, content_type="multipart/form-data")
        self.assertEqual(creada.status_code, 201)
        user_id = creada.json["id"]
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            cuenta = conexion.execute(
                "SELECT u.estado, r.nombre AS rol, u.password_hash FROM usuarios u JOIN roles r ON r.id=u.rol_id WHERE u.id=?",
                (user_id,),
            ).fetchone()
            perfil = conexion.execute(
                "SELECT instructor_id, experiencia_operaciones, antiguedad_desde, fecha_nacimiento, codigo_instructor FROM voluntarios WHERE usuario_id=?",
                (user_id,),
            ).fetchone()
            solicitudes = conexion.execute(
                "SELECT COUNT(*) FROM solicitudes_registro WHERE usuario_id=?", (user_id,)
            ).fetchone()[0]
        self.assertEqual(cuenta["estado"], "ACTIVO")
        self.assertEqual(cuenta["rol"], "INSTRUCTOR_VOLUNTARIO")
        self.assertNotEqual(cuenta["password_hash"], "Clave inicial manual 123!")
        self.assertEqual(perfil["instructor_id"], jefe_id)
        self.assertEqual(perfil["experiencia_operaciones"], "Rescate urbano")
        self.assertEqual(perfil["antiguedad_desde"], "2024-01-15")
        self.assertEqual(perfil["fecha_nacimiento"], "1980-02-03")
        self.assertEqual(perfil["codigo_instructor"], "IMD-030280")
        self.assertEqual(solicitudes, 0)
        self.assertTrue(any(item["id"] == user_id for item in self.cliente.get("/api/instructores-voluntarios").json["voluntarios"]))
        foto = self.cliente.get(f"/api/usuarios/{user_id}/foto")
        self.assertEqual(foto.status_code, 200)
        self.assertEqual(foto.mimetype, "image/png")
        foto.close()
        self.cliente.post("/api/auth/logout", headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(self._login("instructor.demo", "Clave instructor 123!").status_code, 200)
        denegada = self.cliente.post("/api/admin/instructores-voluntarios", json={}, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(denegada.status_code, 403)

    def test_admin_registra_instructor_con_foto(self):
        import io
        self.assertEqual(self._login().status_code, 200)
        creada = self.cliente.post("/api/admin/jefes-personal", data={
            "username": "instructor.foto", "nombre": "Instructor con foto",
            "password": "Contraseña inicial 123!",
            "foto": (io.BytesIO(self._png_prueba()), "instructor.png"),
        }, headers={"X-CSRFToken": self._csrf_token()}, content_type="multipart/form-data")
        self.assertEqual(creada.status_code, 201)
        imagen = self.cliente.get(f"/api/usuarios/{creada.json['id']}/foto")
        self.assertEqual(imagen.status_code, 200)
        self.assertEqual(imagen.mimetype, "image/png")
        imagen.close()

    def test_admin_edita_y_desactiva_instructor_conservando_perfiles(self):
        self.assertEqual(self._login().status_code, 200)
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            instructor_id = conexion.execute("SELECT id FROM usuarios WHERE username='instructor.demo'").fetchone()[0]
            voluntario_id = conexion.execute("SELECT id FROM usuarios WHERE username='voluntario.demo'").fetchone()[0]
            conexion.execute("INSERT INTO instructores (usuario_id, especialidad) VALUES (?, 'Inicial')", (instructor_id,))
            conexion.execute("INSERT INTO voluntarios (usuario_id, instructor_id) VALUES (?, ?)", (voluntario_id, instructor_id))
            conexion.commit()
        editada = self.cliente.patch(f"/api/admin/jefes-personal/{instructor_id}", json={
            "nombre": "Instructor Editado", "especialidad": "Montaña",
        }, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(editada.status_code, 200)
        baja = self.cliente.post(f"/api/admin/jefes-personal/{instructor_id}/desactivar", headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(baja.status_code, 200)
        self.assertEqual(baja.json["voluntarios_desvinculados"], 1)
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            self.assertEqual(conexion.execute("SELECT estado FROM usuarios WHERE id=?", (instructor_id,)).fetchone()[0], "INACTIVO")
            self.assertIsNone(conexion.execute("SELECT instructor_id FROM voluntarios WHERE usuario_id=?", (voluntario_id,)).fetchone()[0])
            self.assertEqual(conexion.execute("SELECT COUNT(*) FROM instructores WHERE usuario_id=?", (instructor_id,)).fetchone()[0], 1)

    def test_admin_crea_periodo_catalogo_y_asignacion(self):
        self.assertEqual(self._login().status_code, 200)
        periodo = self.cliente.post("/api/admin/periodos", json={
            "nombre": "Ciclo demo", "fecha_inicio": "2026-01-01", "fecha_fin": "2026-12-31", "estado": "ACTIVO",
        }, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(periodo.status_code, 201)
        evaluacion = self.cliente.post("/api/admin/evaluaciones", json={
            "codigo": "FIS-DEMO", "nombre": "Evaluación física", "categoria": "FISICA", "origen_nota": "JEFE_PERSONAL",
        }, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(evaluacion.status_code, 201)
        activada = self.cliente.patch(f"/api/admin/evaluaciones/{evaluacion.json['id']}", json={"activo": True}, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(activada.status_code, 200)
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            usuario_id = conexion.execute("SELECT id FROM usuarios WHERE username='voluntario.demo'").fetchone()[0]
            conexion.execute("INSERT INTO voluntarios(usuario_id) VALUES (?)", (usuario_id,))
            conexion.commit()
        asignacion = self.cliente.post("/api/admin/asignaciones", json={
            "voluntario_id": usuario_id, "periodo_id": periodo.json["id"], "evaluacion_id": evaluacion.json["id"],
        }, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(asignacion.status_code, 201)
        self.assertEqual(asignacion.json["estado"], "NO_HABILITADA")
        self.assertEqual(self.cliente.get("/gestion/evaluaciones").status_code, 200)

    def test_instructor_registra_asistencia_y_nota_con_historial(self):
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            instructor_id = conexion.execute("SELECT id FROM usuarios WHERE username='instructor.demo'").fetchone()[0]
            volunteer_id = conexion.execute("SELECT id FROM usuarios WHERE username='voluntario.demo'").fetchone()[0]
            conexion.execute("INSERT INTO instructores(usuario_id) VALUES (?)", (instructor_id,))
            conexion.execute("INSERT INTO voluntarios(usuario_id,instructor_id) VALUES (?,?)", (volunteer_id,instructor_id))
            period_id = conexion.execute("INSERT INTO periodos(nombre,fecha_inicio,fecha_fin,estado) VALUES ('Notas demo','2026-01-01','2026-12-31','ACTIVO')").lastrowid
            evaluation_id = conexion.execute("INSERT INTO evaluaciones(codigo,nombre,categoria,origen_nota,activo) VALUES ('FIS-01','Prueba física','FISICA','JEFE_PERSONAL',1)").lastrowid
            assignment_id = conexion.execute("INSERT INTO asignaciones_evaluacion(voluntario_id,periodo_id,evaluacion_id,estado) VALUES (?,?,?,'HABILITADA')", (volunteer_id,period_id,evaluation_id)).lastrowid
            conexion.commit()
        self.assertEqual(self._login("instructor.demo", "Clave instructor 123!").status_code, 200)
        headers = {"X-CSRFToken": self._csrf_token()}
        asistencia = self.cliente.post("/api/jefe-personal/asistencias", json={
            "fecha": "2026-09-28", "actividad": "Entrenamiento", "asistencias": [{"voluntario_id": volunteer_id, "estado": "PRESENTE"}],
        }, headers=headers)
        self.assertEqual(asistencia.status_code, 200)
        nota = self.cliente.post(f"/api/jefe-personal/asignaciones/{assignment_id}/calificaciones", json={"nota_0_100": 75, "observacion": "Registro inicial"}, headers=headers)
        self.assertEqual(nota.status_code, 201)
        correccion = self.cliente.post(f"/api/jefe-personal/asignaciones/{assignment_id}/calificaciones", json={"nota_0_100": 80, "corregida_de_id": nota.json["id"]}, headers=headers)
        self.assertEqual(correccion.status_code, 201)
        historial = self.cliente.get(f"/api/jefe-personal/asignaciones/{assignment_id}/calificaciones")
        self.assertEqual([item["nota_0_100"] for item in historial.json["historial"]], [75, 80])
        pagina_asistencias = self.cliente.get("/gestion/asistencias")
        self.assertEqual(pagina_asistencias.status_code, 200)
        self.assertIn(b"Fecha de la gesti", pagina_asistencias.data)
        self.assertIn(b"Capacitaciones o cursos", pagina_asistencias.data)
        assets = self.cliente.get("/static/js/app.js")
        self.assertIn(b"ATRASO", assets.data)
        assets.close()
        self.assertEqual(self.cliente.get("/gestion/capacitaciones").status_code, 200)
        self.assertEqual(self.cliente.get("/gestion/calificaciones").status_code, 200)

    def test_asistencias_aceptan_cuatro_estados_y_filtran_por_persona_y_fechas(self):
        with self.app.app_context():
            from sicose.db import obtener_conexion
            connection = obtener_conexion()
            instructor_id = connection.execute("SELECT id FROM usuarios WHERE username='instructor.demo'").fetchone()[0]
            volunteer_id = connection.execute("SELECT id FROM usuarios WHERE username='voluntario.demo'").fetchone()[0]
            connection.execute("INSERT INTO instructores(usuario_id) VALUES (?)", (instructor_id,))
            connection.execute("INSERT INTO voluntarios(usuario_id,instructor_id) VALUES (?,?)", (volunteer_id,instructor_id))
            connection.commit()
        self.assertEqual(self._login("instructor.demo", "Clave instructor 123!").status_code, 200)
        headers = {"X-CSRFToken": self._csrf_token()}
        for index, state in enumerate(("ASISTE", "ATRASO", "PERMISO", "FALTA"), start=1):
            response = self.cliente.post("/api/jefe-personal/asistencias", json={
                "fecha": f"2026-09-0{index}", "actividad": "Entrenamiento",
                "asistencias": [{"voluntario_id": volunteer_id, "estado": state}],
            }, headers=headers)
            self.assertEqual(response.status_code, 200)
        history = self.cliente.get(f"/api/jefe-personal/asistencias?modo=rango&desde=2026-09-01&hasta=2026-09-04&voluntario_id={volunteer_id}")
        self.assertEqual([row["estado"] for row in history.json["asistencias"]], ["FALTA", "PERMISO", "ATRASO", "ASISTE"])
        self.assertEqual(self.cliente.get("/api/jefe-personal/asistencias?modo=rango&desde=2026-09-05&hasta=2026-09-01").status_code, 400)

    def test_capacitaciones_se_listan_y_se_editan_dentro_del_ambito(self):
        with self.app.app_context():
            from sicose.db import obtener_conexion
            connection = obtener_conexion()
            instructor_id = connection.execute("SELECT id FROM usuarios WHERE username='instructor.demo'").fetchone()[0]
            volunteer_id = connection.execute("SELECT id FROM usuarios WHERE username='voluntario.demo'").fetchone()[0]
            connection.execute("INSERT INTO instructores(usuario_id) VALUES (?)", (instructor_id,))
            connection.execute("INSERT INTO voluntarios(usuario_id,instructor_id) VALUES (?,?)", (volunteer_id,instructor_id))
            connection.commit()
        self.assertEqual(self._login("instructor.demo", "Clave instructor 123!").status_code, 200)
        headers = {"X-CSRFToken": self._csrf_token()}
        created = self.cliente.post(f"/api/jefe-personal/instructores-voluntarios/{volunteer_id}/capacitaciones", json={"nombre": "Primeros auxilios", "entidad": "SBRAB", "fecha": "2026-09-10"}, headers=headers)
        self.assertEqual(created.status_code, 201)
        listed = self.cliente.get("/api/jefe-personal/capacitaciones")
        self.assertEqual(listed.json["capacitaciones"][0]["nombre"], "Primeros auxilios")
        edited = self.cliente.patch(f"/api/jefe-personal/capacitaciones/{created.json['id']}", json={"nombre": "Primeros auxilios avanzados"}, headers=headers)
        self.assertEqual(edited.status_code, 200)
        self.assertEqual(self.cliente.get("/api/jefe-personal/capacitaciones").json["capacitaciones"][0]["nombre"], "Primeros auxilios avanzados")

    def test_evaluacion_psicometrica_pendiente_no_se_activa_ni_califica_manualmente(self):
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            instructor_id = conexion.execute("SELECT id FROM usuarios WHERE username='instructor.demo'").fetchone()[0]
            volunteer_id = conexion.execute("SELECT id FROM usuarios WHERE username='voluntario.demo'").fetchone()[0]
            conexion.execute("INSERT INTO instructores(usuario_id) VALUES (?)", (instructor_id,))
            conexion.execute("INSERT INTO voluntarios(usuario_id,instructor_id) VALUES (?,?)", (volunteer_id,instructor_id))
            instrument_id = conexion.execute("INSERT INTO instrumentos(nombre,version,idioma) VALUES ('Candidato','1','es')").lastrowid
            evaluation_id = conexion.execute("INSERT INTO evaluaciones(codigo,nombre,categoria,origen_nota,instrumento_id) VALUES ('PSI-01','Candidato psicométrico','PSICOMETRICA','INSTRUCTOR_VOLUNTARIO',?)", (instrument_id,)).lastrowid
            period_id = conexion.execute("INSERT INTO periodos(nombre,fecha_inicio,fecha_fin,estado) VALUES ('Ciclo psi','2026-01-01','2026-12-31','ACTIVO')").lastrowid
            assignment_id = conexion.execute("INSERT INTO asignaciones_evaluacion(voluntario_id,periodo_id,evaluacion_id) VALUES (?,?,?)", (volunteer_id,period_id,evaluation_id)).lastrowid
            conexion.commit()
        self.assertEqual(self._login().status_code, 200)
        activate = self.cliente.patch(f"/api/admin/evaluaciones/{evaluation_id}", json={"activo": True}, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(activate.status_code, 409)
        self.cliente.post("/api/auth/logout", headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(self._login("instructor.demo", "Clave instructor 123!").status_code, 200)
        score = self.cliente.post(f"/api/jefe-personal/asignaciones/{assignment_id}/calificaciones", json={"nota_0_100": 90}, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(score.status_code, 403)

    def test_voluntario_ve_estado_de_evaluacion_sin_resultados(self):
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            volunteer_id = conexion.execute("SELECT id FROM usuarios WHERE username='voluntario.demo'").fetchone()[0]
            conexion.execute("INSERT INTO voluntarios(usuario_id) VALUES (?)", (volunteer_id,))
            period_id = conexion.execute("INSERT INTO periodos(nombre,fecha_inicio,fecha_fin,estado) VALUES ('Panel demo','2026-01-01','2026-12-31','ACTIVO')").lastrowid
            evaluation_id = conexion.execute("INSERT INTO evaluaciones(codigo,nombre,categoria,origen_nota,activo) VALUES ('FIS-02','Resistencia','FISICA','JEFE_PERSONAL',1)").lastrowid
            assignment_id = conexion.execute("INSERT INTO asignaciones_evaluacion(voluntario_id,periodo_id,evaluacion_id,estado) VALUES (?,?,?,'COMPLETADA')", (volunteer_id,period_id,evaluation_id)).lastrowid
            conexion.execute("INSERT INTO calificaciones(asignacion_id,registrada_por,nota_0_100,observacion) VALUES (?,?,99,'Texto privado')", (assignment_id,1))
            conexion.commit()
        self.assertEqual(self._login("voluntario.demo", "Clave voluntario 123!").status_code, 200)
        respuesta = self.cliente.get("/api/instructor-voluntario/evaluaciones")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json["evaluaciones"][0]["estado"], "COMPLETADA")
        self.assertNotIn("nota_0_100", str(respuesta.json))
        self.assertNotIn("observacion", str(respuesta.json))

    def test_admin_aprueba_solicitud_y_cuenta_puede_ingresar(self):
        creada = self.cliente.post("/api/registro/solicitudes", json={
            "username": "aprobada.demo", "nombres": "Voluntaria", "apellido_paterno": "Aprobada", "apellido_materno": "Demo",
            "fecha_nacimiento": "1990-06-07",
            "password": "Contraseña segura 123!",
        }, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(creada.status_code, 201)
        self.assertEqual(self._login().status_code, 200)
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            instructor_id = conexion.execute("SELECT id FROM usuarios WHERE username='instructor.demo'").fetchone()[0]
            conexion.execute("INSERT INTO instructores (usuario_id) VALUES (?)", (instructor_id,))
            conexion.commit()
        solicitud_id = self.cliente.get("/api/admin/solicitudes").json["solicitudes"][0]["id"]
        aprobada = self.cliente.post(f"/api/admin/solicitudes/{solicitud_id}/aprobar", json={"instructor_id": instructor_id}, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(aprobada.status_code, 200)
        with self.app.app_context():
            from sicose.db import obtener_conexion
            asignado = obtener_conexion().execute("SELECT instructor_id FROM voluntarios JOIN usuarios ON usuarios.id=voluntarios.usuario_id WHERE username='aprobada.demo'").fetchone()[0]
            self.assertEqual(asignado, instructor_id)
        self.cliente.post("/api/auth/logout", headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(self._login("aprobada.demo", "Contraseña segura 123!").status_code, 200)

    def test_invitacion_es_de_un_solo_uso_y_requiere_aprobacion(self):
        self.assertEqual(self._login().status_code, 200)
        creada = self.cliente.post("/api/admin/invitaciones", json={"correo": "invitada@example.org"}, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(creada.status_code, 201)
        token = creada.json["invitacion_url"].rsplit("/", 1)[1]
        respuesta = self.cliente.post(f"/api/registro/invitaciones/{token}", json={
            "username": "invitada.demo", "nombres": "Invitada", "apellido_paterno": "Prueba", "apellido_materno": "Demo",
            "fecha_nacimiento": "1987-12-08", "correo": "invitada@example.org",
            "password": "Contraseña segura 123!",
        }, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(respuesta.status_code, 201)
        repetida = self.cliente.post(f"/api/registro/invitaciones/{token}", json={
            "username": "otra.demo", "nombres": "Otra", "apellido_paterno": "Prueba", "apellido_materno": "Demo",
            "fecha_nacimiento": "1987-12-08", "correo": "invitada@example.org",
            "password": "Contraseña segura 123!",
        }, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(repetida.status_code, 404)

    def test_instructor_solo_lista_y_desactiva_su_equipo(self):
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            instructor_id = conexion.execute("SELECT id FROM usuarios WHERE username='instructor.demo'").fetchone()[0]
            conexion.execute("INSERT INTO instructores (usuario_id) VALUES (?)", (instructor_id,))
            voluntario_id = conexion.execute("SELECT id FROM usuarios WHERE username='voluntario.demo'").fetchone()[0]
            conexion.execute("INSERT INTO voluntarios (usuario_id, instructor_id) VALUES (?, ?)", (voluntario_id, instructor_id))
            conexion.commit()
        self.assertEqual(self._login("instructor.demo", "Clave instructor 123!").status_code, 200)
        listado = self.cliente.get("/api/instructores-voluntarios")
        self.assertEqual([v["username"] for v in listado.json["voluntarios"]], ["voluntario.demo"])
        desactivado = self.cliente.post("/api/instructores-voluntarios/3/desactivar", headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(desactivado.status_code, 200)

    def test_instructor_no_puede_editar_voluntario_de_otro(self):
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            instructor_id = conexion.execute("SELECT id FROM usuarios WHERE username='instructor.demo'").fetchone()[0]
            conexion.execute("INSERT INTO instructores (usuario_id) VALUES (?)", (instructor_id,))
            otro_id = conexion.execute("SELECT id FROM usuarios WHERE username='admin.demo'").fetchone()[0]
            # Perfil voluntario distinto al ámbito asignado.
            conexion.execute("INSERT INTO voluntarios (usuario_id) VALUES (?)", (otro_id,))
            conexion.commit()
        self.assertEqual(self._login("instructor.demo", "Clave instructor 123!").status_code, 200)
        respuesta = self.cliente.patch("/api/instructores-voluntarios/1", json={"nombre": "Cambio"}, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(respuesta.status_code, 404)

    def test_csrf_rechaza_post_sin_token(self):
        csrf_db = Path(".tmp") / f"csrf-{uuid.uuid4().hex}.sqlite3"
        csrf_app = create_app(
            {
                "TESTING": True,
                "WTF_CSRF_ENABLED": True,
                "SECRET_KEY": "clave-de-prueba-csrf",
                "DATABASE": str(csrf_db.resolve()),
            }
        )
        csrf_client = csrf_app.test_client()
        respuesta = csrf_client.post(
            "/api/auth/login", json={"username": "admin.demo", "password": "cualquiera"}
        )
        self.assertEqual(respuesta.status_code, 400)
        if csrf_db.exists():
            csrf_db.unlink()

    def test_configura_cookie_protegida(self):
        self.assertTrue(self.app.config["SESSION_COOKIE_HTTPONLY"])
        self.assertEqual(self.app.config["SESSION_COOKIE_SAMESITE"], "Lax")
        self.assertEqual(self.app.config["PERMANENT_SESSION_LIFETIME"].total_seconds(), 8 * 3600)

    def test_login_registra_auditoria_sin_credenciales(self):
        self._login(password="clave incorrecta")
        self._login()
        self.cliente.post(
            "/api/auth/logout", headers={"X-CSRFToken": self._csrf_token()}
        )
        with self.app.app_context():
            from sicose.db import obtener_conexion

            eventos = obtener_conexion().execute(
                "SELECT accion, resultado FROM auditoria ORDER BY id"
            ).fetchall()
            self.assertEqual(
                [(fila["accion"], fila["resultado"]) for fila in eventos],
                [("LOGIN", "FALLIDO"), ("LOGIN", "EXITOSO"), ("LOGOUT", "EXITOSO")],
            )


if __name__ == "__main__":
    unittest.main()
