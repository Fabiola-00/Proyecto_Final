"""Reapertura excepcional de históricos e integración completa de las entregas 5B."""
import json
import sqlite3
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
import test_cierres_5b as fixtures
from sicose.db import obtener_conexion, inicializar_base_datos


class Historicos5BTestCase(unittest.TestCase):
    for _nombre,_valor in vars(fixtures.CierresTestCase).items():
        if (_nombre.startswith('_') and not _nombre.startswith('__')) or _nombre in ('setUp','tearDown','preparar','fisica','desempeno','curso','activar','calculo','preparar_publicable','vista','publicar','propia','corregir_fisica','preview','cerrar','reabrir','detalle'):
            locals()[_nombre]=_valor

    def historico(self,v2=False):
        self.preparar();self.fisica('FISICA_1','60');self.participacion=self.curso(25)
        if v2:self.activar()
        self._login();self.h={'X-CSRFToken':self._csrf_token()}
        with self.app.app_context():
            c=obtener_conexion();c.execute("UPDATE periodos SET estado='CERRADO' WHERE id=?",(self.pid,));c.commit()

    def evidencia_previa(self):
        r=self.cliente.get(f'/api/5b/periodos/{self.pid}/reapertura-historica-previa')
        self.assertEqual(r.status_code,200,r.json);return r.json

    def excepcional(self,v=None):
        v=v or self.evidencia_previa()
        return self.cliente.post(f'/api/admin/5b/periodos/{self.pid}/reabrir-historico',json={
            'motivo':'Reapertura excepcional con constancia DEMO','firma_fuentes':v['firma_fuentes'],'confirmar_sin_instantanea':True},headers=self.h)

    def evidencia(self):
        r=self.cliente.get(f'/api/5b/periodos/{self.pid}/reapertura-historica')
        self.assertEqual(r.status_code,200,r.json);return r.json['reapertura']

    def test_constancia_fuentes_inmutables_sin_inventar_cierre_ni_regla(self):
        self.historico();v=self.evidencia_previa()
        self.assertTrue(v['contexto']['sin_instantanea_original']);self.assertIsNone(v['contexto']['fecha_cierre_original'])
        self.assertEqual(v['personas'][0]['calculo']['estado'],'NO_RECONSTRUIDO')
        self.assertIsNone(v['personas'][0]['calculo']['resultado_conjunto'])
        self.assertEqual(self.excepcional(v).status_code,201)
        e=self.evidencia();self.assertEqual(e['evidencia']['personas'][0]['notas'][0]['puntos_centesimas'],6000)
        self.assertEqual(self.excepcional(v).status_code,409)
        self.assertEqual(self.cliente.get(f'/api/5b/periodos/{self.pid}/cierres').json['cierres'],[])
        self.assertEqual(self.calculo()['estado'],'SIN_REGLA_NUEVA')
        conf=e['evidencia']['contexto']['configuracion']['id']
        self.assertEqual(self.cliente.post(f'/api/admin/5b/periodos/{self.pid}/calculo',json={'configuracion_id':conf,'regla':'ACUMULADO_TRES_V2','confirmar_fuentes':True},headers=self.h).status_code,409)
        self.corregir_fisica('80')
        cid=self.cerrar().json['cierre_id'];nuevo=self.detalle(cid)
        self.assertEqual(nuevo['numero'],1);self.assertIsNone(nuevo['anterior_id'])
        self.assertEqual(nuevo['contexto']['reapertura_historica'][0]['id'],e['id'])
        self.assertIsNone(nuevo['personas'][0]['calculo']['resultado_conjunto'])
        self.assertEqual(self.evidencia(),e)
        self.assertEqual(self.reabrir(cid).status_code,200)
        self.assertEqual(self.evidencia(),e)
        with self.app.app_context():
            c=obtener_conexion()
            for sql in ["UPDATE reaperturas_historicas_5b SET motivo='otro'",'DELETE FROM reaperturas_historicas_5b']:
                with self.assertRaises(sqlite3.IntegrityError):c.execute(sql)
                c.rollback()

    def test_permisos_csrf_confirmacion_y_sesion_inactiva(self):
        self.historico();v=self.evidencia_previa();url=f'/api/admin/5b/periodos/{self.pid}/reabrir-historico'
        body={'motivo':'Constancia DEMO','firma_fuentes':v['firma_fuentes'],'confirmar_sin_instantanea':True}
        self.assertEqual(self.cliente.post(url,json=body).status_code,400)
        for extra in [{'motivo':' '},{'confirmar_sin_instantanea':False},{'confirmar_sin_instantanea':1},{'otro':True}]:
            self.assertEqual(self.cliente.post(url,json={**body,**extra},headers=self.h).status_code,400)
        self._login('instructor.demo','Clave instructor 123!');self.h={'X-CSRFToken':self._csrf_token()}
        self.assertEqual(self.excepcional(v).status_code,403)
        self.evidencia_previa()
        self._login('voluntario.demo','Clave voluntario 123!');self.h={'X-CSRFToken':self._csrf_token()}
        for ruta in ['reapertura-historica-previa','reapertura-historica']:
            self.assertEqual(self.cliente.get(f'/api/5b/periodos/{self.pid}/{ruta}').status_code,403)
        self.assertEqual(self.excepcional(v).status_code,403)
        self._login();self.h={'X-CSRFToken':self._csrf_token()}
        with self.app.app_context():
            c=obtener_conexion();c.execute("UPDATE usuarios SET estado='INACTIVO' WHERE id=1");c.commit()
        self.assertEqual(self.excepcional(v).status_code,401)

    def test_fuentes_obsoletas_concurrencia_y_cache_privada(self):
        self.historico();v=self.evidencia_previa()
        with self.app.app_context():
            c=obtener_conexion();c.execute("UPDATE usuarios SET nombre_completo='Nombre actualizado DEMO' WHERE id=3");c.commit()
        self.assertEqual(self.excepcional(v).status_code,409)
        v=self.evidencia_previa();cookie=self.cliente.get_cookie(self.app.config['SESSION_COOKIE_NAME']);barrera=threading.Barrier(2)
        def enviar(_):
            cl=self.app.test_client();cl.set_cookie(cookie.key,cookie.value);barrera.wait()
            return cl.post(f'/api/admin/5b/periodos/{self.pid}/reabrir-historico',json={'motivo':'Concurrencia DEMO','firma_fuentes':v['firma_fuentes'],'confirmar_sin_instantanea':True},headers=self.h).status_code
        with ThreadPoolExecutor(max_workers=2) as e:estados=list(e.map(enviar,range(2)))
        self.assertEqual(sorted(estados),[201,409])
        self.assertEqual(self.cliente.get(f'/api/5b/periodos/{self.pid}/reapertura-historica').headers['Cache-Control'],'private, no-store')
        self.assertEqual(self.cliente.get('/api/5b/periodos/999/reapertura-historica').status_code,404)

    def test_no_segundo_activo_no_retirada_no_cierre_con_instantaneas(self):
        self.historico();v=self.evidencia_previa()
        with self.app.app_context():
            c=obtener_conexion();otro=c.execute("INSERT INTO periodos(nombre,fecha_inicio,fecha_fin,estado) VALUES ('Otra DEMO','2027-01-01','2027-12-31','ACTIVO')").lastrowid;c.commit()
        self.assertEqual(self.excepcional(v).status_code,409)
        with self.app.app_context():
            c=obtener_conexion();c.execute("UPDATE periodos SET estado='CERRADO' WHERE id=?",(otro,));c.commit()
        self.assertEqual(self.excepcional(v).status_code,201)
        cid=self.cerrar().json['cierre_id']
        self.assertEqual(self.cliente.get(f'/api/5b/periodos/{self.pid}/reapertura-historica-previa').status_code,409)
        self.assertEqual(self.excepcional(v).status_code,409)
        self.assertEqual(self.reabrir(cid).status_code,200)
        self.cerrar()
        with self.app.app_context():
            c=obtener_conexion();c.execute("INSERT INTO bajas_gestion(periodo_id,motivo,actor_id,actor_nombre,registrada_en) VALUES (?,'Retirada',1,'Admin DEMO','2026-10-14')",(self.pid,));c.commit()
        self.assertEqual(self.excepcional(v).status_code,409)
        self.evidencia()

    def test_regla_v2_preexistente_y_publicacion_se_conservan(self):
        self.preparar_publicable();self.assertEqual(self.publicar().status_code,201)
        antes=self.propia();self._login();self.h={'X-CSRFToken':self._csrf_token()}
        with self.app.app_context():
            c=obtener_conexion();c.execute("UPDATE periodos SET estado='CERRADO' WHERE id=?",(self.pid,));c.commit()
        self.assertEqual(self.excepcional().status_code,201)
        self.assertEqual(self.calculo()['academica']['valor'],75)
        self.assertEqual(self.propia(),antes)

    def test_migracion_v22_repetida_sin_acciones_automaticas(self):
        self.historico()
        with self.app.app_context():
            c=obtener_conexion();c.execute('DROP TABLE reaperturas_historicas_5b');c.execute("UPDATE app_meta SET valor='22' WHERE clave='schema_version'");c.commit()
            tablas=[r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name!='app_meta'")]
            antes={t:[tuple(f) for f in c.execute(f'SELECT * FROM "{t}" ORDER BY rowid')] for t in tablas}
            inicializar_base_datos();inicializar_base_datos()
            for t,datos in antes.items():self.assertEqual([tuple(f) for f in c.execute(f'SELECT * FROM "{t}" ORDER BY rowid')],datos,t)
            self.assertEqual(c.execute('SELECT COUNT(*) FROM reaperturas_historicas_5b').fetchone()[0],0)
            self.assertEqual(c.execute("SELECT valor FROM app_meta WHERE clave='schema_version'").fetchone()[0],'33')
            self.assertEqual(c.execute('PRAGMA quick_check').fetchone()[0],'ok');self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(),[])

    def test_recorrido_integral_fisica_formacion_publicacion_cierre_y_correccion(self):
        self.preparar();self.fisica('FISICA_1','0','NO_CUMPLIDA');self.fisica('FISICA_2','80')
        self.desempeno('DESEMPENO_JEFE','80');self.desempeno('DESEMPENO_COMANDANTE','90')
        part=self.curso(75);self.activar();self.url='/api/5b/personas/3/publicacion'
        self.assertEqual(self.calculo()['resultado_conjunto'],'66.67')
        self.assertEqual(self.publicar().status_code,201)
        propia=self.propia();self.assertEqual(propia['promedio_fisico'],'40')
        self._login();self.h={'X-CSRFToken':self._csrf_token()}
        r=self.cliente.post(f'/api/5b/periodos/{self.pid}/fisicas/FISICA_1/personas/3',json={'fecha':'2026-06-01','motivo':'Reprogramación extraordinaria DEMO','anterior_id':None,'programacion_id':self.fechas['FISICA_1']},headers=self.h)
        self.assertEqual(r.status_code,201);self.assertEqual(self.calculo()['resultado_conjunto'],'66.67')
        cid=self.cerrar().json['cierre_id'];cierre=self.detalle(cid)
        self.assertEqual(self.reabrir(cid).status_code,200)
        self.assertEqual(self.cliente.patch(f'/api/formacion/participaciones/{part}',json={'revision':2,'estado':'Finalizado','puntaje':100,'fecha_finalizacion':'2026-03-01','motivo':'Corrección tras reapertura'},headers=self.h).status_code,200)
        self.assertEqual(self.calculo()['resultado_conjunto'],'75.00')
        self.assertEqual(self.propia(),propia)
        self._login('instructor.demo','Clave instructor 123!');self.h={'X-CSRFToken':self._csrf_token()}
        self.assertEqual(self.publicar().status_code,201)
        nueva=self.propia();self.assertEqual(nueva['academica']['valor'],100)
        for campo in ['DESEMPENO','resultado_conjunto','motivo','actor_nombre','firma_fuentes']:
            self.assertNotIn(campo,json.dumps(nueva))
        self._login();self.h={'X-CSRFToken':self._csrf_token()}
        cid2=self.cerrar().json['cierre_id'];self.assertEqual(self.detalle(cid2)['anterior_id'],cid)
        self.assertEqual(self.detalle(cid),cierre)
        self.assertEqual(self.calculo()['resultado_conjunto'],'75.00')
    def test_historico_sin_configuracion_conserva_calificaciones_anteriores(self):
        self.historico()
        with self.app.app_context():
            c=obtener_conexion()
            eid=c.execute("SELECT id FROM evaluaciones WHERE categoria='FISICA' LIMIT 1").fetchone()[0]
            self.pid=c.execute("INSERT INTO periodos(nombre,fecha_inicio,fecha_fin,estado) VALUES ('Histórico sin config DEMO','2025-01-01','2025-12-31','CERRADO')").lastrowid
            aid=c.execute("INSERT INTO asignaciones_evaluacion(voluntario_id,periodo_id,evaluacion_id,estado) VALUES (3,?,?,'COMPLETADA')",(self.pid,eid)).lastrowid
            nid=c.execute("INSERT INTO calificaciones(asignacion_id,registrada_por,nota_0_100,observacion) VALUES (?,2,70,'Respaldo histórico DEMO')",(aid,)).lastrowid;c.commit()
        v=self.evidencia_previa();self.assertIsNone(v['contexto']['configuracion'])
        self.assertEqual(v['personas'][0]['notas_historicas'][0]['id'],nid)
        self.assertEqual(self.excepcional(v).status_code,201)
        e=self.evidencia();self.assertEqual(e['evidencia']['personas'][0]['notas_historicas'][0]['nota_0_100'],70)
        self.assertEqual(self.calculo()['estado'],'SIN_REGLA_NUEVA')
        cid=self.cerrar().json['cierre_id'];self.assertIsNone(self.detalle(cid)['personas'][0]['calculo']['resultado_conjunto'])
        with self.app.app_context():
            c=obtener_conexion();self.assertIsNone(c.execute('SELECT 1 FROM configuraciones_5b WHERE periodo_id=?',(self.pid,)).fetchone())
            self.assertEqual(c.execute('SELECT nota_0_100 FROM calificaciones WHERE id=?',(nid,)).fetchone()[0],70)
