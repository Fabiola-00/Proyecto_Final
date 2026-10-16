"""Modelo v3: intervalos, ceros oficiales, operaciones y cinco entradas sin IA."""
import unittest
import re
from concurrent.futures import ThreadPoolExecutor
import test_app as fixtures
from sicose.db import obtener_conexion,inicializar_base_datos

class ModeloAnualTestCase(unittest.TestCase):
    for nombre,valor in vars(fixtures.AplicacionTestCase).items():
        if (nombre.startswith('_') and not nombre.startswith('__')) or nombre in ('setUp','tearDown'):
            locals()[nombre]=valor

    def preparar_anual(self):
        with self.app.app_context():
            c=obtener_conexion();c.execute('INSERT INTO voluntarios(usuario_id) VALUES (3)');c.commit()
        self._login('instructor.demo','Clave instructor 123!');self.h={'X-CSRFToken':self._csrf_token()}
        self.base='/api/modelo-anual/gestiones'
        r=self.cliente.post(self.base,json={'nombre':'Gestión propia DEMO','fecha_inicio':'2025-08-15','fecha_fin':'2025-11-30'},headers=self.h)
        self.assertEqual(r.status_code,201,r.json);self.pid=r.json['id'];self.url=f'{self.base}/{self.pid}'
        self.assertEqual(self.cliente.post(self.url+'/iniciar',json={'revision':1,'motivo':'Inicio explícito DEMO'},headers=self.h).status_code,201)
        return self.datos()

    def datos(self):
        r=self.cliente.get(self.url+'/personas/3');self.assertEqual(r.status_code,200,r.json);return r.json

    def nota(self,fuente,valor,ev=None,anterior=None):
        anterior=self.datos()['calculo']['fuentes'][fuente]['id'] if anterior is None else anterior
        return self.cliente.post(self.url+'/personas/3',json={'fuente':fuente,'nota':valor,'anterior_id':anterior,'motivo':'Corrección o registro DEMO','evidencia':ev or {}},headers=self.h)

    def operacion_demo(self,fecha='2025-09-01'):
        r=self.cliente.post('/api/operaciones',json={'tipo_evento':'Rescate DEMO','lugar':'Lugar DEMO','fecha_inicio':fecha,'fecha_fin':fecha,'institucion_responsable':'Entidad DEMO'},headers=self.h)
        self.assertEqual(r.status_code,201,r.json);oid=r.json['id']
        self.assertEqual(self.cliente.post(f'/api/operaciones/{oid}/participaciones',json={'voluntario_ids':[3]},headers=self.h).status_code,201)
        return oid

    def puntuar_operacion(self,oid,valor,anterior=None):
        return self.cliente.post(self.url+f'/personas/3/operaciones/{oid}',json={'nota':valor,'anterior_id':anterior,'motivo':'Valoración DEMO'},headers=self.h)

    def cierre(self):
        vista=self.cliente.get(f'/api/5b/periodos/{self.pid}/cierre-previo');self.assertEqual(vista.status_code,200,vista.json);v=vista.json
        return self.cliente.post(f'/api/admin/5b/periodos/{self.pid}/cerrar',json={'motivo':'Cierre DEMO','firma_fuentes':v['firma_fuentes'],'cierre_anterior_id':v['cierre_anterior_id'],'confirmar_incompletos':True},headers=self.h)

    def test_ceros_oficiales_cinco_entradas_e_inscripcion_idempotente(self):
        d=self.preparar_anual();c=d['calculo']
        self.assertIn('Ceros iniciales oficiales',self.cliente.get('/panel/jefe-personal').data.decode())
        self.assertEqual(len(c['entradas']),5);self.assertEqual([e['valor'] for e in c['entradas']],['0','0','0.00',None,None])
        self.assertEqual({n['origen'] for n in d['historial']['notas']},{'CERO_INICIAL'});self.assertEqual(len(d['historial']['notas']),5)
        self.assertEqual(c['academica']['estado_operaciones'],'PENDIENTE');self.assertEqual(c['academica']['valor'],0)
        self.assertIsNone(c['resultado_conjunto']);self.assertFalse(c['modelo']['listo_para_inferencia'])
        r=self.cliente.post(self.url+'/inscribir',json={'revision':2,'motivo':'Comprobación DEMO'},headers=self.h);self.assertEqual(r.status_code,201,r.json);self.assertEqual(r.json['inscritos'],0)
        self.assertEqual(len(self.datos()['historial']['notas']),5)
        for fuente in ('PSICOMETRICA_1','ACADEMICA'):
            self.assertEqual(self.cliente.post(self.url+'/personas/3',json={'fuente':fuente,'nota':80,'anterior_id':1,'motivo':'DEMO','evidencia':{}},headers=self.h).status_code,409)

    def test_academica_suma_cursos_operaciones_tope_rango_y_correccion(self):
        self.preparar_anual();oid=self.operacion_demo();self.assertEqual(self.puntuar_operacion(oid,'60.25').status_code,201)
        curso={'nombre':'Curso dentro DEMO','tipo':'Taller','entidad':'Entidad DEMO','fecha_inicio':'2025-08-01','fecha_fin':'2025-09-01','puntaje':70}
        r=self.cliente.post('/api/cursos',json=curso,headers=self.h);self.assertEqual(r.status_code,201,r.json);cid=r.json['id']
        self.assertEqual(self.cliente.post(f'/api/cursos/{cid}/participantes',json={'voluntario_ids':[3]},headers=self.h).status_code,201)
        part=self.cliente.get(f'/api/cursos/{cid}/participantes').json['participantes'][0]
        self.partid=part['id']
        r=self.cliente.patch(f'/api/formacion/participaciones/{self.partid}',json={'revision':1,'estado':'Finalizado','puntaje':70,'fecha_finalizacion':'2025-09-02','motivo':'Finalización DEMO'},headers=self.h);self.assertEqual(r.status_code,200,r.json)
        a=self.datos()['calculo']['academica'];self.assertEqual(a['valor'],100);self.assertEqual(a['puntos_sin_tope'],130.25);self.assertEqual(len(a['detalle']),1)
        anterior=self.datos()['historial']['operaciones'][-1]['id']
        self.assertEqual(self.puntuar_operacion(oid,0).status_code,409)
        self.assertEqual(self.puntuar_operacion(oid,0,anterior).status_code,201);self.assertEqual(self.datos()['calculo']['academica']['valor'],70)
        fuera=self.operacion_demo('2025-12-01');self.assertEqual(self.puntuar_operacion(fuera,100).status_code,409)
        for v in (True,-1,101,'0.001'):
            self.assertEqual(self.puntuar_operacion(oid,v,anterior).status_code,409)

    def test_fisica_no_cumplida_reprogramacion_y_correccion_exacta(self):
        self.preparar_anual();ruta=f'/api/5b/periodos/{self.pid}/fisicas/FISICA_1'
        r=self.cliente.post(ruta,json={'fecha':'2025-09-01','anterior_id':None,'motivo':'Común DEMO'},headers=self.h);self.assertEqual(r.status_code,201,r.json)
        agenda=self.datos()['fisicas']['FISICA_1'];ev={'estado':'NO_CUMPLIDA','fecha_realizacion':None,'programacion_id':agenda['comun']['id'],'reprogramacion_id':None}
        self.assertEqual(self.nota('FISICA_1',0,ev).status_code,201)
        r=self.cliente.post(ruta+'/personas/3',json={'fecha':'2025-10-01','anterior_id':None,'programacion_id':agenda['comun']['id'],'motivo':'Extraordinaria DEMO'},headers=self.h);self.assertEqual(r.status_code,201,r.json)
        d=self.datos();self.assertEqual(d['calculo']['fuentes']['FISICA_1']['origen'],'NO_CUMPLIDA')
        self.assertEqual(self.nota('FISICA_1',80,ev).status_code,409)
        ev.update(estado='CUMPLIDA',fecha_realizacion='2025-10-01',reprogramacion_id=d['fisicas']['FISICA_1']['individual']['id'])
        self.assertEqual(self.nota('FISICA_1','80.01',ev).status_code,201)
        self.assertEqual(self.datos()['calculo']['fisica'],'40.005')
        self.assertEqual(len(self.datos()['historial']['notas']),7)

    def test_cierre_jefe_snapshot_bloqueos_y_reapertura_admin(self):
        self.preparar_anual();oid=self.operacion_demo();self.assertEqual(self.puntuar_operacion(oid,25).status_code,201)
        self.assertEqual(self.nota('DESEMPENO_JEFE',80).status_code,201)
        r=self.cierre();self.assertEqual(r.status_code,201,r.json);cid=r.json['cierre_id']
        d=self.datos();self.assertFalse(d['calculo']['provisional']);self.assertEqual(d['calculo']['academica']['valor'],25)
        self.assertEqual(self.nota('DESEMPENO_JEFE',90).status_code,409);self.assertEqual(self.puntuar_operacion(oid,100).status_code,409)
        self.assertEqual(self.cliente.patch(f'/api/operaciones/{oid}',json={'lugar':'Cambio cerrado'},headers=self.h).status_code,409)
        url=f'/api/admin/5b/periodos/{self.pid}/reabrir'
        self.assertEqual(self.cliente.post(url,json={'cierre_id':cid,'motivo':'DEMO'},headers=self.h).status_code,403)
        self._login();self.h={'X-CSRFToken':self._csrf_token()}
        self.assertEqual(self.cliente.post(url,json={'cierre_id':cid,'motivo':'Reapertura DEMO'},headers=self.h).status_code,200)
        self.assertEqual(self.nota('DESEMPENO_JEFE',90).status_code,201)
        self.assertEqual(self.cierre().status_code,201)
        antiguo=self.cliente.get(f'/api/5b/periodos/{self.pid}/cierres/{cid}').json['cierre']['personas'][0]
        self.assertEqual(antiguo['calculo']['desempeno'],'40');self.assertIn('evidencia_modelo_anual',antiguo)

    def test_permisos_inactivos_csrf_y_fuente_desactivada(self):
        self.preparar_anual();oid=self.operacion_demo()
        cuerpo={'nota':20,'anterior_id':None,'motivo':'DEMO'};ruta=self.url+f'/personas/3/operaciones/{oid}'
        self.assertEqual(self.cliente.post(ruta,json=cuerpo).status_code,400)
        self._login('voluntario.demo','Clave voluntario 123!');h={'X-CSRFToken':self._csrf_token()}
        for url in ('/gestion/modelo-anual',self.base,self.url,self.url+'/personas/3'):self.assertEqual(self.cliente.get(url).status_code,403)
        self.assertEqual(self.cliente.post(ruta,json=cuerpo,headers=h).status_code,403)
        self._login('instructor.demo','Clave instructor 123!');self.h={'X-CSRFToken':self._csrf_token()}
        self.assertEqual(self.cliente.patch(f'/api/5b/gestiones/{self.pid}/evaluaciones/ACADEMICA',json={'activa':False,'revision':0,'motivo':'DEMO'},headers=self.h).status_code,200)
        self.assertEqual(self.puntuar_operacion(oid,20).status_code,409)
        with self.app.app_context():c=obtener_conexion();c.execute("UPDATE usuarios SET estado='INACTIVO' WHERE id=3");c.commit()
        self.assertEqual(self.nota('DESEMPENO_JEFE',90).status_code,409)
        self.assertEqual(self.cliente.post(f'/api/admin/5b/periodos/{self.pid}/publicar',json={'revision':1},headers=self.h).status_code,403)

    def test_edicion_fechas_historial_cierre_bloquea_ambos_intervalos(self):
        self.preparar_anual()
        r=self.cliente.post(self.base,json={'nombre':'Borrador propio DEMO','fecha_inicio':'2027-02-01','fecha_fin':'2027-05-01'},headers=self.h);self.assertEqual(r.status_code,201)
        url=self.base+'/'+str(r.json['id']);body={'nombre':'Borrador corregido DEMO','fecha_inicio':'2027-01-15','fecha_fin':'2027-06-01','revision':1,'motivo':'Corrección de fechas DEMO'}
        self.assertEqual(self.cliente.patch(url,json=body,headers=self.h).status_code,200)
        self.assertEqual(self.cliente.patch(url,json=body,headers=self.h).status_code,409)
        self.assertEqual(len(self.cliente.get(url).json['historial_gestion']),2)
        self.assertEqual(self.cliente.patch(self.url,json=body,headers=self.h).status_code,409)
        self.assertEqual(self.cliente.post(self.base,json={'nombre':'Solapada DEMO','fecha_inicio':'2025-11-01','fecha_fin':'2025-12-31'},headers=self.h).status_code,400)

    def test_concurrencia_no_bifurca_notas(self):
        self.preparar_anual();anterior=self.datos()['calculo']['fuentes']['DESEMPENO_JEFE']['id']
        def enviar(valor):
            cliente=self.app.test_client()
            token=re.search(rb'name="csrf_token" value="([^"]+)"',cliente.get('/login').data).group(1).decode()
            cliente.post('/api/auth/login',json={'username':'instructor.demo','password':'Clave instructor 123!'},headers={'X-CSRFToken':token})
            token=re.search(rb'name="csrf_token" value="([^"]+)"',cliente.get('/panel/jefe-personal').data).group(1).decode()
            return cliente.post(self.url+'/personas/3',json={'fuente':'DESEMPENO_JEFE','nota':valor,'anterior_id':anterior,'motivo':'Concurrente DEMO','evidencia':{}},headers={'X-CSRFToken':token}).status_code
        with ThreadPoolExecutor(max_workers=2) as ex:estados=list(ex.map(enviar,[40,60]))
        self.assertEqual(sorted(estados),[201,409]);self.assertEqual(len(self.datos()['historial']['notas']),6)

    def test_migracion_aditiva_repetida_sin_adopcion(self):
        with self.app.app_context():
            c=obtener_conexion();tablas=['eventos_modelo_anual','notas_operacion_anual','notas_modelo_anual','personas_modelo_anual','modelos_anuales']
            c.execute('DROP TRIGGER periodo_modelo_fechas')
            for t in tablas:c.execute('DROP TABLE '+t)
            c.execute("UPDATE app_meta SET valor='23' WHERE clave='schema_version'");c.commit()
            antes={t:[tuple(f) for f in c.execute('SELECT * FROM '+t)] for t in ('usuarios','roles','periodos','notas_operativas')}
            inicializar_base_datos();inicializar_base_datos()
            for t,filas in antes.items():self.assertEqual([tuple(f) for f in c.execute('SELECT * FROM '+t)],filas)
            for t in tablas:self.assertEqual(c.execute('SELECT COUNT(*) FROM '+t).fetchone()[0],0)
            self.assertEqual(c.execute("SELECT valor FROM app_meta WHERE clave='schema_version'").fetchone()[0],'25')
            self.assertEqual(c.execute('PRAGMA quick_check').fetchone()[0],'ok');self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(),[])

    def test_bloqueo_formacion_en_fecha_anterior_y_nueva_del_periodo_cerrado(self):
        self.preparar_anual()
        curso={'nombre':'Curso fecha DEMO','tipo':'Taller','entidad':'Entidad DEMO','fecha_inicio':'2025-07-01','fecha_fin':'2025-07-02','puntaje':15}
        cid=self.cliente.post('/api/cursos',json=curso,headers=self.h).json['id']
        self.cliente.post(f'/api/cursos/{cid}/participantes',json={'voluntario_ids':[3]},headers=self.h)
        part=self.cliente.get(f'/api/cursos/{cid}/participantes').json['participantes'][0]['id'];ruta=f'/api/formacion/participaciones/{part}'
        body={'revision':1,'estado':'Finalizado','puntaje':15,'fecha_finalizacion':'2025-07-15','motivo':'Finalización fuera DEMO'}
        self.assertEqual(self.cliente.patch(ruta,json=body,headers=self.h).status_code,200)
        self.assertEqual(self.cierre().status_code,201)
        self.assertEqual(self.cliente.patch(ruta,json={**body,'revision':2,'fecha_finalizacion':'2025-09-02'},headers=self.h).status_code,409)
        self._login();self.h={'X-CSRFToken':self._csrf_token()};cid_cierre=self.cliente.get(self.url).json['cierres'][-1]['id']
        self.cliente.post(f'/api/admin/5b/periodos/{self.pid}/reabrir',json={'motivo':'Reabrir DEMO','cierre_id':cid_cierre},headers=self.h)
        self.assertEqual(self.cliente.patch(ruta,json={**body,'revision':2,'fecha_finalizacion':'2025-09-02'},headers=self.h).status_code,200)
        self.assertEqual(self.cierre().status_code,201)
        self.assertEqual(self.cliente.patch(ruta,json={**body,'revision':3,'fecha_finalizacion':'2025-12-02'},headers=self.h).status_code,409)
        self.assertEqual(self.cliente.patch(ruta,json={'revision':3,'estado':'No completado','motivo':'Retirar DEMO'},headers=self.h).status_code,409)

    def test_habilitacion_individual_rehabilita_sin_reset_y_privacidad(self):
        self.preparar_anual();self.assertEqual(self.nota('DESEMPENO_JEFE',81).status_code,201)
        ruta='/api/evaluaciones/personas/3/habilitacion';body={'periodo_id':self.pid,'clave':'DESEMPENO_JEFE','habilitada':False}
        self.assertEqual(self.cliente.patch(ruta,json=body,headers=self.h).status_code,200)
        self.assertIsNone(self.datos()['calculo']['desempeno']);self.assertEqual(self.nota('DESEMPENO_JEFE',90).status_code,409)
        self.assertEqual(self.cliente.patch(ruta,json={**body,'habilitada':True},headers=self.h).status_code,200)
        self.assertEqual(self.datos()['calculo']['desempeno'],'40.5')
        self._login();self.h={'X-CSRFToken':self._csrf_token()}
        self.assertEqual(self.cliente.post(f'/api/admin/5b/periodos/{self.pid}/configuracion',json={'fuentes':{}},headers=self.h).status_code,409)
        self.assertEqual(self.cliente.post(f'/api/admin/5b/periodos/{self.pid}/publicar',json={'revision':1},headers=self.h).status_code,409)
        self._login('voluntario.demo','Clave voluntario 123!')
        self.assertEqual(self.cliente.get(f'/api/evaluaciones/propias?periodo_id={self.pid}').status_code,403)
        self.assertNotIn(self.pid,[p['id'] for p in self.cliente.get('/api/evaluaciones/gestiones').json['periodos']])

    def test_retiro_revision_y_triggers_preservan_historia(self):
        self.preparar_anual();antes=self.datos()['historial']
        self.assertEqual(self.cliente.delete(self.url,json={'revision':1,'motivo':'Baja obsoleta'},headers=self.h).status_code,409)
        self.assertEqual(self.cliente.delete(self.url,json={'revision':2,'motivo':'Baja conservada DEMO'},headers=self.h).status_code,200)
        r=self.cliente.get(self.url);self.assertEqual(r.status_code,200);self.assertTrue(r.json['periodo']['retirada'])
        self.assertEqual(self.nota('DESEMPENO_JEFE',50).status_code,409)
        with self.app.app_context():
            c=obtener_conexion();self.assertEqual(c.execute('SELECT COUNT(*) FROM notas_modelo_anual WHERE periodo_id=?',(self.pid,)).fetchone()[0],len(antes['notas']))
            import sqlite3
            with self.assertRaises(sqlite3.IntegrityError):c.execute('UPDATE notas_modelo_anual SET puntos_centesimas=100 WHERE periodo_id=?',(self.pid,))
            c.rollback()
            with self.assertRaises(sqlite3.IntegrityError):c.execute("UPDATE periodos SET fecha_fin='2025-12-01' WHERE id=?",(self.pid,))
            c.rollback()
