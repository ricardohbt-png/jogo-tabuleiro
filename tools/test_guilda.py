"""Guilda dos Heróis — Fase 0. Roda da raiz: python tools/test_guilda.py"""
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

def setup(phase="city"):
    r = GameRoom("TEST")
    errs = []; calls = {"city": 0, "push": 0}
    async def noop(*a, **k): pass
    async def cap_send(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error": errs.append(msg.get("msg",""))
    async def cap_city(*a, **k): calls["city"] += 1
    async def cap_push(*a, **k): calls["push"] += 1
    r.gm_say = noop; r.broadcast = noop; r._broadcast_dado = noop
    r.broadcast_city_state = cap_city; r.push_state = cap_push; r.send_to = cap_send
    r.phase = phase; r._errs = errs; r._calls = calls
    return r

async def main():
    import tempfile, shutil
    S.CHARACTERS_IN_USE.clear() if hasattr(S, "CHARACTERS_IN_USE") else None

    # [1] make_player tem os campos da guilda
    print("\n[1] Campos da guilda no make_player")
    p = make_player("p1", "Victor", "warrior", 0)
    check("guild_owned.especializacoes vazio", p["guild_owned"]["especializacoes"] == [])
    check("guild_owned.tecnicas vazio", p["guild_owned"]["tecnicas"] == [])
    check("guild_equip.tecnica None", p["guild_equip"]["tecnica"] is None)
    check("technique_cooldowns vazio", p["technique_cooldowns"] == {})

    # [2] save round-trip em pasta temporária
    print("\n[2] Save round-trip")
    tmp = tempfile.mkdtemp()
    old_dir = S.GUILD_SAVE_DIR
    S.GUILD_SAVE_DIR = tmp
    try:
        p["guild_owned"]["tecnicas"] = ["brutalidade"]
        p["guild_equip"]["tecnica"] = "brutalidade"
        S.write_guild_save(p)
        loaded = S.load_guild_save("warrior")
        check("carregou tecnicas", loaded["tecnicas"] == ["brutalidade"])
        check("carregou equip.tecnica", loaded["equip"]["tecnica"] == "brutalidade")
        check("classe sem save → vazio", S.load_guild_save("mage")["tecnicas"] == [])
        with open(os.path.join(tmp, "rogue.json"), "w", encoding="utf-8") as f:
            f.write("{lixo}")
        check("save corrompido → vazio", S.load_guild_save("rogue")["tecnicas"] == [])
        q = make_player("p2", "Victor", "warrior", 0)
        S.apply_guild_save(q)
        check("apply_guild_save popula", q["guild_owned"]["tecnicas"] == ["brutalidade"]
              and q["guild_equip"]["tecnica"] == "brutalidade")
    finally:
        S.GUILD_SAVE_DIR = old_dir
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n{'='*40}\n  {PASS} passaram, {FAIL} falharam\n{'='*40}")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
