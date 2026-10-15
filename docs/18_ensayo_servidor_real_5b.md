# 18. Ensayo integral de 5B contra servidor real

Fecha: **2026-10-14**. Esquema **v23**. Ensayo técnico asistido con Chromium contra Flask/Werkzeug real en `127.0.0.1`, con base DEMO temporal aislada y personas ficticias. Sin interceptar HTTP ni simular respuestas API. **No constituye aceptación humana ni institucional y no declara cerrada Fase 5B.**

## Alcance ejecutado

Se utilizaron los tres roles con sesiones separadas y login desde la interfaz. Publicación/republicación, cierre/reapertura y reapertura excepcional se ejecutaron desde los modales reales; las comprobaciones adicionales y algunas correcciones se hicieron con HTTP autenticado real desde el navegador. Las solicitudes mutables válidas usaron el CSRF emitido por el servidor.

| Comprobación | Resultado observado |
|---|---|
| Instructor antes de publicación | Publicación propia ausente, sin notas numéricas publicadas. |
| Cálculo inicial | No cumplida=0, Física 2=80, curso=75 y Desempeño 80/90: Física=40, Desempeño=85 y conjunto=66,67. |
| Reapertura histórica con otro activo | HTTP 409, sin segundo período activo. |
| Permisos por rol | Jefe sin cierre administrativo; Instructor sin historial administrativo de cierres: HTTP 403. |
| Reprogramación individual | Conservó el cero confirmado y el conjunto=66,67. |
| Corrección académica en año cerrado | HTTP 409. |
| Reapertura y corrección | Curso corregido de 75 a 100, conjunto=75,00; Instructor conservó los 75 publicados hasta republicar. |
| Republicación | HTTP 201, Instructor vio 100 académicos, sin Desempeño/conjunto/firma/actor administrativos. |
| Deshabilitar/rehabilitar fuente | Ocultó y restituyó Física 1 de la publicación autorizada. |
| Recierre | Segundo cierre enlazado al primero; detalle del primer cierre idéntico al conservado antes de corregir. |
| Cuenta inactiva/reactivada | Sesión propia rechazada con HTTP 401; reactivar no recuperó la sesión antigua. Nuevo login necesario. |
| Histórico sin instantánea | Reapertura excepcional con motivo/constancia, evidencia NO_RECONSTRUIDO y fecha original no acreditada; posterior primer cierre con instantáneas. |

**12 comprobaciones funcionales satisfactorias**, con **25 peticiones API de comprobación explícitas**, además de las solicitudes reales de la interfaz. No se interpretan estas peticiones como 25 pruebas unitarias ni como un conteo total de tráfico.

## Revisión visual

**12 escenarios**: Administrador, Jefe de Personal e Instructor Voluntario × 360/1447 px × claro/oscuro. Sin errores JavaScript ni desbordes de documento en esos escenarios. Capturas finales con animaciones desactivadas para evitar imágenes durante transiciones; se inspeccionaron capturas de gestores e Instructor. El Instructor mostró únicamente sus notas publicadas y estados permitidos.

No se realizó un nuevo ensayo visual PDF, prueba de carga, despliegue productivo ni validación psicométrica.

## Entorno, datos e integridad

- El aislamiento de ejecución bloqueó inicialmente la conexión local del navegador. Se autorizó ejecutar servidor y navegador en el mismo entorno fuera de ese aislamiento, ambos limitados al DEMO de loopback; no se publicó un servicio externo.
- Se corrigió el cierre de la conexión SQLite del arnés temporal para poder retirar limpiamente la base de ensayo en Windows. No se cambió código del producto.
- Cierre final DEMO: v23, quick_check=ok, FK=0; 3 cierres, 3 instantáneas, 1 reapertura ordinaria, 1 excepcional y 2 publicaciones. Son exclusivamente registros ficticios del ensayo.
- Servidor final detenido y base temporal final retirada. Base de trabajo preservada: se compararon sus tablas anteriores con el respaldo de v22, sin cambios de datos, exceptuando la versión de esquema previamente migrada a v23. Tabla de reaperturas históricas de trabajo sigue vacía; quick_check=ok y FK=0.
- No hubo nueva migración, seed, instalación de dependencias ni cambio de notas/estados/publicaciones en la base de trabajo. `.env`, `.venv`, fotos e historial conservados.

Evidencias ignoradas en `.tmp/ensayo5b/`: `resultado.json`, `base-final.json`, `recorrido.log`, `servidor.log` y capturas por rol/anchura/tema. Los archivos temporales de arranque contienen solo configuración DEMO. La suite previa de **135 pruebas en 301,157 s** es evidencia de la entrega anterior; **no se repitió** porque en este ensayo no cambió el producto.

## Estado de aceptación

Este ensayo aporta evidencia técnica con servidor real, adicional a los escenarios anteriores con API simulada. No sustituye la decisión de los responsables humanos. La [guía y acta de aceptación](17_validacion_integral_5b.md) siguen pendientes de revisión humana, con aprobación institucional del procedimiento y del uso de información por separado.

No se identificaron incidencias funcionales en el alcance recorrido. No se inventan firmas, responsables ni aceptación por haber aprobado automatizaciones. Las entregas técnicas de 5B están implementadas y este recorrido queda verificado; para declarar su aceptación operativa falta el ensayo/revisión de los responsables y su registro real.
Controles finales de este ensayo: compilación Python, sintaxis de los cinco JavaScript, 91 enlaces locales en seis documentos y git diff --check correctos. Comprobación de preservación en `.tmp/ensayo5b/preservacion.json`: 43 tablas anteriores, v23/quick_check=ok/FK=0 y evidencia histórica de trabajo vacía.

## Confirmación posterior del solicitante — 2026-10-14

Tras recibir el informe y la consulta de aceptación, el solicitante declaró haber realizado el ensayo humano y aceptar operativamente 5B. La aceptación operativa queda registrada en docs/17_validacion_integral_5b.md; sustituye su estado pendiente anterior. El ensayo técnico y esa declaración son evidencias distintas. Aprobación institucional y piloto siguen pendientes, sin cierre global de Fase 5B.
