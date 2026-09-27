// Regressão: o #dice-canvas (camada dos dados, cobre o tabuleiro inteiro) não
// pode capturar o mouse durante uma mira nem depois que os dados somem.
// Bug: após qualquer rolagem ele ficava com pointer-events:auto para sempre; a
// prévia da mira não seguia o cursor e o 1º clique numa casa caía no "clique
// fora" da sessão de mira, cancelando a magia/arremesso.
// Rodar: node tools/test_dados_mira.js
'use strict';
const fs = require('fs');
const path = require('path');
const src = fs.readFileSync(path.join(__dirname, '..', 'game.js'), 'utf8');

let ok = 0, falhas = 0;
function check(cond, msg){ if(cond){ ok++; } else { falhas++; console.log('FALHOU:', msg); } }

function extrair(nome){
  const i = src.indexOf(`function ${nome}(`);
  if(i < 0) throw new Error('função não encontrada: ' + nome);
  // Pula a lista de parâmetros (pode ter `{…}` desestruturado, ex. _aimEnd).
  let p = 0, j = src.indexOf('(', i);
  for(; j < src.length; j++){
    if(src[j] === '(') p++;
    else if(src[j] === ')' && --p === 0) break;
  }
  let d = 0;
  j = src.indexOf('{', j);
  for(; j < src.length; j++){
    if(src[j] === '{') d++;
    else if(src[j] === '}' && --d === 0) break;
  }
  return src.slice(i, j + 1);
}

// [1] comportamento de _setDiceDismissable/_syncDiceDismissable com stubs
const dc = { style:{}, classList:{ c:new Set(), toggle(k, on){ on ? this.c.add(k) : this.c.delete(k); } } };
const ctx = { $: () => dc, _dice2: [], _dice3: [], _mirando: false };
const fn = new Function('ctx', `
  const $ = ctx.$; const _dice2 = ctx._dice2; const _dice3 = ctx._dice3;
  const _aimSessionIs = () => ctx._mirando;
  ${extrair('_setDiceDismissable')}
  ${extrair('_syncDiceDismissable')}
  return { _setDiceDismissable, _syncDiceDismissable };
`)(ctx);

fn._setDiceDismissable(true);
check(dc.style.pointerEvents === 'auto', '[1a] sem mira, dado na tela aceita o clique');
ctx._mirando = true;
fn._setDiceDismissable(true);
check(dc.style.pointerEvents === 'none', '[1b] durante a mira o dice-canvas não captura o mouse');
ctx._mirando = false;
ctx._dice3.push({});
fn._syncDiceDismissable();
check(dc.style.pointerEvents === 'auto', '[1c] fim da mira com dado 3D na tela: volta a aceitar o clique');
ctx._dice3.length = 0;
fn._syncDiceDismissable();
check(dc.style.pointerEvents === 'none', '[1d] sem dado na tela o dice-canvas solta o mouse');

// [2] fiação: os pontos em que os dados somem e a mira começa/termina
check(/_dice3\.splice\(i, 1\);\s*\n\s*if\(!_dice3\.length\) _syncDiceDismissable\(\);/.test(src),
  '[2a] o fade do último dado 3D solta o mouse');
check(/ctx\.clearRect\(0, 0, dc\.width, dc\.height\);\s*\n\s*_syncDiceDismissable\(\);/.test(src),
  '[2b] o fade do último dado 2D solta o mouse');
const aimStart = extrair('_aimStart');
check(/_aimSessionState\.current = session;[\s\S]*_setDiceDismissable\(false\)/.test(aimStart),
  '[2c] _aimStart solta o dice-canvas depois de instalar a sessão');
check(/_syncDiceDismissable\(\)/.test(extrair('_aimEnd')),
  '[2d] _aimEnd devolve o clique aos dados que ainda estejam na tela');

console.log(`${ok} ok, ${falhas} falha(s)`);
process.exit(falhas ? 1 : 0);
