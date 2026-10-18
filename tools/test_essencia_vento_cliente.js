// Alcance da Essência do Vento Favorável — roda: node tools/test_essencia_vento_cliente.js
const fs = require('fs');
const path = require('path');
const raiz = path.join(__dirname, '..');
const enviados = [];
let sock = null;
global.WebSocket = class {
  constructor() { this.readyState = 1; sock = this; }
  send(s) { enviados.push(JSON.parse(s)); }
  close() {}
};
global.window = {};
global.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
global.location = { search: '', protocol: 'http:', host: 'x' };
global.setTimeout = () => 0; global.clearTimeout = () => {};
const GS = eval(fs.readFileSync(path.join(raiz, 'src', 'gameState.js'), 'utf8') + '; GS');
GS.connect('ws://x', 'Thorin', 'create');
const chegar = msg => sock.onmessage({ data: JSON.stringify(msg) });
const check = (nome, ok) => {
  if (!ok) { console.error('❌ ' + nome); process.exitCode = 1; }
  else console.log('✅ ' + nome);
};

const player = { id: 'p1', alive: true, pos: [0, 0], weapon: { id: 'arco_curto', range: 6 } };
chegar({ type: 'game_state', players: [player], monsters: [], tiles: [], rooms: [], explored: [] });
const me = GS.gameState.players[0];
check('arco respeita o alcance normal sem a essência', !GS.weaponCanReachTile(me, 8, 0));
me.essencia_vento_rodadas = 3;
check('essência aumenta o alcance reto do arco em duas casas', GS.weaponCanReachTile(me, 8, 0));
check('a prévia mostra o alcance efetivo de oito casas', GS.weaponReachInfo(me, 8, 0).effectiveRange === 8);
check('diagonal do arco continua usando metade do alcance ampliado', GS.weaponCanReachTile(me, 4, 4));
check('besta continua exigindo linha ortogonal mesmo com a essência', (() => {
  me.weapon = { id: 'besta', range: 6 };
  return !GS.weaponCanReachTile(me, 6, 2) && GS.weaponCanReachTile(me, 8, 0);
})());
check('arma de haste com alcance não recebe bônus de projétil', (() => {
  me.weapon = { id: 'alabarda', range: 4 };
  return !GS.weaponCanReachTile(me, 6, 0);
})());

const jogo = fs.readFileSync(path.join(raiz, 'game.js'), 'utf8');
check('mira de itens arremessáveis envia o alcance ampliado ao estado de mira',
  /const alcance = \(catDef\.alcance \|\| item\.alcance \|\| 4\) \+ _bonusAlcanceArremessoCli\(me\)/.test(jogo));
check('mira de armas arremessadas amplia validação e casas destacadas',
  /item\.throw_range \+ _bonusAlcanceArremessoCli\(me\)/.test(jogo)
  && /const alcance = tr \+ _bonusAlcanceArremessoCli\(me\)/.test(jogo));
console.log(`\n${process.exitCode ? 'Falha' : 'Todas as verificações passaram'}`);
