"""Genera 200 casos GSE/Mini-IPIP y entrena 9→6→4; exclusivamente offline."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sicose.red_experimental import evaluar
from sicose.red_gse_miniipip import ENTRADAS, SALIDAS, REGLAS, RedGseMiniIpip, datos_sinteticos


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--salida', type=Path, default=Path('output/modelo_gse_miniipip_200_20261017'))
    args = parser.parse_args()
    args.salida.mkdir(parents=True, exist_ok=False)
    filas = datos_sinteticos()
    dataset = args.salida/'datos_sinteticos.csv'
    with dataset.open('w', newline='', encoding='utf-8') as archivo:
        w = csv.writer(archivo)
        w.writerow(('id', 'origen', 'particion', *ENTRADAS, *SALIDAS))
        w.writerows((f['id'], f['origen'], f['particion'], *f['entradas'], *f['objetivos']) for f in filas)
    grupos = {p: [f for f in filas if f['particion'] == p]
              for p in ('entrenamiento', 'validacion', 'prueba')}
    red = RedGseMiniIpip()
    red.entrenar(grupos['entrenamiento'], validacion=grupos['validacion'],
                 epocas=300, paciencia=25, l2=.001)
    evaluaciones = {}
    for p, grupo in grupos.items():
        resultado = evaluar(red, grupo)
        resultado['entropia_cruzada'] = red.perdida(grupo)
        resultado['por_salida'] = {}
        for i, nombre in enumerate(SALIDAS):
            vp = vn = fp = fn = 0
            for f in grupo:
                pred = int(red.adelante(f['entradas'])[2][i] >= .5)
                real = f['objetivos'][i]
                vp += pred == real == 1
                vn += pred == real == 0
                fp += pred == 1 and real == 0
                fn += pred == 0 and real == 1
            resultado['por_salida'][nombre] = dict(vp=vp, vn=vn, fp=fp, fn=fn,
                f1=2*vp/(2*vp+fp+fn) if 2*vp+fp+fn else 0)
        evaluaciones[p] = resultado
    informe = dict(estado='ENTRENADO_SOLO_SINTETICO', uso_en_personas=False,
        registros_totales=200, semillas=dict(datos=2718, pesos=31415, orden=42),
        arquitectura=[9, 6, 4], parametros=88, entrenamiento=red.entrenamiento,
        reglas_etiquetado=REGLAS, evaluaciones=evaluaciones,
        umbral_metricas=.5, umbrales_abstencion=[.35, .65],
        advertencia='Reproduce hipótesis inventadas. No estima prevalencias ni valida recomendaciones humanas; activaciones no calibradas.')
    for nombre, valor in (('modelo.json', red.exportar()), ('informe.json', informe)):
        (args.salida/nombre).write_text(json.dumps(valor, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    with (args.salida/'predicciones.csv').open('w', newline='', encoding='utf-8') as archivo:
        w = csv.writer(archivo)
        w.writerow(('id', 'particion', *('objetivo_'+s for s in SALIDAS),
                    *('activacion_'+s for s in SALIDAS), 'estado'))
        for f in filas:
            resultado = red.simular(f['entradas'])
            w.writerow((f['id'], f['particion'], *f['objetivos'],
                        *resultado['activaciones_no_calibradas'].values(), resultado['estado']))
    archivos = ('datos_sinteticos.csv', 'modelo.json', 'informe.json', 'predicciones.csv')
    manifest = dict(experimento='GSE_MINIIPIP_200_V1', uso_en_personas=False,
                    sha256={n: hashlib.sha256((args.salida/n).read_bytes()).hexdigest() for n in archivos})
    (args.salida/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    lineas = ['# Red experimental GSE + Mini-IPIP — 200 casos', '',
        'Modelo 9→6→4, 88 parámetros. Exclusivamente sintético, sin uso en personas.', '',
        'Entradas: '+', '.join(ENTRADAS)+'.', '', 'Salidas: '+', '.join(SALIDAS)+'.', '',
        '## Generación y significado', '',
        'Se simulan puntuaciones agregadas, no respuestas ni reactivos oficiales. GSE 10–40; cada suma Mini-IPIP 4–20. Todas las entradas se normalizan por su rango completo a 0–1.', '',
        'Muestreo uniforme independiente por rechazo y estratificación: 200 filas únicas, 16 combinaciones de etiquetas en cada partición, mitad de positivos por salida. No representa prevalencias ni correlaciones poblacionales.', '',
        'Reglas de etiquetado ficticias (valores normalizados):', '']
    lineas.extend('- **'+k+'**: '+v for k, v in REGLAS.items())
    lineas.extend(['', 'Estas ponderaciones NO constituyen una interpretación validada de personalidad. Las primeras tres salidas requieren además una nota institucional menor a 60; la cuarta requiere GSE normalizada menor a 0,50, corte inventado. Ningún rasgo aislado basta. GSE carece de corte universal.', '',
        '## Entrenamiento y evaluación', '',
        'Semillas fijas: datos 2718, pesos 31415, orden SGD 42. L2 0,001, tasa 0,03, máximo 300 épocas, paciencia 25. Se restaura la mejor pérdida de validación; la prueba no interviene en la selección.', '',
        f'Época elegida: {red.entrenamiento["epoca_elegida"]}; ejecutadas: {red.entrenamiento["epocas_ejecutadas"]}.', '',
        '| Partición | Casos | Coincidencia de las 4 etiquetas a umbral 0,5 | Abstenciones |',
        '|---|---:|---:|---:|'])
    for p, r in evaluaciones.items():
        lineas.append(f'| {p} | {r["n"]} | {r["coincidencia_completa"]:.2%} | {r["abstenciones"]} |')
    lineas.extend(['', 'La coincidencia anterior fuerza etiquetas a 0,5; no equivale a recomendaciones emitidas. La simulación se abstiene si alguna activación está entre 0,35 y 0,65. Las activaciones no son probabilidades calibradas.', '',
        'Los 200 casos sirven para verificar aprendizaje de reglas artificiales; no bastan para acreditar utilidad real. No comparar estas métricas directamente con DASS/CBI: cambiaron datos, etiquetas y significado.', '',
        '## Reproducir', '',
        'Desde la raíz, ejecutar con el Python existente: `python scripts/entrenar_red_gse_miniipip.py --salida output/nueva_ejecucion_gse`. El destino debe ser nuevo. No accede a SQLite, formularios, rutas ni personas.', '',
        'Se conservan íntegros el modelo DASS/CBI y sus comparaciones. Esta versión es el nuevo experimento solicitado; no se integra automáticamente en Flask.', '',
        'Fuentes de rangos y dimensiones: [GSE](https://userpage.fu-berlin.de/~health/faq_gse.pdf) y [Mini-IPIP en español](https://ipip.ori.org/Spanishmini-IPIPposneg.htm).', ''])
    (args.salida/'README.md').write_text('\n'.join(lineas), encoding='utf-8')
    print(json.dumps(informe, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
