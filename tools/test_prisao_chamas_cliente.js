// Testes do lado do cliente da Prisão de Chamas (game.js), sem navegador.
//
// Roda da raiz:
//     node tools/test_prisao_chamas_cliente.js
'use strict';
const fs = require('fs');
const path = require('path');

const SRC = fs.readFileSync(path.join(__dirname, '..', 'game.js'), 'utf8');
let PASS = 0, FAIL = 0;
function check(name, cond){ if(cond){ PASS++; console.log('  ✅ ' + name); } else { FAIL++; console.log('  ❌ ' + name); } }

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
function declSource(name){
  const m = SRC.match(new RegExp('^(?:const|let) ' + name + ' = [\\s\\S]*?;[ \\t]*$', 'm'));
  if(!m) throw new Error('declaração não encontrada: ' + name);
  return m[0].replace(/^(const|let) /, 'var ');
}
function tryFn(name){ try { return fnSource(name); } catch(e){ return null; } }

const FLAMES = [[3,3],[4,3],[5,3],[3,4],[5,4],[3,5],[4,5],[5,5]];   // borda 3x3 em (4,4)

console.log('\n[1] As chamas persistentes da zona só acendem quando o projétil chega');
{
  // A zona chega no game_state junto do `start`; o portão antigo
  // (`_bolaFogoZonaLiberada`) só olhava as anims da Bola de Fogo e liberava a
  // Prisão na hora — a parede de fogo já estava acesa com o projétil no ar.
  const gate = tryFn('_zonaFogoLiberada');
  check('existe um portão único por tipo de zona (_zonaFogoLiberada)', !!gate);
  if(gate){
    const code = [declSource('_prisaoChamasAnims'), declSource('_bolaFogoAnims'),
      fnSource('_prisaoChamasProgress'), fnSource('_bolaFogoProgress'), fnSource('_bolaFogoZonaLiberada'),
      fnSource('_prisaoChamasZonaLiberada'), gate].join('\n');
    const now = 10000;
    const api = new Function('performance', 'window', code + '\nreturn {gate:_zonaFogoLiberada, prisao:_prisaoChamasAnims};')({ now: () => now }, { _bolaFogoAnims: [] });
    const zona = { tipo:'prisao_chamas', visualId:'pz1', tiles: FLAMES };
    check('sem anim (reconexão): liberada', api.gate(zona) === true);
    api.prisao.push({ animationId:'pz1', start: now - 100, travelMs: 800, impactMs: 980, duration: 2400 });
    check('projétil no ar: NÃO liberada', api.gate(zona) === false);
    api.prisao[0].start = now - 900;
    check('projétil chegou: liberada', api.gate(zona) === true);
    check('Bola de Fogo continua passando pelo portão dela', api.gate({ tipo:'bola_fogo', visualId:'x' }) === true);
  }
  const sites = (SRC.match(/_bolaFogoZonaLiberada\(z\)/g) || []).length;
  const novos = (SRC.match(/_zonaFogoLiberada\(z\)/g) || []).length;
  check('os 3 pontos de render usam o portão único (2D ×2 e 3D)', novos >= 3 && sites === 0);
}

console.log('\n[2] Números de dano esperam o projétil chegar (chamas e calor adjacente)');
{
  const fb = tryFn('_prisaoChamasFeedbackStartAt');
  check('existe _prisaoChamasFeedbackStartAt', !!fb);
  if(fb){
    const code = [declSource('_prisaoChamasAnims'), fb].join('\n');
    const api = new Function(code + '\nreturn {at:_prisaoChamasFeedbackStartAt, anims:_prisaoChamasAnims};')();
    api.anims.push({ animationId:'pz2', start: 1000, travelMs: 800, impactMs: 980, flames: FLAMES, tiles: FLAMES, center:[4,4] });
    check('criatura sobre a chama: espera o impacto', api.at({ pos:[3,3] }) === 1800);
    check('criatura adjacente (calor): espera o impacto', api.at({ pos:[2,2] }) === 1800);
    check('interior da prisão (adjacente à borda): espera o impacto', api.at({ pos:[4,4] }) === 1800);
    check('longe da prisão: sem atraso', api.at({ pos:[9,9] }) == null);
  }
  const detect = fnSource('_detectHpChanges');
  check('_detectHpChanges consulta o portão da Prisão', /_prisaoChamasFeedbackStartAt\(entry\)/.test(detect)
    && /_prisaoChamasFeedbackStartAt\(e\)/.test(detect));
}

console.log('\n' + '='.repeat(62));
console.log(`  ${PASS} passaram, ${FAIL} falharam`);
console.log('='.repeat(62));
process.exit(FAIL ? 1 : 0);
