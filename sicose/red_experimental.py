"""MLP multietiqueta aislado: exclusivamente simulación con datos sintéticos.

No importar desde rutas de personas ni usar como interpretación psicométrica.
Biblioteca estándar, pesos JSON (sin pickle), semilla reproducible.
"""
import itertools
import math
import random
from copy import deepcopy

ENTRADAS = ('fisica', 'desempeno', 'academica', 'dass_depresion', 'dass_ansiedad',
            'dass_estres', 'cbi_personal', 'cbi_trabajo', 'cbi_personas')
MAXIMOS = (100, 100, 100, 42, 42, 42, 100, 100, 100)
SALIDAS = ('apoyo_fisico', 'acompanamiento_desempeno', 'apoyo_formativo', 'revision_profesional')
TEXTOS = ('Proponer acompañamiento para preparación física.',
          'Proponer acompañamiento y retroalimentación en el desempeño.',
          'Proponer un plan de formación y capacitación.',
          'Solicitar revisión confidencial por un profesional; sin conclusión automática.')


def normalizar(valores):
    if not isinstance(valores, (list, tuple)) or len(valores) != len(ENTRADAS):
        raise ValueError('Se requieren nueve valores completos; no se imputan ceros.')
    if any(type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= m
           for v, m in zip(valores, MAXIMOS)):
        raise ValueError('Entradas fuera de rango, ausentes o no finitas.')
    return [v/m for v, m in zip(valores, MAXIMOS)]


def _ejemplo(rng, patron):
    x = [(rng.randrange(0, 6000) if bit else rng.randrange(6000, 10001))/10000
         for bit in patron[:3]]
    while True:
        psico = [rng.randrange(22)/21 for _ in range(3)] + [
            rng.randrange(25)/24, rng.randrange(29)/28, rng.randrange(25)/24]
        if int(max(psico) > .6) == patron[3]:
            return [v*m for v, m in zip(x+psico, MAXIMOS)]


def datos_sinteticos(por_patron=None, semilla=2718):
    """16 combinaciones equilibradas; umbrales didácticos, NO clínicos.

    No incluye identidad, respuestas individuales, ni datos del SQLite local.
    División estratificada antes del entrenamiento. Sin filas idénticas.
    """
    # Compatibilidad explícita con el generador anterior, sin cambiar sus filas.
    if por_patron is None:
        return datos_compactos(semilla)
    if type(por_patron) is not int or por_patron < 20:
        raise ValueError('Se requieren al menos 20 ejemplos por patrón.')
    rng = random.Random(semilla)
    filas = []
    for patron in itertools.product((0, 1), repeat=4):
        for i in range(por_patron):
            entradas = _ejemplo(rng, patron)
            particion = 'entrenamiento' if i < int(.7*por_patron) else (
                'validacion' if i < int(.85*por_patron) else 'prueba')
            filas.append({'id': len(filas)+1, 'origen': 'SINTETICO', 'particion': particion,
                          'entradas': entradas, 'objetivos': list(patron)})
    rng.shuffle(filas)
    return filas


def datos_compactos(semilla=2718):
    """Exactamente 200 casos: 140/30/30; 16 patrones presentes en cada parte.

    Pares complementarios mantienen cada salida equilibrada: 70/70 en
    entrenamiento y 15/15 en validación y prueba. Ocho patrones tienen
    13 casos y ocho tienen 12. Las particiones se fijan antes de entrenar.
    """
    rng = random.Random(semilla)
    patrones = []
    for paridad in (0, 1):
        pares = []
        for p in itertools.product((0, 1), repeat=4):
            q = tuple(1-b for b in p)
            if sum(p) % 2 == paridad and p < q:
                pares.append((p, q))
        rng.shuffle(pares)
        for p, q in pares:
            patrones.extend((p, q) if rng.randrange(2) else (q, p))
    filas = []
    for particion, cantidad in (('entrenamiento', 140), ('validacion', 30), ('prueba', 30)):
        for _ in range(cantidad):
            patron = patrones[len(filas) % len(patrones)]
            filas.append({'id': len(filas)+1, 'origen': 'SINTETICO', 'particion': particion,
                          'entradas': _ejemplo(rng, patron), 'objetivos': list(patron)})
    rng.shuffle(filas)
    return filas


def sigmoide(z):
    return 1/(1+math.exp(-max(-40, min(40, z))))


