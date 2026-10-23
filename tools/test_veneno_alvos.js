'use strict';
// GS.venenoAlvos: quais armas e pilhas de munição o painel único "Envenenar" oferece.
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const root = path.join(__dirname, '..');
const context = {
  window: { LANG_STRINGS: {} },
  WebSocket: class { constructor(){ this.readyState = 1; } send(){} close(){} },
  localStorage: { getItem: () => null, setItem: () => {}, removeItem: () => {} },
  location: { search: '', protocol: 'http:', host: 'x' },
  setTimeout: () => 0, clearTimeout: () => {},
};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(root, 'src/gameState.js'), 'utf8') + '\nthis.api=GS;', context);
const GS = context.api;

let falhas = 0;
function check(label, actual, expected){
  const ok = JSON.stringify(actual) === JSON.stringify(expected);
  console.log(`${ok ? 'OK ' : 'FALHOU'} ${label}${ok ? '' : ` -> ${JSON.stringify(actual)} (esperado ${JSON.stringify(expected)})`}`);
  if(!ok) falhas++;
}
const flechas = (n, extra = {}) => ({ id: 'flechas', effect: 'ammo', ammo_type: 'flechas', ammo_count: n, ...extra });
const espada = { id: 'shortsword', die: 'd6' };
const adaga = { id: 'dagger', die: 'd4' };
const arco = { id: 'arco_curto', die: 'd6' };
const besta = { id: 'hand_crossbow', die: 'd6' };
const alvos = (me, o) => GS.venenoAlvos(me, { metodo: 'frasco', venenoId: 'v1', maxPorFrasco: 10, ...o });

// 1. Duas armas corpo a corpo: as duas aparecem, nenhuma munição.
let r = alvos({ gear: { weapon: espada, off_hand: adaga }, bag: [] });
check('corpo a corpo: 2 armas', r.armas.map(a => a.slot), ['weapon', 'off_hand']);
check('corpo a corpo: sem munição', r.municoes.length, 0);

// 2. Arco na mão principal: só munição (arco não recebe veneno direto), flechas da mão e da bolsa agrupadas.
r = alvos({ gear: { weapon: arco, off_hand: flechas(6) }, bag: [flechas(8), { id: 'x' }] });
check('arco: sem arma direta', r.armas.length, 0);
check('arco: flechas iguais viram UM cartão', r.municoes.length, 1);
check('arco: total e quantidade', [r.municoes[0].total, r.municoes[0].qtd, r.municoes[0].sobra, r.municoes[0].parcial], [14, 10, 4, false]);

// 3. Com pouca munição o cartão avisa que a dose é parcial.
r = alvos({ gear: { weapon: arco }, bag: [flechas(4)] });
check('pouca munição: parcial', [r.municoes[0].qtd, r.municoes[0].parcial], [4, true]);

// 4. Munição já envenenada e munição de outro tipo ficam de fora.
r = alvos({ gear: { weapon: arco }, bag: [flechas(5, { poison_ids: ['v9'] }), { id: 'v', effect: 'ammo', ammo_type: 'virotes', ammo_count: 5 }] });
check('só munição limpa e compatível', r.municoes.length, 0);

// 5. Munições com propriedades diferentes não se misturam.
r = alvos({ gear: { weapon: arco }, bag: [flechas(5), flechas(5, { damage_bonus: 1 })] });
check('assinaturas diferentes: 2 cartões', r.municoes.length, 2);

// 6. Cargas antigas na arma de tiro bloqueiam o preparo de munição.
r = alvos({ gear: { weapon: { ...arco, poison_slots: ['v1'] } }, bag: [flechas(5)] });
check('cargas legadas bloqueiam', r.municoes[0].legado, true);

// 7. Limite de venenos distintos na arma (1 sem a especialização, 2 com).
const comOutro = { ...espada, poison_slots: ['v2', 'v2'] };
r = alvos({ gear: { weapon: comOutro } });
check('outro veneno, limite 1: não cabe', r.armas[0].cabe, false);
r = alvos({ gear: { weapon: comOutro } }, { doisVenenos: true });
check('outro veneno, limite 2: cabe', r.armas[0].cabe, true);
r = alvos({ gear: { weapon: { ...espada, poison_slots: ['v1'] } } });
check('mesmo veneno sempre cabe (renova)', r.armas[0].cabe, true);

// 8. Besta de mão na mão secundária: direta só pelo Veneno Rápido; pelo frasco só munição.
const gear = { weapon: espada, off_hand: besta };
r = alvos({ gear, bag: [{ id: 'v', effect: 'ammo', ammo_type: 'virotes', ammo_count: 3 }] });
check('frasco: besta de mão só pela munição', [r.armas.map(a => a.slot), r.municoes.length, r.municoes[0].weaponSlot], [['weapon'], 1, 'off_hand']);
r = alvos({ gear, bag: [] }, { metodo: 'veneno_rapido' });
check('veneno rápido: besta de mão também direto', r.armas.map(a => a.slot), ['weapon', 'off_hand']);

// 9. Munição que está na mão secundária não vale quando a arma de tiro É a mão secundária.
r = alvos({ gear: { weapon: espada, off_hand: besta }, bag: [] });
check('sem munição: nenhum cartão', r.municoes.length, 0);

// 10. Sem arma equipada: nada a oferecer.
r = alvos({ gear: {}, bag: [flechas(5)] });
check('sem arma: sem alvos', [r.armas.length, r.municoes.length], [0, 0]);

// 11. Fiação do painel no game.js: ele precisa se desenhar ao abrir, e o HUD do Ladino
// não pode chamar `desenhar()` (um trecho solto já quebrou o botão de Detectar Armadilhas).
const fonte = fs.readFileSync(path.join(root, 'game.js'), 'utf8').split('\r\n').join('\n');
const ini = fonte.indexOf('function abrirPainelEnvenenar(');
const corpo = fonte.slice(ini, fonte.indexOf('\n}\n', ini) + 3);
check('painel declara desenhar()', corpo.includes('const desenhar=()=>'), true);
check('painel chama desenhar() ao abrir', corpo.endsWith('\n  desenhar();\n}\n'), true);
const iniLadino = fonte.indexOf('function _rogueSkillBtn(');
const ladino = fonte.slice(iniLadino, fonte.indexOf('\n}\n', iniLadino));
check('_rogueSkillBtn não chama desenhar()', /(^|[^\w.])desenhar\(/.test(ladino), false);

if(falhas){ console.log(`\n${falhas} falha(s)`); process.exit(1); }
console.log('\ntudo ok');
