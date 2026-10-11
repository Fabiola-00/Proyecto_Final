"""Comandante SBRAB y notas operativas por fuente; históricos sin inferencia."""
import sqlite3
import re
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user
from werkzeug.security import generate_password_hash

from . import db
from .permissions import role_required

seguimiento_bp = Blueprint("seguimiento", __name__)
GESTORES = ("ADMINISTRADOR", "JEFE_PERSONAL", "COMANDANTE_GRUPO")
FUENTES = ("FISICA_1", "FISICA_2", "ACADEMICA", "DESEMPENO_JEFE", "DESEMPENO_COMANDANTE")


def fallo(mensaje, estado=400):
    return jsonify(error=mensaje, codigo="seguimiento_invalido"), estado


def texto(datos, nombre, limite, requerido=False):
    valor = datos.get(nombre)
    if valor is None and not requerido:
        return None
    if not isinstance(valor, str) or len(valor.strip()) > limite or (requerido and not valor.strip()):
        raise ValueError(f"El campo {nombre} no es válido.")
    return valor.strip() or None


def persona(conexion, identificador):
    sql = """SELECT u.id,u.nombre_completo AS nombre,u.estado,v.codigo_instructor,
             v.grado,v.especialidad_principal,v.instructor_id FROM voluntarios v
             JOIN usuarios u ON u.id=v.usuario_id WHERE u.id=? AND u.estado='ACTIVO'"""
    args = [identificador]
    if current_user.rol == "JEFE_PERSONAL":
        sql += " AND v.instructor_id=?"
        args.append(current_user.id)
    return conexion.execute(sql, args).fetchone()


def pagina(titulo, nav, plantilla):
    return render_template(plantilla, titulo_pagina=titulo, nav_activo=nav,
                           indicadores=[], periodo_actual=db.periodo_actual(),
                           descripcion="Seguimiento operativo autorizado de SBRAB.")


@seguimiento_bp.get("/panel/comandante")
@role_required("COMANDANTE_GRUPO")
def panel_comandante():
    return pagina("Comandante del Grupo SBRAB", "seguimiento_5b", "seguimiento_operativo.html")


@seguimiento_bp.get("/gestion/seguimiento-operativo")
@role_required(*GESTORES)
def pagina_seguimiento():
    return pagina("Notas operativas por fuente", "seguimiento_5b", "seguimiento_operativo.html")


@seguimiento_bp.get("/gestion/comandante")
@role_required("ADMINISTRADOR")
def pagina_comandante():
    return pagina("Comandante de SBRAB", "comandante", "gestion_comandante.html")


@seguimiento_bp.get("/api/admin/comandantes")
@role_required("ADMINISTRADOR")
def listar_comandantes():
    filas = db.obtener_conexion().execute("""SELECT u.id,u.username,u.nombre_completo AS nombre,
             u.correo,u.estado FROM usuarios u JOIN roles r ON r.id=u.rol_id
             WHERE r.nombre='COMANDANTE_GRUPO' ORDER BY u.id""")
    return jsonify(comandantes=[dict(f) for f in filas])


