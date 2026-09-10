# -*- coding: utf-8 -*-
r"""
Guarda de regressao do custo por quadro do 3D da masmorra.

CAUSA RAIZ (medida em 2026-08-25, mapa 44x40 "resgate de elara"):
cada familia de realce por casa criava um mesh para TODA casa de chao ao
entrar na masmorra -- 17 familias mais o fogo persistente (21 objetos por
casa) = 37.586 nos na cena, dos quais so ~140 ficavam visiveis. O renderer
percorre a arvore inteira a cada quadro, entao o custo aparecia mesmo sem
nada desenhado:

    37.586 nos -> render() 8,20 ms/quadro (2 draw calls, 24 triangulos)
    19.064 nos -> render() 4,78 ms/quadro   (sem o fogo por casa)
     3.910 nos -> render() 1,13 ms/quadro   (sem overlay pre-criado)

Congelar matrixAutoUpdate nos 37.585 objetos NAO mudou nada (7,05 -> 6,89 ms):
o custo e a TRAVESSIA da arvore, nao a conta de matriz. Por isso a correcao
tem de reduzir a QUANTIDADE de nos -- criar o mesh da casa so quando ela
precisa aparecer.

Roda da raiz:  python tools/test_overlays_3d.py
"""
import io
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.join(RAIZ, "game.js")

# Familias que cobrem uma casa por vez e passam quase todo o tempo invisiveis.
FAMILIAS = [
    "moveHighlightMeshes", "atkHighlightMeshes", "weaponRangeMeshes",
    "masterAttackRangeMeshes", "masterAttackZoneMeshes", "masterFootprintMeshes",
    "masterHistoryAttackerMeshes", "masterHistoryTargetMeshes",
    "spellRangeMeshes", "spellZonaMeshes", "spellDoubleMeshes", "spellAreaMeshes",
    "spellEscuridaoMeshes", "spellSilencioMeshes", "spellFireFx",
    "spellLivingFlameFx",
]

PASS = 0
FAIL = 0


def check(nome, cond, detalhe=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print("  [ok] " + nome)
    else:
        FAIL += 1
        print("  [FALHA] " + nome + ((" -- " + detalhe) if detalhe else ""))


src = io.open(GAME, encoding="utf-8").read()

print("[1] helpers do pool preguicoso existem")
check("_mkOverlayPool definido", "function _mkOverlayPool(" in src)
check("_overlayAt definido", "function _overlayAt(" in src)
check("_overlayShowOnly definido", "function _overlayShowOnly(" in src)

# Uma familia pode nascer direto de _mkOverlayPool ou de um atalho local
# (ex.: _mkSpell) -- desde que esse atalho devolva um _mkOverlayPool.
FABRICAS = {"_mkOverlayPool"}
for m in re.finditer(r"const\s+(_mk\w+)\s*=\s*\([^)]*\)\s*=>\s*_mkOverlayPool\(", src):
    FABRICAS.add(m.group(1))


def preguicosa(nome, texto=None):
    txt = src if texto is None else texto
    # aceita "nome = _mkX(" (const) e "nome: _mkX(" (dentro de objeto)
    m = re.search(r"\b" + re.escape(nome) + r"\s*[:=]\s*(_mk\w+)\s*\(", txt)
    return m is not None and m.group(1) in FABRICAS


print("[2] cada familia por casa nasce de fabrica preguicosa")
print("     fabricas reconhecidas: " + ", ".join(sorted(FABRICAS)))
for fam in FAMILIAS:
    check(fam + " e preguicosa", preguicosa(fam))

print("[3] spellTargetMeshes (self/ally/enemy) tambem e preguicoso")
m = re.search(r"spellTargetMeshes\s*=\s*\{(.*?)\n  \};", src, re.S)
corpo = m.group(1) if m else ""
check("os 3 lados usam fabrica preguicosa",
      bool(corpo) and all(preguicosa(l, corpo) for l in ("self", "ally", "enemy")),
      "corpo lido: %r" % corpo[:120])

print("[4] nenhuma familia volta a ser pre-criada varrendo o grid")
for fam in FAMILIAS:
    eager = re.search(r"\b" + re.escape(fam) + r"\[`\$\{fx\},\$\{fy\}`\]\s*=", src)
    check(fam + " sem gravacao por varredura do grid", eager is None)
check("sem 'spellFireFx[key] = { group:' no laco de construcao",
      re.search(r"spellFireFx\[key\]\s*=\s*\{\s*group:", src) is None)

print("[5] os consumidores usam o pool em vez de varrer o dicionario")
# O padrao antigo dependia de a casa JA existir no dicionario.
for fam in FAMILIAS:
    velho = re.search(
        r"for\s*\(\s*const\s*\[\s*key\s*,\s*\w+\s*\]\s*of\s*Object\.entries\(g3\."
        + re.escape(fam) + r"\)", src)
    check(fam + " sem 'for...of Object.entries' de visibilidade", velho is None)

print("[6] a animacao do fogo tolera entrada nula (casa inelegivel)")
check("_animarFogoPersistente3D checa fx antes de usar",
      re.search(r"for\(const fx of Object\.values\(g3\.spellFireFx\)\)\{\s*\n"
                r"(\s*//[^\n]*\n)*\s*if\(!fx \|\|", src) is not None)
check("chamas vivas persistentes usam o GLB da decoração",
      "spellLivingFlameFx" in src and "DECOR_GLB_TYPES.chama_viva" in src
      and "new T.AnimationMixer(inst)" in src
      and "_animarChamasVivasPersistentes3D" in src)

print("")
print("PASS=%d FAIL=%d" % (PASS, FAIL))
sys.exit(1 if FAIL else 0)
