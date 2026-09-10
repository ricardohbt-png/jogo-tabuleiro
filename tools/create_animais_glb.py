"""Cria as miniaturas 3D estilizadas dos animais ambientais do bestiário.

Rato, gato e ovelha são as formas basicas da Metamorfose e nasceram sem arte
nenhuma: caiam na miniatura GENERICA do renderer (o "boneco branco"). Este
script gera os tres .glb no mesmo pipeline procedural do `create_pombo_glb.py`.

Convencoes herdadas do pombo, e que o renderer assume:
  - a frente da criatura aponta para +Z (o `facing` gira o grupo em torno de Y);
  - o modelo e transladado para encostar a base em Y=0;
  - a silhueta importa mais que o detalhe, porque `build3DFig` normaliza tudo
    pela bounding box e a peca e vista de cima, em isometrica.

Uso (da raiz do projeto):  python tools/create_animais_glb.py
"""

from pathlib import Path

import numpy as np
import trimesh


BASE = Path(__file__).resolve().parents[1]
OUT_DIR = BASE / "assets" / "models3d" / "monstros"


def material(nome, color, roughness=0.88, metallic=0.0):
    return trimesh.visual.material.PBRMaterial(
        name=nome,
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
    mesh.visual.material = material(name, color)
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
    mesh.visual.material = material(name, color)
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
    mesh.visual.material = material(name, color)
    return mesh


def _exportar(meshes, nome):
    """Assenta a peca no chao e grava o .glb."""
    scene = trimesh.Scene(meshes)
    scene.apply_translation([0, -float(scene.bounds[0][1]), 0])
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    destino = OUT_DIR / f"{nome}.glb"
    scene.export(destino, file_type="glb")
    print(f"criado: {destino} ({destino.stat().st_size} bytes)")


# ── Rato ──────────────────────────────────────────────────────────────────
def make_rato():
    """Corpo baixo e alongado, orelhas redondas grandes e cauda longa — os
    tres tracos que fazem a silhueta ser lida como rato vista de cima. A paleta
    branca e rosa diferencia a forma da Metamorfose das criaturas comuns."""
    meshes = []
    pelo = (0.96, 0.95, 0.92)
    ventre = (1.00, 0.70, 0.76)
    focinho = (1.00, 0.78, 0.82)
    rosa = (0.94, 0.38, 0.50)
    preto = (0.02, 0.018, 0.015)

    # Corpo em gota: mais largo atras, afinando para o focinho (+Z).
    meshes.append(ellipsoid("corpo", (0, 0.115, -0.03), (0.105, 0.10, 0.165), pelo))
    meshes.append(ellipsoid("ventre", (0, 0.075, -0.02), (0.088, 0.055, 0.135), ventre))
    meshes.append(ellipsoid("cabeca", (0, 0.125, 0.135), (0.078, 0.072, 0.085), pelo))
    meshes.append(cone_between("focinho", (0, 0.115, 0.19), (0, 0.10, 0.275), 0.045, focinho))
    meshes.append(ellipsoid("nariz", (0, 0.10, 0.272), (0.016, 0.014, 0.012), rosa, 12, 8))

    # Orelhas grandes e circulares, viradas para os lados.
    for lado in (-1, 1):
        orelha = ellipsoid(
            "orelha_esquerda" if lado < 0 else "orelha_direita",
            (0.062 * lado, 0.185, 0.10), (0.052, 0.052, 0.016), rosa, 16, 12)
        orelha.apply_transform(
            trimesh.transformations.rotation_matrix(0.38 * lado, [0, 0, 1]))
        meshes.append(orelha)

    for lado in (-1, 1):
        meshes.append(ellipsoid("olho", (0.042 * lado, 0.148, 0.185),
                                (0.014, 0.014, 0.011), preto, 12, 8))

    # Cauda: tres segmentos encolhendo, curvada para o lado.
    meshes.append(cylinder_between("cauda_1", (0, 0.10, -0.185), (0.03, 0.075, -0.30), 0.013, rosa, 8))
    meshes.append(cylinder_between("cauda_2", (0.03, 0.075, -0.30), (0.085, 0.05, -0.38), 0.010, rosa, 8))
    meshes.append(cylinder_between("cauda_3", (0.085, 0.05, -0.38), (0.155, 0.038, -0.415), 0.0075, rosa, 8))

    # Patas curtas: o rato quase encosta a barriga no chao.
    for lado in (-1, 1):
        for z, nome in ((0.085, "pata_frente"), (-0.09, "pata_tras")):
            meshes.append(cylinder_between(
                nome, (0.062 * lado, 0.055, z), (0.072 * lado, 0.012, z), 0.014, rosa, 8))

    _exportar(meshes, "rato")


# ── Gato ──────────────────────────────────────────────────────────────────
def make_gato():
    """Gato sentado: a pose sentada le melhor de cima que a de quatro patas,
    e as orelhas triangulares dao a leitura imediata da especie."""
    meshes = []
    pelo = (0.28, 0.26, 0.30)
    listra = (0.19, 0.175, 0.21)
    peito = (0.62, 0.60, 0.58)
    rosa = (0.55, 0.36, 0.38)
    verde = (0.55, 0.68, 0.35)
    preto = (0.02, 0.018, 0.015)

    # Tronco em cone invertido (traseiro apoiado, peito erguido).
    meshes.append(ellipsoid("ancas", (0, 0.135, -0.055), (0.155, 0.135, 0.155), pelo))
    meshes.append(ellipsoid("tronco", (0, 0.275, 0.01), (0.125, 0.145, 0.115), pelo))
    meshes.append(ellipsoid("peito", (0, 0.255, 0.085), (0.088, 0.11, 0.06), peito))
    meshes.append(ellipsoid("cabeca", (0, 0.44, 0.035), (0.115, 0.105, 0.105), pelo))
    meshes.append(ellipsoid("focinho", (0, 0.405, 0.12), (0.062, 0.048, 0.045), peito))
    meshes.append(ellipsoid("nariz", (0, 0.425, 0.152), (0.018, 0.015, 0.012), rosa, 12, 8))

    # Orelhas triangulares com miolo rosa.
    for lado in (-1, 1):
        base = (0.072 * lado, 0.50, 0.01)
        ponta = (0.098 * lado, 0.615, 0.0)
        meshes.append(cone_between("orelha", base, ponta, 0.055, pelo, 12))
        meshes.append(cone_between("orelha_interna",
                                   (0.072 * lado, 0.505, 0.015),
                                   (0.093 * lado, 0.59, 0.008), 0.03, rosa, 10))

    for lado in (-1, 1):
        meshes.append(ellipsoid("olho", (0.052 * lado, 0.462, 0.095),
                                (0.024, 0.026, 0.016), verde, 12, 10))
        meshes.append(ellipsoid("pupila", (0.052 * lado, 0.462, 0.107),
                                (0.007, 0.021, 0.008), preto, 10, 8))

    # Listras nas costas — quebram o volume liso na vista de cima.
    for i, z in enumerate((-0.14, -0.055, 0.03)):
        meshes.append(ellipsoid(f"listra_{i}", (0, 0.30 - i * 0.02, z),
                                (0.10, 0.055, 0.022), listra, 16, 10))

    # Patas dianteiras esticadas ate o chao, na frente do corpo.
    for lado in (-1, 1):
        x = 0.068 * lado
        meshes.append(cylinder_between("pata_frente", (x, 0.20, 0.115), (x, 0.028, 0.145), 0.028, pelo, 10))
        meshes.append(ellipsoid("pe_frente", (x, 0.028, 0.163), (0.033, 0.026, 0.045), peito, 14, 10))

    # Cauda enrolando por fora do corpo, apoiada no chao.
    meshes.append(cylinder_between("cauda_1", (0, 0.115, -0.19), (0.10, 0.065, -0.255), 0.026, pelo, 10))
    meshes.append(cylinder_between("cauda_2", (0.10, 0.065, -0.255), (0.20, 0.04, -0.205), 0.023, pelo, 10))
    meshes.append(cylinder_between("cauda_3", (0.20, 0.04, -0.205), (0.245, 0.035, -0.10), 0.020, listra, 10))

    _exportar(meshes, "gato")


# ── Ovelha ────────────────────────────────────────────────────────────────
def make_ovelha():
    """Corpo de la em blocos sobrepostos, cabeca e patas escuras: o contraste
    entre la clara e extremidades escuras e o que identifica a ovelha de cima."""
    meshes = []
    la = (0.90, 0.88, 0.84)
    la_sombra = (0.76, 0.74, 0.70)
    escuro = (0.16, 0.15, 0.16)
    focinho = (0.26, 0.24, 0.25)
    preto = (0.02, 0.018, 0.015)

    # Volume de la: um elipsoide grande mais tufos, para nao virar uma capsula lisa.
    meshes.append(ellipsoid("corpo", (0, 0.305, -0.02), (0.185, 0.165, 0.245), la))
    tufos = [
        ((0, 0.415, 0.075), (0.115, 0.09, 0.10)),
        ((0, 0.415, -0.115), (0.125, 0.095, 0.105)),
        ((0.135, 0.34, -0.02), (0.085, 0.09, 0.135)),
        ((-0.135, 0.34, -0.02), (0.085, 0.09, 0.135)),
        ((0, 0.30, -0.225), (0.115, 0.10, 0.075)),
    ]
    for i, (pos, esc) in enumerate(tufos):
        meshes.append(ellipsoid(f"tufo_{i}", pos, esc, la_sombra if i % 2 else la, 18, 12))

    # Pescoco curto e cabeca escura projetada para a frente e para baixo.
    meshes.append(cylinder_between("pescoco", (0, 0.36, 0.185), (0, 0.315, 0.265), 0.062, escuro, 12))
    meshes.append(ellipsoid("cabeca", (0, 0.305, 0.30), (0.072, 0.075, 0.095), escuro))
    meshes.append(ellipsoid("focinho", (0, 0.275, 0.375), (0.045, 0.045, 0.05), focinho))
    meshes.append(ellipsoid("topete", (0, 0.375, 0.265), (0.072, 0.05, 0.055), la, 16, 12))

    # Orelhas caidas para os lados.
    for lado in (-1, 1):
        orelha = ellipsoid("orelha", (0.082 * lado, 0.335, 0.285),
                           (0.055, 0.022, 0.032), escuro, 14, 10)
        orelha.apply_transform(
            trimesh.transformations.rotation_matrix(-0.35 * lado, [0, 0, 1]))
        meshes.append(orelha)

    for lado in (-1, 1):
        meshes.append(ellipsoid("olho", (0.048 * lado, 0.325, 0.362),
                                (0.013, 0.013, 0.010), preto, 10, 8))

    # Quatro patas finas e escuras.
    for lado in (-1, 1):
        for z, nome in ((0.115, "pata_frente"), (-0.13, "pata_tras")):
            x = 0.098 * lado
            meshes.append(cylinder_between(nome, (x, 0.20, z), (x, 0.022, z), 0.024, escuro, 10))
            meshes.append(ellipsoid("casco", (x, 0.022, z), (0.029, 0.022, 0.032), preto, 12, 8))

    # Cauda curta de la.
    meshes.append(ellipsoid("cauda", (0, 0.30, -0.275), (0.048, 0.055, 0.042), la, 14, 10))

    _exportar(meshes, "ovelha")


if __name__ == "__main__":
    make_rato()
    make_gato()
    make_ovelha()
