"""Experimento offline GSE/Mini-IPIP: sin reactivos ni conexión con personas.

Las etiquetas son una hipótesis didáctica, no baremos ni recomendaciones validadas.
Se generan puntuaciones agregadas posibles, no respuestas a cuestionarios.
"""
import itertools
import math
import random

from sicose.red_experimental import RedExperimental, RedDosCapas

ENTRADAS = ('fisica', 'desempeno', 'academica', 'gse_autoeficacia',
            'mini_extraversion', 'mini_amabilidad', 'mini_responsabilidad',
            'mini_neuroticismo', 'mini_apertura')
MINIMOS = (0, 0, 0, 10, 4, 4, 4, 4, 4)
MAXIMOS = (100, 100, 100, 40, 20, 20, 20, 20, 20)
SALIDAS = ('preparacion_y_confianza', 'comunicacion_y_colaboracion',
           'aprendizaje_y_autonomia', 'afrontamiento_y_metas')
TEXTOS = (
    'Proponer preparación física progresiva, metas alcanzables y seguimiento de hábitos y confianza.',
    'Proponer prácticas de coordinación y comunicación, responsabilidades graduales y retroalimentación individual.',
    'Proponer capacitación práctica con objetivos y seguimiento para favorecer la autonomía.',
    'Ofrecer orientación voluntaria para revisar exigencias, organizar metas y explorar estrategias de afrontamiento; sin conclusión clínica.',
)
REGLAS = {
    'naturaleza': 'HIPOTESIS_DIDACTICA_NO_VALIDADA',
    'preparacion_y_confianza': 'fisica < 60 y 0.70*(1-F) + 0.20*(1-G) + 0.10*(1-C) > 0.42',
    'comunicacion_y_colaboracion': 'desempeno < 60 y 0.65*(1-D) + 0.20*(1-G) + 0.075*(1-E) + 0.075*(1-A) > 0.42',
    'aprendizaje_y_autonomia': 'academica < 60 y 0.65*(1-Ac) + 0.20*(1-G) + 0.075*(1-O) + 0.075*(1-C) > 0.42',
    'afrontamiento_y_metas': 'G < 0.50 y 0.65*(1-G) + 0.20*N + 0.15*(1-C) > 0.50',
    'leyenda': 'F=fisica,D=desempeno,Ac=academica,G=GSE,E=extraversion,A=amabilidad,C=responsabilidad,N=neuroticismo,O=apertura; todos normalizados 0-1.',
    'limites': 'Cortes y pesos inventados solo para simulación. Ningún rasgo activa por sí solo una salida. GSE no tiene corte universal. No implican causalidad ni necesidades reales.',
}


def normalizar(valores):
    if not isinstance(valores, (tuple, list)) or len(valores) != 9:
        raise ValueError('Se requieren nueve puntuaciones completas GSE/Mini-IPIP.')
    if any(type(v) not in (int, float) or not math.isfinite(v) or not lo <= v <= hi
           for v, lo, hi in zip(valores, MINIMOS, MAXIMOS)):
        raise ValueError('Puntuaciones fuera de rango; no se imputan valores ausentes.')
    return [(v-lo)/(hi-lo) for v, lo, hi in zip(valores, MINIMOS, MAXIMOS)]


def objetivos_sinteticos(valores):
    f, d, ac, g, e, a, c, n, o = normalizar(valores)
    return [int(f < .6 and .70*(1-f)+.20*(1-g)+.10*(1-c) > .42),
            int(d < .6 and .65*(1-d)+.20*(1-g)+.075*(1-e)+.075*(1-a) > .42),
            int(ac < .6 and .65*(1-ac)+.20*(1-g)+.075*(1-o)+.075*(1-c) > .42),
            int(g < .5 and .65*(1-g)+.20*n+.15*(1-c) > .5)]


def datos_sinteticos(semilla=2718):
    """200 filas únicas; los 16 patrones presentes en cada partición.

    Muestreo por rechazo estratificado según etiquetas ficticias: NO prevalencias
    de población. Semilla y particiones fijas antes del entrenamiento.
    """
    rng = random.Random(semilla)
    patrones = []
    for paridad in (0, 1):
        pares = [(p, tuple(1-b for b in p)) for p in itertools.product((0, 1), repeat=4)
                 if sum(p) % 2 == paridad and p < tuple(1-b for b in p)]
        rng.shuffle(pares)
        for p, q in pares:
            patrones.extend((p, q) if rng.randrange(2) else (q, p))
    filas, vistos = [], set()
    for particion, cantidad in (('entrenamiento', 140), ('validacion', 30), ('prueba', 30)):
        for _ in range(cantidad):
            patron = patrones[len(filas) % 16]
            for intento in range(100000):
                x = [rng.randrange(201)/2, rng.randrange(201)/2, rng.randrange(101),
                     rng.randrange(10, 41), *[rng.randrange(4, 21) for _ in range(5)]]
                if tuple(x) not in vistos and tuple(objetivos_sinteticos(x)) == patron:
                    break
            else:
                raise RuntimeError('No se pudo completar el patrón sintético.')
            vistos.add(tuple(x))
            filas.append({'id': len(filas)+1, 'origen': 'SINTETICO',
                          'particion': particion, 'entradas': x, 'objetivos': list(patron)})
    rng.shuffle(filas)
    return filas


class RedGseMiniIpip(RedExperimental):
    entradas = ENTRADAS
    maximos = MAXIMOS
    salidas = SALIDAS
    textos = TEXTOS
    normalizar = staticmethod(normalizar)

    def exportar(self):
        modelo = super().exportar()
        modelo.update(formato='MLP_GSE_MINIIPIP_SINTETICO_V1', minimos=MINIMOS,
                      normalizacion='(valor-minimo)/(maximo-minimo)',
                      reglas_etiquetado=REGLAS,
                      puntuaciones='GSE suma 10-40; Mini-IPIP cinco sumas 4-20 tras inversión de ítems; sin reactivos generados.')
        return modelo


class RedGseMiniIpipDosCapas(RedDosCapas, RedGseMiniIpip):
    """Alternativa 9→6→4→4: mismo protocolo y semántica GSE/Mini-IPIP."""

    def __init__(self, semilla=31415):
        super().__init__(semilla=semilla, ocultas=(6, 4))

    def exportar(self):
        modelo = super().exportar()
        modelo['formato'] = 'MLP_GSE_MINIIPIP_DOS_CAPAS_SINTETICO_V1'
        return modelo
