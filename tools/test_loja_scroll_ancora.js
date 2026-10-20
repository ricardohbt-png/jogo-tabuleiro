// O scroll da loja não pode pular ao comprar: a âncora é a linha do item comprado,
// mesmo quando o foco ficou numa linha de uma compra anterior.
// Roda da raiz: node tools/test_loja_scroll_ancora.js
const fs = require('fs');
const vm = require('vm');
const src = fs.readFileSync(require('path').join(__dirname, '..', 'game.js'), 'utf8');
function section(start, end) {
  const a = src.indexOf(start), b = src.indexOf(end, a);
  if (a < 0 || b < 0) throw new Error(`Trecho não encontrado: ${start}`);
  return src.slice(a, b);
}
let falhas = 0;
function check(label, ok) { console.log((ok ? '  ✅ ' : '  ❌ ') + label); if (!ok) falhas++; }

// Lista de 3 linhas de 60px; a lista começa em y=100 e está rolada 200px.
const lista = { scrollTop: 200, getBoundingClientRect: () => ({ top: 100 }), classList: { contains: () => true } };
const linhas = ['a', 'b', 'c'].map((id, i) => ({
  dataset: { shopItemId: id },
  getBoundingClientRect: () => ({ top: 100 + i * 60 - (lista.scrollTop - 200) }),
  closest() { return this; },
}));
lista.querySelectorAll = () => linhas;
let focoAtual = linhas[0];                       // foco "velho", de uma compra anterior
const sandbox = {
  $: id => id === 'shop-modal' ? { classList: { contains: () => true } } : id === 'shop-items-list' ? lista : null,
  GS: { activeShop: 'mercador', shopTabIdx: 1 },
  _gamepadUi: null,
  document: { get activeElement() { return focoAtual; } },
  window: {},
};
vm.createContext(sandbox);
vm.runInContext(section('function _guardarSelecaoLoja(', 'function _restaurarSelecaoLoja('), sandbox);

vm.runInContext("_guardarSelecaoLoja('c')", sandbox);   // compra a linha c com o foco ainda na linha a
const r = sandbox.window._shopSelectionRestore;
check('a âncora é a linha do item comprado, não a do foco antigo', r.rowIndex === 2);
check('relativeTop é a distância da linha comprada ao topo da lista (120px)', r.relativeTop === 120);

focoAtual = linhas[2];                           // foco na própria linha comprada
vm.runInContext("_guardarSelecaoLoja('c')", sandbox);
check('com o foco na linha certa nada muda', sandbox.window._shopSelectionRestore.rowIndex === 2);
process.exit(falhas ? 1 : 0);