@seguimiento_bp.post("/api/admin/comandantes")
@seguimiento_bp.patch("/api/admin/comandantes/<int:identificador>")
@role_required("ADMINISTRADOR")
def guardar_comandante(identificador=None):
    datos = request.get_json(silent=True)
    permitidos = {"nombre", "correo", "estado"} | ({"username", "password"} if identificador is None else set())
    if not isinstance(datos, dict) or not datos or set(datos) - permitidos:
        return fallo("Campos de cuenta no válidos.")
    c = db.obtener_conexion()
    anterior = c.execute("""SELECT u.* FROM usuarios u JOIN roles r ON r.id=u.rol_id
                            WHERE u.id=? AND r.nombre='COMANDANTE_GRUPO'""", (identificador,)).fetchone() if identificador else None
    if identificador and anterior is None:
        return fallo("Comandante no encontrado.", 404)
    valores = dict(anterior) if anterior else {"estado": "ACTIVO"}
    if anterior:
        valores["nombre"] = anterior["nombre_completo"]
    valores.update(datos)
    try:
        nombre = texto(valores, "nombre", 160, True)
        correo = texto(valores, "correo", 254)
        if correo and ("@" not in correo or any(ch.isspace() for ch in correo)):
            raise ValueError("Correo no válido.")
        estado = valores["estado"]
        if estado not in ("ACTIVO", "INACTIVO"):
            raise ValueError("Selecciona Activo o Inactivo.")
        if identificador is None:
            username = texto(valores, "username", 80, True)
            password = datos.get("password")
            if not db.USERNAME_RE.fullmatch(username) or not isinstance(password, str) or not 12 <= len(password) <= 256:
                raise ValueError("Usuario o contraseña no válidos; mínimo 12 caracteres de contraseña.")
            hash_clave = generate_password_hash(password)
    except (ValueError, TypeError) as error:
        return fallo(str(error))
    try:
        c.execute("BEGIN IMMEDIATE")
        if identificador is None:
            rol = c.execute("SELECT id FROM roles WHERE nombre='COMANDANTE_GRUPO'").fetchone()[0]
            identificador = c.execute("""INSERT INTO usuarios(username,nombre_completo,correo,password_hash,rol_id,estado)
                                        VALUES (?,?,?,?,?,?)""", (username, nombre, correo.casefold() if correo else None, hash_clave, rol, estado)).lastrowid
        else:
            c.execute("UPDATE usuarios SET nombre_completo=?,correo=?,estado=?,actualizado_en=? WHERE id=?",
                      (nombre, correo.casefold() if correo else None, estado, db._ahora_utc(), identificador))
        db.registrar_auditoria(c, current_user.id, "COMANDANTE_GUARDADO", "EXITOSO")
        c.commit()
    except sqlite3.IntegrityError:
        c.rollback()
        return fallo("Ya hay un Comandante activo o los datos de cuenta están ocupados.", 409)
    return jsonify(ok=True, id=identificador), 201 if request.method == "POST" else 200


@seguimiento_bp.get("/api/5b/opciones")
@role_required(*GESTORES)
def opciones():
    c = db.obtener_conexion()
    sql = """SELECT u.id,u.nombre_completo AS nombre FROM voluntarios v
             JOIN usuarios u ON u.id=v.usuario_id WHERE u.estado='ACTIVO'"""
    args = []
    if current_user.rol == "JEFE_PERSONAL":
        sql += " AND v.instructor_id=?"
        args.append(current_user.id)
    personal = [dict(f) for f in c.execute(sql + " ORDER BY u.nombre_completo", args)]
    periodos = [dict(f) for f in c.execute("SELECT id,nombre,estado,fecha_inicio,fecha_fin FROM periodos ORDER BY fecha_inicio DESC,id DESC")]
    return jsonify(personal=personal, periodos=periodos)


def notas_persona(c, identificador, periodo_id):
    filas = c.execute("SELECT * FROM notas_operativas WHERE voluntario_id=? AND periodo_id=? ORDER BY id", (identificador, periodo_id))
    notas = []
    for fila in filas:
        nota = dict(fila)
        nota["nota_0_100"] = f"{Decimal(nota.pop('puntos_centesimas')) / 100:.2f}"
        if current_user.rol == "COMANDANTE_GRUPO" and nota["registrada_por"] != current_user.id:
            nota.pop("motivo")
            nota.pop("observacion")
        else:
            nota["referencias"] = [dict(r) for r in c.execute("SELECT capacitacion_id,nombre,entidad,fecha FROM respaldo_academico WHERE nota_id=?", (nota["id"],))]
        notas.append(nota)
    return notas


