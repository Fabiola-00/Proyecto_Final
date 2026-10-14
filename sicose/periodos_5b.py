"""Borradores anuales y publicación atómica de configuración 5B."""
import sqlite3
from datetime import date

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user

from . import db
from .permissions import role_required
from .seguimiento_5b import FUENTES
from .gestiones import retirada, estado_evaluaciones
from .calculos_5b import regla

periodos_5b_bp = Blueprint("periodos_5b", __name__)
CATEGORIAS_FUENTE = {"FISICA_1": "FISICA", "FISICA_2": "FISICA", "ACADEMICA": "ACADEMICA",
                    "DESEMPENO_JEFE": "JEFE_PERSONAL", "DESEMPENO_COMANDANTE": "JEFE_PERSONAL"}


def fallo(mensaje, estado=400):
    return jsonify(error=mensaje, codigo="periodo_5b_invalido"), estado


def anual(periodo):
    try:
        inicio, fin = date.fromisoformat(periodo["fecha_inicio"]), date.fromisoformat(periodo["fecha_fin"])
        return inicio.month == inicio.day == 1 and fin.month == 12 and fin.day == 31 and inicio.year == fin.year
    except (ValueError, TypeError):
        return False


def configuracion(c, periodo_id):
    fila = c.execute("SELECT * FROM configuraciones_5b WHERE periodo_id=?", (periodo_id,)).fetchone()
    if fila is None:
        return None
    valor = dict(fila)
    valor["fuentes"] = [dict(f) for f in c.execute("SELECT fuente,evaluacion_id,nombre,codigo,categoria FROM fuentes_configuracion_5b WHERE configuracion_id=? ORDER BY fuente", (fila["id"],))]
    return valor


def validar_fuentes(c, fuentes, publicar=False):
    if not isinstance(fuentes, dict) or set(fuentes) - set(FUENTES):
        raise ValueError("Fuentes no válidas.")
    if publicar and (set(fuentes) != set(FUENTES) or any(v is None for v in fuentes.values())):
        raise ValueError("Completa las cinco fuentes antes de publicar.")
    resultado = []
    for fuente, eid in fuentes.items():
        if eid is None:
            continue
        if isinstance(eid, bool) or not isinstance(eid, int) or eid < 1:
            raise ValueError("Selecciona una evaluación válida por fuente.")
        evaluacion = c.execute("SELECT id,nombre,codigo,categoria,origen_nota,activo FROM evaluaciones WHERE id=?", (eid,)).fetchone()
        if evaluacion is None or evaluacion["categoria"] != CATEGORIAS_FUENTE[fuente] or evaluacion["origen_nota"] != "JEFE_PERSONAL":
            raise ValueError("La categoría de evaluación no corresponde a la fuente manual.")
        if publicar and not evaluacion["activo"]:
            raise ValueError("Activa las evaluaciones seleccionadas antes de publicar.")
        resultado.append((fuente, eid, evaluacion["nombre"], evaluacion["codigo"], evaluacion["categoria"]))
    return resultado


def guardar_fuentes(c, cid, filas):
    c.execute("DELETE FROM fuentes_configuracion_5b WHERE configuracion_id=?", (cid,))
    c.executemany("INSERT INTO fuentes_configuracion_5b(configuracion_id,fuente,evaluacion_id,nombre,codigo,categoria) VALUES (?,?,?,?,?,?)",
                  ((cid, *fila) for fila in filas))


@periodos_5b_bp.get("/gestion/periodos-5b")
@role_required("ADMINISTRADOR", "JEFE_PERSONAL")
def pagina():
    return render_template("gestion_periodos_5b.html", titulo_pagina="Gestiones (año)",
                           nav_activo="periodos_5b", indicadores=[], periodo_actual=db.periodo_actual(),
                           descripcion="Gestiona los años evaluados y activa sus evaluaciones; el catálogo es independiente.")


