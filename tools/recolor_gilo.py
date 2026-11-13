"""Cria a miniatura 3D de Gilo a partir do Bandido sem sobrescrever o original.

Executar da raiz do projeto:
  blender --background --python tools/recolor_gilo.py
"""
from __future__ import annotations

import math
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/models3d/monstros/bandido.glb"
CROSSBOW = ROOT / "assets/itens/besta.glb"
OUTPUT = ROOT / "assets/models3d/monstros/gilo_dedos_sujos.glb"
BLEND = ROOT / "assets/models3d/monstros/gilo_dedos_sujos.blend"
ALBEDO = ROOT / "assets/models3d/monstros/gilo_dedos_sujos_albedo.png"
PREVIEW_FRONT = ROOT / "assets/models3d/monstros/gilo_dedos_sujos_preview.png"
PREVIEW_BACK = ROOT / "assets/models3d/monstros/gilo_dedos_sujos_preview_back.png"


def _look_at(obj, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def _bounds(objects):
    points = [obj.matrix_world @ Vector(corner)
              for obj in objects for corner in obj.bound_box]
    lo = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    hi = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return lo, hi


def _make_leather(name: str, color, roughness=0.86):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def _recolor_source_texture(meshes):
    changed = set()
    for obj in meshes:
        for material in obj.data.materials:
            if not material or not material.use_nodes:
                continue
            for node in material.node_tree.nodes:
                if node.type != "TEX_IMAGE" or not node.image or node.image.name in changed:
                    continue
                image = node.image
                width, height = image.size
                pixels = np.empty(width * height * 4, dtype=np.float32)
                image.pixels.foreach_get(pixels)
                rgba = pixels.reshape((height, width, 4))
                rgb = rgba[:, :, :3]
                r, g, b = rgb[:, :, 0].copy(), rgb[:, :, 1].copy(), rgb[:, :, 2].copy()
                lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
                spread = rgb.max(axis=2) - rgb.min(axis=2)
                visible = rgb.max(axis=2) > 0.025
                # A cor dourada do couro também se parece com pele. Protege pele
                # apenas nas ilhas UV do rosto e das mãos do Bandido.
                skin_region = np.zeros((height, width), dtype=bool)
                for x0, y0, x1, y1 in ((270, 45, 470, 290), (135, 570, 250, 700),
                                      (650, 585, 775, 710), (1025, 580, 1135, 700),
                                      (1660, 580, 1785, 705)):
                    skin_region[y0:y1, x0:x1] = True
                skin_tone = (r > g * 1.10) & (g > b * 1.05) & (r > 0.24) & (g > 0.10)
                skin = skin_region & skin_tone & visible
                cloth = visible & ~skin

                # Escurece couro e tecido para castanho profundo; preserva ouro
                # saturado em detalhes e mantém pele totalmente intacta.
                gold = cloth & (r > g * 1.25) & (g > b * 1.18) & (spread > 0.16)
                dark_cloth = cloth & ~gold
                rgb[:, :, 0][dark_cloth] = np.clip(r[dark_cloth] * 0.43 + 0.004, 0, 1)
                rgb[:, :, 1][dark_cloth] = np.clip(g[dark_cloth] * 0.30 + 0.002, 0, 1)
                rgb[:, :, 2][dark_cloth] = np.clip(b[dark_cloth] * 0.20 + 0.001, 0, 1)
                rgb[:, :, 0][gold] = np.clip(r[gold] * 0.62, 0, 1)
                rgb[:, :, 1][gold] = np.clip(g[gold] * 0.46, 0, 1)
                rgb[:, :, 2][gold] = np.clip(b[gold] * 0.30, 0, 1)
                neutral = dark_cloth & (spread < 0.11)
                warm = np.clip(lum * 0.50, 0, 1)
                rgb[:, :, 0][neutral] = warm[neutral] * 0.70 + 0.009
                rgb[:, :, 1][neutral] = warm[neutral] * 0.40 + 0.003
                rgb[:, :, 2][neutral] = warm[neutral] * 0.24 + 0.001

                image.pixels.foreach_set(rgba.reshape(-1))
                image.file_format = "PNG"
                image.filepath_raw = str(ALBEDO)
                ALBEDO.parent.mkdir(parents=True, exist_ok=True)
                image.save()
                image.pack()
                image.name = "Gilo roupas marrons escuras"
                changed.add(image.name)
    if not changed:
        raise RuntimeError("Não encontrei textura pintada no GLB do Bandido")
    print("recolored textures", len(changed))


def _point_in_polygon(x, y, polygon):
    inside = False
    j = len(polygon) - 1
    for i, (xi, yi) in enumerate(polygon):
        xj, yj = polygon[j]
        if ((yi > y) != (yj > y)) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
            inside = not inside
        j = i
    return inside


def _remove_hand_dagger_faces(meshes):
    # Polígonos traçados sobre os dois atlas UV do Bandido. Só as lâminas são
    # removidas; mãos, punhos, braços e a besta presa às costas são mantidos.
    atlas_masks = (
        [(526, 846), (545, 824), (579, 806), (625, 789), (672, 772),
         (704, 758), (728, 767), (736, 783), (718, 798), (680, 817),
         (640, 836), (599, 853), (561, 872)],
        [(1261, 738), (1280, 727), (1312, 746), (1352, 775), (1395, 806),
         (1428, 837), (1424, 854), (1401, 849), (1364, 825), (1327, 796),
         (1294, 769), (1272, 756)],
    )
    width, height = 2048, 1536
    removed = 0
    for obj in meshes:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.active
        if uv_layer is None:
            bm.free()
            continue
        faces = []
        for face in bm.faces:
            u = sum(loop[uv_layer].uv.x for loop in face.loops) / len(face.loops)
            v = sum(loop[uv_layer].uv.y for loop in face.loops) / len(face.loops)
            px, py = u * width, (1.0 - v) * height
            if any(_point_in_polygon(px, py, mask) for mask in atlas_masks):
                faces.append(face)
        if faces:
            removed += len(faces)
            bmesh.ops.delete(bm, geom=faces, context="FACES")
            bm.to_mesh(obj.data)
            obj.data.update()
        bm.free()
    if removed < 80:
        raise RuntimeError(f"A máscara UV não encontrou as lâminas esperadas ({removed} faces)")
    print("removed dagger blade faces", removed)


def _add_hat():
    leather = _make_leather("Gilo • couro castanho do chapéu", (0.055, 0.020, 0.008))
    band_mat = _make_leather("Gilo • faixa de couro", (0.022, 0.008, 0.003))
    gold = _make_leather("Gilo • fivela envelhecida", (0.35, 0.20, 0.055), roughness=0.55)

    # Aba larga de couro gasta: ondulação irregular e queda na frente.
    n = 64
    center_x, center_y, brim_z = -0.015, -0.120, 0.820
    rx, ry = 0.390, 0.315
    vertices = []
    for layer, dz in ((0, -0.018), (1, 0.018)):
        for i in range(n):
            a = 2 * math.pi * i / n
            wave = 0.014 * math.sin(3 * a + 0.7) + 0.008 * math.sin(5 * a - 0.4)
            x = (rx + wave) * math.cos(a)
            y = (ry + wave) * math.sin(a)
            droop = 0.048 * (y / ry) + wave * 0.55
            vertices.append((center_x + x, center_y + y, brim_z + dz + droop))
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    faces.append(tuple(range(n, 2 * n)))
    brim_mesh = bpy.data.meshes.new("Gilo hat brim geometry")
    brim_mesh.from_pydata(vertices, [], faces)
    brim_mesh.update()
    brim = bpy.data.objects.new("Gilo Hat • worn leather floppy brim", brim_mesh)
    bpy.context.collection.objects.link(brim)
    brim.data.materials.append(leather)

    # Copa inclinada e afunilada, como o chapéu de couro da referência.
    rings = ((0.830, 0.205, 0.165), (0.905, 0.157, 0.132), (0.985, 0.098, 0.090))
    crown_vertices = []
    for ring_index, (z, crx, cry) in enumerate(rings):
        t = ring_index / (len(rings) - 1)
        tilt_x = 0.045 * t
        tilt_y = 0.028 * t
        for i in range(n):
            a = 2 * math.pi * i / n
            crown_vertices.append((center_x + tilt_x + crx * math.cos(a),
                                   center_y + tilt_y + cry * math.sin(a), z))
    crown_faces = []
    for ring_index in range(len(rings) - 1):
        lower = ring_index * n
        upper = (ring_index + 1) * n
        for i in range(n):
            j = (i + 1) % n
            crown_faces.append((lower + i, lower + j, upper + j, upper + i))
    crown_faces.append(tuple(range((len(rings) - 1) * n, len(rings) * n)))
    crown_mesh = bpy.data.meshes.new("Gilo hat sloped crown geometry")
    crown_mesh.from_pydata(crown_vertices, [], crown_faces)
    crown_mesh.update()
    crown = bpy.data.objects.new("Gilo Hat • sloped leather crown", crown_mesh)
    bpy.context.collection.objects.link(crown)
    crown.data.materials.append(leather)

    # Faixa frontal e fivela pequena, mantidas dentro do contorno do capuz.
    bpy.ops.mesh.primitive_torus_add(major_segments=48, minor_segments=8,
                                     location=(center_x, center_y - 0.002, 0.855),
                                     major_radius=0.142, minor_radius=0.010)
    band = bpy.context.object
    band.name = "Gilo Hat • leather band"
    band.scale.y = 0.86
    band.data.materials.append(band_mat)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(center_x, center_y - 0.142, 0.856))
    buckle = bpy.context.object
    buckle.name = "Gilo Hat • brass buckle"
    buckle.dimensions = (0.052, 0.018, 0.038)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    buckle.data.materials.append(gold)
    return [brim, crown, band, buckle]


