"""Colore a miniatura da espada (GLB cru, só POSITION) usando a paleta de
assets/itens/espada2m.png: lâmina de aço acinzentado com sulco central escuro,
guarda e pomo de ferro claro, anel e colar metálicos, punho de couro marrom.

Uso (da raiz): python tools/colorize_espada_glb.py <origem.glb> <destino.glb>
Mesmo método de tools/colorize_lanca_glb.py: cor por face em COLOR_0.
"""

import sys

import numpy as np
import trimesh


def main(source: str, destination: str) -> None:
    scene = trimesh.load(source, force="scene")
    if len(scene.geometry) != 1:
        raise RuntimeError(f"Esperava uma única malha; encontrei {len(scene.geometry)}.")
    mesh = next(iter(scene.geometry.values()))

    v = np.asarray(mesh.vertices, dtype=float)
    center = v.mean(axis=0)
    _, _, axes = np.linalg.svd(v - center, full_matrices=False)
    axial = (v - center) @ axes[0]
    # Garante o sentido: o pomo (lado curto, depois da guarda) fica no +axial.
    if axial.max() > -axial.min():
        axial = -axial
    across = (v - center) @ axes[1]          # largura da lâmina
    radial = np.linalg.norm((v - center) - np.outer((v - center) @ axes[0], axes[0]), axis=1)

    fa = axial[mesh.faces].mean(axis=1)
    fw = across[mesh.faces].mean(axis=1)
    fr = radial[mesh.faces].mean(axis=1)
    normals = np.asarray(mesh.face_normals)
    light = np.clip(0.74 + 0.26 * np.abs(normals @ np.array([0.25, 0.55, 0.80])), 0.62, 1.0)

    # Paleta amostrada da espada2m.png (sRGB), levemente clareada para a mesa.
    blade = np.array([150, 143, 136], float)
    blade_edge = np.array([178, 172, 166], float)
    fuller = np.array([92, 86, 80], float)
    iron = np.array([160, 153, 148], float)
    iron_dark = np.array([112, 105, 100], float)
    leather = np.array([92, 58, 38], float)
    leather_hi = np.array([122, 80, 52], float)

    colors = np.zeros((len(mesh.faces), 4), dtype=float)
    colors[:, 3] = 255

    # Lâmina (tudo antes da guarda): gradiente do centro para o fio,
    # com o sulco central escuro que percorre quase todo o comprimento.
    blade_m = fa < 0.27
    half_w = np.interp(fa, [-1.30, -1.18, 0.25], [0.035, 0.07, 0.092])
    t = np.clip(np.abs(fw) / half_w, 0, 1)[:, None]
    col = blade * (1 - t ** 2) + blade_edge * t ** 2
    fuller_m = blade_m & (np.abs(fw) < 0.016) & (fa > -1.05) & (fa < 0.22)
    col[fuller_m] = fuller
    colors[blade_m, :3] = col[blade_m]

    # Guarda em cruz: ferro claro, escurecendo nas pontas.
    guard_m = (fa >= 0.27) & (fa < 0.42)
    g = np.clip((fr - 0.10) / 0.22, 0, 1)[:, None]
    colors[guard_m, :3] = (iron * (1 - g) + iron_dark * g)[guard_m]

    # Punho de couro com leve variação ao longo do comprimento.
    grip_m = (fa >= 0.42) & (fa < 0.93)
    stripe = (0.5 + 0.5 * np.sin(fa * 90.0))[:, None]
    colors[grip_m, :3] = (leather * (1 - 0.35 * stripe) + leather_hi * 0.35 * stripe)[grip_m]

    # Colar sob a guarda e anel no meio do punho: metálicos.
    collar_m = (fa >= 0.42) & (fa < 0.455)
    ring_m = (fa >= 0.625) & (fa < 0.705)
    colors[collar_m | ring_m, :3] = iron_dark

    # Pomo.
    pommel_m = fa >= 0.93
    colors[pommel_m, :3] = iron * 0.92

    colors[:, :3] *= light[:, None]
    # COLOR_0 do glTF é LINEAR: converte a paleta sRGB da imagem, senão o
    # renderer clareia tudo (o aço viraria quase branco).
    s = np.clip(colors[:, :3], 0, 255) / 255.0
    lin = np.where(s <= 0.04045, s / 12.92, ((s + 0.055) / 1.055) ** 2.4)
    colors[:, :3] = lin * 255.0
    mesh.visual.face_colors = np.clip(np.round(colors), 0, 255).astype(np.uint8)
    scene.export(destination)
    print(f"GLB colorido salvo em {destination}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Uso: python tools/colorize_espada_glb.py <origem.glb> <destino.glb>")
    main(sys.argv[1], sys.argv[2])
