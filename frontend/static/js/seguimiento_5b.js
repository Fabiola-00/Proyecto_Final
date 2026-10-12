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
    if (actual !== revision) return;
    mensaje.textContent = `${datos.persona.nombre} · ${datos.periodo.nombre} · ${datos.periodo.estado}${datos.configuracion?.estado !== "PUBLICADA" ? " · Sin configuración 5B publicada" : ""}`;
    document.querySelector("#seguimiento-perfil").replaceChildren(elemento("p", `${datos.persona.codigo_instructor || "Sin código"} · ${datos.persona.grado || "Sin grado"} · ${datos.persona.especialidad_principal || "Sin especialidad"}`));
    const formacion = document.querySelector("#seguimiento-formacion"); formacion.replaceChildren(elemento("h3", "Formación registrada"));
    if (!datos.formacion.length) formacion.append(elemento("p", "Sin formación registrada: Académica pendiente."));
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
      const tarjeta = elemento("article", undefined, "tarjeta-modulo"); tarjeta.append(elemento("h3", nombre), elemento("p", ultima ? `Nota: ${ultima.nota_0_100}` : "Pendiente"));
      const configurada = datos.configuracion?.fuentes.find((f) => f.fuente === fuente);
      if (configurada) tarjeta.append(elemento("p", configurada.nombre));
      if (notas.length) {
        const historial = elemento("div");
        notas.forEach((nota) => {
          historial.append(elemento("p", `${nota.nota_0_100} · ${nota.registrada_en} · evaluador: ${nota.evaluador_nombre} · registrado por: ${nota.registrada_por_nombre}${nota.corregida_de_id ? ` · corrige #${nota.corregida_de_id}` : ""}`));
          if (nota.motivo) historial.append(elemento("p", `Motivo: ${nota.motivo}`));
          if (nota.observacion) historial.append(elemento("p", nota.observacion));
          (nota.referencias || []).forEach((ref) => historial.append(elemento("p", `Respaldo: ${ref.nombre} · ${ref.fecha || "Sin fecha"}`)));
        });
        tarjeta.append(botonEdicion(`Historial · ${nombre}`, historial, "Ver historial"));
      }
      const autorizado = ["ADMINISTRADOR", "JEFE_PERSONAL"].includes(rol);
      const tieneRespaldo = fuente !== "ACADEMICA" || datos.formacion.length > 0;
      if (datos.periodo.estado === "ACTIVO" && datos.persona.estado === "ACTIVO" && datos.configuracion?.estado === "PUBLICADA" && autorizado && tieneRespaldo && datos.habilitaciones?.[fuente]) {
        const form = elemento("form", undefined, "formulario-inline"); const label = elemento("label", "Nota de 0 a 100");
        const nota = elemento("input"); nota.name = "nota_0_100"; nota.type = "number"; nota.min = "0"; nota.max = "100"; nota.step = "0.01"; nota.required = true; nota.value = ultima?.nota_0_100 || ""; label.append(nota); form.append(label);
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
