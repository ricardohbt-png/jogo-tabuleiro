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
    """Bardo da caravana: Canção Heroica e Provocação (habilidades de herói reaproveitadas) e, ao nascer,
    arma e instrumento sorteados (`MONSTRO_EQUIP_ALEATORIO["bardo_da_caravana"]` em server.py: o validador
    de ficha descarta campos desconhecidos, então as chances moram lá). `equipment_enabled` fica ligado
    para a arma sorteada entrar no ataque; sem sorteio ele luta com o golpe básico da ficha."""
    f = GF._base("soldado")
    f.update({"type": TIPO_BARDO, "name": "Bardo da Caravana", "emoji": "🎻", "tier": 2, "cr": 2,
              "base_hp": 30, "hp": 30, "ac": 14, "movement": 6, "equipment_enabled": True,
              "equipped_items": [], "equipment": [], "xp": 70, "boss": False,
              "image": "soldado", "portrait": "soldado"})
    # Substitui a Mira Certeira herdada do soldado: o bardo canta e provoca, não mira.
    f["monster_abilities"] = [
        {"id": "hero_bard_cancao_heroica", "uses_per_day": 1, "cooldown_turns": 0, "duration_rounds": 4},
        {"id": "hero_bard_provocacao", "uses_per_day": 2, "cooldown_turns": 3},
    ]
    f.pop("special_abilities", None)
    f["loot_drops"] = [{"kind": "gold", "amount": 40, "chance": 100}]
    return f
