"""Académica: promedio Asistencia, Cursos con tope y Operaciones promediadas."""
import unittest
import test_panel_instructor as fixtures
from sicose.db import obtener_conexion


class AcademicaTresNotasTest(unittest.TestCase):
    for nombre,valor in vars(fixtures.PanelInstructorTestCase).items():
        if not nombre.startswith('test_') and not nombre.startswith('__'):
            locals()[nombre]=valor

    def test_tres_componentes_tope_cursos_intervalo_y_persona(self):
        self.preparar_anual()
        with self.app.app_context():
            c=obtener_conexion()
            for dia,estado,detalle in [('01','PRESENTE','ASISTE'),('02','PRESENTE','ATRASO'),('03','PRESENTE','ASISTE'),('04','AUSENTE','FALTA'),('05','JUSTIFICADO','PERMISO')]:
                c.execute('INSERT INTO asistencias(voluntario_id,fecha,estado,estado_detalle,actividad,registrado_por) VALUES (3,?,?,?,?,2)',('2025-09-'+dia,estado,detalle,'Ordinaria'))
            c.execute("INSERT INTO asistencias(voluntario_id,fecha,estado,estado_detalle,actividad,registrado_por) VALUES (3,'2025-12-01','AUSENTE','FALTA','Ordinaria',2)")
            c.commit()
        for i in range(2):
            r=self.cliente.post('/api/cursos',json={'nombre':f'Curso DEMO {i}','tipo':'Taller','entidad':'DEMO','fecha_inicio':'2025-09-01','fecha_fin':'2025-09-02','puntaje':80},headers=self.h)
            cid=r.json['id']
            self.cliente.post(f'/api/cursos/{cid}/participantes',json={'voluntario_ids':[3]},headers=self.h)
            part=self.cliente.get(f'/api/cursos/{cid}/participantes').json['participantes'][0]
            r=self.cliente.patch(f"/api/formacion/participaciones/{part['id']}",json={'revision':1,'estado':'Finalizado','puntaje':80,'fecha_finalizacion':'2025-09-02','motivo':'DEMO'},headers=self.h)
            self.assertEqual(r.status_code,200)
        for n in (50,20):
            oid=self.operacion_demo();self.assertEqual(self.puntuar_operacion(oid,n).status_code,201)
        a=self.datos()['calculo']['academica']
        self.assertEqual(a['aporte_asistencia'],75)
        self.assertEqual(a['cursos_sin_tope'],160)
        self.assertEqual(a['aporte_cursos'],100)
        self.assertEqual(a['aporte_operaciones'],'35')
        self.assertEqual(a['valor'],70)

    def test_solo_permiso_aporta_cero_y_publicacion_no_cambia_sola(self):
        self.preparar_anual()
        with self.app.app_context():
            c=obtener_conexion();c.execute("INSERT INTO asistencias(voluntario_id,fecha,estado,estado_detalle,actividad,registrado_por) VALUES (3,'2025-09-01','JUSTIFICADO','PERMISO','Ordinaria',2)");c.commit()
        self.assertEqual(self.datos()['calculo']['academica']['aporte_asistencia'],0)
        self.assertEqual(self.publicar().status_code,201)
        with self.app.app_context():
            c=obtener_conexion();c.execute("UPDATE asistencias SET estado='PRESENTE',estado_detalle='ASISTE' WHERE voluntario_id=3");c.commit()
        self.assertAlmostEqual(self.datos()['calculo']['academica']['valor'],100/3)
        self.assertEqual(self.propia().json['publicacion']['academica']['valor'],0)
