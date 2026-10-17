"""Operaciones tipadas, baja segura y migración aditiva aislada."""
import sqlite3
import unittest
import test_modelo_anual as base
from sicose.db import obtener_conexion,inicializar_base_datos


class OperacionesV26TestCase(unittest.TestCase):
    for nombre,valor in vars(base.ModeloAnualTestCase).items():
        if not nombre.startswith('test_') and not nombre.startswith('__'):
            locals()[nombre]=valor

    def crear(self, **extra):
        body={'tipo_operativo':'Preventivo','estado_operacion':'Planificación','lugar':'Lugar DEMO',
              'fecha_inicio':'2025-09-01','fecha_fin':'2025-09-02','institucion_responsable':'Entidad DEMO'}
        return self.cliente.post('/api/operaciones',json={**body,**extra},headers=self.h)

    def preparar(self):
        self.preparar_anual()
        r=self.crear();self.assertEqual(r.status_code,201,r.json);self.oid=r.json['id'];self.ruta=f'/api/operaciones/{self.oid}'

    def eliminar(self,revision=1):
        return self.cliente.delete(self.ruta,json={'revision':revision,'motivo':'Eliminación DEMO'},headers=self.h)

    def test_catalogos_edicion_revision_y_restricciones_sql(self):
        self.preparar()
        for campo in ('tipo_operativo','estado_operacion'):
            for invalido in ('Otro','',None,123):self.assertEqual(self.crear(**{campo:invalido}).status_code,400)
        r=self.cliente.patch(self.ruta,json={'tipo_operativo':'Emergencia','estado_operacion':'En ejecución','revision':1},headers=self.h)
        self.assertEqual(r.status_code,200,r.json)
        o=self.cliente.get('/api/operaciones').json['operaciones'][0]
        self.assertEqual((o['tipo_operativo'],o['estado_operacion'],o['revision']),('Emergencia','En ejecución',2))
        with self.app.app_context():
            from sicose.reporte_individual import datos_individual
            self.assertEqual(datos_individual(obtener_conexion(),3)['operaciones'],[])
            self.assertEqual(self.cliente.post(self.ruta+'/participaciones',json={'voluntario_ids':[3]},headers=self.h).status_code,201)
            self.assertEqual(datos_individual(obtener_conexion(),3)['operaciones'][0]['tipo_evento'],'Emergencia')
        self.assertEqual(self.cliente.patch(self.ruta,json={'estado_operacion':'Finalizado','revision':1},headers=self.h).status_code,409)
        with self.app.app_context():
            c=obtener_conexion()
            with self.assertRaises(sqlite3.IntegrityError):c.execute("UPDATE operaciones SET estado_operacion='Otro' WHERE id=?",(self.oid,))
            c.rollback()

    def test_eliminacion_permanente_solo_sin_vinculos(self):
        self.preparar();self.assertEqual(self.eliminar(99).status_code,409)
        self.assertEqual(self.cliente.delete(self.ruta,json={'revision':1,'motivo':''},headers=self.h).status_code,400)
        r=self.eliminar();self.assertEqual(r.status_code,200,r.json);self.assertFalse(r.json['baja'])
        with self.app.app_context():self.assertIsNone(obtener_conexion().execute('SELECT 1 FROM operaciones WHERE id=?',(self.oid,)).fetchone())

    def test_baja_conserva_notas_acumulado_y_bloquea_nuevas_acciones(self):
        self.preparar()
        self.assertEqual(self.cliente.post(self.ruta+'/participaciones',json={'voluntario_ids':[3]},headers=self.h).status_code,201)
        self.assertEqual(self.puntuar_operacion(self.oid,60).status_code,201)
        antes=self.datos()['calculo']['academica']['valor']
        r=self.eliminar();self.assertEqual(r.status_code,200,r.json);self.assertTrue(r.json['baja'])
        self.assertEqual(self.cliente.get('/api/operaciones').json['operaciones'],[])
        historico=self.cliente.get('/api/operaciones?incluir_bajas=1').json['operaciones'][0]
        self.assertTrue(historico['baja']);self.assertEqual(len(historico['participantes']),1)
        self.assertEqual(self.datos()['calculo']['academica']['valor'],antes)
        self.assertEqual(self.cliente.patch(self.ruta,json={'lugar':'Cambio'},headers=self.h).status_code,409)
        self.assertEqual(self.cliente.post(self.ruta+'/participaciones',json={'voluntario_ids':[3]},headers=self.h).status_code,409)
        self.assertEqual(self.puntuar_operacion(self.oid,90).status_code,409)
        self.assertEqual(self.eliminar().status_code,409)
        with self.app.app_context():
            c=obtener_conexion()
            with self.assertRaises(sqlite3.IntegrityError):c.execute('DELETE FROM bajas_operacion')
            c.rollback()
        self._login('voluntario.demo','Clave voluntario 123!')
        propia=self.cliente.get('/api/operaciones').json['operaciones'][0]
        self.assertTrue(propia['baja']);self.assertEqual(len(propia['participantes']),1)

    def test_permisos_csrf_y_edicion_cerrada(self):
        self.preparar();self.assertEqual(self.cliente.delete(self.ruta,json={'revision':1,'motivo':'DEMO'}).status_code,400)
        self._login('voluntario.demo','Clave voluntario 123!');h={'X-CSRFToken':self._csrf_token()}
        self.assertEqual(self.cliente.delete(self.ruta,json={'revision':1,'motivo':'DEMO'},headers=h).status_code,403)
        self.assertEqual(self.cliente.patch(self.ruta,json={'estado_operacion':'Suspendido'},headers=h).status_code,403)
        self._login();self.h={'X-CSRFToken':self._csrf_token()}
        self.assertEqual(self.cliente.post(self.ruta+'/participaciones',json={'voluntario_ids':[3]},headers=self.h).status_code,201)
        self.assertEqual(self.puntuar_operacion(self.oid,20).status_code,201)
        self.assertEqual(self.cierre().status_code,201)
        self.assertEqual(self.cliente.patch(self.ruta,json={'estado_operacion':'Finalizado'},headers=self.h).status_code,409)
        self.assertEqual(self.eliminar().status_code,200)

    def test_migracion_v25_repetida_preserva_textos_y_vinculos(self):
        self.preparar()
        self.assertEqual(self.cliente.post(self.ruta+'/participaciones',json={'voluntario_ids':[3]},headers=self.h).status_code,201)
        with self.app.app_context():
            c=obtener_conexion()
            c.execute("UPDATE operaciones SET tipo_evento='Texto histórico sin inferir' WHERE id=?",(self.oid,))
            for campo in ('tipo_operativo','estado_operacion','revision'):c.execute(f'ALTER TABLE operaciones DROP COLUMN {campo}')
            c.execute('DROP TABLE bajas_operacion')
            c.execute("UPDATE app_meta SET valor='25' WHERE clave='schema_version'");c.commit()
            inicializar_base_datos();inicializar_base_datos()
            o=c.execute('SELECT * FROM operaciones WHERE id=?',(self.oid,)).fetchone()
            self.assertEqual(o['tipo_evento'],'Texto histórico sin inferir');self.assertIsNone(o['tipo_operativo']);self.assertIsNone(o['estado_operacion'])
            self.assertEqual(o['revision'],1)
            self.assertEqual(c.execute('SELECT COUNT(*) FROM participaciones_operacion WHERE operacion_id=?',(self.oid,)).fetchone()[0],1)
            self.assertEqual(c.execute("SELECT valor FROM app_meta WHERE clave='schema_version'").fetchone()[0],'29')
            self.assertEqual(c.execute('PRAGMA quick_check').fetchone()[0],'ok');self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(),[])
