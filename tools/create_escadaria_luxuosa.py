"""Cria a miniatura da escadaria luxuosa para as decorações."""
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


def cube(name, loc, dims, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, mat)
    if bevel:
        mod = obj.modifiers.new("Arestas lapidadas", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        norm = obj.modifiers.new("Normais suaves", "WEIGHTED_NORMAL")
        bpy.ops.object.modifier_apply(modifier=norm.name)
    return obj


def cylinder(name, loc, radius, depth, mat, vertices=12, radius_top=None):
    if radius_top is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                            depth=depth, location=loc)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius,
                                        radius2=radius_top, depth=depth,
                                        location=loc)
    obj = bpy.context.object
    obj.name = name
    assign(obj, mat)
    bevel = obj.modifiers.new("Borda polida", "BEVEL")
    bevel.width = min(radius * 0.08, 0.018)
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
    obj = cylinder(name, (a + b) * 0.5, radius, delta.length, mat, vertices)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = delta.to_track_quat("Z", "Y")
    return obj


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def make_staircase():
    marble = material("Mármore marfim", (0.72, 0.70, 0.64), 0.08, 0.3)
    marble_light = material("Mármore claro", (0.91, 0.88, 0.78), 0.05, 0.25)
    marble_shadow = material("Mármore nas laterais", (0.43, 0.40, 0.35), 0.06, 0.38)
    burgundy = material("Veludo vinho", (0.28, 0.012, 0.038), 0.0, 0.82)
    gold = material("Bronze dourado", (0.67, 0.39, 0.085), 0.72, 0.29)
    gold_light = material("Dourado polido", (0.91, 0.66, 0.22), 0.68, 0.23)

    # Duas escadas paralelas ocupam a frente do footprint 4x4; ambas chegam
    # a um patamar comum ao fundo. A frente fica na borda -Y.
    flight_width = 1.55
    flight_centers = (-0.95, 0.95)
    landing_width = 3.72
    start_y = -1.60
    steps = 10
    run = 0.25
    rise = 0.145
    tread_depth = run + 0.025
    for i in range(steps):
        y = start_y + i * run
        top = (i + 1) * rise
        for flight, center_x in enumerate(flight_centers, start=1):
            cube(f"Voo {flight} | degrau {i + 1:02d} | espelho",
                 (center_x, y + run * 0.5, top * 0.5),
                 (flight_width, run + 0.01, top), marble_shadow, 0.018)
            cube(f"Voo {flight} | degrau {i + 1:02d} | piso",
                 (center_x, y + tread_depth * 0.5, top - 0.018),
                 (flight_width, tread_depth, 0.05), marble_light, 0.016)
            cube(f"Voo {flight} | degrau {i + 1:02d} | veludo vinho",
                 (center_x, y + tread_depth * 0.52, top + 0.009),
                 (1.12, tread_depth * 0.70, 0.012), burgundy, 0.008)
            for x in (center_x - 0.58, center_x + 0.58):
                cube(f"Voo {flight} | degrau {i + 1:02d} | filete dourado",
                     (x, y + 0.018, top + 0.009),
                     (0.024, 0.035, 0.018), gold_light, 0.006)

    # Patamar superior comum com tapete largo e roseta central.
    landing_y = start_y + steps * run + 0.36
    landing_z = steps * rise
    cube("Patamar | base de mármore", (0, landing_y, landing_z - 0.11),
         (landing_width, 0.72, 0.22), marble, 0.035)
    cube("Patamar | superfície clara", (0, landing_y, landing_z + 0.005),
         (landing_width, 0.70, 0.045), marble_light, 0.02)
    cube("Patamar | tapete vinho", (0, landing_y - 0.04, landing_z + 0.031),
         (2.42, 0.47, 0.012), burgundy, 0.008)
    for x in (-1.24, 1.24):
        cube("Patamar | moldura dourada", (x, landing_y - 0.04, landing_z + 0.04),
             (0.035, 0.50, 0.014), gold_light, 0.008)
    sphere("Patamar | medalha dourada", (0, landing_y, landing_z + 0.044),
           (0.12, 0.12, 0.014), gold_light, 12, 6)

    # Quatro corrimões: exteriores e divisórias centrais entre os dois voos.
    # Balaústres torneados e terminais dourados mantêm a composição simétrica.
    for x in (-1.72, -0.16, 0.16, 1.72):
        points = []
        for i in range(7):
            y = -1.48 + i * 0.34
            z = 0.50 + (y + 1.48) * 0.56
            points.append((x, y, z))
            cylinder("Corrimão | balaústre torneado", (x, y, z - 0.17),
                     0.045, 0.34, gold, 10, radius_top=0.031)
            sphere("Corrimão | nó do balaústre", (x, y, z - 0.14),
                   (0.058, 0.058, 0.055), gold_light, 10, 6)
            cylinder("Corrimão | base do balaústre", (x, y, z - 0.30),
                     0.064, 0.045, gold_light, 10)
        for a, b in zip(points, points[1:]):
            rod("Corrimão | travessa dourada", a, b, 0.035, gold_light, 8)
        for _px, y, z in (points[0], points[-1]):
            cylinder("Corrimão | terminal", (x, y, z + 0.07),
                     0.065, 0.13, gold_light, 10, radius_top=0.025)
            sphere("Corrimão | pináculo", (x, y, z + 0.15),
                   (0.065, 0.065, 0.065), gold_light, 10, 6)

    # Four low corner plinths anchor the entry and the upper landing.
    for x in (-1.72, 1.72):
        for y, z in ((-1.62, 0.14), (landing_y + 0.38, landing_z + 0.09)):
            cube("Pilastra | pedestal", (x, y, z), (0.24, 0.24, 0.28), marble, 0.025)
            cube("Pilastra | gola dourada", (x, y, z + 0.15), (0.27, 0.27, 0.045), gold, 0.014)
            sphere("Pilastra | pináculo", (x, y, z + 0.22),
                   (0.085, 0.085, 0.10), gold_light, 10, 7)


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    make_staircase()

    scene = bpy.context.scene
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
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.22

    target = (0, 0.05, 0.72)
    bpy.ops.object.camera_add(location=(5.1, -6.7, 4.9))
    camera = bpy.context.object
    camera.name = "Câmera | miniatura isométrica"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 5.55
    look_at(camera, target)
    scene.camera = camera
    for name, location, energy, size, color in (
        ("Luz principal", (4.2, -4.5, 6.8), 780, 4.0, (1.0, 0.84, 0.66)),
        ("Luz de preenchimento", (-3.0, -1.5, 4.5), 500, 4.0, (0.76, 0.84, 1.0)),
        ("Luz de recorte", (0.0, 4.0, 5.5), 620, 3.5, (1.0, 0.70, 0.45)),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.data.color = color
        look_at(light, target)

    scene.render.filepath = str(OUT / "escadaria_luxuosa_preview.png")
    bpy.ops.render.render(write_still=True)
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.filepath = str(OUT / "escadaria_luxuosa.png")
    bpy.ops.render.render(write_still=True)

    meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "escadaria_luxuosa.blend"))
    bpy.ops.object.join()
    bpy.ops.export_scene.gltf(
        filepath=str(OUT / "escadaria_luxuosa.glb"),
        export_format="GLB", use_selection=True, export_apply=True,
        export_materials="EXPORT", export_texcoords=True, export_normals=True,
        export_yup=True,
    )
    print("ESCADARIA_LUXUOSA", "meshes=", len(meshes))


if __name__ == "__main__":
    main()
