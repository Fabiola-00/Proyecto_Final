// Sin dependencias: contrato de preferencias y seguimiento del sistema.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const js = fs.readFileSync('frontend/static/js/app.js', 'utf8');
const bloque = js.slice(0, js.indexOf('if (appShell && sidebarButton)'));
function entorno(preferencia, oscuro, bloqueo = false) {
  const eventos = {}, sistemaEventos = {}, selectorEventos = {};
  const root = {dataset: {}, style: {}};
  const almacen = new Map(preferencia ? [['sicose-tema', preferencia]] : []);
  const selector = {setAttribute:()=>{}, addEventListener:(e,f) => selectorEventos[e] = f};
  const sistema = {matches:oscuro, addEventListener:(e,f) => sistemaEventos[e] = f};
  const window = {localStorage:{getItem:k => {if(bloqueo)throw Error();return almacen.get(k);}, setItem:(k,v) => {if(bloqueo)throw Error();almacen.set(k,v);}}, matchMedia:()=>sistema, addEventListener:(e,f) => eventos[e] = f};
  vm.runInNewContext(bloque,{window,document:{documentElement:root,querySelector:s => s === '#boton-tema' ? selector : null}});
  return {root,almacen,selector,selectorEventos,sistema,sistemaEventos,eventos};
}
let e = entorno(null,true);
assert.equal(e.root.dataset.theme,'dark');
e.sistema.matches=false; e.sistemaEventos.change(); assert.equal(e.root.dataset.theme,'light');
e.selectorEventos.click(); assert.equal(e.almacen.get('sicose-tema'),'dark');
e.sistema.matches=false; e.sistemaEventos.change(); assert.equal(e.root.dataset.theme,'dark');
e.eventos.storage({key:'sicose-tema',newValue:'light'}); assert.equal(e.root.dataset.theme,'light');
e.eventos.storage({key:'sicose-tema',newValue:null});
assert.equal(entorno('valor-invalido',true).root.dataset.theme,'dark');
assert.equal(entorno(null,true,true).root.dataset.theme,'dark');
assert.equal(entorno('light',true).root.dataset.theme,'light');
assert.equal(entorno('dark',false).root.dataset.theme,'dark');
console.log('Preferencias: sistema, cambio del equipo, manual, persistencia, otra pestaña y almacenamiento bloqueado: OK');
