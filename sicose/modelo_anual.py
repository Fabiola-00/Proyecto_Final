"""Cinco entradas anuales; ceros oficiales, operaciones auditadas y modelo pendiente."""
import json
import re
import sqlite3
from datetime import date
from decimal import Decimal
from fractions import Fraction
from flask import Blueprint, jsonify, request, render_template
from flask_login import current_user
from . import db
from .permissions import role_required
from .gestiones import retirada, estado_evaluaciones

anual_bp=Blueprint('modelo_anual',__name__)
FUENTES=('FISICA_1','FISICA_2','DESEMPENO_JEFE','DESEMPENO_COMANDANTE','ACADEMICA')


def evento(c,pid,accion,razon,anterior,nuevo):
    c.execute('INSERT INTO eventos_modelo_anual(periodo_id,accion,anterior_json,nuevo_json,motivo,actor_id,actor_nombre,registrada_en) VALUES (?,?,?,?,?,?,?,?)',(pid,accion,serializar(anterior),serializar(nuevo),razon,current_user.id,current_user.nombre,db._ahora_utc()))


def es_modelo(c,pid):
    return c.execute('SELECT 1 FROM modelos_anuales WHERE periodo_id=?',(pid,)).fetchone() is not None


def serializar(v):
    return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))


def puntos(valor):
    if isinstance(valor,bool) or not isinstance(valor,(str,int,float)) or not re.fullmatch(r'[0-9]{1,3}(?:\.[0-9]{1,2})?',str(valor)):
        raise ValueError('Nota de 0 a 100 con hasta dos decimales.')
    numero=Decimal(str(valor))
    if not numero.is_finite() or not 0<=numero<=100:raise ValueError('Nota de 0 a 100.')
    return int(numero*100)


def numero(cent):
    if cent is None:return None
    return format(Decimal(cent.numerator)/Decimal(cent.denominator)/100,'f') if isinstance(cent,Fraction) else f'{cent//100}.{cent%100:02d}'


def observacion_calificacion(datos):
    valor = datos.get('motivo', '')
    if not isinstance(valor, str) or len(valor.strip()) > 2000:
        raise ValueError('Observación inválida, máximo 2000 caracteres.')
    return valor.strip()


def motivo(datos):
    valor=datos.get('motivo')
    if not isinstance(valor,str) or not 1<=len(valor.strip())<=2000:raise ValueError('Motivo obligatorio, máximo 2000 caracteres.')
    return valor.strip()


def periodo(c,pid,activo=False):
    p=c.execute('SELECT p.*,m.revision,m.formato,m.iniciada_en FROM periodos p JOIN modelos_anuales m ON m.periodo_id=p.id WHERE p.id=?',(pid,)).fetchone()
    if p is None:raise LookupError('Gestión del modelo anual no encontrada.')
    if activo and (retirada(c,pid) or p['estado']!='ACTIVO'):raise ValueError('Requiere una Gestión activa y no retirada.')
    return {**dict(p),'retirada':retirada(c,pid)}


def persona(c,pid,uid):
    from .tabla_evaluaciones import habilitada
    if not c.execute("SELECT 1 FROM usuarios u JOIN personas_modelo_anual p ON p.voluntario_id=u.id WHERE p.periodo_id=? AND u.id=? AND u.estado='ACTIVO'",(pid,uid)).fetchone():
        raise ValueError('Persona no inscrita o cuenta inactiva.')
    return habilitada


def inscribir(c,pid,razon):
    nuevos=0
    for fila in c.execute("SELECT v.usuario_id FROM voluntarios v JOIN usuarios u ON u.id=v.usuario_id JOIN roles r ON r.id=u.rol_id WHERE u.estado='ACTIVO' AND r.nombre='INSTRUCTOR_VOLUNTARIO' ORDER BY u.id").fetchall():
        uid=fila[0]
        if c.execute('SELECT 1 FROM personas_modelo_anual WHERE periodo_id=? AND voluntario_id=?',(pid,uid)).fetchone():continue
        ahora=db._ahora_utc()
        c.execute('INSERT INTO personas_modelo_anual VALUES (?,?,?,?)',(pid,uid,current_user.id,ahora))
        for fuente in FUENTES:
            c.execute("INSERT INTO notas_modelo_anual(periodo_id,voluntario_id,fuente,puntos_centesimas,origen,evidencia_json,motivo,actor_id,actor_nombre,registrada_en) VALUES (?,?,?,0,'CERO_INICIAL','{}',?,?,?,?)",(pid,uid,fuente,'Cero oficial de inicio de Gestión: '+razon,current_user.id,current_user.nombre,ahora))
            c.execute('INSERT INTO habilitaciones_operativas(voluntario_id,periodo_id,clave,habilitada,registrada_por,registrada_en) VALUES (?,?,?,1,?,?)',(uid,pid,fuente,current_user.id,ahora))
        nuevos+=1
    return nuevos


