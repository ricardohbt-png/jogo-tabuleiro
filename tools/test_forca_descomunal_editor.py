"""Testes da configuração de Força Descomunal no editor de monstros."""
from copy import deepcopy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


def check(label, condition):
    assert condition, label
    print("OK:", label)


raw = deepcopy(next(m for m in S.MONSTER_DEFS if m["type"] == "esqueleto_humano"))
raw.update({
    "type": "teste_forca_descomunal_configuravel", "name": "Teste Força",
    "monster_abilities": [{
        "id": "forca_descomunal", "uses_per_day": 1, "cooldown_turns": 2, "dc": 17,
    }],
})
ok, monster = S._validate_custom_monster(raw)
check("Força Descomunal configurável é válida", ok)
ability = next(a for a in monster["special_abilities"] if a["id"] == "forca_descomunal")
check("preserva a recarga selecionada", ability["cooldown_turns"] == 2)
check("preserva a CD selecionada", ability["dc"] == 17)
check("descrição mostra a recarga selecionada", "Recarga 2 rodadas" in ability["descricao"])
check("descrição mostra a CD selecionada", "CD 17" in ability["descricao"])
