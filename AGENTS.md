# Guía del proyecto SICOSE

* Mantener el stack acordado: Flask, SQLite, HTML, CSS y JavaScript puro; no agregar frameworks ni servicios externos sin justificación y aprobación.
* Usar español en interfaz, documentación, mensajes y nombres de dominio cuando resulte claro y consistente.
* Antes de cada fase, describir objetivo y archivos afectados. Trabajar en cambios pequeños, conservar historial y no borrar datos históricos.
* Backend como frontera de seguridad: autorización por rol y recurso, validación en servidor, consultas parametrizadas, contraseñas con hash moderno, sesiones protegidas, CSRF donde corresponda y auditoría de operaciones sensibles.
* Nunca incluir secretos, credenciales, claves de prueba, datos personales o la base SQLite en el frontend o control de versiones. Usar únicamente datos ficticios para demos.
* No exponer ni habilitar instrumentos psicométricos sin confirmar permisos, versión lingüística, reglas oficiales de puntuación y revisión profesional. No inventar reactivos ni interpretaciones.
* Los resultados psicométricos son confidenciales. Evitar registros y reportes que expongan respuestas cuando no sean necesarios.
* La IA permanece como interfaz desacoplada sin modelo, predicciones ni sustitutos basados en reglas. No presentar resultados de IA hasta que exista modelo validado y revisión autorizada.
* No afirmar una función como terminada sin verificación apropiada y registrar exactamente qué se verificó.
* Al editar documentación, conservar las decisiones y limitaciones abiertas hasta que una decisión institucional las cierre explícitamente.



\# Instrucciones permanentes del proyecto SICOPE



\## Contexto

SICOPE es un sistema académico de control y evaluación de personal voluntario de rescate y emergencias. El objetivo es un prototipo funcional, no un producto comercial de producción.



\## Stack

\- Frontend: HTML5, CSS3 y JavaScript puro.

\- Backend: Python y Flask.

\- Base de datos: SQLite.

\- Comunicación: API REST con JSON.

\- IA futura: módulo Python desacoplado; no simular un modelo entrenado.



\## Diseño

\- Azul institucional: #1F1ABC.

\- Naranja institucional: #FA9648.

\- Interfaz responsiva y accesible, con navegación clara por rol.

\- Referencia visual: https://www.evaluar.com, sin copiar su identidad o diseño exacto.



\## Roles y permisos

\- Administrador: gestión global de usuarios, instructores, voluntarios, catálogos, ponderaciones, evaluaciones, períodos y reportes.

\- Instructor: gestión de voluntarios, asignaciones, activación/desactivación/reinicio de pruebas psicométricas y calificaciones de las tres evaluaciones a su cargo.

\- Voluntario: completar pruebas habilitadas y consultar únicamente sus propios resultados e informes.

\- Verificar autorización en el backend en cada endpoint protegido; ocultar elementos de interfaz no es control de seguridad.

\- El instructor puede desactivar, pero no eliminar físicamente, voluntarios.



\## Evaluaciones

Seis componentes: tres psicométricos completados por voluntarios; evaluación física, rendimiento académico y criterio de instructor completados por instructores. Escala inicial de 0 a 100 y pesos configurables 10/10/10/25/15/30, suma 100%, pendientes de validación institucional. Versionar los pesos por período.



\## Historial e integridad

\- Cada reinicio genera un nuevo intento.

\- No sobrescribir ni eliminar resultados históricos.

\- Usar transacciones y claves foráneas.

\- Registrar acciones sensibles en auditoría.



\## Seguridad y privacidad

\- Contraseñas almacenadas con hash seguro.

\- Secretos solo en variables de entorno, nunca en el repositorio.

\- No exponer SQLite ni credenciales al navegador.

\- Validar y sanear entradas, usar consultas parametrizadas y protección CSRF según corresponda.

\- Usar datos ficticios en desarrollo y demostraciones.

\- Restringir resultados psicométricos a voluntario propietario, instructores autorizados y administrador.



\## IA responsable

\- No inventar predicciones ni presentar reglas simples como red neuronal entrenada.

\- El modelo aún no existe; diseñar una interfaz modular para su futura integración.

\- Generar análisis solo bajo solicitud del instructor.

\- Mostrar limitaciones y permitir revisión profesional. No usar predicciones como diagnóstico psicológico ni como decisión automática de permanencia.



\## Desarrollo

\- Trabajar en fases pequeñas y revisar los archivos existentes antes de cambiarlos.

\- No hacer cambios destructivos sin autorización.

\- Escribir código legible y documentar decisiones relevantes.

\- Añadir o actualizar pruebas para funcionalidades y permisos.

\- Ejecutar pruebas tras los cambios e informar claramente qué se probó y qué quedó pendiente.

\- Si falta una decisión que afecte seguridad, datos, puntuación o validez psicométrica, preguntar antes de asumir.

