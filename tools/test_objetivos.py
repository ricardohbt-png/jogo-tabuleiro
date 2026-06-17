"""Testes da Fase 3: objetivos, prisioneiro e saída (só masmorra autorada).
Roda da raiz: python tools/test_objetivos.py"""
import asyncio, sys, os, json
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import GameRoom, make_player

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def fixture():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(base, "dungeons", "test_fase3.json"), encoding="utf-8") as f:
        return json.load(f)

def setup_authored(defn=None):
    r = GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.send_to = noop
    r.broadcast_city_state = noop
    for pid, nome, cls in (("p1", "Victor", "warrior"), ("p2", "Pedro", "mage")):
        r.players[pid] = make_player(pid, nome, cls, 0)
    r.player_order = list(r.players.keys())
    r.host_pid = "p1"
    r.mode = "authored"; r.dungeon_def = defn or fixture()
    r.phase = "city"
    return r

async def test_instanciar():
    print("\n[1] carregador instancia exit/prisoner/objectives")
    r = setup_authored()
    await r.enter_dungeon("p1")
    check("exit_pos do arquivo", r.exit_pos == [14, 4])
    check("objectives carregados", r.objectives and r.objectives["primary"]["type"] == "rescue_prisoner")
    check("prisioneiro instanciado (cativo, vivo)",
          r.prisoner and r.prisoner["pos"] == [14, 1]
          and r.prisoner["freed"] is False and r.prisoner["alive"] is True)
    check("bau-chave marcado",
          any(c.get("key_objective") for c in r.chests.values()))
    check("rescue_failed comeca False", r.rescue_failed is False)

async def test_conclusao_simples():
    print("\n[2] conclusão por objetivo dispara end_game(victory)")

    async def cenario(primary_type, prep):
        r = setup_authored()
        d = r.dungeon_def
        d["objectives"] = {"primary": {"type": primary_type}, "secondary": []}
        await r.enter_dungeon("p1")
        vit = {"chamado": False, "victory": None}
        async def fake_end(victory): vit["chamado"] = True; vit["victory"] = victory
        r.end_game = fake_end
        await prep(r)
        await r._check_objectives()
        return r, vit

    # kill_all: mata todos
    async def mata_todos(r):
        for m in r.monsters.values(): m["hp"] = 0
    r, vit = await cenario("kill_all", mata_todos)
    check("kill_all → vitória", vit["chamado"] and vit["victory"] is True)

    # kill_all não conclui com monstro vivo
    r2 = setup_authored(); r2.dungeon_def["objectives"] = {"primary": {"type": "kill_all"}, "secondary": []}
    await r2.enter_dungeon("p1")
    vit2 = {"c": False}
    async def fe2(victory): vit2["c"] = True
    r2.end_game = fe2
    await r2._check_objectives()
    check("kill_all não conclui com monstros vivos", vit2["c"] is False)

    # kill_target: mata só o alvo
    async def mata_alvo(r):
        for m in r.monsters.values():
            if m.get("authored_target"): m["hp"] = 0
    r, vit = await cenario("kill_target", mata_alvo)
    check("kill_target (só o alvo morto) → vitória", vit["chamado"] is True)

    # reach_exit: herói na saída
    async def poe_na_saida(r):
        list(r.players.values())[0]["pos"] = list(r.exit_pos)
    r, vit = await cenario("reach_exit", poe_na_saida)
    check("reach_exit (herói na saída) → vitória", vit["chamado"] is True)

    # open_key_chest
    async def abre_chave(r):
        r.key_chest_opened = True
    r, vit = await cenario("open_key_chest", abre_chave)
    check("open_key_chest → vitória", vit["chamado"] is True)

async def test_prisioneiro():
    print("\n[3] prisioneiro: libertar, seguir, escolta, morte")
    r = setup_authored()
    r.dungeon_def["objectives"] = {"primary": {"type": "rescue_prisoner"}, "secondary": []}
    await r.enter_dungeon("p1")
    p1 = r.players["p1"]
    # herói adjacente ao prisioneiro cativo
    p1["pos"] = [r.prisoner["pos"][0] - 1, r.prisoner["pos"][1]]
    p1["action_done"] = False
    r.turn_index = r.player_order.index("p1")
    await r.handle_libertar_prisioneiro("p1")
    check("prisioneiro libertado por herói adjacente", r.prisoner["freed"] is True)
    check("libertar gastou a ação", p1["action_done"] is True)

    # escolta: prisioneiro junto da saída → rescue cumprido
    r.prisoner["pos"] = [r.exit_pos[0], r.exit_pos[1]]
    check("rescue cumprido perto da saída",
          r._objetivo_cumprido(r.objectives["primary"]) is True)

    # morte do prisioneiro → falha, sem encerrar.
    # Chama _processar_prisioneiro_turno direto (gm_phase moveria o monstro antes),
    # e neutraliza o passo de seguir p/ o prisioneiro não sair de perto do monstro.
    r2 = setup_authored()
    r2.dungeon_def["objectives"] = {"primary": {"type": "rescue_prisoner"}, "secondary": []}
    await r2.enter_dungeon("p1")
    r2.prisoner["freed"] = True; r2.prisoner["hp"] = 1
    vit = {"c": False}
    async def fe(victory): vit["c"] = True
    r2.end_game = fe
    r2._step_towards = lambda ent, dest: None       # isola: sem mover o prisioneiro
    m = next(iter(r2.monsters.values()))
    m["hp"] = 10; m["pos"] = [r2.prisoner["pos"][0] + 1, r2.prisoner["pos"][1]]   # adjacente
    await r2._processar_prisioneiro_turno()
    check("prisioneiro morto marca rescue_failed", r2.rescue_failed is True)
    check("morte do prisioneiro NÃO encerra a partida", vit["c"] is False)
    check("status do resgate = failed",
          r2._objetivo_status(r2.objectives["primary"]) == "failed")

async def test_bonus_secundario():
    print("\n[4] secundário cumprido concede bônus de XP/ouro")
    r = setup_authored()
    r.dungeon_def["objectives"] = {"primary": {"type": "kill_all"},
                                   "secondary": [{"type": "open_key_chest"}]}
    await r.enter_dungeon("p1")
    r.end_game = lambda victory=True: asyncio.sleep(0)  # não encerra de verdade
    p1 = r.players["p1"]
    xp0, ouro0 = p1["xp"], p1["gold"]
    # cumpre principal (kill_all) e secundário (open_key_chest)
    for m in r.monsters.values(): m["hp"] = 0
    r.key_chest_opened = True
    await r._check_objectives()
    check("XP do grupo subiu pelo secundário", p1["xp"] > xp0)
    check("ouro do grupo subiu pelo secundário", p1["gold"] > ouro0)

async def main():
    await test_instanciar()
    await test_conclusao_simples()
    await test_prisioneiro()
    await test_bonus_secundario()
    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
