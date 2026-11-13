"""Cria o carrinho manual de entregas com carga para a cidade."""
from pathlib import Path
import math

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)


def material(name, color, metallic=0.0, roughness=0.78):
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


def cube(name, loc, dims, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, mat)
    if bevel:
        mod = obj.modifiers.new("Bordas gastas", "BEVEL")
        mod.width = bevel
        mod.segments = 1
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        norm = obj.modifiers.new("Normais da madeira", "WEIGHTED_NORMAL")
        bpy.ops.object.modifier_apply(modifier=norm.name)
    return obj


def cylinder(name, loc, radius, depth, mat, vertices=12,
             rotation=None, radius_top=None):
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
    bevel = obj.modifiers.new("Arestas arredondadas", "BEVEL")
    bevel.width = min(radius * 0.08, 0.015)
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


def torus(name, loc, major, minor, mat, rotation=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                     major_segments=16, minor_segments=6,
                                     location=loc, rotation=rotation or (0, 0, 0))
    obj = bpy.context.object
    obj.name = name
    assign(obj, mat)
    return obj


def materials():
    return {
        "wood": material("Carvalho escuro", (0.23, 0.105, 0.045)),
        "wood_light": material("Tábuas de carvalho", (0.43, 0.24, 0.095)),
        "wood_edge": material("Arestas de madeira", (0.15, 0.065, 0.025)),
        "iron": material("Ferro das rodas", (0.075, 0.085, 0.085), 0.78, 0.43),
        "iron_light": material("Ferro gasto", (0.24, 0.24, 0.21), 0.66, 0.5),
        "burlap": material("Juta dos sacos", (0.53, 0.35, 0.16)),
        "burlap_light": material("Costura da juta", (0.72, 0.52, 0.27)),
        "rope": material("Cordas de carga", (0.48, 0.30, 0.11)),
        "log": material("Lenha castanha", (0.32, 0.14, 0.055)),
        "log_end": material("Corte claro da lenha", (0.70, 0.48, 0.25)),
        "clay": material("Cerâmica vermelha", (0.54, 0.17, 0.065)),
        "clay_light": material("Faixa da cerâmica", (0.83, 0.48, 0.18)),
    }


def add_wheel(side, m):
    x, y, z = side * 0.43, 0.20, 0.34
    axis_x = (0, math.pi / 2, 0)
    cylinder("Roda | cubo", (x, y, z), 0.105, 0.18, m["wood_edge"],
             12, axis_x)
    cylinder("Roda | cubo de ferro", (side * 0.525, y, z), 0.073, 0.035,
             m["iron_light"], 12, axis_x)
    # Wooden rim, iron tire and eight spokes in the wheel plane.
    torus("Roda | aro de madeira", (side * 0.48, y, z), 0.285, 0.045,
          m["wood_light"], axis_x)
    torus("Roda | cinta de ferro", (side * 0.515, y, z), 0.292, 0.018,
          m["iron"], axis_x)
    for i in range(8):
        angle = math.tau * i / 8
        end = (x, y + math.cos(angle) * 0.25, z + math.sin(angle) * 0.25)
        rod("Roda | raio", (x, y, z), end, 0.022, m["wood"], 7)
    for i in range(8):
        angle = math.tau * i / 8
        sphere("Roda | rebite", (side * 0.535,
               y + math.cos(angle) * 0.292,
               z + math.sin(angle) * 0.292), (0.015, 0.018, 0.018),
               m["iron_light"], 7, 5)


def add_sack(name, center, scale, m):
    x, y, z = center
    sx, sy, sz = scale
    body = sphere(name + " | corpo", (x, y, z + sz * 0.43),
                  (sx, sy, sz * 0.70), m["burlap"], 14, 10)
    neck = sphere(name + " | boca amarrada", (x, y, z + sz * 0.94),
                  (sx * 0.40, sy * 0.42, sz * 0.24), m["burlap_light"], 10, 7)
    torus(name + " | cordão", (x, y, z + sz * 0.84), sx * 0.44,
          0.014, m["rope"])
    for side in (-1, 1):
        rod(name + " | costura", (x + side * sx * 0.65, y, z + sz * 0.24),
            (x + side * sx * 0.45, y, z + sz * 0.68), 0.008,
            m["burlap_light"], 5)
    return body


