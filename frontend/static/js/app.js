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

aplicarTema(appShell || loginForm ? leerPreferencia("sicose-tema", "light") : "light");
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

let modalEdicion;
let formularioModal;
function cerrarEdicion() { if (modalEdicion?.open) modalEdicion.close(); }
function mostrarErrorEdicion(error) {
  if (modalEdicion?.open) modalEdicion.querySelector(".modal-mensaje").textContent = error.message;
}
function botonEdicion(titulo, formulario, etiqueta) {
  const boton = elemento("button", etiqueta, "boton-editar"); boton.type = "button";
  boton.addEventListener("click", () => {
    if (!modalEdicion) {
      modalEdicion = elemento("dialog", undefined, "modal-edicion");
      modalEdicion.setAttribute("aria-labelledby", "modal-edicion-titulo");
      const cabecera = elemento("header", undefined, "modal-cabecera");
      const encabezado = elemento("h2"); encabezado.id = "modal-edicion-titulo";
      const cerrar = elemento("button", "×", "modal-cerrar"); cerrar.type = "button"; cerrar.setAttribute("aria-label", "Cerrar formulario");
      cerrar.addEventListener("click", cerrarEdicion); cabecera.append(encabezado, cerrar);
      const contenido = elemento("div", undefined, "modal-contenido");
      const mensaje = elemento("p", undefined, "mensaje modal-mensaje"); mensaje.setAttribute("role", "alert");
      const pie = elemento("footer", undefined, "modal-pie");
      const cancelar = elemento("button", "Cancelar", "boton-editar"); cancelar.type = "button"; cancelar.addEventListener("click", cerrarEdicion); pie.append(cancelar);
      modalEdicion.append(cabecera, mensaje, contenido, pie); document.body.append(modalEdicion);
      modalEdicion.addEventListener("close", () => {
        document.body.classList.remove("modal-abierto");
        formularioModal?.querySelectorAll("input[type='password'], input[type='file']").forEach((campo) => { campo.value = ""; });
      });
    }
    formularioModal = formulario;
    modalEdicion.querySelector("h2").textContent = titulo;
    modalEdicion.querySelector(".modal-mensaje").textContent = "";
    modalEdicion.querySelector(".modal-contenido").replaceChildren(formulario);
    document.body.classList.add("modal-abierto"); modalEdicion.showModal();
  });
  return boton;
}

function inicialCodigo(valor) {
  const primera = String(valor || "").trim().normalize("NFKD").replace(/[\u0300-\u036f]/g, "")[0] || "";
  return /^[A-Za-z]$/.test(primera) ? primera.toUpperCase() : "";
}

