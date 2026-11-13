"""Cria o espantalho e a carroça carregada de feno, com variantes de fogo.

Os GLBs são as miniaturas de runtime; PNGs transparentes atendem ao editor e
ao tabuleiro 2D. O blend da carroça mantém todos os estágios na mesma cena,
alinhados ao modelo existente da carroça.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)
random.seed(20261030)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                       bpy.data.cameras, bpy.data.lights):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def mat(name, color, roughness=0.78, metallic=0.0, emission=None):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission:
        color_socket = bsdf.inputs.get("Emission Color") or bsdf.inputs.get("Emission")
        strength_socket = bsdf.inputs.get("Emission Strength")
        if color_socket:
            color_socket.default_value = (*emission[0], 1.0)
        if strength_socket:
            strength_socket.default_value = emission[1]
    return material


def finish_mesh(name, verts, faces, material, smooth=False):
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    if smooth:
        for poly in mesh.polygons:
            poly.use_smooth = True
    return obj


def cube(name, location, dimensions, material, bevel=0.0, rotation=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    obj.rotation_euler[2] = rotation
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if material:
        obj.data.materials.append(material)
    if bevel:
        mod = obj.modifiers.new("Arestas macias", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        norm = obj.modifiers.new("Normais", "WEIGHTED_NORMAL")
        bpy.ops.object.modifier_apply(modifier=norm.name)
    return obj


def uv_sphere(name, location, scale, material, segments=20, rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                        radius=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def cylinder(name, a, b, radius, material, vertices=10, radius_top=None):
    start, end = Vector(a), Vector(b)
    direction = end - start
    if radius_top is None or abs(radius_top - radius) < 1e-6:
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                            depth=direction.length,
                                            location=(start + end) / 2)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius,
                                        radius2=radius_top, depth=direction.length,
                                        location=(start + end) / 2)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(material)
    return obj


def curve_line(name, points, material, radius=0.008, resolution=2):
    curve = bpy.data.curves.new(name + " Curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = radius
    curve.bevel_resolution = resolution
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, co in zip(spline.points, points):
        point.co = (*co, 1.0)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.object
    obj.data.materials.clear()
    obj.data.materials.append(material)
    return obj


def flame(name, center, width, height, material, lean=0.0):
    """Chama baixa facetada, com base larga e ponta inclinada."""
    x, y, z = center
    rings = ((0.00, 0.42), (0.20, 0.50), (0.48, 0.33), (0.72, 0.21), (0.90, 0.11))
    sides = 7
    verts, faces = [], []
    for ri, (h, radius) in enumerate(rings):
        cx = x + lean * h
        cy = y + math.sin(ri * 0.8) * width * 0.08
        for i in range(sides):
            angle = math.tau * i / sides
            wobble = 1 + 0.10 * math.sin(i * 3 + ri)
            verts.append((cx + math.cos(angle) * width * radius * wobble,
                          cy + math.sin(angle) * width * radius * wobble,
                          z + height * h))
    for ri in range(len(rings) - 1):
        for i in range(sides):
            a = ri * sides + i
            b = ri * sides + (i + 1) % sides
            faces.append((a, b, b + sides, a + sides))
    tip = len(verts)
    verts.append((x + lean * height, y, z + height))
    base = (len(rings) - 1) * sides
    for i in range(sides):
        faces.append((base + i, base + (i + 1) % sides, tip))
    return finish_mesh(name, verts, faces, material, smooth=True)


def make_camera_lights(target, distance, ortho_scale):
    scene = bpy.context.scene
    bpy.ops.object.camera_add(location=(target[0] + distance,
                                        target[1] - distance * 1.35,
                                        target[2] + distance * 0.90))
    camera = bpy.context.object
    camera.name = "Câmera de miniatura"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = ortho_scale
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera
    for name, loc, power, size, color in (
        ("Luz quente", (target[0] + 2.8, target[1] - 3.2, target[2] + 4.2), 420, 3.0, (1.0, 0.83, 0.61)),
        ("Luz de preenchimento", (target[0] - 3.5, target[1] - 1.0, target[2] + 2.3), 240, 3.5, (0.78, 0.86, 1.0)),
        ("Luz de recorte", (target[0] + 0.4, target[1] + 3.0, target[2] + 3.3), 300, 2.5, (1.0, 0.64, 0.34)),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        light = bpy.context.object
        light.name = name
        light.data.energy = power
        light.data.shape = "DISK"
        light.data.size = size
        light.data.color = color
        light.rotation_euler = (Vector(target) - light.location).to_track_quat("-Z", "Y").to_euler()


def render_png(path):
    scene = bpy.context.scene
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def export_glb(path, export_objects):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in export_objects:
        if obj and obj.name in bpy.context.scene.objects:
            obj.select_set(True)
    if not export_objects:
        raise RuntimeError(f"Nenhuma malha selecionada para {path.name}")
    bpy.context.view_layer.objects.active = export_objects[0]
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB",
                              use_selection=True, export_apply=True,
                              export_yup=True, export_materials="EXPORT")


def setup_render():
    scene = bpy.context.scene
    # O Blender instalado neste workspace expõe EEVEE com o identificador
    # BLENDER_EEVEE (o sufixo NEXT não existe nesta build 5.1.2).
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.world.color = (0.08, 0.08, 0.08)
    scene.render.image_settings.color_depth = "8"


def save_blend(path):
    bpy.ops.wm.save_as_mainfile(filepath=str(path))


def build_espantalho():
    clear_scene()
    wood = mat("Madeira gasta", (0.25, 0.12, 0.055))
    wood_light = mat("Madeira clara", (0.42, 0.25, 0.11))
    burlap = mat("Saco de estopa", (0.47, 0.34, 0.20))
    burlap_light = mat("Costura de estopa", (0.69, 0.53, 0.31))
    shirt = mat("Camisa azul desbotada", (0.30, 0.37, 0.42))
    patch = mat("Remendo ocre", (0.58, 0.36, 0.13))
    trousers = mat("Calça castanha", (0.29, 0.20, 0.13))
    hat = mat("Chapéu de palha escura", (0.31, 0.22, 0.10))
    straw = mat("Palha dourada", (0.70, 0.49, 0.17))
    eyes = mat("Olhos de botão", (0.035, 0.025, 0.018), roughness=0.36)

    # Poste fincado e travessa de madeira, ambos centrados no footprint.
    cylinder("Estaca central", (0.0, 0.02, 0.0), (0.0, 0.02, 1.16), 0.052, wood, 8, 0.035)
    cylinder("Travessa dos braços", (-0.43, 0.02, 0.79), (0.43, 0.02, 0.79), 0.037, wood_light, 8)
    cylinder("Braço esquerdo de palha", (-0.46, 0.02, 0.79), (-0.58, 0.02, 0.86), 0.055, straw, 8, 0.018)
    cylinder("Braço direito de palha", (0.46, 0.02, 0.79), (0.58, 0.02, 0.86), 0.055, straw, 8, 0.018)

    # Roupa folgada e remendada sobre a armação.
    cube("Corpo da camisa", (0.0, 0.015, 0.61), (0.52, 0.25, 0.44), shirt, bevel=0.08)
    cube("Remendo da camisa", (-0.14, -0.119, 0.57), (0.13, 0.014, 0.12), patch, bevel=0.018)
    cube("Remendo lateral", (0.24, 0.016, 0.68), (0.016, 0.12, 0.10), burlap_light, bevel=0.012)
    # Duas pernas de pano pendem separadas e deixam a estrutura fácil de ler.
    cube("Perna esquerda", (-0.13, 0.02, 0.31), (0.19, 0.20, 0.26), trousers, bevel=0.045, rotation=-0.10)
    cube("Perna direita", (0.13, 0.02, 0.31), (0.19, 0.20, 0.26), trousers, bevel=0.045, rotation=0.10)
    cube("Pé esquerdo de palha", (-0.15, -0.015, 0.17), (0.25, 0.27, 0.08), straw, bevel=0.032, rotation=-0.12)
    cube("Pé direito de palha", (0.15, -0.015, 0.17), (0.25, 0.27, 0.08), straw, bevel=0.032, rotation=0.12)

    # Cabeça de saco com costuras, olhos de botão e chapéu gasto.
    uv_sphere("Cabeça de estopa", (0.0, -0.025, 1.00), (0.19, 0.17, 0.19), burlap, 20, 14)
    for x in (-0.065, 0.065):
        uv_sphere("Botão do rosto", (x, -0.179, 1.025), (0.022, 0.012, 0.027), eyes, 12, 8)
    curve_line("Boca costurada", [(-0.055, -0.184, 0.955), (-0.025, -0.19, 0.948),
                                  (0.015, -0.19, 0.948), (0.055, -0.184, 0.955)], burlap_light, 0.008)
    curve_line("Costura vertical", [(0.0, -0.19, 0.88), (0.0, -0.19, 0.92),
                                    (0.0, -0.19, 0.96)], burlap_light, 0.006)
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.27, depth=0.045,
                                        location=(0.0, -0.01, 1.17))
    brim = bpy.context.object
    brim.name = "Aba do chapéu"
    brim.data.materials.append(hat)
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.18, radius2=0.10, depth=0.16,
                                    location=(0.0, 0.0, 1.27))
    crown = bpy.context.object
    crown.name = "Copa do chapéu"
    crown.data.materials.append(hat)

    # Feixes irregulares saem das mangas e da cabeça sem alargar o objeto além de 1 casa.
    for i in range(18):
        side = -1 if i % 2 else 1
        z = 0.74 + (i % 5) * 0.035
        cylinder(f"Haste de palha {i:02d}",
                 (side * 0.46, -0.01, z), (side * (0.57 + random.random() * 0.05), -0.01, z + random.uniform(-0.035, 0.055)),
                 0.012, straw, 5, 0.002)
    for i in range(10):
        a = math.tau * i / 10
        cylinder(f"Palha da cabeça {i:02d}",
                 (0.15 * math.cos(a), 0.015 + 0.14 * math.sin(a), 0.99),
                 (0.22 * math.cos(a), 0.015 + 0.21 * math.sin(a), 1.00 + 0.035 * math.sin(i * 1.2)),
                 0.012, straw, 5, 0.002)

    setup_render()
    make_camera_lights((0.0, 0.0, 0.68), 3.0, 1.75)
    render_png(OUT / "espantalho.png")
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    export_glb(OUT / "espantalho.glb", meshes)
    save_blend(OUT / "espantalho.blend")


def create_bale(name, center, size, rotation, hay, twine, straw_light):
    x, y, z = center
    sx, sy, sz = size
    body = cube(name, center, size, hay, bevel=min(0.075, min(size) * 0.16), rotation=rotation)
    exported = [body]
    # Duas amarrações visíveis contornam cada fardo, em corda escura.
    for offset in (-0.22, 0.22):
        cx = x + math.cos(rotation) * offset
        cy = y + math.sin(rotation) * offset
        cord = cube(name + " | amarra", (cx, cy, z + sz * 0.02),
                    (0.027, sy + 0.045, sz + 0.045), twine,
                    bevel=0.010, rotation=rotation)
        exported.append(cord)
    # Fibras curtas no topo para quebrar a superfície lisa dos fardos.
    for i in range(14):
        lx = random.uniform(-sx * 0.42, sx * 0.42)
        ly = random.uniform(-sy * 0.40, sy * 0.40)
        start = (x + lx, y + ly, z + sz * 0.50)
        end = (start[0] + random.uniform(-0.035, 0.035),
               start[1] + random.uniform(-0.035, 0.035),
               start[2] + random.uniform(0.008, 0.030))
        exported.append(cylinder(name + " | fibra", start, end, 0.007,
                                 straw_light, 5, 0.0015))
    return exported


def build_carroca_feno():
    clear_scene()
    setup_render()
    bpy.ops.import_scene.gltf(filepath=str(OUT / "carroca.glb"))
    cart_meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not cart_meshes:
        raise RuntimeError("A miniatura carroca.glb não contém malhas")
    for obj in cart_meshes:
        obj.name = "Carroça original | " + obj.name

    hay = mat("Feno seco", (0.54, 0.37, 0.16), roughness=0.97)
    hay_light = mat("Fibras douradas", (0.72, 0.52, 0.23), roughness=0.95)
    hay_shadow = mat("Feno sombreado", (0.37, 0.24, 0.09), roughness=0.98)
    twine = mat("Cordão de fardo", (0.22, 0.14, 0.07), roughness=0.88)
    flame_outer = mat("Fogo laranja", (0.95, 0.18, 0.025), roughness=0.42,
                      emission=((1.0, 0.12, 0.01), 2.0))
    flame_mid = mat("Fogo dourado", (1.0, 0.48, 0.025), roughness=0.38,
                    emission=((1.0, 0.30, 0.01), 2.8))
    flame_inner = mat("Núcleo amarelo", (1.0, 0.79, 0.16), roughness=0.32,
                      emission=((1.0, 0.64, 0.05), 3.0))

    # A cama da carroça é central e aberta; os fardos formam uma carga baixa.
    hay_objects = []
    hay_objects += create_bale("Fardo central", (0.02, 0.00, 0.25), (0.75, 0.39, 0.34), 0.04,
                                hay, twine, hay_light)
    hay_objects += create_bale("Fardo traseiro", (-0.28, 0.02, 0.30), (0.55, 0.34, 0.36), -0.10,
                                hay_shadow, twine, hay_light)
    hay_objects += create_bale("Fardo frontal", (0.34, 0.02, 0.30), (0.52, 0.35, 0.36), 0.08,
                                hay, twine, hay_light)

    stage1, stage2 = [], []
    # Rodadas 1–2: pequenas chamas somente na carga de feno.
    for i, (x, y, width, height, lean) in enumerate((
        (-0.38, -0.12, 0.11, 0.36, -0.10), (-0.08, 0.05, 0.12, 0.42, 0.07),
        (0.23, -0.07, 0.10, 0.32, 0.10), (0.43, 0.08, 0.09, 0.28, -0.06),
    )):
        stage1.append(flame(f"Fogo no feno {i+1}", (x, y, 0.39), width, height,
                            flame_outer if i % 2 == 0 else flame_mid, lean))
        stage1.append(flame(f"Núcleo do feno {i+1}", (x, y - 0.01, 0.40), width * 0.42,
                            height * 0.64, flame_inner, lean * 0.7))
    # Rodadas 3–4: o fogo sobe pelas rodas, laterais e fardos, mantendo o GLB dentro do 2×2.
    full_flames = (
        (-0.80, -0.23, 0.15, 0.76, -0.11), (-0.52, 0.26, 0.13, 0.94, 0.09),
        (-0.12, -0.32, 0.16, 0.82, -0.08), (0.26, 0.29, 0.15, 1.02, 0.08),
        (0.65, -0.18, 0.14, 0.90, 0.13), (0.79, 0.20, 0.12, 0.64, -0.12),
        (-0.70, 0.02, 0.12, 0.58, 0.08), (0.02, 0.34, 0.12, 0.70, -0.09),
    )
    for i, (x, y, width, height, lean) in enumerate(full_flames):
        outer = flame_outer if i % 2 == 0 else flame_mid
        stage2.append(flame(f"Chama total {i+1}", (x, y, -0.08), width, height, outer, lean))
        if i % 2 == 0:
            stage2.append(flame(f"Núcleo total {i+1}", (x, y - 0.01, -0.045), width * 0.42,
                                height * 0.62, flame_inner, lean * 0.7))

    make_camera_lights((0.0, 0.0, 0.28), 4.2, 2.75)
    # A orientação segue o modelo da carroça; stage bounds mantêm o mesmo footprint.
    all_base = cart_meshes + hay_objects
    for obj in stage1 + stage2:
        obj.hide_render = True
        obj.hide_set(True)
    render_png(OUT / "carroca_feno.png")
    export_glb(OUT / "carroca_feno.glb", all_base)

    for obj in stage1:
        obj.hide_render = False
        obj.hide_set(False)
    render_png(OUT / "carroca_feno_feno_fogo.png")
    export_glb(OUT / "carroca_feno_feno_fogo.glb", all_base + stage1)

    for obj in stage1:
        obj.hide_render = True
        obj.hide_set(True)
    for obj in stage2:
        obj.hide_render = False
        obj.hide_set(False)
    render_png(OUT / "carroca_feno_chamas_total.png")
    export_glb(OUT / "carroca_feno_chamas_total.glb", all_base + stage2)

    # Salva a cena com o estado neutro visível; as duas coleções de fogo ficam
    # disponíveis no blend e podem ser revisadas ou ajustadas sem reimportar o GLB.
    for obj in stage2:
        obj.hide_render = True
        obj.hide_set(True)
    for obj in stage1:
        obj.hide_render = True
        obj.hide_set(True)
    save_blend(OUT / "carroca_feno.blend")


if __name__ == "__main__":
    build_espantalho()
    build_carroca_feno()
    print("DECOR_ASSETS", OUT / "espantalho.glb", OUT / "carroca_feno.glb")
