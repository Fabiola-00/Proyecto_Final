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

## Punto de continuidad del proyecto — 2026-10-10 (revisión documental)

Este bloque permite continuar el trabajo desde el estado actual sin recrear la configuración local ni repetir decisiones ya confirmadas.

- **Fase:** Fase 5 parcial; 4B implementada técnicamente, pendiente aceptación operativa. El plan conserva la numeración histórica y separa 4A/4B, 5A/5B, psicometría, reportes operativos/psicométricos, preparación del piloto e IA opcional. Fase 6 e integración de IA todavía no comienzan; existen reportes operativos PDF de cursos y asistencia, con alcance limitado. Consultar `docs/05_plan_desarrollo.md` antes de elegir el siguiente alcance.
- **Esquema:** SQLite versión 14. La v14 añade grado y fecha de incorporación canónica, ambos nullable; al editar una fecha explícita se sincroniza su año y antiguedad_desde. La v10 añade la relación de especialidades secundarias sin rellenar históricos. La v9 agrega residencia e incorporación nullable, sin rellenar históricos ni modificar antiguedad_desde. La migración v8 agrega `voluntarios.especialidad_principal` de forma aditiva; los perfiles existentes se conservan con NULL hasta que se editen. Tras cambios futuros de esquema, inicializar de forma aditiva y verificar integridad; nunca resetear ni borrar datos históricos.
- **Verificación histórica (2026-10-10, primera entrega 4B):** 54 pruebas aprobadas en 61,107 s con `python -m unittest discover -s tests -v`, Python de `.venv` y bases aisladas; enlaces locales comprobados y `git diff --check` sin errores. **Evidencia histórica (2026-09-29):** 43 pruebas aprobadas en v8; también pasaron `python -m compileall -q sicose tests`, `node --check frontend\static\js\app.js`, `git diff --check`; SQLite verificó `quick_check=ok`, cero infracciones de claves foráneas y cuatro asistencias preservadas. En 4B se aplicó v9 tras respaldo SQLite: datos previos conservados en 18 tablas, campos nuevos NULL, quick_check=ok y cero infracciones FK. Compilación Python, sintaxis JavaScript y seis escenarios de interfaz en Chromium con API simulada correctos.
- **Entorno local:** el repositorio ya tiene `.venv`, `.env` e `instance/sicose.sqlite3`. No recrear ni reemplazar `.env`, no mostrar sus secretos y no volver a instalar/configurar el entorno sin una necesidad concreta. El estado de Git contiene cambios de trabajo sin commit: inspeccionarlos y preservarlos antes de editar.

### Decisiones acordadas que no deben volver a preguntarse

- Roles: `ADMINISTRADOR`, `JEFE_PERSONAL` (Jefe de Personal) e `INSTRUCTOR_VOLUNTARIO` (Instructor Voluntario). Cada uno debe entrar a su dashboard; la autorización siempre se valida en servidor.
- El dashboard de Administrador administra cuentas y evaluaciones globales. Jefe de Personal gestiona únicamente los Instructores Voluntarios activos asignados, sus registros permitidos y sus notas no psicométricas. Instructor Voluntario solo debe ver estado/avance de sus evaluaciones, nunca notas u observaciones; puede editar exclusivamente correo y foto propios mediante Mi perfil, según decisión del 2026-10-10.
- El registro de asistencia conserva **fecha y actividad** y tiene exactamente cuatro opciones visibles: **Asiste, Atraso, Permiso y Falta**. Esquema v7 conserva el campo histórico anterior y agrega `estado_detalle`. El historial permite filtrar por Instructor Voluntario, por la última fecha con registros o por rango inicial/final. En el formulario, cada fila muestra Nombre completo, Código, Estado de cuenta horizontal (ACTIVO verde/INACTIVO rojo) y Asistencia seleccionable; la llamada solo incluye personal activo autorizado.
- **Capacitaciones o Cursos** es una página aparte en los menús de Administrador y Jefe de Personal. El alcance confirmado es listar, registrar y editar filas de `capacitaciones`; no borrar físicamente registros. En v11 existe catálogo común administrativo y curso_id opcional; el nombre histórico sigue preservado.
- Identidad visual: logo SBRAB, azul `#1D1BBE`, naranja `#F57B1A`, dashboards plegables y modo claro/oscuro. Evaluar.com es solo inspiración general; no copiar su marca/interfaz.
- Código de Instructor Voluntario: inicial de nombres y de cada apellido + `DDMMAA`; la fecha completa ya está acordada y el backend genera el código. La regla definitiva para una colisión sigue sin definición; el comportamiento actual la rechaza preventivamente.
- No habilitar evaluaciones psicométricas hasta documentar aprobación profesional/institucional, licencia/derechos, versión lingüística, puntuación y retención. No fabricar reactivos, resultados, predicciones ni IA.

