"""Especializações do Bardo (Fase 1e). Roda da raiz: python tools/test_bardo_espec.py"""
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

def bard(**owned):
    p = make_player("b", "Henrique", "bard", 0)
    p["guild_owned"]["especializacoes"] = list(owned.get("esp", []))
    p["pos"] = [0, 0]; p["alive"] = True
    return p

def monster(mid="m1", type_="goblin", pos=(0,1), hp=20):
    return {"id": mid, "type": type_, "name": "Goblin", "nome": "Goblin",
            "pos": list(pos), "hp": hp, "max_hp": hp, "ac": 10}

async def main():
    # [1] Catálogo literal do bardo
    print("\n[1] Catálogo do Bardo (literais)")
    ids = [i["id"] for i in S.guild_items_for_class("bard")]
    for eid in ["bardo_cancao_acerto","bardo_cancao_dano","bardo_cancao_ca",
                "bardo_cancao_movimento","bardo_cancao_resistencia",
                "bardo_cancao_suprema","bardo_provocacao_2","bardo_provocacao_3",
                "bardo_lendas_supremas"]:
        check(f"catálogo tem {eid}", eid in ids)
    check("cada canção custa 100", all(S.guild_item(f"bardo_cancao_{a}")["preco"] == 100
          for a in ["acerto","dano","ca","movimento","resistencia"]))
    check("canção suprema custa 200", S.guild_item("bardo_cancao_suprema")["preco"] == 200)
    check("provocacao_2 custa 150", S.guild_item("bardo_provocacao_2")["preco"] == 150)
    check("provocacao_3 requer _2", S.guild_item("bardo_provocacao_3")["requer"] == "bardo_provocacao_2")
    check("lendas supremas custa 300", S.guild_item("bardo_lendas_supremas")["preco"] == 300)

    # [2] Lendas geradas de MONSTER_DEFS
    print("\n[2] Lendas Avançadas (geradas)")
    ids = [i["id"] for i in S.guild_items_for_class("bard")]
    for mdef in S.MONSTER_DEFS:
        gid = f"lenda_{mdef['type']}"
        check(f"catálogo tem {gid}", gid in ids)
    check("preço goblin (T1) = 60", S.guild_item("lenda_goblin")["preco"] == 60)
    check("preço orc (T2) = 90", S.guild_item("lenda_orc")["preco"] == 90)
    check("preço troll (T3) = 120", S.guild_item("lenda_troll")["preco"] == 120)
    check("preço dragon (T4) = 200", S.guild_item("lenda_dragon")["preco"] == 200)
    check("lenda guarda lenda_tipo", S.guild_item("lenda_goblin")["lenda_tipo"] == "goblin")

    print(f"\n{'='*40}\nPASS={PASS} FAIL={FAIL}\n{'='*40}")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
