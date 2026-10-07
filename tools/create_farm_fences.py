"""Gera cerca reta, curva, quebrada e porteiras aberta/fechada para o tabuleiro."""
from pathlib import Path
import math

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)


def material(name, color, roughness=0.9):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    m.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (*color, 1)
    m.node_tree.nodes.get("Principled BSDF").inputs["Roughness"].default_value = roughness
    return m


def cube(name, loc, size, mat, bevel=0.015, rotation=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    if rotation:
        obj.rotation_euler = rotation
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("Cantos arredondados", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def beam_between(name, a, b, width, depth, mat):
    a, b = Vector(a), Vector(b)
    delta = b - a
    obj = cube(name, (a + b) / 2, (delta.length, depth, width), mat,
               bevel=min(width, depth) * 0.10,
               rotation=delta.to_track_quat("X", "Z").to_euler())
    return obj


def post(name, x, y, z=0.52, mat=None, size=(0.12, 0.14, 1.04)):
    cube(name, (x, y, z), size, mat, bevel=0.025)
    top = z + size[2] / 2
    cube(name + " ponta", (x, y, top + 0.035), (size[0] * 1.15, size[1] * 1.15, 0.07),
         mat, bevel=0.018)


def curved_rail(name, points, z, width, mat, steps=12):
    # Segmentos curtos retangulares dão aspecto de madeira facetada e robusta.
    coords = []
    for i in range(steps + 1):
        t = i / steps
        angle = math.pi + t * (math.pi / 2)
        coords.append((0.45 * math.cos(angle), 0.45 * math.sin(angle), z))
    for i in range(len(coords) - 1):
        beam_between(name, coords[i], coords[i + 1], width, 0.085, mat)


def add_gate_hinges(x, y, z, metal):
    for zz in (z - 0.25, z + 0.20):
        cube("Dobradiça de ferro", (x, y - 0.085, zz), (0.17, 0.025, 0.045), metal, 0.006)
        cube("Pino da dobradiça", (x - 0.055, y - 0.10, zz), (0.028, 0.03, 0.09), metal, 0.006)


def add_sign(x, y, z, wood, dark):
    cube("Plaquinha da porteira", (x, y - 0.105, z), (0.37, 0.045, 0.20), wood, 0.018)
    # Letras em relevo convertidas para malha, voltadas para a frente do modelo.
    bpy.ops.object.text_add(location=(x, y - 0.132, z - 0.045), rotation=(math.pi / 2, 0, 0))
    txt = bpy.context.object
    txt.name = "Letreiro PASTO"
    txt.data.body = "PASTO"
    txt.data.align_x = "CENTER"
    txt.data.align_y = "CENTER"
    txt.data.size = 0.092
    txt.data.extrude = 0.0015
    txt.data.materials.append(dark)
    bpy.ops.object.convert(target="MESH")


def build(kind):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                       bpy.data.cameras, bpy.data.lights):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)

    wood = material("Madeira de carvalho", (0.32, 0.17, 0.075))
    light_wood = material("Tábuas de madeira", (0.48, 0.29, 0.13))
    dark_wood = material("Veios escuros", (0.16, 0.082, 0.035))
    iron = material("Ferro envelhecido", (0.16, 0.18, 0.18), 0.58)

    if kind == "cerca_reta":
        post("Poste esquerdo", -0.45, 0, mat=wood)
        post("Poste central", 0, 0, z=0.47, mat=wood, size=(0.105, 0.12, 0.94))
        post("Poste direito", 0.45, 0, mat=wood)
        for z in (0.34, 0.68):
            beam_between("Travessa horizontal", (-0.43, -0.005, z), (0.43, -0.005, z),
                         0.12, 0.10, light_wood)
        for x in (-0.27, 0.27):
            cube("Prego de ferro", (x, -0.061, 0.34), (0.035, 0.018, 0.035), iron, 0.006)
            cube("Prego de ferro", (x, -0.061, 0.68), (0.035, 0.018, 0.035), iron, 0.006)

    elif kind == "cerca_curva":
        # Um canto de 90 graus; girar no editor permite formar qualquer quina.
        post("Poste da quina", 0, 0, mat=wood)
        post("Poste da ponta A", -0.45, 0, z=0.47, mat=wood, size=(0.105, 0.12, 0.94))
        post("Poste da ponta B", 0, 0.45, z=0.47, mat=wood, size=(0.105, 0.12, 0.94))
        for z in (0.34, 0.68):
            curved_rail("Travessa curva", (), z, 0.12, light_wood)
        for x, y in ((-0.24, -0.005), (-0.005, 0.24)):
            cube("Prego da quina", (x, y - 0.06, 0.68), (0.032, 0.018, 0.032), iron, 0.005)

    elif kind == "cerca_quebrada":
        # Duas pontas partidas deixam passagem central para criaturas e peões.
        post("Ponta quebrada esquerda", -0.43, 0, z=0.27, mat=wood, size=(0.12, 0.14, 0.54))
        post("Poste direito", 0.43, 0, z=0.43, mat=wood, size=(0.11, 0.13, 0.86))
        beam_between("Travessa caída", (-0.40, -0.01, 0.31), (-0.12, -0.01, 0.14),
                     0.11, 0.09, light_wood)
        beam_between("Travessa partida", (0.12, -0.01, 0.62), (0.40, -0.01, 0.51),
                     0.11, 0.09, light_wood)
        cube("Lasca", (-0.14, -0.01, 0.16), (0.07, 0.10, 0.07), dark_wood, 0.006)
        cube("Prego solto", (0.29, -0.063, 0.51), (0.035, 0.018, 0.035), iron, 0.005)

    else:
        opened = kind == "porteira_aberta"
        post("Poste de dobradiça", -0.47, 0, mat=wood)
        post("Poste de fecho", 0.47, 0, mat=wood)
        add_sign(0.47, 0, 0.91, light_wood, dark_wood)
        add_gate_hinges(-0.40, 0, 0.52, iron)
        if opened:
            # Folha aberta a 90 graus, recolhida para o lado da cerca.
            for z in (0.31, 0.70):
                beam_between("Travessa da porteira aberta", (-0.40, -0.03, z),
                             (-0.40, -0.78, z), 0.105, 0.09, light_wood)
            for y in (-0.16, -0.39, -0.62):
                beam_between("Ripinha aberta", (-0.40, y, 0.32), (-0.40, y, 0.69),
                             0.08, 0.075, wood)
            beam_between("Diagonal da porteira", (-0.40, -0.12, 0.37),
                         (-0.40, -0.67, 0.65), 0.075, 0.075, dark_wood)
        else:
            # Folha fechada alinhada entre postes, com travessa e reforço diagonal.
            for z in (0.31, 0.70):
                beam_between("Travessa da porteira fechada", (-0.40, -0.005, z),
                             (0.40, -0.005, z), 0.105, 0.09, light_wood)
            for x in (-0.29, -0.10, 0.10, 0.29):
                beam_between("Ripa vertical", (x, -0.015, 0.34), (x, -0.015, 0.67),
                             0.075, 0.075, wood)
            beam_between("Diagonal da porteira", (-0.34, -0.065, 0.36),
                         (0.34, -0.065, 0.65), 0.065, 0.06, dark_wood)
            add_gate_hinges(0.40, 0, 0.52, iron)
            cube("Trinco", (0.39, -0.08, 0.52), (0.12, 0.035, 0.045), iron, 0.006)

    # Otimiza a malha agrupando por material, sem juntar madeira e ferragens.
    for mat in list(bpy.data.materials):
        group = [o for o in bpy.context.scene.objects
                 if o.type == "MESH" and o.data.materials and mat in o.data.materials[:]]
        if len(group) < 2:
            continue
        bpy.ops.object.select_all(action="DESELECT")
        for obj in group:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = group[0]
        bpy.ops.object.join()
        group[0].name = kind + " | " + mat.name
        group[0].data.name = group[0].name + " Mesh"

    # A imagem e o GLB compartilham enquadramento isométrico e origem no centro do tile.
    scene = bpy.context.scene
    bpy.ops.object.camera_add(location=(2.25, -3.4, 2.25))
    camera = bpy.context.object
    camera.name = "Câmera de miniatura"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 1.75
    camera.rotation_euler = (Vector((0, 0, 0.53)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera
    for name, loc, energy, size in (("Principal", (1, -2, 3.2), 140, 2.2),
                                    ("Preenchimento", (-2, -1, 2), 75, 2.0),
                                    ("Recorte", (1.2, 2, 2.7), 90, 1.8)):
        bpy.ops.object.light_add(type="AREA", location=loc)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.rotation_euler = (Vector((0, 0, 0.5)) - light.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    scene.render.filepath = str(OUT / (kind + "_preview.png"))
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / (kind + ".blend")))
    bpy.ops.render.render(write_still=True)
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.filepath = str(OUT / (kind + ".png"))
    bpy.ops.render.render(write_still=True)

    bpy.ops.object.select_all(action="DESELECT")
    meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.export_scene.gltf(filepath=str(OUT / (kind + ".glb")), export_format="GLB",
                              use_selection=True, export_apply=True, export_yup=True,
                              export_materials="EXPORT")
    print("ASSET_EXPORT", kind, "meshes=", len(meshes))


if __name__ == "__main__":
    for asset in ("cerca_reta", "cerca_curva", "cerca_quebrada",
                  "porteira_aberta", "porteira_fechada"):
        build(asset)
