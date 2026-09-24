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

console.log('\n[4] _somGolpe / _somDor');
{
  const tocados = [];
  const estado = { players: [
    { id: 'h1', gear: { off_hand: { id: 'escudo_p', kind: 'shield' } } },
    { id: 'h2', gear: { off_hand: null } },
  ] };
  const f = montar(['_jogadorDaChave', '_temEscudo', '_somGolpe', '_somDor'], {
    GS: { gameState: estado },
    sfx: (e, o) => { tocados.push([e, o && o.pos]); return true; },
    _combatPrimaryDamageType: t => Array.isArray(t) ? t[0] : t,
  });
  const golpe = (c) => { tocados.length = 0; const r = f._somGolpe(c); return [r, tocados.map(x => x[0])]; };
  let [r, t] = golpe({ hit: true, impacto: 'cortante', targetPos: [1, 1], targetKey: 'm:9' });
  check('acerto cortante → golpe_cortante', r && t.join() === 'golpe_cortante');
  [r, t] = golpe({ hit: true, crit: true, impacto: 'natural', targetPos: [1, 1], targetKey: 'm:9' });
  check('crítico soma golpe_critico', t.join() === 'golpe_natural,golpe_critico');
  [r, t] = golpe({ hit: true, impacto: null, targetPos: [1, 1], targetKey: 'm:9' });
  check('sem impacto → contundente', t.join() === 'golpe_contundente');
  [r, t] = golpe({ hit: false, targetPos: [1, 1], targetKey: 'p:h1' });
  check('erro em herói com escudo → escudo_bloqueio', t.join() === 'escudo_bloqueio');
  [r, t] = golpe({ hit: false, fumble: true, targetPos: [1, 1], targetKey: 'p:h1' });
  check('falha crítica não é bloqueio → golpe_erro', t.join() === 'golpe_erro');
  [r, t] = golpe({ hit: false, targetPos: [1, 1], targetKey: 'p:h2' });
  check('erro sem escudo → golpe_erro', t.join() === 'golpe_erro');
  [r, t] = golpe({ hit: true, area: true, targetPos: [1, 1] });
  check('arremesso de área não toca golpe', r === false && t.length === 0);
  check('pos do alvo vai junto', (golpe({ hit: true, impacto: 'cortante', targetPos: [4, 5], targetKey: 'm:9' }), tocados[0][1][0] === 4));

  tocados.length = 0;
  check('dor física em herói → dor_heroi', f._somDor({ hit: true, targetKey: 'p:h1', targetPos: [1, 1] }, { damageType: ['physical'] }) && tocados[0][0] === 'dor_heroi');
  tocados.length = 0;
  check('dor física em monstro → dor_criatura', f._somDor({ hit: true, targetKey: 'm:9', targetPos: [1, 1] }, { damageType: 'physical' }) && tocados[0][0] === 'dor_criatura');
  tocados.length = 0;
  check('dano de fogo não usa dor (fica a síntese)', f._somDor({ hit: true, targetKey: 'm:9' }, { damageType: ['fire'] }) === false && tocados.length === 0);
}

console.log('\n[5] Fiação de combate');
check('base da cena leva impacto', /attacker_pos:msg\.attacker_pos, target_pos:msg\.target_pos, projectile: msg\.projectile \|\| null, impacto: msg\.impacto \|\| null/.test(GAME));
check('impact chama _somGolpe antes do cue adiado', /const tocouGolpe = !c\.tardio && _somGolpe\(c\);/.test(GAME));
check('cue adiado só toca sem amostra', /if\(f\.cueAdiado\)\{ if\(!tocouGolpe\) _playCombatCue\(f\.cueAdiado\.kind, f\.cueAdiado\.opts\); f\.cueAdiado = null; \}/.test(GAME));
check('dor tenta amostra antes da síntese', /if\(fb\.cue && !_somDor\(c, fb\)\) _playCombatCue\('damage', fb\.cue\);/.test(GAME));
check('2D (sem cena) também tenta amostra', /const tocou = _somGolpe\(\{/.test(GAME));

console.log(`\n=== ${PASS} passaram, ${FAIL} falharam ===`);
process.exit(FAIL ? 1 : 0);
