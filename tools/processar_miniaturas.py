#!/usr/bin/env python3
"""
Processa as fotos de miniaturas (frente + verso lado a lado) em texturas de peão.
==================================================================================
Entrada : assets/pawns/_fontes/*.png|jpg  (foto com frente à esquerda, verso à direita)
Saída   : assets/pawns/<classe>/frente.png, costas.png (+ *_normal.png, *_original.png)

Pipeline por imagem:
  1. Divide no separador vertical claro do centro (fallback: metade exata)
  2. Remove o fundo escuro por flood-fill a partir das bordas (preserva o
     pedestal preto porque ele não é contíguo em cor ao fundo marrom)
  3. Preenche buracos, mantém só o maior componente, suaviza a borda do alpha
  4. Contorno claro estilo adesivo (mesmo visual das texturas atuais)
  5. Recorta, centraliza em quadrado e exporta em 1024×1024
  6. Gera normal map (mesma técnica do make_3d_pawns.py) — sem re-iluminar,
     pois as fotos novas já têm iluminação realista
"""

import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from rembg import new_session, remove
from scipy.ndimage import (
    binary_fill_holes, binary_dilation,
    gaussian_filter, label, distance_transform_edt,
)

# modelo de segmentação (baixado na primeira execução)
_SESSAO = new_session('isnet-general-use')

BASE       = Path(r"C:\Users\RICARDO\Desktop\jogo tabuleiro\assets\pawns")
FONTES     = BASE / "_fontes"
OUT_SIZE   = 1024          # resolução final (anterior era 512)
TOL        = 34.0          # tolerância de cor do flood-fill do fundo
OUTLINE_PX = 12            # espessura do contorno adesivo em px (na escala final)
OUTLINE_RGB = (235, 233, 228)
MARGEM     = 0.04          # folga ao redor da figura no quadro final

# palavra-chave no nome do arquivo → pasta da classe
CLASSES = {
    'bard':  ['bard', 'henrique'],
    'cleric': ['cler', 'lewis'],
    'warrior': ['guerr', 'anao', 'anão', 'warrior', 'viktor', 'victor'],
    'mage':  ['mago', 'mage', 'pedro'],
    'paladin': ['palad', 'richard'],
    'rogue': ['ladin', 'rogue', 'ladr', 'luccas'],
}


def classe_do_arquivo(nome: str):
    n = nome.lower()
    for classe, chaves in CLASSES.items():
        if any(k in n for k in chaves):
            return classe
    return None


