"""Testes do sistema de Instrumentos do Bardo — Fase 1."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server

def test_stats_por_qualidade():
    for q, alc, dano in [("velho", 3, "1d4"), ("rustico", 4, "1d6"), ("padrao", 5, "2d6")]:
        inst = server.criar_instrumento("harpa", q)
        st = server.GameRoom._instrumento_stats(inst)
        assert st["alcance"] == alc, (q, st)
        assert st["dano"] == dano, (q, st)
        assert st["custo_fome"] == 3 and st["custo_sede"] == 3, st

def test_refinado_afixo_alcance():
    inst = server.criar_instrumento("harpa", "refinado", refinado_bonus="alcance")
    st = server.GameRoom._instrumento_stats(inst)
    assert st["alcance"] == 6, st
    assert st["dano"] == "2d6", st

def test_refinado_afixo_custo_nunca_negativo():
    inst = server.criar_instrumento("sino", "refinado", refinado_bonus="fome")
    st = server.GameRoom._instrumento_stats(inst)
    assert st["custo_fome"] == 1, st
    assert st["custo_sede"] == 2, st
    # cruza o zero: alaude tem custo_fome 0 → clamp em 0
    inst0 = server.criar_instrumento("alaude", "refinado", refinado_bonus="fome")
    assert server.GameRoom._instrumento_stats(inst0)["custo_fome"] == 0

def test_nome_derivado():
    assert server.criar_instrumento("harpa", "velho")["name"] == "Harpa Velha"
    assert server.criar_instrumento("tambor", "padrao")["name"] == "Tambor de Guerra Padrão"

def test_tipo_item_e_maos():
    inst = server.criar_instrumento("harpa", "padrao")
    assert inst["tipo_item"] == "instrumento"
    assert server.INSTRUMENTOS_BASE["harpa"]["maos"] == 2
    assert server.INSTRUMENTOS_BASE["sino"]["maos"] == 1

def _room_bardo():
    room = server.GameRoom.__new__(server.GameRoom)
    room.phase = "playing"
    room.round_num = 1
    room.turn_index = 0
    room.monsters = {}
    room.players = {}
    p = {
        "id": "p1", "name": "Henrique", "class_id": "bard", "alive": True,
        "pos": [5, 5], "dex": 16, "int_": 12, "spd": 6,
        "fome": 100, "sede": 100, "hp": 9, "max_hp": 9,
        "action_done": False, "instrumento_usado": False,
        "bag": [], "bag_size": 6,
        "gear": {k: None for k in server.GEAR_SLOTS},
        "moves_left": 6,
    }
    room.players["p1"] = p
    room.turn_order = ["p1"]
    room._is_turn = lambda pid: pid == "p1"
    room.map_w = server.MAP_W
    room.map_h = server.MAP_H
    room.tiles = [[server.FLOOR] * server.MAP_W for _ in range(server.MAP_H)]
    return room, p

def test_sem_slot_dedicado_instrumento():
    # O instrumento vive na mão do escudo (off_hand), sem slot próprio.
    assert "instrumento" not in server.GEAR_SLOTS

def test_slot_category_instrumento():
    inst = server.criar_instrumento("harpa", "padrao")
    assert server.GameRoom._slot_category_for_item(inst) == "off_hand"


import asyncio
def _run(coro): asyncio.run(coro)

def _mute(room):
    async def noop(*a, **k): return None
    room.gm_say = noop
    room.send_to = noop
    room.broadcast = noop
    room.push_state = noop
    room._broadcast_dado = noop

def test_economia_2maos_bloqueia_apos_acao():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("harpa", "padrao")  # 2 mãos
    m = {"id": "m1", "name": "Goblin", "hp": 20, "pos": [6, 5], "alive": True,
         "ref_": 0, "ca": 10, "saves_base": {}}
    room.monsters["m1"] = m
    p["action_done"] = True
    _run(room.handle_usar_instrumento("p1", {"target_id": "m1"}))
    assert m["hp"] == 20     # bloqueado

def test_economia_1mao_nao_gasta_acao_principal():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("sino", "padrao")   # 1 mão
    _run(room.handle_usar_instrumento("p1", {}))
    assert p["instrumento_usado"] is True
    assert p["action_done"] is False

def test_um_instrumento_por_turno():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("sino", "padrao")
    _run(room.handle_usar_instrumento("p1", {}))
    fome_apos_1 = p["fome"]
    _run(room.handle_usar_instrumento("p1", {}))  # recusa
    assert p["fome"] == fome_apos_1

async def _save_falha(*a, **k): return (False, 1, 0, 1)
async def _save_passa(*a, **k): return (True, 20, 0, 20)
async def _dano10(n, faces, label): return 10

def test_nota_cortante_dano_cheio_na_falha():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("harpa", "padrao")  # 5q, 2d6
    m = {"id": "m1", "name": "Goblin", "hp": 30, "pos": [8, 5], "alive": True}
    room.monsters["m1"] = m
    room._save_mostrado = _save_falha
    room._rolar_dano_mostrado = _dano10
    _run(room.handle_usar_instrumento("p1", {"target_id": "m1"}))
    assert m["hp"] == 20     # 30 - 10 (cheio)

def test_nota_cortante_meia_no_sucesso():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("harpa", "padrao")
    m = {"id": "m1", "name": "Goblin", "hp": 30, "pos": [6, 5], "alive": True}
    room.monsters["m1"] = m
    room._save_mostrado = _save_passa
    room._rolar_dano_mostrado = _dano10
    _run(room.handle_usar_instrumento("p1", {"target_id": "m1"}))
    assert m["hp"] == 25     # 30 - 5 (metade)

def test_nota_cortante_fora_de_alcance_recusa():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("harpa", "velho")   # 3q
    m = {"id": "m1", "name": "Goblin", "hp": 30, "pos": [10, 5], "alive": True}
    room.monsters["m1"] = m
    fome0 = p["fome"]
    _run(room.handle_usar_instrumento("p1", {"target_id": "m1"}))
    assert m["hp"] == 30 and p["fome"] == fome0   # nada, sem custo

def test_ndfaces():
    assert server._ndfaces("2d6") == (2, 6)
    assert server._ndfaces("1") == (1, 1)
    assert server._ndfaces("1d4") == (1, 4)

async def _dano8(n, faces, label): return 8

def test_acorde_aoe_falha_empurra():
    room, p = _room_bardo(); _mute(room)
    p["pos"] = [5, 5]
    p["gear"]["off_hand"] = server.criar_instrumento("tambor", "padrao")  # raio2, 2d4, push2
    m = {"id": "m1", "name": "Goblin", "hp": 30, "pos": [6, 5], "alive": True}
    far = {"id": "m2", "name": "Ogro", "hp": 30, "pos": [12, 5], "alive": True}
    room.monsters = {"m1": m, "m2": far}
    room._save_mostrado = _save_falha
    room._rolar_dano_mostrado = _dano8
    empurrados = []
    room._empurrar = lambda alvo, dx, dy, dist: empurrados.append((alvo["id"], dx, dy, dist)) or False
    _run(room.handle_usar_instrumento("p1", {}))
    assert m["hp"] == 22          # 30 - 8 (cheio)
    assert far["hp"] == 30        # fora do raio
    assert ("m1", 1, 0, 2) in empurrados   # empurrado 2 casas em +x

def test_acorde_sucesso_meia_sem_empurrao():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("tambor", "padrao")
    m = {"id": "m1", "name": "Goblin", "hp": 30, "pos": [6, 5], "alive": True}
    room.monsters = {"m1": m}
    room._save_mostrado = _save_passa
    room._rolar_dano_mostrado = _dano8
    def _no_push(*a): raise AssertionError("não deveria empurrar")
    room._empurrar = _no_push
    _run(room.handle_usar_instrumento("p1", {}))
    assert m["hp"] == 26          # 30 - 4 (metade)

def test_ecos_ativa_aura():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("sino", "padrao")  # 1d4, dur 3
    _run(room.handle_usar_instrumento("p1", {}))
    assert p["ecos_ate"] == room.round_num + 3
    assert p["ecos_dano"] == "1d4"
    assert p["instrumento_usado"] is True
    assert p["action_done"] is False   # 1 mão: pode atacar depois

def test_ecos_retaliacao():
    room, p = _room_bardo(); _mute(room)
    p["ecos_ate"] = room.round_num + 2
    p["ecos_dano"] = "1d4"
    p["gear"]["off_hand"] = server.criar_instrumento("sino", "padrao")  # Sino ainda empunhado
    m = {"id": "m1", "name": "Goblin", "hp": 20, "pos": [5, 5], "alive": True}
    room.monsters["m1"] = m
    async def _dano3(n, faces, label): return 3
    room._rolar_dano_mostrado = _dano3
    _run(room._instr_ecos_retaliar(p, m))
    assert m["hp"] == 17

def test_ecos_expira():
    room, p = _room_bardo(); _mute(room)
    p["ecos_ate"] = room.round_num - 1   # já expirou
    p["gear"]["off_hand"] = server.criar_instrumento("sino", "padrao")
    m = {"id": "m1", "name": "Goblin", "hp": 20, "pos": [5, 5], "alive": True}
    _run(room._instr_ecos_retaliar(p, m))
    assert m["hp"] == 20

def test_ecos_para_se_desequipar_sino():
    # Ativou Ecos e depois trocou o Sino por outra coisa → a aura para (evita
    # tocar-e-trocar-por-escudo mantendo a retaliação).
    room, p = _room_bardo(); _mute(room)
    p["ecos_ate"] = room.round_num + 2
    p["ecos_dano"] = "1d4"
    p["gear"]["off_hand"] = None            # Sino guardado / trocado
    m = {"id": "m1", "name": "Goblin", "hp": 20, "pos": [5, 5], "alive": True}
    async def _dano3(n, faces, label): return 3
    room._rolar_dano_mostrado = _dano3
    _run(room._instr_ecos_retaliar(p, m))
    assert m["hp"] == 20                     # sem retaliação

def test_ecos_nao_retalia_bardo_morto():
    # Um bardo morto pelo próprio golpe que dispararia a retaliação não revida.
    room, p = _room_bardo(); _mute(room)
    p["ecos_ate"] = room.round_num + 2
    p["ecos_dano"] = "1d4"
    p["gear"]["off_hand"] = server.criar_instrumento("sino", "padrao")
    p["alive"] = False
    m = {"id": "m1", "name": "Goblin", "hp": 20, "pos": [5, 5], "alive": True}
    async def _dano3(n, faces, label): return 3
    room._rolar_dano_mostrado = _dano3
    _run(room._instr_ecos_retaliar(p, m))
    assert m["hp"] == 20                     # sem retaliação

def test_sinfonia_boost_por_qualidade():
    room, p = _room_bardo(); _mute(room)
    p["guild_owned"] = {"especializacoes": [], "tecnicas": []}
    assert room._cancao_nivel_atributo(p, "acerto") == 1   # sem alaúde
    p["gear"]["off_hand"] = server.criar_instrumento("alaude", "velho")
    assert room._cancao_nivel_atributo(p, "acerto") == 2   # velho: só acerto
    assert room._cancao_nivel_atributo(p, "dano") == 1
    p["gear"]["off_hand"] = server.criar_instrumento("alaude", "padrao")
    for a in ("acerto", "dano", "ca", "movimento", "resistencia"):
        assert room._cancao_nivel_atributo(p, a) == 2, a

def test_sinfonia_empilha_com_espec():
    room, p = _room_bardo(); _mute(room)
    p["guild_owned"] = {"especializacoes": ["bardo_cancao_acerto"], "tecnicas": []}
    p["gear"]["off_hand"] = server.criar_instrumento("alaude", "padrao")
    assert room._cancao_nivel_atributo(p, "acerto") == 3   # 2 (espec) + 1 (alaúde)

def test_instrumento_roteia_para_bolsa():
    room, p = _room_bardo(); _mute(room)
    inst = server.criar_instrumento("harpa", "rustico")
    res = room._route_acquired_item(p, inst)
    assert res == "bag"
    assert inst in p["bag"]
    assert p["gear"]["off_hand"] is None    # NÃO auto-equipa

def test_instrumento_sku_gera_instancia():
    sku = server.instrumento_sku("harpa", "rustico", preco=120)
    assert sku["tipo_item"] == "instrumento"
    assert sku["buy_price"] == 120
    assert sku["allowed_classes"] == ["bard"]
    assert sku["id"] == "instrumento_harpa_rustico"   # id único p/ a loja

def test_instrumento_bolsa_cheia_nao_auto_equipa():
    room, p = _room_bardo(); _mute(room)
    p["bag"] = [{"id": f"junk{i}"} for i in range(p["bag_size"])]
    inst = server.criar_instrumento("harpa", "rustico")
    res = room._route_acquired_item(p, inst)
    assert res == "full"
    assert p["gear"]["off_hand"] is None    # NÃO faz resgate-equipar

def test_loadout_inicial_henrique():
    p = server.make_player("p1", "Henrique", "bard", 0)
    # arma real (com die), não mais o "instrumento" sem dano
    assert p["gear"]["weapon"].get("id") != "instrumento"
    assert p["weapon"].get("die")                    # arma de dano
    # Alaúde Velho no slot de instrumento
    inst = p["gear"]["off_hand"]
    assert inst and inst["base"] == "alaude" and inst["qualidade"] == "velho"

def test_reduzir_mov_monstro():
    room, p = _room_bardo(); _mute(room)
    m = {"id": "m1", "name": "Goblin", "hp": 20, "pos": [6, 5], "alive": True, "movement": 6}
    room._reduzir_mov_monstro(m, 2, 1)
    assert m["movement"] == 4
    assert m["mov_reduzido_orig"] == 6
    assert m["mov_reduzido_rodadas"] == 1
    room._reduzir_mov_monstro(m, 100, 1)
    assert m["movement"] == 1
    assert m["mov_reduzido_orig"] == 6

def test_tambor_velho_reduz_movimento():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("tambor", "velho")  # raio1, 1d2, push0
    m = {"id": "m1", "name": "Goblin", "hp": 20, "pos": [5, 5], "alive": True, "movement": 6}
    room.monsters["m1"] = m
    async def _falha(*a, **k): return (False, 1, 0, 1)
    async def _d(n, faces, label): return 1
    room._save_mostrado = _falha; room._rolar_dano_mostrado = _d
    _run(room.handle_usar_instrumento("p1", {}))
    assert m["movement"] == 5   # push=0 → -1 movimento

def test_chamado_general_falha_medo_e_pen():
    room, p = _room_bardo(); _mute(room)
    p["pos"] = [5, 5]
    p["gear"]["off_hand"] = server.criar_instrumento("trompa", "padrao")  # cone5 pen_falha2 pen_suc1
    dentro = {"id": "m1", "name": "Goblin", "hp": 20, "pos": [6, 5], "alive": True, "movement": 6}
    fora   = {"id": "m2", "name": "Ogro",   "hp": 20, "pos": [5, 1], "alive": True, "movement": 6}
    room.monsters = {"m1": dentro, "m2": fora}
    async def _falha(*a, **k): return (False, 1, 0, 1)
    room._save_mostrado = _falha
    _run(room.handle_usar_instrumento("p1", {"dir": [1, 0]}))
    assert dentro.get("com_medo") is True and dentro["medo_rodadas"] == 1
    assert dentro["movement"] == 4          # 6 - pen_falha 2
    assert fora.get("com_medo") is None
    assert fora["movement"] == 6

def test_chamado_general_sucesso_so_pen_menor():
    room, p = _room_bardo(); _mute(room)
    p["pos"] = [5, 5]
    p["gear"]["off_hand"] = server.criar_instrumento("trompa", "padrao")
    m = {"id": "m1", "name": "Goblin", "hp": 20, "pos": [6, 5], "alive": True, "movement": 6}
    room.monsters = {"m1": m}
    async def _passa(*a, **k): return (True, 20, 0, 20)
    room._save_mostrado = _passa
    _run(room.handle_usar_instrumento("p1", {"dir": [1, 0]}))
    assert m.get("com_medo") is None
    assert m["movement"] == 5                # 6 - pen_sucesso 1

def test_trompa_refinada_alcance_bump_cone():
    inst = server.criar_instrumento("trompa", "refinado", refinado_bonus="alcance")
    st = server.GameRoom._instrumento_stats(inst)
    assert st["cone"] == 6   # padrao 5 + 1

def test_chamado_general_sem_direcao_recusa():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("trompa", "padrao")
    m = {"id": "m1", "name": "Goblin", "hp": 20, "pos": [6, 5], "alive": True, "movement": 6}
    room.monsters = {"m1": m}
    fome0 = p["fome"]
    _run(room.handle_usar_instrumento("p1", {}))
    assert p["fome"] == fome0 and m["movement"] == 6

def test_dueto_marcial_ativa():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("lira", "padrao")  # dur 3
    _run(room.handle_usar_instrumento("p1", {}))
    assert p["dueto_marcial_ate"] == room.round_num + 3
    assert p["instrumento_usado"] is True
    assert p["action_done"] is False   # 1 mão

def test_dueto_marcial_reage_cap_1():
    room, p = _room_bardo(); _mute(room)   # p = bardo em [5,5]
    p["gear"]["off_hand"] = server.criar_instrumento("lira", "padrao")
    p["dueto_marcial_ate"] = room.round_num + 3
    ally = {"id": "a1", "class_id": "warrior", "alive": True, "pos": [5, 6]}
    room.players["a1"] = ally
    m = {"id": "m1", "name": "Goblin", "hp": 20, "max_hp": 20, "ac": 5, "pos": [6, 5], "alive": True}
    room.monsters["m1"] = m
    reacoes = []
    async def _react(bardo, alvo): reacoes.append((bardo["id"], alvo["id"]))
    room._ataque_basico_reativo = _react
    _run(room._reacoes_instrumento_apos_ataque(ally, m, 5))
    _run(room._reacoes_instrumento_apos_ataque(ally, m, 5))   # 2ª na mesma rodada
    assert reacoes == [("p1", "m1")]   # cap 1/rodada

def test_dueto_marcial_runico_cap_2():
    room, p = _room_bardo(); _mute(room)
    inst = server.criar_instrumento("lira", "padrao"); inst["encantamento"] = "runico"
    p["gear"]["off_hand"] = inst
    p["dueto_marcial_ate"] = room.round_num + 3
    ally = {"id": "a1", "class_id": "warrior", "alive": True, "pos": [5, 6]}
    room.players["a1"] = ally
    m = {"id": "m1", "name": "Goblin", "hp": 20, "max_hp": 20, "ac": 5, "pos": [6, 5], "alive": True}
    room.monsters["m1"] = m
    reacoes = []
    async def _react(bardo, alvo): reacoes.append(1)
    room._ataque_basico_reativo = _react
    for _ in range(3):
        _run(room._reacoes_instrumento_apos_ataque(ally, m, 5))
    assert len(reacoes) == 2   # Rúnico: 2/rodada

def test_dueto_marcial_guardas():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("lira", "padrao")
    p["dueto_marcial_ate"] = room.round_num + 3
    ally = {"id": "a1", "class_id": "warrior", "alive": True, "pos": [5, 6]}
    room.players["a1"] = ally
    longe = {"id": "m2", "name": "Longe", "hp": 9, "max_hp": 9, "ac": 5, "pos": [9, 9], "alive": True}
    room.monsters["m2"] = longe
    reacoes = []
    async def _react(b, a): reacoes.append(1)
    room._ataque_basico_reativo = _react
    _run(room._reacoes_instrumento_apos_ataque(ally, longe, 5))
    assert reacoes == []          # alvo fora de adjacência do bardo
    p["gear"]["off_hand"] = None
    m = {"id": "m1", "name": "Goblin", "hp": 9, "max_hp": 9, "ac": 5, "pos": [6, 5], "alive": True}
    room.monsters["m1"] = m
    _run(room._reacoes_instrumento_apos_ataque(ally, m, 5))
    assert reacoes == []          # sem Lira equipada

def test_dueto_fantasma_ativa_e_ecoa():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("flauta", "padrao")  # fracao 50, dur 3
    _run(room.handle_usar_instrumento("p1", {}))
    assert p["dueto_fantasma_ate"] == room.round_num + 3
    assert p["dueto_fantasma_fracao"] == 50
    assert p["action_done"] is False   # 1 mão
    m = {"id": "m1", "name": "Goblin", "hp": 20, "max_hp": 20, "pos": [6, 5], "alive": True}
    room.monsters["m1"] = m
    _run(room._reacoes_instrumento_apos_ataque(p, m, 10))
    assert m["hp"] == 15   # eco = 10*50//100 = 5

def test_dueto_fantasma_sem_flauta_nao_ecoa():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = None
    p["dueto_fantasma_ate"] = room.round_num + 3
    p["dueto_fantasma_fracao"] = 50
    m = {"id": "m1", "name": "Goblin", "hp": 20, "max_hp": 20, "pos": [6, 5], "alive": True}
    room.monsters["m1"] = m
    _run(room._reacoes_instrumento_apos_ataque(p, m, 10))
    assert m["hp"] == 20

def test_dueto_fantasma_expira():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("flauta", "padrao")
    p["dueto_fantasma_ate"] = room.round_num - 1   # expirado
    p["dueto_fantasma_fracao"] = 50
    m = {"id": "m1", "name": "Goblin", "hp": 20, "max_hp": 20, "pos": [6, 5], "alive": True}
    room.monsters["m1"] = m
    _run(room._reacoes_instrumento_apos_ataque(p, m, 10))
    assert m["hp"] == 20

def test_skus_fase2_existem():
    for base in ("trompa", "lira", "flauta"):
        sku = server.instrumento_sku(base, "padrao", preco=200)
        assert sku["tipo_item"] == "instrumento" and sku["base"] == base
        assert sku["allowed_classes"] == ["bard"]
    ids = {i.get("id") for i in server.SHOP_MERCHANT}
    assert "instrumento_trompa_padrao" in ids
    assert "instrumento_lira_padrao" in ids
    assert "instrumento_flauta_padrao" in ids


# ── Bug 1 (fix): morte processada 1x quando a reação/eco do instrumento é
# quem mata o alvo (server.py handle_attack — a chamada de
# _reacoes_instrumento_apos_ataque foi movida para DEPOIS do check de morte
# do golpe original, ~server.py linha 6739→6772). ──────────────────────────

def test_dueto_fantasma_kill_processa_morte_1x():
    # Eco da Flauta: quando o próprio eco é quem zera o HP, ele mesmo chama
    # _monster_dies (e retorna) — prova que o caminho do eco só mata 1x.
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("flauta", "padrao")
    p["dueto_fantasma_ate"] = room.round_num + 3
    p["dueto_fantasma_fracao"] = 50
    m = {"id": "m1", "name": "Goblin", "hp": 4, "max_hp": 20, "pos": [6, 5], "alive": True}
    room.monsters["m1"] = m
    mortes = []
    async def _dies(mon, killer):
        mortes.append(mon["id"]); mon["hp"] = 0
    room._monster_dies = _dies
    _run(room._reacoes_instrumento_apos_ataque(p, m, 10))   # eco = 10*50//100 = 5 → mata (hp 4)
    assert m["hp"] == 0
    assert mortes == ["m1"]   # morte processada 1x pelo eco

def test_reacao_lira_kill_via_handle_attack_processa_morte_1x():
    """Regressão real do Bug 1: o golpe ORIGINAL de um aliado (guerreiro) não
    mata (5 -> 2 HP); a reação do Dueto Marcial (Lira do bardo) é quem termina
    o alvo. Passa pelo handle_attack de verdade (sem mockar
    _ataque_basico_reativo) — antes do fix, o check de morte do golpe original
    via _monster_dies rodava DEPOIS da reação já ter zerado o HP, chamando
    _monster_dies uma 2ª vez sobre o mesmo alvo (XP/loot em dobro)."""
    room = server.GameRoom("TEST")
    _mute(room)
    room.phase = "playing"
    room.round_num = 1
    warrior = server.make_player("h", "Guerreiro", "warrior", 0)
    warrior["pos"] = [0, 0]; warrior["alive"] = True
    warrior["str_"] = 10; warrior["fome"] = 50; warrior["sede"] = 50
    warrior["atk_bonus"] = 0
    warrior["weapon"] = {"id": "espada", "name": "Espada", "die": "1d6", "stat": "str_"}
    bardo = server.make_player("b", "Henrique", "bard", 1)
    bardo["pos"] = [1, 1]; bardo["alive"] = True
    bardo["str_"] = 10; bardo["fome"] = 50; bardo["sede"] = 50
    bardo["atk_bonus"] = 0
    bardo["weapon"] = {"id": "adaga", "name": "Adaga", "die": "1d4", "stat": "str_"}
    bardo["gear"]["off_hand"] = server.criar_instrumento("lira", "padrao")
    bardo["dueto_marcial_ate"] = room.round_num + 3
    room.players = {"h": warrior, "b": bardo}
    room.turn_order = ["h", "b"]
    room._is_turn = lambda pid: pid == "h"
    monstro = {"id": "m1", "name": "Goblin", "hp": 5, "max_hp": 20, "ac": 5, "pos": [0, 1], "alive": True}
    room.monsters = {"m1": monstro}
    room._rolar_ataque = lambda atk, ac, v=False, d=False: (True, 10, 10 + atk, False, None)
    orig_roll_dice = server.roll_dice
    server.roll_dice = lambda die_str: 3
    mortes = []
    async def _dies(mon, killer):
        mortes.append(mon["id"]); mon["hp"] = 0; mon["alive"] = False
    room._monster_dies = _dies
    try:
        _run(room.handle_attack("h", "m1"))
    finally:
        server.roll_dice = orig_roll_dice
    # Guerreiro: 5 -> 2 (não mata). Reação da Lira: mais 3 -> mata.
    assert monstro["hp"] == 0
    assert mortes == ["m1"], f"morte processada {len(mortes)}x (esperado 1x): {mortes}"


# ── Bug 2 (fix): Trompa (_reduzir_mov_monstro) e Cola (arremessável tático)
# coexistem — Cola foi refatorada para passar pelo mecanismo unificado, em vez
# de um gate `if "mov_reduzido_orig" not in alvo` que fazia a Cola virar no-op
# quando a Trompa já tivesse marcado esse campo primeiro. ────────────────────

def test_trompa_depois_cola_reduz_corretamente():
    room, p = _room_bardo(); _mute(room)
    m = {"id": "m1", "name": "Goblin", "hp": 20, "pos": [6, 5], "alive": True, "movement": 6}
    room._reduzir_mov_monstro(m, 1, 1)          # Trompa -1 → 5
    assert m["movement"] == 5
    orig = m.get("mov_reduzido_orig", m["movement"])
    room._reduzir_mov_monstro(m, orig - orig // 2, 2)   # simula a Cola (via helper unificado)
    assert m["movement"] == 3                   # min(5, 6//2) = 3 (Cola não é anulada)


# ── Fase 3 (Réquiem Final / Violino) — Task 1: ativação, alcance/LOS, toggle ──

def test_requiem_ativa():
    room, p = _room_bardo(); _mute(room)
    p["pos"] = [5, 5]
    p["gear"]["off_hand"] = server.criar_instrumento("violino", "padrao")
    m = {"id": "m1", "name": "Lich", "hp": 30, "max_hp": 30, "pos": [8, 5], "alive": True}
    room.monsters["m1"] = m
    room._tem_linha_de_visao = lambda a, b: True
    _run(room.handle_usar_instrumento("p1", {"target_id": "m1"}))
    assert p["requiem_alvo"] == "m1"
    assert p["requiem_contador"] == 0
    assert m["requiem_por"] == "p1"
    assert p["action_done"] is True

def test_requiem_toggle_off():
    room, p = _room_bardo(); _mute(room)
    p["pos"] = [5, 5]
    p["gear"]["off_hand"] = server.criar_instrumento("violino", "padrao")
    m = {"id": "m1", "name": "Lich", "hp": 30, "max_hp": 30, "pos": [8, 5], "alive": True}
    room.monsters["m1"] = m
    room._tem_linha_de_visao = lambda a, b: True
    _run(room.handle_usar_instrumento("p1", {"target_id": "m1"}))
    fome_apos_ativar = p["fome"]
    p["action_done"] = True
    _run(room.handle_usar_instrumento("p1", {}))
    assert p["requiem_alvo"] is None
    assert m.get("requiem_por") is None
    assert p["fome"] == fome_apos_ativar

def test_requiem_fora_de_alcance_recusa():
    room, p = _room_bardo(); _mute(room)
    p["pos"] = [5, 5]
    p["gear"]["off_hand"] = server.criar_instrumento("violino", "velho")
    m = {"id": "m1", "name": "Lich", "hp": 30, "max_hp": 30, "pos": [12, 5], "alive": True}
    room.monsters["m1"] = m
    room._tem_linha_de_visao = lambda a, b: True
    fome0 = p["fome"]
    _run(room.handle_usar_instrumento("p1", {"target_id": "m1"}))
    assert p.get("requiem_alvo") is None and p["fome"] == fome0

def test_requiem_escalada_e_teto():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("violino", "velho")  # dado d2, teto 3
    m = {"id": "m1", "name": "Lich", "hp": 100, "max_hp": 100, "pos": [8, 5], "alive": True}
    room.monsters["m1"] = m
    p["requiem_alvo"] = "m1"; p["requiem_contador"] = 0; m["requiem_por"] = "p1"
    async def _falha(*a, **k): return (False, 1, 0, 1)
    room._save_mostrado = _falha
    seq = []
    orig_roll = server.roll_dice
    server.roll_dice = lambda s: (seq.append(s) or 1)
    for _ in range(5):
        _run(room._processar_requiem_turno(m))
    server.roll_dice = orig_roll
    assert seq == ["1d2", "2d2", "3d2", "3d2", "3d2"]   # sobe até o teto 3 e trava

def test_requiem_sucesso_sem_dano():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("violino", "padrao")
    m = {"id": "m1", "name": "Lich", "hp": 30, "max_hp": 30, "pos": [8, 5], "alive": True}
    room.monsters["m1"] = m
    p["requiem_alvo"] = "m1"; p["requiem_contador"] = 0; m["requiem_por"] = "p1"
    async def _passa(*a, **k): return (True, 20, 0, 20)
    room._save_mostrado = _passa
    _run(room._processar_requiem_turno(m))
    assert m["hp"] == 30
    assert p["requiem_contador"] == 1

def test_requiem_mata_encerra():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("violino", "padrao")
    m = {"id": "m1", "name": "Lich", "hp": 3, "max_hp": 30, "pos": [8, 5], "alive": True}
    room.monsters["m1"] = m
    p["requiem_alvo"] = "m1"; p["requiem_contador"] = 0; m["requiem_por"] = "p1"
    async def _falha(*a, **k): return (False, 1, 0, 1)
    room._save_mostrado = _falha
    mortes = []
    async def _dies(mon, killer): mortes.append(mon["id"]); mon["hp"] = 0
    room._monster_dies = _dies
    orig_roll = server.roll_dice
    server.roll_dice = lambda s: 10
    _run(room._processar_requiem_turno(m))
    server.roll_dice = orig_roll
    assert mortes == ["m1"]
    assert p["requiem_alvo"] is None

def test_requiem_taunt():
    room, p = _room_bardo(); _mute(room)
    p["pos"] = [5, 5]
    p["requiem_alvo"] = "m1"
    alvo   = {"id": "m1", "name": "Lich", "hp": 30, "pos": [12, 12], "alive": True, "requiem_por": "p1"}
    perto  = {"id": "m2", "name": "Goblin", "hp": 10, "pos": [6, 5], "alive": True}
    longe  = {"id": "m3", "name": "Ogro", "hp": 10, "pos": [15, 15], "alive": True}
    room.monsters = {"m1": alvo, "m2": perto, "m3": longe}
    assert room._requiem_forca_bardo(alvo) is p     # o alvo (qualquer distância)
    assert room._requiem_forca_bardo(perto) is p    # dentro do raio 3
    assert room._requiem_forca_bardo(longe) is None # fora e não-alvo

def test_concentracao_quebra():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("violino", "padrao")
    m = {"id": "m1", "name": "Lich", "hp": 30, "pos": [8, 5], "alive": True, "requiem_por": "p1"}
    room.monsters["m1"] = m
    p["requiem_alvo"] = "m1"; p["requiem_contador"] = 2
    async def _falha(*a, **k): return (False, 1, 0, 1)
    room._save_mostrado = _falha
    _run(room._concentracao_requiem(p, 12))
    assert p["requiem_alvo"] is None
    assert m.get("requiem_por") is None

def test_concentracao_resiste():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("violino", "padrao")
    m = {"id": "m1", "name": "Lich", "hp": 30, "pos": [8, 5], "alive": True, "requiem_por": "p1"}
    room.monsters["m1"] = m
    p["requiem_alvo"] = "m1"
    async def _passa(*a, **k): return (True, 20, 0, 20)
    room._save_mostrado = _passa
    _run(room._concentracao_requiem(p, 12))
    assert p["requiem_alvo"] == "m1"

def test_concentracao_cd_8_mais_dano():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("violino", "padrao")
    m = {"id": "m1", "name": "Lich", "hp": 30, "pos": [8, 5], "alive": True, "requiem_por": "p1"}
    room.monsters["m1"] = m
    p["requiem_alvo"] = "m1"
    cds = []
    async def _cap(alvo, tipo, dif, **k): cds.append(dif); return (True, 20, 0, 20)
    room._save_mostrado = _cap
    _run(room._concentracao_requiem(p, 7))
    assert cds == [15]                     # 8 + 7

def test_concentracao_sem_requiem_noop():
    room, p = _room_bardo(); _mute(room)
    called = []
    async def _s(*a, **k): called.append(1); return (True, 20, 0, 20)
    room._save_mostrado = _s
    _run(room._concentracao_requiem(p, 99))   # sem requiem_alvo
    assert called == []                        # não testa nada

def test_requiem_manutencao_debita():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("violino", "padrao")
    p["requiem_alvo"] = "m1"; p["fome"] = 50; p["sede"] = 50
    _run(room._cobrar_manutencao_requiem(p))
    assert p["fome"] == 48 and p["sede"] == 48
    assert p["requiem_alvo"] == "m1"

def test_requiem_manutencao_sem_recursos_encerra():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("violino", "padrao")
    m = {"id": "m1", "name": "Lich", "hp": 30, "pos": [8, 5], "alive": True, "requiem_por": "p1"}
    room.monsters["m1"] = m
    p["requiem_alvo"] = "m1"; p["fome"] = 1; p["sede"] = 50
    _run(room._cobrar_manutencao_requiem(p))
    assert p["requiem_alvo"] is None
    assert m.get("requiem_por") is None

def test_requiem_manutencao_sem_violino_encerra():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = None            # guardou o violino
    p["requiem_alvo"] = "m1"; p["fome"] = 50; p["sede"] = 50
    _run(room._cobrar_manutencao_requiem(p))
    assert p["requiem_alvo"] is None

def test_sku_violino_existe():
    sku = server.instrumento_sku("violino", "padrao", preco=320)
    assert sku["tipo_item"] == "instrumento" and sku["base"] == "violino"
    ids = {i.get("id") for i in server.SHOP_MERCHANT}
    assert "instrumento_violino_padrao" in ids

# ── Fase 3 — bugfixes de revisão final ──────────────────────────────────────

def test_requiem_alvo_sobrevive_nao_encerra():
    """Bug 1: Resistência Morta (Zumbi) sobrevive à morte "seria" — o Réquiem
    NÃO pode ser encerrado nesse caso (_monster_dies só encerra após a morte
    ser final; _processar_requiem_turno re-checa hp após _monster_dies)."""
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("violino", "padrao")
    m = {"id": "m1", "name": "Zumbi", "hp": 3, "max_hp": 30, "pos": [8, 5], "alive": True, "requiem_por": "p1"}
    room.monsters["m1"] = m
    p["requiem_alvo"] = "m1"; p["requiem_contador"] = 0
    async def _falha(*a, **k): return (False, 1, 0, 1)
    room._save_mostrado = _falha
    async def _dies(mon, killer): mon["hp"] = 1   # Resistência Morta: sobrevive
    room._monster_dies = _dies
    orig = server.roll_dice; server.roll_dice = lambda s: 10
    _run(room._processar_requiem_turno(m))
    server.roll_dice = orig
    assert p["requiem_alvo"] == "m1"   # sobreviveu → Réquiem continua
    assert m.get("requiem_por") == "p1"

def test_requiem_recast_troca_alvo():
    """Bug 3: reativar o instrumento COM target_id enquanto o Réquiem já está
    ativo deve RECASTAR num novo alvo (liberando o antigo), não desligar."""
    room, p = _room_bardo(); _mute(room)
    p["pos"] = [5, 5]
    p["gear"]["off_hand"] = server.criar_instrumento("violino", "padrao")
    m1 = {"id": "m1", "name": "A", "hp": 30, "max_hp": 30, "pos": [7, 5], "alive": True}
    m2 = {"id": "m2", "name": "B", "hp": 30, "max_hp": 30, "pos": [8, 5], "alive": True}
    room.monsters = {"m1": m1, "m2": m2}
    room._tem_linha_de_visao = lambda a, b: True
    _run(room.handle_usar_instrumento("p1", {"target_id": "m1"}))
    assert p["requiem_alvo"] == "m1" and m1["requiem_por"] == "p1"
    p["instrumento_usado"] = False; p["action_done"] = False   # novo turno simulado
    _run(room.handle_usar_instrumento("p1", {"target_id": "m2"}))   # recast
    assert p["requiem_alvo"] == "m2" and m2["requiem_por"] == "p1"
    assert m1.get("requiem_por") is None   # alvo antigo liberado

def test_concentracao_legacy_loop():
    """Bug 2: monstro SEM ai_type (ex.: goblin — usa o loop legado inline de
    gm_phase, não o caminho modular de _run_monster_ai) acertando o bardo com
    Réquiem ativo deve testar concentração via _concentracao_requiem. Teste
    ponta-a-ponta: chama room.gm_phase() de verdade (não uma reprodução
    isolada), com d20_attack/roll_dice forçados para garantir acerto
    determinístico, e monkeypatcha _concentracao_requiem para gravar a
    chamada — confirma tanto que ela É chamada quanto o dano exato recebido."""
    room, p = _room_bardo(); _mute(room)
    p["pos"] = [5, 5]; p["ac"] = 10
    p["requiem_alvo"] = "m2"   # Réquiem ativo (em qualquer alvo — não afeta o teste)
    m = {"id": "m1", "name": "Goblin", "hp": 10, "max_hp": 10, "pos": [6, 5],
         "atk_bonus": 5, "damage": "1d6", "ac": 12, "movement": 5}   # SEM "ai_type"
    room.monsters = {"m1": m}
    room.rooms = []
    room.zonas_especiais = []
    room.smoke = {}
    room.immune = {}
    room.temp_def = {}
    room.taunted = None
    room.blessed = {}
    room.prisoner = None

    chamadas = []
    async def _fake_concentracao(bardo, dano):
        chamadas.append((bardo["id"], dano))
    room._concentracao_requiem = _fake_concentracao

    orig_d20, orig_roll = server.d20_attack, server.roll_dice
    server.d20_attack = lambda atk, ac: (True, 15, atk + 15, False)   # sempre acerta, sem crítico
    server.roll_dice  = lambda s: 4
    try:
        _run(room.gm_phase())
    finally:
        server.d20_attack = orig_d20
        server.roll_dice  = orig_roll

    assert p["hp"] == 5                 # 9 - 4 de dano
    assert chamadas == [("p1", 4)]      # _concentracao_requiem foi chamado pelo loop LEGADO

def test_afixo_fome_sede():
    st = {"custo_fome": 3, "custo_sede": 3}
    server.GameRoom._aplicar_afixo(st, "fome_sede")
    assert st["custo_fome"] == 2 and st["custo_sede"] == 2

def test_ana_fome_sede_no_instrumento():
    inst = server.criar_instrumento("harpa", "padrao", origem="ana", origem_bonus="fome_sede")
    st = server.GameRoom._instrumento_stats(inst)
    assert st["custo_fome"] == 2 and st["custo_sede"] == 2

def test_afixos_validos_origem():
    assert server._afixos_validos_origem("alaude", "elfica") == []
    assert "concentracao" in server._afixos_validos_origem("violino", "ana")
    va = server._afixos_validos_origem("harpa", "elfica")
    assert "cd" in va and "alcance" in va and "duracao" not in va
    vs = server._afixos_validos_origem("sino", "elfica")
    assert "duracao" in vs and "cd" not in vs and "alcance" not in vs

def test_nome_com_origem():
    assert server.criar_instrumento("harpa", "refinado", origem="elfica",
                                    origem_bonus="cd")["name"] == "Harpa Refinada Élfica"
    assert server.criar_instrumento("tambor", "padrao", origem="ana",
                                    origem_bonus="fome_sede")["name"] == "Tambor de Guerra Padrão Anão"
    assert server.criar_instrumento("harpa", "velho")["name"] == "Harpa Velha"

import random as _rnd

def test_roller_gera_instrumentos_validos():
    _rnd.seed(1234)
    for _ in range(300):
        inst = server.gerar_instrumento_aleatorio()
        assert inst["tipo_item"] == "instrumento"
        assert inst["base"] in server.INSTRUMENTOS_BASE
        if inst.get("origem_bonus"):
            assert inst["origem_bonus"] in server._afixos_validos_origem(inst["base"], inst["origem"])
        if inst["base"] == "alaude":
            assert inst["origem"] != "elfica"

def test_roller_respeita_bases():
    _rnd.seed(1)
    for _ in range(50):
        inst = server.gerar_instrumento_aleatorio(bases=["harpa"])
        assert inst["base"] == "harpa"

def test_resolver_loot_instrumento():
    inst = server._resolver_loot_instrumento({"tipo": "instrumento_aleatorio"})
    assert inst is not None and inst["tipo_item"] == "instrumento"
    assert server._resolver_loot_instrumento({"tipo": "item", "id": "x"}) is None
    assert server._resolver_loot_instrumento({"id": "y"}) is None

def test_hidratar_itens_bau_token():
    out = server.hidratar_itens_bau([{"tipo": "instrumento_aleatorio"}])
    assert len(out) == 1 and out[0]["tipo_item"] == "instrumento"

def test_afixo_cd_aumenta_instrumento_cd():
    room, p = _room_bardo(); _mute(room)   # dex 16 → mod +3 → CD base 8+3=11
    base_cd = room._instrumento_cd(p, server.criar_instrumento("harpa", "padrao"))
    elf_cd = room._instrumento_cd(p, server.criar_instrumento("harpa", "padrao",
                                                              origem="elfica", origem_bonus="cd"))
    assert elf_cd == base_cd + 1

def test_alaude_runico_resist():
    room, p = _room_bardo()
    p["gear"]["off_hand"] = server.criar_instrumento("alaude", "padrao", encantamento="runico")
    p["cancao_ativa"] = True
    ally = {"id": "a1", "class_id": "warrior", "alive": True, "buffs_cancao": {"bonus_acerto": 1}}
    room.players["a1"] = ally
    assert room._alaude_runico_resist(ally, "fortitude") == 1
    assert room._alaude_runico_resist(ally, "vontade") == 1
    assert room._alaude_runico_resist(ally, "reflexos") == 0
    sem = {"id": "a2", "class_id": "rogue", "alive": True}
    room.players["a2"] = sem
    assert room._alaude_runico_resist(sem, "fortitude") == 0        # sem buffs_cancao
    p["gear"]["off_hand"] = server.criar_instrumento("alaude", "padrao")   # não Rúnico
    assert room._alaude_runico_resist(ally, "fortitude") == 0

def test_alaude_runico_no_testar_save():
    room, p = _room_bardo()
    p["gear"]["off_hand"] = server.criar_instrumento("alaude", "padrao", encantamento="runico")
    p["cancao_ativa"] = True
    ally = {"id": "a1", "class_id": "warrior", "alive": True, "buffs_cancao": {},
            "saves_base": {}, "fort": 0, "will": 0}
    room.players["a1"] = ally
    import random as _r
    _r.seed(1)
    _, _, bonus_com, _ = room._testar_save(ally, "fortitude", 99)
    p["gear"]["off_hand"] = None
    _r.seed(1)
    _, _, bonus_sem, _ = room._testar_save(ally, "fortitude", 99)
    assert bonus_com - bonus_sem == 1

def test_tambor_runico_atordoa_e_penaliza():
    room, p = _room_bardo(); _mute(room)
    p["pos"] = [5, 5]
    p["gear"]["off_hand"] = server.criar_instrumento("tambor", "padrao", encantamento="runico")
    falho = {"id": "m1", "name": "A", "hp": 30, "pos": [6, 5], "alive": True}
    passou = {"id": "m2", "name": "B", "hp": 30, "pos": [5, 6], "alive": True}
    room.monsters = {"m1": falho, "m2": passou}
    async def _save(alvo, tipo, dif, **k): return (alvo["id"] == "m2", 1, 0, 1)  # m2 passa, m1 falha
    room._save_mostrado = _save
    room._rolar_dano_mostrado = _dano8
    room._empurrar = lambda *a: False
    _run(room.handle_usar_instrumento("p1", {}))
    assert falho.get("perde_turno") is True
    assert room._acorde_atk_pen(passou) == -1
    assert room._acorde_atk_pen(falho) == 0

def test_acorde_atk_pen_expira():
    room, p = _room_bardo()
    m = {"acorde_atk_pen_ate": room.round_num + 1}
    assert room._acorde_atk_pen(m) == -1
    room.round_num += 2
    assert room._acorde_atk_pen(m) == 0

def test_tambor_normal_nao_atordoa():
    room, p = _room_bardo(); _mute(room)
    p["pos"] = [5, 5]
    p["gear"]["off_hand"] = server.criar_instrumento("tambor", "padrao")   # não Rúnico
    m = {"id": "m1", "name": "A", "hp": 30, "pos": [6, 5], "alive": True}
    room.monsters = {"m1": m}
    room._save_mostrado = _save_falha
    room._rolar_dano_mostrado = _dano8
    room._empurrar = lambda *a: False
    _run(room.handle_usar_instrumento("p1", {}))
    assert m.get("perde_turno") is None

def test_harpa_runica_linha():
    room, p = _room_bardo(); _mute(room)
    p["pos"] = [5, 5]
    p["gear"]["off_hand"] = server.criar_instrumento("harpa", "padrao", encantamento="runico")  # alcance 5
    a = {"id": "m1", "name": "A", "hp": 30, "pos": [6, 5], "alive": True}
    b = {"id": "m2", "name": "B", "hp": 30, "pos": [8, 5], "alive": True}
    fora = {"id": "m3", "name": "C", "hp": 30, "pos": [6, 7], "alive": True}
    room.monsters = {"m1": a, "m2": b, "m3": fora}
    room._save_mostrado = _save_falha
    room._rolar_dano_mostrado = _dano10
    _run(room.handle_usar_instrumento("p1", {"dir": [1, 0]}))
    assert a["hp"] == 20 and b["hp"] == 20   # ambos na linha +x (dano cheio 10)
    assert fora["hp"] == 30                  # fora da linha

def test_harpa_runica_sem_direcao_recusa():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("harpa", "padrao", encantamento="runico")
    m = {"id": "m1", "name": "A", "hp": 30, "pos": [6, 5], "alive": True}
    room.monsters = {"m1": m}
    fome0 = p["fome"]
    _run(room.handle_usar_instrumento("p1", {}))   # sem dir
    assert m["hp"] == 30 and p["fome"] == fome0

def test_harpa_normal_ainda_alvo_unico():
    room, p = _room_bardo(); _mute(room)
    p["pos"] = [5, 5]
    p["gear"]["off_hand"] = server.criar_instrumento("harpa", "padrao")   # não Rúnica
    a = {"id": "m1", "name": "A", "hp": 30, "pos": [6, 5], "alive": True}
    b = {"id": "m2", "name": "B", "hp": 30, "pos": [8, 5], "alive": True}
    room.monsters = {"m1": a, "m2": b}
    room._save_mostrado = _save_falha
    room._rolar_dano_mostrado = _dano10
    _run(room.handle_usar_instrumento("p1", {"target_id": "m1"}))
    assert a["hp"] == 20 and b["hp"] == 30   # só o alvo

def test_skus_runico_lendario():
    ids = {i.get("id") for i in server.SHOP_MERCHANT}
    assert "instrumento_sino_padrao_runico" in ids
    assert "instrumento_violino_padrao_runico" in ids
    lend = next(i for i in server.SHOP_MERCHANT
                if i.get("id") == "instrumento_harpa_refinado_elfica_runico")
    assert "Lendária" in lend["name"]

def test_roller_gera_runico():
    _rnd.seed(7)
    encs = set()
    for _ in range(2000):
        encs.add(server.gerar_instrumento_aleatorio().get("encantamento"))
    assert "runico" in encs and "nenhum" in encs

def test_roller_runico_valido():
    _rnd.seed(11)
    for _ in range(2000):
        inst = server.gerar_instrumento_aleatorio()
        if inst.get("encantamento") == "runico":
            assert inst["tipo_item"] == "instrumento"
            server.GameRoom._instrumento_stats(inst)   # não lança

def test_sku_encantamento():
    sku = server.instrumento_sku("sino", "padrao", preco=300, encantamento="runico")
    assert sku["encantamento"] == "runico"
    assert sku["id"] == "instrumento_sino_padrao_runico"
    assert "Rúnico" in sku["name"]

def test_nome_runico():
    assert server.criar_instrumento("sino", "padrao", encantamento="runico")["name"] == "Sino Padrão Rúnico"
    assert server.criar_instrumento("harpa", "velho", encantamento="runico")["name"] == "Harpa Velha Rúnica"

def test_nome_lendario():
    inst = server.criar_instrumento("harpa", "refinado", origem="elfica",
                                    origem_bonus="cd", encantamento="runico")
    assert inst["name"] == "Harpa Lendária Élfica"
    inst2 = server.criar_instrumento("tambor", "refinado", origem="ana",
                                     origem_bonus="fome_sede", encantamento="runico")
    assert inst2["name"] == "Tambor de Guerra Lendário Anão"

def test_nome_sem_runico_inalterado():
    assert server.criar_instrumento("harpa", "velho")["name"] == "Harpa Velha"
    assert server.criar_instrumento("harpa", "refinado", origem="elfica",
                                    origem_bonus="cd")["name"] == "Harpa Refinada Élfica"

def test_violino_runico_menos_1_vontade():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("violino", "padrao", encantamento="runico")
    m = {"id": "m1", "name": "Lich", "hp": 100, "max_hp": 100, "pos": [8, 5], "alive": True, "requiem_por": "p1"}
    room.monsters["m1"] = m
    p["requiem_alvo"] = "m1"; p["requiem_contador"] = 0
    caps = []
    async def _cap(alvo, tipo, dif, extra_mod=0, **k): caps.append(extra_mod); return (True, 20, 0, 20)
    room._save_mostrado = _cap
    _run(room._processar_requiem_turno(m))
    assert caps == [-1]

def test_violino_normal_sem_penalidade():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("violino", "padrao")
    m = {"id": "m1", "name": "Lich", "hp": 100, "max_hp": 100, "pos": [8, 5], "alive": True, "requiem_por": "p1"}
    room.monsters["m1"] = m
    p["requiem_alvo"] = "m1"; p["requiem_contador"] = 0
    caps = []
    async def _cap(alvo, tipo, dif, extra_mod=0, **k): caps.append(extra_mod); return (True, 20, 0, 20)
    room._save_mostrado = _cap
    _run(room._processar_requiem_turno(m))
    assert caps == [0]

def test_lira_runica_cap_2():
    room, p = _room_bardo()
    assert room._dueto_marcial_cap(server.criar_instrumento("lira", "padrao", encantamento="runico")) == 2
    assert room._dueto_marcial_cap(server.criar_instrumento("lira", "padrao")) == 1
    # guarda: um Rúnico de OUTRA base não herda a cota da Lira
    assert room._dueto_marcial_cap(server.criar_instrumento("sino", "padrao", encantamento="runico")) == 1

def test_runico_stat_layer():
    sino = server.criar_instrumento("sino", "padrao", encantamento="runico")
    assert server.GameRoom._instrumento_stats(sino)["dano"] == "1d6"
    flauta = server.criar_instrumento("flauta", "padrao", encantamento="runico")
    assert server.GameRoom._instrumento_stats(flauta)["duracao"] == 5   # 3 + 2
    trompa = server.criar_instrumento("trompa", "padrao", encantamento="runico")
    assert server.GameRoom._instrumento_stats(trompa)["medo"] == 2      # 1 + 1
    assert server.GameRoom._instrumento_stats(server.criar_instrumento("sino", "padrao"))["dano"] == "1d4"

def test_sku_origem():
    sku = server.instrumento_sku("harpa", "padrao", preco=320, origem="elfica", origem_bonus="cd")
    assert sku["origem"] == "elfica" and sku["origem_bonus"] == "cd"
    assert sku["id"] == "instrumento_harpa_padrao_elfica"
    assert "Élfica" in sku["name"]
    ids = {i.get("id") for i in server.SHOP_MERCHANT}
    assert "instrumento_harpa_padrao_elfica" in ids
    assert "instrumento_violino_padrao_ana" in ids

# ─── Fase 5 — Gaita (Improviso) ─────────────────────────────────────────────

def test_gaita_base_existe():
    b = server.INSTRUMENTOS_BASE["gaita"]
    assert b["maos"] == 1 and b["modo"] == "ativada"
    assert b["habilidade_nome"] == "Improviso"
    assert b["efeito"]["tipo"] == "improviso"
    assert b["custo_fome"] == 3 and b["custo_sede"] == 3
    assert b["runico"]["grande_encore"] is True

def test_gaita_nome_e_genero():
    assert server.criar_instrumento("gaita", "velho")["name"] == "Gaita Velha"
    inst = server.criar_instrumento("gaita", "padrao", encantamento="runico")
    assert "Rúnica" in inst["name"], inst["name"]

def test_gaita_stats_custo():
    st = server.GameRoom._instrumento_stats(server.criar_instrumento("gaita", "padrao"))
    assert st["custo_fome"] == 3 and st["custo_sede"] == 3

def test_cascata_sem_encore():
    room, p = _room_bardo()
    room._rolar_2d6 = lambda: 7
    passos, meta = room._improviso_rolar_cascata(runico=False)
    assert passos == [7]
    assert meta == {"encore_menor": False, "grande_encore": False}

def test_cascata_encore_simples():
    room, p = _room_bardo()
    seq = iter([12, 7, 3])  # 12 -> rola 7 e 3
    room._rolar_2d6 = lambda: next(seq)
    passos, meta = room._improviso_rolar_cascata(runico=False)
    assert passos == [7, 3]
    assert meta["encore_menor"] is False and meta["grande_encore"] is False

def test_cascata_encore_menor():
    room, p = _room_bardo()
    seq = iter([12, 12, 5])  # 12 -> rola 12 (2o doze) e 5; nao-runica NAO recursa
    room._rolar_2d6 = lambda: next(seq)
    passos, meta = room._improviso_rolar_cascata(runico=False)
    assert passos == [5]
    assert meta["encore_menor"] is True and meta["grande_encore"] is False

def test_cascata_grande_encore_runica():
    room, p = _room_bardo()
    seq = iter([12, 12, 3, 12, 4, 2, 3])
    room._rolar_2d6 = lambda: next(seq)
    passos, meta = room._improviso_rolar_cascata(runico=True)
    assert meta["encore_menor"] is True and meta["grande_encore"] is True
    assert 12 not in passos

def test_cascata_teto_anti_loop():
    room, p = _room_bardo()
    room._rolar_2d6 = lambda: 12  # sempre 12 (runica): precisa terminar
    passos, meta = room._improviso_rolar_cascata(runico=True)
    assert meta["grande_encore"] is True

def test_pagar_fome_sede_sem_encore():
    room, p = _room_bardo()
    p["fome"] = 10; p["sede"] = 10
    room._pagar_fome_sede(p, 3, 2)
    assert p["fome"] == 7 and p["sede"] == 8

def test_pagar_fome_sede_encore_menor():
    room, p = _room_bardo()
    p["fome"] = 10; p["sede"] = 10
    p["encore_menor_ate"] = room.round_num
    room._pagar_fome_sede(p, 3, 2)
    assert p["fome"] == 8 and p["sede"] == 9

def test_pagar_fome_sede_grande_encore():
    room, p = _room_bardo()
    p["fome"] = 10; p["sede"] = 10
    p["grande_encore_ate"] = room.round_num
    room._pagar_fome_sede(p, 5, 5)
    assert p["fome"] == 10 and p["sede"] == 10

def test_pagar_fome_sede_magia_gratis():
    room, p = _room_bardo()
    p["class_id"] = "cleric"  # ensure mage/cleric for free-spell branch
    p["fome"] = 10; p["sede"] = 10
    p["encore_magia_gratis"] = 1
    room._pagar_fome_sede(p, 4, 4, contexto="magia")
    assert p["fome"] == 10 and p["sede"] == 10
    assert p.get("encore_magia_gratis", 0) == 0
    room._pagar_fome_sede(p, 4, 4, contexto="magia")
    assert p["fome"] == 6 and p["sede"] == 6

def test_pagar_fome_sede_piso_zero():
    room, p = _room_bardo()
    p["fome"] = 1; p["sede"] = 0
    room._pagar_fome_sede(p, 3, 3)
    assert p["fome"] == 0 and p["sede"] == 0

def _add_aliado(room, pid, pos, cls="warrior", cancao=False):
    q = {"id": pid, "name": pid, "class_id": cls, "alive": True, "pos": pos,
         "fome": 100, "sede": 100, "gear": {k: None for k in server.GEAR_SLOTS}}
    if cancao:
        q["buffs_cancao"] = {}
    room.players[pid] = q
    return q

def test_encore_menor_raio5():
    room, p = _room_bardo()
    perto = _add_aliado(room, "a1", [7, 5], "warrior")
    longe = _add_aliado(room, "a2", [20, 20], "mage")
    room._aplicar_encore_menor(p)
    assert perto["encore_menor_ate"] == room.round_num
    assert "encore_menor_ate" not in longe
    assert p["encore_menor_ate"] == room.round_num

def test_encore_menor_magia_gratis_mago_clerigo():
    room, p = _room_bardo()
    mago = _add_aliado(room, "m1", [6, 5], "mage")
    guerreiro = _add_aliado(room, "g1", [6, 6], "warrior")
    room._aplicar_encore_menor(p)
    assert mago["encore_magia_gratis"] == 1
    assert guerreiro.get("encore_magia_gratis", 0) == 0

def test_grande_encore_sob_cancao():
    room, p = _room_bardo()
    orig = server.roll_dice
    try:
        server.roll_dice = lambda s: 3
        dentro = _add_aliado(room, "c1", [9, 9], "cleric", cancao=True)
        fora = _add_aliado(room, "c2", [9, 8], "warrior", cancao=False)
        room._aplicar_grande_encore(p)
        assert dentro["grande_encore_ate"] == room.round_num + 3
        assert "grande_encore_ate" not in fora
        assert dentro["encore_magia_gratis"] >= 999
    finally:
        server.roll_dice = orig

# ─── Fase 5 — Improviso: passos sem-alvo + fila de alvo + meta ────────────

def _bardo_com_gaita(qual="padrao", runico=False):
    room, p = _room_bardo()
    async def noop(*a, **k): pass
    room.gm_say = noop; room.send_to = noop; room.push_state = noop
    p["gear"]["off_hand"] = server.criar_instrumento(
        "gaita", qual, encantamento=("runico" if runico else "nenhum"))
    return room, p

def _make_save(ok):
    async def _s(m, tipo, cd, **k): return (ok, 10, cd)
    return _s
def _make_dano(n):
    async def _d(nd, faces, label): return n
    return _d

def test_improviso_resultado_ecos_1rodada():
    room, p = _bardo_com_gaita()
    room._rolar_2d6 = lambda: 4          # Ecos Dolorosos
    st = server.GameRoom._instrumento_stats(p["gear"]["off_hand"])
    _run(room._instr_improviso(p, p["gear"]["off_hand"], st, {}))
    assert p["ecos_ate"] == room.round_num + 1

def test_improviso_resultado_desafinado():
    room, p = _bardo_com_gaita()
    room._rolar_2d6 = lambda: 2
    st = server.GameRoom._instrumento_stats(p["gear"]["off_hand"])
    _run(room._instr_improviso(p, p["gear"]["off_hand"], st, {}))
    assert p["desafinado_ate"] == room.round_num + 1

def test_improviso_enfileira_alvo():
    room, p = _bardo_com_gaita()
    room._rolar_2d6 = lambda: 7          # Nota Cortante — precisa de alvo
    st = server.GameRoom._instrumento_stats(p["gear"]["off_hand"])
    _run(room._instr_improviso(p, p["gear"]["off_hand"], st, {}))
    fila = p.get("improviso_pendente", [])
    assert len(fila) == 1 and fila[0]["res"] == 7 and fila[0]["alvo_tipo"] == "monstro"

def test_improviso_encore_aplica_meta():
    room, p = _bardo_com_gaita()
    seq = iter([12, 8, 12])  # 12 -> [8, 12]; o 12 do reroll -> Encore Menor (nao-runica)
    room._rolar_2d6 = lambda: next(seq)
    room._save_mostrado = _make_save(True); room._rolar_dano_mostrado = _make_dano(0)
    room.monsters = {}   # sem alvos p/ o Acorde: so nao deve crashar
    st = server.GameRoom._instrumento_stats(p["gear"]["off_hand"])
    _run(room._instr_improviso(p, p["gear"]["off_hand"], st, {}))
    assert p["encore_menor_ate"] == room.round_num

def test_improviso_sinfonia_temp():
    room, p = _bardo_com_gaita()
    room._rolar_2d6 = lambda: 10         # Sinfonia Heroica
    st = server.GameRoom._instrumento_stats(p["gear"]["off_hand"])
    _run(room._instr_improviso(p, p["gear"]["off_hand"], st, {}))
    assert p["sinfonia_temp_ate"] == room.round_num + 1
    assert isinstance(p.get("sinfonia_temp_atributos"), list)

# ─── Fase 5 — Improviso: resolução de alvo (Task 6) ────────────────────────

def test_improviso_alvo_nota_cortante():
    room, p = _bardo_com_gaita()
    room.monsters = {"m1": {"id": "m1", "name": "Orc", "hp": 30, "pos": [6, 5],
                            "def_reflexos": 0}}
    room._save_mostrado = _make_save(False); room._rolar_dano_mostrado = _make_dano(6)
    room._instrumento_cd = lambda p, inst: 11
    p["improviso_pendente"] = [{"res": 7, "tier": "padrao", "alvo_tipo": "monstro"}]
    _run(room.handle_improviso_alvo("p1", {"target_id": "m1"}))
    assert room.monsters["m1"]["hp"] == 24
    assert p["improviso_pendente"] == []

def test_improviso_requiem_tick():
    room, p = _bardo_com_gaita()
    room.monsters = {"m1": {"id": "m1", "name": "Orc", "hp": 30, "pos": [6, 5]}}
    room._save_mostrado = _make_save(False); room._instrumento_cd = lambda p, i: 11
    orig = server.roll_dice; server.roll_dice = lambda s: 5
    try:
        virt, vst = room._improviso_virt_st(p["gear"]["off_hand"], "violino")
        _run(room._improviso_requiem_tick(p, virt, vst, room.monsters["m1"]))
    finally:
        server.roll_dice = orig
    assert room.monsters["m1"]["hp"] == 25
    assert "requiem_alvo" not in p

# ─── Fase 5 — Task 7: Gaita ligada ao handle_usar_instrumento + end_turn ───

def test_usar_instrumento_gaita_1mao():
    room, p = _bardo_com_gaita()
    room._rolar_2d6 = lambda: 3          # Falha — sem efeito colateral
    p["fome"] = 10; p["sede"] = 10
    _run(room.handle_usar_instrumento("p1", {}))
    assert p["instrumento_usado"] is True
    assert p["action_done"] is False
    assert p["fome"] == 7 and p["sede"] == 7

def test_end_turn_limpa_fila_improviso():
    room, p = _bardo_com_gaita()
    p["improviso_pendente"] = [{"res": 7, "tier": "padrao", "alvo_tipo": "monstro"}]
    room._limpar_improviso_pendente(p)
    assert p.get("improviso_pendente") in (None, [])


if __name__ == "__main__":
    import inspect
    fns = [f for n, f in sorted(globals().items()) if n.startswith("test_") and inspect.isfunction(f)]
    for f in fns:
        f(); print("ok", f.__name__)
    print(f"\n{len(fns)} testes passaram.")
