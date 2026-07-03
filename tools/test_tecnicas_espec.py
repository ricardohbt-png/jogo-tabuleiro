"""Técnicas da Guilda — Recarga Curta (Fase 2a). Roda: python tools/test_tecnicas_espec.py"""
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
    r.phase = phase; r._errs = errs; r.round_num = 1
    return r

def hero(cls="warrior", tid=None, **kw):
    p = make_player("h", "Heroi", cls, 0)
    p["pos"] = [0, 0]; p["alive"] = True
    p["fome"] = 20; p["sede"] = 20
    if tid:
        p["guild_owned"]["tecnicas"] = [tid]
        p["guild_equip"]["tecnica"] = tid
    for k, v in kw.items(): p[k] = v
    return p

async def main():
    # [1] Catálogo
    print("\n[1] Catálogo — Recarga Curta")
    for tid in ["tecnica_mira_perfeita","tecnica_espirito_indomavel","tecnica_grito_guerra","tecnica_pressa"]:
        it = S.guild_item(tid)
        check(f"existe {tid}", it is not None)
        check(f"{tid} recarga 3", it and it["recarga_rodadas"] == 3)
        check(f"{tid} preco 100", it and it["preco"] == 100)
        check(f"{tid} classe None", it and it["classe"] is None)
    check("pressa custa 4/4", S.guild_item("tecnica_pressa")["custo_fome"] == 4
          and S.guild_item("tecnica_pressa")["custo_sede"] == 4)
    check("mira custa 2/2", S.guild_item("tecnica_mira_perfeita")["custo_fome"] == 2)

    print(f"\n{'='*40}\nPASS={PASS} FAIL={FAIL}\n{'='*40}")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
