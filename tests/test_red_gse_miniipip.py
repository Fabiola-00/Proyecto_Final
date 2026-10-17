"""Integridad, gradientes y separación del nuevo experimento sintético."""
from collections import Counter
from copy import deepcopy
import csv
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from sicose.red_gse_miniipip import (RedGseMiniIpip, datos_sinteticos,
    normalizar, objetivos_sinteticos, SALIDAS)


class RedGseMiniIpipTestCase(unittest.TestCase):
    def test_cli_y_modelo_guardado_reproducibles(self):
        Path('.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir='.tmp') as carpeta:
            destino = Path(carpeta)/'modelo'
            proceso = subprocess.run([sys.executable, 'scripts/entrenar_red_gse_miniipip.py',
                                      '--salida', str(destino)], capture_output=True, timeout=30)
            self.assertEqual(proceso.returncode, 0, proceso.stderr)
            manifest = json.loads((destino/'manifest.json').read_text(encoding='utf-8'))
            for nombre, huella in manifest['sha256'].items():
                self.assertEqual(hashlib.sha256((destino/nombre).read_bytes()).hexdigest(), huella)
            modelo = json.loads((destino/'modelo.json').read_text(encoding='utf-8'))
            informe = json.loads((destino/'informe.json').read_text(encoding='utf-8'))
            with (destino/'datos_sinteticos.csv').open(newline='', encoding='utf-8') as archivo:
                self.assertEqual(len(list(csv.DictReader(archivo))), 200)
            red = RedGseMiniIpip()
            red._restaurar(modelo['pesos'])
            red.entrenada = True
            filas = datos_sinteticos()
            val = [f for f in filas if f['particion'] == 'validacion']
            self.assertAlmostEqual(red.perdida(val), informe['evaluaciones']['validacion']['entropia_cruzada'])
            referencia = RedGseMiniIpip()
            referencia.entrenar([f for f in filas if f['particion'] == 'entrenamiento'],
                               epocas=modelo['entrenamiento']['epoca_elegida'], l2=.001)
            self.assertEqual(red._pesos(), referencia._pesos())
            self.assertEqual(informe['parametros'], 88)
            original = Path('output/modelo_sintetico_200_20261017')
            seleccion = json.loads((original/'seleccion_modelo.json').read_text(encoding='utf-8'))
            for nombre, huella in seleccion['huellas_sha256'].items():
                self.assertEqual(hashlib.sha256((original/nombre).read_bytes()).hexdigest(), huella)
            # Un destino existente se rechaza antes de sobrescribir sus archivos.
            repetido = subprocess.run([sys.executable, 'scripts/entrenar_red_gse_miniipip.py',
                                      '--salida', str(destino)], capture_output=True, timeout=30)
            self.assertNotEqual(repetido.returncode, 0)
            for nombre, huella in manifest['sha256'].items():
                self.assertEqual(hashlib.sha256((destino/nombre).read_bytes()).hexdigest(), huella)

    def test_rangos_normalizacion_y_ausencias(self):
        self.assertEqual(normalizar([0, 0, 0, 10, 4, 4, 4, 4, 4]), [0]*9)
        self.assertEqual(normalizar([100, 100, 100, 40, 20, 20, 20, 20, 20]), [1]*9)
        for valor in (None, 0, 9, 41, float('nan'), True):
            with self.assertRaises(ValueError):
                normalizar([50, 50, 50, valor, 12, 12, 12, 12, 12])

    def test_200_reproducibles_completos_disjuntos_y_equilibrados(self):
        filas = datos_sinteticos()
        self.assertEqual(filas, datos_sinteticos())
        self.assertEqual(len({tuple(f['entradas']) for f in filas}), 200)
        self.assertEqual({f['id'] for f in filas}, set(range(1, 201)))
        self.assertEqual(Counter(f['particion'] for f in filas),
                         dict(entrenamiento=140, validacion=30, prueba=30))
        for f in filas:
            self.assertEqual(f['objetivos'], objetivos_sinteticos(f['entradas']))
            self.assertEqual(f['origen'], 'SINTETICO')
            normalizar(f['entradas'])
        for p, n in (('entrenamiento', 140), ('validacion', 30), ('prueba', 30)):
            grupo = [f for f in filas if f['particion'] == p]
            self.assertEqual({tuple(f['objetivos']) for f in grupo}, set(itertools.product((0, 1), repeat=4)))
            self.assertEqual([sum(f['objetivos'][i] for f in grupo) for i in range(4)], [n//2]*4)

    def test_personalidad_aislada_no_activa_salidas(self):
        for rasgos in itertools.product((4, 20), repeat=5):
            self.assertEqual(objetivos_sinteticos([100, 100, 100, 40, *rasgos]), [0]*4)

    def test_gradientes_de_los_88_parametros(self):
        red = RedGseMiniIpip()
        x, t = [55, 72, 30, 19, 8, 16, 11, 18, 7], [1, 0, 1, 1]
        antes = deepcopy(red._pesos())
        red._paso({'entradas': x, 'objetivos': t}, .001, 0)
        despues = red._pesos()
        red._restaurar(antes)
        fila = [{'entradas': x, 'objetivos': t}]
        cantidad = 0
        for nombre in antes:
            pesos = getattr(red, nombre)
            for j, valor in enumerate(pesos):
                indices = range(len(valor)) if isinstance(valor, list) else (None,)
                for i in indices:
                    grupo = pesos[j] if i is not None else pesos
                    indice = i if i is not None else j
                    original = grupo[indice]
                    grupo[indice] = original+1e-5
                    mas = red.perdida(fila)
                    grupo[indice] = original-1e-5
                    menos = red.perdida(fila)
                    grupo[indice] = original
                    nuevo = despues[nombre][j][i] if i is not None else despues[nombre][j]
                    self.assertAlmostEqual((original-nuevo)/.001, (mas-menos)/2e-5, places=6)
                    cantidad += 1
        self.assertEqual(cantidad, 88)

    def test_exportacion_y_simulacion_con_nuevas_salidas(self):
        filas = datos_sinteticos()
        train = [f for f in filas if f['particion'] == 'entrenamiento']
        val = [f for f in filas if f['particion'] == 'validacion']
        red = RedGseMiniIpip()
        red.entrenar(train, validacion=val, epocas=60, l2=.001)
        modelo = red.exportar()
        self.assertEqual(modelo['arquitectura'], [9, 6, 4])
        self.assertEqual(modelo['salidas'], SALIDAS)
        self.assertEqual(modelo['minimos'][3], 10)
        self.assertFalse(modelo['uso_en_personas'])
        resultado = red.simular(val[0]['entradas'])
        self.assertEqual(tuple(resultado['activaciones_no_calibradas']), SALIDAS)
        self.assertFalse(resultado['uso_en_personas'])

    def test_no_entrena_con_prueba_o_puntuaciones_invalidas(self):
        filas = datos_sinteticos()
        red = RedGseMiniIpip()
        antes = deepcopy(red._pesos())
        with self.assertRaises(ValueError):
            red.entrenar([f for f in filas if f['particion'] == 'prueba'])
        train = [f for f in filas if f['particion'] == 'entrenamiento']
        train[-1]['entradas'][3] = 0
        with self.assertRaises(ValueError):
            red.entrenar(train)
        self.assertEqual(red._pesos(), antes)
