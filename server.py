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
import math
import mimetypes
import os
import random
import string
import sys
import time
from copy import deepcopy
from websockets.http11 import Response
from websockets.datastructures import Headers

# ─── MAP CONSTANTS ────────────────────────────────────────────────────────────

WALL  = 0
FLOOR = 1
DOOR  = 2
MAP_W = 30
MAP_H = 30
PRIS_HP = 12        # vida do prisioneiro (Fase 3)
OBJ_BONUS_XP = 50   # XP concedido por objetivo secundário cumprido (Fase 3)
OBJ_BONUS_OURO = 25 # ouro concedido por objetivo secundário cumprido (Fase 3)

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
    """Rola uma expressão de dados com múltiplos termos somados/subtraídos —
    cada termo é 'NdM' (rolagem) ou 'K' (constante).
    Ex.: '1d8', '2d6+3', '2d6+1d4-1', '1d6-2'."""
    s = str(die_str).strip().replace(' ', '')
    if not s:
        return 0
    total, i, n, sinal = 0, 0, len(s), 1
    while i < n:
        if s[i] in '+-':
            sinal = -1 if s[i] == '-' else 1
            i += 1
        j = i
        while j < n and s[j] not in '+-':
            j += 1
        termo, i = s[i:j], j
        if not termo:
            continue
        if 'd' in termo:
            a, _, b = termo.partition('d')
            cnt = int(a) if a else 1
            total += sinal * sum(random.randint(1, int(b)) for _ in range(cnt))
        else:
            total += sinal * int(termo)
        sinal = 1
    return total

def d20_attack(atk_bonus, target_ac):
    """Roll 1d20+atk_bonus vs target_ac. Returns (hit, roll, total, crit)."""
    roll = random.randint(1, 20)
    total = roll + atk_bonus
    crit = (roll == 20)
    return (crit or total >= target_ac), roll, total, crit

# ─── SOBREVIVÊNCIA — fome/sede unificado ─────────────────────────────────────
# O SERVIDOR é a fonte autoritativa, escala 0–100 (player["fome"], player["sede"],
# máximo SOBREVIVENCIA_MAX=100). Cliente e servidor usam a MESMA escala (0–100),
# então não há conversão (FATOR_CONVERSAO=1).
FATOR_CONVERSAO   = 1
SOBREVIVENCIA_MAX = 100           # valor máximo (escala 0–100)

def fome_sede_para_cliente(v):    # servidor (0–100) → cliente (0–100) — identidade
    return v * FATOR_CONVERSAO

def fome_sede_do_cliente(v):      # cliente (0–100) → servidor (0–100) — identidade
    return v / FATOR_CONVERSAO

# Tabela de consumo por tipo de ação (escala 0–100).
CONSUMO_ACOES = {
    'apenas_movimento':              {'fome': 0,   'sede': 1},   # caminhar: -1 sede (por turno; ver handle_move)
    'apenas_acao':                   {'fome': 1,   'sede': 0},   # ação principal (ex.: arremesso) ~ ataque básico
    'movimento_mais_acao':           {'fome': 1,   'sede': 1},
    'habilidade_especial':           {'fome': 1,   'sede': 2},
    'habilidade_especial_movimento': {'fome': 2,   'sede': 3},
    'acao_bonus':                    {'fome': 1,   'sede': 1},   # ação bônus: -1 fome E -1 sede
    'receber_dano':                  {'fome': 0,   'sede': 1},
    'descansar':                     {'fome': 1,   'sede': 0  },
}

# ─── SISTEMA DE DOENÇAS ────────────────────────────────────────────────────────
# Heróis contraem doenças (ex.: Infecção do Zumbi). Persistem até serem curadas
# por clérigo (Purificação) ou Templo. Cada "sintoma" é o PACOTE inteiro do nível.
# Severidade = nº de sintomas acumulados (leve→pesada→grave). Os deltas reais nos
# campos do jogador são guardados em p["doenca"]["deltas"] e revertidos na cura.
DOENCA_SEVERIDADE = {"leve": ["leve"], "pesada": ["leve", "medio"],
                     "grave": ["leve", "medio", "grave"]}
DOENCA_NIVEL_NOME = ["leve", "pesada", "grave"]
# Descrição textual dos sintomas (para o cliente).
DOENCA_SINTOMA_DESC = {
    "leve":  "-1 Reflexos, -1 Fortitude, -1 movimento",
    "medio": "-2 DES, -2 FOR, +1 fome/sede por ação",
    "grave": "-2 CON, -2 INT",
}

# ─── CANÇÃO HEROICA / PROVOCAÇÃO (Henrique, o Bardo) ──────────────────────────
# A Canção Heroica é um buff musical alternável (toggle). O bardo escolhe um
# subconjunto destes 5 atributos; cada um custa 1 de fome OU 1 de sede (ver
# `custo`), cobrado na ativação E como manutenção a cada turno do bardo. Os
# buffs afetam aliados num raio Chebyshev de CANCAO_RAIO.
CANCAO_ATRIBUTOS = [
    {"id": "acerto",      "label": "Acerto",      "custo": "sede",  "efeito": "bonus_acerto"},
    {"id": "dano",        "label": "Dano",        "custo": "fome",  "efeito": "bonus_dano"},
    {"id": "ca",          "label": "Armadura",    "custo": "sede",  "efeito": "bonus_ca"},
    {"id": "movimento",   "label": "Movimento",   "custo": "fome",  "efeito": "bonus_mov"},
    {"id": "resistencia", "label": "Resistência", "custo": "sede",  "efeito": "bonus_res"},
]

CANCAO_RAIO      = 5    # alcance (Chebyshev) dos buffs da canção
PROVOCACAO_RAIO  = 3    # alcance (Chebyshev) da Provocação
PROVOCACAO_TURNOS = 4   # 1 turno de desvantagem + 3 turnos de alvo forçado

def _calcular_custo_cancao(atributos_escolhidos):
    """Soma o custo de fome/sede dos atributos escolhidos (1 por atributo)."""
    custo = {"fome": 0, "sede": 0}
    for attr_id in atributos_escolhidos:
        attr = next((a for a in CANCAO_ATRIBUTOS if a["id"] == attr_id), None)
        if attr:
            custo[attr["custo"]] += 1
    return custo

def _distancia_chebyshev(pos1, pos2):
    """Distância de rei (Chebyshev) entre dois pontos [x, y]."""
    return max(abs(pos1[0] - pos2[0]), abs(pos1[1] - pos2[1]))

# ─── WEAPONS ──────────────────────────────────────────────────────────────────

WEAPONS = {
    # ── Corpo a Corpo ─────────────────────────────────────────────────────────
    "unarmed":       {"id": "unarmed",       "name": "Desarmado",            "die": None,   "stat": "str_"},
    # finesse=True → dano usa o melhor modificador entre FOR e DES (atributo
    # 'forcaOuDestreza' da spec).
    "dagger":        {"id": "dagger",        "name": "Adaga",                "die": "1d4",  "stat": "str_", "finesse": True, "throw_range": 3, "categoria": "perfurante"},
    # ── Armas iniciais da spec (EQUIPAMENTOS_INICIAIS) ──
    "machado_basico":{"id": "machado_basico","name": "Machado de Ferro",     "die": "1d6",  "stat": "str_", "categoria": "cortante"},
    "cajado_madeira":{"id": "cajado_madeira","name": "Cajado de Madeira",    "die": "1d6",  "stat": "str_", "reach": "cajado", "categoria": "contundente"},
    "instrumento":   {"id": "instrumento",   "name": "Instrumento Musical",  "die": None,   "stat": "dex"},
    "bordao":        {"id": "bordao",        "name": "Bordão",               "die": "1d6",  "stat": "str_", "categoria": "contundente"},
    "lanca_curta":   {"id": "lanca_curta",   "name": "Lança Curta",          "die": "1d6",  "stat": "str_", "throw_range": 5, "categoria": "perfurante"},
    # Lança: arma de ALCANCE corpo-a-corpo (reach="lanca" → 2 retos / 1 diagonal,
    # ver _lanca_no_alcance). NÃO é arma de duas mãos — pode usar escudo.
    "lanca":         {"id": "lanca",         "name": "Lança",                "die": "1d8",  "stat": "str_", "reach": "lanca", "categoria": "perfurante"},
    "maca":          {"id": "maca",          "name": "Maça",                 "die": "1d6",  "stat": "str_", "categoria": "contundente"},
    "chicote":       {"id": "chicote",       "name": "Chicote",              "die": "1d4",  "stat": "dex",  "range": 2, "categoria": "cortante"},
    "staff":         {"id": "staff",         "name": "Cajado Arcano",        "die": "1d6",  "stat": "str_", "reach": "cajado", "categoria": "contundente"},
    "shortsword":    {"id": "shortsword",    "name": "Espada Curta",         "die": "1d6",  "stat": "str_", "categoria": "cortante"},
    "longsword":     {"id": "longsword",     "name": "Espada Longa",         "die": "1d8",  "stat": "str_", "categoria": "cortante"},
    "warhammer":     {"id": "warhammer",     "name": "Martelo de Guerra",    "die": "1d8",  "stat": "str_", "categoria": "contundente"},
    "mangual":       {"id": "mangual",       "name": "Mangual",              "die": "1d8",  "stat": "str_", "categoria": "contundente"},
    "machado_duplo": {"id": "machado_duplo", "name": "Machado Duplo",        "die": "1d8",  "stat": "str_", "categoria": "cortante"},
    "bastsword":     {"id": "bastsword",     "name": "Espada Bastarda",      "die": "1d10", "stat": "str_", "categoria": "cortante"},
    # two_handed=True → não pode ser empunhada junto com escudo (ver _conflito_duas_maos).
    "machado_orc":   {"id": "machado_orc",   "name": "Machado de Guerra Órquico", "die": "1d10", "stat": "str_", "categoria": "cortante", "two_handed": True},
    "alabarda":      {"id": "alabarda",      "name": "Alabarda",             "die": "1d10", "stat": "str_", "range": 2, "categoria": "perfurante", "two_handed": True},
    "espada2m":      {"id": "espada2m",      "name": "Espada de 2 Mãos",    "die": "2d6",  "stat": "str_", "categoria": "cortante", "two_handed": True},
    # ── À Distância ───────────────────────────────────────────────────────────
    "arco_curto":    {"id": "arco_curto",    "name": "Arco Curto",           "die": "1d6",  "stat": "dex",  "range": 8,  "categoria": "perfurante"},
    "hand_crossbow": {"id": "hand_crossbow", "name": "Besta de Mão",         "die": "1d4",  "stat": "dex",  "range": 4,  "categoria": "perfurante"},
    "longbow":       {"id": "longbow",       "name": "Arco Longo",           "die": "1d8",  "stat": "dex",  "range": 12, "categoria": "perfurante"},
    "besta":         {"id": "besta",         "name": "Besta",                "die": "1d8",  "stat": "dex",  "range": 10, "categoria": "perfurante"},
}

# Armas de projétil → tipos de munição aceitos (básica e especial)
RANGED_AMMO = {
    "arco_curto":    ["flechas", "flechas_incendiarias"],
    "longbow":       ["flechas", "flechas_incendiarias"],
    "besta":         ["virotes", "virotes_incendiarios"],
    "hand_crossbow": ["virotes", "virotes_incendiarios"],
}

# ─── CHARACTER CLASSES ────────────────────────────────────────────────────────

CLASSES = {
    # ── D20 nível 1 — cada classe com atributos temáticos (16/14/12/10)
    # BAB: guerreiro/richard/arqueiro = +1 (cheio), outros = +0 (médio/baixo)
    # Saves: Bom = +2 base, Ruim = +0 base  |  atk_bonus = BAB + mod(STR)
    "warrior": {
        "name": "Guerreiro Anão", "emoji": "⚔️", "color": "#e74c3c",
        "hp": 14, "mp": 0, "max_mp": 0, "spd": 6, "start_gold": 20,   # warrior não usa mais mp — habilidades custam fome/sede
        "str_": 18, "dex": 10, "con_": 14, "int_": 8,
        "ac_base": 12, "weapon": "machado_basico", "atk_bonus": 5,  # BAB 1 + FOR mod(18)=+4; ac_base 12=10+couro+2 | Victor: Machado de Ferro (1d6 FOR)
        "saves_base": {"fort": 2, "ref": 0, "will": 0},          # Fort bom, Ref/Von ruins
        "desc": "Tanque resistente com golpes poderosos",
        "skills": [
            {
                "id":          "mira_certeira",
                "name":        "Mira Certeira",
                "description": "+2 no dado de acerto neste turno",
                "fome_cost":   0,
                "sede_cost":   2,
                "target":      "self",
                "icon":        "⚔️"
            },
            {
                "id":          "golpe_devastador",
                "name":        "Golpe Devastador",
                "description": "Dobra cada dado de dano neste turno",
                "fome_cost":   2,
                "sede_cost":   4,
                "target":      "self",
                "icon":        "💥"
            },
            {
                "id":          "furia_berserker",
                "name":        "Fúria Berserker",
                "description": "Ataque extra neste turno com habilidades ativas",
                "fome_cost":   5,
                "sede_cost":   5,
                "target":      "self",
                "icon":        "🔥"
            }
        ],
    },
    "mage": {
        "name": "Pedro, o Tímido", "emoji": "🔮", "color": "#9b59b6",
        "hp": 7, "mp": 22, "spd": 5, "start_gold": 20,
        "str_": 8, "dex": 12, "con_": 12, "int_": 18,
        "ac_base": 11, "weapon": "cajado_madeira", "atk_bonus": -1,  # BAB 0 + FOR mod(8)=-1; ac_base 11=10+manto+1 | Pedro: Cajado (1d6 FOR)
        "saves_base": {"fort": 0, "ref": 0, "will": 2},       # Von bom, Fort/Ref ruins
        "desc": "Devastador com magia, mas frágil",
        "skills": [
            {"id": "fireball",     "name": "Bola de Fogo",  "mp": 5, "desc": "4d6 fogo todos inimigos (CD15)",  "target": "all_enemies"},
            {"id": "ice_lance",    "name": "Lança de Gelo", "mp": 3, "desc": "3d6+FOR dano em 1 inimigo",       "target": "enemy"},
            {"id": "magic_shield", "name": "Escudo Mágico", "mp": 4, "desc": "+4 CA por 1 turno",               "target": "self"},
            # ── Metamagia (Pedro) — ações livres (toggles) que MODIFICAM a magia do
            # GRIMÓRIO lançada neste turno. Empilháveis; o custo só é cobrado ao
            # lançar e SÓ se a habilidade tiver efeito na magia. Mensagens dedicadas
            # (aprimorar_magia / estender_magia / fortalecer_magia).
            {
                "id": "aprimorar_magia",
                "name": "Aprimorar Magia",
                "description": "Ação livre. +1 na dificuldade (CD) do teste de resistência da magia. 🍖-3 ao lançar.",
                "icon": "🎯",
                "tipo": "acao_livre",
                "target": "self",
                "fome_cost": 3,
                "sede_cost": 0,
            },
            {
                "id": "estender_magia",
                "name": "Estender Magia",
                "description": "Ação livre. +1 turno na duração da magia. 🍖-3 💧-3 ao lançar.",
                "icon": "⏱️",
                "tipo": "acao_livre",
                "target": "self",
                "fome_cost": 3,
                "sede_cost": 3,
            },
            {
                "id": "fortalecer_magia",
                "name": "Fortalecer Magia",
                "description": "Ação livre. Multiplica o dano da magia por 1,5. 🍖-6 💧-6 ao lançar.",
                "icon": "💥",
                "tipo": "acao_livre",
                "target": "self",
                "fome_cost": 6,
                "sede_cost": 6,
            },
        ],
    },
    "rogue": {
        "name": "Luccas, o Astuto", "emoji": "🗡️", "color": "#2ecc71",
        "hp": 9, "mp": 0, "max_mp": 0, "spd": 7, "start_gold": 20,   # Luccas não usa MP — habilidades custam fome/sede
        "str_": 10, "dex": 18, "con_": 12, "int_": 10,
        "ac_base": 14, "weapon": "dagger", "atk_bonus": 4,   # BAB 0 + DES mod(18)=+4; ac_base 14=10+couro+DES
        "saves_base": {"fort": 0, "ref": 2, "will": 0},       # Ref bom, Fort/Von ruins
        "desc": "Veloz, detecta armadilhas, golpe furtivo",
        "skills": [
            {
                "id": "ataque_furtivo",
                "name": "Ataque Furtivo",
                "description": "Passiva. +2d4 dano extra quando há aliado adjacente ao alvo (ou se estiver invisível). +1d4 por faixa de nível.",
                "icon": "🗡️",
                "tipo": "passiva",
                "target": "self",
                "fome_cost": 0,
                "sede_cost": 0,
            },
            {
                "id": "detectar_armadilhas",
                "name": "Detectar Armadilhas",
                "description": "Ação bônus (alternável). Revela armadilhas próximas e não dispara as da masmorra. Manutenção 💧-1/turno.",
                "icon": "🔍",
                "tipo": "acao_bonus",
                "target": "self",
                "fome_cost": 0,
                "sede_cost": 0,
                "sede_manutencao": 1,
            },
            {
                "id": "esconder_sombras",
                "name": "Esconder nas Sombras",
                "description": "Ação bônus. d20+DES vs percepção dos monstros. Invisível (não é alvo) enquanto ativo. Manutenção 🍖-1 💧-1/turno.",
                "icon": "🌑",
                "tipo": "acao_bonus",
                "target": "self",
                "fome_cost": 2,
                "sede_cost": 1,
                "fome_manutencao": 1,
                "sede_manutencao": 1,
            },
            {
                "id": "veneno_rapido",
                "name": "Veneno Rápido",
                "description": "Ação livre. Unta um veneno da bolsa na arma — os próximos golpes certeiros envenenam o alvo.",
                "icon": "☠️",
                "tipo": "acao_livre",
                "target": "self",
                "fome_cost": 0,
                "sede_cost": 1,
            },
            {
                "id": "criar_armadilha",
                "name": "Criar Armadilha",
                "description": "Ação principal. Coloca uma armadilha na própria casa ou adjacente. Custa fome/sede + ouro.",
                "icon": "🪤",
                "tipo": "acao_principal",
                "target": "tile",
                "fome_cost": 2,
                "sede_cost": 1,
            },
        ],
    },
    "cleric": {
        "name": "Frade Lewis", "emoji": "✨", "color": "#f39c12",
        "hp": 10, "mp": 0, "spd": 5, "start_gold": 20,   # Lewis não usa MP — milagres custam fome/sede
        "str_": 10, "dex": 10, "con_": 14, "int_": 16,
        "ac_base": 11, "weapon": "cajado_madeira", "atk_bonus": 0,   # BAB 0 + FOR mod(10)=0; ac_base 11=10+couro+1 | Lewis: Cajado (1d6 FOR)
        "saves_base": {"fort": 2, "ref": 0, "will": 2},       # Fort e Von bons, Ref ruim
        "desc": "Frade que canaliza milagres — cura, purifica e ressuscita aliados",
        "skills": [
            {
                "id": "cura",
                "name": "Cura",
                "description": "1d8 a 3d8 + INT em um aliado. 💧-1 por dado. Alcance estendível com 🍖.",
                "icon": "🙌",
                "tipo": "acao_principal",
                "target": "ally",
                "fome_cost": 0,
                "sede_cost": 1,
            },
            {
                "id": "cura_area",
                "name": "Cura em Área",
                "description": "1d8 a 3d8 + INT em todos os aliados no raio 5. 🍖-4 💧-4 por dado.",
                "icon": "🌟",
                "tipo": "acao_principal",
                "target": "area",
                "fome_cost": 4,
                "sede_cost": 4,
            },
            {
                "id": "purificacao",
                "name": "Purificação",
                "description": "Remove veneno, doença, maldição ou petrificação de um aliado adjacente.",
                "icon": "✨",
                "tipo": "acao_principal",
                "target": "ally",
                "fome_cost": 1,
                "sede_cost": 0,
            },
            {
                "id": "ressurreicao",
                "name": "Ressurreição",
                "description": "Traz um aliado morto adjacente de volta com 1 HP. 🍖-10 💧-10.",
                "icon": "💫",
                "tipo": "acao_principal",
                "target": "ally",
                "fome_cost": 10,
                "sede_cost": 10,
            },
        ],
    },
    "bard": {
        "name": "Henrique, o Bardo", "emoji": "🎶", "color": "#9b7fd4",
        "hp": 9, "mp": 0, "max_mp": 0, "spd": 6, "start_gold": 20,   # bardo não usa MP — habilidades custam fome/sede
        "str_": 10, "dex": 16, "con_": 12, "int_": 12,
        "ac_base": 13, "weapon": "instrumento", "atk_bonus": 3,   # BAB 0 + DES mod(16)=+3; ac_base 13 inclui manto+1 | Henrique: Instrumento (sem dano) + Adaga 2ª mão
        "saves_base": {"fort": 0, "ref": 2, "will": 2},           # Ref e Von bons, Fort ruim
        "desc": "Músico que inspira aliados com canções e provoca inimigos",
        "skills": [
            {
                "id": "cancao_heroica",
                "name": "Canção Heroica",
                "description": "Ativa buffs musicais para aliados em raio de 5 quadrados",
                "icon": "🎵",
                "tipo": "cancao",
                "target": "self",
                "fome_cost": 0,
                "sede_cost": 0,
            },
            {
                "id": "provocacao",
                "name": "Provocação",
                "description": "Impõe desvantagem ao inimigo e o força a atacar Henrique por 3 turnos",
                "icon": "😤",
                "tipo": "debuff",
                "target": "enemy",
                "fome_cost": 3,
                "sede_cost": 3,
            },
        ],
        "habilidade_passiva": {
            "id": "conhecimento_lendas",
            "name": "Conhecimento das Lendas",
            "description": "Revela a ficha completa de qualquer inimigo ao passar o mouse",
            "icon": "📖",
            "tipo": "passiva",
        },
    },
    "paladin": {
        "name": "Richard, o Cavaleiro", "emoji": "🛡️", "color": "#3498db",
        "hp": 12, "mp": 0, "max_mp": 0, "spd": 6, "start_gold": 20,   # paladino não usa MP — habilidades custam fome/sede
        "str_": 16, "dex": 10, "con_": 14, "int_": 10,
        "ac_base": 14, "weapon": "shortsword", "atk_bonus": 4,  # BAB 1 + FOR mod(16)=+3; ac_base 14=10+cota+0
        "saves_base": {"fort": 2, "ref": 0, "will": 2},          # Fort e Von bons, Ref ruim
        "desc": "Aço e honra forjados na mesma bigorna. Não conhece recuo.",
        "skills": [
            {
                "id": "imposicao_maos",
                "name": "Imposição das Mãos",
                "description": "Cura 1d6 + bônus Força em aliado adjacente",
                "icon": "🙏",
                "tipo": "cura",
                "target": "ally",
                "fome_cost": 3,
                "sede_cost": 2,
            },
            {
                "id": "golpe_sagrado",
                "name": "Golpe Sagrado",
                "description": "+1d8 dano sagrado. Dobrado contra mortos-vivos e demônios",
                "icon": "⚔️",
                "tipo": "buff_ativo",
                "target": "self",
                "fome_cost": 3,
                "sede_cost": 3,
                "fome_manutencao": 1,
                "sede_manutencao": 1,
            },
            {
                "id": "protetor",
                "name": "Protetor",
                "description": "Aliado recebe metade do dano. A outra metade vai para Richard",
                "icon": "🛡️",
                "tipo": "buff_aliado",
                "target": "ally",
                "fome_cost": 2,
                "sede_cost": 2,
                "fome_manutencao": 1,
                "sede_manutencao": 0,
            },
            {
                "id": "regeneracao_divina",
                "name": "Regeneração Divina",
                "description": "Recupera 1 HP por turno até HP máximo",
                "icon": "✨",
                "tipo": "acao_livre",
                "target": "self",
                "fome_cost": 2,
                "sede_cost": 1,
                "fome_manutencao": 1,
                "sede_manutencao": 1,
            },
            {
                "id": "guerreiro_luz",
                "name": "Guerreiro da Luz",
                "description": "+1/+2 em Visão, Ataque, Dano e CA. Apenas Richard",
                "icon": "💡",
                "tipo": "acao_livre",
                "target": "self",
                "fome_cost": 0,
                "sede_cost": 0,
            },
        ],
    },
}

# ─── DAMAGE TYPES ─────────────────────────────────────────────────────────────
# Usado em ataques de heróis/monstros e habilidades especiais.
# Armas brancas = "physical". Magias têm subtipo: ("magic", "fire"), etc.
DMG_PHYSICAL  = "physical"
DMG_FIRE      = "fire"
DMG_COLD      = "cold"
DMG_LIGHTNING = "lightning"
DMG_HOLY      = "holy"
DMG_POISON    = "poison"
DMG_MAGIC     = "magic"

# Normaliza nomes de elemento (PT, usados nas magias) → chave de damage type acima,
# para aplicar fraquezas/imunidades elementais via _apply_damage_types.
_NORM_ELEMENTO = {
    "fogo": DMG_FIRE, "fire": DMG_FIRE, "chamas": DMG_FIRE, "flames": DMG_FIRE,
    "frio": DMG_COLD, "gelo": DMG_COLD, "cold": DMG_COLD,
    "eletricidade": DMG_LIGHTNING, "raio": DMG_LIGHTNING, "relampago": DMG_LIGHTNING,
    "lightning": DMG_LIGHTNING,
    "sagrado": DMG_HOLY, "holy": DMG_HOLY, "luz": DMG_HOLY, "light": DMG_HOLY,
    "veneno": DMG_POISON, "poison": DMG_POISON,
    "fisico": DMG_PHYSICAL, "physical": DMG_PHYSICAL,
    "magico": DMG_MAGIC, "magic": DMG_MAGIC,
}

# ─── CORROSÃO DE EQUIPAMENTOS (Devorador Orgânico) ──────────────────────────
# Sistema LEVE / RUNTIME: itens equipados orgânicos acumulam um "nível de dano"
# (0=intacto, 1=danificado, 2=quebrado, 3=destruído). As penalidades são
# aplicadas em tempo de combate (CA / acerto / dano) e o estado é RESETADO ao
# entrar em nova dungeon: níveis 1-2 são REPARADOS; nível 3 (destruído) é
# PERMANENTE (não volta). Estado vive em p["corrosao"] e p["corrosao_viva"].
CORROSAO_ARMADURA_ORGANICA = {"leather", "cloak"}   # couro / manto (tecido)
CORROSAO_ARMA_MADEIRA = {"cajado_madeira", "bordao", "staff", "instrumento",
                         "arco_curto", "longbow", "besta", "hand_crossbow"}
# Devorador de Metal: corrói metal (madeira/couro/ossos são imunes).
CORROSAO_ARMADURA_METAL = {"chainmail", "bronze_armor", "plate", "fullplate"}
CORROSAO_ARMA_METAL = {"dagger", "machado_basico", "machado_duplo", "machado_orc",
                       "sword", "magic_sword", "shortsword", "longsword",
                       "bastsword", "espada2m", "warhammer", "mangual", "maca"}
CORROSAO_NIVEL_NOME = {1: "danificado", 2: "quebrado", 3: "destruído"}

MONSTER_DEFS = [
    # ── Placeholders (sistema legado) ─────────────────────────────────────────
    # TODO: Substituir por monstros reais com fichas completas
    {"type": "goblin",    "name": "Goblin",         "emoji": "👺", "hp": 8,  "ac": 12, "atk_bonus": 2,  "damage": "1d4", "xp": 10,  "gold": 5,   "tier": 1},
    {"type": "skeleton",  "name": "Esqueleto",      "emoji": "💀", "hp": 10, "ac": 13, "atk_bonus": 3,  "damage": "1d6", "xp": 15,  "gold": 8,   "tier": 1, "undead": True},
    {"type": "orc",       "name": "Orc",            "emoji": "👹", "hp": 16, "ac": 14, "atk_bonus": 5,  "damage": "1d8", "xp": 25,  "gold": 12,  "tier": 2},
    {"type": "dark_mage", "name": "Mago das Trevas","emoji": "🧟", "hp": 12, "ac": 12, "atk_bonus": 4,  "damage": "1d6", "xp": 30,  "gold": 20,  "tier": 2},
    {"type": "troll",     "name": "Troll",          "emoji": "🗿", "hp": 22, "ac": 16, "atk_bonus": 7,  "damage": "1d10","xp": 40,  "gold": 25,  "tier": 3},
    {"type": "dragon",    "name": "Dragão Ancião",  "emoji": "🐉", "hp": 60, "ac": 20, "atk_bonus": 12, "damage": "2d8", "xp": 200, "gold": 100, "tier": 4, "boss": True},
    # ── Monstros com ficha completa ───────────────────────────────────────────
    # Campo "porte": categoria de tamanho VISUAL da miniatura (guia a escala do
    # sprite no cliente — distinto de "size", que é o footprint no grid).
    # Valores: "minusculo" | "pequeno" | "medio" | "grande" | "enorme".
    # O cliente mapeia para um fator de escala (_PORTE_FATOR em game.js);
    # ausente ou desconhecido = "medio" (1.0). Ex.: kobolds são "pequeno".
    {
        "type": "aranha_sombria", "name": "Aranha Sombria", "emoji": "🕷️",
        "tier": 1, "cr": 0.25,
        "hp": 8, "ac": 13, "size": [1, 1], "movement": 7,
        "str_": 8, "dex": 16, "con_": 10, "int_": 2,
        "fort": 2, "ref_": 5, "will": -4,
        "attacks": [
            {"name": "Mordida", "atk_bonus": 1, "damage": "1d4-1",
             "damage_types": ["physical"], "num_attacks": 1,
             "on_hit": "veneno_aranha_sombria"},
        ],
        "special_abilities": [
            {"id": "disparo_teia", "name": "Disparo de Teia",
             "action_type": "acao", "uses_per_combat": 1,
             "range": 4, "target": "single",
             "dc": 11, "save": "reflexos",
             "damage": None, "damage_types": [],
             "effect": "perde_turno", "effect_duration": 1},
        ],
        "immunities": [],
        "weaknesses": [{"type": "physical", "categoria": "contundente", "bonus_flat": 2}],
        "loot_table": {"1-50": None, "51-100": {"tipo": "item", "id": "veneno_aranha_sombria"}},
        "spawn_min": 1, "spawn_max": 3,
        "ai_type": "emboscador",
        "porte": "medio",
        "image": "aranhasombria",
        "undead": False, "boss": False,
    },
    {
        "type": "escorpiao_pedra", "name": "Escorpião de Pedra", "emoji": "🦂",
        "tier": 1, "cr": 0.5,
        "hp": 12, "ac": 14, "size": [1, 1], "movement": 5,
        "str_": 10, "dex": 12, "con_": 12, "int_": 1,
        "fort": 4, "ref_": 3, "will": 0,
        "attacks": [
            {"name": "Pinça",  "atk_bonus": 2, "damage": "1d4",
             "damage_types": ["physical"], "num_attacks": 2, "on_hit": None},
            {"name": "Ferrão", "atk_bonus": 2, "damage": "1d4",
             "damage_types": ["physical"], "num_attacks": 1,
             "on_hit": "veneno_escorpiao_pedra"},
        ],
        "special_abilities": [
            {"id": "veneno_ferrao", "name": "Veneno do Ferrão",
             "action_type": "passiva",
             "dc": 9, "save": "fortitude",
             "effect": "penalidade_ataque_movimento"},
        ],
        "immunities": [],
        "weaknesses": [{"type": "physical", "categoria": "contundente", "bonus_flat": 2}],
        "loot_table": {"1-60": {"tipo": "item", "id": "veneno_escorpiao_pedra"}, "61-100": None},
        "spawn_min": 1, "spawn_max": 2,
        "ai_type": "agressivo",
        "porte": "medio",
        "image": "escorpiaodepedra",
        "undead": False, "boss": False,
    },
    # ── Esqueleto Humano ──────────────────────────────────────────────────────
    {
        "type": "esqueleto_humano", "name": "Esqueleto Humano", "emoji": "💀",
        "tier": 1, "cr": 0.5,
        "hp": 10, "ac": 12, "size": [1, 1], "movement": 5,
        "str_": 10, "dex": 12, "con_": 10, "int_": 2,
        "fort": 2, "ref_": 3, "will": 0,
        "darkvision_range": 4,
        "attacks": [
            # Arma definida em make_monster (roll 1d100 na criação)
            {"name": "Espada Curta", "atk_bonus": 2, "damage": "1d6",
             "damage_types": ["physical"], "num_attacks": 1, "on_hit": None,
             "categoria": "cortante"},
        ],
        "special_abilities": [
            {"id": "sem_dor",          "name": "Sem Dor",         "action_type": "passiva"},
            {"id": "corpo_inerte",     "name": "Corpo Inerte",    "action_type": "passiva"},
            {"id": "fraqueza_magica",  "name": "Fraqueza Mágica", "action_type": "passiva",
             "descricao": "-2 em testes contra magias que controlam mortos-vivos"},
        ],
        "immunities": ["veneno", "controle_mental"],
        "weaknesses": [
            {"type": "physical", "categoria": "perfurante",  "bonus_flat": -2,
             "descricao": "Resistência a perfurante (-2 dano)"},
            {"type": "physical", "categoria": "cortante",    "bonus_flat": -1,
             "descricao": "Resistência a cortante (-1 dano)"},
            {"type": "physical", "categoria": "contundente", "bonus_flat": 2,
             "descricao": "Vulnerável a impacto (+2 dano)"},
            {"type": "sagrado",  "multiplier": 2,
             "descricao": "Dano sagrado dobrado"},
        ],
        "min_damage": 1,
        "loot_table": {
            "1-70":  None,
            "71-90": {"tipo": "gold", "valor": 2},
            "91-100": {"tipo": "gold", "valor": 4},
        },
        "spawn_min": 1, "spawn_max": 3,
        "ai_type": "esqueleto_humano",
        "porte": "medio",
        "image": "esqueletoHumano",
        "undead": True, "boss": False,
    },
    # ── Esqueleto Animal ──────────────────────────────────────────────────────
    {
        "type": "esqueleto_animal", "name": "Esqueleto Animal", "emoji": "🦴",
        "tier": 1, "cr": 0.5,
        "hp": 8, "ac": 13, "size": [1, 1], "movement": 6,
        "str_": 12, "dex": 14, "con_": 10, "int_": 2,
        "fort": 2, "ref_": 4, "will": 0,
        "darkvision_range": 8,
        "attacks": [
            {"name": "Mordida", "atk_bonus": 4, "damage": "1d6+2",
             "damage_types": ["physical"], "num_attacks": 1, "on_hit": None,
             "categoria": "perfurante"},
        ],
        "special_abilities": [
            {"id": "movimento_erratico", "name": "Movimento Errático", "action_type": "passiva",
             "descricao": "Ignora terreno difícil — avança sem hesitar"},
            {"id": "sem_instinto",       "name": "Sem Instinto",       "action_type": "passiva",
             "descricao": "Nunca foge nem recua — avança até ser destruído"},
            {"id": "fraqueza_magica",    "name": "Fraqueza Mágica",    "action_type": "passiva",
             "descricao": "-2 em testes contra magias que controlam mortos-vivos"},
        ],
        "immunities": ["veneno", "controle_mental"],
        "weaknesses": [
            {"type": "physical", "categoria": "perfurante",  "bonus_flat": -2,
             "descricao": "Resistência a perfurante (-2 dano)"},
            {"type": "physical", "categoria": "cortante",    "bonus_flat": -1,
             "descricao": "Resistência a cortante (-1 dano)"},
            {"type": "physical", "categoria": "contundente", "bonus_flat": 2,
             "descricao": "Vulnerável a impacto (+2 dano)"},
            {"type": "sagrado",  "multiplier": 2,
             "descricao": "Dano sagrado dobrado"},
        ],
        "min_damage": 1,
        "loot_table": {"1-100": None},
        "spawn_min": 1, "spawn_max": 3,
        "ai_type": "esqueleto_animal",
        "porte": "medio",
        "image": "esqueletoAnimal",
        "undead": True, "boss": False,
    },
    # ── Lobo Cinzento ─────────────────────────────────────────────────────────
    {
        "type": "lobo_cinzento", "name": "Lobo Cinzento", "emoji": "🐺",
        "tier": 1, "cr": 0.5,
        "hp": 16, "ac": 13, "size": [1, 1], "movement": 8,
        "str_": 14, "dex": 14, "con_": 12, "int_": 2,
        "fort": 4, "ref_": 4, "will": 1,
        "attacks": [
            {"name": "Mordida", "atk_bonus": 4, "damage": "1d6+2",
             "damage_types": ["physical"], "num_attacks": 1, "on_hit": None},
        ],
        "special_abilities": [
            {"id": "caca_em_bando", "name": "Caça em Bando",   "action_type": "passiva"},
            {"id": "derrubar",      "name": "Derrubar",         "action_type": "passiva",
             "dc": 11, "save": "reflexos"},
        ],
        "immunities": [],
        "weaknesses": [
            {"type": "save_penalty", "save": "fortitude", "bonus_flat": -2,
             "descricao": "Sensível a venenos — -2 Fort vs venenos"},
        ],
        "loot_table": {"1-100": None},
        "spawn_min": 2, "spawn_max": 4,
        "ai_type": "lobo_cinzento",
        "porte": "medio",
        "image": "loboCinzento",
        "undead": False, "boss": False,
    },
    # ── Crocodilo Jovem (ND 1) ───────────────────────────────────────────────
    {
        "type": "crocodilo_jovem", "name": "Crocodilo Jovem", "emoji": "🐊",
        "tier": 1, "cr": 1,
        "hp": 16, "ac": 13, "size": [2, 1], "oriented": True, "movement": 6,
        "str_": 16, "dex": 10, "con_": 14, "int_": 2,
        "fort": 5, "ref_": 2, "will": 1,
        "attacks": [
            {"name": "Mordida", "atk_bonus": 5, "damage": "1d8+3",
             "damage_types": ["physical"], "num_attacks": 1, "on_hit": None,
             "categoria": "perfurante"},
        ],
        "special_abilities": [
            {"id": "agarrar",         "name": "Agarrar",          "action_type": "passiva",
             "dc": 12, "save": "fortitude",
             "descricao": "Ao acertar, alvo testa FOR ou REF CD 12 — falha: preso"},
            {"id": "atq_mandibula",   "name": "Ataque de Mandíbula", "action_type": "passiva",
             "descricao": "Se alvo preso e adjacente: 1d8+3 dano direto (sem rolagem de acerto)"},
            {"id": "arrastar",        "name": "Arrastar",          "action_type": "passiva",
             "descricao": "Move alvo preso junto ao se deslocar"},
        ],
        "immunities": [],
        "weaknesses": [
            {"type": DMG_LIGHTNING, "multiplier": 1.5,
             "descricao": "+50% dano elétrico (dobrado na água)"},
        ],
        "loot_table": {"1-100": None},
        "spawn_min": 1, "spawn_max": 2,
        "ai_type": "crocodilo_jovem",
        "porte": "medio",
        "image": "crocodiloJovem",
        "undead": False, "boss": False,
    },
    # ── Cobra Constritora (ND 1) ─────────────────────────────────────────────
    {
        "type": "cobra_constritora", "name": "Cobra Constritora", "emoji": "🐍",
        "tier": 1, "cr": 1,
        "hp": 14, "ac": 12, "size": [1, 1], "movement": 7,
        "str_": 14, "dex": 14, "con_": 12, "int_": 1,
        "fort": 4, "ref_": 4, "will": 1,
        "attacks": [
            {"name": "Mordida", "atk_bonus": 4, "damage": "1d6+2",
             "damage_types": ["physical"], "num_attacks": 1, "on_hit": None,
             "categoria": "perfurante"},
        ],
        "special_abilities": [
            {"id": "constricao",      "name": "Constrição",       "action_type": "passiva",
             "dc": 11, "save": "fortitude", "escape_saves": ["fortitude"],
             "descricao": "Ao acertar, alvo testa FOR CD 11 — falha: preso"},
            {"id": "esmagar",         "name": "Esmagar",          "action_type": "passiva",
             "descricao": "Enquanto preso e adjacente: 1d6 dano automático por turno"},
        ],
        "immunities": [],
        "weaknesses": [
            {"type": "physical", "categoria": "cortante", "bonus_flat": 2,
             "descricao": "Corpo vulnerável a corte (+2 dano cortante)"},
        ],
        "loot_table": {"1-100": None},
        "spawn_min": 1, "spawn_max": 2,
        "ai_type": "cobra_constritora",
        "porte": "grande",
        "image": "cobraConstritora",
        "undead": False, "boss": False,
    },
    # ── Cobra Venenosa (ND 1) ────────────────────────────────────────────────
    {
        "type": "cobra_venenosa", "name": "Cobra Venenosa", "emoji": "🐍",
        "tier": 1, "cr": 1,
        "hp": 14, "ac": 13, "size": [1, 1], "movement": 6,
        "str_": 10, "dex": 14, "con_": 12, "int_": 1,
        "fort": 3, "ref_": 4, "will": 1,
        "attacks": [
            {"name": "Mordida", "atk_bonus": 4, "damage": "1d6+2",
             "damage_types": ["physical"], "num_attacks": 1,
             "on_hit": "veneno_cobra_cuspidora", "categoria": "perfurante"},
        ],
        "special_abilities": [
            {"id": "veneno",            "name": "Veneno",           "action_type": "passiva",
             "descricao": "Ao acertar a mordida, aplica veneno (doença leve)"},
            {"id": "ataque_rapido",     "name": "Ataque Rápido",    "action_type": "passiva",
             "descricao": "Se não se mover no turno: +1 no ataque"},
            {"id": "camuflagem_natural","name": "Camuflagem Natural","action_type": "passiva",
             "descricao": "+2 CA contra o primeiro ataque em terreno natural"},
        ],
        "immunities": [],
        "weaknesses": [
            {"type": "physical", "categoria": "contundente", "bonus_flat": 1,
             "descricao": "Corpo frágil (+1 dano de concussão)"},
        ],
        "loot_table": {
            "1-90":  None,
            "91-100": {"tipo": "item", "id": "veneno_cobra_cuspidora"},
        },
        "spawn_min": 1, "spawn_max": 2,
        "ai_type": "cobra_venenosa",
        "porte": "medio",
        "image": "cobraVenenosa",
        "undead": False, "boss": False,
    },
    # ── Devorador Orgânico (ND 1) ────────────────────────────────────────────
    {
        "type": "devorador_organico", "name": "Devorador Orgânico", "emoji": "🟢",
        "tier": 1, "cr": 1,
        "hp": 16, "ac": 11, "size": [1, 1], "movement": 5,
        "str_": 12, "dex": 10, "con_": 12, "int_": 2,
        "fort": 3, "ref_": 2, "will": 1,
        "attacks": [
            {"name": "Toque Corrosivo", "atk_bonus": 3, "damage": "1d6+1",
             "damage_types": ["physical"], "num_attacks": 1, "on_hit": None,
             "categoria": "contundente"},
        ],
        "special_abilities": [
            {"id": "toque_putrefato",  "name": "Toque Putrefato",  "action_type": "passiva",
             "descricao": "Ao acertar: +1 nível de dano em equipamento orgânico do alvo (couro/madeira/tecido)"},
            {"id": "corrosao_viva",    "name": "Corrosão Viva",    "action_type": "passiva",
             "descricao": "Alvo sem armadura: 1 dano/turno por 2 turnos (acumula a cada acerto)"},
            {"id": "absorver_materia", "name": "Absorver Matéria", "action_type": "passiva",
             "descricao": "Quando destrói um item orgânico: recupera 1d4 HP"},
        ],
        "immunities": ["cegueira", "escuridao"],
        "weaknesses": [
            {"type": "fire", "multiplier": 2,
             "descricao": "Combustão rápida (dano de fogo dobrado)"},
        ],
        "loot_table": {
            "1-40":   None,
            "41-80":  {"tipo": "gold", "valor": "1d2"},
            "81-100": {"tipo": "gold", "valor": "1d6"},
        },
        "spawn_min": 1, "spawn_max": 2,
        "ai_type": "devorador_organico",
        "porte": "medio",
        "image": "devoradorOrganico",
        "undead": False, "boss": False,
    },
    # ── Urso Negro (ND 1) ────────────────────────────────────────────────────
    {
        "type": "urso_negro", "name": "Urso Negro", "emoji": "🐻",
        "tier": 1, "cr": 1,
        "hp": 18, "ac": 13, "size": [1, 1], "movement": 6,
        "str_": 18, "dex": 12, "con_": 14, "int_": 2,
        "fort": 5, "ref_": 3, "will": 1,
        "attacks": [
            {"name": "Mordida", "atk_bonus": 6, "damage": "1d8+4",
             "damage_types": ["physical"], "num_attacks": 1, "on_hit": None,
             "categoria": "perfurante"},
            {"name": "Garra",   "atk_bonus": 6, "damage": "1d6+4",
             "damage_types": ["physical"], "num_attacks": 1, "on_hit": None,
             "categoria": "cortante"},
        ],
        "special_abilities": [
            {"id": "furia", "name": "Fúria", "action_type": "passiva",
             "descricao": "Com HP < 50%: +2 de dano em todos os ataques"},
        ],
        "immunities": [],
        "weaknesses": [
            {"type": "physical", "categoria": "perfurante", "bonus_flat": 1,
             "descricao": "Corpo massivo: +1 dano de perfuração/alcance (arcos, bestas, lanças)"},
            {"type": "physical", "categoria": "contundente", "bonus_flat": -1,
             "descricao": "Corpo massivo: -1 dano de concussão (martelos, maças, bastões)"},
        ],
        "loot_table": {"1-100": None},
        "spawn_min": 1, "spawn_max": 1,
        "ai_type": "agressivo",
        "porte": "grande",
        "image": "ursoNegro",
        "undead": False, "boss": False,
    },
    # ── Orc Guerreiro (ND 1) ─────────────────────────────────────────────────
    {
        "type": "orc_guerreiro", "name": "Orc Guerreiro", "emoji": "👹",
        "tier": 1, "cr": 1,
        "hp": 17, "ac": 13, "size": [1, 1], "movement": 6,
        "str_": 16, "dex": 12, "con_": 14, "int_": 8,
        "fort": 5, "ref_": 3, "will": 1,
        "attacks": [
            {"name": "Machado", "atk_bonus": 5, "damage": "1d10+3",
             "damage_types": ["physical"], "num_attacks": 1, "on_hit": None,
             "categoria": "cortante"},
        ],
        "special_abilities": [
            {"id": "investida_brutal", "name": "Investida Brutal", "action_type": "passiva",
             "descricao": "Se mover antes de atacar: +2 de dano"},
            {"id": "furia_cega",       "name": "Fúria Cega",       "action_type": "passiva",
             "descricao": "Se sofreu dano na rodada anterior: +1 de dano, mas -1 CA"},
            {"id": "mente_limitada",   "name": "Mente Limitada",   "action_type": "passiva",
             "descricao": "-1 em testes de Vontade contra efeitos mentais"},
        ],
        "immunities": [],
        "weaknesses": [
            {"type": "save_penalty", "save": "vontade", "bonus_flat": -1, "em_magia": True,
             "descricao": "Mente limitada: -1 em Vontade contra efeitos mentais"},
        ],
        "loot_table": {
            "1-40":   None,
            "41-70":  {"tipo": "gold", "valor": 2},
            "71-90":  {"tipo": "gold", "valor": 4},
            "91-100": {"tipo": "gold", "valor": 6},
        },
        "guaranteed_loot": ["machado_orc"],   # "arma equipada" — sempre dropa
        "spawn_min": 1, "spawn_max": 2,
        "ai_type": "orc_guerreiro",
        "porte": "medio",
        "image": "orcGuerreiro",
        "undead": False, "boss": False,
    },
    # ── Goblins das Fendas (base: HP 9 / CA 13 / Mov 6) ──────────────────────
    # Fraqueza compartilhada — Mente Fraca: -2 em Vontade vs controle mental.
    {
        "type": "goblin_arqueiro", "name": "Goblin Arqueiro", "emoji": "👺",
        "tier": 1, "cr": 0.25,
        "hp": 9, "ac": 13, "size": [1, 1], "movement": 6,
        "str_": 10, "dex": 14, "con_": 10, "int_": 10,
        "fort": 2, "ref_": 4, "will": 1,
        "attacks": [
            {"name": "Arco Curto", "atk_bonus": 4, "damage": "1d6",
             "damage_types": ["physical"], "num_attacks": 1, "on_hit": None,
             "range": 8, "categoria": "perfurante"},
        ],
        "special_abilities": [
            {"id": "mente_fraca", "name": "Mente Fraca", "action_type": "passiva",
             "descricao": "-2 em testes de Vontade contra magias de controle mental"},
        ],
        "immunities": [],
        "weaknesses": [
            {"type": "save_penalty", "save": "vontade", "bonus_flat": -2, "em_magia": True,
             "descricao": "Mente fraca: -2 em Vontade contra controle mental"},
        ],
        "loot_table": {
            "1-40": None, "41-70": {"tipo": "gold", "valor": 2},
            "71-90": {"tipo": "gold", "valor": 2}, "91-100": {"tipo": "gold", "valor": 3},
        },
        "guaranteed_loot": ["arco_curto"],
        "spawn_min": 1, "spawn_max": 3,
        "ai_type": "goblin_arqueiro",
        "porte": "pequeno",
        "image": "goblinArqueiro",
        "undead": False, "boss": False,
    },
    {
        "type": "goblin_combatente", "name": "Goblin Combatente", "emoji": "👺",
        "tier": 1, "cr": 0.25,
        "hp": 9, "ac": 13, "size": [1, 1], "movement": 6,
        "str_": 10, "dex": 14, "con_": 10, "int_": 10,
        "fort": 2, "ref_": 4, "will": 1,
        # attacks (adaga OU espada curta) e guaranteed_loot definidos em make_monster.
        "attacks": [
            {"name": "Adaga", "atk_bonus": 4, "damage": "1d4+2",
             "damage_types": ["physical"], "num_attacks": 1, "on_hit": None,
             "categoria": "perfurante"},
        ],
        "special_abilities": [
            {"id": "arremesso",   "name": "Arremesso",   "action_type": "acao_bonus",
             "descricao": "Arremesso 1d4+2 (alcance 3) como ação bônus; 1 natural quebra a arma"},
            {"id": "mente_fraca", "name": "Mente Fraca", "action_type": "passiva",
             "descricao": "-2 em testes de Vontade contra magias de controle mental"},
        ],
        "immunities": [],
        "weaknesses": [
            {"type": "save_penalty", "save": "vontade", "bonus_flat": -2, "em_magia": True,
             "descricao": "Mente fraca: -2 em Vontade contra controle mental"},
        ],
        "loot_table": {
            "1-40": None, "41-70": {"tipo": "gold", "valor": 2},
            "71-90": {"tipo": "gold", "valor": 2}, "91-100": {"tipo": "gold", "valor": 3},
        },
        "guaranteed_loot": ["dagger"],
        "spawn_min": 1, "spawn_max": 3,
        "ai_type": "goblin_melee",
        "porte": "pequeno",
        "image": "goblinCombatente",
        "undead": False, "boss": False,
    },
    {
        "type": "goblin_dual", "name": "Goblin Dual", "emoji": "👺",
        "tier": 1, "cr": 1,
        "hp": 9, "ac": 13, "size": [1, 1], "movement": 6,
        "str_": 10, "dex": 14, "con_": 10, "int_": 10,
        "fort": 2, "ref_": 4, "will": 1,
        "attacks": [
            {"name": "Espada Curta", "atk_bonus": 2, "damage": "1d6",
             "damage_types": ["physical"], "num_attacks": 1, "on_hit": None,
             "categoria": "cortante"},
            {"name": "Adaga", "atk_bonus": 4, "damage": "1d4+2",
             "damage_types": ["physical"], "num_attacks": 1, "on_hit": None,
             "categoria": "perfurante"},
        ],
        "special_abilities": [
            {"id": "arremesso",   "name": "Arremesso",   "action_type": "acao_bonus",
             "descricao": "Arremesso 1d4+2 (alcance 3) como ação bônus; 1 natural quebra a arma"},
            {"id": "mente_fraca", "name": "Mente Fraca", "action_type": "passiva",
             "descricao": "-2 em testes de Vontade contra magias de controle mental"},
        ],
        "immunities": [],
        "weaknesses": [
            {"type": "save_penalty", "save": "vontade", "bonus_flat": -2, "em_magia": True,
             "descricao": "Mente fraca: -2 em Vontade contra controle mental"},
        ],
        "loot_table": {
            "1-40": None, "41-70": {"tipo": "gold", "valor": 2},
            "71-90": {"tipo": "gold", "valor": 2}, "91-100": {"tipo": "gold", "valor": 3},
        },
        "guaranteed_loot": ["shortsword", "dagger"],
        "spawn_min": 1, "spawn_max": 1,
        # Chefe do bando: traz combatentes e arqueiros (ver spawn_companions).
        "spawn_companions": [
            {"type": "goblin_combatente", "min": 1, "max": 2},
            {"type": "goblin_arqueiro",   "min": 1, "max": 1},
            {"type": "goblin_xama",       "min": 0, "max": 1},   # suporte mágico ocasional
        ],
        "ai_type": "goblin_melee",
        "porte": "medio",
        "image": "goblinDual",
        "undead": False, "boss": False,
    },
    {
        "type": "goblin_xama", "name": "Xamã Goblin", "emoji": "👺",
        "tier": 1, "cr": 1,
        "hp": 10, "ac": 12, "size": [1, 1], "movement": 6,
        "str_": 8, "dex": 14, "con_": 10, "int_": 12,
        "fort": 2, "ref_": 4, "will": 3,
        "attacks": [
            {"name": "Cajado", "atk_bonus": 3, "damage": "1d6-1",
             "damage_types": ["physical"], "num_attacks": 1, "on_hit": None,
             "categoria": "contundente"},
        ],
        "special_abilities": [
            {"id": "silencio",   "name": "Silêncio",   "action_type": "magia",
             "uses_per_combat": 1, "circulo": 2,
             "descricao": "Cria área de Silêncio (some se o xamã morrer)"},
            {"id": "amaldicoar", "name": "Amaldiçoar", "action_type": "magia",
             "uses_per_combat": 1, "circulo": 1,
             "descricao": "Debuff -1 em ataque/dano/CA/resistência nos heróis"},
            {"id": "abencoar",   "name": "Abençoar",   "action_type": "magia",
             "uses_per_combat": 1, "circulo": 1,
             "descricao": "Buff +1 em ataque/dano/CA/resistência nos goblins aliados"},
            {"id": "concentracao_fragil", "name": "Concentração Frágil", "action_type": "passiva",
             "descricao": "Se sofrer dano, não pode usar magia no próximo turno"},
        ],
        "immunities": [],
        "weaknesses": [
            {"type": "save_penalty", "save": "vontade", "bonus_flat": -2, "em_magia": True,
             "descricao": "Mente fraca: -2 em Vontade contra controle mental"},
        ],
        "loot_table": {
            "1-20":  None,
            "21-40": {"tipo": "item", "id": "garrafa_vinho"},
            "41-70": {"tipo": "gold", "valor": 2},
            "71-90": {"tipo": "gold", "valor": 4},
            "91-98": {"tipo": "gold", "valor": 6},
            "99-100": {"tipo": "raro_xama"},   # 50% Poção de Cura / 50% Pergaminho (1º círculo)
        },
        "spawn_min": 1, "spawn_max": 1,
        # Lidera o próprio bando de suporte.
        "spawn_companions": [
            {"type": "goblin_combatente", "min": 1, "max": 2},
            {"type": "goblin_arqueiro",   "min": 1, "max": 1},
        ],
        "ai_type": "goblin_xama",
        "porte": "pequeno",
        "image": "xamaGoblin",
        "undead": False, "boss": False,
    },
    # ── Kobolds (surgem juntos: 1-4 lanceiros + 1-2 besteiros) ───────────────
    {
        "type": "kobold_lanceiro", "name": "Kobold Lanceiro", "emoji": "🐊",
        "tier": 1, "cr": 0.25,
        "hp": 7, "ac": 12, "size": [1, 1], "movement": 7,
        "str_": 8, "dex": 14, "con_": 10, "int_": 12,
        "fort": 2, "ref_": 4, "will": 2,
        "attacks": [
            {"name": "Lança Curta", "atk_bonus": 1, "damage": "1d6-1",
             "damage_types": ["physical"], "num_attacks": 1, "on_hit": None},
        ],
        "special_abilities": [
            {"id": "veneno_lanca",   "name": "Lança Envenenada",      "action_type": "acao_livre",
             "dc": 8, "save": "fortitude", "effect": "veneno_aranha_sombria"},
            {"id": "covardia_kobold","name": "Covardia Instintiva",   "action_type": "passiva",
             "dc": 10, "save": "vontade",  "effect": "medo_kobold",   "effect_duration": 2},
        ],
        "immunities": [],
        "weaknesses": [],
        "loot_table": {
            "1-40":  None,
            "41-70": {"tipo": "gold", "valor": 1},
            "71-90": {"tipo": "gold", "valor": 2},
            "91-100": {"tipo": "item", "id": "veneno_aranha_sombria"},
        },
        "spawn_min": 1, "spawn_max": 4,
        "spawn_companion": {"type": "kobold_besteiro", "min": 1, "max": 2},
        "ai_type": "kobold_lanceiro",
        "porte": "pequeno",
        "image": "koboldlanceiro",
        "undead": False, "boss": False,
    },
    {
        "type": "kobold_besteiro", "name": "Kobold Besteiro", "emoji": "🐊",
        "tier": 1, "cr": 0.25,
        "hp": 7, "ac": 12, "size": [1, 1], "movement": 7,
        "str_": 8, "dex": 14, "con_": 10, "int_": 12,
        "fort": 2, "ref_": 4, "will": 2,
        "attacks": [
            {"name": "Besta de Mão", "atk_bonus": 4, "damage": "1d4+2",
             "damage_types": ["physical"], "num_attacks": 1, "on_hit": None,
             "range": 4},
        ],
        "special_abilities": [
            {"id": "covardia_kobold","name": "Covardia Instintiva",   "action_type": "passiva",
             "dc": 10, "save": "vontade",  "effect": "medo_kobold",   "effect_duration": 2},
        ],
        "immunities": [],
        "weaknesses": [],
        "loot_table": {
            "1-40":  None,
            "41-70": {"tipo": "gold", "valor": 1},
            "71-90": {"tipo": "gold", "valor": 2},
            "91-95": {"tipo": "item", "id": "veneno_aranha_sombria"},
            "96-100": {"tipo": "item", "id": "virote_incendiario", "qtd": "1d6"},
        },
        "spawn_min": 0, "spawn_max": 0,   # spawna apenas como companion do lanceiro
        "ai_type": "kobold_besteiro",
        "porte": "pequeno",
        "image": "koboldbesteiro",
        "undead": False, "boss": False,
    },
    # ── Necromante (ND 2): mago nível 2, conjurador + mestre dos mortos ──────────
    {
        "type": "necromante", "name": "Necromante", "emoji": "🧙",
        "tier": 2, "cr": 2, "level": 2,        # mago nível 2 (escala Bola de Fogo p/ 2d6, CD 12)
        "hp": 16, "ac": 12, "size": [1, 1], "movement": 5,
        "str_": 8, "dex": 12, "con_": 12, "int_": 16,
        "fort": 4, "ref_": 4, "will": 6,
        "attacks": [
            {"name": "Adaga", "atk_bonus": 4, "damage": "1d4+1",
             "damage_types": ["physical"], "num_attacks": 1, "on_hit": None,
             "categoria": "perfurante"},
        ],
        "special_abilities": [
            # 3 magias por dia (1 uso cada) — miradas nos heróis (área).
            {"id": "bola_fogo",  "name": "Bola de Fogo", "action_type": "magia",
             "uses_per_combat": 1, "circulo": 1},
            {"id": "medo",       "name": "Medo",         "action_type": "magia",
             "uses_per_combat": 1, "circulo": 1},
            {"id": "amaldicoar", "name": "Amaldiçoar",   "action_type": "magia",
             "uses_per_combat": 1, "circulo": 1},
            # Pergaminho de uso único (NÃO conta no limite diário) — controle progressivo.
            {"id": "dominar_morto_vivo", "name": "Dominar Morto-Vivo",
             "action_type": "acao", "range": 4, "circulo": 3},
            {"id": "mestre_dos_mortos", "name": "Mestre dos Mortos", "action_type": "passiva",
             "descricao": "Inicia com 2 esqueletos; mortos-vivos próximos recebem +1 em Vontade"},
            {"id": "concentracao_sombria", "name": "Concentração Sombria", "action_type": "passiva",
             "descricao": "Ao sofrer dano: Vontade CD 10 ou perde a ação de magia no turno"},
            {"id": "essencia_profana", "name": "Essência Profana", "action_type": "passiva",
             "descricao": "Sofre dano dobrado de efeitos sagrados/luz"},
        ],
        "immunities": [],
        "weaknesses": [
            {"type": "holy", "multiplier": 2,
             "descricao": "Essência profana: dano sagrado/luz dobrado"},
        ],
        # Loot especial tratado em _necromante_loot (tabela + pergaminho se não dominou).
        "loot_table": {"1-100": None},
        "spawn_min": 1, "spawn_max": 1,
        "spawn_companions": [
            {"type": "esqueleto_humano", "min": 2, "max": 2},   # Mestre dos Mortos
        ],
        "ai_type": "necromante",
        "porte": "medio",
        "image": "necromante",
        "undead": False, "boss": False,
    },
    # ── Zumbi Infectado (ND 1): morto-vivo lento que transmite doença ───────────
    {
        "type": "zumbi_infectado", "name": "Zumbi Infectado", "emoji": "🧟",
        "tier": 1, "cr": 1,
        "hp": 22, "ac": 10, "size": [1, 1], "movement": 4,
        "str_": 14, "dex": 6, "con_": 16, "int_": 3,
        "fort": 5, "ref_": 0, "will": 1,
        "darkvision_range": 8,
        "attacks": [
            {"name": "Golpe", "atk_bonus": 4, "damage": "1d6+2",
             "damage_types": ["physical"], "num_attacks": 1, "on_hit": None,
             "categoria": "contundente"},
        ],
        "special_abilities": [
            {"id": "resistencia_morta", "name": "Resistência Morta", "action_type": "passiva",
             "dc": 10, "save": "fortitude",
             "descricao": "A 0 HP: Fortitude CD 10 → fica com 1 HP (dano sagrado/luz ignora e destrói de vez)"},
            {"id": "infeccao", "name": "Infecção", "action_type": "passiva",
             "dc": 10, "save": "fortitude",
             "descricao": "Ao acertar: alvo testa Fortitude CD 10 ou contrai 1 sintoma leve"},
            {"id": "lento_incansavel", "name": "Lento e Incansável", "action_type": "passiva",
             "descricao": "Não corre nem foge — avança sem parar"},
            {"id": "corpo_morto", "name": "Corpo Morto", "action_type": "passiva",
             "descricao": "Não come, bebe nem respira"},
        ],
        "immunities": ["veneno", "controle_mental"],
        "weaknesses": [
            {"type": "holy", "multiplier": 2,
             "descricao": "Consagrado à destruição: dano sagrado/luz dobrado (morte sagrada = destruição total)"},
        ],
        "loot_table": {"1-100": None},
        "spawn_min": 1, "spawn_max": 2,
        "ai_type": "zumbi",
        "porte": "medio",
        "image": "zumbi",
        "undead": True, "boss": False,
    },
    # ── Lagarto Carniceiro (ND 2): predador de 2 casas em linha (frente/trás) ────
    {
        "type": "lagarto_carniceiro", "name": "Lagarto Carniceiro", "emoji": "🦎",
        "tier": 2, "cr": 2,
        "hp": 24, "ac": 14, "size": [2, 1], "oriented": True, "movement": 7,
        "str_": 16, "dex": 14, "con_": 14, "int_": 6,
        "fort": 4, "ref_": 4, "will": 1,
        "attacks": [
            {"name": "Mordida", "atk_bonus": 6, "damage": "1d8+3",
             "damage_types": ["physical"], "num_attacks": 2, "on_hit": None,
             "categoria": "perfurante"},
        ],
        # Garras do Combo Devorador (só disparam se as 2 mordidas acertarem).
        "garra_attack": {"name": "Garra", "atk_bonus": 5, "damage": "1d6+3",
                         "damage_types": ["physical"], "num_attacks": 1, "on_hit": None,
                         "categoria": "cortante"},
        "special_abilities": [
            {"id": "combo_devorador", "name": "Combo Devorador", "action_type": "passiva",
             "descricao": "Se as 2 mordidas acertarem no turno: 2 ataques de Garra imediatos"},
            {"id": "predador_oportunista", "name": "Predador Oportunista", "action_type": "passiva",
             "descricao": "+1 nas mordidas contra alvos com menos de 50% do HP"},
            {"id": "faro_carnica", "name": "Faro de Carniça", "action_type": "passiva",
             "descricao": "Prioriza sempre o alvo com menor HP"},
            {"id": "duas_cabecas", "name": "Duas Cabeças", "action_type": "passiva",
             "descricao": "+1 em percepção; difícil de surpreender (flavor)"},
        ],
        "immunities": [],
        "weaknesses": [
            {"type": "veneno_dobrado", "descricao": "Sensível a venenos: todos os efeitos dobrados"},
        ],
        "loot_table": {"1-100": None},
        "spawn_min": 1, "spawn_max": 1,
        "ai_type": "lagarto_carniceiro",
        "porte": "grande",
        "image": "lagartoCarniceiro",
        "undead": False, "boss": False,
    },
    # ── Devorador de Metal (ND 2): corrói equipamentos metálicos ────────────────
    {
        "type": "devorador_metal", "name": "Devorador de Metal", "emoji": "🔩",
        "tier": 2, "cr": 2,
        "hp": 22, "ac": 13, "size": [1, 1], "movement": 5,
        "str_": 14, "dex": 10, "con_": 14, "int_": 3,
        "fort": 4, "ref_": 2, "will": 1,
        "attacks": [
            {"name": "Mordida", "atk_bonus": 4, "damage": "1d8+2",
             "damage_types": ["physical"], "num_attacks": 1, "on_hit": None,
             "categoria": "perfurante"},
        ],
        "special_abilities": [
            {"id": "mordida_corrosiva", "name": "Mordida Corrosiva", "action_type": "passiva",
             "descricao": "Ao acertar: +1 nível de dano na arma OU armadura metálica do alvo"},
            {"id": "devorar_metal", "name": "Devorar Metal", "action_type": "passiva",
             "descricao": "Item a 3 níveis é destruído e o Devorador recupera 1d6 HP"},
            {"id": "alimentacao_metalica", "name": "Alimentação Metálica", "action_type": "passiva",
             "descricao": "Gasta a ação para consumir item metálico no chão e recuperar 1d6 HP"},
        ],
        "immunities": ["cegueira", "escuridao"],
        "weaknesses": [
            {"type": "lightning", "bonus_flat": 2,
             "descricao": "Corpo condutor: +2 de dano de eletricidade"},
        ],
        # Ouro preso no corpo — recuperado ao derrotá-lo.
        "loot_table": {"1-100": {"tipo": "gold", "valor": "1d6"}},
        "spawn_min": 1, "spawn_max": 2,
        "ai_type": "devorador_metal",
        "porte": "medio",
        "image": "devoradordemetal",
        "undead": False, "boss": False,
    },
    # ── Bugbear — Bicho-Papão das Sombras (ND 2): caçador furtivo das trevas ─────
    {
        "type": "bugbear_sombras", "name": "Bugbear — Bicho-Papão das Sombras", "emoji": "😈",
        "tier": 2, "cr": 2, "level": 3,   # conjura Manto de Escuridão como conjurador nível 3
        "hp": 22, "ac": 14, "size": [1, 1], "movement": 7,
        "str_": 16, "dex": 16, "con_": 12, "int_": 8,
        "fort": 4, "ref_": 5, "will": 2,
        "visao_escuro": True,        # enxerga perfeitamente no escuro (sempre ativo)
        "darkvision_range": 99,      # vê na névoa como quem tem Visão no Escuro
        "attacks": [
            # 3 ataques/turno: 2 Garras + 1 Mordida.
            {"name": "Garras", "atk_bonus": 6, "damage": "1d6+3",
             "damage_types": ["physical"], "num_attacks": 2, "on_hit": None,
             "categoria": "cortante"},
            {"name": "Mordida", "atk_bonus": 6, "damage": "1d8+3",
             "damage_types": ["physical"], "num_attacks": 1, "on_hit": None,
             "categoria": "perfurante"},
        ],
        "special_abilities": [
            # Comportamento das habilidades de escuridão é ligado no Lote 2.
            {"id": "manto_escuridao", "name": "Manto de Escuridão", "action_type": "magia",
             "uses_per_combat": 1, "circulo": 1,
             "descricao": "Cria uma área de escuridão centrada em si (1x por combate)"},
            {"id": "ataque_das_sombras", "name": "Ataque das Sombras", "action_type": "passiva",
             "descricao": "Se o alvo não o enxerga (bugbear oculto OU alvo na escuridão sem visão no escuro): +2 ataque e +1d6 de dano em TODOS os ataques"},
            {"id": "cacador_das_trevas", "name": "Caçador das Trevas", "action_type": "passiva",
             "descricao": "Em área escura: +2 CA, +1 ataque e sempre pode usar Ataque das Sombras"},
            {"id": "desaparecer_nas_sombras", "name": "Desaparecer nas Sombras", "action_type": "acao_livre",
             "cooldown_turns": 5,
             "descricao": "Só na escuridão (após Manto): fica oculto (imune a ataques à distância; corpo a corpo -4), move até 3, até o início do próximo turno"},
            {"id": "visao_perfeita_escuro", "name": "Visão no Escuro", "action_type": "passiva",
             "descricao": "Enxerga perfeitamente no escuro — não sofre penalidades nas trevas"},
        ],
        "immunities": [],
        "weaknesses": [
            {"type": "fire", "multiplier": 2,
             "descricao": "Criatura das sombras: sofre dano dobrado de fogo"},
            {"type": "holy", "multiplier": 2,
             "descricao": "Criatura das sombras: sofre dano dobrado de efeitos sagrados/luz"},
            # Sob luz direta (zona de 'luz') o bugbear ataca com -2. Dormente até
            # existir uma fonte de luz no jogo (decisão do usuário — sem luz padrão).
            {"type": "luz_direta", "atk_penalty": -2,
             "descricao": "Sob luz direta: -2 em ataques"},
        ],
        "loot_table": {
            "1-60":   None,
            "61-85":  {"tipo": "gold", "valor": 2},
            "86-95":  {"tipo": "gold", "valor": 4},
            "96-98":  {"tipo": "scroll", "magia_id": "manto_escuridao"},  # pergaminho da escuridão
            "99-100": {"tipo": "item", "id": "vela_escuridao"},           # Vela da Escuridão (criada no Lote 3)
        },
        "spawn_min": 1, "spawn_max": 2,
        "ai_type": "bugbear_sombras",
        "porte": "medio",
        "image": "bugbear",          # assets/pawns/monstros/bugbear/bugbear.png
        "undead": False, "boss": False,
    },
    # ── Ogro de Clava (ND 2): bruto ofensivo (ocupa 1 tile) ─────────────────────
    {
        "type": "ogro_clava", "name": "Ogro de Clava", "emoji": "🧌",
        "tier": 2, "cr": 2,
        "hp": 32, "ac": 12, "size": [1, 1], "movement": 5,
        "str_": 18, "dex": 8, "con_": 17, "int_": 6,
        "fort": 5, "ref_": 1, "will": 0,
        "attacks": [
            {"name": "Clava Pesada", "atk_bonus": 6, "damage": "1d12+4",
             "damage_types": ["physical"], "num_attacks": 1, "on_hit": None,
             "categoria": "contundente"},
        ],
        "special_abilities": [
            {"id": "golpe_brutal", "name": "Golpe Brutal", "action_type": "ataque",
             "cooldown_turns": 3,
             "descricao": "+2 de dano ao ataque (recarga 3 rodadas); usado para finalizar"},
            {"id": "forca_descomunal", "name": "Força Descomunal", "action_type": "ataque",
             "cooldown_turns": 4, "save": "fortitude", "dc": 10,
             "descricao": "Ataque normal; se acertar, Fortitude CD 10 ou atordoado (perde a próxima rodada). Recarga 4 rodadas"},
            {"id": "mente_bruta", "name": "Mente Bruta", "action_type": "passiva",
             "descricao": "-2 em Vontade contra controle mental"},
            {"id": "lento_previsivel", "name": "Lento e Previsível", "action_type": "passiva",
             "descricao": "Se errar um ataque: -2 de CA até o próximo turno"},
        ],
        "immunities": [],
        "weaknesses": [
            {"type": "save_penalty", "save": "vontade", "bonus_flat": -2, "em_magia": True,
             "descricao": "Mente Bruta: -2 em Vontade contra controle mental"},
        ],
        "loot_table": {
            "1-40":   None,
            "41-70":  {"tipo": "gold", "valor": 2},
            "71-90":  {"tipo": "gold", "valor": 4},
            "91-100": {"tipo": "comida"},   # comida aleatória (Ração/taverna)
        },
        "spawn_min": 1, "spawn_max": 1,
        "ai_type": "ogro",
        "porte": "grande",
        "image": "ogroClava",
        "undead": False, "boss": False,
    },
    # ── Ogro de Lança (ND 2): bruto defensivo (ocupa 1 tile), alcance estendido ──
    {
        "type": "ogro_lanca", "name": "Ogro de Lança", "emoji": "🧌",
        "tier": 2, "cr": 2,
        "hp": 32, "ac": 14, "size": [1, 1], "movement": 5,   # CA 14 (com escudo)
        "str_": 18, "dex": 8, "con_": 17, "int_": 6,
        "fort": 5, "ref_": 1, "will": 0,
        "reach_lanca": True,   # alcance 2 à frente / 1 diagonal (ver _lanca_no_alcance)
        "attacks": [
            {"name": "Lança Grande", "atk_bonus": 6, "damage": "1d10+4",
             "damage_types": ["physical"], "num_attacks": 1, "on_hit": None,
             "categoria": "perfurante"},
        ],
        "special_abilities": [
            {"id": "golpe_brutal", "name": "Golpe Brutal", "action_type": "ataque",
             "cooldown_turns": 3,
             "descricao": "+2 de dano ao ataque (recarga 3 rodadas); usado para finalizar"},
            {"id": "forca_descomunal", "name": "Força Descomunal", "action_type": "ataque",
             "cooldown_turns": 4, "save": "fortitude", "dc": 10,
             "descricao": "Ataque normal; se acertar, Fortitude CD 10 ou atordoado (perde a próxima rodada). Recarga 4 rodadas"},
            {"id": "mente_bruta", "name": "Mente Bruta", "action_type": "passiva",
             "descricao": "-2 em Vontade contra controle mental"},
            {"id": "lento_previsivel", "name": "Lento e Previsível", "action_type": "passiva",
             "descricao": "Se errar um ataque: -2 de CA até o próximo turno"},
        ],
        "immunities": [],
        "weaknesses": [
            {"type": "save_penalty", "save": "vontade", "bonus_flat": -2, "em_magia": True,
             "descricao": "Mente Bruta: -2 em Vontade contra controle mental"},
        ],
        "loot_table": {
            "1-40":   None,
            "41-70":  {"tipo": "gold", "valor": 2},
            "71-90":  {"tipo": "gold", "valor": 4},
            "91-100": {"tipo": "comida"},
        },
        "spawn_min": 1, "spawn_max": 1,
        "ai_type": "ogro",
        "porte": "grande",
        "image": "ogroLanca",
        "undead": False, "boss": False,
    },
]

CHEST_ITEMS = [
    # ── Consumíveis (vão para a mochila, max 6 slots) ──
    {"id": "health_potion", "name": "Poção de Vida",     "emoji": "🧪", "item_slot": "bag",       "effect": "heal",      "value": 10},
    {"id": "mana_potion",   "name": "Poção de Mana",     "emoji": "💙", "item_slot": "bag",       "effect": "mana",      "value": 8},
    {"id": "elixir",        "name": "Elixir da Força",   "emoji": "⚗️", "item_slot": "bag",       "effect": "atk_bonus", "value": 3},
    {"id": "antidote",      "name": "Antídoto",          "emoji": "💚", "item_slot": "bag",       "effect": "heal",      "value": 6},
    {"id": "garrafa_vinho", "name": "Garrafa de Vinho",  "emoji": "🍷", "item_slot": "bag",       "effect": "wine",      "value": 15},
    {"id": "racao",         "name": "Ração (Pão e Água)", "emoji": "🥖", "item_slot": "bag",       "effect": "ration",    "value": 15},
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

# allowed_classes ausente = TODAS as classes podem usar (sem restrição).
# categoria = subtipo de dano físico: "cortante" / "perfurante" / "contundente" (concussão).
# two_handed = True → não empunha junto com escudo (ver _conflito_duas_maos).
SHOP_WEAPONS = [
    # ─── Leves (1d4) ───────────────────────────────────────────────────────────
    {"id": "dagger",        "name": "Adaga",              "emoji": "🗡️",  "die": "1d4",  "stat": "str_", "price": 5,  "throw_range": 3, "finesse": True, "categoria": "perfurante"},
    {"id": "chicote",       "name": "Chicote",            "emoji": "🪢",  "die": "1d4",  "stat": "dex",  "price": 8,  "range": 2, "categoria": "cortante",
     "allowed_classes": ["mage", "bard", "rogue", "paladin", "warrior"]},
    {"id": "hand_crossbow", "name": "Besta de Mão",       "emoji": "🏹",  "die": "1d4",  "stat": "dex",  "price": 10, "range": 4, "categoria": "perfurante"},
    # ─── Médias (1d6) ──────────────────────────────────────────────────────────
    {"id": "lanca_curta",   "name": "Lança Curta",        "emoji": "🔱",  "die": "1d6",  "stat": "str_", "price": 7,  "throw_range": 5, "categoria": "perfurante",
     "allowed_classes": ["bard", "rogue", "paladin", "warrior"]},
    {"id": "bordao",        "name": "Bordão",             "emoji": "🪄",  "die": "1d6",  "stat": "str_", "price": 8,  "categoria": "contundente",
     "allowed_classes": ["cleric", "bard", "rogue", "paladin", "warrior"]},
    {"id": "staff",         "name": "Cajado Arcano",      "emoji": "🪄",  "die": "1d6",  "stat": "str_", "price": 10, "reach": "cajado", "categoria": "contundente",
     "allowed_classes": ["mage", "bard", "rogue", "paladin", "warrior"]},
    {"id": "maca",          "name": "Maça",               "emoji": "🔨",  "die": "1d6",  "stat": "str_", "price": 10, "categoria": "contundente",
     "allowed_classes": ["bard", "rogue", "paladin", "warrior"]},
    {"id": "shortsword",    "name": "Espada Curta",       "emoji": "⚔️",  "die": "1d6",  "stat": "str_", "price": 12, "categoria": "cortante",
     "allowed_classes": ["bard", "rogue", "paladin", "warrior"]},
    {"id": "arco_curto",    "name": "Arco Curto",         "emoji": "🏹",  "die": "1d6",  "stat": "dex",  "price": 12, "range": 8, "categoria": "perfurante",
     "allowed_classes": ["bard", "rogue", "paladin", "warrior"]},
    # ─── Pesadas (1d8) ─────────────────────────────────────────────────────────
    {"id": "lanca",         "name": "Lança",              "emoji": "🔱",  "die": "1d8",  "stat": "str_", "price": 14, "reach": "lanca", "categoria": "perfurante",
     "allowed_classes": ["paladin", "warrior"]},
    {"id": "longsword",     "name": "Espada Longa",       "emoji": "⚔️",  "die": "1d8",  "stat": "str_", "price": 16, "categoria": "cortante",
     "allowed_classes": ["paladin", "warrior"]},
    {"id": "longbow",       "name": "Arco Longo",         "emoji": "🏹",  "die": "1d8",  "stat": "dex",  "price": 16, "range": 12, "categoria": "perfurante",
     "allowed_classes": ["paladin", "warrior"]},
    {"id": "warhammer",     "name": "Martelo de Guerra",  "emoji": "🔨",  "die": "1d8",  "stat": "str_", "price": 18, "categoria": "contundente",
     "allowed_classes": ["paladin", "warrior"]},
    {"id": "besta",         "name": "Besta",              "emoji": "🏹",  "die": "1d8",  "stat": "dex",  "price": 18, "range": 10, "categoria": "perfurante",
     "allowed_classes": ["cleric", "rogue", "paladin", "warrior"]},
    {"id": "mangual",       "name": "Mangual",            "emoji": "⚔️",  "die": "1d8",  "stat": "str_", "price": 20, "categoria": "contundente",
     "allowed_classes": ["cleric", "paladin", "warrior"]},
    {"id": "machado_duplo", "name": "Machado Duplo",      "emoji": "🪓",  "die": "1d8",  "stat": "str_", "price": 22, "categoria": "cortante",
     "allowed_classes": ["paladin", "warrior"]},
    # ─── Muito Pesadas (1d10 / 2d6) ────────────────────────────────────────────
    {"id": "bastsword",     "name": "Espada Bastarda",    "emoji": "⚔️",  "die": "1d10", "stat": "str_", "price": 25, "categoria": "cortante",
     "allowed_classes": ["paladin", "warrior"]},
    {"id": "machado_orc",   "name": "Machado de Guerra Órquico", "emoji": "🪓", "die": "1d10", "stat": "str_", "price": 26, "categoria": "cortante", "two_handed": True,
     "allowed_classes": ["paladin", "warrior"]},
    {"id": "alabarda",      "name": "Alabarda",           "emoji": "🪓",  "die": "1d10", "stat": "str_", "price": 28, "range": 2, "categoria": "perfurante", "two_handed": True,
     "allowed_classes": ["paladin", "warrior"]},
    {"id": "espada2m",      "name": "Espada de 2 Mãos",  "emoji": "⚔️",  "die": "2d6",  "stat": "str_", "price": 35, "categoria": "cortante", "two_handed": True,
     "allowed_classes": ["paladin", "warrior"]},
]

# allowed_classes ausente = TODAS as classes podem usar (sem restrição).
SHOP_ARMORS = [
    # ── Proteções / Escudos (slot acessório — somam com armadura) ──────────────
    {"id": "escudo_p",     "name": "Escudo Pequeno",     "emoji": "🛡️", "ac_bonus": 1, "price": 15, "kind": "shield",
     "allowed_classes": ["cleric", "paladin", "warrior"]},
    {"id": "escudo_g",     "name": "Escudo Grande",      "emoji": "🛡️", "ac_bonus": 2, "price": 25, "kind": "shield",
     "allowed_classes": ["paladin", "warrior"]},
    # ── Armaduras (slot armadura) ─────────────────────────────────────────────
    {"id": "cloak",        "name": "Manto",              "emoji": "🧣",  "ac_bonus": 1, "price": 15, "kind": "armor"},
    {"id": "leather",      "name": "Armadura de Couro",  "emoji": "🥋",  "ac_bonus": 2, "price": 30, "kind": "armor",
     "allowed_classes": ["cleric", "bard", "rogue", "paladin", "warrior"]},
    {"id": "chainmail",    "name": "Cota de Malha",      "emoji": "🪖",  "ac_bonus": 4, "price": 100, "kind": "armor",
     "allowed_classes": ["cleric", "bard", "paladin", "warrior"]},
    {"id": "bronze_armor", "name": "Armadura de Bronze", "emoji": "🪖",  "ac_bonus": 5, "price": 200, "kind": "armor",
     "allowed_classes": ["paladin", "warrior"]},
    {"id": "plate",        "name": "Armadura de Placas", "emoji": "🛡️", "ac_bonus": 6, "price": 400, "kind": "armor",
     "allowed_classes": ["paladin", "warrior"]},
    {"id": "fullplate",    "name": "Armadura Completa",  "emoji": "🛡️", "ac_bonus": 8, "price": 800, "kind": "armor",
     "allowed_classes": ["paladin", "warrior"]},
]

SHOP_MERCHANT = [
    {"id": "health_potion", "name": "Poção de Cura",    "emoji": "🧪",  "price": 8,  "item_slot": "bag",   "effect": "heal",      "value": 10},
    {"id": "mana_potion",   "name": "Poção de Mana",    "emoji": "💙",  "price": 8,  "item_slot": "bag",   "effect": "mana",      "value": 8},
    {"id": "elixir",        "name": "Elixir da Força",  "emoji": "⚗️", "price": 12, "item_slot": "bag",   "effect": "atk_bonus", "value": 3},
    {"id": "antidote",      "name": "Antídoto",          "emoji": "💚",  "price": 5,  "item_slot": "bag",   "effect": "heal",      "value": 6},
    {"id": "vela_escuridao","name": "Vela da Escuridão", "emoji": "🕯️", "price": 50, "item_slot": "bag",   "effect": "veil_shadow","value": 0},
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
    # ── Venenos (consumíveis de bolsa — untam a arma; ver VENENOS) ──
    {"id": "veneno_aranha_sombria", "name": "Veneno da Aranha Sombria", "emoji": "🕷️", "price": 8,  "item_slot": "bag", "effect": "coat_poison", "value": 0, "veneno_id": "veneno_aranha_sombria"},
    {"id": "veneno_escorpiao_pedra","name": "Veneno do Escorpião Pedra","emoji": "🦂", "price": 12, "item_slot": "bag", "effect": "coat_poison", "value": 0, "veneno_id": "veneno_escorpiao_pedra"},
    {"id": "veneno_cobra_cuspidora","name": "Veneno de Cobra Cuspidora","emoji": "🐍", "price": 16, "item_slot": "bag", "effect": "coat_poison", "value": 0, "veneno_id": "veneno_cobra_cuspidora"},
    {"id": "veneno_basilisco",      "name": "Peçonha do Basilisco",     "emoji": "🦎", "price": 20, "item_slot": "bag", "effect": "coat_poison", "value": 0, "veneno_id": "veneno_basilisco"},
    {"id": "veneno_polvo_abissal",  "name": "Tinta do Polvo Abissal",   "emoji": "🐙", "price": 15, "item_slot": "bag", "effect": "coat_poison", "value": 0, "veneno_id": "veneno_polvo_abissal"},
    # ── Munições básicas (slot off_hand — 10 projéteis por pacote) ──
    {"id": "flechas",  "name": "Flechas (×10)",  "emoji": "🏹", "price": 3,
     "item_slot": "ammo", "effect": "ammo", "ammo_type": "flechas", "ammo_count": 10},
    {"id": "virotes",  "name": "Virotes (×10)",  "emoji": "🏹", "price": 3,
     "item_slot": "ammo", "effect": "ammo", "ammo_type": "virotes", "ammo_count": 10},
    # ── Munições especiais incendiárias (slot off_hand — vendidas individualmente) ──
    {"id": "virote_incendiario", "name": "Virote Incendiário", "emoji": "🔥", "price": 4,
     "item_slot": "ammo", "effect": "ammo", "ammo_type": "virotes_incendiarios", "ammo_count": 1,
     "extra_damage": "1d4", "extra_damage_types": ["fire"]},
    {"id": "flecha_incendiaria", "name": "Flecha Incendiária", "emoji": "🔥", "price": 4,
     "item_slot": "ammo", "effect": "ammo", "ammo_type": "flechas_incendiarias", "ammo_count": 1,
     "extra_damage": "1d4", "extra_damage_types": ["fire"]},
]

# ─── VENENOS ──────────────────────────────────────────────────────────────────
# Catálogo autoritativo de venenos (espelha CATALOGO_ITENS no cliente). O efeito
# é aplicado via _aplicar_veneno a QUALQUER alvo (jogador ou monstro): um teste
# de Fortitude decide se resiste/sofre o efeito (total/parcial). Os efeitos têm
# duração em rodadas e são revertidos por _processar_venenos_turno.
#
# Adaptação ao modelo de dados do servidor (≠ spec original):
#   • atributos de jogador são scores brutos: str_, dex, con_, int_ (não stats_mod)
#   • saves são totais precomputados: p["fort"], p["ref_"], p["will"]
#   • penalidades vão em alvo["penalidades"] = {"ataque","movimento","dano","ca",...}
#   • redução de FOR → menos dano corpo a corpo; redução de CON → recalcula max_hp
#   • status petrificado/cego usam flags + contador próprio de rodadas
VENENO_CARGAS  = 3    # nº de golpes certeiros que uma untada de veneno envenena
MAX_AMMO_STACK = 10   # máximo de projéteis por slot de munição (bolsa ou off_hand)

# atributo do veneno (PT, igual ao cliente) → chave de score do jogador no servidor
_VENENO_ATTR_MAP = {
    "forca": "str_", "constituicao": "con_", "destreza": "dex", "inteligencia": "int_",
}

VENENOS = {
    "veneno_aranha_sombria": {
        "nome": "Veneno da Aranha Sombria", "icone": "🕷️",
        "operacao": "reduzir", "atributo": "forca", "valor": "1d4", "duracao": "1d6",
        "save": "fortitude", "dificuldade": 8, "anula": True,
    },
    "veneno_escorpiao_pedra": {
        "nome": "Veneno do Escorpião Pedra", "icone": "🦂",
        "operacao": "penalidade", "atributos": [("ataque", -1), ("movimento", -1)],
        "duracao": "1d6", "save": "fortitude", "dificuldade": 9, "anula": True,
    },
    "veneno_cobra_cuspidora": {
        "nome": "Veneno de Cobra Cuspidora", "icone": "🐍",
        "operacao": "reduzir", "atributo": "constituicao", "valor": "1d4", "duracao": "1d6",
        "save": "fortitude", "dificuldade": 10, "anula": True, "recalcular_hp": True,
    },
    "veneno_basilisco": {
        "nome": "Peçonha do Basilisco", "icone": "🦎",
        "operacao": "petrificar", "duracao": 1, "duracao_falha": "1d4",
        "penalidade_falha": [("movimento", -1)],
        "save": "fortitude", "dificuldade": 12, "anula": False,
    },
    "veneno_polvo_abissal": {
        "nome": "Tinta do Polvo Abissal", "icone": "🐙",
        "operacao": "cegar", "duracao": "1d4", "penalidade_ataque": -4, "bloqueia_distancia": True,
        "duracao_falha": "1d4", "penalidade_falha": [("percepcao", -2)],
        "save": "fortitude", "dificuldade": 11, "anula": False,
    },
}

# ─── MASMORRAS AUTORADAS (Fase 1 do editor) ───────────────────────────────────
DUNGEONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dungeons")
# Catálogo de itens que um baú autorado pode conter (Fase 1: só CHEST_ITEMS).
_DUNGEON_ITEM_CATALOG = {it["id"]: it for it in CHEST_ITEMS}

def _contar_chao_alcancavel(tiles, w, h, start, limite):
    """Conta casas caminháveis (FLOOR/DOOR) alcançáveis a partir de `start`,
    parando ao atingir `limite` (otimização). Usado p/ garantir spawn dos heróis."""
    sx, sy = start
    if not (0 <= sx < w and 0 <= sy < h) or tiles[sy][sx] == WALL:
        return 0
    visto = {(sx, sy)}; pilha = [(sx, sy)]; conta = 0
    while pilha:
        x, y = pilha.pop()
        conta += 1
        if conta >= limite:
            return conta
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if (0 <= nx < w and 0 <= ny < h and (nx, ny) not in visto
                    and tiles[ny][nx] != WALL):
                visto.add((nx, ny)); pilha.append((nx, ny))
    return conta

def validar_dungeon(defn):
    """Valida um dict de masmorra autorada. Retorna (ok: bool, msg: str)."""
    if not isinstance(defn, dict):
        return False, "Masmorra não é um objeto JSON."
    if defn.get("schema_version") != 1:
        return False, f"schema_version não suportado: {defn.get('schema_version')!r} (esperado 1)."
    grid = defn.get("grid")
    if not isinstance(grid, dict):
        return False, "grid ausente ou inválido."
    w, h = grid.get("w"), grid.get("h")
    if (isinstance(w, bool) or isinstance(h, bool)
            or not (isinstance(w, int) and isinstance(h, int)
                    and 1 <= w <= 60 and 1 <= h <= 60)):
        return False, "grid.w/grid.h ausentes ou fora de 1..60."
    tiles = defn.get("tiles")
    if not (isinstance(tiles, list) and len(tiles) == h):
        return False, f"tiles deve ter {h} linhas (grid.h)."
    for y, row in enumerate(tiles):
        if not (isinstance(row, list) and len(row) == w):
            return False, f"linha {y} de tiles deve ter {w} colunas (grid.w)."
        for x, v in enumerate(row):
            if v not in (0, 1, 2):
                return False, f"tile inválido em ({x},{y}): {v!r} (use 0/1/2)."

    def in_grid(p):
        return (isinstance(p, (list, tuple)) and len(p) == 2
                and isinstance(p[0], int) and isinstance(p[1], int)
                and 0 <= p[0] < w and 0 <= p[1] < h)

    def tile_at(p):
        return tiles[p[1]][p[0]]

    ent = defn.get("entrance")
    if not (isinstance(ent, dict) and in_grid([ent.get("x"), ent.get("y")])):
        return False, "entrance ausente ou fora do grid."
    if tile_at([ent["x"], ent["y"]]) != FLOOR:
        return False, "entrance precisa estar em FLOOR (1)."

    def _as_list(key):
        """defn[key] como lista (ausente/None → []); levanta sentinela se tipo errado."""
        v = defn.get(key)
        return [] if v is None else v

    rooms = _as_list("rooms")
    if not isinstance(rooms, list):
        return False, "rooms deve ser uma lista."
    for r in rooms:
        if not isinstance(r, dict):
            return False, "cada sala deve ser um objeto JSON."
    # Precisa de ≥1 sala e de uma sala de entrada — enter_dungeon usa a sala
    # role=="entrance" (e cairia em IndexError com rooms vazio).
    if not rooms:
        return False, "a masmorra precisa de ao menos uma sala."
    if not any(r.get("role") == "entrance" for r in rooms):
        return False, "nenhuma sala com role 'entrance'."
    room_ids = {r.get("id") for r in rooms}
    for r in rooms:
        for d in (r.get("doors") or []):
            if not in_grid(d) or tile_at(d) != DOOR:
                return False, f"porta {d} da sala {r.get('id')} não é um tile DOOR (2)."

    monsters = _as_list("monsters")
    if not isinstance(monsters, list):
        return False, "monsters deve ser uma lista."
    tipos_monstro = {m["type"] for m in MONSTER_DEFS}
    for mo in monsters:
        if not isinstance(mo, dict):
            return False, "cada monstro deve ser um objeto JSON."
        if mo.get("type") not in tipos_monstro:
            return False, f"monstro tipo desconhecido: {mo.get('type')!r}."
        if not in_grid(mo.get("pos")) or tile_at(mo["pos"]) == WALL:
            return False, f"monstro em casa inválida: {mo.get('pos')}."
        if mo.get("room_id") not in room_ids:
            return False, f"monstro com room_id inexistente: {mo.get('room_id')!r}."

    chests = _as_list("chests")
    if not isinstance(chests, list):
        return False, "chests deve ser uma lista."
    for ch in chests:
        if not isinstance(ch, dict):
            return False, "cada baú deve ser um objeto JSON."
        if not in_grid(ch.get("pos")) or tile_at(ch["pos"]) == WALL:
            return False, f"baú em casa inválida: {ch.get('pos')}."
        gold = ch.get("gold", 0)
        if isinstance(gold, bool) or not isinstance(gold, (int, float)) or gold < 0:
            return False, "baú com gold inválido ou negativo."
        for it in (ch.get("items") or []):
            if not isinstance(it, dict):
                return False, f"item de baú inválido: {it!r}."
            if it.get("id") not in _DUNGEON_ITEM_CATALOG:
                return False, f"item de baú desconhecido: {it.get('id')!r}."

    traps = _as_list("traps")
    if not isinstance(traps, list):
        return False, "traps deve ser uma lista."
    for tr in traps:
        if not isinstance(tr, dict):
            return False, "cada armadilha deve ser um objeto JSON."
        if tr.get("tipo") not in ARMADILHAS:
            return False, f"armadilha tipo desconhecido: {tr.get('tipo')!r}."
        if not in_grid(tr.get("pos")) or tile_at(tr["pos"]) == WALL:
            return False, f"armadilha em casa inválida: {tr.get('pos')}."
        if tr["tipo"] == "fosso_envenenado" and tr.get("veneno_id") not in VENENOS:
            return False, f"fosso_envenenado exige veneno_id válido: {tr.get('veneno_id')!r}."

    pr = defn.get("prisoner")
    if pr is not None:
        if not isinstance(pr, dict):
            return False, "prisoner deve ser um objeto JSON."
        if not in_grid(pr.get("pos")) or tile_at(pr["pos"]) == WALL:
            return False, f"prisioneiro em casa inválida: {pr.get('pos')}."
        if pr.get("room_id") not in room_ids:
            return False, f"prisioneiro com room_id inexistente: {pr.get('room_id')!r}."

    ex = defn.get("exit")
    if ex is not None and not in_grid([ex.get("x"), ex.get("y")]):
        return False, "exit fora do grid."

    if _contar_chao_alcancavel(tiles, w, h, [ent["x"], ent["y"]], limite=6) < 6:
        return False, "menos de 6 casas de chão alcançáveis a partir da entrada."

    return True, "ok"

def hidratar_itens_bau(items):
    """Resolve [{'id': ...}] nos dicts completos de CHEST_ITEMS. Ignora ids
    desconhecidos (a validação já recusa antes de chegar aqui)."""
    out = []
    for it in items or []:
        if not isinstance(it, dict):
            continue
        base = _DUNGEON_ITEM_CATALOG.get(it.get("id"))
        if base:
            out.append(deepcopy(base))
    return out

def make_authored_trap(tdef):
    """Cria o dict de uma armadilha de masmorra autorada (hostil, oculta),
    no formato de self.armadilhas. Espelha _gerar_armadilhas_kobold.
    Pressupõe `tdef` já validado por validar_dungeon (tipo/pos presentes)."""
    tipo = tdef["tipo"]
    meta = ARMADILHAS[tipo]
    arm = {
        "id":            new_id(),
        "tipo":          tipo,
        "pos":           [tdef["pos"][0], tdef["pos"][1]],
        "icone":         meta["icone"],
        "nome":          meta["nome"],
        "visivel":       False,
        "ativada":       False,
        "aliada":        False,
        "so_luccas":     False,
        "efeitos_ativos": [],
    }
    if tipo == "fosso_envenenado":
        arm["veneno_id"] = tdef.get("veneno_id")
    return arm

def carregar_dungeon(file):
    """Lê e parseia um arquivo de DUNGEONS_DIR. Retorna dict ou None."""
    if not isinstance(file, str) or not file or file != os.path.basename(file):
        return None  # proteção contra path traversal (sem componente de diretório)
    caminho = os.path.join(DUNGEONS_DIR, file)
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def listar_dungeons():
    """Varre DUNGEONS_DIR e devolve [{id, name, file}] das masmorras válidas."""
    out = []
    try:
        arquivos = sorted(f for f in os.listdir(DUNGEONS_DIR) if f.endswith(".json"))
    except Exception:
        return out
    for file in arquivos:
        defn = carregar_dungeon(file)
        if not defn:
            continue
        ok, _ = validar_dungeon(defn)
        if ok:
            out.append({"id": defn.get("id", file), "name": defn.get("name", file), "file": file})
    return out

CAMPAIGNS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "campaigns")

def carregar_campanha(file):
    """Lê e parseia um arquivo de CAMPAIGNS_DIR. Retorna dict ou None."""
    if not isinstance(file, str) or not file or file != os.path.basename(file):
        return None  # proteção contra path traversal
    caminho = os.path.join(CAMPAIGNS_DIR, file)
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def validar_campanha(defn):
    """Valida um dict de campanha. Retorna (ok: bool, msg: str). Cada fase deve
    existir em dungeons/ e passar em validar_dungeon."""
    if not isinstance(defn, dict):
        return False, "Campanha não é um objeto JSON."
    if defn.get("schema_version") != 1:
        return False, f"schema_version não suportado: {defn.get('schema_version')!r} (esperado 1)."
    dungeons = defn.get("dungeons")
    if not (isinstance(dungeons, list) and len(dungeons) >= 1):
        return False, "campanha precisa de ao menos uma masmorra em 'dungeons'."
    for i, file in enumerate(dungeons):
        d = carregar_dungeon(file) if isinstance(file, str) else None
        if d is None:
            return False, f"fase {i+1}: masmorra '{file}' não encontrada."
        ok, msg = validar_dungeon(d)
        if not ok:
            return False, f"fase {i+1} ('{file}'): {msg}"
    return True, "ok"

def listar_campanhas():
    """Varre CAMPAIGNS_DIR e devolve [{id, name, file}] das campanhas válidas."""
    out = []
    try:
        arquivos = sorted(f for f in os.listdir(CAMPAIGNS_DIR) if f.endswith(".json"))
    except Exception:
        return out
    for file in arquivos:
        defn = carregar_campanha(file)
        if not defn:
            continue
        ok, _ = validar_campanha(defn)
        if ok:
            out.append({"id": defn.get("id", file), "name": defn.get("name", file), "file": file})
    return out

# ─── ARMADILHAS ───────────────────────────────────────────────────────────────
# Sistema de armadilhas COLOCÁVEIS (distinto das `self.traps` geradas na masmorra).
# São criadas pelo Luccas (rogue) ou disparadas por quem pisar na casa. Cada
# armadilha viva é um dict em self.armadilhas (ver _NOVA_ARMADILHA). O efeito é
# aplicado via _disparar_armadilha → _aplicar_efeito_armadilha a QUALQUER alvo
# (jogador OU monstro): um teste de Reflexos decide se evita/sofre.
#
# Adaptação ao modelo de dados do servidor (≠ spec original):
#   • posições são `pos:[x,y]` (não tx/ty)
#   • self.monsters é dict (itera .values()); ouro é p["gold"]; Luccas = class_id "rogue"
#   • fome/sede em escala 0–100; saves via _testar_save (Reflexos = ref_)
#   • veneno do "fosso envenenado" reutiliza _aplicar_veneno
#   • dano progressivo (incendiária) tica em _processar_efeitos_armadilha_turno
ARMADILHA_CUSTO_FOME = 2   # criar uma armadilha consome recurso do criador
ARMADILHA_CUSTO_SEDE = 1

ARMADILHAS = {
    "buraco": {
        "nome": "Buraco", "icone": "🕳️", "dificuldade": 10, "save": "reflexos",
        "custo_ouro": 0, "persiste": True, "visivel_apos": True,
        "efeitos": [{"tipo": "perder_movimento"}],
        "descricao": "Reflexos dif 10 ou perde o movimento. Permanece ativa.",
    },
    "armadilha_urso": {
        "nome": "Armadilha de Urso", "icone": "🪤", "dificuldade": 10, "save": "reflexos",
        "custo_ouro": 1, "persiste": False,
        "efeitos": [{"tipo": "dano", "valor": "1d4", "elemento": "fisico"},
                    {"tipo": "perder_movimento"}],
        "descricao": "1d4 de dano + perde movimento. Some após ativar.",
    },
    "fosso_estacas": {
        "nome": "Fosso com Estacas", "icone": "⛏️", "dificuldade": 10, "save": "reflexos",
        "custo_ouro": 2, "persiste": True, "visivel_apos": True,
        "efeitos": [{"tipo": "dano", "valor": "1d6", "elemento": "fisico"},
                    {"tipo": "perder_movimento"}],
        "descricao": "1d6 de dano + perde movimento. Fica visível após ativar.",
    },
    "rede": {
        "nome": "Rede", "icone": "🕸️", "dificuldade": 11, "save": "reflexos",
        "custo_ouro": 4, "persiste": False,
        "efeitos": [{"tipo": "perder_rodada"}],
        "descricao": "Perde a rodada inteira. Some após ativar.",
    },
    "armadilha_incendiaria": {
        "nome": "Armadilha Incendiária", "icone": "🔥", "dificuldade": 12, "save": "reflexos",
        "custo_ouro": 10, "persiste": False,
        "efeitos": [{"tipo": "dano", "valor": "1d6", "elemento": "fogo", "rodada": 1},
                    {"tipo": "dano", "valor": "1d4", "elemento": "fogo", "rodada": 2},
                    {"tipo": "dano", "valor": "1",   "elemento": "fogo", "rodada": 3}],
        "descricao": "Dano de fogo progressivo: 1d6 + 1d4 + 1 em 3 rodadas.",
    },
    "mina_terrestre": {
        "nome": "Mina Terrestre", "icone": "💣", "dificuldade": 12, "save": "reflexos",
        "save_reduz": True, "custo_ouro": 20, "persiste": False, "area": 1,
        "efeitos": [{"tipo": "dano", "valor": "2d6", "elemento": "explosao", "area": True}],
        "descricao": "2d6 de dano em área de 1 quadrado. Save reduz à metade.",
    },
    "fosso_envenenado": {
        "nome": "Fosso com Estacas Envenenadas", "icone": "☠️", "dificuldade": 10,
        "save": "reflexos", "custo_ouro": 2, "custo_veneno": True,
        "persiste": True, "visivel_apos": True,
        "efeitos": [{"tipo": "dano", "valor": "1d6", "elemento": "fisico"},
                    {"tipo": "veneno"}],
        "descricao": "1d6 de dano + efeito do veneno usado. Fica visível após ativar.",
    },
    "nuvem_gas": {
        "nome": "Nuvem de Gás", "icone": "🌫️", "dificuldade": 13, "save": "fortitude",
        "custo_ouro": 25, "persiste": False, "area": 1,
        "efeitos": [{"tipo": "reduzir_con", "valor": "1d6", "duracao": 3, "area": True}],
        "descricao": "-1d6 CON por 3 rodadas em área. Recalcula HP.",
    },
}

SHOP_TEMPLE = [
    {"id": "full_heal", "name": "Cura Completa",  "emoji": "💖",  "price": 15, "effect": "full_heal"},
    {"id": "full_mana", "name": "Restaurar Mana", "emoji": "🔷",  "price": 10, "effect": "full_mana"},
    {"id": "bless",     "name": "Bênção Divina",  "emoji": "✨",  "price": 12, "effect": "bless",    "value": 2},
    {"id": "cleanse",   "name": "Purificação",    "emoji": "🕊️", "price": 8,  "effect": "cleanse"},
]

SHOP_TAVERN = [
    # ── Refeições de balcão: consumidas na hora, NÃO ocupam slot, 1×/visita à cidade ──
    {"id": "refeicao_simples", "name": "Refeição Simples", "emoji": "🍲", "price": 4,  "effect": "meal_survival", "fome": 25, "sede": 25},
    {"id": "banquete",         "name": "Banquete",         "emoji": "🍗", "price": 10, "effect": "meal_survival", "fome": 50, "sede": 50},
    # ── Provisões: vão para a mochila (1 slot cada), consumidas depois via "usar item" ──
    {"id": "pao",            "name": "Pão",              "emoji": "🥖", "price": 1,  "item_slot": "bag", "effect": "food", "fome": 10, "sede": 0},
    {"id": "garrafa_agua",   "name": "Garrafa de Água",  "emoji": "💧", "price": 2,  "item_slot": "bag", "effect": "food", "fome": 0,  "sede": 10},
    {"id": "suco_fruta",     "name": "Suco de Fruta",    "emoji": "🧃", "price": 5,  "item_slot": "bag", "effect": "food", "fome": 5,  "sede": 10},
    {"id": "caneca_cerveja", "name": "Caneca de Cerveja","emoji": "🍺", "price": 5,  "item_slot": "bag", "effect": "ale",  "value": 10},
    {"id": "garrafa_vinho",  "name": "Garrafa de Vinho", "emoji": "🍷", "price": 10, "item_slot": "bag", "effect": "wine", "value": 15},
    {"id": "racao_viagem",   "name": "Ração de Viagem",  "emoji": "🥩", "price": 20, "item_slot": "bag", "effect": "food", "fome": 20, "sede": 0},
    {"id": "cantil_agua",    "name": "Cantil de Água",   "emoji": "🧴", "price": 25, "item_slot": "bag", "effect": "food", "fome": 0,  "sede": 20},
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
            # Salas começam trancadas (porta fechada), exceto a entrada. Heróis
            # precisam abrir a porta para entrar; monstros lá dentro ficam
            # dormentes até a porta ser aberta.
            "locked": role != "entrance",
            "doors": [],   # tiles DOOR no anel externo (entradas da sala)
        })

    # ── Detect doorways: UMA porta por entrada/saída ─────────────────────────
    # Uma "abertura" é um grupo contíguo de casas de corredor coladas à borda
    # interna da sala. Cada abertura recebe UMA porta (no limiar, lado do
    # corredor); as demais casas da abertura são fechadas SELANDO a parede do
    # lado da SALA (a borda interna vira WALL). Nunca fechamos o corredor — isso
    # poderia cortar passagens e desconectar o mapa. Resultado: cada sala fica
    # com paredes limpas e portas de 1 casa exatamente nas entradas/saídas.
    for room in room_data:
        rx0, ry0, rw, rh = room["x"], room["y"], room["w"], room["h"]
        # casa de corredor (fora) -> casa de borda interna correspondente
        corr_to_edge = {}
        for iy in range(ry0, ry0 + rh):
            for ix in range(rx0, rx0 + rw):
                if not (ix == rx0 or ix == rx0 + rw - 1 or iy == ry0 or iy == ry0 + rh - 1):
                    continue
                for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                    nx, ny = ix + dx, iy + dy
                    if not (0 <= nx < MAP_W and 0 <= ny < MAP_H):
                        continue
                    if room_contains(room, nx, ny):
                        continue  # ainda dentro da sala
                    if tiles[ny][nx] in (FLOOR, DOOR):
                        corr_to_edge.setdefault((nx, ny), (ix, iy))

        # agrupa casas de corredor contíguas (4-dir) → cada grupo é uma abertura
        corr_tiles = set(corr_to_edge)
        nao_visto  = set(corr_tiles)
        aberturas  = []
        while nao_visto:
            ini = nao_visto.pop()
            pilha = [ini]; grupo = [ini]
            while pilha:
                x, y = pilha.pop()
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    n = (x + dx, y + dy)
                    if n in nao_visto:
                        nao_visto.discard(n); pilha.append(n); grupo.append(n)
            aberturas.append(sorted(grupo))

        # escolhe a porta (casa central) de cada abertura; guarda as bordas das
        # portas E suas vizinhas internas — assim a casa interna da porta nunca
        # fica isolada do miolo da sala (caso de porta num canto do retângulo).
        portas    = [g[len(g) // 2] for g in aberturas]
        protegido = set()
        for p in portas:
            ex, ey = corr_to_edge[p]
            protegido.add((ex, ey))
            for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if room_contains(room, ex + ddx, ey + ddy):
                    protegido.add((ex + ddx, ey + ddy))

        for grupo, porta in zip(aberturas, portas):
            for c in grupo:
                if c == porta:
                    if tiles[c[1]][c[0]] == FLOOR:
                        tiles[c[1]][c[0]] = DOOR
                    if [c[0], c[1]] not in room["doors"]:
                        room["doors"].append([c[0], c[1]])
                else:
                    e = corr_to_edge[c]
                    if e not in protegido:             # não isola a entrada de nenhuma porta
                        tiles[e[1]][e[0]] = WALL        # fecha a parede da sala (lado interno)

    return tiles, room_data

def room_contains(room, tx, ty):
    return room["x"] <= tx < room["x"] + room["w"] and room["y"] <= ty < room["y"] + room["h"]

def player_room(rooms, px, py):
    for r in rooms:
        if room_contains(r, px, py):
            return r
    return None

# ─── GRIMÓRIO (SISTEMA DE MAGIAS) ─────────────────────────────────────────────
# Catálogo autoritativo de magias de Pedro (mage) e Lewis (cleric). Esta é a
# camada de DADOS da fundação do sistema de magias; o dispatcher e o roteamento
# ficam em GameRoom (handle_magia / _executar_magia_grimorio).
#
# Adaptação ao modelo de dados do servidor (≠ spec original):
#   • atributos do caster são scores brutos (int_) — bônus via mod(p["int_"])
#   • self.monsters é dict (itera .values()); posições são pos:[x,y] (não tx/ty)
#   • saves via _testar_save (tupla); INT, fome/sede 0–10, log via gm_say
#   • custo = MP do círculo (CIRCULO_MP) + 🍖/💧 de sobrevivência da ação
#   • zonas (escuridão/silêncio) vivem em self.zonas_especiais e ticam por rodada
#
# FUNDAÇÃO: por ora apenas o sistema de escuridão/visão está conjurável
# (GRIMORIO_IMPLEMENTADAS). As demais magias entram nos próximos prompts.
CIRCULO_MP = {"primeiro": 1, "segundo": 2, "terceiro": 3}

# ─── PERGAMINHOS MÁGICOS ───────────────────────────────────────────────────────
# Item de uso único que guarda UMA magia do grimório. Só mago/clérigo usam.
# Nível necessário p/ lançar o círculo normalmente (usado no cálculo de falha):
PERGAMINHO_NIVEL_CIRCULO = {"primeiro": 1, "segundo": 3, "terceiro": 5}
PERGAMINHO_CIRCULO_NOME  = {1: "primeiro", 2: "segundo", 3: "terceiro"}
PERGAMINHO_PRECO_BASE    = {"primeiro": 20, "segundo": 40, "terceiro": 70}
# Acréscimo de preço (moedas) por bônus de INT do pergaminho (+0..+5).
PERGAMINHO_INT_SURCHARGE = {0: 0, 1: 10, 2: 20, 3: 40, 4: 50, 5: 100}
PERGAMINHO_NIVEL_MAX     = 5    # a escala de dano/alcance satura no nível 5
PERGAMINHO_INT_MAX       = 5    # bônus de INT máximo (INT 20)
PERGAMINHO_FALHA_MAX     = 95   # teto da chance de falha / efeito nocivo (sempre 5% de chance)

# Lewis (cleric) NÃO usa MP — suas magias custam SLOTS por círculo (magias por dia).
# MODO DE TESTE: todos os círculos liberados desde o nível 1 e com folga de slots,
# para que todas as magias possam ser testadas agora (ignora requisito de nível).
# Os slots são resetados no início de cada turno do clérigo (ver _start de turno).
CLERIC_SLOTS = {"primeiro": 9, "segundo": 9, "terceiro": 9}

# Magias cuja lógica já está implementada (as demais retornam "em desenvolvimento").
# ⚠️ MODO TESTE: Pedro (mage) lança QUALQUER magia do grimório ignorando classe,
# círculo/nível, MP/slots, custo de 🍖/💧 e o limite de 1 ação por turno. Para testar
# o grimório livremente. Defina False para voltar ao comportamento normal.
MAGE_TESTE_LIVRE = False

GRIMORIO_IMPLEMENTADAS = {"manto_escuridao", "visao_escuro",
                          "bola_fogo", "relampago", "raio_congelante",
                          "saciar", "criar_alimentos", "clarividencia", "raio_divino",
                          "abencoar", "amaldicoar", "abencoar_arma",
                          "sono", "medo", "comando", "dominar_mente",
                          "dominar_morto_vivo", "lentidao",
                          "invisibilidade", "regeneracao_magica", "jato_ar",
                          "velocidade", "protecao_energia", "conjurar_elemental",
                          "silencio", "barreira_arcana", "contramagica"}

GRIMORIO = {
    # ── 1º CÍRCULO — MAGO ─────────────────────────────────────────────────────
    "bola_fogo": {
        "id": "bola_fogo", "nome": "Bola de Fogo",
        "circulo": "primeiro", "classe": ["mage"],
        "icone": "🔥", "tipo": "area_persistente",
        "alcance_base": 5, "alcance_escala": 1,   # +1 por nível
        "area_raio": 2,
        "dano_por_nivel": "1d6",                   # 1d6 por nível na rodada 1
        "save": "reflexos", "save_efeito": "metade",
        "rodadas": 3, "dano_decai": True,          # R2 = ½R1, R3 = ½R2
        "entrar_sofre_dano": True, "sair_evita": True,
        "descricao": "1d6/nível. Área persiste 3 rodadas com dano decaindo.",
    },
    "relampago": {
        "id": "relampago", "nome": "Relâmpago",
        "circulo": "primeiro", "classe": ["mage"],
        "icone": "⚡", "tipo": "linha_reflexiva",
        "alcance_base": 7, "alcance_escala": 2,    # 7 casas no nível 1 (+2/nível)
        "dano_por_nivel": "1d6",                   # 1d6 por nível por impacto
        "save": "reflexos", "save_efeito": "metade",
        "pode_ferir_aliados": True, "pode_ferir_caster": True,
        "ricochete_volta": True,                   # ricocheteia de volta pelo mesmo trajeto
        "dano_por_impacto": True, "save_por_impacto": True,
        "descricao": "1d6/nível por impacto. Linha reta de 7 casas + ricochete de volta (casas atingidas 2x). Pedro só é ferido na volta.",
    },
    "raio_congelante": {
        "id": "raio_congelante", "nome": "Raio Congelante",
        "circulo": "primeiro", "classe": ["mage"],
        "icone": "❄️", "tipo": "alvo",
        "alcance_base": 3, "alcance_escala": 1,    # +1 por nível
        "dano_base": "3d4", "dano_escala": "2d4",  # +2d4 a cada 2 níveis
        "sem_save_dano": True,                     # dano sempre total, sem Reflexos
        "save": "fortitude",                       # save só para paralisação
        "paralisado_rodadas_max": 2, "novo_teste_por_rodada": True,
        "descricao": "3d4+2d4/2níveis sem save. Fortitude ou paralisado 1-2 rodadas.",
    },
    "sono": {
        "id": "sono", "nome": "Sono",
        "circulo": "primeiro", "classe": ["mage"],
        "icone": "🌙", "tipo": "area",
        "alcance": 5, "area_raio": 2,
        "save": "vontade", "save_efeito": "nenhum",
        "efeito_falha": "dormindo",
        "duracao": "1d4+1",
        "primeiro_ataque_critico": True,
        "acorda_com_dano": True,
        "descricao": "Área. Vontade ou dorme 1d4+1. Primeiro ataque = crítico. Acorda com dano.",
    },
    "comando": {
        "id": "comando", "nome": "Comando",
        "circulo": "primeiro", "classe": ["mage", "cleric"],
        "icone": "🗣️", "tipo": "alvo",
        "alcance": 4,
        "save": "vontade", "save_efeito": "nenhum",
        "efeito_falha": "controlado",
        "duracao": 1, "sem_habilidades": True,
        "descricao": "Vontade ou controla 1 ação do alvo. Sem habilidades especiais.",
    },
    "medo": {
        "id": "medo", "nome": "Medo",
        "circulo": "primeiro", "classe": ["mage", "cleric"],
        "icone": "😱", "tipo": "area",
        "alcance": 5, "area_raio": 2,
        "save": "vontade", "save_efeito": "nenhum",
        "efeito_falha": "com_medo",
        "duracao": "1d4+1",
        "penalidade_ataque": -1,
        "descricao": "Área. Vontade ou foge 1d4+1 rodadas. -1 ataque. Não se aproxima.",
    },
    "clarividencia": {
        "id": "clarividencia", "nome": "Clarividência",
        "circulo": "primeiro", "classe": ["mage", "cleric"],
        "icone": "🔮", "tipo": "area_fixa",
        "area_base": 4,
        "duracao": 2, "remove_nevoa": True,
        "escala_nivel": True,
        "descricao": "Remove névoa em área 4x4 (+escala por nível). Dura 2 rodadas.",
    },
    "barreira_arcana": {
        "id": "barreira_arcana", "nome": "Barreira Arcana",
        "circulo": "primeiro", "classe": ["mage"],
        "icone": "🛡️", "tipo": "buff_self",
        "duracao": "ate_absorver",
        "slot_ao_absorver": True,
        "descricao": "Cancela 1 magia recebida. Slot consumido ao absorver. Dura até ativar.",
    },
    "contramagica": {
        "id": "contramagica", "nome": "Contramágica",
        "circulo": "primeiro", "classe": ["mage"],
        "icone": "🛑", "tipo": "reacao",
        "save": "teste_oposto",
        "slot_ao_usar": True,
        "descricao": "Reação. Teste oposto vs magia inimiga. Sucesso: cancela + inimigo perde ação.",
    },
    # ── 1º CÍRCULO — CLÉRIGO ──────────────────────────────────────────────────
    "abencoar": {
        "id": "abencoar", "nome": "Abençoar",
        "circulo": "primeiro", "classe": ["cleric"],
        "icone": "✨", "tipo": "area",
        "alcance": 0, "area_raio": 3,
        "buff": {"ataque": 1, "dano": 1, "ca": 1, "resistencia": 1},
        "duracao": "1d4+1",
        "descricao": "Área 6x6. +1 ataque/dano/CA/resistência. Dura 1d4+1 rodadas.",
    },
    "amaldicoar": {
        "id": "amaldicoar", "nome": "Amaldiçoar",
        "circulo": "primeiro", "classe": ["cleric"],
        "icone": "☠️", "tipo": "area",
        "alcance": 5, "area_raio": 1,
        "debuff": {"ataque": -1, "dano": -1, "ca": -1, "resistencia": -1},
        "duracao": "1d4+1",
        "descricao": "Área 3x3. -1 ataque/dano/CA/resistência. Dura 1d4+1 rodadas.",
    },
    "abencoar_arma": {
        "id": "abencoar_arma", "nome": "Abençoar Arma",
        "circulo": "primeiro", "classe": ["cleric"],
        "icone": "⚔️", "tipo": "alvo_aliado",
        "alcance": 6,
        "buff": {"ataque": 1, "dano": 1},
        "duracao": "1d6+2",
        "descricao": "+1 ataque e dano na arma de aliado. Dura 1d6+2 rodadas.",
    },
    "saciar": {
        "id": "saciar", "nome": "Saciar",
        "circulo": "primeiro", "classe": ["cleric"],
        "icone": "💧", "tipo": "toque",
        "alcance": 1,
        "fome_bonus": 10, "sede_bonus": 10,
        "descricao": "Toque. +10 fome +10 sede em 1 aliado.",
    },
    # ── 2º CÍRCULO — AMBOS ────────────────────────────────────────────────────
    "silencio": {
        "id": "silencio", "nome": "Silêncio",
        "circulo": "segundo", "classe": ["mage", "cleric"],
        "icone": "🔇", "tipo": "area_fixa",
        "alcance_base": 5, "alcance_escala": 1,   # 5 + 1 por 2 níveis
        "area_lado": 4,                            # área 4x4
        "bloqueia_magias": True, "bloqueia_cancao": True,
        "duracao": "1d4",
        "descricao": "Área 4x4. Sem magias nem bônus de Canção Heroica dentro. Dura 1d4 rodadas.",
    },
    "manto_escuridao": {
        "id": "manto_escuridao", "nome": "Manto de Escuridão",
        "circulo": "segundo", "classe": ["mage", "cleric"],
        "icone": "🌑", "tipo": "area_centrada",
        "area_raio": 3,
        "sistema_escuridao": True,
        "duracao": "1d4",
        "descricao": "Raio 3. Escuridão — sem visão noturna: desvantagem. Com visão noturna: vantagem.",
    },
    "criar_alimentos": {
        "id": "criar_alimentos", "nome": "Criar Alimentos",
        "circulo": "segundo", "classe": ["cleric"],
        "icone": "🍞", "tipo": "utilidade",
        "agua": "1d6+1", "pao": "1d6+2",
        "descricao": "Cria 1d6+1 água e 1d6+2 pão. Lewis distribui para o grupo.",
    },
    "regeneracao_magica": {
        "id": "regeneracao_magica", "nome": "Regeneração",
        "circulo": "segundo", "classe": ["cleric"],
        "icone": "🌿", "tipo": "buff_aliado",
        "alcance": 6,
        "pool": "2d6+2", "cura_por_rodada": 1,
        "resurrect_com_pool": True,
        "fome_sede_ao_ressurgir": -3,
        "descricao": "Pool 2d6+2. +1 HP/rodada. Se morrer: volta com 1 HP -3 fome/sede.",
    },
    "protecao_energia": {
        "id": "protecao_energia", "nome": "Proteção contra Energia",
        "circulo": "segundo", "classe": ["mage", "cleric"],
        "icone": "🛡️", "tipo": "buff_self",
        "reducao_por_rodada": 10,
        "tipos": ["fogo", "gelo", "eletricidade"],
        "duracao": "1d6+1",
        "descricao": "Absorve 10 dano/rodada de fogo, gelo ou eletricidade. Dura 1d6+1.",
    },
    "invisibilidade": {
        "id": "invisibilidade", "nome": "Invisibilidade",
        "circulo": "segundo", "classe": ["mage"],
        "icone": "🫥", "tipo": "buff_self",
        "duracao": "1d6+1",
        "vantagem_ataque": True,
        "ativa_furtivo": True,
        "quebra_ao_atacar": True,
        "quebra_ao_lancar": True,
        "descricao": "Inimigos não atacam. Ataque com vantagem + furtivo. Quebra ao atacar/lançar.",
    },
    "visao_escuro": {
        "id": "visao_escuro", "nome": "Visão no Escuro",
        "circulo": "segundo", "classe": ["mage", "cleric"],
        "icone": "👁️", "tipo": "buff_aliado",
        "alcance": 6,
        "ignora_escuridao": True,
        "duracao": "1d6+2",
        "descricao": "Aliado ignora escuridão completamente. Dura 1d6+2 rodadas.",
    },
    "jato_ar": {
        "id": "jato_ar", "nome": "Jato de Ar",
        "circulo": "segundo", "classe": ["mage"],
        "icone": "🌪️", "tipo": "cone",
        "comprimento": 4, "base_largura": 4,
        "dano": "1d6",
        "save": "reflexos",
        "empurra_falha": "1d6", "empurra_sucesso": 2,
        "dano_colisao": "1d4",
        "descricao": "Cone 4q. 1d6 dano. Falha: empurra 1d6q. Colisão com parede: +1d4.",
    },
    # ── 3º CÍRCULO ────────────────────────────────────────────────────────────
    "velocidade": {
        "id": "velocidade", "nome": "Velocidade",
        "circulo": "terceiro", "classe": ["mage"],
        "icone": "⚡", "tipo": "buff_self",
        "dobra_acoes": True,
        "duracao": "1d4",
        "descricao": "Dobra todas as ações no turno. Custo normal por ação. Dura 1d4 rodadas.",
    },
    "lentidao": {
        "id": "lentidao", "nome": "Lentidão",
        "circulo": "terceiro", "classe": ["mage"],
        "icone": "🐌", "tipo": "area",
        "alcance": 5, "area_raio": 1,
        "save": "vontade",
        "efeito_falha": {"acoes": 1, "reacao": False, "ca": -1},
        "efeito_sucesso": {"movimento": "metade", "ataque": -1},
        "duracao": "1d4",
        "descricao": "Área 3x3. Falha: 1 ação/rodada, -1 CA, sem reação. Sucesso: mov/2, -1 ataque.",
    },
    "dominar_mente": {
        "id": "dominar_mente", "nome": "Dominar Mente",
        "circulo": "terceiro", "classe": ["mage", "cleric"],
        "icone": "🧠", "tipo": "alvo",
        "alcance": 5,
        "save": "vontade", "save_efeito": "nenhum",
        "efeito_falha": "dominado",
        "duracao": "1d4",
        "novo_teste_ao_dano": True,
        "descricao": "Vontade ou dominado 1d4 rodadas. Novo teste ao sofrer dano.",
    },
    "dominar_morto_vivo": {
        "id": "dominar_morto_vivo", "nome": "Dominar Morto-Vivo",
        "circulo": "terceiro", "classe": ["mage"],
        "icone": "💀", "tipo": "alvo",
        "alcance": 4,
        "requer_tipo": "morto_vivo",
        "save": "vontade", "save_efeito": "nenhum",
        "controle_progressivo": True,        # 3 rodadas de Vontade (bônus = ND) → controle total
        "conta_slots_animar": False,         # slot único, fora do orçamento de Animar Mortos
        "descricao": "Morto-vivo testa Vontade (bônus = ND) ao ser lançada e a cada rodada na "
                     "fase dos servos. Passar quebra o controle (volta hostil); 3 falhas seguidas "
                     "= controle permanente. Slot único. Não conta para Animar Mortos.",
    },
    "conjurar_elemental": {
        "id": "conjurar_elemental", "nome": "Conjurar Elemental",
        "circulo": "terceiro", "classe": ["cleric"],
        "icone": "🌪️", "tipo": "invocacao",
        "tipos": {
            "fogo":     {"hp": 18, "dano": "2d6", "especial": "explosao_6d6"},
            "eletrico": {"hp": 20, "dano": "1d8", "especial": "linha_3q"},
            "gelo":     {"hp": 22, "dano": "1d6", "especial": "-2_fisico_+2_fogo"},
            "pedra":    {"hp": 26, "dano": "1d8", "especial": "metade_fisico"},
        },
        "movimento": 6, "age_apos_lewis": True,
        "controlado": True, "explosao_afeta_aliados": True,
        "descricao": "Invoca elemental controlado. Age após Lewis. Movimento 6q.",
    },
    "raio_divino": {
        "id": "raio_divino", "nome": "Raio Divino",
        "circulo": "terceiro", "classe": ["cleric"],
        "icone": "✨", "tipo": "alvo",
        "alcance": 6,
        "dano_por_nivel": "1d6+1",
        "save": "reflexos", "save_efeito": "metade",
        "dobrado_vs": ["morto_vivo", "demonio"],
        "descricao": "1d6+1 por nível. Reflexos: metade. Dobrado vs mortos-vivos e demônios.",
    },
}

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

# Mão secundária inicial (dual-wield) por classe — EQUIPAMENTOS_INICIAIS.
# Item de off_hand com `die`/`stat` → habilita o ataque de mão secundária no
# combate. effect "none"/value 0 → não altera CA/atributos.
_STARTING_OFFHAND = {
    "rogue": {"id": "adaga_secundaria", "name": "Adaga Secundária", "emoji": "🗡️",
              "item_slot": "off_hand", "kind": "weapon", "die": "1d4", "stat": "str_",
              "finesse": True, "throw_range": 3, "effect": "none", "value": 0},
    "bard":  {"id": "dagger", "name": "Adaga", "emoji": "🗡️",
              "item_slot": "off_hand", "kind": "weapon", "die": "1d4", "stat": "str_",
              "finesse": True, "throw_range": 3, "effect": "none", "value": 0},
}

_WEAPON_EMOJI = {
    "unarmed": "✊", "dagger": "🗡️", "bordao": "🪄", "staff": "🪄",
    "machado_basico": "🪓", "cajado_madeira": "🪄", "instrumento": "🎵",
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

# ─── SLOT SECUNDÁRIO — regras por personagem ──────────────────────────────────
# ATENÇÃO (scaffolding): estas regras usam as chaves de herói do CLIENTE
# (victorCoiceBravo, luccas, …) e ids em português do CATALOGO_ITENS do cliente.
# O servidor hoje usa `class_id` (warrior, rogue, …), slot `off_hand` e ids em
# inglês — então `handle_equip`/`_pode_equipar_secundario` abaixo AINDA NÃO são
# chamados pelo roteador de mensagens nem casam com os itens do servidor. Inserido
# verbatim conforme especificação, à espera da reconciliação catálogo↔servidor.
SECUNDARIO_PERMITIDO = {
    'victorCoiceBravo': ['escudo_leve', 'escudo_pesado', 'tocha', 'adaga_secundaria'],
    'richardCavaleiro': ['escudo_leve', 'escudo_pesado', 'tocha'],
    'lewis':            ['escudo_leve', 'tocha', 'grimorio'],
    'luccas':           ['escudo_leve', 'tocha', 'adaga_secundaria'],
    'henrique':         ['tocha', 'adaga_secundaria'],
    'pedro':            ['varinha_simples', 'varinha_poder',
                         'varinha_arcana', 'grimorio', 'tocha'],
}

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
            "off_hand": deepcopy(_STARTING_OFFHAND.get(cls_id)),  # mão esquerda: arma 2ª / escudo (dual-wield inicial)
            "armor":    starting_armor_item,   # corpo
            "head":     None,                  # elmo / tiara / capuz
            "ring1":    None,                  # anel
            "ring2":    None,                  # anel
            "item1":    None,                  # item ativo (mochila/luvas/cinto)
            "item2":    None,                  # item ativo
        },
        "status": [],
        "alive": True,
        "connected": True,   # False quando o jogador cai/sai — sai da masmorra e é pulado nos turnos
        "pos": [0, 0],
        "moves_left": cls["spd"],
        "action_done": False,
        "bonus_action_used": False,   # reseta a cada turno — máx. 1 ação bônus por turno
        "fome": 100,                  # 0–100 (escala unificada servidor/cliente)
        "sede": 100,                  # 0–100
        "taverna_refeicoes": [],      # refeições de balcão já usadas nesta visita à cidade
        "moved_this_turn": False,     # caminhar custa -1 sede só na 1ª casa do turno
        "slot": slot,
        "skills": cls["skills"],
        # Buffs de turno do warrior (flags planas) — limpos em handle_end_turn
        "skill_bonus_acerto": 0,
        "skill_dobrar_dano":  False,
        "skill_ataque_extra": False,
        "skill_extra_usado":  False,   # Fúria: extra (2º ataque) já concedido neste turno
        # Canção Heroica do bardo (toggle) — estado próprio; inerte para outras classes
        "cancao_ativa":       False,
        "cancao_atributos":   [],
        "cancao_custo":       {"fome": 0, "sede": 0},
        "cancao_atacou_apos": False,   # já pagou o custo extra de ataque sob canção neste turno?
        # buffs_cancao é injetado/removido nos aliados no raio (ver _aplicar_buffs_cancao)
        # ── Estado das habilidades do paladino (Richard) — inerte p/ outras classes ──
        "golpe_sagrado_ativo": False,  # +1d8 sagrado por ataque (manutenção 🍖-1 💧-1)
        "protetor_ativo":      False,  # divide o dano recebido por um aliado protegido
        "protetor_alvo":       None,   # pid do aliado sob Protetor
        "regeneracao_ativa":   False,  # +1 HP por turno (manutenção 🍖-1 💧-1)
        "guerreiro_luz_ativo": False,  # buff de combate (visão/ataque/dano/CA)
        "guerreiro_luz_bonus": {},     # {"visao","ataque","dano","ca"} — 0..2 cada
        "guerreiro_luz_custo": {"fome": 0, "sede": 0},  # manutenção por turno
        # ── Metamagia do mago (Pedro) — inerte p/ outras classes ──
        "aprimorar_ativo":   False,  # Aprimorar Magia armada → +1 CD do save (🍖-3 ao lançar)
        "estender_ativo":    False,  # Estender Magia armada → +1 turno de duração (🍖-3 💧-3)
        "fortalecer_ativo":  False,  # Fortalecer Magia armada → dano ×1,5 (🍖-6 💧-6)
        # ── Estado das habilidades do ladino (Luccas) — inerte p/ outras classes ──
        "invisivel_sombras":   False,  # Esconder nas Sombras (manutenção 🍖-1 💧-1)
        "detectar_ativo":      False,  # Detectar Armadilhas ativa (manutenção 💧-1)
        "weapon_poison":       None,   # veneno untado na arma (Veneno Rápido / coat_poison)
        "weapon_poison_hits":  0,      # golpes certeiros restantes com veneno
        # ── Magias de Lewis (cleric) — slots por círculo (não usa MP) ──────────────
        "magias_usadas_hoje":  {"primeiro": 0, "segundo": 0, "terceiro": 0},
        "magias_conhecidas":   [],     # ids do GRIMORIO memorizados (vazio = todas da classe)
    }

def make_monster(mdef, room):
    m = deepcopy(mdef)
    m["id"] = new_id()
    m["max_hp"] = m["hp"]
    m["pos"] = [room["cx"], room["cy"]]
    m["room_id"] = room["id"]
    # Inicializa contadores de habilidades especiais (formato novo)
    if "special_abilities" in m:
        m["ability_uses"] = {
            ab["id"]: ab["uses_per_combat"]
            for ab in m["special_abilities"]
            if "uses_per_combat" in ab and ab["uses_per_combat"] is not None
        }
        m["ability_cooldowns"] = {}
    # ── Goblins: munição do arqueiro, escolha de arma do combatente, arremesso ──
    if m.get("type") == "goblin_arqueiro":
        m["flechas"] = 10
        m["pode_arremessar"] = False
    if m.get("type") == "goblin_combatente":
        if random.random() < 0.5:
            m["attacks"] = [{"name": "Adaga", "atk_bonus": 4, "damage": "1d4+2",
                             "damage_types": ["physical"], "num_attacks": 1,
                             "on_hit": None, "categoria": "perfurante"}]
            m["guaranteed_loot"] = ["dagger"]
        else:
            m["attacks"] = [{"name": "Espada Curta", "atk_bonus": 2, "damage": "1d6",
                             "damage_types": ["physical"], "num_attacks": 1,
                             "on_hit": None, "categoria": "cortante"}]
            m["guaranteed_loot"] = ["shortsword", "dagger"]
        m["pode_arremessar"] = True
    if m.get("type") == "goblin_dual":
        m["pode_arremessar"] = True
    # ── Kobold Lanceiro: lança envenenada + doses extras ──────────────────────
    if m.get("type") == "kobold_lanceiro":
        m["veneno_arma_ativo"]  = True               # 1 dose já aplicada na lança
        m["veneno_arma_id"]     = "veneno_aranha_sombria"
        m["veneno_doses_extras"] = random.randint(1, 3)   # 1–3 frascos extras
        m["covardia_testada"]   = False
        m["kobold_medo"]        = False
        m["kobold_medo_rodadas"] = 0
    # ── Kobold Besteiro: virotes normais + 10% de virotes especiais ──────────
    if m.get("type") == "kobold_besteiro":
        m["virotes"]            = 10
        m["virotes_especiais_tipo"]  = None
        m["virotes_especiais_count"] = 0
        if random.randint(1, 100) <= 10:
            tipo_roll = random.randint(1, 2)
            m["virotes_especiais_tipo"]  = ("veneno_escorpiao_pedra" if tipo_roll == 1
                                             else "incendiario")
            m["virotes_especiais_count"] = roll_dice("1d4")
        m["covardia_testada"]   = False
        m["kobold_medo"]        = False
        m["kobold_medo_rodadas"] = 0
    # ── Esqueleto Humano: sorteia arma ao criar ────────────────────────────────
    if m.get("type") == "esqueleto_humano":
        _roll = random.randint(1, 100)
        if _roll <= 30:
            _nome, _die, _cat, _range = "Espada Curta",  "1d6",  "cortante",   None
            m["esqueleto_arma_id"] = "shortsword"
        elif _roll <= 60:
            _nome, _die, _cat, _range = "Lança",         "1d6",  "perfurante", 2
            m["esqueleto_arma_id"] = "lanca_curta"
        elif _roll <= 70:
            _nome, _die, _cat, _range = "Espada Longa",  "1d8",  "cortante",   None
            m["esqueleto_arma_id"] = "longsword"
        elif _roll <= 80:
            _nome, _die, _cat, _range = "Espada Curta",  "1d6",  "cortante",   None
            m["esqueleto_arma_id"] = "shortsword"
            m["ac"] += 2   # escudo: CA 12 → 14
            m["esqueleto_escudo"] = True
        elif _roll <= 90:
            _nome, _die, _cat, _range = "Lança",         "1d6",  "perfurante", 2
            m["esqueleto_arma_id"] = "lanca_curta"
            m["ac"] += 2   # escudo: CA 12 → 14
            m["esqueleto_escudo"] = True
        elif _roll <= 95:
            _nome, _die, _cat, _range = "Machado",       "1d10", "cortante",   None
            m["esqueleto_arma_id"] = "machado_basico"
        else:
            _nome, _die, _cat, _range = "Espada 2 Mãos", "1d10", "cortante",   None
            m["esqueleto_arma_id"] = "espada2m"
        atk = {"name": _nome, "atk_bonus": 2, "damage": _die,
               "damage_types": ["physical"], "num_attacks": 1, "on_hit": None,
               "categoria": _cat}
        if _range:
            atk["range"] = _range
        m["attacks"] = [atk]
    return m

def spawn_monsters_for_room(room, player_count):
    tier = 1 if room["role"] == "monster" else 4
    is_boss = (tier == 4)
    # Salas normais: apenas monstros com ficha completa (ai_type definido).
    # Monstros legado sem ai_type não têm attacks list e não funcionam no novo sistema.
    # Sala do boss: usa o pool antigo sem filtro (dragão ainda é legado).
    pool = [m for m in MONSTER_DEFS
            if m.get("boss", False) == is_boss
            and m.get("spawn_max", 1) > 0
            and (is_boss or "ai_type" in m)]
    if not pool:
        return []
    if tier == 4:
        boss_def = next(m for m in MONSTER_DEFS if m.get("boss"))
        return [make_monster(boss_def, room)]
    mdef = random.choice(pool)
    min_c = mdef.get("spawn_min", 1)
    max_c = mdef.get("spawn_max", min(3, player_count))
    # Teto nunca abaixo do piso: com poucos jogadores (ex.: solo) um monstro com
    # spawn_min=2 produzia randint(2, 1) → ValueError e a masmorra não abria.
    count = random.randint(min_c, max(min_c, min(max_c, player_count)))
    monsters = [make_monster(mdef, room) for _ in range(count)]
    # Companion spawn: aceita um único `spawn_companion` (ex.: kobold) ou uma
    # lista `spawn_companions` (ex.: bando do Goblin Dual: combatentes + arqueiros).
    companions = list(mdef.get("spawn_companions", []))
    if mdef.get("spawn_companion"):
        companions.append(mdef["spawn_companion"])
    for companion in companions:
        comp_def = next((d for d in MONSTER_DEFS if d["type"] == companion["type"]), None)
        if comp_def:
            n = random.randint(companion["min"], companion["max"])
            monsters.extend(make_monster(comp_def, room) for _ in range(n))
    return monsters

def make_trap(room, tiles):
    # Sorteia uma casa de CHÃO dentro da sala (evita as bordas que viraram
    # parede ao posicionar as portas — uma armadilha na parede nunca dispara).
    floors = [[x, y]
              for y in range(room["y"], room["y"] + room["h"])
              for x in range(room["x"], room["x"] + room["w"])
              if tiles[y][x] == FLOOR]
    pos = random.choice(floors) if floors else [room["cx"], room["cy"]]
    return {"id": new_id(), "pos": pos,
            "damage": random.randint(4, 8), "triggered": False, "room_id": room["id"]}

def preco_pergaminho(circulo_nome, nivel, int_bonus):
    """Preço = base do círculo × multiplicador de nível + acréscimo de INT.
    multiplicador = (nível de conjurador − nível mínimo do círculo) + 1."""
    base   = PERGAMINHO_PRECO_BASE.get(circulo_nome, 20)
    min_lv = PERGAMINHO_NIVEL_CIRCULO.get(circulo_nome, 1)
    mult   = max(1, (nivel - min_lv) + 1)
    return base * mult + PERGAMINHO_INT_SURCHARGE.get(int_bonus, 0)

def preview_pergaminho(magia, nivel, int_bonus):
    """Calcula a prévia exibível de um pergaminho (dano/alcance/CD no nível +
    bônus de INT marcados). Usa os campos estruturados do GRIMORIO."""
    circ_num = {"primeiro": 1, "segundo": 2, "terceiro": 3}.get(magia.get("circulo", "primeiro"), 1)
    # Alcance (fixo, ou base + escala×(nível-1)); None = pessoal/área no caster.
    if "alcance" in magia:
        alcance = magia["alcance"]
    elif "alcance_base" in magia:
        alcance = magia["alcance_base"] + magia.get("alcance_escala", 0) * (nivel - 1)
    else:
        alcance = None
    # Dano: "dano_por_nivel" (XdY × nível) ou "dano_base" (+ "dano_escala" a cada 2 níveis).
    dano = None
    def _mult_dado(dado, fator):
        try:
            n, face = str(dado).lower().split("d"); return f"{int(n) * fator}d{face}"
        except Exception:
            return f"{fator}×{dado}"
    if magia.get("dano_por_nivel"):
        dano = _mult_dado(magia["dano_por_nivel"], nivel)
    elif magia.get("dano_base"):
        base = magia["dano_base"]; esc = magia.get("dano_escala")
        try:
            bn, bf = str(base).lower().split("d")
            total = int(bn) + (int(str(esc).lower().split("d")[0]) * (nivel // 2) if esc else 0)
            dano = f"{total}d{bf}"
        except Exception:
            dano = base
    return {
        "nivel": nivel,
        "int_bonus": int_bonus,
        "dano": dano,
        "alcance": alcance,
        "area_raio": magia.get("area_raio"),
        "cd": (8 + int_bonus + circ_num) if magia.get("save") else None,
        "save": magia.get("save"),
        "duracao": magia.get("duracao"),
        "efeito": magia.get("descricao") if not dano else None,
    }

def _num_dados_dano(dano_str):
    """Quantidade de dados de uma string 'XdY' (0 se não houver)."""
    try:
        return int(str(dano_str).lower().split("d")[0])
    except Exception:
        return 0

def gerar_pergaminho(circulo_num=1, classe=None, nivel=None, int_bonus=0,
                     magia_id=None, talentos=None):
    """Cria um item de pergaminho com uma magia implementada do círculo dado.
    `nivel` = nível de conjurador (default = mínimo do círculo; escala dano/alcance
    e entra no cálculo de falha). `int_bonus` = modificador de INT (+0..+5; afeta a
    CD e o dano). `talentos` = dict {cd,duracao,dano} de metamagias do Pedro JÁ
    GRAVADAS no pergaminho (aplicadas só onde fazem sentido). Inclui o preço."""
    nome_circ = PERGAMINHO_CIRCULO_NOME.get(circulo_num, "primeiro")
    if magia_id and magia_id in GRIMORIO_IMPLEMENTADAS:
        sid = magia_id
        nome_circ = GRIMORIO[sid]["circulo"]
    else:
        elig = [s for s in GRIMORIO_IMPLEMENTADAS
                if GRIMORIO[s]["circulo"] == nome_circ
                and (classe is None or classe in GRIMORIO[s].get("classe", []))]
        if not elig:
            return None
        sid = random.choice(elig)
    mg     = GRIMORIO[sid]
    min_lv = PERGAMINHO_NIVEL_CIRCULO[nome_circ]
    nivel  = min_lv if nivel is None else max(min_lv, min(PERGAMINHO_NIVEL_MAX, nivel))
    int_bonus = max(0, min(PERGAMINHO_INT_MAX, int_bonus))
    pv = preview_pergaminho(mg, nivel, int_bonus)

    # Talentos do Pedro gravados — só valem onde aplicáveis (save / duração / dano).
    req = talentos or {}
    t_cd   = bool(req.get("cd"))      and bool(mg.get("save"))
    t_dur  = bool(req.get("duracao")) and bool(mg.get("duracao"))
    t_dano = bool(req.get("dano"))    and bool(mg.get("dano_por_nivel") or mg.get("dano_base"))

    preco = preco_pergaminho(nome_circ, nivel, int_bonus)
    if t_cd:   preco += 50
    if t_dur:  preco += 50
    if t_dano: preco += 20 * _num_dados_dano(pv.get("dano"))

    # Reflete os talentos na prévia (CD +1; dano ×1.5; duração estendida).
    if t_cd and pv.get("cd") is not None:
        pv["cd"] += 1
    pv["talento_cd"], pv["talento_duracao"], pv["talento_dano"] = t_cd, t_dur, t_dano

    suf = []
    if nivel > min_lv:    suf.append(f"Nv{nivel}")
    if int_bonus > 0:     suf.append(f"INT+{int_bonus}")
    if t_dano:            suf.append("Dano×1.5")
    if t_cd:              suf.append("CD+1")
    if t_dur:             suf.append("Dur+")
    nome = f"Pergaminho: {mg['nome']}" + (f" ({', '.join(suf)})" if suf else "")
    return {
        "id": f"pergaminho_{sid}", "name": nome,
        "emoji": "📜", "item_slot": "bag", "effect": "scroll",
        "magia_id": sid, "circulo": nome_circ,
        "nivel_conjurador": nivel, "int_bonus": int_bonus,
        "talento_cd": t_cd, "talento_duracao": t_dur, "talento_dano": t_dano,
        "price": preco,
        "preview": pv,
    }

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
        # True depois que a masmorra da expedição foi gerada. Enquanto for True,
        # toda volta da cidade RETOMA a mesma masmorra (mapa/monstros/baús/portas/
        # névoa/armadilhas intactos) em vez de regenerar. Volta a False quando a
        # masmorra é concluída (boss derrotado → end_game), liberando uma nova.
        self.dungeon_generated = False
        # Tamanho do tabuleiro (procedural = 30×30; masmorra autorada define o seu).
        self.map_w = MAP_W
        self.map_h = MAP_H
        # Seleção de masmorra no lobby (Fase 1 do editor).
        self.mode = "procedural"          # "procedural" | "authored"
        self.selected_dungeon = None      # nome do arquivo em dungeons/ (modo authored)
        self.dungeon_def = None           # dict cru da masmorra autorada carregada
        # Fase 3 — objetivos/prisioneiro/saída (só em masmorra autorada).
        self.exit_pos = None
        self.objectives = None
        self.objective_status = None
        self.prisoner = None
        self.rescue_failed = False
        self._objetivo_concluido = False
        # Fase 4a — campanha.
        self.campaign = None         # dict carregado (modo "campaign")
        self.campaign_phase = 0      # índice da fase atual em campaign["dungeons"]
        self.key_chest_opened = False
        self.monsters = {}      # id -> monster
        self.corpses = {}       # id -> cadáver (monstro morto, alvo de Animar Mortos)
        self.animados_phase_pid = None  # pid no "turno dos servos" (logo após o mago)
        self.traps = []
        self.armadilhas = []    # armadilhas colocáveis (ver ARMADILHAS) — distintas de self.traps
        self._armadilha_seq = 0 # contador p/ ids únicos de armadilha
        self.zonas_especiais = []  # zonas mágicas (escuridão/silêncio) — ver GRIMORIO/handle_magia
        self.turn_index = 0
        self.round_num = 1
        # Timer de turno (30s): tarefa asyncio + token p/ descartar timers velhos.
        self.TURN_LIMIT_S = 30
        self.turn_timer_task = None
        self.turn_token = 0
        self.turn_timer_started_ms = None   # epoch ms do início do turno atual (p/ contagem no cliente)
        self.gm_log = []        # narrative messages
        self.explored = set()   # (x,y) tuples visible to all
        self.door_rooms = {}    # (x,y) -> [room_id,...] — salas que cada porta destranca
        self.magic_reveal = {}  # (x,y) -> rodada de expiração (Clarividência revela interior)
        self.stairs_pos = None  # [x, y] — entrance staircase tile
        self.temp_def = {}      # pid -> bonus_def (lasts 1 turn)
        self.temp_def_turnos = {}  # pid -> turnos restantes (>1 = duração estendida; Aprimorar Magia do mago)
        self.smoke = {}         # mid -> True (monsters miss next attack)
        self.immune = {}        # pid -> turns_remaining
        self.blessed = {}       # pid -> atk_bonus
        self.taunted = None     # pid who has taunt active
        self.chests  = {}       # chest_id -> chest dict (persistent world loot)
        self.shop_scrolls = []  # pergaminhos à venda no mercador (renovados por visita à cidade)

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

    # Atraso por casa na animação fiel de deslize (monstros inimigos e servos
    # auto-comandados). ~0.12s/casa: próximo dos 0,25s/casa do herói, mas mais
    # ágil para não arrastar o turno dos monstros. Ajuste aqui para mudar o ritmo.
    STEP_ANIM_DELAY = 0.12

    async def _emit_entity_step(self, entity_id, frm, to, kind):
        """Anima o deslize de UMA casa no cliente (kind: 'monster'|'animado').
        O cliente interpola from→to ao longo de STEP_ANIM_DELAY; o push_state
        seguinte reconcilia a posição autoritativa final."""
        await self.broadcast({
            "type": "entity_step",
            "id": entity_id, "from": list(frm), "to": list(to), "kind": kind,
        })
        await asyncio.sleep(self.STEP_ANIM_DELAY)

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
        self.players[pid] = {"id": pid, "name": name, "class_id": None, "ready": False, "connected": True, "slot": len(self.players)}
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
            ),
            "dungeons": listar_dungeons(),
            "campaigns": listar_campanhas(),
            "mode": self.mode,
            "selected_dungeon": self.selected_dungeon,
        })

    async def handle_select_dungeon(self, pid, file):
        """Host escolhe a masmorra do lobby. file=None → procedural."""
        if pid != self.host_pid:
            return
        if self.phase != "lobby":
            return
        if not file:
            self.mode = "procedural"; self.selected_dungeon = None
            self.dungeon_def = None
            self.campaign = None; self.campaign_phase = 0
        else:
            defn = carregar_dungeon(file)
            ok, msg = (False, "Masmorra não encontrada.") if defn is None else validar_dungeon(defn)
            if not ok:
                await self.send_to(pid, {"type": "error", "msg": f"Masmorra inválida: {msg}"})
                return
            # Guarda o dict já carregado/validado para enter_dungeon usar
            # (autorada = mode=="authored" and self.dungeon_def is not None).
            self.mode = "authored"; self.selected_dungeon = file
            self.dungeon_def = defn
            self.campaign = None; self.campaign_phase = 0
        await self.broadcast_lobby()

    async def handle_select_campaign(self, pid, file):
        """Host escolhe uma campanha do lobby. file=None → procedural."""
        if pid != self.host_pid:
            return
        if self.phase != "lobby":
            return
        if not file:
            self.mode = "procedural"; self.selected_dungeon = None
            self.dungeon_def = None; self.campaign = None; self.campaign_phase = 0
        else:
            defn = carregar_campanha(file)
            ok, msg = (False, "Campanha não encontrada.") if defn is None else validar_campanha(defn)
            if not ok:
                await self.send_to(pid, {"type": "error", "msg": f"Campanha inválida: {msg}"})
                return
            self.mode = "campaign"; self.campaign = defn; self.campaign_phase = 0
            self.selected_dungeon = None; self.dungeon_def = None
        await self.broadcast_lobby()

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
        self._gerar_loja_pergaminhos()
        await self.broadcast({"type": "game_start"})
        await self.broadcast_city_state()

    # ── city phase ─────────────────────────────────────────────────────────

    async def broadcast_city_state(self):
        await self.broadcast({
            "type": "city_state",
            "players": list(self.players.values()),
            "host": self.host_pid,
            "campaign": self._campaign_payload(),
            "shops": {
                "ferreiro": {"weapons": SHOP_WEAPONS, "armors": SHOP_ARMORS},
                "mercador": SHOP_MERCHANT + self.shop_scrolls,   # mercador inclui pergaminhos
                "templo":   SHOP_TEMPLE,
                "taverna":  SHOP_TAVERN,
            },
        })

    def _gerar_loja_pergaminhos(self):
        """Renova o estoque de pergaminhos do mercador: uma MISTURA de básicos
        (nível mínimo, +0 INT) e reforçados (nível de conjurador e/ou INT maiores,
        com preço calculado). Ids únicos p/ a compra."""
        def _tal():
            # Pede os 3 talentos com ~40% cada; gerar_pergaminho filtra os aplicáveis.
            return {"cd": random.random() < 0.4, "duracao": random.random() < 0.4,
                    "dano": random.random() < 0.4}
        specs = [
            (1, None, 0, None),                                      # 1º básico
            (1, None, 0, None),                                      # 1º básico
            (1, random.randint(2, 5), random.randint(0, 2), _tal()), # 1º reforçado
            (2, None, 0, None),                                      # 2º básico
            (2, random.randint(3, 5), random.randint(0, 3), _tal()), # 2º reforçado
            (3, None, random.randint(0, 2), _tal()),                # 3º reforçado
        ]
        ofertas = []
        for i, (circ, nivel, intb, tal) in enumerate(specs):
            sc = gerar_pergaminho(circ, nivel=nivel, int_bonus=intb, talentos=tal)
            if not sc:
                continue
            sc["id"] = f"{sc['id']}_loja{i}"   # id único p/ a compra
            ofertas.append(sc)
        self.shop_scrolls = ofertas

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
            item = (next((i for i in SHOP_MERCHANT if i["id"] == item_id), None)
                    or next((i for i in self.shop_scrolls if i["id"] == item_id), None))
        elif shop == "templo":
            item = next((i for i in SHOP_TEMPLE   if i["id"] == item_id), None)
        elif shop == "taverna":
            item = next((i for i in SHOP_TAVERN   if i["id"] == item_id), None)

        if not item:
            await self.send_to(pid, {"type": "error", "msg": "Item não encontrado."})
            return

        # ── Restrição de classe (allowed_classes) — vale também na compra ──────
        allowed = item.get("allowed_classes")
        if allowed and p.get("class_id") not in allowed:
            await self.send_to(pid, {"type": "error",
                "msg": f"Sua classe não pode usar {item['name']}!"})
            return

        # ── Arma de 2 mãos × escudo: não podem coexistir (bloquear com aviso) ──
        if shop == "ferreiro_weapon":
            if WEAPONS.get(item_id, {}).get("two_handed") and self._off_hand_ocupa_mao(p):
                await self.send_to(pid, {"type": "error",
                    "msg": f"{item['name']} é arma de 2 mãos — desequipe o escudo ou a 2ª arma antes de empunhá-la."})
                return
        elif shop == "ferreiro_armor" and item.get("kind") == "shield":
            # O escudo só auto-equipa se a mão esquerda estiver livre; nesse caso
            # uma arma de 2 mãos equipada criaria o conflito → bloquear.
            if p["gear"].get("off_hand") is None and (p.get("weapon") or {}).get("two_handed"):
                await self.send_to(pid, {"type": "error",
                    "msg": f"Você empunha uma arma de 2 mãos — não pode equipar {item['name']}."})
                return

        price = item["price"]
        if p["gold"] < price:
            await self.send_to(pid, {"type": "error", "msg": "Ouro insuficiente!"})
            return

        p["gold"] -= price
        log = ""

        if shop == "ferreiro_weapon":
            # Adaga comprada com a mão principal já ocupada vai para a BOLSA — o
            # jogador escolhe equipar na mão principal ou como 2ª arma (botões).
            if self._eh_adaga(item) and p["gear"].get("weapon"):
                if len(p["bag"]) >= p.get("bag_size", 6):
                    p["gold"] += price
                    await self.send_to(pid, {"type": "error", "msg": "Inventário cheio — abra espaço para comprar."})
                    return
                p["bag"].append({**item, "buy_price": price})
                log = f"🔨 **{p['name']}** comprou **{item['name']}** (guardada na bolsa)."
            else:
                w = {**WEAPONS[item_id]}
                p["weapon"] = w
                # Dict de exibição/inventário auto-descritivo: inclui os campos de
                # combate (die/stat/range/reach/categoria/two_handed) para que
                # reequipar pela bolsa restaure as estatísticas e detecte 2 mãos.
                p["gear"]["weapon"] = {
                    "id": item_id, "name": item["name"],
                    "emoji": item.get("emoji", "⚔️"),
                    "item_slot": "weapon", "effect": "atk", "value": 0,
                    "buy_price": price,
                    **{k: w[k] for k in ("die", "stat", "range", "reach",
                                         "finesse", "throw_range", "categoria",
                                         "two_handed") if k in w},
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
            if slot == "ammo":
                # Munição: vai para o slot off_hand; acumula se mesmo tipo
                ammo_type  = item["ammo_type"]
                ammo_count = item.get("ammo_count", 10)
                off = p["gear"].get("off_hand")
                if off and off.get("effect") == "ammo" and off.get("ammo_type") == ammo_type \
                        and off.get("ammo_count", 0) < MAX_AMMO_STACK:
                    # Mesmo tipo já equipado e com espaço: adiciona ao contador
                    space = MAX_AMMO_STACK - off.get("ammo_count", 0)
                    add   = min(ammo_count, space)
                    off["ammo_count"] = off.get("ammo_count", 0) + add
                    log = f"🛒 **{p['name']}** recarregou **{item['name']}** (+{add} → {off['ammo_count']} total)."
                elif off is None:
                    # Off-hand livre: equipa diretamente
                    p["gear"]["off_hand"] = {**item, "buy_price": price}
                    log = f"🛒 **{p['name']}** equipou **{item['name']}** na mão esquerda ({ammo_count} projéteis)."
                else:
                    # Off-hand ocupado ou mesmo tipo lotado: empilha na bolsa (máx MAX_AMMO_STACK)
                    existing_bag = next(
                        (b for b in p["bag"]
                         if b.get("effect") == "ammo" and b.get("ammo_type") == ammo_type
                         and b.get("ammo_count", 0) < MAX_AMMO_STACK), None)
                    if existing_bag:
                        add = min(ammo_count, MAX_AMMO_STACK - existing_bag.get("ammo_count", 0))
                        existing_bag["ammo_count"] = existing_bag.get("ammo_count", 0) + add
                        log = f"🛒 **{p['name']}** guardou **{item['name']}** na bolsa ({existing_bag['ammo_count']} total)."
                    elif len(p["bag"]) >= p.get("bag_size", 6):
                        p["gold"] += price
                        await self.send_to(pid, {"type": "error", "msg": "Mão esquerda ocupada e inventário cheio!"})
                        return
                    else:
                        p["bag"].append({**item, "buy_price": price})
                        log = f"🛒 **{p['name']}** guardou **{item['name']}** na bolsa (equipe na mão esquerda para usar)."
            elif slot == "bag":
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
                self._curar_doenca(p)   # o Templo também cura doenças
                log = f"⛪ **{p['name']}** foi purificado de todos os males!"

        elif shop == "taverna":
            effect = item.get("effect")
            if effect == "meal_survival":
                # Refeição de balcão: consumida na hora, 1× por visita à cidade.
                if item_id in p.get("taverna_refeicoes", []):
                    p["gold"] += price  # estorna — compra recusada
                    await self.send_to(pid, {"type": "error",
                        "msg": f"Você já pediu {item['name']} nesta visita à cidade."})
                    return
                fome = item.get("fome", 0)
                sede = item.get("sede", 0)
                p["fome"] = min(100, p.get("fome", 0) + fome)
                p["sede"] = min(100, p.get("sede", 0) + sede)
                p.setdefault("taverna_refeicoes", []).append(item_id)
                log = f"🍺 **{p['name']}** se serve de **{item['name']}**: +{fome} fome e +{sede} sede!"
            else:
                # Provisões (item_slot bag): vão para a mochila para consumo posterior.
                if len(p["bag"]) >= p.get("bag_size", 6):
                    p["gold"] += price
                    await self.send_to(pid, {"type": "error",
                        "msg": f"Inventário cheio (máx {p.get('bag_size', 6)} itens)!"})
                    return
                p["bag"].append({**item, "buy_price": price})
                log = f"🍺 **{p['name']}** comprou **{item['name']}**!"

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

    def load_authored_dungeon(self, defn):
        """Carrega uma masmorra autorada (dict já validado) no estado da sala.
        Instancia só o que o motor entende; exit/prisoner/objectives ficam em
        self.dungeon_def (inertes até a Fase 3)."""
        self.dungeon_def = defn
        self.map_w = defn["grid"]["w"]
        self.map_h = defn["grid"]["h"]
        self.tiles = deepcopy(defn["tiles"])

        # Salas no mesmo formato de generate_dungeon.
        self.rooms = []
        for r in defn.get("rooms", []):
            x, y, w, h = r["x"], r["y"], r["w"], r["h"]
            role = r.get("role", "empty")
            self.rooms.append({
                "id": r["id"], "x": x, "y": y, "w": w, "h": h,
                "cx": x + w // 2, "cy": y + h // 2, "role": role,
                "cleared": role in ("entrance", "empty"),
                "looted": False,
                "locked": bool(r.get("locked", role != "entrance")),
                "doors": [list(d) for d in r.get("doors", [])],
            })

        # Mapa porta -> salas que ela destranca.
        self.door_rooms = {}
        for room in self.rooms:
            for dx, dy in room.get("doors", []):
                self.door_rooms.setdefault((dx, dy), []).append(room["id"])

        # Monstros em casa exata (sem distribuição/companheiros automáticos).
        self.monsters = {}
        for mo in defn.get("monsters", []):
            mdef = next(d for d in MONSTER_DEFS if d["type"] == mo["type"])
            room = self._room_by_id(mo.get("room_id")) or self.rooms[0]
            m = make_monster(mdef, room)
            m["pos"] = [mo["pos"][0], mo["pos"][1]]
            m["room_id"] = mo.get("room_id")
            m["boss"] = False                       # Fase 1: end_game-on-boss é da Fase 3
            m["authored_boss"] = bool(mo.get("boss"))
            m["authored_target"] = bool(mo.get("target"))
            self.monsters[m["id"]] = m

        # Baús com conteúdo exato (itens hidratados do catálogo do servidor).
        self.chests = {}
        for ch in defn.get("chests", []):
            self._spawn_chest(ch["pos"], int(ch.get("gold", 0)),
                              hidratar_itens_bau(ch.get("items", [])))

        # Armadilhas de masmorra autoradas (hostis, ocultas).
        self.traps = []
        self.armadilhas = [make_authored_trap(t) for t in defn.get("traps", [])]

        # Stairs = ponto de entrada.
        ent = defn["entrance"]
        self.stairs_pos = [ent["x"], ent["y"]]

        # Fase 3: instancia o que estava inerte.
        ex = defn.get("exit")
        self.exit_pos = [ex["x"], ex["y"]] if ex else None
        self.objectives = deepcopy(defn.get("objectives") or {"primary": {"type": "kill_all"}, "secondary": []})
        self.objective_status = None
        self.rescue_failed = False
        self._objetivo_concluido = False
        pr = defn.get("prisoner")
        self.prisoner = ({"pos": [pr["pos"][0], pr["pos"][1]], "room_id": pr.get("room_id"),
                          "hp": PRIS_HP, "max_hp": PRIS_HP, "freed": False, "alive": True}
                         if pr else None)
        # Marca o baú-chave por posição (o dict de baú vivo não carrega a flag).
        keyposes = {tuple(c["pos"]) for c in defn.get("chests", []) if c.get("key_objective")}
        for ch in self.chests.values():
            ch["key_objective"] = tuple(ch["pos"]) in keyposes

    def _spawn_tiles_near(self, start, n):
        """Devolve até `n` casas de CHÃO (FLOOR/DOOR) mais próximas de `start`
        por BFS, na ordem de proximidade. Usado p/ posicionar heróis."""
        sx, sy = start
        out = []; visto = {(sx, sy)}; fila = [(sx, sy)]
        while fila and len(out) < n:
            x, y = fila.pop(0)
            if self.tiles[y][x] != WALL:
                out.append([x, y])
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.map_w and 0 <= ny < self.map_h
                        and (nx, ny) not in visto and self.tiles[ny][nx] != WALL):
                    visto.add((nx, ny)); fila.append((nx, ny))
        return out

    async def enter_dungeon(self, pid):
        if pid != self.host_pid:
            await self.send_to(pid, {"type": "error", "msg": "Apenas o anfitrião pode entrar na masmorra."})
            return
        if self.phase != "city":
            return

        self.phase = "playing"
        self.animados_phase_pid = None   # ponteiro de turno transitório (zera em qualquer entrada)

        # A masmorra só é GERADA na 1ª entrada da expedição (ou após concluída).
        # Toda volta da cidade apenas a RETOMA — nada do mundo é regenerado nem
        # limpo, então mapa/monstros/baús/portas/névoa/armadilhas ficam exatamente
        # como o herói deixou. Ver self.dungeon_generated.
        nova = not self.dungeon_generated
        pids = list(self.players.keys())
        # Campanha: a 1ª entrada de cada fase carrega a masmorra da fase atual.
        if self.mode == "campaign" and self.campaign and nova:
            self.dungeon_def = carregar_dungeon(self.campaign["dungeons"][self.campaign_phase])
        autorada = self.mode in ("authored", "campaign") and self.dungeon_def is not None

        if nova:
            self.corpses = {}        # cadáveres não persistem entre masmorras distintas
            self.chests  = {}        # baús do andar anterior não persistem no novo mapa
            self.monsters = {}       # zera monstros da expedição anterior (senão reaparecem em paredes do novo mapa)
            self.traps = []          # idem armadilhas de masmorra
            self.armadilhas = []     # idem armadilhas colocáveis
            self.zonas_especiais = []
            self.explored = set()    # névoa volta ao início no mapa novo
            self.magic_reveal = {}
            self.exit_pos = None; self.objectives = None; self.objective_status = None
            self.prisoner = None; self.rescue_failed = False; self._objetivo_concluido = False
            self.key_chest_opened = False
            if autorada:
                self.load_authored_dungeon(self.dungeon_def)
            else:
                self.map_w, self.map_h = MAP_W, MAP_H
                self.tiles, self.rooms = generate_dungeon()

            if not autorada:
                # Mapa porta -> salas que ela destranca (uma porta pode servir 2 salas)
                self.door_rooms = {}
                for room in self.rooms:
                    for dx, dy in room.get("doors", []):
                        self.door_rooms.setdefault((dx, dy), []).append(room["id"])

        # Place players at entrance (reentram pela mesma escada que usaram p/ sair).
        entrance = next((r for r in self.rooms if r["role"] == "entrance"), self.rooms[0])
        if autorada:
            ent_pt = [self.dungeon_def["entrance"]["x"], self.dungeon_def["entrance"]["y"]]
            spawn_tiles = self._spawn_tiles_near(ent_pt, len(pids))
        else:
            spawn_tiles = None
        offsets = [(0,0),(1,0),(-1,0),(0,1),(1,1),(-1,1)]
        for i, pid2 in enumerate(pids):
            if spawn_tiles is not None:
                self.players[pid2]["pos"] = list(spawn_tiles[i % len(spawn_tiles)])
            else:
                ox, oy = offsets[i % len(offsets)]
                self.players[pid2]["pos"] = [entrance["cx"] + ox, entrance["cy"] + oy]
            self.players[pid2]["moves_left"]       = self.players[pid2]["spd"]
            self.players[pid2]["action_done"]      = False
            self.players[pid2]["bonus_action_used"] = False
            if nova:
                self._resetar_corrosao(self.players[pid2])   # corrosão reseta por dungeon
                self._resetar_vinho(self.players[pid2])      # embriaguez não persiste
                self._resetar_cerveja(self.players[pid2])    # embriaguez da cerveja não persiste

        if nova:
            if not autorada:
                # Spawn monsters & traps (só procedural; autorada já posicionou tudo)
                for room in self.rooms:
                    if room["role"] == "monster":
                        spawned = self._distribuir_monstros(spawn_monsters_for_room(room, len(pids)), room)
                        for m in spawned:
                            self.monsters[m["id"]] = m
                        if any("kobold" in m.get("type", "") for m in spawned):
                            self._gerar_armadilhas_kobold(room)
                    if room["role"] == "boss":
                        boss_def = next(m for m in MONSTER_DEFS if m.get("boss"))
                        for m in self._distribuir_monstros([make_monster(boss_def, room)], room):
                            self.monsters[m["id"]] = m
                    if room["role"] == "trap":
                        self.traps.append(make_trap(room, self.tiles))
            self.dungeon_generated = True   # marca: próximas voltas da cidade retomam esta masmorra

        # Stairs tile — centre of entrance room (same spawn point as players).
        # No modo autorado, load_authored_dungeon já fixou a escada no ponto de
        # entrada autorado (que pode não coincidir com o centro da sala).
        if not autorada:
            self.stairs_pos = [entrance["cx"], entrance["cy"]]

        # Reveal entrance (room + 1-tile border so surrounding walls are visible)
        self._reveal_room(entrance)

        await self.broadcast({"type": "enter_dungeon"})
        self._iniciar_timer_turno()   # 30s do 1º turno (ou do turno atual ao retomar)
        await self.push_state()
        if nova:
            await self.gm_say(gm("intro"))
            await self.gm_say(f"Os aventureiros partem da cidade e adentram a masmorra. Turno 1 — é a vez de **{self.players[self.current_pid()]['name']}**.")
        else:
            await self.gm_say(f"🚪 Os aventureiros descem novamente as escadas — a masmorra permanece exatamente como a deixaram. É a vez de **{self.players[self.current_pid()]['name']}**.")

    def current_pid(self):
        if not self.player_order:
            return None
        return self.player_order[self.turn_index % len(self.player_order)]

    def _ativo(self, p):
        """Jogador ativo no jogo: vivo E conectado. Desconectados saem da
        masmorra (peão fora do tabuleiro) e são pulados na ordem de turnos."""
        return bool(p) and bool(p.get("alive")) and p.get("connected", True)

    # ── TIMER DE TURNO (30s) ────────────────────────────────────────────────
    def _cancelar_timer_turno(self):
        t = self.turn_timer_task
        # Não cancela a própria tarefa em execução: quando o timeout dispara ele
        # chama handle_end_turn → _iniciar_timer_turno → aqui; cancelar a si mesmo
        # abortaria o push_state final. O token já impede o re-disparo do antigo.
        if t and not t.done() and t is not asyncio.current_task():
            t.cancel()
        self.turn_timer_task = None
        self.turn_timer_started_ms = None

    def _iniciar_timer_turno(self):
        """(Re)inicia os 30s do jogador da vez. Só na masmorra e para um jogador
        ativo. O token garante que um timer antigo não encerre um turno novo."""
        self._cancelar_timer_turno()
        if self.phase != "playing":
            return
        p = self.players.get(self.current_pid())
        if not self._ativo(p):
            return
        self.turn_token += 1
        self.turn_timer_started_ms = int(time.time() * 1000)
        self.turn_timer_task = asyncio.create_task(
            self._turn_timer_expira(self.current_pid(), self.turn_token))

    async def _turn_timer_expira(self, pid, token):
        try:
            await asyncio.sleep(self.TURN_LIMIT_S)
        except asyncio.CancelledError:
            return
        # Continua sendo o MESMO turno do MESMO jogador?
        if token != self.turn_token or self.phase != "playing" or self.current_pid() != pid:
            return
        p = self.players.get(pid)
        nome = p["name"] if p else "?"
        await self._forcar_fim_turno(
            pid, f"⏳ Tempo esgotado! O turno de **{nome}** foi encerrado automaticamente.")

    async def _forcar_fim_turno(self, pid, motivo=None):
        """Encerra à força o turno de `pid` (timeout de 30s ou desconexão no
        próprio turno). handle_end_turn pode só abrir a fase dos servos sem
        avançar; repete até o turno realmente passar (limite de segurança)."""
        if self.phase != "playing" or self.current_pid() != pid:
            return
        if motivo:
            await self.gm_say(motivo)
        for _ in range(4):
            if self.current_pid() != pid:
                break
            await self.handle_end_turn(pid)

    # ── DESCONEXÃO / SAÍDA NO MEIO DA PARTIDA ───────────────────────────────
    async def handle_disconnect_em_jogo(self, pid):
        """Jogador caiu/saiu durante a partida: o personagem deixa a masmorra
        (peão fora do tabuleiro), é pulado nos turnos e, se era a vez dele, o
        turno avança — os outros continuam normalmente. A ficha permanece em
        self.players para a reconexão (ver rejoin)."""
        p = self.players.get(pid)
        if not p or not p.get("connected", True):
            return
        p["connected"] = False
        # Anfitrião caiu → passa o comando a outro jogador conectado.
        if self.host_pid == pid:
            nxt = next((q["id"] for q in self.players.values()
                        if q["id"] != pid and q.get("connected")), None)
            if nxt:
                self.host_pid = nxt
        era_turno = (self.phase == "playing" and self.current_pid() == pid)
        if self.phase == "playing":
            p["pos"] = [-1, -1]   # fora do tabuleiro: monstros ignoram, não ocupa casa
            await self.gm_say(f"🔌 **{p['name']}** perdeu a conexão e deixou a masmorra. O grupo segue em frente!")
        else:
            await self.gm_say(f"🔌 **{p['name']}** desconectou-se.")
        if era_turno:
            await self._forcar_fim_turno(pid)   # avança o turno (já reinicia o timer)
        elif self.phase == "playing":
            self._iniciar_timer_turno()
            await self.push_state()
        if self.phase == "city":
            await self.broadcast_city_state()

    def _distribuir_monstros(self, spawned, room):
        """Espalha os monstros em casas de chão livres da sala, reservando o
        footprint inteiro dos multi-tile (regra: nenhuma entidade compartilha
        casa). Retorna só os que couberam — excedente sem casa livre é descartado."""
        cx, cy = room["cx"], room["cy"]
        # Candidatas: chão da sala, ordenadas pela proximidade do centro (agrupa).
        cands = sorted(
            ([x, y]
             for y in range(room["y"], room["y"] + room["h"])
             for x in range(room["x"], room["x"] + room["w"])
             if 0 <= x < self.map_w and 0 <= y < self.map_h and self.tiles[y][x] == FLOOR),
            key=lambda c: max(abs(c[0] - cx), abs(c[1] - cy)))
        ocupadas = set()
        colocados = []
        # Maiores primeiro: os 2x2 precisam de espaço contíguo.
        def _cabe(m, c, f):
            return all(tuple(t) not in ocupadas
                       and 0 <= t[0] < self.map_w and 0 <= t[1] < self.map_h
                       and self.tiles[t[1]][t[0]] == FLOOR
                       for t in self._monster_tiles_at(m, c[0], c[1], f))

        for m in sorted(spawned,
                        key=lambda mm: -(mm.get("size", [1, 1])[0] * mm.get("size", [1, 1])[1])):
            # Orientado: tenta cada facing até achar um que caiba (footprint de 2
            # casas em linha). Caso geral: facing None (bloco w×h da âncora).
            facings = [[-1, 0], [1, 0], [0, -1], [0, 1]] if m.get("oriented") else [None]
            anchor = chosen_facing = None
            for c in cands:
                for f in facings:
                    if _cabe(m, c, f):
                        anchor, chosen_facing = c, f
                        break
                if anchor is not None:
                    break
            if anchor is None:
                continue   # sem casa livre para o footprint: descarta
            m["pos"] = [anchor[0], anchor[1]]
            if chosen_facing is not None:
                m["facing"] = list(chosen_facing)
            for t in self._monster_tiles_at(m, anchor[0], anchor[1], chosen_facing):
                ocupadas.add(tuple(t))
            colocados.append(m)
        return colocados

    def _reveal_room(self, room):
        # Reveal room interior + 1-tile border so surrounding walls are visible
        for ry in range(max(0, room["y"] - 1), min(self.map_h, room["y"] + room["h"] + 1)):
            for rx in range(max(0, room["x"] - 1), min(self.map_w, room["x"] + room["w"] + 1)):
                self.explored.add((rx, ry))

    def _reveal_around(self, px, py, radius=1):
        for dy in range(-radius, radius+1):
            for dx in range(-radius, radius+1):
                x, y = px+dx, py+dy
                # Não revela o interior de uma sala trancada (porta fechada
                # esconde o conteúdo). A própria porta, no anel externo, é
                # revelada normalmente.
                if self._tile_in_locked_room(x, y):
                    continue
                self.explored.add((x, y))

    # ── PORTAS / SALAS TRANCADAS ───────────────────────────────────────────
    def _room_by_id(self, rid):
        if rid is None:
            return None
        return next((r for r in self.rooms if r["id"] == rid), None)

    def _door_owner_rooms(self, x, y):
        """Salas que a porta em (x,y) controla."""
        return [self._room_by_id(rid) for rid in self.door_rooms.get((x, y), [])
                if self._room_by_id(rid) is not None]

    def _is_closed_door(self, x, y):
        """True se (x,y) é uma porta fechada. Uma porta serve até 2 salas; só
        fica passável quando TODAS estão destrancadas (basta uma trancada para
        a porta seguir fechada)."""
        if not (0 <= x < self.map_w and 0 <= y < self.map_h):
            return False
        if self.tiles[y][x] != DOOR:
            return False
        return any(r.get("locked") for r in self._door_owner_rooms(x, y))

    def _blocks_tile(self, x, y):
        """Tile intransponível: parede ou porta fechada (fora do mapa também)."""
        if not (0 <= x < self.map_w and 0 <= y < self.map_h):
            return True
        return self.tiles[y][x] == WALL or self._is_closed_door(x, y)

    def _tile_in_locked_room(self, x, y):
        for r in self.rooms:
            if r.get("locked") and room_contains(r, x, y):
                return True
        return False

    def _get_raio_visao(self, p):
        """Raio (Chebyshev) de revelação da névoa para um jogador. Base 3;
        somado ao bônus de Visão do Guerreiro da Luz (Richard) quando ativo."""
        raio_base = 3
        if p.get("class_id") == "paladin" and p.get("guerreiro_luz_ativo"):
            return raio_base + p.get("guerreiro_luz_bonus", {}).get("visao", 0)
        return raio_base

    # ── turn actions ───────────────────────────────────────────────────────

    async def handle_move(self, pid, dx, dy):
        if not self._is_turn(pid): return
        p = self.players[pid]
        if not p["alive"]: return
        if p.get("preso"):
            captor = self.monsters.get(p.get("preso_por"))
            if captor and captor["hp"] > 0:
                await self.send_to(pid, {"type": "error",
                    "msg": f"⛓️ Você está preso por **{captor['name']}**! Impossível se mover (tente escapar no próximo turno)."})
                return
            p["preso"] = False; p.pop("preso_por", None)
        if p.get("perde_turno"):
            await self.send_to(pid, {"type": "error", "msg": "🕸️ Você está imobilizado e não pode se mover! Encerre o turno."})
            return
        if p.get("petrificado"):
            await self.send_to(pid, {"type": "error", "msg": "🗿 Você está petrificado e não pode se mover!"})
            return
        if p.get("paralisado"):
            await self.send_to(pid, {"type": "error", "msg": "❄️ Você está paralisado e não pode se mover!"})
            return
        if p.get("dormindo"):
            await self.send_to(pid, {"type": "error", "msg": "🌙 Você está dormindo e não pode se mover!"})
            return
        if p["moves_left"] <= 0:
            await self.send_to(pid, {"type": "error", "msg": "Sem movimentos restantes."})
            return

        nx, ny = p["pos"][0] + dx, p["pos"][1] + dy
        if not (0 <= nx < self.map_w and 0 <= ny < self.map_h):
            return
        if self.tiles[ny][nx] == WALL:
            await self.send_to(pid, {"type": "error", "msg": "Caminho bloqueado."})
            return
        if self._is_closed_door(nx, ny):
            await self.send_to(pid, {"type": "error",
                "msg": "🚪 A porta está fechada. Clique nela para abri-la."})
            return

        # Block movement into a tile occupied by a living monster (footprint multi-tile incluso)
        for m in self.monsters.values():
            if m["hp"] > 0 and [nx, ny] in self._monster_tiles(m):
                await self.send_to(pid, {"type": "error", "msg": "Um inimigo bloqueia o caminho!"})
                return

        # Block movement into a tile occupied by another player
        for other_pid, other_p in self.players.items():
            if other_pid != pid and other_p["alive"] and other_p["pos"] == [nx, ny]:
                await self.send_to(pid, {"type": "error", "msg": "Outro aventureiro está neste espaço."})
                return

        # Block movement into a tile occupied by an animated servant
        if self._animado_em([nx, ny]):
            await self.send_to(pid, {"type": "error", "msg": "Um servo animado ocupa este espaço."})
            return

        p["pos"] = [nx, ny]
        p["moves_left"] -= 1
        # Caminhar custa -1 sede UMA vez por turno (na 1ª casa andada), não por casa.
        if not p.get("moved_this_turn"):
            p["moved_this_turn"] = True
            extra = self._doenca_custo_extra(p)   # sintoma médio: +1 fome/sede ao mover
            p["sede"] = max(0, p["sede"] - 1 - extra)
            if extra:
                p["fome"] = max(0, p["fome"] - extra)
        self._reveal_around(nx, ny, radius=self._get_raio_visao(p))   # raio base + bônus de Visão (Guerreiro da Luz)

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
                    cancao_res = self._cancao_bonus(p, "bonus_res")
                    passed = save_roll + p["ref_"] + self._modificador_sobrevivencia(p) + cancao_res >= 13
                    await self.broadcast({"type": "dice_roll", "die": "d20",
                                           "value": save_roll, "label": "Reflexos"})
                    if passed:
                        await self.gm_say(prefix + f" **{p['name']}** passou no teste de **Reflexos** (CD 13) e se esquivou!")
                    else:
                        p["hp"] = max(0, p["hp"] - trap["damage"])
                        await self.gm_say(prefix + f" **{p['name']}** falhou em **Reflexos** (CD 13) e sofre **{trap['damage']}** de dano!")
                        if p["hp"] <= 0:
                            await self._player_dies(pid)

        # Armadilha colocável nesta casa? (dispara sobre quem pisou)
        if p["alive"]:
            arm = self._armadilha_no_tile(nx, ny)
            if arm:
                await self._disparar_armadilha(p, arm)

        # Pisar numa zona de Bola de Fogo ativa causa dano (entrar sofre dano).
        if p["alive"]:
            await self._verificar_entrada_zona_fogo(p, nx, ny)

        await self.push_state()

    async def handle_open_door(self, pid, tx, ty):
        """Herói abre uma porta adjacente — ação gratuita (não gasta movimento
        nem a ação). Destranca a(s) sala(s) ligada(s), revela o interior e
        desperta os monstros lá dentro (passam a perseguir os heróis)."""
        if not self._is_turn(pid):
            return
        p = self.players.get(pid)
        if not p or not p["alive"]:
            return
        if not (0 <= tx < self.map_w and 0 <= ty < self.map_h):
            return
        if self.tiles[ty][tx] != DOOR:
            return
        locked_owners = [r for r in self._door_owner_rooms(tx, ty) if r.get("locked")]
        if not locked_owners:
            return  # já está aberta
        # precisa estar adjacente à porta (inclui diagonais)
        if max(abs(p["pos"][0] - tx), abs(p["pos"][1] - ty)) > 1:
            await self.send_to(pid, {"type": "error",
                "msg": "Aproxime-se da porta para abri-la."})
            return

        self.explored.add((tx, ty))
        await self.gm_say(f"🚪 **{p['name']}** abre uma porta!")
        for r in locked_owners:
            r["locked"] = False
            self._reveal_room(r)
            key = "room_" + r["role"]
            if key in GM:
                await self.gm_say(gm(key))
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

    def _tem_linha_de_visao(self, pos_a, pos_b):
        """Linha de visão entre dois tiles: True se NENHUMA parede intercepta a
        linha reta entre os centros (Bresenham supercover — visita todos os
        tiles que a linha toca, sem deixar 'frestas' diagonais). Endpoints não
        bloqueiam. Paredes barram ataques à distância, arremessos e magias."""
        x0, y0 = int(pos_a[0]), int(pos_a[1])
        x1, y1 = int(pos_b[0]), int(pos_b[1])
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x1 > x0 else -1
        sy = 1 if y1 > y0 else -1
        # Percorre as fronteiras de célula (variante supercover): a cada passo
        # avança no eixo cujo cruzamento de borda vem primeiro; quando a linha
        # cruza exatamente um canto, avança nos DOIS eixos (corta o canto — um
        # par de paredes em diagonal ainda bloqueia pelos dois lados).
        x, y = x0, y0
        ix = iy = 0   # quantos passos já dados em cada eixo
        while (x, y) != (x1, y1):
            # Compara (ix+0.5)/dx com (iy+0.5)/dy sem divisão (produtos cruzados)
            t_x = (2 * ix + 1) * dy   # próximo cruzamento vertical
            t_y = (2 * iy + 1) * dx   # próximo cruzamento horizontal
            if t_x < t_y:
                x += sx; ix += 1
            elif t_x > t_y:
                y += sy; iy += 1
            else:
                # Canto exato — a linha tangencia as DUAS células ortogonais.
                # Se qualquer uma for parede, não existe fresta diagonal: bloqueia.
                cx1, cy1 = x + sx, y
                cx2, cy2 = x, y + sy
                if self._blocks_tile(cx1, cy1):
                    return False
                if self._blocks_tile(cx2, cy2):
                    return False
                x += sx; ix += 1
                y += sy; iy += 1
            if (x, y) == (x1, y1):
                break
            if not (0 <= x < self.map_w and 0 <= y < self.map_h):
                return False
            if self.tiles[y][x] == WALL or self._is_closed_door(x, y):
                return False
        return True

    def _free_tile_near(self, pos):
        """Floor tile adjacente (8-dir) a `pos`, livre de monstros/baús.
        Usado para depositar a adaga arremessada. Fallback: a própria tile."""
        cx, cy = pos
        occupied = {tuple(m["pos"]) for m in self.monsters.values()}
        occupied |= {tuple(c["pos"]) for c in self.chests.values()}
        cands = []
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.map_w and 0 <= ny < self.map_h and \
                   self.tiles[ny][nx] == FLOOR and (nx, ny) not in occupied:
                    cands.append([nx, ny])
        return random.choice(cands) if cands else list(pos)

    # ── Ladino (Luccas): Ataque Furtivo + Esconder nas Sombras ─────────────────

    def _dados_furtivo(self, nivel):
        """Nº de d4 do Ataque Furtivo por faixa de nível: 1–2 → 2, 3–4 → 3, 5+ → 4."""
        if nivel <= 2:   return 2
        elif nivel <= 4: return 3
        else:            return 4

    def _verificar_ataque_furtivo(self, luccas, alvo):
        """True se Luccas estiver invisível nas sombras, oculto pela Vela da
        Escuridão, OU houver um aliado vivo (jogador) adjacente — Chebyshev — ao alvo."""
        if luccas.get("invisivel_sombras") or luccas.get("oculto_vela"):
            return True
        ax, ay = alvo["pos"]
        for pid2, aliado in self.players.items():
            if pid2 == luccas["id"] or not aliado["alive"]:
                continue
            if max(abs(aliado["pos"][0] - ax), abs(aliado["pos"][1] - ay)) <= 1:
                return True
        return False

    async def _quebrar_invisibilidade(self, p, motivo="ao agir"):
        """Encerra o estado invisível das sombras (atacar/mover revela Luccas)."""
        if not p.get("invisivel_sombras"):
            return False
        p["invisivel_sombras"] = False
        await self.gm_say(f"🌑 **{p['name']}** revela-se ({motivo}).")
        return True

    async def handle_attack(self, pid, target_id, buffs=None):
        if not self._is_turn(pid): return
        p = self.players[pid]
        if not p["alive"] or self._acao_bloqueada(p): return

        # ── Status de veneno: petrificado não age; cego não usa ataque à distância ──
        if p.get("petrificado"):
            await self.send_to(pid, {"type": "error", "msg": "🗿 Você está petrificado e não pode agir!"})
            return
        if p.get("paralisado"):
            await self.send_to(pid, {"type": "error", "msg": "❄️ Você está paralisado e não pode agir!"})
            return
        if p.get("dormindo"):
            await self.send_to(pid, {"type": "error", "msg": "🌙 Você está dormindo e não pode agir!"})
            return
        if p.get("cego") and p.get("bloqueia_distancia") and (p.get("weapon") or {}).get("range") is not None:
            await self.send_to(pid, {"type": "error", "msg": "🙈 Cego — não pode usar ataques à distância!"})
            return

        if target_id in self.monsters:
            target = self.monsters[target_id]

            # ── Range check: ranged weapons use Chebyshev distance; melee cardinal-only ──
            weapon_here = p.get("weapon")
            w_range = weapon_here.get("range") if weapon_here else None

            # ── Checagem de munição para arcos e bestas ──
            _valid_ammo = RANGED_AMMO.get((weapon_here or {}).get("id")) if w_range is not None else None
            if _valid_ammo:
                _off = p.get("gear", {}).get("off_hand")
                _off_type = (_off or {}).get("ammo_type")
                if not _off or _off_type not in _valid_ammo or _off.get("ammo_count", 0) <= 0:
                    nome_proj = "flechas" if _valid_ammo[0] == "flechas" else "virotes"
                    await self.send_to(pid, {"type": "error",
                        "msg": f"🏹 Sem {nome_proj} (básicos ou incendiários)! Equipe na mão esquerda."})
                    return

            if w_range is not None:
                # Desaparecer nas Sombras: imune a ataques à distância enquanto oculto.
                if target.get("oculto_sombras"):
                    await self.send_to(pid, {"type": "error",
                        "msg": f"🌫️ {target['name']} desapareceu nas sombras — imune a ataques à distância!"})
                    return
                eff_range = self._alcance_escuridao(p, target, w_range)   # escuridão limita a 2q
                # Multi-tile: vale a casa do corpo mais próxima com linha de visão.
                body = self._monster_tiles(target)
                in_range = [t for t in body
                            if max(abs(p["pos"][0] - t[0]), abs(p["pos"][1] - t[1])) <= eff_range]
                if not in_range:
                    extra = " (escuridão limita o alcance a 2q — use Visão no Escuro)" if eff_range < w_range else ""
                    await self.send_to(pid, {
                        "type": "error",
                        "msg": f"⚠ {target['name']} está fora de alcance! (máximo {eff_range} quadrados){extra}"
                    })
                    return
                if not any(self._tem_linha_de_visao(p["pos"], t) for t in in_range):
                    await self.send_to(pid, {"type": "error",
                        "msg": f"🧱 Uma parede bloqueia a linha de tiro até {target['name']}!"})
                    return
            elif (weapon_here or {}).get("reach") == "lanca":
                # Lança: alcance estendido (2 retos ortogonais / 1 diagonal).
                if not self._lanca_no_alcance_jogador(p["pos"], target):
                    await self.send_to(pid, {
                        "type": "error",
                        "msg": f"⚠ {target['name']} está fora do alcance da lança! (2 casas em linha reta ou 1 na diagonal)"
                    })
                    return
            elif (weapon_here or {}).get("reach") == "cajado":
                # Cajado: alcance de todas as casas adjacentes (Chebyshev 1, inclui diagonais).
                if not self._cajado_no_alcance_jogador(p["pos"], target):
                    await self.send_to(pid, {
                        "type": "error",
                        "msg": f"⚠ {target['name']} está fora de alcance! Aproxime-se (1 quadrado, inclusive diagonal)."
                    })
                    return
            else:
                # Multi-tile: adjacente a QUALQUER casa do corpo (atacável nas 2 casas).
                if not self._is_adjacent_to_monster(p["pos"], target):
                    await self.send_to(pid, {
                        "type": "error",
                        "msg": f"⚠ {target['name']} está fora de alcance! Aproxime-se (1 quadrado ortogonal)."
                    })
                    return

            # ── Custo extra do bardo: atacar enquanto sustenta a Canção Heroica ──
            # Concentrar-se na música E lutar é exaustivo: o 1º ataque de cada
            # turno sob canção custa +2 fome / +1 sede. Cobrado só depois do range
            # check (ataque inválido não gasta) e bloqueia se faltar recurso —
            # o bardo deve desativar a canção para poder atacar sem fôlego.
            if p.get("class_id") == "bard" and p.get("cancao_ativa") and not p.get("cancao_atacou_apos"):
                custo_extra_fome, custo_extra_sede = 2, 1
                if p["fome"] < custo_extra_fome or p["sede"] < custo_extra_sede:
                    await self.send_to(pid, {"type": "error",
                        "msg": f"Sem fôlego para atacar sob a canção — precisa 🍖{custo_extra_fome} 💧{custo_extra_sede} (ou desative a canção)."})
                    return
                p["fome"] = max(0, p["fome"] - custo_extra_fome)
                p["sede"] = max(0, p["sede"] - custo_extra_sede)
                p["cancao_atacou_apos"] = True
                await self.gm_say(f"🎵⚔️ **{p['name']}** ataca sustentando a canção (🍖-{custo_extra_fome} 💧-{custo_extra_sede}).")

            # ── Habilidades ARMADAS do warrior (buffs) — cobra fome/sede AGORA ──
            # As skills são armadas no cliente (toggle, sem custo); o custo só é
            # pago ao agir (este ataque). Validamos o custo combinado das skills
            # selecionadas, debitamos e setamos as flags planas — só ALÉM do range
            # check, para que um ataque inválido não cobre recursos. As skills são
            # escolhidas ANTES da ação (este ataque); o ataque extra da Fúria é
            # resolvido inline logo abaixo, na MESMA ação.
            if buffs:
                sel = [s for s in p.get("skills", [])
                       if s["id"] in buffs and "mp" not in s]
                total_fome = sum(s.get("fome_cost", 0) for s in sel)
                total_sede = sum(s.get("sede_cost", 0) for s in sel)
                # SEM teto: o jogador pode sempre gastar — pode esgotar fome/sede
                # até 0 (risco de exaustão). Nada bloqueia o uso por falta de recurso.
                p["fome"] = max(0, p["fome"] - total_fome)
                p["sede"] = max(0, p["sede"] - total_sede)
                self._verificar_estado_sobrevivencia(p)
                nomes = []
                for s in sel:
                    sid = s["id"]
                    if sid == "mira_certeira":
                        p["skill_bonus_acerto"] = p.get("skill_bonus_acerto", 0) + 2
                    elif sid == "golpe_devastador":
                        p["skill_dobrar_dano"] = True
                    elif sid == "furia_berserker":
                        p["skill_ataque_extra"] = True
                    nomes.append(f"{s.get('icon','')}{s.get('name', sid)}")
                if sel:
                    await self.gm_say(
                        f"**{p['name']}** ativa {', '.join(nomes)} "
                        f"(🍖-{total_fome}{f' 💧-{total_sede}' if total_sede else ''}).")

            # ── Buffs de turno (flags planas) + modificador de sobrevivência ──
            # surv_mod: +1 (saciado, fome&sede>80) ou -1/-2 (exaustão, <20).
            surv_mod  = self._modificador_sobrevivencia(p)
            preso_pen = -2 if p.get("preso") else 0
            cancao_acerto = self._cancao_bonus(p, "bonus_acerto")
            cancao_dano   = self._cancao_bonus(p, "bonus_dano")
            # Guerreiro da Luz (Richard): +acerto/+dano enquanto o buff estiver ativo
            gl = p.get("guerreiro_luz_bonus", {}) if p.get("guerreiro_luz_ativo") else {}
            gl_atk  = gl.get("ataque", 0)
            gl_dano = gl.get("dano", 0)
            eff_atk = (p["atk_bonus"] + p.get("skill_bonus_acerto", 0) + surv_mod + preso_pen
                       + cancao_acerto + gl_atk + self._pen(p, "ataque")
                       + self._mod_magia(p, "ataque")                        # Abençoar
                       - self._corrosao_arma_pen(p)                          # arma de madeira corroída
                       - (4 if target.get("oculto_sombras") else 0))         # alvo oculto nas sombras (corpo a corpo)
            if preso_pen:
                await self.gm_say(f"⛓️ **{p['name']}** ataca enquanto preso — **-2** no acerto!")
            # Amaldiçoar reduz a CA do alvo (mod_magia ca negativo) → mais fácil de acertar.
            # Camuflagem Natural (cobra venenosa): +2 CA contra o PRIMEIRO ataque.
            # Fúria Cega (orc): -1 CA enquanto enfurecido.
            eff_target_ac = (target["ac"] + self._mod_magia(target, "ca")
                             + self._camuflagem_bonus(target)
                             + self._cacador_trevas_ca_bonus(target)        # Caçador das Trevas: +2 CA em área escura
                             - self._furia_cega_ca_pen(target)
                             - self._lento_previsivel_ca_pen(target))       # Ogro: -2 CA após errar
            # Vantagem (Invisibilidade ou Visão no Escuro na escuridão) vs Desvantagem
            # (atacar às cegas na escuridão). Vantagem+desvantagem se anulam.
            esc = self._verificar_escuridao(p, target)
            vantagem    = bool(p.get("invisivel_magico")) or bool(p.get("oculto_vela")) or esc == "vantagem"
            desvantagem = esc == "desvantagem"
            hit, roll, total, crit, _desc = self._rolar_ataque(eff_atk, eff_target_ac, vantagem, desvantagem)

            # ── Consumo de munição (projétil gasto ao atirar, hit ou miss) ──
            _ammo_extra_dmg   = None   # dano extra do projétil especial (incendiário)
            _ammo_extra_types = []
            if _valid_ammo:
                _off = p["gear"].get("off_hand")
                if _off and _off.get("ammo_type") in _valid_ammo:
                    _ammo_extra_dmg   = _off.get("extra_damage")
                    _ammo_extra_types = _off.get("extra_damage_types", [])
                    _off["ammo_count"] = _off.get("ammo_count", 1) - 1
                    if _off["ammo_count"] <= 0:
                        p["gear"]["off_hand"] = None
                        await self.gm_say(f"🏹 **{p['name']}** usou o último projétil!")

            # ── Consumo de veneno (ranged: por disparo; melee: só no acerto) ──
            _ranged_poison_vid = None   # veneno ativo neste disparo (ranged)
            if _valid_ammo and p.get("weapon_poison"):
                _ranged_poison_vid = p["weapon_poison"]
                p["weapon_poison_hits"] = p.get("weapon_poison_hits", 1) - 1
                if p["weapon_poison_hits"] <= 0:
                    p["weapon_poison"] = None

            if p.get("invisivel_magico"):
                p["invisivel_magico"] = False; p.pop("invisivel_magico_rodadas", None)
                await self.gm_say(f"🫥 **{p['name']}** ataca com vantagem e revela-se!")
            if esc == "desvantagem":
                await self.gm_say(f"🌑 **{p['name']}** ataca às cegas na escuridão — **desvantagem** (2d20, usa {roll}).")
            elif esc == "vantagem":
                await self.gm_say(f"🌑 **{p['name']}** enxerga na escuridão e ataca com **vantagem** (2d20, usa {roll}).")
            # Sono: o primeiro ataque contra um alvo dormindo é crítico e o acorda.
            if target.get("dormindo"):
                hit, crit = True, True
                target.pop("dormindo", None); target.pop("dormindo_rodadas", None)
                await self.gm_say(f"🌙 **{target['name']}** é atacado dormindo — golpe **CRÍTICO** e desperta!")
            # Label distingue claramente da Mão Secundária — evita confusão visual
            # com "rolagem de desvantagem" quando o jogador é dual-wielder (Henrique).
            await self.broadcast({"type": "dice_roll", "die": "d20", "value": roll,
                                   "label": "⚔️ Ataque (Mão Principal)", "hit": hit, "crit": crit})
            if hit:
                weapon = p.get("weapon")
                die_str = weapon.get("die") if weapon else None
                if die_str:
                    # Armed attack — roll weapon die
                    raw_dmg = roll_dice(die_str)
                    if p.get("skill_dobrar_dano"):
                        raw_dmg *= 2   # Golpe Devastador: dobra os dados de dano
                    # finesse (atributo 'forcaOuDestreza'): melhor de FOR/DES
                    if weapon.get("finesse"):
                        stat_bonus = max(mod(p.get("str_", 12)), mod(p.get("dex", 12)))
                    else:
                        stat_bonus = mod(p.get(weapon["stat"], 12))
                    dmg = raw_dmg + stat_bonus
                    if crit: dmg *= 2
                    dmg = max(1, dmg + surv_mod + cancao_dano + gl_dano
                              + self._mod_magia(p, "dano") - self._corrosao_arma_pen(p))
                    # Fraquezas/imunidades ao dano físico da arma
                    dmg = self._apply_damage_types(dmg, [DMG_PHYSICAL], target, weapon)
                    die_type = "d" + die_str.split("d")[1]
                    await self.broadcast({"type": "dice_roll", "die": die_type,
                                           "value": raw_dmg, "label": "Dano"})
                    weapon_name = weapon.get("name", "arma")
                    sb = f"+{stat_bonus}" if stat_bonus >= 0 else str(stat_bonus)
                    dmg_detail = f"[{die_str}={raw_dmg}{sb}]"
                else:
                    # Unarmed — fixed 1 + STR modifier
                    str_bonus = mod(p.get("str_", 12))
                    base = 2 if p.get("skill_dobrar_dano") else 1   # Golpe Devastador
                    dmg = base + str_bonus
                    if crit: dmg *= 2
                    dmg = max(1, dmg + surv_mod + cancao_dano + gl_dano + self._mod_magia(p, "dano"))
                    weapon_name = "soco"
                    sb = f"+{str_bonus}" if str_bonus >= 0 else str(str_bonus)
                    dmg_detail = f"[{base}{sb}]"
                # Golpe Sagrado (Richard): +1d8 sagrado, dobrado vs morto-vivo/demônio
                holy_detail = ""
                if p.get("golpe_sagrado_ativo"):
                    holy_roll = roll_dice("1d8")
                    await self.broadcast({"type": "dice_roll", "die": "d8", "value": holy_roll, "label": "Golpe Sagrado"})
                    holy = self._apply_damage_types(holy_roll, [DMG_HOLY], target, None)
                    if target.get("undead") or target.get("type") in ("undead", "demon", "skeleton", "esqueleto_humano"):
                        holy *= 2
                        holy_detail = f" +⚡{holy} sagrado (DOBRADO!)"
                    else:
                        holy_detail = f" +⚡{holy} sagrado"
                    dmg += holy
                # Ataque Furtivo (Luccas, passiva): +Nd4 quando há aliado adjacente
                # ao alvo ou Luccas está invisível. Vale 1x na mão principal.
                furtivo_detail = ""
                if p.get("class_id") == "rogue" and self._verificar_ataque_furtivo(p, target):
                    nd4 = self._dados_furtivo(p.get("level", 1))
                    dano_furtivo = sum(random.randint(1, 4) for _ in range(nd4))
                    await self.broadcast({"type": "dice_roll", "die": "d4",
                                           "value": dano_furtivo, "label": "Ataque Furtivo"})
                    dmg += dano_furtivo
                    furtivo_detail = f" +🗡️{dano_furtivo} furtivo [{nd4}d4]"
                target["hp"] -= dmg
                crit_str = " **CRÍTICO!**" if crit else ""
                await self.gm_say(
                    f"⚔️ **{p['name']}** ataca **{target['name']}** com {weapon_name}"
                    f" (d20={roll}+{eff_atk}={total} vs CA {target['ac']}):"
                    f"{crit_str} dano {dmg_detail}{holy_detail}{furtivo_detail} = **{dmg}**!")
                # ── Dano extra de projétil incendiário ──
                if _ammo_extra_dmg and target.get("hp", 1) > 0:
                    xdmg = roll_dice(_ammo_extra_dmg)
                    xdmg = self._apply_damage_types(xdmg, _ammo_extra_types, target)
                    target["hp"] = max(0, target["hp"] - xdmg)
                    await self.gm_say(f"🔥 Projétil incendiário: +{xdmg} de dano de fogo!")
                if target["hp"] <= 0:
                    await self._monster_dies(target, pid)
                else:
                    # Covardia Instintiva (kobolds): checa ao sofrer dano
                    if target.get("ai_type", "").startswith("kobold_"):
                        await self._verificar_covardia_kobold(target)
                    if _ranged_poison_vid:
                        # Ranged: carga já consumida antes do roll; aplica efeito no acerto.
                        await self._aplicar_veneno(target, _ranged_poison_vid, fonte="ataque")
                    elif p.get("weapon_poison"):
                        # Corpo a corpo: 1 carga, consumida só no golpe certeiro.
                        await self._aplicar_veneno(target, p["weapon_poison"], fonte="ataque")
                        p["weapon_poison_hits"] = p.get("weapon_poison_hits", 1) - 1
                        if p["weapon_poison_hits"] <= 0:
                            p["weapon_poison"] = None
                            await self.gm_say(f"🧴 O veneno da arma de **{p['name']}** acabou.")
            else:
                await self.gm_say(
                    f"⚔️ **{p['name']}** ataca **{target['name']}**"
                    f" (d20={roll}+{eff_atk}={total} vs CA {target['ac']}): **ERROU!**")

            # Fim de veneno ranged: anuncia ao esgotar cargas (mesmo em erros).
            if _ranged_poison_vid and p.get("weapon_poison") is None:
                await self.gm_say(f"🧴 O veneno do projétil de **{p['name']}** acabou.")

            # Atacar quebra a invisibilidade das sombras (o furtivo já foi aplicado).
            if p.get("class_id") == "rogue":
                await self._quebrar_invisibilidade(p, "ao atacar")
        else:
            await self.send_to(pid, {"type": "error", "msg": "Alvo inválido."})
            return

        # ── Custo de sobrevivência do ATAQUE BÁSICO: -1 fome por ação de ataque ─
        # (somado aos custos das habilidades armadas, já cobrados acima).
        p["fome"] = max(0, p["fome"] - 1)

        # ── Ataque de mão secundária (dual-wield) — CUSTA AÇÃO BÔNUS ────────────
        # Se a off_hand for uma arma (tem `die`), o alvo seguir vivo e ao alcance,
        # e o jogador ainda tiver a ação bônus do turno, desfere um ataque extra
        # (consome a ação bônus: -1 fome / -1 sede). A arma na 2ª mão (adaga) usa
        # o modificador de DESTREZA no acerto E no dano — independente do atributo
        # de ataque da classe. Para ladino/bardo isto coincide com o bônus normal;
        # para outras classes força DES. offhand_atk = mod(DES) + bônus de nível +
        # os mesmos modificadores situacionais do ataque principal (eff_atk menos o
        # bônus de ataque base da classe).
        off = p["gear"].get("off_hand")
        if off and off.get("die") and not p.get("bonus_action_used") \
           and target_id in self.monsters and self.monsters[target_id]["hp"] > 0:
            tgt = self.monsters[target_id]
            # Golpe corpo a corpo da 2ª arma: SÓ casas ortogonais adjacentes
            # (não usa throw_range como alcance — arremessar é ação separada).
            if self._cardinal_adjacent(p["pos"], tgt["pos"]):
                # consome a ação bônus do turno (consumo via tabela central)
                p["bonus_action_used"] = True
                self._consumir_recursos(p, 'acao_bonus')
                odex = mod(p.get("dex", 12))
                offhand_atk = odex + p.get("level_bonus", 1) + (eff_atk - p["atk_bonus"])
                ohit, oroll, ototal, ocrit = d20_attack(offhand_atk, tgt["ac"] + self._mod_magia(tgt, "ca"))
                await self.broadcast({"type": "dice_roll", "die": "d20", "value": oroll,
                                       "label": "🗡️ Ataque (Mão Secundária)", "hit": ohit, "crit": ocrit,
                                       "offhand": True})
                if ohit:
                    oraw = roll_dice(off["die"])
                    if p.get("skill_dobrar_dano"):
                        oraw *= 2
                    odmg = max(1, (oraw + odex) * (2 if ocrit else 1) + surv_mod)
                    odie_type = "d" + off["die"].split("d")[1]
                    await self.broadcast({"type": "dice_roll", "die": odie_type,
                                           "value": oraw, "label": "Dano (2ª mão)"})
                    tgt["hp"] -= odmg
                    ocrit_str = " **CRÍTICO!**" if ocrit else ""
                    osb = f"+{odex}" if odex >= 0 else str(odex)
                    await self.gm_say(
                        f"🗡️ **{p['name']}** desfere golpe de mão secundária com **{off['name']}** (ação bônus)"
                        f" (d20={oroll}+{offhand_atk}={ototal} vs CA {tgt['ac']}):"
                        f"{ocrit_str} dano [{off['die']}={oraw}{osb} DES] = **{odmg}**!")
                    if tgt["hp"] <= 0:
                        await self._monster_dies(tgt, pid)
                else:
                    await self.gm_say(
                        f"🗡️ **{p['name']}** erra o golpe de mão secundária"
                        f" (d20={oroll}+{offhand_atk}={ototal} vs CA {tgt['ac']}).")

        # ── Fúria Berserker (ataque_extra) — SEGUNDO ATAQUE MANUAL ─────────────
        # Em vez de encerrar a ação, deixamos action_done=False quando a Fúria está
        # ativa e o extra ainda não foi usado, liberando um 2º ataque manual neste
        # turno (o jogador clica atacar de novo; pode rearmar habilidades, pagando
        # mais fome/sede). skill_extra_usado garante que o extra valha 1 vez; o 2º
        # ataque cai no else e encerra a ação. No próximo turno tudo reabre.
        if p.get("skill_ataque_extra") and not p.get("skill_extra_usado"):
            p["skill_extra_usado"] = True
            await self.gm_say(f"🔥 **{p['name']}** — Fúria Berserker: ataque extra disponível! Ataque novamente.")
        else:
            p["action_done"] = True
        await self.push_state()

    async def handle_throw(self, pid, target_id, slot=None):
        """Arremesso de adaga/lança curta. AÇÃO PRINCIPAL se ainda não agiu; se já
        usou a ação principal neste turno, vira AÇÃO BÔNUS. `slot` ("weapon" ou
        "off_hand") escolhe qual arma arremessar; ausente = varre principal→2ª mão.
        Só consome a ação/recurso se o arremesso de fato ocorrer."""
        if not self._is_turn(pid): return
        p = self.players[pid]
        if not p["alive"]: return

        ja_agiu = p.get("action_done", False)

        if ja_agiu:
            # ── Arremesso como AÇÃO BÔNUS ──
            if p.get("bonus_action_used", False):
                await self.send_to(pid, {"type": "error",
                    "msg": "Ação bônus já usada neste turno."}); return
            if not await self._executar_arremesso(pid, target_id, slot):
                return                                   # validação falhou (erro já enviado)
            p["bonus_action_used"] = True
            self._consumir_recursos(p, 'acao_bonus')
        else:
            # ── Arremesso como AÇÃO PRINCIPAL ──
            if not await self._executar_arremesso(pid, target_id, slot):
                return
            p["action_done"] = True
            self._consumir_recursos(p, 'apenas_acao')

        await self.push_state()

    async def _executar_arremesso(self, pid, target_id, slot=None):
        """Executa o arremesso (acerto/dano/destruição/queda). Retorna True se
        executou; False se a validação falhou (erro já enviado). NÃO marca ação
        nem faz push_state (isso é do handle_throw). `slot` força a mão escolhida
        ("weapon"/"off_hand"); ausente = varre mão principal → 2ª mão."""
        p = self.players[pid]

        # Acha a arma arremessável no slot pedido (ou varre principal→secundária).
        # Mão principal: stats de combate vêm de p["weapon"]; secundária: do item.
        gear = p["gear"]
        slot_key = dagger = None
        throw_range = throw_die = None
        keys = (slot,) if slot in ("weapon", "off_hand") else ("weapon", "off_hand")
        for key in keys:
            it = gear.get(key)
            if not it:
                continue
            combat = p.get("weapon") if key == "weapon" else it
            tr  = it.get("throw_range") or (combat or {}).get("throw_range")
            die = it.get("die")        or (combat or {}).get("die")
            if tr and die:
                slot_key, dagger, throw_range, throw_die = key, it, tr, die
                break
        if not dagger:
            await self.send_to(pid, {"type": "error",
                "msg": "Você não tem uma adaga equipada para arremessar."}); return False

        if target_id not in self.monsters:
            await self.send_to(pid, {"type": "error", "msg": "Alvo inválido."}); return False
        target = self.monsters[target_id]

        rng = throw_range
        dx = abs(p["pos"][0] - target["pos"][0]); dy = abs(p["pos"][1] - target["pos"][1])
        if max(dx, dy) > rng:
            await self.send_to(pid, {"type": "error",
                "msg": f"⚠ {target['name']} fora de alcance de arremesso (máx {rng} quadrados)."}); return False
        if not self._tem_linha_de_visao(p["pos"], target["pos"]):
            await self.send_to(pid, {"type": "error",
                "msg": f"🧱 Uma parede bloqueia o arremesso até {target['name']}!"}); return False

        # Rolagem por DESTREZA (1 natural = falha crítica; 20 = crítico)
        dex_mod = mod(p.get("dex", 12))
        roll = random.randint(1, 20)
        total = roll + p["atk_bonus"]
        nat1 = (roll == 1)
        crit = (roll == 20)
        hit = (not nat1) and (crit or total >= target["ac"])

        await self.broadcast({"type": "dice_roll", "die": "d20", "value": roll,
                               "label": "Arremesso", "hit": hit, "crit": crit})

        # A adaga deixa o equipamento (arremessada)
        gear[slot_key] = None
        self._apply_gear_effect(p, dagger, False)   # remove efeito (none → no-op)
        if slot_key == "weapon":
            p["weapon"] = deepcopy(WEAPONS["unarmed"])   # mão principal fica vazia

        if hit:
            die_str = throw_die
            raw = roll_dice(die_str)
            dmg = max(1, (raw + dex_mod) * (2 if crit else 1))
            die_type = "d" + die_str.split("d")[1]
            await self.broadcast({"type": "dice_roll", "die": die_type,
                                   "value": raw, "label": "Dano (arremesso)"})
            target["hp"] -= dmg
            sb = f"+{dex_mod}" if dex_mod >= 0 else str(dex_mod)
            crit_str = " **CRÍTICO!**" if crit else ""
            await self.gm_say(
                f"🎯 **{p['name']}** arremessa **{dagger['name']}** em **{target['name']}**"
                f" (d20={roll}+{p['atk_bonus']}={total} vs CA {target['ac']}):"
                f"{crit_str} dano [{die_str}={raw}{sb} DES] = **{dmg}**!")
            if target["hp"] <= 0:
                await self._monster_dies(target, pid)
        elif nat1:
            await self.gm_say(
                f"💥 **{p['name']}** arremessa **{dagger['name']}** mas rola **1 natural** —"
                f" a adaga se perde para sempre!")
        else:
            await self.gm_say(
                f"🎯 **{p['name']}** arremessa **{dagger['name']}** em **{target['name']}**"
                f" (d20={roll}+{p['atk_bonus']}={total} vs CA {target['ac']}): **ERROU!**")

        # Recuperação: 1 natural = perdida; qualquer outro valor = cai no chão.
        # O item caído é uma adaga funcional (carrega die/throw_range p/ reuso).
        if not nat1:
            drop_item = deepcopy(dagger)
            drop_item.setdefault("emoji", "🗡️")
            drop_item.setdefault("die", throw_die)
            drop_item.setdefault("throw_range", throw_range)
            drop_item.setdefault("item_slot", "weapon")
            self._spawn_chest(self._free_tile_near(target["pos"]), 0, [drop_item])
            await self.gm_say(
                f"🗡️ A **{dagger['name']}** caiu no chão perto do alvo — aproxime-se para recuperá-la.")

        return True

    # ── cálculo de ataque com adaga por Destreza (scaffolding) ──────────────────
    # NOTA: inserido verbatim conforme especificação. AINDA NÃO é chamado — a
    # lógica autoritativa de ataque/arremesso já vive em handle_attack e
    # _executar_arremesso (que usam p["dex"], mod(), target["ac"] e
    # _free_tile_near). Este método assume um modelo diferente:
    #   • player['stats_mod']['destreza']  → no servidor é p["dex"] (score bruto)
    #   • self._get_bonus_atributo(...)     → NÃO existe (use mod())
    #   • alvo['ca']                        → no servidor é alvo["ac"]
    #   • self._posicao_adjacente_ao_alvo() → NÃO existe (use _free_tile_near())
    # Mantido para a futura reconciliação; chamá-lo hoje lançaria AttributeError.
    def _calcular_ataque_adaga(self, player, alvo, arremesso=False):
        destreza = player['stats_mod'].get('destreza', 10)
        bonus_dex = self._get_bonus_atributo(destreza)

        # Rolagem de ataque
        d20      = random.randint(1, 20)
        acerto   = d20 + bonus_dex
        ca_alvo  = alvo.get('ca', 10)

        resultado = {
            'd20':      d20,
            'bonus':    bonus_dex,
            'acerto':   acerto,
            'acertou':  acerto >= ca_alvo,
            'critico':  d20 == 20,
            'falha':    d20 == 1,
        }

        if resultado['acertou'] or resultado['critico']:
            dano_base = random.randint(1, 4)  # 1d4
            dano_total = dano_base + bonus_dex

            if resultado['critico']:
                dano_total = (dano_base * 2) + bonus_dex

            resultado['dano'] = max(1, dano_total)

        # Tratamento especial do arremesso
        if arremesso:
            if d20 == 1:
                resultado['arma_destruida'] = True
            else:
                resultado['arma_no_chao'] = True
                resultado['posicao_queda'] = self._posicao_adjacente_ao_alvo(alvo)

        return resultado

    # ── adaga secundária como AÇÃO BÔNUS (scaffolding) ──────────────────────────
    # NOTA: inserido verbatim conforme especificação. AINDA NÃO roteado e depende
    # de helpers/conceitos que NÃO existem no servidor:
    #   • gear['secundario']            → no servidor o slot é 'off_hand'
    #   • self._get_personagem(id)      → NÃO existe (use self.monsters[id])
    #   • self._e_adjacente(a, b)       → NÃO existe (Chebyshev inline == 1)
    #   • self._distancia(a, b)         → NÃO existe (Chebyshev inline)
    #   • self._aplicar_dano(alvo, n)   → NÃO existe
    #   • self._log(player, msg)        → NÃO existe (use gm_say/broadcast)
    #   • self._registrar_arma_no_chao  → NÃO existe (use _spawn_chest)
    #   • _calcular_ataque_adaga        → já é scaffolding (ver método acima)
    # Só `_consumir_recursos` existe. Chamar estes hoje lançaria AttributeError.
    # O fluxo real de mão secundária/arremesso já vive em handle_attack/handle_throw.
    def handle_ataque_adaga_secundaria(self, player, data):
        # Verifica ação bônus disponível
        if player.get('bonus_action_used'):
            return {'error': 'Ação bônus já usada neste turno'}

        # Verifica se tem adaga secundária equipada
        secundario = player['gear'].get('secundario', {})
        if not secundario or secundario.get('id') != 'adaga_secundaria':
            return {'error': 'Adaga secundária não equipada'}

        # Verifica alcance — deve ser adjacente
        alvo_id  = data.get('alvo_id')
        alvo     = self._get_personagem(alvo_id)
        if not self._e_adjacente(player, alvo):
            return {'error': 'Alvo fora do alcance da adaga secundária'}

        # Executa o ataque
        resultado = self._calcular_ataque_adaga(player, alvo)

        # Marca ação bônus como usada
        player['bonus_action_used'] = True

        # Consome fome e sede
        self._consumir_recursos(player, 'acao_bonus')

        # Aplica dano se acertou
        if resultado.get('acertou') or resultado.get('critico'):
            self._aplicar_dano(alvo, resultado['dano'])

        return {
            'sucesso':   True,
            'resultado': resultado,
            'tipo':      'ataque_adaga_secundaria',
        }

    def handle_arremesso_adaga_secundaria(self, player, data):
        # Verifica ação bônus disponível
        if player.get('bonus_action_used'):
            return {'error': 'Ação bônus já usada neste turno'}

        # Verifica se tem adaga secundária equipada
        secundario = player['gear'].get('secundario', {})
        if not secundario or secundario.get('id') != 'adaga_secundaria':
            return {'error': 'Adaga secundária não equipada'}

        # Verifica alcance do arremesso — 3 quadrados
        alvo_id = data.get('alvo_id')
        alvo    = self._get_personagem(alvo_id)
        dist    = self._distancia(player, alvo)
        if dist > 3:
            return {'error': f'Alvo a {dist} quadrados — máximo 3 para arremesso'}

        # Executa o arremesso
        resultado = self._calcular_ataque_adaga(player, alvo, arremesso=True)

        # Remove adaga do slot secundário
        player['gear']['secundario'] = None

        # Marca ação bônus como usada
        player['bonus_action_used'] = True

        # Consome fome e sede
        self._consumir_recursos(player, 'acao_bonus')

        if resultado.get('arma_destruida'):
            self._log(player, '💀 Adaga secundária destruída no arremesso!')
        else:
            self._registrar_arma_no_chao(
                'adaga_secundaria',
                resultado['posicao_queda']
            )

        if resultado.get('acertou') or resultado.get('critico'):
            self._aplicar_dano(alvo, resultado['dano'])

        return {
            'sucesso':   True,
            'resultado': resultado,
            'tipo':      'arremesso_adaga_secundaria',
        }

    # ── arremesso da LANÇA CURTA por Força (scaffolding) ────────────────────────
    # NOTA: inserido verbatim conforme especificação. AINDA NÃO roteado e depende
    # dos mesmos helpers inexistentes do cálculo da adaga (stats_mod,
    # _get_bonus_atributo, _get_personagem, _distancia, _e_linha_reta,
    # _tem_linha_de_visao, _aplicar_dano, _log, _registrar_arma_no_chao,
    # _posicao_adjacente_ao_alvo, gear['arma']). Além disso `lanca_curta` não
    # existe no servidor (só `lanca` range-2 SEM throw_range), e o fluxo real de
    # arremesso (_executar_arremesso) usa DESTREZA p/ todo arremesso — não a FORÇA
    # daqui. Só `_consumir_recursos` existe. Chamá-los hoje lançaria AttributeError.
    def _calcular_ataque_lanca_arremesso(self, player, alvo):
        forca     = player['stats_mod'].get('forca', 10)
        bonus_for = self._get_bonus_atributo(forca)
        d20    = random.randint(1, 20)
        acerto = d20 + bonus_for
        ca_alvo = alvo.get('ca', 10)
        resultado = {
            'd20':     d20,
            'bonus':   bonus_for,
            'acerto':  acerto,
            'acertou': acerto >= ca_alvo,
            'critico': d20 == 20,
            'falha':   d20 == 1,
        }
        if resultado['acertou'] or resultado['critico']:
            dano_base  = random.randint(1, 6)   # 1d6
            dano_total = dano_base + bonus_for
            if resultado['critico']:
                dano_total = (dano_base * 2) + bonus_for
            resultado['dano'] = max(1, dano_total)
        # Resultado 1 — lança destruída
        if d20 == 1:
            resultado['arma_destruida'] = True
        else:
            resultado['arma_no_chao']  = True
            resultado['posicao_queda'] = self._posicao_adjacente_ao_alvo(alvo)
        return resultado

    def handle_arremesso_lanca(self, player, data):
        arma = player['gear'].get('arma', {})
        # Verifica se tem lança curta equipada
        if not arma or arma.get('id') != 'lanca_curta':
            return {'error': 'Lança curta não equipada'}
        # Determina se é ação principal ou bônus
        ja_agiu     = player.get('action_done', False)
        bonus_usado = player.get('bonus_action_used', False)
        if ja_agiu and bonus_usado:
            return {'error': 'Sem ações disponíveis para arremessar'}
        # Verifica alcance — 3 quadrados linha reta
        alvo_id = data.get('alvo_id')
        alvo    = self._get_personagem(alvo_id)
        dist    = self._distancia(player, alvo)
        if dist > 3:
            return {'error': f'Alvo a {dist} quadrados — máximo 3 para arremesso'}
        # Verifica linha reta incluindo diagonais
        if not self._e_linha_reta(player, alvo):
            return {'error': 'Arremesso deve ser em linha reta'}
        # Verifica linha de visão
        if not self._tem_linha_de_visao(player, alvo):
            return {'error': 'Sem linha de visão para o alvo'}
        # Executa o arremesso
        resultado = self._calcular_ataque_lanca_arremesso(player, alvo)
        # Remove lança do slot de arma
        player['gear']['arma'] = None
        # Marca ação usada
        if ja_agiu:
            player['bonus_action_used'] = True
            self._consumir_recursos(player, 'acao_bonus')
        else:
            player['action_done'] = True
            self._consumir_recursos(player, 'apenas_acao')
        # Processa resultado
        if resultado.get('arma_destruida'):
            self._log(player, '💀 Lança curta destruída no arremesso!')
        else:
            self._registrar_arma_no_chao('lanca_curta', resultado['posicao_queda'])
        if resultado.get('acertou') or resultado.get('critico'):
            self._aplicar_dano(alvo, resultado['dano'])
            self._log(player, f"💥 Lança acertou! {resultado['dano']} de dano")
        else:
            self._log(player, '💨 Lança errou!')
        return {
            'sucesso':   True,
            'resultado': resultado,
            'tipo':      'arremesso_lanca',
        }

    # ── ANIMAR MORTOS — habilidade de classe do Pedro (roteada) ─────────────────
    # Fatia vertical: cadáveres rastreados em self.corpses (criados em
    # _monster_dies). Pedro (class_id 'mage') anima um cadáver adjacente; o d100
    # decide sucesso/falha/hostil. Os animados ficam REGISTRADOS em p['animados']
    # (persistem entre masmorras) mas ainda NÃO agem em combate. O resultado da
    # rolagem é enviado ao jogador (msg 'animar_result') para a animação D100 no
    # cliente; push_state atualiza o tabuleiro (cadáver some / vira hostil).
    #
    # Reconciliação da spec do PASSO 2 (estruturas reais do servidor):
    #   key→class_id ('mage') · nivel→level · stats_mod.inteligencia→int_ ·
    #   _get_bonus_atributo→mod() · fome/sede 0–10 (custo 2) · cadáver via
    #   self.corpses · hostil = restaura hp do monstro morto em self.monsters.
    async def handle_animar_mortos(self, pid, data):
        if not self._is_turn(pid):
            return
        p = self.players[pid]
        if not p["alive"]:
            return
        # Apenas Pedro (classe 'mage')
        if p.get("class_id") != "mage":
            await self.send_to(pid, {"type": "error", "msg": "Apenas Pedro pode usar Animar Mortos."})
            return
        if p.get("action_done"):
            await self.send_to(pid, {"type": "error", "msg": "Ação principal já usada neste turno."})
            return

        cadaver_id = data.get("cadaver_id")
        corpse = self.corpses.get(cadaver_id)
        if not corpse:
            await self.send_to(pid, {"type": "error", "msg": "Cadáver inválido ou já consumido."})
            return

        # Adjacência (Chebyshev ≤ 1 — inclui diagonais)
        dx = abs(p["pos"][0] - corpse["pos"][0])
        dy = abs(p["pos"][1] - corpse["pos"][1])
        if max(dx, dy) > 1:
            await self.send_to(pid, {"type": "error", "msg": "Pedro deve estar adjacente ao cadáver."})
            return

        nivel_pedro   = p.get("level", 1)
        nivel_monstro = corpse.get("nivel", corpse.get("tier", 1))

        # Slots disponíveis = mod(INT) + ⌊nível/2⌋ (mín. 1); ocupados = nível do monstro
        bonus_int     = mod(p.get("int_", 10))
        slots_max     = max(1, bonus_int + nivel_pedro // 2)
        animados      = p.setdefault("animados", [])
        slots_usados  = sum(a.get("slots", 1) for a in animados)
        slots_monstro = nivel_monstro
        if slots_usados + slots_monstro > slots_max:
            await self.send_to(pid, {
                "type": "error",
                "msg": f"Slots insuficientes — {slots_monstro} necessários, "
                       f"{slots_max - slots_usados} disponíveis."
            })
            return

        # Custo de sobrevivência (escala 0–10; spec 20/80 ≈ 2/10), independente do resultado
        custo = 2
        p["fome"] = max(0, p.get("fome", 10) - custo)
        p["sede"] = max(0, p.get("sede", 10) - custo)
        self._verificar_estado_sobrevivencia(p)

        # Chance de sucesso e zona hostil (mesma fórmula de HERO_DATA.pedro)
        nivel_max = 2 if nivel_pedro <= 2 else 4 if nivel_pedro <= 4 else 5
        diferenca = nivel_monstro - nivel_max
        chance = 90 + (abs(diferenca) * 5 if diferenca < 0 else -diferenca * 10)
        chance = min(99, max(1, chance))
        zona_hostil = max(0, diferenca * 10)

        # d100 = dois d10 (dezena + unidade); 00 = 100
        d10_dezena  = random.randint(0, 9)
        d10_unidade = random.randint(0, 9)
        rolagem = d10_dezena * 10 + d10_unidade
        if rolagem == 0:
            rolagem = 100

        if rolagem <= zona_hostil:
            resultado = "hostil"
        elif rolagem <= chance:
            resultado = "sucesso"
        else:
            resultado = "falha"

        if resultado == "sucesso":
            animados.append({
                "id":         cadaver_id,
                "owner":      pid,                       # dono (Pedro) — vira pó se ele morrer
                "nome":       f"{corpse['nome']} Animado",
                "icone":      corpse.get("icone", "💀"),
                "tipo":       corpse.get("tipo", "skeleton"),  # sprite original do monstro
                "nivel":      nivel_monstro,
                "slots":      slots_monstro,
                "ca":         corpse.get("ca", 10),
                "vida_max":   corpse.get("vida_max", 10),
                "vida_atual": corpse.get("vida_max", 10),
                "dano":       corpse.get("dano", "1d4"),
                "movimento":  corpse.get("movimento", 3),
                "moves_left": corpse.get("movimento", 3),  # controle do jogador (reseta/rodada)
                "acted":      False,                        # já atacou nesta rodada?
                "pos":        list(corpse["pos"]),       # nasce na casa do cadáver
                "hostil":     False,
            })
            self.corpses.pop(cadaver_id, None)
            self.monsters.pop(cadaver_id, None)   # remove o corpo morto subjacente
            await self.gm_say(
                f"💀 **{p['name']}** anima **{corpse['nome']}** — um novo servo ergue-se! (d100={rolagem})")
        elif resultado == "hostil":
            self.corpses.pop(cadaver_id, None)
            m = self.monsters.get(cadaver_id)
            if m is not None:
                m["hp"] = m.get("max_hp", corpse.get("vida_max", 10))   # ressuscita vivo
            await self.gm_say(
                f"💀 **FALHA CATASTRÓFICA!** O cadáver de **{corpse['nome']}** ergue-se HOSTIL! (d100={rolagem})")
        else:
            await self.gm_say(
                f"💨 **{p['name']}** falha em animar **{corpse['nome']}** — o cadáver permanece inerte. (d100={rolagem})")

        p["action_done"] = True

        # Resultado da rolagem → cliente (animação D100 + sync dos animados)
        await self.send_to(pid, {
            "type":        "animar_result",
            "resultado":   resultado,
            "rolagem":     rolagem,
            "d10_dezena":  d10_dezena,
            "d10_unidade": d10_unidade,
            "chance":      chance,
            "zona_hostil": zona_hostil,
            "fome":        p["fome"],
            "sede":        p["sede"],
            "animados":    animados,
        })
        await self.push_state()

    # ── Animados em combate (sistema completo) ──────────────────────────────────
    def _all_animados(self):
        """Todos os animados vivos de todos os jogadores (cada um tem 'owner')."""
        out = []
        for pp in self.players.values():
            for a in pp.get("animados", []):
                if a.get("vida_atual", 0) > 0:
                    out.append(a)
        return out

    def _animado_em(self, pos, exclude_id=None):
        for a in self._all_animados():
            if a.get("id") != exclude_id and a.get("pos") == list(pos):
                return True
        return False

    def _remover_animado(self, aid):
        """Remove um animado (vira pó) da lista de seu dono."""
        for pp in self.players.values():
            if pp.get("animados"):
                pp["animados"] = [a for a in pp["animados"] if a.get("id") != aid]

    def _tile_livre_para_animado(self, nx, ny, self_id):
        if not (0 <= nx < self.map_w and 0 <= ny < self.map_h): return False
        if self.tiles[ny][nx] == WALL: return False
        if any(m["hp"] > 0 and [nx, ny] in self._monster_tiles(m) for m in self.monsters.values()): return False
        if any(p["alive"] and p["pos"] == [nx, ny] for p in self.players.values()): return False
        if self._animado_em([nx, ny], exclude_id=self_id): return False
        return True

    async def handle_comandar_animados(self, pid):
        """No turno dos servos: cada animado move até `movimento` casas em direção
        ao monstro vivo mais próximo e ataca se ficar adjacente."""
        if not self._is_turn(pid): return
        if self.animados_phase_pid != pid:
            await self.send_to(pid, {"type": "error", "msg": "Encerre seu turno primeiro para abrir o turno dos servos."}); return
        p = self.players[pid]
        if not p["alive"]: return
        if p.get("class_id") not in ("mage", "cleric"):
            await self.send_to(pid, {"type": "error", "msg": "Apenas o mago ou clérigo comanda servos."}); return
        animados = p.get("animados", [])
        if not animados:
            await self.send_to(pid, {"type": "error", "msg": "Você não tem servos."}); return
        if not any(m["hp"] > 0 for m in self.monsters.values()):
            await self.send_to(pid, {"type": "error", "msg": "Nenhum inimigo para os animados atacarem."}); return

        # Atalho "comandar todos": auto-resolve os servos que ainda têm ação nesta
        # janela (respeita moves_left/acted; sem custo de ação bônus — o upkeep já
        # é cobrado por turno). Útil durante o turno dos servos.
        await self.gm_say(f"💀 **{p['name']}** comanda seus servos mortos-vivos!")

        for a in list(animados):
            if a.get("vida_atual", 0) <= 0 or a.get("acted") or a.get("dormindo"):
                continue
            if a.get("dominado_por_monstro"):   # roubado por necromante — não obedece
                continue
            living = [m for m in self.monsters.values() if m["hp"] > 0]
            if not living:
                break
            target = min(living, key=lambda m: abs(m["pos"][0]-a["pos"][0]) + abs(m["pos"][1]-a["pos"][1]))
            eh_eletrico = a.get("especial") == "linha_3q"
            atk_range   = 3 if eh_eletrico else 1

            # Elemental Elétrico: verifica se já tem alvo em linha dentro de 3q (sem mover)
            pode_atacar_agora = (
                self._em_linha_cardinal(a["pos"], target["pos"], atk_range)
                and not self._linha_bloqueada_por_parede(a["pos"], target["pos"])
            ) if eh_eletrico else self._cardinal_adjacent(a["pos"], target["pos"])

            # Move (cardinal greedy) até `moves_left` casas se ainda não pode atacar
            if not pode_atacar_agora:
                for _ in range(a.get("moves_left", a.get("movimento", 3))):
                    if self._cardinal_adjacent(a["pos"], target["pos"]):
                        break
                    if eh_eletrico and self._em_linha_cardinal(a["pos"], target["pos"], atk_range) \
                            and not self._linha_bloqueada_por_parede(a["pos"], target["pos"]):
                        break
                    dx = 0 if a["pos"][0] == target["pos"][0] else (1 if target["pos"][0] > a["pos"][0] else -1)
                    dy = 0 if a["pos"][1] == target["pos"][1] else (1 if target["pos"][1] > a["pos"][1] else -1)
                    moved = False
                    for adx, ady in [(dx, 0), (0, dy)]:
                        if adx == 0 and ady == 0:
                            continue
                        nx, ny = a["pos"][0]+adx, a["pos"][1]+ady
                        if self._tile_livre_para_animado(nx, ny, a["id"]):
                            frm = list(a["pos"])
                            a["pos"] = [nx, ny]; moved = True
                            await self._emit_entity_step(a["id"], frm, a["pos"], "animado")
                            break
                    if not moved:
                        break

            # Ataca se no alcance
            pode_atacar = (
                self._em_linha_cardinal(a["pos"], target["pos"], atk_range)
                and not self._linha_bloqueada_por_parede(a["pos"], target["pos"])
            ) if eh_eletrico else self._cardinal_adjacent(a["pos"], target["pos"])

            if pode_atacar:
                roll, _esc = self._rolar_d20_escuridao(a, target)
                total = roll + a.get("nivel", 1)
                if roll == 20 or total >= target["ac"]:
                    dmg = max(1, roll_dice(a.get("dano", "1d4")) * (2 if roll == 20 else 1))
                    target["hp"] -= dmg
                    await self.gm_say(
                        f"⚔️ **{a['nome']}** ataca **{target['name']}** "
                        f"(d20={roll}+{a.get('nivel',1)}={total} vs CA {target['ac']}): **{dmg}** de dano!")
                    if target["hp"] <= 0:
                        await self._monster_dies(target, pid)
                    await self._linha_eletrica(a, list(target["pos"]), pid)
                else:
                    await self.gm_say(
                        f"⚔️ **{a['nome']}** ataca **{target['name']}** e erra "
                        f"(d20={roll}+{a.get('nivel',1)}={total} vs CA {target['ac']}).")
            # O atalho "comandar todos" gasta o turno do animado.
            a["moves_left"] = 0
            a["acted"] = True

        await self.push_state()

    async def handle_mover_animado(self, pid, animado_id, dx, dy):
        """Controle manual: move UM animado uma casa (gasta 1 de movimento)."""
        if not self._is_turn(pid): return
        if self.animados_phase_pid != pid:
            await self.send_to(pid, {"type": "error", "msg": "Encerre seu turno primeiro para mover os servos."}); return
        p = self.players[pid]
        if not p["alive"]: return
        a = next((x for x in p.get("animados", []) if x.get("id") == animado_id), None)
        if not a or a.get("vida_atual", 0) <= 0:
            await self.send_to(pid, {"type": "error", "msg": "Animado inválido."}); return
        if a.get("dominado_por_monstro"):
            await self.send_to(pid, {"type": "error", "msg": "💀 Este servo está sob controle de um necromante!"}); return
        if a.get("dormindo"):
            await self.send_to(pid, {"type": "error", "msg": "🌙 Este servo está dormindo."}); return
        if a.get("moves_left", 0) <= 0:
            await self.send_to(pid, {"type": "error", "msg": "Servo sem movimento neste turno."}); return
        if abs(dx) > 1 or abs(dy) > 1 or (dx == 0 and dy == 0):
            return
        nx, ny = a["pos"][0] + dx, a["pos"][1] + dy
        if not self._tile_livre_para_animado(nx, ny, a["id"]):
            await self.send_to(pid, {"type": "error", "msg": "Caminho bloqueado para o servo."}); return
        a["pos"] = [nx, ny]
        a["moves_left"] -= 1
        await self.push_state()

    async def handle_atacar_animado(self, pid, animado_id, target_id):
        """Controle manual: UM animado ataca um monstro adjacente (1 ataque/rodada)."""
        if not self._is_turn(pid): return
        if self.animados_phase_pid != pid:
            await self.send_to(pid, {"type": "error", "msg": "Encerre seu turno primeiro para atacar com os servos."}); return
        p = self.players[pid]
        if not p["alive"]: return
        a = next((x for x in p.get("animados", []) if x.get("id") == animado_id), None)
        if not a or a.get("vida_atual", 0) <= 0:
            await self.send_to(pid, {"type": "error", "msg": "Animado inválido."}); return
        if a.get("dominado_por_monstro"):
            await self.send_to(pid, {"type": "error", "msg": "💀 Este servo está sob controle de um necromante!"}); return
        if a.get("dormindo"):
            await self.send_to(pid, {"type": "error", "msg": "🌙 Este servo está dormindo."}); return
        if a.get("acted"):
            await self.send_to(pid, {"type": "error", "msg": "Servo já atacou neste turno."}); return
        m = self.monsters.get(target_id)
        if not m or m["hp"] <= 0:
            await self.send_to(pid, {"type": "error", "msg": "Alvo inválido."}); return
        # Elemental Elétrico ataca em linha cardinal de até 3 casas; demais requerem adjacência.
        eh_eletrico = a.get("especial") == "linha_3q"
        if eh_eletrico:
            if not self._em_linha_cardinal(a["pos"], m["pos"], 3):
                await self.send_to(pid, {"type": "error",
                    "msg": "⚡ O elemental elétrico ataca em linha reta (máx 3 casas)."}); return
            if self._linha_bloqueada_por_parede(a["pos"], m["pos"]):
                await self.send_to(pid, {"type": "error",
                    "msg": "⚡ Linha de descarga bloqueada por parede."}); return
        else:
            if not self._cardinal_adjacent(a["pos"], m["pos"]):
                await self.send_to(pid, {"type": "error",
                    "msg": "Servo não está adjacente ao alvo."}); return

        a["acted"] = True
        roll, _esc = self._rolar_d20_escuridao(a, m)   # escuridão: desvantagem/vantagem
        total = roll + a.get("nivel", 1)
        hit = roll == 20 or total >= m["ac"]
        await self.broadcast({"type": "dice_roll", "die": "d20", "value": roll,
                               "label": a["nome"], "hit": hit, "crit": roll == 20})
        if hit:
            dmg = max(1, roll_dice(a.get("dano", "1d4")) * (2 if roll == 20 else 1))
            m["hp"] -= dmg
            await self.gm_say(
                f"⚔️ **{a['nome']}** ataca **{m['name']}** "
                f"(d20={roll}+{a.get('nivel',1)}={total} vs CA {m['ac']}): **{dmg}** de dano!")
            if m["hp"] <= 0:
                await self._monster_dies(m, pid)
            await self._linha_eletrica(a, list(m["pos"]), pid)   # Elemental Elétrico: linha de 3
        else:
            await self.gm_say(
                f"⚔️ **{a['nome']}** ataca **{m['name']}** e erra "
                f"(d20={roll}+{a.get('nivel',1)}={total} vs CA {m['ac']}).")
        await self.push_state()

    async def handle_skill(self, pid, skill_id, target_id):
        if not self._is_turn(pid): return
        p = self.players[pid]
        if not p["alive"]: return

        skill = next((s for s in p["skills"] if s["id"] == skill_id), None)
        if not skill:
            await self.send_to(pid, {"type": "error", "msg": "Habilidade inválida."}); return

        # ── Habilidades de custo Fome/Sede (warrior) ──────────────────────────
        # NOVO MODELO: o warrior ARMA as habilidades no cliente (toggle) e o custo
        # de fome/sede + aplicação das flags acontece em handle_attack (ao agir),
        # com base na lista `buffs` enviada junto do ataque. Aqui é no-op para não
        # cobrar duas vezes caso uma mensagem `skill` chegue para essas skills.
        # (As metamagias do mago também caem aqui — têm mensagens dedicadas.)
        if "mp" not in skill:
            return

        # (Sistema LEGADO de magias de MP — fireball/ice_lance/magic_shield —
        # mantido oculto/inerte. Sem metamagia: Pedro lança pelo GRIMÓRIO.)
        if p["action_done"]:
            return
        custo_mp = skill["mp"]
        if p["mp"] < custo_mp:
            await self.send_to(pid, {"type": "error", "msg": "MP insuficiente."}); return

        p["mp"]  -= custo_mp
        p["fome"] = max(0, p["fome"] - 1)   # custo de sobrevivência da AÇÃO (igual ao ataque básico)
        await self._apply_skill(p, skill, target_id)
        p["action_done"] = True
        await self.push_state()

    async def _apply_skill(self, p, skill, target_id, dmg_mult=1, dur_bonus=1):
        # dmg_mult / dur_bonus: multiplicadores da Metamagia do mago (Aprimorar
        # Magia). Default 1/1 → inerte para todas as outras classes/chamadas.
        sid = skill["id"]
        alive_monsters = [m for m in self.monsters.values() if m["hp"] > 0]
        # Modificador de sobrevivência (+1 saciado / -1/-2 exaustão) — aplicado aos
        # acertos e ao dano das magias, igual ao ataque básico do warrior.
        surv_mod  = self._modificador_sobrevivencia(p)
        preso_pen = -2 if p.get("preso") else 0

        if sid == "heavy_blow":
            t = self.monsters.get(target_id)
            if t:
                if not self._cardinal_adjacent(p["pos"], t["pos"]):
                    await self.gm_say(f"⚠ **{p['name']}** tenta **Golpe Pesado** mas o inimigo está fora de alcance!"); return
                hit, roll, total, crit = d20_attack(p["atk_bonus"] + surv_mod + preso_pen, t["ac"])
                await self.broadcast({"type": "dice_roll", "die": "d20", "value": roll, "label": "Golpe Pesado"})
                if hit:
                    weapon = p["weapon"]
                    raw_dmg = roll_dice(weapon["die"])
                    die_type = "d" + weapon["die"].split("d")[1]
                    await self.broadcast({"type": "dice_roll", "die": die_type, "value": raw_dmg, "label": "Dano"})
                    dmg = (raw_dmg + mod(p[weapon["stat"]])) * 2
                    if crit: dmg *= 2
                    dmg = max(1, dmg + surv_mod)
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
            # Paredes bloqueiam a explosão: só atinge inimigos com linha de visão
            alive_monsters = [m for m in alive_monsters
                              if self._tem_linha_de_visao(p["pos"], m["pos"])]
            for m in alive_monsters:
                dmg = max(1, (roll_dice("4d6") + mod(p["int_"]) + surv_mod) * dmg_mult)
                m["hp"] -= dmg
                total_dmg_list.append(dmg)
            avg = sum(total_dmg_list) // max(1, len(total_dmg_list)) if total_dmg_list else 0
            extra = " ⚡(Aprimorada x2)" if dmg_mult > 1 else ""
            await self.gm_say(f"🔥 **{p['name']}** lança **Bola de Fogo**{extra}! {len(alive_monsters)} inimigo(s) sofrem ~**{avg}** de dano (4d6+INT)!")
            for m in list(alive_monsters):
                if m["hp"] <= 0: await self._monster_dies(m, p["id"])

        elif sid == "ice_lance":
            t = self.monsters.get(target_id)
            if t:
                if not self._tem_linha_de_visao(p["pos"], t["pos"]):
                    await self.send_to(p["id"], {"type": "error",
                        "msg": f"🧱 Uma parede bloqueia a Lança de Gelo até {t['name']}!"}); return
                raw_dmg = roll_dice("3d6")
                await self.broadcast({"type": "dice_roll", "die": "d6", "value": raw_dmg, "label": "Lança de Gelo"})
                dmg = max(1, (raw_dmg + mod(p["int_"]) + surv_mod) * dmg_mult)
                t["hp"] -= dmg
                extra = " ⚡(Aprimorada x2)" if dmg_mult > 1 else ""
                await self.gm_say(f"🧊 **{p['name']}** usa **Lança de Gelo**{extra} em **{t['name']}**: **{dmg}** de dano de frio!")
                if t["hp"] <= 0: await self._monster_dies(t, p["id"])

        elif sid == "magic_shield":
            # +4 CA; Aprimorar (duração x2) concede também +1 turno de validade,
            # registrado em temp_def_turnos para sobreviver a um end_turn extra.
            self.temp_def[p["id"]] = self.temp_def.get(p["id"], 0) + 4
            if dur_bonus > 1:
                self.temp_def_turnos[p["id"]] = max(self.temp_def_turnos.get(p["id"], 0), 2)
                await self.gm_say(f"✨ **{p['name']}** ativa **Escudo Mágico** ⚡(Aprimorado)! +4 CA por 2 turnos.")
            else:
                await self.gm_say(f"✨ **{p['name']}** ativa **Escudo Mágico**! +4 CA até o próximo turno.")

        elif sid == "backstab":
            t = self.monsters.get(target_id)
            if t:
                if not self._cardinal_adjacent(p["pos"], t["pos"]):
                    await self.gm_say(f"⚠ **{p['name']}** tenta **Ataque Furtivo** mas o inimigo está fora de alcance!"); return
                hit, roll, total, crit = d20_attack(p["atk_bonus"] + 2 + surv_mod + preso_pen, t["ac"])
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
                    dmg = max(1, dmg + surv_mod)
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
                dmg = max(1, roll_dice("2d6") + mod(p["int_"]) + surv_mod)
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
                if not self._tem_linha_de_visao(p["pos"], t["pos"]):
                    await self.send_to(p["id"], {"type": "error",
                        "msg": f"🧱 Uma parede bloqueia a linha de tiro até {t['name']}!"}); return
                total_dmg = 0
                hits = 0
                for _ in range(2):
                    hit, roll, total, crit = d20_attack(p["atk_bonus"] + surv_mod + preso_pen, t["ac"])
                    await self.broadcast({"type": "dice_roll", "die": "d20", "value": roll, "label": "Tiro Duplo"})
                    if hit:
                        weapon = p["weapon"]
                        raw_dmg = roll_dice(weapon["die"])
                        die_type = "d" + weapon["die"].split("d")[1]
                        await self.broadcast({"type": "dice_roll", "die": die_type, "value": raw_dmg, "label": "Dano"})
                        if crit: raw_dmg *= 2
                        total_dmg += max(1, raw_dmg + mod(p[weapon["stat"]]) + surv_mod)
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
            # Flechas não atravessam paredes: só inimigos com linha de visão
            alive_monsters = [m for m in alive_monsters
                              if self._tem_linha_de_visao(p["pos"], m["pos"])]
            for m in alive_monsters:
                dmg = max(1, roll_dice("1d8") + mod(p["dex"]) + surv_mod)
                m["hp"] -= dmg
            await self.gm_say(f"🏹 **{p['name']}** usa **Chuva de Flechas**! 1d8+DES em todos os inimigos!")
            for m in list(alive_monsters):
                if m["hp"] <= 0: await self._monster_dies(m, p["id"])

        elif sid == "piercing_shot":
            t = self.monsters.get(target_id)
            if t:
                if not self._tem_linha_de_visao(p["pos"], t["pos"]):
                    await self.send_to(p["id"], {"type": "error",
                        "msg": f"🧱 Uma parede bloqueia a linha de tiro até {t['name']}!"}); return
                weapon = p["weapon"]
                raw_dmg = roll_dice(weapon["die"])
                die_type = "d" + weapon["die"].split("d")[1]
                await self.broadcast({"type": "dice_roll", "die": die_type, "value": raw_dmg, "label": "Tiro Perfurante"})
                dmg = max(1, raw_dmg * 2 + mod(p[weapon["stat"]]) + surv_mod)
                t["hp"] -= dmg
                await self.gm_say(f"🎯 **{p['name']}** usa **Tiro Perfurante** em **{t['name']}**: **{dmg}** de dano (acerto automático, ignora CA)!")
                if t["hp"] <= 0: await self._monster_dies(t, p["id"])

        elif sid == "smite":
            t = self.monsters.get(target_id)
            if t:
                if not self._cardinal_adjacent(p["pos"], t["pos"]):
                    await self.gm_say(f"⚠ **{p['name']}** tenta **Golpe Divino** mas o inimigo está fora de alcance!"); return
                hit, roll, total, crit = d20_attack(p["atk_bonus"] + surv_mod + preso_pen, t["ac"])
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
                    dmg = max(1, base + holy + surv_mod)
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

        # ── Bard (Henrique) ────────────────────────────────────────────────────
        # As habilidades do bardo (Canção Heroica e Provocação) NÃO passam por
        # _apply_skill: têm mensagens dedicadas (ativar_cancao / desativar_cancao /
        # provocacao) porque dependem de seleção de atributos e de alvo próprio,
        # fora do fluxo genérico de `skill`. A passiva Conhecimento das Lendas é
        # puramente de cliente (hover revela a ficha do monstro, cujos dados já
        # viajam no push_state). Ver handle_ativar_cancao / handle_provocacao.

    # ── Mago: Metamagia (Pedro) — toggles de ação livre ─────────────────────
    # 3 toggles EMPILHÁVEIS que MODIFICAM a magia do GRIMÓRIO lançada neste turno
    # (aplicadas em handle_magia). Não cobram nada ao armar — o custo em fome/sede
    # é pago ao LANÇAR e só se a habilidade tiver efeito. Flags limpas em handle_end_turn.

    async def _toggle_metamagia(self, pid, flag, nome, icone):
        if not self._is_turn(pid): return
        p = self.players.get(pid)
        if not p or not p["alive"]: return
        if p.get("class_id") != "mage":
            await self.send_to(pid, {"type": "error", "msg": f"Apenas Pedro pode usar {nome}."}); return
        novo = not p.get(flag)
        p[flag] = novo
        await self.gm_say(f"{icone} **{p['name']}** {'arma' if novo else 'desarma'} **{nome}**"
                          + (" (custo ao lançar)." if novo else "."))
        await self.push_state()

    async def handle_aprimorar_magia(self, pid, data=None):
        await self._toggle_metamagia(pid, "aprimorar_ativo", "Aprimorar Magia", "🎯")

    async def handle_estender_magia(self, pid, data=None):
        await self._toggle_metamagia(pid, "estender_ativo", "Estender Magia", "⏱️")

    async def handle_fortalecer_magia(self, pid, data=None):
        await self._toggle_metamagia(pid, "fortalecer_ativo", "Fortalecer Magia", "💥")

    # ── Bardo: Canção Heroica (toggle de buffs musicais) ────────────────────

    def _no_raio(self, origem, alvo, raio):
        """True se `alvo` está dentro de `raio` (Chebyshev) de `origem`."""
        return _distancia_chebyshev(origem["pos"], alvo["pos"]) <= raio

    async def handle_ativar_cancao(self, pid, data):
        if not self._is_turn(pid): return
        p = self.players.get(pid)
        if not p or not p["alive"]: return
        if p.get("class_id") != "bard":
            await self.send_to(pid, {"type": "error", "msg": "Apenas Henrique pode usar esta habilidade."}); return
        if p.get("cancao_ativa"):
            await self.send_to(pid, {"type": "error", "msg": "Desative a canção atual antes de trocar os atributos."}); return

        atributos = data.get("atributos", []) if data else []
        ids_validos = [a["id"] for a in CANCAO_ATRIBUTOS]
        atrib_validos = [a for a in atributos if a in ids_validos]
        if not atrib_validos:
            await self.send_to(pid, {"type": "error", "msg": "Escolha pelo menos um atributo para a canção."}); return

        custo = _calcular_custo_cancao(atrib_validos)
        if p["fome"] < custo["fome"] or p["sede"] < custo["sede"]:
            await self.send_to(pid, {"type": "error",
                "msg": f"Recursos insuficientes — precisa 🍖{custo['fome']} 💧{custo['sede']}."}); return

        p["fome"] = max(0, p["fome"] - custo["fome"])
        p["sede"] = max(0, p["sede"] - custo["sede"])

        p["cancao_ativa"]       = True
        p["cancao_atributos"]   = atrib_validos
        p["cancao_custo"]       = custo
        p["cancao_atacou_apos"] = False

        await self._aplicar_buffs_cancao(p)
        labels = ", ".join(next(a["label"] for a in CANCAO_ATRIBUTOS if a["id"] == x) for x in atrib_validos)
        await self.gm_say(
            f"🎵 **{p['name']}** entoa a **Canção Heroica** [{labels}]! "
            f"Aliados em {CANCAO_RAIO} quadrados são inspirados (🍖-{custo['fome']} 💧-{custo['sede']}).")
        await self.push_state()

    async def handle_desativar_cancao(self, pid, data=None):
        p = self.players.get(pid)
        if not p or not p.get("cancao_ativa"): return
        await self._remover_buffs_cancao(p)
        p["cancao_ativa"]     = False
        p["cancao_atributos"] = []
        p["cancao_custo"]     = {"fome": 0, "sede": 0}
        await self.gm_say(f"🔇 **{p['name']}** encerra a Canção Heroica.")
        await self.push_state()

    async def _aplicar_buffs_cancao(self, bardo):
        """(Re)aplica os buffs da canção aos aliados vivos dentro do raio."""
        buffs = {}
        for attr_id in bardo.get("cancao_atributos", []):
            attr = next((a for a in CANCAO_ATRIBUTOS if a["id"] == attr_id), None)
            if attr:
                buffs[attr["efeito"]] = 1
        for jogador in self.players.values():
            if not jogador.get("alive"): continue
            if not self._no_raio(bardo, jogador, CANCAO_RAIO): continue
            jogador["buffs_cancao"] = buffs.copy()

    async def _remover_buffs_cancao(self, bardo):
        """Remove os buffs da canção de todos os jogadores."""
        for jogador in self.players.values():
            jogador.pop("buffs_cancao", None)

    async def _cobrar_manutencao_cancao(self, p):
        """Upkeep da canção, cobrado no início do turno do bardo. Sem recursos,
        a canção é interrompida. Com recursos, debita e reaplica os buffs (os
        aliados podem ter se movido para dentro/fora do raio)."""
        if not p.get("cancao_ativa"): return
        custo = p.get("cancao_custo", {"fome": 0, "sede": 0})
        if p["fome"] < custo["fome"] or p["sede"] < custo["sede"]:
            await self._remover_buffs_cancao(p)
            p["cancao_ativa"]     = False
            p["cancao_atributos"] = []
            p["cancao_custo"]     = {"fome": 0, "sede": 0}
            await self.gm_say(f"🔇 A Canção Heroica de **{p['name']}** se cala — recursos insuficientes.")
            return
        p["fome"] = max(0, p["fome"] - custo["fome"])
        p["sede"] = max(0, p["sede"] - custo["sede"])
        await self._remover_buffs_cancao(p)
        await self._aplicar_buffs_cancao(p)
        labels = ", ".join(next(a["label"] for a in CANCAO_ATRIBUTOS if a["id"] == x) for x in p.get("cancao_atributos", []))
        await self.gm_say(f"🎵 Canção Heroica de **{p['name']}** [{labels}] — manutenção 🍖-{custo['fome']} 💧-{custo['sede']}.")

    def _interromper_cancao(self, p, motivo):
        """Cancela a canção sem push (chamado de contextos síncronos, ex.: morte).
        Limpa os buffs dos aliados de forma síncrona."""
        if not p.get("cancao_ativa"): return None
        for jogador in self.players.values():
            jogador.pop("buffs_cancao", None)
        p["cancao_ativa"]     = False
        p["cancao_atributos"] = []
        p["cancao_custo"]     = {"fome": 0, "sede": 0}
        return f"🔇 A Canção Heroica de **{p['name']}** é interrompida — {motivo}."

    # ── Bardo: Provocação (ação bônus de controle) ──────────────────────────

    async def handle_provocacao(self, pid, data):
        if not self._is_turn(pid): return
        p = self.players.get(pid)
        if not p or not p["alive"]: return
        if p.get("class_id") != "bard":
            await self.send_to(pid, {"type": "error", "msg": "Apenas Henrique pode usar Provocação."}); return
        if p.get("bonus_action_used"):
            await self.send_to(pid, {"type": "error", "msg": "Ação bônus já usada neste turno."}); return

        fome_cost, sede_cost = 3, 3
        if p["fome"] < fome_cost or p["sede"] < sede_cost:
            await self.send_to(pid, {"type": "error",
                "msg": f"Recursos insuficientes — precisa 🍖{fome_cost} 💧{sede_cost}."}); return

        alvo = self.monsters.get(data.get("target_id")) if data else None
        if not alvo or alvo["hp"] <= 0:
            await self.send_to(pid, {"type": "error", "msg": "Alvo não encontrado."}); return
        if not self._no_raio(p, alvo, PROVOCACAO_RAIO):
            await self.send_to(pid, {"type": "error",
                "msg": f"Alvo fora do alcance — máximo {PROVOCACAO_RAIO} quadrados."}); return
        if alvo.get("provocado_turnos", 0) > 0:
            await self.send_to(pid, {"type": "error", "msg": "Este inimigo já está provocado."}); return

        p["fome"] = max(0, p["fome"] - fome_cost)
        p["sede"] = max(0, p["sede"] - sede_cost)
        p["bonus_action_used"] = True

        alvo["provocado"]              = True
        alvo["provocado_turnos"]       = PROVOCACAO_TURNOS   # 1 turno de desvantagem + 3 de alvo forçado
        alvo["provocado_turno_efeito"] = True                # próximo ataque do inimigo é com desvantagem
        alvo["provocado_por"]          = pid                 # Henrique é o alvo forçado

        await self.gm_say(
            f"😤 **{p['name']}** provoca **{alvo['name']}**! Desvantagem no próximo ataque "
            f"e alvo forçado por 3 turnos (🍖-{fome_cost} 💧-{sede_cost}).")
        await self.push_state()

    # ── Frade Lewis (cleric): milagres de cura ──────────────────────────────
    # As 4 habilidades de Lewis NÃO passam pelo fluxo genérico de `skill` (não
    # têm "mp"): cada uma é uma ação principal dedicada com custo em fome/sede,
    # no mesmo modelo do warrior/bardo/paladino. INT modifica a cura. Alcance via
    # _no_raio (Chebyshev). Purificação reverte efeitos de veneno/petrificação
    # usando _reverter_efeito_veneno (espelha a expiração em _processar_venenos_turno).

    PURIFICACAO_CUSTOS = {
        "veneno":       {"fome": 1, "sede": 0},
        "doenca":       {"fome": 2, "sede": 1},
        "maldicao":     {"fome": 3, "sede": 2},
        "petrificacao": {"fome": 5, "sede": 5},
    }

    async def handle_cura(self, pid, data):
        """Cura individual: 1–3 d8 + INT. -1 sede/dado, alcance estendível com fome."""
        if not self._is_turn(pid): return
        p = self.players.get(pid)
        if not p or not p["alive"]: return
        if p.get("class_id") != "cleric":
            await self.send_to(pid, {"type": "error", "msg": "Apenas Lewis pode usar Cura."}); return
        if p.get("action_done"):
            await self.send_to(pid, {"type": "error", "msg": "Ação principal já usada neste turno."}); return

        num_dados = max(1, min(3, int((data or {}).get("num_dados", 1))))
        alcance   = max(0, min(2, int((data or {}).get("alcance_extra", 0))))
        custo_sede = num_dados          # -1 sede por dado
        custo_fome = alcance            # -1 fome por extensão de alcance
        alcance_tiles = 1 + alcance * 3 # 1, 4 ou 7 quadrados

        if p["sede"] < custo_sede:
            await self.send_to(pid, {"type": "error", "msg": f"Sede insuficiente — precisa 💧{custo_sede}."}); return
        if p["fome"] < custo_fome:
            await self.send_to(pid, {"type": "error", "msg": f"Fome insuficiente — precisa 🍖{custo_fome}."}); return

        alvo = self.players.get((data or {}).get("target_id"))
        if not alvo or not alvo.get("alive"):
            await self.send_to(pid, {"type": "error", "msg": "Aliado inválido."}); return
        if not self._no_raio(p, alvo, alcance_tiles):
            await self.send_to(pid, {"type": "error", "msg": f"Alvo fora do alcance — máximo {alcance_tiles}q."}); return
        if not self._tem_linha_de_visao(p["pos"], alvo["pos"]):
            await self.send_to(pid, {"type": "error",
                "msg": "🧱 Uma parede bloqueia a energia curativa — precisa ver o aliado!"}); return

        dados = [random.randint(1, 8) for _ in range(num_dados)]
        bonus_int = mod(p["int_"])
        cura = max(1, sum(dados) + bonus_int)
        await self.broadcast({"type": "dice_roll", "die": "d8", "value": sum(dados), "label": "Cura"})

        hp_antes = alvo["hp"]
        alvo["hp"] = min(alvo["max_hp"], alvo["hp"] + cura)
        cura_real = alvo["hp"] - hp_antes

        p["sede"] = max(0, p["sede"] - custo_sede)
        p["fome"] = max(0, p["fome"] - custo_fome)
        p["action_done"] = True

        dados_str = "+".join(str(d) for d in dados)
        await self.gm_say(
            f"🙌 **{p['name']}** cura **{alvo['name']}** — {num_dados}d8({dados_str})"
            f"{'+' if bonus_int >= 0 else ''}{bonus_int} = **{cura_real}** HP "
            f"({alvo['hp']}/{alvo['max_hp']}) | alcance {alcance_tiles}q "
            f"(🍖-{custo_fome} 💧-{custo_sede})")
        await self.push_state()

    async def handle_cura_area(self, pid, data):
        """Cura em área: 1–3 d8 + INT em todos os aliados vivos no raio 5."""
        if not self._is_turn(pid): return
        p = self.players.get(pid)
        if not p or not p["alive"]: return
        if p.get("class_id") != "cleric":
            await self.send_to(pid, {"type": "error", "msg": "Apenas Lewis pode usar Cura em Área."}); return
        if p.get("action_done"):
            await self.send_to(pid, {"type": "error", "msg": "Ação principal já usada neste turno."}); return

        num_dados  = max(1, min(3, int((data or {}).get("num_dados", 1))))
        custo_fome = num_dados * 4
        custo_sede = num_dados * 4
        raio = 5

        if p["fome"] < custo_fome or p["sede"] < custo_sede:
            await self.send_to(pid, {"type": "error",
                "msg": f"Recursos insuficientes — precisa 🍖{custo_fome} 💧{custo_sede}."}); return

        dados = [random.randint(1, 8) for _ in range(num_dados)]
        bonus_int = mod(p["int_"])
        cura = max(1, sum(dados) + bonus_int)
        await self.broadcast({"type": "dice_roll", "die": "d8", "value": sum(dados), "label": "Cura em Área"})

        curados = []
        for aliado in self.players.values():
            if not aliado.get("alive"): continue
            if not self._no_raio(p, aliado, raio): continue
            # A onda curativa não atravessa paredes — só aliados visíveis
            if not self._tem_linha_de_visao(p["pos"], aliado["pos"]): continue
            hp_antes = aliado["hp"]
            aliado["hp"] = min(aliado["max_hp"], aliado["hp"] + cura)
            cura_real = aliado["hp"] - hp_antes
            if cura_real > 0:
                curados.append(f"{aliado['name']}(+{cura_real})")

        p["fome"] = max(0, p["fome"] - custo_fome)
        p["sede"] = max(0, p["sede"] - custo_sede)
        p["action_done"] = True

        dados_str = "+".join(str(d) for d in dados)
        await self.gm_say(
            f"🌟 **{p['name']}** invoca **Cura em Área** — {num_dados}d8({dados_str})"
            f"{'+' if bonus_int >= 0 else ''}{bonus_int} HP no raio {raio}q "
            f"| {len(curados)} curado(s)"
            f"{': ' + ', '.join(curados) if curados else ''} "
            f"(🍖-{custo_fome} 💧-{custo_sede})")
        await self.push_state()

    def _reverter_efeito_veneno(self, alvo, efeito):
        """Desfaz um efeito de veneno ativo (espelha a expiração em
        _processar_venenos_turno). Restaura scores/HP/saves/penalidades."""
        alvo.setdefault("penalidades", {})
        op = efeito.get("operacao")
        if op == "reduzir":
            if efeito.get("attr_key"):     # jogador — restaura score
                alvo[efeito["attr_key"]] = min(25, alvo.get(efeito["attr_key"], 10) + efeito["valor"])
                if efeito.get("hp_delta"):
                    alvo["max_hp"] += efeito["hp_delta"]
                if efeito.get("fort_delta"):
                    alvo["fort"] = alvo.get("fort", 0) + efeito["fort_delta"]
            else:                          # monstro — desfaz tradução
                if efeito.get("hp_perdido"):
                    alvo["max_hp"] = alvo.get("max_hp", alvo.get("hp", 1)) + efeito["hp_perdido"]
                if efeito.get("pen_dano"):
                    alvo["penalidades"]["dano"] = alvo["penalidades"].get("dano", 0) + efeito["pen_dano"]
        elif op == "penalidade":
            for attr, val in efeito.get("atributos", []):
                alvo["penalidades"][attr] = alvo["penalidades"].get(attr, 0) - val

    async def handle_purificacao(self, pid, data):
        """Remove veneno, doença, maldição ou petrificação de um aliado adjacente."""
        if not self._is_turn(pid): return
        p = self.players.get(pid)
        if not p or not p["alive"]: return
        if p.get("class_id") != "cleric":
            await self.send_to(pid, {"type": "error", "msg": "Apenas Lewis pode usar Purificação."}); return
        if p.get("action_done"):
            await self.send_to(pid, {"type": "error", "msg": "Ação principal já usada neste turno."}); return

        tipo = (data or {}).get("tipo")
        if tipo not in self.PURIFICACAO_CUSTOS:
            await self.send_to(pid, {"type": "error", "msg": "Tipo de purificação inválido."}); return
        custo = self.PURIFICACAO_CUSTOS[tipo]

        alvo = self.players.get((data or {}).get("target_id"))
        if not alvo or not alvo.get("alive"):
            await self.send_to(pid, {"type": "error", "msg": "Aliado inválido."}); return
        if not self._no_raio(p, alvo, 1):
            await self.send_to(pid, {"type": "error", "msg": "Purificação requer contato adjacente."}); return
        if p["fome"] < custo["fome"] or p["sede"] < custo["sede"]:
            await self.send_to(pid, {"type": "error",
                "msg": f"Recursos insuficientes — precisa 🍖{custo['fome']} 💧{custo['sede']}."}); return

        nomes = {"veneno": "veneno", "doenca": "doença",
                 "maldicao": "maldição", "petrificacao": "petrificação"}
        removido = False

        if tipo == "veneno":
            efeitos = alvo.get("efeitos_veneno", [])
            cego = alvo.get("cego")
            if efeitos or cego:
                for efeito in efeitos:
                    self._reverter_efeito_veneno(alvo, efeito)
                alvo["efeitos_veneno"] = []
                if cego:
                    alvo["cego"] = False
                    alvo["cego_rodadas"] = 0
                    pen = alvo.pop("cego_pen_ataque", -4)
                    alvo.setdefault("penalidades", {})
                    alvo["penalidades"]["ataque"] = alvo["penalidades"].get("ataque", 0) - pen
                    alvo["bloqueia_distancia"] = False
                removido = True
            else:
                await self.send_to(pid, {"type": "error", "msg": f"{alvo['name']} não está envenenado."}); return

        elif tipo == "petrificacao":
            if alvo.get("petrificado"):
                alvo["petrificado"] = False
                alvo["petrificado_rodadas"] = 0
                removido = True
            else:
                await self.send_to(pid, {"type": "error", "msg": f"{alvo['name']} não está petrificado."}); return

        elif tipo == "doenca":
            if alvo.get("doente"):
                self._curar_doenca(alvo)   # remove a doença inteira e reverte os atributos
                removido = True
            else:
                await self.send_to(pid, {"type": "error", "msg": f"{alvo['name']} não está doente."}); return

        elif tipo == "maldicao":
            if alvo.get("amaldicoado"):
                alvo["amaldicoado"] = False
                alvo["maldicao_tipo"] = None
                removido = True
            else:
                await self.send_to(pid, {"type": "error", "msg": f"{alvo['name']} não está amaldiçoado."}); return

        if removido:
            p["fome"] = max(0, p["fome"] - custo["fome"])
            p["sede"] = max(0, p["sede"] - custo["sede"])
            p["action_done"] = True
            await self.gm_say(
                f"✨ **{p['name']}** purifica **{alvo['name']}** — livre de "
                f"{nomes[tipo]}! (🍖-{custo['fome']} 💧-{custo['sede']})")
            await self.push_state()

    async def handle_ressurreicao(self, pid, data):
        """Traz um aliado morto adjacente de volta com 1 HP. -10 fome -10 sede."""
        if not self._is_turn(pid): return
        p = self.players.get(pid)
        if not p or not p["alive"]: return
        if p.get("class_id") != "cleric":
            await self.send_to(pid, {"type": "error", "msg": "Apenas Lewis pode usar Ressurreição."}); return
        if p.get("action_done"):
            await self.send_to(pid, {"type": "error", "msg": "Ação principal já usada neste turno."}); return

        custo_fome, custo_sede = 10, 10
        if p["fome"] < custo_fome or p["sede"] < custo_sede:
            await self.send_to(pid, {"type": "error",
                "msg": f"Recursos insuficientes — precisa 🍖{custo_fome} 💧{custo_sede}."}); return

        alvo = self.players.get((data or {}).get("target_id"))
        if not alvo:
            await self.send_to(pid, {"type": "error", "msg": "Aliado não encontrado."}); return
        if alvo.get("alive"):
            await self.send_to(pid, {"type": "error", "msg": f"{alvo['name']} ainda está vivo."}); return
        if not self._no_raio(p, alvo, 1):
            await self.send_to(pid, {"type": "error", "msg": "Ressurreição requer contato adjacente com o aliado."}); return

        alvo["alive"] = True
        alvo["hp"] = 1
        alvo["action_done"] = True          # ressuscitado não age neste turno
        alvo["bonus_action_used"] = True
        # Limpa os efeitos que possam ter causado/seguido a morte
        alvo["petrificado"] = False
        alvo["petrificado_rodadas"] = 0
        alvo["efeitos_veneno"] = []

        p["fome"] = max(0, p["fome"] - custo_fome)
        p["sede"] = max(0, p["sede"] - custo_sede)
        p["action_done"] = True

        await self.gm_say(
            f"💫 **RESSURREIÇÃO!** **{p['name']}** traz **{alvo['name']}** de volta à "
            f"vida com **1 HP**! (🍖-{custo_fome} 💧-{custo_sede})")
        await self.push_state()

    # ── Paladino (Richard): aço e honra ─────────────────────────────────────
    # As 5 habilidades de Richard NÃO passam pelo fluxo genérico de `skill` (não
    # têm "mp"): Imposição das Mãos é ação principal dedicada; Golpe Sagrado e
    # Protetor são ações bônus alternáveis; Regeneração Divina e Guerreiro da Luz
    # são ações livres. Custo e manutenção em fome/sede, no mesmo modelo do
    # warrior/bardo. Upkeep em _processar_manutencao_richard (início do turno);
    # transferência de dano do Protetor em _processar_dano_protetor (gm_phase);
    # bônus de combate (acerto/dano/CA) integrados em handle_attack / gm_phase.

    async def handle_imposicao_maos(self, pid, data):
        if not self._is_turn(pid): return
        p = self.players.get(pid)
        if not p or not p["alive"]: return
        if p.get("class_id") != "paladin":
            await self.send_to(pid, {"type": "error", "msg": "Apenas Richard pode usar esta habilidade."}); return
        if p.get("action_done"):
            await self.send_to(pid, {"type": "error", "msg": "Ação principal já usada neste turno."}); return

        fome_cost, sede_cost = 3, 2
        if p["fome"] < fome_cost or p["sede"] < sede_cost:
            await self.send_to(pid, {"type": "error", "msg": f"Recursos insuficientes 🍖{fome_cost} 💧{sede_cost}."}); return

        alvo_id = data.get("target_id") if data else None
        if alvo_id == pid:
            await self.send_to(pid, {"type": "error", "msg": "Richard não pode curar a si mesmo com esta habilidade."}); return
        alvo = self.players.get(alvo_id)
        if not alvo or not alvo.get("alive"):
            await self.send_to(pid, {"type": "error", "msg": "Aliado inválido."}); return
        if not self._no_raio(p, alvo, 1):
            await self.send_to(pid, {"type": "error", "msg": "Aliado deve estar adjacente a Richard."}); return

        raw = roll_dice("1d6")
        await self.broadcast({"type": "dice_roll", "die": "d6", "value": raw, "label": "Imposição das Mãos"})
        cura = max(1, raw + mod(p["str_"]))
        hp_antes = alvo["hp"]
        alvo["hp"] = min(alvo["max_hp"], alvo["hp"] + cura)
        cura_efetiva = alvo["hp"] - hp_antes

        p["fome"] = max(0, p["fome"] - fome_cost)
        p["sede"] = max(0, p["sede"] - sede_cost)
        p["action_done"] = True

        await self.gm_say(
            f"🙏 **{p['name']}** usa **Imposição das Mãos** em **{alvo['name']}** — "
            f"cura **{cura_efetiva}** HP ({alvo['hp']}/{alvo['max_hp']})! (🍖-{fome_cost} 💧-{sede_cost})")
        await self.push_state()

    async def handle_golpe_sagrado(self, pid, data=None):
        if not self._is_turn(pid): return
        p = self.players.get(pid)
        if not p or not p["alive"]: return
        if p.get("class_id") != "paladin":
            await self.send_to(pid, {"type": "error", "msg": "Apenas Richard pode usar Golpe Sagrado."}); return
        if p.get("golpe_sagrado_ativo"):
            await self.send_to(pid, {"type": "error", "msg": "Golpe Sagrado já está ativo."}); return
        if p.get("bonus_action_used"):
            await self.send_to(pid, {"type": "error", "msg": "Ação bônus já usada neste turno."}); return

        fome_cost, sede_cost = 3, 3
        if p["fome"] < fome_cost or p["sede"] < sede_cost:
            await self.send_to(pid, {"type": "error", "msg": f"Recursos insuficientes 🍖{fome_cost} 💧{sede_cost}."}); return

        p["fome"] = max(0, p["fome"] - fome_cost)
        p["sede"] = max(0, p["sede"] - sede_cost)
        p["golpe_sagrado_ativo"] = True
        p["bonus_action_used"] = True

        await self.gm_say(
            f"⚔️ **{p['name']}** invoca **Golpe Sagrado** — +1d8 de dano sagrado por ataque! "
            f"(🍖-{fome_cost} 💧-{sede_cost})")
        await self.push_state()

    async def handle_desativar_golpe_sagrado(self, pid, data=None):
        p = self.players.get(pid)
        if not p or p.get("class_id") != "paladin" or not p.get("golpe_sagrado_ativo"): return
        p["golpe_sagrado_ativo"] = False
        await self.gm_say(f"⚔️ **{p['name']}** baixa a lâmina sagrada — Golpe Sagrado desativado.")
        await self.push_state()

    async def handle_protetor(self, pid, data):
        if not self._is_turn(pid): return
        p = self.players.get(pid)
        if not p or not p["alive"]: return
        if p.get("class_id") != "paladin":
            await self.send_to(pid, {"type": "error", "msg": "Apenas Richard pode usar Protetor."}); return
        if p.get("bonus_action_used"):
            await self.send_to(pid, {"type": "error", "msg": "Ação bônus já usada neste turno."}); return

        fome_cost, sede_cost = 2, 2
        if p["fome"] < fome_cost or p["sede"] < sede_cost:
            await self.send_to(pid, {"type": "error", "msg": f"Recursos insuficientes 🍖{fome_cost} 💧{sede_cost}."}); return

        alvo_id = data.get("target_id") if data else None
        if alvo_id == pid:
            await self.send_to(pid, {"type": "error", "msg": "Richard não pode se proteger com esta habilidade."}); return
        alvo = self.players.get(alvo_id)
        if not alvo or not alvo.get("alive"):
            await self.send_to(pid, {"type": "error", "msg": "Aliado inválido."}); return
        if not self._no_raio(p, alvo, 4):
            await self.send_to(pid, {"type": "error", "msg": "Aliado fora do raio de 4 quadrados."}); return

        p["fome"] = max(0, p["fome"] - fome_cost)
        p["sede"] = max(0, p["sede"] - sede_cost)
        p["protetor_ativo"] = True
        p["protetor_alvo"] = alvo_id
        p["bonus_action_used"] = True

        await self.gm_say(
            f"🛡️ **{p['name']}** torna-se **Protetor** de **{alvo['name']}** — "
            f"metade do dano recebido será transferido a Richard! (🍖-{fome_cost} 💧-{sede_cost})")
        await self.push_state()

    async def handle_desativar_protetor(self, pid, data=None):
        p = self.players.get(pid)
        if not p or p.get("class_id") != "paladin" or not p.get("protetor_ativo"): return
        p["protetor_ativo"] = False
        p["protetor_alvo"] = None
        await self.gm_say(f"🛡️ **{p['name']}** encerra a proteção — Protetor desativado.")
        await self.push_state()

    async def handle_acao_livre_richard(self, pid, data):
        if not self._is_turn(pid): return
        p = self.players.get(pid)
        if not p or not p["alive"]: return
        if p.get("class_id") != "paladin":
            await self.send_to(pid, {"type": "error", "msg": "Apenas Richard pode usar esta habilidade."}); return

        habilidade_id = data.get("habilidade_id") if data else None
        if habilidade_id == "regeneracao_divina":
            await self._ativar_regeneracao_divina(p, pid)
        elif habilidade_id == "guerreiro_luz":
            await self._ativar_guerreiro_luz(p, pid, data)
        else:
            await self.send_to(pid, {"type": "error", "msg": "Habilidade livre inválida."}); return
        await self.push_state()

    async def _ativar_regeneracao_divina(self, p, pid):
        if p.get("regeneracao_ativa"):
            # Toggle: re-invocar enquanto ativa desliga (botão PARAR no cliente)
            p["regeneracao_ativa"] = False
            await self.gm_say(f"✨ **{p['name']}** encerra a Regeneração Divina.")
            return
        if p.get("hp", 0) >= p.get("max_hp", 1):
            await self.send_to(pid, {"type": "error", "msg": "HP já está no máximo."}); return

        fome_cost, sede_cost = 2, 1
        if p["fome"] < fome_cost or p["sede"] < sede_cost:
            await self.send_to(pid, {"type": "error", "msg": f"Recursos insuficientes 🍖{fome_cost} 💧{sede_cost}."}); return

        p["fome"] = max(0, p["fome"] - fome_cost)
        p["sede"] = max(0, p["sede"] - sede_cost)
        p["regeneracao_ativa"] = True
        await self.gm_say(f"✨ **{p['name']}** ativa **Regeneração Divina** — +1 HP por turno. (🍖-{fome_cost} 💧-{sede_cost})")

    async def _ativar_guerreiro_luz(self, p, pid, data):
        if p.get("guerreiro_luz_ativo"):
            # Toggle: dissipa se já estava ativo
            p["guerreiro_luz_ativo"] = False
            p["guerreiro_luz_bonus"] = {}
            p["guerreiro_luz_custo"] = {"fome": 0, "sede": 0}
            await self.gm_say(f"💡 **{p['name']}** dissipa o Guerreiro da Luz.")
            return

        bonus = (data.get("bonus") or {}) if data else {}
        def _b(k):
            try:    return min(2, max(0, int(bonus.get(k, 0))))
            except (TypeError, ValueError): return 0
        bonus_validos = {"visao": _b("visao"), "ataque": _b("ataque"),
                         "dano": _b("dano"), "ca": _b("ca")}

        custo_fome = bonus_validos["dano"] + bonus_validos["ca"]
        custo_sede = bonus_validos["visao"] + bonus_validos["ataque"]
        if custo_fome == 0 and custo_sede == 0:
            await self.send_to(pid, {"type": "error", "msg": "Escolha pelo menos um bônus."}); return
        if p["fome"] < custo_fome or p["sede"] < custo_sede:
            await self.send_to(pid, {"type": "error", "msg": f"Recursos insuficientes 🍖{custo_fome} 💧{custo_sede}."}); return

        p["fome"] = max(0, p["fome"] - custo_fome)
        p["sede"] = max(0, p["sede"] - custo_sede)
        p["guerreiro_luz_ativo"] = True
        p["guerreiro_luz_bonus"] = bonus_validos
        p["guerreiro_luz_custo"] = {"fome": custo_fome, "sede": custo_sede}
        await self.gm_say(
            f"💡 **{p['name']}** torna-se **Guerreiro da Luz** | "
            f"visão+{bonus_validos['visao']} ataque+{bonus_validos['ataque']} "
            f"dano+{bonus_validos['dano']} CA+{bonus_validos['ca']} "
            f"(manutenção 🍖-{custo_fome} 💧-{custo_sede}).")
        # Revela imediatamente com o novo raio (o bônus de Visão expande a névoa
        # já na casa atual, sem esperar o próximo movimento). explored é cumulativo.
        if bonus_validos["visao"] > 0 and p.get("pos"):
            raio = self._get_raio_visao(p)
            self._reveal_around(p["pos"][0], p["pos"][1], radius=raio)
            await self.gm_say(f"👁️ Visão de **{p['name']}** expandida para raio {raio}.")

    async def _processar_manutencao_richard(self, p):
        """Upkeep das habilidades sustentadas de Richard — cobrado no início do
        seu turno. Sem recursos, a habilidade correspondente é interrompida."""
        if p.get("class_id") != "paladin" or not p.get("alive"): return

        # Regeneração Divina — +1 HP por turno até o máximo
        if p.get("regeneracao_ativa"):
            if p["hp"] >= p["max_hp"]:
                p["regeneracao_ativa"] = False
                await self.gm_say(f"✨ Regeneração Divina de **{p['name']}** se encerra — HP máximo atingido.")
            elif p["fome"] < 1 or p["sede"] < 1:
                p["regeneracao_ativa"] = False
                await self.gm_say(f"✨ Regeneração Divina de **{p['name']}** se interrompe — recursos insuficientes.")
            else:
                p["hp"] = min(p["max_hp"], p["hp"] + 1)
                p["fome"] = max(0, p["fome"] - 1)
                p["sede"] = max(0, p["sede"] - 1)
                await self.gm_say(f"✨ **{p['name']}** — Regeneração Divina: +1 HP ({p['hp']}/{p['max_hp']}) 🍖-1 💧-1.")

        # Golpe Sagrado — manutenção 🍖-1 💧-1
        if p.get("golpe_sagrado_ativo"):
            if p["fome"] < 1 or p["sede"] < 1:
                p["golpe_sagrado_ativo"] = False
                await self.gm_say(f"⚔️ Golpe Sagrado de **{p['name']}** se desfaz — recursos insuficientes.")
            else:
                p["fome"] = max(0, p["fome"] - 1)
                p["sede"] = max(0, p["sede"] - 1)
                await self.gm_say(f"⚔️ Golpe Sagrado de **{p['name']}** sustentado 🍖-1 💧-1.")

        # Protetor — manutenção 🍖-1; cai se aliado morrer/sair do raio
        if p.get("protetor_ativo"):
            alvo = self.players.get(p.get("protetor_alvo"))
            if p["fome"] < 1:
                p["protetor_ativo"] = False
                p["protetor_alvo"] = None
                await self.gm_say(f"🛡️ Protetor de **{p['name']}** se interrompe — fome insuficiente.")
            elif not alvo or not alvo.get("alive") or not self._no_raio(p, alvo, 4):
                p["protetor_ativo"] = False
                p["protetor_alvo"] = None
                await self.gm_say(f"🛡️ Protetor de **{p['name']}** se desfaz — aliado fora do raio.")
            else:
                p["fome"] = max(0, p["fome"] - 1)
                await self.gm_say(f"🛡️ **{p['name']}** mantém Protetor sobre **{alvo['name']}** 🍖-1.")

        # Guerreiro da Luz — manutenção conforme os bônus escolhidos
        if p.get("guerreiro_luz_ativo"):
            custo = p.get("guerreiro_luz_custo", {"fome": 0, "sede": 0})
            if p["fome"] < custo["fome"] or p["sede"] < custo["sede"]:
                p["guerreiro_luz_ativo"] = False
                p["guerreiro_luz_bonus"] = {}
                await self.gm_say(f"💡 Guerreiro da Luz de **{p['name']}** se apaga — recursos insuficientes.")
            else:
                p["fome"] = max(0, p["fome"] - custo["fome"])
                p["sede"] = max(0, p["sede"] - custo["sede"])
                await self.gm_say(f"💡 Guerreiro da Luz de **{p['name']}** sustentado 🍖-{custo['fome']} 💧-{custo['sede']}.")

    async def _processar_dano_protetor(self, alvo_id, dano_original):
        """Se `alvo_id` está sob Protetor de um Richard vivo e no raio, divide o
        dano (ambos arredondam para baixo). Retorna (dano_no_alvo, transferencia),
        onde transferencia é (richard, dano_richard) ou None."""
        richard = next(
            (q for q in self.players.values()
             if q.get("class_id") == "paladin"
             and q.get("protetor_ativo")
             and q.get("protetor_alvo") == alvo_id
             and q.get("alive")),
            None)
        if not richard:
            return dano_original, None
        alvo = self.players.get(alvo_id)
        if not alvo or not self._no_raio(richard, alvo, 4):
            richard["protetor_ativo"] = False
            richard["protetor_alvo"] = None
            await self.gm_say(f"🛡️ Protetor de **{richard['name']}** se desfaz — aliado saiu do raio.")
            return dano_original, None
        dano_aliado  = dano_original // 2
        dano_richard = dano_original // 2
        await self.gm_say(
            f"🛡️ **Protetor** absorve! **{alvo['name']}** recebe {dano_aliado}, "
            f"**{richard['name']}** recebe {dano_richard}.")
        return dano_aliado, (richard, dano_richard)

    # ── exit dungeon (return to city via entrance stairs) ──────────────────

    async def handle_exit_dungeon(self, pid):
        if self.phase != "playing": return
        p = self.players.get(pid)
        if not p or not p["alive"]: return
        await self.gm_say(f"🚪 **{p['name']}** usa as escadas de saída. Os aventureiros retornam à cidade!")
        await self._voltar_para_cidade()

    async def _voltar_para_cidade(self):
        """Transição masmorra→cidade reusável (saída pela escada e avanço de fase)."""
        self._cancelar_timer_turno()   # fora da masmorra não há timer de turno
        self.phase = "city"
        self._gerar_loja_pergaminhos()
        for pp in self.players.values():
            pp["moves_left"]        = pp["spd"]
            pp["action_done"]       = False
            pp["bonus_action_used"] = False
            pp["taverna_refeicoes"] = []   # refeições de balcão renovam a cada visita à cidade
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

    def _escudo_equipado(self, p):
        """True se o jogador tem um escudo na mão esquerda (off_hand)."""
        off = p.get("gear", {}).get("off_hand")
        return bool(off) and (off.get("kind") == "shield" or off.get("item_slot") == "shield")

    def _off_hand_ocupa_mao(self, p):
        """True se a mão esquerda está ocupada por algo que exige uma mão livre:
        escudo OU 2ª arma (dual-wield). Munição (flechas/virotes) não ocupa a mão."""
        off = p.get("gear", {}).get("off_hand")
        if not off:
            return False
        if off.get("kind") == "shield" or off.get("item_slot") == "shield":
            return True
        return bool(off.get("die"))   # arma secundária (adaga)

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
        if s == "ammo" or item.get("effect") == "ammo":   # flechas/virotes → off_hand
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
        if item.get("die"):   # arma sem item_slot (SHOP_WEAPONS / loot de monstros)
            return "weapon"
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
        """Equipar/trocar equipamento é AÇÃO LIVRE: sem custo de ação bônus e sem
        limite por turno (pode equipar/trocar quantas vezes quiser). A lógica de
        equipar fica em _executar_equip_from_bag (só falha por restrição de classe
        ou conflito de 2 mãos)."""
        p = self.players.get(pid)
        if not p:
            return
        if not await self._executar_equip_from_bag(pid, slot_index):
            return                                   # validação falhou (erro já enviado)
        await self.push_state()

    async def _executar_equip_from_bag(self, pid, slot_index):
        """Equipa um item do inventário no slot correto (8 slots) — lógica
        original inalterada. Retorna True se equipou; False se a validação
        falhou (erro já enviado). NÃO marca ação nem faz push_state."""
        p = self.players.get(pid)
        if not p:
            return False
        if slot_index < 0 or slot_index >= len(p["bag"]):
            await self.send_to(pid, {"type": "error", "msg": "Slot de inventário inválido."}); return False

        item = p["bag"][slot_index]
        cat  = self._slot_category_for_item(item)

        if cat == "bag":
            await self.send_to(pid, {"type": "error", "msg": "Este item é consumível — use-o durante o combate!"}); return False

        # Restrição de classe (allowed_classes)
        allowed = item.get("allowed_classes")
        if allowed and p.get("class_id") not in allowed:
            await self.send_to(pid, {"type": "error",
                "msg": f"Sua classe não pode usar {item['name']}!"}); return False

        # ── Arma de 2 mãos × escudo/2ª arma: não podem coexistir (bloquear) ──
        if cat == "weapon" and item.get("two_handed") and self._off_hand_ocupa_mao(p):
            await self.send_to(pid, {"type": "error",
                "msg": f"{item['name']} é arma de 2 mãos — desequipe o escudo ou a 2ª arma primeiro."}); return False
        if cat == "off_hand" and (item.get("kind") == "shield" or item.get("item_slot") == "shield") \
                and (p.get("weapon") or {}).get("two_handed"):
            await self.send_to(pid, {"type": "error",
                "msg": f"Você empunha uma arma de 2 mãos — desequipe-a antes de usar {item['name']}."}); return False

        # Remove do inventário antes de equipar
        p["bag"].pop(slot_index)

        if cat == "weapon":
            log = self._equip_into_slot(p, item, "weapon", "⚔️")
            # Sincroniza p["weapon"] (usado pelo combate) se o item tiver die/stat
            if item.get("die") and item.get("stat"):
                combat_fields = ("id", "name", "die", "stat", "range", "reach",
                                 "finesse", "throw_range", "categoria", "two_handed")
                p["weapon"] = {k: item[k] for k in combat_fields if k in item}
        elif cat == "off_hand":
            # Munição: empilha no mesmo tipo; senão substitui o off_hand
            if item.get("effect") == "ammo":
                off = p["gear"].get("off_hand")
                if off and off.get("effect") == "ammo" and off.get("ammo_type") == item.get("ammo_type") \
                        and off.get("ammo_count", 0) < MAX_AMMO_STACK:
                    qty = min(item.get("ammo_count", 1), MAX_AMMO_STACK - off.get("ammo_count", 0))
                    off["ammo_count"] = off.get("ammo_count", 0) + qty
                    log = f"🏹 **{p['name']}** recarregou **{item['name']}** (+{qty} → {off['ammo_count']} total)!"
                else:
                    log = self._equip_into_slot(p, item, "off_hand", "🏹")
            else:
                log = self._equip_into_slot(p, item, "off_hand", "🛡️")
        elif cat == "armor":    log = self._equip_into_slot(p, item, "armor",    "🛡️")
        elif cat == "head":     log = self._equip_into_slot(p, item, "head",     "⛑️")
        elif cat == "ring":     log = self._equip_into_pair(p, item, ("ring1","ring2"), "💍")
        else:                   log = self._equip_into_pair(p, item, ("item1","item2"), "🎒")

        if log:
            await self.gm_say(log)
        return True

    @staticmethod
    def _eh_adaga(item):
        """True se o item é uma adaga (pode ser usada como 2ª arma / dual-wield)."""
        if not item:
            return False
        iid = (item.get("id") or "").lower()
        nm  = (item.get("name") or "").lower()
        return iid.startswith("dagger") or iid == "adaga_secundaria" or "adaga" in nm

    async def handle_equip_offhand(self, pid, slot_index):
        """Equipa uma ADAGA do inventário na mão esquerda (off_hand) como 2ª arma
        (dual-wield). AÇÃO LIVRE — sem custo e sem limite por turno."""
        p = self.players.get(pid)
        if not p:
            return
        if slot_index < 0 or slot_index >= len(p["bag"]):
            await self.send_to(pid, {"type": "error", "msg": "Slot de inventário inválido."}); return

        item = p["bag"][slot_index]
        if not self._eh_adaga(item) or not item.get("die"):
            await self.send_to(pid, {"type": "error",
                "msg": "Só uma adaga pode ser empunhada como 2ª arma na mão esquerda."}); return
        # Restrição de classe (allowed_classes) — adaga não tem, mas respeita se houver
        allowed = item.get("allowed_classes")
        if allowed and p.get("class_id") not in allowed:
            await self.send_to(pid, {"type": "error",
                "msg": f"Sua classe não pode usar {item['name']}!"}); return
        # Arma de 2 mãos na mão principal impede o uso de 2ª arma (como o escudo).
        if (p.get("weapon") or {}).get("two_handed"):
            await self.send_to(pid, {"type": "error",
                "msg": "Você empunha uma arma de 2 mãos — não pode usar uma 2ª arma."}); return

        p["bag"].pop(slot_index)
        log = self._equip_into_slot(p, item, "off_hand", "🗡️")
        if log:
            await self.gm_say(log + " (2ª arma — mão esquerda)")
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

    # ── validação de slot secundário (scaffolding — ver SECUNDARIO_PERMITIDO) ────
    # NOTA: handle_equip ainda NÃO é roteado (o caminho ativo é
    # handle_equip_from_bag). Mantido verbatim conforme a especificação; usa
    # heroi_key do cliente, slot 'secundario' e gear['arma']/duasMaos — conceitos
    # que ainda não existem no modelo autoritativo do servidor.
    def _pode_equipar_secundario(self, heroi_key, item_id):
        permitidos = SECUNDARIO_PERMITIDO.get(heroi_key, [])
        return item_id in permitidos

    def handle_equip(self, player, data):
        item_id   = data.get('item_id')
        slot      = data.get('slot')
        heroi_key = player.get('key')

        if slot == 'secundario':
            if not self._pode_equipar_secundario(heroi_key, item_id):
                return {
                    'error': f'{item_id} não pode ser equipado no slot secundário por {heroi_key}'
                }

        # Verifica incompatibilidade adaga secundária + arma duas mãos
        if item_id == 'adaga_secundaria':
            arma_atual = player['gear'].get('arma', {})
            if arma_atual.get('duasMaos'):
                return {
                    'error': 'Adaga secundária incompatível com arma de duas mãos'
                }

        # Verifica incompatibilidade escudo + arma duas mãos
        if item_id in ['escudo_leve', 'escudo_pesado']:
            arma_atual = player['gear'].get('arma', {})
            if arma_atual.get('duasMaos'):
                return {
                    'error': 'Escudo incompatível com arma de duas mãos'
                }

        # Executa o equip normalmente
        # ... lógica existente de equip aqui

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

        if chest.get("key_objective"):
            self.key_chest_opened = True

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

            # Munição: tenta empilhar em off_hand ou em slot de bag do mesmo tipo
            if item.get("effect") == "ammo":
                ammo_type = item.get("ammo_type")
                qty       = item.get("ammo_count", 1)
                off = p["gear"].get("off_hand")
                if off and off.get("effect") == "ammo" and off.get("ammo_type") == ammo_type \
                        and off.get("ammo_count", 0) < MAX_AMMO_STACK:
                    add = min(qty, MAX_AMMO_STACK - off.get("ammo_count", 0))
                    off["ammo_count"] = off.get("ammo_count", 0) + add
                    chest["items"].pop(idx)
                    await self.gm_say(
                        f"🏹 **{p['name']}** recarregou **{item['name']}** do baú (+{add} → {off['ammo_count']} no slot)!")
                else:
                    existing = next(
                        (b for b in p["bag"]
                         if b.get("effect") == "ammo" and b.get("ammo_type") == ammo_type
                         and b.get("ammo_count", 0) < MAX_AMMO_STACK), None)
                    if existing:
                        add = min(qty, MAX_AMMO_STACK - existing.get("ammo_count", 0))
                        existing["ammo_count"] = existing.get("ammo_count", 0) + add
                        chest["items"].pop(idx)
                        await self.gm_say(
                            f"📦 **{p['name']}** guardou **{item['name']}** na bolsa ({existing['ammo_count']} total)!")
                    else:
                        result = self._add_to_inventory(p, item)
                        if result == "full":
                            await self.send_to(pid, {"type": "error", "msg": "Inventário cheio!"}); return
                        chest["items"].pop(idx)
                        await self.gm_say(
                            f"📦 **{p['name']}** pegou **{item['emoji']} {item['name']}** do baú!")
            else:
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

    # ── Ação Bônus ─────────────────────────────────────────────────────────────
    # Efeitos de item que contam como ação bônus (máx. 1 por turno).
    BONUS_ACTION_EFFECTS = {"heal", "mana", "atk_bonus", "antidote", "coat_poison", "veil_shadow"}

    def _consumir_recursos(self, player, tipo_acao):
        """Consumo CENTRAL de fome/sede (escala 0–10). Substitui os consumos
        hardcoded espalhados pelo servidor — toda ação consome pela mesma tabela
        (CONSUMO_ACOES). NÃO aplica thresholds/colapso/morte ainda."""
        custo = CONSUMO_ACOES.get(tipo_acao, {'fome': 0, 'sede': 0})
        extra = self._doenca_custo_extra(player)   # sintoma médio: +1 fome/sede por ação
        player['fome'] = max(0, player.get('fome', SOBREVIVENCIA_MAX) - custo['fome'] - extra)
        player['sede'] = max(0, player.get('sede', SOBREVIVENCIA_MAX) - custo['sede'] - extra)
        self._verificar_estado_sobrevivencia(player)

    def _verificar_estado_sobrevivencia(self, player):
        """Placeholder — a lógica de estado (thresholds/colapso/morte) será
        adicionada depois. Por ora não altera a lógica de jogo."""
        pass

    def _penalidade_sobrevivencia(self, p):
        """Penalidade: -1 se fome < 20, -1 se sede < 20 (somam → até -2). 0 se ambos ≥ 20."""
        pen = 0
        if p.get("fome", 100) < 20: pen += 1
        if p.get("sede", 100) < 20: pen += 1
        return pen

    # ── Sistema de doenças ──────────────────────────────────────────────────────
    def _doenca_mov_pen(self, p):
        """Penalidade de movimento por sintomas leves (somada em _moves_base)."""
        d = p.get("doenca")
        return -d.get("mov_pen", 0) if (p.get("doente") and d) else 0

    def _doenca_custo_extra(self, p):
        """+fome/+sede por ação (e por mover) do sintoma médio."""
        d = p.get("doenca")
        return d.get("custo_extra", 0) if (p.get("doente") and d) else 0

    def _aplicar_sintoma_tier(self, p, tier):
        """Aplica o PACOTE de um nível de sintoma, registrando os deltas reais
        (revertidos na cura). mov_pen/custo_extra são parâmetros próprios da doença."""
        d = p["doenca"]; deltas = d["deltas"]
        def aj(campo, x):
            if x:
                p[campo] = p.get(campo, 0) + x
                deltas[campo] = deltas.get(campo, 0) + x
        if tier == "leve":
            aj("ref_", -1); aj("fort", -1); d["mov_pen"] += 1
        elif tier == "medio":
            aj("str_", -2); aj("dex", -2)
            aj("ac", -1); aj("ref_", -1)        # -2 DES → -1 mod (CA e Reflexos)
            d["custo_extra"] += 1
        elif tier == "grave":
            antes = p.get("con_", 10)
            aj("con_", -2)
            fort_delta = get_bonus_constituicao(antes) - get_bonus_constituicao(max(0, antes - 2))
            hp_delta   = max(0, fort_delta * p.get("level", 1))
            aj("fort", -fort_delta); aj("max_hp", -hp_delta)
            p["hp"] = min(p.get("hp", 1), p.get("max_hp", 1))
            aj("int_", -2); aj("will", -1)      # -2 INT → -1 mod (Vontade)

    async def _aplicar_doenca(self, p, severidade="leve"):
        """Aplica/agrava uma doença no jogador. 'fonte define o nível': uma fonte
        mais forte sobe a severidade; igual/menor não piora. Retorna True se mudou."""
        if not self._eh_jogador(p):
            return False
        novos = DOENCA_SEVERIDADE.get(severidade, ["leve"])
        d = p.get("doenca") if p.get("doente") else None
        atuais = d["sintomas"] if d else []
        alvo_tiers = novos if len(novos) > len(atuais) else atuais
        faltam = [t for t in alvo_tiers if t not in atuais]
        if not faltam:
            return False
        if not d:
            d = p["doenca"] = {"sintomas": [], "deltas": {}, "mov_pen": 0, "custo_extra": 0}
            p["doente"] = True
        for tier in faltam:
            self._aplicar_sintoma_tier(p, tier)
            d["sintomas"].append(tier)
        d["severidade"] = DOENCA_NIVEL_NOME[len(d["sintomas"]) - 1]
        p["doenca_tipo"] = d["severidade"]
        sint = ", ".join(DOENCA_SINTOMA_DESC[t] for t in d["sintomas"])
        await self.gm_say(
            f"🦠 **{p['name']}** contrai uma **Doença {d['severidade'].capitalize()}**! "
            f"Sintomas: {sint}. (curável por clérigo ou templo)")
        return True

    def _curar_doenca(self, p):
        """Remove a doença inteira, revertendo todos os deltas. Retorna True se curou."""
        d = p.get("doenca")
        if not d and not p.get("doente"):
            return False
        for campo, x in (d or {}).get("deltas", {}).items():
            p[campo] = p.get(campo, 0) - x
        p["hp"] = min(p.get("hp", 1), p.get("max_hp", 1))
        p["doente"] = False
        p.pop("doenca", None)
        p.pop("doenca_tipo", None)
        return True

    def _modificador_sobrevivencia(self, p):
        """Modificador líquido aplicado a TODOS os acertos, testes de resistência e
        dano do jogador:
          +1 (SACIADO) se fome > 80 E sede > 80;
          menos a penalidade de exaustão (-1 por fome/sede < 20).
        Faixa neutra (20–80, ou só um acima de 80) = 0."""
        bonus = 1 if (p.get("fome", 100) > 80 and p.get("sede", 100) > 80) else 0
        return bonus - self._penalidade_sobrevivencia(p)

    async def _executar_acao_bonus(self, p):
        """Valida e consome a ação bônus do jogador neste turno.
        Retorna True se permitida; False (com mensagem) se já usada.
        Consumo via tabela central (_consumir_recursos, 'acao_bonus').
        """
        if p.get("bonus_action_used"):
            await self.gm_say(f"⚠️ **{p['name']}** já usou sua ação bônus neste turno.")
            return False

        p["bonus_action_used"] = True
        self._consumir_recursos(p, 'acao_bonus')
        await self.gm_say(
            f"🎯 **{p['name']}** usou ação bônus! "
            f"🍖 Fome: {p['fome']:.1f}/10 | 💧 Sede: {p['sede']:.1f}/10"
        )
        return True

    # ── VENENOS ─────────────────────────────────────────────────────────────
    # Sistema central de venenos. Aplica/processa/expira efeitos em QUALQUER
    # alvo (jogador ou monstro). Ver VENENOS (catálogo) e CLAUDE.md/VISUAL_CONTRACT.

    # ══════════════════════════════════════════════════════════════════════════
    # SISTEMA DE MAGIAS (GRIMÓRIO) — FUNDAÇÃO
    # Pedro (mage) e Lewis (cleric) lançam via mensagem WS 'magia'. Esta fundação
    # entrega: roteamento (handle_magia), cobrança de custo (MP do círculo +
    # 🍖/💧), o dispatcher (_executar_magia_grimorio) e o sistema de zonas/
    # escuridão. A lógica de cada magia entra nos próximos prompts — por ora só
    # GRIMORIO_IMPLEMENTADAS são conjuráveis.
    # ══════════════════════════════════════════════════════════════════════════

    async def handle_magia(self, pid, data):
        """Lança uma magia do GRIMÓRIO (Pedro/mage, Lewis/cleric). Valida classe,
        elegibilidade, MP e custo de sobrevivência; depois despacha o efeito."""
        if not self._is_turn(pid):
            return
        p = self.players.get(pid)
        if not p or not p["alive"]:
            return
        # MODO TESTE: Pedro lança qualquer magia ignorando classe/nível/custo/ação.
        livre = MAGE_TESTE_LIVRE and p.get("class_id") == "mage"
        if p.get("class_id") not in ("mage", "cleric"):
            await self.send_to(pid, {"type": "error", "msg": "Sua classe não lança magias do grimório."}); return
        if p.get("petrificado"):
            await self.send_to(pid, {"type": "error", "msg": "🗿 Você está petrificado e não pode lançar magias!"}); return
        if p.get("paralisado"):
            await self.send_to(pid, {"type": "error", "msg": "❄️ Você está paralisado e não pode lançar magias!"}); return
        if p.get("dormindo"):
            await self.send_to(pid, {"type": "error", "msg": "🌙 Você está dormindo e não pode lançar magias!"}); return
        if self._em_silencio(p):
            await self.send_to(pid, {"type": "error", "msg": "🔇 Você está numa área de Silêncio e não pode lançar magias!"}); return

        # ── Metamagia do mago (Pedro): Reflexa / Acelerar ─────────────────────
        is_mage = p.get("class_id") == "mage"

        # Ação principal (1 por turno).
        if self._acao_bloqueada(p) and not livre:
            await self.send_to(pid, {"type": "error", "msg": "Ação principal já usada neste turno."}); return

        magia_id = (data or {}).get("magia_id")
        magia = GRIMORIO.get(magia_id)
        if not magia:
            await self.send_to(pid, {"type": "error", "msg": "Magia desconhecida."}); return
        if p["class_id"] not in magia.get("classe", []) and not livre:
            await self.send_to(pid, {"type": "error", "msg": f"{p['name']} não pode lançar {magia['nome']}."}); return
        if magia_id not in GRIMORIO_IMPLEMENTADAS:
            await self.send_to(pid, {"type": "error",
                "msg": f"{magia['icone']} {magia['nome']} ainda está em desenvolvimento."}); return

        # Custo do círculo: Lewis (cleric) gasta SLOTS de magia; as demais classes, MP.
        circulo = magia.get("circulo", "primeiro")
        is_cleric = p.get("class_id") == "cleric"
        custo_mp = CIRCULO_MP.get(circulo, 1)
        if livre:
            pass   # MODO TESTE: sem checagem de slot/MP/nível
        elif is_cleric:
            p.setdefault("magias_usadas_hoje", {"primeiro": 0, "segundo": 0, "terceiro": 0})
            limite = CLERIC_SLOTS.get(circulo, 0)
            if p["magias_usadas_hoje"].get(circulo, 0) >= limite:
                await self.send_to(pid, {"type": "error",
                    "msg": f"Sem slots de magia de {circulo} círculo."}); return
        elif p.get("mp", 0) < custo_mp:
            await self.send_to(pid, {"type": "error", "msg": f"MP insuficiente — precisa {custo_mp}."}); return

        # ── Metamagia (Pedro): Aprimorar (+1 CD do save) / Estender (+1 turno) /
        # Fortalecer (dano ×1,5). EMPILHÁVEIS; o custo em 🍖/💧 é pago AGORA e SÓ se
        # a habilidade tiver efeito nesta magia (tem dano / duração / teste). ─────
        dmg_mult, dur_bonus, dc_bonus = 1, 0, 0
        if is_mage:
            tem_dano    = self._magia_tem_dano(magia)
            tem_duracao = "duracao" in magia
            tem_save    = "save" in magia
            mm_fome = mm_sede = 0
            partes = []
            if p.get("fortalecer_ativo") and tem_dano:
                dmg_mult = 1.5; mm_fome += 6; mm_sede += 6; partes.append("Fortalecer (dano ×1,5)")
            if p.get("estender_ativo") and tem_duracao:
                dur_bonus = 1; mm_fome += 3; mm_sede += 3; partes.append("Estender (+1 turno)")
            if p.get("aprimorar_ativo") and tem_save:
                dc_bonus = 1; mm_fome += 3; partes.append("Aprimorar (+1 CD)")
            if (mm_fome or mm_sede) and not livre:
                if p["fome"] < mm_fome or p["sede"] < mm_sede:
                    await self.send_to(pid, {"type": "error",
                        "msg": f"Recursos insuficientes p/ metamagia 🍖-{mm_fome} 💧-{mm_sede}."}); return
                p["fome"] = max(0, p["fome"] - mm_fome)
                p["sede"] = max(0, p["sede"] - mm_sede)
            if partes:
                custo_txt = (f" | 🍖-{mm_fome}" + (f" 💧-{mm_sede}" if mm_sede else "")) if (mm_fome or mm_sede) else ""
                await self.gm_say(f"🔮 **{p['name']}** — metamagia: {', '.join(partes)}{custo_txt}.")

        # Custo do círculo (slot p/ Lewis, MP p/ os demais) + 🍖/💧 de sobrevivência.
        if not livre:
            if is_cleric:
                p["magias_usadas_hoje"][circulo] = p["magias_usadas_hoje"].get(circulo, 0) + 1
            else:
                p["mp"] = max(0, p["mp"] - custo_mp)
            p["fome"] = max(0, p.get("fome", 10) - 1)
            p["sede"] = max(0, p.get("sede", 10) - 1)
            self._verificar_estado_sobrevivencia(p)

        # Aprimorar: +1 na CD do save é lido por _dif_magia via flag temporária no caster.
        p["_mm_dc_bonus"] = dc_bonus
        await self._executar_magia_grimorio(p, magia, data or {}, dmg_mult, dur_bonus)
        p["_mm_dc_bonus"] = 0

        # Invisibilidade quebra ao lançar (a menos que a própria magia a tenha concedido agora).
        if p.get("invisivel_magico") and magia_id != "invisibilidade":
            p["invisivel_magico"] = False; p.pop("invisivel_magico_rodadas", None)
            await self.gm_say(f"🫥 **{p['name']}** revela-se ao lançar magia.")

        if not livre:                      # MODO TESTE: não consome a ação do turno
            p["action_done"] = True
        await self.push_state()

    def _magia_tem_dano(self, magia):
        """True se a magia causa dano (alguma chave 'dano…' ou id de magia de dano)."""
        if any(str(k).startswith("dano") for k in magia.keys()):
            return True
        return magia.get("id") in ("bola_fogo", "relampago", "raio_congelante", "raio_divino", "jato_ar")

    async def _executar_magia_grimorio(self, caster, magia, data, dmg_mult=1, dur_bonus=0):
        """Despacha a execução de uma magia já paga. FUNDAÇÃO: implementa o sistema
        de escuridão/visão; as demais recaem em _magia_nao_implementada."""
        mid       = magia["id"]
        nivel     = caster.get("level", 1)            # noqa: F841 — usado pelas magias futuras
        bonus_int = mod(caster.get("int_", 10))       # noqa: F841 — idem

        # ── Magias de dano de Pedro (revisadas) ─────────────────────────────────
        if mid == "bola_fogo":
            await self._executar_bola_fogo(caster, magia, data, dmg_mult, dur_bonus)

        elif mid == "relampago":
            await self._executar_relampago(caster, magia, data, dmg_mult)

        elif mid == "raio_congelante":
            await self._executar_raio_congelante(caster, magia, data, dmg_mult, dur_bonus)

        # ── Batch 1: utilidades, dano direto ────────────────────────────────────
        elif mid == "saciar":
            await self._executar_saciar(caster, magia, data)
        elif mid == "criar_alimentos":
            await self._executar_criar_alimentos(caster, magia)
        elif mid == "clarividencia":
            await self._executar_clarividencia(caster, magia, data)
        elif mid == "raio_divino":
            await self._executar_raio_divino(caster, magia, data, dmg_mult)

        # ── Batch 1b: buffs/debuffs de combate ──────────────────────────────────
        elif mid == "abencoar":
            await self._executar_abencoar(caster, magia, dur_bonus)
        elif mid == "amaldicoar":
            await self._executar_amaldicoar(caster, magia, data, dur_bonus)
        elif mid == "abencoar_arma":
            await self._executar_abencoar_arma(caster, magia, data, dur_bonus)

        # ── Batch 2: status/controle (disrupção simples da IA do monstro) ───────
        elif mid == "sono":
            await self._executar_sono(caster, magia, data, dur_bonus)
        elif mid == "medo":
            await self._executar_medo(caster, magia, data, dur_bonus)
        elif mid == "comando":
            await self._executar_comando(caster, magia, data)
        elif mid == "dominar_mente":
            await self._executar_dominar_mente(caster, magia, data, dur_bonus)
        elif mid == "dominar_morto_vivo":
            await self._executar_dominar_morto_vivo(caster, magia, data)
        elif mid == "lentidao":
            await self._executar_lentidao(caster, magia, data, dur_bonus)

        # ── Batch 3: buffs sustentados ──────────────────────────────────────────
        elif mid == "invisibilidade":
            await self._executar_invisibilidade(caster, magia, dur_bonus)
        elif mid == "regeneracao_magica":
            await self._executar_regeneracao(caster, magia, data)
        elif mid == "jato_ar":
            await self._executar_jato_ar(caster, magia, data, dmg_mult)
        elif mid == "velocidade":
            await self._executar_velocidade(caster, magia, dur_bonus)
        elif mid == "protecao_energia":
            await self._executar_protecao_energia(caster, magia, dur_bonus)
        elif mid == "conjurar_elemental":
            await self._executar_conjurar_elemental(caster, magia, data)
        elif mid == "silencio":
            await self._executar_silencio(caster, magia, data, dur_bonus)
        elif mid == "barreira_arcana":
            await self._executar_barreira_arcana(caster, magia)
        elif mid == "contramagica":
            await self._executar_contramagica(caster, magia)

        # ── Manto de Escuridão: cria zona de escuridão centrada no caster ───────
        elif mid == "manto_escuridao":
            dur = self._rolar_dado(magia.get("duracao", "1d4")) + dur_bonus
            await self._aplicar_escuridao(caster, raio=magia.get("area_raio", 3), duracao=dur)

        # ── Visão no Escuro: concede a um aliado (ou ao caster) visão noturna ───
        elif mid == "visao_escuro":
            alvo = self.players.get(data.get("target_id")) or caster
            if not alvo.get("alive"):
                await self.send_to(caster["id"], {"type": "error", "msg": "Aliado inválido."}); return
            dur = self._rolar_dado(magia.get("duracao", "1d6+2")) + dur_bonus
            alvo["visao_escuro"]         = True
            alvo["visao_escuro_rodadas"] = dur
            await self.gm_say(f"👁️ **{alvo['name']}** recebe Visão no Escuro por {dur} rodada(s).")

        else:
            await self._magia_nao_implementada(caster, magia)

    async def _magia_nao_implementada(self, caster, magia):
        await self.gm_say(
            f"📖 **{caster['name']}** prepara **{magia['nome']}** {magia.get('icone','')}, "
            f"mas seus efeitos ainda não foram conjurados (em desenvolvimento).")

    def _eh_morto_vivo_ou_demonio(self, alvo):
        if self._eh_jogador(alvo):
            return False
        t = (alvo.get("type") or alvo.get("tipo") or "").lower()
        return bool(alvo.get("undead")) or t in (
            "skeleton", "undead", "zombie", "ghost", "wraith", "lich",
            "demon", "demonio", "devil")

    # ── Modificadores mágicos de combate (Abençoar/Amaldiçoar/Abençoar Arma) ─────
    # Vivem em alvo["mods_magia"] = {ataque,dano,ca,resistencia,rodadas}. Lidos no
    # ataque do jogador, no ataque do monstro e em _testar_save; expiram por rodada.
    def _mod_magia(self, alvo, chave):
        m = alvo.get("mods_magia")
        return m.get(chave, 0) if m else 0

    def _set_mod_magia(self, alvo, deltas, rodadas):
        cur = alvo.get("mods_magia") or {}
        for k, v in deltas.items():
            cur[k] = v                                   # define (não acumula)
        cur["rodadas"] = max(cur.get("rodadas", 0), rodadas)
        alvo["mods_magia"] = cur

    async def _processar_mods_magia_turno(self, alvo):
        m = alvo.get("mods_magia")
        if not m:
            return
        m["rodadas"] = m.get("rodadas", 0) - 1
        if m["rodadas"] <= 0:
            alvo.pop("mods_magia", None)
            await self.gm_say(f"✨ Os efeitos mágicos em **{alvo.get('name','alvo')}** se dissipam.")

    # ── Batch 1: utilidades e dano direto ───────────────────────────────────────
    async def _executar_saciar(self, caster, magia, data):
        """Toque: +fome/+sede num aliado adjacente."""
        alvo = self.players.get((data or {}).get("target_id"))
        if not alvo or not alvo["alive"]:
            await self.send_to(caster["id"], {"type": "error", "msg": "Aliado inválido."}); return
        dist = max(abs(caster["pos"][0]-alvo["pos"][0]), abs(caster["pos"][1]-alvo["pos"][1]))
        if dist > magia.get("alcance", 1):
            await self.send_to(caster["id"], {"type": "error", "msg": "O aliado precisa estar adjacente."}); return
        fb, sb = magia.get("fome_bonus", 10), magia.get("sede_bonus", 10)
        alvo["fome"] = min(100, alvo.get("fome", 0) + fb)
        alvo["sede"] = min(100, alvo.get("sede", 0) + sb)
        self._verificar_estado_sobrevivencia(alvo)
        await self.gm_say(f"💧 **{caster['name']}** sacia **{alvo['name']}** (+{fb} fome, +{sb} sede).")

    async def _executar_criar_alimentos(self, caster, magia):
        """Cria comida/água e distribui a todos os aliados vivos."""
        agua = self._rolar_dado(magia.get("agua", "1d6+1"))
        pao  = self._rolar_dado(magia.get("pao", "1d6+2"))
        n = 0
        for p in self.players.values():
            if not p["alive"]: continue
            p["fome"] = min(100, p.get("fome", 0) + pao)
            p["sede"] = min(100, p.get("sede", 0) + agua)
            self._verificar_estado_sobrevivencia(p)
            n += 1
        await self.gm_say(f"🍞 **{caster['name']}** cria alimentos: +{pao} fome e +{agua} sede para {n} aliado(s).")

    async def _executar_clarividencia(self, caster, magia, data):
        """Olho mágico que enxerga QUALQUER ponto do mapa — sem limite de alcance
        e atravessando paredes e portas fechadas. Revela a névoa da área alvo,
        mostra os monstros que estiverem ali (visibilidade ao vivo temporária) e
        expõe as armadilhas do local. Se a mira tocar uma sala (mesmo trancada),
        revela o interior inteiro dela. NÃO abre portas nem desperta criaturas."""
        nivel  = caster.get("level", 1)
        escala = {1: 4, 2: 4, 3: 6, 4: 6, 5: 8}.get(min(nivel, 5), 4)
        raio   = max(1, escala // 2)
        tx = int((data or {}).get("tx", caster["pos"][0]))
        ty = int((data or {}).get("ty", caster["pos"][1]))
        dur    = magia.get("duracao", 2)
        expira = self.round_num + dur
        antes  = len(self.explored)
        reveladas = set()   # tiles que esta conjuração revelou (p/ achar monstros/armadilhas)

        def _revelar(x, y):
            if 0 <= x < self.map_w and 0 <= y < self.map_h:
                self.explored.add((x, y))
                self.magic_reveal[(x, y)] = expira   # visibilidade ao vivo (monstros) temporária
                reveladas.add((x, y))

        # Área quadrada centrada no alvo (revela mesmo o interior de salas trancadas)
        for dy in range(-raio, raio + 1):
            for dx in range(-raio, raio + 1):
                _revelar(tx + dx, ty + dy)

        # Se a mira tocar uma sala (trancada ou não) — pela área ou perto da
        # porta — revela a sala inteira (todo o conteúdo).
        salas_reveladas = 0
        for r in self.rooms:
            toca = room_contains(r, tx, ty) or any(
                max(abs(d[0] - tx), abs(d[1] - ty)) <= raio for d in r.get("doors", []))
            if not toca:
                continue
            if r.get("locked"):
                salas_reveladas += 1
            for ry in range(max(0, r["y"] - 1), min(self.map_h, r["y"] + r["h"] + 1)):
                for rx in range(max(0, r["x"] - 1), min(self.map_w, r["x"] + r["w"] + 1)):
                    _revelar(rx, ry)

        # Conta monstros à vista na área revelada (já visíveis via magic_reveal).
        monstros = sum(1 for m in self.monsters.values()
                       if m["hp"] > 0 and tuple(m["pos"]) in reveladas)

        # Expõe armadilhas no local: as de masmorra (self.traps) já aparecem por
        # estarem em `explored`; as colocáveis ocultas (self.armadilhas) passam a
        # ser visíveis para os jogadores.
        traps_mascara = sum(1 for t in self.traps
                            if not t.get("triggered") and tuple(t["pos"]) in reveladas)
        for a in self.armadilhas:
            if a.get("esgotada"):
                continue
            if tuple(a["pos"]) in reveladas and not a.get("visivel"):
                a["visivel"] = True
                traps_mascara += 1

        novos = len(self.explored) - antes
        partes = [f"{novos} casa(s) reveladas"]
        if monstros:        partes.append(f"{monstros} monstro(s) à vista")
        if traps_mascara:   partes.append(f"{traps_mascara} armadilha(s) detectada(s)")
        if salas_reveladas: partes.append("interior de sala trancada exposto")
        await self.gm_say(
            f"🔮 **{caster['name']}** lança Clarividência — " + ", ".join(partes) +
            f" ({dur} rodada(s)).")

    async def _executar_raio_divino(self, caster, magia, data, dmg_mult):
        """1d6+1 por nível; Reflexos = metade; dobrado vs mortos-vivos/demônios."""
        nivel     = caster.get("level", 1)
        bonus_int = mod(caster.get("int_", 10))
        alcance   = magia.get("alcance", 6)
        alvo_id   = (data or {}).get("target_id")
        alvo = self.players.get(alvo_id) or next(
            (m for m in self.monsters.values() if m.get("id") == alvo_id), None)
        vivo = alvo and (alvo["alive"] if self._eh_jogador(alvo) else alvo["hp"] > 0)
        if not vivo:
            await self.send_to(caster["id"], {"type": "error", "msg": "Alvo inválido."}); return
        dist = max(abs(caster["pos"][0]-alvo["pos"][0]), abs(caster["pos"][1]-alvo["pos"][1]))
        if dist > alcance:
            await self.send_to(caster["id"], {"type": "error", "msg": f"Alvo fora do alcance ({dist} > {alcance})."}); return

        dano = int((((await self._rolar_dano_mostrado(nivel, 6, "✨ Dano")) + nivel) * dmg_mult) + 0.5)
        save_ok, *_ = await self._save_mostrado(alvo, "reflexos", self._dif_magia(caster, magia))
        if save_ok:
            dano //= 2
        if self._eh_morto_vivo_ou_demonio(alvo):
            dano *= 2
            await self.gm_say(f"✨ Raio Divino DOBRADO contra **{alvo['name']}** (morto-vivo/demônio)!")
        alvo["hp"] = max(0, alvo["hp"] - dano)
        await self.gm_say(f"✨ **{caster['name']}** atinge **{alvo['name']}** com Raio Divino: {dano} de dano sagrado.")
        if alvo["hp"] <= 0:
            if self._eh_jogador(alvo):
                await self._player_dies(alvo["id"])
            else:
                await self._monster_dies(alvo, caster["id"])

    # ── Batch 1b: buffs/debuffs de combate (usam mods_magia) ─────────────────────
    async def _executar_abencoar(self, caster, magia, dur_bonus):
        """Área centrada no caster: +1 ataque/dano/CA/resistência aos aliados no raio."""
        dur  = self._rolar_dado(magia.get("duracao", "1d4+1")) + dur_bonus
        raio = magia.get("area_raio", 3)
        buff = magia.get("buff", {"ataque": 1, "dano": 1, "ca": 1, "resistencia": 1})
        cx, cy = caster["pos"]
        n = 0
        for p in self.players.values():
            if not p["alive"]: continue
            if max(abs(p["pos"][0]-cx), abs(p["pos"][1]-cy)) > raio: continue
            self._set_mod_magia(p, buff, dur)
            n += 1
        await self.gm_say(f"✨ **{caster['name']}** abençoa {n} aliado(s): +1 ataque/dano/CA/resistência por {dur} rodada(s).")

    async def _executar_amaldicoar(self, caster, magia, data, dur_bonus):
        """Área centrada na casa escolhida: -1 ataque/dano/CA/resistência aos inimigos no raio."""
        dur    = self._rolar_dado(magia.get("duracao", "1d4+1")) + dur_bonus
        raio   = magia.get("area_raio", 1)
        debuff = magia.get("debuff", {"ataque": -1, "dano": -1, "ca": -1, "resistencia": -1})
        tx = int((data or {}).get("tx", caster["pos"][0]))
        ty = int((data or {}).get("ty", caster["pos"][1]))
        if not await self._checar_alcance_centro(caster, magia, tx, ty): return
        n = 0
        for alvo in self._alvos_na_area(tx, ty, raio):
            self._set_mod_magia(alvo, debuff, dur)
            n += 1
        await self.gm_say(f"☠️ **{caster['name']}** amaldiçoa {n} alvo(s): -1 ataque/dano/CA/resistência por {dur} rodada(s) (afeta aliados/minions).")

    async def _executar_abencoar_arma(self, caster, magia, data, dur_bonus):
        """Aliado à distância: +1 ataque e dano na arma por algumas rodadas."""
        alvo = self.players.get((data or {}).get("target_id"))
        if not alvo or not alvo["alive"]:
            await self.send_to(caster["id"], {"type": "error", "msg": "Aliado inválido."}); return
        dist = max(abs(caster["pos"][0]-alvo["pos"][0]), abs(caster["pos"][1]-alvo["pos"][1]))
        if dist > magia.get("alcance", 6):
            await self.send_to(caster["id"], {"type": "error", "msg": "Aliado fora do alcance."}); return
        dur  = self._rolar_dado(magia.get("duracao", "1d6+2")) + dur_bonus
        buff = magia.get("buff", {"ataque": 1, "dano": 1})
        self._set_mod_magia(alvo, buff, dur)
        await self.gm_say(f"⚔️ **{caster['name']}** abençoa a arma de **{alvo['name']}**: +1 ataque/dano por {dur} rodada(s).")

    # ── Batch 2: helpers de movimento e status de monstro ───────────────────────
    def _passo_livre(self, m, nx, ny):
        """True se o monstro m pode pisar em (nx,ny) — footprint multi-tile inteiro
        livre de parede/porta fechada e de qualquer outra entidade viva."""
        return self._monster_can_occupy(m, nx, ny)

    def _passo_monstro(self, m, tx, ty, away=False):
        """Move m um passo cardinal em direção a (tx,ty) — ou para longe, se away."""
        sx = 0 if m["pos"][0] == tx else (1 if tx > m["pos"][0] else -1)
        sy = 0 if m["pos"][1] == ty else (1 if ty > m["pos"][1] else -1)
        if away:
            sx, sy = -sx, -sy
        for adx, ady in [(sx, 0), (0, sy)]:
            if adx == 0 and ady == 0:
                continue
            nx, ny = m["pos"][0] + adx, m["pos"][1] + ady
            if self._passo_livre(m, nx, ny):
                m["pos"] = [nx, ny]
                return True
        return False

    async def _fugir_monstro(self, m):
        vivos = [p for p in self.players.values() if p["alive"]]
        if not vivos:
            return
        alvo = min(vivos, key=lambda p: abs(p["pos"][0]-m["pos"][0]) + abs(p["pos"][1]-m["pos"][1]))
        moveu = self._passo_monstro(m, alvo["pos"][0], alvo["pos"][1], away=True)
        await self.gm_say(f"😱 **{m['name']}** está apavorado e foge" + ("!" if moveu else " (encurralado)!"))

    async def _acao_dominado(self, m, alive_monsters):
        """Monstro dominado age como aliado: ataca/avança contra o monstro mais próximo."""
        outros = [o for o in alive_monsters if o["id"] != m["id"] and o["hp"] > 0 and not o.get("dominado")]
        if not outros:
            await self.gm_say(f"🧠 **{m['name']}** (dominado) não encontra outro inimigo.")
            return
        alvo = min(outros, key=lambda o: abs(o["pos"][0]-m["pos"][0]) + abs(o["pos"][1]-m["pos"][1]))
        if self._cardinal_adjacent(m["pos"], alvo["pos"]):
            m_atk = m["atk_bonus"] + self._pen(m, "ataque") + self._mod_magia(m, "ataque")
            hit, roll, total, crit = d20_attack(m_atk, alvo["ac"] + self._mod_magia(alvo, "ca"))
            await self.broadcast({"type": "dice_roll", "die": "d20", "value": roll,
                                  "label": f"{m['name']} (dominado)", "hit": hit, "crit": crit})
            if hit:
                raw = roll_dice(m["damage"])
                if crit: raw *= 2
                dmg = max(1, raw + self._pen(m, "dano") + self._mod_magia(m, "dano"))
                alvo["hp"] = max(0, alvo["hp"] - dmg)
                await self.gm_say(f"🧠 **{m['name']}** (dominado) ataca **{alvo['name']}**: {dmg} de dano!")
                if alvo["hp"] <= 0:
                    await self._monster_dies(alvo, m.get("dominado_por", ""))
            else:
                await self.gm_say(f"🧠 **{m['name']}** (dominado) ataca **{alvo['name']}** e erra!")
        else:
            self._passo_monstro(m, alvo["pos"][0], alvo["pos"][1])
            await self.gm_say(f"🧠 **{m['name']}** (dominado) avança contra **{alvo['name']}**.")

    async def _processar_status_jogador_turno(self, p):
        """Tica status de controle (de magias em área) no início do turno do JOGADOR.
        Sono bloqueia as ações (ver guardas em handle_move/attack/magia); Medo/Lentidão
        já aplicam -1 via mods_magia. Aqui só expiram os contadores."""
        for flag, rod, nome in (("dormindo", "dormindo_rodadas", "Sono"),
                                 ("com_medo", "medo_rodadas", "Medo"),
                                 ("lento", "lento_rodadas", "Lentidão")):
            if p.get(flag):
                p[rod] = p.get(rod, 1) - 1
                if p[rod] <= 0:
                    p.pop(flag, None); p.pop(rod, None)
                    await self.gm_say(f"✨ **{p['name']}** se livra de {nome}.")
        if p.get("dormindo"):
            await self.gm_say(f"🌙 **{p['name']}** está dormindo — não pode agir neste turno.")

    async def _status_monstro_turno(self, m, alive_monsters):
        """Resolve status de controle no turno do monstro. Retorna 'pulou' se o
        turno foi consumido pelo status (não deve agir normalmente)."""
        # Sono: dorme e perde o turno; expira no início do turno em que zera.
        if m.get("dormindo"):
            if m.get("dormindo_rodadas", 0) <= 0:
                m.pop("dormindo", None); m.pop("dormindo_rodadas", None)
                await self.gm_say(f"🌙 **{m['name']}** desperta.")
                return None
            m["dormindo_rodadas"] -= 1
            await self.gm_say(f"🌙 **{m['name']}** está dormindo e perde o turno.")
            return "pulou"
        # Comando: perde o turno uma vez.
        if m.get("comandado"):
            m.pop("comandado", None)
            await self.gm_say(f"🗣️ **{m['name']}** está sob Comando e perde a ação.")
            return "pulou"
        # Dominado: age contra os próprios aliados.
        if m.get("dominado"):
            if not m.get("dominado_permanente"):
                if m.get("dominado_rodadas", 0) <= 0:
                    m.pop("dominado", None); m.pop("dominado_rodadas", None); m.pop("dominado_por", None)
                    await self.gm_say(f"🧠 **{m['name']}** se liberta do domínio.")
                    return None
                m["dominado_rodadas"] -= 1
            await self._acao_dominado(m, alive_monsters)
            return "pulou"
        # Medo: foge do jogador mais próximo, sem atacar.
        if m.get("com_medo"):
            if m.get("medo_rodadas", 0) <= 0:
                m.pop("com_medo", None); m.pop("medo_rodadas", None)
                await self.gm_say(f"😱 **{m['name']}** recupera a coragem.")
                return None
            m["medo_rodadas"] -= 1
            await self._fugir_monstro(m)
            return "pulou"
        # Lentidão: age em rodadas alternadas (perde metade dos turnos).
        if m.get("lento"):
            if m.get("lento_rodadas", 0) <= 0:
                m.pop("lento", None); m.pop("lento_rodadas", None); m.pop("lento_pulou", None)
            else:
                m["lento_rodadas"] -= 1
                m["lento_pulou"] = not m.get("lento_pulou", False)
                if m["lento_pulou"]:
                    await self.gm_say(f"🐌 **{m['name']}** está lento e perde o turno.")
                    return "pulou"
        return None

    # ── Batch 2: magias de status ───────────────────────────────────────────────
    def _monstros_na_area(self, tx, ty, raio):
        return [m for m in self.monsters.values()
                if m["hp"] > 0 and self._na_area(m, tx, ty, raio)]

    def _na_area(self, obj, tx, ty, raio):
        # Dentro do raio (Chebyshev) E com linha de visão a partir do centro da
        # área — paredes/portas fechadas fazem sombra: quem está atrás não é
        # atingido pela magia/explosão.
        if max(abs(obj["pos"][0]-tx), abs(obj["pos"][1]-ty)) > raio:
            return False
        return self._tem_linha_de_visao([tx, ty], obj["pos"])

    def _alvos_na_area(self, tx, ty, raio):
        """TODOS os vivos na área (monstros + jogadores + animados/minions) — magias
        de área não discriminam aliados, minions ou inimigos. Paredes bloqueiam:
        só é atingido quem tem linha de visão a partir do centro da área."""
        out = [m for m in self.monsters.values() if m["hp"] > 0 and self._na_area(m, tx, ty, raio)]
        out += [p for p in self.players.values() if p["alive"] and self._na_area(p, tx, ty, raio)]
        out += [a for a in self._all_animados() if self._na_area(a, tx, ty, raio)]
        return out

    def _vivo(self, alvo):
        """HP atual do alvo (jogador/monstro usa 'hp'; animado usa 'vida_atual')."""
        return alvo.get("vida_atual", alvo.get("hp", 0)) > 0

    async def _aplicar_dano_alvo(self, alvo, dano, elemento, killer_pid=None):
        """Aplica dano a qualquer alvo (monstro/jogador/animado), tratando morte."""
        if dano <= 0:
            return
        if "vida_atual" in alvo:                       # animado / elemental
            dano = self._ajustar_dano_elemental(alvo, dano, elemento)
            alvo["vida_atual"] = max(0, alvo["vida_atual"] - dano)
            if alvo["vida_atual"] <= 0:
                await self._animado_morre(alvo, killer_pid)
        elif self._eh_jogador(alvo):
            alvo["hp"] = max(0, alvo["hp"] - dano)
            await self._acordar_se_dormindo(alvo)      # dano acorda quem dorme
            if alvo["hp"] <= 0:
                await self._player_dies(alvo["id"])
        else:                                          # monstro
            # Fraquezas/imunidades elementais (ex.: fogo ×2 no Devorador, raio no Crocodilo).
            dano = self._apply_damage_types(dano, [_NORM_ELEMENTO.get(elemento, elemento)], alvo)
            alvo["hp"] = max(0, alvo["hp"] - dano)
            await self._acordar_se_dormindo(alvo)
            if alvo["hp"] <= 0:
                await self._monster_dies(alvo, killer_pid)

    async def _acordar_se_dormindo(self, alvo):
        if alvo.get("dormindo"):
            alvo.pop("dormindo", None); alvo.pop("dormindo_rodadas", None)
            await self.gm_say(f"🌙 **{alvo.get('name') or alvo.get('nome','Alvo')}** acorda com o dano!")

    def _alvo_monstro(self, alvo_id):
        return next((m for m in self.monsters.values() if m.get("id") == alvo_id), None)

    async def _checar_alcance_centro(self, caster, magia, tx, ty):
        """Valida o alcance do conjurador até o CENTRO de uma magia de área.
        Retorna False (e avisa o cliente) se estiver além do `alcance` da magia.
        O alcance é geometria de jogo — vale mesmo no modo teste livre."""
        alc = magia.get("alcance")
        if alc is None:
            return True
        dist = max(abs(caster["pos"][0] - tx), abs(caster["pos"][1] - ty))
        if dist > alc:
            await self.send_to(caster["id"], {"type": "error",
                "msg": f"Centro da magia fora do alcance ({dist} > {alc})."})
            return False
        return True

    async def _executar_sono(self, caster, magia, data, dur_bonus):
        bonus_int = mod(caster.get("int_", 10))
        tx = int((data or {}).get("tx", caster["pos"][0])); ty = int((data or {}).get("ty", caster["pos"][1]))
        if not await self._checar_alcance_centro(caster, magia, tx, ty): return
        dur = self._rolar_dado(magia.get("duracao", "1d4+1")) + dur_bonus
        n = 0
        for alvo in self._alvos_na_area(tx, ty, magia.get("area_raio", 2)):
            save_ok, *_ = await self._save_mostrado(alvo, "vontade", self._dif_magia(caster, magia))
            if not save_ok:
                alvo["dormindo"] = True; alvo["dormindo_rodadas"] = dur; n += 1
        await self.gm_say(f"🌙 **{caster['name']}** lança Sono — {n} alvo(s) adormecem por até {dur} rodada(s) (afeta aliados/minions também).")

    async def _executar_medo(self, caster, magia, data, dur_bonus):
        bonus_int = mod(caster.get("int_", 10))
        tx = int((data or {}).get("tx", caster["pos"][0])); ty = int((data or {}).get("ty", caster["pos"][1]))
        if not await self._checar_alcance_centro(caster, magia, tx, ty): return
        dur = self._rolar_dado(magia.get("duracao", "1d4+1")) + dur_bonus
        n = 0
        for alvo in self._alvos_na_area(tx, ty, magia.get("area_raio", 2)):
            save_ok, *_ = await self._save_mostrado(alvo, "vontade", self._dif_magia(caster, magia))
            if not save_ok:
                alvo["com_medo"] = True; alvo["medo_rodadas"] = dur
                self._set_mod_magia(alvo, {"ataque": -1}, dur); n += 1
        await self.gm_say(f"😱 **{caster['name']}** lança Medo — {n} alvo(s) afetado(s) por {dur} rodada(s) (-1 ataque; afeta aliados/minions).")

    async def _executar_comando(self, caster, magia, data):
        bonus_int = mod(caster.get("int_", 10))
        alvo = self._alvo_monstro((data or {}).get("target_id"))
        if not alvo or alvo["hp"] <= 0:
            await self.send_to(caster["id"], {"type": "error", "msg": "Alvo inválido."}); return
        dist = max(abs(caster["pos"][0]-alvo["pos"][0]), abs(caster["pos"][1]-alvo["pos"][1]))
        if dist > magia.get("alcance", 4):
            await self.send_to(caster["id"], {"type": "error", "msg": "Alvo fora do alcance."}); return
        save_ok, *_ = await self._save_mostrado(alvo, "vontade", self._dif_magia(caster, magia))
        if not save_ok:
            alvo["comandado"] = True
            await self.gm_say(f"🗣️ **{caster['name']}** comanda **{alvo['name']}** — perderá a próxima ação!")
        else:
            await self.gm_say(f"🗣️ **{alvo['name']}** resiste ao Comando.")

    async def _executar_dominar_mente(self, caster, magia, data, dur_bonus):
        bonus_int = mod(caster.get("int_", 10))
        alvo = self._alvo_monstro((data or {}).get("target_id"))
        if not alvo or alvo["hp"] <= 0:
            await self.send_to(caster["id"], {"type": "error", "msg": "Alvo inválido."}); return
        dist = max(abs(caster["pos"][0]-alvo["pos"][0]), abs(caster["pos"][1]-alvo["pos"][1]))
        if dist > magia.get("alcance", 5):
            await self.send_to(caster["id"], {"type": "error", "msg": "Alvo fora do alcance."}); return
        save_ok, *_ = await self._save_mostrado(alvo, "vontade", self._dif_magia(caster, magia))
        if not save_ok:
            dur = self._rolar_dado(magia.get("duracao", "1d4")) + dur_bonus
            alvo["dominado"] = True; alvo["dominado_rodadas"] = dur; alvo["dominado_por"] = caster["id"]
            await self.gm_say(f"🧠 **{caster['name']}** domina a mente de **{alvo['name']}** por {dur} rodada(s)!")
        else:
            await self.gm_say(f"🧠 **{alvo['name']}** resiste a Dominar Mente.")

    # ── Dominar Morto-Vivo: CONTROLE PROGRESSIVO (3 rodadas de Vontade) ──────────
    #   Lançamento (rodada 1): morto-vivo testa Vontade (bônus = ND). Passa → falha.
    #   Falha → vira servo TEMPORÁRIO do caster (entra em caster["animados"], age na
    #   fase dos servos como os minions). A cada rodada (início da fase dos servos) faz
    #   novo teste: passar QUEBRA o controle (volta hostil ao tabuleiro); 3 falhas
    #   seguidas → controle PERMANENTE. Slot único: relançar destrói o permanente ou
    #   libera o temporário antes de afetar o novo alvo. Pedro morre → o servo vira pó.
    def _nd_criatura(self, alvo):
        """Nível de Desafio (ND) de uma criatura: nível do animado ou tier do monstro."""
        return alvo.get("nivel", alvo.get("tier", 1)) or 1

    def _monstro_para_animado(self, m, owner_pid, cd):
        """Converte um monstro morto-vivo em um animado dominado (mesmo shape dos servos)."""
        atk = (m.get("attacks") or [{}])[0]
        return {
            "id":         m["id"],
            "owner":      owner_pid,                         # dono (caster) — vira pó se ele morre
            "nome":       f"{m.get('name', 'Morto-Vivo')} (Dominado)",
            "icone":      m.get("emoji", "💀"),
            "tipo":       m.get("type", "undead"),
            "nivel":      self._nd_criatura(m),
            "slots":      0,                                 # domínio não ocupa slot de Animar
            "ca":         m.get("ac", 10),
            "vida_max":   m.get("max_hp", m.get("hp", 10)),
            "vida_atual": max(1, m.get("hp", 10)),
            "dano":       atk.get("damage") or m.get("damage", "1d4"),
            "movimento":  m.get("movement", 4),
            "moves_left": m.get("movement", 4),
            "acted":      False,
            "pos":        list(m["pos"]),
            "hostil":     False,
            "por_dominacao": True,
            "_snapshot":  deepcopy(m),                       # p/ restaurar como hostil se escapar
            "dominacao":  {"rodada": 2, "permanente": False, "cd": cd},
        }

    def _restaurar_monstro_dominado(self, a):
        """Devolve um animado-por-dominação ao tabuleiro como monstro HOSTIL (HP atual)."""
        snap = a.get("_snapshot")
        if not snap:
            return None
        snap["hp"]  = max(1, a.get("vida_atual", 1))
        snap["pos"] = list(a["pos"])
        # Limpa flags do sistema antigo de dominação por si acaso.
        for k in ("dominado", "dominado_permanente", "dominado_rodadas", "dominado_por"):
            snap.pop(k, None)
        self.monsters[snap["id"]] = snap
        return snap

    async def _liberar_dominacao_anterior(self, caster):
        """Slot único: ao relançar, destrói o dominado PERMANENTE ou libera o TEMPORÁRIO."""
        for a in list(caster.get("animados", [])):
            if not a.get("por_dominacao") or a.get("dominado_por_monstro"):
                continue
            if a.get("dominacao", {}).get("permanente"):
                await self.gm_say(f"💀 **{a['nome']}** se desfaz em pó para abrir caminho ao novo domínio.")
                self._remover_animado(a["id"])
            else:
                m = self._restaurar_monstro_dominado(a)
                self._remover_animado(a["id"])
                if m:
                    await self.gm_say(f"💀 O controle sobre **{m['name']}** se rompe — volta a ser hostil.")

    async def _executar_dominar_morto_vivo(self, caster, magia, data):
        alvo = self._alvo_monstro((data or {}).get("target_id"))
        if not alvo or alvo["hp"] <= 0:
            await self.send_to(caster["id"], {"type": "error", "msg": "Alvo inválido."}); return
        if not self._eh_morto_vivo_ou_demonio(alvo):
            await self.send_to(caster["id"], {"type": "error", "msg": "O alvo não é um morto-vivo."}); return
        dist = max(abs(caster["pos"][0]-alvo["pos"][0]), abs(caster["pos"][1]-alvo["pos"][1]))
        if dist > magia.get("alcance", 4):
            await self.send_to(caster["id"], {"type": "error", "msg": "Alvo fora do alcance."}); return

        # Slot único: libera/destrói o morto-vivo dominado anteriormente por este caster.
        await self._liberar_dominacao_anterior(caster)

        dif = self._dif_magia(caster, magia)
        nd  = self._nd_criatura(alvo)
        save_ok, *_ = await self._save_mostrado(alvo, "vontade", dif, extra_mod=nd)
        if save_ok:
            await self.gm_say(f"💀 **{alvo['name']}** resiste ao domínio (Vontade vs CD {dif}, ND +{nd}).")
            return
        # Falha: vira servo temporário e já age nesta fase dos servos.
        animado = self._monstro_para_animado(alvo, caster["id"], dif)
        self.monsters.pop(alvo["id"], None)
        caster.setdefault("animados", []).append(animado)
        await self.gm_say(
            f"💀 **{caster['name']}** domina **{alvo['name']}**! Controle temporário — o morto-vivo "
            f"testará Vontade (CD {dif}) a cada rodada; 3 falhas seguidas = controle PERMANENTE.")

    async def _retestar_dominacao_jogador(self, p):
        """Início da fase dos servos: cada morto-vivo dominado por ESTE jogador (controle
        progressivo, ainda não permanente) testa Vontade. Passar quebra o controle (volta
        hostil); falhar avança rumo ao controle permanente (3 falhas seguidas)."""
        for a in list(p.get("animados", [])):
            if not a.get("por_dominacao") or a.get("dominado_por_monstro"):
                continue
            dom = a.get("dominacao", {})
            if dom.get("permanente"):
                continue
            nd = self._nd_criatura(a)
            cd = dom.get("cd", 13)
            save_ok, *_ = await self._save_mostrado(a, "vontade", cd, extra_mod=nd)
            if save_ok:
                m = self._restaurar_monstro_dominado(a)
                self._remover_animado(a["id"])
                nome = m["name"] if m else a["nome"]
                await self.gm_say(f"💀 **{nome}** rompe o domínio e volta a ser HOSTIL!")
            else:
                rod = dom.get("rodada", 2)
                if rod >= 3:
                    dom["permanente"] = True
                    await self.gm_say(f"💀 O domínio de **{p['name']}** sobre **{a['nome']}** torna-se PERMANENTE!")
                else:
                    dom["rodada"] = rod + 1
                    await self.gm_say(f"💀 **{a['nome']}** continua dominado (falha {rod}/3).")

    async def _agir_animados_dominados_por_monstro(self):
        """Fase dos monstros: animados roubados por um necromante re-testam Vontade; se
        ainda dominados (ou já permanentes) atacam o personagem mais próximo. Passar →
        volta ao dono original (Pedro). Necromante morto → também volta ao dono."""
        for pp in self.players.values():
            for a in list(pp.get("animados", [])):
                mid = a.get("dominado_por_monstro")
                if not mid or a.get("vida_atual", 0) <= 0:
                    continue
                necro = self.monsters.get(mid)
                dom   = a.get("dominacao", {})
                dono  = self.players.get(a.get("dono_original") or a.get("owner"))
                dono_nome = dono["name"] if dono else "seu invocador"
                # Necromante morto: o controle se desfaz, volta ao dono.
                if necro is None or necro["hp"] <= 0:
                    a.pop("dominado_por_monstro", None); a.pop("dominacao", None); a.pop("dono_original", None)
                    await self.gm_say(f"💀 Sem o necromante, **{a['nome']}** volta a obedecer **{dono_nome}**.")
                    continue
                # Re-teste de Vontade (enquanto não for permanente).
                if not dom.get("permanente"):
                    nd = self._nd_criatura(a)
                    cd = dom.get("cd", 13)
                    save_ok, *_ = await self._save_mostrado(a, "vontade", cd, extra_mod=nd)
                    if save_ok:
                        a.pop("dominado_por_monstro", None); a.pop("dominacao", None); a.pop("dono_original", None)
                        await self.gm_say(f"💀 **{a['nome']}** rompe o controle do necromante e volta a obedecer **{dono_nome}**!")
                        continue
                    rod = dom.get("rodada", 2)
                    if rod >= 3:
                        dom["permanente"] = True
                        await self.gm_say(f"💀 O necromante domina **{a['nome']}** PERMANENTEMENTE!")
                    else:
                        dom["rodada"] = rod + 1
                await self._animado_ataca_jogador(a)

    async def _animado_ataca_jogador(self, a):
        """Um animado controlado por monstro avança até o personagem mais próximo e ataca."""
        alvos = [p for p in self.players.values() if p["alive"]]
        if not alvos:
            return
        target = min(alvos, key=lambda p: abs(p["pos"][0]-a["pos"][0]) + abs(p["pos"][1]-a["pos"][1]))
        if not self._cardinal_adjacent(a["pos"], target["pos"]):
            for _ in range(a.get("movimento", 3)):
                if self._cardinal_adjacent(a["pos"], target["pos"]):
                    break
                dx = 0 if a["pos"][0] == target["pos"][0] else (1 if target["pos"][0] > a["pos"][0] else -1)
                dy = 0 if a["pos"][1] == target["pos"][1] else (1 if target["pos"][1] > a["pos"][1] else -1)
                moved = False
                for adx, ady in [(dx, 0), (0, dy)]:
                    if adx == 0 and ady == 0:
                        continue
                    nx, ny = a["pos"][0]+adx, a["pos"][1]+ady
                    if self._tile_livre_para_animado(nx, ny, a["id"]):
                        a["pos"] = [nx, ny]; moved = True; break
                if not moved:
                    break
        if not self._cardinal_adjacent(a["pos"], target["pos"]):
            return
        roll  = random.randint(1, 20)
        total = roll + a.get("nivel", 1)
        eff_ac = target["ac"] + self.temp_def.get(target["id"], 0) + self._mod_magia(target, "ca")
        hit = roll == 20 or total >= eff_ac
        await self.broadcast({"type": "dice_roll", "die": "d20", "value": roll,
                               "label": f"{a['nome']} (dominado)", "hit": hit, "crit": roll == 20})
        if hit:
            dmg = max(1, roll_dice(a.get("dano", "1d4")) * (2 if roll == 20 else 1))
            target["hp"] = max(0, target["hp"] - dmg)
            await self.gm_say(f"⚔️ **{a['nome']}** (dominado) ataca **{target['name']}**: **{dmg}** de dano!")
            if target["hp"] <= 0:
                await self._player_dies(target["id"])
        else:
            await self.gm_say(f"⚔️ **{a['nome']}** (dominado) ataca **{target['name']}** e erra.")

    async def _executar_lentidao(self, caster, magia, data, dur_bonus):
        bonus_int = mod(caster.get("int_", 10))
        tx = int((data or {}).get("tx", caster["pos"][0])); ty = int((data or {}).get("ty", caster["pos"][1]))
        if not await self._checar_alcance_centro(caster, magia, tx, ty): return
        dur = self._rolar_dado(magia.get("duracao", "1d4")) + dur_bonus
        n = 0
        for alvo in self._alvos_na_area(tx, ty, magia.get("area_raio", 1)):
            save_ok, *_ = await self._save_mostrado(alvo, "vontade", self._dif_magia(caster, magia))
            if not save_ok:   # falha grave: perde metade dos turnos, -1 CA, -1 ataque
                alvo["lento"] = True; alvo["lento_rodadas"] = dur; alvo["lento_pulou"] = False
                self._set_mod_magia(alvo, {"ca": -1, "ataque": -1}, dur)
            else:             # sucesso: efeito brando (-1 ataque)
                self._set_mod_magia(alvo, {"ataque": -1}, dur)
            n += 1
        await self.gm_say(f"🐌 **{caster['name']}** lança Lentidão — {n} alvo(s) afetado(s) por {dur} rodada(s) (afeta aliados/minions).")

    # ── Batch 3: buffs sustentados (Invisibilidade, Regeneração) ─────────────────
    def _acao_bloqueada(self, p):
        """True se p não pode fazer outra ação principal. Velocidade concede 1 ação
        extra por turno: ao tentar agir já tendo agido, consome a extra e libera."""
        if p.get("perde_turno"):
            return True  # Imobilizado (teia, etc.) — perde o turno inteiro
        if not p.get("action_done"):
            return False
        if p.get("velocidade_rodadas", 0) > 0 and not p.get("velocidade_extra_usada"):
            p["velocidade_extra_usada"] = True
            p["action_done"] = False
            return False
        return True

    async def _executar_velocidade(self, caster, magia, dur_bonus):
        dur = self._rolar_dado(magia.get("duracao", "1d4")) + dur_bonus
        caster["velocidade_rodadas"]      = dur
        caster["velocidade_extra_usada"]  = False   # ação extra disponível já neste turno
        await self.gm_say(f"⚡ **{caster['name']}** acelera — ações dobradas e movimento dobrado por {dur} rodada(s)!")

    async def _executar_barreira_arcana(self, caster, magia):
        """Prepara uma barreira que cancela a PRÓXIMA magia recebida (dura até absorver).
        Hoje os monstros não lançam magia; absorve magia recebida de qualquer fonte
        (ex.: fogo em área, Relâmpago, Jato de Ar de um aliado)."""
        caster["barreira_arcana"] = True
        await self.gm_say(
            f"🛡️ **{caster['name']}** ergue uma **Barreira Arcana** — cancelará a próxima magia "
            f"recebida (e só então consome o slot).")

    async def _reacao_anti_magia(self, alvo, fonte=None):
        """Reações que cancelam uma magia recebida: Barreira Arcana (cancela automático)
        ou Contramágica (teste oposto d20+INT vs a fonte). Retorna True se cancelou."""
        if alvo.get("barreira_arcana"):
            alvo["barreira_arcana"] = False
            await self.gm_say(f"🛡️ A **Barreira Arcana** de **{alvo.get('name','alvo')}** absorve a magia recebida!")
            return True
        if alvo.get("contramagica_preparada"):
            alvo["contramagica_preparada"] = False        # a reação é gasta (sucesso OU falha)
            meu = random.randint(1, 20) + mod(alvo.get("int_", 10))
            op  = random.randint(1, 20) + (mod(fonte.get("int_", 10)) if fonte else 2)
            if meu >= op:
                await self.gm_say(f"🛑 **Contramágica** de **{alvo.get('name','alvo')}** vence o teste oposto ({meu} vs {op}) e cancela a magia!")
                return True
            await self.gm_say(f"🛑 **Contramágica** de **{alvo.get('name','alvo')}** falha no teste oposto ({meu} vs {op}).")
            return False
        return False

    async def _executar_contramagica(self, caster, magia):
        """Prepara uma Contramágica: ao receber a próxima magia, faz teste oposto para
        cancelá-la (consome ao usar). Hoje os monstros não lançam magia — atua contra
        magia recebida de qualquer fonte (friendly-fire)."""
        caster["contramagica_preparada"] = True
        await self.gm_say(
            f"🛑 **{caster['name']}** prepara **Contramágica** — teste oposto para cancelar a "
            f"próxima magia recebida (consome a reação ao usar).")

    async def _executar_silencio(self, caster, magia, data, dur_bonus):
        """Zona de Silêncio 4x4 (sem teste de resistência): dentro dela ninguém lança
        magia nem recebe os bônus da Canção Heroica. Centro escolhido dentro do alcance
        (5 + 1 por 2 níveis). Duração 1d4 rodadas."""
        nivel   = caster.get("level", 1)
        alcance = magia.get("alcance_base", 5) + (nivel // 2) * magia.get("alcance_escala", 1)
        lado    = magia.get("area_lado", 4)
        tx = int((data or {}).get("tx", caster["pos"][0]))
        ty = int((data or {}).get("ty", caster["pos"][1]))
        dist = max(abs(caster["pos"][0]-tx), abs(caster["pos"][1]-ty))
        if dist > alcance:
            await self.send_to(caster["id"], {"type": "error",
                "msg": f"Centro fora do alcance ({dist} > {alcance})."}); return
        dur = self._rolar_dado(magia.get("duracao", "1d4")) + dur_bonus
        self.zonas_especiais.append({
            "id":      f"silencio_{caster['id']}_{self.round_num}",
            "tipo":    "silencio",
            "cx":      tx, "cy": ty, "lado": lado,
            "duracao": dur, "ativa": True, "caster": caster["id"],
        })
        await self.gm_say(
            f"🔇 **{caster['name']}** cria uma área de **Silêncio** {lado}x{lado} em ({tx},{ty}) "
            f"por {dur} rodada(s) — sem magias nem bônus de Canção Heroica dentro (alcance {alcance}q).")

    async def _executar_conjurar_elemental(self, caster, magia, data):
        """Invoca um elemental CONTROLÁVEL: entra na lista `animados` do caster, então
        reusa tudo (mira dos monstros, janela dos servos ao encerrar turno, controle por
        clique no tabuleiro, render). Specials por tipo ficam para um passo futuro."""
        tipos = magia.get("tipos", {})
        tipo  = (data or {}).get("tipo_elemental", "pedra")
        if tipo not in tipos:
            tipo = "pedra" if "pedra" in tipos else next(iter(tipos), "pedra")
        stats   = tipos.get(tipo, {"hp": 20, "dano": "1d6"})
        icones  = {"fogo": "🔥", "eletrico": "⚡", "gelo": "❄️", "pedra": "🪨"}
        ca_tipo = {"fogo": 14, "eletrico": 14, "gelo": 15, "pedra": 16}
        ATK_ELEMENTAL = 4   # bônus de ataque da criatura (usado como roll + nivel)

        # Casa livre adjacente ao caster (8 vizinhos); fallback = casa do caster.
        ox, oy = caster["pos"]
        pos = [ox, oy]
        for ddx, ddy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
            if self._tile_livre_para_animado(ox+ddx, oy+ddy, None):
                pos = [ox+ddx, oy+ddy]; break

        self._elemental_seq = getattr(self, "_elemental_seq", 0) + 1
        mov = magia.get("movimento", 6)
        hpv = stats.get("hp", 20)
        elem = {
            "id":         f"elemental_{tipo}_{self._elemental_seq}",
            "owner":      caster["id"],
            "nome":       f"Elemental de {tipo.capitalize()}",
            "icone":      icones.get(tipo, "🌪️"),
            "tipo":       "elemental",
            "tipo_elemental": tipo,
            "especial":   stats.get("especial"),
            "nivel":      ATK_ELEMENTAL,        # +4 de ataque (formula do animado: roll + nivel)
            "slots":      0,
            "ca":         ca_tipo.get(tipo, 14),
            "vida_max":   hpv, "vida_atual": hpv,
            "dano":       stats.get("dano", "1d6"),
            "movimento":  mov, "moves_left": mov,
            "acted":      False, "pos": pos, "hostil": False,
        }
        caster.setdefault("animados", []).append(elem)
        await self.gm_say(
            f"🌪️ **{caster['name']}** conjura um **Elemental de {tipo.capitalize()}** "
            f"(HP {hpv}, dano {stats.get('dano','1d6')}, mov {mov}). "
            f"Controle-o como os servos — encerre o turno para abrir a janela dos elementais.")

    # ── Especiais dos elementais ────────────────────────────────────────────────
    def _ajustar_dano_elemental(self, alvo, dano, elemento):
        """Imunidades e resistências dos elementais ao dano recebido.
        Fogo: imune a fogo. Elétrico: imune a eletricidade. Gelo: imune a frio
        (−2 físico, +2 fogo). Pedra: −3 físico (resistência)."""
        if dano <= 0:
            return dano
        tipo = alvo.get("tipo_elemental", "")
        elem = (elemento or "fisico").lower()
        # Normaliza variantes de acentuação
        elem = elem.replace("á", "a").replace("é", "e").replace("ê", "e")

        eh_fisico   = elem in ("fisico", "ataque", "corte", "impacto", "")
        eh_fogo     = elem in ("fogo", "fire", "chamas", "flames")
        eh_eletrico = elem in ("eletrico", "eletricidade", "raio", "lightning",
                               "relampago", "eletricidade")
        eh_frio     = elem in ("gelo", "frio", "cold", "congelante", "raio_congelante")

        if tipo == "fogo"    and eh_fogo:      return 0          # imune a fogo
        if tipo == "eletrico" and eh_eletrico: return 0          # imune a eletricidade
        if tipo == "gelo":
            if eh_frio:   return 0                               # imune a frio
            if eh_fisico: return max(1, dano - 2)               # −2 físico
            if eh_fogo:   return dano + 2                       # vulnerável a fogo
        if tipo == "pedra" and eh_fisico:
            return max(1, dano - 3)                             # −3 físico
        return dano

    def _em_linha_cardinal(self, pos_a, pos_b, max_dist):
        """True se pos_b está numa linha cardinal de pos_a, dentro de max_dist casas."""
        dx, dy = pos_b[0] - pos_a[0], pos_b[1] - pos_a[1]
        if dx != 0 and dy != 0:          # diagonal — não é linha cardinal
            return False
        return 1 <= abs(dx) + abs(dy) <= max_dist

    def _linha_bloqueada_por_parede(self, pos_a, pos_b):
        """True se há uma parede entre pos_a e pos_b (verifica tiles intermediários)."""
        dx, dy = pos_b[0] - pos_a[0], pos_b[1] - pos_a[1]
        sx = (dx > 0) - (dx < 0)
        sy = (dy > 0) - (dy < 0)
        cx, cy = pos_a[0] + sx, pos_a[1] + sy
        while [cx, cy] != pos_b:
            if not (0 <= cx < self.map_w and 0 <= cy < self.map_h):
                return True
            if self.tiles[cy][cx] == WALL:
                return True
            cx += sx; cy += sy
        return False

    async def _animado_morre(self, animado, killer_pid=None):
        """Morte de um animado/elemental: dispara a explosão (fogo) e o remove."""
        if animado.get("especial") == "explosao_6d6" and not animado.get("_explodiu"):
            animado["_explodiu"] = True
            await self.gm_say(f"💥 **{animado.get('nome','Elemental')}** é destruído e EXPLODE!")
            await self._explosao_elemental(animado, killer_pid)
        else:
            await self.gm_say(f"💨 **{animado.get('nome','Servo')}** foi destruído!")
        self._remover_animado(animado["id"])

    async def _explosao_elemental(self, elem, killer_pid=None):
        """Explosão do Elemental de Fogo: 6d6 de fogo em raio 1 — CD 12 Reflexos para metade."""
        cx, cy = elem["pos"]; raio = 1
        dano_total = sum(random.randint(1, 6) for _ in range(6))

        # Destaca a área no cliente (tiles vermelhos por ~2 s)
        tiles_area = [
            [x, y]
            for y in range(cy - raio, cy + raio + 1)
            for x in range(cx - raio, cx + raio + 1)
            if 0 <= x < self.map_w and 0 <= y < self.map_h
        ]
        await self.broadcast({
            "type": "explosion_area",
            "cx": cx, "cy": cy, "tiles": tiles_area, "duracao_ms": 2200
        })

        await self.broadcast({"type": "dice_roll", "die": "d6",
                               "value": dano_total, "label": "🔥 Explosão 6d6"})
        await self.gm_say(
            f"💥 A explosão causa até **{dano_total}** de dano em chamas"
            f" (raio {raio}) — CD 12 Reflexos para metade! Atinge aliados também!")
        kp = killer_pid or elem.get("owner", "")

        # Monstros (fazem save — criaturas mais fortes resistem melhor)
        for m in list(self.monsters.values()):
            if m["hp"] > 0 and max(abs(m["pos"][0]-cx), abs(m["pos"][1]-cy)) <= raio:
                salvou, d20, bonus, total = await self._save_mostrado(m, "reflexos", 12)
                d = dano_total // 2 if salvou else dano_total
                if salvou:
                    await self.gm_say(
                        f"🎲 **{m['name']}** esquiva parcial (d20={d20}+{bonus}={total} ≥ 12) — {d} de dano.")
                m["hp"] = max(0, m["hp"] - d)
                if m["hp"] <= 0:
                    await self._monster_dies(m, kp)

        # Jogadores
        for pid, pl in list(self.players.items()):
            if pl["alive"] and max(abs(pl["pos"][0]-cx), abs(pl["pos"][1]-cy)) <= raio:
                salvou, d20, bonus, total = await self._save_mostrado(pl, "reflexos", 12)
                dano_final = dano_total // 2 if salvou else dano_total
                if salvou:
                    await self.gm_say(
                        f"✅ **{pl['name']}** esquiva da explosão (d20={d20}+{bonus}={total} ≥ 12) — {dano_final} de dano.")
                else:
                    await self.gm_say(
                        f"❌ **{pl['name']}** é atingido em cheio (d20={d20}+{bonus}={total} < 12) — {dano_final} de dano.")
                d = await self._absorver_energia(pl, dano_final, "fogo")
                pl["hp"] = max(0, pl["hp"] - d)
                if pl["hp"] <= 0:
                    await self._player_dies(pid)

        # Outros animados/elementais (sem save — entidades mágicas absorvem conforme tipo)
        for a in list(self._all_animados()):
            if a["id"] == elem["id"]:
                continue
            if max(abs(a["pos"][0]-cx), abs(a["pos"][1]-cy)) <= raio:
                d = self._ajustar_dano_elemental(a, dano_total, "fogo")
                a["vida_atual"] = max(0, a["vida_atual"] - d)
                if a["vida_atual"] <= 0:
                    await self._animado_morre(a, kp)

    async def _linha_eletrica(self, a, alvo_pos, pid):
        """Elemental Elétrico: descarrega uma linha de 3 casas (alvo + 2 além, na direção)."""
        if a.get("especial") != "linha_3q":
            return
        dx = (alvo_pos[0] - a["pos"][0]); dy = (alvo_pos[1] - a["pos"][1])
        dx = (dx > 0) - (dx < 0); dy = (dy > 0) - (dy < 0)
        if dx == 0 and dy == 0:
            return
        faces = a.get("dano", "1d8").split("d")[-1]
        for k in (1, 2):                                   # 2 casas além do alvo
            tx, ty = alvo_pos[0] + dx * k, alvo_pos[1] + dy * k
            extra = next((mm for mm in self.monsters.values() if mm["hp"] > 0 and mm["pos"] == [tx, ty]), None)
            if extra:
                d2 = max(1, roll_dice(a.get("dano", "1d8")))
                await self.broadcast({"type": "dice_roll", "die": f"d{faces}", "value": d2, "label": "⚡ Linha"})
                extra["hp"] = max(0, extra["hp"] - d2)
                await self.gm_say(f"⚡ A linha elétrica do **{a['nome']}** atinge **{extra['name']}**: {d2} de dano!")
                if extra["hp"] <= 0:
                    await self._monster_dies(extra, pid)

    async def _executar_protecao_energia(self, caster, magia, dur_bonus):
        dur     = self._rolar_dado(magia.get("duracao", "1d6+1")) + dur_bonus
        reducao = magia.get("reducao_por_rodada", 10)
        caster["protecao_rodadas"]  = dur
        caster["protecao_max"]      = reducao
        caster["protecao_restante"] = reducao
        caster["protecao_tipos"]    = list(magia.get("tipos", ["fogo", "gelo", "eletricidade"]))
        await self.gm_say(f"🛡️ **{caster['name']}** fica protegido: absorve até {reducao} de dano de fogo/gelo/eletricidade por rodada ({dur} rodada(s)).")

    async def _absorver_energia(self, alvo, dano, tipo):
        """Reduz dano do tipo elemental se o alvo tiver Proteção contra Energia (até o restante da rodada)."""
        if dano <= 0 or alvo.get("protecao_rodadas", 0) <= 0:
            return dano
        if tipo not in alvo.get("protecao_tipos", []):
            return dano
        restante = alvo.get("protecao_restante", 0)
        if restante <= 0:
            return dano
        absorvido = min(restante, dano)
        alvo["protecao_restante"] = restante - absorvido
        await self.gm_say(f"🛡️ Proteção de **{alvo['name']}** absorve {absorvido} de {tipo} (resta {alvo['protecao_restante']}).")
        return dano - absorvido

    async def _executar_invisibilidade(self, caster, magia, dur_bonus):
        dur = self._rolar_dado(magia.get("duracao", "1d6+1")) + dur_bonus
        caster["invisivel_magico"] = True
        caster["invisivel_magico_rodadas"] = dur
        await self.gm_say(f"🫥 **{caster['name']}** fica invisível por {dur} rodada(s) — inimigos não o atacam; ataca com vantagem; quebra ao atacar/lançar.")

    async def _executar_regeneracao(self, caster, magia, data):
        alvo = self.players.get((data or {}).get("target_id"))
        if not alvo or not alvo["alive"]:
            await self.send_to(caster["id"], {"type": "error", "msg": "Aliado inválido."}); return
        dist = max(abs(caster["pos"][0]-alvo["pos"][0]), abs(caster["pos"][1]-alvo["pos"][1]))
        if dist > magia.get("alcance", 6):
            await self.send_to(caster["id"], {"type": "error", "msg": "Aliado fora do alcance."}); return
        pool = self._rolar_dado(magia.get("pool", "2d6+2"))
        alvo["regen_pool"]     = pool
        alvo["regen_ressurge"] = bool(magia.get("resurrect_com_pool", True))
        await self.gm_say(f"🌿 **{caster['name']}** regenera **{alvo['name']}** — reserva {pool} (+1 HP/rodada; revive uma vez com 1 HP).")

    # ── Jato de Ar (cone na direção; dano + empurrão + colisão na parede) ─────────
    def _cone_tiles(self, ox, oy, dx, dy, comp, base):
        """Casas do cone que abre a partir de (ox,oy) na direção (dx,dy)."""
        px, py = -dy, dx   # eixo perpendicular à direção
        tiles = set()
        for k in range(1, comp + 1):
            cxk, cyk = ox + dx * k, oy + dy * k
            hw = max(0, round((k / comp) * (base / 2)))   # meia-largura cresce até a base
            for o in range(-hw, hw + 1):
                tx, ty = cxk + px * o, cyk + py * o
                if 0 <= tx < self.map_w and 0 <= ty < self.map_h and self.tiles[ty][tx] != WALL:
                    tiles.add((tx, ty))
        return tiles

    def _empurrar(self, alvo, dx, dy, dist):
        """Empurra alvo até `dist` casas em (dx,dy). Retorna True se colidiu (parou cedo)."""
        for _ in range(max(0, dist)):
            nx, ny = alvo["pos"][0] + dx, alvo["pos"][1] + dy
            if not (0 <= nx < self.map_w and 0 <= ny < self.map_h) or self.tiles[ny][nx] == WALL:
                return True
            if any(o["hp"] > 0 and o["pos"] == [nx, ny] for o in self.monsters.values() if o is not alvo):
                return True
            if any(p["alive"] and p["pos"] == [nx, ny] for p in self.players.values() if p is not alvo):
                return True
            if self._animado_em([nx, ny]):
                return True
            alvo["pos"] = [nx, ny]
        return False

    async def _executar_jato_ar(self, caster, magia, data, dmg_mult):
        bonus_int = mod(caster.get("int_", 10))
        save_dif  = self._dif_magia(caster, magia)
        dirv = (data or {}).get("dir", [0, 0])
        dx = 1 if dirv[0] > 0 else -1 if dirv[0] < 0 else 0
        dy = 1 if dirv[1] > 0 else -1 if dirv[1] < 0 else 0
        if dx == 0 and dy == 0:
            await self.send_to(caster["id"], {"type": "error", "msg": "Direção inválida para o Jato de Ar."}); return

        tiles = self._cone_tiles(caster["pos"][0], caster["pos"][1], dx, dy,
                                 magia.get("comprimento", 4), magia.get("base_largura", 4))
        # Atinge TODOS no cone (exceto o próprio caster): monstros, aliados E animados/minions.
        alvos  = [m for m in self.monsters.values() if m["hp"] > 0 and tuple(m["pos"]) in tiles]
        alvos += [p for p in self.players.values()
                  if p["alive"] and p["id"] != caster["id"] and tuple(p["pos"]) in tiles]
        alvos += [a for a in self._all_animados() if tuple(a["pos"]) in tiles]
        # Empurra os mais distantes primeiro (evita empilhar um no espaço do outro).
        alvos.sort(key=lambda a: abs(a["pos"][0]-caster["pos"][0]) + abs(a["pos"][1]-caster["pos"][1]), reverse=True)

        n = 0
        for alvo in alvos:
            nome = alvo.get("name") or alvo.get("nome", "Alvo")
            if self._eh_jogador(alvo) and await self._reacao_anti_magia(alvo, caster):
                continue
            dano = int((await self._rolar_dano_mostrado(1, 6, "🌪️ Dano")) * dmg_mult + 0.5)
            save_ok, *_ = await self._save_mostrado(alvo, "reflexos", save_dif)
            push = magia.get("empurra_sucesso", 2) if save_ok else self._rolar_dado(magia.get("empurra_falha", "1d6"))
            if self._empurrar(alvo, dx, dy, push):
                col = self._rolar_dado(magia.get("dano_colisao", "1d4"))
                dano += col
                await self.gm_say(f"🌪️ **{nome}** é arremessado contra a parede (+{col} de colisão).")
            await self.gm_say(f"🌪️ **{nome}** sofre {dano} (empurrado {push}q).")
            await self._aplicar_dano_alvo(alvo, dano, None, caster["id"]); n += 1
        await self.gm_say(f"🌪️ **{caster['name']}** lança Jato de Ar — {n} alvo(s) no cone.")

    # ── Dados de magia exibidos no cliente (anima cada dado via handleDiceRoll) ──
    async def _broadcast_dado(self, die, value, label):
        await self.broadcast({"type": "dice_roll", "die": die, "value": value, "label": label})

    async def _rolar_dano_mostrado(self, n, faces, label):
        """Rola n dados de `faces`, anima CADA dado no cliente e retorna a soma."""
        total = 0
        for _ in range(max(1, int(n))):
            v = random.randint(1, faces)
            total += v
            await self._broadcast_dado(f"d{faces}", v, label)
        return total

    def _save_weakness_pen(self, alvo, tipo):
        """Penalidade de save vinda de fraquezas marcadas `em_magia` (ex.: Mente
        Limitada do Orc: -1 em Vontade vs efeitos mentais). Só vale no caminho de
        magias/efeitos (_save_mostrado), não nos venenos."""
        total = 0
        for w in alvo.get("weaknesses", []):
            if (w.get("type") == "save_penalty" and w.get("em_magia")
                    and w.get("save") == tipo):
                total += w.get("bonus_flat", 0)
        return total

    async def _save_mostrado(self, alvo, tipo, dif, extra_mod=0):
        """Faz um teste de resistência e anima o d20 do alvo no cliente."""
        extra_mod += self._save_weakness_pen(alvo, tipo)
        passou, d20, bonus, total = self._testar_save(alvo, tipo, dif, extra_mod=extra_mod)
        lab = {"reflexos": "Reflexos", "fortitude": "Fortitude", "vontade": "Vontade"}.get(tipo, tipo)
        await self._broadcast_dado("d20", d20, f"{lab} {'✓' if passou else '✗'}")
        return passou, d20, bonus, total

    def _dif_magia(self, caster, magia):
        """Dificuldade para resistir: 8 + bônus de INT + círculo (1/2/3). Aprimorar
        Magia (Pedro) soma +1 via flag temporária `_mm_dc_bonus` setada em handle_magia."""
        circ = {"primeiro": 1, "segundo": 2, "terceiro": 3}.get(magia.get("circulo", "primeiro"), 1)
        return 8 + mod(caster.get("int_", 10)) + circ + caster.get("_mm_dc_bonus", 0)

    # ── Bola de Fogo (área persistente que decai R1→R2→R3) ──────────────────────
    async def _executar_bola_fogo(self, caster, magia, data, dmg_mult, dur_bonus):
        nivel     = caster.get("level", 1)
        bonus_int = mod(caster.get("int_", 10))
        alcance   = magia["alcance_base"] + magia["alcance_escala"] * (nivel - 1)
        save_dif  = self._dif_magia(caster, magia)
        raio      = magia.get("area_raio", 2)
        cx = int((data or {}).get("tx", caster["pos"][0]))
        cy = int((data or {}).get("ty", caster["pos"][1]))

        # Alcance e linha de visão até o CENTRO da explosão: a magia viaja do
        # conjurador ao ponto-alvo — parede no caminho bloqueia o lançamento.
        dist_centro = max(abs(caster["pos"][0] - cx), abs(caster["pos"][1] - cy))
        if dist_centro > alcance:
            await self.send_to(caster["id"], {"type": "error",
                "msg": f"Centro da Bola de Fogo fora do alcance ({dist_centro} > {alcance})."}); return
        if not self._tem_linha_de_visao(caster["pos"], [cx, cy]):
            await self.send_to(caster["id"], {"type": "error",
                "msg": "🧱 Uma parede bloqueia a trajetória da Bola de Fogo!"}); return

        # R1 = 1d6 por nível; R2 = ½R1; R3 = ½R2. (anima cada d6 no cliente)
        dano_r1 = int((await self._rolar_dano_mostrado(nivel, 6, "🔥 Dano")) * dmg_mult + 0.5)
        dano_r2 = dano_r1 // 2
        dano_r3 = dano_r2 // 2

        atingidos = await self._aplicar_dano_area_fogo(caster["id"], cx, cy, raio, dano_r1, save_dif, "R1")

        # Zona persistente que aplica R2 e R3 no início das próximas rodadas.
        self.zonas_especiais.append({
            "id": f"bola_fogo_{cx}_{cy}_{self.round_num}", "tipo": "bola_fogo",
            "cx": cx, "cy": cy, "raio": raio,
            "dano_r2": dano_r2, "dano_r3": dano_r3,
            "rodada_atual": 2, "rodadas_max": 3,
            "save_dif": save_dif, "ativa": True, "caster": caster["id"],
        })
        await self.gm_say(
            f"🔥 **{caster['name']}** lança **Bola de Fogo** (nível {nivel}) — "
            f"R1:{dano_r1} R2:{dano_r2} R3:{dano_r3} | alcance {alcance}q | {atingidos} atingido(s).")

    async def _aplicar_dano_area_fogo(self, caster_id, cx, cy, raio, dano, save_dif, rotulo, com_save=True):
        """Dano de fogo a TODOS no raio — monstros, jogadores E animados (não discrimina
        aliados/minions). Só R1 testa Reflexos (com_save); R2/R3 = dano cheio."""
        n = 0
        for alvo in self._alvos_na_area(cx, cy, raio):
            # A onda de fogo se expande a partir do centro — paredes fazem
            # sombra: quem está atrás delas não é atingido.
            if not self._tem_linha_de_visao([cx, cy], alvo["pos"]):
                continue
            ehjog = self._eh_jogador(alvo)
            if ehjog and await self._reacao_anti_magia(alvo, self.players.get(caster_id)):
                continue   # Barreira/Contramágica (só jogadores)
            if com_save:
                save_ok, *_ = await self._save_mostrado(alvo, "reflexos", save_dif)
                d = dano // 2 if save_ok else dano; extra = ' (½)' if save_ok else ''
            else:
                d = dano; extra = ''
            if ehjog:
                d = await self._absorver_energia(alvo, d, "fogo")   # Proteção contra Energia
            nome = alvo.get("name") or alvo.get("nome", "Alvo")
            await self.gm_say(f"🔥 {rotulo}: **{nome}** sofre {d}{extra}.")
            await self._aplicar_dano_alvo(alvo, d, "fogo", caster_id)
            n += 1
        return n

    async def _processar_zona_bola_fogo(self, zona):
        """Tica a zona de Bola de Fogo no início da rodada (R2, depois R3)."""
        if not zona.get("ativa"): return
        rodada = zona.get("rodada_atual", 2)
        dano   = zona.get(f"dano_r{rodada}", 0)
        if dano <= 0 or rodada > zona.get("rodadas_max", 3):
            zona["ativa"] = False; return
        await self._aplicar_dano_area_fogo(
            zona.get("caster", ""), zona["cx"], zona["cy"],
            zona.get("raio", 2), dano, zona.get("save_dif", 12), f"Zona de fogo R{rodada}", com_save=False)
        zona["rodada_atual"] = rodada + 1
        if zona["rodada_atual"] > zona.get("rodadas_max", 3):
            zona["ativa"] = False
            await self.gm_say("🔥 A zona de Bola de Fogo se extingue.")

    async def _verificar_entrada_zona_fogo(self, ator, nx, ny):
        """Pisar numa zona de Bola de Fogo ativa causa o dano da rodada atual (entrar sofre dano)."""
        for zona in self.zonas_especiais:
            if zona.get("tipo") != "bola_fogo" or not zona.get("ativa"): continue
            if max(abs(nx - zona["cx"]), abs(ny - zona["cy"])) > zona.get("raio", 2): continue
            dano = zona.get(f"dano_r{zona.get('rodada_atual', 2)}", 0)
            if dano <= 0: continue
            d = dano   # zona = R2/R3 → sem teste de resistência
            d = await self._absorver_energia(ator, d, "fogo")   # Proteção contra Energia
            ator["hp"] = max(0, ator["hp"] - d)
            await self.gm_say(f"🔥 **{ator['name']}** entrou na zona de fogo e sofre {d}!")
            if ator["hp"] <= 0:
                if self._eh_jogador(ator):
                    await self._player_dies(ator["id"])
                else:
                    await self._monster_dies(ator, zona.get("caster", ""))
            break  # um disparo por movimento

    def _caminho_relampago(self, origem, dx, dy, alcance):
        """Casas visitadas (na ordem) gastando `alcance` passos de deslocamento. Ao
        bater em parede/borda, INVERTE a direção (ricochete) e continua gastando o
        mesmo orçamento — ex.: 5 até a parede + 2 de volta = 7. Casas pisadas 2x
        sofrem dano 2x; a origem (Pedro) só entra se o ricochete voltar até ela."""
        x, y = origem
        seq = []
        for _ in range(alcance):
            nx, ny = x + dx, y + dy
            if not (0 <= nx < self.map_w and 0 <= ny < self.map_h) or self.tiles[ny][nx] == WALL:
                dx, dy = -dx, -dy                      # ricochete na parede
                nx, ny = x + dx, y + dy
                if not (0 <= nx < self.map_w and 0 <= ny < self.map_h) or self.tiles[ny][nx] == WALL:
                    break                              # preso (ambos os lados bloqueados)
            x, y = nx, ny
            seq.append((x, y))
        return seq

    # ── Relâmpago (linha reta; ricocheteia na parede gastando o mesmo alcance) ────
    # O raio tem um orçamento de deslocamento = alcance (7 no nível 1). Anda na
    # direção escolhida; ao bater numa parede, ricocheteia e continua com o que
    # sobrou. Casas pisadas 2x sofrem dano 2x; Pedro (origem) só é ferido se o
    # ricochete voltar até ele. Dano (1d6/nível) + Reflexos por impacto.
    async def _executar_relampago(self, caster, magia, data, dmg_mult):
        nivel     = caster.get("level", 1)
        bonus_int = mod(caster.get("int_", 10))
        alcance   = magia["alcance_base"] + magia["alcance_escala"] * (nivel - 1)
        save_dif  = self._dif_magia(caster, magia)

        dirv = (data or {}).get("dir", [0, 0])
        dx = 1 if dirv[0] > 0 else -1 if dirv[0] < 0 else 0
        dy = 1 if dirv[1] > 0 else -1 if dirv[1] < 0 else 0
        if dx == 0 and dy == 0:
            await self.send_to(caster["id"], {"type": "error", "msg": "Direção inválida para o Relâmpago."}); return

        sequencia = self._caminho_relampago(caster["pos"], dx, dy, alcance)

        logs, feriu_caster, impactos = [], False, {}
        for (x, y) in sequencia:
            # Qualquer criatura na casa: monstro, jogador (aliado/caster) OU animado/minion.
            alvo = next((m for m in self.monsters.values() if m["hp"] > 0 and m["pos"] == [x, y]), None)
            if alvo is None:
                alvo = next((p for p in self.players.values() if p["alive"] and p["pos"] == [x, y]), None)
            if alvo is None:
                alvo = next((a for a in self._all_animados() if a["pos"] == [x, y]), None)
            if alvo is None:
                continue
            ehjog = self._eh_jogador(alvo)
            if ehjog and await self._reacao_anti_magia(alvo, caster):   # Barreira/Contramágica
                continue
            d = int((await self._rolar_dano_mostrado(nivel, 6, "⚡ Dano")) * dmg_mult + 0.5)
            save_ok, *_ = await self._save_mostrado(alvo, "reflexos", save_dif)
            d = d // 2 if save_ok else d
            if ehjog:
                d = await self._absorver_energia(alvo, d, "eletricidade")   # Proteção contra Energia
            aid = alvo.get("id")
            impactos[aid] = impactos.get(aid, 0) + 1
            logs.append(f"{(alvo.get('name') or alvo.get('nome','?'))}:{d}")
            if ehjog and aid == caster["id"]:
                feriu_caster = True
            await self._aplicar_dano_alvo(alvo, d, "eletricidade", caster["id"])

        multi = sum(1 for v in impactos.values() if v > 1)
        await self.gm_say(
            f"⚡ **{caster['name']}** lança **Relâmpago** (nível {nivel}, alcance {alcance}q c/ ricochete) — "
            f"impactos: {', '.join(logs) or 'nenhum'}"
            + (f" | {multi} alvo(s) atingido(s) 2x" if multi else "")
            + (" | ⚠️ atingiu o próprio Pedro na volta!" if feriu_caster else ""))

    # ── Raio Congelante (dano sem save + paralisação por Fortitude) ──────────────
    async def _executar_raio_congelante(self, caster, magia, data, dmg_mult, dur_bonus):
        nivel     = caster.get("level", 1)
        bonus_int = mod(caster.get("int_", 10))
        alcance   = magia["alcance_base"] + magia["alcance_escala"] * (nivel - 1)
        alvo_id   = (data or {}).get("target_id")
        alvo = self.players.get(alvo_id) or next(
            (m for m in self.monsters.values() if m.get("id") == alvo_id), None)
        vivo = alvo and (alvo["alive"] if self._eh_jogador(alvo) else alvo["hp"] > 0)
        if not vivo:
            await self.send_to(caster["id"], {"type": "error", "msg": "Alvo inválido."}); return

        dist = max(abs(caster["pos"][0]-alvo["pos"][0]), abs(caster["pos"][1]-alvo["pos"][1]))
        if dist > alcance:
            await self.send_to(caster["id"], {"type": "error", "msg": f"Alvo fora do alcance ({dist} > {alcance})."}); return
        if not self._tem_linha_de_visao(caster["pos"], alvo["pos"]):
            await self.send_to(caster["id"], {"type": "error",
                "msg": "🧱 Uma parede bloqueia o Raio Congelante!"}); return

        # Dano: 3d4 + 2d4 a cada 2 níveis — SEM save de Reflexos. (anima cada d4)
        nd   = 3 + ((nivel - 1) // 2) * 2
        dano = int((await self._rolar_dano_mostrado(nd, 4, "❄️ Dano")) * dmg_mult + 0.5)
        alvo["hp"] = max(0, alvo["hp"] - dano)
        await self.gm_say(f"❄️ **{caster['name']}** lança **Raio Congelante**: {nd}d4 = {dano} (sem save) em **{alvo['name']}**.")

        # Fortitude evita a paralisação (não o dano).
        save_ok, *_ = await self._save_mostrado(alvo, "fortitude", self._dif_magia(caster, magia))
        if not save_ok:
            alvo["paralisado"]             = True
            alvo["paralisado_rodadas"]     = 1
            alvo["paralisado_save"]        = "fortitude"
            alvo["paralisado_dificuldade"] = self._dif_magia(caster, magia)
            alvo["paralisado_rodada_max"]  = magia.get("paralisado_rodadas_max", 2)
            await self.gm_say(f"❄️ **{alvo['name']}** está **paralisado**! (novo Fortitude por rodada, máx {alvo['paralisado_rodada_max']})")
        else:
            await self.gm_say(f"❄️ **{alvo['name']}** resistiu à paralisação.")

        if alvo["hp"] <= 0:
            if self._eh_jogador(alvo):
                await self._player_dies(alvo["id"])
            else:
                await self._monster_dies(alvo, caster["id"])

    async def _processar_paralisacao_turno(self, alvo):
        """Início do turno do paralisado: novo save. Retorna True se continua paralisado."""
        if not alvo.get("paralisado"): return False
        dif   = alvo.get("paralisado_dificuldade", 12)
        max_r = alvo.get("paralisado_rodada_max", 2)
        save_ok, *_ = self._testar_save(alvo, alvo.get("paralisado_save", "fortitude"), dif)
        if save_ok:
            alvo["paralisado"] = False; alvo["paralisado_rodadas"] = 0
            await self.gm_say(f"✅ **{alvo['name']}** se libertou da paralisação!")
            return False
        alvo["paralisado_rodadas"] = alvo.get("paralisado_rodadas", 0) + 1
        if alvo["paralisado_rodadas"] >= max_r:
            alvo["paralisado"] = False; alvo["paralisado_rodadas"] = 0
            await self.gm_say(f"✅ A paralisação de **{alvo['name']}** terminou.")
            return False
        await self.gm_say(f"❄️ **{alvo['name']}** continua paralisado ({alvo['paralisado_rodadas']}/{max_r}).")
        return True

    # ── Sistema de zonas mágicas / escuridão ───────────────────────────────────
    # Zonas vivem em self.zonas_especiais; cada uma tem cx/cy/raio/duracao/ativa.
    # _verificar_escuridao/_alcance_escuridao são a API que a resolução de
    # combate (handle_attack) consultará quando a integração for ligada.

    def _zona_contem(self, x, y, zona):
        """True se (x,y) está no raio Chebyshev da zona."""
        return max(abs(x - zona["cx"]), abs(y - zona["cy"])) <= zona.get("raio", 0)

    def _zonas_ativas(self, tipo):
        return [z for z in self.zonas_especiais if z.get("ativa") and z.get("tipo") == tipo]

    def _em_escuridao(self, obj):
        x, y = obj.get("pos", [0, 0])
        return any(self._zona_contem(x, y, z) for z in self._zonas_ativas("escuridao"))

    def _em_zona_quadrada(self, x, y, z):
        """Contém (x,y) num quadrado de lado `lado` cujo canto central é (cx,cy).
        Para lado 4: x em [cx-1, cx+2], y em [cy-1, cy+2] (a casa-alvo no quadrante central)."""
        h = z.get("lado", 4) // 2
        return (z["cx"] - h + 1) <= x <= (z["cx"] + h) and (z["cy"] - h + 1) <= y <= (z["cy"] + h)

    def _em_silencio(self, obj):
        x, y = obj.get("pos", [0, 0])
        return any(self._em_zona_quadrada(x, y, z) for z in self._zonas_ativas("silencio"))

    def _cancao_bonus(self, p, chave):
        """Bônus da Canção Heroica (bardo) — SUPRIMIDO dentro de uma área de Silêncio."""
        if self._em_silencio(p):
            return 0
        return p.get("buffs_cancao", {}).get(chave, 0)

    def _verificar_escuridao(self, atacante, alvo):
        """Modificador de visão no combate: 'normal' | 'vantagem' | 'desvantagem'."""
        if not self._zonas_ativas("escuridao"):
            return "normal"
        # Imunidade a escuridão (ex.: Devorador Orgânico) — enxerga nas trevas.
        if "escuridao" in atacante.get("immunities", []):
            return "normal"
        if not self._em_escuridao(atacante):
            return "normal"
        atacante_ve = atacante.get("visao_escuro", False)
        alvo_ve     = alvo.get("visao_escuro", False)
        if atacante_ve and not alvo_ve:
            return "vantagem"
        if not atacante_ve:
            return "desvantagem"
        return "normal"

    def _alcance_escuridao(self, atacante, alvo, alcance_original):
        """Na escuridão sem visão no escuro, o alcance efetivo cai para ≤2 quadrados."""
        if atacante.get("visao_escuro"):
            return alcance_original
        if self._verificar_escuridao(atacante, alvo) == "desvantagem":
            return min(alcance_original, 2)
        return alcance_original

    def _rolar_d20_escuridao(self, atacante, alvo):
        """d20 do animado/minion considerando a escuridão. Retorna (roll, modo)."""
        esc = self._verificar_escuridao(atacante, alvo)
        if esc == "normal":
            return random.randint(1, 20), esc
        r = [random.randint(1, 20), random.randint(1, 20)]
        return (max(r) if esc == "vantagem" else min(r)), esc

    # ── Bugbear das Sombras: helpers de combate nas trevas ──────────────────────
    def _tem_habilidade(self, m, ab_id):
        """True se o monstro possui a habilidade especial `ab_id` na ficha."""
        return any(a.get("id") == ab_id for a in m.get("special_abilities", []))

    def _sob_luz_direta(self, m):
        """True se o monstro está sob luz direta (zona 'luz'). Hoje não há fonte de
        luz no jogo — fica dormente até um efeito de luz ser adicionado (decisão do
        usuário: sem luz ambiente padrão)."""
        x, y = m.get("pos", [0, 0])
        return any(self._zona_contem(x, y, z) for z in self._zonas_ativas("luz"))

    def _luz_atk_pen(self, m):
        """Fraqueza de Luz: -2 em ataques quando o monstro está sob luz direta."""
        if self._eh_jogador(m) or not self._sob_luz_direta(m):
            return 0
        for w in m.get("weaknesses", []):
            if w.get("type") == "luz_direta":
                return w.get("atk_penalty", -2)
        return 0

    def _cacador_trevas_ca_bonus(self, m):
        """Caçador das Trevas: +2 CA enquanto o monstro está em área escura."""
        if self._eh_jogador(m):
            return 0
        return 2 if (self._tem_habilidade(m, "cacador_das_trevas") and self._em_escuridao(m)) else 0

    def _ataque_das_sombras_ativo(self, m, alvo):
        """Ataque das Sombras ativo se o monstro o possui E: está em área escura
        (Caçador das Trevas concede uso garantido) OU está oculto OU o alvo está na
        escuridão sem visão no escuro (não enxerga o bugbear)."""
        if self._eh_jogador(m) or not self._tem_habilidade(m, "ataque_das_sombras"):
            return False
        if self._tem_habilidade(m, "cacador_das_trevas") and self._em_escuridao(m):
            return True
        if m.get("oculto_sombras"):
            return True
        if self._em_escuridao(alvo) and not alvo.get("visao_escuro"):
            return True
        return False

    def _sombras_atk_bonus(self, m, alvo):
        """Ataque das Sombras: +2 no acerto quando ativo."""
        return 2 if self._ataque_das_sombras_ativo(m, alvo) else 0

    def _sombras_dano_bonus(self, m, alvo):
        """Ataque das Sombras: +1d6 de dano (rolado) quando ativo; 0 caso contrário."""
        return roll_dice("1d6") if self._ataque_das_sombras_ativo(m, alvo) else 0

    # ── Ogro: helpers de alcance da lança, Golpe Brutal e Lento e Previsível ────
    def _lanca_no_alcance(self, m, alvo_pos):
        """Alcance da Lança Grande sem sistema de 'frente': a partir de qualquer
        casa do corpo do ogro, atinge o alvo a até 2 casas em LINHA RETA (ortogonal,
        sem parede no meio) OU a 1 casa na DIAGONAL — reproduz '2 à frente, 1 diagonal'."""
        ax, ay = alvo_pos
        for tx, ty in self._monster_tiles(m):
            dx, dy = ax - tx, ay - ty
            if dy == 0 and 1 <= abs(dx) <= 2:                       # horizontal
                if abs(dx) == 2 and self._blocks_tile(tx + (1 if dx > 0 else -1), ty):
                    continue
                return True
            if dx == 0 and 1 <= abs(dy) <= 2:                       # vertical
                if abs(dy) == 2 and self._blocks_tile(tx, ty + (1 if dy > 0 else -1)):
                    continue
                return True
            if abs(dx) == 1 and abs(dy) == 1:                       # diagonal (1)
                return True
        return False

    def _lanca_no_alcance_jogador(self, pos, m):
        """Alcance da Lança (reach) para o JOGADOR: a partir de pos atinge
        qualquer tile do monstro a até 2 casas em LINHA RETA ortogonal (sem
        parede no meio) OU a 1 casa na DIAGONAL — '2 retos, 1 diagonal'."""
        px, py = pos
        for tx, ty in self._monster_tiles(m):
            dx, dy = tx - px, ty - py
            if dy == 0 and 1 <= abs(dx) <= 2:                       # horizontal
                if abs(dx) == 2 and self._blocks_tile(px + (1 if dx > 0 else -1), py):
                    continue
                return True
            if dx == 0 and 1 <= abs(dy) <= 2:                       # vertical
                if abs(dy) == 2 and self._blocks_tile(px, py + (1 if dy > 0 else -1)):
                    continue
                return True
            if abs(dx) == 1 and abs(dy) == 1:                       # diagonal (1)
                return True
        return False

    def _cajado_no_alcance_jogador(self, pos, m):
        """Alcance do Cajado para o JOGADOR: atinge qualquer tile do monstro a 1
        casa em qualquer direção (Chebyshev 1 — inclui as 4 diagonais)."""
        px, py = pos
        for tx, ty in self._monster_tiles(m):
            if max(abs(tx - px), abs(ty - py)) == 1:
                return True
        return False

    def _em_alcance_ogro(self, m, alvo_pos):
        """True se o alvo está ao alcance de ataque do ogro (lança = alcance estendido)."""
        if m.get("reach_lanca"):
            return self._lanca_no_alcance(m, alvo_pos)
        return self._is_adjacent_to_monster(alvo_pos, m)

    def _golpe_brutal_bonus(self, m):
        """Golpe Brutal: +2 de dano no ataque marcado (flag consumida pela IA)."""
        return 2 if m.get("_golpe_brutal_ativo") else 0

    def _lento_previsivel_ca_pen(self, m):
        """Lento e Previsível: -2 de CA até o próximo turno após errar um ataque."""
        if self._eh_jogador(m):
            return 0
        return 2 if m.get("lento_previsivel_ativo") else 0

    def _loot_comida(self):
        """Comida encontrada na masmorra: Pão ou Garrafa de Água (comum, 50/50) e,
        em 5% dos casos, uma Caneca de Cerveja. Todos vão para a mochila (1 slot)."""
        if random.random() < 0.05:
            food_id = "caneca_cerveja"
        else:
            food_id = random.choice(("pao", "garrafa_agua"))
        base = next((i for i in SHOP_TAVERN if i["id"] == food_id), None)
        if not base:
            return None
        it = deepcopy(base)
        it.setdefault("item_slot", "bag")
        it.pop("price", None)   # item achado não carrega preço de loja
        return it

    def _rolar_ataque(self, atk_bonus, target_ac, vantagem=False, desvantagem=False):
        """d20_attack com vantagem/desvantagem (2d20). Vantagem+desvantagem = normal.
        Retorna (hit, roll, total, crit, descartado) — descartado=None se rolagem única."""
        if vantagem and desvantagem:
            vantagem = desvantagem = False
        if not vantagem and not desvantagem:
            h, r, t, c = d20_attack(atk_bonus, target_ac)
            return h, r, t, c, None
        a = d20_attack(atk_bonus, target_ac)
        b = d20_attack(atk_bonus, target_ac)
        usado, outro = (a, b) if (a[1] >= b[1]) == vantagem else (b, a)
        return usado[0], usado[1], usado[2], usado[3], outro[1]

    async def _aplicar_escuridao(self, caster, raio, duracao):
        """Cria uma zona de escuridão centrada no caster."""
        x, y = caster.get("pos", [0, 0])
        self.zonas_especiais.append({
            "id":      f"escuridao_{caster['id']}_{self.round_num}",
            "tipo":    "escuridao",
            "cx":      x, "cy": y, "raio": raio,
            "duracao": duracao, "ativa": True,
            "caster":  caster["id"],
        })
        await self.gm_say(f"🌑 **Escuridão** criada — raio {raio}, {duracao} rodada(s).")

    async def _processar_zonas_turno(self):
        """Decrementa a duração das zonas a cada rodada; remove e anuncia expiradas."""
        if not self.zonas_especiais:
            return
        for z in self.zonas_especiais:
            if not z.get("ativa"):
                continue
            if z.get("tipo") == "bola_fogo":
                # Zona de fogo: aplica dano da rodada (R2/R3) e avança a contagem.
                await self._processar_zona_bola_fogo(z)
            elif z.get("duracao", 0) > 0:
                z["duracao"] -= 1
                if z["duracao"] <= 0:
                    z["ativa"] = False
                    await self.gm_say(f"🌫️ A zona de {z.get('tipo','?')} se dissipou.")
        self.zonas_especiais = [z for z in self.zonas_especiais if z.get("ativa")]

    async def _processar_buffs_magicos_turno(self, alvo):
        """Tica buffs mágicos temporários no início do turno (Visão no Escuro, Invisibilidade, Regeneração)."""
        if alvo.get("visao_escuro_rodadas", 0) > 0:
            alvo["visao_escuro_rodadas"] -= 1
            if alvo["visao_escuro_rodadas"] <= 0:
                alvo["visao_escuro"] = False
                alvo.pop("visao_escuro_rodadas", None)
                await self.gm_say(f"👁️ A Visão no Escuro de **{alvo['name']}** se esvai.")
        # Invisibilidade: expira por duração.
        if alvo.get("invisivel_magico_rodadas", 0) > 0:
            alvo["invisivel_magico_rodadas"] -= 1
            if alvo["invisivel_magico_rodadas"] <= 0:
                alvo["invisivel_magico"] = False
                alvo.pop("invisivel_magico_rodadas", None)
                await self.gm_say(f"🫥 A Invisibilidade de **{alvo['name']}** termina.")
        # Proteção contra Energia: renova a absorção da rodada; expira por duração.
        if alvo.get("protecao_rodadas", 0) > 0:
            alvo["protecao_restante"] = alvo.get("protecao_max", 10)
            alvo["protecao_rodadas"] -= 1
            if alvo["protecao_rodadas"] <= 0:
                for _k in ("protecao_rodadas", "protecao_restante", "protecao_max", "protecao_tipos"):
                    alvo.pop(_k, None)
                await self.gm_say(f"🛡️ A Proteção contra Energia de **{alvo['name']}** termina.")
        # Velocidade: a cada turno renova a ação extra; expira por duração.
        if alvo.get("velocidade_rodadas", 0) > 0:
            alvo["velocidade_extra_usada"] = False
            alvo["velocidade_rodadas"] -= 1
            if alvo["velocidade_rodadas"] <= 0:
                alvo.pop("velocidade_rodadas", None)
                alvo.pop("velocidade_extra_usada", None)
                await self.gm_say(f"⚡ A Velocidade de **{alvo['name']}** termina.")
        # Regeneração: cura +1 HP/rodada da reserva.
        if alvo.get("regen_pool", 0) > 0 and alvo.get("alive"):
            if alvo["hp"] < alvo["max_hp"]:
                cura = min(alvo.get("regen_por_rodada", 1), alvo["regen_pool"])
                alvo["hp"] = min(alvo["max_hp"], alvo["hp"] + cura)
                alvo["regen_pool"] -= cura
                await self.gm_say(f"🌿 Regeneração cura **{alvo['name']}** +{cura} ({alvo['hp']}/{alvo['max_hp']}; reserva {alvo['regen_pool']}).")
            if alvo["regen_pool"] <= 0:
                alvo.pop("regen_pool", None); alvo.pop("regen_ressurge", None)

    def _rolar_dado(self, expressao):
        """Rola uma expressão de dados; ints passam direto. Aceita 'NdM',
        'NdM±K' e múltiplos termos — delega ao roll_dice robusto. Clampa em 0."""
        if isinstance(expressao, int):
            return expressao
        return max(0, roll_dice(str(expressao)))

    def _eh_jogador(self, alvo):
        return alvo.get("id") in self.players

    def _pen(self, alvo, chave):
        """Penalidade ativa de veneno para uma chave (valor já assinado, ≤ 0)."""
        return alvo.get("penalidades", {}).get(chave, 0)

    def _moves_base(self, p):
        """Movimento do turno = spd + bônus de canção + penalidade de veneno/doença (mov)."""
        return max(0, p["spd"] + self._cancao_bonus(p, "bonus_mov")
                   + self._pen(p, "movimento") + self._doenca_mov_pen(p))

    def _veneno_save_bonus(self, alvo, tipo_save):
        """Bônus de save. Jogador e monstros novos usam saves individuais;
        monstros legados derivam do tier."""
        chave = {"fortitude": "fort", "reflexos": "ref_", "vontade": "will"}.get(tipo_save, "fort")
        if self._eh_jogador(alvo):
            return alvo.get(chave, 0)
        # Monstros novos têm saves explícitos (fort / ref_ / will)
        if chave in alvo:
            return alvo[chave]
        # Fallback legado: tier + 1
        return alvo.get("tier", 1) + 1

    def _testar_save(self, alvo, tipo_save, dificuldade, extra_mod=0):
        """Retorna (passou, d20, bonus, total). extra_mod: bônus/penalidade adicional ao save."""
        bonus = self._veneno_save_bonus(alvo, tipo_save) + self._mod_magia(alvo, "resistencia") + extra_mod
        d20   = random.randint(1, 20)
        total = d20 + bonus
        return (total >= dificuldade), d20, bonus, total

    async def _aplicar_veneno(self, alvo, veneno_id, fonte="ataque"):
        """Aplica um veneno em qualquer alvo (jogador ou monstro)."""
        veneno = VENENOS.get(veneno_id)
        if not veneno:
            return
        nome      = veneno["nome"]
        alvo_nome = alvo.get("name", "Alvo")

        # Imunidade: mortos-vivos / constructos não têm fisiologia p/ venenos.
        if not self._eh_jogador(alvo) and (
            alvo.get("undead") or alvo.get("type") in ("skeleton", "construct", "undead")
        ):
            await self.gm_say(f"🧪 **{nome}** não afeta **{alvo_nome}** (imune a venenos).")
            return

        # Fraqueza de criatura a venenos (ex: lobos/cães sofrem -2 Fort vs veneno)
        _save_pen = 0
        for _w in alvo.get("weaknesses", []):
            if _w.get("type") == "save_penalty" and _w.get("save") == veneno.get("save", "fortitude"):
                _save_pen += _w.get("bonus_flat", 0)
        save_ok, d20, sb, stot = self._testar_save(
            alvo, veneno.get("save", "fortitude"), veneno.get("dificuldade", 10), extra_mod=_save_pen)
        sb_str = f"+{sb}" if sb >= 0 else str(sb)
        pen_str = f" (fraqueza a venenos: {_save_pen:+d})" if _save_pen else ""
        await self.gm_say(
            f"🎲 **{alvo_nome}** — save {veneno.get('save','fortitude')}: "
            f"d20({d20}){sb_str}={stot} vs dif {veneno.get('dificuldade',10)}{pen_str} → "
            f"{'resistiu' if save_ok else 'falhou'}.")

        if save_ok and veneno.get("anula"):
            await self.gm_say(f"☑️ **{alvo_nome}** resistiu ao **{nome}**!")
            return

        op      = veneno.get("operacao")
        # Sensível a Venenos (ex.: Lagarto Carniceiro): magnitude E duração dobradas.
        dobro   = 2 if any(w.get("type") == "veneno_dobrado"
                           for w in alvo.get("weaknesses", [])) else 1
        if dobro > 1:
            await self.gm_say(f"🧪 **{alvo_nome}** é **sensível a venenos** — efeitos dobrados!")
        duracao = self._rolar_dado(veneno.get("duracao", 1)) * dobro
        alvo.setdefault("efeitos_veneno", [])
        alvo.setdefault("penalidades", {})

        if op == "reduzir":
            attr   = veneno["atributo"]            # 'forca' | 'constituicao'
            valor  = self._rolar_dado(veneno["valor"]) * dobro
            efeito = {"veneno_id": veneno_id, "nome": nome, "operacao": "reduzir",
                      "atributo": attr, "valor": valor, "duracao": duracao}
            if self._eh_jogador(alvo):
                attr_key = _VENENO_ATTR_MAP.get(attr, "str_")
                antes = alvo.get(attr_key, 10)
                alvo[attr_key] = max(0, antes - valor)
                efeito["attr_key"] = attr_key
                if attr == "constituicao":
                    depois     = alvo[attr_key]
                    fort_delta = get_bonus_constituicao(antes) - get_bonus_constituicao(depois)
                    hp_delta   = max(0, fort_delta * alvo.get("level", 1))
                    if hp_delta:
                        alvo["max_hp"] = max(1, alvo["max_hp"] - hp_delta)
                        alvo["hp"]     = min(alvo["hp"], alvo["max_hp"])
                        efeito["hp_delta"] = hp_delta
                    if fort_delta:
                        alvo["fort"] = alvo.get("fort", 0) - fort_delta
                        efeito["fort_delta"] = fort_delta
                    await self.gm_say(
                        f"💉 **{alvo_nome}**: CON {antes}→{alvo[attr_key]}"
                        + (f" (HP máx -{efeito['hp_delta']})" if efeito.get("hp_delta") else "") + ".")
            else:
                # Monstro: traduz FOR→menos dano, CON→menos HP máximo.
                if attr == "constituicao":
                    alvo["max_hp"] = max(1, alvo.get("max_hp", alvo.get("hp", 1)) - valor)
                    alvo["hp"]     = min(alvo.get("hp", 1), alvo["max_hp"])
                    efeito["hp_perdido"] = valor
                else:
                    alvo["penalidades"]["dano"] = alvo["penalidades"].get("dano", 0) - 1
                    efeito["pen_dano"] = 1
            alvo["efeitos_veneno"].append(efeito)
            await self.gm_say(f"☠️ **{nome}**: -{valor} de {attr} em **{alvo_nome}** por {duracao} rodada(s).")

        elif op == "penalidade":
            atribs = [(attr, val * dobro) for attr, val in veneno.get("atributos", [])]
            efeito = {"veneno_id": veneno_id, "nome": nome, "operacao": "penalidade",
                      "atributos": atribs, "duracao": duracao}
            for attr, val in atribs:
                alvo["penalidades"][attr] = alvo["penalidades"].get(attr, 0) + val
            alvo["efeitos_veneno"].append(efeito)
            await self.gm_say(f"☠️ **{nome}**: -1 ataque e -1 movimento em **{alvo_nome}** por {duracao} rodada(s).")

        elif op == "petrificar":
            if save_ok:
                # Save parcial — penalidade de falha (sem petrificar).
                dur_falha = self._rolar_dado(veneno.get("duracao_falha", 1))
                for attr, val in veneno.get("penalidade_falha", []):
                    alvo["penalidades"][attr] = alvo["penalidades"].get(attr, 0) + val
                alvo["efeitos_veneno"].append({
                    "veneno_id": veneno_id, "nome": nome, "operacao": "penalidade",
                    "atributos": list(veneno.get("penalidade_falha", [])), "duracao": dur_falha})
                await self.gm_say(f"⚠️ **{nome}**: save parcial — **{alvo_nome}** -1 movimento por {dur_falha} rodada(s).")
            else:
                pet_dur = self._rolar_dado(veneno.get("duracao", 1)) * dobro
                alvo["petrificado"]         = True
                alvo["petrificado_rodadas"] = pet_dur
                await self.gm_say(f"🗿 **{nome}**: **{alvo_nome}** petrificado por {pet_dur} rodada(s)!")

        elif op == "cegar":
            if not self._eh_jogador(alvo) and "cegueira" in alvo.get("immunities", []):
                await self.gm_say(f"🛡️ **{alvo_nome}** é **imune a cegueira**!")
                return
            if save_ok:
                dur_falha = self._rolar_dado(veneno.get("duracao_falha", 1))
                for attr, val in veneno.get("penalidade_falha", []):
                    alvo["penalidades"][attr] = alvo["penalidades"].get(attr, 0) + val
                alvo["efeitos_veneno"].append({
                    "veneno_id": veneno_id, "nome": nome, "operacao": "penalidade",
                    "atributos": list(veneno.get("penalidade_falha", [])), "duracao": dur_falha})
                await self.gm_say(f"⚠️ **{nome}**: save parcial — percepção de **{alvo_nome}** reduzida por {dur_falha} rodada(s).")
            else:
                pen = veneno.get("penalidade_ataque", -4)
                alvo["cego"]               = True
                alvo["cego_rodadas"]       = duracao
                alvo["cego_pen_ataque"]    = pen
                alvo["bloqueia_distancia"] = veneno.get("bloqueia_distancia", False)
                alvo["penalidades"]["ataque"] = alvo["penalidades"].get("ataque", 0) + pen
                await self.gm_say(f"🙈 **{nome}**: **{alvo_nome}** cego por {duracao} rodada(s) ({pen} em ataques)!")

        await self.push_state()

    async def _processar_venenos_turno(self, alvo):
        """Início do turno do alvo: tica durações, reverte efeitos expirados e
        os contadores de petrificado/cego. Seguro para jogador OU monstro."""
        alvo.setdefault("penalidades", {})
        alvo_nome = alvo.get("name", "Alvo")

        restantes = []
        for efeito in alvo.get("efeitos_veneno", []):
            efeito["duracao"] -= 1
            if efeito["duracao"] > 0:
                restantes.append(efeito)
                continue
            op = efeito.get("operacao")
            if op == "reduzir":
                if efeito.get("attr_key"):     # jogador — restaura score
                    alvo[efeito["attr_key"]] = min(25, alvo.get(efeito["attr_key"], 10) + efeito["valor"])
                    if efeito.get("hp_delta"):
                        alvo["max_hp"] += efeito["hp_delta"]
                    if efeito.get("fort_delta"):
                        alvo["fort"] = alvo.get("fort", 0) + efeito["fort_delta"]
                else:                          # monstro — desfaz tradução
                    if efeito.get("hp_perdido"):
                        alvo["max_hp"] = alvo.get("max_hp", alvo.get("hp", 1)) + efeito["hp_perdido"]
                    if efeito.get("pen_dano"):
                        alvo["penalidades"]["dano"] = alvo["penalidades"].get("dano", 0) + efeito["pen_dano"]
            elif op == "penalidade":
                for attr, val in efeito.get("atributos", []):
                    alvo["penalidades"][attr] = alvo["penalidades"].get(attr, 0) - val
            await self.gm_say(f"✅ Efeito de **{efeito.get('nome','veneno')}** expirou em **{alvo_nome}**.")
        alvo["efeitos_veneno"] = restantes

        if alvo.get("petrificado"):
            alvo["petrificado_rodadas"] = max(0, alvo.get("petrificado_rodadas", 0) - 1)
            if alvo["petrificado_rodadas"] <= 0:
                alvo["petrificado"] = False
                await self.gm_say(f"✅ **{alvo_nome}** não está mais petrificado.")
        if alvo.get("cego"):
            alvo["cego_rodadas"] = max(0, alvo.get("cego_rodadas", 0) - 1)
            if alvo["cego_rodadas"] <= 0:
                alvo["cego"] = False
                pen = alvo.pop("cego_pen_ataque", -4)
                alvo["penalidades"]["ataque"] = alvo["penalidades"].get("ataque", 0) - pen
                alvo["bloqueia_distancia"] = False
                await self.gm_say(f"✅ Cegueira expirou em **{alvo_nome}**.")

    # ── ARMADILHAS (colocáveis) ─────────────────────────────────────────────
    # Foundation do Passo 2: criar / disparar / desarmar armadilhas. Reusa os
    # helpers de veneno (_rolar_dado, _testar_save, _aplicar_veneno) e o modelo
    # de dados real (pos:[x,y], self.monsters dict, gold, fome/sede 0–100).

    def _armadilha_no_tile(self, x, y):
        """Armadilha ARMÁVEL nessa casa (ignora as já gastas/desativadas)."""
        return next((a for a in self.armadilhas
                     if a["pos"] == [x, y]
                     and not a.get("desativada") and not a.get("esgotada")), None)

    async def handle_criar_armadilha(self, pid, msg):
        """Luccas (rogue) prepara uma armadilha na própria casa ou adjacente."""
        if not self._is_turn(pid): return
        p = self.players.get(pid)
        if not p or not p["alive"]: return
        if p.get("class_id") != "rogue":
            await self.send_to(pid, {"type": "error", "msg": "Apenas Luccas pode criar armadilhas."}); return
        if p.get("petrificado"):
            await self.send_to(pid, {"type": "error", "msg": "🗿 Você está petrificado e não pode agir!"}); return
        if p.get("action_done"):
            await self.send_to(pid, {"type": "error", "msg": "Ação principal já usada neste turno."}); return

        tipo_id = msg.get("tipo")
        tipo = ARMADILHAS.get(tipo_id)
        if not tipo:
            await self.send_to(pid, {"type": "error", "msg": "Armadilha inválida."}); return

        custo_ouro = tipo.get("custo_ouro", 0)
        if p["gold"] < custo_ouro:
            await self.send_to(pid, {"type": "error", "msg": f"Ouro insuficiente — precisa {custo_ouro}🪙."}); return
        if p["fome"] < ARMADILHA_CUSTO_FOME or p["sede"] < ARMADILHA_CUSTO_SEDE:
            await self.send_to(pid, {"type": "error",
                "msg": f"Recursos insuficientes (🍖-{ARMADILHA_CUSTO_FOME} 💧-{ARMADILHA_CUSTO_SEDE})."}); return

        # Posição: casa atual ou cardinalmente adjacente.
        tx = int(msg.get("tx", p["pos"][0]))
        ty = int(msg.get("ty", p["pos"][1]))
        if not (0 <= tx < self.map_w and 0 <= ty < self.map_h) or self.tiles[ty][tx] == WALL:
            await self.send_to(pid, {"type": "error", "msg": "Posição inválida para a armadilha."}); return
        if abs(tx - p["pos"][0]) + abs(ty - p["pos"][1]) > 1:
            await self.send_to(pid, {"type": "error", "msg": "Coloque a armadilha na sua casa ou casa adjacente."}); return
        if self._armadilha_no_tile(tx, ty) or any(t["pos"] == [tx, ty] and not t["triggered"] for t in self.traps):
            await self.send_to(pid, {"type": "error", "msg": "Já existe uma armadilha nessa casa."}); return

        # Fosso envenenado: consome 1 frasco de veneno da bolsa.
        veneno_id = None
        if tipo.get("custo_veneno"):
            veneno_id = msg.get("veneno_id")
            if not veneno_id or veneno_id not in VENENOS:
                await self.send_to(pid, {"type": "error", "msg": "Escolha um veneno para o fosso."}); return
            frasco = next((i for i in p["bag"] if i.get("id") == veneno_id), None)
            if not frasco:
                await self.send_to(pid, {"type": "error", "msg": "Veneno não encontrado na bolsa."}); return
            p["bag"].remove(frasco)

        p["gold"] -= custo_ouro
        p["fome"] = max(0, p["fome"] - ARMADILHA_CUSTO_FOME)
        p["sede"] = max(0, p["sede"] - ARMADILHA_CUSTO_SEDE)
        p["action_done"] = True

        self._armadilha_seq += 1
        self.armadilhas.append({
            "id":        f"arm_{self._armadilha_seq}_{tx}_{ty}",
            "tipo":      tipo_id,
            "pos":       [tx, ty],
            "criador":   pid,             # pid do aliado que colocou
            "visivel":   False,           # já foi revelada/disparada?
            "ativada":   False,
            "veneno_id": veneno_id,
            "efeitos_ativos": [],         # dano progressivo agendado (incendiária)
        })
        await self.gm_say(f"🪤 **{p['name']}** prepara **{tipo['nome']}** em ({tx},{ty}).")
        await self.push_state()

    async def _disparar_armadilha(self, alvo, arm):
        """Dispara a armadilha sobre `alvo` (jogador OU monstro)."""
        tipo = ARMADILHAS.get(arm["tipo"])
        if not tipo or arm.get("desativada") or arm.get("esgotada"):
            return
        nome = tipo["nome"]
        alvo_nome = alvo.get("name") or alvo.get("nome", "Alvo")
        await self.gm_say(f"⚠️ **{alvo_nome}** ativou **{nome}**!")

        if tipo.get("area"):
            await self._aplicar_armadilha_area(arm, tipo)
        else:
            save_ok, d20, sb, stot = self._testar_save(alvo, tipo["save"], tipo["dificuldade"])
            sb_str = f"+{sb}" if sb >= 0 else str(sb)
            await self.broadcast({"type": "dice_roll", "die": "d20", "value": d20,
                                  "label": f"{alvo_nome} — {tipo['save']}"})
            await self.gm_say(f"🎲 Save {tipo['save']}: d20({d20}){sb_str}={stot} vs dif "
                              f"{tipo['dificuldade']} → {'evitou' if save_ok else 'falhou'}.")
            if not save_ok:
                for ef in tipo["efeitos"]:
                    await self._aplicar_efeito_armadilha(alvo, ef, arm)
            else:
                await self.gm_say(f"✅ **{alvo_nome}** evitou **{nome}** sem dano!")

        # Persistência / visibilidade.
        if tipo.get("persiste"):
            arm["ativada"] = True
            if tipo.get("visivel_apos"):
                arm["visivel"] = True
        elif arm.get("efeitos_ativos"):
            arm["esgotada"] = True   # já disparou; mantém só p/ dano residual (incendiária)
        else:
            self.armadilhas = [a for a in self.armadilhas if a["id"] != arm["id"]]

    async def _aplicar_armadilha_area(self, arm, tipo):
        """Armadilhas de área (mina/gás): cada alvo no raio testa o próprio save."""
        cx, cy = arm["pos"]
        r = tipo.get("area", 1)
        alvos = [p for p in self.players.values()
                 if p["alive"] and abs(p["pos"][0]-cx) <= r and abs(p["pos"][1]-cy) <= r]
        alvos += [m for m in self.monsters.values()
                  if m["hp"] > 0 and abs(m["pos"][0]-cx) <= r and abs(m["pos"][1]-cy) <= r]
        for alvo in alvos:
            alvo_nome = alvo.get("name") or alvo.get("nome", "Alvo")
            save_ok, d20, sb, stot = self._testar_save(alvo, tipo["save"], tipo["dificuldade"])
            await self.broadcast({"type": "dice_roll", "die": "d20", "value": d20,
                                  "label": f"{alvo_nome} — {tipo['save']}"})
            if save_ok and not tipo.get("save_reduz"):
                await self.gm_say(f"✅ **{alvo_nome}** evitou **{tipo['nome']}**!")
                continue
            metade = bool(save_ok and tipo.get("save_reduz"))
            for ef in tipo["efeitos"]:
                await self._aplicar_efeito_armadilha(alvo, {**ef, "metade": metade}, arm)

    async def _aplicar_efeito_armadilha(self, alvo, ef, arm):
        tipo_ef = ef.get("tipo")
        alvo_nome = alvo.get("name") or alvo.get("nome", "Alvo")

        if tipo_ef == "dano":
            if ef.get("rodada", 1) > 1:
                # Dano progressivo: agenda p/ rodadas seguintes (ver _processar_efeitos_armadilha_turno).
                arm.setdefault("efeitos_ativos", []).append({
                    "alvo_id": alvo.get("id"), "valor": ef["valor"],
                    "elemento": ef.get("elemento", "fisico"), "rodadas_restantes": ef["rodada"] - 1,
                })
                return
            dano = self._rolar_dado(ef["valor"])
            if ef.get("metade"):
                dano = max(1, dano // 2)
            await self._dano_em_alvo(alvo, dano, ef.get("elemento", "fisico"), arm.get("criador"))

        elif tipo_ef == "perder_movimento":
            alvo["moves_left"] = 0
            alvo["movimento_perdido"] = True
            await self.gm_say(f"🦵 **{alvo_nome}** perde o movimento!")

        elif tipo_ef == "perder_rodada":
            alvo["moves_left"] = 0
            if self._eh_jogador(alvo):
                alvo["action_done"] = True
                alvo["bonus_action_used"] = True
            else:
                alvo["perde_turno"] = True
            await self.gm_say(f"⏸️ **{alvo_nome}** perde a rodada inteira!")

        elif tipo_ef == "veneno":
            if arm.get("veneno_id"):
                await self._aplicar_veneno(alvo, arm["veneno_id"], fonte="armadilha")

        elif tipo_ef == "reduzir_con":
            valor = self._rolar_dado(ef["valor"])
            if ef.get("metade"):
                valor = max(1, valor // 2)
            await self._reduzir_con_temporario(alvo, valor, ef.get("duracao", 3))

    async def _dano_em_alvo(self, alvo, dano, elemento, killer_pid=None):
        """Subtrai HP e trata morte de jogador / monstro / animado."""
        alvo_nome = alvo.get("name") or alvo.get("nome", "Alvo")
        if "vida_atual" in alvo:    # animado (servo do mago / elemental)
            dano = self._ajustar_dano_elemental(alvo, dano, elemento)   # resistências do elemental
            alvo["vida_atual"] = max(0, alvo["vida_atual"] - dano)
            await self.gm_say(f"💥 **{alvo_nome}** sofre **{dano}** de dano ({elemento}).")
            if alvo["vida_atual"] <= 0:
                await self._animado_morre(alvo, killer_pid)
            return
        alvo["hp"] = max(0, alvo.get("hp", 0) - dano)
        await self.gm_say(f"💥 **{alvo_nome}** sofre **{dano}** de dano ({elemento}) "
                          f"({alvo['hp']}/{alvo.get('max_hp', '?')} HP).")
        if alvo["hp"] <= 0:
            if self._eh_jogador(alvo):
                await self._player_dies(alvo["id"])
            else:
                await self._monster_dies(alvo, killer_pid)

    async def _reduzir_con_temporario(self, alvo, valor, duracao):
        """Reduz CON por N rodadas (nuvem de gás). Registra em efeitos_veneno p/
        reverter automaticamente em _processar_venenos_turno (mesmo shape do veneno)."""
        alvo.setdefault("efeitos_veneno", [])
        alvo.setdefault("penalidades", {})
        alvo_nome = alvo.get("name") or alvo.get("nome", "Alvo")
        efeito = {"nome": "Nuvem de Gás", "operacao": "reduzir",
                  "atributo": "constituicao", "valor": valor, "duracao": duracao}
        if self._eh_jogador(alvo):
            antes = alvo.get("con_", 10)
            alvo["con_"] = max(0, antes - valor)
            efeito["attr_key"] = "con_"
            fort_delta = get_bonus_constituicao(antes) - get_bonus_constituicao(alvo["con_"])
            hp_delta = max(0, fort_delta * alvo.get("level", 1))
            if hp_delta:
                alvo["max_hp"] = max(1, alvo["max_hp"] - hp_delta)
                alvo["hp"] = min(alvo["hp"], alvo["max_hp"])
                efeito["hp_delta"] = hp_delta
            if fort_delta:
                alvo["fort"] = alvo.get("fort", 0) - fort_delta
                efeito["fort_delta"] = fort_delta
        else:
            alvo["max_hp"] = max(1, alvo.get("max_hp", alvo.get("hp", 1)) - valor)
            alvo["hp"] = min(alvo.get("hp", 1), alvo["max_hp"])
            efeito["hp_perdido"] = valor
        alvo["efeitos_veneno"].append(efeito)
        await self.gm_say(f"🌫️ **{alvo_nome}**: -{valor} de CON por {duracao} rodada(s).")

    async def handle_desarmar_armadilha(self, pid, msg):
        """Luccas desarma uma armadilha na própria casa ou adjacente (teste de DES)."""
        if not self._is_turn(pid): return
        p = self.players.get(pid)
        if not p or not p["alive"]: return
        if p.get("action_done"):
            await self.send_to(pid, {"type": "error", "msg": "Ação principal já usada neste turno."}); return

        arm = self._armadilha_no_tile(p["pos"][0], p["pos"][1])
        if not arm:
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                arm = self._armadilha_no_tile(p["pos"][0] + dx, p["pos"][1] + dy)
                if arm: break
        if not arm:
            await self.send_to(pid, {"type": "error", "msg": "Nenhuma armadilha adjacente para desarmar."}); return

        tipo = ARMADILHAS.get(arm["tipo"], {})
        dif = tipo.get("dificuldade", 10)
        d20 = random.randint(1, 20)
        bonus = mod(p.get("dex", 10))
        total = d20 + bonus
        p["action_done"] = True
        await self.broadcast({"type": "dice_roll", "die": "d20", "value": d20, "label": f"{p['name']} — Desarmar"})
        await self.gm_say(f"🔧 **{p['name']}** tenta desarmar **{tipo.get('nome', arm['tipo'])}**: "
                          f"d20({d20})+DES({bonus})={total} vs dif {dif}.")
        if d20 == 1:
            await self.gm_say("💀 Falha crítica! A armadilha dispara no próprio Luccas!")
            await self._disparar_armadilha(p, arm)
        elif total >= dif:
            self.armadilhas = [a for a in self.armadilhas if a["id"] != arm["id"]]
            await self.gm_say("✅ Armadilha desarmada com sucesso!")
        else:
            await self.gm_say(f"❌ Falha no desarme ({total} vs {dif}) — tente de novo no próximo turno.")
        await self.push_state()

    # ── HABILIDADES DO LADINO (Luccas) ──────────────────────────────────────
    # Detectar Armadilhas / Esconder nas Sombras (alternáveis) e Veneno Rápido
    # (ação livre). Reusam o sistema de venenos (weapon_poison/VENENO_CARGAS), a
    # revelação por self.explored e o gate "detect_trap" de handle_move.

    def _revelar_armadilhas_luccas(self, p):
        """Revela (adiciona a self.explored) as armadilhas de masmorra não
        disparadas dentro do raio de visão de Luccas. Retorna quantas revelou."""
        raio = self._get_raio_visao(p)
        px, py = p["pos"]
        reveladas = 0
        for tr in self.traps:
            if tr["triggered"]:
                continue
            if max(abs(tr["pos"][0] - px), abs(tr["pos"][1] - py)) <= raio \
               and tuple(tr["pos"]) not in self.explored:
                self.explored.add(tuple(tr["pos"]))
                reveladas += 1
        return reveladas

    async def handle_detectar_armadilhas(self, pid, msg):
        """Luccas alterna a Detecção de Armadilhas (ação bônus). Enquanto ativa,
        revela armadilhas próximas e não dispara as da masmorra. Manutenção 💧-1/turno."""
        if not self._is_turn(pid): return
        p = self.players.get(pid)
        if not p or not p["alive"]: return
        if p.get("class_id") != "rogue":
            await self.send_to(pid, {"type": "error", "msg": "Apenas Luccas pode detectar armadilhas."}); return
        if p.get("petrificado"):
            await self.send_to(pid, {"type": "error", "msg": "🗿 Você está petrificado e não pode agir!"}); return

        # Alternar OFF (gratuito) — encerra a detecção.
        if p.get("detectar_ativo"):
            p["detectar_ativo"] = False
            if "detect_trap" in p.get("status", []):
                p["status"].remove("detect_trap")
            await self.gm_say(f"🔍 **{p['name']}** desativa a detecção de armadilhas.")
            await self.push_state(); return

        # Alternar ON — consome a ação bônus do turno (sem custo de recurso na ativação).
        if p.get("bonus_action_used"):
            await self.send_to(pid, {"type": "error", "msg": "Ação bônus já usada neste turno."}); return
        p["bonus_action_used"] = True
        p["detectar_ativo"] = True
        if "detect_trap" not in p.setdefault("status", []):
            p["status"].append("detect_trap")
        reveladas = self._revelar_armadilhas_luccas(p)
        await self.gm_say(
            f"🔍 **{p['name']}** ativa a Detecção de Armadilhas — "
            f"{reveladas} armadilha(s) revelada(s). (manutenção 💧-1/turno)")
        await self.push_state()

    async def _cobrar_manutencao_detectar(self, p):
        """Upkeep da Detecção de Armadilhas no início do turno de Luccas."""
        if not p.get("detectar_ativo"):
            return
        if p["sede"] < 1:
            p["detectar_ativo"] = False
            if "detect_trap" in p.get("status", []):
                p["status"].remove("detect_trap")
            await self.gm_say(f"🔍 Detecção de **{p['name']}** cessa — sede insuficiente.")
            return
        p["sede"] = max(0, p["sede"] - 1)
        self._revelar_armadilhas_luccas(p)

    async def handle_esconder_sombras(self, pid, msg):
        """Luccas tenta se esconder nas sombras (ação bônus). Em sucesso, fica
        invisível (monstros não o escolhem como alvo) até atacar/mover. Garante
        Ataque Furtivo no próximo golpe. Manutenção 🍖-1 💧-1/turno."""
        if not self._is_turn(pid): return
        p = self.players.get(pid)
        if not p or not p["alive"]: return
        if p.get("class_id") != "rogue":
            await self.send_to(pid, {"type": "error", "msg": "Apenas Luccas pode usar esta habilidade."}); return
        if p.get("petrificado"):
            await self.send_to(pid, {"type": "error", "msg": "🗿 Você está petrificado e não pode agir!"}); return

        # Alternar OFF (gratuito) — sai das sombras.
        if p.get("invisivel_sombras"):
            p["invisivel_sombras"] = False
            await self.gm_say(f"🌑 **{p['name']}** sai das sombras.")
            await self.push_state(); return

        if p.get("bonus_action_used"):
            await self.send_to(pid, {"type": "error", "msg": "Ação bônus já usada neste turno."}); return
        custo_fome, custo_sede = 2, 1
        if p["fome"] < custo_fome or p["sede"] < custo_sede:
            await self.send_to(pid, {"type": "error",
                "msg": f"Recursos insuficientes (🍖-{custo_fome} 💧-{custo_sede})."}); return

        # Dificuldade = percepção do monstro mais atento + nº de monstros na sala.
        monstros = [m for m in self.monsters.values() if m["hp"] > 0]
        percepcao = max((m.get("percepcao", 10) for m in monstros), default=8)
        dificuldade = percepcao + len(monstros)

        d20 = random.randint(1, 20)
        bonus_dex = mod(p.get("dex", 10))
        total = d20 + bonus_dex

        # Custo é pago independentemente do resultado (gasto o fôlego ao tentar).
        p["fome"] = max(0, p["fome"] - custo_fome)
        p["sede"] = max(0, p["sede"] - custo_sede)
        p["bonus_action_used"] = True

        sucesso = total >= dificuldade
        await self.broadcast({"type": "dice_roll", "die": "d20", "value": d20,
                               "label": f"{p['name']} — Furtividade", "hit": sucesso})
        if sucesso:
            p["invisivel_sombras"] = True
            await self.gm_say(
                f"🌑 **{p['name']}** desaparece nas sombras! "
                f"(d20={d20}+{bonus_dex}={total} vs {dificuldade}) — "
                f"invisível até agir. Manutenção 🍖-1 💧-1/turno.")
        else:
            await self.gm_say(
                f"❌ **{p['name']}** falha em se esconder "
                f"(d20={d20}+{bonus_dex}={total} vs {dificuldade}).")
        await self.push_state()

    async def _cobrar_manutencao_sombras(self, p):
        """Upkeep do Esconder nas Sombras no início do turno de Luccas."""
        if not p.get("invisivel_sombras"):
            return
        if p["fome"] < 1 or p["sede"] < 1:
            p["invisivel_sombras"] = False
            await self.gm_say(f"🌑 **{p['name']}** sai das sombras — sem fôlego para se manter oculto.")
            return
        p["fome"] = max(0, p["fome"] - 1)
        p["sede"] = max(0, p["sede"] - 1)

    async def handle_veneno_rapido(self, pid, msg):
        """Veneno Rápido (ação livre): unta um veneno da bolsa na arma. Reusa o
        sistema weapon_poison/VENENO_CARGAS — os próximos golpes certeiros envenenam.
        Custa apenas 💧-1 (não consome ação principal nem bônus)."""
        if not self._is_turn(pid): return
        p = self.players.get(pid)
        if not p or not p["alive"]: return
        if p.get("class_id") != "rogue":
            await self.send_to(pid, {"type": "error", "msg": "Apenas Luccas pode usar Veneno Rápido."}); return
        if p.get("petrificado"):
            await self.send_to(pid, {"type": "error", "msg": "🗿 Você está petrificado e não pode agir!"}); return

        custo_sede = 1
        if p["sede"] < custo_sede:
            await self.send_to(pid, {"type": "error", "msg": f"Sede insuficiente (💧-{custo_sede})."}); return

        veneno_id = msg.get("veneno_id")
        frasco = next((i for i in p["bag"]
                       if (i.get("veneno_id") == veneno_id or i.get("id") == veneno_id)
                       and i.get("veneno_id") in VENENOS), None)
        if not frasco:
            await self.send_to(pid, {"type": "error", "msg": "Veneno não encontrado na bolsa."}); return

        vid = frasco["veneno_id"]
        p["bag"].remove(frasco)
        p["sede"] = max(0, p["sede"] - custo_sede)
        _w_id = (p.get("weapon") or {}).get("id", "")
        _is_ranged = _w_id in RANGED_AMMO
        cargas = VENENO_CARGAS if _is_ranged else 1
        p["weapon_poison"]      = vid
        p["weapon_poison_hits"] = cargas
        desc_veneno = (f"os próximos {VENENO_CARGAS} disparos (acerto ou erro) transferem o veneno"
                       if _is_ranged
                       else "o próximo golpe certeiro envenena o alvo")
        await self.gm_say(
            f"☠️ **{p['name']}** aplica **{VENENOS[vid]['nome']}** na arma (ação livre) — "
            f"{desc_veneno}! 💧-{custo_sede}")
        await self.push_state()

    async def _processar_inicio_turno_luccas(self, p):
        """Upkeep das habilidades alternáveis de Luccas no início do seu turno."""
        if p.get("class_id") != "rogue" or not p["alive"]:
            return
        await self._cobrar_manutencao_detectar(p)
        await self._cobrar_manutencao_sombras(p)

    async def _processar_efeitos_armadilha_turno(self):
        """Tica o dano progressivo (incendiária) uma vez por rodada."""
        for arm in list(self.armadilhas):
            restantes = []
            for ef in arm.get("efeitos_ativos", []):
                alvo = self.players.get(ef["alvo_id"]) or self.monsters.get(ef["alvo_id"])
                if alvo and (alvo.get("alive") or alvo.get("hp", 0) > 0):
                    dano = self._rolar_dado(ef["valor"])
                    await self._dano_em_alvo(alvo, dano, ef.get("elemento", "fogo"), arm.get("criador"))
                ef["rodadas_restantes"] -= 1
                if ef["rodadas_restantes"] > 0:
                    restantes.append(ef)
            arm["efeitos_ativos"] = restantes
        # Remove armadilhas gastas sem dano residual pendente.
        self.armadilhas = [a for a in self.armadilhas
                           if not (a.get("esgotada") and not a.get("efeitos_ativos"))]

    def _serializar_armadilhas(self):
        """Estado das armadilhas para o cliente. Armadilhas de aliado são visíveis
        a todos os jogadores (para não pisarem); monstros não recebem game_state."""
        out = []
        for a in self.armadilhas:
            if a.get("esgotada"):
                continue
            tipo = ARMADILHAS.get(a["tipo"], {})
            out.append({
                "id":      a["id"],
                "tipo":    a["tipo"],
                "pos":     a["pos"],
                "icone":   tipo.get("icone", "🪤"),
                "nome":    tipo.get("nome", a["tipo"]),
                "visivel": a.get("visivel", False),
                "ativada": a.get("ativada", False),
                "aliada":  a.get("criador") in self.players,
                "so_luccas": False,   # reservado p/ armadilhas de masmorra detectadas (futuro)
            })
        return out

    async def handle_use_item(self, pid, item_id):
        if not self._is_turn(pid): return
        p = self.players[pid]
        item = next((i for i in p["bag"] if i["id"] == item_id), None)
        if not item:
            await self.send_to(pid, {"type": "error", "msg": "Item não encontrado."}); return

        effect, val = item["effect"], item.get("value", 0)

        # Pergaminhos exigem mira — usados pelo fluxo dedicado (use_scroll).
        if effect == "scroll":
            await self.handle_use_scroll(pid, item_id, {})
            return

        # Vela da Escuridão não acumula com outras furtividades — valida ANTES de
        # gastar a ação bônus (senão o jogador perderia a ação à toa).
        if effect == "veil_shadow" and (p.get("invisivel_sombras") or
                                        p.get("invisivel_magico") or p.get("oculto_vela")):
            await self.send_to(pid, {"type": "error",
                "msg": "Você já está furtivo — a vela não acumula com outro efeito de furtividade."})
            return

        # Itens consumíveis de bolsa são ações bônus — verificar antes de aplicar
        if effect in self.BONUS_ACTION_EFFECTS:
            ok = await self._executar_acao_bonus(p)
            if not ok:
                return  # já usou ação bônus neste turno — abortar sem consumir o item

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
        elif effect == "coat_poison":
            vid = item.get("veneno_id")
            if vid not in VENENOS:
                await self.send_to(pid, {"type": "error", "msg": "Veneno desconhecido."}); return
            _w_id = (p.get("weapon") or {}).get("id", "")
            _is_ranged = _w_id in RANGED_AMMO
            cargas = VENENO_CARGAS if _is_ranged else 1
            p["weapon_poison"]      = vid
            p["weapon_poison_hits"] = cargas
            desc = (f"{VENENO_CARGAS} disparos (acerto ou erro) envenenam o alvo"
                    if _is_ranged else "1 golpe certeiro envenena o alvo")
            await self.gm_say(
                f"{item['emoji']} **{p['name']}** unta **{item['name']}** na arma — "
                f"{desc}!")
        elif effect == "wine":
            p["fome"] = min(100, p.get("fome", 0) + val)
            p["sede"] = min(100, p.get("sede", 0) + val)
            # Penalidade -1 ataque / -1 Reflexos por 10 rodadas (não acumula: reinicia).
            if not p.get("vinho_ativo"):
                p["vinho_ativo"] = True
                p["atk_bonus"]  -= 1
                p["ref_"]       -= 1
            p["vinho_rodadas"] = 10
            await self.gm_say(
                f"{item['emoji']} **{p['name']}** vira a **{item['name']}** (+{val} fome/sede), "
                f"mas fica embriagado: **-1 ataque / -1 Reflexos** por 10 rodadas!")
        elif effect == "ration":
            p["fome"] = min(100, p.get("fome", 0) + val)
            p["sede"] = min(100, p.get("sede", 0) + val)
            self._verificar_estado_sobrevivencia(p)
            await self.gm_say(
                f"{item['emoji']} **{p['name']}** come a **{item['name']}**: +{val} fome e +{val} sede.")
        elif effect == "food":
            # Provisão genérica da taverna: restaura fome e/ou sede (campos no item).
            fome = item.get("fome", 0)
            sede = item.get("sede", 0)
            p["fome"] = min(100, p.get("fome", 0) + fome)
            p["sede"] = min(100, p.get("sede", 0) + sede)
            self._verificar_estado_sobrevivencia(p)
            partes = []
            if fome: partes.append(f"+{fome} fome")
            if sede: partes.append(f"+{sede} sede")
            await self.gm_say(
                f"{item['emoji']} **{p['name']}** consome **{item['name']}**: {' e '.join(partes)}.")
        elif effect == "ale":
            # Caneca de Cerveja: +fome/sede, mas embriaga (-1 ataque por 10 rodadas).
            p["fome"] = min(100, p.get("fome", 0) + val)
            p["sede"] = min(100, p.get("sede", 0) + val)
            if not p.get("cerveja_ativo"):
                p["cerveja_ativo"] = True
                p["atk_bonus"]    -= 1
            p["cerveja_rodadas"] = 10
            self._verificar_estado_sobrevivencia(p)
            await self.gm_say(
                f"{item['emoji']} **{p['name']}** vira a **{item['name']}** (+{val} fome/sede), "
                f"mas fica alegre: **-1 ataque** por 10 rodadas!")
        elif effect == "veil_shadow":
            # Acende a vela: oculto até o fim do turno. Ladino → Ataque Furtivo
            # automático; demais → próximo ataque com vantagem (ver handle_attack).
            p["oculto_vela"] = True
            if p.get("class_id") == "rogue":
                extra = " — seu próximo ataque é um **Ataque Furtivo** automático!"
            else:
                extra = " — seu próximo ataque tem **vantagem**!"
            await self.gm_say(
                f"{item['emoji']} **{p['name']}** acende a **{item['name']}**, e a luz "
                f"em volta é sugada: fica **oculto** até o fim do turno{extra}")

        p["bag"].remove(item)
        await self.push_state()

    # ── Pergaminhos mágicos ─────────────────────────────────────────────────────
    def _inimigo_mais_proximo(self, p):
        vivos = [m for m in self.monsters.values() if m["hp"] > 0]
        if not vivos:
            return None
        return min(vivos, key=lambda m: max(abs(m["pos"][0] - p["pos"][0]),
                                            abs(m["pos"][1] - p["pos"][1])))

    def _magia_tipo(self, magia):
        """Classifica a magia para o efeito nocivo do pergaminho."""
        mid = magia["id"]
        if self._magia_tem_dano(magia):
            return "dano"
        if mid in ("amaldicoar", "sono", "medo", "comando", "dominar_mente",
                   "dominar_morto_vivo", "lentidao") or "debuff" in magia:
            return "debuff"
        if mid in ("silencio", "manto_escuridao"):
            return "zona"
        if mid == "conjurar_elemental":
            return "invocacao"
        if mid in ("abencoar", "abencoar_arma", "visao_escuro", "invisibilidade",
                   "regeneracao_magica", "velocidade", "protecao_energia",
                   "barreira_arcana", "contramagica") or "buff" in magia:
            return "buff"
        return "utilidade"

    async def _pergaminho_conjurar(self, p, magia, data, nivel, int_bonus, talentos=None):
        """Conjura a magia do pergaminho com o NÍVEL de conjurador e o BÔNUS de INT
        marcados no item (escala dano/alcance e CD = 8+bônus+círculo), restaurando
        os do personagem ao final. A metamagia do USUÁRIO não afeta pergaminhos —
        só os talentos JÁ GRAVADOS no item (cd/duração/dano ×1.5) valem."""
        t = talentos or {}
        dmg_mult  = 1.5 if t.get("dano") else 1
        dur_bonus = 1 if t.get("duracao") else 0
        dc_bonus  = 1 if t.get("cd") else 0
        lv0, int0, dc0 = p.get("level", 1), p.get("int_", 10), p.get("_mm_dc_bonus", 0)
        p["level"]        = nivel
        p["int_"]         = 10 + 2 * int_bonus   # mod(int_) == int_bonus
        p["_mm_dc_bonus"] = dc_bonus             # talento Aprimorar gravado (+1 CD)
        try:
            await self._executar_magia_grimorio(p, magia, data or {}, dmg_mult, dur_bonus)
        finally:
            p["level"], p["int_"], p["_mm_dc_bonus"] = lv0, int0, dc0

    async def _pergaminho_invocar_hostil(self, p):
        """Invocação que dá errado: surge uma criatura hostil aos jogadores."""
        sala = next((r for r in self.rooms if r.get("id") == p.get("room_id")),
                    {"id": p.get("room_id"), "cx": p["pos"][0], "cy": p["pos"][1]})
        comp_def = next((d for d in MONSTER_DEFS if d["type"] == "aranha_sombria"), None)
        if not comp_def:
            await self.gm_say("🌫️ A invocação falha sem se materializar."); return
        m = make_monster(comp_def, sala)
        m["pos"] = list(p["pos"])
        m["name"] = "Elemental Descontrolado"
        self.monsters[m["id"]] = m
        await self.gm_say(f"😈 A invocação do pergaminho surge **HOSTIL** perto de **{p['name']}**!")

    async def _pergaminho_efeito_nocivo(self, p, magia, data, nivel, int_bonus, talentos=None):
        """Efeito nocivo genérico (decisão do projeto): dano/debuff/zona miram o
        próprio jogador; buff vai para o inimigo mais próximo; invocação fica hostil.
        Os talentos gravados continuam valendo (a magia 'turbinada' machuca mais)."""
        tipo = self._magia_tipo(magia)
        px, py = p["pos"]
        if tipo in ("dano", "debuff", "zona"):
            d = {"tx": px, "ty": py, "target_id": p["id"], "dir": [0, 1]}
            await self.gm_say(f"☠️ **{magia['nome']}** se volta contra **{p['name']}**!")
            await self._pergaminho_conjurar(p, magia, d, nivel, int_bonus, talentos)
        elif tipo == "buff":
            inimigo = self._inimigo_mais_proximo(p)
            if inimigo:
                buff = magia.get("buff") or {"ataque": 1, "dano": 1, "ca": 1, "resistencia": 1}
                self._set_mod_magia(inimigo, buff, 3)
                await self.gm_say(
                    f"😈 **{magia['nome']}** beneficia o inimigo **{inimigo['name']}** por engano!")
            else:
                await self.gm_say(f"🌫️ **{magia['nome']}** se dissipa sem alvo.")
        elif tipo == "invocacao":
            await self._pergaminho_invocar_hostil(p)
        else:
            await self.gm_say(f"🌫️ **{magia['nome']}** falha e a energia se perde inutilmente.")

    async def handle_use_scroll(self, pid, item_id, data=None):
        """Usa um pergaminho: rola falha (classe + nível), conjura no sucesso ou
        aplica efeito nocivo na falha. Gasta a ação e o pergaminho (sempre)."""
        if not self._is_turn(pid):
            return
        p = self.players.get(pid)
        if not p or not p["alive"]:
            return
        if p.get("class_id") not in ("mage", "cleric"):
            await self.send_to(pid, {"type": "error",
                "msg": "Apenas mago ou clérigo conseguem usar pergaminhos mágicos."}); return
        scroll = next((i for i in p["bag"]
                       if i.get("id") == item_id and i.get("effect") == "scroll"), None)
        if not scroll:
            await self.send_to(pid, {"type": "error", "msg": "Pergaminho não encontrado."}); return
        if self._acao_bloqueada(p):
            await self.send_to(pid, {"type": "error", "msg": "Ação principal já usada neste turno."}); return
        if p.get("petrificado") or p.get("paralisado") or p.get("dormindo"):
            await self.send_to(pid, {"type": "error", "msg": "Você não consegue conjurar agora."}); return
        if self._em_silencio(p):
            await self.send_to(pid, {"type": "error", "msg": "🔇 Você está em área de Silêncio — não pode conjurar!"}); return
        magia = GRIMORIO.get(scroll.get("magia_id"))
        if not magia:
            await self.send_to(pid, {"type": "error", "msg": "Magia do pergaminho desconhecida."}); return

        nivel = scroll.get("nivel_conjurador", 1)
        int_b = scroll.get("int_bonus", 0)
        talentos = {"cd": scroll.get("talento_cd"), "duracao": scroll.get("talento_duracao"),
                    "dano": scroll.get("talento_dano")}
        # Consome a AÇÃO e o pergaminho — sempre (sucesso, falha ou nocivo).
        p["action_done"] = True
        try:
            p["bag"].remove(scroll)
        except ValueError:
            pass

        await self.gm_say(f"📜 **{p['name']}** usa **{scroll['name']}**...")

        falhou, motivos = False, []
        # 1) Falha de classe (50%) — magia exclusiva da OUTRA classe.
        if p["class_id"] not in magia.get("classe", []):
            rc = random.randint(1, 100)
            if rc <= 50:
                falhou = True; motivos.append(f"classe errada (d100={rc}≤50%)")
            else:
                motivos.append(f"classe ok (d100={rc}>50%)")
        # 2) Falha por nível — (nível do pergaminho − nível do personagem) × 15% (teto 95%).
        diff = max(0, nivel - p.get("level", 1))
        chance = min(PERGAMINHO_FALHA_MAX, diff * 15)
        if chance > 0:
            rn = random.randint(1, 100)
            if rn <= chance:
                falhou = True; motivos.append(f"nível (d100={rn}≤{chance}%)")
            else:
                motivos.append(f"nível ok (d100={rn}>{chance}%)")

        if not falhou:
            extra = f" ({'; '.join(motivos)})" if motivos else ""
            await self.gm_say(f"✨ Conjuração **bem-sucedida**!{extra}")
            await self._pergaminho_conjurar(p, magia, data or {}, nivel, int_b, talentos)
        else:
            harm = min(PERGAMINHO_FALHA_MAX, diff * 5)
            rh = random.randint(1, 100) if harm > 0 else 100
            if harm > 0 and rh <= harm:
                await self.gm_say(
                    f"💥 A magia **falha** e provoca um **efeito nocivo**! "
                    f"({'; '.join(motivos)}; nocivo d100={rh}≤{harm}%)")
                await self._pergaminho_efeito_nocivo(p, magia, data or {}, nivel, int_b, talentos)
            else:
                await self.gm_say(f"🌫️ O pergaminho **falha** e a energia se dissipa. ({'; '.join(motivos)})")

        await self.push_state()

    async def handle_end_turn(self, pid):
        if not self._is_turn(pid): return
        p = self.players[pid]
        # Limpa imobilização (teia/rede) — o jogador encerrou o turno bloqueado
        p.pop("perde_turno", None)
        p.pop("oculto_vela", None)   # Vela da Escuridão: oculto dura só até o fim do turno

        # ── Turno dos servos: logo após o mago jogar, ele controla os animados ──
        # O primeiro "encerrar turno" abre a janela dos servos (sem avançar); o
        # próximo "encerrar turno" passa adiante.
        # Controle progressivo (Dominar Morto-Vivo): re-teste de Vontade ao abrir a fase.
        if self.animados_phase_pid != pid:
            await self._retestar_dominacao_jogador(p)
        # Animados roubados por um necromante não obedecem o jogador nesta fase.
        animados_vivos = [a for a in p.get("animados", [])
                          if a.get("vida_atual", 0) > 0 and not a.get("dominado_por_monstro")]
        if animados_vivos and self.animados_phase_pid != pid:
            self.animados_phase_pid = pid
            # Upkeep: cada cadáver reanimado custa -1 fome e -1 sede por turno.
            custo = len(animados_vivos)
            p["fome"] = max(0, p.get("fome", 10) - custo)
            p["sede"] = max(0, p.get("sede", 10) - custo)
            for a in animados_vivos:               # orçamento p/ a janela de controle
                a["moves_left"] = a.get("movimento", 3)
                a["acted"] = False
                # Sono/Lentidão em minions (de magias em área): expiram aqui.
                for flag, rod in (("dormindo", "dormindo_rodadas"), ("lento", "lento_rodadas")):
                    if a.get(flag):
                        a[rod] = a.get(rod, 1) - 1
                        if a[rod] <= 0:
                            a.pop(flag, None); a.pop(rod, None)
            plural = "s" if custo > 1 else ""
            await self.gm_say(
                f"💀 Turno dos servos de **{p['name']}** ({custo} animado{plural}) — "
                f"mova/ataque e encerre o turno novamente. "
                f"🍖 {p['fome']:.0f}/10 💧 {p['sede']:.0f}/10")
            await self.push_state()
            return
        self.animados_phase_pid = None

        p["moves_left"]        = p["spd"]
        p["action_done"]       = False
        p["bonus_action_used"] = False
        p["moved_this_turn"]   = False   # reabre o custo de -1 sede ao caminhar no novo turno
        # buffs de turno do warrior expiram ao fim do turno (flags planas)
        p["skill_bonus_acerto"] = 0
        p["skill_dobrar_dano"]  = False
        p["skill_ataque_extra"] = False
        p["skill_extra_usado"]  = False
        p["cancao_atacou_apos"] = False   # reabre o custo extra de atacar sob a canção no novo turno
        # metamagia do mago expira ao fim do turno (flags planas)
        p["aprimorar_ativo"]   = False
        p["estender_ativo"]    = False
        p["fortalecer_ativo"]  = False

        # Clear temp effects for this player.
        # temp_def normalmente dura 1 turno; o Escudo Mágico Aprimorado (Pedro)
        # marca temp_def_turnos>1 e sobrevive a esse end_turn extra.
        if self.temp_def_turnos.get(pid, 0) > 1:
            self.temp_def_turnos[pid] -= 1
        else:
            self.temp_def.pop(pid, None)
            self.temp_def_turnos.pop(pid, None)
        if pid in self.blessed:
            self.players[pid]["atk_bonus"] = self.players[pid]["base_atk_bonus"]
            self.blessed.pop(pid)
        if self.immune.get(pid, 0) > 0:
            self.immune[pid] -= 1

        # Advance turn
        n_jogadores = len(self.player_order)
        volta_antes = self.turn_index // n_jogadores   # número da "volta" atual
        self.turn_index += 1
        # Skip dead players
        attempts = 0
        while attempts < n_jogadores:
            cur = self.player_order[self.turn_index % n_jogadores]
            if self._ativo(self.players[cur]):   # pula mortos E desconectados
                break
            self.turn_index += 1
            attempts += 1

        # Completou uma volta (rodada)? Dispara a fase do GM. Usa a comparação de
        # voltas (não `turn_index % n == 0`): assim, quando o pulo de um jogador
        # MORTO cai justo no fim da volta, a fase do GM ainda dispara uma vez.
        if self.turn_index // n_jogadores > volta_antes:
            self.round_num += 1
            # Clarividência: revelações mágicas expiram com o passar das rodadas.
            self.magic_reveal = {k: v for k, v in self.magic_reveal.items()
                                 if v > self.round_num}
            await self.gm_phase()
            await self._processar_efeitos_armadilha_turno()   # dano progressivo (incendiária)
            await self._processar_zonas_turno()               # escuridão/silêncio expiram por rodada
            await self._aplicar_exaustao_rodada()   # sempre, mesmo sem monstros
        else:
            next_p = self.players[self.current_pid()]
            next_p["moves_left"] = next_p["spd"]
            if next_p.get("perde_turno"):
                next_p["action_done"]       = True
                next_p["bonus_action_used"] = True
                next_p["moves_left"]        = 0
                await self.gm_say(f"🕸️ Turno de **{next_p['name']}** — imobilizado! Encerre o turno para continuar.")
            else:
                await self.gm_say(f"🎲 Turno de **{next_p['name']}**!")

        # ── Início do turno do novo jogador ────────────────────────────────────
        # Upkeep da Canção Heroica (cobra manutenção / interrompe se faltar
        # recurso) e concede o bônus de Movimento da canção sobre o spd base.
        cur_p = self.players[self.current_pid()]
        if cur_p.get("class_id") == "bard" and cur_p.get("cancao_ativa"):
            await self._cobrar_manutencao_cancao(cur_p)
        if cur_p.get("class_id") == "paladin":
            await self._processar_manutencao_richard(cur_p)
        if cur_p.get("class_id") == "rogue":
            await self._processar_inicio_turno_luccas(cur_p)
        if cur_p.get("class_id") == "cleric":
            # MODO DE TESTE: recarrega os slots de magia do Lewis a cada turno, para
            # que todas as magias fiquem sempre disponíveis para teste.
            cur_p["magias_usadas_hoje"] = {"primeiro": 0, "segundo": 0, "terceiro": 0}
        # Venenos: tica/expira efeitos no início do turno do jogador (antes de fixar o movimento).
        await self._processar_venenos_turno(cur_p)
        # Corrosão Viva (Devorador Orgânico): DoT por turno em quem está sem armadura.
        await self._processar_corrosao_viva_turno(cur_p)
        # Embriaguez (Garrafa de Vinho): tica e expira a penalidade.
        await self._processar_vinho_turno(cur_p)
        # Embriaguez (Caneca de Cerveja): tica e expira a penalidade de ataque.
        await self._processar_cerveja_turno(cur_p)
        # Buffs mágicos temporários (ex.: Visão no Escuro) expiram no início do turno.
        await self._processar_buffs_magicos_turno(cur_p)
        # Paralisação (Raio Congelante): novo Fortitude no início do turno.
        if cur_p.get("paralisado"):
            await self._processar_paralisacao_turno(cur_p)
        # Sono/Medo/Lentidão (de magias em área) no jogador.
        await self._processar_status_jogador_turno(cur_p)
        # Buffs/debuffs mágicos (Abençoar/Amaldiçoar) expiram por rodada.
        await self._processar_mods_magia_turno(cur_p)
        # Agarrar (crocodilo/cobra): tentativa de escape no início do turno.
        if cur_p.get("preso"):
            await self._processar_escape_agarrar(cur_p)
        cur_p["moves_left"] = self._moves_base(cur_p)
        # Se ainda preso após a tentativa, bloqueia o movimento.
        if cur_p.get("preso"):
            captor = self.monsters.get(cur_p.get("preso_por"))
            if captor and captor["hp"] > 0:
                cur_p["moves_left"] = 0
        # Velocidade: movimento dobrado enquanto ativa.
        if cur_p.get("velocidade_rodadas", 0) > 0:
            cur_p["moves_left"] *= 2

        self._iniciar_timer_turno()   # 30s para o novo jogador da vez
        await self.push_state()

    # ── Sistema de monstros — helpers ────────────────────────────────────────

    def _camuflagem_bonus(self, target):
        """Camuflagem Natural (cobra venenosa): +2 CA contra o PRIMEIRO ataque
        recebido (consumido após o primeiro uso). O dungeon é tratado como
        terreno natural, então a camuflagem está sempre disponível 1×."""
        if target.get("camuflagem_usada"):
            return 0
        if any(ab.get("id") == "camuflagem_natural"
               for ab in target.get("special_abilities", [])):
            target["camuflagem_usada"] = True
            return 2
        return 0

    def _furia_bonus(self, m):
        """Fúria: +2 de dano enquanto o monstro está com HP < 50% (ex.: Urso Negro)."""
        if not any(ab.get("id") == "furia" for ab in m.get("special_abilities", [])):
            return 0
        return 2 if m.get("hp", 0) < m.get("max_hp", m.get("hp", 1)) / 2 else 0

    def _investida_bonus(self, m):
        """Investida Brutal: +2 de dano se o monstro se moveu antes de atacar
        neste turno (flag `_investiu` setada pela IA)."""
        return 2 if m.get("_investiu") else 0

    def _furia_cega_dano_bonus(self, m):
        """Fúria Cega: +1 de dano enquanto enfurecido (sofreu dano na rodada anterior)."""
        return 1 if m.get("furia_cega") else 0

    def _furia_cega_ca_pen(self, m):
        """Fúria Cega: -1 de CA enquanto enfurecido (alvo mais fácil de acertar)."""
        return 1 if m.get("furia_cega") else 0

    def _player_effective_ac(self, p):
        """CA efetiva de um jogador ao ser atacado por um monstro (escudo/canção/
        Guerreiro da Luz/Amaldiçoar e corrosão de armadura)."""
        gl_ca = (p.get("guerreiro_luz_bonus", {}).get("ca", 0)
                 if p.get("guerreiro_luz_ativo") else 0)
        return (p["ac"] + self.temp_def.get(p["id"], 0)
                + self._cancao_bonus(p, "bonus_ca")
                + gl_ca + self._mod_magia(p, "ca")
                - self._corrosao_ca_pen(p))

    # ── Corrosão de equipamentos (Devorador Orgânico) ──────────────────────────
    def _corr(self, p):
        """Estado de corrosão do jogador (inicializa sob demanda, chave a chave)."""
        c = p.setdefault("corrosao", {})
        c.setdefault("armadura_lvl", 0)
        c.setdefault("armadura_com_ca", False)   # a armadura corroída concede CA? (couro/metal sim; manto não)
        c.setdefault("armadura_destruida", False)
        c.setdefault("arma_lvl", 0)
        c.setdefault("arma_destruida", False)
        return c

    def _tem_armadura(self, p):
        """'Com armadura' = item no slot armor que dá proteção real (couro/cota/...).
        Manto (cloak, 0 CA) e ausência de armadura contam como SEM armadura —
        gatilho da Corrosão Viva e da priorização da IA."""
        c = self._corr(p)
        if c["armadura_destruida"]:
            return False
        a = p["gear"].get("armor")
        return bool(a) and a.get("id") != "cloak"

    def _corrosao_ca_pen(self, p):
        """Penalidade de CA por corrosão (só armadura que concede CA perde CA)."""
        c = self._corr(p)
        if not c["armadura_com_ca"]:
            return 0
        return min(c["armadura_lvl"], 3)   # danificado -1, quebrado -2, destruído -3

    def _corrosao_arma_pen(self, p):
        """Penalidade de acerto/dano por arma de madeira corroída."""
        c = self._corr(p)
        if c["arma_destruida"]:
            return 0                        # já desarmado (soco) — sem penalidade extra
        return min(c["arma_lvl"], 2)        # danificado -1, quebrado -2

    async def _devorador_cura(self, m, dado):
        """Cura o devorador ao destruir/consumir um item (Absorver Matéria 1d4 /
        Devorar Metal 1d6)."""
        cura  = roll_dice(dado)
        antes = m["hp"]
        m["hp"] = min(m.get("max_hp", m["hp"]), m["hp"] + cura)
        ganho = m["hp"] - antes
        if ganho > 0:
            await self.gm_say(f"🍖 **{m['name']}** devora o material destruído e recupera **{ganho}** HP!")

    async def _corroer_equipamento(self, m, p, armaduras_ids, armas_ids, cura="1d4", label="Corrosão"):
        """Degrada UM equipamento do alvo (prioridade: armadura > arma) cujos ids
        estejam nos conjuntos dados. Destruição (nível 3) é PERMANENTE e cura o
        devorador por `cura`. Usado pelos Devoradores Orgânico e de Metal."""
        c = self._corr(p)
        armor  = p["gear"].get("armor")
        weapon = p.get("weapon")

        if (armor and armor.get("id") in armaduras_ids and not c["armadura_destruida"]):
            c["armadura_lvl"] += 1
            c["armadura_com_ca"] = (armor.get("id") != "cloak")   # manto não dá CA; couro/metal sim
            if c["armadura_lvl"] >= 3:
                c["armadura_destruida"] = True
                p["gear"]["armor"]      = None
                await self.gm_say(
                    f"💥 A armadura de **{p['name']}** ({armor.get('name','armadura')}) "
                    f"foi **destruída permanentemente**!")
                await self._devorador_cura(m, cura)
            else:
                nome = CORROSAO_NIVEL_NOME[c["armadura_lvl"]]
                efeito = f" (-{c['armadura_lvl']} CA)" if c["armadura_com_ca"] else ""
                await self.gm_say(f"🦷 **{label}**: a armadura de **{p['name']}** está **{nome}**{efeito}!")
            return

        if (weapon and weapon.get("id") in armas_ids and not c["arma_destruida"]):
            c["arma_lvl"] += 1
            if c["arma_lvl"] >= 3:
                c["arma_destruida"] = True
                p["weapon"]         = {**WEAPONS["unarmed"]}
                p["gear"]["weapon"] = None
                await self.gm_say(
                    f"💥 A arma de **{p['name']}** ({weapon.get('name','arma')}) "
                    f"foi **destruída permanentemente** — agora luta desarmado!")
                await self._devorador_cura(m, cura)
            else:
                nome = CORROSAO_NIVEL_NOME[c["arma_lvl"]]
                await self.gm_say(
                    f"🦷 **{label}**: a arma de **{p['name']}** "
                    f"({weapon.get('name','arma')}) está **{nome}** (-{c['arma_lvl']} acerto/dano)!")
            return
        # Nenhum equipamento do tipo certo exposto — nada a corroer.

    async def _aplicar_toque_putrefato(self, m, p):
        """Devorador Orgânico: corrói couro/manto e armas de madeira (cura 1d4)."""
        await self._corroer_equipamento(m, p, CORROSAO_ARMADURA_ORGANICA,
                                        CORROSAO_ARMA_MADEIRA, "1d4", "Toque Putrefato")

    async def _aplicar_mordida_corrosiva(self, m, p):
        """Devorador de Metal: corrói armaduras e armas de METAL (cura 1d6)."""
        await self._corroer_equipamento(m, p, CORROSAO_ARMADURA_METAL,
                                        CORROSAO_ARMA_METAL, "1d6", "Mordida Corrosiva")

    async def _aplicar_corrosao_viva(self, m, p):
        """Corrosão Viva: alvo SEM armadura ganha uma pilha de DoT (1 dano/turno
        por 2 turnos). Cada acerto acumula +1 dano por turno."""
        if self._tem_armadura(p):
            return
        p.setdefault("corrosao_viva", []).append(2)   # nova pilha: dura 2 rodadas
        n = len(p["corrosao_viva"])
        await self.gm_say(
            f"☣️ **Corrosão Viva** em **{p['name']}** — agora **{n}** de dano por turno (2 rodadas)!")

    async def _processar_corrosao_viva_turno(self, p):
        """Tica a Corrosão Viva no início do turno do jogador."""
        pilhas = p.get("corrosao_viva")
        if not pilhas:
            return
        dano = len(pilhas)
        p["hp"] = max(0, p["hp"] - dano)
        await self.gm_say(
            f"☣️ A corrosão consome **{p['name']}**: **{dano}** de dano! "
            f"({p['hp']}/{p['max_hp']} HP)")
        p["corrosao_viva"] = [t - 1 for t in pilhas if t - 1 > 0]
        if p["hp"] <= 0:
            await self._player_dies(p["id"])

    async def _processar_vinho_turno(self, p):
        """Tica a embriaguez da Garrafa de Vinho; ao expirar, restaura ataque/Reflexos."""
        if p.get("vinho_rodadas", 0) <= 0:
            return
        p["vinho_rodadas"] -= 1
        if p["vinho_rodadas"] <= 0 and p.get("vinho_ativo"):
            p["vinho_ativo"] = False
            p["atk_bonus"]  += 1
            p["ref_"]       += 1
            await self.gm_say(f"🍷 **{p['name']}** se recupera da embriaguez (penalidade do vinho acabou).")

    def _resetar_vinho(self, p):
        """Reset por dungeon: cancela a embriaguez restaurando os atributos."""
        if p.get("vinho_ativo"):
            p["atk_bonus"] += 1
            p["ref_"]      += 1
        p["vinho_ativo"]   = False
        p["vinho_rodadas"] = 0

    async def _processar_cerveja_turno(self, p):
        """Tica a embriaguez da Caneca de Cerveja; ao expirar, restaura o ataque."""
        if p.get("cerveja_rodadas", 0) <= 0:
            return
        p["cerveja_rodadas"] -= 1
        if p["cerveja_rodadas"] <= 0 and p.get("cerveja_ativo"):
            p["cerveja_ativo"] = False
            p["atk_bonus"]    += 1
            await self.gm_say(f"🍺 **{p['name']}** recupera a pontaria (penalidade da cerveja acabou).")

    def _resetar_cerveja(self, p):
        """Reset por dungeon: cancela a embriaguez da cerveja restaurando o ataque."""
        if p.get("cerveja_ativo"):
            p["atk_bonus"] += 1
        p["cerveja_ativo"]   = False
        p["cerveja_rodadas"] = 0

    def _resetar_corrosao(self, p):
        """Reset por dungeon: REPARA os danos de nível 1-2 (limpa o estado, então as
        penalidades on-the-fly somem). Itens DESTRUÍDOS (nível 3) são permanentes —
        não voltam (já foram removidos do slot)."""
        p.pop("corrosao", None)
        p["corrosao_viva"] = []

    def _apply_damage_types(self, raw_dmg, damage_types, target, weapon=None):
        """Aplica imunidades e fraquezas do alvo ao dano. Retorna dano ajustado."""
        for dtype in damage_types:
            if dtype in target.get("immunities", []):
                return 0
        total = raw_dmg
        for weakness in target.get("weaknesses", []):
            if weakness.get("type") not in damage_types:
                continue
            req_cat = weakness.get("categoria")
            if req_cat and (weapon or {}).get("categoria") != req_cat:
                continue
            if "multiplier" in weakness:
                total = int(total * weakness["multiplier"])
            elif "bonus_flat" in weakness:
                total += weakness["bonus_flat"]
        # Marca se o ÚLTIMO dano recebido por um monstro foi sagrado/luz — usado pela
        # Resistência Morta do Zumbi (morte sagrada = destruição total, sem retorno).
        if not self._eh_jogador(target):
            target["_dano_sagrado_recente"] = (DMG_HOLY in damage_types)
        min_dmg = target.get("min_damage", 0)
        return max(min_dmg, total)

    def _avg_level(self):
        alive = [p for p in self.players.values() if p["alive"]]
        if not alive:
            return 1
        return sum(p.get("level", 1) for p in alive) / len(alive)

    def _calc_monster_xp(self, m):
        """Retorna (xp_por_jogador, qtd_jogadores_vivos)."""
        alive_count = max(1, len([p for p in self.players.values() if p["alive"]]))
        if "cr" in m:
            cr = m["cr"]
            xp_total = int(300 * self._avg_level() * (2 ** (cr - 1)) / 2)
            return max(1, xp_total // alive_count), alive_count
        share = m.get("xp", 0) // alive_count
        return share, alive_count

    def _roll_monster_loot(self, m):
        """Rola a tabela de loot do monstro. Retorna dict de item ou None."""
        loot_table = m.get("loot_table")
        if not loot_table:
            return None
        roll = random.randint(1, 100)
        for range_str, item in loot_table.items():
            lo, hi = map(int, range_str.split("-"))
            if lo <= roll <= hi:
                return item
        return None

    def _monster_facing(self, m):
        """Direção cardinal que a cabeça de um monstro ORIENTADO encara.
        Default: oeste ([-1,0]), batendo com a arte (cabeça à esquerda)."""
        f = m.get("facing") or [-1, 0]
        return [f[0], f[1]]

    def _monster_tiles_at(self, m, ax, ay, facing=None):
        """Footprint do monstro com a âncora em (ax,ay).
        - ORIENTADO (`oriented`): ocupa 2 casas em linha — FRENTE (cabeça) = (ax,ay)
          e TRÁS (cauda) = imediatamente atrás da cabeça (oposto ao facing). O
          parâmetro `facing` sobrepõe o atual (usado ao avaliar uma virada).
        - Caso geral: bloco w×h a partir do canto (ax,ay)."""
        if m.get("oriented"):
            fx, fy = facing if facing is not None else self._monster_facing(m)
            return [[ax, ay], [ax - fx, ay - fy]]
        w, h = m.get("size", [1, 1])
        return [[ax + dx, ay + dy] for dx in range(w) for dy in range(h)]

    def _monster_tiles(self, m):
        """Lista de [x,y] tiles ocupados pelo monstro (frente = m['pos'])."""
        return self._monster_tiles_at(m, m["pos"][0], m["pos"][1])

    def _face_toward(self, m, target_pos):
        """ORIENTADO: vira a cabeça para encarar `target_pos` (cardinal dominante),
        desde que a cauda caiba atrás. Só orientação (visual/posicional) — não move."""
        if not m.get("oriented"):
            return
        px, py = m["pos"]
        dx, dy = target_pos[0] - px, target_pos[1] - py
        if dx == 0 and dy == 0:
            return
        f = [1 if dx > 0 else -1, 0] if abs(dx) >= abs(dy) else [0, 1 if dy > 0 else -1]
        if self._monster_can_occupy(m, px, py, f):
            m["facing"] = f

    def _entity_blocks(self, x, y, exclude_mid=None, exclude_pid=None, exclude_aid=None):
        """True se (x,y) está ocupado por entidade viva: monstro (footprint
        multi-tile), jogador ou animado. Exclusões por id para auto-checagem."""
        for mid2, m2 in self.monsters.items():
            if mid2 == exclude_mid or m2["hp"] <= 0:
                continue
            if [x, y] in self._monster_tiles(m2):
                return True
        for pid2, p2 in self.players.items():
            if pid2 == exclude_pid or not p2["alive"]:
                continue
            if p2["pos"] == [x, y]:
                return True
        return self._animado_em([x, y], exclude_id=exclude_aid)

    def _monster_can_occupy(self, m, ax, ay, facing=None):
        """True se o monstro m pode posicionar sua âncora em (ax,ay): footprint
        inteiro dentro do mapa, sem parede/porta fechada e sem outra entidade
        viva (a própria m é ignorada via exclude_mid). `facing` avalia uma virada
        de um monstro orientado (footprint recalculado com essa direção)."""
        for tx, ty in self._monster_tiles_at(m, ax, ay, facing):
            if self._blocks_tile(tx, ty):          # fora do mapa, parede ou porta fechada
                return False
            if self._entity_blocks(tx, ty, exclude_mid=m["id"]):
                return False
        return True

    def _is_adjacent_to_monster(self, pos, m):
        """True se pos é cardinalmente adjacente a qualquer tile do monstro."""
        for tx, ty in self._monster_tiles(m):
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                if [tx + dx, ty + dy] == list(pos):
                    return True
        return False

    def _get_monster_primary_target(self, m, targets):
        """Seleciona o alvo com prioridade: provocação > taunt > mais próximo."""
        if m.get("provocado") and m.get("provocado_turnos", 0) > 0:
            prov_pid = m.get("provocado_por")
            if prov_pid in self.players and self.players[prov_pid]["alive"]:
                return {"kind": "player", "obj": self.players[prov_pid]}
        if self.taunted and self.taunted in self.players and self.players[self.taunted]["alive"]:
            return {"kind": "player", "obj": self.players[self.taunted]}
        return min(targets, key=lambda t: (
            abs(t["obj"]["pos"][0] - m["pos"][0]) + abs(t["obj"]["pos"][1] - m["pos"][1])
        ))

    async def _monster_move_step(self, m, target_pos, avoid_tiles=None):
        """Move o monstro 1 passo cardinal em direção a target_pos.
        avoid_tiles: frozenset de (x,y) que o monstro recusa pisar (ex: armadilhas próprias)."""
        avoid = avoid_tiles or frozenset()
        frm = list(m["pos"])
        dx = 0 if m["pos"][0] == target_pos[0] else (1 if target_pos[0] > m["pos"][0] else -1)
        dy = 0 if m["pos"][1] == target_pos[1] else (1 if target_pos[1] > m["pos"][1] else -1)
        for adx, ady in [(dx, 0), (0, dy)]:
            if adx == 0 and ady == 0:
                continue
            nx, ny = m["pos"][0] + adx, m["pos"][1] + ady
            # Orientado: ao dar o passo ele VIRA a cabeça para a direção do passo
            # (a cauda segue para a casa que a cabeça acabou de deixar).
            cand_facing = [adx, ady] if m.get("oriented") else None
            # footprint inteiro (multi-tile) precisa estar fora das casas evitadas
            if any((tx, ty) in avoid for tx, ty in self._monster_tiles_at(m, nx, ny, cand_facing)):
                continue
            if not self._monster_can_occupy(m, nx, ny, cand_facing):   # parede/porta/entidade em qualquer casa do footprint
                continue
            m["pos"] = [nx, ny]
            if cand_facing is not None:
                m["facing"] = cand_facing
            break
        # Anima o deslize fiel de 1 casa no cliente (só se de fato moveu).
        if m["pos"] != frm:
            await self._emit_entity_step(m["id"], frm, m["pos"], "monster")
        arm = self._armadilha_no_tile(m["pos"][0], m["pos"][1])
        if arm:
            await self._disparar_armadilha(m, arm)

    async def _execute_one_monster_attack(self, m, atk_def, target_obj):
        """Executa um único ataque de um monstro com formato novo."""
        target   = target_obj["obj"]
        is_player = target_obj["kind"] == "player"
        tgt_name = target["name"] if is_player else target["nome"]
        self._face_toward(m, target["pos"])   # orientado: encara o alvo ao atacar

        if self.smoke.get(m["id"]):
            self.smoke.pop(m["id"])
            await self.gm_say(f"💨 **{m['name']}** tenta atacar **{tgt_name}** mas a fumaça confunde!")
            return
        if is_player and self.immune.get(target["id"], 0) > 0:
            await self.gm_say(f"🛡️ **{m['name']}** ataca **{tgt_name}** mas o Escudo Divino bloqueia!")
            return

        effective_ac = self._player_effective_ac(target) if is_player else target["ca"]

        m_atk = (atk_def["atk_bonus"] + self._pen(m, "ataque") + self._mod_magia(m, "ataque")
                 + self._sombras_atk_bonus(m, target)               # Ataque das Sombras (+2)
                 + self._luz_atk_pen(m))                            # Fraqueza de Luz (-2 sob luz direta)
        esc = self._verificar_escuridao(m, target)
        prov = bool(m.get("provocado_turno_efeito"))
        desvantagem = prov or esc == "desvantagem"
        vantagem    = esc == "vantagem"
        if vantagem and desvantagem:
            vantagem = desvantagem = False
        if prov:
            m["provocado_turno_efeito"] = False

        if vantagem or desvantagem:
            hit, roll, total, crit, discarded = self._rolar_ataque(
                m_atk, effective_ac, vantagem, desvantagem)
            modo = "vantagem" if vantagem else "desvantagem"
            await self.broadcast({"type": "dice_roll", "die": "d20", "value": discarded,
                                   "label": f"{m['name']} — descartado", "discarded": True})
            await self.broadcast({"type": "dice_roll", "die": "d20", "value": roll,
                                   "label": f"{m['name']} — {modo}", "hit": hit, "crit": crit, "kept": True})
        else:
            hit, roll, total, crit = d20_attack(m_atk, effective_ac)
            await self.broadcast({"type": "dice_roll", "die": "d20", "value": roll,
                                   "label": m["name"], "hit": hit, "crit": crit})

        if target.get("dormindo"):
            hit, crit = True, True
            target.pop("dormindo", None); target.pop("dormindo_rodadas", None)
            await self.gm_say(f"🌙 **{tgt_name}** é atacado dormindo — golpe **CRÍTICO** e desperta!")

        if hit:
            raw_dmg = roll_dice(atk_def["damage"])
            if crit:
                raw_dmg *= 2
            sombra_dano = self._sombras_dano_bonus(m, target)        # Ataque das Sombras (+1d6)
            if sombra_dano:
                await self.broadcast({"type": "dice_roll", "die": "d6",
                                       "value": sombra_dano, "label": "Ataque das Sombras"})
            dmg = max(1, raw_dmg + self._pen(m, "dano") + self._mod_magia(m, "dano")
                      + self._furia_bonus(m)                         # Fúria (HP < 50%)
                      + self._investida_bonus(m)                     # Investida Brutal (moveu)
                      + self._furia_cega_dano_bonus(m)               # Fúria Cega (dano na rodada anterior)
                      + self._golpe_brutal_bonus(m)                  # Ogro: Golpe Brutal (+2)
                      + sombra_dano)                                 # Ataque das Sombras (+1d6)
            dmg = self._apply_damage_types(dmg, atk_def.get("damage_types", ["physical"]), target)
            die_type = "d" + atk_def["damage"].split("d")[1].split("+")[0]
            await self.broadcast({"type": "dice_roll", "die": die_type, "value": raw_dmg, "label": "Dano"})
            crit_str = " **CRÍTICO!**" if crit else ""
            atk_name = atk_def.get("name", "Ataque")
            if is_player:
                dmg_alvo, transfer = await self._processar_dano_protetor(target["id"], dmg)
                target["hp"] = max(0, target["hp"] - dmg_alvo)
                await self.gm_say(
                    f"💢 **{m['name']}** · {atk_name} em **{tgt_name}**"
                    f" (d20={roll}+{m_atk}={total} vs CA {effective_ac}):"
                    f"{crit_str} **{dmg_alvo}** de dano! ({target['hp']}/{target['max_hp']} HP)")
                if transfer:
                    richard, dano_r = transfer
                    richard["hp"] = max(0, richard["hp"] - dano_r)
                    if richard["hp"] <= 0:
                        await self._player_dies(richard["id"])
                if target["hp"] <= 0:
                    await self._player_dies(target["id"])
                # Efeito on-hit (ex: veneno na mordida)
                elif atk_def.get("on_hit"):
                    await self._aplicar_veneno(target, atk_def["on_hit"], fonte="ataque")
                # Extra damage (ex: virote incendiário do kobold besteiro)
                if atk_def.get("extra_damage") and target.get("hp", 1) > 0:
                    xdmg = roll_dice(atk_def["extra_damage"])
                    xdmg = self._apply_damage_types(xdmg, atk_def.get("extra_damage_types", []), target)
                    target["hp"] = max(0, target["hp"] - xdmg)
                    await self.gm_say(f"🔥 Virote incendiário: +{xdmg} de dano de fogo!")
                    if target["hp"] <= 0:
                        await self._player_dies(target["id"])
            else:
                dmg_ef = self._ajustar_dano_elemental(target, dmg, "fisico")
                target["vida_atual"] = max(0, target["vida_atual"] - dmg_ef)
                await self.gm_say(
                    f"💢 **{m['name']}** · {atk_name} em **{tgt_name}**"
                    f" (d20={roll}+{m_atk}={total} vs CA {effective_ac}):"
                    f"{crit_str} **{dmg_ef}** de dano! ({target['vida_atual']}/{target['vida_max']} HP)")
                if target["vida_atual"] <= 0:
                    await self._animado_morre(target, m.get("id"))
            return True   # acertou
        else:
            await self.gm_say(
                f"💢 **{m['name']}** · {atk_def.get('name','Ataque')} em **{tgt_name}**"
                f" (d20={roll}+{m_atk}={total} vs CA {effective_ac}): **ERROU!**")
            return False  # errou

    async def _monster_execute_attacks(self, m, target_obj):
        """Executa todos os ataques de um monstro no formato novo."""
        target    = target_obj["obj"]
        is_player = target_obj["kind"] == "player"
        for atk_def in m.get("attacks", []):
            for _ in range(atk_def.get("num_attacks", 1)):
                if is_player and (not target.get("alive") or target.get("hp", 0) <= 0):
                    return
                if not is_player and target.get("vida_atual", 0) <= 0:
                    return
                await self._execute_one_monster_attack(m, atk_def, target_obj)

    async def _use_monster_ability(self, m, ability, target_obj):
        """Usa uma habilidade especial do monstro. Retorna True se ativada."""
        ab_id = ability["id"]
        # Verifica usos/cooldown
        if "uses_per_combat" in ability:
            if m.get("ability_uses", {}).get(ab_id, 0) <= 0:
                return False
            m["ability_uses"][ab_id] -= 1
        elif "cooldown_turns" in ability:
            if m.get("ability_cooldowns", {}).get(ab_id, 0) > 0:
                return False
            m.setdefault("ability_cooldowns", {})[ab_id] = ability["cooldown_turns"]

        target    = target_obj["obj"]
        is_player = target_obj["kind"] == "player"
        tgt_name  = target["name"] if is_player else target["nome"]
        ab_name   = ability["name"]

        save_ok, d20, sb, stot = self._testar_save(target, ability["save"], ability["dc"])
        sb_str = f"+{sb}" if sb >= 0 else str(sb)
        await self.broadcast({"type": "dice_roll", "die": "d20", "value": d20,
                               "label": f"{m['name']} — {ab_name}", "hit": not save_ok})
        await self.gm_say(
            f"✨ **{m['name']}** usa **{ab_name}** em **{tgt_name}**! "
            f"Save {ability['save']}: d20({d20}){sb_str}={stot} vs CD {ability['dc']} — "
            f"{'resistiu!' if save_ok else 'falhou!'}")

        if not save_ok:
            if ability.get("damage"):
                raw = roll_dice(ability["damage"])
                adj = self._apply_damage_types(raw, ability.get("damage_types", []), target)
                if is_player:
                    target["hp"] = max(0, target["hp"] - adj)
                    if target["hp"] <= 0:
                        await self._player_dies(target["id"])
                else:
                    target["vida_atual"] = max(0, target["vida_atual"] - adj)
                    if target["vida_atual"] <= 0:
                        await self._animado_morre(target, m.get("id"))
            effect = ability.get("effect")
            if effect == "perde_turno":
                target["perde_turno"] = True
                await self.gm_say(f"🕸️ **{tgt_name}** está imobilizado e perderá o próximo turno!")
            elif effect == "petrificado":
                target["petrificado"] = True
                target["petrificado_rodadas"] = ability.get("effect_duration", 1)
                await self.gm_say(f"🗿 **{tgt_name}** foi petrificado!")
            elif effect == "dormindo":
                target["dormindo"] = True
                target["dormindo_rodadas"] = ability.get("effect_duration", 1)
                await self.gm_say(f"😴 **{tgt_name}** adormeceu!")
            elif effect == "lento":
                target["lento"] = True
                target["lento_rodadas"] = ability.get("effect_duration", 1)
                await self.gm_say(f"🐌 **{tgt_name}** ficou lento!")
            elif effect == "cego":
                target["cego"] = True
                target["cego_rodadas"] = ability.get("effect_duration", 1)
                await self.gm_say(f"👁️ **{tgt_name}** foi cegado!")
        return True

    # ── Armadilhas de sala — kobolds ─────────────────────────────────────────
    def _gerar_armadilhas_kobold(self, room):
        """Gera 1–4 armadilhas no quarto dos kobolds.
        65% estacas envenenadas (fosso_envenenado), 35% rede.
        Venom das estacas: 40% veneno_aranha_sombria, 60% veneno_escorpiao_pedra."""
        n = random.randint(1, 4)
        cx, cy = room["cx"], room["cy"]
        for _ in range(n):
            px = cx + random.randint(-2, 2)
            py = cy + random.randint(-2, 2)
            if not (0 <= px < self.map_w and 0 <= py < self.map_h):
                continue
            if self.tiles[py][px] == WALL:
                continue
            trap_roll = random.randint(1, 100)
            if trap_roll <= 65:
                # Estacas envenenadas
                v_roll = random.randint(1, 100)
                vid = "veneno_aranha_sombria" if v_roll <= 40 else "veneno_escorpiao_pedra"
                tipo = "fosso_envenenado"
            else:
                tipo = "rede"
                vid  = None
            arm = {
                "id":          new_id(),
                "tipo":        tipo,
                "pos":         [px, py],
                "icone":       "⛏️☠️" if tipo == "fosso_envenenado" else "🕸️",
                "nome":        "Estacas Envenenadas" if tipo == "fosso_envenenado" else "Rede",
                "visivel":     False,       # invisível até ser ativada/detectada
                "ativada":     False,
                "aliada":      False,       # machuca jogadores, não kobolds
                "kobold_trap": True,        # kobolds sabem onde estão e evitam
                "so_luccas":   False,
            }
            if vid:
                arm["veneno_id"] = vid
            self.armadilhas.append(arm)

    # ── Loot Esqueleto ────────────────────────────────────────────────────────
    async def _esqueleto_loot(self, m):
        """Sempre: arma equipada. Adicional: 70% nada / 20% 2 moedas / 10% 4 moedas."""
        from copy import deepcopy
        items = []
        # Arma sempre
        arma_id = m.get("esqueleto_arma_id")
        if arma_id:
            arma_item = next((w for w in SHOP_WEAPONS if w["id"] == arma_id), None)
            if arma_item:
                items.append(deepcopy(arma_item))
        if items:
            self._spawn_chest(list(m["pos"]), 0, items)
        # Gold adicional (tabela)
        gold_roll = random.randint(1, 100)
        gold = 0
        if 71 <= gold_roll <= 90:
            gold = 2
        elif gold_roll >= 91:
            gold = 4
        if gold > 0:
            for p in self.players.values():
                if p["alive"]:
                    p["gold"] = p.get("gold", 0) + gold
            await self.gm_say(f"💰 **{m['name']}** deixou {gold} moeda(s).")

    # ── Loot Kobold ───────────────────────────────────────────────────────────
    async def _kobold_loot(self, m):
        """Distribui loot de kobold: arma sempre + tabela base + extras."""
        from copy import deepcopy
        items_sempre = []
        gold_total = 0

        if m.get("type") == "kobold_lanceiro":
            # Arma sempre
            lanca = next((i for i in SHOP_WEAPONS if i["id"] == "lanca_curta"), None)
            if lanca:
                items_sempre.append(deepcopy(lanca))

            # Doses de veneno restantes (dose na arma + doses extras)
            doses = m.get("veneno_doses_extras", 0)
            if m.get("veneno_arma_ativo"):
                doses += 1
            veneno_item = next((i for i in SHOP_MERCHANT if i["id"] == "veneno_aranha_sombria"), None)
            for _ in range(doses):
                if veneno_item:
                    items_sempre.append(deepcopy(veneno_item))

            # Extra independente: 20% veneno
            if random.randint(1, 100) <= 20:
                if veneno_item:
                    items_sempre.append(deepcopy(veneno_item))

        elif m.get("type") == "kobold_besteiro":
            # Arma sempre
            besta = next((i for i in SHOP_WEAPONS if i["id"] == "hand_crossbow"), None)
            if besta:
                items_sempre.append(deepcopy(besta))

            # Virotes restantes → item real no loot
            virotes_rest = m.get("virotes", 0)
            if virotes_rest > 0:
                virote_base = next((i for i in SHOP_MERCHANT if i["id"] == "virotes"), None)
                if virote_base:
                    virote_loot = deepcopy(virote_base)
                    virote_loot["ammo_count"] = virotes_rest
                    virote_loot["name"] = f"Virotes (×{virotes_rest})"
                    items_sempre.append(virote_loot)

            # Virotes especiais restantes
            v_esp_tipo  = m.get("virotes_especiais_tipo")
            v_esp_count = m.get("virotes_especiais_count", 0)
            if v_esp_tipo and v_esp_count > 0:
                if v_esp_tipo == "incendiario":
                    virote_item = next((i for i in SHOP_MERCHANT if i["id"] == "virote_incendiario"), None)
                    for _ in range(v_esp_count):
                        if virote_item:
                            items_sempre.append(deepcopy(virote_item))
                elif v_esp_tipo == "veneno_escorpiao_pedra":
                    veneno_item = next((i for i in SHOP_MERCHANT if i["id"] == "veneno_escorpiao_pedra"), None)
                    for _ in range(v_esp_count):
                        if veneno_item:
                            items_sempre.append(deepcopy(veneno_item))

            # Extras independentes: 5% veneno aranha, 5% 1d6 virotes incendiários
            if random.randint(1, 100) <= 5:
                veneno_item = next((i for i in SHOP_MERCHANT if i["id"] == "veneno_aranha_sombria"), None)
                if veneno_item:
                    items_sempre.append(deepcopy(veneno_item))
            if random.randint(1, 100) <= 5:
                virote_item = next((i for i in SHOP_MERCHANT if i["id"] == "virote_incendiario"), None)
                if virote_item:
                    for _ in range(roll_dice("1d6")):
                        items_sempre.append(deepcopy(virote_item))

        # Tabela base (01-40 nada, 41-70 1 moeda, 71-90 2 moedas, 91-100 nada)
        base_roll = random.randint(1, 100)
        if 41 <= base_roll <= 70:
            gold_total += 1
        elif 71 <= base_roll <= 90:
            gold_total += 2

        # Distribui ouro entre jogadores vivos
        if gold_total > 0:
            for p in self.players.values():
                if p["alive"]:
                    p["gold"] = p.get("gold", 0) + gold_total
            await self.gm_say(f"💰 **{m['name']}** deixou {gold_total} moeda(s).")

        # Spawna baú com itens físicos (se houver)
        if items_sempre:
            self._spawn_chest(list(m["pos"]), 0, items_sempre)
            await self.gm_say(f"🎒 Loot de **{m['name']}** deixado no chão!")

    async def _necromante_loot(self, m):
        """Tesouro do Necromante (1d100): ouro / vinho / ração / pergaminho 1º círculo.
        Se ele NÃO usou o Dominar Morto-Vivo, o pergaminho aparece no tesouro."""
        gold, itens = 0, []
        roll = random.randint(1, 100)
        if roll <= 40:
            pass                                                      # 40% nada
        elif roll <= 70:
            gold = 2                                                  # 30% 2 moedas
        elif roll <= 90:                                              # 20% 2 moedas + vinho
            gold = 2
            v = next((i for i in CHEST_ITEMS if i["id"] == "garrafa_vinho"), None)
            if v: itens.append(deepcopy(v))
        elif roll <= 95:                                             # 5% 2 moedas + ração
            gold = 2
            r = next((i for i in CHEST_ITEMS if i["id"] == "racao"), None)
            if r: itens.append(deepcopy(r))
        else:                                                        # 5% pergaminho 1º círculo
            sc = gerar_pergaminho(1)
            if sc: itens.append(sc)
        # Pergaminho de Dominar Morto-Vivo se ele NÃO o usou em combate.
        if not m.get("usou_dominar"):
            dom = gerar_pergaminho(3, magia_id="dominar_morto_vivo")
            if dom: itens.append(dom)
        if gold > 0 or itens:
            self._spawn_chest(list(m["pos"]), gold, itens)
            await self.gm_say("🎒 Um **baú de saque** apareceu!")

    # ── Covardia Instintiva (kobolds) ─────────────────────────────────────────
    async def _verificar_covardia_kobold(self, m):
        """Checa se o kobold atingiu 50% do HP e rola Vontade CD 10."""
        if m.get("kobold_medo") or m.get("covardia_testada"):
            return
        threshold = math.ceil(m["max_hp"] / 2)
        if m["hp"] > threshold:
            return
        m["covardia_testada"] = True
        save_ok, d20, sb, stot = self._testar_save(m, "vontade", 10)
        sb_str = f"+{sb}" if sb >= 0 else str(sb)
        if save_ok:
            await self.gm_say(
                f"💪 **{m['name']}** resistiu ao medo! "
                f"(d20={d20}{sb_str}={stot})")
        else:
            m["kobold_medo"]        = True
            m["kobold_medo_rodadas"] = 2
            await self.gm_say(
                f"😱 **{m['name']}** entrou em pânico! Vai fugir por 2 rodadas. "
                f"(d20={d20}{sb_str}={stot})")

    # ── IA de fuga (medo kobold) ──────────────────────────────────────────────
    async def _ai_kobold_medo(self, m, targets):
        """Kobold com medo: usa movimento +1 para se afastar do inimigo mais próximo."""
        # Tick-down do medo
        m["kobold_medo_rodadas"] = max(0, m["kobold_medo_rodadas"] - 1)
        if m["kobold_medo_rodadas"] <= 0:
            m["kobold_medo"] = False
            await self.gm_say(f"😤 **{m['name']}** recuperou a coragem!")
            return

        if not targets:
            return

        # Inimigo mais próximo (distância Chebyshev)
        def dist(t):
            return max(abs(m["pos"][0] - t["obj"]["pos"][0]),
                       abs(m["pos"][1] - t["obj"]["pos"][1]))
        nearest_pos = min(targets, key=dist)["obj"]["pos"]

        # Alvo de fuga = ponto oposto exagerado
        flee_x = m["pos"][0] + (m["pos"][0] - nearest_pos[0]) * 20
        flee_y = m["pos"][1] + (m["pos"][1] - nearest_pos[1]) * 20

        kobold_safe = frozenset(
            tuple(a["pos"]) for a in self.armadilhas
            if a.get("kobold_trap") and not a.get("desativada"))

        flee_movement = m.get("movement", 7) + 1
        for _ in range(flee_movement):
            pos_antes = list(m["pos"])
            await self._monster_move_step(m, [flee_x, flee_y], avoid_tiles=kobold_safe)
            if m["pos"] == pos_antes:
                break

        await self.gm_say(f"😱 **{m['name']}** foge em pânico!")

    # ── IA Esqueleto Animal ───────────────────────────────────────────────────
    async def _ai_esqueleto_animal(self, m, targets):
        """Sem Instinto: sempre avança, nunca foge. Movimento Errático: ignora terreno."""
        target_obj = self._get_monster_primary_target(m, targets)
        if not target_obj:
            return
        target = target_obj["obj"]
        if not self._is_adjacent_to_monster(target["pos"], m):
            for _ in range(m.get("movement", 6)):
                pos_antes = list(m["pos"])
                await self._monster_move_step(m, target["pos"])
                if m["pos"] == pos_antes or self._is_adjacent_to_monster(target["pos"], m):
                    break
        if self._is_adjacent_to_monster(target["pos"], m):
            await self._execute_one_monster_attack(m, m["attacks"][0], target_obj)

    # ── IA Esqueleto Humano ───────────────────────────────────────────────────
    async def _ai_esqueleto_humano(self, m, targets):
        target_obj = self._get_monster_primary_target(m, targets)
        if not target_obj:
            return
        target = target_obj["obj"]
        atk = m["attacks"][0]
        atk_range = atk.get("range")   # None = corpo a corpo; 2 = lança

        def em_alcance():
            if atk_range:
                # Lança: distância Chebyshev ≤ range (pode atacar de 2 tiles)
                dx = abs(m["pos"][0] - target["pos"][0])
                dy = abs(m["pos"][1] - target["pos"][1])
                return max(dx, dy) <= atk_range
            return self._is_adjacent_to_monster(target["pos"], m)

        if not em_alcance():
            for _ in range(m.get("movement", 5)):
                pos_antes = list(m["pos"])
                await self._monster_move_step(m, target["pos"])
                if m["pos"] == pos_antes or em_alcance():
                    break

        if em_alcance():
            await self._execute_one_monster_attack(m, atk, target_obj)

    # ── IA Lobo Cinzento ─────────────────────────────────────────────────────
    async def _ai_lobo_cinzento(self, m, targets):
        target_obj = self._get_monster_primary_target(m, targets)
        if not target_obj:
            return
        target = target_obj["obj"]

        # Aproxima-se do alvo
        if not self._is_adjacent_to_monster(target["pos"], m):
            for _ in range(m.get("movement", 8)):
                pos_antes = list(m["pos"])
                await self._monster_move_step(m, target["pos"])
                if m["pos"] == pos_antes or self._is_adjacent_to_monster(target["pos"], m):
                    break

        if not self._is_adjacent_to_monster(target["pos"], m):
            return

        # Caça em Bando: +2 ataque se outro lobo adjacente ao alvo
        outros_lobos = [m2 for m2 in self.monsters.values()
                        if m2["id"] != m["id"]
                        and m2.get("type") == "lobo_cinzento"
                        and m2["hp"] > 0]
        bando_bonus = 2 if any(self._is_adjacent_to_monster(target["pos"], m2)
                                for m2 in outros_lobos) else 0

        atk = dict(m["attacks"][0])
        if bando_bonus:
            atk = {**atk, "atk_bonus": atk["atk_bonus"] + bando_bonus}
            await self.gm_say(f"🐺 **{m['name']}** ataca em bando! (+2 acerto)")

        hit = await self._execute_one_monster_attack(m, atk, target_obj)

        # Derrubar: Ref CD 11 ao acertar
        if hit and target_obj["kind"] == "player" and target.get("hp", 1) > 0:
            derrubar = next((ab for ab in m.get("special_abilities", [])
                             if ab["id"] == "derrubar"), None)
            if derrubar:
                dc = derrubar.get("dc", 11)
                save_ok, d20, sb, stot = self._testar_save(target, "reflexos", dc)
                sb_str = f"+{sb}" if sb >= 0 else str(sb)
                if not save_ok:
                    target["moves_left"] = 0
                    await self.gm_say(
                        f"🐾 **{target['name']}** foi derrubado! "
                        f"(d20={d20}{sb_str}={stot} vs CD {dc}) — perde o movimento restante!")
                else:
                    await self.gm_say(
                        f"🐾 **{target['name']}** resistiu ao derrube "
                        f"(d20={d20}{sb_str}={stot}).")

    # ── Escape de Agarrar ─────────────────────────────────────────────────────
    async def _processar_escape_agarrar(self, p):
        """Tentativa de escape no início do turno do jogador. Os saves e a CD
        vêm da habilidade de agarrão do captor (crocodilo: FOR/REF CD 12;
        cobra: FOR CD 11)."""
        captor = self.monsters.get(p.get("preso_por"))
        if not captor or captor["hp"] <= 0:
            p["preso"] = False
            p.pop("preso_por", None)
            return

        # Localiza a habilidade de agarrão do captor para CD e saves de escape.
        grip = next((ab for ab in captor.get("special_abilities", [])
                     if ab.get("id") in ("agarrar", "constricao")), None)
        dc    = grip.get("dc", 12) if grip else 12
        saves = grip.get("escape_saves") if grip else None
        if not saves:
            saves = ["fortitude", "reflexos"]   # padrão (compat. crocodilo)

        SAVE_LBL = {"fortitude": "FOR", "reflexos": "REF", "vontade": "VON"}
        sucesso = False
        partes  = []
        for s in saves:
            ok, d20, sb, tot = self._testar_save(p, s, dc)
            sb_str = f"+{sb}" if sb >= 0 else str(sb)
            partes.append(f"{SAVE_LBL.get(s, s.upper())} d20={d20}{sb_str}={tot}")
            sucesso = sucesso or ok
        detalhe = " | ".join(partes)

        if sucesso:
            p["preso"] = False
            p.pop("preso_por", None)
            await self.gm_say(
                f"💪 **{p['name']}** se soltou do agarrão de **{captor['name']}**! "
                f"({detalhe} vs CD {dc})")
        else:
            await self.gm_say(
                f"⛓️ **{p['name']}** tenta escapar mas falha! "
                f"({detalhe} vs CD {dc}) — perde o movimento!")

    # ── IA Crocodilo Jovem ────────────────────────────────────────────────────
    async def _ai_crocodilo_jovem(self, m, targets):
        """
        Agarrar: mordida acerta → FOR CD 12 ou fica preso.
        Ataque de Mandíbula: se já há preso adjacente → 1d8+3 automático.
        Arrastar: ao final, puxa preso para adjacente se necessário.
        """
        target_obj = self._get_monster_primary_target(m, targets)
        if not target_obj:
            return
        target = target_obj["obj"]

        # Verifica se há um jogador preso adjacente
        preso_pid = None
        preso_p   = None
        for pid2, p2 in self.players.items():
            if p2.get("preso_por") == m["id"] and p2.get("hp", 1) > 0:
                if self._is_adjacent_to_monster(p2["pos"], m):
                    preso_pid = pid2
                    preso_p   = p2
                    break

        # Ataque de Mandíbula: dano automático no preso adjacente
        if preso_p:
            jaw_dmg = roll_dice("1d8") + 3
            jaw_dmg = self._apply_damage_types(jaw_dmg, ["physical"], preso_p)
            preso_p["hp"] = max(0, preso_p["hp"] - jaw_dmg)
            await self.gm_say(
                f"🦷 **{m['name']}** esmaga **{preso_p['name']}** nas mandíbulas! "
                f"{jaw_dmg} de dano perfurante (automático)!")
            if preso_p["hp"] <= 0:
                preso_p["preso"] = False
                preso_p.pop("preso_por", None)
                await self._player_dies(preso_pid)
            return  # usou a ação principal no preso

        # Não há preso: move + mordida + tentativa de agarrar
        if not self._is_adjacent_to_monster(target["pos"], m):
            for _ in range(m.get("movement", 6)):
                pos_antes = list(m["pos"])
                await self._monster_move_step(m, target["pos"])
                if m["pos"] == pos_antes or self._is_adjacent_to_monster(target["pos"], m):
                    break

        if not self._is_adjacent_to_monster(target["pos"], m):
            # Arrastar: se há preso mas não adjacente, puxa 1 tile
            for pid2, p2 in self.players.items():
                if p2.get("preso_por") == m["id"] and p2.get("hp", 1) > 0:
                    p2["pos"] = list(m["pos"])  # puxa para a posição do croc
                    await self.gm_say(f"🐊 **{m['name']}** arrasta **{p2['name']}**!")
            return

        atk = m["attacks"][0]
        hit = await self._execute_one_monster_attack(m, atk, target_obj)

        # Tentativa de agarrar no acerto
        if hit and target_obj["kind"] == "player" and target.get("hp", 1) > 0 and not target.get("preso"):
            agarrar = next((ab for ab in m.get("special_abilities", []) if ab["id"] == "agarrar"), None)
            dc = agarrar.get("dc", 12) if agarrar else 12
            save_ok, d20, sb, stot = self._testar_save(target, "fortitude", dc)
            sb_str = f"+{sb}" if sb >= 0 else str(sb)
            if not save_ok:
                target["preso"]    = True
                target["preso_por"] = m["id"]
                await self.gm_say(
                    f"🐊 **{target['name']}** está preso nas mandíbulas do **{m['name']}**! "
                    f"(d20={d20}{sb_str}={stot} vs CD {dc}) — não pode se mover!")
            else:
                await self.gm_say(
                    f"🐊 **{target['name']}** resistiu ao agarrar "
                    f"(d20={d20}{sb_str}={stot} vs CD {dc}).")

    # ── IA Cobra Constritora ──────────────────────────────────────────────────
    async def _ai_cobra_constritora(self, m, targets):
        """
        Constrição: mordida acerta → FOR CD 11 ou fica preso.
        Esmagar: se já há preso adjacente → 1d6 automático por turno.
        """
        target_obj = self._get_monster_primary_target(m, targets)
        if not target_obj:
            return
        target = target_obj["obj"]

        # Verifica se há um jogador preso adjacente
        preso_pid = None
        preso_p   = None
        for pid2, p2 in self.players.items():
            if p2.get("preso_por") == m["id"] and p2.get("hp", 1) > 0:
                if self._is_adjacent_to_monster(p2["pos"], m):
                    preso_pid = pid2
                    preso_p   = p2
                    break

        # Esmagar: dano automático no preso adjacente
        if preso_p:
            crush = roll_dice("1d6")
            crush = self._apply_damage_types(crush, ["physical"], preso_p)
            preso_p["hp"] = max(0, preso_p["hp"] - crush)
            await self.gm_say(
                f"🐍 **{m['name']}** aperta seus anéis em **{preso_p['name']}**! "
                f"{crush} de dano por constrição (automático)!")
            if preso_p["hp"] <= 0:
                preso_p["preso"] = False
                preso_p.pop("preso_por", None)
                await self._player_dies(preso_pid)
            return  # usou a ação principal no preso

        # Não há preso: move + mordida + tentativa de constringir
        if not self._is_adjacent_to_monster(target["pos"], m):
            for _ in range(m.get("movement", 7)):
                pos_antes = list(m["pos"])
                await self._monster_move_step(m, target["pos"])
                if m["pos"] == pos_antes or self._is_adjacent_to_monster(target["pos"], m):
                    break

        if not self._is_adjacent_to_monster(target["pos"], m):
            return

        atk = m["attacks"][0]
        hit = await self._execute_one_monster_attack(m, atk, target_obj)

        # Tentativa de constringir no acerto
        if hit and target_obj["kind"] == "player" and target.get("hp", 1) > 0 and not target.get("preso"):
            constr = next((ab for ab in m.get("special_abilities", []) if ab["id"] == "constricao"), None)
            dc = constr.get("dc", 11) if constr else 11
            save_ok, d20, sb, stot = self._testar_save(target, "fortitude", dc)
            sb_str = f"+{sb}" if sb >= 0 else str(sb)
            if not save_ok:
                target["preso"]    = True
                target["preso_por"] = m["id"]
                await self.gm_say(
                    f"🐍 **{target['name']}** foi enrolado pela **{m['name']}**! "
                    f"(d20={d20}{sb_str}={stot} vs CD {dc}) — não pode se mover!")
            else:
                await self.gm_say(
                    f"🐍 **{target['name']}** escapou dos anéis "
                    f"(d20={d20}{sb_str}={stot} vs CD {dc}).")

    # ── IA Cobra Venenosa ─────────────────────────────────────────────────────
    async def _ai_cobra_venenosa(self, m, targets):
        """Emboscadora: ataca e recua, evita combate direto.
        Ataque Rápido: +1 no ataque se a cobra não se mover no turno.
        Veneno: on_hit na mordida (tratado por _execute_one_monster_attack).
        """
        target_obj = self._get_monster_primary_target(m, targets)
        if not target_obj:
            return
        target = target_obj["obj"]

        moveu = False
        if not self._is_adjacent_to_monster(target["pos"], m):
            for _ in range(m.get("movement", 6)):
                pos_antes = list(m["pos"])
                await self._monster_move_step(m, target["pos"])
                if m["pos"] != pos_antes:
                    moveu = True
                if m["pos"] == pos_antes or self._is_adjacent_to_monster(target["pos"], m):
                    break

        if not self._is_adjacent_to_monster(target["pos"], m):
            return  # não alcançou o alvo neste turno

        # Ataque Rápido: +1 no acerto se não se moveu (bote do esconderijo).
        atk = dict(m["attacks"][0])
        if not moveu:
            atk["atk_bonus"] = atk.get("atk_bonus", 0) + 1
            await self.gm_say(
                f"🐍 **{m['name']}** dá o bote imóvel — **Ataque Rápido** (+1 no acerto)!")
        await self._execute_one_monster_attack(m, atk, target_obj)

        # Ataca e recua: afasta-se um passo do alvo após a mordida.
        if m["hp"] > 0:
            if self._passo_monstro(m, target["pos"][0], target["pos"][1], away=True):
                await self.gm_say(f"🐍 **{m['name']}** recua para as sombras após morder.")

    # ── IA Devorador Orgânico ─────────────────────────────────────────────────
    def _em_zona_fogo(self, pos):
        """True se a casa está numa zona de Bola de Fogo ativa."""
        for zona in self.zonas_especiais:
            if zona.get("tipo") == "bola_fogo" and zona.get("ativa"):
                if max(abs(pos[0] - zona["cx"]), abs(pos[1] - zona["cy"])) <= zona.get("raio", 2):
                    return True
        return False

    async def _ai_devorador_organico(self, m, targets):
        """Prioriza alvos com armadura leve (couro), depois sem armadura. Aplica
        Toque Putrefato e Corrosão Viva no acerto. Evita zonas de fogo."""
        players_alvo = [t for t in targets if t["kind"] == "player"]
        forcado = (m.get("provocado") and m.get("provocado_turnos", 0) > 0) or bool(self.taunted)
        if forcado or not players_alvo:
            target_obj = self._get_monster_primary_target(m, targets)
        else:
            def prio(t):
                pl = t["obj"]
                a  = pl["gear"].get("armor")
                if a and a.get("id") == "leather":
                    rank = 0                       # armadura leve (couro) = prato preferido
                elif not self._tem_armadura(pl):
                    rank = 1                       # sem armadura
                else:
                    rank = 2                       # armadura pesada (metal)
                dist = abs(pl["pos"][0] - m["pos"][0]) + abs(pl["pos"][1] - m["pos"][1])
                return (rank, dist)
            target_obj = min(players_alvo, key=prio)
        if not target_obj:
            return
        target = target_obj["obj"]

        # Aproxima-se evitando entrar em zonas de fogo (combustão rápida).
        if not self._is_adjacent_to_monster(target["pos"], m):
            for _ in range(m.get("movement", 5)):
                pos_antes = list(m["pos"])
                await self._monster_move_step(m, target["pos"])
                if m["pos"] == pos_antes:
                    break
                if self._em_zona_fogo(m["pos"]):
                    self._passo_monstro(m, target["pos"][0], target["pos"][1], away=True)
                    await self.gm_say(f"🟢 **{m['name']}** recua das chamas!")
                    break
                if self._is_adjacent_to_monster(target["pos"], m):
                    break

        if not self._is_adjacent_to_monster(target["pos"], m):
            return

        atk = m["attacks"][0]
        hit = await self._execute_one_monster_attack(m, atk, target_obj)

        # Efeitos no acerto contra jogador.
        if hit and target_obj["kind"] == "player" and target.get("hp", 1) > 0:
            await self._aplicar_toque_putrefato(m, target)
            await self._aplicar_corrosao_viva(m, target)

    # ── IA Devorador de Metal ───────────────────────────────────────────────────
    def _item_metalico(self, it):
        return bool(it) and (it.get("id") in CORROSAO_ARMA_METAL
                             or it.get("id") in CORROSAO_ARMADURA_METAL)

    def _chest_metal_adjacente(self, m):
        """Baú adjacente (ou sob o monstro) com algum item metálico → (chest, item)."""
        tiles = self._monster_tiles(m)
        for ch in self.chests.values():
            cp = ch.get("pos", [99, 99])
            if cp not in tiles and not self._is_adjacent_to_monster(cp, m):
                continue
            for it in ch.get("items", []):
                if self._item_metalico(it):
                    return ch, it
        return None, None

    async def _ai_devorador_metal(self, m, targets):
        """Corrói metal: prioriza alvos com armadura metálica > arma metálica;
        consome metal do chão para se curar (Alimentação Metálica)."""
        # Alimentação Metálica: ferido + baú metálico ao alcance → consome e cura 1d6.
        if m["hp"] < m.get("max_hp", m["hp"]):
            ch, it = self._chest_metal_adjacente(m)
            if ch and it:
                ch["items"].remove(it)
                if not ch.get("items") and not ch.get("gold"):
                    self.chests.pop(ch["id"], None)
                await self.gm_say(f"🍖 **{m['name']}** devora **{it.get('name','metal')}** do chão!")
                await self._devorador_cura(m, "1d6")
                return

        players_alvo = [t for t in targets if t["kind"] == "player"]
        forcado = (m.get("provocado") and m.get("provocado_turnos", 0) > 0) or bool(self.taunted)
        if forcado or not players_alvo:
            target_obj = self._get_monster_primary_target(m, targets)
        else:
            def prio(t):
                pl = t["obj"]; a = pl["gear"].get("armor"); w = pl.get("weapon")
                if a and a.get("id") in CORROSAO_ARMADURA_METAL:
                    rank = 0                       # armadura metálica = alvo preferido
                elif w and w.get("id") in CORROSAO_ARMA_METAL:
                    rank = 1                       # arma metálica
                else:
                    rank = 2                       # sem metal — ignorado (prioridade baixa)
                dist = abs(pl["pos"][0] - m["pos"][0]) + abs(pl["pos"][1] - m["pos"][1])
                return (rank, dist)
            target_obj = min(players_alvo, key=prio)
        if not target_obj:
            return
        target = target_obj["obj"]
        if not self._is_adjacent_to_monster(target["pos"], m):
            for _ in range(m.get("movement", 5)):
                pa = list(m["pos"])
                await self._monster_move_step(m, target["pos"])
                if m["pos"] == pa or self._is_adjacent_to_monster(target["pos"], m):
                    break
        if not self._is_adjacent_to_monster(target["pos"], m):
            return
        hit = await self._execute_one_monster_attack(m, m["attacks"][0], target_obj)
        if hit and target_obj["kind"] == "player" and target.get("hp", 1) > 0:
            await self._aplicar_mordida_corrosiva(m, target)

    # ── IA Orc Guerreiro ──────────────────────────────────────────────────────
    async def _ai_orc_guerreiro(self, m, targets):
        """Investida Brutal (+2 se mover antes de atacar) e Fúria Cega (enfurece se
        sofreu dano desde o turno anterior: +1 dano, -1 CA)."""
        # Fúria Cega: snapshot de HP entre turnos do orc.
        ref = m.get("_furia_cega_hp_ref", m.get("max_hp", m["hp"]))
        enfurecido = m["hp"] < ref
        if enfurecido and not m.get("furia_cega"):
            await self.gm_say(f"😡 **{m['name']}** entra em **Fúria Cega**! +1 de dano, mas -1 CA.")
        m["furia_cega"] = enfurecido
        m["_furia_cega_hp_ref"] = m["hp"]

        m["_investiu"] = False   # reseta a Investida deste turno

        target_obj = self._get_monster_primary_target(m, targets)
        if not target_obj:
            return
        target = target_obj["obj"]

        moveu = False
        if not self._is_adjacent_to_monster(target["pos"], m):
            for _ in range(m.get("movement", 6)):
                pos_antes = list(m["pos"])
                await self._monster_move_step(m, target["pos"])
                if m["pos"] != pos_antes:
                    moveu = True
                if m["pos"] == pos_antes or self._is_adjacent_to_monster(target["pos"], m):
                    break

        if not self._is_adjacent_to_monster(target["pos"], m):
            return

        if moveu:
            m["_investiu"] = True   # Investida Brutal armada para este ataque
            await self.gm_say(f"🐗 **{m['name']}** parte para a **Investida Brutal** (+2 de dano)!")
        await self._monster_execute_attacks(m, target_obj)
        m["_investiu"] = False      # consome após atacar

    # ── Goblins: arremesso (ação bônus) + IAs ──────────────────────────────────
    async def _goblin_arremesso(self, m, targets):
        """Arremesso como ação bônus: 1d4+2, alcance 3. No 1 natural a arma quebra
        (perde a habilidade e a adaga do drop)."""
        if not m.get("pode_arremessar"):
            return
        cands = [t for t in targets if t["kind"] == "player"
                 and max(abs(m["pos"][0] - t["obj"]["pos"][0]),
                         abs(m["pos"][1] - t["obj"]["pos"][1])) <= 3
                 and self._tem_linha_de_visao(m["pos"], t["obj"]["pos"])]
        if not cands:
            return
        target_obj = min(cands, key=lambda t: max(abs(m["pos"][0] - t["obj"]["pos"][0]),
                                                  abs(m["pos"][1] - t["obj"]["pos"][1])))
        target = target_obj["obj"]
        d20  = random.randint(1, 20)
        await self.broadcast({"type": "dice_roll", "die": "d20", "value": d20,
                              "label": f"{m['name']} — Arremesso"})
        if d20 == 1:   # 1 natural → a arma quebra
            m["pode_arremessar"] = False
            m["guaranteed_loot"] = [g for g in m.get("guaranteed_loot", []) if g != "dagger"]
            await self.gm_say(f"💥 **{m['name']}** tira **1** no arremesso — a adaga **se quebra**!")
            return
        eff_ac = self._player_effective_ac(target)
        total  = d20 + 4
        if d20 == 20 or total >= eff_ac:
            dmg = self._apply_damage_types(roll_dice("1d4") + 2, ["physical"], target)
            target["hp"] = max(0, target["hp"] - dmg)
            await self.gm_say(
                f"🗡️ **{m['name']}** arremessa a adaga em **{target['name']}** "
                f"(d20={d20}+4={total} vs CA {eff_ac}): **{dmg}** de dano!")
            if target["hp"] <= 0:
                await self._player_dies(target["id"])
        else:
            await self.gm_say(
                f"🗡️ **{m['name']}** arremessa a adaga em **{target['name']}** mas **erra** "
                f"(d20={d20}+4={total} vs CA {eff_ac}).")

    async def _ai_goblin_melee(self, m, targets):
        """Goblin Combatente/Dual: avança e ataca corpo a corpo (1 ou 2 ataques),
        e arremessa a adaga como ação bônus (alcance 3)."""
        target_obj = self._get_monster_primary_target(m, targets)
        if not target_obj:
            return
        target = target_obj["obj"]
        if not self._is_adjacent_to_monster(target["pos"], m):
            for _ in range(m.get("movement", 6)):
                pos_antes = list(m["pos"])
                await self._monster_move_step(m, target["pos"])
                if m["pos"] == pos_antes or self._is_adjacent_to_monster(target["pos"], m):
                    break
        if self._is_adjacent_to_monster(target["pos"], m):
            await self._monster_execute_attacks(m, target_obj)
        # Ação bônus: arremesso (cobre alvos a até 3 casas, mesmo sem chegar ao corpo a corpo).
        await self._goblin_arremesso(m, targets)

    async def _ai_goblin_arqueiro(self, m, targets):
        """Goblin Arqueiro: atira de longe (10 flechas); sem flechas, recua."""
        if m.get("flechas", 0) <= 0:
            if not m.get("sem_municao_avisado"):
                m["sem_municao_avisado"] = True
                await self.gm_say(f"🏹 **{m['name']}** ficou sem flechas e recua!")
            if targets:
                alvo = min(targets, key=lambda t: max(abs(m["pos"][0] - t["obj"]["pos"][0]),
                                                      abs(m["pos"][1] - t["obj"]["pos"][1])))["obj"]
                self._passo_monstro(m, alvo["pos"][0], alvo["pos"][1], away=True)
            return
        target_obj = self._get_monster_primary_target(m, targets)
        if not target_obj:
            return
        target = target_obj["obj"]
        atk_range = m["attacks"][0].get("range", 8)

        def pode_atirar():
            cheb = max(abs(m["pos"][0] - target["pos"][0]), abs(m["pos"][1] - target["pos"][1]))
            return cheb <= atk_range and self._tem_linha_de_visao(m["pos"], target["pos"])

        if not pode_atirar():
            for _ in range(m.get("movement", 6)):
                pos_antes = list(m["pos"])
                await self._monster_move_step(m, target["pos"])
                if m["pos"] == pos_antes or pode_atirar():
                    break
        if not pode_atirar():
            return
        await self._execute_one_monster_attack(m, m["attacks"][0], target_obj)
        m["flechas"] = max(0, m["flechas"] - 1)

    # ── Xamã Goblin (conjurador) ───────────────────────────────────────────────
    async def _xama_silencio(self, m, centro):
        dur = self._rolar_dado("1d4")
        self.zonas_especiais.append({
            "id": f"silencio_{m['id']}_{self.round_num}", "tipo": "silencio",
            "cx": centro[0], "cy": centro[1], "lado": 4,
            "duracao": dur, "ativa": True, "caster": m["id"],
        })
        await self.gm_say(
            f"🔇 **{m['name']}** conjura **Silêncio** 4x4 em ({centro[0]},{centro[1]}) "
            f"por {dur} rodada(s) — sem magias dentro!")

    async def _xama_amaldicoar(self, m, centro):
        dur = self._rolar_dado("1d4+1")
        debuff = {"ataque": -1, "dano": -1, "ca": -1, "resistencia": -1}
        n = 0
        for p in self.players.values():
            if not p["alive"]:
                continue
            if max(abs(p["pos"][0] - centro[0]), abs(p["pos"][1] - centro[1])) > 1:
                continue
            self._set_mod_magia(p, debuff, dur); n += 1
        await self.gm_say(
            f"☠️ **{m['name']}** lança **Amaldiçoar** em {n} herói(s): "
            f"-1 ataque/dano/CA/resistência por {dur} rodada(s)!")

    async def _xama_abencoar(self, m):
        dur  = self._rolar_dado("1d4+1")
        buff = {"ataque": 1, "dano": 1, "ca": 1, "resistencia": 1}
        n = 0
        for o in self.monsters.values():
            if o["hp"] <= 0:
                continue
            if max(abs(o["pos"][0] - m["pos"][0]), abs(o["pos"][1] - m["pos"][1])) > 3:
                continue
            self._set_mod_magia(o, buff, dur); n += 1
        await self.gm_say(
            f"✨ **{m['name']}** lança **Abençoar** em {n} aliado(s): "
            f"+1 ataque/dano/CA/resistência por {dur} rodada(s)!")

    async def _xama_tentar_magia(self, m, targets):
        """Escolhe e lança UMA magia (1/turno, cada 1x/combate). Retorna True se lançou."""
        uses   = m.get("ability_uses", {})
        heroes = [p for p in self.players.values() if self._ativo(p)]
        if not heroes:
            return False
        def cheb(pos):
            return max(abs(m["pos"][0] - pos[0]), abs(m["pos"][1] - pos[1]))
        # 1) Silêncio sobre um conjurador herói no alcance (anula os magos/clérigos).
        if uses.get("silencio", 0) > 0:
            casters = sorted((p for p in heroes if p.get("class_id") in ("mage", "cleric")),
                             key=lambda p: cheb(p["pos"]))
            alvo = next((p for p in casters if cheb(p["pos"]) <= 5), None)
            if alvo:
                await self._xama_silencio(m, alvo["pos"]); uses["silencio"] -= 1; return True
        # 2) Amaldiçoar sobre o herói mais próximo no alcance.
        if uses.get("amaldicoar", 0) > 0:
            alvo = min(heroes, key=lambda p: cheb(p["pos"]))
            if cheb(alvo["pos"]) <= 5:
                await self._xama_amaldicoar(m, alvo["pos"]); uses["amaldicoar"] -= 1; return True
        # 3) Abençoar aliados goblins próximos.
        if uses.get("abencoar", 0) > 0:
            aliados = [o for o in self.monsters.values()
                       if o["hp"] > 0 and o["id"] != m["id"] and cheb(o["pos"]) <= 3]
            if aliados:
                await self._xama_abencoar(m); uses["abencoar"] -= 1; return True
        return False

    async def _ai_xama_goblin(self, m, targets):
        """Conjurador: 1 magia/turno (cada 1x/combate). Concentração Frágil: se
        sofreu dano desde o turno anterior, não conjura. Sem magia → cajado."""
        ref    = m.get("_cf_hp_ref", m.get("max_hp", m["hp"]))
        sofreu = m["hp"] < ref
        m["_cf_hp_ref"] = m["hp"]

        target_obj = self._get_monster_primary_target(m, targets)
        if not target_obj:
            return
        target = target_obj["obj"]

        pode_magia = not sofreu and not self._em_silencio(m)
        if sofreu:
            await self.gm_say(f"🤕 **{m['name']}** sofreu dano e perde a concentração — sem magia neste turno!")

        if pode_magia and await self._xama_tentar_magia(m, targets):
            return   # gastou a ação com a magia

        # Sem magia disponível: aproxima e ataca de cajado.
        if not self._is_adjacent_to_monster(target["pos"], m):
            for _ in range(m.get("movement", 6)):
                pos_antes = list(m["pos"])
                await self._monster_move_step(m, target["pos"])
                if m["pos"] == pos_antes or self._is_adjacent_to_monster(target["pos"], m):
                    break
        if self._is_adjacent_to_monster(target["pos"], m):
            await self._monster_execute_attacks(m, target_obj)

    # ── IA Lagarto Carniceiro ───────────────────────────────────────────────────
    def _hp_alvo(self, obj):
        """HP atual / máximo de um alvo (jogador usa hp/max_hp; animado vida_atual/max)."""
        if "vida_atual" in obj:
            return obj.get("vida_atual", 0), obj.get("vida_max", obj.get("vida_atual", 1)) or 1
        return obj.get("hp", 0), obj.get("max_hp", obj.get("hp", 1)) or 1

    async def _ai_lagarto_carniceiro(self, m, targets):
        """Faro de Carniça: prioriza o alvo com MENOR HP. 2 mordidas (Predador
        Oportunista: +1 vs alvo <50% HP); se ambas acertam → Combo Devorador (2 garras)."""
        forcado = (m.get("provocado") and m.get("provocado_turnos", 0) > 0) or bool(self.taunted)
        if forcado:
            target_obj = self._get_monster_primary_target(m, targets)
        elif targets:
            target_obj = min(targets, key=lambda t: self._hp_alvo(t["obj"])[0])
        else:
            return
        if not target_obj:
            return
        target = target_obj["obj"]
        if not self._is_adjacent_to_monster(target["pos"], m):
            for _ in range(m.get("movement", 7)):
                pa = list(m["pos"])
                await self._monster_move_step(m, target["pos"])
                if m["pos"] == pa or self._is_adjacent_to_monster(target["pos"], m):
                    break
        if not self._is_adjacent_to_monster(target["pos"], m):
            return
        # 2 mordidas (Predador Oportunista: +1 vs alvo ferido).
        bite = dict(m["attacks"][0]); bite["num_attacks"] = 1
        hp, hpmax = self._hp_alvo(target)
        if hp < hpmax * 0.5:
            bite["atk_bonus"] = bite.get("atk_bonus", 0) + 1
            await self.gm_say(f"🦎 **{m['name']}** fareja a presa ferida — **+1** nas mordidas!")
        acertos = 0
        for _ in range(2):
            if self._hp_alvo(target)[0] <= 0:
                break
            if await self._execute_one_monster_attack(m, bite, target_obj):
                acertos += 1
        # Combo Devorador: 2 mordidas certeiras → 2 garras imediatas.
        if acertos >= 2 and self._hp_alvo(target)[0] > 0:
            garra = m.get("garra_attack")
            if garra:
                await self.gm_say(f"🦎 **Combo Devorador**! **{m['name']}** crava 2 garras!")
                for _ in range(2):
                    if self._hp_alvo(target)[0] <= 0:
                        break
                    await self._execute_one_monster_attack(m, garra, target_obj)

    # ── IA Zumbi Infectado ──────────────────────────────────────────────────────
    async def _ai_zumbi(self, m, targets):
        """Lento e Incansável: avança e ataca, nunca foge. Infecção: ao acertar um
        herói, ele testa Fortitude CD 10 ou contrai 1 sintoma leve (regra dos zumbis)."""
        target_obj = self._get_monster_primary_target(m, targets)
        if not target_obj:
            return
        target = target_obj["obj"]
        if not self._is_adjacent_to_monster(target["pos"], m):
            for _ in range(m.get("movement", 4)):
                pa = list(m["pos"])
                await self._monster_move_step(m, target["pos"])
                if m["pos"] == pa or self._is_adjacent_to_monster(target["pos"], m):
                    break
        if not self._is_adjacent_to_monster(target["pos"], m):
            return
        hit = await self._execute_one_monster_attack(m, m["attacks"][0], target_obj)
        if hit and target_obj["kind"] == "player" and target.get("hp", 1) > 0:
            inf = next((ab for ab in m.get("special_abilities", []) if ab["id"] == "infeccao"), None)
            dc = inf.get("dc", 10) if inf else 10
            ok, d20, sb, tot = self._testar_save(target, "fortitude", dc)
            if ok:
                await self.gm_say(f"🦠 **{target['name']}** resiste à infecção (Fortitude {tot} vs CD {dc}).")
            else:
                await self.gm_say(f"🦠 **{target['name']}** é infectado! (Fortitude {tot} vs CD {dc})")
                await self._aplicar_doenca(target, "leve")   # zumbis só aplicam 1 sintoma leve

    # ── IA Kobold Lanceiro ────────────────────────────────────────────────────
    async def _ai_kobold_lanceiro(self, m, targets):
        if m.get("kobold_medo"):
            await self._ai_kobold_medo(m, targets)
            return

        target_obj = self._get_monster_primary_target(m, targets)
        if not target_obj:
            return
        target = target_obj["obj"]

        kobold_safe = frozenset(
            tuple(a["pos"]) for a in self.armadilhas
            if a.get("kobold_trap") and not a.get("desativada"))

        if not self._is_adjacent_to_monster(target["pos"], m):
            for _ in range(m.get("movement", 7)):
                pos_antes = list(m["pos"])
                await self._monster_move_step(m, target["pos"], avoid_tiles=kobold_safe)
                if m["pos"] == pos_antes or self._is_adjacent_to_monster(target["pos"], m):
                    break

        if not self._is_adjacent_to_monster(target["pos"], m):
            return

        # Prepara ataque com veneno se lança estiver envenenada
        atk = dict(m["attacks"][0])
        if m.get("veneno_arma_ativo"):
            atk["on_hit"] = m.get("veneno_arma_id", "veneno_aranha_sombria")

        hit = await self._execute_one_monster_attack(m, atk, target_obj)

        # Dose consumida no acerto; ação livre: aplicar próxima dose
        if m.get("veneno_arma_ativo") and hit:
            m["veneno_arma_ativo"] = False
        if not m.get("veneno_arma_ativo") and m.get("veneno_doses_extras", 0) > 0:
            m["veneno_doses_extras"] -= 1
            m["veneno_arma_ativo"]   = True
            await self.gm_say(
                f"🧪 **{m['name']}** reaplica o veneno na lança "
                f"({m['veneno_doses_extras']} doses restantes).")

    # ── IA Kobold Besteiro ────────────────────────────────────────────────────
    async def _ai_kobold_besteiro(self, m, targets):
        if m.get("kobold_medo"):
            await self._ai_kobold_medo(m, targets)
            return

        if m.get("virotes", 0) <= 0:
            if not m.get("sem_municao_avisado"):
                m["sem_municao_avisado"] = True
                await self.gm_say(f"🏹 **{m['name']}** ficou sem virotes e tenta fugir!")
            # Fuga: afasta-se do inimigo mais próximo
            if not targets:
                return
            def _dist_fuga(t):
                return max(abs(m["pos"][0] - t["obj"]["pos"][0]),
                           abs(m["pos"][1] - t["obj"]["pos"][1]))
            nearest_pos = min(targets, key=_dist_fuga)["obj"]["pos"]
            flee_x = m["pos"][0] + (m["pos"][0] - nearest_pos[0]) * 20
            flee_y = m["pos"][1] + (m["pos"][1] - nearest_pos[1]) * 20
            kobold_safe = frozenset(tuple(a["pos"]) for a in self.armadilhas
                                    if a.get("kobold_trap") and not a.get("desativada"))
            for _ in range(m.get("movement", 7) + 1):
                pos_antes = list(m["pos"])
                await self._monster_move_step(m, [flee_x, flee_y], avoid_tiles=kobold_safe)
                if m["pos"] == pos_antes:
                    break
            return

        target_obj = self._get_monster_primary_target(m, targets)
        if not target_obj:
            return
        target = target_obj["obj"]

        atk_range = m["attacks"][0].get("range", 4)

        kobold_safe = frozenset(
            tuple(a["pos"]) for a in self.armadilhas
            if a.get("kobold_trap") and not a.get("desativada"))

        def chebyshev():
            return max(abs(m["pos"][0] - target["pos"][0]),
                       abs(m["pos"][1] - target["pos"][1]))

        # Pode atirar = dentro do alcance E com linha de visão (a mesma regra
        # dos jogadores: paredes bloqueiam virotes — sem tiro através delas).
        def pode_atirar():
            return chebyshev() <= atk_range and \
                   self._tem_linha_de_visao(m["pos"], target["pos"])

        # Move até entrar no alcance COM visada (sem precisar estar adjacente)
        if not pode_atirar():
            for _ in range(m.get("movement", 7)):
                pos_antes = list(m["pos"])
                await self._monster_move_step(m, target["pos"], avoid_tiles=kobold_safe)
                if m["pos"] == pos_antes or pode_atirar():
                    break

        if not pode_atirar():
            return   # ainda fora do alcance ou sem linha de visão

        # Prepara ataque — verifica virote especial
        atk = dict(m["attacks"][0])
        if m.get("virotes_especiais_count", 0) > 0:
            tipo = m["virotes_especiais_tipo"]
            if tipo == "incendiario":
                atk["extra_damage"]       = "1d4"
                atk["extra_damage_types"] = ["fire"]
            elif tipo == "veneno_escorpiao_pedra":
                atk["on_hit"] = "veneno_escorpiao_pedra"
            m["virotes_especiais_count"] -= 1

        await self._execute_one_monster_attack(m, atk, target_obj)
        m["virotes"] = max(0, m.get("virotes", 1) - 1)

    async def _run_monster_ai(self, m, targets):
        """Despacha para a IA específica do monstro."""
        ai = m.get("ai_type", "agressivo")
        if ai == "kobold_lanceiro":
            await self._ai_kobold_lanceiro(m, targets)
        elif ai == "kobold_besteiro":
            await self._ai_kobold_besteiro(m, targets)
        elif ai == "lobo_cinzento":
            await self._ai_lobo_cinzento(m, targets)
        elif ai == "esqueleto_humano":
            await self._ai_esqueleto_humano(m, targets)
        elif ai == "esqueleto_animal":
            await self._ai_esqueleto_animal(m, targets)
        elif ai == "crocodilo_jovem":
            await self._ai_crocodilo_jovem(m, targets)
        elif ai == "cobra_constritora":
            await self._ai_cobra_constritora(m, targets)
        elif ai == "cobra_venenosa":
            await self._ai_cobra_venenosa(m, targets)
        elif ai == "devorador_organico":
            await self._ai_devorador_organico(m, targets)
        elif ai == "devorador_metal":
            await self._ai_devorador_metal(m, targets)
        elif ai == "orc_guerreiro":
            await self._ai_orc_guerreiro(m, targets)
        elif ai == "goblin_melee":
            await self._ai_goblin_melee(m, targets)
        elif ai == "goblin_arqueiro":
            await self._ai_goblin_arqueiro(m, targets)
        elif ai == "goblin_xama":
            await self._ai_xama_goblin(m, targets)
        elif ai == "agressivo":
            await self._ai_agressivo(m, targets)
        elif ai == "emboscador":
            await self._ai_emboscador(m, targets)
        elif ai == "necromante":
            await self._ai_necromante(m, targets)
        elif ai == "zumbi":
            await self._ai_zumbi(m, targets)
        elif ai == "lagarto_carniceiro":
            await self._ai_lagarto_carniceiro(m, targets)
        elif ai == "bugbear_sombras":
            await self._ai_bugbear_sombras(m, targets)
        elif ai == "ogro":
            await self._ai_ogro(m, targets)
        # Outros tipos serão adicionados conforme novos monstros forem criados

    async def _ai_agressivo(self, m, targets):
        """IA de monstros agressivos: move na direção do alvo mais próximo
        usando o movimento total do monstro e ataca se adjacente."""
        target_obj = self._get_monster_primary_target(m, targets)
        if not target_obj:
            return
        target = target_obj["obj"]

        if self._is_adjacent_to_monster(target["pos"], m):
            await self._monster_execute_attacks(m, target_obj)
            return

        movement = m.get("movement", 5)
        for _ in range(movement):
            pos_antes = list(m["pos"])
            await self._monster_move_step(m, target["pos"])
            if m["pos"] == pos_antes:   # bloqueado — não conseguiu avançar
                break
            if self._is_adjacent_to_monster(target["pos"], m):
                break

        if self._is_adjacent_to_monster(target["pos"], m):
            await self._monster_execute_attacks(m, target_obj)

    def _alvo_vivo(self, target_obj):
        """True se o alvo (jogador ou animado) ainda está vivo."""
        o = target_obj["obj"]
        if target_obj["kind"] == "player":
            return o.get("alive") and o.get("hp", 0) > 0
        return o.get("vida_atual", 0) > 0

    async def _tentar_desaparecer_sombras(self, m, target):
        """Ação livre após o Manto: se na escuridão e fora de cooldown (5 turnos),
        o bugbear fica oculto (imune a ataques à distância; corpo a corpo -4) até o
        início do próximo turno e move até 3 quadrados em direção ao alvo."""
        if not self._tem_habilidade(m, "desaparecer_nas_sombras"):
            return
        if m.get("ability_cooldowns", {}).get("desaparecer_nas_sombras", 0) > 0:
            return
        if not self._em_escuridao(m):
            return
        m.setdefault("ability_cooldowns", {})["desaparecer_nas_sombras"] = 5
        m["oculto_sombras"] = True
        await self.gm_say(
            f"🌫️ **{m['name']}** **desaparece nas sombras** — imune a ataques à "
            f"distância e difícil de acertar (corpo a corpo: -4) até seu próximo turno!")
        for _ in range(3):
            antes = list(m["pos"])
            await self._monster_move_step(m, target["pos"])
            if m["pos"] == antes:
                break

    async def _ai_bugbear_sombras(self, m, targets):
        """Bugbear das Sombras: aproxima-se do alvo, conjura Manto de Escuridão (1x/
        combate) quando perto — para a zona cobrir o alvo — e Desaparecer nas Sombras
        (ação livre). Nos turnos seguintes ataca da escuridão, ganhando o ataque extra
        do Caçador das Trevas e o bônus do Ataque das Sombras."""
        # Início do turno: o oculto de Desaparecer expira e o cooldown decrementa.
        if m.pop("oculto_sombras", False):
            await self.gm_say(f"👁️ **{m['name']}** reaparece das sombras.")
        cds = m.get("ability_cooldowns")
        if cds:
            for k in list(cds):
                cds[k] = max(0, cds[k] - 1)

        target_obj = self._get_monster_primary_target(m, targets)
        if not target_obj:
            return
        target = target_obj["obj"]

        # Aproxima-se do alvo.
        if not self._is_adjacent_to_monster(target["pos"], m):
            for _ in range(m.get("movement", 7)):
                antes = list(m["pos"])
                await self._monster_move_step(m, target["pos"])
                if m["pos"] == antes or self._is_adjacent_to_monster(target["pos"], m):
                    break

        perto = max(abs(m["pos"][0] - target["pos"][0]),
                    abs(m["pos"][1] - target["pos"][1])) <= 3

        # Manto de Escuridão (1x/combate) quando perto, p/ a zona (raio 3) cobrir o
        # alvo. Em seguida, Desaparecer nas Sombras (ação livre). Gasta a ação principal.
        if (perto and not self._em_escuridao(m)
                and m.get("ability_uses", {}).get("manto_escuridao", 0) > 0):
            m["ability_uses"]["manto_escuridao"] -= 1
            await self.gm_say(f"🌑 **{m['name']}** conjura **Manto de Escuridão**!")
            # Alcance/duração idênticos à magia (GRIMORIO), conjurada como nível 3.
            magia = GRIMORIO.get("manto_escuridao", {})
            raio  = magia.get("area_raio", 3)
            dur   = self._rolar_dado(magia.get("duracao", "1d4"))
            await self._aplicar_escuridao(m, raio=raio, duracao=dur)
            await self._tentar_desaparecer_sombras(m, target)
            return

        # Ataca (3 ataques) + ataque extra do Caçador das Trevas em área escura.
        if self._is_adjacent_to_monster(target["pos"], m):
            await self._monster_execute_attacks(m, target_obj)
            if self._cacador_trevas_ca_bonus(m) and self._alvo_vivo(target_obj):
                garra = next((a for a in m["attacks"] if a["name"] == "Garras"), m["attacks"][0])
                await self.gm_say("🌑 **Caçador das Trevas** — ataque extra das garras!")
                await self._execute_one_monster_attack(m, garra, target_obj)

    async def _ai_ogro(self, m, targets):
        """Ogro (Clava/Lança): avança até o alvo mais próximo e bate forte.
        Lança = alcance estendido. Usa Força Descomunal assim que disponível;
        Golpe Brutal para finalizar alvos enfraquecidos. Errar → -2 CA (Lento e
        Previsível). Recargas decrementam no início do próprio turno."""
        # Início do turno: limpa o -2 CA do turno anterior e decrementa recargas.
        m.pop("lento_previsivel_ativo", None)
        cds = m.get("ability_cooldowns")
        if cds:
            for k in list(cds):
                cds[k] = max(0, cds[k] - 1)

        target_obj = self._get_monster_primary_target(m, targets)
        if not target_obj:
            return
        target = target_obj["obj"]

        # Aproxima-se até ficar ao alcance (lança alcança a 2 / 1 diagonal).
        if not self._em_alcance_ogro(m, target["pos"]):
            for _ in range(m.get("movement", 5)):
                antes = list(m["pos"])
                await self._monster_move_step(m, target["pos"])
                if m["pos"] == antes or self._em_alcance_ogro(m, target["pos"]):
                    break
        if not self._em_alcance_ogro(m, target["pos"]):
            return

        atk = m["attacks"][0]
        cds = m.setdefault("ability_cooldowns", {})
        alvo_hp = target.get("hp", 0) if target_obj["kind"] == "player" else target.get("vida_atual", 0)
        usar_gb = (self._tem_habilidade(m, "golpe_brutal") and cds.get("golpe_brutal", 0) <= 0
                   and alvo_hp <= 12)                               # finalizar enfraquecidos
        usar_fd = (self._tem_habilidade(m, "forca_descomunal") and cds.get("forca_descomunal", 0) <= 0)

        if usar_gb:                                                 # Golpe Brutal (finalizar)
            cds["golpe_brutal"] = 3
            m["_golpe_brutal_ativo"] = True
            await self.gm_say(f"💥 **{m['name']}** desfere um **Golpe Brutal** para finalizar (+2 dano)!")
            hit = await self._execute_one_monster_attack(m, atk, target_obj)
            m.pop("_golpe_brutal_ativo", None)
        elif usar_fd:                                              # Força Descomunal (atordoar)
            cds["forca_descomunal"] = 4
            await self.gm_say(f"💪 **{m['name']}** ataca com **Força Descomunal**!")
            hit = await self._execute_one_monster_attack(m, atk, target_obj)
            if hit and self._alvo_vivo(target_obj):
                passou, d20, sb, stot = self._testar_save(target, "fortitude", 10)
                sbs = f"+{sb}" if sb >= 0 else str(sb)
                await self.broadcast({"type": "dice_roll", "die": "d20", "value": d20,
                                       "label": f"{m['name']} — Força Descomunal", "hit": not passou})
                tgt_name = target["name"] if target_obj["kind"] == "player" else target["nome"]
                if passou:
                    await self.gm_say(f"💪 **{tgt_name}** aguenta o impacto (Fortitude d20({d20}){sbs}={stot} vs CD 10).")
                else:
                    target["perde_turno"] = True
                    await self.gm_say(f"💫 **{tgt_name}** fica **atordoado** (Fortitude {stot} vs CD 10) e perde a próxima rodada!")
        else:                                                      # ataque normal
            hit = await self._execute_one_monster_attack(m, atk, target_obj)

        # Lento e Previsível: errou o ataque → -2 CA até o próximo turno.
        if not hit and self._tem_habilidade(m, "lento_previsivel"):
            m["lento_previsivel_ativo"] = True
            await self.gm_say(f"🐢 **{m['name']}** erra e fica desequilibrado — **-2 CA** até o próximo turno!")

    def _necro_controla_animado(self, m):
        return any(a.get("dominado_por_monstro") == m["id"]
                   for pp in self.players.values() for a in pp.get("animados", []))

    async def _necro_tentar_dominar(self, m):
        """Pergaminho Dominar Morto-Vivo (uso único, não conta no limite). Domina o
        morto-vivo animado mais forte ao alcance. Retorna True se conjurou."""
        ability = next((ab for ab in m.get("special_abilities", [])
                        if ab["id"] == "dominar_morto_vivo"), None)
        if not ability or m.get("usou_dominar") or self._necro_controla_animado(m):
            return False
        alc = ability.get("range", 4)
        candidatos = [a for pp in self.players.values() for a in pp.get("animados", [])
                      if a.get("vida_atual", 0) > 0 and not a.get("dominado_por_monstro")
                      and max(abs(a["pos"][0]-m["pos"][0]), abs(a["pos"][1]-m["pos"][1])) <= alc]
        if not candidatos:
            return False
        alvo = max(candidatos, key=lambda a: self._nd_criatura(a))
        dc   = 8 + ability.get("circulo", 3) + mod(m.get("int_", 10))
        nd   = self._nd_criatura(alvo)
        m["usou_dominar"] = True   # pergaminho consumido (não dropa no loot)
        await self.gm_say(f"🧙 **{m['name']}** usa o **Pergaminho de Dominar Morto-Vivo** em **{alvo['nome']}**!")
        save_ok, *_ = await self._save_mostrado(alvo, "vontade", dc, extra_mod=nd)
        if save_ok:
            await self.gm_say(f"💀 **{alvo['nome']}** resiste (Vontade vs CD {dc}, ND +{nd}).")
        else:
            alvo["dominado_por_monstro"] = m["id"]
            alvo["dono_original"]        = alvo.get("owner")
            alvo["dominacao"]            = {"cd": dc, "rodada": 2, "permanente": False}
            await self.gm_say(
                f"💀 O necromante toma o controle de **{alvo['nome']}**! Testará Vontade "
                f"(CD {dc}) a cada rodada; 3 falhas seguidas = controle PERMANENTE.")
        return True

    def _necro_cluster(self, heroes):
        """Posição (de um herói) que maximiza heróis no raio 2 — melhor centro de área."""
        if not heroes:
            return None
        def cobre(c):
            return sum(1 for h in heroes
                       if max(abs(h["pos"][0]-c[0]), abs(h["pos"][1]-c[1])) <= 2)
        melhor = max(heroes, key=lambda h: cobre(h["pos"]))
        return list(melhor["pos"])

    def _necro_heroes_no_raio(self, heroes, centro, raio):
        return sum(1 for h in heroes
                   if max(abs(h["pos"][0]-centro[0]), abs(h["pos"][1]-centro[1])) <= raio)

    async def _necro_cast(self, m, magia_id, centro):
        """Conjura uma magia de área do necromante centrada em `centro` (heróis).
        Só conjura se o centro estiver no alcance. Retorna True se conjurou."""
        magia = GRIMORIO.get(magia_id)
        if not magia:
            return False
        alc = magia.get("alcance")
        if alc is None and "alcance_base" in magia:
            alc = magia["alcance_base"] + magia.get("alcance_escala", 0) * (m.get("level", 1) - 1)
        if alc is not None:
            d = max(abs(m["pos"][0]-centro[0]), abs(m["pos"][1]-centro[1]))
            if d > alc:
                return False
        await self._executar_magia_grimorio(m, magia, {"tx": centro[0], "ty": centro[1]}, 1, 0)
        return True

    async def _ai_necromante(self, m, targets):
        """Conjurador ND 2: abre com Bola de Fogo no grupo, Medo p/ dispersar,
        Amaldiçoar p/ enfraquecer; rouba mortos-vivos animados (pergaminho Dominar);
        Concentração Sombria (Vontade CD 10 ao sofrer dano) e fuga sem servos."""
        # Concentração Sombria: snapshot de HP; se sofreu dano, Vontade CD 10 ou sem magia.
        ref    = m.get("_cs_hp_ref", m.get("max_hp", m["hp"]))
        sofreu = m["hp"] < ref
        m["_cs_hp_ref"] = m["hp"]
        pode_magia = True
        if sofreu and any(ab["id"] == "concentracao_sombria" for ab in m.get("special_abilities", [])):
            ok, d20, sb, tot = self._testar_save(m, "vontade", 10)
            if ok:
                await self.gm_say(f"🧙 **{m['name']}** mantém a concentração (Vontade {tot} vs CD 10).")
            else:
                pode_magia = False
                await self.gm_say(f"💥 **{m['name']}** perde a concentração — sem magia neste turno! (Vontade {tot} vs CD 10)")

        heroes = [p for p in self.players.values() if self._ativo(p)]
        uses   = m.get("ability_uses", {})

        # Instinto de Sobrevivência: sem mortos-vivos por perto (≤6) → tenta fugir.
        undead_perto = any(
            o["hp"] > 0 and o.get("undead") and o["id"] != m["id"]
            and max(abs(o["pos"][0]-m["pos"][0]), abs(o["pos"][1]-m["pos"][1])) <= 6
            for o in self.monsters.values())
        if not undead_perto and not self._necro_controla_animado(m):
            await self._fugir_monstro(m)
            return

        if pode_magia:
            # Pergaminho Dominar Morto-Vivo (não conta no limite das 3 magias).
            if await self._necro_tentar_dominar(m):
                return
            centro = self._necro_cluster(heroes)
            if centro:
                grupo = self._necro_heroes_no_raio(heroes, centro, 2) >= 2
                # Abre com Bola de Fogo se há grupo.
                if grupo and uses.get("bola_fogo", 0) > 0:
                    if await self._necro_cast(m, "bola_fogo", centro):
                        uses["bola_fogo"] -= 1; return
                # Amaldiçoar p/ enfraquecer (raio 1).
                if uses.get("amaldicoar", 0) > 0 and self._necro_heroes_no_raio(heroes, centro, 1) >= 1:
                    if await self._necro_cast(m, "amaldicoar", centro):
                        uses["amaldicoar"] -= 1; return
                # Medo p/ dispersar grupo.
                if grupo and uses.get("medo", 0) > 0:
                    if await self._necro_cast(m, "medo", centro):
                        uses["medo"] -= 1; return
                # Sobrando: usa Bola de Fogo / Medo mesmo em alvo único.
                if uses.get("bola_fogo", 0) > 0 and await self._necro_cast(m, "bola_fogo", centro):
                    uses["bola_fogo"] -= 1; return
                if uses.get("medo", 0) > 0 and await self._necro_cast(m, "medo", centro):
                    uses["medo"] -= 1; return

        # Sem magia disponível: adaga (aproxima e ataca).
        target_obj = self._get_monster_primary_target(m, targets)
        if not target_obj:
            return
        target = target_obj["obj"]
        if not self._is_adjacent_to_monster(target["pos"], m):
            for _ in range(m.get("movement", 5)):
                pa = list(m["pos"])
                await self._monster_move_step(m, target["pos"])
                if m["pos"] == pa or self._is_adjacent_to_monster(target["pos"], m):
                    break
        if self._is_adjacent_to_monster(target["pos"], m):
            await self._monster_execute_attacks(m, target_obj)

    async def _ai_emboscador(self, m, targets):
        """IA da Aranha Sombria: usa teia em alvo distante; morde se adjacente."""
        target_obj = self._get_monster_primary_target(m, targets)
        if not target_obj:
            return
        target = target_obj["obj"]

        adj = self._is_adjacent_to_monster(target["pos"], m)

        if adj:
            await self._monster_execute_attacks(m, target_obj)
        else:
            # Tenta Disparo de Teia se disponível e no alcance
            teia = next((ab for ab in m.get("special_abilities", [])
                         if ab["id"] == "disparo_teia"), None)
            used_teia = False
            if teia:
                dist = max(abs(m["pos"][0] - target["pos"][0]),
                           abs(m["pos"][1] - target["pos"][1]))
                if (m.get("ability_uses", {}).get("disparo_teia", 0) > 0
                        and dist <= teia["range"]):
                    used_teia = await self._use_monster_ability(m, teia, target_obj)
            if not used_teia:
                # Move em direção ao alvo e ataca se ficar adjacente
                await self._monster_move_step(m, target["pos"])
                if self._is_adjacent_to_monster(target["pos"], m):
                    await self._monster_execute_attacks(m, target_obj)

    # ── GM phase (monsters act) ─────────────────────────────────────────────

    async def gm_phase(self):
        alive_monsters = [m for m in self.monsters.values() if m["hp"] > 0]
        alive_players = [p for p in self.players.values() if self._ativo(p)]
        if not alive_monsters or not alive_players:
            return

        await self.gm_say(gm("monster_moves"))

        # Alvos dos monstros = jogadores vivos + animados vivos (de qualquer jogador).
        def _targets():
            # Luccas invisível nas sombras não é escolhido como alvo pelos monstros.
            ts = [{"kind": "player", "obj": p} for p in self.players.values()
                  if self._ativo(p) and not p.get("invisivel_sombras") and not p.get("invisivel_magico")]
            for a in self._all_animados():
                if a.get("dominado_por_monstro"):   # aliado dos monstros — não é alvo deles
                    continue
                ts.append({"kind": "animado", "obj": a})
            return ts

        for m in alive_monsters:
            if m["hp"] <= 0:
                continue
            # Monstro dormente: sala ainda trancada (porta fechada). Não percebe
            # nem persegue os heróis — permanece imóvel até a porta ser aberta.
            room_m = self._room_by_id(m.get("room_id"))
            if room_m and room_m.get("locked"):
                continue
            # Venenos: tica/expira efeitos no início do turno do monstro.
            await self._processar_venenos_turno(m)
            await self._processar_mods_magia_turno(m)   # Amaldiçoar expira por rodada
            if m["hp"] <= 0:
                continue
            # Petrificado: perde o turno (não move nem ataca).
            if m.get("petrificado"):
                await self.gm_say(f"🗿 **{m['name']}** está petrificado e perde o turno!")
                continue
            # Paralisado (Raio Congelante): novo Fortitude; se falhar, perde o turno.
            if m.get("paralisado"):
                if await self._processar_paralisacao_turno(m):
                    continue
            if m.get("perde_turno"):
                m["perde_turno"] = False
                await self.gm_say(f"🕸️ **{m['name']}** está preso (rede) e perde o turno!")
                continue
            # Status de magia (Sono/Comando/Dominar/Medo/Lentidão): pode consumir o turno.
            if await self._status_monstro_turno(m, alive_monsters) == "pulou":
                continue
            targets = _targets()
            if not targets:
                break

            # Monstros com ai_type usam o sistema de IA modular
            if m.get("ai_type"):
                await self._run_monster_ai(m, targets)
                # Provocação tick (igual para todos)
                if m.get("provocado"):
                    m["provocado_turnos"] = max(0, m.get("provocado_turnos", 0) - 1)
                    if m["provocado_turnos"] <= 0:
                        m["provocado"] = False
                        m["provocado_turno_efeito"] = False
                        m["provocado_por"] = None
                continue

            # Prioridade de alvo: Provocação do bardo (por monstro) > Provocar do
            # guerreiro (taunt global) > inimigo mais próximo.
            tobj = None
            if m.get("provocado") and m.get("provocado_turnos", 0) > 0:
                prov_pid = m.get("provocado_por")
                if prov_pid in self.players and self.players[prov_pid]["alive"]:
                    tobj = {"kind": "player", "obj": self.players[prov_pid]}
                else:
                    # Provocador morto/ausente: provocação perde o efeito.
                    m["provocado"] = False
                    m["provocado_turnos"] = 0
                    m["provocado_turno_efeito"] = False
            if tobj is None and self.taunted and self.taunted in self.players and self.players[self.taunted]["alive"]:
                tobj = {"kind": "player", "obj": self.players[self.taunted]}
            if tobj is None:
                tobj = min(targets, key=lambda t: abs(t["obj"]["pos"][0]-m["pos"][0]) + abs(t["obj"]["pos"][1]-m["pos"][1]))
            target = tobj["obj"]
            is_player = tobj["kind"] == "player"
            tgt_name = target["name"] if is_player else target["nome"]

            # D20: monstros atacam só de casas cardinalmente adjacentes
            if self._cardinal_adjacent(m["pos"], target["pos"]):
                if self.smoke.get(m["id"]):
                    self.smoke.pop(m["id"])
                    await self.gm_say(f"💨 **{m['name']}** tenta atacar **{tgt_name}** mas a fumaça confunde!")
                    continue
                if is_player and self.immune.get(target["id"], 0) > 0:
                    await self.gm_say(f"🛡️ **{m['name']}** ataca **{tgt_name}** mas o Escudo Divino bloqueia!")
                    continue

                if is_player:
                    gl_ca = (target.get("guerreiro_luz_bonus", {}).get("ca", 0)
                             if target.get("guerreiro_luz_ativo") else 0)
                    effective_ac = (target["ac"] + self.temp_def.get(target["id"], 0)
                                    + self._cancao_bonus(target, "bonus_ca")
                                    + gl_ca + self._mod_magia(target, "ca"))   # Abençoar (+CA no aliado)
                else:
                    effective_ac = target["ca"]
                # Provocação: o 1º ataque do inimigo provocado é com DESVANTAGEM
                # (rola 2d20 e usa o pior). O efeito vale uma vez (turno de desvantagem).
                # Envia AMBOS os dados ao cliente: o "descartado" (maior) marcado para
                # animar em vermelho, e o "usado" (menor — pior) marcado em verde.
                # Penalidade de veneno no ataque do monstro (cego/escorpião), se houver.
                m_atk = m["atk_bonus"] + self._pen(m, "ataque") + self._mod_magia(m, "ataque")  # Amaldiçoar
                # Desvantagem: Provocação OU atacar às cegas na escuridão. Vantagem: ver na escuridão.
                esc = self._verificar_escuridao(m, target)
                prov = bool(m.get("provocado_turno_efeito"))
                desvantagem = prov or esc == "desvantagem"
                vantagem    = esc == "vantagem"
                if vantagem and desvantagem:
                    vantagem = desvantagem = False
                if prov:
                    m["provocado_turno_efeito"] = False
                if vantagem or desvantagem:
                    hit, roll, total, crit, discarded = self._rolar_ataque(m_atk, effective_ac, vantagem, desvantagem)
                    modo = "vantagem" if vantagem else "desvantagem"
                    motivos = []
                    if prov: motivos.append("provocado")
                    if esc == "desvantagem": motivos.append("escuridão")
                    if esc == "vantagem": motivos.append("vê na escuridão")
                    await self.gm_say(
                        f"⚠️ **{m['name']}** ataca com **{modo}** ({', '.join(motivos)}) — "
                        f"d20 **{roll}** usado, ~~{discarded}~~ descartado.")
                    await self.broadcast({"type": "dice_roll", "die": "d20", "value": discarded,
                                          "label": f"{m['name']} — descartado", "discarded": True})
                    await self.broadcast({"type": "dice_roll", "die": "d20", "value": roll,
                                          "label": f"{m['name']} — {modo}",
                                          "hit": hit, "crit": crit, "kept": True})
                else:
                    hit, roll, total, crit = d20_attack(m_atk, effective_ac)
                    await self.broadcast({"type": "dice_roll", "die": "d20", "value": roll,
                                          "label": m["name"], "hit": hit, "crit": crit})
                # Sono: atacar um alvo dormindo (jogador/minion) é crítico e o desperta.
                if target.get("dormindo"):
                    hit, crit = True, True
                    target.pop("dormindo", None); target.pop("dormindo_rodadas", None)
                    await self.gm_say(f"🌙 **{tgt_name}** é atacado dormindo — golpe **CRÍTICO** e desperta!")
                if hit:
                    raw_dmg = roll_dice(m["damage"])
                    if crit: raw_dmg *= 2
                    dmg = max(1, raw_dmg + self._pen(m, "dano") + self._mod_magia(m, "dano"))  # Amaldiçoar
                    die_type = "d" + m["damage"].split("d")[1]
                    await self.broadcast({"type": "dice_roll", "die": die_type,
                                           "value": raw_dmg, "label": "Dano"})
                    crit_str = " **CRÍTICO!**" if crit else ""
                    if is_player:
                        # Protetor (Richard): divide o dano com o paladino, se ativo
                        dmg_alvo, transfer = await self._processar_dano_protetor(target["id"], dmg)
                        target["hp"] = max(0, target["hp"] - dmg_alvo)
                        await self.gm_say(
                            f"💢 **{m['name']}** ataca **{tgt_name}**"
                            f" (d20={roll}+{m_atk}={total} vs CA {effective_ac}):"
                            f"{crit_str} **{dmg_alvo}** de dano! ({target['hp']}/{target['max_hp']} HP)")
                        if transfer:
                            richard, dano_richard = transfer
                            richard["hp"] = max(0, richard["hp"] - dano_richard)
                            if richard["hp"] <= 0:
                                await self._player_dies(richard["id"])
                        if target["hp"] <= 0:
                            await self._player_dies(target["id"])
                    else:
                        dmg_ef = self._ajustar_dano_elemental(target, dmg, "fisico")   # Pedra/Gelo
                        target["vida_atual"] = max(0, target["vida_atual"] - dmg_ef)
                        await self.gm_say(
                            f"💢 **{m['name']}** ataca **{tgt_name}**"
                            f" (d20={roll}+{m_atk}={total} vs CA {effective_ac}):"
                            f"{crit_str} **{dmg_ef}** de dano! ({target['vida_atual']}/{target['vida_max']} HP)")
                        if target["vida_atual"] <= 0:
                            await self._animado_morre(target, m.get("id"))
                else:
                    await self.gm_say(
                        f"💢 **{m['name']}** ataca **{tgt_name}**"
                        f" (d20={roll}+{m_atk}={total} vs CA {effective_ac}): **ERROU!**")
            else:
                # Move em direção ao alvo — cardinal, sem empilhar (monstros/jogadores/animados)
                dx = 0 if m["pos"][0] == target["pos"][0] else (1 if target["pos"][0] > m["pos"][0] else -1)
                dy = 0 if m["pos"][1] == target["pos"][1] else (1 if target["pos"][1] > m["pos"][1] else -1)
                for adx, ady in [(dx, 0), (0, dy)]:
                    if adx == 0 and ady == 0:
                        continue
                    nx, ny = m["pos"][0]+adx, m["pos"][1]+ady
                    if not self._monster_can_occupy(m, nx, ny):   # footprint multi-tile inteiro livre
                        continue
                    m["pos"] = [nx, ny]
                    break
                # Monstro pisou em armadilha colocável (de aliado)?
                arm = self._armadilha_no_tile(m["pos"][0], m["pos"][1])
                if arm:
                    await self._disparar_armadilha(m, arm)

            # Provocação: consome 1 turno por rodada de monstro; ao zerar, expira.
            if m.get("provocado"):
                m["provocado_turnos"] = max(0, m.get("provocado_turnos", 0) - 1)
                if m["provocado_turnos"] <= 0:
                    m["provocado"] = False
                    m["provocado_turno_efeito"] = False
                    m["provocado_por"] = None

        # Animados roubados por um necromante agem contra os personagens (e re-testam Vontade).
        await self._agir_animados_dominados_por_monstro()

        # Fase 3: prisioneiro libertado segue o herói mais próximo e leva dano de monstros adjacentes.
        await self._processar_prisioneiro_turno()

        self.taunted = None
        # Reset blessed ATK bonus
        for pid2 in list(self.blessed.keys()):
            self.players[pid2]["atk_bonus"] = self.players[pid2]["base_atk_bonus"]
        self.blessed.clear()

        # Restore moves for next round
        for pid2, p in self.players.items():
            if p["alive"]:
                p["moves_left"]        = self._moves_base(p)
                p["action_done"]       = False
                p["bonus_action_used"] = False
                p["moved_this_turn"]   = False
                # Animados recuperam movimento/ação a cada rodada (controle do dono)
                for a in p.get("animados", []):
                    a["moves_left"] = a.get("movimento", 3)
                    a["acted"] = False

        # Check if all players dead
        if not any(p["alive"] for p in self.players.values()):
            await self.end_game(victory=False)

    async def _aplicar_exaustao_rodada(self):
        """Exaustão: jogador com fome OU sede em 0 perde 1 de vida POR RODADA
        (a partir da rodada seguinte ao esgotamento, até fome E sede voltarem
        acima de 0). HP 0 = morte. Roda toda rodada, mesmo sem monstros."""
        for pid2, p in list(self.players.items()):
            if p["alive"] and (p.get("fome", 1) <= 0 or p.get("sede", 1) <= 0):
                p["hp"] = max(0, p["hp"] - 1)
                motivos = []
                if p.get("fome", 1) <= 0: motivos.append("fome")
                if p.get("sede", 1) <= 0: motivos.append("sede")
                await self.gm_say(
                    f"☠️ **{p['name']}** sofre de exaustão ({' e '.join(motivos)}) — "
                    f"**-1 HP** ({p['hp']}/{p['max_hp']}).")
                if p["hp"] <= 0:
                    await self._player_dies(pid2)

    # ── death & XP ─────────────────────────────────────────────────────────

    async def _monster_dies(self, m, killer_pid):
        if m["hp"] > 0: return

        # Resistência Morta (Zumbi): a 0 HP, Fortitude CD 10 → fica com 1 HP. Dano
        # sagrado/luz IGNORA e o destrói de vez (sem retorno).
        rm = next((ab for ab in m.get("special_abilities", [])
                   if ab["id"] == "resistencia_morta"), None)
        if rm:
            if m.get("_dano_sagrado_recente"):
                await self.gm_say(f"✨ **{m['name']}** é **destruído pela luz sagrada** — não há retorno!")
            else:
                ok, d20, sb, tot = self._testar_save(m, "fortitude", rm.get("dc", 10))
                if ok:
                    m["hp"] = 1
                    await self.gm_say(
                        f"🧟 **{m['name']}** recusa-se a tombar! (Fortitude {tot} vs CD {rm.get('dc',10)}) — fica com **1 HP**.")
                    return
                await self.gm_say(f"🧟 **{m['name']}** finalmente tomba (Fortitude {tot} vs CD {rm.get('dc',10)}).")

        # Silêncio do Xamã Goblin termina se ele morrer.
        if any(z.get("tipo") == "silencio" and z.get("caster") == m["id"]
               for z in self.zonas_especiais):
            self.zonas_especiais = [z for z in self.zonas_especiais
                                    if not (z.get("tipo") == "silencio" and z.get("caster") == m["id"])]
            await self.gm_say(f"🔇 O Silêncio de **{m['name']}** se dissipa com sua morte.")

        # Libera jogadores agarrados por este monstro
        for p in self.players.values():
            if p.get("preso_por") == m["id"]:
                p["preso"] = False
                p.pop("preso_por", None)
                await self.gm_say(f"🔓 **{p['name']}** se soltou — o predador foi abatido!")

        # Nível para Animar Mortos: CR fracionário ≤ 0.5 → 1 slot; CR inteiro = round(CR)
        cr = m.get("cr", m.get("tier", 1))
        nivel_animado = 1 if cr <= 0.5 else max(1, round(cr))

        if not m.get("boss") and not m.get("undead"):
            # Mortos-vivos destruídos não deixam cadáver reanimável
            primeiro_ataque = (m.get("attacks") or [{}])[0]
            self.corpses[m["id"]] = {
                "id":        m["id"],
                "nome":      m["name"],
                "icone":     m.get("emoji", "💀"),
                "tipo":      m.get("type", "skeleton"),
                "tier":      m.get("tier", 1),
                "nivel":     nivel_animado,
                "ca":        m.get("ac", 10),
                "vida_max":  m.get("max_hp", m.get("hp", 10)),
                "dano":      primeiro_ataque.get("damage", m.get("damage", "1d4")),
                "movimento": m.get("movement", 3),
                "pos":       list(m["pos"]),
                "room_id":   m.get("room_id"),
            }

        # XP: monstros novos usam fórmula por CR+nível médio; legados usam valor fixo
        share_xp, alive_count = self._calc_monster_xp(m)
        for p in self.players.values():
            if p["alive"]:
                p["xp"] += share_xp
                await self._check_level_up(p)

        # Loot: monstros novos têm tabela própria por monstro; legados usam sala+65%
        mroom = next((r for r in self.rooms if r["id"] == m.get("room_id")), None)

        # ── Loot especial: kobolds ─────────────────────────────────────────────
        if m.get("type", "").startswith("kobold_"):
            await self.gm_say(f"💀 **{m['name']}** foi derrotado! +{share_xp} XP!")
            await self._kobold_loot(m)
            if m.get("boss"):
                await self.end_game(victory=True)
            return

        # ── Loot especial: necromante ───────────────────────────────────────────
        if m.get("type") == "necromante":
            await self.gm_say(f"💀 **{m['name']}** foi derrotado! +{share_xp} XP!")
            await self._necromante_loot(m)
            return

        # ── Loot especial: esqueletos ───────────────────────────────────────────
        if m.get("type") in ("esqueleto_humano", "esqueleto_animal"):
            await self.gm_say(
                f"💀 **{m['name']}** foi destruído! +{share_xp} XP! "
                f"Os ossos perdem a estrutura mágica.")
            if m.get("type") == "esqueleto_humano":
                await self._esqueleto_loot(m)
            return

        if "loot_table" in m:
            # Sistema novo: loot individual ao morrer
            loot = self._roll_monster_loot(m)
            gold = 0
            loot_items = []
            if loot:
                if loot.get("tipo") == "gold":
                    gv = loot.get("valor", loot.get("amount", 0))
                    gold = roll_dice(gv) if isinstance(gv, str) else gv
                elif loot.get("tipo") == "item":
                    item_def = (
                        next((i for i in CHEST_ITEMS    if i["id"] == loot["id"]), None) or
                        next((i for i in SHOP_WEAPONS   if i["id"] == loot["id"]), None) or
                        next((i for i in SHOP_MERCHANT  if i["id"] == loot["id"]), None)
                    )
                    if item_def:
                        loot_items.append(deepcopy(item_def))
                elif loot.get("tipo") == "scroll":
                    sc = gerar_pergaminho(loot.get("circulo", 1), loot.get("classe"),
                                          magia_id=loot.get("magia_id"))
                    if sc:
                        loot_items.append(sc)
                elif loot.get("tipo") == "comida":
                    fd = self._loot_comida()
                    if fd:
                        loot_items.append(fd)
                elif loot.get("tipo") == "raro_xama":
                    # 50% Poção de Cura / 50% Pergaminho de 1º círculo (mago ou clérigo).
                    if random.random() < 0.5:
                        pot = next((i for i in SHOP_MERCHANT if i["id"] == "health_potion"), None)
                        if pot:
                            loot_items.append(deepcopy(pot))
                    else:
                        # 95% básico (nível 1, +0); 5% reforçado (+1 INT ou nível 2).
                        if random.random() < 0.05:
                            sc = (gerar_pergaminho(1, int_bonus=1) if random.random() < 0.5
                                  else gerar_pergaminho(1, nivel=2))
                        else:
                            sc = gerar_pergaminho(1)
                        if sc:
                            loot_items.append(sc)
            # Loot garantido (ex.: "arma equipada" do Orc) — sempre dropa.
            for gid in m.get("guaranteed_loot", []):
                gdef = (
                    next((i for i in CHEST_ITEMS   if i["id"] == gid), None) or
                    next((i for i in SHOP_WEAPONS  if i["id"] == gid), None) or
                    next((i for i in SHOP_MERCHANT if i["id"] == gid), None)
                )
                if gdef:
                    loot_items.append(deepcopy(gdef))
            chest_msg = ""
            if loot_items or gold > 0:
                self._spawn_chest(list(m["pos"]), gold, loot_items)
                chest_msg = " Um **baú de saque** apareceu!"
            await self.gm_say(f"💀 **{m['name']}** foi derrotado! +{share_xp} XP!{chest_msg}")
        else:
            # Sistema legado: baú só quando a sala toda é limpa
            gold = m.get("gold", 0)
            if mroom:
                living = [mm for mm in self.monsters.values()
                          if mm.get("room_id") == mroom["id"] and mm["hp"] > 0]
                if not living:
                    mroom["cleared"] = True
                    loot_items = []
                    if random.random() < 0.65:
                        loot_items.append(deepcopy(random.choice(CHEST_ITEMS)))
                    if loot_items or gold > 0:
                        self._spawn_chest(list(m["pos"]), gold, loot_items)
                        await self.gm_say(f"💀 **{m['name']}** foi derrotado! +{share_xp} XP! Um **baú de saque** apareceu!")
                    else:
                        await self.gm_say(f"💀 **{m['name']}** foi derrotado! +{share_xp} XP!")
                else:
                    await self.gm_say(f"💀 **{m['name']}** foi derrotado! +{share_xp} XP!")
            else:
                await self.gm_say(f"💀 **{m['name']}** foi derrotado! +{share_xp} XP!")

        if m.get("boss"):
            await self.end_game(victory=True)

    async def _player_dies(self, pid):
        p = self.players[pid]
        if not p["alive"]: return
        # Regeneração: se ainda há reserva, reergue com 1 HP em vez de cair (-3 fome/sede).
        if p.get("regen_ressurge") and p.get("regen_pool", 0) > 0:
            p["hp"] = 1
            p["fome"] = max(0, p.get("fome", 0) - 3)
            p["sede"] = max(0, p.get("sede", 0) - 3)
            p.pop("regen_pool", None); p.pop("regen_ressurge", None)
            await self.gm_say(f"🌿 **{p['name']}** seria derrotado, mas a **Regeneração** o reergue com 1 HP! (-3 fome/sede)")
            return
        p["alive"] = False
        p["hp"] = 0
        await self.gm_say(f"💔 **{p['name']}** foi derrotado! Os companheiros devem continuar...")

        # Bardo incapacitado: a Canção Heroica cessa e os aliados perdem os buffs.
        if p.get("cancao_ativa"):
            msg = self._interromper_cancao(p, "Henrique foi incapacitado")
            if msg: await self.gm_say(msg)

        # Paladino incapacitado: todas as habilidades sustentadas se desfazem.
        if p.get("class_id") == "paladin":
            p["golpe_sagrado_ativo"] = False
            p["protetor_ativo"]      = False
            p["protetor_alvo"]       = None
            p["regeneracao_ativa"]   = False
            p["guerreiro_luz_ativo"] = False
            p["guerreiro_luz_bonus"] = {}
            p["guerreiro_luz_custo"] = {"fome": 0, "sede": 0}
            await self.gm_say(f"💫 **{p['name']}** é incapacitado — todas as habilidades sagradas se desfazem.")

        # Se o mestre morre, seus animados viram pó imediatamente.
        if p.get("animados"):
            p["animados"] = []
            await self.gm_say("💨 Sem seu mestre, os servos mortos-vivos desfazem-se em pó!")

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

    # ── Fase 3: avaliação de objetivos ──────────────────────────────────────

    async def _conceder_bonus_secundario(self, obj):
        """Concede XP+ouro ao grupo por um objetivo secundário cumprido."""
        for p in self.players.values():
            if p.get("alive"):
                p["xp"] += OBJ_BONUS_XP
                p["gold"] += OBJ_BONUS_OURO
                await self._check_level_up(p)
        nome = (obj or {}).get("type", "objetivo")
        await self.gm_say(f"⭐ Objetivo secundário **{nome}** cumprido! +{OBJ_BONUS_XP} XP, +{OBJ_BONUS_OURO} ouro ao grupo.")

    def _objetivo_cumprido(self, obj):
        """True se o objetivo `obj` está cumprido no estado atual (só autorado)."""
        t = (obj or {}).get("type")
        vivos = [m for m in self.monsters.values() if m["hp"] > 0]
        if t == "kill_all":
            return len(vivos) == 0
        if t == "kill_target":
            alvos = [m for m in self.monsters.values() if m.get("authored_target")]
            return bool(alvos) and all(m["hp"] <= 0 for m in alvos)
        if t == "reach_exit":
            return self.exit_pos is not None and any(
                p["pos"] == self.exit_pos for p in self.players.values() if p.get("alive"))
        if t == "open_key_chest":
            return bool(getattr(self, "key_chest_opened", False))
        if t == "rescue_prisoner":
            if not self.prisoner or not self.prisoner.get("freed") or not self.prisoner.get("alive"):
                return False
            destino = self.exit_pos or self.stairs_pos
            if not destino:
                return False
            px, py = self.prisoner["pos"]
            return max(abs(px - destino[0]), abs(py - destino[1])) <= 1
        return False

    def _objetivo_status(self, obj):
        if obj and obj.get("type") == "rescue_prisoner" and self.rescue_failed:
            return "failed"
        return "done" if self._objetivo_cumprido(obj) else "pending"

    async def _check_objectives(self):
        """Catch-all chamado por push_state. Recalcula o status p/ o HUD e, se o
        principal está cumprido, concede bônus dos secundários e encerra em vitória."""
        if not self.objectives:
            return
        prim = self.objectives.get("primary")
        secs = self.objectives.get("secondary") or []
        self.objective_status = {
            "primary": {"type": (prim or {}).get("type"), "status": self._objetivo_status(prim)},
            "secondary": [{"type": s.get("type"), "status": self._objetivo_status(s)} for s in secs],
        }
        if (self.phase == "playing" and not self._objetivo_concluido
                and prim and self._objetivo_cumprido(prim)):
            self._objetivo_concluido = True
            for s in secs:
                if self._objetivo_cumprido(s):
                    await self._conceder_bonus_secundario(s)
            if (self.mode == "campaign" and self.campaign
                    and self.campaign_phase < len(self.campaign["dungeons"]) - 1):
                # Avança para a próxima fase via cidade/loja.
                self.campaign_phase += 1
                self.dungeon_generated = False     # próxima entrada carrega a nova fase
                self._objetivo_concluido = False   # a nova fase tem seus próprios objetivos
                await self.gm_say("🏆 Fase concluída! Retornem à cidade antes da próxima masmorra.")
                await self._voltar_para_cidade()
            else:
                await self.end_game(victory=True)

    async def handle_libertar_prisioneiro(self, pid):
        if not self._is_turn(pid):
            return
        p = self.players.get(pid)
        if not p or not p.get("alive") or p.get("action_done"):
            return
        if not self.prisoner or not self.prisoner.get("alive") or self.prisoner.get("freed"):
            await self.send_to(pid, {"type": "error", "msg": "Não há prisioneiro para libertar."}); return
        px, py = p["pos"]; bx, by = self.prisoner["pos"]
        if max(abs(px - bx), abs(py - by)) > 1:
            await self.send_to(pid, {"type": "error", "msg": "Aproxime-se do prisioneiro."}); return
        self.prisoner["freed"] = True
        p["action_done"] = True
        await self.gm_say(f"🔓 **{p['name']}** libertou o prisioneiro!")
        await self.push_state()

    async def _processar_prisioneiro_turno(self):
        """Prisioneiro libertado: 1 passo em direção ao herói vivo mais próximo;
        depois, cada monstro adjacente o fere. Morte → rescue_failed (não encerra)."""
        pr = self.prisoner
        if not pr or not pr.get("freed") or not pr.get("alive"):
            return
        herois = [p for p in self.players.values() if self._ativo(p)]
        if herois:
            alvo = min(herois, key=lambda p: max(abs(p["pos"][0] - pr["pos"][0]),
                                                 abs(p["pos"][1] - pr["pos"][1])))
            self._step_towards(pr, alvo["pos"])
        # Dano de monstros adjacentes (caminho dedicado, simples e isolado).
        for m in self.monsters.values():
            if m["hp"] <= 0:
                continue
            if max(abs(m["pos"][0] - pr["pos"][0]), abs(m["pos"][1] - pr["pos"][1])) <= 1:
                dano = random.randint(2, 5)
                pr["hp"] -= dano
                await self.gm_say(f"⚔️ Um monstro fere o prisioneiro ({dano})!")
                if pr["hp"] <= 0:
                    pr["alive"] = False
                    self.rescue_failed = True
                    await self.gm_say("☠️ O prisioneiro foi morto! O resgate falhou.")
                    break

    def _step_towards(self, ent, dest):
        """Move `ent` (dict com 'pos') 1 casa em direção a `dest` por casa livre
        (FLOOR/DOOR, não ocupada por monstro/herói). Sem diagonal."""
        ex, ey = ent["pos"]; dx, dy = dest
        opcoes = sorted([(ex + sx, ey + sy) for sx, sy in ((1,0),(-1,0),(0,1),(0,-1))],
                        key=lambda c: max(abs(c[0] - dx), abs(c[1] - dy)))
        ocup = {tuple(m["pos"]) for m in self.monsters.values() if m["hp"] > 0}
        ocup |= {tuple(p["pos"]) for p in self.players.values() if p.get("alive")}
        for nx, ny in opcoes:
            if (0 <= nx < self.map_w and 0 <= ny < self.map_h
                    and self.tiles[ny][nx] != WALL and (nx, ny) not in ocup):
                ent["pos"] = [nx, ny]; return

    async def end_game(self, victory):
        self.phase = "ended"
        self._cancelar_timer_turno()
        if victory:
            self.dungeon_generated = False   # masmorra concluída: uma nova entrada geraria outra

        text = gm("victory") if victory else gm("defeat")
        await self.gm_say(text)
        await self.broadcast({"type": "game_over", "victory": victory})

    # ── state serialisation ─────────────────────────────────────────────────

    def _is_turn(self, pid):
        return self.phase == "playing" and self.current_pid() == pid

    # Raio (Chebyshev) de visão AO VIVO ao redor de cada minion (animado/elemental).
    # Recomputado a cada broadcast: revela área + monstros enquanto o minion está lá
    # e reverte sozinho à névoa quando ele sai/morre (não grava em `explored`).
    MINION_VISAO_RAIO = 2

    def _live_reveal_tiles(self):
        """Tiles com visibilidade ao vivo neste broadcast: Clarividência (magic_reveal)
        + raio ao redor de cada minion vivo. Não persiste — some quando o minion sai."""
        tiles = set(self.magic_reveal.keys())
        r = self.MINION_VISAO_RAIO
        for a in self._all_animados():
            if a.get("vida_atual", 0) <= 0:
                continue
            ax, ay = a["pos"]
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    x, y = ax + dx, ay + dy
                    if not (0 <= x < self.map_w and 0 <= y < self.map_h):
                        continue
                    # Mesma regra do herói: não revela o interior de sala trancada.
                    if self._tile_in_locked_room(x, y):
                        continue
                    tiles.add((x, y))
        return tiles

    def _campaign_payload(self):
        if self.mode == "campaign" and self.campaign:
            return {"name": self.campaign.get("name"),
                    "phase": self.campaign_phase + 1,
                    "total": len(self.campaign["dungeons"])}
        return None

    async def push_state(self):
        await self._check_objectives()
        await self.broadcast({
            "type": "game_state",
            "tiles": self.tiles,
            "rooms": self.rooms,
            "players": list(self.players.values()),
            "monsters": [m for m in self.monsters.values() if m["hp"] > 0],
            "corpses": list(self.corpses.values()),
            "traps": [t for t in self.traps if not t["triggered"] and tuple(t["pos"]) in self.explored],
            "armadilhas": self._serializar_armadilhas(),
            "zonas_especiais": [z for z in self.zonas_especiais if z.get("ativa")],
            "explored": [list(e) for e in self.explored],
            "revealed": [list(k) for k in self._live_reveal_tiles()],   # Clarividência + visão ao vivo dos minions
            "stairs_pos": self.stairs_pos,
            "campaign": self._campaign_payload(),
            "objectives": self.objective_status,
            "exit_pos": self.exit_pos,
            "prisoner": self.prisoner,
            "current_turn": self.current_pid(),
            "animados_turn": self.animados_phase_pid,   # pid no turno dos servos (ou None)
            "turn_timer_started": self.turn_timer_started_ms,  # epoch ms do início do turno (p/ contagem 30s)
            "turn_timer_limit": self.TURN_LIMIT_S,
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

def _delta(v):
    """Sanitiza um passo de movimento vindo do cliente: somente -1, 0 ou +1.
    Sem isto, um cliente alterado podia enviar move {dx:5} e teleportar 5
    casas pagando 1 de movimento (handle_move valida o destino, não o salto)."""
    try:
        v = int(v)
    except (TypeError, ValueError):
        return 0
    return max(-1, min(1, v))


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

                elif t == "rejoin":
                    # Reconexão: religa este WebSocket a um jogador que caiu no
                    # meio da partida (fora do lobby o jogador permanece em
                    # room.players — só a conexão é descartada no disconnect).
                    code = (msg.get("code") or "").upper()
                    name = (msg.get("name") or "")[:20]
                    alvo_room = rooms.get(code)
                    if not alvo_room:
                        await err("Sala não encontrada para reconexão.")
                        continue
                    alvo = next((p for p in alvo_room.players.values()
                                 if p["name"] == name), None)
                    if not alvo:
                        await err("Jogador não encontrado nesta sala.")
                        continue
                    if alvo["id"] in alvo_room.connections:
                        await err("Esse jogador ainda está conectado.")
                        continue
                    pid  = alvo["id"]          # religa identidade antiga
                    room = alvo_room
                    room.connections[pid] = ws
                    alvo["connected"] = True   # volta a contar nos turnos
                    # Reenvia a sequência de mensagens que coloca o cliente na
                    # tela correta da fase atual.
                    if room.phase == "lobby":
                        await room.broadcast_lobby()
                    elif room.phase == "city":
                        await ws.send(json.dumps({"type": "game_start"}))
                        await room.broadcast_city_state()
                        await room.gm_say(f"🔌 **{name}** reconectou-se à aventura.")
                    else:   # playing — o personagem REENTRA pela escada de entrada
                        ent = next((r for r in room.rooms if r["role"] == "entrance"),
                                   (room.rooms[0] if room.rooms else None))
                        if ent:
                            alvo["pos"] = [ent["cx"], ent["cy"]]
                        await ws.send(json.dumps({"type": "game_start"}))
                        await ws.send(json.dumps({"type": "enter_dungeon"}))
                        room._iniciar_timer_turno()   # reativa o timer caso estivesse parado
                        await room.push_state()
                        await room.gm_say(f"🔌 **{name}** reconectou-se e voltou à masmorra!")

                elif t == "select_class":
                    if room: await room.select_class(pid, msg.get("class_id"))

                elif t == "select_dungeon":
                    if room: await room.handle_select_dungeon(pid, msg.get("file"))

                elif t == "select_campaign":
                    if room: await room.handle_select_campaign(pid, msg.get("file"))

                elif t == "start_game":
                    if room: await room.start_game(pid)

                elif t == "move":
                    dx, dy = _delta(msg.get("dx", 0)), _delta(msg.get("dy", 0))
                    # Exatamente 1 casa ortogonal por mensagem (regra do tabuleiro)
                    if room and abs(dx) + abs(dy) == 1:
                        await room.handle_move(pid, dx, dy)

                elif t == "open_door":
                    if room: await room.handle_open_door(pid, int(msg.get("tx", -1)), int(msg.get("ty", -1)))

                elif t == "libertar_prisioneiro":
                    if room: await room.handle_libertar_prisioneiro(pid)

                elif t == "attack":
                    if room: await room.handle_attack(pid, msg.get("target_id"), msg.get("buffs"))

                elif t == "throw":
                    if room: await room.handle_throw(pid, msg.get("target_id"), msg.get("slot"))

                elif t == "skill":
                    if room: await room.handle_skill(pid, msg.get("skill_id"), msg.get("target_id"))

                elif t == "magia":
                    if room: await room.handle_magia(pid, msg)

                elif t == "aprimorar_magia":
                    if room: await room.handle_aprimorar_magia(pid, msg)

                elif t == "estender_magia":
                    if room: await room.handle_estender_magia(pid, msg)

                elif t == "fortalecer_magia":
                    if room: await room.handle_fortalecer_magia(pid, msg)

                elif t == "ativar_cancao":
                    if room: await room.handle_ativar_cancao(pid, msg)

                elif t == "desativar_cancao":
                    if room: await room.handle_desativar_cancao(pid)

                elif t == "provocacao":
                    if room: await room.handle_provocacao(pid, msg)

                elif t == "cura":
                    if room: await room.handle_cura(pid, msg)

                elif t == "cura_area":
                    if room: await room.handle_cura_area(pid, msg)

                elif t == "purificacao":
                    if room: await room.handle_purificacao(pid, msg)

                elif t == "ressurreicao":
                    if room: await room.handle_ressurreicao(pid, msg)

                elif t == "imposicao_maos":
                    if room: await room.handle_imposicao_maos(pid, msg)

                elif t == "golpe_sagrado":
                    if room: await room.handle_golpe_sagrado(pid, msg)

                elif t == "desativar_golpe_sagrado":
                    if room: await room.handle_desativar_golpe_sagrado(pid)

                elif t == "protetor":
                    if room: await room.handle_protetor(pid, msg)

                elif t == "desativar_protetor":
                    if room: await room.handle_desativar_protetor(pid)

                elif t == "acao_livre_richard":
                    if room: await room.handle_acao_livre_richard(pid, msg)

                elif t == "animar_mortos":
                    if room: await room.handle_animar_mortos(pid, msg)

                elif t == "comandar_animados":
                    if room: await room.handle_comandar_animados(pid)

                elif t == "mover_animado":
                    dx, dy = _delta(msg.get("dx", 0)), _delta(msg.get("dy", 0))
                    if room and abs(dx) + abs(dy) == 1:
                        await room.handle_mover_animado(pid, msg.get("animado_id"), dx, dy)

                elif t == "atacar_animado":
                    if room: await room.handle_atacar_animado(pid, msg.get("animado_id"), msg.get("target_id"))

                elif t == "criar_armadilha":
                    if room: await room.handle_criar_armadilha(pid, msg)

                elif t == "desarmar_armadilha":
                    if room: await room.handle_desarmar_armadilha(pid, msg)

                elif t == "detectar_armadilhas":
                    if room: await room.handle_detectar_armadilhas(pid, msg)

                elif t == "esconder_sombras":
                    if room: await room.handle_esconder_sombras(pid, msg)

                elif t == "veneno_rapido":
                    if room: await room.handle_veneno_rapido(pid, msg)

                elif t == "use_item":
                    if room: await room.handle_use_item(pid, msg.get("item_id"))

                elif t == "use_scroll":
                    if room: await room.handle_use_scroll(pid, msg.get("item_id"), msg)

                elif t == "end_turn":
                    if room: await room.handle_end_turn(pid)

                elif t == "shop_buy":
                    if room: await room.handle_shop_buy(pid, msg.get("shop"), msg.get("item_id"))

                elif t == "sell_item":
                    if room: await room.handle_shop_sell(pid, msg.get("item_slot"))

                elif t == "equip_from_bag":
                    if room: await room.handle_equip_from_bag(pid, int(msg.get("slot_index", -1)))

                elif t == "equip_offhand":
                    if room: await room.handle_equip_offhand(pid, int(msg.get("slot_index", -1)))

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
            elif pid in room.players:
                # Caiu/saiu durante a partida: personagem deixa a masmorra,
                # turno avança se for o caso, os outros continuam jogando.
                await room.handle_disconnect_em_jogo(pid)

# ─── STATIC FILE SERVING (mesma porta do WebSocket) ───────────────────────────
# Servir o cliente (index.html, game.js, src/, assets/...) pela MESMA porta 8765
# permite que UM único túnel https cubra a página E o WebSocket (wss) no mesmo
# domínio. Sem isso, página https + ws inseguro dá erro de "mixed content" e os
# amigos teriam de digitar o endereço do servidor à mão. Ver process_request.

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Tipos que o mimetypes do sistema às vezes não conhece (varia por SO).
for _ext, _ct in (
    (".js", "application/javascript"), (".mjs", "application/javascript"),
    (".css", "text/css"), (".json", "application/json"),
    (".glb", "model/gltf-binary"), (".gltf", "model/gltf+json"),
    (".woff2", "font/woff2"), (".woff", "font/woff"), (".ttf", "font/ttf"),
    (".svg", "image/svg+xml"), (".png", "image/png"), (".jpg", "image/jpeg"),
    (".webp", "image/webp"), (".ico", "image/x-icon"),
):
    mimetypes.add_type(_ct, _ext)

# Só estes diretórios/arquivos da raiz são servidos — evita expor server.py,
# .git, memórias etc. Subpastas listadas liberam todo o conteúdo recursivamente.
_STATIC_ROOTS = ("src", "assets")
_STATIC_FILES = {"index.html", "game.js", "game.css"}

def _http(status, reason, body, ctype="text/plain; charset=utf-8"):
    if isinstance(body, str):
        body = body.encode("utf-8")
    headers = Headers({"Content-Type": ctype,
                       "Content-Length": str(len(body)),
                       "Cache-Control": "no-cache"})
    return Response(status, reason, headers, body)

def _serve_static(request):
    """Resolve o caminho pedido pelo navegador para um arquivo do cliente.
    Protege contra path traversal e só expõe o necessário para jogar."""
    raw = request.path.split("?", 1)[0].split("#", 1)[0]   # tira cache-buster ?v=
    rel = raw.lstrip("/") or "index.html"
    full = os.path.normpath(os.path.join(BASE_DIR, rel))
    # Mantém dentro de BASE_DIR (bloqueia ../ e caminhos absolutos)
    if full != BASE_DIR and not full.startswith(BASE_DIR + os.sep):
        return _http(403, "Forbidden", "403 Forbidden")
    # Allow-list: arquivo solto liberado OU dentro de um dir estático permitido
    top = rel.replace("\\", "/").split("/", 1)[0]
    if rel not in _STATIC_FILES and top not in _STATIC_ROOTS:
        return _http(404, "Not Found", "404 Not Found")
    if not os.path.isfile(full):
        return _http(404, "Not Found", "404 Not Found")
    try:
        with open(full, "rb") as f:
            body = f.read()
    except OSError:
        return _http(404, "Not Found", "404 Not Found")
    ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
    if ctype.startswith("text/") or ctype in (
            "application/javascript", "application/json", "image/svg+xml"):
        ctype += "; charset=utf-8"
    return _http(200, "OK", body, ctype)

def process_request(connection, request):
    """Chamado a cada requisição na porta do servidor. Handshake de WebSocket
    (header `Upgrade: websocket`) → segue o fluxo normal de jogo (return None).
    Qualquer outra coisa é um navegador pedindo a página/recursos → serve estático."""
    if request.headers.get("Upgrade", "").lower() == "websocket":
        return None
    return _serve_static(request)

# ─── MAIN ─────────────────────────────────────────────────────────────────────

async def main():
    # Force UTF-8 on Windows terminals (prevents UnicodeEncodeError with special chars)
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, TypeError):
        pass

    print("=" * 60)
    print("  LEGENDS FOR HIRE - Servidor (jogo + WebSocket na mesma porta)")
    print("=" * 60)
    print("  Local:    http://localhost:8765/index.html")
    print()
    print("  Para jogar na internet (link unico para os amigos):")
    print("    1) Deixe este servidor rodando")
    print("    2) Em outro terminal abra um tunel para a porta 8765, ex.:")
    print("         cloudflared tunnel --url http://localhost:8765")
    print("         (ou: ngrok http 8765)")
    print("    3) Compartilhe o link https gerado + /index.html")
    print("  Os amigos so abrem o link, escolhem o nome e entram pelo codigo.")
    print("=" * 60)

    # process_request serve os arquivos do cliente na mesma porta → um único
    # túnel https cobre página + wss, sem mixed content nem digitar endereço.
    async with websockets.serve(handler, "0.0.0.0", 8765,
                                process_request=process_request):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
