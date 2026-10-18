"""Migración aditiva local v28→v29 con respaldo y comparación íntegra de filas.

No crea cuentas, respuestas, revisiones, activaciones ni recomendaciones.
Ejecutar después de las pruebas, con el entorno local existente.
"""
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT/'.env')
from sicose import create_app
from sicose.db import obtener_conexion,inicializar_base_datos


def huellas(c):
    resultado={}
    for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall():
        nombre=r[0]
        filas=[tuple(f) for f in c.execute('SELECT * FROM "'+nombre.replace('"','""')+'"')]
        if nombre=='app_meta':filas=[f for f in filas if f[0]!='schema_version']
        serializadas=sorted(json.dumps(f,ensure_ascii=False,default=lambda v:v.hex()) for f in filas)
        resultado[nombre]={'filas':len(filas),'sha256':hashlib.sha256('\n'.join(serializadas).encode()).hexdigest()}
    return resultado


def main():
    app=create_app()
    with app.app_context():
        path=Path(app.config['DATABASE'])
        if not path.is_absolute():path=ROOT/path
        path=path.resolve()
        if not path.is_relative_to(ROOT):raise RuntimeError('La base configurada no está dentro del proyecto autorizado.')
        if not path.is_file():raise RuntimeError('La base local existente no se encontró. No se creará otra.')
        c=obtener_conexion()
        version=c.execute("SELECT valor FROM app_meta WHERE clave='schema_version'").fetchone()[0]
        if version!='28':raise RuntimeError('Se esperaba v28; no se aplicó ningún cambio.')
        if c.execute('PRAGMA quick_check').fetchone()[0]!='ok' or c.execute('PRAGMA foreign_key_check').fetchall():
            raise RuntimeError('La integridad previa requiere revisión.')
        antes=huellas(c)
        destino=path.parent/'backups'/f'sicose-20261018-pre-v29-{uuid.uuid4().hex[:8]}.sqlite3'
        destino.parent.mkdir(exist_ok=True)
        with sqlite3.connect(destino) as respaldo:c.backup(respaldo)
        inicializar_base_datos();inicializar_base_datos()
        despues=huellas(c)
        if any(despues.get(k)!=v for k,v in antes.items()):
            raise RuntimeError('La comparación detectó un cambio inesperado; conservar respaldo y revisar antes de usar.')
        nuevas=sorted(set(despues)-set(antes))
        assert all(despues[t]['filas']==0 for t in nuevas)
        actual=c.execute("SELECT valor FROM app_meta WHERE clave='schema_version'").fetchone()[0]
        qc=c.execute('PRAGMA quick_check').fetchone()[0]
        fk=len(c.execute('PRAGMA foreign_key_check').fetchall())
        assert actual=='29' and qc=='ok' and fk==0
        informe=dict(version_anterior=version,version_actual=actual,respaldo=str(destino.relative_to(ROOT)),
            tablas_previas=len(antes),tablas_finales=len(despues),previas_preservadas=True,
            nuevas=nuevas,tablas_nuevas_vacias=True,inicializaciones=2,quick_check=qc,fk=fk,
            huellas_antes=antes,huellas_despues=despues)
        (ROOT/'.tmp').mkdir(exist_ok=True)
        (ROOT/'.tmp/recomendaciones-migracion.json').write_text(json.dumps(informe,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({k:v for k,v in informe.items() if not k.startswith('huellas')},ensure_ascii=False))


if __name__=='__main__':main()