class RedExperimental:
    entradas = ENTRADAS
    maximos = MAXIMOS
    salidas = SALIDAS
    textos = TEXTOS
    normalizar = staticmethod(normalizar)

    def __init__(self, semilla=31415, ocultas=6):
        self.entrenada = False
        self.entrenamiento = None
        rng = random.Random(semilla)
        self.w1 = [[rng.uniform(-.5, .5) for _ in ENTRADAS] for _ in range(ocultas)]
        self.b1 = [0.] * ocultas
        self.w2 = [[rng.uniform(-.5, .5) for _ in range(ocultas)] for _ in SALIDAS]
        self.b2 = [0.] * len(SALIDAS)

    def adelante(self, valores):
        x = self.normalizar(valores)
        h = [math.tanh(sum(w*v for w, v in zip(fila, x))+b) for fila, b in zip(self.w1, self.b1)]
        y = [sigmoide(sum(w*v for w, v in zip(fila, h))+b) for fila, b in zip(self.w2, self.b2)]
        return x, h, y

    def perdida(self, filas):
        """Entropía cruzada sumada sobre las cuatro salidas, media por caso."""
        return -sum(sum(t*math.log(max(y, 1e-12)) + (1-t)*math.log(max(1-y, 1e-12))
                        for t, y in zip(f['objetivos'], self.adelante(f['entradas'])[2]))
                    for f in filas)/len(filas)

    def _pesos(self):
        return {k: getattr(self, k) for k in ('w1', 'b1', 'w2', 'b2')}

    def _restaurar(self, pesos):
        for nombre, valor in pesos.items():
            setattr(self, nombre, valor)

    def _arquitectura(self):
        return [len(ENTRADAS), len(self.b1), len(SALIDAS)]

    def _paso(self, f, tasa, l2):
        x, h, y = self.adelante(f['entradas'])
        dy = [a-b for a, b in zip(y, f['objetivos'])]
        dh = [(1-v*v)*sum(d*self.w2[k][j] for k, d in enumerate(dy)) for j, v in enumerate(h)]
        for k, d in enumerate(dy):
            self.b2[k] -= tasa*d
            for j, v in enumerate(h):
                self.w2[k][j] -= tasa*(d*v + l2*self.w2[k][j])
        for j, d in enumerate(dh):
            self.b1[j] -= tasa*d
            for i, v in enumerate(x):
                self.w1[j][i] -= tasa*(d*v + l2*self.w1[j][i])

    def entrenar(self, filas, epocas=60, tasa=.03, validacion=None, paciencia=25, l2=0.):
        if type(epocas) is not int or not 1 <= epocas <= 1000 or type(tasa) not in (int, float) or not math.isfinite(tasa) or not 0 < tasa <= 1:
            raise ValueError('Épocas y tasa de aprendizaje inválidas.')
        if not filas or any(f['origen'] != 'SINTETICO' or f['particion'] != 'entrenamiento' for f in filas):
            raise ValueError('Solo entrenamiento sintético; prueba/validación están excluidas.')
        if type(paciencia) is not int or paciencia < 1 or type(l2) not in (int, float) or not math.isfinite(l2) or not 0 <= l2 <= 1:
            raise ValueError('Paciencia o regularización inválidas.')
        if validacion is not None:
            if not validacion or any(f['origen'] != 'SINTETICO' or f['particion'] != 'validacion' for f in validacion):
                raise ValueError('La parada temprana solo puede consultar validación sintética.')
            if ({f['id'] for f in filas} & {f['id'] for f in validacion} or
                    {tuple(f['entradas']) for f in filas} & {tuple(f['entradas']) for f in validacion}):
                raise ValueError('Entrenamiento y validación deben ser disjuntos.')
        for f in list(filas) + (list(validacion) if validacion is not None else []):
            self.normalizar(f['entradas'])
            if len(f['objetivos']) != 4 or any(type(v) is not int or v not in (0, 1) for v in f['objetivos']):
                raise ValueError('Se requieren cuatro objetivos binarios sintéticos.')
        rng = random.Random(42)
        orden = list(filas)
        mejor, pesos, elegida, sin_mejora = math.inf, None, 0, 0
        for epoca in range(1, epocas+1):
            rng.shuffle(orden)
            for f in orden:
                self._paso(f, tasa, l2)
            if validacion is not None:
                perdida = self.perdida(validacion)
                if perdida < mejor - 1e-6:
                    mejor, elegida, sin_mejora = perdida, epoca, 0
                    pesos = deepcopy(self._pesos())
                else:
                    sin_mejora += 1
                if sin_mejora >= paciencia:
                    break
        if pesos is not None:
            self._restaurar(pesos)
        self.entrenada = True
        self.entrenamiento = {'epocas_maximas': epocas, 'epocas_ejecutadas': epoca,
                              'epoca_elegida': elegida if validacion is not None else epoca,
                              'parada_temprana': validacion is not None, 'paciencia': paciencia,
                              'l2': l2, 'tasa': tasa,
                              'criterio': 'ENTROPIA_CRUZADA_VALIDACION' if validacion is not None else 'EPOCAS_FIJAS'}

    def simular(self, valores):
        if not self.entrenada:
            raise ValueError('El modelo todavía no está entrenado.')
        _, _, y = self.adelante(valores)
        incierta = any(.35 < v < .65 for v in y)
        textos = [t for t, v in zip(self.textos, y) if v >= .65]
        if incierta:
            textos = ['Resultado indeterminado: requiere revisión humana.']
        elif not textos:
            textos = ['Mantener seguimiento y oportunidades generales de desarrollo.']
        return {'origen': 'SINTETICO', 'experimental': True, 'uso_en_personas': False,
                'activaciones_no_calibradas': dict(zip(self.salidas, y)),
                'estado': 'ABSTENCION' if incierta else 'SIMULACION', 'sugerencias': textos}

    def exportar(self):
        return {'formato': 'MLP_SINTETICO_V1', 'origen': 'SINTETICO', 'uso_en_personas': False,
                'estado': 'ENTRENADO_SOLO_SINTETICO' if self.entrenada else 'SIN_ENTRENAR',
                'entrenamiento': self.entrenamiento,
                'entradas': self.entradas, 'maximos': self.maximos, 'salidas': self.salidas,
                'arquitectura': self._arquitectura(),
                'activacion_oculta': 'tanh', 'activacion_salida': 'sigmoid',
                'pesos': self._pesos()}


