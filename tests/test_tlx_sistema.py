"""NASA-TLX operativo y modelo fijado, sin datos reales."""
import csv
import hashlib
import json
from pathlib import Path
import unittest
import test_recomendaciones as fixtures
from sicose.db import obtener_conexion
from sicose.instrumentos_actuales import puntuar, firma
from sicose.recomendaciones import cargar_modelo, contexto, historial, MODELO_ANTERIOR_SHA
from sicose.modelo_anual import serializar


class TlxSistemaTest(unittest.TestCase):
    for nombre, valor in vars(fixtures.RecomendacionesTestCase).items():
        if (nombre.startswith('_') and not nombre.startswith('__')) or nombre in ('setUp','tearDown','preparar_anual','datos','nota','cierre','operacion_demo','puntuar_operacion','login_rol','revisar','habilitar','completar','generar','confirmar'):
            locals()[nombre]=valor

    def test_seis_dimensiones_rangos_pasos_y_sin_total(self):
        r=puntuar('NASATLX',[0,20,40,60,80,100])
        self.assertEqual([v['valor'] for v in r.values()],[0,20,40,60,80,100])
        self.assertEqual(r['rendimiento']['valor'],60)
        self.assertEqual(len(r),6)
        for v in (True,None,1,99,105,-5):
            with self.assertRaises(ValueError):puntuar('NASATLX',[v]*6)

    def test_simulacro_revisiones_privacidad_y_confirmacion(self):
        self.preparar_anual();self.revisar()
        ruta=self.url+'/pruebas/NASATLX'
        self.assertEqual(self.cliente.patch(ruta,json=dict(activa=True,revision=0),headers=self.h).status_code,409)
        body=dict(nombre='Simulacro común',fecha='2025-09-01',revision=0,realizado=True)
        self.assertEqual(self.cliente.put(self.url+'/simulacro-tlx',json={**body,'fecha':'2026-10-18'},headers=self.h).status_code,409)
        self.assertEqual(self.cliente.put(self.url+'/simulacro-tlx',json=body,headers=self.h).status_code,200)
        self.assertEqual(self.cliente.patch(ruta,json=dict(activa=True,revision=0),headers=self.h).status_code,200)
        self.login_rol('propia')
        d=self.cliente.get(ruta+'/propia').json;self.assertEqual(d['formulario']['simulacro']['nombre'],body['nombre'])
        payload=dict(revision=0,ciclo=0,respuestas=[50]*6)
        self.assertEqual(self.cliente.post(ruta+'/finalizar',json=payload,headers=self.h).status_code,409)
        self.assertEqual(self.cliente.put(ruta+'/propia',json={**payload,'respuestas':[None,0,None,None,None,None]},headers=self.h).status_code,200)
        self.login_rol('jefe')
        d=self.cliente.get(self.url+'/personas/3/pruebas').json['pruebas'][2]
        self.assertNotIn('subescalas',d);self.assertNotIn('respuestas',d)
        self.assertEqual(self.cliente.put(self.url+'/simulacro-tlx',json={**body,'revision':1},headers=self.h).status_code,409)
        self.login_rol('propia')
        self.assertEqual(self.cliente.post(ruta+'/finalizar',json={**payload,'revision':1,'confirmar_simulacro':True},headers=self.h).status_code,200)
        self.assertEqual(self.cliente.get(ruta+'/propia').json,dict(estado='Completada'))
        self.assertEqual(self.cliente.get(self.url+'/personas/3/pruebas').status_code,403)

    def test_faltante_tlx_bloquea_y_reinicio_conserva_fuentes(self):
        self.completar();rid=self.generar();self.assertEqual(self.confirmar(rid).status_code,200)
        d=self.cliente.get(self.rec).json
        self.assertEqual(len(d['entradas']),15);self.assertEqual(d['modelo']['semilla'],401)
        p=self.cliente.get(self.url+'/personas/3/pruebas').json['pruebas'][2]
        r=self.cliente.post(self.url+'/personas/3/pruebas/NASATLX/reiniciar',json=dict(password='Clave instructor 123!',intento_ref=p['intento_ref'],revision=p['revision'],confirmar=True),headers=self.h)
        self.assertEqual(r.status_code,200,r.json)
        d=self.cliente.get(self.rec).json;self.assertFalse(d['puede_generar']);self.assertEqual(d['historial'][0]['estado'],'Desactualizada')
        self.login_rol('propia');ruta=self.url+'/pruebas/NASATLX';d=self.cliente.get(ruta+'/propia').json
        self.assertEqual(d['respuestas'],[None]*6)
        r=self.cliente.post(ruta+'/finalizar',json=dict(revision=d['revision'],ciclo=d['ciclo'],respuestas=[100]*6,confirmar_simulacro=True),headers=self.h)
        self.assertEqual(r.status_code,200,r.json)
        with self.app.app_context():
            c=obtener_conexion();self.assertEqual(c.execute('SELECT simulacro_confirmado FROM tlx_reintentos_pruebas').fetchone()[0],1)
            self.assertEqual(c.execute('SELECT count(*) FROM intentos_pruebas').fetchone()[0],2)
            self.assertFalse(c.execute('PRAGMA foreign_key_check').fetchall())

    def test_inferencia_coincide_con_200_predicciones_guardadas(self):
        base=Path('output/comparacion_tlx_1564_15664_200_20261018')
        modelo=cargar_modelo()
        entradas=modelo.exportar()['entradas'];salidas=modelo.exportar()['salidas']
        with (base/'datos.csv').open(encoding='utf-8',newline='') as f:datos={int(r['id']):[float(r[k]) for k in entradas] for r in csv.DictReader(f)}
        with (base/'predicciones.csv').open(encoding='utf-8',newline='') as f:
            filas=[r for r in csv.DictReader(f) if r['arquitectura']=='15-6-4' and r['semilla']=='401']
        self.assertEqual(len(filas),200)
        for f in filas:
            self.assertEqual(modelo.adelante(datos[int(f['id'])])[-1],[float(f['activacion_'+k]) for k in salidas])

    def test_recomendacion_antigua_cerrada_se_conserva_y_reapertura_desactualiza(self):
        self.completar();self.login_rol('admin')
        with self.app.app_context():
            c=obtener_conexion();ctx=contexto(c,self.pid,3);f=ctx['fuentes']
            f['version_integracion']='ORIENTACION_V29';f['modelo_sha256']=MODELO_ANTERIOR_SHA;f['entradas']=f['entradas'][:9];del f['pruebas']['NASATLX']
            firma_fuentes=hashlib.sha256(serializar(f).encode()).hexdigest()
            c.execute('INSERT INTO recomendaciones(periodo_id,voluntario_id,firma_fuentes,fuentes_json,entradas_json,modelo_sha256,resultado_json,actor_id,actor_nombre,generada_en) VALUES (?,3,?,?,?,?,?,1,?,?)',(self.pid,firma_fuentes,serializar(f),serializar(dict(zip(list(ctx['entradas'])[:9],f['entradas']))),MODELO_ANTERIOR_SHA,serializar(dict(sugerencias=['Orientación histórica'],estado_modelo='PROPUESTA',aviso='Histórico')),'Responsable de prueba','2025-09-01'))
            rid=c.execute('SELECT max(id) FROM recomendaciones').fetchone()[0]
            c.execute('INSERT INTO confirmaciones_recomendacion VALUES (?,?,?,?,?)',(rid,'Confirmación histórica',1,'Responsable de prueba','2025-09-01'));c.commit()
        self.assertEqual(self.cierre().status_code,201)
        d=self.cliente.get(self.rec).json;self.assertEqual(d['historial'][0]['estado'],'Confirmada');self.assertEqual(len(d['entradas']),9)
        with self.app.app_context():
            c=obtener_conexion();cid=c.execute('SELECT max(id) FROM cierres_5b WHERE periodo_id=?',(self.pid,)).fetchone()[0]
        r=self.cliente.post(f'/api/admin/5b/periodos/{self.pid}/reabrir',json=dict(cierre_id=cid,motivo='Reapertura de prueba'),headers=self.h)
        self.assertEqual(r.status_code,200,r.json)
        self.assertEqual(self.cliente.get(self.rec).json['historial'][0]['estado'],'Desactualizada')
