"""Paint a materialless crocodile GLB from a supplied thumbnail palette."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image


def reference_lut(path: Path) -> np.ndarray:
    image = np.array(Image.open(path).convert("RGBA"), dtype=np.uint8)
    rgb = image[:, :, :3].astype(np.float32)
    mask = (image[:, :, 3] >= 8) & (rgb.max(axis=2) > 8)
    if not np.any(mask):
        raise RuntimeError(f"Referência sem pixels utilizáveis: {path}")

    pixels = rgb[mask]
    luminance = pixels @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    centers = []
    colors = []
    for lo in range(0, 256, 16):
        selected = (luminance >= lo) & (luminance < lo + 16)
        if np.any(selected):
            centers.append((lo + lo + 15) * 0.5)
            colors.append(np.median(pixels[selected], axis=0))
    if len(centers) < 2:
        raise RuntimeError("Paleta insuficiente na referência")

    levels = np.arange(256, dtype=np.float32)
    centers = np.asarray(centers, dtype=np.float32)
    colors = np.asarray(colors, dtype=np.float32)
    lut = np.column_stack(
        [np.interp(levels, centers, colors[:, channel]) for channel in range(3)]
    )
    return np.clip(lut, 0, 255).astype(np.uint8)


def paint_mesh(mesh: trimesh.Trimesh, lut: np.ndarray) -> None:
    centers = mesh.triangles_center
    normals = mesh.face_normals
    z_min, z_max = mesh.bounds[:, 2]
    z_span = max(float(z_max - z_min), 1e-6)
    height = np.clip((centers[:, 2] - z_min) / z_span, 0.0, 1.0)
    normal_up = normals[:, 2]

    # The GLB has no source materials, so build a restrained painted finish
    # from the reference's actual brown, olive and warm-gold color curve.
    body_tone = 48.0 + 62.0 * height + 30.0 * np.maximum(normal_up, 0.0)
    scale_noise = np.sin(centers[:, 0] * 71.0 + centers[:, 1] * 43.0 + centers[:, 2] * 29.0)
    scale_noise += 0.45 * np.sin(centers[:, 0] * 137.0 - centers[:, 1] * 89.0)
    body_tone += 7.5 * scale_noise
    belly = (normal_up < -0.34) & (height > 0.22)
    body_tone[belly] += 42.0
    dorsal = (normal_up > 0.58) & (height > 0.34)
    body_tone[dorsal] += 8.0

    plinth = height < 0.10
    terrain = (height >= 0.10) & (height < 0.26) & (normal_up > 0.12)
    tone = np.clip(body_tone, 8, 220).astype(np.uint8)
    face_colors = lut[tone]

    # Rocks, muddy water and vegetation are deliberately darker and greener
    # than the hide, while the outer plinth remains charcoal like the reference.
    terrain_tone = np.clip(42.0 + 18.0 * scale_noise, 20, 78).astype(np.uint8)
    terrain_colors = lut[terrain_tone].astype(np.float32)
    terrain_colors *= np.array([0.88, 0.98, 0.78], dtype=np.float32)
    face_colors[terrain] = np.clip(terrain_colors[terrain], 0, 255).astype(np.uint8)
    face_colors[plinth] = np.array([42, 39, 35], dtype=np.uint8)

    vertex_colors = np.zeros((len(mesh.vertices), 4), dtype=np.uint8)
    vertex_colors[:, 3] = 255
    for face_index, face in enumerate(mesh.faces):
        vertex_colors[face, :3] = face_colors[face_index]
    mesh.visual = trimesh.visual.ColorVisuals(vertex_colors=vertex_colors)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.input.is_file():
        raise FileNotFoundError(args.input)
    if not args.reference.is_file():
        raise FileNotFoundError(args.reference)

    scene = trimesh.load(args.input, force="scene")
    if not isinstance(scene, trimesh.Scene) or len(scene.geometry) != 1:
        raise RuntimeError("Esperava um GLB com uma única malha")
    mesh = next(iter(scene.geometry.values()))
    if not isinstance(mesh, trimesh.Trimesh):
        raise RuntimeError("A geometria do GLB não é uma malha triangular")

    vertices_before = len(mesh.vertices)
    faces_before = len(mesh.faces)
    paint_mesh(mesh, reference_lut(args.reference))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    scene.export(temporary, file_type="glb")
    temporary.replace(args.output)
    print(
        f"saved {args.output} (vertices={vertices_before}, faces={faces_before}, "
        "colors=vertex_colors)"
    )


if __name__ == "__main__":
    main()
