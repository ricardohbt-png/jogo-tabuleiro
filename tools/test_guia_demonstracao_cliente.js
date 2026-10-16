// Controlador de "Me mostra" — roda da raiz: node tools/test_guia_demonstracao_cliente.js
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");
let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); }
                                else { FAIL++; console.log("  ❌ " + name); } };

global.window = {};
eval(fs.readFileSync(path.join(raiz, "src", "guiaTutorial.js"), "utf8"));
eval(fs.readFileSync(path.join(raiz, "src", "guiaDemonstracao.js"), "utf8"));
const Demo = window.GuiaDemonstracao;

console.log("\n[0] borda de entrada do gamepad");
check("botão que iniciou Me mostra não cancela enquanto fica segurado",
  Demo.entradaNova([{ pressed: true }], [{ pressed: true }], false, false) === false);
check("estado booleano de botão gamepad mantido não cria nova entrada",
  Demo.entradaNova([true], [true], false, false) === false);
check("borda booleana de botão gamepad é detectada",
  Demo.entradaNova([true], [false], false, false) === true);
check("nova pressão no gamepad interrompe a sequência",
  Demo.entradaNova([{ pressed: true }], [{ pressed: false }], false, false) === true);
check("novo movimento do analógico interrompe a sequência",
  Demo.entradaNova([], [], true, false) === true);
check("analógico mantido não cancela novamente",
  Demo.entradaNova([], [], true, true) === false);

function ambiente({inventarioAberto = false, indisponivel = null} = {}) {
  let seq = 0;
  const timers = new Map();
  const operacoes = [], focos = [], estados = [];
  let aberto = inventarioAberto, openCalls = 0, gameActionCalls = 0;
  const registrar = op => {
    operacoes.push(op);
    if (!((op.acao === "focar" && typeof op.alvo === "string")
        || (op.acao === "abrir_interface" && ["inventario", "habilidades", "magias"].includes(op.alvo))))
      gameActionCalls++;
  };
  const demo = Demo.criar({
    validar: passo => window.GuiaTutorial.demonstracaoValidada(passo),
    parseUi: ui => window.GuiaTutorial.parseUi(ui),
    inventarioAberto: () => aberto,
    abrirInventario: () => { openCalls++; aberto = true; registrar({ acao: "abrir_interface", alvo: "inventario" }); },
    abrirHabilidades: () => registrar({ acao: "abrir_interface", alvo: "habilidades" }),
    abrirMagias: () => registrar({ acao: "abrir_interface", alvo: "magias" }),
    focar: alvo => { focos.push(alvo); registrar({ acao: "focar", alvo }); return alvo !== indisponivel; },
    aoEstado: info => estados.push(info),
    agendar: (fn, ms) => { const id = ++seq; timers.set(id, { fn, ms }); return id; },
    cancelarAgendamento: id => timers.delete(id),
    intervalo: 10
  });
  return {
    demo, timers, operacoes, focos, estados,
    get openCalls() { return openCalls; },
    get gameActionCalls() { return gameActionCalls; },
    fecharInventario() { aberto = false; },
    rodarProximo() { const item = timers.entries().next().value; if (item) { timers.delete(item[0]); item[1].fn(); } },
    drenar() { while (timers.size) this.rodarProximo(); },
    marcarAcaoReal() { gameActionCalls++; }
  };
}

const passo = { ui: "botao:inventario", demonstracao: [
  { acao: "focar", alvo: "botao:inventario" },
  { acao: "abrir_interface", alvo: "inventario" },
  { acao: "focar", alvo: "slot:weapon" }
] };

console.log("\n[1] cursor por clique e espera da ação real");
{
  const a = ambiente();
  const avancar = (sessao, p = passo, chave = "fala_2:0:hero") =>
    typeof sessao.demo.avancar === "function" && sessao.demo.avancar(p, chave) !== false;
  check("primeiro clique executa só o primeiro foco", avancar(a)
    && JSON.stringify(a.focos) === JSON.stringify(["botao:inventario"])
    && a.openCalls === 0 && a.timers.size === 0);
  check("clique seguinte abre o inventário sem avançar outra operação", avancar(a)
    && a.openCalls === 1 && a.focos.length === 1 && a.timers.size === 0);
  check("terceiro clique destaca o slot e para antes de equipar", avancar(a)
    && a.focos.at(-1) === "slot:weapon" && a.demo.estado() === "aguardando_jogador"
    && a.gameActionCalls === 0);
  check("clique no limite repete a orientação sem executar ação", avancar(a)
    && a.focos.at(-1) === "slot:weapon" && a.gameActionCalls === 0);
}

