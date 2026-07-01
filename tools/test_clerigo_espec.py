"""Especializações do Clérigo (Fase 1b). Roda da raiz: python tools/test_clerigo_espec.py"""
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
    r._no_raio = lambda *a, **k: True
    r._tem_linha_de_visao = lambda *a, **k: True
    r.phase = phase; r._errs = errs
    return r

def cleric(**owned):
    p = make_player("c", "Lewis", "cleric", 0)
    p["guild_owned"]["especializacoes"] = list(owned.get("esp", []))
    return p

async def main():
    # [1] Catálogo
    print("\n[1] Catálogo do Clérigo")
    ids = [i["id"] for i in S.guild_items_for_class("cleric")]
    for eid in ["clerigo_cura_2","clerigo_cura_3","clerigo_massa_2","clerigo_massa_3",
                "clerigo_purif_2","clerigo_purif_3","clerigo_ressur_2","clerigo_ressur_3"]:
        check(f"catálogo tem {eid}", eid in ids)
    check("cura_3 requer cura_2", S.guild_item("clerigo_cura_3")["requer"] == "clerigo_cura_2")
    check("massa_2 sem requer", S.guild_item("clerigo_massa_2")["requer"] is None)
    check("ressur_3 requer ressur_2", S.guild_item("clerigo_ressur_3")["requer"] == "clerigo_ressur_2")
    check("preço II = 150", S.guild_item("clerigo_cura_2")["preco"] == 150)
    check("preço III = 200", S.guild_item("clerigo_purif_3")["preco"] == 200)

    # [2] Cura teto
    print("\n[2] Cura teto")
    r = setup()
    check("teto base = 1", r._cura_teto(cleric()) == 1)
    check("teto cura_2 = 2", r._cura_teto(cleric(esp=["clerigo_cura_2"])) == 2)
    check("teto cura_3 = 3", r._cura_teto(cleric(esp=["clerigo_cura_2","clerigo_cura_3"])) == 3)
    # integração: pedir 3 dados sem cura_3 cura no máx 1 (base). Dado fixo=8, INT Lewis(16)=+3.
    _orig = S.random.randint; S.random.randint = lambda a,b: 8
    try:
        r = setup(); c = cleric(); c["pos"]=[0,0]; r.players["c"]=c
        alvo = make_player("a","Ana","warrior",1); alvo["pos"]=[0,1]; alvo["hp"]=1; alvo["max_hp"]=99; r.players["a"]=alvo
        await r.handle_cura("c", {"target_id":"a","num_dados":3,"alcance_extra":0})
        check("cura base clampa a 1 dado (1+8+3=12)", alvo["hp"] == 1 + (8 + 3))
    finally:
        S.random.randint = _orig

    # [3] Cura em Massa: nível → dados + raio
    print("\n[3] Cura em Massa")
    r = setup()
    check("massa base = 1", r._massa_nivel(cleric()) == 1)
    check("massa_2 = 2", r._massa_nivel(cleric(esp=["clerigo_massa_2"])) == 2)
    check("massa_3 = 3", r._massa_nivel(cleric(esp=["clerigo_massa_2","clerigo_massa_3"])) == 3)
    # integração: raio usado = 2*nível (capturado via r._no_raio); dados clampados ao nível
    _orig = S.random.randint; S.random.randint = lambda a,b: 8
    raios = []
    try:
        r = setup()
        def cap_raio(p, alvo, raio, *a, **k): raios.append(raio); return True
        r._no_raio = cap_raio
        c = cleric(esp=["clerigo_massa_2"]); c["pos"]=[0,0]; r.players["c"]=c
        alvo = make_player("a","Ana","warrior",1); alvo["pos"]=[0,1]; alvo["hp"]=1; alvo["max_hp"]=99; r.players["a"]=alvo
        await r.handle_cura_area("c", {"num_dados":3})
        check("massa_2 usa raio 4", 4 in raios)
        check("massa_2 clampa dados a 2 (1+2*8+3=20)", alvo["hp"] == 1 + (2*8 + 3))
    finally:
        S.random.randint = _orig

    # [4] Purificação: tipos por nível
    print("\n[4] Purificação")
    r = setup()
    check("base só veneno", r._purif_tipos(cleric()) == {"veneno"})
    check("II +doença", r._purif_tipos(cleric(esp=["clerigo_purif_2"])) == {"veneno","doenca"})
    check("III +maldição/petrif", r._purif_tipos(cleric(esp=["clerigo_purif_2","clerigo_purif_3"]))
          == {"veneno","doenca","maldicao","petrificacao"})
    # integração: purificar 'doenca' sem purif_2 é recusado (sem efeito)
    r = setup(); c = cleric(); c["pos"]=[0,0]; r.players["c"]=c
    alvo = make_player("a","Ana","warrior",1); alvo["pos"]=[0,1]; r.players["a"]=alvo
    await r.handle_purificacao("c", {"target_id":"a","tipo":"doenca"})
    check("recusa doença sem purif_2", any("purific" in e.lower() or "aprendeu" in e.lower() for e in r._errs))

    # [5] Ressurreição: HP e custo por nível
    print("\n[5] Ressurreição")
    r = setup()
    check("ressur base = 1", r._ressur_nivel(cleric()) == 1)
    check("ressur_2 = 2", r._ressur_nivel(cleric(esp=["clerigo_ressur_2"])) == 2)
    check("ressur_3 = 3", r._ressur_nivel(cleric(esp=["clerigo_ressur_2","clerigo_ressur_3"])) == 3)
    # integração nível II: metade dos PV + custo 15/15
    r = setup(); c = cleric(esp=["clerigo_ressur_2"]); c["pos"]=[0,0]; c["fome"]=50; c["sede"]=50; r.players["c"]=c
    morto = make_player("a","Ana","warrior",1); morto["pos"]=[0,1]; morto["alive"]=False; morto["hp"]=0; morto["max_hp"]=20; r.players["a"]=morto
    await r.handle_ressurreicao("c", {"target_id":"a"})
    check("ressur II → metade PV (10)", morto["hp"] == 10)
    check("ressur II → custo 15/15", c["fome"] == 35 and c["sede"] == 35)
    # integração nível III: PV cheio + custo 20/20
    r = setup(); c = cleric(esp=["clerigo_ressur_2","clerigo_ressur_3"]); c["pos"]=[0,0]; c["fome"]=50; c["sede"]=50; r.players["c"]=c
    morto = make_player("a","Ana","warrior",1); morto["pos"]=[0,1]; morto["alive"]=False; morto["hp"]=0; morto["max_hp"]=20; r.players["a"]=morto
    await r.handle_ressurreicao("c", {"target_id":"a"})
    check("ressur III → PV cheio (20)", morto["hp"] == 20)
    check("ressur III → custo 20/20", c["fome"] == 30 and c["sede"] == 30)

    print(f"\n{'='*40}\n  {PASS} passaram, {FAIL} falharam\n{'='*40}")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
