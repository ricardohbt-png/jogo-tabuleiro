"""Gera miniaturas 3D de juncos e raízes retorcidas para o pântano.

Cada decoração recebe um projeto Blender editável, GLB para o tabuleiro,
PNG transparente para o editor/visão 2D e uma imagem de prévia iluminada.
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


def assign(obj, material):
    obj.data.materials.append(material)
    return obj


def ellipsoid(name, pos, scale, material, segments=16, rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                        radius=1, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, material)
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def tapered_stem(name, points, radii, material, resolution=3, bevel=0.018):
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


def blade(name, base, tip, width, material, bend=(0, 0, 0)):
    """Fita estreita e facetada com ponta afilada, sem sobreposição de faces."""
    b, t = Vector(base), Vector(tip)
    direction = t - b
    side = direction.cross(Vector((0, 1, 0)))
    if side.length < 1e-5:
        side = direction.cross(Vector((1, 0, 0)))
    side.normalize()
    mid = b + direction * 0.50 + Vector(bend)
    verts = [tuple(b - side * width * 0.28), tuple(b + side * width * 0.28),
             tuple(mid - side * width * 0.50), tuple(mid + side * width * 0.50),
             tuple(t)]
    mesh = bpy.data.meshes.new(name + " mesh")
    mesh.from_pydata(verts, [], [(0, 1, 3, 2), (2, 3, 4)])
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def build_reeds(rng):
    greens = [mat("Junco | verde oliva", (0.18, 0.24, 0.075)),
              mat("Junco | verde úmido", (0.25, 0.31, 0.10)),
              mat("Junco | verde jovem", (0.34, 0.37, 0.13))]
    stalks = [mat("Haste de junco | verde escuro", (0.16, 0.21, 0.065)),
              mat("Haste de junco | oliva", (0.30, 0.31, 0.10))]
    cattails = [mat("Espiga | marrom profundo", (0.20, 0.095, 0.040)),
                mat("Espiga | castanho quente", (0.34, 0.16, 0.055))]
    base_moss = mat("Turfa na base", (0.12, 0.15, 0.07))
    ellipsoid("Pequena touceira de turfa", (0, 0, 0.055),
              (0.28, 0.24, 0.075), base_moss, 20, 10)
    # Folhas arqueadas em camadas dão volume, mas deixam o centro arejado.
    for i in range(13):
        a = math.tau * i / 13 + rng.uniform(-0.20, 0.20)
        radius = rng.uniform(0.075, 0.24)
        height = rng.uniform(0.42, 0.73)
        base = (math.cos(a) * radius * 0.28, math.sin(a) * radius * 0.28, 0.08)
        tip = (math.cos(a) * radius * 1.8, math.sin(a) * radius * 1.8,
               height * rng.uniform(0.82, 1.0))
        bend = (math.cos(a) * rng.uniform(0.035, 0.12),
                math.sin(a) * rng.uniform(0.035, 0.12), 0)
        blade("Folha longa de junco %02d" % i, base, tip,
              rng.uniform(0.035, 0.065), rng.choice(greens), bend)
    # Hastes altas de espessura real, com espigas ovais identificáveis em miniatura.
    reed_count = 8
    for i in range(reed_count):
        a = math.tau * i / reed_count + rng.uniform(-0.22, 0.22)
        radius = rng.uniform(0.025, 0.15)
        height = rng.uniform(0.64, 0.92)
        lean = rng.uniform(-0.10, 0.10)
        x, y = math.cos(a) * radius, math.sin(a) * radius
        stem_mat = rng.choice(stalks)
        tapered_stem("Haste vertical %02d" % i,
                      [(x, y, 0.08), (x + lean * 0.45, y, height * 0.56),
                       (x + lean, y, height)],
                      [1.0, 0.9, 0.7], stem_mat, bevel=rng.uniform(0.012, 0.018))
        if i < 5:
            cat_height = rng.uniform(0.12, 0.18)
            cat = ellipsoid("Espiga cilíndrica de junco %02d" % i,
                            (x + lean, y, height + cat_height * 0.22),
                            (0.027, 0.027, cat_height), rng.choice(cattails), 14, 10)
            cat.rotation_euler[1] = -lean * 0.8
            # Pequeno colar claro marca o encontro da espiga com a haste.
            ellipsoid("Colar da espiga", (x + lean, y, height - 0.012),
                      (0.022, 0.022, 0.018), greens[2], 12, 8)
    # Folhinhas baixas e musgo pontuam a base sem formar uma plataforma opaca.
    for i in range(8):
        a = math.tau * i / 8
        ellipsoid("Tufo baixo", (math.cos(a) * 0.17, math.sin(a) * 0.15, 0.065),
                  (0.055, 0.038, 0.025), greens[i % len(greens)], 12, 8)


def build_roots(rng):
    woods = [mat("Raiz encharcada | marrom escuro", (0.105, 0.060, 0.033)),
             mat("Raiz encharcada | castanho", (0.19, 0.105, 0.052)),
             mat("Raiz velha | cinza castanho", (0.27, 0.20, 0.12)),
             mat("Fenda escura na madeira", (0.055, 0.040, 0.025))]
    mosses = [mat("Musgo de raiz | verde profundo", (0.08, 0.14, 0.045)),
              mat("Musgo de raiz | verde oliva", (0.18, 0.23, 0.065))]
    mud = mat("Lodo preso nas raízes", (0.105, 0.115, 0.065))
    ellipsoid("Lama achatada sob o emaranhado", (0, 0, 0.035),
              (0.84, 0.36, 0.045), mud, 24, 10)
    # Raízes grossas serpenteiam no chão e se cruzam; terminações afiladas
    # preservam a leitura de madeira retorcida em escala de miniatura.
    for i in range(7):
        y = -0.27 + i * 0.09
        phase = rng.uniform(-0.16, 0.16)
        z = rng.uniform(0.075, 0.14)
        points = [(-0.84, y + phase, z), (-0.54, y - phase * 0.4, z + 0.055),
                  (-0.23, y + phase, z + rng.uniform(0.06, 0.16)),
                  (0.14, y - phase, z + rng.uniform(0.015, 0.11)),
                  (0.49, y + phase * 0.5, z + 0.075), (0.82, y + phase, z + 0.02)]
        radius = rng.uniform(0.040, 0.070)
        tapered_stem("Raiz serpenteante %02d" % i, points,
                      [1.45, 1.20, 0.92, 0.78, 0.52, 0.06],
                      rng.choice(woods[:3]), bevel=radius)
    # Raízes arqueadas mais altas criam uma silhueta irregular e pontes naturais.
    for i in range(5):
        x = -0.60 + i * 0.30
        direction = rng.choice((-1, 1))
        y = rng.uniform(-0.20, 0.20)
        peak = rng.uniform(0.25, 0.38)
        points = [(x - 0.23, y, 0.10), (x - 0.12, y + direction * 0.10, peak * 0.77),
                  (x + 0.02, y + direction * 0.16, peak),
                  (x + 0.18, y + direction * 0.06, peak * 0.55),
                  (x + 0.29, y - direction * 0.08, 0.105)]
        tapered_stem("Arco de raiz nodosa %02d" % i, points,
                      [0.92, 1.18, 1.0, 0.72, 0.10],
                      rng.choice(woods[:3]), bevel=rng.uniform(0.035, 0.053))
    # Raízes secundárias finas e quebradas saem das laterais.
    for i in range(10):
        x = rng.uniform(-0.74, 0.72)
        side = rng.choice((-1, 1))
        y = side * rng.uniform(0.18, 0.29)
        z = rng.uniform(0.075, 0.14)
        points = [(x - 0.09, y * 0.55, z), (x, y, z + rng.uniform(0.015, 0.07)),
                  (x + rng.uniform(0.10, 0.24), side * rng.uniform(0.29, 0.38), 0.055)]
        tapered_stem("Raiz fina lateral %02d" % i, points,
                      [0.72, 0.48, 0.04], rng.choice(woods[:3]),
                      bevel=rng.uniform(0.014, 0.024))
    # Musgo em manchas pequenas, encaixadas no topo das raízes.
    for i in range(13):
        x = rng.uniform(-0.69, 0.70)
        y = rng.uniform(-0.26, 0.25)
        z = rng.uniform(0.14, 0.29)
        ellipsoid("Almofada de musgo %02d" % i, (x, y, z),
                  (rng.uniform(0.045, 0.095), rng.uniform(0.030, 0.055),
                   rng.uniform(0.012, 0.026)), rng.choice(mosses), 12, 8)


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def setup_camera(slug):
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
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.08, 0.10, 0.09, 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.36
    for name, loc, energy, size, color in (
        ("Luz quente", (1.0, -1.4, 2.0), 65, 1.3, (1.0, 0.83, 0.63)),
        ("Preenchimento frio", (-1.4, -0.3, 1.1), 34, 1.3, (0.68, 0.86, 0.78)),
        ("Recorte de névoa", (0.2, 1.0, 1.5), 52, 0.9, (0.79, 0.92, 0.76)),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        lamp = bpy.context.object
        lamp.name = name
        lamp.data.energy = energy
        lamp.data.shape = "DISK"
        lamp.data.size = size
        lamp.data.color = color
        point_at(lamp, (0, 0, 0.32))
    bpy.ops.object.camera_add(location=(1.45, -2.30, 1.70))
    camera = bpy.context.object
    camera.name = "Câmera da miniatura"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 1.35 if slug == "juncos" else 2.05
    point_at(camera, (0, 0, 0.43 if slug == "juncos" else 0.24))
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
        group[0].name = "Brejo | " + material.name


def export_one(slug, builder):
    clear_scene()
    builder(random.Random(74021 if slug == "juncos" else 74037))
    merge_by_material()
    setup_camera(slug)
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
    export_one("juncos", build_reeds)
    export_one("raizes_torcidas", build_roots)


if __name__ == "__main__":
    build()
