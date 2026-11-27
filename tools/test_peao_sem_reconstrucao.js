// tools/test_peao_sem_reconstrucao.js — node tools/test_peao_sem_reconstrucao.js
//
// POR QUE ESTE TESTE EXISTE
//   A assinatura que decide se o peão 3D de um herói é RECONSTRUÍDO incluía
//   `isCur` (é a vez dele) e `p.facing` (para onde olha). Passar o turno refazia
//   dois peões (GLB clonado, contornos, materiais) só para ligar o anel dourado,
//   e cada passo que mudava de direção refazia o peão de quem andou. Agora o anel
//   nasce em todo peão de herói e só é mostrado/escondido, e a direção vira um
//   giro da raiz — respeitando as rotações temporárias que também moram ali.
//
// O QUE ELE COBRA
//   • funções reais (_sincronizarPeaoHeroi3D/_girarRaizPeao3D) com stubs
//   • fiação: assinatura sem isCur/facing, anel criado para todo herói, GLB
//     tardio lendo a direção atual, deslize só girando quem gira pela raiz
const fs = require('fs');
const path = require('path');
const raiz = path.join(__dirname, '..');
const GAME = fs.readFileSync(path.join(raiz, 'game.js'), 'utf8').replace(/\r\n/g, '\n');
let PASS = 0, FAIL = 0;
const check = (n, c, extra) => {
  if (c) { PASS++; console.log('  ✅ ' + n); }
  else { FAIL++; console.log('  ❌ ' + n + (extra ? '\n     ' + extra : '')); }
};

const U = require('./js_teste_util');
const RENDER = U.funcao(GAME, 'renderMap3D');
// Trecho do laço de uma entidade: da obterFig dela até a próxima obterFig.
function blocoDoLaco(marco) {
  const i = RENDER.indexOf(marco);
  if (i < 0) throw new Error('laço não encontrado: ' + marco);
  const j = RENDER.indexOf('obterFig(', i + marco.length);
  return RENDER.slice(i, j < 0 ? RENDER.length : j);
}
// Argumentos do JSON.stringify da assinatura do peão (o que decide reconstruir).
function assinatura(bloco) {
  const chamada = U.parenteses(bloco, 0);
  return U.parenteses(chamada, chamada.indexOf('JSON.stringify'));
}
// Assinatura sem a chamada _eixoDirecaoSig(…) (que pode receber a direção de propósito).
function semEixo(sig) {
  const i = sig.indexOf('_eixoDirecaoSig');
  return i < 0 ? sig : sig.slice(0, i) + sig.slice(i + U.parenteses(sig, i).length + '_eixoDirecaoSig'.length);
}

function extrair(nome) {
  const ini = GAME.indexOf('\nfunction ' + nome + '(');
  if (ini < 0) throw new Error('função não encontrada: ' + nome);
  const fim = GAME.indexOf('\n}', ini);
  return GAME.slice(ini, fim + 2);
}
const nomes = ['_facingToRotY', '_girarRaizPeao3D', '_sincronizarPeaoHeroi3D'];
const F = new Function(nomes.map(extrair).join('\n') + '\nreturn {' + nomes.join(',') + '};')();

function fig(extra = {}) {
  return { rotation: { y: 0 }, userData: Object.assign({ turnRing: { visible: false } }, extra) };
}
const LESTE = [1, 0], NORTE = [0, -1];

console.log('\n[1] Anel da vez: liga/desliga sem peça nova');
{
  const f = fig({ giraRaiz: true });
  F._sincronizarPeaoHeroi3D(f, true, null);
  check('vez dele → anel visível e isCurrentFig', f.userData.turnRing.visible === true && f.userData.isCurrentFig === true);
  F._sincronizarPeaoHeroi3D(f, false, null);
  check('vez de outro → anel oculto e isCurrentFig=false', f.userData.turnRing.visible === false && f.userData.isCurrentFig === false);
  const semAnel = { rotation: { y: 0 }, userData: {} };
  F._sincronizarPeaoHeroi3D(semAnel, true, null);
  check('peão sem anel (monstro/legado) não quebra', semAnel.userData.isCurrentFig === true);
  F._sincronizarPeaoHeroi3D(null, true, null);
  check('fig ausente é ignorada', true);
}

console.log('\n[2] Direção: gira a raiz só de quem gira pela raiz');
{
  const f = fig({ giraRaiz: true });
  F._sincronizarPeaoHeroi3D(f, false, LESTE);
  check('GLB de herói olha para Leste', f.rotation.y === F._facingToRotY(LESTE), String(f.rotation.y));
  check('guarda a direção para o GLB que chegar depois', f.userData._facingRotY === F._facingToRotY(LESTE));
  F._sincronizarPeaoHeroi3D(f, false, NORTE);
  check('vira para Norte sem reconstruir', f.rotation.y === F._facingToRotY(NORTE));
  const bb = fig({ giraRaiz: false });
  F._sincronizarPeaoHeroi3D(bb, false, LESTE);
  check('billboard/metamorfoseado: raiz intocada', bb.rotation.y === 0 && bb.userData._facingRotY === undefined);
}

