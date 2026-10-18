"""Genera 200 puntuaciones agregadas para experimentación offline, sin etiquetas."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import random


VARIABLES = (
    ('fisica', 'Físico promedio', 0, 100, .5),
    ('desempeno', 'Desempeño promedio', 0, 100, .5),
    ('academica', 'Académica acumulada con tope', 0, 100, 1),
    ('gse_autoeficacia', 'GSE: autoeficacia general', 10, 40, 1),
    ('mini_extraversion', 'Mini-IPIP: extraversión', 4, 20, 1),
    ('mini_amabilidad', 'Mini-IPIP: amabilidad', 4, 20, 1),
    ('mini_responsabilidad', 'Mini-IPIP: responsabilidad', 4, 20, 1),
    ('mini_neuroticismo', 'Mini-IPIP: neuroticismo', 4, 20, 1),
    ('mini_apertura', 'Mini-IPIP: apertura', 4, 20, 1),
    ('tlx_demanda_mental', 'NASA-TLX: demanda mental', 0, 100, 5),
    ('tlx_demanda_fisica', 'NASA-TLX: demanda física', 0, 100, 5),
    ('tlx_demanda_temporal', 'NASA-TLX: demanda temporal', 0, 100, 5),
    ('tlx_rendimiento', 'NASA-TLX: rendimiento percibido (0 bueno; 100 malo)', 0, 100, 5),
    ('tlx_esfuerzo', 'NASA-TLX: esfuerzo', 0, 100, 5),
    ('tlx_frustracion', 'NASA-TLX: frustración', 0, 100, 5),
)
SEMILLA = 20261018


def generar():
    """Cobertura marginal equilibrada; no supone correlaciones poblacionales."""
    rng = random.Random(SEMILLA)
    columnas = []
    for _, _, minimo, maximo, paso in VARIABLES:
        niveles = round((maximo-minimo)/paso)+1
        # Cada nivel aparece floor(200/niveles) o ceil(200/niveles) veces.
        indices = list(range(niveles))
        rng.shuffle(indices)
        valores = [minimo+indices[i % niveles]*paso for i in range(200)]
        rng.shuffle(valores)
        columnas.append(valores)
    particiones = ['entrenamiento']*140 + ['validacion']*30 + ['prueba']*30
    rng.shuffle(particiones)
    filas = [dict(id=i+1, origen='Datos', particion=particiones[i],
                  **{v[0]: columnas[j][i] for j, v in enumerate(VARIABLES)})
             for i in range(200)]
    validar(filas)
    return filas


def validar(filas):
    assert len(filas) == 200
    assert {f['id'] for f in filas} == set(range(1, 201))
    assert Counter(f['particion'] for f in filas) == dict(entrenamiento=140, validacion=30, prueba=30)
    assert len({tuple(f[v[0]] for v in VARIABLES) for f in filas}) == 200
    for f in filas:
        assert f['origen'] == 'Datos'
        for clave, _, minimo, maximo, paso in VARIABLES:
            valor = f[clave]
            assert minimo <= valor <= maximo
            assert abs((valor-minimo)/paso-round((valor-minimo)/paso)) < 1e-9


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--salida', type=Path, default=Path('output/datos_tlx_gse_miniipip_200_20261018'))
    args = parser.parse_args()
    filas = generar()
    args.salida.mkdir(parents=True, exist_ok=False)
    ruta = args.salida/'datos.csv'
    with ruta.open('w', newline='', encoding='utf-8') as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)
    with ruta.open(newline='', encoding='utf-8') as archivo:
        leidas = list(csv.DictReader(archivo))
    assert len(leidas) == 200 and all(len(f) == 18 for f in leidas)
    resumen = dict(titulo='Datos NASA-TLX, GSE y Mini-IPIP', origen='Datos',
        procedencia='Generación computacional de puntuaciones agregadas para experimentación; no son observaciones ni respuestas de personas reales.',
        semilla=SEMILLA, registros=200, entradas=15,
        metodo='Cobertura marginal equilibrada de niveles discretos, con permutaciones independientes. No representa prevalencias ni correlaciones empíricas.',
        particiones=dict(Counter(f['particion'] for f in filas)),
        etiquetas='Pendientes de definir nuevas salidas y reglas explícitas; no se reutilizan las anteriores.',
        entrenamiento_realizado=False, uso_en_personas=False,
        contexto_tlx='Una aplicación por Gestión después de práctica o simulacro común. No se inventa una práctica, fecha ni Gestión real.',
        tlx='Seis valoraciones sin ponderar por separado; sin comparaciones por pares ni índice global ponderado.',
        normalizacion='Futuro modelo: (valor-minimo)/(maximo-minimo); CSV conserva escala original.',
        variables=[dict(clave=k, descripcion=d, minimo=lo, maximo=hi, paso=p,
                        observado_min=min(f[k] for f in filas), observado_max=max(f[k] for f in filas))
                   for k, d, lo, hi, p in VARIABLES],
        fuentes=['https://www.nasa.gov/wp-content/uploads/2026/03/nasa-tlx-v1-0-searchable-text-and-forms.pdf',
                 'https://userpage.fu-berlin.de/~health/spanscal.htm',
                 'https://ipip.ori.org/Spanishmini-IPIPposneg.htm'])
    (args.salida/'diccionario.json').write_text(json.dumps(resumen, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    lineas = ['# Datos NASA-TLX, GSE y Mini-IPIP', '',
        '200 registros nuevos, 15 entradas, origen visible **Datos**. Puntuaciones generadas por computadora para experimentación; no proceden de personas reales.', '',
        '## Alcance', '',
        'Una aplicación NASA-TLX por Gestión después de una práctica o simulacro común. El conjunto no se vincula a usuarios, fechas, prácticas ni gestiones reales. Solo puntuaciones agregadas, sin reactivos ni respuestas individuales.', '',
        'No hay etiquetas: el solicitante decidió definir nuevas salidas antes de entrenar. Este conjunto aún no permite entrenamiento supervisado. No se ha entrenado ni sustituido el modelo vigente ni cambiado formularios o SQLite.', '',
        '## Variables', '', '| Variable | Rango | Paso |', '|---|---:|---:|']
    lineas += [f'| {k}: {d} | {lo}–{hi} | {p} |' for k, d, lo, hi, p in VARIABLES]
    lineas += ['', 'NASA-TLX usa seis valoraciones individuales 0–100 en pasos de 5. Rendimiento conserva el sentido del formulario: 0 bueno, 100 malo; las demás van de baja a alta demanda/esfuerzo/frustración. No se calcula el índice ponderado original ni se inventan pesos.', '',
        '## Generación y verificación', '',
        'Semilla 20261018. Cobertura marginal equilibrada y permutaciones independientes. Muestreo de rangos posibles, sin asumir distribución, correlación o prevalencia real. Las combinaciones extremas son deliberadas para ensayar límites, no perfiles de una población.', '',
        'Partición preliminar fija 140 entrenamiento / 30 validación / 30 prueba. Sin estratificación por salidas todavía inexistentes; revisar cobertura de etiquetas antes de entrenar y documentar cualquier cambio de versión. No consultar prueba para elegir reglas, arquitectura o pesos.', '',
        'Verificado: 200 filas únicas, 15 valores completos por fila, IDs únicos, rangos, pasos y particiones. Normalización futura por rangos teóricos, no por mínimos/máximos observados.', '',
        'Reproducir desde la raíz: `python scripts/generar_datos_tlx_gse_miniipip.py --salida output/nueva_carpeta_datos`. Se exige destino nuevo.', '',
        '## Fuentes', '']
    lineas += [f'- {url}' for url in resumen['fuentes']]
    (args.salida/'README.md').write_text('\n'.join(lineas)+'\n', encoding='utf-8')
    manifiesto = {n: hashlib.sha256((args.salida/n).read_bytes()).hexdigest()
                  for n in ('datos.csv', 'diccionario.json', 'README.md')}
    (args.salida/'manifest.json').write_text(json.dumps(manifiesto, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(registros=200, entradas=15, particiones=resumen['particiones'],
                         etiquetas='pendientes', salida=str(args.salida)), ensure_ascii=False))


if __name__ == '__main__':
    main()