def calcular(c,uid,pid):
    p=periodo(c,pid)
    if not c.execute('SELECT 1 FROM personas_modelo_anual WHERE periodo_id=? AND voluntario_id=?',(pid,uid)).fetchone():
        return {'regla':'CINCO_ENTRADAS_V3','estado':'FUERA_DEL_MODELO','resultado_conjunto':None,'faltantes':['SIN_INSCRIPCION'],'bloqueos':[], 'academica':{'valor':None,'detalle':[]},'fisica':None,'desempeno':None,'fuentes':{},'provisional':True}
    from .tabla_evaluaciones import habilitada
    notas={f:dict(c.execute('SELECT * FROM notas_modelo_anual WHERE periodo_id=? AND voluntario_id=? AND fuente=? ORDER BY id DESC LIMIT 1',(pid,uid,f)).fetchone()) for f in FUENTES}
    bloqueos=[f for f in FUENTES if not habilitada(c,uid,pid,f)]
    cursos=[dict(f) for f in c.execute("SELECT id AS participacion_id,nombre_curso,puntaje,fecha_finalizacion,revision FROM participaciones_curso WHERE voluntario_id=? AND estado='Finalizado' AND fecha_finalizacion BETWEEN ? AND ? ORDER BY fecha_finalizacion,id",(uid,p['fecha_inicio'],p['fecha_fin']))]
    ops=[dict(f) for f in c.execute('''SELECT n.*,COALESCE(o.tipo_operativo,o.tipo_evento) AS tipo_evento,o.fecha_inicio FROM notas_operacion_anual n JOIN operaciones o ON o.id=n.operacion_id
          WHERE NOT EXISTS(SELECT 1 FROM retiros_operacion_vigentes r WHERE r.operacion_id=n.operacion_id AND r.voluntario_id=n.voluntario_id) AND n.periodo_id=? AND n.voluntario_id=? AND o.fecha_inicio BETWEEN ? AND ? AND NOT EXISTS(SELECT 1 FROM notas_operacion_anual x WHERE x.anterior_id=n.id) ORDER BY n.operacion_id''',(pid,uid,p['fecha_inicio'],p['fecha_fin']))]
    suma_cursos=sum(f['puntaje']*100 for f in cursos)
    promedio_ops=Fraction(sum(f['puntos_centesimas'] for f in ops),len(ops)) if ops else 0
    from .asistencias import PROYECCION, totales
    asistencia_academica=totales(f[0] for f in c.execute(f'SELECT {PROYECCION} FROM asistencias a WHERE a.voluntario_id=? AND a.fecha BETWEEN ? AND ?',(uid,p['fecha_inicio'],p['fecha_fin'])))
    nota_asistencia=Decimal(str(asistencia_academica['porcentaje'] or 0))
    nota_cursos=min(10000,suma_cursos)
    suma_componentes=Fraction(nota_asistencia*100)+nota_cursos+promedio_ops
    academia=(suma_componentes/3 if suma_componentes else 0) if 'ACADEMICA' not in bloqueos else None
    def media(a,b):return None if a in bloqueos or b in bloqueos else Fraction(notas[a]['puntos_centesimas']+notas[b]['puntos_centesimas'],2)
    fisica=media('FISICA_1','FISICA_2');desempeno=media('DESEMPENO_JEFE','DESEMPENO_COMANDANTE')
    def estado_componente(a,b):
        iniciales=sum(notas[f]['origen']=='CERO_INICIAL' for f in (a,b))
        return 'CERO_INICIAL_OFICIAL' if iniciales==2 else 'PARCIAL_CON_CERO_INICIAL_OFICIAL' if iniciales else 'CALIFICADA'
    from .pruebas_actuales import estado as estado_prueba, intento as intento_prueba
    from .instrumentos_actuales import firma as firma_prueba
    psico_estados=[]
    for clave in ('GSE','MINIIPIP','NASATLX'):
        a=estado_prueba(c,pid,clave);i=intento_prueba(c,pid,uid,clave)
        completa=bool(i and i['finalizada_en'] and i['firma_formulario']==firma_prueba(clave))
        psico_estados.append('COMPLETADA' if completa and a['activa'] and a['revisada'] else ('DESHABILITADA' if not a['activa'] else 'PENDIENTE_PRUEBA'))
    faltantes_psico=[f'PSICOMETRICA_{i+1}' for i,estado in enumerate(psico_estados) if estado!='COMPLETADA']
    entradas=[{'clave':k,'nombre':n,'valor':numero(v),'estado':'DESHABILITADA' if v is None and not k.startswith('PSICO') else estado} for k,n,v,estado in (
        ('FISICA','Física',fisica,estado_componente('FISICA_1','FISICA_2')),
        ('DESEMPENO','Desempeño',desempeno,estado_componente('DESEMPENO_JEFE','DESEMPENO_COMANDANTE')),
        ('ACADEMICA','Académica',academia,'CALCULADA' if cursos or ops or asistencia_academica['computables'] else 'CERO_INICIAL_OFICIAL'),
        ('PSICOMETRICA_1','GSE · Autoeficacia',None,psico_estados[0]),('PSICOMETRICA_2','Mini-IPIP · Personalidad',None,psico_estados[1]),('PSICOMETRICA_3','NASA-TLX · Carga de trabajo',None,psico_estados[2]))]
    return {'regla':'CINCO_ENTRADAS_V3','estado':'INCOMPLETO' if faltantes_psico or bloqueos else 'COMPLETO','resultado_conjunto':None,'fisica':numero(fisica),'desempeno':numero(desempeno),
        'academica':{'valor':float(numero(academia)) if academia is not None else None,'puntos_sin_tope':float(numero(suma_componentes)), 'criterio_academica':'PROMEDIO_ASISTENCIA_CURSOS_OPERACIONES_V1','aporte_asistencia':float(nota_asistencia),'aporte_cursos':nota_cursos/100,'cursos_sin_tope':suma_cursos/100,'asistencia':asistencia_academica,'tope':100,'detalle':cursos,'operaciones':ops,'estado_operaciones':'CALIFICADAS' if ops else 'PENDIENTE','aporte_operaciones':numero(promedio_ops),'criterio_operaciones':'PROMEDIO_CALIFICADAS','operaciones_calificadas':len(ops)},
        'entradas':entradas,'fuentes':notas,'faltantes':faltantes_psico+bloqueos,'bloqueos':bloqueos,'provisional':True,
        'modelo':{'estado':'ENTRENADO_EXPERIMENTAL','recomendacion_ascenso':None,'recomendacion_operaciones':None,'listo_para_inferencia':not faltantes_psico and not bloqueos}}


