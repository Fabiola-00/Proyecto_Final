"""Cálculo provisional exacto; activación explícita, sin publicación ni instantáneas."""
import sqlite3
from decimal import Decimal
from fractions import Fraction
from flask import Blueprint, jsonify, request
from flask_login import current_user
from . import db
from .permissions import role_required
from .gestiones import activa, retirada

calculos_bp = Blueprint('calculos_5b', __name__)


def regla(c, pid):
    fila = c.execute('SELECT * FROM reglas_calculo_5b WHERE periodo_id=?', (pid,)).fetchone()
    return dict(fila) if fila else None


def expresar(centesimas):
    """Componentes exactos: una media de centésimas puede necesitar tres decimales."""
    return format(Decimal(centesimas.numerator) / Decimal(centesimas.denominator) / 100, 'f')


def calcular(c, uid, pid):
    from .tabla_evaluaciones import habilitada
    periodo = c.execute('SELECT estado FROM periodos WHERE id=?', (pid,)).fetchone()
    if periodo and periodo['estado'] == 'CERRADO':
        from .cierres_5b import resultado_cerrado
        return resultado_cerrado(c, uid, pid)
    from .modelo_anual import es_modelo, calcular as calcular_anual
    if es_modelo(c, pid):
        return calcular_anual(c, uid, pid)
    r = regla(c, pid)
    if r is None:
        return {'regla': None, 'estado': 'SIN_REGLA_NUEVA', 'resultado_conjunto': None, 'faltantes': [],
                'limite': 'Activa explícitamente ACUMULADO_TRES_V2; los históricos no se adoptan automáticamente.'}
    faltantes, bloqueos, fuentes = [], [], {}
    for fuente in ('FISICA_1', 'FISICA_2', 'DESEMPENO_JEFE', 'DESEMPENO_COMANDANTE'):
        n = c.execute('SELECT * FROM notas_operativas WHERE voluntario_id=? AND periodo_id=? AND fuente=? ORDER BY id DESC LIMIT 1', (uid, pid, fuente)).fetchone()
        valida = bool(n and n['configuracion_id'] == r['configuracion_id'])
        fisica = c.execute('SELECT estado,fecha_realizacion,programacion_id,reprogramacion_id FROM resultados_fisicos WHERE nota_id=?', (n['id'],)).fetchone() if n and fuente.startswith('FISICA_') else None
        if fuente.startswith('FISICA_') and fisica is None:
            valida = False
        disponible = activa(c, pid, fuente) and habilitada(c, uid, pid, fuente)
        fuentes[fuente] = {'nota_id': n['id'] if n else None, 'nota': f"{n['puntos_centesimas']/100:.2f}" if n else None,
                          'incluida': valida and disponible, 'resultado_fisico': dict(fisica) if fisica else None}
        if not disponible:
            bloqueos.append(fuente)
        if not valida or not disponible:
            faltantes.append(fuente)
    detalle = [dict(f) for f in c.execute("""SELECT p.id AS participacion_id,p.curso_id,p.nombre_curso,p.puntaje,p.fecha_finalizacion,p.revision,
                 h.id AS historial_id FROM participaciones_curso p JOIN historial_participaciones_curso h
                 ON h.participacion_id=p.id AND h.revision=p.revision
                 WHERE p.voluntario_id=? AND p.estado='Finalizado' AND substr(p.fecha_finalizacion,1,4)=?
                 ORDER BY p.fecha_finalizacion,p.id""", (uid, f"{r['ano']:04d}"))]
    suma = sum(f['puntaje'] for f in detalle)
    academia_disponible = activa(c, pid, 'ACADEMICA') and habilitada(c, uid, pid, 'ACADEMICA')
    academia = min(suma, 100) if detalle and academia_disponible else None
    if academia is None:
        faltantes.append('ACADEMICA')
    if not academia_disponible:
        bloqueos.append('ACADEMICA')
    fisica, desempeno = None, None
    def media(a, b):
        if not fuentes[a]['incluida'] or not fuentes[b]['incluida']:
            return None
        valores = [c.execute('SELECT puntos_centesimas FROM notas_operativas WHERE id=?', (fuentes[f]['nota_id'],)).fetchone()[0] for f in (a, b)]
        return Fraction(sum(valores), 2)
    fisica = media('FISICA_1', 'FISICA_2')
    desempeno = media('DESEMPENO_JEFE', 'DESEMPENO_COMANDANTE')
    conjunto, exacto = None, None
    if not faltantes:
        exacto = (fisica + desempeno + academia * 100) / 3
        cent = (2 * exacto.numerator + exacto.denominator) // (2 * exacto.denominator)
        conjunto = f'{cent // 100}.{cent % 100:02d}'
    return {'regla': r['regla'], 'activacion': r, 'estado': 'COMPLETO' if not faltantes else 'INCOMPLETO',
            'resultado_conjunto': conjunto, 'fisica': expresar(fisica) if fisica is not None else None,
            'desempeno': expresar(desempeno) if desempeno is not None else None,
            'academica': {'valor': academia, 'puntos_sin_tope': suma, 'tope': 100, 'detalle': detalle},
            'fuentes': fuentes, 'faltantes': faltantes, 'bloqueos': bloqueos, 'provisional': True,
            'resultado_exacto_centesimas': {'numerador': exacto.numerator, 'denominador': exacto.denominator} if exacto is not None else None}


