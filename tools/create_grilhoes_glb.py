"""Cria duas miniaturas de ferro para as decorações da masmorra.

Gera .blend editável, GLB, PNG transparente para o mapa 2D e prévia 3D.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

import bpy
from mathutils import Quaternion, Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)
random.seed(14603)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                       bpy.data.cameras, bpy.data.lights):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def make_material(name, color, metallic=0.65, roughness=0.48):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return mat


def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj


def bevel_cube(name, location, dimensions, mat, bevel=0.012):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, mat)
    mod = obj.modifiers.new("Forged softened edges", "BEVEL")
    mod.width = bevel
    mod.segments = 3
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    mod = obj.modifiers.new("Weighted forged normals", "WEIGHTED_NORMAL")
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def sphere(name, center, scale, mat, segments=32, rings=20):
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


def torus(name, location, major, minor, mat, rotation=(0, 0, 0), segments=28):
    bpy.ops.mesh.primitive_torus_add(major_segments=segments, minor_segments=10,
                                    location=location, major_radius=major,
                                    minor_radius=minor, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    assign(obj, mat)
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def cylinder(name, location, radius, depth, mat, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=radius, depth=depth,
                                       location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    assign(obj, mat)
    mod = obj.modifiers.new("Rim bevel", "BEVEL")
    mod.width = min(0.004, radius * 0.2)
    mod.segments = 2
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    mod = obj.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def make_arc_cuff(name, center, radius, tube, mat, plane="floor",
                  start=-math.pi / 2, end=math.pi / 2):
    """An open horseshoe cuff in the floor XY or wall XZ plane."""
    c = Vector(center)
    u = Vector((1, 0, 0))
    v = Vector((0, 1, 0)) if plane == "floor" else Vector((0, 0, 1))
    steps, sides = 34, 10
    verts, faces = [], []
    for i in range(steps + 1):
        t = start + (end - start) * i / steps
        radial = (math.cos(t) * u + math.sin(t) * v).normalized()
        point = c + radial * radius
        tangent = (-math.sin(t) * u + math.cos(t) * v).normalized()
        binormal = tangent.cross(radial).normalized()
        for j in range(sides):
            a = 2 * math.pi * j / sides
            p = point + tube * (math.cos(a) * radial + math.sin(a) * binormal)
            verts.append(tuple(p))
    for i in range(steps):
        for j in range(sides):
            a = i * sides + j
            b = i * sides + (j + 1) % sides
            faces.append((a, b, b + sides, a + sides))
    faces.extend((tuple(range(sides - 1, -1, -1)),
                  tuple(steps * sides + j for j in range(sides))))
    mesh = bpy.data.meshes.new(name + " mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for face in mesh.polygons:
        face.use_smooth = True
    return obj


def sample_polyline(points, t):
    lengths = [(Vector(points[i + 1]) - Vector(points[i])).length
               for i in range(len(points) - 1)]
    distance = max(0.0, min(0.9999, t)) * sum(lengths)
    for i, length in enumerate(lengths):
        if distance <= length:
            f = distance / max(length, 1e-6)
            point = Vector(points[i]).lerp(Vector(points[i + 1]), f)
            tangent = (Vector(points[i + 1]) - Vector(points[i])).normalized()
            return point, tangent
        distance -= length
    return Vector(points[-1]), (Vector(points[-1]) - Vector(points[-2])).normalized()


def chain_links(name, points, count, major, minor, mat):
    for i in range(count):
        point, tangent = sample_polyline(points, (i + 0.5) / count)
        q = tangent.to_track_quat("Z", "Y")
        if i % 2:
            # Alternate the link plane so each oval passes through the next.
            q = q @ Quaternion((1, 0, 0), math.pi / 2)
        torus("%s | elo %02d" % (name, i + 1), point, major, minor, mat,
              rotation=q.to_euler(), segments=20)


def iron_set():
    return {
        "iron": make_material("Ferro negro forjado", (0.055, 0.064, 0.072), 0.82, 0.40),
        "edge": make_material("Arestas de aço gasto", (0.205, 0.225, 0.235), 0.78, 0.38),
        "rust": make_material("Ferrugem antiga", (0.22, 0.090, 0.042), 0.28, 0.83),
        "dark": make_material("Ferro escurecido", (0.025, 0.030, 0.035), 0.72, 0.57),
    }


def build_floor_ball_chain():
    m = iron_set()
    cx, cy, r = -0.145, -0.080, 0.188
    sphere("Bola maciça de ferro", (cx, cy, r), (r, r, r), m["iron"], 40, 28)
    torus("Costura de fundição da bola", (cx, cy, r), r * 0.995, 0.0045,
          m["edge"], segments=48)
    for i, angle in enumerate((0.55, 2.05, 3.55, 5.05)):
        x = cx + math.cos(angle) * r * 0.69
        y = cy + math.sin(angle) * r * 0.69
        z = r + math.sqrt(max(0, r * r - (x - cx) ** 2 - (y - cy) ** 2)) * 0.70
        sphere("Marca martelada %02d" % i, (x, y, z), (0.012, 0.012, 0.004),
               m["dark"], 12, 8)
    torus("Olhal da bola", (-0.025, -0.108, 0.305), 0.034, 0.009, m["edge"],
          rotation=(math.pi / 2, 0, 0), segments=28)
    cylinder("Base do olhal", (-0.025, -0.105, 0.276), 0.028, 0.012, m["iron"])
    sphere("Pino do olhal", (-0.025, -0.114, 0.305), (0.011, 0.010, 0.011),
           m["edge"], 16, 10)
    path = [(-0.025, -0.125, 0.305), (0.015, -0.150, 0.210),
            (0.055, -0.105, 0.058), (0.125, -0.015, 0.045),
            (0.220, 0.005, 0.045)]
    chain_links("Corrente no piso", path, 13, 0.035, 0.0075, m["edge"])
    cuff = (0.255, 0.070, 0.035)
    make_arc_cuff("Algema aberta", cuff, 0.082, 0.014, m["iron"], "floor",
                  -math.pi / 2, math.pi / 2)
    for i, angle in enumerate((-math.pi / 2, math.pi / 2)):
        x = cuff[0] + math.cos(angle) * 0.082
        y = cuff[1] + math.sin(angle) * 0.082
        cylinder("Dobradiça da algema %d" % i, (x, y, 0.038), 0.018, 0.025, m["edge"])
        sphere("Rebite da algema %d" % i, (x, y, 0.053), (0.008, 0.008, 0.005),
               m["rust"], 12, 8)
    bevel_cube("Fecho da algema", (0.267, 0.070, 0.056), (0.035, 0.025, 0.016),
               m["edge"], 0.005)
    torus("Argola de ligação da algema", (0.172, 0.050, 0.047), 0.022, 0.006,
          m["iron"], segments=20)
    return ("Bola maciça e algema aberta ligadas por corrente de ferro",
            (1.12, -1.35, 1.18), (0.02, 0.0, 0.10), 1.10,
            (0.0, 0.0, 1.25), 0.92)


def build_wall_shackles():
    m = iron_set()
    # Backplate at +Y becomes the -Z attachment face in the exported GLB.
    bevel_cube("Placa de fixação dos grilhões", (0, 0.045, 0.435),
               (0.300, 0.065, 0.550), m["iron"], 0.035)
    bevel_cube("Reforço central da placa", (0, -0.002, 0.435),
               (0.065, 0.018, 0.420), m["edge"], 0.012)
    for i, (x, z) in enumerate(((-0.105, 0.655), (0.105, 0.655),
                                (-0.105, 0.230), (0.105, 0.230))):
        cylinder("Parafuso de parede %02d" % i, (x, -0.012, z), 0.020, 0.018,
                 m["edge"], rotation=(math.pi / 2, 0, 0))
        cylinder("Fenda do parafuso %02d" % i, (x, -0.023, z), 0.003, 0.003,
                 m["dark"], rotation=(math.pi / 2, 0, 0))
    for side, x in ((-1, -0.145), (1, 0.145)):
        torus("Olhal de parede %s" % side, (side * 0.095, -0.035, 0.670),
              0.032, 0.008, m["edge"], rotation=(math.pi / 2, 0, 0), segments=24)
        start = (side * 0.095, -0.050, 0.660)
        end_x = x - side * 0.012
        chain_links("Corrente suspensa %s" % side,
                    [start, (side * 0.170, -0.105, 0.485),
                     (side * 0.220, -0.135, 0.300),
                     (end_x, -0.140, 0.205)], 14, 0.032, 0.0065, m["edge"])
        center = (x, -0.145, 0.125)
        arc = (math.pi / 2, 3 * math.pi / 2) if side < 0 else (-math.pi / 2, math.pi / 2)
        make_arc_cuff("Grilhão de parede %s" % side, center, 0.078, 0.014,
                      m["iron"], "wall", arc[0], arc[1])
        for j, angle in enumerate(arc):
            px = x + math.cos(angle) * 0.078
            pz = 0.125 + math.sin(angle) * 0.078
            cylinder("Fecho do grilhão %s-%d" % (side, j), (px, -0.145, pz),
                     0.017, 0.024, m["edge"], rotation=(math.pi / 2, 0, 0))
            sphere("Pino do grilhão %s-%d" % (side, j), (px, -0.162, pz),
                   (0.008, 0.005, 0.008), m["rust"], 12, 8)
    return ("Par de grilhões abertos em placa rebitada à parede",
            (0.95, -1.60, 0.86), (0, -0.02, 0.40), 1.12,
            (0, -2.2, 0.42), 1.04)


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def add_lights(target):
    scene = bpy.context.scene
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.075, 0.083, 0.095, 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.32
    for name, loc, energy, size, color in (
        ("Luz principal", (1.1, -1.4, 1.8), 75, 1.0, (1.0, 0.86, 0.68)),
        ("Preenchimento", (-1.1, -0.6, 0.95), 35, 1.2, (0.78, 0.86, 1.0)),
        ("Recorte", (0.2, 1.0, 1.4), 65, 0.8, (1.0, 0.70, 0.44)),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        lamp = bpy.context.object
        lamp.name = name
        lamp.data.energy = energy
        lamp.data.shape = "DISK"
        lamp.data.size = size
        lamp.data.color = color
        point_at(lamp, target)


def render_camera(name, location, target, ortho_scale):
    bpy.ops.object.camera_add(location=location)
    camera = bpy.context.object
    camera.name = name
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = ortho_scale
    point_at(camera, target)
    bpy.context.scene.camera = camera
    return camera


def export_one(slug, builder, wall=False):
    clear_scene()
    setup = builder()
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 1050
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    scene.render.filepath = str(OUT / (slug + "_preview.png"))
    add_lights(setup[2])
    render_camera("Câmera de prévia", setup[1], setup[2], setup[3])
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / (slug + ".blend")))
    bpy.ops.render.render(write_still=True)
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.filepath = str(OUT / (slug + ".png"))
    render_camera("Câmera do ícone 2D", setup[4], (0, 0, 0) if not wall else (0, 0, 0.40), setup[5])
    bpy.ops.render.render(write_still=True)
    bpy.ops.object.select_all(action="DESELECT")
    meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.export_scene.gltf(filepath=str(OUT / (slug + ".glb")),
                              export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True,
                              export_materials="EXPORT")
    print("ASSET_EXPORT", slug, "meshes=", len(meshes), "wall=", wall)


def build():
    bpy.context.scene.unit_settings.system = "METRIC"
    export_one("bola_corrente", build_floor_ball_chain)
    export_one("grilhoes_parede", build_wall_shackles, wall=True)


if __name__ == "__main__":
    build()
