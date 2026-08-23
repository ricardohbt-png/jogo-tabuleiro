"""Testes das armadilhas de teletransporte, dardos e baú-armadilha."""
import asyncio, os, sys

try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server import GameRoom, FLOOR, make_player

PASS = FAIL = 0
def check(name, ok):
    global PASS, FAIL
    if ok: PASS += 1; print("  OK ", name)
    else: FAIL += 1; print("  XX ", name)

def setup():
    r = GameRoom("TRAP")
    async def noop(*a, **k): pass
    r.gm_say = r.broadcast = r.send_to = r.push_state = noop
    r.tiles = [[FLOOR] * 7 for _ in range(7)]
    r.map_w = r.map_h = 7
    p = make_player("p1", "Herói", "warrior", 0)
    p["pos"] = [1, 1]
    r.players[p["id"]] = p
    return r, p

async def main():
    print("\n[teletransporte]")
    r, p = setup()
    r._testar_save = lambda *a: (False, 1, 0, 1)
    arm = {"id":"t1", "tipo":"armadilha_teletransporte", "saida":[4,4]}
    used = await r._disparar_teletransporte(p, arm, {"nome":"Armadilha de Teletransporte", "icone":"🌀", "descricao":""})
    check("falha teleporta para saída livre", used and p["pos"] == [4,4])

    r, p = setup(); r._testar_save = lambda *a: (False, 1, 0, 1)
    ocupante = make_player("p2", "Outro", "warrior", 0); ocupante["pos"] = [4,4]; r.players["p2"] = ocupante
    used = await r._disparar_teletransporte(p, {"id":"t2", "tipo":"armadilha_teletransporte", "saida":[4,4]}, {"nome":"Armadilha de Teletransporte", "icone":"🌀", "descricao":""})
    check("saída ocupada usa adjacente livre", used and p["pos"] != [4,4] and max(abs(p["pos"][0]-4), abs(p["pos"][1]-4)) == 1)

    r, p = setup(); r._testar_save = lambda *a: (True, 20, 0, 20)
    used = await r._disparar_teletransporte(p, {"id":"t3", "tipo":"armadilha_teletransporte", "saida":[4,4]}, {"nome":"Armadilha de Teletransporte", "icone":"🌀", "descricao":""})
    check("sucesso mantém armadilha ativa", not used and p["pos"] == [1,1])

    print("\n[baú-armadilha]")
    r, p = setup(); r._testar_save = lambda *a: (True, 20, 0, 20)
    d = {"id":"d1", "chest_trap_monster_type":"goblin_combatente", "chest_trap_triggered":False}
    await r._disparar_bau_armadilha(p["id"], p, d)
    check("primeiro clique marca a armadilha", d["chest_trap_triggered"])
    check("surge monstro adjacente", len(r.monsters) == 1 and max(abs(next(iter(r.monsters.values()))["pos"][0]-1), abs(next(iter(r.monsters.values()))["pos"][1]-1)) == 1)
    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    return FAIL

if __name__ == "__main__": sys.exit(asyncio.run(main()))
