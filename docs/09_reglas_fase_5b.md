# 09. Definición de reglas de Fase 5B

Fecha: **2026-10-11**. Estado: **primera entrega implementada (v15); ciclo, cálculo y cierres pendientes**. Las decisiones del solicitante configuran el prototipo; no equivalen a validación o aprobación institucional de una puntuación.

## Objetivo y estado contrastado

Definir períodos, versiones de ponderación, faltantes, precisión y resultados reproducibles antes de programarlos. Existen períodos BORRADOR/ACTIVO/CERRADO, alta/listado administrativos, asignaciones y notas 0–100 con historial. Hay tablas versiones_ponderacion (BORRADOR/APROBADA/RETIRADA) y pesos_evaluacion (peso entre 0 y 1), pero no API de publicación, validación transaccional de suma, cierre/reapertura ni cálculo de resultados. No hay vínculos de versiones a instantáneas de resultados calculados.

Fase 5A tiene cierre técnico y aceptación operativa humana pendiente. No se modifican datos ni contratos existentes mientras se define 5B. Las fechas de períodos históricos permanecen intactas; cualquier incompatibilidad con las reglas nuevas requerirá tratamiento explícito, sin renombrar/cerrar/ajustar períodos automáticamente.

## Decisiones confirmadas por el solicitante

| Tema | Regla confirmada |
|---|---|
| Componentes | Física, Académica y Desempeño, de igual importancia. |
| Resultado conjunto | Promedio simple: (Física + Académica + Desempeño) / 3; no usar 33,33 % truncado. |
| Física | Dos evaluaciones de 0–100 por gestión; promedio simple de ambas. Las dos son obligatorias; falta una y el componente queda incompleto. |
| Académica | Nota global manual 0–100 respaldada por historial; Jefe registra/corrige en su ámbito y Administrador puede corregir con historial. Comandante no la edita. Motivo y referencias a cursos/capacitaciones de la persona obligatorios; sin formación queda pendiente. |
| Desempeño | Dos notas independientes 0–100: Jefe y Comandante; promedio simple. Ambas obligatorias; si falta alguna, componente y resultado conjunto incompletos. |
| Institución/grupo | Un único grupo SBRAB; no crear gestión de múltiples grupos. |
| Comandante | Un cargo de Comandante de SBRAB, cuyo nombre de responsable puede cambiar sin cambiar el cargo. Rol propio COMANDANTE_GRUPO implementado en v15; consulta seguimiento SBRAB y edita solo su aportación de Desempeño. |
| Configuración | Congelada durante el período activo; configuraciones diferentes para un período futuro, preservando históricos. |
| Cierre incompleto | Permitido: personas incompletas identificadas y resultado numérico ausente; no fabricar ceros ni redistribuir. |
| Reapertura | Administrador con motivo; conserva cierre anterior y genera un cierre nuevo al volver a cerrar. Configuración no cambia. |
| Asistencia | Porcentaje operativo separado; no se convierte en nota ni entra en la ponderación. |
| Psicometría | Fuera del cálculo de esta entrega; continúa condicionada en Fase 6. |
| Períodos nuevos | Anuales, del 1 de enero al 31 de diciembre; solo uno ACTIVO a la vez. |
| Gestión | Administrador crea borradores, activa/publica, cierra y reabre con motivo obligatorio. |
| Jefe | Registra/corrige notas solo mientras el período esté ACTIVO y dentro de su ámbito autorizado. |
| Año de cabecera | Informativo; no crea ni modifica períodos almacenados. |
| Escala de notas | Notas de entrada 0–100; igual importancia de los tres componentes confirmada, sin porcentajes configurables distintos en esta primera entrega. |
| Faltantes | Falta alguna de las tres notas: Incompleto / No calculable; sin reemplazo por cero ni redistribución de pesos. |
| Cero | Una nota registrada como 0 es válida y participa en el cálculo. |
| Precisión nueva | Notas nuevas de hasta dos decimales; no alterar notas históricas. |
| Redondeo del resultado | Dos decimales, mitad hacia arriba, aplicado solo al final; sin redondeos intermedios. |

## Responsabilidades y privacidad acordadas

| Actor | Registro/corrección | Consulta y límites |
|---|---|---|
| Administrador | Gestiona cuentas/ciclo/configuración; puede corregir notas con historial y realiza cierres/reaperturas motivadas. | Alcance administrativo vigente; conserva autoría y cierres anteriores. |
| Jefe de Personal | Física, nota Académica con respaldo y su propia aportación de Desempeño, sobre personal activo asignado y período activo. | Conserva alcance vigente; no registra en nombre del Comandante. |
| Comandante del Grupo | Solo su propia aportación de Desempeño, en período activo y grupo SBRAB. | Consulta personal, asistencia, formación y notas/resultados operativos SBRAB; no observaciones ajenas. No administra cuentas, permisos, períodos ni configuración, ni edita Física/Académica o la aportación del Jefe. |
| Instructor Voluntario | Sin cambios de autoservicio: solo correo/foto. | Estado/avance propio, sin notas, resultado numérico ni observaciones. |

