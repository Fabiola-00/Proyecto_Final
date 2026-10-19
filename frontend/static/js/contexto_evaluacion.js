"use strict";
function actualizarContextoEvaluacion(pid, uid) {
  const url = new URL(location.href);
  if (pid) url.searchParams.set('periodo_id', pid); else url.searchParams.delete('periodo_id');
  if (pid && uid) url.searchParams.set('persona_id', uid); else url.searchParams.delete('persona_id');
  history.replaceState(null, '', url);
  document.querySelectorAll('a[data-contexto-evaluacion]').forEach(a => {
    const destino = new URL(a.href);
    destino.search = url.searchParams.toString();
    a.href = destino.pathname + destino.search;
  });
}
