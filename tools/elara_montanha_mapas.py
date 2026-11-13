"""Mapas da rota do Olho (montanhas acima de Graciero), usados por `gerar_elara_montanha.py`.

Tudo é determinístico (semente fixa por mapa). Calibração: 4 heróis nível 5, a rota mais difícil da campanha.
As duas vias (com o bardo que guia ou sem ele) vivem no MESMO mapa: o que muda são as falas, que levam `requisito`.
"""
import copy
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (RAIZ, os.path.join(RAIZ, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import server as S  # noqa: E402
from charcos_mapas import montar_fila, obj  # noqa: E402
from elara_graciero_fichas import ID_OLHO  # noqa: E402
from elara_montanha_fichas import TIPO_ASSASSINO, TIPO_BARDO  # noqa: E402

SOLDADO, ORC, DUAL, ARQUEIRO = "soldado", "orc", "goblin_dual", "goblin_arqueiro"

F_BARDO_AJUDOU = "elara_bardo_ajudou"
F_TRILHA = "elara_montanha_trilha"
F_DESFILADEIRO = "elara_montanha_desfiladeiro"
F_ASSASSINO_FUGIU = "elara_assassino_fugiu"
F_ROTA = "elara_rota_olho_vencida"
F_OLHO = "elara_olho_recuperado"
EXPECTED = {"heroes": 4, "level": 5}
ND_MIN, ND_MAX = 8, 14

COM_GUIA = {"fato": F_BARDO_AJUDOU}
SEM_GUIA = {"sem_fato": F_BARDO_AJUDOU}

FUGA_TEXTO = ("O assassino recua um passo, sorri sem os olhos e se joga rochedo abaixo. Quando vocês olham, só há "
              "neve solta e uma moeda de prata sem cunho: ele some como quem ainda tem mais uma ordem a cumprir.")


def _fala(c, fid, pos, nome, emoji, texto, raio=3, requisito=None):
    c.fala(fid, pos, nome, emoji, texto, raio)
    if requisito:
        c.falas[-1]["requisito"] = S._clean_requirement(requisito)


def _montar(prefixo, semente, larguras):
    return montar_fila(larguras, 14, prefixo, semente, piso="pedra_cinza", parede="rocha_marrom")


def masmorra_trilha():
    c, xs, hs = _montar("trilha", 5101, [11, 11, 11])
    m = c.m
    ent, sai = m.em(0, 1, hs // 2), m.em(2, 9, hs // 2)
    c.proteger(ent, sai)
    c.mon(SOLDADO, 0, 8, 2); c.mon(SOLDADO, 0, 8, 7)
    c.mon_livre(DUAL, 0, 3); c.mon_livre(ORC, 0, 3); c.mon_livre(SOLDADO, 0, 2); c.mon_livre(ARQUEIRO, 0, 3)
    c.espalha("rocha_grande", 0, 1); c.espalha("rochas_rachadas", 0, 3)
    c.armadilhas.append({"tipo": "armadilha_urso", "pos": m.em(0, 5, 1)})
    c.mon(ORC, 1, 8, 3); c.mon(ORC, 1, 8, 6)
    c.mon_livre(SOLDADO, 1, 4); c.mon_livre(DUAL, 1, 3); c.mon_livre(ARQUEIRO, 1, 4)
    c.espalha("rocha_grande", 1, 1); c.espalha("estalactites_estalagmites", 1, 2)
    c.armadilhas.append({"tipo": "rede", "pos": m.em(1, 4, 5)})
    c.mon(DUAL, 2, 6, 3); c.mon(DUAL, 2, 6, 6)
    c.mon_livre(SOLDADO, 2, 4); c.mon_livre(ORC, 2, 3); c.mon_livre(ARQUEIRO, 2, 3)
    c.espalha("rochas_rachadas", 2, 3)
    c.armadilhas.append({"tipo": "fosso_estacas", "pos": m.em(2, 4, 4)})
    _fala(c, "trilha_chegada", m.em(0, 1, 2), "Narrador", "⛰️",
          "A trilha sobe em curvas apertadas. Há marcas de rodas fundas na lama gelada: uma carga pesada passou "
          "por aqui sem pedir licença a ninguém.", 4)
    _fala(c, "trilha_guia", m.em(0, 2, hs // 2), "Bardo", "🎻",
          "\"Por aqui. Eles descansam depois do desfiladeiro. Fiquem perto: a serra não perdoa quem anda "
          "distraído.\"", 4, COM_GUIA)
    _fala(c, "trilha_marcas", m.em(0, 2, hs // 2), "Narrador", "🪨",
          "Nas pedras, riscos recentes de faca marcam o caminho: o Gilo passou por aqui com pressa.", 4, SEM_GUIA)
    return c.finalizar("elara_montanha_1", "A Trilha do Contrabando", "ar_livre", 5, {
        "primary": obj("reach_exit", 200, 60, fato=F_TRILHA), "secondary": []}, ent, sai,
        expected_party=dict(EXPECTED), marcador_entrada="poste")


def masmorra_desfiladeiro():
    """Terreno do `penhasco.json` do autor; aqui só entram história, monstros e objetivo.

    Ordem: chegada na margem sul, a guarda da ponte, o bardo (ou o rastro) na cabeceira, a travessia sob as flechas
    da outra margem e a trilha que sobe até a saída, no fim do caminho de pedras."""
    d = copy.deepcopy(S.carregar_dungeon("penhasco.json"))
    sul = {"id": 0, "x": 0, "y": 13, "w": 26, "h": 6, "role": "entrance", "locked": False, "doors": []}
    norte = {"id": 1, "x": 0, "y": 0, "w": 26, "h": 7, "role": "monster", "locked": False, "doors": []}
    monstros = {
        0: ((SOLDADO, (12, 14)), (SOLDADO, (13, 14)),
            (ORC, (10, 14)), (ORC, (15, 14)), (ORC, (16, 15)),
            (DUAL, (6, 16)), (DUAL, (19, 17)), (DUAL, (20, 16)),
            (ARQUEIRO, (9, 13)), (ARQUEIRO, (16, 13)), (ARQUEIRO, (5, 16))),
        1: ((SOLDADO, (11, 5)), (SOLDADO, (14, 5)), (SOLDADO, (10, 4)), (SOLDADO, (15, 4)),
            (DUAL, (9, 5)), (DUAL, (16, 5)), (DUAL, (12, 2)),
            (ORC, (13, 2)), (ORC, (18, 3)), (ORC, (6, 3)),
            (ARQUEIRO, (10, 6)), (ARQUEIRO, (15, 6)), (ARQUEIRO, (9, 6)), (ARQUEIRO, (16, 6))),
    }
    falas = [
        ("desfil_chegada", (12, 17), "🌬️", 4, None,
         "A trilha acaba na beira do desfiladeiro. Uma ponte de madeira range sobre o vazio, e o vento sobe do abismo "
         "como um aviso."),
        ("desfil_morte", (13, 13), "🏹", 1, COM_GUIA,
         "Um zumbido seco vindo da outra margem. O bardo, que ia à frente, cai de joelhos na cabeceira da ponte com "
         "uma flecha de ponta tingida no peito e uma moeda de prata sem cunho na mão aberta. Não houve tempo. Nem de "
         "gritar."),
        ("desfil_rastro", (13, 13), "🩸", 1, SEM_GUIA,
         "Na cabeceira da ponte, o rastro de alguém que subiu antes de vocês e foi calado no caminho: pegadas, sangue "
         "seco e uma flecha de ponta tingida, vinda da outra margem."),
        ("desfil_margem", (13, 4), "🌬️", 2, None,
         "A ponte fica para trás. O caminho de pedras segue margem acima, e ao longe sobe a fumaça de um acampamento."),
    ]
    d.update({
        "id": "elara_montanha_2", "name": "O Desfiladeiro", "ambiente": "ar_livre", "saida_permitida": False,
        "marcador_entrada": "poste", "expected_party": dict(EXPECTED), "exit": {"x": 16, "y": 0},
        "rooms": [sul, norte],
        "monsters": [{"type": t, "pos": list(pos), "room_id": sala, "boss": False, "target": False}
                     for sala, grupo in monstros.items() for t, pos in grupo],
        "chests": [{"pos": [16, 17], "gold": 0, "items": [{"id": "health_potion_improved"} for _ in range(4)],
                    "key_objective": False}],
        "traps": [{"tipo": "fosso_estacas", "pos": [8, 15]}, {"tipo": "rede", "pos": [15, 2]},
                  {"tipo": "armadilha_urso", "pos": [16, 2]},
                  {"tipo": "armadilha_dardos_envenenados", "pos": [15, 1], "veneno_id": "veneno_escorpiao_pedra"}],
        "falas": [{"id": fid, "pos": list(pos), "falante": {"nome": "Narrador", "emoji": emoji}, "texto": texto,
                   "trigger": {"tipo": "proximidade", "raio": raio},
                   **({"requisito": S._clean_requirement(req)} if req else {})}
                  for fid, pos, emoji, raio, req, texto in falas],
        "objectives": {"primary": obj("reach_exit", 240, 80, fato=F_DESFILADEIRO), "secondary": []},
    })
    return d


def masmorra_caravana():
    c, xs, hs = _montar("carav", 5103, [11, 12, 12])
    m = c.m
    ent, sai = m.em(0, 1, hs // 2), m.em(2, 10, hs // 2)
    c.proteger(ent, sai)
    c.mon(SOLDADO, 0, 8, 2); c.mon(SOLDADO, 0, 8, 7)
    c.mon_livre(DUAL, 0, 3); c.mon_livre(ORC, 0, 3); c.mon_livre(ARQUEIRO, 0, 4); c.mon_livre(SOLDADO, 0, 2)
    c.espalha("carroca", 0, 1); c.espalha("barril", 0, 3)
    c.armadilhas.append({"tipo": "armadilha_urso", "pos": m.em(0, 5, 1)})
    c.mon(TIPO_BARDO, 1, 8, 4)
    c.mon(SOLDADO, 1, 5, 3); c.mon(SOLDADO, 1, 5, 7)
    c.mon_livre(DUAL, 1, 2); c.mon_livre(ARQUEIRO, 1, 2); c.mon_livre(SOLDADO, 1, 2)
    c.espalha("carroca", 1, 1); c.espalha("barril", 1, 3)
    c.armadilhas.append({"tipo": "rede", "pos": m.em(1, 3, 5)})
    chefe = c.mon(TIPO_ASSASSINO, 2, 8, 4, alvo=True)
    chefe["fuga_chefe"] = {"fato": F_ASSASSINO_FUGIU, "texto": FUGA_TEXTO}
    c.mon(DUAL, 2, 5, 3); c.mon(DUAL, 2, 5, 7)
    c.mon_livre(SOLDADO, 2, 3); c.mon_livre(ORC, 2, 2)
    c.espalha("carroca", 2, 1); c.espalha("barril", 2, 2)
    c.armadilhas.append({"tipo": "armadilha_dardos_envenenados", "pos": m.em(2, 3, 5),
                         "veneno_id": "veneno_escorpiao_pedra"})
    _fala(c, "carav_chegada", m.em(0, 1, 2), "Narrador", "🔥",
          "Fogueiras de acampamento e carroças cobertas de lona: a caravana descansa, e quem a vigia não parece "
          "estar ali por acaso.", 4)
    _fala(c, "carav_bau", m.em(2, 9, 2), "Narrador", "📦",
          "No fundo da última carroça, um baú de ferro pesa mais do que devia. Está quente ao toque.", 5)
    _fala(c, "carav_guia", m.em(2, 2, hs // 2), "Narrador", "🎻",
          "Se o guia estivesse aqui, teria dito que era exatamente isto. Vocês seguem em frente por ele.", 4,
          COM_GUIA)
    return c.finalizar("elara_montanha_3", "A Caravana", "ar_livre", 5, {
        "primary": obj("kill_target", 400, 150, itens=[ID_OLHO], fatos=[F_ROTA, F_OLHO]), "secondary": []},
        ent, sai, expected_party=dict(EXPECTED), marcador_entrada="poste", saida_permitida=False)


def nd_por_sala(d):
    cr = {m["type"]: S.monster_cr(m) for m in S.MONSTER_DEFS}
    out = {}
    for m in d["monsters"]:
        out[m["room_id"]] = out.get(m["room_id"], 0) + cr.get(m["type"], 0)
    return out


ARQUIVOS = {"elara_montanha_1.json": masmorra_trilha, "elara_montanha_2.json": masmorra_desfiladeiro,
            "elara_montanha_3.json": masmorra_caravana}
