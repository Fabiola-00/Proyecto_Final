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
 observaciones TEXT
);
CREATE TABLE IF NOT EXISTS operaciones (
 id INTEGER PRIMARY KEY, tipo_evento TEXT NOT NULL, lugar TEXT NOT NULL,
 fecha_inicio TEXT NOT NULL, fecha_fin TEXT, institucion_responsable TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS participaciones_operacion (
 operacion_id INTEGER NOT NULL REFERENCES operaciones(id) ON DELETE RESTRICT,
 voluntario_id INTEGER NOT NULL REFERENCES voluntarios(usuario_id) ON DELETE RESTRICT,
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
