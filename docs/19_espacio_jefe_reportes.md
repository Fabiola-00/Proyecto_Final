# Espacio de trabajo del Jefe de Personal — 2026-10-14

Entrega posterior a la aceptación operativa de 5B, con SQLite v23 y sin migración. Esta reorganización tiene su propia verificación técnica; no amplía la aceptación humana anterior ni acredita aprobación institucional.

## Navegación y alcance

- Espacio de Trabajo: Inicio.
- Personal y Operaciones: Instructores Voluntarios, Asistencias, Cursos y Capacitaciones, Operaciones.
- Evaluación Anual: Gestión, Evaluaciones, Notas y Resultados, Reportes.

Inicio consulta cifras globales de SBRAB: personal admitido por estado, finalizaciones personales de todos los años, operaciones iniciadas en el año de Bolivia y evaluaciones habilitadas de cuentas activas en la gestión activa. Los gráficos son descriptivos; pendientes y No cumplidas permanecen separados. Sin gestión activa, la tarjeta de pendientes indica No disponible. Las asignaciones históricas a un Jefe no limitan estas consultas.

Gestión ofrece consulta del año/estado, edición de borradores elegibles y eliminación lógica motivada. Conserva las restricciones, valores anteriores y comprobaciones de concurrencia del backend. La pantalla simplificada no incluye formularios de configuración, cálculo, publicación, cierre ni creación; el permiso previo de crear borradores mediante API se conserva. **El solicitante confirmó mantener la activación del ciclo exclusivamente en el Administrador**, igual que su configuración y regla de cálculo. Las gestiones retiradas permanecen identificadas para consulta.

Evaluaciones reúne habilitación individual y activación de los seis ítems comunes por gestión. Cambiar la activación anual exige motivo y revisión vigente; psicometría continúa condicionada. Habilitar personas conserva las restricciones existentes de cuenta activa, gestión activa y fuente habilitada. Notas y Resultados conserva su pantalla y reglas. El menú del Administrador y el del Instructor conservan sus opciones previas. La tarjeta Reportes del Inicio administrativo ahora enlaza al centro disponible.

## Operaciones

**Confirmado por el solicitante:** Administrador y Jefe crean y editan operaciones y asignan participantes globalmente. Los formularios de creación/edición y asignación utilizan el modal común. La asignación admite varios checkbox de personas activas; excluye ya asignadas de la lista. El backend conserva la entrada singular `voluntario_id` y añade `voluntario_ids` (1–500 enteros únicos). Transacción serializada: si una persona está inactiva o ya participa, se rechaza el lote completo. No se incorpora borrado ni desvinculación; el Instructor consulta exclusivamente sus participaciones.

## Centro de reportes

`/gestion/reportes`, solo Administrador/Jefe, centraliza los PDF existentes de evaluaciones, asistencia y catálogo de cursos, y añade:

- `/api/reportes/formacion.pdf?desde=AAAA-MM-DD&hasta=AAAA-MM-DD`: finalizaciones personales vigentes dentro del rango inclusivo; nombre/código, curso/tipo/entidad capturados al asignar, fecha personal y puntos. No incluye pendientes ni los transforma en cero; cero finalizado se conserva. No equivale a una publicación propia ni a instantánea de cierre.
- `/api/reportes/operaciones.pdf?desde=AAAA-MM-DD&hasta=AAAA-MM-DD`: operaciones iniciadas dentro del rango inclusivo, con evento/lugar/fechas/institución y nombre/código de cada participante. Incluye eventos sin participantes; cada participación ocupa una fila.

Los dos nuevos reportes incluyen participantes históricos aunque su cuenta esté inactiva. Excluyen contactos, credenciales, observaciones, motivos y autores privados mediante selección explícita de campos. Son privados `no-store`, con auditoría de generación, carimbo SBRAB, hora de Bolivia y encabezados repetidos. Se rechazan fechas inválidas, orden invertido, parámetros extra o repetidos. Los accesos contextuales existentes de cursos/asistencia se conservan; en la nueva pantalla Evaluaciones el PDF se genera desde Reportes.

## Verificación del 2026-10-14

Tres pruebas nuevas de navegación/permisos, filtros/privacidad y asignación atómica aprobadas en 6,535 s. Recorrido con Flask real en loopback y base DEMO aislada: Jefe crea operación/asigna por checkbox, desactiva/reactiva Física 2 por gestión y descarga ambos PDF. Veinticuatro escenarios visuales: cinco pantallas y modal de edición, 360/1447 px y ambos temas; sin errores JavaScript ni desbordes, capturas inspeccionadas tras esperar el estado estable de las transiciones. PDF de formación/operaciones, caso vacío y paginación de 80 filas/11 páginas renderizados e inspeccionados; encabezados y ceros preservados.

