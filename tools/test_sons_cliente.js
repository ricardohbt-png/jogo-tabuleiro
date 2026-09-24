// tools/test_sons_cliente.js — node tools/test_sons_cliente.js
// Ganchos de som do game.js: extrai as funções REAIS e roda com stubs.
const fs = require('fs');
const path = require('path');
const raiz = path.join(__dirname, '..');
const GAME = fs.readFileSync(path.join(raiz, 'game.js'), 'utf8');
let PASS = 0, FAIL = 0;
const check = (n, c) => { if (c) { PASS++; console.log('  ✅ ' + n); } else { FAIL++; console.log('  ❌ ' + n); } };
global.window = {};
eval(fs.readFileSync(path.join(raiz, 'src', 'soundBank.js'), 'utf8'));
const SB = global.window.SoundBank;

function extrair(nome) {
  const ini = GAME.indexOf('\nfunction ' + nome + '(');
  if (ini < 0) throw new Error('função não encontrada: ' + nome);
  const fim = GAME.indexOf('\n}', ini);
  return GAME.slice(ini, fim + 2);
}
// Monta as funções pedidas num escopo com os stubs dados; devolve {nome: fn}.
function montar(nomes, stubs) {
  const corpo = nomes.map(extrair).join('\n') + '\nreturn {' + nomes.join(',') + '};';
  return new Function(...Object.keys(stubs), corpo)(...Object.values(stubs));
}

console.log('\n[1] index.html carrega o soundBank antes do game.js');
const html = fs.readFileSync(path.join(raiz, 'index.html'), 'utf8');
check('soundBank.js incluído', html.includes('src/soundBank.js'));
check('antes do game.js', html.indexOf('src/soundBank.js') < html.indexOf('"game.js?v=') || html.indexOf('src/soundBank.js') < html.indexOf("game.js?v="));

console.log('\n[2] Motor: funções existem');
for (const f of ['sfx', '_sfxCarregar', '_sfxPreCarregar', '_sfxPan', '_ambienceBus', '_ambienciaGarantir', '_ambienciaParar'])
  check('game.js define ' + f, GAME.includes('\nfunction ' + f + '('));
check('_setAmbienceVol atualiza o canal', /function _setAmbienceVol\(v\)\{[\s\S]{0,200}_ambBusNode/.test(GAME));

console.log(`\n=== ${PASS} passaram, ${FAIL} falharam ===`);
process.exit(FAIL ? 1 : 0);