console.log("\n[2] suspensão e mudança de etapa");
{
  const a = ambiente();
  const avancar = chave => typeof a.demo.avancar === "function" && a.demo.avancar(passo, chave) !== false;
  avancar("fala_2:0:hero");
  avancar("fala_2:0:hero");
  a.demo.suspender?.("janela_fechada");
  a.fecharInventario();
  check("retomar reaplica a operação atual antes de seguir", avancar("fala_2:0:hero")
    && a.openCalls === 2 && a.focos.length === 1);
  check("o clique após retomar executa a próxima operação", avancar("fala_2:0:hero")
    && a.focos.at(-1) === "slot:weapon");
  avancar("fala_2:0:hero");
  const focoAntes = a.focos.length;
  check("novo passo começa uma demonstração nova só no clique", avancar("fala_2:1:hero")
    && a.focos.length === focoAntes + 1 && a.focos.at(-1) === "botao:inventario");
}

console.log("\n[3] alvo indisponível e ações não automatizadas");
{
  const a = ambiente({ indisponivel: "slot:weapon" });
  const avancar = () => typeof a.demo.avancar === "function" && a.demo.avancar(passo, "fala_2:0:hero") !== false;
  avancar(); avancar(); avancar();
  check("alvo indisponível usa fallback sem executar ação real", a.demo.estado() === "aguardando_jogador"
    && a.estados.some(e => e.fallback === true) && a.gameActionCalls === 0);
}

console.log("\n[3b] integração das prévias visuais no cursor por clique");
{
  const previsoes = [], limpezas = [];
  const demo = Demo.criar({
    validar: passo => window.GuiaTutorial.demonstracaoValidada(passo),
    parseUi: ui => window.GuiaTutorial.parseUi(ui),
    focar: () => true,
    preverVisual: op => { previsoes.push(op); return true; },
    limparVisual: motivo => limpezas.push(motivo)
  });
  const roteiro = { demonstracao: [
    { acao: "focar", alvo: "casa:[5,15]" },
    { acao: "prever_movimento", alvo: "casa:[5,15]" }
  ] };
  demo.avancar(roteiro, "movimento:0:hero");
  demo.avancar(roteiro, "movimento:0:hero");
  check("roteiro encaminha a operação visual ao adaptador", previsoes.length === 1
    && previsoes[0].acao === "prever_movimento");
  demo.avancar(roteiro, "movimento:0:hero");
  check("clique no limite repete a mesma prévia visual", previsoes.length === 2
    && previsoes[1].alvo === "casa:[5,15]");
  const cursorAntes = demo.cursor();
  demo.interagir();
  check("interação limpa animação sem avançar o cursor", limpezas.length > 0
    && demo.cursor() === cursorAntes);
  demo.suspender("janela_fechada");
  check("pausa remove prévia visual", limpezas.at(-1) === "suspender");
  demo.cancelar();
  check("fechar ou trocar passo limpa preview atual", limpezas.at(-1) === "cancelar");
}

