#!/usr/bin/env python3
"""
3D Lighting Effect for Character Pawns — Legends for Hire
=========================================================
Técnica:
  1. Distance Transform na máscara alpha → profundidade real da silhueta
     (pixels no centro do personagem = mais "altos", bordas = mais "baixos")
  2. Curva senoidal na profundidade → volume mais arredondado/esférico
  3. Gradiente de Sobel → normais de superfície (como um normal map)
  4. Lambert + Phong sobre essas normais → iluminação física realista
  5. Blend: 50% original + 50% iluminado → preserva o art style do personagem

Também:
  • Copia costa.png → costas.png em todos os heróis (fix de naming)
  • Gera frente_normal.png / costas_normal.png para uso opcional em Three.js
  • Faz backup em frente_original.png antes de sobrescrever
"""

import os, sys, shutil
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt, generic_filter

# ── Configurações ──────────────────────────────────────────────────────────────
PAWNS_DIR      = Path(r"C:\Users\RICARDO\Desktop\jogo tabuleiro\assets\pawns")
BLEND_STRENGTH = 0.52   # 0 = original puro, 1 = efeito completo
AMBIENT        = 0.28   # iluminação base (impede preto total nas sombras)
DIFFUSE_STR    = 0.58   # força da luz difusa (Lambert)
SPECULAR_STR   = 0.22   # força do brilho especular (Phong)
SHININESS      = 28     # concentração do brilho (maior = mais pontual)

# Direção da luz em espaço de textura:
#   X: eixo horizontal (negativo = da esquerda)
#   Y: eixo vertical   (positivo = de cima)
#   Z: em direção ao viewer (sempre positivo)
# Resultado: luz vinda de cima-ligeiramente-à-esquerda → aspecto de tocha/luz de cima
LIGHT = np.array([-0.25, 0.80, 0.55], dtype=np.float64)
LIGHT /= np.linalg.norm(LIGHT)


# ── Utilitários ────────────────────────────────────────────────────────────────

def sobel_x(arr):
    """Gradiente horizontal com kernel Sobel 3×3."""
    kernel = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float64)
    h, w = arr.shape
    out = np.zeros_like(arr)
    padded = np.pad(arr, 1, mode='edge')
    for i in range(3):
        for j in range(3):
            out += kernel[i, j] * padded[i:i+h, j:j+w]
    return out

def sobel_y(arr):
    """Gradiente vertical com kernel Sobel 3×3."""
    kernel = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float64)
    h, w = arr.shape
    out = np.zeros_like(arr)
    padded = np.pad(arr, 1, mode='edge')
    for i in range(3):
        for j in range(3):
            out += kernel[i, j] * padded[i:i+h, j:j+w]
    return out


# ── Core: Depth + Normais ──────────────────────────────────────────────────────

def compute_normals(alpha: np.ndarray):
    """
    Estima normais de superfície a partir da máscara alpha.
    Retorna array (H, W, 3) com normais normalizadas.
    """
    mask = alpha > 0.3

    # Distance transform: distância de cada pixel à borda da silhueta
    depth_raw = distance_transform_edt(mask)

    if depth_raw.max() < 1:
        h, w = alpha.shape
        flat_normals = np.zeros((h, w, 3))
        flat_normals[..., 2] = 1.0
        return flat_normals, depth_raw

    depth_norm = depth_raw / depth_raw.max()

    # Curva senoidal → volume mais esférico (não linear)
    depth_curve = np.sin(depth_norm * (np.pi / 2))

    # Gradiente → normais (sem scipy.ndimage.sobel para evitar dependências extras)
    gx =  sobel_x(depth_curve) / 8.0   # dividir por 8 normaliza o kernel Sobel
    gy = -sobel_y(depth_curve) / 8.0   # Y negado: coordenada de imagem vs mundo

    # Z aponta sempre para o viewer; magnitude relativa controla "suavidade" da curva
    gz = np.ones_like(gx) * 0.6

    length = np.sqrt(gx**2 + gy**2 + gz**2) + 1e-8
    normals = np.stack([gx / length, gy / length, gz / length], axis=-1)

    return normals, depth_curve


# ── Core: Iluminação ───────────────────────────────────────────────────────────

