"""Bajas, permisos, ceros, ejemplos y privacidad del espacio reorganizado."""
import unittest
from concurrent.futures import ThreadPoolExecutor
import test_modelo_anual as base
from sicose.db import obtener_conexion, inicializar_base_datos


class OrganizacionTestCase(unittest.TestCase):
    for nombre,valor in vars(base.ModeloAnualTestCase).items():
        if not nombre.startswith('test_') and not nombre.startswith('__'):
            locals()[nombre]=valor

    def curso(self):
        d={'nombre':'Curso retiro DEMO','tipo':'Taller','entidad':'Entidad DEMO','fecha_inicio':'2025-08-15','fecha_fin':'2025-09-01','puntaje':35}
        r=self.cliente.post('/api/cursos',json=d,headers=self.h);self.assertEqual(r.status_code,201,r.json)
        self.cid=r.json['id'];return self.cid

    def participante(self):
        cid=self.curso();self.assertEqual(self.cliente.post(f'/api/cursos/{cid}/participantes',json={'voluntario_ids':[3]},headers=self.h).status_code,201)
        return self.cliente.get(f'/api/cursos/{cid}/participantes').json['participantes'][0]

    def test_eliminar_gestion_vacia_y_proteger_ceros_oficiales(self):
        self.preparar_anual()
        r=self.cliente.post(self.base,json={'nombre':'Gestión vacía DEMO','fecha_inicio':'2027-01-01','fecha_fin':'2027-12-31'},headers=self.h);pid=r.json['id']
        d={'motivo':'Eliminación DEMO','nombre_anterior':'Gestión vacía DEMO','estado_anterior':'BORRADOR'}
        self.assertEqual(self.cliente.delete(f'/api/gestiones/{pid}/eliminar',json={**d,'nombre_anterior':'Otra'},headers=self.h).status_code,409)
        self.assertEqual(self.cliente.delete(f'/api/gestiones/{pid}/eliminar',json=d,headers=self.h).status_code,200)
        self.assertEqual(self.cliente.get(self.base+f'/{pid}').status_code,404)
        d={'motivo':'No destruir resultados','nombre_anterior':'Gestión propia DEMO','estado_anterior':'ACTIVO'}
        self.assertEqual(self.cliente.delete(f'/api/gestiones/{self.pid}/eliminar',json=d,headers=self.h).status_code,409)
        self.assertEqual(len(self.datos()['historial']['notas']),5)

    def test_curso_sin_participacion_eliminado_y_con_participacion_baja(self):
        self.preparar_anual();cid=self.curso()
        self.assertEqual(self.cliente.delete(f'/api/cursos/{cid}',json={'motivo':'Prueba DEMO'},headers=self.h).json['baja'],False)
        p=self.participante();cid=self.cid
        self.assertEqual(self.cliente.delete(f'/api/cursos/{cid}',json={'motivo':'Baja DEMO'},headers=self.h).json['baja'],True)
        self.assertNotIn(cid,[c['id'] for c in self.cliente.get('/api/cursos').json['cursos']])
        self.assertEqual(len(self.cliente.get(f'/api/cursos/{cid}/participantes').json['participantes']),1)
        self.assertEqual(self.cliente.post(f'/api/cursos/{cid}/participantes',json={'voluntario_ids':[3]},headers=self.h).status_code,400)
        self.assertEqual(self.cliente.patch(f'/api/cursos/{cid}',json={'nombre':'Cambio'},headers=self.h).status_code,409)

    def test_retirada_recalcula_conserva_historial_y_bloquea_gestion_cerrada(self):
        self.preparar_anual();p=self.participante()
        body={'revision':1,'estado':'Finalizado','puntaje':35,'fecha_finalizacion':'2025-09-01','motivo':'Finalizar DEMO'}
        self.assertEqual(self.cliente.patch(f'/api/formacion/participaciones/{p["id"]}',json=body,headers=self.h).status_code,200)
        self.assertEqual(self.datos()['calculo']['academica']['valor'],35)
        retiro={'motivo':'Retirada DEMO','participaciones':[{'id':p['id'],'revision':2}]}
        self.assertEqual(self.cierre().status_code,201)
        self.assertEqual(self.cliente.post(f'/api/cursos/{self.cid}/retirar-participantes',json=retiro,headers=self.h).status_code,409)
        self._login();self.h={'X-CSRFToken':self._csrf_token()};cierre=self.cliente.get(self.url).json['cierres'][-1]['id']
        self.assertEqual(self.cliente.post(f'/api/admin/5b/periodos/{self.pid}/reabrir',json={'cierre_id':cierre,'motivo':'Reabrir DEMO'},headers=self.h).status_code,200)
        self.assertEqual(self.cliente.post(f'/api/cursos/{self.cid}/retirar-participantes',json=retiro,headers=self.h).status_code,200)
        self.assertEqual(self.datos()['calculo']['academica']['valor'],0)
        historia=self.cliente.get(f'/api/formacion/participaciones/{p["id"]}/historial').json['historial']
        self.assertEqual([h['puntaje'] for h in historia],[None,35,None])
        self.assertEqual(self.cliente.post(f'/api/cursos/{self.cid}/retirar-participantes',json=retiro,headers=self.h).status_code,409)
        self.assertEqual(self.cliente.patch(f'/api/formacion/participaciones/{p["id"]}',json={**body,'revision':3},headers=self.h).status_code,400)

    def test_retirada_multiple_atomica_y_revision_vigente(self):
        self.preparar_anual();p=self.participante()
        d={'motivo':'Lote DEMO','participaciones':[{'id':p['id'],'revision':1},{'id':999999,'revision':1}]}
        self.assertEqual(self.cliente.post(f'/api/cursos/{self.cid}/retirar-participantes',json=d,headers=self.h).status_code,409)
        actual=self.cliente.get(f'/api/cursos/{self.cid}/participantes').json['participantes'][0]
        self.assertFalse(actual['retirada']);self.assertEqual(actual['revision'],1)
        with self.app.app_context():c=obtener_conexion();c.execute("UPDATE usuarios SET estado='INACTIVO' WHERE id=3");c.commit()
        self.assertEqual(self.cliente.post(f'/api/cursos/{self.cid}/retirar-participantes',json={**d,'participaciones':d['participaciones'][:1]},headers=self.h).status_code,409)

    def test_fisica_sin_fechas_y_no_cumplida_auditada(self):
        self.preparar_anual()
        self.assertEqual(self.nota('FISICA_1',80,{'estado':'CUMPLIDA'}).status_code,201)
        self.assertEqual(self.nota('FISICA_2',2,{'estado':'NO_CUMPLIDA'}).status_code,409)
        self.assertEqual(self.nota('FISICA_2',0,{'estado':'NO_CUMPLIDA'}).status_code,201)
        self.assertEqual(self.datos()['calculo']['fisica'],'40')
        self.assertEqual(self.nota('FISICA_2',90,{'estado':'CUMPLIDA'}).status_code,201)
        self.assertEqual(self.datos()['calculo']['fisica'],'85')

    def activar_demo(self):
        ruta=self.url+'/ejemplos/PSICOMETRICA_1'
        self.assertEqual(self.cliente.patch(ruta,json={'activa':True,'anterior':False},headers=self.h).status_code,200)

    def test_ejemplo_aleatorio_puntua_en_servidor_y_no_altera_psicometria(self):
        self.preparar_anual();self.activar_demo()
        self._login('voluntario.demo','Clave voluntario 123!');h={'X-CSRFToken':self._csrf_token()};ruta=self.url+'/ejemplo/PSICOMETRICA_1'
        propia=self.cliente.get('/api/modelo-anual/propio');self.assertEqual(propia.status_code,200)
        self.assertNotIn('puntos_centesimas',str(propia.json));self.assertNotIn('DESEMPENO',str(propia.json))
        d=self.cliente.post(ruta,json={},headers=h).json;self.assertEqual(len(d['preguntas']),2)
        self.assertEqual(self.cliente.post(ruta,json={},headers=h).json['intento_id'],d['intento_id'])
        respuestas=[q['a']+q['b'] if q['operador']=='+' else q['a']-q['b'] for q in d['preguntas']]
        body={'intento_id':d['intento_id'],'respuestas':respuestas}
        self.assertEqual(self.cliente.post(ruta+'/finalizar',json={**body,'puntaje':100},headers=h).status_code,409)
        r=self.cliente.post(ruta+'/finalizar',json=body,headers=h);self.assertEqual(r.json['puntaje_ejemplo'],100);self.assertFalse(r.json['oficial'])
        self.assertEqual(self.cliente.post(ruta+'/finalizar',json=body,headers=h).status_code,409)
        self.assertEqual(self.cliente.get(self.url+'/ejemplos').status_code,403)
        self._login('instructor.demo','Clave instructor 123!')
        self.assertEqual(self.cliente.get(self.url+'/ejemplos').json['resultados'][0]['puntaje'],100)
        self.assertIsNone(self.datos()['calculo']['entradas'][3]['valor'])
        self.assertEqual(self.datos()['calculo']['entradas'][3]['estado'],'PENDIENTE_INSTRUMENTO')

    def test_demo_csrf_inactivo_desactivado_cerrado_y_concurrencia(self):
        self.preparar_anual();self.activar_demo()
        self.assertEqual(self.cliente.patch(self.url+'/ejemplos/PSICOMETRICA_1',json={'activa':False,'anterior':False},headers=self.h).status_code,409)
        self._login('voluntario.demo','Clave voluntario 123!');h={'X-CSRFToken':self._csrf_token()};ruta=self.url+'/ejemplo/PSICOMETRICA_1'
        self.assertEqual(self.cliente.post(ruta,json={}).status_code,400)
        self.assertEqual(self.cliente.post(self.url+'/ejemplo/PSICOMETRICA_2',json={},headers=h).status_code,409)
        d=self.cliente.post(ruta,json={},headers=h).json
        body={'intento_id':d['intento_id'],'respuestas':[0,0]}
        with self.cliente.session_transaction() as s:sesion=dict(s)
        def finalizar(_):
            with self.app.test_client() as client:
                with client.session_transaction() as s:s.update(sesion)
                return client.post(ruta+'/finalizar',json=body,headers=h).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:self.assertEqual(sorted(pool.map(finalizar,range(2))),[200,409])
        self._login('instructor.demo','Clave instructor 123!');self.h={'X-CSRFToken':self._csrf_token()}
        self.assertEqual(self.cierre().status_code,201)
        self._login('voluntario.demo','Clave voluntario 123!');h={'X-CSRFToken':self._csrf_token()}
        self.assertEqual(self.cliente.post(ruta,json={},headers=h).status_code,409)
        with self.app.app_context():c=obtener_conexion();c.execute("UPDATE usuarios SET estado='INACTIVO' WHERE id=3");c.commit()
        self.assertNotEqual(self.cliente.get('/api/modelo-anual/propio').status_code,200)

    def test_paginas_titulo_favicon_navegacion_y_migracion_repetida(self):
        self.preparar_anual()
        for ruta in ['/panel/jefe-personal','/gestion/periodos-5b','/gestion/modelo-anual','/gestion/operaciones','/gestion/reportes']:
            r=self.cliente.get(ruta);self.assertEqual(r.status_code,200,ruta);html=r.data.decode()
            self.assertIn('<title>SICOSE - SBRAB</title>',html);self.assertIn('rel="icon"',html)
            self.assertNotIn('>Notas y Resultados</span>',html)
        self.assertEqual(self.cliente.get('/gestion/seguimiento-operativo').status_code,302)
        with self.app.app_context():
            c=obtener_conexion();antes=c.execute('SELECT COUNT(*) FROM notas_modelo_anual').fetchone()[0]
            inicializar_base_datos();inicializar_base_datos()
            self.assertEqual(c.execute('SELECT COUNT(*) FROM notas_modelo_anual').fetchone()[0],antes)
            self.assertEqual(c.execute('PRAGMA quick_check').fetchone()[0],'ok');self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(),[])

    def test_reporte_actual_pdf_privado_sin_puntajes_demostrativos(self):
        self.preparar_anual()
        r=self.cliente.get(f'/api/evaluaciones/reporte.pdf?periodo_id={self.pid}')
        self.assertEqual(r.status_code,200);self.assertEqual(r.mimetype,'application/pdf')
        self.assertIn('inline',r.headers['Content-Disposition']);self.assertIn('no-store',r.headers['Cache-Control'])
        self.assertTrue(r.data.startswith(b'%PDF'));r.close()
        self.assertEqual(self.cierre().status_code,201)
        with self.app.app_context():c=obtener_conexion();c.execute("UPDATE usuarios SET nombre_completo='Nombre corregido DEMO' WHERE id=3");c.commit()
        from unittest.mock import patch
        from io import BytesIO
        with patch('sicose.reportes_personal.generar_listado',return_value=BytesIO(b'%PDF demo')) as generar:
            r=self.cliente.get(f'/api/evaluaciones/reporte.pdf?periodo_id={self.pid}')
            self.assertEqual(r.status_code,200);r.close()
            self.assertEqual(generar.call_args.args[3][0][0],'voluntario.demo')
        self._login('voluntario.demo','Clave voluntario 123!')
        self.assertEqual(self.cliente.get(f'/api/evaluaciones/reporte.pdf?periodo_id={self.pid}').status_code,403)
