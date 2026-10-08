// Fatia 15 (cliente): na sala de treino do Mago o HUD de slots mostra tudo livre.
// Roda da raiz: node tools/test_slots_treino_cliente.js
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
const decl = SRC.match(/^const SLOTS_POR_NIVEL_CLIENT = [\s\S]*?^};/m)[0].replace(/^const /, 'var ');
const code = [decl, fnSource('_slotsMaxParaHeroi'), fnSource('_slotsMenuMagias'), fnSource('renderSlotsMenuMagias')].join('\n');
const ctx = { GS: { gameState: { round: 3 } }, t: (k, p) => k + (p ? JSON.stringify(p) : ''), _labelCirculo: c => c };
new Function('ctx', 'with(ctx){' + code + '\nctx.menu = _slotsMenuMagias; ctx.render = renderSlotsMenuMagias;}')(ctx);

const base = { class_id: 'mage', level: 1, slots_remaining: { primeiro: [5, 5], segundo: [], terceiro: [], quarto: [5, 5, 5] } };
let s = ctx.menu(base);
check('fora da sala: círculo esgotado fica sem livres', s.primeiro.livres === 0 && s.quarto.livres === 0);
check('fora da sala: sem rótulo de treino', !ctx.render(base).includes('slots_treino_livre'));
const treino = { ...base, slots_livres_treino: true, slots_remaining: { primeiro: [], segundo: [], terceiro: [], quarto: [] } };
s = ctx.menu(treino);
check('na sala: todos os círculos acionáveis (inclui o que o nível ainda não libera)', ['primeiro', 'segundo', 'terceiro', 'quarto'].every(c => s[c].livres >= 1 && s[c].treinoLivre));
check('na sala: o painel diz "ilimitados"', ctx.render(treino).includes('ui.magia.slots_treino_livre'));
console.log(`\n${PASS} ok, ${FAIL} falha(s)`);
process.exit(FAIL ? 1 : 0);
