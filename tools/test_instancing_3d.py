# -*- coding: utf-8 -*-
r"""
Guarda de regressao do custo do tabuleiro 3D conforme a masmorra e explorada.

CAUSA RAIZ (medida em 2026-08-25/26, mapa 44x40 "resgate de elara"):
cada casa e cada peca de decoracao era um mesh proprio na cena. Como um draw
call custa ~3 us de CPU, o quadro ficava proporcional ao QUANTO JA FOI
EXPLORADO -- era essa a "lentidao ao longo do jogo":

    inicio da fase (nevoa fechada):     186 draw calls ->  1,9 ms/quadro
    masmorra toda explorada:          3.582 draw calls -> 10,8 ms/quadro

Duas hipoteses testadas e DESCARTADAS: colapsar TODOS os materiais num so
economizava 1,5 ms de 10,8; congelar matrixAutoUpdate em 3.081 objetos nao
mudava nada. Tambem NAO e preenchimento: baixar a resolucao 16x nao mudou o
tempo. O que pesa e a QUANTIDADE de draw calls.

Correcao: tudo que e estatico e so ligado/desligado pela nevoa virou
InstancedMesh -- casas (1.760 em 30 combinacoes de geometria/material), brilho
de chao (882), detalhes de parede (439) e cenario (156). O mesh original
CONTINUA existindo fora da cena como "procuracao": e nele que o resto do codigo
escreve `visible` (nevoa) e `material` (passagem secreta), e e ele o alvo do
raycast do clique.

    depois: 395 draw calls -> 2,8 ms/quadro (3.959 -> 747 nos na cena)

Roda da raiz:  python tools/test_instancing_3d.py
"""
import io
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.join(RAIZ, "game.js")

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

print("[1] o tabuleiro e desenhado por InstancedMesh")
check("_rebuildTileInstances existe", "function _rebuildTileInstances(" in src)
check("_prepararTileProxy existe", "function _prepararTileProxy(" in src)
check("usa T.InstancedMesh", "new T.InstancedMesh(" in src)
check("o rebuild e chamado no renderMap3D", "_rebuildTileInstances();" in src)

print("[2] a casa NAO entra mais na cena (senao o draw call volta)")
check("sem 'scene.add(mesh)' antes de tileMeshes[key]",
      re.search(r"scene\.add\(mesh\);\s*\n\s*tileMeshes\[key\]\s*=", src) is None)
check("sem 'scene.add(eMesh)' para o entulho",
      re.search(r"scene\.add\(eMesh\);\s*\n\s*tileMeshes\[`entulho:", src) is None)
check("a casa passa por _prepararTileProxy", "_prepararTileProxy(mesh);" in src)
check("o entulho passa por _prepararTileProxy", "_prepararTileProxy(eMesh);" in src)

print("[3] a procuracao mantem matrixWorld (o raycast do clique depende dela)")
bloco = re.search(r"function _prepararTileProxy\(mesh\)\{(.*?)\n\}", src, re.S)
corpo = bloco.group(1) if bloco else ""
check("fixa matrixWorld a partir de matrix",
      "matrixWorld.copy(mesh.matrix)" in corpo, "corpo: %r" % corpo[:120])
check("desliga matrixAutoUpdate (a casa nunca se move)",
      "matrixAutoUpdate = false" in corpo)

print("[4] o rebuild so roda quando a nevoa/material muda")
check("existe a flag _tilesDirty", "_tilesDirty" in src)
check("o rebuild sai cedo quando nao ha mudanca",
      re.search(r"if\(!_tilesDirty\) return;", src) is not None)
check("a visibilidade da casa marca a flag",
      re.search(r"if\(mesh\.visible !== vis\)\{\s*mesh\.visible = vis;\s*_tilesDirty = true;", src) is not None)
check("a troca de material da passagem secreta marca a flag",
      re.search(r"mesh\.material = sm;\s*_tilesDirty = true;", src) is not None)

print("[5] o brilho de chao e uma InstancedMesh, nao 882 meshes")
check("wetFloorInst existe", "wetFloorInst" in src)
check("_atualizarWetFloor3D existe", "function _atualizarWetFloor3D(" in src)
check("nao restou wetFloorMeshes", "wetFloorMeshes" not in src)

print("[6] material de detalhe de parede e memoizado (nao 1 por mesh)")
mk = re.search(r"const mkSt = \(v\) => \{(.*?)\n  \};", src, re.S)
corpo_mk = mk.group(1) if mk else ""
check("mkSt consulta um cache", bool(corpo_mk) and "_stCache" in corpo_mk,
      "corpo: %r" % corpo_mk[:100])

print("[7] detalhes de parede e cenario tambem sao instanciados")
check("_rebuildDetailInstances existe", "function _rebuildDetailInstances(" in src)
check("existe a flag _detailDirty", "_detailDirty" in src)
check("varre as TRES familias (detalhe + cenario + estaticos de tocha)",
      "const familias = [g3.wallDetailMeshes, g3.sceneryMeshes, g3.torchStaticMeshes];" in src)
