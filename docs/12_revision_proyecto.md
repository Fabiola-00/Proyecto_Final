# 12. Revisión estructural y del plan SICOSE

Fecha: **2026-10-13**. Diagnóstico inicial previo a 5B.1; la actualización posterior figura al final. Revisión de README, AGENTS, HISTORY, plan general, reglas posteriores, módulos Flask, esquema, plantillas, JavaScript y pruebas. Diagnóstico del prototipo académico local; no constituye aceptación operativa ni autorización institucional.

## Hasta dónde llegó el proyecto

| Fase | Estado comprobado | Pendiente principal |
|---|---|---|
| 0 — Especificación | Base documental existente y acuerdos posteriores registrados. | Aceptación institucional, privacidad y requisitos del piloto. |
| 1/1A — Base ejecutable | Implementada para entorno local: fábrica Flask, plantillas y configuración externa. | Preparación de operación institucional pertenece al piloto. |
| 2 — Persistencia/autenticación | Implementada: SQLite v18, migraciones, sesiones, roles, CSRF, hash y auditoría. | Restauración ensayada y endurecimiento de despliegue. |
| 3 — Diseño/dashboards | Implementada técnicamente: paneles por rol, identidad SBRAB y frontend propio. | Aceptación humana del recorrido; esta revisión no repite ensayo visual. |
| 4A — Gestión y autoservicio | Implementada técnicamente: solicitudes/aprobación, bajas lógicas y correo/foto propios. | Aceptación operativa; política definitiva de colisiones y reactivación explícita. |
| 4B — Perfil/relaciones | Implementada técnicamente: identidad, geografía, grado, incorporación, especialidades, cursos y operaciones. | Aceptación operativa; corrección de vínculos si se amplía alcance. |
| 5A — Seguimiento operativo | Cierre técnico registrado: asistencia, calendario, notas/historial y PDF operativos. | Aceptación operativa. |
| 5B — Evaluaciones por gestión | Parcial: configuración/activo único, habilitación, notas auditadas y formación individual v18. | Programación física, acumulación/cálculos, publicación y cierres/reaperturas. |
| 6 — Psicometría | Condicionada; preparación de catálogo no equivale a aplicación. | Licencias, idioma, puntuación, revisión profesional e institución. |
| 7 — Reportes | Parcial: PDF cursos/asistencia/evaluaciones. | Excel, resultados calculados y reportes psicométricos autorizados. |
| Piloto | Pendiente. | Operación, restauración, HTTPS/WSGI, privacidad y aceptación institucional. |
| 8 — IA | Opcional, sin implementación. | Propósito, datos autorizados y validación; fuera del cierre básico. |

El punto de desarrollo actual es **5B parcial con parte de 7 adelantada**. No corresponde expresar un porcentaje global: las etapas tienen tamaños y condiciones diferentes, y el cierre técnico es distinto de aceptación operativa.

## Estructura y mantenibilidad

La separación actual es adecuada para el tamaño del prototipo: `sicose/` concentra Flask y persistencia; `frontend/` plantillas/recursos; `tests/` verificación aislada; `docs/` decisiones; `instance/` SQLite y fotos privadas fuera de Git. La fábrica registra blueprints por área. No se justifica cambiar de stack ni incorporar servicios para completar lo pendiente.

Puntos de mantenimiento que conviene abordar gradualmente:

- `management.py` (1014 líneas), `evaluations.py` (630) y `app.js` (995) concentran varias responsabilidades. Extraer módulos por dominio cuando se intervengan, preservando contratos de API y permisos; evitar una reestructuración masiva antes de cerrar 5B.
- `tests/test_app.py` contiene 87 pruebas en una clase y 1873 líneas. Separar por autenticación, personal, asistencia, formación, gestiones/reportes y migraciones con fixtures comunes, sin reducir cobertura ni cambiar el descubrimiento.
- `db.py` concentra inicialización y migraciones; mantener preservación/idempotencia y pruebas de esquemas anteriores. Una futura separación por versión debe conservar orden y transacciones, sin resetear la base.
- Coexisten `capacitaciones` histórica, participaciones nuevas, notas antiguas y fuentes 5B. Esta compatibilidad es intencional: documentar qué entra en cada cálculo y no copiar/adoptar históricos automáticamente.
- Persisten plantilla/panel y nombres de Comandante históricos. Login y carga de sesión lo excluyen; creación/edición devuelve retirada del cargo. Revisar su limpieza solo con pruebas de conservación de autoría; su presencia no demuestra un cuarto rol operativo habilitado.

## Revisión de los documentos solicitados

| Archivo | Hallazgo | Acción |
|---|---|---|
| README | Resumen v18 coherente; distingue configuración y notas publicadas, pendientes e historial. | Añadir referencia a este diagnóstico y evidencia actual. |
| AGENTS | Continuidad coherente con reglas actuales; preserva entorno y decisiones confirmadas. | Añadir punto de revisión actual y secuencia de 5B. |
| HISTORY | Conserva cambios y pruebas fechadas, pero combina bloques por fases y fechas fuera de orden. | Preservar las entradas; identificar su organización histórica y añadir esta revisión al final. No usar una entrada antigua como estado vigente. |
| Plan general | Cabecera del 2026-10-11 y apartados principales conservaban Jefe por equipo, cuatro roles/Comandante operativo, Académica manual y PDF sin evaluaciones. | Actualizar resumen y alcances vigentes; conservar puntos históricos con advertencia explícita. |