def evidencia(c,pid,uid):
    return {'inscripcion':dict(c.execute('SELECT * FROM personas_modelo_anual WHERE periodo_id=? AND voluntario_id=?',(pid,uid)).fetchone()),
        'notas':[dict(f) for f in c.execute('SELECT * FROM notas_modelo_anual WHERE periodo_id=? AND voluntario_id=? ORDER BY id',(pid,uid))],
        'operaciones':[dict(f) for f in c.execute('SELECT * FROM notas_operacion_anual WHERE periodo_id=? AND voluntario_id=? ORDER BY id',(pid,uid))]}


@anual_bp.after_request
def privada(r):
    r.headers['Cache-Control']='private, no-store';return r


@anual_bp.get('/gestion/modelo-anual')
@role_required('ADMINISTRADOR','JEFE_PERSONAL')
def pagina():
    return render_template('modelo_anual.html',titulo_pagina='Evaluaciones',nav_activo='evaluaciones_jefe',indicadores=[],periodo_actual=db.periodo_actual(),descripcion='Evaluación institucional: Físico, Desempeño y Académica, con sus respaldos de formación, operaciones y asistencia.')


@anual_bp.get('/gestion/pruebas-recomendacion')
@role_required('ADMINISTRADOR','JEFE_PERSONAL','INSTRUCTOR_VOLUNTARIO')
def pagina_pruebas():
    propia = current_user.rol == 'INSTRUCTOR_VOLUNTARIO'
    return render_template('pruebas_recomendacion.html',titulo_pagina='Pruebas y Recomendación',
        nav_activo='pruebas_recomendacion',indicadores=[],periodo_actual=db.periodo_actual(),
        propia=propia,descripcion='Responde tus pruebas habilitadas y consulta su estado.' if propia else 'Administra NASA-TLX, GSE y Mini-IPIP, consulta resultados y revisa las propuestas de orientación del modelo.')


