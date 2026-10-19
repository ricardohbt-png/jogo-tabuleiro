"""Gera a miniatura 3D da choupana de palha escura do vilarejo ribeirinho."""
from pathlib import Path
import math

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)
SLUG = "choupana_palha_escura"


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
    timber = [mat("Madeira escura %d" % i, color) for i, color in enumerate((
        (0.20, 0.105, 0.052), (0.29, 0.16, 0.075), (0.36, 0.21, 0.105),
    ))]
    reed = [mat("Trama de taquara %d" % i, color) for i, color in enumerate((
        (0.28, 0.20, 0.115), (0.38, 0.28, 0.16), (0.22, 0.16, 0.10),
    ))]
    thatch = [mat("Palha escura %d" % i, color) for i, color in enumerate((
        (0.045, 0.031, 0.018), (0.075, 0.050, 0.026),
        (0.105, 0.067, 0.032), (0.030, 0.024, 0.015),
    ))]
    clay = mat("Argila vermelho-ocre", (0.43, 0.16, 0.075))
    dark = mat("Interior escuro", (0.045, 0.035, 0.025))
    rope = mat("Corda vegetal", (0.46, 0.34, 0.18))

    # Postes e travessas levantam a casa acima do terreno úmido da margem.
    for x in (-1.06, 1.06):
        for y in (-0.91, 0.91):
            beam("Estaca de sustentação", (x, y, 0.06), (x, y, 0.82), 0.075,
                 timber[0], 10)
    for z in (0.28, 0.73):
        beam("Travessa lateral", (-1.08, -0.91, z), (-1.08, 0.91, z),
             0.052, timber[1])
        beam("Travessa lateral", (1.08, -0.91, z), (1.08, 0.91, z),
             0.052, timber[1])
        beam("Travessa frontal", (-1.06, -0.91, z), (1.06, -0.91, z),
             0.052, timber[1])
        beam("Travessa traseira", (-1.06, 0.91, z), (1.06, 0.91, z),
             0.052, timber[1])

    # Plataforma de tábuas encaixadas, sem decoração solta no footprint.
    box("Viga da plataforma", (0, 0, 0.84), (2.40, 2.15, 0.16), timber[0], 0.025)
    for y in [i * 0.19 - 0.95 for i in range(11)]:
        box("Tábua do assoalho", (0, y, 0.94), (2.28, 0.17, 0.075),
            timber[1 + (int((y + 1) * 10) % 2)], 0.012)

    # Parede de trama vegetal; a frente é dividida para manter a entrada legível.
    wall_bottom, wall_top = 0.98, 2.18
    box("Parede lateral esquerda", (-0.99, 0, 1.56), (0.09, 1.84, 1.16), reed[0], 0.01)
    box("Parede lateral direita", (0.99, 0, 1.56), (0.09, 1.84, 1.16), reed[1], 0.01)
    box("Parede dos fundos", (0, 0.89, 1.56), (1.98, 0.09, 1.16), reed[0], 0.01)
    # Frente: porta central escura, sem folha, flanqueada por painéis trançados.
    box("Painel frontal esquerdo", (-0.70, -0.89, 1.56), (0.58, 0.09, 1.16), reed[1], 0.01)
    box("Painel frontal direito", (0.70, -0.89, 1.56), (0.58, 0.09, 1.16), reed[2], 0.01)
    box("Verga acima da entrada", (0, -0.89, 2.02), (0.82, 0.10, 0.27), reed[0], 0.01)
    box("Vão escuro da porta", (0, -0.852, 1.46), (0.68, 0.025, 0.88), dark, 0.0)

    # Esteios verticais e cordas horizontais sugerem a trama artesanal de taquara.
    for x in (-0.96, -0.72, -0.48, -0.24, 0, 0.24, 0.48, 0.72, 0.96):
        if abs(x) < 0.36:
            continue
        beam("Esteio da trama", (x, -0.952, wall_bottom), (x, -0.952, wall_top),
             0.022, timber[2])
    for z in (1.10, 1.30, 1.50, 1.70, 1.90, 2.08):
        beam("Amarra frontal", (-0.98, -0.965, z), (0.98, -0.965, z), 0.014, rope)
    for y in (-0.70, -0.35, 0, 0.35, 0.70):
        beam("Esteio lateral", (1.045, y, wall_bottom), (1.045, y, wall_top),
             0.020, timber[2])

    # Moldura de madeira escura e um motivo geométrico em argila sobre a entrada.
    for x in (-0.39, 0.39):
        box("Montante da porta", (x, -1.00, 1.43), (0.075, 0.075, 0.98), timber[0], 0.01)
    box("Lintel da porta", (0, -1.00, 1.94), (0.86, 0.075, 0.10), timber[0], 0.01)
    # Losango ocre em relevo, referência gráfica discreta sem texto.
    mesh_obj("Motivo tribal de argila", [
        (-0.18, -1.012, 2.10), (0, -1.025, 2.22),
        (0.18, -1.012, 2.10), (0, -1.025, 1.98),
    ], [(0, 1, 2, 3)], clay)
    for x in (-0.27, 0.27):
        box("Marca de argila", (x, -1.012, 2.10), (0.035, 0.02, 0.11), clay, 0.004)

    # Frontões triangulares fecham a construção sob o telhado de duas águas.
    for y, name in ((-0.90, "dianteiro"), (0.90, "traseiro")):
        mesh_obj("Frontão " + name,
                 [(-1.00, y, wall_top), (1.00, y, wall_top), (0, y, 3.06)],
                 [(0, 1, 2)], reed[0])

    # Telhado espesso de duas águas e cumeeira alta, todo coberto de palha escura.
    ridge_z, eave_z = 3.18, 2.12
    y_front, y_back = -1.38, 1.38
    roof_edge = 1.43
    for side in (-1, 1):
        edge_x = side * roof_edge
        verts = [
            (0, y_front, ridge_z), (0, y_back, ridge_z),
            (edge_x, y_back, eave_z), (edge_x, y_front, eave_z),
            (0, y_front, ridge_z - 0.12), (0, y_back, ridge_z - 0.12),
            (edge_x, y_back, eave_z - 0.12), (edge_x, y_front, eave_z - 0.12),
        ]
        mesh_obj("Massa de palha do telhado", verts,
                 [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
                  (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)],
                 thatch[0 if side < 0 else 1])
        # Fibras corridas da cumeeira ao beiral criam textura de palha, não telhas.
        for col, y in enumerate([-1.28 + i * 0.18 for i in range(15)]):
            for strand, offset in enumerate((-0.035, 0.0, 0.035)):
                sway = ((col + strand) % 3 - 1) * 0.018
                beam("Feixe de palha", (side * 0.055, y + offset, ridge_z - 0.035),
                     (side * (roof_edge - 0.015), y + offset + sway, eave_z + 0.045),
                     0.022 + ((col + strand) % 2) * 0.008,
                     thatch[(col + strand) % len(thatch)], 6)
        # Palha pendente na beirada dá ao telhado um contorno irregular.
        for col, y in enumerate([-1.22 + i * 0.20 for i in range(13)]):
            drop = 0.10 + (col % 3) * 0.025
            beam("Franja de palha", (edge_x, y, eave_z + 0.06),
                 (edge_x + side * 0.025, y + 0.015, eave_z - drop),
                 0.025, thatch[(col + side) % len(thatch)], 6)

    beam("Cumeeira trançada", (0, y_front - 0.03, ridge_z + 0.025),
         (0, y_back + 0.03, ridge_z + 0.025), 0.075, thatch[2], 10)

    # Pequena escada frontal alinhada à porta, incluída no mesmo limite de 3 casas.
    for step in range(4):
        y = -1.02 - step * 0.12
        z = 0.79 - step * 0.19
        box("Degrau da escada", (0, y, z), (0.72, 0.16, 0.08), timber[1], 0.012)
    for x in (-0.37, 0.37):
        beam("Lateral da escada", (x, -1.02, 0.90), (x, -1.46, 0.12),
             0.035, timber[0], 8)


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
        group[0].name = "Choupana de palha escura | " + material.name


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
    camera.name = "Câmera da miniatura ribeirinha"
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
