"""Color the hand bell model to match assets/itens/sino.png."""
from __future__ import annotations

import sys
from pathlib import Path

import bpy
import numpy as np


def _palette():
    # The reference has a polished brass bell and a dark mahogany handle.
    return {
        "brass": ((0.72, 0.40, 0.095), 0.34, 0.72),
        "mahogany": ((0.115, 0.026, 0.012), 0.54, 0.025),
        "brass_trim": ((0.82, 0.53, 0.17), 0.30, 0.76),
    }


def _material(name, color, roughness, metallic):
    mat = bpy.data.materials.new(f"Sino - {name}")
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def _assign(meshes):
    palette = _palette()
    materials = {name: _material(name, *settings) for name, settings in palette.items()}
    indexes = {name: i for i, name in enumerate(palette)}
    counts = {name: 0 for name in palette}
    points = np.asarray([
        tuple(obj.matrix_world @ vertex.co)
        for obj in meshes for vertex in obj.data.vertices
    ], dtype=np.float64)
    center = points.mean(axis=0)
    axis = np.linalg.eigh(np.cov((points - center).T))[1][:, -1]
    if axis[1] < 0:
        axis *= -1

    for obj in meshes:
        mesh = obj.data
        mesh.materials.clear()
        for material in materials.values():
            mesh.materials.append(material)
        for face in mesh.polygons:
            point = np.asarray(tuple(obj.matrix_world @ face.center), dtype=np.float64)
            along = float(np.dot(point - center, axis))
            # The bell and clapper sit at the negative end of the main axis;
            # the handle runs toward the positive end.
            if along < 0.14:
                name = "brass"
            elif 0.14 <= along < 0.24 or 0.90 <= along < 0.96 or along >= 1.27:
                name = "brass_trim"
            else:
                name = "mahogany"
            face.material_index = indexes[name]
            face.use_smooth = True
            counts[name] += 1

    if min(counts.values()) < 100:
        raise RuntimeError(f"Distribuição de materiais insuficiente: {counts}")
    return counts


def _signature(meshes):
    points = [obj.matrix_world @ vertex.co for obj in meshes for vertex in obj.data.vertices]
    bounds = tuple(min(point[i] for point in points) for i in range(3)) + tuple(
        max(point[i] for point in points) for i in range(3)
    )
    return sum(len(obj.data.vertices) for obj in meshes), sum(
        len(obj.data.polygons) for obj in meshes
    ), bounds


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) != 2:
        raise SystemExit("Uso: ... -- <origem.glb> <destino.glb>")
    source, destination = (Path(value).resolve() for value in args)
    reference = Path(__file__).resolve().parents[1] / "assets" / "itens" / "sino.png"
    if not source.is_file() or not reference.is_file():
        raise FileNotFoundError(source if not source.is_file() else reference)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("O GLB não contém malhas")
    original = _signature(meshes)
    counts = _assign(meshes)

    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = max(meshes, key=lambda obj: len(obj.data.vertices))
    destination.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(destination), export_format="GLB", use_selection=True,
        export_materials="EXPORT", export_normals=True, export_texcoords=True,
        export_cameras=False, export_lights=False,
    )

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(destination))
    exported = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    final = _signature(exported) if exported else None
    if (not exported or final[1] != original[1]
            or not all(abs(a - b) <= 1e-4 for a, b in zip(final[2], original[2]))
            or not any(obj.data.materials for obj in exported)):
        raise RuntimeError(f"Geometria/exportação inesperada: original={original}, saída={final}")
    print(f"Geometria: vértices={final[0]}, faces={final[1]}, bounds={final[2]}; faces por material={counts}")
    print(f"Referência: {reference}; GLB: {destination}")


if __name__ == "__main__":
    main()
