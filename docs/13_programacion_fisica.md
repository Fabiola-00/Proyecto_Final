# 13. Programación física — 5B.1, v19

Entrega del **2026-10-13**. Programación, reprogramación extraordinaria individual y No cumplida auditada implementadas técnicamente. No implementa promedios, acumulación académica, publicación de notas ni cierre/reapertura. Fase 5B sigue parcial; aceptación operativa e institucional pendientes.

## Permisos y recorrido

En esta entrega el solicitante confirmó que **Administrador y Jefe de Personal** crean/corrigen las fechas comunes y autorizan reprogramaciones individuales. La administración de gestiones y su configuración sigue siendo exclusiva del Administrador.

En **Notas operativas por fuente**, seleccionar persona y gestión. Física 1 y Física 2 permiten programar su fecha común, consultar historial de fechas y reprogramar a la persona. Son exactamente dos fuentes por gestión anual; la programación no depende de `instructor_id`. Cambiar una fecha común no reemplaza una excepción individual existente.

Escrituras requieren gestión anual ACTIVA y configuración PUBLICADA. Reprogramaciones y resultados personales requieren cuenta ACTIVA y fuente habilitada. Inactivos permiten consulta administrativa de historial y notas, sin nuevas reprogramaciones/resultados/correcciones. Instructor conserva la proyección propia de habilitación, estado y avance, sin notas, motivos, autores ni acceso a APIs administrativas de programación.

## Fechas y resultados

Fechas comunes e individuales explícitas, formato AAAA-MM-DD y dentro del año de la gestión. Cada versión conserva actor, nombre capturado, fecha UTC, motivo y enlace anterior; reprogramación conserva además fecha efectiva anterior y versión común utilizada. Repetir la misma fecha con la revisión vigente no crea historial duplicado.

Registrar **Cumplida** exige fecha real dentro de la gestión y no futura según Bolivia; nota 0–100 con hasta dos decimales. No se exige igualdad entre fecha prevista y fecha realizada: ambas se conservan separadas. Un cero por cumplimiento es Finalizada, distinto de No cumplida.

Confirmar **No cumplida** exige motivo, cero explícito y ausencia de fecha de realización; no se permite confirmar antes de la fecha efectiva prevista. Pasar la fecha no registra nada automáticamente. Sin nota sigue Pendiente. Reprogramar conserva íntegramente el resultado vigente, incluido un cero confirmado, hasta registrar cumplimiento/corrección.

Correcciones exigen motivo, ID de nota vigente y versiones vigentes de fecha común/individual. Cada resultado enlaza la nota auditada existente con las fechas que se utilizaron. Anteriores permanecen intactos. Avance considera No cumplida como resuelta, separándola de Finalizada y Pendiente; PDF administrativo refleja el estado y cero vigentes. No se calcula todavía el promedio físico.

## Compatibilidad

Migración aditiva: tres tablas nuevas, sin columnas cambiadas ni notas, fechas o estados inferidos. `PROMEDIO_TRES_V1` y sus fuentes congeladas no se modifican. La programación se registra por una acción explícita; las notas anteriores no se reclasifican ni se enlazan automáticamente. Una corrección posterior explícita conserva la nota previa y añade un resultado nuevo con sus referencias.

El API manual anterior admite todavía notas físicas sin programación cuando esa fuente no tiene fecha común, por compatibilidad con el circuito v15–v18. No admite No cumplida sin programación. Al existir una programación común exige el resultado físico explícito y sus revisiones; no permite omitirlo para eludir su validación. La interfaz nueva exige fecha común antes de registrar resultados. El tratamiento de configuraciones y notas históricas para cálculos corresponde a 5B.2, sin adopción automática.

## Persistencia y API

