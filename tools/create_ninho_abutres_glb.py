"""Gera a miniatura de ninho de abutres em PNG transparente e GLB."""
from __future__ import annotations

import math
import random
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)
SLUG = "ninho_abutres"


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                       bpy.data.cameras, bpy.data.lights):
        for data in list(collection):
            if data.users == 0:
                collection.remove(data)


def material(name, color, roughness=.82, bump=.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    if bump:
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 45
        noise.inputs["Detail"].default_value = 2.5
        relief = nodes.new("ShaderNodeBump")
        relief.inputs["Strength"].default_value = bump
        relief.inputs["Distance"].default_value = .012
        links.new(noise.outputs["Fac"], relief.inputs["Height"])
        links.new(relief.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def ellipsoid(name, pos, scale, mat, segments=20, rings=12, smooth=True):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                         radius=1, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    for face in obj.data.polygons:
        face.use_smooth = smooth
    return obj


def tube(name, points, radii, mat, bevel, resolution=8, sides=5):
    curve = bpy.data.curves.new(name + " curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = resolution
    curve.bevel_depth = bevel
    curve.bevel_resolution = 2
    curve.resolution_u = max(2, resolution)
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for bp, point, radius in zip(spline.bezier_points, points, radii):
        bp.co = point
        bp.radius = radius
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    return bpy.context.object


def feather(name, start, end, width, thickness, mat, ribs=6):
    a, b = Vector(start), Vector(end)
    axis = (b - a).normalized()
    side = axis.cross(Vector((0, 0, 1)))
    if side.length < .05:
        side = axis.cross(Vector((0, 1, 0)))
    side.normalize()
    normal = side.cross(axis).normalized()
    length = (b - a).length
    rings = ((0.0, .18), (.18, .70), (.48, 1.0), (.76, .76), (.92, .43), (1.0, .025))
    verts, faces = [], []
    for t, profile in rings:
        center = a + axis * (length * t)
        for j in range(ribs):
            angle = 2 * math.pi * j / ribs
            point = center + side * (math.cos(angle) * width * profile)
            point += normal * (math.sin(angle) * thickness * profile)
            verts.append(tuple(point))
    for i in range(len(rings) - 1):
        for j in range(ribs):
            p = i * ribs + j
            q = i * ribs + (j + 1) % ribs
            faces.append((p, q, q + ribs, p + ribs))
    faces.extend((tuple(reversed(range(ribs))),
                  tuple((len(rings)-1)*ribs+j for j in range(ribs))))
    mesh = bpy.data.meshes.new(name + " mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    return obj


def angular_ledge(rng, stone_mats):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1,
                                          location=(0, 0, .082))
    obj = bpy.context.object
    obj.name = "Afloramento de arenito sob o ninho"
    for vertex in obj.data.vertices:
        wobble = 1 + rng.uniform(-.065, .065)
        vertex.co.x *= .405 * wobble
        vertex.co.y *= .325 * wobble
        vertex.co.z = max(-.065, vertex.co.z * .09 * wobble)
    for mat in stone_mats:
        obj.data.materials.append(mat)
    for face in obj.data.polygons:
        face.use_smooth = False
        face.material_index = rng.choices((0, 1, 2), (5, 3, 2))[0]
    return obj


def build_nest(rng, twigs, straw, dark_wood):
    ellipsoid("Base entrelaçada do ninho", (0, .025, .145),
              (.31, .265, .10), dark_wood, 24, 12)
    # Repeated, irregular twig courses form a sturdy open bowl.
    for row in range(5):
        z = .135 + row * .019
        rx = .285 - row * .012
        ry = .238 - row * .010
        count = 17 if row % 2 == 0 else 14
        phase = row * .31
        points = []
        for index in range(count + 1):
            angle = math.tau * index / count
            wobble = 1 + .045 * math.sin(angle * 5 + phase) + rng.uniform(-.012, .012)
            points.append((rx * wobble * math.cos(angle),
                           .025 + ry * wobble * math.sin(angle),
                           z + .012 * math.sin(angle * 3 + phase)))
        tube("Volta de galhos trançados %02d" % row, points,
             [rng.uniform(.45, 1.0) for _ in points],
             rng.choice(twigs), rng.uniform(.008, .012), 4)

    # Broken twig ends extend beyond the rim and make the nest silhouette rough.
    for index in range(13):
        angle = rng.uniform(0, math.tau)
        inner = rng.uniform(.20, .26)
        outer = rng.uniform(.27, .335)
        y_bias = .025
        start = (inner * math.cos(angle), y_bias + inner * .83 * math.sin(angle),
                 rng.uniform(.17, .22))
        end = (outer * math.cos(angle + rng.uniform(-.12, .12)),
               y_bias + outer * .83 * math.sin(angle + rng.uniform(-.12, .12)),
               rng.uniform(.18, .26))
        middle = ((start[0]+end[0])*.5 + rng.uniform(-.025, .025),
                  (start[1]+end[1])*.5 + rng.uniform(-.02, .02),
                  (start[2]+end[2])*.5 + rng.uniform(-.015, .015))
        tube("Galho quebrado da borda %02d" % index, [start, middle, end],
             [1, .72, .12], rng.choice(twigs), rng.uniform(.006, .010), 5)

    # A shallow lining remains visible between the eggs and the bird.
    ellipsoid("Palha seca no fundo", (0, .005, .195), (.205, .15, .035),
              straw, 20, 8)
    for index in range(9):
        angle = math.tau * index / 9
        start = (.13 * math.cos(angle), .015 + .11 * math.sin(angle), .205)
        end = (.22 * math.cos(angle + .12), .025 + .18 * math.sin(angle + .12), .235)
        tube("Fibra clara da borda %02d" % index,
             [start, ((start[0]+end[0])*.5, (start[1]+end[1])*.5, .224), end],
             [1, .7, .1], straw, .004, 4)


def build_egg(name, pos, shell, spot, rng):
    x, y, z = pos
    ellipsoid(name, pos, (.047, .061, .064), shell, 20, 12)
    # Sparse, subdued speckles break up the smooth parchment-colored shell.
    for index in range(11):
        angle = rng.uniform(0, math.tau)
        h = rng.uniform(-.55, .65)
        radius = math.sqrt(max(.1, 1 - h*h))
        px = x + math.cos(angle) * .047 * radius * .97
        py = y + math.sin(angle) * .061 * radius * .97
        pz = z + h * .064 * .98
        ellipsoid(name + " speckle %02d" % index, (px, py, pz),
                  (.0045, .003, .006), spot, 8, 5)


def build_vulture(rng, plumage, flight, cream, skin, beak, eye, talon):
    # Body sits behind the eggs so both the bird and clutch stay readable.
    ellipsoid("Corpo compacto do abutre", (0, .15, .315),
              (.09, .135, .056), plumage[0], 24, 14)
    ellipsoid("Peito castanho dourado", (0, .045, .306),
              (.062, .052, .043), plumage[1], 20, 12)
    for index in range(7):
        x = (index - 3) * .023
        feather("Pluma de contorno do dorso %02d" % index,
                (x*.72, .045, .383 - abs(x)*.10),
                (x, .18 + abs(x)*.10, .36 - abs(x)*.08),
                .018, .005, plumage[index % len(plumage)])
    # Layer short overlapping feathers across the camera-facing flank so the
    # silhouette reads as plumage instead of one smooth, oversized body.
    for row in range(3):
        z = .276 + row * .024
        for col in range(5):
            x = (col - 2) * .032
            feather("Pluma do flanco %02d %02d" % (row, col),
                    (x * .75, .005, z + .008),
                    (x, .105, z - .004), .017, .0045,
                    plumage[(row + col) % len(plumage)])
    # Pale down collar separates the bare head from the dark body feathers.
    for index in range(9):
        angle = math.tau * index / 9
        feather("Pluma clara do colar %02d" % index,
                (.071*math.cos(angle), -.018, .354 + .026*math.sin(angle)),
                (.096*math.cos(angle), -.041, .35 + .023*math.sin(angle)),
                .014, .006, cream)

    # Folded wings: layered coverts over long dark flight feathers on each side.
    for side in (-1, 1):
        ellipsoid("Asa recolhida", (side*.068, .13, .323),
                  (.032, .092, .020), plumage[2], 18, 10)
        for index in range(7):
            t = index / 6
            feather("Rêmige da asa %s %02d" % (side, index),
                    (side*(.075 + .012*t), .055 + .025*t, .331 - .01*t),
                    (side*(.135 + .035*t), .18 + .055*t, .277 - .025*t),
                    .018, .005, flight[index % len(flight)])
        for index in range(6):
            t = index / 5
            feather("Pluma sobre a asa %s %02d" % (side, index),
                    (side*(.055 + .012*t), -.005 + .018*t, .33 - .008*t),
                    (side*(.11 + .03*t), -.005 + .035*t, .30 - .022*t),
                    .016, .0045, plumage[(index + 1) % len(plumage)])

    # A short fan of tail feathers extends behind the bird, away from the viewer.
    for index in range(7):
        spread = (index - 3) / 3
        feather("Pluma da cauda %02d" % index,
                (spread*.045, .235, .325),
                (spread*.12, .33 - abs(spread)*.035, .277 + abs(spread)*.015),
                .022, .007, flight[index % len(flight)])

    # Bare, dusky head and neck; a muted slate-red keeps it natural rather than cartoonish.
    tube("Pescoço nu do abutre", [(0, .035, .33), (.012, -.075, .402),
         (.025, -.132, .432)], [1.0, .82, .65], skin, .023, 8)
    ellipsoid("Cabeça nua do abutre", (.025, -.143, .447),
              (.031, .038, .031), skin, 16, 10, False)
    # Small ridges suggest the folded skin around the throat.
    for index in range(3):
        y = -.072 - index*.014
        tube("Dobra do pescoço %02d" % index,
             [(.004, y, .399+index*.007), (.025, y-.003, .403+index*.007),
              (.047, y, .399+index*.007)], [1, .8, 1], skin, .0025, 5)

    for side in (-1, 1):
        ellipsoid("Íris âmbar", (.025 + side*.025, -.169, .452),
                  (.003, .002, .0032), eye, 10, 6)
        ellipsoid("Pupila negra", (.025 + side*.026, -.171, .452),
                  (.0015, .0011, .0018), beak, 8, 5)
        ellipsoid("Cera do bico", (.025 + side*.005, -.178, .431),
                  (.005, .005, .005), cream, 10, 6)
    # Strong hooked bill points down over the front rim of the nest.
    tube("Bico curvo de queratina", [(.025, -.177, .431), (.025, -.204, .419),
         (.025, -.219, .398), (.025, -.205, .39)], [1, .82, .52, .04],
         beak, .010, 9)

    # Two sturdy scaly legs and curved dark talons grip the twigs.
    for side in (-1, 1):
        x = side*.075
        tube("Perna escamosa %s" % side,
             [(x, .025, .286), (x, .005, .244), (x, -.035, .226)],
             [1, .82, .72], talon, .011, 7)
        for toe in (-1, 0, 1):
            offset = toe*.023
            tube("Garra %s %s" % (side, toe),
                 [(x, -.035, .226), (x+offset*.7, -.071, .216),
                  (x+offset, -.082, .199), (x+offset, -.068, .193)],
                 [1, .82, .55, .05], beak, .006, 7)


def build(seed=73128):
    rng = random.Random(seed)
    stone = [material("Arenito | ocre queimado", (.31, .205, .115), .94, .14),
             material("Arenito | luz", (.43, .30, .18), .95, .12),
             material("Arenito | sombra", (.20, .14, .09), .98, .1)]
    twigs = [material("Galho seco | castanho", (.17, .085, .038), .91, .12),
             material("Galho seco | sol", (.28, .15, .065), .9, .1),
             material("Galho seco | sombra", (.105, .055, .03), .95, .08)]
    straw = material("Palha e capim seco", (.48, .32, .14), .94, .1)
    nest_dark = material("Interior trançado do ninho", (.115, .065, .033), .98, .12)
    eggshell = material("Ovos | marfim manchado", (.68, .53, .32), .38, .06)
    egg_spot = material("Manchas dos ovos", (.31, .19, .105), .72)
    plumage = [material("Plumagem | chocolate", (.17, .087, .044), .9, .12),
               material("Plumagem | castanho quente", (.26, .14, .071), .88, .1),
               material("Plumagem | asa escura", (.105, .057, .034), .91, .1)]
    flight = [material("Rêmiges | carvão castanho", (.075, .045, .031), .91, .07),
              material("Rêmiges | marrom escuro", (.12, .067, .037), .9, .07),
              material("Rêmiges | ponta gasta", (.19, .11, .058), .88, .06)]
    cream = material("Penugem clara do pescoço", (.43, .30, .17), .95, .08)
    skin = material("Pele nua | vermelho terroso", (.19, .082, .066), .72, .12)
    beak = material("Bico e garras | queratina", (.065, .052, .039), .52, .07)
    talon = material("Pernas | cinza arroxeado", (.21, .145, .12), .76, .1)
    eye = material("Olhos | âmbar", (.49, .31, .10), .34)

    angular_ledge(rng, stone)
    for index in range(7):
        angle = math.tau * index / 7
        ellipsoid("Pedra solta no parapeito %02d" % index,
                  (.34*math.cos(angle), .27*math.sin(angle), .068),
                  (.055, .043, .035), stone[index % len(stone)], 12, 8, False)
    build_nest(rng, twigs, straw, nest_dark)
    # Eggs remain in the front of the nest and visible beneath the perched bird.
    build_egg("Ovo do abutre A", (-.105, -.13, .235), eggshell, egg_spot, rng)
    build_egg("Ovo do abutre B", (.005, -.155, .232), eggshell, egg_spot, rng)
    build_vulture(rng, plumage, flight, cream, skin, beak, eye, talon)
    # Loose feathers caught between stones reinforce the dry cliff setting.
    feather("Pena solta junto ao ninho", (.265, -.19, .08),
            (.37, -.235, .075), .022, .006, plumage[1])


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def setup_scene():
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 48
    scene.render.resolution_x = scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (.055, .045, .038, 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = .28
    for name, loc, energy, size, color in (
        ("Sol de fim de tarde", (1.0, -1.35, 1.8), 48, 1.0, (1.0, .76, .52)),
        ("Luz fria do céu", (-1.3, -.5, 1.2), 30, 1.1, (.72, .81, .94)),
        ("Recorte do paredão", (.15, 1.0, 1.35), 38, .8, (1.0, .66, .39)),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        lamp = bpy.context.object
        lamp.name = name
        lamp.data.energy = energy
        lamp.data.shape = "DISK"
        lamp.data.size = size
        lamp.data.color = color
        point_at(lamp, (0, .03, .27))
    bpy.ops.object.camera_add(location=(1.28, -2.25, 1.55))
    camera = bpy.context.object
    camera.name = "Câmera da miniatura"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 1.2
    point_at(camera, (0, .035, .27))
    scene.camera = camera


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
        group[0].name = "Ninho de abutres | " + mat.name


def main():
    clear_scene()
    build()
    merge_by_material()
    setup_scene()
    scene = bpy.context.scene
    scene.render.filepath = str(OUT / (SLUG + "_preview.png"))
    scene.render.film_transparent = False
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / (SLUG + ".blend")))
    bpy.ops.render.render(write_still=True)
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.film_transparent = True
    scene.render.filepath = str(OUT / (SLUG + ".png"))
    bpy.ops.render.render(write_still=True)
    bpy.ops.object.select_all(action="DESELECT")
    meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.export_scene.gltf(filepath=str(OUT / (SLUG + ".glb")),
                              export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True,
                              export_materials="EXPORT")
    print("ASSET_EXPORT", SLUG, "meshes=", len(meshes))


if __name__ == "__main__":
    main()
