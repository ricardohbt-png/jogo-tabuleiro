"""Cria um galinheiro baixo com três ninhos frontais e ovos visíveis."""
from pathlib import Path
import math

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)
SLUG = "galinheiro"


def mat(name, color, roughness=0.9):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    return m


def box(name, pos, size, material, bevel=0.015, rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    if rot:
        obj.rotation_euler = rot
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    if bevel:
        mod = obj.modifiers.new("Cantos suaves", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def beam(name, a, b, width, depth, material):
    a, b = Vector(a), Vector(b)
    delta = b - a
    return box(name, (a + b) / 2, (delta.length, depth, width), material,
               min(width, depth) * 0.12,
               delta.to_track_quat("X", "Z").to_euler())


def egg_mesh(name, pos, material, rotation):
    # Perfil assimétrico simples de ovo, mais estreito em uma das pontas.
    x, y, z = pos
    rings = [(-0.077, 0.008), (-0.056, 0.034), (-0.020, 0.048),
             (0.020, 0.046), (0.052, 0.032), (0.073, 0.008)]
    sides = 12
    verts = []
    for h, r in rings:
        for i in range(sides):
            a = 2 * math.pi * i / sides
            verts.append((r * math.cos(a), r * math.sin(a), h))
    faces = []
    for row in range(len(rings) - 1):
        for i in range(sides):
            a = row * sides + i
            b = row * sides + (i + 1) % sides
            c = (row + 1) * sides + (i + 1) % sides
            d = (row + 1) * sides + i
            faces.append((a, b, c, d))
    faces.append(tuple(range(sides - 1, -1, -1)))
    top = (len(rings) - 1) * sides
    faces.append(tuple(top + i for i in range(sides)))
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = pos
    obj.rotation_euler = rotation
    return obj


def mesh_obj(name, verts, faces, material):
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(verts, [], faces)
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
    wood = mat("Madeira mel", (0.43, 0.25, 0.12))
    wood_light = mat("Tábuas claras", (0.59, 0.38, 0.20))
    wood_dark = mat("Madeira escura", (0.23, 0.12, 0.06))
    cream = mat("Pintura marfim", (0.77, 0.67, 0.48))
    roof = [mat("Telhas vermelhas %d" % i, c) for i, c in enumerate(
        ((0.43, 0.13, 0.085), (0.56, 0.19, 0.10), (0.36, 0.105, 0.075)))]
    straw = mat("Palha dos ninhos", (0.68, 0.47, 0.20))
    straw_light = mat("Palha dourada", (0.82, 0.62, 0.30))
    white_egg = mat("Casca creme", (0.92, 0.84, 0.66), 0.44)
    brown_egg = mat("Casca marrom", (0.56, 0.31, 0.16), 0.48)
    iron = mat("Ferragens", (0.18, 0.19, 0.17), 0.58)
    dark = mat("Interior do galinheiro", (0.095, 0.065, 0.036))

    # Piso elevado e casinha compacta dentro do footprint de 2x2.
    box("Plataforma de madeira", (0, 0.02, 0.16), (1.78, 1.58, 0.22), wood_dark, 0.035)
    box("Corpo do galinheiro", (0, 0.08, 0.67), (1.48, 1.28, 0.92), cream, 0.02)
    # Tábuas verticais decorativas e postes de canto.
    for x in (-0.70, 0.70):
        for y in (-0.50, 0.66):
            box("Poste de canto", (x, y, 0.72), (0.12, 0.12, 1.10), wood, 0.018)
    for x in (-0.48, -0.24, 0, 0.24, 0.48):
        box("Tábua frontal", (x, -0.576, 0.72), (0.045, 0.035, 0.82), wood_light, 0.008)
    for y in (-0.32, 0.02, 0.36):
        box("Tábua lateral", (0.755, y, 0.72), (0.035, 0.045, 0.82), wood_light, 0.008)
    for y, label in ((-0.57, "frente"), (0.72, "fundo")):
        mesh_obj("Empena " + label,
                 [(-0.72, y, 1.10), (0.72, y, 1.10), (0, y, 1.67)],
                 [(0, 1, 2)], cream)

    # Porta pequena e rampa ficam ao lado das caixas de ninho.
    box("Abertura escura da portinhola", (0.48, -0.605, 0.46), (0.30, 0.035, 0.40), dark, 0.005)
    box("Folha da portinhola", (0.48, -0.633, 0.45), (0.24, 0.045, 0.34), wood_dark, 0.015)
    box("Rampa", (0.49, -0.79, 0.22), (0.28, 0.48, 0.08), wood_light, 0.02,
        rot=(math.radians(-19), 0, 0))
    for x in (0.40, 0.49, 0.58):
        beam("Ripa da rampa", (x, -0.98, 0.12), (x, -0.59, 0.30), 0.025, 0.025, wood_dark)

    # Três caixas abertas voltadas para a frente, com cama de palha e ovos.
    nest_centers = (-0.48, 0.0, 0.48)
    for n, cx in enumerate(nest_centers):
        back_y = -0.66
        front_y = -1.015
        floor_z = 0.48
        box("Fundo do ninho", (cx, back_y, 0.67), (0.43, 0.08, 0.43), wood_dark, 0.012)
        box("Base do ninho", (cx, -0.85, floor_z), (0.46, 0.43, 0.09), wood, 0.012)
        for side in (-1, 1):
            box("Lateral do ninho", (cx + side * 0.22, -0.85, 0.64),
                (0.07, 0.43, 0.38), wood_light, 0.012)
        box("Borda frontal do ninho", (cx, front_y, 0.535), (0.46, 0.07, 0.14), wood, 0.012)
        # Feixes de palha cruzados na cama, em relevo para leitura em miniatura.
        for j in range(5):
            xx = cx + (j - 2) * 0.055
            beam("Palha do ninho", (xx - 0.08, -0.94, 0.545),
                 (xx + 0.06, -0.73, 0.56 + 0.01 * (j % 2)),
                 0.018, 0.018, straw if j % 2 else straw_light)
        # Dois ovos em cada ninho, apoiados sobre a palha e visíveis de frente.
        for k, dx in enumerate((-0.09, 0.09)):
            egg_mesh("Ovo %d-%d" % (n + 1, k + 1),
                     (cx + dx, -0.93, 0.69),
                     white_egg if (n + k) % 2 == 0 else brown_egg,
                     (math.pi / 2, 0, (-0.20 if k == 0 else 0.16)))
    # Cobertura estreita sobre os ninhos protege as caixas da chuva.
    box("Beiral dos ninhos", (0, -0.84, 0.91), (1.62, 0.56, 0.12), wood_dark, 0.02,
        rot=(math.radians(-7), 0, 0))
    box("Telhas sobre os ninhos", (0, -0.85, 0.985), (1.68, 0.60, 0.055), roof[1], 0.015,
        rot=(math.radians(-7), 0, 0))

    # Telhado principal em duas águas, com cumeeira e ripas vermelhas.
    ridge_z, eave_z = 1.68, 1.10
    y_front, y_back = -0.70, 0.86
    for side in (-1, 1):
        edge_x = side * 0.92
        verts = [(0, y_front, ridge_z), (0, y_back, ridge_z),
                 (edge_x, y_back, eave_z), (edge_x, y_front, eave_z),
                 (0, y_front, ridge_z - 0.08), (0, y_back, ridge_z - 0.08),
                 (edge_x, y_back, eave_z - 0.08), (edge_x, y_front, eave_z - 0.08)]
        mesh = bpy.data.meshes.new("Telhado | Mesh")
        mesh.from_pydata(verts, [], [(0, 1, 2, 3), (7, 6, 5, 4),
                                     (0, 3, 7, 4), (1, 5, 6, 2),
                                     (0, 4, 5, 1), (3, 2, 6, 7)])
        mesh.materials.append(roof[1 if side > 0 else 0])
        mesh.update()
        roof_obj = bpy.data.objects.new("Água do telhado", mesh)
        bpy.context.collection.objects.link(roof_obj)
        for j, frac in enumerate((0.25, 0.50, 0.75)):
            x = side * (0.89 * frac)
            z = ridge_z - (ridge_z - eave_z) * frac + 0.02
            beam("Ripa de telha", (x, y_front - 0.02, z),
                 (x, y_back + 0.02, z), 0.035, 0.035, roof[(j + 1) % len(roof)])
    beam("Cumeeira", (0, y_front - 0.08, ridge_z + 0.015),
         (0, y_back + 0.08, ridge_z + 0.015), 0.10, 0.10, wood_dark)
    # Caibros frontais aparentes e pequenos adornos de ferro.
    for x in (-0.72, 0.72):
        beam("Caibro de empena", (0, y_front - 0.035, ridge_z - 0.04),
             (x, y_front - 0.035, eave_z + 0.02), 0.055, 0.055, wood_dark)
    for x in (-0.60, 0.60):
        box("Ferragem frontal", (x, -0.61, 1.02), (0.08, 0.025, 0.05), iron, 0.006)


def merge_by_material():
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
        group[0].name = "Galinheiro | " + material.name


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
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.10, 0.09, 0.07, 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35
    for name, loc, energy, size, color in (
        ("Sol de manhã", (2.5, -3.0, 4.0), 260, 3.0, (1.0, 0.84, 0.65)),
        ("Luz de preenchimento", (-3.0, -0.2, 2.5), 150, 2.5, (0.78, 0.88, 1.0)),
        ("Luz de contorno", (0.5, 2.5, 3.0), 190, 2.0, (1.0, 0.78, 0.52)),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        lamp = bpy.context.object
        lamp.name = name
        lamp.data.energy = energy
        lamp.data.shape = "DISK"
        lamp.data.size = size
        lamp.data.color = color
        point_at(lamp, (0, -0.1, 0.72))
    bpy.ops.object.camera_add(location=(2.7, -4.1, 2.55))
    camera = bpy.context.object
    camera.name = "Câmera da miniatura"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 2.85
    point_at(camera, (0, -0.05, 0.78))
    scene.camera = camera
    scene.render.filepath = str(OUT / (SLUG + "_preview.png"))


def export_asset():
    clear_scene()
    build()
    merge_by_material()
    setup_scene()
    scene = bpy.context.scene
    bpy.ops.object.select_all(action="DESELECT")
    meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / (SLUG + ".blend")))
    bpy.ops.render.render(write_still=True)
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.filepath = str(OUT / (SLUG + ".png"))
    bpy.ops.render.render(write_still=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT / (SLUG + ".glb")),
                              export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True,
                              export_materials="EXPORT")
    print("ASSET_EXPORT", SLUG, "meshes=", len(meshes))


if __name__ == "__main__":
    export_asset()