@periodos_5b_bp.get("/api/admin/5b/periodos")
@role_required("ADMINISTRADOR", "JEFE_PERSONAL")
def listar():
    c = db.obtener_conexion()
    periodos = []
    retiradas = []
    for fila in c.execute("SELECT * FROM periodos ORDER BY fecha_inicio DESC,id DESC"):
        periodo = dict(fila)
        periodo["anual"] = anual(periodo)
        periodo["configuracion"] = configuracion(c, periodo["id"])
        periodo["tiene_asignaciones"] = bool(c.execute("SELECT 1 FROM asignaciones_evaluacion WHERE periodo_id=? LIMIT 1", (periodo["id"],)).fetchone())
        periodo["tiene_notas_5b"] = bool(c.execute("SELECT 1 FROM notas_operativas WHERE periodo_id=? LIMIT 1", (periodo["id"],)).fetchone())
        periodo["retirada"] = retirada(c, periodo["id"])
        periodo["evaluaciones_gestion"] = estado_evaluaciones(c, periodo["id"])
        periodo["regla_calculo"] = regla(c, periodo["id"])
        from .cierres_5b import resumen
        periodo["cierres"] = resumen(c, periodo["id"])
        periodo["historial_activaciones"] = [dict(r) for r in c.execute("SELECT * FROM activaciones_gestion WHERE periodo_id=? ORDER BY id", (periodo["id"],))]
        periodo["historial_ediciones"] = [dict(r) for r in c.execute("SELECT * FROM historial_gestiones WHERE periodo_id=? ORDER BY id", (periodo["id"],))]
        periodo["baja"] = dict(c.execute("SELECT * FROM bajas_gestion WHERE periodo_id=?", (periodo["id"],)).fetchone()) if periodo["retirada"] else None
        (retiradas if periodo["retirada"] else periodos).append(periodo)
    return jsonify(periodos=periodos, retiradas=retiradas)


@periodos_5b_bp.post("/api/admin/5b/periodos")
@role_required("ADMINISTRADOR", "JEFE_PERSONAL")
def crear():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict) or set(datos) != {"nombre", "ano"}:
        return fallo("Ingresa nombre y año del borrador.")
    nombre, ano = datos["nombre"], datos["ano"]
    if not isinstance(nombre, str) or not 2 <= len(nombre.strip()) <= 120 or isinstance(ano, bool) or not isinstance(ano, int) or not 1 <= ano <= 9999:
        return fallo("Nombre o año no válidos.")
    c = db.obtener_conexion()
    try:
        pid = c.execute("INSERT INTO periodos(nombre,fecha_inicio,fecha_fin,estado,creado_por) VALUES (?,?,?,'BORRADOR',?)",
                        (nombre.strip(), f"{ano:04d}-01-01", f"{ano:04d}-12-31", current_user.id)).lastrowid
        db.registrar_auditoria(c, current_user.id, "PERIODO_5B_BORRADOR", "EXITOSO")
        c.commit()
    except sqlite3.IntegrityError:
        c.rollback()
        return fallo("Ya existe un período con ese nombre.", 409)
    return jsonify(ok=True, id=pid), 201


