"""Ubicación atómica y retirada de participantes con evidencia conservada."""
import sqlite3
import unittest
import test_operaciones_v26 as base
from sicose.db import obtener_conexion,inicializar_base_datos


class OperacionesV27TestCase(unittest.TestCase):
    for nombre,valor in vars(base.OperacionesV26TestCase).items():
        if not nombre.startswith('test_') and not nombre.startswith('__'):
            locals()[nombre]=valor

    def datos_retiro(self):
        o=self.cliente.get('/api/operaciones?incluir_bajas=1').json['operaciones'][0]
        return {'motivo':'Retirada DEMO','participaciones':[{'voluntario_id':p['voluntario_id'],'revision':p['revision']} for p in o['participantes'] if not p['retirada']]}

    def vincular_y_calificar(self):
        self.preparar()
        self.assertEqual(self.cliente.post(self.ruta+'/participaciones',json={'voluntario_ids':[3]},headers=self.h).status_code,201)
        self.assertEqual(self.puntuar_operacion(self.oid,60).status_code,201)

    def test_departamento_zona_validaciones_y_edicion(self):
        self.preparar_anual()
        r=self.crear(departamento='La Paz',zona='Zona DEMO');self.assertEqual(r.status_code,201,r.json);oid=r.json['id']
        for extra in ({'departamento':'Otro','zona':'Centro'},{'departamento':'La Paz','zona':''},{'departamento':'La Paz','zona':123}):
            self.assertEqual(self.crear(**extra).status_code,400)
        with self.app.app_context():
            c=obtener_conexion();o=c.execute('SELECT * FROM operaciones WHERE id=?',(oid,)).fetchone()
            self.assertEqual((o['departamento'],o['zona']),('La Paz','Zona DEMO'))
            with self.assertRaises(sqlite3.IntegrityError):c.execute("UPDATE operaciones SET departamento='Otro' WHERE id=?",(oid,))
            c.rollback()
        r=self.cliente.patch(f'/api/operaciones/{oid}',json={'departamento':'Cochabamba','zona':'Nueva zona','revision':1},headers=self.h)
        self.assertEqual(r.status_code,200,r.json)
        o=self.cliente.get('/api/operaciones').json['operaciones'][0]
        self.assertEqual((o['departamento'],o['zona']),('Cochabamba','Nueva zona'))
        html=self.cliente.get('/gestion/operaciones').data.decode()
        self.assertIn('js/operaciones.js',html)
        self.assertNotIn('name="lugar"',html)

    def test_retirada_recalcula_sin_borrar_notas_y_bloquea_reasignar(self):
        self.vincular_y_calificar();self.assertEqual(self.datos()['calculo']['academica']['valor'],60)
        d=self.datos_retiro();self.assertEqual(d['participaciones'][0]['revision'],2)
        r=self.cliente.post(self.ruta+'/retirar-participantes',json=d,headers=self.h)
        self.assertEqual(r.status_code,200,r.json)
        actual=self.datos();self.assertEqual(actual['calculo']['academica']['valor'],0)
        self.assertEqual(len(actual['historial']['operaciones']),1)
        self.assertEqual(actual['historial']['operaciones'][0]['puntos_centesimas'],6000)
        self.assertTrue(actual['operaciones'][0]['retirada'])
        self.assertEqual(self.puntuar_operacion(self.oid,80).status_code,409)
        self.assertEqual(self.cliente.post(self.ruta+'/participaciones',json={'voluntario_ids':[3]},headers=self.h).status_code,409)
        self.assertEqual(self.cliente.post(self.ruta+'/retirar-participantes',json=d,headers=self.h).status_code,409)
        with self.app.app_context():
            c=obtener_conexion()
            with self.assertRaises(sqlite3.IntegrityError):c.execute('DELETE FROM retiros_operacion')
            c.rollback()

    def test_cierre_bloquea_retiro_hasta_reapertura(self):
        self.vincular_y_calificar();d=self.datos_retiro();self.assertEqual(self.cierre().status_code,201)
        self.assertEqual(self.cliente.post(self.ruta+'/retirar-participantes',json=d,headers=self.h).status_code,409)
        self._login();self.h={'X-CSRFToken':self._csrf_token()}
        cierre=self.cliente.get(self.url).json['cierres'][-1]['id']
        r=self.cliente.post(f'/api/admin/5b/periodos/{self.pid}/reabrir',json={'cierre_id':cierre,'motivo':'Reabrir DEMO'},headers=self.h)
        self.assertEqual(r.status_code,200,r.json)
        self.assertEqual(self.cliente.post(self.ruta+'/retirar-participantes',json=d,headers=self.h).status_code,200)
        self.assertEqual(self.datos()['calculo']['academica']['valor'],0)

    def test_retiro_atomico_revision_inactivo_csrf_y_roles(self):
        self.vincular_y_calificar();d=self.datos_retiro()
        self.assertEqual(self.cliente.post(self.ruta+'/retirar-participantes',json=d).status_code,400)
        alterado={'motivo':'DEMO','participaciones':d['participaciones']+[{'voluntario_id':99999,'revision':1}]}
        self.assertEqual(self.cliente.post(self.ruta+'/retirar-participantes',json=alterado,headers=self.h).status_code,409)
        self.assertEqual(self.datos()['calculo']['academica']['valor'],60)
        obsoleto={'motivo':'DEMO','participaciones':[{'voluntario_id':3,'revision':1}]}
        self.assertEqual(self.cliente.post(self.ruta+'/retirar-participantes',json=obsoleto,headers=self.h).status_code,409)
        with self.app.app_context():
            c=obtener_conexion();c.execute("UPDATE usuarios SET estado='INACTIVO' WHERE id=3");c.commit()
        self.assertEqual(self.cliente.post(self.ruta+'/retirar-participantes',json=d,headers=self.h).status_code,409)
        with self.app.app_context():
            c=obtener_conexion();c.execute("UPDATE usuarios SET estado='ACTIVO' WHERE id=3");c.commit()
        self._login('voluntario.demo','Clave voluntario 123!');h={'X-CSRFToken':self._csrf_token()}
        self.assertEqual(self.cliente.post(self.ruta+'/retirar-participantes',json=d,headers=h).status_code,403)

    def test_migracion_v26_sin_dividir_lugar_ni_perder_participantes(self):
        self.vincular_y_calificar()
        with self.app.app_context():
            c=obtener_conexion();antes=tuple(c.execute('SELECT * FROM notas_operacion_anual').fetchone())
            c.execute('DROP TABLE retiros_operacion')
            for campo in ('departamento','zona'):c.execute(f'ALTER TABLE operaciones DROP COLUMN {campo}')
            c.execute('ALTER TABLE participaciones_operacion DROP COLUMN revision')
            c.execute("UPDATE app_meta SET valor='26' WHERE clave='schema_version'");c.commit()
            inicializar_base_datos();inicializar_base_datos()
            o=c.execute('SELECT * FROM operaciones WHERE id=?',(self.oid,)).fetchone()
            self.assertIsNone(o['departamento']);self.assertIsNone(o['zona']);self.assertEqual(o['lugar'],'Lugar DEMO')
            self.assertEqual(antes,tuple(c.execute('SELECT * FROM notas_operacion_anual').fetchone()))
            self.assertEqual(c.execute('SELECT revision FROM participaciones_operacion').fetchone()[0],1)
            self.assertEqual(c.execute('PRAGMA quick_check').fetchone()[0],'ok');self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(),[])
