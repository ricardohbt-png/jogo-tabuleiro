"""Cria a miniatura 3D do Templo de Alva e Luz para o editor."""
from pathlib import Path
import math

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def material(name, color, metallic=0.0, roughness=0.78):
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


def cube(name, loc, dims, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, mat)
    if bevel:
        mod = obj.modifiers.new("Quinas talhadas", "BEVEL")
        mod.width = bevel
        mod.segments = 1
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        norm = obj.modifiers.new("Normais de pedra", "WEIGHTED_NORMAL")
        bpy.ops.object.modifier_apply(modifier=norm.name)
    return obj


def cylinder(name, loc, radius, depth, mat, vertices=16, rotation=None,
             radius_top=None):
    if radius_top is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                            depth=depth, location=loc,
                                            rotation=rotation or (0, 0, 0))
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius,
                                        radius2=radius_top, depth=depth,
                                        location=loc, rotation=rotation or (0, 0, 0))
    obj = bpy.context.object
    obj.name = name
    assign(obj, mat)
    bevel = obj.modifiers.new("Arestas polidas", "BEVEL")
    bevel.width = min(radius * 0.08, 0.035)
    bevel.segments = 1
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    return obj


def sphere(name, loc, scale, mat, segments=20, rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                        radius=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, mat)
    for face in obj.data.polygons:
        face.use_smooth = False
    return obj


def rod(name, start, end, radius, mat, vertices=10):
    a, b = Vector(start), Vector(end)
    delta = b - a
    obj = cylinder(name, (a + b) * 0.5, radius, delta.length, mat, vertices)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = delta.to_track_quat("Z", "Y")
    return obj


