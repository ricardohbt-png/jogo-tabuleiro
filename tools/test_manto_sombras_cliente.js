// Nuvem de sombras do Manto da Escuridão (game.js), sem navegador.
// Extrai as funções reais do arquivo e as executa com stubs mínimos.
//
// Roda da raiz:
//     node tools/test_manto_sombras_cliente.js
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

// ── Ambiente mínimo ────────────────────────────────────────────────────────
let AGORA = 10000;
const performance = { now: () => AGORA };
const GS = { isPreview: false };
let mode3D = false, g3 = null;
const sons = [];
function _tocarSomMantoEscuridao(n){ sons.push(['toca', n.id]); n.sound = { ok: true }; }
function _pararSomMantoEscuridao(n){ if(n.sound) sons.push(['para', n.id]); n.sound = null; }
function _scheduleVisualFrame(){ return 1; }
function _sombraDispose3D(){}
function _tickSombras2D(){}

const nomes = ['SOMBRA_NASCER_MS', 'SOMBRA_SAIR_MS', 'SOMBRA_ANEL_MS', 'SOMBRA_OPACIDADE',
  'SOMBRA_POR_CASA', 'SOMBRA_CORES', '_sombraNuvens', '_sombraBaseline', '_sombra2DRaf'];
// Algumas constantes dividem a linha com outras: declara a linha inteira.
const linhas = new Set();
for(const n of nomes){
  const m = SRC.match(new RegExp('^(?:const|let) [^\\n]*\\b' + n + '\\b[^\\n]*$', 'm'));
  if(!m) throw new Error('declaração não encontrada: ' + n);
  linhas.add(m[0].replace(/^(const|let) /, 'var '));
}
eval([...linhas].join('\n') + '\n' + ['_ehZonaFumaca', '_ehZonaSombra', '_addCheb', '_addQuadrado',
  '_sombraCasasRelativas', '_sombrasSync', '_sombrasAvancar', '_sombraFase', '_sombraNascNovelo',
  '_sombraCentro', '_sombraNoveloEstado', '_sombraReset'].map(fnSource).join('\n')
  + '\nglobalThis.__S = { _ehZonaSombra, _sombraCasasRelativas, _sombrasSync, _sombrasAvancar, _sombraCentro, _sombraReset, _sombraNoveloEstado, _sombraFase, get nuvens(){ return _sombraNuvens; }, setBaseline(v){ _sombraBaseline = v; } };');
const S = globalThis.__S;

const manto = (o = {}) => Object.assign({ id: 'escuridao_h1_3', tipo: 'escuridao', cx: 5, cy: 5, raio: 3,
  area_lado: null, duracao: 3, ativa: true, caster: 'h1', visual_id: 'manto_escuridao_h1_3_5_5',
  seguir_caster: true }, o);
const estado = (zonas, round = 3) => ({ round, zonas_especiais: zonas });

console.log('\n[1] Quais zonas viram nuvem de sombras');
check('o Manto do herói vira sombra', S._ehZonaSombra(manto()));
check('o Manto do monstro (sem visual_id) também', S._ehZonaSombra(manto({ visual_id: null, id: 'escuridao_m7_3' })));
check('a bomba de fumaça NÃO (tem nuvem própria)', !S._ehZonaSombra(manto({ visual_id: 'fumaca_h1_3_5_5' })));
check('outra zona NÃO', !S._ehZonaSombra({ tipo: 'bola_fogo' }));

console.log('\n[2] A nuvem cobre as casas REAIS da zona');
const r3 = S._sombraCasasRelativas(manto());
check('raio 3 → 7×7 = 49 casas', r3.length === 49);
check('centradas no conjurador (−3..+3)', Math.min(...r3.map(c => c[0])) === -3 && Math.max(...r3.map(c => c[0])) === 3);
const cajado = S._sombraCasasRelativas(manto({ area_lado: 8 }));
check('com Cajado Arcano (lado 8) → 64 casas', cajado.length === 64);
check('na âncora assimétrica do realce (−3..+4)', Math.min(...cajado.map(c => c[0])) === -3 && Math.max(...cajado.map(c => c[0])) === 4);

