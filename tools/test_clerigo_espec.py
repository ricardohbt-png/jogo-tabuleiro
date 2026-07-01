"""Especializações do Clérigo (Fase 1b). Roda da raiz: python tools/test_clerigo_espec.py"""
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
    r._no_raio = lambda *a, **k: True
    r._tem_linha_de_visao = lambda *a, **k: True
    r.phase = phase; r._errs = errs
    return r

def cleric(**owned):
    p = make_player("c", "Lewis", "cleric", 0)
    p["guild_owned"]["especializacoes"] = list(owned.get("esp", []))
    return p

async def main():
    # [1] Catálogo
    print("\n[1] Catálogo do Clérigo")
    ids = [i["id"] for i in S.guild_items_for_class("cleric")]
    for eid in ["clerigo_cura_2","clerigo_cura_3","clerigo_massa_2","clerigo_massa_3",
                "clerigo_purif_2","clerigo_purif_3","clerigo_ressur_2","clerigo_ressur_3"]:
        check(f"catálogo tem {eid}", eid in ids)
    check("cura_3 requer cura_2", S.guild_item("clerigo_cura_3")["requer"] == "clerigo_cura_2")
    check("massa_2 sem requer", S.guild_item("clerigo_massa_2")["requer"] is None)
    check("ressur_3 requer ressur_2", S.guild_item("clerigo_ressur_3")["requer"] == "clerigo_ressur_2")
    check("preço II = 150", S.guild_item("clerigo_cura_2")["preco"] == 150)
    check("preço III = 200", S.guild_item("clerigo_purif_3")["preco"] == 200)

    print(f"\n{'='*40}\n  {PASS} passaram, {FAIL} falharam\n{'='*40}")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
