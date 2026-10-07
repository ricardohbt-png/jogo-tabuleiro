"""Cria uma cabana rústica de fazenda com varanda e chaminé de pedra."""
from pathlib import Path
import math

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)
SLUG = "cabana_rustica"


def mat(name, color, roughness=0.9):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    return m


def box(name, pos, size, material, bevel=0.02, rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    if rot:
        obj.rotation_euler = rot
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    if bevel:
        mod = obj.modifiers.new("Bordas gastas", "BEVEL")
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


def cylinder(name, pos, radius, depth, material, axis="Z", vertices=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                        location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    if axis == "X":
        obj.rotation_euler[1] = math.pi / 2
    elif axis == "Y":
        obj.rotation_euler[0] = math.pi / 2
    return obj


def mesh_obj(name, verts, faces, material):
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def log_wall(x1, x2, y1, y2, z, radius, wood, row):
    # Quatro troncos intertravados em cada fiada, com as pontas cruzando os cantos.
    cylinder("Tronco frontal", (0, y1, z), radius, x2 - x1, wood, "X", 14)
    cylinder("Tronco traseiro", (0, y2, z), radius, x2 - x1, wood, "X", 14)
    cylinder("Tronco lateral esquerdo", (x1, 0, z), radius, y2 - y1, wood, "Y", 14)
    cylinder("Tronco lateral direito", (x2, 0, z), radius, y2 - y1, wood, "Y", 14)
    # Entalhes escuros pequenos nas pontas sugerem encaixe de cabana artesanal.
    if row % 2 == 0:
        for x in (x1 + 0.04, x2 - 0.04):
            box("Marca de entalhe", (x, y1, z + radius * 0.45),
                (0.035, 0.035, 0.022), wood, 0.003)


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
    timber = [mat("Troncos de pinho %d" % i, color) for i, color in enumerate((
        (0.36, 0.20, 0.095), (0.45, 0.27, 0.13), (0.29, 0.15, 0.068)))]
    boards = mat("Tábuas da varanda", (0.50, 0.32, 0.16))
    dark_wood = mat("Madeira escura", (0.18, 0.092, 0.042))
    roof = [mat("Telhado de madeira %d" % i, color) for i, color in enumerate((
        (0.25, 0.18, 0.12), (0.33, 0.23, 0.14), (0.20, 0.14, 0.10)))]
    stone = [mat("Pedra da chaminé %d" % i, color) for i, color in enumerate((
        (0.40, 0.39, 0.35), (0.50, 0.47, 0.41), (0.32, 0.33, 0.31)))]
    glass = mat("Vidro escuro", (0.12, 0.22, 0.25), 0.42)
    iron = mat("Ferro envelhecido", (0.15, 0.16, 0.15), 0.56)

    # Base de pedra e seis fiadas de troncos arredondados.
    box("Fundação de pedra", (0, 0.02, 0.20), (2.66, 2.42, 0.36), stone[0], 0.04)
    for row in range(6):
        z = 0.48 + row * 0.235
        log_wall(-1.20, 1.20, -1.00, 1.00, z, 0.125, timber[row % len(timber)], row)
    # Vigas mais escuras reforçam as quinas e o topo das paredes.
    for x in (-1.16, 1.16):
        for y in (-0.96, 0.96):
            box("Coluna de canto", (x, y, 1.17), (0.14, 0.14, 1.45), dark_wood, 0.018)
    for y in (-1.01, 1.01):
        box("Frechal frontal/traseiro", (0, y, 1.82), (2.48, 0.15, 0.14), dark_wood, 0.018)
    for x in (-1.21, 1.21):
        box("Frechal lateral", (x, 0, 1.82), (0.15, 2.12, 0.14), dark_wood, 0.018)

    # Porta de madeira e duas janelas com moldura no frontão voltado para a varanda.
    box("Porta escura", (0, -1.075, 0.99), (0.60, 0.055, 1.14), dark_wood, 0.018)
    for x in (-0.235, -0.08, 0.08, 0.235):
        box("Tábua da porta", (x, -1.112, 0.99), (0.12, 0.035, 1.05), boards, 0.01)
    beam("Travessa da porta", (-0.28, -1.14, 0.72), (0.28, -1.14, 0.72), 0.055, 0.035, dark_wood)
    for x in (-0.76, 0.76):
        box("Vidro da janela", (x, -1.073, 1.28), (0.34, 0.045, 0.38), glass, 0.01)
        box("Moldura vertical da janela", (x, -1.11, 1.28), (0.41, 0.06, 0.055), boards, 0.008)
        box("Moldura horizontal da janela", (x, -1.11, 1.28), (0.055, 0.06, 0.43), boards, 0.008)
        box("Travessa da janela", (x, -1.145, 1.28), (0.025, 0.025, 0.35), dark_wood, 0.004)
        box("Travessa da janela", (x, -1.145, 1.28), (0.32, 0.025, 0.025), dark_wood, 0.004)

    # Empenas triangulares de madeira no frontão e na parede dos fundos.
    for y, name in ((-1.00, "dianteira"), (1.00, "traseira")):
        mesh_obj("Empena " + name,
                 [(-1.18, y, 1.83), (1.18, y, 1.83), (0, y, 2.60)],
                 [(0, 1, 2)], boards)
        beam("Caibro frontal", (-1.15, y - 0.035, 1.85), (0, y - 0.035, 2.58),
             0.075, 0.07, dark_wood)
        beam("Caibro frontal", (0, y - 0.035, 2.58), (1.15, y - 0.035, 1.85),
             0.075, 0.07, dark_wood)
    box("Respiradouro triangular", (0, -1.045, 2.16), (0.28, 0.035, 0.18), glass, 0.01)
    beam("Travessa do respiradouro", (-0.15, -1.08, 2.16), (0.15, -1.08, 2.16),
         0.025, 0.02, dark_wood)

    # Telhado principal de duas águas com beirais e ripas aparentes.
    ridge_z, eave_z = 2.73, 1.86
    y_front, y_back = -1.27, 1.27
    for side in (-1, 1):
        edge_x = side * 1.39
        verts = [(0, y_front, ridge_z), (0, y_back, ridge_z),
                 (edge_x, y_back, eave_z), (edge_x, y_front, eave_z),
                 (0, y_front, ridge_z - 0.11), (0, y_back, ridge_z - 0.11),
                 (edge_x, y_back, eave_z - 0.11), (edge_x, y_front, eave_z - 0.11)]
        mesh = bpy.data.meshes.new("Água do telhado Mesh")
        mesh.from_pydata(verts, [], [(0, 1, 2, 3), (7, 6, 5, 4),
                                     (0, 3, 7, 4), (1, 5, 6, 2),
                                     (0, 4, 5, 1), (3, 2, 6, 7)])
        mesh.materials.append(roof[1 if side > 0 else 0])
        mesh.update()
        obj = bpy.data.objects.new("Água do telhado", mesh)
        bpy.context.collection.objects.link(obj)
        for j, frac in enumerate((0.26, 0.52, 0.78)):
            x = side * (1.35 * frac)
            z = ridge_z - (ridge_z - eave_z) * frac + 0.025
            beam("Ripa do telhado", (x, y_front - 0.015, z),
                 (x, y_back + 0.015, z), 0.035, 0.035, roof[(j + 1) % len(roof)])
    beam("Cumeeira", (0, y_front - 0.06, ridge_z), (0, y_back + 0.06, ridge_z),
         0.12, 0.12, dark_wood)

    # Varanda frontal: piso, cobertura inclinada e dois pilares robustos.
    box("Piso da varanda", (0, -1.32, 0.22), (2.55, 0.52, 0.16), boards, 0.025)
    for x in (-1.13, 1.13):
        box("Pilar da varanda", (x, -1.48, 0.98), (0.13, 0.13, 1.46), dark_wood, 0.018)
        box("Capitel do pilar", (x, -1.48, 1.74), (0.20, 0.20, 0.10), boards, 0.018)
    beam("Caibro dianteiro da varanda", (-1.24, -1.58, 1.78),
         (1.24, -1.58, 1.78), 0.11, 0.12, dark_wood)
    # Cobertura de uma água encosta sob o beiral principal.
    verts = [(-1.30, -1.62, 1.78), (1.30, -1.62, 1.78),
             (1.30, -1.03, 1.98), (-1.30, -1.03, 1.98),
             (-1.30, -1.62, 1.70), (1.30, -1.62, 1.70),
             (1.30, -1.03, 1.90), (-1.30, -1.03, 1.90)]
    mesh_obj("Cobertura da varanda", verts,
             [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (3, 2, 6, 7),
              (0, 3, 7, 4), (1, 5, 6, 2)], roof[1])
    for x in (-0.90, -0.45, 0, 0.45, 0.90):
        beam("Ripa da varanda", (x, -1.64, 1.76), (x, -1.03, 1.95),
             0.035, 0.035, boards)
    # Banco simples de varanda, preso à parede ao lado da porta.
    box("Banco da varanda", (-0.78, -1.32, 0.57), (0.48, 0.25, 0.09), boards, 0.018)
    for x in (-0.96, -0.60):
        box("Pé do banco", (x, -1.32, 0.39), (0.07, 0.20, 0.33), dark_wood, 0.012)

    # Chaminé de pedra na lateral direita, subindo acima da cumeeira.
    chimney_x, chimney_y = 0.93, 0.70
    for row in range(8):
        z = 1.20 + row * 0.16
        block_mat = stone[(row * 2) % len(stone)]
        box("Bloco da chaminé", (chimney_x, chimney_y, z), (0.48, 0.50, 0.18),
            block_mat, 0.025)
    box("Boca escura da chaminé", (chimney_x, chimney_y, 2.45), (0.32, 0.33, 0.08), dark_wood, 0.015)
    box("Aro da chaminé", (chimney_x, chimney_y, 2.52), (0.58, 0.60, 0.12), stone[1], 0.025)


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
        group[0].name = "Cabana rústica | " + material.name


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
        ("Sol quente", (3.0, -3.5, 5.0), 350, 3.5, (1.0, 0.82, 0.60)),
        ("Luz de preenchimento", (-3.2, -0.5, 3.0), 210, 3.0, (0.78, 0.88, 1.0)),
        ("Recorte dourado", (0.3, 3.2, 4.2), 280, 2.6, (1.0, 0.78, 0.50)),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        lamp = bpy.context.object
        lamp.name = name
        lamp.data.energy = energy
        lamp.data.shape = "DISK"
        lamp.data.size = size
        lamp.data.color = color
        point_at(lamp, (0, -0.05, 1.35))
    bpy.ops.object.camera_add(location=(4.5, -6.8, 4.4))
    camera = bpy.context.object
    camera.name = "Câmera da miniatura"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 4.10
    point_at(camera, (0, -0.15, 1.48))
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
