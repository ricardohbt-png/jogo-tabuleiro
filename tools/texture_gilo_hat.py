"""Aplica textura irregular de couro ao chapéu do Gilo no .blend atual e exporta o modelo oficial.

Não reconstrói nem substitui a geometria do .blend. Executar com Blender 5.1:
  blender --background --python tools/texture_gilo_hat.py
"""
from __future__ import annotations

import math
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
BLEND = ROOT / "assets/models3d/monstros/gilo_dedos_sujos.blend"
GLB = ROOT / "assets/models3d/monstros/gilo_dedos_sujos.glb"
TEXTURE = ROOT / "assets/models3d/monstros/gilo_chapeu_couro.png"
PREVIEW_FRONT = ROOT / "assets/models3d/monstros/gilo_dedos_sujos_preview.png"
PREVIEW_BACK = ROOT / "assets/models3d/monstros/gilo_dedos_sujos_preview_back.png"


def _value_noise(size: int, grid: int, rng: np.random.Generator) -> np.ndarray:
    field = rng.random((grid + 1, grid + 1), dtype=np.float32)
    coord = np.linspace(0, grid, size, endpoint=False, dtype=np.float32)
    x0 = coord.astype(np.int32)
    y0 = coord.astype(np.int32)
    fx = coord - x0
    fy = fx
    # A two-dimensional grid, sampled with smooth bilinear interpolation.
    xx0, yy0 = np.meshgrid(x0, y0)
    xx1 = xx0 + 1
    yy1 = yy0 + 1
    fxx, fyy = np.meshgrid(fx, fy)
    sx = fxx * fxx * (3 - 2 * fxx)
    sy = fyy * fyy * (3 - 2 * fyy)
    a = field[yy0, xx0] * (1 - sx) + field[yy0, xx1] * sx
    b = field[yy1, xx0] * (1 - sx) + field[yy1, xx1] * sx
    return a * (1 - sy) + b * sy


def _make_leather_texture() -> bpy.types.Image:
    size = 1024
    rng = np.random.default_rng(190326)
    broad = _value_noise(size, 5, rng) - 0.5
    medium = _value_noise(size, 19, rng) - 0.5
    mottles = _value_noise(size, 71, rng) - 0.5
    grain = _value_noise(size, 221, rng) - 0.5
    pores = _value_noise(size, 520, rng) - 0.5
    pixel_noise = rng.normal(0, 1.5, (size, size)).astype(np.float32)

    # Several scales create uneven wear and a fine, pebbled leather grain.
    tone = (45 + broad * 26 + medium * 22 + mottles * 17
            + grain * 12 + pores * 8 + pixel_noise)
    fleck = np.clip((mottles * 0.60 + grain * 0.40 - 0.20) * 2.4, 0, 1)
    tone += fleck * 11
    tone = np.clip(tone, 15, 92)
    rgba = np.empty((size, size, 4), dtype=np.float32)
    rgba[:, :, 0] = tone * 1.44 / 255.0
    rgba[:, :, 1] = tone * 0.68 / 255.0
    rgba[:, :, 2] = tone * 0.37 / 255.0
    rgba[:, :, 3] = 1.0

    old_image = bpy.data.images.get("Gilo • couro castanho irregular")
    if old_image is not None:
        bpy.data.images.remove(old_image, do_unlink=True)
    image = bpy.data.images.new("Gilo • couro castanho irregular", width=size,
                                height=size, alpha=True, float_buffer=False)
    image.pixels.foreach_set(rgba.reshape(-1))
    image.filepath_raw = str(TEXTURE)
    image.file_format = "PNG"
    TEXTURE.parent.mkdir(parents=True, exist_ok=True)
    image.save()
    image.pack()
    return image


