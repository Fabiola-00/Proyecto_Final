CREATE TABLE IF NOT EXISTS app_meta (
    clave TEXT PRIMARY KEY,
    valor TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE CHECK (nombre IN ('ADMINISTRADOR', 'JEFE_PERSONAL', 'INSTRUCTOR_VOLUNTARIO', 'COMANDANTE_GRUPO'))
);

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL COLLATE NOCASE UNIQUE CHECK (length(username) BETWEEN 3 AND 80),
    nombre_completo TEXT NOT NULL CHECK (length(nombre_completo) BETWEEN 1 AND 160),
    correo TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    password_version INTEGER NOT NULL DEFAULT 1 CHECK (password_version > 0),
    foto_perfil TEXT,
    rol_id INTEGER NOT NULL REFERENCES roles(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    estado TEXT NOT NULL DEFAULT 'ACTIVO' CHECK (estado IN ('PENDIENTE', 'ACTIVO', 'INACTIVO', 'RECHAZADO')),
    creado_en TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    actualizado_en TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ultimo_acceso TEXT
);

CREATE TABLE IF NOT EXISTS instructores (
    usuario_id INTEGER PRIMARY KEY REFERENCES usuarios(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    especialidad TEXT,
    creado_en TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS voluntarios (
    usuario_id INTEGER PRIMARY KEY REFERENCES usuarios(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    instructor_id INTEGER REFERENCES instructores(usuario_id) ON UPDATE RESTRICT ON DELETE SET NULL,
    nombres TEXT,
    apellido_paterno TEXT,
    apellido_materno TEXT,
    fecha_nacimiento TEXT,
    codigo_instructor TEXT UNIQUE,
    especialidad_principal TEXT CHECK (especialidad_principal IS NULL OR especialidad_principal IN ('Rescate en agua', 'Rescate en montaña', 'Rescate en selva', 'Lucha contra incendios', 'Primeros Auxilios', 'K-9')),
    experiencia_operaciones TEXT,
    antiguedad_desde TEXT,
    fecha_incorporacion TEXT,
    grado TEXT CHECK (grado IS NULL OR grado IN ('Instructor Inicial','Instructor Segundo','Instructor Primero','Instructor Principal','Instructor Mayor')),
    pais_residencia TEXT CHECK (pais_residencia IS NULL OR pais_residencia = 'Bolivia'),
    departamento_residencia TEXT CHECK (departamento_residencia IS NULL OR departamento_residencia IN ('Beni','Chuquisaca','Cochabamba','La Paz','Oruro','Pando','Potosí','Santa Cruz','Tarija')),
    ano_incorporacion INTEGER CHECK (ano_incorporacion IS NULL OR (typeof(ano_incorporacion) = 'integer' AND ano_incorporacion BETWEEN 1 AND 9999)),
    creado_en TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS solicitudes_registro (
    id INTEGER PRIMARY KEY,
    usuario_id INTEGER NOT NULL UNIQUE REFERENCES usuarios(id) ON DELETE RESTRICT,
    invitacion_id INTEGER REFERENCES invitaciones(id) ON DELETE RESTRICT,
    estado TEXT NOT NULL DEFAULT 'PENDIENTE'
        CHECK (estado IN ('PENDIENTE', 'APROBADA', 'RECHAZADA')),
    revisada_por INTEGER REFERENCES usuarios(id) ON DELETE RESTRICT,
    revisada_en TEXT,
    creada_en TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS invitaciones (
    id INTEGER PRIMARY KEY,
    token_hash TEXT NOT NULL UNIQUE,
    correo TEXT,
    creada_por INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    expira_en TEXT NOT NULL,
    utilizada_en TEXT,
    creada_en TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS periodos (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE,
    fecha_inicio TEXT NOT NULL,
    fecha_fin TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'BORRADOR' CHECK (estado IN ('BORRADOR', 'ACTIVO', 'CERRADO')),
    creado_por INTEGER REFERENCES usuarios(id) ON DELETE RESTRICT,
    creado_en TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    CHECK (fecha_fin >= fecha_inicio)
);

CREATE TABLE IF NOT EXISTS instrumentos (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    version TEXT NOT NULL,
    idioma TEXT NOT NULL,
    fuente_url TEXT,
    licencia TEXT,
    estado_aprobacion TEXT NOT NULL DEFAULT 'PENDIENTE'
        CHECK (estado_aprobacion IN ('PENDIENTE', 'APROBADO', 'RECHAZADO')),
    regla_puntuacion_referencia TEXT,
    responsable_revision TEXT,
    creado_en TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    UNIQUE (nombre, version, idioma)
);

CREATE TABLE IF NOT EXISTS evaluaciones (
    id INTEGER PRIMARY KEY,
    codigo TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    categoria TEXT NOT NULL CHECK (categoria IN ('PSICOMETRICA', 'FISICA', 'ACADEMICA', 'JEFE_PERSONAL')),
    origen_nota TEXT NOT NULL CHECK (origen_nota IN ('INSTRUCTOR_VOLUNTARIO', 'JEFE_PERSONAL')),
    instrumento_id INTEGER REFERENCES instrumentos(id) ON DELETE RESTRICT,
    activo INTEGER NOT NULL DEFAULT 0 CHECK (activo IN (0, 1)),
    creado_en TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS asignaciones_evaluacion (
    id INTEGER PRIMARY KEY,
    voluntario_id INTEGER NOT NULL REFERENCES voluntarios(usuario_id) ON DELETE RESTRICT,
    periodo_id INTEGER NOT NULL REFERENCES periodos(id) ON DELETE RESTRICT,
    evaluacion_id INTEGER NOT NULL REFERENCES evaluaciones(id) ON DELETE RESTRICT,
    estado TEXT NOT NULL DEFAULT 'NO_HABILITADA'
        CHECK (estado IN ('NO_HABILITADA', 'HABILITADA', 'EN_PROGRESO', 'COMPLETADA')),
    habilitada_por INTEGER REFERENCES usuarios(id) ON DELETE RESTRICT,
    habilitada_en TEXT,
    UNIQUE (voluntario_id, periodo_id, evaluacion_id)
);

CREATE TABLE IF NOT EXISTS versiones_ponderacion (
    id INTEGER PRIMARY KEY,
    periodo_id INTEGER NOT NULL REFERENCES periodos(id) ON DELETE RESTRICT,
    version INTEGER NOT NULL CHECK (version > 0),
    estado TEXT NOT NULL DEFAULT 'BORRADOR' CHECK (estado IN ('BORRADOR', 'APROBADA', 'RETIRADA')),
    aprobada_por INTEGER REFERENCES usuarios(id) ON DELETE RESTRICT,
    aprobada_en TEXT,
    creada_en TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    UNIQUE (periodo_id, version)
);

CREATE TABLE IF NOT EXISTS pesos_evaluacion (
    version_id INTEGER NOT NULL REFERENCES versiones_ponderacion(id) ON DELETE RESTRICT,
    evaluacion_id INTEGER NOT NULL REFERENCES evaluaciones(id) ON DELETE RESTRICT,
    peso REAL NOT NULL CHECK (peso BETWEEN 0 AND 1),
    PRIMARY KEY (version_id, evaluacion_id)
);

CREATE TABLE IF NOT EXISTS intentos (
    id INTEGER PRIMARY KEY,
    asignacion_id INTEGER NOT NULL REFERENCES asignaciones_evaluacion(id) ON DELETE RESTRICT,
    numero INTEGER NOT NULL CHECK (numero > 0),
    estado TEXT NOT NULL DEFAULT 'EN_PROGRESO' CHECK (estado IN ('EN_PROGRESO', 'COMPLETADO', 'ANULADO')),
    iniciado_en TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    enviado_en TEXT,
    puntuacion_bruta REAL,
    nota_0_100 REAL CHECK (nota_0_100 IS NULL OR nota_0_100 BETWEEN 0 AND 100),
    UNIQUE (asignacion_id, numero)
);

CREATE TABLE IF NOT EXISTS respuestas (
    id INTEGER PRIMARY KEY,
    intento_id INTEGER NOT NULL REFERENCES intentos(id) ON DELETE RESTRICT,
    referencia_item TEXT NOT NULL,
    respuesta_json TEXT NOT NULL,
    creado_en TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    UNIQUE (intento_id, referencia_item)
);

CREATE TABLE IF NOT EXISTS calificaciones (
    id INTEGER PRIMARY KEY,
    asignacion_id INTEGER NOT NULL REFERENCES asignaciones_evaluacion(id) ON DELETE RESTRICT,
    registrada_por INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    nota_0_100 REAL NOT NULL CHECK (nota_0_100 BETWEEN 0 AND 100),
    observacion TEXT,
    corregida_de_id INTEGER REFERENCES calificaciones(id) ON DELETE RESTRICT,
    registrada_en TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS capacitaciones (
    id INTEGER PRIMARY KEY,
    voluntario_id INTEGER NOT NULL REFERENCES voluntarios(usuario_id) ON DELETE RESTRICT,
    nombre TEXT NOT NULL,
    entidad TEXT,
    fecha TEXT,
    observacion TEXT,
    creado_en TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS asistencias (
    id INTEGER PRIMARY KEY,
    voluntario_id INTEGER NOT NULL REFERENCES voluntarios(usuario_id) ON DELETE RESTRICT,
    fecha TEXT NOT NULL,
    estado TEXT NOT NULL CHECK (estado IN ('PRESENTE', 'AUSENTE', 'JUSTIFICADO')),
    estado_detalle TEXT CHECK (estado_detalle IS NULL OR estado_detalle IN ('ASISTE', 'ATRASO', 'PERMISO', 'FALTA')),
    actividad TEXT,
    registrado_por INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    creado_en TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    UNIQUE (voluntario_id, fecha, actividad)
);

CREATE TABLE IF NOT EXISTS auditoria (
    id INTEGER PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    accion TEXT NOT NULL,
    resultado TEXT NOT NULL CHECK (resultado IN ('EXITOSO', 'FALLIDO')),
    direccion_ip TEXT,
    fecha TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

-- Fase 4B: conjunto de especialidades secundarias, independiente de la principal.
CREATE TABLE IF NOT EXISTS especialidades_secundarias (
    voluntario_id INTEGER NOT NULL REFERENCES voluntarios(usuario_id) ON DELETE RESTRICT,
    especialidad TEXT NOT NULL CHECK (especialidad IN ('Rescate en agua','Rescate en montaña','Rescate en selva','Lucha contra incendios','Primeros Auxilios','K-9')),
    PRIMARY KEY (voluntario_id, especialidad)
);

CREATE TABLE IF NOT EXISTS cursos (
 id INTEGER PRIMARY KEY, nombre TEXT NOT NULL COLLATE NOCASE UNIQUE CHECK(length(nombre) BETWEEN 1 AND 160),
 tipo TEXT CHECK(tipo IS NULL OR tipo IN ('Capacitación','Especialización','Actualización','Taller','Seminario (Webinar)')),
 entidad TEXT, fecha_inicio TEXT, fecha_fin TEXT,
 estado TEXT CHECK(estado IS NULL OR estado IN ('Próximo','En curso','Finalizado')),
 observaciones TEXT,
 puntaje INTEGER CHECK(puntaje IS NULL OR (typeof(puntaje)='integer' AND puntaje BETWEEN 0 AND 100))
);
CREATE TABLE IF NOT EXISTS operaciones (
 id INTEGER PRIMARY KEY, tipo_evento TEXT NOT NULL, lugar TEXT NOT NULL,
 fecha_inicio TEXT NOT NULL, fecha_fin TEXT, institucion_responsable TEXT NOT NULL,
 tipo_operativo TEXT CHECK(tipo_operativo IS NULL OR tipo_operativo IN ('Preventivo','Reactivo','Especial','Emergencia')),
 estado_operacion TEXT CHECK(estado_operacion IS NULL OR estado_operacion IN ('Planificación','En ejecución','Finalizado','Suspendido')),
 revision INTEGER NOT NULL DEFAULT 1 CHECK(revision>0),
 departamento TEXT CHECK(departamento IS NULL OR departamento IN ('Beni','Chuquisaca','Cochabamba','La Paz','Oruro','Pando','Potosí','Santa Cruz','Tarija')),
 zona TEXT CHECK(zona IS NULL OR length(trim(zona)) BETWEEN 1 AND 160)
);
CREATE TABLE IF NOT EXISTS participaciones_operacion (
 operacion_id INTEGER NOT NULL REFERENCES operaciones(id) ON DELETE RESTRICT,
 voluntario_id INTEGER NOT NULL REFERENCES voluntarios(usuario_id) ON DELETE RESTRICT,
 revision INTEGER NOT NULL DEFAULT 1 CHECK(revision>0),
 PRIMARY KEY(operacion_id, voluntario_id)
);

CREATE TABLE IF NOT EXISTS perfil_geografico (
 voluntario_id INTEGER PRIMARY KEY REFERENCES voluntarios(usuario_id) ON DELETE RESTRICT,
 pais_residencia TEXT, departamento_residencia TEXT, nacionalidad TEXT
);

CREATE TABLE IF NOT EXISTS historial_asistencias (
 id INTEGER PRIMARY KEY,
 asistencia_id INTEGER NOT NULL REFERENCES asistencias(id) ON DELETE RESTRICT,
 estado_anterior TEXT NOT NULL, estado_nuevo TEXT NOT NULL,
 corregido_por INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 corregido_en TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);


CREATE TABLE IF NOT EXISTS notas_operativas (
    id INTEGER PRIMARY KEY,
    voluntario_id INTEGER NOT NULL REFERENCES voluntarios(usuario_id) ON DELETE RESTRICT,
    periodo_id INTEGER NOT NULL REFERENCES periodos(id) ON DELETE RESTRICT,
    configuracion_id INTEGER REFERENCES configuraciones_5b(id) ON DELETE RESTRICT,
    evaluacion_id INTEGER REFERENCES evaluaciones(id) ON DELETE RESTRICT,
    fuente TEXT NOT NULL CHECK(fuente IN ('FISICA_1','FISICA_2','ACADEMICA','DESEMPENO_JEFE','DESEMPENO_COMANDANTE')),
    puntos_centesimas INTEGER NOT NULL CHECK(typeof(puntos_centesimas)='integer' AND puntos_centesimas BETWEEN 0 AND 10000),
    evaluador_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    registrada_por INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    evaluador_nombre TEXT NOT NULL,
    registrada_por_nombre TEXT NOT NULL,
    motivo TEXT,
    observacion TEXT,
    corregida_de_id INTEGER UNIQUE REFERENCES notas_operativas(id) ON DELETE RESTRICT,
    registrada_en TEXT NOT NULL DEFAULT(strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_nota_operativa_inicial
ON notas_operativas(voluntario_id,periodo_id,fuente) WHERE corregida_de_id IS NULL;
CREATE TABLE IF NOT EXISTS respaldo_academico (
    nota_id INTEGER NOT NULL REFERENCES notas_operativas(id) ON DELETE RESTRICT,
    capacitacion_id INTEGER NOT NULL REFERENCES capacitaciones(id) ON DELETE RESTRICT,
    nombre TEXT NOT NULL,
    entidad TEXT,
    fecha TEXT,
    PRIMARY KEY(nota_id,capacitacion_id)
);

CREATE TABLE IF NOT EXISTS configuraciones_5b (
    id INTEGER PRIMARY KEY,
    periodo_id INTEGER NOT NULL UNIQUE REFERENCES periodos(id) ON DELETE RESTRICT,
    version INTEGER NOT NULL DEFAULT 1 CHECK(version=1),
    revision INTEGER NOT NULL DEFAULT 1 CHECK(revision>0),
    estado TEXT NOT NULL DEFAULT 'BORRADOR' CHECK(estado IN ('BORRADOR','PUBLICADA')),
    regla TEXT NOT NULL DEFAULT 'PROMEDIO_TRES_V1' CHECK(regla='PROMEDIO_TRES_V1'),
    creada_por INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    publicada_por INTEGER REFERENCES usuarios(id) ON DELETE RESTRICT,
    publicada_en TEXT
);
CREATE TABLE IF NOT EXISTS fuentes_configuracion_5b (
    configuracion_id INTEGER NOT NULL REFERENCES configuraciones_5b(id) ON DELETE RESTRICT,
    fuente TEXT NOT NULL CHECK(fuente IN ('FISICA_1','FISICA_2','ACADEMICA','DESEMPENO_JEFE','DESEMPENO_COMANDANTE')),
    evaluacion_id INTEGER NOT NULL REFERENCES evaluaciones(id) ON DELETE RESTRICT,
    nombre TEXT NOT NULL,
    codigo TEXT NOT NULL,
    categoria TEXT NOT NULL,
    PRIMARY KEY(configuracion_id,fuente)
);

CREATE TABLE IF NOT EXISTS habilitaciones_operativas (
    id INTEGER PRIMARY KEY,
    voluntario_id INTEGER NOT NULL REFERENCES voluntarios(usuario_id) ON DELETE RESTRICT,
    periodo_id INTEGER NOT NULL REFERENCES periodos(id) ON DELETE RESTRICT,
    clave TEXT NOT NULL,
    habilitada INTEGER NOT NULL CHECK(habilitada IN (0,1)),
    registrada_por INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    registrada_en TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS habilitacion_persona_periodo ON habilitaciones_operativas(voluntario_id,periodo_id,clave,id);

CREATE TABLE IF NOT EXISTS participaciones_curso (
 id INTEGER PRIMARY KEY,
 curso_id INTEGER NOT NULL REFERENCES cursos(id) ON DELETE RESTRICT,
 voluntario_id INTEGER NOT NULL REFERENCES voluntarios(usuario_id) ON DELETE RESTRICT,
 nombre_curso TEXT NOT NULL, entidad_curso TEXT NOT NULL, tipo_curso TEXT NOT NULL,
 inicio_curso TEXT NOT NULL, fin_curso TEXT NOT NULL,
 puntaje_base INTEGER NOT NULL CHECK(typeof(puntaje_base)='integer' AND puntaje_base BETWEEN 0 AND 100),
 estado TEXT NOT NULL DEFAULT 'Asignado' CHECK(estado IN ('Asignado','En curso','Finalizado','No completado')),
 puntaje INTEGER CHECK(puntaje IS NULL OR (typeof(puntaje)='integer' AND puntaje BETWEEN 0 AND 100)),
 fecha_finalizacion TEXT,
 revision INTEGER NOT NULL DEFAULT 1 CHECK(revision>0),
 creado_por INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 creado_en TEXT NOT NULL,
 CHECK((estado='Finalizado' AND puntaje IS NOT NULL AND fecha_finalizacion IS NOT NULL)
       OR (estado!='Finalizado' AND puntaje IS NULL AND fecha_finalizacion IS NULL)),
 UNIQUE(curso_id,voluntario_id)
);
CREATE TABLE IF NOT EXISTS historial_participaciones_curso (
 id INTEGER PRIMARY KEY,
 participacion_id INTEGER NOT NULL REFERENCES participaciones_curso(id) ON DELETE RESTRICT,
 revision INTEGER NOT NULL,
 estado TEXT NOT NULL CHECK(estado IN ('Asignado','En curso','Finalizado','No completado')),
 puntaje INTEGER, fecha_finalizacion TEXT,
 motivo TEXT,
 registrada_por INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 responsable_nombre TEXT NOT NULL,
 registrada_en TEXT NOT NULL,
 UNIQUE(participacion_id,revision)
);

CREATE TABLE IF NOT EXISTS programaciones_fisicas (
 id INTEGER PRIMARY KEY,
 periodo_id INTEGER NOT NULL REFERENCES periodos(id) ON DELETE RESTRICT,
 fuente TEXT NOT NULL CHECK(fuente IN ('FISICA_1','FISICA_2')),
 fecha TEXT NOT NULL, motivo TEXT NOT NULL,
 anterior_id INTEGER UNIQUE REFERENCES programaciones_fisicas(id) ON DELETE RESTRICT,
 actor_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 actor_nombre TEXT NOT NULL, modificada_en TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS fisica_comun_inicial ON programaciones_fisicas(periodo_id,fuente) WHERE anterior_id IS NULL;
CREATE TABLE IF NOT EXISTS reprogramaciones_fisicas (
 id INTEGER PRIMARY KEY,
 periodo_id INTEGER NOT NULL REFERENCES periodos(id) ON DELETE RESTRICT,
 fuente TEXT NOT NULL CHECK(fuente IN ('FISICA_1','FISICA_2')),
 voluntario_id INTEGER NOT NULL REFERENCES voluntarios(usuario_id) ON DELETE RESTRICT,
 programacion_id INTEGER NOT NULL REFERENCES programaciones_fisicas(id) ON DELETE RESTRICT,
 fecha TEXT NOT NULL, fecha_anterior TEXT NOT NULL, motivo TEXT NOT NULL,
 anterior_id INTEGER UNIQUE REFERENCES reprogramaciones_fisicas(id) ON DELETE RESTRICT,
 actor_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 actor_nombre TEXT NOT NULL, modificada_en TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS fisica_individual_inicial ON reprogramaciones_fisicas(voluntario_id,periodo_id,fuente) WHERE anterior_id IS NULL;
CREATE TABLE IF NOT EXISTS resultados_fisicos (
 nota_id INTEGER PRIMARY KEY REFERENCES notas_operativas(id) ON DELETE RESTRICT,
 programacion_id INTEGER NOT NULL REFERENCES programaciones_fisicas(id) ON DELETE RESTRICT,
 reprogramacion_id INTEGER REFERENCES reprogramaciones_fisicas(id) ON DELETE RESTRICT,
 estado TEXT NOT NULL CHECK(estado IN ('CUMPLIDA','NO_CUMPLIDA')),
 fecha_realizacion TEXT,
 CHECK((estado='NO_CUMPLIDA' AND fecha_realizacion IS NULL) OR (estado='CUMPLIDA' AND fecha_realizacion IS NOT NULL))
);
CREATE TRIGGER IF NOT EXISTS resultado_fisico_cero BEFORE INSERT ON resultados_fisicos
WHEN NOT EXISTS(SELECT 1 FROM notas_operativas n JOIN programaciones_fisicas p ON p.id=NEW.programacion_id
 WHERE n.id=NEW.nota_id AND n.fuente=p.fuente AND n.periodo_id=p.periodo_id
 AND (NEW.estado!='NO_CUMPLIDA' OR n.puntos_centesimas=0))
BEGIN SELECT RAISE(ABORT,'resultado_fisico_invalido'); END;

CREATE TRIGGER IF NOT EXISTS programaciones_fisicas_update BEFORE UPDATE ON programaciones_fisicas BEGIN SELECT RAISE(ABORT,'historial_fisico_inmutable'); END;

CREATE TRIGGER IF NOT EXISTS programaciones_fisicas_delete BEFORE DELETE ON programaciones_fisicas BEGIN SELECT RAISE(ABORT,'historial_fisico_inmutable'); END;

CREATE TRIGGER IF NOT EXISTS reprogramaciones_fisicas_update BEFORE UPDATE ON reprogramaciones_fisicas BEGIN SELECT RAISE(ABORT,'historial_fisico_inmutable'); END;

CREATE TRIGGER IF NOT EXISTS reprogramaciones_fisicas_delete BEFORE DELETE ON reprogramaciones_fisicas BEGIN SELECT RAISE(ABORT,'historial_fisico_inmutable'); END;

CREATE TRIGGER IF NOT EXISTS resultados_fisicos_update BEFORE UPDATE ON resultados_fisicos BEGIN SELECT RAISE(ABORT,'historial_fisico_inmutable'); END;

CREATE TRIGGER IF NOT EXISTS resultados_fisicos_delete BEFORE DELETE ON resultados_fisicos BEGIN SELECT RAISE(ABORT,'historial_fisico_inmutable'); END;

CREATE INDEX IF NOT EXISTS fisica_comun_vigente ON programaciones_fisicas(periodo_id,fuente,id);
CREATE INDEX IF NOT EXISTS fisica_individual_vigente ON reprogramaciones_fisicas(voluntario_id,periodo_id,fuente,id);


-- 5B.2: estado operativo separado de períodos y configuraciones congeladas.
CREATE TABLE IF NOT EXISTS bajas_gestion (
 periodo_id INTEGER PRIMARY KEY REFERENCES periodos(id) ON DELETE RESTRICT,
 motivo TEXT NOT NULL, actor_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 actor_nombre TEXT NOT NULL, registrada_en TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS historial_gestiones (
 id INTEGER PRIMARY KEY, periodo_id INTEGER NOT NULL REFERENCES periodos(id) ON DELETE RESTRICT,
 nombre_anterior TEXT NOT NULL, nombre_nuevo TEXT NOT NULL,
 ano_anterior INTEGER NOT NULL, ano_nuevo INTEGER NOT NULL,
 actor_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 actor_nombre TEXT NOT NULL, registrada_en TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS activaciones_gestion (
 id INTEGER PRIMARY KEY, periodo_id INTEGER NOT NULL REFERENCES periodos(id) ON DELETE RESTRICT,
 clave TEXT NOT NULL CHECK(clave IN ('FISICA_1','FISICA_2','ACADEMICA','DESEMPENO_JEFE','DESEMPENO_COMANDANTE','PSICOMETRICAS')),
 activa INTEGER NOT NULL CHECK(activa IN (0,1)), motivo TEXT NOT NULL,
 anterior_id INTEGER UNIQUE REFERENCES activaciones_gestion(id) ON DELETE RESTRICT,
 actor_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 actor_nombre TEXT NOT NULL, registrada_en TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS activacion_inicial ON activaciones_gestion(periodo_id,clave) WHERE anterior_id IS NULL;
CREATE INDEX IF NOT EXISTS activacion_gestion_vigente ON activaciones_gestion(periodo_id,clave,id);
CREATE TABLE IF NOT EXISTS reglas_calculo_5b (
 periodo_id INTEGER PRIMARY KEY REFERENCES periodos(id) ON DELETE RESTRICT,
 ano INTEGER NOT NULL UNIQUE CHECK(ano BETWEEN 1 AND 9999),
 configuracion_id INTEGER NOT NULL REFERENCES configuraciones_5b(id) ON DELETE RESTRICT,
 regla TEXT NOT NULL CHECK(regla='ACUMULADO_TRES_V2'),
 activada_por INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 responsable_nombre TEXT NOT NULL, activada_en TEXT NOT NULL
);

CREATE TRIGGER IF NOT EXISTS bajas_gestion_update BEFORE UPDATE ON bajas_gestion BEGIN SELECT RAISE(ABORT,'historial_gestion_inmutable'); END;

CREATE TRIGGER IF NOT EXISTS bajas_gestion_delete BEFORE DELETE ON bajas_gestion BEGIN SELECT RAISE(ABORT,'historial_gestion_inmutable'); END;

CREATE TRIGGER IF NOT EXISTS historial_gestiones_update BEFORE UPDATE ON historial_gestiones BEGIN SELECT RAISE(ABORT,'historial_gestion_inmutable'); END;

CREATE TRIGGER IF NOT EXISTS historial_gestiones_delete BEFORE DELETE ON historial_gestiones BEGIN SELECT RAISE(ABORT,'historial_gestion_inmutable'); END;

CREATE TRIGGER IF NOT EXISTS activaciones_gestion_update BEFORE UPDATE ON activaciones_gestion BEGIN SELECT RAISE(ABORT,'historial_gestion_inmutable'); END;

CREATE TRIGGER IF NOT EXISTS activaciones_gestion_delete BEFORE DELETE ON activaciones_gestion BEGIN SELECT RAISE(ABORT,'historial_gestion_inmutable'); END;

CREATE TRIGGER IF NOT EXISTS reglas_calculo_5b_update BEFORE UPDATE ON reglas_calculo_5b BEGIN SELECT RAISE(ABORT,'historial_gestion_inmutable'); END;

CREATE TRIGGER IF NOT EXISTS reglas_calculo_5b_delete BEFORE DELETE ON reglas_calculo_5b BEGIN SELECT RAISE(ABORT,'historial_gestion_inmutable'); END;


CREATE TABLE IF NOT EXISTS publicaciones_5b (
 id INTEGER PRIMARY KEY,
 voluntario_id INTEGER NOT NULL REFERENCES voluntarios(usuario_id) ON DELETE RESTRICT,
 periodo_id INTEGER NOT NULL REFERENCES reglas_calculo_5b(periodo_id) ON DELETE RESTRICT,
 revision INTEGER NOT NULL CHECK(revision>0),
 anterior_id INTEGER UNIQUE REFERENCES publicaciones_5b(id) ON DELETE RESTRICT,
 contenido_json TEXT NOT NULL, fuentes_json TEXT NOT NULL, motivo TEXT NOT NULL,
 publicada_por INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 responsable_nombre TEXT NOT NULL, publicada_en TEXT NOT NULL,
 UNIQUE(voluntario_id,periodo_id,revision)
);
CREATE UNIQUE INDEX IF NOT EXISTS publicacion_inicial ON publicaciones_5b(voluntario_id,periodo_id) WHERE anterior_id IS NULL;
CREATE TRIGGER IF NOT EXISTS publicacion_inmutable_actualizar BEFORE UPDATE ON publicaciones_5b
BEGIN SELECT RAISE(ABORT,'publicacion_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS publicacion_inmutable_borrar BEFORE DELETE ON publicaciones_5b
BEGIN SELECT RAISE(ABORT,'publicacion_inmutable'); END;

-- 5B.4: cada cierre y reapertura conserva su autoría e instantáneas.
CREATE TABLE IF NOT EXISTS cierres_5b (
 id INTEGER PRIMARY KEY, periodo_id INTEGER NOT NULL REFERENCES periodos(id) ON DELETE RESTRICT,
 numero INTEGER NOT NULL CHECK(numero>0), anterior_id INTEGER UNIQUE REFERENCES cierres_5b(id) ON DELETE RESTRICT,
 contexto_json TEXT NOT NULL, firma_fuentes TEXT NOT NULL, motivo TEXT NOT NULL,
 actor_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT, actor_nombre TEXT NOT NULL,
 registrada_en TEXT NOT NULL, total_personas INTEGER NOT NULL CHECK(total_personas>=0),
 incompletos INTEGER NOT NULL CHECK(incompletos>=0 AND incompletos<=total_personas), UNIQUE(periodo_id,numero)
);
CREATE UNIQUE INDEX IF NOT EXISTS cierre_inicial_5b ON cierres_5b(periodo_id) WHERE anterior_id IS NULL;
CREATE TABLE IF NOT EXISTS instantaneas_cierre_5b (
 cierre_id INTEGER NOT NULL REFERENCES cierres_5b(id) ON DELETE RESTRICT,
 voluntario_id INTEGER NOT NULL REFERENCES voluntarios(usuario_id) ON DELETE RESTRICT,
 contenido_json TEXT NOT NULL, PRIMARY KEY(cierre_id,voluntario_id)
);
CREATE TABLE IF NOT EXISTS reaperturas_5b (
 id INTEGER PRIMARY KEY, cierre_id INTEGER NOT NULL UNIQUE REFERENCES cierres_5b(id) ON DELETE RESTRICT,
 motivo TEXT NOT NULL, actor_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 actor_nombre TEXT NOT NULL, registrada_en TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS cierre_5b_update BEFORE UPDATE ON cierres_5b BEGIN SELECT RAISE(ABORT,'cierre_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS cierre_5b_delete BEFORE DELETE ON cierres_5b BEGIN SELECT RAISE(ABORT,'cierre_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS instantanea_5b_update BEFORE UPDATE ON instantaneas_cierre_5b BEGIN SELECT RAISE(ABORT,'cierre_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS instantanea_5b_delete BEFORE DELETE ON instantaneas_cierre_5b BEGIN SELECT RAISE(ABORT,'cierre_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS reapertura_5b_update BEFORE UPDATE ON reaperturas_5b BEGIN SELECT RAISE(ABORT,'cierre_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS reapertura_5b_delete BEFORE DELETE ON reaperturas_5b BEGIN SELECT RAISE(ABORT,'cierre_inmutable'); END;

-- Evidencia tomada al reabrir: nunca se atribuye al cierre antiguo sin instantánea.
CREATE TABLE IF NOT EXISTS reaperturas_historicas_5b (
 id INTEGER PRIMARY KEY, periodo_id INTEGER NOT NULL UNIQUE REFERENCES periodos(id) ON DELETE RESTRICT,
 contenido_json TEXT NOT NULL, firma_fuentes TEXT NOT NULL, motivo TEXT NOT NULL,
 actor_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 actor_nombre TEXT NOT NULL, registrada_en TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS reapertura_historica_update BEFORE UPDATE ON reaperturas_historicas_5b
BEGIN SELECT RAISE(ABORT,'evidencia_historica_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS reapertura_historica_delete BEFORE DELETE ON reaperturas_historicas_5b
BEGIN SELECT RAISE(ABORT,'evidencia_historica_inmutable'); END;

-- Modelo anual de cinco entradas v3: no adopta ni modifica las reglas v1/v2.
CREATE TABLE IF NOT EXISTS modelos_anuales (
 periodo_id INTEGER PRIMARY KEY REFERENCES periodos(id) ON DELETE RESTRICT,
 formato TEXT NOT NULL DEFAULT 'CINCO_ENTRADAS_V3' CHECK(formato='CINCO_ENTRADAS_V3'),
 revision INTEGER NOT NULL DEFAULT 1 CHECK(revision>0),
 creada_por INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 creada_en TEXT NOT NULL, iniciada_por INTEGER REFERENCES usuarios(id) ON DELETE RESTRICT, iniciada_en TEXT
);
CREATE TABLE IF NOT EXISTS personas_modelo_anual (
 periodo_id INTEGER NOT NULL REFERENCES modelos_anuales(periodo_id) ON DELETE RESTRICT,
 voluntario_id INTEGER NOT NULL REFERENCES voluntarios(usuario_id) ON DELETE RESTRICT,
 registrada_por INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT, registrada_en TEXT NOT NULL,
 PRIMARY KEY(periodo_id,voluntario_id)
);
CREATE TABLE IF NOT EXISTS notas_modelo_anual (
 id INTEGER PRIMARY KEY, periodo_id INTEGER NOT NULL, voluntario_id INTEGER NOT NULL,
 fuente TEXT NOT NULL CHECK(fuente IN ('FISICA_1','FISICA_2','DESEMPENO_JEFE','DESEMPENO_COMANDANTE','ACADEMICA')),
 puntos_centesimas INTEGER NOT NULL CHECK(typeof(puntos_centesimas)='integer' AND puntos_centesimas BETWEEN 0 AND 10000),
 origen TEXT NOT NULL CHECK(origen IN ('CERO_INICIAL','CUMPLIDA','NO_CUMPLIDA','MANUAL')),
 anterior_id INTEGER UNIQUE REFERENCES notas_modelo_anual(id) ON DELETE RESTRICT,
 evidencia_json TEXT NOT NULL, motivo TEXT NOT NULL,
 actor_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT, actor_nombre TEXT NOT NULL, registrada_en TEXT NOT NULL,
 FOREIGN KEY(periodo_id,voluntario_id) REFERENCES personas_modelo_anual(periodo_id,voluntario_id) ON DELETE RESTRICT,
 CHECK(origen!='CERO_INICIAL' OR (puntos_centesimas=0 AND anterior_id IS NULL)),
 CHECK(origen!='NO_CUMPLIDA' OR puntos_centesimas=0)
);
CREATE UNIQUE INDEX IF NOT EXISTS nota_anual_inicial ON notas_modelo_anual(periodo_id,voluntario_id,fuente) WHERE anterior_id IS NULL;
CREATE TABLE IF NOT EXISTS notas_operacion_anual (
 id INTEGER PRIMARY KEY, periodo_id INTEGER NOT NULL, voluntario_id INTEGER NOT NULL,
 operacion_id INTEGER NOT NULL,
 puntos_centesimas INTEGER NOT NULL CHECK(typeof(puntos_centesimas)='integer' AND puntos_centesimas BETWEEN 0 AND 10000),
 anterior_id INTEGER UNIQUE REFERENCES notas_operacion_anual(id) ON DELETE RESTRICT,
 evidencia_json TEXT NOT NULL, motivo TEXT NOT NULL,
 actor_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT, actor_nombre TEXT NOT NULL, registrada_en TEXT NOT NULL,
 FOREIGN KEY(periodo_id,voluntario_id) REFERENCES personas_modelo_anual(periodo_id,voluntario_id) ON DELETE RESTRICT,
 FOREIGN KEY(operacion_id,voluntario_id) REFERENCES participaciones_operacion(operacion_id,voluntario_id) ON DELETE RESTRICT
);
CREATE UNIQUE INDEX IF NOT EXISTS operacion_anual_inicial ON notas_operacion_anual(periodo_id,voluntario_id,operacion_id) WHERE anterior_id IS NULL;
CREATE TRIGGER IF NOT EXISTS persona_modelo_update BEFORE UPDATE ON personas_modelo_anual BEGIN SELECT RAISE(ABORT,'historial_anual_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS persona_modelo_delete BEFORE DELETE ON personas_modelo_anual BEGIN SELECT RAISE(ABORT,'historial_anual_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS nota_modelo_update BEFORE UPDATE ON notas_modelo_anual BEGIN SELECT RAISE(ABORT,'historial_anual_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS nota_modelo_delete BEFORE DELETE ON notas_modelo_anual BEGIN SELECT RAISE(ABORT,'historial_anual_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS nota_operacion_update BEFORE UPDATE ON notas_operacion_anual BEGIN SELECT RAISE(ABORT,'historial_anual_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS nota_operacion_delete BEFORE DELETE ON notas_operacion_anual BEGIN SELECT RAISE(ABORT,'historial_anual_inmutable'); END;

CREATE TRIGGER IF NOT EXISTS periodo_modelo_fechas BEFORE UPDATE OF fecha_inicio,fecha_fin,nombre ON periodos
WHEN EXISTS(SELECT 1 FROM modelos_anuales m WHERE m.periodo_id=OLD.id AND m.iniciada_en IS NOT NULL)
AND (NEW.fecha_inicio!=OLD.fecha_inicio OR NEW.fecha_fin!=OLD.fecha_fin OR NEW.nombre!=OLD.nombre)
BEGIN SELECT RAISE(ABORT,'periodo_modelo_iniciado_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS modelo_iniciado_update BEFORE UPDATE ON modelos_anuales
WHEN OLD.iniciada_en IS NOT NULL BEGIN SELECT RAISE(ABORT,'modelo_iniciado_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS modelo_anual_delete BEFORE DELETE ON modelos_anuales BEGIN SELECT RAISE(ABORT,'modelo_anual_inmutable'); END;

CREATE TABLE IF NOT EXISTS eventos_modelo_anual (
 id INTEGER PRIMARY KEY, periodo_id INTEGER NOT NULL REFERENCES modelos_anuales(periodo_id) ON DELETE RESTRICT,
 accion TEXT NOT NULL, anterior_json TEXT NOT NULL, nuevo_json TEXT NOT NULL, motivo TEXT NOT NULL,
 actor_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT, actor_nombre TEXT NOT NULL, registrada_en TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS evento_modelo_update BEFORE UPDATE ON eventos_modelo_anual BEGIN SELECT RAISE(ABORT,'historial_anual_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS evento_modelo_delete BEFORE DELETE ON eventos_modelo_anual BEGIN SELECT RAISE(ABORT,'historial_anual_inmutable'); END;

-- v25: bajas con historial y ejercicios didácticos sin valor psicométrico.
CREATE TABLE IF NOT EXISTS bajas_curso (
 curso_id INTEGER PRIMARY KEY REFERENCES cursos(id) ON DELETE RESTRICT,
 motivo TEXT NOT NULL, actor_id INTEGER NOT NULL REFERENCES usuarios(id),
 actor_nombre TEXT NOT NULL, registrada_en TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS retiros_curso (
 participacion_id INTEGER PRIMARY KEY REFERENCES participaciones_curso(id) ON DELETE RESTRICT,
 motivo TEXT NOT NULL, actor_id INTEGER NOT NULL REFERENCES usuarios(id),
 actor_nombre TEXT NOT NULL, registrada_en TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS activaciones_demo (
 periodo_id INTEGER NOT NULL REFERENCES modelos_anuales(periodo_id) ON DELETE RESTRICT,
 clave TEXT NOT NULL CHECK(clave IN ('PSICOMETRICA_1','PSICOMETRICA_2')),
 activa INTEGER NOT NULL CHECK(activa IN (0,1)), actor_id INTEGER NOT NULL REFERENCES usuarios(id),
 modificada_en TEXT NOT NULL, PRIMARY KEY(periodo_id,clave)
);
CREATE TABLE IF NOT EXISTS intentos_demo (
 id INTEGER PRIMARY KEY, periodo_id INTEGER NOT NULL, voluntario_id INTEGER NOT NULL,
 clave TEXT NOT NULL CHECK(clave IN ('PSICOMETRICA_1','PSICOMETRICA_2')),
 preguntas_json TEXT NOT NULL, iniciada_en TEXT NOT NULL,
 puntaje INTEGER CHECK(puntaje IN (0,50,100)), finalizada_en TEXT,
 UNIQUE(periodo_id,voluntario_id,clave),
 FOREIGN KEY(periodo_id,voluntario_id) REFERENCES personas_modelo_anual(periodo_id,voluntario_id) ON DELETE RESTRICT,
 CHECK((puntaje IS NULL AND finalizada_en IS NULL) OR (puntaje IS NOT NULL AND finalizada_en IS NOT NULL))
);
CREATE TRIGGER IF NOT EXISTS baja_curso_update BEFORE UPDATE ON bajas_curso BEGIN SELECT RAISE(ABORT,'baja_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS baja_curso_delete BEFORE DELETE ON bajas_curso BEGIN SELECT RAISE(ABORT,'baja_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS retiro_curso_update BEFORE UPDATE ON retiros_curso BEGIN SELECT RAISE(ABORT,'retiro_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS retiro_curso_delete BEFORE DELETE ON retiros_curso BEGIN SELECT RAISE(ABORT,'retiro_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS intento_demo_update BEFORE UPDATE ON intentos_demo
WHEN OLD.finalizada_en IS NOT NULL OR NEW.periodo_id!=OLD.periodo_id OR NEW.voluntario_id!=OLD.voluntario_id OR NEW.clave!=OLD.clave OR NEW.preguntas_json!=OLD.preguntas_json OR NEW.iniciada_en!=OLD.iniciada_en
BEGIN SELECT RAISE(ABORT,'ejemplo_finalizado_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS intento_demo_delete BEFORE DELETE ON intentos_demo BEGIN SELECT RAISE(ABORT,'ejemplo_inmutable'); END;
-- Solo se admite eliminar metadatos de una gestión que nunca se inició.
DROP TRIGGER IF EXISTS modelo_anual_delete;
CREATE TRIGGER modelo_anual_delete BEFORE DELETE ON modelos_anuales
WHEN OLD.iniciada_en IS NOT NULL OR EXISTS(SELECT 1 FROM personas_modelo_anual WHERE periodo_id=OLD.periodo_id)
BEGIN SELECT RAISE(ABORT,'modelo_anual_inmutable'); END;
DROP TRIGGER IF EXISTS evento_modelo_delete;
CREATE TRIGGER evento_modelo_delete BEFORE DELETE ON eventos_modelo_anual
WHEN EXISTS(SELECT 1 FROM modelos_anuales WHERE periodo_id=OLD.periodo_id AND iniciada_en IS NOT NULL)
BEGIN SELECT RAISE(ABORT,'historial_anual_inmutable'); END;


CREATE TABLE IF NOT EXISTS bajas_operacion (
 operacion_id INTEGER PRIMARY KEY REFERENCES operaciones(id) ON DELETE RESTRICT,
 motivo TEXT NOT NULL CHECK(length(trim(motivo)) BETWEEN 1 AND 2000),
 actor_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 actor_nombre TEXT NOT NULL, registrada_en TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS baja_operacion_update BEFORE UPDATE ON bajas_operacion BEGIN SELECT RAISE(ABORT,'baja_operacion_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS baja_operacion_delete BEFORE DELETE ON bajas_operacion BEGIN SELECT RAISE(ABORT,'baja_operacion_inmutable'); END;

CREATE TABLE IF NOT EXISTS retiros_operacion (
 operacion_id INTEGER NOT NULL, voluntario_id INTEGER NOT NULL,
 motivo TEXT NOT NULL CHECK(length(trim(motivo)) BETWEEN 1 AND 2000),
 actor_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 actor_nombre TEXT NOT NULL, registrada_en TEXT NOT NULL,
 PRIMARY KEY(operacion_id,voluntario_id),
 FOREIGN KEY(operacion_id,voluntario_id) REFERENCES participaciones_operacion(operacion_id,voluntario_id) ON DELETE RESTRICT
);
CREATE TRIGGER IF NOT EXISTS retiro_operacion_update BEFORE UPDATE ON retiros_operacion BEGIN SELECT RAISE(ABORT,'retiro_operacion_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS retiro_operacion_delete BEFORE DELETE ON retiros_operacion BEGIN SELECT RAISE(ABORT,'retiro_operacion_inmutable'); END;

-- Circuito oficial condicionado a versión/revisión externa; sin reactivos semilla.
CREATE TABLE IF NOT EXISTS activaciones_psicometria (
 periodo_id INTEGER NOT NULL REFERENCES periodos(id) ON DELETE RESTRICT,
 clave TEXT NOT NULL CHECK(clave IN ('DASS21','CBI')),
 activa INTEGER NOT NULL CHECK(activa IN (0,1)),
 revision INTEGER NOT NULL CHECK(revision>0),
 actor_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 modificada_en TEXT NOT NULL, PRIMARY KEY(periodo_id,clave)
);
CREATE TABLE IF NOT EXISTS historial_activaciones_psicometria (
 id INTEGER PRIMARY KEY, periodo_id INTEGER NOT NULL REFERENCES periodos(id) ON DELETE RESTRICT,
 clave TEXT NOT NULL CHECK(clave IN ('DASS21','CBI')), activa INTEGER NOT NULL CHECK(activa IN (0,1)),
 revision INTEGER NOT NULL, actor_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 registrada_en TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS intentos_psicometria (
 id INTEGER PRIMARY KEY,
 periodo_id INTEGER NOT NULL REFERENCES periodos(id) ON DELETE RESTRICT,
 voluntario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 clave TEXT NOT NULL CHECK(clave IN ('DASS21','CBI')),
 version TEXT NOT NULL, firma_formulario TEXT NOT NULL, formulario_json TEXT NOT NULL,
 respuestas_json TEXT NOT NULL, resultados_json TEXT,
 revision INTEGER NOT NULL CHECK(revision>0),
 iniciada_en TEXT NOT NULL, guardada_en TEXT NOT NULL, finalizada_en TEXT,
 UNIQUE(periodo_id,voluntario_id,clave),
 CHECK((finalizada_en IS NULL AND resultados_json IS NULL) OR (finalizada_en IS NOT NULL AND resultados_json IS NOT NULL))
);
CREATE TRIGGER IF NOT EXISTS intento_psicometria_update BEFORE UPDATE ON intentos_psicometria
WHEN OLD.finalizada_en IS NOT NULL OR NEW.periodo_id!=OLD.periodo_id OR NEW.voluntario_id!=OLD.voluntario_id
 OR NEW.clave!=OLD.clave OR NEW.version!=OLD.version OR NEW.firma_formulario!=OLD.firma_formulario OR NEW.formulario_json!=OLD.formulario_json OR NEW.iniciada_en!=OLD.iniciada_en
BEGIN SELECT RAISE(ABORT,'psicometria_finalizada_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS intento_psicometria_delete BEFORE DELETE ON intentos_psicometria BEGIN SELECT RAISE(ABORT,'psicometria_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS historial_psicometria_update BEFORE UPDATE ON historial_activaciones_psicometria BEGIN SELECT RAISE(ABORT,'historial_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS historial_psicometria_delete BEFORE DELETE ON historial_activaciones_psicometria BEGIN SELECT RAISE(ABORT,'historial_inmutable'); END;

-- v29: instrumentos actuales y recomendaciones; históricos DASS/CBI intactos.
CREATE TABLE IF NOT EXISTS revisiones_pruebas (
 id INTEGER PRIMARY KEY, periodo_id INTEGER NOT NULL REFERENCES periodos(id) ON DELETE RESTRICT,
 clave TEXT NOT NULL CHECK(clave IN ('GSE','MINIIPIP')), firma_formulario TEXT NOT NULL,
 formulario_json TEXT NOT NULL, observacion TEXT NOT NULL,
 actor_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 actor_nombre TEXT NOT NULL, rol TEXT NOT NULL CHECK(rol IN ('ADMINISTRADOR','JEFE_PERSONAL')),
 registrada_en TEXT NOT NULL, UNIQUE(periodo_id,clave,firma_formulario,rol)
);
CREATE TABLE IF NOT EXISTS activaciones_pruebas (
 periodo_id INTEGER NOT NULL REFERENCES periodos(id) ON DELETE RESTRICT,
 clave TEXT NOT NULL CHECK(clave IN ('GSE','MINIIPIP')), activa INTEGER NOT NULL CHECK(activa IN (0,1)),
 revision INTEGER NOT NULL CHECK(revision>0), actor_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 modificada_en TEXT NOT NULL, PRIMARY KEY(periodo_id,clave)
);
CREATE TABLE IF NOT EXISTS historial_activaciones_pruebas (
 id INTEGER PRIMARY KEY, periodo_id INTEGER NOT NULL REFERENCES periodos(id) ON DELETE RESTRICT,
 clave TEXT NOT NULL CHECK(clave IN ('GSE','MINIIPIP')), activa INTEGER NOT NULL CHECK(activa IN (0,1)),
 revision INTEGER NOT NULL, actor_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 registrada_en TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS intentos_pruebas (
 id INTEGER PRIMARY KEY, periodo_id INTEGER NOT NULL REFERENCES periodos(id) ON DELETE RESTRICT,
 voluntario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 clave TEXT NOT NULL CHECK(clave IN ('GSE','MINIIPIP')), version TEXT NOT NULL,
 firma_formulario TEXT NOT NULL, formulario_json TEXT NOT NULL,
 respuestas_json TEXT NOT NULL, resultados_json TEXT, revision INTEGER NOT NULL CHECK(revision>0),
 iniciada_en TEXT NOT NULL, guardada_en TEXT NOT NULL, finalizada_en TEXT,
 UNIQUE(periodo_id,voluntario_id,clave),
 CHECK((finalizada_en IS NULL AND resultados_json IS NULL) OR (finalizada_en IS NOT NULL AND resultados_json IS NOT NULL))
);
CREATE TABLE IF NOT EXISTS recomendaciones (
 id INTEGER PRIMARY KEY, periodo_id INTEGER NOT NULL REFERENCES periodos(id) ON DELETE RESTRICT,
 voluntario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 anterior_id INTEGER UNIQUE REFERENCES recomendaciones(id) ON DELETE RESTRICT,
 firma_fuentes TEXT NOT NULL, fuentes_json TEXT NOT NULL, entradas_json TEXT NOT NULL,
 modelo_sha256 TEXT NOT NULL, resultado_json TEXT NOT NULL,
 actor_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 actor_nombre TEXT NOT NULL, generada_en TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_recomendaciones_persona ON recomendaciones(periodo_id,voluntario_id,id);
CREATE UNIQUE INDEX IF NOT EXISTS recomendacion_inicial ON recomendaciones(periodo_id,voluntario_id) WHERE anterior_id IS NULL;
CREATE TRIGGER IF NOT EXISTS recomendacion_anterior_insert BEFORE INSERT ON recomendaciones
WHEN NEW.anterior_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM recomendaciones r WHERE r.id=NEW.anterior_id AND r.periodo_id=NEW.periodo_id AND r.voluntario_id=NEW.voluntario_id)
BEGIN SELECT RAISE(ABORT,'recomendacion_anterior_invalida'); END;
CREATE TABLE IF NOT EXISTS confirmaciones_recomendacion (
 recomendacion_id INTEGER PRIMARY KEY REFERENCES recomendaciones(id) ON DELETE RESTRICT,
 observacion TEXT NOT NULL CHECK(length(trim(observacion)) BETWEEN 1 AND 2000),
 actor_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 actor_nombre TEXT NOT NULL, confirmada_en TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS intento_prueba_update BEFORE UPDATE ON intentos_pruebas
WHEN OLD.finalizada_en IS NOT NULL OR NEW.periodo_id!=OLD.periodo_id OR NEW.voluntario_id!=OLD.voluntario_id
 OR NEW.clave!=OLD.clave OR NEW.version!=OLD.version OR NEW.firma_formulario!=OLD.firma_formulario
 OR NEW.formulario_json!=OLD.formulario_json OR NEW.iniciada_en!=OLD.iniciada_en
BEGIN SELECT RAISE(ABORT,'prueba_finalizada_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS intento_prueba_delete BEFORE DELETE ON intentos_pruebas BEGIN SELECT RAISE(ABORT,'prueba_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS revision_prueba_update BEFORE UPDATE ON revisiones_pruebas BEGIN SELECT RAISE(ABORT,'revision_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS revision_prueba_delete BEFORE DELETE ON revisiones_pruebas BEGIN SELECT RAISE(ABORT,'revision_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS historial_prueba_update BEFORE UPDATE ON historial_activaciones_pruebas BEGIN SELECT RAISE(ABORT,'historial_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS historial_prueba_delete BEFORE DELETE ON historial_activaciones_pruebas BEGIN SELECT RAISE(ABORT,'historial_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS recomendacion_update BEFORE UPDATE ON recomendaciones BEGIN SELECT RAISE(ABORT,'recomendacion_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS recomendacion_delete BEFORE DELETE ON recomendaciones BEGIN SELECT RAISE(ABORT,'recomendacion_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS confirmacion_recomendacion_update BEFORE UPDATE ON confirmaciones_recomendacion BEGIN SELECT RAISE(ABORT,'confirmacion_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS confirmacion_recomendacion_delete BEFORE DELETE ON confirmaciones_recomendacion BEGIN SELECT RAISE(ABORT,'confirmacion_inmutable'); END;

-- v30: ciclos adicionales sin alterar ni borrar los intentos originales.
CREATE TABLE IF NOT EXISTS reinicios_pruebas (
 id INTEGER PRIMARY KEY, periodo_id INTEGER NOT NULL REFERENCES periodos(id) ON DELETE RESTRICT,
 voluntario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 clave TEXT NOT NULL CHECK(clave IN ('GSE','MINIIPIP')),
 intento_original_id INTEGER UNIQUE REFERENCES intentos_pruebas(id) ON DELETE RESTRICT,
 reintento_anterior_id INTEGER UNIQUE REFERENCES reintentos_pruebas(id) ON DELETE RESTRICT,
 actor_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 actor_nombre TEXT NOT NULL, reiniciada_en TEXT NOT NULL,
 CHECK((intento_original_id IS NOT NULL AND reintento_anterior_id IS NULL)
    OR (intento_original_id IS NULL AND reintento_anterior_id IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS idx_reinicios_persona ON reinicios_pruebas(periodo_id,voluntario_id,clave,id);
CREATE TABLE IF NOT EXISTS reintentos_pruebas (
 id INTEGER PRIMARY KEY, reinicio_id INTEGER NOT NULL UNIQUE REFERENCES reinicios_pruebas(id) ON DELETE RESTRICT,
 periodo_id INTEGER NOT NULL REFERENCES periodos(id) ON DELETE RESTRICT,
 voluntario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 clave TEXT NOT NULL CHECK(clave IN ('GSE','MINIIPIP')), version TEXT NOT NULL,
 firma_formulario TEXT NOT NULL, formulario_json TEXT NOT NULL,
 respuestas_json TEXT NOT NULL, resultados_json TEXT, revision INTEGER NOT NULL CHECK(revision>0),
 iniciada_en TEXT NOT NULL, guardada_en TEXT NOT NULL, finalizada_en TEXT,
 CHECK((finalizada_en IS NULL AND resultados_json IS NULL) OR (finalizada_en IS NOT NULL AND resultados_json IS NOT NULL))
);
CREATE TRIGGER IF NOT EXISTS reinicio_prueba_insert BEFORE INSERT ON reinicios_pruebas
WHEN NOT ((NEW.intento_original_id IS NOT NULL AND NOT EXISTS(
 SELECT 1 FROM reinicios_pruebas WHERE periodo_id=NEW.periodo_id AND voluntario_id=NEW.voluntario_id AND clave=NEW.clave)
 AND EXISTS(SELECT 1 FROM intentos_pruebas i WHERE i.id=NEW.intento_original_id AND i.periodo_id=NEW.periodo_id AND i.voluntario_id=NEW.voluntario_id AND i.clave=NEW.clave AND i.finalizada_en IS NOT NULL))
 OR (NEW.reintento_anterior_id IS NOT NULL AND EXISTS(
 SELECT 1 FROM reintentos_pruebas i WHERE i.id=NEW.reintento_anterior_id AND i.periodo_id=NEW.periodo_id AND i.voluntario_id=NEW.voluntario_id AND i.clave=NEW.clave AND i.finalizada_en IS NOT NULL
 AND i.reinicio_id=(SELECT max(r.id) FROM reinicios_pruebas r WHERE r.periodo_id=NEW.periodo_id AND r.voluntario_id=NEW.voluntario_id AND r.clave=NEW.clave))))
BEGIN SELECT RAISE(ABORT,'reinicio_anterior_invalido'); END;
CREATE TRIGGER IF NOT EXISTS reintento_prueba_insert BEFORE INSERT ON reintentos_pruebas
WHEN NOT EXISTS(SELECT 1 FROM reinicios_pruebas r WHERE r.id=NEW.reinicio_id AND r.periodo_id=NEW.periodo_id AND r.voluntario_id=NEW.voluntario_id AND r.clave=NEW.clave)
BEGIN SELECT RAISE(ABORT,'reinicio_incompatible'); END;
CREATE TRIGGER IF NOT EXISTS reintento_prueba_update BEFORE UPDATE ON reintentos_pruebas
WHEN OLD.finalizada_en IS NOT NULL OR NEW.reinicio_id!=OLD.reinicio_id OR NEW.periodo_id!=OLD.periodo_id
 OR NEW.voluntario_id!=OLD.voluntario_id OR NEW.clave!=OLD.clave OR NEW.version!=OLD.version
 OR NEW.firma_formulario!=OLD.firma_formulario OR NEW.formulario_json!=OLD.formulario_json OR NEW.iniciada_en!=OLD.iniciada_en
BEGIN SELECT RAISE(ABORT,'prueba_finalizada_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS reintento_prueba_delete BEFORE DELETE ON reintentos_pruebas BEGIN SELECT RAISE(ABORT,'prueba_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS reinicio_prueba_update BEFORE UPDATE ON reinicios_pruebas BEGIN SELECT RAISE(ABORT,'reinicio_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS reinicio_prueba_delete BEFORE DELETE ON reinicios_pruebas BEGIN SELECT RAISE(ABORT,'reinicio_inmutable'); END;


-- v31: almacenamiento NASA-TLX independiente, sin reconstruir históricos.
CREATE TABLE IF NOT EXISTS tlx_revisiones_pruebas (
 id INTEGER PRIMARY KEY, periodo_id INTEGER NOT NULL REFERENCES periodos(id) ON DELETE RESTRICT,
 clave TEXT NOT NULL CHECK(clave IN ('NASATLX')), firma_formulario TEXT NOT NULL,
 formulario_json TEXT NOT NULL, observacion TEXT NOT NULL,
 actor_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 actor_nombre TEXT NOT NULL, rol TEXT NOT NULL CHECK(rol IN ('ADMINISTRADOR','JEFE_PERSONAL')),
 registrada_en TEXT NOT NULL, UNIQUE(periodo_id,clave,firma_formulario,rol)
);
CREATE TABLE IF NOT EXISTS tlx_activaciones_pruebas (
 periodo_id INTEGER NOT NULL REFERENCES periodos(id) ON DELETE RESTRICT,
 clave TEXT NOT NULL CHECK(clave IN ('NASATLX')), activa INTEGER NOT NULL CHECK(activa IN (0,1)),
 revision INTEGER NOT NULL CHECK(revision>0), actor_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 modificada_en TEXT NOT NULL, PRIMARY KEY(periodo_id,clave)
);
CREATE TABLE IF NOT EXISTS tlx_historial_activaciones_pruebas (
 id INTEGER PRIMARY KEY, periodo_id INTEGER NOT NULL REFERENCES periodos(id) ON DELETE RESTRICT,
 clave TEXT NOT NULL CHECK(clave IN ('NASATLX')), activa INTEGER NOT NULL CHECK(activa IN (0,1)),
 revision INTEGER NOT NULL, actor_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 registrada_en TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tlx_intentos_pruebas (
 id INTEGER PRIMARY KEY, periodo_id INTEGER NOT NULL REFERENCES periodos(id) ON DELETE RESTRICT,
 voluntario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 clave TEXT NOT NULL CHECK(clave IN ('NASATLX')), version TEXT NOT NULL,
 firma_formulario TEXT NOT NULL, formulario_json TEXT NOT NULL,
 respuestas_json TEXT NOT NULL, resultados_json TEXT, revision INTEGER NOT NULL CHECK(revision>0),
 simulacro_confirmado INTEGER NOT NULL DEFAULT 0 CHECK(simulacro_confirmado IN (0,1)),
 iniciada_en TEXT NOT NULL, guardada_en TEXT NOT NULL, finalizada_en TEXT,
 UNIQUE(periodo_id,voluntario_id,clave),
 CHECK(finalizada_en IS NULL OR simulacro_confirmado=1),
 CHECK((finalizada_en IS NULL AND resultados_json IS NULL) OR (finalizada_en IS NOT NULL AND resultados_json IS NOT NULL))
);
CREATE TABLE IF NOT EXISTS tlx_reinicios_pruebas (
 id INTEGER PRIMARY KEY, periodo_id INTEGER NOT NULL REFERENCES periodos(id) ON DELETE RESTRICT,
 voluntario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 clave TEXT NOT NULL CHECK(clave IN ('NASATLX')),
 intento_original_id INTEGER UNIQUE REFERENCES tlx_intentos_pruebas(id) ON DELETE RESTRICT,
 reintento_anterior_id INTEGER UNIQUE REFERENCES tlx_reintentos_pruebas(id) ON DELETE RESTRICT,
 actor_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 actor_nombre TEXT NOT NULL, reiniciada_en TEXT NOT NULL,
 CHECK((intento_original_id IS NOT NULL AND reintento_anterior_id IS NULL)
    OR (intento_original_id IS NULL AND reintento_anterior_id IS NOT NULL))
);
CREATE TABLE IF NOT EXISTS tlx_reintentos_pruebas (
 id INTEGER PRIMARY KEY, reinicio_id INTEGER NOT NULL UNIQUE REFERENCES tlx_reinicios_pruebas(id) ON DELETE RESTRICT,
 periodo_id INTEGER NOT NULL REFERENCES periodos(id) ON DELETE RESTRICT,
 voluntario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 clave TEXT NOT NULL CHECK(clave IN ('NASATLX')), version TEXT NOT NULL,
 firma_formulario TEXT NOT NULL, formulario_json TEXT NOT NULL,
 respuestas_json TEXT NOT NULL, resultados_json TEXT, revision INTEGER NOT NULL CHECK(revision>0),
 simulacro_confirmado INTEGER NOT NULL DEFAULT 0 CHECK(simulacro_confirmado IN (0,1)),
 iniciada_en TEXT NOT NULL, guardada_en TEXT NOT NULL, finalizada_en TEXT,
 CHECK(finalizada_en IS NULL OR simulacro_confirmado=1),
 CHECK((finalizada_en IS NULL AND resultados_json IS NULL) OR (finalizada_en IS NOT NULL AND resultados_json IS NOT NULL))
);
CREATE TRIGGER IF NOT EXISTS tlx_intento_prueba_update BEFORE UPDATE ON tlx_intentos_pruebas
WHEN OLD.finalizada_en IS NOT NULL OR NEW.periodo_id!=OLD.periodo_id OR NEW.voluntario_id!=OLD.voluntario_id
 OR NEW.clave!=OLD.clave OR NEW.version!=OLD.version OR NEW.firma_formulario!=OLD.firma_formulario
 OR NEW.formulario_json!=OLD.formulario_json OR NEW.iniciada_en!=OLD.iniciada_en
BEGIN SELECT RAISE(ABORT,'prueba_finalizada_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS tlx_intento_prueba_delete BEFORE DELETE ON tlx_intentos_pruebas BEGIN SELECT RAISE(ABORT,'prueba_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS tlx_revision_prueba_update BEFORE UPDATE ON tlx_revisiones_pruebas BEGIN SELECT RAISE(ABORT,'revision_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS tlx_revision_prueba_delete BEFORE DELETE ON tlx_revisiones_pruebas BEGIN SELECT RAISE(ABORT,'revision_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS tlx_historial_prueba_update BEFORE UPDATE ON tlx_historial_activaciones_pruebas BEGIN SELECT RAISE(ABORT,'historial_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS tlx_historial_prueba_delete BEFORE DELETE ON tlx_historial_activaciones_pruebas BEGIN SELECT RAISE(ABORT,'historial_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS tlx_reinicio_prueba_insert BEFORE INSERT ON tlx_reinicios_pruebas
WHEN NOT ((NEW.intento_original_id IS NOT NULL AND NOT EXISTS(
 SELECT 1 FROM tlx_reinicios_pruebas WHERE periodo_id=NEW.periodo_id AND voluntario_id=NEW.voluntario_id AND clave=NEW.clave)
 AND EXISTS(SELECT 1 FROM tlx_intentos_pruebas i WHERE i.id=NEW.intento_original_id AND i.periodo_id=NEW.periodo_id AND i.voluntario_id=NEW.voluntario_id AND i.clave=NEW.clave AND i.finalizada_en IS NOT NULL))
 OR (NEW.reintento_anterior_id IS NOT NULL AND EXISTS(
 SELECT 1 FROM tlx_reintentos_pruebas i WHERE i.id=NEW.reintento_anterior_id AND i.periodo_id=NEW.periodo_id AND i.voluntario_id=NEW.voluntario_id AND i.clave=NEW.clave AND i.finalizada_en IS NOT NULL
 AND i.reinicio_id=(SELECT max(r.id) FROM tlx_reinicios_pruebas r WHERE r.periodo_id=NEW.periodo_id AND r.voluntario_id=NEW.voluntario_id AND r.clave=NEW.clave))))
BEGIN SELECT RAISE(ABORT,'reinicio_anterior_invalido'); END;
CREATE TRIGGER IF NOT EXISTS tlx_reintento_prueba_insert BEFORE INSERT ON tlx_reintentos_pruebas
WHEN NOT EXISTS(SELECT 1 FROM tlx_reinicios_pruebas r WHERE r.id=NEW.reinicio_id AND r.periodo_id=NEW.periodo_id AND r.voluntario_id=NEW.voluntario_id AND r.clave=NEW.clave)
BEGIN SELECT RAISE(ABORT,'reinicio_incompatible'); END;
CREATE TRIGGER IF NOT EXISTS tlx_reintento_prueba_update BEFORE UPDATE ON tlx_reintentos_pruebas
WHEN OLD.finalizada_en IS NOT NULL OR NEW.reinicio_id!=OLD.reinicio_id OR NEW.periodo_id!=OLD.periodo_id
 OR NEW.voluntario_id!=OLD.voluntario_id OR NEW.clave!=OLD.clave OR NEW.version!=OLD.version
 OR NEW.firma_formulario!=OLD.firma_formulario OR NEW.formulario_json!=OLD.formulario_json OR NEW.iniciada_en!=OLD.iniciada_en
BEGIN SELECT RAISE(ABORT,'prueba_finalizada_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS tlx_reintento_prueba_delete BEFORE DELETE ON tlx_reintentos_pruebas BEGIN SELECT RAISE(ABORT,'prueba_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS tlx_reinicio_prueba_update BEFORE UPDATE ON tlx_reinicios_pruebas BEGIN SELECT RAISE(ABORT,'reinicio_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS tlx_reinicio_prueba_delete BEFORE DELETE ON tlx_reinicios_pruebas BEGIN SELECT RAISE(ABORT,'reinicio_inmutable'); END;
CREATE INDEX IF NOT EXISTS tlx_idx_reinicios_persona ON tlx_reinicios_pruebas(periodo_id,voluntario_id,clave,id);
CREATE TABLE IF NOT EXISTS simulacros_tlx (
 periodo_id INTEGER PRIMARY KEY REFERENCES periodos(id) ON DELETE RESTRICT,
 nombre TEXT NOT NULL CHECK(length(trim(nombre)) BETWEEN 3 AND 200), fecha TEXT NOT NULL,
 revision INTEGER NOT NULL CHECK(revision>0), actor_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 actor_nombre TEXT NOT NULL, registrada_en TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS simulacro_tlx_update BEFORE UPDATE ON simulacros_tlx
WHEN NEW.periodo_id!=OLD.periodo_id OR EXISTS(SELECT 1 FROM tlx_intentos_pruebas WHERE periodo_id=OLD.periodo_id)
BEGIN SELECT RAISE(ABORT,'simulacro_con_intentos_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS simulacro_tlx_delete BEFORE DELETE ON simulacros_tlx BEGIN SELECT RAISE(ABORT,'simulacro_inmutable'); END;

-- v32: publicación propia del modelo anual, independiente de las reglas históricas.
CREATE TABLE IF NOT EXISTS publicaciones_modelo_anual (
 id INTEGER PRIMARY KEY,
 voluntario_id INTEGER NOT NULL REFERENCES voluntarios(usuario_id) ON DELETE RESTRICT,
 periodo_id INTEGER NOT NULL REFERENCES modelos_anuales(periodo_id) ON DELETE RESTRICT,
 revision INTEGER NOT NULL CHECK(revision>0),
 anterior_id INTEGER UNIQUE REFERENCES publicaciones_modelo_anual(id) ON DELETE RESTRICT,
 contenido_json TEXT NOT NULL, fuentes_json TEXT NOT NULL, motivo TEXT NOT NULL,
 publicada_por INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 responsable_nombre TEXT NOT NULL, publicada_en TEXT NOT NULL,
 UNIQUE(voluntario_id,periodo_id,revision)
);
CREATE UNIQUE INDEX IF NOT EXISTS publicacion_anual_inicial ON publicaciones_modelo_anual(voluntario_id,periodo_id) WHERE anterior_id IS NULL;
CREATE TRIGGER IF NOT EXISTS publicacion_anual_inmutable_actualizar BEFORE UPDATE ON publicaciones_modelo_anual
BEGIN SELECT RAISE(ABORT,'publicacion_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS publicacion_anual_inmutable_borrar BEFORE DELETE ON publicaciones_modelo_anual
BEGIN SELECT RAISE(ABORT,'publicacion_inmutable'); END;

-- Reingresos sin modificar los retiros originales ni las notas.
CREATE TABLE IF NOT EXISTS movimientos_participacion_operacion (
 operacion_id INTEGER NOT NULL, voluntario_id INTEGER NOT NULL,
 revision INTEGER NOT NULL CHECK(revision>0),
 tipo TEXT NOT NULL CHECK(tipo IN ('RETIRO','REINGRESO')),
 motivo TEXT NOT NULL CHECK(length(trim(motivo)) BETWEEN 1 AND 2000),
 actor_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
 actor_nombre TEXT NOT NULL, registrada_en TEXT NOT NULL,
 PRIMARY KEY(operacion_id,voluntario_id,revision),
 FOREIGN KEY(operacion_id,voluntario_id) REFERENCES participaciones_operacion(operacion_id,voluntario_id) ON DELETE RESTRICT
);
CREATE TRIGGER IF NOT EXISTS movimiento_operacion_update BEFORE UPDATE ON movimientos_participacion_operacion BEGIN SELECT RAISE(ABORT,'movimiento_operacion_inmutable'); END;
CREATE TRIGGER IF NOT EXISTS movimiento_operacion_delete BEFORE DELETE ON movimientos_participacion_operacion BEGIN SELECT RAISE(ABORT,'movimiento_operacion_inmutable'); END;
CREATE VIEW IF NOT EXISTS retiros_operacion_vigentes AS
 SELECT r.* FROM retiros_operacion r WHERE COALESCE((
 SELECT m.tipo FROM movimientos_participacion_operacion m
 WHERE m.operacion_id=r.operacion_id AND m.voluntario_id=r.voluntario_id
 ORDER BY m.revision DESC LIMIT 1),'RETIRO')='RETIRO';
