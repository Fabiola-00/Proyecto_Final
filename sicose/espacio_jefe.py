"""Espacio de trabajo global y reportes administrativos con campos explícitos."""
from datetime import date
from flask import Blueprint, render_template, request, jsonify, send_file, redirect
from . import db
from .permissions import role_required
from .formacion import hoy_bolivia

espacio_bp = Blueprint('espacio_jefe', __name__)


def tendencias_mensuales(c, periodo):
    """Conteos por mes dentro del intervalo inclusivo de la Gestión activa."""
    meses=[]
    if periodo:
        inicio=date.fromisoformat(periodo['fecha_inicio'])
        fin=date.fromisoformat(periodo['fecha_fin'])
        mes=inicio.replace(day=1)
        nombres=('Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic')
        while mes<=fin:
            meses.append((mes.strftime('%Y-%m'),f'{nombres[mes.month-1]} {mes.year}'))
            if mes.year==fin.year and mes.month==fin.month: break
            mes=date(mes.year+1,1,1) if mes.month==12 else date(mes.year,mes.month+1,1)
    tendencias=[]
    for titulo,tabla,columna,extra in [('Operaciones','operaciones','fecha_inicio',''),('Cursos registrados','cursos','fecha_inicio',''),('Días con asistencia registrada','asistencias','fecha',''),('Formaciones finalizadas','participaciones_curso','fecha_finalizacion'," AND estado='Finalizado'")]:
        # Tabla/columna provienen de esta lista fija; solo fechas recibidas como parámetros.
        conteo='COUNT(DISTINCT fecha)' if tabla=='asistencias' else 'COUNT(*)'
        valores=dict(c.execute(f'SELECT substr({columna},1,7),{conteo} FROM {tabla} WHERE {columna} BETWEEN ? AND ?'+extra+f' GROUP BY substr({columna},1,7)',(periodo['fecha_inicio'],periodo['fecha_fin'])).fetchall()) if periodo else {}
        filas=[dict(mes=clave,nombre=nombre,valor=valores.get(clave,0)) for clave,nombre in meses]
        mayor=max([f['valor'] for f in filas] or [1]) or 1
        for f in filas: f['alto']=round(f['valor']/mayor*110)
        tendencias.append(dict(titulo=titulo,filas=filas))
    return tendencias


