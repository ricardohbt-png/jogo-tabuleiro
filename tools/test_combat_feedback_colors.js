const fs = require('fs');
const vm = require('vm');
const assert = require('assert');

const game = fs.readFileSync('game.js', 'utf8');
const start = game.indexOf('function _combatFeedbackColor(');
assert.notStrictEqual(start, -1, 'helper de cor do dano deve existir');
const fn = game.slice(start).match(/^function _combatFeedbackColor[\s\S]*?^}/m)?.[0];
assert.ok(fn, 'helper de cor do dano deve fechar');
const displayFn = game.slice(game.indexOf('function _combatFeedbackDisplayText('))
  .match(/^function _combatFeedbackDisplayText[\s\S]*?^}/m)?.[0];
assert.ok(displayFn, 'helper do texto do dano deve fechar');

const colors = {
  physical: '#f4eee2', fire: '#ff8a32',
};
const context = {
  VC: { feedback: { combat: {
    damageColor: '#ff6262', heroDamageColor: '#ff8d8d',
    resistedColor: '#62c8ff', vulnerableColor: '#ff4f64',
    damageTypes: { physical: { color: colors.physical }, fire: { color: colors.fire } },
  } } },
  _highContrast: false,
  _combatDamageTypeInfo: type => ({ key: type, color: colors[type] || '#ffffff', icon: type === 'fire' ? '🔥' : '⚔' }),
  t: key => ({
    'ui.menu.damage.status.resisted': 'RESISTED',
    'ui.menu.damage.status.vulnerable': 'VULNERABLE',
  }[key] || key),
};
vm.createContext(context);
vm.runInContext(`${fn}; ${displayFn}; this.color = _combatFeedbackColor; this.display = _combatFeedbackDisplayText;`, context);

assert.strictEqual(context.color('damage', 'physical'), '#f4eee2',
  'dano físico normal mantém a cor atual');
assert.strictEqual(context.color('damage', 'fire'), '#ff8a32',
  'dano elemental normal mantém a cor do tipo');
assert.strictEqual(context.color('damage', 'fire', 'resisted'), '#62c8ff',
  'dano resistido usa azul mesmo quando é elemental');
assert.strictEqual(context.color('damage', 'physical', 'vulnerable'), '#ff4f64',
  'dano vulnerável usa vermelho sem depender do tipo');
assert.strictEqual(context.display({kind:'damage', text:'8', damageType:'fire', status:'DOBRADO', reaction:'vulnerable'}),
  '🔥 8 VULNERABLE', 'o complemento identifica vulnerabilidade sem dizer DOBRADO');
assert.strictEqual(context.display({kind:'damage', text:'4', damageType:'fire', status:'METADE', reaction:'resisted'}),
  '🔥 4 RESISTED', 'o complemento identifica resistência sem dizer METADE');

const help = fs.readFileSync('game.js', 'utf8');
const translations = fs.readFileSync('src/lang/strings.js', 'utf8');
assert.match(help, /ui\.menu\.dano_cores_titulo/,
  'as configurações de jogo devem incluir a legenda de cores de dano');
assert.match(help, /ui\.menu\.dano_cores/,
  'as configurações devem abrir a tabela explicativa');
assert.match(translations, /"ui\.menu\.dano_cores"/,
  'a tabela de cores deve ter tradução');
assert.match(translations, /VULNERÁVEL/,
  'a legenda deve explicar vulnerabilidade');
assert.match(translations, /RESISTIDO/,
  'a legenda deve explicar resistência');

console.log('combat feedback colors: ok');
