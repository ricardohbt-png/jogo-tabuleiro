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

    # [2] Cura pelas Mãos
    print("\n[2] Cura pelas Mãos")
    r = setup()
    check("dados base = 1", r._cura_maos_dados(paladin()) == 1)
    check("dados II = 2", r._cura_maos_dados(paladin(esp=["paladino_cura_maos_2"])) == 2)
    _orig = S.roll_dice; S.roll_dice = lambda s: sum(6 for _ in range(int(s.split("d")[0])))  # cada dado=6
    try:
        from server import mod
        # II: 2d6(=12)+FOR
        r = setup(); p = paladin(esp=["paladino_cura_maos_2"]); p["fome"]=50; p["sede"]=50; r.players["r"]=p
        alvo = make_player("a","Ana","warrior",1); alvo["pos"]=[0,1]; alvo["hp"]=1; alvo["max_hp"]=99; r.players["a"]=alvo
        await r.handle_imposicao_maos("r", {"target_id":"a"})
        check("II cura 2d6+FOR", alvo["hp"] == 1 + (12 + mod(p["str_"])))
        check("II custo base (3/2)", p["fome"] == 47 and p["sede"] == 48)
        # III: extra_d6=2 → +2d6 e custo +4/+4 (total base+extra: 7 fome, 6 sede)
        r = setup(); p = paladin(esp=["paladino_cura_maos_2","paladino_cura_maos_3"]); p["fome"]=50; p["sede"]=50; r.players["r"]=p
        alvo = make_player("a","Ana","warrior",1); alvo["pos"]=[0,1]; alvo["hp"]=1; alvo["max_hp"]=999; r.players["a"]=alvo
        await r.handle_imposicao_maos("r", {"target_id":"a","extra_d6":2})
        check("III cura 2d6+2d6+FOR (=24+FOR)", alvo["hp"] == 1 + (24 + mod(p["str_"])))
        check("III custo total (3+4=7 fome, 2+4=6 sede)", p["fome"] == 50-7 and p["sede"] == 50-6)
        # extra_d6 ignorado sem cura_maos_3
        r = setup(); p = paladin(esp=["paladino_cura_maos_2"]); p["fome"]=50; p["sede"]=50; r.players["r"]=p
        alvo = make_player("a","Ana","warrior",1); alvo["pos"]=[0,1]; alvo["hp"]=1; alvo["max_hp"]=999; r.players["a"]=alvo
        await r.handle_imposicao_maos("r", {"target_id":"a","extra_d6":3})
        check("extra_d6 ignorado sem cura_maos_3", alvo["hp"] == 1 + (12 + mod(p["str_"])) and p["fome"]==47 and p["sede"]==48)
    finally:
        S.roll_dice = _orig

    # [3] Ataque Sagrado (dados)
    print("\n[3] Ataque Sagrado")
    r = setup()
    check("sagrado base = 1 d8", r._ataque_sagrado_dados(paladin()) == 1)
    check("sagrado II = 2 d8", r._ataque_sagrado_dados(paladin(esp=["paladino_ataque_sagrado_2"])) == 2)

    # [4] Guerreiro da Luz: teto de atributos
    print("\n[4] Guerreiro da Luz (atributos)")
    r = setup()
    check("max base = 2", r._gdl_max_atributos(paladin()) == 2)
    check("max luz_2 = 3", r._gdl_max_atributos(paladin(esp=["paladino_luz_2"])) == 3)
    check("max luz_3 = 4", r._gdl_max_atributos(paladin(esp=["paladino_luz_2","paladino_luz_3"])) == 4)
    # integração: 3 atributos sem luz_2 é recusado
    r = setup(); p = paladin(); p["fome"]=50; p["sede"]=50; r.players["r"]=p
    await r._ativar_guerreiro_luz(p, "r", {"bonus":{"ataque":1,"dano":1,"ca":1}})
    check("recusa 3 atributos sem luz_2", not p.get("guerreiro_luz_ativo") and r._errs)
    # com luz_2 aceita 3
    r = setup(); p = paladin(esp=["paladino_luz_2"]); p["fome"]=50; p["sede"]=50; r.players["r"]=p
    await r._ativar_guerreiro_luz(p, "r", {"bonus":{"ataque":1,"dano":1,"ca":1}})
    check("aceita 3 atributos com luz_2", p.get("guerreiro_luz_ativo") is True)

    # [5] Guerreiro da Luz: detecção de armadilhas
    print("\n[5] Guerreiro da Luz (armadilhas)")
    r = setup()
    check("trap raio base = 1", r._gdl_trap_raio(paladin()) == 1)
    check("trap raio luz_2 = 2", r._gdl_trap_raio(paladin(esp=["paladino_luz_2"])) == 2)
    check("trap raio luz_3 = 3", r._gdl_trap_raio(paladin(esp=["paladino_luz_2","paladino_luz_3"])) == 3)
    # integração: revela armadilha colocável hostil a 2 quadrados com raio 2
    r = setup(); p = paladin(esp=["paladino_luz_2"]); p["pos"]=[0,0]; r.players["r"]=p
    r.armadilhas = [{"pos":[0,2], "visivel": False, "criador": "monstro1"}]
    r.traps = []
    r.explored = set()
    n = r._revelar_armadilhas_raio(p, r._gdl_trap_raio(p))
    check("revelou armadilha a 2q com raio 2", r.armadilhas[0]["visivel"] is True and n == 1)
    # fora do raio (raio 1) não revela
    r = setup(); p = paladin(); p["pos"]=[0,0]; r.players["r"]=p
    r.armadilhas = [{"pos":[0,2], "visivel": False, "criador": "monstro1"}]
    r.traps = []; r.explored = set()
    r._revelar_armadilhas_raio(p, r._gdl_trap_raio(p))
    check("não revela a 2q com raio 1", r.armadilhas[0]["visivel"] is False)

    # [6] Defensor
    print("\n[6] Defensor")
    r = setup()
    check("raio base = 4", r._defensor_raio(paladin()) == 4)
    check("raio II = 5", r._defensor_raio(paladin(esp=["paladino_defensor_2"])) == 5)
    check("split base = (5,5) de 10", r._defensor_split(paladin(), 10) == (5, 5))
    check("split III = (4,4) de 10", r._defensor_split(paladin(esp=["paladino_defensor_2","paladino_defensor_3"]), 10) == (4, 4))
    # integração: _processar_dano_protetor divide 40/40 com _3
    r = setup(); p = paladin(esp=["paladino_defensor_2","paladino_defensor_3"]); p["pos"]=[0,0]
    p["protetor_ativo"]=True; p["protetor_alvo"]="a"; r.players["r"]=p
    alvo = make_player("a","Ana","warrior",1); alvo["pos"]=[0,1]; r.players["a"]=alvo
    dano_alvo, transfer = await r._processar_dano_protetor("a", 10)
    check("protetor III → aliado 4", dano_alvo == 4)
    check("protetor III → richard 4", transfer is not None and transfer[1] == 4)
    # integração: raio 5 permite proteger a distância 5, raio 4 (base) não
    r = setup(); p = paladin(esp=["paladino_defensor_2"]); p["pos"]=[0,0]
    p["protetor_ativo"]=True; p["protetor_alvo"]="a"; r.players["r"]=p
    alvo = make_player("a","Ana","warrior",1); alvo["pos"]=[0,5]; r.players["a"]=alvo
    dano_alvo, transfer = await r._processar_dano_protetor("a", 10)
    check("raio 5 (II) mantém proteção a 5q", transfer is not None)

    # [7] Regeneração em área
    print("\n[7] Regeneração")
    r = setup()
    check("regen raio base = 0", r._regen_raio(paladin()) == 0)
    check("regen raio II = 1", r._regen_raio(paladin(esp=["paladino_regen_2"])) == 1)
    check("regen raio III = 2", r._regen_raio(paladin(esp=["paladino_regen_2","paladino_regen_3"])) == 2)
    # integração: upkeep com regen_2 cura Richard e aliado adjacente
    r = setup(); p = paladin(esp=["paladino_regen_2"]); p["pos"]=[0,0]; p["hp"]=5; p["max_hp"]=20
    p["fome"]=50; p["sede"]=50; p["regeneracao_ativa"]=True; r.players["r"]=p
    alvo = make_player("a","Ana","warrior",1); alvo["pos"]=[0,1]; alvo["hp"]=5; alvo["max_hp"]=20; r.players["a"]=alvo
    await r._processar_manutencao_richard(p)
    check("regen II cura Richard +1", p["hp"] == 6)
    check("regen II cura aliado adjacente +1", alvo["hp"] == 6)
    # base não cura aliado (só Richard)
    r = setup(); p = paladin(); p["pos"]=[0,0]; p["hp"]=5; p["max_hp"]=20; p["fome"]=50; p["sede"]=50; p["regeneracao_ativa"]=True; r.players["r"]=p
    alvo = make_player("a","Ana","warrior",1); alvo["pos"]=[0,1]; alvo["hp"]=5; alvo["max_hp"]=20; r.players["a"]=alvo
    await r._processar_manutencao_richard(p)
    check("base não cura aliado", alvo["hp"] == 5)
    check("base ainda cura Richard +1", p["hp"] == 6)

    print(f"\n{'='*40}\n  {PASS} passaram, {FAIL} falharam\n{'='*40}")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
