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
    f.update({"type": TIPO_ESCORPIAO, "name": "Escorpião Gigante", "tier": 1, "cr": 1.5,
              "base_hp": 17, "hp": 18, "natural_armor": 4, "ac": 15,
              "base_attack_bonus": 4, "porte": "medio",
              "model3d": "assets/models3d/monstros/escorpiao_gigante_preto.glb",
              "loot_table": {
                  "1-15": {"tipo": "item", "id": "veneno_escorpiao_aprimorado", "quantidade": 1},
                  "16-25": {"tipo": "item", "id": "veneno_escorpiao_aprimorado", "quantidade": 2},
                  "26-30": {"tipo": "item", "id": "veneno_escorpiao_aprimorado", "quantidade": 3},
                  "31-100": None,
              }})
    for a in f.get("attacks", []):
        a["base_attack_bonus"] = 4
        a["atk_bonus"] = 4
        if a.get("name") == "Pinça":
            a["damage"] = "2d4"
        elif a.get("name") == "Ferrão":
            a["damage"] = "1d6"
            a["poison_dc"] = 14
    for ability in f.get("special_abilities", []):
        if ability.get("id") == "envenenar":
            ability["poison_dc"] = 14
    for ability in f.get("monster_abilities", []):
        if ability.get("id") == "envenenar":
            ability["poison_dc"] = 14
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
    """Relíquia de missão: sem bônus, fora da loja e do loot. `baus` só o põe no catálogo (a conversa que o concede
    só acha itens de lá); baús aleatórios não sorteiam por isso."""
    return {"id": ID_OLHO, "name": "Olho de Arveluz", "emoji": "👁️", "item_type": "ring", "bonuses": [],
            "allowed_classes": [], "price": 0,
            "descricao": "Uma relíquia pesada do Templo de Alva e Luz. Está quente ao toque.",
            "disponibilidade": {"loja": False, "baus": True, "loot_monstro": False}}