def resumen_panel(c):
    personal = {r['estado']: r['n'] for r in c.execute("SELECT u.estado,COUNT(*) n FROM usuarios u JOIN voluntarios v ON v.usuario_id=u.id WHERE u.estado IN ('ACTIVO','INACTIVO') GROUP BY u.estado")}
    formacion = {r['estado']: r['n'] for r in c.execute('SELECT estado,COUNT(*) n FROM participaciones_curso GROUP BY estado')}
    periodo = c.execute("SELECT * FROM periodos p WHERE estado='ACTIVO' AND NOT EXISTS(SELECT 1 FROM bajas_gestion b WHERE b.periodo_id=p.id) ORDER BY id DESC LIMIT 1").fetchone()
    evaluaciones = {'Finalizadas': 0, 'No cumplidas': 0, 'Pendientes': 0}
    if periodo:
        from .tabla_evaluaciones import datos_gestion
        from .modelo_anual import es_modelo, calcular as calcular_anual
        if es_modelo(c,periodo['id']):
            evaluaciones={'Calificadas':0,'Ceros iniciales oficiales':0,'Pendientes':0}
            for u in c.execute("SELECT a.voluntario_id FROM personas_modelo_anual a JOIN usuarios u ON u.id=a.voluntario_id WHERE a.periodo_id=? AND u.estado='ACTIVO'",(periodo['id'],)).fetchall():
                entradas=calcular_anual(c,u[0],periodo['id'])['entradas']
                evaluaciones['Calificadas']+=sum(e['estado'] in ('CALIFICADA','CALCULADA') and e['valor'] is not None for e in entradas)
                evaluaciones['Ceros iniciales oficiales']+=sum(e['valor'] is not None and e['estado'] not in ('CALIFICADA','CALCULADA') for e in entradas)
                evaluaciones['Pendientes']+=sum(e['valor'] is None for e in entradas)
        for persona in ([] if es_modelo(c,periodo['id']) else datos_gestion(c, periodo['id'])['personas']):
            if persona['estado'] == 'ACTIVO':
                for etiqueta, clave in [('Finalizadas','finalizadas'),('No cumplidas','no_cumplidas'),('Pendientes','pendientes')]:
                    evaluaciones[etiqueta] += persona['resumen'][clave]
    ano = hoy_bolivia().year
    operaciones = c.execute('SELECT COUNT(*) FROM operaciones WHERE fecha_inicio>=? AND fecha_inicio<=?', (f'{ano}-01-01', f'{ano}-12-31')).fetchone()[0]
    def grafico(titulo, alcance, valores):
        return dict(titulo=titulo, alcance=alcance, total=sum(valores.values()), filas=[dict(etiqueta=k,valor=v) for k,v in valores.items()])
    gestion = f"Gestión activa: {periodo['nombre']}." if periodo else 'Sin gestión activa.'
    tendencias=tendencias_mensuales(c,periodo)
    return dict(gestion=gestion, tendencias=tendencias, indicadores=[
        dict(etiqueta='Instructores Voluntarios activos',valor=personal.get('ACTIVO',0),detalle='Directorio global SBRAB'),
        dict(etiqueta='Formaciones finalizadas',valor=formacion.get('Finalizado',0),detalle='Finalizaciones personales de todos los años'),
        dict(etiqueta='Operaciones del año',valor=operaciones,detalle=f'Por fecha de inicio en {ano}'),
        dict(etiqueta='Evaluaciones pendientes',valor=evaluaciones['Pendientes'] if periodo else 'No disponible',detalle='Habilitadas de cuentas activas en la gestión activa')],
        graficos=[grafico('Personal admitido','Estado actual; excluye solicitudes pendientes.',personal),grafico('Formación personal','Participaciones de todos los años.',formacion),grafico('Evaluaciones habilitadas',gestion+' Solo cuentas activas.',evaluaciones)])


@espacio_bp.get('/gestion/evaluaciones-personal')
@role_required('ADMINISTRADOR','JEFE_PERSONAL')
def evaluaciones():
    if request.args.get('historico') != '1': return redirect('/gestion/modelo-anual')
    return render_template('evaluaciones_jefe.html', titulo_pagina='Evaluaciones', nav_activo='evaluaciones_jefe', indicadores=[], periodo_actual=db.periodo_actual(), descripcion='Activa los ítems por gestión y habilita al personal.')


@espacio_bp.get('/gestion/reportes')
@role_required('ADMINISTRADOR','JEFE_PERSONAL')
def reportes():
    return render_template('gestion_reportes.html', titulo_pagina='Reportes',nav_activo='reportes',indicadores=[],periodo_actual=db.periodo_actual(),descripcion='Reportes administrativos de evaluaciones, asistencia, formación y operaciones.')


