"""Circuito actual, nueve entradas, propuestas versionadas y privacidad."""
import json
import sqlite3
from pathlib import Path
from unittest.mock import patch
import unittest
from concurrent.futures import ThreadPoolExecutor
import test_modelo_anual as anual
from sicose.db import obtener_conexion, inicializar_base_datos
from sicose.instrumentos_actuales import CATALOGO, INVERSOS, formulario, firma, puntuar
from sicose.recomendaciones import MODELO_SHA, cargar_modelo
from sicose.reporte_individual import datos_individual, generar_individual


class RecomendacionesTestCase(unittest.TestCase):
    for nombre, valor in vars(anual.ModeloAnualTestCase).items():
        if (nombre.startswith('_') and not nombre.startswith('__')) or nombre in ('setUp','tearDown','preparar_anual','datos','nota','cierre','operacion_demo','puntuar_operacion'):
            locals()[nombre]=valor

    def login_rol(self, rol):
        credenciales={'admin':('admin.demo','Clave demo segura 123!'), 'jefe':('instructor.demo','Clave instructor 123!'), 'propia':('voluntario.demo','Clave voluntario 123!')}
        self._login(*credenciales[rol]);self.h={'X-CSRFToken':self._csrf_token()}

    def revisar(self):
        for rol in ('admin','jefe'):
            self.login_rol(rol)
            for clave in CATALOGO:
                r=self.cliente.post(self.url+f'/pruebas/{clave}/revision',json={'firma_formulario':firma(clave),'observacion':'Revisión de versión, puntuación y conservación por Gestión.','confirmar':True},headers=self.h)
                self.assertEqual(r.status_code,200,r.json)

    def habilitar(self):
        self.revisar()
        r=self.cliente.put(self.url+'/simulacro-tlx',json={'nombre':'Simulacro común de prueba','fecha':'2025-09-01','revision':0,'realizado':True},headers=self.h)
        self.assertEqual(r.status_code,200,r.json)
        for clave in CATALOGO:
            r=self.cliente.patch(self.url+f'/pruebas/{clave}',json={'activa':True,'revision':0},headers=self.h)
            self.assertEqual(r.status_code,200,r.json)

    def completar(self):
        self.preparar_anual();self.habilitar();self.login_rol('propia')
        for clave in CATALOGO:
            r=self.cliente.post(self.url+f'/pruebas/{clave}/finalizar',json=({'revision':0,'respuestas':[50]*6,'confirmar_simulacro':True} if clave=='NASATLX' else {'revision':0,'respuestas':[3]*len(CATALOGO[clave]['items'])}),headers=self.h)
            self.assertEqual(r.status_code,200,r.json)
        self.login_rol('jefe')
        self.rec=self.url+'/personas/3/recomendacion'
        return self.cliente.get(self.rec).json

    def generar(self):
        d=self.cliente.get(self.rec).json
        r=self.cliente.post(self.rec,json={'firma_fuentes':d['firma_fuentes'],'anterior_id':d['ultima_id']},headers=self.h)
        self.assertIn(r.status_code,(200,201),r.json)
        return r.json['id']

    def confirmar(self,rid,observacion='Revisadas las entradas y salida; acompañamiento orientativo.'):
        d=self.cliente.get(self.rec).json
        return self.cliente.post(self.rec+f'/{rid}/confirmar',json={'firma_fuentes':d['firma_fuentes'],'observacion':observacion,'confirmar':True},headers=self.h)

    def test_puntuacion_gse_mini_por_item_y_extremos(self):
        self.assertEqual(puntuar('GSE',[1]*10)['autoeficacia']['valor'],10)
        self.assertEqual(puntuar('GSE',[4]*10)['autoeficacia']['valor'],40)
        for alto,esperado in ((True,20),(False,4)):
            respuestas=[(1 if i in INVERSOS else 5) if alto else (5 if i in INVERSOS else 1) for i in range(1,21)]
            self.assertEqual({v['valor'] for v in puntuar('MINIIPIP',respuestas).values()},{esperado})
        base=puntuar('MINIIPIP',[3]*20)
        for i in range(1,21):
            valores=[3]*20;valores[i-1]=4
            diferencia=sum(v['valor'] for v in puntuar('MINIIPIP',valores).values())-sum(v['valor'] for v in base.values())
            self.assertEqual(diferencia,-1 if i in INVERSOS else 1)
        for v in (0,True,5,None):
            with self.assertRaises(ValueError):puntuar('GSE',[v]*10)

    def test_revision_de_ambos_roles_y_por_gestion_sin_autoactivar(self):
        self.preparar_anual()
        self.assertEqual(self.cliente.patch(self.url+'/pruebas/GSE',json={'activa':True,'revision':0},headers=self.h).status_code,409)
        self.login_rol('admin')
        body={'firma_formulario':firma('GSE'),'observacion':'Versión revisada','confirmar':True}
        self.assertEqual(self.cliente.post(self.url+'/pruebas/GSE/revision',json=body).status_code,400)
        self.assertEqual(self.cliente.post(self.url+'/pruebas/GSE/revision',json=body,headers=self.h).status_code,200)
        self.assertEqual(self.cliente.patch(self.url+'/pruebas/GSE',json={'activa':True,'revision':0},headers=self.h).status_code,409)
        self.login_rol('jefe')
        self.assertEqual(self.cliente.post(self.url+'/pruebas/GSE/revision',json={**body,'firma_formulario':'obsoleta'},headers=self.h).status_code,409)
        self.assertEqual(self.cliente.post(self.url+'/pruebas/GSE/revision',json=body,headers=self.h).status_code,200)
        self.assertEqual(self.cliente.post(self.url+'/pruebas/GSE/revision',json=body,headers=self.h).status_code,200)
        d=self.cliente.get(self.url+'/pruebas').json
        self.assertTrue(d['pruebas'][0]['revisada']);self.assertFalse(d['pruebas'][0]['activa'])
        self.assertFalse(d['pruebas'][1]['revisada'])
        with self.app.app_context():
            c=obtener_conexion();self.assertEqual(c.execute('SELECT count(*) FROM revisiones_pruebas').fetchone()[0],2)

    def test_avance_conflicto_finalizacion_unica_y_privacidad(self):
        self.preparar_anual();self.habilitar();self.login_rol('propia')
        ruta=self.url+'/pruebas/GSE'
        form=self.cliente.get(ruta+'/propia').json
        self.assertEqual(form['formulario']['minimo_respuesta'],1)
        self.assertIn('Gestión',form['formulario']['politica'])
        self.assertEqual(self.cliente.put(ruta+'/propia',json={'revision':0,'respuestas':[2,None]+[None]*8},headers=self.h).status_code,200)
        self.assertEqual(self.cliente.put(ruta+'/propia',json={'revision':0,'respuestas':[2]*10},headers=self.h).status_code,409)
        self.login_rol('jefe')
        d=self.cliente.get(self.url+'/personas/3/pruebas').json['pruebas'][0]
        self.assertNotIn('respuestas',d);self.assertNotIn('subescalas',d)
        self.login_rol('propia')
        self.assertEqual(self.cliente.get(ruta+'/propia').json['respuestas'][0],2)
        self.assertEqual(self.cliente.post(ruta+'/finalizar',json={'revision':1,'respuestas':[2]*10},headers=self.h).status_code,200)
        self.assertEqual(self.cliente.get(ruta+'/propia').json,{'estado':'Completada'})
        self.assertEqual(self.cliente.post(ruta+'/finalizar',json={'revision':2,'respuestas':[4]*10},headers=self.h).status_code,409)
        for url in (self.url+'/pruebas', self.url+'/personas/3/pruebas',self.url+'/personas/3/recomendacion'):
            self.assertEqual(self.cliente.get(url).status_code,403)
        self.assertEqual(self.cliente.get('/api/pruebas/propias?usuario_id=2').status_code,409)
        self.login_rol('admin')
        resultado=self.cliente.get(self.url+'/personas/3/pruebas').json['pruebas'][0]
        self.assertEqual(resultado['subescalas']['autoeficacia']['valor'],20)
        self.assertEqual(resultado['respuestas'],[2]*10)

    def test_quince_entradas_con_ceros_oficiales_y_propuesta_idempotente(self):
        d=self.completar()
        calculo=self.datos()['calculo']
        self.assertEqual(calculo['estado'],'COMPLETO')
        self.assertTrue(calculo['modelo']['listo_para_inferencia'])
        self.assertEqual([e['estado'] for e in calculo['entradas'][-2:]],['COMPLETADA','COMPLETADA'])
        self.assertTrue(d['puede_generar'],d)
        self.assertEqual(list(d['entradas'].values()).count(None),0)
        self.assertEqual(d['entradas']['gse_autoeficacia'],30)
        self.assertEqual(d['entradas']['fisica'],0)
        rid=self.generar();self.assertEqual(self.generar(),rid)
        d=self.cliente.get(self.rec).json
        self.assertEqual(len(d['historial']),1);self.assertEqual(d['historial'][0]['estado'],'Propuesta')
        self.assertEqual(d['historial'][0]['modelo_sha256'],MODELO_SHA)
        self.assertFalse(d['historial'][0]['resultado']['validacion_personal'])
        self.assertEqual(self.cliente.post(self.rec,json={'firma_fuentes':d['firma_fuentes'],'anterior_id':rid,'entradas':[100]*9},headers=self.h).status_code,409)
        self.assertEqual(self.cliente.get(self.rec).headers['Cache-Control'],'private, no-store')

    def test_concurrencia_no_duplica_propuestas_ni_sobrescribe_confirmacion(self):
        d=self.completar()
        with self.cliente.session_transaction() as s:sesion=dict(s)
        clientes=[self.app.test_client(),self.app.test_client()]
        for cliente in clientes:
            with cliente.session_transaction() as s:s.update(sesion)
        payload={'firma_fuentes':d['firma_fuentes'],'anterior_id':None}
        with ThreadPoolExecutor(max_workers=2) as pool:
            resultados=list(pool.map(lambda c:c.post(self.rec,json=payload,headers=self.h).status_code,clientes))
        self.assertEqual(sorted(resultados),[201,409])
        rid=self.cliente.get(self.rec).json['ultima_id']
        with ThreadPoolExecutor(max_workers=2) as pool:
            resultados=list(pool.map(lambda par:par[0].post(self.rec+f'/{rid}/confirmar',json={'firma_fuentes':d['firma_fuentes'],'confirmar':True,'observacion':par[1]},headers=self.h).status_code,zip(clientes,['Constancia uno','Constancia dos'])))
        self.assertEqual(sorted(resultados),[200,409])
        with self.app.app_context():
            c=obtener_conexion();self.assertEqual(c.execute('SELECT count(*) FROM recomendaciones').fetchone()[0],1)
            self.assertEqual(c.execute('SELECT count(*) FROM confirmaciones_recomendacion').fetchone()[0],1)

    def test_cambio_academico_de_operacion_desactualiza(self):
        self.completar();rid=self.generar();oid=self.operacion_demo()
        r=self.puntuar_operacion(oid,50);self.assertEqual(r.status_code,201,r.json)
        d=self.cliente.get(self.rec).json
        self.assertEqual(d['historial'][0]['estado'],'Desactualizada')
        self.assertEqual(d['entradas']['academica'],50)
        nuevo=self.generar();self.assertNotEqual(nuevo,rid)

    def test_no_imputa_pruebas_pendientes_y_controla_csrf(self):
        self.preparar_anual();self.rec=self.url+'/personas/3/recomendacion'
        d=self.cliente.get(self.rec).json
        self.assertFalse(d['puede_generar']);self.assertIsNone(d['entradas']['gse_autoeficacia'])
        payload={'firma_fuentes':d['firma_fuentes'],'anterior_id':None}
        self.assertEqual(self.cliente.post(self.rec,json=payload).status_code,400)
        self.assertEqual(self.cliente.post(self.rec,json=payload,headers=self.h).status_code,409)

    def test_confirmacion_separada_pdf_y_version_desactualizada(self):
        self.completar();rid=self.generar()
        with self.app.app_context():
            datos=datos_individual(obtener_conexion(),3);self.assertIsNone(datos['recomendacion'])
        self.assertEqual(self.confirmar(rid,'').status_code,409)
        self.assertEqual(self.confirmar(rid).status_code,200)
        self.assertEqual(self.confirmar(rid).status_code,200)
        self.assertEqual(self.confirmar(rid,'Otro texto').status_code,409)
        with self.app.app_context():
            datos=datos_individual(obtener_conexion(),3)
            self.assertEqual(datos['recomendacion']['id'],rid)
            self.assertTrue(generar_individual(datos).getvalue().startswith(b'%PDF'))
            anterior=obtener_conexion().execute('SELECT resultado_json FROM recomendaciones WHERE id=?',(rid,)).fetchone()[0]
        r=self.nota('DESEMPENO_JEFE',70);self.assertEqual(r.status_code,201,r.json)
        d=self.cliente.get(self.rec).json;self.assertEqual(d['historial'][0]['estado'],'Desactualizada')
        self.assertEqual(self.confirmar(rid).status_code,409)
        with self.app.app_context():
            c=obtener_conexion();self.assertIsNone(datos_individual(c,3)['recomendacion'])
            self.assertEqual(c.execute('SELECT resultado_json FROM recomendaciones WHERE id=?',(rid,)).fetchone()[0],anterior)
        nuevo=self.generar();self.assertNotEqual(nuevo,rid)
        self.assertEqual(self.confirmar(nuevo).status_code,200)
        d=self.cliente.get(self.rec).json;self.assertEqual([f['estado'] for f in d['historial']],['Confirmada','Desactualizada'])

    def test_conflictos_de_fuentes_y_desactivacion_conservan_historial(self):
        d=self.completar();rid=self.generar()
        self.assertEqual(self.cliente.patch(self.url+'/pruebas/GSE',json={'activa':False,'revision':1},headers=self.h).status_code,200)
        self.assertEqual(self.cliente.get(self.rec).json['historial'][0]['estado'],'Desactualizada')
        self.assertEqual(self.cliente.patch(self.url+'/pruebas/GSE',json={'activa':True,'revision':2},headers=self.h).status_code,200)
        self.assertEqual(self.cliente.get(self.rec).json['historial'][0]['estado'],'Desactualizada')
        self.assertEqual(self.cliente.post(self.rec,json={'firma_fuentes':d['firma_fuentes'],'anterior_id':rid},headers=self.h).status_code,409)
        self.assertNotEqual(self.generar(),rid)

    def test_cierre_reapertura_e_inactivo(self):
        self.completar();rid=self.generar();self.assertEqual(self.confirmar(rid).status_code,200)
        self.login_rol('admin');r=self.cierre();self.assertEqual(r.status_code,201,r.json)
        d=self.cliente.get(self.rec).json
        self.assertFalse(d['puede_generar']);self.assertEqual(d['historial'][0]['estado'],'Confirmada')
        self.assertEqual(self.cliente.post(self.rec,json={'firma_fuentes':d['firma_fuentes'],'anterior_id':rid},headers=self.h).status_code,409)
        self.assertEqual(self.confirmar(rid).status_code,409)
        self.assertEqual(self.cliente.post(self.url+'/pruebas/GSE/revision',json={},headers=self.h).status_code,409)
        with self.app.app_context():
            c=obtener_conexion();cierre=c.execute('SELECT id FROM cierres_5b WHERE periodo_id=? ORDER BY id DESC LIMIT 1',(self.pid,)).fetchone()[0]
        r=self.cliente.post(f'/api/admin/5b/periodos/{self.pid}/reabrir',json={'cierre_id':cierre,'motivo':'Reapertura para corrección'},headers=self.h)
        self.assertEqual(r.status_code,200,r.json)
        self.assertTrue(self.cliente.get(self.rec).json['puede_generar'])
        with self.app.app_context():
            c=obtener_conexion();c.execute("UPDATE usuarios SET estado='INACTIVO' WHERE id=3");c.commit()
        d=self.cliente.get(self.rec).json;self.assertFalse(d['puede_generar'])
        self.assertEqual(self.cliente.post(self.rec,json={'firma_fuentes':d['firma_fuentes'],'anterior_id':rid},headers=self.h).status_code,409)

    def test_pesos_fijados_y_modelo_no_disponible(self):
        self.completar()
        with patch('sicose.recomendaciones.MODELO_PATH',Path('.tmp/modelo-inexistente.json')):
            d=self.cliente.get(self.rec).json;self.assertFalse(d['puede_generar']);self.assertIn('Modelo seleccionado no disponible.',d['faltantes'])
        with patch('sicose.recomendaciones.MODELO_SHA','otra'):
            self.assertFalse(self.cliente.get(self.rec).json['puede_generar'])
        with self.app.app_context():
            self.assertEqual(cargar_modelo().exportar()['arquitectura'],[15,6,4])

    def test_prioridad_unica_con_empate_e_historial_inmutable(self):
        self.completar()
        modelo=cargar_modelo()
        with patch.object(type(modelo),'adelante',return_value=([0]*15,[0]*6,[.8,.5,.8,.1])):
            rid=self.generar()
        d=self.cliente.get(self.rec).json['historial'][0]
        self.assertEqual(d['resultado']['estado_modelo'],'PROPUESTA')
        self.assertEqual(d['resultado']['criterio_seleccion'],'ARGMAX_V1')
        self.assertEqual(d['resultado']['salida_prioritaria'],'preparacion_progresiva_y_confianza')
        self.assertEqual(len(d['resultado']['sugerencias']),1)
        self.assertEqual(d['resultado']['margen_activacion'],0)
        self.assertEqual(len(d['resultado']['empates_maximos']),2)
        self.assertEqual(self.confirmar(rid,'Se revisa la línea prioritaria y el empate con otra salida.').status_code,200)
        with self.app.app_context():
            c=obtener_conexion();antes=[tuple(f) for f in c.execute('SELECT * FROM recomendaciones')]
            inicializar_base_datos();inicializar_base_datos()
            self.assertEqual(antes,[tuple(f) for f in c.execute('SELECT * FROM recomendaciones')])
            for sql in ('DELETE FROM recomendaciones','UPDATE recomendaciones SET firma_fuentes=\'otra\'','DELETE FROM confirmaciones_recomendacion','DELETE FROM intentos_pruebas','UPDATE intentos_pruebas SET respuestas_json=\'[]\''):
                with self.assertRaises(sqlite3.IntegrityError):c.execute(sql)
                c.rollback()
            self.assertEqual(c.execute('PRAGMA quick_check').fetchone()[0],'ok')
            self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(),[])
