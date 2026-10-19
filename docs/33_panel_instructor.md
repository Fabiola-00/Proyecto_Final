# Panel del Instructor Voluntario

Decisiones confirmadas por el solicitante e implementación del 2026-10-19, SQLite v32. Sustituye la ocultación de Desempeño para la consulta propia del modelo anual: se permite únicamente su promedio publicado. Las notas individuales del Jefe/Comandante, observaciones, autores y recomendaciones siguen fuera de esta consulta.

## Presentación y alcance

- Inicio: cuatro cuadros compactos de la Gestión activa no retirada: Evaluaciones Asignadas, Evaluaciones Completadas, Evaluaciones Pendientes y Cantidad de Cursos Completados. Se cuentan Física 1, Física 2, Académica y Desempeño conjunto; no se incluyen pruebas psicométricas ni ejercicios. El cero inicial no acredita una evaluación completada. Académica se considera registrada cuando tiene formación finalizada o una nota vigente de operación no retirada dentro del intervalo; Desempeño requiere ambas fuentes habilitadas y calificadas. Los cursos completados se cuentan por finalización personal dentro del intervalo. Sin Gestión activa, los cuatro contadores son cero.
- Se elimina «Tu avance». «Mis Evaluaciones» queda como aviso de evaluaciones habilitadas pendientes, sin notas.
- Perfil se sitúa al pie de la barra lateral, inmediatamente antes de «PERÍODO ACTUAL».
- Asistencias: selector de Gestión y cuatro gráficos mensuales de registros propios por Asiste/Atraso/Permiso/Falta. Respeta fechas inclusivas, meses parciales, meses vacíos y cruces de año. Cuenta registros por actividad, sin convertir días sin registro en Falta. Se sustituye el calendario completo.
- Cursos: selector de Gestión y tabla con el estilo de Operaciones. Se incluyen las participaciones cuyo curso se solapa con el intervalo o cuya finalización personal pertenece a él. Se conserva el estado personal y solo se muestra la calificación de la última publicación disponible para esa Gestión.
- Operaciones: selector de Gestión, filtrado por solapamiento inclusivo de fechas y participaciones exclusivamente propias. Se conserva la tabla y su detalle existentes; el API histórico sin parámetros continúa disponible.
- Evaluaciones: selector de Gestión y resultados publicados de las dos físicas, promedio físico, Académica y promedio de Desempeño. No muestra el resultado conjunto ni las notas individuales de Desempeño. Las Gestiones históricas conservan su publicación anterior; las que no contienen un promedio publicado muestran «Sin publicar».
- Pruebas conserva su tabla, formularios y privacidad actuales.

Cada selector ofrece Gestiones iniciadas activas/cerradas no retiradas; preselecciona la activa o, si no existe, la más reciente. La selección no admite indicar otra persona. No cambia habilitaciones, cálculos, modelos, respuestas ni publicaciones reales.

## Publicación del modelo anual

La publicación histórica depende de `reglas_calculo_5b` mediante clave foránea y no admite las Gestiones V3. Por ello se añade `publicaciones_modelo_anual`, referida a `modelos_anuales`, sin modificar las tablas históricas. Versiones enlazadas, índice de publicación inicial y triggers de inmutabilidad conservan el historial. La instantánea de cierre incluye la publicación anual correspondiente.

Administrador/Jefe pueden revisar y publicar desde la persona seleccionada en Evaluaciones: físicas, Académica y únicamente el promedio de Desempeño, con motivo obligatorio. Se exige cuenta activa, Gestión activa no retirada, fuentes habilitadas, revisión publicada y firma vigente; cierre e inactividad bloquean la acción. Una corrección conserva la versión publicada anterior hasta republicación. Una fuente deshabilitada oculta lo publicado y rehabilitarla recupera esa versión, sin adoptar correcciones nuevas automáticamente. No hay publicación automática al iniciar, cerrar o migrar.

## Migración local verificada

`scripts/migrar_panel_instructor_v32.py` aplicó v31→v32 tras respaldo `instance/backups/sicose-20261019-pre-v32-e7b973fd.sqlite3`. Dos inicializaciones, 73 tablas previas preservadas mediante comparación de huellas y filas (salvo `schema_version`), 74 finales, una tabla nueva vacía, `quick_check=ok`, cero errores de claves foráneas. Evidencia en `.tmp/panel-instructor-migracion.json`. Sin publicaciones, respuestas, cuentas ni activaciones reales creadas; `.env`, `.venv`, fotos y modelos preservados.

## Verificación

Seis pruebas nuevas aprobadas en 17,926 s: publicación y promedio con redondeo, corrección/republicación, privacidad, deshabilitación, cierre, Inicio, límites mensuales, filtros propios de operaciones y notas de cursos conservadas hasta republicación. Las pruebas usan SQLite temporal.

Recorrido con servidor Flask y base sintética aislados: seis vistas del Instructor a 360 px y 1484 px, sin desborde global medido. Se inspeccionaron capturas de Inicio, Asistencias, Cursos, Evaluaciones y Pruebas; se comprobaron modos claro y oscuro en el recorrido, sin afirmar una matriz completa de ambos temas para cada vista. La tabla de Evaluaciones admite desplazamiento horizontal interno en móvil. No equivale a aceptación humana ni institucional.

Regresión final de 18 pruebas aprobada en 34,410 s (`.tmp/panel-instructor-regresion-final.log`): seis del panel, diez de publicación histórica y las dos expectativas de Inicio ajustadas al diseño solicitado. Python compilado, ambos JavaScript modificados con sintaxis correcta y `git diff --check` sin errores. El control administrativo de publicación se abrió y envió también mediante navegador con el Jefe sintético, sin errores de consola observados; únicamente sobre la base aislada.

Suite general ejecutada: 259 pruebas en 598,652 s; 257 aprobadas y dos expectativas antiguas de texto de Inicio fallaron (`Cursos asignados` y `Privacidad personal`). Se actualizaron al diseño autorizado y ambas pasaron dentro de la regresión final de 18 pruebas. No se ejecutó una segunda suite general ni se declara 259/259 aprobadas. Log `.tmp/panel-instructor-suite.log`.

Control final: 89 enlaces locales válidos en README, AGENTS, HISTORY y este documento; base local consultada en solo lectura v32/quick_check=ok/FK=0, tabla nueva con cero publicaciones. Servidor de ensayo detenido y sus dos bases sintéticas retiradas tras verificar su identidad.
