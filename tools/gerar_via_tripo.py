#!/usr/bin/env python3
"""
Gera miniaturas 3D dos heróis via Tripo AI (imagem→3D generativo).
====================================================================
A IA do Tripo carrega o conhecimento de anatomia/proporções aprendido de
milhões de modelos 3D — gera a malha completa (com concavidades, laterais
corretas) e texturiza a partir das fotos. Substitui o casco de silhuetas.

Requer: TRIPO_API_KEY no ambiente (https://platform.tripo3d.ai → API Keys)

Uso:
    python gerar_via_tripo.py            # todos os personagens
    python gerar_via_tripo.py richard    # só um

Entrada (mesma de antes):
    assets/pawns/_fontes/<Personagem>/frente|costas|esquerda|direita.(png|jpeg)
    (fallback: ficha única <Personagem>.jpeg fatiada)
Saída:
    assets/models3d/<classe>.glb
"""

import asyncio
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from tripo3d import TripoClient

# Reusa o pré-processamento do pipeline anterior: rembg, medição/corte do
# pedestal, fatiamento de fichas e mapeamento personagem→classe.
import gerar_miniaturas_3d as G

BASE  = Path(r"C:\Users\RICARDO\Desktop\jogo tabuleiro")
SAIDA = BASE / "assets" / "models3d"
TMP   = BASE / "assets" / "pawns" / "_tripo_tmp"

# Ordem exigida pelo multiview_to_model: frente, costas, esquerda, direita
ORDEM_VISTAS = ['front', 'back', 'sideL', 'sideR']

MODEL_VERSION = 'v3.1-20260211'


def preparar_vista(frame: Image.Image, destino: Path):
    """Recorta a figura (rembg), remove o pedestal e centra em fundo branco."""
    rgb, alpha = G.recortar(frame)
    t, f, c = G.medir_estatua(alpha)
    alpha = G.cortar_em(alpha, c + int(0.015 * max(f - t, 1)))

    ys, xs = np.where(alpha > 0.5)
    m = 16
    y0, y1 = max(ys.min() - m, 0), min(ys.max() + m, alpha.shape[0])
    x0, x1 = max(xs.min() - m, 0), min(xs.max() + m, alpha.shape[1])
    rgb, a = rgb[y0:y1, x0:x1], alpha[y0:y1, x0:x1]

    # quadro quadrado com folga, fundo branco limpo
    h, w = a.shape
    lado = int(max(h, w) * 1.08)
    quadro = np.full((lado, lado, 3), 255.0)
    oy, ox = (lado - h) // 2, (lado - w) // 2
    mascara = (a > 0.5)[..., None]
    quadro[oy:oy + h, ox:ox + w] = np.where(mascara, rgb, 255.0)
    Image.fromarray(np.clip(quadro, 0, 255).astype(np.uint8)).save(destino)


def coletar_quadros(caminho: Path):
    if caminho.is_dir():
        return G.quadros_de_pasta(caminho)
    layout = G.VISTAS.get(caminho.stem.lower())
    if layout is None:
        return {}
    return G.fatiar(Image.open(caminho), layout)


async def gerar(client: TripoClient, classe: str, quadros: dict):
    faltam = [v for v in ORDEM_VISTAS if v not in quadros]
    if faltam:
        print(f"  ✗ vistas ausentes p/ multivista: {faltam}")
        return False

    TMP.mkdir(exist_ok=True)
    caminhos = []
    for v in ORDEM_VISTAS:
        destino = TMP / f"{classe}_{v}.png"
        preparar_vista(quadros[v], destino)
        caminhos.append(str(destino))
    print(f"    vistas preparadas em {TMP.name}/")

    task_id = await client.multiview_to_model(
        images=caminhos,
        model_version=MODEL_VERSION,
        texture=True,
        pbr=True,
        texture_quality='detailed',
        geometry_quality='detailed',
        texture_alignment='original_image',
    )
    print(f"    tarefa {task_id} — aguardando o Tripo gerar…")
    task = await client.wait_for_task(task_id, polling_interval=4.0, verbose=False)

    if task.status != 'success':
        print(f"  ✗ tarefa terminou com status {task.status}")
        return False

    arquivos = await client.download_task_models(task, str(TMP))
    origem = None
    for chave in ('pbr_model', 'model', 'base_model'):
        if arquivos.get(chave):
            origem = Path(arquivos[chave])
            break
    if origem is None or not origem.exists():
        print(f"  ✗ download sem modelo utilizável: {arquivos}")
        return False

    destino = SAIDA / f"{classe}.glb"
    destino.write_bytes(origem.read_bytes())
    print(f"  ✓ {destino.name} ({destino.stat().st_size // 1024} KB) [Tripo {MODEL_VERSION}]")
    return True


async def main():
    if not os.environ.get('TRIPO_API_KEY'):
        print("Defina TRIPO_API_KEY (https://platform.tripo3d.ai → API Keys)")
        return

    alvo = sys.argv[1].lower() if len(sys.argv) > 1 else None
    SAIDA.mkdir(exist_ok=True)

    async with TripoClient() as client:
        saldo = await client.get_balance()
        print(f"Créditos Tripo: {saldo}")

        vistos = set()
        for f in sorted(G.FONTES.iterdir()):
            if not f.is_dir() and f.suffix.lower() not in G.EXTS:
                continue
            if alvo and alvo not in f.stem.lower():
                continue
            if not f.is_dir() and (G.FONTES / f.stem).is_dir():
                continue          # a pasta homônima tem prioridade
            classe = G.classe_do_arquivo(f.stem)
            if classe is None or classe in vistos:
                continue
            vistos.add(classe)
            print(f"[{classe}] ← {f.name}")
            quadros = coletar_quadros(f)
            try:
                await gerar(client, classe, quadros)
            except Exception as e:
                print(f"  ✗ ERRO: {e}")


if __name__ == '__main__':
    asyncio.run(main())
