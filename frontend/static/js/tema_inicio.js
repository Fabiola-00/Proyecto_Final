"use strict";
// Antes del CSS: evita un destello del tema contrario al abrir otra página.
(() => {
  let preferencia = 'system';
  try { preferencia = localStorage.getItem('sicose-tema') || 'system'; } catch { /* Preferencia del equipo. */ }
  if (!['light', 'dark', 'system'].includes(preferencia)) preferencia = 'system';
  const oscuro = preferencia === 'dark' || (preferencia === 'system' && matchMedia('(prefers-color-scheme: dark)').matches);
  document.documentElement.dataset.theme = oscuro ? 'dark' : 'light';
  document.documentElement.dataset.themePreference = preferencia;
})();
