"""Notas publicadas, orden por grado, filtros y permisos del listado PDF."""
import unittest
from unittest.mock import patch
from fractions import Fraction
from sicose.db import obtener_conexion
from sicose.reporte_notas_grados import datos_listado, generar_listado
import test_panel_instructor as fixtures


class ReporteNotasGradosTest(unittest.TestCase):
    for nombre,valor in vars(fixtures.PanelInstructorTestCase).items():
        if not nombre.startswith('test_') and not nombre.startswith('__'):
            locals()[nombre]=valor

    def test_publicacion_exclusiva_media_y_pdf_para_ambos_gestores(self):
        self.preparar_anual()
        self.assertEqual(self.nota('DESEMPENO_JEFE',80).status_code,201)
        self.assertEqual(self.nota('DESEMPENO_COMANDANTE',90,{'comandante_nombre':'Externo DEMO'}).status_code,201)
        with self.app.app_context():
            self.assertIsNone(datos_listado(obtener_conexion(),self.pid)['filas'][0]['final'])
        self.assertEqual(self.publicar().status_code,201)
        with self.app.app_context():
            d=datos_listado(obtener_conexion(),self.pid)
            f=d['filas'][0]
            self.assertEqual(f['final'],sum(Fraction(n) for n in f['notas'])/3)
            self.assertTrue(generar_listado(d).getvalue().startswith(b'%PDF'))
            anterior=f['final']
        self.assertEqual(self.nota('DESEMPENO_JEFE',20).status_code,201)
        with self.app.app_context():
            self.assertEqual(datos_listado(obtener_conexion(),self.pid)['filas'][0]['final'],anterior)
        for usuario,clave in [('admin.demo','Clave demo segura 123!'),('instructor.demo','Clave instructor 123!')]:
            self._login(usuario,clave)
            html=self.cliente.get('/gestion/reportes').data.decode()
            self.assertIn('/api/reportes/notas-por-grado.pdf',html)
            r=self.cliente.get(f'/api/reportes/notas-por-grado.pdf?periodo_id={self.pid}')
            self.assertEqual(r.status_code,200)
            self.assertEqual(r.headers['Cache-Control'],'private, no-store')
            self.assertTrue(r.data.startswith(b'%PDF'))

    def test_grado_antes_de_nota_desempate_y_exclusion_de_inactivos(self):
        self.preparar_anual()
        with self.app.app_context():
            c=obtener_conexion()
            c.execute("UPDATE voluntarios SET grado='Instructor Inicial' WHERE usuario_id=3")
            rol=c.execute("SELECT id FROM roles WHERE nombre='INSTRUCTOR_VOLUNTARIO'").fetchone()[0]
            for uid,grado,apellido,estado in [(4,'Instructor Mayor','Zulu','ACTIVO'),(5,'Instructor Mayor','Alfa','ACTIVO'),(6,'Instructor Mayor','Beta','INACTIVO'),(7,None,'Pendiente','ACTIVO')]:
                c.execute('INSERT INTO usuarios(id,username,nombre_completo,password_hash,rol_id,estado) VALUES (?,?,?,?,?,?)',(uid,f'grado{uid}.demo',apellido,'hash-sintetico',rol,estado))
                c.execute('INSERT INTO voluntarios(usuario_id,grado,apellido_paterno) VALUES (?,?,?)',(uid,grado,apellido))
                inscripcion=tuple(c.execute('SELECT * FROM personas_modelo_anual WHERE periodo_id=? AND voluntario_id=3',(self.pid,)).fetchone())
                c.execute('INSERT INTO personas_modelo_anual VALUES (?,?,?,?)',(inscripcion[0],uid,*inscripcion[2:]))
            c.commit()
            def publicada(c,uid,pid):
                if uid==7:return None
                n=100 if uid==3 else 80
                return dict(promedio_fisico=n,academica={'valor':n},desempeno={'valor':n})
            with patch('sicose.reporte_notas_grados.proyeccion',side_effect=publicada):
                filas=datos_listado(c,self.pid)['filas']
            self.assertEqual([f['id'] for f in filas],[5,4,3,7])
            self.assertIsNone(filas[-1]['final'])

    def test_parametros_instructor_y_gestion_inexistente(self):
        self.preparar_anual()
        ruta='/api/reportes/notas-por-grado.pdf'
        for sufijo in ('','?periodo_id=x','?periodo_id=1&periodo_id=2','?periodo_id=1&extra=1'):
            self.assertEqual(self.cliente.get(ruta+sufijo).status_code,400)
        self.assertEqual(self.cliente.get(ruta+'?periodo_id=99999').status_code,404)
        self._login('voluntario.demo','Clave voluntario 123!')
        self.assertEqual(self.cliente.get(ruta+f'?periodo_id={self.pid}').status_code,403)
