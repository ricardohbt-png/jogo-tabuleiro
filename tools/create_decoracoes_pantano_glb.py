"""Cria duas decorações 3D de pântano com Blender.

Exporta tronco podre com fungos e conjunto de tocos alagados em .blend, GLB,
PNG transparente para editor/mapa e prévia 3D.
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


def material(name, color, roughness=0.9, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    shader = m.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    return m


def assign(obj, mat):
    obj.data.materials.append(mat)
    return obj


def ellipsoid(name, center, scale, mat, segments=20, rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                        radius=1, location=center)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, mat)
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def cylinder(name, center, radius, depth, mat, vertices=16, bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                        depth=depth, location=center)
    obj = bpy.context.object
    obj.name = name
    assign(obj, mat)
    if bevel:
        mod = obj.modifiers.new("Bordas gastas", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        obj.modifiers.new("Normais suaves", "WEIGHTED_NORMAL")
        bpy.ops.object.modifier_apply(modifier="Normais suaves")
    return obj


def tube_between(name, a, b, radius, mat, vertices=10):
    va, vb = Vector(a), Vector(b)
    delta = vb - va
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                        depth=delta.length, location=(va + vb) * 0.5)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = delta.to_track_quat("Z", "Y")
    assign(obj, mat)
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def tapered_log_shell(name, center_x, length, radius, z_center, bark_mats, seed):
    rng = random.Random(seed)
    rings, sides = 22, 40
    verts, faces = [], []
    for i in range(rings + 1):
        t = i / rings
        x = center_x - length / 2 + length * t
        taper = 0.91 + 0.09 * math.sin(math.pi * t)
        for j in range(sides):
            a = math.tau * j / sides
            noise = (1 + 0.045 * math.sin(a * 7 + t * 19 + seed)
                     + 0.025 * math.sin(a * 13 - t * 11)
                     + 0.016 * math.sin(a * 3 + t * 27))
            r = radius * taper * noise
            verts.append((x, math.cos(a) * r, z_center + math.sin(a) * r))
    for i in range(rings):
        for j in range(sides):
            a = i * sides + j
            b = i * sides + (j + 1) % sides
            faces.append((a, b, b + sides, a + sides))
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(rng.choice(bark_mats))
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for poly in mesh.polygons:
        poly.use_smooth = True
    return obj


def add_log_fungi(rng, center_x, radius, z_center, bark_detail, fungus):
    # Fungos em pequenos leques, com haste curta e chapéus sobrepostos.
    for i in range(8):
        x = center_x + rng.uniform(-0.72, 0.70)
        side = rng.choice((-1, 1))
        y = side * rng.uniform(0.12, 0.22)
        surface_z = z_center + math.sqrt(max(0.02, radius * radius - y * y))
        if surface_z < 0.27:
            continue
        height = rng.uniform(0.055, 0.115)
        base = (x, y, surface_z - 0.015)
        cap_center = (x + rng.uniform(-0.018, 0.018), y + side * 0.008,
                      surface_z + height * 0.68)
        cylinder("Haste de fungo", (x, y, surface_z + height * 0.36),
                 rng.uniform(0.012, 0.021), height * 0.72,
                 rng.choice(fungus[0:2]), 12, 0.004)
        ellipsoid("Chapéu de fungo", cap_center,
                  (rng.uniform(0.045, 0.071), rng.uniform(0.040, 0.065),
                   rng.uniform(0.018, 0.031)), rng.choice(fungus[2:]), 16, 9)
        # Pontos e lamelas dão escala ao fungo sem poluir a silhueta.
        if i % 2 == 0:
            ellipsoid("Pinta pálida do chapéu", (cap_center[0] + 0.012,
                      cap_center[1] - 0.014, cap_center[2] + 0.020),
                      (0.008, 0.006, 0.003), fungus[0], 10, 6)


def build_rotten_log(rng):
    bark = [material("Casca podre | marrom escuro", (0.105, 0.060, 0.035)),
            material("Casca úmida | castanho", (0.18, 0.095, 0.048)),
            material("Casca desbotada | cinza marrom", (0.24, 0.19, 0.12)),
            material("Fendas podres | sombra", (0.045, 0.035, 0.025))]
    wood = material("Madeira interna envelhecida", (0.34, 0.22, 0.12))
    fungi = [material("Haste de fungo | creme", (0.63, 0.57, 0.38)),
             material("Haste de fungo | ocre", (0.42, 0.30, 0.14)),
             material("Fungo | ocre apagado", (0.48, 0.27, 0.11)),
             material("Fungo | bege pálido", (0.72, 0.62, 0.38)),
             material("Fungo | verde oliva", (0.25, 0.32, 0.12))]
    moss = material("Musgo de pântano", (0.09, 0.16, 0.045))
    center_x, zc, radius, length = 0.0, 0.265, 0.245, 1.76
    tapered_log_shell("Tronco oco | casca encharcada", center_x, length,
                      radius, zc, bark[:3], 620)
    # Disco de cerne quebrado na ponta distante, com buraco escurecido no centro.
    cylinder("Corte de madeira podre", (length / 2 - 0.005, 0, zc),
             radius * 0.77, 0.018, wood, 32, 0.006).rotation_euler[1] = math.pi / 2
    cylinder("Interior escuro do tronco oco", (length / 2 + 0.006, 0, zc),
             radius * 0.42, 0.012, bark[3], 28, 0.003).rotation_euler[1] = math.pi / 2
    # Anéis de madeira irregular e borda aberta no corte.
    for r in (radius * 0.62, radius * 0.43, radius * 0.25):
        bpy.ops.mesh.primitive_torus_add(major_segments=32, minor_segments=7,
                                        major_radius=r, minor_radius=0.004,
                                        location=(length / 2 + 0.014, 0, zc),
                                        rotation=(0, math.pi / 2, 0))
        assign(bpy.context.object, bark[2])
        bpy.context.object.name = "Anel exposto no corte"
    # Veios rachados longitudinais baixos, com comprimentos alternados.
    for i in range(16):
        a = math.tau * i / 16 + rng.uniform(-0.12, 0.12)
        x0 = rng.uniform(-0.84, 0.12)
        x1 = min(0.84, x0 + rng.uniform(0.25, 0.78))
        r = radius * 1.015
        p0 = (x0, math.cos(a) * r, zc + math.sin(a) * r)
        p1 = ((x0 + x1) / 2, math.cos(a + 0.035) * r,
              zc + math.sin(a + 0.035) * r)
        p2 = (x1, math.cos(a + rng.uniform(-0.07, 0.07)) * r,
              zc + math.sin(a + rng.uniform(-0.07, 0.07)) * r)
        tube_between("Veio rachado %02d" % i, p0, p1, 0.0045, rng.choice(bark[1:]))
        tube_between("Veio rachado %02d ponta" % i, p1, p2, 0.0045, rng.choice(bark[1:]))
    add_log_fungi(rng, center_x, radius, zc, bark, fungi)
    # Musgo escuro em pequenos agrupamentos na face superior do tronco.
    for i in range(7):
        x = rng.uniform(-0.74, 0.68)
        y = rng.uniform(-0.08, 0.08)
        z = zc + math.sqrt(max(0.02, radius ** 2 - y ** 2)) + 0.003
        ellipsoid("Mancha de musgo", (x, y, z),
                  (rng.uniform(0.09, 0.17), rng.uniform(0.035, 0.06), 0.012),
                  moss, 14, 8)


def stump_mesh(name, cx, cy, height, radius, bark, top_mat, seed):
    rng = random.Random(seed)
    sides = 16
    levels = [(0.02, 0.92), (0.10, 1.0), (height * 0.78, 0.96),
              (height, 0.88)]
    verts, faces = [], []
    for li, (z, factor) in enumerate(levels):
        for j in range(sides):
            a = math.tau * j / sides
            jitter = rng.uniform(0.93, 1.07)
            top_wave = (0.04 * math.sin(a * 3 + seed) if li == len(levels) - 1 else 0)
            rr = radius * factor * jitter
            verts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr,
                          z + top_wave))
    for li in range(len(levels) - 1):
        for j in range(sides):
            a = li * sides + j
            b = li * sides + (j + 1) % sides
            faces.append((a, b, b + sides, a + sides))
    mesh = bpy.data.meshes.new(name + " bark mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(bark)
    mesh.update()
    obj = bpy.data.objects.new(name + " | casca", mesh)
    bpy.context.collection.objects.link(obj)
    # Tampão torto de madeira escura, com alguns raios de cerne rachado.
    top_verts = [(cx, cy, height - 0.005)] + verts[(len(levels) - 1) * sides:]
    top_faces = [(0, j + 1, (j + 1) % sides + 1) for j in range(sides)]
    top_mesh = bpy.data.meshes.new(name + " top mesh")
    top_mesh.from_pydata(top_verts, [], top_faces)
    top_mesh.materials.append(top_mat)
    top_mesh.update()
    top_obj = bpy.data.objects.new(name + " | topo partido", top_mesh)
    bpy.context.collection.objects.link(top_obj)
    for i in range(5):
        a = rng.uniform(0, math.tau)
        rr = radius * rng.uniform(0.18, 0.68)
        start = (cx + math.cos(a) * rr, cy + math.sin(a) * rr, height + 0.005)
        end = (cx + math.cos(a) * radius * 0.72,
               cy + math.sin(a) * radius * 0.72, height - 0.006)
        tube_between("Lasca no topo", start, end, 0.004, bark, 8)
    # Sulcos altos e verticais enfatizam madeira inchada pela água.
    for j in range(7):
        a = math.tau * j / 7 + 0.1
        r = radius * 1.015
        start = (cx + math.cos(a) * r, cy + math.sin(a) * r, 0.08)
        end = (cx + math.cos(a + 0.025) * r, cy + math.sin(a + 0.025) * r,
               height * rng.uniform(0.55, 0.93))
        tube_between("Sulco de casca do toco", start, end, 0.0045, top_mat, 8)


def build_waterlogged_stumps(rng):
    water = material("Água parada | verde profundo", (0.045, 0.14, 0.12), 0.34, 0.08)
    ripple = material("Reflexo turvo", (0.17, 0.29, 0.23), 0.28, 0.04)
    bark = material("Toco alagado | casca preta", (0.075, 0.052, 0.034))
    bark_light = material("Toco alagado | casca cinzenta", (0.16, 0.12, 0.075))
    heart = material("Madeira aberta | marrom escuro", (0.23, 0.15, 0.075))
    heart_light = material("Madeira aberta | anéis", (0.38, 0.27, 0.13))
    fungus = material("Fungo pequeno | verde pálido", (0.39, 0.43, 0.22))
    # Poça baixa de contorno irregular, dentro do limite da casa.
    verts, faces = [(0, 0, 0.012)], []
    count = 48
    for i in range(count):
        a = math.tau * i / count
        r = 0.385 * (1 + 0.10 * math.sin(a * 5) + 0.055 * math.sin(a * 9 + 0.7))
        verts.append((math.cos(a) * r, math.sin(a) * r * 0.88, 0.012))
    for i in range(count):
        faces.append((0, i + 1, (i + 1) % count + 1))
    mesh = bpy.data.meshes.new("Água rasa irregular mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(water)
    mesh.update()
    puddle = bpy.data.objects.new("Poça parada em torno dos tocos", mesh)
    bpy.context.collection.objects.link(puddle)
    # Um par de ondas rasas e alguns reflexos quebrados sobre a água.
    for i, radius in enumerate((0.20, 0.31)):
        bpy.ops.mesh.primitive_torus_add(major_segments=32, minor_segments=6,
                                        major_radius=radius, minor_radius=0.003,
                                        location=(-0.12 + i * 0.22, -0.16, 0.018))
        assign(bpy.context.object, ripple)
        bpy.context.object.name = "Ondulação quase imóvel"
    # Três troncos cortados de alturas variadas, formando um grupo de tocos.
    stump_mesh("Toco central", -0.045, 0.035, 0.51, 0.145, bark, heart, 41)
    stump_mesh("Toco baixo", -0.235, -0.12, 0.34, 0.105, bark_light, heart_light, 53)
    stump_mesh("Toco fino", 0.215, 0.135, 0.39, 0.087, bark, heart, 67)
    # Cerne em anéis aparentes no maior toco, além de manchas de fungo aquático.
    for radius in (0.098, 0.064, 0.031):
        bpy.ops.mesh.primitive_torus_add(major_segments=28, minor_segments=5,
                                        major_radius=radius, minor_radius=0.003,
                                        location=(-0.045, 0.035, 0.518))
        assign(bpy.context.object, heart_light)
        bpy.context.object.name = "Anel de crescimento no toco"
    for i in range(6):
        x = rng.uniform(-0.34, 0.31)
        y = rng.uniform(-0.24, 0.27)
        z = rng.uniform(0.15, 0.27)
        ellipsoid("Fungo de brejo no toco", (x, y, z),
                  (0.035, 0.030, 0.018), fungus, 12, 8)


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def merge_by_material():
    for mat in list(bpy.data.materials):
        group = [obj for obj in bpy.context.scene.objects
                 if obj.type == "MESH" and mat in obj.data.materials[:]]
        if len(group) < 2:
            continue
        bpy.ops.object.select_all(action="DESELECT")
        for obj in group:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = group[0]
        bpy.ops.object.join()
        group[0].name = "Pântano | " + mat.name
        group[0].data.name = group[0].name + " Mesh"


def scene_camera(slug):
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
        point_at(lamp, (0, 0, 0.26))
    bpy.ops.object.camera_add(location=(1.35, -2.25, 1.65))
    camera = bpy.context.object
    camera.name = "Câmera da miniatura"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 2.15 if slug == "tronco_podre_fungos" else 1.30
    point_at(camera, (0, 0, 0.29))
    scene.camera = camera
    scene.render.filepath = str(OUT / (slug + "_preview.png"))


def export_one(slug, build):
    clear_scene()
    rng = random.Random(16231 if slug == "tronco_podre_fungos" else 16421)
    build(rng)
    merge_by_material()
    scene_camera(slug)
    bpy.ops.object.select_all(action="DESELECT")
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
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
    export_one("tronco_podre_fungos", build_rotten_log)
    export_one("tocos_alagados", build_waterlogged_stumps)


if __name__ == "__main__":
    build()
