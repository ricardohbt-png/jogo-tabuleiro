"""Cria uma banca compacta de flores e vasos ornamentais para o editor."""
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
        mod = obj.modifiers.new("Bordas gastas", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        norm = obj.modifiers.new("Normais suaves", "WEIGHTED_NORMAL")
        bpy.ops.object.modifier_apply(modifier=norm.name)
    return obj


def cylinder(name, loc, radius, depth, mat, vertices=12,
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
    bevel = obj.modifiers.new("Borda de cerâmica", "BEVEL")
    bevel.width = min(radius * 0.07, 0.012)
    bevel.segments = 1
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    return obj


def sphere(name, loc, scale, mat, segments=10, rings=7):
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


def rod(name, start, end, radius, mat, vertices=7):
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


def flower_materials():
    return {
        "wood": material("Carvalho da banca", (0.28, 0.13, 0.055)),
        "wood_light": material("Tábuas claras", (0.46, 0.25, 0.10)),
        "wood_dark": material("Sombra da madeira", (0.17, 0.07, 0.03)),
        "iron": material("Ferro escuro", (0.10, 0.11, 0.10), 0.58, 0.48),
        "terracotta": material("Terracota", (0.56, 0.18, 0.07)),
        "cream_pot": material("Cerâmica creme", (0.78, 0.61, 0.39)),
        "blue_pot": material("Cerâmica azul esmaltada", (0.035, 0.18, 0.39), 0.12, 0.35),
        "leaf": material("Folhas verdes", (0.045, 0.24, 0.055)),
        "leaf_light": material("Folhas novas", (0.22, 0.42, 0.055)),
        "stem": material("Hastes", (0.18, 0.29, 0.035)),
        "rose": material("Pétalas rubras", (0.75, 0.035, 0.11)),
        "pink": material("Pétalas rosadas", (0.95, 0.20, 0.36)),
        "yellow": material("Pétalas douradas", (0.96, 0.59, 0.045)),
        "violet": material("Pétalas violetas", (0.36, 0.085, 0.62)),
        "white": material("Pétalas marfim", (0.95, 0.85, 0.62)),
        "center": material("Centros das flores", (0.95, 0.72, 0.12)),
        "cloth_green": material("Tecido verde da cobertura", (0.08, 0.27, 0.12)),
        "cloth_cream": material("Tecido creme da cobertura", (0.82, 0.68, 0.42)),
        "sign": material("Placa pintada", (0.055, 0.19, 0.13)),
    }


def add_pot(name, center, radius, height, pot_mat):
    x, y, z = center
    cylinder(name + " | corpo", (x, y, z + height * 0.46), radius * 0.70,
             height * 0.88, pot_mat, 12, radius_top=radius)
    cylinder(name + " | pé", (x, y, z + height * 0.06), radius * 0.62,
             height * 0.13, pot_mat, 12)
    cylinder(name + " | borda", (x, y, z + height * 0.91), radius * 1.05,
             height * 0.10, pot_mat, 12)
    # Dark soil remains visible around the flower stems.
    soil = material("Terra úmida de " + name, (0.095, 0.052, 0.025))
    cylinder(name + " | terra", (x, y, z + height * 0.82), radius * 0.83,
             height * 0.035, soil, 12)
    return z + height


def add_bloom(prefix, center, petal_mat, scale=1.0):
    x, y, z = center
    sphere(prefix + " | miolo", (x, y, z),
           (0.035 * scale, 0.035 * scale, 0.032 * scale),
           flower_mats["center"], 8, 6)
    for i in range(6):
        angle = math.tau * i / 6
        px = x + math.cos(angle) * 0.050 * scale
        py = y + math.sin(angle) * 0.050 * scale
        petal = sphere(prefix + " | pétala", (px, py, z),
                       (0.045 * scale, 0.027 * scale, 0.027 * scale),
                       petal_mat, 8, 6)
        petal.rotation_euler[2] = angle


def add_flower_bunch(prefix, pot_center, top_z, colors, height=0.35):
    x, y, _ = pot_center
    spots = [(-0.055, -0.025), (0.045, -0.025), (0.0, 0.055),
             (-0.075, 0.045), (0.075, 0.045)]
    for i, (dx, dy) in enumerate(spots):
        stem_h = height * (0.72 + (i % 3) * 0.12)
        z0 = top_z - 0.015
        z1 = z0 + stem_h
        fx, fy = x + dx, y + dy
        rod(prefix + " | haste %02d" % i, (fx, fy, z0),
            (fx + dx * 0.42, fy + dy * 0.42, z1), 0.009, flower_mats["stem"], 6)
        for side in (-1, 1):
            leaf_z = z0 + stem_h * (0.42 if side < 0 else 0.60)
            leaf = sphere(prefix + " | folha %02d %d" % (i, side),
                          (fx + side * 0.045, fy, leaf_z),
                          (0.055, 0.025, 0.018),
                          flower_mats["leaf"] if i % 2 else flower_mats["leaf_light"], 8, 6)
            leaf.rotation_euler[1] = side * 0.28
        bloom_mat = colors[i % len(colors)]
        add_bloom(prefix + " | flor %02d" % i,
                  (fx + dx * 0.42, fy + dy * 0.42, z1), bloom_mat,
                  0.82 if i % 2 else 1.0)


def make_stand():
    global flower_mats
    flower_mats = flower_materials()
    m = flower_mats

    # Narrow painted stall, fitted inside a single tile.
    cube("Banca | base", (0, 0, 0.12), (0.84, 0.84, 0.18), m["wood_dark"], 0.035)
    cube("Banca | prateleira inferior", (0, 0.02, 0.26), (0.72, 0.68, 0.085), m["wood_light"], 0.018)
    for x in (-0.30, 0.30):
        for y in (-0.28, 0.28):
            cube("Banca | perna", (x, y, 0.48), (0.075, 0.075, 0.43), m["wood"], 0.012)
            cylinder("Banca | ponteira", (x, y, 0.255), 0.05, 0.05, m["iron"], 8)
    cube("Banca | tampo", (0, 0, 0.73), (0.86, 0.76, 0.12), m["wood_light"], 0.026)
    cube("Banca | friso frontal", (0, -0.394, 0.68), (0.70, 0.025, 0.09), m["wood_dark"], 0.01)
    for x in (-0.22, 0, 0.22):
        sphere("Banca | prego de bronze", (x, -0.412, 0.68),
               (0.018, 0.012, 0.018), m["iron"], 8, 6)

    # Short striped canopy and flower emblem add a clear market-stall silhouette.
    for x in (-0.35, 0.35):
        cube("Toldo | montante", (x, 0.20, 1.22), (0.055, 0.055, 0.93), m["wood"], 0.01)
        sphere("Toldo | ponteira", (x, 0.20, 1.70), (0.05, 0.05, 0.07), m["iron"], 8, 6)
    for i in range(5):
        x0 = -0.40 + i * 0.16
        x1 = x0 + 0.16
        verts = [(x0, -0.39, 1.54), (x1, -0.39, 1.54),
                 (x1, 0.29, 1.67), (x0, 0.29, 1.67)]
        mesh = bpy.data.meshes.new("Toldo listrado mesh")
        mesh.from_pydata(verts, [], [(0, 1, 2, 3)])
        mesh.materials.append(m["cloth_green"] if i % 2 == 0 else m["cloth_cream"])
        panel = bpy.data.objects.new("Toldo | faixa %d" % i, mesh)
        bpy.context.collection.objects.link(panel)
        # A thin folded edge keeps the canvas visible from the front.
        cube("Toldo | babado frontal", ((x0 + x1) / 2, -0.395, 1.51),
             (0.15, 0.035, 0.12), m["cloth_green"] if i % 2 == 0 else m["cloth_cream"], 0.018)
    cube("Toldo | travessa", (0, 0.23, 1.57), (0.78, 0.06, 0.07), m["wood_dark"], 0.01)

    # Hanging sign with a simple flower medallion, without lettering.
    cube("Placa | fundo verde", (0, -0.434, 1.31), (0.30, 0.035, 0.24), m["sign"], 0.018)
    sphere("Placa | flor", (0, -0.46, 1.32), (0.055, 0.018, 0.055), m["pink"], 10, 8)
    sphere("Placa | centro", (0, -0.48, 1.32), (0.020, 0.012, 0.020), m["center"], 8, 6)
    for i in range(5):
        a = math.tau * i / 5
        sphere("Placa | pétala", (math.cos(a) * 0.065, -0.46, 1.32 + math.sin(a) * 0.065),
               (0.025, 0.012, 0.025), m["pink"], 8, 6)

    # Colorful glazed, terracotta and cream pots sit on the counter.
    pots = [(-0.24, -0.16, 0.79, 0.13, 0.25, m["terracotta"], [m["rose"], m["pink"]]),
            (0.24, -0.13, 0.79, 0.13, 0.25, m["blue_pot"], [m["yellow"], m["white"]]),
            (0.00, 0.17, 0.79, 0.14, 0.28, m["cream_pot"], [m["violet"], m["pink"]])]
    for i, (x, y, z, radius, height, pot_mat, blooms) in enumerate(pots):
        top_z = add_pot("Vaso ornamental %d" % (i + 1),
                        (x, y, z), radius, height, pot_mat)
        add_flower_bunch("Buquê do vaso %d" % (i + 1), (x, y, z), top_z,
                         blooms, height=0.34 + i * 0.025)

    # Smaller pots and flower bundles fill the lower shelf and frame the stand.
    for i, x in enumerate((-0.22, 0.22)):
        pot = m["blue_pot"] if i == 0 else m["terracotta"]
        z = 0.31
        top_z = add_pot("Vasinho da prateleira %d" % (i + 1),
                        (x, 0.0, z), 0.095, 0.18, pot)
        add_flower_bunch("Raminho da prateleira %d" % (i + 1),
                         (x, 0, z), top_z, [m["yellow"] if i == 0 else m["white"]],
                         height=0.20)


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    make_stand()
    target = (0, 0, 0.92)
    bpy.ops.object.camera_add(location=(3.5, -4.5, 3.2))
    camera = bpy.context.object
    camera.name = "Câmera | banca de flores"
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
        ("Luz principal", (3.0, -3.8, 5.0), 480, 3.0, (1.0, 0.83, 0.63)),
        ("Luz de preenchimento", (-3.2, -1.4, 3.1), 350, 2.8, (0.72, 0.84, 1.0)),
        ("Luz de recorte", (0.0, 3.3, 4.0), 320, 2.4, (1.0, 0.72, 0.42)),
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
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "banca_flores.blend"))
    scene.render.filepath = str(OUT / "banca_flores_preview.png")
    bpy.ops.render.render(write_still=True)
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.filepath = str(OUT / "banca_flores.png")
    bpy.ops.render.render(write_still=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    bpy.ops.export_scene.gltf(filepath=str(OUT / "banca_flores.glb"),
                              export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True,
                              export_materials="EXPORT")
    print("ASSET_EXPORT banca_flores source_meshes=", len(meshes), "glb_meshes=1")


if __name__ == "__main__":
    main()
