"""Cria uma miniatura 3D de um pequeno oásis para o tabuleiro desértico."""
from __future__ import annotations

import math
import random
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)
SLUG = "oasis_pequeno"


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for data in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                 bpy.data.cameras, bpy.data.lights):
        for block in list(data):
            if block.users == 0:
                data.remove(block)


def mat(name, color, roughness=0.86, metallic=0.0):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    return material


def ellipsoid(name, pos, scale, material, segments=16, rings=10,
              smooth=True, rotation=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                        radius=1, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    if rotation:
        obj.rotation_euler = rotation
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    for face in obj.data.polygons:
        face.use_smooth = smooth
    return obj


def tube(name, points, radii, material, bevel=0.018, resolution=8):
    path = bpy.data.curves.new(name + " curve", "CURVE")
    path.dimensions = "3D"
    path.resolution_u = resolution
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


def make_sandy_island(rng, sand_mats):
    """O disco irregular dá uma borda firme e uma elevação baixa de areia."""
    count = 64
    rings = ((0.62, 0.20), (0.84, 0.24), (0.96, 0.13), (1.0, 0.035))
    verts, faces, face_materials = [], [], []
    verts.append((0.0, 0.0, 0.17))
    for ri, (radius, z) in enumerate(rings):
        for i in range(count):
            a = math.tau * i / count
            wobble = 1 + 0.025 * math.sin(5 * a + 0.4) + 0.018 * math.sin(9 * a)
            r = radius * wobble
            verts.append((1.94 * r * math.cos(a), 1.86 * r * math.sin(a),
                          z + (rng.uniform(-0.012, 0.012) if ri in (2, 3, 4) else 0)))
    for i in range(count):
        faces.append((0, 1 + (i + 1) % count, 1 + i))
        face_materials.append(0)
    for ri in range(len(rings) - 1):
        for i in range(count):
            a = 1 + ri * count + i
            b = 1 + ri * count + (i + 1) % count
            c = 1 + (ri + 1) * count + (i + 1) % count
            d = 1 + (ri + 1) * count + i
            faces.append((a, b, c, d))
            face_materials.append(0)
    mesh = bpy.data.meshes.new("Ilha baixa de areia mesh")
    mesh.from_pydata(verts, [], faces)
    for material in sand_mats:
        mesh.materials.append(material)
    mesh.update()
    island = bpy.data.objects.new("Ilha baixa de areia", mesh)
    bpy.context.collection.objects.link(island)
    for poly, index in zip(mesh.polygons, face_materials):
        poly.material_index = index
        poly.use_smooth = True


def make_water(rng, water_mats):
    """Bacia elíptica com prateleira azul clara e lâmina irregular turquesa."""
    count = 64
    rings = ((0.70, 0.205), (0.88, 0.222), (1.0, 0.238))
    rx, ry, cy = 1.18, 0.91, -0.22
    verts, faces, assignments = [], [], []
    verts.append((0.0, cy, 0.214))
    for ri, (radius, z) in enumerate(rings):
        for i in range(count):
            a = math.tau * i / count
            wobble = 1 + 0.025 * math.sin(4 * a + 0.6) + 0.016 * math.cos(7 * a)
            r = radius * wobble
            verts.append((rx * r * math.cos(a), cy + ry * r * math.sin(a),
                          z + 0.008 * math.sin(3 * a + ri)))
    # Centro único + leque de triângulos evita uma tampa com vértices coincidentes.
    for i in range(count):
        faces.append((0, 1 + i, 1 + (i + 1) % count))
        assignments.append(1)
    for ri in range(len(rings) - 1):
        for i in range(count):
            a = 1 + ri * count + i
            b = 1 + ri * count + (i + 1) % count
            c = 1 + (ri + 1) * count + (i + 1) % count
            d = 1 + (ri + 1) * count + i
            faces.append((a, b, c, d))
            assignments.append(0 if ri == 0 else 2)
    mesh = bpy.data.meshes.new("Lago turquesa mesh")
    mesh.from_pydata(verts, [], faces)
    for material in water_mats:
        mesh.materials.append(material)
    mesh.update()
    water = bpy.data.objects.new("Lago turquesa raso", mesh)
    bpy.context.collection.objects.link(water)
    for poly, index in zip(mesh.polygons, assignments):
        poly.material_index = index
        poly.use_smooth = True

    # Pequenas ondas claras dão leitura de água sem transformar o lago em gelo.
    ripple = water_mats[3]
    for i, (x, y, length, angle) in enumerate((
        (-0.42, -0.38, 0.22, -0.18), (0.34, -0.13, 0.17, 0.24),
        (-0.03, 0.19, 0.25, -0.10), (0.55, 0.24, 0.11, 0.34),
    )):
        tube("Reflexo ondulado %02d" % i,
             [(x - length / 2, y, 0.255), (x, y + 0.018, 0.259),
              (x + length / 2, y, 0.255)], [0.1, 0.9, 0.1], ripple, 0.009, 5)


def make_rock(name, pos, scale, material, rotation, rng):
    rock = ellipsoid(name, pos, scale, material, 12, 7, False, rotation)
    # Pequena irregularidade facetada evita seixos com aparência de bolinhas.
    for vertex in rock.data.vertices:
        fac = rng.uniform(0.93, 1.07)
        vertex.co *= fac
    return rock


def make_palm(name, x, y, height, lean_x, lean_y, rng, bark_mats, leaf_mats, nut_mat):
    # Tronco afunilado em anéis deslocados, com sulcos naturais e leve curvatura.
    rings, sides = 14, 12
    verts, faces, materials = [], [], []
    for ri in range(rings + 1):
        t = ri / rings
        cx = x + lean_x * t * t + 0.035 * math.sin(t * 4.1 + x)
        cy = y + lean_y * t * t
        z = 0.23 + height * t
        radius = 0.125 * (1 - 0.48 * t) * (1 + 0.025 * math.sin(t * 35))
        for j in range(sides):
            a = math.tau * j / sides
            rib = 1 + 0.045 * math.cos(a * 6 + t * 8)
            verts.append((cx + radius * rib * math.cos(a),
                          cy + radius * rib * math.sin(a), z))
    for ri in range(rings):
        for j in range(sides):
            a = ri * sides + j
            b = ri * sides + (j + 1) % sides
            faces.append((a, b, b + sides, a + sides))
            materials.append((ri // 2 + j // 4) % len(bark_mats))
    faces.append(tuple(reversed(range(sides))))
    materials.append(0)
    faces.append(tuple(rings * sides + j for j in range(sides)))
    materials.append(1)
    mesh = bpy.data.meshes.new(name + " trunk mesh")
    mesh.from_pydata(verts, [], faces)
    for material in bark_mats:
        mesh.materials.append(material)
    mesh.update()
    trunk = bpy.data.objects.new(name + " | tronco curvo", mesh)
    bpy.context.collection.objects.link(trunk)
    for poly, index in zip(mesh.polygons, materials):
        poly.material_index = index
        poly.use_smooth = True

    crown = (x + lean_x, y + lean_y, 0.23 + height)
    # Cicatrizes horizontais espaçadas e discretas no tronco.
    for level in (0.18, 0.35, 0.52, 0.69, 0.83):
        t = level
        cx = x + lean_x * t * t + 0.035 * math.sin(t * 4.1 + x)
        cy = y + lean_y * t * t
        z = 0.23 + height * t
        radius = 0.125 * (1 - 0.48 * t) * 1.012
        tube(name + " | anel do tronco", [(cx - radius, cy, z), (cx, cy - radius, z + .004),
             (cx + radius, cy, z)], [0.12, 0.25, 0.12], bark_mats[2], 0.008, 4)

    # Cocos pequenos aparecem entre as frondes no topo.
    for i in range(4):
        a = math.tau * i / 4 + 0.3
        ellipsoid(name + " | coco %02d" % i,
                  (crown[0] + math.cos(a) * 0.105, crown[1] + math.sin(a) * 0.105,
                   crown[2] - 0.08), (0.075, 0.071, 0.082), nut_mat, 12, 8, True)

    # Frondes pinadas; cada folíolo é uma lâmina estreita e arqueada, não uma esfera.
    fronds = 9
    for fi in range(fronds):
        a = math.tau * fi / fronds + rng.uniform(-0.13, 0.13)
        dx, dy = math.cos(a), math.sin(a)
        side_x, side_y = -dy, dx
        length = rng.uniform(0.82, 1.08)
        lift = rng.uniform(0.17, 0.34)
        droop = rng.uniform(0.36, 0.53)
        rachis_points = []
        for step in range(5):
            t = step / 4
            reach = length * t
            z = crown[2] + lift * math.sin(t * math.pi * 0.72) - droop * t * t
            rachis_points.append((crown[0] + dx * reach,
                                  crown[1] + dy * reach, z))
        leafmat = leaf_mats[fi % len(leaf_mats)]
        # Cápsulas curtas formam a nervura central. Mantêm o filete contínuo e
        # evitam tubos Bezier muito curvos no GLB, que alguns importadores reparam.
        for si, (start, end) in enumerate(zip(rachis_points, rachis_points[1:])):
            start_v, end_v = Vector(start), Vector(end)
            delta = end_v - start_v
            rib = ellipsoid(name + " | nervura %02d segmento %02d" % (fi, si),
                            (start_v + end_v) * 0.5,
                            (0.014, 0.014, delta.length * 0.58), leafmat, 10, 6)
            rib.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()

        leaf_verts, leaf_faces = [], []
        pairs = 13
        for j in range(1, pairs + 1):
            t = 0.12 + 0.82 * j / (pairs + 1)
            reach = length * t
            base_z = crown[2] + lift * math.sin(t * math.pi * 0.72) - droop * t * t
            span = (0.22 + 0.07 * math.sin(math.pi * t)) * (1 - 0.26 * t)
            # O ângulo fecha no fim da fronde, mantendo a copa compacta.
            for sign in (-1, 1):
                base = (crown[0] + dx * reach, crown[1] + dy * reach, base_z)
                tip_t = min(1.0, t + 0.045)
                tip_r = length * tip_t
                tip = (crown[0] + dx * tip_r + side_x * sign * span,
                       crown[1] + dy * tip_r + side_y * sign * span,
                       base_z - span * 0.43 - 0.035)
                mid = (crown[0] + dx * (reach + length * 0.025) + side_x * sign * span * 0.56,
                       crown[1] + dy * (reach + length * 0.025) + side_y * sign * span * 0.56,
                       base_z - span * 0.19 - 0.006)
                start_i = len(leaf_verts)
                leaf_verts.extend((base, mid, tip))
                leaf_faces.append((start_i, start_i + 1, start_i + 2))
        leaf_mesh = bpy.data.meshes.new(name + " fronde folíolos mesh")
        leaf_mesh.from_pydata(leaf_verts, [], leaf_faces)
        leaf_mesh.materials.append(leafmat)
        leaf_mesh.update()
        leaf_obj = bpy.data.objects.new(name + " | folíolos da fronde %02d" % fi, leaf_mesh)
        bpy.context.collection.objects.link(leaf_obj)
        # As faces são visíveis dos dois lados, mesmo em corte baixo no tabuleiro.
        for poly in leaf_mesh.polygons:
            poly.use_smooth = True


def build(rng):
    sand = [mat("Areia dourada", (0.57, 0.39, 0.19)),
            mat("Areia iluminada", (0.73, 0.55, 0.30)),
            mat("Areia em sombra", (0.42, 0.29, 0.15))]
    water = [mat("Água rasa | turquesa", (0.12, 0.56, 0.54), 0.42, 0.0),
             mat("Água funda | azul petróleo", (0.035, 0.43, 0.48), 0.60, 0.0),
             mat("Água da margem | verde clara", (0.24, 0.69, 0.62), 0.45, 0.0),
             mat("Reflexos suaves", (0.58, 0.84, 0.72), 0.25, 0.0)]
    rock_mats = [mat("Pedra calcária clara", (0.63, 0.55, 0.40)),
                 mat("Pedra ocre", (0.49, 0.39, 0.26)),
                 mat("Pedra sombreada", (0.35, 0.31, 0.25))]
    bark = [mat("Palmeira | casca quente", (0.35, 0.19, 0.085)),
            mat("Palmeira | fibra clara", (0.56, 0.34, 0.16)),
            mat("Palmeira | anéis escuros", (0.22, 0.12, 0.06))]
    leaves = [mat("Folhas | verde esmeralda", (0.13, 0.36, 0.17)),
              mat("Folhas | verde ao sol", (0.26, 0.51, 0.20)),
              mat("Folhas | verde profundo", (0.075, 0.24, 0.13))]
    nut = mat("Cocos maduros", (0.25, 0.13, 0.055))

    make_sandy_island(rng, sand)
    make_water(rng, water)

    # Pedras de margem alternam formas e alturas; o centro do lago fica aberto.
    rocks = [((-1.35, -0.24, 0.25), (0.35, 0.27, 0.25), 0),
             ((-0.94, -0.98, 0.23), (0.38, 0.25, 0.21), 1),
             ((0.70, -1.02, 0.22), (0.42, 0.27, 0.20), 0),
             ((1.42, -0.38, 0.25), (0.32, 0.25, 0.27), 2),
             ((1.23, 0.77, 0.22), (0.38, 0.30, 0.20), 1),
             ((-1.17, 0.81, 0.24), (0.33, 0.27, 0.24), 0),
             ((0.12, -1.48, 0.15), (0.24, 0.16, 0.12), 2),
             ((-0.31, 1.31, 0.19), (0.28, 0.20, 0.16), 1)]
    for i, (pos, scale, mi) in enumerate(rocks):
        rot = (rng.uniform(-0.15, 0.15), rng.uniform(-0.2, 0.2), rng.uniform(-0.8, 0.8))
        make_rock("Rocha de margem %02d" % i, pos, scale, rock_mats[mi], rot, rng)

    # Três palmeiras em tamanhos diferentes emolduram o lago sem ocultá-lo.
    make_palm("Palmeira central", 0.18, 0.95, 2.08, 0.05, -0.05, rng, bark, leaves, nut)
    make_palm("Palmeira à esquerda", -1.30, 0.38, 1.78, 0.10, -0.03, rng, bark, leaves, nut)
    make_palm("Palmeira à direita", 1.20, 0.44, 1.88, -0.08, -0.04, rng, bark, leaves, nut)

    # Gramíneas muito baixas em poucos pontos, como transição natural entre areia e água.
    grass = [mat("Capim do oásis | verde-claro", (0.43, 0.52, 0.20)),
             mat("Capim do oásis | verde-sombra", (0.25, 0.36, 0.15))]
    for i, (x, y) in enumerate(((-0.74, -1.28), (0.94, -1.20), (-1.47, 0.38), (1.48, 0.35))):
        for blade in range(3):
            a = blade * math.tau / 3 + i * 0.55
            end = (x + math.cos(a) * 0.10, y + math.sin(a) * 0.10, 0.38 + 0.03 * blade)
            tube("Tufo baixo na margem %02d-%d" % (i, blade),
                 [(x, y, 0.21), ((x + end[0]) / 2, (y + end[1]) / 2, 0.31), end],
                 [0.65, 0.4, 0.03], grass[(i + blade) % 2], 0.015, 4)


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def setup_scene():
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.10, 0.09, 0.065, 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35
    for name, loc, energy, size, color in (
        ("Sol quente", (3.2, -4.0, 6.0), 420, 4.0, (1.0, 0.80, 0.57)),
        ("Preenchimento do céu", (-4.0, -0.2, 3.4), 250, 3.5, (0.73, 0.86, 1.0)),
        ("Recorte dourado", (0.0, 4.0, 5.0), 330, 2.8, (1.0, 0.78, 0.48)),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        lamp = bpy.context.object
        lamp.name = name
        lamp.data.energy = energy
        lamp.data.shape = "DISK"
        lamp.data.size = size
        lamp.data.color = color
        point_at(lamp, (0, 0, 1.05))
    bpy.ops.object.camera_add(location=(5.0, -7.4, 5.0))
    camera = bpy.context.object
    camera.name = "Câmera da miniatura"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 5.45
    point_at(camera, (0, 0, 1.17))
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
        group[0].name = "Oásis | " + material.name


def export():
    clear_scene()
    build(random.Random(102021))
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
