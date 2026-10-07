"""Gera miniaturas 3D de arbusto seco e capim amarelado."""
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


def mat(name, color, roughness=0.9):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    return material


def ellipsoid(name, pos, scale, material, segments=14, rings=8, smooth=True):
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


def branch(name, points, radii, material, bevel=0.018):
    curve = bpy.data.curves.new(name + " curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 8
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
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.object
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def build_dry_bush(rng):
    bark = [mat("Galho seco | castanho", (0.24, 0.13, 0.055)),
            mat("Galho seco | sol queimado", (0.39, 0.23, 0.095)),
            mat("Galho seco | sombra", (0.15, 0.085, 0.04))]
    leaves = [mat("Folhas ressecadas | ocre", (0.58, 0.37, 0.12)),
              mat("Folhas ressecadas | palha", (0.72, 0.52, 0.22)),
              mat("Folhas ressecadas | ferrugem", (0.42, 0.20, 0.065))]
    sand = mat("Areia sob o arbusto", (0.49, 0.34, 0.17))
    stone = mat("Seixos áridos", (0.32, 0.27, 0.19))
    ellipsoid("Pequeno monte de areia", (0, 0, 0.045), (0.34, 0.29, 0.075),
              sand, 20, 9)
    # Galhos principais torcidos e assimétricos, saindo de uma base seca.
    for i in range(7):
        a = math.tau * i / 7 + rng.uniform(-0.28, 0.28)
        reach = rng.uniform(0.20, 0.32)
        height = rng.uniform(0.34, 0.57)
        x, y = math.cos(a) * reach, math.sin(a) * reach
        start = (rng.uniform(-0.06, 0.06), rng.uniform(-0.05, 0.05), 0.075)
        mid = (x * 0.37 + rng.uniform(-0.055, 0.055),
               y * 0.37 + rng.uniform(-0.055, 0.055), height * 0.48)
        end = (x, y, height)
        twig = rng.choice(bark)
        branch("Galho seco principal %02d" % i, [start, mid, end],
               [1.0, 0.70, 0.12], twig, rng.uniform(0.015, 0.024))
        # Bifurcações finas e curvas quebradas nas extremidades.
        for j in range(2):
            side = -1 if j == 0 else 1
            branch("Ramificação quebradiça %02d-%d" % (i, j),
                   [mid, (mid[0] + side * 0.08, mid[1] + side * 0.018, mid[2] + 0.07),
                    (x + side * 0.07, y - side * 0.035, height + rng.uniform(0.04, 0.12))],
                   [0.85, 0.48, 0.035], twig, 0.010)
        # Poucas folhas enroladas permanecem presas, sem virar uma moita verde.
        for j in range(3):
            t = rng.uniform(0.58, 1.0)
            px = mid[0] * (1 - t) + x * t
            py = mid[1] * (1 - t) + y * t
            pz = mid[2] * (1 - t) + height * t + rng.uniform(0.015, 0.075)
            leaf = ellipsoid("Folha seca enrolada", (px, py, pz),
                             (rng.uniform(0.025, 0.047), 0.013, 0.009),
                             rng.choice(leaves), 10, 6)
            leaf.rotation_euler[1] = rng.uniform(-0.9, 0.9)
            leaf.rotation_euler[2] = a + rng.uniform(-1.2, 1.2)
    # Espinhos curtos e pedras pequenas reforçam o aspecto áspero do arbusto.
    for i in range(8):
        a = math.tau * i / 8
        pos = (math.cos(a) * 0.20, math.sin(a) * 0.20, rng.uniform(0.15, 0.43))
        tip = (pos[0] + math.cos(a) * 0.055, pos[1] + math.sin(a) * 0.055, pos[2] + 0.018)
        branch("Espinho seco", [pos, tip], [1.0, 0.03], bark[2], 0.005)
    for i in range(3):
        a = i * math.tau / 3 + 0.3
        ellipsoid("Pedra do deserto", (math.cos(a) * 0.31, math.sin(a) * 0.25, 0.055),
                  (0.045, 0.035, 0.025), stone, 9, 6, smooth=False)


def build_yellow_grass(rng):
    straw = [mat("Capim seco | palha dourada", (0.68, 0.49, 0.18)),
             mat("Capim seco | amarelo pálido", (0.82, 0.65, 0.30)),
             mat("Capim seco | sombra ocre", (0.48, 0.31, 0.10))]
    stem_mat = mat("Hastes envelhecidas", (0.46, 0.34, 0.13))
    sand = mat("Tufo de areia", (0.48, 0.34, 0.17))
    seed_mats = [mat("Sementes maduras", (0.57, 0.36, 0.10)),
                 mat("Sementes claras", (0.76, 0.57, 0.24))]
    ellipsoid("Base baixa de areia", (0, 0, 0.035), (0.30, 0.26, 0.055),
              sand, 18, 8)
    # Folhas em leque, com alturas e inclinações variadas para criar uma silhueta
    # seca e aérea, atravessável sem parecer um arbusto bloqueador.
    blades = 24
    for i in range(blades):
        a = math.tau * i / blades + rng.uniform(-0.13, 0.13)
        reach = rng.uniform(0.11, 0.31)
        height = rng.uniform(0.28, 0.52)
        side = rng.uniform(-0.045, 0.045)
        x, y = math.cos(a) * reach, math.sin(a) * reach
        z0 = 0.065
        bend_x, bend_y = math.cos(a) * side, math.sin(a) * side
        color = rng.choice(straw)
        branch("Folha arqueada de capim %02d" % i,
               [(0, 0, z0), (x * 0.34, y * 0.34, height * 0.49),
                (x * 0.80 + bend_x, y * 0.80 + bend_y, height * 0.83),
                (x, y, height)],
               [0.8, 1.0, 0.52, 0.025], color, rng.uniform(0.010, 0.016))
    # Hastes florais centrais com espiguetas miúdas, tom sobre tom.
    for i in range(6):
        a = math.tau * i / 6 + rng.uniform(-0.22, 0.22)
        h = rng.uniform(0.42, 0.57)
        x, y = math.cos(a) * rng.uniform(0.025, 0.11), math.sin(a) * rng.uniform(0.025, 0.11)
        branch("Haste com sementes %02d" % i,
               [(0, 0, 0.065), (x * 0.6, y * 0.6, h * 0.55),
                (x, y, h)], [0.8, 0.72, 0.25], stem_mat, 0.009)
        for j in range(4):
            z = h - 0.095 + j * 0.028
            offset = (j - 1.5) * 0.019
            seed = ellipsoid("Espigueta madura", (x + math.cos(a) * offset,
                              y + math.sin(a) * offset, z),
                             (0.012, 0.012, 0.024), seed_mats[(i + j) % 2], 9, 6)
            seed.rotation_euler[1] = 0.32 * math.sin(j + i)


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
        point_at(lamp, (0, 0, 0.34 if slug == "arbusto_seco" else 0.25))
    bpy.ops.object.camera_add(location=(1.45, -2.30, 1.65))
    camera = bpy.context.object
    camera.name = "Câmera da miniatura"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 1.25 if slug == "arbusto_seco" else 1.18
    point_at(camera, (0, 0, 0.34 if slug == "arbusto_seco" else 0.28))
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
        group[0].name = "Vegetação do deserto | " + material.name


def export_one(slug, build, seed):
    clear_scene()
    build(random.Random(seed))
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
    export_one("arbusto_seco", build_dry_bush, 95021)
    export_one("capim_amarelado", build_yellow_grass, 95037)


if __name__ == "__main__":
    build()
