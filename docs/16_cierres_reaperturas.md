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

Gestiones que ya estaban CERRADO antes de 5B.4 no reciben instantáneas retroactivas. Sin un cierre conservado de este circuito no se reabren por la API nueva; el tratamiento de esos históricos requiere una entrega explícita, sin fabricar resultados ni motivos anteriores. No hay cierres/reaperturas automáticos por fechas ni nuevas reglas de puntuación.

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
