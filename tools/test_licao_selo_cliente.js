// A lição seguinte chega na mesma rajada que o selo da anterior: a janela refeita não pode apagá-lo.
const fs = require('fs');
const vm = require('vm');
const assert = require('assert');

const game = fs.readFileSync('game.js', 'utf8');
const fn = game.match(/^function _mostrarJanelaLicao[\s\S]*?^}/m)?.[0];
assert.ok(fn, '_mostrarJanelaLicao deve existir');

function no(cls) {
  return { className: cls, classList: { contains: c => cls.split(' ').includes(c) } };
}
const host = {
  children: [], _open: false,
  classList: { add: () => { host._open = true; }, remove() {}, contains: () => host._open },
  appendChild(el) { host.children.push(el); },
  set innerHTML(v) { host.children = []; host.html = v; },
};
const ctx = {
  $: () => host, _licaoUltima: null, _guiaFecharPasso() {}, _guiaIniciar() {}, _esc: s => String(s),
  _tutHTML: s => String(s), t: k => k, _guiaMostrar() {}, GS: {},
  GuiaTutorial: { parseUi: () => null },
};
vm.createContext(ctx);
vm.runInContext(`${fn}; this.f = _mostrarJanelaLicao;`, ctx);

const msg = { falante: { nome: 'x', emoji: 'y' }, texto: 't', licao_id: 'b',
              passo: { id: 'p', texto: 'a', i: 0, n: 2, informativo: true } };
ctx.f(msg);
const selo = no('licao-selo'), ok = no('licao-ok'), outro = no('licao-acoes');
host.children = [outro, selo, ok];
ctx.f(msg);
assert.ok(host.children.includes(selo), 'o selo da lição concluída sobrevive à próxima lição');
assert.ok(host.children.includes(ok), 'o ✓ do passo sobrevive');
assert.ok(!host.children.includes(outro), 'o resto é refeito');
console.log('licao selo cliente: ok');