@anual_bp.get('/api/modelo-anual/gestiones')
@anual_bp.post('/api/modelo-anual/gestiones')
@role_required('ADMINISTRADOR','JEFE_PERSONAL')
def gestiones():
    c=db.obtener_conexion()
    if request.method=='GET':
        return jsonify(periodos=[{**dict(f),'retirada':retirada(c,f['id'])} for f in c.execute('SELECT p.*,m.revision,m.iniciada_en FROM periodos p JOIN modelos_anuales m ON m.periodo_id=p.id ORDER BY p.fecha_inicio DESC,p.id DESC')])
    d=request.get_json(silent=True)
    try:
        if not isinstance(d,dict) or set(d)!={'nombre','fecha_inicio','fecha_fin'}:raise ValueError('Nombre, inicio y fin requeridos.')
        if not isinstance(d['nombre'],str) or not 2<=len(d['nombre'].strip())<=120:raise ValueError('Nombre de 2 a 120 caracteres.')
        for k in ('fecha_inicio','fecha_fin'):
            if not isinstance(d[k],str) or date.fromisoformat(d[k]).isoformat()!=d[k]:raise ValueError('Fechas ISO válidas requeridas.')
        if d['fecha_fin']<d['fecha_inicio']:raise ValueError('El fin no puede preceder al inicio.')
        c.execute('BEGIN IMMEDIATE')
        # Cada evidencia temporal se imputa a un solo período del modelo nuevo.
        if c.execute('SELECT 1 FROM modelos_anuales m JOIN periodos p ON p.id=m.periodo_id WHERE p.fecha_inicio<=? AND p.fecha_fin>=? AND NOT EXISTS(SELECT 1 FROM bajas_gestion b WHERE b.periodo_id=p.id)',(d['fecha_fin'],d['fecha_inicio'])).fetchone():raise ValueError('El rango se superpone con otra Gestión del modelo nuevo.')
        pid=c.execute("INSERT INTO periodos(nombre,fecha_inicio,fecha_fin,estado,creado_por) VALUES (?,?,?,'BORRADOR',?)",(d['nombre'].strip(),d['fecha_inicio'],d['fecha_fin'],current_user.id)).lastrowid
        c.execute('INSERT INTO modelos_anuales(periodo_id,creada_por,creada_en) VALUES (?,?,?)',(pid,current_user.id,db._ahora_utc()))
        evento(c,pid,'CREAR','Creación de borrador',{},d)
        db.registrar_auditoria(c,current_user.id,'GESTION_MODELO_ANUAL_CREADA','EXITOSO');c.commit();return jsonify(ok=True,id=pid),201
    except (ValueError,TypeError) as e:c.rollback();return jsonify(error=str(e)),400
    except sqlite3.IntegrityError:c.rollback();return jsonify(error='Nombre o intervalo en conflicto.'),409


