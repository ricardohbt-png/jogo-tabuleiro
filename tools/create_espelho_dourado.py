"""Cria o espelho dourado de parede em PNG, GLB e arquivo Blender editável."""
from pathlib import Path
import math

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)


def material(name, color, metallic=0.0, roughness=0.55):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def assign(obj, mat):
    obj.data.materials.append(mat)
    return obj


def sphere(name, loc, scale, mat, segments=16, rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                        radius=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, mat)
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def cube(name, loc, dims, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, mat)
    if bevel:
        mod = obj.modifiers.new("Bordas trabalhadas", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        norm = obj.modifiers.new("Normais polidas", "WEIGHTED_NORMAL")
        bpy.ops.object.modifier_apply(modifier=norm.name)
    return obj


def curve_ellipse(name, cx, cy, cz, rx, rz, thickness, mat, count=64):
    data = bpy.data.curves.new(name + " curve", "CURVE")
    data.dimensions = "3D"
    data.resolution_u = 2
    data.bevel_depth = thickness
    data.bevel_resolution = 3
    spline = data.splines.new("POLY")
    spline.points.add(count - 1)
    for i, point in enumerate(spline.points):
        angle = math.tau * i / count
        point.co = (cx + rx * math.cos(angle), cy,
                    cz + rz * math.sin(angle), 1)
    spline.use_cyclic_u = True
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    data.materials.append(mat)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    bpy.context.object.select_set(False)
    return bpy.context.object


def rod(name, start, end, radius, mat, vertices=10):
    a, b = Vector(start), Vector(end)
    delta = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                        depth=delta.length, location=(a + b) * 0.5)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = delta.to_track_quat("Z", "Y")
    assign(obj, mat)
    return obj


def add_leaf(name, x, z, angle, y, gold, highlight):
    leaf = sphere(name, (x, y, z), (0.07, 0.026, 0.13), gold, 12, 8)
    leaf.rotation_euler[1] = angle
    # The central rib catches a fine gold highlight on the room-facing side.
    dx, dz = math.sin(angle) * 0.085, math.cos(angle) * 0.085
    rod(name + " | nervura", (x - dx, y + 0.025, z - dz),
        (x + dx, y + 0.025, z + dz), 0.008, highlight, 6)


