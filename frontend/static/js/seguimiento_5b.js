"use strict";

const comandanteAlta = document.querySelector("#comandante-alta");
if (comandanteAlta) {
  const mensaje = document.querySelector("#comandante-mensaje");
  const lista = document.querySelector("#comandantes-lista");
  async function cargarComandantes() {
    const { comandantes } = await apiJson("/api/admin/comandantes");
    lista.replaceChildren();
    if (!comandantes.length) lista.append(elemento("p", "No hay Comandante registrado."));
    comandantes.forEach((persona) => {
      const tarjeta = elemento("article", undefined, "tarjeta-modulo");
      tarjeta.append(elemento("h3", persona.nombre), elemento("p", `${persona.username} · ${persona.estado}`));
      const form = elemento("form", undefined, "formulario-inline");
      [["nombre", "Nombre completo", persona.nombre], ["correo", "Correo", persona.correo || ""]].forEach(([nombre, etiqueta, valor]) => {
        const label = elemento("label", etiqueta); const input = elemento("input"); input.name = nombre; input.value = valor;
        input.maxLength = nombre === "nombre" ? 160 : 254; input.required = nombre === "nombre"; if (nombre === "correo") input.type = "email";
        label.append(input); form.append(label);
      });
      const label = elemento("label", "Estado"); const estado = elemento("select"); estado.name = "estado";
      ["ACTIVO", "INACTIVO"].forEach((valor) => { const opcion = elemento("option", valor); opcion.value = valor; opcion.selected = valor === persona.estado; estado.append(opcion); });
      label.append(estado); form.append(label, elemento("button", "Guardar cambios"));
      form.addEventListener("submit", async (event) => {
        event.preventDefault(); if (!form.reportValidity()) return;
        try { await apiJson(`/api/admin/comandantes/${persona.id}`, { method: "PATCH", body: Object.fromEntries(new FormData(form)) }); cerrarEdicion(); await cargarComandantes(); }
        catch (error) { mostrarErrorEdicion(error); }
      });
      tarjeta.append(botonEdicion(`Editar Comandante · ${persona.nombre}`, form, "Editar"));
      const clave = elemento("form", undefined, "formulario-inline"); const claveLabel = elemento("label", "Nueva contraseña");
      const password = elemento("input"); password.name = "password"; password.type = "password"; password.minLength = 12; password.maxLength = 256; password.required = true; password.autocomplete = "new-password";
      claveLabel.append(password); clave.append(claveLabel, elemento("button", "Restablecer contraseña"));
      clave.addEventListener("submit", async (event) => {
        event.preventDefault(); if (!clave.reportValidity()) return;
        try { await apiJson(`/api/admin/usuarios/${persona.id}/restablecer-clave`, { method: "POST", body: { password: password.value } }); clave.reset(); cerrarEdicion(); mensaje.textContent = "Contraseña restablecida; sesiones anteriores invalidadas."; }
        catch (error) { mostrarErrorEdicion(error); }
      });
      tarjeta.append(botonEdicion(`Restablecer contraseña · ${persona.nombre}`, clave, "Restablecer contraseña"));
      lista.append(tarjeta);
    });
  }
  comandanteAlta.addEventListener("submit", async (event) => {
    event.preventDefault(); if (!comandanteAlta.reportValidity()) return;
    const boton = comandanteAlta.querySelector("button"); boton.disabled = true;
    try { await apiJson("/api/admin/comandantes", { method: "POST", body: Object.fromEntries(new FormData(comandanteAlta)) }); comandanteAlta.reset(); mensaje.textContent = "Comandante creado."; await cargarComandantes(); }
    catch (error) { mensaje.textContent = error.message; }
    finally { boton.disabled = false; }
  });
  cargarComandantes().catch((error) => { mensaje.textContent = error.message; });
}

