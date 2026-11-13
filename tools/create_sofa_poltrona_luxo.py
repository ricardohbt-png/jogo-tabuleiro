"""Cria o sofá e a poltrona estofados da casa de luxo."""
from pathlib import Path
import math

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)


def mat(name, color, metallic=0.0, roughness=0.75):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return m


def assign(obj, material):
    obj.data.materials.append(material)
    return obj


def cube(name, loc, dims, material, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, material)
    if bevel:
        mod = obj.modifiers.new("Bordas acolchoadas", "BEVEL")
        mod.width = bevel
        mod.segments = 3
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        norm = obj.modifiers.new("Normais macias", "WEIGHTED_NORMAL")
        bpy.ops.object.modifier_apply(modifier=norm.name)
    return obj


def cylinder(name, loc, radius, depth, material, vertices=12,
             radius_top=None):
    if radius_top is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                            depth=depth, location=loc)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius,
                                        radius2=radius_top, depth=depth,
                                        location=loc)
    obj = bpy.context.object
    obj.name = name
    assign(obj, material)
    bevel = obj.modifiers.new("Aresta torneada", "BEVEL")
    bevel.width = min(radius * 0.1, 0.016)
    bevel.segments = 2
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    return obj


def sphere(name, loc, scale, material, segments=12, rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                        radius=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, material)
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def rod(name, start, end, radius, material, vertices=8):
    a, b = Vector(start), Vector(end)
    delta = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                        depth=delta.length, location=(a + b) * 0.5)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = delta.to_track_quat("Z", "Y")
    assign(obj, material)
    return obj


def luxury_materials(prefix):
    return {
        "wood": mat(prefix + " | nogueira escura", (0.18, 0.065, 0.030)),
        "wood_light": mat(prefix + " | nogueira iluminada", (0.34, 0.14, 0.055)),
        "gold": mat(prefix + " | latão dourado", (0.69, 0.39, 0.10), 0.68, 0.34),
        "gold_light": mat(prefix + " | friso de ouro", (0.91, 0.66, 0.25), 0.58, 0.30),
        "velvet": mat(prefix + " | veludo bordô", (0.25, 0.012, 0.035), 0.0, 0.91),
        "velvet_light": mat(prefix + " | veludo claro", (0.38, 0.025, 0.065), 0.0, 0.88),
        "blue": mat(prefix + " | almofada azul real", (0.025, 0.075, 0.24), 0.0, 0.86),
        "piping": mat(prefix + " | vivo dourado", (0.84, 0.57, 0.18), 0.44, 0.43),
    }


