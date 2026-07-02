"""Especializações do Paladino (Fase 1c). Roda da raiz: python tools/test_paladino_espec.py"""
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

def paladin(**owned):
    p = make_player("r", "Richard", "paladin", 0)
    p["guild_owned"]["especializacoes"] = list(owned.get("esp", []))
    p["pos"] = [0, 0]
    return p

async def main():
    # [1] Catálogo
    print("\n[1] Catálogo do Paladino")
    ids = [i["id"] for i in S.guild_items_for_class("paladin")]
    for eid in ["paladino_cura_maos_2","paladino_cura_maos_3","paladino_ataque_sagrado_2",
                "paladino_luz_2","paladino_luz_3","paladino_defensor_2","paladino_defensor_3",
                "paladino_regen_2","paladino_regen_3"]:
        check(f"catálogo tem {eid}", eid in ids)
    check("cura_maos_3 requer _2", S.guild_item("paladino_cura_maos_3")["requer"] == "paladino_cura_maos_2")
    check("ataque_sagrado_2 sem requer", S.guild_item("paladino_ataque_sagrado_2")["requer"] is None)
    check("luz_3 requer luz_2", S.guild_item("paladino_luz_3")["requer"] == "paladino_luz_2")
    check("preço II = 150", S.guild_item("paladino_defensor_2")["preco"] == 150)
    check("preço III = 200", S.guild_item("paladino_regen_3")["preco"] == 200)

    print(f"\n{'='*40}\n  {PASS} passaram, {FAIL} falharam\n{'='*40}")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
