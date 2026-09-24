// tools/test_chamas_peao.js — node tools/test_chamas_peao.js
// Chamas vivas no peão em chamas (status em_chamas_rodadas): extrai as funções
// REAIS do game.js e roda com stubs (sem THREE nem canvas de verdade).
const fs = require('fs');
const path = require('path');
const GAME = fs.readFileSync(path.join(__dirname, '..', 'game.js'), 'utf8');
let PASS = 0, FAIL = 0;
const check = (n, c) => { if (c) { PASS++; console.log('  ✅ ' + n); } else { FAIL++; console.log('  ❌ ' + n); } };
function extrair(nome) {
  const ini = GAME.indexOf('\nfunction ' + nome + '(');
  if (ini < 0) throw new Error('função não encontrada: ' + nome);
  return GAME.slice(ini, GAME.indexOf('\n}', ini) + 2);
}

console.log('\n[1] Fiação');
check('figura comum usa _makeChamasFx3D (não o 🔥 parado)', /if\(emChamas\)\{ const fx = _makeChamasFx3D\(baseR\);/.test(GAME));
check('criatura orientada usa _makeChamasFx3D', /const fx = _makeChamasFx3D\(0\.45\);/.test(GAME));
check('_makeChamasSprite3D removido', !GAME.includes('function _makeChamasSprite3D('));
check('laço 3D anima as chamas', /_updateFumaca3D\(now\);\s*_updateChamasFx3D\(now\);/.test(GAME));
check('2D: monstro em chamas desenha labaredas', /if\(m\.em_chamas_rodadas > 0\)\s*_desenharChamasPeao2D\(/.test(GAME));
check('2D: herói em chamas desenha labaredas', /if\(p\.em_chamas_rodadas > 0 && !_invisP\)\s*_desenharChamasPeao2D\(/.test(GAME));
check('sprites sem tone mapping e sem mistura aditiva', /depthWrite: false, toneMapped: false \}\)/.test(GAME)
  && !/_makeChamasFx3D[\s\S]{0,2500}AdditiveBlending/.test(GAME));

console.log('\n[2] _updateChamasFx3D anima e solta figuras descartadas');
{
  class V { constructor(x = 0, y = 0, z = 0) { this.x = x; this.y = y; this.z = z; }
    clone() { return new V(this.x, this.y, this.z); } set(x, y, z) { this.x = x; this.y = y; this.z = z; } }
  const sprite = (ud) => ({ userData: ud, position: new V(), scale: { set(x, y) { this.x = x; this.y = y; } }, material: { opacity: 0 } });
  const cena = { parent: null };
  const mkGrp = (parent, criadoEm) => ({ parent, visible: true, userData: { raio: 0.32, criadoEm },
    worldToLocal: v => v,
    children: [sprite({ chama: { w: .3, h: .6, y: .1, x: .1, z: 0, fase: 1 } }),
               sprite({ brasa: { x: 0, z: 0, atraso: 0, deriva: .1, s: 1 } })] });
  const naCena = mkGrp(cena, 0), solto = mkGrp(null, 0), recente = mkGrp(null, 9500);
  const set = new Set([naCena, solto, recente]);
  const f = new Function('g3', '_chamasFx3D', 'CHAMAS_FX',
    extrair('_updateChamasFx3D') + '\nreturn _updateChamasFx3D;')(
    { scene: cena, camera: { position: new V(10, 10, 0) } }, set, { vidaBrasaMs: 1100 });
  f(10000);
  const h1 = naCena.children[0].scale.y, y1 = naCena.children[1].position.y;
  f(10240);
  check('labareda muda de altura com o tempo', naCena.children[0].scale.y !== h1);
  check('brasa sobe', naCena.children[1].position.y !== y1);
  check('anel puxado para o lado da câmera (+x)', naCena.children[0].position.x > 0.1 + 0.3);
  check('figura fora da cena há >1 s é solta', !set.has(solto));
  check('figura recém-criada ainda não é solta', set.has(recente));
}

console.log('\n[3] _desenharChamasPeao2D desenha e agenda o próximo quadro');
{
  let preenchidos = 0, agendou = 0;
  const grad = { addColorStop() {} };
  const ctx = { save() {}, restore() {}, beginPath() {}, moveTo() {}, bezierCurveTo() {}, arc() {},
    fill() { preenchidos++; }, createLinearGradient: () => grad, globalAlpha: 1, fillStyle: '' };
  const f = new Function('_agendarChamas2D', '_CHAMAS_2D_CAMADAS',
    extrair('_desenharChamasPeao2D') + '\nreturn _desenharChamasPeao2D;')(() => agendou++, [[1, 'a', 'b'], [.6, 'a', 'b'], [.3, 'a', 'b']]);
  f(ctx, 100, 100, 50, 1234, 7);
  check('3 labaredas × 3 camadas + 3 brasas', preenchidos === 12);
  check('agenda redesenho enquanto houver fogo', agendou === 1);
}

console.log(`\n=== ${PASS} passaram, ${FAIL} falharam ===`);
process.exit(FAIL ? 1 : 0);
