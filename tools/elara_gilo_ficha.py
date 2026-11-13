"""Ficha oficial do Gilo Dedos Sujos, chefe do Ramo B de "O Resgate de Elara"."""
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
    f.update({"type": TIPO_GILO, "name": "Gilo Dedos Sujos", "emoji": "🗡️", "tier": 2, "cr": 2.5,
              "level": 4, "class_id": "rogue", "base_hp": 35, "hp": 36,
              "ac": 16, "movement": 6, "str_": 14, "dex": 15, "con_": 12, "int_": 11,
              "base_attack_bonus": 3, "fort_base": 1, "ref_base": 4, "will_base": 1,
              "natural_armor": 0,
              "equipment_enabled": True,
              "equipped_items": ["leather_plate", "hand_crossbow", "ring_vita", "circlet",
                                 "boots", "amulet", "cinto_utilidades"],
              "equipment": ["leather_plate", "hand_crossbow", "ring_vita", "circlet",
                            "boots", "amulet", "cinto_utilidades"],
              "gilo_loadout": {
                  "weapons": [{"id": "hand_crossbow", "quantity": 2}],
                  "armor": "leather_plate",
                  "accessories": ["ring_vita", "ring_vita", "amulet", "circlet", "boots", "cinto_utilidades"],
                  "consumables": {
                      "virote_incendiario": 30, "virote_alquimico": 10,
                      "frasco_piche": 2, "frasco_oleo": 2, "fogo_grego": 2,
                      "health_potion_concentrated": 3, "veneno_agonia_sufocante": 2,
                      "ensaio_sobre_a_cegueira": 1, "veneno_ardonia_negra": 1,
                      "bomba_flash": 4,
                  },
                  "veneno_rapido_level": 3,
                  "flash_reaction": "somente_quando_gilo_for_atacado",
                  "abilities": [
                      {"id": "disparo_duplo", "name": "Disparo Duplo", "uses": "ataques duplos com as duas bestas"},
                      {"id": "mira_perfeita", "name": "Mira Perfeita", "cooldown_rounds": 4},
                      {"id": "arremesso_rapido", "name": "Arremesso Rápido", "cooldown_rounds": 4},
                      {"id": "sangue_frio", "name": "Sangue Frio", "cooldown_rounds": 5},
                      {"id": "veneno_rapido_3", "name": "Veneno Rápido III",
                       "effect": "dois venenos diferentes por conjunto de 10 virotes"},
                  ],
              },
              "xp": 60, "boss": True, "ai_type": "agressivo", "ai_profile": "agressivo",
              "image": "gilo_dedos_sujos", "portrait": "gilo_dedos_sujos",
              "model3d": "assets/models3d/monstros/gilo_dedos_sujos.glb"})
    f["special_abilities"] = []
    f["monster_abilities"] = []
    f["attacks"] = [{"name": "Besta de Mão", "damage": "1d4", "damage_types": ["physical"],
                     "num_attacks": 1, "attack_attribute": "dex", "damage_attribute": "dex",
                     "apply_attribute_damage": True, "attribute_mod_base": 3,
                     "base_attack_bonus": 3, "atk_bonus": 6, "range": 4,
                     "on_hit": None, "on_hit_effect": None, "poison_dc": 10,
                     "extra_damage": None, "extra_damage_types": []},
                    {"name": "Besta de Mão (segunda)", "damage": "1d4", "damage_types": ["physical"],
                     "num_attacks": 1, "attack_attribute": "dex", "damage_attribute": "dex",
                     "apply_attribute_damage": True, "attribute_mod_base": 3,
                     "base_attack_bonus": 3, "atk_bonus": 6, "range": 4,
                     "on_hit": None, "on_hit_effect": None, "poison_dc": 10,
                     "extra_damage": None, "extra_damage_types": []}]
    f["loot_drops"] = [{"kind": "gold", "amount": 40, "chance": 100}]
    return f