Las reglas de 5B y su publicación ya fueron acordadas: requieren implementación, no una nueva consulta general sobre pesos/redondeo. Los documentos 01–03, 07–09 y cierre 5A son contexto fechado; ante diferencias prevalecen los acuerdos 10/11 y la implementación comprobada. El plan debe dirigir trabajo futuro; HISTORY conserva la evolución.

## Reformulación necesaria

Se mantiene la numeración 0–8 y se divide el trabajo restante de 5B en cuatro entregas verificables:

1. **5B.1 Física:** dos fechas comunes, reprogramación individual y No cumplida auditada con cero confirmado; pendiente sin nota distinto.
2. **5B.2 Acumulación/cálculos:** puntos por fecha de finalización personal, imputación única/tope 100, promedios y redondeo final. Definir tratamiento explícito de configuraciones históricas congeladas.
3. **5B.3 Publicación/republicación:** Instructor recibe solo físicas y formación/acumulado publicados; correcciones mantienen versión publicada anterior hasta republicar. Desempeño y resultado conjunto ocultos.
4. **5B.4 Cierre/reapertura:** motivo administrativo, incompletos y cada instantánea preservada; aceptación operativa aparte.

Fase 7 operativa avanza con los datos disponibles y añade resultados solo después del cálculo/publicación aplicables. Fase 6 queda condicionada y separada; no debe bloquear entregas operativas. Preparar el piloto después de aceptar el alcance elegido y verificar restauración/operación/privacidad. IA queda opcional.

Prioridades transversales: aceptación de 4A/4B/5A, política de colisiones, reactivación explícita de inactivos, tratamiento de históricos y preparación institucional. No se agregan reglas de autorización o privacidad nuevas en esta revisión.

## Verificación del 2026-10-13

- Suite completa: **87 pruebas aprobadas en 143,824 s**, ejecutada con `.venv/Scripts/python.exe -m unittest discover -s tests -v`.
- Compilación Python de `sicose` y `tests`: correcta.
- Sintaxis de los cinco JavaScript de `frontend/static/js`: correcta.
- `git diff --check`: correcto.

La base local se consultó únicamente en lectura: **schema_version=18, quick_check=ok, cero infracciones FK**. No se ejecutó init-db, seed ni migración sobre la base local. Las pruebas funcionales usan bases sintéticas aisladas. No se repitieron los escenarios Chromium ni la inspección visual de PDF; sus evidencias del 2026-10-12 siguen históricas.

Se preservaron modificaciones locales preexistentes en README, AGENTS e HISTORY. Entrega documental: sin cambio de código funcional, permisos, esquema, secretos o datos.


## Ejecución posterior del plan — 2026-10-13

5B.1 implementada técnicamente en SQLite v19: programación común de dos físicas, reprogramación extraordinaria y No cumplida auditada, con cero conservado hasta cumplimiento/corrección. Administrador/Jefe autorizados a programar y reprogramar por confirmación del solicitante. [Detalle y nueva evidencia](13_programacion_fisica.md). El diagnóstico y las 87 pruebas anteriores conservan su contexto documental. Pendientes 5B.2–5B.4 y aceptación operativa/institucional; no se declara cerrada 5B.


Actualización posterior — 2026-10-13, v20: [5B.2 y Gestiones](14_calculos_y_gestiones.md) implementa acumulado académico/cálculos provisionales mediante activación explícita, CRUD compartido de gestiones con baja lógica y activación anual separada de habilitación individual. Sustituye los pendientes de cálculo y la exclusividad de CRUD de gestiones de los bloques anteriores; configuración/publicación del ciclo siguen administrativas. Pendientes 5B.3 publicación y 5B.4 cierres. La evidencia anterior conserva su fecha/contexto.


Actualización posterior — 2026-10-13, v21: [5B.3 publicación/republicación](15_publicacion_notas.md) implementa versiones físicas/académicas propias, publicación parcial y ocultación mientras la fuente esté deshabilitada o Gestión retirada. Mis cursos muestra puntos desde snapshot publicado; correcciones mantienen versión/fecha anterior hasta republicar. Desempeño/conjunto y fuentes privadas no se publican. La evidencia de esta entrega anterior conserva su contexto. Siguiente pendiente 5B.4 cierre/reapertura con instantáneas.

### Actualización posterior — Activación de personal (2026-10-13)

La reactivación explícita de cuentas de Instructor Voluntario queda implementada para Administrador y Jefe de Personal, junto a la desactivación, desde el directorio global. Conserva historial, exige nuevo login y no sustituye la aprobación administrativa de solicitudes. Este cambio resuelve ese pendiente técnico del diagnóstico anterior; aceptación operativa y política de colisiones continúan pendientes. No modifica el alcance pendiente de 5B.4.

### Actualización posterior — 5B.4 (2026-10-14)

Cierre/reapertura con motivo, confirmación de incompletos e instantáneas por persona implementado técnicamente en v22. Esta entrega resuelve ese pendiente técnico del diagnóstico; las instantáneas se conservan sin recalcular con fuentes actuales y la reapertura mantiene configuración/activo único. Formación del año cerrado bloqueada en origen/destino hasta reabrir. No declara cerrada Fase 5B ni resuelve aceptación operativa/institucional o requisitos del piloto. [Detalle y evidencias](16_cierres_reaperturas.md).
