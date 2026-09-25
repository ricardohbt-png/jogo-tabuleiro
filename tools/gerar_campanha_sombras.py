"""Gerador da campanha "Sombras sob Alva e Luz".

Roda da raiz do projeto:
    python tools/gerar_campanha_sombras.py            # valida e grava
    python tools/gerar_campanha_sombras.py --simular  # só relata (ND por sala, avisos, artes)
    python tools/gerar_campanha_sombras.py --forcar   # regrava masmorra editada à mão

Spec: docs/superpowers/specs/2026-09-25-campanha-sombras-alva-e-luz-design.md

Só toca no que é dele: as 4 masmorras `sombras_*.json`, os destinos `sombras_*` de
world_adventures.json, a conversa `sombras_caravanas` do Bartender e o anel
`anel_garra_negra`. Tudo o mais é relido e regravado intacto.
"""
import argparse
import hashlib
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
import server as S  # noqa: E402

WALL, FLOOR, DOOR = S.WALL, S.FLOOR, S.DOOR

ARQUIVOS = ("sombras_1_vau.json", "sombras_2_minas.json",
            "sombras_3a_saloes.json", "sombras_3b_trono.json")
ANEL_ID = "anel_garra_negra"
CONVERSA_ID = "sombras_caravanas"
FATO_GANCHO = "sombras_caravanas"
ASSINATURAS = os.path.join(RAIZ, "tools", ".sombras_assinaturas.json")
MUSICA_ABERTURA = "assets/story/a_song_of_old_stones.mp3"
MUSICA_TROLL = "assets/story/the_kraken_s_overture.mp3"


