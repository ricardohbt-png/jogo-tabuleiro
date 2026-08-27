"""Testes da configuração de Morte Explosiva no editor."""
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
    "type": "teste_morte_explosiva_cfg",
    "name": "Teste Explosão",
    "monster_abilities": [{
        "id": "morte_explosiva", "uses_per_day": 1, "cooldown_turns": 0,
        "damage_dice": 4, "damage_faces": 8, "radius": 3, "dc": 17, "duration": 4,
    }],
})
ok, monster = S._validate_custom_monster(base)
check("ficha com Morte Explosiva é válida", ok)
ability = next(a for a in monster["special_abilities"] if a["id"] == "morte_explosiva")
check("permanece passiva", ability["action_type"] == "passiva")
check("dados configurados", ability["damage"] == "4d8")
check("raio configurado", ability["radius"] == 3)
check("CD configurada", ability["dc"] == 17)
check("duração das chamas configurada", ability["duration"] == 4)

legacy = deepcopy(base)
legacy["type"] = "teste_morte_explosiva_legacy"
legacy["monster_abilities"][0]["id"] = "explosao_final"
ok, migrated = S._validate_custom_monster(legacy)
check("ID antigo é aceito para migração", ok)
check("ID antigo migra para Morte Explosiva",
      any(a["id"] == "morte_explosiva" for a in migrated["special_abilities"]))

base["type"] = "teste_retaliacao_cfg"
base["name"] = "Teste Retaliação"
base["monster_abilities"] = [{
    "id": "dano_retaliacao", "uses_per_day": 1, "cooldown_turns": 0,
    "damage_dice": 3, "damage_faces": 10, "damage_type": "fire",
}]
ok, monster = S._validate_custom_monster(base)
check("Dano de Retaliação configurável é válido", ok)
ability = next(a for a in monster["special_abilities"] if a["id"] == "dano_retaliacao")
check("dados e elemento de retaliação configurados", ability["damage"] == "3d10" and ability["damage_types"] == ["fire"])
