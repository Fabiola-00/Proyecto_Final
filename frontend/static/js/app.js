"use strict";

const loginForm = document.querySelector("#login-form");
const logoutButton = document.querySelector("#logout-button");
const authMessage = document.querySelector("#auth-message");
const csrfToken = document.querySelector('[name="csrf_token"]')?.value;
const appShell = document.querySelector(".app-shell");
const menuButton = document.querySelector("#boton-menu");
const sidebarButton = document.querySelector("#boton-sidebar");
const themeButton = document.querySelector("#boton-tema");
const themeIcon = document.querySelector("#tema-icono");
const themeLabel = document.querySelector("#tema-etiqueta");
const mobileBackdrop = document.querySelector("#fondo-movil");
const registrationForm = document.querySelector("#registro-form");
const managementMessage = document.querySelector("#gestion-mensaje");
const adminProfileForm = document.querySelector("#admin-profile-form");

function leerPreferencia(clave, predeterminado) {
  try { return window.localStorage.getItem(clave) ?? predeterminado; }
  catch { return predeterminado; }
}

function guardarPreferencia(clave, valor) {
  try { window.localStorage.setItem(clave, valor); }
  catch { /* El panel sigue siendo usable aunque el navegador bloquee el almacenamiento local. */ }
}

function aplicarTema(tema) {
  const oscuro = tema === "dark";
  document.documentElement.dataset.theme = oscuro ? "dark" : "light";
  document.documentElement.style.colorScheme = oscuro ? "dark" : "light";
  if (themeButton) {
    themeButton.setAttribute("aria-pressed", String(oscuro));
    themeButton.setAttribute("aria-label", oscuro ? "Cambiar a modo claro" : "Cambiar a modo oscuro");
    if (themeIcon) themeIcon.textContent = oscuro ? "☀" : "◐";
    if (themeLabel) themeLabel.textContent = oscuro ? "Modo claro" : "Modo oscuro";
  }
}

aplicarTema(appShell ? leerPreferencia("sicose-tema", "light") : "light");
if (themeButton) {
  themeButton.addEventListener("click", () => {
    const nuevoTema = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    aplicarTema(nuevoTema);
    guardarPreferencia("sicose-tema", nuevoTema);
  });
}

if (appShell && sidebarButton) {
  const plegado = leerPreferencia("sicose-menu-plegado", "false") === "true";
  appShell.classList.toggle("sidebar-plegado", plegado);
  sidebarButton.setAttribute("aria-expanded", String(!plegado));
  sidebarButton.setAttribute("aria-label", plegado ? "Expandir menú lateral" : "Plegar menú lateral");
  sidebarButton.title = plegado ? "Expandir menú lateral" : "Plegar menú lateral";
  sidebarButton.addEventListener("click", () => {
    const estaPlegado = appShell.classList.toggle("sidebar-plegado");
    sidebarButton.setAttribute("aria-expanded", String(!estaPlegado));
    sidebarButton.setAttribute("aria-label", estaPlegado ? "Expandir menú lateral" : "Plegar menú lateral");
    sidebarButton.title = estaPlegado ? "Expandir menú lateral" : "Plegar menú lateral";
    guardarPreferencia("sicose-menu-plegado", String(estaPlegado));
  });
}

async function apiJson(path, options = {}) {
  const headers = { "X-CSRFToken": csrfToken, ...(options.headers || {}) };
  if (options.body && typeof FormData !== "undefined" && options.body instanceof FormData) {
    delete headers["Content-Type"];
  } else if (options.body && typeof options.body !== "string") {
    headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(options.body);
  }
  const response = await fetch(path, { ...options, headers });
  const tipo = response.headers.get("content-type") || "";
  if (!tipo.includes("application/json")) {
    throw new Error(`El servidor respondió con una página HTML (HTTP ${response.status}) al consultar ${path}. Recarga la página e inténtalo de nuevo.`);
  }
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "No se pudo completar la operación.");
  return data;
}

function elemento(etiqueta, texto, clase) {
  const nodo = document.createElement(etiqueta);
  if (texto !== undefined) nodo.textContent = texto;
  if (clase) nodo.className = clase;
  return nodo;
}

function cerrarMenu() {
  appShell?.classList.remove("menu-abierto");
  menuButton?.setAttribute("aria-expanded", "false");
  menuButton?.setAttribute("aria-label", "Abrir menú de navegación");
  if (mobileBackdrop) mobileBackdrop.hidden = true;
}

