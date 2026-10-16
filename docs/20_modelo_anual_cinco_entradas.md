# Modelo anual de cinco entradas — 2026-10-15, SQLite v24

> Actualización posterior v25: [organización del espacio](21_organizacion_espacio_trabajo.md) sustituye programación física v3, navegación, eliminación y acceso propio a estados. Incorpora PDF v3 y ejemplos aritméticos separados de las entradas psicométricas oficiales. El contenido siguiente documenta el corte v24.

## Objetivo y contraste con la imagen

El diagrama presenta Física, Desempeño, Académica, Psicométrica 1 y Psicométrica 2 (0–100) como entradas de una futura red neuronal para recomendar ascenso y participación en operaciones. El sistema anterior solo calculaba tres componentes y un promedio conjunto, con Académica basada en cursos. Ese promedio no era una red neuronal ni generaba las recomendaciones de la imagen.

Esta entrega prepara la estructura y sus fuentes reales. Dos psicométricas quedan sin instrumento/nota y el modelo SIN_ENTRENAR, sin recomendaciones. No se inventan probabilidades, umbrales ni reactivos. Requiere revisión humana y las autorizaciones profesionales/institucionales futuras.

## Acuerdos nuevos confirmados por el solicitante

- Operaciones: cada participación tiene nota variable de 0 a 100, con hasta dos decimales, registrada/corregida por Administrador/Jefe. El Jefe realiza la valoración; se conserva el acceso administrativo de gestión.
- Académica = min(100, suma de puntos personales de cursos finalizados + suma de notas vigentes de participaciones en operaciones). Sin redistribuir pesos ni promediar cursos y operaciones. Detalle completo aunque exceda 100.
- Sin operaciones calificadas: estado Pendiente con aporte 0. En el nuevo modelo, sin otras evidencias el componente Académica también vale el cero oficial de inicio; esto sustituye la regla de suma vacía pendiente solo para v3.
- Nueva Gestión con inicio/fin propios elegidos por el Jefe; puede cruzar años y no está limitada a enero–diciembre. Cursos se imputan por fecha de finalización personal; operaciones por inicio del evento dentro del intervalo inclusivo. Los períodos nuevos no se superponen entre sí para evitar doble imputación temporal; los históricos se mantienen separados.
- Inicio explícito con **ceros oficiales**, no meros ceros visuales provisionales, excepto las dos psicométricas, que permanecen sin nota. No equivale a registrar No cumplida ni una fecha física ficticia.
- Administrador/Jefe pueden crear, editar borradores, iniciar, inscribir personas activas y retirar con motivo/historial. El Jefe también cierra gestiones, tanto del circuito anterior como del modelo nuevo; la reapertura sigue exclusiva del Administrador.
- Red neuronal se entrenará después, con datos autorizados, resultados de referencia y validación. Esta entrega no produce recomendaciones ni un sustituto aritmético.

## Versiones y preservación

`CINCO_ENTRADAS_V3` se guarda aparte, sin modificar `PROMEDIO_TRES_V1`, `ACUMULADO_TRES_V2`, sus notas/publicaciones/configuraciones ni cierres existentes. El Administrador mantiene la configuración/publicación del circuito anterior. No se convierten gestiones antiguas al modelo nuevo ni se resetean datos al migrar.

Cada persona activa inscrita obtiene cinco registros base con cero y origen CERO_INICIAL: FISICA_1, FISICA_2, DESEMPENO_JEFE, DESEMPENO_COMANDANTE y base ACADEMICA. Las cinco entradas finales son Física (media de las dos), Desempeño (media de las dos fuentes), Académica calculada, Psicométrica 1 y 2. Las psicométricas no reciben ceros, formularios ni instrumentos ficticios. Estado parcial diferencia una fuente ya calificada de otra que aún conserva su cero inicial.

Solo se inscriben cuentas activas; las personas inactivas conservan consulta administrativa de su evaluación previa, sin nuevas notas. Inscribir nuevamente a personas ya inscritas no resetea sus resultados ni duplica ceros. Existe acción para incorporar a nuevos activos después del inicio.

