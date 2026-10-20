# Aporte promedio de Operaciones — 2026-10-20

Decisión del solicitante: las notas de Operaciones se promedian, en lugar de sumarse. Aplicado al modelo anual V3 abierto. Ejemplo: 50 y 20 aportan 35. Académica conserva suma de cursos + promedio de operaciones, con tope 100.

Se incluye la última nota de cada operación calificada dentro del intervalo de la Gestión, excluyendo participaciones actualmente retiradas. Una operación pendiente no se convierte en cero; una nota registrada de cero sí participa en el denominador. Sin operaciones calificadas el aporte es cero y el estado permanece Pendiente. Se utiliza Fraction para conservar precisión durante el promedio y el tope; se mantiene el formato y tipo de los campos existentes. Se añaden criterio_operaciones=PROMEDIO_CALIFICADAS y operaciones_calificadas para identificar el criterio en el resumen.

Los cierres conservan sus resultados congelados. Publicaciones existentes permanecen intactas hasta republicación; reportes que usan notas publicadas mantienen esa misma regla. La consulta administrativa y el reporte individual de resultados vigentes reflejan el nuevo cálculo abierto. No se modifica SQLite v33, notas registradas, cursos ni pesos del modelo; no se reentrena la red ni se generan recomendaciones/publicaciones reales. La firma de recomendaciones utiliza el valor calculado y conserva su control de vigencia.

Archivos principales: sicose/modelo_anual.py y frontend/static/js/modelo_anual.js. El resumen muestra «promedio de calificadas» únicamente cuando está presente el nuevo criterio; una instantánea histórica sin ese campo conserva el rótulo genérico «aporte».

Verificación: conjunto de 30 regresiones en 70,130 s: 29 aprobadas y una diferencia de formato del cero inicial detectada (0 frente a 0.00). Se preservó el formato previo y se repitió esa prueba junto a la nueva prueba de publicación/corrección/republicación: dos aprobadas en 2,121 s. El conjunto incluye promedio 50/20=35, cero calificado, pendiente excluido, retiro/reingreso, cierre, panel y reporte por grado. No se afirma segunda ejecución completa del conjunto ni suite general. Sintaxis JavaScript y diff correctos.