Evidencias locales: `.tmp/espacio-jefe/`, `.tmp/espacio-dirigidas.log` y `.tmp/espacio-suite-final.log`. Suite final y controles: ver registro final de esta entrega en HISTORY.md. No se ejecuta seed, inicialización ni migración; no se modifica la base de trabajo.

Consulta de integridad solo lectura de la base de trabajo: v23, quick_check=ok y cero infracciones de claves foráneas. Frente al respaldo anterior a v23, 40 de las 42 tablas de datos comparadas coinciden; usuarios conserva los mismos IDs y solo difiere en ultimo_acceso/actualizado_en, y auditoría tiene 217 filas frente a 213. No se restauran ni sobrescriben estas diferencias de uso. app_meta conserva el cambio histórico esperado 22→23. Las escrituras del recorrido y las pruebas se limitaron a bases DEMO aisladas.

Comprobación adicional: borrador editado y retirado con motivo desde el modal; error de fechas de operación visible dentro del modal. Otros seis escenarios móviles en ambos temas (menú del Jefe desplegado y paneles de Administrador/Instructor) sin errores/desbordes; nueve enlaces únicos del Jefe, incluido Reportes accesible. Total visual: 30 escenarios. Servidores DEMO detenidos y bases temporales retiradas con integridad v23/quick_check=ok/FK=0.

Regresión dirigida final: cuatro pruebas aprobadas en 10,106 s, incluida asignación efectiva de dos participantes y preservación del permiso administrativo de activación; prueba del Inicio administrativo aprobada en 0,664 s tras conectar Reportes. El primer recorrido completo (138 pruebas/357,051 s) tuvo una aserción de marcado antiguo del enlace Gestión; corregida y aprobada en la regresión dirigida. La pasada completa final se registra por separado.


Verificación final del 2026-10-14: **138 pruebas aprobadas en 354,019 s**; cuatro dirigidas finales en 10,106 s y una del Inicio administrativo en 0,664 s. Treinta escenarios visuales con Flask real/base DEMO, 360/1447 px y ambos temas, sin errores JavaScript ni desbordes; capturas revisadas. Dos PDF nuevos, caso vacío y paginación de 80 filas/11 páginas renderizados e inspeccionados. Compilación Python, seis JavaScript, 159 enlaces en 22 documentos y git diff --check correctos. Sin migración, nuevas dependencias ni seed de la base de trabajo; v23/quick_check=ok/FK=0 en consulta solo lectura. Entorno, fotos, historial y trabajo local previo conservados. Servidores DEMO detenidos y sus bases temporales retiradas. La aceptación operativa previa de 5B no se extiende automáticamente a esta reorganización; aprobación institucional/piloto conservan sus pendientes.


### Modelo anual de cinco entradas — 2026-10-15, v24

Acuerdos posteriores al corte v23: Gestión con fechas propias; Jefe inicia y cierra, reapertura administrativa. Inicio registra ceros oficiales salvo dos psicométricas pendientes. Académica suma cursos y notas de operaciones del intervalo hasta 100; sin operaciones, estado Pendiente y aporte cero. Física y Desempeño conservan sus dos fuentes. Formato CINCO_ENTRADAS_V3 separado de históricos V1/V2, sin adopción ni reseteo al migrar. Modelo SIN_ENTRENAR y sin recomendaciones; no se sustituye por promedio. Instructor sin acceso v3 hasta publicación específica, aún pendiente; PDF v3 también pendiente. [Reglas, APIs, compatibilidad y verificación](20_modelo_anual_cinco_entradas.md). La aceptación previa de 5B no se extiende a esta reformulación.


## Reorganización posterior — 2026-10-15, v25

Véase [espacio de trabajo vigente](21_organizacion_espacio_trabajo.md): Gestión/Evaluaciones sin duplicación, eliminación permanente solo sin resultados/evidencia protegida, cursos con baja y retirada auditadas, físicas v3 sin fechas, estados propios, ejemplos aritméticos sin valor psicométrico y PDF anual v3 administrativo. Cierres/históricos conservados. La aceptación anterior no se extiende automáticamente a este cambio; psicometría oficial, publicación numérica propia v3, IA, institución y piloto pendientes.
