"""Fichas da rota do Olho (montanhas). O assassino é ficha personalizada; o Bardo da Caravana é uma variante NATIVA do
Bardo (`_variante_bardo_caravana` no server.py): precisa da IA, da Canção e do instrumento do Bardo, que uma ficha
personalizada não carrega."""
import elara_gilo_ficha as G

TIPO_ASSASSINO = "assassino_da_caravana"
TIPO_BARDO = "bardo_da_caravana"


def ficha_assassino():
    f = G.ficha_gilo()
    f.update({"type": TIPO_ASSASSINO, "name": "O Assassino da Serra", "emoji": "🗡️", "tier": 3, "cr": 3,
              "base_hp": 45, "hp": 45, "ac": 16, "movement": 7, "xp": 120, "boss": True,
              "image": "soldado", "portrait": "soldado"})
    f["loot_drops"] = [{"kind": "gold", "amount": 90, "chance": 100}]
    return f