console.log('\n[3] Rotações temporárias recebem a direção na BASE');
{
  const casos = [
    ['giro do ataque', { _spinAttackBaseRotationY: 0 }, '_spinAttackBaseRotationY'],
    ['redemoinho', { _whirlpoolWasSpinning: true, _whirlpoolBaseRotationY: 0 }, '_whirlpoolBaseRotationY'],
    ['tempestade', { _tempestadeWasSpinning: true, _tempestadeBaseRotationY: 0 }, '_tempestadeBaseRotationY'],
    ['pose de combate', { _scenePoseAtiva: true, _sceneBaseRotY: 0 }, '_sceneBaseRotY'],
  ];
  for (const [nome, ud, base] of casos) {
    const f = fig(Object.assign({ giraRaiz: true }, ud));
    f.rotation.y = 1.234;   // valor "no meio do efeito"
    F._sincronizarPeaoHeroi3D(f, false, LESTE);
    check(`${nome}: base atualizada, rotação corrente intocada`,
      f.userData[base] === F._facingToRotY(LESTE) && f.rotation.y === 1.234);
  }
  const sel = fig({ giraRaiz: true });
  sel.rotation.y = 0.5;     // girando devagar por estar selecionado
  F._sincronizarPeaoHeroi3D(sel, false, LESTE, true);
  check('selecionado: não arranca do giro, só guarda a direção',
    sel.rotation.y === 0.5 && sel.userData._facingRotY === F._facingToRotY(LESTE));
}

