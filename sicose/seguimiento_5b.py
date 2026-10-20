"""Comandante SBRAB y notas operativas por fuente; históricos sin inferencia."""
import sqlite3
import re
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, render_template, request, redirect
from flask_login import current_user

from . import db
from .permissions import role_required

seguimiento_bp = Blueprint("seguimiento", __name__)
GESTORES = ("ADMINISTRADOR", "JEFE_PERSONAL")
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
             JOIN usuarios u ON u.id=v.usuario_id WHERE u.id=? AND u.estado IN ('ACTIVO','INACTIVO')"""
    args = [identificador]
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
    # Página histórica retirada; los enlaces guardados llevan al módulo vigente.
    return redirect('/gestion/modelo-anual')


@seguimiento_bp.get("/gestion/comandante")
@role_required("ADMINISTRADOR")
def pagina_comandante():
    return fallo("La cuenta operativa de Comandante está retirada. Usa la transcripción en Notas operativas.", 410)


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
    return fallo("El cargo Comandante se registra en la nota; su cuenta operativa está retirada.", 410)


@seguimiento_bp.get("/api/5b/opciones")
@role_required(*GESTORES)
def opciones():
    c = db.obtener_conexion()
    sql = """SELECT u.id,u.nombre_completo AS nombre FROM voluntarios v
             JOIN usuarios u ON u.id=v.usuario_id WHERE u.estado IN ('ACTIVO','INACTIVO')"""
    args = []
    personal = [dict(f) for f in c.execute(sql + " ORDER BY u.nombre_completo", args)]
    periodos = [dict(f) for f in c.execute("SELECT id,nombre,estado,fecha_inicio,fecha_fin FROM periodos WHERE NOT EXISTS(SELECT 1 FROM modelos_anuales m WHERE m.periodo_id=periodos.id) AND NOT EXISTS(SELECT 1 FROM bajas_gestion b WHERE b.periodo_id=periodos.id) ORDER BY fecha_inicio DESC,id DESC")]
    return jsonify(personal=personal, periodos=periodos)


def notas_persona(c, identificador, periodo_id):
    filas = c.execute("SELECT * FROM notas_operativas WHERE voluntario_id=? AND periodo_id=? ORDER BY id", (identificador, periodo_id))
    notas = []
    for fila in filas:
        nota = dict(fila)
        nota["nota_0_100"] = f"{Decimal(nota.pop('puntos_centesimas')) / 100:.2f}"
        resultado = c.execute('SELECT estado,fecha_realizacion,programacion_id,reprogramacion_id FROM resultados_fisicos WHERE nota_id=?', (nota['id'],)).fetchone()
        nota['fisica'] = dict(resultado) if resultado else None
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
    formacion_personal = [dict(f) for f in c.execute("SELECT id,curso_id,nombre_curso,entidad_curso,estado,puntaje,fecha_finalizacion FROM participaciones_curso WHERE voluntario_id=? ORDER BY id",(identificador,))]
    from .periodos_5b import configuracion
    from .tabla_evaluaciones import habilitada
    from .fisicas import vigente
    fisicas = {f: vigente(c, periodo_id, f, identificador) for f in ('FISICA_1', 'FISICA_2')}
    historial_fisicas = [dict(r) for r in c.execute('SELECT * FROM reprogramaciones_fisicas WHERE periodo_id=? AND voluntario_id=? ORDER BY id', (periodo_id, identificador))]
    from .gestiones import estado_evaluaciones
    from .calculos_5b import regla
    return jsonify(regla_calculo=regla(c, periodo_id), activaciones=estado_evaluaciones(c, periodo_id), fisicas=fisicas, historial_fisicas=historial_fisicas, participaciones_curso=formacion_personal, habilitaciones={f:habilitada(c,identificador,periodo_id,f) for f in FUENTES}, configuracion=configuracion(c, periodo_id), persona=dict(perfil), periodo=dict(periodo), formacion=formacion,
                   asistencias=asistencia, notas=notas_persona(c, identificador, periodo_id), notas_historicas=historicas)


@seguimiento_bp.post("/api/5b/personas/<int:identificador>/notas")
@role_required(*GESTORES)
def registrar_nota(identificador):
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict) or set(datos) - {"periodo_id", "fuente", "nota_0_100", "corregida_de_id", "motivo", "observacion", "capacitaciones", "comandante_nombre", "fisica"}:
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
        comandante_nombre = texto(datos, "comandante_nombre", 160, fuente == "DESEMPENO_COMANDANTE")
        if fuente != "DESEMPENO_COMANDANTE" and comandante_nombre:
            raise ValueError("Nombre del Comandante solo para su aportación.")
        motivo = texto(datos, "motivo", 2000)
        observacion = texto(datos, "observacion", 2000)
        referencias = datos.get("capacitaciones", [])
        if not isinstance(referencias, list) or len(referencias) > 100 or any(isinstance(i, bool) or not isinstance(i, int) or i < 1 for i in referencias) or len(set(referencias)) != len(referencias):
            raise ValueError("Referencias de formación no válidas.")
        if fuente == "ACADEMICA" and not referencias:
            raise ValueError("Académica requiere formación personal referenciada.")
        if fuente not in ('FISICA_1', 'FISICA_2') and fuente != "ACADEMICA" and (referencias or motivo):
            raise ValueError("El respaldo académico corresponde solo a Académica.")
        if fuente in ('FISICA_1', 'FISICA_2') and referencias:
            raise ValueError('Física no admite respaldo académico.')
        if fuente not in ('FISICA_1', 'FISICA_2') and 'fisica' in datos:
            raise ValueError('El resultado físico corresponde solo a Física.')
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
    from .modelo_anual import es_modelo
    if es_modelo(c,pid):
        c.rollback();return fallo('Usa el registro del modelo anual para esta Gestión.',409)
    def rechazar(mensaje, estado):
        c.rollback()
        return fallo(mensaje, estado)
    perfil = persona(c, identificador)
    periodo = c.execute("SELECT estado FROM periodos WHERE id=?", (pid,)).fetchone()
    if perfil is None or periodo is None:
        return rechazar("Persona o período fuera de tu ámbito.", 404)
    if perfil["estado"] != "ACTIVO":
        return rechazar("Reactiva la cuenta antes de registrar notas.", 409)
    from .gestiones import retirada
    if retirada(c, pid) or periodo["estado"] != "ACTIVO":
        return rechazar("Solo se registran/corrigen notas en período activo.", 409)
    fuente_configurada = c.execute("""SELECT f.configuracion_id,f.evaluacion_id FROM fuentes_configuracion_5b f
                            JOIN configuraciones_5b c ON c.id=f.configuracion_id
                            WHERE c.periodo_id=? AND c.estado='PUBLICADA' AND f.fuente=?""", (pid,fuente)).fetchone()
    if fuente_configurada is None:
        return rechazar("El período requiere una configuración 5B publicada; no se adoptan históricos automáticamente.",409)
    from .tabla_evaluaciones import habilitada
    if not habilitada(c, identificador, pid, fuente):
        return rechazar("La evaluación está deshabilitada para esta persona y gestión.", 409)
    ultima = c.execute("SELECT * FROM notas_operativas WHERE voluntario_id=? AND periodo_id=? AND fuente=? ORDER BY id DESC LIMIT 1", (identificador, pid, fuente)).fetchone()
    if (ultima and correccion != ultima["id"]) or (correccion is not None and (ultima is None or correccion != ultima["id"])):
        return rechazar("Recarga el historial; solo puede corregirse la nota vigente.", 409)
    from .calculos_5b import regla
    if fuente == "ACADEMICA" and regla(c, pid):
        return rechazar("Académica se acumula desde formación individual; no admite notas globales manuales con la regla nueva.", 409)
    resultado_fisico = None
    if fuente in ('FISICA_1', 'FISICA_2'):
        from .fisicas import validar_resultado, Conflicto
        try:
            resultado_fisico = validar_resultado(c, identificador, pid, fuente, datos.get('fisica'), puntos)
        except Conflicto as error:
            return rechazar(str(error), 409)
        except ValueError as error:
            return rechazar(str(error), 400)
    respaldo = []
    for referencia in referencias:
        fila = c.execute("SELECT id,nombre,entidad,fecha FROM capacitaciones WHERE id=? AND voluntario_id=?", (referencia, identificador)).fetchone()
        if fila is None:
            return rechazar("La formación referenciada no pertenece a esa persona.", 400)
        respaldo.append(fila)
    evaluador = ultima["evaluador_id"] if ultima else current_user.id
    nombre_evaluador = comandante_nombre if fuente == "DESEMPENO_COMANDANTE" else (ultima["evaluador_nombre"] if ultima else current_user.nombre)
    # Sin vincular al evaluador externo con una cuenta operativa: guardar nombre y transcriptor.
    if fuente == "DESEMPENO_COMANDANTE":
        evaluador = ultima["evaluador_id"] if ultima else current_user.id
    nid = c.execute("""INSERT INTO notas_operativas(voluntario_id,periodo_id,fuente,puntos_centesimas,evaluador_id,registrada_por,
                evaluador_nombre,registrada_por_nombre,motivo,observacion,corregida_de_id,configuracion_id,evaluacion_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (identificador, pid, fuente, int(puntos * 100), evaluador, current_user.id, nombre_evaluador, current_user.nombre, motivo, observacion, correccion, fuente_configurada["configuracion_id"], fuente_configurada["evaluacion_id"])).lastrowid
    c.executemany("INSERT INTO respaldo_academico(nota_id,capacitacion_id,nombre,entidad,fecha) VALUES (?,?,?,?,?)",
                  ((nid, fila["id"], fila["nombre"], fila["entidad"], fila["fecha"]) for fila in respaldo))
    if resultado_fisico:
        c.execute('INSERT INTO resultados_fisicos(nota_id,programacion_id,reprogramacion_id,estado,fecha_realizacion) VALUES (?,?,?,?,?)',
                  (nid, resultado_fisico['programacion_id'], resultado_fisico['reprogramacion_id'], resultado_fisico['estado'], resultado_fisico['fecha_realizacion']))
    db.registrar_auditoria(c, current_user.id, "NOTA_OPERATIVA_CORREGIDA" if ultima else "NOTA_OPERATIVA_REGISTRADA", "EXITOSO")
    c.commit()
    return jsonify(ok=True, id=nid), 201
