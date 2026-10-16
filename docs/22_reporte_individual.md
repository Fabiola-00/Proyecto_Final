# Reporte individual del Instructor Voluntario - 2026-10-16

## Uso y alcance

En Reportes, Administrador/Jefe selecciona un Instructor Voluntario admitido y genera un PDF que abre en otra pestaña. La Gestión se resuelve automáticamente desde el único período ACTIVO no retirado; no se confunde con el año calendario del servidor ni se activa una Gestión. El formulario envía su identificador para detectar un cambio de Gestión entre consulta y generación. Sin Gestión activa o con selección obsoleta se devuelve conflicto explícito.

El reporte admite perfiles ACTIVO/INACTIVO para consulta administrativa. Instructor no accede a esta exportación porque incluye fuentes de Desempeño y datos administrativos. Las rutas comprueban roles en backend; seleccionar un ID distinto no amplía el acceso a cuentas pendientes/rechazadas ni a otros roles.

## Contenido

1. Perfil: fotografía disponible, código, nombre completo, nombres/apellidos, nacimiento, grado, cuenta, correo/usuario, nacionalidad, residencia, incorporación, antigüedad y especialidades principal/secundarias; experiencia previa registrada como dato del perfil, sin convertirla en participación. Los datos ausentes dicen Sin registrar; sin fotografía válida se informa su ausencia. No se exponen contraseñas, hashes, tokens, versión de contraseña ni rutas de archivos.
2. Calificaciones: las dos físicas y las dos fuentes de Desempeño, sus estados/orígenes y los componentes Físico, Desempeño promediado y Académico con la regla del sistema. Se distinguen ceros oficiales de inicio, notas registradas y deshabilitación. No se redistribuyen pesos ni se cambia el cálculo. Los valores exactos que requieren más de dos decimales se conservan.
3. Cursos: participaciones con intervalo capturado al asignar que solapa la Gestión o finalización personal dentro de ella. Incluye Finalizado, En curso, Asignado y No completado; retirada identificada. Se muestran nombre, tipo, entidad, fechas, estado, finalización y puntaje personal cuando existe. El catálogo actual no reemplaza la copia capturada al asignar.
4. Operaciones: participaciones personales con solapamiento inclusivo del intervalo, fecha inicial como referencia si el histórico carece de fin; tipo, institución, lugar, fechas y última nota de esa Gestión cuando existe. No se califican participaciones desde el reporte.
5. Asistencia: Asiste/Atraso/Permiso/Falta y porcentaje (Asiste+Atraso)/(Asiste+Atraso+Falta), dos decimales; Permiso excluido. Sin denominador No disponible; sin registro no equivale a Falta. Conteo por registros personales, sin gráfico y separado de las notas.
6. Dos psicométricas oficiales pendientes, cada una con su apartado de resultado y subescalas pendientes de seleccionar/aprobar el instrumento. No se incorporan resultados demostrativos ni se inventan subescalas o una puntuación única.
7. Recomendación de ascenso/operaciones pendiente: modelo sin entrenar/validar, sin inferencia ni recomendación fabricada.

El PDF presenta información vigente consultada en una transacción, con fecha/hora de Bolivia. Es una exportación de Gestión activa, no una instantánea de cierre ni una publicación propia del Instructor. Los otros reportes conservan su alcance.

## Presentación y referencias de RR. HH.

Formato A4 vertical, paleta institucional clara para impresión, foto proporcionada, carimbo con emblema/nombre completo SBRAB en todas las páginas, pie confidencial con código/fecha/página. Secciones numeradas, tablas con encabezados repetidos, texto seleccionable y distribución multipágina automática para muchos registros. No se presenta como PDF/UA certificado ni como documento clínico.

La propuesta de diseño aplica criterios de claridad y trazabilidad basados en estas referencias, sin atribuirles aprobación del documento ni suponer normativa boliviana:

- [CIPD - People analytics](https://www.cipd.org/en/knowledge/factsheets/analytics-factsheet/): decisiones sobre personas basadas en evidencia; separar datos descriptivos de inferencias. Se refleja en resultados verificables y recomendación explícitamente pendiente.
- [CIPD - Privacy policy](https://www.cipd.org/en/privacy-policy/): referencia de práctica institucional de confidencialidad y corrección de datos, no una norma jurídica aplicable a SBRAB.
- [GOV.UK - Publishing accessible documents](https://www.gov.uk/guidance/publishing-accessible-documents): lenguaje claro, estructura simple, títulos y encabezados de tabla. Se aplica a la organización visual; el PDF generado no acredita etiquetado accesible integral.

## Implementación y seguridad

- `GET /api/reportes/individual/contexto`: Gestión activa y selector mínimo de personas admitidas.
- `GET /api/reportes/individual/<uid>.pdf?periodo_id=<activa>`: exportación administrativa privada `no-store`, disposición `inline`, sin guardar copias de datos reales en el repositorio.
- Fotografía: solo el nombre interno PNG/JPG con formato admitido dentro de la carpeta de medios configurada. Contenido validado/normalizado en memoria y proporción conservada; ausencia/corrupción produce marcador legible, no una foto inventada.
- Auditoría mínima de actor/persona/Gestión y acción de generación, sin respuestas psicométricas o datos personales completos en el registro.
- Sin dependencias nuevas, migración, seed ni cambios de `.venv`, `.env` o base de trabajo. Pruebas y ejemplo exclusivamente en bases temporales DEMO.

## Verificación

Cinco pruebas específicas cubren PDF real con foto, dos gestores, privacidad/inline, auditoría, alcance de fechas, cursos pendientes, operaciones/calificaciones, porcentaje, falta de Gestión activa, selección obsoleta, parámetros, ausencia de datos/foto y acceso denegado a Instructor. El ejemplo sintético en `output/pdf/reporte-individual-demo.pdf` tiene tres páginas renderizadas e inspeccionadas; cifras, encabezados/pies, imagen y ausencia de secretos comprobados por extracción. La regresión relevante y sus resultados exactos se registran en HISTORY al finalizar la entrega.

Pendientes: psicometría autorizada con subescalas definitivas, modelo entrenado/validado, aceptación humana del nuevo reporte y requisitos institucionales. No se da por aprobada la salida por las pruebas automáticas.