@periodos_5b_bp.patch("/api/admin/5b/periodos/<int:pid>")
@role_required("ADMINISTRADOR", "JEFE_PERSONAL")
def editar_gestion(pid):
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict) or set(datos) != {"nombre", "ano", "nombre_anterior", "ano_anterior"}:
        return fallo("Ingresa nombre, año y los valores anteriores de la gestión.")
    nombre, ano = datos["nombre"], datos["ano"]
    if not isinstance(nombre, str) or not 2 <= len(nombre.strip()) <= 120 or type(ano) is not int or not 1 <= ano <= 9999 or not isinstance(datos["nombre_anterior"], str) or type(datos["ano_anterior"]) is not int:
        return fallo("Nombre o año no válidos.")
    c = db.obtener_conexion()
    try:
        c.execute("BEGIN IMMEDIATE")
        periodo = c.execute("SELECT * FROM periodos WHERE id=?", (pid,)).fetchone()
        if periodo is None:
            c.rollback(); return fallo("Gestión no encontrada.", 404)
        conf = configuracion(c, pid)
        if retirada(c, pid) or periodo["estado"] != "BORRADOR" or not anual(periodo) or (conf and conf["estado"] == "PUBLICADA"):
            c.rollback(); return fallo("Solo se editan gestiones anuales en borrador; las publicadas conservan sus datos.", 409)
        if c.execute("SELECT 1 FROM notas_operativas WHERE periodo_id=?", (pid,)).fetchone() or c.execute("SELECT 1 FROM asignaciones_evaluacion WHERE periodo_id=?", (pid,)).fetchone():
            c.rollback(); return fallo("La gestión tiene registros o asignaciones; no se reescribe su historia.", 409)
        if (datos["nombre_anterior"], datos["ano_anterior"]) != (periodo["nombre"], int(periodo["fecha_inicio"][:4])):
            c.rollback(); return fallo("La gestión cambió; recarga antes de editar.", 409)
        if (nombre.strip(), ano) == (periodo["nombre"], int(periodo["fecha_inicio"][:4])):
            c.rollback(); return jsonify(ok=True, id=pid)
        c.execute("UPDATE periodos SET nombre=?,fecha_inicio=?,fecha_fin=? WHERE id=?", (nombre.strip(), f"{ano:04d}-01-01", f"{ano:04d}-12-31", pid))
        c.execute("INSERT INTO historial_gestiones(periodo_id,nombre_anterior,nombre_nuevo,ano_anterior,ano_nuevo,actor_id,actor_nombre,registrada_en) VALUES (?,?,?,?,?,?,?,?)", (pid,periodo["nombre"],nombre.strip(),int(periodo["fecha_inicio"][:4]),ano,current_user.id,current_user.nombre,db._ahora_utc()))
        if conf:
            c.execute("UPDATE configuraciones_5b SET revision=revision+1 WHERE id=?", (conf["id"],))
        db.registrar_auditoria(c, current_user.id, "GESTION_BORRADOR_EDITADA", "EXITOSO")
        c.commit()
    except (sqlite3.IntegrityError, sqlite3.OperationalError):
        c.rollback(); return fallo("Nombre ocupado o edición concurrente; recarga las gestiones.", 409)
    return jsonify(ok=True, id=pid)


@periodos_5b_bp.post("/api/admin/5b/periodos/<int:pid>/configuracion")
@periodos_5b_bp.patch("/api/admin/5b/periodos/<int:pid>/configuracion")
@role_required("ADMINISTRADOR")
def editar_configuracion(pid):
    datos = request.get_json(silent=True)
    campos = {"fuentes"} if request.method == "POST" else {"fuentes", "revision"}
    if not isinstance(datos, dict) or set(datos) != campos:
        return fallo("Campos de configuración no válidos.")
    if request.method == "PATCH" and (isinstance(datos["revision"], bool) or not isinstance(datos["revision"], int) or datos["revision"] < 1):
        return fallo("Revisión no válida.")
    c = db.obtener_conexion()
    try:
        c.execute("BEGIN IMMEDIATE")
        periodo = c.execute("SELECT * FROM periodos WHERE id=?", (pid,)).fetchone()
        if periodo is None:
            c.rollback(); return fallo("Período no encontrado.", 404)
        if retirada(c, pid) or periodo["estado"] != "BORRADOR" or not anual(periodo) or c.execute("SELECT 1 FROM notas_operativas WHERE periodo_id=?", (pid,)).fetchone():
            c.rollback(); return fallo("Configura un borrador anual sin notas previas; los históricos se conservan.", 409)
        existente = c.execute("SELECT * FROM configuraciones_5b WHERE periodo_id=?", (pid,)).fetchone()
        if request.method == "POST" and existente:
            c.rollback(); return fallo("Ya existe configuración; recarga y edita su revisión vigente.", 409)
        if request.method == "PATCH" and existente is None:
            c.rollback(); return fallo("Configuración no encontrada.", 404)
        if existente and (existente["estado"] != "BORRADOR" or isinstance(datos["revision"], bool) or datos["revision"] != existente["revision"]):
            c.rollback(); return fallo("Configuración publicada o revisión desactualizada.", 409)
        filas = validar_fuentes(c, datos["fuentes"])
        if existente:
            cid = existente["id"]
            c.execute("UPDATE configuraciones_5b SET revision=revision+1 WHERE id=?", (cid,))
        else:
            cid = c.execute("INSERT INTO configuraciones_5b(periodo_id,creada_por) VALUES (?,?)", (pid, current_user.id)).lastrowid
        guardar_fuentes(c, cid, filas)
        db.registrar_auditoria(c, current_user.id, "CONFIGURACION_5B_BORRADOR", "EXITOSO")
        c.commit()
    except ValueError as error:
        c.rollback(); return fallo(str(error))
    except (sqlite3.IntegrityError, sqlite3.OperationalError):
        c.rollback(); return fallo("Conflicto de configuración; recarga antes de reintentar.", 409)
    return jsonify(ok=True, configuracion=configuracion(c, pid)), 201 if request.method == "POST" else 200


