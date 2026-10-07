"""Gera a miniatura de um altar de sacrifício em uma clareira antiga."""
from __future__ import annotations

import math
import random
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)
SLUG = "pedra_sacrificio"


def material(name, color, roughness=.9, bump=.06):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    if bump:
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 38
        noise.inputs["Detail"].default_value = 3
        relief = nodes.new("ShaderNodeBump")
        relief.inputs["Strength"].default_value = bump
        relief.inputs["Distance"].default_value = .012
        links.new(noise.outputs["Fac"], relief.inputs["Height"])
        links.new(relief.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def ellipsoid(name, pos, scale, mat, rng, segments=16, rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                         radius=1, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for vertex in obj.data.vertices:
        factor = rng.uniform(.94, 1.06)
        vertex.co *= factor
    obj.data.materials.append(mat)
    for face in obj.data.polygons:
        face.use_smooth = False
    return obj


def stone_slab(name, center, half_x, half_y, z0, z1, mat, rng):
    """Low-poly chipped stone slab with a slightly uneven top surface."""
    count = 9
    outline = []
    for index in range(count):
        angle = math.tau * index / count
        wobble = rng.uniform(.88, 1.10)
        outline.append((center[0] + math.cos(angle) * half_x * wobble,
                        center[1] + math.sin(angle) * half_y * wobble))
    verts = []
    for x, y in outline:
        verts.append((x, y, z0 + rng.uniform(-.012, .012)))
    for x, y in outline:
        verts.append((x, y, z1 + rng.uniform(-.018, .018)))
    faces = [tuple(reversed(range(count))), tuple(range(count, count * 2))]
    faces.extend((index, (index + 1) % count,
                  (index + 1) % count + count, index + count)
                 for index in range(count))
    mesh = bpy.data.meshes.new(name + " mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for poly in mesh.polygons:
        poly.use_smooth = False
    bevel = obj.modifiers.new("Quinas gastas", "BEVEL")
    bevel.width = .012
    bevel.segments = 2
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    return obj


def tube(name, points, mat, radius=.004, resolution=5):
    curve = bpy.data.curves.new(name + " curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = resolution
    curve.bevel_depth = radius
    curve.bevel_resolution = 2
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, co in zip(spline.bezier_points, points):
        point.co = co
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    return bpy.context.object


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
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (.035, .045, .036, 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = .3
    for name, loc, energy, size, color in (
        ("Luz dourada filtrada pela copa", (1.0, -1.5, 1.8), 47, 1.0, (1.0, .79, .57)),
        ("Luz fria da clareira", (-1.3, -.4, 1.2), 32, 1.1, (.68, .82, .73)),
        ("Recorte entre as árvores", (.1, 1.0, 1.5), 37, .85, (1.0, .68, .43)),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        lamp = bpy.context.object
        lamp.name = name
        lamp.data.energy = energy
        lamp.data.shape = "DISK"
        lamp.data.size = size
        lamp.data.color = color
        lamp.rotation_euler = (Vector((0, 0, .22)) - lamp.location).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.object.camera_add(location=(1.45, -2.6, 1.7))
    camera = bpy.context.object
    camera.name = "Câmera da miniatura"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 1.24
    camera.rotation_euler = (Vector((0, 0, .22)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera


def build(seed=91824):
    rng = random.Random(seed)
    soil = material("Terra úmida da clareira", (.20, .15, .10), .98, .12)
    soil_light = material("Terra e folhas secas", (.31, .22, .13), .96, .09)
    stone = [material("Granito antigo %02d" % i, color, .94, .13)
             for i, color in enumerate(((.30, .30, .27), (.39, .38, .33),
                                        (.24, .25, .23), (.34, .32, .28)))]
    moss = [material("Musgo escuro", (.12, .19, .095), .98, .08),
            material("Musgo iluminado", (.22, .28, .13), .97, .08)]
    leaf = [material("Folhas caídas %02d" % i, color, .9, .04)
            for i, color in enumerate(((.29, .22, .10), (.38, .29, .12),
                                       (.22, .24, .12), (.44, .32, .15)))]
    rune = material("Ranhuras rituais", (.13, .105, .085), .98, .02)
    wax = material("Cera velha", (.36, .29, .20), .83, .03)
    stain = material("Pigmento ritual oxidado", (.25, .095, .065), .91, .03)

    # Irregular patch of open earth separates the altar from the surrounding forest.
    ellipsoid("Clareira de terra exposta", (0, 0, .035),
              (.465, .445, .052), soil, rng, 24, 10)
    for index in range(7):
        angle = math.tau * index / 7
        ellipsoid("Borda de pedra musgosa %02d" % index,
                  (.38 * math.cos(angle), .35 * math.sin(angle), .055),
                  (rng.uniform(.07, .12), rng.uniform(.06, .10), .045),
                  stone[index % len(stone)], rng, 12, 8)

    # A broad altar table on a single worn pedestal, with chipped edges and old runes.
    stone_slab("Pedestal talhado", (0, .025), .19, .18,
               .07, .25, stone[2], rng)
    stone_slab("Tampo da pedra de sacrifício", (0, -.005), .315, .235,
               .245, .355, stone[1], rng)
    # Dark, shallow engraved sigils remain visible on the top face.
    for side in (-1, 1):
        tube("Runa lateral %s" % side,
             [(side*.205, -.105, .361), (side*.235, -.035, .36),
              (side*.205, .035, .362)], rune, .004)
        tube("Runa transversal %s" % side,
             [(side*.16, -.135, .36), (side*.105, -.11, .362)], rune, .003)
    tube("Marca ritual central", [(-.065, .02, .361), (0, .065, .363),
         (.065, .02, .361), (0, -.045, .362), (-.065, .02, .361)],
         stain, .006)
    # A faint oxidized trace, not an active effect or loot marker.
    ellipsoid("Pigmento gasto no altar", (0, -.005, .358),
              (.045, .024, .004), stain, rng, 12, 6)

    # Small spent offerings: wax stubs and fallen leaves around the clearing.
    for index, pos in enumerate(((-.27, -.19), (.27, -.17), (.29, .18))):
        height = rng.uniform(.045, .065)
        bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=.022,
                                            depth=height, location=(pos[0], pos[1], .065 + height/2))
        candle = bpy.context.object
        candle.name = "Vela apagada %02d" % index
        candle.data.materials.append(wax)
        for face in candle.data.polygons:
            face.use_smooth = False
    for index in range(28):
        angle = rng.uniform(0, math.tau)
        radius = rng.uniform(.28, .45)
        x, y = math.cos(angle) * radius, math.sin(angle) * radius
        leaf_obj = ellipsoid("Folha caída %02d" % index, (x, y, .078),
                             (rng.uniform(.018, .04), rng.uniform(.009, .02), .0035),
                             rng.choice(leaf), rng, 8, 5)
        leaf_obj.rotation_euler[2] = angle + rng.uniform(-.8, .8)
    for index in range(9):
        angle = rng.uniform(0, math.tau)
        radius = rng.uniform(.32, .44)
        x, y = math.cos(angle) * radius, math.sin(angle) * radius
        ellipsoid("Mancha de musgo %02d" % index, (x, y, .09),
                  (rng.uniform(.025, .055), rng.uniform(.018, .04), .008),
                  rng.choice(moss), rng, 10, 6)


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                       bpy.data.cameras, bpy.data.lights):
        for data in collection:
            if data.users == 0:
                collection.remove(data)
    build()
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
