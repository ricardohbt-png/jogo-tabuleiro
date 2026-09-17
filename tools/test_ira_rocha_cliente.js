// Testes do lado do cliente da Ira da Rocha Ardente (game.js), sem navegador.
// Extrai as funções do arquivo e as executa com stubs mínimos de THREE/GS.
//
// Roda da raiz:
//     node tools/test_ira_rocha_cliente.js
'use strict';
const fs = require('fs');
const path = require('path');

const SRC = fs.readFileSync(path.join(__dirname, '..', 'game.js'), 'utf8');
let PASS = 0, FAIL = 0;
function check(name, cond){ if(cond){ PASS++; console.log('  ✅ ' + name); } else { FAIL++; console.log('  ❌ ' + name); } }

// Corpo de uma função de topo `function nome(...) {...}` (chaves balanceadas).
function fnSource(name){
  const i = SRC.indexOf('function ' + name + '(');
  if(i < 0) throw new Error('função não encontrada: ' + name);
  let d = 0;
  for(let k = SRC.indexOf('{', i); k < SRC.length; k++){
    if(SRC[k] === '{') d++;
    else if(SRC[k] === '}'){ d--; if(!d) return SRC.slice(i, k + 1); }
  }
  throw new Error('chaves desbalanceadas em ' + name);
}
// Uma declaração de módulo (`const X = ...;` / `let X = ...;`, até o `;` que
// fecha a linha — pode ocupar várias), como `var` para ficar visível no eval.
function declSource(name){
  const m = SRC.match(new RegExp('^(?:const|let) ' + name + ' = [\\s\\S]*?;[ \\t]*$', 'm'));
  if(!m) throw new Error('declaração não encontrada: ' + name);
  return m[0].replace(/^(const|let) /, 'var ');
}

// ── Stubs de THREE ─────────────────────────────────────────────────────────
class V { constructor(){ this.x = 0; this.y = 0; this.z = 0; } set(){ return this; } copy(){ return this; } setScalar(){ return this; } }
class Obj {
  constructor(){ this.position = new V(); this.scale = new V(); this.rotation = new V(); this.userData = {}; this.visible = true;
    this.material = { opacity: 0, dispose(){} }; this.geometry = { dispose(){} }; this.children = []; this.parent = null; }
  add(...c){ for(const x of c){ x.parent = this; this.children.push(x); } }
  remove(){}
  traverse(f){ f(this); this.children.forEach(c => c.traverse(f)); }
}
class Mat { constructor(o){ Object.assign(this, o || {}); this.opacity = this.opacity || 0; } dispose(){} }
const THREE = new Proxy({ AdditiveBlending: 1, DoubleSide: 2 }, {
  get: (t, k) => k in t ? t[k]
    : String(k).endsWith('Material') ? Mat
    : k === 'Vector3' ? V
    : k === 'BufferGeometry' ? class { setFromPoints(){ return this; } dispose(){} }
    : Obj,
});

function animStart(){
  return { animationId: 'a', origin: [1, 1], center: [4, 4], tiles: [[3, 3], [4, 4]], flames: [],
    isFlames: false, chargeMs: 760, travelMs: 800, impactMs: 980, start: 0, duration: 3140, seed: 1,
    impactPlayed: false, group: null, orb: null, orbGlow: null, castCore: null, castCoreGlow: null,
    castRings: [], castEmbers: [], trail: [], fissure: [], tileMeshes: [], tileRings: [], crackLines: [], flameColumns: [] };
}

console.log('\n[1] Animação 3D não lança exceção no impacto');
{
  const code = [declSource('IRA_ROCHA_CORES'), declSource('IRA_ROCHA_CROSTA_OPACIDADE'), ...['_iraRochaHash', '_iraRochaProgress', '_iraRochaBuild3D',
    '_iraRochaDispose3D', '_iraRochaUpdate3D'].map(fnSource)].join('\n');
  const g3 = { scene: new Obj() }, window = { THREE };
  const run = new Function('g3', 'window', code + '\nreturn _iraRochaUpdate3D;')(g3, window);
  const anim = animStart();
  let erro = null;
  for(const t of [100, 900, 1561, 2500, 3200]){ try { run(anim, t); } catch(e){ erro = erro || (t + ': ' + e.message); } }
  check('update3D roda da carga ao fim sem ReferenceError' + (erro ? ' (' + erro + ')' : ''), !erro);
  check('anel de impacto foi criado após o impacto', !!(anim.group && anim.group.userData.impactRing));
}

