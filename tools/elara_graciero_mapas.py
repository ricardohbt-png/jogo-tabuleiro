"""Mapas de Graciero e do esconderijo do Leonel, usados por `gerar_elara_graciero.py`.

Tudo é determinístico (semente fixa por mapa). Calibração: Graciero 4 heróis nível 4; esconderijo nível 5.
A Praça viva e a morta partem da MESMA planta e das mesmas sementes: só mudam a fala e a decoração.
O esconderijo alerta é o normal com guardas e uma armadilha a mais, acrescentados DEPOIS dos básicos
(assim as casas sorteadas antes não mudam).
"""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (RAIZ, os.path.join(RAIZ, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import server as S  # noqa: E402
from charcos_mapas import montar_fila, obj  # noqa: E402
from elara_graciero_fichas import TIPO_ESCORPIAO, TIPO_LEONEL  # noqa: E402

SOLDADO, ORC, DUAL, ARQUEIRO = "soldado", "orc", "goblin_dual", "goblin_arqueiro"

RELOGIO_ID = "elara_graciero"
F_LENTO = "elara_graciero_lento"
F_BECO = "elara_beco_vencido"
F_CAIS = "elara_cais_vencido"
F_GILO_MORREU = "elara_gilo_morreu"
F_VIU_MORRER = "elara_viu_gilo_morrer"
F_DICA_MONTANHA = "elara_dica_montanha"
F_ELARA = "elara_elara_salva"
F_LEONEL = "elara_leonel_vencido"

EXP4 = {"heroes": 4, "level": 4}
EXP5 = {"heroes": 4, "level": 5}


def relogio_graciero():
    return {"id": RELOGIO_ID, "limite": 30, "fato_ao_passar": F_LENTO, "avisos": [
        {"em": 12, "texto": "Os sinos da cidade batem a hora. Alguém, em algum lugar, já está se mexendo."},
        {"em": 22, "texto": "As ruas esvaziam. Quem procurava o grupo começa a se cansar de esperar."},
        {"em": 30, "texto": "O tempo está quase esgotado: o que correu pela cidade já não vai esperar."}]}


def nd_por_sala(d):
    cr = {m["type"]: S.monster_cr(m) for m in S.MONSTER_DEFS}
    out = {}
    for m in d["monsters"]:
        out[m["room_id"]] = out.get(m["room_id"], 0) + cr.get(m["type"], 0)
    return out


def _frente(prefixo, semente, larguras, did, nome, ambiente, carta, fato, fala_texto):
    c, xs, hs = montar_fila(larguras, 14, prefixo, semente, piso="pedra_cinza", parede="pedra_normal")
    m = c.m
    ent, sai = m.em(0, 1, hs // 2), m.em(2, larguras[2] - 2, hs // 2)
    c.proteger(ent, sai)
    c.mon(SOLDADO, 0, 7, 2); c.mon(SOLDADO, 0, 7, 6)
    c.mon_livre(ORC, 0, 2); c.mon_livre(ARQUEIRO, 0, 2); c.mon_livre(DUAL, 0, 1)
    c.espalha("barril", 0, 3); c.espalha("estante", 0, 1)
    c.armadilhas.append({"tipo": "armadilha_urso", "pos": m.em(0, 5, 1)})
    c.mon(ORC, 1, 8, 3); c.mon(ORC, 1, 8, 6)
    c.mon_livre(SOLDADO, 1, 2); c.mon_livre(DUAL, 1, 1); c.mon_livre(ARQUEIRO, 1, 2)
    c.espalha("barril", 1, 3); c.espalha("carroca", 1, 1)
    c.armadilhas.append({"tipo": "rede", "pos": m.em(1, 4, 5)})
    c.mon(DUAL, 2, 6, 3); c.mon(DUAL, 2, 6, 6)
    c.mon_livre(SOLDADO, 2, 2); c.mon_livre(ORC, 2, 2); c.mon_livre(ARQUEIRO, 2, 2)
    c.espalha("barril", 2, 3); c.espalha("estante_armas", 2, 1)
    c.armadilhas.append({"tipo": "armadilha_dardos_envenenados", "pos": m.em(2, 4, 4),
                         "veneno_id": "veneno_escorpiao_pedra"})
    c.bau(m.em(2, larguras[2] - 3, 3), 60, [{"id": "carta", "texto": carta}])
    c.baus[-1]["key_objective"] = True
    c.fala(prefixo + "_chegada", m.em(0, 1, 2), "Narrador", "🏙️", fala_texto, 4)
    d = c.finalizar(did, nome, ambiente, 4, {
        "primary": obj("open_key_chest", 160, 60, fato=fato), "secondary": []}, ent, sai,
        expected_party=dict(EXP4))
    d["relogio"] = relogio_graciero()
    return d


def masmorra_beco():
    return _frente("beco", 4101, [10, 10, 10], "elara_graciero_beco", "Os Becos de Graciero", "ar_livre",
                   "\"Entrega de sexta: três moças, a de cabelo escuro primeiro. O comprador paga na porta dos "
                   "fundos, como sempre, e não quer perguntas. — o Gilo\"", F_BECO,
                   "Graciero é grande demais para um grupo só olhar. Nos becos, as pessoas conhecem o assunto "
                   "e fingem que não.")


def masmorra_cais():
    return _frente("cais", 4102, [11, 11, 10], "elara_graciero_cais", "O Cais dos Leilões", "ar_livre",
                   "\"A casa do Leonel recebe as encomendas pelo cais. A cela é nos porões, por trás da casa de "
                   "leilões. A irmã do mago é a do meio.\"", F_CAIS,
                   "O cais cheira a maresia e a dinheiro sujo. Em Graciero, nome de nobre se diz baixinho.")


def _praca(prefixo, did, nome, viva):
    c, xs, hs = montar_fila([16], 14, prefixo, 4103, piso="pedra_cinza", parede="pedra_normal")
    m = c.m
    ent, sai = m.em(0, 1, hs // 2), m.em(0, 14, hs // 2)
    c.proteger(ent, sai)
    for dx, dy in ((8, 2), (8, 7), (11, 4), (11, 8)):
        c.mon(TIPO_ESCORPIAO, 0, dx, dy)
    c.mon_livre(TIPO_ESCORPIAO, 0, 2)
    c.espalha("barril", 0, 3); c.espalha("carroca", 0, 1)
    c.armadilhas.append({"tipo": "armadilha_urso", "pos": m.em(0, 5, 3)})
    if viva:
        c.fala(prefixo + "_ultimas", m.em(0, 2, hs // 2), "Gilo Dedos Sujos", "🗡️",
               "Não... não era para ser assim! A pedra já foi entregue aos que sobem a montanha. O nobre da "
               "cidade paga em ouro... Eles... estão vindo...", 12)
        c.fala(prefixo + "_silencio", m.em(0, 8, hs // 2), "Narrador", "🦂",
               "Escorpiões grandes como cães saem dos esgotos e cobrem o Gilo. O grito dura pouco. Depois só "
               "o estalar das garras vem na direção de vocês.", 12)
    else:
        c.deco("monte_ossos", 0, 9, 5)
        c.fala(prefixo + "_corpo", m.em(0, 2, hs // 2), "Narrador", "🦂",
               "Chegaram tarde. No meio da praça, o que sobrou do mercenário: ossos limpos, botas fundas de lama "
               "e um cheiro doce de peçonha. As garras ainda estalam na sombra.", 12)
    fatos = {"fato": F_GILO_MORREU}
    if viva:
        fatos["fatos"] = [F_VIU_MORRER, F_DICA_MONTANHA]
    return c.finalizar(did, nome, "ar_livre", 4, {
        "primary": obj("kill_all", 200, 80, **fatos), "secondary": []}, ent, sai, expected_party=dict(EXP4))


def masmorra_praca_viva():
    return _praca("pracav", "elara_graciero_praca_viva", "A Praça dos Escorpiões", True)


def masmorra_praca_morta():
    return _praca("pracam", "elara_graciero_praca_morta", "A Praça dos Escorpiões", False)


def _leonel_1(alerta):
    c, xs, hs = montar_fila([10, 11, 10], 14, "casa", 4105, piso="madeira_escura", parede="madeira")
    m = c.m
    ent, sai = m.em(0, 1, hs // 2), m.em(2, 8, hs // 2)
    c.proteger(ent, sai)
    c.mon(SOLDADO, 0, 7, 2); c.mon(SOLDADO, 0, 7, 6)
    c.mon_livre(ORC, 0, 2); c.mon_livre(ARQUEIRO, 0, 2)
    c.espalha("barril", 0, 2); c.espalha("estante", 0, 1)
    c.armadilhas.append({"tipo": "armadilha_urso", "pos": m.em(0, 5, 1)})
    c.mon(DUAL, 1, 8, 3); c.mon(DUAL, 1, 8, 6)
    c.mon_livre(SOLDADO, 1, 2); c.mon_livre(ORC, 1, 1)
    c.espalha("mesa_cadeiras", 1, 1); c.espalha("estante", 1, 1)
    c.armadilhas.append({"tipo": "rede", "pos": m.em(1, 4, 5)})
    c.mon(SOLDADO, 2, 6, 3); c.mon(ORC, 2, 6, 6)
    c.mon_livre(DUAL, 2, 2); c.mon_livre(ARQUEIRO, 2, 2)
    c.espalha("barril", 2, 2); c.espalha("estante_armas", 2, 1)
    c.armadilhas.append({"tipo": "armadilha_dardos_envenenados", "pos": m.em(2, 4, 4),
                         "veneno_id": "veneno_escorpiao_pedra"})
    c.fala("casa_chegada", m.em(0, 1, 2), "Narrador", "🏛️",
           "A casa de leilões brilha de dia. Por trás do ouro e das cortinas, homens armados vigiam cada porta.", 4)
    if alerta:       # acrescentados por último: não deslocam nada do que foi sorteado antes
        c.mon_livre(SOLDADO, 0, 1); c.mon_livre(DUAL, 1, 1)
        c.armadilhas.append({"tipo": "rede", "pos": m.em(2, 3, 2)})
        c.fala("casa_alerta", m.em(1, 1, 2), "Narrador", "⚠️",
               "Os guardas estão postados em pares, olhando as portas. Alguém avisou que viriam.", 4)
    did, nome = ("elara_leonel_1_alerta", "A Casa de Leilões (em alerta)") if alerta else ("elara_leonel_1", "A Casa de Leilões")
    return c.finalizar(did, nome, "masmorra", 5, {
        "primary": obj("reach_exit", 220, 80), "secondary": []}, ent, sai, expected_party=dict(EXP5))


def masmorra_leonel_1():
    return _leonel_1(False)


def masmorra_leonel_1_alerta():
    return _leonel_1(True)


def masmorra_leonel_2():
    c, xs, hs = montar_fila([12, 13], 14, "porao", 4106, piso="pedra_cinza", parede="pedra_normal")
    m = c.m
    ent, sai = m.em(0, 1, hs // 2), m.em(1, 11, hs // 2)
    c.proteger(ent, sai)
    c.mon(SOLDADO, 0, 8, 3); c.mon(SOLDADO, 0, 8, 7)
    c.mon_livre(ORC, 0, 2); c.mon_livre(DUAL, 0, 1); c.mon_livre(ARQUEIRO, 0, 2)
    c.espalha("grades_prisao", 0, 2); c.espalha("barril", 0, 2)
    c.armadilhas.append({"tipo": "armadilha_urso", "pos": m.em(0, 5, 1)})
    chefe = c.mon(TIPO_LEONEL, 1, 8, 4, alvo=True)
    c.mon(SOLDADO, 1, 5, 3); c.mon(SOLDADO, 1, 5, 7)
    c.mon_livre(DUAL, 1, 2); c.mon_livre(ORC, 1, 1)
    c.espalha("barril", 1, 2); c.espalha("estante", 1, 1)
    c.armadilhas.append({"tipo": "rede", "pos": m.em(1, 3, 5)})
    c.bau(m.em(1, 11, 2), 100, [{"id": "carta", "texto": (
        "\"Elara, a do Templo: vendida para o nobre das montanhas. Se o mago vier, entregue-lhe a chave e diga "
        "que a pedra não importa mais.\"")}])
    c.baus[-1]["key_objective"] = True
    c.fala("porao_chegada", m.em(0, 1, 2), "Narrador", "⛓️",
           "Os porões cheiram a mofo e a algemas. Choro baixo vem de trás de uma parede de grades.", 4)
    c.fala("porao_elara", m.em(1, 10, 2), "Elara", "🙏",
           "Eu sabia que viriam! Não deixem que ele me leve de novo... o homem que paga disse que alguém "
           "ainda mais forte espera a pedra.", 3)
    d = c.finalizar("elara_leonel_2", "Os Porões do Leonel", "masmorra", 5, {
        "primary": obj("kill_target", 300, 150, fato=F_LEONEL),
        "secondary": [obj("open_key_chest", 100, 0, fato=F_ELARA)]}, ent, sai,
        expected_party=dict(EXP5), saida_permitida=False)
    return d


ARQUIVOS = {
    "elara_graciero_beco.json": masmorra_beco, "elara_graciero_cais.json": masmorra_cais,
    "elara_graciero_praca_viva.json": masmorra_praca_viva, "elara_graciero_praca_morta.json": masmorra_praca_morta,
    "elara_leonel_1.json": masmorra_leonel_1, "elara_leonel_1_alerta.json": masmorra_leonel_1_alerta,
    "elara_leonel_2.json": masmorra_leonel_2}
