"""Testes de Envenenar no editor de monstros."""
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
    "type": "teste_envenenar", "name": "Teste Envenenar",
    "attacks": [
        {"name": "Garra", "damage": "1d4", "damage_types": ["physical"]},
        {"name": "Mordida", "damage": "1d6", "damage_types": ["physical"]},
    ],
    "monster_abilities": [{"id": "envenenar", "uses_per_day": 1, "cooldown_turns": 0,
                             "attack_index": 1, "veneno_id": "veneno_escorpiao_pedra", "poison_dc": 16}],
})
ok, monster = S._validate_custom_monster(raw)
check("Envenenar configurável é válido", ok)
check("vincula o ataque selecionado", monster["attacks"][1]["on_hit"] == "veneno_escorpiao_pedra")
check("preserva a CD selecionada", monster["attacks"][1]["poison_dc"] == 16)
check("não altera os outros ataques", monster["attacks"][0]["on_hit"] is None)

room = {"id": "r", "cx": 1, "cy": 1}
instance = S.make_monster(monster, room)
check("instância mantém o vínculo", instance["attacks"][1]["on_hit"] == "veneno_escorpiao_pedra")
