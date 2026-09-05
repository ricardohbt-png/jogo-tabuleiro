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

console.log("\n==============================================================");
console.log(`  ${PASS} passaram, ${FAIL} falharam`);
console.log("==============================================================");
process.exit(FAIL ? 1 : 0);
