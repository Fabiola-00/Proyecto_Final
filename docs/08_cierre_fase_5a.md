# 08. Cierre técnico de Fase 5A — Seguimiento operativo

Fecha de verificación: **2026-10-11**. Estado: **cierre técnico cumplido; aceptación operativa del solicitante pendiente**. Este documento registra verificaciones automatizadas y revisión visual con datos sintéticos; no declara aprobación institucional ni preparación del piloto.

## Objetivo, alcance y límites

Verificar notas manuales e historial, cursos/historial personal y asistencia/calendario/PDF dentro de los permisos ya aprobados. Sin cambios de roles, esquema (v14), entorno, base local ni reglas de puntuación institucional. Las notas siguen entre 0 y 100; no se crean promedios oficiales, ponderaciones ni psicometría.

El catálogo común de cursos sigue separado de las capacitaciones personales; no se añadió interfaz de asignación de personas. Sus APIs existentes e historial propio se verifican. Las ediciones de catálogo/capacitaciones conservan auditoría mínima, pero no se promete versionado completo de todos sus valores anteriores.

## Secuencia y criterios verificados

| Entrega | Casos comprobados | Resultado técnico |
|---|---|---|
| Notas e historial | Primera nota, cero válido, corrección enlazada a la más reciente, autor/fecha, referencia antigua o inválida, campos ajenos y números fuera de rango. | Validación correcta y anteriores conservadas; no se sobreescriben notas. |
| Guardados simultáneos | Dos altas iniciales y dos correcciones concurrentes con la misma referencia. | En cada pareja: un 201 y un 409; una sola cadena de notas, sin ramas. |
| Permisos de notas | CSRF, reasignación, acceso propio sin notas/observaciones, bloqueo manual de psicometría y período cerrado. | Rechazos por rol/ámbito y conservación comprobados. |
| Interfaz de notas | Sin asignaciones, carga/error, guardar y corregir consecutivamente, período cerrado, selección preservada. | Controles bloqueados mientras cargan/guardan; error/estado vacío explícitos; historial disponible en cierre. |
| Cursos personales | Enlace opcional, renombrado de catálogo y edición de observaciones, fechas inválidas, ámbito y consulta propia. | Nombre histórico preservado; fecha ISO válida; Instructor sin observaciones ni terceros. |
| Catálogo de cursos | Registro/edición y modal precargado; separación de asignación; permisos y filtros PDF. | Flujo y permisos existentes comprobados; sin borrado físico. |
| Asistencia | Cuatro estados, Falta inicial, carga de llamada, duplicados/correcciones, historial, filtros, calendario propio y rango de reporte. | Comportamiento aprobado y privacidad comprobados. |
| PDF operativos | Exportación HTTP real desde base aislada, carimbo institucional, cabeceras, columnas y paginación. | Reportes de cursos y asistencia renderizados e inspeccionados: tres páginas cada uno. |
| Responsividad | Administrador/Jefe: notas, cursos, asistencia; Instructor: cursos y calendario; 360/1447 px y estados vacíos de notas. | 20 escenarios Chromium sin errores JavaScript ni desborde de página. |

## Correcciones realizadas

- Notas: selector conservado al guardar y recargar, opción inicial vacía, guardado deshabilitado hasta obtener historial, protección frente a respuestas tardías y doble envío. Período cerrado permite consulta e impide edición; errores de carga no habilitan guardar una nota sin referencia.
- CSS: el formulario oculto de notas respeta hidden aunque tenga display:flex por su clase.
- Backend de notas: BEGIN IMMEDIATE serializa comprobación de última nota e inserción. Una segunda operación con referencia obsoleta recibe 409; la interfaz recarga el historial para revisar/reintentar. Validación estricta de referencia entera positiva, campos admitidos y nota finita. No se altera precisión ni se introduce regla de redondeo.
- Capacitaciones: editar observaciones de un vínculo sin cambiar curso_id conserva el nombre histórico; un vínculo nuevo toma el nombre vigente del catálogo. Fecha falsa, numérica, lista o formato no ISO rechazados.

## Evidencias del cierre

Suite final: **68 pruebas aprobadas en 48,333 s** con `python -m unittest discover -s tests -v`, bases aisladas y entorno existente. Cuatro pruebas nuevas cubren notas/privacidad/cierre, simultaneidad, capacitación histórica/fechas y reasignación. Las primeras ejecuciones detectaron errores en la preparación del token CSRF del cliente concurrente; se corrigió obteniéndolo del dashboard tras login y la prueba concurrente pasó antes de repetir la suite completa.

Compilación Python, sintaxis JavaScript, enlaces locales y `git diff --check` correctos. Los PDF de prueba contienen solo datos sintéticos y permanecen en .tmp ignorado; no son información institucional real. No se ejecutó init-db ni se cambió el esquema/base local. Cambio previo de frontend/login.html preservado.

## Aceptación operativa pendiente

El solicitante debe revisar el recorrido visible con datos sintéticos: registrar/corregir una nota, comprobar historial, editar curso, llamar/corregir asistencia, consultar calendario propio y abrir/imprimir los PDF. Registrar aceptación o incidencias; no asumir una aprobación por el resultado de pruebas automatizadas. También queda pendiente la aceptación operativa de perfiles de 4A/4B.

Siguiente entrega propuesta: **definición de reglas de Fase 5B** (períodos, cierre/reapertura, publicación e historial de ponderaciones, faltantes/cero, precisión y redondeo). No implementarlas sin decisiones aprobadas. Privacidad/retención, licencia y autorización psicométrica, respaldo/restauración, HTTPS/operación y aceptación institucional del piloto mantienen sus requisitos previos.

Referencias: [plan](05_plan_desarrollo.md), [README](../README.md), [AGENTS](../AGENTS.md) e [historial](../HISTORY.md).
