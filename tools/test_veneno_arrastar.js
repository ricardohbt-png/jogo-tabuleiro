'use strict';
// Frasco de veneno arrastado no inventário: reconhece o frasco (bolsa/cinto), escolhe o alvo
// (arma ou pilha de munição) e o painel "Envenenar" mostra só esse alvo como confirmação.
// Roda da raiz: node tools/test_veneno_arrastar.js
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const root = path.join(__dirname, '..');
const game = fs.readFileSync(path.join(root, 'game.js'), 'utf8');
const modal = fs.readFileSync(path.join(root, 'src/ui/inventoryModal.js'), 'utf8');

let pass = 0, fail = 0;
const check = (nome, cond) => { if (cond) { pass++; console.log('  ✅ ' + nome); } else { fail++; console.log('  ❌ ' + nome); } };

function extrair(fonte, nome) {
  const ini = fonte.indexOf('function ' + nome + '(');
  if (ini < 0) throw new Error('função não encontrada: ' + nome);
  let prof = 0;
  for (let i = fonte.indexOf('{', ini); i < fonte.length; i++) {
    if (fonte[i] === '{') prof++;
    if (fonte[i] === '}' && !--prof) return fonte.slice(ini, i + 1);
  }
  throw new Error('chaves não fecham: ' + nome);
}

// GS real, para os alvos que o painel de fato oferece.
const ctxGS = {
  window: { LANG_STRINGS: {} },
  WebSocket: class { constructor() { this.readyState = 1; } send() {} close() {} },
  localStorage: { getItem: () => null, setItem: () => {}, removeItem: () => {} },
  location: { search: '', protocol: 'http:', host: 'x' },
  setTimeout: () => 0, clearTimeout: () => {},
};
vm.createContext(ctxGS);
vm.runInContext(fs.readFileSync(path.join(root, 'src/gameState.js'), 'utf8') + '\nthis.api=GS;', ctxGS);
const GS = ctxGS.api;

// ── Funções do game.js (filtro e motivo) ─────────────────────────────────────
const fabricaPainel = new Function('t',
  extrair(game, '_filtrarAlvoFixoVeneno') + '\n' + extrair(game, '_motivoSemAlvoVeneno') +
  '\nreturn {_filtrarAlvoFixoVeneno,_motivoSemAlvoVeneno};');
const painel = fabricaPainel(k => k);

const frasco = { id: 'veneno_aranha', effect: 'coat_poison', veneno_id: 'veneno_aranha' };
const flechas = (n, extra = {}) => ({ id: 'flechas', effect: 'ammo', ammo_type: 'flechas', ammo_count: n, ...extra });
const espada = { id: 'shortsword', die: '1d6' };
const adaga = { id: 'dagger', die: '1d4' };
const arco = { id: 'arco_curto', die: '1d6' };
const alvos = (me) => GS.venenoAlvos(me, { metodo: 'frasco', venenoId: 'veneno_aranha', maxPorFrasco: 10 });

// 1. Soltar sobre a arma corpo a corpo: só aquela arma.
let me = { gear: { weapon: espada, off_hand: adaga }, bag: [] };
let r = painel._filtrarAlvoFixoVeneno(alvos(me), { tipo: 'arma', slot: 'off_hand' });
check('arma: só a mão escolhida', r.armas.map(a => a.slot).join() === 'off_hand' && r.municoes.length === 0);

// 2. Soltar sobre a pilha da bolsa: só aquela pilha.
me = { gear: { weapon: arco }, bag: [flechas(8), { id: 'x' }, flechas(5, { ammo_type: 'flechas' })] };
r = painel._filtrarAlvoFixoVeneno(alvos(me), { tipo: 'municao', source: 'bag', index: 2 });
check('bolsa: só a pilha do índice escolhido', r.municoes.length === 1 && r.municoes[0].index === 2 && r.municoes[0].item.ammo_count === 5);

// 3. Soltar sobre a munição equipada na mão do escudo.
me = { gear: { weapon: arco, off_hand: flechas(6) }, bag: [flechas(8)] };
r = painel._filtrarAlvoFixoVeneno(alvos(me), { tipo: 'municao', source: 'off_hand', index: 0 });
check('mão do escudo: só a pilha equipada', r.municoes.length === 1 && r.municoes[0].source === 'off_hand');

// 4. Com arco e besta equipados, a mesma pilha não vira duas opções.
me = { gear: { weapon: arco, off_hand: { id: 'hand_crossbow', die: '1d4' } }, bag: [flechas(8)] };
r = painel._filtrarAlvoFixoVeneno(alvos(me), { tipo: 'municao', source: 'bag', index: 0 });
check('pilha repetida para duas mãos vira uma opção só', r.municoes.length <= 1);

// 5. Sem arco: a pilha não tem alvo e a mensagem explica por quê.
me = { gear: { weapon: espada }, bag: [flechas(8)] };
r = painel._filtrarAlvoFixoVeneno(alvos(me), { tipo: 'municao', source: 'bag', index: 0 });
check('sem arco compatível: nenhum alvo', r.municoes.length === 0 && r.armas.length === 0);
check('sem arco: motivo é "sem arma compatível"',
  painel._motivoSemAlvoVeneno(me, { tipo: 'municao', source: 'bag', index: 0 }) === 'ui.veneno.arrastar_sem_arma');

// 6. Pilha que já tem veneno: motivo "já envenenado".
me = { gear: { weapon: arco }, bag: [flechas(8, { poison_ids: ['veneno_aranha'] })] };
check('pilha já envenenada: nenhum alvo',
  painel._filtrarAlvoFixoVeneno(alvos(me), { tipo: 'municao', source: 'bag', index: 0 }).municoes.length === 0);
