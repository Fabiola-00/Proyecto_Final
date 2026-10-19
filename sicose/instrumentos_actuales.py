"""GSE española y Mini-IPIP equilibrado: versiones fijas y puntuación descriptiva.

GSE: Bäßler, Schwarzer y Jerusalem, 1993; referencia Bäßler/Schwarzer 1996.
https://userpage.fu-berlin.de/~health/spanscal.htm
Permiso de reproducción para estudios con atribución: FAQ de los autores.
Mini-IPIP: traducción Agustín Martínez-Molina, versión original con inversos.
https://ipip.ori.org/Spanishmini-IPIPposneg.htm (material IPIP de dominio público).
No se mezclan las columnas original y positiva ni se asignan categorías clínicas.
"""
import hashlib
from .modelo_anual import serializar

GSE_ITEMS = (
    'Puedo encontrar la manera de obtener lo que quiero aunque alguien se me oponga.',
    'Puedo resolver problemas difíciles si me esfuerzo lo suficiente.',
    'Me es fácil persistir en lo que me he propuesto hasta llegar a alcanzar mis metas.',
    'Tengo confianza en que podría manejar eficazmente acontecimientos inesperados.',
    'Gracias a mis cualidades y recursos puedo superar situaciones imprevistas.',
    'Cuando me encuentro en dificultades puedo permanecer tranquilo/a porque cuento con las habilidades necesarias para manejar situaciones difíciles.',
    'Venga lo que venga, por lo general soy capaz de manejarlo.',
    'Puedo resolver la mayoría de los problemas si me esfuerzo lo necesario.',
    'Si me encuentro en una situación difícil, generalmente se me ocurre qué debo hacer.',
    'Al tener que hacer frente a un problema, generalmente se me ocurren varias alternativas de cómo resolverlo.',
)
MINI_ITEMS = (
    'Soy el alma de la fiesta', 'Soy sensible hacia las emociones de otros',
    'Realizo mis tareas inmediatamente', 'Tengo frecuentes cambios de ánimo',
    'Tengo mucha imaginación', 'No hablo mucho',
    'No me interesan los problemas de otras personas',
    'A menudo olvido poner las cosas en su lugar',
    'Estoy relajado la mayor parte del tiempo', 'No estoy interesado en las ideas abstractas',
    'En las fiestas hablo con muchas personas', 'Siento las emociones de los otros',
    'Me gusta el orden', 'Me molesto fácilmente',
    'Tengo dificultad para entender ideas abstractas', 'Prefiero pasar desapercibido',
    'En realidad no estoy interesado en los demás', 'Soy desordenado',
    'Rara vez me siento triste', 'No tengo buena imaginación',
)
CATALOGO = {
    'GSE': dict(nombre='GSE · Autoeficacia general', version='GSE-Bassler-1993-es-V1',
        algoritmo='GSE-SUMA-10-40-V1', opciones=['Incorrecto', 'Apenas cierto', 'Más bien cierto', 'Cierto'],
        instrucciones='Lee cada afirmación y selecciona la opción que mejor describa tu percepción general de tu capacidad para afrontar dificultades.',
        fuente='https://userpage.fu-berlin.de/~health/spanscal.htm',
        atribucion='Judith Bäßler, Ralf Schwarzer y Matthias Jerusalem (1993). Adaptación española; Bäßler y Schwarzer (1996). Uso académico con atribución.', items=GSE_ITEMS),
    'MINIIPIP': dict(nombre='Mini-IPIP · Personalidad', version='MiniIPIP-MartinezMolina-2018-es-equilibrada-V1',
        algoritmo='MINIIPIP-SUMAS-INVERSOS-V1', opciones=['Nada de acuerdo', 'Algo de acuerdo', 'Medio acuerdo', 'Mucho acuerdo', 'Total acuerdo'],
        instrucciones='A continuación, se presenta una serie de frases cortas que describen cómo las personas se comportan generalmente. Léelas con atención y señala la alternativa de respuesta que mejor describa tu comportamiento en general. No hay respuestas correctas o incorrectas, y recuerda que los datos serán tratados con confidencialidad.',
        fuente='https://ipip.ori.org/Spanishmini-IPIPposneg.htm',
        atribucion='Mini-IPIP: Donnellan et al. (2006). Traducción de Agustín Martínez-Molina; Martínez-Molina y Arias (2018). Material IPIP de dominio público.', items=MINI_ITEMS),
}
POLITICA = ('Respuestas, resultados y recomendaciones se conservan vinculados a la Gestión, sin borrado automático. '
            'Administrador y Jefe de Personal consultan respuestas finalizadas y resultados; los avances no se les revelan. '
            'El Instructor recibe únicamente Completada al finalizar. Uso orientativo, sin diagnóstico ni decisiones automáticas de ascenso, sanción o aptitud operativa.')
