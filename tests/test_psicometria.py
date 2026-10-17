"""Flujo aislado con reactivos ficticios, sin suplantar revisión profesional real."""
import hashlib
import itertools
import json
import sqlite3
import unittest
import test_modelo_anual as anual
from sicose.db import obtener_conexion, inicializar_base_datos
from sicose.modelo_anual import serializar
from sicose.psicometria_puntuacion import CATALOGO, puntuar
from sicose.red_experimental import datos_sinteticos, normalizar, RedExperimental, SALIDAS


class PsicometriaTestCase(unittest.TestCase):
    for nombre in ('setUp', 'tearDown', '_crear_usuario', '_login', '_csrf_token', 'preparar_anual', 'datos'):
        locals()[nombre] = getattr(anual.ModeloAnualTestCase, nombre)

    def preparar(self, revisada=True):
        self.preparar_anual()
        self.psico = self.url+'/psicometria'
        if revisada:
            self.app.config['PSICOMETRIA_REVISIONES'] = {}
            for k, f in CATALOGO.items():
                form = {'version': f['version'], 'algoritmo': f['algoritmo'], 'instrucciones': 'SIMULACIÓN TÉCNICA, NO INSTRUMENTO.',
                        'items': [{'texto': f'Ítem ficticio {i+1}', 'opciones': [f'Opción ficticia {j}' for j in range(f['maximo_respuesta']+1)]} for i in range(f['cantidad'])]}
                revision = {c: 'DEMO AISLADA SIN VALIDEZ PROFESIONAL' for c in (
                    'profesional', 'referencia_profesional', 'aprobacion_institucional', 'fecha', 'retencion',
                    'protocolo_confidencialidad', 'aplicabilidad_19_items_cbi')}
                revision.update(firma_formulario=hashlib.sha256(serializar(form).encode()).hexdigest(), devolucion_instructor='SOLO_ESTADO')
                self.app.config['PSICOMETRIA_REVISIONES'][k] = {'formulario': form, 'revision': revision}

    def activar(self, clave='DASS21', activa=True, revision=0):
        return self.cliente.patch(self.psico+'/'+clave, json={'activa': activa, 'revision': revision}, headers=self.h)

    def instructor(self):
        self._login('voluntario.demo', 'Clave voluntario 123!')
        self.h = {'X-CSRFToken': self._csrf_token()}

    def test_bloqueo_oficial_y_firma_revisada(self):
        self.preparar(False)
        self.assertEqual(self.activar().status_code, 409)
        self.assertFalse(self.cliente.get(self.psico).json['pruebas'][0]['revisada'])
        self.app.config['PSICOMETRIA_REVISIONES'] = {'DASS21': {'formulario': {}, 'revision': {}}}
        self.assertEqual(self.activar().status_code, 409)

    def test_activaciones_independientes_permisos_csrf_y_concurrencia(self):
        self.preparar()
        self.assertEqual(self.cliente.patch(self.psico+'/DASS21', json={'activa': True, 'revision': 0}).status_code, 400)
        self.assertEqual(self.activar().status_code, 200)
        self.assertEqual(self.activar(activa=False).status_code, 409)
        d = self.cliente.get(self.psico).json['pruebas']
        self.assertEqual([p['activa'] for p in d], [True, False])
        self.instructor()
        self.assertEqual(self.activar('CBI').status_code, 403)
        self.assertEqual(len(self.cliente.get('/api/psicometria/propia').json['pruebas']), 1)
        self.assertEqual(self.cliente.get('/api/psicometria/propia?usuario_id=2').status_code, 409)

    def test_guardar_reanudar_finalizar_y_privacidad(self):
        self.preparar(); self.assertEqual(self.activar().status_code, 200); self.instructor()
        base = self.psico+'/DASS21'
        self.assertEqual(self.cliente.get(base+'/propia').json['revision'], 0)
        respuestas = [None]*21; respuestas[0] = 2
        self.assertEqual(self.cliente.put(base+'/propia', json={'revision': 0, 'respuestas': respuestas}, headers=self.h).status_code, 200)
        self.assertEqual(self.cliente.get(base+'/propia').json['respuestas'], respuestas)
        self.assertEqual(self.cliente.put(base+'/propia', json={'revision': 0, 'respuestas': respuestas}, headers=self.h).status_code, 409)
        self.assertEqual(self.cliente.post(base+'/finalizar', json={'revision': 1, 'respuestas': respuestas}, headers=self.h).status_code, 409)
        d = {'revision': 1, 'respuestas': [1]*21}
        self.assertEqual(self.cliente.post(base+'/finalizar', json={**d, 'puntaje': 0}, headers=self.h).status_code, 409)
        r = self.cliente.post(base+'/finalizar', json=d, headers=self.h)
        self.assertEqual(r.status_code, 200, r.json)
        self.assertEqual(set(r.json), {'estado', 'revision'})
        self.assertEqual(r.headers['Cache-Control'], 'private, no-store')
        self.assertEqual(self.cliente.get(base+'/propia').json, {'estado': 'Completada'})
        self.assertEqual(self.cliente.post(base+'/finalizar', json={'revision': 2, 'respuestas': [0]*21}, headers=self.h).status_code, 409)
        url = self.url+'/personas/3/psicometria'
        self.assertEqual(self.cliente.get(url).status_code, 403)
        self._login('instructor.demo', 'Clave instructor 123!')
        d = self.cliente.get(url).json['pruebas'][0]
        self.assertEqual(d['respuestas'], [1]*21)
        self.assertEqual(d['subescalas']['depresion']['valor'], 14)
        self._login()
        self.assertEqual(self.cliente.get(url).status_code, 200)
        with self.app.app_context():
            c = obtener_conexion()
            with self.assertRaises(sqlite3.IntegrityError): c.execute('DELETE FROM intentos_psicometria')
            c.rollback()
            with self.assertRaises(sqlite3.IntegrityError): c.execute("UPDATE intentos_psicometria SET respuestas_json='[]'")
            c.rollback()
            self.assertFalse(any('respuestas' in r[0] for r in c.execute("SELECT accion FROM auditoria WHERE accion LIKE 'PSICOMETRIA%'").fetchall()))

    def test_desactivar_conserva_borrador_y_bloquea_respuestas(self):
        self.preparar(); self.activar(); self.instructor()
        base = self.psico+'/DASS21'
        self.cliente.put(base+'/propia', json={'revision': 0, 'respuestas': [1]*21}, headers=self.h)
        self._login('instructor.demo', 'Clave instructor 123!'); self.h = {'X-CSRFToken': self._csrf_token()}
        self.assertNotIn('respuestas', self.cliente.get(self.url+'/personas/3/psicometria').json['pruebas'][0])
        self.assertEqual(self.activar(activa=False, revision=1).status_code, 200)
        self.instructor(); self.assertEqual(self.cliente.get(base+'/propia').status_code, 409)
        self._login('instructor.demo', 'Clave instructor 123!'); self.h = {'X-CSRFToken': self._csrf_token()}
        self.activar(revision=2); self.instructor()
        self.assertEqual(self.cliente.get(base+'/propia').json['respuestas'], [1]*21)

    def test_cierre_inactivo_version_y_aislamiento(self):
        self.preparar(); self.activar(); self.instructor()
        base = self.psico+'/DASS21'
        self.assertEqual(self.cliente.get(base+'/propia?usuario_id=2').status_code, 409)
        self.assertEqual(self.cliente.get(self.psico+'/CBI/propia').status_code, 409)
        self.cliente.put(base+'/propia', json={'revision': 0, 'respuestas': [1]*21}, headers=self.h)
        self.app.config['PSICOMETRIA_REVISIONES']['DASS21']['formulario']['items'][0]['texto'] = 'CAMBIO'
        self.assertEqual(self.cliente.get(base+'/propia').status_code, 409)
        with self.app.app_context():
            c = obtener_conexion(); c.execute("UPDATE periodos SET estado='CERRADO' WHERE id=?", (self.pid,)); c.commit()
        self.assertEqual(self.cliente.post(base+'/finalizar', json={'revision': 1, 'respuestas': [1]*21}, headers=self.h).status_code, 409)

    def test_cbi_finalizada_y_migracion_idempotente(self):
        self.preparar(); self.assertEqual(self.activar('CBI').status_code, 200); self.instructor()
        r = self.cliente.post(self.psico+'/CBI/finalizar', json={'revision': 0, 'respuestas': [2]*19}, headers=self.h)
        self.assertEqual(r.status_code, 200, r.json)
        with self.app.app_context():
            c = obtener_conexion(); antes = [tuple(r) for r in c.execute('SELECT * FROM intentos_psicometria')]
            inicializar_base_datos(); inicializar_base_datos()
            self.assertEqual(antes, [tuple(r) for r in c.execute('SELECT * FROM intentos_psicometria')])
            self.assertEqual(c.execute('PRAGMA quick_check').fetchone()[0], 'ok')
            self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(), [])


