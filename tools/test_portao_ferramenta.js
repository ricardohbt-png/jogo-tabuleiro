'use strict';
const assert = require('assert'), fs = require('fs');
const src = fs.readFileSync('tools/editor.js','utf8');
function extract(name){
  const start=src.indexOf('  function '+name+'('); assert(start>=0,'função ausente: '+name);
  let depth=0; for(let i=src.indexOf('{',start);i<src.length;i++){
    if(src[i]==='{') depth++; else if(src[i]==='}' && --depth===0) return src.slice(start,i+1);
  }
}
const S={grid:{w:5,h:5},tiles:Array.from({length:5},()=>Array(5).fill(0)),rooms:[],doorConditions:{},doorStyles:{},portcullisGroups:{},doorRotations:{}};
const make=new Function('S','DOOR','portcullisGroupAt','roomBorderTouches','doorBaseAngle','setPortcullisSpan','doorLink',
  extract('portcullisPlacementCells')+'\n'+extract('placePortcullis')+';return placePortcullis;');
let saved;
const place=make(S,2,()=>null,()=>false,()=>Math.PI/2,c=>{saved=c;return true;},()=>{});
assert(place(1,1,3,'horizontal'));
assert.deepStrictEqual(saved,[[1,1],[2,1],[3,1]]);
assert.deepStrictEqual(S.tiles[1],[0,2,2,2,0]);
assert.strictEqual(S.doorRotations['1,1'],3);
const before=JSON.stringify(S);
assert.strictEqual(place(4,3,3,'horizontal'),false);
assert.strictEqual(JSON.stringify(S),before,'falha não altera o mapa');
assert(place(0,1,3,'vertical'));
assert.deepStrictEqual(saved,[[0,1],[0,2],[0,3]]);
assert.strictEqual(S.doorRotations['0,1'],0);
const stateBeforeFailure=JSON.stringify(S);
const reject=make(S,2,()=>null,()=>false,()=>0,()=>false,()=>{});
assert.strictEqual(reject(3,3,2,'horizontal'),false);
assert.strictEqual(JSON.stringify(S),stateBeforeFailure,'falha de agrupamento reverte a edição');
const actualState={grid:{w:8,h:8},tiles:Array.from({length:8},()=>Array(8).fill(0)),rooms:[],doorConditions:{},doorStyles:{},portcullisGroups:{},doorRotations:{},materiais:{},alturasParede:{}};
const names=['doorKey','portcullisGroupAt','removePortcullisGroup','doorOwnersAt','doorFinalQuarter','validPortcullisSpan','setPortcullisSpan','doorRotationAt','doorBaseAngle','roomBorderTouches','doorLink','portcullisPlacementCells','placePortcullis'];
const actual = new Function('S','DOOR','WALL','matCompat',names.map(extract).join('\n')+';return {placePortcullis,validPortcullisSpan};')(actualState,2,0,()=>true);
assert(actual.placePortcullis(2,2,3,'horizontal'));
assert.deepStrictEqual(actualState.portcullisGroups['2,2'],[[2,2],[3,2],[4,2]]);
assert(actual.validPortcullisSpan(actualState.portcullisGroups['2,2']));
assert(actual.placePortcullis(6,2,3,'vertical'));
assert.deepStrictEqual(actualState.portcullisGroups['6,2'],[[6,2],[6,3],[6,4]]);
assert(actual.validPortcullisSpan(actualState.portcullisGroups['6,2']));
const intact=JSON.stringify(actualState);
assert.strictEqual(actual.placePortcullis(3,2,2,'horizontal'),false);
assert.strictEqual(JSON.stringify(actualState),intact,'sobreposição não apaga o portão existente');
console.log('OK: posicionamento, largura, orientação e limites');
