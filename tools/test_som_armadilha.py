"""Aviso público `armadilha_disparo` (som da explosão da Mina Terrestre).
O trap_result é privado de quem foi atingido; o disparo de uma armadilha de
área precisa chegar à sala inteira — inclusive quando quem pisa é um monstro.
Roda da raiz: python tools/test_som_armadilha.py"""
import asyncio, sys, os
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import GameRoom, make_player, make_monster

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print("  ✅", name)
    else: FAIL += 1; print("  ❌", name)

def setup():
    r = GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.push_state = noop; r._broadcast_dado = noop
    r.tiles = [[server.FLOOR] * server.MAP_W for _ in range(server.MAP_H)]
    r.phase = "playing"
    r.pub = []; r.priv = []
    async def bc(msg, *a, **k): r.pub.append(msg)
    async def st(pid, msg): r.priv.append((pid, msg))
    r.broadcast = bc; r.send_to = st
    return r

def disparos(r):
    return [m for m in r.pub if m.get("type") == "armadilha_disparo"]

def rng(d20):
    return lambda a, b: d20 if b == 20 else 3

async def main():
    print("\n[1] Monstro pisa na mina do Luccas → aviso público")
    r = setup()
    m = make_monster(next(d for d in server.MONSTER_DEFS if d["type"] == "goblin"), {"id": 1, "cx": 5, "cy": 5}); m["pos"] = [5, 5]; r.monsters = {m["id"]: m}
    arm = {"id": "a1", "tipo": "mina_terrestre", "pos": [5, 5], "ativada": False, "aliada": True}
    r.armadilhas = [arm]
    _o = server.random.randint; server.random.randint = rng(2)
    await r._disparar_armadilha(m, arm)
    server.random.randint = _o
    d = disparos(r)
    check("um único armadilha_disparo", len(d) == 1)
    check("tipo_id e posição da mina", d and d[0]["tipo_id"] == "mina_terrestre" and d[0]["pos"] == [5, 5])
    check("sem herói atingido, nenhum trap_result privado", not [x for x in r.priv if x[1].get("type") == "trap_result"])

    print("\n[2] Herói escapa (metade do dano) → explosão soa mesmo assim")
    r = setup()
    p = make_player("p1", "A", "rogue", 0); p["pos"] = [5, 5]; r.players = {"p1": p}
    arm = {"id": "a2", "tipo": "mina_terrestre", "pos": [5, 5], "ativada": False}
    r.armadilhas = [arm]
    _o = server.random.randint; server.random.randint = rng(19)
    await r._disparar_armadilha(p, arm)
    server.random.randint = _o
    tr = [x[1] for x in r.priv if x[1].get("type") == "trap_result"]
    check("herói resistiu com metade do dano", tr and tr[0]["metade"] is True and tr[0]["dano"] > 0)
    check("disparo público enviado uma vez", len(disparos(r)) == 1)
    ordem = [x.get("type") for x in r.pub if x.get("type") in ("armadilha_disparo", "dice_roll")]
    check("aviso sai antes das rolagens de save", ordem and ordem[0] == "armadilha_disparo")

    print("\n[3] Soldado arremessa granada → aviso público item_impacto")
    for iid in ("granada", "granada_superior"):
        r = setup()
        p = make_player("p1", "A", "warrior", 0); p["pos"] = [5, 5]; r.players = {"p1": p}
        sold = make_monster(next(d for d in server.MONSTER_DEFS if d["type"] == "goblin"), {"id": 1, "cx": 2, "cy": 5})
        sold["pos"] = [2, 5]; r.monsters = {sold["id"]: sold}
        r._tem_linha_de_visao = lambda *a, **k: True
        _o = server.random.randint; server.random.randint = rng(2)
        await r._monster_throw_item(sold, {"obj": p, "kind": "player"}, {"id": iid})
        server.random.randint = _o
        ii = [m for m in r.pub if m.get("type") == "item_impacto"]
        check(f"{iid}: um item_impacto na casa do alvo", len(ii) == 1 and ii[0]["item_id"] == iid and ii[0]["pos"] == [5, 5])

    print("\n[4] Herói arremessa granada → o feedback leva o item_id (o cliente toca no impact)")
    r = setup()
    p = make_player("p1", "A", "rogue", 0); p["pos"] = [5, 5]; r.players = {"p1": p}
    item = {"id": "granada", "name": "Granada Explosiva", "emoji": "💣", "item_slot": "bag", "effect": "throwable"}
    p["bag"] = [item]
    r._tem_linha_de_visao = lambda *a, **k: True
    await r._throw_item_area(p, server.ARREMESSAVEIS["granada"], item, 7, 5)
    st = [m for m in r.pub if m.get("type") == "attack_feedback" and m.get("phase") == "start"]
    check("start com projectile item granada", bool(st) and (st[0].get("projectile") or {}).get("item_id") == "granada")

    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
