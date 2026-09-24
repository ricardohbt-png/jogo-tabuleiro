"""Colore o GLB do machado segundo a arte de ``machado_duplo.png``.

O modelo de origem é uma única malha sem materiais. Este script preserva sua
geometria e grava ``COLOR_0`` por face: aço escuro e gasto na cabeça, madeira
castanha no cabo e couro/anéis escurecidos nas empunhaduras.

Uso (da raiz):
    python tools/colorize_machado_glb.py <origem.glb> <destino.glb>
"""

from __future__ import annotations

import sys

import numpy as np
import trimesh


def _linear_srgb(colors: np.ndarray) -> np.ndarray:
    """Converte cores sRGB de referência para COLOR_0 linear do glTF."""
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
    # Neste modelo, a cabeça larga fica no extremo positivo do eixo principal.
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

    # Paleta observada em assets/itens/machado_duplo.png. A leve variação de
    # tom no aço e na madeira evita uma peça lisa demais no tabuleiro.
    steel = np.array([112, 103, 98], dtype=float)
    steel_edge = np.array([169, 158, 150], dtype=float)
    steel_dark = np.array([62, 54, 51], dtype=float)
    wood = np.array([93, 58, 37], dtype=float)
    wood_hi = np.array([132, 86, 53], dtype=float)
    leather = np.array([55, 37, 30], dtype=float)
    iron_ring = np.array([73, 62, 57], dtype=float)

    colors = np.empty((len(mesh.faces), 4), dtype=float)
    colors[:, 3] = 255

    # Cabo de madeira: do pomo até a junção sob a cabeça.
    grain = (0.5 + 0.5 * np.sin(fa * 15.0 + fr * 43.0))[:, None]
    colors[:, :3] = wood * (1.0 - 0.30 * grain) + wood_hi * (0.30 * grain)

    # Empunhadura inferior enrolada e pomo de metal fosco.
    grip = (fa >= -1.17) & (fa < -0.84)
    pommel = fa < -1.32
    colors[grip, :3] = leather
    colors[pommel, :3] = iron_ring

    # Anéis e colar que prendem o cabo; suas faixas acompanham a arte de
    # referência, sem alterar a topologia da malha.
    rings = (
        ((fa >= -1.23) & (fa < -1.17))
        | ((fa >= -0.87) & (fa < -0.81))
        | ((fa >= -0.36) & (fa < -0.29))
        | ((fa >= -0.18) & (fa < 0.08))
    )
    colors[rings, :3] = iron_ring

    # Cabeça dupla: aço antigo, mais claro nos limites largos (os fios) e
    # mais escuro junto ao olho do machado.
    head = fa >= 0.08
    edge = np.clip((fr - 0.12) / 0.49, 0.0, 1.0)[:, None] ** 1.6
    colors[head, :3] = (steel * (1.0 - edge) + steel_edge * edge)[head]
    eye = head & (fr < 0.15)
    colors[eye, :3] = steel_dark

    colors[:, :3] *= light[:, None]
    colors[:, :3] = _linear_srgb(colors[:, :3])
    mesh.visual.face_colors = np.clip(np.round(colors), 0, 255).astype(np.uint8)
    scene.export(destination)
    print(f"GLB colorido salvo em {destination}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Uso: python tools/colorize_machado_glb.py <origem.glb> <destino.glb>")
    main(sys.argv[1], sys.argv[2])
