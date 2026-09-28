# 02. Arquitectura técnica

## Esquema

Aplicación monolítica modular: navegador con HTML/CSS/JavaScript nativo → API REST JSON Flask → capa de servicios y autorización → repositorios SQLite. Flask entrega páginas estáticas/templates y endpoints JSON bajo un mismo origen para reducir complejidad CORS. Base local fuera del directorio público.

## Módulos propuestos

- `auth`: ingreso, cierre, sesiones, invitaciones y solicitudes pendientes.
- `usuarios`: roles, instructores, voluntarios, asignación y estados.
- `periodos`: ciclos y versiones de ponderación.
- `evaluaciones`: catálogo, asignación, habilitación, intentos, notas y observaciones.
- `reportes`: exportaciones con alcance aplicado según rol.
- `auditoria`: registro de acciones sensibles.
- `ia`: interfaz/proveedor desacoplado futuro; sin implementación predictiva inicialmente.

Separar rutas, servicios, persistencia y validadores. Las reglas de autorización residen en servidor y se aplican antes de consultar/devolver el recurso. API responde errores JSON con código HTTP apropiado sin filtrar trazas o información sensible.

## Seguridad y privacidad previstas

- Contraseñas con hash adaptativo reconocido (Werkzeug/PBKDF2 o Argon2 si dependencia aprobada); jamás texto plano.
- Secretos por variable de entorno/configuración local ignorada por Git; modo de desarrollo falla con mensaje claro si falta configuración obligatoria sensible.
- Cookies de sesión `HttpOnly`, `SameSite`, `Secure` en HTTPS; duración y renovación configurables; cerrar sesión invalida la sesión.
- Token CSRF para acciones mutables autenticadas con cookie; validación de origen como defensa complementaria.
- Validación y límites de longitud/rango en servidor, SQL parametrizado, escape contextual al renderizar y límites de carga.
- Roles y propiedad de recurso comprobados en cada endpoint; no confiar en ids o roles recibidos desde el navegador.
- Auditoría append-only lógica para operación, actor, objetivo, fecha y metadatos mínimos; nunca contraseñas, tokens o respuestas completas por defecto.
- Base de datos con permisos de sistema operativo, copias de respaldo y retención definidos antes de uso real. Demo con datos ficticios.
- HTTPS, política de privacidad, consentimiento/aviso de uso y respuesta a incidentes son requisitos para despliegue real, fuera del prototipo local.

## API candidata

`POST /api/auth/login`, `POST /api/auth/logout`, `POST /api/registro/solicitudes`; `GET /api/usuarios`, `POST /api/usuarios`, `PATCH /api/usuarios/{id}`; `GET /api/periodos`, `POST /api/periodos`; `GET /api/evaluaciones`, `POST /api/evaluaciones/{id}/intentos`; `POST /api/intentos/{id}/respuestas`; `POST /api/voluntarios/{id}/calificaciones`; `GET /api/reportes/voluntarios/{id}`. Endpoints ilustrativos, sujetos a la fase de diseño; no están implementados.

## Dependencias y ejecución

Flask y biblioteca estándar `sqlite3` bastan para núcleo. Exportación PDF/Excel requerirá evaluar una biblioteca mantenida (p. ej. ReportLab y openpyxl) en fase de reportes. Fijar versiones en archivo de dependencias, configuración local fuera de Git, migraciones SQLite con historial y comandos documentados cuando se implemente. No añadir framework frontend.

## Límites

SQLite es adecuado para prototipo de concurrencia moderada local; despliegue multiinstancia o alta concurrencia exigiría revisión de arquitectura. No es un sistema clínico ni una plataforma de diagnóstico. La integración IA futura debe ser invocable explícitamente por instructor, auditable, revisable por profesional y nunca decisión automática.
