"""5B.1: estados explícitos, historial y conflictos en bases aisladas."""
import sqlite3
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import test_app as fixtures
from sicose.db import obtener_conexion, inicializar_base_datos


class FisicasTestCase(unittest.TestCase):
    # Reutilizar fixtures existentes sin heredar las 87 pruebas del módulo anterior.
    for _nombre, _valor in vars(fixtures.AplicacionTestCase).items():
        if (_nombre.startswith('_') and not _nombre.startswith('__')) or _nombre in ('setUp', 'tearDown'):
            locals()[_nombre] = _valor

    def preparar(self):
        _, self.pid = self._preparar_notas_5b()
        self.ruta = f'/api/5b/periodos/{self.pid}/fisicas/FISICA_1'
        self.h = {'X-CSRFToken': self._csrf_token()}
        r = self.cliente.post(self.ruta, json={'fecha': '2026-03-01', 'motivo': 'Primera prueba común', 'anterior_id': None}, headers=self.h)
        self.assertEqual(r.status_code, 201, r.json)
        self.cid = r.json['id']

    def resultado(self, estado='NO_CUMPLIDA', nota='0', anterior=None, rid=None, fecha=None):
        body = {'periodo_id': self.pid, 'fuente': 'FISICA_1', 'nota_0_100': nota, 'motivo': 'Confirmación o corrección',
                'fisica': {'estado': estado, 'fecha_realizacion': fecha, 'programacion_id': self.cid, 'reprogramacion_id': rid}}
        if anterior:
            body['corregida_de_id'] = anterior
        return self.cliente.post('/api/5b/personas/3/notas', json=body, headers=self.h)

    def test_cero_reprogramacion_cumplimiento_historial_privacidad(self):
        self.preparar()
        antes = self.cliente.get(f'/api/evaluaciones/tabla?periodo_id={self.pid}').json['personas'][0]
        self.assertEqual(antes['resumen']['no_cumplidas'], 0)
        self.assertEqual(antes['evaluaciones'][0]['nota'], None)
        r = self.resultado(); self.assertEqual(r.status_code, 201, r.json); nid = r.json['id']
        r = self.cliente.post(self.ruta+'/personas/3', json={'fecha': '2026-10-01', 'motivo': 'Extraordinaria', 'anterior_id': None, 'programacion_id': self.cid}, headers=self.h)
        self.assertEqual(r.status_code, 201, r.json); rid = r.json['id']
        fila = self.cliente.get(f'/api/evaluaciones/tabla?periodo_id={self.pid}').json['personas'][0]
        self.assertEqual((fila['evaluaciones'][0]['estado'], fila['evaluaciones'][0]['nota'], fila['resumen']['no_cumplidas']), ('NO_CUMPLIDA','0.00',1))
        self.assertEqual(self.resultado('CUMPLIDA','88.25',nid,fecha='2026-10-01').status_code,409)
        r = self.resultado('CUMPLIDA','88.25',nid,rid,'2026-10-01');self.assertEqual(r.status_code,201,r.json)
        datos=self.cliente.get(f'/api/5b/personas/3?periodo_id={self.pid}').json
        self.assertEqual([n['nota_0_100'] for n in datos['notas']],['0.00','88.25'])
        self.assertEqual(datos['historial_fisicas'][0]['fecha_anterior'],'2026-03-01')
        self.assertEqual(datos['historial_fisicas'][0]['actor_id'],2)
        self._login('voluntario.demo','Clave voluntario 123!')
        propias=self.cliente.get(f'/api/evaluaciones/propias?periodo_id={self.pid}').json
        self.assertEqual(propias['evaluaciones'][0]['estado'],'FINALIZADA')
        for secreto in ('88.25','actor_id','motivo','nota_id','fecha_realizacion'):
            self.assertNotIn(secreto,str(propias))
        self.assertEqual(self.cliente.get(f'/api/5b/periodos/{self.pid}/fisicas').status_code,403)
        self.assertEqual(self.cliente.post(self.ruta,json={'fecha':'2026-03-02','motivo':'Intento','anterior_id':self.cid},headers={'X-CSRFToken':self._csrf_token()}).status_code,403)

    def test_calificacion_fisica_sin_observacion(self):
        self.preparar()
        body = {'periodo_id': self.pid, 'fuente': 'FISICA_1', 'nota_0_100': '0',
                'fisica': {'estado': 'NO_CUMPLIDA', 'fecha_realizacion': None,
                           'programacion_id': self.cid, 'reprogramacion_id': None}}
        r = self.cliente.post('/api/5b/personas/3/notas', json=body, headers=self.h)
        self.assertEqual(r.status_code, 201, r.json)

    def test_fechas_motivo_cero_y_revision(self):
        self.preparar()
        for valor in ('2027-01-01','2026-02-30','20260301',None):
            r=self.cliente.post(self.ruta,json={'fecha':valor,'motivo':'Corrección','anterior_id':self.cid},headers=self.h)
            self.assertEqual(r.status_code,400,r.json)
        for nota in ('1','100'):
            self.assertEqual(self.resultado(nota=nota).status_code,400)
        self.assertEqual(self.resultado(fecha='2026-03-01').status_code,400)
        self.assertEqual(self.resultado('CUMPLIDA','0',fecha='9999-01-01').status_code,400)
        with patch('sicose.fisicas.hoy', return_value=__import__('datetime').date(2026,2,1)):
            self.assertEqual(self.resultado().status_code,409)
        payload={'fecha':'2026-03-02','motivo':'Cambio común','anterior_id':self.cid}
        r=self.cliente.post(self.ruta,json=payload,headers=self.h);self.assertEqual(r.status_code,201)
        self.assertEqual(self.cliente.post(self.ruta,json=payload,headers=self.h).status_code,409)
        self.assertEqual(self.resultado().status_code,409)
        with self.app.app_context():
            c=obtener_conexion()
            with self.assertRaises(sqlite3.IntegrityError):c.execute('DELETE FROM programaciones_fisicas')
            c.rollback()

    def test_permisos_csrf_inactivo_deshabilitado_y_gestion(self):
        self.preparar()
        payload={'fecha':'2026-04-01','motivo':'Extraordinaria','anterior_id':None,'programacion_id':self.cid}
        ruta=self.ruta+'/personas/3'
        self.assertEqual(self.cliente.post(ruta,json=payload).status_code,400)
        self.assertEqual(self.cliente.post(self.ruta+'/personas/0',json=payload,headers=self.h).status_code,400)
        self.cliente.patch('/api/evaluaciones/personas/3/habilitacion',json={'periodo_id':self.pid,'clave':'FISICA_1','habilitada':False},headers=self.h)
        self.assertEqual(self.cliente.post(ruta,json=payload,headers=self.h).status_code,409)
        self.assertEqual(self.resultado().status_code,409)
        self.cliente.patch('/api/evaluaciones/personas/3/habilitacion',json={'periodo_id':self.pid,'clave':'FISICA_1','habilitada':True},headers=self.h)
        with self.app.app_context():
            c=obtener_conexion();c.execute("UPDATE usuarios SET estado='INACTIVO' WHERE id=3");c.commit()
        self.assertEqual(self.cliente.post(ruta,json=payload,headers=self.h).status_code,409)
        self.assertEqual(self.resultado().status_code,409)
        self.assertEqual(self.cliente.get(f'/api/5b/personas/3?periodo_id={self.pid}').status_code,200)
        self._login();self.h={'X-CSRFToken':self._csrf_token()}
        with self.app.app_context():
            c=obtener_conexion();c.execute("UPDATE periodos SET estado='CERRADO' WHERE id=?",(self.pid,));c.commit()
        self.assertEqual(self.cliente.post(self.ruta,json={'fecha':'2026-03-02','motivo':'Cambio','anterior_id':self.cid},headers=self.h).status_code,409)
        self.assertEqual(self.resultado().status_code,409)

    def test_programacion_individual_y_resultados_concurrentes(self):
        self.preparar()
        clientes=[]
        for _ in range(2):
            cli=self.app.test_client()
            with cli.session_transaction() as ses:
                ses['_user_id']='2';ses['sicose_password_version']=1
            clientes.append(cli)
        self.app.config['WTF_CSRF_ENABLED']=False
        for individual in (False, True):
            barrier=threading.Barrier(2)
            def guardar(cli):
                payload={'fecha':'2026-04-01','motivo':'Concurrencia','anterior_id':None if individual else self.cid}
                if individual:payload['programacion_id']=self.cid
                barrier.wait(timeout=5)
                return cli.post(self.ruta+('/personas/3' if individual else ''),json=payload).status_code
            with ThreadPoolExecutor(max_workers=2) as pool: estados=list(pool.map(guardar,clientes))
            self.assertEqual(sorted(estados),[201,409])
            if not individual:self.cid=self.cliente.get(f'/api/5b/periodos/{self.pid}/fisicas').json['pruebas']['FISICA_1']['comun']['id']
        rid=self.cliente.get(f'/api/5b/personas/3?periodo_id={self.pid}').json['fisicas']['FISICA_1']['individual']['id']
        barrier=threading.Barrier(2)
        def nota(cli):
            barrier.wait(timeout=5)
            return cli.post('/api/5b/personas/3/notas',json={'periodo_id':self.pid,'fuente':'FISICA_1','nota_0_100':'0','motivo':'No cumplida','fisica':{'estado':'NO_CUMPLIDA','fecha_realizacion':None,'programacion_id':self.cid,'reprogramacion_id':rid}}).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:estados=list(pool.map(nota,clientes))
        self.assertEqual(sorted(estados),[201,409])
        anterior=self.cliente.get(f'/api/5b/personas/3?periodo_id={self.pid}').json['notas'][-1]['id']
        barrier=threading.Barrier(2)
        def corregir(cli):
            barrier.wait(timeout=5)
            return cli.post('/api/5b/personas/3/notas',json={'periodo_id':self.pid,'fuente':'FISICA_1','nota_0_100':'70','corregida_de_id':anterior,'motivo':'Cumplimiento posterior','fisica':{'estado':'CUMPLIDA','fecha_realizacion':'2026-04-01','programacion_id':self.cid,'reprogramacion_id':rid}}).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:estados=list(pool.map(corregir,clientes))
        self.assertEqual(sorted(estados),[201,409])

    def test_dos_pruebas_cero_cumplido_correccion_y_fechas_independientes(self):
        self.preparar();self._login();self.h={'X-CSRFToken':self._csrf_token()}
        segunda=self.ruta.replace('FISICA_1','FISICA_2')
        r=self.cliente.post(segunda,json={'fecha':'2026-09-01','motivo':'Segunda común','anterior_id':None},headers=self.h)
        self.assertEqual(r.status_code,201,r.json)
        self.assertEqual(self.cliente.post(self.ruta.replace('FISICA_1','FISICA_3'),json={'fecha':'2026-09-01','motivo':'Tercera','anterior_id':None},headers=self.h).status_code,400)
        r=self.resultado('CUMPLIDA','0',fecha='2026-03-01');self.assertEqual(r.status_code,201,r.json)
        nid=r.json['id']
        fila=self.cliente.get(f'/api/evaluaciones/tabla?periodo_id={self.pid}').json['personas'][0]
        self.assertEqual(fila['evaluaciones'][0]['estado'],'FINALIZADA')
        self.assertEqual(fila['evaluaciones'][1]['estado'],'PENDIENTE')
        payload={'fecha':'2026-04-01','motivo':'Individual','anterior_id':None,'programacion_id':self.cid}
        r=self.cliente.post(self.ruta+'/personas/3',json=payload,headers=self.h);self.assertEqual(r.status_code,201)
        rid=r.json['id'];payload['anterior_id']=rid
        self.assertEqual(self.cliente.post(self.ruta+'/personas/3',json=payload,headers=self.h).json['id'],rid)
        r=self.cliente.post(self.ruta,json={'fecha':'2026-05-01','motivo':'Corrección común','anterior_id':self.cid},headers=self.h)
        self.assertEqual(r.status_code,201);self.cid=r.json['id']
        datos=self.cliente.get(f'/api/5b/personas/3?periodo_id={self.pid}').json
        self.assertEqual(datos['fisicas']['FISICA_1']['fecha_prevista'],'2026-04-01')
        self.assertEqual(datos['fisicas']['FISICA_2']['fecha_prevista'],'2026-09-01')
        self.assertEqual(len(datos['historial_fisicas']),1)
        self.assertEqual(self.resultado('CUMPLIDA','80',nid,rid,'2026-04-01').status_code,201)
        self.assertEqual(self.resultado('CUMPLIDA','90',nid,rid,'2026-04-01').status_code,409)

    def test_migracion_v18_preserva_e_idempotente(self):
        self.preparar()
        with self.app.app_context():
            c=obtener_conexion()
            tablas=[r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT IN ('programaciones_fisicas','reprogramaciones_fisicas','resultados_fisicos','app_meta')")]
            antes={t:[tuple(r) for r in c.execute(f'SELECT * FROM {t} ORDER BY rowid')] for t in tablas}
            c.execute('DROP TABLE resultados_fisicos');c.execute('DROP TABLE reprogramaciones_fisicas');c.execute('DROP TABLE programaciones_fisicas')
            c.execute("UPDATE app_meta SET valor='18' WHERE clave='schema_version'");c.commit()
            inicializar_base_datos();inicializar_base_datos()
            for t in tablas:self.assertEqual(antes[t],[tuple(r) for r in c.execute(f'SELECT * FROM {t} ORDER BY rowid')],t)
            self.assertEqual(c.execute("SELECT valor FROM app_meta WHERE clave='schema_version'").fetchone()[0],'32')
            self.assertEqual(c.execute('PRAGMA quick_check').fetchone()[0],'ok')
            self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(),[])
