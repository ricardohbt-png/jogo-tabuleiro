"""
Legends for Hire - WebSocket Game Server
Multiplayer RPG board game (Hero Quest / D&D style)
Up to 6 players + GM (computer)

Requirements: pip install websockets
Run: python server.py
"""

import asyncio
import websockets
import json
import random
import string
import sys
from copy import deepcopy

# ─── MAP CONSTANTS ────────────────────────────────────────────────────────────

WALL  = 0
FLOOR = 1
DOOR  = 2
MAP_W = 30
MAP_H = 30

# ─── D20 HELPERS ──────────────────────────────────────────────────────────────

def mod(score): return (score - 10) // 2

def get_bonus_constituicao(constituicao):
    """Bônus de HP/Fortitude baseado na Constituição (tabela D20 expandida 0–25)."""
    tabela = {
         0: -5,  1: -5,  2: -4,  3: -4,  4: -3,  5: -3,
         6: -2,  7: -2,  8: -1,  9: -1, 10:  0, 11:  0,
        12: +1, 13: +1, 14: +2, 15: +2, 16: +3, 17: +3,
        18: +4, 19: +4, 20: +5, 21: +5, 22: +6, 23: +6,
        24: +7, 25: +7,
    }
    valor_seguro = max(0, min(25, int(constituicao)))
    return tabela[valor_seguro]

def roll_dice(die_str):
    """Roll dice from string like '1d8' or '2d6'."""
    n, d = die_str.split('d')
    return sum(random.randint(1, int(d)) for _ in range(int(n) if n else 1))

def d20_attack(atk_bonus, target_ac):
    """Roll 1d20+atk_bonus vs target_ac. Returns (hit, roll, total, crit)."""
    roll = random.randint(1, 20)
    total = roll + atk_bonus
    crit = (roll == 20)
    return (crit or total >= target_ac), roll, total, crit

# ─── WEAPONS ──────────────────────────────────────────────────────────────────

WEAPONS = {
    # ── Corpo a Corpo ─────────────────────────────────────────────────────────
    "unarmed":       {"id": "unarmed",       "name": "Desarmado",            "die": None,   "stat": "str_"},
    "dagger":        {"id": "dagger",        "name": "Adaga",                "die": "1d4",  "stat": "str_"},
    "bordao":        {"id": "bordao",        "name": "Bordão",               "die": "1d6",  "stat": "str_"},
    "lanca":         {"id": "lanca",         "name": "Lança",                "die": "1d6",  "stat": "str_", "range": 2},
    "maca":          {"id": "maca",          "name": "Maça",                 "die": "1d6",  "stat": "str_"},
    "chicote":       {"id": "chicote",       "name": "Chicote",              "die": "1d4",  "stat": "dex",  "range": 2},
    "staff":         {"id": "staff",         "name": "Cajado Arcano",        "die": "1d6",  "stat": "str_"},
    "shortsword":    {"id": "shortsword",    "name": "Espada Curta",         "die": "1d6",  "stat": "str_"},
    "longsword":     {"id": "longsword",     "name": "Espada Longa",         "die": "1d8",  "stat": "str_"},
    "warhammer":     {"id": "warhammer",     "name": "Martelo de Guerra",    "die": "1d8",  "stat": "str_"},
    "mangual":       {"id": "mangual",       "name": "Mangual",              "die": "1d8",  "stat": "str_"},
    "machado_duplo": {"id": "machado_duplo", "name": "Machado Duplo",        "die": "1d8",  "stat": "str_"},
    "bastsword":     {"id": "bastsword",     "name": "Espada Bastarda",      "die": "1d10", "stat": "str_"},
    "alabarda":      {"id": "alabarda",      "name": "Alabarda",             "die": "1d10", "stat": "str_", "range": 2},
    "espada2m":      {"id": "espada2m",      "name": "Espada de 2 Mãos",    "die": "2d6",  "stat": "str_"},
    # ── À Distância ───────────────────────────────────────────────────────────
    "arco_curto":    {"id": "arco_curto",    "name": "Arco Curto",           "die": "1d6",  "stat": "dex",  "range": 8},
    "hand_crossbow": {"id": "hand_crossbow", "name": "Besta de Mão",         "die": "1d4",  "stat": "dex",  "range": 6},
    "longbow":       {"id": "longbow",       "name": "Arco Longo",           "die": "1d8",  "stat": "dex",  "range": 12},
    "besta":         {"id": "besta",         "name": "Besta",                "die": "1d8",  "stat": "dex",  "range": 10},
}

# ─── CHARACTER CLASSES ────────────────────────────────────────────────────────

CLASSES = {
    # ── D20 nível 1 — cada classe com atributos temáticos (16/14/12/10)
    # BAB: guerreiro/richard/arqueiro = +1 (cheio), outros = +0 (médio/baixo)
    # Saves: Bom = +2 base, Ruim = +0 base  |  atk_bonus = BAB + mod(STR)
    "warrior": {
        "name": "Guerreiro", "emoji": "⚔️", "color": "#e74c3c",
        "hp": 14, "mp": 8, "spd": 6, "start_gold": 20,
        "str_": 18, "dex": 10, "con_": 14, "int_": 8,
        "ac_base": 12, "weapon": "shortsword", "atk_bonus": 5,  # BAB 1 + FOR mod(18)=+4; ac_base 12=10+couro+2
        "saves_base": {"fort": 2, "ref": 0, "will": 0},          # Fort bom, Ref/Von ruins
        "desc": "Tanque resistente com golpes poderosos",
        "skills": [
            {"id": "heavy_blow",  "name": "Golpe Pesado",   "mp": 3, "desc": "2× dano de arma em 1 inimigo",   "target": "enemy"},
            {"id": "taunt",       "name": "Provocar",       "mp": 4, "desc": "Força monstros a atacarem você", "target": "self"},
            {"id": "shield_bash", "name": "Bash de Escudo", "mp": 2, "desc": "+3 CA por 1 turno",              "target": "self"},
        ],
    },
    "mage": {
        "name": "Pedro, o Tímido", "emoji": "🔮", "color": "#9b59b6",
        "hp": 7, "mp": 22, "spd": 5, "start_gold": 20,
        "str_": 8, "dex": 12, "con_": 12, "int_": 18,
        "ac_base": 10, "weapon": "dagger", "atk_bonus": -1,  # BAB 0 + FOR mod(8)=-1; ac_base 10=10+manto+0
        "saves_base": {"fort": 0, "ref": 0, "will": 2},       # Von bom, Fort/Ref ruins
        "desc": "Devastador com magia, mas frágil",
        "skills": [
            {"id": "fireball",     "name": "Bola de Fogo",  "mp": 5, "desc": "4d6 fogo todos inimigos (CD15)",  "target": "all_enemies"},
            {"id": "ice_lance",    "name": "Lança de Gelo", "mp": 3, "desc": "3d6+FOR dano em 1 inimigo",       "target": "enemy"},
            {"id": "magic_shield", "name": "Escudo Mágico", "mp": 4, "desc": "+4 CA por 1 turno",               "target": "self"},
        ],
    },
    "rogue": {
        "name": "Luccas, o Astuto", "emoji": "🗡️", "color": "#2ecc71",
        "hp": 9, "mp": 13, "spd": 7, "start_gold": 20,
        "str_": 10, "dex": 18, "con_": 12, "int_": 10,
        "ac_base": 14, "weapon": "dagger", "atk_bonus": 4,   # BAB 0 + DES mod(18)=+4; ac_base 14=10+couro+DES
        "saves_base": {"fort": 0, "ref": 2, "will": 0},       # Ref bom, Fort/Von ruins
        "desc": "Veloz, detecta armadilhas, golpe furtivo",
        "skills": [
            {"id": "backstab",    "name": "Ataque Furtivo",    "mp": 4, "desc": "Arma+2d6 dano furtivo",        "target": "enemy"},
            {"id": "detect_trap", "name": "Detectar Armadilha","mp": 2, "desc": "Revela armadilhas próximas",    "target": "self"},
            {"id": "smoke_bomb",  "name": "Bomba de Fumaça",   "mp": 3, "desc": "Inimigos erram próximo ataque", "target": "self"},
        ],
    },
    "cleric": {
        "name": "Frade Lewis", "emoji": "✨", "color": "#f39c12",
        "hp": 10, "mp": 20, "spd": 5, "start_gold": 20,
        "str_": 10, "dex": 10, "con_": 14, "int_": 16,
        "ac_base": 11, "weapon": "bordao", "atk_bonus": 0,   # BAB 0 + FOR mod(10)=0; ac_base 11=10+couro+1
        "saves_base": {"fort": 2, "ref": 0, "will": 2},       # Fort e Von bons, Ref ruim
        "desc": "Cura aliados e causa dano sagrado",
        "skills": [
            {"id": "heal",       "name": "Curar",        "mp": 5, "desc": "Restaura 2d6+2 HP de 1 aliado",      "target": "ally"},
            {"id": "holy_light", "name": "Luz Sagrada",  "mp": 6, "desc": "2d6 sagrado em todos inimigos",       "target": "all_enemies"},
            {"id": "bless",      "name": "Benção",        "mp": 3, "desc": "+2 Bônus de Ataque a todos aliados",  "target": "all_allies"},
        ],
    },
    "bard": {
        "name": "Henrique, o Bardo", "emoji": "🎶", "color": "#9b7fd4",
        "hp": 9, "mp": 18, "spd": 6, "start_gold": 20,
        "str_": 10, "dex": 16, "con_": 12, "int_": 12,
        "ac_base": 12, "weapon": "shortsword", "atk_bonus": 3,   # BAB 0 + DES mod(16)=+3
        "saves_base": {"fort": 0, "ref": 2, "will": 2},           # Ref e Von bons, Fort ruim
        "desc": "Músico mágico que inspira aliados e confunde inimigos",
        "skills": [
            {"id": "bard_inspire",   "name": "Inspiração",         "mp": 3, "desc": "+2 Ataque a todos aliados por 1 turno",    "target": "all_allies"},
            {"id": "bard_confusion", "name": "Canção da Confusão", "mp": 5, "desc": "Todos inimigos erram próximo ataque",       "target": "all_enemies"},
            {"id": "bard_lullaby",   "name": "Balada Curativa",    "mp": 4, "desc": "Cura 1d6+2 HP em todos aliados",            "target": "all_allies"},
        ],
    },
    "paladin": {
        "name": "Richard, o Cavaleiro", "emoji": "🛡️", "color": "#3498db",
        "hp": 12, "mp": 16, "spd": 6, "start_gold": 20,
        "str_": 16, "dex": 10, "con_": 14, "int_": 10,
        "ac_base": 14, "weapon": "shortsword", "atk_bonus": 4,  # BAB 1 + FOR mod(16)=+3; ac_base 14=10+cota+0
        "saves_base": {"fort": 2, "ref": 0, "will": 2},          # Fort e Von bons, Ref ruim
        "desc": "Aço e honra forjados na mesma bigorna. Não conhece recuo.",
        "skills": [
            {"id": "smite",        "name": "Golpe Divino",  "mp": 4, "desc": "Arma+1d6 sagrado em 1 inimigo",     "target": "enemy"},
            {"id": "divine_shield","name": "Escudo Divino", "mp": 5, "desc": "1 aliado imune a dano por 1 turno",  "target": "ally"},
            {"id": "holy_aura",    "name": "Aura Sagrada",  "mp": 6, "desc": "+2 CA a todos aliados por 2 turnos", "target": "all_allies"},
        ],
    },
}

