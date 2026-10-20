# Académica: Asistencia, Cursos y Operaciones — 2026-10-20

Decisiones confirmadas por el solicitante:

- Académica = (Nota Asistencia + Nota Cursos y Capacitaciones + Nota Operaciones) / 3.
- Asistencia es el porcentaje propio de la Gestión entre 0 y 100. Sin registros computables, incluidos solo Permisos, aporta cero.
- Cursos suma las notas de participaciones finalizadas que integran el cálculo de la Gestión, con tope de 100 antes de promediar.
- Operaciones conserva el promedio de las últimas notas calificadas y vigentes, excluyendo participaciones retiradas; pendientes fuera del denominador, cero registrado incluido.

Ejemplo: Asistencia 75 + Cursos acumulados 160 (nota 100) + Operaciones 50 y 20 (nota 35): Académica = 70. Promedio con precisión racional; porcentaje de asistencia con los dos decimales del indicador existente. Se conserva el bloqueo por habilitación de Académica.

## Presentación

Cuatro tarjetas separadas con margen, borde superior y título: Asistencia - Gestión <año de inicio>, Cursos y Capacitaciones - Gestión <año>, Operaciones - Gestión <año>, Resumen de Académica. Gráfico y tablas conservados. Total de cada componente en negrita debajo de su contenido. La asistencia muestra su porcentaje total; explicación de cálculo en icono de información con title al acercar el mouse y nombre accesible. El resumen muestra los tres valores, la división por tres y la nota final. Sin inventar año o registros fuera del intervalo seleccionado.

Campos adicionales en academica: criterio_academica=PROMEDIO_ASISTENCIA_CURSOS_OPERACIONES_V1, aporte_asistencia, aporte_cursos, cursos_sin_tope y asistencia. puntos_sin_tope contiene la suma de los tres componentes antes de dividir. La publicación conserva en fuentes el criterio y conteo de asistencia; no se publican automáticamente los cambios. Las publicaciones anteriores y sus notas de reporte por grado permanecen hasta republicación explícita. Cierres conservan la instantánea y regla original; la interfaz no los rotula como cálculo nuevo. Reporte individual identifica el promedio nuevo cuando corresponde.

Sin migración (SQLite v33), cambios de entorno, notas registradas ni pesos de red; no se crean publicaciones o respuestas reales.

## Verificación

35 regresiones finales aprobadas en 87,253 s, log .tmp/academica-tres-notas-final.log: nuevos tres componentes/tope, periodo, solo Permisos, publicación estable ante corrección de asistencia, modelo anual, cierre, reingresos, panel del Instructor y PDF individual. Primer conjunto: 34 aprobadas y una expectativa del cálculo previo corregida antes de repetir los 35. Sin suite general.

Datos sintéticos aislados: recorrido administrativo de los cuatro bloques en oscuro y claro, totales 75/100/35 y resultado 70 verificados en DOM y capturas inspeccionadas. La primera conexión al servidor sintético fue bloqueada por el entorno; servidor aislado relanzado y recorrido completado. No se modificó la sesión operativa del usuario. Sintaxis JavaScript y diff correctos. No se afirma matriz exhaustiva de tamaños/roles ni interacción táctil del tooltip.
