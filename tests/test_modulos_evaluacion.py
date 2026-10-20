"""Separación de navegación/páginas sin modificar permisos ni datos."""
import unittest
import test_modelo_anual as fixtures
from sicose.db import obtener_conexion


class ModulosEvaluacionTest(unittest.TestCase):
    for nombre, valor in vars(fixtures.ModeloAnualTestCase).items():
        if (nombre.startswith('_') and not nombre.startswith('__')) or nombre in ('setUp','tearDown'):
            locals()[nombre] = valor

    def test_paginas_administrativas_separadas_y_nav_activa(self):
        for username, password in (('admin.demo','Clave demo segura 123!'),('instructor.demo','Clave instructor 123!')):
            self._login(username,password)
            institucional = self.cliente.get('/gestion/modelo-anual')
            self.assertEqual(institucional.status_code,200)
            html = institucional.data.decode()
            for texto in ('id="psicometria-activaciones"','id="psicometria-resultados"','id="recomendacion-panel"','js/psicometria.js','js/recomendaciones.js'):
                self.assertNotIn(texto,html)
            self.assertNotIn('Evaluaciones históricas',html)
            self.assertNotIn('Calificaciones y publicaciones históricas',html)
            seguimiento = self.cliente.get('/gestion/seguimiento-operativo?historico=1')
            self.assertEqual(seguimiento.status_code,302)
            self.assertEqual(seguimiento.headers['Location'],'/gestion/modelo-anual')
            retirada = self.cliente.get('/gestion/evaluaciones-personal?historico=1')
            self.assertEqual(retirada.status_code,302)
            self.assertEqual(retirada.headers['Location'],'/gestion/modelo-anual')
            self.assertIn('id="modelo-notas"',html)
            self.assertIn('data-contexto-evaluacion',html)
            self.assertEqual(html.count('aria-current="page"'),1)
            pruebas = self.cliente.get('/gestion/pruebas-recomendacion?periodo_id=1&persona_id=3')
            self.assertEqual(pruebas.status_code,200)
            html = pruebas.data.decode()
            for texto in ('id="psicometria-activaciones"','id="recomendacion-panel"','js/pruebas_recomendacion.js'):
                self.assertIn(texto,html)
            self.assertNotIn('id="modelo-notas"',html)
            self.assertNotIn('js/modelo_anual.js',html)
            self.assertEqual(html.count('aria-current="page"'),1)
            self.assertEqual(pruebas.headers['Cache-Control'],'private, no-store')

    def test_instructor_mueve_formularios_sin_acceso_a_recomendaciones(self):
        self._login('voluntario.demo','Clave voluntario 123!')
        propia=self.cliente.get('/gestion/pruebas-recomendacion')
        self.assertEqual(propia.status_code,200)
        html=propia.data.decode()
        self.assertIn('id="psicometria-propia"',html)
        self.assertNotIn('id="recomendacion-panel"',html)
        self.assertNotIn('js/recomendaciones.js',html)
        self.assertEqual(html.count('aria-current="page"'),1)
        self.assertNotIn('id="psicometria-propia"',self.cliente.get('/mis-evaluaciones/anual').data.decode())
        self.assertEqual(self.cliente.get('/gestion/modelo-anual').status_code,403)
        self.assertEqual(self.cliente.get('/api/modelo-anual/gestiones/1/personas/3/recomendacion').status_code,403)

    def test_sesion_requerida_y_consulta_no_modifica_registros(self):
        self.assertIn(self.cliente.get('/gestion/pruebas-recomendacion').status_code,(302,401))
        self._login('admin.demo','Clave demo segura 123!')
        with self.app.app_context():
            c=obtener_conexion()
            antes={t:c.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in ('intentos_pruebas','reinicios_pruebas','recomendaciones')}
        for ruta in ('/gestion/modelo-anual','/gestion/pruebas-recomendacion'):
            self.assertEqual(self.cliente.get(ruta).status_code,200)
        with self.app.app_context():
            c=obtener_conexion()
            self.assertEqual(antes,{t:c.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in antes})
