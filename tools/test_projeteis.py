"""Projéteis (frente B): campo `projectile` no attack_feedback e emissão no arremesso.
Roda da raiz: python -X utf8 tools/test_projeteis.py"""
import asyncio, sys, os, random
from copy import deepcopy
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def sala():
    """Sala mínima que CAPTURA os broadcasts (a frente A só os silenciava)."""
    r = S.GameRoom("TEST")
    r._msgs = []
    async def cap(msg, *a, **k):
        if isinstance(msg, dict): r._msgs.append(msg)
    async def noop(*a, **k): pass
    r.broadcast = cap; r.gm_say = noop; r.push_state = noop
    r.broadcast_city_state = noop; r.send_to = noop
    r._is_turn = lambda pid: True
    r._tem_linha_de_visao = lambda *a, **k: True
    r.phase = "playing"
    r.map_w = 14; r.map_h = 14
    r.tiles = [[S.FLOOR]*14 for _ in range(14)]
    r.rooms = [{"id": "r0", "x": 0, "y": 0, "w": 14, "h": 14, "cx": 7, "cy": 7, "locked": False}]
    r.monsters = {}; r.chests = {}; r.ground_items = {}
    p = S.make_player("p1", "Victor", "warrior", 0); r.players["p1"] = p
    p["pos"] = [1, 1]; p["atk_bonus"] = 50; p["alive"] = True; p["connected"] = True
    r.connections["p1"] = object()
    r.monsters["m1"] = {"id": "m1", "name": "Alvo", "type": "orc", "hp": 999, "ac": 1,
                        "pos": [4, 1], "alive": True, "special_abilities": [],
                        "alertado": True, "room_id": "r0"}
    return r, p

def feedbacks(r, fase="start"):
    return [m for m in r._msgs if m.get("type") == "attack_feedback" and m.get("phase") == fase]

def test_helper():
    print("\n[1] _projetil_de")
    check("arco_curto → arrow", S._projetil_de({"id": "arco_curto", "range": 6, "categoria": "perfurante"}) == {"kind": "arrow"})
    check("longbow → arrow",    S._projetil_de({"id": "longbow"}) == {"kind": "arrow"})
    check("besta → bolt",       S._projetil_de({"id": "besta"}) == {"kind": "bolt"})
    check("hand_crossbow → bolt", S._projetil_de({"id": "hand_crossbow"}) == {"kind": "bolt"})
    check("chicote (range 2, sem projétil) → None", S._projetil_de({"id": "chicote", "range": 2, "categoria": "cortante"}) is None)
    check("alabarda (range 2 perfurante, HERÓI) → None", S._projetil_de({"id": "alabarda", "range": 2, "categoria": "perfurante"}) is None)
    check("arma do editor com ammo virotes → bolt", S._projetil_de({"id": "besta_custom_x", "ammo": "virotes", "range": 5}) == {"kind": "bolt"})
    check("arma do editor com ammo flechas → arrow", S._projetil_de({"id": "arco_custom_x", "ammo": "flechas", "range": 5}) == {"kind": "arrow"})
    check("monstro: range≥2 perfurante → arrow", S._projetil_de({"name": "Arco", "range": 8, "categoria": "perfurante"}, monstro=True) == {"kind": "arrow"})
    check("monstro: range≥2 não-perfurante (cuspe) → None", S._projetil_de({"name": "Cuspe", "range": 4, "categoria": "acido"}, monstro=True) is None)
    check("monstro: range 1 → None", S._projetil_de({"name": "Garras", "range": 1, "categoria": "perfurante"}, monstro=True) is None)
    check("monstro: campo projectile sobrepõe", S._projetil_de({"name": "Besta", "range": 4, "projectile": "bolt"}, monstro=True) == {"kind": "bolt"})
    check("projectile inválido é ignorado", S._projetil_de({"name": "X", "range": 4, "projectile": "laser"}, monstro=True) is None)
    check("None/vazio → None", S._projetil_de(None) is None and S._projetil_de({}) is None)
    kb = next(d for d in S.MONSTER_DEFS if d.get("type") == "kobold_besteiro")
    check("ficha kobold_besteiro declara projectile bolt", kb["attacks"][0].get("projectile") == "bolt")

def test_sites():
    print("\n[2] Campo projectile nos sites de start")
    r, p = sala()
    p["weapon"] = {"id": "arco_curto", "name": "Arco Curto", "die": "1d6", "stat": "dex", "range": 6, "categoria": "perfurante"}
    p["gear"]["off_hand"] = {"id": "flechas", "name": "Flechas", "effect": "ammo", "ammo_type": "flechas", "ammo_count": 10}   # arco exige munição
    random.seed(7)
    asyncio.run(r.handle_attack("p1", "m1"))
    st = feedbacks(r)
    check("herói com arco: start emitido", len(st) == 1)
    check("herói com arco: projectile arrow", st and st[0].get("projectile") == {"kind": "arrow"})
    check("result não carrega projectile", all("projectile" not in m for m in feedbacks(r, "result")))

    r, p = sala(); r._msgs.clear()
    p["weapon"] = {"id": "espada", "name": "Espada", "die": "1d8", "stat": "str_", "categoria": "cortante"}
    r.monsters["m1"]["pos"] = [2, 1]
    asyncio.run(r.handle_attack("p1", "m1"))
    st = feedbacks(r)
    check("herói corpo a corpo: start sem a chave projectile", st and "projectile" not in st[0])

    r, p = sala(); r._msgs.clear()
    mdef = next(d for d in S.MONSTER_DEFS if d.get("type") == "goblin_arqueiro")
    m = S.make_monster(mdef, r.rooms[0]); m["id"] = "g1"; m["pos"] = [6, 1]; m["room_id"] = "r0"; m["alertado"] = True
    r.monsters["g1"] = m
    atk = dict(m["attacks"][0])
    asyncio.run(r._execute_one_monster_attack(m, atk, {"kind": "player", "obj": p}))
    st = feedbacks(r)
    check("goblin arqueiro: start com arrow", st and st[-1].get("projectile") == {"kind": "arrow"})

    r, p = sala(); r._msgs.clear()
    mdef = next(d for d in S.MONSTER_DEFS if d.get("type") == "kobold_besteiro")
    m = S.make_monster(mdef, r.rooms[0]); m["id"] = "k1"; m["pos"] = [4, 1]; m["room_id"] = "r0"; m["alertado"] = True
    r.monsters["k1"] = m
    asyncio.run(r._execute_one_monster_attack(m, dict(m["attacks"][0]), {"kind": "player", "obj": p}))
    st = feedbacks(r)
    check("kobold besteiro: start com bolt", st and st[-1].get("projectile") == {"kind": "bolt"})

if __name__ == "__main__":
    print("=" * 60); print("  TESTE — Projéteis (frente B)"); print("=" * 60)
    test_helper()
    test_sites()
    print("\n" + "=" * 60)
    print(f"  {PASS} passaram, {FAIL} falharam")
    print("=" * 60)
    sys.exit(1 if FAIL else 0)