function configurarVistaPreviaCodigo(formulario) {
  if (!formulario) return;
  const actualizar = () => {
    const { nombres, apellido_paterno: paterno, apellido_materno: materno, fecha_nacimiento: fecha } = formulario.elements;
    const iniciales = [inicialCodigo(nombres?.value), inicialCodigo(paterno?.value), inicialCodigo(materno?.value)];
    const salida = formulario.querySelector("[data-codigo-instructor]");
    if (!salida) return;
    const partesFecha = fecha?.value?.split("-");
    salida.textContent = iniciales.every(Boolean) && partesFecha?.length === 3
      ? `${iniciales.join("")}-${partesFecha[2]}${partesFecha[1]}${partesFecha[0].slice(-2)}`
      : "Completa nombres y fecha de nacimiento";
  };
  ["nombres", "apellido_paterno", "apellido_materno", "fecha_nacimiento"].forEach((campo) => {
    formulario.elements[campo]?.addEventListener("input", actualizar);
    formulario.elements[campo]?.addEventListener("change", actualizar);
  });
  actualizar();
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
  configurarVistaPreviaCodigo(registrationForm);
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
    if (!registrationForm.reportValidity()) return;
    const data = new FormData(registrationForm);
    data.delete("csrf_token");
    try {
      const endpoint = token ? `/api/registro/invitaciones/${encodeURIComponent(token)}` : "/api/registro/solicitudes";
      const resultado = await apiJson(endpoint, { method: "POST", body: data });
      registrationForm.reset();
      authMessage.textContent = `Solicitud recibida. Código de Instructor: ${resultado.codigo_instructor}. La cuenta estará disponible después de la aprobación administrativa.`;
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

const paisesLatinoamerica = ["Argentina", "Bolivia", "Brasil", "Chile", "Colombia", "Costa Rica", "Cuba", "Ecuador", "El Salvador", "Guatemala", "Haití", "Honduras", "México", "Nicaragua", "Panamá", "Paraguay", "Perú", "República Dominicana", "Uruguay", "Venezuela"];
const departamentosBolivia = ["Beni", "Chuquisaca", "Cochabamba", "La Paz", "Oruro", "Pando", "Potosí", "Santa Cruz", "Tarija"];
function configurarResidencia(formulario) {
  if (!formulario) return;
  const pais = formulario.elements.pais_residencia;
  if (!pais) return;
  function actualizar(limpiar = false) {
    const anterior = formulario.elements.departamento_residencia;
    const valor = limpiar ? "" : anterior.value;
    const nuevo = elemento(pais.value === "Bolivia" ? "select" : "input"); nuevo.name = "departamento_residencia";
    if (pais.value === "Bolivia") {
      nuevo.append(elemento("option", "Sin registrar")); nuevo.options[0].value = "";
      departamentosBolivia.forEach((nombre) => {const opcion=elemento("option",nombre);opcion.value=nombre;nuevo.append(opcion);});
    } else {nuevo.type="text";nuevo.maxLength=160;nuevo.placeholder="Departamento / provincia";}
    nuevo.required=anterior.required;nuevo.value=valor;anterior.replaceWith(nuevo);
  }
  pais.addEventListener("change",()=>actualizar(true));
  formulario.addEventListener("reset",()=>window.setTimeout(()=>actualizar(true),0));actualizar();
}

function iconoAccionInstructor(boton, tipo, etiqueta) {
  const trazos = {
    ver: ["M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7", "M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0"],
    asignar: ["M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2", "M13 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0", "M20 8v6", "M17 11h6"],
    editar: ["M16 3l5 5-12 12-6 1 1-6L16 3Z", "M13 6l5 5"],
    desactivar: ["M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0", "M6 6l12 12"],
    retirar: ["M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2", "M13 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0", "M17 11h6"],
    activar: ["M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0", "M8 12l3 3 5-6"]
  };
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 24 24"); svg.setAttribute("aria-hidden", "true"); svg.setAttribute("focusable", "false");
  svg.setAttribute("fill", "none"); svg.setAttribute("stroke", "currentColor"); svg.setAttribute("stroke-width", "1.8");
  svg.setAttribute("stroke-linecap", "round"); svg.setAttribute("stroke-linejoin", "round");
  trazos[tipo].forEach((d) => { const path = document.createElementNS("http://www.w3.org/2000/svg", "path"); path.setAttribute("d", d); svg.append(path); });
  boton.replaceChildren(svg); boton.classList.add("accion-icono"); boton.title = etiqueta; boton.setAttribute("aria-label", etiqueta);
  return boton;
}

const volunteerList = document.querySelector("#voluntarios-lista");
if (volunteerList) {
  const solicitudesLista = document.querySelector("#solicitudes-lista");
  const altaManualForm = document.querySelector("#instructor-voluntario-form");
  const altaManualMensaje = document.querySelector("#instructor-voluntario-form-mensaje");
  configurarVistaPreviaCodigo(altaManualForm);
  configurarResidencia(altaManualForm);
  let instructoresActivos = [];
  const esAdministrador = document.body.dataset.rol === "ADMINISTRADOR";

  async function cargarVoluntarios() {
    volunteerList.replaceChildren();
    const { voluntarios } = await apiJson("/api/instructores-voluntarios");
    if (!voluntarios.length) {
      const fila = elemento("tr");
      const celda = elemento("td", "No hay Instructores Voluntarios registrados.", "tabla-vacia");
      celda.colSpan = 7; fila.append(celda); volunteerList.append(fila);
    }
    voluntarios.forEach((voluntario) => {
      const fila = elemento("tr");
      const perfil = elemento("td", undefined, "celda-perfil");
      const contenidoPerfil = elemento("div", undefined, "perfil-en-fila");
      if (voluntario.tiene_foto) {
        const foto = elemento("img"); foto.src = `/api/usuarios/${voluntario.id}/foto`; foto.alt = `Foto de ${voluntario.nombre}`; foto.className = "foto-perfil"; contenidoPerfil.append(foto);
      } else contenidoPerfil.append(elemento("span", voluntario.nombre.slice(0, 1).toUpperCase(), "avatar avatar-perfil"));
      contenidoPerfil.append(elemento("strong", voluntario.nombre));
      perfil.append(contenidoPerfil);
      const estado = elemento("td");
      estado.append(elemento("span", voluntario.estado, `estado-tabla estado-${voluntario.estado.toLowerCase()}`));
      const acciones = elemento("td", undefined, "acciones-tabla");
      const contenidoAcciones = elemento("div", undefined, "acciones-en-fila"); acciones.append(contenidoAcciones);
      const fechaNacimiento = voluntario.fecha_nacimiento ? voluntario.fecha_nacimiento.split("-").reverse().join("/") : "Pendiente de actualizar";
      const antiguedad = voluntario.antiguedad_anos == null ? "No disponible" : `${voluntario.antiguedad_anos} años`;
      fila.append(perfil, elemento("td", voluntario.codigo_instructor || "Pendiente"), elemento("td", voluntario.grado || "Sin registrar"), elemento("td", voluntario.especialidad_principal || "Sin especialidad registrada"), estado, elemento("td", antiguedad), acciones);
      const consulta = elemento("div", undefined, "consulta-perfil");
      if (voluntario.tiene_foto) {
        const foto = elemento("img"); foto.src = `/api/usuarios/${voluntario.id}/foto`; foto.alt = `Foto de ${voluntario.nombre}`; foto.className = "foto-perfil"; consulta.append(foto);
      }
      const datosPerfil = elemento("dl", undefined, "datos-perfil");
      const camposPerfil = [
        ["Nombre completo", voluntario.nombre], ["Nombres", voluntario.nombres],
        ["Apellido paterno", voluntario.apellido_paterno], ["Apellido materno", voluntario.apellido_materno],
        ["Fecha de nacimiento", fechaNacimiento], ["Código", voluntario.codigo_instructor], ["Grado", voluntario.grado],
        ["Especialidad principal", voluntario.especialidad_principal],
        ["Especialidades secundarias", (voluntario.especialidades_secundarias || []).join(", ")],
        ["Estado", voluntario.estado], ["Nombre de usuario", voluntario.username], ["Correo electrónico", voluntario.correo],
        ["Nacionalidad", voluntario.nacionalidad], ["País de residencia registrado", voluntario.pais_residencia],
        ["Departamento", voluntario.departamento_residencia], ["Año de incorporación registrado", voluntario.ano_incorporacion],
        ["Fecha de incorporación", voluntario.fecha_incorporacion], ["Antigüedad desde registrada", voluntario.antiguedad_desde], ["Antigüedad calculada", antiguedad],
        ["Experiencia en operaciones", voluntario.experiencia_operaciones],
        ["Jefe de Personal asignado", instructoresActivos.find((jefe) => jefe.id === Number(voluntario.instructor_id))?.nombre || (voluntario.instructor_id ? `Asignación ${voluntario.instructor_id}` : "Sin asignar")]
      ];
      camposPerfil.forEach(([etiqueta, valor]) => { const dato = elemento("div"); dato.append(elemento("dt", etiqueta), elemento("dd", valor == null || valor === "" ? "Sin registrar" : String(valor))); datosPerfil.append(dato); });
      consulta.append(datosPerfil);
      contenidoAcciones.append(iconoAccionInstructor(botonEdicion(`Ver Instructor Voluntario · ${voluntario.nombre}`, consulta, "Ver"), "ver", `Ver ${voluntario.nombre}`));
      if (voluntario.estado === "ACTIVO" || esAdministrador) {

        const form = elemento("form", undefined, "formulario-inline");
        const fields = [["nombres", "Nombres", voluntario.nombres || ""], ["apellido_paterno", "Apellido paterno", voluntario.apellido_paterno || ""], ["apellido_materno", "Apellido materno", voluntario.apellido_materno || ""], ["fecha_nacimiento", "Fecha de nacimiento", voluntario.fecha_nacimiento || ""], ["correo", "Correo", voluntario.correo || ""], ["experiencia_operaciones", "Experiencia", voluntario.experiencia_operaciones || ""], ["fecha_incorporacion", "Fecha de incorporación", voluntario.fecha_incorporacion || ""]];
        fields.forEach(([name, label, value]) => {
          const input = elemento("input"); input.name = name; input.value = value;
          if (name === "fecha_incorporacion" || name === "fecha_nacimiento") input.type = "date";
          if (["nombres", "apellido_paterno", "apellido_materno", "fecha_nacimiento"].includes(name)) input.required = true;
          const caption = elemento("label", label); caption.append(input); form.append(caption);
        });
        const gradoLabel = elemento("label", "Grado"); const grado = elemento("select"); grado.name = "grado";
        grado.append(elemento("option", "Sin registrar")); grado.options[0].value = "";
        ["Instructor Inicial", "Instructor Segundo", "Instructor Primero", "Instructor Principal", "Instructor Mayor"].forEach((valor) => { const opcion = elemento("option", valor); opcion.value = valor; opcion.selected = voluntario.grado === valor; grado.append(opcion); });
        gradoLabel.append(grado); form.append(gradoLabel);
        const specialtyCaption = elemento("label", "Especialidad principal");
        const specialty = elemento("select"); specialty.name = "especialidad_principal";
        const noSpecialty = elemento("option", "Sin especialidad registrada"); noSpecialty.value = ""; specialty.append(noSpecialty);
        ["Rescate en agua", "Rescate en montaña", "Rescate en selva", "Lucha contra incendios", "Primeros Auxilios", "K-9"].forEach((value) => {
          const option = elemento("option", value); option.value = value; option.selected = voluntario.especialidad_principal === value; specialty.append(option);
        });
        specialtyCaption.append(specialty); form.append(specialtyCaption);
        const secundariasLabel = elemento("label", "Especialidades secundarias (selección múltiple)");
        const secundarias = elemento("select"); secundarias.multiple = true; secundarias.size = 6;
        Array.from(specialty.options).filter((opcion) => opcion.value).forEach((opcion) => {
          const nueva = elemento("option", opcion.value); nueva.value = opcion.value;
          nueva.selected = (voluntario.especialidades_secundarias || []).includes(opcion.value); secundarias.append(nueva);
        });
        secundariasLabel.append(secundarias); form.append(secundariasLabel);
        [["nacionalidad", "País de nacionalidad", paisesLatinoamerica], ["departamento_residencia", "Departamento de residencia", departamentosBolivia]].forEach(([nombre, etiqueta, opciones]) => {
          const caption = elemento("label", etiqueta); const select = elemento("select"); select.name = nombre;
          const vacio = elemento("option", "Sin registrar"); vacio.value = ""; select.append(vacio);
          opciones.forEach((valor) => { const opcion = elemento("option", valor); opcion.value = valor; opcion.selected = voluntario[nombre] === valor; select.append(opcion); });
          if (nombre === "departamento_residencia" && voluntario[nombre] && !opciones.includes(voluntario[nombre])) {
            const opcion=elemento("option",voluntario[nombre]);opcion.value=voluntario[nombre];opcion.selected=true;select.append(opcion);
          }
          caption.append(select); form.append(caption);
        });
        const residencia = elemento("input"); residencia.type = "hidden"; residencia.name = "pais_residencia"; residencia.value = voluntario.pais_residencia || "Bolivia"; form.append(residencia);
        if (!voluntario.fecha_incorporacion && (voluntario.ano_incorporacion || voluntario.antiguedad_desde)) {
          form.append(elemento("p", `Incorporación histórica: año ${voluntario.ano_incorporacion ?? "sin registrar"}; antigüedad desde ${voluntario.antiguedad_desde || "sin registrar"}. Completa la fecha para unificar los datos.`, "texto-secundario"));
        }
        configurarResidencia(form);
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
            body.especialidades_secundarias = Array.from(secundarias.selectedOptions, (opcion) => opcion.value);
            const foto = formData.get("foto"); delete body.foto;
            if ("instructor_id" in body) body.instructor_id = body.instructor_id ? Number(body.instructor_id) : null;
            const resultado = await apiJson(`/api/instructores-voluntarios/${voluntario.id}`, { method: "PATCH", body });
            if (foto?.size) { const carga = new FormData(); carga.append("foto", foto); await apiJson(`/api/usuarios/${voluntario.id}/foto`, { method: "PUT", body: carga }); }
            cerrarEdicion();
            managementMessage.textContent = `Perfil actualizado. Código de Instructor: ${resultado.codigo_instructor || "sin cambios"}.`;
            await cargarVoluntarios();
          }
          catch (error) { managementMessage.textContent = error.message; mostrarErrorEdicion(error); }
        });
        if (esAdministrador || voluntario.estado === "ACTIVO") contenidoAcciones.append(iconoAccionInstructor(botonEdicion(`Editar perfil · ${voluntario.nombre}`, form, "Editar perfil"), "editar", `Editar perfil de ${voluntario.nombre}`));
        if (esAdministrador) {

          const resetForm = elemento("form", undefined, "formulario-inline");
          const field = elemento("label", "Nueva contraseña (mínimo 12 caracteres)"); const password = elemento("input"); password.type = "password"; password.name = "password"; password.minLength = 12; password.maxLength = 256; password.required = true; password.autocomplete = "new-password"; field.append(password); resetForm.append(field, elemento("button", "Restablecer clave"));
          resetForm.addEventListener("submit", async (event) => { event.preventDefault(); try { await apiJson(`/api/admin/usuarios/${voluntario.id}/restablecer-clave`, { method: "POST", body: { password: password.value } }); resetForm.reset(); cerrarEdicion(); managementMessage.textContent = "Contraseña restablecida; las sesiones anteriores quedaron invalidadas."; } catch (error) { managementMessage.textContent = error.message; mostrarErrorEdicion(error); } });
          form.append(botonEdicion(`Restablecer contraseña · ${voluntario.nombre}`, resetForm, "Restablecer contraseña"));
        }
      }
      if (["ACTIVO", "INACTIVO"].includes(voluntario.estado)) {
        const activar = voluntario.estado === "INACTIVO";
        const accion = activar ? "Activar" : "Desactivar";
        const cambiar = elemento("button", accion, activar ? "boton-editar" : "boton-secundario"); cambiar.type = "button";
        cambiar.addEventListener("click", async () => {
          if (!window.confirm(`¿${accion} a ${voluntario.nombre}? ${activar ? "Podrá iniciar sesión nuevamente." : "Se bloqueará su acceso."} Su historial se conservará.`)) return;
          cambiar.disabled = true;
          try {
            await apiJson(`/api/instructores-voluntarios/${voluntario.id}/estado`, { method: "PATCH", body: { estado: activar ? "ACTIVO" : "INACTIVO", estado_anterior: voluntario.estado } });
            managementMessage.textContent = `${voluntario.nombre}: ${activar ? "ACTIVO" : "INACTIVO"}. Historial conservado.`;
            await cargarVoluntarios();
          } catch (error) { managementMessage.textContent = error.message; }
          finally { cambiar.disabled = false; }
        });
        contenidoAcciones.append(iconoAccionInstructor(cambiar, activar ? "activar" : "desactivar", `${accion} a ${voluntario.nombre}`));
      }
      volunteerList.append(fila);
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
      instructoresActivos.forEach((instructor) => { const option = elemento("option", instructor.nombre); option.value = instructor.id; option.selected = Number(solicitud.instructor_id) === instructor.id; assign.append(option); });
      card.append(assign);
      [["aprobar", "Aprobar"], ["rechazar", "Rechazar"]].forEach(([accion, texto]) => {
        const button = elemento("button", texto, accion === "rechazar" ? "boton-secundario" : "");
        button.addEventListener("click", async () => {
          try {
            const body = accion === "aprobar" && assign.value ? { instructor_id: Number(assign.value) } : {};
            await apiJson(`/api/admin/solicitudes/${solicitud.id}/${accion}`, { method: "POST", body });
            await Promise.all([cargarSolicitudes(), cargarVoluntarios()]);
          } catch (error) { managementMessage.textContent = error.message; mostrarErrorEdicion(error); }
        });
        card.append(button);
      });
      solicitudesLista.append(card);
    });
  }

  if (altaManualForm) altaManualForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const rutaAlta = esAdministrador ? "/api/admin/instructores-voluntarios" : "/api/jefe-personal/instructores-voluntarios";
      const data = await apiJson(rutaAlta, { method: "POST", body: new FormData(altaManualForm) });
      altaManualForm.reset();
      altaManualMensaje.textContent = `${data.mensaje || "Instructor Voluntario creado y activado."} Código: ${data.codigo_instructor}.`;
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

  const formularioDetalles = document.querySelector("#agregar-instructor-voluntario");
  const abrirFormularioDesdeEnlace = () => {
    if (formularioDetalles && window.location.hash === "#agregar-instructor-voluntario") formularioDetalles.open = true;
  };
  abrirFormularioDesdeEnlace();
  window.addEventListener("hashchange", abrirFormularioDesdeEnlace);
}