@calculos_bp.post('/api/admin/5b/periodos/<int:pid>/calculo')
@role_required('ADMINISTRADOR')
def activar(pid):
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict) or set(datos) != {'configuracion_id', 'regla', 'confirmar_fuentes'} or type(datos['configuracion_id']) is not int or datos['regla'] != 'ACUMULADO_TRES_V2' or datos['confirmar_fuentes'] is not True:
        return jsonify(error='Confirma explícitamente regla nueva, configuración y alcance de fuentes.'), 400
    c = db.obtener_conexion()
    try:
        c.execute('BEGIN IMMEDIATE')
        from .fisicas import periodo_activo
        p = periodo_activo(c, pid)
        from .modelo_anual import es_modelo
        if es_modelo(c,pid):
            c.rollback();return jsonify(error='La Gestión usa CINCO_ENTRADAS_V3; no se adopta V2.'),409
        if (c.execute('SELECT 1 FROM cierres_5b WHERE periodo_id=?', (pid,)).fetchone()
                or c.execute('SELECT 1 FROM reaperturas_historicas_5b WHERE periodo_id=?', (pid,)).fetchone()):
            c.rollback(); return jsonify(error='La Gestión ya tiene cierres: conserva su regla original; una regla nueva corresponde a una Gestión futura.'), 409
        conf = c.execute("SELECT id FROM configuraciones_5b WHERE periodo_id=? AND estado='PUBLICADA'", (pid,)).fetchone()
        if retirada(c, pid) or conf['id'] != datos['configuracion_id'] or regla(c, pid):
            c.rollback(); return jsonify(error='Gestión retirada, regla existente o configuración desactualizada.'), 409
        c.execute("INSERT INTO reglas_calculo_5b(periodo_id,ano,configuracion_id,regla,activada_por,responsable_nombre,activada_en) VALUES (?,?,?,'ACUMULADO_TRES_V2',?,?,?)", (pid, int(p['fecha_inicio'][:4]), conf['id'], current_user.id, current_user.nombre, db._ahora_utc()))
        db.registrar_auditoria(c, current_user.id, 'REGLA_CALCULO_V2_ACTIVADA', 'EXITOSO')
        c.commit()
        return jsonify(ok=True, regla=regla(c, pid)), 201
    except (sqlite3.IntegrityError, sqlite3.OperationalError):
        c.rollback(); return jsonify(error='Conflicto o año con regla nueva ya registrada; no se duplican imputaciones académicas.'), 409
    except ValueError as error:
        c.rollback(); return jsonify(error=str(error)), 409


@calculos_bp.get('/api/5b/personas/<int:uid>/calculo')
@role_required('ADMINISTRADOR', 'JEFE_PERSONAL')
def consultar(uid):
    try:
        from .tabla_evaluaciones import periodo_solicitado
        from .seguimiento_5b import persona
        pid = periodo_solicitado()
        c = db.obtener_conexion()
        c.execute('BEGIN')
        if persona(c, uid) is None or not c.execute('SELECT 1 FROM periodos WHERE id=?', (pid,)).fetchone():
            c.rollback(); return jsonify(error='Persona o gestión no encontrada.'), 404
        valor = calcular(c, uid, pid)
        c.commit()
        return jsonify(calculo=valor)
    except ValueError as error:
        return jsonify(error=str(error)), 400