def make_cart():
    m = materials()
    # Rectangular handcart bed and low plank sides.
    for i in range(5):
        y = -0.28 + i * 0.22
        cube("Caçamba | assoalho %d" % i, (0, y, 0.68),
             (0.67, 0.205, 0.095), m["wood_light"], 0.018)
    for x in (-0.36, 0.36):
        for y in (-0.39, 0.58):
            cube("Caçamba | montante", (x, y, 0.91), (0.075, 0.075, 0.57), m["wood"], 0.012)
        for z in (0.80, 0.99, 1.18):
            cube("Caçamba | tábua lateral", (x, 0.095, z),
                 (0.065, 0.91, 0.15), m["wood_light" if z != 0.99 else "wood"], 0.018)
    for y in (-0.39, 0.58):
        for z in (0.80, 0.99, 1.18):
            cube("Caçamba | tábua de cabeceira", (0, y, z),
                 (0.68, 0.06, 0.15), m["wood_light"], 0.018)
    # Iron corner straps, axle, and feet.
    rod("Carrinho | eixo", (-0.55, 0.20, 0.34), (0.55, 0.20, 0.34), 0.045, m["iron"], 10)
    for x in (-0.34, 0.34):
        for y in (-0.36, 0.56):
            cube("Caçamba | cantoneira", (x, y, 0.96), (0.025, 0.025, 0.48), m["iron"], 0.005)
    for side in (-1, 1):
        add_wheel(side, m)

    # Two long handles project from the front for a porter to pull.
    for x in (-0.22, 0.22):
        rod("Carrinho | varal", (x, -0.28, 0.60), (x, -0.98, 0.55), 0.045, m["wood"], 8)
        cylinder("Carrinho | punho de ferro", (x, -0.98, 0.55), 0.052, 0.13,
                 m["iron_light"], 8, (math.pi / 2, 0, 0))
    # Small foot rest keeps the loaded trolley upright when parked.
    rod("Carrinho | apoio", (-0.24, -0.23, 0.13), (0.24, -0.23, 0.13), 0.045, m["iron"], 8)
    for x in (-0.22, 0.22):
        rod("Carrinho | perna de apoio", (x, -0.22, 0.16), (x, -0.07, 0.60), 0.035, m["iron"], 8)

    # Three burlap parcels fill the cart without hiding the walls.
    add_sack("Saco de entrega esquerdo", (-0.16, -0.12, 1.22),
             (0.19, 0.23, 0.36), m)
    add_sack("Saco de entrega direito", (0.16, 0.06, 1.22),
             (0.19, 0.23, 0.34), m)
    add_sack("Saco pequeno de entrega", (0.02, 0.36, 1.22),
             (0.18, 0.19, 0.29), m)

    # Tied firewood bundle laid across the rear of the cargo.
    for i in range(5):
        x = -0.25 + i * 0.125
        y = 0.39 + (i % 2) * 0.055
        rod("Lenha | tora %d" % i, (x, y - 0.20, 1.55),
            (x, y + 0.20, 1.55), 0.055, m["log" if i % 2 else "wood_light"], 9)
        cylinder("Lenha | corte %d" % i, (x, y - 0.205, 1.55), 0.052, 0.012,
                 m["log_end"], 9, (math.pi / 2, 0, 0))
    for x in (-0.23, 0.22):
        rod("Lenha | amarração", (x, 0.17, 1.50), (x, 0.62, 1.50),
            0.014, m["rope"], 6)

    # A small glazed jar signals fragile goods mixed with deliveries.
    cylinder("Jarro | corpo", (0, -0.35, 1.37), 0.105, 0.28, m["clay"], 12,
             radius_top=0.075)
    cylinder("Jarro | gargalo", (0, -0.35, 1.55), 0.055, 0.12, m["clay"], 10,
             radius_top=0.04)
    torus("Jarro | faixa dourada", (0, -0.35, 1.38), 0.102, 0.012, m["clay_light"])


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    make_cart()
    target = (0, -0.02, 0.90)
    bpy.ops.object.camera_add(location=(3.8, -4.7, 3.4))
    camera = bpy.context.object
    camera.name = "Câmera | carrinho de entregas"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 3.05
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
        ("Luz principal", (4.0, -4.0, 5.0), 560, 3.0, (1.0, 0.84, 0.65)),
        ("Luz de preenchimento", (-3.5, -1.0, 3.5), 380, 3.0, (0.76, 0.84, 1.0)),
        ("Luz de recorte", (0.0, 4.0, 4.5), 360, 2.8, (1.0, 0.70, 0.43)),
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
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "carrinho_entregas.blend"))
    scene.render.filepath = str(OUT / "carrinho_entregas_preview.png")
    bpy.ops.render.render(write_still=True)
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.filepath = str(OUT / "carrinho_entregas.png")
    bpy.ops.render.render(write_still=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    bpy.ops.export_scene.gltf(filepath=str(OUT / "carrinho_entregas.glb"),
                              export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True,
                              export_materials="EXPORT")
    print("ASSET_EXPORT carrinho_entregas source_meshes=", len(meshes), "glb_meshes=1")


if __name__ == "__main__":
    main()