@anual_bp.post('/api/modelo-anual/gestiones/<int:pid>/iniciar')
@anual_bp.post('/api/modelo-anual/gestiones/<int:pid>/inscribir')
@role_required('ADMINISTRADOR','JEFE_PERSONAL')
def iniciar(pid):
    c=db.obtener_conexion();d=request.get_json(silent=True)
    try:
        if not isinstance(d,dict) or set(d)!={'revision','motivo'} or type(d['revision']) is not int:raise ValueError('Revisión y motivo requeridos.')
        razon=motivo(d);c.execute('BEGIN IMMEDIATE');p=periodo(c,pid)
        inscripcion=request.path.endswith('/inscribir')
        if p['retirada'] or d['revision']!=p['revision'] or p['estado']!=('ACTIVO' if inscripcion else 'BORRADOR'):raise ValueError('Estado o revisión desactualizados.')
        if not inscripcion:
            if c.execute("SELECT 1 FROM periodos p WHERE estado='ACTIVO' AND id!=? AND NOT EXISTS(SELECT 1 FROM bajas_gestion b WHERE b.periodo_id=p.id)",(pid,)).fetchone():raise ValueError('Ya existe otra Gestión activa; ciérrala explícitamente.')
            c.execute("UPDATE periodos SET estado='ACTIVO' WHERE id=?",(pid,))
            c.execute('UPDATE modelos_anuales SET revision=revision+1,iniciada_por=?,iniciada_en=? WHERE periodo_id=?',(current_user.id,db._ahora_utc(),pid))
        nuevos=inscribir(c,pid,razon);evento(c,pid,'INSCRIBIR' if inscripcion else 'INICIAR',razon,p,{'estado':'ACTIVO','nuevas_personas':nuevos});db.registrar_auditoria(c,current_user.id,'GESTION_MODELO_ANUAL_INICIADA' if not inscripcion else 'PERSONAS_MODELO_ANUAL_INSCRITAS','EXITOSO');c.commit();return jsonify(ok=True,inscritos=nuevos),201
    except LookupError as e:c.rollback();return jsonify(error=str(e)),404
    except ValueError as e:c.rollback();return jsonify(error=str(e)),409
    except (sqlite3.IntegrityError,sqlite3.OperationalError):c.rollback();return jsonify(error='Conflicto concurrente. Recarga.'),409


@anual_bp.get('/api/modelo-anual/gestiones/<int:pid>')
@role_required('ADMINISTRADOR','JEFE_PERSONAL')
def consultar(pid):
    c=db.obtener_conexion()
    try:
        c.execute('BEGIN');p=periodo(c,pid)
        from .calculos_5b import calcular as resultado
        personas=[{**dict(u),'calculo':resultado(c,u['id'],pid)} for u in c.execute('SELECT u.id,u.nombre_completo AS nombre,u.estado FROM personas_modelo_anual a JOIN usuarios u ON u.id=a.voluntario_id WHERE a.periodo_id=? ORDER BY u.nombre_completo,u.id',(pid,)).fetchall()]
        from .cierres_5b import resumen
        r={'periodo':p,'personas':personas,'cierres':resumen(c,pid),'activaciones':estado_evaluaciones(c,pid),'historial_gestion':[dict(f) for f in c.execute('SELECT * FROM eventos_modelo_anual WHERE periodo_id=? ORDER BY id',(pid,))]};c.commit();return jsonify(r)
    except LookupError as e:c.rollback();return jsonify(error=str(e)),404
    except ValueError as e:c.rollback();return jsonify(error=str(e)),409


