"""Regressão das regras de custo de movimento em água."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server


def main():
    room = server.GameRoom.__new__(server.GameRoom)
    room.materiais = {(1, 1): "agua", (2, 2): "agua_profunda"}
    # A sala e' montada com __new__ (sem __init__) de proposito: o custo de
    # passo em agua e' funcao pura de material + equipamento. Mas o
    # _water_step_cost passou a consultar a Tempestade de Ciclones, e o
    # __init__ e' quem cria `zonas_especiais` -- sem esta linha o teste estoura
    # AttributeError. Fica explicito de que estado a funcao depende hoje.
    room.zonas_especiais = []
    sem_armadura = {"gear": {"armor": None}}
    media = {"gear": {"armor": {"armor_category": "media"}}}
    pesada = {"gear": {"armor": {"armor_category": "pesada"}}}
    natural = {"natural_armor": 3}
    erratico = {"natural_armor": 3, "special_abilities": [{"id": "movimento_erratico"}]}
    voador = {"voo": True, "altura": 2,
              "gear": {"armor": {"armor_category": "pesada"}}}

    checks = [
        (room._water_step_cost(sem_armadura, 1, 1) == 2, "água sem armadura = 2"),
        (room._water_step_cost(sem_armadura, 2, 2) == 3, "água profunda sem armadura = 3"),
        (room._water_step_cost(media, 1, 1) == 3, "média em água = 3"),
        (room._water_step_cost(media, 2, 2) == 4, "média em profunda = 4"),
        (room._water_step_cost(pesada, 1, 1) == 4, "pesada em água = 4"),
        (room._water_step_cost(pesada, 2, 2) == 5, "pesada em profunda = 5"),
        (room._water_step_cost(natural, 1, 1) == 3, "natural em água = 3"),
        (room._water_step_cost(natural, 2, 2) == 4, "natural em profunda = 4"),
        (room._water_step_cost(erratico, 1, 1) == 1 and room._water_step_cost(erratico, 2, 2) == 1,
         "Movimento Errático ignora água"),
        (room._water_step_cost(voador, 1, 1) == 1
         and room._water_step_cost(voador, 2, 2) == 1
         and room._water_step_cost(voador, 3, 3) == 1,
         "Voo acima do chão ignora custos de terreno"),
        (room._water_turn_moves(voador, 6) == 6,
         "Voo acima do chão ignora penalidade de pântano"),
        (room._water_turn_moves({}, 0) == 1, "mínimo de movimento = 1"),
        (room._water_turn_moves({}, 1) == 1, "um ponto permite a passada mínima"),
    ]
    for ok, label in checks:
        assert ok, label
        print("OK", label)


if __name__ == "__main__":
    main()
