"""Especializações do Ladino (Fase 1d). Roda da raiz: python tools/test_ladino_espec.py"""
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

def rogue(**owned):
    p = make_player("l", "Luccas", "rogue", 0)
    p["guild_owned"]["especializacoes"] = list(owned.get("esp", []))
    p["pos"] = [0, 0]
    return p

def monster(mid="m1", pos=(0,1), hp=20):
    return {"id": mid, "name": "Goblin", "pos": list(pos), "hp": hp, "max_hp": hp, "ac": 10}

async def main():
    # [1] Catálogo — 8 nós literais
    print("\n[1] Catálogo do Ladino (literais)")
    ids = [i["id"] for i in S.guild_items_for_class("rogue")]
    for eid in ["ladino_furtivo_2","ladino_furtivo_3","ladino_desarme_2","ladino_desarme_3",
                "ladino_veneno_2","ladino_veneno_3","ladino_esconder_2","ladino_esconder_3"]:
        check(f"catálogo tem {eid}", eid in ids)
    check("furtivo_3 requer furtivo_2", S.guild_item("ladino_furtivo_3")["requer"] == "ladino_furtivo_2")
    check("desarme_2 sem requer", S.guild_item("ladino_desarme_2")["requer"] is None)
    check("veneno_3 requer veneno_2", S.guild_item("ladino_veneno_3")["requer"] == "ladino_veneno_2")
    check("esconder_3 requer esconder_2", S.guild_item("ladino_esconder_3")["requer"] == "ladino_esconder_2")
    check("preço II = 150", S.guild_item("ladino_furtivo_2")["preco"] == 150)
    check("preço III = 200", S.guild_item("ladino_esconder_3")["preco"] == 200)

    # [2] Fórmulas de armadilha (geradas)
    print("\n[2] Fórmulas de armadilha")
    ids = [i["id"] for i in S.guild_items_for_class("rogue")]
    for eid, preco in [("ladino_armadilha_urso",100), ("ladino_fosso_estacas",120),
                        ("ladino_fosso_envenenado",130), ("ladino_rede",150),
                        ("ladino_armadilha_incendiaria",180), ("ladino_mina_terrestre",220),
                        ("ladino_nuvem_gas",250)]:
        check(f"catálogo tem {eid}", eid in ids)
        check(f"{eid} preço {preco}", S.guild_item(eid)["preco"] == preco)
    check("buraco não vira nó de compra", "ladino_buraco" not in ids and
          not any(v.get("nome","").endswith("Buraco") for v in S.GUILD_CATALOG.values()))

    # [3] Ataque Furtivo — base vs II
    print("\n[3] Ataque Furtivo base/II")
    r = setup()
    luccas = rogue(); luccas["pos"] = [0,0]; r.players["l"] = luccas
    aliado = make_player("a", "Ana", "warrior", 1); aliado["pos"] = [1,1]; aliado["alive"] = True; r.players["a"] = aliado
    alvo = monster(pos=(1,1))
    check("base: sem oculto e sem furtivo_2 → False", not r._verificar_ataque_furtivo(luccas, alvo))
    luccas["invisivel_sombras"] = True
    check("base: oculto → True", r._verificar_ataque_furtivo(luccas, alvo))
    luccas["invisivel_sombras"] = False
    luccas["guild_owned"]["especializacoes"] = ["ladino_furtivo_2"]
    check("com furtivo_2: aliado adjacente ao alvo → True", r._verificar_ataque_furtivo(luccas, alvo))

    # [4] Ataque Furtivo Supremo (reação)
    print("\n[4] Furtivo Supremo — reação")
    _orig_rand = S.random.randint; S.random.randint = lambda a,b: 4  # dado fixo=4
    try:
        # aliado (warrior) ataca e Luccas (com furtivo_3) reage
        r = setup(); r.round_num = 1
        luccas = rogue(esp=["ladino_furtivo_2","ladino_furtivo_3"]); luccas["pos"]=[5,5]; r.players["l"]=luccas
        aliado = make_player("a","Ana","warrior",1); aliado["pos"]=[0,0]; r.players["a"]=aliado
        alvo = monster(hp=20)
        await r._furtivo_reativo(aliado, alvo)
        check("reação aplica dano (2d4 nível 1 = 8)", alvo["hp"] == 12)
        # 2ª vez no MESMO alvo na MESMA rodada não dispara de novo
        await r._furtivo_reativo(aliado, alvo)
        check("não reage 2x no mesmo alvo na mesma rodada", alvo["hp"] == 12)
        # nova rodada libera de novo
        r.round_num = 2
        await r._furtivo_reativo(aliado, alvo)
        check("nova rodada libera a reação de novo", alvo["hp"] == 4)
        # Luccas atacando não dispara nele mesmo
        r2 = setup(); r2.round_num = 1
        luccas2 = rogue(esp=["ladino_furtivo_3"]); luccas2["pos"]=[0,0]; r2.players["l"]=luccas2
        alvo2 = monster(hp=20)
        await r2._furtivo_reativo(luccas2, alvo2)
        check("não reage ao próprio ataque de Luccas", alvo2["hp"] == 20)
        # alvo já morto não recebe reação
        r3 = setup(); r3.round_num = 1
        luccas3 = rogue(esp=["ladino_furtivo_3"]); luccas3["pos"]=[5,5]; r3.players["l"]=luccas3
        aliado3 = make_player("a","Ana","warrior",1); aliado3["pos"]=[0,0]; r3.players["a"]=aliado3
        alvo3 = monster(hp=0)
        await r3._furtivo_reativo(aliado3, alvo3)
        check("não reage a alvo já com hp<=0", alvo3["hp"] == 0)
        # sem furtivo_3 não reage
        r4 = setup(); r4.round_num = 1
        luccas4 = rogue(esp=["ladino_furtivo_2"]); luccas4["pos"]=[5,5]; r4.players["l"]=luccas4
        aliado4 = make_player("a","Ana","warrior",1); aliado4["pos"]=[0,0]; r4.players["a"]=aliado4
        alvo4 = monster(hp=20)
        await r4._furtivo_reativo(aliado4, alvo4)
        check("sem furtivo_3 não reage", alvo4["hp"] == 20)
        # Luccas petrificado não reage
        r5 = setup(); r5.round_num = 1
        luccas5 = rogue(esp=["ladino_furtivo_3"]); luccas5["pos"]=[5,5]; luccas5["petrificado"]=True; r5.players["l"]=luccas5
        aliado5 = make_player("a","Ana","warrior",1); aliado5["pos"]=[0,0]; r5.players["a"]=aliado5
        alvo5 = monster(hp=20)
        await r5._furtivo_reativo(aliado5, alvo5)
        check("Luccas petrificado não reage", alvo5["hp"] == 20)
        # Luccas paralisado não reage
        r6 = setup(); r6.round_num = 1
        luccas6 = rogue(esp=["ladino_furtivo_3"]); luccas6["pos"]=[5,5]; luccas6["paralisado"]=True; r6.players["l"]=luccas6
        aliado6 = make_player("a","Ana","warrior",1); aliado6["pos"]=[0,0]; r6.players["a"]=aliado6
        alvo6 = monster(hp=20)
        await r6._furtivo_reativo(aliado6, alvo6)
        check("Luccas paralisado não reage", alvo6["hp"] == 20)
        # Luccas imobilizado (perde_turno) não reage
        r7 = setup(); r7.round_num = 1
        luccas7 = rogue(esp=["ladino_furtivo_3"]); luccas7["pos"]=[5,5]; luccas7["perde_turno"]=True; r7.players["l"]=luccas7
        aliado7 = make_player("a","Ana","warrior",1); aliado7["pos"]=[0,0]; r7.players["a"]=aliado7
        alvo7 = monster(hp=20)
        await r7._furtivo_reativo(aliado7, alvo7)
        check("Luccas imobilizado não reage", alvo7["hp"] == 20)
    finally:
        S.random.randint = _orig_rand

    # [5] Fórmulas: gate em handle_criar_armadilha
    print("\n[5] Fórmulas — gate")
    r = setup()
    r.tiles = [[S.FLOOR for _ in range(r.map_w)] for _ in range(r.map_h)]
    luccas = rogue(); luccas["pos"] = [0,0]; luccas["gold"] = 100; r.players["l"] = luccas
    check("buraco sempre destravado", "buraco" in r._armadilhas_desbloqueadas(luccas))
    check("armadilha_urso bloqueada sem fórmula", "armadilha_urso" not in r._armadilhas_desbloqueadas(luccas))
    await r.handle_criar_armadilha("l", {"tipo": "armadilha_urso", "tx": 0, "ty": 0})
    check("recusa criar tipo bloqueado (sem armadilha nova)", len(r.armadilhas) == 0 and r._errs)
    luccas["guild_owned"]["especializacoes"] = ["ladino_armadilha_urso"]
    check("armadilha_urso destravada após compra (simulada)", "armadilha_urso" in r._armadilhas_desbloqueadas(luccas))
    r._errs = []
    await r.handle_criar_armadilha("l", {"tipo": "armadilha_urso", "tx": 0, "ty": 0})
    check("cria armadilha destravada com sucesso", len(r.armadilhas) == 1 and not r._errs)

    # [6] Desarme — bônus e recuperação
    print("\n[6] Desarme")
    r = setup()
    check("bônus base = 0", r._desarme_bonus(rogue()) == 0)
    check("bônus com desarme_2 = 2", r._desarme_bonus(rogue(esp=["ladino_desarme_2"])) == 2)
    check("bônus com desarme_3 = 2 (não soma mais)", r._desarme_bonus(rogue(esp=["ladino_desarme_2","ladino_desarme_3"])) == 2)
    # integração: desarme_3 recupera ouro em sucesso duplo (mock d20 alto)
    _orig_rand = S.random.randint; S.random.randint = lambda a,b: 20
    try:
        r = setup(); luccas = rogue(esp=["ladino_desarme_2","ladino_desarme_3"])
        luccas["pos"] = [0,0]; luccas["gold"] = 0; luccas["dex"] = 10; r.players["l"] = luccas
        r.armadilhas = [{"id":"arm1","tipo":"armadilha_urso","pos":[0,0],"visivel":True,"ativada":False}]
        r._armadilha_no_tile = lambda x,y: next((a for a in r.armadilhas if a["pos"]==[x,y]), None)
        await r.handle_desarmar_armadilha("l", {})
        check("desarmou com sucesso", len(r.armadilhas) == 0)
        check("recuperou o ouro (custo_ouro da armadilha_urso=1)", luccas["gold"] == 1)
    finally:
        S.random.randint = _orig_rand

    # [7] Veneno Rápido
    print("\n[7] Veneno Rápido")
    r = setup()
    check("golpes base = 1", r._veneno_rapido_max_hits(rogue()) == 1)
    check("golpes com veneno_2 = 2", r._veneno_rapido_max_hits(rogue(esp=["ladino_veneno_2"])) == 2)
    check("2 slots sem veneno_3", not r._veneno_rapido_2_slots(rogue()))
    check("2 slots com veneno_3", r._veneno_rapido_2_slots(rogue(esp=["ladino_veneno_2","ladino_veneno_3"])))
    # integração: aplicar 1º veneno preenche slot 1; 2º (com veneno_3) preenche slot 2 sem apagar o 1º
    r = setup()
    luccas = rogue(esp=["ladino_veneno_2","ladino_veneno_3"])
    luccas["sede"] = 50
    luccas["weapon"] = {"id": "dagger"}
    luccas["bag"] = [{"id":"frasco_a","veneno_id":"veneno_fraco"}, {"id":"frasco_b","veneno_id":"veneno_forte"}]
    r.players["l"] = luccas
    S.VENENOS.setdefault("veneno_fraco", {"nome":"Fraco"})
    S.VENENOS.setdefault("veneno_forte", {"nome":"Forte"})
    await r.handle_veneno_rapido("l", {"veneno_id": "veneno_fraco"})
    check("1º veneno preenche slot 1", luccas["weapon_poison"] == "veneno_fraco")
    check("slot 1 dura 2 golpes (veneno_2)", luccas["weapon_poison_hits"] == 2)
    await r.handle_veneno_rapido("l", {"veneno_id": "veneno_forte"})
    check("2º veneno preenche slot 2 (não apaga o 1º)",
          luccas["weapon_poison"] == "veneno_fraco" and luccas.get("weapon_poison_2") == "veneno_forte")

    print(f"\n{'='*40}\n  {PASS} passaram, {FAIL} falharam\n{'='*40}")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
