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

    # [3] Canção Heroica — nível por atributo + Suprema
    print("\n[3] Canção Heroica")
    r = setup()
    check("nivel base acerto = 1", r._cancao_nivel_atributo(bard(), "acerto") == 1)
    check("nivel comprado dano = 2",
          r._cancao_nivel_atributo(bard(esp=["bardo_cancao_dano"]), "dano") == 2)
    check("dano não afeta acerto",
          r._cancao_nivel_atributo(bard(esp=["bardo_cancao_dano"]), "acerto") == 1)
    check("reducao base = 0", r._cancao_custo_reducao(bard()) == 0)
    check("reducao com suprema = 1",
          r._cancao_custo_reducao(bard(esp=["bardo_cancao_suprema"])) == 1)

    # buffs aplicados usam o nível
    r = setup()
    b = bard(esp=["bardo_cancao_dano"]); r.players["b"] = b
    b["cancao_atributos"] = ["acerto", "dano"]
    await r._aplicar_buffs_cancao(b)
    check("buff acerto = 1", b["buffs_cancao"].get("bonus_acerto") == 1)
    check("buff dano = 2 (comprado)", b["buffs_cancao"].get("bonus_dano") == 2)

    # ativação com Suprema debita custo reduzido (mín 0)
    r = setup()
    b = bard(esp=["bardo_cancao_suprema"]); r.players["b"] = b
    b["fome"] = 10; b["sede"] = 10
    await r.handle_ativar_cancao("b", {"atributos": ["dano", "acerto"]})
    # dano=fome, acerto=sede → custo bruto 1/1, reduzido a 0/0
    check("ativação suprema não gasta fome", b["fome"] == 10)
    check("ativação suprema não gasta sede", b["sede"] == 10)
    check("custo salvo já reduzido", b["cancao_custo"] == {"fome": 0, "sede": 0})

    print(f"\n{'='*40}\nPASS={PASS} FAIL={FAIL}\n{'='*40}")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
