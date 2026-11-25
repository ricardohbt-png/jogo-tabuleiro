// Percepção na ficha de status: o bônus do equipamento (Óculos do Terceiro Olho) precisa aparecer.
// Roda da raiz: node tools/test_percepcao_status.js
const fs = require('fs'), path = require('path'), assert = require('assert');
const raiz = path.join(__dirname, '..');
const game = fs.readFileSync(path.join(raiz, 'game.js'), 'utf8').split('\r\n').join('\n');
const lang = fs.readFileSync(path.join(raiz, 'src/lang/interface.js'), 'utf8');
let n = 0; const ok = (c, m) => { assert.ok(c, m); n++; };

const src = game.match(/function _percepcaoDetalhesStatus\(p\)\{[\s\S]*?\n\}\n/)[0];
const det = new Function(src + '; return _percepcaoDetalhesStatus;')();

let d = det({percepcao: 17, vision_radius: 5, gear: {head: {id: 'oculos_terceiro_olho', effect: 'perception_bonus', value: 5}}});
ok(d.valor === 17 && d.equip === 5 && d.base === 12 && d.pen === 0 && d.raio === 5, 'óculos: 12 base + 5 equipamento = 17, veio ' + JSON.stringify(d));
d = det({percepcao: 12, vision_radius: 5, gear: {head: null, weapon: {id: 'x'}}});
ok(d.equip === 0 && d.base === 12, 'sem item o bônus é 0');
d = det({percepcao: 14, vision_radius: 5, penalidades: {percepcao: -2},
  gear: {head: {id: 'y', effect: 'vision', bonuses: [{effect: 'perception_bonus', value: 4}]}}});
ok(d.equip === 4 && d.pen === -2 && d.base === 12, 'bônus na lista bonuses e penalidade, veio ' + JSON.stringify(d));
d = det({vision_radius: 6, gear: {}});
ok(d.valor === 13 && d.equip === 0, 'sem valor do servidor: 10 + metade da visão, veio ' + JSON.stringify(d));

ok(/<h3>\$\{t\('ui\.status\.exploracao'\)\}<\/h3>/.test(game), 'seção Exploração ausente no painel de status');
ok(/_percepcaoDetalhesStatus\(p\)/.test(game), 'painel não usa o cálculo');
for (const k of ['exploracao', 'detalhe_percepcao']) {
  const m = lang.match(new RegExp('"ui\.status\.' + k + '":[^\n]*'));
  ok(m && /"en":/.test(m[0]) && /"pt":/.test(m[0]), 'chave sem pt/en: ' + k);
}
console.log('test_percepcao_status: ' + n + ' verificações OK');
