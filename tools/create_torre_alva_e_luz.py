"""Cria a miniatura da torre cilíndrica de Alva e Luz."""
from pathlib import Path
import math
import random

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)


def material(name, color, roughness=0.9, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def assign(obj, mat):
    obj.data.materials.append(mat)
    return obj


def cube(name, loc, dims, mat, bevel=0.0, rotation_z=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.rotation_euler[2] = rotation_z
    assign(obj, mat)
    if bevel:
        mod = obj.modifiers.new("Quinas talhadas pelo tempo", "BEVEL")
        mod.width = bevel
        mod.segments = 1
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        mod = obj.modifiers.new("Normais ponderadas", "WEIGHTED_NORMAL")
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def cylinder(name, loc, radius, depth, mat, vertices=16, radius_top=None):
    if radius_top is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                            depth=depth, location=loc)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius,
                                        radius2=radius_top, depth=depth,
                                        location=loc)
    obj = bpy.context.object
    obj.name = name
    assign(obj, mat)
    bevel = obj.modifiers.new("Aresta de pedra gasta", "BEVEL")
    bevel.width = 0.018
    bevel.segments = 1
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    return obj


def rod(name, start, end, radius, mat, vertices=8):
    a, b = Vector(start), Vector(end)
    delta = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                        depth=delta.length, location=(a + b) / 2)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = delta.to_track_quat("Z", "Y")
    assign(obj, mat)
    return obj


def tower_shell(name, outer_mat, inner_mat, n=16):
    """Tapered hollow shaft with a visible annular parapet and open crown."""
    rings = [
        (0.22, 0.84),
        (4.45, 0.75),
        (4.45, 0.49),
        (3.94, 0.50),
    ]
    verts = []
    for z, radius in rings:
        for i in range(n):
            a = math.tau * i / n
            verts.append((math.cos(a) * radius, math.sin(a) * radius, z))
    faces, mids = [], []
    for ring_idx in (0, 2):
        start = ring_idx * n
        next_start = (ring_idx + 1) * n
        for i in range(n):
            j = (i + 1) % n
            faces.append((start + i, start + j, next_start + j, next_start + i))
            mids.append(0 if ring_idx == 0 else 1)
    # Annular top thickness between the outer tower wall and the inside.
    for i in range(n):
        j = (i + 1) % n
        faces.append((n + i, n + j, 2 * n + j, 2 * n + i))
        mids.append(0)
    mesh = bpy.data.meshes.new(name + " malha")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(outer_mat)
    mesh.materials.append(inner_mat)
    for poly, material_index in zip(mesh.polygons, mids):
        poly.material_index = material_index
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def join_objects(objects, name):
    objects = [obj for obj in objects if obj and obj.name in bpy.data.objects]
    if len(objects) < 2:
        return objects[0] if objects else None
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    joined = bpy.context.object
    joined.name = name
    return joined


