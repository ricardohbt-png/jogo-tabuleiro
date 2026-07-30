"""Testes de Solidificar como fraqueza especial do editor."""
from copy import deepcopy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


def check(label, condition):
    assert condition, label
    print("OK:", label)


raw = deepcopy(next(m for m in S.MONSTER_DEFS if m["type"] == "esqueleto_humano"))
raw.update({"type": "teste_solidificar", "name": "Teste Solidificar",
            "negative_ability_ids": ["solidificar_frio"]})
ok, monster = S._validate_custom_monster(raw)
check("Solidificar é aceito como fraqueza", ok)
check("fraqueza especial é gravada", any(w.get("type") == "solidificar_frio"
                                           for w in monster["weaknesses"]))

room = S.GameRoom("SOLIDIFY_TEST")
room.round_num = 2
target = {"weaknesses": monster["weaknesses"], "resistances": [], "hp": 10}
room._apply_damage_types(1, [S.DMG_COLD], target)
room.round_num = 3
room._apply_damage_types(1, [S.DMG_COLD], target)
check("dois frios consecutivos ativam solidificação", target.get("solido_ate_rodada") == 5)
