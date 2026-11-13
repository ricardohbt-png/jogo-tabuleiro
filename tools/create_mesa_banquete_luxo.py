"""Cria a mesa de banquete 2x3 com cadeiras, louça e castiçais."""
from pathlib import Path
import math

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)


def material(name, color, metallic=0.0, roughness=0.72):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return mat


def assign(obj, mat):
    obj.data.materials.append(mat)
    return obj


def cube(name, loc, dims, mat, bevel=0.0, rotation=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    if rotation:
        obj.rotation_euler = rotation
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, mat)
    if bevel:
        mod = obj.modifiers.new("Bordas esculpidas", "BEVEL")
        mod.width = bevel
        mod.segments = 1
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        norm = obj.modifiers.new("Normais suaves", "WEIGHTED_NORMAL")
        bpy.ops.object.modifier_apply(modifier=norm.name)
    return obj


def cylinder(name, loc, radius, depth, mat, vertices=16,
             rotation=None, radius_top=None):
    kwargs = dict(vertices=vertices, radius=radius, depth=depth,
                  location=loc, rotation=rotation or (0, 0, 0))
    if radius_top is None:
        bpy.ops.mesh.primitive_cylinder_add(**kwargs)
    else:
        del kwargs["radius"]
        kwargs["radius1"] = radius
        kwargs["radius2"] = radius_top
        bpy.ops.mesh.primitive_cone_add(**kwargs)
    obj = bpy.context.object
    obj.name = name
    assign(obj, mat)
    bevel = obj.modifiers.new("Aresta polida", "BEVEL")
    bevel.width = min(radius * 0.06, 0.012)
    bevel.segments = 1
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    return obj


def sphere(name, loc, scale, mat, segments=12, rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,
                                        ring_count=rings, radius=1,
                                        location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, mat)
    return obj


def rod(name, start, end, radius, mat, vertices=8):
    a, b = Vector(start), Vector(end)
    delta = b - a
    obj = cylinder(name, (a + b) * 0.5, radius, delta.length,
                   mat, vertices)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = delta.to_track_quat("Z", "Y")
    return obj


def table_materials():
    return {
        "wood": material("Nogueira escura polida", (0.20, 0.075, 0.035)),
        "wood_light": material("Nogueira iluminada", (0.36, 0.16, 0.065)),
        "gold": material("Latão dourado", (0.68, 0.39, 0.095), 0.72, 0.32),
        "gold_light": material("Dourado claro", (0.92, 0.68, 0.26), 0.56, 0.30),
        "cloth": material("Toalha de veludo bordô", (0.22, 0.008, 0.034), 0.0, 0.92),
        "runner": material("Caminho de mesa azul real", (0.035, 0.10, 0.30), 0.0, 0.85),
        "trim": material("Fio de ouro bordado", (0.84, 0.59, 0.20), 0.42, 0.44),
        "cushion": material("Veludo das cadeiras", (0.32, 0.014, 0.046), 0.0, 0.9),
        "porcelain": material("Porcelana marfim", (0.93, 0.88, 0.73), 0.04, 0.28),
        "blue": material("Filete azul da louça", (0.035, 0.12, 0.37), 0.1, 0.32),
        "silver": material("Talheres de prata", (0.70, 0.74, 0.76), 0.82, 0.25),
        "wine": material("Vinho rubi", (0.30, 0.012, 0.035), 0.0, 0.24),
        "candle": material("Cera de vela", (0.96, 0.86, 0.63), 0.0, 0.68),
        "flame": material("Chama dourada", (1.0, 0.40, 0.035), 0.0, 0.35),
    }