if (menuButton && mobileBackdrop) {
  menuButton.addEventListener("click", () => {
    const abierto = appShell.classList.toggle("menu-abierto");
    menuButton.setAttribute("aria-expanded", String(abierto));
    menuButton.setAttribute("aria-label", abierto ? "Cerrar menú de navegación" : "Abrir menú de navegación");
    mobileBackdrop.hidden = !abierto;
  });
  mobileBackdrop.addEventListener("click", cerrarMenu);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") cerrarMenu();
  });
  document.querySelectorAll(".navegacion a").forEach((enlace) => {
    enlace.addEventListener("click", cerrarMenu);
  });
}

if (loginForm) {
  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = document.querySelector("#login-button");
    const username = loginForm.elements.username.value.trim();
    const password = loginForm.elements.password.value;
    authMessage.textContent = "Verificando acceso…";
    button.disabled = true;
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
        body: JSON.stringify({ username, password }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "No fue posible iniciar sesión.");
      window.location.assign(result.redirect_url);
    } catch (error) {
      authMessage.textContent = error.message || "No fue posible conectar con el servidor.";
    } finally {
      button.disabled = false;
    }
  });
}

if (logoutButton) {
  logoutButton.addEventListener("click", async () => {
    logoutButton.disabled = true;
    authMessage.textContent = "Cerrando sesión…";
    try {
      const response = await fetch("/api/auth/logout", {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken },
      });
      if (!response.ok) throw new Error("No fue posible cerrar sesión.");
      window.location.assign("/login");
    } catch (error) {
      authMessage.textContent = error.message;
      logoutButton.disabled = false;
    }
  });
}

if (registrationForm) {
  const token = registrationForm.dataset.token;
  if (token) {
    apiJson(`/api/registro/invitaciones/${encodeURIComponent(token)}`)
      .then((data) => {
        const correo = registrationForm.elements.correo;
        if (data.correo) { correo.value = data.correo; correo.readOnly = true; }
      })
      .catch((error) => {
        authMessage.textContent = error.message;
        registrationForm.querySelector("button").disabled = true;
      });
  }
  registrationForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(registrationForm);
    data.delete("csrf_token");
    try {
      const endpoint = token ? `/api/registro/invitaciones/${encodeURIComponent(token)}` : "/api/registro/solicitudes";
      await apiJson(endpoint, { method: "POST", body: data });
      registrationForm.reset();
      authMessage.textContent = "Solicitud recibida. La cuenta estará disponible después de la aprobación administrativa.";
    } catch (error) { authMessage.textContent = error.message; }
  });
}

if (adminProfileForm) {
  const profileMessage = document.querySelector("#admin-profile-message");
  adminProfileForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(adminProfileForm);
    const nueva = formData.get("nueva_clave");
    const confirmar = formData.get("confirmar_clave");
    const foto = formData.get("foto");
    if (nueva !== confirmar) { profileMessage.textContent = "La confirmación no coincide con la nueva contraseña."; return; }
    if (!foto?.size) formData.delete("foto");
    formData.delete("confirmar_clave");
    try {
      const result = await apiJson("/api/admin/perfil", { method: "PATCH", body: formData });
      profileMessage.textContent = result.requiere_nuevo_login
        ? "Contraseña actualizada. Volverás al inicio de sesión."
        : "Perfil actualizado.";
      window.setTimeout(() => window.location.assign(result.requiere_nuevo_login ? "/login" : window.location.pathname), 1000);
    } catch (error) { profileMessage.textContent = error.message; }
  });
}

