"use strict";
{
  const filtro = document.querySelector('#modelo-filtro'), personas = document.querySelector('#modelo-persona');
  const ciclo = document.querySelector('#modelo-ciclo'), mensaje = document.querySelector('#modelo-mensaje');
  let turno = 0;
  function seleccionarPersona() {
    actualizarContextoEvaluacion(filtro.elements.periodo.value, personas.value);
    document.dispatchEvent(new CustomEvent('sicose:psicometria-persona', {detail:{pid:filtro.elements.periodo.value, uid:personas.value}}));
  }
  async function cargar() {
    const pid = filtro.elements.periodo.value;
    if (!pid) return;
    const actual = ++turno, previa = personas.value || new URLSearchParams(location.search).get('persona_id');
    mensaje.textContent = '';
    const d = await apiJson(`/api/modelo-anual/gestiones/${pid}`);
    if (actual !== turno || pid !== filtro.elements.periodo.value) return;
    const p = d.periodo;
    ciclo.replaceChildren(elemento('h2',p.nombre),elemento('p',`${p.fecha_inicio} — ${p.fecha_fin} · ${p.retirada?'Retirada · solo consulta':p.estado==='BORRADOR'?'Preparada':p.estado}`));
    personas.replaceChildren(elemento('option','Seleccionar persona')); personas.options[0].value = '';
    d.personas.forEach(p => {const o = elemento('option',`${p.nombre} · ${p.estado}`);o.value=p.id;personas.append(o);});
    if ([...personas.options].some(o => o.value === previa)) personas.value = previa;
    actualizarContextoEvaluacion(pid,personas.value);
    document.dispatchEvent(new CustomEvent('sicose:psicometria-gestion',{detail:{pid,editable:!p.retirada && p.estado==='ACTIVO'}}));
  }
  filtro.addEventListener('submit',e => {e.preventDefault();cargar().catch(e => mensaje.textContent=e.message);});
  filtro.elements.periodo.addEventListener('change',() => {
    ++turno; ciclo.replaceChildren();personas.replaceChildren(elemento('option','Seleccionar persona'));personas.options[0].value='';
    actualizarContextoEvaluacion(filtro.elements.periodo.value,'');
  });
  personas.addEventListener('change',seleccionarPersona);
  apiJson('/api/modelo-anual/gestiones').then(d => {
    const consulta = new URLSearchParams(location.search), solicitado = consulta.get('periodo_id');
    d.periodos.filter(p => !p.retirada || String(p.id)===solicitado).forEach(p => {
      const o=elemento('option',`${p.nombre} · ${p.fecha_inicio} — ${p.fecha_fin} · ${p.retirada?'Retirada':p.estado==='BORRADOR'?'Preparada':p.estado}`);o.value=p.id;filtro.elements.periodo.append(o);
    });
    const pid=solicitado || d.periodos.find(p=>!p.retirada&&p.estado==='ACTIVO')?.id;
    if (pid && [...filtro.elements.periodo.options].some(o=>o.value===String(pid))) {filtro.elements.periodo.value=pid;return cargar();}
  }).catch(e=>mensaje.textContent=e.message);
}
