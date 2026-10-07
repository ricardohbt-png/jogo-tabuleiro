"""Cria a miniatura 3D de um tronco caído com musgo para a masmorra/floresta.

Gera .blend editável, GLB de runtime e PNG transparente para editor/mapa 2D.
O modelo fica deitado ao longo do eixo X, centrado no footprint 2×1 e apoiado
no piso; o renderizador gira junto com a decoração.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)
random.seed(90817)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for data in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                 bpy.data.cameras, bpy.data.lights):
        for item in list(data):
            if item.users == 0:
                data.remove(item)


def material(name, color, roughness=0.9):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def assign(obj, mat):
    obj.data.materials.append(mat)
    return obj


def ellipsoid(name, location, scale, mat, segments=20, rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                        radius=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, mat)
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def cylinder_between(name, start, end, radius, mat, vertices=12):
    a, b = Vector(start), Vector(end)
    delta = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                        depth=delta.length, location=(a + b) * 0.5)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = delta.to_track_quat("Z", "Y")
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel = obj.modifiers.new("Fibras suavizadas", "BEVEL")
    bevel.width = radius * 0.45
    bevel.segments = 2
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    return assign(obj, mat)


def curved_tube(name, points, radius, mat):
    curve = bpy.data.curves.new(name + " path", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 8
    curve.bevel_depth = radius
    curve.bevel_resolution = 2
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, co in zip(spline.points, points):
        point.co = (*co, 1)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.object
    obj.select_set(False)
    return obj


def bark_log(mats):
    """Tronco irregular de casca grossa com base natural apoiada no chão."""
    rings, sides = 24, 48
    verts, faces = [], []
    for ix in range(rings + 1):
        t = ix / rings
        x = -0.88 + 1.76 * t + 0.018 * math.sin(t * math.pi * 4)
        base_r = 0.285 + 0.025 * math.sin(t * math.pi) + 0.012 * math.sin(t * 9)
        for j in range(sides):
            a = 2 * math.pi * j / sides
            noise = (1 + 0.035 * math.sin(a * 7 + t * 21)
                     + 0.020 * math.sin(a * 13 - t * 15)
                     + 0.012 * math.sin(a * 21 + t * 8))
            # O eixo do tronco é X; z sobe a partir do piso (raio de 0.29).
            y = math.cos(a) * base_r * noise
            z = 0.292 + math.sin(a) * base_r * noise
            verts.append((x, y, z))
    for i in range(rings):
        for j in range(sides):
            a = i * sides + j
            b = i * sides + (j + 1) % sides
            faces.append((a, b, b + sides, a + sides))
    # Tampas irregulares como seções cortadas/rachadas nas duas pontas.
    for end in (0, rings):
        center = len(verts)
        x = verts[end * sides][0]
        verts.append((x, 0, 0.292))
        for j in range(sides):
            q = end * sides + j
            r = end * sides + (j + 1) % sides
            faces.append((center, r, q) if end == 0 else (center, q, r))
    mesh = bpy.data.meshes.new("Casca orgânica | malha principal")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mats[0])
    mesh.update()
    obj = bpy.data.objects.new("Tronco | casca escura e envelhecida", mesh)
    bpy.context.collection.objects.link(obj)
    for p in mesh.polygons:
        p.use_smooth = True
    return obj


def end_grain(side, mat_dark, mat_wood, mat_light):
    """Corte de topo com cerne visível e anéis concêntricos."""
    x = side * 0.884
    outward = 1 if side > 0 else -1
    # Disco facetado e anéis no plano YZ, orientados para fora do tronco.
    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=0.218, depth=0.014,
                                        location=(x, 0, 0.292),
                                        rotation=(0, math.pi / 2, 0))
    core = bpy.context.object
    core.name = "Topo partido | cerne exposto"
    assign(core, mat_wood)
    bevel = core.modifiers.new("Borda lascada", "BEVEL")
    bevel.width = 0.009
    bevel.segments = 2
    bpy.context.view_layer.objects.active = core
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    for radius, minor, mat in ((0.175, 0.006, mat_light), (0.128, 0.004, mat_dark),
                               (0.083, 0.004, mat_light), (0.045, 0.003, mat_dark)):
        bpy.ops.mesh.primitive_torus_add(major_segments=40, minor_segments=8,
                                        major_radius=radius, minor_radius=minor,
                                        location=(x + outward * 0.010, 0, 0.292),
                                        rotation=(0, math.pi / 2, 0))
        ring = bpy.context.object
        ring.name = "Anel de crescimento"
        assign(ring, mat)


def moss_patch(name, center, size, mat, seed):
    """Mancha rugosa projetada na curvatura da casca, sem placas flutuantes."""
    rng = random.Random(seed)
    cx, cy, _cz = center
    half_x, _depth, _height = size
    radial_z = math.sqrt(max(0.0, 0.285 ** 2 - cy ** 2))
    theta = math.atan2(radial_z, cy)
    half_theta = min(0.62, max(0.20, _depth / 0.285))
    count = 30
    verts = [(cx, 0.0, 0.0)]
    for i in range(count):
        a = 2 * math.pi * i / count
        jitter = rng.uniform(0.80, 1.13)
        x = cx + math.cos(a) * half_x * jitter
        ang = theta + math.sin(a) * half_theta * jitter
        t = max(0.0, min(1.0, (x + 0.88) / 1.76))
        bark_radius = 0.285 + 0.025 * math.sin(t * math.pi) + 0.012 * math.sin(t * 9)
        bark_noise = (1 + 0.035 * math.sin(ang * 7 + t * 21)
                      + 0.020 * math.sin(ang * 13 - t * 15)
                      + 0.012 * math.sin(ang * 21 + t * 8))
        radius = bark_radius * bark_noise + 0.012
        verts.append((x, math.cos(ang) * radius, 0.292 + math.sin(ang) * radius))
    faces = [(0, i + 1, (i + 1) % count + 1) for i in range(count)]
    mesh = bpy.data.meshes.new(name + " | malha aderente")
    mesh.from_pydata(verts, [], faces)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for face in mesh.polygons:
        face.use_smooth = True
    return obj


def add_bark_ridges(mats):
    # Veios compridos seguem o cilindro e alternam entre ocres, sombras e casca.
    for i in range(15):
        angle = 2 * math.pi * i / 15 + random.uniform(-0.12, 0.12)
        points = []
        left = random.uniform(-0.86, -0.42)
        right = random.uniform(0.42, 0.86)
        phase = random.uniform(0, math.tau)
        for j in range(8):
            t = j / 7
            x = left + (right - left) * t
            a = angle + 0.070 * math.sin(t * 8 + phase) + 0.025 * math.sin(t * 19 + phase)
            radius = 0.294 + 0.019 * math.sin(t * math.pi) + 0.004
            points.append((x, math.cos(a) * radius, 0.292 + math.sin(a) * radius))
        curved_tube("Veio de casca %02d" % i, points,
                    random.uniform(0.0025, 0.0045), random.choice((mats[1], mats[3], mats[4])))
    # Fendas escuras curtas e fissuras nas extremidades quebradas.
    for i in range(12):
        x = random.choice((-1, 1)) * random.uniform(0.72, 0.87)
        a = random.uniform(0, math.tau)
        r = 0.288
        p0 = (x, math.cos(a) * r, 0.292 + math.sin(a) * r)
        p1 = (x - math.copysign(random.uniform(0.025, 0.09), x),
              math.cos(a + 0.05) * (r + 0.008),
              0.292 + math.sin(a + 0.05) * (r + 0.008))
        curved_tube("Fissura escura %02d" % i, [p0, p1], 0.003, mats[4])


def build_model():
    bark = [
        material("Casca | marrom profundo", (0.16, 0.075, 0.038)),
        material("Casca | castanho úmido", (0.24, 0.115, 0.055)),
        material("Casca | sulcos dourados", (0.34, 0.18, 0.075)),
        material("Casca | madeira velha", (0.28, 0.14, 0.065)),
        material("Fendas | sombra", (0.055, 0.030, 0.018)),
    ]
    wood = material("Cerne | madeira clara partida", (0.53, 0.31, 0.13))
    ring_light = material("Cerne | anéis claros", (0.70, 0.46, 0.22))
    ring_dark = material("Cerne | anéis escuros", (0.27, 0.13, 0.055))
    moss = [
        material("Musgo | verde profundo", (0.035, 0.085, 0.020)),
        material("Musgo | verde floresta", (0.060, 0.125, 0.030)),
        material("Musgo | pontas vivas", (0.090, 0.155, 0.035)),
        material("Líquen | verde acinzentado", (0.135, 0.155, 0.070)),
    ]
    bark_log(bark)
    end_grain(-1, ring_dark, wood, ring_light)
    end_grain(1, ring_dark, wood, ring_light)
    add_bark_ridges(bark)

    # Galhos quebrados projetam-se para trás e para as laterais, sem exceder 2×1.
    branch_roots = [(-0.48, 0.17, 0.39), (0.30, -0.19, 0.38), (0.62, 0.16, 0.38)]
    for i, (x, y, z) in enumerate(branch_roots):
        dx = -0.10 if i != 1 else 0.10
        dy = 0.13 if y > 0 else -0.13
        end = (x + dx, y + dy, z + random.uniform(0.055, 0.10))
        mid = (x + dx * 0.55, y + dy * 0.55, z + 0.045)
        curved_tube("Galho quebrado %d" % i, [(x, y, z), mid, end],
                    0.024, bark[1])
        ellipsoid("Ponta escura do galho %d" % i, end,
                  (0.018, 0.018, 0.016), bark[4], 12, 8)

    # Musgo em ilhas assimétricas acompanha o topo e a lateral visível.
    patches = [
        ((-0.58, -0.02, 0.529), (0.35, 0.19, 0.019), 0),
        ((-0.12, 0.055, 0.562), (0.32, 0.16, 0.018), 1),
        ((0.38, 0.005, 0.540), (0.38, 0.17, 0.020), 0),
        ((0.66, -0.06, 0.495), (0.19, 0.12, 0.018), 1),
        ((-0.39, -0.205, 0.455), (0.23, 0.095, 0.016), 1),
        ((0.18, -0.225, 0.445), (0.27, 0.082, 0.015), 0),
        ((-0.69, 0.01, 0.505), (0.15, 0.09, 0.015), 3),
    ]
    for i, (center, scale, m) in enumerate(patches):
        surface_z = 0.292 + math.sqrt(max(0.0, 0.285 ** 2 - center[1] ** 2))
        center = (center[0], center[1], surface_z - scale[2] * 0.30)
        moss_patch("Musgo irregular %02d" % i, center, scale, moss[m], 410 + i)
    # Grânulos e pequenas folhinhas rompem a superfície lisa das manchas.
    for i in range(28):
        x = random.uniform(-0.80, 0.80)
        y = random.uniform(-0.15, 0.15)
        surface_z = 0.292 + math.sqrt(max(0.0, 0.285 ** 2 - y ** 2))
        z = surface_z + random.uniform(0.003, 0.007)
        ellipsoid("Tufo de musgo %02d" % i, (x, y, z),
                  (random.uniform(0.016, 0.035), random.uniform(0.008, 0.017),
                   random.uniform(0.005, 0.010)), random.choice(moss[:3]), 10, 6)

    # Musgo rente ao piso e líquen preso à casca na face voltada para a câmera.
    moss_patch("Líquen na casca", (-0.03, -0.272, 0.31), (0.22, 0.035, 0.065), moss[3], 39)


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def setup_scene():
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.10, 0.12, 0.15, 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35
    for name, location, energy, size, color in (
        ("Luz principal quente", (0.7, -1.5, 2.1), 72, 1.5, (1.0, 0.86, 0.67)),
        ("Preenchimento de floresta", (-1.3, -0.2, 1.0), 38, 1.3, (0.69, 0.83, 0.67)),
        ("Recorte suave", (0.1, 1.0, 1.6), 58, 1.1, (0.78, 0.89, 0.70)),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.data.color = color
        point_at(light, (0, 0, 0.32))
    bpy.ops.object.camera_add(location=(1.65, -2.6, 1.72))
    camera = bpy.context.object
    camera.name = "Câmera de prévia 3D"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 2.35
    point_at(camera, (0, 0, 0.30))
    bpy.context.scene.camera = camera


def export_asset():
    # Agrupa por material para manter poucas chamadas de desenho no runtime.
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
        group[0].name = "Tronco e detalhes | " + mat.name
        group[0].data.name = group[0].name + " Mesh"
    bpy.ops.object.select_all(action="DESELECT")
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "tronco_musgo.blend"))
    scene = bpy.context.scene
    scene.render.filepath = str(OUT / "tronco_musgo_preview.png")
    bpy.ops.render.render(write_still=True)
    # Sprite de alta leitura para o editor e o mapa 2D.
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.filepath = str(OUT / "tronco_musgo.png")
    bpy.ops.render.render(write_still=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT / "tronco_musgo.glb"),
                              export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True,
                              export_materials="EXPORT")
    print("ASSET_EXPORT tronco_musgo meshes=%d" % len(meshes))


def build():
    clear_scene()
    build_model()
    setup_scene()
    export_asset()


if __name__ == "__main__":
    build()
