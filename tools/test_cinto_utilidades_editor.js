// Run from root: node tools/test_cinto_utilidades_editor.js
const fs = require('fs'), vm = require('vm'), assert = require('assert');
const {spawnSync} = require('child_process');
const path = require('path');
const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(__dirname, 'editor.js'), 'utf8');
const context = {window: {}, CAT: null, t: x => x, nomeCat: (_, id, name) => name,
  curseCatalog: () => [], opt: () => ''};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname, 'editor_catalog.js'), 'utf8'), context);
context.CAT = context.window.EDITOR_CATALOG;
vm.runInContext(source.slice(source.indexOf('  function editorEscapeText('), source.indexOf('  const CURSE_CATEGORIES')), context);
let pass = 0, fail = 0;
function test(name, fn) { try { fn(); pass++; console.log('PASS ' + name); }
  catch (e) { fail++; console.log('FAIL ' + name + ': ' + e.message); } }
const plain = x => JSON.parse(JSON.stringify(x));
const slot = (id, quantity=1) => ({item: {id}, quantity});
const out = x => plain(context.exportLootItem(x));
// Execute the actual shared expressions used by each import/export pipeline.
const paths = ['c.items.map(exportLootItem)', '(c.items || []).map(exportLootItem)',
  'd.loot.items.map(exportLootItem)', '(d.loot.items || []).map(exportLootItem)'];
for (const expr of paths) assert(source.includes(expr), 'pipeline changed: ' + expr);
function pipeline(expr, entries) {
  context.c = {items: entries}; context.d = {loot: {items: entries}};
  return plain(vm.runInContext(expr, context));
}
for (const [id, capacity] of [['cinto_utilidades', 4], ['cinto_com_bolsos', 2]]) {
  for (const [label, exportPath, importPath] of [['chest', paths[0], paths[1]], ['decor', paths[2], paths[3]]]) {
    test(label + ' legacy ' + id + ' becomes fixed empty pockets', () =>
      assert.deepStrictEqual(pipeline(importPath, pipeline(exportPath, [{id}])), [{id, utility_belt_slots: Array(capacity).fill(null)}]));
    test(label + ' preloaded ' + id + ' round trip', () => {
      const pockets = [slot('health_potion', 4), slot('veneno_fungo_acre', 2)];
      if (capacity === 4) pockets.push(slot('granada', 3), null);
      const belt = {id, utility_belt_slots: pockets};
      assert.deepStrictEqual(pipeline(importPath, pipeline(exportPath, [belt])), [belt]);
    });
  }
  test(id + ' model controls have exact positions and shared image', () => {
    const html = context.lootItemRowHTML({id}, 0, 'remove');
    assert.strictEqual((html.match(/data-belt-item\b/g) || []).length, capacity);
    assert.strictEqual((html.match(/data-belt-quantity\b/g) || []).length, capacity);
    const image = html.match(/<img src="([^"]+)"/)[1];
    assert.strictEqual(new URL(image, 'https://example.test/tools/editor.html').pathname, '/assets/itens/cinto_e_bolsos.png');
    assert(!html.includes('value="flechas"')); assert(!html.includes('value="carta"'));
  });
}
for (const entry of [slot('flechas'), slot('carta'), slot('cinto_com_bolsos'), slot('missing'),
  slot(context.CAT.items.find(item=>item.kind==='armor').id),
  slot(context.CAT.items.find(item=>item.die).id),
  slot([]), slot({}), slot('health_potion', 0), slot('health_potion', 5),
  slot('health_potion', true), slot('health_potion', '2'), slot('health_potion', 1.5), {quantity:1}]) {
  test('sanitize ' + JSON.stringify(entry), () =>
    assert.deepStrictEqual(out({id:'cinto_com_bolsos', utility_belt_slots:[entry]}).utility_belt_slots, [null,null]));
}
for (const malformed of [null, {}, 'slots', [null], [{item:null,quantity:1}]]) {
  test('malformed pocket container ' + JSON.stringify(malformed), () =>
    assert.deepStrictEqual(out({id:'cinto_com_bolsos', utility_belt_slots:malformed}).utility_belt_slots,[null,null]));
}
test('duplicate IDs clear later stack and excess positions disappear', () =>
  assert.deepStrictEqual(out({id:'cinto_com_bolsos', utility_belt_slots:[slot('health_potion',2),slot('health_potion',3),slot('granada')]}).utility_belt_slots,
    [slot('health_potion',2),null]));
