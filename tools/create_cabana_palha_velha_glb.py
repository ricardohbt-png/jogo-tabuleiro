"""Gera a miniatura 3D da cabana de palha velha."""
from pathlib import Path
import math

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)
SLUG = "cabana_palha_velha"


def mat(name, color, roughness=0.92):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    return material


def box(name, pos, size, material, bevel=0.012, rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    if rot:
        obj.rotation_euler = rot
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    if bevel:
        mod = obj.modifiers.new("Arestas arredondadas", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def beam(name, a, b, radius, material, vertices=8):
    a, b = Vector(a), Vector(b)
    delta = b - a
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=radius, depth=delta.length,
        location=(a + b) / 2,
    )
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(material)
    return obj


def mesh_obj(name, vertices, faces, material):
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for data in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                 bpy.data.cameras, bpy.data.lights):
        for block in list(data):
            if block.users == 0:
                data.remove(block)


def build():
    timber = [mat("Madeira velha %d" % i, color) for i, color in enumerate((
        (0.16, 0.13, 0.09), (0.25, 0.20, 0.13), (0.34, 0.27, 0.17),
    ))]
    reed = [mat("Palha trançada da parede %d" % i, color) for i, color in enumerate((
        (0.25, 0.21, 0.14), (0.32, 0.27, 0.17), (0.19, 0.17, 0.12),
    ))]
    thatch = [mat("Palha ressecada %d" % i, color) for i, color in enumerate((
        (0.13, 0.12, 0.085), (0.20, 0.18, 0.12),
        (0.29, 0.24, 0.15), (0.08, 0.075, 0.05),
    ))]
    rope = mat("Corda antiga", (0.38, 0.29, 0.16))
    repair = mat("Remendos de madeira", (0.37, 0.25, 0.13))
    dark = mat("Interior escuro", (0.025, 0.020, 0.015))
    clay = mat("Pigmento antigo", (0.35, 0.17, 0.07))

    # Base baixa e redonda, com uma parede de trama circular em torno do interior.
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.98, depth=0.16,
                                        location=(0, 0, 0.08))
    bpy.context.object.name = "Base circular de madeira"
    bpy.context.object.data.materials.append(timber[0])

    segments = 32
    outer_radius, inner_radius = 1.02, 0.91
    wall_bottom, wall_top = 0.16, 1.58
    verts = []
    for radius, z in ((outer_radius, wall_bottom), (outer_radius, wall_top),
                      (inner_radius, wall_bottom), (inner_radius, wall_top)):
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            verts.append((radius * math.cos(angle), radius * math.sin(angle), z))
    faces = []
    for i in range(segments):
        j = (i + 1) % segments
        faces.extend((
            (i, j, segments + j, segments + i),
            (2 * segments + j, 2 * segments + i,
             3 * segments + i, 3 * segments + j),
            (segments + i, segments + j, 3 * segments + j, 3 * segments + i),
            (j, i, 2 * segments + i, 2 * segments + j),
        ))
    mesh_obj("Parede circular de palha", verts, faces, reed[0])

    # Esteios verticais e amarras em anéis dão à palha sua trama artesanal.
    for i in range(20):
        angle = 2 * math.pi * i / 20
        x, y = outer_radius * math.cos(angle), outer_radius * math.sin(angle)
        beam("Esteio da parede redonda", (x, y, wall_bottom), (x, y, wall_top),
             0.027, timber[i % len(timber)], 6)
    for z in (0.42, 0.76, 1.10, 1.44):
        radius = outer_radius + 0.018
        for i in range(32):
            a0, a1 = 2 * math.pi * i / 32, 2 * math.pi * (i + 1) / 32
            beam("Amarra circular de fibra",
                 (radius * math.cos(a0), radius * math.sin(a0), z),
                 (radius * math.cos(a1), radius * math.sin(a1), z),
                 0.014, rope, 5)

    # Entrada em arco, escura, com moldura torta e tábuas de reparo.
    door_y = -1.055
    door_points = [(-0.31, door_y, 0.18), (0.31, door_y, 0.18),
                   (0.31, door_y, 0.93)]
    for i in range(1, 13):
        angle = math.pi * i / 12
        door_points.append((0.31 * math.cos(angle), door_y,
                            0.93 + 0.31 * math.sin(angle)))
    mesh_obj("Entrada em arco", door_points,
             [tuple(range(len(door_points)))], dark)
    for x in (-0.34, 0.34):
        beam("Montante torto da porta", (x, -1.02, 0.18), (x * 0.97, -1.02, 0.94),
             0.045, timber[0], 7)
    for i in range(8):
        a0, a1 = math.pi * i / 8, math.pi * (i + 1) / 8
        beam("Arco de madeira da porta",
             (0.34 * math.cos(a0), -1.02, 0.94 + 0.34 * math.sin(a0)),
             (0.34 * math.cos(a1), -1.02, 0.94 + 0.34 * math.sin(a1)),
             0.042, timber[0], 7)
    box("Tábua de reparo na frente", (-0.70, -0.72, 0.77),
        (0.16, 0.035, 0.48), repair, 0.008, rot=(0.0, 0.08, -0.10))
    beam("Escora antiga", (0.76, -0.70, 0.26), (0.89, -0.49, 1.40),
         0.038, repair, 6)
    mesh_obj("Símbolo antigo sobre a porta", [
        (-0.15, -1.04, 1.54), (0.0, -1.06, 1.70),
        (0.15, -1.04, 1.54), (0.0, -1.06, 1.39),
    ], [(0, 1, 2, 3)], clay)

    # Telhado cônico espesso de palha, com beiral irregular e fibras radiais.
    roof_radius, eave_z, peak_z = 1.36, 1.55, 3.18
    roof_segments = 32
    verts = []
    for radius, z in ((roof_radius, eave_z), (0.035, peak_z),
                      (roof_radius - 0.12, eave_z - 0.07), (0.02, peak_z - 0.12)):
        for i in range(roof_segments):
            angle = 2 * math.pi * i / roof_segments
            verts.append((radius * math.cos(angle), radius * math.sin(angle), z))
    faces = []
    for i in range(roof_segments):
        j = (i + 1) % roof_segments
        faces.extend(((roof_segments + i, i, j),
                      (3 * roof_segments + j, 2 * roof_segments + j,
                       2 * roof_segments + i, 3 * roof_segments + i),
                      (i, 2 * roof_segments + i, 2 * roof_segments + j, j)))
    mesh_obj("Telhado conico de palha", verts, faces, thatch[0])

    for i in range(32):
        angle = 2 * math.pi * i / 32
        wobble = ((i % 3) - 1) * 0.018
        end_radius = roof_radius + wobble
        beam("Feixe comprido do telhado",
             (0.03 * math.cos(angle), 0.03 * math.sin(angle), peak_z - 0.04),
             (end_radius * math.cos(angle), end_radius * math.sin(angle), eave_z + 0.015),
             0.024 + (i % 2) * 0.007, thatch[i % len(thatch)], 6)

    for radius in (0.40, 0.72, 1.02, 1.25):
        z = peak_z - ((radius - 0.035) / (roof_radius - 0.035)) * (peak_z - eave_z)
        for i in range(32):
            a0, a1 = 2 * math.pi * i / 32, 2 * math.pi * (i + 1) / 32
            beam("Trama circular do telhado",
                 (radius * math.cos(a0), radius * math.sin(a0), z),
                 (radius * math.cos(a1), radius * math.sin(a1), z),
                 0.012, rope if radius == 1.02 else thatch[1], 5)

    # Palha pendente em comprimentos diferentes e duas áreas remendadas.
    for i in range(28):
        angle = 2 * math.pi * i / 28
        drop = 0.08 + (i % 4) * 0.025
        radius = roof_radius + 0.015
        beam("Franja gasta de palha",
             (radius * math.cos(angle), radius * math.sin(angle), eave_z + 0.04),
             ((radius + 0.035) * math.cos(angle),
              (radius + 0.035) * math.sin(angle), eave_z - drop),
             0.021, thatch[(i + 1) % len(thatch)], 5)
    for angle in (0.35, 2.55, 4.25):
        radius = 0.83
        z = peak_z - ((radius - 0.035) / (roof_radius - 0.035)) * (peak_z - eave_z)
        beam("Feixe substituído no telhado",
             (radius * math.cos(angle), radius * math.sin(angle), z + 0.045),
             ((radius + 0.27) * math.cos(angle),
              (radius + 0.27) * math.sin(angle), z - 0.29),
             0.035, repair, 6)