### Estado funcional para el siguiente trabajo

- Ya hay solicitudes públicas pendientes, aprobación/rechazo, alta manual administrativa de Instructores Voluntarios, directorios tabulares: Administrador lista, crea, edita y desactiva; Jefe de Personal consulta, edita y desactiva únicamente Instructores Voluntarios activos asignados y solicita altas pendientes con aprobación/rechazo administrativo; gestión de Jefes de Personal, asignaciones, fotos privadas y restablecimiento administrativo de contraseñas.
- El perfil v8 incluye nombres, apellidos, fecha de nacimiento, código y especialidad principal con el catálogo ya acordado. Los perfiles anteriores pueden mostrar “Sin especialidad registrada”. El pendiente histórico de especialidad principal quedó resuelto en v8. `antiguedad_desde` es una fecha y `experiencia_operaciones` texto libre; no representan antigüedad calculada ni operaciones relacionadas. En v9 hay país/departamento de residencia (Bolivia y sus nueve departamentos), año de incorporación y antigüedad = año calendario actual del servidor menos incorporación; campos opcionales sin inferir datos históricos. Administrador/Jefe autorizado los ve/edita, Jefe solo activos asignados; en v9 Instructor no los recibía; en v11 consulta residencia/nacionalidad propias sin editar, con incorporación aún oculta. En v11 están implementados nacionalidad/residencia ampliada, catálogo de cursos y operaciones relacionadas; las reglas vigentes se detallan abajo. Los campos de operación acordados son tipo de evento, lugar, fecha de inicio/fin e institución responsable.
- El año mostrado como período actual en los encabezados de dashboards se calcula con el año calendario local del servidor; no se crean, renombran ni alteran filas guardadas en `periodos`.
- Fase 5 incluye asistencia, capacitaciones, períodos/catálogo/asignaciones iniciales y calificaciones manuales no psicométricas con historial. Versionado completo de ponderaciones, reglas de faltantes/promedios, evaluaciones psicométricas requieren trabajo adicional. El autoservicio acordado de correo y foto está implementado.
- Reportes PDF/Excel y cualquier IA no están implementados. La IA no forma parte del estado actual.

### Límites y siguiente entrega

- Primera entrega 4B implementada: residencia e incorporación conforme a decisiones del 2026-10-10. Pendiente aceptación operativa del solicitante; las especialidades secundarias ya están implementadas en v10; cursos/operaciones y geografía ampliada quedaron implementados en v11 conforme a los acuerdos posteriores; ver estado vigente al final.

- Esta actualización es documental; preserva cambios locales previos en `frontend/gestion_asistencias.html`, `frontend/static/css/estilos.css`, `frontend/static/js/app.js` y `tests/test_app.py`, sin atribuirles fecha de implementación.
- Fase 4A: flujos acordados implementados y verificados por pruebas HTTP; aceptación visual/operativa pendiente. el 2026-10-10 se autorizó e implementó solicitud de alta por Jefe, pendiente de aprobación administrativa y asignada al Jefe autenticado. El backend limita consulta/edición/desactivación del Jefe a personal activo asignado. El autoservicio autorizado e implementado en Mi perfil permite solo correo y foto; identidad, código, especialidad, antigüedad, rol, estado y asignación quedan excluidos. La política definitiva de colisiones sigue pendiente.
- `/api/admin/estado` comprueba autorización administrativa, no salud integral. Las tablas de pesos no acreditan versiones publicadas ni promedios oficiales.

