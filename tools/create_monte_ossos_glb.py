"""Build the low, floor-mounted bone-pile decoration with Blender."""
from pathlib import Path
from math import sin

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)


def material(name, color, roughness=0.82):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def add_material(obj, mat):
    obj.data.materials.append(mat)
    return obj


def ellipsoid(name, location, scale, mat, segments=16, rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments, ring_count=rings, radius=1, location=location
    )
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for face in obj.data.polygons:
        face.use_smooth = True
    return add_material(obj, mat)


def bone_chip(name, location, scale, mat, seed=0):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1, location=location)
    obj = bpy.context.object
    obj.name = name
    for vertex in obj.data.vertices:
        wobble = 1.0 + 0.11 * sin(vertex.co.x * 17 + vertex.co.y * 31 + vertex.co.z * 23 + seed)
        vertex.co.x *= scale[0] * wobble
        vertex.co.y *= scale[1] * wobble
        vertex.co.z *= scale[2] * wobble
    for face in obj.data.polygons:
        face.use_smooth = True
    return add_material(obj, mat)


def rod(name, start, end, radius, mat, vertices=12):
    a, b = Vector(start), Vector(end)
    delta = b - a
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=radius, depth=delta.length,
        location=(a + b) * 0.5
    )
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = delta.to_track_quat("Z", "Y")
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel = obj.modifiers.new("soft bone ends", "BEVEL")
    bevel.width = radius * 0.42
    bevel.segments = 2
    obj.modifiers.new("weighted normals", "WEIGHTED_NORMAL")
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    bpy.ops.object.modifier_apply(modifier="weighted normals")
    return add_material(obj, mat)


def long_bone(name, start, end, mat, radius=0.021, head=0.037):
    rod(name + " shaft", start, end, radius, mat)
    a, b = Vector(start), Vector(end)
    direction = (b - a).normalized()
    head *= 0.78
    for suffix, point, sign in (("head A", a, -1), ("head B", b, 1)):
        center = point + direction * (head * 0.17 * sign)
        ellipsoid(name + " " + suffix, center, (head, head * 0.80, head * 0.72), mat, 16, 10)


def curved_bone(name, points, mat, radius=0.018):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 12
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for bp, p in zip(spline.bezier_points, points):
        bp.co = p
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    add_material(obj, mat)
    for index, point in enumerate((points[0], points[-1])):
        ellipsoid(name + " end %d" % index, point, (radius * 1.05, radius * 1.05, radius * 0.95), mat, 12, 8)
    return obj