def merge_by_material():
    for material in list(bpy.data.materials):
        group = [obj for obj in bpy.context.scene.objects
                 if obj.type == "MESH" and material in obj.data.materials[:]
                 and obj.name not in ("Parede circular de palha", "Telhado conico de palha")]
        if len(group) < 2:
            continue
        bpy.ops.object.select_all(action="DESELECT")
        for obj in group:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = group[0]
        bpy.ops.object.join()
        group[0].name = "Cabana de palha velha | " + material.name


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
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.10, 0.085, 0.065, 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35
    for name, loc, energy, size, color in (
        ("Luz quente da margem", (3.2, -4.0, 5.6), 430, 3.4, (1.0, 0.78, 0.54)),
        ("Preenchimento frio", (-3.4, -0.5, 3.6), 270, 3.0, (0.68, 0.82, 1.0)),
        ("Recorte dourado", (0.2, 3.4, 4.8), 360, 2.8, (1.0, 0.69, 0.39)),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        lamp = bpy.context.object
        lamp.name = name
        lamp.data.energy = energy
        lamp.data.shape = "DISK"
        lamp.data.size = size
        lamp.data.color = color
        point_at(lamp, (0, -0.05, 1.65))
    bpy.ops.object.camera_add(location=(4.4, -6.4, 4.6))
    camera = bpy.context.object
    camera.name = "Câmera da cabana envelhecida"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 4.25
    point_at(camera, (0, -0.05, 1.70))
    scene.camera = camera
    scene.render.filepath = str(OUT / (SLUG + ".png"))


def export_asset():
    clear_scene()
    build()
    merge_by_material()
    setup_scene()
    scene = bpy.context.scene
    meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / (SLUG + ".blend")))
    scene.render.resolution_x = scene.render.resolution_y = 1024
    bpy.ops.render.render(write_still=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT / (SLUG + ".glb")),
                              export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True,
                              export_materials="EXPORT")
    print("ASSET_EXPORT", SLUG, "meshes=", len(meshes))


if __name__ == "__main__":
    export_asset()
