"""Cambio explícito de estado sin aprobar altas ni recuperar sesiones antiguas."""
import unittest
import test_app as fixtures
from sicose.db import obtener_conexion


class EstadoPersonalTestCase(unittest.TestCase):
    setUp = fixtures.AplicacionTestCase.setUp
    tearDown = fixtures.AplicacionTestCase.tearDown
    _crear_usuario = fixtures.AplicacionTestCase._crear_usuario
    _login = fixtures.AplicacionTestCase._login
    _csrf_token = fixtures.AplicacionTestCase._csrf_token

    def preparar(self):
        with self.app.app_context():
            c = obtener_conexion()
            c.execute("INSERT INTO voluntarios (usuario_id, instructor_id, experiencia_operaciones) VALUES (3,NULL,'Historia DEMO')")
            c.commit()

    def cambiar(self, estado, anterior, uid=3):
        return self.cliente.patch(f'/api/instructores-voluntarios/{uid}/estado',
            json={'estado': estado, 'estado_anterior': anterior}, headers={'X-CSRFToken': self._csrf_token()})

    def test_ambos_roles_estado_auditoria_concurrencia_y_preservacion(self):
        self.preparar()
        for user, password in [('admin.demo','Clave demo segura 123!'), ('instructor.demo','Clave instructor 123!')]:
            self._login(user,password)
            with self.app.app_context():
                c=obtener_conexion()
                antes=tuple(c.execute('SELECT * FROM voluntarios WHERE usuario_id=3').fetchone())
                hash_antes=c.execute('SELECT password_hash FROM usuarios WHERE id=3').fetchone()[0]
            self.assertEqual(self.cambiar('INACTIVO','ACTIVO').status_code,200)
            self.assertEqual(self.cambiar('ACTIVO','ACTIVO').status_code,409)
            self.assertEqual(self.cambiar('INACTIVO','INACTIVO').json['sin_cambios'],True)
            self.assertEqual(self.cambiar('ACTIVO','INACTIVO').status_code,200)
            with self.app.app_context():
                c=obtener_conexion()
                self.assertEqual(tuple(c.execute('SELECT * FROM voluntarios WHERE usuario_id=3').fetchone()),antes)
                self.assertEqual(c.execute('SELECT password_hash FROM usuarios WHERE id=3').fetchone()[0],hash_antes)
                audit=c.execute("SELECT usuario_id,accion,fecha FROM auditoria WHERE accion LIKE 'INSTRUCTOR_VOLUNTARIO_%:3:%' ORDER BY id").fetchall()
                self.assertTrue(audit[-2]['accion'].endswith('ACTIVO->INACTIVO'))
                self.assertTrue(audit[-1]['accion'].endswith('INACTIVO->ACTIVO'))
                self.assertEqual(audit[-1]['usuario_id'],1 if user=='admin.demo' else 2)
                self.assertTrue(audit[-1]['fecha'])
        self.assertEqual(len(audit),4)

    def test_permisos_csrf_solicitudes_y_roles_destino(self):
        self.preparar()
        self._login()
        self.assertEqual(self.cliente.patch('/api/instructores-voluntarios/3/estado',json={'estado':'INACTIVO','estado_anterior':'ACTIVO'}).status_code,400)
        self.assertEqual(self.cambiar('PENDIENTE','ACTIVO').status_code,400)
        self.assertEqual(self.cambiar('INACTIVO','ACTIVO',1).status_code,404)
        for estado in ['PENDIENTE','RECHAZADO']:
            with self.app.app_context():
                c=obtener_conexion();c.execute('UPDATE usuarios SET estado=? WHERE id=3',(estado,));c.commit()
            self.assertEqual(self.cambiar('ACTIVO','INACTIVO').status_code,409)
            self.assertEqual(self.cliente.post('/api/instructores-voluntarios/3/desactivar',headers={'X-CSRFToken':self._csrf_token()}).status_code,409)
        with self.app.app_context():
            c=obtener_conexion();c.execute("UPDATE usuarios SET estado='ACTIVO' WHERE id=3");c.commit()
        self._login('voluntario.demo','Clave voluntario 123!')
        self.assertEqual(self.cambiar('INACTIVO','ACTIVO').status_code,403)
        self._login('instructor.demo','Clave instructor 123!')
        with self.app.app_context():
            c=obtener_conexion();c.execute("UPDATE usuarios SET estado='INACTIVO' WHERE id=2");c.commit()
        self.assertEqual(self.cambiar('INACTIVO','ACTIVO').status_code,401)

    def test_desactivar_bloquea_login_y_reactivar_exige_sesion_nueva(self):
        self.preparar()
        self._login('voluntario.demo','Clave voluntario 123!')
        sesion=self.cliente.get_cookie(self.app.config['SESSION_COOKIE_NAME'])
        self._login()
        self.assertEqual(self.cliente.post('/api/instructores-voluntarios/3/desactivar',headers={'X-CSRFToken':self._csrf_token()}).status_code,200)
        otro=self.app.test_client();otro.set_cookie(self.app.config['SESSION_COOKIE_NAME'],sesion.value)
        self.assertEqual(otro.get('/api/auth/me').status_code,401)
        self.assertEqual(self._login('voluntario.demo','Clave voluntario 123!').status_code,401)
        self.assertEqual(self.cambiar('ACTIVO','INACTIVO').status_code,200)
        otro.set_cookie(self.app.config['SESSION_COOKIE_NAME'],sesion.value)
        self.assertEqual(otro.get('/api/auth/me').status_code,401)
        self.assertEqual(self._login('voluntario.demo','Clave voluntario 123!').status_code,200)