const instructorForm = document.querySelector("#instructor-form");
const instructorList = document.querySelector("#instructores-lista");
if (instructorForm && instructorList) {
  const formMessage = document.querySelector("#instructor-form-mensaje");
  const listMessage = document.querySelector("#instructores-mensaje");

  async function cargarInstructoresAdmin() {
    instructorList.replaceChildren();
    const { instructores } = await apiJson("/api/admin/jefes-personal");
    if (!instructores.length) {
      const fila = elemento("tr");
      const celda = elemento("td", "No hay Jefes de Personal registrados.", "tabla-vacia");
      celda.colSpan = 7; fila.append(celda); instructorList.append(fila);
    }
    instructores.forEach((instructor) => {
      const fila = elemento("tr");
      const perfil = elemento("td", undefined, "celda-perfil");
      if (instructor.tiene_foto) {
        const foto = elemento("img"); foto.src = `/api/usuarios/${instructor.id}/foto`; foto.alt = `Foto de ${instructor.nombre}`; foto.className = "foto-perfil"; perfil.append(foto);
      } else perfil.append(elemento("span", instructor.nombre.slice(0, 1).toUpperCase(), "avatar avatar-perfil"));
      perfil.append(elemento("strong", instructor.nombre));
      const acciones = elemento("td", undefined, "acciones-tabla");
      const estado = elemento("td"); estado.append(elemento("span", instructor.estado, `estado-tabla estado-${instructor.estado.toLowerCase()}`));
      fila.append(perfil, elemento("td", instructor.username), elemento("td", instructor.correo || "Sin correo"), elemento("td", instructor.especialidad || "Sin especialidad"), elemento("td", String(instructor.voluntarios_activos)), estado, acciones);

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
          cerrarEdicion(); listMessage.textContent = "Perfil actualizado.";
          await cargarInstructoresAdmin();
        } catch (error) { listMessage.textContent = error.message; mostrarErrorEdicion(error); }
      });
      acciones.append(botonEdicion(`Editar perfil · ${instructor.nombre}`, form, "Editar perfil"));

      const resetForm = elemento("form", undefined, "formulario-inline"); const passwordCaption = elemento("label", "Nueva contraseña (mínimo 12 caracteres)"); const password = elemento("input"); password.type = "password"; password.name = "password"; password.minLength = 12; password.maxLength = 256; password.required = true; password.autocomplete = "new-password"; passwordCaption.append(password); resetForm.append(passwordCaption, elemento("button", "Restablecer clave"));
      resetForm.addEventListener("submit", async (event) => { event.preventDefault(); try { await apiJson(`/api/admin/usuarios/${instructor.id}/restablecer-clave`, { method: "POST", body: { password: password.value } }); resetForm.reset(); cerrarEdicion(); listMessage.textContent = "Contraseña restablecida; las sesiones anteriores quedaron invalidadas."; } catch (error) { listMessage.textContent = error.message; mostrarErrorEdicion(error); } }); acciones.append(botonEdicion(`Restablecer contraseña · ${instructor.nombre}`, resetForm, "Restablecer contraseña"));
      if (instructor.estado === "ACTIVO") {
        const deactivate = elemento("button", "Desactivar Jefe de Personal", "boton-secundario");
        deactivate.addEventListener("click", async () => {
          if (!window.confirm(`¿Desactivar a ${instructor.nombre}? Sus Instructores Voluntarios quedarán sin Jefe de Personal asignado.`)) return;
          try {
            const result = await apiJson(`/api/admin/jefes-personal/${instructor.id}/desactivar`, { method: "POST" });
            listMessage.textContent = `Jefe de Personal desactivado. Instructores Voluntarios desvinculados: ${result.voluntarios_desvinculados}.`;
            await cargarInstructoresAdmin();
          } catch (error) { listMessage.textContent = error.message; mostrarErrorEdicion(error); }
        });
        acciones.append(deactivate);
      }
      instructorList.append(fila);
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

  const formularioDetalles = document.querySelector("#agregar-jefe-personal");
  const abrirFormularioDesdeEnlace = () => {
    if (formularioDetalles && window.location.hash === "#agregar-jefe-personal") formularioDetalles.open = true;
  };
  abrirFormularioDesdeEnlace();
  window.addEventListener("hashchange", abrirFormularioDesdeEnlace);
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
      card.append(elemento("h3", item.nombre), elemento("p", `${item.codigo} · ${item.categoria} · ${item.activo ? "Disponible en catálogo" : "No disponible en catálogo"}`));
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
      const button = elemento("button", item.activo ? "Retirar del catálogo" : "Habilitar en catálogo", item.activo ? "boton-secundario" : "");
      button.addEventListener("click", async () => {
        try { await apiJson(`/api/admin/evaluaciones/${item.id}`, { method: "PATCH", body: { activo: !item.activo } }); await cargarCatalogo(); }
        catch (error) { formMessage.textContent = error.message; }
      });
      card.append(button); evaluationList.append(card);
    });
    const active = evaluaciones.filter((item) => item.activo);
    if (!assignmentForm) return;
    const select = assignmentForm.elements.evaluacion_id;
    select.replaceChildren();
    active.forEach((item) => { const option = elemento("option", `${item.nombre} · ${item.categoria}`); option.value = item.id; select.append(option); });
  }

  async function cargarAsignacionesAdmin() {
    if (!assignmentList) return;
    const { asignaciones } = await apiJson("/api/jefe-personal/asignaciones");
    assignmentList.replaceChildren();
    asignaciones.forEach((item) => assignmentList.append(elemento("article", `${item.voluntario} · ${item.periodo} · ${item.evaluacion} · ${item.estado}`, "tarjeta-modulo")));
  }

  async function cargarPeriodos() {
    if (!periodsList) return;
    const { periodos } = await apiJson("/api/admin/periodos"); periodsList.replaceChildren();
    periodos.forEach((period) => periodsList.append(elemento("article", `${period.nombre} · ${period.fecha_inicio} – ${period.fecha_fin} · ${period.estado}`, "tarjeta-modulo")));
    const select = assignmentForm.elements.periodo_id; select.replaceChildren();
    periodos.filter((period) => period.estado === "ACTIVO").forEach((period) => { const option = elemento("option", period.nombre); option.value = period.id; select.append(option); });
  }

  periodForm?.addEventListener("submit", async (event) => {
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

  assignmentForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const body = Object.fromEntries(new FormData(assignmentForm).entries());
    ["voluntario_id", "periodo_id", "evaluacion_id"].forEach((key) => { body[key] = Number(body[key]); });
    try { await apiJson("/api/admin/asignaciones", { method: "POST", body }); assignmentMessage.textContent = "Evaluación asignada (inicia deshabilitada)."; await cargarAsignacionesAdmin(); }
    catch (error) { assignmentMessage.textContent = error.message; }
  });

  Promise.all([
    cargarCatalogo(), cargarAsignacionesAdmin(),
    assignmentForm ? apiJson("/api/admin/instructores-voluntarios-activos").then(({ voluntarios }) => {
      const select = assignmentForm.elements.voluntario_id;
      select.replaceChildren(); voluntarios.forEach((v) => { const option = elemento("option", v.nombre); option.value = v.id; select.append(option); });
    }) : Promise.resolve(),
    cargarPeriodos(),
  ]).catch((error) => { (assignmentMessage || formMessage).textContent = error.message; });
}

