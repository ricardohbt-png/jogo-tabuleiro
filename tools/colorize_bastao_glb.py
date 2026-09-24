"""Colore ``bastao.glb`` segundo a arte de ``assets/itens/staff.png``.

O GLB original possui uma única malha sem materiais. A geometria permanece
intacta; esta rotina grava COLOR_0 por face para a haste de madeira/couro, os
ornamentos de bronze envelhecido e a gema azul do topo.

Uso (da raiz):
    python tools/colorize_bastao_glb.py <origem.glb> <destino.glb>
"""

from __future__ import annotations

import sys

import numpy as np
import trimesh


def _to_linear_srgb(colors: np.ndarray) -> np.ndarray:
    srgb = np.clip(colors, 0, 255) / 255.0
    return np.where(srgb <= 0.04045, srgb / 12.92,
                    ((srgb + 0.055) / 1.055) ** 2.4) * 255.0


def main(source: str, destination: str) -> None:
    scene = trimesh.load(source, force="scene")
    if not isinstance(scene, trimesh.Scene):
        scene = trimesh.Scene(scene)
    if len(scene.geometry) != 1:
        raise RuntimeError(f"Esperava uma única malha; encontrei {len(scene.geometry)}.")

    mesh = next(iter(scene.geometry.values()))
    vertices = np.asarray(mesh.vertices, dtype=float)
    center = vertices.mean(axis=0)
    _, _, axes = np.linalg.svd(vertices - center, full_matrices=False)
    axis = axes[0]
    axial = (vertices - center) @ axis
    # O aro com a gema fica no extremo superior do bastão.
    if axial.max() < -axial.min():
        axial = -axial
        axis = -axis
    radial = np.linalg.norm(
        (vertices - center) - np.outer(axial, axis), axis=1
    )

    fa = axial[mesh.faces].mean(axis=1)
    fr = radial[mesh.faces].mean(axis=1)
    normals = np.asarray(mesh.face_normals)
    light = np.clip(
        0.70 + 0.30 * np.abs(normals @ np.array([0.25, 0.55, 0.80])),
        0.58, 1.0,
    )

    # Cores amostradas visualmente de staff.png: madeira e couro escuros,
    # bronze quente nos ramos e azul vivo, mas não neon, na gema.
    wood = np.array([79, 45, 26], dtype=float)
    wood_hi = np.array([121, 72, 39], dtype=float)
    leather = np.array([43, 25, 18], dtype=float)
    bronze = np.array([124, 61, 28], dtype=float)
    bronze_hi = np.array([172, 91, 42], dtype=float)
    bronze_dark = np.array([70, 34, 20], dtype=float)
    gem = np.array([19, 127, 177], dtype=float)
    gem_hi = np.array([71, 198, 238], dtype=float)

    colors = np.empty((len(mesh.faces), 4), dtype=float)
    colors[:, 3] = 255

    # Haste de madeira com grão discreto e o punho inferior em couro.
    grain = (0.5 + 0.5 * np.sin(fa * 17.0 + fr * 59.0))[:, None]
    colors[:, :3] = wood * (1.0 - 0.34 * grain) + wood_hi * (0.34 * grain)
    # A curva externa do aro desce até essa faixa axial, mas é bem mais larga
    # que o punho. Restringir o couro ao núcleo fino preserva o bronze do aro.
    grip = (fa < -0.72) & (fr < 0.075)
    colors[grip, :3] = leather

    # As abraçadeiras da haste e a transição para o aro são bronze escuro.
    bands = (
        ((fa >= -0.76) & (fa < -0.68))
        | ((fa >= -0.34) & (fa < -0.25))
        | ((fa >= -0.04) & (fa < 0.05))
        | ((fa >= 0.17) & (fa < 0.31))
    )
    colors[bands, :3] = bronze_dark

    # Ramo/aro no topo: cobre envelhecido, claro nas bordas expostas.
    crown = (fa >= 0.31) | (fr > 0.075)
    edge = np.clip((fr - 0.035) / 0.080, 0.0, 1.0)[:, None]
    colors[crown, :3] = (bronze * (1.0 - edge) + bronze_hi * edge)[crown]

    # A gema fica no núcleo do aro: centro azul profundo e pequeno brilho azul.
    stone = crown & (fa >= 0.48) & (fa <= 0.82) & (fr < 0.052)
    highlight = stone & (fa >= 0.58) & (fa <= 0.70) & (fr < 0.030)
    colors[stone, :3] = gem
    colors[highlight, :3] = gem_hi

    colors[:, :3] *= light[:, None]
    colors[:, :3] = _to_linear_srgb(colors[:, :3])
    mesh.visual.face_colors = np.clip(np.round(colors), 0, 255).astype(np.uint8)
    scene.export(destination)
    print(f"GLB colorido salvo em {destination}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Uso: python tools/colorize_bastao_glb.py <origem.glb> <destino.glb>")
    main(sys.argv[1], sys.argv[2])
