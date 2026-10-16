"use strict";
const cursosCatalogo = document.querySelector("#curso-catalogo-lista");
if (cursosCatalogo) {
  const alta = document.querySelector("#curso-catalogo-form");
  const mensaje = document.querySelector("#curso-catalogo-mensaje");
  let hoy = "";
  let personal = [];
  function informar(texto, exito = false) { mensaje.textContent = texto; mensaje.classList.toggle("cursos-exito", exito); }
  function estadoClase(estado) { return ({ "Próximo": "proximo", "En curso": "en-curso", "Finalizado": "finalizado" })[estado] || "incompleto"; }
  function estadoVista(form) {
    const salida = form.querySelector(".curso-estado-previo");
    function actualizar() {
      const inicio = form.elements.fecha_inicio.value; const fin = form.elements.fecha_fin.value;
      const estado = inicio && fin && fin >= inicio && hoy ? hoy < inicio ? "Próximo" : hoy <= fin ? "En curso" : "Finalizado" : "Completa las fechas";
      salida.textContent = estado; salida.className = `curso-estado-previo estado-curso estado-curso-${estadoClase(estado)}`;
      form.elements.fecha_fin.min = inicio;
    }
    form.elements.fecha_inicio.addEventListener("change", actualizar); form.elements.fecha_fin.addEventListener("change", actualizar); actualizar();
  }
  async function guardarCurso(form, id) {
    if (!form.reportValidity()) return false;
    const body = Object.fromEntries(new FormData(form)); body.puntaje = Number(body.puntaje);
    const boton = form.querySelector("button"); boton.disabled = true;
    try { await apiJson(`/api/cursos${id ? "/" + id : ""}`, { method: id ? "PATCH" : "POST", body }); return true; }
    finally { boton.disabled = false; }
  }
  function tabla(cabeceras, clase = "") {
    const contenedor = elemento("div", undefined, "tabla-contenedor");
    const t = elemento("table", undefined, `tabla-registros ${clase}`); const head = elemento("thead"); const tr = elemento("tr");
    cabeceras.forEach((texto) => { const th = elemento("th", texto); th.scope = "col"; tr.append(th); });
    head.append(tr); const body = elemento("tbody"); t.append(head, body); contenedor.append(t);
    return { contenedor, body };
  }
  function icono(titulo, panel, tipo, etiqueta) { return iconoAccionInstructor(botonEdicion(titulo, panel, etiqueta), tipo, etiqueta); }
  function abrirParticipantes(curso) {
    const panel = elemento("div");
    const boton = icono(`Participantes · ${curso.nombre}`, panel, "ver", `Ver participantes de ${curso.nombre}`);
    boton.addEventListener("click", async () => {
      panel.replaceChildren(elemento("p", "Cargando participantes…"));
      try {
        const { participantes } = await apiJson(`/api/cursos/${curso.id}/participantes`);
        panel.replaceChildren(elemento("p", "La finalización es individual. Los puntajes todavía no se publican al Instructor.", "evaluaciones-ayuda"));
        if (!participantes.length) { panel.append(elemento("p", "Sin participantes asignados.")); return; }
        const t = tabla(["Instructor", "Estado", "Puntaje", "Finalización", "Acciones"], "tabla-participantes-curso");
        participantes.forEach((p) => {
          const tr = elemento("tr"); const nombre = elemento("td", p.nombre);
          nombre.append(elemento("small", p.cuenta_estado, `participante-cuenta ${p.cuenta_estado === "ACTIVO" ? "participante-activo" : "participante-inactivo"}`));
          tr.append(nombre, elemento("td", p.retirada ? "Retirado" : p.estado), elemento("td", p.puntaje === null ? "Pendiente" : `${p.puntaje} pts`), elemento("td", p.fecha_finalizacion || "Pendiente"));
          const acciones = elemento("td"); const fila = elemento("div", undefined, "acciones-curso");
          if (p.cuenta_estado === "ACTIVO" && !p.retirada) fila.append(editarParticipacion(curso, p));
          const historia = elemento("div"); const ver = icono(`Historial · ${p.nombre}`, historia, "ver", `Ver historial de ${p.nombre}`);
          ver.addEventListener("click", async () => {
            historia.replaceChildren(elemento("p", "Cargando historial…"));
            try {
              const { historial } = await apiJson(`/api/formacion/participaciones/${p.id}/historial`); historia.replaceChildren();
              historial.forEach((h) => {
                const registro = elemento("article", undefined, "historial-formacion");
                registro.append(elemento("strong", `Revisión ${h.revision} · ${h.estado}`), elemento("p", `${h.puntaje === null ? "Sin puntaje obtenido" : h.puntaje + " puntos"} · ${h.fecha_finalizacion || "Sin finalización"}`), elemento("p", `${h.responsable_nombre} · ${h.registrada_en}`));
                if (h.motivo) registro.append(elemento("p", h.motivo)); historia.append(registro);
              });
            } catch (error) { historia.replaceChildren(elemento("p", error.message)); }
          });
          fila.append(ver); acciones.append(fila); tr.append(acciones); t.body.append(tr);
        }); panel.append(t.contenedor);
      } catch (error) { panel.replaceChildren(elemento("p", error.message)); }
    });
    return boton;
  }
  function editarParticipacion(curso, p) {
    const form = elemento("form", undefined, "formulario-inline");
    const estadoLabel = elemento("label", "Estado personal"); const estado = elemento("select"); estado.name = "estado";
    ["Asignado", "En curso", "Finalizado", "No completado"].forEach((valor) => { const o = elemento("option", valor); o.value = valor; o.selected = valor === p.estado; estado.append(o); }); estadoLabel.append(estado); form.append(estadoLabel);
    form.append(elemento("p", `Puntaje de referencia al asignar: ${p.puntaje_base} puntos. Curso: ${p.inicio_curso} — ${p.fin_curso}.`, "evaluaciones-ayuda"));
    const final = elemento("div", undefined, "finalizacion-personal");
    const puntoLabel = elemento("label", "Puntaje individual (0–100, entero)"); const puntos = elemento("input"); puntos.type = "number"; puntos.name = "puntaje"; puntos.min = "0"; puntos.max = "100"; puntos.step = "1"; puntos.value = p.puntaje ?? p.puntaje_base; puntoLabel.append(puntos);
    const fechaLabel = elemento("label", "Fecha de finalización personal"); const fecha = elemento("input"); fecha.type = "date"; fecha.name = "fecha_finalizacion"; fecha.min = p.inicio_curso; fecha.max = hoy; fecha.value = p.fecha_finalizacion || ""; fechaLabel.append(fecha); final.append(puntoLabel, fechaLabel); form.append(final);
    function alternar() { const esFinal = estado.value === "Finalizado"; final.hidden = !esFinal; [puntos, fecha].forEach((control) => { control.required = esFinal; control.disabled = !esFinal; }); }
    estado.addEventListener("change", alternar); alternar();
    const motivoLabel = elemento("label", "Motivo del cambio"); const motivo = elemento("textarea"); motivo.name = "motivo"; motivo.required = true; motivo.maxLength = 2000; motivoLabel.append(motivo); form.append(motivoLabel);
    const guardar = elemento("button", "Guardar cambio"); form.append(guardar);
    form.addEventListener("submit", async (event) => {
      event.preventDefault(); if (!form.reportValidity()) return; guardar.disabled = true;
      const body = Object.fromEntries(new FormData(form)); body.revision = p.revision; if ("puntaje" in body) body.puntaje = Number(body.puntaje);
      try { await apiJson(`/api/formacion/participaciones/${p.id}`, { method: "PATCH", body }); cerrarEdicion(); informar("Participación actualizada. Historial conservado.", true); await cargarCursos(); }
      catch (error) { mostrarErrorEdicion(error); }
      finally { guardar.disabled = false; }
    });
    return icono(`Actualizar participación · ${p.nombre}`, form, "editar", `Actualizar participación de ${p.nombre}`);
  }
  function asignarParticipantes(curso) {
    const panel = elemento("div"); const boton = icono(`Asignar participantes · ${curso.nombre}`, panel, "asignar", `Asignar participantes a ${curso.nombre}`);
    if (!curso.estado || curso.puntaje === null || !curso.entidad || !curso.tipo) { boton.disabled = true; boton.title = "Completa las fechas, entidad, tipo y puntaje del curso antes de asignar."; }
    boton.addEventListener("click", async () => {
      panel.replaceChildren(elemento("p", "Cargando personal…"));
      try {
        const [{ participantes }, { voluntarios }] = await Promise.all([apiJson(`/api/cursos/${curso.id}/participantes`), apiJson("/api/instructores-voluntarios")]);
        personal = voluntarios.filter((p) => p.estado === "ACTIVO" && !participantes.some((a) => a.voluntario_id === p.id)); panel.replaceChildren();
        if (!personal.length) { panel.append(elemento("p", "No hay personal activo sin asignar a este curso.")); return; }
        const form = elemento("form", undefined, "formulario-inline");
        const grupo = elemento("fieldset", undefined, "asignacion-participantes");
        grupo.append(elemento("legend", "Instructores Voluntarios (selección múltiple)"));
        const lista = elemento("div", undefined, "asignacion-participantes-lista");
        personal.forEach((p) => {
          const fila = elemento("label", undefined, "asignacion-participante");
          const casilla = elemento("input"); casilla.type = "checkbox"; casilla.name = "voluntario_ids"; casilla.value = p.id;
          fila.append(casilla, elemento("span", `${p.nombre} · ${p.codigo_instructor || "Sin código"}`)); lista.append(fila);
        });
        const contador = elemento("p", "0 personas seleccionadas", "evaluaciones-ayuda"); contador.setAttribute("aria-live", "polite");
        grupo.append(lista, contador);
        form.append(grupo, elemento("p", "Marca una o varias personas. La asignación inicia sin puntaje obtenido; la finalización se registra después.", "evaluaciones-ayuda"));
        const seleccionados = () => Array.from(lista.querySelectorAll("input:checked"), (control) => Number(control.value));
        const guardar = elemento("button", "Asignar participantes"); guardar.disabled = true; form.append(guardar);
        lista.addEventListener("change", () => {
          const cantidad = seleccionados().length;
          contador.textContent = `${cantidad} ${cantidad === 1 ? "persona seleccionada" : "personas seleccionadas"}`;
          guardar.disabled = cantidad === 0;
        });
        form.addEventListener("submit", async (event) => {
          event.preventDefault(); const ids = seleccionados(); if (!ids.length || !form.reportValidity()) return; guardar.disabled = true;
          grupo.disabled = true;
          try { await apiJson(`/api/cursos/${curso.id}/participantes`, { method: "POST", body: { voluntario_ids: ids } }); cerrarEdicion(); informar("Participantes asignados.", true); await cargarCursos(); }
          catch (error) { mostrarErrorEdicion(error); }
          finally { grupo.disabled = false; guardar.disabled = seleccionados().length === 0; }
        }); panel.append(form);
      } catch (error) { panel.replaceChildren(elemento("p", error.message)); }
    }); return boton;
  }
  function retirarParticipantes(curso) {
    const panel=elemento('div'),boton=botonEdicion(`Retirar participantes · ${curso.nombre}`,panel,'Retirar participantes');
    boton.addEventListener('click',async()=>{
      panel.replaceChildren(elemento('p','Cargando participantes…'));
      try {
        const {participantes}=await apiJson(`/api/cursos/${curso.id}/participantes`),form=elemento('form',undefined,'formulario-inline'),grupo=elemento('fieldset',undefined,'campo-ancho');grupo.append(elemento('legend','Participantes que se retirarán'));
        participantes.filter(p=>!p.retirada).forEach(p=>{const l=elemento('label',undefined,'asignacion-participante'),i=elemento('input');i.type='checkbox';i.value=p.id;i.dataset.revision=p.revision;i.disabled=p.cuenta_estado!=='ACTIVO';l.append(i,elemento('span',`${p.nombre} · ${p.estado} · ${p.cuenta_estado}`));grupo.append(l);});
        const l=elemento('label','Motivo'),m=elemento('textarea');m.required=true;m.maxLength=2000;l.append(m);const b=elemento('button','Retirar seleccionados');b.disabled=true;grupo.addEventListener('change',()=>b.disabled=!grupo.querySelector('input:checked'));form.append(grupo,l,elemento('p','Se conserva el historial. Los puntajes se retiran del acumulado vigente; las gestiones cerradas requieren reapertura.'),b);panel.replaceChildren(form);
        form.addEventListener('submit',async e=>{e.preventDefault();const seleccion=[...grupo.querySelectorAll('input:checked')].map(i=>({id:Number(i.value),revision:Number(i.dataset.revision)}));if(!seleccion.length)return;b.disabled=true;try{await apiJson(`/api/cursos/${curso.id}/retirar-participantes`,{method:'POST',body:{motivo:m.value,participaciones:seleccion}});cerrarEdicion();informar('Participantes retirados; historial conservado.',true);await cargarCursos();}catch(err){mostrarErrorEdicion(err);b.disabled=false;}});
      } catch(err){panel.replaceChildren(elemento('p',err.message));}
    });return iconoAccionInstructor(boton,'retirar','Retirar participantes');
  }
  function eliminarCurso(curso) {
    const f=elemento('form',undefined,'formulario-inline');f.append(elemento('p','Sin participaciones se eliminará permanentemente. Con vínculos se dará de baja conservando formación e historial.'));const l=elemento('label','Motivo'),m=elemento('textarea');m.required=true;m.maxLength=2000;l.append(m);f.append(l,elemento('button','Eliminar / dar de baja'));
    f.addEventListener('submit',async e=>{e.preventDefault();const b=f.querySelector('button');b.disabled=true;try{const r=await apiJson(`/api/cursos/${curso.id}`,{method:'DELETE',body:{motivo:m.value}});cerrarEdicion();informar(r.baja?'Curso dado de baja; historial conservado.':'Curso eliminado.',true);await cargarCursos();}catch(err){mostrarErrorEdicion(err);b.disabled=false;}});
    return icono(`Eliminar curso · ${curso.nombre}`,f,'desactivar',`Eliminar curso ${curso.nombre}`);
  }
  async function cargarCursos() {
    const datos = await apiJson("/api/cursos"+(document.querySelector('#cursos-incluir-bajas').checked?'?incluir_bajas=1':'')); hoy = datos.hoy; cursosCatalogo.replaceChildren(); estadoVistaInicial();
    if (!datos.cursos.length) { cursosCatalogo.append(elemento("p", "Sin cursos registrados.")); return; }
    const t = tabla(["Curso / Entidad", "Tipo", "Inicio / Fin", "Estado automático", "Puntaje", "Participantes", "Acciones"], "tabla-cursos");
    datos.cursos.forEach((curso) => {
      const tr = elemento("tr"); const nombre = elemento("td"); nombre.append(elemento("strong", curso.nombre+(curso.baja?' · Baja':'')), elemento("small", curso.entidad || "Entidad sin registrar"));
      const fechas = elemento("td"); fechas.append(elemento("span", curso.fecha_inicio || "Sin inicio"), elemento("small", curso.fecha_fin || "Sin fin"));
      const estado = elemento("td"); estado.append(elemento("span", curso.estado || "Sin fechas completas", `estado-curso estado-curso-${estadoClase(curso.estado)}`));
      tr.append(nombre, elemento("td", curso.tipo || "Sin registrar"), fechas, estado, elemento("td", curso.puntaje === null ? "Pendiente" : `${curso.puntaje} pts`), elemento("td", `${curso.participantes_total} (${curso.finalizados_total} finalizados)`));
      const acciones = elemento("td"); const fila = elemento("div", undefined, "acciones-curso"); fila.append(abrirParticipantes(curso));
      if(curso.baja){fila.append(retirarParticipantes(curso));acciones.append(fila);tr.append(acciones);t.body.append(tr);return;}
      const edicion = document.querySelector("#curso-edicion-template").content.firstElementChild.cloneNode(true);
      ["nombre", "tipo", "entidad", "fecha_inicio", "fecha_fin", "puntaje", "observaciones"].forEach((campo) => { edicion.elements[campo].value = curso[campo] ?? ""; }); estadoVista(edicion);
      edicion.addEventListener("submit", async (event) => { event.preventDefault(); try { if (await guardarCurso(edicion, curso.id)) { cerrarEdicion(); informar("Curso actualizado; asignaciones previas conservadas.", true); await cargarCursos(); } } catch (error) { mostrarErrorEdicion(error); } });
      fila.append(icono(`Editar curso · ${curso.nombre}`, edicion, "editar", `Editar curso ${curso.nombre}`), asignarParticipantes(curso), retirarParticipantes(curso), eliminarCurso(curso)); acciones.append(fila); tr.append(acciones); t.body.append(tr);
    }); cursosCatalogo.append(t.contenedor);
  }
  let vistaConfigurada = false;
  function estadoVistaInicial() { if (!vistaConfigurada) { estadoVista(alta); vistaConfigurada = true; } else alta.elements.fecha_inicio.dispatchEvent(new Event("change")); }
  alta.addEventListener("submit", async (event) => { event.preventDefault(); try { if (await guardarCurso(alta)) { alta.reset(); document.querySelector('#registro-curso').open=false; informar("Curso registrado.", true); await cargarCursos(); } } catch (error) { informar(error.message); } });
  document.querySelector('#cursos-incluir-bajas').addEventListener('change',()=>cargarCursos().catch(e=>informar(e.message)));
  cargarCursos().catch((error) => informar(error.message));
}

