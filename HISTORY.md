# Historial de cambios y configuraciones — SICOSE

## 2026-09-29 — Especialidad principal y año mostrado en dashboards

- Se agregó `voluntarios.especialidad_principal` mediante migración aditiva SQLite v8, con el catálogo acordado: Rescate en agua, Rescate en montaña, Rescate en selva, Lucha contra incendios, Primeros Auxilios y K-9. Los registros históricos quedan NULL y la interfaz los identifica como “Sin especialidad registrada”.
- La especialidad se captura en solicitudes y altas manuales, se valida en backend, se puede editar en el CRUD y aparece en el directorio de Instructores Voluntarios y junto a nombre/código en el registro de asistencia.
- Las pantallas protegidas muestran el año calendario actual en la etiqueta del dashboard. La actualización no cambia ni crea filas en `periodos`, que continúan como datos operativos administrados por su módulo.
- README, continuidad de AGENTS y documentación del esquema/inicio se alinearon con v8. Se añadieron pruebas para las vistas anuales y la nueva propiedad del perfil.
- Verificación: 43 pruebas aprobadas, compilación Python, sintaxis JavaScript y diff limpios. Base local migrada a v8 con `quick_check=ok`, cero infracciones FK, cuatro asistencias y un período existente conservados.

Registra requisitos acordados, cambios funcionales y configuraciones relevantes. Los estados describen el repositorio y las verificaciones disponibles; una entrada no implica que el cambio esté publicado o en producción. Las fechas de las fases tempranas no pudieron confirmarse y por eso se conserva su orden sin atribuirles fechas inventadas.

## Historial por fases

### Fase 1 — Base ejecutable

- Se creó el esqueleto de desarrollo con Python/Flask, HTML, CSS y JavaScript nativo.
- Se configuraron SQLite, variables locales, archivos de entorno de ejemplo, estructura inicial, ruta mínima y guía para instalar y ejecutar en Windows.
- Se añadieron pruebas iniciales para verificar la respuesta HTTP.

### Fase 2 — Persistencia y autenticación

- Se añadieron el modelo SQLite, perfiles y cuentas con contraseñas almacenadas como hash, autenticación y autorización por rol.
- Se añadieron login/logout, sesiones protegidas, validación CSRF, auditoría mínima y seed idempotente del Administrador.
- Se acordó validar permisos en backend y conservar datos e historial al ampliar el esquema.

### Fase 3 — Diseño y dashboards por rol

- Se implementaron una plantilla compartida y dashboards separados para Administrador, Jefe de Personal e Instructor Voluntario; login dirige al panel correspondiente al rol.
- Se incorporaron navegación lateral plegable, modo claro/oscuro, indicadores conectados a la base y diseño adaptable.
- Se adoptó la identidad SBRAB: emblema institucional, azul `#1D1BBE` y naranja `#F57B1A`. El acceso también se actualizó para incluir el logo y mantener el mismo lenguaje visual.
- Evaluar.com quedó como referencia general de organización; no se copia su marca o interfaz.

### Fase 4 — Solicitudes y administración de personal

- Se implementaron solicitudes públicas de registro de Instructor Voluntario, aprobación/rechazo administrativo y asignación a un Jefe de Personal. Las cuentas pendientes no acceden a datos protegidos.
- Administración puede crear cuentas de Instructor Voluntario manualmente. Se conserva la revisión de solicitudes; el panel dejó de ofrecer invitaciones por correo y mantiene las rutas antiguas por compatibilidad.
- Se incorporó una vista CRUD tabular para Instructores Voluntarios y otra para Jefes de Personal, con altas plegables, edición y desactivación lógica que conserva historial.
- Se añadieron altas/edición/desactivación de Jefes de Personal y controles para que un Jefe de Personal opere solo sobre su equipo asignado.

### Fotos, configuración de cuenta y cambio de nombres de rol

