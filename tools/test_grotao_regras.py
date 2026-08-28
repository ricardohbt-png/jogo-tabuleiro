"""Regressões das regras de combate específicas do Grotão."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


def check(label, value):
    if not value:
        raise AssertionError(label)
    print("  OK", label)


def make_grotao(room):
    definition = next(x for x in S.MONSTER_DEFS if x["type"] == "grotao")
    monster = S.make_monster(definition, {"id": "g1", "cx": 5, "cy": 5})
    monster["pos"] = [5, 5]
    monster["facing"] = [1, 0]
    monster["movement"] = 0
    room.monsters = {monster["id"]: monster}
    return monster


async def main():
    room = S.GameRoom("grotao-regras")
    room.tiles = [[S.FLOOR] * S.MAP_W for _ in range(S.MAP_H)]
    room.gm_say = room.broadcast = room.send_to = room.push_state = lambda *a, **k: None
    monster = make_grotao(room)
    weak_tile = next(tile for tile in room._monster_tiles(monster)
                     if room._ponto_vulneravel_atingido(monster, tile))
    p1 = {"id": "p1", "pos": [weak_tile[0] - 1, weak_tile[1]]}
    p2 = {"id": "p2", "pos": [weak_tile[0], weak_tile[1] - 1]}

    check("primeiro personagem adjacente reserva o ponto", room._reservar_ponto_vulneravel_grotao(p1, monster, weak_tile))
    check("o personagem reservado ignora a redução", room._ponto_vulneravel_ac(monster, weak_tile, 15, attacker_id="p1") == 10)
    check("outro personagem não usa o ponto na mesma rodada",
          not room._reservar_ponto_vulneravel_grotao(p2, monster, weak_tile)
          and room._ponto_vulneravel_ac(monster, weak_tile, 15, attacker_id="p2") == 15)
    check("o personagem reservado pode repetir o ataque",
          room._reservar_ponto_vulneravel_grotao(p1, monster, weak_tile))
    room.round_num += 1
    check("a reserva muda na rodada seguinte",
          room._reservar_ponto_vulneravel_grotao(p2, monster, weak_tile))

    # O Cuspe Ácido ocorre junto do ataque normal quando o alvo está adjacente.
    player = S.make_player("p", "Alvo", "warrior", 0)
    player["pos"] = [5, 4]
    room.players = {"p": player}
    monster = make_grotao(room)
    calls = []

    async def fake_acid(*args):
        calls.append("acid")

    async def fake_attacks(*args):
        calls.append("attacks")

    room._grotao_cuspir_acido = fake_acid
    room._monster_execute_attacks = fake_attacks
    await room._ai_grotao(monster, [{"kind": "player", "obj": player}])
    check(f"Cuspe Ácido e ataque normal no mesmo turno ({calls})", calls == ["acid", "attacks"])

    # Cercado: a cauda ocupa a ação principal, mas o ácido continua livre.
    room = S.GameRoom("grotao-cauda")
    room.tiles = [[S.FLOOR] * S.MAP_W for _ in range(S.MAP_H)]
    room.gm_say = room.broadcast = room.send_to = room.push_state = lambda *a, **k: None
    monster = make_grotao(room)
    p1 = S.make_player("p1", "A", "warrior", 0)
    p2 = S.make_player("p2", "B", "warrior", 0)
    # O Grotão NÃO é `oriented` (decisão do autor): a Cauda Varredora alcança a
    # coluna imediatamente atrás do footprint 2x2 — [4,5] e [4,6] com ele em [5,5]
    # olhando para leste. Com `oriented` ligado o alcance seria uma casa mais longe.
    p1["pos"], p2["pos"] = [4, 5], [4, 6]
    room.players = {"p1": p1, "p2": p2}
    targets = [{"kind": "player", "obj": p1}, {"kind": "player", "obj": p2}]
    check("dois inimigos ativam a área traseira da cauda",
          len(room._grotao_alvos_cauda(monster, targets)) == 2)
    calls = []
    async def fake_tail(*args):
        calls.append("tail")
    room._usar_cauda_varredora = fake_tail
    room._grotao_cuspir_acido = fake_acid
    room._monster_execute_attacks = fake_attacks
    await room._ai_grotao(monster, targets)
    check(f"cauda e ácido no turno de cerco ({calls})", calls == ["tail", "acid"])

    print("RESULTADO: regras do Grotão passaram")


asyncio.run(main())
