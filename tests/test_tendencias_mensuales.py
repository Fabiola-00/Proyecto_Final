"""Intervalos inclusivos, meses vacíos y agrupación descriptiva del dashboard."""
import sqlite3
import unittest
from sicose.espacio_jefe import tendencias_mensuales


class TendenciasMensualesTestCase(unittest.TestCase):
    def setUp(self):
        self.c=sqlite3.connect(':memory:')
        self.c.executescript('CREATE TABLE operaciones(fecha_inicio TEXT); CREATE TABLE cursos(fecha_inicio TEXT); CREATE TABLE asistencias(fecha TEXT); CREATE TABLE participaciones_curso(fecha_finalizacion TEXT,estado TEXT);')

    def tearDown(self): self.c.close()

    def test_limites_parciales_y_conteos_de_las_cuatro_series(self):
        fechas=['2026-08-14','2026-08-15','2026-08-31','2026-09-01','2026-11-20','2026-11-21',None]
        for tabla,columna in [('operaciones','fecha_inicio'),('cursos','fecha_inicio'),('asistencias','fecha')]:
            self.c.executemany(f'INSERT INTO {tabla}({columna}) VALUES (?)',[(f,) for f in fechas])
        self.c.executemany('INSERT INTO participaciones_curso VALUES (?,?)',[(f,'Finalizado') for f in fechas]+[('2026-10-01','No completado')])
        datos=tendencias_mensuales(self.c,{'fecha_inicio':'2026-08-15','fecha_fin':'2026-11-20'})
        self.assertEqual(len(datos),4)
        for g in datos:
            self.assertEqual([f['mes'] for f in g['filas']],['2026-08','2026-09','2026-10','2026-11'])
            self.assertEqual([f['valor'] for f in g['filas']],[2,1,0,1])
            self.assertEqual([f['alto'] for f in g['filas']],[110,55,0,55])

    def test_cruce_de_ano_sin_mezclar_meses_y_febrero_bisiesto(self):
        self.c.executemany('INSERT INTO operaciones VALUES (?)',[('2023-12-31',),('2024-01-01',),('2024-02-29',),('2024-03-01',)])
        filas=tendencias_mensuales(self.c,{'fecha_inicio':'2023-12-15','fecha_fin':'2024-02-29'})[0]['filas']
        self.assertEqual([f['nombre'] for f in filas],['Dic 2023','Ene 2024','Feb 2024'])
        self.assertEqual([f['valor'] for f in filas],[1,1,1])

    def test_asistencias_cuenta_dias_unicos_aunque_haya_varias_personas_o_actividades(self):
        self.c.executemany('INSERT INTO asistencias VALUES (?)',[(f,) for f in ['2026-08-31']+['2026-09-01']*6+['2026-09-02']*12+['2026-10-16']*3+['2026-10-17']*5])
        grafico=tendencias_mensuales(self.c,{'fecha_inicio':'2026-09-01','fecha_fin':'2026-10-16'})[2]
        self.assertEqual(grafico['titulo'],'Días con asistencia registrada')
        self.assertEqual([f['valor'] for f in grafico['filas']],[2,1])

    def test_todos_los_meses_sin_registros_y_periodo_de_un_dia(self):
        filas=tendencias_mensuales(self.c,{'fecha_inicio':'2026-01-01','fecha_fin':'2026-12-31'})[0]['filas']
        self.assertEqual(len(filas),12);self.assertTrue(all(f['valor']==f['alto']==0 for f in filas))
        filas=tendencias_mensuales(self.c,{'fecha_inicio':'2026-10-16','fecha_fin':'2026-10-16'})[0]['filas']
        self.assertEqual(len(filas),1);self.assertEqual(filas[0]['nombre'],'Oct 2026')

    def test_sin_gestion_activa_no_inventa_intervalos(self):
        self.c.execute("INSERT INTO operaciones VALUES ('2026-10-16')")
        self.assertTrue(all(g['filas']==[] for g in tendencias_mensuales(self.c,None)))
