# 05. Plan de desarrollo

**Punto de control actual: Fase 1A implementada y verificada.** La Fase 1 se dividió para respetar el alcance autorizado: esta entrega cubre el esqueleto local Flask/SQLite; autenticación, aprobación de altas, sesiones, CSRF y auditoría funcional quedan para una fase posterior explícitamente aprobada. Cada fase inicia con alcance/archivos; al terminar se realizan verificaciones apropiadas y se reporta su alcance.

| Fase | Objetivo | Entregables tentativos | Condición para avanzar |
|---|---|---|---|
| 0. Especificación | Alinear alcance, seguridad, modelo y candidatos psicométricos | README, AGENTS.md y seis documentos en `docs/` | Aprobación del solicitante y resolución de decisiones críticas |
| 1A. Base ejecutable | Estructura Python/Flask, configuración local, conexión SQLite, esquema técnico mínimo y frontend base | Fábrica Flask, página inicial, endpoint de salud, comando `init-db`, guía Windows y prueba básica | Completa en esta entrega; no contiene cuentas, sesiones ni datos de negocio |
| 1B. Base segura | Autenticación y aprobación de alta, sesiones, roles, CSRF y auditoría funcional | Login, flujo de aprobación y controles de autorización | Requiere autorización de alcance y decisiones de privacidad del proyecto |
| 2. Gestión | Períodos, usuarios, instructores, asignaciones y perfiles | CRUD permitido y bajas lógicas | Verificar autorización, validación e historial |
| 3. Evaluaciones no psicométricas | Calificación física, académica y criterio con historial | Formularios, intentos/registro, avance | Definir faltantes, correcciones y escalas institucionales |
| 4. Instrumentos aprobados | Habilitar solo instrumentos con autorización, versión/idioma y revisión profesional | Pruebas autoadministradas y puntuación documentada | Aprobación de derechos, contenido, validación local y privacidad |
| 5. Reportes | PDF individuales/consolidados y Excel con permisos | Exportación auditada y filtros | Confirmar campos, destinatarios, retención y reglas de promedio |
| 6. Integración IA opcional | Conectar modelo entrenado/validado y flujo de revisión bajo solicitud | Adaptador, versión de modelo, salida revisable | Dataset/model card, validación, revisión ética/profesional y autorización |

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
