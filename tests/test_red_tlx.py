"""Verificación numérica del gradiente de ambas arquitecturas experimentales."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from red_tlx_experimental import RedTlx


class RedTlxTest(unittest.TestCase):
    def setUp(self):
        self.fila = dict(id=1, origen='Datos', particion='entrenamiento',
                         entradas=[65, 40, 55, 25, 8, 12, 15, 9, 16, 30, 50, 70, 25, 60, 40],
                         objetivos=[1, 0, 1, 0])

    def test_gradiente_numerico_todos_pesos_y_sesgos(self):
        for ocultas in ((6,), (6, 6)):
            red = RedTlx(ocultas)
            dw, db = red.gradientes(self.fila)
            eps = 1e-5
            for conjunto, gradientes in ((red.w, dw), (red.b, db)):
                for l, capa in enumerate(conjunto):
                    for k, elemento in enumerate(capa):
                        vector = elemento if isinstance(elemento, list) else capa
                        indices = range(len(vector)) if isinstance(elemento, list) else [k]
                        for j in indices:
                            inicial = vector[j]
                            vector[j] = inicial+eps; mayor = red.perdida([self.fila])
                            vector[j] = inicial-eps; menor = red.perdida([self.fila])
                            vector[j] = inicial
                            esperado = gradientes[l][k][j] if isinstance(elemento, list) else gradientes[l][k]
                            self.assertAlmostEqual((mayor-menor)/(2*eps), esperado, places=7)

    def test_dimensiones_parametros_y_reproducibilidad(self):
        for ocultas, n in (((6,), 124), ((6, 6), 166)):
            a, b = RedTlx(ocultas), RedTlx(ocultas)
            self.assertEqual(a.exportar(), b.exportar())
            self.assertEqual(a.exportar()['parametros'], n)
            self.assertEqual(len(a.adelante(self.fila['entradas'])[-1]), 4)
            self.assertEqual(a.normalizar([v[2] for v in __import__('generar_datos_tlx_gse_miniipip').VARIABLES]), [0]*15)

    def test_bloquea_solapamiento_y_particion_de_prueba(self):
        red = RedTlx()
        for f in (dict(self.fila, particion='prueba'), dict(self.fila, origen='Real')):
            with self.assertRaises(ValueError):
                red.entrenar([f], [dict(self.fila, id=2, particion='validacion')])
        with self.assertRaises(ValueError):
            red.entrenar([self.fila], [dict(self.fila, particion='validacion')])

    def test_entrenamiento_restaura_minimo_validacion(self):
        for ocultas in ((6,), (6, 6)):
            red = RedTlx(ocultas)
            v = dict(self.fila, id=2, particion='validacion', entradas=[66, *self.fila['entradas'][1:]])
            inicial = red.perdida([v])
            red.entrenar([self.fila], [v], epocas=25)
            self.assertLess(red.perdida([v]), inicial)
            self.assertAlmostEqual(red.perdida([v]), min(red.entrenamiento['perdida_validacion_por_epoca']), places=10)


if __name__ == '__main__':
    unittest.main()
