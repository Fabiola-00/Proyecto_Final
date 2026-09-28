"use strict";

const loginForm = document.querySelector("#login-form");
const logoutButton = document.querySelector("#logout-button");
const authMessage = document.querySelector("#auth-message");
const csrfToken = document.querySelector('[name="csrf_token"]')?.value;

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