const attendanceForm = document.querySelector("#asistencias-form");
if (attendanceForm) {
  const attendanceRows = document.querySelector("#asistencias-voluntarios");
  const attendanceMessage = document.querySelector("#asistencias-mensaje");
  const attendanceHistory = document.querySelector("#asistencias-historial");
  const attendanceDate = attendanceForm.elements.fecha;
  const attendanceActivity = attendanceForm.elements.actividad;
  const attendanceSave = document.querySelector("#guardar-asistencias");
  const attendanceCount = document.querySelector("#asistencias-conteo");
  const historyForm = document.querySelector("#asistencias-filtros");
  const historySummary = document.querySelector("#asistencias-historial-resumen");
  let activeVolunteers = [];
  let revisionLlamada=0;

  async function cargarEquipoAsistencia() {
    const { voluntarios } = await apiJson("/api/instructores-voluntarios");
    activeVolunteers = voluntarios.filter((voluntario) => voluntario.estado === "ACTIVO");
    const historyVolunteer = historyForm.elements.voluntario_id;
    historyVolunteer.replaceChildren(elemento("option", "Todos los de mi ámbito")); historyVolunteer.options[0].value = "";
    voluntarios.forEach((voluntario) => { const option = elemento("option", voluntario.nombre); option.value = voluntario.id; historyVolunteer.append(option); });
  }

  function actualizarConteo() {
    const selects = [...attendanceRows.querySelectorAll("select")];
    const completed = selects.filter((select) => select.value).length;
    attendanceCount.textContent = selects.length ? `${completed} de ${selects.length} estados seleccionados` : "";
    attendanceSave.disabled = !selects.length || completed !== selects.length || !attendanceDate.value;
  }

  function renderizarEquipo() {
    attendanceRows.replaceChildren(); attendanceSave.disabled = true;
    if (!attendanceDate.value) {
      const filaVacia=elemento("tr");filaVacia.append(elemento("td", "Selecciona una fecha para cargar el equipo activo.", "tabla-vacia"));attendanceRows.append(filaVacia);
      attendanceRows.firstElementChild.firstElementChild.colSpan = 4;
      actualizarConteo(); return;
    }
    if (!activeVolunteers.length) {
      const emptyRow = elemento("tr"); const emptyCell = elemento("td", "No hay Instructores Voluntarios activos en tu ámbito.", "tabla-vacia"); emptyCell.colSpan = 4; emptyRow.append(emptyCell); attendanceRows.append(emptyRow);
      actualizarConteo(); return;
    }
    activeVolunteers.forEach((voluntario) => {
      const row = elemento("tr", undefined, "fila-asistencia");
      const nombre = elemento("td", voluntario.nombre || "—");
      const codigo = elemento("td", voluntario.codigo_instructor || "—");
      const estado = elemento("td", undefined, "estado-asistencia");
      const valorEstado = voluntario.estado || "ACTIVO";
      const etiquetaEstado = elemento("span", valorEstado, "estado-asistencia-etiqueta");
      if (valorEstado === "ACTIVO") etiquetaEstado.classList.add("estado-asistencia-activo");
      if (valorEstado === "INACTIVO") etiquetaEstado.classList.add("estado-asistencia-inactivo");
      estado.append(etiquetaEstado);
      const select = elemento("select"); select.name = "estado"; select.dataset.volunteerId = voluntario.id; select.required = true;

      [["ASISTE", "Asiste"], ["ATRASO", "Atraso"], ["PERMISO", "Permiso"], ["FALTA", "Falta"]].forEach(([value, label]) => { const opt = elemento("option", label); opt.value = value; select.append(opt); });
      select.value="FALTA";select.setAttribute("aria-label",`Asistencia de ${voluntario.nombre}`);
      const asistencia = elemento("td"); asistencia.append(select);
      select.addEventListener("change", actualizarConteo);
      row.append(nombre, codigo, estado, asistencia); attendanceRows.append(row);
    });
    actualizarConteo();
  }

  async function cargarHistorialAsistencia() {
    const data = new FormData(historyForm);
    const params = new URLSearchParams({ modo: data.get("modo") });
    if (data.get("voluntario_id")) params.set("voluntario_id", data.get("voluntario_id"));
    if (data.get("modo") === "rango") { params.set("desde", data.get("desde")); params.set("hasta", data.get("hasta")); }
    const { asistencias, modo, fecha_consultada: latestDate } = await apiJson(`/api/jefe-personal/asistencias?${params}`);
    attendanceHistory.replaceChildren();
    if (!asistencias.length) {
      historySummary.textContent = modo === "ultima" ? "No hay gestiones registradas para este filtro." : "No hay registros en el rango seleccionado.";
      const empty = elemento("tr"); const cell = elemento("td", "Sin registros de asistencia.", "tabla-vacia"); cell.colSpan = 5; empty.append(cell); attendanceHistory.append(empty); return;
    }
    historySummary.textContent = modo === "ultima" ? `Última gestión registrada: ${latestDate}.` : `Mostrando ${asistencias.length} registros del ${data.get("desde")} al ${data.get("hasta")}.`;
    const labels = { ASISTE: "Asiste", ATRASO: "Atraso", PERMISO: "Permiso", FALTA: "Falta" };
    asistencias.forEach((row) => {
      const tr = elemento("tr");
      [row.fecha, row.voluntario, row.actividad || "—", labels[row.estado] || row.estado].forEach((value) => tr.append(elemento("td", value)));
      const acciones=elemento("td");const editar=elemento("form",undefined,"formulario-inline");
      const label=elemento("label","Estado");const select=elemento("select");select.name="estado";
      Object.entries(labels).forEach(([valor,etiqueta])=>{const opcion=elemento("option",etiqueta);opcion.value=valor;select.append(opcion);});select.value=row.estado;label.append(select);editar.append(label,elemento("button","Guardar corrección"));
      const historial=elemento("div");editar.append(historial);
      const boton=botonEdicion(`Corregir asistencia · ${row.voluntario} · ${row.fecha}`,editar,"Editar / historial");
      boton.addEventListener("click",async()=>{try{const {historial:registros}=await apiJson(`/api/jefe-personal/asistencias/${row.id}/historial`);historial.replaceChildren();if(!registros.length)historial.append(elemento("p","Sin correcciones previas."));registros.forEach((r)=>historial.append(elemento("p",`${labels[r.estado_anterior]||r.estado_anterior} → ${labels[r.estado_nuevo]||r.estado_nuevo} · ${r.corregido_por} · ${r.corregido_en} (UTC)`)));}catch(error){mostrarErrorEdicion(error);}});
      editar.addEventListener("submit",async(e)=>{e.preventDefault();try{await apiJson(`/api/jefe-personal/asistencias/${row.id}`,{method:"PATCH",body:{estado:select.value}});cerrarEdicion();attendanceMessage.textContent="Corrección guardada con historial.";await cargarHistorialAsistencia();await cargarLlamada();}catch(error){mostrarErrorEdicion(error);}});
      acciones.append(boton);tr.append(acciones);attendanceHistory.append(tr);
    });
  }

  async function cargarLlamada(){
    const revision=++revisionLlamada;
    renderizarEquipo();document.querySelector("#asistencias-gestion").value=attendanceDate.value.slice(0,4);
    if(!attendanceDate.value||!attendanceActivity.value.trim())return;
    attendanceSave.disabled=true;
    try{const {asistencias}=await apiJson(`/api/jefe-personal/asistencias?${new URLSearchParams({modo:"rango",desde:attendanceDate.value,hasta:attendanceDate.value})}`);
      if(revision!==revisionLlamada)return;
      asistencias.filter((r)=>r.actividad===attendanceActivity.value.trim()).forEach((r)=>{const select=attendanceRows.querySelector(`select[data-volunteer-id="${r.voluntario_id}"]`);if(select)select.value=r.estado;});actualizarConteo();
    }catch(error){if(revision===revisionLlamada){attendanceMessage.textContent=error.message;attendanceSave.disabled=true;}}
  }
  attendanceDate.addEventListener("change", cargarLlamada);attendanceActivity.addEventListener("change", cargarLlamada);
  attendanceForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!attendanceForm.reportValidity()) return;
    const entries = [...attendanceRows.querySelectorAll("select")].map((select) => ({ voluntario_id: Number(select.dataset.volunteerId), estado: select.value }));
    try {
      const result = await apiJson("/api/jefe-personal/asistencias", { method: "POST", body: { fecha: attendanceDate.value, actividad: attendanceActivity.value.trim(), asistencias: entries } });
      attendanceMessage.textContent = `Asistencia guardada para ${result.registrados} personas.`;
      historyForm.elements.modo.value = "ultima"; historyForm.elements.voluntario_id.value = "";
      await cargarHistorialAsistencia();
    } catch (error) { attendanceMessage.textContent = error.message; }
  });

  historyForm.elements.modo.addEventListener("change", () => {
    const range = historyForm.elements.modo.value === "rango";
    historyForm.elements.desde.disabled = !range; historyForm.elements.hasta.disabled = !range;
    historyForm.elements.desde.required = range; historyForm.elements.hasta.required = range;
  });
  historyForm.addEventListener("submit", async (event) => { event.preventDefault(); if (!historyForm.reportValidity()) return; try { await cargarHistorialAsistencia(); } catch (error) { historySummary.textContent = error.message; } });
  historyForm.elements.voluntario_id.addEventListener("change", () => { if (historyForm.elements.modo.value === "ultima") cargarHistorialAsistencia().catch((error) => { historySummary.textContent = error.message; }); });

  const hoy = new Date(); attendanceDate.value = `${hoy.getFullYear()}-${String(hoy.getMonth() + 1).padStart(2, "0")}-${String(hoy.getDate()).padStart(2, "0")}`;
  cargarEquipoAsistencia().then(() => { renderizarEquipo(); return cargarHistorialAsistencia(); }).catch((error) => { attendanceMessage.textContent = error.message; });
}

