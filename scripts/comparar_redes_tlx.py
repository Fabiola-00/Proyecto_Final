"""Entrena/compara 15-6-4 y 15-6-6-4 sin cambiar el modelo operativo."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import statistics
from time import perf_counter

from red_tlx_experimental import RedTlx, evaluar
from generar_datos_tlx_gse_miniipip import VARIABLES, validar
from etiquetar_datos_tlx_gse_miniipip import SALIDAS, puntuar

ROOT = Path(__file__).resolve().parents[1]
SEMILLAS = (31415, 7, 19, 43, 101, 211, 307, 401, 503, 607)


def guardar(p, objeto):
    p.write_text(json.dumps(objeto, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def distribucion(valores):
    return dict(media=statistics.mean(valores), desviacion=statistics.stdev(valores), minimo=min(valores), maximo=max(valores))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--salida', type=Path, default=ROOT/'output/comparacion_tlx_1564_15664_200_20261018')
    args = parser.parse_args()
    fuente = ROOT/'output/datos_etiquetados_tlx_gse_miniipip_200_20261018'
    for n, h in json.loads((fuente/'manifest.json').read_text()).items():
        if hashlib.sha256((fuente/n).read_bytes()).hexdigest() != h:
            raise ValueError('Fuente modificada: '+n)
    with (fuente/'datos.csv').open(newline='', encoding='utf-8') as f:
        originales = list(csv.DictReader(f))
    validar([dict(id=int(f['id']), origen=f['origen'], particion=f['particion'],
                  **{v[0]: float(f[v[0]]) for v in VARIABLES}) for f in originales])
    filas = [dict(id=int(f['id']), origen=f['origen'], particion=f['particion'],
                  entradas=[float(f[v[0]]) for v in VARIABLES], objetivos=[int(f[k]) for k in SALIDAS]) for f in originales]
    assert all(f['objetivos'] == puntuar(f['entradas']) for f in filas)
    grupos = {p: [f for f in filas if f['particion'] == p] for p in ('entrenamiento', 'validacion', 'prueba')}
    args.salida.mkdir(parents=True, exist_ok=False)
    for n in ('datos.csv', 'reglas.json'):
        (args.salida/n).write_bytes((fuente/n).read_bytes())
    protocolo = dict(arquitecturas=[[15, 6, 4], [15, 6, 6, 4]], parametros=[124, 166],
        semillas=SEMILLAS, particiones={p: len(g) for p, g in grupos.items()},
        hiperparametros=dict(epocas=300, paciencia=25, tasa=.03, l2=.001),
        seleccion_arquitectura='Menor media de BCE de validación entre diez semillas prefijadas.',
        seleccion_ejemplar='Menor BCE de validación dentro de cada arquitectura; no mediante prueba.',
        advertencia='Una sola partición de 200 datos generados y reglas didácticas. Semillas no son muestras independientes. Sin validación personal ni adopción automática.',
        sha256_datos=hashlib.sha256((fuente/'datos.csv').read_bytes()).hexdigest(),
        umbral_metricas=.5, abstencion='Global si cualquier salida cae estrictamente entre 0.35 y 0.65; no son probabilidades calibradas.')
    guardar(args.salida/'protocolo.json', protocolo)
    ejecuciones, redes = [], {}
    for ocultas in ((6,), (6, 6)):
        nombre = '-'.join(map(str, (15, *ocultas, 4)))
        carpeta = args.salida/nombre
        carpeta.mkdir()
        for semilla in SEMILLAS:
            red = RedTlx(ocultas, semilla)
            inicio = perf_counter()
            red.entrenar(grupos['entrenamiento'], grupos['validacion'], **protocolo['hiperparametros'])
            segundos = perf_counter()-inicio
            modelo = red.exportar()
            modelo['semilla_pesos'] = semilla
            modelo['datos_sha256'] = protocolo['sha256_datos']
            guardar(carpeta/f'modelo_semilla_{semilla}.json', modelo)
            r = dict(arquitectura=nombre, semilla=semilla, parametros=modelo['parametros'],
                epoca_elegida=red.entrenamiento['epoca_elegida'], epocas_ejecutadas=red.entrenamiento['epocas_ejecutadas'],
                segundos_entrenamiento=segundos, entrenamiento=evaluar(red, grupos['entrenamiento']),
                validacion=evaluar(red, grupos['validacion']))
            ejecuciones.append(r)
            redes[nombre, semilla] = red
            print(f'{nombre} semilla {semilla}: validación BCE={r["validacion"]["bce"]:.6f}', flush=True)
    nombres = ('15-6-4', '15-6-6-4')
    medias = {n: statistics.mean(r['validacion']['bce'] for r in ejecuciones if r['arquitectura'] == n) for n in nombres}
    preferida = min(nombres, key=lambda n: (medias[n], len(n)))
    ejemplares = {n: min((r for r in ejecuciones if r['arquitectura'] == n), key=lambda r: r['validacion']['bce'])['semilla'] for n in nombres}
    # Congelar selección ANTES de calcular cualquier métrica de prueba.
    seleccion = dict(arquitectura_recomendada=preferida, criterio=protocolo['seleccion_arquitectura'],
                     medias_bce_validacion=medias, semillas_ejemplares=ejemplares,
                     modelo_operativo_reemplazado=False)
    guardar(args.salida/'seleccion_por_validacion.json', seleccion)
    for r in ejecuciones:
        red = redes[r['arquitectura'], r['semilla']]
        r['prueba'] = evaluar(red, grupos['prueba'])
    resumen = {}
    for n in nombres:
        rs = [r for r in ejecuciones if r['arquitectura'] == n]
        resumen[n] = dict(parametros=rs[0]['parametros'],
            validacion_bce=distribucion([r['validacion']['bce'] for r in rs]),
            prueba_bce=distribucion([r['prueba']['bce'] for r in rs]),
            prueba_coincidencia=distribucion([r['prueba']['coincidencia_completa'] for r in rs]),
            prueba_f1_macro=distribucion([r['prueba']['f1_macro'] for r in rs]),
            prueba_abstenciones=distribucion([r['prueba']['abstenciones'] for r in rs]),
            segundos=distribucion([r['segundos_entrenamiento'] for r in rs]))
        for semilla, nombre_salida in ((31415, 'modelo_control_31415.json'), (ejemplares[n], 'modelo_ejemplar_validacion.json')):
            (args.salida/n/nombre_salida).write_bytes((args.salida/n/f'modelo_semilla_{semilla}.json').read_bytes())
    control = {n: next(r for r in ejecuciones if r['arquitectura'] == n and r['semilla'] == 31415) for n in nombres}
    guardar(args.salida/'resultados.json', dict(resumen=resumen, seleccion=seleccion, ejecuciones=ejecuciones))
    with (args.salida/'metricas.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(('arquitectura', 'semilla', 'parametros', 'epoca_elegida', 'validacion_bce', 'prueba_bce', 'prueba_aciertos_30', 'prueba_f1_macro', 'prueba_abstenciones_30'))
        w.writerows((r['arquitectura'], r['semilla'], r['parametros'], r['epoca_elegida'], r['validacion']['bce'], r['prueba']['bce'], r['prueba']['aciertos_completos'], r['prueba']['f1_macro'], r['prueba']['abstenciones']) for r in ejecuciones)
    with (args.salida/'predicciones.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(('arquitectura', 'semilla', 'id', 'particion', *('objetivo_'+s for s in SALIDAS), *('activacion_'+s for s in SALIDAS), 'abstencion'))
        for (n, semilla), red in redes.items():
            for fila in filas:
                y = red.adelante(fila['entradas'])[-1]
                w.writerow((n, semilla, fila['id'], fila['particion'], *fila['objetivos'], *y, int(any(.35 < v < .65 for v in y))))
    a, b = (resumen[n] for n in nombres)
    lineas = ['# Comparación 15 → 6 → 4 y 15 → 6 → 6 → 4', '',
        'Entrenamiento experimental sobre los mismos 200 Datos generados, con reglas de etiquetas V1; sin respuestas reales. No mide utilidad ni precisión sobre personas.', '',
        '## Protocolo', '',
        'Diez semillas pareadas por arquitectura: '+', '.join(map(str, SEMILLAS))+'. Misma partición 140/30/30, sin regenerar filas ni etiquetas. Normalización por rangos teóricos, tanh oculta, cuatro sigmoides independientes. SGD lote 1, orden 42, tasa 0,03, L2 0,001 solo en pesos; máximo 300 épocas, paciencia 25, mejora mínima 1e-6 y restauración de mejores pesos.', '',
        'BCE: suma de entropías cruzadas de cuatro salidas, promediada por caso, sin penalización L2 en la métrica. Menor es mejor. Selección por media de BCE de validación; ejemplar por menor BCE de validación dentro de cada arquitectura. Selección guardada antes de evaluar prueba.', '',
        '## Comparativo de diez inicializaciones', '',
        '| Medida | 15 → 6 → 4 | 15 → 6 → 6 → 4 |', '|---|---:|---:|',
        '| Parámetros | 124 | 166 |']
    for titulo, clave, porcentaje in [('BCE validación ↓', 'validacion_bce', False), ('BCE prueba ↓', 'prueba_bce', False),
             ('Coincidencia completa prueba ↑', 'prueba_coincidencia', True), ('F1 macro prueba ↑', 'prueba_f1_macro', True),
             ('Abstenciones / 30', 'prueba_abstenciones', False), ('Segundos entrenamiento', 'segundos', False)]:
        def fmt(r):
            v = r[clave]
            return f'{v["media"]:.2%} ± {v["desviacion"]:.2%}' if porcentaje else f'{v["media"]:.4f} ± {v["desviacion"]:.4f}'
        lineas.append(f'| {titulo} | {fmt(a)} | {fmt(b)} |')
    lineas += ['', 'Media ± desviación estándar muestral entre semillas; no intervalos de confianza ni diez conjuntos independientes.', '',
        '## Control con semilla 31415', '', '| Arquitectura | Época elegida / ejecutadas | BCE validación | Aciertos completos / 30 | Abstenciones / 30 |', '|---|---:|---:|---:|---:|']
    for n, r in control.items():
        lineas.append(f'| {n} | {r["epoca_elegida"]} / {r["epocas_ejecutadas"]} | {r["validacion"]["bce"]:.4f} | {r["prueba"]["aciertos_completos"]} | {r["prueba"]["abstenciones"]} |')
    lineas += ['', '## Selección y límites', '', f'**Arquitectura recomendada para este experimento: {preferida}**, por menor BCE media de validación. No se sustituye el modelo operativo.', '',
        'Ejemplares elegidos únicamente por validación: '+', '.join(f'{n}: semilla {s}' for n, s in ejemplares.items())+'. Se conservan todos los modelos y el control fijo 31415; no escoger semilla por aciertos de prueba.', '',
        'Coincidencia completa exige acertar las cuatro etiquetas simultáneamente con umbral 0,50. F1 macro promedia las cuatro salidas. Son métricas distintas de emisión de recomendaciones: cualquier activación entre 0,35 y 0,65 implica abstención global; las activaciones no son probabilidades calibradas.', '',
        'La mayor profundidad agrega 42 parámetros (+33,87%). Puede representar relaciones más complejas, pero aumenta costo y variabilidad; con 140 filas de entrenamiento no garantiza mejor generalización.', '',
        'Solo un reparto y 30 filas de prueba; etiquetas de reglas inventadas y distribución artificial. Las semillas estudian inicialización, no variabilidad de población. Comparación exploratoria; no demuestra eficacia clínica/institucional ni autoriza decisiones de personal. Una siguiente ronda que use esta prueba deberá declararla reutilizada.', '',
        'Pesos/modelos JSON por semilla; métricas, predicciones y huellas en esta carpeta. Sin SQLite, cambios de formularios ni inferencia sobre personas.', '',
        'Reproducir: `python scripts/comparar_redes_tlx.py --salida output/nueva_comparacion_tlx` (destino nuevo).']
    (args.salida/'README.md').write_text('\n'.join(lineas)+'\n', encoding='utf-8')
    guardar(args.salida/'manifest.json', {str(p.relative_to(args.salida)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(args.salida.rglob('*')) if p.is_file() and p.name != 'manifest.json'})
    print(json.dumps(dict(resumen=resumen, seleccion=seleccion), ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    main()
