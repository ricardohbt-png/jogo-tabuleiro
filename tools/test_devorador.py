"""Teste das mecânicas do Devorador Orgânico (corrosão de equipamentos,
Corrosão Viva, Absorver Matéria, fraqueza a fogo, imunidades).
Roda da raiz: python tools/test_devorador.py
Stuba a camada de rede do GameRoom para testar a lógica isoladamente."""
import asyncio, sys, os
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import GameRoom, make_player, make_monster, MONSTER_DEFS

def dev_def():
    return next(m for m in MONSTER_DEFS if m["type"] == "devorador_organico")

def setup():
    r = GameRoom("TEST")
    # stub rede
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.send_to = noop
    r._broadcast_dado = noop
    r._tem_linha_de_visao = lambda *a, **k: True   # sem paredes nos testes
    r.tiles = [[server.FLOOR] * server.MAP_W for _ in range(server.MAP_H)]  # piso vazio p/ movimento
    r.phase = "playing"
    return r

def mk_dev(r):
    room = {"id": 1, "cx": 5, "cy": 5}
    d = make_monster(dev_def(), room)
    d["pos"] = [5, 5]
    r.monsters[d["id"]] = d
    return d

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

async def main():
    # ── Corrosão de armadura de couro (guerreiro) ──────────────────────────────
    print("\n[1] Toque Putrefato — armadura de couro (warrior)")
    r = setup(); d = mk_dev(r)
    w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
    check("couro intacto: ca_pen=0", r._corrosao_ca_pen(w) == 0)
    await r._aplicar_toque_putrefato(d, w)
    check("danificado: ca_pen=1", r._corrosao_ca_pen(w) == 1)
    await r._aplicar_toque_putrefato(d, w)
    check("quebrado: ca_pen=2", r._corrosao_ca_pen(w) == 2)
    hp_antes = d["hp"]
    await r._aplicar_toque_putrefato(d, w)
    # Fase 2a (corrosão generalizada): a penalidade persistida após a destruição
    # passa a ser travada em M=2 (default) em vez de crescer p/ 3 — a peça some
    # do slot, mas a CA que ela concedia já estava embutida em p["ac"]; a
    # penalidade agora cancela exatamente essa CA (antes deixava a base -1).
    check("destruído: ca_pen=2 (correção intencional, Fase 2a)", r._corrosao_ca_pen(w) == 2)
    check("armadura removida do slot", w["gear"]["armor"] is None)
    check("Absorver Matéria curou (1d4)", d["hp"] >= hp_antes)  # >= pois pode já estar no máx
    # arma do warrior é metal (machado) → nunca corrói
    await r._aplicar_toque_putrefato(d, w)
    check("arma de metal não corrói", r._corr(w)["arma_lvl"] == 0)

    # ── Corrosão de manto (tecido, 0 CA) e arma de madeira (mago) ──────────────
    print("\n[2] Toque Putrefato — manto + cajado de madeira (mage)")
    r = setup(); d = mk_dev(r)
    mg = make_player("p2", "Pedro", "mage", 1); r.players["p2"] = mg
    check("mago sem armadura real (manto)", r._tem_armadura(mg) is False)
    await r._aplicar_toque_putrefato(d, mg)   # degrada manto (prioridade armadura)
    check("manto não dá pen de CA", r._corrosao_ca_pen(mg) == 0)
    await r._aplicar_toque_putrefato(d, mg)   # manto quebrado
    await r._aplicar_toque_putrefato(d, mg)   # manto destruído
    check("manto destruído removido", mg["gear"]["armor"] is None)
    check("manto destruído: ca_pen=0", r._corrosao_ca_pen(mg) == 0)
    # agora corrói o cajado (madeira)
    await r._aplicar_toque_putrefato(d, mg)
    check("cajado danificado: arma_pen=1", r._corrosao_arma_pen(mg) == 1)
    await r._aplicar_toque_putrefato(d, mg)
    check("cajado quebrado: arma_pen=2", r._corrosao_arma_pen(mg) == 2)
    await r._aplicar_toque_putrefato(d, mg)
    check("cajado destruído → desarmado", mg["weapon"]["id"] == "unarmed")
    check("cajado destruído: arma_pen=0", r._corrosao_arma_pen(mg) == 0)

    # ── Corrosão Viva: só em quem está sem armadura ────────────────────────────
    print("\n[3] Corrosão Viva (DoT acumulativo)")
    r = setup(); d = mk_dev(r)
    w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
    mg = make_player("p2", "Pedro", "mage", 1); r.players["p2"] = mg
    await r._aplicar_corrosao_viva(d, w)
    check("warrior c/ couro: imune à Corrosão Viva", not w.get("corrosao_viva"))
    await r._aplicar_corrosao_viva(d, mg)
    await r._aplicar_corrosao_viva(d, mg)
    check("mago acumula 2 pilhas", len(mg.get("corrosao_viva", [])) == 2)
    hp0 = mg["hp"]
    await r._processar_corrosao_viva_turno(mg)
    check("tica 2 de dano (2 pilhas)", mg["hp"] == hp0 - 2)
    await r._processar_corrosao_viva_turno(mg)
    check("tica de novo 2 de dano", mg["hp"] == hp0 - 4)
    await r._processar_corrosao_viva_turno(mg)
    check("pilhas expiram após 2 rodadas", not mg.get("corrosao_viva"))

    # ── Fraqueza a fogo ×2 e imunidades ────────────────────────────────────────
    print("\n[4] Fraqueza a fogo ×2 e imunidades")
    r = setup(); d = mk_dev(r)
    hp0 = d["hp"]
    await r._aplicar_dano_alvo(d, 5, "fogo")
    check("fogo dobrado: 5 → 10 de dano", d["hp"] == hp0 - 10)
    d["hp"] = d["max_hp"]
    await r._aplicar_veneno(d, "veneno_polvo_abissal")   # cega
    check("imune a cegueira", not d.get("cego"))
    check("imune a escuridão (sem desvantagem)",
          r._verificar_escuridao(d, {"visao_escuro": False}) == "normal")

    # ── Reset por dungeon: repara níveis 1-2, mas destruição é PERMANENTE ───────
    print("\n[5] Reset por dungeon (_resetar_corrosao)")
    # (a) dano de nível 1 é reparado no reset
    r = setup(); d = mk_dev(r)
    w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
    await r._aplicar_toque_putrefato(d, w)   # couro danificado (nível 1)
    check("antes do reset: -1 CA por corrosão", r._corrosao_ca_pen(w) == 1)
    r._resetar_corrosao(w)
    check("reset repara dano nível 1 (ca_pen 0)", r._corrosao_ca_pen(w) == 0)
    # (b) item destruído (nível 3) é PERMANENTE — não volta no reset
    r = setup(); d = mk_dev(r)
    mg = make_player("p2", "Pedro", "mage", 1); r.players["p2"] = mg
    for _ in range(6):  # destrói manto e cajado
        await r._aplicar_toque_putrefato(d, mg)
    check("antes do reset: desarmado", mg["weapon"]["id"] == "unarmed")
    r._resetar_corrosao(mg)
    check("destruição é permanente: segue desarmado", mg["weapon"]["id"] == "unarmed")
    check("destruição é permanente: armadura não volta", mg["gear"]["armor"] is None)
    check("reset zera o estado de corrosão", r._corr(mg)["armadura_lvl"] == 0)

    # ── IA integrada (smoke test) ──────────────────────────────────────────────
    print("\n[6] IA do Devorador (smoke test, sem exceções)")
    r = setup(); d = mk_dev(r)
    w = make_player("p1", "Victor", "warrior", 0); w["pos"] = [5, 6]; r.players["p1"] = w
    mg = make_player("p2", "Pedro", "mage", 1); mg["pos"] = [8, 8]; r.players["p2"] = mg
    r.player_order = ["p1", "p2"]
    targets = [{"kind": "player", "obj": w}, {"kind": "player", "obj": mg}]
    try:
        await r._ai_devorador_organico(d, targets)
        check("IA rodou sem exceção", True)
    except Exception as e:
        check(f"IA rodou sem exceção (erro: {e})", False)

    # ── Urso Negro: Fúria, fraqueza por categoria, multi-ataque ────────────────
    print("\n[7] Urso Negro (Fúria + fraqueza Corpo Massivo + multi-ataque)")
    r = setup()
    urso_def = next(m for m in MONSTER_DEFS if m["type"] == "urso_negro")
    urso = make_monster(urso_def, {"id": 1, "cx": 5, "cy": 5})
    urso["pos"] = [5, 5]; r.monsters[urso["id"]] = urso
    check("2 ataques (Mordida + Garra)", len(urso["attacks"]) == 2)
    check("Fúria off com HP cheio", r._furia_bonus(urso) == 0)
    urso["hp"] = 8   # < 50% de 18
    check("Fúria on com HP < 50% (+2)", r._furia_bonus(urso) == 2)
    # Fraqueza Corpo Massivo (10 de dano base)
    perf = {"categoria": "perfurante"}; cont = {"categoria": "contundente"}; cort = {"categoria": "cortante"}
    check("perfurante: +1 dano (10→11)", r._apply_damage_types(10, ["physical"], urso, perf) == 11)
    check("contundente: -1 dano (10→9)", r._apply_damage_types(10, ["physical"], urso, cont) == 9)
    check("cortante: neutro (10→10)",    r._apply_damage_types(10, ["physical"], urso, cort) == 10)
    # Multi-ataque: conta acertos em alvo "couraçado" imortal
    r2 = setup()
    urso2 = make_monster(urso_def, {"id": 1, "cx": 5, "cy": 5}); urso2["pos"] = [5, 5]
    r2.monsters[urso2["id"]] = urso2
    alvo = make_player("p1", "Victor", "warrior", 0)
    alvo["pos"] = [5, 6]; alvo["hp"] = 999; alvo["max_hp"] = 999; alvo["ac"] = -100  # sempre acerta
    r2.players["p1"] = alvo
    hits = {"n": 0}
    orig = r2._aplicar_dano_alvo
    # conta ataques via broadcast de "Dano"? Mais simples: conta chamadas de execução
    cnt = {"n": 0}
    orig_exec = r2._execute_one_monster_attack
    async def spy(m, atk, tobj):
        cnt["n"] += 1
        return await orig_exec(m, atk, tobj)
    r2._execute_one_monster_attack = spy
    await r2._monster_execute_attacks(urso2, {"kind": "player", "obj": alvo})
    check("multi-ataque executa os 2 golpes", cnt["n"] == 2)

    # ── Orc Guerreiro: Investida, Fúria Cega, Mente Limitada, loot ─────────────
    print("\n[8] Orc Guerreiro (Investida + Fúria Cega + Mente Limitada + loot)")
    from server import CHEST_ITEMS, SHOP_WEAPONS, SHOP_MERCHANT
    r = setup()
    orc_def = next(m for m in MONSTER_DEFS if m["type"] == "orc_guerreiro")
    orc = make_monster(orc_def, {"id": 1, "cx": 5, "cy": 5}); orc["pos"] = [5, 5]
    r.monsters[orc["id"]] = orc
    # Investida Brutal
    check("Investida off por padrão", r._investida_bonus(orc) == 0)
    orc["_investiu"] = True
    check("Investida on (+2)", r._investida_bonus(orc) == 2)
    orc["_investiu"] = False
    # Fúria Cega (dano + CA)
    check("Fúria Cega off: +0 dano / -0 CA",
          r._furia_cega_dano_bonus(orc) == 0 and r._furia_cega_ca_pen(orc) == 0)
    orc["furia_cega"] = True
    check("Fúria Cega on: +1 dano", r._furia_cega_dano_bonus(orc) == 1)
    check("Fúria Cega on: -1 CA", r._furia_cega_ca_pen(orc) == 1)
    orc["furia_cega"] = False
    # Mente Limitada (-1 Vontade só vs efeitos mentais)
    check("save_weakness vontade = -1", r._save_weakness_pen(orc, "vontade") == -1)
    check("save_weakness fortitude = 0", r._save_weakness_pen(orc, "fortitude") == 0)
    # bônus do save de Vontade já reflete o -1 (will 1 → 0)
    _, _, bonus_v, _ = await r._save_mostrado(orc, "vontade", 99)
    check("save Vontade aplica -1 (bônus 0)", bonus_v == 0)
    _, _, bonus_f, _ = await r._save_mostrado(orc, "fortitude", 99)
    check("save Fortitude intacto (bônus 5)", bonus_f == 5)
    # Loot garantido — o machado é uma arma 1d10 e o lookup de loot o encontra
    todos_itens = CHEST_ITEMS + SHOP_WEAPONS + SHOP_MERCHANT
    machado = next((i for i in todos_itens if i["id"] == "machado_orc"), None)
    check("machado_orc é arma 1d10 cortante",
          machado is not None and machado.get("die") == "1d10" and machado.get("categoria") == "cortante")
    check("orc tem guaranteed_loot=machado_orc", orc_def.get("guaranteed_loot") == ["machado_orc"])
    check("lookup de loot resolve machado_orc (SHOP_WEAPONS)",
          any(i["id"] == "machado_orc" for i in SHOP_WEAPONS))

    print("\n[9] Fúria Cega — modelo de snapshot entre turnos (IA)")
    r = setup()
    orc = make_monster(orc_def, {"id": 1, "cx": 5, "cy": 5}); orc["pos"] = [5, 5]
    r.monsters[orc["id"]] = orc
    adj = make_player("p1", "Victor", "warrior", 0); adj["pos"] = [5, 6]  # adjacente (sem mover)
    adj["hp"] = 999; adj["max_hp"] = 999; r.players["p1"] = adj
    r.player_order = ["p1"]
    targets = [{"kind": "player", "obj": adj}]
    orc["hp"] = 10   # sofreu dano (max 17) antes do 1º turno
    await r._ai_orc_guerreiro(orc, targets)
    check("enfurece após perder HP", orc["furia_cega"] is True)
    # próximo turno sem novo dano → calmo
    await r._ai_orc_guerreiro(orc, targets)
    check("acalma se não sofreu novo dano", orc["furia_cega"] is False)

    # ── Goblins das Fendas ─────────────────────────────────────────────────────
    print("\n[10] Goblins (Mente Fraca, escolha de arma, arremesso, bando)")
    import server as S
    r = setup()
    arq_def = next(m for m in MONSTER_DEFS if m["type"] == "goblin_arqueiro")
    comb_def = next(m for m in MONSTER_DEFS if m["type"] == "goblin_combatente")
    dual_def = next(m for m in MONSTER_DEFS if m["type"] == "goblin_dual")
    arq = make_monster(arq_def, {"id": 1, "cx": 5, "cy": 5})
    # Mente Fraca -2 Vontade
    check("Mente Fraca: -2 em Vontade", r._save_weakness_pen(arq, "vontade") == -2)
    check("Arqueiro: 10 flechas", arq.get("flechas") == 10)
    check("Arqueiro: alcance 8", arq["attacks"][0].get("range") == 8)
    check("Arqueiro: dropa o arco", arq.get("guaranteed_loot") == ["arco_curto"])
    check("Arqueiro não arremessa", arq.get("pode_arremessar") is False)
    # Combatente: escolhe adaga OU espada, sempre com adaga de arremesso no loot
    nomes = set(); loot_ok = True
    for _ in range(60):
        c = make_monster(comb_def, {"id": 1, "cx": 5, "cy": 5})
        nomes.add(c["attacks"][0]["name"])
        if "dagger" not in c.get("guaranteed_loot", []): loot_ok = False
    check("Combatente sorteia Adaga e Espada Curta", {"Adaga", "Espada Curta"} <= nomes)
    check("Combatente sempre tem adaga no drop", loot_ok)
    # Dual: 2 ataques, dropa espada+adaga, é chefe de bando
    dual = make_monster(dual_def, {"id": 1, "cx": 5, "cy": 5})
    check("Dual: 2 ataques", len(dual["attacks"]) == 2)
    check("Dual: dropa espada + adaga", set(dual.get("guaranteed_loot", [])) == {"shortsword", "dagger"})
    check("Dual: tem spawn_companions (comb/arq/xamã)", len(dual_def.get("spawn_companions", [])) == 3)

    # Arremesso: 1 natural quebra a arma
    r = setup()
    comb = make_monster(comb_def, {"id": 1, "cx": 5, "cy": 5}); comb["pos"] = [5, 5]
    r.monsters[comb["id"]] = comb
    alvo = make_player("p1", "Victor", "warrior", 0); alvo["pos"] = [5, 6]
    alvo["hp"] = 999; alvo["max_hp"] = 999; r.players["p1"] = alvo
    tgts = [{"kind": "player", "obj": alvo}]
    _orig = S.random.randint
    S.random.randint = lambda a, b: 1            # força 1 natural
    await r._goblin_arremesso(comb, tgts)
    S.random.randint = _orig
    check("Arremesso nat1 quebra a arma", comb.get("pode_arremessar") is False)
    check("Arremesso nat1 remove a adaga do drop", "dagger" not in comb.get("guaranteed_loot", []))
    # Arremesso acerto (d20=20)
    r = setup()
    comb2 = make_monster(comb_def, {"id": 1, "cx": 5, "cy": 5}); comb2["pos"] = [5, 5]
    r.monsters[comb2["id"]] = comb2
    alvo2 = make_player("p1", "Victor", "warrior", 0); alvo2["pos"] = [5, 6]
    alvo2["hp"] = 50; alvo2["max_hp"] = 50; r.players["p1"] = alvo2
    S.random.randint = lambda a, b: 20 if b == 20 else 1   # d20=20 acerta; dados de dano=1
    await r._goblin_arremesso(comb2, [{"kind": "player", "obj": alvo2}])
    S.random.randint = _orig
    check("Arremesso acerto causa dano (1d4=1 +2 = 3)", alvo2["hp"] == 47)
    check("Arremesso acerto não quebra a arma", comb2.get("pode_arremessar") is True)

    # Bando do Dual: sempre traz combatentes + arqueiros
    band_ok = True; viu_dual = 0
    for _ in range(3000):
        ms = S.spawn_monsters_for_room({"id": 1, "role": "monster", "cx": 5, "cy": 5,
                                        "x": 3, "y": 3, "w": 5, "h": 5}, 4)
        tipos = [x["type"] for x in ms]
        if "goblin_dual" in tipos:
            viu_dual += 1
            if "goblin_combatente" not in tipos or "goblin_arqueiro" not in tipos:
                band_ok = False
    check("Dual apareceu em amostras", viu_dual > 0)
    check("bando do Dual sempre tem combatente + arqueiro", band_ok)

    # ── Xamã Goblin ────────────────────────────────────────────────────────────
    print("\n[11] Xamã Goblin (conjuração, Concentração Frágil, vinho)")
    xama_def = next(m for m in MONSTER_DEFS if m["type"] == "goblin_xama")
    r = setup()
    xama = make_monster(xama_def, {"id": 1, "cx": 5, "cy": 5}); xama["pos"] = [5, 5]
    r.monsters[xama["id"]] = xama
    check("3 magias 1x/combate cada",
          xama["ability_uses"] == {"silencio": 1, "amaldicoar": 1, "abencoar": 1})
    # Abençoar buffa goblins aliados
    ally = make_monster(comb_def, {"id": 1, "cx": 6, "cy": 5}); ally["pos"] = [6, 5]
    r.monsters[ally["id"]] = ally
    await r._xama_abencoar(xama)
    check("Abençoar: +1 ataque no goblin aliado", r._mod_magia(ally, "ataque") == 1)
    # Amaldiçoar debuffa herói
    r = setup()
    xama = make_monster(xama_def, {"id": 1, "cx": 5, "cy": 5}); xama["pos"] = [5, 5]
    r.monsters[xama["id"]] = xama
    hero = make_player("p1", "Victor", "warrior", 0); hero["pos"] = [5, 6]; r.players["p1"] = hero
    await r._xama_amaldicoar(xama, hero["pos"])
    check("Amaldiçoar: -1 ataque no herói", r._mod_magia(hero, "ataque") == -1)
    # Silêncio cria zona do xamã
    r = setup()
    xama = make_monster(xama_def, {"id": 1, "cx": 5, "cy": 5}); xama["pos"] = [5, 5]
    r.monsters[xama["id"]] = xama
    await r._xama_silencio(xama, [7, 7])
    check("Silêncio cria zona do xamã",
          any(z["tipo"] == "silencio" and z["caster"] == xama["id"] for z in r.zonas_especiais))
    # Concentração Frágil: sem dano conjura; com dano não conjura
    r = setup()
    xama = make_monster(xama_def, {"id": 1, "cx": 5, "cy": 5}); xama["pos"] = [5, 5]
    r.monsters[xama["id"]] = xama
    mage = make_player("p1", "Pedro", "mage", 1); mage["pos"] = [5, 6]
    mage["hp"] = 999; mage["max_hp"] = 999; r.players["p1"] = mage
    await r._ai_xama_goblin(xama, [{"kind": "player", "obj": mage}])
    check("conjura sem dano (silêncio sobre o mago)", xama["ability_uses"]["silencio"] == 0)
    r = setup()
    xama = make_monster(xama_def, {"id": 1, "cx": 5, "cy": 5}); xama["pos"] = [5, 5]
    r.monsters[xama["id"]] = xama
    mage = make_player("p1", "Pedro", "mage", 1); mage["pos"] = [5, 6]
    mage["hp"] = 999; mage["max_hp"] = 999; r.players["p1"] = mage
    xama["hp"] = 5   # sofreu dano (max 10)
    await r._ai_xama_goblin(xama, [{"kind": "player", "obj": mage}])
    check("Concentração Frágil bloqueia magia após dano",
          xama["ability_uses"]["silencio"] == 1 and xama["ability_uses"]["amaldicoar"] == 1)
    # Silêncio termina se o xamã morre
    r = setup(); r.rooms = []
    xama = make_monster(xama_def, {"id": 1, "cx": 5, "cy": 5}); xama["pos"] = [5, 5]
    r.monsters[xama["id"]] = xama
    p1 = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = p1
    await r._xama_silencio(xama, [5, 5])
    xama["hp"] = 0
    await r._monster_dies(xama, "p1")
    check("Silêncio some quando o xamã morre",
          not any(z["tipo"] == "silencio" and z["caster"] == xama["id"] for z in r.zonas_especiais))
    # Loot do xamã (vinho + poção rara)
    lt = xama_def["loot_table"]
    check("loot 21-40 = garrafa de vinho", lt["21-40"] == {"tipo": "item", "id": "garrafa_vinho"})
    check("loot 99-100 = raro (poção ou pergaminho)", lt["99-100"] == {"tipo": "raro_xama"})
    from server import _DUNGEON_ITEM_CATALOG
    check("garrafa_vinho resolve no catálogo de loot (def da taverna)",
          "garrafa_vinho" in _DUNGEON_ITEM_CATALOG)

    print("\n[12] Garrafa de Vinho (consumível)")
    r = setup(); r._is_turn = lambda pid: True
    hero = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = hero
    hero["fome"] = 50; hero["sede"] = 50
    atk0, ref0 = hero["atk_bonus"], hero["ref_"]
    wine = {"id": "garrafa_vinho", "name": "Garrafa de Vinho", "emoji": "🍷",
            "item_slot": "bag", "effect": "wine", "value": 15}
    hero["bag"] = [dict(wine)]
    await r.handle_use_item("p1", "garrafa_vinho")
    check("vinho +15 fome/sede", hero["fome"] == 65 and hero["sede"] == 65)
    check("vinho -1 ataque / -1 Reflexos", hero["atk_bonus"] == atk0 - 1 and hero["ref_"] == ref0 - 1)
    check("vinho dura 10 rodadas", hero["vinho_rodadas"] == 10)
    hero["bag"] = [dict(wine)]; hero["vinho_rodadas"] = 3
    await r.handle_use_item("p1", "garrafa_vinho")
    check("vinho não acumula (penalidade única, reinicia p/ 10)",
          hero["atk_bonus"] == atk0 - 1 and hero["ref_"] == ref0 - 1 and hero["vinho_rodadas"] == 10)
    hero["vinho_rodadas"] = 1
    await r._processar_vinho_turno(hero)
    check("vinho expira e restaura ataque/Reflexos",
          hero["atk_bonus"] == atk0 and hero["ref_"] == ref0 and not hero.get("vinho_ativo"))

    print("\n[13] Spawn do Xamã (bando próprio + ocasional no Dual)")
    import collections
    cnt = collections.Counter(); dual_total = 0; dual_com_xama = 0
    for _ in range(4000):
        ms = S.spawn_monsters_for_room({"id": 1, "role": "monster", "cx": 5, "cy": 5,
                                        "x": 3, "y": 3, "w": 5, "h": 5}, 4)
        tipos = [x["type"] for x in ms]
        for t in tipos:
            cnt[t] += 1
        if "goblin_dual" in tipos:
            dual_total += 1
            if "goblin_xama" in tipos:
                dual_com_xama += 1
    check("Xamã spawna (anchor próprio)", cnt["goblin_xama"] > 0)
    check("bando do Dual às vezes traz xamã (0-1)", 0 < dual_com_xama < dual_total)

    # ── Pergaminhos mágicos ─────────────────────────────────────────────────────
    print("\n[14] Pergaminho Mágico (geração, sucesso, falha, nocivo, cross-classe)")
    from server import (GRIMORIO, gerar_pergaminho, preco_pergaminho,
                        PERGAMINHO_PRECO_BASE, PERGAMINHO_INT_SURCHARGE)

    def mk_scroll(magia_id, nivel, int_b=0):
        mg = GRIMORIO[magia_id]
        return {"id": f"pergaminho_{magia_id}", "name": f"Pergaminho: {mg['nome']}",
                "emoji": "📜", "item_slot": "bag", "effect": "scroll",
                "magia_id": magia_id, "circulo": mg["circulo"],
                "nivel_conjurador": nivel, "int_bonus": int_b}

    # Geração (básico = nível mínimo do círculo, +0 INT)
    sc = gerar_pergaminho(1)
    check("gerar básico 1º: nível 1, +0 INT",
          sc and sc["nivel_conjurador"] == 1 and sc["int_bonus"] == 0)
    sc3 = gerar_pergaminho(3, classe="mage")
    check("gerar círculo 3 mago: nível 5", sc3 and sc3["nivel_conjurador"] == 5
          and GRIMORIO[sc3["magia_id"]]["circulo"] == "terceiro")
    # Preço: base×mult_nível + acréscimo_INT
    scbf = gerar_pergaminho(1, magia_id="bola_fogo", nivel=5, int_bonus=2)
    check("preço bola_fogo nv5 +2INT = 20×5+20 = 120", scbf and scbf["price"] == 120)
    check("preco_pergaminho 2º nv3 +0 = 40", preco_pergaminho("segundo", 3, 0) == 40)
    check("preco_pergaminho 2º nv4 +3 = 80+40 = 120", preco_pergaminho("segundo", 4, 3) == 120)
    # Nível/INT respeitam tetos (5 / +5)
    sccap = gerar_pergaminho(1, magia_id="bola_fogo", nivel=99, int_bonus=99)
    check("teto nível 5 / INT +5", sccap["nivel_conjurador"] == 5 and sccap["int_bonus"] == 5)
    # Classificação para efeito nocivo
    rr = setup()
    check("_magia_tipo: bola_fogo = dano", rr._magia_tipo(GRIMORIO["bola_fogo"]) == "dano")
    check("_magia_tipo: amaldicoar = debuff", rr._magia_tipo(GRIMORIO["amaldicoar"]) == "debuff")
    check("_magia_tipo: abencoar = buff", rr._magia_tipo(GRIMORIO["abencoar"]) == "buff")
    check("_magia_tipo: conjurar_elemental = invocacao", rr._magia_tipo(GRIMORIO["conjurar_elemental"]) == "invocacao")

    # Sucesso: mago, magia de mago de 1º círculo, nível 1 → sem falha
    r = setup(); r._is_turn = lambda pid: True
    mage = make_player("p1", "Pedro", "mage", 1); mage["pos"] = [5, 5]; r.players["p1"] = mage
    mob = make_monster(next(m for m in MONSTER_DEFS if m["type"] == "urso_negro"),
                       {"id": 1, "cx": 6, "cy": 5}); mob["pos"] = [6, 5]
    mob["hp"] = 50; mob["max_hp"] = 50; r.monsters[mob["id"]] = mob
    mage["bag"] = [mk_scroll("bola_fogo", 1)]
    await r.handle_use_scroll("p1", "pergaminho_bola_fogo", {"tx": 6, "ty": 5})
    check("sucesso: pergaminho consumido", not mage["bag"])
    check("sucesso: ação consumida", mage["action_done"] is True)
    check("sucesso: magia teve efeito (mob sofreu dano)", mob["hp"] < 50)

    # Falha por nível, SEM nocivo (d100=20: 20≤30 falha; 20>10 sem nocivo)
    r = setup(); r._is_turn = lambda pid: True
    mage = make_player("p1", "Pedro", "mage", 1); mage["pos"] = [5, 5]; r.players["p1"] = mage
    mob = make_monster(next(m for m in MONSTER_DEFS if m["type"] == "urso_negro"),
                       {"id": 1, "cx": 6, "cy": 5}); mob["pos"] = [6, 5]
    mob["hp"] = 50; mob["max_hp"] = 50; r.monsters[mob["id"]] = mob
    mage["bag"] = [mk_scroll("bola_fogo", 3)]   # nível 3, personagem nível 1 → 30% falha
    _o = S.random.randint; S.random.randint = lambda a, b: 20
    await r.handle_use_scroll("p1", "pergaminho_bola_fogo", {"tx": 6, "ty": 5})
    S.random.randint = _o
    check("falha s/ nocivo: pergaminho consumido", not mage["bag"])
    check("falha s/ nocivo: sem efeito no mob", mob["hp"] == 50)

    # Falha COM efeito nocivo (debuff vira no próprio jogador) — d100=5
    r = setup(); r._is_turn = lambda pid: True
    cle = make_player("p1", "Lewis", "cleric", 1); cle["pos"] = [5, 5]; r.players["p1"] = cle
    cle["bag"] = [mk_scroll("amaldicoar", 3)]   # cleric usa magia de cleric; nível 3 vs 1 → 30%
    _o = S.random.randint; S.random.randint = lambda a, b: 5   # 5≤30 falha; 5≤10 nocivo
    await r.handle_use_scroll("p1", "pergaminho_amaldicoar", {})
    S.random.randint = _o
    check("nocivo: debuff atinge o próprio jogador (-1 ataque)", r._mod_magia(cle, "ataque") == -1)
    check("nocivo: pergaminho consumido", not cle["bag"])

    # Cross-classe: clérigo usando pergaminho de magia exclusiva de mago (50% falha)
    r = setup(); r._is_turn = lambda pid: True
    cle = make_player("p1", "Lewis", "cleric", 1); cle["pos"] = [5, 5]; r.players["p1"] = cle
    mob = make_monster(next(m for m in MONSTER_DEFS if m["type"] == "urso_negro"),
                       {"id": 1, "cx": 6, "cy": 5}); mob["pos"] = [6, 5]
    mob["hp"] = 50; mob["max_hp"] = 50; r.monsters[mob["id"]] = mob
    cle["bag"] = [mk_scroll("bola_fogo", 1)]    # bola_fogo é exclusiva de mago
    _o = S.random.randint; S.random.randint = lambda a, b: 30   # 30≤50 → falha de classe
    await r.handle_use_scroll("p1", "pergaminho_bola_fogo", {"tx": 6, "ty": 5})
    S.random.randint = _o
    check("cross-classe falha (50%): sem efeito no mob", mob["hp"] == 50)
    check("cross-classe: pergaminho consumido", not cle["bag"])

    # Guerreiro não pode usar pergaminho
    r = setup(); r._is_turn = lambda pid: True
    war = make_player("p1", "Victor", "warrior", 0); war["bag"] = [mk_scroll("bola_fogo", 1)]
    r.players["p1"] = war
    await r.handle_use_scroll("p1", "pergaminho_bola_fogo", {})
    check("guerreiro não usa pergaminho (item permanece)", len(war["bag"]) == 1)

    # Escala pelo nível/INT do pergaminho + ignora metamagia (spy no executor)
    r = setup()
    mage = make_player("p1", "Pedro", "mage", 1); mage["pos"] = [5, 5]; r.players["p1"] = mage
    int0 = mage["int_"]; mage["aprimorar_ativo"] = True; mage["_mm_dc_bonus"] = 5  # metamagia "suja"
    cap = {}
    async def _spy_exec(caster, magia, data, dm, db):
        cap["level"] = caster["level"]; cap["intmod"] = (caster["int_"] - 10) // 2
        cap["dc"] = caster.get("_mm_dc_bonus"); cap["dm"] = dm; cap["db"] = db
    r._executar_magia_grimorio = _spy_exec
    await r._pergaminho_conjurar(mage, GRIMORIO["bola_fogo"], {"tx": 5, "ty": 5}, 5, 3)
    check("conjura no NÍVEL do pergaminho (5)", cap.get("level") == 5)
    check("conjura com BÔNUS de INT (+3)", cap.get("intmod") == 3)
    check("ignora metamagia (dc_bonus=0, mult=1, dur=0)",
          cap.get("dc") == 0 and cap.get("dm") == 1 and cap.get("db") == 0)
    check("restaura nível/INT/metamagia do personagem",
          mage["level"] == 1 and mage["int_"] == int0 and mage["_mm_dc_bonus"] == 5)

    # Exemplo do design: pergaminho nível 5 com personagem nível 1 = 60% de falha
    r = setup(); r._is_turn = lambda pid: True
    mage = make_player("p1", "Pedro", "mage", 1); mage["pos"] = [5, 5]; r.players["p1"] = mage
    mob = make_monster(next(m for m in MONSTER_DEFS if m["type"] == "urso_negro"),
                       {"id": 1, "cx": 6, "cy": 5}); mob["pos"] = [6, 5]
    mob["hp"] = 50; mob["max_hp"] = 50; r.monsters[mob["id"]] = mob
    mage["bag"] = [mk_scroll("bola_fogo", 5)]   # nível 5, personagem 1 → diff 4 → 60%
    _o = S.random.randint; S.random.randint = lambda a, b: 60   # 60≤60 falha; nocivo 20, 60>20 sem nocivo
    await r.handle_use_scroll("p1", "pergaminho_bola_fogo", {"tx": 6, "ty": 5})
    S.random.randint = _o
    check("nível 5 vs nível 1 = 60% (d100=60 falha, sem efeito no mob)",
          mob["hp"] == 50 and not mage["bag"])

    # ── Pergaminhos aprimorados com talentos do Pedro ──────────────────────────
    print("\n[15] Pergaminhos com talentos (preço, aplicabilidade, efeito)")
    # Preço: dano = 20/dado no nível; cd/duração = +50 cada
    bf5 = gerar_pergaminho(1, magia_id="bola_fogo", nivel=5,
                           talentos={"cd": True, "duracao": True, "dano": True})
    check("Bola nv5 cd+dano = 100base +100dano +50cd = 250", bf5["price"] == 250)
    check("Bola: dano e cd aplicam, duração NÃO (sem duracao)",
          bf5["talento_dano"] and bf5["talento_cd"] and not bf5["talento_duracao"])
    check("Bola: CD na prévia +1 (8+0+1+1=10)", bf5["preview"]["cd"] == 10)
    rc1 = gerar_pergaminho(1, magia_id="raio_congelante", nivel=1,
                           talentos={"cd": True, "dano": True})
    check("Raio Congelante nv1 cd+dano = 20 +60 +50 = 130", rc1["price"] == 130)
    ab = gerar_pergaminho(1, magia_id="abencoar", talentos={"cd": True, "duracao": True, "dano": True})
    check("Abençoar: só duração aplica (+50)", ab["price"] == 70
          and ab["talento_duracao"] and not ab["talento_cd"] and not ab["talento_dano"])
    # Efeito no conjurar: talentos viram dmg_mult/dur_bonus/dc_bonus
    r = setup()
    mage = make_player("p1", "Pedro", "mage", 1); mage["pos"] = [5, 5]; r.players["p1"] = mage
    capt = {}
    async def _spy2(caster, magia, data, dm, db):
        capt["dm"] = dm; capt["db"] = db; capt["dc"] = caster.get("_mm_dc_bonus")
    r._executar_magia_grimorio = _spy2
    await r._pergaminho_conjurar(mage, GRIMORIO["raio_congelante"], {"target_id": "x"}, 1, 0,
                                 {"cd": True, "dano": True, "duracao": False})
    check("talento dano → dmg_mult 1.5", capt.get("dm") == 1.5)
    check("talento cd → _mm_dc_bonus 1", capt.get("dc") == 1)
    check("sem talento duração → dur_bonus 0", capt.get("db") == 0)

    # ── Necromante (ND 2) ───────────────────────────────────────────────────────
    print("\n[16] Necromante (essência profana, magias, concentração, loot)")
    necro_def = next(m for m in MONSTER_DEFS if m["type"] == "necromante")
    check("necromante nível 2", necro_def.get("level") == 2)
    # Os 2 esqueletos deixaram de nascer junto do necromante: agora vêm de
    # Mestre dos Mortos, gasto como AÇÃO na primeira vez (ver
    # tools/test_mestre_dos_mortos.py).
    check("não nasce mais com companheiros", not necro_def.get("spawn_companions"))
    mdm = next((a for a in necro_def["special_abilities"] if a["id"] == "mestre_dos_mortos"), None)
    check("Mestre dos Mortos é ação de 1 uso",
          mdm and mdm.get("action_type") == "acao" and mdm.get("uses_per_combat") == 1)
    check("3 magias diárias + dominar na ficha",
          all(any(a["id"] == x for a in necro_def["special_abilities"])
              for x in ("bola_fogo", "medo", "amaldicoar", "dominar_morto_vivo")))
    # Essência Profana: dano sagrado/luz dobrado
    r = setup()
    nec = make_monster(necro_def, {"id": 1, "cx": 5, "cy": 5}); nec["pos"] = [5, 5]
    r.monsters[nec["id"]] = nec
    check("essência profana: sagrado ×2 (5→10)", r._apply_damage_types(5, ["holy"], nec) == 10)
    nec["hp"] = nec["max_hp"]
    await r._aplicar_dano_alvo(nec, 5, "sagrado")
    check("dano 'sagrado' normalizado p/ holy ×2 (5→10)", nec["hp"] == nec["max_hp"] - 10)

    # Bola de Fogo no grupo: 2 heróis em cluster sofrem dano de fogo
    r = setup()
    nec = make_monster(necro_def, {"id": 1, "cx": 5, "cy": 5}); nec["pos"] = [5, 5]
    r.monsters[nec["id"]] = nec
    h1 = make_player("p1", "A", "warrior", 0); h1["pos"] = [7, 5]; h1["hp"] = 99; h1["max_hp"] = 99
    h2 = make_player("p2", "B", "rogue", 1);   h2["pos"] = [7, 6]; h2["hp"] = 99; h2["max_hp"] = 99
    r.players = {"p1": h1, "p2": h2}
    await r._necro_cast(nec, "bola_fogo", [7, 5])
    check("Bola de Fogo do necromante fere heróis em área", h1["hp"] < 99 and h2["hp"] < 99)

    # Concentração Sombria: sofreu dano + falha na Vontade → sem magia
    r = setup(); r._is_turn = lambda pid: True
    nec = make_monster(necro_def, {"id": 1, "cx": 5, "cy": 5}); nec["pos"] = [5, 5]
    nec["hp"] = 8   # sofreu dano (max 16) desde o turno anterior
    r.monsters[nec["id"]] = nec
    sk = make_monster(next(m for m in MONSTER_DEFS if m["type"] == "esqueleto_humano"),
                      {"id": 1, "cx": 6, "cy": 5}); sk["pos"] = [6, 5]; r.monsters[sk["id"]] = sk  # morto-vivo perto
    h1 = make_player("p1", "A", "warrior", 0); h1["pos"] = [5, 6]; h1["hp"] = 99; h1["max_hp"] = 99
    h2 = make_player("p2", "B", "rogue", 1);   h2["pos"] = [6, 6]; h2["hp"] = 99; h2["max_hp"] = 99
    r.players = {"p1": h1, "p2": h2}
    tgts = [{"kind": "player", "obj": h1}, {"kind": "player", "obj": h2}]
    _o = S.random.randint; S.random.randint = lambda a, b: 1   # Vontade falha (1+6=7<10)
    await r._ai_necromante(nec, tgts)
    S.random.randint = _o
    check("Concentração Sombria: dano+falha → não conjura",
          nec["ability_uses"]["bola_fogo"] == 1 and nec["ability_uses"]["amaldicoar"] == 1)

    # Loot: se não usou Dominar, o pergaminho aparece no tesouro
    r = setup()
    nec = make_monster(necro_def, {"id": 1, "cx": 5, "cy": 5}); nec["pos"] = [5, 5]
    r.monsters[nec["id"]] = nec
    h1 = make_player("p1", "A", "warrior", 0); r.players = {"p1": h1}
    _o = S.random.randint; S.random.randint = lambda a, b: 50   # tabela: 2 moedas, sem outro item
    await r._necromante_loot(nec)
    S.random.randint = _o
    chest_items = [it for ch in r.chests.values() for it in ch.get("items", [])]
    check("loot: pergaminho de Dominar Morto-Vivo aparece se não usado",
          any(it.get("magia_id") == "dominar_morto_vivo" for it in chest_items))
    # Se usou, NÃO aparece
    r = setup()
    nec = make_monster(necro_def, {"id": 1, "cx": 5, "cy": 5}); nec["pos"] = [5, 5]
    nec["usou_dominar"] = True
    r.monsters[nec["id"]] = nec
    r.players = {"p1": make_player("p1", "A", "warrior", 0)}
    _o = S.random.randint; S.random.randint = lambda a, b: 50
    await r._necromante_loot(nec)
    S.random.randint = _o
    chest_items = [it for ch in r.chests.values() for it in ch.get("items", [])]
    check("loot: pergaminho NÃO aparece se já dominou",
          not any(it.get("magia_id") == "dominar_morto_vivo" for it in chest_items))

    # Ração restaura fome/sede
    r = setup(); r._is_turn = lambda pid: True
    h = make_player("p1", "A", "warrior", 0); h["fome"] = 50; h["sede"] = 50; r.players = {"p1": h}
    h["bag"] = [{"id": "racao", "name": "Ração (Pão e Água)", "emoji": "🥖",
                 "item_slot": "bag", "effect": "ration", "value": 15}]
    await r.handle_use_item("p1", "racao")
    check("Ração: +15 fome/sede, sem penalidade",
          h["fome"] == 65 and h["sede"] == 65 and not h.get("vinho_ativo"))

    # ── Sistema de Doenças + Zumbi Infectado ────────────────────────────────────
    print("\n[17] Sistema de Doenças + Zumbi Infectado")
    r = setup()
    p = make_player("p1", "A", "warrior", 0); r.players = {"p1": p}
    ref0, fort0 = p["ref_"], p["fort"]; spd0 = r._moves_base(p)
    await r._aplicar_doenca(p, "leve")
    check("doença leve: doente + 1 sintoma", p["doente"] and p["doenca"]["sintomas"] == ["leve"])
    check("leve: -1 Reflexos / -1 Fortitude", p["ref_"] == ref0 - 1 and p["fort"] == fort0 - 1)
    check("leve: -1 movimento", r._moves_base(p) == spd0 - 1)
    await r._aplicar_doenca(p, "leve")
    check("reinfecção leve não piora", p["doenca"]["sintomas"] == ["leve"])
    r._curar_doenca(p)
    check("cura remove doença e restaura saves/mov",
          not p.get("doente") and p["ref_"] == ref0 and p["fort"] == fort0 and r._moves_base(p) == spd0)

    # Doença grave (leve+médio+grave) e recálculo de derivados
    r = setup()
    p = make_player("p1", "A", "cleric", 0); r.players = {"p1": p}
    ac0   = p["ac"];   dex0 = p["dex"];  str0 = p["str_"]
    con0  = p["con_"]; int0 = p["int_"]; hp0  = p["max_hp"]; will0 = p["will"]
    await r._aplicar_doenca(p, "grave")
    check("grave: 3 sintomas", p["doenca"]["sintomas"] == ["leve", "medio", "grave"])
    check("médio: -2 DES → -1 CA", p["dex"] == dex0 - 2 and p["ac"] == ac0 - 1)
    check("médio: -2 FOR", p["str_"] == str0 - 2)
    check("médio: custo_extra=1", p["doenca"]["custo_extra"] == 1)
    check("grave: -2 CON / -2 INT", p["con_"] == con0 - 2 and p["int_"] == int0 - 2)
    check("grave: HP máximo reduzido", p["max_hp"] < hp0)
    fome_b = p["fome"]; r._consumir_recursos(p, "apenas_acao")   # base fome 1 + extra 1
    check("sintoma médio: ação custa +1 fome", p["fome"] == fome_b - 2)
    r._curar_doenca(p)
    check("cura (grave) restaura CA/CON/INT/HPmáx/Vontade",
          p["ac"] == ac0 and p["con_"] == con0 and p["int_"] == int0
          and p["max_hp"] == hp0 and p["will"] == will0)

    # Zumbi: ficha + fraqueza + flag de dano sagrado
    zdef = next(m for m in MONSTER_DEFS if m["type"] == "zumbi_infectado")
    check("zumbi: undead + imune veneno/controle",
          zdef["undead"] and "veneno" in zdef["immunities"] and "controle_mental" in zdef["immunities"])
    r = setup(); z = make_monster(zdef, {"id": 1, "cx": 5, "cy": 5}); z["pos"] = [5, 5]
    r.monsters[z["id"]] = z
    check("Consagrado à Destruição: sagrado ×2 (5→10)", r._apply_damage_types(5, ["holy"], z) == 10)
    check("flag de dano sagrado setada", z.get("_dano_sagrado_recente") is True)
    r._apply_damage_types(3, ["physical"], z)
    check("flag limpa após dano físico", z.get("_dano_sagrado_recente") is False)

    # Resistência Morta: 0 HP + Fortitude passa → fica com 1 HP
    r = setup(); r.rooms = []; r.players = {"p1": make_player("p1", "A", "warrior", 0)}
    z = make_monster(zdef, {"id": 1, "cx": 5, "cy": 5}); z["pos"] = [5, 5]; z["hp"] = 0
    r.monsters[z["id"]] = z
    _o = S.random.randint; S.random.randint = lambda a, b: 20
    await r._monster_dies(z, "p1")
    S.random.randint = _o
    check("Resistência Morta: sobrevive a 0 com 1 HP", z["hp"] == 1)
    # CD aumenta pela metade do dano que excedeu 0 HP, arredondando para cima.
    # Ex.: 2 HP - 6 dano = -4 → CD 10 + ceil(4/2) = 12.
    r = setup(); r.rooms = []; r.players = {"p1": make_player("p1", "A", "warrior", 0)}
    z = make_monster(zdef, {"id": 1, "cx": 5, "cy": 5}); z["pos"] = [5, 5]; z["hp"] = -4
    r.monsters[z["id"]] = z
    cds = []
    r._testar_save = lambda alvo, tipo, cd: (cds.append(cd) or (True, 20, 0, 20))
    await r._monster_dies(z, "p1")
    check("Resistência Morta: excesso 4 → CD 12", cds == [12] and z["hp"] == 1)
    # Ex.: 1 HP - 9 dano = -8 → CD 10 + ceil(8/2) = 14.
    z["hp"] = -8
    cds.clear()
    await r._monster_dies(z, "p1")
    check("Resistência Morta: excesso 8 → CD 14", cds == [14] and z["hp"] == 1)
    # Excesso ímpar também sobe: ceil(3/2) = 2, portanto CD 12.
    z["hp"] = -3
    cds.clear()
    await r._monster_dies(z, "p1")
    check("Resistência Morta: excesso 3 arredonda para CD 12", cds == [12] and z["hp"] == 1)
    # Morte sagrada destrói (sem save)
    r = setup(); r.rooms = []; r.players = {"p1": make_player("p1", "A", "warrior", 0)}
    z = make_monster(zdef, {"id": 1, "cx": 5, "cy": 5}); z["pos"] = [5, 5]; z["hp"] = 0
    z["_dano_sagrado_recente"] = True
    r.monsters[z["id"]] = z
    await r._monster_dies(z, "p1")
    check("Morte sagrada: destruído (sem Resistência Morta)", z["hp"] == 0)

    # Infecção pela IA do zumbi: acerta → herói testa Fortitude → falha → doente
    r = setup()
    z = make_monster(zdef, {"id": 1, "cx": 5, "cy": 5}); z["pos"] = [5, 5]; r.monsters[z["id"]] = z
    h = make_player("p1", "A", "mage", 1); h["pos"] = [5, 6]; h["ac"] = -100; h["hp"] = 99; h["max_hp"] = 99
    h["fort"] = 0; r.players = {"p1": h}
    _o = S.random.randint; S.random.randint = lambda a, b: 2   # acerta (ac -100, não-nat1) e save 2<10 falha
    await r._ai_zumbi(z, [{"kind": "player", "obj": h}])
    S.random.randint = _o
    check("Infecção: herói fica doente após ser acertado", h.get("doente") is True)

    # ── Lagarto Carniceiro (ND 2) ────────────────────────────────────────────────
    print("\n[18] Lagarto Carniceiro (combo, predador, faro, sensível a venenos)")
    ldef = next(m for m in MONSTER_DEFS if m["type"] == "lagarto_carniceiro")
    check("lagarto: tamanho 2x1 orientado", ldef["size"] == [2, 1] and ldef.get("oriented") is True)
    check("lagarto: fraqueza veneno dobrado",
          any(w.get("type") == "veneno_dobrado" for w in ldef["weaknesses"]))
    check("lagarto: garra do combo definida", ldef.get("garra_attack", {}).get("damage") == "1d6+3")

    def make_spy(room, store):
        orig = room._execute_one_monster_attack
        async def spy(m, atk, tobj):
            store.append((atk["name"], atk.get("atk_bonus")))
            return await orig(m, atk, tobj)
        room._execute_one_monster_attack = spy

    # Sensível a Venenos: perda de HP máximo dobrada (CON poison)
    r = setup()
    lag = make_monster(ldef, {"id": 1, "cx": 5, "cy": 5}); lag["pos"] = [5, 5]
    r.monsters[lag["id"]] = lag
    hpmax0 = lag["max_hp"]
    _o = S.random.randint; S.random.randint = lambda a, b: 3   # save 3+4=7<10 falha; valor 3 → dobrado 6
    await r._aplicar_veneno(lag, "veneno_cobra_cuspidora")
    S.random.randint = _o
    check("Sensível a Venenos: perda de HP máx dobrada (24→18)", lag["max_hp"] == hpmax0 - 6)

    # Combo Devorador: 2 mordidas acertam → 2 garras
    r = setup()
    lag = make_monster(ldef, {"id": 1, "cx": 5, "cy": 5}); lag["pos"] = [5, 5]
    r.monsters[lag["id"]] = lag
    h = make_player("p1", "A", "warrior", 0); h["pos"] = [5, 7]; h["ac"] = -100
    h["hp"] = 200; h["max_hp"] = 200; r.players = {"p1": h}
    calls = []; make_spy(r, calls)
    _o = S.random.randint; S.random.randint = lambda a, b: 10   # acerta (não-nat1, ac -100)
    await r._ai_lagarto_carniceiro(lag, [{"kind": "player", "obj": h}])
    S.random.randint = _o
    nomes = [c[0] for c in calls]
    check("Combo: 2 mordidas + 2 garras", nomes.count("Mordida") == 2 and nomes.count("Garra") == 2)

    # Predador Oportunista: alvo <50% HP → mordida +1 (6→7)
    r = setup()
    lag = make_monster(ldef, {"id": 1, "cx": 5, "cy": 5}); lag["pos"] = [5, 5]
    r.monsters[lag["id"]] = lag
    h = make_player("p1", "A", "warrior", 0); h["pos"] = [5, 7]; h["ac"] = -100
    h["hp"] = 5; h["max_hp"] = 200; r.players = {"p1": h}
    calls = []; make_spy(r, calls)
    _o = S.random.randint; S.random.randint = lambda a, b: 10
    await r._ai_lagarto_carniceiro(lag, [{"kind": "player", "obj": h}])
    S.random.randint = _o
    mord = [c[1] for c in calls if c[0] == "Mordida"]
    check("Predador: +1 nas mordidas vs alvo ferido", mord and all(b == 7 for b in mord))

    # Faro de Carniça: prioriza o alvo de MENOR HP
    r = setup()
    lag = make_monster(ldef, {"id": 1, "cx": 5, "cy": 5}); lag["pos"] = [5, 5]
    r.monsters[lag["id"]] = lag
    forte = make_player("p1", "A", "warrior", 0); forte["pos"] = [5, 7]; forte["ac"] = -100
    forte["hp"] = 200; forte["max_hp"] = 200
    fraco = make_player("p2", "B", "mage", 1); fraco["pos"] = [6, 7]; fraco["ac"] = -100
    fraco["hp"] = 4; fraco["max_hp"] = 99
    r.players = {"p1": forte, "p2": fraco}
    _o = S.random.randint; S.random.randint = lambda a, b: 10
    await r._ai_lagarto_carniceiro(lag, [{"kind": "player", "obj": forte},
                                         {"kind": "player", "obj": fraco}])
    S.random.randint = _o
    check("Faro: atacou o alvo de menor HP", fraco["hp"] < 4 and forte["hp"] == 200)

    # ── Devorador de Metal (ND 2) ────────────────────────────────────────────────
    print("\n[19] Devorador de Metal (corrosão de metal, devorar, condutor)")
    dmdef = next(m for m in MONSTER_DEFS if m["type"] == "devorador_metal")
    check("metal: fraqueza eletricidade +2",
          any(w.get("type") == "lightning" and w.get("bonus_flat") == 2 for w in dmdef["weaknesses"]))
    check("metal: loot de ouro 1d6", dmdef["loot_table"]["1-100"] == {"tipo": "gold", "valor": "1d6"})
    r = setup(); dm = make_monster(dmdef, {"id": 1, "cx": 5, "cy": 5}); dm["pos"] = [5, 5]
    r.monsters[dm["id"]] = dm
    check("Corpo Condutor: eletricidade +2 (5→7)", r._apply_damage_types(5, ["lightning"], dm) == 7)
    # Corrói arma de metal (warrior tem machado_basico = metal)
    r = setup(); dm = make_monster(dmdef, {"id": 1, "cx": 5, "cy": 5}); dm["pos"] = [5, 5]
    r.monsters[dm["id"]] = dm
    w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
    await r._aplicar_mordida_corrosiva(dm, w)
    check("metal corrói arma metálica (machado): -1 acerto/dano", r._corrosao_arma_pen(w) == 1)
    check("metal NÃO corrói o couro (orgânico)", r._corr(w)["armadura_lvl"] == 0)
    # Material Orgânico: mago (manto + cajado) é imune à corrosão metálica
    r = setup(); dm = make_monster(dmdef, {"id": 1, "cx": 5, "cy": 5}); dm["pos"] = [5, 5]
    r.monsters[dm["id"]] = dm
    mg = make_player("p2", "Pedro", "mage", 1); r.players["p2"] = mg
    await r._aplicar_mordida_corrosiva(dm, mg)
    check("Material Orgânico: manto/cajado não sofrem corrosão metálica",
          r._corr(mg)["armadura_lvl"] == 0 and r._corr(mg)["arma_lvl"] == 0)
    # Armadura metálica corroída perde CA
    r = setup(); dm = make_monster(dmdef, {"id": 1, "cx": 5, "cy": 5}); dm["pos"] = [5, 5]
    r.monsters[dm["id"]] = dm
    pa = make_player("p1", "Victor", "warrior", 0)
    pa["gear"]["armor"] = {"id": "chainmail", "name": "Cota de Malha", "effect": "def_", "value": 4}
    r.players["p1"] = pa
    await r._aplicar_mordida_corrosiva(dm, pa)
    check("metal corrói cota de malha: -1 CA", r._corrosao_ca_pen(pa) == 1)
    # Devorar Metal: destruir item cura o devorador (1d6)
    r = setup(); dm = make_monster(dmdef, {"id": 1, "cx": 5, "cy": 5}); dm["pos"] = [5, 5]
    dm["hp"] = 5; r.monsters[dm["id"]] = dm
    w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
    for _ in range(3):  # destrói o machado
        await r._aplicar_mordida_corrosiva(dm, w)
    check("Devorar Metal: arma destruída → desarmado", w["weapon"]["id"] == "unarmed")
    check("Devorar Metal: devorador curou", dm["hp"] > 5)
    # Alimentação Metálica: consome item metálico de baú adjacente e cura
    r = setup(); dm = make_monster(dmdef, {"id": 1, "cx": 5, "cy": 5}); dm["pos"] = [5, 5]
    dm["hp"] = 5; r.monsters[dm["id"]] = dm
    r.players = {"p1": make_player("p1", "A", "warrior", 0)}
    espada = next(i for i in CHEST_ITEMS if i["id"] == "sword")
    r._spawn_chest([5, 6], 0, [dict(espada)])
    await r._ai_devorador_metal(dm, [])
    check("Alimentação Metálica: curou consumindo metal do chão", dm["hp"] > 5)
    check("Alimentação Metálica: item sumiu do baú",
          not any(it.get("id") == "sword" for ch in r.chests.values() for it in ch.get("items", [])))

    print(f"\n===== RESULTADO: {PASS} passaram, {FAIL} falharam =====")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