def _import_hand_crossbow(label, location, rotation):
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(CROSSBOW))
    created = [obj for obj in bpy.context.scene.objects if obj not in before]
    meshes = [obj for obj in created if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError(f"A besta não contém malhas: {CROSSBOW}")
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bow = bpy.context.view_layer.objects.active
    bow.name = f"Gilo Hand Crossbow • {label}"
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    bow.rotation_euler = rotation
    bow.scale = (0.22, 0.22, 0.22)
    bow.location = location
    for obj in created:
        if obj != bow and obj.name in bpy.data.objects:
            bpy.data.objects.remove(obj, do_unlink=True)
    return bow


def _render_preview(meshes, output: Path, side: str, center, span):
    direction = -1 if side == "front" else 1
    bpy.ops.object.camera_add(location=center + Vector((0.35, direction * 5.0, 1.05)))
    camera = bpy.context.object
    camera.name = f"Gilo preview camera {side}"
    _look_at(camera, center + Vector((0, 0, (span) * 0.02)))
    camera.data.lens = 54
    bpy.context.scene.camera = camera
    for name, offset, energy, size in (
        ("Key", (0.8, direction * 3.0, 3.3), 260, 2.3),
        ("Fill", (-1.8, direction * 2.4, 1.7), 150, 2.0),
        ("Rim", (0.5, -direction * 1.6, 2.7), 180, 1.8),
    ):
        bpy.ops.object.light_add(type="AREA", location=center + Vector(offset))
        light = bpy.context.object
        light.name = f"Gilo preview {side} {name}"
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
    scene.render.filepath = str(output)
    scene.world = bpy.data.worlds.new(f"Gilo preview world {side}")
    scene.world.color = (0.012, 0.010, 0.009)
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)