Existe un solo grupo SBRAB y un cargo de Comandante; no implementar selector ni gestión multigrupo. La persona/nombre responsable puede cambiar, pero el cargo permanece. Preservar identificadores y autoría: cambios de nombre no reescriben la autoría capturada en cierres; no reutilizar automáticamente historial/credenciales para otra persona. La gestión del responsable corresponde a Administración, no al propio Comandante.

Los permisos de consulta no conceden escritura por sí mismos. Las notas de Jefe y Comandante son aportaciones independientes con actor identificable; no debe ser posible que un Jefe envíe un campo para suplantar al Comandante. Correcciones administrativas conservan responsable de la aportación y autor de la corrección, sin mezclar ambos conceptos. La consulta de Comandante excluye observaciones/motivos ajenos, incluso en historial, respuesta JSON y exportaciones.

## Fuente y respaldo de cada nota

- Física: dos evaluaciones identificadas por gestión, no un promedio automático de todas las notas de una categoría. Las fechas concretas se configuran sin inventar calendario de entregas. Se exige una nota vigente para cada evaluación; cada corrección conserva su cadena previa.
- Académica: Jefe ingresa una nota global 0–100, un motivo y una o más referencias a cursos/capacitaciones del historial de la persona. Referencias válidas y de esa persona; no basta seleccionar un curso del catálogo común en el que no tenga un registro personal. Sin formación registrada, pendiente. No convertir cantidad/duración/estado de cursos en puntos ni deducir una rúbrica institucional.
- Desempeño: dos aportaciones independientes, una Jefe y una Comandante; ambas obligatorias. El Administrador no convierte por defecto una nota genérica antigua en una de estas aportaciones.
- Usar última nota válida de cada cadena de corrección, no promediar filas históricas. Conservar datos y referencias de las fuentes para reproducir el resultado.
- Fuentes/evaluaciones concretas se configuran en borrador antes de publicar. Perfiles, períodos, cursos y notas históricos no se reetiquetan/enlazan automáticamente. Los casos incompatibles quedan para revisión explícita.

## Ciclo de período y configuración

1. Administrador crea un período anual en BORRADOR y completa fuentes/configuración de los tres componentes. Solo las fechas nuevas siguen enero–diciembre; no reajustar períodos existentes.
2. Publicar/activar solo con configuración válida y completa. Comprobar de forma atómica que no existe otro período ACTIVO. Borrador editable; al activar queda congelada la configuración.
3. En ACTIVO, registrar/corregir según rol, conservando historial. Los cambios de notas no son cambios de configuración; actualizan el resultado provisional sin alterar cierres anteriores. No permitir registros/correcciones en BORRADOR/CERRADO.
4. Administrador cierra. Permitir personas incompletas, identificando qué fuentes faltan y manteniendo resultado numérico ausente. Guardar una instantánea por persona, sin reemplazar notas faltantes por cero.
5. Reabrir con motivo obligatorio, solo si no introduce un segundo período activo. Conservar el cierre anterior, su configuración y resultados. Permitir correcciones autorizadas; al cerrar de nuevo crear otra instantánea vinculada al cierre anterior. Configuración original permanece congelada; una regla nueva corresponde a período futuro.

Instantánea: período/cierre, persona, configuración/fuentes, IDs y valores de notas vigentes, estado completo/incompleto y faltantes, resultado sin redondear reproducible y resultado final, fecha/autor y referencias al cierre previo. Capturar respaldo Académico y autoría pertinentes; no filtrar motivos privados al Comandante/Instructor. No calcular de nuevo una instantánea antigua con una configuración actual.

Reasignaciones/cambios de responsables conservan notas y sus autores; no copian ni duplican automáticamente aportaciones. En activo se aplica el ámbito autorizado vigente; los cierres conservan quién evaluó y la configuración utilizada. Personas/grupos históricos nunca se borran por cambio de responsable.

## Contrato de cálculo confirmado

`Física = (Física_1 + Física_2) / 2`

`Académica = nota_global_manual_respaldada_por_historial`

`Desempeño = (Desempeño_Jefe + Desempeño_Comandante) / 2`

`resultado_sin_redondear = (Física + Académica + Desempeño) / 3`

Si falta un componente, no hay resultado numérico. Si falta alguna nota física, Física queda incompleta. Si falta alguna aportación de Desempeño, también queda incompleto. No redistribuir importancia entre componentes ni sustituir falta por cero.

Con los cinco datos de entrada completos, la fórmula equivalente es:

`resultado_sin_redondear = (Física_1 + Física_2 + 2 × Académica + Desempeño_Jefe + Desempeño_Comandante) / 6`

Esto conserva igual importancia de los tres componentes: no es el promedio simple de las cinco notas de entrada. Los ejemplos son aritméticos para el prototipo; no acreditan validez institucional.

