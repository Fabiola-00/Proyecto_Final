"""Reporte individual: permisos, alcance temporal y evidencia sintética aislada."""
import unittest
from unittest.mock import patch
from pathlib import Path
import test_modelo_anual as base
from sicose.db import obtener_conexion
from sicose.reporte_individual import datos_individual, generar_individual


class ReporteIndividualTestCase(unittest.TestCase):
    for nombre,valor in vars(base.ModeloAnualTestCase).items():
        if not nombre.startswith('test_') and not nombre.startswith('__'):
            locals()[nombre]=valor

    def ruta(self):
        return f'/api/reportes/individual/3.pdf?periodo_id={self.pid}'

    def test_pdf_real_privado_foto_pendientes_y_ambos_gestores(self):
        self.preparar_anual()
        self.assertEqual(self.nota('DESEMPENO_JEFE',80).status_code,201)
        self.assertEqual(self.nota('DESEMPENO_COMANDANTE',90,{'comandante_nombre':'Evaluador externo DEMO'}).status_code,201)
        with self.app.app_context():
            c=obtener_conexion()
            foto='a'*32+'.png'
            from PIL import Image
            Path(self.app.config['PERFIL_MEDIA_FOLDER']).mkdir(exist_ok=True)
            Image.new('RGB',(100,140),'#226DC6').save(Path(self.app.config['PERFIL_MEDIA_FOLDER'])/foto)
            c.execute('UPDATE usuarios SET foto_perfil=? WHERE id=3',(foto,));c.commit()
            d=datos_individual(c,3)
            self.assertEqual(float(d['calculo']['desempeno']),85)
            self.assertNotIn('password_hash',d['persona'])
        for admin in (False,True):
            if admin:self._login()
            r=self.cliente.get(self.ruta())
            self.assertEqual(r.status_code,200,r.json if r.is_json else '')
            self.assertTrue(r.data.startswith(b'%PDF'))
            self.assertEqual(r.headers['Cache-Control'],'private, no-store')
            self.assertIn('inline',r.headers['Content-Disposition'])
        with self.app.app_context():
            c=obtener_conexion()
            self.assertEqual(c.execute("SELECT COUNT(*) FROM auditoria WHERE accion LIKE 'REPORTE_INDIVIDUAL:%'").fetchone()[0],2)

    def test_alcance_personal_cursos_pendientes_y_asistencia(self):
        self.preparar_anual();oid=self.operacion_demo();self.operacion_demo('2025-12-01')
        self.assertEqual(self.puntuar_operacion(oid,75).status_code,201)
        curso={'nombre':'Curso pendiente DEMO','tipo':'Taller','entidad':'Entidad DEMO','fecha_inicio':'2025-08-01','fecha_fin':'2025-10-01','puntaje':20}
        r=self.cliente.post('/api/cursos',json=curso,headers=self.h);cid=r.json['id']
        self.assertEqual(self.cliente.post(f'/api/cursos/{cid}/participantes',json={'voluntario_ids':[3]},headers=self.h).status_code,201)
        with self.app.app_context():
            c=obtener_conexion()
            for fecha,estado,detalle in [('2025-08-15','PRESENTE','ASISTE'),('2025-11-30','PRESENTE','ATRASO'),('2025-09-01','AUSENTE','FALTA'),('2025-09-02','JUSTIFICADO','PERMISO'),('2025-12-01','AUSENTE','FALTA')]:
                c.execute('INSERT INTO asistencias(voluntario_id,fecha,estado,estado_detalle,actividad,registrado_por) VALUES (3,?,?,?,?,2)',(fecha,estado,detalle,'Ordinaria'))
            c.commit();d=datos_individual(c,3)
            self.assertEqual(d['asistencia']['porcentaje'],66.67)
            self.assertEqual(d['asistencia']['FALTA'],1)
            self.assertEqual(len(d['operaciones']),1)
            self.assertEqual(d['operaciones'][0]['puntos_centesimas'],7500)
            self.assertEqual(d['cursos'][0]['estado'],'Asignado')
            self.assertIsNone(d['cursos'][0]['puntaje'])
            self.assertAlmostEqual(d['calculo']['academica']['valor'],(66.67+75)/3)

    def test_sin_activa_cambio_de_gestion_parametros_y_persona(self):
        self._login()
        self.assertEqual(self.cliente.get('/api/reportes/individual/contexto').status_code,409)
        self.preparar_anual()
        contexto=self.cliente.get('/api/reportes/individual/contexto')
        self.assertEqual(contexto.status_code,200)
        self.assertEqual(contexto.json['periodo']['id'],self.pid)
        self.assertEqual(self.cliente.get(f'/api/reportes/individual/3.pdf?periodo_id={self.pid+1}').status_code,409)
        self.assertEqual(self.cliente.get(f'/api/reportes/individual/99999.pdf?periodo_id={self.pid}').status_code,404)
        self.assertEqual(self.cliente.get('/api/reportes/individual/3.pdf').status_code,400)
        self.assertEqual(self.cliente.get(self.ruta()+'&periodo_id=99').status_code,400)

    def test_instructor_no_accede_y_sin_foto_no_fabrica_datos(self):
        self.preparar_anual()
        with self.app.app_context():
            d=datos_individual(obtener_conexion(),3)
            self.assertIsNone(d['asistencia']['porcentaje'])
            self.assertTrue(generar_individual(d).getvalue().startswith(b'%PDF'))
        self._login('voluntario.demo','Clave voluntario 123!')
        self.assertEqual(self.cliente.get(self.ruta()).status_code,403)
        self.assertEqual(self.cliente.get('/api/reportes/individual/contexto').status_code,403)
        self.assertNotIn('Reporte individual',self.cliente.get('/panel/instructor-voluntario').data.decode())

    def test_foto_ruta_invalida_no_se_abre(self):
        self.preparar_anual()
        with self.app.app_context():
            c=obtener_conexion();c.execute("UPDATE usuarios SET foto_perfil='../../.env' WHERE id=3");c.commit()
            d=datos_individual(c,3)
            with patch('sicose.reporte_individual.Image',side_effect=AssertionError('No abrir foto inválida')):
                self.assertTrue(generar_individual(d).getvalue().startswith(b'%PDF'))
