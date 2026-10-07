// Porta só onde o autor criou. Roda da raiz:
//   node tools/test_porta_so_onde_autor.js
// O buildWallDetails punha arco, pilares e folha de porta de madeira em todo
// corredor de 1 casa de largura ao lado de uma sala — inclusive sem porta
// nenhuma no mapa. Aqui ele roda de verdade (THREE de mentira) num corredor
// estreito e nenhuma casa de chão pode ganhar peça.
const fs = require("fs");
const path = require("path");
const src = fs.readFileSync(path.join(__dirname, "..", "game.js"), "utf8");

let PASS = 0, FAIL = 0;
const check = (n, c) => { if (c) { PASS++; console.log("  ✅ " + n); } else { FAIL++; console.log("  ❌ " + n); } };

function extrair(nome) {
  const i = src.indexOf("function " + nome + "(");
  if (i < 0) throw new Error("não achei " + nome);
  let d = 0, j = src.indexOf("{", i);
  for (; j < src.length; j++) {
    if (src[j] === "{") d++;
    else if (src[j] === "}" && --d === 0) break;
  }
  return src.slice(i, j + 1);
}

class Obj { constructor() { this.position = { set() {} }; this.rotation = {}; this.children = [];
  this.userData = {}; } add(c) { this.children.push(c); } updateMatrixWorld() {} }
const T = {
  Mesh: class extends Obj { constructor(g, m) { super(); this.geometry = g; this.material = m; } },
  Group: Obj,
  BoxGeometry: class { constructor(...a) { this.a = a; } },
  CylinderGeometry: class { constructor(...a) { this.a = a; } },
  MeshStandardMaterial: class { constructor() { this.color = { setRGB() {} }; } },
  Color: class {},
};
const TILE_WALL = 0, TILE_FLOOR = 1, TILE_DOOR = 2;
const TERRENO_ELEVACAO_STEP_3D = 0.24;
const elevacaoTerreno = () => 0;
const matDaCasa = () => null;
const generateTexture = () => ({});
const buildWallDetails = eval("(" + extrair("buildWallDetails") + ")");

// Sala 3x3 à esquerda, corredor de 1 casa (x=4..6, y=2) e sala 3x3 à direita.
const W = 11, H = 5;
const tiles = Array.from({ length: H }, () => Array(W).fill(TILE_WALL));
for (let y = 1; y <= 3; y++) for (let x = 1; x <= 3; x++) tiles[y][x] = TILE_FLOOR;
for (let y = 1; y <= 3; y++) for (let x = 7; x <= 9; x++) tiles[y][x] = TILE_FLOOR;
for (let x = 4; x <= 6; x++) tiles[2][x] = TILE_FLOOR;
const det = buildWallDetails(T, null, { tiles }, {}, 1, 0.1, 2.2) || {};

console.log("\n[1] Corredor estreito sem porta no mapa");
const chaos = Object.keys(det).filter(k => { const [x, y] = k.split(",").map(Number); return tiles[y][x] === TILE_FLOOR; });
const corredor = ["4,2", "5,2", "6,2"];
check("as casas do corredor não ganham arco/porta", corredor.every(k => !det[k]));
const pecas = k => (det[k] || []).filter(m => !(m.geometry && m.geometry.a && m.geometry.a.length === 4)).length;
check("nenhuma casa de chão ganha peça além de coluna de canto",
      chaos.every(k => pecas(k) === 0));
check("as paredes seguem com rodapé", Object.keys(det).some(k => { const [x, y] = k.split(",").map(Number); return tiles[y][x] === TILE_WALL; }));

console.log("\n[2] O enfeite não volta");
const corpo = extrair("buildWallDetails");
check("sem folha de porta de madeira", !/generateTexture\('wood'\)/.test(corpo));
check("sem arco de pedras", !/archR|floorNeighbors/.test(corpo));

console.log(`\n${PASS} ok, ${FAIL} falha(s)`);
process.exit(FAIL ? 1 : 0);