check('pilha já envenenada: motivo correto',
  painel._motivoSemAlvoVeneno(me, { tipo: 'municao', source: 'bag', index: 0 }) === 'ui.veneno.arrastar_ja_envenenada');

// 7. Arco na mão principal: o veneno vai nas flechas.
me = { gear: { weapon: arco }, bag: [flechas(8)] };
check('arco como alvo: nenhum cartão e dica das flechas',
  painel._filtrarAlvoFixoVeneno(alvos(me), { tipo: 'arma', slot: 'weapon' }).armas.length === 0
  && painel._motivoSemAlvoVeneno(me, { tipo: 'arma', slot: 'weapon' }) === 'ui.veneno.arrastar_arma_distancia');

// 8. Sem alvo fixo, nada é filtrado (fluxo antigo).
me = { gear: { weapon: espada, off_hand: adaga }, bag: [] };
const todos = alvos(me);
check('sem alvo fixo devolve tudo', painel._filtrarAlvoFixoVeneno(todos, null) === todos);

// ── Funções do inventoryModal (reconhecer o frasco e o alvo do slot) ────────
function modalCom(estado) {
  const fonte = ['_beltEntry', '_frascoVenenoArrastado', '_alvoVenenoDoSlot'].map(n => extrair(modal, n)).join('\n');
  const fab = new Function('estado', 'BELT_CAPACITIES', 'BELT_STACK_CAPACITIES',
    'let _selected = estado.selected, _readOnly = estado.readOnly, _storageCtx = estado.storage;\n' +
    fonte + '\nreturn {_frascoVenenoArrastado,_alvoVenenoDoSlot};');
  return fab(estado, { cinto_utilidades: 4 }, { cinto_utilidades: 4 });
}
const jogador = {
  bag: [frasco, flechas(8), { id: 'potion', effect: 'heal' }],
  gear: {
    weapon: espada, off_hand: flechas(10),
    item1: { id: 'cinto_utilidades', utility_belt_token: 'T1', utility_belt_slots: [{ item: frasco, quantity: 2 }, { item: { id: 'potion', effect: 'heal' }, quantity: 1 }] },
  },
};
let m = modalCom({ selected: { kind: 'bag', index: 0 } });
let f = m._frascoVenenoArrastado(jogador);
check('frasco da bolsa é reconhecido', f && f.itemId === 'veneno_aranha' && f.sourceInfo === undefined);
check('poção da bolsa não é frasco de veneno', modalCom({ selected: { kind: 'bag', index: 2 } })._frascoVenenoArrastado(jogador) === null);
check('munição da bolsa não é frasco de veneno', modalCom({ selected: { kind: 'bag', index: 1 } })._frascoVenenoArrastado(jogador) === null);
f = modalCom({ selected: { kind: 'belt', gearSlot: 'item1', pocketIndex: 0 } })._frascoVenenoArrastado(jogador);
check('frasco do cinto leva a origem e o token', f && f.sourceInfo && f.sourceInfo.source === 'utility_belt' && f.sourceInfo.beltToken === 'T1' && f.sourceInfo.pocketIndex === 0);
check('poção do cinto não é frasco', modalCom({ selected: { kind: 'belt', gearSlot: 'item1', pocketIndex: 1 } })._frascoVenenoArrastado(jogador) === null);
check('ficha só de leitura não reconhece', modalCom({ selected: { kind: 'bag', index: 0 }, readOnly: true })._frascoVenenoArrastado(jogador) === null);
check('baú aberto não reconhece', modalCom({ selected: { kind: 'bag', index: 0 }, storage: {} })._frascoVenenoArrastado(jogador) === null);
check('nada selecionado não reconhece', modalCom({ selected: null })._frascoVenenoArrastado(jogador) === null);
m = modalCom({ selected: null });
check('slot da arma → alvo arma', JSON.stringify(m._alvoVenenoDoSlot(jogador, 'weapon')) === JSON.stringify({ tipo: 'arma', slot: 'weapon' }));
check('mão do escudo com flechas → alvo munição', JSON.stringify(m._alvoVenenoDoSlot(jogador, 'off_hand')) === JSON.stringify({ tipo: 'municao', source: 'off_hand', index: 0 }));
check('slot vazio → sem alvo', m._alvoVenenoDoSlot({ gear: {} }, 'weapon') === null);
check('escudo na mão secundária → sem alvo', m._alvoVenenoDoSlot({ gear: { off_hand: { id: 'escudo_p', kind: 'shield' } } }, 'off_hand') === null);

// ── Fiação: os pontos de soltar chamam o painel com alvo fixo ───────────────
check('soltar sobre pilha da bolsa abre a confirmação',
  /frascoNaBolsa && alvo && alvo\.effect === 'ammo'[\s\S]{0,200}_soltarVenenoSobre\(player, frascoNaBolsa, \{tipo:'municao', source:'bag', index:toIndex\}\)/.test(modal));
check('soltar sobre arma/munição equipada abre a confirmação (antes do retorno antecipado)',
  /frascoNoSlot[\s\S]{0,500}if\(!sel \|\| sel\.kind === 'gear' \|\| sel\.kind === 'belt'/.test(modal));
check('soltar na aljava avisa em vez de falhar', /_frascoVenenoArrastado\(_currentPlayer\(\)\)\)\{\s*if\(typeof toast/.test(modal));
check('painel aceita alvoFixo e troca o título', /alvoFixo=null\}=\{\}\)\{/.test(game) && /ui\.veneno\.titulo_confirmar/.test(game));
check('painel único segue sendo o mesmo (envenenar_municao e use_item)', /type:'envenenar_municao'/.test(game) && /type:'use_item',item_id:escolhidos\[0\]/.test(game));

console.log(`\n=== ${pass} passaram, ${fail} falharam ===`);
process.exit(fail ? 1 : 0);