@periodos_5b_bp.post("/api/admin/5b/periodos/<int:pid>/publicar")
@role_required("ADMINISTRADOR")
def publicar(pid):
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict) or set(datos) != {"revision"} or isinstance(datos["revision"], bool) or not isinstance(datos["revision"], int):
        return fallo("Selecciona la revisión de configuración vigente.")
    c = db.obtener_conexion()
    try:
        c.execute("BEGIN IMMEDIATE")
        periodo = c.execute("SELECT * FROM periodos WHERE id=?", (pid,)).fetchone()
        conf = configuracion(c, pid)
        if periodo is None or conf is None:
            c.rollback(); return fallo("Período o configuración no encontrados.", 404)
        if retirada(c, pid) or periodo["estado"] != "BORRADOR" or not anual(periodo) or conf["estado"] != "BORRADOR" or conf["revision"] != datos["revision"]:
            c.rollback(); return fallo("Recarga un borrador anual y su revisión vigente.", 409)
        if c.execute("SELECT 1 FROM periodos WHERE estado='ACTIVO' AND id!=? AND NOT EXISTS(SELECT 1 FROM bajas_gestion b WHERE b.periodo_id=periodos.id)", (pid,)).fetchone():
            c.rollback(); return fallo("Ya hay un período activo. No se cerrará ni modificará automáticamente.", 409)
        if c.execute("SELECT 1 FROM notas_operativas WHERE periodo_id=?", (pid,)).fetchone():
            c.rollback(); return fallo("No se adoptan notas previas automáticamente.", 409)
        filas = validar_fuentes(c, {f["fuente"]: f["evaluacion_id"] for f in conf["fuentes"]}, publicar=True)
        guardar_fuentes(c, conf["id"], filas)
        c.execute("UPDATE configuraciones_5b SET estado='PUBLICADA',publicada_por=?,publicada_en=? WHERE id=?", (current_user.id, db._ahora_utc(), conf["id"]))
        c.execute("UPDATE periodos SET estado='ACTIVO' WHERE id=?", (pid,))
        db.registrar_auditoria(c, current_user.id, "CONFIGURACION_5B_PUBLICADA_ACTIVA", "EXITOSO")
        c.commit()
    except ValueError as error:
        c.rollback(); return fallo(str(error))
    except (sqlite3.IntegrityError, sqlite3.OperationalError):
        c.rollback(); return fallo("Conflicto de activación; recarga los períodos.", 409)
    return jsonify(ok=True, configuracion=configuracion(c, pid))
