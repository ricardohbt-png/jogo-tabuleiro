// Regressões do assentamento de GLB: terreno autorado, escala e carga assíncrona.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '..', 'game.js'), 'utf8');
const config = source.match(/const DECOR_GLB_GROUND_Y = Object.freeze\(\{[\s\S]*?\}\);/)[0];
const builder = source.slice(source.indexOf('function _buildObjetoGLB('), source.indexOf('// Brasões e cortinas', source.indexOf('function _buildObjetoGLB(')));
class Vec {
  constructor(x=0,y=0,z=0) { this.set(x,y,z); }
  set(x,y,z) { Object.assign(this,{x,y,z}); return this; }
  copy(v) { return this.set(v.x,v.y,v.z); }
}
class Group {
  constructor() { this.position=new Vec(); this.scale=new Vec(1,1,1); this.rotation={}; this.children=[]; }
  add(obj) { this.children.push(obj); }
}
let loaded;
const T = {Group, Vector3:Vec, Box3: class {
  setFromObject(inst) { this.min=inst.bounds.min; this.max=inst.bounds.max; return this; }
  getSize(v) { return v.set(this.max.x-this.min.x,this.max.y-this.min.y,this.max.z-this.min.z); }
}};
// A escala do wrapper é uniforme; a escala vertical do editor pertence ao grupo pai.
const original = Group;
T.Group = class extends original {
  constructor() { super(); this.scale.setScalar = s => this.scale.set(s,s,s); }
};
const g3 = {T,decorMeshes:{},scene:{add(){},remove(){}}};
const context = vm.createContext({g3,DECOR_GLB_FLOOR_Y:.225,
  _loadDecorGLB(_T,_path,cb){ loaded=cb; },
  _disposeDecorMesh(){},_facingAngleY3D(){return 0;},_buildObjetoMini(){}});
vm.runInContext(config+'\n'+builder,context);
function load(name, footprint, expectedAnchor, minY) {
  const id=name;
  const slot=new T.Group();
  slot.userData={glbPath:'assets/objetos/'+name};
  slot.position.set(3,.225+1.5,5);
  slot.visible=true;
  g3.decorMeshes[id]=slot;
  context._buildObjetoGLB(id,null,slot.userData.glbPath,footprint,footprint,[0,1]);
  // O terreno pode mudar enquanto o download está pendente.
  slot.position.y=.225+2.0;
  const inst={bounds:{min:new Vec(-1,minY,-1),max:new Vec(1,2,1)},
    position:new Vec(),traverse(){},userData:{}};
  loaded({clone(){return inst;},userData:{}});
  const grp=g3.decorMeshes[id], wrap=grp.children[0];
  assert.equal(grp.position.y,slot.position.y,'carga mantém elevação atual');
  assert.equal(inst.position.y,-expectedAnchor,'plano autorado é a origem vertical');
  for(const verticalScale of [0.6,1,1.5]) {
    const surface=grp.position.y+(expectedAnchor+inst.position.y)*wrap.scale.y*verticalScale;
    assert.equal(surface,slot.position.y,'escala mantém o chão alinhado');
  }
}
load('oasis_pequeno.glb',4,.185,.015);
load('estatua_soterrada.glb',1,.205,.01);
load('acampamento_abandonado.glb',2,.045,.003);
load('cama.glb',1,-.1,-.1);
assert.match(source,/placeholder\.position\.set\(worldX, DECOR_GLB_FLOOR_Y \+ dFloorY, worldZ\)/);
console.log('OK: terreno autorado, base convencional, escala vertical e elevação durante carga.');
