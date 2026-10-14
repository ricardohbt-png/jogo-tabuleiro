// Reações elementais, lado do cliente: custo de movimento dos materiais novos
// (piche = 2 como lava/areia; lava_solidificada = chão normal) e paleta 2D.
// Roda da raiz: node tools/test_reacoes_cliente.js
'use strict';
const fs = require('fs');
const path = require('path');

const STATE = fs.readFileSync(path.join(__dirname, '..', 'src', 'gameState.js'), 'utf8');
const GAME = fs.readFileSync(path.join(__dirname, '..', 'game.js'), 'utf8');
let PASS = 0, FAIL = 0;
function check(name, cond){ if(cond){ PASS++; console.log('  ✅ ' + name); } else { FAIL++; console.log('  ❌ ' + name); } }

function fnSource(name){
  const i = STATE.indexOf('function ' + name + '(');
  if(i < 0) throw new Error('função não encontrada: ' + name);
  let d = 0;
  for(let k = STATE.indexOf('{', i); k < STATE.length; k++){
    if(STATE[k] === '{') d++;
    else if(STATE[k] === '}'){ d--; if(!d) return STATE.slice(i, k + 1); }
  }
  throw new Error('chaves desbalanceadas em ' + name);
}

// Corredor de uma linha (y=5), x 0..13; material 'mat' de x=2 em diante.
function alcance(mat, mov){
  const code = ['terrainMoveCost', '_custoVentoTempestade', 'bfsReachable', 'findPath', '_entraNaNeve', '_neveJaCobrada', '_ignoraPenalidadePantano']
    .map(n => { try { return fnSource(n); } catch(e){ return ''; } }).join('\n');
  const materiais = {}; for(let x = 2; x < 14; x++) materiais[`${x},5`] = mat;
  const ctx = {
    _custoElevacao: () => 0, _ponteEm: () => false, alturaDe: a => Number(a && a.altura) || 0,
    _walkable: (tiles, x, y) => y === 5 && x >= 0 && x < 14, _occupiedSet: () => new Set(),
    doorSets: () => ({ open: new Set() }), gameState: { materiais, zonas_especiais: [] },
  };
  const keys = Object.keys(ctx);
  const api = new Function(...keys, code + '\nreturn {bfs:bfsReachable};')(...keys.map(k => ctx[k]));
  const explored = new Set(); for(let x = 0; x < 14; x++) explored.add(`${x},5`);
  const out = new Set();
  api.bfs([], explored, 1, 5, mov, out, { materiais, actor: {}, state: ctx.gameState });
  return out;
}

