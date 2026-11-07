"""Aplica as seis crianças dos Charcos ao que o autor já editou à mão (idempotente).

Roda da raiz do projeto:
    python -X utf8 tools/aplicar_charcos_seis_criancas.py            # grava
    python -X utf8 tools/aplicar_charcos_seis_criancas.py --simular  # só relata

O gerador (`gerar_campanha_charcos.py`) não regrava os mapas do autor, então a mudança da Aldeia
mora aqui. Só toca no combinado:
  * dungeons/charcos_4b_aldeia.json: `prisoner` -> `prisoners` (as seis crianças, no mesmo cercado),
    objetivo principal com destino, meta e faixas (sem `se_falhar`) e sem `alternativo`;
  * world_adventures.json: `charcos_mare` com `renome_recompensa` 0 e o final por faixa;
  * city_scenes.json: conversas `charcos_*` da taverna da Vila dos Charcos (gratidão por faixa e luto);
  * tools/.charcos_assinaturas.json (assinatura do mapa gerado) e tools/editor_dungeons.js.
Formatação e fim de linha dos arquivos são os de sempre (indent 2, sem alterar o resto).
"""
import argparse
import json
import os
import sys
from copy import deepcopy

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (RAIZ, os.path.join(RAIZ, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import server as S  # noqa: E402
import gerar_campanha_charcos as G  # noqa: E402
import charcos_mapas as M  # noqa: E402

ALDEIA = "charcos_4b_aldeia.json"
# Canto da sala 2 (x42, y12): o cercado. As crianças ocupam o mesmo miolo que o refém único ocupava.
SALA_X, SALA_Y = 42, 12


def _ler(caminho):
    with open(caminho, "rb") as f:
        return json.loads(f.read().decode("utf-8"))


def _gravar(caminho, dados, crlf=True):
    """Mesmo formato dos arquivos do projeto: indent 2, sem `\\u`, sem quebra no fim."""
    txt = json.dumps(dados, ensure_ascii=False, indent=2)
    if crlf:
        txt = txt.replace("\n", "\r\n")
    with open(caminho, "wb") as f:
        f.write(txt.encode("utf-8"))


def casas_livres(defn):
    """As seis casas do cercado, conferidas no mapa de verdade: chão livre de parede, decoração,
    monstro, baú e armadilha, e alcançáveis a partir da casa onde o refém único ficava."""
    casas = [[SALA_X + dx, SALA_Y + dy] for dx, dy in M.CASAS_CRIANCAS]
    cena = deepcopy(defn)
    cena.pop("prisoner", None); cena.pop("prisoners", None)
    r = S.GameRoom("CRIANCAS")

    async def _nada(*a, **k):
        pass
    r.gm_say = r.broadcast = r.send_to = r.push_state = _nada
    r.load_authored_dungeon(cena)
    ocupadas = {tuple(t) for d in r.decorations for t in r._decor_tiles(d)}
    ocupadas |= {tuple(m["pos"]) for m in r.monsters.values()}
    ocupadas |= {tuple(c["pos"]) for c in r.chests.values()}
    ocupadas |= {tuple(a["pos"]) for a in (defn.get("traps") or [])}
    ocupadas |= {tuple(d["pos"]) for d in (defn.get("decorations") or [])}
    for x, y in casas:
        if defn["tiles"][y][x] != S.FLOOR or r._blocks_tile(x, y) or (x, y) in ocupadas:
            raise ValueError(f"casa ({x},{y}) do cercado não está livre; escolha outras em CASAS_CRIANCAS")
    ref = tuple(defn["prisoner"]["pos"]) if isinstance(defn.get("prisoner"), dict) else tuple(casas[1])
    from collections import deque
    visto, fila = {ref}, deque([ref])
    while fila:
        x, y = fila.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n in visto or not (0 <= n[0] < r.map_w and 0 <= n[1] < r.map_h) or r._blocks_tile(*n):
                continue
            visto.add(n); fila.append(n)
    fora = [c for c in casas if tuple(c) not in visto]
    if fora:
        raise ValueError(f"casas {fora} não são alcançáveis a partir do cercado")
    return casas


def mapa_novo(atual):
    """A Aldeia gravada com as seis crianças. Só `prisoner`, o objetivo principal e `alternativo` mudam."""
    pronto = "prisoners" in atual and "prisoner" not in atual
    casas = [pr["pos"] for pr in atual["prisoners"]] if pronto else casas_livres(atual)
    novo = {}
    for k, v in atual.items():
        if k in ("prisoner", "prisoners"):
            novo["prisoners"] = M.criancas(casas)
        else:
            novo[k] = v
    if "prisoners" not in novo:
        novo["prisoners"] = M.criancas(casas)
    objetivos = deepcopy(atual["objectives"])
    objetivos["primary"] = M.objetivo_resgate_aldeia()
    objetivos.pop("alternativo", None)
    novo["objectives"] = objetivos
    ok, msg = S.validar_dungeon(novo)
    if not ok:
        raise ValueError(f"{ALDEIA} inválido: {msg}")
    return novo


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Seis crianças e final por faixa nos Charcos.")
    ap.add_argument("--simular", action="store_true", help="só relata, não grava")
    args = ap.parse_args(argv)
    c = G.caminhos_padrao()
    caminho_mapa = os.path.join(c["dungeons_dir"], ALDEIA)

    art = G.preparar(so_dados=True)           # valida destinos e conversas; registra o troféu em memória
    mudancas = []

    atual = _ler(caminho_mapa)
    novo = mapa_novo(atual)
    if novo != atual or list(novo) != list(atual):
        mudancas.append((caminho_mapa, novo, True))

    aventuras = _ler(c["adventures"])
    dest = G.destinos()[G.AVENTURA]
    antes = aventuras[G.AVENTURA]
    depois = dict(antes, renome_recompensa=dest["renome_recompensa"], outro_rota=dest["outro_rota"])
    if depois != antes:
        aventuras[G.AVENTURA] = depois
        mudancas.append((c["adventures"], aventuras, True))

    cenas = _ler(c["scenes"])
    slots = ((cenas.get(G.CIDADE) or {}).get("taverna") or {}).get("slots") or []
    por_id = {s.get("id"): s for s in slots if isinstance(s, dict)}
    faltam = [sid for sid in art["conversas"] if sid not in por_id]
    if faltam:
        raise ValueError(f"city_scenes.json: slots da taverna da Vila dos Charcos não encontrados: {faltam}")
    antes_cenas = deepcopy(cenas)
    G.mesclar_conversas(por_id, art["conversas"])
    if cenas != antes_cenas:
        mudancas.append((c["scenes"], cenas, True))

    assin = _ler(c["assinaturas"])
    gerada = G.assinatura(G.masmorras()[ALDEIA])
    if assin.get(ALDEIA) != gerada:
        assin[ALDEIA] = gerada
        mudancas.append((c["assinaturas"], assin, False))

    if not mudancas:
        print("nada a fazer: tudo já estava aplicado")
        return 0
    for caminho, _, _ in mudancas:
        print(("vai gravar " if args.simular else "gravando ") + os.path.relpath(caminho, RAIZ))
    if args.simular:
        return 0
    for caminho, dados, crlf in mudancas:
        _gravar(caminho, dados, crlf)
    S._regen_dungeons_index()
    print("OK: seis crianças, faixas, final e luto aplicados; editor_dungeons.js regenerado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
