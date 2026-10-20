"""Pruebas de autenticación, autorización y persistencia SICOSE."""

import re
import sqlite3
import struct
import unittest
import uuid
import zlib
from datetime import date
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

from sicose import create_app
from sicose.db import inicializar_base_datos, seed_admin


class AplicacionTestCase(unittest.TestCase):
    def setUp(self):
        Path(".tmp").mkdir(exist_ok=True)
        self.db_path = Path(".tmp") / f"test-{uuid.uuid4().hex}.sqlite3"
        self.media_path = Path(".tmp") / f"media-{uuid.uuid4().hex}"
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "clave-de-prueba-no-usar-fuera-de-tests",
                "DATABASE": str(self.db_path.resolve()),
                "PERFIL_MEDIA_FOLDER": str(self.media_path.resolve()),
            }
        )
        self.cliente = self.app.test_client()
        with self.app.app_context():
            inicializar_base_datos()
            self._crear_usuario("admin.demo", "ADMINISTRADOR", "Clave demo segura 123!")
            self._crear_usuario("instructor.demo", "JEFE_PERSONAL", "Clave instructor 123!")
            self._crear_usuario("voluntario.demo", "INSTRUCTOR_VOLUNTARIO", "Clave voluntario 123!")

    def tearDown(self):
        self.cliente = None
        if self.db_path.exists():
            self.db_path.unlink()
        if self.media_path.exists():
            for archivo in self.media_path.iterdir():
                archivo.unlink()
            self.media_path.rmdir()

    def _crear_usuario(self, username, rol, password):
        from sicose.db import obtener_conexion

        conexion = obtener_conexion()
        rol_id = conexion.execute("SELECT id FROM roles WHERE nombre = ?", (rol,)).fetchone()[0]
        conexion.execute(
            """INSERT INTO usuarios (username, nombre_completo, password_hash, rol_id)
               VALUES (?, ?, ?, ?)""",
            (username, username, generate_password_hash(password), rol_id),
        )
        conexion.commit()

    def _login(self, username="admin.demo", password="Clave demo segura 123!"):
        token = self._csrf_token()
        return self.cliente.post(
            "/api/auth/login",
            json={"username": username, "password": password},
            headers={"X-CSRFToken": token},
        )

    def _csrf_token(self):
        pagina = self.cliente.get("/", follow_redirects=True)
        coincidencia = re.search(rb'name="csrf_token" value="([^"]+)"', pagina.data)
        self.assertIsNotNone(coincidencia, "El formulario debe emitir token CSRF")
        return coincidencia.group(1).decode("ascii")

    def _post_alta(self, ruta, **kwargs):
        """Fixture de alta con los datos obligatorios y foto sintética actuales."""
        import io
        datos = dict(kwargs.pop("json", kwargs.pop("data", {})))
        datos.setdefault("correo", f"{datos.get('username', 'demo')}@example.test")
        datos.setdefault("pais_residencia", "Bolivia")
        datos.setdefault("departamento_residencia", "La Paz")
        datos.setdefault("nacionalidad", "Bolivia")
        datos.setdefault("foto", (io.BytesIO(self._png_prueba()), "perfil.png"))
        kwargs["content_type"] = "multipart/form-data"
        return self.cliente.post(ruta, data=datos, **kwargs)

    def test_perfil_grado_incorporacion_estado_y_solicitud_ampliada(self):
        from sicose.db import obtener_conexion
        datos = {**self._datos_alta_4a(), "estado": "INACTIVO", "grado": "Instructor Mayor", "fecha_incorporacion": "2022-12-31"}
        self._login()
        headers = {"X-CSRFToken": self._csrf_token()}
        r = self._post_alta("/api/admin/instructores-voluntarios", json=datos, headers=headers)
        self.assertEqual(r.status_code, 201, r.json)
        uid = r.json["id"]
        perfil = next(v for v in self.cliente.get("/api/instructores-voluntarios").json["voluntarios"] if v["id"] == uid)
        self.assertEqual(perfil["estado"], "INACTIVO")
        self.assertEqual(perfil["grado"], "Instructor Mayor")
        self.assertEqual(perfil["ano_incorporacion"], 2022)
        self.assertEqual(perfil["antiguedad_desde"], "2022-12-31")
        self.assertEqual(perfil["antiguedad_anos"], date.today().year - 2022)
        self.assertEqual(self._login(datos["username"], datos["password"]).status_code, 401)
        self._login()
        ruta = f"/api/instructores-voluntarios/{uid}"
        for invalido in ({"grado": "Almirante"}, {"fecha_incorporacion": "9999-01-01"}, {"fecha_incorporacion": "2020-01-01", "ano_incorporacion": 2021}):
            self.assertEqual(self.cliente.patch(ruta, json=invalido, headers={"X-CSRFToken": self._csrf_token()}).status_code, 400)
        self.assertEqual(self.cliente.patch(ruta, json={"fecha_incorporacion": "2021-06-01"}, headers={"X-CSRFToken": self._csrf_token()}).status_code, 200)
        with self.app.app_context():
            inicializar_base_datos(); inicializar_base_datos()
            c = obtener_conexion()
            self.assertEqual(tuple(c.execute("SELECT fecha_incorporacion,ano_incorporacion,antiguedad_desde,grado FROM voluntarios WHERE usuario_id=?", (uid,)).fetchone()), ("2021-06-01",2021,"2021-06-01","Instructor Mayor"))
            self.assertEqual(c.execute("PRAGMA quick_check").fetchone()[0], "ok")
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])
        # Public applicant cannot set account state or grade, even with a valid photo.
        self.cliente.post('/api/auth/logout', headers={"X-CSRFToken":self._csrf_token()})
        nueva = {**self._datos_alta_4a(), "username":"publica.grado", "nombres":"Pública", "correo":"publica@example.test", "fecha_incorporacion":"2020-02-02"}
        for prohibido in ({"grado":"Instructor Inicial"},{"estado":"ACTIVO"}):
            self.assertEqual(self._post_alta('/api/registro/solicitudes',json={**nueva,**prohibido},headers={"X-CSRFToken":self._csrf_token()}).status_code,400)
        r = self._post_alta('/api/registro/solicitudes',json=nueva,headers={"X-CSRFToken":self._csrf_token()})
        self.assertEqual(r.status_code,201,r.json)
        with self.app.app_context():
            c = obtener_conexion()
            fila=c.execute("SELECT u.estado,v.grado,v.fecha_incorporacion,p.nacionalidad,p.departamento_residencia FROM usuarios u JOIN voluntarios v ON v.usuario_id=u.id JOIN perfil_geografico p ON p.voluntario_id=u.id WHERE u.username='publica.grado'").fetchone()
            self.assertEqual(tuple(fila),('PENDIENTE',None,'2020-02-02','Bolivia','La Paz'))

    def test_grado_ambito_jefe_consulta_propia_y_campos_obligatorios(self):
        from sicose.db import obtener_conexion
        jefe = self._preparar_jefe_4a()
        with self.app.app_context():
            c=obtener_conexion();c.execute("INSERT INTO voluntarios(usuario_id,instructor_id,ano_incorporacion,antiguedad_desde) VALUES (3,?,2020,'2019-01-01')",(jefe,));c.commit()
        self.assertEqual(self.cliente.patch('/api/instructores-voluntarios/3',json={'grado':'Instructor Primero'},headers={"X-CSRFToken":self._csrf_token()}).status_code,200)
        p=self.cliente.get('/api/instructores-voluntarios').json['voluntarios'][0]
        self.assertEqual((p['ano_incorporacion'],p['antiguedad_desde'],p['fecha_incorporacion']),(2020,'2019-01-01',None))
        self._login('voluntario.demo','Clave voluntario 123!')
        self.assertIn(b'Instructor Primero',self.cliente.get('/mi-perfil').data)
        self.assertEqual(self.cliente.patch('/api/instructor-voluntario/perfil',json={'grado':'Instructor Mayor'},headers={"X-CSRFToken":self._csrf_token()}).status_code,400)
        self._login()
        self.cliente.post('/api/instructores-voluntarios/3/desactivar',headers={"X-CSRFToken":self._csrf_token()})
        self._login('instructor.demo','Clave instructor 123!')
        self.assertEqual(self.cliente.patch('/api/instructores-voluntarios/3',json={'grado':'Instructor Mayor'},headers={"X-CSRFToken":self._csrf_token()}).status_code,409)
        # Required profile data and media must also be enforced by the server.
        self._login()
        datos={**self._datos_alta_4a(),'nacionalidad':'Bolivia','departamento_residencia':'La Paz','pais_residencia':'Bolivia'}
        self.assertEqual(self.cliente.post('/api/admin/instructores-voluntarios',json=datos,headers={"X-CSRFToken":self._csrf_token()}).status_code,400)
        for campo in ('correo','nacionalidad','departamento_residencia'):
            self.assertEqual(self._post_alta('/api/admin/instructores-voluntarios',json={**datos,campo:''},headers={"X-CSRFToken":self._csrf_token()}).status_code,400)

    def _preparar_notas_5a(self):
        from sicose.db import obtener_conexion
        jefe=self._preparar_jefe_4a()
        with self.app.app_context():
            c=obtener_conexion()
            c.execute("INSERT INTO voluntarios(usuario_id,instructor_id) VALUES (3,?)",(jefe,))
            periodo=c.execute("INSERT INTO periodos(nombre,fecha_inicio,fecha_fin,estado) VALUES ('DEMO 5A','2026-01-01','2026-12-31','ACTIVO')").lastrowid
            evaluacion=c.execute("INSERT INTO evaluaciones(codigo,nombre,categoria,origen_nota,activo) VALUES ('DEMO5A','Física DEMO','FISICA','JEFE_PERSONAL',1)").lastrowid
            asignacion=c.execute("INSERT INTO asignaciones_evaluacion(voluntario_id,periodo_id,evaluacion_id) VALUES (3,?,?)",(periodo,evaluacion)).lastrowid
            c.commit()
        return asignacion,periodo

    def test_5a_notas_validacion_historial_cierre_y_privacidad(self):
        from sicose.db import obtener_conexion
        aid,pid=self._preparar_notas_5a();ruta=f'/api/jefe-personal/asignaciones/{aid}/calificaciones'
        headers={'X-CSRFToken':self._csrf_token()}
        self.assertEqual(self.cliente.post(ruta,json={'nota_0_100':0}).status_code,400)
        for datos in ({'nota_0_100':True},{'nota_0_100':float('nan')},{'nota_0_100':101},{'nota_0_100':-1},{'nota_0_100':0,'corregida_de_id':True},{'nota_0_100':0,'corregida_de_id':'1'},{'nota_0_100':0,'rol':'ADMINISTRADOR'}):
            self.assertEqual(self.cliente.post(ruta,json=datos,headers=headers).status_code,400)
        r=self.cliente.post(ruta,json={'nota_0_100':0,'observacion':'Privada DEMO'},headers=headers)
        self.assertEqual(r.status_code,201);anterior=r.json['id']
        self.assertEqual(self.cliente.post(ruta,json={'nota_0_100':80},headers=headers).status_code,409)
        self.assertEqual(self.cliente.post(ruta,json={'nota_0_100':100,'corregida_de_id':anterior},headers=headers).status_code,201)
        self.assertEqual(self.cliente.post(ruta,json={'nota_0_100':50,'corregida_de_id':anterior},headers=headers).status_code,409)
        historial=self.cliente.get(ruta).json['historial']
        self.assertEqual([n['nota_0_100'] for n in historial],[0,100])
        self.assertEqual(historial[1]['corregida_de_id'],anterior)
        self.assertTrue(all(n['registrada_por'] and n['registrada_en'] for n in historial))
        with self.app.app_context():
            c=obtener_conexion();c.execute("UPDATE periodos SET estado='CERRADO' WHERE id=?",(pid,));c.commit()
        self.assertEqual(self.cliente.post(ruta,json={'nota_0_100':90,'corregida_de_id':historial[-1]['id']},headers=headers).status_code,409)
        self.assertEqual(self.cliente.get('/api/jefe-personal/asignaciones').json['asignaciones'][0]['periodo_estado'],'CERRADO')
        self._login('voluntario.demo','Clave voluntario 123!')
        self.assertEqual(self.cliente.get(ruta).status_code,403)
        self.assertEqual(self.cliente.get('/gestion/calificaciones').status_code,403)
        propio=self.cliente.get('/api/instructor-voluntario/evaluaciones')
        self.assertNotIn('Privada DEMO',str(propio.json));self.assertNotIn('nota_0_100',str(propio.json))

    def test_5a_notas_simultaneas_no_crean_ramas(self):
        import threading
        from concurrent.futures import ThreadPoolExecutor
        from sicose.db import obtener_conexion
        aid,_=self._preparar_notas_5a();ruta=f'/api/jefe-personal/asignaciones/{aid}/calificaciones'
        self._login()
        clientes=[]
        for _ in range(2):
            cli=self.app.test_client();token=re.search(rb'name="csrf_token" value="([^"]+)"',cli.get('/login').data).group(1).decode()
            self.assertEqual(cli.post('/api/auth/login',json={'username':'admin.demo','password':'Clave demo segura 123!'},headers={'X-CSRFToken':token}).status_code,200)
            token=re.search(rb'name="csrf_token" value="([^"]+)"',cli.get('/',follow_redirects=True).data).group(1).decode()
            clientes.append((cli,token))
        for base in (None,'ultima'):
            with self.app.app_context():
                row=obtener_conexion().execute('SELECT id FROM calificaciones ORDER BY id DESC LIMIT 1').fetchone()
            anterior=row[0] if base else None;barrier=threading.Barrier(2)
            def guardar(par):
                cli,token=par;datos={'nota_0_100':80}
                if anterior is not None:datos['corregida_de_id']=anterior
                barrier.wait(timeout=5)
                return cli.post(ruta,json=datos,headers={'X-CSRFToken':token}).status_code
            with ThreadPoolExecutor(max_workers=2) as pool:resultados=list(pool.map(guardar,clientes))
            self.assertEqual(sorted(resultados),[201,409])
        with self.app.app_context():
            notas=obtener_conexion().execute('SELECT id,corregida_de_id FROM calificaciones ORDER BY id').fetchall()
            self.assertEqual(len(notas),2);self.assertEqual(notas[1][1],notas[0][0])

    def test_5a_capacitacion_edicion_preserva_nombre_y_valida_fecha(self):
        from sicose.db import obtener_conexion
        self._preparar_notas_5a()
        with self.app.app_context():
            c=obtener_conexion();curso=c.execute("INSERT INTO cursos(nombre) VALUES ('Nombre original DEMO')").lastrowid;c.commit()
        ruta='/api/jefe-personal/instructores-voluntarios/3/capacitaciones';h={'X-CSRFToken':self._csrf_token()}
        for fecha in (False,0,20261011,[], '20261011'):
            self.assertEqual(self.cliente.post(ruta,json={'curso_id':curso,'fecha':fecha},headers=h).status_code,400)
        r=self.cliente.post(ruta,json={'curso_id':curso,'fecha':'2026-10-11','observacion':'Privada'},headers=h);self.assertEqual(r.status_code,201)
        cid=r.json['id']
        with self.app.app_context():
            c=obtener_conexion();c.execute("UPDATE cursos SET nombre='Nombre nuevo DEMO' WHERE id=?",(curso,));c.commit()
        self.assertEqual(self.cliente.patch(f'/api/jefe-personal/capacitaciones/{cid}',json={'observacion':'Corrección'},headers=h).status_code,200)
        self.assertEqual(self.cliente.get('/api/jefe-personal/capacitaciones').json['capacitaciones'][0]['nombre'],'Nombre original DEMO')
        self._login('voluntario.demo','Clave voluntario 123!')
        datos=self.cliente.get('/api/instructor-voluntario/capacitaciones').json['capacitaciones'][0]
        self.assertEqual(datos['nombre'],'Nombre original DEMO');self.assertNotIn('observacion',datos)

    def test_5a_notas_jefe_global_sin_asignacion_historial_preservado(self):
        from sicose.db import obtener_conexion
        aid,_=self._preparar_notas_5a();ruta=f'/api/jefe-personal/asignaciones/{aid}/calificaciones';h={'X-CSRFToken':self._csrf_token()}
        self.assertEqual(self.cliente.post(ruta,json={'nota_0_100':75},headers=h).status_code,201)
        with self.app.app_context():
            c=obtener_conexion();c.execute('UPDATE voluntarios SET instructor_id=NULL WHERE usuario_id=3');c.commit()
        self.assertEqual(self.cliente.get(ruta).status_code,200)
        anterior=self.cliente.get(ruta).json['historial'][0]['id']
        self.assertEqual(self.cliente.post(ruta,json={'nota_0_100':80,'corregida_de_id':anterior},headers=h).status_code,201)
        self._login()
        self.assertEqual(len(self.cliente.get(ruta).json['historial']),2)

    def _configurar_periodo_5b(self,pid):
        from sicose.db import obtener_conexion
        self._login()
        with self.app.app_context():
            c=obtener_conexion();eids={}
            for categoria in ('FISICA','ACADEMICA','JEFE_PERSONAL'):
                e=c.execute("SELECT id FROM evaluaciones WHERE categoria=? AND activo=1 AND origen_nota='JEFE_PERSONAL' LIMIT 1",(categoria,)).fetchone()
                if e is None:
                    eid=c.execute("INSERT INTO evaluaciones(codigo,nombre,categoria,origen_nota,activo) VALUES (?,?,?,'JEFE_PERSONAL',1)",('CFG-'+categoria,'Evaluación '+categoria,categoria)).lastrowid
                else:eid=e[0]
                eids[categoria]=eid
            c.commit()
        fuentes={'FISICA_1':eids['FISICA'],'FISICA_2':eids['FISICA'],'ACADEMICA':eids['ACADEMICA'],'DESEMPENO_JEFE':eids['JEFE_PERSONAL'],'DESEMPENO_COMANDANTE':eids['JEFE_PERSONAL']}
        h={'X-CSRFToken':self._csrf_token()}
        r=self.cliente.post(f'/api/admin/5b/periodos/{pid}/configuracion',json={'fuentes':fuentes},headers=h);self.assertEqual(r.status_code,201,r.json)
        return r.json['configuracion'],fuentes

    def _preparar_notas_5b(self):
        from sicose.db import obtener_conexion
        aid,pid=self._preparar_notas_5a()
        with self.app.app_context():
            c=obtener_conexion();c.execute("UPDATE periodos SET estado='BORRADOR' WHERE id=?",(pid,));c.commit()
        conf,_=self._configurar_periodo_5b(pid)
        r=self.cliente.post(f'/api/admin/5b/periodos/{pid}/publicar',json={'revision':conf['revision']},headers={'X-CSRFToken':self._csrf_token()});self.assertEqual(r.status_code,200,r.json)
        self._login('instructor.demo','Clave instructor 123!')
        for fuente in ('FISICA_1','FISICA_2','ACADEMICA','DESEMPENO_JEFE','DESEMPENO_COMANDANTE'):
            r=self.cliente.patch('/api/evaluaciones/personas/3/habilitacion',json={'periodo_id':pid,'clave':fuente,'habilitada':True},headers={'X-CSRFToken':self._csrf_token()});self.assertEqual(r.status_code,200,r.json)
        return aid,pid

    def test_5b_comandante_retirado_sin_borrar_historial(self):
        from sicose.db import obtener_conexion
        with self.app.app_context():
            self._crear_usuario('comandante.demo','COMANDANTE_GRUPO','Clave comandante 123!')
        self.assertEqual(self._login('comandante.demo','Clave comandante 123!').status_code,401)
        self._login();h={'X-CSRFToken':self._csrf_token()}
        self.assertEqual(self.cliente.post('/api/admin/comandantes',json={'nombre':'Nuevo'},headers=h).status_code,410)
        historicos=self.cliente.get('/api/admin/comandantes').json['comandantes']
        self.assertEqual(len(historicos),1);self.assertEqual(historicos[0]['estado'],'ACTIVO')
        self.assertNotIn(b'Comandante SBRAB',self.cliente.get('/',follow_redirects=True).data)
        # Existing sessions no longer load as active operational users.
        with self.cliente.session_transaction() as ses:
            ses['_user_id']=str(historicos[0]['id']);ses['sicose_password_version']=1
        self.assertEqual(self.cliente.get('/api/auth/me').status_code,401)

    def test_5b_transcripcion_comandante_por_admin_jefe_privacidad_y_autoria(self):
        _,pid=self._preparar_notas_5b();ruta='/api/5b/personas/3/notas';h={'X-CSRFToken':self._csrf_token()}
        base={'periodo_id':pid,'fuente':'DESEMPENO_COMANDANTE','nota_0_100':'80.01'}
        self.assertEqual(self.cliente.post(ruta,json=base,headers=h).status_code,400)
        r=self.cliente.post(ruta,json={**base,'comandante_nombre':'Comandante DEMO'},headers=h);self.assertEqual(r.status_code,201,r.json)
        nid=r.json['id'];self._login();h={'X-CSRFToken':self._csrf_token()}
        self.assertEqual(self.cliente.post(ruta,json={**base,'comandante_nombre':'Comandante DEMO','nota_0_100':'90','corregida_de_id':nid},headers=h).status_code,201)
        notas=self.cliente.get(f'/api/5b/personas/3?periodo_id={pid}').json['notas']
        self.assertEqual(len(notas),2);self.assertEqual(notas[-1]['evaluador_nombre'],'Comandante DEMO')
        self.assertEqual((notas[0]['registrada_por'],notas[-1]['registrada_por']),(2,1))
        self._login('voluntario.demo','Clave voluntario 123!')
        self.assertEqual(self.cliente.get(f'/api/5b/personas/3?periodo_id={pid}').status_code,403)
        propias=self.cliente.get(f'/api/evaluaciones/propias?periodo_id={pid}').json
        self.assertNotIn('90.00',str(propias));self.assertNotIn('Comandante DEMO',str(propias));self.assertNotIn('nota_id',str(propias))

    def test_5b_respaldo_precision_periodo_y_ambito(self):
        from sicose.db import obtener_conexion
        _,pid=self._preparar_notas_5b();ruta='/api/5b/personas/3/notas';h={'X-CSRFToken':self._csrf_token()}
        with self.app.app_context():
            c=obtener_conexion();ref=c.execute("INSERT INTO capacitaciones(voluntario_id,nombre,fecha) VALUES (3,'Nombre respaldo','2026-10-01')").lastrowid;c.commit()
        base={'periodo_id':pid,'fuente':'ACADEMICA','nota_0_100':'0.00','motivo':'','capacitaciones':[ref]}
        for extra in ({'motivo':123},{'capacitaciones':[]},{'capacitaciones':[9999]},{'capacitaciones':[ref,ref]},{'nota_0_100':True},{'nota_0_100':'82.345'},{'nota_0_100':'NaN'},{'nota_0_100':'101'},{'evaluador_id':1}):
            self.assertEqual(self.cliente.post(ruta,json={**base,**extra},headers=h).status_code,400)
        r=self.cliente.post(ruta,json=base,headers=h);self.assertEqual(r.status_code,201,r.json)
        with self.app.app_context():
            c=obtener_conexion();c.execute("UPDATE capacitaciones SET nombre='Renombrado' WHERE id=?",(ref,));c.commit()
        datos=self.cliente.get(f'/api/5b/personas/3?periodo_id={pid}').json
        self.assertEqual(datos['notas'][0]['nota_0_100'],'0.00');self.assertEqual(datos['notas'][0]['referencias'][0]['nombre'],'Nombre respaldo')
        for estado in ('BORRADOR','CERRADO'):
            with self.app.app_context():
                c=obtener_conexion();c.execute('UPDATE periodos SET estado=? WHERE id=?',(estado,pid));c.commit()
            self.assertEqual(self.cliente.post(ruta,json={**base,'corregida_de_id':r.json['id']},headers=h).status_code,409)
        with self.app.app_context():
            c=obtener_conexion();c.execute('UPDATE voluntarios SET instructor_id=NULL WHERE usuario_id=3');c.commit()
        self.assertEqual(self.cliente.get(f'/api/5b/personas/3?periodo_id={pid}').status_code,200)

    def test_5b_notas_concurrentes_cadena_unica(self):
        import threading
        from concurrent.futures import ThreadPoolExecutor
        from sicose.db import obtener_conexion
        _,pid=self._preparar_notas_5b();clientes=[]
        for _ in range(2):
            cli=self.app.test_client();token=re.search(rb'name="csrf_token" value="([^"]+)"',cli.get('/login').data).group(1).decode()
            self.assertEqual(cli.post('/api/auth/login',json={'username':'instructor.demo','password':'Clave instructor 123!'},headers={'X-CSRFToken':token}).status_code,200)
            token=re.search(rb'name="csrf_token" value="([^"]+)"',cli.get('/',follow_redirects=True).data).group(1).decode();clientes.append((cli,token))
        for paso in range(2):
            with self.app.app_context():row=obtener_conexion().execute('SELECT id FROM notas_operativas ORDER BY id DESC LIMIT 1').fetchone()
            anterior=row[0] if row else None;barrier=threading.Barrier(2)
            def guardar(par):
                cli,token=par;body={'periodo_id':pid,'fuente':'FISICA_1','nota_0_100':'75.01'}
                if anterior:body['corregida_de_id']=anterior
                barrier.wait(timeout=5)
                return cli.post('/api/5b/personas/3/notas',json=body,headers={'X-CSRFToken':token}).status_code
            with ThreadPoolExecutor(max_workers=2) as pool:estados=list(pool.map(guardar,clientes))
            self.assertEqual(sorted(estados),[201,409])
        with self.app.app_context():
            c=obtener_conexion();self.assertEqual(c.execute('SELECT COUNT(*) FROM notas_operativas').fetchone()[0],2)
            self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(),[])

    def _curso_participacion(self):
        from sicose.db import obtener_conexion
        self._login()
        with self.app.app_context():
            c=obtener_conexion();c.execute('INSERT INTO voluntarios(usuario_id) VALUES (3)');c.commit()
        datos={'nombre':'Curso operativo DEMO','tipo':'Taller','entidad':'Entidad DEMO','fecha_inicio':'2020-01-01','fecha_fin':'2020-01-31','puntaje':25}
        r=self.cliente.post('/api/cursos',json=datos,headers={'X-CSRFToken':self._csrf_token()});self.assertEqual(r.status_code,201,r.json)
        return r.json['id']

    def test_formacion_migracion_v17_preserva_catalogo_e_historial_sin_adopcion(self):
        from contextlib import closing
        from sicose.db import obtener_conexion
        from sicose.formacion import proyectar_curso
        ruta=Path('.tmp')/f'formacion-v17-{uuid.uuid4().hex}.sqlite3'
        try:
            esquema=Path('sicose/schema.sql').read_text(encoding='utf-8').split('CREATE TABLE IF NOT EXISTS participaciones_curso')[0]
            esquema=esquema.replace(" observaciones TEXT,"+chr(10)+" puntaje INTEGER CHECK(puntaje IS NULL OR (typeof(puntaje)='integer' AND puntaje BETWEEN 0 AND 100))", " observaciones TEXT")
            with closing(sqlite3.connect(ruta)) as c:
                c.executescript(esquema);c.execute("ALTER TABLE capacitaciones ADD COLUMN curso_id INTEGER REFERENCES cursos(id) ON DELETE RESTRICT");c.execute("INSERT INTO roles(id,nombre) VALUES (1,'INSTRUCTOR_VOLUNTARIO')")
                c.execute("INSERT INTO usuarios(id,username,nombre_completo,password_hash,rol_id) VALUES (3,'historico.demo','Histórico DEMO','hash-sintetico',1)")
                c.execute('INSERT INTO voluntarios(usuario_id) VALUES (3)')
                c.execute("INSERT INTO cursos(id,nombre,estado) VALUES (10,'Curso histórico DEMO','Finalizado')")
                c.execute("INSERT INTO capacitaciones(voluntario_id,nombre,curso_id,fecha,observacion) VALUES (3,'Nombre histórico propio',10,'2020-10-01','Observación conservada')")
                c.execute("INSERT INTO app_meta(clave,valor) VALUES ('schema_version','17')");c.commit()
            app=create_app({'TESTING':True,'SECRET_KEY':'prueba-sintetica','DATABASE':str(ruta.resolve())})
            with app.app_context():
                inicializar_base_datos();inicializar_base_datos();c=obtener_conexion()
                curso=c.execute('SELECT * FROM cursos').fetchone();self.assertEqual((curso['nombre'],curso['estado'],curso['puntaje']),('Curso histórico DEMO','Finalizado',None))
                self.assertIsNone(proyectar_curso(curso)['estado']);self.assertEqual(c.execute('SELECT nombre,curso_id,fecha,observacion FROM capacitaciones').fetchone()[0],'Nombre histórico propio')
                self.assertEqual(c.execute('SELECT COUNT(*) FROM participaciones_curso').fetchone()[0],0);self.assertEqual(c.execute('SELECT COUNT(*) FROM historial_participaciones_curso').fetchone()[0],0)
                self.assertEqual(c.execute('PRAGMA quick_check').fetchone()[0],'ok');self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(),[])
        finally:
            if ruta.exists():ruta.unlink()

    def test_formacion_estado_automatico_limites_y_puntajes_enteros(self):
        from unittest.mock import patch
        from sicose.formacion import proyectar_curso
        base={'fecha_inicio':'2026-10-01','fecha_fin':'2026-10-10','estado':'Próximo'}
        for hoy,esperado in [(date(2026,9,30),'Próximo'),(date(2026,10,1),'En curso'),(date(2026,10,10),'En curso'),(date(2026,10,11),'Finalizado')]:
            self.assertEqual(proyectar_curso(base,hoy)['estado'],esperado)
        self.assertIsNone(proyectar_curso({'fecha_inicio':None,'fecha_fin':None,'estado':'Finalizado'})['estado'])
        from datetime import datetime,timezone
        from sicose.formacion import hoy_bolivia
        class Reloj(datetime):
            @classmethod
            def now(cls,tz=None):return cls(2026,10,13,2,0,tzinfo=timezone.utc).astimezone(tz)
        with patch('sicose.formacion.datetime',Reloj):self.assertEqual(hoy_bolivia(),date(2026,10,12))
        cid=self._curso_participacion();h={'X-CSRFToken':self._csrf_token()}
        with patch('sicose.formacion.hoy_bolivia',return_value=date(2020,1,1)):
            self.assertEqual(self.cliente.get('/api/cursos').json['cursos'][0]['estado'],'En curso')
        for valor in (-1,101,True,1.5,'10',None):
            self.assertEqual(self.cliente.patch(f'/api/cursos/{cid}',json={'puntaje':valor},headers=h).status_code,400)
        for valor in (0,100):self.assertEqual(self.cliente.patch(f'/api/cursos/{cid}',json={'puntaje':valor},headers=h).status_code,200)
        for cambio in ({'estado':'Finalizado'},{'fecha_inicio':''},{'fecha_fin':'2019-12-31'},{'entidad':''}):
            self.assertEqual(self.cliente.patch(f'/api/cursos/{cid}',json=cambio,headers=h).status_code,400)
        self.assertEqual(self.cliente.get('/api/cursos').json['cursos'][0]['puntaje'],100)

    def test_formacion_asignacion_atomica_snapshots_historia_y_privacidad(self):
        from sicose.db import obtener_conexion
        cid=self._curso_participacion();h={'X-CSRFToken':self._csrf_token()};ruta=f'/api/cursos/{cid}/participantes'
        self.assertEqual(self.cliente.post(ruta,json={'voluntario_ids':[3,999]},headers=h).status_code,400)
        self.assertEqual(self.cliente.get(ruta).json['participantes'],[])
        self.assertEqual(self.cliente.post(ruta,json={'voluntario_ids':[3]},headers=h).status_code,201)
        self.assertEqual(self.cliente.post(ruta,json={'voluntario_ids':[3]},headers=h).status_code,409)
        p=self.cliente.get(ruta).json['participantes'][0];self.assertEqual((p['estado'],p['puntaje'],p['puntaje_base']),('Asignado',None,25))
        self.assertEqual(self.cliente.patch(f'/api/cursos/{cid}',json={'nombre':'Renombrado DEMO','puntaje':100,'fecha_inicio':'2030-01-01','fecha_fin':'2030-02-01'},headers=h).status_code,200)
        self.assertEqual(self.cliente.get(ruta).json['participantes'][0]['nombre_curso'],'Curso operativo DEMO')
        self._login('instructor.demo','Clave instructor 123!');h={'X-CSRFToken':self._csrf_token()}
        cambio={'revision':1,'estado':'Finalizado','puntaje':10,'fecha_finalizacion':'2020-01-10','motivo':'Finalización individual DEMO'}
        url=f"/api/formacion/participaciones/{p['id']}"
        self.assertEqual(self.cliente.patch(url,json=cambio,headers=h).status_code,200)
        self.assertEqual(self.cliente.patch(url,json=cambio,headers=h).status_code,409)
        self.assertEqual(self.cliente.patch(url,json={**cambio,'revision':2,'puntaje':0,'fecha_finalizacion':'2021-01-10','motivo':'Corrección de fecha y puntaje'},headers=h).status_code,200)
        historia=self.cliente.get(url+'/historial').json['historial'];self.assertEqual([r['puntaje'] for r in historia],[None,10,0]);self.assertEqual([r['registrada_por'] for r in historia],[1,2,2])
        self.assertEqual(self.cliente.patch(url,json={'revision':3,'estado':'No completado','motivo':'Rectificación de cumplimiento'},headers=h).status_code,200)
        self.assertEqual(self.cliente.get(ruta).json['participantes'][0]['puntaje'],None)
        self.assertEqual(self.cliente.get(url+'/historial').json['historial'][2]['fecha_finalizacion'],'2021-01-10')
        with self.app.app_context():
            c=obtener_conexion();self.assertEqual(c.execute('SELECT COUNT(*) FROM participaciones_curso').fetchone()[0],1);self.assertEqual(c.execute('SELECT COUNT(*) FROM calificaciones').fetchone()[0],0)
        self._login('voluntario.demo','Clave voluntario 123!')
        propia=self.cliente.get('/api/instructor-voluntario/formacion').json['participaciones'][0]
        self.assertEqual(self.cliente.get('/api/instructor-voluntario/formacion?voluntario_id=1').status_code,400)
        self.assertEqual(propia['estado'],'No completado');self.assertNotIn('puntaje',propia);self.assertNotIn('motivo',propia);self.assertNotIn('registrada_por',propia)
        self.assertEqual(self.cliente.get(ruta).status_code,403);self.assertEqual(self.cliente.get(url+'/historial').status_code,403)
        self.assertIn(b'Cantidad de Cursos Completados',self.cliente.get('/',follow_redirects=True).data)

    def test_formacion_fechas_revision_csrf_inactivos_y_sin_finalizacion_automatica(self):
        from sicose.db import obtener_conexion
        cid=self._curso_participacion();ruta=f'/api/cursos/{cid}/participantes';h={'X-CSRFToken':self._csrf_token()}
        self.assertEqual(self.cliente.post(ruta,json={'voluntario_ids':[3]}).status_code,400)
        self.assertEqual(self.cliente.post(ruta,json={'voluntario_ids':[3]},headers=h).status_code,201)
        p=self.cliente.get(ruta).json['participantes'][0];self.assertEqual(self.cliente.get('/api/cursos').json['cursos'][0]['estado'],'Finalizado');self.assertEqual(p['estado'],'Asignado')
        url=f"/api/formacion/participaciones/{p['id']}";base={'estado':'Finalizado','puntaje':25,'fecha_finalizacion':'2020-01-10','revision':1,'motivo':''}
        for cambio in ({'puntaje':True},{'puntaje':1.5},{'fecha_finalizacion':'2035-01-01'},{'fecha_finalizacion':'2019-12-31'},{'motivo':123},{'revision':True},{'voluntario_id':3}):
            self.assertEqual(self.cliente.patch(url,json={**base,**cambio},headers=h).status_code,400)
        self.assertEqual(self.cliente.patch(url,json={**base,'estado':'En curso'},headers=h).status_code,400)
        with self.app.app_context():
            c=obtener_conexion();c.execute("UPDATE usuarios SET estado='INACTIVO' WHERE id=3");c.commit()
        self.assertEqual(self.cliente.patch(url,json=base,headers=h).status_code,409)
        self.assertEqual(self.cliente.get(url+'/historial').status_code,200)
        with self.app.app_context():
            c=obtener_conexion();c.execute("UPDATE usuarios SET estado='ACTIVO' WHERE id=3");c.commit()
        self.assertEqual(self.cliente.patch(url,json=base,headers=h).status_code,200)
        self.assertEqual(self.cliente.patch(url,json={**base,'revision':2},headers=h).status_code,200)
        self.assertEqual(len(self.cliente.get(url+'/historial').json['historial']),2)

    def test_formacion_concurrencia_no_crea_duplicados_ni_ramas(self):
        import threading
        from concurrent.futures import ThreadPoolExecutor
        cid=self._curso_participacion();clientes=[]
        for _ in range(2):
            cli=self.app.test_client();token=re.search(rb'name="csrf_token" value="([^"]+)"',cli.get('/login').data).group(1).decode()
            cli.post('/api/auth/login',json={'username':'instructor.demo','password':'Clave instructor 123!'},headers={'X-CSRFToken':token})
            token=re.search(rb'name="csrf_token" value="([^"]+)"',cli.get('/',follow_redirects=True).data).group(1).decode();clientes.append((cli,token))
        barrier=threading.Barrier(2)
        def asignar(par):
            cli,t=par;barrier.wait(timeout=5);return cli.post(f'/api/cursos/{cid}/participantes',json={'voluntario_ids':[3]},headers={'X-CSRFToken':t}).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:estados=list(pool.map(asignar,clientes))
        self.assertEqual(sorted(estados),[201,409]);p=self.cliente.get(f'/api/cursos/{cid}/participantes').json['participantes'][0]
        barrier=threading.Barrier(2)
        def finalizar(par):
            cli,t=par;barrier.wait(timeout=5);return cli.patch(f"/api/formacion/participaciones/{p['id']}",json={'revision':1,'estado':'Finalizado','puntaje':15,'fecha_finalizacion':'2020-01-15','motivo':'Finalización concurrente DEMO'},headers={'X-CSRFToken':t}).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:estados=list(pool.map(finalizar,clientes))
        self.assertEqual(sorted(estados),[200,409]);self.assertEqual(len(self.cliente.get(f"/api/formacion/participaciones/{p['id']}/historial").json['historial']),2)

    def test_reformulacion_jefe_unico_preserva_cuentas_anteriores(self):
        from sicose.db import obtener_conexion
        self._login();h={'X-CSRFToken':self._csrf_token()}
        nuevo={'username':'jefe.nuevo','nombre':'Nuevo responsable','password':'Clave nuevo jefe 123!'}
        self.assertEqual(self.cliente.post('/api/admin/jefes-personal',json=nuevo,headers=h).status_code,409)
        with self.app.app_context():
            c=obtener_conexion();c.execute("UPDATE usuarios SET estado='INACTIVO' WHERE id=2");c.commit()
        r=self.cliente.post('/api/admin/jefes-personal',json=nuevo,headers=h);self.assertEqual(r.status_code,201,r.json)
        with self.app.app_context():
            c=obtener_conexion()
            with self.assertRaises(sqlite3.IntegrityError):c.execute("UPDATE usuarios SET estado='ACTIVO' WHERE id=2")
            c.rollback();self.assertEqual(c.execute("SELECT COUNT(*) FROM usuarios u JOIN roles r ON r.id=u.rol_id WHERE r.nombre='JEFE_PERSONAL'").fetchone()[0],2)

    def test_reformulacion_tabla_habilitacion_inactivos_csrf_e_historial(self):
        from sicose.db import obtener_conexion
        _,pid=self._preparar_notas_5b();ruta='/api/evaluaciones/personas/3/habilitacion';h={'X-CSRFToken':self._csrf_token()}
        body={'periodo_id':pid,'clave':'FISICA_1','habilitada':False}
        self.assertEqual(self.cliente.patch(ruta,json=body).status_code,400)
        self.assertEqual(self.cliente.patch(ruta,json={**body,'habilitada':1},headers=h).status_code,400)
        nota={'periodo_id':pid,'fuente':'FISICA_1','nota_0_100':'80'}
        r=self.cliente.post('/api/5b/personas/3/notas',json=nota,headers=h);self.assertEqual(r.status_code,201)
        self.assertEqual(self.cliente.patch(ruta,json=body,headers=h).status_code,200)
        self.assertEqual(self.cliente.post('/api/5b/personas/3/notas',json={**nota,'corregida_de_id':r.json['id']},headers=h).status_code,409)
        datos=self.cliente.get(f'/api/evaluaciones/tabla?periodo_id={pid}').json
        e=datos['personas'][0]['evaluaciones'][0];self.assertEqual((e['habilitada'],e['estado'],e['nota']),(False,'FINALIZADA','80.00'))
        with self.app.app_context():
            c=obtener_conexion();c.execute("UPDATE usuarios SET estado='INACTIVO' WHERE id=3");c.execute('UPDATE voluntarios SET instructor_id=NULL WHERE usuario_id=3');c.commit()
        self.assertEqual(self.cliente.get(f'/api/5b/personas/3?periodo_id={pid}').status_code,200)
        self.assertEqual(self.cliente.get(f'/api/evaluaciones/tabla?periodo_id={pid}').json['personas'][0]['estado'],'INACTIVO')
        self.assertEqual(self.cliente.patch(ruta,json={**body,'habilitada':True},headers=h).status_code,409)
        self.assertEqual(self.cliente.post('/api/5b/personas/3/notas',json={**nota,'corregida_de_id':r.json['id']},headers=h).status_code,409)
        self.assertEqual(self.cliente.get('/gestion/evaluaciones').status_code,200)
        self.assertEqual(self.cliente.get('/api/admin/evaluaciones').status_code,200)
        self.assertEqual(self.cliente.get(f'/api/evaluaciones/tabla?periodo_id={pid}&periodo_id=2').status_code,400)

    def test_reformulacion_proyeccion_propia_y_pdf_por_gestion(self):
        from sicose.db import obtener_conexion
        _,pid=self._preparar_notas_5b();h={'X-CSRFToken':self._csrf_token()}
        nota={'periodo_id':pid,'fuente':'DESEMPENO_COMANDANTE','nota_0_100':'95','comandante_nombre':'Evaluador externo DEMO','observacion':'Privada'}
        self.assertEqual(self.cliente.post('/api/5b/personas/3/notas',json=nota,headers=h).status_code,201)
        r=self.cliente.get(f'/api/evaluaciones/reporte.pdf?periodo_id={pid}');self.assertEqual(r.status_code,200);self.assertTrue(r.data.startswith(b'%PDF'));self.assertEqual(r.headers['Cache-Control'],'private, no-store')
        self.assertEqual(self.cliente.get('/api/evaluaciones/reporte.pdf').status_code,400)
        with self.app.app_context():
            c=obtener_conexion();otro=c.execute("INSERT INTO periodos(nombre,fecha_inicio,fecha_fin,estado) VALUES ('Otro año','2027-01-01','2027-12-31','BORRADOR')").lastrowid;c.commit()
        self.assertTrue(all(e['nota'] is None for e in self.cliente.get(f'/api/evaluaciones/tabla?periodo_id={otro}').json['personas'][0]['evaluaciones']))
        self._login('voluntario.demo','Clave voluntario 123!')
        self.assertEqual(self.cliente.get('/mis-evaluaciones').status_code,200)
        datos=self.cliente.get(f'/api/evaluaciones/propias?periodo_id={pid}').json
        self.assertTrue(all(set(e)=={'clave','nombre','habilitada','activa','estado'} for e in datos['evaluaciones']))
        self.assertNotIn('Privada',str(datos));self.assertNotIn('Evaluador externo DEMO',str(datos));self.assertNotIn('95.00',str(datos))
        self.assertEqual(self.cliente.get(f'/api/evaluaciones/tabla?periodo_id={pid}').status_code,403)
        self.assertEqual(self.cliente.get(f'/api/evaluaciones/reporte.pdf?periodo_id={pid}').status_code,403)
        propios=self.cliente.get(f'/api/evaluaciones/propias?periodo_id={otro}').json
        self.assertIsNone(propios['resumen']['avance']);self.assertEqual(propios['resumen']['habilitadas'],0)

    def test_reformulacion_psicometria_sigue_condicionada(self):
        _,pid=self._preparar_notas_5b();h={'X-CSRFToken':self._csrf_token()}
        from sicose.db import obtener_conexion
        with self.app.app_context():
            c=obtener_conexion();iid=c.execute("INSERT INTO instrumentos(nombre,version,idioma,estado_aprobacion) VALUES ('Instrumento sintético','1','es','PENDIENTE')").lastrowid
            eid=c.execute("INSERT INTO evaluaciones(codigo,nombre,categoria,origen_nota,instrumento_id,activo) VALUES ('PSICO-DEMO','Psico pendiente','PSICOMETRICA','INSTRUCTOR_VOLUNTARIO',?,1)",(iid,)).lastrowid;c.commit()
        self.assertEqual(self.cliente.patch('/api/evaluaciones/personas/3/habilitacion',json={'periodo_id':pid,'clave':f'PSICO:{eid}','habilitada':True},headers=h).status_code,409)
        self.assertEqual(self.cliente.patch('/api/evaluaciones/personas/3/habilitacion',json={'periodo_id':pid,'clave':f'PSICO:{eid}','habilitada':False},headers=h).status_code,200)
        with self.app.app_context():
            c=obtener_conexion();self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(),[])

    def test_5b_migracion_v14_preserva_roles_identidad_e_historia(self):
        from sicose.db import obtener_conexion
        from contextlib import closing
        ruta=Path('.tmp')/f'migracion14-{uuid.uuid4().hex}.sqlite3'
        try:
            esquema=Path('sicose/schema.sql').read_text(encoding='utf-8').split('CREATE TABLE IF NOT EXISTS notas_operativas')[0].replace(", 'COMANDANTE_GRUPO'",'')
            with closing(sqlite3.connect(ruta)) as c:
                c.executescript(esquema)
                c.execute("INSERT INTO roles(id,nombre) VALUES (41,'ADMINISTRADOR'),(42,'JEFE_PERSONAL'),(43,'INSTRUCTOR_VOLUNTARIO')")
                c.execute("INSERT INTO usuarios(id,username,nombre_completo,password_hash,rol_id) VALUES (51,'historico.demo','Histórico DEMO','hash-demo-no-login',43)")
                c.execute("INSERT INTO voluntarios(usuario_id,ano_incorporacion,antiguedad_desde) VALUES (51,2020,'2019-01-01')")
                c.execute("INSERT INTO capacitaciones(voluntario_id,nombre) VALUES (51,'Historia conservada')")
                c.execute("INSERT INTO app_meta(clave,valor) VALUES ('schema_version','14')");c.commit()
            app=create_app({'TESTING':True,'SECRET_KEY':'secreto-sintetico','DATABASE':str(ruta.resolve())})
            with app.app_context():
                inicializar_base_datos();inicializar_base_datos();c=obtener_conexion()
                self.assertEqual(c.execute("SELECT id FROM roles WHERE nombre='INSTRUCTOR_VOLUNTARIO'").fetchone()[0],43)
                self.assertEqual(tuple(c.execute('SELECT usuario_id,ano_incorporacion,antiguedad_desde FROM voluntarios').fetchone()),(51,2020,'2019-01-01'))
                self.assertEqual(c.execute('SELECT nombre FROM capacitaciones').fetchone()[0],'Historia conservada')
                self.assertEqual(c.execute('SELECT COUNT(*) FROM notas_operativas').fetchone()[0],0)
                self.assertEqual(c.execute('SELECT COUNT(*) FROM usuarios').fetchone()[0],1)
                self.assertEqual(c.execute('PRAGMA quick_check').fetchone()[0],'ok');self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(),[])
        finally:
            if ruta.exists():ruta.unlink()

    def test_5b_gestiones_admin_jefe_y_configuracion_solo_admin(self):
        self._login();h={'X-CSRFToken':self._csrf_token()}
        r=self.cliente.post('/api/admin/5b/periodos',json={'nombre':'Gestión DEMO','ano':2026},headers=h);self.assertEqual(r.status_code,201)
        pid=r.json['id'];url=f'/api/admin/5b/periodos/{pid}'
        conf,fuentes=self._configurar_periodo_5b(pid);h={'X-CSRFToken':self._csrf_token()}
        cambio={'nombre':'Gestión siguiente DEMO','ano':2027,'nombre_anterior':'Gestión DEMO','ano_anterior':2026}
        self.assertEqual(self.cliente.patch(url,json=cambio).status_code,400)
        self.assertEqual(self.cliente.patch(url,json={**cambio,'ano':True},headers=h).status_code,400)
        self.assertEqual(self.cliente.patch(url,json=cambio,headers=h).status_code,200)
        fila=self.cliente.get('/api/admin/5b/periodos').json['periodos'][0]
        self.assertEqual((fila['nombre'],fila['fecha_inicio'],fila['fecha_fin']),('Gestión siguiente DEMO','2027-01-01','2027-12-31'))
        self.assertEqual(fila['configuracion']['revision'],conf['revision']+1)
        self.assertEqual(self.cliente.patch(url,json=cambio,headers=h).status_code,409)
        self.assertEqual(self.cliente.post(url+'/publicar',json={'revision':conf['revision']},headers=h).status_code,409)
        self.assertEqual(self.cliente.post(url+'/publicar',json={'revision':fila['configuracion']['revision']},headers=h).status_code,200)
        self.assertEqual(self.cliente.patch(url,json={**cambio,'nombre_anterior':fila['nombre'],'ano_anterior':2027,'ano':2028},headers=h).status_code,409)
        admin=self.cliente.get('/',follow_redirects=True).data
        self.assertIn('aria-label="Gestión"'.encode(),admin)
        for username,pw in [('instructor.demo','Clave instructor 123!'),('voluntario.demo','Clave voluntario 123!')]:
            self._login(username,pw);h={'X-CSRFToken':self._csrf_token()}
            jefe=username=='instructor.demo'
            panel=self.cliente.get('/',follow_redirects=True).data
            self.assertEqual('aria-label="Gestión"'.encode() in panel,jefe)
            self.assertEqual(self.cliente.get('/gestion/periodos-5b').status_code,200 if jefe else 403)
            self.assertEqual(self.cliente.get('/api/admin/5b/periodos').status_code,200 if jefe else 403)
            self.assertEqual(self.cliente.post('/api/admin/5b/periodos',json={'nombre':'Gestión compartida','ano':2028},headers=h).status_code,201 if jefe else 403)
            self.assertEqual(self.cliente.patch(url,json=cambio,headers=h).status_code,409 if jefe else 403)
            self.assertEqual(self.cliente.patch(url+'/configuracion',json={'fuentes':fuentes,'revision':2},headers=h).status_code,403)
            self.assertEqual(self.cliente.post(url+'/publicar',json={'revision':2},headers=h).status_code,403)
            self.assertEqual(self.cliente.get('/api/evaluaciones/gestiones').status_code,200)

    def test_5b_periodos_anuales_borradores_y_permisos(self):
        self._login();h={'X-CSRFToken':self._csrf_token()}
        for datos in ({'nombre':'Año','ano':True},{'nombre':'Año','ano':0},{'nombre':'Año','ano':10000},{'nombre':'Año','ano':2026,'estado':'ACTIVO'}):
            self.assertEqual(self.cliente.post('/api/admin/5b/periodos',json=datos,headers=h).status_code,400)
        r=self.cliente.post('/api/admin/5b/periodos',json={'nombre':'Anual DEMO','ano':2026},headers=h);self.assertEqual(r.status_code,201)
        p=self.cliente.get('/api/admin/5b/periodos').json['periodos'][0]
        self.assertEqual((p['estado'],p['fecha_inicio'],p['fecha_fin']),('BORRADOR','2026-01-01','2026-12-31'))
        for estado,inicio,fin in [('ACTIVO','2027-01-01','2027-12-31'),('BORRADOR','2027-02-01','2027-12-31'),('BORRADOR','2027-01-01','2028-12-31')]:
            self.assertEqual(self.cliente.post('/api/admin/periodos',json={'nombre':'Inválido','fecha_inicio':inicio,'fecha_fin':fin,'estado':estado},headers=h).status_code,400)
        self.assertEqual(self.cliente.post('/api/admin/5b/periodos',json={'nombre':'Sin CSRF','ano':2027}).status_code,400)
        self._login('instructor.demo','Clave instructor 123!')
        self.assertEqual(self.cliente.get('/gestion/periodos-5b').status_code,200)
        self.assertEqual(self.cliente.get('/api/admin/5b/periodos').status_code,200)
        self.assertEqual(self.cliente.post(f"/api/admin/5b/periodos/{p['id']}/configuracion",json={'fuentes':{}},headers={'X-CSRFToken':self._csrf_token()}).status_code,403)

    def test_5b_configuracion_completa_revision_congelacion_y_vinculo(self):
        from sicose.db import obtener_conexion
        self._login();h={'X-CSRFToken':self._csrf_token()}
        pid=self.cliente.post('/api/admin/5b/periodos',json={'nombre':'Config DEMO','ano':2026},headers=h).json['id']
        ruta=f'/api/admin/5b/periodos/{pid}'
        conf,fuentes=self._configurar_periodo_5b(pid);h={'X-CSRFToken':self._csrf_token()}
        r=self.cliente.patch(ruta+'/configuracion',json={'fuentes':{'FISICA_1':fuentes['FISICA_1']},'revision':1},headers=h);self.assertEqual(r.status_code,200);self.assertEqual(r.json['configuracion']['revision'],2)
        self.assertEqual(self.cliente.patch(ruta+'/configuracion',json={'fuentes':fuentes,'revision':1},headers=h).status_code,409)
        self.assertEqual(self.cliente.post(ruta+'/publicar',json={'revision':2},headers=h).status_code,400)
        with self.app.app_context():
            c=obtener_conexion();self.assertEqual(c.execute('SELECT estado FROM periodos WHERE id=?',(pid,)).fetchone()[0],'BORRADOR')
        self.assertEqual(self.cliente.patch(ruta+'/configuracion',json={'fuentes':{'ACADEMICA':fuentes['FISICA_1']},'revision':2},headers=h).status_code,400)
        self.assertEqual(self.cliente.patch(ruta+'/configuracion',json={'fuentes':fuentes,'revision':2},headers=h).status_code,200)
        self.assertEqual(self.cliente.post(ruta+'/publicar',json={'revision':3},headers=h).status_code,200)
        publicado=self.cliente.get('/api/admin/5b/periodos').json['periodos'][0]['configuracion'];original=next(f['nombre'] for f in publicado['fuentes'] if f['fuente']=='FISICA_1')
        self.assertEqual(self.cliente.patch(ruta+'/configuracion',json={'fuentes':fuentes,'revision':3},headers=h).status_code,409)
        self.assertEqual(self.cliente.post(ruta+'/publicar',json={'revision':3},headers=h).status_code,409)
        self.assertEqual(self.cliente.patch(f"/api/admin/evaluaciones/{fuentes['FISICA_1']}",json={'nombre':'Nombre cambiado','activo':False},headers=h).status_code,200)
        self.assertEqual(next(f['nombre'] for f in self.cliente.get('/api/admin/5b/periodos').json['periodos'][0]['configuracion']['fuentes'] if f['fuente']=='FISICA_1'),original)
        with self.app.app_context():
            c=obtener_conexion();c.execute('INSERT INTO instructores(usuario_id) VALUES (2)');c.execute('INSERT INTO voluntarios(usuario_id,instructor_id) VALUES (3,2)');c.commit()
            for sql,args in [("UPDATE configuraciones_5b SET estado='BORRADOR' WHERE id=?",(conf['id'],)),('DELETE FROM fuentes_configuracion_5b WHERE configuracion_id=?',(conf['id'],)),("UPDATE periodos SET fecha_fin='2026-12-30' WHERE id=?",(pid,))]:
                with self.assertRaises(sqlite3.IntegrityError):c.execute(sql,args)
                c.rollback()
        self._login('instructor.demo','Clave instructor 123!')
        self.assertEqual(self.cliente.patch('/api/evaluaciones/personas/3/habilitacion',json={'periodo_id':pid,'clave':'FISICA_1','habilitada':True},headers={'X-CSRFToken':self._csrf_token()}).status_code,200)
        r=self.cliente.post('/api/5b/personas/3/notas',json={'periodo_id':pid,'fuente':'FISICA_1','nota_0_100':'80.01'},headers={'X-CSRFToken':self._csrf_token()});self.assertEqual(r.status_code,201,r.json)
        nota=self.cliente.get(f'/api/5b/personas/3?periodo_id={pid}').json['notas'][0]
        self.assertEqual((nota['configuracion_id'],nota['evaluacion_id']),(conf['id'],fuentes['FISICA_1']))

    def test_5b_publicacion_concurrente_activo_unico(self):
        import threading
        from concurrent.futures import ThreadPoolExecutor
        self._login();pares=[]
        for ano in (2026,2027):
            pid=self.cliente.post('/api/admin/5b/periodos',json={'nombre':f'Gestión {ano}','ano':ano},headers={'X-CSRFToken':self._csrf_token()}).json['id']
            conf,_=self._configurar_periodo_5b(pid);cli=self.app.test_client();tok=re.search(rb'name="csrf_token" value="([^"]+)"',cli.get('/login').data).group(1).decode()
            self.assertEqual(cli.post('/api/auth/login',json={'username':'admin.demo','password':'Clave demo segura 123!'},headers={'X-CSRFToken':tok}).status_code,200)
            tok=re.search(rb'name="csrf_token" value="([^"]+)"',cli.get('/',follow_redirects=True).data).group(1).decode();pares.append((cli,tok,pid,conf['revision']))
        barrier=threading.Barrier(2)
        def activar(par):
            cli,tok,pid,rev=par;barrier.wait(timeout=5)
            return cli.post(f'/api/admin/5b/periodos/{pid}/publicar',json={'revision':rev},headers={'X-CSRFToken':tok}).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:estados=list(pool.map(activar,pares))
        self.assertEqual(sorted(estados),[200,409])
        periodos=self.cliente.get('/api/admin/5b/periodos').json['periodos']
        self.assertEqual(sum(p['estado']=='ACTIVO' for p in periodos),1)
        self.assertEqual(sum(p['configuracion']['estado']=='PUBLICADA' for p in periodos),1)

    def test_5b_migracion_v15_conserva_activos_y_notas_sin_adopcion(self):
        from contextlib import closing
        from sicose.db import obtener_conexion
        ruta=Path('.tmp')/f'v15-{uuid.uuid4().hex}.sqlite3'
        try:
            esquema=Path('sicose/schema.sql').read_text(encoding='utf-8').split('CREATE TABLE IF NOT EXISTS configuraciones_5b')[0]
            esquema=chr(10).join(linea for linea in esquema.splitlines() if "configuracion_id INTEGER REFERENCES" not in linea and "evaluacion_id INTEGER REFERENCES evaluaciones(id) ON DELETE RESTRICT," not in linea)
            with closing(sqlite3.connect(ruta)) as c:
                c.executescript(esquema);c.execute("INSERT INTO roles(id,nombre) VALUES (1,'JEFE_PERSONAL'),(2,'INSTRUCTOR_VOLUNTARIO')")
                c.execute("INSERT INTO usuarios(id,username,nombre_completo,password_hash,rol_id) VALUES (1,'jefe.demo','Jefe DEMO','hash-sintetico',1),(2,'persona.demo','Persona DEMO','hash-sintetico',2)")
                c.execute('INSERT INTO instructores(usuario_id) VALUES (1)')
                c.execute('INSERT INTO voluntarios(usuario_id,instructor_id) VALUES (2,1)')
                c.execute("INSERT INTO periodos(id,nombre,fecha_inicio,fecha_fin,estado) VALUES (1,'Histórico A','2025-02-01','2025-12-01','ACTIVO'),(2,'Histórico B','2026-01-01','2026-12-31','ACTIVO')")
                c.execute("INSERT INTO notas_operativas(voluntario_id,periodo_id,fuente,puntos_centesimas,evaluador_id,registrada_por,evaluador_nombre,registrada_por_nombre) VALUES (2,1,'FISICA_1',7501,1,1,'Jefe DEMO','Jefe DEMO')");c.commit()
            app=create_app({'TESTING':True,'SECRET_KEY':'prueba-sintetica','DATABASE':str(ruta.resolve())})
            with app.app_context():
                inicializar_base_datos();inicializar_base_datos();c=obtener_conexion()
                self.assertEqual(c.execute("SELECT COUNT(*) FROM periodos WHERE estado='ACTIVO'").fetchone()[0],2)
                fila=c.execute('SELECT puntos_centesimas,configuracion_id,evaluacion_id FROM notas_operativas').fetchone();self.assertEqual(tuple(fila),(7501,None,None))
                self.assertEqual(c.execute('SELECT COUNT(*) FROM configuraciones_5b').fetchone()[0],0)
                with self.assertRaises(sqlite3.IntegrityError):c.execute("INSERT INTO periodos(nombre,fecha_inicio,fecha_fin,estado) VALUES ('Tercero','2027-01-01','2027-12-31','ACTIVO')")
                c.rollback();self.assertEqual(c.execute('PRAGMA quick_check').fetchone()[0],'ok');self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(),[])
        finally:
            if ruta.exists():ruta.unlink()

    def test_login_correcto(self):
        respuesta = self._login()
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json["usuario"]["rol"], "ADMINISTRADOR")
        cookie = respuesta.headers.get("Set-Cookie", "")
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Lax", cookie)

    def test_dashboard_muestra_ano_calendario_sin_periodo_activo(self):
        self.assertEqual(self._login().status_code, 200)
        for ruta in ("/panel/administrador", "/gestion/instructores-voluntarios",
                     "/gestion/jefes-personal", "/configuracion", "/gestion/evaluaciones",
                     "/gestion/asistencias", "/gestion/capacitaciones", "/gestion/calificaciones"):
            with self.subTest(ruta=ruta):
                respuesta = self.cliente.get(ruta)
                self.assertEqual(respuesta.status_code, 200)
                self.assertIn(str(date.today().year).encode(), respuesta.data)
                self.assertNotIn(b"Sin per\xc3\xadodo activo", respuesta.data)
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            self.assertEqual(conexion.execute("SELECT COUNT(*) FROM periodos").fetchone()[0], 0)

    def test_login_con_contrasena_incorrecta(self):
        respuesta = self._login(password="incorrecta")
        self.assertEqual(respuesta.status_code, 401)
        self.assertEqual(respuesta.json["error"], "Usuario o contraseña incorrectos.")

    def test_login_con_usuario_inexistente(self):
        respuesta = self._login(username="nadie.demo")
        self.assertEqual(respuesta.status_code, 401)
        self.assertEqual(respuesta.json["error"], "Usuario o contraseña incorrectos.")

    def test_usuario_inactivo_no_inicia_sesion(self):
        with self.app.app_context():
            from sicose.db import obtener_conexion

            self._crear_usuario("pendiente.demo", "INSTRUCTOR_VOLUNTARIO", "Clave pendiente 123!")
            obtener_conexion().execute(
                "UPDATE usuarios SET estado = 'PENDIENTE' WHERE username = ?",
                ("pendiente.demo",),
            )
            obtener_conexion().commit()
        respuesta = self._login("pendiente.demo", "Clave pendiente 123!")
        self.assertEqual(respuesta.status_code, 401)

    def test_api_protegida_rechaza_sin_sesion(self):
        respuesta = self.cliente.get("/api/admin/estado")
        self.assertEqual(respuesta.status_code, 401)

    def test_ruta_api_inexistente_devuelve_json_y_no_html(self):
        respuesta = self.cliente.get("/api/ruta-que-no-existe")
        self.assertEqual(respuesta.status_code, 404)
        self.assertEqual(respuesta.mimetype, "application/json")
        self.assertEqual(respuesta.json["codigo"], "no_encontrado")

    def test_admin_puede_acceder_a_ruta_restringida(self):
        self.assertEqual(self._login().status_code, 200)
        respuesta = self.cliente.get("/api/admin/estado")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json, {"estado": "autorizado"})

    def test_instructor_no_accede_a_ruta_admin(self):
        self.assertEqual(self._login("instructor.demo", "Clave instructor 123!").status_code, 200)
        self.assertEqual(self.cliente.get("/api/admin/estado").status_code, 403)

    def test_voluntario_no_accede_a_ruta_admin(self):
        self.assertEqual(self._login("voluntario.demo", "Clave voluntario 123!").status_code, 200)
        self.assertEqual(self.cliente.get("/api/admin/estado").status_code, 403)

    def test_inicio_admin_muestra_dashboard_y_metricas(self):
        self.assertEqual(self._login().status_code, 200)
        respuesta = self.cliente.get("/", follow_redirects=True)
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(b"Panel de administraci\xc3\xb3n", respuesta.data)
        self.assertIn(b"Voluntarios activos", respuesta.data)
        self.assertIn(b'id="boton-tema"', respuesta.data)
        self.assertIn(b'id="boton-sidebar"', respuesta.data)
        self.assertIn(b"images/sbrab-logo.png", respuesta.data)
        self.assertIn(b"Agregar Jefe de Personal", respuesta.data)
        self.assertIn(b"Ver todos los Jefes de Personal", respuesta.data)
        self.assertIn(b"Capacitaciones y Cursos", respuesta.data)
        self.assertIn(b"SICOSE", respuesta.data)

    def test_logo_institucional_esta_disponible_como_imagen(self):
        respuesta = self.cliente.get("/static/images/sbrab-logo.png")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.mimetype, "image/png")
        respuesta.close()

    def test_login_muestra_emblema_y_estilos_institucionales(self):
        respuesta = self.cliente.get("/login")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(b"images/sbrab-logo.png", respuesta.data)
        self.assertIn(b"Emblema institucional SBRAB", respuesta.data)
        css = self.cliente.get("/static/css/estilos.css")
        self.assertEqual(css.status_code, 200)
        self.assertIn(b"#1E1BBB", css.data)
        self.assertIn(b"#F2AB7E", css.data)
        css.close()

    def test_inicio_instructor_muestra_solo_su_panel(self):
        self.assertEqual(self._login("instructor.demo", "Clave instructor 123!").status_code, 200)
        respuesta = self.cliente.get("/", follow_redirects=True)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(self.cliente.get("/panel/jefe-personal").status_code, 200)
        self.assertIn(b"Panel del Jefe de Personal", respuesta.data)
        self.assertIn(b"Resumen SBRAB", respuesta.data)
        self.assertNotIn(b"Panel de administraci\xc3\xb3n", respuesta.data)

    def test_inicio_voluntario_muestra_solo_su_panel(self):
        self.assertEqual(self._login("voluntario.demo", "Clave voluntario 123!").status_code, 200)
        respuesta = self.cliente.get("/", follow_redirects=True)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(self.cliente.get("/panel/instructor-voluntario").status_code, 200)
        self.assertIn(b"Mi seguimiento", respuesta.data)
        self.assertEqual(respuesta.data.count(b'class="tarjeta-indicador"'), 4)
        self.assertNotIn(b"Panel del Jefe de Personal", respuesta.data)

    def test_ruta_panel_de_otro_rol_retorna_403(self):
        self.assertEqual(self._login("voluntario.demo", "Clave voluntario 123!").status_code, 200)
        respuesta = self.cliente.get("/panel/administrador")
        self.assertEqual(respuesta.status_code, 403)
        self.assertIn(b"Acceso no disponible", respuesta.data)

    def test_logout_y_rechazo_posterior(self):
        self.assertEqual(self._login().status_code, 200)
        respuesta = self.cliente.post(
            "/api/auth/logout", headers={"X-CSRFToken": self._csrf_token()}
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(self.cliente.get("/api/auth/me").status_code, 401)

    def test_me_solo_devuelve_campos_publicos(self):
        self.assertEqual(self._login().status_code, 200)
        usuario = self.cliente.get("/api/auth/me").json["usuario"]
        self.assertEqual(set(usuario), {"id", "username", "nombre", "rol", "estado"})
        self.assertNotIn("password", usuario)
        self.assertNotIn("password_hash", usuario)

    def test_password_se_guarda_solo_como_hash(self):
        with self.app.app_context():
            from sicose.db import obtener_conexion

            fila = obtener_conexion().execute(
                "SELECT password_hash FROM usuarios WHERE username = ?", ("admin.demo",)
            ).fetchone()
            self.assertNotEqual(fila["password_hash"], "Clave demo segura 123!")
            self.assertTrue(check_password_hash(fila["password_hash"], "Clave demo segura 123!"))

    def test_seed_admin_es_idempotente_y_no_cambia_clave(self):
        with self.app.app_context():
            from sicose.db import obtener_conexion

            self.assertTrue(seed_admin("otro.admin.demo", "Primera clave segura 123!"))
            antes = obtener_conexion().execute(
                "SELECT password_hash FROM usuarios WHERE username = ?", ("otro.admin.demo",)
            ).fetchone()[0]
            self.assertFalse(seed_admin("otro.admin.demo", "Otra clave segura 456!"))
            despues = obtener_conexion().execute(
                "SELECT password_hash FROM usuarios WHERE username = ?", ("otro.admin.demo",)
            ).fetchone()[0]
            self.assertEqual(antes, despues)
            cantidad_eventos = obtener_conexion().execute(
                "SELECT COUNT(*) FROM auditoria WHERE accion = 'ADMIN_SEED'"
            ).fetchone()[0]
            self.assertEqual(cantidad_eventos, 1)

    def test_esquema_incluye_entidades_base_y_versiona_sin_borrar(self):
        with self.app.app_context():
            from sicose.db import obtener_conexion

            conexion = obtener_conexion()
            tablas = {
                fila[0]
                for fila in conexion.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
            self.assertTrue(
                {
                    "roles", "usuarios", "voluntarios", "instructores", "periodos",
                    "evaluaciones", "intentos", "respuestas", "calificaciones",
                    "capacitaciones", "asistencias", "auditoria",
                }.issubset(tablas)
            )
            columnas_voluntarios = {fila["name"] for fila in conexion.execute("PRAGMA table_info(voluntarios)")}
            self.assertTrue({"nombres", "apellido_paterno", "apellido_materno", "fecha_nacimiento", "codigo_instructor"}.issubset(columnas_voluntarios))
            version = conexion.execute(
                "SELECT valor FROM app_meta WHERE clave = ?", ("schema_version",)
            ).fetchone()[0]
            self.assertEqual(version, "33")
            columnas_asistencias = {fila["name"] for fila in conexion.execute("PRAGMA table_info(asistencias)")}
            self.assertIn("estado_detalle", columnas_asistencias)
            self.assertEqual(
                conexion.execute("SELECT COUNT(*) FROM roles").fetchone()[0], 4
            )
            self.assertEqual(conexion.execute("PRAGMA foreign_keys").fetchone()[0], 1)
            with self.assertRaises(sqlite3.IntegrityError):
                conexion.execute(
                    """INSERT INTO usuarios (username, nombre_completo, password_hash, rol_id)
                       VALUES (?, ?, ?, ?)""",
                    ("sin.rol", "Sin rol", "hash-no-usado", 9999),
                )

    def test_migracion_renombra_roles_sin_perder_perfiles_ni_evaluaciones(self):
        legacy_path = Path(".tmp") / f"legacy-{uuid.uuid4().hex}.sqlite3"
        old_schema = (Path("sicose") / "schema.sql").read_text(encoding="utf-8")
        old_schema = old_schema.replace(
            "('ADMINISTRADOR', 'JEFE_PERSONAL', 'INSTRUCTOR_VOLUNTARIO', 'COMANDANTE_GRUPO')",
            "('ADMINISTRADOR', 'INSTRUCTOR', 'VOLUNTARIO')",
        ).replace(
            "('PSICOMETRICA', 'FISICA', 'ACADEMICA', 'JEFE_PERSONAL')",
            "('PSICOMETRICA', 'FISICA', 'ACADEMICA', 'INSTRUCTOR')",
        ).replace(
            "('INSTRUCTOR_VOLUNTARIO', 'JEFE_PERSONAL')",
            "('VOLUNTARIO', 'INSTRUCTOR')",
        ).replace(
            "    nombres TEXT,\n    apellido_paterno TEXT,\n    apellido_materno TEXT,\n    fecha_nacimiento TEXT,\n    codigo_instructor TEXT UNIQUE,\n", ""
        ).replace(
            "    estado_detalle TEXT CHECK (estado_detalle IS NULL OR estado_detalle IN ('ASISTE', 'ATRASO', 'PERMISO', 'FALTA')),\n", ""
        )
        legacy = sqlite3.connect(legacy_path)
        legacy.execute("PRAGMA foreign_keys=ON")
        legacy.executescript(old_schema)
        legacy.execute("INSERT INTO app_meta (clave, valor) VALUES ('schema_version', '5')")
        legacy.executemany("INSERT INTO roles(nombre) VALUES (?)", [("ADMINISTRADOR",), ("INSTRUCTOR",), ("VOLUNTARIO",)])
        roles = {name: role_id for role_id, name in legacy.execute("SELECT id,nombre FROM roles")}
        legacy.execute("INSERT INTO usuarios(username,nombre_completo,password_hash,rol_id) VALUES ('jefe.demo','Jefe demo','hash',?)", (roles["INSTRUCTOR"],))
        jefe_id = legacy.execute("SELECT id FROM usuarios WHERE username='jefe.demo'").fetchone()[0]
        legacy.execute("INSERT INTO instructores(usuario_id) VALUES (?)", (jefe_id,))
        legacy.execute("INSERT INTO usuarios(username,nombre_completo,password_hash,rol_id) VALUES ('iv.demo','IV demo','hash',?)", (roles["VOLUNTARIO"],))
        iv_id = legacy.execute("SELECT id FROM usuarios WHERE username='iv.demo'").fetchone()[0]
        legacy.execute("INSERT INTO voluntarios(usuario_id,instructor_id) VALUES (?,?)", (iv_id, jefe_id))
        legacy.execute("INSERT INTO asistencias(voluntario_id,fecha,estado,actividad,registrado_por) VALUES (?, '2026-09-01', 'PRESENTE', 'Histórica', ?)", (iv_id, jefe_id))
        period_id = legacy.execute("INSERT INTO periodos(nombre,fecha_inicio,fecha_fin) VALUES ('Migración','2026-01-01','2026-12-31')").lastrowid
        eval_id = legacy.execute("INSERT INTO evaluaciones(codigo,nombre,categoria,origen_nota) VALUES ('JEF-OLD','Registro previo','INSTRUCTOR','INSTRUCTOR')").lastrowid
        legacy.execute("INSERT INTO asignaciones_evaluacion(voluntario_id,periodo_id,evaluacion_id) VALUES (?,?,?)", (iv_id, period_id, eval_id))
        legacy.commit()
        legacy.close()

        legacy_app = create_app({
            "TESTING": True,
            "SECRET_KEY": "clave-de-prueba-migracion",
            "DATABASE": str(legacy_path.resolve()),
            "PERFIL_MEDIA_FOLDER": str(self.media_path.resolve()),
        })
        try:
            with legacy_app.app_context():
                inicializar_base_datos()
                from sicose.db import obtener_conexion
                conexion = obtener_conexion()
                migrated_roles = {fila["nombre"]: fila["id"] for fila in conexion.execute("SELECT id,nombre FROM roles")}
                self.assertEqual(migrated_roles["JEFE_PERSONAL"], roles["INSTRUCTOR"])
                self.assertEqual(migrated_roles["INSTRUCTOR_VOLUNTARIO"], roles["VOLUNTARIO"])
                self.assertEqual(conexion.execute("SELECT instructor_id FROM voluntarios WHERE usuario_id=?", (iv_id,)).fetchone()[0], jefe_id)
                self.assertEqual(tuple(conexion.execute("SELECT categoria,origen_nota FROM evaluaciones WHERE id=?", (eval_id,)).fetchone()), ("JEFE_PERSONAL", "JEFE_PERSONAL"))
                self.assertEqual(conexion.execute("SELECT COUNT(*) FROM asignaciones_evaluacion WHERE voluntario_id=? AND evaluacion_id=?", (iv_id, eval_id)).fetchone()[0], 1)
                self.assertIsNone(conexion.execute("SELECT fecha_nacimiento FROM voluntarios WHERE usuario_id=?", (iv_id,)).fetchone()[0])
                asistencia_migrada = conexion.execute("SELECT estado,estado_detalle FROM asistencias WHERE voluntario_id=?", (iv_id,)).fetchone()
                self.assertEqual(tuple(asistencia_migrada), ("PRESENTE", "ASISTE"))
                self.assertEqual(conexion.execute("SELECT valor FROM app_meta WHERE clave='schema_version'").fetchone()[0], "33")
                self.assertEqual(conexion.execute("PRAGMA foreign_key_check").fetchall(), [])
        finally:
            if legacy_path.exists():
                legacy_path.unlink()

    def test_solicitud_publica_crea_usuario_pendiente_sin_sesion(self):
        respuesta = self._post_alta("/api/registro/solicitudes", json={
            "username": "nueva.demo", "nombres": "Nueva", "apellido_paterno": "Voluntaria", "apellido_materno": "Demo",
            "fecha_nacimiento": "1978-04-02",
            "especialidad_principal": "Rescate en montaña",
            "correo": "nueva@example.org", "password": "Contraseña segura 123!",
        }, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.json["codigo_instructor"], "NVD-020478")
        self.assertEqual(self.cliente.get("/api/auth/me").status_code, 401)
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            usuario = conexion.execute("SELECT estado, password_hash FROM usuarios WHERE username='nueva.demo'").fetchone()
            self.assertEqual(usuario["estado"], "PENDIENTE")
            self.assertNotEqual(usuario["password_hash"], "Contraseña segura 123!")
            self.assertEqual(conexion.execute("SELECT COUNT(*) FROM solicitudes_registro").fetchone()[0], 1)
            perfil = conexion.execute("SELECT fecha_nacimiento, codigo_instructor FROM voluntarios JOIN usuarios ON usuarios.id=voluntarios.usuario_id WHERE username='nueva.demo'").fetchone()
            self.assertEqual(tuple(perfil), ("1978-04-02", "NVD-020478"))

    def _png_prueba(self):
        def chunk(tipo, contenido):
            crc = zlib.crc32(tipo + contenido) & 0xffffffff
            return struct.pack(">I", len(contenido)) + tipo + contenido + struct.pack(">I", crc)
        return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00")) + chunk(b"IEND", b""))

    def test_registro_guarda_foto_en_instancia_y_la_sirve_solo_con_autorizacion(self):
        import io
        self.assertEqual(self._post_alta("/api/registro/solicitudes", data={
            "username": "foto.demo", "nombres": "Voluntaria", "apellido_paterno": "Foto", "apellido_materno": "Demo",
            "fecha_nacimiento": "1980-02-03", "especialidad_principal": "K-9", "password": "Contraseña segura 123!",
            "foto": (io.BytesIO(self._png_prueba()), "perfil.png"),
        }, headers={"X-CSRFToken": self._csrf_token()}, content_type="multipart/form-data").status_code, 201)
        archivos_confirmados = set(self.media_path.iterdir())
        colision = self._post_alta("/api/registro/solicitudes", data={
            "username": "foto.colision", "nombres": "Voluntaria", "apellido_paterno": "Foto", "apellido_materno": "Demo",
            "fecha_nacimiento": "1980-02-03", "especialidad_principal": "K-9", "password": "Contraseña segura 123!",
            "foto": (io.BytesIO(self._png_prueba()), "colision.png"),
        }, headers={"X-CSRFToken": self._csrf_token()}, content_type="multipart/form-data")
        self.assertEqual(colision.status_code, 409)
        self.assertEqual(set(self.media_path.iterdir()), archivos_confirmados)
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            usuario_id, nombre_archivo = conexion.execute("SELECT id, foto_perfil FROM usuarios WHERE username='foto.demo'").fetchone()
            archivo = Path(self.app.config["PERFIL_MEDIA_FOLDER"]) / nombre_archivo
            self.assertTrue(archivo.is_file())
        # El administrador puede revisar la imagen de un perfil pendiente.
        self.assertEqual(self._login().status_code, 200)
        imagen = self.cliente.get(f"/api/usuarios/{usuario_id}/foto")
        self.assertEqual(imagen.status_code, 200)
        self.assertEqual(imagen.mimetype, "image/png")
        self.assertEqual(imagen.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(imagen.headers["Cache-Control"], "private, no-store")
        imagen.close()

    def test_admin_restablece_clave_e_invalida_sesion_anterior(self):
        admin = self.app.test_client()
        volunteer = self.app.test_client()
        def login(client, username, password):
            pagina = client.get("/registro")
            csrf = re.search(rb'name="csrf_token" value="([^"]+)"', pagina.data).group(1).decode()
            return client.post("/api/auth/login", json={"username": username, "password": password}, headers={"X-CSRFToken": csrf})
        self.assertEqual(login(volunteer, "voluntario.demo", "Clave voluntario 123!").status_code, 200)
        self.assertEqual(login(admin, "admin.demo", "Clave demo segura 123!").status_code, 200)
        with self.app.app_context():
            from sicose.db import obtener_conexion
            user_id = obtener_conexion().execute("SELECT id FROM usuarios WHERE username='voluntario.demo'").fetchone()[0]
        csrf = re.search(rb'name="csrf_token" value="([^"]+)"', admin.get("/gestion/instructores-voluntarios").data).group(1).decode()
        response = admin.post(f"/api/admin/usuarios/{user_id}/restablecer-clave", json={"password": "Nueva clave segura 456!"}, headers={"X-CSRFToken": csrf})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(volunteer.get("/api/auth/me").status_code, 401)
        self.assertEqual(login(volunteer, "voluntario.demo", "Nueva clave segura 456!").status_code, 200)

    def test_paginas_registro_y_gestion_cargan(self):
        registro = self.cliente.get("/registro")
        self.assertEqual(registro.status_code, 200)
        self.assertIn(b"Solicitud de registro", registro.data)
        self.assertEqual(self._login().status_code, 200)
        gestion = self.cliente.get("/gestion/instructores-voluntarios")
        self.assertEqual(gestion.status_code, 200)
        self.assertIn(b"Solicitudes pendientes", gestion.data)
        self.assertIn(b"Agregar Instructor Voluntario", gestion.data)
        self.assertIn(b"Todos los Instructores Voluntarios", gestion.data)
        self.assertNotIn(b'id="invitacion-form"', gestion.data)
        self.assertIn(b'<details id="agregar-instructor-voluntario"', gestion.data)
        self.assertIn(b'<tbody id="voluntarios-lista"', gestion.data)
        self.assertIn(b"Acciones", gestion.data)
        instructores = self.cliente.get("/gestion/jefes-personal")
        self.assertEqual(instructores.status_code, 200)
        self.assertIn(b"Agregar Jefe de Personal", instructores.data)
        self.assertIn(b'<details id="agregar-jefe-personal"', instructores.data)
        self.assertIn(b'<tbody id="instructores-lista"', instructores.data)
        self.assertIn(b"Acciones CRUD", instructores.data)
        self.assertEqual(self.cliente.get("/api/admin/jefes-personal").mimetype, "application/json")

    def test_admin_crea_instructor_y_cuenta_accede_a_panel_diferenciado(self):
        self.assertEqual(self._login().status_code, 200)
        with self.app.app_context():
            from sicose.db import obtener_conexion
            c=obtener_conexion();c.execute("UPDATE usuarios SET estado='INACTIVO' WHERE id=2");c.commit()
        creada = self.cliente.post("/api/admin/jefes-personal", json={
            "username": "instructor.nuevo", "nombre": "Instructor Nuevo",
            "correo": "nuevo@example.org", "especialidad": "Rescate",
            "password": "Contraseña inicial 123!",
        }, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(creada.status_code, 201)
        instructor_id = creada.json["id"]
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            self.assertEqual(conexion.execute("SELECT estado FROM usuarios WHERE id=?", (instructor_id,)).fetchone()[0], "ACTIVO")
            self.assertEqual(conexion.execute("SELECT especialidad FROM instructores WHERE usuario_id=?", (instructor_id,)).fetchone()[0], "Rescate")
            password_hash = conexion.execute("SELECT password_hash FROM usuarios WHERE id=?", (instructor_id,)).fetchone()[0]
            self.assertNotEqual(password_hash, "Contraseña inicial 123!")
        self.cliente.post("/api/auth/logout", headers={"X-CSRFToken": self._csrf_token()})
        ingreso = self._login("instructor.nuevo", "Contraseña inicial 123!")
        self.assertEqual(ingreso.status_code, 200)
        inicio = self.cliente.get("/", follow_redirects=True)
        self.assertIn(b"Panel del Jefe de Personal", inicio.data)
        self.assertNotIn(b"Panel de administraci", inicio.data)
        rechazo = self.cliente.post("/api/admin/jefes-personal", json={}, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(rechazo.status_code, 403)

    def test_admin_crea_instructor_voluntario_manualmente_con_foto(self):
        import io

        self.assertEqual(self._login().status_code, 200)
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            jefe_id = conexion.execute("SELECT id FROM usuarios WHERE username='instructor.demo'").fetchone()[0]
            conexion.execute("INSERT INTO instructores (usuario_id, especialidad) VALUES (?, 'Rescate')", (jefe_id,))
            conexion.commit()

        creada = self._post_alta("/api/admin/instructores-voluntarios", data={
            "username": "iv.manual",
            "nombres": "Instructor Voluntario", "apellido_paterno": "Manual", "apellido_materno": "Demo",
            "fecha_nacimiento": "1980-02-03",
            "especialidad_principal": "Rescate en agua",
            "correo": "iv.manual@example.org",
            "password": "Clave inicial manual 123!",
            "experiencia_operaciones": "Rescate urbano",
            "antiguedad_desde": "2024-01-15",
            "instructor_id": str(jefe_id),
            "foto": (io.BytesIO(self._png_prueba()), "perfil.png"),
        }, headers={"X-CSRFToken": self._csrf_token()}, content_type="multipart/form-data")
        self.assertEqual(creada.status_code, 201)
        user_id = creada.json["id"]
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            cuenta = conexion.execute(
                "SELECT u.estado, r.nombre AS rol, u.password_hash FROM usuarios u JOIN roles r ON r.id=u.rol_id WHERE u.id=?",
                (user_id,),
            ).fetchone()
            perfil = conexion.execute(
                "SELECT instructor_id, experiencia_operaciones, antiguedad_desde, fecha_nacimiento, codigo_instructor, especialidad_principal FROM voluntarios WHERE usuario_id=?",
                (user_id,),
            ).fetchone()
            solicitudes = conexion.execute(
                "SELECT COUNT(*) FROM solicitudes_registro WHERE usuario_id=?", (user_id,)
            ).fetchone()[0]
        self.assertEqual(cuenta["estado"], "ACTIVO")
        self.assertEqual(cuenta["rol"], "INSTRUCTOR_VOLUNTARIO")
        self.assertNotEqual(cuenta["password_hash"], "Clave inicial manual 123!")
        self.assertEqual(perfil["instructor_id"], jefe_id)
        self.assertEqual(perfil["experiencia_operaciones"], "Rescate urbano")
        self.assertEqual(perfil["antiguedad_desde"], "2024-01-15")
        self.assertEqual(perfil["fecha_nacimiento"], "1980-02-03")
        self.assertEqual(perfil["codigo_instructor"], "IMD-030280")
        self.assertEqual(perfil["especialidad_principal"], "Rescate en agua")
        self.assertEqual(solicitudes, 0)
        self.assertTrue(any(item["id"] == user_id for item in self.cliente.get("/api/instructores-voluntarios").json["voluntarios"]))
        cambio_especialidad = self.cliente.patch(
            f"/api/instructores-voluntarios/{user_id}",
            json={"especialidad_principal": "K-9"},
            headers={"X-CSRFToken": self._csrf_token()},
        )
        self.assertEqual(cambio_especialidad.status_code, 200)
        especialidad_invalida = self.cliente.patch(
            f"/api/instructores-voluntarios/{user_id}",
            json={"especialidad_principal": "Otra"},
            headers={"X-CSRFToken": self._csrf_token()},
        )
        self.assertEqual(especialidad_invalida.status_code, 400)
        foto = self.cliente.get(f"/api/usuarios/{user_id}/foto")
        self.assertEqual(foto.status_code, 200)
        self.assertEqual(foto.mimetype, "image/png")
        foto.close()
        self.cliente.post("/api/auth/logout", headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(self._login("instructor.demo", "Clave instructor 123!").status_code, 200)
        denegada = self._post_alta("/api/admin/instructores-voluntarios", json={}, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(denegada.status_code, 403)

    def test_admin_registra_instructor_con_foto(self):
        import io
        self.assertEqual(self._login().status_code, 200)
        with self.app.app_context():
            from sicose.db import obtener_conexion
            c=obtener_conexion();c.execute("UPDATE usuarios SET estado='INACTIVO' WHERE id=2");c.commit()
        creada = self.cliente.post("/api/admin/jefes-personal", data={
            "username": "instructor.foto", "nombre": "Instructor con foto",
            "password": "Contraseña inicial 123!",
            "foto": (io.BytesIO(self._png_prueba()), "instructor.png"),
        }, headers={"X-CSRFToken": self._csrf_token()}, content_type="multipart/form-data")
        self.assertEqual(creada.status_code, 201)
        imagen = self.cliente.get(f"/api/usuarios/{creada.json['id']}/foto")
        self.assertEqual(imagen.status_code, 200)
        self.assertEqual(imagen.mimetype, "image/png")
        imagen.close()

    def test_admin_edita_y_desactiva_instructor_conservando_perfiles(self):
        self.assertEqual(self._login().status_code, 200)
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            instructor_id = conexion.execute("SELECT id FROM usuarios WHERE username='instructor.demo'").fetchone()[0]
            voluntario_id = conexion.execute("SELECT id FROM usuarios WHERE username='voluntario.demo'").fetchone()[0]
            conexion.execute("INSERT INTO instructores (usuario_id, especialidad) VALUES (?, 'Inicial')", (instructor_id,))
            conexion.execute("INSERT INTO voluntarios (usuario_id, instructor_id) VALUES (?, ?)", (voluntario_id, instructor_id))
            conexion.commit()
        editada = self.cliente.patch(f"/api/admin/jefes-personal/{instructor_id}", json={
            "nombre": "Instructor Editado", "especialidad": "Montaña",
        }, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(editada.status_code, 200)
        baja = self.cliente.post(f"/api/admin/jefes-personal/{instructor_id}/desactivar", headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(baja.status_code, 200)
        self.assertEqual(baja.json["voluntarios_desvinculados"], 1)
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            self.assertEqual(conexion.execute("SELECT estado FROM usuarios WHERE id=?", (instructor_id,)).fetchone()[0], "INACTIVO")
            self.assertIsNone(conexion.execute("SELECT instructor_id FROM voluntarios WHERE usuario_id=?", (voluntario_id,)).fetchone()[0])
            self.assertEqual(conexion.execute("SELECT COUNT(*) FROM instructores WHERE usuario_id=?", (instructor_id,)).fetchone()[0], 1)

    def test_admin_crea_periodo_catalogo_y_asignacion(self):
        self.assertEqual(self._login().status_code, 200)
        periodo = self.cliente.post("/api/admin/periodos", json={
            "nombre": "Ciclo demo", "fecha_inicio": "2026-01-01", "fecha_fin": "2026-12-31", "estado": "BORRADOR",
        }, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(periodo.status_code, 201)
        evaluacion = self.cliente.post("/api/admin/evaluaciones", json={
            "codigo": "FIS-DEMO", "nombre": "Evaluación física", "categoria": "FISICA", "origen_nota": "JEFE_PERSONAL",
        }, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(evaluacion.status_code, 201)
        activada = self.cliente.patch(f"/api/admin/evaluaciones/{evaluacion.json['id']}", json={"activo": True}, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(activada.status_code, 200)
        conf,_=self._configurar_periodo_5b(periodo.json['id'])
        self.assertEqual(self.cliente.post(f"/api/admin/5b/periodos/{periodo.json['id']}/publicar",json={'revision':conf['revision']},headers={'X-CSRFToken':self._csrf_token()}).status_code,200)
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            usuario_id = conexion.execute("SELECT id FROM usuarios WHERE username='voluntario.demo'").fetchone()[0]
            conexion.execute("INSERT INTO voluntarios(usuario_id) VALUES (?)", (usuario_id,))
            conexion.commit()
        asignacion = self.cliente.post("/api/admin/asignaciones", json={
            "voluntario_id": usuario_id, "periodo_id": periodo.json["id"], "evaluacion_id": evaluacion.json["id"],
        }, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(asignacion.status_code, 201)
        self.assertEqual(asignacion.json["estado"], "NO_HABILITADA")
        self.assertEqual(self.cliente.get("/gestion/evaluaciones").status_code, 200)

    def test_instructor_registra_asistencia_y_nota_con_historial(self):
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            instructor_id = conexion.execute("SELECT id FROM usuarios WHERE username='instructor.demo'").fetchone()[0]
            volunteer_id = conexion.execute("SELECT id FROM usuarios WHERE username='voluntario.demo'").fetchone()[0]
            conexion.execute("INSERT INTO instructores(usuario_id) VALUES (?)", (instructor_id,))
            conexion.execute("INSERT INTO voluntarios(usuario_id,instructor_id) VALUES (?,?)", (volunteer_id,instructor_id))
            period_id = conexion.execute("INSERT INTO periodos(nombre,fecha_inicio,fecha_fin,estado) VALUES ('Notas demo','2026-01-01','2026-12-31','ACTIVO')").lastrowid
            evaluation_id = conexion.execute("INSERT INTO evaluaciones(codigo,nombre,categoria,origen_nota,activo) VALUES ('FIS-01','Prueba física','FISICA','JEFE_PERSONAL',1)").lastrowid
            assignment_id = conexion.execute("INSERT INTO asignaciones_evaluacion(voluntario_id,periodo_id,evaluacion_id,estado) VALUES (?,?,?,'HABILITADA')", (volunteer_id,period_id,evaluation_id)).lastrowid
            conexion.commit()
        self.assertEqual(self._login("instructor.demo", "Clave instructor 123!").status_code, 200)
        headers = {"X-CSRFToken": self._csrf_token()}
        asistencia = self.cliente.post("/api/jefe-personal/asistencias", json={
            "fecha": "2026-09-28", "actividad": "Entrenamiento", "asistencias": [{"voluntario_id": volunteer_id, "estado": "PRESENTE"}],
        }, headers=headers)
        self.assertEqual(asistencia.status_code, 200)
        nota = self.cliente.post(f"/api/jefe-personal/asignaciones/{assignment_id}/calificaciones", json={"nota_0_100": 75, "observacion": "Registro inicial"}, headers=headers)
        self.assertEqual(nota.status_code, 201)
        correccion = self.cliente.post(f"/api/jefe-personal/asignaciones/{assignment_id}/calificaciones", json={"nota_0_100": 80, "corregida_de_id": nota.json["id"]}, headers=headers)
        self.assertEqual(correccion.status_code, 201)
        historial = self.cliente.get(f"/api/jefe-personal/asignaciones/{assignment_id}/calificaciones")
        self.assertEqual([item["nota_0_100"] for item in historial.json["historial"]], [75, 80])
        pagina_asistencias = self.cliente.get("/gestion/asistencias")
        self.assertEqual(pagina_asistencias.status_code, 200)
        self.assertIn(b"Fecha", pagina_asistencias.data)
        self.assertIn(b"Actividad", pagina_asistencias.data)
        self.assertIn(b"Cursos y Capacitaciones", pagina_asistencias.data)
        assets = self.cliente.get("/static/js/app.js")
        self.assertIn(b"ATRASO", assets.data)
        assets.close()
        self.assertEqual(self.cliente.get("/gestion/capacitaciones").status_code, 200)
        self.assertEqual(self.cliente.get("/gestion/calificaciones").status_code, 200)

    def test_pagina_asistencias_usa_esquema_en_tabla(self):
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            instructor_id = conexion.execute("SELECT id FROM usuarios WHERE username='instructor.demo'").fetchone()[0]
            volunteer_id = conexion.execute("SELECT id FROM usuarios WHERE username='voluntario.demo'").fetchone()[0]
            conexion.execute("INSERT INTO instructores(usuario_id) VALUES (?)", (instructor_id,))
            conexion.execute("INSERT INTO voluntarios(usuario_id,instructor_id) VALUES (?,?)", (volunteer_id,instructor_id))
            conexion.commit()
        self.assertEqual(self._login("instructor.demo", "Clave instructor 123!").status_code, 200)
        pagina = self.cliente.get("/gestion/asistencias")
        self.assertEqual(pagina.status_code, 200)
        for fragmento in (b"Nombre completo", b"C\xc3\xb3digo", b"Estado", b"Asistencia"):
            self.assertIn(fragmento, pagina.data)

    def test_asistencias_aceptan_cuatro_estados_y_filtran_por_persona_y_fechas(self):
        with self.app.app_context():
            from sicose.db import obtener_conexion
            connection = obtener_conexion()
            instructor_id = connection.execute("SELECT id FROM usuarios WHERE username='instructor.demo'").fetchone()[0]
            volunteer_id = connection.execute("SELECT id FROM usuarios WHERE username='voluntario.demo'").fetchone()[0]
            connection.execute("INSERT INTO instructores(usuario_id) VALUES (?)", (instructor_id,))
            connection.execute("INSERT INTO voluntarios(usuario_id,instructor_id) VALUES (?,?)", (volunteer_id,instructor_id))
            connection.commit()
        self.assertEqual(self._login("instructor.demo", "Clave instructor 123!").status_code, 200)
        headers = {"X-CSRFToken": self._csrf_token()}
        for index, state in enumerate(("ASISTE", "ATRASO", "PERMISO", "FALTA"), start=1):
            response = self.cliente.post("/api/jefe-personal/asistencias", json={
                "fecha": f"2026-09-0{index}", "actividad": "Entrenamiento",
                "asistencias": [{"voluntario_id": volunteer_id, "estado": state}],
            }, headers=headers)
            self.assertEqual(response.status_code, 200)
        history = self.cliente.get(f"/api/jefe-personal/asistencias?modo=rango&desde=2026-09-01&hasta=2026-09-04&voluntario_id={volunteer_id}")
        self.assertEqual([row["estado"] for row in history.json["asistencias"]], ["FALTA", "PERMISO", "ATRASO", "ASISTE"])
        self.assertEqual(self.cliente.get("/api/jefe-personal/asistencias?modo=rango&desde=2026-09-05&hasta=2026-09-01").status_code, 400)

    def test_capacitaciones_se_listan_y_se_editan_dentro_del_ambito(self):
        with self.app.app_context():
            from sicose.db import obtener_conexion
            connection = obtener_conexion()
            instructor_id = connection.execute("SELECT id FROM usuarios WHERE username='instructor.demo'").fetchone()[0]
            volunteer_id = connection.execute("SELECT id FROM usuarios WHERE username='voluntario.demo'").fetchone()[0]
            connection.execute("INSERT INTO instructores(usuario_id) VALUES (?)", (instructor_id,))
            connection.execute("INSERT INTO voluntarios(usuario_id,instructor_id) VALUES (?,?)", (volunteer_id,instructor_id))
            connection.commit()
        self.assertEqual(self._login("instructor.demo", "Clave instructor 123!").status_code, 200)
        headers = {"X-CSRFToken": self._csrf_token()}
        created = self.cliente.post(f"/api/jefe-personal/instructores-voluntarios/{volunteer_id}/capacitaciones", json={"nombre": "Primeros auxilios", "entidad": "SBRAB", "fecha": "2026-09-10"}, headers=headers)
        self.assertEqual(created.status_code, 201)
        listed = self.cliente.get("/api/jefe-personal/capacitaciones")
        self.assertEqual(listed.json["capacitaciones"][0]["nombre"], "Primeros auxilios")
        edited = self.cliente.patch(f"/api/jefe-personal/capacitaciones/{created.json['id']}", json={"nombre": "Primeros auxilios avanzados"}, headers=headers)
        self.assertEqual(edited.status_code, 200)
        self.assertEqual(self.cliente.get("/api/jefe-personal/capacitaciones").json["capacitaciones"][0]["nombre"], "Primeros auxilios avanzados")

    def test_evaluacion_psicometrica_pendiente_no_se_activa_ni_califica_manualmente(self):
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            instructor_id = conexion.execute("SELECT id FROM usuarios WHERE username='instructor.demo'").fetchone()[0]
            volunteer_id = conexion.execute("SELECT id FROM usuarios WHERE username='voluntario.demo'").fetchone()[0]
            conexion.execute("INSERT INTO instructores(usuario_id) VALUES (?)", (instructor_id,))
            conexion.execute("INSERT INTO voluntarios(usuario_id,instructor_id) VALUES (?,?)", (volunteer_id,instructor_id))
            instrument_id = conexion.execute("INSERT INTO instrumentos(nombre,version,idioma) VALUES ('Candidato','1','es')").lastrowid
            evaluation_id = conexion.execute("INSERT INTO evaluaciones(codigo,nombre,categoria,origen_nota,instrumento_id) VALUES ('PSI-01','Candidato psicométrico','PSICOMETRICA','INSTRUCTOR_VOLUNTARIO',?)", (instrument_id,)).lastrowid
            period_id = conexion.execute("INSERT INTO periodos(nombre,fecha_inicio,fecha_fin,estado) VALUES ('Ciclo psi','2026-01-01','2026-12-31','ACTIVO')").lastrowid
            assignment_id = conexion.execute("INSERT INTO asignaciones_evaluacion(voluntario_id,periodo_id,evaluacion_id) VALUES (?,?,?)", (volunteer_id,period_id,evaluation_id)).lastrowid
            conexion.commit()
        self.assertEqual(self._login().status_code, 200)
        activate = self.cliente.patch(f"/api/admin/evaluaciones/{evaluation_id}", json={"activo": True}, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(activate.status_code, 409)
        self.cliente.post("/api/auth/logout", headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(self._login("instructor.demo", "Clave instructor 123!").status_code, 200)
        score = self.cliente.post(f"/api/jefe-personal/asignaciones/{assignment_id}/calificaciones", json={"nota_0_100": 90}, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(score.status_code, 403)

    def test_voluntario_ve_estado_de_evaluacion_sin_resultados(self):
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            volunteer_id = conexion.execute("SELECT id FROM usuarios WHERE username='voluntario.demo'").fetchone()[0]
            conexion.execute("INSERT INTO voluntarios(usuario_id) VALUES (?)", (volunteer_id,))
            period_id = conexion.execute("INSERT INTO periodos(nombre,fecha_inicio,fecha_fin,estado) VALUES ('Panel demo','2026-01-01','2026-12-31','ACTIVO')").lastrowid
            evaluation_id = conexion.execute("INSERT INTO evaluaciones(codigo,nombre,categoria,origen_nota,activo) VALUES ('FIS-02','Resistencia','FISICA','JEFE_PERSONAL',1)").lastrowid
            assignment_id = conexion.execute("INSERT INTO asignaciones_evaluacion(voluntario_id,periodo_id,evaluacion_id,estado) VALUES (?,?,?,'COMPLETADA')", (volunteer_id,period_id,evaluation_id)).lastrowid
            conexion.execute("INSERT INTO calificaciones(asignacion_id,registrada_por,nota_0_100,observacion) VALUES (?,?,99,'Texto privado')", (assignment_id,1))
            conexion.commit()
        self.assertEqual(self._login("voluntario.demo", "Clave voluntario 123!").status_code, 200)
        respuesta = self.cliente.get("/api/instructor-voluntario/evaluaciones")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json["evaluaciones"][0]["estado"], "COMPLETADA")
        self.assertNotIn("nota_0_100", str(respuesta.json))
        self.assertNotIn("observacion", str(respuesta.json))

    def test_admin_aprueba_solicitud_y_cuenta_puede_ingresar(self):
        creada = self._post_alta("/api/registro/solicitudes", json={
            "username": "aprobada.demo", "nombres": "Voluntaria", "apellido_paterno": "Aprobada", "apellido_materno": "Demo",
            "fecha_nacimiento": "1990-06-07",
            "especialidad_principal": "Primeros Auxilios",
            "password": "Contraseña segura 123!",
        }, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(creada.status_code, 201)
        self.assertEqual(self._login().status_code, 200)
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            instructor_id = conexion.execute("SELECT id FROM usuarios WHERE username='instructor.demo'").fetchone()[0]
            conexion.execute("INSERT INTO instructores (usuario_id) VALUES (?)", (instructor_id,))
            conexion.commit()
        solicitud_id = self.cliente.get("/api/admin/solicitudes").json["solicitudes"][0]["id"]
        aprobada = self.cliente.post(f"/api/admin/solicitudes/{solicitud_id}/aprobar", json={"instructor_id": instructor_id}, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(aprobada.status_code, 200)
        with self.app.app_context():
            from sicose.db import obtener_conexion
            asignado = obtener_conexion().execute("SELECT instructor_id FROM voluntarios JOIN usuarios ON usuarios.id=voluntarios.usuario_id WHERE username='aprobada.demo'").fetchone()[0]
            self.assertEqual(asignado, instructor_id)
        self.cliente.post("/api/auth/logout", headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(self._login("aprobada.demo", "Contraseña segura 123!").status_code, 200)

    def test_invitacion_es_de_un_solo_uso_y_requiere_aprobacion(self):
        self.assertEqual(self._login().status_code, 200)
        creada = self.cliente.post("/api/admin/invitaciones", json={"correo": "invitada@example.org"}, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(creada.status_code, 201)
        token = creada.json["invitacion_url"].rsplit("/", 1)[1]
        respuesta = self._post_alta(f"/api/registro/invitaciones/{token}", json={
            "username": "invitada.demo", "nombres": "Invitada", "apellido_paterno": "Prueba", "apellido_materno": "Demo",
            "fecha_nacimiento": "1987-12-08", "correo": "invitada@example.org",
            "especialidad_principal": "Rescate en selva",
            "password": "Contraseña segura 123!",
        }, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(respuesta.status_code, 201)
        repetida = self._post_alta(f"/api/registro/invitaciones/{token}", json={
            "username": "otra.demo", "nombres": "Otra", "apellido_paterno": "Prueba", "apellido_materno": "Demo",
            "fecha_nacimiento": "1987-12-08", "correo": "invitada@example.org",
            "especialidad_principal": "Rescate en selva",
            "password": "Contraseña segura 123!",
        }, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(repetida.status_code, 404)

    def test_instructor_solo_lista_y_desactiva_su_equipo(self):
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            instructor_id = conexion.execute("SELECT id FROM usuarios WHERE username='instructor.demo'").fetchone()[0]
            conexion.execute("INSERT INTO instructores (usuario_id) VALUES (?)", (instructor_id,))
            voluntario_id = conexion.execute("SELECT id FROM usuarios WHERE username='voluntario.demo'").fetchone()[0]
            conexion.execute("INSERT INTO voluntarios (usuario_id, instructor_id) VALUES (?, ?)", (voluntario_id, instructor_id))
            conexion.commit()
        self.assertEqual(self._login("instructor.demo", "Clave instructor 123!").status_code, 200)
        listado = self.cliente.get("/api/instructores-voluntarios")
        self.assertEqual([v["username"] for v in listado.json["voluntarios"]], ["voluntario.demo"])
        self.assertIn("especialidad_principal", listado.json["voluntarios"][0])
        desactivado = self.cliente.post("/api/instructores-voluntarios/3/desactivar", headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(desactivado.status_code, 200)

    def test_instructor_no_puede_editar_voluntario_de_otro(self):
        with self.app.app_context():
            from sicose.db import obtener_conexion
            conexion = obtener_conexion()
            instructor_id = conexion.execute("SELECT id FROM usuarios WHERE username='instructor.demo'").fetchone()[0]
            conexion.execute("INSERT INTO instructores (usuario_id) VALUES (?)", (instructor_id,))
            otro_id = conexion.execute("SELECT id FROM usuarios WHERE username='admin.demo'").fetchone()[0]
            # Perfil voluntario distinto al ámbito asignado.
            conexion.execute("INSERT INTO voluntarios (usuario_id) VALUES (?)", (otro_id,))
            conexion.commit()
        self.assertEqual(self._login("instructor.demo", "Clave instructor 123!").status_code, 200)
        respuesta = self.cliente.patch("/api/instructores-voluntarios/1", json={"nombre": "Cambio"}, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(respuesta.status_code, 404)

    def _preparar_jefe_4a(self):
        from sicose.db import obtener_conexion
        with self.app.app_context():
            conexion = obtener_conexion()
            jefe_id = conexion.execute("SELECT id FROM usuarios WHERE username='instructor.demo'").fetchone()[0]
            conexion.execute("INSERT INTO instructores(usuario_id) VALUES (?)", (jefe_id,))
            conexion.commit()
        self._login("instructor.demo", "Clave instructor 123!")
        return jefe_id

    def _datos_alta_4a(self):
        return {"username": "alta.jefe", "password": "Clave nueva segura 123!",
                "nombres": "Ana", "apellido_paterno": "Perez", "apellido_materno": "Diaz",
                "fecha_nacimiento": "1990-05-12", "especialidad_principal": "Rescate en agua"}

    def test_alta_jefe_pendiente_se_aprueba_con_asignacion_preservada(self):
        from sicose.db import obtener_conexion
        jefe_id = self._preparar_jefe_4a()
        self.assertIn(b">Guardar</button>", self.cliente.get("/gestion/instructores-voluntarios").data)
        respuesta = self._post_alta("/api/jefe-personal/instructores-voluntarios",
                                      json=self._datos_alta_4a(), headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.json["estado"], "PENDIENTE")
        usuario_id = respuesta.json["id"]
        self.assertEqual(self.cliente.get(f"/api/usuarios/{usuario_id}/foto").status_code, 403)
        self.assertEqual(self.cliente.get("/api/instructores-voluntarios").json["voluntarios"], [])
        with self.app.app_context():
            conexion = obtener_conexion()
            self.assertEqual(conexion.execute("SELECT instructor_id FROM voluntarios WHERE usuario_id=?", (usuario_id,)).fetchone()[0], jefe_id)
            solicitud_id = conexion.execute("SELECT id FROM solicitudes_registro WHERE usuario_id=?", (usuario_id,)).fetchone()[0]
            self.assertTrue(check_password_hash(conexion.execute("SELECT password_hash FROM usuarios WHERE id=?", (usuario_id,)).fetchone()[0], self._datos_alta_4a()["password"]))
            self.assertEqual(conexion.execute("SELECT usuario_id FROM auditoria WHERE accion='SOLICITUD_ALTA_JEFE'").fetchone()[0], jefe_id)
        token = self._csrf_token()
        self.assertEqual(self.cliente.post(f"/api/admin/solicitudes/{solicitud_id}/aprobar", json={}, headers={"X-CSRFToken": token}).status_code, 403)
        self.assertEqual(self.cliente.patch(f"/api/instructores-voluntarios/{usuario_id}", json={"correo": "nuevo@example.test"}, headers={"X-CSRFToken": token}).status_code, 404)
        self.cliente.post("/api/auth/logout", headers={"X-CSRFToken": token})
        self.assertEqual(self._login("alta.jefe", self._datos_alta_4a()["password"]).status_code, 401)
        self._login()
        solicitudes = self.cliente.get("/api/admin/solicitudes").json["solicitudes"]
        self.assertEqual(solicitudes[0]["instructor_id"], jefe_id)
        aprobada = self.cliente.post(f"/api/admin/solicitudes/{solicitud_id}/aprobar", json={}, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(aprobada.status_code, 200)
        with self.app.app_context():
            self.assertEqual(obtener_conexion().execute("SELECT instructor_id FROM voluntarios WHERE usuario_id=?", (usuario_id,)).fetchone()[0], jefe_id)
        self.assertEqual(self._login("alta.jefe", self._datos_alta_4a()["password"]).status_code, 200)

    def test_alta_jefe_rechaza_campos_administrativos_csrf_y_colision(self):
        self._preparar_jefe_4a()
        ruta = "/api/jefe-personal/instructores-voluntarios"
        self.assertEqual(self._post_alta(ruta, json=self._datos_alta_4a()).status_code, 400)
        token = self._csrf_token()
        for campo, valor in (("instructor_id", 1), ("estado", "ACTIVO"), ("rol", "ADMINISTRADOR"), ("codigo_instructor", "OTRO")):
            datos = {**self._datos_alta_4a(), campo: valor}
            self.assertEqual(self._post_alta(ruta, json=datos, headers={"X-CSRFToken": token}).status_code, 400)
        self.assertEqual(self._post_alta(ruta, json=self._datos_alta_4a(), headers={"X-CSRFToken": token}).status_code, 201)
        datos = {**self._datos_alta_4a(), "username": "otra.cuenta"}
        self.assertEqual(self._post_alta(ruta, json=datos, headers={"X-CSRFToken": token}).status_code, 409)
        self._login()
        self.assertEqual(self._post_alta(ruta, json=datos, headers={"X-CSRFToken": self._csrf_token()}).status_code, 403)

    def test_jefe_consulta_inactivos_sin_editar_perfil(self):
        from sicose.db import obtener_conexion
        jefe_id = self._preparar_jefe_4a()
        with self.app.app_context():
            conexion = obtener_conexion()
            conexion.execute("INSERT INTO voluntarios(usuario_id,instructor_id) VALUES (3,?)", (jefe_id,))
            conexion.execute("UPDATE usuarios SET estado='INACTIVO' WHERE id=3")
            conexion.commit()
        self.assertEqual(len(self.cliente.get("/api/instructores-voluntarios").json["voluntarios"]), 1)
        self.assertEqual(self.cliente.get("/api/usuarios/3/foto").status_code, 404)
        self.assertEqual(self.cliente.patch("/api/instructores-voluntarios/3", json={"correo": "nuevo@example.test"}, headers={"X-CSRFToken": self._csrf_token()}).status_code, 409)
        self._login()
        self.assertEqual(len(self.cliente.get("/api/instructores-voluntarios").json["voluntarios"]), 1)

    def test_autoservicio_correo_foto_solo_modifica_cuenta_propia(self):
        import io
        from sicose.db import obtener_conexion
        self._login("voluntario.demo", "Clave voluntario 123!")
        pagina = self.cliente.get("/mi-perfil")
        self.assertEqual(pagina.status_code, 200)
        self.assertIn(b'id="perfil-propio-form"', pagina.data)
        self.assertNotIn(b'name="fecha_nacimiento"', pagina.data)
        respuesta = self.cliente.patch("/api/instructor-voluntario/perfil", data={
            "correo": "  PROPIO@example.test  ", "foto": (io.BytesIO(self._png_prueba()), "perfil.png")
        }, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(respuesta.status_code, 200)
        with self.cliente.get("/api/usuarios/3/foto") as foto_propia:
            self.assertEqual(foto_propia.status_code, 200)
        self.assertEqual(self.cliente.get("/api/usuarios/1/foto").status_code, 403)
        self.assertEqual(self.cliente.put("/api/usuarios/1/foto", data={"foto": (io.BytesIO(self._png_prueba()), "otra.png")}, headers={"X-CSRFToken": self._csrf_token()}).status_code, 403)
        with self.app.app_context():
            conexion = obtener_conexion()
            usuario = conexion.execute("SELECT correo,nombre_completo,estado FROM usuarios WHERE id=3").fetchone()
            self.assertEqual(tuple(usuario), ("propio@example.test", "voluntario.demo", "ACTIVO"))
            self.assertIsNone(conexion.execute("SELECT correo FROM usuarios WHERE id=1").fetchone()[0])
            self.assertEqual(conexion.execute("SELECT usuario_id FROM auditoria WHERE accion='PERFIL_PROPIO_ACTUALIZADO'").fetchone()[0], 3)
        self.assertEqual(self.cliente.patch("/api/instructor-voluntario/perfil", json={"correo": ""}, headers={"X-CSRFToken": self._csrf_token()}).status_code, 200)
        with self.app.app_context():
            self.assertIsNone(obtener_conexion().execute("SELECT correo FROM usuarios WHERE id=3").fetchone()[0])

    def test_autoservicio_rechaza_campos_roles_csrf_y_sesion_inactiva(self):
        from sicose.db import obtener_conexion
        ruta = "/api/instructor-voluntario/perfil"
        self.assertEqual(self.cliente.patch(ruta, json={"correo": "x@example.test"}, headers={"X-CSRFToken": self._csrf_token()}).status_code, 401)
        self._login()
        self.assertEqual(self.cliente.get("/mi-perfil").status_code, 403)
        self.assertEqual(self.cliente.patch(ruta, json={"correo": "x@example.test"}, headers={"X-CSRFToken": self._csrf_token()}).status_code, 403)
        self._login("instructor.demo", "Clave instructor 123!")
        self.assertEqual(self.cliente.get("/mi-perfil").status_code, 403)
        self._login("voluntario.demo", "Clave voluntario 123!")
        self.assertEqual(self.cliente.patch(ruta, json={"correo": "x@example.test"}).status_code, 400)
        for campo in ("id", "usuario_id", "rol", "estado", "instructor_id", "nombres", "fecha_nacimiento", "codigo_instructor", "especialidad_principal", "antiguedad_desde", "experiencia_operaciones", "nota", "observaciones"):
            self.assertEqual(self.cliente.patch(ruta, json={"correo": "x@example.test", campo: "cambio"}, headers={"X-CSRFToken": self._csrf_token()}).status_code, 400)
        with self.app.app_context():
            conexion = obtener_conexion()
            self.assertIsNone(conexion.execute("SELECT correo FROM usuarios WHERE id=3").fetchone()[0])
            conexion.execute("UPDATE usuarios SET estado='INACTIVO' WHERE id=3")
            conexion.commit()
        self.assertEqual(self.cliente.get("/mi-perfil").status_code, 302)

    def test_autoservicio_rechaza_correo_foto_invalidos_y_revierte_colision(self):
        import io
        from sicose.db import obtener_conexion
        ruta = "/api/instructor-voluntario/perfil"
        with self.app.app_context():
            conexion = obtener_conexion()
            conexion.execute("UPDATE usuarios SET correo='ocupado@example.test' WHERE id=1")
            conexion.commit()
        self._login("voluntario.demo", "Clave voluntario 123!")
        token = self._csrf_token()
        for correo in ("sin-arroba", "con espacio@example.test", "a" * 255, 123):
            self.assertEqual(self.cliente.patch(ruta, json={"correo": correo}, headers={"X-CSRFToken": token}).status_code, 400)
        respuesta = self.cliente.patch(ruta, data={"correo": "nuevo@example.test", "foto": (io.BytesIO(b"invalida"), "foto.png")}, headers={"X-CSRFToken": token})
        self.assertEqual(respuesta.status_code, 400)
        respuesta = self.cliente.patch(ruta, data={"correo": "ocupado@example.test", "foto": (io.BytesIO(self._png_prueba()), "foto.png")}, headers={"X-CSRFToken": token})
        self.assertEqual(respuesta.status_code, 409)
        with self.app.app_context():
            self.assertEqual(tuple(obtener_conexion().execute("SELECT correo,foto_perfil FROM usuarios WHERE id=3").fetchone()), (None, None))
        self.assertEqual(list(self.media_path.glob("*")), [])

    def test_residencia_y_antiguedad_validan_catalogo_y_limites(self):
        from sicose.perfil_residencia import validar_perfil_residencia, antiguedad_calculada, DEPARTAMENTOS_BOLIVIA
        hoy = date(2026, 10, 10)
        self.assertEqual(len(DEPARTAMENTOS_BOLIVIA), 9)
        for departamento in DEPARTAMENTOS_BOLIVIA:
            datos = {"pais_residencia": "Bolivia", "departamento_residencia": departamento, "ano_incorporacion": "2020"}
            self.assertEqual(validar_perfil_residencia(datos, hoy=hoy)["ano_incorporacion"], 2020)
        for datos in ({"pais_residencia": "País no admitido"}, {"departamento_residencia": "La Paz"}, {"pais_residencia": "Bolivia", "departamento_residencia": "Otro"}, {"ano_incorporacion": 2027}, {"ano_incorporacion": 0}, {"ano_incorporacion": True}, {"ano_incorporacion": 2020.5}, {"ano_incorporacion": "2020.0"}):
            with self.assertRaises(ValueError): validar_perfil_residencia(datos, hoy=hoy)
        self.assertEqual(antiguedad_calculada(2026, hoy), 0)
        self.assertEqual(antiguedad_calculada(2020, hoy), 6)
        self.assertEqual(antiguedad_calculada(2020, date(2027, 1, 1)), 7)
        self.assertIsNone(antiguedad_calculada(None, hoy))

    def test_gestion_residencia_guarda_calcula_y_preserva_fecha_historica(self):
        from sicose.db import obtener_conexion
        jefe_id = self._preparar_jefe_4a()
        with self.app.app_context():
            conexion = obtener_conexion()
            conexion.execute("INSERT INTO voluntarios(usuario_id,instructor_id,antiguedad_desde) VALUES (3,?,'2019-01-15')", (jefe_id,))
            conexion.commit()
        cambios = {"pais_residencia": "Bolivia", "departamento_residencia": "La Paz", "ano_incorporacion": date.today().year}
        respuesta = self.cliente.patch("/api/instructores-voluntarios/3", json=cambios, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(respuesta.status_code, 200)
        perfil = self.cliente.get("/api/instructores-voluntarios").json["voluntarios"][0]
        self.assertEqual(perfil["antiguedad_anos"], 0)
        self.assertEqual(perfil["departamento_residencia"], "La Paz")
        self.assertEqual(perfil["antiguedad_desde"], "2019-01-15")
        self.assertEqual(self.cliente.patch("/api/instructores-voluntarios/3", json={"pais_residencia": ""}, headers={"X-CSRFToken": self._csrf_token()}).status_code, 400)
        self.assertEqual(self.cliente.patch("/api/instructores-voluntarios/1", json=cambios, headers={"X-CSRFToken": self._csrf_token()}).status_code, 404)
        self._login("voluntario.demo", "Clave voluntario 123!")
        self.assertEqual(self.cliente.get("/api/instructores-voluntarios").status_code, 403)
        self.assertEqual(self.cliente.patch("/api/instructor-voluntario/perfil", json=cambios, headers={"X-CSRFToken": self._csrf_token()}).status_code, 400)
        pagina = self.cliente.get("/mi-perfil").data
        self.assertNotIn(b"ano_incorporacion", pagina)
        self.assertNotIn("ano_incorporacion", str(self.cliente.get("/api/instructor-voluntario/evaluaciones").json))
        self._login()
        vacios = {"pais_residencia": "", "departamento_residencia": "", "ano_incorporacion": ""}
        self.assertEqual(self.cliente.patch("/api/instructores-voluntarios/3", json=vacios, headers={"X-CSRFToken": self._csrf_token()}).status_code, 200)
        self.assertIsNone(self.cliente.get("/api/instructores-voluntarios").json["voluntarios"][0]["antiguedad_anos"])

    def test_altas_gestion_residencia_y_registro_publico_restringido(self):
        from sicose.db import obtener_conexion
        jefe_id = self._preparar_jefe_4a()
        datos = {**self._datos_alta_4a(), "pais_residencia": "Bolivia", "departamento_residencia": "Beni", "ano_incorporacion": 2024}
        respuesta = self._post_alta("/api/jefe-personal/instructores-voluntarios", json=datos, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(respuesta.status_code, 201)
        with self.app.app_context():
            fila = obtener_conexion().execute("SELECT pais_residencia,departamento_residencia,ano_incorporacion,instructor_id FROM voluntarios WHERE usuario_id=?", (respuesta.json["id"],)).fetchone()
            self.assertEqual(tuple(fila), ("Bolivia", "Beni", 2024, jefe_id))
        self._login()
        datos.update(username="alta.admin", fecha_nacimiento="1991-05-12")
        self.assertEqual(self._post_alta("/api/admin/instructores-voluntarios", json=datos, headers={"X-CSRFToken": self._csrf_token()}).status_code, 201)
        datos.update(username="alta.publica", fecha_nacimiento="1992-05-12")
        datos.update(username="registro.geo", nombres="Geografía", apellido_paterno="Nueva", apellido_materno="Demo")
        self.assertEqual(self._post_alta("/api/registro/solicitudes", json=datos, headers={"X-CSRFToken": self._csrf_token()}).status_code, 201)

    def test_migracion_v8_a_v9_preserva_perfiles_y_es_idempotente(self):
        from sicose.db import obtener_conexion
        with self.app.app_context():
            conexion = obtener_conexion()
            conexion.execute("INSERT INTO voluntarios(usuario_id,antiguedad_desde,experiencia_operaciones) VALUES (3,'2020-01-15','Histórica')")
            for campo in ("pais_residencia", "departamento_residencia", "ano_incorporacion"):
                conexion.execute(f"ALTER TABLE voluntarios DROP COLUMN {campo}")
            conexion.execute("UPDATE app_meta SET valor='8' WHERE clave='schema_version'")
            conexion.commit()
            antes = conexion.execute("SELECT * FROM voluntarios").fetchone()
            inicializar_base_datos()
            inicializar_base_datos()
            despues = conexion.execute("SELECT * FROM voluntarios").fetchone()
            for campo in antes.keys(): self.assertEqual(antes[campo], despues[campo])
            for campo in ("pais_residencia", "departamento_residencia", "ano_incorporacion"):
                self.assertIsNone(despues[campo])
            self.assertEqual(conexion.execute("SELECT valor FROM app_meta WHERE clave='schema_version'").fetchone()[0], "33")
            self.assertEqual(conexion.execute("PRAGMA quick_check").fetchone()[0], "ok")
            self.assertEqual(conexion.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_secundarias_permisos_validacion_y_consulta_propia(self):
        from sicose.db import obtener_conexion
        jefe_id = self._preparar_jefe_4a()
        with self.app.app_context():
            conexion = obtener_conexion()
            conexion.execute("INSERT INTO voluntarios(usuario_id,instructor_id,especialidad_principal) VALUES (3,?,'K-9')", (jefe_id,))
            conexion.commit()
        ruta = "/api/instructores-voluntarios/3"
        def editar(valores):
            return self.cliente.patch(ruta, json={"especialidades_secundarias": valores}, headers={"X-CSRFToken": self._csrf_token()})
        self.assertEqual(editar(["K-9", "Primeros Auxilios"]).status_code, 200)
        self.assertEqual(self.cliente.get("/api/instructores-voluntarios").json["voluntarios"][0]["especialidades_secundarias"], ["K-9", "Primeros Auxilios"])
        for invalido in (None, "K-9", ["Otro"], ["K-9", "K-9"], [False]):
            self.assertEqual(editar(invalido).status_code, 400)
        self.assertEqual(self.cliente.patch(ruta, json={"especialidades_secundarias": []}).status_code, 400)
        self._login("voluntario.demo", "Clave voluntario 123!")
        self.assertIn(b'Primeros Auxilios', self.cliente.get("/mi-perfil").data)
        self.assertEqual(editar([]).status_code, 403)
        self.assertEqual(self.cliente.patch("/api/instructor-voluntario/perfil", json={"especialidades_secundarias": []}, headers={"X-CSRFToken": self._csrf_token()}).status_code, 400)
        self._login()
        self.assertEqual(editar([]).status_code, 200)
        with self.app.app_context():
            conexion = obtener_conexion()
            conexion.execute("UPDATE voluntarios SET instructor_id=NULL WHERE usuario_id=3")
            conexion.commit()
        self._login("instructor.demo", "Clave instructor 123!")
        self.assertEqual(editar(["K-9"]).status_code, 200)

    def test_4b_catalogo_y_capacitaciones_relacionales_sin_filtraciones(self):
        from sicose.db import obtener_conexion
        jefe = self._preparar_jefe_4a()
        with self.app.app_context():
            conexion=obtener_conexion()
            conexion.execute("INSERT INTO voluntarios(usuario_id,instructor_id) VALUES (3,?)",(jefe,))
            conexion.execute("INSERT INTO capacitaciones(voluntario_id,nombre,observacion) VALUES (3,'Histórico','Privada')")
            conexion.commit()
        self.assertEqual(self.cliente.post('/api/cursos',json={'nombre':'Curso Jefe DEMO','tipo':'Capacitación','entidad':'Entidad DEMO','fecha_inicio':'2026-10-01','fecha_fin':'2026-10-20','puntaje':10},headers={'X-CSRFToken':self._csrf_token()}).status_code,201)
        self._login()
        respuesta=self.cliente.post('/api/cursos',json={'nombre':'Curso DEMO','tipo':'Capacitación','entidad':'Entidad DEMO','fecha_inicio':'2026-10-01','fecha_fin':'2026-10-20','puntaje':10},headers={'X-CSRFToken':self._csrf_token()})
        self.assertEqual(respuesta.status_code,201);curso=respuesta.json['id']
        self.assertEqual(self.cliente.post('/api/cursos',json={'nombre':'Curso DEMO','tipo':'Capacitación','entidad':'Entidad DEMO','fecha_inicio':'2026-10-01','fecha_fin':'2026-10-20','puntaje':10},headers={'X-CSRFToken':self._csrf_token()}).status_code,409)
        self._login('instructor.demo','Clave instructor 123!')
        ruta='/api/jefe-personal/instructores-voluntarios/3/capacitaciones'
        registro=self.cliente.post(ruta,json={'curso_id':curso,'observacion':'Oculta'},headers={'X-CSRFToken':self._csrf_token()})
        self.assertEqual(registro.status_code,201)
        self.assertEqual(self.cliente.post(ruta,json={'curso_id':999},headers={'X-CSRFToken':self._csrf_token()}).status_code,400)
        self._login('voluntario.demo','Clave voluntario 123!')
        registros=self.cliente.get('/api/instructor-voluntario/capacitaciones').json['capacitaciones']
        self.assertEqual(len(registros),2)
        self.assertTrue(all('observacion' not in fila and 'voluntario_id' not in fila for fila in registros))
        self.assertEqual(self.cliente.get('/api/cursos').status_code,403)
        self.assertEqual(self.cliente.get('/mis-cursos').status_code,200)
        with self.app.app_context():
            historico=obtener_conexion().execute("SELECT nombre,curso_id,observacion FROM capacitaciones WHERE nombre='Histórico'").fetchone()
            self.assertEqual(tuple(historico),('Histórico',None,'Privada'))

    def test_4b_operaciones_eventos_admin_participaciones_por_ambito(self):
        from sicose.db import obtener_conexion
        jefe=self._preparar_jefe_4a()
        with self.app.app_context():
            conexion=obtener_conexion();conexion.execute("INSERT INTO voluntarios(usuario_id,instructor_id) VALUES (3,?)",(jefe,));conexion.commit()
        evento={'tipo_evento':'Simulacro','lugar':'Lugar DEMO','fecha_inicio':'2026-10-01','fecha_fin':'2026-10-02','institucion_responsable':'Entidad DEMO'}
        self.assertEqual(self.cliente.post('/api/operaciones',json={**evento,'fecha_fin':'2026-09-30'},headers={'X-CSRFToken':self._csrf_token()}).status_code,400)
        self._login()
        self.assertEqual(self.cliente.post('/api/operaciones',json={**evento,'fecha_fin':'2026-09-30'},headers={'X-CSRFToken':self._csrf_token()}).status_code,400)
        respuesta=self.cliente.post('/api/operaciones',json=evento,headers={'X-CSRFToken':self._csrf_token()});self.assertEqual(respuesta.status_code,201);identificador=respuesta.json['id']
        self.assertEqual(self.cliente.patch(f'/api/operaciones/{identificador}',json={'lugar':'Otro lugar DEMO'},headers={'X-CSRFToken':self._csrf_token()}).status_code,200)
        self._login('instructor.demo','Clave instructor 123!')
        self.assertEqual(self.cliente.patch(f'/api/operaciones/{identificador}',json={'lugar':'Edición global del Jefe'},headers={'X-CSRFToken':self._csrf_token()}).status_code,200)
        ruta=f'/api/operaciones/{identificador}/participaciones'
        self.assertEqual(self.cliente.post(ruta,json={'voluntario_id':3}).status_code,400)
        self.assertEqual(self.cliente.post(ruta,json={'voluntario_id':1},headers={'X-CSRFToken':self._csrf_token()}).status_code,404)
        self.assertEqual(self.cliente.post(ruta,json={'voluntario_id':3},headers={'X-CSRFToken':self._csrf_token()}).status_code,201)
        self.assertEqual(self.cliente.post(ruta,json={'voluntario_id':3},headers={'X-CSRFToken':self._csrf_token()}).status_code,409)
        self._login('voluntario.demo','Clave voluntario 123!')
        eventos=self.cliente.get('/api/operaciones').json['operaciones'];self.assertEqual(len(eventos),1)
        self.assertEqual(eventos[0]['participantes'],[{'voluntario_id':3,'nombre':'voluntario.demo','revision':1,'cuenta_estado':'ACTIVO','retirada':0}])
        self.assertEqual(self.cliente.post(ruta,json={'voluntario_id':3},headers={'X-CSRFToken':self._csrf_token()}).status_code,403)
        self.assertEqual(self.cliente.get('/gestion/operaciones').status_code,200)
        with self.app.app_context():
            conexion=obtener_conexion();conexion.execute("UPDATE voluntarios SET instructor_id=NULL WHERE usuario_id=3");conexion.commit()
        self._login('instructor.demo','Clave instructor 123!')
        self.assertEqual(len(self.cliente.get('/api/operaciones').json['operaciones'][0]['participantes']),1)
        self.assertEqual(self.cliente.post(ruta,json={'voluntario_id':3},headers={'X-CSRFToken':self._csrf_token()}).status_code,409)

    def test_4b_geografia_ampliada_consulta_propia_y_migracion_aditiva(self):
        from sicose.db import obtener_conexion
        jefe=self._preparar_jefe_4a()
        with self.app.app_context():
            conexion=obtener_conexion();conexion.execute("INSERT INTO voluntarios(usuario_id,instructor_id,pais_residencia,departamento_residencia) VALUES (3,?,'Bolivia','La Paz')",(jefe,));conexion.commit()
        datos={'pais_residencia':'Perú','departamento_residencia':'Cusco','nacionalidad':'Bolivia'}
        respuesta=self.cliente.patch('/api/instructores-voluntarios/3',json=datos,headers={'X-CSRFToken':self._csrf_token()});self.assertEqual(respuesta.status_code,200)
        perfil=self.cliente.get('/api/instructores-voluntarios').json['voluntarios'][0]
        for campo,valor in datos.items():self.assertEqual(perfil[campo],valor)
        with self.app.app_context():
            inicializar_base_datos();inicializar_base_datos();conexion=obtener_conexion()
            self.assertEqual(conexion.execute('PRAGMA quick_check').fetchone()[0],'ok');self.assertEqual(conexion.execute('PRAGMA foreign_key_check').fetchall(),[])
        self._login('voluntario.demo','Clave voluntario 123!')
        self.assertIn(b'Cusco',self.cliente.get('/mi-perfil').data)
        self.assertEqual(self.cliente.patch('/api/instructor-voluntario/perfil',json=datos,headers={'X-CSRFToken':self._csrf_token()}).status_code,400)
        self._login('instructor.demo','Clave instructor 123!')
        self.assertEqual(self.cliente.patch('/api/instructores-voluntarios/3',json={'pais_residencia':'Bolivia','departamento_residencia':'Otro'},headers={'X-CSRFToken':self._csrf_token()}).status_code,400)

    def test_cursos_registro_validacion_fechas_y_pantalla_sin_personas(self):
        self._login()
        datos={'nombre':'Taller DEMO','tipo':'Taller','puntaje':10,'entidad':'Entidad DEMO','fecha_inicio':'2026-10-01','fecha_fin':'2026-10-10','observaciones':'Opcional'}
        headers={'X-CSRFToken':self._csrf_token()}
        respuesta=self.cliente.post('/api/cursos',json=datos,headers=headers)
        self.assertEqual(respuesta.status_code,201)
        curso=self.cliente.get('/api/cursos').json['cursos'][0]
        for campo,valor in datos.items(): self.assertEqual(curso[campo],valor)
        for cambio in ({'tipo':'Otro'},{'estado':'Otro'},{'fecha_fin':'2026-09-01'},{'fecha_inicio':False},{'observaciones':123},{'voluntario_id':3}):
            self.assertEqual(self.cliente.patch(f"/api/cursos/{curso['id']}",json=cambio,headers=headers).status_code,400)
        self.assertEqual(self.cliente.patch(f"/api/cursos/{curso['id']}",json={'estado':'Finalizado'},headers=headers).status_code,400)
        pagina=self.cliente.get('/gestion/capacitaciones').data
        self.assertNotIn(b'name="voluntario_id"',pagina)
        self.assertIn(b'Registro de curso',pagina)
        self.assertEqual(self.cliente.post('/api/cursos',json=datos).status_code,400)

    def test_reporte_cursos_por_fecha_tipo_estado_y_roles(self):
        from sicose.db import obtener_conexion
        self._preparar_jefe_4a()
        with self.app.app_context():
            c=obtener_conexion()
            c.executemany("INSERT INTO cursos(nombre,tipo,estado,fecha_inicio,fecha_fin) VALUES (?,?,?,?,?)", [('Curso A','Taller','Finalizado','2026-10-01','2026-10-05'),('Curso B','Capacitación','Próximo','2026-10-02','2026-10-09'),('Curso C','Taller','Próximo',None,None)])
            c.commit()
        ruta='/api/cursos/reporte.pdf'
        consulta={'desde':'2026-10-01','hasta':'2026-10-02','tipo':'Taller','estado':'Próximo'}
        from unittest.mock import patch
        from io import BytesIO
        with patch('sicose.formacion.hoy_bolivia',return_value=date(2026,9,30)), patch('sicose.reportes_cursos.generar_pdf_cursos', return_value=BytesIO(b'%PDF-1.4 DEMO')) as generar:
            respuesta=self.cliente.get(ruta,query_string=consulta)
            self.assertEqual(respuesta.status_code,200);self.assertEqual(respuesta.mimetype,'application/pdf')
            self.assertEqual([r['nombre'] for r in generar.call_args.args[0]],['Curso A'])
            self.assertNotIn('observaciones',generar.call_args.args[0][0]);respuesta.close()
        respuesta=self.cliente.get(ruta,query_string=consulta);self.assertTrue(respuesta.data.startswith(b'%PDF-'));respuesta.close()
        for cambio in ({'hasta':'2026-09-01'},{'tipo':'Otro'},{'estado':'Otro'},{'desde':'fecha'}):
            self.assertEqual(self.cliente.get(ruta,query_string={**consulta,**cambio}).status_code,400)
        self._login('voluntario.demo','Clave voluntario 123!')
        self.assertEqual(self.cliente.get(ruta,query_string=consulta).status_code,403)
        self.assertEqual(self.cliente.post('/api/cursos',json={'nombre':'No','tipo':'Taller','estado':'Próximo'},headers={'X-CSRFToken':self._csrf_token()}).status_code,403)

    def test_asistencia_correcciones_historial_y_no_duplicados(self):
        from sicose.db import obtener_conexion
        jefe=self._preparar_jefe_4a()
        with self.app.app_context():
            c=obtener_conexion();c.execute('INSERT INTO voluntarios(usuario_id,instructor_id) VALUES (3,?)',(jefe,));c.commit()
        datos={'fecha':'2026-10-10','actividad':'Entrenamiento','asistencias':[{'voluntario_id':3,'estado':'FALTA'}]}
        ruta='/api/jefe-personal/asistencias'
        for estado in ('FALTA','ASISTE','ASISTE'):
            datos['asistencias'][0]['estado']=estado
            self.assertEqual(self.cliente.post(ruta,json=datos,headers={'X-CSRFToken':self._csrf_token()}).status_code,200)
        identificador=self.cliente.get(ruta).json['asistencias'][0]['id']
        historial=self.cliente.get(f'{ruta}/{identificador}/historial').json['historial']
        self.assertEqual(len(historial),1);self.assertEqual(historial[0]['estado_anterior'],'FALTA');self.assertEqual(historial[0]['estado_nuevo'],'ASISTE')
        self._login()
        self.assertEqual(self.cliente.patch(f'{ruta}/{identificador}',json={'estado':'ATRASO'},headers={'X-CSRFToken':self._csrf_token()}).status_code,200)
        self.assertEqual(self.cliente.patch(f'{ruta}/{identificador}',json={'estado':'FALTA'}).status_code,400)
        self.assertEqual(self.cliente.patch(f'{ruta}/{identificador}',json={'estado':'FALTA','fecha':'2026-10-11'},headers={'X-CSRFToken':self._csrf_token()}).status_code,400)
        with self.app.app_context():
            c=obtener_conexion();inicializar_base_datos();inicializar_base_datos()
            self.assertEqual(c.execute('SELECT COUNT(*) FROM asistencias').fetchone()[0],1)
            filas=c.execute('SELECT corregido_por,corregido_en FROM historial_asistencias ORDER BY id').fetchall()
            self.assertEqual([f[0] for f in filas],[jefe,1]);self.assertTrue(all(f[1] for f in filas))
            c.execute('UPDATE voluntarios SET instructor_id=NULL WHERE usuario_id=3');c.commit()
        self._login('instructor.demo','Clave instructor 123!')
        self.assertEqual(self.cliente.patch(f'{ruta}/{identificador}',json={'estado':'FALTA'},headers={'X-CSRFToken':self._csrf_token()}).status_code,200)
        self.assertEqual(self.cliente.get(f'{ruta}/{identificador}/historial').status_code,200)
        self._login('voluntario.demo','Clave voluntario 123!')
        self.assertEqual(self.cliente.get(f'{ruta}/{identificador}/historial').status_code,403)

    def test_asistencia_calendario_y_reporte_por_ambito_sin_filtraciones(self):
        from sicose.db import obtener_conexion
        jefe=self._preparar_jefe_4a()
        with self.app.app_context():
            c=obtener_conexion();c.execute('INSERT INTO voluntarios(usuario_id,instructor_id) VALUES (3,?)',(jefe,));c.commit()
        for fecha,actividad,estado in [('2026-10-01','Uno','ASISTE'),('2026-10-01','Dos','ATRASO'),('2026-10-02','Uno','PERMISO'),('2026-10-03','Uno','FALTA'),('2025-10-01','Uno','FALTA')]:
            self.assertEqual(self.cliente.post('/api/jefe-personal/asistencias',json={'fecha':fecha,'actividad':actividad,'asistencias':[{'voluntario_id':3,'estado':estado}]},headers={'X-CSRFToken':self._csrf_token()}).status_code,200)
        argumentos={'desde':'2026-10-01','hasta':'2026-10-03'}
        ruta='/api/jefe-personal/asistencias/reporte'
        reporte=self.cliente.get(ruta,query_string=argumentos).json
        self.assertEqual(len(reporte['llamadas']),4)
        self.assertEqual(reporte['personas'][0]['totales']['porcentaje'],66.67)
        respuesta=self.cliente.get(ruta+'.pdf',query_string=argumentos);self.assertEqual(respuesta.status_code,200);self.assertTrue(respuesta.data.startswith(b'%PDF-'));respuesta.close()
        self.assertEqual(self.cliente.get(ruta,query_string={'desde':'2026-10-03','hasta':'2026-10-01'}).status_code,400)
        self.assertEqual(self.cliente.get(ruta,query_string={**argumentos,'materia':'X'}).status_code,400)
        self._login('voluntario.demo','Clave voluntario 123!')
        resumen=self.cliente.get('/api/instructor-voluntario/asistencias?gestion=2026').json
        self.assertEqual(len(resumen['registros']),4);self.assertEqual(resumen['totales']['FALTA'],1)
        self.assertEqual(set(resumen['registros'][0]),{'fecha','estado'})
        self.assertEqual(self.cliente.get('/api/instructor-voluntario/asistencias?gestion=2026&voluntario_id=2').status_code,400)
        self.assertEqual(self.cliente.get(ruta,query_string=argumentos).status_code,403)
        self.assertEqual(self.cliente.get('/mis-asistencias').status_code,200)
        self.assertEqual(self.cliente.get('/api/instructor-voluntario/asistencias?gestion=2024').json['totales']['porcentaje'],None)
        with self.app.app_context():
            c=obtener_conexion();c.execute('UPDATE voluntarios SET instructor_id=NULL WHERE usuario_id=3');c.commit()
        self._login('instructor.demo','Clave instructor 123!')
        self.assertEqual(len(self.cliente.get(ruta,query_string=argumentos).json['personas']),1)

    def test_csrf_rechaza_post_sin_token(self):
        csrf_db = Path(".tmp") / f"csrf-{uuid.uuid4().hex}.sqlite3"
        csrf_app = create_app(
            {
                "TESTING": True,
                "WTF_CSRF_ENABLED": True,
                "SECRET_KEY": "clave-de-prueba-csrf",
                "DATABASE": str(csrf_db.resolve()),
            }
        )
        csrf_client = csrf_app.test_client()
        respuesta = csrf_client.post(
            "/api/auth/login", json={"username": "admin.demo", "password": "cualquiera"}
        )
        self.assertEqual(respuesta.status_code, 400)
        if csrf_db.exists():
            csrf_db.unlink()

    def test_configura_cookie_protegida(self):
        self.assertTrue(self.app.config["SESSION_COOKIE_HTTPONLY"])
        self.assertEqual(self.app.config["SESSION_COOKIE_SAMESITE"], "Lax")
        self.assertEqual(self.app.config["PERMANENT_SESSION_LIFETIME"].total_seconds(), 8 * 3600)

    def test_login_registra_auditoria_sin_credenciales(self):
        self._login(password="clave incorrecta")
        self._login()
        self.cliente.post(
            "/api/auth/logout", headers={"X-CSRFToken": self._csrf_token()}
        )
        with self.app.app_context():
            from sicose.db import obtener_conexion

            eventos = obtener_conexion().execute(
                "SELECT accion, resultado FROM auditoria ORDER BY id"
            ).fetchall()
            self.assertEqual(
                [(fila["accion"], fila["resultado"]) for fila in eventos],
                [("LOGIN", "FALLIDO"), ("LOGIN", "EXITOSO"), ("LOGOUT", "EXITOSO")],
            )


if __name__ == "__main__":
    unittest.main()