console.log('\n[1] Piche custa 2 por casa (4 de movimento = 2 casas)');
{
  const out = alcance('piche', 4);
  check('(3,5) alcançável — 2ª casa de piche', out.has('3,5'));
  check('(4,5) NÃO alcançável — 3ª casa', !out.has('4,5'));
}
console.log('\n[2] Chão normal e lava solidificada custam 1 (4 casas)');
{
  const chao = alcance('pedra_cinza', 4);
  check('chão normal: (5,5) alcançável', chao.has('5,5') && !chao.has('6,5'));
  const crosta = alcance('lava_solidificada', 4);
  check('lava_solidificada: (5,5) alcançável', crosta.has('5,5') && !crosta.has('6,5'));
}
console.log('\n[3] Paleta 2D do game.js');
check('piche em MAT_PALETTE_2D', /MAT_PALETTE_2D\s*=\s*\{[\s\S]*?\bpiche:\s*\{/.test(GAME));
check('lava_solidificada em MAT_PALETTE_2D', /MAT_PALETTE_2D\s*=\s*\{[\s\S]*?\blava_solidificada:\s*\{/.test(GAME));

const raiz = path.join(__dirname, '..');
global.window = global.window || {};
const RE = eval(fs.readFileSync(path.join(raiz, "src", "reacoesElementais.js"), "utf8") + "; window.ReacoesElementais");
console.log("[4] estilo");
check("choque azul 700ms", RE.estilo("choque").cor === "#7fd4ff" && RE.estilo("choque").duracaoMs === 700);
check("incendio laranja", RE.estilo("incendio").cor === "#ff8a2a");
check("tipo desconhecido -> null", RE.estilo("xxx") === null);
console.log("[5] crosta acabando");
const st = { round: 5, materiais: { "3,3": "lava_solidificada", "4,3": "lava_solidificada", "5,3": "lava" },
             terrenos_temp: { "3,3": 6, "4,3": 8 } };
check("só a crosta com ≤1 rodada restante", JSON.stringify(RE.crostasAcabando(st)) === JSON.stringify([[3, 3]]));
check("estado vazio não quebra", RE.crostasAcabando({}).length === 0 && RE.crostasAcabando(null).length === 0);
console.log("[6] tooltip por material");
check("casa comum -> null", RE.descreverCasa(st, 9, 9) === null);
const st2 = { round: 5, materiais: { "1,1": "piche", "2,1": "agua", "3,1": "lava_solidificada" }, terrenos_temp: { "3,1": 8 } };
check("piche -> chave", RE.descreverCasa(st2, 1, 1).chave === "ui.reacao.casa.piche");
check("água -> chave", RE.descreverCasa(st2, 2, 1).chave === "ui.reacao.casa.agua");
const st3 = { ...st2, zonas_especiais: [{ ativa: true, tipo: "chamas_piche", tiles: [[1, 1]] }] };
check("piche em chamas -> chave própria", RE.descreverCasa(st3, 1, 1).chave === "ui.reacao.casa.piche_chamas");
check("zona inativa não conta", RE.descreverCasa({ ...st2, zonas_especiais: [{ ativa: false, tipo: "chamas_piche", tiles: [[1, 1]] }] }, 1, 1).chave === "ui.reacao.casa.piche");
check("game.js lista chamas_piche nas zonas de fogo persistente", /_atualizarZonasMagia[^]*?z\.tipo === 'chamas_piche'/.test(fs.readFileSync(path.join(raiz, "game.js"), "utf8")));
check("água rasa: conduz e protege", RE.descreverCasa(st2, 2, 1).chave === "ui.reacao.casa.agua");
const stW = { materiais: { "1,1": "agua_profunda", "2,1": "rodamoinho", "3,1": "rodamoinho_profundo", "4,1": "pantano" }, round: 1 };
check("água profunda -> agua_fogo", RE.descreverCasa(stW, 1, 1).chave === "ui.reacao.casa.agua_fogo");
check("redemoinho -> agua_fogo", RE.descreverCasa(stW, 2, 1).chave === "ui.reacao.casa.agua_fogo");
check("redemoinho profundo -> agua_fogo", RE.descreverCasa(stW, 3, 1).chave === "ui.reacao.casa.agua_fogo");
check("pântano -> pantano", RE.descreverCasa(stW, 4, 1).chave === "ui.reacao.casa.pantano");
const c = RE.descreverCasa(st2, 3, 1);
check("crosta -> rodadas restantes", c.chave === "ui.reacao.casa.crosta" && c.params.n === 3);
console.log("[7] fiação");
const jogo2 = fs.readFileSync(path.join(raiz, "game.js"), "utf8");
check("GS trata reacao_elemental", fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8").includes("case 'reacao_elemental'"));
check("game.js ouve reacaoElemental uma vez", (jogo2.match(/GS\.on\('reacaoElemental'/g) || []).length === 1);
check("game.js não duplica GS.on('gameState')", (jogo2.match(/^GS\.on\('gameState'/gm) || []).length === 1);
check("index.html carrega o módulo", fs.readFileSync(path.join(raiz, "index.html"), "utf8").includes("src/reacoesElementais.js"));
const jogoSrc = jogo2.split("\r\n").join("\n");
check("renderMap chama _reacoesDesenhar2D(ctx, state, visionSet)", /_reacoesDesenhar2D\(ctx, state, visionSet\);/.test(jogoSrc));
check("loop 3D chama _reacoes3DAtualizar ao lado de _intencoesAtualizar3D", /_intencoesAtualizar3D\(\);\s*_reacoes3DAtualizar\(\);/.test(jogoSrc));
check("dispose3D chama _reacoes3DDispose", /function dispose3D[^]*?_reacoes3DDispose\(\);/.test(jogoSrc));
check("tooltip da reação só descreve casa visível", /function _reacaoCasaTooltipHTML[^]*?_reacoesVisivel\(_guiaVisao3D\(st\), \[tx, ty\]\)[^]*?descreverCasa/.test(jogoSrc));
const corpo3D = jogoSrc.split("function _reacoes3DAtualizar")[1].split("function _reacaoCasaTooltipHTML")[0];
check("crostas 3D em cache por estado", /function _reacoesCrostas3D[^]*?_reacoesCrostasRef !== st/.test(jogoSrc) && !corpo3D.includes("ReacoesElementais.crostasAcabando"));
check("_reacoes3DDispose zera _reacoesAnims", /function _reacoes3DDispose[^]*?_reacoesAnims\.length = 0/.test(jogoSrc));
const lang = fs.readFileSync(path.join(raiz, "src", "lang", "interface.js"), "utf8").replace(/\r?\n/g, " ");
for (const k of ["ui.reacao.casa.piche", "ui.reacao.casa.piche_chamas", "ui.reacao.casa.agua", "ui.reacao.casa.agua_fogo", "ui.reacao.casa.pantano", "ui.reacao.casa.crosta"])
  check("chave " + k + " pt+en", new RegExp('"' + k.replace(/\./g, "\\.") + '":\\s*\\{[^]{0,200}?"pt"[^]{0,200}?"en"|"' + k.replace(/\./g, "\\.") + '":\\s*\\{[^]{0,200}?"en"[^]{0,200}?"pt"').test(lang));
const _pt = k => { const j = lang.indexOf('"' + k + '"'); const m = /"pt":\s*"([^"]*)"/.exec(lang.slice(j, j + 400)); return m ? m[1] : ""; };
check("pt de agua menciona fogo", /fogo/i.test(_pt("ui.reacao.casa.agua")));
check("pt de pantano menciona fogo", /fogo/i.test(_pt("ui.reacao.casa.pantano")));
const vc = fs.readFileSync(path.join(raiz, "src", "visualConfig.js"), "utf8");
check("VC.materiais tem piche e lava_solidificada", /piche\s*:/.test(vc) && /lava_solidificada\s*:/.test(vc));

console.log('\n' + '='.repeat(62));
console.log(`  ${PASS} passaram, ${FAIL} falharam`);
console.log('='.repeat(62));
process.exit(FAIL ? 1 : 0);
