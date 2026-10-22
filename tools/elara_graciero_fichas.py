"""Fichas e item de Graciero (final de "O Resgate de Elara")."""
import copy
import json
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TIPO_ESCORPIAO = "escorpiao_gigante"
TIPO_LEONEL = "leonel"
ID_OLHO = "olho_de_arveluz"


def _base(tipo):
    with open(os.path.join(RAIZ, "monstros_personalizados.json"), encoding="utf-8") as f:
        for m in json.load(f):
            if m.get("type") == tipo:
                return copy.deepcopy(m)
    raise LookupError(f"ficha base `{tipo}` ausente em monstros_personalizados.json")


def ficha_escorpiao_gigante():
    f = _base("escorpiao_de_pedra_customizado")
    f.update({"type": TIPO_ESCORPIAO, "name": "Escorpião Gigante", "cr": 1, "base_hp": 16, "hp": 16,
              "ac": 14, "porte": "medio"})
    for a in f.get("attacks", []):
        a["damage"] = "1d8"
        a["atk_bonus"] = 5
    return f


def ficha_leonel():
    f = _base("soldado")
    f.update({"type": TIPO_LEONEL, "name": "Leonel", "emoji": "🎩", "tier": 3, "cr": 3, "base_hp": 55,
              "hp": 55, "ac": 15, "movement": 6, "equipment_enabled": False, "equipped_items": [],
              "equipment": [], "xp": 120, "boss": True, "image": "soldado", "portrait": "soldado"})
    f["attacks"] = [{"name": "Florete", "damage": "1d8", "damage_types": ["physical"], "num_attacks": 2,
                     "attack_attribute": "dex", "damage_attribute": "dex", "apply_attribute_damage": True,
                     "attribute_mod_base": 2, "base_attack_bonus": 0, "atk_bonus": 5, "range": None,
                     "on_hit": None, "on_hit_effect": None, "poison_dc": 10, "extra_damage": None,
                     "extra_damage_types": []}]
    f["loot_drops"] = [{"kind": "gold", "amount": 120, "chance": 100}]
    return f


def item_olho():
    """Relíquia de missão: não dá bônus, não vai à loja, aos baús nem ao loot."""
    return {"id": ID_OLHO, "name": "Olho de Arveluz", "emoji": "👁️", "item_type": "ring", "bonuses": [],
            "allowed_classes": [], "price": 0,
            "descricao": "Uma relíquia pesada do Templo de Alva e Luz. Está quente ao toque.",
            "disponibilidade": {"loja": False, "baus": False, "loot_monstro": False}}
