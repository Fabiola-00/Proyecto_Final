"""Panel personal, intervalos y publicación del promedio sin fuentes privadas."""
import json
import unittest
from unittest.mock import patch
from flask import render_template
import test_modelo_anual as fixtures
from sicose.db import obtener_conexion


class PanelInstructorTestCase(unittest.TestCase):
    for nombre,valor in vars(fixtures.ModeloAnualTestCase).items():
        if not nombre.startswith('test_') and not nombre.startswith('__'):
            locals()[nombre] = valor

    def propia(self):
        self._login('voluntario.demo','Clave voluntario 123!')
        return self.cliente.get(f'/api/evaluaciones/propias?periodo_id={self.pid}')

    def publicar(self):
        ruta='/api/5b/personas/3/publicacion'
        v=self.cliente.get(ruta+f'?periodo_id={self.pid}').json['publicacion']
        return self.cliente.post(ruta,json=dict(periodo_id=self.pid,revision_publicada=v['revision_publicada'],firma_fuentes=v['firma_fuentes'],motivo='Publicación DEMO'),headers=self.h)

    def test_promedio_operaciones_se_publica_y_correccion_requiere_republicacion(self):
        self.preparar_anual()
        a=self.operacion_demo();b=self.operacion_demo()
        self.assertEqual(self.puntuar_operacion(a,50).status_code,201)
        self.assertEqual(self.puntuar_operacion(b,20).status_code,201)
        self.assertEqual(self.publicar().status_code,201)
        self.assertAlmostEqual(self.propia().json['publicacion']['academica']['valor'],35/3)
        self._login('instructor.demo','Clave instructor 123!');self.h={'X-CSRFToken':self._csrf_token()}
        anterior=[n for n in self.datos()['historial']['operaciones'] if n['operacion_id']==b][-1]['id']
        self.assertEqual(self.puntuar_operacion(b,100,anterior).status_code,201)
        self.assertAlmostEqual(self.propia().json['publicacion']['academica']['valor'],35/3)
        self._login('instructor.demo','Clave instructor 123!');self.h={'X-CSRFToken':self._csrf_token()}
        self.assertEqual(self.publicar().status_code,201)
        self.assertEqual(self.propia().json['publicacion']['academica']['valor'],25)

    def test_promedio_publicado_correccion_republicacion_y_privacidad(self):
        self.preparar_anual()
        self.assertEqual(self.nota('DESEMPENO_JEFE','81.01').status_code,201)
        self.assertEqual(self.nota('DESEMPENO_COMANDANTE',70,{'comandante_nombre':'Nombre reservado DEMO'}).status_code,201)
        self.assertIsNone(self.propia().json['publicacion'])
        self._login('instructor.demo','Clave instructor 123!');self.h={'X-CSRFToken':self._csrf_token()}
        self.assertEqual(self.publicar().status_code,201)
        p=self.propia().json['publicacion']
        self.assertEqual(p['desempeno']['valor'],'75.51')
        grafico=self.cliente.get(f'/mis-evaluaciones/anual?periodo_id={self.pid}')
        self.assertEqual(grafico.status_code,200)
        html=grafico.data.decode()
        self.assertIn('resultados-torres',html)
        self.assertIn('height:75.51%',html)
        self.assertNotIn('Nombre reservado',html)
        self.assertNotIn('81.01',html)
        for prohibido in ('81.01','70.00','Nombre reservado','nota_id','motivo','DESEMPENO_JEFE','DESEMPENO_COMANDANTE'):
            self.assertNotIn(prohibido,json.dumps(p))
        self._login('instructor.demo','Clave instructor 123!');self.h={'X-CSRFToken':self._csrf_token()}
        self.assertTrue(self.publicar().json['sin_cambios'])
        self.assertEqual(self.nota('DESEMPENO_JEFE',90).status_code,201)
        self.assertEqual(self.propia().json['publicacion']['desempeno']['valor'],'75.51')
        self._login('instructor.demo','Clave instructor 123!');self.h={'X-CSRFToken':self._csrf_token()}
        self.assertEqual(self.publicar().status_code,201)
        self.assertEqual(self.propia().json['publicacion']['desempeno']['valor'],'80.00')
        self.assertEqual(self.cliente.post('/api/5b/personas/3/publicacion',json={},headers={'X-CSRFToken':self._csrf_token()}).status_code,403)

    def test_ocultar_desempeno_deshabilitado_y_bloquear_publicacion_cerrada(self):
        self.preparar_anual();self.assertEqual(self.publicar().status_code,201)
        self.assertEqual(self.cliente.patch('/api/evaluaciones/personas/3/habilitacion',json=dict(periodo_id=self.pid,clave='DESEMPENO_JEFE',habilitada=False),headers=self.h).status_code,200)
        self.assertIsNone(self.propia().json['publicacion']['desempeno'])
        self._login('instructor.demo','Clave instructor 123!');self.h={'X-CSRFToken':self._csrf_token()}
        self.assertEqual(self.cierre().status_code,201)
        self.assertEqual(self.publicar().status_code,409)

    def test_inicio_solo_gestion_activa_y_pendientes_institucionales(self):
        self.preparar_anual();self.assertEqual(self.nota('FISICA_1',80,{'estado':'CUMPLIDA'}).status_code,201)
        self.propia()
        pagina=self.cliente.get('/panel/instructor-voluntario').data.decode()
        self.assertNotIn('Tu avance',pagina)
        self.assertEqual(pagina.count('class="tarjeta-indicador"'),4)
        self.assertIn('Evaluaciones Asignadas',pagina)
        self.assertIn('Académica, Desempeño',pagina)
        self.assertNotIn('NASA',pagina)
        self.assertGreater(pagina.index('aria-label="Mi perfil"'),pagina.index('class="lateral-inferior"'))
        self.assertLess(pagina.index('aria-label="Mi perfil"'),pagina.index('PERÍODO ACTUAL'))

    def test_asistencias_meses_limites_y_aislamiento(self):
        self.preparar_anual()
        with self.app.app_context():
            c=obtener_conexion()
            for fecha,estado,detalle in [('2025-08-14','PRESENTE','ASISTE'),('2025-08-15','PRESENTE','ASISTE'),('2025-09-01','PRESENTE','ATRASO'),('2025-11-30','JUSTIFICADO','PERMISO'),('2025-12-01','AUSENTE','FALTA')]:
                c.execute('INSERT INTO asistencias(voluntario_id,fecha,estado,estado_detalle,actividad,registrado_por) VALUES (3,?,?,?,?,2)',(fecha,estado,detalle,'Ordinaria'))
            c.execute("INSERT INTO asistencias(voluntario_id,fecha,estado,estado_detalle,actividad,registrado_por) VALUES (3,'2025-08-15','PRESENTE','ASISTE','Terreno',2)")
            self._crear_usuario('otra.demo','INSTRUCTOR_VOLUNTARIO','Clave otra DEMO 123!')
            c.execute('INSERT INTO voluntarios(usuario_id) VALUES (4)')
            c.execute("INSERT INTO asistencias(voluntario_id,fecha,estado,estado_detalle,actividad,registrado_por) VALUES (4,'2025-08-15','PRESENTE','ASISTE','Ordinaria',2)")
            c.commit()
        self.propia()
        with patch('sicose.panel_instructor.render_template', wraps=render_template) as render:
            pagina=self.cliente.get(f'/mis-asistencias?periodo_id={self.pid}').data.decode()
            graficos=render.call_args.kwargs['graficos']
            self.assertEqual([[f['valor'] for f in g['filas']] for g in graficos],[[2,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,0,0]])
        self.assertIn('2025-08',pagina);self.assertIn('2025-11',pagina)
        self.assertNotIn('<small>2025-12</small>',pagina)
        self.assertNotIn('asistencias-calendario',pagina)
        self.assertEqual(self.cliente.get('/mis-asistencias?persona_id=2').status_code,400)

    def test_operaciones_filtra_solapamientos_sin_cambiar_tabla(self):
        self.preparar_anual();dentro=self.operacion_demo();self.operacion_demo('2025-12-01')
        self.propia()
        datos=self.cliente.get(f'/api/operaciones?periodo_id={self.pid}').json['operaciones']
        self.assertEqual([o['id'] for o in datos],[dentro])
        self.assertEqual([p['voluntario_id'] for p in datos[0]['participantes']],[3])
        pagina=self.cliente.get('/gestion/operaciones').data.decode()
        self.assertIn('gestion-propia-selector',pagina);self.assertIn('js/operaciones.js',pagina)
        self.assertEqual(self.cliente.get('/mis-cursos?periodo_id=99999').status_code,400)

    def test_cursos_calificacion_publicada_estable_y_gestion_cerrada(self):
        self.preparar_anual()
        r=self.cliente.post('/api/cursos',json=dict(nombre='Curso visible DEMO',tipo='Taller',entidad='Entidad DEMO',fecha_inicio='2025-08-16',fecha_fin='2025-08-20',puntaje=73),headers=self.h)
        cid=r.json['id']
        self.assertEqual(self.cliente.post(f'/api/cursos/{cid}/participantes',json={'voluntario_ids':[3]},headers=self.h).status_code,201)
        part=self.cliente.get(f'/api/cursos/{cid}/participantes').json['participantes'][0]
        ruta=f"/api/formacion/participaciones/{part['id']}"
        self.assertEqual(self.cliente.patch(ruta,json=dict(revision=1,estado='Finalizado',puntaje=73,fecha_finalizacion='2025-08-20',motivo='DEMO'),headers=self.h).status_code,200)
        self.propia()
        pagina=self.cliente.get('/mis-cursos').data.decode()
        self.assertIn('Curso visible DEMO',pagina);self.assertNotIn('<td>73</td>',pagina)
        self._login('instructor.demo','Clave instructor 123!');self.h={'X-CSRFToken':self._csrf_token()}
        self.assertEqual(self.publicar().status_code,201)
        self.assertEqual(self.cliente.patch(ruta,json=dict(revision=2,estado='Finalizado',puntaje=88,fecha_finalizacion='2025-08-20',motivo='DEMO'),headers=self.h).status_code,200)
        self.propia()
        pagina=self.cliente.get('/mis-cursos').data.decode()
        self.assertIn('<td>73</td>',pagina);self.assertNotIn('<td>88</td>',pagina)
        self.assertEqual(self.cliente.get('/api/instructor-voluntario/formacion').json['publicaciones'][0]['academica']['cursos'][0]['puntaje'],73)
        self._login('instructor.demo','Clave instructor 123!');self.h={'X-CSRFToken':self._csrf_token()}
        self.assertEqual(self.cierre().status_code,201)
        self.propia()
        self.assertIn('<td>73</td>',self.cliente.get(f'/mis-cursos?periodo_id={self.pid}').data.decode())
        self.assertEqual(self.cliente.get('/mis-cursos?persona_id=1').status_code,400)


if __name__ == '__main__':
    unittest.main()
