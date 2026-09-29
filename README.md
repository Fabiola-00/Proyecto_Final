# SICOSE

Sistema de Control y Evaluación de Personal. Prototipo académico para seguimiento de voluntarios de rescate y emergencias.

## Estado

Fase 5 parcial — asistencias, catálogo/asignación de evaluaciones y notas no psicométricas con historial. Los dashboards por rol incorporan el emblema SBRAB, modo claro/oscuro y menú lateral plegable con los colores institucionales azul `#1D1BBE` y naranja `#F57B1A`. Se añadieron fotos de perfil privadas y restablecimiento administrativo de contraseñas antes de iniciar Fase 6. Los paneles siguen separados por rol: Administrador, Jefe de Personal e Instructor Voluntario. La versión 5 migró los códigos antiguos de rol conservando cuentas e historiales; la versión 6 agrega datos de identidad y fecha/código institucional de Instructores Voluntarios de forma aditiva. Los formularios e intentos psicométricos quedan bloqueados porque no hay instrumentos autorizados en `docs/06_pruebas_psicometricas.md`. La aplicación sigue siendo un prototipo local, no un sistema listo para producción.

## Documentación

- [Especificación funcional](docs/01_especificacion_funcional.md)
- [Arquitectura técnica](docs/02_arquitectura_tecnica.md)
- [Modelo de datos](docs/03_modelo_datos.md)
- [Diseño visual](docs/04_diseno_visual.md)
- [Plan de desarrollo](docs/05_plan_desarrollo.md)
- [Revisión de instrumentos psicométricos](docs/06_pruebas_psicometricas.md)
- [Instrucciones para agentes](AGENTS.md)
- [Instalación y ejecución en Windows](docs/07_inicio_desarrollo.md)
- [Historial de cambios y configuraciones](HISTORY.md)

## Stack previsto

Python/Flask, SQLite, HTML5, CSS3 y JavaScript puro mediante API REST JSON. Dependencias adicionales, si se proponen, se justificarán antes de incorporarlas. No cargar información personal real en la demostración.

## Inicio rápido en Windows

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
flask --app sicose init-db
flask --app sicose seed-admin
flask --app sicose run --debug
```

Antes de ejecutar los comandos Flask, completa en `.env` un secreto aleatorio `SICOSE_SECRET_KEY` y una contraseña local de desarrollo para `SICOSE_ADMIN_PASSWORD` (mínimo 12 caracteres). El usuario demo es `admin.demo`; el seed no imprime ni sobrescribe contraseñas.

Abre `http://127.0.0.1:5000/login`. Tras iniciar sesión, cada rol llega a su vista inicial. La guía completa, pruebas y límites están en [docs/07_inicio_desarrollo.md](docs/07_inicio_desarrollo.md).