### Inicio y pruebas en Windows

Desde la raíz y con el entorno existente activado, el servidor se inicia con `flask --app sicose run --debug` y las pruebas con `python -m unittest discover -s tests -v`. La guía completa y creación inicial de entorno están en `docs/07_inicio_desarrollo.md`; no repetir su configuración si `.venv` y `.env` ya existen. Para revisar y actualizar requerimientos/estado leer `README.md`, `docs/01_especificacion_funcional.md`, `docs/02_arquitectura_tecnica.md`, `docs/03_modelo_datos.md` y `docs/05_plan_desarrollo.md`.

### Estado vigente — Cierre técnico de Fase 4B (2026-10-10)

Esquema v11. Nacionalidad (país) y residencia diferenciadas, con 20 países latinoamericanos iniciales; Bolivia con nueve departamentos, los demás con provincia/departamento en texto libre. Administrador/Jefe autorizado editan; Instructor consulta sus propios datos geográficos. Incorporación sigue limitada a gestión. Secundarias consultables por ámbito, editables por Administrador/Jefe; la principal puede repetirse como secundaria.

Catálogo común de cursos creado/editado solo por Administrador; capacitaciones vinculadas opcionalmente por Administrador/Jefe al personal de su ámbito activo. Instructor consulta su formación sin observaciones. Históricos sin enlace automático; renombrar catálogo no cambia nombres previamente registrados. Administrador crea/edita eventos de operaciones; Administrador/Jefe vinculan personal activo de su ámbito; Instructor consulta solo sus participaciones. Se conserva el texto histórico de experiencia; no se implementa borrado/desvinculación.

58 pruebas aprobadas en 62,893 s. Migración local v11 con respaldo, 19 tablas anteriores preservadas, inicialización repetida, curso_id previo NULL, quick_check=ok y cero infracciones FK. Cierre técnico implementado; aceptación operativa pendiente. Siguiente entrega: Fase 5A, ensayo de asistencia, capacitaciones y notas manuales por rol, con correcciones e historial. Privacidad/retención y autorización institucional siguen pendientes antes del piloto.

Verificación visual final 4B (2026-10-10): 18 escenarios en Chromium, tres roles y anchos 360/1447 px con datos sintéticos/API simulada; sin desborde ni errores JavaScript. Conservación de provincia al abrir modal y curso_id al editar comprobadas. El desborde inicial del control de foto móvil se corrigió limitando controles al ancho disponible. Enlaces documentales, compilación Python, sintaxis JavaScript y git diff --check correctos.

### Corrección vigente — Registro de cursos (2026-10-10, v12)

La pantalla “Capacitaciones y Cursos” registra cursos independientes de personas. Incluye nombre, tipo (Capacitación, Especialización, Actualización, Taller, Seminario (Webinar)), entidad organizadora, inicio/fin, estado (Próximo, En curso, Finalizado) y observaciones opcionales. Nombre, tipo y estado obligatorios para registros nuevos; fechas/entidad opcionales; fin requiere inicio y no puede precederlo. Estado se elige manualmente, sin deducirlo de fechas. Administrador registra/edita; Jefe consulta el catálogo según permisos ya acordados. Edición mediante modal responsivo con datos precargados y errores en el modal.

Se retiraron de esta pantalla el selector de Instructor y el formulario de asignación. Los registros personales históricos, sus vínculos y APIs se conservan; no hay interfaz nueva de asignación en esta entrega. “Mis cursos” sigue consultando historial personal sin observaciones. Las observaciones del catálogo son distintas del historial personal y solo se muestran a Administrador/Jefe.

Migración v12 aditiva: campos nuevos nullable en cursos, sin inferir tipo, estado ni fechas de históricos. Respaldo SQLite previo, datos de 23 tablas anteriores preservados, inicialización repetida, quick_check=ok y FK=0. 59 pruebas aprobadas en 42,354 s (ejecución final); cuatro escenarios Chromium con API simulada, Administrador/Jefe a 360/1447px, opciones exactas y edición modal correctas. Compilación Python, sintaxis JavaScript y diff comprobados.