Conservar precisión en promedios internos y redondear solo el resultado final a dos decimales, mitad hacia arriba. No sustituir divisiones exactas por coeficientes porcentuales truncados. Las notas nuevas ingresadas admiten hasta dos decimales; no redondear su entrada silenciosamente. Los datos históricos mantienen su precisión original y requieren referencias reproducibles, sin migración que los altere.

### Casos de aceptación confirmados

| Entradas o valor previo al redondeo | Resultado esperado |
|---|---|
| Física 1 = 80; Física 2 = 100 | Física = 90; conservar referencia de ambas notas. |
| Física 1 = 80; Física 2 ausente | Física incompleta; resultado conjunto no calculable. |
| Desempeño Jefe = 80; Comandante = 100 | Desempeño = 90. |
| Desempeño Jefe = 80; Comandante ausente | Desempeño incompleto; resultado conjunto no calculable. |
| Componentes completos Física = 80, Académica = 90, Desempeño = 100 | Resultado conjunto 90,00. |
| Algún componente ausente | Incompleto / No calculable; resultado numérico ausente, distinto de 0. |
| Todos los datos obligatorios registrados como 0 | Resultado 0,00; no tratar como incompleto. |
| Alguna nota ingresada fuera de 0–100 | Entrada rechazada, sin corrección automática. |
| Nota nueva 82,345 | Rechazo por más de dos decimales. |
| Física 1 = 80,01; Física 2 = 80,02 | Física interna = 80,015; no sustituirla por 80,02 antes del promedio conjunto. |
| Resultado sin redondear 82,345 / 82,344 | Resultado final 82,35 / 82,34, respectivamente. |
| Persona sin cursos registrados | Académica pendiente; no fabricar nota ni cero; resultado conjunto no calculable. |
| Académica sin motivo o con referencia a formación de otra persona | Entrada rechazada. |
| Física 1 = 80; Física 2 = 80,01; Académica = 80; Desempeño Jefe = 80; Comandante = 80,01 | Resultado sin redondear 80,003333…; final 80,00. Redondear antes los componentes produciría un resultado incorrecto. |

## Estado de implementación y límites

Primera entrega v15: rol Comandante/cuenta única/panel, consulta de seguimiento autorizada sin observaciones ajenas, cinco fuentes de notas independientes, respaldo académico y correcciones con responsable/autor preservados. Esquemas anteriores y notas históricas conservados, sin adopción automática.

Aún pendientes ciclo anual/publicación/congelación, asociación de fuentes con evaluaciones configuradas, activo único por período, cálculo y cierres/reaperturas con instantáneas. No confundir instantáneas del respaldo académico con instantáneas de resultado cerrado; estas últimas no existen aún. Pantalla/API de notas por asignación anteriores siguen compatibles y no se incorporan al cálculo 5B automáticamente.

No se asignan umbrales de aprobación, apto/no apto, promociones ni decisiones automáticas. Sin aprobación institucional de puntuación ni psicometría; fuera de alcance grupos múltiples. Aceptación de 5A/piloto y privacidad/retención mantienen sus pendientes.

## Criterios verificables para la implementación posterior

- Rechazar dos períodos activos simultáneos y cambios no autorizados; respetar períodos históricos sin migración silenciosa.
- No permitir notas nuevas/correcciones en BORRADOR o CERRADO conforme al alcance confirmado; Instructor y personas fuera de ámbito sin acceso numérico.
- Publicación atómica con fuentes/evaluaciones válidas, promedio simple exacto, configuración congelada y resultados ligados a ella.
- Académica con motivo y formación propia referenciada; Comandante limitado a su aportación sin observaciones ajenas ni administración.
- Casos completos, dos notas físicas obligatorias, evidencia académica, aportaciones de desempeño, faltantes/cero, última corrección válida y redondeo final según decisiones aprobadas.
- Cierre permitido con incompletos identificados; reapertura motivada sin segundo activo ni cambio de configuración, autor/fecha, instantáneas preservadas y resultados anteriores reproducibles.
- Pruebas HTTP de permisos/CSRF y concurrencia; UI responsiva y estados vacío/error/incompleto; migraciones aditivas con respaldo solo si son necesarias.

Referencias: [plan](05_plan_desarrollo.md), [cierre 5A](08_cierre_fase_5a.md), [README](../README.md), [AGENTS](../AGENTS.md) e [historial](../HISTORY.md).

## Secuencia concreta para implementar 5B

1. **Implementado v15:** rol Comandante/cargo único SBRAB, fuentes separadas, respaldo académico y autorización por actor/objeto; migración preservando históricos.
2. Borradores/configuración anual, publicación/congelación, activación única y guardado/corrección solo en ACTIVO.
3. Cálculo provisional exacto, faltantes, redondeo y casos de aceptación aprobados.
4. Cierre con instantáneas, reapertura motivada, conservación/reproducción y revisión por rol.

El siguiente trabajo continúa desde la etapa 2. La base local ya está migrada a v15; no recrear entorno/base ni repetir migración sin necesidad.
