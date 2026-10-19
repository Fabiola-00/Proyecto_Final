"use strict";
{
  const propia = document.querySelector('#psicometria-propia');
  const mensaje = document.querySelector('#psicometria-mensaje');
  const activaciones = document.querySelector('#psicometria-activaciones');
  const resultados = document.querySelector('#psicometria-resultados');
  const reinicios = document.querySelector('#psicometria-reinicio');
  let seleccion = 0, seleccionPersona = 0;
  let detalleGestion = null;
  const botonesReinicio = new Map();
  function bloquearReinicios() {
    botonesReinicio.forEach(b => { b.disabled = true; b.onclick = null; b.title = 'Selecciona un Instructor con la prueba completada.'; });
    const objetivo = document.querySelector('#reinicio-pruebas-objetivo');
    if (objetivo) objetivo.textContent = 'Reinicio individual: selecciona un Instructor en el selector de esta página.';
  }
  document.querySelector('#modelo-filtro select')?.addEventListener('change', () => {
    ++seleccion; ++seleccionPersona; detalleGestion = null; botonesReinicio.clear(); activaciones.replaceChildren(); reinicios.replaceChildren(); resultados.replaceChildren();
  });
  document.querySelector('#modelo-persona')?.addEventListener('change', () => {
    ++seleccionPersona; bloquearReinicios(); resultados.replaceChildren();
  });
  function tabla(contenedor, columnas) {
    const wrap = elemento('div', undefined, 'tabla-contenedor');
    const t = elemento('table', undefined, 'tabla-registros tabla-compacta');
    const head = elemento('thead'), tr = elemento('tr'), body = elemento('tbody');
    columnas.forEach(c => tr.append(elemento('th', c))); head.append(tr); t.append(head, body);
    wrap.append(t); contenedor.append(wrap); return body;
  }
  function fila(body, valores) {
    const tr = elemento('tr'); valores.forEach(v => tr.append(elemento('td', String(v)))); body.append(tr); return tr;
  }
  async function cargarPropias() {
    const d = await apiJson('/api/pruebas/propias'); propia.replaceChildren();
    if (!d.pruebas.length) propia.append(elemento('p', 'Sin pruebas habilitadas.'));
    const body = tabla(propia, ['Gestión', 'Prueba', 'Estado', 'Acción']);
    d.pruebas.forEach(p => {
      const tr = fila(body, [p.gestion, p.nombre, p.estado]), td = elemento('td');
      if (p.disponible) {
        const b = elemento('button', 'Abrir / continuar', 'boton-editar'); b.type = 'button';
        b.addEventListener('click', async () => {
          b.disabled = true;
          try { await abrir(p); } catch (e) { mensaje.textContent = e.message; } finally { b.disabled = false; }
        }); td.append(b);
      } else td.textContent = p.estado === 'Completada' ? 'Completada' : 'No disponible';
      tr.append(td);
    });
  }
  async function abrir(p) {
    const base = `/api/modelo-anual/gestiones/${p.periodo_id}/pruebas/${p.clave}`;
    const d = await apiJson(`${base}/propia`);
    if (d.estado === 'Completada') { await cargarPropias(); return; }
    const form = elemento('form', undefined, 'formulario-psicometria'); let revision = d.revision;
    form.append(elemento('p', d.formulario.instrucciones), elemento('p', d.formulario.politica), elemento('p', d.formulario.atribucion));
    if (d.formulario.simulacro) form.append(elemento('p', `Simulacro común: ${d.formulario.simulacro.nombre} · ${d.formulario.simulacro.fecha}`));
    d.formulario.items.forEach((item, i) => {
      const l = elemento('label', `${i+1}. ${item.texto}`), s = elemento('select');
      s.name = `item${i}`; const vacio = elemento('option', 'Seleccionar respuesta'); vacio.value = ''; s.append(vacio);
      item.opciones.forEach((v, n) => { const o = elemento('option', v); o.value = n * (d.formulario.paso_respuesta || 1) + (d.formulario.minimo_respuesta || 0); s.append(o); });
      s.value = d.respuestas[i] === null ? '' : String(d.respuestas[i]); l.append(s); form.append(l);
    });
    const estado = elemento('p'); estado.setAttribute('role', 'status');
    const guardar = elemento('button', 'Guardar avance', 'boton-editar'); guardar.type = 'button';
    const fin = elemento('button', 'Finalizar prueba');
    const l = elemento('label', p.clave==='NASATLX' ? 'Confirmo que participé y finalicé el simulacro común indicado, y envío definitivamente mis respuestas.' : 'Confirmo la finalización definitiva; no podré volver a responderla.');
    const confirmar = elemento('input'); confirmar.type = 'checkbox'; l.prepend(confirmar);
    form.append(l, guardar, fin, estado);
    async function enviar(final) {
      if (final && !confirmar.checked) { estado.textContent = 'Confirma la finalización definitiva.'; return; }
      guardar.disabled = fin.disabled = true;
      try {
        const respuestas = d.formulario.items.map((_, i) => form.elements[`item${i}`].value).map(v => v === '' ? null : Number(v));
        const cuerpo = {revision, respuestas, ciclo:d.ciclo || 0};
        if (p.clave==='NASATLX') cuerpo.confirmar_simulacro=confirmar.checked;
        const r = await apiJson(`${base}/${final ? 'finalizar' : 'propia'}`, {method: final ? 'POST' : 'PUT', body: cuerpo});
        revision = r.revision;
        if (final) { cerrarEdicion(); mensaje.textContent = 'Completada'; await cargarPropias(); }
        else estado.textContent = 'Avance guardado.';
      } catch (e) { estado.textContent = e.message; }
      finally { guardar.disabled = fin.disabled = false; }
    }
    guardar.addEventListener('click', () => enviar(false));
    form.addEventListener('submit', e => { e.preventDefault(); enviar(true); });
    botonEdicion(p.nombre, form, 'Responder prueba').click();
  }
  document.addEventListener('sicose:psicometria-gestion', async e => {
    const turno = ++seleccion, {pid, editable} = e.detail;
    detalleGestion = e.detail; ++seleccionPersona; botonesReinicio.clear();
    activaciones.replaceChildren(); reinicios.replaceChildren(); resultados.replaceChildren();
    try {
      const d = await apiJson(`/api/modelo-anual/gestiones/${pid}/pruebas`);
      if (turno !== seleccion) return;
      activaciones.append(elemento('h2', 'Habilitación de pruebas psicométricas en esta Gestión'));
      activaciones.append(elemento('p', d.simulacro ? `Simulacro común NASA-TLX: ${d.simulacro.nombre} · ${d.simulacro.fecha}` : 'NASA-TLX requiere registrar un simulacro común ya realizado antes de habilitarse.'));
      if (editable) {
        const form = elemento('form',undefined,'formulario-psicometria');
        for (const [nombre,titulo,tipo] of [['nombre','Nombre del simulacro común','text'],['fecha','Fecha de realización','date']]) {
          const l=elemento('label',titulo),i=elemento('input');i.name=nombre;i.type=tipo;i.required=true;i.value=d.simulacro?.[nombre]||'';if(nombre==='nombre')i.maxLength=200;l.append(i);form.append(l);
        }
        const l=elemento('label','Confirmo que el simulacro común ya fue realizado. No se podrá cambiar cuando existan intentos.'),check=elemento('input');check.type='checkbox';check.required=true;l.prepend(check);
        const guardar=elemento('button','Guardar simulacro'),estado=elemento('p');estado.setAttribute('role','status');form.append(l,guardar,estado);
        form.addEventListener('submit',async ev=>{ev.preventDefault();guardar.disabled=true;try{await apiJson(`/api/modelo-anual/gestiones/${pid}/simulacro-tlx`,{method:'PUT',body:{nombre:form.elements.nombre.value,fecha:form.elements.fecha.value,revision:d.simulacro?.revision||0,realizado:check.checked}});cerrarEdicion();document.dispatchEvent(new CustomEvent('sicose:psicometria-gestion',{detail:e.detail}));}catch(err){estado.textContent=err.message;}finally{guardar.disabled=false;}});
        activaciones.append(botonEdicion('Simulacro común de NASA-TLX',form,d.simulacro?'Ver / editar simulacro':'Registrar simulacro común'));
      }
      activaciones.append(elemento('p', 'Habilitar y deshabilitar afecta a toda la Gestión.'));
      reinicios.append(elemento('h2', 'Reinicio Individual'),elemento('p','Reiniciar afecta únicamente al Instructor seleccionado y conserva el resultado anterior en el historial. Requiere tu contraseña de inicio de sesión.'));
      const objetivo = elemento('p', 'Reinicio individual: selecciona un Instructor en el selector de esta página.');
      objetivo.id = 'reinicio-pruebas-objetivo'; objetivo.setAttribute('role', 'status'); reinicios.append(objetivo);
      const tablaReinicios = tabla(reinicios, ['Prueba', 'Acción individual']);
      const body = tabla(activaciones, ['Prueba', 'Revisión', 'Habilitación', 'Acción']);
      d.pruebas.forEach(p => {
        const tr = fila(body, [p.nombre, p.revisada ? 'Revisión registrada por ambos roles' : `Revisiones: ${p.revisiones.length}/2`, p.activa ? 'Habilitada' : 'Deshabilitada']);
        const td = elemento('td'), b = elemento('button', p.activa ? 'Deshabilitar' : 'Habilitar', 'boton-editar');
        b.type = 'button'; b.disabled = !editable || (!p.revisada && !p.activa) || (p.clave==='NASATLX'&&!p.activa&&!d.simulacro);
        if(p.clave==='NASATLX'&&!d.simulacro)b.title='Registra primero el simulacro común realizado.';
        b.addEventListener('click', async () => {
          b.disabled = true;
          try {
            await apiJson(`/api/modelo-anual/gestiones/${pid}/pruebas/${p.clave}`, {method: 'PATCH', body: {activa: !p.activa, revision: p.revision}});
            document.dispatchEvent(new CustomEvent('sicose:psicometria-gestion', {detail: e.detail}));
          } catch (err) { document.querySelector('#modelo-mensaje').textContent = err.message; b.disabled = false; }
        }); td.append(b);
        const reinicio = elemento('button', 'Reiniciar', 'boton-editar'); reinicio.type = 'button'; reinicio.disabled = true;
        reinicio.title = 'Selecciona un Instructor con la prueba completada.';
        reinicio.setAttribute('aria-label', `Reiniciar ${p.nombre} del Instructor seleccionado`);
        botonesReinicio.set(p.clave, reinicio);
        const filaReinicio = fila(tablaReinicios, [p.nombre]), accionReinicio = elemento('td');
        accionReinicio.append(reinicio); filaReinicio.append(accionReinicio);
        const rol = document.body.dataset.rol;
        if (editable && !p.revisiones.some(r => r.rol === rol)) {
          const revisar = elemento('form', undefined, 'formulario-psicometria');
          revisar.append(elemento('p', `${p.formulario.version} · ${p.formulario.atribucion}`), elemento('p', p.formulario.politica));
          revisar.append(elemento('p', p.clave==='NASATLX'?'Seis dimensiones de 0 a 100, pasos de 5, sin índice ponderado. Rendimiento: 0 bueno / 100 malo. Adaptación al español para SICOSE; sin validación lingüística acreditada.':p.clave === 'GSE' ? 'Puntuación: suma de diez respuestas de 1 a 4; rango 10–40, sin categorías.' : 'Cinco sumas de 4 a 20. Inversos: 6, 7, 8, 9, 10, 15, 16, 17, 18, 19 y 20; se puntúan como 6 − respuesta.'));
          const enlace = elemento('a', 'Consultar versión y fuente'); enlace.href = p.formulario.fuente; enlace.target = '_blank'; enlace.rel = 'noopener noreferrer'; revisar.append(enlace);
          const preguntas = tabla(revisar, ['Ítem', 'Texto', 'Opciones']);
          p.formulario.items.forEach((item, i) => fila(preguntas, [i+1, item.texto, item.opciones.join(' / ')]));
          const l = elemento('label', 'Constancia de revisión'), observacion = elemento('textarea'); observacion.name = 'observacion'; observacion.required = true; observacion.maxLength = 2000; l.append(observacion);
          const aceptar = elemento('label', 'He revisado la versión, puntuación, alcance orientativo, privacidad y conservación por Gestión.'), check = elemento('input'); check.type = 'checkbox'; check.required = true; aceptar.prepend(check);
          const enviar = elemento('button', 'Registrar mi revisión'), mensajeRevision = elemento('p'); mensajeRevision.setAttribute('role', 'status'); revisar.append(l, aceptar, enviar, mensajeRevision);
          revisar.addEventListener('submit', async ev => { ev.preventDefault(); enviar.disabled = true; try { await apiJson(`/api/modelo-anual/gestiones/${pid}/pruebas/${p.clave}/revision`, {method:'POST', body:{firma_formulario:p.firma_formulario, confirmar:check.checked, observacion:observacion.value}}); cerrarEdicion(); document.dispatchEvent(new CustomEvent('sicose:psicometria-gestion', {detail:e.detail})); } catch (err) { mensajeRevision.textContent = err.message; } finally { enviar.disabled = false; } });
          td.append(botonEdicion(`Revisar · ${p.nombre}`, revisar, 'Revisar versión'));
        }
        tr.append(td);
      });
      activaciones.append(elemento('h3', 'Estado por Instructor Voluntario'));
      const estados = tabla(activaciones, ['Instructor Voluntario', ...d.pruebas.map(p=>p.nombre)]);
      d.personas.forEach(p => fila(estados, [p.nombre, ...d.pruebas.map(f=>p.pruebas[f.clave])]));
      const uid = document.querySelector('#modelo-persona')?.value;
      if (uid) document.dispatchEvent(new CustomEvent('sicose:psicometria-persona', {detail:{pid,uid}}));
    } catch (err) { if (turno === seleccion) activaciones.textContent = err.message; }
  });
  document.addEventListener('sicose:psicometria-persona', async e => {
    const {pid, uid} = e.detail; const turno = ++seleccionPersona; bloquearReinicios(); resultados.replaceChildren();
    if (!uid) return;
    try {
      const d = await apiJson(`/api/modelo-anual/gestiones/${pid}/personas/${uid}/pruebas`);
      if (turno !== seleccionPersona) return;
      const objetivo = document.querySelector('#reinicio-pruebas-objetivo');
      if (objetivo) objetivo.textContent = `Reinicio individual: ${d.persona.nombre}`;
      d.pruebas.forEach(p => {
        const boton = botonesReinicio.get(p.clave);
        if (!boton) return;
        boton.disabled = !d.puede_reiniciar || p.estado !== 'Completada';
        boton.title = boton.disabled ? 'Requiere prueba completada, Gestión activa y cuenta activa.' : `Reiniciar ${p.nombre} de ${d.persona.nombre}`;
        boton.onclick = () => {
          const form = elemento('form', undefined, 'formulario-psicometria');
          form.append(elemento('p', `Instructor: ${d.persona.nombre} · Prueba: ${p.nombre}`),
            elemento('p', 'El resultado vigente dejará de usarse y la prueba quedará pendiente con respuestas vacías. Se conservará el intento anterior y las recomendaciones vinculadas quedarán desactualizadas. La habilitación de la prueba no cambia.'));
          const l = elemento('label', 'Tu contraseña de inicio de sesión'), password = elemento('input');
          password.type = 'password'; password.name = 'password'; password.autocomplete = 'current-password'; password.required = true; password.maxLength = 256; l.append(password);
          const aceptar = elemento('label', 'Confirmo el reinicio de esta prueba para este Instructor.'), check = elemento('input'); check.type = 'checkbox'; check.required = true; aceptar.prepend(check);
          const enviar = elemento('button', 'Confirmar reinicio'), estado = elemento('p'); estado.setAttribute('role', 'status'); form.append(l, aceptar, enviar, estado);
          form.addEventListener('submit', async ev => {
            ev.preventDefault(); enviar.disabled = true;
            const claveIngresada = password.value; password.value = '';
            try {
              await apiJson(`/api/modelo-anual/gestiones/${pid}/personas/${uid}/pruebas/${p.clave}/reiniciar`, {method:'POST',body:{password:claveIngresada,intento_ref:p.intento_ref,revision:p.revision,confirmar:check.checked}});
              cerrarEdicion();
              document.querySelector('#modelo-mensaje').textContent = 'Prueba reiniciada. Resultado anterior conservado y recomendaciones vinculadas desactualizadas.';
              if (detalleGestion && String(detalleGestion.pid) === String(pid)) document.dispatchEvent(new CustomEvent('sicose:psicometria-gestion',{detail:detalleGestion}));
            } catch (err) { estado.textContent = err.message; }
            finally { enviar.disabled = false; }
          });
          botonEdicion(`Reiniciar · ${p.nombre}`, form, 'Reiniciar prueba').click();
        };
      });
      resultados.append(elemento('h2', 'Resumen de pruebas psicométricas'));
      resultados.append(elemento('p', 'Resultados descriptivos para revisión administrativa. Sin diagnóstico ni decisión automática.'));
      resultados.append(elemento('p', 'GSE: 10 a 40. Mini-IPIP: cinco sumas de 4 a 20. NASA-TLX: seis dimensiones de carga de trabajo de 0 a 100; rendimiento 0 bueno / 100 malo. No son calificaciones institucionales.'));
      const nombresSubescalas = {autoeficacia: 'Autoeficacia', extraversion: 'Extraversión', amabilidad: 'Amabilidad', responsabilidad: 'Responsabilidad', neuroticismo: 'Neuroticismo', apertura: 'Apertura', depresion: 'Depresión', ansiedad: 'Ansiedad', estres: 'Estrés', personal: 'Personal', trabajo: 'Trabajo', personas: 'Atención a personas', demanda_mental:'Demanda mental', demanda_fisica:'Demanda física', demanda_temporal:'Demanda temporal', rendimiento:'Rendimiento (0 bueno / 100 malo)', esfuerzo:'Esfuerzo', frustracion:'Frustración'};
      const body = tabla(resultados, ['Prueba', 'Estado', 'Subescalas', 'Respuestas']);
      d.pruebas.forEach((p, i) => {
        const indicador = document.querySelector(`#modelo-entradas [data-fuente="PSICOMETRICA_${i+1}"]`);
        if (indicador) {
          indicador.querySelector('h3').textContent = p.nombre;
          indicador.querySelector('strong').textContent = p.estado;
          indicador.querySelector('p').textContent = p.estado === 'Completada' ? 'Subescalas disponibles en el resumen administrativo.' : 'Resultados pendientes.';
        }
        const texto = p.subescalas ? Object.entries(p.subescalas).map(([k,v]) => `${nombresSubescalas[k] || k}: ${v.valor.toFixed(2)} / ${v.rango[1]}${v.suma === undefined ? '' : ` (suma original: ${v.suma}/21)`}`).join(' · ') : 'Pendiente';
        const tr = fila(body, [p.nombre, p.estado, texto]), td = elemento('td');
        if (p.respuestas) {
          const panel = elemento('div'); panel.append(elemento('p', `${p.version} · Finalización: ${p.finalizada_en}`));
          const b = tabla(panel, ['Ítem', 'Pregunta', 'Respuesta', 'Código']);
          if(p.formulario.simulacro)panel.append(elemento('p',`Simulacro: ${p.formulario.simulacro.nombre} · ${p.formulario.simulacro.fecha}`));
          p.respuestas.forEach((v, i) => fila(b, [i+1, p.formulario.items[i].texto, p.formulario.items[i].opciones[(v - (p.formulario.minimo_respuesta || 0))/(p.formulario.paso_respuesta || 1)], v]));
          td.append(botonEdicion(`Respuestas · ${p.nombre}`, panel, 'Ver respuestas'));
        } else td.textContent = 'Pendiente';
        tr.append(td);
      });
      if (d.historial.length) {
        const panel = elemento('details'); panel.append(elemento('summary', 'Historial de pruebas reiniciadas'));
        const h = tabla(panel, ['Prueba', 'Finalización anterior', 'Reinicio', 'Responsable', 'Resultados conservados']);
        d.historial.forEach(p => fila(h, [p.nombre, p.finalizada_en, p.reiniciada_en, p.actor_nombre,
          Object.entries(p.subescalas).map(([k,v]) => `${nombresSubescalas[k] || k}: ${v.valor}`).join(' · ')]));
        resultados.append(panel);
      }
    } catch (err) { if (turno === seleccionPersona) resultados.textContent = err.message; }
  });
  if (propia) cargarPropias().catch(e => mensaje.textContent = e.message);
}
