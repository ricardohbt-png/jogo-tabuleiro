// O editor conserva renome, fato, se_falhar e alternativo dos objetivos (antes o buildJSON os apagava).
const fs = require('fs'), path = require('path');
const src = fs.readFileSync(path.join(__dirname, 'editor.js'), 'utf8');
let falhas = 0;
const ok = (c, m) => { if (!c) { falhas++; console.log('FALHOU:', m); } };
function pega(nome) {
  const i = src.indexOf('  function ' + nome + '(');
  if (i < 0) throw new Error('sem ' + nome);
  let d = 0, j = src.indexOf('{', i);
  for (let k = j; k < src.length; k++) { if (src[k] === '{') d++; else if (src[k] === '}' && --d === 0) return src.slice(i, k + 1); }
}
const corpo = ['objDefaults', 'normalizeObjective', 'objExtras', 'objSerializar', 'seFalharSerializar'].map(pega).join('\n');
const f = new Function(corpo + '; return {normalizeObjective, objSerializar, seFalharSerializar};')();
const o = f.normalizeObjective({ type: 'kill_target', renome: 4, fato: ' m ' }, true);
const s = f.objSerializar(o);
ok(s.renome === 4 && s.fato === 'm', 'objSerializar conserva renome e fato');
ok(!('renome' in f.objSerializar(f.normalizeObjective({ type: 'kill_all' }, true))), 'sem renome nada é gravado');
ok(f.seFalharSerializar({ renome: -5, fato: 'x' }).renome === -5, 'se_falhar conserva o delta negativo');
ok(f.seFalharSerializar({}) === null, 'se_falhar vazio some');
ok(/objectives\.alternativo\) \{ normalizeObjective/.test(src) || /if \(S\.objectives\.alternativo\) normalizeObjective/.test(src), 'loadJSON/buildJSON normalizam o alternativo');
ok(/alternativo: objSerializar\(S\.objectives\.alternativo\)/.test(src), 'buildJSON grava o alternativo');
console.log(falhas ? falhas + ' falha(s)' : 'ok');
process.exit(falhas ? 1 : 0);
