"""Propuestas de orientación con pesos fijados, evidencia y confirmación humana.

La integración autorizada no cambia los artefactos offline ni acredita validez
del modelo. No hay entrenamiento en solicitudes ni decisiones de aptitud.
"""
import hashlib
import json
import math
from pathlib import Path
from flask import Blueprint, jsonify, request
from flask_login import current_user
from . import db
from .modelo_anual import periodo, persona, serializar
from .calculos_5b import calcular
from .permissions import role_required
from .psicometria import transaccion
from .pruebas_actuales import estado, intento, simulacro
from .instrumentos_actuales import firma as firma_formulario, TLX_DIMENSIONES
from .red_gse_miniipip import RedGseMiniIpip, ENTRADAS as ENTRADAS_ANTERIORES
from .modelo_orientacion_tlx import ModeloTlx, ENTRADAS, SALIDAS, TEXTOS

recomendaciones_bp = Blueprint('recomendaciones', __name__)
MODELO_PATH = Path(__file__).resolve().parents[1]/'output/comparacion_tlx_1564_15664_200_20261018/15-6-4/modelo_ejemplar_validacion.json'
MODELO_SHA = 'a98b65067700a975bb1993fe9510235900c21e15009adec8a18f46bca05e1353'
MODELO_ANTERIOR_SHA = 'abb2bed7e4bcc7e232388bf671afbf5d2ba5bce309f14b79026d92a2d0bad252'
AVISO = ('Propuesta de orientación de un modelo experimental entrenado con datos generados. '
         'No es un diagnóstico ni una evaluación de aptitud. Requiere revisión humana; '
         'no decide ascensos, sanciones o participación operativa. Las activaciones no son probabilidades calibradas.')
VERSION_PRIORITARIA = 'ORIENTACION_PRIORITARIA_V1'


def seleccionar_prioridad(activaciones):
    """Una línea por argmax; el orden original resuelve empates exactos."""
    if len(activaciones)!=len(SALIDAS) or any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=1 for v in activaciones):
        raise ValueError('El modelo produjo una salida inválida.')
    orden=sorted(range(len(SALIDAS)),key=lambda i:-activaciones[i])
    elegida=orden[0]
    return dict(criterio_seleccion='ARGMAX_V1',salida_prioritaria=SALIDAS[elegida],
        sugerencias=[TEXTOS[elegida]],margen_activacion=activaciones[elegida]-activaciones[orden[1]],
        orden_activaciones=[dict(salida=SALIDAS[i],activacion=activaciones[i]) for i in orden],
        empates_maximos=[SALIDAS[i] for i in orden if activaciones[i]==activaciones[elegida]],
        desempate='ORDEN_ORIGINAL_DE_SALIDAS')


@recomendaciones_bp.after_request
def privada(r):
    r.headers['Cache-Control'] = 'private, no-store'
    return r


def cargar_modelo():
    try:
        contenido = MODELO_PATH.read_bytes()
    except OSError:
        raise ValueError('Modelo seleccionado no disponible.') from None
    if hashlib.sha256(contenido).hexdigest() != MODELO_SHA:
        raise ValueError('La huella del modelo seleccionado no coincide. Requiere revisión técnica.')
    m = json.loads(contenido)
    return ModeloTlx(m)


