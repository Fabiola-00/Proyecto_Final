"use strict";
{
  const panel = document.querySelector('#recomendacion-panel');
  let turno = 0, contextoSeleccionado = null;
  const nombres = {fisica:'Físico', desempeno:'Desempeño', academica:'Académica', gse_autoeficacia:'GSE · Autoeficacia', mini_extraversion:'Mini-IPIP · Extraversión', mini_amabilidad:'Mini-IPIP · Amabilidad', mini_responsabilidad:'Mini-IPIP · Responsabilidad', mini_neuroticismo:'Mini-IPIP · Neuroticismo', mini_apertura:'Mini-IPIP · Apertura'};
  function limpiar() { ++turno; contextoSeleccionado = null; panel?.replaceChildren(elemento('h2', 'Recomendación'), elemento('p', 'Selecciona un Instructor Voluntario.')); }
  document.querySelector('#modelo-filtro select')?.addEventListener('change', limpiar);
  document.querySelector('#modelo-persona')?.addEventListener('change', limpiar);
  document.addEventListener('sicose:psicometria-gestion', limpiar);
  function tabla(columnas, filas) {
    const wrap=elemento('div',undefined,'tabla-contenedor'), t=elemento('table',undefined,'tabla-registros tabla-compacta'), head=elemento('thead'), tr=elemento('tr'), body=elemento('tbody');
    columnas.forEach(c=>tr.append(elemento('th',c))); head.append(tr); t.append(head,body);
    filas.forEach(f=>{const row=elemento('tr');f.forEach(v=>row.append(elemento('td',String(v))));body.append(row);});wrap.append(t);return wrap;
  }
  async function cargar(pid,uid) {
    if (!panel || !uid) return;
    const actual=++turno; contextoSeleccionado={pid,uid};
    panel.replaceChildren(elemento('h2','Recomendación'),elemento('p','Consultando entradas y versiones…'));
    const base=`/api/modelo-anual/gestiones/${pid}/personas/${uid}/recomendacion`;
    try {
      const d=await apiJson(base);if(actual!==turno)return;
      panel.replaceChildren(elemento('h2','Recomendación'),elemento('p',d.aviso));
      panel.append(tabla(['Entrada','Valor'],Object.entries(d.entradas).map(([k,v])=>[nombres[k]||k,v===null?'Pendiente':Number(v).toFixed(2)])));
      const estado=elemento('p');estado.setAttribute('role','status');
      if(d.faltantes.length)panel.append(elemento('p',`Pendiente: ${d.faltantes.join(' · ')}`));
      if(!d.editable)panel.append(elemento('p','Solo consulta: la Gestión debe estar activa y la cuenta habilitada para generar o confirmar.'));
      const ultima=d.historial[0], vigente=ultima && ultima.estado!=='Desactualizada';
      const generar=elemento('button','Generar recomendación');generar.type='button';generar.disabled=!d.puede_generar || vigente;
      generar.addEventListener('click',async()=>{generar.disabled=true;try{await apiJson(base,{method:'POST',body:{firma_fuentes:d.firma_fuentes,anterior_id:d.ultima_id}});if(actual===turno)await cargar(pid,uid);}catch(e){if(actual===turno){estado.textContent=e.message;generar.disabled=false;}}});
      panel.append(generar,estado);
      if(ultima){
        panel.append(elemento('h3',`Versión ${ultima.id} · ${ultima.estado}`),elemento('p',`Generada: ${ultima.generada_en} · Responsable: ${ultima.generada_por}`),elemento('h4','Salida del modelo'));
        ultima.resultado.sugerencias.forEach(s=>panel.append(elemento('p',s)));
        if(ultima.resultado.estado_modelo==='ABSTENCION')panel.append(elemento('p','El modelo se abstuvo. La revisión humana debe dejar constancia de este resultado indeterminado.'));
        if(ultima.confirmacion){panel.append(elemento('h4','Observación del responsable'),elemento('p',ultima.confirmacion.observacion),elemento('p',`Confirmada por ${ultima.confirmacion.actor_nombre} · ${ultima.confirmacion.confirmada_en}`));}
        else if(ultima.estado==='Propuesta' && d.editable){
          const form=elemento('form',undefined,'formulario-psicometria'),l=elemento('label','Observación del responsable'),nota=elemento('textarea');nota.required=true;nota.maxLength=2000;l.append(nota);
          const aceptar=elemento('label','Confirmo que revisé las entradas y la propuesta, incluido un posible resultado indeterminado.'),check=elemento('input');check.type='checkbox';check.required=true;aceptar.prepend(check);
          const confirmar=elemento('button','Confirmar propuesta para el reporte');form.append(l,aceptar,confirmar);
          form.addEventListener('submit',async e=>{e.preventDefault();confirmar.disabled=true;try{await apiJson(`${base}/${ultima.id}/confirmar`,{method:'POST',body:{firma_fuentes:d.firma_fuentes,observacion:nota.value,confirmar:check.checked}});if(actual===turno)await cargar(pid,uid);}catch(err){if(actual===turno){estado.textContent=err.message;confirmar.disabled=false;}}});panel.append(form);
        }
      }
      const historia=elemento('details');historia.append(elemento('summary','Historial de propuestas y confirmaciones'));
      d.historial.forEach(r=>{const bloque=elemento('details');bloque.append(elemento('summary',`Versión ${r.id} · ${r.estado} · ${r.generada_en}`));
        bloque.append(tabla(['Entrada conservada','Valor'],Object.entries(r.entradas).map(([k,v])=>[nombres[k]||k,v])));
        r.resultado.sugerencias.forEach(s=>bloque.append(elemento('p',s)));
        bloque.append(elemento('p',`Modelo SHA-256: ${r.modelo_sha256}`));
        if(r.confirmacion)bloque.append(elemento('p',`Observación: ${r.confirmacion.observacion}`),elemento('p',`Confirmó: ${r.confirmacion.actor_nombre} · ${r.confirmacion.confirmada_en}`));historia.append(bloque);});panel.append(historia);
    }catch(e){if(actual===turno)panel.replaceChildren(elemento('h2','Recomendación'),elemento('p',e.message));}
  }
  document.addEventListener('sicose:psicometria-persona',e=>cargar(e.detail.pid,e.detail.uid));
}
