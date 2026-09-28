"""Pruebas básicas de disponibilidad HTTP de SICOPE."""

import unittest

from sicope import create_app


class AplicacionTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({"TESTING": True, "DATABASE": ":memory:"})
        self.cliente = self.app.test_client()

    def test_pagina_inicial_responde(self):
        respuesta = self.cliente.get("/")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(b"SICOPE", respuesta.data)

    def test_api_salud_responde_json(self):
        respuesta = self.cliente.get("/api/health")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.mimetype, "application/json")
        self.assertEqual(respuesta.get_json(), {"estado": "ok", "aplicacion": "SICOPE"})

    def test_inicializa_esquema_base_sqlite(self):
        from sicope.db import inicializar_base_datos, obtener_conexion

        with self.app.app_context():
            inicializar_base_datos()
            fila = obtener_conexion().execute(
                "SELECT valor FROM app_meta WHERE clave = ?", ("schema_version",)
            ).fetchone()
            self.assertEqual(fila["valor"], "1")


if __name__ == "__main__":
    unittest.main()
