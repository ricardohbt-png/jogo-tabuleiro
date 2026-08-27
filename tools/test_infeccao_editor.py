"""Testes da configuração de Infecção no editor de monstros."""
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
    "type": "teste_infeccao_configuravel", "name": "Teste Infecção",
    "attacks": [
        {"name": "Golpe", "damage": "1d4", "damage_types": ["physical"], "num_attacks": 1},
        {"name": "Mordida", "damage": "1d6", "damage_types": ["physical"], "num_attacks": 1},
    ],
    "monster_abilities": [{
        "id": "infeccao", "uses_per_day": 1, "cooldown_turns": 0,
        "attack_index": 1, "disease_severity": "moderada", "dc": 16,
    }],
})
ok, monster = S._validate_custom_monster(raw)
check("Infecção configurável é válida", ok)
ability = next(a for a in monster["special_abilities"] if a["id"] == "infeccao")
check("mantém o teste de Fortitude", ability["save"] == "fortitude")
check("preserva a CD selecionada", ability["dc"] == 16)
check("moderada aplica os dois primeiros sintomas", ability["disease_severity"] == "pesada")
check("descrição informa a severidade", "moderada" in ability["descricao"])
check("mantém o ataque escolhido", ability["attack_index"] == 1)
check("efeito fica no ataque escolhido", monster["attacks"][1]["disease_severity"] == "pesada")
check("outro ataque não recebe doença", monster["attacks"][0].get("disease_severity") is None)

legacy = deepcopy(raw)
legacy["type"] = "teste_contagiar_legacy"
legacy["monster_abilities"] = [{"id": "contagiar", "attack_index": 0, "dc": 10, "disease_severity": "leve"}]
ok, migrated = S._validate_custom_monster(legacy)
check("Contagiar é aceito como habilidade canônica", ok)
check("Contagiar vincula doença ao ataque", migrated["attacks"][0]["disease_severity"] == "leve")
