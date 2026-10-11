/* Exercita a projeção usada pelo aviso de perigo, com stubs das regras já
 * existentes de footprint, linha de visão e ataque básico. */
const fs = require('fs');
const vm = require('vm');
const src = fs.readFileSync('game.js', 'utf8');
const start = src.indexOf('function _monsterThreatAreasClient(');
const end = src.indexOf('\nlet _inspectedMonsterId', start);
if (start < 0 || end < 0) throw new Error('helper de áreas do inspetor não encontrado');

const floor = 1, door = 2;
const context = {
  GS: {
    TILE_FLOOR: floor,
    TILE_DOOR: door,
    monsterTiles: m => {
      const [x,y] = m.pos;
      return m.size === 2 ? [[x,y],[x+1,y],[x,y+1],[x+1,y+1]] : [[x,y]];
    },
    hasLineOfSight: (state, ax, ay, bx, by) => {
      if (ax === bx) {
        for (let y=Math.min(ay,by)+1; y<Math.max(ay,by); y++) if (state.tiles[y]?.[ax] === 0) return false;
      } else if (ay === by) {
        for (let x=Math.min(ax,bx)+1; x<Math.max(ax,bx); x++) if (state.tiles[ay]?.[x] === 0) return false;
      }
      return true;
    },
  },
  _masterMonsterAttackPreviewClient: (state, m) => {
    const zone = new Set(), [mx,my] = m.pos;
    for (let y=0; y<state.tiles.length; y++) for (let x=0; x<state.tiles[0].length; x++) {
      const dist = Math.abs(x-mx)+Math.abs(y-my);
      if (state.tiles[y][x] !== floor && state.tiles[y][x] !== door) continue;
      if (m.attacks[0].range == null ? dist === 1 : dist > 0 && dist <= m.attacks[0].range) zone.add(`${x},${y}`);
    }
    return {zone};
  },
};
vm.runInNewContext(src.slice(start,end) + '\nthis.preview = _monsterThreatAreasClient;', context);

const check = (name, condition) => {
  console.log(`${condition ? '✅' : '❌'} ${name}`);
  if (!condition) process.exitCode = 1;
};
const board = (w=5,h=5) => ({tiles:Array.from({length:h},()=>Array(w).fill(floor)), players:[], monsters:[]});
const monster = (pos=[2,2], movement=1, attack={reach:1}) => ({id:'m1',type:'orc',pos,hp:10,movement,attacks:[attack]});

console.log('[1] movimento alcançável + alcance corpo a corpo');
let state = board();
let zones = context.preview(state, monster());
check('ataque imediato usa o conjunto vermelho', zones.attack.has('2,1') && !zones.move.has('2,1'));
check('ameaça após mover usa o conjunto verde', zones.move.has('0,2') && !zones.attack.has('0,2'));
check('não inventa ameaça além do movimento + alcance', !zones.move.has('0,0'));

console.log('[2] paredes e ocupação limitam o caminho');
state = board(); state.tiles[2][3] = 0;
zones = context.preview(state, monster([2,2],2));
check('parede interrompe a projeção para trás dela', !zones.move.has('4,2'));
state = board(); state.players.push({id:'p1',class_id:'warrior',pos:[3,2],hp:10});
zones = context.preview(state, monster([2,2],2));
check('herói ocupado bloqueia o deslocamento projetado', !zones.move.has('4,2'));

console.log('[3] ataques à distância respeitam linha de visão');
state = board(); state.tiles[2][3] = 0;
zones = context.preview(state, monster([2,2],0,{range:3}));
check('não marca alvo além da parede', !zones.attack.has('4,2'));
check('mantém alvos próximos com linha de visão', zones.attack.has('2,1'));

console.log('[4] footprint grande entra no cálculo de ocupação');
state = board(6,6); state.players.push({id:'p1',class_id:'warrior',pos:[4,3],hp:10});
zones = context.preview(state, {...monster([2,2],2),size:2});
check('bloqueia rota que colidiria com herói', !zones.move.has('5,3'));
