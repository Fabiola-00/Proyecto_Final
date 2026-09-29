"""Vistas iniciales protegidas para cada rol del sistema."""

from flask import Blueprint, jsonify, render_template
from flask_login import current_user

from .db import obtener_conexion
from .permissions import role_required

dashboard_bp = Blueprint("dashboard", __name__)


def _periodo_actual(conexion):
    fila = conexion.execute(
        "SELECT nombre FROM periodos WHERE estado = 'ACTIVO' ORDER BY fecha_inicio DESC LIMIT 1"
    ).fetchone()
    return fila["nombre"] if fila else "Sin período activo"


def _renderizar_panel(template, page_title, nav_activo, indicadores, descripcion, **extra):
    conexion = obtener_conexion()
    return render_template(
        template,
        titulo_pagina=page_title,
        nav_activo=nav_activo,
        indicadores=indicadores,
        descripcion=descripcion,
        periodo_actual=_periodo_actual(conexion),
        **extra,
    )


@dashboard_bp.get("/panel/administrador")
@role_required("ADMINISTRADOR")
def administrador():
    conexion = obtener_conexion()
    voluntarios = conexion.execute(
        """SELECT COUNT(*) AS total FROM voluntarios v
           JOIN usuarios u ON u.id = v.usuario_id
           JOIN roles r ON r.id = u.rol_id
           WHERE u.estado = 'ACTIVO' AND r.nombre = 'VOLUNTARIO'"""
    ).fetchone()["total"]
    instructores = conexion.execute(
        """SELECT COUNT(*) AS total FROM instructores i
           JOIN usuarios u ON u.id = i.usuario_id
           JOIN roles r ON r.id = u.rol_id
           WHERE u.estado = 'ACTIVO' AND r.nombre = 'INSTRUCTOR'"""
    ).fetchone()["total"]
    pendientes = conexion.execute(
        "SELECT COUNT(*) AS total FROM usuarios WHERE estado = 'PENDIENTE'"
    ).fetchone()["total"]
    periodos_activos = conexion.execute(
        "SELECT COUNT(*) AS total FROM periodos WHERE estado = 'ACTIVO'"
    ).fetchone()["total"]
    return _renderizar_panel(
        "dashboard_administrador.html",
        "Panel de administración",
        "inicio",
        [
            {"etiqueta": "Voluntarios activos", "valor": voluntarios, "detalle": "Perfiles registrados"},
            {"etiqueta": "Instructores activos", "valor": instructores, "detalle": "Perfiles registrados"},
            {"etiqueta": "Usuarios pendientes", "valor": pendientes, "detalle": "Cuentas sin activar"},
            {"etiqueta": "Períodos activos", "valor": periodos_activos, "detalle": "Ciclos vigentes"},
        ],
        "Resumen general construido con los datos registrados en SICOSE.",
    )


@dashboard_bp.get("/panel/instructor")
@role_required("INSTRUCTOR")
def instructor():
    conexion = obtener_conexion()
    voluntarios = conexion.execute(
        """SELECT COUNT(*) AS total FROM voluntarios v
           JOIN usuarios u ON u.id = v.usuario_id
           WHERE v.instructor_id = ? AND u.estado = 'ACTIVO'""",
        (current_user.id,),
    ).fetchone()["total"]
    asignaciones_pendientes = conexion.execute(
        """SELECT COUNT(*) AS total FROM asignaciones_evaluacion a
           JOIN voluntarios v ON v.usuario_id = a.voluntario_id
           JOIN usuarios u ON u.id = v.usuario_id
           WHERE v.instructor_id = ? AND u.estado = 'ACTIVO'
             AND a.estado IN ('HABILITADA', 'EN_PROGRESO')""",
        (current_user.id,),
    ).fetchone()["total"]
    return _renderizar_panel(
        "dashboard_instructor.html",
        "Panel del instructor",
        "inicio",
        [
            {"etiqueta": "Voluntarios asignados", "valor": voluntarios, "detalle": "Perfiles activos"},
            {"etiqueta": "Evaluaciones pendientes", "valor": asignaciones_pendientes, "detalle": "Habilitadas o en progreso"},
        ],
        "Seguimiento de tus asignaciones y voluntarios autorizados.",
    )


@dashboard_bp.get("/panel/voluntario")
@role_required("VOLUNTARIO")
def voluntario():
    conexion = obtener_conexion()
    filas = conexion.execute(
        """SELECT COUNT(*) AS total,
                  SUM(CASE WHEN estado = 'COMPLETADA' THEN 1 ELSE 0 END) AS completadas
           FROM asignaciones_evaluacion WHERE voluntario_id = ?""",
        (current_user.id,),
    ).fetchone()
    total = filas["total"] or 0
    completadas = filas["completadas"] or 0
    capacitaciones = conexion.execute(
        "SELECT COUNT(*) AS total FROM capacitaciones WHERE voluntario_id = ?",
        (current_user.id,),
    ).fetchone()["total"]
    evaluaciones = conexion.execute(
        """SELECT e.nombre AS evaluacion,p.nombre AS periodo,a.estado
           FROM asignaciones_evaluacion a JOIN evaluaciones e ON e.id=a.evaluacion_id
           JOIN periodos p ON p.id=a.periodo_id WHERE a.voluntario_id=?
           ORDER BY p.fecha_inicio DESC,e.nombre""", (current_user.id,)
    ).fetchall()
    return _renderizar_panel(
        "dashboard_voluntario.html",
        "Mi seguimiento",
        "inicio",
        [
            {"etiqueta": "Evaluaciones asignadas", "valor": total, "detalle": "En todos los períodos"},
            {"etiqueta": "Completadas", "valor": completadas, "detalle": "Según el estado registrado"},
            {"etiqueta": "Pendientes", "valor": total - completadas, "detalle": "Aún no completadas"},
            {"etiqueta": "Capacitaciones", "valor": capacitaciones, "detalle": "Registros en tu perfil"},
        ],
        "Consulta tu avance personal y la información asociada a tu cuenta.",
        evaluaciones_resumen=[dict(fila) for fila in evaluaciones],
    )


@dashboard_bp.get("/api/admin/estado")
@role_required("ADMINISTRADOR")
def estado_admin():
    return jsonify(estado="autorizado")
