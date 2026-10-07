'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm');
const root=path.join(__dirname,'..');
const ui=fs.readFileSync(path.join(root,'src/ui/inventoryModal.js'),'utf8');
const state=fs.readFileSync(path.join(root,'src/gameState.js'),'utf8');
const game=fs.readFileSync(path.join(root,'game.js'),'utf8');
let pass=0,fail=0;
function check(n,c){console.log((c?'PASS ':'FAIL ')+n); c?pass++:fail++;}
check('equipped sections only',ui.includes("for(const gearSlot of ['item1', 'item2'])") && ui.includes('player.gear?.[gearSlot]'));
check('fixed capacities 4 and 2',ui.includes('cinto_utilidades:4') && ui.includes('cinto_com_bolsos:2'));
check('brown pocket style and normal hit area',/\.inv-belt-pocket\{[^}]*width:42px;height:42px[^}]*#/.test(ui));
check('compact icon',/\.inv-belt-pocket .*img\{width:65%;height:65%/.test(ui));
check('compact emoji art',/\.inv-belt-pocket .*inv-bagslot-emoji\{font-size:/.test(ui));
check('quantity badge',ui.includes('inv-belt-count') && ui.includes('entry.quantity'));
check('accessible pockets',ui.includes("slot.dataset.inventorySlot = 'belt'") && ui.includes("slot.setAttribute('aria-label'"));
check('move to belt and bag',ui.includes("GS.moveUtilityBeltItem('to_belt', gearSlot, pocketIndex, sel.index)") && ui.includes("GS.moveUtilityBeltItem('to_bag', sel.gearSlot, sel.pocketIndex,"));
check('use source survives ally target',game.includes('id => useItem(itemId, id, sourceInfo)') && game.includes('...GS.itemSourceFields(sourceInfo)'));
check('target and area throw source',game.includes('GS.throwItem(r.itemId, r.targetId, r.targetPos, window._modoThrowItem.sourceInfo)') && game.includes('GS.throwItemArea(r.itemId, r.tx, r.ty, window._modoThrowItem.sourceInfo)'));
check('touch keyboard drag and tooltip',ui.includes('_onBeltSlotClick') && ui.includes('_activateBeltItem') && ui.includes("slot.addEventListener('keydown'") && ui.includes('_wireTooltip(slot, item.id, null, item)'));
const match=state.match(/function moveUtilityBeltItem\([^]*?\n  }/);
if(match){const msgs=[];vm.runInNewContext(match[0]+';moveUtilityBeltItem("to_belt","item2",1,3)',{send:m=>msgs.push(m)});check('exact move payload',JSON.stringify(msgs[0])===JSON.stringify({type:'move_utility_belt_item',direction:'to_belt',gear_slot:'item2',pocket_index:1,bag_index:3}));}
else check('exact move payload',false);
console.log(`${pass} passed, ${fail} failed`);process.exitCode=fail?1:0;
// Exercise the real modal renderer and event handlers in a minimal DOM harness.
class Element {
  constructor(){this.children=[];this.dataset={};this.events={};this.attrs={};this.className='';this.classList={add:(v)=>this.className+=' '+v,remove:()=>{}};}
  appendChild(e){this.children.push(e);return e;}
  setAttribute(k,v){this.attrs[k]=v;}
  addEventListener(k,v){this.events[k]=v;}
  focus(){} click(){this.onclick?.();}
}
const potion={id:'potion',name:'Potion',item_slot:'bag',effect:'heal'};
const oil={id:'oil',name:'Oil',item_slot:'bag',arremessavel:true};
const player={id:'p',alive:true,bag:[potion,{id:'cinto_utilidades'}],gear:{item1:{id:'cinto_utilidades',utility_belt_token:'belt-A',utility_belt_slots:[{item:potion,quantity:4},{item:oil,quantity:2}]},item2:{id:'cinto_com_bolsos'}}};
const sent=[],host=new Element(),doc={addEventListener(){},createElement:()=>new Element(),getElementById:()=>null,querySelector:()=>null,activeElement:null};
const context={document:doc,localStorage:{getItem:()=>null},window:{_iniciarMiraArremesso:(...a)=>sent.push(['throw',...a])},GS:{gameState:{phase:'playing',players:[player]},myPid:'p',isMyTurn:true,CATALOGO_ITENS:{},moveUtilityBeltItem:(...a)=>sent.push(['move',...a])},t:x=>x,_rotulo:x=>x,itemIconHTML:()=>'',performance:{now:()=>1000},requestAnimationFrame:f=>f(),useItem:(...a)=>sent.push(['use',...a])};
vm.createContext(context);
const instrumented=ui.replace('return { open, close, toggle,',`return { testRender:_renderBelts, testSelect:s=>{_selected=s}, testPlayer:()=>{_openPid='p'}, testBag:_attemptMoveToBag, testReadOnly:x=>{_readOnly=x}, testActivate:_activateBeltItem, open, close, toggle,`);
vm.runInContext(instrumented+';this.modal=InventoryModal;',context);const modal=context.modal;modal.testPlayer();
modal.testRender({querySelector:()=>host},player);
check('runtime renders exactly 4/2 only from equipped belts',host.children.length===2&&host.children[0].children[1].children.length===4&&host.children[1].children[1].children.length===2);
const slots=host.children.flatMap(section=>section.children[1].children);
check('runtime count and item tooltip touch handlers',slots[0].innerHTML.includes('>4</span>')&&slots[0].events.touchstart&&slots[0].events.touchend);
const before=JSON.stringify(player);
modal.testSelect({kind:'bag',index:0});slots[2].onclick();
check('runtime bag to belt exact one unit request',JSON.stringify(sent.pop())===JSON.stringify(['move','to_belt','item1',2,0]));
modal.testSelect({kind:'belt',gearSlot:'item1',pocketIndex:0});modal.testBag(5);
check('runtime pocket to compact bag insertion',JSON.stringify(sent.pop())===JSON.stringify(['move','to_bag','item1',0,2]));
modal.testActivate('item1',0);check('runtime use coordinates',JSON.stringify(sent.pop())===JSON.stringify(['use','potion',undefined,{source:'utility_belt',gearSlot:'item1',pocketIndex:0,beltToken:'belt-A'}]));
modal.testActivate('item1',1);const throwRequest=sent.pop();check('runtime custom throwable coordinates',throwRequest?.[3]?.pocketIndex===1 && throwRequest?.[3]?.beltToken==='belt-A');
check('runtime never changes synchronized inventory',JSON.stringify(player)===before);
modal.testReadOnly(true);modal.testActivate('item1',0);check('runtime read-only cannot use',sent.length===0);
const oldHost=new Element();modal.testRender({querySelector:()=>oldHost},{gear:{item1:{id:'cinto_utilidades'}}});check('runtime old empty belt renders four pockets',oldHost.children[0].children[1].children.length===4);
console.log(`Total: ${pass} passed, ${fail} failed`);process.exitCode=fail?1:0;
function extract(source,name){const start=source.indexOf('function '+name+'(');let depth=0;for(let i=source.indexOf('{',start);i<source.length;i++){if(source[i]==='{')depth++;if(source[i]==='}'&&!--depth)return source.slice(start,i+1);if(source[i]!=='}')continue;}throw Error(name);}
// Renderer use must preserve origin across asynchronous ally selection.
const requests=[],beltSource={source:'utility_belt',gearSlot:'item2',pocketIndex:0,beltToken:'belt-A'};
let choose;
const useCtx={GS:{myPid:'p',gameState:{players:[{id:'p',alive:true,pos:[0,0],gear:{item2:{utility_belt_slots:[{item:{id:'cure',effect:'cure_poison'}}]}}},{id:'q',alive:true,pos:[1,0]}]},itemSourceFields:s=>({source:s.source,gear_slot:s.gearSlot,pocket_index:s.pocketIndex,belt_token:s.beltToken})},send:m=>requests.push(m),CURA_STATUS_EFFECTS:['cure_poison'],openTargetModal:(a,b,c,callback)=>choose=callback,t:x=>x};
vm.runInNewContext(extract(game,'useItem')+';useItem("cure",undefined,sourceInfo)',{...useCtx,sourceInfo:beltSource});useCtx.GS.gameState.players[0].gear.item2={utility_belt_token:'belt-B',utility_belt_slots:[{item:{id:'cure',effect:'cure_poison'}}]};choose('q');
check('real renderer ally-target payload',JSON.stringify(requests[0])===JSON.stringify({type:'use_item',item_id:'cure',target_id:'q',source:'utility_belt',gear_slot:'item2',pocket_index:0,belt_token:'belt-A'}));
const routeCtx={window:{_modoThrowItem:{sourceInfo:beltSource}},GS:{resolveTileClick:()=>({type:'throw',itemId:'oil',targetId:'m',targetPos:[1,0]}),throwItem:(...a)=>requests.push(a),throwItemArea:(...a)=>requests.push(a)},_encerrarMiraArremesso:()=>{}};
vm.runInNewContext(extract(game,'_clickTileThrow')+';_clickTileThrow(1,0)',routeCtx);check('real target throw keeps source',JSON.stringify(requests.pop())===JSON.stringify(['oil','m',[1,0],beltSource]));
routeCtx.GS.resolveTileClick=()=>({type:'throw_area',itemId:'oil',tx:2,ty:3});vm.runInNewContext(extract(game,'_clickTileThrow')+';_clickTileThrow(2,3)',routeCtx);check('real area throw keeps source',JSON.stringify(requests.pop())===JSON.stringify(['oil',2,3,beltSource]));
modal.testReadOnly(false);modal.testPlayer();modal.testSelect(null);doc.activeElement={closest:()=>slots[0]};
modal.gamepadConfirmFocused();check('gamepad selects pocket and offers action',modal.gamepadActionOpen());
modal.gamepadCycleAction();modal.gamepadConfirmFocused();check('gamepad cancel preserves pocket without using',!modal.gamepadActionOpen()&&sent.length===0);
modal.gamepadConfirmFocused();check('gamepad confirms pocket use',sent.pop()?.[0]==='use');
console.log(`Final: ${pass} passed, ${fail} failed`);process.exitCode=fail?1:0;

for (const file of ['strings','interface']) vm.runInContext(fs.readFileSync(path.join(root,'src/lang/'+file+'.js'),'utf8'),context);
vm.runInContext(fs.readFileSync(path.join(root,'src/i18n.js'),'utf8'),context);
context.t=(key,params)=>context.window.I18N.t(key,params);
for(const [lang,beltLabel,emptyLabel] of [['pt','Cinto','Bolso 1 vazio'],['en','Belt','Empty pocket 1']]) {
  context.window.I18N.setLang(lang);
  const localized=new Element();modal.testRender({querySelector:()=>localized},{gear:{item1:{id:'cinto_com_bolsos'}}});
  check('actual inventory belt section and empty pocket '+lang, localized.children[0].children[0].textContent.startsWith(beltLabel+' — ') && localized.children[0].children[1].children[0].attrs['aria-label']===emptyLabel);
}
console.log(`Review final: ${pass} passed, ${fail} failed`);process.exitCode=fail?1:0;