def skull(ivory, pale, worn, socket, teeth):
    # Crânio de perfil, voltado para a direita como na referência do editor.
    before = set(bpy.context.scene.objects)
    # Perfil craniano extrudido e chanfrado: uma única silhueta contínua evita
    # o aspecto de esfera com peças coladas da primeira versão.
    profile = [
        (0.000, 0.092), (0.005, 0.166), (0.025, 0.201), (0.062, 0.221),
        (0.112, 0.224), (0.160, 0.209), (0.196, 0.184), (0.218, 0.158),
        (0.274, 0.143), (0.304, 0.132), (0.293, 0.119), (0.252, 0.111),
        (0.220, 0.099), (0.195, 0.086), (0.147, 0.082), (0.100, 0.089),
        (0.054, 0.094),
    ]
    front_y, back_y = -0.020, 0.075
    vertices = [(x, y, z) for y in (front_y, back_y) for x, z in profile]
    count = len(profile)
    # A face frontal aponta para -Y, em direção à câmera de revisão.
    faces = [tuple(range(count))[::-1], tuple(range(count, count * 2))]
    faces.extend((i, (i + 1) % count, (i + 1) % count + count, i + count) for i in range(count))
    mesh = bpy.data.meshes.new("Skull profile mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(ivory)
    cranium = bpy.data.objects.new("Skull - sculpted profile", mesh)
    bpy.context.collection.objects.link(cranium)
    bevel = cranium.modifiers.new("rounded skull edges", "BEVEL")
    bevel.width = 0.012
    bevel.segments = 3
    bevel.profile = 0.5
    bpy.context.view_layer.objects.active = cranium
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    for face in cranium.data.polygons:
        face.use_smooth = True
    # Escava a órbita na face da malha; a mancha escura fica recuada no fundo.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, radius=1,
                                         location=(0.105, -0.021, 0.163))
    cutter = bpy.context.object
    cutter.name = "temporary eye socket cutter"
    cutter.scale = (0.026, 0.045, 0.021)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.context.view_layer.objects.active = cranium
    boolean = cranium.modifiers.new("carved eye socket", "BOOLEAN")
    boolean.operation = "DIFFERENCE"
    boolean.solver = "EXACT"
    boolean.object = cutter
    bpy.ops.object.modifier_apply(modifier=boolean.name)
    bpy.data.objects.remove(cutter, do_unlink=True)
    ellipsoid("Skull - socket shadow", (0.105, 0.014, 0.163), (0.018, 0.005, 0.014), socket, 16, 10)
    ellipsoid("Skull - cheek", (0.147, -0.027, 0.123), (0.040, 0.009, 0.020), pale, 16, 10)
    ellipsoid("Skull - brow", (0.107, -0.025, 0.188), (0.038, 0.009, 0.009), ivory, 16, 10)
    ellipsoid("Skull - nose cavity", (0.282, -0.022, 0.138), (0.008, 0.005, 0.007), socket, 12, 8)
    for i in range(5):
        x = 0.185 + i * 0.017
        ellipsoid("Skull - tooth %02d" % i, (x, -0.025, 0.105), (0.006, 0.007, 0.009), teeth, 10, 8)
    parts = set(bpy.context.scene.objects) - before
    root = bpy.data.objects.new("Skull assembly", None)
    bpy.context.collection.objects.link(root)
    root.location = (0.105, 0.045, 0.105)
    for obj in parts:
        obj.parent = root
        obj.matrix_parent_inverse = root.matrix_world.inverted()
    root.location.x += 0.015
    root.scale = (0.93, 0.93, 0.93)


