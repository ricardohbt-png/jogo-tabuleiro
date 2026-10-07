"""Cria a miniatura do celeiro medieval 4x4 para editor e tabuleiro."""
from pathlib import Path
import math

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)
SLUG = "celeiro_medieval"


def mat(name, color, roughness=0.88):
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
        mod = obj.modifiers.new("Arestas gastas", "BEVEL")
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


def mesh_obj(name, verts, faces, material):
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def text_mesh(label, body, pos, size, material, rot=(math.pi / 2, 0, 0)):
    bpy.ops.object.text_add(location=pos, rotation=rot)
    obj = bpy.context.object
    obj.name = label
    obj.data.body = body
    obj.data.align_x = "CENTER"
    obj.data.align_y = "CENTER"
    obj.data.size = size
    obj.data.extrude = 0.002
    obj.data.materials.append(material)
    bpy.ops.object.convert(target="MESH")
    return bpy.context.object


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for data in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                 bpy.data.cameras, bpy.data.lights):
        for block in list(data):
            if block.users == 0:
                data.remove(block)


def build_barn():
    stone = [mat("Pedra da fundação %d" % i, color) for i, color in enumerate((
        (0.39, 0.38, 0.33), (0.48, 0.45, 0.38), (0.32, 0.33, 0.31)))]
    timber = mat("Vigas de carvalho", (0.23, 0.115, 0.052))
    timber_lite = mat("Tábuas de carvalho", (0.38, 0.21, 0.095))
    timber_dark = mat("Madeira sombreada", (0.13, 0.065, 0.03))
    plaster = mat("Reboco de cal envelhecido", (0.66, 0.57, 0.41))
    plaster_light = mat("Reboco claro", (0.76, 0.66, 0.48))
    thatch = [mat("Palha do telhado %d" % i, color) for i, color in enumerate((
        (0.47, 0.30, 0.12), (0.58, 0.38, 0.16), (0.39, 0.24, 0.10)))]
    iron = mat("Ferro forjado", (0.13, 0.15, 0.15), 0.58)
    hay = mat("Feno dourado", (0.61, 0.43, 0.17))
    dark = mat("Interior escuro", (0.075, 0.055, 0.033))

    # Base baixa de pedra; o modelo fica dentro do footprint de quatro casas.
    box("Soleira de pedra", (0, 0, 0.22), (3.62, 3.55, 0.42), stone[0], 0.04)
    box("Parede lateral esquerda", (-1.53, 0.04, 1.20), (0.20, 3.12, 1.62), plaster, 0.025)
    box("Parede lateral direita", (1.53, 0.04, 1.20), (0.20, 3.12, 1.62), plaster_light, 0.025)
    box("Parede dos fundos", (0, 1.53, 1.20), (3.12, 0.20, 1.62), plaster, 0.025)
    # Faixa de pedra da fundação em cada face.
    box("Base lateral esquerda", (-1.64, 0.03, 0.42), (0.18, 3.18, 0.40), stone[1], 0.02)
    box("Base lateral direita", (1.64, 0.03, 0.42), (0.18, 3.18, 0.40), stone[2], 0.02)
    box("Base do fundo", (0, 1.64, 0.42), (3.45, 0.18, 0.40), stone[0], 0.02)

    # Fachada emoldura o portal largo das portas do celeiro.
    box("Parede dianteira esquerda", (-1.22, -1.53, 1.19), (0.72, 0.20, 1.60), plaster_light, 0.02)
    box("Parede dianteira direita", (1.22, -1.53, 1.19), (0.72, 0.20, 1.60), plaster, 0.02)
    box("Parede acima do portal", (0, -1.53, 1.94), (1.75, 0.20, 0.30), plaster_light, 0.02)
    box("Escuridão dentro do portal", (0, -1.646, 1.12), (1.55, 0.025, 1.18), dark, 0)
    # Duas folhas fechadas, cada uma feita de tábuas verticais.
    for side, cx in (("esquerda", -0.39), ("direita", 0.39)):
        for i in range(4):
            x = cx + (i - 1.5) * 0.19
            box("Tábua da porta " + side, (x, -1.69, 1.10), (0.175, 0.075, 1.16),
                timber_lite if i % 2 == 0 else timber, 0.012)
        for z in (0.59, 1.56):
            box("Travessa da porta " + side, (cx, -1.738, z), (0.73, 0.045, 0.105), timber_dark, 0.01)
        beam("Reforço diagonal " + side,
             (cx - 0.32, -1.744, 0.66), (cx + 0.32, -1.744, 1.48),
             0.075, 0.055, timber_dark)
    # Batentes, lintel, dobradiças e puxador de ferro.
    for x in (-0.86, 0.86):
        box("Batente do portal", (x, -1.70, 1.14), (0.15, 0.16, 1.44), timber, 0.025)
        for z in (0.72, 1.45):
            box("Dobradiça grande", (x * 0.84, -1.79, z), (0.30, 0.035, 0.045), iron, 0.006)
    box("Lintel de carvalho", (0, -1.68, 1.91), (1.90, 0.18, 0.16), timber, 0.02)
    box("Aro do puxador", (0.03, -1.79, 1.02), (0.07, 0.035, 0.12), iron, 0.012)

    # Vigas escuras reveladas sobre o reboco, com padrão enxaimel medieval.
    for x in (-1.50, -0.97, 0.97, 1.50):
        box("Esteio frontal", (x, -1.66, 1.22), (0.10, 0.10, 1.48), timber, 0.012)
    box("Viga transversal frontal", (0, -1.65, 2.12), (3.10, 0.10, 0.12), timber, 0.012)
    for x in (-1.50, 1.50):
        box("Esteio lateral", (x, 0.02, 1.19), (0.11, 3.12, 1.48), timber, 0.012)
    for y in (-1.05, 0, 1.05):
        box("Viga de amarração lateral", (0, y, 1.91), (3.12, 0.10, 0.12), timber, 0.012)
    for x in (-1.28, 1.28):
        beam("Escora lateral", (x, -0.54, 1.35), (x, -1.04, 1.84), 0.09, 0.09, timber_dark)
        beam("Escora lateral", (x, 0.54, 1.35), (x, 1.04, 1.84), 0.09, 0.09, timber_dark)

    # Triângulos de empena na frente e nos fundos.
    for y, face_name in ((-1.54, "empena dianteira"), (1.54, "empena traseira")):
        verts = [(-1.54, y, 2.08), (1.54, y, 2.08), (0, y, 3.03)]
        mesh_obj("Reboco da " + face_name, verts, [(0, 1, 2)], plaster)
        beam("Caibro da " + face_name, (-1.48, y - 0.035, 2.12), (0, y - 0.035, 3.00),
             0.095, 0.08, timber)
        beam("Caibro da " + face_name, (0, y - 0.035, 3.00), (1.48, y - 0.035, 2.12),
             0.095, 0.08, timber)
    # Janela de ventilação do sótão, com travessas cruzadas.
    box("Nicho da ventilação", (0, -1.60, 2.47), (0.62, 0.035, 0.38), dark, 0.01)
    box("Moldura da ventilação", (0, -1.635, 2.47), (0.72, 0.055, 0.48), timber, 0.025)
    box("Vão escuro da ventilação", (0, -1.67, 2.47), (0.52, 0.025, 0.30), dark, 0.005)
    beam("X da ventilação", (-0.23, -1.70, 2.35), (0.23, -1.70, 2.59), 0.035, 0.025, timber_lite)
    beam("X da ventilação", (-0.23, -1.70, 2.59), (0.23, -1.70, 2.35), 0.035, 0.025, timber_lite)

    # Placa acima das portas, voltada para o caminho de entrada.
    box("Placa do celeiro", (0, -1.79, 2.00), (1.02, 0.055, 0.22), timber_lite, 0.02)
    text_mesh("Letreiro CELEIRO", "CELEIRO", (0, -1.826, 1.995), 0.135, timber_dark)

    # Telhado de duas águas, com beirais e fileiras de palha em relevo.
    y_front, y_back = -1.88, 1.88
    ridge_z, eave_z = 3.18, 2.06
    for side in (-1, 1):
        edge_x = side * 1.88
        verts = [(0, y_front, ridge_z), (0, y_back, ridge_z),
                 (edge_x, y_back, eave_z), (edge_x, y_front, eave_z),
                 (0, y_front, ridge_z - 0.12), (0, y_back, ridge_z - 0.12),
                 (edge_x, y_back, eave_z - 0.12), (edge_x, y_front, eave_z - 0.12)]
        mesh_obj("Água do telhado", verts,
                 [(0, 1, 2, 3), (7, 6, 5, 4), (0, 3, 7, 4), (1, 5, 6, 2),
                  (0, 4, 5, 1), (3, 2, 6, 7)], thatch[side % 3])
        # Faixas estreitas paralelas à cumeeira dão textura de palha em cada água.
        for j, frac in enumerate((0.18, 0.36, 0.54, 0.72, 0.90)):
            x = side * (1.82 * frac)
            z = ridge_z - (ridge_z - eave_z) * frac + 0.025
            beam("Faixa de palha", (x, y_front + 0.05, z),
                 (x, y_back - 0.05, z), 0.035, 0.035, thatch[(j + 1) % 3])
    beam("Cumeeira", (0, -1.95, 3.13), (0, 1.95, 3.13), 0.15, 0.15, timber_dark)
    # Porta-feno na empena, com fardos visíveis no sótão.
    for x in (-0.20, 0, 0.20):
        box("Fardo no sótão", (x, -1.59, 2.25), (0.19, 0.18, 0.15), hay, 0.025)


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


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
        group[0].name = "Celeiro | " + material.name


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
        ("Preenchimento", (-4.0, -0.2, 3.4), 250, 3.5, (0.73, 0.86, 1.0)),
        ("Recorte dourado", (0.0, 4.0, 5.0), 330, 2.8, (1.0, 0.78, 0.48)),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        lamp = bpy.context.object
        lamp.name = name
        lamp.data.energy = energy
        lamp.data.shape = "DISK"
        lamp.data.size = size
        lamp.data.color = color
        point_at(lamp, (0, 0, 1.25))
    bpy.ops.object.camera_add(location=(5.0, -7.4, 5.0))
    camera = bpy.context.object
    camera.name = "Câmera da miniatura"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 5.55
    point_at(camera, (0, 0, 1.42))
    scene.camera = camera
    scene.render.filepath = str(OUT / (SLUG + "_preview.png"))


def export_asset():
    clear_scene()
    build_barn()
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
