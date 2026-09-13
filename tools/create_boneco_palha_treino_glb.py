"""Gera uma miniatura GLB estilizada do boneco de palha de treino.

O modelo segue as convencoes das miniaturas do projeto: Y para cima, frente
apontando para +Z e a base encostada em Y=0. A imagem gerada serve como
referencia visual; o GLB e composto por pecas leves e nomeadas, adequadas para
o renderer Three.js do jogo.
"""

from pathlib import Path
import math

import numpy as np
import trimesh


BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "assets" / "objetos" / "boneco_palha_treino.glb"


def material(name, color, roughness=0.88, metallic=0.0):
    return trimesh.visual.material.PBRMaterial(
        name=name,
        baseColorFactor=(*color, 255),
        roughnessFactor=roughness,
        metallicFactor=metallic,
    )


def set_material(mesh, name, color, roughness=0.88, metallic=0.0):
    mesh.name = name
    mesh.visual.material = material(name, color, roughness, metallic)
    return mesh


def ellipsoid(name, position, scale, color, sections=18, rings=12):
    mesh = trimesh.creation.uv_sphere(radius=1.0, count=[sections, rings])
    transform = np.eye(4)
    transform[:3, :3] = np.diag(scale)
    transform[:3, 3] = position
    mesh.apply_transform(transform)
    return set_material(mesh, name, color)


def box(name, position, extents, color, rotation=None):
    mesh = trimesh.creation.box(extents=extents)
    if rotation is not None:
        mesh.apply_transform(rotation)
    mesh.apply_translation(position)
    return set_material(mesh, name, color)


def cylinder_between(name, start, end, radius, color, sections=10):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    vector = end - start
    length = float(np.linalg.norm(vector))
    mesh = trimesh.creation.cylinder(radius=radius, height=length, sections=sections)
    mesh.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], vector))
    mesh.apply_translation((start + end) / 2.0)
    return set_material(mesh, name, color)


def cone_between(name, start, end, radius, color, sections=8):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    vector = end - start
    length = float(np.linalg.norm(vector))
    mesh = trimesh.creation.cone(radius=radius, height=length, sections=sections)
    mesh.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], vector))
    mesh.apply_translation((start + end) / 2.0)
    return set_material(mesh, name, color)


def torus(name, position, major_radius, minor_radius, color, axis="y"):
    mesh = trimesh.creation.torus(major_radius=major_radius, minor_radius=minor_radius, major_sections=16, minor_sections=6)
    if axis == "y":
        mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
    elif axis == "x":
        mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
    mesh.apply_translation(position)
    return set_material(mesh, name, color)


def target(meshes, prefix, center, outer_radius, z, red, straw):
    """Alvos frontais voltados para +Z, com anel vermelho e miolo de palha."""
    x, y, _ = center
    meshes.append(set_material(
        trimesh.creation.cylinder(radius=outer_radius, height=0.012, sections=24),
        f"{prefix}_alvo_vermelho", red,
    ))
    meshes[-1].apply_translation((x, y, z))
    meshes.append(set_material(
        trimesh.creation.cylinder(radius=outer_radius * 0.47, height=0.016, sections=24),
        f"{prefix}_alvo_miolo", straw,
    ))
    meshes[-1].apply_translation((x, y, z + 0.008))


