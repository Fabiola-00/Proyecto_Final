"use strict";
{
  const lista=document.querySelector('#operaciones-lista');
  if(lista){
    const alta=document.querySelector('#operacion-form'),mensaje=document.querySelector('#operaciones-mensaje');
    const departamentos=['Beni','Chuquisaca','Cochabamba','La Paz','Oruro','Pando','Potosí','Santa Cruz','Tarija'];
    const tipos=['Preventivo','Reactivo','Especial','Emergencia'],estados=['Planificación','En ejecución','Finalizado','Suspendido'];
    const colores={'Planificación':'planificacion','En ejecución':'ejecucion','Finalizado':'finalizado','Suspendido':'suspendido'};
    let personal=[];
    function accion(titulo,panel,tipo,etiqueta){return iconoAccionInstructor(botonEdicion(titulo,panel,etiqueta),tipo,etiqueta);}
    function campo(form,nombre,titulo,valor='',opciones=null,tipo='text'){
      const l=elemento('label',titulo),i=elemento(opciones?'select':'input');i.name=nombre;
      if(opciones){const vacia=elemento('option','Seleccionar');vacia.value='';i.append(vacia);opciones.forEach(v=>{const o=elemento('option',v);o.value=v;i.append(o);});}
      else{i.type=tipo;if(tipo==='text')i.maxLength=160;}
      i.value=valor||'';i.required=nombre!=='fecha_fin';l.append(i);form.append(l);return i;
    }
    function motivo(form){const l=elemento('label','Motivo'),m=elemento('textarea');m.required=true;m.maxLength=2000;l.append(m);form.append(l);return m;}
    function enviar(form,guardar){form.addEventListener('submit',async e=>{e.preventDefault();if(!form.reportValidity())return;const b=form.querySelector('button');b.disabled=true;try{await guardar();cerrarEdicion();await cargar();}catch(err){mostrarErrorEdicion(err);b.disabled=false;}});}
    function ver(o){
      const panel=elemento('div'),datos=elemento('dl',undefined,'datos-perfil');
      [['Tipo de evento',o.tipo_operativo||o.tipo_evento],['Estado',o.estado_operacion||'Sin estado registrado'],['Institución',o.institucion_responsable],['Departamento',o.departamento||'Sin registrar'],['Zona',o.zona||'Sin registrar'],['Inicio',o.fecha_inicio],['Fin',o.fecha_fin||'Sin fecha final'],['Ubicación histórica',o.lugar],['Baja histórica',o.baja?'Sí':'No']].forEach(([k,v])=>datos.append(elemento('dt',k),elemento('dd',v)));
      panel.append(datos,elemento('h3','Participantes'));
      if(!o.participantes.length)panel.append(elemento('p','Sin participantes.'));
      o.participantes.forEach(p=>panel.append(elemento('p',`${p.nombre} · ${p.retirada?'Retirada':'Participación vigente'}${alta?' · '+p.cuenta_estado:''}`)));
      return accion('Detalle de la operación',panel,'ver','Ver operación');
    }
    function editar(o){
      const f=elemento('form',undefined,'formulario-inline');
      campo(f,'tipo_operativo','Tipo de evento',o.tipo_operativo,tipos);campo(f,'estado_operacion','Estado',o.estado_operacion,estados);
      campo(f,'institucion_responsable','Institución',o.institucion_responsable);campo(f,'departamento','Departamento',o.departamento,departamentos);campo(f,'zona','Zona',o.zona);
      campo(f,'fecha_inicio','Inicio',o.fecha_inicio,null,'date');campo(f,'fecha_fin','Fin (opcional)',o.fecha_fin,null,'date');f.append(elemento('button','Guardar cambios'));
      enviar(f,()=>apiJson(`/api/operaciones/${o.id}`,{method:'PATCH',body:{...Object.fromEntries(new FormData(f)),revision:o.revision}}));
      return accion('Editar operación',f,'editar','Editar operación');
    }
    function participantes(o,retirar){
      const f=elemento('form',undefined,'formulario-inline'),grupo=elemento('fieldset',undefined,'campo-ancho');grupo.append(elemento('legend',retirar?'Participantes que se retirarán':'Instructores Voluntarios activos'));
      const candidatos=retirar?o.participantes.filter(p=>!p.retirada):personal.filter(p=>!o.participantes.some(v=>v.voluntario_id===p.id));
      candidatos.forEach(p=>{const l=elemento('label',undefined,'asignacion-participante'),i=elemento('input');i.type='checkbox';i.value=retirar?p.voluntario_id:p.id;i.dataset.revision=p.revision;i.disabled=retirar&&p.cuenta_estado!=='ACTIVO';l.append(i,elemento('span',p.nombre));grupo.append(l);});
      f.append(grupo);if(!candidatos.length)f.append(elemento('p',retirar?'Sin participantes vigentes para retirar.':'Sin personal disponible para asignar.'));
      const m=retirar?motivo(f):null;
      if(retirar)f.append(elemento('p','Se conserva el historial y se retiran los puntos del Académico abierto. Las gestiones cerradas requieren reapertura.'));
      const b=elemento('button',retirar?'Retirar seleccionados':'Asignar seleccionados');b.disabled=true;grupo.addEventListener('change',()=>b.disabled=!grupo.querySelector('input:checked'));f.append(b);
      enviar(f,()=>{const seleccion=[...grupo.querySelectorAll('input:checked')];if(!seleccion.length)throw new Error('Selecciona al menos una persona.');return apiJson(`/api/operaciones/${o.id}/${retirar?'retirar-participantes':'participaciones'}`,{method:'POST',body:retirar?{motivo:m.value,participaciones:seleccion.map(i=>({voluntario_id:Number(i.value),revision:Number(i.dataset.revision)}))}:{voluntario_ids:seleccion.map(i=>Number(i.value))}});});
      return accion(retirar?'Retirar participantes':'Asignar participantes',f,retirar?'retirar':'asignar',retirar?'Retirar participantes':'Asignar participantes');
    }
    function eliminar(o){const f=elemento('form',undefined,'formulario-inline');f.append(elemento('p','Sin vínculos se eliminará permanentemente. Con participantes o notas se conservará como baja histórica.'));const m=motivo(f);f.append(elemento('button','Confirmar eliminación','boton-secundario'));enviar(f,async()=>{const r=await apiJson(`/api/operaciones/${o.id}`,{method:'DELETE',body:{revision:o.revision,motivo:m.value}});mensaje.textContent=r.baja?'Operación dada de baja; historial conservado.':'Operación eliminada.';});return accion('Eliminar operación',f,'desactivar','Eliminar operación');}
    async function cargar(){
      const d=await apiJson('/api/operaciones'+(document.querySelector('#operaciones-incluir-bajas')?.checked?'?incluir_bajas=1':''));lista.replaceChildren();
      const wrap=elemento('div',undefined,'tabla-contenedor'),t=elemento('table',undefined,'tabla-registros tabla-compacta tabla-operaciones'),head=elemento('thead'),fila=elemento('tr'),body=elemento('tbody');
      ['Departamento','Fecha inicio','Fecha fin','Institución','Estado','Acciones'].forEach(v=>{const th=elemento('th',v);th.scope='col';fila.append(th);});head.append(fila);t.append(head,body);wrap.append(t);lista.append(wrap);
      if(!d.operaciones.length){const tr=elemento('tr'),td=elemento('td','Sin operaciones registradas.','tabla-vacia');td.colSpan=6;tr.append(td);body.append(tr);}
      d.operaciones.forEach(o=>{const tr=elemento('tr'),estado=elemento('td'),acciones=elemento('td',undefined,'acciones-operacion');
        [o.departamento||'Sin registrar',o.fecha_inicio,o.fecha_fin||'Sin fecha final',o.institucion_responsable].forEach(v=>tr.append(elemento('td',v)));
        estado.append(elemento('span',o.estado_operacion||'Sin estado registrado',`estado-operacion estado-operacion-${colores[o.estado_operacion]||'historico'}`));if(o.baja)estado.append(elemento('span','Baja histórica','estado-operacion estado-operacion-baja'));
        acciones.append(ver(o));if(alta&&!o.baja)acciones.append(editar(o),participantes(o,false),participantes(o,true),eliminar(o));tr.append(estado,acciones);body.append(tr);
      });
    }
    document.querySelector('#operaciones-incluir-bajas')?.addEventListener('change',()=>cargar().catch(e=>mensaje.textContent=e.message));
    if(alta){alta.querySelector('#operacion-cancelar').addEventListener('click',()=>alta.reset());alta.addEventListener('submit',async e=>{e.preventDefault();if(!alta.reportValidity())return;const b=alta.querySelector('button');b.disabled=true;try{const body=Object.fromEntries(new FormData(alta));delete body.id;await apiJson('/api/operaciones',{method:'POST',body});alta.reset();document.querySelector('#registro-operacion').open=false;mensaje.textContent='Operación registrada.';await cargar();}catch(err){mensaje.textContent=err.message;}finally{b.disabled=false;}});}
    (async()=>{if(alta){const d=await apiJson('/api/instructores-voluntarios');personal=d.voluntarios.filter(p=>p.estado==='ACTIVO');}await cargar();})().catch(e=>mensaje.textContent=e.message);
  }
}
