// Popup dos redemoinhos do Senhor das Águas — roda da raiz:
//   node tools/test_senhor_aguas_cliente.js
//
// Duas metades, como as demais suítes de cliente do projeto:
//  [1]-[3] a DECISÃO pura de abrir o popup, extraída do game.js e avaliada
//          aqui (se a função for renomeada ou sumir, o teste cai);
//  [4]-[6] a FIAÇÃO (camada de z-index, classe do escopo do controle e foco),
//          por varredura estática — é browser-bound e não dá para exercitar
//          em node, e a varredura é o que impede a regressão silenciosa.
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");
const GAME = fs.readFileSync(path.join(raiz, "game.js"), "utf8");
const CSS  = fs.readFileSync(path.join(raiz, "game.css"), "utf8");
const INV  = fs.readFileSync(path.join(raiz, "src", "ui", "inventoryModal.js"), "utf8");

let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); }
                                else { FAIL++; console.log("  ❌ " + name); } };

// Recorta a função pelo nome e devolve o fonte. Ancorado no início da linha
// para não pegar uma chamada.
function fonteDaFuncao(nome, texto = GAME) {
  const i = texto.indexOf("\nfunction " + nome + "(");
  if (i < 0) return null;
  const k = texto.indexOf("{", i);
  let nivel = 0;
  for (let j = k; j < texto.length; j++) {
    if (texto[j] === "{") nivel++;
    else if (texto[j] === "}") { nivel--; if (nivel === 0) return texto.slice(i, j + 1); }
  }
  return null;
}

// z-index declarado para um id, seja em regra CSS ou em style inline do
// markup. Os overlays do jogo nascem dos dois jeitos.
function zIndexDe(id, textos) {
  const esc = id.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  for (const texto of textos) {
    const regra = new RegExp("#" + esc + "[^{]*\\{[^}]*?z-index\\s*:\\s*(\\d+)").exec(texto);
    if (regra) return Number(regra[1]);
    const inline = new RegExp('id="' + esc + '"[\\s\\S]{0,600}?z-index\\s*:\\s*(\\d+)').exec(texto);
    if (inline) return Number(inline[1]);
  }
  return null;
}

console.log("\n[1] A decisão de abrir o popup é uma função pura");
const srcDecisao  = fonteDaFuncao("_senhorAguasDecisaoPopup");
const srcRestante = fonteDaFuncao("_senhorAguasRestante");
const srcLimite   = fonteDaFuncao("_senhorAguasLimite");
check("_senhorAguasDecisaoPopup existe no game.js", !!srcDecisao);
check("não toca DOM, window, GS nem rAF",
  !!srcDecisao && !/\b(document|window|GS|g3|requestAnimationFrame)\b/.test(srcDecisao));
if (srcLimite) eval(srcLimite);
if (srcRestante) eval(srcRestante);
if (srcDecisao) eval(srcDecisao);

// Estado mínimo de uma masmorra com o clérigo na vez e uma zona com cota.
const zonaOk = { id: "z1", tipo: "senhor_das_aguas", ativa: true, caster: "id_1",
                 disponivel_em: 2, redemoinhos: [], redemoinho_max: 2,
                 tiles: [[2, 3], [3, 3]] };
const estado = (over = {}, zona = {}) => ({
  phase: "playing", round: 3, current_turn: "id_1", animados_turn: null,
  current_actor: { kind: "player", id: "id_1" },
  players: [{ id: "id_1", class_id: "cleric", alive: true, level: 5 }],
  zonas_especiais: [{ ...zonaOk, ...zona }],
  ...over,
});

console.log("\n[2] Caso feliz e chave de deduplicação");
if (srcDecisao) {
  const d = _senhorAguasDecisaoPopup(estado(), "id_1", null);
  check("abre no turno do clérigo com cota disponível", d.abrir === true);
  check("devolve a zona escolhida", !!d.zona && d.zona.id === "z1");
  check("a chave identifica zona + rodada",
    typeof d.chave === "string" && d.chave.includes("z1") && d.chave.includes("3"));
  check("a mesma chave não reabre no mesmo turno",
    _senhorAguasDecisaoPopup(estado(), "id_1", d.chave).abrir === false);
  check("o motivo do bloqueio por repetição é explícito",
    _senhorAguasDecisaoPopup(estado(), "id_1", d.chave).motivo === "ja_abriu");
  check("rodada seguinte gera chave nova",
    _senhorAguasDecisaoPopup(estado({ round: 4 }), "id_1", d.chave).abrir === true);
}

