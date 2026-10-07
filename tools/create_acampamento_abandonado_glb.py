"""Cria a miniatura 3D de um acampamento abandonado para decorações."""
from __future__ import annotations

import math
import random
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)
SLUG = "acampamento_abandonado"


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


def uv(name, pos, scale, material, segments=14, rings=8, smooth=False,
       rotation=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                        radius=1, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    if rotation:
        obj.rotation_euler = rotation
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    for p in obj.data.polygons:
        p.use_smooth = smooth
    return obj


def beam(name, start, end, radius, material, sides=9):
    delta = Vector(end) - Vector(start)
    bpy.ops.mesh.primitive_cone_add(vertices=sides, radius1=radius,
                                    radius2=radius * 0.68, depth=delta.length,
                                    location=(Vector(start) + Vector(end)) * 0.5)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(material)
    for p in obj.data.polygons:
        p.use_smooth = False
    return obj


def curve(name, points, material, bevel=0.01):
    c = bpy.data.curves.new(name + " curve", "CURVE")
    c.dimensions = "3D"
    c.resolution_u = 6
    c.bevel_depth = bevel
    c.bevel_resolution = 2
    s = c.splines.new("BEZIER")
    s.bezier_points.add(len(points) - 1)
    for bp, point in zip(s.bezier_points, points):
        bp.co = point
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, c)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.object
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def ground(rng, soil, dry_grass):
    # Tapete irregular de terra/areia com a escala compatível com 2x2 casas.
    count = 48
    rings = ((0.0, 0.045), (0.62, 0.055), (0.88, 0.035), (1.0, 0.012))
    verts, faces = [(0, 0, 0.045)], []
    for ri, (r, z) in enumerate(rings[1:]):
        for i in range(count):
            a = math.tau * i / count
            wobble = 1 + 0.035 * math.sin(a * 5 + 0.8) + 0.02 * math.cos(a * 9)
            rr = r * wobble
            verts.append((0.94 * rr * math.cos(a), 0.89 * rr * math.sin(a),
                          z + (rng.uniform(-0.009, 0.009) if ri >= 1 else 0)))
    for i in range(count):
        faces.append((0, 1 + (i + 1) % count, 1 + i))
    for ri in range(len(rings[1:]) - 1):
        for i in range(count):
            a = 1 + ri * count + i
            b = 1 + ri * count + (i + 1) % count
            c = 1 + (ri + 1) * count + (i + 1) % count
            d = 1 + (ri + 1) * count + i
            faces.append((a, b, c, d))
    mesh = bpy.data.meshes.new("Chão de terra mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(soil)
    mesh.update()
    obj = bpy.data.objects.new("Chão de terra batida", mesh)
    bpy.context.collection.objects.link(obj)
    for p in mesh.polygons:
        p.use_smooth = True

    # Tufo seco ralo e folhas mortas quebram a borda sem competir com o fogo.
    for i in range(12):
        a = math.tau * i / 12 + rng.uniform(-0.15, 0.15)
        x, y = 0.78 * math.cos(a), 0.72 * math.sin(a)
        if -0.58 < x < 0.30 and -0.68 < y < -0.12:
            continue
        h = rng.uniform(0.055, 0.13)
        tip = (x + math.cos(a) * 0.05, y + math.sin(a) * 0.05, h + 0.02)
        curve("Capim seco do acampamento", [(x, y, 0.04),
              (x + math.cos(a) * 0.025, y + math.sin(a) * 0.025, h * 0.62), tip],
              dry_grass, 0.008)


def cloth_panel(name, side, canvas, rng, patch):
    """Lona caída em ondas com bainha rasgada e falhas abertas no tecido."""
    across, depth = 5, 9
    verts, faces = [], []
    for j in range(depth):
        v = j / (depth - 1)
        y = -0.30 + v * 1.08
        ridge_z = 1.08 - 0.18 * v + 0.025 * math.sin(v * 7)
        bottom_z = 0.10 + 0.07 * math.sin(v * 19 + side) + 0.025 * math.sin(v * 31)
        if j in (2, 5, 7):
            bottom_z += 0.12 if j % 2 else -0.025
        edge_x = side * (0.72 + 0.035 * math.sin(v * 17))
        for i in range(across):
            u = i / (across - 1)
            x = side * (0.015 + (abs(edge_x) - 0.015) * u)
            z = ridge_z * (1 - u) + bottom_z * u
            z += 0.025 * math.sin(u * 8 + v * 13 + side) * math.sin(u * math.pi)
            verts.append((x, y + 0.018 * math.sin(u * 5 + v * 16), z))
    for j in range(depth - 1):
        for i in range(across - 1):
            # Duas falhas irregulares: rasgos reais em vez de pinturas escuras.
            if (side > 0 and ((j in (3, 4) and i in (2, 3)) or
                              (j == 6 and i == 1))):
                continue
            a = j * across + i
            b = a + 1
            c = (j + 1) * across + i + 1
            d = c - 1
            faces.append((a, b, c, d) if side > 0 else (d, c, b, a))
    mesh = bpy.data.meshes.new(name + " mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(canvas)
    mesh.materials.append(patch)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for p in mesh.polygons:
        p.use_smooth = True

    # Remendos chatos acompanham a inclinação da lona em vez de parecerem pedras.
    def panel_point(u, v):
        y = -0.30 + v * 1.08
        ridge_z = 1.08 - 0.18 * v + 0.025 * math.sin(v * 7)
        bottom_z = 0.10 + 0.07 * math.sin(v * 19 + side) + 0.025 * math.sin(v * 31)
        edge_x = side * (0.72 + 0.035 * math.sin(v * 17))
        x = side * (0.015 + (abs(edge_x) - 0.015) * u) + side * 0.004
        z = ridge_z * (1 - u) + bottom_z * u
        z += 0.025 * math.sin(u * 8 + v * 13 + side) * math.sin(u * math.pi)
        return (x, y + 0.018 * math.sin(u * 5 + v * 16), z)

    for k, (u, v) in enumerate(((0.43, 0.20), (0.68, 0.76))):
        verts_patch = [panel_point(u - 0.055, v - 0.045),
                       panel_point(u + 0.055, v - 0.045),
                       panel_point(u + 0.055, v + 0.045),
                       panel_point(u - 0.055, v + 0.045)]
        patch_mesh = bpy.data.meshes.new(name + " remendo mesh")
        patch_mesh.from_pydata(verts_patch, [], [(0, 1, 2, 3)])
        patch_mesh.materials.append(patch)
        patch_mesh.update()
        patch_obj = bpy.data.objects.new(name + " | remendo costurado %02d" % k, patch_mesh)
        bpy.context.collection.objects.link(patch_obj)
    for v in (0.31, 0.66, 0.92):
        y = -0.30 + v * 1.08
        x = side * (0.70 + 0.035 * math.sin(v * 17))
        z = 0.13 + 0.04 * math.sin(v * 19 + side)
        curve(name + " | fio desfiado", [(x, y, z),
              (x + side * 0.055, y + 0.025, z - 0.06),
              (x + side * 0.07, y + 0.055, z - 0.12)], canvas, 0.006)


def build(rng):
    soil = mat("Terra empoeirada", (0.37, 0.27, 0.17))
    dry_grass = mat("Palha morta", (0.47, 0.38, 0.20))
    stone = [mat("Pedra da fogueira | cinza", (0.36, 0.34, 0.30)),
             mat("Pedra da fogueira | luz", (0.49, 0.45, 0.38)),
             mat("Pedra da fogueira | fuligem", (0.23, 0.22, 0.20))]
    ash = [mat("Cinza fria", (0.32, 0.30, 0.27)),
           mat("Cinza clara", (0.48, 0.45, 0.40)),
           mat("Carvão apagado", (0.105, 0.085, 0.065))]
    wood = [mat("Madeira velha", (0.30, 0.19, 0.10)),
            mat("Madeira carbonizada", (0.105, 0.075, 0.055)),
            mat("Fibras queimadas", (0.20, 0.13, 0.075))]
    canvas = mat("Lona abandonada | cáqui gasto", (0.34, 0.32, 0.24))
    canvas_light = mat("Lona rasgada | fio claro", (0.48, 0.42, 0.29))
    patch = mat("Remendos de pano escuro", (0.25, 0.24, 0.19))
    rope = mat("Cordame apodrecido", (0.30, 0.23, 0.13))

    ground(rng, soil, dry_grass)

    # Fogueira apagada: aro de pedras, cinza sem brilho e três lenhos frios.
    fire_x, fire_y = -0.28, -0.39
    uv("Canteiro de cinza fria", (fire_x, fire_y, 0.075), (0.43, 0.31, 0.055),
       ash[0], 18, 8, True)
    uv("Cinza clara no centro", (fire_x - 0.025, fire_y + 0.01, 0.105),
       (0.29, 0.20, 0.035), ash[1], 16, 7, True)
    for i in range(9):
        a = math.tau * i / 9 + 0.15
        x, y = fire_x + 0.38 * math.cos(a), fire_y + 0.27 * math.sin(a)
        size = rng.uniform(0.10, 0.15)
        rock = uv("Pedra escurecida do aro %02d" % i,
                  (x, y, 0.105), (size, size * 0.76, rng.uniform(0.07, 0.10)),
                  stone[i % len(stone)], 10, 6, False,
                  (rng.uniform(-0.2, 0.2), rng.uniform(-0.2, 0.2), a))
    # Lenha cruzada, preta e rachada. Sem chama, brilho ou fumaça.
    for i, (start, end, radius) in enumerate((
        ((fire_x - 0.24, fire_y - 0.11, 0.14), (fire_x + 0.21, fire_y + 0.12, 0.18), 0.055),
        ((fire_x - 0.16, fire_y + 0.15, 0.16), (fire_x + 0.18, fire_y - 0.14, 0.15), 0.046),
        ((fire_x - 0.10, fire_y - 0.17, 0.16), (fire_x + 0.12, fire_y + 0.17, 0.17), 0.035),
    )):
        beam("Lenho carbonizado %02d" % i, start, end, radius, wood[1], 9)
        # Faixas ásperas de carvão em uma face superior dos galhos.
        mid = tuple((start[k] + end[k]) * 0.5 for k in range(3))
        uv("Fissura de carvão", (mid[0], mid[1], mid[2] + radius * 0.8),
           (radius * 0.65, radius * 0.18, 0.012), ash[2], 8, 5, False)
    for i in range(7):
        a = rng.uniform(0, math.tau)
        r = rng.uniform(0.12, 0.38)
        uv("Pedaço de carvão frio", (fire_x + math.cos(a) * r,
           fire_y + math.sin(a) * r * 0.7, 0.112),
           (0.025, 0.018, 0.012), ash[2], 8, 5, False)

    # Estrutura de lona caída atrás do fogo, com um suporte partido e estais frouxos.
    pole = mat("Estacas de madeira rachadas", (0.27, 0.17, 0.085))
    beam("Estaca dianteira inclinada", (-0.08, -0.29, 0.04),
         (-0.01, -0.29, 1.13), 0.038, pole)
    beam("Estaca traseira partida", (0.03, 0.76, 0.04),
         (0.02, 0.76, 0.89), 0.040, pole)
    # Lasca exposta na quebra da estaca do fundo.
    beam("Ponta quebrada da estaca", (0.02, 0.76, 0.85),
         (0.10, 0.73, 0.97), 0.026, wood[0], 6)
    beam("Travessa frouxa", (-0.02, -0.28, 1.08),
         (0.02, 0.75, 0.90), 0.027, pole, 8)
    cloth_panel("Pano rasgado esquerdo", -1, canvas, rng, patch)
    cloth_panel("Pano rasgado direito", 1, canvas, rng, patch)

    # Cordas frouxas ainda presas a pequenas estacas no chão.
    for sign in (-1, 1):
        peg_x, peg_y = sign * 0.82, -0.08
        beam("Estaca de amarração", (peg_x, peg_y, 0.02),
             (peg_x + 0.02, peg_y, 0.30), 0.022, pole, 7)
        curve("Corda frouxa", [(0.0, -0.22, 1.00),
              (sign * 0.38, -0.19, 0.55), (peg_x, peg_y, 0.24)], rope, 0.009)

    # Faixa solta no chão, a mesma lona já desfiada pelo vento.
    scrap = uv("Retalho de lona no chão", (0.58, -0.48, 0.072),
               (0.22, 0.105, 0.018), canvas, 12, 6, False,
               (0.02, 0.05, -0.52))
    scrap.name = "Retalho de lona abandonado"


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
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.09, 0.075, 0.055, 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.30
    for name, loc, energy, size, color in (
        ("Luz quente lateral", (2.6, -3.3, 4.5), 300, 3.0, (1.0, 0.78, 0.55)),
        ("Preenchimento frio", (-3.0, -0.4, 2.8), 190, 2.8, (0.74, 0.83, 1.0)),
        ("Recorte suave", (0.1, 3.1, 3.7), 230, 2.5, (1.0, 0.72, 0.46)),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.data.color = color
        point_at(light, (0, 0, 0.50))
    bpy.ops.object.camera_add(location=(2.7, -3.9, 2.8))
    camera = bpy.context.object
    camera.name = "Câmera da miniatura"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 2.85
    point_at(camera, (0, 0.05, 0.53))
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
        group[0].name = "Acampamento | " + material.name


def export():
    clear_scene()
    build(random.Random(104051))
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
