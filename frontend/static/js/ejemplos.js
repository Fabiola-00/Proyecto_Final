"use strict";
{
  const lista=document.querySelector('#evaluaciones-anuales-propias'),mensaje=document.querySelector('#ejemplo-mensaje');
  async function cargar(){
    const d=await apiJson('/api/modelo-anual/propio');lista.replaceChildren();
    if(!d.gestiones.length)lista.append(elemento('p','Sin evaluaciones asignadas en una Gestión activa.'));
    d.gestiones.forEach(p=>{
      const seccion=elemento('section');seccion.append(elemento('h3',p.nombre));
      p.evaluaciones.forEach(e=>{const fila=elemento('article',undefined,'fila-compacta');fila.append(elemento('strong',e.nombre),elemento('span',e.estado));
        if(e.ejemplo && e.estado==='Pendiente'){
          const b=elemento('button','Abrir ejemplo','boton-editar');b.type='button';b.addEventListener('click',async()=>{b.disabled=true;try{const intento=await apiJson(`/api/modelo-anual/gestiones/${p.id}/ejemplo/${e.clave}`,{method:'POST',body:{}}),form=elemento('form',undefined,'formulario-inline');form.append(elemento('p','EJEMPLO ARITMÉTICO. Dos preguntas, 50 puntos cada una. Sin valor psicométrico.'));
            intento.preguntas.forEach((q,i)=>{const l=elemento('label',`${i+1}. ${q.a} ${q.operador} ${q.b} = ? · ${q.valor} puntos`),input=elemento('input');input.type='number';input.name=`respuesta${i}`;input.step='1';input.min='-1000';input.max='1000';input.required=true;l.append(input);form.append(l);});
            const fin=elemento('button','Finalizar ejemplo');form.append(fin);form.addEventListener('submit',async ev=>{ev.preventDefault();if(!form.reportValidity())return;fin.disabled=true;try{const r=await apiJson(`/api/modelo-anual/gestiones/${p.id}/ejemplo/${e.clave}/finalizar`,{method:'POST',body:{intento_id:intento.intento_id,respuestas:[0,1].map(i=>Number(form.elements[`respuesta${i}`].value))}});cerrarEdicion();mensaje.textContent=`Ejemplo finalizado: ${r.puntaje_ejemplo}/100. Sin valor psicométrico.`;await cargar();}catch(err){mostrarErrorEdicion(err);fin.disabled=false;}});botonEdicion(e.nombre,form,'Abrir ejemplo').click();
          }catch(err){mensaje.textContent=err.message;}finally{b.disabled=false;}});fila.append(b);
        }seccion.append(fila);
      });lista.append(seccion);
    });
  }
  if(lista)cargar().catch(e=>mensaje.textContent=e.message);
}
