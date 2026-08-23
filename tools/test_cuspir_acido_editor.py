"""Testes da configuração de Cuspir Ácido no editor de monstros."""
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
    "type": "teste_cuspir_acido_configuravel", "name": "Teste Ácido",
    "monster_abilities": [{
        "id": "cuspir_acido", "uses_per_day": 1, "cooldown_turns": 2,
        "damage_dice": 4, "damage_faces": 8, "range": 7, "dc": 16,
    }],
})
ok, monster = S._validate_custom_monster(raw)
check("Cuspir Ácido configurável é válido", ok)
ability = next(a for a in monster["special_abilities"] if a["id"] == "cuspir_acido")
check("dados de dano configurados", ability["damage"] == "4d8")
check("alcance configurado", ability["range"] == 7)
check("CD de Reflexos configurada", ability["dc"] == 16 and ability["save"] == "reflexos")
check("descrição avisa do dano a equipamento", "equipamento" in ability["descricao"].lower())