MONSTER_DEFS = [
    {"type": "goblin",    "name": "Goblin",         "emoji": "👺", "hp": 8,  "ac": 12, "atk_bonus": 2,  "damage": "1d4", "xp": 10,  "gold": 5,   "tier": 1},
    {"type": "skeleton",  "name": "Esqueleto",      "emoji": "💀", "hp": 10, "ac": 13, "atk_bonus": 3,  "damage": "1d6", "xp": 15,  "gold": 8,   "tier": 1, "undead": True},
    {"type": "orc",       "name": "Orc",            "emoji": "👹", "hp": 16, "ac": 14, "atk_bonus": 5,  "damage": "1d8", "xp": 25,  "gold": 12,  "tier": 2},
    {"type": "dark_mage", "name": "Mago das Trevas","emoji": "🧟", "hp": 12, "ac": 12, "atk_bonus": 4,  "damage": "1d6", "xp": 30,  "gold": 20,  "tier": 2},
    {"type": "troll",     "name": "Troll",          "emoji": "🗿", "hp": 22, "ac": 16, "atk_bonus": 7,  "damage": "1d10","xp": 40,  "gold": 25,  "tier": 3},
    {"type": "dragon",    "name": "Dragão Ancião",  "emoji": "🐉", "hp": 60, "ac": 20, "atk_bonus": 12, "damage": "2d8", "xp": 200, "gold": 100, "tier": 4, "boss": True},
]

CHEST_ITEMS = [
    # ── Consumíveis (vão para a mochila, max 6 slots) ──
    {"id": "health_potion", "name": "Poção de Vida",     "emoji": "🧪", "item_slot": "bag",       "effect": "heal",      "value": 10},
    {"id": "mana_potion",   "name": "Poção de Mana",     "emoji": "💙", "item_slot": "bag",       "effect": "mana",      "value": 8},
    {"id": "elixir",        "name": "Elixir da Força",   "emoji": "⚗️", "item_slot": "bag",       "effect": "atk_bonus", "value": 3},
    {"id": "antidote",      "name": "Antídoto",          "emoji": "💚", "item_slot": "bag",       "effect": "heal",      "value": 6},
    # ── Armas (slot weapon) ──
    {"id": "sword",         "name": "Espada de Ferro",   "emoji": "⚔️", "item_slot": "weapon",    "effect": "atk",       "value": 2},
    {"id": "magic_sword",   "name": "Espada Mágica",     "emoji": "🗡️", "item_slot": "weapon",    "effect": "atk",       "value": 4},
    {"id": "bow",           "name": "Arco Élfico",       "emoji": "🏹", "item_slot": "weapon",    "effect": "atk",       "value": 3},
    {"id": "staff",         "name": "Cajado das Runas",  "emoji": "🪄", "item_slot": "weapon",    "effect": "atk",       "value": 3},
    # ── Armaduras (slot armor) ──
    {"id": "shield",        "name": "Escudo de Madeira", "emoji": "🛡️", "item_slot": "armor",     "effect": "def_",      "value": 2},
    {"id": "chainmail",     "name": "Cota de Malha",     "emoji": "🪖", "item_slot": "armor",     "effect": "def_",      "value": 3},
    {"id": "leather",       "name": "Couro Reforçado",   "emoji": "🥋", "item_slot": "armor",     "effect": "def_",      "value": 1},
    # ── Acessórios (slots acc1 / acc2) ──
    {"id": "amulet",        "name": "Amuleto Sagrado",   "emoji": "📿", "item_slot": "accessory", "effect": "maxhp",     "value": 5},
    {"id": "boots",         "name": "Botas Velozes",     "emoji": "👢", "item_slot": "accessory", "effect": "spd",       "value": 1},
    {"id": "ring",          "name": "Anel de Força",     "emoji": "💍", "item_slot": "accessory", "effect": "atk",       "value": 1},
    {"id": "cloak",         "name": "Manto das Sombras", "emoji": "🧣", "item_slot": "accessory", "effect": "def_",      "value": 1},
]

# ─── SHOP CATALOGS ────────────────────────────────────────────────────────────

SHOP_WEAPONS = [
    # ─── Leves (1d4) ───────────────────────────────────────────────────────────
    {"id": "dagger",        "name": "Adaga",              "emoji": "🗡️",  "die": "1d4",  "stat": "str_", "price": 5},
    {"id": "chicote",       "name": "Chicote",            "emoji": "🪢",  "die": "1d4",  "stat": "dex",  "price": 8,  "range": 2},
    {"id": "hand_crossbow", "name": "Besta de Mão",       "emoji": "🏹",  "die": "1d4",  "stat": "dex",  "price": 10, "range": 6},
    # ─── Médias (1d6) ──────────────────────────────────────────────────────────
    {"id": "bordao",        "name": "Bordão",             "emoji": "🪄",  "die": "1d6",  "stat": "str_", "price": 8},
    {"id": "staff",         "name": "Cajado Arcano",      "emoji": "🪄",  "die": "1d6",  "stat": "str_", "price": 10},
    {"id": "maca",          "name": "Maça",               "emoji": "🔨",  "die": "1d6",  "stat": "str_", "price": 10},
    {"id": "lanca",         "name": "Lança",              "emoji": "🔱",  "die": "1d6",  "stat": "str_", "price": 10, "range": 2},
    {"id": "shortsword",    "name": "Espada Curta",       "emoji": "⚔️",  "die": "1d6",  "stat": "str_", "price": 12},
    {"id": "arco_curto",    "name": "Arco Curto",         "emoji": "🏹",  "die": "1d6",  "stat": "dex",  "price": 12, "range": 8},
    # ─── Pesadas (1d8) ─────────────────────────────────────────────────────────
    {"id": "longsword",     "name": "Espada Longa",       "emoji": "⚔️",  "die": "1d8",  "stat": "str_", "price": 16},
    {"id": "longbow",       "name": "Arco Longo",         "emoji": "🏹",  "die": "1d8",  "stat": "dex",  "price": 16, "range": 12},
    {"id": "warhammer",     "name": "Martelo de Guerra",  "emoji": "🔨",  "die": "1d8",  "stat": "str_", "price": 18},
    {"id": "besta",         "name": "Besta",              "emoji": "🏹",  "die": "1d8",  "stat": "dex",  "price": 18, "range": 10},
    {"id": "mangual",       "name": "Mangual",            "emoji": "⚔️",  "die": "1d8",  "stat": "str_", "price": 20},
    {"id": "machado_duplo", "name": "Machado Duplo",      "emoji": "🪓",  "die": "1d8",  "stat": "str_", "price": 22},
    # ─── Muito Pesadas (1d10 / 2d6) ────────────────────────────────────────────
    {"id": "bastsword",     "name": "Espada Bastarda",    "emoji": "⚔️",  "die": "1d10", "stat": "str_", "price": 25},
    {"id": "alabarda",      "name": "Alabarda",           "emoji": "🪓",  "die": "1d10", "stat": "str_", "price": 28, "range": 2},
    {"id": "espada2m",      "name": "Espada de 2 Mãos",  "emoji": "⚔️",  "die": "2d6",  "stat": "str_", "price": 35},
]

SHOP_ARMORS = [
    # ── Proteções / Escudos (slot acessório — somam com armadura) ──────────────
    {"id": "escudo_p",     "name": "Escudo Pequeno",     "emoji": "🛡️", "ac_bonus": 1, "price": 12, "kind": "shield"},
    {"id": "escudo_g",     "name": "Escudo Grande",      "emoji": "🛡️", "ac_bonus": 2, "price": 20, "kind": "shield"},
    # ── Armaduras (slot armadura) ─────────────────────────────────────────────
    {"id": "cloak",        "name": "Manto",              "emoji": "🧣",  "ac_bonus": 0, "price": 5,  "kind": "armor"},
    {"id": "leather",      "name": "Armadura de Couro",  "emoji": "🥋",  "ac_bonus": 2, "price": 10, "kind": "armor"},
    {"id": "chainmail",    "name": "Cota de Malha",      "emoji": "🪖",  "ac_bonus": 4, "price": 20, "kind": "armor"},
    {"id": "bronze_armor", "name": "Armadura de Bronze", "emoji": "🪖",  "ac_bonus": 5, "price": 30, "kind": "armor"},
    {"id": "plate",        "name": "Armadura de Placas", "emoji": "🛡️", "ac_bonus": 6, "price": 38, "kind": "armor"},
    {"id": "fullplate",    "name": "Armadura Completa",  "emoji": "🛡️", "ac_bonus": 8, "price": 55, "kind": "armor"},
]

SHOP_MERCHANT = [
    {"id": "health_potion", "name": "Poção de Cura",    "emoji": "🧪",  "price": 8,  "item_slot": "bag",   "effect": "heal",      "value": 10},
    {"id": "mana_potion",   "name": "Poção de Mana",    "emoji": "💙",  "price": 8,  "item_slot": "bag",   "effect": "mana",      "value": 8},
    {"id": "elixir",        "name": "Elixir da Força",  "emoji": "⚗️", "price": 12, "item_slot": "bag",   "effect": "atk_bonus", "value": 3},
    {"id": "antidote",      "name": "Antídoto",          "emoji": "💚",  "price": 5,  "item_slot": "bag",   "effect": "heal",      "value": 6},
    # ── Anéis (slots ring1 / ring2) ──
    {"id": "ring_str",      "name": "Anel de Força",     "emoji": "💍",  "price": 12, "item_slot": "ring",  "effect": "atk",       "value": 1},
    {"id": "ring_vita",     "name": "Anel da Vitalidade","emoji": "💍",  "price": 15, "item_slot": "ring",  "effect": "maxhp",     "value": 5},
    # ── Cabeça (slot head) ──
    {"id": "helm_iron",     "name": "Elmo de Ferro",     "emoji": "⛑️", "price": 14, "item_slot": "head",  "effect": "def_",      "value": 1},
    {"id": "circlet",       "name": "Tiara Arcana",      "emoji": "👑",  "price": 16, "item_slot": "head",  "effect": "maxhp",     "value": 4},
    # ── Itens ativos (slots item1 / item2) ──
    {"id": "boots",         "name": "Botas Velozes",     "emoji": "👢",  "price": 10, "item_slot": "item",  "effect": "spd",       "value": 1},
    {"id": "amulet",        "name": "Amuleto da Sorte",  "emoji": "📿",  "price": 15, "item_slot": "item",  "effect": "maxhp",     "value": 5},
    {"id": "backpack",      "name": "Mochila de Couro",  "emoji": "🎒",  "price": 18, "item_slot": "item",  "effect": "bagslots",  "value": 3},
]

SHOP_TEMPLE = [
    {"id": "full_heal", "name": "Cura Completa",  "emoji": "💖",  "price": 15, "effect": "full_heal"},
    {"id": "full_mana", "name": "Restaurar Mana", "emoji": "🔷",  "price": 10, "effect": "full_mana"},
    {"id": "bless",     "name": "Bênção Divina",  "emoji": "✨",  "price": 12, "effect": "bless",    "value": 2},
    {"id": "cleanse",   "name": "Purificação",    "emoji": "🕊️", "price": 8,  "effect": "cleanse"},
]

SHOP_TAVERN = [
    {"id": "meal",      "name": "Refeição",         "emoji": "🍖",  "price": 5,  "effect": "heal",        "value": 8},
    {"id": "fine_meal", "name": "Banquete",          "emoji": "🍗",  "price": 10, "effect": "heal",        "value": 15},
    {"id": "ale",       "name": "Caneca de Cerveja", "emoji": "🍺",  "price": 3,  "effect": "temp_atk",    "value": 1},
    {"id": "rest",      "name": "Descanso Completo", "emoji": "🛏️", "price": 12, "effect": "full_heal_mp"},
]

# ─── GM NARRATION ─────────────────────────────────────────────────────────────