def make_sofa():
    m = luxury_materials("Sofá")
    wood, light, gold, gilt = m["wood"], m["wood_light"], m["gold"], m["gold_light"]
    velvet, pale, blue, piping = m["velvet"], m["velvet_light"], m["blue"], m["piping"]
    # Sofa is 1x2: its length runs along Y and its room-facing side is +X.
    cube("Sofá | base de nogueira", (0, 0, 0.25), (0.91, 1.88, 0.34), wood, 0.07)
    cube("Sofá | avental frontal", (0.43, 0, 0.37), (0.09, 1.68, 0.28), light, 0.03)
    cube("Sofá | filete frontal dourado", (0.483, 0, 0.40), (0.018, 1.55, 0.045), gilt, 0.008)

    # Four feet with turned gold collars and dark walnut tips.
    for x in (-0.30, 0.30):
        for y in (-0.77, 0.77):
            cylinder("Sofá | pé torneado", (x, y, 0.13), 0.075, 0.25, light, 10, 0.052)
            cylinder("Sofá | ponteira dourada", (x, y, 0.055), 0.067, 0.06, gold, 10)
            cylinder("Sofá | anel do pé", (x, y, 0.21), 0.078, 0.035, gilt, 10)

    # Deep upholstered seat and two separate cushions along the two-tile length.
    cube("Sofá | assento estofado", (0.06, 0, 0.60), (0.69, 1.65, 0.30), velvet, 0.11)
    for y in (-0.42, 0.42):
        cube("Sofá | almofada de assento", (0.095, y, 0.765), (0.62, 0.77, 0.10), pale, 0.075)
        cube("Sofá | vivo da almofada", (0.115, y, 0.818), (0.53, 0.68, 0.012), piping, 0.005)

    # Raised back with two padded panels and small sapphire accent pillows.
    cube("Sofá | estrutura do encosto", (-0.32, 0, 0.91), (0.22, 1.79, 0.93), wood, 0.07)
    cube("Sofá | painel do encosto", (-0.195, 0, 0.99), (0.09, 1.57, 0.76), velvet, 0.055)
    for y in (-0.405, 0.405):
        cube("Sofá | almofada do encosto", (-0.125, y, 0.99), (0.075, 0.75, 0.67), pale, 0.08)
        # A low-relief diamond keeps the upholstery readable at miniature scale.
        diamond = sphere("Sofá | botão do encosto", (-0.078, y, 1.00),
                         (0.018, 0.045, 0.045), gilt, 10, 6)
    for y in (-0.56, 0.56):
        pillow = cube("Sofá | almofada azul", (0.14, y, 0.94), (0.27, 0.28, 0.28), blue, 0.075)
        pillow.rotation_euler[1] = -0.12
        sphere("Sofá | botão da almofada", (0.29, y, 0.94), (0.02, 0.035, 0.035), gilt, 8, 6)

    # Broad armrests with carved side panels and gold caps.
    for yside in (-1, 1):
        y = yside * 0.79
        cube("Sofá | braço estofado", (0.10, y, 0.78), (0.77, 0.28, 0.30), velvet, 0.09)
        cube("Sofá | topo do braço", (0.12, y, 0.94), (0.69, 0.25, 0.055), light, 0.025)
        cube("Sofá | friso do braço", (0.30, y, 0.95), (0.25, 0.255, 0.025), gold, 0.012)
        for x in (-0.10, 0.16, 0.39):
            sphere("Sofá | cravo do braço", (x, y + yside * 0.145, 0.79),
                   (0.025, 0.012, 0.025), gilt, 8, 6)

    # Carved crest rail and subtle nail-head rows along the lower apron.
    cube("Sofá | coroamento do encosto", (-0.30, 0, 1.42), (0.28, 1.82, 0.12), light, 0.045)
    for y in (-0.72, -0.48, -0.24, 0, 0.24, 0.48, 0.72):
        sphere("Sofá | cravo frontal", (0.486, y, 0.40), (0.012, 0.022, 0.022), gilt, 8, 6)
    for y in (-0.74, 0.74):
        sphere("Sofá | terminal do coroamento", (-0.30, y, 1.44),
               (0.08, 0.08, 0.075), gold, 10, 6)


