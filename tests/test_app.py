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
        pagina = self.cliente.get("/login")
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
            self.assertEqual(version, "2")
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
