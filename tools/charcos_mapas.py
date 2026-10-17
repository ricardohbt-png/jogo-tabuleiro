"""Mapas da campanha "A Maré do Charco" (usados por `gerar_campanha_charcos.py`).

Tudo é determinístico (semente fixa por mapa): rodar o gerador de novo produz os mesmos arquivos.
Calibração de nível, XP e dificuldade: ver o cabeçalho do gerador.
"""
import os
import random
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (RAIZ, os.path.join(RAIZ, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import server as S  # noqa: E402
from gerar_campanha_sombras import Mapa, monstro, decor, fala, masmorra  # noqa: E402

WALL, FLOOR, DOOR = S.WALL, S.FLOOR, S.DOOR
FATO_MORTE = "charcos_criancas_mortas"
FATO_FERRAO = "charcos_ferrao_morto"
ITEM_TROFEU = "ferrao_do_brejo"
FERRAO = "ferrao_charcos_adulto"

_TAM = {d["type"]: tuple(d.get("size") or (1, 1)) for d in S.MONSTER_DEFS}


class Cena:
    """Mapa + o que está sobre ele (monstros, decoração, baús, materiais)."""

    def __init__(self, prefixo, mapa, semente, piso="grama", parede="rocha_marrom"):
        self.p, self.m, self.rng = prefixo, mapa, random.Random(semente)
        self.piso, self.parede = piso, parede
        self.monstros, self.decs, self.baus, self.armadilhas, self.falas = [], [], [], [], []
        self.oc = set()
        self.mat = {}
        self.proibidas = set()      # casas que decoração sólida não ocupa (portas, entradas…)
        self._n = 0

    # materiais -------------------------------------------------------------
    def pintar(self, rid, material, dx=0, dy=0, w=None, h=None):
        r = self.m._room(rid)
        w = r["w"] - dx if w is None else w
        h = r["h"] - dy if h is None else h
        for y in range(r["y"] + dy, r["y"] + dy + h):
            for x in range(r["x"] + dx, r["x"] + dx + w):
                if self.m.tiles[y][x] != WALL:
                    self.mat[f"{x},{y}"] = material

    def pintar_abs(self, x, y, w, h, material):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                if self.m.tiles[yy][xx] != WALL:
                    self.mat[f"{xx},{yy}"] = material

    # ocupação --------------------------------------------------------------
    @staticmethod
    def _tiles(pos, tam):
        return [(pos[0] + i, pos[1] + j) for i in range(tam[0]) for j in range(tam[1])]

    def _ocupar(self, pos, tam, nome):
        for t in self._tiles(pos, tam):
            assert self.m.tiles[t[1]][t[0]] == FLOOR, (nome, pos, t, "não é chão")
            assert t not in self.oc, (nome, pos, t, "casa já ocupada")
            self.oc.add(t)

    def mon(self, tipo, rid, dx, dy, alvo=False, **extra):
        pos = self.m.em(rid, dx, dy)
        self._ocupar(pos, _TAM[tipo], tipo)
        mo = monstro(tipo, pos, rid, alvo)
        mo.update(extra)
        self.monstros.append(mo)
        return mo

    def mon_livre(self, tipo, rid, n=1, **extra):
        out = []
        for _ in range(n):
            pos = self._sorteia(rid, _TAM[tipo], margem=1)
            self._ocupar(pos, _TAM[tipo], tipo)
            mo = monstro(tipo, pos, rid, False)
            mo.update(extra)
            self.monstros.append(mo)
            out.append(mo)
        return out

    def deco(self, tipo, rid, dx, dy, did=None, **extra):
        pos = self.m.em(rid, dx, dy)
        tam = tuple(S.DECOR_TYPES[tipo].get("size") or (1, 1))
        self._ocupar(pos, tam, tipo)
        self._n += 1
        d = decor(did or f"{self.p}_{tipo}_{self._n}", tipo, pos, **extra)
        self.decs.append(d)
        return d

    def _sorteia(self, rid, tam, margem=0, borda=False):
        r = self.m._room(rid)
        cand = []
        for y in range(r["y"] + margem, r["y"] + r["h"] - margem - tam[1] + 1):
            for x in range(r["x"] + margem, r["x"] + r["w"] - margem - tam[0] + 1):
                ts = self._tiles((x, y), tam)
                if any(self.m.tiles[t[1]][t[0]] != FLOOR or t in self.oc or t in self.proibidas for t in ts):
                    continue
                if borda and not any(t[0] in (r["x"], r["x"] + r["w"] - 1)
                                     or t[1] in (r["y"], r["y"] + r["h"] - 1) for t in ts):
                    continue
                cand.append((x, y))
        assert cand, (rid, "sem casa livre")
        return list(self.rng.choice(cand))

    def espalha(self, tipo, rid, n):
        """Decoração em casas sorteadas; sólida fica na borda da sala (não fecha caminho)."""
        meta = S.DECOR_TYPES[tipo]
        tam = tuple(meta.get("size") or (1, 1))
        for _ in range(n):
            pos = self._sorteia(rid, tam, borda=not meta.get("pisavel"))
            self._ocupar(pos, tam, tipo)
            self._n += 1
            self.decs.append(decor(f"{self.p}_{tipo}_{self._n}", tipo, pos))

    def proteger(self, *casas, raio=1):
        for (x, y) in casas:
            for dx in range(-raio, raio + 1):
                for dy in range(-raio, raio + 1):
                    self.proibidas.add((x + dx, y + dy))

    def bau(self, pos, ouro=0, itens=()):
        self._ocupar(pos, (1, 1), "bau")
        self.baus.append({"pos": pos, "gold": ouro, "items": [dict(i) for i in itens], "key_objective": False})

    def fala(self, fid, pos, nome, emoji, texto, raio=3):
        self.falas.append(fala(fid, pos, nome, emoji, texto, raio))

    def finalizar(self, did, nome, ambiente, nivel, objetivos, entrada, saida=None, **extra):
        m = self.m
        mats = {}
        for y in range(m.h):
            for x in range(m.w):
                k = f"{x},{y}"
                mats[k] = self.mat.get(k) or (self.parede if m.tiles[y][x] == WALL else self.piso)
        d = masmorra(did, nome, m, ambiente, nivel, objetivos["primary"], entrada, saida, **extra)
        d["objectives"] = objetivos
        d["monsters"], d["decorations"], d["chests"] = self.monstros, self.decs, self.baus
        d["traps"], d["falas"], d["materiais"] = self.armadilhas, self.falas, mats
        return d


def obj(tipo, xp, ouro, itens=(), **extra):
    o = {"type": tipo, "xp": xp, "reward": {"gold": ouro, "items": [{"id": i} for i in itens]}}
    o.update(extra)
    return o


def mapa_em_fila(larguras, altura, y0=2, folga=1):
    """Salas lado a lado separadas por uma parede. Devolve (Mapa, [(x, w)], y0, altura_da_sala)."""
    hs = altura - y0 - 2
    total = folga + sum(larguras) + (len(larguras) - 1) + folga
    m = Mapa(total, altura)
    xs, x = [], folga
    for w in larguras:
        xs.append((x, w))
        x += w + 1
    return m, xs, y0, hs


def montar_fila(larguras, altura, prefixo, semente, **kw):
    """Fila de salas 0..n-1 com portas no meio de cada parede; devolve (Cena, xs, hs)."""
    m, xs, y0, hs = mapa_em_fila(larguras, altura)
    for i, (x, w) in enumerate(xs):
        m.sala(i, x, y0, w, hs, role="entrance" if i == 0 else "monster", locked=(i != 0))
    ymeio = y0 + hs // 2
    for i in range(len(xs) - 1):
        m.porta(xs[i][0] + xs[i][1], ymeio, i, i + 1)
    c = Cena(prefixo, m, semente, **kw)
    for i in range(len(xs) - 1):
        px = xs[i][0] + xs[i][1]
        c.proteger((px, ymeio), (px - 1, ymeio), (px + 1, ymeio))
    return c, xs, hs


# ─── 1 · Bordas da Mata ──────────────────────────────────────────────────────
def masmorra_bordas():
    c, xs, hs = montar_fila([11, 12, 11, 9], 16, "bordas", 1101)
    m = c.m
    ent, sai = m.em(0, 1, hs // 2), m.em(3, 8, hs // 2)
    c.proteger(ent, sai)
    # 0 · Trilha de lama
    c.mon("escorpiao_pequeno", 0, 8, 2)
    c.mon("aranha_sombria", 0, 7, 7)
    c.mon_livre("rato", 0, 4)
    c.mon_livre("rato_gigante", 0, 3)
    c.espalha("arvore", 0, 5); c.espalha("moita_espinhosa", 0, 4); c.espalha("capim_alto", 0, 7)
    c.espalha("tronco_musgo", 0, 1)
    c.deco("monte_ossos", 0, 5, 4)
    # 1 · Clareira dos lobos
    c.mon("lobo_cinzento_customizado", 1, 9, 4, alvo=True)
    c.mon("lobo_cinzento", 1, 7, 2); c.mon("lobo_cinzento", 1, 7, 6); c.mon("lobo_cinzento", 1, 5, 4)
    c.mon_livre("rato_gigante", 1, 2)
    c.espalha("arvore", 1, 5); c.espalha("arvore_grande", 1, 1); c.espalha("capim_alto", 1, 6)
    c.deco("monte_ossos", 1, 4, 2); c.deco("ossos_semi_enterrados", 1, 3, 6)
    # 2 · Bosque das aranhas
    c.mon_livre("aranha_sombria", 2, 3)
    c.mon_livre("escorpiao_pedra", 2, 2)
    c.mon_livre("escorpiao_de_pedra_customizado", 2, 1)
    c.mon_livre("cobra_venenosa", 2, 1)
    c.espalha("arvore", 2, 6); c.espalha("arvore_seca", 2, 2); c.espalha("moita_espinhosa", 2, 4)
    c.espalha("tronco_podre_fungos", 2, 1)
    c.deco("ossos_semi_enterrados", 2, 5, 3)
    # 3 · Ponte quebrada (saída)
    c.mon_livre("cobra_venenosa", 3, 1)
    c.mon_livre("rato_gigante", 3, 2)
    c.mon_livre("aranha_sombria", 3, 1)
    c.espalha("arvore", 3, 3); c.espalha("capim_alto", 3, 4)
    c.deco("monte_ossos", 3, 3, 3)
    c.deco("lapide", 3, 5, 6, did="bordas_sinal")
    c.bau(m.em(3, 6, 2), 12, [{"id": "carta", "texto": (
        "Um sapatinho de criança, enlameado, caído junto aos ossos. As marcas de arrasto "
        "seguem para a ponte quebrada e dali para as palafitas, rio abaixo.")}])
    c.fala("bordas_rastro", m.em(0, 3, hs // 2), "Rastreador", "👣",
           "Pegadas pequenas na lama… e outras, maiores, arrastando algo. Fiquem juntos.", 4)
    c.fala("bordas_ossos", m.em(3, 3, hs // 2), "Rastreador", "🦴",
           "Ossos roídos, mas nenhum corpo inteiro. O rastro atravessa a ponte quebrada.", 4)
    return c.finalizar("charcos_1_bordas", "Bordas da Mata", "ar_livre", 2,
                       {"primary": obj("all_heroes_at_exit", 250, 30),
                        "secondary": [obj("kill_target", 150, 25, ["health_potion_small"])]}, ent, sai)


# ─── 2 · Palafitas dos Pescadores ────────────────────────────────────────────
def masmorra_palafitas():
    c, xs, hs = montar_fila([10, 15, 11, 12], 20, "palafitas", 2202)
    m = c.m
    ent, sai = m.em(0, 1, hs // 2), m.em(3, 10, hs // 2)
    c.proteger(ent, sai)
    for rid in range(4):
        c.pintar(rid, "madeira_escura" if rid in (2, 3) else "grama")
    # Margem de entrada
    c.pintar(0, "agua", dx=6, dy=0, w=4)
    c.mon_livre("escorpiao_pedra", 0, 2); c.mon_livre("rato_gigante", 0, 3)
    c.mon_livre("cobra_venenosa", 0, 1)
    c.espalha("arvore", 0, 3); c.espalha("juncos", 0, 5); c.espalha("tocos_alagados", 0, 2)
    c.deco("monte_ossos", 0, 3, 4)
    # 1 · Passarelas: canal fundo com uma ponte de tábuas podres
    r1 = m._room(1)
    c.pintar(1, "agua")
    c.pintar(1, "madeira_escura", dx=0, dy=hs // 2 - 1, w=r1["w"], h=3)       # passarela principal
    xcan = r1["x"] + 6
    c.pintar_abs(xcan, r1["y"], 3, r1["h"], "agua_profunda")             # canal
    ymeio = r1["y"] + hs // 2
    c.mat[f"{xcan - 1},{ymeio}"] = "madeira_escura"
    c.mat[f"{xcan + 3},{ymeio}"] = "madeira_escura"
    c.armadilhas.append({"id": "palafitas_tabua", "tipo": "chao_illusorio",
                         "pos": [xcan + 1, ymeio], "ponte_id": "ponte_0"})
    c.proteger((xcan, ymeio), (xcan + 1, ymeio), (xcan + 2, ymeio), (xcan - 1, ymeio), (xcan + 3, ymeio))
    c.mon("jacare", 1, 1, 1, alvo=True)
    c.mon("crocodilo_jovem", 1, 11, 12)
    c.mon("cobra_constritora", 1, 3, 9)
    c.mon("devorador_organico", 1, 12, 3)
    c.espalha("juncos", 1, 6); c.espalha("tocos_alagados", 1, 4)
    c.deco("monte_ossos", 1, 2, 12); c.deco("monte_ossos", 1, 13, 9)
    # 2 · Depósito dos pescadores
    c.mon("devorador_organico", 2, 8, 2); c.mon("cobra_constritora", 2, 3, 2)
    c.mon_livre("escorpiao_pedra", 2, 2); c.mon_livre("rato_gigante", 2, 2)
    c.deco("cabana_rustica", 2, 1, 6, did="palafitas_cabana")
    c.espalha("barril", 2, 3); c.espalha("juncos", 2, 2)
    c.bau(m.em(2, 9, 8), 25, [{"id": "frasco_oleo"}, {"id": "frasco_oleo"},
                              {"id": "frasco_piche"}, {"id": "frasco_piche"},
                              {"id": "carta", "texto": (
                                  "Homens de capuz, de noite, e um bicho que não passa perto do fogo. "
                                  "Levei óleo e piche para o depósito, caso precisem. Quem ler isto: "
                                  "sigam o rastro para o pântano, mas não deixem a fera livre.")}])
    # 3 · Doca final
    c.pintar(3, "agua", dx=0, dy=0, w=4)
    c.mon("crocodilo_jovem", 3, 1, 1); c.mon("crocodilo_jovem", 3, 1, 10)
    c.mon_livre("cobra_venenosa", 3, 2); c.mon_livre("escorpiao_pequeno", 3, 2)
    c.espalha("juncos", 3, 4); c.espalha("monte_ossos", 3, 2)
    c.fala("palafitas_deposito", m.em(2, 3, hs // 2), "Narrador", "📜",
           "Uma carta pregada na parede e prateleiras com frascos: óleo e piche. A criatura teme o fogo.", 4)
    d = c.finalizar("charcos_2_palafitas", "Palafitas dos Pescadores", "ar_livre", 3,
                    {"primary": obj("all_heroes_at_exit", 300, 40),
                     "secondary": [obj("kill_target", 250, 40, ["antidote"])]}, ent, sai)
    # A ponte: margens a 1 nível, tábuas sobre o canal a 0; o Chão Ilusório cede no meio.
    ini, fim = [xcan - 1, ymeio], [xcan + 3, ymeio]
    d["elevacoes"] = {f"{ini[0]},{ini[1]}": 1, f"{fim[0]},{fim[1]}": 1}
    d["pontes"] = [{"id": "ponte_0", "inicio": ini, "fim": fim, "largura": 1, "altura": 1, "material": "madeira"}]
    return d


# ─── 3 · Travessia do Pântano ────────────────────────────────────────────────
def masmorra_travessia():
    c, xs, hs = montar_fila([10, 14, 14, 12], 20, "travessia", 3303, piso="pantano")
    m = c.m
    ent, sai = m.em(0, 1, hs // 2), m.em(3, 10, hs // 2)
    c.proteger(ent, sai)
    c.pintar(0, "grama")
    c.mon_livre("escorpiao_pedra", 0, 2); c.mon_livre("rato_gigante", 0, 4); c.mon_livre("cobra_venenosa", 0, 1)
    c.mon_livre("cobra_constritora", 0, 1)
    c.espalha("arvore", 0, 3); c.espalha("juncos", 0, 4)
    # 1 · Charco aberto (pântano + poças)
    for (dx, dy, w, h) in ((2, 2, 4, 3), (8, 9, 4, 3)):
        c.pintar(1, "agua", dx=dx, dy=dy, w=w, h=h)
    c.mon("crocodilo_jovem", 1, 3, 2); c.mon("crocodilo_jovem", 1, 9, 10)
    c.mon_livre("cobra_constritora", 1, 1); c.mon_livre("rato_gigante", 1, 2)
    c.mon_livre("cobra_venenosa", 1, 1)
    c.espalha("juncos", 1, 5); c.espalha("tocos_alagados", 1, 3); c.espalha("raizes_torcidas", 1, 2)
    # 2 · Ilhotas (grama) entre água funda
    c.pintar(2, "agua")
    for (dx, dy, w, h) in ((1, 1, 5, 4), (7, 3, 5, 5), (2, 9, 5, 4), (8, 10, 5, 4)):
        c.pintar(2, "grama", dx=dx, dy=dy, w=w, h=h)
    c.pintar(2, "pantano", dx=0, dy=hs // 2 - 1, w=14, h=3)             # a trilha de pântano que liga as ilhotas
    c.mon("crocodilo_jovem", 2, 8, 10)
    c.mon_livre("cobra_venenosa", 2, 2); c.mon_livre("escorpiao_pedra", 2, 2); c.mon_livre("rato_gigante", 2, 2)
    c.mon_livre("cobra_constritora", 2, 1)
    c.espalha("juncos", 2, 4); c.espalha("tocos_alagados", 2, 3)
    # 3 · Aproximação da aldeia: zumbis (primeiro sinal dos necromantes)
    c.pintar(3, "grama", dx=7, dy=0, w=5)
    c.mon_livre("zumbi_infectado", 3, 2); c.mon_livre("cobra_constritora", 3, 1)
    c.mon_livre("escorpiao_de_pedra_customizado", 3, 1); c.mon_livre("escorpiao_pedra", 3, 2)
    c.espalha("arvore_seca", 3, 3); c.espalha("monte_ossos", 3, 3); c.espalha("lapide", 3, 2)
    c.fala("travessia_aldeia", m.em(3, 9, hs // 2), "Narrador", "🔥",
           "Fumaça e cantos baixos. Do alto da ilhota, uma paliçada: a aldeia dos bruxos.", 4)
    return c.finalizar("charcos_3_travessia", "Travessia do Pântano", "ar_livre", 3,
                       {"primary": obj("all_heroes_at_exit", 350, 50), "secondary": []}, ent, sai)


# ─── 4A · Arredores da Aldeia ────────────────────────────────────────────────
def masmorra_arredores():
    c, xs, hs = montar_fila([10, 12, 12, 8], 20, "arredores", 4404, piso="terra", parede="parede_terra")
    m = c.m
    ent, sai = m.em(0, 1, hs // 2), m.em(3, 6, hs // 2)
    c.proteger(ent, sai)
    c.pintar(1, "madeira_escura"); c.pintar(2, "madeira_escura"); c.pintar(3, "madeira_escura")
    # 0 · Trilha
    c.mon_livre("esqueleto_animal", 0, 2); c.mon_livre("rato_gigante", 0, 2); c.mon_livre("esqueleto_humano", 0, 1)
    c.espalha("arvore_seca", 0, 3); c.espalha("monte_ossos", 0, 2)
    # 1 · Vigias de osso
    c.mon_livre("esqueleto_humano", 1, 4); c.mon_livre("esqueleto_animal", 1, 2)
    c.mon_livre("zumbi_infectado", 1, 1); c.mon_livre("goblin_combatente", 1, 2)
    c.espalha("cerca_reta", 1, 5); c.espalha("lapide", 1, 3); c.espalha("monte_ossos", 1, 2)
    # 2 · Pátio externo
    c.mon_livre("goblin_xama", 2, 1); c.mon_livre("esqueleto_humano", 2, 2)
    c.mon_livre("zumbi_infectado", 2, 2); c.mon_livre("goblin_combatente", 2, 2); c.mon_livre("esqueleto_animal", 2, 2)
    c.espalha("cerca_reta", 2, 5); c.espalha("caldeirao", 2, 1); c.espalha("tumba", 2, 2)
    # 3 · Portão
    c.mon_livre("goblin_combatente", 3, 2); c.mon_livre("esqueleto_humano", 3, 2); c.mon_livre("zumbi_infectado", 3, 1)
    c.espalha("cerca_reta", 3, 4); c.deco("porteira_fechada", 3, 7, hs // 2 - 1)
    c.deco("porteira_fechada", 3, 7, hs // 2 + 1)
    c.fala("arredores_vigias", m.em(0, 5, hs // 2), "Narrador", "💀",
           "Vigias de osso andam pelas tábuas. Os bruxos não deixam os mortos descansar.", 4)
    return c.finalizar("charcos_4a_arredores", "Arredores da Aldeia", "ar_livre", 3,
                       {"primary": obj("all_heroes_at_exit", 400, 50), "secondary": []}, ent, sai)


# ─── 4B · A Aldeia (praça, cercado e a cova do Ferrão) ───────────────────────
def masmorra_aldeia():
    m = Mapa(56, 36)
    m.sala(0, 1, 12, 9, 12, role="entrance", locked=False)             # portão
    m.sala(1, 11, 2, 30, 32)                                           # praça
    m.sala(2, 42, 12, 11, 12)                                          # cercado
    m.porta(10, 18, 0, 1)
    m.porta(41, 18, 1, 2)
    c = Cena("aldeia", m, 5505, piso="terra", parede="parede_terra")
    ent, sai = m.em(0, 1, 6), m.em(0, 7, 6)
    c.proteger(ent, sai, (10, 18), (41, 18), (9, 18), (11, 18), (40, 18), (42, 18))
    c.pintar(2, "madeira_escura")

    # A cova do Ferrão: um quarto murado DENTRO da praça (mesma sala: a hostilidade entre monstros só vale aí).
    cx0, cy0 = 28, 20                                                  # canto da parede da cova (absoluto)
    for yy in range(cy0, cy0 + 7):
        for xx in range(cx0, cx0 + 7):
            borda = xx in (cx0, cx0 + 6) or yy in (cy0, cy0 + 6)
            m.tiles[yy][xx] = WALL if borda else FLOOR
    for yy in range(cy0 + 1, cy0 + 6):
        for xx in range(cx0 + 1, cx0 + 6):
            c.mat[f"{xx},{yy}"] = "terra"
    passagens = [(cx0, cy0 + 2), (cx0, cy0 + 3), (cx0, cy0 + 4)]      # parede oeste da cova, quebrada pela corrente
    c.proteger(*[(cx0 + i, cy0 + j) for i in range(-1, 8) for j in range(-1, 8)], raio=0)
    ferrao = c.mon(FERRAO, 1, cx0 + 3 - 11, cy0 + 3 - 2, alvo=True,
                   hostility_override={"mode": "custom", "rules": {"all_monsters": True, "subtypes": [], "types": []}})
    # O mecanismo: uma corrente de ferro à esquerda da parede abre a passagem.
    corrente = c.deco("bola_corrente", 1, cx0 - 3 - 11, cy0 + 3 - 2, did="aldeia_corrente", key_objective=True)
    # Piche e feno perto da cova (fogo + piche: o grupo ferre o Ferrão de longe)
    c.pintar_abs(cx0 - 4, cy0 - 1, 3, 3, "piche")
    c.pintar_abs(cx0 + 8, cy0 + 4, 3, 3, "piche")
    c.pintar_abs(cx0 + 2, cy0 + 8, 5, 2, "piche")
    c.deco("barril", 1, cx0 - 4 - 11, cy0 - 3 - 2); c.deco("barril", 1, cx0 + 9 - 11, cy0 - 2 - 2)
    c.deco("monte_feno", 1, cx0 - 2 - 11, cy0 + 6 - 2)
    c.mon_livre("goblin_combatente", 0, 2); c.mon_livre("esqueleto_animal", 0, 2)
    c.espalha("cerca_reta", 0, 3); c.espalha("monte_ossos", 0, 2)
    # Bruxos da praça — revidam SÓ contra o Ferrão (os heróis seguem sendo alvo normal)
    so_ferrao = {"mode": "custom", "rules": {"all_monsters": False, "subtypes": [], "types": [FERRAO]}}
    # Os bruxos ficam do lado da passagem da cova (a oeste): com a parede aberta há linha de visão até o Ferrão.
    c.mon("goblin_xama", 1, 15, 19, hostility_override=so_ferrao)
    c.mon("goblin_xama", 1, 15, 23, hostility_override=so_ferrao)
    chefe = c.mon("necromante", 1, 33 - 11, 10 - 2, hostility_override=so_ferrao)
    c.mon("necromante", 1, 16, 21, hostility_override=so_ferrao)
    c.mon_livre("goblin_combatente", 1, 3)
    c.mon_livre("esqueleto_humano", 1, 2); c.mon_livre("esqueleto_animal", 1, 2)
    c.mon_livre("zumbi_infectado", 1, 2)
    sino = c.deco("sino_ritualistico", 1, 34 - 11, 9 - 2, did="aldeia_sino", key_objective=True)
    c.espalha("caldeirao", 1, 2); c.espalha("monte_ossos", 1, 4); c.espalha("cerca_reta", 1, 6)
    c.espalha("lapide", 1, 2); c.espalha("pira_chamas", 1, 2)
    # Cercado das crianças
    c.espalha("grades_prisao", 2, 3); c.espalha("monte_feno", 2, 2)
    prisioneiro = m.em(2, 5, 6)
    c.proteger(prisioneiro)
    c.fala("aldeia_corrente", m.em(1, 14, 19), "Narrador", "⛓️",
           "Uma corrente grossa desce até a base da cova de pedra. Se for puxada, a parede cede — e o que está lá dentro sai.", 3)
    c.fala("aldeia_sino", m.em(1, 21, 6), "Narrador", "🔔",
           "O sino ritual do chefe está preso por uma corrente à tranca do cercado. Quem o puxa, abre.", 3)
    c.fala("aldeia_criancas", m.em(2, 3, 6), "Criança", "🧒",
           "Moço! Moça! Tirem a gente daqui! Aquele bicho… ele é maior que a casa!", 4)
    d = c.finalizar("charcos_4b_aldeia", "A Aldeia dos Bruxos", "ar_livre", 4, {
        "primary": obj("rescue_prisoner", 150, 60, se_falhar={"renome": -5, "fato": FATO_MORTE}),
        "secondary": [obj("kill_target", 600, 250, [ITEM_TROFEU], renome=3, fato=FATO_FERRAO)],
        "alternativo": obj("kill_target", 150, 0, fato=FATO_FERRAO),
    }, ent, sai)
    d["prisoner"] = {"pos": prisioneiro, "room_id": 2}
    d["door_conditions"] = {"41,18": {"type": "decor", "key_decor_ids": [sino["id"]], "keys_mode": "any"}}
    d["secret_passages"] = [{"id": f"passage_cova_{i}", "type": "mechanism", "pos": list(pos),
                             "wall_material": "pedra_normal", "key_decor_ids": [corrente["id"]], "keys_mode": "any"}
                            for i, pos in enumerate(passagens)]
    return d