@seguimiento_bp.get("/api/5b/personas/<int:identificador>")
@role_required(*GESTORES)
def consultar_persona(identificador):
    if set(request.args) != {"periodo_id"}:
        return fallo("Selecciona una persona y un período.")
    try:
        periodo_id = int(request.args["periodo_id"])
    except ValueError:
        return fallo("Período no válido.")
    c = db.obtener_conexion()
    perfil = persona(c, identificador)
    periodo = c.execute("SELECT * FROM periodos WHERE id=?", (periodo_id,)).fetchone()
    if perfil is None or periodo is None:
        return fallo("Persona o período fuera del ámbito autorizado.", 404)
    formacion = [dict(f) for f in c.execute("SELECT id,nombre,entidad,fecha,curso_id FROM capacitaciones WHERE voluntario_id=? ORDER BY fecha DESC,id DESC", (identificador,))]
    asistencia = [dict(f) for f in c.execute("""SELECT fecha,actividad,COALESCE(estado_detalle,CASE estado WHEN 'PRESENTE' THEN 'ASISTE'
                      WHEN 'AUSENTE' THEN 'FALTA' ELSE 'PERMISO' END) AS estado FROM asistencias
                      WHERE voluntario_id=?""" + " AND fecha BETWEEN ? AND ? ORDER BY fecha,id",
                      (identificador, periodo["fecha_inicio"], periodo["fecha_fin"]))]
    historicas = [dict(f) for f in c.execute("""SELECT c.id,c.nota_0_100,c.registrada_en,e.nombre AS evaluacion,e.categoria
                  FROM calificaciones c JOIN asignaciones_evaluacion a ON a.id=c.asignacion_id JOIN evaluaciones e ON e.id=a.evaluacion_id
                  WHERE a.voluntario_id=? AND a.periodo_id=? AND e.categoria!='PSICOMETRICA' ORDER BY c.id""", (identificador, periodo_id))]
    return jsonify(persona=dict(perfil), periodo=dict(periodo), formacion=formacion,
                   asistencias=asistencia, notas=notas_persona(c, identificador, periodo_id), notas_historicas=historicas)


