"""Cria a miniatura 3D estilizada do pombo para o bestiário."""

from pathlib import Path

import numpy as np
import trimesh


BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "assets" / "models3d" / "monstros" / "pombo.glb"


def material(color, roughness=0.88, metallic=0.0):
    return trimesh.visual.material.PBRMaterial(
        name="Pombo",
        baseColorFactor=(*color, 255),
        roughnessFactor=roughness,
        metallicFactor=metallic,
    )


def ellipsoid(name, position, scale, color, sections=24, rings=16):
    mesh = trimesh.creation.uv_sphere(radius=1.0, count=[sections, rings])
    mesh.name = name
    transform = np.eye(4)
    transform[:3, :3] = np.diag(scale)
    transform[:3, 3] = position
    mesh.apply_transform(transform)
    mesh.visual.material = material(color)
    return mesh


def cylinder_between(name, start, end, radius, color, sections=12):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    vector = end - start
    length = float(np.linalg.norm(vector))
    mesh = trimesh.creation.cylinder(radius=radius, height=length, sections=sections)
    mesh.name = name
    mesh.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], vector))
    mesh.apply_translation((start + end) / 2.0)
    mesh.visual.material = material(color)
    return mesh


def cone_between(name, start, end, radius, color, sections=16):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    vector = end - start
    length = float(np.linalg.norm(vector))
    mesh = trimesh.creation.cone(radius=radius, height=length, sections=sections)
    mesh.name = name
    mesh.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], vector))
    mesh.apply_translation((start + end) / 2.0)
    mesh.visual.material = material(color)
    return mesh


def make_pigeon():
    meshes = []
    # Silhueta compacta e cores contrastantes: o modelo anterior tinha
    # pescoço/pernas longos e claros demais, ficando parecido com uma galinha
    # quando visto de cima no tabuleiro.
    gray = (0.22, 0.25, 0.29)
    breast = (0.38, 0.42, 0.46)
    dark_gray = (0.075, 0.09, 0.12)
    neck = (0.16, 0.20, 0.25)
    neck_sheen = (0.23, 0.17, 0.30)
    beak = (0.28, 0.24, 0.18)
    pink = (0.42, 0.25, 0.25)
    black = (0.015, 0.012, 0.010)

    # Corpo baixo, cabeça arredondada e bico curto; a frente aponta para +Z.
    meshes.append(ellipsoid("corpo", (0, 0.18, 0), (0.17, 0.18, 0.23), gray))
    meshes.append(ellipsoid("peito", (0, 0.19, 0.14), (0.145, 0.16, 0.095), breast))
    meshes.append(ellipsoid("pescoco", (0, 0.31, 0.015), (0.115, 0.105, 0.115), neck))
    meshes.append(ellipsoid("brilho_pescoco", (0, 0.32, 0.095), (0.095, 0.07, 0.045), neck_sheen))
    meshes.append(ellipsoid("cabeca", (0, 0.405, 0.035), (0.115, 0.11, 0.11), gray))

    # Asas sobrepostas ao corpo, com volume suficiente para leitura isométrica.
    for side in (-1, 1):
        wing = ellipsoid(
            "asa_esquerda" if side < 0 else "asa_direita",
            (0.145 * side, 0.20, -0.015),
            (0.075, 0.145, 0.055),
            dark_gray,
        )
        wing.apply_transform(trimesh.transformations.rotation_matrix(0.32 * side, [0, 0, 1]))
        meshes.append(wing)

    # Cauda curta inclinada para trás (-Z).
    meshes.append(ellipsoid("cauda", (0, 0.19, -0.20), (0.11, 0.10, 0.13), dark_gray))
    meshes.append(ellipsoid("pena_cauda", (0, 0.22, -0.27), (0.07, 0.07, 0.105), gray))

    # Olhos laterais e bico voltado para a frente.
    for side in (-1, 1):
        meshes.append(ellipsoid("olho", (0.085 * side, 0.435, 0.132), (0.021, 0.021, 0.016), black, 12, 8))
        meshes.append(ellipsoid("brilho_olho", (0.085 * side, 0.441, 0.145), (0.006, 0.006, 0.004), (0.95, 0.95, 0.90), 8, 6))
    meshes.append(cone_between("bico", (0, 0.395, 0.135), (0, 0.39, 0.225), 0.034, beak))
    meshes.append(ellipsoid("caruncula", (0, 0.425, 0.132), (0.043, 0.018, 0.016), pink, 16, 8))

    # Pernas e pés apoiados no chão.
    for side in (-1, 1):
        x = 0.065 * side
        meshes.append(cylinder_between("perna", (x, 0.08, 0.02), (x, 0.035, 0.02), 0.012, pink, 8))
        meshes.append(cylinder_between("dedo_frontal", (x, 0.035, 0.02), (x, 0.03, 0.065), 0.009, pink, 8))
        meshes.append(cylinder_between("dedo_lateral", (x, 0.035, 0.02), (x + 0.035 * side, 0.03, 0.045), 0.009, pink, 8))

    # Remove qualquer pequena folga inferior causada pela triangulação.
    scene = trimesh.Scene(meshes)
    bounds = scene.bounds
    scene.apply_translation([0, -float(bounds[0][1]), 0])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    scene.export(OUT, file_type="glb")
    print(f"criado: {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    make_pigeon()