SUBESCALAS = {
    'extraversion': (1, 6, 11, 16), 'amabilidad': (2, 7, 12, 17),
    'responsabilidad': (3, 8, 13, 18), 'neuroticismo': (4, 9, 14, 19),
    'apertura': (5, 10, 15, 20),
}
INVERSOS = {6, 7, 8, 9, 10, 15, 16, 17, 18, 19, 20}
TLX_DIMENSIONES = ('demanda_mental','demanda_fisica','demanda_temporal','rendimiento','esfuerzo','frustracion')
CATALOGO['NASATLX'] = dict(nombre='NASA-TLX · Carga de trabajo', version='NASA-TLX-es-SICOSE-adaptacion-V1',
    algoritmo='TLX-SEIS-DIMENSIONES-0-100-V1', opciones=[str(v) for v in range(0,101,5)],
    instrucciones='Responde solo después de participar en el simulacro común indicado. Valora tu experiencia en esa actividad de 0 a 100, en pasos de 5. Se conservan seis dimensiones por separado; no se calcula el índice ponderado original ni una categoría clínica.',
    fuente='https://www.nasa.gov/wp-content/uploads/2026/03/nasa-tlx-v1-0-searchable-text-and-forms.pdf',
    atribucion='NASA Ames, NASA-TLX. Adaptación al español para SICOSE basada en el manual; no se afirma validación de esta traducción. NASA permite uso y traducción sin autorización adicional. Revisión administrativa de ambos roles requerida.',
    items=('Demanda mental: ¿cuánta actividad mental y perceptiva requirió la tarea? 0 = baja; 100 = alta.',
           'Demanda física: ¿cuánta actividad física requirió la tarea? 0 = baja; 100 = alta.',
           'Demanda temporal: ¿cuánta presión de tiempo sentiste durante la tarea? 0 = baja; 100 = alta.',
           'Rendimiento: ¿cómo valoras el logro de los objetivos de la tarea? 0 = bueno; 100 = malo.',
           'Esfuerzo: ¿cuánto tuviste que esforzarte mental y físicamente para lograr tu rendimiento? 0 = bajo; 100 = alto.',
           'Frustración: ¿cuánta inseguridad, irritación o frustración sentiste durante la tarea? 0 = baja; 100 = alta.'))


def formulario(clave):
    if clave not in CATALOGO:
        raise LookupError('Prueba no encontrada.')
    f = CATALOGO[clave]
    resultado = {k: f[k] for k in ('nombre', 'version', 'algoritmo', 'instrucciones', 'fuente', 'atribucion')} | {
        'minimo_respuesta': 1, 'politica': POLITICA,
        'items': [{'texto': t, 'opciones': f['opciones']} for t in f['items']]}
    if clave == 'NASATLX':
        resultado.update(minimo_respuesta=0, paso_respuesta=5)
    return resultado


def firma(clave):
    return hashlib.sha256(serializar(formulario(clave)).encode()).hexdigest()


def validar(clave, respuestas, completa=False):
    f = CATALOGO[clave]
    if not isinstance(respuestas, list) or len(respuestas) != len(f['items']):
        raise ValueError('Cantidad de respuestas incorrecta.')
    if clave == 'NASATLX':
        if any((v is None and completa) or (v is not None and (type(v) is not int or not 0<=v<=100 or v%5)) for v in respuestas):
            raise ValueError('Responde las seis dimensiones con valores de 0 a 100 en pasos de 5.')
        return
    if any((v is None and completa) or (v is not None and
           (type(v) is not int or not 1 <= v <= len(f['opciones']))) for v in respuestas):
        raise ValueError('Responde todos los ítems con una opción válida.')


def puntuar(clave, respuestas):
    validar(clave, respuestas, True)
    if clave == 'GSE':
        return {'autoeficacia': {'valor': sum(respuestas), 'rango': [10, 40]}}
    if clave == 'NASATLX':
        return {k: {'valor': v, 'rango': [0,100]} for k,v in zip(TLX_DIMENSIONES,respuestas)}
    return {k: {'valor': sum(6-respuestas[i-1] if i in INVERSOS else respuestas[i-1] for i in indices),
                'rango': [4, 20]} for k, indices in SUBESCALAS.items()}
