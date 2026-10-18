# Recomendaciones y pruebas actuales - entrega v29 (2026-10-18)

## Decisiones confirmadas

El solicitante autorizó integrar el flujo en el sistema existente, sin implementación ni aplicación en DEMO. GSE y Mini-IPIP sustituyen a DASS-21/CBI en la interfaz vigente; los registros, algoritmos y APIs anteriores se conservan como históricos. Se mantiene exactamente el modelo GSE/Mini-IPIP 9→6→4 de semilla 31415, época 84 y 88 parámetros; no hay nuevo entrenamiento ni selección de otra semilla.

- Administrador y Jefe generan por botón, únicamente con nueve entradas completas.
- Cada generación es una **Propuesta**. Una revisión humana y una observación del responsable permiten confirmarla para el reporte individual.
- Correcciones de notas o cambios de fuentes relevantes hacen que la versión conservada aparezca **Desactualizada**. Se conserva el historial y se permite generar una nueva versión; no se sobrescribe la anterior.
- Gestión cerrada o retirada: sin nuevas generaciones ni confirmaciones, revisiones de instrumentos, activaciones o respuestas. Reabrir una Gestión sigue siendo exclusivo del Administrador. Se conserva la consulta histórica autorizada.
- La revisión de versiones corresponde a Administrador y Jefe. Cada rol registra una constancia por prueba/Gestión/huella de formulario antes de habilitar. No se crea una aprobación automática ni se afirma revisión clínica profesional.
- Respuestas, resultados y recomendaciones se conservan por Gestión, sin tarea de borrado automático ni plazo numérico inventado. La aprobación de conservación por Gestión no define por sí sola un vencimiento en años.
- Instructor: un intento finalizado por prueba/Gestión, avances recuperables y únicamente «Completada» después de finalizar. Administrador/Jefe consultan resultados y respuestas finalizadas, nunca avances parciales.

La decisión posterior de revisión administrativa sustituye, exclusivamente para estos dos instrumentos y este uso orientativo, el requisito previo de expediente externo DASS/CBI. No cambia sus restricciones históricas ni acredita validez del modelo para decisiones de personal. Los textos de revisión y generación explican el carácter experimental, sin diagnóstico, ascensos, sanciones o aptitud operativa automática.

## Instrumentos y puntuación

`sicose/instrumentos_actuales.py` fija textos, opciones, orden, atribuciones, versión y algoritmo. La revisión se vincula con SHA-256 a todo el formulario, incluida la política informativa. Un cambio exige revisar la nueva huella; no se convierten respuestas antiguas silenciosamente.

| Instrumento | Codificación guardada | Resultados |
|---|---|---|
| GSE española | Diez enteros de 1 a 4 | Suma global 10–40; sin puntos de corte |
| Mini-IPIP español equilibrado | Veinte enteros de 1 a 5 | Cinco sumas independientes 4–20 |

Mini-IPIP: extraversión 1/6/11/16; amabilidad 2/7/12/17; responsabilidad 3/8/13/18; neuroticismo 4/9/14/19; apertura 5/10/15/20. Inversos 6/7/8/9/10/15/16/17/18/19/20: `6 - respuesta`. No mezclar con la variante de redacción positiva. Neuroticismo conserva su dirección; no se renombra como estabilidad emocional. Finalizar requiere todas las respuestas; guardar avance admite `null`, sin puntuarlo.

