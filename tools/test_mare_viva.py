"""Testes de Maré Viva. Execute: python tools/test_mare_viva.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server import GameRoom


def check(label, condition):
    assert condition, label
    print("OK:", label)


room = GameRoom("TIDE_TEST")
monster = {"id": "water_elemental", "pos": [4, 4], "size": [1, 1]}
room.materiais = {(4, 4): "agua"}
check("ativa sobre água", room._mare_viva_ativa(monster))
room.materiais = {(5, 5): "agua_profunda"}
check("ativa adjacente à água profunda", room._mare_viva_ativa(monster))
room.materiais = {(6, 4): "agua"}
check("não ativa além de uma casa", not room._mare_viva_ativa(monster))
