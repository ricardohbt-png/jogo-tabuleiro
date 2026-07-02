"""Especializações do Ladino (Fase 1d). Roda da raiz: python tools/test_ladino_espec.py"""
import asyncio, sys, os
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom, make_player

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def setup(phase="playing"):
    r = GameRoom("TEST")
    errs = []
    async def noop(*a, **k): pass
    async def cap_send(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error": errs.append(msg.get("msg",""))
    r.gm_say = noop; r.broadcast = noop; r._broadcast_dado = noop
    r.broadcast_city_state = noop; r.push_state = noop; r.send_to = cap_send
    r._is_turn = lambda pid: True
    r._no_raio = lambda p, alvo, raio, *a, **k: max(abs(p["pos"][0]-alvo["pos"][0]), abs(p["pos"][1]-alvo["pos"][1])) <= raio
    r._tem_linha_de_visao = lambda *a, **k: True
    r.phase = phase; r._errs = errs
    return r

def rogue(**owned):
    p = make_player("l", "Luccas", "rogue", 0)
    p["guild_owned"]["especializacoes"] = list(owned.get("esp", []))
    p["pos"] = [0, 0]
    return p

def monster(mid="m1", pos=(0,1), hp=20):
    return {"id": mid, "name": "Goblin", "pos": list(pos), "hp": hp, "max_hp": hp, "ac": 10}

async def main():
    # [1] Catálogo — 8 nós literais
    print("\n[1] Catálogo do Ladino (literais)")
    ids = [i["id"] for i in S.guild_items_for_class("rogue")]
    for eid in ["ladino_furtivo_2","ladino_furtivo_3","ladino_desarme_2","ladino_desarme_3",
                "ladino_veneno_2","ladino_veneno_3","ladino_esconder_2","ladino_esconder_3"]:
        check(f"catálogo tem {eid}", eid in ids)
    check("furtivo_3 requer furtivo_2", S.guild_item("ladino_furtivo_3")["requer"] == "ladino_furtivo_2")
    check("desarme_2 sem requer", S.guild_item("ladino_desarme_2")["requer"] is None)
    check("veneno_3 requer veneno_2", S.guild_item("ladino_veneno_3")["requer"] == "ladino_veneno_2")
    check("esconder_3 requer esconder_2", S.guild_item("ladino_esconder_3")["requer"] == "ladino_esconder_2")
    check("preço II = 150", S.guild_item("ladino_furtivo_2")["preco"] == 150)
    check("preço III = 200", S.guild_item("ladino_esconder_3")["preco"] == 200)

    # [2] Fórmulas de armadilha (geradas)
    print("\n[2] Fórmulas de armadilha")
    ids = [i["id"] for i in S.guild_items_for_class("rogue")]
    for eid, preco in [("ladino_armadilha_urso",100), ("ladino_fosso_estacas",120),
                        ("ladino_fosso_envenenado",130), ("ladino_rede",150),
                        ("ladino_armadilha_incendiaria",180), ("ladino_mina_terrestre",220),
                        ("ladino_nuvem_gas",250)]:
        check(f"catálogo tem {eid}", eid in ids)
        check(f"{eid} preço {preco}", S.guild_item(eid)["preco"] == preco)
    check("buraco não vira nó de compra", "ladino_buraco" not in ids and
          not any(v.get("nome","").endswith("Buraco") for v in S.GUILD_CATALOG.values()))

    print(f"\n{'='*40}\n  {PASS} passaram, {FAIL} falharam\n{'='*40}")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
