"""Mapas da rota do Olho (montanhas acima de Graciero), usados por `gerar_elara_montanha.py`.

Tudo é determinístico (semente fixa por mapa). Calibração: 4 heróis nível 5, a rota mais difícil da campanha.
As duas vias (com o bardo que guia ou sem ele) vivem no MESMO mapa: o que muda são as falas, que levam `requisito`.
"""
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
    c, xs, hs = _montar("desfil", 5102, [12, 12, 12])
    m = c.m
    ent, sai = m.em(0, 1, hs // 2), m.em(2, 10, hs // 2)
    c.proteger(ent, sai)
    c.mon(SOLDADO, 0, 9, 3); c.mon(SOLDADO, 0, 9, 7)
    c.mon_livre(DUAL, 0, 3); c.mon_livre(ORC, 0, 3); c.mon_livre(ARQUEIRO, 0, 4); c.mon_livre(SOLDADO, 0, 1)
    c.espalha("rocha_grande", 0, 1); c.espalha("rochas_rachadas", 0, 3)
    c.armadilhas.append({"tipo": "fosso_estacas", "pos": m.em(0, 5, 2)})
    c.mon(ORC, 1, 9, 3); c.mon(ORC, 1, 9, 6)
    c.mon_livre(SOLDADO, 1, 4); c.mon_livre(DUAL, 1, 3); c.mon_livre(ARQUEIRO, 1, 4)
    c.espalha("estalactites_estalagmites", 1, 3); c.espalha("rochas_rachadas", 1, 2)
    c.armadilhas.append({"tipo": "armadilha_urso", "pos": m.em(1, 4, 5)})
    c.armadilhas.append({"tipo": "rede", "pos": m.em(1, 6, 2)})
    c.mon(DUAL, 2, 7, 3); c.mon(DUAL, 2, 7, 7)
    c.mon_livre(SOLDADO, 2, 4); c.mon_livre(ORC, 2, 3); c.mon_livre(ARQUEIRO, 2, 3)
    c.espalha("rocha_grande", 2, 1); c.espalha("rochas_rachadas", 2, 3)
    c.armadilhas.append({"tipo": "armadilha_dardos_envenenados", "pos": m.em(2, 4, 4),
                         "veneno_id": "veneno_escorpiao_pedra"})
    _fala(c, "desfil_chegada", m.em(0, 1, 2), "Narrador", "🌬️",
          "O desfiladeiro é uma fenda estreita entre dois paredões. O vento assobia por ela como um aviso.", 4)
    _fala(c, "desfil_morte", m.em(1, 2, hs // 2), "Narrador", "🏹",
          "Um zumbido seco. O bardo, que ia à frente, cai de joelhos com uma flecha de ponta tingida no peito e uma "
          "moeda de prata sem cunho na mão aberta. Não houve tempo. Nem de gritar.", 5, COM_GUIA)
    _fala(c, "desfil_rastro", m.em(1, 2, hs // 2), "Narrador", "🩸",
          "Ao pé de um rochedo, o rastro de alguém que subiu antes de vocês e foi calado no caminho: pegadas, sangue "
          "seco e uma flecha de ponta tingida.", 5, SEM_GUIA)
    return c.finalizar("elara_montanha_2", "O Desfiladeiro", "ar_livre", 5, {
        "primary": obj("reach_exit", 240, 80, fato=F_DESFILADEIRO), "secondary": []}, ent, sai,
        expected_party=dict(EXPECTED), marcador_entrada="poste", saida_permitida=False)


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
