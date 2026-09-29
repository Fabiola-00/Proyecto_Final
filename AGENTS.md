# Guía del proyecto SICOSE

SICOSE significa **Sistema de Control y Evaluación de Personal**. Es un prototipo académico para seguimiento de personal voluntario de rescate y emergencias, no un producto comercial ni clínico.

## Stack y arquitectura

- Frontend: HTML5, CSS3 y JavaScript puro.
- Backend: Python y Flask; comunicación de interfaz mediante API REST JSON.
- Persistencia: SQLite con consultas parametrizadas, claves foráneas activadas y cambios de esquema aditivos.
- Mantener módulos pequeños y nombres consistentes en español. No agregar frameworks/servicios sin necesidad y autorización.
- Identidad visual: azul `#1F1ABC`, naranja `#FA9648`; usar Evaluar.com solo como referencia general, sin copiar marca o interfaz.

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
