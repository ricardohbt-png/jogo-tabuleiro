// Efeitos de chão acompanham a elevação do terreno (3D). Roda da raiz:
//   node tools/test_efeitos_chao_elevacao.js
//
// As animações de magia, armadilha, fumaça e sombra são montadas com o chão no
// nível 0 e reescrevem `position.y` a cada quadro (ou só uma vez ao montar).
// `_elevarEfeitosChao3D` roda por último no quadro e soma a elevação da casa.
// Este teste extrai as funções REAIS do game.js e confere que:
//  - a peça sobe até o topo do platô da casa onde está;
//  - quadros seguidos sem a animação mexer NÃO acumulam a subida;
//  - quando a animação reescreve o y, a subida é reaplicada sobre o valor novo;
//  - grupos que já calculam a altura sozinhos (protetor, auras) ficam de fora;
//  - o fogo persistente e as labaredas nascem na altura da casa.
const fs = require("fs");
const path = require("path");
const src = fs.readFileSync(path.join(__dirname, "..", "game.js"), "utf8").replace(/\r\n/g, "\n");

let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); }
                                else { FAIL++; console.log("  ❌ " + name); } };

function extrair(nome) {
  const i = src.search(new RegExp("^(?:function " + nome + "\\(|(?:const|let) " + nome + "\\b)", "m"));
  if (i < 0) throw new Error("não achei " + nome);
  if (src.startsWith("function", i)) {
    let d = 0, j = src.indexOf("{", i);
    for (; j < src.length; j++) { if (src[j] === "{") d++; else if (src[j] === "}" && --d === 0) break; }
    return src.slice(i, j + 1);
  }
  return src.slice(i, src.indexOf(";\n", i) + 1).replace(/^const /, "var ").replace(/^let /, "var ");
}

const STEP = 0.24;
const ctx = {
  g3: null, GS: { gameState: null },
  topoSuperficie3D: (st, x, y, TH = 0.22) => TH + (Number(st.elevacoes[`${x},${y}`]) || 0) * STEP,
};
const codigo = ["_EFEITO_CHAO_RE", "_EFEITO_CHAO_FORA", "elevacaoChao3D", "_efeitoChaoElegivel",
  "_elevarNo3D", "_naOrigem3D", "_elevarFilhos3D", "_elevChaoCache", "_mapaTemElevacao",
  "_elevarEfeitosChao3D"].map(extrair).join("\n");
const fn = new Function(...Object.keys(ctx), codigo +
  "\nreturn {elevacaoChao3D, _efeitoChaoElegivel, _elevarEfeitosChao3D};");
const lib = fn(...Object.values(ctx));

const obj = (x, y, z) => ({ isGroup: false, position: { x, y, z }, rotation: { x: 0, y: 0, z: 0 },
                            userData: {}, children: [] });
const grupo = (nome, filhos, pos = [0, 0, 0]) => Object.assign(obj(...pos), { isGroup: true, name: nome, children: filhos });

const state = { elevacoes: { "3,1": 2 }, pontes: [] };
ctx.GS.gameState = state;
// O GS é capturado por referência no closure; recriamos a cena a cada caso.
function rodar(cena) {
  const fn2 = new Function("g3", "GS", "topoSuperficie3D", codigo +
    "\nreturn _elevarEfeitosChao3D();");
  fn2({ scene: { children: cena } }, { gameState: state }, ctx.topoSuperficie3D);
}

console.log("[1] elegibilidade por nome");
check("bola de fogo é efeito de chão", lib._efeitoChaoElegivel("bola-fogo-animation"));
check("armadilha é efeito de chão", lib._efeitoChaoElegivel("trap-fx-buraco"));
check("fumaça é efeito de chão", lib._efeitoChaoElegivel("fumaca-zona1"));
check("protetor fica de fora (segue o peão pela posição de mundo)", !lib._efeitoChaoElegivel("protetor-animation"));
check("aura da canção fica de fora (já usa o topo do terreno)", !lib._efeitoChaoElegivel("cancao-heroica-aura"));
check("grupo sem nome fica de fora", !lib._efeitoChaoElegivel(""));

console.log("[2] peça em casa de platô sobe, sem acumular");
{
  const anel = obj(3, 0.30, 1);
  const chao = obj(1, 0.30, 1);
  const cena = [grupo("bola-fogo-animation", [anel, chao])];
  rodar(cena);
  const alvo = 0.30 + 2 * STEP;
  check("anel na casa de nível 2 sobe 2 níveis", Math.abs(anel.position.y - alvo) < 1e-9);
  check("anel na casa de nível 0 não se mexe", Math.abs(chao.position.y - 0.30) < 1e-9);
  rodar(cena); rodar(cena);
  check("três quadros sem a animação mexer não acumulam", Math.abs(anel.position.y - alvo) < 1e-9);
  anel.position.y = 0.50;   // a animação reescreve o y no quadro seguinte
  rodar(cena);
  check("y reescrito pela animação recebe a subida de novo", Math.abs(anel.position.y - (0.50 + 2 * STEP)) < 1e-9);
  anel.position.x = 1;      // a peça anda para uma casa plana
  rodar(cena);
  check("ao sair do platô a subida é retirada", Math.abs(anel.position.y - 0.50) < 1e-9);
}

console.log("[3] grupo posicionado na casa sobe inteiro");
{
  const g = grupo("guarda-maxima-fx", [obj(0, 0.1, 0)], [3, 0, 1]);
  rodar([g]);
  check("o grupo sobe, não os filhos", Math.abs(g.position.y - 2 * STEP) < 1e-9
        && Math.abs(g.children[0].position.y - 0.1) < 1e-9);
}

console.log("[4] subgrupo na origem: as peças dentro dele é que sobem");
{
  const dentro = obj(3, 0.05, 1);
  const g = grupo("tempestade-de-ciclones-animation", [grupo("ciclones", [dentro])]);
  rodar([g]);
  check("peça do subgrupo sobe", Math.abs(dentro.position.y - (0.05 + 2 * STEP)) < 1e-9);
}

console.log("[5] fora da lista não é tocado");
{
  const peca = obj(3, 0.4, 1);
  rodar([grupo("protetor-animation", [peca])]);
  check("protetor intacto", Math.abs(peca.position.y - 0.4) < 1e-9);
}

console.log("[6] fogo persistente e labaredas nascem na altura da casa");
check("pool do fogo persistente usa a elevação da casa",
      /fireGroup\.position\.set\(fx, elevacaoChao3D\(state, fx, fy\), fy\)/.test(src)
      && !/fireGroup\.position\.set\(fx, 0, fy\)/.test(src));
check("marcador de armadilha usa o topo da casa",
      /dec\.position\.set\(ax, topoSuperficie3D\(state, ax, ay, 0\.232\), ay\)/.test(src)
      && /sp\.position\.set\(ax, topoSuperficie3D\(state, ax, ay, 0\.34\), ay\)/.test(src));
check("o passo roda antes do render", /_elevarEfeitosChao3D\(\);\s*\n\s*g3\.renderer\.render\(g3\.scene, g3\.camera\)/.test(src));

console.log(`\n=== ${PASS} passaram, ${FAIL} falharam ===`);
process.exit(FAIL ? 1 : 0);
