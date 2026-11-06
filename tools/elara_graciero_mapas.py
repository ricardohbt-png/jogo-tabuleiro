"""Mapas de Graciero e do esconderijo do Leonel, usados por `gerar_elara_graciero.py`.

Tudo é determinístico (semente fixa por mapa). Calibração: Graciero 4 heróis nível 4; esconderijo nível 5.
A Praça viva e a morta partem da MESMA planta e das mesmas sementes: só mudam a fala e a decoração.
O esconderijo alerta é o normal com guardas e uma armadilha a mais, acrescentados DEPOIS dos básicos
(assim as casas sorteadas antes não mudam).
"""
import copy
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (RAIZ, os.path.join(RAIZ, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import server as S  # noqa: E402
from charcos_mapas import Cena, montar_fila, obj  # noqa: E402
from gerar_campanha_sombras import Mapa  # noqa: E402
from elara_graciero_fichas import ID_OLHO, TIPO_ESCORPIAO, TIPO_LEONEL  # noqa: E402

SOLDADO, ORC, DUAL, ARQUEIRO = "soldado", "orc", "goblin_dual", "goblin_arqueiro"

RELOGIO_ID = "elara_graciero"
F_LENTO = "elara_graciero_lento"
F_BECO = "elara_beco_vencido"
F_CAIS = "elara_cais_vencido"
F_GILO_MORREU = "elara_gilo_morreu"
F_VIU_MORRER = "elara_viu_gilo_morrer"
F_DICA_MONTANHA = "elara_dica_montanha"
F_OLHO = "elara_olho_recuperado"
F_ELARA = "elara_elara_salva"
F_LEONEL = "elara_leonel_vencido"
F_ELARA_MORTA = "elara_morta"

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
                   "\"A casa do Leonel recebe as encomendas pelo cais. A cela fica na mansão, escondida atrás do salão de "
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
        # A morte do Gilo já passou na abertura da etapa (gerar_elara_graciero.intro_gilo).
        c.fala(prefixo + "_silencio", m.em(0, 8, hs // 2), "Narrador", "🦂",
               "O grito do Gilo já se foi. Agora só o estalar das garras atravessa a praça, vindo das grades "
               "na direção de vocês.", 12)
    else:
        c.deco("monte_ossos", 0, 9, 5)
        c.fala(prefixo + "_corpo", m.em(0, 2, hs // 2), "Narrador", "🦂",
               "Chegaram tarde. No meio da praça, o que sobrou do mercenário: ossos limpos, botas fundas de lama "
               "e um cheiro doce de peçonha. Entre os ossos há um bilhete amassado: \"Pelas moças, o ouro "
               "combinado. Leonel.\" As garras ainda estalam na sombra.", 12)
    fatos = {"fato": F_GILO_MORREU}
    if viva:
        fatos["fatos"] = [F_VIU_MORRER, F_DICA_MONTANHA]
    return c.finalizar(did, nome, "ar_livre", 4, {
        "primary": obj("kill_all", 200, 80, **fatos), "secondary": []}, ent, sai, expected_party=dict(EXP4))


def masmorra_praca_viva():
    return _praca("pracav", "elara_graciero_praca_viva", "A Praça dos Escorpiões", True)


# Casas dos escorpiões extras da Praça da pedra: junto às grades, longe da entrada.
ESCORPIOES_DA_PEDRA = ([20, 6], [21, 8], [21, 10], [20, 11], [19, 12], [21, 12])


def masmorra_praca_pedra():
    """Ramo B: o Olho ainda está com o Gilo e os escorpiões vêm por ele. É a Praça viva como o autor a deixou, com o
    dobro de escorpiões, e quem vence recebe a pedra ali. Sem a dica da montanha: a pedra nunca saiu da cidade."""
    d = copy.deepcopy(S.carregar_dungeon("elara_graciero_praca_viva.json") or masmorra_praca_viva())
    d["id"] = "elara_graciero_praca_pedra"
    base = len(d["monsters"])
    d["monsters"] += [{"type": TIPO_ESCORPIAO, "pos": list(pos), "room_id": 0, "boss": False, "target": False,
                       "source_id": f"mob_{base + i}"} for i, pos in enumerate(ESCORPIOES_DA_PEDRA)]
    d["falas"][0]["texto"] = ("O grito do Gilo já se foi. O embrulho dele ficou caído entre as pedras, e as garras "
                              "saem de todas as grades, atrás dele e de vocês.")
    principal = d["objectives"]["primary"]
    principal["fatos"] = [F_VIU_MORRER, F_OLHO]
    principal["reward"]["items"] = [{"id": ID_OLHO}]
    return d


def masmorra_praca_morta():
    return _praca("pracam", "elara_graciero_praca_morta", "A Praça dos Escorpiões", False)


def masmorra_leonel_1():
    """Terreno da mansão, feito à mão pelo autor no `elara_leonel_1.json`; aqui só entram falas e objetivo.

    O grupo derrota todos no terreno e depois acha a entrada, nos fundos da mansão."""
    d = copy.deepcopy(S.carregar_dungeon("elara_leonel_1.json"))
    outras = [f for f in d["falas"] if f["id"] not in ("casa_chegada", "casa_entrada")]
    d["falas"] = [
        {"id": "casa_chegada", "pos": [2, 28], "falante": {"nome": "Narrador", "emoji": "🏛️"},
         "texto": "Homens armados vigiam os jardins da mansão, e a porta da frente não vai se abrir para vocês. "
                  "Vai ser preciso limpar o terreno e achar outra entrada.",
         "trigger": {"tipo": "proximidade", "raio": 4}},
        {"id": "casa_entrada", "pos": [d["exit"]["x"], d["exit"]["y"]], "falante": {"nome": "Narrador", "emoji": "🚪"},
         "texto": "Nos fundos da mansão, escondida da estrada, uma porta de serviço leva para dentro.",
         "trigger": {"tipo": "proximidade", "raio": 2}},
    ] + outras
    d["objectives"] = {
        "primary": obj("reach_exit", 220, 80), "secondary": [],
        "steps": [
            {"id": "casa_guardas", "condition": {"type": "kill_all"},
             "text": {"pt": "Derrote todos os guardas do terreno", "en": "Defeat all the guards on the grounds"}},
            {"id": "casa_entrada", "condition": {"type": "reach_exit"},
             "text": {"pt": "Encontre a entrada da mansão", "en": "Find the way into the mansion"}},
        ],
    }
    return d


def masmorra_leonel_1_alerta():
    """A mesma mansão com o Leonel avisado: uma dupla guarda a entrada e há uma armadilha a mais."""
    d = masmorra_leonel_1()
    d.update({"id": "elara_leonel_1_alerta", "name": "A Casa de Leilões (em alerta)"})
    d["monsters"] += [{"type": SOLDADO, "pos": [16, 7], "room_id": None, "boss": False, "target": False},
                      {"type": DUAL, "pos": [18, 7], "room_id": None, "boss": False, "target": False}]
    d["traps"] = d["traps"] + [{"tipo": "rede", "pos": [17, 9]}]
    d["falas"] = d["falas"] + [
        {"id": "casa_alerta", "pos": [8, 27], "falante": {"nome": "Narrador", "emoji": "⚠️"},
         "texto": "Os guardas estão postados em pares, olhando as entradas. Alguém avisou que viriam.",
         "trigger": {"tipo": "proximidade", "raio": 4}}]
    return d


def masmorra_leonel_2():
    """Interior da mansão, feito à mão pelo autor no `elara_leonel_2.json`; aqui só entram falas e objetivo.

    Vestíbulo, corredor da escada, cozinha e escritório; atrás da estante do canto fica o salão do leilão
    clandestino e, passando as guilhotinas que o sino desliga, a cela da Elara. A missão só acaba com o Leonel
    caído e a Elara na saída; se ela morrer, o `alternativo` encerra pela morte do Leonel."""
    d = copy.deepcopy(S.carregar_dungeon("elara_leonel_2.json"))
    d["falas"] = [
        {"id": "mansao_chegada", "pos": [2, 4], "falante": {"nome": "Narrador", "emoji": "🏛️"},
         "texto": "Botas correm pelo vestíbulo: os guardas da casa já ouviram a porta.",
         "trigger": {"tipo": "proximidade", "raio": 4}},
        {"id": "mansao_estante", "pos": [24, 7], "falante": {"nome": "Narrador", "emoji": "🕯️"},
         "texto": "O assoalho está gasto até a estante do canto, junto da parede das armaduras, e as velas pendem "
                  "para ela: há ar passando por trás dos livros.",
         "trigger": {"tipo": "proximidade", "raio": 3}},
        {"id": "mansao_passagem", "pos": [29, 7], "falante": {"nome": "Narrador", "emoji": "⛓️"},
         "texto": "Atrás da parede está o verdadeiro salão de leilões: sofás virados para um palco, celas de "
                  "exposição e o Leonel à espera, sem pressa nenhuma.",
         "trigger": {"tipo": "proximidade", "raio": 2}},
        {"id": "salao_corda", "pos": [42, 15], "falante": {"nome": "Narrador", "emoji": "🔔"},
         "texto": "Riscos frescos marcam o piso do corredor, e uma corda corre pelo teto até o sino do palco.",
         "trigger": {"tipo": "proximidade", "raio": 2}},
        {"id": "mansao_elara", "pos": [45, 30], "falante": {"nome": "Elara", "emoji": "🙏"},
         "texto": "Eu sabia que viriam! Não deixem que ele me leve de novo... o homem que paga disse que alguém "
                  "ainda mais forte espera a pedra.",
         "trigger": {"tipo": "proximidade", "raio": 3}},
    ]
    principal = obj("rescue_prisoner", 300, 150, fato=F_LEONEL)
    principal["fatos"] = [F_ELARA]
    principal["se_falhar"] = {"renome": 0, "fato": F_ELARA_MORTA}
    d["objectives"] = {
        "primary": principal,
        "alternativo": obj("kill_target", 150, 150, fato=F_LEONEL),
        "secondary": [obj("open_key_chest", 100, 0)],
        "steps": [
            {"id": "mansao_leonel", "condition": {"type": "kill_target"},
             "text": {"pt": "Derrote o Leonel", "en": "Defeat Leonel"}},
            {"id": "mansao_elara", "condition": {"type": "rescue_prisoner"},
             "text": {"pt": "Leve a Elara até a saída", "en": "Lead Elara to the exit"}},
        ],
    }
    return d


ARQUIVOS = {
    "elara_graciero_beco.json": masmorra_beco, "elara_graciero_cais.json": masmorra_cais,
    "elara_graciero_praca_viva.json": masmorra_praca_viva, "elara_graciero_praca_pedra.json": masmorra_praca_pedra,
    "elara_graciero_praca_morta.json": masmorra_praca_morta,
    "elara_leonel_1.json": masmorra_leonel_1, "elara_leonel_1_alerta.json": masmorra_leonel_1_alerta,
    "elara_leonel_2.json": masmorra_leonel_2}
