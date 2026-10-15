"""Vistas iniciales protegidas para cada rol del sistema."""

from flask import Blueprint, jsonify, render_template
from flask_login import current_user

from .db import obtener_conexion, periodo_actual
from .permissions import role_required

dashboard_bp = Blueprint("dashboard", __name__)


def _renderizar_panel(template, page_title, nav_activo, indicadores, descripcion, **extra):
    conexion = obtener_conexion()
    return render_template(
        template,
        titulo_pagina=page_title,
        nav_activo=nav_activo,
        indicadores=indicadores,
        descripcion=descripcion,
        periodo_actual=periodo_actual(),
        **extra,
    )


@dashboard_bp.get("/panel/administrador")
@role_required("ADMINISTRADOR")
def administrador():
    conexion = obtener_conexion()
    perfiles_voluntarios = conexion.execute(
        """SELECT u.id, u.nombre_completo AS nombre, u.estado,
                  (u.foto_perfil IS NOT NULL) AS tiene_foto
           FROM voluntarios v JOIN usuarios u ON u.id=v.usuario_id
           ORDER BY (u.estado='ACTIVO') DESC, u.nombre_completo, u.id"""
    ).fetchall()
    perfiles_instructores = conexion.execute(
        """SELECT u.id, u.nombre_completo AS nombre, u.estado,
                  (u.foto_perfil IS NOT NULL) AS tiene_foto
           FROM instructores i JOIN usuarios u ON u.id=i.usuario_id
           ORDER BY (u.estado='ACTIVO') DESC, u.nombre_completo, u.id"""
    ).fetchall()
    voluntarios = conexion.execute(
        """SELECT COUNT(*) AS total FROM voluntarios v
           JOIN usuarios u ON u.id = v.usuario_id
           JOIN roles r ON r.id = u.rol_id
           WHERE u.estado = 'ACTIVO' AND r.nombre = 'INSTRUCTOR_VOLUNTARIO'"""
    ).fetchone()["total"]
    instructores = conexion.execute(
        """SELECT COUNT(*) AS total FROM instructores i
           JOIN usuarios u ON u.id = i.usuario_id
           JOIN roles r ON r.id = u.rol_id
           WHERE u.estado = 'ACTIVO' AND r.nombre = 'JEFE_PERSONAL'"""
    ).fetchone()["total"]
    pendientes = conexion.execute(
        "SELECT COUNT(*) AS total FROM usuarios WHERE estado = 'PENDIENTE'"
    ).fetchone()["total"]
    periodos_activos = conexion.execute(
        "SELECT COUNT(*) AS total FROM periodos WHERE estado = 'ACTIVO' AND NOT EXISTS(SELECT 1 FROM bajas_gestion b WHERE b.periodo_id=periodos.id)"
    ).fetchone()["total"]
    return _renderizar_panel(
        "dashboard_administrador.html",
        "Panel de administración",
        "inicio",
        [
            {"etiqueta": "Instructores Voluntarios activos", "valor": voluntarios, "detalle": "Perfiles registrados"},
            {"etiqueta": "Jefes de Personal activos", "valor": instructores, "detalle": "Perfiles registrados"},
            {"etiqueta": "Usuarios pendientes", "valor": pendientes, "detalle": "Cuentas sin activar"},
            {"etiqueta": "Períodos activos", "valor": periodos_activos, "detalle": "Ciclos vigentes"},
        ],
        "Resumen general construido con los datos registrados en SICOSE.",
        perfiles_voluntarios=[dict(fila) for fila in perfiles_voluntarios],
        perfiles_instructores=[dict(fila) for fila in perfiles_instructores],
    )


@dashboard_bp.get("/panel/instructor")
@dashboard_bp.get("/panel/jefe-personal")
@role_required("JEFE_PERSONAL")
def jefe_personal():
    conexion = obtener_conexion()
    from .espacio_jefe import resumen_panel
    resumen = resumen_panel(conexion)
    return _renderizar_panel(
        "dashboard_jefe_personal.html", "Panel del Jefe de Personal", "inicio",
        resumen['indicadores'], "Resumen global del personal, la formación y las evaluaciones de SBRAB.",
        graficos=resumen['graficos'], gestion_panel=resumen['gestion'])



@dashboard_bp.get("/panel/voluntario")
@dashboard_bp.get("/panel/instructor-voluntario")
@role_required("INSTRUCTOR_VOLUNTARIO")
def instructor_voluntario():
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
    cursos_asignados = conexion.execute("SELECT COUNT(*) FROM participaciones_curso WHERE voluntario_id=?", (current_user.id,)).fetchone()[0]
    cursos_finalizados = conexion.execute("SELECT COUNT(*) FROM participaciones_curso WHERE voluntario_id=? AND estado='Finalizado'", (current_user.id,)).fetchone()[0]
    evaluaciones = conexion.execute(
        """SELECT e.nombre AS evaluacion,p.nombre AS periodo,a.estado
           FROM asignaciones_evaluacion a JOIN evaluaciones e ON e.id=a.evaluacion_id
           JOIN periodos p ON p.id=a.periodo_id WHERE a.voluntario_id=?
           ORDER BY p.fecha_inicio DESC,e.nombre""", (current_user.id,)
    ).fetchall()
    return _renderizar_panel(
        "dashboard_instructor_voluntario.html",
        "Mi seguimiento como Instructor Voluntario",
        "inicio",
        [
            {"etiqueta": "Evaluaciones asignadas", "valor": total, "detalle": "En todos los períodos"},
            {"etiqueta": "Completadas", "valor": completadas, "detalle": "Según el estado registrado"},
            {"etiqueta": "Pendientes", "valor": total - completadas, "detalle": "Aún no completadas"},
            {"etiqueta": "Formación histórica", "valor": capacitaciones, "detalle": "Registros anteriores de tu perfil"},
            {"etiqueta": "Cursos asignados", "valor": cursos_asignados, "detalle": f"{cursos_finalizados} finalizados individualmente"},
        ],
        "Consulta tu avance personal y la información asociada a tu cuenta de Instructor Voluntario.",
        evaluaciones_resumen=[dict(fila) for fila in evaluaciones],
    )


@dashboard_bp.get("/api/admin/estado")
@role_required("ADMINISTRADOR")
def estado_admin():
    return jsonify(estado="autorizado")
