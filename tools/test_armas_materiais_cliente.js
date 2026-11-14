'use strict';
// Variantes de material (Freixo Negro, Cedro Rubro, Cerne de Titã, Prata...) seguem as regras da
// arma-base no cliente: veneno só na munição de arcos/bestas, bestas só ortogonais, arcos com metade do
// alcance na diagonal, Lança Curta nas 8 casas e pareamento de Disparo Duplo (besta de mão).
// Roda da raiz:  node tools/test_armas_materiais_cliente.js
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const root = path.join(__dirname, '..');
let sock = null;
const context = {
  window: { LANG_STRINGS: {} },
  WebSocket: class { constructor(){ this.readyState = 1; sock = this; } send(){} close(){} },
  localStorage: { getItem: () => null, setItem: () => {}, removeItem: () => {} },
  location: { search: '', protocol: 'http:', host: 'x' },
  setTimeout: () => 0, clearTimeout: () => {},
};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(root, 'src/gameState.js'), 'utf8') + '\nthis.api=GS;', context);
const GS = context.api;
GS.connect('ws://x', 'Ana', 'create');

let falhas = 0;
function check(label, ok){
  console.log(`${ok ? 'OK ' : 'FALHOU'} ${label}`);
  if(!ok) falhas++;
}

const SUFIXOS = ['_freixo_negro', '_cedro_rubro', '_cerne_tita'];
const BESTAS = ['besta', 'besta_pesada', 'besta_repetidora_patrulha', 'besta_repetidora_guerra', 'hand_crossbow', 'besta_duelista'];
const ARCOS = ['arco_curto', 'longbow', 'arco_composto_curto', 'arco_composto_longo', 'arco_bruto_combatente'];
const ALCANCE = { besta: 8, besta_pesada: 12, besta_repetidora_patrulha: 6, besta_repetidora_guerra: 8,
  hand_crossbow: 4, besta_duelista: 4, arco_curto: 6, longbow: 10, arco_composto_curto: 6,
  arco_composto_longo: 10, arco_bruto_combatente: 10 };

console.log('[1] armaBaseId');
check('Freixo Negro volta para a base', GS.armaBaseId('besta_pesada_freixo_negro') === 'besta_pesada');
check('Prata volta para a base', GS.armaBaseId('lanca_curta_prata') === 'lanca_curta');
check('machadinha prata tem id especial', GS.armaBaseId('machadinha_ana_prata') === 'machadinha_arremesso_ana');
check('id sem material volta igual', GS.armaBaseId('hand_crossbow') === 'hand_crossbow');
check('vazio vira texto vazio', GS.armaBaseId(null) === '');

console.log('[2] veneno só na munição de arcos e bestas (base e variantes)');
const flechas = n => ({ id: 'flechas', effect: 'ammo', ammo_type: 'flechas', ammo_count: n });
const virotes = n => ({ id: 'virotes', effect: 'ammo', ammo_type: 'virotes', ammo_count: n });
for (const base of [...ARCOS, ...BESTAS]) {
  for (const id of [base, ...SUFIXOS.map(s => base + s)]) {
    const municao = ARCOS.includes(base) ? flechas(6) : virotes(6);
    const r = GS.venenoAlvos({ gear: { weapon: { id, die: 'd6' }, off_hand: municao }, bag: [] },
      { metodo: 'frasco', venenoId: 'v1', maxPorFrasco: 10 });
    check(`${id}: arma não recebe veneno direto`, r.armas.length === 0);
    check(`${id}: a munição é oferecida`, r.municoes.length >= 1);
  }
}
const corpo = GS.venenoAlvos({ gear: { weapon: { id: 'shortsword_aco_damasco', die: 'd6' } }, bag: [] },
  { metodo: 'frasco', venenoId: 'v1', maxPorFrasco: 10 });
check('arma corpo a corpo de material recebe veneno direto', corpo.armas.length === 1);

