# Guía del proyecto SICOSE

SICOSE significa **Sistema de Control y Evaluación de Personal**. Es un prototipo académico para seguimiento de personal voluntario de rescate y emergencias, no un producto comercial ni clínico.

## Stack y arquitectura

- Frontend: HTML5, CSS3 y JavaScript puro.
- Backend: Python y Flask; comunicación de interfaz mediante API REST JSON.
- Persistencia: SQLite con consultas parametrizadas, claves foráneas activadas y cambios de esquema aditivos.
- Mantener módulos pequeños y nombres consistentes en español. No agregar frameworks/servicios sin necesidad y autorización.
- Identidad visual aprobada: azul `#1D1BBE`, naranja `#F57B1A`; incorporar el emblema institucional SBRAB proporcionado en la cabecera de la barra lateral. Usar Evaluar.com solo como referencia general, sin copiar marca o interfaz.

## Roles y datos

- Roles vigentes: `ADMINISTRADOR` (Administrador), `JEFE_PERSONAL` (Jefe de Personal) e `INSTRUCTOR_VOLUNTARIO` (Instructor Voluntario). Las bases previas con `INSTRUCTOR`/`VOLUNTARIO` se migran preservando IDs e historial.
- Toda autorización debe comprobarse en el backend; ocultar controles de interfaz no constituye seguridad.
- El Jefe de Personal desactiva, no elimina físicamente, Instructores Voluntarios. Conservar historial y evitar cascadas destructivas.
- Estados pendientes/inactivos no acceden a información protegida.
- No incorporar reactivos ni habilitar pruebas psicométricas sin verificar licencia, versión lingüística, puntuación y revisión profesional.
- No almacenar datos reales para demo. No exponer SQLite, contraseñas, hashes, claves ni tokens a la interfaz.

## Seguridad

- Contraseñas con hash moderno y secretos únicamente desde entorno/`.env` local ignorado por Git.
- Sesiones protegidas, cookie HttpOnly/SameSite, Secure en HTTPS y CSRF en operaciones mutables con cookie.
- Validar entradas en servidor, parametrizar SQL y devolver errores JSON claros sin trazas ni información sensible.
- Auditar operaciones sensibles con metadatos mínimos; nunca registrar credenciales o respuestas psicométricas completas.
- La IA no existe aún. No inventar predicciones ni presentar reglas como modelo entrenado.

## Desarrollo

- Antes de cambiar archivos, inspeccionar el estado actual y explicar objetivo/alcance.
- Avanzar por fases pequeñas. Mantener README y documentos técnicos alineados con lo realmente implementado.
- Ejecutar pruebas relevantes y reportar exactamente sus resultados; no afirmar funciones sin verificarlas.
- No borrar datos históricos ni resetear la base en comandos de inicialización.
- Si falta una decisión que afecte privacidad, autorización, puntuación o validez psicométrica, documentar el límite y consultar antes de asumir.

## Punto de continuidad del proyecto — 2026-09-29

Este bloque permite continuar el trabajo desde el estado actual sin recrear la configuración local ni repetir decisiones ya confirmadas.

- **Fase:** Fase 5 parcial. Fase 6, reportes e integración de IA todavía no comienzan. Consultar `docs/05_plan_desarrollo.md` antes de elegir el siguiente alcance.
- **Esquema:** SQLite versión 8. La migración v8 agrega `voluntarios.especialidad_principal` de forma aditiva; los perfiles existentes se conservan con NULL hasta que se editen. Tras cambios futuros de esquema, inicializar de forma aditiva y verificar integridad; nunca resetear ni borrar datos históricos.
- **Verificación funcional vigente:** 43 pruebas aprobadas con `python -m unittest discover -s tests -v`. En la actualización v8 también pasaron `python -m compileall -q sicose tests`, `node --check frontend\static\js\app.js`, `git diff --check`; SQLite verificó `quick_check=ok`, cero infracciones de claves foráneas y cuatro asistencias preservadas. La base local conserva un período existente sin modificación.
- **Entorno local:** el repositorio ya tiene `.venv`, `.env` e `instance/sicose.sqlite3`. No recrear ni reemplazar `.env`, no mostrar sus secretos y no volver a instalar/configurar el entorno sin una necesidad concreta. El estado de Git contiene cambios de trabajo sin commit: inspeccionarlos y preservarlos antes de editar.

