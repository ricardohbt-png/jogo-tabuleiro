"""Gerador da Parte 1 de "O Resgate de Elara" (Alva e Luz).

Roda da raiz do projeto:
    python tools/gerar_campanha_elara.py            # grava
    python tools/gerar_campanha_elara.py --simular  # só relata

Spec: docs/superpowers/specs/2026-10-21-campanha-resgate-de-elara-design.md
Plano: docs/superpowers/plans/2026-10-21-campanha-elara-parte1-motor.md

Só toca no que é dele: a cena `templo_alva` e o `scene` do ponto `templo` de Alva e Luz, o destino
`elara_parte1` e, SÓ nos dois mapas do autor (`casa_secreta.json`, `fazenda.json`), os campos
`relogio` e `fato` do objetivo principal (aditivo e idempotente; recusa reescrever um arquivo cuja
formatação não é a do editor). Nunca regrava o desenho dos mapas.

ARTE: fundo panorâmico do pátio do Templo e personagem Exequiel de corpo inteiro, ambos em
`assets/cenas/`.
"""
import argparse
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (RAIZ, os.path.join(RAIZ, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import server as S  # noqa: E402

CIDADE = "alva_e_luz"
CENA_ID = "templo_alva"
PONTO_ID = "templo"
NPC_ID = "npc_exequiel"
AVENTURA = "elara_parte1"
AVENTURA_FAZENDA = "elara_fazenda"   # 2º destino: a fazenda, liberada pela carta achada na casa
RELOGIO_ID = "elara_p1"
FUNDO_PROVISORIO = "assets/cenas/fundos/templo_alva_patio.png"
IMAGEM_EXEQUIEL = "assets/cenas/personagens/exequiel_corpo_inteiro.png"

# Fatos da campanha (nomes estáveis: os planos seguintes dependem deles)
F_PEDIU = "elara_pediu"                    # o Templo deu a missão
F_CASA = "elara_casa_vencida"
F_CARTA = "elara_carta_fazenda"            # a carta do baú da casa (gravada pelo objetivo da casa)
F_FAZENDA = "elara_fazenda_vencida"
F_LENTO = "elara_lento"                    # o relógio passou do limite (ausente = rápido)
F_PRESSIONOU = "elara_templo_pressionou"   # o grupo ouviu o Exequiel depois da fazenda
F_RAMO_A = "elara_ramo_a"                  # seguir as moças
F_RAMO_B = "elara_ramo_b"                  # seguir o Gilo

MAPAS = {"casa_secreta.json": F_CASA, "fazenda.json": F_FAZENDA}


def _req(**campos):
    return S._clean_requirement(campos)


def _conversa(cid, texto, requisito=None, fato="", uma_vez=True):
    return {"id": cid, "texto": texto, "requisito": requisito or _req(),
            "efeito": {"renome": 0, "fato": fato, "item_id": ""}, "uma_vez": uma_vez}


def conversas_templo():
    """Conversas do Exequiel. Texto autoral em português; nada dos nomes por trás da rede."""
    return [
        _conversa(
            "elara_pedido",
            "Servas do Templo foram levadas esta noite, mais de uma dezena, entre elas Elara, irmã "
            "do mago Pedro. Os sequestradores usaram uma casa aqui em Alva e Luz, dizem os vizinhos. "
            "Tragam-nas de volta e o Templo paga bem. Rápido: cada hora conta.",
            _req(sem_fato=F_PEDIU), fato=F_PEDIU),
        _conversa(
            "elara_pedro_irma",
            "Pedro, a Elara falou de você ontem mesmo. Disse que o irmão ainda ia ficar famoso. "
            "Encontre-a, e diga-lhe isso pessoalmente.",
            _req(fato=F_PEDIU, heroi_no_grupo="mage")),
        _conversa(
            "elara_henrique_pilheria",
            "Bardo, deixe a graça para depois que as moças estiverem a salvo. E sim, a irmã do mago "
            "é mais bonita do que ele. Não digo mais nada.",
            _req(fato=F_PEDIU, heroi_no_grupo="bard")),
        _conversa(
            "elara_pos_fazenda_rapido",
            "Vocês voltaram depressa, e isso pode fazer toda a diferença. A fazenda era uma "
            "distração: as moças seguem pela estrada e, ao mesmo tempo, alguém esteve aqui no "
            "Templo esta noite e levou uma relíquia. Não posso dizer o que ela é. Com rapidez ainda "
            "podem tentar as duas coisas.",
            _req(fato=F_FAZENDA, sem_fato=F_LENTO), fato=F_PRESSIONOU),
        _conversa(
            "elara_pos_fazenda_lento",
            "Demoraram, e isso custou caro. A fazenda era uma distração: as moças seguem pela "
            "estrada e a relíquia que guardávamos foi roubada esta noite. Não posso dizer o que ela "
            "é, só que não pode ficar em mãos erradas. Já não há tempo para as duas coisas: escolham.",
            # aventura_id = a fazenda concluída: o relógio pode passar do limite
            # durante a fazenda, e o Templo só fala depois dela.
            _req(fato=F_LENTO, aventura_id=AVENTURA_FAZENDA), fato=F_PRESSIONOU),
        _conversa(
            "elara_escolher_mocas",
            "Vamos atrás das moças: a estrada leva à Vila do Riacho.",
            _req(fato=F_PRESSIONOU, sem_fato=F_RAMO_B), fato=F_RAMO_A),
        _conversa(
            "elara_escolher_gilo",
            "Vamos atrás do ladrão da relíquia: ele fugiu rumo à Floresta de Adhadal.",
            _req(fato=F_PRESSIONOU, sem_fato=F_RAMO_A), fato=F_RAMO_B),
    ]


def cena_templo():
    return {"nome": "Templo de Alva e Luz", "background": FUNDO_PROVISORIO, "art_ratio": 1.5,
            "mode": "individual", "mask": "",
            "slots": [{"id": NPC_ID, "name": "Exequiel", "image": IMAGEM_EXEQUIEL,
                       "x": 35.0, "y": 30.3, "w": 30.0, "h": 69.7, "z": 1.0, "dialog": "",
                       "conversations": conversas_templo()}]}


PONTO_CASA = "elara_casa"
PONTO_FAZENDA = "elara_fazenda"
PONTO_REFUGIO = "ponto_1"   # a Fazenda do Leste (Refúgio dos Heróis): só aparece depois da missão da fazenda


def ponto_casa():
    """Entrada da casa no mapa de Alva e Luz: a casa fica na cidade, sem estrada nem emboscada."""
    return {"x": 62.3, "y": 65.72, "type": "dungeon", "name": "A Casa da Viela", "emoji": "🏚️",
            "aventura": AVENTURA, "oculto_ate_liberar": False, "ocultar_apos_concluir": True}


def ponto_fazenda(refugio):
    """Entrada da fazenda no mapa de Alva e Luz, no lugar do Refúgio (que só surge depois)."""
    return {"x": refugio["x"], "y": refugio["y"], "type": "dungeon", "name": "Fazenda do Leste",
            "emoji": "🌾", "aventura": AVENTURA_FAZENDA, "oculto_ate_liberar": False,
            "ocultar_apos_concluir": True}


def destinos():
    base = S.WORLD_LOCATIONS[CIDADE]
    x, y = round(min(100, base["x"] + 5), 2), round(min(100, base["y"] + 3), 2)
    return {AVENTURA: {
        "id": AVENTURA, "nome": "O Resgate de Elara", "x": x, "y": y, "fome": 1, "sede": 1,
        "dungeons": [
            {"file": "casa_secreta.json", "encadear": False,
             "intro": "A casa fica numa viela de Alva e Luz. As janelas estão fechadas e o ar cheira "
                      "a poeira e a algo pior.",
             "outro": "A carta traz o endereço de uma fazenda a leste da cidade. Há um lugar novo no mapa."},
        ],
        "espera_retorno": {"modo": "fixa", "rodadas": 0, "dados": ""},
        "oculto_ate_liberar": True, "revisitavel": False, "ocultar_apos_concluir": True,
        "so_na_cidade": True,
        "outro_rota": "", "requisito": _req(fato=F_PEDIU), "renome_recompensa": 1},
        AVENTURA_FAZENDA: {
            "id": AVENTURA_FAZENDA, "nome": "A Fazenda do Leste", "x": min(100, x + 2), "y": y,
            "fome": 1, "sede": 1,
            "dungeons": [
                {"file": "fazenda.json", "encadear": False, "intro": "",
                 "outro": "Estábulos vazios, rastros de carroça e camas feitas às pressas. Quem quer que "
                          "estivesse ali já cumpriu a sua parte. Voltem ao Templo."},
            ],
            "espera_retorno": {"modo": "fixa", "rodadas": 0, "dados": ""},
            "oculto_ate_liberar": True, "revisitavel": False, "ocultar_apos_concluir": True,
            "so_na_cidade": True,
            "outro_rota": "", "requisito": _req(fato=F_CARTA), "renome_recompensa": 1}}


def relogio_padrao():
    """Relógio generoso: a casa e a fazenda somadas raramente passam de ~40 rodadas."""
    return {"id": RELOGIO_ID, "limite": 60, "fato_ao_passar": F_LENTO,
            "avisos": [
                {"em": 25, "texto": "O sino do Templo ecoa ao longe. A patrulha da estrada já saiu."},
                {"em": 45, "texto": "A noite avança. As moças devem estar cada vez mais longe."},
                {"em": 60, "texto": "O tempo está quase esgotado."}]}


# ─── Gravação ────────────────────────────────────────────────────────────────
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


def ajustar_mapa(caminho, fato):
    """Acrescenta `relogio` e o `fato` do objetivo principal ao mapa do autor. Devolve
    "ok" (gravou), "ja" (já estava) ou "recusado:<motivo>" (arquivo não reconhecido)."""
    try:
        with open(caminho, "r", encoding="utf-8", newline="") as f:
            cru = f.read()
    except OSError:
        return "recusado:arquivo ausente"
    crlf = "\r\n" in cru
    try:
        d = json.loads(cru)
    except ValueError:
        return "recusado:JSON ilegível"
    canonico = json.dumps(d, ensure_ascii=False, indent=2)
    if (canonico.replace("\n", "\r\n") if crlf else canonico) != cru:
        return "recusado:formatação diferente da do editor (não vou reescrever)"
    novo = dict(d)
    primario = dict((novo.get("objectives") or {}).get("primary") or {})
    if novo.get("relogio") == relogio_padrao() and primario.get("fato") == fato:
        return "ja"
    novo["relogio"] = relogio_padrao()
    primario["fato"] = fato
    obj = dict(novo.get("objectives") or {})
    obj["primary"] = primario
    novo["objectives"] = obj
    ok, msg = S.validar_dungeon(novo)
    if not ok:
        return f"recusado:invalidaria o mapa ({msg})"
    saida = json.dumps(novo, ensure_ascii=False, indent=2)
    if crlf:
        saida = saida.replace("\n", "\r\n")
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        f.write(saida)
    return "ok"


def aplicar(simular=False, caminhos=None):
    c = dict({"pontos": S.CITY_MAP_POINTS_FILE, "cenas": S.CITY_SCENES_FILE,
              "adventures": S.WORLD_ADVENTURES_FILE, "dungeons_dir": S.DUNGEONS_DIR},
             **(caminhos or {}))
    pontos = _ler(c["pontos"], {})
    ponto = pontos.get(CIDADE, {}).get(PONTO_ID)
    if ponto is None:
        raise ValueError(f"ponto {PONTO_ID!r} de {CIDADE} não existe em city_map_points.json")
    ponto["scene"] = CENA_ID
    pontos[CIDADE].setdefault(PONTO_CASA, ponto_casa())
    refugio = pontos[CIDADE].get(PONTO_REFUGIO)
    if refugio is not None:
        pontos[CIDADE].setdefault(PONTO_FAZENDA, ponto_fazenda(refugio))
        refugio["requisito"] = _req(fato=F_FAZENDA)     # o Refúgio é a recompensa da missão da fazenda
        refugio["oculto_ate_liberar"] = True

    cenas = _ler(c["cenas"], {})
    da_cidade = cenas.setdefault(CIDADE, {})
    cena = da_cidade.get(CENA_ID)
    if not cena:
        da_cidade[CENA_ID] = cena_templo()
    else:
        slot = next((s for s in cena.get("slots", []) if s.get("id") == NPC_ID), None)
        if slot is None:
            cena.setdefault("slots", []).append(cena_templo()["slots"][0])
        else:
            manter = [cv for cv in slot.get("conversations", []) if not str(cv.get("id", "")).startswith("elara_")]
            slot["conversations"] = conversas_templo() + manter

    aventuras = _ler(c["adventures"], {})
    anterior = aventuras.get(AVENTURA) or {}
    for aid, novo in destinos().items():
        antigo = aventuras.get(aid) or {}
        if "x" in antigo and "y" in antigo:        # a posição no mapa-múndi é do autor
            novo["x"], novo["y"] = antigo["x"], antigo["y"]
        aventuras[aid] = novo
    novo = destinos()[AVENTURA]

    resultado = {}
    for arquivo, fato in MAPAS.items():
        caminho = os.path.join(c["dungeons_dir"], arquivo)
        resultado[arquivo] = "(simulação)" if simular else ajustar_mapa(caminho, fato)
    if simular:
        print(f"conversas do Exequiel: {[cv['id'] for cv in conversas_templo()]}")
        print(f"destino {AVENTURA}: {[e['file'] for e in novo['dungeons']]}")
        return resultado
    _gravar(c["pontos"], pontos)
    _gravar(c["cenas"], cenas)
    _gravar(c["adventures"], aventuras)
    S._regen_dungeons_index()
    return resultado


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--simular", action="store_true")
    args = ap.parse_args(argv)
    for arquivo, res in aplicar(simular=args.simular).items():
        print(f"mapa {arquivo}: {res}")
    print("pronto." if not args.simular else "(simulação: nada foi gravado)")


if __name__ == "__main__":
    main()
