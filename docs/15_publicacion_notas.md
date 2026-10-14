# 15. Publicación y republicación — 5B.3, v21

Entrega del **2026-10-13**, posterior a 5B.2/v20. Publicación técnica de físicas y formación/acumulado propios. No implementa cierres/reaperturas con instantáneas de resultados conjuntos ni acredita aceptación operativa/institucional. Fase 5B sigue parcial.

## Acuerdos y alcance

Administrador **y Jefe de Personal** publican/republican por persona y Gestión. El solicitante confirmó en esta entrega:

- Se admite publicación parcial de las físicas o formación disponibles. Pendientes se indican expresamente; no se inventan ceros ni promedios sin las dos físicas publicadas.
- Lo publicado se **oculta mientras esté deshabilitada la evaluación o retirada su Gestión**. Los datos/versiones permanecen en servidor. Al rehabilitar una evaluación se recupera la última versión publicada de ese componente, con su fecha original; no se publica la corrección vigente automáticamente.

Reglas anteriores conservadas: Instructor consulta únicamente físicas individuales/promedio y puntos de sus cursos/acumulado académico publicados. Corrección conserva valor/fecha publicados anteriores hasta republicar. Desempeño y conjunto permanecen privados. Una publicación de configuración no publica notas.

## Flujo administrativo

En **Notas y resultados**, seleccionar persona y Gestión. El panel Publicación al Instructor muestra versión/fecha y cambios pendientes. Revisar y publicar/republicar abre la vista previa con físicas, cursos, acumulado y pendientes; exige motivo y confirmación de revisión. El backend resuelve todos los valores, sin aceptar notas, fuentes ni autoría arbitrarias del cliente.

Requiere cuenta ACTIVA, Gestión anual ACTIVA no retirada, configuración publicada y regla ACUMULADO_TRES_V2 previamente activada. Las fuentes a actualizar deben estar activas en Gestión y habilitadas individualmente. Una primera publicación exige al menos un dato numérico válido; un cero confirmado/finalizado cuenta. Una republicación puede dejar componentes pendientes o retirar cursos de su instantánea para rectificar una finalización anterior.

La publicación es parcial respecto a datos disponibles, pero cada operación se guarda íntegra. Componentes deshabilitados conservan su versión publicada previa oculta, incluso si se republica otro componente. Los habilitados se actualizan desde sus fuentes vigentes. Versiones sin cambios no generan nuevas filas/auditorías duplicadas.

Cada vista previa lleva firma de físicas/formación y revisión de publicación. BEGIN IMMEDIATE serializa la operación; cambio de notas, formación, habilitación, activación, regla o revisión invalida una vista previa antigua. Dos publicaciones/republicaciones simultáneas de las mismas fuentes generan una sola versión nueva. Cambiar Desempeño no cambia firma, versión, fecha ni indicadores de publicación, porque este módulo no consulta sus notas.

El historial administrativo conserva revisiones, valores, referencias a notas/resultados físicos y participaciones/revisiones/historial de cursos, actor/nombre, motivo y fecha UTC. No se eliminan ni actualizan versiones publicadas.

## Datos y privacidad

Snapshot con lista positiva: Física 1/2 (nota, estado y realización), y Académica (valor limitado a 100, suma sin tope, cursos/puntos/finalizaciones personales). Las fuentes internas son solo físicas/formación. No se copia el objeto completo del cálculo: no se almacenan Desempeño ni resultado conjunto en la publicación.

El promedio físico visible se obtiene exclusivamente de las dos notas publicadas visibles, con precisión exacta. Si alguna está pendiente/deshabilitada/sin publicar, No disponible. No depende de las notas vigentes sin republicar ni de Desempeño.

Cada componente conserva su propia fecha de publicación; republicar otro componente no sustituye esa fecha si sus valores/fuentes no cambiaron. Correcciones con mismo valor pero nueva versión de fuente sí son trazables como republicación.

**Mis evaluaciones** separa estados/avance vigentes de Notas publicadas. La respuesta propia excluye filas y estados de Desempeño también del denominador de avance: solo físicas, Académica y psicométricas propias autorizadas, sin notas psicométricas. No expone fuentes internas, firmas, IDs de notas, actor/motivo, reglas privadas ni conjunto.

**Mis cursos** conserva asignaciones/estados vigentes sin puntos corrientes y añade Formación publicada por Gestión. Los puntos y fecha personal que se muestran proceden de la versión publicada, aunque la participación vigente ya haya sido corregida. Cambiar el año de una finalización no modifica una publicación previa; hace necesaria la republicación de la Gestión afectada.

Ocultación aplicada en servidor en ambas APIs: fuente personal deshabilitada, activación anual deshabilitada o Gestión retirada no entrega sus notas/puntos publicados. Ocultar una física oculta también su promedio; desactivar Académica oculta sus puntos y cursos publicados. Cuenta inactiva no inicia sesión. No hay selector de terceros en APIs propias, ni acceso del Instructor a vista previa/historial administrativos. Respuestas propias con puntos y todas las rutas de publicación/vista previa/historial usan Cache-Control private, no-store.

