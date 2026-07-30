"""Testes de Pele Amaldiçoada. Execute: python tools/test_pele_amaldicoada.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


def check(label, condition):
    assert condition, label
    print("OK:", label)


room = S.GameRoom("CURSE_TEST")
attacker = S.make_player("p1", "Teste", "warrior", 0)
attacker["str_"] = 14  # +2
weapon = {"id": "espada_teste", "name": "Espada", "die": "1d4", "stat": "str_"}
target = {"type": "lobisomem", "subtipo": "raca_padrao", "immunities": [],
          "resistances": [], "weaknesses": []}

old_roll = S.roll_dice
S.roll_dice = lambda expression: 4
try:
    # 4 (dado) + 2 (FOR) + 4 (bônus físico) = 10; Pele Amaldiçoada → 5.
    dmg, *_ = room._resolver_dano_ataque_basico(attacker, target, False, 10,
                                                  bonus_extra=4, weapon_override=weapon)
    check("reduz o total de arma e bônus", dmg == 5)
    magic = dict(weapon, magical=True)
    dmg_magic, *_ = room._resolver_dano_ataque_basico(attacker, target, False, 10,
                                                        bonus_extra=4, weapon_override=magic)
    check("arma mágica causa dano total", dmg_magic == 10)
    check("magia causa dano total", room._apply_damage_types(10, [S.DMG_MAGIC], target) == 10)
finally:
    S.roll_dice = old_roll
