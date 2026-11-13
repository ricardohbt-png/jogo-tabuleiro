"""Cria a miniatura 3D do quartel medieval para o editor de mapas."""
from pathlib import Path
import math
import random

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)


def material(name, color, roughness=0.82, metallic=0.0):
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


def cube(name, loc, dims, mat, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, mat)
    if bevel:
        mod = obj.modifiers.new("Madeira e pedra gastas", "BEVEL")
        mod.width = bevel
        mod.segments = 1
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        mod = obj.modifiers.new("Normais ponderadas", "WEIGHTED_NORMAL")
        bpy.ops.object.modifier_apply(modifier=mod.name)
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


def gable(name, center_x, center_y, base_z, half_width, height, depth, mat):
    verts = [
        (center_x - half_width, center_y - depth / 2, base_z),
        (center_x + half_width, center_y - depth / 2, base_z),
        (center_x, center_y - depth / 2, base_z + height),
        (center_x - half_width, center_y + depth / 2, base_z),
        (center_x + half_width, center_y + depth / 2, base_z),
        (center_x, center_y + depth / 2, base_z + height),
    ]
    faces = [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
    mesh = bpy.data.meshes.new(name + " malha")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def make_barracks():
    stone = material("Pedra escura do quartel", (0.19, 0.18, 0.16))
    stone_light = material("Pedra gasta nas quinas", (0.29, 0.27, 0.23))
    stone_dark = material("Pedra enegrecida da base", (0.105, 0.10, 0.09))
    masonry = [
        material("Alvenaria | carvão", (0.12, 0.12, 0.115)),
        material("Alvenaria | ardósia", (0.16, 0.16, 0.15)),
        material("Alvenaria | cinza antigo", (0.21, 0.20, 0.18)),
        material("Alvenaria | pedra gasta", (0.26, 0.24, 0.21)),
    ]
    timber = material("Vigas de carvalho escuro", (0.20, 0.115, 0.06))
    timber_light = material("Tábuas antigas", (0.34, 0.22, 0.12))
    timber_mid = material("Madeira de porta", (0.27, 0.17, 0.09))
    plaster = material("Reboco ocre envelhecido", (0.39, 0.31, 0.22))
    roof = material("Telhas escuras", (0.085, 0.07, 0.055))
    roof_alt = material("Telhas gastas", (0.15, 0.12, 0.09))
    iron = material("Ferro forjado", (0.16, 0.16, 0.15), 0.4, 0.65)
    red = material("Bandeira vermelho escuro", (0.40, 0.065, 0.035))
    red_light = material("Emblema vermelho gasto", (0.64, 0.15, 0.055))
    shield_wood = material("Escudos de madeira", (0.40, 0.26, 0.13))
    shield_metal = material("Bordas dos escudos", (0.50, 0.39, 0.23), 0.5, 0.45)

    # Base e construção cabem no footprint de 3x3 casas.
    cube("Soleira de pedra", (0, 0, 0.14), (2.88, 2.84, 0.28), stone_dark, 0.04)
    cube("Piso elevado", (0, 0, 0.30), (2.76, 2.70, 0.12), stone_light, 0.025)
    for i in range(3):
        cube("Degrau do quartel %d" % i, (0, -1.40 + i * 0.15, 0.11 + i * 0.065),
             (1.15 + i * 0.10, 0.22, 0.14), stone_light, 0.018)

    # Salão inferior de pedra, reforçado por pilastras e vigas de madeira.
    cube("Salão de pedra", (0, 0.10, 1.18), (2.40, 2.24, 1.72), stone, 0.03)
    for x in (-1.09, 1.09):
        cube("Pilastra frontal", (x, -1.055, 1.12), (0.18, 0.15, 1.56), stone_light, 0.02)
        cube("Viga frontal", (x, -1.14, 1.24), (0.105, 0.06, 1.50), timber, 0.012)
    for z in (0.63, 1.84):
        cube("Viga atravessada da fachada", (0, -1.14, z), (2.29, 0.07, 0.10), timber, 0.012)

    # Porta dupla robusta com ferragens e verga de pedra.
    cube("Entrada escura", (0, -1.035, 1.00), (0.90, 0.06, 1.30), stone_dark)
    for x in (-0.48, 0.48):
        cube("Ombreira de pedra", (x, -1.15, 0.99), (0.15, 0.20, 1.30), stone_light, 0.015)
    cube("Folha esquerda da porta", (-0.215, -1.10, 0.88), (0.40, 0.075, 1.05), timber_mid, 0.015)
    cube("Folha direita da porta", (0.215, -1.10, 0.88), (0.40, 0.075, 1.05), timber_mid, 0.015)
    for x in (-0.34, -0.09, 0.09, 0.34):
        cube("Tábua da porta", (x, -1.145, 0.88), (0.035, 0.025, 0.98), timber_light)
    for z in (0.60, 1.18):
        cube("Travessa de ferro da porta", (0, -1.17, z), (0.79, 0.035, 0.07), iron)
    for x in (-0.075, 0.075):
        cube("Puxador de ferro", (x, -1.20, 0.93), (0.035, 0.025, 0.10), shield_metal, 0.01)

    # Janelas protegidas por grades no térreo e venezianas de madeira no alto.
    for x in (-0.78, 0.78):
        cube("Janela térrea | sombra", (x, -1.075, 1.48), (0.29, 0.055, 0.43), stone_dark)
        cube("Janela térrea | lintel", (x, -1.15, 1.72), (0.38, 0.13, 0.07), stone_light)
        for gx in (x - 0.075, x, x + 0.075):
            rod("Grade de ferro da janela", (gx, -1.17, 1.29), (gx, -1.17, 1.65), 0.018, iron, 6)
    for side in (-1, 1):
        for y in (-0.38, 0.52, 1.13):
            x = side * 1.215
            cube("Janela lateral | moldura", (x, y, 1.46), (0.07, 0.25, 0.42), timber)
            cube("Janela lateral | vidro escuro", (x + side * 0.04, y, 1.46),
                 (0.025, 0.16, 0.30), stone_dark)
            for z in (1.34, 1.46, 1.58):
                cube("Veneziana lateral", (x + side * 0.055, y, z), (0.035, 0.19, 0.025), timber_light)

    # Blocos de alvenaria irregulares no térreo; aberturas e vigas ficam expostas.
    rng = random.Random(41)
    for row, z in enumerate((0.47, 0.77, 1.07, 1.37, 1.67, 1.96)):
        x = -1.00 + (0.15 if row % 2 else 0.0)
        while x < 1.02:
            width = rng.uniform(0.26, 0.39)
            center = x + width / 2
            near_door = abs(center) < 0.52 and z < 1.72
            near_window = any(abs(center - wx) < 0.23 and 1.24 < z < 1.82 for wx in (-0.78, 0.78))
            if not near_door and not near_window and z < 2.03:
                cube("Pedra frontal irregular", (center, -1.052, z),
                     (width, 0.055, rng.uniform(0.21, 0.26)), rng.choice(masonry), 0.012)
            x += width + rng.uniform(0.025, 0.05)
    for side in (-1, 1):
        for row, z in enumerate((0.48, 0.80, 1.12, 1.44, 1.76, 1.98)):
            y = -0.84 + (0.14 if row % 2 else 0.0)
            while y < 1.17:
                length = rng.uniform(0.27, 0.38)
                center = y + length / 2
                near_window = any(abs(center - wy) < 0.20 and 1.23 < z < 1.78
                                  for wy in (-0.38, 0.52, 1.13))
                if not near_window:
                    cube("Pedra lateral irregular", (side * 1.224, center, z),
                         (0.055, length, rng.uniform(0.22, 0.26)), rng.choice(masonry), 0.012)
                y += length + rng.uniform(0.025, 0.05)

    # Mezanino de alojamento em estrutura de carvalho e reboco gasto.
    cube("Pavimento superior em enxaimel", (0, 0.12, 2.43), (2.26, 2.12, 0.93), plaster, 0.02)
    for x in (-1.04, -0.36, 0.36, 1.04):
        cube("Montante do enxaimel", (x, -0.975, 2.43), (0.095, 0.075, 0.93), timber, 0.01)
    for z in (1.99, 2.84):
        cube("Travessa do enxaimel", (0, -0.98, z), (2.32, 0.08, 0.095), timber, 0.01)
    # Duas janelas com veneziana no andar dos soldados.
    for x in (-0.70, 0.70):
        cube("Janela superior | sombra", (x, -1.035, 2.47), (0.34, 0.05, 0.43), stone_dark)
        for sx in (-0.17, 0.17):
            cube("Veneziana superior", (x + sx, -1.085, 2.47), (0.07, 0.06, 0.42), timber_light, 0.01)
        for z in (2.30, 2.47, 2.64):
            cube("Ripa da veneziana", (x, -1.12, z), (0.31, 0.045, 0.035), timber)
    for x in (-0.97, 0.97):
        rod("Mão francesa do beiral", (x, -1.04, 2.79), (x, -1.04, 3.14), 0.035, timber_light, 6)

    # Frontão triangular acima do enxaimel, encaixado sob o telhado.
    gable("Frontão de madeira e reboco", 0, -1.30, 2.78, 1.18, 1.13, 0.08, plaster)
    for x in (-0.92, 0.92):
        rod("Viga inclinada do frontão", (x, -1.36, 2.83), (0, -1.36, 3.88),
            0.045, timber, 7)

    # Telhado de duas águas, com telhas sobrepostas em tons terrosos escuros.
    for side in (-1, 1):
        angle = math.radians(47) * side
        panel = cube("Água do telhado", (side * 0.67, 0.12, 3.32),
                     (1.86, 2.72, 0.15), roof, 0.02)
        panel.rotation_euler[1] = angle
        for row in range(4):
            y = -0.90 + row * 0.69
            for col in range(3):
                x_abs = 0.20 + col * 0.42
                tile = cube("Telha irregular", (side * x_abs, y, 3.89 - x_abs * 0.96),
                            (0.39, 0.46, 0.05), roof_alt if (row + col) % 3 == 0 else roof, 0.012)
                tile.rotation_euler[1] = angle
        cube("Beiral de madeira", (side * 1.31, 0.12, 2.70), (0.12, 2.91, 0.14), timber, 0.02)
    cube("Cumeeira", (0, 0.12, 3.97), (0.13, 2.90, 0.13), timber_light, 0.02)

    # O escudo com armas cruzadas e a bandeira identificam o uso militar.
    cube("Placa de madeira sobre a entrada", (0, -1.20, 1.86), (0.48, 0.09, 0.18), timber, 0.025)
    # Escudo frontal simplificado: placa facetada, aro metálico e emblema.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=1,
                                        location=(0, -1.255, 2.34))
    shield = bpy.context.object
    shield.name = "Escudo do quartel"
    shield.scale = (0.27, 0.07, 0.34)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(shield, shield_wood)
    for x in (-0.18, 0.18):
        rod("Espada cruzada no brasão", (x, -1.34, 2.18), (-x, -1.34, 2.50), 0.018, shield_metal, 6)
        rod("Guarda da espada no brasão", (x - 0.035, -1.34, 2.31), (x + 0.035, -1.34, 2.37), 0.014, shield_metal, 6)
    # Mastro fixado na frente do frontão para a bandeira ficar livre do telhado.
    rod("Mastro da bandeira", (1.30, -1.39, 2.62), (1.30, -1.39, 3.78), 0.028, timber_light, 8)
    for z in (2.76, 3.46):
        rod("Suporte preso à fachada", (1.16, -1.04, z), (1.30, -1.39, z),
            0.026, timber, 7)
    # Bandeirola em tecido com cauda em V, pendente na fachada.
    verts = [
        (0.86, -1.42, 3.61), (1.30, -1.42, 3.61),
        (1.30, -1.42, 2.95), (1.08, -1.42, 3.12), (0.86, -1.42, 2.95),
        (0.86, -1.37, 3.61), (1.30, -1.37, 3.61),
        (1.30, -1.37, 2.95), (1.08, -1.37, 3.12), (0.86, -1.37, 2.95),
    ]
    mesh = bpy.data.meshes.new("Bandeira do quartel malha")
    mesh.from_pydata(verts, [], [(0, 1, 2, 3, 4), (9, 8, 7, 6, 5)])
    mesh.materials.append(red)
    flag = bpy.data.objects.new("Bandeira vermelha do quartel", mesh)
    bpy.context.collection.objects.link(flag)
    rod("Faixa do estandarte", (0.86, -1.44, 3.30), (1.30, -1.44, 3.30), 0.026, red_light, 8)

    # Dois escudos de guarda e lanças junto à parede da entrada.
    for x in (-1.20, 1.20):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=8, radius=1,
                                            location=(x, -1.20, 0.90))
        obj = bpy.context.object
        obj.name = "Escudo de guarda"
        obj.scale = (0.15, 0.07, 0.22)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        assign(obj, shield_wood)
        rod("Faixa metálica do escudo", (x - 0.10, -1.275, 0.90),
            (x + 0.10, -1.275, 0.90), 0.012, shield_metal, 6)
    for x in (-1.31,):
        rod("Lança de guarda", (x, -1.30, 0.38), (x, -1.30, 1.82), 0.022, timber_light, 7)
        bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.065, radius2=0.0,
                                        depth=0.20, location=(x, -1.30, 1.91))
        tip = bpy.context.object
        tip.name = "Ponta de lança"
        tip.rotation_euler[1] = math.pi
        assign(tip, iron)

    # Chaminé simples na água posterior do telhado.
    cube("Chaminé de pedra", (0.78, 0.76, 3.72), (0.28, 0.32, 0.66), stone_light, 0.025)
    cube("Boca da chaminé", (0.78, 0.76, 4.06), (0.37, 0.39, 0.10), stone_dark, 0.02)


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    make_barracks()
    target = (0, 0, 2.10)
    bpy.ops.object.camera_add(location=(6.7, -9.2, 7.0))
    camera = bpy.context.object
    camera.name = "Câmera | miniatura isométrica"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 6.8
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
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.24
    lights = [
        ("Luz principal", (4.0, -6.0, 9.0), 1100, 5.0, (1.0, 0.84, 0.68)),
        ("Preenchimento", (-5.0, -1.5, 5.0), 650, 5.0, (0.72, 0.82, 1.0)),
        ("Recorte", (0.0, 5.0, 7.0), 850, 4.5, (1.0, 0.72, 0.48)),
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
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "quartel_medieval.blend"))
    scene.render.filepath = str(OUT / "quartel_medieval_preview.png")
    bpy.ops.render.render(write_still=True)
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.filepath = str(OUT / "quartel_medieval.png")
    bpy.ops.render.render(write_still=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT / "quartel_medieval.glb"),
                              export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True,
                              export_materials="EXPORT")
    print("ASSET_EXPORT quartel_medieval meshes=", len(meshes))


if __name__ == "__main__":
    main()
