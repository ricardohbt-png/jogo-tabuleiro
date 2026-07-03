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

    # [2] Helpers de nível
    print("\n[2] Helpers de metamagia")
    r = setup()
    check("teto base = 1", r._teto_metamagia(mage()) == 1)
    check("teto tecelagem_2 = 2", r._teto_metamagia(mage(esp=["mago_tecelagem_2"])) == 2)
    check("teto tecelagem_3 = 3", r._teto_metamagia(mage(esp=["mago_tecelagem_3"])) == 3)
    check("fortalecer base = 1.25", r._fortalecer_mult(mage()) == 1.25)
    check("fortalecer_2 = 1.5", r._fortalecer_mult(mage(esp=["mago_fortalecer_2"])) == 1.5)
    check("fortalecer_3 = 2.0", r._fortalecer_mult(mage(esp=["mago_fortalecer_3"])) == 2.0)
    check("aprimorar base = 1", r._aprimorar_bonus(mage()) == 1)
    check("aprimorar_3 = 3", r._aprimorar_bonus(mage(esp=["mago_aprimorar_3"])) == 3)
    check("estender base = 1", r._estender_bonus(mage()) == 1)
    check("estender_3 = 3", r._estender_bonus(mage(esp=["mago_estender_3"])) == 3)

    # [3] Resolução de metamagia (cap + magnitude + custo)
    print("\n[3] _resolver_metamagia")
    r = setup()
    mg = magia_completa()
    # base: as 3 armadas, teto 1 → só Fortalecer aplica (dmg 1.25), excedeu=True
    p = mage(); p["fortalecer_ativo"]=True; p["estender_ativo"]=True; p["aprimorar_ativo"]=True
    dmg, dur, dc, mf, ms, partes, exc = r._resolver_metamagia(p, mg)
    check("teto1: dmg=1.25", dmg == 1.25)
    check("teto1: dur=0 (não aplicou Estender)", dur == 0)
    check("teto1: dc=0 (não aplicou Aprimorar)", dc == 0)
    check("teto1: custo só do Fortalecer 6/6", (mf, ms) == (6, 6))
    check("teto1: excedeu=True", exc is True)

    # tecelagem_2: Fortalecer + Estender
    p = mage(esp=["mago_tecelagem_2"]); p["fortalecer_ativo"]=True; p["estender_ativo"]=True; p["aprimorar_ativo"]=True
    dmg, dur, dc, mf, ms, partes, exc = r._resolver_metamagia(p, mg)
    check("teto2: dmg=1.25 e dur=1", dmg == 1.25 and dur == 1)
    check("teto2: dc=0 (Aprimorar cortado)", dc == 0)
    check("teto2: custo 6+3 / 6+3", (mf, ms) == (9, 9))
    check("teto2: excedeu=True", exc is True)

    # tecelagem_3: as três
    p = mage(esp=["mago_tecelagem_3"]); p["fortalecer_ativo"]=True; p["estender_ativo"]=True; p["aprimorar_ativo"]=True
    dmg, dur, dc, mf, ms, partes, exc = r._resolver_metamagia(p, mg)
    check("teto3: as três aplicam", dmg == 1.25 and dur == 1 and dc == 1)
    check("teto3: custo 6+3+3 / 6+3", (mf, ms) == (12, 9))
    check("teto3: excedeu=False", exc is False)

    # magnitude com upgrades (teto 3)
    p = mage(esp=["mago_tecelagem_3","mago_fortalecer_3","mago_aprimorar_3","mago_estender_3"])
    p["fortalecer_ativo"]=True; p["estender_ativo"]=True; p["aprimorar_ativo"]=True
    dmg, dur, dc, mf, ms, partes, exc = r._resolver_metamagia(p, mg)
    check("magnitude: dmg=2.0", dmg == 2.0)
    check("magnitude: dur=3", dur == 3)
    check("magnitude: dc=3", dc == 3)

    # teto2 com duas metamagias que NÃO são Fortalecer (Estender+Aprimorar) → ambas cabem
    p = mage(esp=["mago_tecelagem_2"]); p["estender_ativo"]=True; p["aprimorar_ativo"]=True
    dmg, dur, dc, mf, ms, partes, exc = r._resolver_metamagia(p, mg)
    check("teto2 sem Fortalecer: Estender+Aprimorar aplicam", dmg == 1 and dur == 1 and dc == 1)
    check("teto2 sem Fortalecer: custo 3+3 / 3", (mf, ms) == (6, 3))
    check("teto2 sem Fortalecer: não excedeu", exc is False)

    # aplicabilidade: magia sem save não cobra Aprimorar
    p = mage(esp=["mago_tecelagem_3"]); p["aprimorar_ativo"]=True
    dmg, dur, dc, mf, ms, partes, exc = r._resolver_metamagia(p, {"id":"x","dano_por_nivel":"1d6"})
    check("sem save: Aprimorar não aplica (dc=0, custo 0)", dc == 0 and (mf, ms) == (0, 0))

    print(f"\n{'='*40}\nPASS={PASS} FAIL={FAIL}\n{'='*40}")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
