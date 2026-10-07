"""Gera miniaturas Blender para a moita espinhosa e o capim alto.

Para cada decoração, exporta .blend editável, GLB do jogo, PNG transparente
para o editor/mapa 2D e uma prévia 3D em ângulo.
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


def mat(name, color, roughness=0.86):
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


def ellipsoid(name, center, scale, material, segments=18, rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                        radius=1, location=center)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, material)
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def tube(name, points, radius, material):
    curve = bpy.data.curves.new(name + " path", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 6
    curve.bevel_depth = radius
    curve.bevel_resolution = 2
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for p, co in zip(spline.points, points):
        p.co = (*co, 1)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.object
    obj.select_set(False)
    return obj


def thorn(name, base, tip, radius, material):
    a, b = Vector(base), Vector(tip)
    delta = b - a
    bpy.ops.mesh.primitive_cone_add(vertices=9, radius1=radius, radius2=0.001,
                                    depth=delta.length, location=(a + b) * 0.5)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = delta.to_track_quat("Z", "Y")
    assign(obj, material)
    bevel = obj.modifiers.new("Ponta natural", "BEVEL")
    bevel.width = 0.003
    bevel.segments = 1
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    return obj


def blade(name, points, width, material):
    """Folha comprida em fita facetada, com nervura central e ponta fina."""
    pts = [Vector(p) for p in points]
    verts, faces = [], []
    for i, p in enumerate(pts):
        tangent = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        side = tangent.cross(Vector((0.0, 1.0, 0.0)))
        if side.length < 1e-5:
            side = tangent.cross(Vector((1.0, 0.0, 0.0)))
        side.normalize()
        f = i / (len(pts) - 1)
        envelope = (math.sin(math.pi * f) ** 0.72) * (0.82 + 0.18 * math.sin(f * 11.0))
        half = max(0.002, width * envelope)
        ridge = Vector((0, 0, 0.006 * math.sin(math.pi * f)))
        verts.extend((tuple(p - side * half), tuple(p + ridge), tuple(p + side * half)))
    for i in range(len(pts) - 1):
        a = i * 3
        b = a + 3
        faces.extend(((a, a + 1, b + 1, b), (a + 1, a + 2, b + 2, b + 1)))
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def thorn_bush(rng):
    bark = [mat("Galhos | madeira castanha", (0.20, 0.095, 0.045)),
            mat("Galhos | luz da casca", (0.32, 0.16, 0.065))]
    thorn_m = mat("Espinhos | pontas de madeira", (0.40, 0.25, 0.11))
    leaves = [mat("Folhas | verde profundo", (0.035, 0.105, 0.030)),
              mat("Folhas | verde bosque", (0.060, 0.16, 0.040)),
              mat("Folhas | verde novo", (0.095, 0.20, 0.045)),
              mat("Folhas | sombra", (0.025, 0.075, 0.025))]
    # Galhos entrelaçados saem de uma base baixa e se abrem em direções variadas.
    branch_paths = []
    for i in range(11):
        a = 2 * math.pi * i / 11 + rng.uniform(-0.20, 0.20)
        reach = rng.uniform(0.25, 0.37)
        base = (rng.uniform(-0.055, 0.055), rng.uniform(-0.055, 0.055), 0.035)
        mid = (math.cos(a) * reach * 0.52, math.sin(a) * reach * 0.52,
               rng.uniform(0.20, 0.34))
        end = (math.cos(a) * reach, math.sin(a) * reach,
               rng.uniform(0.30, 0.50))
        path = [base, mid, end]
        branch_paths.append(path)
        tube("Ramo espinhoso %02d" % i, path, rng.uniform(0.009, 0.015),
             bark[i % len(bark)])
        # Um ou dois espinhos na haste, projetados para fora do arbusto.
        for j, t in enumerate((0.42, 0.76)):
            anchor = Vector(mid).lerp(Vector(end), t)
            direction = Vector((math.cos(a) * 0.8 + rng.uniform(-0.3, 0.3),
                                math.sin(a) * 0.8 + rng.uniform(-0.3, 0.3),
                                rng.uniform(0.12, 0.48))).normalized()
            length = rng.uniform(0.065, 0.105)
            thorn("Espinho %02d-%d" % (i, j), anchor,
                  anchor + direction * length, rng.uniform(0.012, 0.019), thorn_m)
        # Folhas ovais estreitas em pares, alternando alturas e ângulos.
        for j, t in enumerate((0.30, 0.54, 0.78)):
            anchor = Vector(base).lerp(Vector(end), t)
            for side_sign in (-1, 1):
                leaf_dir = Vector((math.cos(a + side_sign * 0.75),
                                   math.sin(a + side_sign * 0.75),
                                   rng.uniform(0.12, 0.44))).normalized()
                tip = anchor + leaf_dir * rng.uniform(0.085, 0.13)
                mid = anchor.lerp(tip, 0.52) + Vector((0, 0, 0.018))
                blade("Folha pontuda %02d-%d-%d" % (i, j, side_sign),
                      [anchor, mid, tip], rng.uniform(0.015, 0.022), rng.choice(leaves))
    # Folhas pontudas no centro dão volume sem a aparência de bolas lisas.
    for i in range(20):
        a = rng.uniform(0, math.tau)
        r = rng.uniform(0.05, 0.23)
        z = rng.uniform(0.20, 0.42)
        base = Vector((math.cos(a) * r, math.sin(a) * r, z))
        direction = Vector((math.cos(a) * rng.uniform(0.5, 1.0),
                            math.sin(a) * rng.uniform(0.5, 1.0),
                            rng.uniform(0.35, 0.85))).normalized()
        tip = base + direction * rng.uniform(0.12, 0.22)
        mid = base.lerp(tip, 0.54) + Vector((0, 0, 0.025))
        blade("Folha central %02d" % i, [base, mid, tip],
              rng.uniform(0.018, 0.027), rng.choice(leaves))
    # Três ramos principais de silhueta ficam acima do centro, com pontas visíveis.
    for i, path in enumerate(branch_paths[::4]):
        p = Vector(path[-1])
        d = Vector((p.x, p.y, 0.25)).normalized()
        thorn("Espinho de silhueta %d" % i, p, p + d * 0.13, 0.021, thorn_m)


def tall_grass(rng):
    greens = [mat("Capim | verde sombra", (0.045, 0.15, 0.045)),
              mat("Capim | verde folha", (0.09, 0.26, 0.055)),
              mat("Capim | verde claro", (0.20, 0.36, 0.075)),
              mat("Capim | verde frio", (0.055, 0.20, 0.10)),
              mat("Capim | pontas douradas", (0.38, 0.42, 0.12))]
    roots = []
    for i in range(44):
        a = rng.uniform(0, math.tau)
        r = rng.uniform(0.015, 0.24)
        x, y = math.cos(a) * r, math.sin(a) * r
        roots.append((x, y))
        height = rng.uniform(0.38, 0.68)
        bend = rng.uniform(-0.22, 0.22)
        reach = rng.uniform(0.11, 0.28)
        direction = a + rng.uniform(-0.60, 0.60)
        pts = []
        for j in range(7):
            t = j / 6
            sweep = reach * (t ** 1.45)
            pts.append((x + math.cos(direction) * sweep + bend * t * t,
                        y + math.sin(direction) * sweep,
                        0.025 + height * t))
        blade("Lâmina de capim %02d" % i, pts, rng.uniform(0.017, 0.031),
              rng.choices(greens, weights=(24, 36, 16, 18, 6), k=1)[0])
    # Folhas baixas e curvadas cobrem as raízes sem formar uma placa sólida.
    for i in range(12):
        x, y = rng.choice(roots)
        angle = rng.uniform(0, math.tau)
        tip = (x + math.cos(angle) * rng.uniform(0.18, 0.30),
               y + math.sin(angle) * rng.uniform(0.18, 0.30),
               rng.uniform(0.20, 0.34))
        blade("Folha baixa %02d" % i, [(x, y, 0.02),
              (x * 0.55 + tip[0] * 0.45, y * 0.55 + tip[1] * 0.45, tip[2] * 0.42),
              (x * 0.20 + tip[0] * 0.80, y * 0.20 + tip[1] * 0.80, tip[2] * 0.82), tip],
              rng.uniform(0.021, 0.034), rng.choice(greens[:4]))


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def consolidate_meshes():
    for material in list(bpy.data.materials):
        group = [o for o in bpy.context.scene.objects
                 if o.type == "MESH" and material in o.data.materials[:]]
        if len(group) < 2:
            continue
        bpy.ops.object.select_all(action="DESELECT")
        for obj in group:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = group[0]
        bpy.ops.object.join()
        group[0].name = "Vegetação | " + material.name
        group[0].data.name = group[0].name + " Mesh"


def setup_camera(slug):
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1100
    scene.render.resolution_y = 1100
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.09, 0.12, 0.10, 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35
    for name, loc, energy, size, color in (
        ("Luz suave da floresta", (1.1, -1.5, 2.0), 65, 1.4, (1.0, 0.90, 0.72)),
        ("Preenchimento verde", (-1.4, -0.4, 1.2), 32, 1.2, (0.72, 0.92, 0.72)),
        ("Recorte de folhas", (0.3, 1.1, 1.7), 54, 0.9, (0.86, 1.0, 0.78)),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.data.color = color
        point_at(light, (0, 0, 0.30))
    bpy.ops.object.camera_add(location=(1.35, -2.15, 1.55))
    camera = bpy.context.object
    camera.name = "Câmera da miniatura"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 1.35
    point_at(camera, (0, 0, 0.31))
    scene.camera = camera
    scene.render.filepath = str(OUT / (slug + "_preview.png"))


def export_one(slug, build):
    clear_scene()
    rng = random.Random(1221 if slug == "moita_espinhosa" else 7221)
    build(rng)
    consolidate_meshes()
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
    export_one("moita_espinhosa", thorn_bush)
    export_one("capim_alto", tall_grass)


if __name__ == "__main__":
    build()
