"""Pruebas de autenticación, autorización y persistencia SICOSE."""

import re
import sqlite3
import unittest
import uuid
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

from sicose import create_app
from sicose.db import inicializar_base_datos, seed_admin


class AplicacionTestCase(unittest.TestCase):
    def setUp(self):
        Path(".tmp").mkdir(exist_ok=True)
        self.db_path = Path(".tmp") / f"test-{uuid.uuid4().hex}.sqlite3"
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "clave-de-prueba-no-usar-fuera-de-tests",
                "DATABASE": str(self.db_path.resolve()),
            }
        )
        self.cliente = self.app.test_client()
        with self.app.app_context():
            inicializar_base_datos()
            self._crear_usuario("admin.demo", "ADMINISTRADOR", "Clave demo segura 123!")
            self._crear_usuario("instructor.demo", "INSTRUCTOR", "Clave instructor 123!")
            self._crear_usuario("voluntario.demo", "VOLUNTARIO", "Clave voluntario 123!")

    def tearDown(self):
        self.cliente = None
        if self.db_path.exists():
            self.db_path.unlink()

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

            self._crear_usuario("pendiente.demo", "VOLUNTARIO", "Clave pendiente 123!")
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
        self.assertIn(b"SICOSE", respuesta.data)

    def test_inicio_instructor_muestra_solo_su_panel(self):
        self.assertEqual(self._login("instructor.demo", "Clave instructor 123!").status_code, 200)
        respuesta = self.cliente.get("/", follow_redirects=True)
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(b"Panel del instructor", respuesta.data)
        self.assertIn(b"Seguimiento asignado", respuesta.data)
        self.assertNotIn(b"Panel de administraci\xc3\xb3n", respuesta.data)

    def test_inicio_voluntario_muestra_solo_su_panel(self):
        self.assertEqual(self._login("voluntario.demo", "Clave voluntario 123!").status_code, 200)
        respuesta = self.cliente.get("/", follow_redirects=True)
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(b"Mi seguimiento", respuesta.data)
        self.assertIn(b"Privacidad personal", respuesta.data)
        self.assertNotIn(b"Panel del instructor", respuesta.data)

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
            version = conexion.execute(
                "SELECT valor FROM app_meta WHERE clave = ?", ("schema_version",)
            ).fetchone()[0]
            self.assertEqual(version, "3")
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

    def test_solicitud_publica_crea_usuario_pendiente_sin_sesion(self):
        respuesta = self.cliente.post("/api/registro/solicitudes", json={
            "username": "nueva.demo", "nombre": "Nueva Voluntaria",
            "correo": "nueva@example.org", "password": "Contraseña segura 123!",
        }, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(self.cliente.get("/api/auth/me").status_code, 401)
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            usuario = conexion.execute("SELECT estado, password_hash FROM usuarios WHERE username='nueva.demo'").fetchone()
            self.assertEqual(usuario["estado"], "PENDIENTE")
            self.assertNotEqual(usuario["password_hash"], "Contraseña segura 123!")
            self.assertEqual(conexion.execute("SELECT COUNT(*) FROM solicitudes_registro").fetchone()[0], 1)

    def test_paginas_registro_y_gestion_cargan(self):
        registro = self.cliente.get("/registro")
        self.assertEqual(registro.status_code, 200)
        self.assertIn(b"Solicitud de registro", registro.data)
        self.assertEqual(self._login().status_code, 200)
        gestion = self.cliente.get("/gestion/voluntarios")
        self.assertEqual(gestion.status_code, 200)
        self.assertIn(b"Solicitudes pendientes", gestion.data)
        instructores = self.cliente.get("/gestion/instructores")
        self.assertEqual(instructores.status_code, 200)
        self.assertIn(b"Registrar instructor", instructores.data)
        self.assertEqual(self.cliente.get("/api/admin/instructores").mimetype, "application/json")

    def test_admin_crea_instructor_y_cuenta_accede_a_panel_diferenciado(self):
        self.assertEqual(self._login().status_code, 200)
        creada = self.cliente.post("/api/admin/instructores", json={
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
        self.assertIn(b"Panel del instructor", inicio.data)
        self.assertNotIn(b"Panel de administraci", inicio.data)
        rechazo = self.cliente.post("/api/admin/instructores", json={}, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(rechazo.status_code, 403)

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
        editada = self.cliente.patch(f"/api/admin/instructores/{instructor_id}", json={
            "nombre": "Instructor Editado", "especialidad": "Montaña",
        }, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(editada.status_code, 200)
        baja = self.cliente.post(f"/api/admin/instructores/{instructor_id}/desactivar", headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(baja.status_code, 200)
        self.assertEqual(baja.json["voluntarios_desvinculados"], 1)
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            self.assertEqual(conexion.execute("SELECT estado FROM usuarios WHERE id=?", (instructor_id,)).fetchone()[0], "INACTIVO")
            self.assertIsNone(conexion.execute("SELECT instructor_id FROM voluntarios WHERE usuario_id=?", (voluntario_id,)).fetchone()[0])
            self.assertEqual(conexion.execute("SELECT COUNT(*) FROM instructores WHERE usuario_id=?", (instructor_id,)).fetchone()[0], 1)

    def test_admin_aprueba_solicitud_y_cuenta_puede_ingresar(self):
        creada = self.cliente.post("/api/registro/solicitudes", json={
            "username": "aprobada.demo", "nombre": "Voluntaria Aprobada",
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
            "username": "invitada.demo", "nombre": "Invitada", "correo": "invitada@example.org",
            "password": "Contraseña segura 123!",
        }, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(respuesta.status_code, 201)
        repetida = self.cliente.post(f"/api/registro/invitaciones/{token}", json={
            "username": "otra.demo", "nombre": "Otra", "correo": "invitada@example.org",
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
        listado = self.cliente.get("/api/voluntarios")
        self.assertEqual([v["username"] for v in listado.json["voluntarios"]], ["voluntario.demo"])
        desactivado = self.cliente.post("/api/voluntarios/3/desactivar", headers={"X-CSRFToken": self._csrf_token()})
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
        respuesta = self.cliente.patch("/api/voluntarios/1", json={"nombre": "Cambio"}, headers={"X-CSRFToken": self._csrf_token()})
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