def make_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for data in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for item in list(data):
            if item.users == 0:
                data.remove(item)

    ivory = material("aged ivory", (0.64, 0.49, 0.31))
    pale = material("worn bone highlights", (0.80, 0.69, 0.50))
    ochre = material("older bone", (0.48, 0.32, 0.19))
    socket = material("deep recesses", (0.025, 0.016, 0.009))
    teeth = material("old teeth", (0.86, 0.77, 0.59))

    # Costelas arqueadas formam uma ossada baixa; as pontas ficam sobre o piso.
    for i, y in enumerate((-0.125, -0.060, 0.005, 0.070, 0.135)):
        z = 0.060 + (i % 2) * 0.010
        curved_bone("Rib %02d" % i, [
            (0.015, y - 0.145, z), (-0.145, y - 0.130, z + 0.014),
            (-0.315, y - 0.070, z + 0.020), (-0.355, y + 0.005, z + 0.014),
            (-0.285, y + 0.090, z), (-0.105, y + 0.145, z - 0.004),
        ], pale if i % 2 == 0 else ivory, radius=0.018)

    # Pequenas vértebras dão leitura de esqueleto por baixo dos ossos cruzados.
    for i in range(6):
        y = -0.155 + i * 0.060
        ellipsoid("Vertebra %02d" % i, (0.055, y, 0.088 + (i % 2) * 0.008),
                  (0.043, 0.031, 0.028), pale if i % 2 else ochre, 16, 10)

    long_bone("Cross bone A", (-0.365, -0.205, 0.067), (0.255, 0.055, 0.120), pale, 0.024, 0.040)
    long_bone("Cross bone B", (-0.325, 0.190, 0.073), (0.225, -0.155, 0.125), ivory, 0.022, 0.039)
    long_bone("Front femur", (-0.315, -0.185, 0.104), (0.115, -0.085, 0.137), ochre, 0.024, 0.043)

    # Fêmures menores e fragmentos preenchem a silhueta semelhante à referência.
    long_bone("Rear fragment", (-0.330, 0.170, 0.098), (-0.115, 0.205, 0.125), pale, 0.020, 0.039)
    long_bone("Short fragment", (-0.030, 0.170, 0.080), (0.145, 0.140, 0.110), ochre, 0.019, 0.034)
    long_bone("Skull support bone", (-0.100, -0.055, 0.067), (0.175, -0.045, 0.095), pale, 0.022, 0.036)
    curved_bone("Loose curved rib", [(-0.255, -0.195, 0.055), (-0.180, -0.245, 0.061),
                                    (-0.080, -0.235, 0.065), (-0.015, -0.185, 0.070)], ivory, .013)

    # Fragmentos curtos sob a ossada unem visualmente a pilha e mantêm o perfil baixo.
    chips = [
        ((-0.275, -0.180, 0.025), (0.055, 0.035, 0.020), ochre),
        ((-0.245, 0.165, 0.024), (0.052, 0.038, 0.018), pale),
        ((-0.080, -0.205, 0.022), (0.060, 0.032, 0.017), ivory),
        ((-0.045, 0.205, 0.024), (0.052, 0.036, 0.020), ochre),
        ((0.155, -0.145, 0.024), (0.048, 0.033, 0.018), pale),
        ((0.200, 0.135, 0.027), (0.050, 0.035, 0.019), ivory),
    ]
    for i, (location, scale, mat) in enumerate(chips):
        bone_chip("Bone debris %02d" % i, location, scale, mat, i * 3)

    # Crânio no lado direito, com órbitas escuras orientadas para a câmera de jogo.
    skull(ivory, pale, ochre, socket, teeth)

    # Render de revisão em ângulo alto, com fundo transparente e sombras de contato.
    bpy.ops.object.camera_add(location=(1.45, -2.15, 3.0))
    camera = bpy.context.object
    camera.name = "Preview Camera"
    target = Vector((0.0, 0.0, 0.10))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 0.92
    bpy.context.scene.camera = camera

    bpy.ops.object.light_add(type="AREA", location=(-1.0, -1.5, 2.4))
    key = bpy.context.object
    key.name = "Soft key"
    key.data.energy = 64
    key.data.shape = "DISK"
    key.data.size = 2.5
    key.rotation_euler = (Vector((0, 0, 0.08)) - key.location).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.object.light_add(type="AREA", location=(1.4, 0.8, 1.6))
    fill = bpy.context.object
    fill.name = "Warm fill"
    fill.data.energy = 18
    fill.data.color = (1.0, 0.78, 0.52)
    fill.data.size = 1.8
    fill.rotation_euler = (Vector((0, 0, 0.10)) - fill.location).to_track_quat("-Z", "Y").to_euler()

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    scene.render.filepath = str(OUT / "monte_ossos_preview.png")
    scene.world.color = (0.12, 0.12, 0.12)
    scene.view_settings.view_transform = "AgX"
    scene.render.resolution_percentage = 100
    scene.camera.data.lens = 50
    scene.render.image_settings.color_depth = "8"
    scene.render.filepath = str(OUT / "monte_ossos_preview.png")

    # Keep the editable Blender source complete; export only the bone meshes.
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "monte_ossos.blend"))
    bpy.ops.render.render(write_still=True)
    bpy.ops.object.select_all(action="DESELECT")
    meshes = [o for o in scene.objects if o.type == "MESH"]
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.export_scene.gltf(
        filepath=str(OUT / "monte_ossos.glb"),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_animations=False,
    )
if __name__ == "__main__":
    make_scene()