console.log('\n[3] Nascimento: só o Manto novo anima e toca som');
S._sombraReset();
S._sombrasSync(estado([manto({ visual_id: 'manto_escuridao_h1_1_5_5' })]));   // 1º estado: linha de base
let n = [...S.nuvens.values()][0];
check('zona que já existia ao entrar nasce pronta (sem animação)', n.nasceEm < AGORA - 1000);
S._sombrasAvancar(AGORA);
check('e muda (sem som)', sons.length === 0);
S._sombrasSync(estado([manto({ visual_id: 'manto_escuridao_h1_1_5_5' }), manto({ id: 'escuridao_h2_3', visual_id: 'manto_escuridao_h2_3_9_9', cx: 9, cy: 9 })]));
const nova = S.nuvens.get('manto_escuridao_h2_3_9_9');
check('Manto lançado nesta rodada nasce agora', nova && nova.nasceEm === AGORA);
S._sombrasAvancar(AGORA);
check('e toca o som do Manto', sons.some(s => s[0] === 'toca' && s[1] === 'manto_escuridao_h2_3_9_9'));
check('densidade proporcional à área (≥ 1 novelo por casa)', nova.novelos.length >= 49);
check('a 1ª volta passa por todas as casas (borda bate com a zona)',
  r3.every(([ox, oy]) => nova.novelos.slice(0, 49).some(nv => Math.round(nv.dx) === ox && Math.round(nv.dz) === oy)));
S._sombraReset(); S.setBaseline(false);
S._sombrasSync(estado([manto({ visual_id: null, id: 'escuridao_m7_3' })]));
check('Manto do monstro (id escuridao_<m>_<rodada>) também é reconhecido como novo',
  [...S.nuvens.values()][0].nasceEm === AGORA);

console.log('\n[4] Onda do centro para fora');
S._sombraReset(); S.setBaseline(false);
S._sombrasSync(estado([manto()]));
n = [...S.nuvens.values()][0];
const centro = n.novelos.find(nv => nv.dx * nv.dx + nv.dz * nv.dz < 0.5);
const borda = n.novelos.find(nv => Math.max(Math.abs(nv.dx), Math.abs(nv.dz)) > 2.6 && !nv.fio);
check('o centro começa antes da borda', centro.atraso < borda.atraso);

console.log('\n[5] Segue o conjurador, deslizando');
// No jogo a nuvem é desenhada a cada quadro desde que nasce; o 1º desenho
// encaixa o centro (de propósito: ao reaparecer, ela não atravessa o mapa).
let c = S._sombraCentro(n, AGORA);
S._sombrasAvancar(AGORA);   // o som começa no nascimento
S._sombrasSync(estado([manto({ cx: 7 })]));
check('o centro autoritativo acompanha a zona', n.cx === 7);
AGORA += 60; c = S._sombraCentro(n, AGORA);
check('o desenho desliza (ainda entre 5 e 7)', c.x > 5 && c.x < 7 && c.movendo);
AGORA += 2000; c = S._sombraCentro(n, AGORA);
check('e chega', Math.abs(c.x - 7) < 0.01);
S._sombrasSync(estado([manto({ cx: 15 })]));
AGORA += 16; c = S._sombraCentro(n, AGORA);
check('teleporte (salto > 3) não arrasta a nuvem pelo mapa', c.x === 15);

console.log('\n[6] Dissipação');
sons.length = 0;
S._sombrasSync(estado([]));
check('zona sumiu → começa a sair', n.saiEm === AGORA);
check('e o som do Manto para', sons.some(s => s[0] === 'para'));
AGORA += 400;
const f = S._sombraFase(n, AGORA);
const st = S._sombraNoveloEstado(n, n.novelos.find(nv => !nv.fio), f, AGORA);
check('a meio caminho a nuvem está mais fraca', st.a < 0.92 && st.a > 0);
AGORA += 2000; S._sombrasAvancar(AGORA);
check('terminada a saída, a nuvem é descartada', S.nuvens.size === 0);

console.log('\n[7] Fiação no game.js');
check('a animação antiga do Manto (anéis/faíscas) saiu', !/_mantoEscuridaoAnims|_mantoEscuridaoBuild3D|_receberAnimacaoMantoEscuridao/.test(SRC));
check('o som do Manto continua', SRC.includes('function _tocarSomMantoEscuridao(') && SRC.includes('function _pararSomMantoEscuridao('));
check('sincroniza junto da fumaça', /_fumacaSync\(state\);\s*\n\s*_sombrasSync\(state\);/.test(SRC));
check('desenha no 2D e atualiza no 3D', SRC.includes('_sombrasDraw2D(ctx, state, _agoraRelampago);') && SRC.includes('_updateSombras3D(now);'));
check('reset e descarte ao trocar de modo', SRC.includes('_sombraReset();') && SRC.includes('_sombraDispose3D(n);\n') || SRC.includes('for(const n of _sombraNuvens.values()) _sombraDispose3D(n);'));
check('o véu roxo por casa não pinta mais o Manto', SRC.includes("!_ehZonaFumaca(z) && !_ehZonaSombra(z))"));

console.log(`\n${'='.repeat(50)}\n  ${PASS} passaram, ${FAIL} falharam\n${'='.repeat(50)}`);
process.exit(FAIL ? 1 : 0);
