// Escolha de direção direto no tabuleiro (sem quadro): tom das casas, giro do boneco,
// confirmar encerrando o turno de novo, cancelar volta ao que era.
// Roda da raiz: node tools/test_direcao_no_tabuleiro.js
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");
const game = fs.readFileSync(path.join(raiz, "game.js"), "utf8").split("\r\n").join("\n");
let PASS = 0, FAIL = 0;
const check = (n, c) => { if (c) { PASS++; console.log("  ✅ " + n); } else { FAIL++; console.log("  ❌ " + n); } };

global.WebSocket = class { constructor() {} send() {} close() {} };
global.window = {};
global.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
global.location = { search: "", protocol: "http:", host: "x" };
global.setTimeout = () => 0; global.clearTimeout = () => {};
const GS = eval(fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8") + "; GS");

function extrair(nome) {
  const i = game.indexOf(`function ${nome}(`);
  if (i < 0) return null;
  let k = game.indexOf("{", i), d = 0;
  for (; k < game.length; k++) { if (game[k] === "{") d++; else if (game[k] === "}") { d--; if (!d) break; } }
  return game.slice(i, k + 1);
}

console.log("\n[1] Sem quadro: nada de diagrama nem botões de seta");
check("o diagrama e os botões saíram", !/bussola-grade|bussola-seta|bussola-ok|_bussolaDiagramaHTML|_BUSSOLA_DIRS/.test(game));
check("a dica rodapé existe e é uma só linha de texto", /bussola-dica-rodape/.test(game) && /ui\.direcao\.dica_rodape/.test(game));
check("a dica só aparece até a primeira confirmação", /if\(!_bussolaJaVista\(\)\)\{/.test(game)
  && /if\(confirmar\)\{\n    _bussolaMarcarVista\(\)/.test(game));

console.log("\n[2] Tom das 8 casas por setor");
const fn = extrair("_setoresDaEscolha");
check("função existe", !!fn);
const roda = (f, tiles) => {
  const fabrica = new Function("GS", "_bussola", "TILE_WALL", fn + "\nreturn _setoresDaEscolha;");
  const me = { pos: [2, 2] };
  return fabrica({ me, setorAtaque: GS.setorAtaque }, { f }, 1)({ tiles });
};
const livre = [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]];
let r = roda([0, 1], livre);   // olhando para o sul
const por = (x, y) => r.find(c => c.x === x && c.y === y)?.setor;
check("8 casas, olhando ao sul", r.length === 8);
check("sul é frente, norte é costas", por(2, 3) === "frente" && por(2, 1) === "costas");
check("leste e oeste são flanco", por(3, 2) === "flanco" && por(1, 2) === "flanco");
r = roda([0, -1], livre);
check("girou ao norte: o tom inverte", por(2, 1) === "frente" && por(2, 3) === "costas");
const paredes = livre.map(l => l.slice()); paredes[1][2] = 1;
r = roda([0, 1], paredes);
check("casa de parede não é pintada", r.length === 7 && por(2, 1) === undefined);
check("sem estado de tiles: nada", roda([0, 1], undefined).length === 0);

console.log("\n[3] Fluxo de confirmar e cancelar");
check("encerrar de novo confirma", /if\(_bussola\)\{ _bussolaFechar\(true\); return; \}/.test(game));
check("cancelar devolve a direção do boneco", /_bussolaGirarPeao\(GS\.facingDe\(GS\.me\)\)/.test(game));
check("o boneco gira ao escolher (3D)", /function _bussolaGirarPeao[\s\S]*?_girarRaizPeao3D\(fig, _facingToRotY\(f\)\)/.test(game));
check("a prévia sobrevive a um redesenho do peão", /_sincronizarPeaoHeroi3D\(_figInvis, isCur, \(_facingPreview/.test(game));
check("2D e 3D desenham o tom, e o 3D é descartado com a cena",
  /_desenharSetoresDirecao2D\(ctx, state\)/.test(game) && /_setoresAtualizar3D\(\);/.test(game) && /_setoresDispose3D\(\);/.test(game));

console.log(`\nTotal: ${PASS} ok, ${FAIL} falhas`);
process.exit(FAIL ? 1 : 0);
