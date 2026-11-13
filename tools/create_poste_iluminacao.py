"""Cria o poste medieval de iluminação com lanterna acesa."""
from pathlib import Path
import math

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)


def material(name, color, metallic=0.0, roughness=0.58, emission=None, strength=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    if emission:
        socket = shader.inputs.get("Emission Color") or shader.inputs.get("Emission")
        if socket:
            socket.default_value = (*emission, 1)
        socket = shader.inputs.get("Emission Strength")
        if socket:
            socket.default_value = strength
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
        mod = obj.modifiers.new("Arestas forjadas", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        norm = obj.modifiers.new("Normais polidas", "WEIGHTED_NORMAL")
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
    bevel = obj.modifiers.new("Bordas suaves", "BEVEL")
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
        face.use_smooth = True
    return obj


def rod(name, start, end, radius, mat, vertices=8):
    a, b = Vector(start), Vector(end)
    delta = b - a
    obj = cylinder(name, (a + b) * 0.5, radius, delta.length, mat, vertices)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = delta.to_track_quat("Z", "Y")
    return obj


def lantern_materials():
    return {
        "iron": material("Ferro forjado escuro", (0.075, 0.085, 0.09), 0.82, 0.42),
        "iron_light": material("Ferro nas bordas", (0.20, 0.20, 0.18), 0.76, 0.38),
        "bronze": material("Bronze envelhecido", (0.45, 0.23, 0.065), 0.68, 0.36),
        "gold": material("Latão da lanterna", (0.82, 0.52, 0.14), 0.58, 0.32),
        "glass": material("Vidro âmbar aceso", (0.68, 0.29, 0.045), 0.08, 0.27,
                          emission=(1.0, 0.34, 0.045), strength=0.38),
        "flame_outer": material("Chama laranja", (1.0, 0.22, 0.025), 0.0, 0.32,
                                emission=(1.0, 0.11, 0.01), strength=2.0),
        "flame_inner": material("Núcleo dourado da chama", (1.0, 0.76, 0.18), 0.0, 0.25,
                                emission=(1.0, 0.50, 0.055), strength=3.2),
    }


def make_lamp():
    m = lantern_materials()
    iron, iron_light = m["iron"], m["iron_light"]
    bronze, gold = m["bronze"], m["gold"]

    # Weighted octagonal plinth keeps the post visually grounded in one tile.
    cylinder("Base | sapata de ferro", (0, 0, 0.09), 0.40, 0.18, iron, 8)
    cylinder("Base | anel de bronze", (0, 0, 0.19), 0.34, 0.055, bronze, 12)
    cylinder("Base | pedestal cônico", (0, 0, 0.35), 0.25, 0.30, iron_light,
             10, radius_top=0.12)
    cylinder("Base | gola dourada", (0, 0, 0.51), 0.16, 0.075, gold, 12)

    # Slender cast-iron shaft with collars, raised ribs and a small side scroll.
    cylinder("Haste | poste principal", (0, 0, 1.13), 0.085, 1.22, iron, 12,
             radius_top=0.065)
    for z, radius in ((0.62, 0.13), (0.72, 0.095), (1.50, 0.105), (1.59, 0.145)):
        cylinder("Haste | anel decorativo", (0, 0, z), radius, 0.055,
                 bronze if z in (0.72, 1.59) else iron_light, 12)
    for angle in range(0, 360, 90):
        a = math.radians(angle)
        x, y = math.cos(a), math.sin(a)
        rod("Haste | filete vertical", (x * 0.071, y * 0.071, 0.75),
            (x * 0.060, y * 0.060, 1.49), 0.012, iron_light, 6)
    # Curled support arms lift the lantern above the shaft collar.
    for side in (-1, 1):
        rod("Suporte | braço inclinado", (side * 0.04, 0, 1.55),
            (side * 0.28, 0, 1.77), 0.035, iron, 8)
        sphere("Suporte | voluta", (side * 0.29, 0, 1.78),
               (0.07, 0.055, 0.065), bronze, 10, 6)
        rod("Suporte | arco da lanterna", (side * 0.28, 0, 1.78),
            (side * 0.28, 0, 1.92), 0.025, iron_light, 8)

    # Square lantern body, with amber panes inside a heavy iron frame.
    zmid = 2.12
    cube("Lanterna | base", (0, 0, 1.86), (0.62, 0.62, 0.10), iron, 0.035)
    cube("Lanterna | friso de latão", (0, 0, 1.925), (0.57, 0.57, 0.035), gold, 0.015)
    cube("Lanterna | aro inferior", (0, 0, 1.96), (0.55, 0.55, 0.035), iron_light, 0.01)
    # Four amber side panels, slightly inset from the iron corner posts.
    pane_z = zmid
    pane_h, pane_w = 0.39, 0.13
    for side in (-1, 1):
        for pane_side in (-1, 1):
            cube("Vidro âmbar | frente e trás",
                 (pane_side * 0.105, side * 0.217, pane_z),
                 (pane_w, 0.025, pane_h), m["glass"], 0.012)
            cube("Vidro âmbar | laterais",
                 (side * 0.217, pane_side * 0.105, pane_z),
                 (0.025, pane_w, pane_h), m["glass"], 0.012)
    for x in (-0.255, 0.255):
        for y in (-0.255, 0.255):
            cylinder("Lanterna | montante de ferro", (x, y, pane_z),
                     0.035, 0.48, iron, 8)
            sphere("Lanterna | rebite", (x, y, 2.30),
                   (0.047, 0.047, 0.047), bronze, 8, 6)
    # Strong warm flame remains visible through the lantern from all directions.
    cylinder("Chama | labareda exterior", (0, 0, 2.13), 0.105, 0.34,
             m["flame_outer"], 7, radius_top=0.014)
    cylinder("Chama | núcleo", (0, -0.012, 2.10), 0.062, 0.24,
             m["flame_inner"], 7, radius_top=0.008)
    cylinder("Lanterna | aro superior", (0, 0, 2.39), 0.34, 0.07, gold, 8)
    # Faceted canopy with a pointed finial.
    cylinder("Lanterna | teto piramidal", (0, 0, 2.52), 0.37, 0.25,
             iron, 4, radius_top=0.045)
    cylinder("Lanterna | filete do teto", (0, 0, 2.42), 0.37, 0.035, bronze, 8)
    sphere("Lanterna | pomo superior", (0, 0, 2.67),
           (0.09, 0.09, 0.08), gold, 10, 6)
    cylinder("Lanterna | pináculo", (0, 0, 2.78), 0.035, 0.18,
             iron_light, 8, radius_top=0.008)


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    make_lamp()
    target = (0, 0, 1.35)
    bpy.ops.object.camera_add(location=(3.7, -4.7, 3.7))
    camera = bpy.context.object
    camera.name = "Câmera | poste medieval"
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
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.07, 0.065, 0.06, 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.30
    for name, location, energy, size, color in (
        ("Luz principal", (3.0, -3.5, 5.0), 450, 2.8, (1.0, 0.82, 0.58)),
        ("Luz de preenchimento", (-3.0, -1.0, 3.0), 250, 2.6, (0.72, 0.80, 1.0)),
        ("Luz quente da lanterna", (0, 0.4, 2.4), 65, 0.55, (1.0, 0.35, 0.08)),
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
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "poste_iluminacao.blend"))
    scene.render.filepath = str(OUT / "poste_iluminacao_preview.png")
    bpy.ops.render.render(write_still=True)
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.filepath = str(OUT / "poste_iluminacao.png")
    bpy.ops.render.render(write_still=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    bpy.ops.export_scene.gltf(filepath=str(OUT / "poste_iluminacao.glb"),
                              export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True,
                              export_materials="EXPORT")
    print("ASSET_EXPORT poste_iluminacao source_meshes=", len(meshes), "glb_meshes=1")


if __name__ == "__main__":
    main()