const cursosPropios = document.querySelector("#cursos-propios-lista");
if (cursosPropios) {
  Promise.all([apiJson("/api/instructor-voluntario/formacion"), apiJson("/api/instructor-voluntario/capacitaciones")]).then(([{ participaciones, publicaciones = [] }, { capacitaciones }]) => {
    cursosPropios.replaceChildren(); cursosPropios.classList.remove("rejilla-modulos");
    cursosPropios.append(elemento("p", "Asignaciones y estados vigentes. Los puntos se muestran aparte según su última versión publicada; una corrección requiere republicación.", "evaluaciones-ayuda"));
    if (!participaciones.length) cursosPropios.append(elemento("p", "Sin cursos asignados."));
    participaciones.forEach((p) => {
      const fila = elemento("article", undefined, "curso-personal");
      fila.append(elemento("h3", p.nombre_curso), elemento("p", `${p.tipo_curso} · ${p.entidad_curso}`), elemento("p", `${p.inicio_curso} — ${p.fin_curso}`), elemento("strong", p.estado));
      if (p.fecha_finalizacion) fila.append(elemento("p", `Finalización personal: ${p.fecha_finalizacion}`)); cursosPropios.append(fila);
    });
    publicaciones.forEach((p) => {
      const fila = elemento("article", undefined, "curso-personal"); const a = p.academica;
      fila.append(elemento("h3", `Formación publicada · Gestión ${p.gestion}`), elemento("p", `Acumulado: ${a.valor ?? "Pendiente"} · Publicado: ${a.publicada_en}`));
      a.cursos.forEach((c) => fila.append(elemento("p", `${c.nombre_curso} · ${c.puntaje} puntos · Finalización publicada: ${c.fecha_finalizacion}`))); cursosPropios.append(fila);
    });
    if (capacitaciones.length) cursosPropios.append(elemento("h3", "Formación histórica (sin finalización individual registrada)"));
    capacitaciones.forEach((curso) => { const fila = elemento("article", undefined, "curso-personal"); fila.append(elemento("h3", curso.nombre), elemento("p", `${curso.fecha || "Sin fecha"} · ${curso.entidad || "Sin entidad"}`)); cursosPropios.append(fila); });
  }).catch((error) => { document.querySelector("#cursos-propios-mensaje").textContent = error.message; });
}
