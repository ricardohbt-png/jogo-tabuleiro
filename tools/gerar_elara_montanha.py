"""Gerador da rota opcional do Olho de "O Resgate de Elara" (as montanhas acima de Graciero).

Roda da raiz do projeto:
    python tools/gerar_elara_montanha.py            # grava
    python tools/gerar_elara_montanha.py --simular  # só relata
    python tools/gerar_elara_montanha.py --forcar   # regrava mapa editado à mão

Spec: docs/superpowers/specs/2026-10-21-campanha-resgate-de-elara-design.md
Plano: docs/superpowers/plans/2026-10-22-campanha-elara-parte5-olho.md

Só toca no que é dele: o destino `elara_montanha`, as fichas do assassino e do bardo da caravana e os três mapas
`elara_montanha_*` (protegidos por assinatura: mapa editado depois de gerado só é regravado com --forcar). A
conversa-dica do Elfo Suspeito de Graciero mora em `gerar_elara_graciero.py`.
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
import elara_montanha_fichas as F  # noqa: E402
from gerar_campanha_sombras import assinatura, Conflito  # noqa: E402

CIDADE = "graciero"
ASSINATURAS = os.path.join(RAIZ, "tools", ".elara_montanha_assinaturas.json")

F_DICA_MONTANHA = "elara_dica_montanha"
F_RAMO_A = "elara_ramo_a"
F_LEONEL_VENCIDO = "elara_leonel_vencido"
F_BARDO_AJUDOU = "elara_bardo_ajudou"
F_ASSASSINO_FUGIU = "elara_assassino_fugiu"


def _req(**campos):
    return S._clean_requirement(campos)


SLIDES_FINAIS = [
    ("A caravana está cercada, os guardas caídos ou em fuga. No fundo da última carroça, o baú de ferro cede: "
     "dentro dele, o Olho de Arveluz, pesado e quente, como se ainda soubesse o próprio nome.", {}),
    ("Antes de descer, vocês cobrem o guia com uma pilha de pedras. Sem ele, ninguém teria achado o desfiladeiro "
     "a tempo.", {"fato": F_BARDO_AJUDOU}),
    ("Vocês subiram sozinhos, guiados por riscos de faca nas pedras. Descem sozinhos, mais cansados do que "
     "da última vez que olharam para trás.", {"sem_fato": F_BARDO_AJUDOU}),
    ("Do assassino, restou uma moeda de prata sem cunho no chão. Alguém que sabia o caminho de volta "
     "desapareceu pela serra.", {"fato": F_ASSASSINO_FUGIU}),
    ("Resta descer a Graciero, onde a cidade ainda espera e o Leonel não sabe o que subiu atrás dele.", {}),
]


def outro_rota():
    slides = []
    for texto, cond in SLIDES_FINAIS:
        slide = {"text": texto}
        if cond:
            slide["requisito"] = _req(**cond)
        slides.append(slide)
    return {"slides": slides}


def destinos():
    base = S.WORLD_LOCATIONS[CIDADE]
    x, y = round(base["x"], 2), round(max(0, base["y"] - 6.0), 2)
    return {"elara_montanha": {
        "id": "elara_montanha", "nome": "As Montanhas de Graciero", "x": x, "y": y, "fome": 2, "sede": 2,
        "dungeons": [{"file": "elara_montanha_1.json", "encadear": True, "intro": "", "outro": ""},
                     {"file": "elara_montanha_2.json", "encadear": True, "intro": "", "outro": ""},
                     {"file": "elara_montanha_3.json", "encadear": False, "intro": "", "outro": ""}],
        "espera_retorno": {"modo": "fixa", "rodadas": 0, "dados": ""},
        "oculto_ate_liberar": True, "revisitavel": False, "ocultar_apos_concluir": True,
        "outro_rota": outro_rota(),
        "requisito": _req(fato=F_DICA_MONTANHA, tambem_fato=F_RAMO_A, sem_fato=F_LEONEL_VENCIDO),
        "renome_recompensa": 2}}


def mapas():
    import elara_montanha_mapas as M
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
    """Põe as fichas no catálogo vivo (para os mapas validarem) e, se `gravar`, no arquivo do editor. O Olho vem de
    `gerar_elara_graciero.py`: aqui só se confere que ele existe."""
    for fn in (F.ficha_assassino, F.ficha_bardo_agente):
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
    import gerar_elara_graciero as GG
    if "olho_de_arveluz" not in S._DUNGEON_ITEM_CATALOG:
        GG.garantir_registros(gravar)


def aplicar(simular=False, forcar=False, caminhos=None):
    c = dict({"adventures": S.WORLD_ADVENTURES_FILE, "dungeons_dir": S.DUNGEONS_DIR,
              "assinaturas": ASSINATURAS}, **(caminhos or {}))
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

    aventuras = _ler(c["adventures"], {})
    for did, dest in destinos().items():
        anterior = aventuras.get(did) or {}
        if "x" in anterior and "y" in anterior:      # a posição no mapa-múndi é do autor
            dest["x"], dest["y"] = anterior["x"], anterior["y"]
        aventuras[did] = dest
    if simular:
        print(f"destinos: {list(destinos())}")
        print(f"mapas: {list(mm)}")
        return
    os.makedirs(c["dungeons_dir"], exist_ok=True)
    for arq, defn in mm.items():
        _gravar(os.path.join(c["dungeons_dir"], arq), defn)
        assin[arq] = assinatura(defn)
    _gravar(c["assinaturas"], assin)
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
