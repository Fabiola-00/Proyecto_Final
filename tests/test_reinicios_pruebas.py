"""Reinicio individual autenticado, ciclos inmutables y efectos en recomendaciones."""
import json
import sqlite3
import unittest
from concurrent.futures import ThreadPoolExecutor
import test_recomendaciones as fixtures
from sicose.db import obtener_conexion, inicializar_base_datos
from sicose.reporte_individual import datos_individual


class ReiniciosPruebasTest(unittest.TestCase):
    for nombre, valor in vars(fixtures.RecomendacionesTestCase).items():
        if (nombre.startswith('_') and not nombre.startswith('__')) or nombre in ('setUp','tearDown','preparar_anual','datos','nota','cierre','operacion_demo','puntuar_operacion','login_rol','revisar','habilitar','completar','generar','confirmar'):
            locals()[nombre] = valor

    def estado_pruebas(self):
        return self.cliente.get(self.url+'/personas/3/pruebas').json

    def payload(self, clave='GSE', password='Clave instructor 123!'):
        p = next(p for p in self.estado_pruebas()['pruebas'] if p['clave']==clave)
        return dict(password=password, intento_ref=p['intento_ref'], revision=p['revision'], confirmar=True)

    def reset(self, clave='GSE', payload=None):
        return self.cliente.post(self.url+f'/personas/3/pruebas/{clave}/reiniciar', json=payload or self.payload(clave), headers=self.h)

    def completar_ciclo(self, clave='GSE', respuesta=3):
        self.login_rol('propia')
        ruta = self.url+f'/pruebas/{clave}'
        d = self.cliente.get(ruta+'/propia').json
        self.assertEqual(d['estado'], 'Pendiente')
        r = self.cliente.post(ruta+'/finalizar', json=dict(revision=d['revision'], ciclo=d['ciclo'], respuestas=[respuesta]*len(d['respuestas'])), headers=self.h)
        self.assertEqual(r.status_code,200,r.json)
        self.assertEqual(self.cliente.get(ruta+'/propia').json,dict(estado='Completada'))
        self.login_rol('jefe')

    def test_password_csrf_y_rol_sin_alterar_resultados(self):
        self.completar(); cuerpo = self.payload(password='incorrecta')
        ruta = self.url+'/personas/3/pruebas/GSE/reiniciar'
        self.assertEqual(self.cliente.post(ruta,json=cuerpo).status_code,400)
        self.assertEqual(self.reset(payload=cuerpo).status_code,403)
        # La contraseña del Administrador no autoriza al Jefe.
        self.assertEqual(self.reset(payload={**cuerpo,'password':'Clave demo segura 123!'}).status_code,403)
        self.assertEqual(self.estado_pruebas()['pruebas'][0]['estado'],'Completada')
        self.login_rol('propia')
        self.assertEqual(self.cliente.post(ruta,json=cuerpo,headers=self.h).status_code,403)
        with self.app.app_context():
            c=obtener_conexion()
            self.assertEqual(c.execute('SELECT count(*) FROM reinicios_pruebas').fetchone()[0],0)

    def test_reinicio_individual_historia_y_recomendacion_obsoleta(self):
        self.completar(); rid=self.generar(); self.assertEqual(self.confirmar(rid).status_code,200)
        anterior=self.estado_pruebas()['pruebas'][0]
        self.assertEqual(self.reset().status_code,200)
        d=self.estado_pruebas()
        self.assertEqual([p['estado'] for p in d['pruebas']],['Pendiente','Completada','Completada'])
        self.assertNotIn('respuestas',d['pruebas'][0]);self.assertNotIn('subescalas',d['pruebas'][0])
        self.assertEqual(d['historial'][0]['subescalas'],anterior['subescalas'])
        self.assertEqual(self.cliente.get(self.rec).json['historial'][0]['estado'],'Desactualizada')
        self.assertFalse(self.cliente.get(self.rec).json['puede_generar'])
        self.assertEqual(self.confirmar(rid).status_code,409)
        with self.app.app_context():
            c=obtener_conexion()
            self.assertIsNone(datos_individual(c,3)['recomendacion'])
            self.assertEqual(c.execute('SELECT respuestas_json FROM intentos_pruebas WHERE clave=\'GSE\'').fetchone()[0],json.dumps([3]*10,separators=(',',':')))
        self.login_rol('propia')
        f=self.cliente.get(self.url+'/pruebas/GSE/propia').json
        self.assertEqual(f['respuestas'],[None]*10)
        self.assertGreater(f['ciclo'],0)
        self.assertTrue(next(p for p in self.cliente.get('/api/pruebas/propias').json['pruebas'] if p['clave']=='GSE')['disponible'])
        self.login_rol('jefe');self.completar_ciclo()
        self.assertTrue(self.cliente.get(self.rec).json['puede_generar'])
        self.assertEqual(self.cliente.get(self.rec).json['historial'][0]['estado'],'Desactualizada')
        nuevo=self.generar();self.assertNotEqual(nuevo,rid)
        self.assertEqual(len(self.cliente.get(self.rec).json['historial']),2)

    def test_multiples_ciclos_sin_reutilizar_formularios_obsoletos(self):
        self.completar();viejo=self.payload()
        self.assertEqual(self.reset(payload=viejo).status_code,200)
        self.assertEqual(self.reset(payload=viejo).status_code,409)
        self.login_rol('propia');ruta=self.url+'/pruebas/GSE'
        d=self.cliente.get(ruta+'/propia').json
        obsoleto=dict(revision=d['revision'],ciclo=d['ciclo'],respuestas=[2]*10)
        self.assertEqual(self.cliente.put(ruta+'/propia',json={k:v for k,v in obsoleto.items() if k!='ciclo'},headers=self.h).status_code,409)
        self.login_rol('jefe');self.completar_ciclo(respuesta=2)
        self.assertEqual(self.reset().status_code,200)
        self.login_rol('propia')
        # Mismo número de revisión inicial, pero ciclo distinto.
        self.assertEqual(self.cliente.post(ruta+'/finalizar',json=obsoleto,headers=self.h).status_code,409)
        self.assertEqual(self.cliente.get(ruta+'/propia').json['respuestas'],[None]*10)
        self.login_rol('jefe');self.completar_ciclo(respuesta=4)
        self.assertEqual(self.estado_pruebas()['pruebas'][0]['subescalas']['autoeficacia']['valor'],40)
        self.assertEqual(len(self.estado_pruebas()['historial']),2)
        with self.app.app_context():
            c=obtener_conexion();inicializar_base_datos();inicializar_base_datos()
            self.assertEqual(c.execute('SELECT count(*) FROM reintentos_pruebas').fetchone()[0],2)
            self.assertFalse(c.execute('PRAGMA foreign_key_check').fetchall())
            for sql in ('DELETE FROM reinicios_pruebas','DELETE FROM reintentos_pruebas','UPDATE reintentos_pruebas SET respuestas_json=\'[]\'','UPDATE reinicios_pruebas SET actor_nombre=\'otro\''):
                with self.assertRaises(sqlite3.IntegrityError):c.execute(sql)
                c.rollback()

    def test_admin_cierre_inactivo_y_prueba_deshabilitada(self):
        self.completar(); self.login_rol('admin')
        cuerpo=self.payload(password='Clave demo segura 123!')
        self.assertEqual(self.cierre().status_code,201)
        self.assertEqual(self.reset(payload=cuerpo).status_code,409)
        with self.app.app_context():
            c=obtener_conexion();c.execute("UPDATE periodos SET estado='ACTIVO' WHERE id=?",(self.pid,));c.execute("UPDATE usuarios SET estado='INACTIVO' WHERE id=3");c.commit()
        self.assertEqual(self.reset(payload=cuerpo).status_code,409)
        with self.app.app_context():
            c=obtener_conexion();c.execute("UPDATE usuarios SET estado='ACTIVO' WHERE id=3");c.commit()
        a=self.cliente.get(self.url+'/pruebas').json['pruebas'][0]
        self.assertEqual(self.cliente.patch(self.url+'/pruebas/GSE',json=dict(activa=False,revision=a['revision']),headers=self.h).status_code,200)
        self.assertEqual(self.reset(payload=cuerpo).status_code,200)
        self.assertFalse(self.cliente.get(self.url+'/pruebas').json['pruebas'][0]['activa'])
        self.assertEqual(self.reset('MINIIPIP',self.payload('MINIIPIP',password='Clave demo segura 123!')).status_code,200)

    def test_concurrencia_un_solo_reinicio_y_sin_password_en_auditoria(self):
        self.completar();cuerpo=self.payload()
        with self.cliente.session_transaction() as s:sesion=dict(s)
        clientes=[self.app.test_client(),self.app.test_client()]
        for c in clientes:
            with c.session_transaction() as s:s.update(sesion)
        ruta=self.url+'/personas/3/pruebas/GSE/reiniciar'
        with ThreadPoolExecutor(max_workers=2) as pool:
            codigos=list(pool.map(lambda c:c.post(ruta,json=cuerpo,headers=self.h).status_code,clientes))
        self.assertEqual(sorted(codigos),[200,409])
        with self.app.app_context():
            c=obtener_conexion()
            self.assertEqual(c.execute('SELECT count(*) FROM reinicios_pruebas').fetchone()[0],1)
            self.assertNotIn(cuerpo['password'],str([tuple(r) for r in c.execute('SELECT * FROM auditoria')]))
