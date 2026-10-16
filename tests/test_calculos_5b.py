"""Regla v2 y gestión anual; fuentes verificables, exactitud y privacidad."""
import re
import sqlite3
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
import test_app as fixtures
from sicose.db import obtener_conexion, inicializar_base_datos


class CalculosTestCase(unittest.TestCase):
    for _nombre, _valor in vars(fixtures.AplicacionTestCase).items():
        if (_nombre.startswith('_') and not _nombre.startswith('__')) or _nombre in ('setUp', 'tearDown'):
            locals()[_nombre] = _valor

    def preparar(self):
        _, self.pid = self._preparar_notas_5b()
        self.h = {'X-CSRFToken': self._csrf_token()}
        self.notas, self.fechas = {}, {}

    def fisica(self, fuente, valor, estado='CUMPLIDA'):
        url=f'/api/5b/periodos/{self.pid}/fisicas/{fuente}'
        r=self.cliente.post(url,json={'fecha':'2026-02-01','motivo':'Prueba común','anterior_id':None},headers=self.h)
        self.assertEqual(r.status_code,201,r.json);self.fechas[fuente]=r.json['id']
        body={'periodo_id':self.pid,'fuente':fuente,'nota_0_100':valor,'motivo':'Resultado explícito',
              'fisica':{'estado':estado,'fecha_realizacion':'2026-02-01' if estado=='CUMPLIDA' else None,'programacion_id':r.json['id'],'reprogramacion_id':None}}
        r=self.cliente.post('/api/5b/personas/3/notas',json=body,headers=self.h)
        self.assertEqual(r.status_code,201,r.json);self.notas[fuente]=r.json['id']

    def desempeno(self, fuente, valor):
        body={'periodo_id':self.pid,'fuente':fuente,'nota_0_100':valor}
        if fuente=='DESEMPENO_COMANDANTE':body['comandante_nombre']='Evaluador externo DEMO'
        r=self.cliente.post('/api/5b/personas/3/notas',json=body,headers=self.h)
        self.assertEqual(r.status_code,201,r.json);self.notas[fuente]=r.json['id']

    def curso(self, puntos, fecha='2026-03-01'):
        self.numero_curso = getattr(self, 'numero_curso', 0) + 1
        self.h={'X-CSRFToken':self._csrf_token()}
        r=self.cliente.post('/api/cursos',json={'nombre':f'Curso DEMO {self.numero_curso}','tipo':'Taller','entidad':'Entidad DEMO','fecha_inicio':'2020-01-01','fecha_fin':'2020-01-31','puntaje':25},headers=self.h)
        self.assertEqual(r.status_code,201,r.json);cid=r.json['id']
        r=self.cliente.post(f'/api/cursos/{cid}/participantes',json={'voluntario_ids':[3]},headers=self.h)
        self.assertEqual(r.status_code,201,r.json)
        p=self.cliente.get(f'/api/cursos/{cid}/participantes').json['participantes'][0]
        r=self.cliente.patch(f"/api/formacion/participaciones/{p['id']}",json={'revision':1,'estado':'Finalizado','puntaje':puntos,'fecha_finalizacion':fecha,'motivo':'Finalización individual'},headers=self.h)
        self.assertEqual(r.status_code,200,r.json)
        return p['id']

    def activar(self):
        self._login();self.h={'X-CSRFToken':self._csrf_token()}
        conf=self.cliente.get('/api/admin/5b/periodos').json['periodos'][0]['configuracion']
        self.conf=conf['id']
        r=self.cliente.post(f'/api/admin/5b/periodos/{self.pid}/calculo',json={'configuracion_id':self.conf,'regla':'ACUMULADO_TRES_V2','confirmar_fuentes':True},headers=self.h)
        self.assertEqual(r.status_code,201,r.json)

    def calculo(self):
        r=self.cliente.get(f'/api/5b/personas/3/calculo?periodo_id={self.pid}');self.assertEqual(r.status_code,200,r.json)
        return r.json['calculo']

    def test_formula_exacta_tope_detalle_y_sin_publicacion(self):
        self.preparar();self.fisica('FISICA_1','80.01');self.fisica('FISICA_2','80.02')
        self.desempeno('DESEMPENO_JEFE','60.01');self.desempeno('DESEMPENO_COMANDANTE','60.02')
        self.curso(80);self.curso(50)
        self.assertEqual(self.calculo()['estado'],'SIN_REGLA_NUEVA')
        self.activar();c=self.calculo()
        self.assertEqual(c['fisica'],'80.015');self.assertEqual(c['desempeno'],'60.015')
        # 240.030/3 = 80.010; redondear antes daría 80.013... -> 80.01 en este caso.
        self.assertEqual(c['resultado_conjunto'],'80.01')
        self.assertEqual((c['academica']['puntos_sin_tope'],c['academica']['valor'],len(c['academica']['detalle'])),(130,100,2))
        self.assertEqual({v['nota_id'] for v in c['fuentes'].values()},set(self.notas.values()))
        url=f'/api/5b/gestiones/{self.pid}/evaluaciones/FISICA_1'
        r=self.cliente.patch(url,json={'activa':False,'revision':0,'motivo':'Suspender física'},headers=self.h)
        self.assertEqual(r.status_code,200,r.json)
        incompleto=self.calculo();self.assertIsNone(incompleto['resultado_conjunto']);self.assertEqual(incompleto['faltantes'],['FISICA_1'])
        self.assertEqual(self.cliente.patch(url,json={'activa':True,'revision':r.json['revision'],'motivo':'Reactivar física'},headers=self.h).status_code,200)
        self.assertEqual(self.calculo()['resultado_conjunto'],'80.01')
        with self.app.app_context():
            conf=obtener_conexion().execute('SELECT regla,version FROM configuraciones_5b WHERE id=?',(self.conf,)).fetchone()
            self.assertEqual(tuple(conf),('PROMEDIO_TRES_V1',1))
        self._login('voluntario.demo','Clave voluntario 123!')
        self.assertEqual(self.cliente.get(f'/api/5b/personas/3/calculo?periodo_id={self.pid}').status_code,403)
        propias=self.cliente.get(f'/api/evaluaciones/propias?periodo_id={self.pid}').json
        for campo in ('resultado_conjunto','80.01','puntaje','nota_id','historial_id'):
            self.assertNotIn(campo,str(propias))

    def test_redondeo_mitad_hacia_arriba_sin_redondeos_intermedios(self):
        self.preparar();self.fisica('FISICA_1','0');self.fisica('FISICA_2','0.01')
        self.desempeno('DESEMPENO_JEFE','0');self.desempeno('DESEMPENO_COMANDANTE','0.01')
        self.curso(0);self.activar()
        self.assertEqual(self.calculo()['resultado_conjunto'],'0.00')
        # Si se redondearan ambas medias 0.005 a 0.01, saldría 0.01 (incorrecto).
        nid=self.notas['DESEMPENO_COMANDANTE']
        r=self.cliente.post('/api/5b/personas/3/notas',json={'periodo_id':self.pid,'fuente':'DESEMPENO_COMANDANTE','nota_0_100':'0.02','comandante_nombre':'DEMO','corregida_de_id':nid},headers=self.h)
        self.assertEqual(r.status_code,201)
        self.assertEqual(self.calculo()['resultado_conjunto'],'0.01') # exacto 0.005, mitad arriba.

    def test_pendiente_sin_formacion_y_cero_confirmado_reprogramado(self):
        self.preparar();self.fisica('FISICA_1','0','NO_CUMPLIDA');self.fisica('FISICA_2','0')
        self.desempeno('DESEMPENO_JEFE','0');self.desempeno('DESEMPENO_COMANDANTE','0');self.activar()
        c=self.calculo();self.assertIsNone(c['resultado_conjunto']);self.assertEqual(c['faltantes'],['ACADEMICA'])
        self.curso(0);self.assertEqual(self.calculo()['resultado_conjunto'],'0.00')
        r=self.cliente.post(f'/api/5b/periodos/{self.pid}/fisicas/FISICA_1/personas/3',json={'fecha':'2026-12-01','motivo':'Extraordinaria','anterior_id':None,'programacion_id':self.fechas['FISICA_1']},headers=self.h)
        self.assertEqual(r.status_code,201);self.assertEqual(self.calculo()['resultado_conjunto'],'0.00')

    def test_imputacion_unica_correccion_cambio_de_ano_y_no_adopcion_manual(self):
        self.preparar()
        r=self.cliente.post('/api/5b/personas/3/notas',json={'periodo_id':self.pid,'fuente':'FISICA_1','nota_0_100':'100'},headers=self.h)
        self.assertEqual(r.status_code,201)
        pid=self.curso(75);self.activar();c=self.calculo()
        self.assertEqual(c['academica']['valor'],75);self.assertIn('FISICA_1',c['faltantes'])
        self.assertFalse(c['fuentes']['FISICA_1']['incluida'])
        r=self.cliente.patch(f'/api/formacion/participaciones/{pid}',json={'revision':2,'estado':'Finalizado','puntaje':40,'fecha_finalizacion':'2025-12-31','motivo':'Corrección de año'},headers=self.h)
        self.assertEqual(r.status_code,200,r.json);self.assertIsNone(self.calculo()['academica']['valor'])
        r=self.cliente.patch(f'/api/formacion/participaciones/{pid}',json={'revision':3,'estado':'Finalizado','puntaje':40,'fecha_finalizacion':'2026-02-01','motivo':'Corrección año vigente'},headers=self.h)
        self.assertEqual(r.status_code,200);self.assertEqual(self.calculo()['academica']['puntos_sin_tope'],40)
        historia=self.cliente.get(f'/api/formacion/participaciones/{pid}/historial').json['historial']
        self.assertEqual([p['puntaje'] for p in historia],[None,75,40,40])

    def test_activacion_anual_personal_historial_permisos_y_concurrencia(self):
        self.preparar();self.fisica('FISICA_1','50');ruta=f'/api/5b/gestiones/{self.pid}/evaluaciones/FISICA_1'
        body={'activa':False,'revision':0,'motivo':'Desactivar este año'}
        self.assertEqual(self.cliente.patch(ruta,json=body).status_code,400)
        r=self.cliente.patch(ruta,json=body,headers=self.h);self.assertEqual(r.status_code,200,r.json);rid=r.json['revision']
        self.assertEqual(self.cliente.patch(ruta,json=body,headers=self.h).status_code,409)
        datos=self.cliente.get(f'/api/evaluaciones/tabla?periodo_id={self.pid}').json['personas'][0]
        self.assertFalse(datos['evaluaciones'][0]['activa']);self.assertTrue(datos['evaluaciones'][0]['habilitada'])
        self.assertEqual(datos['evaluaciones'][0]['nota'],'50.00')
        self.assertEqual(self.cliente.post(f'/api/5b/periodos/{self.pid}/fisicas/FISICA_1/personas/3',json={'fecha':'2026-03-01','motivo':'Extraordinaria','anterior_id':None,'programacion_id':self.fechas['FISICA_1']},headers=self.h).status_code,409)
        self.assertEqual(self.cliente.patch(f'/api/5b/gestiones/{self.pid}/evaluaciones/PSICOMETRICAS',json={'activa':True,'revision':0,'motivo':'Intento sin aprobación'},headers=self.h).status_code,409)
        self.activar();self.assertIn('FISICA_1',self.calculo()['bloqueos'])
        self.app.config['WTF_CSRF_ENABLED']=False;clientes=[]
        for _ in range(2):
            cli=self.app.test_client()
            with cli.session_transaction() as ses:ses['_user_id']='2';ses['sicose_password_version']=1
            clientes.append(cli)
        barrier=threading.Barrier(2)
        def guardar(cli):
            barrier.wait(timeout=5)
            return cli.patch(ruta,json={'activa':True,'revision':rid,'motivo':'Reactivar'}).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:estados=list(pool.map(guardar,clientes))
        self.assertEqual(sorted(estados),[200,409])
        historia=self.cliente.get(f'/api/5b/gestiones/{self.pid}/evaluaciones').json['historial']
        self.assertEqual([h['activa'] for h in historia],[0,1])
        self._login('voluntario.demo','Clave voluntario 123!')
        self.assertEqual(self.cliente.patch(ruta,json=body).status_code,403)

    def test_baja_gestion_conserva_y_libera_ciclo_sin_cerrar(self):
        self.preparar();self.fisica('FISICA_1','0','NO_CUMPLIDA');self.curso(10);self.activar()
        self._login('instructor.demo','Clave instructor 123!');self.h={'X-CSRFToken':self._csrf_token()}
        p=self.cliente.get('/api/admin/5b/periodos').json['periodos'][0]
        body={'motivo':'Retiro anual','nombre_anterior':p['nombre'],'ano_anterior':2026,'estado_anterior':p['estado']}
        url=f'/api/admin/5b/periodos/{self.pid}'
        self.assertEqual(self.cliente.delete(url,json=body).status_code,400)
        self.assertEqual(self.cliente.delete(url,json=body,headers=self.h).status_code,200)
        self.assertEqual(self.cliente.delete(url,json=body,headers=self.h).status_code,409)
        valores=self.cliente.get('/api/admin/5b/periodos').json
        self.assertEqual(valores['periodos'],[]);self.assertEqual(len(valores['retiradas']),1)
        self.assertEqual(self.cliente.get('/api/5b/opciones').json['periodos'],[])
        self.assertEqual(self.cliente.get(f'/api/evaluaciones/tabla?periodo_id={self.pid}').status_code,200)
        self.assertEqual(self.cliente.post(f'/api/5b/periodos/{self.pid}/fisicas/FISICA_2',json={'fecha':'2026-02-02','motivo':'Nueva','anterior_id':None},headers=self.h).status_code,409)
        self.assertEqual(self.cliente.patch('/api/evaluaciones/personas/3/habilitacion',json={'periodo_id':self.pid,'clave':'FISICA_1','habilitada':False},headers=self.h).status_code,409)
        self.assertEqual(self.cliente.post('/api/5b/personas/3/notas',json={'periodo_id':self.pid,'fuente':'FISICA_1','nota_0_100':'50','corregida_de_id':self.notas['FISICA_1'],'motivo':'Corrección','fisica':{'estado':'CUMPLIDA','fecha_realizacion':'2026-02-01','programacion_id':self.fechas['FISICA_1'],'reprogramacion_id':None}},headers=self.h).status_code,409)
        with self.app.app_context():
            c=obtener_conexion();self.assertEqual(c.execute('SELECT estado FROM periodos WHERE id=?',(self.pid,)).fetchone()[0],'ACTIVO')
            self.assertEqual(c.execute('SELECT count(*) FROM notas_operativas').fetchone()[0],1)
            c.execute("INSERT INTO periodos(nombre,fecha_inicio,fecha_fin,estado) VALUES ('Otro ciclo','2027-01-01','2027-12-31','ACTIVO')");c.commit()
            with self.assertRaises(sqlite3.IntegrityError):c.execute("INSERT INTO periodos(nombre,fecha_inicio,fecha_fin,estado) VALUES ('Tercero','2028-01-01','2028-12-31','ACTIVO')")
            c.rollback()

    def test_menu_sin_duplicados_catalogo_separado_y_rutas_funcionales(self):
        for username,pw in [('admin.demo','Clave demo segura 123!'),('instructor.demo','Clave instructor 123!')]:
            self._login(username,pw)
            html=self.cliente.get('/',follow_redirects=True).data.decode()
            nav=html.split('<nav class="navegacion">')[1].split('</nav>')[0]
            enlaces=re.findall(r'href="([^"]+)"',nav)
            self.assertEqual(len(enlaces),len(set(enlaces)))
            self.assertIn('Gestión',nav);self.assertIn('Evaluaciones',nav)
            self.assertNotIn('Notas y resultados',nav);self.assertNotIn('Notas y Resultados',nav)
            self.assertNotIn('Notas e historial',nav);self.assertNotIn('Notas operativas 5B',nav)
            for href in enlaces:self.assertEqual(self.cliente.get(href,follow_redirects=True).status_code,200,href)
            catalogo=self.cliente.get('/gestion/evaluaciones').data.decode()
            for viejo in ('id="periodo-form"','id="asignacion-form"','id="periodos-lista"'):self.assertNotIn(viejo,catalogo)

    def test_regla_explicita_permisos_concurrencia_y_ano_unico(self):
        self.preparar()
        with self.app.app_context():conf=obtener_conexion().execute('SELECT id FROM configuraciones_5b WHERE periodo_id=?',(self.pid,)).fetchone()[0]
        ruta=f'/api/admin/5b/periodos/{self.pid}/calculo'
        body={'configuracion_id':conf,'regla':'ACUMULADO_TRES_V2','confirmar_fuentes':True}
        self.assertEqual(self.cliente.post(ruta,json=body,headers=self.h).status_code,403)
        self._login();self.h={'X-CSRFToken':self._csrf_token()}
        self.assertEqual(self.cliente.post(ruta,json=body).status_code,400)
        self.assertEqual(self.cliente.post(ruta,json={**body,'confirmar_fuentes':False},headers=self.h).status_code,400)
        self.app.config['WTF_CSRF_ENABLED']=False;clientes=[]
        for _ in range(2):
            cli=self.app.test_client()
            with cli.session_transaction() as ses:ses['_user_id']='1';ses['sicose_password_version']=1
            clientes.append(cli)
        barrier=threading.Barrier(2)
        def guardar(cli):
            barrier.wait(timeout=5)
            return cli.post(ruta,json=body).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:estados=list(pool.map(guardar,clientes))
        self.assertEqual(sorted(estados),[201,409])
        p=self.cliente.get('/api/admin/5b/periodos').json['periodos'][0]
        self.assertEqual(self.cliente.delete(f'/api/admin/5b/periodos/{self.pid}',json={'motivo':'Retiro','nombre_anterior':p['nombre'],'ano_anterior':2026,'estado_anterior':p['estado']}).status_code,200)
        nuevo=self.cliente.post('/api/admin/5b/periodos',json={'nombre':'Otra gestión mismo año','ano':2026}).json['id']
        conf2,_=self._configurar_periodo_5b(nuevo)
        self.assertEqual(self.cliente.post(f'/api/admin/5b/periodos/{nuevo}/publicar',json={'revision':conf2['revision']}).status_code,200)
        self.assertEqual(self.cliente.post(f'/api/admin/5b/periodos/{nuevo}/calculo',json={**body,'configuracion_id':conf2['id']}).status_code,409)

    def test_cuenta_inactiva_consulta_y_correcciones_bloqueadas(self):
        self.preparar();self.fisica('FISICA_1','60');pid=self.curso(30);self.activar()
        with self.app.app_context():
            c=obtener_conexion();c.execute("UPDATE usuarios SET estado='INACTIVO' WHERE id=3");c.commit()
        self.assertEqual(self.calculo()['academica']['valor'],30)
        self.assertEqual(self.cliente.patch(f'/api/formacion/participaciones/{pid}',json={'revision':2,'estado':'Finalizado','puntaje':40,'fecha_finalizacion':'2026-04-01','motivo':'Corrección'},headers=self.h).status_code,409)
        self.assertEqual(self.cliente.patch('/api/evaluaciones/personas/3/habilitacion',json={'periodo_id':self.pid,'clave':'FISICA_1','habilitada':False},headers=self.h).status_code,409)
        self.assertEqual(self._login('voluntario.demo','Clave voluntario 123!').status_code,401)

    def test_academica_manual_historica_se_conserva_sin_ser_acumulado(self):
        self.preparar()
        with self.app.app_context():
            c=obtener_conexion();ref=c.execute("INSERT INTO capacitaciones(voluntario_id,nombre,fecha) VALUES (3,'Respaldo antiguo','2026-02-01')").lastrowid;c.commit()
        body={'periodo_id':self.pid,'fuente':'ACADEMICA','nota_0_100':'99','motivo':'Manual anterior','capacitaciones':[ref]}
        r=self.cliente.post('/api/5b/personas/3/notas',json=body,headers=self.h);self.assertEqual(r.status_code,201)
        nid=r.json['id'];self.activar()
        self.assertIsNone(self.calculo()['academica']['valor'])
        self.assertEqual(self.cliente.post('/api/5b/personas/3/notas',json={**body,'corregida_de_id':nid},headers=self.h).status_code,409)
        historial=self.cliente.get(f'/api/5b/personas/3?periodo_id={self.pid}').json['notas']
        self.assertEqual(historial[0]['nota_0_100'],'99.00')

    def test_migracion_v19_no_adopta_notas_ni_reglas(self):
        self.preparar();self.fisica('FISICA_1','0','NO_CUMPLIDA')
        nuevas={'bajas_gestion','historial_gestiones','activaciones_gestion','reglas_calculo_5b'}
        with self.app.app_context():
            c=obtener_conexion();tablas=[r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name!='app_meta'") if r[0] not in nuevas]
            anteriores={t:[tuple(r) for r in c.execute(f'SELECT * FROM {t} ORDER BY rowid')] for t in tablas}
            for t in nuevas:c.execute(f'DROP TABLE {t}')
            c.execute("UPDATE app_meta SET valor='19' WHERE clave='schema_version'");c.commit()
            inicializar_base_datos();inicializar_base_datos()
            for t in tablas:self.assertEqual(anteriores[t],[tuple(r) for r in c.execute(f'SELECT * FROM {t} ORDER BY rowid')],t)
            for t in nuevas:self.assertEqual(c.execute(f'SELECT count(*) FROM {t}').fetchone()[0],0)
            self.assertEqual(c.execute('PRAGMA quick_check').fetchone()[0],'ok');self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(),[])
            self.assertEqual(c.execute("SELECT valor FROM app_meta WHERE clave='schema_version'").fetchone()[0],'27')