const seguimientoFiltros = document.querySelector("#seguimiento-filtros");
if (seguimientoFiltros) {
  const mensaje = document.querySelector("#seguimiento-mensaje");
  const lista = document.querySelector("#seguimiento-notas");
  const fuentes = { FISICA_1: "Física 1", FISICA_2: "Física 2", ACADEMICA: "Académica", DESEMPENO_JEFE: "Desempeño del Jefe", DESEMPENO_COMANDANTE: "Desempeño del Comandante" };
  let revision = 0;
  const rol = document.body.dataset.rol;
  async function cargarSeguimiento() {
    const persona = seguimientoFiltros.elements.persona.value; const periodo = seguimientoFiltros.elements.periodo.value;
    if (!persona || !periodo) return;
    const actual = ++revision; lista.replaceChildren();
    const datos = await apiJson(`/api/5b/personas/${persona}?periodo_id=${periodo}`);
    const programacion = await apiJson(`/api/5b/periodos/${periodo}/fisicas`);
    const { calculo } = await apiJson(`/api/5b/personas/${persona}/calculo?periodo_id=${periodo}`);
    const { publicacion } = await apiJson(`/api/5b/personas/${persona}/publicacion?periodo_id=${periodo}`);
    if (actual !== revision) return;
    const resultado = document.querySelector("#seguimiento-calculo"); resultado.replaceChildren(elemento("h3", calculo.provisional === false ? "Resultado conservado del cierre" : "Resultado provisional"));
    if (!calculo.regla) resultado.append(elemento("p", calculo.limite));
    else {
      resultado.append(elemento("p", `Física: ${calculo.fisica ?? "No disponible"} · Académica: ${calculo.academica.valor ?? "Pendiente"} · Desempeño: ${calculo.desempeno ?? "No disponible"}`), elemento("p", `Resultado conjunto: ${calculo.resultado_conjunto ?? "No disponible"}`), elemento("p", calculo.provisional === false ? `Instantánea del cierre #${calculo.cierre_id}. No se recalcula con fuentes actuales ni equivale a publicación.` : "Cálculo provisional, sin publicación ni cierre. Los componentes conservan precisión exacta; solo el resultado conjunto se redondea."));
      if (calculo.faltantes.length) resultado.append(elemento("p", `Fuentes faltantes o desactivadas: ${calculo.faltantes.map((f) => fuentes[f]).join(", ")}`));
      const detalle = elemento("div"); detalle.append(elemento("p", `Puntos de formación: ${calculo.academica.puntos_sin_tope} · Tope: 100`));
      calculo.academica.detalle.forEach((p) => detalle.append(elemento("p", `${p.nombre_curso} · ${p.fecha_finalizacion} · ${p.puntaje} puntos · participación #${p.participacion_id}, revisión ${p.revision}`)));
      Object.entries(calculo.fuentes).forEach(([f, n]) => detalle.append(elemento("p", `${fuentes[f]} · nota #${n.nota_id ?? "Sin nota"} · ${n.nota ?? "Pendiente"} · ${n.incluida ? "Incluida" : "No incluida"}`)));
      resultado.append(botonEdicion(calculo.provisional === false ? "Fuentes conservadas del cierre" : "Fuentes del cálculo provisional", detalle, "Ver detalle del cálculo"));
    }
    const publicarPanel = elemento("section", undefined, "tarjeta-modulo calculo-provisional"); publicarPanel.append(elemento("h3", "Publicación al Instructor"));
    publicarPanel.append(elemento("p", publicacion.revision_publicada ? `Versión ${publicacion.revision_publicada} · ${publicacion.publicada_en}${publicacion.hay_cambios ? " · Hay correcciones pendientes de republicar" : " · Sin cambios pendientes"}` : "Sin publicación previa."), elemento("p", "Solo se publican físicas y formación/acumulado académico. Admite publicación parcial. Las correcciones conservan la versión publicada anterior hasta republicar; una evaluación deshabilitada o gestión retirada oculta sus notas."));
    if (publicacion.puede_publicar) {
      const form = elemento("form", undefined, "formulario-inline");
      Object.entries(publicacion.contenido.fisicas).forEach(([f, v]) => form.append(elemento("p", `${fuentes[f]}: ${v.nota ?? "Pendiente"} · ${publicacion.habilitadas[f] ? "Se actualizará" : "Conservará versión anterior oculta"}`)));
      const a = publicacion.contenido.academica;
      if (a) { form.append(elemento("p", `Acumulado académico: ${a.valor ?? "Pendiente"}`)); a.cursos.forEach((c) => form.append(elemento("p", `${c.nombre_curso} · ${c.puntaje} puntos · ${c.fecha_finalizacion}`))); }
      const label = elemento("label", "Motivo de publicación o republicación"); const motivo = elemento("textarea"); motivo.required = true; motivo.maxLength = 2000; label.append(motivo);
      const confirmarLabel = elemento("label", "He revisado estos valores y los pendientes"); const confirmar = elemento("input"); confirmar.type = "checkbox"; confirmar.required = true; confirmarLabel.prepend(confirmar);
      const boton = elemento("button", publicacion.revision_publicada ? "Republicar notas revisadas" : "Publicar notas revisadas"); form.append(label, confirmarLabel, boton);
      form.addEventListener("submit", async (event) => {
        event.preventDefault(); if (!form.reportValidity()) return; boton.disabled = true;
        try { await apiJson(`/api/5b/personas/${persona}/publicacion`, { method: "POST", body: { periodo_id: Number(periodo), revision_publicada: publicacion.revision_publicada, firma_fuentes: publicacion.firma_fuentes, motivo: motivo.value } }); cerrarEdicion(); await cargarSeguimiento(); }
        catch (error) { mostrarErrorEdicion(error); } finally { boton.disabled = false; }
      });
      publicarPanel.append(botonEdicion("Revisar publicación al Instructor", form, publicacion.revision_publicada ? "Revisar y republicar" : "Revisar y publicar"));
    } else publicarPanel.append(elemento("p", "Publicación bloqueada: requiere cuenta y gestión activas, regla 5B.2, fuentes habilitadas y datos publicables o una versión anterior que rectificar."));
    const historial = elemento("div"); const abrirHistorial = botonEdicion("Historial de publicaciones", historial, "Historial de publicaciones");
    abrirHistorial.addEventListener("click", async () => {
      historial.replaceChildren(elemento("p", "Consultando versiones…"));
      try { const { historial: versiones } = await apiJson(`/api/5b/personas/${persona}/publicaciones/historial?periodo_id=${periodo}`); historial.replaceChildren(); if (!versiones.length) historial.append(elemento("p", "Sin publicaciones."));
        versiones.forEach((v) => { historial.append(elemento("h3", `Versión ${v.revision} · ${v.publicada_en}`), elemento("p", `${v.responsable_nombre} · ${v.motivo}`)); Object.entries(v.contenido.fisicas).forEach(([f, n]) => historial.append(elemento("p", `${fuentes[f]}: ${n.nota ?? "Pendiente"}`))); if (v.contenido.academica) historial.append(elemento("p", `Acumulado: ${v.contenido.academica.valor ?? "Pendiente"}`)); });
      } catch (error) { mostrarErrorEdicion(error); }
    });
    publicarPanel.append(abrirHistorial); resultado.after(publicarPanel);
    document.querySelectorAll("#seguimiento-publicacion").forEach((n) => n.remove()); publicarPanel.id = "seguimiento-publicacion";
    mensaje.textContent = `${datos.persona.nombre} · ${datos.periodo.nombre} · ${datos.periodo.estado}${datos.configuracion?.estado !== "PUBLICADA" ? " · Sin configuración 5B publicada" : ""}`;
    document.querySelector("#seguimiento-perfil").replaceChildren(elemento("p", `${datos.persona.codigo_instructor || "Sin código"} · ${datos.persona.grado || "Sin grado"} · ${datos.persona.especialidad_principal || "Sin especialidad"}`));
    const formacion = document.querySelector("#seguimiento-formacion"); formacion.replaceChildren(elemento("h3", "Formación registrada"));
    if (!datos.formacion.length) formacion.append(elemento("p", "Sin formación histórica registrada."));
    datos.formacion.forEach((curso) => formacion.append(elemento("p", `${curso.nombre} · ${curso.fecha || "Sin fecha"} · ${curso.entidad || "Sin entidad"}`)));
    (datos.participaciones_curso || []).forEach((curso) => formacion.append(elemento("p", `${curso.nombre_curso} · ${curso.estado} · ${curso.fecha_finalizacion || "Sin finalización personal"} · ${curso.puntaje === null ? "Sin puntaje obtenido" : curso.puntaje + " puntos"}`)));
    const asistencias = document.querySelector("#seguimiento-asistencias"); asistencias.replaceChildren(elemento("h3", "Asistencias del período"));
    if (!datos.asistencias.length) asistencias.append(elemento("p", "Sin registros de asistencia."));
    datos.asistencias.forEach((registro) => asistencias.append(elemento("p", `${registro.fecha} · ${registro.actividad} · ${registro.estado}`)));
    const historico = document.querySelector("#seguimiento-historico"); historico.replaceChildren();
    if (datos.notas_historicas.length) {
      historico.append(elemento("h3", "Notas anteriores sin fuente 5B asignada"));
      datos.notas_historicas.forEach((nota) => historico.append(elemento("p", `${nota.evaluacion} · ${nota.nota_0_100} · ${nota.registrada_en}`)));
    }
    Object.entries(fuentes).forEach(([fuente, nombre]) => {
      const notas = datos.notas.filter((nota) => nota.fuente === fuente); const ultima = notas[notas.length - 1];
      const tarjeta = elemento("article", undefined, "tarjeta-modulo");
      const acumulada = fuente === "ACADEMICA" && datos.regla_calculo;
      tarjeta.append(elemento("h3", nombre), elemento("p", acumulada ? `Acumulado académico: ${calculo.academica.valor ?? "Pendiente"}` : ultima ? `Nota: ${ultima.nota_0_100}` : "Pendiente"));
      const agenda = datos.fisicas?.[fuente];
      const activa = datos.activaciones?.find((e) => e.clave === fuente)?.activa ?? true;
      const operativa = activa && datos.periodo.estado === "ACTIVO" && datos.configuracion?.estado === "PUBLICADA";
      if (!activa) tarjeta.append(elemento("p", "Evaluación desactivada en esta gestión; historial conservado."));
      if (agenda) {
        tarjeta.append(elemento("p", `Fecha común: ${agenda.comun?.fecha || "Sin programación"} · Fecha individual: ${agenda.individual?.fecha || "Sin reprogramación"}`));
        if (ultima?.fisica) tarjeta.append(elemento("p", ultima.fisica.estado === "NO_CUMPLIDA" ? "No cumplida · cero confirmado, conservado durante la reprogramación" : `Cumplida el ${ultima.fisica.fecha_realizacion}`));
        const historial = elemento("div");
        programacion.historial.filter((r) => r.fuente === fuente).forEach((r) => historial.append(elemento("p", `Común: ${r.fecha} · ${r.actor_nombre} · ${r.modificada_en} · ${r.motivo}`)));
        datos.historial_fisicas.filter((r) => r.fuente === fuente).forEach((r) => historial.append(elemento("p", `Individual: ${r.fecha_anterior} → ${r.fecha} · ${r.actor_nombre} · ${r.modificada_en} · ${r.motivo}`)));
        tarjeta.append(botonEdicion(`Fechas e historial · ${nombre}`, historial, "Historial de fechas"));
        function formularioFecha(individual) {
          const form = elemento("form", undefined, "formulario-inline");
          const etiqueta = elemento("label", individual ? "Nueva fecha individual" : "Fecha común");
          const fecha = elemento("input"); fecha.type = "date"; fecha.required = true; fecha.min = datos.periodo.fecha_inicio; fecha.max = datos.periodo.fecha_fin; fecha.value = individual ? agenda.fecha_prevista : agenda.comun?.fecha || ""; etiqueta.append(fecha);
          const motivoLabel = elemento("label", "Motivo"); const motivo = elemento("textarea"); motivo.required = true; motivo.maxLength = 2000; motivoLabel.append(motivo);
          const guardar = elemento("button", "Guardar fecha"); form.append(etiqueta, motivoLabel, guardar);
          form.addEventListener("submit", async (event) => {
            event.preventDefault(); if (!form.reportValidity()) return; guardar.disabled = true;
            const body = { fecha: fecha.value, motivo: motivo.value, anterior_id: (individual ? agenda.individual : agenda.comun)?.id ?? null };
            if (individual) body.programacion_id = agenda.comun.id;
            try { await apiJson(`/api/5b/periodos/${periodo}/fisicas/${fuente}${individual ? `/personas/${persona}` : ""}`, { method: "POST", body }); cerrarEdicion(); await cargarSeguimiento(); }
            catch (error) { mostrarErrorEdicion(error); } finally { guardar.disabled = false; }
          });
          return form;
        }
        if (operativa) tarjeta.append(botonEdicion(`Programación común · ${nombre}`, formularioFecha(false), "Programar fecha común"));
        if (operativa && agenda.comun && datos.persona.estado === "ACTIVO" && datos.habilitaciones?.[fuente]) tarjeta.append(botonEdicion(`Reprogramación extraordinaria · ${nombre}`, formularioFecha(true), "Reprogramar persona"));
      }
      const configurada = datos.configuracion?.fuentes.find((f) => f.fuente === fuente);
      if (configurada) tarjeta.append(elemento("p", configurada.nombre));
      if (notas.length) {
        const historial = elemento("div");
        notas.forEach((nota) => {
          historial.append(elemento("p", `${nota.nota_0_100} · ${nota.registrada_en} · evaluador: ${nota.evaluador_nombre} · registrado por: ${nota.registrada_por_nombre}${nota.corregida_de_id ? ` · corrige #${nota.corregida_de_id}` : ""}`));
          if (nota.motivo) historial.append(elemento("p", `Motivo: ${nota.motivo}`));
          if (nota.observacion) historial.append(elemento("p", nota.observacion));
          if (nota.fisica) historial.append(elemento("p", `${nota.fisica.estado === "NO_CUMPLIDA" ? "No cumplida" : "Cumplida"} · ${nota.fisica.fecha_realizacion || "Sin realización"} · programación #${nota.fisica.programacion_id}`));
          (nota.referencias || []).forEach((ref) => historial.append(elemento("p", `Respaldo: ${ref.nombre} · ${ref.fecha || "Sin fecha"}`)));
        });
        tarjeta.append(botonEdicion(`Historial · ${nombre}`, historial, "Ver historial"));
      }
      const autorizado = ["ADMINISTRADOR", "JEFE_PERSONAL"].includes(rol);
      const tieneRespaldo = fuente !== "ACADEMICA" || (!datos.regla_calculo && datos.formacion.length > 0);
      if (fuente === "ACADEMICA" && datos.regla_calculo) tarjeta.append(elemento("p", "El componente académico procede de formación individual; las notas manuales anteriores se conservan como historial."));
      if (agenda && !agenda.comun) tarjeta.append(elemento("p", "Programa primero la fecha común para registrar un resultado físico."));
      if (datos.periodo.estado === "ACTIVO" && datos.persona.estado === "ACTIVO" && datos.configuracion?.estado === "PUBLICADA" && autorizado && tieneRespaldo && (!agenda || agenda.comun) && datos.habilitaciones?.[fuente]) {
        const form = elemento("form", undefined, "formulario-inline"); const label = elemento("label", "Nota de 0 a 100");
        const nota = elemento("input"); nota.name = "nota_0_100"; nota.type = "number"; nota.min = "0"; nota.max = "100"; nota.step = "0.01"; nota.required = true; nota.value = ultima?.nota_0_100 || ""; label.append(nota); form.append(label);
        let estadoFisico, fechaFisica;
        if (agenda?.comun) {
          const estadoLabel = elemento("label", "Resultado físico"); estadoFisico = elemento("select");
          [["CUMPLIDA", "Cumplida"], ["NO_CUMPLIDA", "No cumplida (cero confirmado)"]].forEach(([valor, nombreEstado]) => { const opcion = elemento("option", nombreEstado); opcion.value = valor; estadoFisico.append(opcion); });
          estadoLabel.append(estadoFisico); const fechaLabel = elemento("label", "Fecha de realización"); fechaFisica = elemento("input"); fechaFisica.type = "date"; fechaFisica.min = datos.periodo.fecha_inicio; fechaFisica.max = datos.periodo.fecha_fin; fechaFisica.value = ultima?.fisica?.fecha_realizacion || ""; fechaLabel.append(fechaFisica);
          const motivoLabel = elemento("label", "Motivo de confirmación o corrección"); const motivo = elemento("textarea"); motivo.name = "motivo"; motivo.maxLength = 2000; motivoLabel.append(motivo);
          function cambiarEstado() { const incumplida = estadoFisico.value === "NO_CUMPLIDA"; nota.readOnly = incumplida; if (incumplida) nota.value = "0"; fechaFisica.disabled = incumplida; fechaFisica.required = !incumplida; motivo.required = incumplida || Boolean(ultima); }
          estadoFisico.addEventListener("change", cambiarEstado); cambiarEstado(); form.append(estadoLabel, fechaLabel, motivoLabel);
        }
        if (fuente === "DESEMPENO_COMANDANTE") {
          const jefeLabel = elemento("label", "Nombre del Comandante evaluador"); const jefeInput = elemento("input"); jefeInput.name = "comandante_nombre"; jefeInput.maxLength = 160; jefeInput.required = true; jefeInput.value = ultima?.evaluador_nombre || ""; jefeLabel.append(jefeInput); form.append(jefeLabel);
        }
        const observado = elemento("label", "Observación propia (opcional)"); const observacion = elemento("textarea"); observacion.name = "observacion"; observacion.maxLength = 2000; observado.append(observacion); form.append(observado);
        let referencias;
        if (fuente === "ACADEMICA") {
          const motivoLabel = elemento("label", "Motivo y respaldo"); const motivo = elemento("textarea"); motivo.name = "motivo"; motivo.maxLength = 2000; motivo.required = true; motivo.value = ultima?.motivo || ""; motivoLabel.append(motivo); form.append(motivoLabel);
          const refs = elemento("label", "Formación personal referenciada (selección múltiple)"); referencias = elemento("select"); referencias.multiple = true; referencias.size = 5; referencias.required = true;
          datos.formacion.forEach((curso) => { const opcion = elemento("option", curso.nombre); opcion.value = curso.id; opcion.selected = (ultima?.referencias || []).some((ref) => ref.capacitacion_id === curso.id); referencias.append(opcion); }); refs.append(referencias); form.append(refs);
        }
        const guardar = elemento("button", ultima ? "Guardar corrección" : "Guardar nota"); form.append(guardar);
        form.addEventListener("submit", async (event) => {
          event.preventDefault(); if (!form.reportValidity()) return; guardar.disabled = true;
          const body = Object.fromEntries(new FormData(form)); body.periodo_id = Number(periodo); body.fuente = fuente;
          if (ultima) body.corregida_de_id = ultima.id;
          if (estadoFisico) body.fisica = { estado: estadoFisico.value, fecha_realizacion: estadoFisico.value === "CUMPLIDA" ? fechaFisica.value : null, programacion_id: agenda.comun.id, reprogramacion_id: agenda.individual?.id ?? null };
          if (referencias) body.capacitaciones = Array.from(referencias.selectedOptions, (opcion) => Number(opcion.value));
          try { await apiJson(`/api/5b/personas/${persona}/notas`, { method: "POST", body }); cerrarEdicion(); await cargarSeguimiento(); }
          catch (error) { mostrarErrorEdicion(error); }
          finally { guardar.disabled = false; }
        });
        tarjeta.append(botonEdicion(`${ultima ? "Corregir" : "Registrar"} · ${nombre}`, form, ultima ? "Corregir" : "Registrar"));
      }
      lista.append(tarjeta);
    });
  }
  seguimientoFiltros.addEventListener("submit", (event) => { event.preventDefault(); if (seguimientoFiltros.reportValidity()) cargarSeguimiento().catch((error) => { lista.replaceChildren(); mensaje.textContent = error.message; }); });
  apiJson("/api/5b/opciones").then(({ personal, periodos }) => {
    personal.forEach((persona) => { const opcion = elemento("option", persona.nombre); opcion.value = persona.id; seguimientoFiltros.elements.persona.append(opcion); });
    periodos.forEach((periodo) => { const opcion = elemento("option", `${periodo.nombre} · ${periodo.estado}`); opcion.value = periodo.id; seguimientoFiltros.elements.periodo.append(opcion); });
    if (!personal.length || !periodos.length) mensaje.textContent = "No hay personal activo o períodos disponibles en tu ámbito.";
  }).catch((error) => { mensaje.textContent = error.message; });
}