@seguimiento_bp.post("/api/5b/personas/<int:identificador>/notas")
@role_required(*GESTORES)
def registrar_nota(identificador):
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict) or set(datos) - {"periodo_id", "fuente", "nota_0_100", "corregida_de_id", "motivo", "observacion", "capacitaciones"}:
        return fallo("Campos de nota no válidos.")
    try:
        pid, fuente = datos.get("periodo_id"), datos.get("fuente")
        if isinstance(pid, bool) or not isinstance(pid, int) or pid < 1 or fuente not in FUENTES:
            raise ValueError("Período o fuente no válidos.")
        valor = datos.get("nota_0_100")
        if isinstance(valor, bool) or not isinstance(valor, (str, int, float)):
            raise ValueError("Nota no válida.")
        if not re.fullmatch(r"[0-9]{1,3}(?:\.[0-9]{1,2})?", str(valor)):
            raise ValueError("Nota decimal de hasta dos decimales no válida.")
        puntos = Decimal(str(valor))
        if not puntos.is_finite() or not 0 <= puntos <= 100 or puntos * 100 != (puntos * 100).to_integral_value():
            raise ValueError("Nota entre 0 y 100 con hasta dos decimales.")
        motivo = texto(datos, "motivo", 2000, fuente == "ACADEMICA")
        observacion = texto(datos, "observacion", 2000)
        referencias = datos.get("capacitaciones", [])
        if not isinstance(referencias, list) or len(referencias) > 100 or any(isinstance(i, bool) or not isinstance(i, int) or i < 1 for i in referencias) or len(set(referencias)) != len(referencias):
            raise ValueError("Referencias de formación no válidas.")
        if fuente == "ACADEMICA" and not referencias:
            raise ValueError("Académica requiere formación personal referenciada.")
        if fuente != "ACADEMICA" and (referencias or motivo):
            raise ValueError("El respaldo académico corresponde solo a Académica.")
        correccion = datos.get("corregida_de_id")
        if correccion is not None and (isinstance(correccion, bool) or not isinstance(correccion, int) or correccion < 1):
            raise ValueError("Referencia de corrección no válida.")
    except (InvalidOperation, ValueError, TypeError) as error:
        return fallo(str(error))
    c = db.obtener_conexion()
    try:
        c.execute("BEGIN IMMEDIATE")
    except sqlite3.OperationalError:
        return fallo("Hay una actualización en curso. Recarga el historial e inténtalo de nuevo.", 409)
    def rechazar(mensaje, estado):
        c.rollback()
        return fallo(mensaje, estado)
    perfil = persona(c, identificador)
    periodo = c.execute("SELECT estado FROM periodos WHERE id=?", (pid,)).fetchone()
    if perfil is None or periodo is None:
        return rechazar("Persona o período fuera de tu ámbito.", 404)
    if periodo["estado"] != "ACTIVO":
        return rechazar("Solo se registran/corrigen notas en período activo.", 409)
    ultima = c.execute("SELECT * FROM notas_operativas WHERE voluntario_id=? AND periodo_id=? AND fuente=? ORDER BY id DESC LIMIT 1", (identificador, pid, fuente)).fetchone()
    rol = current_user.rol
    if rol == "COMANDANTE_GRUPO" and (fuente != "DESEMPENO_COMANDANTE" or (ultima and ultima["evaluador_id"] != current_user.id)):
        return rechazar("Solo puedes registrar/corregir tu propia aportación de Desempeño.", 403)
    if rol == "JEFE_PERSONAL" and (fuente == "DESEMPENO_COMANDANTE" or (fuente == "DESEMPENO_JEFE" and ultima and ultima["evaluador_id"] != current_user.id)):
        return rechazar("Aportación de otro evaluador.", 403)
    if rol == "ADMINISTRADOR" and ultima is None and fuente in ("ACADEMICA", "DESEMPENO_JEFE", "DESEMPENO_COMANDANTE"):
        return rechazar("Esta aportación inicial corresponde a su evaluador; Administración puede corregirla con historial.", 403)
    if (ultima and correccion != ultima["id"]) or (correccion is not None and (ultima is None or correccion != ultima["id"])):
        return rechazar("Recarga el historial; solo puede corregirse la nota vigente.", 409)
    respaldo = []
    for referencia in referencias:
        fila = c.execute("SELECT id,nombre,entidad,fecha FROM capacitaciones WHERE id=? AND voluntario_id=?", (referencia, identificador)).fetchone()
        if fila is None:
            return rechazar("La formación referenciada no pertenece a esa persona.", 400)
        respaldo.append(fila)
    evaluador = ultima["evaluador_id"] if ultima else current_user.id
    nombre_evaluador = ultima["evaluador_nombre"] if ultima else current_user.nombre
    nid = c.execute("""INSERT INTO notas_operativas(voluntario_id,periodo_id,fuente,puntos_centesimas,evaluador_id,registrada_por,
                evaluador_nombre,registrada_por_nombre,motivo,observacion,corregida_de_id) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (identificador, pid, fuente, int(puntos * 100), evaluador, current_user.id, nombre_evaluador, current_user.nombre, motivo, observacion, correccion)).lastrowid
    c.executemany("INSERT INTO respaldo_academico(nota_id,capacitacion_id,nombre,entidad,fecha) VALUES (?,?,?,?,?)",
                  ((nid, fila["id"], fila["nombre"], fila["entidad"], fila["fecha"]) for fila in respaldo))
    db.registrar_auditoria(c, current_user.id, "NOTA_OPERATIVA_CORREGIDA" if ultima else "NOTA_OPERATIVA_REGISTRADA", "EXITOSO")
    c.commit()
    return jsonify(ok=True, id=nid), 201
