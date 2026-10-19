"""5B.4: cierre/reapertura, instantáneas, bloqueos e historial reproducible."""
import json
import sqlite3
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
import test_publicaciones_5b as fixtures
from sicose.db import obtener_conexion, inicializar_base_datos


class CierresTestCase(unittest.TestCase):
    for _nombre, _valor in vars(fixtures.PublicacionesTestCase).items():
        if (_nombre.startswith('_') and not _nombre.startswith('__')) or _nombre in ('setUp','tearDown','preparar','fisica','desempeno','curso','activar','calculo','preparar_publicable','vista','publicar','propia','corregir_fisica'):
            locals()[_nombre] = _valor

    def preview(self):
        r=self.cliente.get(f'/api/5b/periodos/{self.pid}/cierre-previo')
        self.assertEqual(r.status_code,200,r.json)
        return r.json

    def cerrar(self,vista=None,confirmar=True):
        v=vista or self.preview()
        return self.cliente.post(f'/api/admin/5b/periodos/{self.pid}/cerrar',json={
            'motivo':'Cierre anual revisado DEMO','firma_fuentes':v['firma_fuentes'],
            'cierre_anterior_id':v['cierre_anterior_id'],'confirmar_incompletos':confirmar},headers=self.h)

    def reabrir(self,cid):
        return self.cliente.post(f'/api/admin/5b/periodos/{self.pid}/reabrir',json={'motivo':'Revisar resultados DEMO','cierre_id':cid},headers=self.h)

    def detalle(self,cid):
        r=self.cliente.get(f'/api/5b/periodos/{self.pid}/cierres/{cid}')
        self.assertEqual(r.status_code,200,r.json)
        return r.json['cierre']

    def test_cierre_incompleto_confirmacion_cero_y_privacidad(self):
        self.preparar_publicable();self.fisica('FISICA_2','0','NO_CUMPLIDA')
        self.assertEqual(self.publicar().status_code,201)
        propia_antes=self.propia()
        self._login();self.h={'X-CSRFToken':self._csrf_token()}
        self.assertEqual(self.cerrar(confirmar=False).status_code,409)
        r=self.cerrar();self.assertEqual(r.status_code,201,r.json);cid=r.json['cierre_id']
        s=self.detalle(cid);p=s['personas'][0]
        self.assertEqual(p['calculo']['faltantes'],['DESEMPENO_JEFE','DESEMPENO_COMANDANTE'])
        self.assertIsNone(p['calculo']['resultado_conjunto']);self.assertEqual(p['calculo']['fisica'],'30')
        self.assertEqual(p['resultados_fisicos'][1]['estado'],'NO_CUMPLIDA')
        self.assertEqual(self.propia(),propia_antes)
        self.assertEqual(self.cliente.get(f'/api/5b/periodos/{self.pid}/cierres/{cid}').status_code,403)
        self.assertEqual(self.cliente.get(f'/api/5b/periodos/{self.pid}/cierre-previo').status_code,403)

    def test_cierre_completo_exacto_reapertura_recierre_y_autoria(self):
        self.preparar_publicable();self.fisica('FISICA_2','60.01')
        self.desempeno('DESEMPENO_JEFE','0');self.desempeno('DESEMPENO_COMANDANTE','0.01')
        r=self.cerrar();self.assertEqual(r.status_code,201,r.json);cid=r.json['cierre_id']
        antes=self.detalle(cid);p=antes['personas'][0]
        self.assertEqual(p['calculo']['estado'],'COMPLETO')
        self.assertEqual(p['calculo']['resultado_exacto_centesimas'],{'numerador':13501,'denominador':3})
        self.assertEqual(p['calculo']['resultado_conjunto'],'45.00')
        self.assertEqual(self.calculo()['cierre_id'],cid);self.assertFalse(self.calculo()['provisional'])
        self.assertEqual(self.reabrir(cid).status_code,200)
        self.corregir_fisica('90')
        r=self.cerrar();self.assertEqual(r.status_code,201,r.json);nuevo=r.json['cierre_id']
        self.assertEqual(self.detalle(cid),antes)
        self.assertEqual(self.detalle(nuevo)['anterior_id'],cid)
        self.assertNotEqual(self.detalle(nuevo)['personas'][0]['calculo']['resultado_conjunto'],p['calculo']['resultado_conjunto'])
        self.assertEqual(self.detalle(nuevo)['contexto']['configuracion'],antes['contexto']['configuracion'])
        with self.app.app_context():
            c=obtener_conexion()
            for tabla in ['cierres_5b','instantaneas_cierre_5b','reaperturas_5b']:
                with self.assertRaises(sqlite3.IntegrityError):c.execute(f'DELETE FROM {tabla}')
                c.rollback()
                campo='motivo' if tabla!='instantaneas_cierre_5b' else 'contenido_json'
                with self.assertRaises(sqlite3.IntegrityError):c.execute(f"UPDATE {tabla} SET {campo}='otro'")
                c.rollback()
        self._login('instructor.demo','Clave instructor 123!')
        self.assertEqual(self.detalle(cid)['actor_nombre'],'admin.demo')

    def test_permisos_csrf_inactivo_motivo_y_objeto(self):
        self.preparar_publicable();v=self.preview()
        body={'motivo':'Cierre DEMO','firma_fuentes':v['firma_fuentes'],'cierre_anterior_id':None,'confirmar_incompletos':True}
        url=f'/api/admin/5b/periodos/{self.pid}/cerrar'
        self.assertEqual(self.cliente.post(url,json=body).status_code,400)
        self.assertEqual(self.cliente.post(url,json={**body,'motivo':' '},headers=self.h).status_code,400)
        self._login('instructor.demo','Clave instructor 123!');self.h={'X-CSRFToken':self._csrf_token()}
        r=self.cerrar(v);self.assertEqual(r.status_code,201);cid=r.json['cierre_id']
        self.assertEqual(self.reabrir(cid).status_code,403)
        self._login();self.h={'X-CSRFToken':self._csrf_token()}
        self.assertEqual(self.cerrar(v).status_code,409)
        self.assertEqual(self.cliente.get(f'/api/5b/periodos/999/cierres/{cid}').status_code,404)
        self.assertEqual(self.reabrir(cid+1).status_code,409)
        with self.app.app_context():
            c=obtener_conexion();c.execute("UPDATE usuarios SET estado='INACTIVO' WHERE id=1");c.commit()
        self.assertEqual(self.reabrir(cid).status_code,401)

    def test_firma_detecta_correcciones_y_cuenta_y_concurrencia_cierre(self):
        self.preparar_publicable();vieja=self.preview();self.corregir_fisica('77')
        self.assertEqual(self.cerrar(vieja).status_code,409)
        v=self.preview()
        with self.app.app_context():
            c=obtener_conexion();c.execute("UPDATE usuarios SET estado='INACTIVO' WHERE id=3");c.commit()
        self.assertEqual(self.cerrar(v).status_code,409)
        v=self.preview();cookie=self.cliente.get_cookie(self.app.config['SESSION_COOKIE_NAME'])
        barrera=threading.Barrier(2)
        def enviar(_):
            cl=self.app.test_client();cl.set_cookie(cookie.key,cookie.value);barrera.wait()
            return cl.post(f'/api/admin/5b/periodos/{self.pid}/cerrar',json={'motivo':'Cierre concurrente','firma_fuentes':v['firma_fuentes'],'cierre_anterior_id':None,'confirmar_incompletos':True},headers=self.h).status_code
        with ThreadPoolExecutor(max_workers=2) as e:estados=list(e.map(enviar,range(2)))
        self.assertEqual(sorted(estados),[201,409])
        self.assertEqual(len(self.cliente.get(f'/api/5b/periodos/{self.pid}/cierres').json['cierres']),1)

    def test_cerrada_bloquea_notas_fechas_habilitacion_publicacion_y_anual(self):
        self.preparar_publicable();vpub=self.vista();cid=self.cerrar().json['cierre_id']
        nota={'periodo_id':self.pid,'fuente':'DESEMPENO_JEFE','nota_0_100':'50'}
        self.assertEqual(self.cliente.post('/api/5b/personas/3/notas',json=nota,headers=self.h).status_code,409)
        self.assertEqual(self.cliente.post(f'/api/5b/periodos/{self.pid}/fisicas/FISICA_1',json={'fecha':'2026-06-01','motivo':'Cambiar','anterior_id':self.fechas['FISICA_1']},headers=self.h).status_code,409)
        self.assertEqual(self.cliente.post(f'/api/5b/periodos/{self.pid}/fisicas/FISICA_1/personas/3',json={'fecha':'2026-07-01','motivo':'Reprogramar','anterior_id':None,'programacion_id':self.fechas['FISICA_1']},headers=self.h).status_code,409)
        self.assertEqual(self.cliente.patch(f'/api/5b/gestiones/{self.pid}/evaluaciones/FISICA_1',json={'activa':False,'revision':0,'motivo':'Suspender'},headers=self.h).status_code,409)
        self.assertEqual(self.publicar(vpub).status_code,409)
        with self.app.app_context():
            c=obtener_conexion()
            eid=c.execute("SELECT evaluacion_id FROM fuentes_configuracion_5b WHERE configuracion_id=? AND fuente='FISICA_1'",(self.conf,)).fetchone()[0]
            c.execute("INSERT OR IGNORE INTO asignaciones_evaluacion(voluntario_id,periodo_id,evaluacion_id) VALUES (3,?,?)",(self.pid,eid));c.commit()
            aid=c.execute('SELECT id FROM asignaciones_evaluacion WHERE voluntario_id=3 AND periodo_id=? AND evaluacion_id=?',(self.pid,eid)).fetchone()[0]
        self.assertEqual(self.cliente.patch(f'/api/jefe-personal/asignaciones/{aid}/estado',json={'estado':'NO_HABILITADA'},headers=self.h).status_code,409)

        self.assertEqual(self.cliente.patch('/api/evaluaciones/personas/3/habilitacion',json={'periodo_id':self.pid,'clave':'FISICA_1','habilitada':False},headers=self.h).status_code,409)
        self.assertEqual(self.cliente.get(f'/api/5b/periodos/{self.pid}/cierres/{cid}').headers['Cache-Control'],'private, no-store')

    def test_formacion_bloquea_ano_anterior_nuevo_y_desfinalizar(self):
        self.preparar_publicable();otro=self.curso(25,'2025-02-01');cid=self.cerrar().json['cierre_id']
        for part,estado,fecha in [(self.participacion,'Finalizado','2025-03-01'),(self.participacion,'No completado',None),(otro,'Finalizado','2026-03-01')]:
            b={'revision':2,'estado':estado,'motivo':'Corregir año cerrado'}
            if fecha:b.update(puntaje=30,fecha_finalizacion=fecha)
            self.assertEqual(self.cliente.patch(f'/api/formacion/participaciones/{part}',json=b,headers=self.h).status_code,409)
        self.assertEqual(self.reabrir(cid).status_code,200)
        r=self.cliente.patch(f'/api/formacion/participaciones/{self.participacion}',json={'revision':2,'estado':'Finalizado','puntaje':20,'fecha_finalizacion':'2025-03-01','motivo':'Corregir tras reapertura'},headers=self.h)
        self.assertEqual(r.status_code,200,r.json)

    def test_reapertura_no_segundo_activo_ni_retirada(self):
        self.preparar_publicable();cid=self.cerrar().json['cierre_id']
        with self.app.app_context():
            c=obtener_conexion();otro=c.execute("INSERT INTO periodos(nombre,fecha_inicio,fecha_fin,estado) VALUES ('Otra DEMO','2027-01-01','2027-12-31','ACTIVO')").lastrowid;c.commit()
        self.assertEqual(self.reabrir(cid).status_code,409)
        with self.app.app_context():
            c=obtener_conexion();c.execute("UPDATE periodos SET estado='CERRADO' WHERE id=?",(otro,));c.commit()
        self.assertEqual(self.reabrir(cid).status_code,200)
        nuevo=self.cerrar().json['cierre_id']
        self.assertEqual(self.cliente.delete(f'/api/admin/5b/periodos/{self.pid}',json={'motivo':'Retiro con historial','nombre_anterior':'Gestión 2026','ano_anterior':2026,'estado_anterior':'CERRADO'},headers=self.h).status_code,409) # nombre exacto requerido
        with self.app.app_context():
            c=obtener_conexion();c.execute("INSERT INTO bajas_gestion(periodo_id,motivo,actor_id,actor_nombre,registrada_en) VALUES (?,'Retiro',1,'Admin DEMO','2026-10-14')",(self.pid,));c.commit()
        self.assertEqual(self.reabrir(nuevo).status_code,409)
        self.assertEqual(self.detalle(cid)['id'],cid)

    def test_historico_activo_sin_adopcion_y_migracion_idempotente(self):
        self.preparar() # publicada PROMEDIO_TRES_V1 sin opt-in v2
        self._login();self.h={'X-CSRFToken':self._csrf_token()}
        v=self.preview();self.assertIsNone(v['contexto']['regla_calculo'])
        cid=self.cerrar().json['cierre_id'];s=self.detalle(cid)
        self.assertIsNone(s['personas'][0]['calculo']['resultado_conjunto'])
        self.assertEqual(s['personas'][0]['calculo']['faltantes'],['REGLA_V2_NO_ACTIVADA'])
        self.assertEqual(self.reabrir(cid).status_code,200)
        conf=self.detalle(cid)['contexto']['configuracion']['id']
        self.assertEqual(self.cliente.post(f'/api/admin/5b/periodos/{self.pid}/calculo',json={'configuracion_id':conf,'regla':'ACUMULADO_TRES_V2','confirmar_fuentes':True},headers=self.h).status_code,409)
        with self.app.app_context():
            c=obtener_conexion();antes=[tuple(r) for r in c.execute('SELECT * FROM cierres_5b')]
            inicializar_base_datos();inicializar_base_datos()
            self.assertEqual([tuple(r) for r in c.execute('SELECT * FROM cierres_5b')],antes)
            self.assertEqual(c.execute("SELECT valor FROM app_meta WHERE clave='schema_version'").fetchone()[0],'32')
            self.assertEqual(c.execute('PRAGMA quick_check').fetchone()[0],'ok')
            self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(),[])

    def test_reapertura_concurrente_y_cierre_sin_personas(self):
        self.preparar_publicable();cid=self.cerrar().json['cierre_id']
        cookie=self.cliente.get_cookie(self.app.config['SESSION_COOKIE_NAME']);barrera=threading.Barrier(2)
        def abrir(_):
            cl=self.app.test_client();cl.set_cookie(cookie.key,cookie.value);barrera.wait()
            return cl.post(f'/api/admin/5b/periodos/{self.pid}/reabrir',json={'motivo':'Corrección concurrente','cierre_id':cid},headers=self.h).status_code
        with ThreadPoolExecutor(max_workers=2) as e:estados=list(e.map(abrir,range(2)))
        self.assertEqual(sorted(estados),[200,409])
        self.cerrar()
        with self.app.app_context():
            c=obtener_conexion()
            c.execute("UPDATE usuarios SET estado='PENDIENTE' WHERE id=3")
            self.pid=c.execute("INSERT INTO periodos(nombre,fecha_inicio,fecha_fin,estado) VALUES ('Vacía DEMO','2027-01-01','2027-12-31','ACTIVO')").lastrowid;c.commit()
        v=self.preview();self.assertEqual(v['personas'],[])
        r=self.cerrar(v);self.assertEqual(r.status_code,201,r.json)
        self.assertEqual(r.json['total_personas'],0)
        self.assertIsNone(self.detalle(r.json['cierre_id'])['contexto']['configuracion'])

    def test_migracion_v21_preserva_tablas_no_cierra_ni_publica(self):
        self.preparar_publicable()
        with self.app.app_context():
            c=obtener_conexion()
            for tabla in ['instantaneas_cierre_5b','reaperturas_5b','cierres_5b']:
                c.execute(f'DROP TABLE {tabla}')
            c.execute("UPDATE app_meta SET valor='21' WHERE clave='schema_version'");c.commit()
            nombres=[r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
            antes={t:[tuple(r) for r in c.execute(f'SELECT * FROM "{t}" ORDER BY rowid')] for t in nombres if t!='app_meta'}
            inicializar_base_datos();inicializar_base_datos()
            for t,valores in antes.items():self.assertEqual([tuple(r) for r in c.execute(f'SELECT * FROM "{t}" ORDER BY rowid')],valores,t)
            for tabla in ['instantaneas_cierre_5b','reaperturas_5b','cierres_5b']:
                self.assertEqual(c.execute(f'SELECT COUNT(*) FROM {tabla}').fetchone()[0],0)
            self.assertEqual(c.execute('PRAGMA quick_check').fetchone()[0],'ok')
            self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(),[])
