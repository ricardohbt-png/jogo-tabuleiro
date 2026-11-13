"""Cria a miniatura 3D da igreja rústica da Vila de Corvin."""
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
        mod = obj.modifiers.new("Arestas gastas", "BEVEL")
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


def gable(name, x_center, y_center, z_base, half_width, height, depth, mat):
    """Triangular gable wall extruded along Y, facing the camera at -Y."""
    verts = [
        (x_center - half_width, y_center - depth / 2, z_base),
        (x_center + half_width, y_center - depth / 2, z_base),
        (x_center, y_center - depth / 2, z_base + height),
        (x_center - half_width, y_center + depth / 2, z_base),
        (x_center + half_width, y_center + depth / 2, z_base),
        (x_center, y_center + depth / 2, z_base + height),
    ]
    faces = [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
    mesh = bpy.data.meshes.new(name + " malha")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def arch(name, center_x, y, z_base, inner_r, outer_r, depth, mat):
    segments = 12
    verts, faces = [], []
    for yy in (y, y + depth):
        for radius in (inner_r, outer_r):
            for i in range(segments + 1):
                angle = math.pi * i / segments
                verts.append((center_x + math.cos(angle) * radius, yy,
                              z_base + math.sin(angle) * radius))
    layer = segments + 1
    for i in range(segments):
        faces.extend([
            (i, i + 1, layer + i + 1, layer + i),
            (2 * layer + i, 3 * layer + i, 3 * layer + i + 1, 2 * layer + i + 1),
        ])
    mesh = bpy.data.meshes.new(name + " malha")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def make_church():
    stone = material("Pedra escurecida", (0.16, 0.155, 0.145))
    stone_light = material("Pedra gasta nas quinas", (0.25, 0.235, 0.215))
    stone_dark = material("Pedra enegrecida da fundação", (0.095, 0.09, 0.08))
    masonry = [
        material("Alvenaria | carvão", (0.105, 0.105, 0.10)),
        material("Alvenaria | ardósia", (0.14, 0.145, 0.145)),
        material("Alvenaria | cinza antigo", (0.18, 0.17, 0.155)),
        material("Alvenaria | pedra gasta", (0.22, 0.205, 0.18)),
    ]
    timber = material("Madeira escura envelhecida", (0.22, 0.12, 0.065))
    timber_light = material("Vigas de madeira", (0.34, 0.21, 0.11))
    plaster = material("Pedra escura sob as vigas", (0.17, 0.16, 0.145))
    roof = material("Telhas marrons quase negras", (0.075, 0.060, 0.048))
    roof_alt = material("Telhas gastas", (0.12, 0.095, 0.072))
    darkness = material("Interior escuro da entrada", (0.055, 0.045, 0.035))
    iron = material("Ferro da campana", (0.23, 0.22, 0.18), 0.42, 0.58)
    bronze = material("Bronze antigo", (0.38, 0.24, 0.09), 0.35, 0.62)
    glass = material("Vidro âmbar escuro", (0.25, 0.20, 0.12), 0.32, 0.12)

    # Base compacta no footprint de 3x3 casas.
    cube("Fundação de pedra", (0, 0, 0.13), (2.88, 2.82, 0.26), stone_dark, 0.045)
    cube("Piso elevado", (0, 0, 0.29), (2.76, 2.68, 0.12), stone_light, 0.025)
    for i in range(3):
        cube("Degrau da entrada %d" % i, (0, -1.39 + i * 0.15, 0.11 + i * 0.065),
             (1.05 + i * 0.12, 0.22, 0.14), stone_light, 0.018)

    # Nave de pedra com reforços de madeira e frontão triangular.
    cube("Nave de pedra", (0, 0.12, 1.17), (2.42, 2.28, 1.72), stone, 0.035)
    # O frontão é uma parede fina na fachada; as águas reais do telhado ficam
    # separadas e escuras para não parecerem uma cunha sólida sobre a entrada.
    gable("Frontão da nave", 0, -1.02, 2.03, 1.21, 0.86, 0.16, plaster)
    for x in (-1.08, 1.08):
        cube("Contraforte de canto", (x, -1.08, 1.05), (0.20, 0.22, 1.65), stone_light, 0.02)
        cube("Viga de canto", (x, -1.105, 1.23), (0.115, 0.065, 1.40), timber, 0.015)
    for z in (0.63, 1.82):
        cube("Viga horizontal da fachada", (0, -1.105, z), (2.30, 0.07, 0.10), timber, 0.012)

    # Porta funda e arcada de blocos, visível sob o campanário.
    cube("Vão escuro da igreja", (0, -1.105, 0.99), (0.68, 0.055, 1.27), darkness)
    for x in (-0.39, 0.39):
        cube("Ombreira da porta", (x, -1.16, 0.98), (0.12, 0.16, 1.26), stone_light, 0.012)
    arch("Arco de pedra da porta", 0, -1.245, 1.58, 0.39, 0.54, 0.16, stone_light)
    cube("Porta de tábuas", (0, -1.10, 0.76), (0.56, 0.04, 0.76), timber, 0.012)
    for x in (-0.18, 0, 0.18):
        cube("Tábua vertical da porta", (x, -1.131, 0.76), (0.025, 0.018, 0.71), timber_light)
    cube("Ferrolho", (0.19, -1.15, 0.80), (0.055, 0.025, 0.06), iron)

    # Janelas estreitas e pequenas aberturas laterais.
    for x in (-0.76, 0.76):
        cube("Janela frontal | moldura", (x, -1.13, 1.55), (0.30, 0.07, 0.53), timber)
        cube("Janela frontal | vidro", (x, -1.172, 1.55), (0.19, 0.025, 0.39), glass)
        cube("Janela frontal | travessa", (x, -1.19, 1.55), (0.22, 0.025, 0.035), timber_light)
    for side in (-1, 1):
        for y in (-0.36, 0.47, 1.08):
            x = side * 1.225
            cube("Janela lateral | moldura", (x, y, 1.46), (0.07, 0.25, 0.43), timber)
            cube("Janela lateral | vidro", (x + side * 0.04, y, 1.46), (0.025, 0.15, 0.31), glass)

    # Alvenaria irregular em relevo: tons próximos e quinas gastas dão textura
    # de pedra antiga sem cobrir a porta, as janelas ou as vigas aparentes.
    rng = random.Random(23)
    for row, z in enumerate((0.48, 0.77, 1.06, 1.35, 1.64, 1.93)):
        x = -1.00 + (0.16 if row % 2 else 0.0)
        while x < 1.02:
            width = rng.uniform(0.27, 0.39)
            center_x = x + width / 2
            protected_door = abs(center_x) < 0.48 and z < 1.83
            protected_window = any(abs(center_x - wx) < 0.20 and 1.26 < z < 1.83
                                   for wx in (-0.76, 0.76))
            if not protected_door and not protected_window and z < 2.0:
                cube("Bloco de pedra frontal", (center_x, -1.054, z),
                     (width, 0.055, rng.uniform(0.20, 0.255)),
                     rng.choice(masonry), 0.012)
            x += width + rng.uniform(0.025, 0.055)

    for side in (-1, 1):
        for row, z in enumerate((0.48, 0.78, 1.08, 1.38, 1.68, 1.94)):
            y = -0.88 + (0.15 if row % 2 else 0.0)
            while y < 1.17:
                length = rng.uniform(0.27, 0.38)
                center_y = y + length / 2
                at_window = any(abs(center_y - wy) < 0.19 and 1.22 < z < 1.78
                                for wy in (-0.36, 0.47, 1.08))
                if not at_window:
                    cube("Bloco de pedra lateral", (side * 1.224, center_y, z),
                         (0.055, length, rng.uniform(0.21, 0.26)),
                         rng.choice(masonry), 0.012)
                y += length + rng.uniform(0.025, 0.055)

    # Telhado de duas águas com beiral marcado e telhas em fiadas curtas.
    for side in (-1, 1):
        angle = math.radians(47) * side
        panel = cube("Água do telhado", (side * 0.69, 0.13, 2.66),
                     (1.88, 2.65, 0.16), roof, 0.025)
        panel.rotation_euler[1] = angle
        for row in range(4):
            y = -0.91 + row * 0.69
            for col in range(3):
                x = side * (0.22 + col * 0.43)
                z = 3.24 - (0.22 + col * 0.43) * 0.98
                tile = cube("Telha irregular", (x, y, z), (0.40, 0.47, 0.055),
                            roof_alt if (row + col) % 3 == 0 else roof, 0.018)
                tile.rotation_euler[1] = angle
        cube("Beiral escuro", (side * 1.34, 0.13, 2.05), (0.12, 2.84, 0.16), timber, 0.02)
    cube("Cumeeira", (0, 0.13, 3.34), (0.12, 2.82, 0.13), timber_light, 0.025)

    # Torre quadrada sobre a entrada, com campanário aberto sob telhado alto.
    cube("Base da torre", (0, -0.72, 2.63), (1.10, 1.02, 1.10), stone_light, 0.025)
    cube("Face frontal da torre", (0, -1.255, 2.69), (0.78, 0.075, 0.88), plaster, 0.015)
    for x in (-0.49, 0.49):
        cube("Pilar de canto da torre", (x, -0.78, 2.78), (0.12, 0.92, 1.18), timber, 0.012)
        cube("Pilar da torre na fachada", (x, -1.305, 2.73), (0.12, 0.07, 1.0), timber, 0.012)
    for z in (2.27, 3.15):
        cube("Travessa frontal da torre", (0, -1.31, z), (1.04, 0.07, 0.10), timber, 0.012)
    # Visor em arco acima da entrada da igreja.
    cube("Visor da torre", (0, -1.35, 2.82), (0.28, 0.025, 0.40), darkness)
    for x in (-0.19, 0.19):
        cube("Moldura do visor", (x, -1.372, 2.83), (0.055, 0.035, 0.46), timber_light)
    cube("Verga do visor", (0, -1.372, 3.06), (0.43, 0.035, 0.055), timber_light)

    # Vãos do campanário: a abertura e a campana ficam visíveis de frente.
    for x in (-0.54, 0.54):
        cube("Montante do campanário", (x, -0.82, 3.66), (0.13, 1.03, 0.93), timber, 0.012)
    for z in (3.23, 4.08):
        cube("Travessa do campanário", (0, -0.82, z), (1.12, 1.04, 0.12), timber_light, 0.012)
    cube("Viga de suspensão do sino", (0, -0.98, 3.89), (0.58, 0.08, 0.07), iron)
    rod("Alça do sino", (0, -0.99, 3.88), (0, -0.99, 3.72), 0.035, iron, 10)
    bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.22, radius2=0.105,
                                    depth=0.32, location=(0, -1.00, 3.55))
    bell = bpy.context.object
    bell.name = "Campana de bronze"
    assign(bell, bronze)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=1,
                                        location=(0, -1.00, 3.36))
    clapper = bpy.context.object
    clapper.name = "Badalo"
    clapper.scale = (0.045, 0.045, 0.07)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(clapper, iron)
    for y in (-1.30, -0.33):
        cube("Peitoril do campanário", (0, y, 3.25), (1.18, 0.12, 0.10), timber_light)

    # Torre termina num telhado piramidal escuro, com cruz simples.
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.83, radius2=0.03,
                                    depth=0.96, location=(0, -0.72, 4.59),
                                    rotation=(0, 0, math.radians(45)))
    cap = bpy.context.object
    cap.name = "Telhado piramidal da torre"
    assign(cap, roof)
    rod("Cruz da igreja | haste", (0, -0.72, 5.03), (0, -0.72, 5.45), 0.025, iron, 8)
    rod("Cruz da igreja | braço", (-0.15, -0.72, 5.31), (0.15, -0.72, 5.31), 0.022, iron, 8)


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    make_church()
    target = (0, 0, 2.52)
    bpy.ops.object.camera_add(location=(6.5, -8.7, 6.9))
    camera = bpy.context.object
    camera.name = "Câmera | miniatura isométrica"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 6.85
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
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "igreja_corvin.blend"))
    scene.render.filepath = str(OUT / "igreja_corvin_preview.png")
    bpy.ops.render.render(write_still=True)
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.filepath = str(OUT / "igreja_corvin.png")
    bpy.ops.render.render(write_still=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT / "igreja_corvin.glb"),
                              export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True,
                              export_materials="EXPORT")
    print("ASSET_EXPORT igreja_corvin meshes=", len(meshes))


if __name__ == "__main__":
    main()
