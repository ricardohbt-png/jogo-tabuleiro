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
    return room, p

def test_slot_instrumento_existe():
    assert "instrumento" in server.GEAR_SLOTS

def test_slot_category_instrumento():
    inst = server.criar_instrumento("harpa", "padrao")
    assert server.GameRoom._slot_category_for_item(inst) == "instrumento"


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
    p["gear"]["instrumento"] = server.criar_instrumento("harpa", "padrao")  # 2 mãos
    m = {"id": "m1", "name": "Goblin", "hp": 20, "pos": [6, 5], "alive": True,
         "ref_": 0, "ca": 10, "saves_base": {}}
    room.monsters["m1"] = m
    p["action_done"] = True
    _run(room.handle_usar_instrumento("p1", {"target_id": "m1"}))
    assert m["hp"] == 20     # bloqueado

def test_economia_1mao_nao_gasta_acao_principal():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["instrumento"] = server.criar_instrumento("sino", "padrao")   # 1 mão
    _run(room.handle_usar_instrumento("p1", {}))
    assert p["instrumento_usado"] is True
    assert p["action_done"] is False

def test_um_instrumento_por_turno():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["instrumento"] = server.criar_instrumento("sino", "padrao")
    _run(room.handle_usar_instrumento("p1", {}))
    fome_apos_1 = p["fome"]
    _run(room.handle_usar_instrumento("p1", {}))  # recusa
    assert p["fome"] == fome_apos_1

async def _save_falha(*a, **k): return (False, 1, 0, 1)
async def _save_passa(*a, **k): return (True, 20, 0, 20)
async def _dano10(n, faces, label): return 10

def test_nota_cortante_dano_cheio_na_falha():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["instrumento"] = server.criar_instrumento("harpa", "padrao")  # 5q, 2d6
    m = {"id": "m1", "name": "Goblin", "hp": 30, "pos": [8, 5], "alive": True}
    room.monsters["m1"] = m
    room._save_mostrado = _save_falha
    room._rolar_dano_mostrado = _dano10
    _run(room.handle_usar_instrumento("p1", {"target_id": "m1"}))
    assert m["hp"] == 20     # 30 - 10 (cheio)

def test_nota_cortante_meia_no_sucesso():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["instrumento"] = server.criar_instrumento("harpa", "padrao")
    m = {"id": "m1", "name": "Goblin", "hp": 30, "pos": [6, 5], "alive": True}
    room.monsters["m1"] = m
    room._save_mostrado = _save_passa
    room._rolar_dano_mostrado = _dano10
    _run(room.handle_usar_instrumento("p1", {"target_id": "m1"}))
    assert m["hp"] == 25     # 30 - 5 (metade)

def test_nota_cortante_fora_de_alcance_recusa():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["instrumento"] = server.criar_instrumento("harpa", "velho")   # 3q
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
    p["gear"]["instrumento"] = server.criar_instrumento("tambor", "padrao")  # raio2, 2d4, push2
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
    p["gear"]["instrumento"] = server.criar_instrumento("tambor", "padrao")
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
    p["gear"]["instrumento"] = server.criar_instrumento("sino", "padrao")  # 1d4, dur 3
    _run(room.handle_usar_instrumento("p1", {}))
    assert p["ecos_ate"] == room.round_num + 3
    assert p["ecos_dano"] == "1d4"
    assert p["instrumento_usado"] is True
    assert p["action_done"] is False   # 1 mão: pode atacar depois

def test_ecos_retaliacao():
    room, p = _room_bardo(); _mute(room)
    p["ecos_ate"] = room.round_num + 2
    p["ecos_dano"] = "1d4"
    m = {"id": "m1", "name": "Goblin", "hp": 20, "pos": [5, 5], "alive": True}
    room.monsters["m1"] = m
    async def _dano3(n, faces, label): return 3
    room._rolar_dano_mostrado = _dano3
    _run(room._instr_ecos_retaliar(p, m))
    assert m["hp"] == 17

def test_ecos_expira():
    room, p = _room_bardo(); _mute(room)
    p["ecos_ate"] = room.round_num - 1   # já expirou
    m = {"id": "m1", "name": "Goblin", "hp": 20, "pos": [5, 5], "alive": True}
    _run(room._instr_ecos_retaliar(p, m))
    assert m["hp"] == 20

def test_sinfonia_boost_por_qualidade():
    room, p = _room_bardo(); _mute(room)
    p["guild_owned"] = {"especializacoes": [], "tecnicas": []}
    assert room._cancao_nivel_atributo(p, "acerto") == 1   # sem alaúde
    p["gear"]["instrumento"] = server.criar_instrumento("alaude", "velho")
    assert room._cancao_nivel_atributo(p, "acerto") == 2   # velho: só acerto
    assert room._cancao_nivel_atributo(p, "dano") == 1
    p["gear"]["instrumento"] = server.criar_instrumento("alaude", "padrao")
    for a in ("acerto", "dano", "ca", "movimento", "resistencia"):
        assert room._cancao_nivel_atributo(p, a) == 2, a

def test_sinfonia_empilha_com_espec():
    room, p = _room_bardo(); _mute(room)
    p["guild_owned"] = {"especializacoes": ["bardo_cancao_acerto"], "tecnicas": []}
    p["gear"]["instrumento"] = server.criar_instrumento("alaude", "padrao")
    assert room._cancao_nivel_atributo(p, "acerto") == 3   # 2 (espec) + 1 (alaúde)

if __name__ == "__main__":
    import inspect
    fns = [f for n, f in sorted(globals().items()) if n.startswith("test_") and inspect.isfunction(f)]
    for f in fns:
        f(); print("ok", f.__name__)
    print(f"\n{len(fns)} testes passaram.")
