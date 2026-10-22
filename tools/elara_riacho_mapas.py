"""Mapas do Ramo A de "O Resgate de Elara" (Vila do Riacho), usados por `gerar_elara_riacho.py`.

Tudo é determinístico (semente fixa por mapa). Calibração: grupo esperado de 4 heróis nível 2.
O monstro `bandido` está sendo criado em outra frente: troque `TIPO_BANDIDO` aqui quando ele existir.
"""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (RAIZ, os.path.join(RAIZ, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import server as S  # noqa: E402
from charcos_mapas import Cena, montar_fila, obj  # noqa: E402

TIPO_BANDIDO = "goblin_combatente"     # bandido comum
TIPO_CAPANGA = "soldado"               # capanga mais forte
TIPO_ARQUEIRO = "goblin_arqueiro"

F_BARDO_EXPOSTO = "elara_bardo_exposto"
F_MOCAS = "elara_mocas_salvas"

CARTA = {"id": "carta", "texto": (
    "Duas linhas num papel dobrado: \"Fica quieto, Tomé. O bardo da taverna avisa quem vem de "
    "fora, você só abre a porta. A paga do mês segue na mesma gaveta.\"")}


def masmorra_casa():
    """A casa do morador comprado: sala da frente, quarto e porão com o baú-chave."""
    c, xs, hs = montar_fila([10, 10, 10], 13, "casa", 2201, piso="madeira_escura", parede="madeira")
    m = c.m
    ent, sai = m.em(0, 1, hs // 2), m.em(2, 8, hs // 2)
    c.proteger(ent, sai)
    # 0 · Sala da frente
    c.mon(TIPO_BANDIDO, 0, 7, 2); c.mon(TIPO_BANDIDO, 0, 7, 6)
    c.deco("mesa_cadeiras", 0, 4, 3); c.espalha("barril", 0, 2); c.espalha("estante", 0, 1)
    c.armadilhas.append({"tipo": "armadilha_urso", "pos": m.em(0, 5, 1)})
    # 1 · Quarto
    c.mon(TIPO_CAPANGA, 1, 7, 3); c.mon(TIPO_ARQUEIRO, 1, 7, 6)
    c.deco("cama_casal", 1, 2, 2); c.espalha("estante", 1, 1); c.espalha("barril", 1, 1)
    c.armadilhas.append({"tipo": "armadilha_dardos_envenenados", "pos": m.em(1, 4, 5), "veneno_id": "veneno_escorpiao_pedra"})
    # 2 · Porão
    c.mon(TIPO_BANDIDO, 2, 6, 3, alvo=False); c.mon(TIPO_ARQUEIRO, 2, 6, 6)
    c.espalha("barril", 2, 3); c.espalha("estante_armas", 2, 1)
    c.armadilhas.append({"tipo": "rede", "pos": m.em(2, 4, 4)})
    c.bau(m.em(2, 8, 3), 25, [CARTA])
    d = c.baus[-1]
    d["key_objective"] = True
    c.fala("casa_aviso", m.em(0, 1, 2), "Narrador", "🏚️",
           "A casa do Tomé tem a janela fechada à luz do dia. Alguém dentro abafa passos.", 4)
    c.fala("casa_porao", m.em(1, 8, hs // 2), "Narrador", "🕯️",
           "Uma tampa no chão deixa subir um cheiro de mofo. Lá embaixo, uma gaveta trancada.", 3)
    return c.finalizar("elara_riacho_casa", "A Casa do Tomé", "masmorra", 2, {
        "primary": obj("open_key_chest", 120, 40, fato=F_BARDO_EXPOSTO), "secondary": []}, ent, sai,
        expected_party={"heroes": 4, "level": 2})


def masmorra_celeiro():
    """O celeiro: pátio, curral, celeiro (as moças) e palheiro."""
    c, xs, hs = montar_fila([12, 11, 12, 10], 16, "celeiro", 2202, piso="terra", parede="parede_terra")
    m = c.m
    ent, sai = m.em(0, 1, hs // 2), m.em(3, 8, hs // 2)
    c.proteger(ent, sai)
    # 0 · Pátio
    c.mon(TIPO_BANDIDO, 0, 9, 2); c.mon(TIPO_BANDIDO, 0, 9, 7)
    c.espalha("cerca_reta", 0, 3); c.espalha("barril", 0, 2); c.deco("carroca", 0, 4, 4)
    c.armadilhas.append({"tipo": "armadilha_urso", "pos": m.em(0, 6, 1)})
    # 1 · Curral
    c.mon(TIPO_CAPANGA, 1, 8, 3); c.mon(TIPO_ARQUEIRO, 1, 8, 7)
    c.espalha("monte_feno", 1, 3); c.espalha("cerca_reta", 1, 3)
    c.armadilhas.append({"tipo": "rede", "pos": m.em(1, 5, 5)})
    # 2 · Celeiro (as moças ficam no fundo)
    chefe = c.mon(TIPO_CAPANGA, 2, 4, 4, alvo=True)
    c.mon(TIPO_BANDIDO, 2, 4, 7); c.mon(TIPO_BANDIDO, 2, 7, 5)
    c.espalha("monte_feno", 2, 4); c.espalha("barril", 2, 2)
    c.armadilhas.append({"tipo": "armadilha_dardos_envenenados", "pos": m.em(2, 3, 3), "veneno_id": "veneno_escorpiao_pedra"})
    refens = m.em(2, 10, 4)
    c.proteger(refens)
    # 3 · Palheiro (saída)
    c.espalha("monte_feno", 3, 3); c.espalha("barril", 3, 1)
    c.bau(m.em(3, 6, 3), 40, [{"id": "carta", "texto": (
        "\"As moças ficam até o fim da semana. A do Templo, a irmã do mago, já seguiu viagem para "
        "Graciero: não a procurem aqui.\"")}])
    c.fala("celeiro_chegada", m.em(0, 1, 3), "Narrador", "🌾",
           "O celeiro fica atrás do curral. Há mais gente nele do que o gado explica.", 4)
    c.fala("celeiro_mocas", m.em(2, 9, 4), "Moça", "👧",
           "Moço! Moça! Aqui! Levaram a nossa irmã de Templo ontem, rumo a Graciero!", 3)
    d = c.finalizar("elara_riacho_celeiro", "O Celeiro", "ar_livre", 2, {
        "primary": obj("rescue_prisoner", 180, 80, fato=F_MOCAS),
        "secondary": [obj("kill_target", 120, 40)]}, ent, sai,
        expected_party={"heroes": 4, "level": 2}, marcador_entrada="poste")
    d["prisoner"] = {"pos": refens, "room_id": 2}
    return d
