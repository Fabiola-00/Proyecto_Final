# 03. Modelo de datos inicial

Modelo lógico propuesto para SQLite. Claves foráneas habilitadas; IDs internos no secuenciales públicos recomendables (UUID) o ids con controles contra enumeración. Fechas almacenadas UTC en ISO-8601. Cada entidad incluirá `creado_en` y, cuando aplique, `actualizado_en`.

## Entidades

- **usuario** (`id`, `nombre`, `apellido`, `correo` único normalizado, `password_hash`, `rol`, `estado`, `creado_en`, `ultimo_acceso`): rol administrador/instructor/voluntario y estado pendiente/activo/inactivo/rechazado.
- **solicitud_registro** (`id`, datos mínimos, `correo`, `estado`, `codigo_invitacion_id` nullable, `revisado_por`, `revisado_en`): no equivale a cuenta habilitada.
- **invitacion** (`id`, `codigo_hash`, `rol_objetivo`, `creada_por`, `expira_en`, `usada_en`, `estado`): no persistir el código secreto en claro.
- **perfil_voluntario** (`usuario_id` PK/FK, `instructor_id`, `experiencia_operaciones`, `antiguedad_desde`, `estado_servicio`). Inactividad lógica conserva relaciones/historial.
- **curso_voluntario** (`id`, `voluntario_id`, `nombre`, `entidad`, `fecha`, `observacion`).
- **registro_asistencia** (`id`, `voluntario_id`, `fecha`, `estado`, `actividad_id`, `registrado_por`). Política de corrección/auditoría por decidir.
- **periodo** (`id`, `nombre`, `fecha_inicio`, `fecha_fin`, `estado`, `creado_por`).
- **version_ponderacion** (`id`, `periodo_id`, `version`, `estado`, `aprobado_por`, `aprobado_en`, `vigente_desde`), única por período y versión.
- **peso_evaluacion** (`version_id`, `tipo_evaluacion_id`, `peso`): único por tipo/versión; suma validada en servicio/transacción = 1.0 antes de activar.
- **tipo_evaluacion** (`id`, `codigo`, `nombre`, `categoria`, `origen_nota`, `instrumento_id` nullable, `activo`): 3 psicométricas, física, académica, criterio instructor.
- **instrumento** (`id`, `nombre`, `version`, `idioma`, `fuente_url`, `licencia`, `estado_aprobacion`, `regla_puntuacion_referencia`, `responsable_revision`): solo candidatos documentales; no cargar reactivos hasta autorización.
- **asignacion_evaluacion** (`id`, `voluntario_id`, `periodo_id`, `tipo_evaluacion_id`, `estado`, `habilitada_por`, `fecha_habilitacion`): estado no_habilitada/habilitada/en_progreso/completada.
- **intento** (`id`, `asignacion_id`, `numero`, `estado`, `iniciado_en`, `enviado_en`, `puntuacion_bruta`, `nota_0_100`, `calculo_version`): único por asignación y número. No actualizar un intento enviado al reiniciar.
- **calificacion** (`id`, `asignacion_id`, `nota_0_100`, `observacion`, `registrada_por`, `registrada_en`, `corregida_de_id` nullable): historial de correcciones append-only; aplicar una única calificación vigente sin borrar anteriores.
- **auditoria** (`id`, `actor_id`, `accion`, `entidad`, `entidad_id`, `fecha`, `metadatos_minimos`, `resultado`): acceso restringido y sin secretos.
- **solicitud_analisis_ia** (futuro; `id`, `voluntario_id`, `periodo_id`, `solicitada_por`, `estado`, `modelo_version`, `salida`, `revision_profesional`, marcas de tiempo): no crear hasta política/modelo aprobados.

## Relaciones e invariantes

Usuario voluntario 1:1 perfil; instructor se relaciona con voluntarios asignados; período 1:N versiones; versión N:M tipos mediante pesos; asignación une persona, período y tipo; asignación 1:N intentos y calificaciones históricas. No hay borrado en cascada para historial de evaluación. FKs `RESTRICT` o `SET NULL` con política explícita; desactivación lógica para usuarios.

Integridad: nota dentro de 0–100; peso dentro de 0–1; estados restringidos; invitación de un solo uso; intento número único; correo normalizado único; suma de pesos validada atómicamente antes de publicar versión. El promedio requiere política para faltantes, intentos válidos y redondeo, pendiente de decisión institucional.

## Sensibilidad y retención

Respuestas psicométricas son datos de acceso restringido y pueden no ser necesarias tras el cálculo; definir retención, exportación, corrección y eliminación/anónimo conforme a política y normativa aplicable antes de datos reales. Las recomendaciones de IA no se almacenarán porque no hay modelo implementado.
