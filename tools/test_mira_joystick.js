// Mira pelo controle — roda da raiz: node tools/test_mira_joystick.js
//
// Duas metades, como o resto das suítes de cliente do projeto:
//  [1]-[2] o miolo PURO do passo do direcional, extraído do game.js e avaliado
//          aqui (se a função for renomeada ou sumir, o teste cai);
//  [3]-[5] a FIAÇÃO, por varredura estática — é browser-bound (Gamepad API,
//          laço de rAF, THREE), então não dá para exercitar em node, e a
//          varredura é o que impede a regressão silenciosa.
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");
const GAME = fs.readFileSync(path.join(raiz, "game.js"), "utf8");

let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); }
                                else { FAIL++; console.log("  ❌ " + name); } };

// Recorta a função pelo nome e avalia. Ancorado no início da linha para não
// pegar uma chamada.
function fonteDaFuncao(nome) {
  const i = GAME.indexOf("\nfunction " + nome + "(");
  if (i < 0) return null;
  let k = GAME.indexOf("{", i), nivel = 0;
  for (let j = k; j < GAME.length; j++) {
    if (GAME[j] === "{") nivel++;
    else if (GAME[j] === "}") { nivel--; if (nivel === 0) return GAME.slice(i, j + 1); }
  }
  return null;
}

console.log("\n[1] _aimStepTile existe e é puro");
const src = fonteDaFuncao("_aimStepTile");
check("a função foi encontrada no game.js", !!src);
check("não toca DOM, window nem GS", src && !/\b(document|window|GS|g3)\b/.test(src));
eval(src);

const disco = new Set();                       // alcance cheio: Chebyshev raio 2 em (5,5)
for (let y = 3; y <= 7; y++) for (let x = 3; x <= 7; x++) disco.add(`${x},${y}`);
const esparso = new Set(["5,5", "9,5", "5,9"]); // lista de alvos: só 3 casas

console.log("\n[2] Passo do direcional");
check("anda uma casa num alcance cheio",
  String(_aimStepTile([5, 5], 1, 0, disco, 20, 20)) === "6,5");
check("anda na diagonal",
  String(_aimStepTile([5, 5], 1, 1, disco, 20, 20)) === "6,6");
check("na borda do alcance, não sai dele",
  _aimStepTile([7, 5], 1, 0, disco, 20, 20) === null);
check("num conjunto esparso, salta para o próximo alvo na direção",
  String(_aimStepTile([5, 5], 1, 0, esparso, 20, 20)) === "9,5");
check("no esparso, direção sem alvo nenhum não move",
  _aimStepTile([5, 5], -1, 0, esparso, 20, 20) === null);
check("sem alcance publicado o cursor anda livre",
  String(_aimStepTile([0, 0], 1, 0, null, 20, 20)) === "1,0");
check("não atravessa a borda do tabuleiro",
  _aimStepTile([19, 5], 1, 0, null, 20, 20) === null);
check("direção nula não move", _aimStepTile([5, 5], 0, 0, disco, 20, 20) === null);
check("cursor fora do alcance entra nele pela frente",
  String(_aimStepTile([1, 5], 1, 0, disco, 20, 20)) === "3,5");