def contexto(c, pid, uid):
    p = periodo(c, pid)
    u = c.execute('SELECT u.estado FROM usuarios u JOIN personas_modelo_anual a ON a.voluntario_id=u.id WHERE a.periodo_id=? AND u.id=?', (pid, uid)).fetchone()
    if not u:
        raise LookupError('Persona no inscrita en esta Gestión.')
    ultimo = c.execute('SELECT id,modelo_sha256,fuentes_json FROM recomendaciones WHERE periodo_id=? AND voluntario_id=? ORDER BY id DESC LIMIT 1', (pid, uid)).fetchone()
    historico = p['estado']=='CERRADO' and ultimo and ultimo['modelo_sha256']==MODELO_ANTERIOR_SHA
    modelo_sha = MODELO_ANTERIOR_SHA if historico else MODELO_SHA
    calculo = calcular(c, uid, pid)
    faltantes, pruebas, vector = [], {}, []
    for k, v in [('Físico', calculo.get('fisica')), ('Desempeño', calculo.get('desempeno')), ('Académica', calculo.get('academica', {}).get('valor'))]:
        if v is None:
            faltantes.append(k)
        vector.append(float(v) if v is not None else None)
    for clave in (('GSE', 'MINIIPIP') if historico else ('GSE','MINIIPIP','NASATLX')):
        a, i = estado(c, pid, clave), intento(c, pid, uid, clave)
        completa = i and i['finalizada_en'] and i['firma_formulario'] == firma_formulario(clave)
        disponible = a['activa'] and a['revisada'] and completa
        if not disponible:
            faltantes.append(f'{clave}: completar y mantener habilitada la versión revisada')
        pruebas[clave] = dict(activacion_revision=a['revision'], habilitada=a['activa'], revisada=a['revisada'],
            intento_id=i['id'] if i else None, intento_revision=i['revision'] if i else None,
            firma_formulario=i['firma_formulario'] if i else None,
            resultados=json.loads(i['resultados_json']) if completa else None)
        if i and i['ciclo']:
            pruebas[clave]['reinicio_id'] = i['ciclo']
        if clave=='NASATLX':
            pruebas[clave]['simulacro'] = simulacro(c,pid)
            if completa and not i['simulacro_confirmado']:
                faltantes.append('NASA-TLX: confirmar participación en el simulacro')
    g, m = pruebas['GSE']['resultados'], pruebas['MINIIPIP']['resultados']
    vector += [g['autoeficacia']['valor'] if g else None]
    vector += [m[k]['valor'] if m else None for k in ('extraversion', 'amabilidad', 'responsabilidad', 'neuroticismo', 'apertura')]
    if not historico:
        tlx=pruebas['NASATLX']['resultados']
        vector += [tlx[k]['valor'] if tlx else None for k in TLX_DIMENSIONES]
    try:
        if historico:
            path=Path(__file__).resolve().parents[1]/'output/modelo_gse_miniipip_200_20261017/modelo.json'
            contenido=path.read_bytes()
            if hashlib.sha256(contenido).hexdigest()!=MODELO_ANTERIOR_SHA: raise ValueError('Modelo histórico modificado.')
            red=RedGseMiniIpip();red._restaurar(json.loads(contenido)['pesos'])
        else:
            red = cargar_modelo()
        if not faltantes:
            red.normalizar(vector)
    except (ValueError,OSError) as e:
        faltantes.append(str(e))
    version_integracion=VERSION_PRIORITARIA
    if p['estado']=='CERRADO' and ultimo:
        version_integracion=json.loads(ultimo['fuentes_json']).get('version_integracion','ORIENTACION_V29' if historico else 'ORIENTACION_V31')
    fuentes = dict(version_integracion=version_integracion, periodo_id=pid, persona_id=uid,
        fechas=[p['fecha_inicio'], p['fecha_fin']], entradas=vector, modelo_sha256=modelo_sha,
        notas={k: v.get('id', v.get('nota_id')) for k, v in calculo.get('fuentes', {}).items()},
        cursos=calculo.get('academica', {}).get('detalle', []),
        operaciones=calculo.get('academica', {}).get('operaciones', []), pruebas=pruebas)
    # La firma se conserva incluso si falta una fuente, para detectar su retirada.
    firma = hashlib.sha256(serializar(fuentes).encode()).hexdigest()
    ultimo = c.execute('SELECT id FROM recomendaciones WHERE periodo_id=? AND voluntario_id=? ORDER BY id DESC LIMIT 1', (pid, uid)).fetchone()
    editable = p['estado']=='ACTIVO' and not p['retirada'] and u['estado']=='ACTIVO'
    return dict(entradas=dict(zip(ENTRADAS_ANTERIORES if historico else ENTRADAS, vector)), fuentes=fuentes, firma_fuentes=firma,
                faltantes=faltantes, editable=editable, puede_generar=editable and not faltantes,
                ultima_id=ultimo['id'] if ultimo else None, aviso=AVISO,
                modelo=dict(arquitectura=[9,6,4] if historico else [15,6,4], sha256=modelo_sha, semilla=31415 if historico else 401, epoca=84 if historico else 196,
                    criterio_seleccion='ARGMAX_V1' if version_integracion==VERSION_PRIORITARIA else 'UMBRALES_V1'))


def historial(c, pid, uid, ctx):
    salida = []
    for r in c.execute('SELECT * FROM recomendaciones WHERE periodo_id=? AND voluntario_id=? ORDER BY id DESC', (pid, uid)):
        confirmacion = c.execute('SELECT * FROM confirmaciones_recomendacion WHERE recomendacion_id=?', (r['id'],)).fetchone()
        actual = r['firma_fuentes']==ctx['firma_fuentes'] and not ctx['faltantes'] and r['id']==ctx['ultima_id']
        salida.append(dict(id=r['id'], anterior_id=r['anterior_id'], estado='Desactualizada' if not actual else ('Confirmada' if confirmacion else 'Propuesta'),
            generada_en=r['generada_en'], generada_por=r['actor_nombre'], firma_fuentes=r['firma_fuentes'],
            entradas=json.loads(r['entradas_json']), modelo_sha256=r['modelo_sha256'],
            resultado=json.loads(r['resultado_json']), confirmacion=dict(confirmacion) if confirmacion else None))
    return salida