Las evidencias de cursos vigentes dentro del período actualizan el acumulado; no se borran cursos existentes para simular un reinicio. La tabla histórica capacitaciones y notas antiguas no se adoptan como puntos. La base inicial oficial y el acumulado calculado son trazables por separado.

## Datos y seguridad

Cinco tablas nuevas:

| Tabla | Función |
|---|---|
| modelos_anuales | Formato v3, revisión del borrador y actor/fecha de inicio |
| personas_modelo_anual | Una inscripción por persona/Gestión |
| notas_modelo_anual | Ceros y notas/correcciones append-only por fuente; evidencia física/Comandante |
| notas_operacion_anual | Una cadena de notas por período/persona/operación, con captura del evento |
| eventos_modelo_anual | Historial de creación, fechas anteriores/nuevas, inicio, inscripciones y retiro |

Unicidad de primera nota y de sucesor; validación dentro de BEGIN IMMEDIATE. Revisión/fuente/pertenencia vigentes; motivo/actor/UTC. Triggers de inmutabilidad y bloqueo de nombre/fechas de períodos ya iniciados. Tipos estrictos, centésimas enteras y consultas parametrizadas; sesión activa y CSRF.

Se preserva programación física común y reprogramación individual con las funciones existentes, ahora compatibles con intervalos propios. Cumplida exige fecha real válida/no futura; No cumplida exige motivo, cero, fecha prevista alcanzada y sin fecha real. Reprogramar conserva el resultado, incluido un cero confirmado. El cero inicial oficial no afirma que la prueba se haya realizado o incumplido.

Formación se bloquea si la fecha personal anterior o nueva está dentro de un período cerrado, además de los bloqueos anuales históricos. Modificar eventos con notas en períodos cerrados también se bloquea; la comprobación se serializa con el cierre. Se conservan snapshots y autoría separados del Comandante externo.

## Interfaz y contratos

En Gestión aparece Nueva Gestión de cinco entradas: nombre/inicio/fin. Los borradores del modelo tienen edición de fechas con revisión y motivo desde Administrar período y evaluación. Inicio explícito genera los ceros/inscripciones. Baja lógica conserva todo, con revisión y motivo.

Evaluaciones y Notas y Resultados enlazan al panel nuevo `/gestion/modelo-anual`, con cinco tarjetas de entrada, selección de Gestión/persona, calificaciones físicas/desempeño, operaciones, programación/reprogramación, habilitación individual, activación de fuentes e historial. Cierres tienen revisión previa, confirmación de pendientes y consulta de instantáneas. Reapertura visible solo al Administrador.

| Método/ruta | Contrato principal |
|---|---|
| GET/POST `/api/modelo-anual/gestiones` | Lista/crea borrador con nombre, fecha_inicio y fecha_fin |
| GET `/api/modelo-anual/gestiones/<id>` | Personas, cinco entradas, activaciones, cierres e historial administrativo |
| PATCH misma ruta | nombre, fechas, revision, motivo; solo borrador |
| DELETE misma ruta | revision, motivo; baja lógica |
| POST `.../<id>/iniciar` | revision, motivo; un solo período activo, ceros oficiales |
| POST `.../<id>/inscribir` | revision, motivo; nuevos activos, sin resetear inscritos |
| GET `.../<id>/personas/<uid>` | Cálculo/evidencia administrativa y fuentes disponibles |
| POST misma ruta | fuente, nota, anterior_id, motivo, evidencia |
| POST `.../<id>/personas/<uid>/operaciones/<oid>` | nota, anterior_id (null inicial), motivo |

Física usa evidencia con estado/fecha_realizacion/programacion_id/reprogramacion_id. Comandante exige comandante_nombre separado del transcriptor. Académica no acepta una nota manual global; las psicométricas no se califican por esta API. Correcciones obsoletas se rechazan, no bifurcan cadenas.

Se reutilizan APIs de activación/habilitación, programación y cierre. La firma de cierre incorpora historial nuevo, operaciones y calificaciones. Cada snapshot guarda el cálculo y evidencias v3; consultar una Gestión cerrada devuelve la instantánea, sin recalcularla. Reabrir no vuelve a inicializar ceros.