def _unwrap(obj: bpy.types.Object) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    if not obj.data.uv_layers:
        obj.data.uv_layers.new(name="UVMap")
    else:
        obj.data.uv_layers.active = obj.data.uv_layers[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(island_margin=0.018)
    bpy.ops.object.mode_set(mode="OBJECT")


def _apply_texture(material: bpy.types.Material, image: bpy.types.Image) -> None:
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    bsdf = next((node for node in nodes if node.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    out = next((node for node in nodes if node.type == "OUTPUT_MATERIAL"), None)
    if out is None:
        out = nodes.new("ShaderNodeOutputMaterial")
    if not any(link.from_node == bsdf and link.to_node == out for link in links):
        links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    for link in list(bsdf.inputs["Base Color"].links):
        links.remove(link)
    for old_tex in [node for node in nodes
                    if node.type == "TEX_IMAGE" and node.name == "Gilo • textura irregular de couro"]:
        nodes.remove(old_tex)
    tex = nodes.new("ShaderNodeTexImage")
    tex.name = "Gilo • textura irregular de couro"
    tex.label = "Couro castanho irregular"
    tex.image = image
    tex.interpolation = "Linear"
    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.9
    material.diffuse_color = (0.12, 0.045, 0.018, 1.0)


def _look_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def _bounds(objects):
    pts = [obj.matrix_world @ Vector(corner)
           for obj in objects for corner in obj.bound_box]
    lo = Vector(tuple(min(p[i] for p in pts) for i in range(3)))
    hi = Vector(tuple(max(p[i] for p in pts) for i in range(3)))
    return lo, hi


def _render_preview(objects, destination: Path, side: str, center: Vector, span: float) -> None:
    direction = -1 if side == "front" else 1
    bpy.ops.object.camera_add(location=center + Vector((0.35, direction * 5.0, 1.05)))
    camera = bpy.context.object
    camera.name = f"Gilo preview camera {side} (temporary)"
    _look_at(camera, center + Vector((0, 0, span * 0.02)))
    camera.data.lens = 54
    bpy.context.scene.camera = camera
    for name, offset, energy, size in (
        ("Key", (0.8, direction * 3.0, 3.3), 260, 2.3),
        ("Fill", (-1.8, direction * 2.4, 1.7), 150, 2.0),
        ("Rim", (0.5, -direction * 1.6, 2.7), 180, 1.8),
    ):
        bpy.ops.object.light_add(type="AREA", location=center + Vector(offset))
        light = bpy.context.object
        light.name = f"Gilo preview {side} {name} (temporary)"
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        _look_at(light, center)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 64
    scene.render.resolution_x = 700
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = True
    scene.render.filepath = str(destination)
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    bpy.ops.render.render(write_still=True)
    # Preview cameras and lights are temporary; remove them before the next side.
    bpy.data.objects.remove(camera, do_unlink=True)
    for obj in list(bpy.context.scene.objects):
        if obj.name.endswith("(temporary)") and obj.type == "LIGHT":
            bpy.data.objects.remove(obj, do_unlink=True)


def main() -> None:
    if not BLEND.is_file():
        raise FileNotFoundError(BLEND)
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    hats = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"
            and obj.name in {"Gilo Hat • worn leather floppy brim",
                             "Gilo Hat • sloped leather crown",
                             "Gilo Hat • leather band"}]
    if len(hats) != 3:
        raise RuntimeError(f"Esperadas três peças do chapéu no .blend atual; encontrei {len(hats)}")
    body = next((obj for obj in bpy.context.scene.objects
                 if obj.type == "MESH" and obj.name == "tmpf0q5hfcs.ply"), None)
    if body is None:
        raise RuntimeError("Não encontrei a malha base editada no .blend de Gilo")
    body_counts = (len(body.data.vertices), len(body.data.polygons))
    texture = _make_leather_texture()

    hat_materials = {mat for obj in hats for mat in obj.data.materials if mat}
    for mat in hat_materials:
        if "fivela" in mat.name.lower():
            continue
        _apply_texture(mat, texture)
    for obj in hats:
        _unwrap(obj)

    # Salva as alterações de material/UV no arquivo de trabalho aberto pelo usuário.
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    bpy.ops.export_scene.gltf(
        filepath=str(GLB), export_format="GLB", export_materials="EXPORT",
        export_apply=False, export_texcoords=True, export_normals=True,
        export_tangents=False, export_cameras=False, export_lights=False,
    )
    body_after = (len(body.data.vertices), len(body.data.polygons))
    if body_after != body_counts:
        raise RuntimeError(f"A geometria do corpo mudou inesperadamente: {body_counts} -> {body_after}")

    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    lo, hi = _bounds(meshes)
    center = (lo + hi) * 0.5
    span = max(hi - lo)
    _render_preview(meshes, PREVIEW_FRONT, "front", center, span)
    _render_preview(meshes, PREVIEW_BACK, "back", center, span)
    print("saved_glb", GLB)
    print("saved_texture", TEXTURE)
    print("saved_blend", BLEND)
    print("body_geometry_preserved", body_counts)


if __name__ == "__main__":
    main()
