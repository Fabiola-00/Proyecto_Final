# SICOPE

Prototipo académico para seguimiento y evaluación de voluntarios de rescate y emergencias. El repositorio contiene la especificación inicial y ahora incorpora el esqueleto Flask/SQLite de la Fase 1; autenticación, evaluaciones y dashboards siguen fuera de alcance.

## Estado

Fase 1 — base local ejecutable y estructura inicial. Aún no es una aplicación lista para producción.

## Documentación

- [Especificación funcional](docs/01_especificacion_funcional.md)
- [Arquitectura técnica](docs/02_arquitectura_tecnica.md)
- [Modelo de datos](docs/03_modelo_datos.md)
- [Diseño visual](docs/04_diseno_visual.md)
- [Plan de desarrollo](docs/05_plan_desarrollo.md)
- [Revisión de instrumentos psicométricos](docs/06_pruebas_psicometricas.md)
- [Instrucciones para agentes](AGENTS.md)
- [Instalación y ejecución en Windows](docs/07_inicio_desarrollo.md)

## Stack previsto

Python/Flask, SQLite, HTML5, CSS3 y JavaScript puro mediante API REST JSON. Dependencias adicionales, si se proponen, se justificarán antes de incorporarlas. No cargar información personal real en la demostración.

## Inicio rápido en Windows

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
flask --app sicope init-db
flask --app sicope run --debug
```

Abre `http://127.0.0.1:5000/`. Los pasos completos y ejecución de pruebas están en [docs/07_inicio_desarrollo.md](docs/07_inicio_desarrollo.md).
