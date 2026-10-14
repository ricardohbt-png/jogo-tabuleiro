// Regressão: raio 0 deve manter a prévia de área no quadrado escolhido.
const assert = require('assert');
const fs = require('fs');
const vm = require('vm');

const source = fs.readFileSync('game.js', 'utf8');
const match = source.match(/function _recomputarAreaThrow\(hx, hy\) \{[\s\S]*?\n\}/);
assert(match, 'função de prévia de área do arremesso encontrada');

const sandbox = {
  window: {
    _modoThrowItem: { area: 0 },
    _spellHL: { area: new Set(), double: new Set() },
  },
  _addCheb(cx, cy, radius, out) {
    for (let y = cy - radius; y <= cy + radius; y++)
      for (let x = cx - radius; x <= cx + radius; x++) out.add(`${x},${y}`);
  },
  _aplicarSpellHL() {},
};
vm.runInNewContext(`${match[0]}\n_recomputarAreaThrow(7, 4);`, sandbox);
assert.deepStrictEqual(Array.from(sandbox.window._spellHL.area), ['7,4']);
console.log('1 verificação passou');
