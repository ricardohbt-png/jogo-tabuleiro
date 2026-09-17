// Testes do lado do cliente da Tempestade de Ciclones (game.js / gameState.js),
// sem navegador. Extrai as funções dos arquivos e as roda com stubs.
//
// Roda da raiz:
//     node tools/test_tempestade_cliente.js
'use strict';
const fs = require('fs');
const path = require('path');

const GAME = fs.readFileSync(path.join(__dirname, '..', 'game.js'), 'utf8');
const STATE = fs.readFileSync(path.join(__dirname, '..', 'src', 'gameState.js'), 'utf8');
let PASS = 0, FAIL = 0;
function check(name, cond){ if(cond){ PASS++; console.log('  ✅ ' + name); } else { FAIL++; console.log('  ❌ ' + name); } }

function fnSource(src, name){
  const i = src.indexOf('function ' + name + '(');
  if(i < 0) throw new Error('função não encontrada: ' + name);
  let d = 0;
  for(let k = src.indexOf('{', i); k < src.length; k++){
    if(src[k] === '{') d++;
    else if(src[k] === '}'){ d--; if(!d) return src.slice(i, k + 1); }
  }
  throw new Error('chaves desbalanceadas em ' + name);
}
function declSource(src, name){
  const m = src.match(new RegExp('^(?:const|let) ' + name + ' = [\\s\\S]*?;[ \\t]*$', 'm'));
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

const TILES = [[2,1],[3,1],[4,1],[2,2],[3,2],[4,2],[2,3],[3,3],[4,3]];
const CICLONES = [{id:1,pos:[2,1],lado:1},{id:2,pos:[4,3],lado:1},{id:3,pos:[3,2],lado:1}];

function montarModuloTempestade(extraCtx = {}){
  const names = ['_tempestadeAnims', '_tempestadeRaf', 'TEMPESTADE_CONCENTRACAO_MS', 'TEMPESTADE_FORMACAO_MS',
    'TEMPESTADE_MOVIMENTO_MS', 'TEMPESTADE_IMPACTO_MS', 'TEMPESTADE_RELAMPAGO_MS'];
  const fns = ['_tempestadeClamp', '_tempestadeHash', '_tempestadeTiles', '_tempestadeVisible', '_tempestadeAnimFromMessage',
    '_tempestadeAtualizarCiclones', '_tempestadeSincronizarCiclonesEstado', '_tempestadeSyncFromState',
    '_tempestadeReconciliarAlvosPresos', '_tempestadeProgress', '_tempestadeCyclonePosition', '_tempestadeCycloneSpinMs',
    '_tempestadeTargetKey', '_tempestadeEntity', '_tempestadeTargetPos', '_tempestadeCicloneContem',
    '_tempestadeEntidadeTilesEstado', '_tempestadeAlvoCicloneContem', '_tempestadeSyncTargetSpins', '_tempestadeBuildBolt',
    '_tempestadeBuild3D', '_tempestadeDispose3D', '_tempestadeUpdate3D', '_receberAnimacaoTempestade', '_tempestadeTick'];
  const code = [...names.map(n => declSource(GAME, n)), ...fns.map(n => fnSource(GAME, n))].join('\n');
  const g3 = { scene: new Obj(), entityGroup: new Obj() };
  const ctx = {
    window: { THREE }, g3, mode3D: true, GS: { gameState: null, isMaster: () => true, monsterTiles: () => [] },
    _scheduleVisualFrame: () => 1, _cancelVisualFrame: () => {}, _liberarDadosMagia: () => {}, renderMap: () => {},
    _encerrarSelecaoPosicoesTempestade: () => false, _encerrarMovimentoTempestade: () => false,
    toast: () => {}, t: k => k, ...extraCtx,
  };
  const keys = Object.keys(ctx);
  const api = new Function(...keys, code + '\nreturn {anims:_tempestadeAnims, receber:_receberAnimacaoTempestade, sync:_tempestadeSyncFromState, update3D:_tempestadeUpdate3D, get raf(){return _tempestadeRaf;}};')(...keys.map(k => ctx[k]));
  return { api, ctx };
}

// As seções [1] e [2] exercitam funções da reconciliação de ciclones
// (`_tempestadeSincronizarCiclonesEstado` etc.). Num checkout que ainda não
// as tem, elas são puladas com aviso — não é falha, é ausência da feature.
const TEM_RECONCILIACAO = GAME.includes('function _tempestadeSincronizarCiclonesEstado(');
if(!TEM_RECONCILIACAO) console.log('\n[1]/[2] pulados: este checkout não tem a reconciliação de ciclones (WIP).');

console.log('\n[1] A animação da conjuração sobrevive ao game_state com a zona PENDENTE');
if(TEM_RECONCILIACAO){
  // `_tempestadeSyncFromState` só punha em `ativos` zonas já confirmadas; a
  // anim do `start` (id da zona pendente) ganhava endingAt no primeiro render
  // — a carga+viagem sumiam num fade antes de a rocha, digo, o vento chegar.
  const { api } = montarModuloTempestade();
  api.receber({ spell_id:'tempestade_ciclones', phase:'start', animation_id:'z1', caster_id:'c',
    origin:[1,3], center:[3,2], tiles:TILES, side:3, charge_ms:900, travel_ms:800, ciclones:[], placement_required:3 });
  const anim = api.anims.find(a => a.animationId === 'z1');
  api.sync({ zonas_especiais: [{ id:'z1', tipo:'tempestade_ciclones', ativa:true, caster:'c', cx:3, cy:2, lado:3,
    tiles:TILES, ciclones:[], ciclones_pendentes:3, ciclones_permitidos:TILES, duracao:4 }] });
  check('anim do start continua viva com a zona pendente', anim.endingAt == null);
  check('nenhuma anim "formada" foi criada para a prévia', api.anims.length === 1);
  api.sync({ zonas_especiais: [] });
  check('sem a zona no estado, a anim encerra (cancelamento/expiração)', anim.endingAt != null);
}

console.log('\n[2] Em 3D os funis nascem quando os ciclones chegam depois do start');
if(TEM_RECONCILIACAO){
  // `_tempestadeBuild3D` cria as malhas com os ciclones que a anim tem NA HORA
  // (zero no `start`); o resolve/sync enchiam `anim.ciclones` sem descartar o
  // grupo, e a tempestade ficava sem tornado nenhum em 3D.
  const { api } = montarModuloTempestade();
  api.receber({ spell_id:'tempestade_ciclones', phase:'start', animation_id:'z2', caster_id:'c',
    origin:[1,3], center:[3,2], tiles:TILES, side:3, charge_ms:900, travel_ms:800, ciclones:[] });
  const anim = api.anims.find(a => a.animationId === 'z2');
  api.update3D(anim, performance.now());
  check('start: grupo construído sem ciclones', !!anim.group && anim.cycloneMeshes.length === 0);
  api.receber({ spell_id:'tempestade_ciclones', phase:'resolve', animation_id:'z2', zone_id:'z2', caster_id:'c',
    center:[3,2], tiles:TILES, side:3, ciclones:CICLONES, duration_rounds:4, success:true });
  api.update3D(anim, performance.now() + 50);
  check('resolve: 3 ciclones na anim', anim.ciclones.length === 3);
  check('resolve: 3 funis no 3D', anim.cycloneMeshes.length === 3);
  api.sync({ zonas_especiais: [{ id:'z2', tipo:'tempestade_ciclones', ativa:true, caster:'c', cx:3, cy:2, lado:3,
    tiles:TILES, ciclones:CICLONES, duracao:4 }] });
  api.update3D(anim, performance.now() + 100);
  check('sync com o estado mantém os 3 funis', anim.cycloneMeshes.length === 3);
}

console.log('\n[3] O alcance de movimento do cliente cobra o vento da tempestade');
{
  // `terrainMoveCost` (gameState.js) não conhecia `zonas_especiais`: as casas
  // azuis mostravam o dobro do alcance real dentro da tempestade, e para
  // voadores devolvia 1 enquanto o servidor cobra o vento também deles.
  let code = fnSource(STATE, 'terrainMoveCost');
  try { code += '\n' + fnSource(STATE, '_custoVentoTempestade'); } catch(e){ /* ainda não existe: o teste fica vermelho */ }
  const zona = { tipo:'tempestade_ciclones', ativa:true, tiles:TILES };
  function custo(actor, x, y, state){
    const ctx = { _custoElevacao: () => 0, _ponteEm: () => false, alturaDe: a => Number(a.altura) || 0, gameState: state };
    const keys = Object.keys(ctx);
    const fn = new Function(...keys, code + '\nreturn terrainMoveCost;')(...keys.map(k => ctx[k]));
    return fn({ actor, materiais: {}, state }, x, y, 1, 1);
  }
  const state = { zonas_especiais: [zona] };
  check('casa dentro da tempestade custa 2', custo({}, 3, 2, state) === 2);
  check('casa fora da tempestade custa 1', custo({}, 8, 8, state) === 1);
  check('voador dentro da tempestade também paga 2', custo({ voo:true, altura:2 }, 3, 2, state) === 2);
  check('zona pendente (prévia) não impõe vento', custo({}, 3, 2, { zonas_especiais: [{ ...zona, ciclones_pendentes: 3 }] }) === 1);
  check('zona inativa não impõe vento', custo({}, 3, 2, { zonas_especiais: [{ ...zona, ativa:false }] }) === 1);
}

console.log('\n' + '='.repeat(62));
console.log(`  ${PASS} passaram, ${FAIL} falharam`);
console.log('='.repeat(62));
process.exit(FAIL ? 1 : 0);