def add_table(m):
    wood, light = m["wood"], m["wood_light"]
    gold, gilt = m["gold"], m["gold_light"]
    cloth, runner, trim = m["cloth"], m["runner"], m["trim"]

    # Tampo alongado orientado no eixo Y, para ocupar 2x3 casas.
    cube("Mesa | tampo de nogueira", (0, 0, 1.04), (1.43, 2.24, 0.16), wood, 0.045)
    cube("Mesa | filete dourado", (0, 0, 1.13), (1.39, 2.20, 0.045), gold, 0.018)
    cube("Toalha | superfície bordô", (0, 0, 1.17), (1.43, 2.24, 0.055), cloth, 0.025)
    # Barras pendentes da toalha, com friso bordado nos quatro lados.
    for side in (-1, 1):
        x = side * 0.704
        cube("Toalha | caída lateral", (x, 0, 0.985), (0.035, 2.18, 0.34), cloth, 0.012)
        cube("Toalha | bordado lateral", (x + side * 0.021, 0, 0.84),
             (0.015, 2.14, 0.035), trim, 0.008)
    for side in (-1, 1):
        y = side * 1.105
        cube("Toalha | caída nas cabeceiras", (0, y, 0.985),
             (1.38, 0.035, 0.34), cloth, 0.012)
        cube("Toalha | bordado nas pontas", (0, y + side * 0.021, 0.84),
             (1.34, 0.015, 0.035), trim, 0.008)
    # Caminho azul com bordas finas e motivos dourados repetidos.
    cube("Caminho de mesa | veludo azul", (0, 0, 1.208), (0.34, 2.04, 0.025), runner, 0.012)
    for x in (-0.145, 0.145):
        cube("Caminho | borda dourada", (x, 0, 1.224), (0.018, 1.99, 0.012), trim, 0.004)
    for y in (-0.82, -0.41, 0, 0.41, 0.82):
        sphere("Caminho | flor bordada", (0, y, 1.232), (0.055, 0.055, 0.012), gilt, 8, 6)
        for side in (-1, 1):
            sphere("Caminho | pétala", (side * 0.055, y, 1.232),
                   (0.038, 0.022, 0.01), trim, 8, 6)

    # Estrutura, pernas torneadas e acabamentos sob a toalha.
    cube("Mesa | avental frontal", (0, -0.93, 0.87), (1.20, 0.12, 0.25), light, 0.025)
    cube("Mesa | avental traseiro", (0, 0.93, 0.87), (1.20, 0.12, 0.25), light, 0.025)
    for x in (-0.57, 0.57):
        cube("Mesa | avental lateral", (x, 0, 0.87), (0.12, 1.76, 0.25), light, 0.025)
    for x in (-0.55, 0.55):
        for y in (-0.88, 0.88):
            cylinder("Mesa | perna talhada", (x, y, 0.47), 0.105, 0.77, wood, 10,
                     radius_top=0.075)
            cylinder("Mesa | pé dourado", (x, y, 0.12), 0.15, 0.12, gold, 10,
                     radius_top=0.115)
            cylinder("Mesa | anel da perna", (x, y, 0.70), 0.112, 0.055, gilt, 10)
            sphere("Mesa | ornamento do pé", (x, y, 0.055), (0.10, 0.10, 0.065), wood, 10, 6)


