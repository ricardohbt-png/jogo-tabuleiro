"""Gerador da loja "Raízes do Brejo" e da cena da Zumbra (Vila dos Charcos).

Roda da raiz do projeto:
    python tools/gerar_zumbra_charcos.py            # grava os dados
    python tools/gerar_zumbra_charcos.py --simular  # só relata o que gravaria

Só toca no que é dele: a lista `mercador` da Vila dos Charcos em city_shops.json, o ponto
`raizes_do_brejo` de city_map_points.json e a cena `raizes_do_brejo` de city_scenes.json.
Numa cena que já existe, só reescreve as conversas `zumbra_*` e deixa tudo o mais (retrato,
posição, falas que o autor acrescentou pelo editor) como está.

ARTE PROVISÓRIA: fundo e retrato são reaproveitados de assets/tavern/ até o autor subir a
arte da Zumbra pelo editor (aba Cenas e NPCs): troque `background` e `image`.
"""
import argparse
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
import server as S  # noqa: E402

CIDADE = "vila_dos_charcos"
CENA_ID = "raizes_do_brejo"
PONTO_ID = "raizes_do_brejo"
NPC_ID = "npc_zumbra"
TITULO = "Raízes do Brejo"
# Cabana isolada na borda oeste da ilustração (assets/city/vila_charcos.png).
POSICAO = (23.1, 33.7)
FUNDO_PROVISORIO = "assets/tavern/taverna_charco.png"
RETRATO_PROVISORIO = "assets/tavern/homem_misterioso.png"

FATO_GANCHO = "charcos_criancas_sumidas"
FATO_MORTE = "charcos_criancas_mortas"
FATO_FERRAO = "charcos_ferrao_morto"
AVENTURA_TRAVESSIA = "charcos_travessia"


def estoque():
    """Grimórios, iscas de ilusão, poções mágicas (pergaminhos vêm do estoque rotativo)."""
    fonte = [i["id"] for i in S.SHOP_MERCHANT]
    grimorios = [i for i in fonte if i.startswith("grimorio_")]
    iscas = [i for i in ("ignus_fatus", "fata_morgana") if i in fonte]
    pocoes = [i for i in S.POCOES_TAMBEM_NO_MERCADOR if i in fonte]
    return grimorios + iscas + pocoes


def _req(**campos):
    return S._clean_requirement(campos)


def _conversa(cid, texto, requisito=None, fato="", renome=0, item_id="", uma_vez=True):
    return {"id": cid, "texto": texto, "requisito": requisito or {},
            "efeito": {"renome": renome, "fato": fato, "item_id": item_id}, "uma_vez": uma_vez}


def conversas():
    return [
        _conversa(
            "zumbra_chegada",
            "Então a vila não mandou ninguém. Vocês vieram por conta própria, e vieram até a minha "
            "porta. Isso diz alguma coisa. Olhem o que quiserem, mas não toquem no que não pagaram: "
            "as raízes daqui aprenderam a cobrar.",
            _req(sem_fato=FATO_MORTE), fato="zumbra_conhecida"),
        _conversa(
            "zumbra_criancas",
            "As crianças. Eu senti quando sumiram: o brejo ficou quieto demais, e ele só silencia "
            "assim quando alguém o paga. Procurem onde a água é velha. E quando chegarem aos "
            "encapuzados, lembrem: o que prende uma criança nunca é só ferro. Onde há um sino, "
            "alguém o toca. Onde há uma corrente, alguém a solta. Se puderem escolher, deixem a "
            "corrente em paz.",
            _req(fato=FATO_GANCHO, sem_fato=FATO_MORTE), fato="zumbra_avisou"),
        _conversa(
            "zumbra_ferrao",
            "Pisaram na Travessia e ainda respiram. Então sabem que o pior espera na aldeia: um "
            "ferrão do tamanho de uma lança, preso por quem não o controla. Ele odeia fogo e não "
            "aprende com a dor, só com o medo. Eu não vendo coragem, mas vendo luzes que enganam. "
            "Uma isca bem posta faz até aquele bicho olhar para o lado errado.",
            _req(aventura_id=AVENTURA_TRAVESSIA, sem_fato=FATO_MORTE)),
        _conversa(
            "zumbra_ferrao_morto",
            "Então o ferrão caiu, e vocês continuam inteiros. Eu sempre soube que alguém faria "
            "isso. Só não sabia que alguém teria o estômago. Fico em dívida. Levem isto: não é "
            "presente, é pagamento adiantado pelo que ainda virá.",
            _req(fato=FATO_FERRAO, sem_fato=FATO_MORTE), fato="zumbra_confia", renome=1,
            item_id="pocao_barreira_arcana"),
        _conversa(
            "zumbra_confia",
            "Voltem quando o brejo estiver quieto. Há coisas debaixo da água que ainda não "
            "terminaram de acordar, e quando eu souber o que são, vocês serão os primeiros a "
            "ouvir. Até lá, fiquem com o que as raízes podem dar.",
            _req(fato="zumbra_confia", sem_fato=FATO_MORTE), uma_vez=False),
        _conversa(
            "zumbra_luto",
            "Não me peçam consolo. O brejo cobra caro de quem promete e não cumpre, e hoje a "
            "conta chegou para vocês. A vila vai virar as costas, eu sei. Eu nunca esperei nada "
            "de ninguém. Se precisam de alguma coisa, os preços subiram para todos, e não fui eu "
            "quem decidiu.",
            _req(fato=FATO_MORTE), uma_vez=False),
        _conversa(
            "zumbra_rumor",
            "Todo encanto custa alguma coisa. Às vezes é ouro. Às vezes é uma pergunta que você "
            "não vai querer responder.",
            _req(sem_fato=FATO_MORTE), uma_vez=False),
    ]