def main():
    for path in (SOURCE, CROSSBOW):
        if not path.is_file():
            raise FileNotFoundError(path)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(SOURCE))
    body = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not body:
        raise RuntimeError("O GLB do Bandido não contém malha")
    original_geometry = [(obj.name, len(obj.data.vertices), len(obj.data.polygons)) for obj in body]
    _recolor_source_texture(body)
    _remove_hand_dagger_faces(body)

    accessories = _add_hat()
    left_bow = _import_hand_crossbow("mão esquerda", ((-0.395, -0.40, 0.210)),
                                     (math.pi / 2, -0.18, -0.20))
    right_bow = _import_hand_crossbow("mão direita", ((0.395, -0.46, 0.165)),
                                      (math.pi / 2, 0.20, 0.24))
    accessories.extend((left_bow, right_bow))

    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    lo, hi = _bounds(meshes)
    center = (lo + hi) * 0.5
    span = max(hi - lo)
    print("base geometry", original_geometry)
    print("variant bounds", lo[:], hi[:], "size", (hi - lo)[:])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    bpy.ops.export_scene.gltf(
        filepath=str(OUTPUT), export_format="GLB", export_materials="EXPORT",
        export_apply=False, export_texcoords=True, export_normals=True,
        export_tangents=False, export_cameras=False, export_lights=False,
    )
    _render_preview(meshes, PREVIEW_FRONT, "front", center, span)
    _render_preview(meshes, PREVIEW_BACK, "back", center, span)
    print("saved_glb", OUTPUT)
    print("saved_blend", BLEND)
    print("saved_albedo", ALBEDO)
    print("saved_preview", PREVIEW_FRONT)
    print("saved_back_preview", PREVIEW_BACK)


if __name__ == "__main__":
    main()