@anual_bp.get('/api/modelo-anual/gestiones/<int:pid>/personas/<int:uid>')
@anual_bp.post('/api/modelo-anual/gestiones/<int:pid>/personas/<int:uid>')
@role_required('ADMINISTRADOR','JEFE_PERSONAL')
def calificar(pid,uid):
    c=db.obtener_conexion()
    try:
        if request.method=='GET':
            c.execute('BEGIN');p=periodo(c,pid)
            if not c.execute('SELECT 1 FROM personas_modelo_anual WHERE periodo_id=? AND voluntario_id=?',(pid,uid)).fetchone():raise LookupError('Persona no inscrita.')
            from .calculos_5b import calcular as resultado
            from .fisicas import vigente
            ops=[dict(f) for f in c.execute('SELECT o.*,EXISTS(SELECT 1 FROM bajas_operacion b WHERE b.operacion_id=o.id) AS baja,EXISTS(SELECT 1 FROM retiros_operacion_vigentes r WHERE r.operacion_id=o.id AND r.voluntario_id=x.voluntario_id) AS retirada FROM operaciones o JOIN participaciones_operacion x ON x.operacion_id=o.id WHERE x.voluntario_id=? AND o.fecha_inicio<=? AND COALESCE(o.fecha_fin,o.fecha_inicio)>=? ORDER BY o.fecha_inicio,o.id',(uid,p['fecha_fin'],p['fecha_inicio']))]
            cursos=[dict(f) for f in c.execute('''SELECT pc.id,pc.curso_id,pc.nombre_curso,pc.entidad_curso,pc.tipo_curso,
                       pc.inicio_curso,pc.fin_curso,pc.estado,pc.puntaje,pc.fecha_finalizacion,
                       EXISTS(SELECT 1 FROM retiros_curso r WHERE r.participacion_id=pc.id) AS retirada
                       FROM participaciones_curso pc WHERE pc.voluntario_id=?
                       AND ((pc.inicio_curso<=? AND pc.fin_curso>=?) OR pc.fecha_finalizacion BETWEEN ? AND ?)
                       ORDER BY pc.inicio_curso,pc.id''',(uid,p['fecha_fin'],p['fecha_inicio'],p['fecha_inicio'],p['fecha_fin']))]
            from .asistencias import PROYECCION, totales
            asistencia=totales(f['estado'] for f in c.execute(f'SELECT {PROYECCION} AS estado FROM asistencias a WHERE a.voluntario_id=? AND a.fecha BETWEEN ? AND ?',(uid,p['fecha_inicio'],p['fecha_fin'])))
            from .tabla_evaluaciones import habilitacion_personal
            r={'habilitaciones':{f:habilitacion_personal(c,uid,pid,f) for f in FUENTES},'periodo':p,'calculo':resultado(c,uid,pid),'historial':evidencia(c,pid,uid),'operaciones':ops,'cursos':cursos,'asistencia':asistencia,'fisicas':{f:vigente(c,pid,f,uid) for f in ('FISICA_1','FISICA_2')}};c.commit();return jsonify(r)
        d=request.get_json(silent=True)
        if not isinstance(d,dict) or set(d)-{'motivo'}!={'fuente','nota','anterior_id','evidencia'}:raise ValueError('Fuente, nota, versión anterior y evidencia requeridos.')
        if type(d['anterior_id']) is not int or not isinstance(d['evidencia'],dict):raise ValueError('Versión o evidencia inválida.')
        fuente=d['fuente']
        if fuente not in FUENTES[:-1]:raise ValueError('Académica se calcula; psicometría no está autorizada.')
        valor=puntos(d['nota']);razon=observacion_calificacion(d);c.execute('BEGIN IMMEDIATE');p=periodo(c,pid,True);habilitada=persona(c,pid,uid)
        if not habilitada(c,uid,pid,fuente):raise ValueError('Fuente deshabilitada.')
        anterior=c.execute('SELECT id FROM notas_modelo_anual WHERE periodo_id=? AND voluntario_id=? AND fuente=? ORDER BY id DESC LIMIT 1',(pid,uid,fuente)).fetchone()
        if not anterior or anterior[0]!=d['anterior_id']:raise ValueError('La nota cambió; recarga.')
        origen='MANUAL';ev=d['evidencia']
        if fuente.startswith('FISICA_'):
            if set(ev)=={'estado'}:
                if ev['estado'] not in ('CUMPLIDA','NO_CUMPLIDA') or (ev['estado']=='NO_CUMPLIDA' and valor!=0):
                    raise ValueError('Resultado físico inválido; No cumplida requiere cero.')
                origen=ev['estado']
            else:
                # Compatibilidad de resultados con programación histórica.
                from .fisicas import validar_resultado
                validar_resultado(c,uid,pid,fuente,ev,Decimal(valor)/100);origen=ev['estado']
        elif fuente=='DESEMPENO_COMANDANTE':
            if set(ev)!={'comandante_nombre'} or not isinstance(ev['comandante_nombre'],str) or not 1<=len(ev['comandante_nombre'].strip())<=160:raise ValueError('Nombre del Comandante externo obligatorio.')
        elif ev:raise ValueError('Evidencia no válida para esta fuente.')
        c.execute('INSERT INTO notas_modelo_anual(periodo_id,voluntario_id,fuente,puntos_centesimas,origen,anterior_id,evidencia_json,motivo,actor_id,actor_nombre,registrada_en) VALUES (?,?,?,?,?,?,?,?,?,?,?)',(pid,uid,fuente,valor,origen,anterior[0],serializar(ev),razon,current_user.id,current_user.nombre,db._ahora_utc()))
        db.registrar_auditoria(c,current_user.id,'NOTA_MODELO_ANUAL_REGISTRADA','EXITOSO');c.commit();return jsonify(ok=True),201
    except LookupError as e:c.rollback();return jsonify(error=str(e)),404
    except (ValueError,KeyError,TypeError) as e:c.rollback();return jsonify(error=str(e)),409 if request.method=='POST' else 400
    except (sqlite3.IntegrityError,sqlite3.OperationalError):c.rollback();return jsonify(error='Revisión concurrente. Recarga.'),409


