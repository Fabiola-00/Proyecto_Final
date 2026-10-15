# 16. Cierre y reapertura — 5B.4

Entrega técnica del **2026-10-14**, SQLite **v22**. Completa el ciclo de cierre/reapertura del prototipo; no declara cerrada Fase 5B ni acredita aceptación operativa o institucional.

## Permisos y ciclo

- Solo el Administrador cierra y reabre, siempre con motivo de 1–2000 caracteres. Administrador/Jefe consultan revisión previa, historial e instantáneas. Instructor no accede a estos contratos administrativos.
- Se cierra una Gestión ACTIVA no retirada. La revisión muestra todas las personas del directorio admitidas (activas e inactivas), más personas con notas/asignaciones históricas en esa Gestión, con identidad mínima capturada. Las solicitudes sin registros no entran en el cierre.
- El cierre con incompletos está permitido y exige confirmación explícita. No inventa ceros, no redistribuye pesos ni genera resultados conjuntos faltantes. No cumplida con cero conserva su significado; un cero válido no es un faltante.
- Cierre e instantáneas se guardan en una transacción serializada junto al estado CERRADO. Firma de todas las fuentes y cierre previo detectan cambios desde la revisión; conflicto devuelve 409 y exige revisar otra vez.
- Reapertura solo del último cierre, con motivo y sin otra Gestión operativa ACTIVA. Conserva la configuración/regla, las notas/publicaciones y todos los cierres. Dos reaperturas concurrentes no duplican el evento. No cierra otra Gestión automáticamente.
- Un nuevo cierre crea otro número/enlace al anterior, con instantáneas nuevas. Las anteriores se consultan por su ID sin reconstruirlas con datos actuales. Una Gestión retirada conserva el historial, pero no se reabre.

## Instantánea reproducible y privacidad

`cierres_5b` conserva período previo, configuración publicada/fuentes, regla v2 explícita o su ausencia, activaciones anuales, programación común, ponderaciones históricas, motivo, autor/nombre/fecha UTC, firma y totales. `instantaneas_cierre_5b` conserva por persona identidad mínima, estado de cuenta al cierre, cálculo/estado/faltantes/bloqueos, notas con IDs, valores y autoría capturada, historial de habilitaciones, resultados/reprogramaciones físicas, formación pertinente con revisión/autor, respaldo académico anterior, asignaciones y notas manuales históricas no psicométricas, y referencia/copia de la última publicación. No copia contraseñas, hashes, correos, fotos ni respuestas psicométricas.

El cálculo guarda sus referencias y el resultado exacto como fracción de centésimas (`numerador`/`denominador`), además del conjunto final redondeado mitad hacia arriba y los componentes sin redondeos intermedios. Los campos `fuentes` identifican las notas vigentes; las versiones anteriores también se conservan como contexto auditado. La configuración PROMEDIO_TRES_V1 no se modifica. Cierres, instantáneas y reaperturas tienen FK restrictivas y triggers que impiden UPDATE/DELETE.

Mientras la Gestión está cerrada, el endpoint de cálculo usa la instantánea del último cierre (`provisional=false`, `cierre_id`), no los cursos ni metadatos actuales. Una persona añadida después no obtiene un resultado reconstruido: queda `FUERA_DEL_CIERRE`. Tras reabrir se consulta otra vez el provisional; el cierre anterior permanece intacto.

Cerrar/reabrir **no publica ni republica notas**. Instructor mantiene exclusivamente físicas/promedio y formación/acumulado de su publicación visible; Desempeño/conjunto, firma, actor/motivo e instantáneas administrativas permanecen ocultos. La deshabilitación o retirada sigue ocultando publicaciones conforme a 5B.3. Las rutas nuevas son `private, no-store`.

## Bloqueo de escritura

Notas, correcciones, programación/reprogramación, habilitación individual, activaciones por Gestión, opt-in de cálculo y publicaciones requieren Gestión ACTIVA en sus APIs. Se añadió la comprobación explícita al cambio de habilitación heredado. Edición de configuración sigue limitada a borradores; no se cambia al cerrar/reabrir.