console.log('\n[2] O laço de quadros não fica preso se um tick estourar');
{
  // `_tickIraRocha` guarda o id do quadro em `_iraRochaRaf`; se o tick
  // lança, a linha que zera/renova o id não roda e o laço morre para sempre
  // (a próxima conjuração não anima). O tick precisa sobreviver ao erro.
  const code = [declSource('_iraRochaAnims'), declSource('_iraRochaRaf'),
    fnSource('_iraRochaProgress'), fnSource('_tickIraRocha'), fnSource('_receberAnimacaoIraRocha')].join('\n');
  const agendados = [];
  const ctx = {
    _scheduleVisualFrame: fn => { agendados.push(fn); return agendados.length; },
    _iraRochaUpdate3D: () => { throw new Error('boom'); },
    _iraRochaDispose3D: () => {}, _iraRochaPlayImpactSound: () => {}, _liberarDadosMagia: () => {},
    _cancelarAnimsMagiasTerreno: () => {}, _playCombatCue: () => {}, renderMap3D: () => {}, renderMap: () => {},
    _iraRochaAnimFromMessage: () => animStart(),
    mode3D: true, g3: {}, GS: { gameState: {} },
    console: { error: () => {} },   // o tick registra o erro; aqui só poluiria a saída
  };
  const names = Object.keys(ctx);
  const api = new Function(...names, code + '\nreturn {receber:_receberAnimacaoIraRocha, anims:_iraRochaAnims, tick:_tickIraRocha};')(...names.map(k => ctx[k]));
  api.receber({ spell_id: 'ira_rocha_ardente', phase: 'start', animation_id: 'a' });
  check('a 1ª conjuração agenda um quadro', agendados.length === 1);
  let sobreviveu = true;
  try { agendados[0](2000); } catch(e){ sobreviveu = false; }   // já no impacto → update estoura
  check('o tick sobrevive a um erro do update', sobreviveu);
  check('a animação com defeito é descartada (não estoura a cada quadro)', api.anims.length === 0);
  api.anims.length = 0;
  const antes = agendados.length;
  api.receber({ spell_id: 'ira_rocha_ardente', phase: 'start', animation_id: 'b' });
  check('nova conjuração volta a agendar quadros (raf não ficou preso)', agendados.length > antes);
}

console.log('\n[3] Clique de área exige linha de visão ao centro (só nas magias que o servidor exige)');
{
  const code = declSource('MAGIAS_AREA_EXIGEM_LOS') + '\n' + fnSource('_specAlvoMagia');
  function spec(magiaId, los, extra = {}){
    const ctx = {
      GS: { me: { id: 'c', pos: [0, 0], level: 1 }, gameState: { players: [], monsters: [] },
            hasLineOfSight: () => los, monsterTiles: () => [] },
      t: k => k, _dir8: (dx, dy) => [Math.sign(dx), Math.sign(dy)],
      window: { _modoMagia: { magiaId, alvoTipo: 'tile', ...extra } },
    };
    const names = Object.keys(ctx);
    const fn = new Function(...names, code + '\nreturn _specAlvoMagia;')(...names.map(k => ctx[k]));
    return fn('tile', 3, 3);
  }
  check('Ira com parede no caminho: clique recusado', spec('ira_rocha_ardente', false).ok === false);
  check('Ira com visão livre: clique aceito', spec('ira_rocha_ardente', true).ok === true);
  check('Bola de Fogo com parede: clique recusado', spec('bola_fogo', false).ok === false);
  check('Clarividência (alvoLivre) atravessa parede', spec('clarividencia', false, { alvoLivre: true }).ok === true);
  check('Silêncio (servidor não exige LOS) não é bloqueado', spec('silencio', false).ok === true);
}

console.log('\n[4] Números de dano esperam a onda de lava chegar à casa');
{
  // O game_state com o HP descontado chega junto do `start`; sem portão o
  // número aparecia ~2 s antes da rocha cair (a Bola de Fogo tem o dela).
  let fn = null, erro = null;
  try {
    const code = [declSource('_iraRochaAnims'), fnSource('_iraRochaProgress'), fnSource('_iraRochaFeedbackStartAt')].join('\n');
    const api = new Function(code + '\nreturn {anims:_iraRochaAnims, at:_iraRochaFeedbackStartAt};')();
    fn = api.at;
    const anim = animStart(); anim.start = 1000;
    api.anims.push(anim);
    const dentro = fn({ pos: [4, 4] }), borda = fn({ pos: [3, 3] }), fora = fn({ pos: [9, 9] });
    check('casa da área: número só depois do impacto', dentro != null && dentro >= 1000 + 760 + 800);
    check('casa mais distante do centro libera depois (onda)', borda != null && borda > dentro);
    check('casa fora da área: sem atraso', fora == null);
  } catch(e){ erro = e.message; }
  check('portão _iraRochaFeedbackStartAt existe' + (erro ? ' (' + erro + ')' : ''), !erro && typeof fn === 'function');
  const detect = fnSource('_detectHpChanges');
  check('_detectHpChanges consulta o portão da Ira', /_iraRochaFeedbackStartAt\(entry\)/.test(detect));
}

console.log('\n[5] A crosta cobre a lava até a onda revelar a casa');
{
  // O piso autoritativo já chega como lava; um véu de 0.22 deixava a lava
  // 78% visível desde o 1º quadro e a "onda" não tinha o que revelar.
  const b3 = fnSource('_iraRochaBuild3D'), d2 = fnSource('_iraRochaDraw2D');
  const m3 = b3.match(/opacity:\s*IRA_ROCHA_CROSTA_OPACIDADE/);
  const m2 = d2.match(/IRA_ROCHA_CROSTA_OPACIDADE\s*\*\s*\(1-reveal\)/);
  let val = null;
  try { val = new Function(declSource('IRA_ROCHA_CROSTA_OPACIDADE') + '\nreturn IRA_ROCHA_CROSTA_OPACIDADE;')(); } catch(e){}
  check('3D: crosta usa a constante compartilhada', !!m3);
  check('2D: crosta usa a constante compartilhada', !!m2);
  check('crosta é opaca o bastante para esconder a lava (≥ 0.85)', typeof val === 'number' && val >= 0.85);
}

console.log('\n' + '='.repeat(62));
console.log(`  ${PASS} passaram, ${FAIL} falharam`);
console.log('='.repeat(62));
process.exit(FAIL ? 1 : 0);
