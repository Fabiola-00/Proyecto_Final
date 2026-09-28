# 05. Plan de desarrollo

**Punto de control actual: Fase 3 implementada; pendiente de revisión del solicitante.** Cada fase inicia con alcance/archivos; al terminar se realizan verificaciones apropiadas y se reporta su alcance.

| Fase | Objetivo | Entregables tentativos | Condición para avanzar |
|---|---|---|---|
| 0. Especificación | Alinear alcance, seguridad, modelo y candidatos psicométricos | README, AGENTS.md y seis documentos en `docs/` | Aprobación del solicitante y resolución de decisiones críticas |
| 1A. Base ejecutable | Estructura Python/Flask, configuración local, SQLite y frontend base | Fábrica Flask, endpoint de salud, comando inicial y prueba básica | Completada |
| 2. Modelo y autenticación | Tablas base, roles, login/logout, autorización, seed admin y auditoría auth | Esquema SQLite ampliado, login con CSRF, APIs auth, seed idempotente y pruebas | Completada; gestión de usuarios y aprobación de altas siguen pendientes |
| 3. Diseño visual y dashboards | Plantilla compartida, navegación, indicadores y páginas iniciales por rol | Dashboard inicial protegido para administrador, instructor y voluntario | Implementada en esta entrega; los contadores usan datos existentes |
| 4. Gestión | Períodos, usuarios, instructores, asignaciones y perfiles | CRUD permitido y bajas lógicas | Verificar autorización, validación e historial |
| 5. Evaluaciones no psicométricas | Calificación física, académica y criterio con historial | Formularios, intentos/registro, avance | Definir faltantes, correcciones y escalas institucionales |
| 6. Instrumentos aprobados | Habilitar solo instrumentos con autorización, versión/idioma y revisión profesional | Pruebas autoadministradas y puntuación documentada | Aprobación de derechos, contenido, validación local y privacidad |
| 7. Reportes | PDF individuales/consolidados y Excel con permisos | Exportación auditada y filtros | Confirmar campos, destinatarios, retención y reglas de promedio |
| 8. Integración IA opcional | Conectar modelo entrenado/validado y flujo de revisión bajo solicitud | Adaptador, versión de modelo, salida revisable | Dataset/model card, validación, revisión ética/profesional y autorización |

## Riesgos principales

- Daño por interpretación o uso laboral de puntuaciones psicométricas fuera de propósito y población estudiados.
- Acceso indebido a información sensible, en especial por autorización incompleta o reportes amplios.
- Incompatibilidad legal o cultural de instrumentos/ítems y ausencia de validación en Bolivia o en voluntarios de rescate.
- Diferencias entre pesos configurados, reglas de faltantes e informes que alteren decisiones de seguimiento.
- Retención indefinida de historiales y datos sensibles sin política institucional.
- Exposición de datos demo que accidentalmente sean datos reales; usar registros sintéticos.
- Alcance excesivo para un prototipo; implementar por entregas pequeñas y aprobar decisiones institucionales.

## Preguntas de decisión previas a programación

1. ¿Qué institución, país y marco normativo de privacidad rigen el piloto, y quién será responsable de datos?
2. ¿Cómo se aprueban voluntarios: invitación, aprobación administrativa, validación de identidad, consentimiento/aviso y plazo de respuesta?
3. ¿Qué datos identificatorios son imprescindibles, quién puede exportarlos y cuánto tiempo se conservarán evaluaciones, respuestas y auditoría?
4. ¿Qué regla se aplicará a evaluaciones incompletas: no calcular promedio hasta completar seis, promedio proporcional o estado especial? ¿Qué regla de redondeo?
5. ¿Los pesos iniciales son solo demostrativos? ¿Quién puede aprobarlos y cerrar una versión por período?
6. ¿Qué población y modalidad corresponden a cada prueba? ¿Existe psicólogo/especialista autorizado para selección, revisión y eventual adaptación local?
7. ¿Debe existir un usuario administrador semilla para demo? Se propone cargarlo solo mediante comando local y secreto configurado fuera del repositorio.
8. ¿Los PDF consolidados se dirigen exclusivamente a administradores/instructores? ¿Qué campos deben excluirse?
9. ¿Despliegue local de demostración o servidor institucional? ¿Hay requisitos de HTTPS, respaldo y disponibilidad?

## Decisiones asumidas para esta propuesta

Se asume prototipo local, español, usuarios adultos, datos sintéticos, SQLite, mismo origen para web/API, borrado lógico, pesos versionados y que las notas de instrumentos no se convierten automáticamente a la escala institucional hasta definir transformación. La hipótesis de seis notas completas para promedio no se ha aprobado; el comportamiento por defecto en prototipo debe mostrar promedio no disponible cuando falte cualquiera.
