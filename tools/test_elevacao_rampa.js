// Elevação do terreno no 3D — roda da raiz: node tools/test_elevacao_rampa.js
//
// Guarda contra a regressão que apagava o tabuleiro inteiro: a visibilidade das
// rampas (`terrainTransitionMeshes`) foi escrita dentro de
// `_atualizarTerrenoAnimado3D`, que NÃO tem `terrainSet` no escopo — ele é local
// de `renderMap3D`. O bloco só executa quando o autor pinta altura com transição
// "rampa", e a função só chega até ele quando o mapa tem terreno animado
// (água/lava/pântano/rodamoinho). Nessa combinação o `tick()` do 3D lançava
// ReferenceError a cada quadro, ANTES de `renderer.render`, e o tabuleiro sumia
// enquanto o resto da tela (HUD, objetivos, lista de monstros) continuava de pé.
//
// O teste é estático de propósito: o defeito é de ESCOPO, então ele aparece na
// leitura do arquivo, sem precisar de WebGL nem de DOM.
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");

let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); }
                                else { FAIL++; console.log("  ❌ " + name); } };

// Comentário não é código: um `// ver terrainSet em renderMap3D` explicando o
// defeito não pode reabrir o alarme. Removemos só as linhas INTEIRAS de
// comentário e os blocos /* */ — um `//` no meio da linha pode estar dentro de
// uma string (as URLs de CDN do arquivo), e cortar ali esconderia código real.
function semComentarios(texto) {
  return texto
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .split(/\r?\n/)
    .map(linha => (/^\s*\/\//.test(linha) ? "" : linha))
    .join("\n");
}

const src = semComentarios(fs.readFileSync(path.join(raiz, "game.js"), "utf8"));
const linhas = src.split(/\r?\n/);

// Recorta as funções de TOPO (âncora na coluna 0, mesmo idioma do
// tools/test_interface.py): nome -> {ini, fim, corpo}.
function funcoesDeTopo(linhas) {
  const RE_FN = /^(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(/;
  const achadas = [];
  linhas.forEach((linha, i) => {
    const m = RE_FN.exec(linha);
    if (m) achadas.push({ nome: m[1], ini: i });
  });
  const out = new Map();
  achadas.forEach((f, k) => {
    const fim = k + 1 < achadas.length ? achadas[k + 1].ini : linhas.length;
    out.set(f.nome, { ini: f.ini + 1, fim, corpo: linhas.slice(f.ini, fim).join("\n") });
  });
  return out;
}
const FN = funcoesDeTopo(linhas);

console.log("\n[1] O recorte de funções funciona");
check("achou _atualizarTerrenoAnimado3D", FN.has("_atualizarTerrenoAnimado3D"));
check("achou renderMap3D", FN.has("renderMap3D"));
check("achou init3D", FN.has("init3D"));

console.log("\n[2] terrainSet nunca é variável livre");
// Quem cita `terrainSet` precisa declará-lo (let/const/var) ou recebê-lo como
// parâmetro. Sem isso é ReferenceError em tempo de execução — e, dentro do
// laço do 3D, um tabuleiro preto sem nenhuma mensagem óbvia para o autor.
const orfas = [];
for (const [nome, f] of FN) {
  if (!/\bterrainSet\b/.test(f.corpo)) continue;
  const declara = /\b(?:let|const|var)\s+terrainSet\b/.test(f.corpo);
  const parametro = new RegExp(
    `function\\s+${nome.replace(/\$/g, "\\$")}\\s*\\([^)]*\\bterrainSet\\b`).test(f.corpo);
  if (!declara && !parametro) orfas.push(`${nome} (linha ${f.ini})`);
}
check("nenhuma função usa terrainSet sem declarar/receber: "
      + (orfas.join(", ") || "ok"), orfas.length === 0);

console.log("\n[3] A visibilidade da rampa mora onde a névoa é calculada");
const rampaEmAnimacao = /terrainTransitionMeshes/.test(
  FN.get("_atualizarTerrenoAnimado3D")?.corpo || "");
check("_atualizarTerrenoAnimado3D não mexe em terrainTransitionMeshes (é animação, não névoa)",
      rampaEmAnimacao === false);
check("renderMap3D atualiza a visibilidade das rampas",
      /terrainTransitionMeshes/.test(FN.get("renderMap3D")?.corpo || ""));
check("a rampa é revelada pelas casas que ela liga (terrainKeys)",
      /terrainKeys[\s\S]{0,120}terrainSet\.has/.test(FN.get("renderMap3D")?.corpo || ""));

console.log("\n[4] O intervalo de elevação é o mesmo nos quatro arquivos");
// O teto vive em quatro lugares (server, game, gameState, editor). Se o editor
// deixar pintar acima do que validar_dungeon aceita, o autor só descobre ao
// salvar; se um clamp escrito à mão ficar para trás, o valor é silenciosamente
// achatado no meio do caminho — foi assim que os três `min(2, …)` sobreviveram
// ao teto antigo.
function intervalo(arquivo, reMin, reMax) {
  const txt = fs.readFileSync(path.join(raiz, arquivo), "utf8");
  const mn = reMin.exec(txt), mx = reMax.exec(txt);
  return mn && mx ? [Number(mn[1]), Number(mx[1])] : null;
}
const faixas = {
  "server.py": intervalo("server.py",
    /^ELEVACAO_TERRENO_MIN\s*=\s*(-?\d+)/m, /^ELEVACAO_TERRENO_MAX\s*=\s*(-?\d+)/m),
  "game.js": intervalo("game.js",
    /ELEVACAO_TERRENO_MIN\s*=\s*(-?\d+)/, /ELEVACAO_TERRENO_MAX\s*=\s*(-?\d+)/),
  "src/gameState.js": intervalo("src/gameState.js",
    /ELEVACAO_TERRENO_MIN\s*=\s*(-?\d+)/, /ELEVACAO_TERRENO_MAX\s*=\s*(-?\d+)/),
  "tools/editor.js": intervalo("tools/editor.js",
    /ELEVACAO_MIN\s*=\s*(-?\d+)/, /ELEVACAO_MAX\s*=\s*(-?\d+)/),
};
for (const [arq, faixa] of Object.entries(faixas))
  check(`${arq} declara o intervalo`, Array.isArray(faixa));
const ref = faixas["server.py"];
check("o servidor é a referência e chega a 10", ref && ref[0] === -1 && ref[1] === 10);
const fora = Object.entries(faixas)
  .filter(([, f]) => !f || f[0] !== ref[0] || f[1] !== ref[1])
  .map(([a]) => a);
check("os quatro arquivos concordam: " + (fora.join(", ") || "ok"), fora.length === 0);

console.log("\n[5] O acessor de elevação de cada camada usa a constante");
// `max(-1, min(2, …))` dentro do acessor continuava achatando o valor mesmo
// depois de o teto subir. O defeito não vira erro: a altura simplesmente "não
// sobe", e o autor culpa o editor. O clamp genérico `max(a, min(b, …))` é
// idioma comum no projeto, então a checagem olha SÓ estes quatro acessores.
const ACESSORES = [
  ["server.py",        /def _elevacao_terreno\b/],
  ["game.js",          /function elevacaoTerreno\b/],
  ["src/gameState.js", /function _elevacaoTerreno\b/],
  ["tools/editor.js",  /function elevationAt\b/],
];
const cravados = [];
for (const [arq, reFn] of ACESSORES) {
  const ls = semComentarios(fs.readFileSync(path.join(raiz, arq), "utf8")).split(/\r?\n/);
  const i = ls.findIndex(l => reFn.test(l));
  if (i < 0) { cravados.push(`${arq} (acessor não encontrado)`); continue; }
  // A janela para no FECHO do acessor, não num número fixo de linhas: com 10
  // linhas fixas ela vazava para a função seguinte, e o `Math.max(1, Math.min(3,
  // …))` de bridgeTilesOf — clamp legítimo de largura de ponte — era acusado
  // como se fosse o clamp da elevação. Falso positivo em varredura custa caro:
  // manda procurar bug onde não há.
  let fim = i + 1;
  while (fim < ls.length && fim < i + 40 && !/^\s{0,4}\}\s*$/.test(ls[fim])) fim++;
  const corpo = ls.slice(i, fim + 1).join("\n");
  if (/(?:Math\.)?(?:max|min)\(\s*-?\d/.test(corpo)) cravados.push(`${arq}:${i + 1}`);
}
check("nenhum acessor tem número cravado no clamp: " + (cravados.join(", ") || "ok"),
      cravados.length === 0);

console.log("\n[6] init3D continua criando as rampas só no modo 'rampa'");
const corpoInit = FN.get("init3D")?.corpo || "";
check("init3D só monta transição quando transicao_altura === 'rampa'",
      /state\.transicao_altura\s*===\s*'rampa'/.test(corpoInit));
check("cada rampa guarda as duas casas que liga",
      /userData\.terrainKeys\s*=/.test(corpoInit));

// ── Paridade com o servidor: o azul não pode oferecer o que o servidor recusa ──
console.log("\n[7] O BFS do cliente respeita a regra de passo seguro");
global.window = {};
global.localStorage = { getItem: () => null, setItem: () => {} };
global.location = { search: "", protocol: "http:", host: "x" };
const GS = eval(fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8") + "; GS");

const FLOOR = 1, WALL = 0, W = 15, H = 15;

// Dois platôs de altura 3 com um fosso de 2 casas; ponte cruzando.
function cenario({ vertical, largura, vaoParede, transicao = "rampa" }) {
  const tiles = [];
  for (let y = 0; y < H; y++) tiles.push(new Array(W).fill(FLOOR));
  const elevacoes = {};
  const noFosso = (x, y) => vertical ? (y === 6 || y === 7) : (x === 6 || x === 7);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    if (noFosso(x, y)) { elevacoes[`${x},${y}`] = 0; if (vaoParede) tiles[y][x] = WALL; }
    else elevacoes[`${x},${y}`] = 3;
  }
  const inicio = vertical ? [8, 5] : [5, 8];
  const fim    = [8, 8];
  const bt = [];
  if (inicio[1] === fim[1]) {
    const y0 = inicio[1] - Math.floor(largura / 2);
    for (let y = y0; y < y0 + largura; y++)
      for (let x = Math.min(inicio[0], fim[0]); x <= Math.max(inicio[0], fim[0]); x++) bt.push([x, y]);
  } else {
    const x0 = inicio[0] - Math.floor(largura / 2);
    for (let x = x0; x < x0 + largura; x++)
      for (let y = Math.min(inicio[1], fim[1]); y <= Math.max(inicio[1], fim[1]); y++) bt.push([x, y]);
  }
  const explored = [];
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) explored.push([x, y]);
  const hx = vertical ? inicio[0] : inicio[0] - 1;
  const hy = vertical ? inicio[1] - 1 : inicio[1];
  GS.injectPreviewState({
    type: "game_state", master_pid: null,
    players: [{ id: "p1", name: "H", class_id: "warrior", alive: true,
                pos: [hx, hy], altura: 0, moves_left: 12, spd: 12 }],
    monsters: [], tiles, rooms: [], explored, round: 1, current_turn: "p1",
    elevacoes, materiais: {}, decorations: [],
    pontes: [{ id: "b", inicio, fim, largura, altura: 3, tiles: bt }],
    transicao_altura: transicao,
  });
  const st = GS.gameState;
  const res = new Set();
  GS.bfsReachable(st.tiles, new Set(explored.map(([x, y]) => `${x},${y}`)),
    hx, hy, 12, res,
    { materiais: st.materiais, elevacoes: st.elevacoes, state: st, actor: st.players[0] });
  const ox = vertical ? fim[0] : fim[0] + 1;
  const oy = vertical ? fim[1] + 1 : fim[1];
  return { res, bt, outroLado: res.has(`${ox},${oy}`) };
}

// as 12 geometrias atravessam
let atravessam = 0, total = 0;
for (const vertical of [true, false])
  for (const largura of [1, 2, 3])
    for (const vaoParede of [false, true]) {
      total++;
      if (cenario({ vertical, largura, vaoParede }).outroLado) atravessam++;
    }
check(`as ${total} geometrias de ponte atravessam (${atravessam}/${total})`,
      atravessam === total);

// o fosso ao lado da ponte NUNCA entra no alcance
const c = cenario({ vertical: true, largura: 1, vaoParede: false });
check("fosso ao lado da ponte fica fora do alcance",
      !c.res.has("7,6") && !c.res.has("9,6"));

// modo declive: descer 1 nível andando deixa de ser oferecido
const tiles2 = [];
for (let y = 0; y < H; y++) tiles2.push(new Array(W).fill(FLOOR));
const elev2 = {};
for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) elev2[`${x},${y}`] = x < 5 ? 3 : 2;
const explored2 = [];
for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) explored2.push([x, y]);
function alcanceDegrau(transicao) {
  GS.injectPreviewState({
    type: "game_state", master_pid: null,
    players: [{ id: "p1", name: "H", class_id: "warrior", alive: true,
                pos: [4, 5], altura: 0, moves_left: 6, spd: 6 }],
    monsters: [], tiles: tiles2, rooms: [], explored: explored2, round: 1,
    current_turn: "p1", elevacoes: elev2, materiais: {}, decorations: [],
    pontes: [], transicao_altura: transicao,
  });
  const st = GS.gameState;
  const res = new Set();
  GS.bfsReachable(st.tiles, new Set(explored2.map(([x, y]) => `${x},${y}`)),
    4, 5, 6, res,
    { materiais: st.materiais, elevacoes: st.elevacoes, state: st, actor: st.players[0] });
  return res;
}
check("rampa: descer 1 degrau continua no alcance",
      alcanceDegrau("rampa").has("5,5"));
check("declive: descer 1 degrau sai do alcance",
      !alcanceDegrau("declive").has("5,5"));

console.log("\n[8] O editor deriva a altura da ponte, não a congela");
const editorSrc = semComentarios(fs.readFileSync(path.join(raiz, "tools/editor.js"), "utf8"));
check("editor.js tem um helper bridgeAltura", /function\s+bridgeAltura\s*\(/.test(editorSrc));
check("placeBridge usa o helper em vez de elevationAt cru",
      /placeBridge[\s\S]{0,400}altura:\s*bridgeAltura\(/.test(editorSrc));
check("a serialização também deriva",
      /pontes:\s*S\.pontes\.map[\s\S]{0,200}altura:\s*bridgeAltura\(/.test(editorSrc));

console.log("\n" + "=".repeat(62));
console.log(`  ${PASS} passaram, ${FAIL} falharam`);
console.log("=".repeat(62));
process.exit(FAIL ? 1 : 0);
