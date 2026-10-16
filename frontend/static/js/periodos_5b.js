"use strict";
const periodo5bAlta = document.querySelector("#periodo-5b-alta");
if (periodo5bAlta) {
  const mensaje = document.querySelector("#periodos-5b-mensaje");
  const lista = document.querySelector("#periodos-5b-lista");
  const administrador = document.body.dataset.rol === "ADMINISTRADOR";
  const nombres = { FISICA_1: "Física 1", FISICA_2: "Física 2", ACADEMICA: "Académica", DESEMPENO_JEFE: "Desempeño del Jefe", DESEMPENO_COMANDANTE: "Desempeño del Comandante" };
  const categorias = { FISICA_1: "FISICA", FISICA_2: "FISICA", ACADEMICA: "ACADEMICA", DESEMPENO_JEFE: "JEFE_PERSONAL", DESEMPENO_COMANDANTE: "JEFE_PERSONAL" };
  function mostrarPersonasCierre(panel, personas) {
    const incompletos = personas.filter((p) => p.calculo.estado !== "COMPLETO");
    panel.append(elemento("p", `${personas.length} ${personas.length === 1 ? "persona" : "personas"} · ${incompletos.length} ${incompletos.length === 1 ? "incompleta" : "incompletas"}. Los faltantes se conservan sin cero ni redistribución.`));
    if (!personas.length) panel.append(elemento("p", "Sin personas en el alcance del cierre."));
    personas.forEach((p) => {
      const articulo = elemento("article", undefined, "historial-formacion");
      articulo.append(elemento("strong", `${p.persona.nombre} · ${p.persona.codigo || "Sin código"} · ${p.persona.estado}`),
        elemento("p", `${p.calculo.estado} · Resultado conjunto: ${p.calculo.resultado_conjunto ?? "No disponible"}`));
      if (p.calculo.faltantes.length) articulo.append(elemento("p", `Faltantes: ${p.calculo.faltantes.map((f) => nombres[f] || f).join(", ")}`));
      if (p.calculo.regla) articulo.append(elemento("p", `Física: ${p.calculo.fisica ?? "Pendiente"} · Académica: ${p.calculo.academica.valor ?? "Pendiente"} · Desempeño: ${p.calculo.desempeno ?? "Pendiente"}`));
      const exacto = p.calculo.resultado_exacto_centesimas;
      if (exacto) articulo.append(elemento("p", `Resultado exacto en centésimas: ${exacto.numerador}/${exacto.denominador}`));
      const fuentes = elemento("details"); fuentes.append(elemento("summary", "Fuentes conservadas"));
      (p.notas || []).forEach((n) => fuentes.append(elemento("p", `${n.fuente} · ${p.calculo.fuentes?.[n.fuente]?.nota_id === n.id ? "Vigente al cierre" : "Histórica conservada"} · Nota #${n.id}: ${(n.puntos_centesimas / 100).toFixed(2)} · Evaluador: ${n.evaluador_nombre} · Transcripción: ${n.registrada_por_nombre} · ${n.registrada_en}`)));
      (p.formacion || []).forEach((f) => fuentes.append(elemento("p", `${f.nombre_curso} · ${f.estado} · ${f.puntaje ?? "Pendiente"} puntos · ${f.fecha_finalizacion || "Sin finalización"} · revisión ${f.revision} · ${f.responsable_nombre}`)));
      articulo.append(fuentes); panel.append(articulo);
    });
  }
  function mostrarEvidenciaHistorica(panel, evidencia) {
    panel.append(elemento("p", "No existe instantánea del cierre original. Esta evidencia no acredita su fecha ni sus resultados; corresponde exclusivamente al momento de la reapertura y no adopta notas."));
    panel.append(elemento("p", `Gestión: ${evidencia.contexto.periodo.nombre} · Configuración: ${evidencia.contexto.configuracion?.id ?? "Sin configuración 5B"} · Personas documentadas: ${evidencia.personas.length}`));
    evidencia.personas.forEach((p) => {
      const fila = elemento("article", undefined, "historial-formacion");
      fila.append(elemento("strong", `${p.persona.nombre} · ${p.persona.codigo || "Sin código"} · ${p.persona.estado}`));
      (p.notas || []).forEach((n) => fila.append(elemento("p", `Dato disponible · ${n.fuente} · Nota #${n.id}: ${(n.puntos_centesimas / 100).toFixed(2)} · ${n.evaluador_nombre} · ${n.registrada_en}`)));
      (p.formacion || []).forEach((f) => fila.append(elemento("p", `${f.nombre_curso} · ${f.estado} · ${f.puntaje ?? "Sin puntaje"} · ${f.fecha_finalizacion || "Sin finalización"} · revisión ${f.revision}`)));
      if (!p.notas?.length && !p.formacion?.length) fila.append(elemento("p", "Sin notas operativas ni formación pertinente documentadas."));
      panel.append(fila);
    });
  }
  function accionesHistoricas(periodo, tarjeta) {
    if (periodo.reapertura_historica) {
      const panel = elemento("div"); const boton = botonEdicion(`Evidencia de reapertura · ${periodo.nombre}`, panel, "Evidencia de reapertura histórica");
      boton.addEventListener("click", async () => {
        panel.replaceChildren(elemento("p", "Cargando evidencia conservada…"));
        try {
          const { reapertura } = await apiJson(`/api/5b/periodos/${periodo.id}/reapertura-historica`);
          panel.replaceChildren(elemento("p", `${reapertura.actor_nombre} · ${reapertura.registrada_en} · ${reapertura.motivo}`));
          mostrarEvidenciaHistorica(panel, reapertura.evidencia);
        } catch (error) { panel.replaceChildren(elemento("p", error.message)); }
      }); tarjeta.append(boton);
    } else if (periodo.estado === "CERRADO" && !periodo.cierres?.length && !periodo.retirada) {
      const panel = elemento("div"); const abrir = botonEdicion(`Histórico sin instantánea · ${periodo.nombre}`, panel, administrador ? "Reabrir histórico sin instantánea" : "Revisar histórico sin instantánea");
      abrir.addEventListener("click", async () => {
        panel.replaceChildren(elemento("p", "Cargando evidencia disponible…"));
        try {
          const vista = await apiJson(`/api/5b/periodos/${periodo.id}/reapertura-historica-previa`);
          panel.replaceChildren(); mostrarEvidenciaHistorica(panel, vista);
          if (!administrador) return;
          panel.append(elemento("p", "La reapertura conserva la configuración/regla existentes. No activa una regla nueva ni publica notas. Solo se permite sin otra Gestión activa."));
          const form = elemento("form", undefined, "formulario-inline"); const label = elemento("label", "Motivo de reapertura excepcional");
          const motivo = elemento("textarea"); motivo.required = true; motivo.maxLength = 2000; label.append(motivo);
          const constancia = elemento("label", "Confirmo que no existe instantánea original y que la evidencia se toma al reabrir"); const confirmar = elemento("input"); confirmar.type = "checkbox"; confirmar.required = true; constancia.prepend(confirmar);
          const guardar = elemento("button", "Confirmar reapertura excepcional"); form.append(label, constancia, guardar); panel.append(form);
          form.addEventListener("submit", async (event) => {
            event.preventDefault(); if (!form.reportValidity()) return; guardar.disabled = true;
            try {
              await apiJson(`/api/admin/5b/periodos/${periodo.id}/reabrir-historico`, { method: "POST", body: { motivo: motivo.value, firma_fuentes: vista.firma_fuentes, confirmar_sin_instantanea: confirmar.checked } });
              cerrarEdicion(); mensaje.textContent = "Histórico reabierto con constancia de ausencia de instantánea original. Evidencia actual conservada."; await cargarPeriodos5b();
            } catch (error) { mostrarErrorEdicion(error); } finally { guardar.disabled = false; }
          });
        } catch (error) { panel.replaceChildren(elemento("p", error.message)); }
      }); tarjeta.append(abrir);
    }
  }
  function accionesCierre(periodo, tarjeta) {
    accionesHistoricas(periodo, tarjeta);
    const cierres = periodo.cierres || [];
    if (periodo.estado === "ACTIVO" && !periodo.retirada) {
      const panel = elemento("div");
      const abrir = botonEdicion(`Revisión de cierre · ${periodo.nombre}`, panel, administrador ? "Revisar y cerrar gestión" : "Consultar pendientes de cierre");
      abrir.addEventListener("click", async () => {
        panel.replaceChildren(elemento("p", "Cargando revisión de fuentes…"));
        try {
          const vista = await apiJson(`/api/5b/periodos/${periodo.id}/cierre-previo`);
          panel.replaceChildren(elemento("p", "El cierre conserva una instantánea de fuentes y resultados. No publica ni republica notas. La configuración permanece intacta."));
          if (!vista.contexto.regla_calculo) panel.append(elemento("p", "Sin regla v2: cierre histórico documental, sin adoptar notas ni generar resultado conjunto."));
          mostrarPersonasCierre(panel, vista.personas);
          if (!administrador) return;
          const form = elemento("form", undefined, "formulario-inline"); const label = elemento("label", "Motivo del cierre");
          const motivo = elemento("textarea"); motivo.required = true; motivo.maxLength = 2000; label.append(motivo);
          const confirmarLabel = elemento("label", "He revisado las personas y acepto cerrar con los incompletos indicados");
          const confirmar = elemento("input"); confirmar.type = "checkbox"; confirmar.required = true; confirmarLabel.prepend(confirmar);
          const cerrar = elemento("button", "Confirmar cierre"); form.append(label, confirmarLabel, cerrar); panel.append(form);
          form.addEventListener("submit", async (event) => {
            event.preventDefault(); if (!form.reportValidity()) return; cerrar.disabled = true;
            try {
              await apiJson(`/api/admin/5b/periodos/${periodo.id}/cerrar`, { method: "POST", body: { motivo: motivo.value, firma_fuentes: vista.firma_fuentes, cierre_anterior_id: vista.cierre_anterior_id, confirmar_incompletos: confirmar.checked } });
              cerrarEdicion(); mensaje.textContent = "Gestión cerrada; instantáneas conservadas. Las notas publicadas no cambiaron."; await cargarPeriodos5b();
            } catch (error) { mostrarErrorEdicion(error); } finally { cerrar.disabled = false; }
          });
        } catch (error) { panel.replaceChildren(elemento("p", error.message)); }
      }); tarjeta.append(abrir);
    }
    if (cierres.length) {
      const panel = elemento("div");
      cierres.forEach((c) => {
        panel.append(elemento("p", `Cierre ${c.numero} · ${c.actor_nombre} · ${c.registrada_en} · ${c.motivo} · ${c.incompletos}/${c.total_personas} incompletos`));
        if (c.reapertura_id) panel.append(elemento("p", `Reapertura: ${c.reabierta_por} · ${c.reabierta_en} · ${c.motivo_reapertura}`));
        const detalle = elemento("button", `Consultar instantáneas del cierre ${c.numero}`); detalle.type = "button";
        detalle.addEventListener("click", async () => {
          detalle.disabled = true;
          try {
            const { cierre } = await apiJson(`/api/5b/periodos/${periodo.id}/cierres/${c.id}`);
            const salida = elemento("div"); salida.append(elemento("h4", `Cierre ${cierre.numero} · ${cierre.actor_nombre} · ${cierre.registrada_en}`), elemento("p", cierre.motivo), elemento("p", `Gestión capturada: ${cierre.contexto.periodo.nombre} · Configuración ${cierre.contexto.configuracion?.id ?? "histórica sin configuración 5B"}. Consulta conservada, sin recalcular con datos actuales.`));
            mostrarPersonasCierre(salida, cierre.personas); visor.replaceChildren(salida);
          } catch (error) { mostrarErrorEdicion(error); } finally { detalle.disabled = false; }
        }); panel.append(detalle);
      });
      const visor = elemento("div"); panel.append(visor);
      tarjeta.append(botonEdicion(`Cierres e instantáneas · ${periodo.nombre}`, panel, "Historial de cierres"));
    }
    if (administrador && periodo.estado === "CERRADO" && cierres.length && !periodo.retirada) {
      const form = elemento("form", undefined, "formulario-inline");
      form.append(elemento("p", "Reabrir conserva todos los cierres, resultados y configuración. Se rechazará si existe otra Gestión activa. Las correcciones no se publican automáticamente."));
      const label = elemento("label", "Motivo de reapertura"); const motivo = elemento("textarea"); motivo.required = true; motivo.maxLength = 2000; label.append(motivo);
      const boton = elemento("button", "Confirmar reapertura"); form.append(label, boton);
      form.addEventListener("submit", async (event) => {
        event.preventDefault(); if (!form.reportValidity()) return; boton.disabled = true;
        try { await apiJson(`/api/admin/5b/periodos/${periodo.id}/reabrir`, { method: "POST", body: { motivo: motivo.value, cierre_id: cierres[cierres.length - 1].id } }); cerrarEdicion(); mensaje.textContent = "Gestión reabierta; cierres anteriores preservados."; await cargarPeriodos5b(); }
        catch (error) { mostrarErrorEdicion(error); } finally { boton.disabled = false; }
      }); tarjeta.append(botonEdicion(`Reabrir · ${periodo.nombre}`, form, "Reabrir gestión"));
    }
    if (periodo.estado === "CERRADO" && !cierres.length) tarjeta.append(elemento("p", "Cierre histórico sin instantáneas: no se reconstruye el cierre anterior; la reapertura excepcional requiere revisión y constancia administrativa."));
  }
  async function cargarPeriodos5b() {
    const [{ periodos, retiradas = [] }, { evaluaciones }] = await Promise.all([apiJson("/api/admin/5b/periodos"), apiJson("/api/admin/evaluaciones")]);
    lista.replaceChildren();
    if (!periodos.length) lista.append(elemento("p", "No hay períodos registrados."));
    periodos.forEach((periodo) => {
      const conf = periodo.configuracion; const tarjeta = elemento("article", undefined, "tarjeta-modulo");
      tarjeta.append(elemento("h3", periodo.nombre), elemento("p", `${periodo.fecha_inicio} — ${periodo.fecha_fin} · ${periodo.estado}`));
      if (periodo.modelo_anual) { const enlace=elemento('a','Administrar período y evaluación','boton');enlace.href=`/gestion/modelo-anual?periodo_id=${periodo.id}`;tarjeta.append(elemento('p','Modelo de cinco entradas · ceros oficiales'),enlace);lista.append(tarjeta);return; }
      if (conf) {
        tarjeta.append(elemento("p", `Configuración ${conf.version} · revisión ${conf.revision} · ${conf.estado}`));
        conf.fuentes.forEach((f) => tarjeta.append(elemento("p", `${nombres[f.fuente]}: ${f.nombre} (${f.codigo})`)));
      }
      if (periodo.estado === "BORRADOR" && periodo.anual && !periodo.tiene_notas_5b && conf?.estado !== "PUBLICADA") {
        const gestion = elemento("form", undefined, "formulario-inline");
        [["nombre", "Nombre de la gestión", "text", periodo.nombre], ["ano", "Gestión (año)", "number", periodo.fecha_inicio.slice(0, 4)]].forEach(([campo, etiqueta, tipo, valor]) => {
          const label = elemento("label", etiqueta); const input = elemento("input"); input.name = campo; input.type = tipo; input.required = true; input.value = valor;
          if (tipo === "number") { input.min = "1"; input.max = "9999"; input.step = "1"; } else input.maxLength = 120;
          label.append(input); gestion.append(label);
        });
        const guardarGestion = elemento("button", "Guardar gestión"); gestion.append(guardarGestion);
        gestion.addEventListener("submit", async (event) => {
          event.preventDefault(); if (!gestion.reportValidity()) return; guardarGestion.disabled = true;
          const body = Object.fromEntries(new FormData(gestion)); body.ano = Number(body.ano); body.nombre_anterior = periodo.nombre; body.ano_anterior = Number(periodo.fecha_inicio.slice(0, 4));
          try { await apiJson(`/api/admin/5b/periodos/${periodo.id}`, { method: "PATCH", body }); cerrarEdicion(); mensaje.textContent = "Gestión actualizada."; await cargarPeriodos5b(); }
          catch (error) { mostrarErrorEdicion(error); }
          finally { guardarGestion.disabled = false; }
        });
        if (!periodo.tiene_asignaciones) tarjeta.append(botonEdicion(`Editar gestión · ${periodo.nombre}`, gestion, "Editar gestión"));
        if (administrador) {
        const form = elemento("form", undefined, "formulario-inline");
        Object.entries(nombres).forEach(([fuente, nombre]) => {
          const label = elemento("label", nombre); const select = elemento("select"); select.name = fuente;
          const vacio = elemento("option", "Sin definir"); vacio.value = ""; select.append(vacio);
          evaluaciones.filter((e) => e.categoria === categorias[fuente] && e.origen_nota === "JEFE_PERSONAL").forEach((e) => {
            const opcion = elemento("option", `${e.nombre} · ${e.activo ? "Disponible" : "No disponible"}`); opcion.value = e.id;
            opcion.selected = (conf?.fuentes || []).some((f) => f.fuente === fuente && f.evaluacion_id === e.id); select.append(opcion);
          });
          label.append(select); form.append(label);
        });
        form.append(elemento("p", "Las cinco fuentes son independientes; pueden usar la misma evaluación de catálogo cuando su categoría corresponda. Guardar un borrador no lo activa."));
        const guardar = elemento("button", "Guardar configuración"); form.append(guardar);
        form.addEventListener("submit", async (event) => {
          event.preventDefault(); guardar.disabled = true;
          const fuentes = Object.fromEntries(Array.from(new FormData(form), ([k, v]) => [k, v ? Number(v) : null]));
          const body = { fuentes }; if (conf) body.revision = conf.revision;
          try { await apiJson(`/api/admin/5b/periodos/${periodo.id}/configuracion`, { method: conf ? "PATCH" : "POST", body }); cerrarEdicion(); mensaje.textContent = "Borrador guardado."; await cargarPeriodos5b(); }
          catch (error) { mostrarErrorEdicion(error); }
          finally { guardar.disabled = false; }
        });
        tarjeta.append(botonEdicion(`Configurar fuentes · ${periodo.nombre}`, form, "Configurar fuentes"));
        if (conf) {
          const publicar = elemento("button", "Publicar y activar");
          publicar.addEventListener("click", async () => {
            if (!window.confirm(`¿Publicar y activar ${periodo.nombre}? Su configuración quedará congelada.`)) return;
            publicar.disabled = true;
            try { await apiJson(`/api/admin/5b/periodos/${periodo.id}/publicar`, { method: "POST", body: { revision: conf.revision } }); mensaje.textContent = "Período activo y configuración congelada."; await cargarPeriodos5b(); }
            catch (error) { mensaje.textContent = error.message; publicar.disabled = false; }
          });
          tarjeta.append(publicar);
        }
        } else tarjeta.append(elemento("p", "El Administrador configura las fuentes y publica la gestión."));
      } else if (!conf) tarjeta.append(elemento("p", "Período histórico sin configuración 5B; sus datos se conservan."));
      if (conf?.estado === "PUBLICADA") tarjeta.append(elemento("p", "Configuración congelada. Los cambios de catálogo no reescriben estas fuentes."));
      const activaciones = elemento("div");
      (periodo.evaluaciones_gestion || []).forEach((e) => {
        const fila = elemento("div", undefined, "formulario-inline");
        fila.append(elemento("p", `${e.nombre}: ${e.activa ? "Activa" : "Inactiva"}${e.disponible ? "" : " · Sin instrumento aprobado"}`));
        if (["BORRADOR", "ACTIVO"].includes(periodo.estado)) {
          const form = elemento("form", undefined, "formulario-inline"); const label = elemento("label", "Motivo de activación o desactivación"); const motivo = elemento("textarea"); motivo.required = true; motivo.maxLength = 2000; label.append(motivo);
          const boton = elemento("button", e.activa ? "Desactivar evaluación" : "Activar evaluación"); form.append(label, boton);
          form.addEventListener("submit", async (event) => {
            event.preventDefault(); if (!form.reportValidity()) return; boton.disabled = true;
            try { await apiJson(`/api/5b/gestiones/${periodo.id}/evaluaciones/${e.clave}`, { method: "PATCH", body: { activa: !e.activa, revision: e.revision, motivo: motivo.value } }); cerrarEdicion(); await cargarPeriodos5b(); }
            catch (error) { mostrarErrorEdicion(error); } finally { boton.disabled = false; }
          });
          const accion = botonEdicion(`${e.nombre} · ${periodo.nombre}`, form, e.activa ? `Desactivar ${e.nombre}` : `Activar ${e.nombre}`);
          accion.disabled = !e.activa && !e.disponible; fila.append(accion);
        }
        activaciones.append(fila);
      });
      if (periodo.historial_activaciones?.length) {
        activaciones.append(elemento("h4", "Historial de activaciones"));
        periodo.historial_activaciones.forEach((h) => activaciones.append(elemento("p", `${nombres[h.clave] || "Psicométricas"}: ${h.activa ? "Activa" : "Inactiva"} · ${h.actor_nombre} · ${h.registrada_en} · ${h.motivo}`)));
      }
      tarjeta.append(botonEdicion(`Evaluaciones de la gestión · ${periodo.nombre}`, activaciones, "Activar/desactivar evaluaciones"));
      if (periodo.regla_calculo) tarjeta.append(elemento("p", periodo.estado === "CERRADO" ? "Cálculo ACUMULADO_TRES_V2 conservado en la instantánea del último cierre." : "Cálculo ACUMULADO_TRES_V2 activado; resultados provisionales en Notas y resultados."));
      else if (administrador && periodo.estado === "ACTIVO" && conf?.estado === "PUBLICADA" && !periodo.cierres?.length && !periodo.reapertura_historica) {
        const form = elemento("form", undefined, "formulario-inline");
        form.append(elemento("p", "Activar ACUMULADO_TRES_V2 usará notas vinculadas a esta configuración y cursos finalizados en el año. Excluye físicas sin resultado programado y notas antiguas sin configuración. Conserva PROMEDIO_TRES_V1. Sin formación finalizada, Académica queda pendiente. No publica notas ni cierra la gestión."));
        const label = elemento("label", "Confirmo ese alcance"); const confirmar = elemento("input"); confirmar.type = "checkbox"; confirmar.required = true; label.prepend(confirmar);
        const boton = elemento("button", "Activar regla nueva"); form.append(label, boton);
        form.addEventListener("submit", async (event) => {
          event.preventDefault(); if (!form.reportValidity()) return; boton.disabled = true;
          try { await apiJson(`/api/admin/5b/periodos/${periodo.id}/calculo`, { method: "POST", body: { configuracion_id: conf.id, regla: "ACUMULADO_TRES_V2", confirmar_fuentes: confirmar.checked } }); cerrarEdicion(); await cargarPeriodos5b(); }
          catch (error) { mostrarErrorEdicion(error); } finally { boton.disabled = false; }
        });
        tarjeta.append(botonEdicion(`Regla nueva · ${periodo.nombre}`, form, "Activar cálculo 5B.2"));
      }
      const baja = elemento("form", undefined, "formulario-inline"); baja.append(elemento("p", "Se retirará esta gestión de las listas operativas y se bloquearán sus nuevas acciones. Las notas, cursos e historial se conservan. Esta acción no constituye un cierre con instantánea."));
      const labelBaja = elemento("label", "Motivo de baja"); const motivoBaja = elemento("textarea"); motivoBaja.required = true; motivoBaja.maxLength = 2000; labelBaja.append(motivoBaja);
      const retirar = elemento("button", "Eliminar gestión conservando historial"); baja.append(labelBaja, retirar);
      baja.addEventListener("submit", async (event) => {
        event.preventDefault(); if (!baja.reportValidity()) return; retirar.disabled = true;
        try { await apiJson(`/api/admin/5b/periodos/${periodo.id}`, { method: "DELETE", body: { motivo: motivoBaja.value, nombre_anterior: periodo.nombre, ano_anterior: Number(periodo.fecha_inicio.slice(0, 4)), estado_anterior: periodo.estado } }); cerrarEdicion(); await cargarPeriodos5b(); }
        catch (error) { mostrarErrorEdicion(error); } finally { retirar.disabled = false; }
      });
      tarjeta.append(botonEdicion(`Eliminar gestión · ${periodo.nombre}`, baja, "Eliminar gestión"));
      if (periodo.historial_ediciones?.length) {
        const historial = elemento("div"); periodo.historial_ediciones.forEach((h) => historial.append(elemento("p", `${h.nombre_anterior} (${h.ano_anterior}) → ${h.nombre_nuevo} (${h.ano_nuevo}) · ${h.actor_nombre} · ${h.registrada_en}`)));
        tarjeta.append(botonEdicion(`Historial · ${periodo.nombre}`, historial, "Historial de la gestión"));
      }
      accionesCierre(periodo, tarjeta);
      lista.append(tarjeta);
    });
    if (retiradas.length) lista.append(elemento("h3", "Gestiones retiradas · solo historial", "gestiones-separador"));
    retiradas.forEach((p) => {
      const tarjeta = elemento("article", undefined, "tarjeta-modulo"); tarjeta.append(elemento("h3", p.nombre), elemento("p", `${p.fecha_inicio.slice(0, 4)} · Retirada · ${p.baja.actor_nombre} · ${p.baja.registrada_en} · ${p.baja.motivo}`));
      const enlace = elemento("a", "Consultar historial de evaluaciones", "enlace-accion"); enlace.href = `/gestion/tabla-evaluaciones?periodo_id=${p.id}`; tarjeta.append(enlace); accionesCierre(p, tarjeta); lista.append(tarjeta);
    });
  }
  periodo5bAlta.addEventListener("submit", async (event) => {
    event.preventDefault(); if (!periodo5bAlta.reportValidity()) return;
    const boton = periodo5bAlta.querySelector("button"); boton.disabled = true;
    const body = Object.fromEntries(new FormData(periodo5bAlta)); body.ano = Number(body.ano);
    try { await apiJson("/api/admin/5b/periodos", { method: "POST", body }); periodo5bAlta.reset(); mensaje.textContent = "Borrador anual creado."; await cargarPeriodos5b(); }
    catch (error) { mensaje.textContent = error.message; }
    finally { boton.disabled = false; }
  });
  cargarPeriodos5b().catch((error) => { mensaje.textContent = error.message; });
}
