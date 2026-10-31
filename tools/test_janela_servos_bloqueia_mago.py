"""Na vez dos servos o mago não age mais; cada servo age na sua vez.

Roda da raiz:  python -X utf8 tools/test_janela_servos_bloqueia_mago.py

Encerrar o turno do mago abre a janela dos servos (animados_phase_pid). A
iniciativa ainda aponta para o mago nessa janela, então _is_turn(pid) dava
True e o mago podia andar, atacar e lançar magia com o movimento que sobrou.
Agora o turno do herói acabou: só os servos (e o refém liberto) agem até a
janela fechar. Um servo que encerrou a vez não age de novo.
"""
import asyncio, os, sys
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


async def montar():
    """Corredor 8×3: mago p1 em (1,1) com dois esqueletos; p2 longe."""
    r = S.GameRoom("JANELA_SERVOS")
    async def noop(*a, **k): pass
    r.broadcast = noop; r.send_to = noop
    r.players["p1"] = S.make_player("p1", "Pedro", "mage", 0)
    r.players["p2"] = S.make_player("p2", "Bia", "rogue", 1)
    r.phase = "city"; r.host_pid = "p1"
    await r.enter_dungeon("p1")
    r.monsters.clear()
    r.dungeon_intro_active = False
    r._intro_masmorra_bloqueada = lambda: False
    r.erros = []
    async def send_to(pid, msg):
        if msg.get("type") == "error": r.erros.append(str(msg.get("msg")))
    async def push_state(): pass
    r.send_to = send_to; r.push_state = push_state
    r.map_w, r.map_h = 8, 3
    r.tiles = [[S.FLOOR] * 8 for _ in range(3)]
    r.decorations = []
    r._decor_block_tiles = set(); r._decor_tall_tiles = set(); r._decor_low_tiles = set()
    r._mat_solid_tiles = set()
    r.traps = []; r.armadilhas = []
    r.prisoner = None
    # A vez é do mago (p1), pela iniciativa de verdade.
    r.current_actor = lambda: {"kind": "player", "id": "p1"}
    p1, p2 = r.players["p1"], r.players["p2"]
    p1.update({"pos": [1, 1], "moves_left": 6, "action_done": False, "facing": [1, 0]})
    p2.update({"pos": [7, 0], "moves_left": 6})
    for i, x in ((1, 3), (2, 5)):
        p1.setdefault("animados", []).append({
            "id": f"a{i}", "owner": "p1", "pos": [x, 1], "vida_atual": 8, "vida_max": 8,
            "movimento": 6, "moves_left": 6, "tipo": "skeleton", "nome": f"Esqueleto {i}",
            "porte": "medio", "acted": False, "dex": 10 + i})
    r._advance_initiative = noop
    return r


async def main():
    print("\n[1] Antes de encerrar: o mago ainda age")
    r = await montar()
    check("é a vez do mago", r._is_turn("p1"))
    await r.handle_move("p1", 0, -1)
    check("mago anda no próprio turno", r.players["p1"]["pos"] == [1, 0], r.erros)

    print("\n[2] Encerrou: abre a janela dos servos e o mago não age mais")
    r = await montar()
    p1 = r.players["p1"]
    await r.handle_end_turn("p1")
    check("janela dos servos aberta", r.animados_phase_pid == "p1")
    check("sobrou movimento ao mago (é o caso do bug)", p1["moves_left"] > 0, p1["moves_left"])
    await r.handle_move("p1", 0, -1)
    check("mago não anda na vez dos servos", p1["pos"] == [1, 1], p1["pos"])
    await r.handle_move_path("p1", [[0, -1], [1, 0]])
    check("nem por caminho", p1["pos"] == [1, 1], p1["pos"])
    check("ações do herói recusadas no turno dos servos",
          not r._is_turn("p1") and r._is_turn_servos("p1"))

    print("\n[3] Cada servo age na sua vez; quem encerrou não volta a agir")
    atual = r._animados_atual("p1")
    check("o primeiro servo da fila está na vez", atual in ("a1", "a2"), atual)
    a_atual = next(a for a in p1["animados"] if a["id"] == atual)
    pos = list(a_atual["pos"])
    await r.handle_mover_animado("p1", atual, 0, -1)
    check("o servo da vez anda", a_atual["pos"] == [pos[0], pos[1] - 1], r.erros)
    await r.handle_encerrar_animado("p1", atual)
    proximo = r._animados_atual("p1")
    check("a vez passa ao próximo servo", proximo not in (None, atual), proximo)
    pos = list(a_atual["pos"])
    await r.handle_mover_animado("p1", atual, 0, 1)
    check("o servo que encerrou não anda mais", a_atual["pos"] == pos, a_atual["pos"])
    await r.handle_move("p1", 0, -1)
    check("o mago continua sem agir", p1["pos"] == [1, 1], p1["pos"])

    print("\n[4] Último servo encerra: a janela fecha")
    await r.handle_encerrar_animado("p1", proximo)
    check("janela fechada", r.animados_phase_pid is None)

    print("\n[5] Ordem estrita: só o servo da vez age")
    r = await montar()
    p1 = r.players["p1"]
    await r.handle_end_turn("p1")
    atual = r._animados_atual("p1")
    outro = next(a for a in p1["animados"] if a["id"] != atual)
    pos = list(outro["pos"])
    r.erros.clear()
    await r.handle_mover_animado("p1", outro["id"], 0, -1)
    check("servo fora da vez não anda", outro["pos"] == pos, outro["pos"])
    check("recusa explicada", any("vez" in e.lower() or "turn" in e.lower() for e in r.erros), r.erros)
    await r.handle_mover_animado_caminho("p1", outro["id"], [[0, -1], [0, 1]])
    check("nem por caminho", outro["pos"] == pos, outro["pos"])
    outro["acted"] = False
    r.monsters["m1"] = {"id": "m1", "type": "goblin", "hp": 5, "max_hp": 5, "pos": [outro["pos"][0] + 1, 1],
                        "ac": 1}
    hp = r.monsters["m1"]["hp"]
    await r.handle_atacar_animado("p1", outro["id"], "m1")
    check("servo fora da vez não ataca", r.monsters["m1"]["hp"] == hp and not outro.get("acted"))
    await r.handle_encerrar_animado("p1", outro["id"])
    check("encerrar o servo fora da vez é recusado", r._animados_atual("p1") == atual
          and outro["id"] not in r.animados_done, r.animados_done)

    print(f"\n{PASS} ok, {FAIL} falha(s)")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