console.log("\n[3] Cada guarda diz por que barrou");
if (srcDecisao) {
  const motivo = (over, zona) => _senhorAguasDecisaoPopup(estado(over, zona), "id_1", null).motivo;
  check("sem estado", _senhorAguasDecisaoPopup(null, "id_1", null).motivo === "sem_estado");
  check("fora da fase de jogo", motivo({ phase: "city" }) === "fora_de_jogo");
  check("não é o meu turno", motivo({ current_turn: "id_2" }) === "fora_do_turno");
  check("janela dos servos", motivo({ animados_turn: "id_1" }) === "janela_servos");
  check("herói não é clérigo",
    motivo({ players: [{ id: "id_1", class_id: "mage", alive: true, level: 5 }] }) === "nao_clerigo");
  check("herói morto",
    motivo({ players: [{ id: "id_1", class_id: "cleric", alive: false, level: 5 }] }) === "morto");
  check("nenhuma zona do próprio clérigo", motivo({}, { caster: "id_9" }) === "sem_zona");
  check("cota esgotada", motivo({}, { redemoinhos: [[2, 3], [3, 3]] }) === "cota_zerada");
  check("ainda não liberou (2ª rodada)", motivo({ round: 1 }) === "rodada_cedo");
}

console.log("\n[4] O popup fica ACIMA dos menus de personagem");
const zPopup  = zIndexDe("senhor-aguas-overlay", [GAME]);
const zMagias = zIndexDe("menu-magias-overlay", [CSS]);
const zHabil  = zIndexDe("menu-habilidades-overlay", [CSS]);
const zInv    = zIndexDe("inv-modal-overlay", [INV]);
check(`z-index do popup foi lido (${zPopup})`, typeof zPopup === "number");
check(`z-index do menu de magias foi lido (${zMagias})`, typeof zMagias === "number");
check(`z-index do menu de habilidades foi lido (${zHabil})`, typeof zHabil === "number");
check(`z-index do inventário foi lido (${zInv})`, typeof zInv === "number");
// A regressão real: com 121 o popup abria ATRÁS do Grimório (510) e o jogador
// só via a mensagem dentro do menu.
check("popup acima do menu de magias", zPopup > zMagias);
check("popup acima do menu de habilidades", zPopup > zHabil);
check("popup acima do inventário", zPopup > zInv);

