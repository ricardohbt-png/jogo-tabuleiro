"""Especializações do Mago (Fase 1f). Roda da raiz: python tools/test_mago_espec.py"""
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
    r.phase = phase; r._errs = errs
    return r

def mage(**owned):
    p = make_player("m", "Pedro", "mage", 0)
    p["guild_owned"]["especializacoes"] = list(owned.get("esp", []))
    p["pos"] = [0, 0]; p["alive"] = True
    return p

# magia fake com dano + duração + save (para exercitar as 3 metamagias)
def magia_completa():
    return {"id": "fake", "dano_por_nivel": "1d6", "duracao": 3, "save": "reflexos"}

async def main():
    # [1] Catálogo do Mago
    print("\n[1] Catálogo do Mago")
    ids = [i["id"] for i in S.guild_items_for_class("mage")]
    for eid in ["mago_tecelagem_2","mago_tecelagem_3","mago_fortalecer_2","mago_fortalecer_3",
                "mago_aprimorar_2","mago_aprimorar_3","mago_estender_2","mago_estender_3"]:
        check(f"catálogo tem {eid}", eid in ids)
    check("tecelagem_2 = 150", S.guild_item("mago_tecelagem_2")["preco"] == 150)
    check("tecelagem_3 = 300", S.guild_item("mago_tecelagem_3")["preco"] == 300)
    check("fortalecer_2 = 200", S.guild_item("mago_fortalecer_2")["preco"] == 200)
    check("fortalecer_3 = 250", S.guild_item("mago_fortalecer_3")["preco"] == 250)
    check("aprimorar_2 = 150", S.guild_item("mago_aprimorar_2")["preco"] == 150)
    check("estender_2 = 150", S.guild_item("mago_estender_2")["preco"] == 150)
    check("tecelagem_3 requer _2", S.guild_item("mago_tecelagem_3")["requer"] == "mago_tecelagem_2")
    check("fortalecer_3 requer _2", S.guild_item("mago_fortalecer_3")["requer"] == "mago_fortalecer_2")
    check("aprimorar_3 requer _2", S.guild_item("mago_aprimorar_3")["requer"] == "mago_aprimorar_2")
    check("estender_3 requer _2", S.guild_item("mago_estender_3")["requer"] == "mago_estender_2")
    check("aprimorar_2 sem requer", S.guild_item("mago_aprimorar_2")["requer"] is None)

    print(f"\n{'='*40}\nPASS={PASS} FAIL={FAIL}\n{'='*40}")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
