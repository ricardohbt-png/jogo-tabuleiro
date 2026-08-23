"""Testes da habilidade Causar Sangramento no editor e no combate."""

from copy import deepcopy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


def check(label, condition):
    assert condition, label
    print("OK:", label)


raw = deepcopy(next(m for m in S.MONSTER_DEFS if m["type"] == "goblin"))
raw.update({
    "type": "teste_causar_sangramento",
    "name": "Teste Sangramento",
    "monster_abilities": [{
        "id": "causar_sangramento", "uses_per_day": 1, "cooldown_turns": 0,
    }, {
        "id": "causar_hemorragia", "cooldown_turns": 3,
    }],
    "attacks": [{
        "name": "Lâmina", "damage": "1d6", "damage_types": ["physical"],
        "causa_sangramento": True,
        "aplica_hemorragia": True,
    }],
})
ok, monster = S._validate_custom_monster(raw)
check("Causar Sangramento global é aceito pelo editor", ok)
check("a habilidade global chega à ficha", any(
    a.get("id") == "causar_sangramento" for a in monster["special_abilities"]))
hemorrhage = next(a for a in monster["special_abilities"] if a["id"] == "causar_hemorragia")
check("Causar Hemorragia aceita ataque e recarga", hemorrhage["attack_index"] == 0 and hemorrhage["cooldown_turns"] == 3)
check("Causar Hemorragia não é limitada a um único uso", hemorrhage.get("uses_per_day") is None)
check("a opção por ataque é preservada", monster["attacks"][0]["causa_sangramento"] is True)
check("o efeito direto de Hemorragia é preservado", monster["attacks"][0]["aplica_hemorragia"] is True)
instance = S.make_monster(monster, {"id": "r", "cx": 1, "cy": 1})
check("a instância do monstro mantém o ataque especial", any(
    a.get("id") == "causar_hemorragia" for a in instance["special_abilities"]))
check("a instância não transforma recarga em uso único", "causar_hemorragia" not in instance.get("ability_uses", {}))

room = S.GameRoom("BLEED_ABILITY_TEST")
room._rolar_dado = lambda _: 6
normal = {"id": "normal", "name": "Normal", "hp": 20, "max_hp": 20, "alive": True}
room.players = {"normal": normal}
check("a habilidade é reconhecida no monstro", room._tem_habilidade(monster, "causar_sangramento") is True)
check("aplica em personagem vivo", room._aplicar_sangramento(normal)["nivel"] == 1)
check("ataque especial entra em recarga", room._ativar_habilidade_nativa(monster, hemorrhage) is True and monster["ability_cooldowns"]["causar_hemorragia"] == 3)
check("ataque especial respeita a recarga", room._ativar_habilidade_nativa(monster, hemorrhage) is False)
monster["ability_cooldowns"]["causar_hemorragia"] = 0
check("ataque especial volta após a recarga", room._ativar_habilidade_nativa(monster, hemorrhage) is True)

for label, target in [
    ("morto-vivo", {"subtipo": "morto_vivo", "hp": 20}),
    ("elemental", {"type": "elemental_fogo", "hp": 20}),
    ("construto", {"subtipo": "construto", "hp": 20}),
]:
    check(f"imune contra {label}", room._pode_sangrar(target) is False)
    check(f"não aplica Sangramento em {label}", room._aplicar_sangramento(target) is None)
    check(f"não aplica Hemorragia em {label}", room._aplicar_hemorragia(target) is False)

print("CAUSAR_SANGRAMENTO_TEST_PASS")