GM = {
    "intro": [
        "Aventureiros... A Fortaleza das Trevas vos aguarda. Monstros, armadilhas e segredos sombrios residem em seus corredores. Apenas os mais corajosos sobreviverão. Que a sorte os acompanhe.",
        "A lenda fala de um dragão ancião que guarda tesouros imensuráveis nas profundezas. Inúmeros heróis tentaram — nenhum voltou. Serão vocês os primeiros a mudar esse destino?",
        "Uma escuridão antiga tomou conta da masmorra. Os aldeões dependem de vocês. Entre com cautela... o mal os observa.",
    ],
    "room_empty":   ["A câmara parece vazia... por enquanto.", "Silêncio pesado. Apenas poeira e sombras.", "Nada de óbvio aqui. Mas fiquem alertas."],
    "room_monster": ["Cuidado! Criaturas emergem das sombras!", "Um rugido ecoa pelas paredes. Inimigos à vista!", "Olhos brilham na escuridão. Preparem-se para lutar!"],
    "room_chest":   ["Um baú antigo repousa no centro. Será que há tesouros?", "Um cofre ornamentado que não era aberto há séculos...", "Entre os destroços, um baú reluzente!"],
    "room_trap":    ["O chão soa estranho. Pisem com muito cuidado...", "Marcas nas paredes revelam combates passados. Alguém já sofreu aqui.", "Algo parece errado nesta sala..."],
    "room_boss":    ["Um frio sobrenatural toma conta do ambiente. Uma presença maligna aguarda...", "Rugidos profundos ecoam. O senhor das trevas os aguarda!", "A escuridão se adensa. Este é o desafio final. Tudo ou nada!"],
    "combat_start": ["O combate começa! Mostrem do que são capazes!", "Espadas em punho! O inimigo não dará trégua!", "Batalha declarada! Lutem com tudo!"],
    "monster_moves":["As criaturas avançam nas sombras...", "Passos pesados ecoam pelos corredores. Os monstros se aproximam.", "Os inimigos avançam! Estejam preparados!"],
    "victory":      ["VITÓRIA! Os heróis derrotaram o dragão e salvaram o reino! Sua lenda será contada por gerações!", "O mal foi banido! O reino está salvo graças à coragem de todos!", "GLÓRIA AOS AVENTUREIROS! A escuridão recuou!"],
    "defeat":       ["A escuridão venceu... A masmorra permanece perigosa.", "O mal triunfou desta vez. Mas as lendas dos heróis caídos viverão eternamente...", "A masmorra reivindica mais vítimas. Que encontrem paz além..."],
}

def gm(key): return random.choice(GM[key])

# ─── MAP GENERATION ───────────────────────────────────────────────────────────

def generate_dungeon():
    """Generate a dungeon map with rooms connected by corridors."""
    tiles = [[WALL] * MAP_W for _ in range(MAP_H)]
    rooms = []

    # Try to place rooms
    for _ in range(60):
        w = random.randint(4, 8)
        h = random.randint(4, 8)
        x = random.randint(1, MAP_W - w - 1)
        y = random.randint(1, MAP_H - h - 1)
        # Check overlap with buffer
        overlap = any(
            rx - 1 <= x + w and rx + rw + 1 >= x and
            ry - 1 <= y + h and ry + rh + 1 >= y
            for rx, ry, rw, rh in rooms
        )
        if not overlap:
            rooms.append((x, y, w, h))
            if len(rooms) >= 10:
                break

    # Carve rooms
    for x, y, w, h in rooms:
        for ry in range(y, y + h):
            for rx in range(x, x + w):
                tiles[ry][rx] = FLOOR

    # Connect rooms with L-shaped corridors
    for i in range(1, len(rooms)):
        ax, ay = rooms[i-1][0] + rooms[i-1][2]//2, rooms[i-1][1] + rooms[i-1][3]//2
        bx, by = rooms[i][0] + rooms[i][2]//2,     rooms[i][1] + rooms[i][3]//2
        # Horizontal then vertical
        for rx in range(min(ax, bx), max(ax, bx) + 1):
            tiles[ay][rx] = FLOOR
        for ry in range(min(ay, by), max(ay, by) + 1):
            tiles[ry][bx] = FLOOR

    # Assign room roles
    random.shuffle(rooms)
    room_data = []
    roles = (
        ["entrance"] +
        ["monster"] * 3 +
        ["chest"] * 2 +
        ["trap"] * 1 +
        ["empty"] * max(0, len(rooms) - 8) +
        ["boss"]
    )
    for i, (x, y, w, h) in enumerate(rooms):
        role = roles[i] if i < len(roles) else "empty"
        cx, cy = x + w//2, y + h//2
        room_data.append({
            "id": i, "x": x, "y": y, "w": w, "h": h,
            "cx": cx, "cy": cy, "role": role,
            "cleared": role in ("entrance", "empty"),
            "looted": False,
        })

    return tiles, room_data

def room_contains(room, tx, ty):
    return room["x"] <= tx < room["x"] + room["w"] and room["y"] <= ty < room["y"] + room["h"]

def player_room(rooms, px, py):
    for r in rooms:
        if room_contains(r, px, py):
            return r
    return None

# ─── GAME STATE ───────────────────────────────────────────────────────────────

_id_counter = 0
def new_id():
    global _id_counter
    _id_counter += 1
    return f"id_{_id_counter}"

# ─── STARTING ARMOR ITEMS ────────────────────────────────────────────────────
# value=0 because the AC bonus is already baked into ac_base; these items are
# purely for display in the character sheet gear slots.
_STARTING_ARMOR = {
    "warrior": {"id": "leather", "name": "Armadura de Couro", "emoji": "🥋",
                "item_slot": "armor", "effect": "def_", "value": 0},
    "mage":    {"id": "cloak",   "name": "Manto",             "emoji": "🧣",
                "item_slot": "armor", "effect": "def_", "value": 0},
    "rogue":   {"id": "leather", "name": "Armadura de Couro", "emoji": "🥋",
                "item_slot": "armor", "effect": "def_", "value": 0},
    "cleric":  {"id": "leather", "name": "Armadura de Couro", "emoji": "🥋",
                "item_slot": "armor", "effect": "def_", "value": 0},
    "bard":    {"id": "cloak",   "name": "Manto",             "emoji": "🧣",
                "item_slot": "armor", "effect": "def_", "value": 0},
    "paladin": {"id": "chainmail","name": "Cota de Malha",    "emoji": "🪖",
                "item_slot": "armor", "effect": "def_", "value": 0},
}

_WEAPON_EMOJI = {
    "unarmed": "✊", "dagger": "🗡️", "bordao": "🪄", "staff": "🪄",
    "lanca": "🔱", "chicote": "🪢", "maca": "🔨", "warhammer": "🔨",
    "shortsword": "⚔️", "longsword": "⚔️", "bastsword": "⚔️",
    "mangual": "⚔️", "machado_duplo": "🪓", "alabarda": "🪓",
    "espada2m": "⚔️", "arco_curto": "🏹", "longbow": "🏹",
    "hand_crossbow": "🏹", "besta": "🏹",
}

# Slots de equipamento que NÃO são a armadura do corpo mas podem dar +CA
# (escudo na mão esquerda, elmo, anéis, itens ativos).
GEAR_BONUS_SLOTS = ("off_hand", "head", "ring1", "ring2", "item1", "item2")
# Todos os 8 slots de equipamento, na ordem de exibição.
GEAR_SLOTS = ("weapon", "off_hand", "armor", "head", "ring1", "ring2", "item1", "item2")

def _recalculate_ac(p):
    """Recalcula CA a partir da armadura do corpo + bônus de def_ dos demais slots."""
    armor = p["gear"].get("armor")
    armor_val = armor.get("value", 0) if armor else 0
    bonus = 0
    for slot in GEAR_BONUS_SLOTS:
        g = p["gear"].get(slot)
        if g and g.get("effect") == "def_":
            bonus += g.get("value", 0)
    p["ac_base"] = 10 + mod(p["dex"]) + armor_val
    p["ac"]      = p["ac_base"] + bonus

def make_player(pid, name, cls_id, slot):
    cls = CLASSES[cls_id]
    w_id = cls["weapon"]
    weapon = {**WEAPONS[w_id]}
    s, d, c, i_ = cls["str_"], cls["dex"], cls["con_"], cls["int_"]
    sb = cls["saves_base"]
    # AC = armor_base (includes armor bonus) + DEX modifier
    ac_start = cls["ac_base"] + mod(d)
    level_bonus = 1  # +1 per level to attacks and saves; starts at +1 (level 1)

    # HP final já está em cls["hp"] (base + bônus CON calculados nas fichas).
    # con_bonus é mantido apenas para o save de Fortitude.
    con_bonus = get_bonus_constituicao(c)
    hp_total = cls["hp"]   # valor final — NÃO somar con_bonus aqui (já embutido)

    # Starting gear items (display only — stats already baked into ac_start / weapon dict)
    starting_weapon_item = {
        "id": w_id, "name": weapon["name"],
        "emoji": _WEAPON_EMOJI.get(w_id, "⚔️"),
        "item_slot": "weapon", "effect": "atk", "value": 0,
    }
    starting_armor_item = deepcopy(_STARTING_ARMOR.get(cls_id))

    return {
        "id": pid, "name": name, "class_id": cls_id,
        "class_name": cls["name"], "emoji": cls["emoji"], "color": cls["color"],
        "hp": hp_total, "max_hp": hp_total,
        "mp": cls["mp"], "max_mp": cls["mp"],
        # D20 ability scores
        "str_": s, "dex": d, "con_": c, "int_": i_,
        # Combat stats — AC = armor_base + DEX mod
        "ac": ac_start,
        "ac_base": ac_start,          # stored so gear deltas work
        "atk_bonus": cls["atk_bonus"] + level_bonus,
        "base_atk_bonus": cls["atk_bonus"] + level_bonus,
        "weapon": weapon,
        # Saving throws = class base + ability modifier + level bonus
        # Fortitude usa get_bonus_constituicao (tabela explícita 0–25)
        "fort": sb["fort"] + con_bonus + level_bonus,
        "ref_": sb["ref"]  + mod(d) + level_bonus,
        "will": sb["will"] + mod(i_) + level_bonus,
        "level_bonus": level_bonus,
        "spd": cls["spd"],
        "xp": 0, "level": 1,
        "gold": cls.get("start_gold", 20),
        "bag": [],
        "bag_size": 6,            # inventário base (expansível por mochilas)
        "gear": {
            "weapon":   starting_weapon_item,  # mão direita (arma principal)
            "off_hand": None,                  # mão esquerda: arma 2ª / escudo
            "armor":    starting_armor_item,   # corpo
            "head":     None,                  # elmo / tiara / capuz
            "ring1":    None,                  # anel
            "ring2":    None,                  # anel
            "item1":    None,                  # item ativo (mochila/luvas/cinto)
            "item2":    None,                  # item ativo
        },
        "status": [],
        "alive": True,
        "pos": [0, 0],
        "moves_left": cls["spd"],
        "action_done": False,
        "slot": slot,
        "skills": cls["skills"],
    }

def make_monster(mdef, room):
    m = deepcopy(mdef)
    m["id"] = new_id()
    m["max_hp"] = m["hp"]
    m["pos"] = [room["cx"], room["cy"]]
    m["room_id"] = room["id"]
    return m

def spawn_monsters_for_room(room, player_count):
    tier = 1 if room["role"] == "monster" else 4
    pool = [m for m in MONSTER_DEFS if m.get("boss", False) == (tier == 4)]
    if not pool:
        return []
    count = 1 if tier == 4 else random.randint(1, min(3, player_count))
    return [make_monster(random.choice(pool), room) for _ in range(count)]

def make_trap(room):
    return {"id": new_id(), "pos": [room["cx"] + random.randint(-1,1), room["cy"] + random.randint(-1,1)],
            "damage": random.randint(4, 8), "triggered": False, "room_id": room["id"]}

# ─── GAME ROOM ────────────────────────────────────────────────────────────────