const gradeSelect = document.querySelector("#calificacion-asignacion");
if (gradeSelect) {
  const gradeForm = document.querySelector("#calificacion-form");
  const gradeHistory = document.querySelector("#calificacion-historial");
  const psychometricList = document.querySelector("#psicometricas-lista");
  const gradeMessage = document.querySelector("#calificacion-mensaje");
  let assignmentsById = new Map();
  let historiesByAssignment = new Map();
  let revisionHistorial = 0;
  let historialListo = false;
  const guardarNota = gradeForm.querySelector("button[type=submit]");

  async function cargarAsignacionesInstructor() {
    const seleccion = gradeSelect.value;
    const { asignaciones } = await apiJson("/api/jefe-personal/asignaciones");
    assignmentsById = new Map(asignaciones.map((item) => [String(item.id), item]));
    gradeSelect.replaceChildren(elemento("option", "Selecciona una evaluación"));
    gradeSelect.options[0].value = "";
    gradeSelect.value = "";
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
    gradeSelect.value = assignmentsById.has(seleccion) ? seleccion : "";
    if (!asignaciones.some((item) => item.categoria !== "PSICOMETRICA")) gradeMessage.textContent = "No hay evaluaciones manuales asignadas al personal activo de tu ámbito.";
  }

  async function cargarHistorialNota(assignmentId) {
    const revision = ++revisionHistorial;
    historialListo = false; guardarNota.disabled = true; gradeHistory.replaceChildren();
    const { historial } = await apiJson(`/api/jefe-personal/asignaciones/${assignmentId}/calificaciones`);
    if (revision !== revisionHistorial || gradeSelect.value !== String(assignmentId)) return;
    historiesByAssignment.set(String(assignmentId), historial);
    if (!historial.length) gradeHistory.append(elemento("p", "Sin notas registradas para esta asignación.", "nota-informativa"));
    historial.forEach((record) => {
      const detalle = `Nota ${record.nota_0_100} · ${record.registrada_en} · ${record.registrada_por}${record.corregida_de_id ? ` · corrección de #${record.corregida_de_id}` : ""}`;
      gradeHistory.append(elemento("article", record.observacion ? `${detalle} · ${record.observacion}` : detalle, "tarjeta-modulo"));
    });
    const cerrada = assignmentsById.get(String(assignmentId))?.periodo_estado === "CERRADO";
    gradeForm.hidden = cerrada; historialListo = !cerrada; guardarNota.disabled = cerrada;
    guardarNota.textContent = historial.length ? "Guardar corrección" : "Guardar nota";
    if (cerrada) gradeMessage.textContent = "Período cerrado: historial disponible, edición bloqueada.";
  }

  gradeSelect.addEventListener("change", async () => {
    ++revisionHistorial; historialListo = false; guardarNota.disabled = true;
    gradeForm.reset(); gradeMessage.textContent = ""; gradeForm.hidden = !gradeSelect.value;
    if (!gradeSelect.value) { gradeHistory.replaceChildren(); return; }
    try { await cargarHistorialNota(gradeSelect.value); }
    catch (error) { gradeForm.hidden = true; gradeMessage.textContent = error.message; }
  });

  gradeForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!historialListo || !gradeSelect.value || !gradeForm.reportValidity()) return;
    const assignmentId = gradeSelect.value;
    const history = historiesByAssignment.get(assignmentId) || [];
    const latest = history[history.length - 1];
    const body = Object.fromEntries(new FormData(gradeForm).entries()); body.nota_0_100 = Number(body.nota_0_100);
    if (latest) body.corregida_de_id = latest.id;
    guardarNota.disabled = true; gradeSelect.disabled = true; historialListo = false;
    try {
      await apiJson(`/api/jefe-personal/asignaciones/${assignmentId}/calificaciones`, { method: "POST", body });
      gradeForm.reset(); gradeMessage.textContent = latest ? "Corrección guardada; se conservó la nota anterior." : "Nota guardada.";
      await cargarAsignacionesInstructor();
      if (gradeSelect.value === assignmentId) await cargarHistorialNota(assignmentId);
      else gradeForm.hidden = true;
    } catch (error) {
      gradeMessage.textContent = error.message;
      try { await cargarHistorialNota(assignmentId); } catch { gradeForm.hidden = true; }
    } finally { gradeSelect.disabled = false; }
  });

  cargarAsignacionesInstructor().catch((error) => { gradeMessage.textContent = error.message; });
}

