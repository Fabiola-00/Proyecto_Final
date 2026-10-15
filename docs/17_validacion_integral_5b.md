# 17. Validación integral y aceptación operativa de Fase 5B

Preparado el **2026-10-14**, para **SQLite v23**. Las entregas 5B.1–5B.4 y la compatibilidad histórica están implementadas técnicamente. Este documento registra la aceptación operativa comunicada explícitamente por el solicitante el 2026-10-14. No es un acta institucional firmada ni declara cerrada globalmente Fase 5B. Los bloques de evidencia anteriores conservan su contexto.

## Evidencia técnica y alcance

Las pruebas usan bases aisladas y datos sintéticos; no cambian estados, notas o publicaciones en la base de trabajo. Los escenarios visuales usan respuestas API simuladas y no sustituyen un ensayo operativo con el servidor real.

| Entrega | Comportamiento técnico cubierto | Revisión humana pendiente |
|---|---|---|
| 5B.1 | Dos físicas comunes, reprogramación individual, No cumplida explícita con cero, pendiente distinto, historial/concurrencia. | Administrador/Jefe revisan fechas, motivos y distinción pendiente/incumplimiento. |
| 5B.2 | Académica anual por finalización individual, suma/tope, pendiente sin cursos, medias exactas y conjunto mitad arriba; configuración histórica intacta. | Comprobar que pantallas y reglas corresponden al procedimiento institucional que se pretende adoptar. |
| 5B.3 | Publicación parcial/republicación, valores y fechas anteriores conservados, ocultación por deshabilitación/retirada, proyección propia sin Desempeño/conjunto. | Ensayo de los tres roles y comprensión de qué datos están publicados. |
| 5B.4 | Cierre/reapertura motivados, incompletos confirmados, instantáneas conservadas, activo único y bloqueo académico en año anterior/nuevo cerrado. | Revisar la responsabilidad de cierre y la consulta de versiones. |
| Históricos | Reapertura excepcional con constancia de ausencia de instantánea; evidencia actual inmutable, sin atribuirla al cierre antiguo ni adoptar reglas/notas. | Administrador valida que el motivo y la evidencia sean suficientes antes de usar la excepción sobre una Gestión concreta. |

Recorrido integral automatizado adicional: Física 1 No cumplida=0, Física 2=80, curso personal=75 y Desempeño 80/90 producen Física=40, Académica=75, Desempeño=85 y conjunto=66,67. La reprogramación conserva el cero. Tras publicar y cerrar, reabrir/corregir curso a 100 produce conjunto=75,00, pero el Instructor conserva 75 académicos hasta republicar. El recierre conserva la primera instantánea y enlaza la nueva. No se revela Desempeño/conjunto al Instructor.

