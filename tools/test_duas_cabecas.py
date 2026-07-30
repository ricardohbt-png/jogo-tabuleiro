"""Testes da habilidade passiva Duas Cabeças."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


def check(label, condition):
    assert condition, label
    print("OK:", label)


room = object.__new__(S.GameRoom)
normal = {"base_movement": 6, "vision_base": 0, "int_": 10, "dex": 10, "special_abilities": []}
duas_cabecas = {**normal, "special_abilities": [{"id": "duas_cabecas"}]}

check("Duas Cabeças aumenta a visão em 2", S.GameRoom._get_raio_visao_monstro(room, duas_cabecas)
      == S.GameRoom._get_raio_visao_monstro(room, normal) + 2)
check("Duas Cabeças penaliza ataque furtivo", S.GameRoom._penalidade_furtivo_duas_cabecas(room, duas_cabecas) == -2)
check("outras criaturas não recebem penalidade", S.GameRoom._penalidade_furtivo_duas_cabecas(room, normal) == 0)