const perfilPropioForm = document.querySelector("#perfil-propio-form");
if (perfilPropioForm) {
  const mensaje = document.querySelector("#perfil-propio-mensaje");
  const foto = perfilPropioForm.elements.foto;
  const previa = document.querySelector('#perfil-foto-previa');
  const imagen = document.querySelector('#perfil-foto-imagen');
  const estadoFoto = document.querySelector('#perfil-foto-estado');
  const descartar = document.querySelector('#perfil-foto-descartar');
  let fotoUrl;
  function limpiarFoto(texto = 'Tu foto actual se conserva si no seleccionas otra.') {
    if (fotoUrl) URL.revokeObjectURL(fotoUrl);
    fotoUrl = null;
    imagen.removeAttribute('src');
    previa.hidden = true;
    foto.value = '';
    foto.removeAttribute('aria-invalid');
    estadoFoto.textContent = texto;
  }
  foto.addEventListener('change', () => {
    const archivo = foto.files[0];
    if (!archivo) { limpiarFoto(); return; }
    if (archivo.size > 3 * 1024 * 1024 || (archivo.type && !['image/png', 'image/jpeg'].includes(archivo.type))) {
      limpiarFoto('Selecciona una imagen PNG o JPEG de hasta 3 MiB.');
      foto.setAttribute('aria-invalid', 'true');
      return;
    }
    if (fotoUrl) URL.revokeObjectURL(fotoUrl);
    foto.removeAttribute('aria-invalid');
    fotoUrl = URL.createObjectURL(archivo);
    imagen.src = fotoUrl;
    document.querySelector('#perfil-foto-nombre').textContent = archivo.name;
    previa.hidden = false;
    estadoFoto.textContent = 'Foto seleccionada. Guarda los cambios para aplicarla.';
  });
  imagen.addEventListener('error', () => {
    limpiarFoto('No se pudo leer la imagen. Selecciona otro archivo PNG o JPEG.');
    foto.setAttribute('aria-invalid', 'true');
  });
  descartar.addEventListener('click', () => { limpiarFoto(); foto.focus(); });
  window.addEventListener('pagehide', () => { if (fotoUrl) URL.revokeObjectURL(fotoUrl); });
  perfilPropioForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!perfilPropioForm.reportValidity()) return;
    const boton = perfilPropioForm.querySelector("button[type='submit']");
    const datos = new FormData(perfilPropioForm);
    if (!datos.get("foto")?.size) datos.delete("foto");
    boton.disabled = true;
    descartar.disabled = true;
    foto.disabled = true;
    perfilPropioForm.setAttribute('aria-busy', 'true');
    boton.textContent = 'Guardando…';
    mensaje.textContent = 'Guardando tus cambios…';
    try {
      await apiJson("/api/instructor-voluntario/perfil", { method: "PATCH", body: datos });
      mensaje.textContent = "Perfil actualizado.";
      window.setTimeout(() => window.location.reload(), 1000);
    } catch (error) {
      mensaje.textContent = error.message;
      boton.disabled = false;
      descartar.disabled = false;
      foto.disabled = false;
      perfilPropioForm.removeAttribute('aria-busy');
      boton.textContent = 'Guardar cambios';
    }
  });
}

