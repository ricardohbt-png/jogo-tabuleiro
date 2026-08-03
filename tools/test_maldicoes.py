"""Sistema de maldições. Roda da raiz: python tools/test_maldicoes.py

Cobre a trava de item amaldiçoado (`maldicao_prende`): um item preso não pode
sair do slot por NENHUMA via — desequipar, largar no chão, vender, ou ser
empurrado por outro item equipado no mesmo slot.
"""
import asyncio, os, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def sala():
    """Sala em masmorra, com grid livre — o largar precisa de casa adjacente."""
    r = S.GameRoom("MALD")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop
    r.push_state_or_city = noop; r.broadcast_city_state = noop
    r._checkpoint_savegame = lambda *a, **k: None
    r.phase = "playing"
    r.tiles = [[S.FLOOR] * 12 for _ in range(12)]
    r.grid_w = r.grid_h = 12
    r.rooms = [{"id": "r1", "x": 0, "y": 0, "w": 12, "h": 12, "locked": False, "doors": []}]
    p = S.make_player("p1", "Victor", "warrior", 0)
    p["pos"] = [5, 5]; p["gold"] = 500
    r.players["p1"] = p
    r.erros = []
    async def cap(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error": r.erros.append(msg["msg"])
    r.send_to = cap
    return r, p

def anel(prende=True, mid="maos_tremulas", iid="anel_maldito"):
    return {"id": iid, "name": "Anel Maldito", "emoji": "💍", "item_slot": "ring",
            "kind": "ring", "bonuses": [], "buy_price": 100,
            "maldicao_id": mid, "maldicao_prende": prende}

def equipar(r, p, item, slot="ring1"):
    p["gear"][slot] = item
    r._apply_gear_effect(p, item, True)

def test_desequipar():
    print("\n[1] Desequipar item preso")
    r, p = sala()
    equipar(r, p, anel())
    asyncio.run(r.handle_unequip("p1", "ring1"))
    check("recusado", bool(r.erros) and p["gear"]["ring1"] is not None)

def test_largar():
    print("\n[2] Largar item preso no chão")
    r, p = sala()
    equipar(r, p, anel())
    asyncio.run(r.handle_drop_item("p1", "gear", None, "ring1"))
    check("recusado", p["gear"]["ring1"] is not None)
    check("nada foi para o chão", not r.ground_items)
    check("avisou o jogador", any("maldi" in e.lower() for e in r.erros))

def test_vender():
    print("\n[3] Vender item preso")
    r, p = sala()
    r.phase = "city"
    # acessório
    equipar(r, p, anel())
    ouro = p["gold"]
    asyncio.run(r.handle_shop_sell("p1", "ring1"))
    check("acessório: recusado", p["gear"]["ring1"] is not None and p["gold"] == ouro)
    # arma
    r2, p2 = sala(); r2.phase = "city"
    arma = {"id": "lamina_maldita", "name": "Lâmina Maldita", "item_slot": "weapon",
            "kind": "weapon", "die": "1d8", "stat": "str_", "buy_price": 90,
            "maldicao_id": "maos_tremulas", "maldicao_prende": True}
    equipar(r2, p2, arma, "weapon"); p2["weapon"] = dict(arma)
    asyncio.run(r2.handle_shop_sell("p1", "weapon"))
    check("arma: recusada", (p2["gear"]["weapon"] or {}).get("id") == "lamina_maldita")
    # armadura
    r3, p3 = sala(); r3.phase = "city"
    couro = {"id": "couro_maldito", "name": "Couro Maldito", "item_slot": "armor",
             "kind": "armor", "ac_bonus": 2, "bonuses": [], "buy_price": 80,
             "maldicao_id": "maos_tremulas", "maldicao_prende": True}
    equipar(r3, p3, couro, "armor")
    asyncio.run(r3.handle_shop_sell("p1", "armor"))
    check("armadura: recusada", p3["gear"]["armor"] is not None)

def test_empurrar():
    print("\n[4] Equipar outro item por cima do preso")
    r, p = sala()
    equipar(r, p, anel())
    equipar(r, p, anel(prende=False, mid="corpo_exausto", iid="anel_comum"), "ring2")
    outro = anel(prende=False, mid=None, iid="anel_simples")
    outro["maldicao_id"] = None; outro["name"] = "Anel Simples"
    p["bag"].append(outro)
    asyncio.run(r._executar_equip_from_bag("p1", len(p["bag"]) - 1))
    check("os dois anéis cheios: recusado",
          (p["gear"]["ring1"] or {}).get("id") == "anel_maldito")
    check("o anel novo continua na bolsa",
          any(i.get("id") == "anel_simples" for i in p["bag"]))

def test_nao_bloqueia_demais():
    print("\n[5] A trava não pode bloquear o que é legítimo")
    # slot livre no par: equipar não empurra ninguém
    r, p = sala()
    equipar(r, p, anel())
    novo = anel(prende=False, iid="anel_simples"); novo["maldicao_id"] = None
    p["bag"].append(novo)
    asyncio.run(r._executar_equip_from_bag("p1", len(p["bag"]) - 1))
    check("com ring2 livre, equipar funciona", p["gear"]["ring2"] is not None)

    # item amaldiçoado SEM prender sai normalmente
    r2, p2 = sala()
    equipar(r2, p2, anel(prende=False))
    asyncio.run(r2.handle_unequip("p1", "ring1"))
    check("maldição sem trava: desequipa normal", p2["gear"]["ring1"] is None)

    # curada a maldição, o item destrava
    r3, p3 = sala()
    it = anel()
    equipar(r3, p3, it)
    r3._remover_maldicao(p3, "maos_tremulas")
    check("sem a maldição, o item não prende mais",
          not r3._item_maldicao_vinculante(p3, it))
    asyncio.run(r3.handle_unequip("p1", "ring1"))
    check("depois de curar, desequipa", p3["gear"]["ring1"] is None)

    # item comum nunca é afetado
    r4, p4 = sala()
    comum = {"id": "anel_vita", "name": "Anel", "item_slot": "ring", "kind": "ring",
             "bonuses": [], "buy_price": 50}
    equipar(r4, p4, comum)
    asyncio.run(r4.handle_drop_item("p1", "gear", None, "ring1"))
    check("item comum é largado normalmente", p4["gear"]["ring1"] is None)

def test_corrosao_destroi_mas_maldicao_fica():
    print("\n[6] Corrosão destrói o item, mas a maldição fica com o herói")
    # Regra de design: a maldição é do HERÓI, não do item. Perder a peça por
    # mecânica de jogo não é o mesmo que escolher tirá-la — só Templo ou
    # clérigo removem a maldição.
    r, p = sala()
    couro = {"id": "couro_maldito", "name": "Couro Maldito", "item_slot": "armor",
             "kind": "armor", "ac_bonus": 2, "bonuses": [], "buy_price": 80,
             "corrosion_materials": ["metal"], "corrosao_resistente": 0,
             "corrosao_niveis_penalidade": 1,
             "maldicao_id": "maos_tremulas", "maldicao_prende": True}
    equipar(r, p, couro, "armor")
    check("começa amaldiçoado", r._tem_maldicao(p, "maos_tremulas"))
    monstro = {"id": "m1", "name": "Devorador", "hp": 10, "pos": [5, 6]}
    # Corrói até quebrar (N=0 + M=1 → destrói no 2º golpe).
    for _ in range(4):
        asyncio.run(r._corroer_equipamento(monstro, p, S.CORROSAO_ARMADURA_METAL,
                                           S.CORROSAO_ARMA_METAL))
    check("a peça foi destruída", p["gear"]["armor"] is None)
    check("a MALDIÇÃO permanece no herói", r._tem_maldicao(p, "maos_tremulas"))
    check("sem item, nada mais está travado",
          r._slot_travado_por_maldicao(p, "armor") is None)

    # E ela continua curável pelas duas vias previstas.
    r._remover_maldicao(p, "maos_tremulas")
    check("clérigo/Templo ainda removem", not r._tem_maldicao(p, "maos_tremulas"))

def test_remover_maldicao_certa():
    print("\n[7] Purificação remove exatamente a maldição pedida")
    r, p = sala()
    asyncio.run(r._aplicar_maldicao(p, "maos_tremulas"))
    asyncio.run(r._aplicar_maldicao(p, "corpo_exausto"))
    # id que o alvo NÃO tem: antes caía no índice 0 e curava a errada.
    removida = r._remover_maldicao(p, "licantropia")
    check("id ausente não remove nada", removida is None)
    check("as duas maldições continuam",
          r._tem_maldicao(p, "maos_tremulas") and r._tem_maldicao(p, "corpo_exausto"))
    # id presente: remove exatamente aquela, mesmo não sendo a primeira.
    check("remove a pedida", r._remover_maldicao(p, "corpo_exausto") == "corpo_exausto")
    check("a outra fica", r._tem_maldicao(p, "maos_tremulas"))
    check("a pedida saiu", not r._tem_maldicao(p, "corpo_exausto"))
    # sem id: continua removendo a mais antiga (usado quando o cliente não escolhe).
    check("sem id remove a mais antiga", r._remover_maldicao(p) == "maos_tremulas")
    check("sem nada para remover devolve None", r._remover_maldicao(p) is None)

def test_purificacao_nao_cura_errada():
    print("\n[8] Purificar pedindo maldição ausente não cura outra")
    r, p = sala()
    lewis = S.make_player("p2", "Lewis", "cleric", 1)
    lewis["pos"] = [5, 6]; lewis["fome"] = lewis["sede"] = 50
    # Purificar maldição exige a Purificação III da Guilda.
    lewis["guild_owned"] = {"especializacoes": ["clerigo_purif_2", "clerigo_purif_3"]}
    r.players["p2"] = lewis
    r.round_num = 1
    # _is_turn lê current_pid() → initiative_order[initiative_index]; sem
    # initiative_active o handler sai em silêncio no topo.
    r.initiative_active = True
    r.initiative_order = [{"kind": "player", "id": "p2"}]
    r.initiative_index = 0
    asyncio.run(r._aplicar_maldicao(p, "maos_tremulas"))
    asyncio.run(r.handle_purificacao("p2", {"tipo": "maldicao", "target_id": "p1",
                                            "maldicao_id": "licantropia"}))
    check("a maldição real sobreviveu", r._tem_maldicao(p, "maos_tremulas"))
    check("o clérigo foi avisado", any("amaldiçoad" in e.lower() or "maldi" in e.lower()
                                       for e in r.erros))

def test_item_amaldicoado_avisa():
    print("\n[9] Equipar item amaldiçoado avisa o jogador")
    r, p = sala()
    enviados = []
    async def cap(pid, msg, *a, **k): enviados.append(msg)
    r.send_to = cap
    narrado = []
    async def say(txt, *a, **k): narrado.append(txt)
    r.gm_say = say
    it = anel()
    p["bag"].append(it)
    asyncio.run(r._executar_equip_from_bag("p1", len(p["bag"]) - 1))
    check("a maldição foi aplicada", r._tem_maldicao(p, "maos_tremulas"))
    asyncio.run(r._notificar_maldicoes_pendentes())
    curse = [m for m in enviados if m.get("type") == "curse_result"]
    check("mandou curse_result", bool(curse))
    check("o quadro traz o nome da maldição", bool(curse) and curse[0].get("nome") == "Mãos Trêmulas")
    check("o quadro explica o efeito", bool(curse) and "-2" in (curse[0].get("descricao") or ""))
    check("o quadro diz que veio do item",
          bool(curse) and any("item" in str(x).lower() for x in curse[0].get("efeitos_extra") or []))
    check("narrou no log", any("amaldiçoad" in t.lower() for t in narrado))
    enviados.clear()
    asyncio.run(r._notificar_maldicoes_pendentes())
    check("a fila não repete o aviso",
          not [m for m in enviados if m.get("type") == "curse_result"])

def test_aviso_nao_vaza_no_payload():
    print("\n[10] A fila de avisos não vaza no estado do jogador")
    r, p = sala()
    it = anel()
    p["bag"].append(it)
    asyncio.run(r._executar_equip_from_bag("p1", len(p["bag"]) - 1))
    check("a fila existe antes do broadcast", p.get("_maldicoes_a_avisar"))
    asyncio.run(r._notificar_maldicoes_pendentes())
    check("some depois de avisar", not p.get("_maldicoes_a_avisar"))
    check("não é campo durável", "_maldicoes_a_avisar" not in S._DURABLE_FIELDS)

def test_camada_declarativa():
    print("\n[11] Camada declarativa — os três números não mudam")
    # Caracterização: estes valores valem hoje (checagens hardcoded) e têm de
    # continuar valendo depois da migração para MALDICOES[...]["mods"].
    r, p = sala()
    r.round_num = 1
    mov0 = r._moves_base(p)
    asyncio.run(r._aplicar_maldicao(p, "correntes_invisiveis"))
    check("Correntes Invisíveis: -3 de movimento", r._moves_base(p) == mov0 - 3)

    # Vontade: _testar_save devolve (passou, d20, bonus, total) — compara o
    # `bonus`, que é determinístico, em vez do d20.
    r2, p2 = sala()
    base = r2._testar_save(p2, "vontade", 99)[2]
    asyncio.run(r2._aplicar_maldicao(p2, "espirito_covarde"))
    check("Espírito Covarde: -2 em Vontade",
          r2._testar_save(p2, "vontade", 99)[2] == base - 2)

    r3, p3 = sala()
    check("sem maldição, o modificador é 0", r3._maldicao_mod(p3, "ataque") == 0)
    asyncio.run(r3._aplicar_maldicao(p3, "maos_tremulas"))
    check("Mãos Trêmulas: -2 de ataque", r3._maldicao_mod(p3, "ataque") == -2)
    asyncio.run(r3._aplicar_maldicao(p3, "correntes_invisiveis"))
    check("chaves diferentes não se misturam",
          r3._maldicao_mod(p3, "ataque") == -2 and r3._maldicao_mod(p3, "movimento") == -3)
    check("chave sem ninguém devolve 0", r3._maldicao_mod(p3, "visao") == 0)

def test_visao_e_ca():
    print("\n[12] Olhos da Escuridão e Marca do Caçador")
    r, p = sala()
    v0 = r._get_raio_visao(p)
    asyncio.run(r._aplicar_maldicao(p, "olhos_escuridao"))
    check("visão cai 2", r._get_raio_visao(p) == v0 - 2)
    p["spd"] = 1; p["int_"] = 10; p["dex"] = 10
    check("piso de 1 respeitado", r._get_raio_visao(p) >= 1)

    r2, p2 = sala()
    ca0 = r2._player_effective_ac(p2)
    asyncio.run(r2._aplicar_maldicao(p2, "marca_cacador"))
    check("CA efetiva cai 1", r2._player_effective_ac(p2) == ca0 - 1)

def test_pen_veneno_no_jogador():
    print("\n[13] Penalidades de veneno saem do inerte")
    r, p = sala()
    ca0 = r._player_effective_ac(p)
    p["penalidades"] = {"ca": -2}
    check("penalidade de CA do veneno agora vale",
          r._player_effective_ac(p) == ca0 - 2)

def test_dano_fisico():
    print("\n[14] Lâmina Enferrujada e penalidade de dano do veneno")
    # Dado fixo para o teste não depender de sorte.
    r, p = sala()
    p["weapon"] = {"id": "t", "name": "Espada", "die": "1d1", "stat": "str_"}
    # mod +3 → dano base = 1+3 = 4, longe do piso de 1 (com mod 0 o dano já
    # nasce no piso e a subtração de 2 fica mascarada pelo max(1, ...)).
    p["str_"] = 16
    alvo = {"id": "m1", "name": "Alvo", "hp": 50, "ca": 10, "pos": [5, 6]}
    def dano():
        d, *_ = r._resolver_dano_ataque_basico(p, alvo, False, 10)
        return d
    base = dano()
    asyncio.run(r._aplicar_maldicao(p, "lamina_enferrujada"))
    check("dano da arma cai 2", dano() == max(1, base - 2))

    r2, p2 = sala()
    p2["weapon"] = {"id": "t", "name": "Espada", "die": "1d1", "stat": "str_"}
    p2["str_"] = 16
    b2 = r2._resolver_dano_ataque_basico(p2, alvo, False, 10)[0]
    p2["penalidades"] = {"dano": -2}
    check("penalidade de dano do veneno agora vale",
          r2._resolver_dano_ataque_basico(p2, alvo, False, 10)[0] == max(1, b2 - 2))

    r3, p3 = sala()
    p3["weapon"] = {"id": "t", "name": "Faca", "die": "1d1", "stat": "str_"}
    p3["str_"] = 10
    asyncio.run(r3._aplicar_maldicao(p3, "lamina_enferrujada"))
    check("piso de 1 respeitado",
          r3._resolver_dano_ataque_basico(p3, alvo, False, 10)[0] >= 1)

def test_aura_profana():
    print("\n[15] Aura Profana")
    r, p = sala()
    aliado = S.make_player("p2", "Lewis", "cleric", 1)
    aliado["pos"] = [5, 6]   # adjacente a [5,5]
    r.players["p2"] = aliado
    check("sem maldição, ninguém sofre", r._aura_profana_pen(aliado) == 0)
    asyncio.run(r._aplicar_maldicao(p, "aura_profana"))
    check("aliado adjacente leva -1", r._aura_profana_pen(aliado) == -1)
    check("o próprio portador não sofre", r._aura_profana_pen(p) == 0)
    aliado["pos"] = [5, 9]
    check("aliado longe não sofre", r._aura_profana_pen(aliado) == 0)
    aliado["pos"] = [5, 6]; aliado["alive"] = True
    p["alive"] = False
    check("portador morto não irradia", r._aura_profana_pen(aliado) == 0)

def main():
    test_desequipar(); test_largar(); test_vender()
    test_empurrar(); test_nao_bloqueia_demais()
    test_corrosao_destroi_mas_maldicao_fica()
    test_remover_maldicao_certa(); test_purificacao_nao_cura_errada()
    test_item_amaldicoado_avisa(); test_aviso_nao_vaza_no_payload()
    test_camada_declarativa()
    test_visao_e_ca(); test_pen_veneno_no_jogador()
    test_dano_fisico()
    test_aura_profana()
    print(f"\n===== {PASS} passaram, {FAIL} falharam =====")
    sys.exit(1 if FAIL else 0)

main()
