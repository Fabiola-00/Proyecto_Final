"""Comprobación numérica de backprop y comparación reproducible sin cambiar la base."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from sicose.red_experimental import RedDosCapas, datos_sinteticos


class ComparacionRedesTestCase(unittest.TestCase):
    def test_gradientes_numericos_de_los_136_parametros_con_l2(self):
        self._comprobar_gradientes(RedDosCapas(), [9, 8, 4, 4], 136)

    def test_gradientes_numericos_de_los_108_parametros_con_l2(self):
        self._comprobar_gradientes(RedDosCapas(ocultas=(6, 4)), [9, 6, 4, 4], 108)

    def _comprobar_gradientes(self, red, arquitectura, cantidad):
        f = {'entradas': [73, 61, 46, 10, 24, 8, 25, 50, 75], 'objetivos': [0, 0, 1, 1]}
        antes = deepcopy(red._pesos())
        self.assertEqual(red.exportar()['arquitectura'], arquitectura)
        self.assertEqual(sum(sum(len(fila) for fila in v) if k.startswith('w') else len(v) for k, v in antes.items()), cantidad)
        tasa, l2, eps = .005, .001, 1e-6
        red._paso(f, tasa, l2)
        despues = deepcopy(red._pesos())
        red._restaurar(deepcopy(antes))

        def objetivo():
            return red.perdida([f]) + l2/2 * sum(w*w for k, matriz in red._pesos().items()
                                                if k.startswith('w') for fila in matriz for w in fila)

        revisados = 0
        for k, valor in antes.items():
            indices = [(i, j) for i, fila in enumerate(valor) for j in range(len(fila))] if k.startswith('w') else [(i, None) for i in range(len(valor))]
            for i, j in indices:
                parametros = getattr(red, k)[i] if j is not None else getattr(red, k)
                pos = j if j is not None else i
                v = parametros[pos]
                parametros[pos] = v+eps; mas = objetivo()
                parametros[pos] = v-eps; menos = objetivo()
                parametros[pos] = v
                actualizado = despues[k][i][j] if j is not None else despues[k][i]
                analitico = (v-actualizado)/tasa
                self.assertAlmostEqual(analitico, (mas-menos)/(2*eps), delta=2e-6, msg=f'{k}:{i}:{j}')
                revisados += 1
        self.assertEqual(revisados, cantidad)

    def test_dos_capas_restaura_todas_las_matrices_por_validacion(self):
        self._comprobar_restauracion((8, 4))

    def test_restauracion_de_la_alternativa_9644(self):
        self._comprobar_restauracion((6, 4))

    def _comprobar_restauracion(self, ocultas):
        filas = datos_sinteticos()
        train = [f for f in filas if f['particion'] == 'entrenamiento']
        val = [f for f in filas if f['particion'] == 'validacion']
        red = RedDosCapas(ocultas=ocultas)
        with self.assertRaises(ValueError): red.simular(val[0]['entradas'])
        red.entrenar(train, validacion=val, epocas=100, paciencia=5, l2=.001)
        referencia = RedDosCapas(ocultas=ocultas)
        referencia.entrenar(train, epocas=red.entrenamiento['epoca_elegida'], l2=.001)
        self.assertEqual(red.exportar()['pesos'], referencia.exportar()['pesos'])
        self.assertEqual(red.perdida(val), referencia.perdida(val))
        self.assertFalse(red.simular(val[0]['entradas'])['uso_en_personas'])

    def test_dos_capas_rechaza_prueba_y_solapamientos_para_seleccion(self):
        filas = datos_sinteticos()
        train = [f for f in filas if f['particion'] == 'entrenamiento']
        prueba = [f for f in filas if f['particion'] == 'prueba']
        red = RedDosCapas()
        antes = deepcopy(red.exportar())
        with self.assertRaises(ValueError): red.entrenar(train, validacion=prueba)
        val = deepcopy(prueba); val[0]['id'] = train[0]['id']
        for f in val: f['particion'] = 'validacion'
        with self.assertRaises(ValueError): red.entrenar(train, validacion=val)
        self.assertEqual(red.exportar(), antes)

    def test_comparador_reproduce_base_y_conserva_csv_pesos_originales(self):
        self._comprobar_comparador('9-8-4-4', 136)

    def test_comparador_9644_conserva_original_y_selecciona_por_validacion(self):
        self._comprobar_comparador('9-6-4-4', 108)

    def test_rechaza_topologias_ocultas_invalidas(self):
        for ocultas in ((0, 4), (6,), (6, 4, 4), (True, 4), (6, -1), '6,4'):
            with self.assertRaises(ValueError): RedDosCapas(ocultas=ocultas)

    def _comprobar_comparador(self, alternativa, cantidad):
        base = Path('output/modelo_sintetico_200_20261017')
        huellas = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                   (base/'datos_sinteticos.csv', base/'modelo.json', base/'informe.json')}
        Path('.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir='.tmp') as carpeta:
            destino = Path(carpeta)/'comparacion'
            r = subprocess.run([sys.executable, 'scripts/comparar_redes_sinteticas.py', '--salida', str(destino),
                                '--semillas', '31415', '7', '--alternativa', alternativa], capture_output=True, text=True, timeout=60)
            self.assertEqual(r.returncode, 0, r.stderr)
            informe = json.loads((destino/'comparacion.json').read_text(encoding='utf-8'))
            self.assertEqual(len(informe['ejecuciones']), 4)
            self.assertEqual(informe['resumen']['9-6-4']['parametros'], 88)
            self.assertEqual(informe['resumen'][alternativa]['parametros'], cantidad)
            self.assertEqual(informe['protocolo']['arquitecturas'], ['9-6-4', alternativa])
            self.assertEqual(informe['protocolo']['particiones'], {'entrenamiento': 140, 'validacion': 30, 'prueba': 30})
            self.assertEqual(hashlib.sha256((destino/'datos_sinteticos.csv').read_bytes()).hexdigest(), huellas[base/'datos_sinteticos.csv'])
            self.assertFalse(informe['modelo_base_sustituido'])
            esperado = min(informe['resumen'], key=lambda k: informe['resumen'][k]['evaluaciones']['validacion']['perdida']['media'])
            self.assertEqual(informe['favorecida_por_criterio_principal'], esperado)
        for p, huella in huellas.items():
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), huella)