const reporteCursosForm=document.querySelector('#reporte-cursos-form');
if(reporteCursosForm)reporteCursosForm.addEventListener('submit',async(evento)=>{
  evento.preventDefault();if(!reporteCursosForm.reportValidity())return;
  const mensaje=document.querySelector('#reporte-cursos-mensaje');const boton=reporteCursosForm.querySelector('button');
  boton.disabled=true;mensaje.textContent='Generando reporte…';
  try{
    const respuesta=await fetch(`${reporteCursosForm.action}?${new URLSearchParams(new FormData(reporteCursosForm))}`,{credentials:'same-origin'});
    if(!respuesta.ok){const fallo=await respuesta.json();throw new Error(fallo.error||'No se pudo generar el reporte.');}
    const archivo=await respuesta.blob();const url=URL.createObjectURL(archivo);const enlace=document.createElement('a');enlace.href=url;enlace.download=`cursos-${reporteCursosForm.elements.desde.value}-${reporteCursosForm.elements.hasta.value}.pdf`;document.body.append(enlace);enlace.click();enlace.remove();window.setTimeout(()=>URL.revokeObjectURL(url),1000);mensaje.textContent='Reporte PDF generado.';
  }catch(error){mensaje.textContent=error.message;}finally{boton.disabled=false;}
});