def add_chair(m, x, y, facing):
    """Cadeira de espaldar alto; facing é o vetor para a mesa."""
    wood, light = m["wood"], m["wood_light"]
    gold, gilt = m["gold"], m["gold_light"]
    cushion, cloth = m["cushion"], m["cloth"]
    # O assento aponta para o centro; encosto sobe no lado oposto.
    fx, fy = facing
    bx, by = -fx, -fy
    seat_z = 0.63
    cube("Cadeira | assento entalhado", (x, y, seat_z), (0.43, 0.43, 0.16), wood, 0.045)
    cube("Cadeira | almofada de veludo", (x, y, seat_z + 0.095), (0.39, 0.39, 0.095), cushion, 0.045)
    # Pernas e sapatas douradas.
    for dx in (-0.16, 0.16):
        for dy in (-0.15, 0.15):
            px, py = x + dx, y + dy
            cylinder("Cadeira | perna torneada", (px, py, 0.32), 0.043, 0.55, light, 8,
                     radius_top=0.03)
            cylinder("Cadeira | ponteira", (px, py, 0.075), 0.055, 0.08, gold, 8)
    # Travessas e apoios dos braços em madeira dourada.
    for side in (-1, 1):
        if abs(fx) > 0:
            sx, sy = x, y + side * 0.21
            arm_dims = (0.39, 0.075, 0.085)
        else:
            sx, sy = x + side * 0.21, y
            arm_dims = (0.075, 0.39, 0.085)
        cube("Cadeira | braço", (sx, sy, 0.84), arm_dims, light, 0.025)
        cylinder("Cadeira | detalhe do braço", (sx, sy, 0.89), 0.055, 0.035, gold, 10)
        rod("Cadeira | montante do encosto",
            (x + side * 0.17, y, 0.68),
            (x + side * 0.17 + bx * 0.04, y + by * 0.04, 1.36),
            0.045, light, 8)
    # Painel alto acolchoado e moldura no lado oposto à mesa.
    back_center = (x + bx * 0.20, y + by * 0.20, 1.12)
    back_dims = (0.10, 0.36, 0.57) if abs(fx) > 0 else (0.36, 0.10, 0.57)
    cube("Cadeira | espaldar de veludo", back_center, back_dims, cushion, 0.045)
    # Medalhão do encosto voltado para a câmera, sempre no centro do painel.
    if abs(fx) > 0:
        med_x = back_center[0] + bx * 0.056
        sphere("Cadeira | brasão dourado", (med_x, back_center[1], 1.16),
               (0.018, 0.085, 0.105), gilt, 10, 8)
        sphere("Cadeira | flor central", (med_x + bx * 0.02, back_center[1], 1.16),
               (0.012, 0.035, 0.055), gold, 8, 6)
    else:
        med_y = back_center[1] + by * 0.056
        sphere("Cadeira | brasão dourado", (back_center[0], med_y, 1.16),
               (0.085, 0.018, 0.105), gilt, 10, 8)
        sphere("Cadeira | flor central", (back_center[0], med_y + by * 0.02, 1.16),
               (0.035, 0.012, 0.055), gold, 8, 6)
    # Travessa superior, pequenas volutas e ponteiras.
    if abs(fx) > 0:
        cube("Cadeira | coroamento", (x, y, 1.43), (0.48, 0.12, 0.11), light, 0.035)
        for dx in (-0.21, 0.21):
            sphere("Cadeira | pináculo", (x + dx, y, 1.51), (0.055, 0.055, 0.075), gilt, 8, 6)
    else:
        cube("Cadeira | coroamento", (x, y, 1.43), (0.12, 0.48, 0.11), light, 0.035)
        for dy in (-0.21, 0.21):
            sphere("Cadeira | pináculo", (x, y + dy, 1.51), (0.055, 0.055, 0.075), gilt, 8, 6)
    # Faixa dourada no avental frontal do assento.
    if abs(fx) > 0:
        frieze_loc, frieze_dims = (x + fx * 0.215, y, 0.57), (0.025, 0.34, 0.035)
    else:
        frieze_loc, frieze_dims = (x, y + fy * 0.215, 0.57), (0.34, 0.025, 0.035)
    cube("Cadeira | friso do assento", frieze_loc, frieze_dims, gold, 0.008)


def add_place_setting(m, x, y, direction):
    porcelain, blue, silver, gold, wine = (
        m["porcelain"], m["blue"], m["silver"], m["gold"], m["wine"])
    # Prato raso, filete azul e prato menor empilhado.
    cylinder("Louça | prato carregador", (x, y, 1.255), 0.145, 0.025, gold, 20)
    cylinder("Louça | prato de porcelana", (x, y, 1.275), 0.128, 0.025, porcelain, 20)
    cylinder("Louça | borda azul", (x, y, 1.291), 0.108, 0.012, blue, 20)
    cylinder("Louça | prato menor", (x, y, 1.301), 0.092, 0.015, porcelain, 20)
    # Taça facetada junto ao prato, com haste dourada e vinho visível.
    gx = x + direction[0] * 0.19
    gy = y + direction[1] * 0.19
    cylinder("Taça | pé", (gx, gy, 1.255), 0.045, 0.018, gold, 12)
    cylinder("Taça | haste", (gx, gy, 1.31), 0.012, 0.10, silver, 8)
    cylinder("Taça | bojo", (gx, gy, 1.39), 0.057, 0.10, porcelain, 12, radius_top=0.035)
    cylinder("Taça | vinho", (gx, gy, 1.405), 0.043, 0.035, wine, 12)
    # Faca e garfo, alinhados com cada lugar.
    for side in (-1, 1):
        cx = x + side * 0.19
        rod("Talher | cabo", (cx, y - 0.09, 1.255), (cx, y + 0.09, 1.255), 0.012, gold, 6)
        if side < 0:
            rod("Talher | lâmina", (cx, y + 0.07, 1.255), (cx, y + 0.14, 1.255), 0.018, silver, 6)
        else:
            for tine in (-0.018, 0, 0.018):
                rod("Talher | dente do garfo",
                    (cx + tine, y + 0.10, 1.255), (cx + tine, y + 0.16, 1.255),
                    0.006, silver, 5)


