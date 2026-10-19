// Exercita a renderização da carta e a descrição de loja sem iniciar o DOM do jogo.
const fs = require('fs');
const vm = require('vm');
const src = fs.readFileSync(require('path').join(__dirname, '..', 'game.js'), 'utf8');

function section(start, end) {
  const a = src.indexOf(start);
  const b = src.indexOf(end, a);
  if (a < 0 || b < 0) throw new Error(`Trecho não encontrado: ${start}`);
  return src.slice(a, b);
}
function check(label, condition) {
  if (!condition) throw new Error(label);
  console.log(`  ✅ ${label}`);
}

const spell = {id: 'jato_ar', nome: 'Jato de Ar', circulo: 'segundo', icone: '🌬️', descricao: 'Empurra o alvo.'};
const sandbox = {
  GRIMORIO_CLIENT: {jato_ar: spell},
  GRIMORIO_IMPLEMENTADAS_CLIENT: new Set(['jato_ar']),
  _COR_CIRCULO: {segundo: '#55aaff'},
  _RGB_CIRCULO: {segundo: '85,170,255'},
  magiaIconFill: () => '🌬️',
  _magiasConhecidasIds: hero => [...(hero.magias_conhecidas || [])],
  _slotsMaxParaHeroi: hero => hero.slots_max || {},
  _renderAcaoSenhorDasAguas: () => '',
  _renderAcaoIraRocha: () => '',
  _renderAcaoChamadoInverno: () => '',
  _renderAcaoTempestade: () => '',
  _renderAcoesEncerrarMagias: () => '',
  _labelCirculo: id => id,
  t: key => key,
  GS: {gameState: {round: 1}},
  window: null,
};
sandbox.window = sandbox;
vm.createContext(sandbox);
vm.runInContext(section('function criarCartaMagia(', '// Tooltip da carta')
  + section('function renderMagiasFichaEmJogo(', '// Seleção de magias na criação'), sandbox);

console.log('\n[1] Conteúdo das ofertas de loja');
vm.runInContext(section('function _itemDesc(', 'function buyItem('), sandbox);
const desc = sandbox._itemDesc({effect: 'grimoire', name: 'Grimório', magic_ids: ['jato_ar'], descricao: 'Contém Jato de Ar.'});
check('o cliente mostra a descrição com o conteúdo fixo', desc.includes('Jato de Ar'));

console.log('\n[2] Magia acima do círculo disponível');
let html = sandbox.renderMagiasFichaEmJogo({
  class_id: 'mage', magias_conhecidas: [], magias_grimorio: ['jato_ar'],
  slots_max: {primeiro: 2, segundo: 0}, slots_remaining: {}, level: 1,
}, 'mage');
check('a carta aparece marcada como magia do grimório', html.includes('data-magia-id="jato_ar"') && html.includes('GRIMÓRIO'));
check('a carta fica visível, sem slot e sem ação de clique',
  html.includes('sem slot deste círculo') && html.includes('cursor:not-allowed') && !html.includes("castarMagia('jato_ar')"));

console.log('\n[3] Magia com slot e suporte ativo');
html = sandbox.renderMagiasFichaEmJogo({
  class_id: 'mage', magias_conhecidas: [], magias_grimorio: ['jato_ar'],
  slots_max: {primeiro: 2, segundo: 1}, slots_remaining: {}, level: 3,
}, 'mage');
check('a carta habilita conjuração usando slot normal', html.includes("castarMagia('jato_ar')"));

console.log('\n[4] Magia ainda em desenvolvimento');
sandbox.GRIMORIO_IMPLEMENTADAS_CLIENT = new Set();
html = sandbox.renderMagiasFichaEmJogo({
  class_id: 'mage', magias_conhecidas: [], magias_grimorio: ['jato_ar'],
  slots_max: {primeiro: 2, segundo: 1}, slots_remaining: {}, level: 3,
}, 'mage');
check('a carta continua visível e marcada, mas desativada',
  html.includes('data-magia-id="jato_ar"') && html.includes('GRIMÓRIO')
  && html.includes('cursor:not-allowed') && !html.includes("castarMagia('jato_ar')"));
