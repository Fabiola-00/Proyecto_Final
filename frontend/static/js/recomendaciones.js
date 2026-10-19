"use strict";
{
  const panel = document.querySelector('#recomendacion-panel');
  let turno = 0, contextoSeleccionado = null;
  const nombres = {fisica:'Físico', desempeno:'Desempeño', academica:'Académica', gse_autoeficacia:'GSE · Autoeficacia', mini_extraversion:'Mini-IPIP · Extraversión', mini_amabilidad:'Mini-IPIP · Amabilidad', mini_responsabilidad:'Mini-IPIP · Responsabilidad', mini_neuroticismo:'Mini-IPIP · Neuroticismo', mini_apertura:'Mini-IPIP · Apertura',tlx_demanda_mental:'NASA-TLX · Demanda mental',tlx_demanda_fisica:'NASA-TLX · Demanda física',tlx_demanda_temporal:'NASA-TLX · Demanda temporal',tlx_rendimiento:'NASA-TLX · Rendimiento (alto = malo)',tlx_esfuerzo:'NASA-TLX · Esfuerzo',tlx_frustracion:'NASA-TLX · Frustración'};
  function limpiar() { ++turno; contextoSeleccionado = null; panel?.replaceChildren(elemento('h2', 'Recomendación'), elemento('p', 'Selecciona un Instructor Voluntario.')); }
  document.querySelector('#modelo-filtro select')?.addEventListener('change', limpiar);
  document.querySelector('#modelo-persona')?.addEventListener('change', limpiar);
  document.addEventListener('sicose:psicometria-gestion', limpiar);
  function tabla(columnas, filas) {
    const wrap=elemento('div',undefined,'tabla-contenedor'), t=elemento('table',undefined,'tabla-registros tabla-compacta'), head=elemento('thead'), tr=elemento('tr'), body=elemento('tbody');
    columnas.forEach(c=>tr.append(elemento('th',c))); head.append(tr); t.append(head,body);
    filas.forEach(f=>{const row=elemento('tr');f.forEach(v=>row.append(elemento('td',String(v))));body.append(row);});wrap.append(t);return wrap;
  }
  function graficosDimensiones(entradas, grupos) {
    const detalles=elemento('details',undefined,'recomendacion-graficos recomendacion-detalle');
    detalles.append(elemento('summary','Ver gráficos de las dimensiones'));
    let preparado=false;
    detalles.addEventListener('toggle',()=>{
      if(!detalles.open || preparado)return;
      preparado=true;
      const control=elemento('label','Visualización', 'dimensiones-selector'), selector=elemento('select');
      selector.setAttribute('aria-label','Visualización de las dimensiones');
      [['barras','Barras horizontales'],['radar','Diagrama de araña']].forEach(([v,n])=>{
        const opcion=elemento('option',n);opcion.value=v;selector.append(opcion);
      });control.append(selector);
      const contenido=elemento('div',undefined,'dimensiones-grupos');
      detalles.append(elemento('p','Puntuaciones conservadas en esta versión. La longitud de las barras y los ejes de araña representan la posición dentro del rango teórico: (valor − mínimo) / (máximo − mínimo) × 100. No son percentiles ni porcentajes de aptitud.','recomendacion-nota'),control,contenido);
      const dibujar=()=>{
        contenido.dataset.vista=selector.value;
        contenido.replaceChildren();
        grupos.forEach(([nombre,dimensiones,minimo,maximo,nota],indice)=>{
          const datos=dimensiones.filter(([k])=>typeof entradas[k]==='number' && Number.isFinite(entradas[k])).map(([k,n])=>({nombre:n,valor:entradas[k],posicion:Math.max(0,Math.min(100,(entradas[k]-minimo)/(maximo-minimo)*100))}));
          if(!datos.length)return;
          const grupo=elemento('section',undefined,`dimensiones-grupo dimensiones-color-${indice}`);
          grupo.append(elemento('h5',nombre),elemento('p',`Rango original: ${minimo}–${maximo}. ${nota}`,'recomendacion-nota'));
          if(selector.value==='radar' && datos.length>=3) {
            const svg=(tag,atributos={})=>{const nodo=document.createElementNS('http://www.w3.org/2000/svg',tag);Object.entries(atributos).forEach(([k,v])=>nodo.setAttribute(k,String(v)));return nodo;};
            const dibujo=svg('svg',{viewBox:'0 0 360 300',role:'img','aria-label':`${nombre}. ${datos.map(d=>`${d.nombre}: ${d.valor}, rango ${minimo} a ${maximo}`).join('. ')}. Ejes normalizados de 0 a 100.`});
            const punto=(i,p)=>{const angulo=-Math.PI/2+2*Math.PI*i/datos.length;return [180+105*p*Math.cos(angulo),150+105*p*Math.sin(angulo)];};
            const puntos=p=>datos.map((_,i)=>punto(i,p).join(',')).join(' ');
            [.25,.5,.75,1].forEach(p=>{
              dibujo.append(svg('polygon',{points:puntos(p),class:'dimensiones-rejilla'}));
              const texto=svg('text',{x:186,y:150-105*p-3,class:'dimensiones-escala'});texto.textContent=String(p*100);dibujo.append(texto);
            });
            datos.forEach((d,i)=>{
              const [x,y]=punto(i,1),[tx,ty]=punto(i,1.2);
              dibujo.append(svg('line',{x1:180,y1:150,x2:x,y2:y,class:'dimensiones-rejilla'}));
              const texto=svg('text',{x:tx,y:ty,'text-anchor':'middle','dominant-baseline':'middle',class:'dimensiones-eje'});texto.textContent=String(i+1);dibujo.append(texto);
            });
            dibujo.append(svg('polygon',{points:datos.map((d,i)=>punto(i,d.posicion/100).join(',')).join(' '),class:'dimensiones-perfil'}));
            datos.forEach((d,i)=>{const [x,y]=punto(i,d.posicion/100);dibujo.append(svg('circle',{cx:x,cy:y,r:3.5,class:'dimensiones-punto'}));});
            const leyenda=elemento('ol',undefined,'dimensiones-leyenda');datos.forEach(d=>leyenda.append(elemento('li',`${d.nombre}: ${d.valor.toFixed(2)} (${minimo}–${maximo})`)));
            const figura=elemento('figure',undefined,'dimensiones-radar');figura.append(dibujo,elemento('figcaption','Ejes 1–'+datos.length+' · posición en el rango, de 0 a 100.'));grupo.append(figura,leyenda);
          } else {
            if(selector.value==='radar')grupo.append(elemento('p','GSE tiene una sola dimensión; se conserva la barra horizontal.','recomendacion-nota'));
            const lista=elemento('ul',undefined,'dimensiones-barras');
            datos.forEach(d=>{
              const fila=elemento('li'),cabecera=elemento('div',undefined,'dimensiones-barra-cabecera');
              cabecera.append(elemento('span',d.nombre),elemento('strong',`${d.valor.toFixed(2)} · ${minimo}–${maximo}`));
              const pista=elemento('div',undefined,'dimensiones-barra-pista'),relleno=elemento('span',undefined,'dimensiones-barra-relleno');pista.setAttribute('aria-hidden','true');relleno.style.width=`${d.posicion}%`;pista.append(relleno);fila.append(cabecera,pista);lista.append(fila);
            });grupo.append(lista);
          }
          contenido.append(grupo);
        });
      };
      selector.addEventListener('change',dibujar);dibujar();
    });
    return detalles;
  }
  function explicarVersion(r) {
    const bloque=elemento('section',undefined,'recomendacion-explicacion'), entradas=r.entradas;
    const puntaje=k=>Number(entradas[k]).toFixed(2);
    const orientaciones={
      preparacion_progresiva_y_confianza:'Se propone avanzar con prácticas paso a paso y metas alcanzables. El acompañamiento y el reconocimiento de los logros pueden ayudar a ganar confianza y fortalecer la preparación.',
      organizacion_de_tareas_y_manejo_de_carga:'Se propone organizar mejor las prioridades y repartir las tareas con claridad. Acordar un ritmo de trabajo y los apoyos disponibles puede ayudar a afrontar las actividades de una manera más llevadera.',
      comunicacion_y_aprendizaje_acompanado:'Se propone aprender con acompañamiento y reforzar la comunicación en el equipo. Practicar juntos, compartir dudas y recibir comentarios claros puede facilitar el aprendizaje y la coordinación.',
      afrontamiento_y_seguimiento_del_bienestar:'Se propone ofrecer un espacio voluntario de escucha para conversar sobre cómo se vivieron las actividades. A partir de esa conversación, se pueden acordar apoyos y formas de afrontar las exigencias cuidando el bienestar.',
      preparacion_y_confianza:'Se propone avanzar con prácticas graduales y metas alcanzables, reconociendo los logros para fortalecer la preparación y la confianza.',
      comunicacion_y_colaboracion:'Se propone practicar la comunicación y la coordinación en equipo, con responsabilidades claras y comentarios que ayuden a mejorar.',
      aprendizaje_y_autonomia:'Se propone aprender mediante actividades prácticas y objetivos claros, con acompañamiento al inicio y más independencia a medida que se gana experiencia.',
      afrontamiento_y_metas:'Se propone ofrecer una conversación voluntaria sobre las exigencias y las metas personales, para acordar apoyos y próximos pasos que resulten llevaderos.'
    };
    const prioritaria=r.resultado.criterio_seleccion==='ARGMAX_V1';
    const claves=prioritaria?[r.resultado.salida_prioritaria]:Object.entries(r.resultado.activaciones||{}).filter(([,v])=>v>=(r.resultado.umbrales?.[1]??.65)).map(([k])=>k);
    const textos=claves.map(k=>orientaciones[k]).filter(Boolean);
    let lectura;
    if(r.resultado.estado_modelo==='ABSTENCION')lectura='En esta versión no se pudo definir una orientación concreta. El responsable puede conversar con el Instructor y revisar su situación antes de acordar los próximos pasos.';
    else if(textos.length===1)lectura=textos[0];
    else if(textos.length>1)lectura='Esta versión propone combinar las líneas de apoyo indicadas arriba. El responsable puede conversar con el Instructor para elegir por dónde empezar y acordar pasos sencillos, según sus necesidades y metas.';
    else lectura='Se propone mantener el acompañamiento y ofrecer oportunidades para seguir aprendiendo. Conversar con el Instructor puede ayudar a reconocer sus avances y acordar los apoyos que le resulten útiles.';
    const interpretacion=elemento('div',undefined,'recomendacion-interpretacion');
    interpretacion.append(elemento('h4','Interpretación de la recomendación'),elemento('p',lectura));
    if(prioritaria)interpretacion.append(elemento('p','Es un punto de partida para conversar y acordar los próximos pasos con el Instructor y el responsable.'));
    bloque.append(interpretacion);
    const dimensionesMini=[
      ['mini_extraversion','Extraversión','Una puntuación mayor expresa mayor sociabilidad y participación social declaradas.'],
      ['mini_amabilidad','Amabilidad','Una puntuación mayor expresa mayor atención y sensibilidad declaradas hacia otras personas.'],
      ['mini_responsabilidad','Responsabilidad','Una puntuación mayor expresa mayor orden y cumplimiento de tareas declarados.'],
      ['mini_neuroticismo','Neuroticismo','Una puntuación mayor expresa mayor tendencia declarada a emociones desagradables y cambios de ánimo; no es un diagnóstico.'],
      ['mini_apertura','Apertura / intelecto','Una puntuación mayor expresa mayor interés declarado por ideas e imaginación.']
    ];
    const dimensionesTlx=[
      ['tlx_demanda_mental','Demanda mental','Actividad mental y perceptiva que exigió la tarea.'],
      ['tlx_demanda_fisica','Demanda física','Actividad física que exigió la tarea.'],
      ['tlx_demanda_temporal','Demanda temporal','Presión de tiempo percibida durante la tarea.'],
      ['tlx_rendimiento','Rendimiento percibido','0 indica buen rendimiento y 100 mal rendimiento percibido; no es la nota institucional.'],
      ['tlx_esfuerzo','Esfuerzo','Esfuerzo mental y físico necesario para lograr el rendimiento.'],
      ['tlx_frustracion','Frustración','Inseguridad, irritación o frustración percibidas durante la tarea.']
    ].filter(([k])=>Object.hasOwn(entradas,k));
    const detalles=elemento('details',undefined,'recomendacion-detalle');
    detalles.append(elemento('summary','Consultar el significado de cada dimensión'),tabla(['Dimensión','Puntuación conservada','Qué expresa'],[
      ...dimensionesMini.map(([k,n,t])=>[`Mini-IPIP · ${n}`,`${puntaje(k)} · rango 4–20`,t]),
      ...dimensionesTlx.map(([k,n,t])=>[`NASA-TLX · ${n}`,`${puntaje(k)} · rango 0–100`,t])
    ]));
    bloque.append(detalles,graficosDimensiones(entradas,[
      ['Evaluación institucional',[['fisica','Físico'],['desempeno','Desempeño'],['academica','Académica']],0,100,'Calificaciones institucionales.'],
      ['GSE · Autoeficacia',[['gse_autoeficacia','Autoeficacia general']],10,40,'Una dimensión de confianza declarada.'],
      ['Mini-IPIP · Personalidad',dimensionesMini,4,20,'Rasgos independientes, sin nota global ni perfil ideal.'],
      ['NASA-TLX · Carga de trabajo',dimensionesTlx,0,100,'Mayor valor: mayor demanda, esfuerzo o frustración. Rendimiento: 0 bueno, 100 malo; no se invierte el eje.']
    ]));
    return bloque;
  }
  async function cargar(pid,uid) {
    if (!panel || !uid) return;
    const actual=++turno; contextoSeleccionado={pid,uid};
    panel.replaceChildren(elemento('h2','Recomendación'),elemento('p','Consultando entradas y versiones…'));
    const base=`/api/modelo-anual/gestiones/${pid}/personas/${uid}/recomendacion`;
    try {
      const d=await apiJson(base);if(actual!==turno)return;
      panel.replaceChildren();
      const institucionales = ['fisica','desempeno','academica'];
      const psicometricas = ['gse_autoeficacia','mini_extraversion','mini_amabilidad','mini_responsabilidad','mini_neuroticismo','mini_apertura',...['tlx_demanda_mental','tlx_demanda_fisica','tlx_demanda_temporal','tlx_rendimiento','tlx_esfuerzo','tlx_frustracion'].filter(k=>k in d.entradas)];
      const valores = claves => claves.map(k=>[nombres[k]||k,d.entradas[k]===null?'Pendiente':Number(d.entradas[k]).toFixed(2)]);
      panel.append(elemento('h2','Evaluación Institucional · Entrada de consulta'), tabla(['Componente','Nota / 100'],valores(institucionales)));
      const enlace = elemento('a','Registrar o corregir notas en Evaluaciones'); enlace.href=`/gestion/modelo-anual?periodo_id=${encodeURIComponent(pid)}&persona_id=${encodeURIComponent(uid)}`;enlace.dataset.contextoEvaluacion='';panel.append(enlace);
      panel.append(elemento('h2','Pruebas Psicométricas · Entradas del Modelo'),tabla(['Dimensión','Puntuación','Rango'],valores(psicometricas).map((fila,i)=>[...fila,i===0?'10–40':i<6?'4–20':'0–100'])));
      panel.append(elemento('p',d.aviso,'recomendacion-nota'),elemento('p',`Modelo: ${d.modelo.arquitectura.join(' → ')} · ${Object.keys(d.entradas).length} entradas · Revisión humana obligatoria.`,'recomendacion-nota'));
      if(d.modelo.criterio_seleccion==='ARGMAX_V1')panel.append(elemento('p','Las nuevas propuestas seleccionan una sola línea de orientación prioritaria mediante la mayor activación.','recomendacion-nota'));
      const estado=elemento('p');estado.setAttribute('role','status');
      if(d.faltantes.length)panel.append(elemento('p',`Pendiente: ${d.faltantes.join(' · ')}`));
      if(!d.editable)panel.append(elemento('p','Solo consulta: la Gestión debe estar activa y la cuenta habilitada para generar o confirmar.'));
      const ultima=d.historial[0], vigente=ultima && ultima.estado!=='Desactualizada';
      const generar=elemento('button','Generar recomendación');generar.type='button';generar.disabled=!d.puede_generar || vigente;
      generar.addEventListener('click',async()=>{generar.disabled=true;try{await apiJson(base,{method:'POST',body:{firma_fuentes:d.firma_fuentes,anterior_id:d.ultima_id}});if(actual===turno)await cargar(pid,uid);}catch(e){if(actual===turno){estado.textContent=e.message;generar.disabled=false;}}});
      const acciones=elemento('div',undefined,'recomendacion-acciones');acciones.append(generar,estado);panel.append(acciones);
      if(ultima){
        panel.append(elemento('h3',`Versión ${ultima.id} · ${ultima.estado}`,'recomendacion-version'),elemento('p',`Generada: ${ultima.generada_en} · Responsable: ${ultima.generada_por}`,'recomendacion-metadatos'));
        const salida=elemento('section',undefined,'recomendacion-salida'),cuadro=elemento('div',undefined,'recomendacion-salida-cuadro');cuadro.append(elemento('h4',ultima.resultado.criterio_seleccion==='ARGMAX_V1'?'Recomendación (Salida del Modelo)':'Salida del modelo'));
        ultima.resultado.sugerencias.forEach(s=>cuadro.append(elemento('p',s,'recomendacion-texto')));salida.append(cuadro);
        if(ultima.estado==='Desactualizada')salida.append(elemento('p','Esta versión está desactualizada. La explicación corresponde a sus puntuaciones originales; genera otra propuesta con las entradas vigentes.','recomendacion-nota'));
        salida.append(explicarVersion(ultima));panel.append(salida);
        if(ultima.confirmacion){panel.append(elemento('h4','Observaciones del responsable'),elemento('p',ultima.confirmacion.observacion),elemento('p',`Confirmada por ${ultima.confirmacion.actor_nombre} · ${ultima.confirmacion.confirmada_en}`));}
        else if(ultima.estado==='Propuesta' && d.editable){
          const form=elemento('form',undefined,'formulario-psicometria'),l=elemento('label','Observaciones del responsable'),nota=elemento('textarea');nota.required=true;nota.maxLength=2000;l.append(nota);
          const aceptar=elemento('label',ultima.resultado.criterio_seleccion==='ARGMAX_V1'?'Confirmo que revisé las entradas y la línea de orientación prioritaria, considerando el contexto y las limitaciones del modelo.':'Confirmo que revisé las entradas y la propuesta, incluido un posible resultado indeterminado.'),check=elemento('input');check.type='checkbox';check.required=true;aceptar.prepend(check);
          const confirmar=elemento('button','Confirmar propuesta para el reporte');form.append(l,aceptar,confirmar);
          form.addEventListener('submit',async e=>{e.preventDefault();if(actual!==turno || !window.confirm('¿Estás seguro de confirmar esta propuesta para el reporte individual? Se conservarán la salida del modelo y tus observaciones como constancia de la revisión.'))return;confirmar.disabled=true;try{await apiJson(`${base}/${ultima.id}/confirmar`,{method:'POST',body:{firma_fuentes:d.firma_fuentes,observacion:nota.value,confirmar:check.checked}});if(actual===turno)await cargar(pid,uid);}catch(err){if(actual===turno){estado.textContent=err.message;confirmar.disabled=false;}}});panel.append(form);
        }
      }
      const historia=elemento('details');historia.append(elemento('summary','Historial de propuestas y confirmaciones'));
      d.historial.forEach(r=>{const bloque=elemento('details');bloque.append(elemento('summary',`Versión ${r.id} · ${r.estado} · ${r.generada_en}`));
        bloque.append(tabla(['Entrada conservada','Valor'],Object.entries(r.entradas).map(([k,v])=>[nombres[k]||k,v])));
        r.resultado.sugerencias.forEach(s=>bloque.append(elemento('p',s)));
        bloque.append(explicarVersion(r));
        bloque.append(elemento('p',`Modelo SHA-256: ${r.modelo_sha256}`));
        if(r.confirmacion)bloque.append(elemento('p',`Observación: ${r.confirmacion.observacion}`),elemento('p',`Confirmó: ${r.confirmacion.actor_nombre} · ${r.confirmacion.confirmada_en}`));historia.append(bloque);});panel.append(historia);
    }catch(e){if(actual===turno)panel.replaceChildren(elemento('h2','Recomendación'),elemento('p',e.message));}
  }
  document.addEventListener('sicose:psicometria-persona',e=>cargar(e.detail.pid,e.detail.uid));
}