def dividir(img: Image.Image):
    """Divide a foto no separador vertical claro do centro."""
    arr = np.asarray(img.convert('L'), dtype=np.float64)
    h, w = arr.shape
    ini, fim = int(w * 0.42), int(w * 0.58)
    col_brilho = arr[:, ini:fim].mean(axis=0)
    pico = ini + int(np.argmax(col_brilho))
    # só usa o pico se for de fato um separador claro; senão, metade exata
    corte = pico if col_brilho.max() > arr.mean() + 40 else w // 2
    folga = max(2, w // 200)
    rgb = img.convert('RGB')
    return rgb.crop((0, 0, corte - folga, h)), rgb.crop((corte + folga, 0, w, h))


def remover_fundo(metade: Image.Image, tol=TOL):
    """Segmentação por IA (rembg/ISNet) + limpeza morfológica."""
    rgb = np.asarray(metade, dtype=np.float64)

    mascara = remove(metade, session=_SESSAO, only_mask=True)
    alpha = np.asarray(mascara, dtype=np.float64) / 255.0

    # binariza, preenche buracos e mantém só o maior componente
    figura = binary_fill_holes(alpha > 0.5)
    rotulos, n = label(figura)
    if n > 1:
        tamanhos = np.bincount(rotulos.ravel())
        tamanhos[0] = 0
        figura = rotulos == tamanhos.argmax()

    # borda suave do alpha original onde a máscara binária confirma figura
    alpha = np.where(figura, np.maximum(alpha, 0.85), np.minimum(alpha, 0.6))
    alpha = gaussian_filter(alpha, sigma=0.8)
    alpha = np.clip((alpha - 0.35) / 0.45, 0, 1)
    return rgb, alpha


def aplicar_contorno(rgb: np.ndarray, alpha: np.ndarray, espessura: int):
    """Contorno claro estilo adesivo por baixo da figura."""
    solido = alpha > 0.5
    anel = binary_dilation(solido, iterations=espessura) & ~solido
    anel_suave = gaussian_filter(anel.astype(np.float64), sigma=1.0)

    out_rgb = rgb.copy()
    cor = np.array(OUTLINE_RGB, dtype=np.float64)
    mistura = np.clip(anel_suave * (1 - alpha), 0, 1)[..., None]
    out_rgb = out_rgb * (1 - mistura) + cor * mistura
    out_alpha = np.clip(alpha + anel_suave, 0, 1)
    return out_rgb, out_alpha


def enquadrar(rgb: np.ndarray, alpha: np.ndarray, tamanho: int):
    """Recorta pela caixa do alpha e centraliza num quadrado tamanho×tamanho."""
    ys, xs = np.where(alpha > 0.02)
    if len(ys) == 0:
        raise ValueError("nenhuma figura encontrada após remoção do fundo")
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgb, alpha = rgb[y0:y1, x0:x1], alpha[y0:y1, x0:x1]

    h, w = alpha.shape
    lado = int(max(h, w) * (1 + 2 * MARGEM))
    quadro = np.zeros((lado, lado, 4), dtype=np.float64)
    oy, ox = (lado - h) // 2, (lado - w) // 2
    quadro[oy:oy + h, ox:ox + w, :3] = rgb
    quadro[oy:oy + h, ox:ox + w, 3] = alpha * 255

    img = Image.fromarray(np.clip(quadro, 0, 255).astype(np.uint8), 'RGBA')
    return img.resize((tamanho, tamanho), Image.LANCZOS)


# ── Normal map (mesma técnica do make_3d_pawns.py) ────────────────────────────

def gerar_normal_map(img: Image.Image, destino: Path):
    data = np.asarray(img, dtype=np.float64) / 255.0
    alpha = data[..., 3]
    mask = alpha > 0.3
    depth = distance_transform_edt(mask)
    if depth.max() >= 1:
        depth = np.sin((depth / depth.max()) * (np.pi / 2))
    gy, gx = np.gradient(depth)
    gz = np.ones_like(gx) * 0.6
    comp = np.sqrt(gx**2 + gy**2 + gz**2) + 1e-8
    nx, ny, nz = gx / comp, -gy / comp, gz / comp

    h, w = alpha.shape
    nm = np.zeros((h, w, 4), dtype=np.uint8)
    nm[..., 0] = np.clip((nx * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    nm[..., 1] = np.clip((ny * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    nm[..., 2] = np.clip((nz * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    nm[..., 3] = np.clip(alpha * 255, 0, 255).astype(np.uint8)
    transparente = alpha < 0.1
    nm[transparente] = (128, 128, 255, 0)
    Image.fromarray(nm, 'RGBA').save(destino)


# ── Main ───────────────────────────────────────────────────────────────────────

def processar(caminho: Path, tol=TOL, so_preview=False):
    classe = classe_do_arquivo(caminho.stem)
    if classe is None:
        print(f"  ✗ {caminho.name}: classe não reconhecida no nome — pulando")
        return

    print(f"[{classe}] ← {caminho.name}")
    foto = Image.open(caminho)
    frente, costas = dividir(foto)

    destino = BASE / classe
    destino.mkdir(exist_ok=True)
    for lado, metade in (('frente', frente), ('costas', costas)):
        rgb, alpha = remover_fundo(metade, tol)
        esp_origem = max(2, int(round(OUTLINE_PX * alpha.shape[0] / OUT_SIZE)))
        rgb, alpha = aplicar_contorno(rgb, alpha, esp_origem)
        final = enquadrar(rgb, alpha, OUT_SIZE)

        sufixo = '_preview' if so_preview else ''
        final.save(destino / f'{lado}{sufixo}.png')
        if not so_preview:
            final.save(destino / f'{lado}_original.png')
            gerar_normal_map(final, destino / f'{lado}_normal.png')
        print(f"  ✓ {lado}{sufixo}.png ({OUT_SIZE}×{OUT_SIZE})")


def main():
    argv = sys.argv[1:]
    so_preview = '--preview' in argv
    argv = [a for a in argv if not a.startswith('--')]
    tol = float(argv[0]) if argv else TOL

    fontes = sorted(p for p in FONTES.iterdir()
                    if p.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp'))
    if not fontes:
        print(f"Nenhuma imagem em {FONTES}")
        return
    for f in fontes:
        processar(f, tol, so_preview)


if __name__ == '__main__':
    main()
