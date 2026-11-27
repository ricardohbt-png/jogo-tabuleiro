// Regressão: raio 0 deve manter a prévia de área no quadrado escolhido.
// Executa a _recomputarAreaThrow REAL; as outras funções que ela chama viram espiões
// (js_teste_util), então acrescentar uma chamada nova a ela não quebra este teste.
const assert = require('assert');
const U = require('./js_teste_util');

const GAME = U.ler('game.js');
const { api, chamadas, ctx } = U.executar(GAME, ['_recomputarAreaThrow'], {
  window: { _modoThrowItem: { area: 0 }, _spellHL: { area: new Set(), double: new Set() } },
  _addCheb(cx, cy, radius, out) {
    for (let y = cy - radius; y <= cy + radius; y++)
      for (let x = cx - radius; x <= cx + radius; x++) out.add(`${x},${y}`);
  },
});
api._recomputarAreaThrow(7, 4);
assert.deepStrictEqual(Array.from(ctx.window._spellHL.area), ['7,4']);
assert.ok(chamadas.some(c => c.nome === '_aplicarSpellHL'), 'a prévia é desenhada');
console.log('2 verificações passaram');
