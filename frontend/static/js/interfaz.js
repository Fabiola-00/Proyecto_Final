"use strict";
{
  const normalizar = texto => texto.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();

  function actualizarAcciones() {
    document.querySelectorAll('.accion-principal').forEach(b => b.classList.remove('accion-principal'));
    document.querySelectorAll('button, a.boton-enlace').forEach(b => {
      const texto = normalizar((b.getAttribute('aria-label') || b.textContent).trim());
      b.classList.toggle('accion-destructiva', /^(?:(?:confirmar|dar de)\s+)?(eliminar|eliminacion|borrar|rechazar|retirar|retiro|desactivar|desactivacion|baja)\b/.test(texto));
    });
    const dialogo = document.querySelector('dialog[open]');
    const ambito = dialogo || document.querySelector('main') || document.body;
    const candidatos = [...ambito.querySelectorAll('form button:not([type="button"]):not([type="reset"]), a.boton-enlace')];
    const principal = candidatos.find(b => b.getClientRects().length && !b.classList.contains('accion-destructiva') && !/^(consultar|filtrar|buscar|cancelar|cerrar|descartar)\b/.test(normalizar(b.textContent.trim())));
    const cabecera = document.querySelector('#accion-principal-pagina');
    const usarCabecera = Boolean(cabecera && principal && !dialogo);
    if (cabecera && cabecera.hidden === usarCabecera) cabecera.hidden = !usarCabecera;
    if (usarCabecera) {
      if (cabecera.textContent !== principal.textContent) cabecera.textContent = principal.textContent;
      if (cabecera.disabled !== Boolean(principal.disabled)) cabecera.disabled = Boolean(principal.disabled);
      cabecera.onclick = () => { if (principal.isConnected && !principal.disabled) principal.click(); };
      cabecera.classList.add('accion-principal');
    } else {
      principal?.classList.add('accion-principal');
    }
  }
  let pendiente = false;
  function programarAcciones() {
    if (pendiente) return;
    pendiente = true;
    requestAnimationFrame(() => { pendiente = false; actualizarAcciones(); });
  }
  const observador = new MutationObserver(programarAcciones);
  observador.observe(document.body, {subtree: true, childList: true, attributes: true, attributeFilter: ['open', 'disabled', 'hidden']});
  document.addEventListener('toggle', programarAcciones, true);
  window.addEventListener('resize', programarAcciones);
  actualizarAcciones();
}