console.log('[3] Veneno Rápido na besta de mão secundária (base e variantes)');
for (const base of ['hand_crossbow', 'besta_duelista']) {
  for (const id of [base, ...SUFIXOS.map(s => base + s)]) {
    const r = GS.venenoAlvos({ gear: { weapon: { id: 'hand_crossbow', die: 'd4' }, off_hand: { id, die: 'd4' } }, bag: [] },
      { metodo: 'veneno_rapido', venenoId: 'v1', maxPorFrasco: 10 });
    check(`${id} na mão secundária aceita Veneno Rápido`, r.armas.some(a => a.slot === 'off_hand'));
  }
}

console.log('[4] alcance: bestas ortogonais, arcos com metade na diagonal');
function podeAlcancar(id, dx, dy, extra = {}){
  const weapon = { id, range: ALCANCE[id], ...extra };
  const me = { pos: [10, 10], weapon, gear: { weapon } };
  context.__me = me; context.__tx = 10 + dx; context.__ty = 10 + dy;
  return vm.runInContext('GS.weaponCanReachTile(__me, __tx, __ty, 0)', context);
}
for (const base of [...BESTAS, ...ARCOS]) {
  for (const id of [base, ...SUFIXOS.map(s => base + s)]) {
    const extra = base === 'arco_composto_curto' || base === 'arco_composto_longo' || base === 'arco_bruto_combatente'
      ? { range_all_directions: true } : {};
    ALCANCE[id] = ALCANCE[base];
    const diag = Math.min(3, ALCANCE[base]);
    const igual = [[diag, diag], [ALCANCE[base], 0], [0, ALCANCE[base]], [ALCANCE[base] + 1, 0],
      [Math.ceil(ALCANCE[base] / 2), Math.ceil(ALCANCE[base] / 2)], [ALCANCE[base], ALCANCE[base]]]
      .every(([dx, dy]) => podeAlcancar(id, dx, dy, extra) === podeAlcancar(base, dx, dy, extra));
    check(`${id}: alcance igual ao da base`, igual);
  }
}
check('besta variante não atira na diagonal', podeAlcancar('besta_pesada_freixo_negro', 3, 3) === false);
check('arco variante: diagonal só até a metade',
  podeAlcancar('arco_curto_cerne_tita', 3, 3) === true && podeAlcancar('arco_curto_cerne_tita', 4, 4) === false);

console.log('[5] Lança Curta nas 8 casas');
const lanca = { id: 'lanca_curta_aco_damasco' };
const meLanca = { pos: [10, 10], weapon: lanca, gear: { weapon: lanca } };
context.__me = meLanca; context.__tx = 11; context.__ty = 11;
check('variante da lança curta alcança a diagonal', vm.runInContext('GS.weaponCanReachTile(__me, __tx, __ty, 0)', context) === true);

console.log('[6] Disparo Duplo: besta de mão e variantes pareiam entre si');
sock.onmessage({ data: JSON.stringify({ type: 'game_start', pid: 'h' }) });
sock.onmessage({ data: JSON.stringify({ type: 'game_state', players: [{ id: 'h', class_id: 'rogue', pos: [0, 0], alive: true,
  guild_owned: { especializacoes: ['disparo_duplo'] }, gear: {} }], monsters: [], decorations: [], tiles: [[1]], explored: ['0,0'], rooms: [], materiais: {} }) });
const gearBase = { weapon: { id: 'hand_crossbow_freixo_negro', die: 'd4' } };
check('variante pareia com variante na mão secundária',
  GS.isOffhandWeapon({ id: 'besta_duelista_cedro_rubro', die: 'd6' }, gearBase) === true);
check('besta pesada não é arma de mão secundária',
  !GS.isOffhandWeapon({ id: 'besta_pesada_freixo_negro', die: 'd10' }, gearBase));

console.log(falhas ? `\n${falhas} FALHAS` : '\nTodos os testes passaram');
process.exit(falhas ? 1 : 0);
