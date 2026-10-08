// O aliado de treino usa a miniatura do Soldado em 2D e 3D e nunca fica sem aparência.
const fs = require('fs'), vm = require('vm'), assert = require('assert');
const game = fs.readFileSync('game.js', 'utf8');
const fn = game.match(/^function _metamorfoseVisualName[\s\S]*?^}/m)?.[0];
assert.ok(fn);
const ctx = {}; vm.createContext(ctx);
vm.runInContext(`${fn}; this.f = _metamorfoseVisualName;`, ctx);
assert.strictEqual(ctx.f({ training_ally: true, pawn_override: 'soldado' }), 'soldado');
assert.strictEqual(ctx.f({ training_ally: true }), 'soldado', 'sem campo do servidor ainda é soldado');
assert.strictEqual(ctx.f({ class_id: 'warrior' }), null, 'heroi comum nao muda');
assert.strictEqual(ctx.f({ metamorfose_ativa: true, metamorfose_forma_type: 'lobo', training_ally: true }), 'lobo');
// O laço de desenho não pode descartar o aliado (connected=false) em 2D nem em 3D.
for (const marca of ['// 2D-PLAYERS', '// 3D-PLAYERS']) {
  const i = game.indexOf(marca); assert.ok(i > 0, marca);
  const trecho = game.slice(i, i + 700);
  assert.ok(/connected === false && !p\.training_ally/.test(trecho), marca + ' deve poupar training_ally');
}
assert.ok(/MONSTER_GLB|soldado:\s+'assets\/models3d\/monstros\/soldado.glb'/.test(game));
console.log('aprendiz cliente: ok');
