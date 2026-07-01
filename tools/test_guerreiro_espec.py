"""Especializações do Guerreiro (Fase 1a). Roda da raiz: python tools/test_guerreiro_espec.py"""
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
    r.phase = phase; r._errs = errs
    return r

def warrior(**owned):
    p = make_player("p1", "Victor", "warrior", 0)
    p["guild_owned"]["especializacoes"] = list(owned.get("esp", []))
    return p

async def main():
    # [1] Catálogo + tem_espec
    print("\n[1] Catálogo do Guerreiro")
    ids = [i["id"] for i in S.guild_items_for_class("warrior")]
    for eid in ["guerreiro_combinar_2","guerreiro_mestre_combate","guerreiro_mira_3",
                "guerreiro_golpe_3","guerreiro_furia_3"]:
        check(f"catálogo tem {eid}", eid in ids)
    check("combinar_2 sem requer", S.guild_item("guerreiro_combinar_2")["requer"] is None)
    check("mestre requer combinar_2", S.guild_item("guerreiro_mestre_combate")["requer"] == "guerreiro_combinar_2")
    check("mira_3 requer combinar_2", S.guild_item("guerreiro_mira_3")["requer"] == "guerreiro_combinar_2")
    check("preço combinar_2 = 150", S.guild_item("guerreiro_combinar_2")["preco"] == 150)
    check("preço mestre = 300", S.guild_item("guerreiro_mestre_combate")["preco"] == 300)
    check("preço mira_3 = 200", S.guild_item("guerreiro_mira_3")["preco"] == 200)
    p = warrior(esp=["guerreiro_golpe_3"])
    check("tem_espec True", S.tem_espec(p, "guerreiro_golpe_3"))
    check("tem_espec False", not S.tem_espec(p, "guerreiro_mira_3"))

    # [2] Campos novos + Fúria contador
    print("\n[2] Fúria contador + campos")
    r = setup("playing")
    check("_furia_extras base = 1", r._furia_extras(warrior()) == 1)
    check("_furia_extras III = 2", r._furia_extras(warrior(esp=["guerreiro_furia_3"])) == 2)
    p = make_player("p1", "Victor", "warrior", 0)
    check("make_player tem skill_ataques_extras", p.get("skill_ataques_extras") == 0)
    check("make_player tem skill_bonus_dano", p.get("skill_bonus_dano") == 0)
    check("removeu skill_ataque_extra", "skill_ataque_extra" not in p)
    check("removeu skill_extra_usado", "skill_extra_usado" not in p)

    # [3] Teto de combinação
    print("\n[3] Teto de combinação")
    r = setup("playing")
    check("teto base = 1", r._teto_combinacao(warrior()) == 1)
    check("teto combinar_2 = 2", r._teto_combinacao(warrior(esp=["guerreiro_combinar_2"])) == 2)
    check("teto mestre = 3", r._teto_combinacao(warrior(esp=["guerreiro_combinar_2","guerreiro_mestre_combate"])) == 3)

    print(f"\n{'='*40}\n  {PASS} passaram, {FAIL} falharam\n{'='*40}")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
