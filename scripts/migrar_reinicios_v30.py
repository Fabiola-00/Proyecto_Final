"""Migración aditiva v29 a v30, respaldo y verificación íntegra, sin reinicios reales."""
import json
import sqlite3
import uuid
from pathlib import Path

from migrar_recomendaciones_v29 import ROOT, huellas
from sicose import create_app
from sicose.db import obtener_conexion, inicializar_base_datos


def main():
    app = create_app()
    with app.app_context():
        p = Path(app.config['DATABASE'])
        if not p.is_absolute(): p = ROOT/p
        p = p.resolve()
        if not p.is_relative_to(ROOT) or not p.is_file():
            raise RuntimeError('Se requiere la base existente dentro del proyecto autorizado.')
        c = obtener_conexion()
        if c.execute("SELECT valor FROM app_meta WHERE clave='schema_version'").fetchone()[0] != '29':
            raise RuntimeError('Se esperaba v29; sin cambios.')
        if c.execute('PRAGMA quick_check').fetchone()[0] != 'ok' or c.execute('PRAGMA foreign_key_check').fetchall():
            raise RuntimeError('Integridad previa incorrecta; sin cambios.')
        antes = huellas(c)
        respaldo = p.parent/'backups'/f'sicose-20261018-pre-v30-{uuid.uuid4().hex[:8]}.sqlite3'
        respaldo.parent.mkdir(exist_ok=True)
        with sqlite3.connect(respaldo) as destino: c.backup(destino)
        inicializar_base_datos(); inicializar_base_datos()
        despues = huellas(c)
        assert all(despues.get(k) == v for k,v in antes.items())
        nuevas = sorted(set(despues)-set(antes))
        assert nuevas == ['reinicios_pruebas', 'reintentos_pruebas']
        assert all(despues[t]['filas'] == 0 for t in nuevas)
        assert c.execute("SELECT valor FROM app_meta WHERE clave='schema_version'").fetchone()[0] == '30'
        qc = c.execute('PRAGMA quick_check').fetchone()[0]
        fk = len(c.execute('PRAGMA foreign_key_check').fetchall())
        assert qc == 'ok' and fk == 0
        informe = dict(version_anterior=29, version_actual=30, respaldo=str(respaldo.relative_to(ROOT)),
            tablas_previas=len(antes), tablas_finales=len(despues), previas_preservadas=True,
            nuevas=nuevas, nuevas_vacias=True, inicializaciones=2, quick_check=qc, fk=fk,
            huellas_antes=antes, huellas_despues=despues)
        (ROOT/'.tmp').mkdir(exist_ok=True)
        (ROOT/'.tmp/reinicios-migracion.json').write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({k:v for k,v in informe.items() if not k.startswith('huellas')}, ensure_ascii=False))


if __name__ == '__main__': main()