console.log("\n[5] A chave só é gravada quando a janela realmente abriu");
const srcConsiderar = fonteDaFuncao("_considerarPopupSenhorDasAguas");
const srcAbrir      = fonteDaFuncao("_abrirJanelaSenhorDasAguas");
check("_considerarPopupSenhorDasAguas existe", !!srcConsiderar);
check("ela delega a decisão à função pura",
  !!srcConsiderar && /_senhorAguasDecisaoPopup\(/.test(srcConsiderar));
check("_abrirJanelaSenhorDasAguas devolve se abriu",
  !!srcAbrir && /return true;/.test(srcAbrir) && /return false;/.test(srcAbrir));
check("a chave é gravada depois da abertura, não antes",
  !!srcConsiderar
  && srcConsiderar.indexOf("_abrirJanelaSenhorDasAguas(") > 0
  && srcConsiderar.indexOf("_abrirJanelaSenhorDasAguas(")
     < srcConsiderar.lastIndexOf("_senhorAguasUltimoPopupTurno ="));

console.log("\n[6] O controle enxerga e navega o popup");
// _gamepadUiScope() só reconhece overlay com a classe .open; sem ela o escopo
// continua sendo o tabuleiro e os botões da janela ficam inalcançáveis.
check("abrir adiciona a classe open", !!srcAbrir && /classList\.add\(['"]open['"]\)/.test(srcAbrir));
const srcFechar = fonteDaFuncao("_fecharJanelaSenhorDasAguas");
check("fechar remove a classe open", !!srcFechar && /classList\.remove\(['"]open['"]\)/.test(srcFechar));
const srcRecuperarFoco = fonteDaFuncao("_gamepadRecoverSenhorAguasFocus");
const srcPollGamepad = fonteDaFuncao("_pollGamepad");
check("o foco é recuperado quando o gamepad é reconhecido depois do popup",
  !!srcRecuperarFoco && !!srcPollGamepad && /_gamepadRecoverSenhorAguasFocus\(\)/.test(srcPollGamepad));
check("o escopo do controle aceita overlay .open", /\[id\$="-overlay"\]\.open/.test(GAME));
// _gamepadUiScope() resolve empate por ORDEM NO DOM (`open.at(-1)`), não por
// z-index. Os menus de personagem são criados dinamicamente e ficam DEPOIS do
// popup no <body>: sem reancorar, o Grimório rouba o escopo do controle mesmo
// com o popup visualmente por cima. Medido em jogo.
check("abrir reancora o popup no fim do body",
  !!srcAbrir && /document\.body\.appendChild\(overlay\)/.test(srcAbrir));
check("ao abrir, o foco do controle vai para o botão de criar",
  !!srcAbrir && /_gamepadFocusMapPoint\([\s\S]{0,140}senhor-aguas-create/.test(srcAbrir));
check("o botão Fechar responde ao B do controle",
  /id="senhor-aguas-close"[^>]*data-gamepad-cancel|data-gamepad-cancel[^>]*id="senhor-aguas-close"/.test(GAME));
const srcCancel = fonteDaFuncao("_gamepadCancel");
check("B fecha o popup do Senhor das Águas",
  !!srcCancel && /senhor-aguas-overlay/.test(srcCancel) && /_fecharJanelaSenhorDasAguas\(\)/.test(srcCancel));

console.log("\n[V] Um véu esconde o terreno novo até a frente da onda revelar a casa");
// A água/gelo chega no game_state junto do `start` e o tabuleiro já a mostrava
// enquanto a concentração + viagem ainda rodavam (mesma classe do véu da Ira).
{
  const declSource = (name) => {
    const m = GAME.match(new RegExp("^(?:const|let) " + name + " = [\\s\\S]*?;[ \\t]*$", "m"));
    return m ? m[0].replace(/^(const|let) /, "var ") : null;
  };
  const veu = declSource("TERRENO_MAGIA_VEU_OPACIDADE");
  let val = null; try { val = new Function(veu + "\nreturn TERRENO_MAGIA_VEU_OPACIDADE;")(); } catch (e) {}
  check("existe a constante do véu e é opaca o bastante (≥ 0.85)", typeof val === "number" && val >= 0.85);
  const build = fonteDaFuncao("_senhorAguasBuild3D"), upd = fonteDaFuncao("_senhorAguasUpdate3D"), d2 = fonteDaFuncao("_senhorAguasDraw2D");
  check("3D: o build cria o véu com a constante e depthTest ligado",
    /opacity:\s*TERRENO_MAGIA_VEU_OPACIDADE/.test(build) && /cover[\s\S]{0,200}depthTest:\s*true/.test(build));
  check("3D: o update desvanece o véu com o reveal", /cover\.material\.opacity[^\n]*\(1\s*-\s*reveal\)[^\n]*TERRENO_MAGIA_VEU_OPACIDADE|cover\.material\.opacity[^\n]*TERRENO_MAGIA_VEU_OPACIDADE[^\n]*\(1\s*-\s*reveal\)/.test(upd));
  check("2D: o preenchimento do véu usa a constante e o reveal", /TERRENO_MAGIA_VEU_OPACIDADE\s*\*\s*\(1\s*-\s*reveal\)/.test(d2));
  // Comportamento com stubs: véu cheio no início, zerado depois da frente; redemoinhos sem véu.
  try {
    const fns = ["_senhorAguasHash","_senhorAguasAnimFromMessage","_senhorAguasProgress","_senhorAguasSetLine","_senhorAguasBuild3D","_senhorAguasDispose3D","_senhorAguasUpdate3D"];
    const code = [declSource("SENHOR_AGUAS_CONCENTRACAO_MS"), declSource("CHAMADO_INVERNO_CONCENTRACAO_MS"), declSource("SENHOR_AGUAS_TRAVEL_MS"),
      declSource("SENHOR_AGUAS_IMPACT_MS"), veu, declSource("TERRENO_MAGIA_VEU_COR") || "", ...fns.map(f => fonteDaFuncao(f))].join("\n");
    class V { constructor(){ this.x=0; this.y=0; this.z=0; } set(){ return this; } copy(){ return this; } setScalar(){ return this; } lerp(){ return this; } }
    class Obj { constructor(){ this.position=new V(); this.scale=new V(); this.rotation=new V(); this.userData={}; this.visible=true; this.material={opacity:0,dispose(){}}; this.geometry={dispose(){}}; this.children=[]; this.parent=null; } add(...c){ for(const x of c){ x.parent=this; this.children.push(x);} } remove(){} traverse(f){ f(this); this.children.forEach(c=>c.traverse(f)); } lookAt(){} }
    class Mat { constructor(o){ Object.assign(this,o||{}); this.opacity=this.opacity||0; } dispose(){} }
    const THREE = new Proxy({AdditiveBlending:1, DoubleSide:2}, { get:(t,k)=> k in t ? t[k] : String(k).endsWith("Material") ? Mat : k==="Vector3" ? V : k==="BufferGeometry" ? class { setFromPoints(){ return this; } dispose(){} } : Obj });
    const g3 = { scene: new Obj() };
    const api = new Function("g3", "window", "performance", code + "\nreturn {from:_senhorAguasAnimFromMessage, upd:_senhorAguasUpdate3D};")(g3, {THREE}, {now:()=>0});
    const anim = api.from({spell_id:"senhor_das_aguas", phase:"start", origin:[1,1], center:[4,4], tiles:[[3,3],[4,3],[3,4],[4,4]], material:"agua", charge_ms:820, travel_ms:800, impact_ms:1350});
    api.upd(anim, 100);
    const cover = anim.tileMeshes[0].cover;
    check("no início o véu está cheio", !!cover && cover.material.opacity >= val - 0.01);
    api.upd(anim, 820 + 800 + 1350 + 400);
    check("depois da frente o véu sumiu", cover.material.opacity <= 0.01);
    const whirl = api.from({spell_id:"senhor_das_aguas", phase:"whirlpools", origin:[1,1], tiles:[[3,3]], material:"rodamoinho", travel_ms:420, impact_ms:720});
    api.upd(whirl, 100);
    check("marcação de redemoinhos não tem véu", !whirl.tileMeshes[0].cover);
  } catch (e) { check("comportamento do véu com stubs (" + e.message + ")", false); }
}

console.log("\n==============================================================");
console.log(`  ${PASS} passaram, ${FAIL} falharam`);
console.log("==============================================================");
process.exit(FAIL ? 1 : 0);