const volunteerList = document.querySelector("#voluntarios-lista");
if (volunteerList) {
  const solicitudesLista = document.querySelector("#solicitudes-lista");
  const altaManualForm = document.querySelector("#instructor-voluntario-form");
  const altaManualMensaje = document.querySelector("#instructor-voluntario-form-mensaje");
  let instructoresActivos = [];
  const esAdministrador = document.body.dataset.rol === "ADMINISTRADOR";

  async function cargarVoluntarios() {
    volunteerList.replaceChildren();
    const { voluntarios } = await apiJson("/api/instructores-voluntarios");
    if (!voluntarios.length) volunteerList.append(elemento("p", "No hay Instructores Voluntarios registrados.", "nota-informativa"));
    voluntarios.forEach((voluntario) => {
      const card = elemento("article", undefined, "tarjeta-modulo");
      const contenido = elemento("div");
      if (voluntario.tiene_foto) {
        const foto = elemento("img"); foto.src = `/api/usuarios/${voluntario.id}/foto`; foto.alt = `Foto de ${voluntario.nombre}`; foto.className = "foto-perfil"; contenido.append(foto);
      }
      contenido.append(elemento("h3", voluntario.nombre), elemento("p", `${voluntario.username} · ${voluntario.correo || "Sin correo"} · ${voluntario.estado}`));
      if (voluntario.experiencia_operaciones) contenido.append(elemento("p", voluntario.experiencia_operaciones));
      card.append(contenido);
      if (voluntario.estado === "ACTIVO" || esAdministrador) {
        const edit = elemento("details", undefined, "edicion-voluntario");
        edit.append(elemento("summary", "Editar perfil"));
        const form = elemento("form", undefined, "formulario-inline");
        const fields = [["nombre", "Nombre", voluntario.nombre], ["correo", "Correo", voluntario.correo || ""], ["experiencia_operaciones", "Experiencia", voluntario.experiencia_operaciones || ""], ["antiguedad_desde", "Antigüedad desde", voluntario.antiguedad_desde || ""]];
        fields.forEach(([name, label, value]) => {
          const input = elemento("input"); input.name = name; input.value = value;
          if (name === "antiguedad_desde") input.type = "date";
          const caption = elemento("label", label); caption.append(input); form.append(caption);
        });
        const photoCaption = elemento("label", "Foto de perfil (PNG/JPEG, máximo 3 MiB)");
        const photoInput = elemento("input"); photoInput.type = "file"; photoInput.name = "foto"; photoInput.accept = "image/png,image/jpeg"; photoCaption.append(photoInput); form.append(photoCaption);
        if (esAdministrador) {
          const caption = elemento("label", "Jefe de Personal asignado");
          const select = elemento("select"); select.name = "instructor_id";
          const none = elemento("option", "Sin asignar"); none.value = ""; select.append(none);
          instructoresActivos.forEach((instructor) => {
            const option = elemento("option", instructor.nombre); option.value = instructor.id;
            option.selected = Number(voluntario.instructor_id) === instructor.id;
            select.append(option);
          });
          caption.append(select); form.append(caption);
        }
        const save = elemento("button", "Guardar cambios"); form.append(save);
        form.addEventListener("submit", async (event) => {
          event.preventDefault();
          try {
            const formData = new FormData(form);
            const body = Object.fromEntries(formData.entries());
            const foto = formData.get("foto"); delete body.foto;
            if ("instructor_id" in body) body.instructor_id = body.instructor_id ? Number(body.instructor_id) : null;
            await apiJson(`/api/instructores-voluntarios/${voluntario.id}`, { method: "PATCH", body });
            if (foto?.size) { const carga = new FormData(); carga.append("foto", foto); await apiJson(`/api/usuarios/${voluntario.id}/foto`, { method: "PUT", body: carga }); }
            await cargarVoluntarios();
          }
          catch (error) { managementMessage.textContent = error.message; }
        });
        edit.append(form); card.append(edit);
        if (esAdministrador) {
          const reset = elemento("details", undefined, "edicion-voluntario"); reset.append(elemento("summary", "Restablecer contraseña"));
          const resetForm = elemento("form", undefined, "formulario-inline");
          const field = elemento("label", "Nueva contraseña (mínimo 12 caracteres)"); const password = elemento("input"); password.type = "password"; password.name = "password"; password.minLength = 12; password.maxLength = 256; password.required = true; password.autocomplete = "new-password"; field.append(password); resetForm.append(field, elemento("button", "Restablecer clave"));
          resetForm.addEventListener("submit", async (event) => { event.preventDefault(); try { await apiJson(`/api/admin/usuarios/${voluntario.id}/restablecer-clave`, { method: "POST", body: { password: password.value } }); resetForm.reset(); managementMessage.textContent = "Contraseña restablecida; las sesiones anteriores quedaron invalidadas."; } catch (error) { managementMessage.textContent = error.message; } });
          reset.append(resetForm); card.append(reset);
        }
        if (voluntario.estado === "ACTIVO") {
          const deactivate = elemento("button", "Desactivar", "boton-secundario");
          deactivate.addEventListener("click", async () => {
            if (!window.confirm(`¿Desactivar a ${voluntario.nombre}?`)) return;
            try { await apiJson(`/api/instructores-voluntarios/${voluntario.id}/desactivar`, { method: "POST" }); await cargarVoluntarios(); }
            catch (error) { managementMessage.textContent = error.message; }
          });
          card.append(deactivate);
        }
      }
      volunteerList.append(card);
    });
  }

  async function cargarSolicitudes() {
    if (!solicitudesLista) return;
    solicitudesLista.replaceChildren();
    const { solicitudes } = await apiJson("/api/admin/solicitudes");
    if (!solicitudes.length) solicitudesLista.append(elemento("p", "No hay solicitudes pendientes.", "nota-informativa"));
    solicitudes.forEach((solicitud) => {
      const card = elemento("article", undefined, "tarjeta-modulo");
      if (solicitud.tiene_foto) { const foto = elemento("img"); foto.src = `/api/usuarios/${solicitud.usuario_id}/foto`; foto.alt = `Foto de ${solicitud.nombre}`; foto.className = "foto-perfil"; card.append(foto); }
      card.append(elemento("h3", solicitud.nombre), elemento("p", `${solicitud.username} · ${solicitud.correo || "Sin correo"}`));
      const assign = elemento("select"); assign.name = "instructor_id";
      const none = elemento("option", "Sin Jefe de Personal asignado"); none.value = ""; assign.append(none);
      instructoresActivos.forEach((instructor) => { const option = elemento("option", instructor.nombre); option.value = instructor.id; assign.append(option); });
      card.append(assign);
      [["aprobar", "Aprobar"], ["rechazar", "Rechazar"]].forEach(([accion, texto]) => {
        const button = elemento("button", texto, accion === "rechazar" ? "boton-secundario" : "");
        button.addEventListener("click", async () => {
          try {
            const body = accion === "aprobar" && assign.value ? { instructor_id: Number(assign.value) } : {};
            await apiJson(`/api/admin/solicitudes/${solicitud.id}/${accion}`, { method: "POST", body });
            await Promise.all([cargarSolicitudes(), cargarVoluntarios()]);
          } catch (error) { managementMessage.textContent = error.message; }
        });
        card.append(button);
      });
      solicitudesLista.append(card);
    });
  }

  if (altaManualForm) altaManualForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const data = await apiJson("/api/admin/instructores-voluntarios", { method: "POST", body: new FormData(altaManualForm) });
      altaManualForm.reset();
      altaManualMensaje.textContent = data.mensaje || "Instructor Voluntario creado y activado.";
      await cargarVoluntarios();
    } catch (error) { altaManualMensaje.textContent = error.message; }
  });

  const cargarInstructores = esAdministrador
    ? apiJson("/api/admin/jefes-personal").then((data) => {
      instructoresActivos = data.instructores.filter((instructor) => instructor.estado === "ACTIVO");
      const asignado = altaManualForm?.elements.instructor_id;
      if (asignado) {
        asignado.replaceChildren(elemento("option", "Sin asignar"));
        asignado.options[0].value = "";
        instructoresActivos.forEach((instructor) => {
          const option = elemento("option", instructor.nombre); option.value = instructor.id; asignado.append(option);
        });
      }
    })
    : Promise.resolve();
  cargarInstructores.then(() => Promise.all([cargarVoluntarios(), cargarSolicitudes()]))
    .catch((error) => { managementMessage.textContent = error.message; });
}