@espacio_bp.get('/api/reportes/<tipo>.pdf')
@role_required('ADMINISTRADOR','JEFE_PERSONAL')
def reporte(tipo):
    if tipo not in ('formacion','operaciones'):
        return jsonify(error='Reporte no encontrado.'),404
    try:
        if set(request.args) != {'desde','hasta'} or any(len(request.args.getlist(k))!=1 for k in request.args):
            raise ValueError
        desde=date.fromisoformat(request.args['desde']).isoformat()
        hasta=date.fromisoformat(request.args['hasta']).isoformat()
        if hasta<desde: raise ValueError
    except (ValueError,TypeError):
        return jsonify(error='Selecciona un rango de fechas válido.'),400
    c=db.obtener_conexion()
    if tipo=='formacion':
        filas=c.execute("""SELECT u.nombre_completo,v.codigo_instructor,p.nombre_curso,p.tipo_curso,p.entidad_curso,p.fecha_finalizacion,p.puntaje FROM participaciones_curso p JOIN usuarios u ON u.id=p.voluntario_id JOIN voluntarios v ON v.usuario_id=u.id WHERE p.estado='Finalizado' AND p.fecha_finalizacion BETWEEN ? AND ? ORDER BY p.fecha_finalizacion,u.nombre_completo,p.id""",(desde,hasta)).fetchall()
        titulo='Formación personal finalizada'
        subtitulo='Por fecha de finalización personal, inclusive. Excluye participaciones sin finalizar; no convierte pendientes en cero.'
        columnas=['Instructor Voluntario','Código','Curso','Tipo','Entidad','Finalización','Puntos']
        anchos=[135,80,150,100,120,95,45]
    else:
        filas=c.execute("""SELECT o.tipo_evento,o.lugar,o.fecha_inicio,o.fecha_fin,o.institucion_responsable,u.nombre_completo,v.codigo_instructor FROM operaciones o LEFT JOIN participaciones_operacion p ON p.operacion_id=o.id LEFT JOIN usuarios u ON u.id=p.voluntario_id LEFT JOIN voluntarios v ON v.usuario_id=u.id WHERE o.fecha_inicio BETWEEN ? AND ? ORDER BY o.fecha_inicio,o.id,u.nombre_completo""",(desde,hasta)).fetchall()
        titulo='Operaciones y participantes'
        subtitulo='Por fecha de inicio de operación, inclusive. Cada fila representa una participación; se incluyen eventos sin participantes.'
        columnas=['Operación','Lugar','Inicio','Fin','Institución','Participante','Código']
        anchos=[120,100,75,75,140,135,80]
    from .reportes_personal import generar_listado
    archivo=generar_listado(titulo,f'{desde} a {hasta}. '+subtitulo,columnas,[tuple(f) for f in filas],anchos)
    from flask_login import current_user
    db.registrar_auditoria(c,current_user.id,'REPORTE_'+tipo.upper()+'_GENERADO','EXITOSO');c.commit()
    respuesta=send_file(archivo,mimetype='application/pdf',as_attachment=False,download_name=f'{tipo}-{desde}-{hasta}.pdf',max_age=0)
    respuesta.headers['Cache-Control']='private, no-store'
    return respuesta


@espacio_bp.get('/api/reportes/individual/contexto')
@role_required('ADMINISTRADOR','JEFE_PERSONAL')
def contexto_individual():
    from .reporte_individual import gestion_activa
    c=db.obtener_conexion()
    try:
        c.execute('BEGIN')
        periodo=gestion_activa(c)
        personas=[dict(f) for f in c.execute("""SELECT u.id,u.nombre_completo AS nombre,
            v.codigo_instructor AS codigo,u.estado FROM usuarios u
            JOIN voluntarios v ON v.usuario_id=u.id JOIN roles r ON r.id=u.rol_id
            WHERE r.nombre='INSTRUCTOR_VOLUNTARIO' AND u.estado IN ('ACTIVO','INACTIVO')
            ORDER BY u.nombre_completo,u.id""")]
        c.commit();respuesta=jsonify(periodo=periodo,personas=personas)
    except ValueError as error:
        c.rollback();respuesta=jsonify(error=str(error));respuesta.status_code=409
    respuesta.headers['Cache-Control']='private, no-store'
    return respuesta


@espacio_bp.get('/api/reportes/individual/<int:uid>.pdf')
@role_required('ADMINISTRADOR','JEFE_PERSONAL')
def reporte_individual(uid):
    from .reporte_individual import datos_individual,generar_individual
    from flask_login import current_user
    c=db.obtener_conexion()
    try:
        if set(request.args)!={'periodo_id'} or len(request.args.getlist('periodo_id'))!=1:
            return jsonify(error='Selecciona la Gestión activa del reporte.'),400
        pid=int(request.args['periodo_id'])
        c.execute('BEGIN')
        datos=datos_individual(c,uid,pid)
        archivo=generar_individual(datos)
        db.registrar_auditoria(c,current_user.id,f'REPORTE_INDIVIDUAL:PERSONA={uid}:GESTION={pid}','EXITOSO')
        c.commit()
        respuesta=send_file(archivo,mimetype='application/pdf',as_attachment=False,
                            download_name=f'individual-{uid}-gestion-{pid}.pdf',max_age=0)
    except LookupError as error:
        c.rollback();respuesta=jsonify(error=str(error));respuesta.status_code=404
    except (ValueError,TypeError) as error:
        c.rollback();respuesta=jsonify(error=str(error));respuesta.status_code=409
    respuesta.headers['Cache-Control']='private, no-store'
    return respuesta
