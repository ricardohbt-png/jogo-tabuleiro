"""Regressão do Grotão (ND 3). Rode: python tools/test_grotao.py"""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

OK = FAIL = 0
def check(label, value):
    global OK, FAIL
    if value: OK += 1; print("  OK", label)
    else: FAIL += 1; print("  FALHOU", label)

async def noop(*args, **kwargs): pass

def setup():
    g = S.GameRoom("grotao")
    g.tiles = [[S.FLOOR] * S.MAP_W for _ in range(S.MAP_H)]
    g.rooms = []; g.door_rooms = {}; g.zonas_especiais = []; g.armadilhas = []
    g.broadcast = noop; g.gm_say = noop; g.send_to = noop; g.push_state = noop
    return g

async def main():
    definition = next(x for x in S.MONSTER_DEFS if x["type"] == "grotao")
    check("ficha ND3 / quatro casas sem orientação", definition["cr"] == 3 and definition["size"] == [2, 2] and not definition["oriented"])
    check("ataques da ficha (dado + Forca por apply_attribute_damage)",
          [a["damage"] for a in definition["attacks"]] == ["1d10", "1d8"]
          and all(a.get("apply_attribute_damage") for a in definition["attacks"])
          and definition["str_"] == 18)
    # Busca por TIPO, nao por posicao: a lista de fraquezas tem mais de uma
    # entrada (ponto_vulneravel + corpo_pesado) e a ordem nao e contrato.
    _fraq = lambda t: next((w for w in definition["weaknesses"] if w.get("type") == t), None)
    check("carapaça sem fraqueza por impacto",
          definition["resistances"][0]["reduction"] == 3
          and not any(w.get("type") in ("physical", "impacto", "contundente")
                      for w in definition["weaknesses"]))
    check("ponto vulnerável reduz ND em 0,25", (_fraq("ponto_vulneravel") or {}).get("nd_penalty") == .25)

    g = setup(); m = S.make_monster(definition, {"id":"r", "cx":5, "cy":5})
    m["pos"] = [5, 5]; m["facing"] = [1, 0]
    check("footprint fixo 2x2", g._monster_tiles(m) == [[5,5],[5,6],[6,5],[6,6]])
    check("ataque ortogonal cobre as quatro faces",
          set(map(tuple, g._monster_orthogonal_attack_tiles(m))) ==
          {(5,4),(6,4),(5,7),(6,7),(4,5),(4,6),(7,5),(7,6)})
    check("ataque ortogonal aceita as duas casas de cada face",
          all(g._monster_attack_in_range(m, list(pos))
              for pos in ((5,4),(6,4),(5,7),(6,7),(4,5),(4,6),(7,5),(7,6))))
    # Todo dano físico sofre redução; somente o ponto vulnerável a atravessa.
    check("carapaça reduz 3 fora do ponto vulnerável", g._apply_damage_types(8, [S.DMG_PHYSICAL], m, attacker_pos=[7, 5]) == 5 and g._apply_damage_types(8, [S.DMG_PHYSICAL], m, target_pos=[5, 5]) == 5)
    check("ponto vulnerável remove redução física", g._apply_damage_types(8, [S.DMG_PHYSICAL], m, target_pos=[6, 6]) == 8)
    check("só o quadrado posterior direito reduz CA 15 para 10",
           g._ponto_vulneravel_ac(m, [6, 6], 15) == 10
           and g._ponto_vulneravel_ac(m, [6, 5], 15) == 15
           and g._ponto_vulneravel_ac(m, [5, 6], 15) == 15
           and g._ponto_vulneravel_ac(m, [5, 5], 15) == 15)
    # Reflexos falho marca exatamente o dano seguinte daquele efeito com +1.
    old_rand = S.random.randint; S.random.randint = lambda a,b: 1
    passou, *_ = g._testar_save(m, "reflexos", 99)
    check("corpo pesado falha Reflexos", not passou and g._apply_damage_types(5, ["fire"], m) == 6)
    S.random.randint = old_rand

    # Corpo 2x2 fixo ocupa x=5..6; a cauda preserva a face traseira
    # indicada pelo último movimento (facing leste -> coluna x=4).
    p1 = S.make_player("p1", "Armadura", "warrior", 0); p1["pos"] = [4, 5]
    p2 = S.make_player("p2", "Traseira", "warrior", 0); p2["pos"] = [4, 6]
    g.players = {"p1": p1, "p2": p2}; g.monsters = {m["id"]: m}
    targets = [{"kind":"player", "obj":p1}, {"kind":"player", "obj":p2}]
    check("cauda encontra inimigos atrás", len(g._grotao_alvos_cauda(m, targets)) == 2)
    # Ácido em falha de Reflexos aplica um nível à armadura antes da arma.
    g._testar_save = lambda *a, **k: (False, 1, 0, 1)
    hp = p1["hp"]
    await g._grotao_cuspir_acido(m, {"kind":"player", "obj":p1})
    check("ácido causa dano", p1["hp"] < hp)
    check("ácido corrói armadura primeiro", g._corrosao_ca_pen(p1) == 1 and g._corrosao_arma_pen(p1) == 0)

    # Jogador proprio: o p1 pode ter morrido para o acido acima (3d6+1 contra 14 PV),
    # e heroi morto nao tem turno preparado -- reusar o p1 deixava esta checagem
    # instavel (falhava em ~6 de 8 execucoes).
    p3 = S.make_player("p3", "Derrubado", "warrior", 0); p3["pos"] = [8, 8]
    g.players["p3"] = p3
    p3["derrubado_sem_movimento"] = True
    await g._start_initiative_player_turn(p3)
    check("derrubado perde o próximo movimento", p3["moves_left"] == 0 and not p3.get("derrubado_sem_movimento"))

    custom = {"type":"teste_vulneravel", "name":"Teste Vulnerável", "size":[2,1], "oriented":True,
              "attacks":[{"name":"Mordida","damage":"1d6"}], "weaknesses":[{"type":"ponto_vulneravel","tiles":[[1,0]]}]}
    ok, ficha = S._validate_custom_monster(custom)
    check("editor aceita ponto vulnerável em criatura grande", ok and ficha["size"] == [2,1] and ficha["weaknesses"][0]["type"] == "ponto_vulneravel")
    custom["monster_abilities"] = [{"id":"cuspir_acido","uses_per_day":2,"cooldown_turns":3}, {"id":"cauda_varredora","uses_per_day":2,"cooldown_turns":2}, {"id":"furia_bestial","uses_per_day":1,"cooldown_turns":0}]
    ok, ficha = S._validate_custom_monster(custom)
    check("editor salva as três habilidades funcionais", ok and {a["id"] for a in ficha["special_abilities"]} == {"cuspir_acido", "cauda_varredora", "furia_bestial"})
    custom["size"] = [1,1]
    ok, ficha = S._validate_custom_monster(custom)
    check("editor rejeita ponto vulnerável em uma casa", ok and not any(w.get("type") == "ponto_vulneravel" for w in ficha["weaknesses"]))

    # -- Corpo Pesado orientado por DADO, nao pelo tipo cravado ----------------
    # Antes o +1 de dano so existia para type == "grotao"; o editor oferecia a
    # fraqueza corpo_pesado e ela nao fazia nada em criatura personalizada.
    print("[corpo pesado data-driven]")
    g2 = setup()
    generico = {"type": "bicho_pesado", "name": "Bicho Pesado", "hp": 20, "ac": 10,
                "size": [1, 1], "ref_": 0,
                "weaknesses": [{"type": "corpo_pesado"}]}
    m2 = S.make_monster(generico, {"id": "r", "cx": 2, "cy": 2}); m2["pos"] = [2, 2]
    leve = {"type": "bicho_leve", "name": "Bicho Leve", "hp": 20, "ac": 10,
            "size": [1, 1], "ref_": 0, "weaknesses": []}
    m3 = S.make_monster(leve, {"id": "r", "cx": 3, "cy": 3}); m3["pos"] = [3, 3]
    old = S.random.randint; S.random.randint = lambda a, b: 1
    g2._testar_save(m2, "reflexos", 99)
    g2._testar_save(m3, "reflexos", 99)
    S.random.randint = old
    check("criatura do editor com Corpo Pesado sofre +1",
          g2._apply_damage_types(5, ["fire"], m2) == 6)
    check("criatura sem a fraqueza nao sofre +1",
          g2._apply_damage_types(5, ["fire"], m3) == 5)

    print(f"RESULTADO: {OK} passaram, {FAIL} falharam")
    return FAIL

sys.exit(asyncio.run(main()))
