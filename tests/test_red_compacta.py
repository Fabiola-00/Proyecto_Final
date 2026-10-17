"""Modelo compacto: presupuesto de datos, separación y selección por validación."""
import csv
import hashlib
import io
import itertools
import json
from collections import Counter
from copy import deepcopy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from sicose.red_experimental import ENTRADAS, SALIDAS, RedExperimental, datos_sinteticos


class RedCompactaTestCase(unittest.TestCase):
    def test_200_totales_equilibrio_y_cobertura_en_cada_particion(self):
        filas = datos_sinteticos()
        self.assertEqual(len(filas), 200)
        self.assertEqual(filas, datos_sinteticos())
        self.assertEqual({f['id'] for f in filas}, set(range(1, 201)))
        self.assertEqual(len({tuple(f['entradas']) for f in filas}), 200)
        self.assertEqual(sorted(Counter(tuple(f['objetivos']) for f in filas).values()), [12]*8+[13]*8)
        for p, n in [('entrenamiento', 140), ('validacion', 30), ('prueba', 30)]:
            grupo = [f for f in filas if f['particion'] == p]
            self.assertEqual(len(grupo), n)
            self.assertEqual({tuple(f['objetivos']) for f in grupo}, set(itertools.product((0, 1), repeat=4)))
            self.assertEqual([sum(f['objetivos'][i] for f in grupo) for i in range(4)], [n//2]*4)

    def test_reproduce_generador_historico_sin_mezclarlo_con_200(self):
        salida = io.StringIO(newline='')
        w = csv.writer(salida)
        w.writerow(('id', 'origen', 'particion', *ENTRADAS, *SALIDAS))
        w.writerows((f['id'], f['origen'], f['particion'], *f['entradas'], *f['objetivos']) for f in datos_sinteticos(128))
        self.assertEqual(hashlib.sha256(salida.getvalue().encode()).hexdigest(),
                         '1e9f7bea3ae65948bdae77740bb4f95305a3894968990eafb623e9364d29f012')

    def test_restaura_mejor_epoca_y_reduce_parametros(self):
        filas = datos_sinteticos()
        train = [f for f in filas if f['particion'] == 'entrenamiento']
        val = [f for f in filas if f['particion'] == 'validacion']
        red = RedExperimental()
        self.assertEqual(red.exportar()['arquitectura'], [9, 6, 4])
        red.entrenar(train, validacion=val, epocas=100, l2=.001)
        meta = red.entrenamiento
        self.assertLess(meta['epocas_ejecutadas'], 100)
        self.assertEqual(meta['epocas_ejecutadas']-meta['epoca_elegida'], 25)
        referencia = RedExperimental()
        referencia.entrenar(train, epocas=meta['epoca_elegida'], l2=.001)
        self.assertEqual(red.exportar()['pesos'], referencia.exportar()['pesos'])
        self.assertEqual(red.perdida(val), referencia.perdida(val))
        self.assertFalse(red.simular(val[0]['entradas'])['uso_en_personas'])

    def test_no_selecciona_con_prueba_ni_con_datos_solapados(self):
        filas = datos_sinteticos()
        train = [f for f in filas if f['particion'] == 'entrenamiento']
        val = [f for f in filas if f['particion'] == 'validacion']
        prueba = [f for f in filas if f['particion'] == 'prueba']
        red = RedExperimental()
        with self.assertRaises(ValueError): red.entrenar(train, validacion=prueba)
        val = deepcopy(val); val[0]['id'] = train[0]['id']
        with self.assertRaises(ValueError): red.entrenar(train, validacion=val)
        val[0]['id'] = 1000; val[0]['entradas'] = train[0]['entradas'][:]
        with self.assertRaises(ValueError): red.entrenar(train, validacion=val)
        self.assertFalse(red.entrenada)

    def test_validacion_previa_y_controles_de_regularizacion(self):
        train = [f for f in datos_sinteticos() if f['particion'] == 'entrenamiento']
        red = RedExperimental(); antes = deepcopy(red.exportar()['pesos'])
        for kw in ({'l2': -1}, {'l2': float('nan')}, {'paciencia': 0}, {'paciencia': True}):
            with self.assertRaises(ValueError): red.entrenar(train, **kw)
        invalido = deepcopy(train); invalido[-1]['objetivos'] = [1, 0]
        with self.assertRaises(ValueError): red.entrenar(invalido)
        self.assertEqual(antes, red.exportar()['pesos'])

    def test_cli_genera_200_y_guarda_modelo_y_particiones(self):
        Path('.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir='.tmp') as carpeta:
            destino = Path(carpeta)/'modelo'
            r = subprocess.run([sys.executable, 'scripts/entrenar_red_sintetica.py', '--salida', str(destino)],
                               capture_output=True, text=True, timeout=30)
            self.assertEqual(r.returncode, 0, r.stderr)
            informe = json.loads((destino/'informe.json').read_text(encoding='utf-8'))
            modelo = json.loads((destino/'modelo.json').read_text(encoding='utf-8'))
            self.assertEqual(informe['registros_totales'], 200)
            self.assertEqual(informe['parametros'], 88)
            self.assertEqual([informe['evaluaciones'][k]['n'] for k in ('entrenamiento', 'validacion', 'prueba')], [140, 30, 30])
            self.assertEqual(modelo['arquitectura'], [9, 6, 4])
            self.assertEqual(modelo['entrenamiento'], informe['entrenamiento'])
            self.assertFalse(modelo['uso_en_personas'])
            self.assertEqual(hashlib.sha256((destino/'datos_sinteticos.csv').read_bytes()).hexdigest(), informe['datos_sha256'])
            with (destino/'datos_sinteticos.csv').open(encoding='utf-8', newline='') as f:
                self.assertEqual(len(list(csv.DictReader(f))), 200)
