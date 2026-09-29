"use strict";

const loginForm = document.querySelector("#login-form");
const logoutButton = document.querySelector("#logout-button");
const authMessage = document.querySelector("#auth-message");
const csrfToken = document.querySelector('[name="csrf_token"]')?.value;
const appShell = document.querySelector(".app-shell");
const menuButton = document.querySelector("#boton-menu");
const mobileBackdrop = document.querySelector("#fondo-movil");
const registrationForm = document.querySelector("#registro-form");
const managementMessage = document.querySelector("#gestion-mensaje");

async function apiJson(path, options = {}) {
  const headers = { "X-CSRFToken": csrfToken, ...(options.headers || {}) };
  if (options.body && typeof options.body !== "string") {
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
    const data = Object.fromEntries(new FormData(registrationForm).entries());
    delete data.csrf_token;
    try {
      const endpoint = token ? `/api/registro/invitaciones/${encodeURIComponent(token)}` : "/api/registro/solicitudes";
      await apiJson(endpoint, { method: "POST", body: data });
      registrationForm.reset();
      authMessage.textContent = "Solicitud recibida. La cuenta estará disponible después de la aprobación administrativa.";
    } catch (error) { authMessage.textContent = error.message; }
  });
}

const volunteerList = document.querySelector("#voluntarios-lista");
if (volunteerList) {
  const solicitudesLista = document.querySelector("#solicitudes-lista");
  const invitacionForm = document.querySelector("#invitacion-form");
  const invitacionResultado = document.querySelector("#invitacion-resultado");
  let instructoresActivos = [];
  const esAdministrador = document.body.dataset.rol === "ADMINISTRADOR";

  async function cargarVoluntarios() {
    volunteerList.replaceChildren();
    const { voluntarios } = await apiJson("/api/voluntarios");
    if (!voluntarios.length) volunteerList.append(elemento("p", "No hay voluntarios registrados.", "nota-informativa"));
    voluntarios.forEach((voluntario) => {
      const card = elemento("article", undefined, "tarjeta-modulo");
      const contenido = elemento("div");
      contenido.append(elemento("h3", voluntario.nombre), elemento("p", `${voluntario.username} · ${voluntario.correo || "Sin correo"} · ${voluntario.estado}`));
      if (voluntario.experiencia_operaciones) contenido.append(elemento("p", voluntario.experiencia_operaciones));
      card.append(contenido);
      if (voluntario.estado === "ACTIVO") {
        const edit = elemento("details", undefined, "edicion-voluntario");
        edit.append(elemento("summary", "Editar perfil"));
        const form = elemento("form", undefined, "formulario-inline");
        const fields = [["nombre", "Nombre", voluntario.nombre], ["correo", "Correo", voluntario.correo || ""], ["experiencia_operaciones", "Experiencia", voluntario.experiencia_operaciones || ""], ["antiguedad_desde", "Antigüedad desde", voluntario.antiguedad_desde || ""]];
        fields.forEach(([name, label, value]) => {
          const input = elemento("input"); input.name = name; input.value = value;
          if (name === "antiguedad_desde") input.type = "date";
          const caption = elemento("label", label); caption.append(input); form.append(caption);
        });
        if (esAdministrador) {
          const caption = elemento("label", "Instructor asignado");
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
            const body = Object.fromEntries(new FormData(form).entries());
            if ("instructor_id" in body) body.instructor_id = body.instructor_id ? Number(body.instructor_id) : null;
            await apiJson(`/api/voluntarios/${voluntario.id}`, { method: "PATCH", body }); await cargarVoluntarios();
          }
          catch (error) { managementMessage.textContent = error.message; }
        });
        edit.append(form); card.append(edit);
        const deactivate = elemento("button", "Desactivar", "boton-secundario");
        deactivate.addEventListener("click", async () => {
          if (!window.confirm(`¿Desactivar a ${voluntario.nombre}?`)) return;
          try { await apiJson(`/api/voluntarios/${voluntario.id}/desactivar`, { method: "POST" }); await cargarVoluntarios(); }
          catch (error) { managementMessage.textContent = error.message; }
        });
        card.append(deactivate);
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
      card.append(elemento("h3", solicitud.nombre), elemento("p", `${solicitud.username} · ${solicitud.correo || "Sin correo"}`));
      const assign = elemento("select"); assign.name = "instructor_id";
      const none = elemento("option", "Sin instructor asignado"); none.value = ""; assign.append(none);
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

  if (invitacionForm) invitacionForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const data = await apiJson("/api/admin/invitaciones", { method: "POST", body: { correo: invitacionForm.elements.correo.value } });
      invitacionResultado.textContent = `Enlace de un solo uso (expira ${data.expira_en}): ${new URL(data.invitacion_url, window.location.origin).href}`;
      invitacionForm.reset();
    } catch (error) { invitacionResultado.textContent = error.message; }
  });

  const cargarInstructores = esAdministrador
    ? apiJson("/api/admin/instructores").then((data) => { instructoresActivos = data.instructores; })
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
    const { instructores } = await apiJson("/api/admin/instructores");
    if (!instructores.length) instructorList.append(elemento("p", "No hay instructores registrados.", "nota-informativa"));
    instructores.forEach((instructor) => {
      const card = elemento("article", undefined, "tarjeta-modulo");
      card.append(
        elemento("h3", instructor.nombre),
        elemento("p", `${instructor.username} · ${instructor.correo || "Sin correo"}`),
        elemento("p", `${instructor.especialidad || "Sin especialidad"} · ${instructor.voluntarios_activos} voluntarios activos · ${instructor.estado}`),
      );
      const edit = elemento("details", undefined, "edicion-voluntario");
      edit.append(elemento("summary", "Editar perfil"));
      const form = elemento("form", undefined, "formulario-inline");
      [["nombre", "Nombre completo", instructor.nombre], ["correo", "Correo", instructor.correo || ""], ["especialidad", "Especialidad", instructor.especialidad || ""]].forEach(([name, label, value]) => {
        const input = elemento("input"); input.name = name; input.value = value;
        const caption = elemento("label", label); caption.append(input); form.append(caption);
      });
      form.append(elemento("button", "Guardar cambios"));
      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        try {
          await apiJson(`/api/admin/instructores/${instructor.id}`, { method: "PATCH", body: Object.fromEntries(new FormData(form).entries()) });
          listMessage.textContent = "Perfil actualizado.";
          await cargarInstructoresAdmin();
        } catch (error) { listMessage.textContent = error.message; }
      });
      edit.append(form); card.append(edit);
      if (instructor.estado === "ACTIVO") {
        const deactivate = elemento("button", "Desactivar instructor", "boton-secundario");
        deactivate.addEventListener("click", async () => {
          if (!window.confirm(`¿Desactivar a ${instructor.nombre}? Sus voluntarios quedarán sin instructor asignado.`)) return;
          try {
            const result = await apiJson(`/api/admin/instructores/${instructor.id}/desactivar`, { method: "POST" });
            listMessage.textContent = `Instructor desactivado. Voluntarios desvinculados: ${result.voluntarios_desvinculados}.`;
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
    const body = Object.fromEntries(new FormData(instructorForm).entries());
    try {
      await apiJson("/api/admin/instructores", { method: "POST", body });
      instructorForm.reset();
      formMessage.textContent = "Cuenta de instructor creada y activada.";
      await cargarInstructoresAdmin();
    } catch (error) { formMessage.textContent = error.message; }
  });

  cargarInstructoresAdmin().catch((error) => { listMessage.textContent = error.message; });
}