def apply_lighting(rgb: np.ndarray, normals: np.ndarray, alpha: np.ndarray):
    """
    Aplica Lambert + Phong sobre as normais calculadas.
    rgb: float32 array (H, W, 3) com valores 0–1
    """
    # Difuso (Lambert): N · L
    dot = np.einsum('hwc,c->hw', normals, LIGHT)
    diffuse = np.clip(dot, 0, 1)

    # Especular (Phong): viewer em (0,0,1), reflexo em torno da normal
    # R = 2*(N·L)*N - L; specular = max(0, R·V)^shininess
    ndotl = np.clip(dot, 0, 1)
    reflect_z = 2 * normals[..., 2] * ndotl - LIGHT[2]
    specular = np.clip(reflect_z, 0, 1) ** SHININESS

    # Luz total por pixel
    light_val = AMBIENT + DIFFUSE_STR * diffuse + SPECULAR_STR * specular
    light_val = np.clip(light_val, 0, 1.9)   # permite ligeiro overexpose no highlight

    # Aplica à imagem (multiplicação canal a canal preserva matiz)
    lit = np.clip(rgb * light_val[..., None], 0, 1)
    return lit


# ── Core: Normal Map ───────────────────────────────────────────────────────────

def save_normal_map(normals: np.ndarray, alpha: np.ndarray, path: Path):
    """
    Salva normal map em formato OpenGL (R=X, G=Y, B=Z, A=alpha).
    Valores remapeados: -1..1 → 0..255 com 128 = neutro.
    """
    h, w = normals.shape[:2]
    nm = np.zeros((h, w, 4), dtype=np.uint8)
    nm[..., 0] = np.clip((normals[..., 0] * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    nm[..., 1] = np.clip((normals[..., 1] * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    nm[..., 2] = np.clip((normals[..., 2] * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    nm[..., 3] = np.clip(alpha * 255, 0, 255).astype(np.uint8)
    # Pixels transparentes: normal neutra (aponta para o viewer)
    transparent = alpha < 0.1
    nm[transparent, 0] = 128
    nm[transparent, 1] = 128
    nm[transparent, 2] = 255
    Image.fromarray(nm, 'RGBA').save(path)


# ── Pipeline por imagem ────────────────────────────────────────────────────────

def process_image(src: Path, dst: Path, normal_dst: Path):
    img  = Image.open(src).convert('RGBA')
    data = np.array(img, dtype=np.float32) / 255.0

    rgb   = data[..., :3]
    alpha = data[..., 3]

    normals, _ = compute_normals(alpha)
    lit         = apply_lighting(rgb, normals, alpha)

    # Blend: 50% original + 50% iluminado (preserva o art style)
    blended = rgb * (1.0 - BLEND_STRENGTH) + lit * BLEND_STRENGTH
    blended = np.clip(blended, 0, 1)

    # Mantém pixels originais onde a textura é transparente
    out       = np.zeros_like(data)
    mask      = alpha > 0.05
    out[..., :3] = np.where(mask[..., None], blended, rgb)
    out[..., 3]  = alpha

    Image.fromarray((out * 255).astype(np.uint8), 'RGBA').save(dst)
    save_normal_map(normals, alpha, normal_dst)
    print(f"  ✓  {dst.parent.name}/{dst.name}  +  {normal_dst.name}")


# ── Main ────────────────────────────────────────────────────────────────────────

def main():
    errors = []
    classes = sorted(d for d in PAWNS_DIR.iterdir() if d.is_dir())

    for cls_dir in classes:
        print(f"\n[{cls_dir.name}]")

        # Fix naming: costa.png → costas.png
        costa  = cls_dir / 'costa.png'
        costas = cls_dir / 'costas.png'
        if not costas.exists() and costa.exists():
            shutil.copy2(costa, costas)
            print(f"  → copiado costa.png → costas.png")

        for side in ('frente', 'costas'):
            src = cls_dir / f'{side}.png'
            if not src.exists():
                print(f"  ✗  {side}.png não encontrado, pulando")
                continue

            # Backup (apenas uma vez, não sobrescreve backup existente)
            bak = cls_dir / f'{side}_original.png'
            if not bak.exists():
                shutil.copy2(src, bak)
                print(f"  → backup criado: {bak.name}")

            normal_dst = cls_dir / f'{side}_normal.png'
            try:
                process_image(src, src, normal_dst)
            except Exception as e:
                print(f"  ✗  ERRO em {side}.png: {e}")
                errors.append((cls_dir.name, side, str(e)))

    print("\n" + "=" * 50)
    if errors:
        print(f"Concluído com {len(errors)} erro(s):")
        for cls, side, msg in errors:
            print(f"  {cls}/{side}: {msg}")
    else:
        print("Concluído sem erros!")
    print("Backups salvos como *_original.png em cada pasta.")
    print("Normal maps salvos como *_normal.png em cada pasta.")


if __name__ == '__main__':
    main()
