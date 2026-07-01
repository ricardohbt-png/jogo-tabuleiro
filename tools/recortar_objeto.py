"""DEV: recorta um PNG de objeto (assets/objetos) em um cutout de silhueta limpa
para a miniatura 3D extrudada.

Pipeline:
  1. Limiariza o canal alfa (fundo semi-transparente vira transparente).
  2. Fechamento morfológico (junta os vãos finos — ex.: folhas da copa).
  3. Preenche buracos internos totalmente cercados.
  4. Mantém só o maior componente conectado (descarta specks soltos).
  5. Inpinta a cor (RGB) dos pixels recém-incluídos a partir do vizinho
     opaco mais próximo (evita halo branco na face).
  6. Grava RGBA com alfa = 255 dentro da silhueta, 0 fora.

Uso (da raiz do projeto):
    python tools/recortar_objeto.py arvore.png [--out arvore_cutout.png]
        [--thresh 128] [--close 8] [--keep-largest/--no-keep-largest]
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

OBJ_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "assets", "objetos")


def recortar(src_path, thresh=128, close=0, keep_largest=True, max_hole_frac=0.0001,
             margin=0.08, smooth=0.0, gray_sat=40, gray_val=140):
    im = Image.open(src_path).convert("RGBA")
    arr = np.array(im)
    alpha = arr[:, :, 3]

    # O fundo deste PNG é um XADREZ embutido (quadrados cinza/branco OPACOS), não
    # transparência real. Detecta fundo por COR (cinza-claro, baixa saturação) OU
    # alfa baixo; o objeto (verde/marrom, saturado) é o resto. `gray_val` e
    # `gray_sat` controlam o que conta como "cinza de fundo".
    rgb = arr[:, :, :3].astype(np.int16)
    chroma = rgb.max(axis=2) - rgb.min(axis=2)      # ~saturação
    valor = rgb.mean(axis=2)
    is_bg = (alpha < thresh) | ((chroma < gray_sat) & (valor > gray_val))
    mask = ~is_bg

    # Fechamento opcional: junta vãos finos (folhas) sem inchar.
    if close > 0:
        mask = ndimage.binary_dilation(mask, iterations=close)
        mask = ndimage.binary_erosion(mask, iterations=close)

    # Suavização do contorno: borra a máscara e re-limiariza. Arredonda a borda
    # rendada (lóbulos de folha) num contorno coeso de miniatura — sem isso a
    # silhueta extrudada vira uma franja de micro-facetas.
    if smooth > 0:
        mask = ndimage.gaussian_filter(mask.astype("float32"), smooth) >= 0.5

    # Mantém só o maior componente (descarta as ilhas de ruído do halo).
    if keep_largest:
        lbl, n = ndimage.label(mask)
        if n > 1:
            sizes = ndimage.sum(np.ones_like(lbl), lbl, index=range(1, n + 1))
            maior = int(np.argmax(sizes)) + 1
            mask = lbl == maior

    # Preenche SÓ buracos internos pequenos (vãos entre folhas) — não o fundo
    # enclausurado. Buraco = região transparente cercada que não toca a borda.
    preenchido = ndimage.binary_fill_holes(mask)
    buracos = preenchido & ~mask
    if buracos.any():
        lblb, nb = ndimage.label(buracos)
        if nb > 0:
            areas = ndimage.sum(np.ones_like(lblb), lblb, index=range(1, nb + 1))
            limite = max_hole_frac * mask.size
            for i, area in enumerate(areas, start=1):
                if area <= limite:
                    mask[lblb == i] = True

    # Inpaint de cor: pixels do mask sem cor confiável recebem o RGB do pixel de
    # objeto mais próximo. `trusted` = só FRENTE opaca (exclui o xadrez), senão a
    # cor do xadrez vazaria para os vãos preenchidos.
    trusted = mask & (alpha >= 200) & ~is_bg
    novos = mask & ~trusted
    if novos.any() and trusted.any():
        # índices do pixel "trusted" mais próximo, para cada pixel
        idx = ndimage.distance_transform_edt(~trusted, return_distances=False,
                                             return_indices=True)
        for c in range(3):
            canal = arr[:, :, c]
            arr[novos, c] = canal[idx[0][novos], idx[1][novos]]

    out = np.zeros_like(arr)
    out[:, :, :3] = arr[:, :, :3]
    out[mask, 3] = 255

    # Margem transparente: garante que a silhueta NÃO toque a borda do quadro.
    # Sem isso, uma silhueta que encosta nas bordas faz o tracer enclausurar o
    # fundo e gerar uma "placa" em vez do contorno do objeto.
    if margin > 0:
        h0, w0 = out.shape[:2]
        pad = int(round(max(w0, h0) * margin))
        canvas = np.zeros((h0 + 2 * pad, w0 + 2 * pad, 4), dtype=out.dtype)
        canvas[pad:pad + h0, pad:pad + w0] = out
        out = canvas

    cobertura = 100.0 * mask.mean()
    return Image.fromarray(out, "RGBA"), cobertura


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("nome", help="arquivo em assets/objetos (ex.: arvore.png)")
    ap.add_argument("--out", default=None, help="nome de saída (default: <nome>_cutout.png)")
    ap.add_argument("--thresh", type=int, default=128)
    ap.add_argument("--close", type=int, default=0)
    ap.add_argument("--smooth", type=float, default=0.0, help="sigma do blur de suavização do contorno (px)")
    ap.add_argument("--margin", type=float, default=0.08)
    ap.add_argument("--keep-largest", dest="keep_largest", action="store_true", default=True)
    ap.add_argument("--no-keep-largest", dest="keep_largest", action="store_false")
    args = ap.parse_args(argv)

    src = os.path.join(OBJ_DIR, args.nome)
    if not os.path.isfile(src):
        print(f"não encontrado: {src}")
        return 1
    out_name = args.out or (os.path.splitext(args.nome)[0] + "_cutout.png")
    dst = os.path.join(OBJ_DIR, out_name)

    img, cobertura = recortar(src, thresh=args.thresh, close=args.close,
                              keep_largest=args.keep_largest, margin=args.margin,
                              smooth=args.smooth)
    img.save(dst)
    print(f"ok: {out_name}  cobertura silhueta = {cobertura:.1f}%  (thresh={args.thresh} close={args.close})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
