"""Etiqueta las 200 filas existentes con reglas didácticas explícitas, sin entrenar."""
import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path

from generar_datos_tlx_gse_miniipip import VARIABLES, validar

ROOT = Path(__file__).resolve().parents[1]
SALIDAS = (
    'preparacion_progresiva_y_confianza',
    'organizacion_de_tareas_y_manejo_de_carga',
    'comunicacion_y_aprendizaje_acompanado',
    'afrontamiento_y_seguimiento_del_bienestar',
)
TITULOS = (
    'Preparación progresiva y confianza',
    'Organización de tareas y manejo de la carga',
    'Comunicación y aprendizaje acompañado',
    'Afrontamiento y seguimiento del bienestar',
)
REGLAS = (
    ('F < 0.60 o PF >= 0.60', '0.45*(1-F) + 0.20*(1-G) + 0.25*PF + 0.10*EF'),
    ('M >= 0.60 o T >= 0.60 o R >= 0.60', '0.30*M + 0.30*T + 0.20*R + 0.10*EF + 0.10*(1-C)'),
    ('D < 0.60 o AC < 0.60', '0.30*(1-D) + 0.25*(1-AC) + 0.15*(1-G) + 0.10*(1-E) + 0.10*(1-A) + 0.10*(1-O)'),
    ('FR >= 0.60 o EF >= 0.60', '0.35*FR + 0.20*EF + 0.20*(1-G) + 0.15*N + 0.10*(1-C)'),
)


