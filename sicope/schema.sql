CREATE TABLE IF NOT EXISTS app_meta (
    clave TEXT PRIMARY KEY,
    valor TEXT NOT NULL
);

INSERT INTO app_meta (clave, valor)
VALUES ('schema_version', '1')
ON CONFLICT(clave) DO NOTHING;
