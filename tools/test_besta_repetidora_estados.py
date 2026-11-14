"""Disparo Duplo da Besta Repetidora respeita os estados que impedem agir.

As habilidades irmas de arma (Rajada do Vendaval, Pulso do Trovao...) recusam
petrificado/paralisado/dormindo; a Besta Repetidora nao recusava e o heroi
atirava duas vezes mesmo assim.
Roda da raiz: python -X utf8 tools/test_besta_repetidora_estados.py
"""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

FALHAS = []
def check(c, m):
    print(("  ok   " if c else "  FALHA ") + m)
    if not c: FALHAS.append(m)

async def nada(*a, **k): return None

def cena(estado):
    r = S.GameRoom("REP")
    r.gm_say = nada; r.push_state = nada; r.broadcast = nada
    enviados = []
    async def send(pid, msg): enviados.append(msg)
    r.send_to = send
    r.phase = "playing"; r.map_w = r.map_h = 12
    r.tiles = [[S.FLOOR]*12 for _ in range(12)]
    r.rooms = [{"id":0,"x":0,"y":0,"w":12,"h":12,"cx":5,"cy":5,"locked":False,"doors":[]}]
    p = S.make_player("p1", "Teste", "warrior", 0)
    p["pos"] = [2, 2]; p["alive"] = True
    arma = dict(S.WEAPONS["besta_repetidora_guerra"])
    p["gear"]["weapon"] = dict(arma); p["weapon"] = dict(arma)
    p["gear"]["off_hand"] = {"id": "virotes", "effect": "ammo", "ammo_type": "virotes",
                             "ammo_count": 10, "name": "Virotes"}
    if estado == "cego":
        p["cego"] = True; p["bloqueia_distancia"] = True
    elif estado: p[estado] = True
    g = S.make_monster(next(d for d in S.MONSTER_DEFS if d["type"] == "goblin"), r.rooms[0])
    g["id"] = "g"; g["pos"] = [2, 5]; g["hp"] = g["max_hp"] = 999; g["ac"] = -50
    r.players = {"p1": p}; r.monsters = {"g": g}
    r.round_num = 1
    r._is_turn = lambda pid: True
    return r, p, g, enviados

for estado in ("petrificado", "paralisado", "dormindo", "cego"):
    r, p, g, env = cena(estado)
    asyncio.run(r.handle_repeating_crossbow_weapon("p1", "g", [2, 5]))
    check(g["hp"] == 999 and not p.get("action_done"), f"{estado}: nao atira ({g['hp']}/999)")

r, p, g, env = cena(None)
asyncio.run(r.handle_repeating_crossbow_weapon("p1", "g", [2, 5]))
check(g["hp"] < 999, f"sem estado: atira normalmente (PV {g['hp']})")
print()
sys.exit(1 if FALHAS else 0)
