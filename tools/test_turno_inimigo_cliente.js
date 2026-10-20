// Velocidade do turno dos inimigos — estado no cliente (gameState.js real).
// Roda da raiz: node tools/test_turno_inimigo_cliente.js
const fs = require("fs"), path = require("path");
const raiz = path.join(__dirname, "..");
let PASS = 0, FAIL = 0;
const check = (n, c) => { if (c) { PASS++; console.log("  ✅ " + n); } else { FAIL++; console.log("  ❌ " + n); } };

let sock = null; const enviados = [];
global.WebSocket = class { constructor() { this.readyState = 1; sock = this; } send(d) { enviados.push(JSON.parse(d)); } close() {} };
global.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
global.location = { search: "", protocol: "http:", host: "x" };
global.setTimeout = () => 0; global.clearTimeout = () => {};
const GS = eval(fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8") + "; GS");
GS.connect("ws://x", "Ana", "create");
const chegar = m => sock.onmessage({ data: JSON.stringify(m) });
const ultimo = () => enviados[enviados.length - 1];
const gs = extra => Object.assign({ type: "game_state", players: [], monsters: [], explored: [], round: 1, phase: "playing" }, extra);

console.log("[1] Leitura da escolha");
check("sem estado, o padrão é 'atual'", GS.velocidadeInimigos === "atual" && GS.ritmoAutoSegundos === 0);
chegar(gs({ velocidade_inimigos: "lento", ritmo_auto_segundos: 0 }));
check("lê do game_state", GS.velocidadeInimigos === "lento");
chegar({ type: "city_state", phase: "city", players: [], velocidade_inimigos: "passo", ritmo_auto_segundos: 6 });
check("lê do city_state", GS.velocidadeInimigos === "passo" && GS.ritmoAutoSegundos === 6);

console.log("\n[2] Envio");
GS.setVelocidadeInimigos("muito_lento", 0);
check("setVelocidadeInimigos envia nível e tempo", ultimo().type === "set_velocidade_inimigos"
  && ultimo().nivel === "muito_lento" && ultimo().auto_segundos === 0);
GS.setVelocidadeInimigos("passo", 10);
check("com tempo automático", ultimo().nivel === "passo" && ultimo().auto_segundos === 10);

console.log("\n[3] Mensagens do turno dos inimigos");
chegar(gs({ velocidade_inimigos: "passo" }));
let agindo = [], resumos = [];
GS.on("turnoInimigo", () => agindo.push(GS.turnoInimigo().agindo));
GS.on("resumoInimigo", () => resumos.push(GS.turnoInimigo().resumo));
chegar({ type: "turno_inimigo_agindo", monstro_id: "m1", proximos: ["m2"] });
check("guarda o monstro agindo e os próximos", GS.turnoInimigo().agindo === "m1"
  && GS.turnoInimigo().proximos.join() === "m2");
check("emite turnoInimigo", agindo.length === 1 && agindo[0] === "m1");
const faixa = { type: "resumo_ataque_inimigo", monstro_id: "m1", generico: false, atacante_nome: "Orc",
  ataques: [{ alvo_nome: "Ana", ataque: "Machado", acertou: true, dano: 4 }], espera: "clique", segundos: 0 };
chegar(faixa);
check("guarda o resumo", GS.turnoInimigo().resumo.atacante_nome === "Orc" && GS.turnoInimigo().resumo.ataques.length === 1);
check("emite resumoInimigo", resumos.length === 1 && resumos[0].espera === "clique");
chegar(gs({ round: 2, velocidade_inimigos: "passo" }));
check("um game_state novo não apaga o resumo em curso", GS.turnoInimigo().resumo !== null);
chegar({ type: "resumo_inimigo_fechado" });
check("resumo_inimigo_fechado limpa o resumo", GS.turnoInimigo().resumo === null && resumos.length === 2 && resumos[1] === null);
chegar({ type: "turno_inimigo_agindo", monstro_id: null, proximos: [] });
check("anel apagado", GS.turnoInimigo().agindo === null);

console.log("\n[4] Continuar");
chegar(faixa);
GS.continuarTurnoInimigo();
check("envia continuar_turno_inimigo", ultimo().type === "continuar_turno_inimigo");
check("e some com a faixa na hora, sem esperar o servidor", GS.turnoInimigo().resumo === null);

console.log("\n[5] Saída da masmorra e fim de jogo limpam tudo");
chegar({ type: "turno_inimigo_agindo", monstro_id: "m1", proximos: [] }); chegar(faixa);
chegar({ type: "city_state", phase: "city", players: [] });
check("city_state limpa", GS.turnoInimigo().agindo === null && GS.turnoInimigo().resumo === null);
chegar(gs({})); chegar({ type: "turno_inimigo_agindo", monstro_id: "m1", proximos: [] }); chegar(faixa);
chegar({ type: "enter_dungeon", players: [] });
check("enter_dungeon limpa", GS.turnoInimigo().agindo === null && GS.turnoInimigo().resumo === null);
chegar({ type: "turno_inimigo_agindo", monstro_id: "m1", proximos: [] }); chegar(faixa);
chegar({ type: "game_over", victory: false });
check("game_over limpa", GS.turnoInimigo().agindo === null && GS.turnoInimigo().resumo === null);

console.log(`\n=== ${PASS} passaram, ${FAIL} falharam ===`);
process.exit(FAIL ? 1 : 0);
