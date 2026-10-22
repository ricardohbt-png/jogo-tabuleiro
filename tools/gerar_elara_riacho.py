"""Gerador do Ramo A de "O Resgate de Elara" (Vila do Riacho).

Roda da raiz do projeto:
    python tools/gerar_elara_riacho.py            # grava
    python tools/gerar_elara_riacho.py --simular  # só relata
    python tools/gerar_elara_riacho.py --forcar   # regrava mapa editado à mão

Spec: docs/superpowers/specs/2026-10-21-campanha-resgate-de-elara-design.md
Plano: docs/superpowers/plans/2026-10-21-campanha-elara-parte2-riacho.md

Só toca no que é dele: as conversas `elara_*` dos slots `barman`, `patrono_fundo` (mesa de amigos),
`npc_ms254rwd` (garçonete) e `cartas` (o bardo) da taverna da Vila do Riacho (as conversas do autor ficam), os destinos `elara_riacho_*` do
mapa-múndi e os dois mapas `elara_riacho_*.json` (protegidos por assinatura: um mapa editado
depois de gerado só é regravado com --forcar).
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
import elara_riacho_mapas as M  # noqa: E402
from gerar_campanha_sombras import assinatura, Conflito  # noqa: E402

CIDADE = "vila_riacho"
CENA = "taverna"
ASSINATURAS = os.path.join(RAIZ, "tools", ".elara_riacho_assinaturas.json")
ARQUIVOS = {"elara_riacho_casa.json": M.masmorra_casa, "elara_riacho_celeiro.json": M.masmorra_celeiro}

# Fatos (contrato com o plano 3: nomes estáveis)
F_RAMO_A = "elara_ramo_a"
F_T1_FEITO = "elara_t1_feito"
F_T1_GENTIL = "elara_t1_gentil"
F_T1_AMEACA = "elara_t1_ameaca"
F_T1_IGNOROU = "elara_t1_ignorou"
F_EXPOSTO = M.F_BARDO_EXPOSTO
F_DECIDIDO = "elara_bardo_decidido"
F_MORTO = "elara_bardo_morto"
F_INTERROGADO = "elara_bardo_interrogado"
F_POUPADO = "elara_bardo_poupado"
F_GENTIL = "elara_bardo_gentil"
F_MALTRATADO = "elara_bardo_maltratado"
F_FINAL = "elara_bardo_final"
F_VILA_ABALADA = "elara_vila_abalada"
F_LEONEL_CAUTELOSO = "elara_leonel_cauteloso"
F_MOCAS = M.F_MOCAS


def _req(**campos):
    return S._clean_requirement(campos)


def _conversa(cid, texto, requisito, fato="", fatos=(), uma_vez=False):
    efeito = {"renome": 0, "fato": fato, "item_id": ""}
    if fatos:
        efeito["fatos"] = list(fatos)
    return {"id": cid, "texto": texto, "requisito": requisito, "efeito": efeito, "uma_vez": uma_vez}


def conversas():
    """{slot_id: [conversa]} da taverna da Vila do Riacho. Texto autoral; nada dos nomes por trás da rede."""
    ramo = _req(fato=F_RAMO_A)
    return {
        "barman": [
            _conversa("elara_riacho_barman",
                      "Ninguém aqui viu nada, e é assim que a gente continua inteiro. Se querem saber de "
                      "forasteiros, falem com quem toca à noite: ele ouve tudo antes de qualquer um.", ramo),
            _conversa("elara_bardo_escoltar",
                      "Vocês levam o bardo para fora do povoado, pela estrada, sem que ninguém o toque. "
                      "Ele agradece com um aceno curto e não olha para trás.",
                      _req(fato=F_POUPADO, sem_fato=F_FINAL), fato=F_GENTIL, fatos=[F_FINAL], uma_vez=True),
            _conversa("elara_bardo_entregar",
                      "Vocês o entregam à vila. Arrastam-no até a praça sob gritos e pedras. Ele olha para "
                      "vocês como quem não esquece um rosto.",
                      _req(fato=F_POUPADO, sem_fato=F_FINAL), fato=F_MALTRATADO, fatos=[F_FINAL], uma_vez=True),
        ],
        "patrono_fundo": [
            _conversa("elara_riacho_mesa",
                      "O Tomé anda com a bolsa cheia desde a lua passada, e não faz serviço nenhum. Mora na "
                      "casa de janela fechada, no fim da rua. Eu não disse nada.", ramo),
        ],
        "npc_ms254rwd": [
            _conversa("elara_riacho_serva",
                      "Tem uns tropeiros no celeiro do Heitor desde ontem. Mas tropeiro não traz carroça tão "
                      "cheia, de noite, e com tanta gente calada dentro.",
                      _req(fato=F_EXPOSTO)),
        ],
        "cartas": [
            _conversa("elara_t1_gentil",
                      "Você paga uma caneca ao bardo e puxa conversa. Ele se esquiva das perguntas, mas "
                      "agradece o gesto com um sorriso que dura um segundo a mais.",
                      _req(fato=F_RAMO_A, sem_fato=F_T1_FEITO), fato=F_T1_GENTIL,
                      fatos=[F_T1_FEITO, F_GENTIL], uma_vez=True),
            _conversa("elara_t1_ameaca",
                      "Você o prende pelo colarinho e sussurra o que fará se ele mentir. Ele sorri sem os "
                      "olhos, e a melodia que toca muda de tom.",
                      _req(fato=F_RAMO_A, sem_fato=F_T1_FEITO), fato=F_T1_AMEACA,
                      fatos=[F_T1_FEITO, F_MALTRATADO], uma_vez=True),
            _conversa("elara_t1_ignorou",
                      "Você deixa o bardo tocar em paz. Ele parece aliviado... e atento a cada passo de "
                      "vocês até a porta.",
                      _req(fato=F_RAMO_A, sem_fato=F_T1_FEITO), fato=F_T1_IGNOROU,
                      fatos=[F_T1_FEITO], uma_vez=True),
            _conversa("elara_bardo_matar",
                      "Vocês o executam ali mesmo. O silêncio na taverna é de quem entendeu o recado, e "
                      "alguém, lá fora, vai ficar sabendo antes do amanhecer.",
                      _req(fato=F_EXPOSTO, sem_fato=F_DECIDIDO), fato=F_MORTO,
                      fatos=[F_DECIDIDO, F_LEONEL_CAUTELOSO], uma_vez=True),
            _conversa("elara_bardo_interrogar",
                      "Ele canta tudo, tremendo, diante da taverna inteira. A vila ouve cada nome e vira o "
                      "rosto para vocês: ninguém gosta de quem os expõe.",
                      _req(fato=F_EXPOSTO, sem_fato=F_DECIDIDO), fato=F_INTERROGADO,
                      fatos=[F_DECIDIDO, F_VILA_ABALADA], uma_vez=True),
            _conversa("elara_bardo_poupar",
                      "Vocês deixam o bardo vivo. Ele jura silêncio e escuta com atenção o que vocês "
                      "querem dele. O que acontecer depois dependerá do que fizerem com ele.",
                      _req(fato=F_EXPOSTO, sem_fato=F_DECIDIDO), fato=F_POUPADO,
                      fatos=[F_DECIDIDO], uma_vez=True),
        ],
    }


def destinos():
    base = S.WORLD_LOCATIONS[CIDADE]

    def perto(dx, dy):
        return round(min(100, base["x"] + dx), 2), round(min(100, base["y"] + dy), 2)

    def destino(did, nome, dx, dy, arquivo, requisito, renome):
        x, y = perto(dx, dy)
        return {"id": did, "nome": nome, "x": x, "y": y, "fome": 1, "sede": 1,
                "dungeons": [{"file": arquivo, "encadear": False, "intro": "", "outro": ""}],
                "espera_retorno": {"modo": "fixa", "rodadas": 0, "dados": ""},
                "oculto_ate_liberar": True, "revisitavel": False, "ocultar_apos_concluir": True,
                "outro_rota": "", "requisito": requisito, "renome_recompensa": renome}
    return {
        "elara_riacho_casa": destino("elara_riacho_casa", "A Casa do Tomé", 3, 3, "elara_riacho_casa.json",
                                     _req(fato=F_RAMO_A), 0),
        "elara_riacho_celeiro": destino("elara_riacho_celeiro", "O Celeiro do Heitor", 6, 4,
                                        "elara_riacho_celeiro.json", _req(fato=F_DECIDIDO), 1),
    }


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


def aplicar(simular=False, forcar=False, caminhos=None):
    c = dict({"cenas": S.CITY_SCENES_FILE, "adventures": S.WORLD_ADVENTURES_FILE,
              "dungeons_dir": S.DUNGEONS_DIR, "assinaturas": ASSINATURAS}, **(caminhos or {}))
    mapas = {arq: f() for arq, f in ARQUIVOS.items()}
    for arq, defn in mapas.items():
        ok, msg = S.validar_dungeon(defn)
        if not ok:
            raise ValueError(f"{arq}: {msg}")
    assin = _ler(c["assinaturas"], {})
    conflitos = []
    for arq in mapas:
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
        raise ValueError(f"city_scenes.json: slots da taverna do Riacho ausentes ou removidos: {faltam}")
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
        print(f"mapas: {list(mapas)}")
        return
    os.makedirs(c["dungeons_dir"], exist_ok=True)
    for arq, defn in mapas.items():
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
