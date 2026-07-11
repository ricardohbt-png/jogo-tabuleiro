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
    # isola a espec da Canção do instrumento inicial (Alaúde Velho na mão do
    # escudo dá +1 acerto via Sinfonia Heroica)
    p["gear"]["off_hand"] = None
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

    # [4] Provocação II/III
    print("\n[4] Provocação")
    r = setup(); r.round_num = 5
    b = bard(esp=["bardo_provocacao_2"]); r.players["b"] = b
    ally = make_player("a", "Ana", "warrior", 1); ally["pos"] = [0,0]; ally["alive"] = True; r.players["a"] = ally
    mprov = monster(pos=(0,1)); mprov["provocado_turnos"] = 3; mprov["provocado_por"] = "b"
    check("_provocador acha o bardo", r._provocador(mprov) is b)
    check("+2 CA quando o alvo é o bardo dono",
          r._provocacao_ca_bonus(b, mprov) == 2)
    check("sem +2 CA para outro aliado",
          r._provocacao_ca_bonus(ally, mprov) == 0)
    check("bardo ataca com vantagem (II)",
          r._provocacao_atk_vantagem(b, mprov) is True)
    check("aliado NÃO tem vantagem sem III",
          r._provocacao_atk_vantagem(ally, mprov) is False)

    # III: aliados ganham vantagem na janela da rodada
    r = setup(); r.round_num = 5
    b3 = bard(esp=["bardo_provocacao_2","bardo_provocacao_3"]); r.players["b"] = b3
    ally3 = make_player("a","Ana","warrior",1); ally3["pos"]=[0,0]; ally3["alive"]=True; r.players["a"] = ally3
    m3 = monster(pos=(0,1)); m3["provocado_turnos"]=3; m3["provocado_por"]="b"
    m3["provocado_aliados_vantagem_round"] = 5
    check("aliado tem vantagem (III, mesma rodada)",
          r._provocacao_atk_vantagem(ally3, m3) is True)
    m3["provocado_aliados_vantagem_round"] = 4  # rodada anterior
    check("aliado sem vantagem fora da janela",
          r._provocacao_atk_vantagem(ally3, m3) is False)

    # provocador morto/ausente → sem bônus
    r = setup(); r.round_num = 5
    b4 = bard(esp=["bardo_provocacao_2"]); b4["alive"] = False; r.players["b"] = b4
    m4 = monster(pos=(0,1)); m4["provocado_turnos"]=3; m4["provocado_por"]="b"
    check("bardo morto → _provocador None", r._provocador(m4) is None)

    # [5] Lendas — ataque +1
    print("\n[5] Lendas: ataque")
    r = setup()
    b = bard(esp=["lenda_goblin"]); r.players["b"] = b
    ally = make_player("a","Ana","warrior",1); ally["pos"]=[0,0]; ally["alive"]=True; r.players["a"] = ally
    gob = monster(type_="goblin"); orc = monster(type_="orc")
    check("bardo +1 ataque vs goblin estudado", r._lenda_atk_bonus(b, gob) == 1)
    check("bardo +0 ataque vs orc não estudado", r._lenda_atk_bonus(b, orc) == 0)
    check("aliado +0 sem Lendas Supremas", r._lenda_atk_bonus(ally, gob) == 0)

    # Supremas: aliados também ganham
    r = setup()
    b2 = bard(esp=["lenda_goblin","bardo_lendas_supremas"]); r.players["b"] = b2
    ally2 = make_player("a","Ana","warrior",1); ally2["pos"]=[0,0]; ally2["alive"]=True; r.players["a"] = ally2
    check("aliado +1 com Supremas", r._lenda_atk_bonus(ally2, monster(type_="goblin")) == 1)

    # bardo morto → sem bônus
    r = setup()
    bd = bard(esp=["lenda_goblin"]); bd["alive"] = False; r.players["b"] = bd
    ally3 = make_player("a","Ana","warrior",1); ally3["alive"]=True; r.players["a"] = ally3
    check("sem bardo vivo → _bardo_lendas None", r._bardo_lendas() is None)
    check("bardo morto → aliado sem bônus", r._lenda_atk_bonus(ally3, monster(type_="goblin")) == 0)

    # [6] Lendas — resistência +1 (via _testar_save fonte)
    print("\n[6] Lendas: resistência")
    r = setup()
    b = bard(esp=["lenda_goblin"]); r.players["b"] = b
    gob = monster(type_="goblin")
    check("resist +1 vs habilidade de goblin (bardo)",
          r._lenda_resist_bonus(b, gob) == 1)
    check("resist +0 sem fonte", r._lenda_resist_bonus(b, None) == 0)
    check("resist +0 vs espécie não estudada",
          r._lenda_resist_bonus(b, monster(type_="orc")) == 0)

    # _testar_save soma o bônus quando recebe fonte monstro (isola só o bônus)
    def _bonus_delta(alvo, fonte):
        _, _d, sb_no,  _t  = r._testar_save(alvo, "fortitude", 99)
        _, _d2, sb_yes, _t2 = r._testar_save(alvo, "fortitude", 99, fonte=fonte)
        return sb_yes - sb_no
    check("_testar_save(fonte=goblin) soma +1 p/ bardo dono",
          _bonus_delta(b, gob) == 1)
    check("_testar_save(fonte=None) não soma",
          _bonus_delta(b, None) == 0)

    print(f"\n{'='*40}\nPASS={PASS} FAIL={FAIL}\n{'='*40}")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
