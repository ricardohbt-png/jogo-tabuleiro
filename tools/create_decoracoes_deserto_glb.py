"""Gera o cacto do deserto e ossos semienterrados em Blender.

Para cada peça exporta fonte .blend, modelo .glb, ícone PNG transparente e prévia.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for data in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                 bpy.data.cameras, bpy.data.lights):
        for block in list(data):
            if block.users == 0:
                data.remove(block)


def mat(name, color, roughness=0.88):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    shader = m.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    return m


def uv(name, pos, scale, material, segments=18, rings=10, smooth=True):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                        radius=1, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    for face in obj.data.polygons:
        face.use_smooth = smooth
    return obj


def tube(name, points, radii, material, bevel, resolution=8):
    curve = bpy.data.curves.new(name + " curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = resolution
    curve.bevel_depth = bevel
    curve.bevel_resolution = 3
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for bp, point, radius in zip(spline.bezier_points, points, radii):
        bp.co = point
        bp.radius = radius
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.object
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def cactus_stem(name, center, height, base_radius, green, seed, sides=32):
    rng = random.Random(seed)
    rings = 18
    verts, faces = [], []
    for i in range(rings + 1):
        t = i / rings
        z = center[2] + height * t
        if t < 0.84:
            profile = 0.96 + 0.04 * math.sin(math.pi * t / 0.84)
        else:
            u = (t - 0.84) / 0.16
            profile = math.sqrt(max(0.015, 1.0 - u * u))
        radius = base_radius * profile
        for j in range(sides):
            a = math.tau * j / sides
            rib = 1 + 0.055 * math.cos(a * 11 + 0.2) + 0.012 * math.sin(a * 7 + t * 8)
            verts.append((center[0] + math.cos(a) * radius * rib,
                          center[1] + math.sin(a) * radius * rib,
                          z + (rng.uniform(-0.003, 0.003) if i in (0, rings) else 0)))
    for i in range(rings):
        for j in range(sides):
            a = i * sides + j
            b = i * sides + (j + 1) % sides
            faces.append((a, b, b + sides, a + sides))
    faces.append(tuple(reversed(range(sides))))
    faces.append(tuple(rings * sides + j for j in range(sides)))
    mesh = bpy.data.meshes.new(name + " mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(green)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for face in mesh.polygons:
        face.use_smooth = len(face.vertices) == 4
    return obj


def build_cactus(rng):
    cactus = [mat("Cacto | verde sálvia", (0.16, 0.31, 0.16)),
              mat("Cacto | costelas iluminadas", (0.24, 0.40, 0.21)),
              mat("Cacto | sombra", (0.10, 0.23, 0.13))]
    spine = mat("Espinhos marfim", (0.76, 0.69, 0.48))
    sand = mat("Areia dourada", (0.48, 0.34, 0.17))
    sand_light = mat("Areia clara", (0.68, 0.51, 0.27))
    stone = mat("Pedras do deserto", (0.34, 0.29, 0.21))

    uv("Pequena elevação de areia", (0, 0, 0.045), (0.35, 0.31, 0.09), sand, 22, 10)
    uv("Faixa de areia iluminada", (-0.035, -0.035, 0.095), (0.27, 0.22, 0.035), sand_light, 18, 8)
    for i in range(4):
        a = math.tau * i / 4 + 0.4
        uv("Seixo seco %02d" % i, (math.cos(a) * 0.29, math.sin(a) * 0.23, 0.065),
           (0.055, 0.040, 0.032), stone, 10, 6, smooth=False)

    # Tronco central alto e dois braços erguidos, com junções grossas e curvas.
    cactus_stem("Tronco principal do cacto", (0, 0, 0.10), 0.88, 0.155,
                cactus[0], 902, 36)
    tube("Braço esquerdo | sai do tronco", [(-0.10, 0, 0.36), (-0.24, 0, 0.43),
         (-0.29, 0, 0.59), (-0.29, 0, 0.76)], [1.0, 1.0, 0.96, 0.08],
         cactus[0], 0.077, 10)
    tube("Braço direito | sai do tronco", [(0.105, 0.01, 0.48), (0.235, 0.01, 0.55),
         (0.26, 0.01, 0.69), (0.26, 0.01, 0.83)], [1.0, 1.0, 0.96, 0.08],
         cactus[0], 0.069, 10)

    # Costelas estreitas acompanham o tronco e os braços, sem cobrir a forma.
    for i in range(12):
        a = math.tau * i / 12
        x, y = math.cos(a), math.sin(a)
        pts = [(x * 0.149, y * 0.149, 0.16), (x * 0.158, y * 0.158, 0.47),
               (x * 0.153, y * 0.153, 0.80), (x * 0.145, y * 0.145, 0.93)]
        tube("Costela longitudinal %02d" % i, pts, [0.35, 0.72, 0.72, 0.32],
             cactus[1 if i % 3 else 2], 0.008, 5)

    # Espinhos em pequenos pares, em pontos alternados das costelas.
    for level, z in enumerate((0.22, 0.34, 0.47, 0.60, 0.73, 0.86)):
        for j in range(9):
            a = math.tau * j / 9 + (level % 2) * 0.18
            base = (math.cos(a) * 0.154, math.sin(a) * 0.154, z)
            tip = (math.cos(a) * 0.194, math.sin(a) * 0.194, z + 0.012)
            tube("Espinho do tronco", [base, tip], [1, 0.05], spine, 0.004, 3)
    # Espinhos bem espaçados nos braços.
    for arm_x, arm_z in ((-0.29, 0.52), (-0.29, 0.66), (0.26, 0.64), (0.26, 0.77)):
        for side in (-1, 1):
            tube("Espinho dos braços", [(arm_x, 0, arm_z),
                 (arm_x + side * 0.035, -0.004, arm_z + 0.012)], [1, 0.05], spine, 0.004, 3)


def build_bones(rng):
    sand = [mat("Areia compacta", (0.51, 0.37, 0.19)),
            mat("Duna clara", (0.66, 0.49, 0.27)),
            mat("Areia em sombra", (0.37, 0.27, 0.15))]
    bone = [mat("Osso antigo | marfim", (0.71, 0.63, 0.45)),
            mat("Osso antigo | desgaste", (0.48, 0.39, 0.25)),
            mat("Osso exposto ao sol", (0.82, 0.74, 0.56))]
    socket = mat("Órbita escurecida", (0.12, 0.095, 0.065))
    tooth = mat("Dentes secos", (0.88, 0.78, 0.56))

    # Monte baixo cobre a parte inferior das costelas e dos ossos longos.
    uv("Pequeno monte de areia", (0, 0, 0.055), (0.36, 0.31, 0.095), sand[0], 22, 10)
    uv("Língua de areia clara", (-0.08, -0.075, 0.10), (0.27, 0.19, 0.037), sand[1], 18, 8)
    # Coluna vertebral parcialmente coberta, alinhada ao comprimento do fóssil.
    for i in range(6):
        x = -0.25 + i * 0.085
        uv("Vértebra exposta %02d" % i, (x, 0.055, 0.15 + 0.012 * math.sin(i)),
           (0.052, 0.045, 0.032), bone[1 if i % 3 == 0 else 0], 12, 8)

    # Arcos de costelas de uma criatura grande; as pontas entram na areia.
    for i, x in enumerate((-0.19, -0.08, 0.035, 0.15)):
        width = rng.uniform(0.16, 0.19)
        peak = rng.uniform(0.25, 0.31)
        points = [(x - 0.025, -width, 0.105), (x - 0.01, -width * 0.63, peak * 0.78),
                  (x + 0.015, 0.0, peak), (x + 0.01, width * 0.63, peak * 0.78),
                  (x - 0.02, width, 0.105)]
        tube("Costela semienterrada %02d" % i, points,
             [0.12, 0.9, 1.0, 0.88, 0.12], bone[i % len(bone)], 0.023, 8)

    # Crânio lateral com órbitas, focinho curto, mandíbula e dentes pequenos.
    skull_pos = (0.20, -0.095, 0.17)
    uv("Crânio antigo", skull_pos, (0.145, 0.12, 0.105), bone[0], 16, 10, smooth=False)
    uv("Focinho do crânio", (0.29, -0.115, 0.135), (0.095, 0.083, 0.062), bone[1], 14, 8, smooth=False)
    for side in (-1, 1):
        uv("Órbita vazia", (0.205 + side * 0.055, -0.199, 0.184),
           (0.030, 0.012, 0.027), socket, 12, 8)
        uv("Dente exposto", (0.27 + side * 0.023, -0.192, 0.103),
           (0.012, 0.010, 0.025), tooth, 10, 6, smooth=False)
    tube("Mandíbula parcialmente coberta", [(0.12, -0.16, 0.10), (0.22, -0.19, 0.085),
         (0.32, -0.15, 0.105)], [0.8, 1.0, 0.6], bone[1], 0.018, 6)

    # Um osso longo e partido sai da areia, com extremidades alargadas.
    tube("Osso longo exposto", [(-0.32, -0.17, 0.11), (-0.23, -0.20, 0.16),
         (-0.12, -0.18, 0.18), (0.01, -0.13, 0.13)], [0.75, 1.0, 0.95, 0.65],
         bone[2], 0.024, 7)
    for x, y in ((-0.32, -0.17), (0.01, -0.13)):
        uv("Epífise do osso longo", (x, y, 0.12), (0.045, 0.035, 0.030),
           bone[0], 12, 8)
    # Grãos e lascas de areia parcialmente cobrindo os ossos.
    for i in range(7):
        x, y = rng.uniform(-0.30, 0.30), rng.uniform(-0.25, 0.25)
        uv("Grão de areia aderido %02d" % i, (x, y, rng.uniform(0.10, 0.16)),
           (rng.uniform(0.025, 0.05), 0.026, 0.012), rng.choice(sand), 10, 6)


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def setup_scene(slug):
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 1100
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.10, 0.08, 0.055, 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.32
    for name, loc, energy, size, color in (
        ("Sol quente", (1.0, -1.4, 2.0), 58, 1.25, (1.0, 0.79, 0.53)),
        ("Preenchimento do céu", (-1.4, -0.4, 1.3), 33, 1.2, (0.76, 0.84, 0.91)),
        ("Recorte dourado", (0.15, 1.1, 1.6), 46, 0.9, (1.0, 0.78, 0.47)),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        lamp = bpy.context.object
        lamp.name = name
        lamp.data.energy = energy
        lamp.data.shape = "DISK"
        lamp.data.size = size
        lamp.data.color = color
        point_at(lamp, (0, 0, 0.44 if slug == "cacto_deserto" else 0.19))
    bpy.ops.object.camera_add(location=(1.45, -2.30, 1.65))
    camera = bpy.context.object
    camera.name = "Câmera da miniatura"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 1.42 if slug == "cacto_deserto" else 1.22
    point_at(camera, (0, 0, 0.48 if slug == "cacto_deserto" else 0.19))
    scene.camera = camera
    scene.render.filepath = str(OUT / (slug + "_preview.png"))


def merge_by_material():
    for material in list(bpy.data.materials):
        group = [obj for obj in bpy.context.scene.objects
                 if obj.type == "MESH" and material in obj.data.materials[:]]
        if len(group) < 2:
            continue
        bpy.ops.object.select_all(action="DESELECT")
        for obj in group:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = group[0]
        bpy.ops.object.join()
        group[0].name = "Deserto | " + material.name


def export_one(slug, builder, seed):
    clear_scene()
    builder(random.Random(seed))
    merge_by_material()
    setup_scene(slug)
    bpy.ops.object.select_all(action="DESELECT")
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / (slug + ".blend")))
    bpy.ops.render.render(write_still=True)
    scene = bpy.context.scene
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.filepath = str(OUT / (slug + ".png"))
    bpy.ops.render.render(write_still=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT / (slug + ".glb")),
                              export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True,
                              export_materials="EXPORT")
    print("ASSET_EXPORT", slug, "meshes=", len(meshes))


def build():
    export_one("cacto_deserto", build_cactus, 93021)
    export_one("ossos_semi_enterrados", build_bones, 93037)


if __name__ == "__main__":
    build()