Decisión confirmada el 2026-10-14: se bloquea registrar/corregir formación cuando **la fecha anterior o la nueva** imputa a un año anual cerrado, incluido desfinalizar un curso o moverlo a otro año. Se verifica dentro de la misma transacción de la corrección. Administrador debe reabrir antes de guardar; un cambio nulo no crea revisión. Catálogo y asignaciones sin finalización permanecen independientes; no aportan puntos a un año cerrado. Cuentas/perfiles, asistencia y operaciones conservan sus propios permisos y no se congelan por el cierre de evaluaciones; sus cambios no reescriben las instantáneas.

## Compatibilidad histórica

Una Gestión ACTIVA sin opt-in v2 puede cerrarse documentalmente: conserva datos/configuración tal como existen, con `REGLA_V2_NO_ACTIVADA`, sin resultado conjunto ni adopción automática. Es posible cerrar así un período antiguo para liberar el único activo. Reabrir no permite activar por primera vez otra regla en esa Gestión ya cerrada; la regla nueva corresponde a otra Gestión. Configuraciones congeladas nunca se reescriben.

Gestiones que ya estaban CERRADO antes de 5B.4 no reciben instantáneas retroactivas. Desde v23 se permite una reapertura excepcional explícita del Administrador, con motivo y constancia de ausencia de instantánea original. La evidencia disponible se captura al reabrir, sin atribuirla al cierre antiguo ni fabricar su fecha/resultados. No adopta notas ni cambia la regla existente; se describe en la ampliación v23 de este documento. No hay cierres/reaperturas automáticos por fechas ni nuevas reglas de puntuación.

## Uso y APIs

Desde **Gestiones (año)**: Administrador usa **Revisar y cerrar gestión**, revisa faltantes, escribe motivo y confirma. En CERRADO usa **Reabrir gestión**, o **Historial de cierres** para consultar cada versión. Jefe dispone de consulta de pendientes e historial, sin controles mutables de cierre.

- `GET /api/5b/periodos/<id>/cierre-previo`: contexto/personas, `firma_fuentes`, `cierre_anterior_id`.
- `POST /api/admin/5b/periodos/<id>/cerrar`: `motivo`, `firma_fuentes`, `cierre_anterior_id` (null en el primero), `confirmar_incompletos` booleano; devuelve ID y totales.
- `GET /api/5b/periodos/<id>/cierres`: cierres/reaperturas, autor/motivo/fecha y totales.
- `GET /api/5b/periodos/<id>/cierres/<cierre_id>`: instantáneas del cierre indicado, con autorización por Gestión/objeto.
- `POST /api/admin/5b/periodos/<id>/reabrir`: `motivo`, `cierre_id` del último cierre.

## Verificación y pendientes

La migración es aditiva, sin cerrar períodos, adoptar notas ni crear instantáneas automáticamente. Evidencias exactas de pruebas, respaldo, integridad y revisión visual de esta entrega se registran en HISTORY y el bloque final de este documento. No se agregaron dependencias, PDF propios ni psicometría/IA.

Continúan aceptación operativa/institucional de las fases técnicas, política de colisiones y requisitos del piloto (respaldo/restauración ensayados, HTTPS/WSGI, privacidad/retención y operación). Fase 5B no se declara cerrada por estas pruebas técnicas.

## Evidencia de esta entrega — 2026-10-14

Suite completa: **127 pruebas aprobadas en 257,841 s**. Diez pruebas específicas: **12,635 s** tras ampliar la comprobación de habilitación heredada. Ocho escenarios Chromium con API simulada, ambos roles, 360/1447 px y ambos temas, sin errores/desbordes; revisión/cierre/reapertura/recierre/historial, lectura del Jefe y conflicto de firma. Capturas inspeccionadas, sin nuevo ensayo PDF.

Respaldo local `instance/backups/sicose-20261014-pre-v22-3289032b.sqlite3`, 40 tablas previas preservadas, dos inicializaciones, v22, quick_check=ok, FK=0; cierres/instantáneas/reaperturas nuevos vacíos. Entorno, fotos e historial conservados. Evidencias ignoradas en `.tmp/cierres-suite-final.log`, `.tmp/cierres-tests-cierre.log`, `.tmp/cierres-migracion.json` y `.tmp/cierres-ui/`.
Controles finales: compilación Python, sintaxis de cinco JavaScript, 116 enlaces locales en doce documentos y git diff --check correctos. Relectura local v22/quick_check=ok/FK=0, tablas nuevas vacías.

