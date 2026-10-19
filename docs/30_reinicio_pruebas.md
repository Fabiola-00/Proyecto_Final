# Reinicio individual de GSE y Mini-IPIP - 2026-10-18

Ubicación actualizada: la tabla y su acción Reiniciar se trasladaron al módulo lateral **Pruebas y Recomendación**. Se mantienen el alcance individual, contraseña, permisos e historial descritos aquí; ver [organización de módulos](31_modulos_evaluacion_pruebas.md).

## Decisiones confirmadas

El solicitante pidió reiniciar una prueba completada con su contraseña de inicio de sesión y precisó: solo un Instructor seleccionado, conservando el intento anterior en historial protegido. Administrador y Jefe de Personal pueden ejecutar la acción. Se conserva el modelo operativo GSE/Mini-IPIP 9→6→4, su entrenamiento, pesos y aplicación; NASA-TLX y redes de quince entradas quedan como antecedentes experimentales, sin incorporación al sistema.

## Uso

En Pruebas y Recomendación, seleccionar Gestión e Instructor Voluntario. En la tabla «Habilitación de pruebas psicométricas», el botón **Reiniciar** de cada fila actúa únicamente sobre ese Instructor y esa prueba. El texto «Reinicio individual» identifica la persona seleccionada. El botón requiere un resultado completado, cuenta activa y Gestión activa/no retirada.

El modal identifica a la persona y prueba, explica los efectos, solicita **la contraseña de la cuenta que ejecuta la acción** y confirmación expresa. No se acepta la contraseña de otro usuario. La contraseña no se guarda en tablas ni auditoría y el campo se vacía al enviar, también cuando hay error.

Al confirmar:

- El resultado anterior deja de ser vigente; permanece intacto con sus respuestas, puntuaciones, formulario, versión y fechas.
- Se abre un intento nuevo con todas las respuestas vacías y estado **Pendiente**. Se pueden guardar avances y finalizar una vez en ese ciclo.
- La otra prueba, otras personas y otras Gestiones no cambian.
- Habilitación y revisiones de ambos roles permanecen; reiniciar no habilita la prueba automáticamente.
- Las recomendaciones basadas en el intento anterior quedan **Desactualizadas** y se excluyen del reporte individual. Una finalización posterior con las mismas respuestas tampoco reactiva recomendaciones viejas: el ciclo es diferente. Es necesario generar y revisar otra propuesta.

El historial de reinicios está en el resumen psicométrico administrativo y muestra resultados anteriores, finalización, fecha de reinicio y responsable. Instructor sin acceso a ese historial, resultados ni respuestas finalizadas; conserva únicamente «Completada» al finalizar el nuevo ciclo. Los borradores tampoco se muestran a Administrador/Jefe.

## API y persistencia

`POST /api/modelo-anual/gestiones/<pid>/personas/<uid>/pruebas/<clave>/reiniciar`

JSON exacto: `password`, `intento_ref`, `revision`, `confirmar: true`. CSRF y sesión administrativa obligatorios; validación de contraseña en servidor con el hash vigente. Contraseña incorrecta: 403 sin reinicio. Conflicto de versión/ciclo, prueba no completada, persona inactiva o Gestión cerrada/retirada: 409. Transacción serializada evita dos reinicios sobre el mismo resultado. Auditoría mínima del éxito/fallo sin contraseña ni respuestas.

La lectura propia de un formulario pendiente devuelve `ciclo`, que debe acompañar cada guardado/finalización de reintentos. La revisión optimista sigue controlando avances dentro del ciclo. Un formulario abierto antes del reinicio se rechaza aunque su número de revisión coincida. Para compatibilidad, el intento original admite la API anterior sin `ciclo` (equivalente a cero).

SQLite v30 agrega `reinicios_pruebas` y `reintentos_pruebas`. Las tablas originales no se reconstruyen ni se retiran sus restricciones. Reinicios apuntan al intento finalizado anterior y al responsable; reintentos se vinculan a un reinicio único. FKs y triggers protegen pertenencia a persona/Gestión/prueba, cadena de intentos, inmutabilidad de finalizados y prohibición de borrado. La firma de recomendación incorpora el reinicio solo cuando existe; las firmas anteriores a esta funcionalidad permanecen iguales para personas sin reinicio.

Migración aplicada por `scripts/migrar_reinicios_v30.py`, con respaldo `instance/backups/sicose-20261018-pre-v30-728e1545.sqlite3`: 64 tablas previas comparadas y preservadas íntegramente salvo valor schema_version, 66 finales, dos tablas nuevas vacías, dos inicializaciones, quick_check=ok y cero errores FK. Evidencia `.tmp/reinicios-migracion.json`. No se crearon reinicios, respuestas, usuarios o recomendaciones reales para ensayar.

## Verificación

Cinco pruebas específicas aprobadas: contraseña propia/incorrecta/CSRF/roles, reinicio individual y separación de pruebas, recomendación/PDF desactualizados, múltiples ciclos e historial, formularios obsoletos, cierre/inactivo/deshabilitación, inicialización repetida, FKs/triggers y concurrencia. Regresión de recomendaciones, modelo anual y reporte individual: 30 pruebas aprobadas en 49,002 s. Los ensayos usan bases temporales aisladas, sin despliegue en DEMO.

Doce escenarios Chromium con interfaz real y API simulada: Administrador/Jefe/Instructor, 360/1447 px, claro/oscuro; contraseña incorrecta/correcta, limpieza del campo, persona explícita, estado pendiente, historial y ciclo propio. Sin errores JavaScript ni desbordes de página; capturas inspeccionadas. Evidencia `.tmp/reinicios-ui/`.

Suite completa ejecutada: **242 pruebas en 485,077 s; 241 aprobadas y una expectativa histórica obsoleta fallida** en `test_organizacion` (esperaba PENDIENTE_INSTRUMENTO, pero GSE/Mini-IPIP ya estaban implementados y deshabilitados antes de esta entrega). Se actualizó exclusivamente esa expectativa a DESHABILITADA y se repitió el módulo completo: **9 pruebas aprobadas en 7,334 s**. No se presenta esa repetición específica como una segunda ejecución completa. Logs `.tmp/reinicios-suite-completa.log` y `.tmp/reinicios-organizacion-cierre.log`. Sintaxis Python/JavaScript, enlaces y diff correctos; huella del modelo operativo intacta.
