"""Regresión de la alternativa GSE/Mini-IPIP y comparación sobre el CSV actual."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from sicose.red_gse_miniipip import RedGseMiniIpipDosCapas, datos_sinteticos, SALIDAS


class ComparacionGseTestCase(unittest.TestCase):
    def test_gradientes_de_los_108_parametros_con_regularizacion(self):
        red = RedGseMiniIpipDosCapas()
        fila = {'entradas': [73, 61, 46, 24, 8, 19, 12, 16, 7], 'objetivos': [0, 0, 1, 1]}
        antes = deepcopy(red._pesos())
        red._paso(fila, .005, .001)
        despues = deepcopy(red._pesos())
        red._restaurar(deepcopy(antes))
        def objetivo():
            return red.perdida([fila]) + .001/2*sum(w*w for k, v in red._pesos().items()
                                                   if k.startswith('w') for f in v for w in f)
        n = 0
        for k, valores in antes.items():
            indices = [(i, j) for i, f in enumerate(valores) for j in range(len(f))] if k.startswith('w') else [(i, None) for i in range(len(valores))]
            for i, j in indices:
                grupo, pos = (getattr(red, k)[i], j) if j is not None else (getattr(red, k), i)
                v = grupo[pos]
                grupo[pos] = v+1e-6
                mas = objetivo()
                grupo[pos] = v-1e-6
                menos = objetivo()
                grupo[pos] = v
                nuevo = despues[k][i][j] if j is not None else despues[k][i]
                self.assertAlmostEqual((v-nuevo)/.005, (mas-menos)/2e-6, delta=2e-6)
                n += 1
        self.assertEqual(n, 108)
        self.assertEqual(red.exportar()['arquitectura'], [9, 6, 4, 4])

    def test_restaura_todas_las_capas_y_conserva_semantica_gse(self):
        filas = datos_sinteticos()
        train = [f for f in filas if f['particion'] == 'entrenamiento']
        val = [f for f in filas if f['particion'] == 'validacion']
        red = RedGseMiniIpipDosCapas()
        red.entrenar(train, validacion=val, epocas=100, paciencia=5, l2=.001)
        control = RedGseMiniIpipDosCapas()
        control.entrenar(train, epocas=red.entrenamiento['epoca_elegida'], l2=.001)
        self.assertEqual(red._pesos(), control._pesos())
        m = red.exportar()
        self.assertEqual(m['minimos'], (0, 0, 0, 10, 4, 4, 4, 4, 4))
        self.assertEqual(m['salidas'], SALIDAS)
        self.assertIn('DOS_CAPAS', m['formato'])
        self.assertEqual(tuple(red.simular(val[0]['entradas'])['activaciones_no_calibradas']), SALIDAS)
        self.assertFalse(red.simular(val[0]['entradas'])['uso_en_personas'])

    def test_no_selecciona_con_prueba_ni_acepta_rangos_antiguos(self):
        red = RedGseMiniIpipDosCapas()
        antes = deepcopy(red._pesos())
        filas = datos_sinteticos()
        train = [f for f in filas if f['particion'] == 'entrenamiento']
        prueba = [f for f in filas if f['particion'] == 'prueba']
        with self.assertRaises(ValueError):
            red.entrenar(train, validacion=prueba)
        train[-1]['entradas'][4] = 25
        with self.assertRaises(ValueError):
            red.entrenar(train)
        self.assertEqual(red._pesos(), antes)

    def test_cli_mismo_csv_control_exacto_y_modelo_actual_preservado(self):
        base = Path('output/modelo_gse_miniipip_200_20261017')
        manifest = json.loads((base/'manifest.json').read_text(encoding='utf-8'))
        Path('.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir='.tmp') as carpeta:
            salida = Path(carpeta)/'comparacion'
            r = subprocess.run([sys.executable, 'scripts/comparar_redes_sinteticas.py',
                '--perfil', 'gse-miniipip', '--alternativa', '9-6-4-4', '--semillas', '31415', '7',
                '--salida', str(salida)], capture_output=True, timeout=40)
            self.assertEqual(r.returncode, 0, r.stderr)
            comparacion = json.loads((salida/'comparacion.json').read_text(encoding='utf-8'))
            self.assertFalse(comparacion['modelo_base_sustituido'])
            self.assertEqual(comparacion['protocolo']['perfil'], 'gse-miniipip')
            self.assertEqual((salida/'datos_sinteticos.csv').read_bytes(), (base/'datos_sinteticos.csv').read_bytes())
            modelo = json.loads((base/'modelo.json').read_text(encoding='utf-8'))
            control = json.loads((salida/'9-6-4/modelo_semilla_31415.json').read_text(encoding='utf-8'))
            self.assertEqual(modelo, control)
            alternativa = json.loads((salida/'9-6-4-4/modelo_semilla_31415.json').read_text(encoding='utf-8'))
            self.assertEqual(alternativa['entradas'], modelo['entradas'])
            self.assertEqual(alternativa['salidas'], modelo['salidas'])
            self.assertEqual(alternativa['arquitectura'], [9, 6, 4, 4])
            self.assertEqual(comparacion['resumen']['9-6-4-4']['parametros'], 108)
            for nombre, huella in manifest['sha256'].items():
                self.assertEqual(hashlib.sha256((base/nombre).read_bytes()).hexdigest(), huella)
