"""Publicación/republicación, versiones estables y proyecciones privadas."""
import json
import sqlite3
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
import test_calculos_5b as fixtures
from sicose.db import obtener_conexion, inicializar_base_datos


class PublicacionesTestCase(unittest.TestCase):
    for _nombre, _valor in vars(fixtures.CalculosTestCase).items():
        if (_nombre.startswith('_') and not _nombre.startswith('__')) or _nombre in ('setUp','tearDown','preparar','fisica','desempeno','curso','activar','calculo'):
            locals()[_nombre] = _valor

    def preparar_publicable(self):
        self.preparar();self.fisica('FISICA_1','60');self.participacion=self.curso(75);self.activar()
        self.url=f'/api/5b/personas/3/publicacion'

    def vista(self):
        r=self.cliente.get(self.url+f'?periodo_id={self.pid}');self.assertEqual(r.status_code,200,r.json)
        return r.json['publicacion']

    def publicar(self, vista=None):
        v=vista or self.vista()
        return self.cliente.post(self.url,json={'periodo_id':self.pid,'revision_publicada':v['revision_publicada'],'firma_fuentes':v['firma_fuentes'],'motivo':'Publicación revisada'},headers=self.h)

    def propia(self):
        self._login('voluntario.demo','Clave voluntario 123!')
        r=self.cliente.get(f'/api/evaluaciones/propias?periodo_id={self.pid}');self.assertEqual(r.status_code,200,r.json)
        return r.json['publicacion']

    def corregir_fisica(self, puntos):
        self._login();self.h={'X-CSRFToken':self._csrf_token()}
        r=self.cliente.post('/api/5b/personas/3/notas',json={'periodo_id':self.pid,'fuente':'FISICA_1','nota_0_100':puntos,'motivo':'Corrección física','corregida_de_id':self.notas['FISICA_1'],
             'fisica':{'estado':'CUMPLIDA','fecha_realizacion':'2026-02-02','programacion_id':self.fechas['FISICA_1'],'reprogramacion_id':None}},headers=self.h)
        self.assertEqual(r.status_code,201,r.json);self.notas['FISICA_1']=r.json['id']

    def test_parcial_admin_jefe_privacidad_y_datos_propios(self):
        self.preparar_publicable();self.curso(50)
        self.assertIsNone(self.propia())
        self.assertNotIn('puntaje',str(self.cliente.get('/api/instructor-voluntario/formacion').json))
        self._login('instructor.demo','Clave instructor 123!');self.h={'X-CSRFToken':self._csrf_token()}
        self.assertEqual(self.publicar().status_code,201)
        p=self.propia();self.assertEqual(p['fisicas'][0]['nota'],'60.00');self.assertIsNone(p['fisicas'][1]['nota'])
        self.assertIsNone(p['promedio_fisico']);self.assertEqual(p['academica']['valor'],100)
        self.assertEqual(p['academica']['puntos_sin_tope'],125);self.assertEqual(len(p['academica']['cursos']),2)
        for prohibido in ('DESEMPENO','desempeno','conjunto','nota_id','fuentes','motivo','responsable','firma','configuracion'):
            self.assertNotIn(prohibido,json.dumps(p))
        self.assertEqual(self.cliente.get('/api/instructor-voluntario/formacion').json['publicaciones'][0]['academica']['cursos'][0]['puntaje'],75)
        respuesta=self.cliente.get(f'/api/evaluaciones/propias?periodo_id={self.pid}')
        self.assertEqual(respuesta.headers['Cache-Control'],'private, no-store')
        self.assertEqual(self.cliente.get('/api/instructor-voluntario/formacion').headers['Cache-Control'],'private, no-store')
        propios=respuesta.json
        self.assertNotIn('DESEMPENO',json.dumps(propios));self.assertEqual(propios['resumen']['habilitadas'],3)
        self.assertEqual(self.cliente.get('/api/instructor-voluntario/formacion?voluntario_id=4').status_code,400)
        self.assertEqual(self.cliente.get(f'/api/evaluaciones/propias?periodo_id={self.pid}&voluntario_id=4').status_code,400)
        self.assertEqual(self.cliente.get(self.url+f'?periodo_id={self.pid}').status_code,403)
        self.assertEqual(self.cliente.get(f'/api/5b/personas/3/publicaciones/historial?periodo_id={self.pid}').status_code,403)

    def test_correccion_conserva_valor_fecha_y_republicacion_historial(self):
        self.preparar_publicable()
        with patch('sicose.publicaciones_5b.db._ahora_utc',return_value='2026-10-13T10:00:00+00:00'):
            self.assertEqual(self.publicar().status_code,201)
        antes=self.propia();self.corregir_fisica('88.25')
        self.assertTrue(self.vista()['hay_cambios'])
        self.assertEqual(self.propia(),antes)
        self._login('instructor.demo','Clave instructor 123!');self.h={'X-CSRFToken':self._csrf_token()}
        with patch('sicose.publicaciones_5b.db._ahora_utc',return_value='2026-10-13T11:00:00+00:00'):
            self.assertEqual(self.publicar().status_code,201)
        actual=self.propia();self.assertEqual(actual['fisicas'][0]['nota'],'88.25')
        self.assertEqual(actual['fisicas'][0]['publicada_en'],'2026-10-13T11:00:00+00:00')
        self.assertEqual(actual['academica']['publicada_en'],antes['academica']['publicada_en'])
        self._login();self.h={'X-CSRFToken':self._csrf_token()}
        historial=self.cliente.get(f'/api/5b/personas/3/publicaciones/historial?periodo_id={self.pid}').json['historial']
        self.assertEqual([p['contenido']['fisicas']['FISICA_1']['nota'] for p in historial],['60.00','88.25'])
        self.assertEqual([p['responsable_nombre'] for p in historial],['admin.demo','instructor.demo'])
        self.assertEqual(self.publicar().status_code,200)
        with self.app.app_context():
            c=obtener_conexion();self.assertEqual(c.execute('SELECT count(*) FROM publicaciones_5b').fetchone()[0],2)
            with self.assertRaises(sqlite3.IntegrityError):c.execute("UPDATE publicaciones_5b SET motivo='Reescribir'")
            c.rollback()

    def test_curso_corregido_de_ano_sin_cero_inferido_ni_actualizacion_automatica(self):
        self.preparar_publicable();self.publicar();antes=self.propia()
        self._login();self.h={'X-CSRFToken':self._csrf_token()}
        r=self.cliente.patch(f'/api/formacion/participaciones/{self.participacion}',json={'revision':2,'estado':'Finalizado','puntaje':30,'fecha_finalizacion':'2025-12-31','motivo':'Fecha corregida'},headers=self.h)
        self.assertEqual(r.status_code,200,r.json)
        self.assertEqual(self.propia(),antes)
        formacion=self.cliente.get('/api/instructor-voluntario/formacion').json
        self.assertEqual(formacion['publicaciones'][0]['academica']['cursos'][0]['fecha_finalizacion'],'2026-03-01')
        self._login();self.h={'X-CSRFToken':self._csrf_token()};self.assertEqual(self.publicar().status_code,201)
        despues=self.propia();self.assertIsNone(despues['academica']['valor']);self.assertEqual(despues['academica']['cursos'],[])

    def test_ocultacion_personal_anual_baja_y_restauracion_de_publicado(self):
        self.preparar_publicable();self.fisica('FISICA_2','80');self.publicar()
        publicado=self.propia();self.assertEqual(publicado['promedio_fisico'],'70')
        self._login();self.h={'X-CSRFToken':self._csrf_token()}
        ruta=f'/api/evaluaciones/personas/3/habilitacion'
        self.cliente.patch(ruta,json={'periodo_id':self.pid,'clave':'FISICA_1','habilitada':False},headers=self.h)
        p=self.propia();self.assertEqual(len(p['fisicas']),1);self.assertIsNone(p['promedio_fisico']);self.assertNotIn('60.00',str(p))
        self._login();self.h={'X-CSRFToken':self._csrf_token()}
        self.cliente.patch(ruta,json={'periodo_id':self.pid,'clave':'FISICA_1','habilitada':True},headers=self.h)
        r=self.cliente.patch(f'/api/5b/gestiones/{self.pid}/evaluaciones/ACADEMICA',json={'activa':False,'revision':0,'motivo':'Pausa académica'},headers=self.h)
        rid=r.json['revision'];self.assertIsNone(self.propia()['academica'])
        self.assertEqual(self.cliente.get('/api/instructor-voluntario/formacion').json['publicaciones'],[])
        self._login();self.h={'X-CSRFToken':self._csrf_token()}
        self.cliente.patch(f'/api/5b/gestiones/{self.pid}/evaluaciones/ACADEMICA',json={'activa':True,'revision':rid,'motivo':'Reactivar'},headers=self.h)
        self.assertEqual(self.propia(),publicado)
        self._login();self.h={'X-CSRFToken':self._csrf_token()}
        p=self.cliente.get('/api/admin/5b/periodos').json['periodos'][0]
        self.cliente.delete(f'/api/admin/5b/periodos/{self.pid}',json={'motivo':'Retiro','nombre_anterior':p['nombre'],'ano_anterior':2026,'estado_anterior':p['estado']},headers=self.h)
        self.assertEqual(self.publicar().status_code,409);self.assertIsNone(self.propia())
        self.assertEqual(self.cliente.get('/api/instructor-voluntario/formacion').json['publicaciones'],[])
        with self.app.app_context():self.assertEqual(obtener_conexion().execute('SELECT count(*) FROM publicaciones_5b').fetchone()[0],1)

    def test_desempeno_no_modifica_firma_fecha_ni_version_publicada(self):
        self.preparar_publicable();self.publicar();v=self.vista();publicado=self.propia()
        self._login();self.h={'X-CSRFToken':self._csrf_token()};self.desempeno('DESEMPENO_JEFE','90')
        actual=self.vista();self.assertEqual(v['firma_fuentes'],actual['firma_fuentes']);self.assertFalse(actual['hay_cambios'])
        self.assertEqual(self.publicar().status_code,200);self.assertEqual(self.propia(),publicado)

    def test_republicar_otro_componente_conserva_version_oculta_y_su_fecha(self):
        self.preparar_publicable()
        with patch('sicose.publicaciones_5b.db._ahora_utc',return_value='2026-10-13T10:00:00+00:00'):self.publicar()
        ruta='/api/evaluaciones/personas/3/habilitacion'
        self.cliente.patch(ruta,json={'periodo_id':self.pid,'clave':'FISICA_1','habilitada':False},headers=self.h)
        self.assertEqual(self.cliente.patch(f'/api/formacion/participaciones/{self.participacion}',json={'revision':2,'estado':'Finalizado','puntaje':50,'fecha_finalizacion':'2026-03-01','motivo':'Puntos corregidos'},headers=self.h).status_code,200)
        with patch('sicose.publicaciones_5b.db._ahora_utc',return_value='2026-10-13T11:00:00+00:00'):self.assertEqual(self.publicar().status_code,201)
        p=self.propia();self.assertNotIn('60.00',str(p));self.assertEqual(p['academica']['valor'],50)
        self._login();self.h={'X-CSRFToken':self._csrf_token()}
        self.cliente.patch(ruta,json={'periodo_id':self.pid,'clave':'FISICA_1','habilitada':True},headers=self.h)
        p=self.propia();self.assertEqual(p['fisicas'][0]['nota'],'60.00');self.assertEqual(p['fisicas'][0]['publicada_en'],'2026-10-13T10:00:00+00:00')

    def test_publicacion_cero_no_cumplida_y_promedio_de_dos_ceros(self):
        self.preparar();self.fisica('FISICA_1','0','NO_CUMPLIDA');self.activar();self.url='/api/5b/personas/3/publicacion'
        self.assertEqual(self.publicar().status_code,201)
        p=self.propia();self.assertEqual((p['fisicas'][0]['nota'],p['fisicas'][0]['estado']),('0.00','NO_CUMPLIDA'))
        self.assertIsNone(p['academica']['valor']);self.assertIsNone(p['promedio_fisico'])
        self._login();self.h={'X-CSRFToken':self._csrf_token()};self.fisica('FISICA_2','0')
        self.assertEqual(self.publicar().status_code,201);self.assertEqual(self.propia()['promedio_fisico'],'0')

    def test_fuentes_obsoletas_csrf_inactivos_y_campos_arbitrarios(self):
        self.preparar_publicable();v=self.vista();self.corregir_fisica('90')
        self.assertEqual(self.publicar(v).status_code,409)
        body={'periodo_id':self.pid,'revision_publicada':0,'firma_fuentes':self.vista()['firma_fuentes'],'motivo':'Revisado'}
        self.assertEqual(self.cliente.post(self.url,json=body).status_code,400)
        self.assertEqual(self.cliente.post(self.url,json={**body,'nota':'100'},headers=self.h).status_code,400)
        with self.app.app_context():
            c=obtener_conexion();c.execute("UPDATE usuarios SET estado='INACTIVO' WHERE id=3");c.commit()
        self.assertFalse(self.vista()['puede_publicar']);self.assertEqual(self.publicar().status_code,409)
        self.assertEqual(self._login('voluntario.demo','Clave voluntario 123!').status_code,401)

    def test_concurrencia_publicacion_y_republicacion_cadena_unica(self):
        self.preparar_publicable();self.app.config['WTF_CSRF_ENABLED']=False
        clientes=[]
        for uid in ('1','2'):
            cli=self.app.test_client()
            with cli.session_transaction() as ses:ses['_user_id']=uid;ses['sicose_password_version']=1
            clientes.append(cli)
        for paso in range(2):
            v=self.vista();barrier=threading.Barrier(2)
            body={'periodo_id':self.pid,'revision_publicada':v['revision_publicada'],'firma_fuentes':v['firma_fuentes'],'motivo':'Revisión concurrente'}
            def guardar(cli):
                barrier.wait(timeout=5)
                return cli.post(self.url,json=body).status_code
            with ThreadPoolExecutor(max_workers=2) as pool:estados=list(pool.map(guardar,clientes))
            self.assertEqual(sorted(estados),[201,409])
            if paso==0:self.corregir_fisica('70')
        with self.app.app_context():self.assertEqual([r[0] for r in obtener_conexion().execute('SELECT revision FROM publicaciones_5b ORDER BY revision')],[1,2])

    def test_migracion_v20_preserva_sin_publicacion_automatica(self):
        self.preparar_publicable()
        with self.app.app_context():
            c=obtener_conexion();tablas=[r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT IN ('app_meta','publicaciones_5b')")]
            antes={t:[tuple(r) for r in c.execute(f'SELECT * FROM {t} ORDER BY rowid')] for t in tablas}
            c.execute('DROP TABLE publicaciones_5b');c.execute("UPDATE app_meta SET valor='20' WHERE clave='schema_version'");c.commit()
            inicializar_base_datos();inicializar_base_datos()
            for t in tablas:self.assertEqual(antes[t],[tuple(r) for r in c.execute(f'SELECT * FROM {t} ORDER BY rowid')],t)
            self.assertEqual(c.execute('SELECT count(*) FROM publicaciones_5b').fetchone()[0],0)
            self.assertEqual(c.execute("SELECT valor FROM app_meta WHERE clave='schema_version'").fetchone()[0],'22')
            self.assertEqual(c.execute('PRAGMA quick_check').fetchone()[0],'ok');self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(),[])