## Persistencia y contratos

Esquema v21 añade `publicaciones_5b`: FK a persona y regla por Gestión; revisión única por persona/gestión; enlace anterior único; contenido/fuentes JSON generados por servidor; motivo, actor/nombre y fecha. Índice único de primera versión, FK restrictivas y triggers contra UPDATE/DELETE. No modifica tablas/configuraciones/notas previas ni crea publicaciones al migrar.

- GET `/api/5b/personas/<id>/publicacion?periodo_id=<id>`: Administrador/Jefe; vista previa, firma, revisión publicada, elegibilidad y cambios pendientes.
- POST `/api/5b/personas/<id>/publicacion`: Administrador/Jefe; `periodo_id`, `revision_publicada` (cero inicial), `firma_fuentes`, `motivo`. CSRF; 201 para versión nueva, 200 sin cambios, 409 para datos/revisión obsoletos o estado no publicable.
- GET `/api/5b/personas/<id>/publicaciones/historial?periodo_id=<id>`: historial administrativo completo de versiones físicas/académicas.
- GET `/api/evaluaciones/propias?periodo_id=<id>` añade `publicacion` explícitamente filtrada, o null si no hay datos publicados visibles. Su avance propio ya no incluye Desempeño.
- GET `/api/instructor-voluntario/formacion` añade `publicaciones` académicas visibles por Gestión, manteniendo participaciones corrientes sin puntajes ni motivos/autores.

No hay publicación psicométrica, PDF propio nuevo, notificaciones externas, nuevas dependencias ni cierre/reapertura. PROMEDIO_TRES_V1 y opt-in v2 permanecen intactos. Publicaciones son versiones de notas permitidas, distintas de las instantáneas integrales de cierre pendientes en 5B.4.

## Verificación

Pruebas aisladas cubren publicación parcial/cero/tope, vista obsoleta y concurrencia, correcciones sin actualización automática, cambio de año, fechas por componente, copia de componentes ocultos al republicar otro, ocultación/reactivación/baja, privacidad completa y ausencia de efectos de Desempeño, CSRF/cuentas inactivas/campos arbitrarios, historial inmutable y migración idempotente sin publicación automática.

16 escenarios Chromium con API simulada: publicación/republicación/historial para Administrador/Jefe y evaluaciones/cursos propios del Instructor, 360/1447 px, claro/oscuro. Capturas inspeccionadas; no sustituye aceptación operativa. Resultados finales, migración y verificaciones se registran al cierre de esta entrega.

Siguiente entrega: **5B.4 — Cierre/reapertura con motivo e instantáneas**. No se declara cerrada Fase 5B.


### Evidencia final — 2026-10-13

- **114 pruebas aprobadas en 123,012 s**, bases aisladas; diez nuevas de publicación/republicación. Primera suite de 112 en 207,464 s aprobada antes de añadir protección del avance propio y casos adicionales; diez específicas en 28,367 s también aprobadas. La suite final incluye todas las ampliaciones.
- 16 escenarios Chromium con API simulada, tres roles en publicación/evaluaciones/cursos, 360/1447 px y claro/oscuro, sin errores JavaScript ni desbordes; capturas de vista previa y proyección propia inspeccionadas. Escenarios repetidos tras ocultar estados de Desempeño del avance y ajustar control de confirmación.
- Respaldo local `instance/backups/sicose-20261013-pre-v21-2724fe76.sqlite3`; migración v20→v21, **39 tablas previas comparadas/preservadas** (salvo schema_version esperado), dos inicializaciones, quick_check=ok y FK=0. Nueva tabla vacía: no se publicó ninguna nota automáticamente. Entorno/fotos/cambios locales preservados, sin seed ni dependencias nuevas.
- Logs ignorados: `.tmp/publicaciones-suite-cierre.log`, `.tmp/publicaciones-migracion.json`, `.tmp/publicaciones-ui/`. Compilación Python, sintaxis de cinco JavaScript, 107 enlaces locales en doce documentos y git diff --check correctos; nueva comprobación de caché privada incluida en la repetición de cierre.


Cierre final: **114 pruebas aprobadas en 123,012 s**, incluida caché privada/no-store y ocultación de Desempeño en el avance propio. La ejecución anterior de 114 en 221,488 s es evidencia intermedia previa a la protección de caché. Compilación Python, cinco JavaScript, 107 enlaces locales en doce documentos y diff correctos; base local reconsultada solo en lectura v21, quick_check=ok, FK=0 y cero publicaciones automáticas.

### Actualización posterior — 2026-10-14

5B.4 implementa cierre/reapertura con instantáneas separados de las publicaciones. Cerrar no cambia versiones/fechas publicadas; Instructor mantiene la proyección de 5B.3. Reabrir permite correcciones autorizadas, pero su visibilidad sigue requiriendo republicación expresa. [Ciclo y límites](16_cierres_reaperturas.md).
