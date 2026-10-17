"""Compara 9→6→4 con una alternativa de dos capas sobre el mismo CSV sintético."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import statistics
import sys
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sicose.red_experimental import ENTRADAS, SALIDAS, RedExperimental, RedDosCapas, evaluar
from sicose.red_gse_miniipip import (ENTRADAS as ENTRADAS_GSE, SALIDAS as SALIDAS_GSE,
                                   RedGseMiniIpip, RedGseMiniIpipDosCapas)

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'output/modelo_sintetico_200_20261017'
SEMILLAS = (31415, 7, 19, 43, 101, 211, 307, 401, 503, 607)


def cargar_datos(perfil='dass-cbi'):
    base = BASE if perfil == 'dass-cbi' else ROOT/'output/modelo_gse_miniipip_200_20261017'
    entradas, salidas = (ENTRADAS, SALIDAS) if perfil == 'dass-cbi' else (ENTRADAS_GSE, SALIDAS_GSE)
    archivo = base/'datos_sinteticos.csv'
    huella = hashlib.sha256(archivo.read_bytes()).hexdigest()
    original = json.loads((base/'informe.json').read_text(encoding='utf-8'))
    if perfil == 'gse-miniipip':
        manifest = json.loads((base/'manifest.json').read_text(encoding='utf-8'))
        for nombre, esperado in manifest['sha256'].items():
            if hashlib.sha256((base/nombre).read_bytes()).hexdigest() != esperado:
                raise ValueError('Artefacto GSE/Mini-IPIP modificado: '+nombre)
        esperado = manifest['sha256']['datos_sinteticos.csv']
    else:
        esperado = original['datos_sha256']
    if huella != esperado:
        raise ValueError('El CSV no coincide con el experimento base.')
    with archivo.open(encoding='utf-8', newline='') as f:
        filas = [{'id': int(r['id']), 'origen': r['origen'], 'particion': r['particion'],
                  'entradas': [float(r[k]) for k in entradas], 'objetivos': [int(r[k]) for k in salidas]}
                 for r in csv.DictReader(f)]
    if (len(filas) != 200 or len({r['id'] for r in filas}) != 200 or
            len({tuple(r['entradas']) for r in filas}) != 200 or
            any(r['origen'] != 'SINTETICO' for r in filas)):
        raise ValueError('Se requieren los mismos 200 casos sintéticos, disjuntos y sin duplicados.')
    partes = {k: [r for r in filas if r['particion'] == k] for k in ('entrenamiento', 'validacion', 'prueba')}
    if [len(v) for v in partes.values()] != [140, 30, 30]:
        raise ValueError('Particiones diferentes del experimento base.')
    return archivo, huella, partes, original


def distribucion(valores):
    return {'media': statistics.mean(valores), 'desviacion': statistics.stdev(valores),
            'minimo': min(valores), 'maximo': max(valores)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--salida', type=Path, default=ROOT/'output/comparacion_redes_200_20261017')
    p.add_argument('--semillas', type=int, nargs='+', default=list(SEMILLAS))
    p.add_argument('--alternativa', choices=('9-8-4-4', '9-6-4-4'), default='9-8-4-4')
    p.add_argument('--perfil', choices=('dass-cbi', 'gse-miniipip'), default='dass-cbi')
    args = p.parse_args()
    if len(args.semillas) < 2 or len(set(args.semillas)) != len(args.semillas):
        p.error('Indica al menos dos semillas diferentes.')
    if args.perfil == 'gse-miniipip' and args.alternativa != '9-6-4-4':
        p.error('El perfil GSE/Mini-IPIP solo implementa la alternativa solicitada 9-6-4-4.')
    archivo, huella, partes, original = cargar_datos(args.perfil)
    base = archivo.parent
    args.salida.mkdir(parents=True, exist_ok=False)
    (args.salida/'datos_sinteticos.csv').write_bytes(archivo.read_bytes())
    alternativa = args.alternativa
    arquitecturas = ('9-6-4', alternativa)
    ocultas = (8, 4) if alternativa == '9-8-4-4' else (6, 4)
    protocolo = {'registros': 200, 'arquitecturas': list(arquitecturas), 'particiones': {k: len(v) for k, v in partes.items()},
        'datos_sha256': huella, 'semillas_pesos': args.semillas, 'semilla_orden': 42,
        'hiperparametros': {'epocas': 300, 'tasa': .03, 'l2': .001, 'paciencia': 25},
        'seleccion_pesos': 'Menor entropía cruzada de validación por ejecución; restaura pesos.',
        'comparacion_principal': 'Media de entropía cruzada de validación entre semillas prefijadas.',
        'limitaciones': ['Mismos 200 registros y misma prueba de 30 casos ya consultada: comparación exploratoria.',
                        'Varias inicializaciones no representan conjuntos independientes de personas o datos.',
                        'Etiquetas sintéticas de reglas inventadas, sin validez clínica o institucional.',
                        'No se selecciona semilla, arquitectura ni hiperparámetros mediante prueba.',
                        'No se sustituye automáticamente el modelo base.']}
    ejecuciones = []
    mejores = {}
    if args.perfil == 'gse-miniipip':
        protocolo['perfil'] = args.perfil
    for nombre in arquitecturas:
        carpeta = args.salida/nombre; carpeta.mkdir()
        for semilla in args.semillas:
            if args.perfil == 'gse-miniipip':
                red = RedGseMiniIpip(semilla=semilla) if nombre == '9-6-4' else RedGseMiniIpipDosCapas(semilla=semilla)
            else:
                red = RedExperimental(semilla=semilla) if nombre == '9-6-4' else RedDosCapas(semilla=semilla, ocultas=ocultas)
            inicio = perf_counter()
            red.entrenar(partes['entrenamiento'], validacion=partes['validacion'], **protocolo['hiperparametros'])
            segundos = perf_counter()-inicio
            # Reproducción exacta del modelo existente antes de interpretar diferencias.
            if nombre == '9-6-4' and semilla == 31415:
                modelo_base = json.loads((base/'modelo.json').read_text(encoding='utf-8'))
                assert red.exportar()['pesos'] == modelo_base['pesos'], 'El control no reproduce los pesos base.'
                assert all(original['evaluaciones']['prueba'][k] == v
                           for k, v in evaluar(red, partes['prueba']).items())
            medidas = {k: {**evaluar(red, filas), 'perdida': red.perdida(filas)} for k, filas in partes.items()}
            pesos = red.exportar()['pesos']
            parametros = sum(sum(len(f) for f in v) if k.startswith('w') else len(v) for k, v in pesos.items())
            r = {'arquitectura': nombre, 'semilla': semilla, 'parametros': parametros,
                 'segundos_entrenamiento': segundos, 'entrenamiento': red.entrenamiento, 'evaluaciones': medidas}
            ejecuciones.append(r)
            (carpeta/f'modelo_semilla_{semilla}.json').write_text(json.dumps(red.exportar(), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
            anterior = mejores.get(nombre)
            if anterior is None or medidas['validacion']['perdida'] < anterior['perdida_validacion']:
                mejores[nombre] = {'semilla': semilla, 'perdida_validacion': medidas['validacion']['perdida']}
    resumen = {}
    for nombre in arquitecturas:
        grupo = [r for r in ejecuciones if r['arquitectura'] == nombre]
        resumen[nombre] = {'parametros': grupo[0]['parametros'], 'ejecuciones': len(grupo),
            'segundos_entrenamiento': distribucion([r['segundos_entrenamiento'] for r in grupo]),
            'epoca_elegida': distribucion([r['entrenamiento']['epoca_elegida'] for r in grupo]),
            'evaluaciones': {k: {metrica: distribucion([r['evaluaciones'][k][metrica] for r in grupo])
                for metrica in ('coincidencia_completa', 'perdida', 'abstenciones')} for k in partes}}
    comparacion = {}
    for parte in partes:
        diferencias = [next(r for r in ejecuciones if r['arquitectura'] == alternativa and r['semilla'] == s)['evaluaciones'][parte]['coincidencia_completa'] -
                       next(r for r in ejecuciones if r['arquitectura'] == '9-6-4' and r['semilla'] == s)['evaluaciones'][parte]['coincidencia_completa'] for s in args.semillas]
        comparacion[parte] = {**distribucion(diferencias), 'profunda_supera': sum(d > 0 for d in diferencias),
                             'empates': sum(d == 0 for d in diferencias), 'simple_supera': sum(d < 0 for d in diferencias)}
    favorecida = min(resumen, key=lambda k: resumen[k]['evaluaciones']['validacion']['perdida']['media'])
    informe = {'protocolo': protocolo, 'resumen': resumen, 'diferencias_pareadas_coincidencia': comparacion,
               'favorecida_por_criterio_principal': favorecida, 'mejores_semillas_por_validacion': mejores,
               'ejecuciones': ejecuciones, 'modelo_base_sustituido': False}
    (args.salida/'comparacion.json').write_text(json.dumps(informe, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    with (args.salida/'ejecuciones.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(('arquitectura', 'semilla', 'parametros', 'epoca_elegida', 'segundos',
                                      'perdida_validacion', 'coincidencia_validacion', 'coincidencia_prueba', 'abstenciones_prueba'))
        for r in ejecuciones:
            w.writerow((r['arquitectura'], r['semilla'], r['parametros'], r['entrenamiento']['epoca_elegida'], r['segundos_entrenamiento'],
                        r['evaluaciones']['validacion']['perdida'], r['evaluaciones']['validacion']['coincidencia_completa'],
                        r['evaluaciones']['prueba']['coincidencia_completa'], r['evaluaciones']['prueba']['abstenciones']))
    print(json.dumps({'resumen': resumen, 'diferencias': comparacion, 'favorecida_por_validacion': favorecida}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
