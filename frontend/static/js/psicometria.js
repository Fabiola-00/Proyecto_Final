"use strict";
{
  const propia = document.querySelector('#psicometria-propia');
  const mensaje = document.querySelector('#psicometria-mensaje');
  const activaciones = document.querySelector('#psicometria-activaciones');
  const resultados = document.querySelector('#psicometria-resultados');
  let seleccion = 0, seleccionPersona = 0;
  document.querySelector('#modelo-filtro select')?.addEventListener('change', () => {
    ++seleccion; ++seleccionPersona; activaciones.replaceChildren(); resultados.replaceChildren();
  });
  document.querySelector('#modelo-persona')?.addEventListener('change', () => {
    ++seleccionPersona; resultados.replaceChildren();
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
    d.formulario.items.forEach((item, i) => {
      const l = elemento('label', `${i+1}. ${item.texto}`), s = elemento('select');
      s.name = `item${i}`; const vacio = elemento('option', 'Seleccionar respuesta'); vacio.value = ''; s.append(vacio);
      item.opciones.forEach((v, n) => { const o = elemento('option', v); o.value = n + (d.formulario.minimo_respuesta || 0); s.append(o); });
      s.value = d.respuestas[i] === null ? '' : String(d.respuestas[i]); l.append(s); form.append(l);
    });
    const estado = elemento('p'); estado.setAttribute('role', 'status');
    const guardar = elemento('button', 'Guardar avance', 'boton-editar'); guardar.type = 'button';
    const fin = elemento('button', 'Finalizar prueba');
    const l = elemento('label', 'Confirmo la finalización definitiva; no podré volver a responderla.');
    const confirmar = elemento('input'); confirmar.type = 'checkbox'; l.prepend(confirmar);
    form.append(l, guardar, fin, estado);
    async function enviar(final) {
      if (final && !confirmar.checked) { estado.textContent = 'Confirma la finalización definitiva.'; return; }
      guardar.disabled = fin.disabled = true;
      try {
        const respuestas = d.formulario.items.map((_, i) => form.elements[`item${i}`].value).map(v => v === '' ? null : Number(v));
        const r = await apiJson(`${base}/${final ? 'finalizar' : 'propia'}`, {method: final ? 'POST' : 'PUT', body: {revision, respuestas}});
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
    activaciones.replaceChildren(); resultados.replaceChildren();
    try {
      const d = await apiJson(`/api/modelo-anual/gestiones/${pid}/pruebas`);
      if (turno !== seleccion) return;
      activaciones.append(elemento('h2', 'Habilitación de pruebas psicométricas en esta Gestión'));
      const body = tabla(activaciones, ['Prueba', 'Revisión', 'Habilitación', 'Acción']);
      d.pruebas.forEach(p => {
        const tr = fila(body, [p.nombre, p.revisada ? 'Revisión registrada por ambos roles' : `Revisiones: ${p.revisiones.length}/2`, p.activa ? 'Habilitada' : 'Deshabilitada']);
        const td = elemento('td'), b = elemento('button', p.activa ? 'Deshabilitar' : 'Habilitar', 'boton-editar');
        b.type = 'button'; b.disabled = !editable || (!p.revisada && !p.activa);
        b.addEventListener('click', async () => {
          b.disabled = true;
          try {
            await apiJson(`/api/modelo-anual/gestiones/${pid}/pruebas/${p.clave}`, {method: 'PATCH', body: {activa: !p.activa, revision: p.revision}});
            document.dispatchEvent(new CustomEvent('sicose:psicometria-gestion', {detail: e.detail}));
          } catch (err) { document.querySelector('#modelo-mensaje').textContent = err.message; b.disabled = false; }
        }); td.append(b);
        const rol = document.body.dataset.rol;
        if (editable && !p.revisiones.some(r => r.rol === rol)) {
          const revisar = elemento('form', undefined, 'formulario-psicometria');
          revisar.append(elemento('p', `${p.formulario.version} · ${p.formulario.atribucion}`), elemento('p', p.formulario.politica));
          revisar.append(elemento('p', p.clave === 'GSE' ? 'Puntuación: suma de diez respuestas de 1 a 4; rango 10–40, sin categorías.' : 'Cinco sumas de 4 a 20. Inversos: 6, 7, 8, 9, 10, 15, 16, 17, 18, 19 y 20; se puntúan como 6 − respuesta.'));
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
      const estados = tabla(activaciones, ['Instructor Voluntario', 'GSE', 'Mini-IPIP']);
      d.personas.forEach(p => fila(estados, [p.nombre, p.pruebas.GSE, p.pruebas.MINIIPIP]));
      const uid = document.querySelector('#modelo-persona')?.value;
      if (uid) document.dispatchEvent(new CustomEvent('sicose:psicometria-persona', {detail:{pid,uid}}));
    } catch (err) { if (turno === seleccion) activaciones.textContent = err.message; }
  });
  document.addEventListener('sicose:psicometria-persona', async e => {
    const {pid, uid} = e.detail; const turno = ++seleccionPersona; resultados.replaceChildren();
    if (!uid) return;
    try {
      const d = await apiJson(`/api/modelo-anual/gestiones/${pid}/personas/${uid}/pruebas`);
      if (turno !== seleccionPersona) return;
      resultados.append(elemento('h2', 'Resumen de pruebas psicométricas'));
      resultados.append(elemento('p', 'Resultados descriptivos para revisión administrativa. Sin diagnóstico ni decisión automática.'));
      resultados.append(elemento('p', 'GSE: puntuación global de 10 a 40. Mini-IPIP: cinco sumas independientes de 4 a 20. No son calificaciones institucionales.'));
      const nombresSubescalas = {autoeficacia: 'Autoeficacia', extraversion: 'Extraversión', amabilidad: 'Amabilidad', responsabilidad: 'Responsabilidad', neuroticismo: 'Neuroticismo', apertura: 'Apertura', depresion: 'Depresión', ansiedad: 'Ansiedad', estres: 'Estrés', personal: 'Personal', trabajo: 'Trabajo', personas: 'Atención a personas'};
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
          p.respuestas.forEach((v, i) => fila(b, [i+1, p.formulario.items[i].texto, p.formulario.items[i].opciones[v - (p.formulario.minimo_respuesta || 0)], v]));
          td.append(botonEdicion(`Respuestas · ${p.nombre}`, panel, 'Ver respuestas'));
        } else td.textContent = 'Pendiente';
        tr.append(td);
      });
    } catch (err) { if (turno === seleccionPersona) resultados.textContent = err.message; }
  });
  if (propia) cargarPropias().catch(e => mensaje.textContent = e.message);
}
