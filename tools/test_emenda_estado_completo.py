"""Etapa emendada (Casa → Fazenda, Salões → Trono do Troll) não deixa a tela preta.

Roda da raiz:  python -X utf8 tools/test_emenda_estado_completo.py

Ao receber `enter_dungeon` o cliente descarta o gameState. Vindo da cidade o
servidor também já tinha zerado o registro do que cada conexão recebeu (o
`broadcast_city_state` faz isso), mas a emenda não passa pela cidade: o
servidor seguia mandando só as diferenças em relação ao mapa anterior, o
cliente sem estado pedia o completo e, no Solo com grupo, esse pedido saía
com o herói em foco (um extra, sem conexão própria), de modo que o registro
nunca era limpo. Resultado: laço de pedidos e tela preta.

Aqui o gameState.js REAL recebe tudo o que a conexão recebeu numa emenda real.
"""
import asyncio, json, os, subprocess, sys, tempfile
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S

PASS = FAIL = 0
def check(label, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {label}")
    else:    FAIL += 1; print(f"  ❌ {label}" + (f"\n     {extra}" if extra else ""))


class Cliente:
    def __init__(self): self.msgs = []
    async def send(self, data): self.msgs.append(json.loads(data))


def alimentar(msgs):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(msgs, f); nome = f.name
    try:
        out = subprocess.run(["node", os.path.join(RAIZ, "tools", "_estado_delta_node.js"), nome],
                             capture_output=True, text=True, encoding="utf-8", timeout=120)
        assert out.returncode == 0, out.stderr[-500:]
        return json.loads(out.stdout)
    finally:
        os.unlink(nome)


async def emenda(aventura):
    r = S.GameRoom("EMENDA")
    cli = Cliente()
    r.players["p1"] = S.make_player("p1", "Richard", "paladin", 0)
    r.players["p2"] = S.make_player("p2", "Lewis", "cleric", 1); r.players["p2"]["controlador"] = "p1"
    r.players["p3"] = S.make_player("p3", "Pedro", "mage", 2); r.players["p3"]["controlador"] = "p1"
    r.connections = {"p1": cli}
    r.phase = "city"; r.host_pid = "p1"; r.player_order = ["p1", "p2", "p3"]
    adv = S.WORLD_ADVENTURES[aventura]
    etapa0 = S._etapa_obj(adv["dungeons"][0])
    r.mode = "authored"; r.selected_dungeon = etapa0["file"]
    r.dungeon_def = S.carregar_dungeon(etapa0["file"])
    r.world_adventure_id = aventura; r.world_adventure_index = 0
    await r.enter_dungeon("p1", from_world_adventure=True)
    await r._liberar_intro_masmorra(True)
    for _ in range(3):
        await r.push_state()          # a conexão passa a receber só as diferenças
    r._objetivo_concluido = True; r.mission_complete_pending = True
    r._route_exits_complete = lambda: True
    await r.handle_encerrar_missao("p1")
    pend = r._pending_dungeon_entry
    if pend and pend.get("story_key"):
        await r.handle_story_complete("p1", pend["story_key"])
    await r._liberar_intro_masmorra(True)
    await r.push_state()
    return r, cli


async def main():
    print("\n[0] O pedido de estado completo é da conexão, não do herói em foco")
    check("pedir_estado_completo em MENSAGENS_DA_CONEXAO",
          "pedir_estado_completo" in S.MENSAGENS_DA_CONEXAO)

    for aventura, proxima in (("elara_parte1", "fazenda.json"), ("sombras_covil", "sombras_3b_trono.json")):
        print(f"\n[{aventura}] emenda até {proxima}")
        r, cli = await emenda(aventura)
        check("a sala está na etapa seguinte", r.selected_dungeon == proxima, r.selected_dungeon)
        res = alimentar(cli.msgs)
        tipos = [m.get("type") for m in cli.msgs]
        i_entrada = max(i for i, t in enumerate(tipos) if t == "enter_dungeon")
        depois = [(m, res[i]) for i, m in enumerate(cli.msgs) if i > i_entrada and m.get("type") == "game_state"]
        check("houve game_state depois da entrada", bool(depois))
        pediu = [i for i, (m, rr) in enumerate(depois) if rr["pediu"]]
        check("o cliente não precisou pedir o estado completo", not pediu,
              f"{len(pediu)} de {len(depois)} game_state descartados")
        ultimo = depois[-1][1]["estado"] if depois else None
        check("o cliente termina com o mapa novo",
              bool(ultimo) and ultimo.get("tiles") == r.tiles,
              "sem estado" if not ultimo else "mapa diferente")

    print(f"\n{PASS} ok, {FAIL} falha(s)")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
