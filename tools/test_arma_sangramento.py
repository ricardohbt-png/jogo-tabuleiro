"""Testes da habilidade Causar Sangramento concedida por uma arma."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


raw = {
    "id": "lamina_sangrenta_teste",
    "name": "Lâmina Sangrenta",
    "item_type": "weapon",
    "die": "1d6",
    "stat": "str_",
    "categoria": "cortante",
    "granted_ability": "causar_sangramento",
}
ok, item = S._validate_custom_weapon(raw)
assert ok, item
assert item["granted_ability"] == "causar_sangramento"
combat = S._custom_weapon_combat_dict(item)
assert combat["granted_ability"] == "causar_sangramento"
assert "causar_sangramento" in S.WEAPON_GRANTED_ABILITIES
print("ARMA_SANGRAMENTO_TEST_PASS")