def make_tower():
    stone_base = material("Calcário enegrecido", (0.095, 0.095, 0.088))
    stone_top = material("Pedra gasta no coroamento", (0.15, 0.145, 0.13))
    stone_variants = [
        material("Blocos | carvão", (0.055, 0.06, 0.06)),
        material("Blocos | cinza ardósia", (0.08, 0.085, 0.085)),
        material("Blocos | cinza gasto", (0.12, 0.12, 0.11)),
        material("Blocos | pedra clara", (0.17, 0.16, 0.14)),
    ]
    interior = material("Interior escuro do topo", (0.008, 0.01, 0.01))
    slit_dark = material("Frestas de vigia", (0.012, 0.015, 0.015))
    iron = material("Ferro antigo", (0.16, 0.16, 0.15), 0.48, 0.48)

    # Diâmetro total abaixo de 2 casas; eixo alto e maciço como a torre da arte.
    cylinder("Base circular de alvenaria", (0, 0, 0.14), 0.96, 0.28,
             stone_base, 16, radius_top=0.88)
    tower_shell("Fuste cilíndrico oco", stone_base, interior)
    cylinder("Piso escuro no interior", (0, 0, 3.96), 0.49, 0.035,
             interior, 16)

    # Fiadas alternadas de silhares, com variação de tom e juntas visíveis.
    rng = random.Random(17)
    blocks = []
    for row in range(17):
        z = 0.40 + row * 0.235 + rng.uniform(-0.012, 0.012)
        radius = 0.835 - (z / 4.45) * 0.085
        phase = (row % 2) * math.pi / 16
        for i in range(16):
            a = math.tau * i / 16 + phase + rng.uniform(-0.009, 0.009)
            tangent = a + math.pi / 2
            tangential_len = rng.uniform(0.25, 0.30)
            radial_depth = rng.uniform(0.09, 0.14)
            height = rng.uniform(0.18, 0.22)
            obj = cube("Bloco de silhar", (math.cos(a) * radius,
                                            math.sin(a) * radius, z),
                       (tangential_len, radial_depth, height),
                       rng.choices(stone_variants, weights=(5, 5, 3, 1))[0],
                       0.012, tangent)
            blocks.append(obj)
    join_objects(blocks, "Alvenaria irregular | peça única")

    # Frestas estreitas para vigia em faces alternadas da torre.
    for idx, (angle, z) in enumerate(((math.radians(-55), 2.05),
                                      (math.radians(35), 3.02),
                                      (math.radians(145), 2.52),
                                      (math.radians(235), 3.60))):
        radius = 0.80 - (z / 4.45) * 0.07
        x, y = math.cos(angle) * radius, math.sin(angle) * radius
        cube("Fresta vertical de vigia %d" % idx, (x, y, z),
             (0.095, 0.035, 0.39), slit_dark, 0.012, angle + math.pi / 2)
        for offset in (-0.075, 0.075):
            xx, yy = x + math.cos(angle + math.pi / 2) * offset, y + math.sin(angle + math.pi / 2) * offset
            cube("Borda de pedra da fresta", (xx, yy, z),
                 (0.025, 0.045, 0.43), stone_top, 0.008, angle + math.pi / 2)

    # Coroa com parapeito baixo, ameias grossas e abertura central sem cobertura.
    n = 16
    verts = []
    for z, radius in ((4.42, 0.79), (4.82, 0.79), (4.42, 0.49), (4.82, 0.49)):
        for i in range(n):
            a = math.tau * i / n
            verts.append((math.cos(a) * radius, math.sin(a) * radius, z))
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.extend([
            (i, j, n + j, n + i),
            (2 * n + j, 2 * n + i, 3 * n + i, 3 * n + j),
            (n + i, n + j, 3 * n + j, 3 * n + i),
        ])
    parapet_mesh = bpy.data.meshes.new("Parapeito oco malha")
    parapet_mesh.from_pydata(verts, [], faces)
    parapet_mesh.materials.append(stone_top)
    parapet = bpy.data.objects.new("Parapeito circular aberto", parapet_mesh)
    bpy.context.collection.objects.link(parapet)
    for i in range(12):
        a = math.tau * i / 12
        radius = 0.655
        cube("Ameia de pedra", (math.cos(a) * radius, math.sin(a) * radius, 5.00),
             (0.34, 0.30, 0.42), stone_top, 0.025, a + math.pi / 2)

    # Pequenos ressaltos de pedra sob o parapeito, como consolas defensivas.
    for i in range(12):
        a = math.tau * i / 12
        cube("Consolo do coroamento", (math.cos(a) * 0.79, math.sin(a) * 0.79, 4.38),
             (0.25, 0.20, 0.15), stone_top, 0.018, a + math.pi / 2)

    # Aro de ferro discreto dentro do poço superior.
    bpy.ops.mesh.primitive_torus_add(major_segments=16, minor_segments=6,
                                     location=(0, 0, 4.32), major_radius=0.48,
                                     minor_radius=0.018)
    rim = bpy.context.object
    rim.name = "Aro de ferro interno"
    assign(rim, iron)


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    make_tower()
    target = (0, 0, 2.45)
    bpy.ops.object.camera_add(location=(5.8, -8.0, 7.3))
    camera = bpy.context.object
    camera.name = "Câmera | miniatura isométrica"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 6.15
    point_at(camera, target)
    scene = bpy.context.scene
    scene.camera = camera
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 1024
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.07, 0.07, 0.065, 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.22
    lights = [
        ("Luz principal", (4.2, -5.5, 8.5), 650, 4.5, (1.0, 0.86, 0.70)),
        ("Preenchimento", (-4.5, -1.0, 5.0), 400, 4.0, (0.75, 0.84, 1.0)),
        ("Recorte", (0.0, 4.5, 7.0), 450, 4.0, (1.0, 0.74, 0.52)),
    ]
    for name, location, power, size, color in lights:
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.name = name
        light.data.energy = power
        light.data.shape = "DISK"
        light.data.size = size
        light.data.color = color
        point_at(light, target)

    meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "torre_alva_e_luz.blend"))
    scene.render.filepath = str(OUT / "torre_alva_e_luz_preview.png")
    bpy.ops.render.render(write_still=True)
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.filepath = str(OUT / "torre_alva_e_luz.png")
    bpy.ops.render.render(write_still=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT / "torre_alva_e_luz.glb"),
                              export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True,
                              export_materials="EXPORT")
    print("ASSET_EXPORT torre_alva_e_luz meshes=", len(meshes))


if __name__ == "__main__":
    main()
