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

async def main():
    await test_instanciar()
    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
