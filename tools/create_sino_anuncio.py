"""Cria o sino municipal de anúncio em armação de madeira."""
from pathlib import Path
import math

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)


def material(name, color, metallic=0.0, roughness=0.7):
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
        mod = obj.modifiers.new("Madeira boleada", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        norm = obj.modifiers.new("Normais da estrutura", "WEIGHTED_NORMAL")
        bpy.ops.object.modifier_apply(modifier=norm.name)
    return obj


def cylinder(name, loc, radius, depth, mat, vertices=14,
             radius_top=None, rotation=None):
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
    bevel = obj.modifiers.new("Borda fundida", "BEVEL")
    bevel.width = min(radius * 0.06, 0.012)
    bevel.segments = 1
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    return obj


def sphere(name, loc, scale, mat, segments=12, rings=8):
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


def rod(name, start, end, radius, mat, vertices=8):
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


def torus(name, loc, major_radius, minor_radius, mat, rotation=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=major_radius,
                                     minor_radius=minor_radius,
                                     major_segments=16, minor_segments=6,
                                     location=loc, rotation=rotation or (0, 0, 0))
    obj = bpy.context.object
    obj.name = name
    assign(obj, mat)
    return obj


def roof_panel(name, vertices, mat):
    mesh = bpy.data.meshes.new(name + " mesh")
    mesh.from_pydata(vertices, [], [(0, 1, 2, 3)])
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def make_bell():
    wood = material("Carvalho envelhecido", (0.24, 0.105, 0.045))
    wood_light = material("Tábua clara", (0.42, 0.23, 0.09))
    wood_dark = material("Madeira nas sombras", (0.13, 0.055, 0.025))
    slate = material("Telhado de ardósia escura", (0.12, 0.16, 0.18), 0.12, 0.72)
    iron = material("Ferro forjado", (0.075, 0.085, 0.085), 0.78, 0.42)
    bronze = material("Bronze do sino", (0.52, 0.25, 0.065), 0.76, 0.32)
    bronze_light = material("Filete de bronze", (0.88, 0.55, 0.16), 0.62, 0.30)
    rope = material("Corda de cânhamo", (0.49, 0.31, 0.12))

    # Four square posts make an open belfry that fits within a single tile.
    for x in (-0.31, 0.31):
        for y in (-0.31, 0.31):
            cube("Estrutura | pilar", (x, y, 1.10), (0.13, 0.13, 2.12), wood, 0.018)
            cube("Estrutura | sapata", (x, y, 0.12), (0.21, 0.21, 0.16), wood_light, 0.02)
            cube("Estrutura | capitel", (x, y, 2.14), (0.19, 0.19, 0.13), bronze, 0.018)

    # Cross rails and diagonal braces stiffen the four-sided wooden frame.
    for z in (0.34, 1.83):
        for y in (-0.31, 0.31):
            cube("Estrutura | travessa frontal/traseira", (0, y, z),
                 (0.70, 0.105, 0.12), wood_light if z < 1 else wood, 0.016)
        for x in (-0.31, 0.31):
            cube("Estrutura | travessa lateral", (x, 0, z),
                 (0.105, 0.70, 0.12), wood_light if z < 1 else wood, 0.016)
    for xside in (-1, 1):
        for yside in (-1, 1):
            rod("Estrutura | escora", (xside * 0.30, yside * 0.30, 0.40),
                (xside * 0.30, yside * 0.10, 0.82), 0.035, wood_light, 6)

    # Compact gabled roof with wooden ridge and slate-coloured panels.
    roof_panel("Telhado | água esquerda", [
        (-0.45, -0.42, 2.23), (0, -0.42, 2.57),
        (0, 0.42, 2.57), (-0.45, 0.42, 2.23)], slate)
    roof_panel("Telhado | água direita", [
        (0, -0.42, 2.57), (0.45, -0.42, 2.23),
        (0.45, 0.42, 2.23), (0, 0.42, 2.57)], slate)
    rod("Telhado | cumeeira", (0, -0.46, 2.57), (0, 0.46, 2.57),
        0.055, wood_dark, 8)
    for y in (-0.34, 0, 0.34):
        rod("Telhado | ripa esquerda", (-0.40, y, 2.27), (0, y, 2.57),
            0.018, wood_light, 6)
        rod("Telhado | ripa direita", (0, y, 2.57), (0.40, y, 2.27),
            0.018, wood_light, 6)
    for x in (-0.44, 0.44):
        for y in (-0.37, 0.37):
            sphere("Telhado | rebite", (x, y, 2.25), (0.035, 0.035, 0.035), iron, 8, 6)

    # The bell hangs beneath the front eave so the nearest upright does not hide it.
    rod("Sino | braço de suspensão", (0, 0, 2.18), (0, -0.40, 2.18),
        0.04, wood_dark, 8)
    rod("Sino | gancho", (0, -0.40, 2.18), (0, -0.40, 1.95), 0.035, iron, 8)
    torus_rotation = (math.pi / 2, 0, 0)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.095, minor_radius=0.022,
                                     major_segments=14, minor_segments=6,
                                     location=(0, -0.40, 1.90), rotation=torus_rotation)
    assign(bpy.context.object, bronze_light).name = "Sino | argola de suspensão"
    cylinder("Sino | ombro", (0, -0.40, 1.76), 0.115, 0.14, bronze, 14,
             radius_top=0.085)
    cylinder("Sino | campana", (0, -0.40, 1.53), 0.245, 0.39, bronze, 16,
             radius_top=0.105)
    cylinder("Sino | boca reforçada", (0, -0.40, 1.34), 0.252, 0.06,
             bronze_light, 16)
    for z, radius in ((1.70, 0.122), (1.55, 0.19), (1.37, 0.248)):
        torus("Sino | anel torneado", (0, -0.40, z), radius, 0.018, bronze_light)
    sphere("Sino | medalhão frontal", (0, -0.637, 1.56),
           (0.065, 0.018, 0.075), bronze_light, 10, 8)
    sphere("Sino | miolo do medalhão", (0, -0.655, 1.56),
           (0.025, 0.012, 0.03), iron, 8, 6)

    # The clapper and long hemp pull-rope hang below the bell to hand height.
    rod("Sino | haste do badalo", (0, -0.40, 1.47), (0, -0.40, 1.14), 0.028, iron, 8)
    sphere("Sino | badalo", (0, -0.40, 1.10), (0.07, 0.07, 0.09), bronze, 10, 7)
    rod("Corda | fio principal", (0, -0.425, 1.10), (0, -0.425, 0.28),
        0.018, rope, 7)
    sphere("Corda | puxador", (0, -0.425, 0.25), (0.065, 0.065, 0.085),
           wood_light, 10, 7)
    cylinder("Corda | ferrule", (0, -0.425, 0.31), 0.032, 0.045, iron, 8)


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    make_bell()
    target = (0, 0, 1.30)
    bpy.ops.object.camera_add(location=(3.5, -4.6, 3.5))
    camera = bpy.context.object
    camera.name = "Câmera | sino municipal"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 3.25
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
        ("Luz principal", (3.3, -4.0, 5.2), 560, 3.0, (1.0, 0.84, 0.66)),
        ("Luz de preenchimento", (-3.1, -1.4, 3.3), 380, 2.8, (0.75, 0.84, 1.0)),
        ("Luz de recorte", (0.0, 4.0, 4.5), 420, 3.0, (1.0, 0.70, 0.42)),
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
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "sino_anuncio.blend"))
    scene.render.filepath = str(OUT / "sino_anuncio_preview.png")
    bpy.ops.render.render(write_still=True)
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.filepath = str(OUT / "sino_anuncio.png")
    bpy.ops.render.render(write_still=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    bpy.ops.export_scene.gltf(filepath=str(OUT / "sino_anuncio.glb"),
                              export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True,
                              export_materials="EXPORT")
    print("ASSET_EXPORT sino_anuncio source_meshes=", len(meshes), "glb_meshes=1")


if __name__ == "__main__":
    main()
