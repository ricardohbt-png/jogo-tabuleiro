"""Gera uma miniatura de arco rochoso natural para mapas áridos."""
from __future__ import annotations

import math
import random
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)
SLUG = "arco_pedra_deserto"


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                       bpy.data.cameras, bpy.data.lights):
        for data in collection:
            if data.users == 0:
                collection.remove(data)


def material(name, color, roughness=.93, bump=.08):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    if bump:
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 34
        noise.inputs["Detail"].default_value = 3
        relief = nodes.new("ShaderNodeBump")
        relief.inputs["Strength"].default_value = bump
        relief.inputs["Distance"].default_value = .016
        links.new(noise.outputs["Fac"], relief.inputs["Height"])
        links.new(relief.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def ico_rock(name, pos, scale, mat, rng, subdivisions=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=1,
                                          location=pos)
    obj = bpy.context.object
    obj.name = name
    for vert in obj.data.vertices:
        factor = rng.uniform(.88, 1.12)
        vert.co.x *= scale[0] * factor
        vert.co.y *= scale[1] * factor
        vert.co.z *= scale[2] * factor
    obj.data.materials.append(mat)
    for face in obj.data.polygons:
        face.use_smooth = False
    return obj


def arch_wedge(name, a0, a1, spring, inner, outer, depth, mat, rng):
    """Extrude one irregular voussoir section around the natural arch."""
    center = (a0 + a1) * .5
    outer_x, outer_z = outer
    inner_x, inner_z = inner
    jitter = rng.uniform(-.012, .012)
    points = [
        (inner_x * math.cos(a0), spring + inner_z * math.sin(a0)),
        (outer_x * math.cos(a0 + jitter), spring + outer_z * math.sin(a0 + jitter)),
        (outer_x * math.cos(a1 + jitter), spring + outer_z * math.sin(a1 + jitter)),
        (inner_x * math.cos(a1), spring + inner_z * math.sin(a1)),
    ]
    front = -depth * rng.uniform(.92, 1.08)
    back = depth * rng.uniform(.84, 1.08)
    verts = [(x, y, z) for y in (front, back) for x, z in points]
    faces = [(3, 2, 1, 0), (4, 5, 6, 7),
             (0, 1, 5, 4), (1, 2, 6, 5),
             (2, 3, 7, 6), (3, 0, 4, 7)]
    mesh = bpy.data.meshes.new(name + " mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bevel = obj.modifiers.new("Arestas gastas pela areia", "BEVEL")
    bevel.width = .012
    bevel.segments = 2
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    return obj


def stratum(name, points, mat, radius=.004):
    curve = bpy.data.curves.new(name + " curve", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = radius
    curve.bevel_resolution = 2
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for bp, point in zip(spline.bezier_points, points):
        bp.co = point
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
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (.06, .047, .034, 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = .3
    for name, loc, energy, size, color in (
        ("Sol dourado", (1.2, -1.8, 2.1), 55, 1.1, (1.0, .78, .55)),
        ("Luz difusa do céu", (-1.6, -.7, 1.5), 34, 1.2, (.72, .82, 1.0)),
        ("Recorte quente", (.4, 1.5, 1.8), 42, .9, (1.0, .67, .38)),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        lamp = bpy.context.object
        lamp.name = name
        lamp.data.energy = energy
        lamp.data.shape = "DISK"
        lamp.data.size = size
        lamp.data.color = color
        lamp.rotation_euler = (Vector((0, 0, .48)) - lamp.location).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.object.camera_add(location=(1.65, -3.4, 2.15))
    camera = bpy.context.object
    camera.name = "Câmera da miniatura"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 1.58
    camera.rotation_euler = (Vector((0, 0, .49)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera


def build(seed=53021):
    rng = random.Random(seed)
    sandstone = [
        material("Arenito queimado", (.48, .285, .145), .96, .12),
        material("Arenito claro", (.59, .385, .22), .95, .10),
        material("Arenito sombra", (.35, .205, .105), .98, .12),
        material("Camada mineral", (.43, .245, .13), .97, .13),
    ]
    shadow = material("Fissuras de erosão", (.22, .125, .065), .99, .04)
    grit = [material("Cascalho", (.37, .235, .135)),
            material("Cascalho claro", (.55, .36, .21))]

    # Two weathered feet anchor the arch and leave a broad, clear opening.
    for side, label in ((-1, "esquerdo"), (1, "direito")):
        for row in range(3):
            z = .095 + row * .145
            width = rng.uniform(.19, .235) if row < 2 else rng.uniform(.175, .205)
            x = side * (.405 + rng.uniform(-.012, .012))
            ico_rock("Pilar de arenito %s %02d" % (label, row),
                     (x, rng.uniform(-.015, .015), z),
                     (width, .235 + rng.uniform(-.02, .025), .17),
                     rng.choice(sandstone), rng, 2)
        # Long shallow layers on the face reveal sedimentary bands.
        for band in range(3):
            z = .16 + band * .17
            x = side * .405
            stratum("Veio sedimentar %s %02d" % (label, band),
                    [(x-side*.085, -.132, z), (x, -.146, z + .009),
                     (x+side*.075, -.13, z + .004)],
                    sandstone[(band + 1) % len(sandstone)], .0035)

    # A curved, naturally eroded ring built from irregular sandstone masses.
    spring = .495
    inner = (.295, .30)
    outer = (.505, .515)
    count = 13
    for index in range(count):
        a0 = index * math.pi / count + .006
        a1 = (index + 1) * math.pi / count - .006
        arch_wedge("Bloco erodido do arco %02d" % index,
                   a0, a1, spring,
                   (inner[0] + rng.uniform(-.008, .008), inner[1] + rng.uniform(-.008, .008)),
                   (outer[0] + rng.uniform(-.018, .018), outer[1] + rng.uniform(-.016, .016)),
                   rng.uniform(.17, .22), rng.choice(sandstone), rng)

    # A few broken ledges, chipped corners and gravel make it feel rooted in a cliff.
    for side in (-1, 1):
        ico_rock("Ombro de rocha quebrada", (side*.49, .005, .38),
                 (.13, .22, .16), rng.choice(sandstone), rng, 1)
        ico_rock("Pedra caída na base", (side*.48, -.045, .095),
                 (.18, .19, .10), rng.choice(grit), rng, 1)
    for index in range(11):
        x = rng.uniform(-.56, .56)
        y = rng.uniform(-.22, .22)
        ico_rock("Cascalho ao pé do arco %02d" % index,
                 (x, y, rng.uniform(.035, .07)),
                 (rng.uniform(.018, .055), rng.uniform(.02, .05), rng.uniform(.012, .03)),
                 rng.choice(grit), rng, 1)

    # Fine cracks emphasize age without turning the arch into masonry.
    for side in (-1, 1):
        stratum("Fissura na pedra %s" % side,
                [(side*.47, -.222, .69), (side*.445, -.225, .64),
                 (side*.455, -.223, .60)], shadow, .003)


def main():
    clear_scene()
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
