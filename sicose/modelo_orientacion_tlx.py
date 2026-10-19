"""Inferencia únicamente: pesos JSON verificados de la red 15→6→4 ya entrenada."""
import math
from copy import deepcopy

ENTRADAS = ('fisica','desempeno','academica','gse_autoeficacia','mini_extraversion','mini_amabilidad',
    'mini_responsabilidad','mini_neuroticismo','mini_apertura','tlx_demanda_mental','tlx_demanda_fisica',
    'tlx_demanda_temporal','tlx_rendimiento','tlx_esfuerzo','tlx_frustracion')
MINIMOS = (0,0,0,10,4,4,4,4,4,0,0,0,0,0,0)
MAXIMOS = (100,100,100,40,20,20,20,20,20,100,100,100,100,100,100)
SALIDAS = ('preparacion_progresiva_y_confianza','organizacion_de_tareas_y_manejo_de_carga',
    'comunicacion_y_aprendizaje_acompanado','afrontamiento_y_seguimiento_del_bienestar')
TEXTOS = ('Proponer preparación progresiva y confianza mediante prácticas graduales, considerando capacidades, autoeficacia y carga física percibida.',
    'Proponer organización de tareas y manejo de la carga mediante priorización y distribución de tareas según demanda mental y temporal.',
    'Proponer comunicación y aprendizaje acompañado mediante coordinación, retroalimentación y capacitación con acompañamiento.',
    'Ofrecer orientación voluntaria para el afrontamiento y seguimiento del bienestar, revisando exigencias, frustración y estrategias de afrontamiento; sin conclusión clínica.')


class ModeloTlx:
    def __init__(self,m):
        if m['arquitectura'] != [15,6,4] or m['entradas'] != list(ENTRADAS) or m['salidas'] != list(SALIDAS) or m['minimos']!=list(MINIMOS) or m['maximos']!=list(MAXIMOS):
            raise ValueError('Modelo incompatible con las quince entradas vigentes.')
        self.w,self.b=m['pesos']['w'],m['pesos']['b']
        self._documento=m
        if len(self.w)!=2 or [len(w) for w in self.w]!=[6,4] or [len(b) for b in self.b]!=[6,4] or any(len(f)!=n for w,n in zip(self.w,(15,6)) for f in w):
            raise ValueError('Dimensiones de pesos inválidas.')
        if not all(type(v) in (int,float) and math.isfinite(v) for capa in self.w for fila in capa for v in fila) or not all(math.isfinite(v) for b in self.b for v in b):
            raise ValueError('Pesos no finitos.')

    def normalizar(self,x):
        if len(x)!=15 or any(type(v) not in (int,float) or not math.isfinite(v) or not a<=v<=b for v,a,b in zip(x,MINIMOS,MAXIMOS)):
            raise ValueError('Se requieren quince entradas válidas, completas y en rango.')
        return [(v-a)/(b-a) for v,a,b in zip(x,MINIMOS,MAXIMOS)]

    def adelante(self,valores):
        x=self.normalizar(valores)
        h=[math.tanh(sum(w*v for w,v in zip(f,x))+b) for f,b in zip(self.w[0],self.b[0])]
        y=[1/(1+math.exp(-max(-40,min(40,sum(w*v for w,v in zip(f,h))+b)))) for f,b in zip(self.w[1],self.b[1])]
        return x,h,y

    def exportar(self):
        return deepcopy(self._documento)
