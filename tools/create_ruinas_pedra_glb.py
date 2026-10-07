"""Gera uma miniatura 3D de ruínas de pedra com muralha e colunas partidas."""
from __future__ import annotations

import math
import random
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)
SLUG = "ruinas_pedra"


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for data in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                 bpy.data.cameras, bpy.data.lights):
        for block in list(data):
            if block.users == 0:
                data.remove(block)


def mat(name, color, roughness=0.9):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    shader = m.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    return m


def uv(name, pos, scale, material, rng=None, segments=12, rings=7):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                        radius=1, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    for poly in obj.data.polygons:
        poly.use_smooth = False
    if rng:
        for vertex in obj.data.vertices:
            vertex.co *= rng.uniform(0.94, 1.06)
    return obj


def block(name, pos, size, material, rotation=(0, 0, 0), bevel=0.025):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    obj.rotation_euler = rotation
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    if bevel:
        mod = obj.modifiers.new("Arestas quebradas", "BEVEL")
        mod.width = bevel
        mod.segments = 1
        mod.profile = 0.5
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    for poly in obj.data.polygons:
        poly.use_smooth = False
    return obj


def make_ground(rng, stones, dirt):
    count = 48
    verts = [(0, 0, 0.035)]
    faces = []
    for ring, (radius, z) in enumerate(((0.58, 0.10), (0.86, 0.075), (1.0, 0.018))):
        for i in range(count):
            a = math.tau * i / count
            r = radius * (1 + 0.025 * math.sin(a * 5) + 0.018 * math.cos(a * 9))
            verts.append((0.94 * r * math.cos(a), 0.91 * r * math.sin(a), 
                          z + (rng.uniform(-0.008, 0.008) if ring else 0)))
    for i in range(count):
        faces.append((0, 1 + i, 1 + (i + 1) % count))
    for ri in range(2):
        for i in range(count):
            a = 1 + ri * count + i
            b = 1 + ri * count + (i + 1) % count
            c = 1 + (ri + 1) * count + (i + 1) % count
            d = 1 + (ri + 1) * count + i
            faces.append((a, b, c, d))
    mesh = bpy.data.meshes.new("Base de pedra mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(stones[0])
    mesh.update()
    obj = bpy.data.objects.new("Base irregular de pedra", mesh)
    bpy.context.collection.objects.link(obj)
    for poly in mesh.polygons:
        poly.use_smooth = True
    for i in range(8):
        a = math.tau * i / 8 + 0.2
        x, y = 0.64 * math.cos(a), 0.58 * math.sin(a)
        uv("Terra escura entre pedras", (x, y, 0.095),
           (0.12, 0.07, 0.025), dirt, rng, 9, 5)


def broken_column(name, x, y, z0, height, radius, stones, rng, cracked=True):
    sides = 12
    levels = (0.0, 0.10, 0.30, 0.34, 0.57, 0.61, 0.80, 1.0)
    verts, faces, face_materials = [], [], []
    for ri, t in enumerate(levels):
        z = z0 + height * t
        r = radius * (1 - 0.13 * t) * (1 + (0.035 if ri in (1, 3, 5) else 0))
        for j in range(sides):
            a = math.tau * j / sides
            top_delta = (0.075 * math.sin(a * 3 + x * 5)
                         if cracked and ri == len(levels) - 1 else 0)
            rr = r * (1 + 0.035 * math.sin(a * 5 + y * 3))
            verts.append((x + rr * math.cos(a), y + rr * math.sin(a), z + top_delta))
    for ri in range(len(levels) - 1):
        for j in range(sides):
            a = ri * sides + j
            b = ri * sides + (j + 1) % sides
            faces.append((a, b, b + sides, a + sides))
            face_materials.append((j // 3 + ri // 3) % len(stones))
    faces.append(tuple(reversed(range(sides))))
    face_materials.append(0)
    if cracked:
        top_center = len(verts)
        verts.append((x, y, z0 + height))
        base = (len(levels) - 1) * sides
        for j in range(sides):
            faces.append((base + j, base + (j + 1) % sides, top_center))
            face_materials.append(2 if j % 4 == 0 else 0)
    else:
        faces.append(tuple((len(levels) - 1) * sides + j for j in range(sides)))
        face_materials.append(1)
    mesh = bpy.data.meshes.new(name + " mesh")
    mesh.from_pydata(verts, [], faces)
    for material in stones:
        mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for poly, idx in zip(mesh.polygons, face_materials):
        poly.material_index = idx
        poly.use_smooth = len(poly.vertices) == 4
    for idx, angle in enumerate((0.55, 2.7, 4.25)):
        z1 = z0 + height * (0.66 + 0.06 * idx)
        z2 = z0 + height * (0.84 + 0.04 * idx)
        px1 = x + math.cos(angle) * radius * 0.96
        py1 = y + math.sin(angle) * radius * 0.96
        px2 = x + math.cos(angle + 0.16) * radius * 0.98
        py2 = y + math.sin(angle + 0.16) * radius * 0.98
        block(name + " | fissura", ((px1 + px2) / 2, (py1 + py2) / 2, (z1 + z2) / 2),
              (0.014, 0.012, z2 - z1), stones[2], (0, 0, angle), 0)
    return obj


def wall_courses(name, xs, y, zbase, top_profile, stones, rng):
    for row in range(3):
        x = xs[0] + (0.10 if row % 2 else 0)
        col = 0
        while x < xs[1] - 0.08:
            width = rng.uniform(0.21, 0.38)
            cx = x + width / 2
            frac = (cx - xs[0]) / (xs[1] - xs[0])
            available = top_profile(frac)
            z = zbase + 0.13 + row * 0.19
            if z - zbase < available:
                material = stones[(row + col + rng.randrange(len(stones))) % len(stones)]
                block("%s | bloco %d-%d" % (name, row, col),
                      (cx, y + rng.uniform(-0.025, 0.025), z),
                      (width, rng.uniform(0.18, 0.25), rng.uniform(0.14, 0.22)),
                      material, (rng.uniform(-0.07, 0.07), rng.uniform(-0.08, 0.08),
                                 rng.uniform(-0.065, 0.065)), 0.028)
            x += width * rng.uniform(0.82, 0.94)
            col += 1


def build(rng):
    stones = [mat("Calcário cinza", (0.31, 0.32, 0.30)),
              mat("Calcário claro", (0.42, 0.42, 0.39)),
              mat("Pedra envelhecida", (0.22, 0.23, 0.22)),
              mat("Veios quentes", (0.35, 0.31, 0.25))]
    dirt = mat("Terra nas juntas", (0.25, 0.22, 0.17))
    moss = mat("Líquen antigo", (0.29, 0.34, 0.20))
    make_ground(rng, stones, dirt)
    wall_courses("Muralha do fundo", (-0.13, 0.88), 0.48, 0.07,
                 lambda t: 0.69 - 0.34 * t, stones, rng)
    wall_courses("Muralha lateral", (-0.88, -0.24), 0.15, 0.07,
                 lambda t: 0.54 - 0.18 * t, stones, rng)
    broken_column("Coluna partida alta", -0.60, 0.34, 0.08, 1.02, 0.17,
                  stones, rng, True)
    broken_column("Toco de coluna", 0.69, -0.01, 0.08, 0.50, 0.16,
                  stones, rng, True)
    for i, (x, length, rad) in enumerate(((-0.04, 0.43, 0.125), (0.34, 0.36, 0.11))):
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=rad,
                                            depth=length, location=(x, -0.52, 0.20))
        obj = bpy.context.object
        obj.name = "Tambor de coluna caído %02d" % i
        obj.rotation_euler[1] = math.radians(82 + i * 7)
        obj.rotation_euler[2] = math.radians(-12 + i * 19)
        obj.data.materials.append(stones[(i + 1) % len(stones)])
        for poly in obj.data.polygons:
            poly.use_smooth = False
    for i in range(13):
        a = rng.uniform(0, math.tau)
        r = rng.uniform(0.30, 0.79)
        x, y = r * math.cos(a), r * math.sin(a)
        if y > 0.25 and -0.25 < x < 0.55:
            continue
        size = rng.uniform(0.065, 0.15)
        uv("Escombro solto %02d" % i, (x, y, 0.10 + size * 0.38),
           (size, size * rng.uniform(0.65, 1.25), size * rng.uniform(0.55, 0.95)),
           rng.choice(stones), rng, 10, 6)
    for x, y, z, sx, sy in ((-0.42, 0.23, 0.43, .09, .025),
                            (0.55, 0.37, 0.34, .12, .022),
                            (-0.81, 0.14, 0.29, .08, .025),
                            (0.64, -0.02, 0.38, .06, .025)):
        uv("Mancha de líquen", (x, y, z), (sx, sy, .035), moss, rng, 10, 5)


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
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.09, 0.08, 0.065, 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.31
    for name, loc, energy, size, color in (
        ("Luz de pedra quente", (2.6, -3.2, 4.3), 185, 2.9, (1.0, 0.82, 0.63)),
        ("Preenchimento frio", (-2.7, -0.1, 2.9), 125, 2.7, (0.77, 0.84, 1.0)),
        ("Recorte de poeira", (0.3, 2.9, 3.6), 145, 2.5, (1.0, 0.76, 0.52)),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.data.color = color
        point_at(light, (0, 0, 0.55))
    bpy.ops.object.camera_add(location=(2.7, -3.8, 2.7))
    camera = bpy.context.object
    camera.name = "Câmera da miniatura"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 2.65
    point_at(camera, (0, 0.0, 0.53))
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
        group[0].name = "Ruína | " + material.name


def export():
    clear_scene()
    build(random.Random(108021))
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
                              export_apply=True, export_materials="EXPORT")
    print("ASSET_EXPORT", SLUG, "meshes=", len(meshes))


if __name__ == "__main__":
    export()