const instructorForm = document.querySelector("#instructor-form");
const instructorList = document.querySelector("#instructores-lista");
if (instructorForm && instructorList) {
  const formMessage = document.querySelector("#instructor-form-mensaje");
  const listMessage = document.querySelector("#instructores-mensaje");

  async function cargarInstructoresAdmin() {
    instructorList.replaceChildren();
    const { instructores } = await apiJson("/api/admin/jefes-personal");
    if (!instructores.length) instructorList.append(elemento("p", "No hay Jefes de Personal registrados.", "nota-informativa"));
    instructores.forEach((instructor) => {
      const card = elemento("article", undefined, "tarjeta-modulo");
      card.append(
        elemento("h3", instructor.nombre),
        elemento("p", `${instructor.username} · ${instructor.correo || "Sin correo"}`),
        elemento("p", `${instructor.especialidad || "Sin especialidad"} · ${instructor.voluntarios_activos} Instructores Voluntarios activos · ${instructor.estado}`),
      );
      const edit = elemento("details", undefined, "edicion-voluntario");
      edit.append(elemento("summary", "Editar perfil"));
      const form = elemento("form", undefined, "formulario-inline");
      [["nombre", "Nombre completo", instructor.nombre], ["correo", "Correo", instructor.correo || ""], ["especialidad", "Especialidad", instructor.especialidad || ""]].forEach(([name, label, value]) => {
        const input = elemento("input"); input.name = name; input.value = value;
        const caption = elemento("label", label); caption.append(input); form.append(caption);
      });
      const photoCaption = elemento("label", "Foto de perfil (PNG/JPEG, máximo 3 MiB)"); const photoInput = elemento("input"); photoInput.type = "file"; photoInput.name = "foto"; photoInput.accept = "image/png,image/jpeg"; photoCaption.append(photoInput); form.append(photoCaption);
      form.append(elemento("button", "Guardar cambios"));
      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        try {
          const formData = new FormData(form); const body = Object.fromEntries(formData.entries()); const foto = formData.get("foto"); delete body.foto;
          await apiJson(`/api/admin/jefes-personal/${instructor.id}`, { method: "PATCH", body });
          if (foto?.size) { const carga = new FormData(); carga.append("foto", foto); await apiJson(`/api/usuarios/${instructor.id}/foto`, { method: "PUT", body: carga }); }
          listMessage.textContent = "Perfil actualizado.";
          await cargarInstructoresAdmin();
        } catch (error) { listMessage.textContent = error.message; }
      });
      edit.append(form); card.append(edit);
      const reset = elemento("details", undefined, "edicion-voluntario"); reset.append(elemento("summary", "Restablecer contraseña"));
      const resetForm = elemento("form", undefined, "formulario-inline"); const passwordCaption = elemento("label", "Nueva contraseña (mínimo 12 caracteres)"); const password = elemento("input"); password.type = "password"; password.name = "password"; password.minLength = 12; password.maxLength = 256; password.required = true; password.autocomplete = "new-password"; passwordCaption.append(password); resetForm.append(passwordCaption, elemento("button", "Restablecer clave"));
      resetForm.addEventListener("submit", async (event) => { event.preventDefault(); try { await apiJson(`/api/admin/usuarios/${instructor.id}/restablecer-clave`, { method: "POST", body: { password: password.value } }); resetForm.reset(); listMessage.textContent = "Contraseña restablecida; las sesiones anteriores quedaron invalidadas."; } catch (error) { listMessage.textContent = error.message; } }); reset.append(resetForm); card.append(reset);
      if (instructor.estado === "ACTIVO") {
        const deactivate = elemento("button", "Desactivar Jefe de Personal", "boton-secundario");
        deactivate.addEventListener("click", async () => {
          if (!window.confirm(`¿Desactivar a ${instructor.nombre}? Sus Instructores Voluntarios quedarán sin Jefe de Personal asignado.`)) return;
          try {
            const result = await apiJson(`/api/admin/jefes-personal/${instructor.id}/desactivar`, { method: "POST" });
            listMessage.textContent = `Jefe de Personal desactivado. Instructores Voluntarios desvinculados: ${result.voluntarios_desvinculados}.`;
            await cargarInstructoresAdmin();
          } catch (error) { listMessage.textContent = error.message; }
        });
        card.append(deactivate);
      }
      instructorList.append(card);
    });
  }

  instructorForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const body = new FormData(instructorForm); body.delete("csrf_token");
    try {
      await apiJson("/api/admin/jefes-personal", { method: "POST", body });
      instructorForm.reset();
      formMessage.textContent = "Cuenta de Jefe de Personal creada y activada.";
      await cargarInstructoresAdmin();
    } catch (error) { formMessage.textContent = error.message; }
  });

  cargarInstructoresAdmin().catch((error) => { listMessage.textContent = error.message; });
}

