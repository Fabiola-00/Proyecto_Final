"""Navegación global, permisos confirmados y privacidad de los nuevos reportes."""
import unittest
from io import BytesIO
import test_historicos_5b as fixtures
from sicose.db import obtener_conexion
from unittest.mock import patch

class EspacioJefeTestCase(unittest.TestCase):
    for nombre,valor in vars(fixtures.Historicos5BTestCase).items():
        if (nombre.startswith('_') and not nombre.startswith('__')) or nombre in ('setUp','tearDown','preparar','fisica','desempeno','curso','activar','calculo','preparar_publicable','vista','publicar','propia','corregir_fisica'):
            locals()[nombre]=valor

    def texto(self,r):
        self.assertEqual(r.status_code,200,r.json if r.is_json else '')
        self.assertEqual(r.headers['Cache-Control'],'private, no-store')
        self.assertTrue(r.data.startswith(b'%PDF'));return ''

    def test_menu_global_separacion_y_activacion_administrativa(self):
        self.preparar_publicable();self._login('instructor.demo','Clave instructor 123!')
        html=self.cliente.get('/panel/jefe-personal').data.decode()
        nav=html.split('<nav class="navegacion">')[1].split('</nav>')[0]
        for texto in ('Cursos y Capacitaciones','Evaluaciones','Reportes','Gestión'):self.assertIn(texto,nav)
        self.assertNotIn('Notas y Resultados',nav)
        self.assertNotIn('Catálogo',nav);self.assertNotIn('Habilitación y avance',nav)
        for ruta in ('/gestion/periodos-5b','/gestion/evaluaciones-personal','/gestion/reportes'):self.assertEqual(self.cliente.get(ruta,follow_redirects=True).status_code,200)
        pagina=self.cliente.get('/gestion/periodos-5b').data.decode()
        self.assertNotIn('periodo-5b-alta',pagina);self.assertIn('modelo-lista-gestiones',pagina)
        self.assertIn('Resumen SBRAB',html);self.assertNotIn('Seguimiento asignado',html)
        self.assertIn('Días con asistencia registrada',html)
        h={'X-CSRFToken':self._csrf_token()}
        self.assertEqual(self.cliente.post(f'/api/admin/5b/periodos/{self.pid}/publicar',json={'revision':1},headers=h).status_code,403)

    def test_reportes_filtros_privacidad_cero_y_roles(self):
        self.preparar_publicable();self.curso(0)
        self._login('instructor.demo','Clave instructor 123!')
        ruta='/api/reportes/formacion.pdf?desde=2026-01-01&hasta=2026-12-31'
        self.texto(self.cliente.get(ruta))
        with patch('sicose.reportes_personal.generar_listado',return_value=BytesIO(b'%PDF demo')) as generar:
            self.texto(self.cliente.get(ruta))
            args=generar.call_args.args
            self.assertEqual(args[0],'Formación personal finalizada');self.assertIn(0,[fila[-1] for fila in args[3]])
            self.assertEqual(len(args[2]),7);self.assertNotIn('@',str(args[3]))
        for query in ('desde=x&hasta=y','desde=2026-12-31&hasta=2026-01-01','desde=2026-01-01&hasta=2026-12-31&motivo=x','desde=2026-01-01&desde=2026-02-01&hasta=2026-12-31'):
            self.assertEqual(self.cliente.get('/api/reportes/formacion.pdf?'+query).status_code,400)
        with patch('sicose.reportes_personal.generar_listado',return_value=BytesIO(b'%PDF demo')) as generar:
            self.texto(self.cliente.get('/api/reportes/operaciones.pdf?desde=2001-01-01&hasta=2001-12-31'))
            self.assertEqual(generar.call_args.args[3],[])
        self._login('voluntario.demo','Clave voluntario 123!')
        for ruta in ('/gestion/reportes','/gestion/evaluaciones-personal','/api/reportes/formacion.pdf?desde=2026-01-01&hasta=2026-12-31','/api/reportes/operaciones.pdf?desde=2026-01-01&hasta=2026-12-31'):self.assertEqual(self.cliente.get(ruta).status_code,403)

    def test_operaciones_jefe_asignacion_atomica_e_inactivos(self):
        self.preparar_publicable();self._login('instructor.demo','Clave instructor 123!');h={'X-CSRFToken':self._csrf_token()}
        with self.app.app_context():
            self._crear_usuario('participante2.demo','INSTRUCTOR_VOLUNTARIO','Clave demo prueba 123!')
            c=obtener_conexion();otro_id=c.execute("SELECT id FROM usuarios WHERE username='participante2.demo'").fetchone()[0];c.execute('INSERT INTO voluntarios(usuario_id) VALUES (?)',(otro_id,));c.commit()
        evento=dict(tipo_evento='Rescate DEMO',lugar='Lugar DEMO',fecha_inicio='2026-10-01',fecha_fin='2026-10-02',institucion_responsable='Entidad DEMO')
        r=self.cliente.post('/api/operaciones',json=evento,headers=h);self.assertEqual(r.status_code,201);oid=r.json['id'];ruta=f'/api/operaciones/{oid}/participaciones'
        self.assertEqual(self.cliente.patch(f'/api/operaciones/{oid}',json={'lugar':'Lugar corregido'},headers=h).status_code,200)
        self.assertEqual(self.cliente.post(ruta,json={'voluntario_ids':[3,1]},headers=h).status_code,404)
        self.assertEqual(self.cliente.get('/api/operaciones').json['operaciones'][0]['participantes'],[])
        for ids in ([],[3,3],[True]):self.assertEqual(self.cliente.post(ruta,json={'voluntario_ids':ids},headers=h).status_code,400)
        self.assertEqual(self.cliente.post(ruta,json={'voluntario_ids':[3,otro_id]},headers=h).status_code,201)
        self.assertEqual(len(self.cliente.get('/api/operaciones').json['operaciones'][0]['participantes']),2)
        self.assertEqual(self.cliente.post(ruta,json={'voluntario_ids':[3]},headers=h).status_code,409)
        with patch('sicose.reportes_personal.generar_listado',return_value=BytesIO(b'%PDF demo')) as generar:
            self.texto(self.cliente.get('/api/reportes/operaciones.pdf?desde=2026-10-01&hasta=2026-10-01'))
            self.assertEqual(generar.call_args.args[3][0][0:2],('Rescate DEMO','Lugar corregido'))
        with self.app.app_context():
            c=obtener_conexion();c.execute("UPDATE usuarios SET estado='INACTIVO' WHERE id=3");c.commit()
        otro=self.cliente.post('/api/operaciones',json=evento,headers=h).json['id']
        self.assertEqual(self.cliente.post(f'/api/operaciones/{otro}/participaciones',json={'voluntario_ids':[3]},headers=h).status_code,404)
