"use strict";
{
  const lista = document.querySelector('#gestiones-jefe-lista');
  const mensaje = document.querySelector('#gestiones-jefe-mensaje');
  function campo(form, nombre, titulo, valor, tipo='text') {
    const label=elemento('label',titulo), input=elemento('input'); input.name=nombre;input.type=tipo;input.value=valor;input.required=true;
    if(tipo==='text')input.maxLength=160;label.append(input);form.append(label);return input;
  }
  async function cargarGestiones(){
    const datos=await apiJson('/api/admin/5b/periodos');lista.replaceChildren();
    const periodos=[...(datos.periodos || []),...(datos.retiradas || [])];
    if(!periodos.length)lista.append(elemento('p','Sin gestiones registradas.'));
    periodos.forEach(p=>{
      const panel=elemento('article',undefined,'tarjeta-modulo');panel.append(elemento('h3',p.nombre),elemento('p',`${p.fecha_inicio.slice(0,4)} · ${p.retirada ? 'Retirada' : p.estado}`));
      if(p.modelo_anual){const a=elemento('a','Administrar período y evaluación','boton');a.href=`/gestion/modelo-anual?periodo_id=${p.id}`;panel.append(elemento('p',`${p.fecha_inicio} — ${p.fecha_fin} · Cinco entradas`),a);}
      if(!p.retirada && !p.modelo_anual && p.estado==='ACTIVO'){const b=elemento('button','Revisar y cerrar Gestión','boton-editar');b.type='button';b.addEventListener('click',async()=>{b.disabled=true;try{const v=await apiJson(`/api/5b/periodos/${p.id}/cierre-previo`),f=elemento('form',undefined,'formulario-inline');f.append(elemento('p',`${v.personas.length} personas. Se conservarán las instantáneas y los pendientes identificados.`));campo(f,'motivo','Motivo','');const l=elemento('label','Confirmo los incompletos identificados'),i=elemento('input');i.type='checkbox';i.required=true;l.prepend(i);f.append(l,elemento('button','Confirmar cierre'));f.addEventListener('submit',async e=>{e.preventDefault();try{await apiJson(`/api/admin/5b/periodos/${p.id}/cerrar`,{method:'POST',body:{motivo:f.elements.motivo.value,firma_fuentes:v.firma_fuentes,cierre_anterior_id:v.cierre_anterior_id,confirmar_incompletos:i.checked}});cerrarEdicion();await cargarGestiones();}catch(err){mostrarErrorEdicion(err);}});botonEdicion('Cierre con instantáneas',f,'Revisar').click();}catch(err){mensaje.textContent=err.message;}finally{b.disabled=false;}});panel.append(b);}
      if(!p.retirada){
        if(!p.modelo_anual && p.anual && p.estado==='BORRADOR' && !p.tiene_asignaciones && !p.tiene_notas_5b && p.configuracion?.estado!=='PUBLICADA'){
          const form=elemento('form',undefined,'formulario-inline');campo(form,'nombre','Nombre',p.nombre);campo(form,'ano','Año',p.fecha_inicio.slice(0,4),'number');form.append(elemento('button','Guardar cambios'));
          form.addEventListener('submit',async e=>{e.preventDefault();try{await apiJson(`/api/admin/5b/periodos/${p.id}`,{method:'PATCH',body:{nombre:form.elements.nombre.value,ano:Number(form.elements.ano.value),nombre_anterior:p.nombre,ano_anterior:Number(p.fecha_inicio.slice(0,4))}});cerrarEdicion();await cargarGestiones();}catch(err){mostrarErrorEdicion(err);}});
          panel.append(botonEdicion('Editar gestión',form,'Editar'));
        }
        const baja=elemento('form',undefined,'formulario-inline');baja.append(elemento('p','La baja lógica conserva datos e historial y oculta la gestión de las listas operativas.'));campo(baja,'motivo','Motivo','');baja.append(elemento('button','Eliminar gestión'));
        baja.addEventListener('submit',async e=>{e.preventDefault();try{await apiJson(p.modelo_anual?`/api/modelo-anual/gestiones/${p.id}`:`/api/admin/5b/periodos/${p.id}`,{method:'DELETE',body:p.modelo_anual?{motivo:baja.elements.motivo.value,revision:p.modelo_revision}:{motivo:baja.elements.motivo.value,nombre_anterior:p.nombre,ano_anterior:Number(p.fecha_inicio.slice(0,4)),estado_anterior:p.estado}});cerrarEdicion();await cargarGestiones();}catch(err){mostrarErrorEdicion(err);}});
        panel.append(botonEdicion('Eliminar gestión',baja,'Eliminar'));
      }lista.append(panel);
    });
  }
  if(lista)cargarGestiones().catch(e=>mensaje.textContent=e.message);
  const activacion=document.querySelector('#activacion-evaluaciones-anual');
  if(activacion){
    const filtro=document.querySelector('#gestion-evaluaciones-filtro'),aviso=document.querySelector('#activacion-evaluaciones-mensaje');let revision=0;
    filtro.elements.periodo_id.addEventListener('change',()=>{revision++;activacion.replaceChildren();aviso.textContent='Consulta la gestión seleccionada.';});
    document.querySelector('#tabla-evaluaciones').addEventListener('gestion-consultada',async evento=>{
      const p=evento.detail,turno=++revision;activacion.replaceChildren();aviso.textContent='';
      try{const datos=await apiJson(`/api/5b/gestiones/${p.id}/evaluaciones`);if(turno!==revision)return;
        datos.evaluaciones.forEach(e=>{
          const fila=elemento('article',undefined,'tarjeta-modulo');fila.append(elemento('h3',e.nombre),elemento('p',e.activa?'Activa':'Inactiva'));
          if(!datos.retirada && ['BORRADOR','ACTIVO'].includes(p.estado) && e.disponible){
            const form=elemento('form',undefined,'formulario-inline');campo(form,'motivo','Motivo del cambio','');const boton=elemento('button',e.activa?'Desactivar':'Activar');form.append(boton);
            form.addEventListener('submit',async ev=>{ev.preventDefault();boton.disabled=true;try{await apiJson(`/api/5b/gestiones/${p.id}/evaluaciones/${e.clave}`,{method:'PATCH',body:{activa:!e.activa,revision:e.revision,motivo:form.elements.motivo.value}});filtro.requestSubmit();}catch(err){aviso.textContent=err.message;boton.disabled=false;}});fila.append(form);
          }else fila.append(elemento('p',e.disponible?'Solo consulta.':'Condicionada a aprobación institucional y profesional.'));
          activacion.append(fila);
        });
      }catch(err){if(turno===revision)aviso.textContent=err.message;}
    });
  }
  const seleccion=document.querySelector('#reporte-gestion');
  if(seleccion)Promise.all([apiJson('/api/evaluaciones/gestiones'),apiJson('/api/modelo-anual/gestiones')]).then(([historicos,actuales])=>[...(actuales.periodos||[]).filter(p=>!p.retirada),...(historicos.periodos||[])].forEach(p=>{const o=elemento('option',`${p.nombre} · ${p.estado==='BORRADOR'?'Preparada':p.estado}`);o.value=p.id;seleccion.append(o);})).catch(e=>seleccion.closest('form').querySelector('[role=status]').textContent=e.message);
  document.querySelectorAll('.reporte-central').forEach(form=>form.addEventListener('submit',async evento=>{
    evento.preventDefault();if(!form.reportValidity())return;const mensaje=form.querySelector('[role=status]'),boton=form.querySelector('button');boton.disabled=true;mensaje.textContent='Generando reporte…';const vista=window.open('about:blank','_blank');if(vista)vista.opener=null;
    try{const respuesta=await fetch(`${form.dataset.url}?${new URLSearchParams(new FormData(form))}`,{credentials:'same-origin'});if(!respuesta.ok){const error=await respuesta.json();throw new Error(error.error || 'No se pudo generar el reporte.');}if(!respuesta.headers.get('Content-Type')?.includes('application/pdf'))throw new Error('La sesión no permite descargar este reporte. Vuelve a ingresar.');if(!vista)throw new Error('Permite abrir una pestaña para visualizar el reporte.');const url=URL.createObjectURL(await respuesta.blob());vista.location.replace(url);setTimeout(()=>URL.revokeObjectURL(url),300000);mensaje.textContent='Reporte abierto en otra pestaña.';}catch(e){if(vista)vista.close();mensaje.textContent=e.message;}finally{boton.disabled=false;}
  }));
}
