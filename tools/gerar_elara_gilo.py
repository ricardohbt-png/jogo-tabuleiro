"""Gerador do Ramo B de "O Resgate de Elara" (Floresta de Adhadal e Vila de Corvin).

Roda da raiz do projeto:
    python tools/gerar_elara_gilo.py            # grava
    python tools/gerar_elara_gilo.py --simular  # só relata
    python tools/gerar_elara_gilo.py --forcar   # regrava mapa editado à mão

Spec: docs/superpowers/specs/2026-10-21-campanha-resgate-de-elara-design.md
Plano: docs/superpowers/plans/2026-10-22-campanha-elara-parte3-gilo.md

Só toca no que é dele: as conversas `elara_*` dos slots ativos `barman`, `patrono_fundo`, `npc_ms2e74bw`
e `npc_ms2e85ew` da taverna de Corvin (as conversas do autor ficam), os destinos `elara_adhadal` e
`elara_corvin` do mapa-múndi, a ficha `gilo_dedos_sujos` e os quatro mapas `elara_adhadal_*`/
`elara_corvin_*` (protegidos por assinatura: mapa editado depois de gerado só é regravado com --forcar).
Os protótipos do autor (`floresta.json`, `floresta_2.json`) nunca são alterados.
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
import elara_gilo_ficha as G  # noqa: E402
from gerar_campanha_sombras import assinatura, Conflito  # noqa: E402

CIDADE = "vila_corvin"
CENA = "taverna"
ASSINATURAS = os.path.join(RAIZ, "tools", ".elara_gilo_assinaturas.json")

# Fatos (contrato com o plano 4: nomes estáveis)
F_RAMO_B = "elara_ramo_b"
F_CHEGADA = "elara_corvin_chegada"
F_PISTA = "elara_pista_graciero"       # grava o objetivo do confronto com o Gilo
F_RUMO_GRACIERO = "elara_rumo_graciero"   # contrato com o plano 4: o grupo decidiu seguir para Graciero


def _req(**campos):
    return S._clean_requirement(campos)


def _conversa(cid, texto, requisito, fato="", fatos=(), uma_vez=False):
    efeito = {"renome": 0, "fato": fato, "item_id": ""}
    if fatos:
        efeito["fatos"] = list(fatos)
    return {"id": cid, "texto": texto, "requisito": requisito, "efeito": efeito, "uma_vez": uma_vez}


def conversas():
    """{slot_id: [conversa]} da taverna de Corvin. Texto autoral; nada dos nomes por trás da rede."""
    ramo = _req(fato=F_RAMO_B)
    return {
        "barman": [
            _conversa("elara_corvin_barman",
                      "Um sujeito de botas fundas de lama passou por aqui duas noites atrás. Pagou caro por um "
                      "quarto que não usou e saiu antes do galo. Perguntou pela estrada de Graciero.",
                      ramo, fato=F_CHEGADA, uma_vez=True),
            _conversa("elara_corvin_rumo_graciero",
                      "A carta do curtume não deixa dúvida: o Gilo foi vender a pedra e as encomendas em "
                      "Graciero. Vocês pagam a conta e partem na mesma noite, atrás da fumaça.",
                      _req(fato=F_PISTA), fato=F_RUMO_GRACIERO, uma_vez=True),
        ],
        "npc_ms2e74bw": [
            _conversa("elara_corvin_garconete",
                      "Ele tinha os dedos pretos de tinta e de lama, e uma pedra embrulhada num pano que não "
                      "largava nem para comer. Não era dali, mas conhecia o caminho do curtume.", ramo),
        ],
        "patrono_fundo": [
            _conversa("elara_corvin_bardo",
                      "O bardo dedilha uma melodia estridente e finge não ouvir a pergunta. \"Não vi ninguém. "
                      "Ninguém passa por aqui que valha uma canção.\" Mas a música muda de tom quando vocês "
                      "se afastam.", ramo),
        ],
        "npc_ms2e85ew": [
            _conversa("elara_corvin_sombrio",
                      "O homem sombrio não levanta os olhos da caneca. \"Quem procura o Gilo chega tarde "
                      "ou não chega. Ele nunca está sozinho, mesmo quando parece.\"", ramo),
        ],
    }


def destinos():
    a, c = S.WORLD_LOCATIONS["alva_e_luz"], S.WORLD_LOCATIONS[CIDADE]
    meio = (round((a["x"] + c["x"]) / 2, 2), round((a["y"] + c["y"]) / 2, 2))
    perto = (round(min(100, c["x"] + 2.5), 2), round(min(100, c["y"] + 2.5), 2))

    def destino(did, nome, xy, etapas, fome_sede, requisito, renome):
        return {"id": did, "nome": nome, "x": xy[0], "y": xy[1], "fome": fome_sede, "sede": fome_sede,
                "dungeons": [{"file": arq, "encadear": enc, "intro": "", "outro": ""} for arq, enc in etapas],
                "espera_retorno": {"modo": "fixa", "rodadas": 0, "dados": ""},
                "oculto_ate_liberar": True, "revisitavel": False, "ocultar_apos_concluir": True,
                "outro_rota": "", "requisito": requisito, "renome_recompensa": renome}
    return {
        "elara_adhadal": destino("elara_adhadal", "A Floresta de Adhadal", meio,
                                 [("elara_adhadal_1.json", True), ("elara_adhadal_2.json", False)], 2,
                                 _req(fato=F_RAMO_B), 1),
        "elara_corvin": destino("elara_corvin", "O Curtume de Corvin", perto,
                                [("elara_corvin_cacada.json", True), ("elara_corvin_gilo.json", False)], 1,
                                _req(aventura_id="elara_adhadal"), 2),
    }


def mapas():
    import elara_gilo_mapas as M
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


def garantir_ficha(gravar):
    """Põe o Gilo no catálogo vivo (para os mapas validarem) e, se `gravar`, no arquivo do editor."""
    ok, norm = S._validate_custom_monster(G.ficha_gilo())
    if not ok:
        raise ValueError(f"ficha do Gilo inválida: {norm}")
    if gravar:
        atual = next((m for m in S._read_custom_monsters() if m.get("type") == G.TIPO_GILO), None)
        if atual != norm:
            ok, msg = S._save_custom_monster(G.ficha_gilo())
            if not ok:
                raise ValueError(f"não foi possível gravar a ficha do Gilo: {msg}")
    if not any(m.get("type") == G.TIPO_GILO for m in S.MONSTER_DEFS):
        S.MONSTER_DEFS.append(dict(norm, _personalizado=True))


def aplicar(simular=False, forcar=False, caminhos=None):
    c = dict({"cenas": S.CITY_SCENES_FILE, "adventures": S.WORLD_ADVENTURES_FILE,
              "dungeons_dir": S.DUNGEONS_DIR, "assinaturas": ASSINATURAS}, **(caminhos or {}))
    garantir_ficha(gravar=not simular and caminhos is None)
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
        raise ValueError(f"city_scenes.json: slots da taverna de Corvin ausentes ou removidos: {faltam}")
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