test('authored pocket strips forged consumable fields', () =>
  assert.deepStrictEqual(out({id:'cinto_com_bolsos', utility_belt_slots:[{item:{id:'health_potion',value:999},quantity:2}]}).utility_belt_slots,
    [slot('health_potion',2),null]));
test('ordinary loot serialization unchanged', () => {
  assert.deepStrictEqual(out({id:'health_potion', utility_belt_slots:[slot('granada')],value:999}), {id:'health_potion'});
  assert.deepStrictEqual(out({id:'carta',texto:' hello ',curse_mode:'especifica',curse_id:'maos_tremulas'}),
    {id:'carta',texto:'hello',curse_mode:'especifica',curse_id:'maos_tremulas'});
});
test('pocket edits wire both chest and decor panels', () => {
  assert(source.includes('wireUtilityBeltFields(panel, ref.items, renderPanel)'));
  assert(source.includes('wireUtilityBeltFields(panel, ref.loot.items, renderPanel)'));
});
test('control changes select, change quantity, clear and reject duplicates', () => {
  const entries = [{id:'cinto_com_bolsos'}];
  let rerenders = 0;
  const fields = [{dataset:{i:'0',pocket:'0'},value:'health_potion',hasAttribute:()=>true},
    {dataset:{i:'0',pocket:'0'},value:'4',hasAttribute:()=>false},
    {dataset:{i:'0',pocket:'1'},value:'health_potion',hasAttribute:()=>true}];
  context.wireUtilityBeltFields({querySelectorAll:()=>fields}, entries, ()=>rerenders++);
  fields[0].onchange({target:fields[0]}); fields[1].onchange({target:fields[1]});
  assert.deepStrictEqual(plain(entries[0].utility_belt_slots), [slot('health_potion',4),null]);
  fields[2].onchange({target:fields[2]});
  assert.strictEqual(entries[0].utility_belt_slots[1], null);
  fields[0].value=''; fields[0].onchange({target:fields[0]});
  assert.deepStrictEqual(plain(entries[0].utility_belt_slots), [null,null]);
  assert.strictEqual(rerenders, 4);
});
test('custom supported items retain metadata; unavailable custom items stay excluded', () => {
  context.window.EDITOR_CUSTOM_ITEMS = [
    {id:'test_potion',item_slot:'bag',item_type:'potion',disponibilidade:{baus:true}},
    {id:'test_poison',item_slot:'bag',item_type:'poison',effect:'coat_poison',disponibilidade:{baus:true}},
    {id:'test_unavailable',item_slot:'bag',item_type:'potion',disponibilidade:{baus:false,loot_monstro:false}}];
  const ids = context.utilityBeltConsumables().map(item=>item.id);
  assert(ids.includes('test_potion')); assert(ids.includes('test_poison'));
  assert(!ids.includes('test_unavailable'));
  context.window.EDITOR_CUSTOM_ITEMS = [];
});
test('server hydrates safe authoritative pockets and keeps a single belt entry', () => {
  const code = `import server as S
from copy import deepcopy
for iid,n in [('cinto_utilidades',4),('cinto_com_bolsos',2)]:
    raw={'id':iid,'price':1,'icon':'fake','utility_belt_slots':[{'item':{'id':'health_potion','value':999},'quantity':4}]}
    hydrated=S.hidratar_itens_bau([raw])
    assert len(hydrated)==1
    belt=hydrated[0]
    assert belt['price']==S._DUNGEON_ITEM_CATALOG[iid]['price']
    assert belt['price']==(80 if n==4 else 30)
    assert belt['icon']=='assets/itens/cinto_e_bolsos.png'
    assert len(belt['utility_belt_slots'])==n
    assert belt['utility_belt_slots'][0]['item']==S._DUNGEON_ITEM_CATALOG['health_potion']
    assert belt['utility_belt_slots'][0]['quantity']==4
    armor=next(k for k,v in S._DUNGEON_ITEM_CATALOG.items() if v.get('kind')=='armor')
    weapon=next(k for k,v in S._DUNGEON_ITEM_CATALOG.items() if v.get('die'))
    for bad in [[],{},'missing','flechas','carta',iid,armor,weapon]:
        raw['utility_belt_slots']=[{'item':{'id':bad},'quantity':1}]
        assert S.hidratar_itens_bau([raw])[0]['utility_belt_slots']==[None]*n
    for q in [0,5,True,'2',1.5]:
        raw['utility_belt_slots']=[{'item':{'id':'health_potion'},'quantity':q}]
        assert S.hidratar_itens_bau([raw])[0]['utility_belt_slots']==[None]*n
    raw['utility_belt_slots']=[{'item':{'id':'health_potion'},'quantity':2}]*5
    pockets=S.hidratar_itens_bau([raw])[0]['utility_belt_slots']
    assert pockets[0]['quantity']==2 and pockets[1:]==[None]*(n-1)
    for malformed in [None,{},'slots',[None],[{'item':None,'quantity':1}]]:
        raw['utility_belt_slots']=malformed
        assert S.hidratar_itens_bau([raw])[0]['utility_belt_slots']==[None]*n
assert S.hidratar_itens_bau([{'id':[]},{'id':{}},None])==[]
from tools.test_decor_roundtrip import _defn_base
for iid,n in [('cinto_utilidades',4),('cinto_com_bolsos',2)]:
    for pockets in [None,[{'item':{'id':'health_potion'},'quantity':4}]]:
        belt={'id':iid}
        if pockets is not None: belt['utility_belt_slots']=pockets
        d=_defn_base()
        d['chests']=[{'pos':[2,2],'gold':0,'items':[deepcopy(belt)]}]
        dtype=next(k for k,v in S.DECOR_TYPES.items() if v.get('loot_capaz') and v.get('size')==[1,1])
        d['decorations']=[{'type':dtype,'pos':[5,5],'facing':[0,1],'loot':{'gold':0,'items':[deepcopy(belt)]}}]
        assert S.validar_dungeon(d)[0],S.validar_dungeon(d)
        room=S.GameRoom('BELT_EDITOR')
        room.load_authored_dungeon(d)
        chest=next(iter(room.chests.values()))['items']
        decor=room.decorations[0]['loot']['items']
        assert len(chest)==len(decor)==1 and chest==decor
        assert len(chest[0]['utility_belt_slots'])==n
        assert chest[0]['id']==iid
        for bad in [[],{}]:
            malformed=deepcopy(d)
            malformed['chests'][0]['items'][0]['id']=bad
            assert not S.validar_dungeon(malformed)[0]
            malformed=deepcopy(d)
            malformed['decorations'][0]['loot']['items'][0]['id']=bad
            assert not S.validar_dungeon(malformed)[0]
print('server authored belt assertions passed')
`;
  const result = spawnSync('python', ['-X','utf8','-c',code], {cwd:root, encoding:'utf8'});
  assert.strictEqual(result.status, 0, result.stdout + result.stderr);
  console.log(result.stdout.trim());
});

for (const file of ['strings','editor']) vm.runInContext(fs.readFileSync(path.join(root,'src/lang/'+file+'.js'),'utf8'),context);
vm.runInContext(fs.readFileSync(path.join(root,'src/i18n.js'),'utf8'),context);
context.t=(key,params)=>context.window.I18N.t(key,params);
for(const [lang, pocket, empty, itemLabel, quantity] of [
  ['pt','Bolso 1','Vazio','Item do bolso 1','Quantidade do bolso 1'],
  ['en','Pocket 1','Empty','Pocket 1 item','Pocket 1 quantity']]) {
  test('actual belt editor labels resolve '+lang,()=>{
    context.window.I18N.setLang(lang);
    const html=context.utilityBeltFieldsHTML({id:'cinto_com_bolsos'},0);
    assert(html.includes(pocket));assert(html.includes('>'+empty+'</option>'));
    assert(html.includes('aria-label="'+itemLabel+'"'));assert(html.includes('aria-label="'+quantity+'"'));
  });
}

console.log(`${pass} passed, ${fail} failed`);
if (fail) process.exit(1);
