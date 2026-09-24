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

console.log('\n[3] sfx(): variante indisponível cai para outra pronta');
{
  class FakeAudioBuffer { constructor(duration) { this.duration = duration; } }
  const EV = 'clique';
  const arquivos = SB.SFX[EV].arquivos;
  check('evento de teste tem 2 variantes', arquivos.length === 2);

  const buffers = new Map();
  buffers.set(arquivos[0], 'carregando');
  buffers.set(arquivos[1], new FakeAudioBuffer(1));
  const ultimaVariante = new Map();
  ultimaVariante.set(EV, 1); // força escolherVariante(2,1) -> 0 (só resta 1 posição)
  const carregouChamadas = [];
  const ctx = {
    state: 'running',
    createBufferSource: () => ({ buffer: null, playbackRate: { value: 1 }, connect() {}, start() {} }),
    createGain: () => ({ gain: { value: 0 }, connect() {} }),
    createBiquadFilter: () => ({ type: '', frequency: { value: 0 }, connect() {} }),
    createStereoPanner: () => ({ pan: { value: 0 }, connect() {} }),
  };
  const stubs = {
    getAudioContext: () => ctx,
    GS: { gameState: null, isMaster: () => false },
    _sfxMe: () => null,
    _sfxVisaoDe: () => null,
    _sfxPan: () => 0,
    _sfxBus: () => ({}),
    _sfxCarregar: (c) => { carregouChamadas.push(c); },
    _sfxContagem: {},
    _sfxUltimaVariante: ultimaVariante,
    _sfxLimitador: SB.criarLimitador(),
    _sfxBuffers: buffers,
    AudioBuffer: FakeAudioBuffer,
  };
  const { sfx: sfxTeste } = montar(['sfx'], stubs);
  const ok = sfxTeste(EV, {});

  check('sfx() devolve true usando a variante alternativa', ok === true);
  check('tocou a variante 1 (pronta), não a 0 (carregando)', ultimaVariante.get(EV) === 1);
  check('_sfxCarregar foi chamado para a variante 0 indisponível', carregouChamadas.includes(arquivos[0]));
}

console.log(`\n=== ${PASS} passaram, ${FAIL} falharam ===`);
process.exit(FAIL ? 1 : 0);