def make_mirror():
    gold = material("Ouro antigo da moldura", (0.60, 0.31, 0.065), 0.72, 0.34)
    gold_light = material("Filetes de ouro polido", (0.91, 0.66, 0.24), 0.62, 0.28)
    bronze = material("Sombra de bronze", (0.28, 0.12, 0.035), 0.70, 0.42)
    glass = material("Espelho de prata azulada", (0.30, 0.43, 0.52), 0.72, 0.16)
    reflection = material("Reflexo claro no espelho", (0.76, 0.84, 0.85), 0.48, 0.19)
    dark_reflection = material("Reflexo frio no espelho", (0.11, 0.22, 0.31), 0.52, 0.22)
    jewel = material("Jóia de lápis-lazúli", (0.025, 0.09, 0.35), 0.32, 0.25)

    # The back is -Y; the room-facing side is +Y (the wall GLB loader expects this).
    sphere("Espelho | placa traseira oval", (0, -0.015, 1.03),
           (0.60, 0.13, 0.85), bronze, 24, 16)
    sphere("Espelho | corpo da moldura", (0, 0.045, 1.03),
           (0.57, 0.14, 0.81), gold, 24, 16)
    sphere("Espelho | vidro convexo", (0, 0.152, 1.04),
           (0.425, 0.040, 0.665), glass, 24, 16)

    # Concentric oval ridges make a thick, polished carved frame.
    curve_ellipse("Moldura | aro externo dourado", 0, 0.075, 1.04,
                  0.59, 0.83, 0.073, gold_light)
    curve_ellipse("Moldura | friso de bronze", 0, 0.156, 1.04,
                  0.505, 0.744, 0.026, bronze)
    curve_ellipse("Moldura | filete interno", 0, 0.191, 1.04,
                  0.465, 0.704, 0.023, gold_light)
    curve_ellipse("Moldura | linha interna escura", 0, 0.195, 1.04,
                  0.437, 0.676, 0.010, bronze)

    # Elongated highlights suggest a real silvered mirror without text or scenery.
    streak = sphere("Reflexo | faixa de luz", (-0.14, 0.188, 1.11),
                    (0.042, 0.008, 0.45), reflection, 12, 8)
    streak.rotation_euler[1] = -0.18
    streak2 = sphere("Reflexo | luz curta", (0.16, 0.188, 0.79),
                     (0.023, 0.009, 0.23), dark_reflection, 12, 8)
    streak2.rotation_euler[1] = 0.16
    sphere("Reflexo | brilho oval", (-0.28, 0.187, 1.48),
           (0.045, 0.008, 0.060), reflection, 12, 8)

    # Repeated carved leaves follow both sides of the oval frame.
    for side in (-1, 1):
        for z, angle in ((0.52, -0.65), (0.78, -0.35), (1.04, 0),
                         (1.30, 0.35), (1.56, 0.65)):
            x = side * (0.49 if z in (1.04,) else 0.43)
            add_leaf("Moldura | folha lateral", x, z,
                     angle if side > 0 else -angle, 0.245, gold, gold_light)
    # Rosettes at the four compass points of the oval.
    for x, z in ((0, 1.88), (0, 0.20), (-0.585, 1.04), (0.585, 1.04)):
        sphere("Moldura | roseta", (x, 0.22, z), (0.105, 0.055, 0.105), gold_light, 12, 8)
        sphere("Moldura | centro da roseta", (x, 0.272, z), (0.040, 0.018, 0.040), bronze, 10, 6)

    # Baroque crest with a fleur-like finial and mirrored scrolls.
    sphere("Coroamento | medalhão", (0, 0.22, 1.99), (0.16, 0.07, 0.13), gold, 14, 8)
    sphere("Coroamento | gema azul", (0, 0.285, 2.00), (0.062, 0.025, 0.075), jewel, 12, 8)
    for side in (-1, 1):
        rod("Coroamento | haste curva", (0, 0.23, 1.98),
            (side * 0.22, 0.23, 2.15), 0.035, gold_light, 8)
        sphere("Coroamento | voluta", (side * 0.235, 0.23, 2.15),
               (0.075, 0.045, 0.075), gold, 12, 8)
        add_leaf("Coroamento | folha", side * 0.10, 2.12,
                 side * 0.48, 0.255, gold, gold_light)
    sphere("Coroamento | ponta", (0, 0.24, 2.24), (0.075, 0.06, 0.10), gold_light, 12, 8)

    # Small pendant and acanthus curls finish the lower point of the mirror.
    sphere("Base | gota de ouro", (0, 0.22, 0.095), (0.105, 0.06, 0.14), gold, 12, 8)
    sphere("Base | gema azul", (0, 0.278, 0.095), (0.045, 0.02, 0.065), jewel, 10, 8)
    for side in (-1, 1):
        rod("Base | ramo ornamental", (0, 0.23, 0.28),
            (side * 0.20, 0.23, 0.19), 0.026, gold_light, 8)
        sphere("Base | voluta", (side * 0.21, 0.23, 0.18),
               (0.055, 0.035, 0.05), gold, 10, 8)


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def combine_static(meshes):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    make_mirror()
    target = (0, 0.08, 1.13)
    bpy.ops.object.camera_add(location=(2.6, 4.8, 2.9))
    camera = bpy.context.object
    camera.name = "Câmera | espelho de parede"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 2.65
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
    for name, location, energy, size, color in (
        ("Luz principal", (2.7, 3.5, 4.0), 420, 2.4, (1.0, 0.83, 0.62)),
        ("Luz de preenchimento", (-2.5, 2.2, 2.1), 300, 2.0, (0.72, 0.84, 1.0)),
        ("Luz de recorte", (0, -2.0, 3.0), 230, 1.8, (1.0, 0.66, 0.35)),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.data.color = color
        point_at(light, target)

    meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "espelho_dourado.blend"))
    scene.render.filepath = str(OUT / "espelho_dourado_preview.png")
    bpy.ops.render.render(write_still=True)
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.filepath = str(OUT / "espelho_dourado.png")
    bpy.ops.render.render(write_still=True)
    combine_static(meshes)
    bpy.ops.export_scene.gltf(filepath=str(OUT / "espelho_dourado.glb"),
                              export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True,
                              export_materials="EXPORT")
    print("ASSET_EXPORT espelho_dourado materials=", len(meshes))


if __name__ == "__main__":
    main()
