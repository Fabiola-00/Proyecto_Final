"""Reglas del experimento de quince entradas; sin base de datos ni Flask."""
import importlib.util
from pathlib import Path
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('etiquetas_tlx', SCRIPTS/'etiquetar_datos_tlx_gse_miniipip.py')
modulo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(modulo)


class EtiquetasTlxTest(unittest.TestCase):
    def test_sin_dificultades_contextuales_no_activa_por_rasgos(self):
        # GSE bajo, neuroticismo alto, demás Mini bajos: no bastan sin contexto.
        x = [100, 100, 100, 10, 4, 4, 4, 20, 4, 0, 0, 0, 0, 0, 0]
        self.assertEqual(modulo.puntuar(x), [0, 0, 0, 0])

    def test_todas_combinables_y_ninguna(self):
        self.assertEqual(modulo.puntuar([0, 0, 0, 10, 4, 4, 4, 20, 4, 100, 100, 100, 100, 100, 100]), [1]*4)
        self.assertEqual(modulo.puntuar([100, 100, 100, 40, 20, 20, 20, 4, 20, 0, 0, 0, 0, 0, 0]), [0]*4)

    def test_rendimiento_tlx_mayor_es_peor(self):
        x = [100, 100, 100, 40, 20, 20, 20, 4, 20, 50, 0, 50, 0, 0, 0]
        self.assertEqual(modulo.puntuar(x)[1], 0)
        x[12] = 100
        self.assertEqual(modulo.puntuar(x)[1], 1)

    def test_no_imputa_datos_invalidos(self):
        x = [100, 100, 100, 40, 20, 20, 20, 4, 20, 0, 0, 0, 0, 0, 0]
        for i, v in ((0, True), (3, 9), (6, 21), (12, -5), (0, float('nan')), (0, None)):
            copia = x.copy(); copia[i] = v
            with self.assertRaises(ValueError): modulo.puntuar(copia)
        with self.assertRaises(ValueError): modulo.puntuar(x[:-1])

    def test_igualdad_del_umbral_es_inclusiva(self):
        # .30*.5 + .30*.5 + .20*1 = .50, con condición por R.
        x = [100, 100, 100, 40, 20, 20, 20, 4, 20, 50, 0, 50, 100, 0, 0]
        self.assertEqual(modulo.puntuar(x)[1], 1)


if __name__ == '__main__':
    unittest.main()
