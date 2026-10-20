# Reincorporación de participantes en Operaciones — 2026-10-20

El solicitante confirmó que un Instructor retirado debe volver a aparecer en Asignar participantes y que su reincorporación recupera la calificación anterior y su aporte académico. Esta decisión sustituye el bloqueo de reasignación descrito en la entrega v27.

La lista excluye únicamente participantes vigentes. Un Instructor activo retirado vuelve a estar disponible; al asignarlo se reutiliza su participación, se incrementa la revisión y se registra REINGRESO, sin duplicar vínculos ni notas. Un nuevo retiro registra otro movimiento y conserva el primero. Calificaciones y correcciones previas permanecen intactas; el cálculo abierto vuelve a incluir la nota vigente. Las notas publicadas conservan su circuito de republicación.

La reincorporación mantiene permisos de Administrador/Jefe, cuenta activa, operación sin baja y transacción íntegra. Se bloquea si la participación tiene notas en cualquier Gestión cerrada, hasta reapertura administrativa. Duplicar una participación vigente sigue devolviendo conflicto. Retiro conserva motivo y revisión; reingreso registra actor, fecha y motivo descriptivo de la asignación. No modifica instantáneas de cierre.

## SQLite v33

Tabla append-only movimientos_participacion_operacion con clave operación/persona/revisión, tipo RETIRO/REINGRESO, motivo, actor y fecha. Vista retiros_operacion_vigentes resuelve el estado actual mediante el último movimiento, o el retiro original si no hay movimientos. No se borran ni modifican retiros_operacion ni notas. Cálculo, paneles, consulta de participantes y reporte individual utilizan la vista vigente.

Migración local respaldada en instance/backups/sicose-20261020-pre-v33-1228ca21.sqlite3: 74 tablas previas preservadas íntegramente salvo schema_version, 75 finales, una nueva vacía, dos aplicaciones idempotentes, quick_check=ok y cero infracciones FK. Evidencia .tmp/reingresos-migracion.json. Sin reincorporaciones, retiros o publicaciones reales creados por el agente. Entorno, modelos y datos previos conservados.

## Verificación

23 regresiones aprobadas en 58,552 s, log .tmp/reingresos-regresion.log: Operaciones v26/v27, panel del Instructor y reporte individual. Incluyen ciclos repetidos de retiro/reingreso, recuperación del aporte, conservación de notas/retiro original, lote inválido sin cambios parciales, cuenta inactiva, cierre/reapertura, migración v32 idempotente y movimientos inmutables. Las expectativas de esquema vigente se actualizan a v33; las versiones de partida históricas no se cambian. Sintaxis JavaScript y diff comprobados. Sin nueva suite general ni recorrido visual completo del modal.