console.log("\n[4] integração segura no jogo");
{
  const game = fs.readFileSync(path.join(raiz, "game.js"), "utf8");
  const html = fs.readFileSync(path.join(raiz, "index.html"), "utf8");
  const lang = fs.readFileSync(path.join(raiz, "src", "lang", "tutorial.js"), "utf8");
  const css = fs.readFileSync(path.join(raiz, "game.css"), "utf8");
  const inicio = game.indexOf("function _guiaDemonstracaoGarantir()");
  const fim = game.indexOf("function _guiaDemonstracaoIniciar()", inicio);
  const adaptador = inicio >= 0 && fim > inicio ? game.slice(inicio, fim) : "";
  const fechar = (game.match(/function _fecharJanelaLicao\(\)[\s\S]*?\n}/) || [""])[0];
  const reabrir = (game.match(/function _reabrirJanelaLicao\(\)\s*\{[^}]*\}/) || [""])[0];
  const mostrar = (game.match(/function _guiaMostrar\(\)\s*\{[^}]*\}/) || [""])[0];
  const iniciar = (game.match(/function _guiaDemonstracaoIniciar\(\)[\s\S]*?\n}/) || [""])[0];
  const janela = (game.match(/function _mostrarJanelaLicao\(msg,[\s\S]*?\n}/) || [""])[0];
  const foco = (game.match(/function _guiaDemonstracaoFocar\(ui\)[\s\S]*?\n}/) || [""])[0];
  check("game.js carrega só foco e aberturas de interface permitidas",
    /focar:\s*ui\s*=>\s*_guiaDemonstracaoFocar/.test(adaptador)
      && /InventoryModal\.open\(GS\.myPid\)/.test(adaptador)
      && /abrirMenuHabilidades\(GS\.myPid\)/.test(adaptador)
      && /abrirMenuMagias\(GS\.myPid\)/.test(adaptador));
  check("adaptador não chama ações reais da partida",
    !/GS\.(move|attack|castSpell|useItem|endTurn)\s*\(/.test(adaptador));
  const entrada = (game.match(/function _guiaDemonstracaoInteracao\([\s\S]*?\n}/) || [""])[0];
  check("entrada do jogador não bloqueia o evento", /\.interagir\(\)/.test(entrada)
    && !/preventDefault|stopPropagation/.test(entrada));
  check("gamepad reconhece nova entrada sem consumir o botão",
    /GuiaDemonstracao\.entradaNova\(/.test(game)
      && /\(_guiaDemoEstado === 'executando' \|\| _guiaDemoVisualTimeline\?\.ativo\(\)\) && gamepadEntradaNova[\s\S]{0,100}_guiaDemonstracaoInteracao\(null\)/.test(game));
  check("passo novo e herói novo encerram sessão antiga",
    /_guiaDemonstracaoCancelar\('passo_novo'\)/.test(game)
      && /_guiaDemonstracaoCancelar\('heroi_trocado'\)/.test(game));
  check("interface e mensagens da demonstração estão ligadas",
    html.includes("src/guiaDemonstracao.js")
      && lang.includes('"ui.tutorial.demonstracao.iniciada"')
      && lang.includes('"ui.tutorial.demonstracao.agora_voce"')
      && lang.includes('"ui.tutorial.demonstracao.cancelar"')
      && lang.includes('"ui.tutorial.demonstracao.indisponivel"'));
  check("cada clique em Me mostra avança o cursor existente",
    /_guiaDemonstracaoIniciar\(\)/.test(mostrar)
      && /_guiaDemonstracaoGarantir\(\)\.avancar\(/.test(iniciar));
  check("fechar ou pausar preserva o cursor", /_guiaDemonstracaoSuspender/.test(fechar)
    && /_guiaDemonstracaoSuspender/.test(game));
  check("reabrir a lição mantém a demonstração suspensa", /_mostrarJanelaLicao\(_licaoUltima, true\)/.test(reabrir));
  check("botão de pausa preserva a etapa", /onclick="_guiaDemonstracaoSuspender\('manual'\)"/.test(janela));
  check("passo com roteiro válido mostra o botão mesmo sem ui", /demonstracaoDisponivel\(passo\)/.test(janela));
  check("painel mostra os controles disponíveis por método", /licao-demonstracao-controles/.test(janela)
    && /controlesDemonstracao\(/.test(game));
  check("inventário aberto mantém a lição acima do modal", /guia-demo-acima-inventario/.test(game)
    && /#licao-janela\.guia-demo-acima-inventario\s*\{[^}]*z-index:\s*1110/.test(fs.readFileSync(path.join(raiz, "game.css"), "utf8")));
  check("retomar foco do slot reabre o inventário se foi fechado", /parsed\.tipo === 'slot'[\s\S]*InventoryModal\.isOpen\(\)[\s\S]*InventoryModal\.open\(GS\.myPid\)/.test(foco));
  check("adaptador recebe apenas operações de prévia verificadas", /preverVisual:\s*op\s*=>\s*_guiaDemoVisualIniciar\(op\)/.test(adaptador));
  check("game.js não envia ações reais ao reproduzir ghost", /function _guiaDemoVisualIniciar\([\s\S]*?\n}/.test(game)
    && !/GS\.(move|attack|castSpell|useItem|endTurn)\s*\(/.test((game.match(/function _guiaDemoVisualIniciar\([\s\S]*?\n}/) || [""])[0]));
  check("timeline visual carrega antes de game.js", html.indexOf("src/guiaDemonstracaoVisual.js") >= 0
    && html.indexOf("src/guiaDemonstracaoVisual.js") < html.indexOf("game.js?v="));
  check("ghost 2D usa miniatura do herói e valida casas visíveis", /_getHero2DImg\(c\.classe\)/.test(game)
    && /_guiaDemoVisualContextoValido\(amostra, state, visivel\)/.test(game)
    && /c\.caminho\.every\(p => ver\(p\[0\], p\[1\]\)\)/.test(game));
  check("prévia revalida alvo e caminho com o estado atual antes de desenhar",
    /function _guiaDemoVisualContextoValido\([\s\S]*?GS\.findPath\(/.test(game)
      && /GuiaTutorial\.alvoTabuleiro\([\s\S]*?alvoId/.test(game)
      && /_guiaDemoVisualContextoValido\(amostra, state, visivel\)/.test(game)
      && /_guiaDemoVisualContextoValido\(amostra, st, vis \?/.test(game));
  check("prévia de movimento 3D desenha a trilha validada do peão fantasma",
    /function _guiaDemoVisualTrilha3DAtualizar\([\s\S]*?contexto\.caminho[\s\S]*?new T\.Line\(/.test(game)
      && /_guiaDemoVisualTrilha3DAtualizar\(st, c\)/.test(game)
      && /guiaDemoTrilha/.test(game));
  const limpaInicio = game.indexOf('function _guiaDemoVisual3DLimpar()');
  const limpaFim = game.indexOf('function _guiaDemoGhost3DCriar', limpaInicio);
  const limpaGhost = limpaInicio >= 0 && limpaFim > limpaInicio ? game.slice(limpaInicio, limpaFim) : '';
  const limpaClone = limpaGhost.split('if(g3.guiaDemoImpact)')[0];
  check("ghost 3D clona materiais e desativa raycast sem liberar geometria compartilhada",
    /function _guiaDemoGhost3DCriar\([\s\S]*?material\.clone\(\)/.test(game)
      && /function _guiaDemoGhost3DCriar\([\s\S]*?obj\.raycast\s*=\s*\(\)\s*=>\s*\{\}/.test(game)
      && /m\.dispose\(\)/.test(limpaGhost)
      && /if\(geometriaPropria && obj\.geometry\) obj\.geometry\.dispose\(\)/.test(limpaClone));
  check("cursor de equipamento segue âncoras atuais sem clique sintético",
    /getBoundingClientRect\(\)/.test(game) && /pointer-events:\s*none/.test(css)
      && !/dispatchEvent\(|\.click\(\)/.test((game.match(/function _guiaDemoCursorAtualizar\([\s\S]*?\n}/) || [""])[0]));
  check("pausa, fechamento, mudança de modo e dispose3D limpam ghost e ciclo",
    /limparVisual:\s*\(\)\s*=>\s*_guiaDemoVisualLimpar\(\)/.test(adaptador)
      && /function dispose3D\(\)[\s\S]*?_guiaDemoVisualLimpar\(\)/.test(game)
      && /function toggle3D\(\)[\s\S]*?_guiaDemoVisualLimpar\(\)/.test(game));
  check("rótulos da prévia têm português e inglês", lang.includes('ui.tutorial.demonstracao.previsualizando')
    && lang.includes('ui.tutorial.demonstracao.sem_origem'));
}

console.log(`\n${PASS} ok, ${FAIL} falha(s)`);
process.exit(FAIL ? 1 : 0);
