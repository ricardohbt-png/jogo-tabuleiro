"""Testes da configuração de Explosão Final no editor."""
from copy import deepcopy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


def check(label, condition):
    assert condition, label
    print("OK:", label)


base = deepcopy(next(m for m in S.MONSTER_DEFS if m["type"] == "esqueleto_humano"))
base.update({
    "type": "teste_explosao_final_cfg",
    "name": "Teste Explosão",
    "monster_abilities": [{
        "id": "explosao_final", "uses_per_day": 1, "cooldown_turns": 0,
        "damage_dice": 4, "damage_faces": 8, "radius": 3, "dc": 17,
    }],
})
ok, monster = S._validate_custom_monster(base)
check("ficha com Explosão Final é válida", ok)
ability = next(a for a in monster["special_abilities"] if a["id"] == "explosao_final")
check("permanece passiva", ability["action_type"] == "passiva")
check("dados configurados", ability["damage"] == "4d8")
check("raio configurado", ability["radius"] == 3)
check("CD configurada", ability["dc"] == 17)

base["type"] = "teste_corpo_chamas_cfg"
base["name"] = "Teste Corpo em Chamas"
base["monster_abilities"] = [{
    "id": "corpo_em_chamas", "uses_per_day": 1, "cooldown_turns": 0,
    "damage_dice": 3, "damage_faces": 10,
}]
ok, monster = S._validate_custom_monster(base)
check("Corpo em Chamas configurável é válido", ok)
ability = next(a for a in monster["special_abilities"] if a["id"] == "corpo_em_chamas")
check("dados de Corpo em Chamas configurados", ability["damage"] == "3d10")
