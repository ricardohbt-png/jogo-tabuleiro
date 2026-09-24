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
  const estado = { monsters: [{ id: 'e1', type: 'elemental_fogo', pos: [2, 2] }, { id: 9, type: 'goblin', pos: [1, 1] }], players: [
    { id: 'h1', gear: { off_hand: { id: 'escudo_p', kind: 'shield' } } },
    { id: 'h2', gear: { off_hand: null } },
    { id: 'h3', gear: { off_hand: { id: 'escudo_custom', item_slot: 'shield' } } },
  ] };
  const f = montar(['_jogadorDaChave', '_temEscudo', '_somGolpe', '_somDor', '_familiaElementalDaChave', '_familiaDaChave'], {
    SoundBank: SB, _sfxPronto: () => true, setTimeout: (fn) => fn(), ATRASO_DOR_ELEMENTAL_MS: 90, _retaliacaoAposDor: () => {},
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
  check('acerto sem impacto → nada toca (não é golpe físico)', r === false && t.length === 0);
  [r, t] = golpe({ hit: false, impacto: 'cortante', targetPos: [1, 1], targetKey: 'p:h1' });
  check('erro em herói com escudo → escudo_bloqueio', t.join() === 'escudo_bloqueio');
  [r, t] = golpe({ hit: false, fumble: true, impacto: 'cortante', targetPos: [1, 1], targetKey: 'p:h1' });
  check('falha crítica não é bloqueio → golpe_erro', t.join() === 'golpe_erro');
  [r, t] = golpe({ hit: false, impacto: 'cortante', targetPos: [1, 1], targetKey: 'p:h2' });
  check('erro sem escudo → golpe_erro', t.join() === 'golpe_erro');
  [r, t] = golpe({ hit: true, area: true, targetPos: [1, 1] });
  check('arremesso de área não toca golpe', r === false && t.length === 0);
  check('pos do alvo vai junto', (golpe({ hit: true, impacto: 'cortante', targetPos: [4, 5], targetKey: 'm:9' }), tocados[0][1][0] === 4));
  [r, t] = golpe({ hit: true, impacto: 'xyz', targetPos: [1, 1], targetKey: 'm:9' });
  check('impacto inválido → nada toca', r === false && t.length === 0);
  [r, t] = golpe({ hit: false, impacto: 'cortante', targetPos: [1, 1], targetKey: 'p:h3' });
  check('escudo custom (item_slot) → escudo_bloqueio', t.join() === 'escudo_bloqueio');
  [r, t] = golpe({ hit: false, impacto: null, targetPos: [1, 1], targetKey: 'p:h2' });
  check('erro sem impacto (elemental/item) → nada toca', r === false && t.length === 0);
  {
    const fCritFalha = montar(['_jogadorDaChave', '_temEscudo', '_somGolpe', '_somDor', '_familiaElementalDaChave', '_familiaDaChave'], {
    SoundBank: SB, _sfxPronto: () => true, setTimeout: (fn) => fn(), ATRASO_DOR_ELEMENTAL_MS: 90, _retaliacaoAposDor: () => {},
      GS: { gameState: estado },
      sfx: (e) => e !== 'golpe_critico',
      _combatPrimaryDamageType: t2 => Array.isArray(t2) ? t2[0] : t2,
    });
    const rCrit = fCritFalha._somGolpe({ hit: true, crit: true, impacto: 'cortante', targetPos: [1, 1], targetKey: 'm:9' });
    check('crítico sem amostra → _somGolpe devolve false', rCrit === false);
  }

  tocados.length = 0;
  check('dor física em herói → dor_heroi', f._somDor({ hit: true, targetKey: 'p:h1', targetPos: [1, 1] }, { damageType: ['physical'] }) && tocados[0][0] === 'dor_heroi');
  tocados.length = 0;
  check('dor física em goblin → gemido da família (dor_humanoide)', f._somDor({ hit: true, targetKey: 'm:9', targetPos: [1, 1] }, { damageType: 'physical' }) && tocados[0][0] === 'dor_humanoide');
  tocados.length = 0;
  check('dano de fogo em elemental de fogo → dor_elem_fogo', f._somDor({ hit: true, targetKey: 'm:e1', targetPos: [2, 2] }, { damageType: 'fire' }) && tocados[0][0] === 'dor_elem_fogo');
  tocados.length = 0;
  check('dano físico em elemental → dor_elem_fogo (não dor_criatura)', f._somDor({ hit: true, targetKey: 'm:e1', targetPos: [2, 2] }, { damageType: 'physical' }) && tocados[0][0] === 'dor_elem_fogo');
  tocados.length = 0;
  check('golpe que mata elemental não toca dor', f._somDor({ hit: true, death: true, targetKey: 'm:e1' }, { damageType: 'fire' }) === true && tocados.length === 0);
  tocados.length = 0;
  check('dano de fogo não usa dor (fica a síntese)', f._somDor({ hit: true, targetKey: 'm:9' }, { damageType: ['fire'] }) === false && tocados.length === 0);
  tocados.length = 0;
  check('dor física em prisioneiro → dor_heroi', f._somDor({ hit: true, targetKey: 'pr:singleton', targetPos: [1, 1] }, { damageType: ['physical'] }) && tocados[0][0] === 'dor_heroi');
  tocados.length = 0;
  check('golpe fatal (c.death) suprime a dor e o cue de dano', f._somDor({ hit: true, death: true, targetKey: 'm:9', targetPos: [1, 1] }, { damageType: ['physical'] }) === true && tocados.length === 0);
}

console.log('\n[5] Fiação de combate');
check('base da cena leva impacto', /attacker_pos:msg\.attacker_pos, target_pos:msg\.target_pos, projectile: msg\.projectile \|\| null, impacto: msg\.impacto \|\| null/.test(GAME));
check('impact chama _somGolpe antes do cue adiado', /const tocouGolpe = !c\.tardio && _somGolpe\(c\);/.test(GAME));
check('cue adiado só toca sem amostra', /if\(f\.cueAdiado\)\{ if\(!tocouGolpe\) _playCombatCue\(f\.cueAdiado\.kind, f\.cueAdiado\.opts\); f\.cueAdiado = null; \}/.test(GAME));
check('dor tenta amostra antes da síntese', /if\(fb\.cue && !_somDor\(c, fb\)\) _playCombatCue\('damage', fb\.cue\);/.test(GAME));
check('2D (sem cena) também tenta amostra', /const tocou = _somGolpe\(\{/.test(GAME));
check('_detectHpChanges tenta _somDor antes do cue sem cena', /if\(!_somDor\(\{hit:true, targetKey:key, targetPos: impact \|\| entry\.pos\}, \{damageType: primaryDamageType\}\)\) _playCombatCue\('damage', cue\);/.test(GAME));

console.log('\n[6] _somMorteMonstro');
{
  const tocados = [], sintese = [];
  const f = montar(['_somMorteMonstro'], {
    SoundBank: SB,
    sfx: (e) => { tocados.push(e); return true; },
    _playDefeatSound: k => sintese.push(k),
  });
  f._somMorteMonstro({ type: 'goblin', pos: [1, 1] }, 'common');
  check('goblin → morte_humanoide, sem síntese', tocados.join() === 'morte_humanoide' && sintese.length === 0);
  tocados.length = 0;
  f._somMorteMonstro({ type: 'boneco_treino', pos: [1, 1] }, 'magic');
  check('sem família → síntese antiga', tocados.length === 0 && sintese.join() === 'magic');
}
{
  const sintese = [];
  const f = montar(['_somMorteMonstro'], { SoundBank: SB, sfx: () => false, _playDefeatSound: k => sintese.push(k) });
  f._somMorteMonstro({ type: 'goblin', pos: [1, 1] }, 'boss');
  check('amostra ausente → síntese antiga', sintese.join() === 'boss');
}

console.log('\n[7] _capturarSonsDeEstado');
{
  const tocados = [];
  const stubs = {
    SoundBank: SB,
    GS: { myPid: 'h1', doorSets: st => ({ open: new Set(st.abertas || []) }) },
    sfx: (e, o) => { tocados.push([e, o && o.pos]); return true; },
    _sfxVisaoDe: () => new Set(['2,2', '4,4']),
    _sonsPassosDeEstado: () => {},
  };
  // O snapshot `_sonsSnap` é estado de módulo do game.js: recriado aqui, com reset.
  const src = extrair('_capturarSonsDeEstado');
  const f = new Function(...Object.keys(stubs),
    'let _sonsSnap = null; let _rugiram = new Set();\n' + src + '\nreturn { _capturarSonsDeEstado, reset(){ _sonsSnap = null; } };')(...Object.values(stubs));
  const st = (extra) => Object.assign({ players: [{ id: 'h1', pos: [0, 0], gold: 5, bag: [], gear: {}, level: 1 }],
    monsters: [{ id: 'm1', type: 'goblin', hp: 5, pos: [2, 2] }], current_turn: 'x', abertas: [] }, extra);
  f.reset();
  f._capturarSonsDeEstado(st());
  check('1º estado não toca', tocados.length === 0);
  f._capturarSonsDeEstado(st({ current_turn: 'h1', abertas: ['4,4'] }));
  const nomes = tocados.map(x => x[0]);
  check('porta aberta e sua vez', nomes.includes('porta_abre') && nomes.includes('sua_vez'));
  check('porta leva a posição', tocados.find(x => x[0] === 'porta_abre')[1][0] === 4);
  tocados.length = 0;
  f._capturarSonsDeEstado(st({ current_turn: 'h1', abertas: ['4,4'],
    monsters: [{ id: 'm1', type: 'goblin', hp: 5, pos: [2, 2] }, { id: 'm2', type: 'lobo_cinzento', hp: 5, pos: [9, 9] }] }));
  check('monstro fora da visão NÃO ruge', tocados.length === 0);
  f._capturarSonsDeEstado(st({ current_turn: 'h1', abertas: ['4,4'],
    monsters: [{ id: 'm1', type: 'goblin', hp: 5, pos: [2, 2] }, { id: 'm2', type: 'lobo_cinzento', hp: 5, pos: [4, 4] }] }));
  check('ao entrar na visão ruge', tocados.map(x => x[0]).join() === 'rugido_fera');
  tocados.length = 0;
  f._capturarSonsDeEstado(st({ current_turn: 'h1', abertas: ['4,4'],
    monsters: [{ id: 'm3', type: 'goblin', hp: 0, pos: [2, 2] }] }));
  check('monstro morto não ruge', tocados.length === 0);
}

console.log('\n[8] Fiação de estado, morte e ambiente');
check('morte sem cena usa _somMorteMonstro', /_spawnDefeatVisual\(anterior, kind\);\s*_somMorteMonstro\(anterior, kind\);/.test(GAME));
check('morte com cena usa _somMorteMonstro', /onImpact: \[\(\) => \{ _spawnDefeatVisual\(anterior, kind\); _somMorteMonstro\(anterior, kind\); \}\]/.test(GAME));
check('gameState envolve sons/ambiente em try/catch', /_detectHpChanges\(msg\);[^\n]*\n\s*try\{ _capturarSonsDeEstado\(msg\); _ambienciaGarantir\(msg\); \}catch\(e\)\{ console\.warn\('sons:', e\); \}/.test(GAME));
check('enterDungeon zera sons e toca escada (em try/catch)', /GS\.on\('enterDungeon'[\s\S]{0,3000}try\{ _sfxPreCarregar\(\); _sonsReset\(\); sfx\('escada'\); \}catch\(e\)\{ console\.warn\('sons:', e\); \}/.test(GAME));
check('cityState para o ambiente e pré-carrega (em try/catch)', /GS\.on\('cityState'[\s\S]{0,1500}try\{ _ambienciaParar\(\); _sonsReset\(\); _sfxPreCarregar\(\); \}catch\(e\)\{ console\.warn\('sons:', e\); \}/.test(GAME));
check('handleGameOver para o ambiente', /function handleGameOver\(msg\)\{\s*_ambienciaParar\(\);/.test(GAME));
check('showScreen para o ambiente ao sair da masmorra/cidade', /if\(id !== 'screen-game' && id !== 'screen-city'\)\{[\s\S]{0,600}_ambienciaParar\(\);/.test(GAME));

console.log('\n[9] Interface');
const regs = GAME.match(/GS\.on\('serverError'/g) || [];
check('um único GS.on(serverError)', regs.length === 1);
check('o ouvinte único limpa a prévia do Ataque Giratório',
  /GS\.on\('serverError', msg  => \{[\s\S]{0,300}_limparPreviewAtaqueGiratorio\(\)/.test(GAME));
check('o ouvinte único toca recusa', /GS\.on\('serverError', msg  => \{[\s\S]{0,400}sfx\('recusa'\)/.test(GAME));
check('clique delegado em botões', /closest\('button'\)[\s\S]{0,200}sfx\('clique'\)/.test(GAME));
check('_ambienciaGarantir só roda com a tela da masmorra ativa',
  /function _ambienciaGarantir\(state\)\{\s*if\(!document\.getElementById\('screen-game'\)\?\.classList\.contains\('active'\)\) return;/.test(GAME));
check('reconnectFailed para o ambiente',
  /GS\.on\('reconnectFailed', \(\) => \{[\s\S]{0,120}_ambienciaParar\(\);/.test(GAME));

console.log('\n[10] Nenhum GS.on duplicado no game.js');
const nomes = [...GAME.matchAll(/^GS\.on\('([A-Za-z_]+)'/gm)].map(m => m[1]);
const dup = nomes.filter((n, i) => nomes.indexOf(n) !== i);
check('sem duplicatas (GS.on substitui o anterior): ' + (dup.join(',') || 'ok'), dup.length === 0);

console.log('\n[11] Passos dos peões: canal próprio, monstros e outros jogadores');
check('canal _stepsBus existe', GAME.includes('\nfunction _stepsBus('));
check('tocarSomPasso sai pelo canal dos passos', /function tocarSomPasso\([\s\S]{0,1500}fim\.connect\(_stepsBus\(\)\)/.test(GAME));
check('ganho de saída depois do compressor', /comp\.connect\(saida\)/.test(GAME));
check('volume dos passos é salvo', /steps: _stepsVol/.test(GAME) && /o\.steps/.test(GAME));
check('slider no painel de áudio', GAME.includes('id="aud-steps"') && /_setStepsVol\(pSl\.value \/ 100\)/.test(GAME));
check('entity_step de monstro/servo agenda o passo', /function _onEntityStep[\s\S]{0,1200}msg\.kind !== 'player'[\s\S]{0,300}_somPassoEm\(to\)/.test(GAME));
check('_capturarSonsDeEstado chama o diff de passos', /function _capturarSonsDeEstado\(state\)\{[\s\S]{0,80}_sonsPassosDeEstado\(state\)/.test(GAME));
check('_sonsReset zera as posições', /function _sonsReset\(\)\{[^}]*_passosReset\(\)/.test(GAME));
{
  const timers = [], tocados = [];
  const stubs = {
    GS: { myPid: 'h1', isPreview: false, gameState: null },
    _sfxVisaoDe: () => new Set(['1,0', '2,0', '3,0', '5,5', '6,5']),
    tocarSomPasso: (o) => tocados.push(o.pos.join(',')),
    setTimeout: (fn, ms) => timers.push([ms, fn]),
    performance: { now: () => 1000 },
    DURACAO_PASSO_MS: 250,
    mode3D: true,
  };
  const corpo = 'let _passosPosAnt = new Map(); const _passosProxT = new Map();\n'
    + ['_somPassoEm', '_passosReset', '_sonsPassosDeEstado'].map(extrair).join('\n')
    + '\nreturn { _somPassoEm, _passosReset, _sonsPassosDeEstado };';
  const f = new Function(...Object.keys(stubs), corpo)(...Object.values(stubs));
  const st = (h1, h2) => ({ players: [{ id: 'h1', alive: true, pos: h1 }, { id: 'h2', alive: true, pos: h2 }] });
  const rodar = () => { timers.sort((a, b) => a[0] - b[0]).forEach(([, fn]) => fn()); timers.length = 0; };
  f._sonsPassosDeEstado(stubs.GS.gameState = st([0, 0], [0, 0]));
  check('1º estado não toca passo', timers.length === 0);
  f._sonsPassosDeEstado(stubs.GS.gameState = st([1, 0], [3, 0]));
  check('outro jogador andou 3 casas → 3 passos espaçados (seu peão 3D fica de fora)',
    timers.map(t => t[0]).sort((a, b) => a - b).join() === '0,250,500');
  rodar();
  check('passos nas casas do caminho', tocados.join(' ') === '1,0 2,0 3,0');
  tocados.length = 0;
  f._sonsPassosDeEstado(stubs.GS.gameState = st([1, 0], [9, 9]));
  check('salto grande (teleporte) não toca', timers.length === 0);
  f._somPassoEm([8, 8]);
  check('passo na névoa não toca', tocados.length === 0);
  f._somPassoEm([5, 5]);
  check('passo visível toca', tocados.join() === '5,5');
  f._passosReset(); tocados.length = 0;
  f._sonsPassosDeEstado(stubs.GS.gameState = st([2, 0], [6, 5]));
  check('após reset o 1º estado não toca', timers.length === 0);
}

console.log('\n[12] Baú velho ao abrir');
check('catálogo tem bau_abre com 3 versões', SB.SFX.bau_abre && SB.SFX.bau_abre.arquivos.length === 3);
check('openChestWindow toca bau_abre e recua para o arpejo', /function openChestWindow\(chest\)\{[\s\S]{0,400}if\(!sfx\('bau_abre'\)\) tocarSomBau\(\);/.test(GAME));

console.log('\n[13] Explosão da Mina Terrestre (armadilha_disparo)');
{
  const GSJS = fs.readFileSync(path.join(raiz, 'src', 'gameState.js'), 'utf8');
  check('gameState repassa armadilha_disparo', /case 'armadilha_disparo':\s*(\/\/[^\n]*)?\s*_emit\('armadilhaDisparo', msg\)/.test(GSJS));
  check('game.js escuta armadilhaDisparo', /^GS\.on\('armadilhaDisparo', msg => \{ try\{ _somDisparoArmadilha\(msg\); \}catch\(e\)\{\} \}\);/m.test(GAME));
  check('catálogo tem explosao com 3 versões', SB.SFX.explosao && SB.SFX.explosao.arquivos.length === 3);
  const tocados = [], timers = [];
  const src = extrair('_somDisparoArmadilha');
  const f = new Function('GS', 'sfx', 'setTimeout',
    "const SOM_DISPARO_ARMADILHA = { mina_terrestre: 'explosao' }; const ATRASO_IMPACTO_ARMADILHA_MS = 240;\n" + src + '\nreturn _somDisparoArmadilha;')(
    { isPreview: false }, (e, o) => { tocados.push([e, o.pos]); return true; }, (fn, ms) => timers.push([ms, fn]));
  f({ type: 'armadilha_disparo', tipo_id: 'mina_terrestre', pos: [3, 4] });
  check('explosão agendada no impacto (240 ms)', timers.length === 1 && timers[0][0] === 240);
  timers[0][1]();
  check('toca explosao na casa da mina', tocados.length === 1 && tocados[0][0] === 'explosao' && tocados[0][1][0] === 3);
  timers.length = 0;
  f({ type: 'armadilha_disparo', tipo_id: 'nuvem_gas', pos: [3, 4] });
  check('nuvem de gás não explode', timers.length === 0);
  check('constante do código bate com o teste', /const SOM_DISPARO_ARMADILHA = \{ mina_terrestre: 'explosao' \};/.test(GAME) && /const ATRASO_IMPACTO_ARMADILHA_MS = 240;/.test(GAME));
}

console.log('\n[14] Impacto de itens: granadas (explosão) e incendiários (estouro + labaredas)');
{
  const CSJS = fs.readFileSync(path.join(raiz, 'src', 'combatScene.js'), 'utf8');
  const GSJS = fs.readFileSync(path.join(raiz, 'src', 'gameState.js'), 'utf8');
  check('impact da CombatScene carrega item_id', /function emitirImpacto[\s\S]{0,800}item_id: s\.projectile \? \(s\.projectile\.item_id \|\| null\) : null/.test(CSJS));
  check('impact não-tardio toca o som do item (área sempre, alvo só no acerto)', /const tocouGolpe = !c\.tardio && _somGolpe\(c\);\s*if\(!c\.tardio\) try\{ _somExplosaoItem\(c\.item_id, c\.targetPos, c\.area \|\| c\.hit\);[^}]*\}catch\(e\)\{\}/.test(GAME));
  check('sem cena (2D) também toca, pelo itemId guardado no start', /itemId: \(msg\.projectile && msg\.projectile\.item_id\) \|\| null/.test(GAME) && /_somExplosaoItem\(f\.itemId, msg\.target_pos, f\.area \|\| !!msg\.hit\)/.test(GAME));
  check('gameState repassa item_impacto', /case 'item_impacto':\s*(\/\/[^\n]*)?\s*_emit\('itemImpacto', msg\)/.test(GSJS));
  check('game.js escuta itemImpacto (com hit)', /^GS\.on\('itemImpacto', msg => \{ try\{ _somExplosaoItem\(msg && msg\.item_id, msg && msg\.pos, msg && msg\.hit !== false\); \}catch\(e\)\{\} \}\);/m.test(GAME));
  const mapa = GAME.match(/const SOM_IMPACTO_ITEM = \{[\s\S]*?\};/)[0];
  const tocados = [];
  const f = new Function('GS', 'sfx', mapa + '\n' + extrair('_somExplosaoItem') + '\nreturn _somExplosaoItem;')(
    { isPreview: false }, (e, o) => { tocados.push([e, o.pos]); return true; });
  f('granada', [4, 4]); f('granada_superior', [1, 2]); f('bomba_fumaca', [1, 1]); f('frasco_acido', [1, 1]); f(null, null);
  check('granadas explodem; fumaça e ácido não', tocados.map(x => x[0]).join() === 'explosao,explosao');
  check('na casa do impacto', tocados[0][1][0] === 4 && tocados[1][1][1] === 2);
  tocados.length = 0;
  f('bomba_incendiaria', [2, 2]); f('fogo_grego', [3, 3], true); f('frasco_oleo', [5, 5], true);
  check('bomba incendiária, fogo grego e óleo: estouro + labaredas', tocados.map(x => x[0]).join() === 'incendio,incendio,incendio');
  tocados.length = 0;
  f('fogo_grego', [3, 3], false); f('frasco_oleo', [5, 5], false);
  check('fogo grego / óleo que ERRAM não pegam fogo (sem som)', tocados.length === 0);
  check('catálogo tem incendio com 3 versões', SB.SFX.incendio && SB.SFX.incendio.arquivos.length === 3);
}

console.log('\n[15] Elementais: ataque, dor atrasada e rugido na primeira ação');
{
  const tocados = [], timers = [];
  const estado = { monsters: [
    { id: 'e1', type: 'elemental_eletrico', pos: [3, 3] },
    { id: 'g1', type: 'goblin', pos: [4, 3] },
  ] };
  const stubs = {
    GS: { gameState: estado }, SoundBank: SB,
    sfx: (e, o) => { tocados.push([e, o && o.pos]); return true; },
    _sfxPronto: () => true, setTimeout: (fn, ms) => timers.push([ms, fn]), _retaliacaoAposDor: () => {},
    _combatPrimaryDamageType: t => Array.isArray(t) ? t[0] : t,
  };
  const corpo = 'const ATRASO_DOR_ELEMENTAL_MS = 90; let _rugiram = new Set();\n'
    + ['_familiaElementalDaChave', '_familiaDaChave', '_somAtaqueElemental', '_somRugidoAoAgir', '_somDor'].map(extrair).join('\n')
    + '\nreturn { _somAtaqueElemental, _somRugidoAoAgir, _somDor, marcar: id => _rugiram.add(id) };';
  const f = new Function(...Object.keys(stubs), corpo)(...Object.values(stubs));
  check('raio do elemental elétrico → ataque_elem_eletrico', f._somAtaqueElemental({ attackerKey: 'm:e1', targetPos: [4, 3] }) && tocados.pop()[0] === 'ataque_elem_eletrico');
  check('ataque de goblin não toca som de elemento', f._somAtaqueElemental({ attackerKey: 'm:g1', targetPos: [3, 3] }) === false && tocados.length === 0);
  check('catálogo tem ataque_ para os 6 elementos', SB.FAMILIAS_ELEMENTO.every(x => SB.SFX['ataque_' + x] && SB.SFX['ataque_' + x].arquivos.length === 2));
  f._somDor({ hit: true, targetKey: 'm:e1', targetPos: [3, 3] }, { damageType: 'physical' });
  check('dor do elemental é agendada 90 ms depois do golpe', timers.length === 1 && timers[0][0] === 90 && tocados.length === 0);
  timers[0][1](); timers.length = 0;
  check('…e toca dor_elem_eletrico', tocados.pop()[0] === 'dor_elem_eletrico');
  f._somRugidoAoAgir('g1');
  check('1ª ação do goblin ruge', tocados.length === 1 && tocados[0][0] === 'rugido_humanoide');
  f._somRugidoAoAgir('g1');
  check('2ª ação não ruge de novo', tocados.length === 1);
  tocados.length = 0;
  f._somRugidoAoAgir('e1');
  check('elemental não ruge ao agir (o golpe já é o som dele)', tocados.length === 0);
  f.marcar('x9'); estado.monsters.push({ id: 'x9', type: 'orc', pos: [1, 1] });
  f._somRugidoAoAgir('x9');
  check('quem já rugiu ao ser visto não ruge ao agir', tocados.length === 0);
  f._somRugidoAoAgir('heroi_1');
  check('herói não ruge', tocados.length === 0);
  check('rugido ao agir ligado no start do attack_feedback', /_playCombatCue\('attack', \{repeatKey:'attack', volume:\.9\}\);\s*try\{ _somRugidoAoAgir\(msg\.attacker_id\); \}catch\(e\)\{\}/.test(GAME));
  check('ataque elemental no impact da cena', /_somExplosaoItem\(c\.item_id, c\.targetPos, c\.area \|\| c\.hit\); _somAtaqueElemental\(c\);/.test(GAME));
  check('ataque elemental também sem cena (2D)', /_somAtaqueElemental\(\{ attackerKey: _entityKeyById\(msg\.attacker_id\), targetPos: msg\.target_pos \}\)/.test(GAME));
  check('rugido do estado marca o id; reset zera', /if\(e\.id != null\) _rugiram\.add\(String\(e\.id\)\);/.test(GAME) && /_rugiram = new Set\(\);[^}]*\}/.test(GAME));
  check('diffSons manda o id no rugido', SB.diffSons(SB.diffSons(null, { monstros: [] }).snap, { monstros: [{ id: 'k', type: 'goblin', pos: [0, 0] }] }).eventos[0].id === 'k');
}

console.log('\n[16] Raio do elemental e elemental invocado (servo)');
{
  const tocados = [];
  const estado = { monsters: [], players: [{ id: 'h1', animados: [
    { id: 's1', tipo: 'elemental', tipo_elemental: 'gelo', pos: [2, 2] },
    { id: 's2', tipo: 'esqueleto', pos: [3, 3] } ] }] };
  const f = new Function('GS', 'SoundBank', 'sfx', extrair('_familiaElementalDaChave') + extrair('_somAtaqueElemental') + '\nreturn { _familiaElementalDaChave, _somAtaqueElemental };')(
    { gameState: estado }, SB, (e, o) => { tocados.push(e); return true; });
  check('servo elemental de gelo → elem_gelo', f._familiaElementalDaChave('a:s1') === 'elem_gelo');
  check('servo esqueleto → sem voz de elemento', f._familiaElementalDaChave('a:s2') === null);
  f._somAtaqueElemental({ attackerKey: 'a:s1', targetPos: [1, 1] });
  check('golpe do servo elemental toca ataque_elem_gelo', tocados.join() === 'ataque_elem_gelo');
  check('catálogo tem relampago com 2 versões', SB.SFX.relampago && SB.SFX.relampago.arquivos.length === 2);
  check('raio do elemental toca relampago ao sair', /function _receberAnimacaoRaioElemental\(msg\)\{[\s\S]{0,700}sfx\('relampago',\{pos:Array\.isArray\(msg\.origin\)\?msg\.origin:undefined\}\)/.test(GAME));
}

console.log('\n[17] Teste de som (⚙️ → Áudio)');
{
  check('botão no painel de áudio', GAME.includes('id="aud-som-teste"') && /#aud-som-teste'\)\.onclick = \(\) => \{ pop\.style\.display = 'none'; abrirSoundTest\(\); \}/.test(GAME));
  check('clique delegado ignora o painel de teste', /!b\.closest\('#som-teste'\)\) sfx\('clique'\)/.test(GAME));
  const f = new Function('t', "const _SOMTESTE_GRUPOS = [];\n" + extrair('_somTesteNome') + '\nreturn _somTesteNome;')(k => k);
  check('nome de criatura = ação + família', f('ataque_elem_eletrico') === 'ui.somteste.acao.ataque — ui.somteste.familia.elem_eletrico');
  check('dor_heroi usa nome próprio (não vira ação+família)', f('dor_heroi') === 'ui.somteste.ev.dor_heroi');
  // Toda chave que o painel pode pedir existe no dicionário (pt e en).
  global.window.LANG_STRINGS = {};
  eval(fs.readFileSync(path.join(raiz, 'src', 'lang', 'interface.js'), 'utf8'));
  const D = global.window.LANG_STRINGS;
  const pedidas = new Set(['ui.somteste.abrir', 'ui.somteste.titulo', 'ui.somteste.dica', 'ui.somteste.parar', 'ui.somteste.fechar', 'ui.somteste.tocar_versao', 'ui.somteste.grupo.sintetizados']);
  for (const [ev, def] of Object.entries(SB.SFX)) {
    pedidas.add('ui.somteste.grupo.' + def.arquivos[0].split('/')[0]);
    for (const k of f(ev).split(' — ')) pedidas.add(k);
  }
  for (const ev of ['passo', 'bau_arpejo', 'armadilha']) pedidas.add('ui.somteste.ev.' + ev);
  const faltam = [...pedidas].filter(k => !(D[k] && D[k].pt && D[k].en));
  check('todo nome do catálogo tem chave pt/en: ' + (faltam.join(', ') || 'ok'), faltam.length === 0);
}

console.log('\n[18] Choque da aura (retaliação) com o som do elemento');
{
  const tocados = [], timers = [];
  let agora = 1000;
  const f = new Function('GS', 'SoundBank', 'sfx', 'setTimeout', 'clearTimeout', 'performance',
    'const RETALIACAO_APOS_DOR_MS = 120; const RETALIACAO_ESPERA_MAX_MS = 3500; const _retaliacaoPend = new Map(); const _dorElementalEm = new Map();\n'
    + extrair('_somRetaliacao') + extrair('_retaliacaoAposDor') + '\nreturn { _somRetaliacao, _retaliacaoAposDor };')(
    { isPreview: false }, SB, (e, o) => { tocados.push([e, o && o.pos]); return true; },
    (fn, ms) => { timers.push({ fn, ms, vivo: true }); return timers.length - 1; }, (id) => { if (timers[id]) timers[id].vivo = false; },
    { now: () => agora });
  const rodar = () => { const t = timers.filter(x => x.vivo); timers.length = 0; t.forEach(x => x.fn()); };
  const msg = { type: 'dice_roll', retaliacao_tipo: 'elemental_eletrico', retaliacao_pos: [4, 3], damage_type: 'lightning' };
  f._somRetaliacao(msg);
  check('com cena: o choque espera o golpe (nada toca ainda)', tocados.length === 0 && timers.length === 1 && timers[0].ms === 3500);
  f._retaliacaoAposDor('elem_eletrico');
  check('a dor do elemental solta o choque 120 ms depois', timers.filter(x => x.vivo).map(x => x.ms).join() === '120');
  rodar();
  check('toca a faísca (ataque_elem_eletrico) na casa de quem levou o choque', tocados.length === 1 && tocados[0][0] === 'ataque_elem_eletrico' && tocados[0][1][0] === 4);
  tocados.length = 0; agora = 5000;
  f._retaliacaoAposDor('elem_eletrico');    // sem cena: a dor veio ANTES do dado
  agora = 5200;
  f._somRetaliacao(msg);
  check('sem cena (dor acabou de tocar): choque sai já, 120 ms depois', timers.filter(x => x.vivo).map(x => x.ms).join() === '120');
  rodar(); tocados.length = 0;
  agora = 20000;
  f._somRetaliacao(msg); rodar();
  check('sem golpe nenhum: a rede de segurança toca mesmo assim', tocados.length === 1);
  tocados.length = 0;
  f._somRetaliacao({ ...msg, retaliacao_tipo: 'elemental_fogo' }); rodar();
  check('elemental de fogo: labareda', tocados.map(x => x[0]).join() === 'ataque_elem_fogo');
  tocados.length = 0; timers.length = 0;
  check('carapaça espinhosa (não elemental) não usa som de elemento', f._somRetaliacao({ ...msg, retaliacao_tipo: 'aranha_espinhosa' }) === false && timers.length === 0);
  check('dado comum (sem retaliacao_tipo) ignorado', f._somRetaliacao({ type: 'dice_roll', value: 3 }) === false);
  check('ligado no GS.on(diceRoll)', /^GS\.on\('diceRoll', +msg +=> \{ _receberDadoVisual\(msg\); try\{ _somRetaliacao\(msg\); \}catch\(e\)\{\} \}\);/m.test(GAME));
  check('_somDor avisa a retaliação quando a dor do elemental toca', /sfx\('dor_' \+ famEl, \{pos\}\); _retaliacaoAposDor\(famEl\);/.test(GAME));
}

console.log('\n[19] Bomba de fumaça: nuvem guiada pela zona');
{
  let agora = 10000;
  const tocados = [], timers = [];
  const stubs = {
    GS: { isPreview: false }, mode3D: true, g3: null,
    performance: { now: () => agora },
    CombatScene: { areaImpactAt: () => 10700 },
    sfx: (e, o) => { tocados.push([e, o && o.pos && o.pos.join(',')]); return true; },
    setTimeout: (fn, ms) => { timers.push([ms, fn]); return 1; },
    _scheduleVisualFrame: () => 1,
    _tickFumaca2D: () => {},
  };
  global.window.CombatScene = stubs.CombatScene;
  const nomes = ['_ehZonaFumaca', '_fumacaReset', '_fumacaSync', '_fumacaAvancar', '_fumacaFase'];
  const corpo = "const FUMACA_NASCER_MS = 1100, FUMACA_SAIR_MS = 1600, FUMACA_ANEL_MS = 450;\n"
    + GAME.match(/const FUMACA_NOVELOS[^\n]*/)[0] + '\n'
    + "const FUMACA_CORES = [1,2,3,4]; const _fumacaNuvens = new Map(); let _fumacaBaseline = true; let _fumaca2DRaf = null;\n"
    + "function _fumacaDispose3D(n){ n.group = null; }\n"
    + nomes.map(extrair).join('\n') + '\nreturn { ' + nomes.join(', ') + ', mapa: _fumacaNuvens };';
  const f = new Function(...Object.keys(stubs), 'window', corpo)(...Object.values(stubs), { CombatScene: stubs.CombatScene });
  const zona = (vid, extra) => Object.assign({ tipo: 'escuridao', ativa: true, cx: 5, cy: 4, raio: 1, duracao: 2, visual_id: vid }, extra);
  check('zona da bomba é fumaça; Manto não é', f._ehZonaFumaca(zona('fumaca_p1_3_5_4')) && !f._ehZonaFumaca(zona('manto_x')) && !f._ehZonaFumaca(zona(null)));
  f._fumacaSync({ round: 3, zonas_especiais: [zona('fumaca_p1_2_1_1', { cx: 1, cy: 1 })] });
  const velha = f.mapa.get('fumaca_p1_2_1_1');
  check('1º estado (entrou com a zona já ativa): nuvem nasce pronta e muda', velha && velha.somTocado && f._fumacaFase(velha, agora).nasc === 1);
  f._fumacaSync({ round: 3, zonas_especiais: [zona('fumaca_p1_2_1_1', { cx: 1, cy: 1 }), zona('fumaca_p1_3_5_4')] });
  const nova = f.mapa.get('fumaca_p1_3_5_4');
  check('bomba desta rodada nasce na CHEGADA do frasco (areaImpactAt)', nova && nova.nasceEm === 10700 && !nova.somTocado);
  f._fumacaAvancar(agora);
  check('antes da chegada: sem som', tocados.length === 0 && f._fumacaFase(nova, agora).antes);
  agora = 10710; f._fumacaAvancar(agora);
  check('na chegada: puff na casa da bomba', tocados.map(x => x.join('@')).join() === 'fumaca_puff@5,4');
  timers.find(t => t[0] === 120)[1]();
  check('…e o chiado 120 ms depois', tocados[1] && tocados[1][0] === 'fumaca_chiado');
  f._fumacaSync({ round: 4, zonas_especiais: [zona('fumaca_p1_3_5_4', { duracao: 1 })] });
  check('última rodada: nuvem afina', nova.ultima === true && f._fumacaFase(nova, agora).alvo === Number(/FUMACA_OPACIDADE_FIM = ([\d.]+)/.exec(GAME)[1]));
  check('zona que sumiu começa a se desfazer', velha.saiEm === agora);
  agora += 1700; f._fumacaAvancar(agora);
  check('depois de 1,6 s a nuvem desfeita é removida', !f.mapa.has('fumaca_p1_2_1_1') && f.mapa.has('fumaca_p1_3_5_4'));
  f._fumacaReset();
  check('reset (masmorra nova) limpa tudo', f.mapa.size === 0);
  check('fumaça fora da névoa roxa do Manto', /zz\.filter\(z => z\.ativa && z\.tipo === 'escuridao' && !_ehZonaFumaca\(z\)\)/.test(GAME));
  check('ligada no renderMap, no laço 3D e no desenho 2D', /_tempestadeSyncFromState\(state\);\s*_fumacaSync\(state\);/.test(GAME)
    && /_updateArmadilhas3D\(now\);\s*_updateFumaca3D\(now\);/.test(GAME) && /_fumacaDraw2D\(ctx, state, _agoraRelampago\);/.test(GAME));
  check('catálogo tem fumaca_puff e fumaca_chiado', SB.SFX.fumaca_puff && SB.SFX.fumaca_chiado && SB.SFX.fumaca_puff.arquivos.length === 2);
}

console.log('\n[20] Gemido de dano por família de criatura');
{
  const tocados = [], timers = [];
  const estado = { monsters: [
    { id: 'l', type: 'lobo_cinzento', pos: [1, 1] }, { id: 'z', type: 'zumbi_infectado', pos: [2, 2] },
    { id: 'a', type: 'aranha_gigante', pos: [3, 3] }, { id: 'o', type: 'ogro_das_cavernas', pos: [4, 4] },
    { id: 'b', type: 'boneco_treino', pos: [5, 5] } ] };
  const stubs = { GS: { gameState: estado }, SoundBank: SB, _sfxPronto: () => true,
    setTimeout: (fn, ms) => { timers.push(ms); fn(); }, ATRASO_DOR_ELEMENTAL_MS: 90, _retaliacaoAposDor: () => {},
    sfx: (e) => { tocados.push(e); return true; }, _combatPrimaryDamageType: t => t };
  const f = montar(['_familiaElementalDaChave', '_familiaDaChave', '_somDor'], stubs);
  const dor = k => { tocados.length = 0; timers.length = 0; f._somDor({ hit: true, targetKey: 'm:' + k, targetPos: [0, 0] }, { damageType: 'physical' }); return tocados[0]; };
  check('lobo (fera) → dor_fera', dor('l') === 'dor_fera');
  check('…90 ms depois do golpe (não encoberto)', timers[0] === 90);
  check('zumbi → dor_morto_vivo', dor('z') === 'dor_morto_vivo');
  check('aranha → dor_reptil_inseto', dor('a') === 'dor_reptil_inseto');
  check('ogro → dor_grande', dor('o') === 'dor_grande');
  check('boneco (sem voz) → dor_criatura genérico', dor('b') === 'dor_criatura');
  check('fogo em lobo não geme (só dano físico)', (tocados.length = 0, f._somDor({ hit: true, targetKey: 'm:l' }, { damageType: 'fire' }) === false && tocados.length === 0));
  for (const fam of SB.FAMILIAS) {
    check(`${fam}: 4 aparições, 3 mortes, 3 gemidos`, SB.SFX['rugido_' + fam].arquivos.length === 4
      && SB.SFX['morte_' + fam].arquivos.length === 3 && SB.SFX['dor_' + fam].arquivos.length === 3);
  }
}

console.log(`\n=== ${PASS} passaram, ${FAIL} falharam ===`);
process.exit(FAIL ? 1 : 0);