### Actualización vigente — Cursos por Jefe y PDF operativo (2026-10-10)

El solicitante autorizó también al Jefe de Personal a crear/editar el catálogo común; esta decisión sustituye la exclusividad administrativa anterior. Administrador y Jefe ven formulario Registro de curso, edición modal y menú/título “Capacitaciones y Cursos”. La asignación de personas continúa fuera de esta pantalla; historial personal conservado.

Reporte GET `/api/cursos/reporte.pdf`, autorizado para Administrador/Jefe; Instructor excluido. Rango obligatorio e inclusivo por fecha de inicio, tipo/estado opcionales combinados; fechas/filtros inválidos rechazados. Cursos sin inicio excluidos; resultado vacío produce PDF explícito. Incluye nombre, tipo, entidad, fechas, estado y total, sin datos personales ni observaciones. Carimbo en cada página con logo SBRAB, nombre institucional completo, fecha/hora de Bolivia y numeración; respuesta privada no-store y auditoría mínima de generación.

ReportLab incorporado a requirements y al entorno existente; no se recreó .venv, .env ni base. Este reporte inicia una entrega operativa acotada de Fase 7; no implementa reportes personales/psicométricos, Excel ni promedios oficiales. Privacidad/retención y aprobación del piloto siguen pendientes.

Verificación final (2026-10-10): 60 pruebas aprobadas en 28,375 s; PDF sintético multipágina renderizado e inspeccionado, carimbo y tabla sin solapamientos. La primera ejecución falló en dos expectativas del antiguo título; corregidas y suite completa repetida. Compilación Python, sintaxis JavaScript y diff correctos.

Interfaz de Jefe verificada en Chromium a 360/1447 px con API simulada: formulario visible, edición modal y acción de generación PDF sin desborde. El endpoint entrega PDF real validado en pruebas HTTP.

### Entrega vigente — Asistencia, correcciones, calendario y reporte (2026-10-10, v13)

- Administrador consulta/registra/corrige asistencia; Jefe solo personal activo asignado. La llamada muestra nombre del responsable autenticado, gestión anual de la fecha seleccionada y fecha; conserva actividad obligatoria. Los cuatro estados exactos son Asiste, Atraso, Permiso y Falta. Llamada nueva inicia todas las filas en Falta; al elegir fecha/actividad existente se cargan sus estados guardados para corregirlos.
- Clave única persona/fecha/actividad: guardar otra vez actualiza el mismo registro. Corrección conserva estado anterior/nuevo, actor y fecha UTC en historial_asistencias mediante trigger; cambios se auditan. Repetir el mismo estado no crea corrección ni sustituye al último responsable. No se permiten cambiar identidad/fecha/actividad mediante el PATCH de corrección. Históricos no se borran ni se fabrican correcciones anteriores.
- Instructor consulta solo su calendario anual y totales de los cuatro estados, sin datos de terceros ni observaciones ni edición. El día puede tener varias llamadas; totales cuentan registros, no días calendario. Sin registro no se considera Falta.
- Reporte matricial por rango inclusivo de fechas, sin materia ni filtros adicionales. Columnas por fecha/actividad, código y nombre, cuatro totales y porcentaje. Asiste y Atraso cuentan como asistencia; Permiso excluido: (Asiste + Atraso)/(Asiste + Atraso + Falta), redondeado a dos decimales; sin denominador, No disponible. Es un indicador operativo aprobado para esta entrega, no una nota ni promedio oficial de Fase 5B. Jefe exporta solo ámbito activo asignado; Administrador todo su alcance; Instructor no exporta reporte administrativo.
- PDF imprimible horizontal: matriz dividida en bloques de hasta ocho llamadas, filas paginadas y cabeceras repetidas, sin perder columnas. Carimbo SBRAB en cada página con escudo, nombre completo institucional y generación en hora de Bolivia; paginación, rango, leyenda y fórmula visibles. Sin observaciones; descarga privada no-store y auditoría mínima.
- Migración local v13 tras respaldo: 23 tablas anteriores preservadas, inicialización repetida, quick_check=ok y cero infracciones FK. Entorno, secretos y base existente conservados. Aceptación operativa del solicitante pendiente; Fase 5A aún requiere revisar integralmente cursos/notas y sus casos de corrección. Retención/privacidad y autorización institucional siguen pendientes antes del piloto.

