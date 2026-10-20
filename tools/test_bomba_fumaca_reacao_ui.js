const assert = require('assert/strict');
const fs = require('fs');
const vm = require('vm');
const code = fs.readFileSync(require('path').join(__dirname,'../game.js'),'utf8');
const start = code.indexOf('// SMOKE REACTION UI');
const end = code.indexOf('// END SMOKE REACTION UI',start);
assert.ok(start >= 0 && end > start,'reaction UI implementation exists');
class Element {
  constructor(tag){this.tagName=tag;this.children=[];this.style={};this.attrs={};this.isConnected=true;this.disabled=false;}
  setAttribute(k,v){this.attrs[k]=v;}
  appendChild(n){n.parent=this;this.children.push(n);return n;}
  append(...nodes){nodes.forEach(n=>this.appendChild(n));}
  remove(){this.isConnected=false;if(this.parent)this.parent.children=this.parent.children.filter(x=>x!==this);}
  focus(){doc.activeElement=this;}
  querySelectorAll(selector){return this.children.flatMap(n=>[...(selector==='button'&&n.tagName==='button'?[n]:[]),...n.querySelectorAll(selector)]);}
}
const listeners=new Map();
const doc={body:new Element('body'),activeElement:new Element('input'),
  createElement:tag=>new Element(tag),
  addEventListener:(name,fn)=>listeners.set(name,fn),
  removeEventListener:(name,fn)=>{if(listeners.get(name)===fn)listeners.delete(name);}};
const replies=[];let intervalCount=0;
const context={document:doc,Date,Math,GS:{smokeReaction:null,
  responderReacaoFumaca:(...args)=>{replies.push(args);return true;}},
  t:(key,args)=>key+JSON.stringify(args||{}),_gamepadSetUiFocus:()=>{},
  setInterval:()=>++intervalCount,clearInterval:()=>--intervalCount};
vm.createContext(context);vm.runInContext(code.slice(start,end),context);
const offer=id=>({request_id:id,expires_at:Date.now()+12000,
  attacker:{name:'<img onerror=alert(1)>'},target:{name:'Ally'},
  candidates:[{hero_id:'p1',name:'One',item_id:'bomba_fumaca',quantity:1},
    {hero_id:'p2',name:'Two',item_id:'bomba_fumaca',quantity:2},
    {hero_id:'p2',name:'Two',item_id:'bomba_flash',quantity:1}]});
function show(id){const msg=offer(id);context.GS.smokeReaction=msg;context._showSmokeReaction(msg);}
show('r1');
let buttons=doc.body.querySelectorAll('button');
assert.equal(buttons.length,4);
buttons[1].onclick();buttons[1].onclick();
assert.deepEqual(replies[0],['r1','p2',true,'bomba_fumaca']);
assert.equal(replies.length,1,'double click sends once');
show('r2');context._closeSmokeReaction('r1');
assert.equal(doc.body.children.length,1,'old closure cannot close new offer');
listeners.get('keydown')({key:'Escape',preventDefault(){},stopImmediatePropagation(){}});
assert.deepEqual(replies.at(-1),['r2',null,false,'bomba_fumaca']);
context._closeSmokeReaction('r2');
assert.equal(doc.body.children.length,0);
show('rflash');
buttons=doc.body.querySelectorAll('button');
buttons[2].onclick();
assert.deepEqual(replies.at(-1),['rflash','p2',true,'bomba_flash']);
context._closeSmokeReaction('rflash');
assert.equal(doc.body.children.length,0);
assert.equal(listeners.size,0);
assert.equal(intervalCount,0);
console.log('Smoke reaction UI: all assertions passed');