## Ampliación de compatibilidad histórica — 2026-10-14, v23

Decisión confirmada por el solicitante: permitir una **reapertura excepcional** solo al Administrador para una Gestión CERRADO sin cierres con instantáneas. Exige motivo, revisión/firma de fuentes y constancia explícita de ausencia de instantánea original. No hay cierre retroactivo ni fecha/resultado antiguo reconstruido; la evidencia se toma en el momento de la reapertura. Sustituye la limitación inicial de v22 documentada arriba.

- `reaperturas_historicas_5b` guarda una evidencia JSON versionada por Gestión, firma, motivo, actor/nombre/fecha UTC. FK restrictivas, unicidad por Gestión y triggers contra UPDATE/DELETE. Formato `EVIDENCIA_REAPERTURA_HISTORICA_V1`, con fecha original no acreditada y estado de cálculo `NO_RECONSTRUIDO`; no se ejecuta el cálculo al preparar esa evidencia.
- La evidencia conserva los datos actuales mínimos del período/configuración, fuentes, notas y su autoría, formación y revisiones, asignaciones/calificaciones antiguas no psicométricas y última publicación disponible. No copia respuestas psicométricas ni credenciales. Se consulta íntegra después de corregir o cerrar de nuevo; no se reemplaza con información actual.
- Solo sobre una Gestión cerrada no retirada, sin cierres con instantánea ni reapertura excepcional previa. No introduce un segundo activo. Evidencia, evento y estado ACTIVO se guardan atómicamente; concurrencia/fuentes obsoletas devuelven 409, sin cambios parciales. Si hay cierres con instantáneas, se usa la reapertura ordinaria.
- Conserva la regla/configuración existentes, incluida la ausencia de regla v2. Está bloqueada la primera activación de otra regla después de esta excepción. Las notas antiguas sin configuración/física programada no se adoptan; una v2 ya existente conserva exactamente su alcance anterior.
- El primer cierre posterior es el **primer cierre con instantáneas**. Su contexto referencia la reapertura excepcional, no inventa un cierre anterior. A partir de ahí opera la reapertura ordinaria. Evidencia y cierres son registros distintos.
- Administrador/Jefe consultan evidencia/revisión; únicamente Administrador confirma la excepción. Instructor mantiene solo sus versiones publicadas autorizadas, sin ampliación de proyecciones. Las rutas nuevas tienen caché privada no-store.

Desde **Gestiones (año)**: **Reabrir histórico sin instantánea** (Administrador) o **Revisar histórico sin instantánea** (Jefe). Una vez reabierto aparece **Evidencia de reapertura histórica**, también después de un cierre nuevo o retiro operativo.

APIs adicionales:

- `GET /api/5b/periodos/<id>/reapertura-historica-previa`: evidencia disponible y firma; Administrador/Jefe.
- `POST /api/admin/5b/periodos/<id>/reabrir-historico`: `motivo`, `firma_fuentes`, `confirmar_sin_instantanea: true`; Administrador.
- `GET /api/5b/periodos/<id>/reapertura-historica`: evidencia inmutable y metadatos del evento; Administrador/Jefe.

La migración v23 no reabre ninguna Gestión ni genera evidencias automáticamente. Respaldo local `instance/backups/sicose-20261014-pre-v23-c8c8c9bf.sqlite3`: 43 tablas previas preservadas, dos inicializaciones, quick_check=ok, FK=0, nueva tabla vacía. Ver [validación integral y aceptación pendiente](17_validacion_integral_5b.md). La evidencia v22 anterior sigue fechada; no representa la ejecución v23.

Verificación final v23 del 2026-10-14: ocho pruebas específicas aprobadas en 20,885 s, diez de regresión de cierres en 24,903 s y suite completa **135 aprobadas en 301,157 s** tras actualizar las aserciones antiguas de versión. Ocho escenarios visuales sintéticos con ambos gestores/temas y 360/1447 px, sin errores/desbordes; capturas inspeccionadas. Python, cinco JavaScript, 122 enlaces locales en once documentos y diff correctos. Base releída v23/quick_check=ok/FK=0, sin evidencias históricas nuevas. El ensayo humano sigue pendiente.
