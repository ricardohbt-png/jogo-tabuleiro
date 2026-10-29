"""Mapas do Ramo A de "O Resgate de Elara" (Vila do Riacho), usados por `gerar_elara_riacho.py`.

Tudo é determinístico (semente fixa por mapa). Calibração: grupo esperado de 4 heróis nível 2.
O monstro `bandido` já existe: `TIPO_BANDIDO` o usa na casa; o celeiro é do autor (editado à mão).
"""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (RAIZ, os.path.join(RAIZ, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import server as S  # noqa: E402
from charcos_mapas import Cena, montar_fila, obj  # noqa: E402
from gerar_campanha_sombras import Mapa  # noqa: E402

TIPO_BANDIDO = "bandido"               # bandido comum (monstro nativo ND 1)
TIPO_CAPANGA = "soldado"               # capanga mais forte
TIPO_ARQUEIRO = "goblin_arqueiro"
TIPO_VALENTAO = "goblin_dual"           # o mais perigoso dos subordinados (ND 1)
TIPO_OGRO = "ogro_clava"               # a força contratada (ND 2)

F_BARDO_EXPOSTO = "elara_bardo_exposto"
F_MOCAS = "elara_mocas_salvas"

CARTA = {"id": "carta", "texto": (
    "Duas linhas num papel dobrado: \"Fica quieto, Tomé. O bardo da taverna avisa quem vem de "
    "fora, você só abre a porta. A paga do mês segue na mesma gaveta.\"")}


def masmorra_casa():
    """A casa do Tomé: sala da frente, quarto e o porão escondido atrás de uma estante-mecanismo.

    Tomé (o morador comprado) espera no porão com o baú-chave e os capangas; o ogro é a força que a
    rede paga. Calibração para 4 heróis nível 2 (poder 8): ND 3,0 / 4,0 / 6,0 por sala."""
    m = Mapa(36, 14)
    m.sala(0, 1, 2, 10, 10, role="entrance", locked=False)     # sala da frente
    m.sala(1, 12, 2, 10, 10)                                   # quarto
    m.sala(2, 23, 2, 12, 10, locked=False)                     # porão (secreto: só se liga pela estante)
    m.porta(11, 6, 0, 1)
    c = Cena("casa", m, 2201, piso="madeira_escura", parede="madeira")
    hs = 10
    ent, sai = m.em(0, 1, hs // 2), m.em(2, 10, 5)
    c.proteger(ent, sai)
    c.proteger((11, 6), (10, 6), (12, 6))
    c.pintar(2, "terra")
    # 0 · Sala da frente: lareira, mesa, cobertura baixa; os primeiros capangas já estão de olho
    c.mon(TIPO_BANDIDO, 0, 7, 2); c.mon(TIPO_BANDIDO, 0, 7, 7)
    c.mon(TIPO_CAPANGA, 0, 5, 4)
    c.deco("lareira", 0, 4, 0); c.deco("mesa_cadeiras", 0, 3, 5)
    c.deco("barril", 0, 9, 0); c.deco("barril", 0, 9, 9); c.deco("barril", 0, 0, 9)
    c.deco("estante", 0, 7, 0)
    c.armadilhas.append({"tipo": "armadilha_urso", "pos": m.em(0, 5, 2)})
    c.armadilhas.append({"tipo": "lamina_escondida", "pos": m.em(0, 8, 5)})
    # 1 · Quarto: cama, estantes e a estante-mecanismo que esconde a descida
    c.mon(TIPO_BANDIDO, 1, 6, 2); c.mon(TIPO_BANDIDO, 1, 6, 7); c.mon(TIPO_BANDIDO, 1, 3, 5)
    c.mon(TIPO_CAPANGA, 1, 7, 5)
    c.deco("cama_casal", 1, 1, 0); c.deco("cama", 1, 4, 8)
    c.deco("estante", 1, 3, 0); c.deco("barril", 1, 0, 9); c.deco("barril", 1, 1, 9)
    # SEM key_objective: acionar a estante só abre a passagem; o objetivo é abrir o baú do porão
    c.deco("estante_livros", 1, 9, 2, did="casa_estante")
    c.armadilhas.append({"tipo": "armadilha_dardos_envenenados", "pos": m.em(1, 4, 4), "veneno_id": "veneno_escorpiao_pedra"})
    c.armadilhas.append({"tipo": "rede", "pos": m.em(1, 5, 6)})
    # 2 · Porão: Tomé, o capanga grande e o baú-chave
    tome = c.mon(TIPO_BANDIDO, 2, 9, 4, alvo=True)
    c.mon(TIPO_OGRO, 2, 6, 5)
    c.mon(TIPO_BANDIDO, 2, 6, 2); c.mon(TIPO_BANDIDO, 2, 6, 8)
    c.mon(TIPO_CAPANGA, 2, 4, 5)
    c.deco("barril", 2, 11, 0); c.deco("barril", 2, 11, 1); c.deco("barril_cerveja", 2, 11, 9)
    c.deco("barril_cerveja", 2, 10, 9); c.deco("estante_armas", 2, 4, 0); c.deco("estante", 2, 8, 0)
    c.deco("mesa_quimica", 2, 2, 8)
    c.armadilhas.append({"tipo": "rede", "pos": m.em(2, 2, 3)})
    c.armadilhas.append({"tipo": "armadilha_urso", "pos": m.em(2, 8, 6)})
    c.bau(m.em(2, 10, 3), 25, [CARTA])
    c.baus[-1]["key_objective"] = True
    c.fala("casa_aviso", m.em(0, 1, 2), "Narrador", "🏚️",
           "A casa do Tomé tem a janela fechada à luz do dia. Alguém dentro abafa passos.", 4)
    c.fala("casa_estante", m.em(1, 8, 4), "Narrador", "🕯️",
           "Marcas de arrasto no assoalho vão até a estante do canto. Atrás dela sopra um ar frio, de porão.", 3)
    c.fala("casa_tome", m.em(2, 3, 5), "Tomé", "🧔",
           "Eu só abria a porta! Foi o bardo da taverna que mandou! Eles me pagam, eu não pergunto...", 4)
    # A estante abre duas casas da parede entre o quarto e o porão
    d = c.finalizar("elara_riacho_casa", "A Casa do Tomé", "masmorra", 2, {
        "primary": obj("open_key_chest", 120, 40, fato=F_BARDO_EXPOSTO),
        "secondary": [obj("kill_target", 90, 20)]}, ent, sai,
        expected_party={"heroes": 4, "level": 2})
    d["secret_passages"] = [{"id": f"casa_passagem_{i}", "type": "mechanism", "pos": [22, y],
                             "key_decor_ids": ["casa_estante"], "keys_mode": "any"}
                            for i, y in enumerate((6, 7))]
    return d


def masmorra_celeiro():
    """O celeiro: pátio, curral, celeiro (as moças) e palheiro."""
    c, xs, hs = montar_fila([12, 11, 12, 10], 16, "celeiro", 2202, piso="terra", parede="parede_terra")
    m = c.m
    ent, sai = m.em(0, 1, hs // 2), m.em(3, 8, hs // 2)
    c.proteger(ent, sai)
    # 0 · Pátio
    c.mon(TIPO_BANDIDO, 0, 9, 2); c.mon(TIPO_BANDIDO, 0, 9, 7)
    c.mon_livre(TIPO_CAPANGA, 0, 2); c.mon_livre(TIPO_ARQUEIRO, 0, 1)
    c.espalha("cerca_reta", 0, 3); c.espalha("barril", 0, 2); c.deco("carroca", 0, 4, 4)
    c.armadilhas.append({"tipo": "armadilha_urso", "pos": m.em(0, 6, 1)})
    # 1 · Curral
    c.mon(TIPO_CAPANGA, 1, 8, 3); c.mon(TIPO_ARQUEIRO, 1, 8, 7)
    c.mon_livre(TIPO_VALENTAO, 1, 2); c.mon_livre(TIPO_CAPANGA, 1, 1)
    c.espalha("monte_feno", 1, 3); c.espalha("cerca_reta", 1, 3)
    c.armadilhas.append({"tipo": "rede", "pos": m.em(1, 5, 5)})
    # 2 · Celeiro (as moças ficam no fundo)
    chefe = c.mon(TIPO_CAPANGA, 2, 4, 4, alvo=True)
    c.mon(TIPO_BANDIDO, 2, 4, 7); c.mon(TIPO_BANDIDO, 2, 7, 5)
    c.mon_livre(TIPO_VALENTAO, 2, 2); c.mon_livre(TIPO_CAPANGA, 2, 2)
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