Para repetir únicamente ese recorrido con el entorno existente:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -p test_historicos_5b.py -k recorrido_integral -v
```

Las evidencias exactas de la ejecución completa y migración v23 se registran en HISTORY y al final de este documento. No reutilizar resultados v22 como pruebas nuevas.

## Guía del ensayo humano (referencia)

Usar una base DEMO separada y personas ficticias. Conservar la base local, fotos, `.env` y `.venv`; no resetear ni cargar seed en la base de trabajo. El ensayo no debe usar información real del personal.

1. **Administrador:** crear un borrador anual de prueba, configurar las cinco fuentes y publicar/activar la configuración. Verificar que se congela y que no aparece un segundo período operativo ACTIVO. Activar explícitamente la regla v2 solo para ese año nuevo; verificar que eso no publica notas.
2. **Administrador/Jefe:** habilitar individualmente las fuentes, programar ambas físicas con fechas pasadas válidas dentro del año y registrar una No cumplida explícita con motivo y cero. Dejar otra fuente sin nota para observar Pendiente/No disponible; no debe surgir cero automáticamente.
3. **Administrador/Jefe:** registrar Física 2=80 cumplida; asignar y finalizar un curso con puntaje personal 75 y fecha de ese año. Registrar Jefe=80 y Comandante externo=90, distinguiendo su nombre del autor de transcripción. Resultado esperado: Física=40, Académica=75, Desempeño=85, conjunto=66,67.
4. **Instructor:** antes de publicar, revisar habilitación/estados sin notas. **Jefe:** publicar la versión disponible con motivo. **Instructor:** comprobar físicas/promedio y curso/acumulado publicados, sin Desempeño, conjunto, motivos o datos ajenos. Deshabilitar y rehabilitar una fuente: debe ocultarse y recuperar su última versión publicada, no un valor corregido sin republicar.
5. **Administrador/Jefe:** reprogramar Física 1 de forma extraordinaria. El cero confirmado sigue vigente. Intentar corregir desde una vista anterior: el conflicto debe exigir recargar, sin perder historial.
6. **Jefe:** intentar cerrar/reabrir; debe carecer del permiso. **Administrador:** revisar y cerrar con motivo. También ensayar cierre con incompletos confirmados: los faltantes se identifican sin resultado inventado. Consultar historial y detalle conservado.
7. **Administrador/Jefe:** intentar registrar/corregir nota, fecha física o finalización imputada al año cerrado (incluido moverla de/a ese año); debe rechazarse. **Administrador:** reabrir con motivo, sin otro activo. Corregir el curso de 75 a 100: nuevo conjunto=75,00; Instructor conserva 75 académicos publicados hasta republicar. Volver a cerrar y comprobar ambas instantáneas.
8. **Administrador:** en un histórico DEMO ya cerrado sin instantáneas, revisar la reapertura excepcional. Exigir motivo y casilla de constancia; no debe reconstruir resultado/fecha del cierre antiguo. La evidencia tomada al reabrir sigue accesible tras corregir y volver a cerrar. El primer cierre nuevo es el primero con instantáneas, no una reconstrucción del antiguo. No permite activar una regla distinta tras esa reapertura.
9. **Ambos gestores:** verificar textos, navegación y errores en escritorio/móvil y ambos temas. **Instructor:** comprobar nuevamente que sus notas solo siguen la publicación autorizada. Cuenta INACTIVA sin acceso; reactivación exige nuevo login y conserva historial.

Si surge una discrepancia, registrar caso/rol/pasos/esperado/observado y resolverla antes de aceptar. No registrar credenciales, datos personales reales ni respuestas psicométricas en el acta.

## Registro de aceptación operativa — 2026-10-14

| Campo | Estado actual |
|---|---|
| Versión/revisión revisada | Alcance 5B de esta guía y del informe de servidor real, base técnica vigente v23; revisión Git exacta del ensayo humano no aportada. |
| Fecha y responsables por rol | Declaración recibida el 2026-10-14 del solicitante de este chat. Fecha detallada del ensayo, identidad nominal y participantes por rol no aportados. |
| Casos anteriores ejecutados y evidencia | El solicitante confirma haber realizado el ensayo humano y aceptar operativamente 5B. No se aportó desglose por caso; las pruebas técnicas se conservan como evidencia separada. |
| Incidencias, severidad y resolución | No se comunicaron incidencias en esta confirmación; no se infiere un registro detallado ni su resolución individual. |
| Decisión operativa | **Aceptada por declaración explícita del solicitante: «Ya realicé el ensayo humano y acepto operativamente 5B».** |
| Aprobación institucional de reglas/puntuación y uso | **Pendiente; no inferida de pruebas** |

## Qué continúa pendiente

- Aceptación operativa de 5B registrada por declaración del solicitante. Si se requiere un acta formal, faltan identidad/cargo de participantes, fecha detallada, revisión exacta y desglose de casos/incidencias; no se inventan esos datos.
- Aprobación institucional del procedimiento/reglas y del tratamiento de información antes de un piloto; privacidad, minimización, retención y responsables operativos.
- Preparación del piloto (respaldo/restauración ensayados, HTTPS/WSGI, operación e incidentes), con aceptación separada. La política definitiva de colisiones de códigos pertenece a personal y sigue pendiente fuera del cálculo 5B.

Psicometría/IA/Excel no son entregas nuevas de este cierre técnico. No habilitar reactivos ni inventar validación profesional. Aceptar la interfaz del prototipo no equivale a validar una puntuación institucional.

## Evidencia técnica final de esta ampliación — 2026-10-14

- Ocho pruebas nuevas aprobadas en 20,885 s, incluido el recorrido integral descrito y reapertura sin configuración. Diez de regresión de cierres aprobadas en 24,903 s.
- Suite completa final: **135 pruebas aprobadas en 301,157 s**. La primera pasada completa había detectado dos aserciones antiguas que esperaban v22; se actualizaron a v23 y la suite completa se repitió. Resultados/logs separados en HISTORY.
- Ocho escenarios visuales Chromium con API simulada: ambos gestores, 360/1447 px, claro/oscuro, sin errores/desbordes; capturas inspeccionadas. La evidencia no se presenta como fecha/resultado antiguo y el Jefe no confirma reaperturas.
- Compilación Python, sintaxis de cinco JavaScript, 122 enlaces locales en once documentos y git diff --check correctos; sin nuevo ensayo visual PDF.
- Migración local respaldada en `instance/backups/sicose-20261014-pre-v23-c8c8c9bf.sqlite3`, 43 tablas previas preservadas, dos inicializaciones, v23/quick_check=ok/FK=0 y nueva tabla vacía. No se reabrió ni publicó nada en la base local. Entorno, fotos y datos preservados.

Esta evidencia es técnica. Los campos del acta humana continúan **pendientes**, sin aprobación ficticia de la Fase 5B.

## Ensayo adicional contra servidor real — 2026-10-14

Se ejecutó un recorrido técnico con Flask real y base DEMO aislada, sin simular APIs: **12 comprobaciones funcionales**, 25 peticiones API explícitas además de las de interfaz y **12 escenarios visuales** de los tres roles/ambos temas/360 y 1447 px, sin errores JavaScript ni desbordes observados. Publicación, cierre/reapertura, corrección/republicación, cuentas inactivas e históricos comprobados con sesiones reales. [Informe y límites](18_ensayo_servidor_real_5b.md).

La base de trabajo se conservó y el servidor DEMO final quedó detenido. Esta evidencia es adicional a los escenarios simulados anteriores; **no cambia la decisión operativa No emitida ni completa el acta humana**. No se repitió la suite completa previa de 135 pruebas al no cambiar el producto.


La confirmación operativa anterior sustituye los estados «pendiente/No emitida» de los bloques históricos de este documento. No acredita aprobación institucional ni aceptación de 4A/4B/5A, que conservan sus estados propios.