class GameRoom:
    def __init__(self, code):
        self.code = code
        self.connections = {}   # pid -> websocket
        self.players = {}       # pid -> player dict
        self.player_order = []  # list of pid in turn order
        self.phase = "lobby"    # lobby | character_select | playing | ended
        self.host_pid = None
        self.tiles = None
        self.rooms = []
        self.monsters = {}      # id -> monster
        self.traps = []
        self.turn_index = 0
        self.round_num = 1
        self.gm_log = []        # narrative messages
        self.explored = set()   # (x,y) tuples visible to all
        self.stairs_pos = None  # [x, y] — entrance staircase tile
        self.temp_def = {}      # pid -> bonus_def (lasts 1 turn)
        self.smoke = {}         # mid -> True (monsters miss next attack)
        self.immune = {}        # pid -> turns_remaining
        self.blessed = {}       # pid -> atk_bonus
        self.taunted = None     # pid who has taunt active
        self.chests  = {}       # chest_id -> chest dict (persistent world loot)

    # ── broadcast helpers ──────────────────────────────────────────────────

    async def broadcast(self, msg):
        dead = []
        data = json.dumps(msg)
        for pid, ws in list(self.connections.items()):
            try:
                await ws.send(data)
            except Exception:
                dead.append(pid)
        for pid in dead:
            self.connections.pop(pid, None)

    async def send_to(self, pid, msg):
        ws = self.connections.get(pid)
        if ws:
            try:
                await ws.send(json.dumps(msg))
            except Exception:
                pass

    async def gm_say(self, text):
        self.gm_log.append(text)
        if len(self.gm_log) > 80:
            self.gm_log = self.gm_log[-60:]
        await self.broadcast({"type": "gm_narration", "text": text})

    # ── lobby ──────────────────────────────────────────────────────────────

    async def add_player(self, ws, pid, name):
        if len(self.players) >= 6:
            await ws.send(json.dumps({"type": "error", "msg": "Sala cheia (máximo 6 jogadores)."}))
            return False
        self.connections[pid] = ws
        self.players[pid] = {"id": pid, "name": name, "class_id": None, "ready": False, "slot": len(self.players)}
        if not self.host_pid:
            self.host_pid = pid
        await self.broadcast_lobby()
        return True

    async def select_class(self, pid, cls_id):
        if cls_id not in CLASSES:
            return
        # Check not taken
        taken = [p["class_id"] for p in self.players.values() if p["id"] != pid]
        if cls_id in taken:
            await self.send_to(pid, {"type": "error", "msg": "Classe já escolhida por outro jogador."})
            return
        self.players[pid]["class_id"] = cls_id
        self.players[pid]["ready"] = True
        await self.broadcast_lobby()

    async def broadcast_lobby(self):
        await self.broadcast({
            "type": "lobby_state",
            "code": self.code,
            "host": self.host_pid,
            "players": list(self.players.values()),
            "classes": {k: {"name": v["name"], "emoji": v["emoji"], "color": v["color"], "desc": v["desc"]} for k, v in CLASSES.items()},
            "can_start": (
                len(self.players) >= 1 and
                all(p["class_id"] for p in self.players.values())
            )
        })

    # ── game start ─────────────────────────────────────────────────────────

    async def start_game(self, pid):
        if pid != self.host_pid:
            await self.send_to(pid, {"type": "error", "msg": "Apenas o anfitrião pode iniciar."})
            return
        if not all(p["class_id"] for p in self.players.values()):
            await self.send_to(pid, {"type": "error", "msg": "Todos devem escolher uma classe."})
            return

        # Build full player states
        full_players = {}
        for slot, (pid2, p) in enumerate(self.players.items()):
            full_players[pid2] = make_player(pid2, p["name"], p["class_id"], slot)
        self.players = full_players
        self.player_order = list(full_players.keys())

        # Transition to city phase so players can shop before the dungeon
        self.phase = "city"
        await self.broadcast({"type": "game_start"})
        await self.broadcast_city_state()

    # ── city phase ─────────────────────────────────────────────────────────

    async def broadcast_city_state(self):
        await self.broadcast({
            "type": "city_state",
            "players": list(self.players.values()),
            "host": self.host_pid,
            "shops": {
                "ferreiro": {"weapons": SHOP_WEAPONS, "armors": SHOP_ARMORS},
                "mercador": SHOP_MERCHANT,
                "templo":   SHOP_TEMPLE,
                "taverna":  SHOP_TAVERN,
            },
        })

    async def handle_shop_buy(self, pid, shop, item_id):
        if self.phase != "city":
            return
        p = self.players.get(pid)
        if not p:
            return

        # Locate item in the correct catalog
        item = None
        if shop == "ferreiro_weapon":
            item = next((i for i in SHOP_WEAPONS  if i["id"] == item_id), None)
        elif shop == "ferreiro_armor":
            item = next((i for i in SHOP_ARMORS   if i["id"] == item_id), None)
        elif shop == "mercador":
            item = next((i for i in SHOP_MERCHANT if i["id"] == item_id), None)
        elif shop == "templo":
            item = next((i for i in SHOP_TEMPLE   if i["id"] == item_id), None)
        elif shop == "taverna":
            item = next((i for i in SHOP_TAVERN   if i["id"] == item_id), None)

        if not item:
            await self.send_to(pid, {"type": "error", "msg": "Item não encontrado."})
            return

        price = item["price"]
        if p["gold"] < price:
            await self.send_to(pid, {"type": "error", "msg": "Ouro insuficiente!"})
            return

        p["gold"] -= price
        log = ""

        if shop == "ferreiro_weapon":
            w = {**WEAPONS[item_id]}
            p["weapon"] = w
            p["gear"]["weapon"] = {
                "id": item_id, "name": item["name"],
                "emoji": item.get("emoji", "⚔️"),
                "item_slot": "weapon", "effect": "atk", "value": 0,
                "buy_price": price,
            }
            log = f"🔨 **{p['name']}** comprou **{item['name']}**!"

        elif shop == "ferreiro_armor":
            ac_bonus = item.get("ac_bonus", 0)
            kind     = item.get("kind", "armor")
            if kind == "shield":
                # Escudo vai para a mão esquerda (off_hand)
                shield_item = {
                    "id": item_id, "name": item["name"],
                    "emoji": item.get("emoji", "🛡️"),
                    "item_slot": "shield", "effect": "def_", "value": ac_bonus,
                    "buy_price": price,
                }
                if p["gear"].get("off_hand") is None:
                    p["gear"]["off_hand"] = shield_item
                    p["ac"] += ac_bonus
                    log = f"🔨 **{p['name']}** equipou **{item['name']}** (+{ac_bonus} CA)!"
                elif len(p["bag"]) < p.get("bag_size", 6):
                    p["bag"].append(shield_item)
                    log = f"🔨 **{p['name']}** comprou **{item['name']}** (guardado no inventário)."
                else:
                    p["gold"] += price
                    await self.send_to(pid, {"type": "error", "msg": "Mão esquerda ocupada e inventário cheio!"})
                    return
            else:
                # Regular armor replaces armor slot; recalculate keeping shield bonuses
                p["gear"]["armor"] = {
                    "id": item_id, "name": item["name"],
                    "emoji": item.get("emoji", "🛡️"),
                    "item_slot": "armor", "effect": "def_", "value": ac_bonus,
                    "buy_price": price,
                }
                _recalculate_ac(p)
                log = f"🔨 **{p['name']}** comprou **{item['name']}** (CA {p['ac']})!"

        elif shop == "mercador":
            slot = item.get("item_slot", "bag")
            if slot == "bag":
                if len(p["bag"]) >= p.get("bag_size", 6):
                    p["gold"] += price
                    await self.send_to(pid, {"type": "error", "msg": f"Inventário cheio (máx {p.get('bag_size', 6)} itens)!"})
                    return
                p["bag"].append({**item, "buy_price": price})
                log = f"🛒 **{p['name']}** comprou **{item['name']}**!"
            else:
                # Acessório/anel/elmo/mochila — vai para o inventário; o jogador equipa no slot certo
                if len(p["bag"]) >= p.get("bag_size", 6):
                    p["gold"] += price
                    await self.send_to(pid, {"type": "error", "msg": "Inventário cheio — abra espaço para comprar."})
                    return
                p["bag"].append({**item, "buy_price": price})
                log = f"🛒 **{p['name']}** comprou **{item['name']}** (equipe pelo inventário)."

        elif shop == "templo":
            effect = item.get("effect")
            if effect == "full_heal":
                p["hp"] = p["max_hp"]
                log = f"⛪ **{p['name']}** foi curado completamente no Templo!"
            elif effect == "full_mana":
                p["mp"] = p["max_mp"]
                log = f"⛪ **{p['name']}** restaurou toda a mana no Templo!"
            elif effect == "bless":
                bonus = item.get("value", 2)
                p["atk_bonus"] += bonus
                self.blessed[pid] = self.blessed.get(pid, 0) + bonus
                log = f"⛪ **{p['name']}** recebeu a Bênção Divina (+{bonus} ataque)!"
            elif effect == "cleanse":
                p["status"] = []
                log = f"⛪ **{p['name']}** foi purificado de todos os males!"

        elif shop == "taverna":
            effect = item.get("effect")
            if effect == "heal":
                heal = item.get("value", 8)
                p["hp"] = min(p["max_hp"], p["hp"] + heal)
                log = f"🍺 **{p['name']}** recuperou {heal} HP na Taverna!"
            elif effect == "temp_atk":
                bonus = item.get("value", 1)
                p["atk_bonus"] += bonus
                log = f"🍺 **{p['name']}** ganhou +{bonus} de ataque (efeito da cerveja)!"
            elif effect == "full_heal_mp":
                p["hp"] = p["max_hp"]
                p["mp"] = p["max_mp"]
                log = f"🍺 **{p['name']}** descansou completamente e recuperou tudo na Taverna!"

        if log:
            await self.broadcast({"type": "shop_result", "msg": log})
        await self.broadcast_city_state()

    async def handle_shop_sell(self, pid, item_slot):
        """Sell an equipped item or bag item; player receives buy_price // 3 gold."""
        if self.phase != "city":
            return
        p = self.players.get(pid)
        if not p:
            return

        log = ""

        if item_slot == "weapon":
            item = p["gear"].get("weapon")
            if not item or item.get("id") == "unarmed":
                await self.send_to(pid, {"type": "error", "msg": "Nenhuma arma para vender."})
                return
            sell_price = max(1, item.get("buy_price", 0) // 3)
            p["gold"] += sell_price
            # Restore unarmed state
            p["weapon"] = {**WEAPONS["unarmed"]}
            p["gear"]["weapon"] = {
                "id": "unarmed", "name": "Desarmado", "emoji": "✊",
                "item_slot": "weapon", "effect": "atk", "value": 0, "buy_price": 0,
            }
            log = f"💰 **{p['name']}** vendeu **{item['name']}** por {sell_price} ouro!"

        elif item_slot == "armor":
            item = p["gear"].get("armor")
            if not item:
                await self.send_to(pid, {"type": "error", "msg": "Nenhuma armadura para vender."})
                return
            sell_price = max(1, item.get("buy_price", 0) // 3)
            p["gold"] += sell_price
            p["gear"]["armor"] = {
                "id": "cloak", "name": "Manto", "emoji": "🧣",
                "item_slot": "armor", "effect": "def_", "value": 0, "buy_price": 0,
            }
            _recalculate_ac(p)
            log = f"💰 **{p['name']}** vendeu **{item['name']}** por {sell_price} ouro!"

        elif item_slot in ("off_hand", "head", "ring1", "ring2", "item1", "item2", "acc1", "acc2"):
            # 'acc1'/'acc2' aceitos por retrocompatibilidade
            key = {"acc1": "item1", "acc2": "item2"}.get(item_slot, item_slot)
            item = p["gear"].get(key)
            if not item:
                await self.send_to(pid, {"type": "error", "msg": "Nenhum item neste slot."})
                return
            sell_price = max(1, item.get("buy_price", 0) // 3)
            p["gold"] += sell_price
            p["gear"][key] = None
            # Reverter efeitos do item (incremental — mesmo padrão do equip)
            self._apply_gear_effect(p, item, False)
            log = f"💰 **{p['name']}** vendeu **{item['name']}** por {sell_price} ouro!"

        elif item_slot.startswith("bag_"):
            try:
                idx  = int(item_slot.split("_")[1])
                item = p["bag"][idx]
                p["bag"].pop(idx)
                sell_price = max(1, item.get("buy_price", item.get("price", 0)) // 3)
                p["gold"] += sell_price
                log = f"💰 **{p['name']}** vendeu **{item['name']}** por {sell_price} ouro!"
            except (ValueError, IndexError):
                await self.send_to(pid, {"type": "error", "msg": "Item não encontrado na mochila."})
                return
        else:
            await self.send_to(pid, {"type": "error", "msg": "Slot inválido."})
            return

        if log:
            await self.broadcast({"type": "shop_result", "msg": log})
        await self.broadcast_city_state()

    async def enter_dungeon(self, pid):
        if pid != self.host_pid:
            await self.send_to(pid, {"type": "error", "msg": "Apenas o anfitrião pode entrar na masmorra."})
            return
        if self.phase != "city":
            return

        self.phase = "playing"
        self.tiles, self.rooms = generate_dungeon()

        # Place players at entrance
        entrance = next((r for r in self.rooms if r["role"] == "entrance"), self.rooms[0])
        pids = list(self.players.keys())
        offsets = [(0,0),(1,0),(-1,0),(0,1),(1,1),(-1,1)]
        for i, pid2 in enumerate(pids):
            ox, oy = offsets[i % len(offsets)]
            self.players[pid2]["pos"] = [entrance["cx"] + ox, entrance["cy"] + oy]
            self.players[pid2]["moves_left"]  = self.players[pid2]["spd"]
            self.players[pid2]["action_done"] = False

        # Spawn monsters & traps
        for room in self.rooms:
            if room["role"] == "monster":
                for m in spawn_monsters_for_room(room, len(pids)):
                    self.monsters[m["id"]] = m
            if room["role"] == "boss":
                boss_def = next(m for m in MONSTER_DEFS if m.get("boss"))
                m = make_monster(boss_def, room)
                self.monsters[m["id"]] = m
            if room["role"] == "trap":
                self.traps.append(make_trap(room))

        # Stairs tile — centre of entrance room (same spawn point as players)
        self.stairs_pos = [entrance["cx"], entrance["cy"]]

        # Reveal entrance (room + 1-tile border so surrounding walls are visible)
        self._reveal_room(entrance)

        await self.broadcast({"type": "enter_dungeon"})
        await self.push_state()
        await self.gm_say(gm("intro"))
        await self.gm_say(f"Os aventureiros partem da cidade e adentram a masmorra. Turno 1 — é a vez de **{self.players[self.current_pid()]['name']}**.")

    def current_pid(self):
        if not self.player_order:
            return None
        return self.player_order[self.turn_index % len(self.player_order)]

    def _reveal_room(self, room):
        # Reveal room interior + 1-tile border so surrounding walls are visible
        for ry in range(max(0, room["y"] - 1), min(MAP_H, room["y"] + room["h"] + 1)):
            for rx in range(max(0, room["x"] - 1), min(MAP_W, room["x"] + room["w"] + 1)):
                self.explored.add((rx, ry))

    def _reveal_around(self, px, py, radius=1):
        for dy in range(-radius, radius+1):
            for dx in range(-radius, radius+1):
                self.explored.add((px+dx, py+dy))

    # ── turn actions ───────────────────────────────────────────────────────

    async def handle_move(self, pid, dx, dy):
        if not self._is_turn(pid): return
        p = self.players[pid]
        if not p["alive"]: return
        if p["moves_left"] <= 0:
            await self.send_to(pid, {"type": "error", "msg": "Sem movimentos restantes."})
            return

        nx, ny = p["pos"][0] + dx, p["pos"][1] + dy
        if not (0 <= nx < MAP_W and 0 <= ny < MAP_H):
            return
        if self.tiles[ny][nx] == WALL:
            await self.send_to(pid, {"type": "error", "msg": "Caminho bloqueado."})
            return

        # Block movement into a tile occupied by a living monster
        for m in self.monsters.values():
            if m["hp"] > 0 and m["pos"] == [nx, ny]:
                await self.send_to(pid, {"type": "error", "msg": "Um inimigo bloqueia o caminho!"})
                return

        # Block movement into a tile occupied by another player
        for other_pid, other_p in self.players.items():
            if other_pid != pid and other_p["alive"] and other_p["pos"] == [nx, ny]:
                await self.send_to(pid, {"type": "error", "msg": "Outro aventureiro está neste espaço."})
                return

        p["pos"] = [nx, ny]
        p["moves_left"] -= 1
        self._reveal_around(nx, ny, radius=3)   # larger radius keeps corridors fully lit

        # Check room entry
        entered = player_room(self.rooms, nx, ny)
        if entered and not entered["cleared"]:
            await self._on_enter_room(pid, entered)

        # Spawn physical chest when first entering a chest room
        if entered and entered["role"] == "chest" and not entered["looted"]:
            await self._spawn_chest_from_room(entered)

        # Check trap
        for trap in self.traps:
            if trap["pos"] == [nx, ny] and not trap["triggered"]:
                if "detect_trap" not in [s for s in p.get("status", [])]:
                    trap["triggered"] = True
                    prefix = random.choice(GM["room_trap"])
                    save_roll = random.randint(1, 20)
                    passed = save_roll + p["ref_"] >= 13
                    await self.broadcast({"type": "dice_roll", "die": "d20",
                                           "value": save_roll, "label": "Reflexos"})
                    if passed:
                        await self.gm_say(prefix + f" **{p['name']}** passou no teste de **Reflexos** (CD 13) e se esquivou!")
                    else:
                        p["hp"] = max(0, p["hp"] - trap["damage"])
                        await self.gm_say(prefix + f" **{p['name']}** falhou em **Reflexos** (CD 13) e sofre **{trap['damage']}** de dano!")
                        if p["hp"] <= 0:
                            await self._player_dies(pid)

        await self.push_state()

    async def _on_enter_room(self, pid, room):
        if room["cleared"]:
            return
        role = room["role"]
        self._reveal_room(room)
        if role in GM:
            await self.gm_say(gm(role))
        if role in ("monster", "boss"):
            await self.gm_say(gm("combat_start"))
        if role == "chest" and not room["looted"]:
            await self.gm_say(gm("room_chest"))

    # ── adjacency helpers ──────────────────────────────────────────────────

    def _cardinal_adjacent(self, pos_a, pos_b):
        """True only if pos_b is in one of the 4 cardinal directions from pos_a (no diagonal)."""
        dx = abs(pos_a[0] - pos_b[0])
        dy = abs(pos_a[1] - pos_b[1])
        return (dx == 1 and dy == 0) or (dx == 0 and dy == 1)

    async def handle_attack(self, pid, target_id):
        if not self._is_turn(pid): return
        p = self.players[pid]
        if not p["alive"] or p["action_done"]: return

        if target_id in self.monsters:
            target = self.monsters[target_id]

            # ── Range check: ranged weapons use Chebyshev distance; melee cardinal-only ──
            weapon_here = p.get("weapon")
            w_range = weapon_here.get("range") if weapon_here else None
            if w_range is not None:
                dx = abs(p["pos"][0] - target["pos"][0])
                dy = abs(p["pos"][1] - target["pos"][1])
                if max(dx, dy) > w_range:
                    await self.send_to(pid, {
                        "type": "error",
                        "msg": f"⚠ {target['name']} está fora de alcance! (máximo {w_range} quadrados)"
                    })
                    return
            else:
                if not self._cardinal_adjacent(p["pos"], target["pos"]):
                    await self.send_to(pid, {
                        "type": "error",
                        "msg": f"⚠ {target['name']} está fora de alcance! Aproxime-se (1 quadrado ortogonal)."
                    })
                    return

            hit, roll, total, crit = d20_attack(p["atk_bonus"], target["ac"])
            await self.broadcast({"type": "dice_roll", "die": "d20", "value": roll,
                                   "label": "Ataque", "hit": hit, "crit": crit})
            if hit:
                weapon = p.get("weapon")
                die_str = weapon.get("die") if weapon else None
                if die_str:
                    # Armed attack — roll weapon die
                    raw_dmg = roll_dice(die_str)
                    stat_bonus = mod(p.get(weapon["stat"], 12))
                    dmg = raw_dmg + stat_bonus
                    if crit: dmg *= 2
                    dmg = max(1, dmg)
                    die_type = "d" + die_str.split("d")[1]
                    await self.broadcast({"type": "dice_roll", "die": die_type,
                                           "value": raw_dmg, "label": "Dano"})
                    weapon_name = weapon.get("name", "arma")
                    sb = f"+{stat_bonus}" if stat_bonus >= 0 else str(stat_bonus)
                    dmg_detail = f"[{die_str}={raw_dmg}{sb}]"
                else:
                    # Unarmed — fixed 1 + STR modifier
                    str_bonus = mod(p.get("str_", 12))
                    dmg = 1 + str_bonus
                    if crit: dmg *= 2
                    dmg = max(1, dmg)
                    weapon_name = "soco"
                    sb = f"+{str_bonus}" if str_bonus >= 0 else str(str_bonus)
                    dmg_detail = f"[1{sb}]"
                target["hp"] -= dmg
                crit_str = " **CRÍTICO!**" if crit else ""
                await self.gm_say(
                    f"⚔️ **{p['name']}** ataca **{target['name']}** com {weapon_name}"
                    f" (d20={roll}+{p['atk_bonus']}={total} vs CA {target['ac']}):"
                    f"{crit_str} dano {dmg_detail} = **{dmg}**!")
                if target["hp"] <= 0:
                    await self._monster_dies(target, pid)
            else:
                await self.gm_say(
                    f"⚔️ **{p['name']}** ataca **{target['name']}**"
                    f" (d20={roll}+{p['atk_bonus']}={total} vs CA {target['ac']}): **ERROU!**")
        else:
            await self.send_to(pid, {"type": "error", "msg": "Alvo inválido."})
            return

        p["action_done"] = True
        await self.push_state()

    async def handle_skill(self, pid, skill_id, target_id):
        if not self._is_turn(pid): return
        p = self.players[pid]
        if not p["alive"] or p["action_done"]: return

        skill = next((s for s in p["skills"] if s["id"] == skill_id), None)
        if not skill:
            await self.send_to(pid, {"type": "error", "msg": "Habilidade inválida."}); return
        if p["mp"] < skill["mp"]:
            await self.send_to(pid, {"type": "error", "msg": "MP insuficiente."}); return

        p["mp"] -= skill["mp"]
        p["action_done"] = True
        await self._apply_skill(p, skill, target_id)
        await self.push_state()

    async def _apply_skill(self, p, skill, target_id):
        sid = skill["id"]
        alive_monsters = [m for m in self.monsters.values() if m["hp"] > 0]

        if sid == "heavy_blow":
            t = self.monsters.get(target_id)
            if t:
                if not self._cardinal_adjacent(p["pos"], t["pos"]):
                    await self.gm_say(f"⚠ **{p['name']}** tenta **Golpe Pesado** mas o inimigo está fora de alcance!"); return
                hit, roll, total, crit = d20_attack(p["atk_bonus"], t["ac"])
                await self.broadcast({"type": "dice_roll", "die": "d20", "value": roll, "label": "Golpe Pesado"})
                if hit:
                    weapon = p["weapon"]
                    raw_dmg = roll_dice(weapon["die"])
                    die_type = "d" + weapon["die"].split("d")[1]
                    await self.broadcast({"type": "dice_roll", "die": die_type, "value": raw_dmg, "label": "Dano"})
                    dmg = (raw_dmg + mod(p[weapon["stat"]])) * 2
                    if crit: dmg *= 2
                    dmg = max(1, dmg)
                    t["hp"] -= dmg
                    await self.gm_say(f"💥 **{p['name']}** usa **Golpe Pesado** em **{t['name']}** (d20={roll}+{p['atk_bonus']}={total} vs CA {t['ac']}): **{dmg}** de dano!")
                    if t["hp"] <= 0: await self._monster_dies(t, p["id"])
                else:
                    await self.gm_say(f"💥 **{p['name']}** tenta **Golpe Pesado** mas **ERROU** (d20={roll}={total} vs CA {t['ac']})!")

        elif sid == "taunt":
            self.taunted = p["id"]
            await self.gm_say(f"😤 **{p['name']}** usa **Provocar** — todos os monstros agora focam nele!")

        elif sid == "shield_bash":
            self.temp_def[p["id"]] = self.temp_def.get(p["id"], 0) + 3
            await self.gm_say(f"🛡️ **{p['name']}** ergue o escudo! +3 CA até o próximo turno.")

        elif sid == "fireball":
            showcase = roll_dice("4d6")
            await self.broadcast({"type": "dice_roll", "die": "d6", "value": showcase, "label": "Bola de Fogo"})
            total_dmg_list = []
            for m in alive_monsters:
                dmg = max(1, roll_dice("4d6") + mod(p["int_"]))
                m["hp"] -= dmg
                total_dmg_list.append(dmg)
            avg = sum(total_dmg_list) // max(1, len(total_dmg_list)) if total_dmg_list else 0
            await self.gm_say(f"🔥 **{p['name']}** lança **Bola de Fogo**! {len(alive_monsters)} inimigo(s) sofrem ~**{avg}** de dano (4d6+INT)!")
            for m in list(alive_monsters):
                if m["hp"] <= 0: await self._monster_dies(m, p["id"])

        elif sid == "ice_lance":
            t = self.monsters.get(target_id)
            if t:
                raw_dmg = roll_dice("3d6")
                await self.broadcast({"type": "dice_roll", "die": "d6", "value": raw_dmg, "label": "Lança de Gelo"})
                dmg = max(1, raw_dmg + mod(p["int_"]))
                t["hp"] -= dmg
                await self.gm_say(f"🧊 **{p['name']}** usa **Lança de Gelo** em **{t['name']}**: **{dmg}** de dano de frio!")
                if t["hp"] <= 0: await self._monster_dies(t, p["id"])

        elif sid == "magic_shield":
            self.temp_def[p["id"]] = self.temp_def.get(p["id"], 0) + 4
            await self.gm_say(f"✨ **{p['name']}** ativa **Escudo Mágico**! +4 CA até o próximo turno.")

        elif sid == "backstab":
            t = self.monsters.get(target_id)
            if t:
                if not self._cardinal_adjacent(p["pos"], t["pos"]):
                    await self.gm_say(f"⚠ **{p['name']}** tenta **Ataque Furtivo** mas o inimigo está fora de alcance!"); return
                hit, roll, total, crit = d20_attack(p["atk_bonus"] + 2, t["ac"])
                await self.broadcast({"type": "dice_roll", "die": "d20", "value": roll, "label": "Ataque Furtivo"})
                if hit:
                    weapon = p["weapon"]
                    raw_wpn = roll_dice(weapon["die"])
                    raw_snk = roll_dice("2d6")
                    die_type = "d" + weapon["die"].split("d")[1]
                    await self.broadcast({"type": "dice_roll", "die": die_type, "value": raw_wpn, "label": "Dano"})
                    await self.broadcast({"type": "dice_roll", "die": "d6", "value": raw_snk, "label": "Furtivo"})
                    if crit:
                        dmg = (raw_wpn + raw_snk) * 2 + mod(p[weapon["stat"]])
                    else:
                        dmg = raw_wpn + raw_snk + mod(p[weapon["stat"]])
                    dmg = max(1, dmg)
                    t["hp"] -= dmg
                    await self.gm_say(f"🗡️ **{p['name']}** usa **Ataque Furtivo** em **{t['name']}** (d20={roll}+{p['atk_bonus']+2}={total} vs CA {t['ac']}): **{dmg}** de dano furtivo!")
                    if t["hp"] <= 0: await self._monster_dies(t, p["id"])
                else:
                    await self.gm_say(f"🗡️ **{p['name']}** tenta **Ataque Furtivo** mas **ERROU** (d20={roll}={total} vs CA {t['ac']})!")

        elif sid == "detect_trap":
            if "detect_trap" not in p["status"]: p["status"].append("detect_trap")
            revealed = [tr for tr in self.traps if not tr["triggered"]]
            for tr in revealed: self.explored.add(tuple(tr["pos"]))
            await self.gm_say(f"👁️ **{p['name']}** detecta armadilhas! {len(revealed)} armadilha(s) revelada(s).")

        elif sid == "smoke_bomb":
            for m in alive_monsters:
                self.smoke[m["id"]] = True
            await self.gm_say(f"💨 **{p['name']}** lança **Bomba de Fumaça**! Os inimigos errarão o próximo ataque.")

        elif sid == "heal":
            t = self.players.get(target_id, p)
            raw_heal = roll_dice("2d6")
            await self.broadcast({"type": "dice_roll", "die": "d6", "value": raw_heal, "label": "Cura"})
            heal = raw_heal + 2
            t["hp"] = min(t["max_hp"], t["hp"] + heal)
            await self.gm_say(f"💚 **{p['name']}** cura **{t['name']}** em **{heal}** HP! (2d6+2)")

        elif sid == "holy_light":
            showcase = roll_dice("2d6")
            await self.broadcast({"type": "dice_roll", "die": "d6", "value": showcase, "label": "Luz Sagrada"})
            for m in alive_monsters:
                dmg = max(1, roll_dice("2d6") + mod(p["int_"]))
                m["hp"] -= dmg
            await self.gm_say(f"☀️ **{p['name']}** invoca **Luz Sagrada**! 2d6+INT dano sagrado em todos os inimigos!")
            for m in list(alive_monsters):
                if m["hp"] <= 0: await self._monster_dies(m, p["id"])

        elif sid == "bless":
            for p2 in self.players.values():
                if p2["alive"]:
                    p2["atk_bonus"] += 2
                    self.blessed[p2["id"]] = self.blessed.get(p2["id"], 0) + 2
            await self.gm_say(f"🙏 **{p['name']}** abençoa o grupo! +2 Bônus de Ataque para todos por 1 turno.")

        elif sid == "double_shot":
            t = self.monsters.get(target_id)
            if t:
                total_dmg = 0
                hits = 0
                for _ in range(2):
                    hit, roll, total, crit = d20_attack(p["atk_bonus"], t["ac"])
                    await self.broadcast({"type": "dice_roll", "die": "d20", "value": roll, "label": "Tiro Duplo"})
                    if hit:
                        weapon = p["weapon"]
                        raw_dmg = roll_dice(weapon["die"])
                        die_type = "d" + weapon["die"].split("d")[1]
                        await self.broadcast({"type": "dice_roll", "die": die_type, "value": raw_dmg, "label": "Dano"})
                        if crit: raw_dmg *= 2
                        total_dmg += max(1, raw_dmg + mod(p[weapon["stat"]]))
                        hits += 1
                if hits:
                    t["hp"] -= total_dmg
                    await self.gm_say(f"🏹 **{p['name']}** usa **Tiro Duplo** em **{t['name']}**: {hits} acerto(s), **{total_dmg}** de dano total!")
                    if t["hp"] <= 0: await self._monster_dies(t, p["id"])
                else:
                    await self.gm_say(f"🏹 **{p['name']}** usa **Tiro Duplo** mas ambos os tiros **ERRARAM**!")

        elif sid == "arrow_rain":
            showcase = roll_dice("1d8")
            await self.broadcast({"type": "dice_roll", "die": "d8", "value": showcase, "label": "Chuva de Flechas"})
            for m in alive_monsters:
                dmg = max(1, roll_dice("1d8") + mod(p["dex"]))
                m["hp"] -= dmg
            await self.gm_say(f"🏹 **{p['name']}** usa **Chuva de Flechas**! 1d8+DES em todos os inimigos!")
            for m in list(alive_monsters):
                if m["hp"] <= 0: await self._monster_dies(m, p["id"])

        elif sid == "piercing_shot":
            t = self.monsters.get(target_id)
            if t:
                weapon = p["weapon"]
                raw_dmg = roll_dice(weapon["die"])
                die_type = "d" + weapon["die"].split("d")[1]
                await self.broadcast({"type": "dice_roll", "die": die_type, "value": raw_dmg, "label": "Tiro Perfurante"})
                dmg = max(1, raw_dmg * 2 + mod(p[weapon["stat"]]))
                t["hp"] -= dmg
                await self.gm_say(f"🎯 **{p['name']}** usa **Tiro Perfurante** em **{t['name']}**: **{dmg}** de dano (acerto automático, ignora CA)!")
                if t["hp"] <= 0: await self._monster_dies(t, p["id"])

        elif sid == "smite":
            t = self.monsters.get(target_id)
            if t:
                if not self._cardinal_adjacent(p["pos"], t["pos"]):
                    await self.gm_say(f"⚠ **{p['name']}** tenta **Golpe Divino** mas o inimigo está fora de alcance!"); return
                hit, roll, total, crit = d20_attack(p["atk_bonus"], t["ac"])
                await self.broadcast({"type": "dice_roll", "die": "d20", "value": roll, "label": "Golpe Divino"})
                if hit:
                    weapon = p["weapon"]
                    raw_base = roll_dice(weapon["die"])
                    raw_holy = roll_dice("1d6")
                    die_type = "d" + weapon["die"].split("d")[1]
                    await self.broadcast({"type": "dice_roll", "die": die_type, "value": raw_base, "label": "Dano"})
                    await self.broadcast({"type": "dice_roll", "die": "d6", "value": raw_holy, "label": "Sagrado"})
                    base = raw_base + mod(p[weapon["stat"]])
                    holy = raw_holy
                    if crit: base *= 2; holy *= 2
                    dmg = max(1, base + holy)
                    t["hp"] -= dmg
                    await self.gm_say(f"⚡ **{p['name']}** usa **Golpe Divino** em **{t['name']}** (d20={roll}+{p['atk_bonus']}={total} vs CA {t['ac']}): **{dmg}** de dano sagrado!")
                    if t["hp"] <= 0: await self._monster_dies(t, p["id"])
                else:
                    await self.gm_say(f"⚡ **{p['name']}** tenta **Golpe Divino** mas **ERROU** (d20={roll}={total} vs CA {t['ac']})!")

        elif sid == "divine_shield":
            t = self.players.get(target_id, p)
            self.immune[t["id"]] = 1
            await self.gm_say(f"🛡️ **{p['name']}** protege **{t['name']}** com **Escudo Divino**! Imune a dano por 1 turno.")

        elif sid == "holy_aura":
            for p2 in self.players.values():
                if p2["alive"]:
                    self.temp_def[p2["id"]] = self.temp_def.get(p2["id"], 0) + 2
            await self.gm_say(f"✨ **{p['name']}** ativa **Aura Sagrada**! +2 CA para todos por 2 turnos.")

        # ── Bard skills ──────────────────────────────────────────────────────
        elif sid == "bard_inspire":
            for p2 in self.players.values():
                if p2["alive"]:
                    p2["atk_bonus"] += 2
                    self.blessed[p2["id"]] = self.blessed.get(p2["id"], 0) + 2
            await self.gm_say(f"🎶 **{p['name']}** toca **Inspiração**! +2 Bônus de Ataque para todos os aliados por 1 turno!")

        elif sid == "bard_confusion":
            for m in alive_monsters:
                self.smoke[m["id"]] = True
            await self.gm_say(f"🎵 **{p['name']}** entoa **Canção da Confusão**! Todos os inimigos errarão o próximo ataque!")

        elif sid == "bard_lullaby":
            showcase = roll_dice("1d6")
            await self.broadcast({"type": "dice_roll", "die": "d6", "value": showcase, "label": "Balada Curativa"})
            healed = []
            for p2 in self.players.values():
                if p2["alive"]:
                    heal = roll_dice("1d6") + 2
                    p2["hp"] = min(p2["max_hp"], p2["hp"] + heal)
                    healed.append(f"**{p2['name']}** +{heal}")
            detail = ", ".join(healed) if healed else "nenhum"
            await self.gm_say(f"🎶 **{p['name']}** canta **Balada Curativa**! {detail} HP curado(s).")

    # ── exit dungeon (return to city via entrance stairs) ──────────────────

    async def handle_exit_dungeon(self, pid):
        if self.phase != "playing": return
        p = self.players.get(pid)
        if not p or not p["alive"]: return
        # No position check — clicking the staircase tile exits regardless of distance
        self.phase = "city"
        for pp in self.players.values():
            pp["moves_left"] = pp["spd"]
            pp["action_done"] = False
        await self.gm_say(f"🚪 **{p['name']}** usa as escadas de saída. Os aventureiros retornam à cidade!")
        await self.broadcast_city_state()

    # ── inventory helpers ──────────────────────────────────────────────────

    def _apply_gear_effect(self, p, item, equipping):
        mult = 1 if equipping else -1
        e, v = item.get("effect"), item.get("value", 0) * mult
        if e in ("atk", "atk_bonus"):
            p["atk_bonus"] += v; p["base_atk_bonus"] += v
        elif e in ("def_", "ac_bonus"):
            p["ac"] += v
            p["ac_base"] = p.get("ac_base", 10) + v
        elif e == "maxhp":
            p["max_hp"] += v
            if equipping: p["hp"] = min(p["max_hp"], p["hp"] + v)
        elif e == "spd":
            p["spd"] += v
        elif e == "bagslots":
            # Mochila/alforje: expande o inventário enquanto equipada
            p["bag_size"] = max(1, p.get("bag_size", 6) + v)

    def _add_to_inventory(self, p, item):
        """Coloca o item no inventário (bag_size slots). Retorna 'bag'|'full'."""
        if len(p["bag"]) < p.get("bag_size", 6):
            p["bag"].append(item)
            return "bag"
        return "full"

    @staticmethod
    def _slot_category_for_item(item):
        """Categoria de slot de um item: weapon|off_hand|armor|head|ring|item|bag."""
        s   = (item.get("item_slot") or "").lower()
        k   = (item.get("kind") or "").lower()
        iid = (item.get("id") or "").lower()
        nm  = (item.get("name") or "").lower()
        if s == "weapon" or k == "weapon":
            return "weapon"
        if s in ("shield", "off_hand") or k == "shield" or "shield" in iid or "escudo" in nm:
            return "off_hand"
        if s == "head" or k == "head" or any(w in nm for w in ("elmo", "capuz", "tiara", "capacete")):
            return "head"
        if s == "ring" or k == "ring" or "anel" in nm:
            return "ring"
        if s in ("accessory", "belt", "gloves", "backpack", "item") or \
           k in ("accessory", "belt", "gloves", "backpack") or \
           any(w in nm for w in ("mochila", "alforje", "luva", "cinto")):
            return "item"
        if s == "armor" or k == "armor":
            return "armor"
        return "bag"

    def _equip_into_slot(self, p, item, slot_key, log_emoji="🎒"):
        """Equipa item num slot único; devolve o antigo ao inventário (se couber)."""
        gear = p["gear"]
        old = gear.get(slot_key)
        gear[slot_key] = item
        self._apply_gear_effect(p, item, True)
        if old:
            self._apply_gear_effect(p, old, False)
            if len(p["bag"]) < p.get("bag_size", 6):
                p["bag"].append(old)
        return f"{log_emoji} **{p['name']}** equipou **{item['name']}**!"

    def _equip_into_pair(self, p, item, keys, log_emoji="💍"):
        """Equipa em par de slots (anéis/itens): 1º vazio, senão troca o primeiro."""
        gear = p["gear"]
        for k in keys:
            if gear.get(k) is None:
                gear[k] = item
                self._apply_gear_effect(p, item, True)
                return f"{log_emoji} **{p['name']}** equipou **{item['name']}**!"
        return self._equip_into_slot(p, item, keys[0], log_emoji)

    async def handle_equip_from_bag(self, pid, slot_index):
        """Equipa um item do inventário no slot de equipamento correto (8 slots)."""
        p = self.players.get(pid)
        if not p:
            return
        if slot_index < 0 or slot_index >= len(p["bag"]):
            await self.send_to(pid, {"type": "error", "msg": "Slot de inventário inválido."}); return

        item = p["bag"][slot_index]
        cat  = self._slot_category_for_item(item)

        if cat == "bag":
            await self.send_to(pid, {"type": "error", "msg": "Este item é consumível — use-o durante o combate!"}); return

        # Remove do inventário antes de equipar
        p["bag"].pop(slot_index)

        if   cat == "weapon":   log = self._equip_into_slot(p, item, "weapon",   "⚔️")
        elif cat == "off_hand": log = self._equip_into_slot(p, item, "off_hand", "🛡️")
        elif cat == "armor":    log = self._equip_into_slot(p, item, "armor",    "🛡️")
        elif cat == "head":     log = self._equip_into_slot(p, item, "head",     "⛑️")
        elif cat == "ring":     log = self._equip_into_pair(p, item, ("ring1","ring2"), "💍")
        else:                   log = self._equip_into_pair(p, item, ("item1","item2"), "🎒")

        if log:
            await self.gm_say(log)
        await self.push_state()

    async def handle_unequip(self, pid, slot_key):
        """Desequipa um item de um slot, devolvendo-o ao inventário."""
        p = self.players.get(pid)
        if not p or slot_key not in GEAR_SLOTS:
            return
        item = p["gear"].get(slot_key)
        if not item:
            return
        if len(p["bag"]) >= p.get("bag_size", 6):
            await self.send_to(pid, {"type": "error", "msg": "Inventário cheio — não há espaço para desequipar."}); return
        p["gear"][slot_key] = None
        self._apply_gear_effect(p, item, False)
        p["bag"].append(item)
        await self.gm_say(f"📤 **{p['name']}** desequipou **{item['name']}**.")
        await self.push_state()

    # ── chest helpers ──────────────────────────────────────────────────────────

    def _spawn_chest(self, pos, gold, items, source_id=None):
        """Create a persistent chest object in the world. Returns chest id."""
        cid = new_id()
        self.chests[cid] = {
            "id":        cid,
            "pos":       list(pos),
            "gold":      max(0, int(gold)),
            "items":     [deepcopy(i) for i in items],
            "source_id": source_id,
        }
        return cid

    async def _spawn_chest_from_room(self, room):
        """Spawn a physical chest at room centre (replaces _auto_pickup_chest)."""
        room["looted"] = True
        gold  = random.randint(10, 35)
        items = [deepcopy(random.choice(CHEST_ITEMS))]
        if random.random() < 0.45:                            # 45 % chance for 2nd item
            extra = deepcopy(random.choice(CHEST_ITEMS))
            if extra["id"] != items[0]["id"]:
                items.append(extra)
        self._spawn_chest([room["cx"], room["cy"]], gold, items)
        await self.gm_say("🎁 Um **baú** apareceu no centro da sala! Aproxime-se e clique nele para coletar.")

    async def handle_take_from_chest(self, pid, chest_id, kind, index):
        """Player takes gold or an item from a chest (no turn restriction)."""
        p = self.players.get(pid)
        if not p or not p.get("alive"):
            return
        chest = self.chests.get(chest_id)
        if not chest:
            await self.send_to(pid, {"type": "error", "msg": "Baú não encontrado."}); return

        # Distance check — must be within 2 tiles (Chebyshev)
        cx, cy = chest["pos"]
        px, py = p["pos"]
        if max(abs(px - cx), abs(py - cy)) > 2:
            await self.send_to(pid, {"type": "error", "msg": "Muito longe do baú!"}); return

        if kind == "gold":
            amount = chest["gold"]
            if amount <= 0:
                await self.send_to(pid, {"type": "error", "msg": "Sem ouro neste baú."}); return
            p["gold"] += amount
            chest["gold"] = 0
            await self.gm_say(f"🪙 **{p['name']}** pegou **{amount}** ouros do baú!")
        elif kind == "item":
            idx = int(index)
            if idx < 0 or idx >= len(chest["items"]):
                await self.send_to(pid, {"type": "error", "msg": "Item inválido."}); return
            item = chest["items"][idx]
            result = self._add_to_inventory(p, item)
            if result == "full":
                await self.send_to(pid, {"type": "error", "msg": "Inventário cheio!"}); return
            chest["items"].pop(idx)
            await self.gm_say(f"📦 **{p['name']}** pegou **{item['emoji']} {item['name']}** do baú!")
        else:
            return

        # Remove chest if empty
        if chest["gold"] <= 0 and not chest["items"]:
            del self.chests[chest_id]
            await self.gm_say("🔲 O baú está vazio e desaparece.")

        await self.push_state()

    async def handle_use_item(self, pid, item_id):
        if not self._is_turn(pid): return
        p = self.players[pid]
        item = next((i for i in p["bag"] if i["id"] == item_id), None)
        if not item:
            await self.send_to(pid, {"type": "error", "msg": "Item não encontrado."}); return

        effect, val = item["effect"], item["value"]
        if effect == "heal":
            p["hp"] = min(p["max_hp"], p["hp"] + val)
            await self.gm_say(f"{item['emoji']} **{p['name']}** usa **{item['name']}** e recupera **{val}** HP!")
        elif effect == "mana":
            p["mp"] = min(p["max_mp"], p["mp"] + val)
            await self.gm_say(f"{item['emoji']} **{p['name']}** usa **{item['name']}** e recupera **{val}** MP!")
        elif effect == "atk_bonus":
            self.blessed[pid] = self.blessed.get(pid, 0) + val
            p["atk_bonus"] += val
            await self.gm_say(f"{item['emoji']} **{p['name']}** usa **{item['name']}**! +{val} Bônus de Ataque neste turno!")

        p["bag"].remove(item)
        await self.push_state()

    async def handle_end_turn(self, pid):
        if not self._is_turn(pid): return
        p = self.players[pid]
        p["moves_left"] = p["spd"]
        p["action_done"] = False

        # Clear temp effects for this player
        self.temp_def.pop(pid, None)
        if pid in self.blessed:
            self.players[pid]["atk_bonus"] = self.players[pid]["base_atk_bonus"]
            self.blessed.pop(pid)
        if self.immune.get(pid, 0) > 0:
            self.immune[pid] -= 1

        # Advance turn
        self.turn_index += 1
        # Skip dead players
        attempts = 0
        while attempts < len(self.player_order):
            cur = self.player_order[self.turn_index % len(self.player_order)]
            if self.players[cur]["alive"]:
                break
            self.turn_index += 1
            attempts += 1

        # If we wrapped around, GM phase
        if self.turn_index % len(self.player_order) == 0 and self.turn_index > 0:
            self.round_num += 1
            await self.gm_phase()
        else:
            next_p = self.players[self.current_pid()]
            next_p["moves_left"] = next_p["spd"]
            await self.gm_say(f"🎲 Turno de **{next_p['name']}**!")

        await self.push_state()

    # ── GM phase (monsters act) ─────────────────────────────────────────────

    async def gm_phase(self):
        alive_monsters = [m for m in self.monsters.values() if m["hp"] > 0]
        alive_players = [p for p in self.players.values() if p["alive"]]
        if not alive_monsters or not alive_players:
            return

        await self.gm_say(gm("monster_moves"))

        for m in alive_monsters:
            # Find nearest player
            target = min(alive_players, key=lambda p: abs(p["pos"][0]-m["pos"][0]) + abs(p["pos"][1]-m["pos"][1]))

            # If taunted, target the taunter instead
            if self.taunted and self.taunted in self.players and self.players[self.taunted]["alive"]:
                target = self.players[self.taunted]

            # D20: monsters also attack only from cardinally adjacent tiles
            if self._cardinal_adjacent(m["pos"], target["pos"]):
                # Attack
                if self.smoke.get(m["id"]):
                    self.smoke.pop(m["id"])
                    await self.gm_say(f"💨 **{m['name']}** tenta atacar **{target['name']}** mas a fumaça confunde!")
                    continue
                if self.immune.get(target["id"], 0) > 0:
                    await self.gm_say(f"🛡️ **{m['name']}** ataca **{target['name']}** mas o Escudo Divino bloqueia!")
                    continue

                ac_bonus = self.temp_def.get(target["id"], 0)
                effective_ac = target["ac"] + ac_bonus
                hit, roll, total, crit = d20_attack(m["atk_bonus"], effective_ac)
                await self.broadcast({"type": "dice_roll", "die": "d20", "value": roll,
                                       "label": m["name"], "hit": hit, "crit": crit})
                if hit:
                    raw_dmg = roll_dice(m["damage"])
                    if crit: raw_dmg *= 2
                    dmg = max(1, raw_dmg)
                    die_type = "d" + m["damage"].split("d")[1]
                    await self.broadcast({"type": "dice_roll", "die": die_type,
                                           "value": raw_dmg, "label": "Dano"})
                    target["hp"] = max(0, target["hp"] - dmg)
                    crit_str = " **CRÍTICO!**" if crit else ""
                    await self.gm_say(
                        f"💢 **{m['name']}** ataca **{target['name']}**"
                        f" (d20={roll}+{m['atk_bonus']}={total} vs CA {effective_ac}):"
                        f"{crit_str} **{dmg}** de dano! ({target['hp']}/{target['max_hp']} HP)")
                    if target["hp"] <= 0:
                        await self._player_dies(target["id"])
                else:
                    await self.gm_say(
                        f"💢 **{m['name']}** ataca **{target['name']}**"
                        f" (d20={roll}+{m['atk_bonus']}={total} vs CA {effective_ac}): **ERROU!**")
            else:
                # Move toward player — cardinal only (no diagonal movement either)
                dx = 0 if m["pos"][0] == target["pos"][0] else (1 if target["pos"][0] > m["pos"][0] else -1)
                dy = 0 if m["pos"][1] == target["pos"][1] else (1 if target["pos"][1] > m["pos"][1] else -1)
                moved = False
                for adx, ady in [(dx, 0), (0, dy)]:
                    if adx == 0 and ady == 0:
                        continue
                    nx, ny = m["pos"][0]+adx, m["pos"][1]+ady
                    if not (0 <= nx < MAP_W and 0 <= ny < MAP_H and self.tiles[ny][nx] != WALL):
                        continue
                    # Don't stack on other monsters or players
                    if any(m2["hp"] > 0 and m2["pos"] == [nx, ny] for mid2, m2 in self.monsters.items() if mid2 != m["id"]):
                        continue
                    if any(p2["alive"] and p2["pos"] == [nx, ny] for p2 in self.players.values()):
                        continue
                    m["pos"] = [nx, ny]
                    moved = True
                    break

        self.taunted = None
        # Reset blessed ATK bonus
        for pid2 in list(self.blessed.keys()):
            self.players[pid2]["atk_bonus"] = self.players[pid2]["base_atk_bonus"]
        self.blessed.clear()

        # Restore moves for next round
        for pid2, p in self.players.items():
            if p["alive"]:
                p["moves_left"] = p["spd"]
                p["action_done"] = False

        # Check if all players dead
        if not any(p["alive"] for p in self.players.values()):
            await self.end_game(victory=False)

    # ── death & XP ─────────────────────────────────────────────────────────

    async def _monster_dies(self, m, killer_pid):
        if m["hp"] > 0: return
        xp, gold = m.get("xp", 0), m.get("gold", 0)
        alive_count = max(1, len([p for p in self.players.values() if p["alive"]]))
        share_xp = xp // alive_count

        # XP shared automatically — experience isn't a physical object
        for p in self.players.values():
            if p["alive"]:
                p["xp"] += share_xp
                await self._check_level_up(p)

        # Mark room cleared and spawn loot chest
        mroom = next((r for r in self.rooms if r["id"] == m.get("room_id")), None)
        if mroom:
            living_in_room = [mm for mm in self.monsters.values() if mm.get("room_id") == mroom["id"] and mm["hp"] > 0]
            if not living_in_room:
                mroom["cleared"] = True
                # Spawn loot chest at monster's death position
                loot_items = []
                if random.random() < 0.65:
                    loot_items.append(deepcopy(random.choice(CHEST_ITEMS)))
                if loot_items or gold > 0:
                    self._spawn_chest(list(m["pos"]), gold, loot_items)
                    await self.gm_say(f"💀 **{m['name']}** foi derrotado! +{share_xp} XP para todos! Um **baú de saque** apareceu!")
                else:
                    await self.gm_say(f"💀 **{m['name']}** foi derrotado! +{share_xp} XP para todos!")
            else:
                await self.gm_say(f"💀 **{m['name']}** foi derrotado! +{share_xp} XP para todos!")
        else:
            await self.gm_say(f"💀 **{m['name']}** foi derrotado! +{share_xp} XP para todos!")

        boss = m.get("boss", False)
        if boss:
            await self.end_game(victory=True)

    async def _player_dies(self, pid):
        p = self.players[pid]
        if not p["alive"]: return
        p["alive"] = False
        p["hp"] = 0
        await self.gm_say(f"💔 **{p['name']}** foi derrotado! Os companheiros devem continuar...")

        if not any(p["alive"] for p in self.players.values()):
            await self.end_game(victory=False)

    async def _check_level_up(self, p):
        threshold = p["level"] * 30
        if p["xp"] >= threshold:
            p["level"] += 1
            p["level_bonus"] = p["level"]   # level bonus = current level
            p["xp"] -= threshold
            p["max_hp"] += 4
            p["hp"] = min(p["max_hp"], p["hp"] + 4)
            p["atk_bonus"] += 1
            p["base_atk_bonus"] += 1
            p["ac"] += 1
            p["fort"] += 1
            p["ref_"] += 1
            p["will"] += 1
            p["max_mp"] += 2
            p["mp"] = min(p["max_mp"], p["mp"] + 2)
            await self.gm_say(f"⭐ **{p['name']}** subiu para o nível **{p['level']}**! +1 em Ataque, CA e Testes de Resistência!")

    async def end_game(self, victory):
        self.phase = "ended"
        text = gm("victory") if victory else gm("defeat")
        await self.gm_say(text)
        await self.broadcast({"type": "game_over", "victory": victory})

    # ── state serialisation ─────────────────────────────────────────────────

    def _is_turn(self, pid):
        return self.phase == "playing" and self.current_pid() == pid

    async def push_state(self):
        await self.broadcast({
            "type": "game_state",
            "tiles": self.tiles,
            "rooms": self.rooms,
            "players": list(self.players.values()),
            "monsters": [m for m in self.monsters.values() if m["hp"] > 0],
            "traps": [t for t in self.traps if not t["triggered"] and tuple(t["pos"]) in self.explored],
            "explored": [list(e) for e in self.explored],
            "stairs_pos": self.stairs_pos,
            "current_turn": self.current_pid(),
            "round": self.round_num,
            "gm_log": self.gm_log[-30:],
            "phase": self.phase,
            "chests": list(self.chests.values()),
        })

# ─── CONNECTION HANDLER ───────────────────────────────────────────────────────

rooms = {}  # type: dict  # plain dict for Python 3.7+ compatibility

def make_code():
    while True:
        code = "".join(random.choices(string.ascii_uppercase, k=4))
        if code not in rooms:
            return code

async def handler(ws):
    pid = new_id()
    room = None

    async def err(msg):
        await ws.send(json.dumps({"type": "error", "msg": msg}))

    try:
        async for raw in ws:
            try:
                msg = json.loads(raw)
            except Exception:
                continue

            t = msg.get("type")

            try:
                if t == "create_room":
                    name = (msg.get("name") or "Herói")[:20]
                    code = make_code()
                    room = GameRoom(code)
                    rooms[code] = room
                    await room.add_player(ws, pid, name)

                elif t == "join_room":
                    code = (msg.get("code") or "").upper()
                    name = (msg.get("name") or "Herói")[:20]
                    room = rooms.get(code)
                    if not room:
                        await err("Sala não encontrada.")
                        continue
                    if room.phase != "lobby":
                        await err("Jogo já iniciado.")
                        continue
                    ok = await room.add_player(ws, pid, name)
                    if not ok:
                        room = None

                elif t == "select_class":
                    if room: await room.select_class(pid, msg.get("class_id"))

                elif t == "start_game":
                    if room: await room.start_game(pid)

                elif t == "move":
                    if room: await room.handle_move(pid, msg.get("dx",0), msg.get("dy",0))

                elif t == "attack":
                    if room: await room.handle_attack(pid, msg.get("target_id"))

                elif t == "skill":
                    if room: await room.handle_skill(pid, msg.get("skill_id"), msg.get("target_id"))

                elif t == "use_item":
                    if room: await room.handle_use_item(pid, msg.get("item_id"))

                elif t == "end_turn":
                    if room: await room.handle_end_turn(pid)

                elif t == "shop_buy":
                    if room: await room.handle_shop_buy(pid, msg.get("shop"), msg.get("item_id"))

                elif t == "sell_item":
                    if room: await room.handle_shop_sell(pid, msg.get("item_slot"))

                elif t == "equip_from_bag":
                    if room: await room.handle_equip_from_bag(pid, int(msg.get("slot_index", -1)))

                elif t == "unequip":
                    if room: await room.handle_unequip(pid, msg.get("slot_key"))

                elif t == "take_from_chest":
                    if room: await room.handle_take_from_chest(
                        pid, msg.get("chest_id"), msg.get("kind"), msg.get("index", 0)
                    )

                elif t == "enter_dungeon":
                    if room: await room.enter_dungeon(pid)

                elif t == "exit_dungeon":
                    if room: await room.handle_exit_dungeon(pid)

                elif t == "get_city_state":
                    if room and room.phase == "city":
                        await room.broadcast_city_state()

            except Exception as e:
                # Never crash the connection on a handler error — report to client
                try:
                    await err(f"Erro interno: {type(e).__name__}")
                except Exception:
                    pass

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if room:
            room.connections.pop(pid, None)
            if pid in room.players and room.phase == "lobby":
                room.players.pop(pid, None)
                if room.host_pid == pid and room.players:
                    room.host_pid = next(iter(room.players))
                await room.broadcast_lobby()

# ─── MAIN ─────────────────────────────────────────────────────────────────────

async def main():
    # Force UTF-8 on Windows terminals (prevents UnicodeEncodeError with special chars)
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, TypeError):
        pass

    print("=" * 55)
    print("  LEGENDS FOR HIRE - Servidor WebSocket")
    print("=" * 55)
    print("  Endereco: ws://localhost:8765")
    print()
    print("  Para jogar na internet, instale o ngrok e execute:")
    print("    ngrok tcp 8765")
    print("  Compartilhe o endereco gerado com os jogadores.")
    print("=" * 55)

    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
