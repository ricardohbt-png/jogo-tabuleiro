// node tools/test_item_tooltip_hover.js — relógio virtual para o hover de itens.
'use strict';
const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const source = fs.readFileSync(require('path').join(__dirname, '..', 'game.js'), 'utf8');
assert(source.includes('function _ligarTooltipItem('), 'Falta o hover compartilhado com nome imediato e atraso');
let now = 0, next = 0;
const timers = new Map(), elements = new Map();
class Element {
  constructor(){ this.style = {}; this.events = {}; this.isConnected = true; this.scrollTop = 0; this.dataset = {}; }
  addEventListener(name, cb){ (this.events[name] ||= []).push(cb); }
  fire(name, extra = {}){ for(const cb of this.events[name] || []) cb({target:this, currentTarget:this, ...extra}); }
  contains(el){ return el === this; }
  removeAttribute(name){ delete this[name]; }
  getClientRects(){ return this.isConnected ? [this.getBoundingClientRect()] : []; }
  getBoundingClientRect(){ return {left:100, right:148, top:100, bottom:148, width:240, height:80}; }
  appendChild(el){ elements.set(el.id, el); }
}
const body = new Element();
const document = new Element();
Object.assign(document, {body, createElement:()=>new Element(), getElementById:id=>elements.get(id)});
const ctx = vm.createContext({document, window:Object.assign(new Element(), {innerWidth:800, innerHeight:600}), GS:{CATALOGO_ITENS:{}},
  MutationObserver:class {observe(){} disconnect(){}},
  setTimeout(cb, delay){ const id = ++next; timers.set(id, {cb, at:now+delay}); return id; },
  clearTimeout(id){ timers.delete(id); }
});
vm.runInContext(source.slice(source.indexOf('let _itemTooltipReady'), source.indexOf('function fecharQuadrosFlutuantes')), ctx);
function tick(ms){ const end=now+ms; while(true){ const job=[...timers].filter(([,v])=>v.at<=end).sort((a,b)=>a[1].at-b[1].at)[0]; if(!job) break; now=job[1].at; timers.delete(job[0]); job[1].cb(); } now=end; }
let renders=0;
function wire(name){ const el=new Element(); ctx._ligarTooltipItem(el,name,()=>{ renders++; document.getElementById('item-tooltip').innerHTML='DESCRIÇÃO COMPLETA'; }); return el; }
const a=wire('Espada'), b=wire('Escudo');
a.fire('mouseenter');
const tip=document.getElementById('item-tooltip');
assert.equal(tip.textContent,'Espada');
tick(1999); assert.equal(renders,0);
a.fire('mousemove'); tick(1); assert.equal(renders,1,'Movimentos dentro do item não reiniciam o atraso');
assert.equal(tip.style.pointerEvents,'auto');
a.fire('mouseleave'); tick(100); tip.fire('mouseenter'); tick(400);
assert.equal(tip.style.opacity,'1','É possível atravessar o espaço até a descrição');
let stopped=false;
tip.fire('wheel',{stopPropagation(){stopped=true;}});
assert(stopped,'A rodinha não deve alcançar o mapa atrás');
tip.fire('mouseleave'); tick(350); assert.equal(tip.style.opacity,'0');
a.fire('mouseenter'); tick(1000); b.fire('mouseenter'); tick(1000);
assert.equal(renders,1,'Trocar o item cancela o timer antigo');
tick(1000); assert.equal(renders,2);
ctx.esconderTooltip(); tick(3000); assert.equal(tip.style.opacity,'0');
a.fire('mouseenter'); tick(500); a.fire('mouseleave'); tick(2500);
assert.equal(renders,2,'Sair antes de 2s cancela a descrição');
a.fire('mouseenter'); a.isConnected=false; tick(2000);
assert.equal(renders,2,'Item removido não pode abrir um tooltip atrasado');
// Exercita os quatro caminhos reais: loja/baú, pergaminho, instrumento e bolsa.
Object.assign(ctx, {corBordaPorPreco:()=> '#abc', gerarConteudoTooltip:()=> 'ITEM',
  _tooltipPergaminhoHTML:()=> 'PERGAMINHO', _tooltipInstrumentoHTML:()=> 'INSTRUMENTO'});
for(const name of ['aplicarTooltipAoItemDados','aplicarTooltipPergaminho','aplicarTooltipInstrumento']){
  vm.runInContext(source.match(new RegExp('function '+name+'\\([^]*?\\n}'))[0],ctx);
}
for(const [name, html] of [['aplicarTooltipAoItemDados','ITEM'],['aplicarTooltipPergaminho','PERGAMINHO'],['aplicarTooltipInstrumento','INSTRUMENTO']]){
  ctx.esconderTooltip();
  const el=new Element();
  ctx[name](el,{id:'test',name:'Nome'});
  el.fire('mouseenter'); tick(1999); assert.equal(tip.textContent,'Nome');
  tick(1); assert.equal(tip.innerHTML,html);
  const position=[tip.style.left,tip.style.top];
  document.fire('mousemove',{target:el,clientX:600,clientY:500});
  assert.deepEqual([tip.style.left,tip.style.top],position,'A descrição permanece fixa');
}
const inventory=fs.readFileSync(require('path').join(__dirname,'..','src/ui/inventoryModal.js'),'utf8');
ctx._itemDisplayName=item=>item.name;
ctx._showInventoryTooltip=()=>{ tip.innerHTML='INVENTÁRIO'; };
vm.runInContext(inventory.match(/function _wireTooltip\([^]*?\n  }/)[0],ctx);
ctx.esconderTooltip();
const bag=new Element(); ctx._wireTooltip(bag,'test',null,{name:'Bolsa'});
bag.fire('focus'); tick(2000); assert.equal(tip.innerHTML,'INVENTÁRIO');
document.fire('keydown',{key:'Escape'}); assert.equal(tip.style.opacity,'0');
bag.fire('touchstart',{touches:[{clientX:50,clientY:50}]});
tick(350); assert.equal(tip.innerHTML,'INVENTÁRIO');
bag.fire('touchend'); assert.equal(tip.style.opacity,'0');
console.log('OK: nome imediato, 2s, movimento tolerado, troca/cancelamento, travessia e rodinha isolada.');
console.log('OK: handlers reais de loja, pergaminho, instrumento, inventário, teclado e toque.');