console.log('\n[4] Fiação no game.js');
{
  const heroi = blocoDoLaco('obterFig(`pl:');
  const sig = assinatura(heroi);
  check('assinatura do peão sem isCur', !/\bisCur\b/.test(sig), sig);
  check('assinatura do herói sem facing (nem metamorfoseado)', !/facing/.test(sig), sig);
  check('metamorfoseado gira dentro do modelo de monstro',
    /if\s*\(\s*formaVisual\s*\)\s*_setMonsterMeshFacing3D\(/.test(heroi));
  check('laço sincroniza anel e direção após obterFig (a prévia da bússola sobrevive)',
    U.chamaAntes(heroi, 'obterFig', '_sincronizarPeaoHeroi3D') && heroi.includes('_facingPreview'));
  const build = U.funcao(GAME, 'build3DFig');
  check('build3DFig cria o anel para todo herói (classId), visível só na vez',
    /if\s*\(\s*isCurrent\s*\|\|\s*classId\s*\)/.test(build) && /ring\.visible\s*=\s*!!isCurrent/.test(build)
    && /userData\.turnRing\s*=\s*ring/.test(build));
  const linhaGira = (heroi.split('\n').find(l => /giraRaiz\s*=/.test(l)) || '');
  check('giraRaiz marcado só para GLB de herói sem metamorfose',
    linhaGira.includes('_GLB_ENABLED_CLASSES') && linhaGira.includes('!formaVisual'), linhaGira);
  check('GLB de herói tardio usa a direção atual da raiz',
    U.funcao(GAME, '_makeCharacterPawn3D').includes('userData._facingRotY'));
  const iStep = RENDER.indexOf('stepFacing &&');
  const deslize = iStep < 0 ? '' : RENDER.slice(iStep, iStep + 600);
  check('deslize (entity_step) gira só quem gira pela raiz',
    deslize.includes('giraRaiz') && U.chamadas(deslize).includes('_girarRaizPeao3D')
    && U.chamadas(deslize).includes('_setMonsterMeshFacing3D'));
}

// ── Monstros e servos ────────────────────────────────────────────────────────
const nomesM = ['_eixoDirecaoSig', '_grupoDirecaoMonstro3D', '_setMonsterMeshFacing3D'];
let glbs = new Set();
const M = new Function('_monsterGLBPath', '_monsterFacingToRotY',
  nomesM.map(extrair).join('\n') + '\nreturn {' + nomesM.join(',') + '};')(
  (img, tipo) => glbs.has(tipo) ? `assets/${tipo}.glb` : null,
  (f) => f[0] === 1 ? 11 : f[0] === -1 ? 22 : f[1] === 1 ? 33 : 44);

function no(ud = {}, filhos = []) {
  const n = { userData: ud, children: [], parent: null, position: { x: 0, z: 0 }, rotation: { y: 0 }, scale: { x: 1 } };
  n.traverse = fn => { fn(n); n.children.forEach(c => c.traverse(fn)); };
  n.add = c => { c.parent = n; n.children.push(c); };
  filhos.forEach(c => n.add(c));
  return n;
}

console.log('\n[5] Criatura orientada (billboard de 2 casas) vira sem peça nova');
{
  const body = no({ _monsterFacingGroup: true, _monsterGLBPath: null });
  const sprite = no(); sprite.scale.x = 1.8;
  const fogo = no();
  const raiz = no({ _monsterFacingSprite: sprite, _fxMeio: [fogo] }, [body]);
  M._setMonsterMeshFacing3D(raiz, [1, 0]);
  check('corpo gira para Leste', body.rotation.y === Math.PI && body.position.x === -0.5);
  check('sprite espelha e vai ao meio das 2 casas', sprite.scale.x < 0 && sprite.position.x === -0.5);
  check('fogo acompanha o meio das 2 casas', fogo.position.x === -0.5 && fogo.position.z === 0);
  M._setMonsterMeshFacing3D(raiz, [0, 1]);
  check('vira para Sul: corpo, sprite e fogo', body.rotation.y === Math.PI / 2
    && sprite.scale.x > 0 && fogo.position.z === -0.5 && fogo.position.x === 0);
  check('direção atual guardada na raiz', JSON.stringify(raiz.userData._facingAtual) === '[0,1]');
}

console.log('\n[6] GLB de monstro: grupo aninhado e GLB que chega depois');
{
  const corpo = no();
  const raiz = no({}, [corpo]);
  M._setMonsterMeshFacing3D(raiz, [1, 0]);
  check('sem GLB ainda: só guarda a direção', JSON.stringify(raiz.userData._facingAtual) === '[1,0]');
  const wrap = no({ _monsterFacingGroup: true, _monsterGLBPath: 'assets/x.glb', _monsterCenteredLength: true });
  corpo.add(wrap);
  M._setMonsterMeshFacing3D(raiz, raiz.userData._facingAtual);   // o que o `montar` faz
  check('GLB aninhado (raiz → corpo → wrap) é alcançado e girado', wrap.rotation.y === 11 && wrap.position.x === -0.5);
  check('referência ao grupo fica em cache', raiz.userData._facingGroupRef === wrap);
  M._setMonsterMeshFacing3D(raiz, [0, -1]);
  check('vira de novo sem peça nova', wrap.rotation.y === 44 && wrap.position.z === 0.5);
  M._setMonsterMeshFacing3D(raiz, null);
  check('direção ausente não mexe em nada', wrap.rotation.y === 44);
}

console.log('\n[7] Só o EIXO do orientado com GLB entra na assinatura');
{
  glbs = new Set(['crocodilo']);
  check('1 casa (não orientado): null', M._eixoDirecaoSig(false, 'goblin', 'goblin', null, [1, 0]) === null);
  check('orientado em billboard: null (gira por inteiro)', M._eixoDirecaoSig(true, 'lagarto', 'lagarto', null, [1, 0]) === null);
  check('orientado com GLB: Leste e Oeste = mesmo eixo',
    M._eixoDirecaoSig(true, 'croc', 'crocodilo', null, [1, 0]) === M._eixoDirecaoSig(true, 'croc', 'crocodilo', null, [-1, 0]));
  check('orientado com GLB: Norte difere de Leste',
    M._eixoDirecaoSig(true, 'croc', 'crocodilo', null, [0, -1]) !== M._eixoDirecaoSig(true, 'croc', 'crocodilo', null, [1, 0]));
  check('model3d do editor conta como GLB', M._eixoDirecaoSig(true, 'x', 'x', 'assets/y.glb', [0, 1]) === 'v');
}

console.log('\n[8] Fiação de monstros e servos no game.js');
{
  const mon = blocoDoLaco('obterFig(`mon:');
  const sigM = assinatura(mon);
  check('assinatura do monstro sem m.facing (só o eixo)',
    sigM.includes('_eixoDirecaoSig(') && !/facing/.test(semEixo(sigM)), sigM);
  check('monstro aplica a direção após obterFig', U.chamaAntes(mon, 'obterFig', '_setMonsterMeshFacing3D'));
  const ani = blocoDoLaco('obterFig(`ani:');
  const sigA = assinatura(ani);
  check('assinatura do servo sem a.facing (só o eixo)',
    sigA.includes('_eixoDirecaoSig(') && !/facing/.test(semEixo(sigA)), sigA);
  check('servo aplica a direção após obterFig', U.chamaAntes(ani, 'obterFig', '_setMonsterMeshFacing3D'));
  const pawnM = U.funcao(GAME, '_makeMonsterPawn3D');
  check('GLB de monstro tardio reaplica a direção atual',
    pawnM.includes('_facingAtual') && U.chamadas(pawnM).includes('_setMonsterMeshFacing3D'));
  const orientado = U.funcao(GAME, '_buildOrientedCreature3D');
  check('sprite orientado que carrega depois usa o espelho atual',
    /scale\.x\s*<\s*0\s*\?\s*-1\s*:\s*1/.test(orientado));
  check('fogo/gelo da criatura orientada registrados em _fxMeio',
    (orientado.match(/_fxMeio\.push\(/g) || []).length >= 2);
}

console.log(`\n=== ${PASS} passaram, ${FAIL} falharam ===`);
process.exit(FAIL ? 1 : 0);
