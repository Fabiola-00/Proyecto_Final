"""Genera 200 casos y entrena una red compacta fuera de Flask/SQLite. Solo simulación."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sicose.red_experimental import ENTRADAS, SALIDAS, RedExperimental, datos_sinteticos, evaluar


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--salida', type=Path, default=Path('output/modelo_sintetico_200'))
    p.add_argument('--epocas', type=int, default=300, help='Máximo; se restaura la mejor época de validación.')
    args = p.parse_args()
    if not 1 <= args.epocas <= 1000:
        p.error('Épocas entre 1 y 1000.')
    # Cada ejecución tiene carpeta propia; nunca sobrescribir un artefacto revisado.
    args.salida.mkdir(parents=True, exist_ok=False)
    filas = datos_sinteticos()
    dataset = args.salida/'datos_sinteticos.csv'
    with dataset.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(('id', 'origen', 'particion', *ENTRADAS, *SALIDAS))
        w.writerows((v['id'], v['origen'], v['particion'], *v['entradas'], *v['objetivos']) for v in filas)
    red = RedExperimental()
    red.entrenar([f for f in filas if f['particion'] == 'entrenamiento'], epocas=args.epocas,
                 validacion=[f for f in filas if f['particion'] == 'validacion'], paciencia=25, l2=.001)
    informe = {'estado': 'ENTRENADO_SOLO_SINTETICO', 'semillas': [2718, 31415, 42],
               'registros_totales': len(filas), 'arquitectura': red.exportar()['arquitectura'],
               'parametros': sum(len(w) for w in red.w1+red.w2)+len(red.b1)+len(red.b2),
               'entrenamiento': red.entrenamiento,
               'datos_sha256': hashlib.sha256(dataset.read_bytes()).hexdigest(),
               'umbral_didactico': .6, 'umbrales_abstencion': [.35, .65],
               'advertencia': 'Los objetivos provienen de reglas inventadas, no de profesionales ni recomendaciones históricas.',
               'evaluaciones': {k: evaluar(red, [f for f in filas if f['particion'] == k])
                                for k in ('entrenamiento', 'validacion', 'prueba')}}
    for nombre, valor in [('modelo.json', red.exportar()), ('informe.json', informe)]:
        (args.salida/nombre).write_text(json.dumps(valor, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(informe, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