def para_reporte(c, pid, uid):
    from .modelo_anual import es_modelo
    if not es_modelo(c, pid):
        return None
    ctx = contexto(c, pid, uid)
    registros = historial(c, pid, uid, ctx)
    if registros and registros[0]['estado']=='Confirmada':
        return registros[0]
    return None


@recomendaciones_bp.get('/api/modelo-anual/gestiones/<int:pid>/personas/<int:uid>/recomendacion')
@recomendaciones_bp.post('/api/modelo-anual/gestiones/<int:pid>/personas/<int:uid>/recomendacion')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
@transaccion
def gestionar(c, pid, uid):
    ctx = contexto(c, pid, uid)
    if request.method == 'GET':
        return jsonify(**{k:v for k,v in ctx.items() if k!='fuentes'}, historial=historial(c, pid, uid, ctx))
    periodo(c, pid, True)
    persona(c, pid, uid)
    d = request.get_json(silent=True)
    if not isinstance(d, dict) or set(d) != {'firma_fuentes', 'anterior_id'} or not (d['anterior_id'] is None or type(d['anterior_id']) is int):
        raise ValueError('Firma de fuentes y propuesta anterior requeridas. No se aceptan entradas manuales.')
    if not ctx['puede_generar']:
        raise ValueError('Faltan entradas o habilitaciones: '+', '.join(ctx['faltantes']))
    if d['firma_fuentes'] != ctx['firma_fuentes'] or d['anterior_id'] != ctx['ultima_id']:
        raise ValueError('Las fuentes o la propuesta cambiaron. Recarga antes de generar.')
    previas = historial(c, pid, uid, ctx)
    if previas and previas[0]['estado'] != 'Desactualizada':
        return jsonify(ok=True, id=previas[0]['id'], sin_cambios=True)
    red = cargar_modelo()
    x = [ctx['entradas'][k] for k in ENTRADAS]
    _, _, y = red.adelante(x)
    prioridad=seleccionar_prioridad(y)
    resultado = dict(estado_modelo='PROPUESTA',
        arquitectura=[15,6,4], semilla=401, epoca=196,
        activaciones=dict(zip(SALIDAS,y)), aviso=AVISO,**prioridad,
        origen_entrenamiento='DATOS_GENERADOS', validacion_personal=False)
    rid = c.execute('INSERT INTO recomendaciones(periodo_id,voluntario_id,anterior_id,firma_fuentes,fuentes_json,entradas_json,modelo_sha256,resultado_json,actor_id,actor_nombre,generada_en) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
        (pid,uid,ctx['ultima_id'],ctx['firma_fuentes'],serializar(ctx['fuentes']),serializar(ctx['entradas']),MODELO_SHA,serializar(resultado),current_user.id,current_user.nombre,db._ahora_utc())).lastrowid
    db.registrar_auditoria(c,current_user.id,f'RECOMENDACION_PROPUESTA:{pid}:{uid}:{rid}','EXITOSO')
    return jsonify(ok=True,id=rid),201


@recomendaciones_bp.post('/api/modelo-anual/gestiones/<int:pid>/personas/<int:uid>/recomendacion/<int:rid>/confirmar')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
@transaccion
def confirmar(c,pid,uid,rid):
    periodo(c,pid,True)
    persona(c,pid,uid)
    ctx = contexto(c,pid,uid)
    d = request.get_json(silent=True)
    if not isinstance(d,dict) or set(d)!={'firma_fuentes','observacion','confirmar'} or d['confirmar'] is not True:
        raise ValueError('Confirma la revisión humana e incluye la observación del responsable.')
    if not isinstance(d['observacion'],str) or not 1<=len(d['observacion'].strip())<=2000:
        raise ValueError('Observación del responsable obligatoria, máximo 2000 caracteres.')
    registros = historial(c,pid,uid,ctx)
    if (not registros or registros[0]['id']!=rid or registros[0]['estado']=='Desactualizada'
        or d['firma_fuentes']!=ctx['firma_fuentes'] or ctx['faltantes']):
        raise ValueError('Propuesta desactualizada o fuentes incompletas. Genera una nueva propuesta.')
    if registros[0]['confirmacion']:
        if registros[0]['confirmacion']['observacion']!=d['observacion'].strip():
            raise ValueError('La confirmación conservada no se puede modificar.')
        return jsonify(ok=True,sin_cambios=True)
    c.execute('INSERT INTO confirmaciones_recomendacion VALUES (?,?,?,?,?)',
        (rid,d['observacion'].strip(),current_user.id,current_user.nombre,db._ahora_utc()))
    db.registrar_auditoria(c,current_user.id,f'RECOMENDACION_CONFIRMADA:{pid}:{uid}:{rid}','EXITOSO')
    return jsonify(ok=True)
