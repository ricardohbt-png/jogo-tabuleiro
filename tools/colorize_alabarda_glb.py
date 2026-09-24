"""Colore a miniatura da alabarda (GLB cru, só POSITION) usando a paleta de
assets/itens/alabarda.png: lâmina, gancho e ponta de aço escuro, soquete e
anéis de ferro, haste de madeira marrom com trechos enrolados em couro escuro
perto da cabeça e da base, e o ferrão inferior de metal.

Uso (da raiz): python tools/colorize_alabarda_glb.py <origem.glb> <destino.glb>
Mesmo método de tools/colorize_espada_glb.py: cor por face em COLOR_0 (linear).
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
    # O eixo principal da malha inteira fica torto por causa da lâmina
    # lateral; o eixo da HASTE vem só do trecho central do cabo.
    c = v.mean(axis=0)
    _, _, ax = np.linalg.svd(v - c, full_matrices=False)
    a0 = (v - c) @ ax[0]
    shaft = v[(a0 > -1.0) & (a0 < -0.1)]
    c2 = shaft.mean(axis=0)
    _, _, ax2 = np.linalg.svd(shaft - c2, full_matrices=False)
    d = ax2[0] if ax2[0] @ ax[0] >= 0 else -ax2[0]
    # Sentido: a cabeça (lado longo, a partir do centro do cabo) fica no +.
    axial = (v - c2) @ d
    if axial.max() < -axial.min():
        axial = -axial
    radial = np.linalg.norm((v - c2) - np.outer((v - c2) @ d, d), axis=1)

    fa = axial[mesh.faces].mean(axis=1)
    fr = radial[mesh.faces].mean(axis=1)
    normals = np.asarray(mesh.face_normals)
    light = np.clip(0.74 + 0.26 * np.abs(normals @ np.array([0.25, 0.55, 0.80])), 0.62, 1.0)

    # Paleta amostrada da alabarda.png (sRGB), levemente clareada para a mesa.
    steel = np.array([118, 110, 106], float)
    steel_edge = np.array([150, 143, 138], float)
    iron = np.array([72, 65, 59], float)
    wood = np.array([96, 64, 42], float)
    wood_hi = np.array([118, 80, 52], float)
    wrap = np.array([50, 38, 33], float)

    colors = np.zeros((len(mesh.faces), 4), dtype=float)
    colors[:, 3] = 255

    # Haste de madeira com variação suave ao longo do comprimento.
    t = (0.5 + 0.5 * np.sin(fa * 7.0))[:, None]
    colors[:, :3] = wood * (1 - t) + wood_hi * t

    # Trechos enrolados em couro escuro: base do cabo e logo abaixo da cabeça.
    wrap_m = ((fa >= -0.54) & (fa < -0.28)) | ((fa >= 0.28) & (fa < 0.57))
    colors[wrap_m, :3] = wrap

    # Anéis de ferro (engrossamentos medidos no cabo).
    rings_m = (((fa >= -0.32) & (fa < -0.27)) | ((fa >= 0.28) & (fa < 0.33))
               | ((fa >= 0.45) & (fa < 0.50)))
    colors[rings_m, :3] = iron

    # Ferrão inferior.
    colors[fa < -0.54, :3] = iron

    # Cabeça: soquete de ferro junto à haste; lâmina e gancho de aço,
    # mais claros na borda (fio).
    head_m = fa >= 0.57
    socket_m = head_m & (fr < 0.06)
    blade_m = head_m & ~socket_m
    e = np.clip((fr - 0.06) / 0.28, 0, 1)[:, None] ** 2
    colors[blade_m, :3] = (steel * (1 - e) + steel_edge * e)[blade_m]
    colors[socket_m, :3] = iron

    # Ponta superior (acima da lâmina): aço.
    colors[fa >= 1.28, :3] = steel

    colors[:, :3] *= light[:, None]
    # COLOR_0 do glTF é LINEAR: converte a paleta sRGB da imagem.
    s = np.clip(colors[:, :3], 0, 255) / 255.0
    lin = np.where(s <= 0.04045, s / 12.92, ((s + 0.055) / 1.055) ** 2.4)
    colors[:, :3] = lin * 255.0
    mesh.visual.face_colors = np.clip(np.round(colors), 0, 255).astype(np.uint8)
    scene.export(destination)
    print(f"GLB colorido salvo em {destination}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Uso: python tools/colorize_alabarda_glb.py <origem.glb> <destino.glb>")
    main(sys.argv[1], sys.argv[2])
