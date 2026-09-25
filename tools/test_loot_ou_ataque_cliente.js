// Escolha "pegar item ou atacar" quando monstro e item dividem a casa.
// Roda da raiz: node tools/test_loot_ou_ataque_cliente.js
'use strict';
const fs = require('fs');
const path = require('path');
const GAME = fs.readFileSync(path.join(__dirname, '..', 'game.js'), 'utf8');
let PASS = 0, FAIL = 0;
const check = (n, c) => { if(c){ PASS++; console.log('  ✅ ' + n); } else { FAIL++; console.log('  ❌ ' + n); } };

function extrair(nome){
  const i = GAME.indexOf('function ' + nome + '(');
  if(i < 0) throw new Error('não achei ' + nome);
  let d = 0;
  for(let k = GAME.indexOf('{', i); k < GAME.length; k++){
    if(GAME[k] === '{') d++; else if(GAME[k] === '}'){ d--; if(!d) return GAME.slice(i, k + 1); }
  }
}

// DOM mínimo: elementos com filhos, classes e onclick.
function el(tag){
  return { tag, children: [], style: {}, textContent: '', innerHTML: '', onclick: null,
    classList: { set: new Set(), add(c){ this.set.add(c); }, remove(c){ this.set.delete(c); } },
    append(...c){ this.children.push(...c); }, appendChild(c){ this.children.push(c); } };
}
const dom = { 'target-modal': el('div'), 'target-list': el('div'), 'target-title': el('div') };
const document = { createElement: el };
const $ = id => dom[id];
const t = (k, p) => k + (p ? JSON.stringify(p) : '');
const log = [];
let resolveResposta = null;
const GS = {
  gameState: { monsters: [{ id: 'm1', name: 'Goblin', hp: 5, max_hp: 7 }] },
  pickupItem: id => log.push(['pegar', id]),
  resolveTileClick: () => resolveResposta,
  notifyAttack: () => log.push(['notify']),
};
const sendAttack = (id, pos) => log.push(['atacar', id, pos]);
const closeTargetModal = () => dom['target-modal'].classList.remove('open');
const _gamepadSetUiFocus = () => {};
const _gamepadFocusMapPoint = () => {};
const toast = m => log.push(['toast', m]);

const abrir = eval('(' + extrair('_abrirEscolhaLootOuAtaque') + ')');
const gi = { id: 'g1', item: { name: 'Espada' } };
const ataque = { type: 'attack', targetId: 'm1', targetPos: [3, 4] };

console.log('\n[1] Abre o painel com as duas ações');
check('abre quando há item e monstro vivo', abrir(gi, ataque) === true);
check('o painel fica aberto', dom['target-modal'].classList.set.has('open'));
const botoes = dom['target-list'].children;
check('duas escolhas', botoes.length === 2);
check('o texto do loot é traduzível (sem português cru)', !GAME.includes("'Recolher o loot'") && GAME.includes("t('ui.bau.recolher_loot')"));

console.log('\n[2] Pegar o item');
botoes[0].onclick();
check('pega o item certo', log.some(l => l[0] === 'pegar' && l[1] === 'g1'));
check('e fecha o painel', !dom['target-modal'].classList.set.has('open'));

console.log('\n[3] Atacar revalida no estado mais recente');
log.length = 0; dom['target-list'].children.length = 0;
abrir(gi, ataque);
resolveResposta = { type: 'attack', targetId: 'm1', targetPos: [3, 4] };
dom['target-list'].children[1].onclick();
check('ataque válido é enviado', log.some(l => l[0] === 'atacar' && l[1] === 'm1'));
log.length = 0; dom['target-list'].children.length = 0;
abrir(gi, ataque);
resolveResposta = { type: 'move' };   // o monstro saiu enquanto o painel estava aberto
dom['target-list'].children[1].onclick();
check('se o monstro saiu, não ataca', !log.some(l => l[0] === 'atacar'));
check('e avisa', log.some(l => l[0] === 'toast'));

console.log('\n[4] Recusa quando não há o que escolher');
check('sem item: não abre', abrir(null, ataque) === false);
check('monstro morto: não abre', (GS.gameState.monsters[0].hp = 0, abrir(gi, ataque)) === false);
GS.gameState.monsters[0].hp = 5;
check('ação que não é ataque: não abre', abrir(gi, { type: 'move' }) === false);

console.log('\n[5] Ligado no clique do tabuleiro');
check('handleTileClick oferece a escolha antes de atacar',
  /if\(podePegar && ataque\?\.type === 'attack'\)\{\s*if\(_abrirEscolhaLootOuAtaque\(gi, ataque\)\) return;/.test(GAME));

console.log(`\n${'='.repeat(50)}\n  ${PASS} passaram, ${FAIL} falharam\n${'='.repeat(50)}`);
process.exit(FAIL ? 1 : 0);