Verificación final de asistencia (2026-10-10): 62 pruebas aprobadas en 69,702 s con bases aisladas; seis escenarios Chromium a 360/1447 px por los tres roles con API simulada. PDF sintético de seis páginas inspeccionado, cabeceras/carimbo y paginación correctos; encabezado del reporte adaptado para mantener legibilidad. Compilación Python, sintaxis JavaScript, enlaces locales y git diff --check correctos.


### Perfil y directorio vigentes — Grado e incorporación (2026-10-10, v14)

- Directorio con Nombre completo, Código, Grado, Especialidad Principal, Estado, Antigüedad y Acciones. Estado horizontal: ACTIVO verde, INACTIVO rojo, con texto identificable. Ver consulta en modal los datos permitidos y foto; Editar perfil usa modal y Desactivar conserva baja lógica. Restablecer contraseña sigue siendo exclusivo del Administrador, dentro de Editar perfil; nunca se muestra la contraseña guardada ni su hash.
- Grados permitidos: Instructor Inicial, Instructor Segundo, Instructor Primero, Instructor Principal e Instructor Mayor. Administrador los asigna/edita; Jefe solo en personal activo asignado y puede proponerlo al solicitar el alta de su equipo. Instructor consulta el suyo sin editar. La solicitud pública no permite enviar grado; queda NULL hasta revisión del personal autorizado. No se asigna un grado por defecto a históricos ni se infiere por antigüedad.
- Una sola Fecha de incorporación en alta y edición. Al registrarla se sincronizan fecha_incorporacion, antiguedad_desde y ano_incorporacion. Antigüedad = año calendario actual del servidor menos año de incorporación, sin descontar meses/días. Fechas inválidas/futuras y año/fecha contradictorios rechazados. Históricos mantienen año y fecha anterior, incluso si difieren, hasta completar explícitamente la nueva fecha; no se fabrican fechas desde un año. Borrar una fecha canónica existente borra también sus dos valores derivados; un formulario sin fecha histórica completa conserva el año previo.
- Alta administrativa permite ACTIVO o INACTIVO. Solicitudes de Jefe/públicas permanecen PENDIENTE, sin selector que habilite acceso, hasta aprobación administrativa. Las cuentas inactivas/pendientes no acceden a información protegida.
- Alta y solicitudes incluyen nombres, ambos apellidos, nacimiento, código generado en servidor, especialidad principal, usuario, correo, contraseña, nacionalidad, departamento y foto PNG/JPEG (máximo 3 MiB). Correo, nacionalidad, departamento y foto ahora son obligatorios también en servidor. Fecha de incorporación y grado son opcionales; las solicitudes públicas no incluyen grado. Residencia Bolivia oculta en las pantallas nuevas, nacionalidad independiente y catálogo latinoamericano existente. Países históricos se conservan en consulta/edición; no hay reclasificación automática a Bolivia en migración. Botón Guardar. Invitaciones usan el mismo formulario y validaciones.
- Migración v14 aditiva: grado y fecha_incorporacion nullable, sin rellenar perfiles anteriores. Respaldo local previo; 24 tablas anteriores preservadas, inicialización repetida, quick_check=ok y cero infracciones de claves foráneas. No se recrearon .venv, .env ni base local.

Verificación actual (2026-10-10): 64 pruebas aprobadas en 31,611 s, con bases aisladas. Ocho escenarios Chromium con datos sintéticos/API simulada (Administración, Jefe, Instructor y solicitud pública; 360/1447 px), modales precargados, campos/opciones/roles y ausencia de desborde comprobados. Compilación Python, sintaxis JavaScript y git diff --check correctos. La primera ejecución detectó dos expectativas antiguas de etiquetas (Guardar y retiro de Especialidad en tabla de asistencia); actualizadas y suite completa repetida. No se afirma cierre de Fase 5A ni aceptación institucional del piloto.