def ponto():
    return {"x": POSICAO[0], "y": POSICAO[1], "type": "mercador", "name": TITULO,
            "titulo_loja": TITULO, "emoji": "🌿", "scene": CENA_ID,
            "oculto_ate_liberar": False, "ocultar_apos_concluir": False}


def cena_nova():
    return {"nome": "Zumbra", "background": FUNDO_PROVISORIO, "art_ratio": 1.5, "mode": "individual",
            "mask": "",
            "slots": [{"id": NPC_ID, "name": "Zumbra", "image": RETRATO_PROVISORIO,
                       "x": 35.0, "y": 30.3, "w": 30.0, "h": 69.7, "z": 1.0, "dialog": "",
                       "conversations": conversas()}]}


def _ler(caminho, padrao):
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return padrao


def _gravar(caminho, dados):
    tmp = caminho + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    os.replace(tmp, caminho)


def aplicar(simular=False, caminhos=None):
    c = dict({"shops": S.CITY_SHOPS_FILE, "pontos": S.CITY_MAP_POINTS_FILE, "cenas": S.CITY_SCENES_FILE},
             **(caminhos or {}))
    lojas = _ler(c["shops"], {})
    lojas.setdefault(CIDADE, {})["mercador"] = estoque()

    pontos = _ler(c["pontos"], {})
    pontos.setdefault(CIDADE, {})[PONTO_ID] = ponto()

    cenas = _ler(c["cenas"], {})
    da_cidade = cenas.setdefault(CIDADE, {})
    cena = da_cidade.get(CENA_ID)
    if not cena:
        da_cidade[CENA_ID] = cena_nova()
    else:
        slot = next((s for s in cena.get("slots", []) if s.get("id") == NPC_ID), None)
        if slot is None:
            cena.setdefault("slots", []).append(cena_nova()["slots"][0])
        else:
            manter = [cv for cv in slot.get("conversations", []) if not str(cv.get("id", "")).startswith("zumbra_")]
            slot["conversations"] = conversas() + manter
    if simular:
        print(f"estoque ({len(lojas[CIDADE]['mercador'])} itens): {lojas[CIDADE]['mercador']}")
        print(f"ponto {PONTO_ID}: {pontos[CIDADE][PONTO_ID]}")
        print(f"conversas: {[cv['id'] for cv in da_cidade[CENA_ID]['slots'][0]['conversations']]}")
        return
    _gravar(c["shops"], lojas)
    _gravar(c["pontos"], pontos)
    _gravar(c["cenas"], cenas)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--simular", action="store_true")
    args = ap.parse_args(argv)
    aplicar(simular=args.simular)
    print("pronto." if not args.simular else "(simulação: nada foi gravado)")


if __name__ == "__main__":
    main()
