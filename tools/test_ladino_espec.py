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
        fome_ini, sede_ini = luccas["fome"], luccas["sede"]
        r.armadilhas = [{"id":"arm1","tipo":"armadilha_urso","pos":[1,1],"visivel":True,"ativada":False}]
        r._armadilha_no_tile = lambda x,y: next((a for a in r.armadilhas if a["pos"]==[x,y]), None)
        await r.handle_desarmar_armadilha("l", {"tx": 1, "ty": 1})
        check("desarmou diagonal adjacente com sucesso", len(r.armadilhas) == 0)
        check("desarme custa 1 de fome e sede", luccas["fome"] == fome_ini - 1 and luccas["sede"] == sede_ini - 1)
        check("recuperou o ouro (custo_ouro da armadilha_urso=1)", luccas["gold"] == 1)
    finally:
        S.random.randint = _orig_rand

    # [7] Veneno Rápido — modelo de poison_slots (cargas na arma equipada).
    # Teto de cargas melee por spec: base 1; veneno_2 → 2 cargas do mesmo veneno
    # (dura 2 golpes); veneno_3 → um 2º veneno DIFERENTE ao mesmo tempo (máx 2
    # distintos, FIFO); veneno_2+veneno_3 → 2 venenos × 2 cargas = 4.
    print("\n[7] Veneno Rápido")
    r = setup()
    check("capacidade base = 1", r._capacidade_poison_melee(rogue()) == 1)
    check("capacidade com veneno_2 = 2", r._capacidade_poison_melee(rogue(esp=["ladino_veneno_2"])) == 2)
    check("capacidade com veneno_3 = 2", r._capacidade_poison_melee(rogue(esp=["ladino_veneno_3"])) == 2)
    check("capacidade com veneno_2+veneno_3 = 4",
          r._capacidade_poison_melee(rogue(esp=["ladino_veneno_2","ladino_veneno_3"])) == 4)
    check("não-ladino nunca passa de 1",
          r._capacidade_poison_melee(make_player("w","W","warrior",0)) == 1)

    S.VENENOS.setdefault("veneno_fraco", {"nome":"Fraco"})
    S.VENENOS.setdefault("veneno_forte", {"nome":"Forte"})
    def _luccas_armado(esp):
        p = rogue(esp=esp); p["sede"] = 50
        arma = {"id": "dagger"}
        p["gear"] = dict(p.get("gear") or {}); p["gear"]["weapon"] = arma
        p["weapon"] = arma
        # 2 frascos de fraco (handle_veneno_rapido consome o frasco a cada uso;
        # o teste de reaplicar precisa de um 2º fraco na bolsa) + 1 de forte.
        p["bag"] = [{"id":"fa","veneno_id":"veneno_fraco"},
                    {"id":"fb","veneno_id":"veneno_forte"},
                    {"id":"fc","veneno_id":"veneno_fraco"}]
        return p

    # base: 1 marcador; reaplicar substitui
    r = setup(); l = _luccas_armado([]); r.players["l"] = l
    await r.handle_veneno_rapido("l", {"veneno_id": "veneno_fraco"})
    check("base: 1 carga", r._weapon_poison_slots(l) == ["veneno_fraco"])
    await r.handle_veneno_rapido("l", {"veneno_id": "veneno_forte"})
    check("base: outro veneno substitui", r._weapon_poison_slots(l) == ["veneno_forte"])

    # veneno_2: mesmo veneno dura 2 golpes; outro veneno substitui (1 distinto só)
    r = setup(); l = _luccas_armado(["ladino_veneno_2"]); r.players["l"] = l
    await r.handle_veneno_rapido("l", {"veneno_id": "veneno_fraco"})
    check("veneno_2: 2 cargas do mesmo", r._weapon_poison_slots(l) == ["veneno_fraco","veneno_fraco"])
    await r.handle_veneno_rapido("l", {"veneno_id": "veneno_forte"})
    check("veneno_2 sem veneno_3: outro veneno substitui",
          r._weapon_poison_slots(l) == ["veneno_forte","veneno_forte"])

    # veneno_3: 2 venenos distintos ao mesmo tempo (1 carga cada, FIFO)
    r = setup(); l = _luccas_armado(["ladino_veneno_3"]); r.players["l"] = l
    await r.handle_veneno_rapido("l", {"veneno_id": "veneno_fraco"})
    await r.handle_veneno_rapido("l", {"veneno_id": "veneno_forte"})
    check("veneno_3: mantém 2 venenos distintos (antigo primeiro)",
          r._weapon_poison_slots(l) == ["veneno_fraco","veneno_forte"])

    # veneno_2 + veneno_3: 2 venenos × 2 cargas; o antigo é gasto primeiro
    r = setup(); l = _luccas_armado(["ladino_veneno_2","ladino_veneno_3"]); r.players["l"] = l
    await r.handle_veneno_rapido("l", {"veneno_id": "veneno_fraco"})
    check("veneno_2+3: 1º veneno com 2 cargas",
          r._weapon_poison_slots(l) == ["veneno_fraco","veneno_fraco"])
    await r.handle_veneno_rapido("l", {"veneno_id": "veneno_forte"})
    check("veneno_2+3: 2 venenos × 2 cargas (antigo primeiro)",
          r._weapon_poison_slots(l) == ["veneno_fraco","veneno_fraco","veneno_forte","veneno_forte"])
    # reaplicar o fraco recarrega e o move pro fim (máx 2 distintos preservado)
    await r.handle_veneno_rapido("l", {"veneno_id": "veneno_fraco"})
    check("veneno_2+3: reaplicar recarrega, mantém 2 distintos",
          r._weapon_poison_slots(l) == ["veneno_forte","veneno_forte","veneno_fraco","veneno_fraco"])

    # [8] Esconder nas Sombras
    print("\n[8] Esconder nas Sombras")
    r = setup()
    check("bônus base = 0", r._esconder_bonus(rogue()) == 0)
    check("bônus com esconder_2 = 2", r._esconder_bonus(rogue(esp=["ladino_esconder_2"])) == 2)
    check("bônus com esconder_3 = 2 (não soma mais)", r._esconder_bonus(rogue(esp=["ladino_esconder_2","ladino_esconder_3"])) == 2)
    # sem esconder_3: gasta ação bônus
    r = setup(); r.round_num = 1; luccas = rogue(); luccas["pos"]=[0,0]; luccas["fome"]=50; luccas["sede"]=50; r.players["l"]=luccas
    _orig_rand = S.random.randint; S.random.randint = lambda a,b: 20
    try:
        await r.handle_esconder_sombras("l", {})
        check("sem esconder_3: gasta ação bônus", luccas.get("bonus_action_used") is True)
        r.monsters["m1"] = monster()
        await r.handle_attack("l", "m1")
        check("pode atacar na ação principal no mesmo turno", not r._errs and r.monsters["m1"]["hp"] < 20)
        check("ataque principal fica consumido", luccas.get("action_done") is True)
    finally:
        S.random.randint = _orig_rand
    # com esconder_3: continua gastando ação bônus
    r2 = setup(); luccas2 = rogue(esp=["ladino_esconder_2","ladino_esconder_3"]); luccas2["pos"]=[0,0]
    luccas2["fome"]=50; luccas2["sede"]=50; r2.players["l"]=luccas2
    _orig_rand2 = S.random.randint; S.random.randint = lambda a,b: 20
    try:
        await r2.handle_esconder_sombras("l", {})
        check("com esconder_3: gasta ação bônus", luccas2.get("bonus_action_used") is True)
    finally:
        S.random.randint = _orig_rand2
    # ao ser revelado com esconder_3, ganha +2 de CA (temp_def)
    r3 = setup(); luccas3 = rogue(esp=["ladino_esconder_2","ladino_esconder_3"]); luccas3["id"]="l"
    luccas3["invisivel_sombras"] = True; r3.players["l"] = luccas3
    await r3._quebrar_invisibilidade(luccas3, "ao atacar")
    check("CA +2 por 1 rodada ao revelar com esconder_3", r3.temp_def.get("l") == 2)
    # sem esconder_3, não ganha CA
    r4 = setup(); luccas4 = rogue(); luccas4["id"]="l"
    luccas4["invisivel_sombras"] = True; r4.players["l"] = luccas4
    await r4._quebrar_invisibilidade(luccas4, "ao atacar")
    check("sem esconder_3, não ganha CA ao revelar", r4.temp_def.get("l", 0) == 0)

    print(f"\n{'='*40}\n  {PASS} passaram, {FAIL} falharam\n{'='*40}")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