- Se agregó carga opcional de fotos PNG/JPEG a los formularios de perfiles, edición administrativa y visualización privada en los paneles del Administrador, Jefe de Personal e Instructor Voluntario. Las imágenes se guardan bajo `instance/perfiles`, fuera de recursos estáticos.
- Administración puede editar su propio nombre, foto y contraseña; también restablecer las contraseñas de Jefes de Personal e Instructores Voluntarios. El cambio almacena un hash e invalida sesiones anteriores.
- Los nombres vigentes pasaron de `INSTRUCTOR`/`VOLUNTARIO` a `JEFE_PERSONAL`/`INSTRUCTOR_VOLUNTARIO`. La migración v5 conserva IDs, perfiles, relaciones e historial.

### Datos de identidad del Instructor Voluntario — esquema v6

- Se acordaron nombres, apellido paterno, apellido materno y fecha completa de nacimiento para crear el código institucional de tres iniciales más `DDMMAA` (ejemplo `DMC-020478`).
- Los formularios de solicitud, alta administrativa y edición se coordinaron con los campos almacenados. El servidor genera el código y rechaza colisiones; la política definitiva para duplicados sigue pendiente.
- La migración v6 agrega los campos sin inventar información para perfiles históricos y crea un índice único parcial para códigos presentes.
- Siguen pendientes datos demográficos/organizacionales: país/nacionalidad y departamento dependiente, año de incorporación y antigüedad calculada, especialidad principal/secundarias, catálogo relacional de cursos y operaciones.

### Fase 5 parcial — Evaluaciones, asistencia y capacitaciones

- Administración tiene pantallas iniciales para períodos, catálogo de evaluaciones y asignaciones. Jefe de Personal puede registrar/corregir calificaciones manuales no psicométricas con historial; el Instructor Voluntario solo consulta estados y avance, sin notas ni observaciones.
- Se rediseñó asistencia como lista por fecha y actividad con los estados Asiste, Atraso, Permiso y Falta. El historial filtra por Instructor Voluntario, última fecha registrada o rango de fechas.
- Capacitaciones o Cursos se separó de Asistencias y se añadió al menú lateral de Administrador y Jefe de Personal. La pantalla permite listar, registrar y editar entradas de `capacitaciones`; no hay borrado físico y el Jefe de Personal queda limitado a su ámbito.
- La migración aditiva v7 agregó `asistencias.estado_detalle` y conservó la columna de estado previa. Los registros antiguos siguen intactos; una categoría de presentación se deriva de cada estado legado para el historial nuevo.
- Las pruebas psicométricas continúan bloqueadas: no hay instrumentos, reactivos ni reglas de puntuación aprobados para habilitarlas. Fase 6 no ha comenzado.

## Revisión de consistencia y migración local — 2026-09-29

- La auditoría de base y formularios encontró desajuste entre el esquema local anterior y los campos requeridos por el código. Se corrigió el orden de actualización de `schema_version` para marcar una migración solo después de ejecutarla correctamente.
- Se alineó la vista previa del código de Instructor Voluntario con la validación del servidor; se reforzó la validación de solicitudes y se evita dejar archivos de foto huérfanos cuando una operación falla.
- En esa revisión la base local aún estaba en versión 5. Posteriormente se ejecutó `flask --app sicose init-db` para aplicar la migración acumulada a versión 7. Se conservaron las 4 filas existentes de asistencia.
- Tras la migración local, SQLite devolvió `quick_check=ok` y cero infracciones de claves foráneas.
- En las verificaciones funcionales más recientes, 42 pruebas aprobaron; también pasaron la compilación de Python, `node --check frontend\static\js\app.js` y `git diff --check` (este último mostró avisos de conversión de finales de línea, sin errores de espacios).

## Actualización documental — 2026-09-29

- Se reorganizó este historial para reflejar fases, migraciones, acuerdos visuales, cambios de roles, administración de perfiles y el estado parcial de Fase 5.
- Se amplió `README.md` con requisitos aprobados, alcance por rol, privacidad, datos del Instructor Voluntario, identidad visual, estado implementado/pendiente, instalación, pruebas y referencias técnicas.
- Esta actualización solo modifica documentación; las cifras de pruebas de la sección anterior corresponden al último cambio funcional verificado.
