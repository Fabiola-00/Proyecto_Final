"""Claves numéricas candidatas; no incluye reactivos ni interpretación clínica."""
from fractions import Fraction

CATALOGO = {
    'DASS21': {'nombre': 'DASS-21', 'version': 'Daza-2002-es-candidata', 'cantidad': 21,
               'maximo_respuesta': 3, 'algoritmo': 'DASS21-SUMA-X2-V1'},
    'CBI': {'nombre': 'CBI', 'version': 'Molinero-2013-es-candidata', 'cantidad': 19,
            'maximo_respuesta': 4, 'algoritmo': 'CBI-MEDIA-INVERSION13-V1'},
}


def validar_respuestas(clave, respuestas, completa=False):
    ficha = CATALOGO[clave]
    if not isinstance(respuestas, list) or len(respuestas) != ficha['cantidad']:
        raise ValueError('Cantidad de respuestas incorrecta.')
    if any((v is None and completa) or (v is not None and
           (type(v) is not int or not 0 <= v <= ficha['maximo_respuesta'])) for v in respuestas):
        raise ValueError('Responde todos los ítems aplicables con una opción válida.')


def puntuar(clave, respuestas):
    validar_respuestas(clave, respuestas, completa=True)
    if clave == 'DASS21':
        grupos = {'depresion': (3, 5, 10, 13, 16, 17, 21),
                  'ansiedad': (2, 4, 7, 9, 15, 19, 20),
                  'estres': (1, 6, 8, 11, 12, 14, 18)}
        return {k: {'suma': sum(respuestas[i-1] for i in indices),
                    'valor': 2 * sum(respuestas[i-1] for i in indices), 'rango': [0, 42]}
                for k, indices in grupos.items()}
    # Codificación canónica: 0=menor frecuencia/intensidad, 4=mayor.
    # El ítem global 13 (energía disponible) tiene dirección inversa.
    valores = [25 * (4-v if i == 12 else v) for i, v in enumerate(respuestas)]
    grupos = {'personal': valores[:6], 'trabajo': valores[6:13], 'personas': valores[13:]}
    return {k: {'valor': float(Fraction(sum(v), len(v))), 'numerador': sum(v),
                'denominador': len(v), 'rango': [0, 100]} for k, v in grupos.items()}