## Límites expresos

Todas las nuevas APIs son solo Administrador/Jefe y privadas no-store. Las cuentas Instructor no acceden a fuentes, firmas, Desempeño ni recomendaciones inexistentes. Las versiones publicadas del circuito anterior siguen funcionando. **La publicación propia y los PDF del modelo v3 no están implementados en esta entrega**: no se usa la publicación v2 para exponer resultados nuevos ni se presenta un PDF anterior como reporte v3. Son siguientes entregas separadas si se solicitan; mientras tanto los datos v3 permanecen administrativos.

El resultado conjunto v2 se conserva solo para históricos. En v3 resultado_conjunto es null y el modelo devuelve SIN_ENTRENAR, recomendaciones null y listo_para_inferencia=false. Las dos psicométricas pendientes impiden una entrada completa; no declarar listo el modelo ni aceptar instrumentos por un simple interruptor.

No hay aceptación operativa/institucional automática de esta reformulación. La aceptación previa de 5B corresponde al alcance anterior. No se cambia el stack ni se añaden dependencias.

## Verificación

Primera regresión completa: 146 pruebas aprobadas en 363,891 s. Once pruebas específicas nuevas aprobadas en 18,139 s; doce dirigidas incluyendo el permiso actualizado de cierre en 20,130 s. La suite final ampliada se registra en HISTORY al finalizar.

Dieciséis escenarios visuales con Flask real y base DEMO aislada, 360/1447 px y ambos temas; sin errores JS ni desbordes tras corregir la distribución móvil. Corrección de operación 75,25, cierre por Jefe, consulta de snapshot y denegación del Instructor comprobados. Capturas inspeccionadas. Sin nuevo ensayo de PDF al no cambiar renderizadores.

Migración respaldada `instance/backups/sicose-20261015-pre-v24-e3222dda.sqlite3`: dos inicializaciones, 44 tablas previas preservadas (excepto metadato de versión), cinco nuevas vacías, v24, quick_check=ok y FK=0. Ninguna Gestión/cero/publicación creada al migrar. Se conservan .venv, .env, fotos y cambios documentales previos, incluido DESARROLLO.md.

Evidencias locales ignoradas: `.tmp/modelo-anual-tests*.log`, `.tmp/modelo-anual-dirigidas-cierre.log`, `.tmp/modelo-anual-suite*.log`, `.tmp/modelo-anual-migracion.json` y `.tmp/modelo-anual-ui/`.


Verificación del 2026-10-15: suite completa de **149 pruebas aprobadas en 339,579 s**; regresión posterior de doce pruebas en **21,002 s**, incluida consulta histórica de retiradas y cierre del Jefe. Dieciséis escenarios visuales finales con Flask real/base DEMO, 360/1447 px y ambos temas, sin errores JavaScript ni desbordes; capturas revisadas. Python, siete JavaScript, 167 enlaces locales en 24 documentos y git diff --check correctos. DESARROLLO conserva DDL v23 y suplemento v24: ambos ejecutados dos veces en temporal, 49 tablas/13 índices explícitos/50 triggers, quick_check=ok/FK=0. Base de trabajo migrada tras respaldo, dos inicializaciones y 44 tablas anteriores preservadas salvo versión; cinco tablas nuevas vacías, v24/quick_check=ok/FK=0, ninguna Gestión ni cero creado automáticamente. Servidores DEMO detenidos y bases temporales retiradas. Sin dependencias nuevas, seed ni cambio de .env/.venv/fotos; documentación previa preservada. Psicométricas, red neuronal, publicación propia y PDF específicos de v3 pendientes; no se declara aceptación humana/institucional ni cierre global de 5B.


Consulta de retiradas: Administración/Jefe conservan el historial desde el enlace contextual, sin acciones de edición/inicio/calificación. Ceros iniciales oficiales son una categoría distinta de calificaciones registradas en el dashboard, sin afirmar que una prueba fue realizada.
