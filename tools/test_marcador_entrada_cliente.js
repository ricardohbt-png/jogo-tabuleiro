// Cliente — marcador de entrada "poste" no lugar da escada (2D, 3D, dicas e textos).
// Roda da raiz: node tools/test_marcador_entrada_cliente.js
'use strict';
const fs = require('fs'), path = require('path');
const ler = (...p) => fs.readFileSync(path.join(__dirname, '..', ...p), 'utf8');
const norm = (t) => t.split(String.fromCharCode(13)).join('');
const js = norm(ler('game.js')), lang = norm(ler('src', 'lang', 'interface.js'));
let pass = 0, fail = 0;
function check(label, ok) { if (ok) { pass++; console.log('  ✅ ' + label); } else { fail++; console.log('  ❌ ' + label); } }

console.log('\n[1] Auxiliar único');
check('há _entradaEhPoste(state) lendo marcador_entrada', /function _entradaEhPoste\(\s*st\s*\)\s*\{[^}]*marcador_entrada\s*===\s*'poste'/.test(js));

console.log('\n[2] 2D');
const i2 = js.indexOf('// ── Stairs (dungeon entrance / exit)');
const b2 = js.slice(i2, i2 + 2600);
check('o desenho 2D ramifica por poste e não pinta a escada nele', /_entradaEhPoste\(state\)/.test(b2) && /_desenharPoste2D\(/.test(b2));
check('existe _desenharPoste2D', /function _desenharPoste2D\(/.test(js));

console.log('\n[3] 3D');
const i3 = js.indexOf('let stairGroup = null;');
const b3 = js.slice(i3, i3 + 3600);
check('o 3D monta um poste (mastro + pano) quando é poste', /_entradaEhPoste\(state\)/.test(b3) && /_montarPoste3D\(/.test(b3));
check('existe _montarPoste3D com mastro, pano e brilho pulsante (isStairGlow)', /function _montarPoste3D\(/.test(js)
  && /_montarPoste3D[\s\S]{0,1800}isStairGlow/.test(js));

console.log('\n[4] Dicas, diálogo e textos');
const tips = js.match(/ui\.tabuleiro\.escada_saida/g) || [];
check('as dicas de passar o mouse e o diálogo escolhem o nome pelo marcador', /_nomeMarcadorEntrada\(/.test(js) && (js.match(/tip.innerHTML=_dicaEntradaHTML/g) || []).length === 2);
check('a dica sem retorno existe', /ui\.tabuleiro\.poste_sem_retorno/.test(js));
for (const k of ['ui.tabuleiro.poste_entrada', 'ui.tabuleiro.poste_sem_retorno', 'ui.tabuleiro.poste_rotulo']) {
  const i = lang.indexOf('"' + k + '": {');
  const m = i < 0 ? null : [null, lang.slice(i, lang.indexOf('\n  }', i))];
  check(k + ' tem pt e en', !!m && /"pt":/.test(m[1]) && /"en":/.test(m[1]));
}

console.log(`\n=== ${pass} passaram, ${fail} falharam ===`);
process.exit(fail ? 1 : 0);
