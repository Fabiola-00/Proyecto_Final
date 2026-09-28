"use strict";

const loginForm = document.querySelector("#login-form");
const logoutButton = document.querySelector("#logout-button");
const authMessage = document.querySelector("#auth-message");
const csrfToken = document.querySelector('[name="csrf_token"]')?.value;
const appShell = document.querySelector(".app-shell");
const menuButton = document.querySelector("#boton-menu");
const mobileBackdrop = document.querySelector("#fondo-movil");

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