class RedDosCapas(RedExperimental):
    """Dos capas ocultas configurables para comparación offline, sin cambiar la base."""
    def __init__(self, semilla=31415, ocultas=(8, 4)):
        if not isinstance(ocultas, (tuple, list)) or len(ocultas) != 2 or any(type(v) is not int or not 1 <= v <= 128 for v in ocultas):
            raise ValueError('Se requieren dos capas ocultas de 1 a 128 neuronas.')
        self.entrenada = False
        self.entrenamiento = None
        rng = random.Random(semilla)
        dimensiones = (9, *ocultas, 4)
        for i, (entrada, salida) in enumerate(zip(dimensiones, dimensiones[1:]), 1):
            setattr(self, f'w{i}', [[rng.uniform(-.5, .5) for _ in range(entrada)] for _ in range(salida)])
            setattr(self, f'b{i}', [0.]*salida)

    def adelante(self, valores):
        x = self.normalizar(valores)
        h1 = [math.tanh(sum(w*v for w, v in zip(fila, x))+b) for fila, b in zip(self.w1, self.b1)]
        h2 = [math.tanh(sum(w*v for w, v in zip(fila, h1))+b) for fila, b in zip(self.w2, self.b2)]
        y = [sigmoide(sum(w*v for w, v in zip(fila, h2))+b) for fila, b in zip(self.w3, self.b3)]
        return x, (h1, h2), y

    def _pesos(self):
        return {k: getattr(self, k) for k in ('w1', 'b1', 'w2', 'b2', 'w3', 'b3')}

    def _arquitectura(self):
        return [9, len(self.b1), len(self.b2), 4]

    def _paso(self, f, tasa, l2):
        x, (h1, h2), y = self.adelante(f['entradas'])
        dy = [a-b for a, b in zip(y, f['objetivos'])]
        dh2 = [(1-v*v)*sum(d*self.w3[k][j] for k, d in enumerate(dy)) for j, v in enumerate(h2)]
        dh1 = [(1-v*v)*sum(d*self.w2[k][j] for k, d in enumerate(dh2)) for j, v in enumerate(h1)]
        # Calcular todos los deltas antes de modificar cualquier peso.
        for pesos, sesgos, anterior, deltas in ((self.w3, self.b3, h2, dy),
                (self.w2, self.b2, h1, dh2), (self.w1, self.b1, x, dh1)):
            for k, d in enumerate(deltas):
                sesgos[k] -= tasa*d
                for j, v in enumerate(anterior):
                    pesos[k][j] -= tasa*(d*v + l2*pesos[k][j])


def evaluar(red, filas):
    aciertos = [0]*len(red.salidas)
    exactos = abstenciones = 0
    for f in filas:
        y = red.adelante(f['entradas'])[2]
        bits = [int(v >= .5) for v in y]
        for i, (a, b) in enumerate(zip(bits, f['objetivos'])):
            aciertos[i] += a == b
        exactos += bits == f['objetivos']
        abstenciones += red.simular(f['entradas'])['estado'] == 'ABSTENCION'
    n = len(filas)
    return {'n': n, 'coincidencia_por_salida': dict(zip(red.salidas, [v/n for v in aciertos])),
            'coincidencia_completa': exactos/n, 'abstenciones': abstenciones,
            'alcance': 'Reproducción de reglas sintéticas; sin validez clínica o institucional.'}
