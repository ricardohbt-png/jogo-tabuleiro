"""Fichas da rota do Olho (montanhas): o assassino e o bardo da caravana."""
import elara_gilo_ficha as G
import elara_graciero_fichas as GF

TIPO_ASSASSINO = "assassino_da_caravana"
TIPO_BARDO = "bardo_da_caravana"


def ficha_assassino():
    f = G.ficha_gilo()
    f.update({"type": TIPO_ASSASSINO, "name": "O Assassino da Serra", "emoji": "🗡️", "tier": 3, "cr": 3,
              "base_hp": 45, "hp": 45, "ac": 16, "movement": 7, "xp": 120, "boss": True,
              "image": "soldado", "portrait": "soldado"})
    f["loot_drops"] = [{"kind": "gold", "amount": 90, "chance": 100}]
    return f


def ficha_bardo_agente():
    f = GF._base("soldado")
    f.update({"type": TIPO_BARDO, "name": "Bardo da Caravana", "emoji": "🎻", "tier": 2, "cr": 2,
              "base_hp": 30, "hp": 30, "ac": 14, "movement": 6, "equipment_enabled": False,
              "equipped_items": [], "equipment": [], "xp": 70, "boss": False,
              "image": "soldado", "portrait": "soldado"})
    f["loot_drops"] = [{"kind": "gold", "amount": 40, "chance": 100}]
    return f