def build():
    straw = (0.78, 0.45, 0.16)
    straw_light = (0.96, 0.68, 0.27)
    straw_dark = (0.52, 0.27, 0.09)
    wood = (0.25, 0.105, 0.035)
    wood_light = (0.43, 0.22, 0.08)
    burlap = (0.64, 0.46, 0.27)
    rope = (0.28, 0.16, 0.075)
    red = (0.64, 0.105, 0.045)

    meshes = []

    # Base circular de madeira, com uma segunda camada para dar leitura de peca.
    meshes.append(set_material(
        trimesh.creation.cylinder(radius=0.34, height=0.095, sections=32),
        "base_madeira", wood,
    ))
    meshes[-1].apply_translation((0, 0.0475, 0))
    meshes.append(set_material(
        trimesh.creation.cylinder(radius=0.285, height=0.018, sections=32),
        "base_tampo", wood_light,
    ))
    meshes[-1].apply_translation((0, 0.102, 0))

    # Poste central e tres escoras, como na referencia.
    meshes.append(cylinder_between("poste_central", (0, 0.095, 0), (0, 1.48, 0), 0.048, wood_light, 10))
    for side in (-1, 1):
        meshes.append(cylinder_between(
            f"escora_{side}", (0.0, 0.11, 0), (0.24 * side, 0.11, -0.015), 0.035, wood, 8,
        ))
    meshes.append(cylinder_between("escora_frontal", (0, 0.11, 0), (0, 0.11, 0.24), 0.035, wood, 8))

    # Tronco e cabeca acolchoados.
    meshes.append(ellipsoid("tronco_palha", (0, 1.20, 0), (0.235, 0.28, 0.17), straw, 24, 16))
    meshes.append(ellipsoid("cabeca_burlap", (0, 1.72, 0), (0.17, 0.18, 0.17), burlap, 22, 14))

    # Bracos em cruz, com um nucleo de madeira e feixes de palha sobrepostos.
    meshes.append(cylinder_between("trave_bracos", (-0.78, 1.46, 0), (0.78, 1.46, 0), 0.052, wood_light, 10))
    for side in (-1, 1):
        s = float(side)
        meshes.append(ellipsoid(f"feixe_braco_{side}", (0.48 * s, 1.46, 0), (0.34, 0.095, 0.095), straw_light, 16, 10))
        meshes.append(torus(f"corda_pulso_{side}", (0.76 * s, 1.46, 0), 0.084, 0.018, rope, axis="x"))
        # Pequenas pontas de palha tornam as extremidades menos geometricas.
        for i, dy in enumerate((-0.06, 0.0, 0.06)):
            meshes.append(cone_between(
                f"palha_braco_{side}_{i}", (0.77 * s, 1.46 + dy, 0), (0.88 * s, 1.46 + dy * 1.6, 0),
                0.022, straw_light, 6,
            ))

    # Amarracoes principais e cruzamento de corda no peito.
    meshes.append(torus("corda_pescoco", (0, 1.51, 0), 0.19, 0.022, rope, axis="y"))
    meshes.append(torus("corda_cintura", (0, 0.99, 0), 0.22, 0.022, rope, axis="y"))
    meshes.append(torus("corda_punho_esq", (-0.53, 1.46, 0), 0.095, 0.02, rope, axis="x"))
    meshes.append(torus("corda_punho_dir", (0.53, 1.46, 0), 0.095, 0.02, rope, axis="x"))
    meshes.append(cylinder_between("corda_diagonal_a", (-0.16, 1.36, 0.17), (0.16, 1.05, 0.17), 0.014, rope, 8))
    meshes.append(cylinder_between("corda_diagonal_b", (0.16, 1.36, 0.17), (-0.16, 1.05, 0.17), 0.014, rope, 8))
    meshes.append(torus("corda_base", (0, 0.28, 0), 0.064, 0.02, rope, axis="y"))

    # Franjas de palha na parte inferior do corpo e no topo da cabeca.
    for i in range(14):
        angle = 2 * math.pi * i / 14
        x = 0.18 * math.cos(angle)
        z = 0.11 * math.sin(angle)
        meshes.append(cone_between(
            f"franja_tronco_{i}", (x, 0.99, z), (x * 1.16, 0.83 + 0.015 * (i % 2), z * 1.16),
            0.023, straw_light if i % 3 else straw_dark, 6,
        ))
    for i in range(13):
        angle = 2 * math.pi * i / 13
        x = 0.10 * math.cos(angle)
        z = 0.10 * math.sin(angle)
        meshes.append(cone_between(
            f"tufo_cabeca_{i}", (x, 1.85, z), (x * 1.35, 2.01 + 0.035 * (i % 2), z * 1.35),
            0.019, straw_light, 6,
        ))

    # Alvos da frente (+Z), alinhados com a imagem de referencia.
    target(meshes, "cabeca", (0, 1.72, 0), 0.082, 0.166, red, burlap)
    target(meshes, "tronco", (0, 1.20, 0), 0.115, 0.169, red, straw)

    # Limpa pequenas variacoes numericas e assenta a peca no chao.
    scene = trimesh.Scene(meshes)
    scene.apply_translation([0, -float(scene.bounds[0][1]), 0])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    scene.export(OUT, file_type="glb")
    print(f"GLB criado: {OUT} ({OUT.stat().st_size} bytes, {len(meshes)} objetos)")


if __name__ == "__main__":
    build()