def add_candlestick(m, x, y):
    gold, gilt, wax, flame = m["gold"], m["gold_light"], m["candle"], m["flame"]
    cylinder("Castiçal | base", (x, y, 1.27), 0.095, 0.045, gold, 12)
    cylinder("Castiçal | haste", (x, y, 1.43), 0.025, 0.28, gilt, 10)
    for z in (1.34, 1.49):
        sphere("Castiçal | nó", (x, y, z), (0.045, 0.045, 0.035), gold, 8, 6)
    cylinder("Castiçal | prato", (x, y, 1.57), 0.078, 0.025, gold, 12)
    cylinder("Vela | cera", (x, y, 1.74), 0.036, 0.34, wax, 10)
    sphere("Vela | chama", (x, y, 1.94), (0.035, 0.035, 0.075), flame, 8, 6)


def make_banquet():
    m = table_materials()
    add_table(m)
    # Três lugares de cada lado e uma cadeira em cada cabeceira: oito assentos.
    for xside in (-1, 1):
        for y in (-0.78, 0, 0.78):
            add_chair(m, xside * 0.80, y, (-xside, 0))
            add_place_setting(m, xside * 0.43, y, (-xside, 0))
    for side in (-1, 1):
        add_chair(m, 0, side * 1.38, (0, -side))
        add_place_setting(m, 0, side * 0.91, (0, -side))
    # Três castiçais de mesa, alinhados sobre o caminho bordado.
    for y in (-0.73, 0, 0.73):
        add_candlestick(m, 0, y)


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    make_banquet()

    target = (0, 0, 0.82)
    bpy.ops.object.camera_add(location=(4.8, -6.4, 5.6))
    camera = bpy.context.object
    camera.name = "Câmera | miniatura isométrica"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 4.45
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
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.08, 0.07, 0.06, 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.25
    for name, location, power, size, color in (
        ("Luz principal", (4.5, -5.0, 8.0), 1050, 5.0, (1.0, 0.84, 0.66)),
        ("Luz de preenchimento", (-4.0, -1.5, 5.5), 650, 4.5, (0.76, 0.84, 1.0)),
        ("Luz de recorte", (0.5, 4.5, 7.0), 750, 4.0, (1.0, 0.72, 0.48)),
    ):
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
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "mesa_banquete_luxo.blend"))
    scene.render.filepath = str(OUT / "mesa_banquete_luxo_preview.png")
    bpy.ops.render.render(write_still=True)
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.filepath = str(OUT / "mesa_banquete_luxo.png")
    bpy.ops.render.render(write_still=True)
    # Combina as peças por objeto antes da exportação; os slots de material
    # permanecem separados, reduzindo os draw calls do conjunto no tabuleiro.
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    export_meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    print("GLB_MERGED_MESHES", len(export_meshes))
    bpy.ops.export_scene.gltf(filepath=str(OUT / "mesa_banquete_luxo.glb"),
                              export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True,
                              export_materials="EXPORT")
    print("ASSET_EXPORT mesa_banquete_luxo meshes=", len(meshes))


if __name__ == "__main__":
    main()
