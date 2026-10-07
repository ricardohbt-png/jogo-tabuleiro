"""Cria uma cabeça monumental de pedra parcialmente soterrada na areia."""
from __future__ import annotations

import math
import random
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)
SLUG = "estatua_soterrada"


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for data in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                 bpy.data.cameras, bpy.data.lights):
        for block in list(data):
            if block.users == 0:
                data.remove(block)


def mat(name, color, roughness=0.92):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    return material


def uv(name, pos, scale, material, segments=20, rings=12, smooth=True):
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


def curve(name, points, radii, material, bevel=0.01):
    path = bpy.data.curves.new(name + " curve", "CURVE")
    path.dimensions = "3D"
    path.resolution_u = 8
    path.bevel_depth = bevel
    path.bevel_resolution = 3
    spline = path.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for bp, point, radius in zip(spline.bezier_points, points, radii):
        bp.co = point
        bp.radius = radius
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, path)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.object
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def build(rng):
    stone = [mat("Arenito antigo | dourado", (0.47, 0.34, 0.20)),
             mat("Arenito antigo | luz", (0.59, 0.45, 0.28)),
             mat("Arenito antigo | sombra", (0.32, 0.24, 0.16)),
             mat("Arenito antigo | pátina", (0.39, 0.39, 0.29))]
    eye_shadow = mat("Sombra das cavidades", (0.18, 0.14, 0.095))
    sand = [mat("Duna | ocre", (0.54, 0.38, 0.19)),
            mat("Duna | face ao sol", (0.70, 0.52, 0.28)),
            mat("Duna | areia escura", (0.41, 0.29, 0.15))]

    # A cabeça está inclinada, desgastada pelo vento; a duna cobre queixo,
    # pescoço e parte da boca, deixando a testa e os olhos acima da areia.
    head_center = (0.0, 0.015, 0.48)
    head = uv("Cabeça monumental semienterrada", head_center,
              (0.255, 0.205, 0.325), stone[0], 24, 16)
    head.rotation_euler[1] = math.radians(-5)
    # Maçãs do rosto e testa modeladas com volumes baixos em vez de uma face lisa.
    uv("Testa esculpida", (0.0, -0.151, 0.615), (0.205, 0.065, 0.115),
       stone[1], 18, 10)
    for side in (-1, 1):
        uv("Maçã do rosto", (side * 0.135, -0.159, 0.43),
           (0.095, 0.060, 0.09), stone[1 if side == 1 else 0], 16, 10)
        uv("Orelha gasta", (side * 0.238, -0.015, 0.49),
           (0.044, 0.052, 0.075), stone[2], 14, 9)
        # Cavidade e pálpebra de pedra dão expressão antiga sem olhos vivos.
        uv("Órbita funda", (side * 0.087, -0.207, 0.525),
           (0.060, 0.020, 0.030), eye_shadow, 14, 8)
        curve("Pálpebra de pedra", [(side * 0.145, -0.223, 0.526),
              (side * 0.087, -0.235, 0.510), (side * 0.030, -0.223, 0.526)],
              [0.35, 1.0, 0.35], stone[2], 0.014)
        curve("Sobrancelha entalhada", [(side * 0.155, -0.214, 0.568),
              (side * 0.090, -0.238, 0.581), (side * 0.025, -0.222, 0.565)],
              [0.35, 1.0, 0.32], stone[1], 0.022)

    # Nariz quebrado pelo tempo, com ponta e narinas parcialmente encobertas.
    uv("Ponte do nariz", (0, -0.227, 0.472), (0.052, 0.074, 0.12),
       stone[1], 16, 10)
    uv("Ponta do nariz partida", (0, -0.275, 0.414), (0.064, 0.050, 0.042),
       stone[0], 14, 8)
    for side in (-1, 1):
        uv("Narina escurecida", (side * 0.030, -0.309, 0.397),
           (0.014, 0.008, 0.010), eye_shadow, 10, 6)

    # Boca severa e sulcos faciais; a linha inferior some dentro da duna.
    curve("Linha da boca", [(-0.095, -0.218, 0.365), (0, -0.244, 0.353),
          (0.095, -0.218, 0.365)], [0.25, 1.0, 0.25], stone[2], 0.012)
    curve("Lábio superior", [(-0.083, -0.221, 0.371), (0, -0.246, 0.382),
          (0.083, -0.221, 0.371)], [0.25, 1.0, 0.25], stone[1], 0.014)

    # Cocar de placas quebradas sugere uma escultura de civilização antiga.
    uv("Faixa de cocar", (0, -0.005, 0.695), (0.255, 0.206, 0.066),
       stone[2], 20, 10)
    for side in (-1, 1):
        for i in range(3):
            z = 0.59 - i * 0.090
            y = -0.175 + i * 0.008
            panel = uv("Placa lateral do cocar", (side * (0.207 - i * 0.025), y, z),
                       (0.052, 0.048, 0.082), stone[2 if i % 2 == 0 else 0], 12, 8,
                       smooth=False)
            panel.rotation_euler[1] = side * math.radians(-8)

    # Rachaduras estreitas e lascas removidas na testa e nas têmporas.
    cracks = [([(-0.17, -0.196, 0.66), (-0.13, -0.211, 0.625),
                (-0.145, -0.207, 0.594)], 0.005),
              ([(0.18, -0.177, 0.60), (0.15, -0.203, 0.574),
                (0.17, -0.195, 0.55)], 0.004),
              ([(-0.21, -0.14, 0.49), (-0.18, -0.20, 0.46),
                (-0.19, -0.19, 0.43)], 0.004)]
    for i, (points, width) in enumerate(cracks):
        curve("Fissura no arenito %02d" % i, points, [0.35, 1.0, 0.1], stone[2], width)

    # Duna frontal alta e ondulada soterrra a base da estátua.
    uv("Duna envolvendo a cabeça", (0.0, -0.025, 0.205),
       (0.365, 0.315, 0.195), sand[0], 24, 12)
    uv("Língua de areia à esquerda", (-0.20, -0.17, 0.17),
       (0.20, 0.205, 0.105), sand[1], 18, 9)
    uv("Língua de areia à direita", (0.22, 0.06, 0.155),
       (0.18, 0.21, 0.095), sand[2], 18, 9)
    # Pequenos fragmentos de pedra quase perdidos na areia.
    for i in range(9):
        x, y = rng.uniform(-0.34, 0.34), rng.uniform(-0.25, 0.25)
        z = rng.uniform(0.105, 0.20)
        chip = uv("Fragmento de arenito soterrado %02d" % i, (x, y, z),
                  (rng.uniform(0.025, 0.052), 0.025, 0.018),
                  rng.choice(sand), 9, 6, smooth=False)
        chip.rotation_euler[2] = rng.uniform(-0.9, 0.9)


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def setup_scene():
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
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.30
    for name, loc, energy, size, color in (
        ("Sol quente", (1.0, -1.4, 2.0), 52, 1.25, (1.0, 0.79, 0.53)),
        ("Preenchimento do céu", (-1.4, -0.4, 1.3), 30, 1.2, (0.76, 0.84, 0.91)),
        ("Recorte dourado", (0.15, 1.1, 1.6), 42, 0.9, (1.0, 0.78, 0.47)),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        lamp = bpy.context.object
        lamp.name = name
        lamp.data.energy = energy
        lamp.data.shape = "DISK"
        lamp.data.size = size
        lamp.data.color = color
        point_at(lamp, (0, 0, 0.37))
    bpy.ops.object.camera_add(location=(1.45, -2.30, 1.65))
    camera = bpy.context.object
    camera.name = "Câmera da miniatura"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 1.32
    point_at(camera, (0, 0, 0.38))
    scene.camera = camera
    scene.render.filepath = str(OUT / (SLUG + "_preview.png"))


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


def export():
    clear_scene()
    build(random.Random(96021))
    merge_by_material()
    setup_scene()
    bpy.ops.object.select_all(action="DESELECT")
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / (SLUG + ".blend")))
    bpy.ops.render.render(write_still=True)
    scene = bpy.context.scene
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.filepath = str(OUT / (SLUG + ".png"))
    bpy.ops.render.render(write_still=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT / (SLUG + ".glb")),
                              export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True,
                              export_materials="EXPORT")
    print("ASSET_EXPORT", SLUG, "meshes=", len(meshes))


if __name__ == "__main__":
    export()
