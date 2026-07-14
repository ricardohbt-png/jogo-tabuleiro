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
    check("ficha ND3 / seis casas", definition["cr"] == 3 and definition["size"] == [2, 3] and definition["oriented"])
    check("ataques da ficha", [a["damage"] for a in definition["attacks"]] == ["1d10+4", "1d8+4"])
    check("carapaça sem fraqueza por impacto", definition["resistances"][0]["reduction"] == 2 and len(definition["weaknesses"]) == 1)
    check("ponto vulnerável reduz ND em 0,25", definition["weaknesses"][0].get("nd_penalty") == .25)

    g = setup(); m = S.make_monster(definition, {"id":"r", "cx":5, "cy":5})
    m["pos"] = [5, 5]; m["facing"] = [1, 0]
    check("footprint orientado 2x3", g._monster_tiles(m) == [[5,5],[5,6],[4,5],[4,6],[3,5],[3,6]])
    # Ataque vindo da frente sofre redução; do lado ignora a carapaça.
    check("carapaça reduz 2 pela frente", g._apply_damage_types(8, [S.DMG_PHYSICAL], m, attacker_pos=[7, 5]) == 6)
    check("ponto vulnerável remove redução física", g._apply_damage_types(8, [S.DMG_PHYSICAL], m, target_pos=[4, 5]) == 8)
    check("dois pontos vulneráveis reduzem CA 15 para 10", g._ponto_vulneravel_ac(m, [4, 5], 15) == 10 and g._ponto_vulneravel_ac(m, [4, 6], 15) == 10 and g._ponto_vulneravel_ac(m, [5, 5], 15) == 15)
    # Reflexos falho marca exatamente o dano seguinte daquele efeito com +1.
    old_rand = S.random.randint; S.random.randint = lambda a,b: 1
    passou, *_ = g._testar_save(m, "reflexos", 99)
    check("corpo pesado falha Reflexos", not passou and g._apply_damage_types(5, ["fire"], m) == 6)
    S.random.randint = old_rand

    p1 = S.make_player("p1", "Armadura", "warrior", 0); p1["pos"] = [2, 5]
    p2 = S.make_player("p2", "Traseira", "warrior", 0); p2["pos"] = [3, 4]
    g.players = {"p1": p1, "p2": p2}; g.monsters = {m["id"]: m}
    targets = [{"kind":"player", "obj":p1}, {"kind":"player", "obj":p2}]
    check("cauda encontra inimigos atrás", len(g._grotao_alvos_cauda(m, targets)) == 2)
    # Ácido em falha de Reflexos aplica um nível à armadura antes da arma.
    g._testar_save = lambda *a, **k: (False, 1, 0, 1)
    hp = p1["hp"]
    await g._grotao_cuspir_acido(m, {"kind":"player", "obj":p1})
    check("ácido causa dano", p1["hp"] < hp)
    check("ácido corrói armadura primeiro", g._corrosao_ca_pen(p1) == 1 and g._corrosao_arma_pen(p1) == 0)

    p1["derrubado_sem_movimento"] = True
    await g._start_initiative_player_turn(p1)
    check("derrubado perde o próximo movimento", p1["moves_left"] == 0 and not p1.get("derrubado_sem_movimento"))

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

    print(f"RESULTADO: {OK} passaram, {FAIL} falharam")
    return FAIL

sys.exit(asyncio.run(main()))