Fuentes consultadas el 2026-10-17: [GSE española](https://userpage.fu-berlin.de/~health/spanscal.htm), [permiso para estudios y puntuación GSE](https://userpage.fu-berlin.de/~health/faq_gse.pdf), [Mini-IPIP español](https://ipip.ori.org/Spanishmini-IPIPposneg.htm), [dominio público IPIP](https://ipip.ori.org/newPermission.htm). La GSE se incorpora al prototipo académico con atribución y permiso de investigación de los autores; no se afirma una licencia comercial ilimitada. Mini-IPIP es material IPIP de dominio público. Se verifica la versión de puntuación, sin atribuir validación en rescatistas bolivianos.

## Flujo administrativo y propio

En Evaluaciones, seleccionar Gestión. En «Habilitación de pruebas psicométricas», cada rol abre «Revisar versión», lee formulario, opciones, puntuación, fuentes y política, registra su constancia y confirma. Una vez revisada por ambos roles, Administrador o Jefe habilita cada prueba independientemente. Las revisiones no activan automáticamente una prueba.

En el panel del Instructor aparecen sus pruebas habilitadas. Guarda avances mediante revisión optimista, continúa y confirma la finalización definitiva. El cálculo se realiza en servidor dentro de la misma transacción. Un segundo intento o la modificación de uno finalizado se rechazan. Al terminar se cierra el formulario y se muestra «Completada»; las respuestas y puntuaciones finales dejan de estar disponibles en la API propia.

En Evaluaciones, el resumen de la persona muestra GSE global y las cinco dimensiones Mini-IPIP; «Ver respuestas» está reservado a Administrador/Jefe y solo existe para intentos finalizados. Los ejercicios aritméticos anteriores se retiran de esta interfaz, manteniendo sus registros y APIs históricos. No se agregan cuentas, puntuaciones, revisiones o respuestas de demostración a la base local.

## Nueve entradas y adaptación del modelo

Orden fijo: Físico (promedio), Desempeño (promedio), Académica (acumulado), GSE, extraversión, amabilidad, responsabilidad, neuroticismo y apertura. Las notas se obtienen del cálculo oficial del servidor, nunca del cuerpo de la solicitud. Los ceros oficiales iniciales son valores válidos según la decisión vigente; las pruebas pendientes no se sustituyen por ceros. Fuentes institucionales deshabilitadas o pruebas sin finalizar/habilitar/revisar impiden generar.

La adaptación operativa está en `sicose/recomendaciones.py`. Carga exclusivamente el archivo seleccionado con huella fijada `abb2bed7e4bcc7e232388bf671afbf5d2ba5bce309f14b79026d92a2d0bad252`; comprueba estructura y orden/rangos, restaura los pesos y realiza propagación hacia adelante. Un archivo ausente o cambiado bloquea la generación. No se usa `pickle`, no se entrena en solicitudes y no se alteran los metadatos históricos del experimento offline.

La integración autorizada presenta resultados sobre puntuaciones del sistema como propuestas experimentales con revisión humana, no como recomendaciones científicamente validadas. El archivo offline conserva su procedencia y marca de experimento; no se modifica para aparentar validación. `docs/26_informe_modelo_964_gse_miniipip.md` y su PDF describen el corte previo a esta integración y conservan su fecha como informe del entrenamiento.

Se conservan tanh, cuatro sigmoides y normalización `(valor-min)/(max-min)`. Salidas: preparación/confianza, comunicación/colaboración, aprendizaje/autonomía y afrontamiento/metas. Se activan desde 0,65; están inactivas hasta 0,35. Cualquier activación intermedia produce abstención global y el texto de revisión humana, sin sugerencias parciales. Las activaciones no se presentan como probabilidades.

## Firma, historial y confirmación

Cada Propuesta conserva las nueve entradas, referencias de notas, participaciones académicas y revisiones, intentos psicométricos, habilitaciones de pruebas y sus revisiones, fechas de Gestión, huella del modelo, resultado numérico/textual, responsable, fecha UTC y propuesta anterior. No guarda las respuestas completas otra vez en la recomendación: se referencian los intentos inmutables y sus resultados.

La firma de fuentes se calcula sobre un JSON canónico. Antes de generar o confirmar se comprueba de nuevo en una transacción `BEGIN IMMEDIATE`. Una pestaña con fuentes o propuesta anterior obsoletas recibe conflicto. Una repetición sin cambios no crea una nueva versión ni auditoría duplicada. La base impide cadenas iniciales o sucesoras duplicadas, alteraciones y borrados de evidencia conservada.

«Desactualizada» se deriva al consultar comparando firma, disponibilidad de fuentes y última versión; no se modifica el registro original. Las correcciones conservan IDs nuevos aunque vuelva el mismo valor numérico y, por ello, no rehabilitan accidentalmente una propuesta antigua. Deshabilitar y rehabilitar una prueba también cambia su revisión y exige generar nuevamente.

La confirmación es un registro independiente e inmutable, con observación obligatoria del responsable y su fecha/identidad. No modifica el texto ni activaciones del modelo. La confirmación de una abstención conserva el resultado indeterminado y la observación humana por separado; no lo convierte en una clasificación concluyente. Una segunda confirmación idéntica es idempotente; un texto distinto no puede sobrescribirla. Solo la última propuesta vigente se confirma y se publica en el reporte.

## Reporte individual

En la Gestión activa, presenta GSE y Mini-IPIP finalizadas con subescalas/rangos, sin respuestas individuales. Solo incluye la última propuesta vigente **Confirmada**. Una Propuesta sin confirmar o una versión Desactualizada deja la sección pendiente. Diferencia «Salida del modelo» y «Observación del responsable», junto con autorías, fechas, número de versión, huella y alcance experimental. Se conservan carimbo, foto, notas, formación, operaciones, asistencia y autorización administrativa.

## APIs

| Ruta relativa a `/api/modelo-anual/gestiones/<pid>` | Método | Acceso |
|---|---|---|
| `/pruebas` | GET | Administrador/Jefe: revisión, estados y formularios |
| `/pruebas/<clave>/revision` | POST | Administrador/Jefe: constancia del propio rol |
| `/pruebas/<clave>` | PATCH | Administrador/Jefe: habilitación con revisión vigente |
| `/pruebas/<clave>/propia` | GET/PUT | Instructor: solo formulario/avance propios |
| `/pruebas/<clave>/finalizar` | POST | Instructor: finalización propia y única |
| `/personas/<uid>/pruebas` | GET | Administrador/Jefe: solo respuestas/resultados finalizados |
| `/personas/<uid>/recomendacion` | GET/POST | Administrador/Jefe: contexto/historial y generación |
| `/personas/<uid>/recomendacion/<rid>/confirmar` | POST | Administrador/Jefe: revisión humana |

`GET /api/pruebas/propias` lista estados propios. Las rutas antiguas `/psicometria` permanecen separadas. Todas las rutas nuevas tienen autorización en servidor y `Cache-Control: private, no-store`; las mutaciones heredan CSRF. Las auditorías contienen acción/actor/identificadores mínimos, sin respuestas ni observaciones completas.

## Persistencia y entrega

SQLite v29 agrega seis tablas: `revisiones_pruebas`, `activaciones_pruebas`, `historial_activaciones_pruebas`, `intentos_pruebas`, `recomendaciones` y `confirmaciones_recomendacion`. No se amplían o reconstruyen las tablas históricas de DASS/CBI. Claves foráneas RESTRICT, finalizaciones inmutables y evidencia append-only. No se cambia el entorno o los pesos seleccionados.

Migración local mediante `scripts/migrar_recomendaciones_v29.py`: exige base existente v28, revisa integridad previa, respalda con SQLite Backup API, inicializa dos veces y compara todas las filas de las tablas previas mediante huellas, exceptuando exclusivamente el valor de versión del esquema. No ejecuta seed ni crea aprobaciones, respuestas o propuestas. La evidencia de ejecución se registra separadamente al completar la migración; no confundir el script preparado con una migración aplicada.

Las pruebas automatizadas usan bases temporales de pruebas, no una entrega DEMO ni modificaciones de expedientes reales. La revisión visual usa fixtures de interfaz sin acceso a la base local. La aceptación humana del flujo y la revisión efectiva de cada formulario quedan en manos de los responsables; no se simulan como realizadas.


## Evidencia de cierre técnico - 2026-10-18

- Migración local aplicada: respaldo `instance/backups/sicose-20261018-pre-v29-f19bed98.sqlite3`, 58 tablas previas preservadas, 64 finales, seis nuevas vacías, inicialización repetida dos veces, `quick_check=ok` y cero infracciones FK. Log `.tmp/recomendaciones-migracion.json`.
- Suite general: 226 pruebas aprobadas en 358,830 s. Tras los ajustes finales de estados y dos pruebas adicionales, 30 pruebas específicas aprobadas en 49,245 s, incluidas concurrencia, cambio de Académica, cierres, permisos, privacidad y PDF. No sumar ambos conteos como pruebas distintas. Logs `.tmp/recomendaciones-suite.log` y `.tmp/recomendaciones-cierre-tests.log`.
- Interfaz: doce escenarios automatizados con fixtures, tres roles, 360/1447 px y claro/oscuro, sin errores JavaScript ni desbordes. Capturas inspeccionadas; evidencia `.tmp/recomendaciones-ui/`. No es una instancia DEMO implementada o desplegada.
- PDF de prueba de tres páginas renderizado; sección de subescalas, salida del modelo y observación humana inspeccionada, con carimbo y privacidad conservados. Archivo interno `.tmp/recomendaciones-reporte-qa.pdf`; no contiene expedientes reales.
- Pesos originales preservados; aceptación humana del nuevo flujo y revisiones reales de formularios no se dan por realizadas.
