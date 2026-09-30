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
  const iniLaco = GAME.indexOf('const _figInvis = obterFig(`pl:${p.id}`');
  const trecho = GAME.slice(iniLaco, GAME.indexOf('\n', GAME.indexOf('JSON.stringify(', iniLaco) + 1) + 200);
  const sig = trecho.slice(trecho.indexOf('JSON.stringify(['), trecho.indexOf(']),'));
  check('assinatura do peão sem isCur', !/\bisCur\b/.test(sig), sig);
  check('assinatura só leva facing quando metamorfoseado', sig.includes('formaVisual ? p.facing : null')
    && !/,\s*p\.facing\s*,/.test(sig), sig);
  check('laço sincroniza anel e direção após obterFig',
    GAME.includes('_sincronizarPeaoHeroi3D(_figInvis, isCur, p.facing, !!pSel);'));
  check('build3DFig cria o anel para todo herói (classId), visível só na vez',
    /if\(isCurrent \|\| classId\)\{[\s\S]{0,700}ring\.visible = !!isCurrent;[\s\S]{0,80}grp\.userData\.turnRing = ring;/.test(GAME));
  check('giraRaiz marcado só para GLB de herói sem metamorfose',
    GAME.includes('f.userData.giraRaiz = _GLB_ENABLED_CLASSES.has(p.class_id) && !formaVisual;'));
  const montar = GAME.slice(GAME.indexOf('\nfunction _makeCharacterPawn3D('), GAME.indexOf('\nfunction _loadMonsterGLB('));
  check('GLB de herói tardio usa a direção atual da raiz',
    /const montar = tpl => \{[\s\S]{0,400}r\.userData\._facingRotY != null\) rotY = r\.userData\._facingRotY;/.test(montar));
  check('deslize (entity_step) gira só quem gira pela raiz',
    GAME.includes('if(stepFacing && mesh.userData.giraRaiz) _girarRaizPeao3D(mesh, _facingToRotY(stepFacing));')
    && GAME.includes("else if(stepFacing && mesh.userData.pid === undefined) _setMonsterMeshFacing3D(mesh, stepFacing);"));
}

console.log(`\n=== ${PASS} passaram, ${FAIL} falharam ===`);
process.exit(FAIL ? 1 : 0);
