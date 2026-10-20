// A descrição da loja não pode vazar o id técnico do efeito (ex.: ILLUSION_LURE).
// Roda da raiz: node tools/test_item_desc_efeito.js
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

// Só o ui.item.efeito.heal existe no dicionário de mentira; o resto cai no fallback.
const chaves = { 'ui.item.efeito.bagslots': 'Slots de mochila' };
const sandbox = {
  I18N: { tem: k => k in chaves },
  t: k => chaves[k] ?? k,
  GRIMORIO_CLIENT: {},
  GS: { CATALOGO_ITENS: { frasco_x: { descricao: 'Descrição do catálogo.' } } },
};
vm.createContext(sandbox);
vm.runInContext(section('function _rotulo(', '// Os hotspots da cidade'), sandbox);
vm.runInContext(section('function _itemDesc(', 'function buyItem('), sandbox);
const d = item => vm.runInContext('_itemDesc', sandbox)(item);

check('efeito sem rótulo usa a descrição do próprio item',
  d({ id: 'ignus_fatus', effect: 'illusion_lure', value: 2, descricao: 'Cria uma isca.' }) === 'Cria uma isca.');
check('sem descrição no item, usa a do catálogo do cliente',
  d({ id: 'frasco_x', effect: 'throwable' }) === 'Descrição do catálogo.');
check('efeito COM rótulo traduzido continua mostrando o rótulo + valor',
  d({ id: 'mochila', effect: 'bagslots', value: 2, descricao: 'ignorada' }) === 'Slots de mochila 2');
check('sem rótulo e sem descrição, o id técnico ainda é o último recurso (comportamento antigo)',
  d({ id: 'sem_nada', effect: 'efeito_novo', value: 3 }) === 'efeito_novo 3');
process.exit(falhas ? 1 : 0);