console.log("\n[2b] Nota Cortante: o alcance pintado é o do instrumento");
// O alcance vinha peneirado por chão + linha de visão, o que numa sala fechada
// desenhava o formato da SALA em vez do alcance da arma. Agora ele é o mesmo
// disco Chebyshev que as magias pintam; a linha de visão continua valendo, mas
// só para dizer o que é ALVO válido (o verde) e para aceitar o clique.
const srcMira = fonteDaFuncao("_iniciarMiraInstrumento");
check("a função da mira do instrumento foi encontrada", !!srcMira);
check("o alcance é montado com _addCheb, como o das magias", /_addCheb\(/.test(srcMira));
check("o alcance NÃO é peneirado por TILE_FLOOR", !/TILE_FLOOR/.test(srcMira));
check("a casa do próprio bardo sai do alcance", /range\.delete\(/.test(srcMira));
check("a linha de visão ainda decide o ALVO válido (verde)",
  /validTargets[\s\S]{0,400}?hasLineOfSight\(/.test(srcMira));
check("o raio vem dos stats do instrumento", /instrumentoStatsClient\([\s\S]{0,120}?alcance/.test(srcMira));

console.log("\n[2c] Nenhum contorno: o alcance é pintado, como os demais");
check("não sobrou função de contorno", !/_aimRenderRangeOutline3D|_aimBordaDoAlcance/.test(GAME));
check("o 2D pinta o alcance com o preenchimento da paleta",
  /for \(const k of hl\.range\) draw\(k, AIM_COLORS\.range\.fill\)/.test(GAME));
check("o 3D acende o alcance pelo pool de casas",
  /toggle\(g3\.spellRangeMeshes,\s+hl\.range\);/.test(GAME));

console.log("\n[3] O direcional esquerdo não move o peão durante a mira");
// O ramo da mira precisa vir ANTES do ramo que chama GS.move, senão o herói
// anda enquanto o jogador escolhe o alvo — o defeito que motivou esta camada.
const iMira = GAME.indexOf("} else if(_aimAlgumModoAtivo()){");
const iMove = GAME.indexOf("} else if(_gamepadRepeat('move', moveDir, now) && GS.isMyTurn){");
check("existe um ramo de mira no laço do controle", iMira > 0);
check("existe o ramo de movimento do peão", iMove > 0);
check("a mira é testada ANTES do movimento", iMira > 0 && iMove > 0 && iMira < iMove);
check("o ramo da mira chama _aimGamepadStep",
  /_aimAlgumModoAtivo\(\)\)\{[\s\S]{0,700}?_aimGamepadStep\(/.test(GAME));
check("o ramo da mira zera o canal de movimento",
  /_aimAlgumModoAtivo\(\)\)\{[\s\S]{0,900}?_gamepadRepeat\('move', null, now\)/.test(GAME));

console.log("\n[4] Analógico direito travado e cursor semeado");
check("o analógico direito é travado junto com o do ataque",
  GAME.includes("} else if(_gamepadInput.attackMode || _aimAlgumModoAtivo()){"));
check("_aimStart semeia o cursor do controle", /_aimStart[\s\S]{0,4000}?_aimSeedGamepadCursor\(\);/.test(GAME));
check("_aimEnd zera o canal do direcional da mira",
  /_aimEnd[\s\S]{0,900}?_gamepadRepeat\('aimCursor', null/.test(GAME));
check("a semente usa o alcance publicado", /function _aimSeedGamepadCursor[\s\S]{0,900}?_aimGamepadRangeSet\(\)/.test(GAME));

console.log("\n[5] Uma cadeia de mira só, compartilhada por mouse e controle");
// Antes havia DUAS cadeias de `window._modoX` copiadas (mousemove 2D e 3D) e
// nenhuma no controle. Se voltar a haver mais de um lugar recalculando a
// prévia, elas divergem — foi assim que o controle ficou sem área.
check("_aimPreviewAt existe", GAME.includes("function _aimPreviewAt("));
check("o mousemove 2D delega a _aimPreviewAt",
  /addEventListener\('mousemove'[\s\S]{0,900}?_aimPreviewAt\(/.test(GAME));
check("o on3DMouseMove delega a _aimPreviewAt",
  /function on3DMouseMove[\s\S]{0,900}?_aimPreviewAt\(/.test(GAME));
check("o passo do controle delega a _aimPreviewAt",
  /function _aimGamepadStep[\s\S]{0,600}?_aimPreviewAt\(/.test(GAME));
const chamadas = (GAME.match(/_recomputarAreaMagia\(/g) || []).length;
check(`_recomputarAreaMagia é chamada em poucos lugares (${chamadas})`, chamadas <= 6);
check("os modos legados de arremesso ficam FORA da camada nova",
  !/function _aimAlgumModoAtivo\(\)[\s\S]{0,700}?_modoArremessoLanca/.test(GAME));

console.log("\n[6] A semente do cursor alcança uma área remota");
// Defeito medido: o Senhor das Águas pinta um quadrado longe do herói. A
// semente antiga só olhava monstro-no-alcance e casa-do-herói; quando nenhum
// dos dois estava no conjunto ela DESISTIA, e o cursor ficava fora da área.
// Como _aimStepTile só acha casa válida em linha reta, uma área desalinhada da
// linha, da coluna e das diagonais do herói travava as 8 direções.
const srcPerto = fonteDaFuncao("_aimCasaMaisProximaPermitida");
check("_aimCasaMaisProximaPermitida existe no game.js", !!srcPerto);
check("é pura: não toca DOM, window nem GS",
  !!srcPerto && !/\b(document|window|GS|g3)\b/.test(srcPerto));
if (srcPerto) {
  eval(srcPerto);
  // 2x2 desalinhado de (7,25) mais uma casa nitidamente mais perto: assim o
  // "mais próxima" é único e o teste não depende do critério de empate.
  const remota = new Set(["2,3", "3,3", "2,4", "3,4", "6,20"]);
  check("herói fora da área: devolve a casa permitida mais próxima",
    String(_aimCasaMaisProximaPermitida([7, 25], remota)) === "6,20");
  check("herói dentro da área: fica onde está",
    String(_aimCasaMaisProximaPermitida([2, 4], remota)) === "2,4");
  check("conjunto vazio não inventa casa",
    _aimCasaMaisProximaPermitida([7, 25], new Set()) === null);
  check("sem conjunto publicado devolve null",
    _aimCasaMaisProximaPermitida([7, 25], null) === null);
  check("empate é resolvido pela ordem do conjunto (determinístico)",
    String(_aimCasaMaisProximaPermitida([5, 5], new Set(["4,4", "6,6"]))) === "4,4");
}
check("a semente usa a casa mais próxima quando não há candidato",
  /function _aimSeedGamepadCursor[\s\S]{0,1200}?_aimCasaMaisProximaPermitida\(/.test(GAME));

console.log("\n[7] O botão de confirmar da mira é alcançável no controle");
// #aim-session-hud é anexado ao <body>, fora de #screen-game, e o cursor de
// interface (Y) só listava #objectives-hud e #btn-libertar — então uma mira de
// seleção múltipla não tinha como ser CONFIRMADA no controle.
const srcPtr = fonteDaFuncao("_gamepadUiPointerControls");
check("_gamepadUiPointerControls existe", !!srcPtr);
check("a lista do cursor de interface inclui os botões da mira",
  !!srcPtr && /#aim-session-hud button/.test(srcPtr));

console.log("\n[8] O guarda de \"tem mira ativa\" cobre TODOS os modos da camada");
// _aimAlgumModoAtivo e _aimPreviewAt sao as duas metades da MESMA camada: a
// primeira responde "ha mira ativa?" e a segunda trata a casa. Um modo que so
// esteja na segunda fica meio ligado: no mouse 3D o hover nunca roda (o
// on3DMouseMove so chama _aimPreviewAt quando o guarda diz que ha mira) e no
// controle o direcional cai no ramo de MOVIMENTO, andando com o herói em vez
// de percorrer as casas da mira. Foi o que aconteceu com _modoIraRocha
// (Chamas Vivas da Ira da Rocha Ardente).
// fonteDaFuncao ancora na 1a chave depois do nome -- que em _aimPreviewAt e a
// da DESESTRUTURACAO do parametro, nao a do corpo. Aqui o corpo e recortado
// pulando a lista de parametros primeiro.
function corpoDaFuncao(nome) {
  const i = GAME.indexOf(String.fromCharCode(10) + "function " + nome + "(");
  if (i < 0) return null;
  let j = GAME.indexOf("(", i), par = 0;
  for (; j < GAME.length; j++) {
    if (GAME[j] === "(") par++;
    else if (GAME[j] === ")") { par--; if (par === 0) break; }
  }
  let k = GAME.indexOf("{", j), n = 0;
  for (let m = k; m < GAME.length; m++) {
    if (GAME[m] === "{") n++;
    else if (GAME[m] === "}") { n--; if (n === 0) return GAME.slice(k, m + 1); }
  }
  return null;
}
const srcPreview = corpoDaFuncao("_aimPreviewAt");
const srcGuarda  = corpoDaFuncao("_aimAlgumModoAtivo");
check("_aimPreviewAt existe", !!srcPreview);
check("_aimAlgumModoAtivo existe", !!srcGuarda);
if (srcPreview && srcGuarda) {
  // Só conta o modo REALMENTE consultado (`if (window._modoX)`); o que aparece
  // em comentário (a nota dos modos legados) não vale.
  const semComentario = txt => txt.replace(/\/\/[^\n]*/g, "");
  const modos = txt => [...new Set(
    (semComentario(txt).match(/window\.(_modo[A-Za-z]+)/g) || []).map(m => m.slice(7)))];
  const tratados = modos(srcPreview);
  const faltando = tratados.filter(k => !new Set(modos(srcGuarda)).has(k));
  check("a varredura achou os modos de _aimPreviewAt", tratados.length >= 10);
  check("nenhum modo tratado ficou fora do guarda" +
        (faltando.length ? " (faltam: " + faltando.join(", ") + ")" : ""),
    faltando.length === 0);
}
console.log("\n==============================================================");
console.log(`  ${PASS} passaram, ${FAIL} falharam`);
console.log("==============================================================");
process.exit(FAIL ? 1 : 0);