# ─── Mapa ────────────────────────────────────────────────────────────────────
class Mapa:
    """Grade de paredes onde se cavam salas retangulares separadas por UMA parede;
    a porta entre duas salas vizinhas é a casa dessa parede e entra na lista
    `doors` das duas (door_rooms destranca toda sala que a lista)."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.tiles = [[WALL] * w for _ in range(h)]
        self.rooms = []

    def sala(self, rid, x, y, w, h, role="monster", locked=True, **extra):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.tiles[yy][xx] = FLOOR
        room = {"id": rid, "x": x, "y": y, "w": w, "h": h, "role": role,
                "locked": locked, "doors": []}
        room.update(extra)
        self.rooms.append(room)
        return room

    def porta(self, x, y, *rids):
        self.tiles[y][x] = DOOR
        for rid in rids:
            self._room(rid)["doors"].append([x, y])

    def _room(self, rid):
        return next(r for r in self.rooms if r["id"] == rid)

    def em(self, rid, dx, dy):
        """Casa absoluta a partir do canto da sala (dx, dy dentro dela)."""
        r = self._room(rid)
        assert 0 <= dx < r["w"] and 0 <= dy < r["h"], (rid, dx, dy)
        return [r["x"] + dx, r["y"] + dy]


def monstro(tipo, pos, rid, alvo=False):
    return {"type": tipo, "pos": pos, "room_id": rid, "boss": alvo, "target": alvo}


def decor(did, tipo, pos, **extra):
    d = {"id": did, "type": tipo, "pos": pos, "facing": [0, 1], "loot": None}
    d.update(extra)
    return d


def fala(fid, pos, nome, emoji, texto, raio=3):
    return {"id": fid, "pos": pos, "falante": {"nome": nome, "emoji": emoji},
            "texto": texto, "trigger": {"tipo": "proximidade", "raio": raio}}


def masmorra(did, nome, mapa, ambiente, nivel, objetivo, entrada, saida=None, **extra):
    d = {"schema_version": 1, "id": did, "name": nome, "ambiente": ambiente,
         "saida_permitida": True, "start_mode": "entrance",
         "grid": {"w": mapa.w, "h": mapa.h}, "tiles": mapa.tiles, "rooms": mapa.rooms,
         "door_conditions": {}, "entrance": {"x": entrada[0], "y": entrada[1]},
         "exit": ({"x": saida[0], "y": saida[1]} if saida else None),
         "monsters": [], "chests": [], "traps": [], "decorations": [],
         "secret_passages": [], "master_reinforcements": [], "falas": [],
         "expected_party": {"heroes": 4, "level": nivel},
         "objectives": {"primary": objetivo, "secondary": []}}
    d.update(extra)
    if d["exit"] is None:
        del d["exit"]
    return d


# ─── 1 · Emboscada no Vau ────────────────────────────────────────────────────
def masmorra_vau():
    m = Mapa(36, 12)
    m.sala(0, 1, 2, 10, 8, role="entrance", locked=False)     # Trilha
    m.sala(1, 12, 2, 10, 8)                                   # Carroça tombada
    m.sala(2, 23, 2, 12, 8)                                   # Acampamento
    m.porta(11, 5, 0, 1)
    m.porta(22, 5, 1, 2)
    d = masmorra("sombras_1_vau", "Emboscada no Vau", m, "ar_livre", 1,
                 {"type": "rescue_prisoner", "xp": 0, "reward": {"gold": 40, "items": []}},
                 entrada=m.em(0, 0, 3), saida=m.em(2, 11, 3))
    d["monsters"] = [
        monstro("goblin_arqueiro", m.em(0, 8, 1), 0),
        monstro("goblin_arqueiro", m.em(0, 8, 6), 0),
        monstro("goblin_combatente", m.em(0, 7, 3), 0),
        monstro("goblin_combatente", m.em(1, 4, 2), 1),
        monstro("goblin_combatente", m.em(1, 4, 5), 1),
        monstro("goblin_combatente", m.em(1, 6, 3), 1),
        monstro("lobo_cinzento_customizado", m.em(1, 7, 6), 1),
        monstro("goblin_combatente", m.em(2, 3, 2), 2),
        monstro("goblin_combatente", m.em(2, 3, 5), 2),
        monstro("goblin_arqueiro", m.em(2, 8, 1), 2),
        monstro("goblin_arqueiro", m.em(2, 8, 6), 2),
        monstro("goblin_dual", m.em(2, 6, 4), 2),
    ]
    d["traps"] = [{"tipo": "armadilha_urso", "pos": m.em(0, 4, 3)}]
    d["chests"] = [{"pos": m.em(1, 8, 1), "gold": 12, "items": []}]
    d["prisoner"] = {"pos": m.em(2, 10, 1), "room_id": 2}
    d["decorations"] = [
        decor("vau_carroca", "carroca", m.em(1, 1, 5)),
        decor("vau_arvore_1", "arvore", m.em(0, 1, 0)),
        decor("vau_arvore_2", "arvore_grande", m.em(0, 2, 6)),
        decor("vau_arvore_3", "arvore_seca", m.em(1, 0, 0)),
        decor("vau_arvore_4", "arvore", m.em(2, 0, 7)),
        decor("vau_fogueira", "fogueira", m.em(2, 5, 1)),
    ]
    d["falas"] = [fala("vau_tome", m.em(2, 10, 1), "Tomé", "🧔",
                       "Aqui! Tirem-me destas cordas! A estrada para casa segue logo ali.", 4)]
    return d


# ─── 2 · Minas de Pedra-Funda ────────────────────────────────────────────────
def masmorra_minas():
    m = Mapa(42, 12)
    m.sala(0, 1, 3, 8, 6, role="entrance", locked=False)      # Boca da mina
    m.sala(1, 10, 3, 10, 6, role="trap")                      # Ponte das estacas
    m.sala(2, 21, 3, 9, 6)                                    # Galerias fundas
    m.sala(3, 31, 2, 10, 8, role="chest")                     # Depósito
    m.porta(9, 5, 0, 1)
    m.porta(20, 5, 1, 2)
    m.porta(30, 5, 2, 3)
    carta = {"id": "carta", "texto":
             "Ordem da Garra Negra: levem tudo o que brilha ao Covil. O guardião que "
             "não morre não gosta de esperar — e nunca, NUNCA, levem fogo para perto dele."}
    d = masmorra("sombras_2_minas", "Minas de Pedra-Funda", m, "masmorra", 2,
                 {"type": "open_key_chest", "xp": 0, "reward": {"gold": 60, "items": []}},
                 entrada=m.em(0, 0, 2))
    d["monsters"] = [
        monstro("kobold_lanceiro", m.em(0, 5, 1), 0),
        monstro("kobold_lanceiro", m.em(0, 5, 4), 0),
        monstro("kobold_lanceiro", m.em(0, 6, 2), 0),
        monstro("kobold_besteiro", m.em(0, 7, 0), 0),
        monstro("kobold_besteiro", m.em(0, 7, 5), 0),
        monstro("kobold_besteiro", m.em(1, 9, 0), 1),
        monstro("kobold_besteiro", m.em(1, 9, 5), 1),
        monstro("aranha_sombria", m.em(2, 3, 1), 2),
        monstro("aranha_sombria", m.em(2, 3, 4), 2),
        monstro("aranha_sombria", m.em(2, 6, 0), 2),
        monstro("aranha_sombria", m.em(2, 6, 5), 2),
        monstro("cobra_venenosa", m.em(2, 7, 2), 2),
        monstro("ogro_clava", m.em(3, 7, 3), 3),
        monstro("goblin_dual", m.em(3, 5, 1), 3),
        monstro("kobold_lanceiro", m.em(3, 5, 6), 3),
        monstro("kobold_lanceiro", m.em(3, 3, 4), 3),
    ]
    d["traps"] = [{"tipo": "fosso_estacas", "pos": m.em(1, 3, 2)},
                  {"tipo": "buraco", "pos": m.em(1, 6, 3)}]
    d["chests"] = [{"pos": m.em(3, 9, 3), "gold": 60, "key_objective": True,
                    "items": [{"id": "frasco_acido"}, {"id": "frasco_acido"},
                              {"id": "frasco_oleo"}, carta]}]
    d["falas"] = [fala("minas_kobold", m.em(1, 0, 2), "Kobold ferido", "🦎",
                       "Cuidado com as estacas... o chefe manda pisar só nas pedras escuras.", 3)]
    return d


# ─── 3a · Covil — Salões de Cima ─────────────────────────────────────────────
def masmorra_saloes():
    m = Mapa(40, 12)
    m.sala(0, 1, 3, 5, 6, role="entrance", locked=False)      # Portão
    m.sala(1, 7, 2, 9, 8, required=True, required_mode="clear")    # Guarita
    m.sala(2, 17, 2, 10, 8, required=True, required_mode="clear")  # Salão de armas
    m.sala(3, 28, 2, 10, 8, required=True, required_mode="clear")  # Escadaria
    m.porta(6, 5, 0, 1)
    m.porta(16, 5, 1, 2)
    m.porta(27, 5, 2, 3)
    d = masmorra("sombras_3a_saloes", "Covil da Garra Negra — Salões de Cima", m,
                 "masmorra", 3,
                 {"type": "salas_obrigatorias", "xp": 0, "reward": {"gold": 0, "items": []}},
                 entrada=m.em(0, 0, 2))
    d["monsters"] = [
        monstro("goblin_dual", m.em(1, 5, 2), 1),
        monstro("goblin_dual", m.em(1, 5, 5), 1),
        monstro("goblin_arqueiro", m.em(1, 8, 1), 1),
        monstro("goblin_arqueiro", m.em(1, 8, 6), 1),
        monstro("orc_guerreiro", m.em(2, 5, 2), 2),
        monstro("orc_guerreiro", m.em(2, 5, 5), 2),
        monstro("goblin_combatente", m.em(2, 7, 1), 2),
        monstro("goblin_combatente", m.em(2, 7, 6), 2),
        monstro("orc_guerreiro", m.em(3, 5, 3), 3),
        monstro("dark_mage", m.em(3, 8, 4), 3),
        monstro("goblin_dual", m.em(3, 4, 1), 3),
        monstro("goblin_dual", m.em(3, 4, 6), 3),
    ]
    return d


# ─── 3b · Covil — O Trono de Pedra ───────────────────────────────────────────
def masmorra_trono():
    m = Mapa(24, 18)
    m.sala(0, 1, 1, 8, 8, role="entrance", locked=False)      # Poço antigo
    m.sala(1, 10, 1, 13, 10, role="boss")                     # Trono
    m.sala(2, 1, 10, 8, 6, locked=False)                      # Esconderijo (secreto)
    m.porta(9, 4, 0, 1)
    passagem = [4, 9]                  # parede entre o Poço (y ≤ 8) e o Esconderijo (y ≥ 10)
    d = masmorra("sombras_3b_trono", "Covil da Garra Negra — O Trono de Pedra", m,
                 "masmorra", 3,
                 {"type": "kill_target", "xp": 0, "reward": {"gold": 120, "items": []}},
                 entrada=m.em(0, 1, 1))
    d["monsters"] = [
        monstro("troll", m.em(1, 9, 4), 1, alvo=True),
        monstro("orc_guerreiro", m.em(1, 7, 2), 1),
        monstro("goblin_arqueiro", m.em(1, 11, 1), 1),
        monstro("goblin_arqueiro", m.em(1, 11, 8), 1),
        monstro("bugbear_sombras", m.em(2, 4, 4), 2),
        monstro("aranha_sombria", m.em(2, 1, 3), 2),
        monstro("aranha_sombria", m.em(2, 6, 3), 2),
    ]
    d["decorations"] = [
        decor("trono_fonte", "fonte", m.em(0, 5, 1), charges=3),
        decor("trono_estante", "estante_livros", m.em(0, 5, 6)),
        decor("trono_braseiro_1", "fogueira", m.em(1, 6, 1)),
        decor("trono_braseiro_2", "fogueira", m.em(1, 6, 8)),
    ]
    d["secret_passages"] = [{"id": "trono_passagem", "type": "mechanism", "pos": passagem,
                             "key_decor_ids": ["trono_estante"], "keys_mode": "any"}]
    d["chests"] = [{"pos": m.em(2, 6, 1), "gold": 30, "items": [{"id": ANEL_ID}]}]
    d["falas"] = [fala("trono_pista", m.em(0, 3, 5), "Vento", "🌬️",
                       "O vento assobia atrás da estante… como se houvesse um corredor do outro lado.", 2)]
    return d


def masmorras():
    return {"sombras_1_vau.json": masmorra_vau(), "sombras_2_minas.json": masmorra_minas(),
            "sombras_3a_saloes.json": masmorra_saloes(), "sombras_3b_trono.json": masmorra_trono()}


# ─── História ────────────────────────────────────────────────────────────────
# Cada slide só leva texto; a arte que ele pede fica em ARTES_PEDIDAS, que o
# --simular imprime (o autor sobe as imagens pelo editor depois).
ARTES_PEDIDAS = []


def historia(chave, slides, audio=None):
    out = []
    for i, (texto, arte) in enumerate(slides):
        ARTES_PEDIDAS.append((f"{chave}#{i + 1}", arte))
        out.append({"text": texto, "fit": "contain"})
    h = {"slides": out}
    if audio:
        h["audio"] = audio
    return h


def _etapa(arquivo, intro, outro, encadear=False):
    return {"file": arquivo, "encadear": encadear, "intro": intro, "outro": outro}


def destinos():
    ARTES_PEDIDAS.clear()
    base_x, base_y = S.WORLD_LOCATIONS["alva_e_luz"]["x"], S.WORLD_LOCATIONS["alva_e_luz"]["y"]

    def perto(dx, dy):
        return round(max(0, min(100, base_x + dx)), 2), round(max(0, min(100, base_y + dy)), 2)

    vau_intro = historia("vau.intro", [
        ("A Estrada do Vau atravessa o bosque a leste de Alva e Luz. Há três luas nenhuma "
         "caravana chega do outro lado.", "estrada de floresta ao entardecer, marcas de rodas na lama"),
        ("Na curva do rio, uma carroça tombada. Cordas cortadas. E, entre as árvores, o "
         "brilho de olhos pequenos e amarelos.", "carroça tombada, goblins espreitando no mato"),
    ], MUSICA_ABERTURA)
    vau_outro = historia("vau.outro", [
        ("— Não era só roubo — diz Tomé, esfregando os pulsos. — Eles levavam a carga para "
         "as velhas minas de Pedra-Funda. Falavam de uma garra negra.",
         "Tomé ferido junto à fogueira do acampamento"),
    ])
    minas_intro = historia("minas.intro", [
        ("As minas de Pedra-Funda foram abandonadas quando a veia de prata secou. Agora, "
         "dizem os mineiros, a montanha voltou a ranger à noite.",
         "entrada de mina escorada, trilhos enferrujados"),
        ("Pegadas miúdas e rastros de carga arrastada descem para o escuro.",
         "túnel com pegadas de kobold iluminado por tocha"),
    ], MUSICA_ABERTURA)
    minas_outro = historia("minas.outro", [
        ("No cofre, frascos que os kobolds nunca entenderam — ácido e óleo — e um bilhete "
         "com o sinal de uma garra negra: o Covil, e um guardião que não morre.",
         "cofre aberto com frascos e um bilhete marcado por uma garra"),
    ])
    covil_intro = historia("covil.intro", [
        ("O Covil da Garra Negra fica numa fortaleza em ruínas, na encosta sobre as minas.",
         "fortaleza em ruínas na encosta, fumaça saindo das seteiras"),
        ("Daqui não há volta até o fim: os andares se emendam, e o que for gasto lá dentro "
         "não se recupera.", "portão de pedra entreaberto, escuro lá dentro"),
    ], MUSICA_ABERTURA)
    saloes_outro = historia("covil.transicao", [
        ("A escadaria desce para o calor. Cheiro de fumaça e de carne podre. Algo enorme "
         "respira lá embaixo.", "escada de pedra descendo para um salão iluminado por braseiros"),
    ])
    trono_intro = historia("trono.intro", [
        ("No Trono de Pedra, entre braseiros, o guardião se levanta: um troll. As feridas "
         "que os heróis abrem se fecham diante dos olhos.",
         "troll enorme de pé diante de um trono de pedra, braseiros acesos"),
        ("Ácido e fogo. É o que diz o bilhete. É o que sobrou do cofre.",
         "mão segurando um frasco de ácido"),
    ], MUSICA_TROLL)
    trono_outro = historia("trono.outro", [
        ("O troll tomba de vez. O bando da Garra Negra se desfaz na noite.",
         "troll caído entre braseiros apagados"),
    ])
    fim_rota = historia("covil.fim", [
        ("Semanas depois, as caravanas voltam a cruzar o Vau. Em Alva e Luz, o nome do "
         "grupo corre de mesa em mesa na taverna.", "praça de Alva e Luz em festa, caravana chegando"),
        ("E, em algum lugar sob a fortaleza, uma estante esconde um segredo que talvez "
         "ninguém tenha encontrado.", "estante de livros na penumbra, uma fresta de escuridão atrás"),
    ])

    def destino(did, nome, dx, dy, custo, etapas, requisito, renome, outro_rota=""):
        x, y = perto(dx, dy)
        return {"id": did, "nome": nome, "x": x, "y": y, "fome": custo, "sede": custo,
                "dungeons": etapas, "espera_retorno": {"modo": "fixa", "rodadas": 0, "dados": ""},
                "oculto_ate_liberar": True, "revisitavel": False, "outro_rota": outro_rota,
                "requisito": S._clean_requirement(requisito), "renome_recompensa": renome}

    return {
        "sombras_vau": destino("sombras_vau", "Emboscada no Vau", 6, 3, 1,
                               [_etapa("sombras_1_vau.json", vau_intro, vau_outro)],
                               {"fato": FATO_GANCHO}, 1),
        "sombras_minas": destino("sombras_minas", "Minas de Pedra-Funda", 11, -4, 2,
                                 [_etapa("sombras_2_minas.json", minas_intro, minas_outro)],
                                 {"aventura_id": "sombras_vau"}, 1),
        "sombras_covil": destino("sombras_covil", "Covil da Garra Negra", 16, -9, 3,
                                 [_etapa("sombras_3a_saloes.json", covil_intro, saloes_outro, encadear=True),
                                  _etapa("sombras_3b_trono.json", trono_intro, trono_outro)],
                                 {"aventura_id": "sombras_minas"}, 2, outro_rota=fim_rota),
    }


# ─── Anel e conversa ─────────────────────────────────────────────────────────
def anel_bruto():
    return {"id": ANEL_ID, "name": "Anel da Garra Negra", "emoji": "💍", "item_type": "ring",
            "bonuses": [{"effect": "atk_bonus", "value": 1}, {"effect": "vision", "value": 1}],
            "granted_ability": "hero_rogue_esconder_sombras",
            "allowed_classes": [], "price": 250,
            "disponibilidade": {"loja": False, "baus": True, "loot_monstro": False}}


def conversa_bartender():
    return {"id": CONVERSA_ID,
            "texto": ("As caravanas que saem pela Estrada do Vau não chegam do outro lado. "
                      "O último cocheiro, Tomé, sumiu com a carga há três luas. Se vocês "
                      "forem para os lados do Vau... tomem cuidado com o mato."),
            "requisito": {}, "efeito": {"fato": FATO_GANCHO}, "uma_vez": True}


# ─── Medidas (compartilhadas com --simular e com os testes) ─────────────────
def nd_por_sala(defn):
    """ND por sala = monster_cr dos monstros + trap_cr das armadilhas dentro dela."""
    defs = {m["type"]: m for m in S.MONSTER_DEFS}
    nd = {r["id"]: 0.0 for r in defn["rooms"]}
    for mo in defn.get("monsters", []):
        nd[mo["room_id"]] += S.monster_cr(defs[mo["type"]])
    for t in defn.get("traps", []):
        for r in defn["rooms"]:
            if r["x"] <= t["pos"][0] < r["x"] + r["w"] and r["y"] <= t["pos"][1] < r["y"] + r["h"]:
                nd[r["id"]] += S.trap_cr(S.ARMADILHAS[t["tipo"]])
    return {rid: round(v, 3) for rid, v in nd.items()}


def faixa(nd, poder):
    """Mesmas faixas de src/difficulty.js (razão ND ÷ poder)."""
    razao = nd / max(1, poder)
    for chave, teto in (("facil", 0.4), ("equilibrada", 0.8), ("dificil", 1.2)):
        if razao < teto:
            return chave
    return "mortal"


def salas_alcancaveis(defn, passagens_abertas=False):
    """Ids das salas alcançáveis a pé a partir da entrada (FLOOR/DOOR ortogonal)."""
    tiles = [row[:] for row in defn["tiles"]]
    if passagens_abertas:
        for sp in defn.get("secret_passages", []):
            tiles[sp["pos"][1]][sp["pos"][0]] = FLOOR
    ini = (defn["entrance"]["x"], defn["entrance"]["y"])
    vistos, fila = {ini}, [ini]
    while fila:
        x, y = fila.pop()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (0 <= ny < len(tiles) and 0 <= nx < len(tiles[0])
                    and tiles[ny][nx] in (FLOOR, DOOR) and (nx, ny) not in vistos):
                vistos.add((nx, ny))
                fila.append((nx, ny))
    return {r["id"] for r in defn["rooms"]
            if any((x, y) in vistos for x in range(r["x"], r["x"] + r["w"])
                   for y in range(r["y"], r["y"] + r["h"]))}


# ─── Montagem ────────────────────────────────────────────────────────────────
def preparar():
    """Monta e valida TUDO em memória. Levanta ValueError na primeira invalidez."""
    ok, anel = S._validate_custom_item(anel_bruto())
    if not ok:
        raise ValueError(f"anel inválido: {anel}")
    outros = [r for r in S._read_custom_items() if isinstance(r, dict) and r.get("id") != ANEL_ID]
    S._apply_custom_items(outros + [anel])      # o baú do Trono precisa achar o anel
    mm = masmorras()
    for arquivo, defn in mm.items():
        ok, msg = S.validar_dungeon(defn)
        if not ok:
            raise ValueError(f"{arquivo}: {msg}")
    return {"masmorras": mm, "destinos": destinos(), "anel": anel,
            "conversa": S._clean_scene_conversations([conversa_bartender()], "")[0]}
