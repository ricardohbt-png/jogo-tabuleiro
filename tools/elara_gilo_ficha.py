"""Ficha do Gilo Dedos Sujos (chefe do Ramo B de "O Resgate de Elara"): derivada do `soldado`."""
import copy
import json
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIPO_GILO = "gilo_dedos_sujos"


def _soldado():
    with open(os.path.join(RAIZ, "monstros_personalizados.json"), encoding="utf-8") as f:
        for m in json.load(f):
            if m.get("type") == "soldado":
                return m
    raise LookupError("ficha base `soldado` ausente em monstros_personalizados.json")


def ficha_gilo():
    f = copy.deepcopy(_soldado())
    f.update({"type": TIPO_GILO, "name": "Gilo Dedos Sujos", "emoji": "🗡️", "tier": 2, "cr": 2,
              "base_hp": 38, "hp": 38, "ac": 14, "movement": 7, "dex": 16, "ref_": 4,
              "equipment_enabled": False, "equipped_items": [], "equipment": [],
              "xp": 60, "boss": False, "ai_type": "agressivo", "ai_profile": "agressivo",
              "image": "soldado", "portrait": "soldado"})
    f["attacks"] = [{"name": "Adaga", "damage": "1d6", "damage_types": ["physical"], "num_attacks": 2,
                     "attack_attribute": "dex", "damage_attribute": "dex", "apply_attribute_damage": True,
                     "attribute_mod_base": 2, "base_attack_bonus": 0, "atk_bonus": 4, "range": None,
                     "on_hit": None, "on_hit_effect": None, "poison_dc": 10, "extra_damage": None,
                     "extra_damage_types": []}]
    f["loot_drops"] = [{"kind": "gold", "amount": 40, "chance": 100}]
    return f