const evaluationForm = document.querySelector("#evaluacion-form");
if (evaluationForm) {
  const periodForm = document.querySelector("#periodo-form");
  const periodMessage = document.querySelector("#periodo-mensaje");
  const periodsList = document.querySelector("#periodos-lista");
  const evaluationList = document.querySelector("#evaluaciones-lista");
  const assignmentForm = document.querySelector("#asignacion-form");
  const assignmentList = document.querySelector("#asignaciones-admin-lista");
  const formMessage = document.querySelector("#evaluacion-form-mensaje");
  const assignmentMessage = document.querySelector("#asignacion-mensaje");

  async function cargarCatalogo() {
    const { evaluaciones } = await apiJson("/api/admin/evaluaciones");
    evaluationList.replaceChildren();
    evaluaciones.forEach((item) => {
      const card = elemento("article", undefined, "tarjeta-modulo");
      card.append(elemento("h3", item.nombre), elemento("p", `${item.codigo} · ${item.categoria} · ${item.activo ? "Activa" : "Inactiva"}`));
      if (item.categoria === "PSICOMETRICA") card.append(elemento("p", `Instrumento: ${item.estado_instrumento || "sin autorización"}`));
      const editor = elemento("details", undefined, "edicion-voluntario"); editor.append(elemento("summary", "Editar nombre"));
      const editForm = elemento("form", undefined, "formulario-inline");
      const name = elemento("input"); name.name = "nombre"; name.value = item.nombre; name.maxLength = 160; name.required = true;
      const label = elemento("label", "Nombre"); label.append(name); editForm.append(label, elemento("button", "Guardar"));
      editForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        try { await apiJson(`/api/admin/evaluaciones/${item.id}`, { method: "PATCH", body: { nombre: name.value, activo: Boolean(item.activo) } }); await cargarCatalogo(); }
        catch (error) { formMessage.textContent = error.message; }
      });
      editor.append(editForm); card.append(editor);
      const button = elemento("button", item.activo ? "Desactivar" : "Activar", item.activo ? "boton-secundario" : "");
      button.addEventListener("click", async () => {
        try { await apiJson(`/api/admin/evaluaciones/${item.id}`, { method: "PATCH", body: { activo: !item.activo } }); await cargarCatalogo(); }
        catch (error) { formMessage.textContent = error.message; }
      });
      card.append(button); evaluationList.append(card);
    });
    const active = evaluaciones.filter((item) => item.activo);
    const select = assignmentForm.elements.evaluacion_id;
    select.replaceChildren();
    active.forEach((item) => { const option = elemento("option", `${item.nombre} · ${item.categoria}`); option.value = item.id; select.append(option); });
  }

  async function cargarAsignacionesAdmin() {
    const { asignaciones } = await apiJson("/api/jefe-personal/asignaciones");
    assignmentList.replaceChildren();
    asignaciones.forEach((item) => assignmentList.append(elemento("article", `${item.voluntario} · ${item.periodo} · ${item.evaluacion} · ${item.estado}`, "tarjeta-modulo")));
  }

  async function cargarPeriodos() {
    const { periodos } = await apiJson("/api/admin/periodos"); periodsList.replaceChildren();
    periodos.forEach((period) => periodsList.append(elemento("article", `${period.nombre} · ${period.fecha_inicio} – ${period.fecha_fin} · ${period.estado}`, "tarjeta-modulo")));
    const select = assignmentForm.elements.periodo_id; select.replaceChildren();
    periodos.filter((period) => period.estado === "ACTIVO").forEach((period) => { const option = elemento("option", period.nombre); option.value = period.id; select.append(option); });
  }

  periodForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await apiJson("/api/admin/periodos", { method: "POST", body: Object.fromEntries(new FormData(periodForm).entries()) });
      periodForm.reset(); periodMessage.textContent = "Período creado.";
      await cargarPeriodos();
    } catch (error) { periodMessage.textContent = error.message; }
  });

  evaluationForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await apiJson("/api/admin/evaluaciones", { method: "POST", body: Object.fromEntries(new FormData(evaluationForm).entries()) });
      evaluationForm.reset(); formMessage.textContent = "Evaluación creada inactiva.";
      await cargarCatalogo();
    } catch (error) { formMessage.textContent = error.message; }
  });

  assignmentForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const body = Object.fromEntries(new FormData(assignmentForm).entries());
    ["voluntario_id", "periodo_id", "evaluacion_id"].forEach((key) => { body[key] = Number(body[key]); });
    try { await apiJson("/api/admin/asignaciones", { method: "POST", body }); assignmentMessage.textContent = "Evaluación asignada (inicia deshabilitada)."; await cargarAsignacionesAdmin(); }
    catch (error) { assignmentMessage.textContent = error.message; }
  });

  Promise.all([
    cargarCatalogo(), cargarAsignacionesAdmin(),
    apiJson("/api/admin/instructores-voluntarios-activos").then(({ voluntarios }) => {
      const select = assignmentForm.elements.voluntario_id;
      select.replaceChildren(); voluntarios.forEach((v) => { const option = elemento("option", v.nombre); option.value = v.id; select.append(option); });
    }),
    cargarPeriodos(),
  ]).catch((error) => { assignmentMessage.textContent = error.message; });
}

