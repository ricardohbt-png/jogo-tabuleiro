// Testes das opções de encerramento no HUD e no menu de magias, sem navegador.
'use strict';
const fs = require('fs');
const path = require('path');
const SRC = fs.readFileSync(path.join(__dirname, '..', 'game.js'), 'utf8');
let PASS = 0, FAIL = 0;
function check(name, ok){ if(ok){ PASS++; console.log('  ✅ ' + name); } else { FAIL++; console.log('  ❌ ' + name); } }
function fnSource(name){
  const i = SRC.indexOf('function ' + name + '(');
  if(i < 0) throw new Error('função não encontrada: ' + name);
  let d = 0;
  for(let k = SRC.indexOf('{', i); k < SRC.length; k++){
    if(SRC[k] === '{') d++;
    else if(SRC[k] === '}' && --d === 0) return SRC.slice(i, k + 1);
  }
  throw new Error('chaves desbalanceadas em ' + name);
}
function declSource(name){
  const m = SRC.match(new RegExp('^(?:const|let) ' + name + ' = [\\s\\S]*?;[ \\t]*$', 'm'));
  if(!m) throw new Error('declaração não encontrada: ' + name);
  return m[0].replace(/^(const|let) /, 'var ');
}

const state = {round: 3, current_turn: 'c', zonas_especiais: [
  {id:'winter', tipo:'chamado_inverno', caster:'c', ativa:true, expira_em:7},
  {id:'permanent', tipo:'chamado_inverno', caster:'c', ativa:true, permanente:true},
  {id:'water', tipo:'senhor_das_aguas', caster:'c', ativa:true, expira_em:8},
  {id:'lava', tipo:'ira_rocha_ardente', caster:'c', ativa:true, expira_em:6},
  {id:'storm-pending', tipo:'tempestade_ciclones', caster:'c', ativa:true, ciclones_pendentes:2},
  {id:'storm', tipo:'tempestade_ciclones', caster:'c', ativa:true, expira_em:9},
  {id:'fire', tipo:'prisao_chamas', caster:'c', ativa:true, expira_em:10},
  {id:'other', tipo:'senhor_das_aguas', caster:'x', ativa:true, expira_em:8},
]};
const ctx = {
  GS: {gameState:state, myPid:'c', isMyTurn:true},
  t: (key, params={}) => Object.entries(params).reduce((s,[k,v]) => s.replaceAll(`{${k}}`, String(v)), key),
  _esc: value => String(value ?? ''),
};
const code = [declSource('_magiasEncerraveisInfo'), fnSource('_zonasMagicasQuePossoEncerrar'),
  fnSource('_renderAcoesEncerrarMagias')].join('\n');
const api = new Function(...Object.keys(ctx), code + '\nreturn {zonas:_zonasMagicasQuePossoEncerrar, render:_renderAcoesEncerrarMagias};')
  (...Object.values(ctx));
const cleric = {id:'c', class_id:'cleric'};
const clericZones = api.zonas(cleric, state);
check('clérigo vê suas quatro magias temporárias concluídas',
  clericZones.map(z => z.id).join(',') === 'winter,water,lava,storm');
check('Chamado permanente, Tempestade pendente e zona alheia ficam ocultos',
  !clericZones.some(z => ['permanent','storm-pending','other'].includes(z.id)));
check('mago vê apenas a própria Prisão de Chamas',
  api.zonas({id:'c',class_id:'mage'}, state).map(z => z.id).join(',') === 'fire');
check('botões do menu identificam magia e instância exatas',
  api.render(cleric).includes("GS.encerrarMagiaZona('storm')")
  && api.render(cleric).includes('cat.magia.tempestade_ciclones.nome'));
ctx.GS.isMyTurn = false;
state.current_turn = 'other-player';
check('fora do turno não aparecem opções de encerramento', api.zonas(cleric, state).length === 0);
console.log(`\nResultado: ${PASS} passou, ${FAIL} falhou`);
process.exitCode = FAIL ? 1 : 0;