# As pedras do arco vivem em Group rotacionado: tem de usar a matriz de MUNDO.
check("usa matrixWorld nas instancias de detalhe",
      "inst.setMatrixAt(i, g.itens[i].matrixWorld)" in src)
check("o add() do buildWallDetails nao poe na cena",
      re.search(r"const add = \(key, mesh\) => \{[^}]*scene\.add\(mesh\);", src, re.S) is None)
check("o add() congela a matriz de mundo",
      re.search(r"const add = \(key, mesh\) => \{.*?mesh\.updateMatrixWorld\(true\);", src, re.S) is not None)
check("o barril nao entra na cena",
      re.search(r"grp\.visible = false;\s+scene\.add\(grp\);\s+if\(!sceneryMeshes", src) is None)
check("o barril congela a matriz de mundo",
      re.search(r"grp\.updateMatrixWorld\(true\);\s+if\(!sceneryMeshes", src) is not None)
check("o rebuild de detalhe e chamado UMA vez (depois das duas familias)",
      src.count("_rebuildDetailInstances();") == 1,
      "achei %d chamadas" % src.count("_rebuildDetailInstances();"))

print("[8] tochas: geometria/material compartilhados e estaticos instanciados")
check("suporte e tigela usam o ironMat compartilhado (sem clone)",
      "ironMat.clone()" not in src)
check("a tigela tem geometria unica (bowlGeo hoisted)",
      "const bowlGeo = new T.TorusGeometry(0.063, 0.025, 5, 12);" in src)
check("o suporte memoriza a geometria por direcao de parede",
      "brkGeoCache" in src)
check("os cones tem 3 geometrias, nao uma por chama",
      "const coneGeos = coneSpecs.map(" in src)
check("os estaticos da tocha entram no instanciador",
      "g3.torchStaticMeshes" in src
      and "const familias = [g3.wallDetailMeshes, g3.sceneryMeshes, g3.torchStaticMeshes];" in src)
# A cintilacao e por cone (emissiveIntensity e uniform de material): as chamas
# TEM de continuar com material proprio, senao todas piscam juntas.
check("cada chama mantem material proprio (cintilacao independente)",
      "new T.MeshStandardMaterial({" in src and "coneGeos[ci]," in src)
check("a ancora de luz da tocha usa coordenada de MUNDO",
      "lx: bx + fx, ly: by + 0.28, lz: bz + fz" in src,
      "era fx/fz (local, +-0,15): toda luz de tocha caia perto da origem do mapa")

print("[9] niveis de qualidade grafica (a alavanca para GPU fraca)")
check("PERF_PRESETS tem os 3 niveis",
      all(('%s:' % n) in src for n in ("alta", "media", "baixa")) and "PERF_PRESETS" in src)
check("_aplicarQualidade3D existe", "function _aplicarQualidade3D(" in src)
check("o nivel persiste no localStorage", "'lfh_perf'" in src)
# Tirar a luz da CENA e o que corta custo por fragmento; zerar intensidade nao.
check("as luzes extras saem da cena, nao so apagam",
      "slot.light.parent.remove(slot.light)" in src)
check("a sombra e desligada de verdade no nivel baixo",
      "g3.renderer.shadowMap.enabled = cfg.sombras" in src)
check("a resolucao do buffer acompanha o nivel",
      "setPixelRatio(Math.min(window.devicePixelRatio || 1, cfg.pixelRatio))" in src)
# Mudar a contagem de luzes obriga a refazer os programas.
check("os materiais sao marcados para recompilar", "m.needsUpdate = true" in src)
check(
      "a qualidade e aplicada ANTES do renderer.compile",
      re.search(r"_aplicarQualidade3D\(\);\s+try\{ renderer\.compile", src) is not None)
check("medidor de FPS conta dentro do laco 3D", "_fpsTick(now);" in src)
check("o medidor e recriado no boot quando estava ligado",
      "if(_fpsMostrar) _setFpsMostrar(true);" in src)

print("[10] InstancedMesh nao pode ser descartada pelo frustum")
# O bounding sai de UMA instancia na origem; sem frustumCulled=false o
# tabuleiro inteiro some quando a camera se afasta do centro.
check("as instancias desligam o frustumCulled",
      src.count("inst.frustumCulled = false") >= 2
      and "wetFloorInst.frustumCulled = false" in src)

print("[11] a arte da TELA DE SELECAO fica fora do otimizador de imagens")
otim = io.open(os.path.join(RAIZ, "tools", "otimizar_imagens.py"), encoding="utf-8").read()
check("assets/portraits nao esta na politica",
      not re.search(r'"assets/portraits":\s*\(', otim),
      "selecao_personagens.jpg e um sprite sheet de tela cheia; reduzi-lo borrou os 6 tiles")
mod = io.open(os.path.join(RAIZ, "tools", "otimizar_modelos3d.py"), encoding="utf-8").read()
check("os GLB de heroi (raiz de models3d) ficam fora",
      '"assets/models3d/monstros"' in mod and '"assets/models3d":' not in mod,
      "o heroi aparece em tela cheia no carrossel de selecao")

print("")
print("PASS=%d FAIL=%d" % (PASS, FAIL))
sys.exit(1 if FAIL else 0)
