// Testes da mira cliente da Nota Cortante, sem navegador.
// Roda da raiz: node tools/test_nota_cortante_mira.js
'use strict';
const fs = require('fs');
const path = require('path');

const SRC = fs.readFileSync(path.join(__dirname, '..', 'game.js'), 'utf8');
let PASS = 0, FAIL = 0;
function check(name, cond){
  if(cond){ PASS++; console.log('  ✅ ' + name); }
  else { FAIL++; console.log('  ❌ ' + name); }
}
function fnSource(name){
  const i = SRC.indexOf('function ' + name + '(');
  if(i < 0) throw new Error('função não encontrada: ' + name);
  const signatureEnd = /\)\s*\{/g;
  signatureEnd.lastIndex = i;
  const match = signatureEnd.exec(SRC);
  if(!match) throw new Error('corpo da função não encontrado: ' + name);
  const body = match.index + match[0].lastIndexOf('{');
  let depth = 0;
  for(let k = body; k < SRC.length; k++){
    if(SRC[k] === '{') depth++;
    else if(SRC[k] === '}' && --depth === 0) return SRC.slice(i, k + 1);
  }
  throw new Error('chaves desbalanceadas em ' + name);
}

const tiles = Array.from({length:7}, () => Array(8).fill(1));
const me = {pos:[2,3]};
const GS = {
  me,
  gameState:{tiles, doors:{closed:[]}, decorations:[], pontes:[], materiais:{}},
  doorSets:() => ({closed:new Set()}),
  decorTilesOf:() => [],
};
const window = { _modoDirecaoInstrumento:null, _spellHL:{range:new Set(),area:new Set(),double:new Set()} };
const document = {getElementById:() => null};
const TILE_FLOOR = 1, TILE_DOOR = 2;
let receivedDirection = null, endCount = 0;
const _aimSetHover = () => {};
const _aimSetHoverFromSets = () => {};
const _aimSetStatus = () => {};
const _aimEnd = () => { endCount++; window._modoDirecaoInstrumento = null; };
const _aimSetHighlights = () => {};
const t = key => key;

const code = [
  fnSource('_notaCortantePreviewTiles'),
  fnSource('_clickTileDirecaoInstrumento'),
].join('\n');
const api = new Function('GS','window','document','TILE_FLOOR','TILE_DOOR',
  '_aimSetHover','_aimSetHoverFromSets','_aimSetStatus','_aimEnd','_aimSetHighlights','t',
  code + '\nreturn {_notaCortantePreviewTiles,_clickTileDirecaoInstrumento};')(
    GS,window,document,TILE_FLOOR,TILE_DOOR,_aimSetHover,_aimSetHoverFromSets,
    _aimSetStatus,_aimEnd,_aimSetHighlights,t);

const possibleArea = api._notaCortantePreviewTiles(me, 4);
window._modoDirecaoInstrumento = {
  previewNota:true, alcanceNota:4, possibleArea,
  onEscolher:(dx,dy) => { receivedDirection=[dx,dy]; },
};

console.log('\n[1] Alcance e clique em qualquer ponto da linha');
check('a casa distante da linha está na área possível', possibleArea.has('6,3'));
api._clickTileDirecaoInstrumento(6,3);
check('clicar na casa distante escolhe a direção correta', receivedDirection?.[0]===1 && receivedDirection?.[1]===0);
check('a mira encerra exatamente uma vez ao selecionar', endCount===1);

console.log('\n[2] Prévia vermelha e linha verde');
check('a função de hover mantém a área possível em vermelho e pinta a linha sob o cursor de verde',
  /range:mode\.possibleArea,\s*area:_notaCortantePreviewTiles\(GS\.me,mode\.alcanceNota,dir\)/.test(SRC));
check('os quadrados vermelhos usam a paleta de bloqueio vermelha apenas para Nota Cortante',
  /const rangeFill=window\._modoDirecaoInstrumento\?\.previewNota\s*\? AIM_COLORS\.blocked\.fill\s*: AIM_COLORS\.range\.fill/.test(SRC));
check('o mesmo vermelho e verde é aplicado no renderizador 3D',
  /mat\.color\.setHex\(notaCortanteAim\?AIM_COLORS\.blocked\.hex:AIM_COLORS\.range\.hex\)/.test(SRC)
    && /toggle\(g3\.spellAreaMeshes,\s*hl\.area\)/.test(SRC));

console.log('\n[3] Clique inválido não dispara a habilidade');
receivedDirection = null;
window._modoDirecaoInstrumento = {
  previewNota:true, alcanceNota:4, possibleArea,
  onEscolher:(dx,dy) => { receivedDirection=[dx,dy]; },
};
api._clickTileDirecaoInstrumento(3,2);
check('diagonal não envia direção', receivedDirection===null);
check('a mira continua ativa depois de clique inválido', !!window._modoDirecaoInstrumento);

console.log(`\n${PASS} passaram, ${FAIL} falharam`);
process.exitCode = FAIL ? 1 : 0;