@anual_bp.post('/api/modelo-anual/gestiones/<int:pid>/personas/<int:uid>/operaciones/<int:oid>')
@role_required('ADMINISTRADOR','JEFE_PERSONAL')
def operacion(pid,uid,oid):
    c=db.obtener_conexion();d=request.get_json(silent=True)
    try:
        if not isinstance(d,dict) or set(d)-{'motivo'}!={'nota','anterior_id'} or (d['anterior_id'] is not None and type(d['anterior_id']) is not int):raise ValueError('Nota y versión anterior requeridas.')
        valor=puntos(d['nota']);razon=observacion_calificacion(d);c.execute('BEGIN IMMEDIATE');p=periodo(c,pid,True);habilitada=persona(c,pid,uid)
        from .operaciones import baja
        if baja(c,oid):raise ValueError('La operación está dada de baja; conserva sus calificaciones históricas.')
        if c.execute('SELECT 1 FROM retiros_operacion_vigentes WHERE operacion_id=? AND voluntario_id=?',(oid,uid)).fetchone():raise ValueError('La participación fue retirada; conserva sus notas históricas.')
        if not habilitada(c,uid,pid,'ACADEMICA'):raise ValueError('Académica deshabilitada.')
        o=c.execute('SELECT o.*,EXISTS(SELECT 1 FROM bajas_operacion b WHERE b.operacion_id=o.id) AS baja,EXISTS(SELECT 1 FROM retiros_operacion_vigentes r WHERE r.operacion_id=o.id AND r.voluntario_id=x.voluntario_id) AS retirada FROM operaciones o JOIN participaciones_operacion x ON x.operacion_id=o.id WHERE o.id=? AND x.voluntario_id=?',(oid,uid)).fetchone()
        if not o or not p['fecha_inicio']<=o['fecha_inicio']<=p['fecha_fin']:raise ValueError('Participación fuera del período o no asignada.')
        anterior=c.execute('SELECT id FROM notas_operacion_anual WHERE periodo_id=? AND voluntario_id=? AND operacion_id=? ORDER BY id DESC LIMIT 1',(pid,uid,oid)).fetchone()
        if d['anterior_id']!=(anterior[0] if anterior else None):raise ValueError('La nota de operación cambió; recarga.')
        c.execute('INSERT INTO notas_operacion_anual(periodo_id,voluntario_id,operacion_id,puntos_centesimas,anterior_id,evidencia_json,motivo,actor_id,actor_nombre,registrada_en) VALUES (?,?,?,?,?,?,?,?,?,?)',(pid,uid,oid,valor,d['anterior_id'],serializar(dict(o)),razon,current_user.id,current_user.nombre,db._ahora_utc()))
        c.execute('UPDATE participaciones_operacion SET revision=revision+1 WHERE operacion_id=? AND voluntario_id=?',(oid,uid))
        db.registrar_auditoria(c,current_user.id,'OPERACION_ANUAL_CALIFICADA','EXITOSO');c.commit();return jsonify(ok=True),201
    except (ValueError,KeyError,TypeError) as e:c.rollback();return jsonify(error=str(e)),409
    except LookupError as e:c.rollback();return jsonify(error=str(e)),404
    except (sqlite3.IntegrityError,sqlite3.OperationalError):c.rollback();return jsonify(error='Nota concurrente. Recarga.'),409