class PuntuacionYRedTestCase(unittest.TestCase):
    def test_claves_dass_extremos_y_por_item(self):
        for k in ('depresion', 'ansiedad', 'estres'):
            self.assertEqual(puntuar('DASS21', [3]*21)[k]['valor'], 42)
            self.assertEqual(puntuar('DASS21', [0]*21)[k]['valor'], 0)
        self.assertEqual(puntuar('DASS21', [1]+[0]*20)['estres']['valor'], 2)
        for valores in ([True]*21, [4]*21, [None]*21, [1]*20):
            with self.assertRaises(ValueError): puntuar('DASS21', valores)

    def test_cbi_inversion_y_medias_exactas(self):
        a = [0]*19; a[12] = 4
        self.assertEqual([v['valor'] for v in puntuar('CBI', a).values()], [0, 0, 0])
        b = [4]*19; b[12] = 0
        self.assertEqual([v['valor'] for v in puntuar('CBI', b).values()], [100, 100, 100])
        self.assertEqual([v['valor'] for v in puntuar('CBI', [2]*19).values()], [50, 50, 50])

    def test_dataset_disjunto_reproducible_y_cobertura(self):
        filas = datos_sinteticos(20)
        self.assertEqual(filas, datos_sinteticos(20))
        self.assertEqual({tuple(f['objetivos']) for f in filas}, set(itertools.product((0, 1), repeat=4)))
        self.assertEqual(len({tuple(f['entradas']) for f in filas}), len(filas))
        self.assertEqual({f['origen'] for f in filas}, {'SINTETICO'})
        self.assertEqual(len(SALIDAS), 4)

    def test_entrenamiento_no_admite_test_y_rechaza_datos_faltantes(self):
        r = RedExperimental()
        with self.assertRaises(ValueError): r.simular([0]*9)
        with self.assertRaises(ValueError): r.entrenar(datos_sinteticos(20))
        for valores in ([None]*9, [0]*8, [float('nan')]*9, [float('inf')]*9, [True]*9, [-1]*9):
            with self.assertRaises(ValueError): normalizar(valores)
        filas = [f for f in datos_sinteticos(20) if f['particion'] == 'entrenamiento']
        antes = serializar(r.exportar())
        r.entrenar(filas, epocas=2)
        self.assertNotEqual(antes, serializar(r.exportar()))
        self.assertFalse(r.simular([0]*9)['uso_en_personas'])
