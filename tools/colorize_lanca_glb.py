"""Aplica materiais por região a um GLB de lança sem alterar o original."""

from pathlib import Path
import sys

import numpy as np
import trimesh


def main(source: str, destination: str) -> None:
    mesh_or_scene = trimesh.load(source, force="scene")
    if not isinstance(mesh_or_scene, trimesh.Scene):
        scene = trimesh.Scene(mesh_or_scene)
    else:
        scene = mesh_or_scene

    if len(scene.geometry) != 1:
        raise RuntimeError(f"Esperava uma única malha; encontrei {len(scene.geometry)}.")

    mesh = next(iter(scene.geometry.values()))
    vertices = np.asarray(mesh.vertices, dtype=float)
    center = vertices.mean(axis=0)
    _, _, axes = np.linalg.svd(vertices - center, full_matrices=False)
    long_axis = axes[0]
    axial = (vertices - center) @ long_axis
    radial = np.linalg.norm((vertices - center) - np.outer(axial, long_axis), axis=1)

    # O modelo está alinhado ao longo de um eixo diagonal. A extremidade de
    # maior raio é a lâmina; a extremidade oposta é o pomo metálico.
    face_axial = axial[mesh.faces].mean(axis=1)
    face_radial = radial[mesh.faces].mean(axis=1)
    face_normals = np.asarray(mesh.face_normals)
    light = np.clip(0.72 + 0.28 * np.abs(face_normals @ np.array([0.25, 0.55, 0.80])), 0.60, 1.0)

    colors = np.zeros((len(mesh.faces), 4), dtype=np.uint8)
    colors[:, 3] = 255

    wood = np.array([115, 52, 22], dtype=float)
    wood_hi = np.array([160, 83, 30], dtype=float)
    steel = np.array([170, 178, 184], dtype=float)
    steel_dark = np.array([65, 70, 76], dtype=float)
    bronze = np.array([112, 77, 42], dtype=float)

    # Haste de madeira, com uma variação suave para evitar o aspecto plástico.
    wood_mix = np.clip((face_axial + 1.45) / 1.80, 0.0, 1.0)[:, None]
    wood_color = wood * (1.0 - wood_mix) + wood_hi * wood_mix
    wood_color *= light[:, None]
    colors[:, :3] = np.clip(wood_color, 0, 255).astype(np.uint8)

    # Lâmina grande e ferrão inferior: metal prateado escurecido nas faces.
    head = face_axial >= 0.43
    butt = face_axial <= -1.53
    metal_color = steel[None, :] * light[:, None]
    metal_color *= (0.88 + 0.12 * np.clip(face_radial / 0.12, 0, 1))[:, None]
    colors[head | butt, :3] = np.clip(metal_color[head | butt], 0, 255).astype(np.uint8)

    # Anéis e encaixes próximos à lâmina e ao punho.
    bands = ((0.27 <= face_axial) & (face_axial < 0.43)) | ((-1.62 < face_axial) & (face_axial < -1.48))
    band_color = bronze[None, :] * light[:, None]
    colors[bands, :3] = np.clip(band_color[bands], 0, 255).astype(np.uint8)

    # Pequenas faixas metálicas intermediárias, detectadas pelo aumento local
    # da espessura em relação à haste.
    ring_candidates = (face_radial > 0.072) & (face_axial > -1.45) & (face_axial < 0.27)
    colors[ring_candidates, :3] = np.clip((steel_dark[None, :] + 24) * light[ring_candidates, None], 0, 255).astype(np.uint8)

    mesh.visual.face_colors = colors
    scene.export(destination)
    print(f"GLB colorido salvo em {destination}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Uso: python tools/colorize_lanca_glb.py <origem.glb> <destino.glb>")
    main(sys.argv[1], sys.argv[2])
