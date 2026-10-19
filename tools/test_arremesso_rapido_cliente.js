'use strict';
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
GS.connect('ws://x', 'Aventureiro', 'create');

function check(label, actual, expected){
  if(actual !== expected) throw new Error(`${label}: expected ${expected}, got ${actual}`);
  console.log(`OK ${label}`);
}

const player = {
  id: 'h', alive: true, action_done: true, bonus_action_used: false,
  guild_owned: { especializacoes: ['arremesso_rapido'], tecnicas: [] },
  arremesso_rapido_rodada: 4, arremesso_rapido_usados: 1,
};
GS.injectPreviewState({type:'game_state', phase:'playing', round:4,
  master_pid:'h', players:[player], monsters:[]});
check('permite a segunda mira com talento, primeira tentativa e bônus livre', GS.canThrowItem(player), true);
player.bonus_action_used = true;
check('bloqueia se a ação bônus já foi gasta', GS.canThrowItem(player), false);
player.bonus_action_used = false;
player.arremesso_rapido_usados = 0;
check('não transforma a primeira mira após outra ação em ação bônus', GS.canThrowItem(player), false);
player.arremesso_rapido_usados = 1;
player.guild_owned.especializacoes = [];
check('bloqueia segunda mira sem talento', GS.canThrowItem(player), false);
player.action_done = false;
check('continua permitindo primeira mira na ação principal', GS.canThrowItem(player), true);
player.action_done = true;
player.guild_owned.especializacoes = ['arremesso_rapido'];
player.arremesso_rapido_rodada = 3;
check('ignora contador antigo de outra rodada', GS.canThrowItem(player), false);