def make_armchair():
    m = luxury_materials("Poltrona")
    wood, light, gold, gilt = m["wood"], m["wood_light"], m["gold"], m["gold_light"]
    velvet, pale, blue, piping = m["velvet"], m["velvet_light"], m["blue"], m["piping"]
    # A reading armchair with its matching footrest fills the requested 1x2 footprint.
    cube("Poltrona | base de nogueira", (0, 0.02, 0.25), (0.91, 1.88, 0.34), wood, 0.07)
    for x in (-0.31, 0.31):
        for y in (-0.70, 0.61):
            cylinder("Poltrona | pé torneado", (x, y, 0.13), 0.072, 0.25, light, 10, 0.05)
            cylinder("Poltrona | ponteira dourada", (x, y, 0.055), 0.064, 0.06, gold, 10)

    # High back and generously padded seat.
    cube("Poltrona | assento estofado", (0, -0.12, 0.62), (0.72, 0.83, 0.30), velvet, 0.11)
    cube("Poltrona | almofada do assento", (0, -0.10, 0.79), (0.65, 0.73, 0.10), pale, 0.075)
    cube("Poltrona | vivo do assento", (0, -0.10, 0.845), (0.57, 0.63, 0.014), piping, 0.005)
    cube("Poltrona | estrutura do encosto", (0, -0.68, 0.98), (0.83, 0.22, 1.14), wood, 0.07)
    cube("Poltrona | painel acolchoado", (0, -0.545, 1.00), (0.68, 0.08, 0.91), velvet, 0.065)
    cube("Poltrona | almofada do encosto", (0, -0.49, 0.98), (0.55, 0.075, 0.75), pale, 0.08)
    for z in (0.82, 1.05, 1.28):
        sphere("Poltrona | botão estofado", (0, -0.445, z), (0.032, 0.016, 0.032), gilt, 8, 6)

    # Winged back and cushioned arms, framed in dark walnut and gilt piping.
    for side in (-1, 1):
        cube("Poltrona | asa lateral", (side * 0.35, -0.52, 1.06),
             (0.14, 0.47, 0.77), velvet, 0.065)
        cube("Poltrona | filete da asa", (side * 0.425, -0.52, 1.06),
             (0.018, 0.39, 0.63), gilt, 0.009)
        cube("Poltrona | braço estofado", (side * 0.40, 0.02, 0.79),
             (0.19, 0.73, 0.24), velvet, 0.07)
        cube("Poltrona | topo do braço", (side * 0.40, 0.04, 0.92),
             (0.20, 0.67, 0.045), light, 0.02)
        for y in (-0.16, 0.02, 0.20):
            sphere("Poltrona | cravo do braço", (side * 0.501, y, 0.81),
                   (0.012, 0.021, 0.021), gilt, 8, 6)
    cube("Poltrona | coroamento do encosto", (0, -0.67, 1.58), (0.91, 0.25, 0.12), light, 0.04)
    sphere("Poltrona | medalhão do encosto", (0, -0.526, 1.47),
           (0.10, 0.03, 0.10), gold, 10, 8)
    sphere("Poltrona | gema azul", (0, -0.49, 1.47),
           (0.04, 0.02, 0.05), blue, 10, 8)

    # Matching upholstered footrest at the forward end of the two-tile footprint.
    cube("Poltrona | apoio para os pés", (0, 0.73, 0.36), (0.76, 0.55, 0.38), wood, 0.07)
    cube("Poltrona | almofada do apoio", (0, 0.73, 0.59), (0.72, 0.51, 0.16), velvet, 0.075)
    cube("Poltrona | filete do apoio", (0, 0.73, 0.675), (0.62, 0.42, 0.016), gilt, 0.006)
    for x in (-0.27, 0.27):
        cylinder("Poltrona | pé do apoio", (x, 0.73, 0.12), 0.06, 0.20, light, 10, 0.043)
        cylinder("Poltrona | ponteira do apoio", (x, 0.73, 0.05), 0.052, 0.05, gold, 10)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def export_piece(slug, builder, camera_pos, ortho):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    builder()
    target = (0, 0, 0.78)
    bpy.ops.object.camera_add(location=camera_pos)
    camera = bpy.context.object
    camera.name = "Câmera | miniatura isométrica"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = ortho
    look_at(camera, target)
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
        ("Luz principal", (4.2, -4.5, 6.8), 680, 4.0, (1.0, 0.84, 0.66)),
        ("Luz de preenchimento", (-3.0, -1.5, 4.5), 420, 4.0, (0.76, 0.84, 1.0)),
        ("Luz de recorte", (0.0, 4.0, 5.5), 520, 3.5, (1.0, 0.70, 0.45)),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.data.color = color
        look_at(light, target)

    meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / (slug + ".blend")))
    scene.render.filepath = str(OUT / (slug + "_preview.png"))
    bpy.ops.render.render(write_still=True)
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.filepath = str(OUT / (slug + ".png"))
    bpy.ops.render.render(write_still=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    bpy.ops.export_scene.gltf(filepath=str(OUT / (slug + ".glb")),
                              export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True,
                              export_materials="EXPORT")
    print("ASSET_EXPORT", slug, "source_meshes=", len(meshes), "glb_meshes=1")


def main():
    export_piece("sofa_luxo", make_sofa, (4.0, -4.5, 3.2), 3.1)
    export_piece("poltrona_luxo", make_armchair, (3.8, 4.2, 3.0), 3.2)


if __name__ == "__main__":
    main()
