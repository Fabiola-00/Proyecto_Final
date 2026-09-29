CREATE TABLE IF NOT EXISTS app_meta (
    clave TEXT PRIMARY KEY,
    valor TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE CHECK (nombre IN ('ADMINISTRADOR', 'INSTRUCTOR', 'VOLUNTARIO'))
);

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL COLLATE NOCASE UNIQUE CHECK (length(username) BETWEEN 3 AND 80),
    nombre_completo TEXT NOT NULL CHECK (length(nombre_completo) BETWEEN 1 AND 160),
    correo TEXT UNIQUE,
    password_hash TEXT NOT NULL,
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
    experiencia_operaciones TEXT,
    antiguedad_desde TEXT,
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
    categoria TEXT NOT NULL CHECK (categoria IN ('PSICOMETRICA', 'FISICA', 'ACADEMICA', 'INSTRUCTOR')),
    origen_nota TEXT NOT NULL CHECK (origen_nota IN ('VOLUNTARIO', 'INSTRUCTOR')),
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

INSERT INTO app_meta (clave, valor)
VALUES ('schema_version', '3')
ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor;