@anual_bp.patch('/api/modelo-anual/gestiones/<int:pid>')
@role_required('ADMINISTRADOR','JEFE_PERSONAL')
def editar(pid):
    c=db.obtener_conexion();d=request.get_json(silent=True)
    try:
        if not isinstance(d,dict) or set(d)!={'nombre','fecha_inicio','fecha_fin','revision','motivo'} or type(d['revision']) is not int:raise ValueError('Nombre, fechas, revisión y motivo requeridos.')
        razon=motivo(d)
        if not isinstance(d['nombre'],str) or not 2<=len(d['nombre'].strip())<=120:raise ValueError('Nombre de 2 a 120 caracteres.')
        for k in ('fecha_inicio','fecha_fin'):
            if not isinstance(d[k],str) or date.fromisoformat(d[k]).isoformat()!=d[k]:raise ValueError('Fechas válidas requeridas.')
        if d['fecha_inicio']>d['fecha_fin']:raise ValueError('Rango inválido.')
        c.execute('BEGIN IMMEDIATE');p=periodo(c,pid)
        if p['retirada'] or p['estado']!='BORRADOR' or p['revision']!=d['revision']:raise ValueError('Solo borrador y revisión vigente.')
        if c.execute('SELECT 1 FROM modelos_anuales m JOIN periodos p ON p.id=m.periodo_id WHERE p.id!=? AND p.fecha_inicio<=? AND p.fecha_fin>=? AND NOT EXISTS(SELECT 1 FROM bajas_gestion b WHERE b.periodo_id=p.id)',(pid,d['fecha_fin'],d['fecha_inicio'])).fetchone():raise ValueError('Rango superpuesto.')
        c.execute('UPDATE periodos SET nombre=?,fecha_inicio=?,fecha_fin=? WHERE id=?',(d['nombre'].strip(),d['fecha_inicio'],d['fecha_fin'],pid))
        c.execute('UPDATE modelos_anuales SET revision=revision+1 WHERE periodo_id=?',(pid,))
        evento(c,pid,'EDITAR',razon,p,{k:d[k] for k in ('nombre','fecha_inicio','fecha_fin','revision')})
        db.registrar_auditoria(c,current_user.id,'BORRADOR_MODELO_ANUAL_EDITADO','EXITOSO');c.commit();return jsonify(ok=True)
    except LookupError as e:c.rollback();return jsonify(error=str(e)),404
    except (ValueError,TypeError) as e:c.rollback();return jsonify(error=str(e)),409
    except (sqlite3.IntegrityError,sqlite3.OperationalError):c.rollback();return jsonify(error='Edición concurrente. Recarga.'),409

@anual_bp.delete('/api/modelo-anual/gestiones/<int:pid>')
@role_required('ADMINISTRADOR','JEFE_PERSONAL')
def retirar(pid):
    c=db.obtener_conexion();d=request.get_json(silent=True)
    try:
        if not isinstance(d,dict) or set(d)!={'revision','motivo'} or type(d['revision']) is not int:raise ValueError('Revisión y motivo requeridos.')
        razon=motivo(d);c.execute('BEGIN IMMEDIATE');p=periodo(c,pid)
        if p['retirada'] or p['revision']!=d['revision']:raise ValueError('Revisión obsoleta o Gestión retirada. Recarga.')
        evento(c,pid,'RETIRAR',razon,p,{'retirada':True})
        c.execute('INSERT INTO bajas_gestion(periodo_id,motivo,actor_id,actor_nombre,registrada_en) VALUES (?,?,?,?,?)',(pid,razon,current_user.id,current_user.nombre,db._ahora_utc()))
        db.registrar_auditoria(c,current_user.id,'GESTION_MODELO_ANUAL_RETIRADA','EXITOSO');c.commit();return jsonify(ok=True)
    except LookupError as e:c.rollback();return jsonify(error=str(e)),404
    except (ValueError,TypeError) as e:c.rollback();return jsonify(error=str(e)),409
    except (sqlite3.IntegrityError,sqlite3.OperationalError):c.rollback();return jsonify(error='Retiro concurrente. Recarga.'),409
