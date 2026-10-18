"""MLP offline de quince entradas, con una o dos capas ocultas; JSON sin pickle."""
from copy import deepcopy
import math
import random

from generar_datos_tlx_gse_miniipip import VARIABLES
from etiquetar_datos_tlx_gse_miniipip import SALIDAS, TITULOS


class RedTlx:
    def __init__(self, ocultas=(6,), semilla=31415):
        if tuple(ocultas) not in ((6,), (6, 6)):
            raise ValueError('Arquitecturas admitidas: 15-6-4 y 15-6-6-4.')
        self.arquitectura = [15, *ocultas, 4]
        rng = random.Random(semilla)
        self.w = [[[rng.uniform(-.5, .5) for _ in range(n)] for _ in range(m)]
                  for n, m in zip(self.arquitectura, self.arquitectura[1:])]
        self.b = [[0.]*m for m in self.arquitectura[1:]]
        self.entrenamiento = None

    @staticmethod
    def normalizar(x):
        if len(x) != 15:
            raise ValueError('Quince entradas requeridas.')
        for v, (_, _, lo, hi, _) in zip(x, VARIABLES):
            if type(v) not in (float, int) or not math.isfinite(v) or not lo <= v <= hi:
                raise ValueError('Entrada inválida; sin imputación.')
        return [(v-lo)/(hi-lo) for v, (_, _, lo, hi, _) in zip(x, VARIABLES)]

    def adelante(self, x):
        activaciones = [self.normalizar(x)]
        for i, (w, b) in enumerate(zip(self.w, self.b)):
            z = [sum(p*a for p, a in zip(fila, activaciones[-1]))+sesgo for fila, sesgo in zip(w, b)]
            activaciones.append([1/(1+math.exp(-max(-40, min(40, v)))) for v in z]
                                if i == len(self.w)-1 else [math.tanh(v) for v in z])
        return activaciones

    def perdida(self, filas):
        return -sum(sum(t*math.log(max(y, 1e-12))+(1-t)*math.log(max(1-y, 1e-12))
                        for t, y in zip(f['objetivos'], self.adelante(f['entradas'])[-1]))
                    for f in filas)/len(filas)

    def gradientes(self, f):
        a = self.adelante(f['entradas'])
        deltas = [None]*len(self.w)
        deltas[-1] = [y-t for y, t in zip(a[-1], f['objetivos'])]
        for l in range(len(self.w)-2, -1, -1):
            deltas[l] = [(1-v*v)*sum(self.w[l+1][k][j]*d for k, d in enumerate(deltas[l+1]))
                         for j, v in enumerate(a[l+1])]
        return [[[d*v for v in a[l]] for d in ds] for l, ds in enumerate(deltas)], deltas

    def entrenar(self, filas, validacion, epocas=300, paciencia=25, tasa=.03, l2=.001):
        for grupo, particion in ((filas, 'entrenamiento'), (validacion, 'validacion')):
            if not grupo or any(f['origen'] != 'Datos' or f['particion'] != particion for f in grupo):
                raise ValueError('Partición u origen inválido.')
            for f in grupo:
                self.normalizar(f['entradas'])
                if len(f['objetivos']) != 4 or any(type(v) is not int or v not in (0, 1) for v in f['objetivos']):
                    raise ValueError('Cuatro etiquetas binarias requeridas.')
        if ({f['id'] for f in filas} & {f['id'] for f in validacion} or
                {tuple(f['entradas']) for f in filas} & {tuple(f['entradas']) for f in validacion}):
            raise ValueError('Particiones solapadas.')
        rng = random.Random(42)
        orden = list(filas)
        mejor, elegida, espera, pesos = math.inf, 0, 0, None
        historial = []
        for epoca in range(1, epocas+1):
            rng.shuffle(orden)
            for f in orden:
                dw, db = self.gradientes(f)
                for l, w in enumerate(self.w):
                    for k, fila in enumerate(w):
                        self.b[l][k] -= tasa*db[l][k]
                        for j in range(len(fila)):
                            fila[j] -= tasa*(dw[l][k][j]+l2*fila[j])
            perdida = self.perdida(validacion)
            historial.append(perdida)
            if perdida < mejor-1e-6:
                mejor, elegida, espera = perdida, epoca, 0
                pesos = deepcopy((self.w, self.b))
            else:
                espera += 1
            if espera >= paciencia:
                break
        self.w, self.b = pesos
        self.entrenamiento = dict(epoca_elegida=elegida, epocas_ejecutadas=epoca,
            epocas_maximas=epocas, paciencia=paciencia, tasa=tasa, l2=l2, semilla_orden=42,
            lote=1, tolerancia=1e-6, criterio='Menor BCE de validación; restaura pesos',
            perdida_validacion_por_epoca=historial)

    def exportar(self):
        return dict(formato='MLP_TLX_GSE_MINIIPIP_V1', origen='Datos',
            procedencia='Puntuaciones generadas por computadora, etiquetas de reglas didácticas; sin validación personal.',
            uso_en_personas=False, estado='ENTRENADO_EXPERIMENTAL' if self.entrenamiento else 'SIN_ENTRENAR',
            arquitectura=self.arquitectura, parametros=sum(len(f) for w in self.w for f in w)+sum(map(len, self.b)),
            entradas=[v[0] for v in VARIABLES], minimos=[v[2] for v in VARIABLES], maximos=[v[3] for v in VARIABLES],
            normalizacion='(valor-minimo)/(maximo-minimo)', salidas=SALIDAS, titulos=TITULOS,
            activacion_oculta='tanh', activacion_salida='sigmoid',
            pesos=dict(w=self.w, b=self.b), entrenamiento=self.entrenamiento,
            umbral_metricas=.5, umbrales_abstencion=[.35, .65])


def evaluar(red, filas):
    predicciones = [red.adelante(f['entradas'])[-1] for f in filas]
    aciertos = sum(all(int(y >= .5) == t for y, t in zip(p, f['objetivos'])) for p, f in zip(predicciones, filas))
    abstenciones = sum(any(.35 < y < .65 for y in p) for p in predicciones)
    por_salida = {}
    for k, nombre in enumerate(SALIDAS):
        vp = vn = fp = fn = 0
        for p, f in zip(predicciones, filas):
            y, t = int(p[k] >= .5), f['objetivos'][k]
            vp += y == t == 1; vn += y == t == 0
            fp += y == 1 and t == 0; fn += y == 0 and t == 1
        por_salida[nombre] = dict(vp=vp, vn=vn, fp=fp, fn=fn,
            f1=2*vp/(2*vp+fp+fn) if 2*vp+fp+fn else 0,
            exactitud=(vp+vn)/len(filas))
    return dict(n=len(filas), bce=red.perdida(filas), aciertos_completos=aciertos,
        coincidencia_completa=aciertos/len(filas), abstenciones=abstenciones,
        f1_macro=sum(v['f1'] for v in por_salida.values())/4, por_salida=por_salida)
