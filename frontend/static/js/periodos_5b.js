"use strict";
const periodo5bAlta = document.querySelector("#periodo-5b-alta");
if (periodo5bAlta) {
  const mensaje = document.querySelector("#periodos-5b-mensaje");
  const lista = document.querySelector("#periodos-5b-lista");
  const nombres = { FISICA_1: "Física 1", FISICA_2: "Física 2", ACADEMICA: "Académica global", DESEMPENO_JEFE: "Desempeño del Jefe", DESEMPENO_COMANDANTE: "Desempeño del Comandante" };
  const categorias = { FISICA_1: "FISICA", FISICA_2: "FISICA", ACADEMICA: "ACADEMICA", DESEMPENO_JEFE: "JEFE_PERSONAL", DESEMPENO_COMANDANTE: "JEFE_PERSONAL" };
  async function cargarPeriodos5b() {
    const [{ periodos }, { evaluaciones }] = await Promise.all([apiJson("/api/admin/5b/periodos"), apiJson("/api/admin/evaluaciones")]);
    lista.replaceChildren();
    if (!periodos.length) lista.append(elemento("p", "No hay períodos registrados."));
    periodos.forEach((periodo) => {
      const conf = periodo.configuracion; const tarjeta = elemento("article", undefined, "tarjeta-modulo");
      tarjeta.append(elemento("h3", periodo.nombre), elemento("p", `${periodo.fecha_inicio} — ${periodo.fecha_fin} · ${periodo.estado}`));
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
        const form = elemento("form", undefined, "formulario-inline");
        Object.entries(nombres).forEach(([fuente, nombre]) => {
          const label = elemento("label", nombre); const select = elemento("select"); select.name = fuente;
          const vacio = elemento("option", "Sin definir"); vacio.value = ""; select.append(vacio);
          evaluaciones.filter((e) => e.categoria === categorias[fuente] && e.origen_nota === "JEFE_PERSONAL").forEach((e) => {
            const opcion = elemento("option", `${e.nombre} · ${e.activo ? "Activa" : "Inactiva"}`); opcion.value = e.id;
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
      } else if (!conf) tarjeta.append(elemento("p", "Período histórico sin configuración 5B; sus datos se conservan."));
      if (conf?.estado === "PUBLICADA") tarjeta.append(elemento("p", "Configuración congelada. Los cambios de catálogo no reescriben estas fuentes."));
      lista.append(tarjeta);
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
