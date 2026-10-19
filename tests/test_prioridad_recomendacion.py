"""Selección relativa única, trazabilidad y conservación de reglas anteriores."""
import hashlib
import json
import unittest
import test_recomendaciones as fixtures
from sicose.db import obtener_conexion
from sicose.modelo_anual import serializar
from sicose.modelo_orientacion_tlx import SALIDAS, TEXTOS
from sicose.recomendaciones import seleccionar_prioridad, contexto, MODELO_SHA


class SeleccionPrioridadTest(unittest.TestCase):
    def test_siempre_una_linea_incluso_bajas_intermedias_y_empates(self):
        casos=[([.1,.2,.3,.05],2),([.45,.48,.46,.47],1),([0,0,0,0],0),
               ([1,1,1,1],0),([.8,.5,.8,.1],0),([.35,.65,.34,.1],1),
               ([.90000001,.9,.2,.3],0)]
        casos += [([.2 if i==ganador else .1 for i in range(4)],ganador) for ganador in range(4)]
        for valores,ganador in casos:
            with self.subTest(valores=valores):
                r=seleccionar_prioridad(valores)
                self.assertEqual(r['salida_prioritaria'],SALIDAS[ganador])
                self.assertEqual(r['sugerencias'],[TEXTOS[ganador]])
                self.assertEqual(r['criterio_seleccion'],'ARGMAX_V1')
                self.assertGreaterEqual(r['margen_activacion'],0)
                self.assertEqual(r['orden_activaciones'][0]['salida'],SALIDAS[ganador])
        r=seleccionar_prioridad([.1,.2,.2,.1])
        self.assertEqual(r['empates_maximos'],[SALIDAS[1],SALIDAS[2]])
        self.assertEqual(r['margen_activacion'],0)
        self.assertEqual(r['desempate'],'ORDEN_ORIGINAL_DE_SALIDAS')

    def test_salidas_invalidas_no_fabrican_orientacion(self):
        for valores in ([],[.1]*3,[.1]*5,[True,.1,.1,.1],[float('nan'),0,0,0],
                        [float('inf'),0,0,0],[-.1,0,0,0],[1.1,0,0,0],['.5',0,0,0]):
            with self.subTest(valores=valores),self.assertRaises(ValueError):
                seleccionar_prioridad(valores)


class HistorialPrioridadTest(unittest.TestCase):
    for nombre,valor in vars(fixtures.RecomendacionesTestCase).items():
        if (nombre.startswith('_') and not nombre.startswith('__')) or nombre in ('setUp','tearDown','preparar_anual','datos','nota','cierre','operacion_demo','puntuar_operacion','login_rol','revisar','habilitar','completar','generar','confirmar'):
            locals()[nombre]=valor

    def test_politica_anterior_se_conserva_cerrada_y_versiona_al_reabrir(self):
        self.completar();self.login_rol('admin')
        with self.app.app_context():
            c=obtener_conexion();ctx=contexto(c,self.pid,3);fuentes=ctx['fuentes']
            fuentes['version_integracion']='ORIENTACION_V31'
            firma=hashlib.sha256(serializar(fuentes).encode()).hexdigest()
            resultado=dict(estado_modelo='ABSTENCION',sugerencias=['Resultado indeterminado: requiere revisión humana.'],aviso='Regla histórica',umbrales=[.35,.65])
            c.execute('INSERT INTO recomendaciones(periodo_id,voluntario_id,firma_fuentes,fuentes_json,entradas_json,modelo_sha256,resultado_json,actor_id,actor_nombre,generada_en) VALUES (?,3,?,?,?,?,?,1,?,?)',
                (self.pid,firma,serializar(fuentes),serializar(ctx['entradas']),MODELO_SHA,serializar(resultado),'Revisor de prueba','2025-09-01'))
            rid=c.execute('SELECT max(id) FROM recomendaciones').fetchone()[0]
            c.execute('INSERT INTO confirmaciones_recomendacion VALUES (?,?,?,?,?)',(rid,'Constancia histórica',1,'Revisor de prueba','2025-09-01'));c.commit()
            antes=tuple(c.execute('SELECT * FROM recomendaciones WHERE id=?',(rid,)).fetchone())
        d=self.cliente.get(self.rec).json
        self.assertEqual(d['historial'][0]['estado'],'Desactualizada')
        self.assertEqual(d['historial'][0]['resultado'],resultado)
        self.assertEqual(self.cierre().status_code,201)
        d=self.cliente.get(self.rec).json
        self.assertEqual(d['historial'][0]['estado'],'Confirmada')
        self.assertEqual(d['modelo']['criterio_seleccion'],'UMBRALES_V1')
        self.assertFalse(d['puede_generar'])
        with self.app.app_context():
            c=obtener_conexion();cid=c.execute('SELECT max(id) FROM cierres_5b WHERE periodo_id=?',(self.pid,)).fetchone()[0]
        r=self.cliente.post(f'/api/admin/5b/periodos/{self.pid}/reabrir',json=dict(cierre_id=cid,motivo='Reapertura de prueba'),headers=self.h)
        self.assertEqual(r.status_code,200,r.json)
        self.assertEqual(self.cliente.get(self.rec).json['historial'][0]['estado'],'Desactualizada')
        nueva=self.generar();self.assertNotEqual(rid,nueva)
        self.assertEqual(self.generar(),nueva)
        d=self.cliente.get(self.rec).json
        self.assertEqual(d['historial'][0]['resultado']['criterio_seleccion'],'ARGMAX_V1')
        self.assertEqual(len(d['historial'][0]['resultado']['sugerencias']),1)
        self.assertEqual(d['historial'][1]['resultado'],resultado)
        with self.app.app_context():
            c=obtener_conexion()
            self.assertEqual(antes,tuple(c.execute('SELECT * FROM recomendaciones WHERE id=?',(rid,)).fetchone()))
