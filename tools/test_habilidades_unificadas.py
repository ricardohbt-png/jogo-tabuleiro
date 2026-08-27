"""Regressões das habilidades unificadas do editor de criaturas."""
from copy import deepcopy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


def check(label, condition):
    if not condition:
        raise AssertionError(label)
    print(f"OK: {label}")


base = deepcopy(next(m for m in S.MONSTER_DEFS if m["type"] == "lacralion_adulto"))
base.update({
    "type": "teste_habilidades_unificadas",
    "name": "Teste Habilidades Unificadas",
    "monster_abilities": [{
        "id": "carapaca_espinhosa", "damage_dice": 3, "damage_faces": 8,
        "damage_type": "acid",
    }],
    "negative_ability_ids": ["mente_fraca"],
    "negative_ability_configs": {
        "vulnerabilidade": {"penalty": 3, "saves": ["fortitude", "vontade", "reflexos"]},
    },
})
ok, monster = S._validate_custom_monster(base)
check("ficha com aliases antigos é válida", ok)
abilities = {a["id"]: a for a in monster["special_abilities"]}
check("retaliação migra para o ID canônico", "dano_retaliacao" in abilities)
check("retaliação preserva dados e elemento", abilities["dano_retaliacao"]["damage"] == "3d8"
      and abilities["dano_retaliacao"]["damage_types"] == ["acid"])
check("fraqueza migra para Vulnerabilidade", monster["negative_ability_ids"] == ["vulnerabilidade"])
vulnerability = next(w for w in monster["weaknesses"] if w.get("vulnerabilidade"))
check("Vulnerabilidade preserva penalidade e os três testes",
      vulnerability["bonus_flat"] == -3
      and vulnerability["saves"] == ["fortitude", "vontade", "reflexos"])

print("Todos os testes de habilidades unificadas passaram.")
