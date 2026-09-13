'use strict';
// Exercita o fluxo real de game_state pelo WebSocket, sem depender do DOM.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

class SocketTeste {
  constructor() { this.readyState = 1; SocketTeste.current = this; }
  send() {}
  close() { this.readyState = 3; }
}

const context = vm.createContext({
  WebSocket: SocketTeste,
  setTimeout, clearTimeout, console,
  localStorage: { getItem: () => null, setItem() {}, removeItem() {} },
});
const source = fs.readFileSync(path.join(__dirname, '..', 'src', 'gameState.js'), 'utf8');
vm.runInContext(source, context);
const GS = vm.runInContext('GS', context);
GS.connect('ws://teste', 'Lewis', 'login');

const avisos = [];
GS.on('darknessEntered', msg => avisos.push(msg));
const receber = (ativo, rodadas = 0) => SocketTeste.current.onmessage({
  data: JSON.stringify({
    type: 'game_state', phase: 'playing', current_turn: 'cleric-1',
    players: [{ id: 'cleric-1', name: 'Lewis', class_id: 'cleric', alive: true,
      escuridao_desvantagem: ativo, escuridao_rodadas: rodadas }],
  }),
});

receber(false);
assert.equal(avisos.length, 0, 'estado normal não abre aviso');
receber(true, 2);
assert.equal(avisos.length, 1, 'entrada na escuridão abre aviso');
assert.equal(avisos[0].rounds, 2, 'aviso recebe duração autoritativa');
receber(true, 1);
assert.equal(avisos.length, 1, 'atualização e tick não duplicam aviso');
receber(false);
receber(true, 2);
assert.equal(avisos.length, 2, 'nova entrada na escuridão abre outro aviso');
GS.connect('ws://teste', 'Lewis', 'login');
receber(true, 3);
assert.equal(avisos.length, 3, 'primeiro estado após reiniciar em escuridão abre aviso');

console.log('Escuridão: transições de status e duração validadas.');
