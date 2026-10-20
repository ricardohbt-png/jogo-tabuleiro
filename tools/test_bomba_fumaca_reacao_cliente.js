// node tools/test_bomba_fumaca_reacao_cliente.js
const fs = require('fs');
const assert = require('assert/strict');
const path = require('path');
let socket;
const sent = [];
global.WebSocket = class {
  constructor(){ this.readyState = 1; socket = this; }
  send(raw){ sent.push(JSON.parse(raw)); }
  close(){}
};
global.localStorage = {getItem:()=>null,setItem(){},removeItem(){}};
global.location = {search:'',protocol:'http:',host:'test'};
global.window = {};
global.setTimeout = ()=>0;
global.clearTimeout = ()=>{};
const GS = eval(fs.readFileSync(path.join(__dirname,'../src/gameState.js'),'utf8')+';GS');
GS.connect('ws://test','Ana','create');
assert.equal(GS.CATALOGO_ITENS.bomba_flash.alcance,5);
assert.equal(GS.CATALOGO_ITENS.bomba_flash.alvo,'ataque_alvo');
assert.equal(GS.CATALOGO_ITENS.bomba_flash.icon,'assets/itens/bomba_flash.png');
const receive = msg => socket.onmessage({data:JSON.stringify(msg)});
receive({type:'lobby_state',code:'TEST',host:'h1',players:[
  {id:'h1',name:'Ana',class_id:'warrior'},
  {id:'h2',name:'Bia',class_id:'mage',controlador:'h1'}]});
const offer = id => ({type:'smoke_reaction_prompt',request_id:id,expires_at:Date.now()+12000,
  attacker:{id:'m1',name:'Goblin',pos:[3,3]},target:{id:'h1',name:'Ana',pos:[2,3]},
  candidates:[{hero_id:'h1',name:'Ana',item_id:'bomba_fumaca',quantity:1},
    {hero_id:'h1',name:'Ana',item_id:'bomba_flash',quantity:2},
    {hero_id:'h2',name:'Bia',item_id:'bomba_fumaca',quantity:2}]});
assert.equal(typeof GS.responderReacaoFumaca,'function','smoke reaction sender exists');
receive(offer('r1'));
assert.equal(GS.smokeReaction.candidates.length,3);
assert.equal(GS.myPid,'h1','offer does not steal focus');
assert.equal(GS.responderReacaoFumaca('r1','h2',true),true);
assert.equal(sent.at(-1).heroi,'h2','explicit extra overrides focus');
assert.equal(sent.at(-1).item_id,'bomba_fumaca');
assert.equal(GS.responderReacaoFumaca('r1','h1',true,'bomba_flash'),true);
assert.equal(sent.at(-1).item_id,'bomba_flash','reaction chooses the exact throwable');
assert.equal(GS.responderReacaoFumaca('old','h1',true),false);
receive(offer('r2'));
receive({type:'smoke_reaction_closed',request_id:'r1'});
assert.equal(GS.smokeReaction.request_id,'r2','old closure preserves new offer');
GS.responderReacaoFumaca('r2',null,false);
assert.equal(sent.at(-1).heroi,null,'decline is connection-wide');
receive({type:'smoke_reaction_closed',request_id:'r2'});
assert.equal(GS.smokeReaction,null);
receive(offer('r3'));
receive({type:'enter_dungeon'});
assert.equal(GS.smokeReaction,null,'map transition clears pending offer');
receive(offer('r4'));
socket.onclose();
assert.equal(GS.smokeReaction,null,'disconnect clears pending offer');
console.log('Smoke reaction client state: all assertions passed');