const calendarioAsistenciasForm=document.querySelector('#calendario-asistencias-form');
if(calendarioAsistenciasForm){
 const etiquetas={ASISTE:'Asiste',ATRASO:'Atraso',PERMISO:'Permiso',FALTA:'Falta'};
 async function cargarCalendario(){
  const {gestion,registros,totales}=await apiJson(`/api/instructor-voluntario/asistencias?${new URLSearchParams(new FormData(calendarioAsistenciasForm))}`);
  const resumen=document.querySelector('#asistencias-propias-totales');resumen.replaceChildren();Object.entries(etiquetas).forEach(([clave,nombre])=>resumen.append(elemento('article',`${nombre}: ${totales[clave]}`,'tarjeta-modulo')));
  const calendario=document.querySelector('#asistencias-calendario');calendario.replaceChildren();
  const meses=['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];
  meses.forEach((mes,indice)=>{const tarjeta=elemento('article',undefined,'tarjeta-modulo');tarjeta.append(elemento('h3',`${mes} ${gestion}`));const dias=elemento('div',undefined,'calendario-dias');
   ['L','M','M','J','V','S','D'].forEach((d)=>dias.append(elemento('span',d,'calendario-semana')));
   const primero=new Date(0);primero.setFullYear(gestion,indice,1);const ultimo=new Date(0);ultimo.setFullYear(gestion,indice+1,0);
   for(let blanco=0;blanco<(primero.getDay()+6)%7;blanco++)dias.append(elemento('span',''));
   for(let dia=1;dia<=ultimo.getDate();dia++){const fecha=`${String(gestion).padStart(4,'0')}-${String(indice+1).padStart(2,'0')}-${String(dia).padStart(2,'0')}`;const celda=elemento('div',undefined,'calendario-dia');celda.append(elemento('strong',String(dia)));registros.filter((r)=>r.fecha===fecha).forEach((r)=>{const marca=elemento('span',etiquetas[r.estado],`marca-asistencia marca-${r.estado.toLowerCase()}`);marca.title=`${fecha}: ${etiquetas[r.estado]}`;celda.append(marca);});dias.append(celda);}tarjeta.append(dias);calendario.append(tarjeta);
  });
 }
 calendarioAsistenciasForm.addEventListener('submit',async(e)=>{e.preventDefault();try{await cargarCalendario();document.querySelector('#calendario-asistencias-mensaje').textContent='Calendario actualizado.';}catch(error){document.querySelector('#calendario-asistencias-mensaje').textContent=error.message;}});
 cargarCalendario().catch((error)=>{document.querySelector('#calendario-asistencias-mensaje').textContent=error.message;});
}
const reporteAsistenciasForm=document.querySelector('#reporte-asistencias-form');
if(reporteAsistenciasForm){
 const mensaje=document.querySelector('#reporte-asistencias-mensaje');const abreviaturas={ASISTE:'A',ATRASO:'T',PERMISO:'P',FALTA:'F'};
 reporteAsistenciasForm.addEventListener('submit',async(e)=>{e.preventDefault();if(!reporteAsistenciasForm.reportValidity())return;
  try{const datos=await apiJson(`/api/jefe-personal/asistencias/reporte?${new URLSearchParams(new FormData(reporteAsistenciasForm))}`);
   const tabla=document.querySelector('#reporte-asistencias-tabla');tabla.replaceChildren();const cabeza=elemento('thead');const encabezado=elemento('tr');['Nro.','Código','Instructor Voluntario',...datos.llamadas.map((c)=>`${c.fecha} · ${c.actividad||'Sin actividad'}`),'Asiste','Atraso','Permiso','Falta','% asistencia'].forEach((c)=>encabezado.append(elemento('th',c)));cabeza.append(encabezado);tabla.append(cabeza);const cuerpo=elemento('tbody');datos.personas.forEach((p,i)=>{const fila=elemento('tr');[i+1,p.codigo||'Sin código',p.nombre,...p.estados.map((s)=>abreviaturas[s]||'—'),p.totales.ASISTE,p.totales.ATRASO,p.totales.PERMISO,p.totales.FALTA,p.totales.porcentaje==null?'No disponible':`${p.totales.porcentaje.toFixed(2)}%`].forEach((c)=>fila.append(elemento('td',String(c))));cuerpo.append(fila);});tabla.append(cuerpo);mensaje.textContent=`Responsable: ${datos.responsable} · Rango ${datos.desde} a ${datos.hasta} · ${datos.personas.length} personas. Las columnas distinguen fecha y actividad; sin registro no equivale a Falta.`;
  }catch(error){mensaje.textContent=error.message;}
 });
 document.querySelector('#asistencias-pdf').addEventListener('click',async()=>{if(!reporteAsistenciasForm.reportValidity())return;try{const respuesta=await fetch(`/api/jefe-personal/asistencias/reporte.pdf?${new URLSearchParams(new FormData(reporteAsistenciasForm))}`,{credentials:'same-origin'});if(!respuesta.ok){throw new Error((await respuesta.json()).error);}const url=URL.createObjectURL(await respuesta.blob());const enlace=document.createElement('a');enlace.href=url;enlace.download='reporte-asistencias.pdf';document.body.append(enlace);enlace.click();enlace.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);mensaje.textContent='PDF generado; puedes abrirlo e imprimirlo.';}catch(error){mensaje.textContent=error.message;}});
}