### Decisiones acordadas que no deben volver a preguntarse

- Roles: `ADMINISTRADOR`, `JEFE_PERSONAL` (Jefe de Personal) e `INSTRUCTOR_VOLUNTARIO` (Instructor Voluntario). Cada uno debe entrar a su dashboard; la autorización siempre se valida en servidor.
- El dashboard de Administrador administra cuentas y evaluaciones globales. Jefe de Personal gestiona únicamente los Instructores Voluntarios activos asignados, sus registros permitidos y sus notas no psicométricas. Instructor Voluntario solo debe ver estado/avance de sus evaluaciones, nunca notas u observaciones; puede editar su perfil propio como requerimiento acordado, aunque ese autoservicio sigue pendiente.
- El registro de asistencia conserva **fecha y actividad** y tiene exactamente cuatro opciones visibles: **Asiste, Atraso, Permiso y Falta**. Esquema v7 conserva el campo histórico anterior y agrega `estado_detalle`. El historial permite filtrar por Instructor Voluntario, por la última fecha con registros o por rango inicial/final. En el formulario, cada fila muestra nombre completo, código, especialidad principal y estado.
- **Capacitaciones o Cursos** es una página aparte en los menús de Administrador y Jefe de Personal. El alcance confirmado es listar, registrar y editar filas de `capacitaciones`; no borrar físicamente registros. El nombre de curso aún es texto libre, no catálogo relacional.
- Identidad visual: logo SBRAB, azul `#1D1BBE`, naranja `#F57B1A`, dashboards plegables y modo claro/oscuro. Evaluar.com es solo inspiración general; no copiar su marca/interfaz.
- Código de Instructor Voluntario: inicial de nombres y de cada apellido + `DDMMAA`; la fecha completa ya está acordada y el backend genera el código. La regla definitiva para una colisión sigue sin definición; el comportamiento actual la rechaza preventivamente.
- No habilitar evaluaciones psicométricas hasta documentar aprobación profesional/institucional, licencia/derechos, versión lingüística, puntuación y retención. No fabricar reactivos, resultados, predicciones ni IA.

### Estado funcional para el siguiente trabajo

- Ya hay solicitudes públicas pendientes, aprobación/rechazo, alta manual administrativa de Instructores Voluntarios, directorios CRUD tabulares por rol, gestión de Jefes de Personal, asignaciones, fotos privadas y restablecimiento administrativo de contraseñas.
- El perfil v8 incluye nombres, apellidos, fecha de nacimiento, código y especialidad principal con el catálogo ya acordado. Los perfiles anteriores pueden mostrar “Sin especialidad registrada”. País/nacionalidad, departamento dependiente, incorporación/antigüedad calculada, especialidades secundarias, catálogo relacional de cursos y tabla/relaciones de operaciones siguen pendientes. Los campos de operación acordados son tipo de evento, lugar, fecha de inicio/fin e institución responsable.
- El año mostrado como período actual en los encabezados de dashboards se calcula con el año calendario local del servidor; no se crean, renombran ni alteran filas guardadas en `periodos`.
- Fase 5 incluye asistencia, capacitaciones, períodos/catálogo/asignaciones iniciales y calificaciones manuales no psicométricas con historial. Versionado completo de ponderaciones, reglas de faltantes/promedios, evaluaciones psicométricas y autoservicio de perfil del Instructor Voluntario requieren trabajo adicional.
- Reportes PDF/Excel y cualquier IA no están implementados. La IA no forma parte del estado actual.

### Inicio y pruebas en Windows

Desde la raíz y con el entorno existente activado, el servidor se inicia con `flask --app sicose run --debug` y las pruebas con `python -m unittest discover -s tests -v`. La guía completa y creación inicial de entorno están en `docs/07_inicio_desarrollo.md`; no repetir su configuración si `.venv` y `.env` ya existen. Para revisar y actualizar requerimientos/estado leer `README.md`, `docs/01_especificacion_funcional.md`, `docs/02_arquitectura_tecnica.md`, `docs/03_modelo_datos.md` y `docs/05_plan_desarrollo.md`.