const attendanceForm = document.querySelector("#asistencias-form");
if (attendanceForm) {
  const attendanceRows = document.querySelector("#asistencias-voluntarios");
  const attendanceMessage = document.querySelector("#asistencias-mensaje");
  const attendanceHistory = document.querySelector("#asistencias-historial");
  const courseForm = document.querySelector("#capacitacion-form");
  const courseMessage = document.querySelector("#capacitacion-mensaje");

  async function cargarEquipoAsistencia() {
    const { voluntarios } = await apiJson("/api/instructores-voluntarios");
    const activos = voluntarios.filter((voluntario) => voluntario.estado === "ACTIVO");
    attendanceRows.replaceChildren();
    const courseSelect = courseForm.elements.voluntario_id; courseSelect.replaceChildren();
    activos.forEach((voluntario) => {
      const option = elemento("option", voluntario.nombre); option.value = voluntario.id; courseSelect.append(option);
      const card = elemento("label", `${voluntario.nombre} · Asistencia`, "tarjeta-modulo");
      const select = elemento("select"); select.name = "estado"; select.dataset.volunteerId = voluntario.id; select.required = true;
      const prompt = elemento("option", "Selecciona el estado"); prompt.value = ""; prompt.selected = true; prompt.disabled = true; select.append(prompt);
      [["PRESENTE", "Presente"], ["AUSENTE", "Ausente"], ["JUSTIFICADO", "Justificado"]].forEach(([value, label]) => { const opt = elemento("option", label); opt.value = value; select.append(opt); });
      card.append(select); attendanceRows.append(card);
    });
  }

  async function cargarHistorialAsistencia() {
    const { asistencias } = await apiJson("/api/jefe-personal/asistencias"); attendanceHistory.replaceChildren();
    if (!asistencias.length) attendanceHistory.append(elemento("p", "Sin registros de asistencia.", "nota-informativa"));
    asistencias.slice(0, 30).forEach((row) => attendanceHistory.append(elemento("article", `${row.fecha} · ${row.actividad} · ${row.voluntario}: ${row.estado}`, "tarjeta-modulo")));
  }

  attendanceForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(attendanceForm);
    const entries = [...attendanceRows.querySelectorAll("select")].map((select) => ({ voluntario_id: Number(select.dataset.volunteerId), estado: select.value }));
    try {
      const result = await apiJson("/api/jefe-personal/asistencias", { method: "POST", body: { fecha: data.get("fecha"), actividad: data.get("actividad"), asistencias: entries } });
      attendanceMessage.textContent = `Registros guardados: ${result.registrados}.`; await cargarHistorialAsistencia();
    } catch (error) { attendanceMessage.textContent = error.message; }
  });

  courseForm.addEventListener("submit", async (event) => {
    event.preventDefault(); const data = Object.fromEntries(new FormData(courseForm).entries());
    const volunteerId = Number(data.voluntario_id); delete data.voluntario_id;
    try { await apiJson(`/api/jefe-personal/instructores-voluntarios/${volunteerId}/capacitaciones`, { method: "POST", body: data }); courseForm.reset(); courseMessage.textContent = "Capacitación registrada."; }
    catch (error) { courseMessage.textContent = error.message; }
  });

  Promise.all([cargarEquipoAsistencia(), cargarHistorialAsistencia()]).catch((error) => { attendanceMessage.textContent = error.message; });
}

