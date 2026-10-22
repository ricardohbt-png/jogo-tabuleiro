"""Mapas do Ramo B de "O Resgate de Elara" (Adhadal e Corvin), usados por `gerar_elara_gilo.py`.

Adhadal são CÓPIAS ajustadas dos protótipos do autor (`floresta.json`, `floresta_2.json`), que nunca
são alterados; Corvin é novo. Tudo determinístico. Calibração: grupo esperado de 4 heróis nível 3.
"""
import collections
import copy
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (RAIZ, os.path.join(RAIZ, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import server as S  # noqa: E402
from charcos_mapas import montar_fila, obj  # noqa: E402
from gerar_campanha_sombras import fala as _fala  # noqa: E402
from elara_gilo_ficha import TIPO_GILO  # noqa: E402

F_ADHADAL = "elara_adhadal_vencida"
F_CACADA = "elara_cacada_vencida"
F_GILO_FUGIU = "elara_gilo_fugiu"
F_PISTA = "elara_pista_graciero"
ND_MAX_ADHADAL = 10.8          # 0,9 × poder (4 heróis × nível 3)
EXPECTED = {"heroes": 4, "level": 3}

SOLDADO, ORC, DUAL, ARQUEIRO = "soldado", "orc", "goblin_dual", "goblin_arqueiro"

FUGA_TEXTO = ("Derrotado, o Gilo ri entre os dentes. Uma melodia estridente vem de uma janela, o ar se "
              "enche de fumaça e, quando ela baixa, ele sumiu — e um bardo, no telhado, já fugia.")


def _proto(nome):
    with open(os.path.join(RAIZ, "dungeons", nome + ".json"), encoding="utf-8") as f:
        return json.load(f)


def _crs():
    return {m["type"]: S.monster_cr(m) for m in S.MONSTER_DEFS}


def nd_total(d):
    cr = _crs()
    return sum(cr.get(m["type"], 0) for m in d["monsters"])


# ─── geometria do protótipo ─────────────────────────────────────────────────
def casas_bloqueadas(d):
    sala = S.GameRoom("TMP")
    out = set()
    for dec in d.get("decorations", []):
        meta = S.DECOR_TYPES.get(dec["type"], {})
        if meta.get("pisavel") or meta.get("special") == "wall":
            continue
        out.update(tuple(t) for t in sala._decor_tiles(dec))
    return out


def alcancaveis(d, origem):
    """BFS (4 direções) por chão sem decoração sólida; devolve {casa: distância}."""
    t, bloq = d["tiles"], casas_bloqueadas(d)
    h, w = len(t), len(t[0])
    dist = {tuple(origem): 0}
    fila = collections.deque([tuple(origem)])
    while fila:
        x, y = fila.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if (0 <= n[0] < w and 0 <= n[1] < h and n not in dist and n not in bloq
                    and t[n[1]][n[0]] in (S.FLOOR, S.DOOR)):
                dist[n] = dist[(x, y)] + 1
                fila.append(n)
    return dist


def _livres(d, dist, minimo, maximo):
    """Casas do caminho, entre as distâncias dadas, sem monstro nem decoração, em ordem estável."""
    ocupadas = {tuple(m["pos"]) for m in d["monsters"]} | casas_bloqueadas(d)
    ent, sai = d["entrance"], d.get("exit") or {}
    ocupadas |= {(ent["x"], ent["y"]), (sai.get("x"), sai.get("y"))}
    return sorted(c for c, k in dist.items() if minimo <= k <= maximo and c not in ocupadas)


def _espacar(casas, n):
    if not casas or n <= 0:
        return []
    passo = max(1, len(casas) // n)
    return casas[passo // 2::passo][:n]


def _adaptar(d, did, nome, trampas, falas):
    d = copy.deepcopy(d)
    d.update({"id": did, "name": nome, "marcador_entrada": "poste", "expected_party": dict(EXPECTED)})
    dist = alcancaveis(d, (d["entrance"]["x"], d["entrance"]["y"]))
    sai = d.get("exit")
    alvo = dist[(sai["x"], sai["y"])] if sai else max(dist.values())
    cand = _livres(d, dist, 6, max(7, alvo - 4))
    pos = _espacar(cand, len(trampas) + len(falas))
    for tipo, p in zip(trampas, pos):
        d["traps"].append({"tipo": tipo, "pos": list(p)})
    for (fid, nome_f, emoji, texto), p in zip(falas, pos[len(trampas):]):
        d["falas"].append(_fala(fid, list(p), nome_f, emoji, texto, 3))
    return d


# ─── Adhadal ────────────────────────────────────────────────────────────────
def masmorra_adhadal_1():
    d = _adaptar(_proto("floresta"), "elara_adhadal_1", "Floresta de Adhadal — Entrada",
                 ["armadilha_urso", "rede", "buraco"],
                 [("adhadal_pegadas", "Narrador", "👣",
                   "Pegadas fundas de bota, de alguém com pressa e com peso. Seguem para dentro da mata.")])
    d["objectives"]["primary"] = obj("reach_exit", 100, 20)
    return d


def masmorra_adhadal_2():
    d = copy.deepcopy(_proto("floresta_2"))
    cr = _crs()
    d["monsters"].sort(key=lambda m: (-cr.get(m["type"], 0), m["pos"][1], m["pos"][0]))
    while nd_total(d) > ND_MAX_ADHADAL:
        d["monsters"].pop(0)
    d["monsters"].sort(key=lambda m: (m["pos"][1], m["pos"][0]))
    dist = alcancaveis(d, (d["entrance"]["x"], d["entrance"]["y"]))
    ocup = {tuple(m["pos"]) for m in d["monsters"]}
    longe = max(k for c, k in dist.items() if c not in ocup)
    sai = min(c for c, k in dist.items() if k >= longe - 2 and c not in ocup)
    d["exit"] = {"x": sai[0], "y": sai[1]}
    d["saida_permitida"] = False
    d = _adaptar(d, "elara_adhadal_2", "Floresta de Adhadal — Coração da Mata",
                 ["armadilha_urso", "rede"],
                 [("adhadal_separam", "Narrador", "🌲",
                   "Aqui os rastros se separam: um segue para o norte, outro some na água. Quem foi na frente "
                   "sabia que seria seguido.")])
    d["objectives"]["primary"] = obj("reach_exit", 160, 40, fato=F_ADHADAL)
    return d


# ─── Corvin ─────────────────────────────────────────────────────────────────
def masmorra_corvin_cacada():
    c, xs, hs = montar_fila([10, 11, 10], 14, "cacada", 3301, piso="terra", parede="parede_terra")
    m = c.m
    ent, sai = m.em(0, 1, hs // 2), m.em(2, 8, hs // 2)
    c.proteger(ent, sai)
    c.mon(ORC, 0, 7, 2); c.mon(ORC, 0, 7, 6)
    c.mon_livre(SOLDADO, 0, 2); c.mon_livre(ARQUEIRO, 0, 2); c.mon_livre(DUAL, 0, 1)
    c.espalha("barril", 0, 3); c.espalha("estante", 0, 1)
    c.armadilhas.append({"tipo": "armadilha_urso", "pos": m.em(0, 5, 1)})
    c.mon(SOLDADO, 1, 8, 3); c.mon(SOLDADO, 1, 8, 6)
    c.mon_livre(ORC, 1, 2); c.mon_livre(ARQUEIRO, 1, 2); c.mon_livre(DUAL, 1, 1)
    c.espalha("barril", 1, 3); c.espalha("carroca", 1, 1)
    c.armadilhas.append({"tipo": "rede", "pos": m.em(1, 4, 5)})
    c.mon(DUAL, 2, 6, 3); c.mon(DUAL, 2, 6, 6)
    c.mon_livre(SOLDADO, 2, 2); c.mon_livre(ORC, 2, 2); c.mon_livre(ARQUEIRO, 2, 2)
    c.espalha("barril", 2, 3); c.espalha("estante_armas", 2, 1)
    c.armadilhas.append({"tipo": "armadilha_dardos_envenenados", "pos": m.em(2, 4, 4),
                         "veneno_id": "veneno_escorpiao_pedra"})
    c.bau(m.em(2, 8, 3), 40, [{"id": "carta", "texto": (
        "\"O homem de dedos sujos dorme no velho curtume, depois da ponte. Leva a pedra e uma carta para "
        "Graciero. Não deixem ele chegar de manhã.\"")}])
    c.baus[-1]["key_objective"] = True
    c.fala("cacada_chegada", m.em(0, 1, 2), "Narrador", "🌆",
           "Os arredores de Corvin cheiram a couro curtido e a medo. Há gente demais calada nas janelas.", 4)
    return c.finalizar("elara_corvin_cacada", "Os Arredores de Corvin", "ar_livre", 3, {
        "primary": obj("open_key_chest", 140, 50, fato=F_CACADA), "secondary": []}, ent, sai,
        expected_party=dict(EXPECTED))


def masmorra_corvin_gilo():
    c, xs, hs = montar_fila([12, 12], 14, "gilo", 3302, piso="madeira_escura", parede="madeira")
    m = c.m
    ent, sai = m.em(0, 1, hs // 2), m.em(1, 10, hs // 2)
    c.proteger(ent, sai)
    c.mon(SOLDADO, 0, 8, 3); c.mon(SOLDADO, 0, 8, 7)
    c.mon_livre(DUAL, 0, 2); c.mon_livre(ORC, 0, 2); c.mon_livre(ARQUEIRO, 0, 2)
    c.espalha("barril", 0, 3); c.espalha("mesa_cadeiras", 0, 1)
    c.armadilhas.append({"tipo": "armadilha_urso", "pos": m.em(0, 5, 1)})
    gilo = c.mon(TIPO_GILO, 1, 7, 4, alvo=True)
    gilo["fuga_chefe"] = {"fato": F_GILO_FUGIU, "texto": FUGA_TEXTO}
    c.mon(SOLDADO, 1, 4, 3); c.mon(SOLDADO, 1, 4, 7)
    c.mon_livre(DUAL, 1, 2)
    c.espalha("barril", 1, 3); c.espalha("estante", 1, 1)
    c.armadilhas.append({"tipo": "rede", "pos": m.em(1, 3, 5)})
    c.bau(m.em(1, 10, 2), 80, [{"id": "carta", "texto": (
        "\"Levo a pedra e as encomendas para Graciero. O nobre das esposas paga em ouro e não faz perguntas. "
        "Se alguém me seguir, a fumaça e o bardo cuidam do resto.\"")}])
    c.fala("gilo_chegada", m.em(0, 1, 2), "Narrador", "🏚️",
           "O velho curtume range ao vento. Alguém ri lá dentro, baixo, de quem já esperava visita.", 4)
    return c.finalizar("elara_corvin_gilo", "O Esconderijo do Gilo", "masmorra", 3, {
        "primary": obj("kill_target", 200, 80, fato=F_PISTA), "secondary": []}, ent, sai,
        expected_party=dict(EXPECTED))


ARQUIVOS = {"elara_adhadal_1.json": masmorra_adhadal_1, "elara_adhadal_2.json": masmorra_adhadal_2,
            "elara_corvin_cacada.json": masmorra_corvin_cacada, "elara_corvin_gilo.json": masmorra_corvin_gilo}