def puntuar(valores):
    if len(valores) != 15:
        raise ValueError('Se requieren quince entradas completas.')
    for v, (_, _, lo, hi, _) in zip(valores, VARIABLES):
        if type(v) not in (int, float) or not math.isfinite(v) or not lo <= v <= hi:
            raise ValueError('Entrada no numérica, ausente o fuera de rango.')
    f, d, ac, g, e, a, c, n, o, m, pf, t, r, ef, fr = [
        (v-lo)/(hi-lo) for v, (_, _, lo, hi, _) in zip(valores, VARIABLES)]
    condiciones = (f < .6 or pf >= .6, m >= .6 or t >= .6 or r >= .6,
                   d < .6 or ac < .6, fr >= .6 or ef >= .6)
    indices = (.45*(1-f)+.20*(1-g)+.25*pf+.10*ef,
               .30*m+.30*t+.20*r+.10*ef+.10*(1-c),
               .30*(1-d)+.25*(1-ac)+.15*(1-g)+.10*(1-e)+.10*(1-a)+.10*(1-o),
               .35*fr+.20*ef+.20*(1-g)+.15*n+.10*(1-c))
    return [int(cond and indice >= .5) for cond, indice in zip(condiciones, indices)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--entrada', type=Path, default=ROOT/'output/datos_tlx_gse_miniipip_200_20261018')
    parser.add_argument('--salida', type=Path, default=ROOT/'output/datos_etiquetados_tlx_gse_miniipip_200_20261018')
    args = parser.parse_args()
    origen = args.entrada/'datos.csv'
    for nombre, huella in json.loads((args.entrada/'manifest.json').read_text()).items():
        if hashlib.sha256((args.entrada/nombre).read_bytes()).hexdigest() != huella:
            raise ValueError('El conjunto de entrada cambió: '+nombre)
    with origen.open(newline='', encoding='utf-8') as f:
        filas = list(csv.DictReader(f))
    base = [dict(id=int(f['id']), origen=f['origen'], particion=f['particion'],
                 **{v[0]: float(f[v[0]]) for v in VARIABLES}) for f in filas]
    validar(base)
    # No se seleccionan reglas a partir de los resultados ni se remuestrean filas.
    etiquetadas = [dict(f, **dict(zip(SALIDAS, puntuar([float(f[v[0]]) for v in VARIABLES])))) for f in filas]
    args.salida.mkdir(parents=True, exist_ok=False)
    with (args.salida/'datos.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(etiquetadas[0]))
        w.writeheader()
        w.writerows(etiquetadas)
    reglas = dict(version='TLX_GSE_MINIIPIP_ETIQUETAS_V1',
        naturaleza='HIPOTESIS_DIDACTICAS_NO_VALIDADAS',
        procedencia='Datos generados por computadora; etiquetas calculadas mediante reglas propuestas para experimentar, sin evaluaciones humanas.',
        proposito='Líneas de apoyo combinables, sin diagnóstico, ascensos, sanciones ni aptitud automática.',
        normalizacion='(valor-minimo)/(maximo-minimo), según rangos teóricos del diccionario original.',
        leyenda='F=fisica,D=desempeno,AC=academica,G=GSE,E=extraversion,A=amabilidad,C=responsabilidad,N=neuroticismo,O=apertura,M=demanda mental,PF=demanda fisica,T=demanda temporal,R=rendimiento TLX (alto=malo),EF=esfuerzo,FR=frustracion.',
        interpretacion='1: línea de apoyo propuesta por regla; 0: esa regla no propone la línea, no acredita bienestar ni capacidad. Cuatro ceros: seguimiento general. Varios unos: apoyos combinables.',
        limites='Pesos, condiciones y umbral 0.50 inventados para ensayo, no baremos ni cortes de los instrumentos. Rasgos de personalidad no activan por sí solos una salida. No implican causalidad. Carga alta puede responder a la tarea o a su organización.',
        salidas=[dict(clave=k, titulo=titulo, condicion=cond, indice=indice,
                      etiqueta='1 si se cumple la condición y el índice >= 0.50; 0 en otro caso')
                 for k, titulo, (cond, indice) in zip(SALIDAS, TITULOS, REGLAS)])
    (args.salida/'reglas.json').write_text(json.dumps(reglas, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    # Informe por entrenamiento/validación; prueba se mantiene sin explorar.
    cobertura = {}
    for p in ('entrenamiento', 'validacion'):
        grupo = [f for f in etiquetadas if f['particion'] == p]
        cobertura[p] = dict(n=len(grupo), positivos={k: sum(f[k] for f in grupo) for k in SALIDAS},
            patrones=dict(Counter(''.join(str(f[k]) for k in SALIDAS) for f in grupo)))
        assert all(0 < sum(f[k] for f in grupo) < len(grupo) for k in SALIDAS)
    informe = dict(registros=200, entradas=15, salidas=4,
        particiones=dict(Counter(f['particion'] for f in filas)),
        cobertura=cobertura, prueba='Reservada; etiquetas aplicadas sin explorar distribución ni resultados.',
        entrenamiento_realizado=False, modelo_operativo_modificado=False,
        sha256_entrada=hashlib.sha256(origen.read_bytes()).hexdigest(),
        verificacion='200 IDs/entradas/particiones conservados; cuatro etiquetas binarias por fila. Sin remuestreo ni balance artificial por etiquetas.')
    (args.salida/'informe.json').write_text(json.dumps(informe, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    lineas = ['# Datos etiquetados NASA-TLX, GSE y Mini-IPIP', '',
        '200 filas originales conservadas, 15 entradas y cuatro etiquetas binarias combinables. Origen visible: Datos. Son puntuaciones generadas por computadora, sin observaciones reales.', '',
        '## Reglas V1', '',
        'Todas las variables se normalizan por sus rangos teóricos. Cada salida exige una condición contextual y un índice >= 0,50. Pesos/cortes son hipótesis didácticas inventadas, no interpretaciones validadas de los instrumentos.', '', reglas['leyenda'], '']
    for titulo, (cond, indice) in zip(TITULOS, REGLAS):
        lineas += [f'### {titulo}', '', f'- Condición: `{cond}`.', f'- Índice: `{indice}`.', '']
    lineas += [reglas['interpretacion'], '', reglas['limites'], '',
        '## Conservación y estado', '',
        'No se regeneran datos ni se cambian particiones. 140 entrenamiento / 30 validación / 30 prueba. La regla se aplica igual a las tres; solo se resume la cobertura de entrenamiento/validación, manteniendo prueba sin explorar.', '',
        'No hay entrenamiento, métricas nuevas ni integración en Flask o SQLite. El modelo vigente 9→6→4 sigue intacto. La aprobación de las cuatro salidas no acredita validez de estas reglas ni recomendaciones personales.', '',
        'Reproducir: `python scripts/etiquetar_datos_tlx_gse_miniipip.py --salida output/nueva_carpeta_etiquetada`. Se exige carpeta nueva. Ver reglas.json e informe.json.']
    (args.salida/'README.md').write_text('\n'.join(lineas)+'\n', encoding='utf-8')
    manifest = {n: hashlib.sha256((args.salida/n).read_bytes()).hexdigest()
                for n in ('datos.csv', 'reglas.json', 'informe.json', 'README.md')}
    (args.salida/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(informe, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