def arch_ring(name, center_x, front_y, base_z, inner_r, outer_r, depth, mat):
    """Segmented stone arch surrounding the open central entrance."""
    segments = 16
    verts = []
    faces = []
    for y in (front_y, front_y + depth):
        for radius in (inner_r, outer_r):
            for i in range(segments + 1):
                angle = math.pi * i / segments
                verts.append((center_x + math.cos(angle) * radius,
                              y, base_z + math.sin(angle) * radius))
    layer = segments + 1
    for i in range(segments):
        a, b = i, i + 1
        c, d = layer + i + 1, layer + i
        faces.append((a, b, c, d))
        a2, b2, c2, d2 = 2 * layer + i, 2 * layer + i + 1, 3 * layer + i + 1, 3 * layer + i
        faces.append((a2, d2, c2, b2))
        faces.append((a, a2, b2, b))
        faces.append((d, c, c2, d2))
    mesh = bpy.data.meshes.new(name + " mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def make_temple():
    stone = material("Calcário marfim", (0.72, 0.67, 0.55))
    stone_light = material("Pedra clara das molduras", (0.89, 0.82, 0.66))
    stone_shadow = material("Pedra em sombra", (0.46, 0.42, 0.36))
    roof_blue = material("Azul profundo esmaltado", (0.035, 0.095, 0.30), 0.18, 0.48)
    gold = material("Ouro da cúpula", (0.83, 0.47, 0.075), 0.70, 0.29)
    gold_light = material("Ouro luminoso", (1.0, 0.70, 0.18), 0.52, 0.3)
    banner_blue = material("Tecido azul real", (0.055, 0.12, 0.43))
    banner_purple = material("Tecido violeta", (0.24, 0.075, 0.34))
    dark = material("Interior sombreado", (0.055, 0.045, 0.04))
    window_blue = material("Vitral azul", (0.06, 0.30, 0.55), 0.28, 0.35)

    # Plataforma escalonada: a projeção máxima cabe no footprint de seis casas.
    cube("Fundação quadrada", (0, 0, 0.16), (5.72, 5.72, 0.32), stone_shadow, 0.08)
    cube("Primeiro degrau", (0, 0, 0.34), (5.52, 5.52, 0.16), stone, 0.04)
    cube("Laje superior", (0, 0.49, 0.48), (4.85, 4.55, 0.20), stone_light, 0.035)
    # Escadaria frontal no lado -Y.
    for i in range(4):
        y = -2.72 + i * 0.29
        z = 0.11 + i * 0.11
        cube("Escadaria frontal | degrau %d" % i, (0, y, z),
             (2.65 + i * 0.27, 0.34, 0.22), stone_light if i % 2 == 0 else stone, 0.025)

    # Nave e volumes laterais; a faixa central da fachada fica aberta como entrada.
    cube("Nave | corpo posterior", (0, 0.88, 2.20), (4.12, 2.70, 3.28), stone, 0.045)
    cube("Nave | ala esquerda", (-1.72, -0.73, 1.86), (0.82, 1.58, 2.65), stone, 0.035)
    cube("Nave | ala direita", (1.72, -0.73, 1.86), (0.82, 1.58, 2.65), stone, 0.035)
    # Molduras em faixas claras sobre a fachada e as laterais.
    cube("Cornija frontal", (0, -1.56, 3.55), (4.45, 0.26, 0.20), stone_light, 0.035)
    cube("Cornija lateral", (0, 0.75, 3.72), (4.42, 2.95, 0.20), stone_light, 0.035)
    cube("Friso azul frontal", (0, -1.64, 3.78), (3.96, 0.075, 0.12), roof_blue, 0.015)

    # Pórtico recuado com arco real em volta de um vão escuro e profundo.
    front_y = -1.60
    cube("Portal | sombra interior", (0, -0.05, 1.77), (1.55, 0.08, 2.50), dark)
    for x in (-0.86, 0.86):
        cube("Portal | ombreira", (x, front_y, 1.68), (0.22, 0.42, 2.46), stone_light, 0.035)
        cylinder("Portal | base", (x, front_y - 0.015, 0.56), 0.18, 0.20, gold, 12)
        cylinder("Portal | capitel", (x, front_y - 0.015, 2.91), 0.20, 0.16, gold, 12)
    arch_ring("Portal | arco de pedra", 0, front_y - 0.21, 2.83, 0.87, 1.15,
              0.42, stone_light)
    # Medalhão central na chave do arco.
    sphere("Medalhão solar do portal", (0, front_y - 0.46, 2.85),
           (0.18, 0.07, 0.18), gold_light, 16, 10)

    # Colunas delgadas ornamentam a frente, sem bloquear a porta.
    for x in (-1.46, 1.46):
        for y in (-1.58, -0.42):
            cylinder("Coluna | base", (x, y, 0.72), 0.27, 0.24, stone_light, 12)
            cylinder("Coluna | fuste", (x, y, 1.80), 0.17, 1.94, stone_light, 12)
            for band_z in (1.02, 2.53):
                cylinder("Coluna | anel dourado", (x, y, band_z), 0.205, 0.075, gold, 12)
            cylinder("Coluna | capitel", (x, y, 2.87), 0.28, 0.23, stone_light, 12)

    # Vitral frontal alto com moldura dourada e lancetas nas paredes laterais.
    for x in (-1.70, 1.70):
        cube("Vitral lateral | moldura", (x, -1.17, 2.16), (0.39, 0.06, 0.80), gold)
        cube("Vitral lateral | azul", (x, -1.21, 2.16), (0.27, 0.035, 0.66), window_blue)
    for x in (-1.36, 1.36):
        for y in (0.26, 1.20):
            cube("Janela lateral | moldura", (x, y, 2.30), (0.07, 0.48, 0.86), gold)
            cube("Janela lateral | vitral", (x + (0.045 if x < 0 else -0.045), y, 2.30),
                 (0.035, 0.34, 0.70), window_blue)

    # Tambor octogonal e cúpula segmentada azul e dourada.
    cylinder("Tambor da cúpula", (0, 0.49, 4.04), 1.64, 0.62, stone_light, 12)
    cylinder("Tambor | aro inferior dourado", (0, 0.49, 3.78), 1.71, 0.10, gold, 16)
    cylinder("Tambor | aro superior", (0, 0.49, 4.33), 1.67, 0.10, gold_light, 16)
    sphere("Grande cúpula azul", (0, 0.49, 4.73), (1.57, 1.57, 1.25), roof_blue, 24, 16)
    # Gomos dourados sobem pela superfície como nervuras da cúpula.
    for i in range(12):
        angle = math.tau * i / 12
        px, py = math.cos(angle), math.sin(angle)
        points = []
        for j in range(1, 10):
            a = -math.pi / 2 + math.pi * j / 11
            radius = 1.57 * math.cos(a)
            z = 4.73 + 1.25 * math.sin(a)
            points.append((px * radius, 0.49 + py * radius, z))
        for j in range(len(points) - 1):
            rod("Cúpula | nervura dourada", points[j], points[j + 1], 0.027, gold_light, 8)
    cylinder("Lanterna da cúpula", (0, 0.49, 5.91), 0.42, 0.43, gold, 12)
    sphere("Coroamento da lanterna", (0, 0.49, 6.18), (0.48, 0.48, 0.24), gold_light, 16, 10)
    cylinder("Agulha dourada", (0, 0.49, 6.52), 0.045, 0.52, gold_light, 8)
    sphere("Ponta da agulha", (0, 0.49, 6.80), (0.12, 0.12, 0.15), gold_light, 12, 8)

    # Pequenas cúpulas de canto deixam o perfil da silhueta próximo da referência.
    for x in (-1.75, 1.75):
        for y in (-0.77, 1.82):
            cylinder("Pináculo | base", (x, y, 3.92), 0.34, 0.30, stone_light, 10)
            sphere("Pináculo | cúpula", (x, y, 4.20), (0.30, 0.30, 0.32), gold, 12, 8)
            cylinder("Pináculo | haste", (x, y, 4.52), 0.035, 0.36, gold_light, 8)

    # Bandeiras azuis e violetas nos dois lados da entrada.
    for i, x in enumerate((-2.12, 2.12)):
        y = -1.69
        rod("Estandarte | haste", (x, y, 2.95), (x, y, 4.18), 0.035, gold, 8)
        cloth = banner_blue if i == 0 else banner_purple
        cube("Estandarte | pano", (x, y - 0.025, 3.65), (0.43, 0.055, 0.88), cloth, 0.02)
        # Emblema solar simples em ouro, sem texto.
        sphere("Estandarte | sol", (x, y - 0.065, 3.77), (0.13, 0.035, 0.13), gold_light, 12, 8)
        for j in range(8):
            angle = math.tau * j / 8
            rod("Estandarte | raio", (x + math.cos(angle) * 0.07, y - 0.066, 3.77 + math.sin(angle) * 0.07),
                (x + math.cos(angle) * 0.13, y - 0.066, 3.77 + math.sin(angle) * 0.13),
                0.012, gold_light, 6)
        # Recorte triangular no fim da flâmula.
        cube("Estandarte | peso", (x, y - 0.02, 3.20), (0.42, 0.06, 0.12), cloth, 0.025)

    # Arcos e frisos geométricos na base da fachada.
    for x in (-2.06, 2.06):
        cube("Pilastra de canto", (x, -1.57, 2.10), (0.28, 0.30, 2.85), stone_light, 0.03)
        for z in (0.83, 3.35):
            cube("Pilastra | moldura dourada", (x, -1.75, z), (0.36, 0.035, 0.09), gold, 0.015)
    # Degraus centrais dourados no limiar.
    for i in range(3):
        cube("Limiar | faixa", (0, -1.72 + i * 0.09, 0.61 + i * 0.035),
             (1.65, 0.12, 0.06), gold if i == 0 else stone_light, 0.015)


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def main():
    clear_scene()
    make_temple()
    target = (0, 0, 3.45)
    bpy.ops.object.camera_add(location=(9.5, -13.5, 10.6))
    camera = bpy.context.object
    camera.name = "Câmera | miniatura isométrica"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 9.4
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
    lights = [
        ("Luz principal", (4.5, -7.0, 11.0), 1450, 6.0, (1.0, 0.84, 0.65)),
        ("Luz de preenchimento", (-5.0, -2.5, 7.0), 850, 6.5, (0.72, 0.82, 1.0)),
        ("Luz de recorte", (0.0, 6.0, 9.0), 1100, 5.0, (1.0, 0.70, 0.42)),
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
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "templo_alva_e_luz.blend"))
    scene.render.filepath = str(OUT / "templo_alva_e_luz_preview.png")
    bpy.ops.render.render(write_still=True)
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.filepath = str(OUT / "templo_alva_e_luz.png")
    bpy.ops.render.render(write_still=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT / "templo_alva_e_luz.glb"),
                              export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True,
                              export_materials="EXPORT")
    print("ASSET_EXPORT templo_alva_e_luz meshes=", len(meshes))


if __name__ == "__main__":
    main()
