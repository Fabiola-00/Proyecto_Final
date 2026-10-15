"use strict";
const tablaEvaluaciones = document.querySelector("#tabla-evaluaciones");
if (tablaEvaluaciones) {
  const propia = tablaEvaluaciones.dataset.propia === "si";
  const filtro = document.querySelector("#gestion-evaluaciones-filtro");
  const resultado = document.querySelector("#evaluaciones-resultado");
  const mensaje = document.querySelector("#tabla-evaluaciones-mensaje");
  const reporte = document.querySelector("#reporte-evaluaciones");
  const gestiones = new Map();
  const estados = { FINALIZADA: "Finalizada", PENDIENTE: "Pendiente", EN_PROGRESO: "En progreso", NO_CUMPLIDA: "No cumplida" };
  function ano(periodo) { return periodo.gestion || periodo.fecha_inicio?.slice(0, 4) || gestiones.get(String(periodo.id)) || "Sin año"; }
  function invalidarReporte() { if (reporte) { reporte.disabled = true; delete reporte.dataset.url; } }
  reporte?.addEventListener("click", () => { if (!reporte.disabled && reporte.dataset.url) window.location.assign(reporte.dataset.url); });
  let solicitud = 0;
  function detalle(persona, periodo) {
    const panel = elemento("div", undefined, "detalle-evaluaciones");
    if (!propia && (persona.estado !== "ACTIVO" || periodo.estado !== "ACTIVO")) panel.append(elemento("p", "Solo consulta: la cuenta y la gestión deben estar activas para cambiar habilitaciones.", "evaluaciones-ayuda"));
    persona.evaluaciones.forEach((e) => {
      const fila = elemento("article", undefined, "detalle-evaluacion");
      const informacion = elemento("div", undefined, "evaluacion-informacion"); informacion.append(elemento("h3", e.nombre));
      if (!propia) informacion.append(elemento("small", `Nota: ${e.nota ?? "Pendiente"}${e.historica ? " · Histórica" : ""}`));
      const indicadores = elemento("div", undefined, "evaluacion-indicadores");
      indicadores.append(elemento("span", e.habilitada ? "Habilitada" : "Deshabilitada", `evaluacion-etiqueta ${e.habilitada ? "evaluacion-habilitada" : ""}`), elemento("span", estados[e.estado] || e.estado, `evaluacion-etiqueta evaluacion-${e.estado.toLowerCase()}`));
      if (e.activa === false) indicadores.append(elemento("span", "Inactiva en esta gestión", "evaluacion-etiqueta"));
      fila.append(informacion, indicadores);
      if (!propia && !periodo.retirada && e.activa !== false && persona.estado === "ACTIVO" && periodo.estado === "ACTIVO") {
        const boton = elemento("button", e.habilitada ? "Deshabilitar" : "Habilitar", "evaluacion-alternar boton-editar");
        boton.type = "button"; boton.setAttribute("aria-label", `${e.habilitada ? "Deshabilitar" : "Habilitar"} ${e.nombre}`);
        boton.addEventListener("click", async () => {
          boton.disabled = true;
          try { await apiJson(`/api/evaluaciones/personas/${persona.id}/habilitacion`, { method: "PATCH", body: { periodo_id: periodo.id, clave: e.clave, habilitada: !e.habilitada } }); cerrarEdicion(); await cargar(); }
          catch (error) { mostrarErrorEdicion(error); boton.disabled = false; }
        });
        fila.append(boton);
      }
      panel.append(fila);
    });
    return panel;
  }
  async function cargar() {
    const pid = filtro.elements.periodo_id.value;
    if (!pid) return;
    const turno = ++solicitud; invalidarReporte();
    const datos = await apiJson(`/api/evaluaciones/${propia ? "propias" : "tabla"}?periodo_id=${pid}`);
    if (turno !== solicitud || pid !== filtro.elements.periodo_id.value) return;
    resultado.replaceChildren(); mensaje.textContent = "";
    tablaEvaluaciones.dispatchEvent(new CustomEvent("gestion-consultada", {detail: datos.periodo}));
    if (propia) {
      const r = datos.resumen;
      resultado.append(elemento("p", `Avance: ${r.avance === null ? "No disponible" : r.avance + " %"} · Finalizadas: ${r.finalizadas} · Pendientes: ${r.pendientes} · No cumplidas: ${r.no_cumplidas}`), detalle(datos, datos.periodo));
      const publicado = elemento("section", undefined, "tarjeta-modulo calculo-provisional"); publicado.append(elemento("h3", "Notas publicadas"));
      const p = datos.publicacion;
      if (!p) publicado.append(elemento("p", "Sin notas publicadas disponibles para consultar."));
      else {
        publicado.append(elemento("p", `Versión publicada ${p.revision} · ${p.publicada_en}`));
        p.fisicas.forEach((f) => publicado.append(elemento("p", `${f.nombre}: ${f.nota ?? "Pendiente"} · ${estados[f.estado]} · Publicada: ${f.publicada_en}${f.fecha_realizacion ? " · Realizada: " + f.fecha_realizacion : ""}`)));
        publicado.append(elemento("p", `Promedio físico publicado: ${p.promedio_fisico ?? "No disponible"}`));
        if (p.academica) {
          publicado.append(elemento("p", `Acumulado académico publicado: ${p.academica.valor ?? "Pendiente"} · Publicado: ${p.academica.publicada_en}`));
          p.academica.cursos.forEach((c) => publicado.append(elemento("p", `${c.nombre_curso} · ${c.puntaje} puntos · Finalización publicada: ${c.fecha_finalizacion}`)));
        }
      }
      resultado.append(publicado);
      return;
    }
    if (reporte) { reporte.dataset.url = `/api/evaluaciones/reporte.pdf?periodo_id=${pid}`; reporte.disabled = false; }
    const contenedor = elemento("div", undefined, "tabla-contenedor"); const tabla = elemento("table", undefined, "tabla-registros tabla-evaluaciones");
    tabla.setAttribute("aria-label", `Evaluaciones de la gestión ${ano(datos.periodo)}`);
    const columnas = elemento("colgroup"); ["nombre", "codigo", "estado", "cantidad", "cantidad", "avance", "acciones"].forEach((nombre) => columnas.append(elemento("col", undefined, `evaluaciones-col-${nombre}`))); tabla.append(columnas);
    const cabecera = elemento("thead"); const titulos = elemento("tr");
    ["Nombre completo", "Código", "Estado", "Finalizadas", "Pendientes / No cumplidas", "Avance", "Acciones"].forEach((nombre) => titulos.append(Object.assign(elemento("th", nombre), { scope: "col" })));
    cabecera.append(titulos); tabla.append(cabecera); const cuerpo = elemento("tbody");
    datos.personas.forEach((p) => {
      const tr = elemento("tr"); const r = p.resumen;
      tr.append(elemento("td", p.nombre, "evaluaciones-nombre"), elemento("td", p.codigo || "Sin código", "evaluaciones-codigo"));
      const cuenta = elemento("td"); cuenta.append(elemento("span", p.estado, `estado-tabla estado-${p.estado.toLowerCase()}`)); tr.append(cuenta);
      [r.finalizadas, `${r.pendientes} / ${r.no_cumplidas}`].forEach((valor) => tr.append(elemento("td", String(valor), "evaluaciones-cantidad")));
      tr.append(elemento("td", r.avance === null ? "No disponible" : r.avance + " %", "evaluaciones-avance"));
      const acciones = elemento("td", undefined, "evaluaciones-acciones");
      acciones.append(iconoAccionInstructor(botonEdicion(`${p.nombre} · Gestión ${ano(datos.periodo)}`, detalle(p, datos.periodo), "Ver"), "ver", `Ver evaluaciones de ${p.nombre}`)); tr.append(acciones); cuerpo.append(tr);
    });
    tabla.append(cuerpo); contenedor.append(tabla); resultado.append(contenedor);
    if (!datos.personas.length) resultado.append(elemento("p", "Sin Instructores Voluntarios registrados."));
  }
  filtro.addEventListener("submit", (event) => { event.preventDefault(); if (filtro.reportValidity()) cargar().catch((error) => { resultado.replaceChildren(); mensaje.textContent = error.message; }); });
  filtro.elements.periodo_id.addEventListener("change", () => { ++solicitud; resultado.replaceChildren(); invalidarReporte(); });
  apiJson("/api/evaluaciones/gestiones").then(({ periodos, retiradas = [] }) => {
    const solicitada = new URLSearchParams(window.location.search).get("periodo_id");
    if (!propia && solicitada) periodos = [...periodos, ...retiradas];
    periodos.forEach((p) => {
      const gestion = ano(p); gestiones.set(String(p.id), gestion);
      const repetida = periodos.filter((otro) => ano(otro) === gestion && otro.estado === p.estado).length > 1;
      const opcion = elemento("option", `${gestion}${repetida ? " · " + p.nombre : ""} · ${p.retirada ? "Retirada (historial)" : p.estado}`); opcion.value = p.id; opcion.title = p.nombre; filtro.elements.periodo_id.append(opcion);
    });
    if (!periodos.length) mensaje.textContent = "No hay gestiones registradas.";
    if (solicitada && periodos.some((p) => String(p.id) === solicitada)) { filtro.elements.periodo_id.value = solicitada; cargar().catch((error) => { mensaje.textContent = error.message; }); }
  }).catch((error) => { mensaje.textContent = error.message; });
}