const gradeSelect = document.querySelector("#calificacion-asignacion");
if (gradeSelect) {
  const gradeForm = document.querySelector("#calificacion-form");
  const gradeHistory = document.querySelector("#calificacion-historial");
  const psychometricList = document.querySelector("#psicometricas-lista");
  const gradeMessage = document.querySelector("#calificacion-mensaje");
  let assignmentsById = new Map();
  let historiesByAssignment = new Map();

  async function cargarAsignacionesInstructor() {
    const { asignaciones } = await apiJson("/api/jefe-personal/asignaciones");
    assignmentsById = new Map(asignaciones.map((item) => [String(item.id), item]));
    gradeSelect.replaceChildren(elemento("option", "Selecciona una evaluación"));
    psychometricList.replaceChildren();
    asignaciones.filter((item) => item.categoria === "PSICOMETRICA").forEach((item) => {
      const card = elemento("article", undefined, "tarjeta-modulo");
      card.append(elemento("h3", `${item.voluntario} · ${item.evaluacion}`), elemento("p", `${item.periodo} · ${item.estado}`));
      const results = elemento("div");
      const viewResults = elemento("button", "Ver intentos y resultados", "boton-secundario");
      viewResults.addEventListener("click", async () => {
        try {
          const { intentos } = await apiJson(`/api/jefe-personal/asignaciones/${item.id}/resultados`);
          results.replaceChildren();
          if (!intentos.length) results.append(elemento("p", "Sin intentos registrados."));
          intentos.forEach((attempt) => results.append(elemento("p", `Intento ${attempt.numero} · ${attempt.estado} · ${attempt.enviado_en || "Sin envío"} · ${attempt.nota_0_100 === null ? "Sin resultado" : `Resultado ${attempt.nota_0_100}`}`)));
        } catch (error) { gradeMessage.textContent = error.message; }
      });
      card.append(viewResults, results);
      const button = elemento("button", item.estado === "HABILITADA" ? "Desactivar prueba" : "Activar prueba", item.estado === "HABILITADA" ? "boton-secundario" : "");
      button.addEventListener("click", async () => {
        const estado = item.estado === "HABILITADA" ? "NO_HABILITADA" : "HABILITADA";
        try { await apiJson(`/api/jefe-personal/asignaciones/${item.id}/estado`, { method: "PATCH", body: { estado } }); await cargarAsignacionesInstructor(); }
        catch (error) { gradeMessage.textContent = error.message; }
      });
      card.append(button); psychometricList.append(card);
    });
    asignaciones.filter((item) => item.categoria !== "PSICOMETRICA").forEach((item) => {
      const option = elemento("option", `${item.voluntario} · ${item.evaluacion} · ${item.periodo}`); option.value = item.id; gradeSelect.append(option);
    });
  }

  async function cargarHistorialNota(assignmentId) {
    gradeHistory.replaceChildren();
    const { historial } = await apiJson(`/api/jefe-personal/asignaciones/${assignmentId}/calificaciones`);
    historiesByAssignment.set(String(assignmentId), historial);
    historial.forEach((record) => {
      const detalle = `Nota ${record.nota_0_100} · ${record.registrada_en} · ${record.registrada_por}${record.corregida_de_id ? ` · corrección de #${record.corregida_de_id}` : ""}`;
      gradeHistory.append(elemento("article", record.observacion ? `${detalle} · ${record.observacion}` : detalle, "tarjeta-modulo"));
    });
  }

  gradeSelect.addEventListener("change", async () => {
    gradeForm.hidden = !gradeSelect.value;
    if (!gradeSelect.value) { gradeHistory.replaceChildren(); return; }
    try { await cargarHistorialNota(gradeSelect.value); }
    catch (error) { gradeMessage.textContent = error.message; }
  });

  gradeForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const history = historiesByAssignment.get(gradeSelect.value) || [];
    const latest = history[history.length - 1];
    const body = Object.fromEntries(new FormData(gradeForm).entries()); body.nota_0_100 = Number(body.nota_0_100);
    if (latest) body.corregida_de_id = latest.id;
    try {
      await apiJson(`/api/jefe-personal/asignaciones/${gradeSelect.value}/calificaciones`, { method: "POST", body });
      gradeForm.reset(); gradeMessage.textContent = latest ? "Corrección guardada; se conservó la nota anterior." : "Nota guardada.";
      await Promise.all([cargarHistorialNota(gradeSelect.value), cargarAsignacionesInstructor()]);
    } catch (error) { gradeMessage.textContent = error.message; }
  });

  cargarAsignacionesInstructor().catch((error) => { gradeMessage.textContent = error.message; });
}