- `programaciones_fisicas`: versiones de las dos fechas comunes por período/fuente.
- `reprogramaciones_fisicas`: versiones extraordinarias por período/fuente/persona.
- `resultados_fisicos`: estado Cumplida/No cumplida, fecha real y referencias a programación/nota. Cero confirmado protegido también mediante trigger.
- GET `/api/5b/periodos/<id>/fisicas`: fechas comunes vigentes e historial administrativo.
- POST `/api/5b/periodos/<id>/fisicas/<fuente>`: `fecha`, `motivo`, `anterior_id` (null en primera programación).
- POST `/api/5b/periodos/<id>/fisicas/<fuente>/personas/<id>`: mismos campos y `programacion_id`; primera excepción usa `anterior_id=null`.
- GET `/api/5b/personas/<id>?periodo_id=<id>` añade fechas vigentes, historial individual y resultado físico por versión de nota.
- POST de notas existente recibe `fisica`: `estado` (`CUMPLIDA`/`NO_CUMPLIDA`), `fecha_realizacion`, `programacion_id`, `reprogramacion_id` (null sin excepción); conserva `corregida_de_id`, motivo y nota.

Autorización backend, CSRF, consultas parametrizadas, claves foráneas restrictivas, índices de consulta, transacciones BEGIN IMMEDIATE y comparación de revisiones. Historial físico inmutable por triggers de UPDATE/DELETE; no hay borrado de programación ni notas desde la interfaz/API.

## Verificación y siguientes entregas

La evidencia final de pruebas, interfaz y migración se registra abajo y en HISTORY. Pruebas de interfaz con API simulada complementan las pruebas HTTP reales en bases aisladas; no acreditan aceptación operativa humana.

Pendientes: **5B.2** acumulación/cálculos y tratamiento explícito de históricos; **5B.3** publicación/republicación; **5B.4** cierre/reapertura con instantáneas. Psicometría e IA siguen fuera de esta entrega. No se declara cerrada Fase 5B.


### Evidencia final — 2026-10-13

- Suite completa: **93 pruebas aprobadas en 195,680 s**, bases aisladas; seis específicas de 5B.1. Concurrencia de fechas comunes/individuales y notas iniciales/correcciones, dos pruebas independientes, cero cumplido/No cumplida, reprogramación, historial, permisos, CSRF, cuentas inactivas, habilitación, fechas/versiones, privacidad y migración repetida.
- 20 escenarios Chromium con API simulada: tres roles en Notas operativas/proyección propia (12), Administrador/Jefe en tabla/modal (8), 360/1447 px y claro/oscuro. Programación/reprogramación, envío de cero confirmado, estado No cumplida y privacidad verificados; sin errores JavaScript ni desbordes. Capturas inspeccionadas. No sustituye aceptación operativa.
- PDF HTTP con estado No cumplida/cero: 200, cabecera PDF, privado no-store y auditoría correcta; sin nueva inspección visual de PDF.
- Compilación Python, sintaxis de cinco JavaScript, enlaces locales y git diff --check correctos.
- Migración local v18→v19 tras respaldo `instance/backups/sicose-20261013-pre-v19-b3c3c9bd.sqlite3`: 32 tablas previas preservadas (schema_version actualizado), dos inicializaciones, quick_check=ok, FK=0, tres tablas nuevas vacías; sin notas/fechas inferidas, seed ni nuevas dependencias.

Logs/artefactos locales ignorados: `.tmp/fisicas-suite-final.log`, `.tmp/fisicas-migracion.json`, `.tmp/fisicas-ui/`.


Actualización posterior — 2026-10-13, v20: [5B.2 y Gestiones](14_calculos_y_gestiones.md) implementa acumulado académico/cálculos provisionales mediante activación explícita, CRUD compartido de gestiones con baja lógica y activación anual separada de habilitación individual. Sustituye los pendientes de cálculo y la exclusividad de CRUD de gestiones de los bloques anteriores; configuración/publicación del ciclo siguen administrativas. Pendientes 5B.3 publicación y 5B.4 cierres. La evidencia anterior conserva su fecha/contexto.


Actualización posterior — 2026-10-13, v21: [5B.3 publicación/republicación](15_publicacion_notas.md) implementa versiones físicas/académicas propias, publicación parcial y ocultación mientras la fuente esté deshabilitada o Gestión retirada. Mis cursos muestra puntos desde snapshot publicado; correcciones mantienen versión/fecha anterior hasta republicar. Desempeño/conjunto y fuentes privadas no se publican. La evidencia de esta entrega anterior conserva su contexto. Siguiente pendiente 5B.4 cierre/reapertura con instantáneas.
