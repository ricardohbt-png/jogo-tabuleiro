"""Gerador de Graciero, o desfecho de "O Resgate de Elara".

Roda da raiz do projeto:
    python tools/gerar_elara_graciero.py            # grava
    python tools/gerar_elara_graciero.py --simular  # só relata
    python tools/gerar_elara_graciero.py --forcar   # regrava mapa editado à mão

Spec: docs/superpowers/specs/2026-10-21-campanha-resgate-de-elara-design.md
Plano: docs/superpowers/plans/2026-10-22-campanha-elara-parte4-graciero.md

Só toca no que é dele: as conversas `elara_*` dos slots ativos da taverna de Graciero (as conversas do
autor ficam), os destinos `elara_graciero_*`/`elara_leonel_*` do mapa-múndi, as fichas `escorpiao_gigante` e
`leonel`, o item `olho_de_arveluz` e os sete mapas (protegidos por assinatura: mapa editado depois de gerado
só é regravado com --forcar).
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
import elara_graciero_fichas as F  # noqa: E402
from gerar_campanha_sombras import assinatura, Conflito  # noqa: E402

CIDADE = "graciero"
CENA = "taverna"
ASSINATURAS = os.path.join(RAIZ, "tools", ".elara_graciero_assinaturas.json")

# Fatos (contrato com o plano 5: nomes estáveis)
F_RUMO = "elara_rumo_graciero"
F_RAMO_A = "elara_ramo_a"
F_RAMO_B = "elara_ramo_b"
F_MOCAS = "elara_mocas_salvas"
F_POUPADO = "elara_bardo_poupado"
F_GENTIL = "elara_bardo_gentil"
F_MALTRATADO = "elara_bardo_maltratado"
F_AJUDOU = "elara_bardo_ajudou"
F_TRAIU = "elara_bardo_traiu"
F_CAUTELOSO = "elara_leonel_cauteloso"
F_LENTO = "elara_graciero_lento"
F_GILO_MORREU = "elara_gilo_morreu"
F_DICA_MONTANHA = "elara_dica_montanha"
F_OLHO = "elara_olho_recuperado"
F_LEONEL_VENCIDO = "elara_leonel_vencido"
F_PEDRO = "elara_graciero_pedro_falou"
F_HENRIQUE = "elara_graciero_henrique_falou"


def _req(**campos):
    return S._clean_requirement(campos)


def _conversa(cid, texto, requisito, fato="", fatos=(), item_id="", uma_vez=False):
    efeito = {"renome": 0, "fato": fato, "item_id": item_id}
    if fatos:
        efeito["fatos"] = list(fatos)
    return {"id": cid, "texto": texto, "requisito": requisito, "efeito": efeito, "uma_vez": uma_vez}


def conversas():
    """{slot_id: [conversa]} da taverna de Graciero. Texto autoral; nada dos nomes por trás da rede."""
    rumo = _req(fato=F_RUMO)
    return {
        "barman": [
            _conversa("elara_gilo_pertences",
                      "Os guardas da cidade, ainda pálidos por causa dos escorpiões, entregam ao grupo o que "
                      "acharam entre os ossos do mercenário: um embrulho de pano que pesa mais do que devia. "
                      "Está quente ao toque.",
                      _req(fato=F_GILO_MORREU, sem_fato=F_RAMO_A), fato=F_OLHO, item_id=F.ID_OLHO, uma_vez=True),
        ],
        "npc_ms2ee41a": [
            _conversa("elara_graciero_garconete",
                      "Anda correndo que um senhor de casaca compra esposas pelo cais, e que as moças somem das "
                      "ruas na noite de sexta. Eu só trago a bebida.", rumo),
            _conversa("elara_graciero_bardo_ajuda",
                      "O bardo que vocês pouparam está encostado no balcão, de mão no instrumento. \"Não "
                      "esqueci. A caravana subiu a serra, rumo ao norte. Levem isto: é o que eu sei.\"",
                      _req(fato=F_POUPADO, tambem_fato=F_GENTIL, sem_fato=F_MALTRATADO),
                      fato=F_AJUDOU, fatos=[F_DICA_MONTANHA], uma_vez=True),
            _conversa("elara_graciero_bardo_traicao",
                      "Um assobio estridente corta a taverna. O bardo que vocês pouparam sorri de longe e some "
                      "pela porta dos fundos. Em pouco tempo, alguém na cidade já sabe que vocês chegaram.",
                      _req(fato=F_POUPADO, tambem_fato=F_MALTRATADO),
                      fato=F_TRAIU, fatos=[F_CAUTELOSO], uma_vez=True),
        ],
        "npc_ms2egify": [
            _conversa("elara_graciero_nobre",
                      "Um homem de casaca limpa fala sem olhar para vocês: \"Em Graciero, os respeitáveis "
                      "dormem tranquilos. Os que perguntam demais dormem menos.\"", rumo),
            _conversa("elara_graciero_henrique",
                      "O bardo do grupo faz uma mesura exagerada para a garçonete e cochicha, rindo, que a irmã "
                      "do mago \"deve ser tão feia quanto ele\". Alguém na mesa ao lado ouve e não gosta.",
                      _req(fato=F_RUMO, heroi_no_grupo="bard"), fato=F_HENRIQUE, uma_vez=True),
        ],
        "npc_ms2ej3o7": [
            _conversa("elara_graciero_gnomo",
                      "O gnomo balança as perninhas no banco alto: \"Nas docas se fala baixinho de uma casa de "
                      "leilões. Quem entra por lá nem sempre sai pela mesma porta.\"", rumo),
            _conversa("elara_graciero_pedro",
                      "O mago olha o fundo da caneca sem beber. \"Ela escreveu todo mês, até parar. Se tocaram "
                      "nela, vão todos pagar.\" Ninguém ri.",
                      _req(fato=F_RUMO, heroi_no_grupo="mage"), fato=F_PEDRO, uma_vez=True),
        ],
        "npc_ms2ef8oi": [
            _conversa("elara_graciero_elfo",
                      "O elfo desvia o olhar: \"Há quem pague bem para que as coisas sumam. E há quem, no norte, "
                      "pague melhor para que elas cheguem.\"", rumo),
            _conversa("elara_graciero_serra",
                      "O elfo fala sem mexer os lábios: \"Uma caravana subiu a serra com uma carga que ninguém "
                      "queria ver. Ainda dá tempo de alcançá-la, se não demorarem demais por aqui.\"",
                      _req(fato=F_DICA_MONTANHA, tambem_fato=F_RAMO_A, sem_fato=F_LEONEL_VENCIDO)),
        ],
    }


SLIDES_FINAIS = [
    ("A casa de leilões fica em silêncio quando o Leonel cai. Nos porões, a grade se abre e a Elara sai "
     "vendo a luz, magra e furiosa, mas viva.", {}),
    ("O mago atravessa o porão em três passos e abraça a irmã. Por um instante, nenhum dos dois consegue falar.",
     {"heroi_no_grupo": "mage"}),
    ("O bardo faz uma reverência elaborada diante da Elara e ouve dela, seca, que já ouviu a piada sobre ela "
     "e não achou graça.", {"heroi_no_grupo": "bard"}),
    ("As moças de Riacho já tinham voltado para casa. Aqui, outras jovens do Templo saem dos porões, uma a uma, "
     "sem acreditar que a luz do dia é para elas.", {"fato": "elara_mocas_salvas"}),
    ("Nos porões, outras servas do Templo esperavam, esquecidas. Voltam com vocês para Alva e Luz, "
     "agradecendo calada.", {"fato": F_RAMO_B}),
    ("O Olho de Arveluz volta ao Templo pesado e quente. O sacerdote o toma sem agradecer e o esconde "
     "debaixo do manto, olhando para longe.", {"item_id": F.ID_OLHO}),
    ("O Olho de Arveluz não está aqui. Ele sobe a serra, para o norte, numa caravana que não pede licença a "
     "ninguém.", {"item_id": F.ID_OLHO, "negar": True}),
    ("O bardo que vocês pouparam, de longe, ergue o chapéu uma última vez. Sem ele, a cidade teria sido "
     "bem mais difícil.", {"fato": F_AJUDOU}),
    ("O bardo que vocês pouparam também ergue o chapéu, mas para outro lado. Alguém soube cedo demais da "
     "chegada do grupo.", {"fato": F_TRAIU}),
    ("Fica no ar uma sensação ruim. O Gilo era pequeno demais para tudo isso. Alguma coisa muito maior, "
     "muito irritada, continua se movendo longe daqui.", {}),
]


def outro_rota():
    slides = []
    for texto, cond in SLIDES_FINAIS:
        slide = {"text": texto}
        cond = dict(cond)
        negar = cond.pop("negar", False)
        if cond:
            slide["requisito"] = _req(**cond)
            if negar:
                slide["negar"] = True
        slides.append(slide)
    return {"slides": slides}


def destinos():
    base = S.WORLD_LOCATIONS[CIDADE]

    def perto(dx, dy):
        return round(min(100, max(0, base["x"] + dx)), 2), round(min(100, max(0, base["y"] + dy)), 2)

    def destino(did, nome, dx, dy, etapas, requisito, renome, final=False):
        x, y = perto(dx, dy)
        return {"id": did, "nome": nome, "x": x, "y": y, "fome": 1, "sede": 1,
                "dungeons": [{"file": arq, "encadear": enc, "intro": "", "outro": ""} for arq, enc in etapas],
                "espera_retorno": {"modo": "fixa", "rodadas": 0, "dados": ""},
                "oculto_ate_liberar": True, "revisitavel": False, "ocultar_apos_concluir": True,
                "outro_rota": outro_rota() if final else "", "requisito": requisito, "renome_recompensa": renome}
    return {
        "elara_graciero_beco": destino("elara_graciero_beco", "Os Becos de Graciero", -2.0, 2.0,
                                       [("elara_graciero_beco.json", False)], _req(fato=F_RUMO), 1),
        "elara_graciero_cais": destino("elara_graciero_cais", "O Cais dos Leilões", 1.5, 2.5,
                                       [("elara_graciero_cais.json", False)],
                                       _req(aventura_id="elara_graciero_beco"), 1),
        "elara_graciero_praca_viva": destino("elara_graciero_praca_viva", "A Praça dos Escorpiões", 3.0, 0.5,
                                             [("elara_graciero_praca_viva.json", False)],
                                             _req(aventura_id="elara_graciero_cais", sem_fato=F_LENTO), 2),
        "elara_graciero_praca_morta": destino("elara_graciero_praca_morta", "A Praça dos Escorpiões", 3.0, 0.5,
                                              [("elara_graciero_praca_morta.json", False)],
                                              _req(aventura_id="elara_graciero_cais", fato=F_LENTO), 2),
        "elara_leonel_casa": destino("elara_leonel_casa", "A Casa de Leilões", 0.5, -2.5,
                                     [("elara_leonel_1.json", True), ("elara_leonel_2.json", False)],
                                     _req(fato=F_GILO_MORREU, sem_fato=F_CAUTELOSO), 3, final=True),
        "elara_leonel_casa_alerta": destino("elara_leonel_casa_alerta", "A Casa de Leilões", 0.5, -2.5,
                                            [("elara_leonel_1_alerta.json", True), ("elara_leonel_2.json", False)],
                                            _req(fato=F_GILO_MORREU, tambem_fato=F_CAUTELOSO), 3, final=True),
    }


def mapas():
    import elara_graciero_mapas as M
    return {arq: f() for arq, f in M.ARQUIVOS.items()}


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


def garantir_registros(gravar):
    """Põe fichas e Olho no catálogo vivo (para os mapas e as conversas validarem) e, se `gravar`, nos arquivos
    do editor (pelos mesmos caminhos dele)."""
    for fn in (F.ficha_escorpiao_gigante, F.ficha_leonel):
        ok, norm = S._validate_custom_monster(fn())
        if not ok:
            raise ValueError(f"ficha {fn.__name__} inválida: {norm}")
        if gravar:
            atual = next((m for m in S._read_custom_monsters() if m.get("type") == norm["type"]), None)
            if atual != norm:
                ok, msg = S._save_custom_monster(fn())
                if not ok:
                    raise ValueError(f"não foi possível gravar a ficha {norm['type']}: {msg}")
        if not any(m.get("type") == norm["type"] for m in S.MONSTER_DEFS):
            S.MONSTER_DEFS.append(dict(norm, _personalizado=True))
    ok, item = S._validate_custom_item(F.item_olho())
    if not ok:
        raise ValueError(f"item do Olho inválido: {item}")
    if gravar:
        atual = next((r for r in S._read_custom_items() if isinstance(r, dict) and r.get("id") == F.ID_OLHO), None)
        if atual != item:
            ok, msg = S._save_custom_item(F.item_olho())
            if not ok:
                raise ValueError(f"não foi possível gravar o Olho: {msg}")
    else:
        registros = [r for r in S._read_custom_items() if isinstance(r, dict) and r.get("id") != F.ID_OLHO]
        S._apply_custom_items(registros + [item])


def aplicar(simular=False, forcar=False, caminhos=None):
    c = dict({"cenas": S.CITY_SCENES_FILE, "adventures": S.WORLD_ADVENTURES_FILE,
              "dungeons_dir": S.DUNGEONS_DIR, "assinaturas": ASSINATURAS}, **(caminhos or {}))
    garantir_registros(gravar=not simular and caminhos is None)
    mm = mapas()
    for arq, defn in mm.items():
        ok, msg = S.validar_dungeon(defn)
        if not ok:
            raise ValueError(f"{arq}: {msg}")
    assin = _ler(c["assinaturas"], {})
    conflitos = []
    for arq in mm:
        caminho = os.path.join(c["dungeons_dir"], arq)
        if os.path.exists(caminho) and not forcar:
            atual = _ler(caminho, None)
            if atual is None or assin.get(arq) != assinatura(atual):
                conflitos.append(arq)
    if conflitos:
        raise Conflito("editados depois de gerados (use --forcar): " + ", ".join(conflitos))

    cenas = _ler(c["cenas"], {})
    slots = {s.get("id"): s for s in ((cenas.get(CIDADE) or {}).get(CENA) or {}).get("slots", []) if isinstance(s, dict)}
    faltam = [sid for sid in conversas() if sid not in slots or slots[sid].get("removed")]
    if faltam:
        raise ValueError(f"city_scenes.json: slots da taverna de Graciero ausentes ou removidos: {faltam}")
    for slot in slots.values():                       # limpa conversas elara_* de slots que já não recebem nenhuma
        if slot["id"] not in conversas():
            slot["conversations"] = [cv for cv in (slot.get("conversations") or [])
                                     if not str(cv.get("id", "")).startswith("elara_")]
    for sid, convs in conversas().items():
        slot = slots[sid]
        manter = [cv for cv in (slot.get("conversations") or []) if not str(cv.get("id", "")).startswith("elara_")]
        slot["conversations"] = manter + convs

    aventuras = _ler(c["adventures"], {})
    for did, dest in destinos().items():
        anterior = aventuras.get(did) or {}
        if "x" in anterior and "y" in anterior:      # a posição no mapa-múndi é do autor
            dest["x"], dest["y"] = anterior["x"], anterior["y"]
        aventuras[did] = dest
    if simular:
        print(f"conversas: {[cv['id'] for convs in conversas().values() for cv in convs]}")
        print(f"destinos: {list(destinos())}")
        print(f"mapas: {list(mm)}")
        return
    os.makedirs(c["dungeons_dir"], exist_ok=True)
    for arq, defn in mm.items():
        _gravar(os.path.join(c["dungeons_dir"], arq), defn)
        assin[arq] = assinatura(defn)
    _gravar(c["assinaturas"], assin)
    _gravar(c["cenas"], cenas)
    _gravar(c["adventures"], aventuras)
    S._regen_dungeons_index()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--simular", action="store_true")
    ap.add_argument("--forcar", action="store_true")
    args = ap.parse_args(argv)
    try:
        aplicar(simular=args.simular, forcar=args.forcar)
    except (Conflito, ValueError) as e:
        print(f"RECUSADO: {e}  (nada foi gravado)")
        return 2
    print("pronto." if not args.simular else "(simulação: nada foi gravado)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
